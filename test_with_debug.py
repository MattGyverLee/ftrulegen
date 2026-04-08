#!/usr/bin/env python3
"""Test Rule Assistant with German-Swedish data - with detailed error logging"""

import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add src_py to path
src_py = Path(__file__).parent / 'src_py'
sys.path.insert(0, str(src_py))

# Set up comprehensive logging with traceback
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'debug_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)-8s] %(asctime)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("="*70)
logger.info("Testing Rule Assistant with Debug Output")
logger.info("="*70)
logger.info(f"Log file: {log_file}")

try:
    from PyQt6.QtWidgets import QApplication
    from flextrans_integration import start_rule_assistant
    
    # Use the extracted test data
    rule_file = Path(__file__).parent / 'test_data' / 'German-Swedish-TestRule.xml'
    flex_data_file = Path(__file__).parent / 'test_data' / 'German-Swedish-FLExData.xml'
    test_data_file = Path(__file__).parent / 'test_data' / 'test_display.html'
    
    logger.info(f"\nUsing test data:")
    logger.info(f"  Rules:    {rule_file}")
    logger.info(f"  FLEx:     {flex_data_file}")
    logger.info(f"  Test:     {test_data_file}")
    
    # Verify files exist
    if not rule_file.exists() or not flex_data_file.exists():
        logger.error("[ERROR] Required files not found")
        sys.exit(1)
    
    # Create test data if needed
    if not test_data_file.exists():
        logger.info("Creating minimal test data HTML...")
        test_data_file.parent.mkdir(exist_ok=True)
        with open(test_data_file, 'w', encoding='utf-8') as f:
            f.write('<html><body><p>Test data</p></body></html>')
    
    logger.info("\n" + "="*70)
    logger.info("LAUNCHING RULE ASSISTANT")
    logger.info("="*70)
    logger.info("[INFO] All uncaught exceptions will be logged below...")
    logger.info("[INFO] Try to reproduce the crash and close the window")
    logger.info("="*70)
    
    app = QApplication(sys.argv)
    logger.info("[OK] QApplication initialized")
    
    # Install exception hook to catch GUI exceptions
    def exception_hook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("="*70)
        logger.error("UNCAUGHT EXCEPTION IN GUI")
        logger.error("="*70)
        logger.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        logger.error("="*70)
    
    sys.excepthook = exception_hook
    
    saved, rule_index, launch_lrt = start_rule_assistant(
        rule_file=str(rule_file),
        flex_data_file=str(flex_data_file),
        test_data_file=str(test_data_file),
        came_from_lrt=False,
        ui_lang_code="en"
    )
    
    logger.info(f"\n[RESULT] Module closed")
    logger.info(f"  Saved: {saved}")
    logger.info(f"  Rule index: {rule_index}")
    
    logger.info("\n" + "="*70)
    logger.info("Test Complete")
    logger.info("="*70)
    logger.info(f"Full log saved to: {log_file}")

except Exception as e:
    logger.exception(f"FATAL ERROR: {e}")
    logger.error("="*70)
    import traceback
    logger.error(traceback.format_exc())
    logger.error("="*70)
    sys.exit(1)
