#!/usr/bin/env python3
"""
Standalone Rule Assistant Launcher
Connects to a real FLEx project and launches the Rule Assistant
"""

import os
import sys
import argparse
from pathlib import Path

# Add src_py to path for the Python module
src_py = Path(__file__).parent / 'src_py'
sys.path.insert(0, str(src_py))

def main():
    parser = argparse.ArgumentParser(
        description='Launch Rule Assistant for a FLEx project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python standalone_launcher.py --project "C:\\FLEx Projects\\MyLanguage\\MyLanguage.fwdata"
  python standalone_launcher.py --project "C:\\FLEx Projects\\MyLanguage\\MyLanguage.fwdata" --rules "rules.xml"
        '''
    )

    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Path to FLEx project file (.fwdata)'
    )
    parser.add_argument(
        '--rules', '-r',
        default='RuleAssistantRules.xml',
        help='Path to save/load rules (default: RuleAssistantRules.xml)'
    )
    parser.add_argument(
        '--target-config',
        help='Path to target language configuration (if different from source project)'
    )

    args = parser.parse_args()

    # Validate project file exists
    project_path = Path(args.project)
    if not project_path.exists():
        print(f"[ERROR] Project file not found: {args.project}")
        sys.exit(1)

    print("[INFO] Initializing Rule Assistant for standalone use...")
    print(f"[INFO] FLEx project: {project_path}")
    print(f"[INFO] Rules file: {args.rules}")

    try:
        # Try to import FLEx access libraries
        # Note: This requires flextoolslib to be available
        print("[INFO] Attempting to open FLEx project...")

        try:
            from flextoolslib import FlexProject, Report, Utils, FTPaths
            import CreateApertiumRules
            from RuleAssistant import GetRuleAssistantStartData, GetTestDataFile
        except ImportError as e:
            print(f"""
[ERROR] Cannot import FlexTools libraries: {e}

This standalone launcher requires FlexTools libraries to access FLEx data.

SOLUTION: Run this from FlexTools instead:
  1. Copy RuleAssistant.py to: D:\\Apps\\FLExTrans\\FlexTools\\Modules\\FLExTrans\\
  2. Open your FLEx project in FLEx
  3. Go to Tools > FLExTrans > Rule Assistant

OR: Set up the FlexTools Python environment:
  - Install: pip install flextoolslib
  - Ensure PyQt6 is installed: pip install PyQt6
            """)
            sys.exit(1)

        # Create a minimal report object for FLEx operations
        class SimpleReport:
            def Info(self, msg):
                print(f"[INFO] {msg}")
            def Error(self, msg):
                print(f"[ERROR] {msg}")
            def Warning(self, msg):
                print(f"[WARN] {msg}")

        report = SimpleReport()

        # Open the FLEx project
        print("[INFO] Opening FLEx project database...")
        proj = FlexProject()
        proj.OpenProject(str(project_path))

        if not proj.IsProjectOpen():
            print("[ERROR] Failed to open FLEx project")
            sys.exit(1)

        print(f"[OK] Opened project: {proj.ProjectName()}")

        # Gather FLEx data
        print("[INFO] Extracting linguistic data from FLEx...")

        # Build configuration map
        configMap = {
            'SourceLanguageCode': proj.LangCodeForLangName(proj.SourceLanguageName()),
            'TargetLanguageCode': proj.LangCodeForLangName(proj.TargetLanguageName()),
        }

        # Get start data
        startData = GetRuleAssistantStartData(report, proj, proj, configMap)

        # Get test data
        testData = GetTestDataFile(report, proj, configMap)

        # Write data to temporary files
        import tempfile
        tmpdir = tempfile.gettempdir()
        flex_data_file = os.path.join(tmpdir, 'flex_data.xml')
        test_data_file = os.path.join(tmpdir, 'test_data.xml')

        startData.write(flex_data_file)
        if testData:
            testData.write(test_data_file)

        print(f"[OK] Extracted FLEx data")
        print(f"[INFO] Source language: {proj.SourceLanguageName()}")
        print(f"[INFO] Target language: {proj.TargetLanguageName()}")

        # Close FLEx project (we're done extracting data)
        proj.CloseProject()

        # Launch the Rule Assistant GUI
        print("[INFO] Launching Rule Assistant GUI...")
        from PyQt6.QtWidgets import QApplication
        from flextrans_integration import start_rule_assistant

        app = QApplication(sys.argv)

        saved, rule_index, launch_lrt = start_rule_assistant(
            rule_file=args.rules,
            flex_data_file=flex_data_file,
            test_data_file=test_data_file,
            came_from_lrt=False,
            ui_lang_code='en'
        )

        if saved:
            print(f"[OK] Rules saved successfully")
            print(f"[INFO] Rule index: {rule_index}")

            # Re-open FLEx to generate transfer rules
            print("[INFO] Generating Apertium transfer rules...")
            proj = FlexProject()
            proj.OpenProject(str(project_path))

            # Create transfer rules file path
            transfer_rules_file = project_path.parent / 'transfer_rules.xml'

            # Generate rules (this calls CreateApertiumRules)
            ruleCount = CreateApertiumRules.CreateRules(
                proj, proj, report, configMap,
                args.rules, str(transfer_rules_file),
                rule_index
            )

            if ruleCount:
                print(f"[OK] Generated {ruleCount} transfer rules")
                print(f"[OK] Rules saved to: {transfer_rules_file}")
            else:
                print("[WARN] No transfer rules were generated")

            proj.CloseProject()
        else:
            print("[INFO] No changes were saved")

        sys.exit(0)

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
