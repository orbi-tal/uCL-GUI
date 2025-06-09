import os
import platform
import sys
import site
from pathlib import Path

def get_platform():
    return platform.system().lower()

# Icon paths for different platforms
icon_file = None
assets_ico = os.path.join('assets', 'icon.ico')
assets_icns = os.path.join('assets', 'icon.icns')
assets_png = os.path.join('assets', 'icon.png')

# Platform-specific icon selection
if get_platform() == 'windows' and os.path.exists(assets_ico):
    icon_file = assets_ico
elif get_platform() == 'darwin' and os.path.exists(assets_icns):
    icon_file = assets_icns
elif os.path.exists(assets_png):
    icon_file = assets_png

print(f"Using icon: {icon_file}")

# PyInstaller Analysis configuration
block_cipher = None

# Get site-packages path for all platforms
try:
    site_packages = site.getsitepackages()[0]
    pyqt_path = os.path.join(site_packages, 'PyQt6')
    print(f"Site packages path: {site_packages}")
    print(f"PyQt6 path: {pyqt_path}")
except Exception as e:
    print(f"Error getting site packages: {e}")
    # Fallback for any platform
    if hasattr(sys, 'prefix'):
        site_packages = os.path.join(sys.prefix, 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages')
        pyqt_path = os.path.join(site_packages, 'PyQt6')
        print(f"Using fallback site packages path: {site_packages}")

# On macOS, try to locate Qt plugins in different locations
if get_platform() == 'darwin':
    qt_plugins_paths = [
        os.path.join(pyqt_path, 'Qt6', 'plugins'),
        os.path.join(pyqt_path, 'Qt', 'plugins'),
        os.path.join(site_packages, 'PyQt6', 'Qt', 'plugins'),
        os.path.join(site_packages, 'PyQt6', 'Qt6', 'plugins'),
    ]
    
    for path in qt_plugins_paths:
        if os.path.exists(path):
            print(f"Found Qt plugins at: {path}")
            os.environ['QT_PLUGIN_PATH'] = path
            break

# Add debugging information for all platforms
print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"OS: {get_platform()}")

# Simplified Analysis - let PyInstaller handle dependencies automatically
a = Analysis(
    ['src/launcher.py'],
    pathex=[],
    binaries=[],  # Empty list is safer - we'll handle platform-specific binaries below
    datas=[
        # Include all assets
        ('assets', 'assets'),
        # Include style files
        ('src/ui/style/*.py', 'src/ui/style'),
        ('src/ui/style/fonts', 'src/ui/style/fonts'),
        # Include Qt plugins for macOS
        (os.path.join(pyqt_path, 'Qt6', 'plugins', 'platforms'), 'PyQt6/Qt6/plugins/platforms') if os.path.exists(os.path.join(pyqt_path, 'Qt6', 'plugins', 'platforms')) and get_platform() == 'darwin' else (),
        (os.path.join(pyqt_path, 'Qt6', 'plugins', 'styles'), 'PyQt6/Qt6/plugins/styles') if os.path.exists(os.path.join(pyqt_path, 'Qt6', 'plugins', 'styles')) and get_platform() == 'darwin' else (),
        (os.path.join(pyqt_path, 'Qt6', 'plugins', 'imageformats'), 'PyQt6/Qt6/plugins/imageformats') if os.path.exists(os.path.join(pyqt_path, 'Qt6', 'plugins', 'imageformats')) and get_platform() == 'darwin' else (),
    ],
    exclude_binaries=False,
    # Platform-specific configuration
    hiddenimports=[
        # PyQt6 core modules
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtSvg',
        'PyQt6.QtPrintSupport',
        'PyQt6.sip',

        # Application modules
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

        # Core modules
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
    runtime_hooks=['runtime_hook.py'] if os.path.exists('runtime_hook.py') else [],
    excludes=[
        # Exclude unnecessary modules
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,  # Let Windows handle assemblies
    cipher=block_cipher,
    noarchive=False,
)

# Configure the PYZ archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Platform-specific executable configuration
if get_platform() == 'darwin':
    # macOS: Create app bundle with more debugging and fixes for Qt
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='userchrome-loader',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,  # Disable UPX on macOS
        console=False,  # Set to False for production (no terminal window)
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_file,
    )

    # Add explicit plugins and frameworks for Qt on macOS
    extra_binaries = []
    try:
        # Look for Qt plugins in multiple possible locations
        possible_qt_roots = [
            os.path.join(pyqt_path, 'Qt6'),
            os.path.join(pyqt_path, 'Qt'),
            os.path.join(site_packages, 'PyQt6', 'Qt6'),
            os.path.join(site_packages, 'PyQt6', 'Qt'),
        ]
        
        # Plugin categories we need
        plugin_categories = ['platforms', 'styles', 'imageformats', 'iconengines']
        
        # Try each possible Qt root
        for qt_root in possible_qt_roots:
            plugin_dir = os.path.join(qt_root, 'plugins')
            if os.path.exists(plugin_dir):
                print(f"Found Qt plugins directory: {plugin_dir}")
                for category in plugin_categories:
                    category_dir = os.path.join(plugin_dir, category)
                    if os.path.exists(category_dir):
                        print(f"Found {category} plugins at: {category_dir}")
                        for item in os.listdir(category_dir):
                            if item.endswith('.dylib'):
                                source_item = os.path.join(category_dir, item)
                                if os.path.isfile(source_item):
                                    print(f"Adding Qt plugin: {item} from {source_item} to {category}")
                                    extra_binaries.append((source_item, category))
    except Exception as e:
        print(f"Warning: Failed to collect Qt plugins: {e}")

    # Safe collect - handle the case where extra_binaries might be empty or invalid
    try:
        coll = COLLECT(
            exe,
            a.binaries,
            a.zipfiles,
            a.datas,
            extra_binaries,
            strip=False,
            upx=False,
            upx_exclude=[],
            name='userchrome-loader'
        )
    except Exception as e:
        print(f"Warning: Error during COLLECT with extra_binaries: {e}")
        # Fallback without extra_binaries
        coll = COLLECT(
            exe,
            a.binaries,
            a.zipfiles,
            a.datas,
            strip=False,
            upx=False,
            upx_exclude=[],
            name='userchrome-loader'
        )

    app = BUNDLE(
        coll,
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
            'NSPrincipalClass': 'NSApplication',
            'CFBundleDocumentTypes': [],
            'LSEnvironment': {
                'QT_PLUGIN_PATH': '../Resources/PyQt6/Qt6/plugins',
                'QT_QPA_PLATFORM_PLUGIN_PATH': '../Resources/PyQt6/Qt6/plugins/platforms',
            },
        },
    )

else:
    # Windows/Linux: Create single executable
    try:
        # Platform-specific configurations
        if get_platform() == 'linux':
            console_mode = False  # GUI mode for Linux
            strip_mode = False    # Don't strip symbols on Linux for better error reporting
            upx_mode = False      # Disable UPX on Linux to avoid compatibility issues
        else:  # Windows
            console_mode = False  # GUI mode for Windows
            strip_mode = False    # Don't strip symbols on Windows
            upx_mode = True       # UPX is generally safe on Windows
            
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
            strip=strip_mode,
            upx=upx_mode,
            upx_exclude=[
                # Don't compress graphics libraries
                'libGL.so*',
                'libGLX.so*',
                'libEGL.so*',
                'libGLU.so*',
                'libxcb*.so*',
                'libxkb*.so*',
                # Don't compress DLLs on Windows
                '*.dll',
            ],
            runtime_tmpdir=None,
            console=console_mode,
            disable_windowed_traceback=False,
            target_arch=None,
            codesign_identity=None,
            entitlements_file=None,
            icon=icon_file,
        )
    except Exception as e:
        print(f"Error during EXE creation: {e}")
        # Fallback with minimal options
        exe = EXE(
            pyz,
            a.scripts,
            a.binaries,
            a.zipfiles,
            a.datas,
            [],
            name='userchrome-loader',
            debug=False,
            strip=False,
            upx=False,
            runtime_tmpdir=None,
            console=True,  # Enable console for debugging in fallback mode
            icon=icon_file,
        )
