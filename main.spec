import os
import platform
import sys
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

# Simplified Analysis - let PyInstaller handle dependencies automatically
a = Analysis(
    ['src/launcher.py'],
    pathex=[],
    binaries=[],  # Let PyInstaller auto-detect binaries
    datas=[
        # Include all assets
        ('assets', 'assets'),
        # Include style files
        ('src/ui/style/*.py', 'src/ui/style'),
        ('src/ui/style/fonts', 'src/ui/style/fonts'),
    ],
    exclude_binaries=False,
    win_private_assemblies=False,  # Let Windows handle assemblies
    hiddenimports=[
        # PyQt6 core modules
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
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

# Platform-specific executable configuration
if get_platform() == 'darwin':
    # macOS: Create app bundle
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
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_file,
    )

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
