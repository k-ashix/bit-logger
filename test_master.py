"""
Bit-Logger Master Test Runner & Architectural Auditor Entrypoint
Directly invokes test_helper_scripts/test_master.py
"""

import sys
import os

# Add repo root and test_helper_scripts to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from test_helper_scripts.test_master import main

if __name__ == "__main__":
    main()
