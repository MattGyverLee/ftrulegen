"""Root conftest.py for pytest configuration."""

import sys
from pathlib import Path

# Add repo root to the Python path so src_py can be imported as a package
repo_root = Path(__file__).parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
