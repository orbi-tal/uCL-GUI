# This file marks the directory as a Python package
# It enables direct imports from the src module
import sys
import os

# Add the parent directory to sys.path to allow both forms of imports:
# 1. from src.module import X
# 2. from module import X
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Enable absolute imports for all modules
__path__ = [os.path.dirname(os.path.abspath(__file__))]