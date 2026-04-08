#!/usr/bin/env python3
"""Test Rule Assistant with German-Swedish project data"""

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
log_file = log_dir / f'german_swedish_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

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
logger.info("Testing Rule Assistant with German-Swedish Data")
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
    if not rule_file.exists():
        logger.error(f"[ERROR] Rule file not found: {rule_file}")
        sys.exit(1)
    if not flex_data_file.exists():
        logger.error(f"[ERROR] FLEx data file not found: {flex_data_file}")
        sys.exit(1)
    
    # Create minimal test data file if it doesn't exist
    if not test_data_file.exists():
        logger.info("Creating minimal test data HTML...")
        test_data_file.parent.mkdir(exist_ok=True)
        with open(test_data_file, 'w', encoding='utf-8') as f:
            f.write('''<html><head><style>
.lu { margin-left: 5px; font-size: 75%; }
.pos { color: blue; margin-left: 5px; }
</style></head><body>
<p><b>Source Text:</b> German-Swedish Sample</p>
<p><span class="lu">Haus<span class="pos">n</span></span> → <span class="lu">hus<span class="pos">n</span></span></p>
<p><span class="lu">Mann<span class="pos">n</span></span> → <span class="lu">man<span class="pos">n</span></span></p>
</body></html>''')
        logger.info(f"[OK] Created test data: {test_data_file}")
    
    logger.info("\n" + "="*70)
    logger.info("LAUNCHING RULE ASSISTANT WITH GERMAN-SWEDISH DATA")
    logger.info("="*70)
    
    app = QApplication(sys.argv)
    logger.info("[OK] QApplication initialized")
    
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
    logger.info(f"  Launch LRT: {launch_lrt}")
    
    if saved:
        logger.info(f"[OK] Rules were modified and saved")
    else:
        logger.info(f"[INFO] No changes were made")
    
    logger.info("\n" + "="*70)
    logger.info("German-Swedish Test Complete")
    logger.info("="*70)
    logger.info(f"Full log saved to: {log_file}")

except Exception as e:
    logger.exception(f"FATAL ERROR: {e}")
    logger.error("\n" + "="*70)
    logger.error("CRITICAL ERROR - See details above")
    logger.error("="*70)
    sys.exit(1)
