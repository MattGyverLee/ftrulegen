# FLExTrans Rule Assistant Python Integration Plan

## Current Toolchain State

### 1. **FLExTrans.py** (Entry Point)
- **Location**: `D:\Apps\FLExTrans\FlexTools\FLExTrans.py` (lines 29-34)
- **Status**: ✓ Already initializes QtWebEngine
```python
try:
    from PyQt6.QtWebEngineCore import QtWebEngine
    QtWebEngine.initialize()
except Exception:
    pass  # WebEngine initialization may fail, but we tried
```

### 2. **FLExTransMenu.py** (Menu System)
- **Location**: `D:\Apps\FLExTrans\FlexTools\FLExTransMenu.py` (lines 34-42)
- **Status**: ✓ Imports QWebEngineWidgets at module load time
```python
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
    from PyQt6.QtWebChannel import QWebChannel  # noqa: F401
except ImportError:
    pass  # WebEngine may not be available in all environments
```

### 3. **RuleAssistant.py** (Currently Calls Java EXE)
- **Location**: `D:\Apps\FLExTrans\FlexTools\Modules\FLExTrans\RuleAssistant.py`
- **Current Function** (lines 441-473): `StartRuleAssistant(report, ruleAssistantFile, ruleAssistGUIinputfile, testDataFile, fromLRT=False)`
- **Current Implementation**:
  - Calls subprocess to run `PROGRAMFILES\FLExTransRuleAssistant\FLExTransRuleAssistant.exe`
  - Parses stdout for return codes: "1" (single rule) or "2" (all rules)
  - Returns tuple: `(saved: bool, rule_index: Optional[int], launch_lrt: bool)`

## Integration Architecture

### The Good News
✓ WebEngine infrastructure **already in place**
✓ Both FLExTrans.py and FLExTransMenu.py import QWebEngineWidgets
✓ QApplication instance management already working
✓ Return value format matches our Python module exactly
✓ No subprocess overhead - can run in-process

### Why Previous Integration Failed
The issue was likely:
1. Our module tried to import QWebEngineWidgets in RuleAssistant.py **after** FLExTransMenu imported it
2. QWebEngineWidgets must be imported **once, at module load time, before QApplication is created**
3. By the time RuleAssistant.py ran, the import order was wrong

## Proposed Integration Solution

### Step 1: Deploy Python Module
**Copy to**: `D:\Apps\FLExTrans\FlexTools\Modules\FLExTrans\RuleAssistantLib\`

```
RuleAssistantLib/
  src_py/
    __init__.py
    constants.py
    model/
    flexmodel/
    service/
    view/
    assets/
    i18n/
    tests/
    flextrans_integration.py
```

### Step 2: Update RuleAssistant.py - Add Import at Top
**File**: `D:\Apps\FLExTrans\FlexTools\Modules\FLExTrans\RuleAssistant.py`
**Location**: After line 89 (after other imports)

```python
# CRITICAL: Import our Python module's dependencies at module load time
# This ensures QWebEngineWidgets is imported before QApplication is created
# Must happen BEFORE StartRuleAssistant() is called
try:
    import sys
    from pathlib import Path
    _ra_lib = Path(__file__).parent / 'RuleAssistantLib' / 'src_py'
    if _ra_lib.exists():
        sys.path.insert(0, str(_ra_lib.parent))
        from flextrans_integration import start_rule_assistant
        _HAS_PYTHON_RA = True
    else:
        _HAS_PYTHON_RA = False
except ImportError as e:
    _HAS_PYTHON_RA = False
    logger_or_fallback = lambda msg: None  # silent fallback
```

### Step 3: Replace StartRuleAssistant() Function
**File**: `D:\Apps\FLExTrans\FlexTools\Modules\FLExTrans\RuleAssistant.py`
**Lines**: 441-473

```python
def StartRuleAssistant(report, ruleAssistantFile, ruleAssistGUIinputfile,
                       testDataFile, fromLRT=False):
    """Launch the Rule Assistant GUI.

    First tries the new Python/PyQt6 version if available,
    falls back to Java EXE for backwards compatibility.
    """

    # Try Python version first (already imported at module load time)
    if _HAS_PYTHON_RA:
        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            lang_code = Utils.getInterfaceLangCode()
            saved, rule_index, launch_lrt = start_rule_assistant(
                rule_file=ruleAssistantFile,
                flex_data_file=ruleAssistGUIinputfile,
                test_data_file=testDataFile,
                came_from_lrt=fromLRT,
                ui_lang_code=lang_code,
            )

            return (saved, rule_index, launch_lrt)

        except Exception as e:
            report.Warning(_translate('RuleAssistant',
                'Python Rule Assistant failed: {error}. Falling back to Java version.').format(error=str(e)))
            # Fall through to Java version below

    # Fallback: Use Java EXE if Python version not available or failed
    try:
        fullRApath = os.path.join(os.environ['PROGRAMFILES'], FTPaths.RULE_ASSISTANT_DIR, FTPaths.RULE_ASSISTANT)

        params = [fullRApath, ruleAssistantFile, ruleAssistGUIinputfile,
                  testDataFile, 'y' if fromLRT else 'n', Utils.getInterfaceLangCode()]

        result = subprocess.run(params, capture_output=True)

        output = result.stdout.decode('utf-8').strip().split()
        lrt = (not fromLRT) and ('LRT' in output)

        if not output or output[0] not in ['1', '2']:
            if len(output) > 1:
                report.Error(_translate('RuleAssistant', 'An error happened when running the {ruleAssistant} tool: {error}').format(error=' '.join(output), ruleAssistant=docs[FTM_Name]))
            return (False, None, lrt)

        elif output[0] == '1':
            return (True, int(output[1]), lrt)
        else:
            return (True, None, lrt)

    except Exception as e:
        report.Error(_translate('RuleAssistant', 'An error happened when running the {ruleAssistant} tool: {error}').format(error=str(e), ruleAssistant=docs[FTM_Name]))
        return (False, None, False)
```

## Deployment Checklist

- [ ] Copy `src_py/` to `D:\Apps\FLExTrans\FlexTools\Modules\FLExTrans\RuleAssistantLib\src_py\`
- [ ] Update RuleAssistant.py with import at module level (Step 2)
- [ ] Update StartRuleAssistant() function (Step 3)
- [ ] Test opening Rule Assistant from FlexTools GUI
- [ ] Test adding/editing rules
- [ ] Test with multiple projects (German-Swedish, etc.)
- [ ] Verify fallback to Java version works if Python version fails
- [ ] Test that no crashes occur on exit

## Risk Mitigation

**Backwards Compatibility**:
- Fallback to Java EXE if Python version fails
- No changes to external APIs or return formats
- Only affects internal implementation

**WebEngine Issue Prevention**:
- Import happens at module load time (FLExTrans.py and FLExTransMenu.py already do this)
- QApplication.instance() checks for existing instance
- No attempt to create new QApplication if one already exists

## Success Criteria

✓ Rule Assistant opens from FlexTools Tools menu
✓ Grammar tree displays with boxes and connector lines
✓ Can add/edit words, categories, features
✓ Changes save to XML correctly
✓ No crashes on normal operations
✓ Graceful fallback if Python version unavailable
