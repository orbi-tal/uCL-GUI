# libarchive Dependency Fix

This document explains the fix for the `ModuleNotFoundError: No module named 'libarchive.public'` error that was occurring when running the PyInstaller-packaged application.

## Problem

When launching the compiled executable, the application was failing with the following error:

```
Traceback (most recent call last):
  File "gui.py", line 32, in <module>
  File "PyInstaller/loader/pyimod02_importers.py", line 384, in exec_module
  File "main.py", line 14, in <module>
ModuleNotFoundError: No module named 'libarchive.public'
[PYI-57531:ERROR] Failed to execute script 'gui' due to unhandled exception!
```

This error occurred because the `libarchive-c` Python package wasn't being correctly bundled with PyInstaller.

## Solution: Make libarchive Optional

Rather than trying to fix the complex dependency issues with libarchive across different platforms, we've made libarchive completely optional. The application now relies on Python's built-in modules:

1. `zipfile` for handling `.zip` and `.xpi` files
2. `tarfile` for handling `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, and `.tbz2` files

### Changes Made:

1. **Modified `src/core/archive.py`**:
   - Made libarchive import optional with a fallback mechanism
   - Added improved error handling with descriptive messages
   - Added fallback to zipfile for handling Firefox extensions (.xpi files)
   - Application can now function fully without libarchive

2. **Updated GitHub Actions workflow**:
   - Made libarchive installation optional and non-blocking
   - Removed complex configuration steps for macOS

3. **Updated PyInstaller configuration**:
   - Removed explicit libarchive dependencies from main.spec
   - Simplified the build process across all platforms

## Benefits of This Approach

1. **Cross-platform compatibility**: The application now works consistently across all platforms
2. **Simplified build process**: No need for complex system-level dependencies
3. **Reduced maintenance**: Fewer potential points of failure in the build pipeline
4. **Still supports all required formats**: All critical archive formats are handled using built-in Python modules

## Testing

To verify this fix:

1. Build the application on any platform
2. Test extracting Firefox extensions (.xpi files)
3. Test extracting .zip files
4. Test extracting .tar.gz files

## Future Improvements

If advanced archive format support (like .7z or .rar) becomes necessary in the future, we can:

1. Add a more user-friendly warning message when attempting to open these formats
2. Create a separate optional plugin system for enhanced archive support
3. Include instructions for users who need to handle these formats

## References

- [Python zipfile documentation](https://docs.python.org/3/library/zipfile.html)
- [Python tarfile documentation](https://docs.python.org/3/library/tarfile.html)
- [PyInstaller documentation](https://pyinstaller.readthedocs.io/en/stable/)