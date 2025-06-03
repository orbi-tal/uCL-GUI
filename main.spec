import os
import platform
import sys
from pathlib import Path
from PyInstaller.building.api import BUNDLE, EXE, PYZ, COLLECT, MERGE
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all, collect_submodules

def get_platform():
    return platform.system().lower()

def get_platform_libraries():
    """Get platform-specific libraries that need to be explicitly included"""
    platform_name = get_platform()
    binaries = []

    if platform_name == 'windows':
        # Windows: Include Python DLL and runtime libraries
        py_version = f"{sys.version_info.major}{sys.version_info.minor}"
        required_dlls = [
            # Python core DLLs
            f'python{py_version}.dll',

            # Microsoft Visual C++ Runtime DLLs
            'vcruntime140.dll',
            'vcruntime140_1.dll',  # Required for 64-bit apps
            'msvcp140.dll',

            # Universal C Runtime DLLs
            'ucrtbase.dll',
            'api-ms-win-crt-runtime-l1-1-0.dll',
            'api-ms-win-crt-heap-l1-1-0.dll',
            'api-ms-win-crt-math-l1-1-0.dll',
            'api-ms-win-crt-stdio-l1-1-0.dll',
            'api-ms-win-crt-locale-l1-1-0.dll',
            'api-ms-win-crt-string-l1-1-0.dll',
            'api-ms-win-crt-convert-l1-1-0.dll',
            'api-ms-win-crt-filesystem-l1-1-0.dll',
            'api-ms-win-crt-environment-l1-1-0.dll',
            'api-ms-win-crt-process-l1-1-0.dll',
            'api-ms-win-crt-time-l1-1-0.dll',
            'api-ms-win-crt-utility-l1-1-0.dll',
        ]

        # Search paths for Windows DLLs, ordered by priority
        search_paths = [
            os.path.dirname(sys.executable),
            sys.base_prefix,
            os.path.join(sys.base_prefix, 'DLLs'),
            os.path.join(sys.base_prefix, 'Library', 'bin'),
            os.environ.get('SYSTEMROOT', ''),
            os.path.join(os.environ.get('SYSTEMROOT', ''), 'System32'),
            os.path.join(os.environ.get('SYSTEMROOT', ''), 'SysWOW64'),
        ]

        # Track DLLs we've already found to avoid duplicates
        found_dlls = set()

        # Find all required DLLs
        for dll in required_dlls:
            if dll in found_dlls:
                continue

            for path in search_paths:
                if not path:
                    continue

                dll_path = Path(path) / dll
                if dll_path.exists():
                    print(f"Found DLL: {dll_path}")
                    binaries.append((str(dll_path), '.'))
                    found_dlls.add(dll)
                    break

        print(f"Total Windows DLLs found: {len(binaries)}")

    elif platform_name == 'linux':
            # Linux: Include libpython and other critical libraries
            # Note: When building for AppImage, most library dependencies will be handled by the AppImage format
            py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            lib_patterns = [
                f"libpython{py_version}.so*",
                f"libpython{py_version}m.so*",
                "libcurl.so*",
                "libarchive.so*",
                "libEGL.so*",  # Add EGL library for PyQt6
            ]

        # Common library locations on Linux
        lib_dirs = [
            os.path.join(sys.base_prefix, 'lib'),
            '/usr/lib',
            '/usr/lib64',
            '/lib',
            '/lib64',
            '/usr/local/lib',
        ]

        # Add more paths from environment if available
        if 'DYLD_LIBRARY_PATH' in os.environ:
            for path in os.environ['DYLD_LIBRARY_PATH'].split(':'):
                if path and path not in lib_dirs:
                    lib_dirs.append(path)

        # Standard library paths should be sufficient

        # Find libraries using glob patterns
        import glob
        for lib_dir in lib_dirs:
            if not os.path.exists(lib_dir):
                continue

            for pattern in lib_patterns:
                for lib_path in glob.glob(os.path.join(lib_dir, pattern)):
                    if os.path.isfile(lib_path) and os.access(lib_path, os.R_OK):
                        print(f"Found Linux library: {lib_path}")
                        binaries.append((lib_path, '.'))

        print(f"Total Linux libraries found: {len(binaries)}")

    elif platform_name == 'darwin':
        # macOS: Include Python dylib and other critical libraries
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        lib_patterns = [
            f"libpython{py_version}.dylib",
            f"libpython{py_version}m.dylib",
            "libcurl.*.dylib",
            "libarchive.*.dylib",
        ]

        # Common library locations on macOS
        lib_dirs = [
            os.path.join(sys.base_prefix, 'lib'),
            '/usr/lib',
            '/usr/local/lib',
            '/opt/homebrew/lib',
        ]

        # Add more paths from environment if available
        if 'DYLD_LIBRARY_PATH' in os.environ:
            for path in os.environ['DYLD_LIBRARY_PATH'].split(':'):
                if path and path not in lib_dirs:
                    lib_dirs.append(path)

        # Find libraries using glob patterns
        import glob
        for lib_dir in lib_dirs:
            if not os.path.exists(lib_dir):
                continue

            for pattern in lib_patterns:
                for lib_path in glob.glob(os.path.join(lib_dir, pattern)):
                    if os.path.isfile(lib_path) and os.access(lib_path, os.R_OK):
                        print(f"Found macOS library: {lib_path}")
                        binaries.append((lib_path, '.'))

        print(f"Total macOS libraries found: {len(binaries)}")

    return binaries

# Icon paths for different platforms
icon_file = os.path.join('assets', 'icon.svg')  # Default SVG icon

# Check for icons in assets directory
assets_ico = os.path.join('assets', 'icon.ico')
assets_icns = os.path.join('assets', 'icon.icns')
assets_png = os.path.join('assets', 'icon.png')

# Platform-specific icon file
if get_platform() == 'windows' and os.path.exists(assets_ico):
    icon_file = assets_ico
elif get_platform() == 'darwin' and os.path.exists(assets_icns):
    icon_file = assets_icns
elif os.path.exists(assets_png):
    icon_file = assets_png

# PyInstaller Analysis configuration
block_cipher = None

# Configure the Analysis with our runtime hook
a = Analysis(
    ['src/launcher.py'],
    pathex=[],
    binaries=get_platform_libraries(),
    datas=[
        ('assets', 'assets'),
        ('src/ui/icons', 'src/ui/icons'),
        ('src/ui/styles', 'src/ui/styles'),
    ],
    hiddenimports=[
        # Both forms of module imports
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.sip',
        'pycurl',
        'libarchive',
        # Traditional import format
        'src.ui.workers.update_worker',
        'src.ui.workers.url_import_worker',
        'src.ui.dialogs.update_dialog',
        'src.ui.dialogs.loading_dialog',
        'src.ui.dialogs.welcome_dialog',
        # Relative import format
        'src.ui.workers',
        'src.ui.dialogs',
        'src.ui.main_window',
        'src.core.config',
        'src.core.profile_manager',
        'src.core.style_manager',
        'src.core.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],  # Include our runtime hook
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Configure the PYZ archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Configure the EXE for onefile mode
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='userchrome-loader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# macOS specific configuration
if get_platform() == 'darwin':
    app = BUNDLE(
        exe,
        name='UserChrome Loader.app',
        icon=icon_file,
        bundle_identifier='com.orbital.userchrome-loader',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleExecutable': 'userchrome-loader',
            'CFBundleName': 'UserChrome Loader',
            'CFBundleDisplayName': 'UserChrome Loader',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        },
    )