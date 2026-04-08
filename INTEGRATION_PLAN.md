# FLExTrans Rule Assistant Python Integration Plan - VANILLA VERSION

## Current Toolchain State (Vanilla FLExTrans 3.15.1)

### 1. **FLExTrans.py** (Entry Point)
- **Status**: ❌ NO QtWebEngine initialization
- Simple launcher: just imports and calls `main()` from flextoolslib

### 2. **FLExTransMenu.py** (Menu System)
- **Status**: ❌ NO QWebEngineWidgets imports
- Only imports: QApplication, QCoreApplication
- Does NOT prepare for web engine usage

### 3. **RuleAssistant.py** (Currently Calls Java EXE)
- **Location**: `D:\Apps\FLExTrans\FlexTools\Modules\FLExTrans\RuleAssistant.py`
- **Status**: Calls subprocess to Java EXE (lines 441-473)
- **Function**: `StartRuleAssistant(report, ruleAssistantFile, ruleAssistGUIinputfile, testDataFile, fromLRT=False)`
- **Return Format**: `(saved: bool, rule_index: Optional[int], launch_lrt: bool)`

## Key Difference from Modified Version

The vanilla version does **NOT** have WebEngine infrastructure setup. We must add it ourselves.

## Integration Architecture - REVISED

### Why QtWebEngine Initialization is Critical

PyQt6's QtWebEngineWidgets has special requirements:
1. **QtWebEngine.initialize()** must be called early in application startup
2. QWebEngineWidgets must be imported BEFORE any QWebEngineView is created
3. Failure to do this causes crashes or hangs when trying to create QWebEngineView

### Solution: Add WebEngine Setup to RuleAssistant.py

Since neither FLExTrans.py nor FLExTransMenu.py initialize WebEngine, we add it to RuleAssistant.py **at module load time** (not in StartRuleAssistant function).

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

### Step 2: Update RuleAssistant.py - Import WebEngine Modules
**File**: `D:\Apps\FLExTrans\FlexTools\Modules\FLExTrans\RuleAssistant.py`
**Location**: After line 98 (after initial translations setup, before other imports)

```python
# Pre-import QWebEngine modules at module load time
# Modern PyQt6 (6.10.2+) handles initialization automatically, no explicit QtWebEngine.initialize() needed
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
    from PyQt6.QtWebChannel import QWebChannel  # noqa: F401
except ImportError:
    # If imports fail, fallback to Java EXE will work
    pass

# Import our Python Rule Assistant module
import sys
from pathlib import Path

_ra_lib_path = Path(__file__).parent / 'RuleAssistantLib'
if _ra_lib_path.exists():
    sys.path.insert(0, str(_ra_lib_path))
    try:
        from flextrans_integration import start_rule_assistant
        _HAS_PYTHON_RA = True
    except ImportError:
        _HAS_PYTHON_RA = False
else:
    _HAS_PYTHON_RA = False
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

    # Try Python version first (WebEngine initialized at module load time)
    if _HAS_PYTHON_RA:
        try:
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
            # Log but fall through to Java version
            report.Warning(_translate('RuleAssistant',
                'Python Rule Assistant failed: {error}. Falling back to Java version.').format(error=str(e)))

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
- [ ] Add QtWebEngine initialization code at module load (Step 2)
- [ ] Replace StartRuleAssistant() function (Step 3)
- [ ] Test opening Rule Assistant from FlexTools GUI (Tools menu)
- [ ] Test adding/editing rules
- [ ] Test with German-Swedish project
- [ ] Verify fallback to Java version if Python version fails
- [ ] Test that no crashes occur on exit
- [ ] Test with at least 2 different FLEx projects

## Key Design Decisions

### Why Module-Load-Time Initialization?
- QApplication may already exist when StartRuleAssistant() is called
- QtWebEngine.initialize() must happen early, before WebEngine is used
- Importing QWebEngineWidgets at module load ensures it's available

### Why Fallback to Java EXE?
- Ensures backwards compatibility
- If our module has any issues, users can still use the Java version
- No risk of complete breakage

### Why Not Modify FLExTrans.py?
- Not our code - vanilla version
- Changes there might affect other modules
- Better to keep changes localized to RuleAssistant.py

## Success Criteria

✓ Rule Assistant opens from FlexTools Tools menu
✓ Grammar tree displays with boxes and connector lines
✓ Can add/edit words, categories, features
✓ Changes save to XML correctly
✓ No crashes on normal operations
✓ Graceful fallback if Python version has issues
✓ Java EXE still works if needed

## Risk Assessment

**Low Risk** because:
- WebEngine module imports are defensive (try/except)
- Fallback to Java EXE always available
- No changes to external APIs
- No changes to other modules
- Return format unchanged

## WebEngine Compatibility with FLExTrans/FlexTools

**PyQt6 Version in Use**: 6.10.2
**QWebEngine Status**: ✓ Available and auto-initialized

Modern PyQt6 (6.10.2+) automatically initializes WebEngine when modules are imported. There is **no need** to call `QtWebEngine.initialize()` like in older versions (PyQt5/early PyQt6).

**Verified working**:
- ✓ `from PyQt6.QtWebEngineWidgets import QWebEngineView`
- ✓ `from PyQt6.QtWebChannel import QWebChannel`
- ✓ Creating `QWebEngineView()` directly without pre-initialization
- ✓ No explicit `QtWebEngine.initialize()` call required

**Import recommendation** (Step 2):
Simply import the modules at RuleAssistant.py module load time; Python handles the rest:
```python
from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
from PyQt6.QtWebChannel import QWebChannel  # noqa: F401
```
