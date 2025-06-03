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
        # Windows: Include only essential Python and runtime DLLs
        py_version = f"{sys.version_info.major}{sys.version_info.minor}"
        required_dlls = [
            # Python core DLL
            f'python{py_version}.dll',
            # Essential Microsoft Visual C++ Runtime DLLs
            'vcruntime140.dll',
            'msvcp140.dll',
        ]

        # Simplified search paths for Windows DLLs
        search_paths = [
            os.path.dirname(sys.executable),
            os.path.join(sys.base_prefix, 'DLLs'),
            os.path.join(os.environ.get('SYSTEMROOT', ''), 'System32'),
        ]

        # Find required DLLs
        for dll in required_dlls:
            for path in search_paths:
                if not path:
                    continue
                dll_path = Path(path) / dll
                if dll_path.exists():
                    print(f"Found DLL: {dll_path}")
                    binaries.append((str(dll_path), '.'))
                    break

        print(f"Total Windows DLLs found: {len(binaries)}")

    elif platform_name == 'linux':
        # Linux: Let PyInstaller handle most dependencies automatically
        # Only include critical libraries that are commonly missed
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        import glob
        lib_dirs = [
            os.path.join(sys.base_prefix, 'lib'),
            '/usr/lib/x86_64-linux-gnu',
            '/usr/lib',
        ]

        # Only look for Python shared library if needed
        for lib_dir in lib_dirs:
            if not os.path.exists(lib_dir):
                continue

            for lib_path in glob.glob(os.path.join(lib_dir, f"libpython{py_version}*.so*")):
                if os.path.isfile(lib_path):
                    print(f"Found Linux library: {lib_path}")
                    binaries.append((lib_path, '.'))
                    break

        print(f"Total Linux libraries found: {len(binaries)}")

    elif platform_name == 'darwin':
        # macOS: Let PyInstaller handle most dependencies
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        import glob
        lib_dirs = [
            os.path.join(sys.base_prefix, 'lib'),
            '/usr/local/lib',
            '/opt/homebrew/lib',
        ]

        # Only look for Python dylib if needed
        for lib_dir in lib_dirs:
            if not os.path.exists(lib_dir):
                continue

            for lib_path in glob.glob(os.path.join(lib_dir, f"libpython{py_version}*.dylib")):
                if os.path.isfile(lib_path):
                    print(f"Found macOS library: {lib_path}")
                    binaries.append((lib_path, '.'))
                    break

        print(f"Total macOS libraries found: {len(binaries)}")

    return binaries

# Icon paths for different platforms
icon_file = None

# Check for platform-specific icons first
assets_ico = os.path.join('assets', 'icon.ico')
assets_icns = os.path.join('assets', 'icon.icns')
assets_png = os.path.join('assets', 'icon.png')
assets_svg = os.path.join('assets', 'icon.svg')

# Platform-specific icon selection
if get_platform() == 'windows' and os.path.exists(assets_ico):
    icon_file = assets_ico
elif get_platform() == 'darwin' and os.path.exists(assets_icns):
    icon_file = assets_icns
elif os.path.exists(assets_png):
    icon_file = assets_png
elif os.path.exists(assets_svg):
    icon_file = assets_svg

# PyInstaller Analysis configuration
block_cipher = None

# Configure the Analysis
a = Analysis(
    ['src/launcher.py'],
    pathex=[],
    binaries=get_platform_libraries(),
    datas=[
        # Include all assets
        ('assets', 'assets'),
        # Include only necessary style files
        ('src/ui/style/*.py', 'src/ui/style'),
        ('src/ui/style/fonts', 'src/ui/style/fonts'),
    ],
    exclude_binaries=False,
    hiddenimports=[
        # PyQt6 core modules
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.sip',

        # Application modules - using consistent absolute imports
        'src.launcher',
        'src.ui.main_window',
        'src.ui.workers.update_worker',
        'src.ui.workers.url_import_worker',
        'src.ui.dialogs.update_dialog',
        'src.ui.dialogs.loading_dialog',
        'src.ui.dialogs.welcome_dialog',
        'src.ui.dialogs.confirm_dialog',
        'src.ui.dialogs.css_selection_dialog',
        'src.ui.dialogs.file_dialogs',
        'src.ui.dialogs.subfolder_dialog',
        'src.ui.style.style',
        'src.ui.style.icons',
        'src.ui.style.animated_button',
        'src.ui.style.shadow_utils',
        'src.ui.presenters.main_presenter',
        'src.ui.presenters.import_presenter',
        'src.ui.presenters.manage_imports_presenter',

        # Core application modules
        'src.core.archive',
        'src.core.download',
        'src.core.exceptions',
        'src.core.mod',
        'src.core.models',
        'src.core.profile',
        'src.core.userchrome',

        # Application services
        'src.application.import_service',
        'src.application.profile_service',
        'src.application.settings',
        'src.application.update_service',

        # Infrastructure
        'src.infrastructure.config_store',
        'src.infrastructure.file_manager',
        'src.infrastructure.github_api',
        'src.infrastructure.gitlab_api',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
    ],
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

# Configure the EXE
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
    upx_exclude=[
        # Don't compress libraries that might have issues
        'libGL.so*',
        'libGLX.so*',
        'libEGL.so*',
        'libGLU.so*',
        '*.dylib',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# macOS app bundle configuration (only if building on macOS)
if get_platform() == 'darwin':
    app = BUNDLE(
        exe,
        name='UserChrome Loader.app',
        icon=icon_file,
        bundle_identifier='com.orbital.userchrome-loader',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'CFBundleExecutable': 'userchrome-loader',
            'CFBundleName': 'UserChrome Loader',
            'CFBundleDisplayName': 'UserChrome Loader',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'LSMinimumSystemVersion': '10.15.0',
        },
    )
