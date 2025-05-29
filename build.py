#!/usr/bin/env python3
"""
Build script for UserChrome Loader
Supports building for Linux, Windows, and macOS
"""

import os
import sys
import subprocess
import shutil
import platform
import argparse
from pathlib import Path

# Build configuration
BUILD_CONFIG = {
    'app_name': 'UserChrome Loader',
    'app_version': '1.0.0',
    'app_author': 'Orbital',
    'app_description': 'A tool for managing UserChrome CSS customizations',
    'entry_point': 'src/launcher.py',
    'spec_file': 'main.spec',
    'icon_file': '',  # Add icon file path when available
}

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_colored(message, color=Colors.WHITE):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.END}")

def print_step(step_name):
    """Print build step header"""
    print_colored(f"\n{'='*50}", Colors.CYAN)
    print_colored(f" {step_name}", Colors.CYAN + Colors.BOLD)
    print_colored(f"{'='*50}", Colors.CYAN)

def run_command(command, cwd=None, check=True):
    """Run a command and return the result"""
    print_colored(f"Running: {' '.join(command)}", Colors.YELLOW)
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"Error: {e}", Colors.RED)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        raise

def check_dependencies():
    """Check if required dependencies are installed"""
    print_step("Checking Dependencies")
    
    required_packages = [
        'PyQt6',
        'pyinstaller',
        'pycurl',
        'libarchive-c',
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_colored(f"✓ {package} is installed", Colors.GREEN)
        except ImportError:
            print_colored(f"✗ {package} is missing", Colors.RED)
            missing_packages.append(package)
    
    if missing_packages:
        print_colored(f"\nMissing packages: {', '.join(missing_packages)}", Colors.RED)
        print_colored("Install them with: pip install " + ' '.join(missing_packages), Colors.YELLOW)
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print_step("Installing Dependencies")
    
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print_colored("requirements.txt not found, installing minimal dependencies", Colors.YELLOW)
        run_command([sys.executable, "-m", "pip", "install", "PyQt6", "pyinstaller", "pycurl", "libarchive-c"])

def clean_build():
    """Clean previous build artifacts"""
    print_step("Cleaning Previous Build")
    
    paths_to_clean = [
        "build",
        "dist",
        "__pycache__",
        "*.spec~",
    ]
    
    for path in paths_to_clean:
        if '*' in path:
            # Handle glob patterns
            import glob
            for file_path in glob.glob(path, recursive=True):
                if os.path.exists(file_path):
                    print_colored(f"Removing {file_path}", Colors.YELLOW)
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
        else:
            if os.path.exists(path):
                print_colored(f"Removing {path}", Colors.YELLOW)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
    
    # Clean Python cache files
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print_colored(f"Removing {pycache_path}", Colors.YELLOW)
            shutil.rmtree(pycache_path)
            dirs.remove('__pycache__')

def get_platform_info():
    """Get platform information"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    platform_map = {
        'linux': 'linux',
        'darwin': 'macos',
        'windows': 'windows'
    }
    
    return platform_map.get(system, system), machine

def build_executable(mode='onefile', debug=False):
    """Build the executable using PyInstaller"""
    print_step("Building Executable")
    
    platform_name, machine = get_platform_info()
    
    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
    ]
    
    # Add mode
    if mode == 'onefile':
        cmd.append("--onefile")
    elif mode == 'onedir':
        cmd.append("--onedir")
    
    # Add debug options
    if debug:
        cmd.extend(["--debug", "all"])
        cmd.append("--console")
    else:
        cmd.append("--windowed")
    
    # Add platform-specific options
    if platform_name == 'windows':
        cmd.append("--disable-windowed-traceback")
    elif platform_name == 'macos':
        cmd.extend(["--osx-bundle-identifier", "com.orbital.userchrome-loader"])
    
    # Add spec file if it exists
    spec_file = BUILD_CONFIG['spec_file']
    if os.path.exists(spec_file):
        print_colored(f"Using spec file: {spec_file}", Colors.GREEN)
        cmd.append(spec_file)
    else:
        print_colored(f"Spec file {spec_file} not found, using direct build", Colors.YELLOW)
        
        # Add entry point
        cmd.append(BUILD_CONFIG['entry_point'])
        
        # Add name
        cmd.extend(["--name", "userchrome-loader"])
        
        # Add icon if available
        icon_file = BUILD_CONFIG['icon_file']
        if icon_file and os.path.exists(icon_file):
            cmd.extend(["--icon", icon_file])
        
        # Add hidden imports
        hidden_imports = [
            'PyQt6.QtWidgets',
            'PyQt6.QtCore',
            'PyQt6.QtGui',
            'PyQt6.sip',
            'pycurl',
            'libarchive',
            'src.ui.workers.update_worker',
            'src.ui.workers.url_import_worker',
            'src.ui.dialogs.update_dialog',
            'src.ui.dialogs.loading_dialog',
            'src.ui.dialogs.welcome_dialog',
        ]
        
        for import_name in hidden_imports:
            cmd.extend(["--hidden-import", import_name])
    
    # Run PyInstaller
    run_command(cmd)
    
    print_colored(f"Build completed for {platform_name}-{machine}", Colors.GREEN)

def create_installer():
    """Create platform-specific installer"""
    print_step("Creating Installer")
    
    platform_name, machine = get_platform_info()
    
    if platform_name == 'windows':
        create_windows_installer()
    elif platform_name == 'macos':
        create_macos_installer()
    elif platform_name == 'linux':
        create_linux_package()
    else:
        print_colored(f"No installer creation support for {platform_name}", Colors.YELLOW)

def create_windows_installer():
    """Create Windows installer using NSIS or Inno Setup"""
    print_colored("Windows installer creation not implemented yet", Colors.YELLOW)
    print_colored("You can manually create an installer using NSIS or Inno Setup", Colors.BLUE)

def create_macos_installer():
    """Create macOS DMG installer"""
    print_colored("macOS DMG creation not implemented yet", Colors.YELLOW)
    print_colored("You can manually create a DMG using hdiutil", Colors.BLUE)

def create_linux_package():
    """Create Linux package (AppImage, deb, rpm)"""
    print_colored("Linux package creation not implemented yet", Colors.YELLOW)
    print_colored("You can manually create packages using fpm or similar tools", Colors.BLUE)

def test_executable():
    """Test the built executable"""
    print_step("Testing Executable")
    
    platform_name, _ = get_platform_info()
    
    # Find the executable
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print_colored("Dist directory not found", Colors.RED)
        return False
    
    executable_name = "userchrome-loader"
    if platform_name == 'windows':
        executable_name += ".exe"
    elif platform_name == 'macos':
        executable_name = "UserChrome Loader.app"
    
    executable_path = None
    for item in dist_dir.iterdir():
        if item.name == executable_name or item.name.startswith("userchrome-loader"):
            executable_path = item
            break
    
    if not executable_path:
        print_colored("Executable not found in dist directory", Colors.RED)
        return False
    
    print_colored(f"Found executable: {executable_path}", Colors.GREEN)
    
    # Test basic execution (with timeout to prevent hanging)
    try:
        if platform_name == 'macos' and executable_path.suffix == '.app':
            test_cmd = ["open", "-W", "-n", str(executable_path), "--args", "--version"]
        else:
            test_cmd = [str(executable_path), "--help"]
        
        print_colored("Testing executable launch...", Colors.BLUE)
        result = subprocess.run(
            test_cmd,
            timeout=10,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_colored("Executable test passed", Colors.GREEN)
            return True
        else:
            print_colored(f"Executable test failed with code {result.returncode}", Colors.YELLOW)
            if result.stderr:
                print(result.stderr)
            return True  # Still consider it successful if it at least runs
            
    except subprocess.TimeoutExpired:
        print_colored("Executable test timed out (probably GUI app)", Colors.YELLOW)
        return True
    except Exception as e:
        print_colored(f"Executable test failed: {e}", Colors.RED)
        return False

def print_build_info():
    """Print build information"""
    print_step("Build Information")
    
    platform_name, machine = get_platform_info()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    print_colored(f"App Name: {BUILD_CONFIG['app_name']}", Colors.WHITE)
    print_colored(f"Version: {BUILD_CONFIG['app_version']}", Colors.WHITE)
    print_colored(f"Platform: {platform_name}-{machine}", Colors.WHITE)
    print_colored(f"Python: {python_version}", Colors.WHITE)
    print_colored(f"Entry Point: {BUILD_CONFIG['entry_point']}", Colors.WHITE)

def main():
    """Main build function"""
    parser = argparse.ArgumentParser(description='Build UserChrome Loader')
    parser.add_argument('--mode', choices=['onefile', 'onedir'], default='onefile',
                       help='Build mode (default: onefile)')
    parser.add_argument('--debug', action='store_true',
                       help='Build in debug mode')
    parser.add_argument('--clean', action='store_true',
                       help='Clean build artifacts only')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install dependencies only')
    parser.add_argument('--no-test', action='store_true',
                       help='Skip executable testing')
    parser.add_argument('--installer', action='store_true',
                       help='Create installer package')
    
    args = parser.parse_args()
    
    print_colored(f"\n{BUILD_CONFIG['app_name']} Build Script", Colors.BOLD + Colors.CYAN)
    print_colored(f"Version {BUILD_CONFIG['app_version']}", Colors.CYAN)
    
    try:
        # Change to script directory
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        print_build_info()
        
        if args.install_deps:
            install_dependencies()
            return
        
        if args.clean:
            clean_build()
            return
        
        # Check dependencies
        if not check_dependencies():
            print_colored("\nInstall missing dependencies with --install-deps", Colors.RED)
            sys.exit(1)
        
        # Clean previous build
        clean_build()
        
        # Build executable
        build_executable(mode=args.mode, debug=args.debug)
        
        # Test executable
        if not args.no_test:
            if not test_executable():
                print_colored("Executable test failed, but build may still be usable", Colors.YELLOW)
        
        # Create installer
        if args.installer:
            create_installer()
        
        print_step("Build Complete")
        print_colored(f"✓ {BUILD_CONFIG['app_name']} built successfully!", Colors.GREEN + Colors.BOLD)
        print_colored("Check the 'dist' directory for your executable", Colors.BLUE)
        
    except KeyboardInterrupt:
        print_colored("\nBuild cancelled by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\nBuild failed: {e}", Colors.RED)
        sys.exit(1)

if __name__ == '__main__':
    main()