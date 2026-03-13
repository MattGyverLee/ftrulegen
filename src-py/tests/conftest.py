# Copyright (c) 2024-2026 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

import os
import sys

# Add src-py to path so tests can import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Test data directory (Java test data, shared)
TEST_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "test", "org", "sil", "ftrulegen", "testdata"
)
