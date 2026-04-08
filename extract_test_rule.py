"""Extract a default rule from German-Swedish project for testing."""

import sys
from pathlib import Path

# Add src_py to path
src_py = Path(__file__).parent / 'src_py'
sys.path.insert(0, str(src_py))

from src_py.model.enums import HeadValue
from src_py.model.feature import Feature
from src_py.model.flex_trans_rule import FLExTransRule
from src_py.model.source_target import Source, Target
from src_py.model.flex_trans_rule_generator import FLExTransRuleGenerator
from src_py.service.xml_backend_provider import XMLBackEndProvider
from src_py.service.xml_flex_data_provider import XMLFLExDataBackEndProvider

# Load FLEx data from the project
flex_data_file = Path('d:/Apps/FLExTrans/WorkProjects/German-Swedish/Build/ruleAssistantGUIinput.xml')
print(f"[INFO] Loading FLEx data from: {flex_data_file}")

flex_data = XMLFLExDataBackEndProvider.load_data_from_file(str(flex_data_file))
print(f"[OK] Loaded FLEx data")
print(f"    Source: {flex_data.source_data.name}")
print(f"    Target: {flex_data.target_data.name}")
print(f"    Source categories: {len(flex_data.source_data.categories)}")
print(f"    Target categories: {len(flex_data.target_data.categories)}")

# Create a generator with this FLEx data
gen = FLExTransRuleGenerator()
gen.flex_data = flex_data

# Create a simple default rule: German noun -> Swedish noun
print("\n[INFO] Creating default rule: Noun with gender/number agreement...")

source = Source()
target = Target()

# SOURCE: German noun with features
src_word = source.insert_new_word_at(0)
src_word.word_category = "n"
src_word.head = HeadValue.yes
src_word.features.append(Feature(label="gender", value="m"))
src_word.features.append(Feature(label="number", value="sg"))

# TARGET: Swedish noun with matching features
tgt_word = target.insert_new_word_at(0)
tgt_word.word_category = "n"
tgt_word.head = HeadValue.yes
tgt_word.features.append(Feature(label="gender", value="com"))
tgt_word.features.append(Feature(label="number", value="sg"))

rule = FLExTransRule(name="German-noun-to-Swedish-noun", source=source, target=target)
rule.description = "Simple noun transformation with gender and number agreement"
gen.flex_trans_rules.append(rule)

print(f"[OK] Created rule: {rule.name}")

# Save to test data directory
test_output = Path('test_data/German-Swedish-TestRule.xml')
test_output.parent.mkdir(exist_ok=True)

print(f"\n[INFO] Saving to: {test_output}")
XMLBackEndProvider.save_data_to_file(gen, str(test_output))
print(f"[OK] Saved test rule file ({test_output.stat().st_size} bytes)")

# Also copy FLEx data for convenience
flex_copy = Path('test_data/German-Swedish-FLExData.xml')
import shutil
shutil.copy(flex_data_file, flex_copy)
print(f"[OK] Copied FLEx data to: {flex_copy}")

print(f"\n[SUCCESS] Test data extracted!")
print(f"\nTest files created:")
print(f"  Rules:    {test_output.absolute()}")
print(f"  FLEx:     {flex_copy.absolute()}")
