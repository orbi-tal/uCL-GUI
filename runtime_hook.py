import sys
import os

# Add the project directory to Python's path
project_dir = os.path.dirname(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else os.path.abspath('.')
src_dir = os.path.join(project_dir, 'src')

# Add src directory to sys.path if it's not already there
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
    
# Add project directory to sys.path if it's not already there
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Print paths for debugging (optional)
print(f"Runtime hook: Added {project_dir} and {src_dir} to sys.path")
print(f"Full sys.path: {sys.path}")