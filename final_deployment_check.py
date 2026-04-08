#!/usr/bin/env python3
"""Final deployment readiness check"""

import sys
import os
from pathlib import Path

print("="*70)
print("FINAL DEPLOYMENT READINESS CHECK")
print("="*70)

# Test 1: FlexTools-style import
print("\n[TEST 1] FlexTools-style import (add src_py to path)")
src_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src_py')
if src_py_path not in sys.path:
    sys.path.insert(0, src_py_path)

try:
    from flextrans_integration import start_rule_assistant
    print("[PASS] Can import start_rule_assistant from flextrans_integration")
except Exception as e:
    print(f"[FAIL] {e}")
    sys.exit(1)

# Test 2: Core module imports
print("\n[TEST 2] Core module imports")
try:
    from src_py.model.flex_trans_rule_generator import FLExTransRuleGenerator
    from src_py.model.flex_trans_rule import FLExTransRule
    from src_py.model.source_target import Source, Target
    from src_py.service.xml_backend_provider import XMLBackEndProvider
    from src_py.service.web_page_producer import WebPageProducer
    print("[PASS] All core modules import successfully")
except Exception as e:
    print(f"[FAIL] {e}")
    sys.exit(1)

# Test 3: CSS assets are available
print("\n[TEST 3] CSS assets availability")
assets_dir = Path(__file__).parent / "src_py" / "assets"
css_files = list(assets_dir.glob("*.css"))
if len(css_files) >= 2:
    print(f"[PASS] Found {len(css_files)} CSS files in assets/")
    for f in css_files:
        print(f"       - {f.name}")
else:
    print(f"[FAIL] Only found {len(css_files)} CSS files, expected at least 2")
    sys.exit(1)

# Test 4: Verify CSS is loaded in WebPageProducer
print("\n[TEST 4] CSS loading in WebPageProducer")
producer = WebPageProducer()
if len(producer._treeflex_css) > 0 and len(producer._rulegen_css) > 0:
    print(f"[PASS] CSS files loaded:")
    print(f"       - treeflex.css: {len(producer._treeflex_css)} chars")
    print(f"       - rulegen.css: {len(producer._rulegen_css)} chars")
else:
    print("[FAIL] CSS files not loaded properly")
    sys.exit(1)

# Test 5: Complete workflow test
print("\n[TEST 5] Complete module workflow")
try:
    source = Source()
    target = Target()
    
    sw = source.insert_new_word_at(0)
    sw.word_category = "v"
    
    from src_py.model.feature import Feature
    from src_py.model.enums import HeadValue
    
    tw = target.insert_new_word_at(0)
    tw.head = HeadValue.yes
    tw.features.append(Feature(label="number", value="sg"))
    
    rule = FLExTransRule(name="TestRule", source=source, target=target)
    
    # Validate
    from src_py.service.validity_checker import ValidityChecker
    is_valid, _ = ValidityChecker.validate_rule(rule)
    assert is_valid
    
    # Assign IDs
    from src_py.service.rule_id_parent_setter import RuleIdentifierAndParentSetter
    setter = RuleIdentifierAndParentSetter()
    setter.set_identifiers_and_parents(rule)
    
    # Generate HTML
    html = producer.produce_web_page(rule)
    assert "<!DOCTYPE html" in html
    assert "qwebchannel" in html
    
    # Save to XML
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".xml") as f:
        gen = FLExTransRuleGenerator()
        gen.flex_trans_rules.append(rule)
        XMLBackEndProvider.save_data_to_file(gen, f.name)
        
        # Load back
        loaded = XMLBackEndProvider.load_data_from_file(f.name)
        assert len(loaded.flex_trans_rules) == 1
        assert loaded.flex_trans_rules[0].name == "TestRule"
    
    print("[PASS] Complete workflow successful")
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Check required files exist
print("\n[TEST 6] Required files in src_py/")
required_files = [
    "constants.py",
    "flextrans_integration.py",
    "model/__init__.py",
    "model/enums.py",
    "model/flex_trans_rule.py",
    "service/__init__.py",
    "service/xml_backend_provider.py",
    "service/web_page_producer.py",
    "view/__init__.py",
    "view/main_window.py",
    "assets/treeflex.css",
    "assets/rulegen.css",
]

src_py_dir = Path(__file__).parent / "src_py"
missing = []
for f in required_files:
    if not (src_py_dir / f).exists():
        missing.append(f)

if missing:
    print(f"[FAIL] Missing files: {missing}")
    sys.exit(1)
else:
    print(f"[PASS] All {len(required_files)} required files present")

print("\n" + "="*70)
print("[SUCCESS] Module is ready for production deployment to FlexTools")
print("="*70)
print("\nNext steps:")
print("1. Copy src_py/ to D:\Apps\FLExTrans\FlexTools\Modules\FLExTrans\RuleAssistantLib\\")
print("2. Verify Python 3.13+ and PyQt6 are installed in FlexTools environment")
print("3. Test with RuleAssistant.py in FlexTools")
print("\nSee DEPLOYMENT.md for detailed instructions.")
