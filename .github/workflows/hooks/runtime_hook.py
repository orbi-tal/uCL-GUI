import os
import sys

def collect_ucrt_dlls():
    """Runtime hook for UCRT DLLs to ensure Windows compatibility"""
    print("Runtime hook for UCRT DLLs executed successfully")
    
    # Add Windows System32 to PATH if needed
    if sys.platform == "win32":
        system32_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
        if system32_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = system32_path + os.pathsep + os.environ.get("PATH", "")

# Call function when hook is loaded
collect_ucrt_dlls()