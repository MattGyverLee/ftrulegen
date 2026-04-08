#!/usr/bin/env python3
"""
Debug Launcher for Rule Assistant
Shows all console output, errors, and debugging information
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src_py to path
src_py = Path(__file__).parent / 'src_py'
sys.path.insert(0, str(src_py))

# Set up comprehensive logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'rule_assistant_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)-8s] %(asctime)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)  # Also print to console
    ]
)

logger = logging.getLogger(__name__)
logger.info("="*70)
logger.info("Rule Assistant Debug Launcher Started")
logger.info("="*70)
logger.info(f"Log file: {log_file}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")

def test_imports():
    """Test that all required modules can be imported"""
    logger.info("\n[TEST] Checking module imports...")

    modules_to_test = [
        ('PyQt6.QtWidgets', 'PyQt6'),
        ('src_py.model.flex_trans_rule_generator', 'FLExTransRuleGenerator'),
        ('src_py.flextrans_integration', 'flextrans_integration'),
        ('src_py.service.web_page_producer', 'WebPageProducer'),
    ]

    for import_path, label in modules_to_test:
        try:
            __import__(import_path)
            logger.info(f"  [OK] {label}")
        except ImportError as e:
            logger.error(f"  [FAIL] {label}: {e}")
            return False

    return True

def test_assets():
    """Test that CSS assets are available"""
    logger.info("\n[TEST] Checking CSS assets...")

    assets_dir = src_py / 'assets'
    css_files = ['treeflex.css', 'rulegen.css']

    for css_file in css_files:
        asset_path = assets_dir / css_file
        if asset_path.exists():
            size = asset_path.stat().st_size
            logger.info(f"  [OK] {css_file} ({size} bytes)")
        else:
            logger.error(f"  [MISSING] {css_file} at {asset_path}")
            return False

    return True

def test_module_functionality():
    """Test basic module functionality"""
    logger.info("\n[TEST] Testing module functionality...")

    try:
        from src_py.model.source_target import Source, Target
        from src_py.model.flex_trans_rule import FLExTransRule
        from src_py.model.feature import Feature
        from src_py.model.enums import HeadValue
        from src_py.service.web_page_producer import WebPageProducer

        # Create a test rule
        source = Source()
        target = Target()

        sw = source.insert_new_word_at(0)
        sw.word_category = "v"

        tw = target.insert_new_word_at(0)
        tw.head = HeadValue.yes
        tw.features.append(Feature(label="number", value="sg"))

        rule = FLExTransRule(name="TestRule", source=source, target=target)
        logger.info(f"  [OK] Created test rule: {rule.name}")

        # Test HTML generation
        producer = WebPageProducer()
        html = producer.produce_web_page(rule)
        logger.info(f"  [OK] Generated HTML ({len(html)} chars)")

        if 'qwebchannel' not in html:
            logger.warning("  [WARN] QWebChannel not found in HTML")
            return False

        logger.info(f"  [OK] QWebChannel integration verified")
        return True

    except Exception as e:
        logger.exception(f"  [ERROR] Module test failed: {e}")
        return False

def main():
    """Main entry point"""
    try:
        # Run diagnostic tests
        logger.info("\n" + "="*70)
        logger.info("RUNNING DIAGNOSTICS")
        logger.info("="*70)

        tests = [
            ("Module Imports", test_imports),
            ("CSS Assets", test_assets),
            ("Module Functionality", test_module_functionality),
        ]

        all_passed = True
        for test_name, test_func in tests:
            try:
                if not test_func():
                    all_passed = False
                    logger.warning(f"\n[WARN] {test_name} test had issues")
            except Exception as e:
                all_passed = False
                logger.exception(f"\n[ERROR] {test_name} test failed: {e}")

        if not all_passed:
            logger.warning("\n[WARN] Some diagnostics failed. Check above for details.")
            logger.warning("The module may not work correctly in FlexTools.")
        else:
            logger.info("\n[OK] All diagnostics passed!")

        # Launch the module
        logger.info("\n" + "="*70)
        logger.info("LAUNCHING RULE ASSISTANT MODULE")
        logger.info("="*70)

        from PyQt6.QtWidgets import QApplication
        from flextrans_integration import start_rule_assistant

        # Create test files for debugging
        test_rule_file = Path(__file__).parent / 'debug_rules.xml'
        test_flex_data = Path(__file__).parent / 'debug_flex_data.xml'
        test_data = Path(__file__).parent / 'debug_test_data.xml'

        # Create minimal test files if they don't exist
        if not test_rule_file.exists():
            from src_py.model.flex_trans_rule_generator import FLExTransRuleGenerator
            from src_py.service.xml_backend_provider import XMLBackEndProvider
            gen = FLExTransRuleGenerator()
            XMLBackEndProvider.save_data_to_file(gen, str(test_rule_file))
            logger.info(f"Created test rule file: {test_rule_file}")

        logger.info(f"Using rule file: {test_rule_file}")
        logger.info(f"Using flex data file: {test_flex_data}")
        logger.info(f"Using test data file: {test_data}")

        app = QApplication(sys.argv)
        logger.info("[OK] QApplication initialized")

        saved, rule_index, launch_lrt = start_rule_assistant(
            rule_file=str(test_rule_file),
            flex_data_file=str(test_flex_data),
            test_data_file=str(test_data),
            came_from_lrt=False,
            ui_lang_code="en"
        )

        logger.info(f"\n[RESULT] Module closed")
        logger.info(f"  Saved: {saved}")
        logger.info(f"  Rule index: {rule_index}")
        logger.info(f"  Launch LRT: {launch_lrt}")

        if saved:
            logger.info(f"[OK] Rules were modified and saved")
        else:
            logger.info(f"[INFO] No changes were made")

        logger.info("\n" + "="*70)
        logger.info("Rule Assistant Closed Successfully")
        logger.info("="*70)
        logger.info(f"Full log saved to: {log_file}")
        logger.info("Review the log file for any errors or warnings")

        return 0

    except Exception as e:
        logger.exception(f"FATAL ERROR: {e}")
        logger.error("\n" + "="*70)
        logger.error("CRITICAL ERROR - See details above")
        logger.error("="*70)
        logger.error(f"Log file: {log_file}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
