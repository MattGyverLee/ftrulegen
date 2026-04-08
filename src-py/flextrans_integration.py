"""Integration point for FlexTools RuleAssistant module

This module provides the StartRuleAssistant function that RuleAssistant.py
in FlexTools calls to launch the PyQt6 Rule Assistant window.
"""

import sys
from typing import NamedTuple, Optional
from PyQt6.QtWidgets import QApplication

from .view.main_window import RuleAssistantWindow, WindowResult


def start_rule_assistant(
    rule_file: str,
    flex_data_file: str,
    test_data_file: str,
    came_from_lrt: bool = False,
    ui_lang_code: str = "en"
) -> tuple[bool, Optional[int], bool]:
    """Launch the Rule Assistant window.

    This is called by RuleAssistant.py in the FlexTools environment to
    replace the subprocess call to the Java EXE.

    Args:
        rule_file: Path to rule XML file (read/write)
        flex_data_file: Path to FLEx metadata XML file (read)
        test_data_file: Path to test data HTML file (read)
        came_from_lrt: Whether launched from Live Rule Tester
        ui_lang_code: UI language code ("en", "fr", "es", "de")

    Returns:
        Tuple of (saved: bool, rule_index: Optional[int], launch_lrt: bool)
        - saved: True if user saved rules
        - rule_index: Index of rule to generate, or None if generate all or none
        - launch_lrt: True if user wants to launch Live Rule Tester afterwards
    """
    # Ensure QApplication exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create and show the window
    window = RuleAssistantWindow(
        rule_file=rule_file,
        flex_data_file=flex_data_file,
        test_data_file=test_data_file,
        came_from_lrt=came_from_lrt,
        ui_lang_code=ui_lang_code,
    )

    window.show()

    # Block until window closes
    app.exec()

    # Get result
    result = window.get_result()
    return (result.saved, result.rule_index, result.launch_lrt)
