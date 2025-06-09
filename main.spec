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

# Get site-packages path for macOS
site_packages = site.getsitepackages()[0]
pyqt_path = os.path.join(site_packages, 'PyQt6')

# Add debugging information for macOS
if get_platform() == 'darwin':
    print(f"PyQt6 path: {pyqt_path}")
    print(f"Site packages: {site_packages}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")

# Simplified Analysis - let PyInstaller handle dependencies automatically
a = Analysis(
    ['src/launcher.py'],
    pathex=[],
    binaries=[
        # Explicitly include Qt plugins for macOS
        (os.path.join(pyqt_path, 'Qt6', 'plugins', 'platforms', '*'), 'platforms') if get_platform() == 'darwin' else (),
        (os.path.join(pyqt_path, 'Qt6', 'plugins', 'styles', '*'), 'styles') if get_platform() == 'darwin' else (),
    ],  # Explicitly include necessary binaries for macOS
    datas=[
        # Include all assets
        ('assets', 'assets'),
        # Include style files
        ('src/ui/style/*.py', 'src/ui/style'),
        ('src/ui/style/fonts', 'src/ui/style/fonts'),
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
        console=True,  # Set to True for debugging
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_file,
    )

    # Add explicit plugins and frameworks for Qt on macOS
    extra_binaries = []
    qt_plugin_paths = [
        ('platforms', os.path.join(pyqt_path, 'Qt6', 'plugins', 'platforms')),
        ('styles', os.path.join(pyqt_path, 'Qt6', 'plugins', 'styles')),
        ('imageformats', os.path.join(pyqt_path, 'Qt6', 'plugins', 'imageformats')),
    ]
    
    for dest, src in qt_plugin_paths:
        if os.path.exists(src):
            for item in os.listdir(src):
                if item.endswith('.dylib'):
                    source_item = os.path.join(src, item)
                    if os.path.isfile(source_item):
                        print(f"Adding Qt plugin: {item} from {source_item} to {dest}")
                        extra_binaries.append((source_item, dest))

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
        },
    )

else:
    # Windows/Linux: Create single executable
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
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_file,
    )
