import os
import platform
import sys
from pathlib import Path

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
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        lib_patterns = [
            f"libpython{py_version}.so*",
            f"libpython{py_version}m.so*",
            "libcurl.so*",
            "libarchive.so*",
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

        # Check for homebrew libarchive path
        homebrew_lib_paths = [
            '/opt/homebrew/opt/libarchive/lib',
            '/usr/local/opt/libarchive/lib',
        ]
        for lib_path in homebrew_lib_paths:
            if os.path.exists(lib_path) and lib_path not in lib_dirs:
                lib_dirs.append(lib_path)
                print(f"Added homebrew libarchive path: {lib_path}")

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

# Use icons if they exist, otherwise fallback to SVG
icon_file_ico = assets_ico if os.path.exists(assets_ico) else icon_file  # Windows
icon_file_icns = assets_icns if os.path.exists(assets_icns) else icon_file  # macOS

# Ensure assets directory exists
os.makedirs('assets', exist_ok=True)



# Log icon availability
print(f"SVG icon exists: {os.path.exists(icon_file)}")
print(f"ICO icon exists: {os.path.exists(assets_ico)}")
print(f"ICNS icon exists: {os.path.exists(assets_icns)}")
print(f"PNG icon exists: {os.path.exists(assets_png)}")
print(f"Using ICO: {icon_file_ico} (exists: {os.path.exists(icon_file_ico)})")
print(f"Using ICNS: {icon_file_icns} (exists: {os.path.exists(icon_file_icns)})")

# Platform specific configurations
PLATFORM_CONFIG = {
    'linux': {
        'upx': False,
        'console': False,
        'disable_windowed_traceback': False,
        'icon': assets_png if os.path.exists(assets_png) else icon_file,
    },
    'windows': {
        'upx': False,
        'console': False,  # Disable console for end users
        'disable_windowed_traceback': False,
        'icon': icon_file_ico,
    },
    'darwin': {
        'upx': False,
        'console': False,
        'disable_windowed_traceback': False,
        'icon': icon_file_icns,
        'onefile': False,  # Force onedir mode for macOS
    }
}

# Platform-specific exclusions
excludes_per_platform = {
    'windows': ['fcntl', 'grp', 'pwd', 'termios'],
    'linux': ['winsound', 'msvcrt'],
    'darwin': ['winsound', 'msvcrt', 'fcntl'],
}

# Essential hidden imports - let PyInstaller auto-discover the rest
HIDDEN_IMPORTS = [
    # Core PyQt6 modules (minimal set)
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.sip',

    # Application-specific modules
    'pycurl',
    'libarchive',
    'libarchive.public',
    'libarchive.extract',
    'libarchive.write',
    'libarchive.read',
    'libarchive.entry',
    'libarchive.ffi',
    'libarchive.callback',
    'json',
    'configparser',
    'platform',
    'shutil',
    'tempfile',
    'datetime',
    'urllib.parse',
    'typing_extensions',
    'zipfile',
    'threading',
    'queue',

    # Your application modules
    'src.ui.workers.update_worker',
    'src.ui.workers.url_import_worker',
    'src.ui.dialogs.update_dialog',
    'src.ui.dialogs.loading_dialog',
    'src.ui.dialogs.welcome_dialog',
    'src.application.update_service',
    'src.infrastructure.github_api',
    'src.infrastructure.gitlab_api',
]

# Add platform-specific PyQt6 modules only if needed
if get_platform() == 'linux':
    HIDDEN_IMPORTS.append('PyQt6.QtDBus')
elif get_platform() == 'darwin':
    # Add extra libarchive modules for macOS
    HIDDEN_IMPORTS.extend([
        'libarchive.ffi',
        'libarchive.callback',
        'libarchive.entry',
    ])

# Modules to exclude
EXCLUDES = [
    'tkinter',
    'unittest',
    'email',
    'html',
    'http',
    'xml',
    'pydoc',
    'doctest',
    '_testcapi',
    'distutils',
    'pkg_resources',
    'PIL',
    'numpy',
    'pandas',
    'matplotlib',
    'scipy',
    # Don't exclude these - ensure all libarchive components are included
    # 'libarchive', 
    # 'libarchive.public',
    # 'libarchive.extract',
    # 'libarchive.write',
    # 'libarchive.read',
]

# Add platform-specific exclusions
platform_exclusions = excludes_per_platform.get(get_platform(), [])
if platform_exclusions:
    print(f"Adding platform-specific exclusions for {get_platform()}: {platform_exclusions}")
    EXCLUDES.extend(platform_exclusions)

# Explicitly exclude problematic PyQt6 modules on macOS to avoid framework conflicts
if get_platform() == 'darwin':
    problem_modules = ['PyQt6.QtBluetooth', 'PyQt6.QtNfc', 'PyQt6.QtPositioning', 'PyQt6.QtWebEngine']
    for module in problem_modules:
        if module not in EXCLUDES:
            EXCLUDES.append(module)
    print(f"Added PyQt6 exclusions for macOS: {[m for m in EXCLUDES if m.startswith('PyQt6.Qt')]}")

# Collect data files and binaries
datas = []
binaries = []

# Include Bricolage Grotesque font files
font_dir = os.path.join('src', 'ui', 'style', 'fonts')
if os.path.exists(font_dir):
    for fname in os.listdir(font_dir):
        if fname.lower().endswith('.ttf') or fname.lower().endswith('.otf'):
            datas.append((os.path.join(font_dir, fname), 'src/ui/style/fonts'))

# Include all the application icons from assets directory
for icon_name in ['icon.svg', 'icon.ico', 'icon.icns', 'icon.png', 'icon_512.png']:
    icon_path = os.path.join('assets', icon_name)
    if os.path.exists(icon_path):
        datas.append((icon_path, 'assets'))
        print(f"Added {icon_path} to build data files")

# Add platform-specific libraries
binaries.extend(get_platform_libraries())

# Let PyInstaller handle its own build directory management
# Aggressive cleanup can interfere with PyInstaller's internal processes

# Add project path to sys.path to help PyInstaller find dependencies
sys.path.insert(0, os.path.abspath('.'))

# Platform-specific path modifications
if get_platform() == 'linux':
    if 'LD_LIBRARY_PATH' in os.environ:
        paths = os.environ['LD_LIBRARY_PATH'].split(':')
        for path in paths:
            if path not in sys.path and os.path.exists(path):
                sys.path.append(path)
elif get_platform() == 'darwin':
    sys.path.append('/Library/Frameworks')
    sys.path.append(os.path.expanduser('~/Library/Frameworks'))

print(f"Total hidden imports: {len(HIDDEN_IMPORTS)}")
print(f"Total exclusions: {len(EXCLUDES)}")
print(f"Total data files: {len(datas)}")
print(f"Total binaries: {len(binaries)}")

# Add PKG_CONFIG_PATH for libarchive on macOS
if get_platform() == 'darwin':
    pkg_config_paths = [
        "/opt/homebrew/opt/libarchive/lib/pkgconfig",
        "/usr/local/opt/libarchive/lib/pkgconfig"
    ]
    for pkg_path in pkg_config_paths:
        if os.path.exists(pkg_path):
            os.environ['PKG_CONFIG_PATH'] = pkg_path
            print(f"Set PKG_CONFIG_PATH to {pkg_path}")
            break

a = Analysis(
    ['src/launcher.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    cipher=None,
    noarchive=False,
    # Add more debug info
    log_level='DEBUG',
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
)

# Determine if we're using onefile mode for this platform
use_onefile = True
if get_platform() == 'darwin':
    # macOS requires onedir mode to avoid framework conflicts
    use_onefile = False
    print("macOS: Using onedir mode to avoid framework conflicts")

exe = EXE(
    pyz,
    a.scripts,
    # Only include binaries, zipfiles, and datas for onefile mode
    a.binaries if use_onefile else [],
    a.zipfiles if use_onefile else [],
    a.datas if use_onefile else [],
    [],
    name='userchrome-loader',
    debug=False,  # Disable debug for production builds
    bootloader_ignore_signals=False,
    strip=False,  # Keep symbols for better error reporting
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    **PLATFORM_CONFIG[get_platform()]
)

# macOS app bundle creation
if get_platform() == 'darwin':
    # Check icon for macOS
    if not os.path.exists(icon_file_icns):
        print(f"Warning: No ICNS icon found. App will use default icon.")
        PLATFORM_CONFIG['darwin']['icon'] = None
    elif not icon_file_icns.endswith('.icns'):
        print(f"Note: Using SVG icon for macOS. For best results, generate a proper .icns file.")

    # Define app bundle info
    app_info = {
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13.0',
        'CFBundleDisplayName': 'UserChrome Loader',
        'CFBundleExecutable': 'userchrome-loader',
        'CFBundleIdentifier': 'com.orbital.userchrome-loader',
        'CFBundleName': 'UserChrome Loader',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'LSApplicationCategoryType': 'public.app-category.utilities',
        # Add additional settings to avoid QtBluetooth framework issues
        'NSBluetoothAlwaysUsageDescription': 'This app does not use Bluetooth',
        'NSBluetoothPeripheralUsageDescription': 'This app does not use Bluetooth',
    }

    # Create macOS app bundle
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='userchrome-loader.app',
        icon=icon_file_icns,
        bundle_identifier='com.orbital.userchrome-loader',
        info_plist=app_info,
    )
