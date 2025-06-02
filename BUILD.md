# UserChrome Loader - Build Instructions

This document provides comprehensive instructions for building UserChrome Loader from source on Linux, Windows, and macOS.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Build Process](#detailed-build-process)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Troubleshooting](#troubleshooting)
- [Development Setup](#development-setup)

## Prerequisites

### System Requirements

- **Python 3.8 or higher** (3.10+ recommended)
- **Git** for cloning the repository
- **Platform-specific dependencies** (see below)

### Python Dependencies

The following Python packages are required:

```
PyQt6>=6.8.0
PyQt6-sip>=13.9.1
libarchive-c>=5.1
pycurl>=7.45.4
pyinstaller>=6.11.1
pyinstaller-hooks-contrib>=2024.11
typing_extensions>=4.12.2
setuptools>=75.7.0
```

### Platform-Specific Dependencies

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3-dev python3-pip git build-essential
sudo apt install libarchive-dev libcurl4-openssl-dev
sudo apt install qt6-base-dev qt6-tools-dev-tools  # Optional: for Qt development
```

#### Linux (Fedora/RHEL/CentOS)
```bash
sudo dnf install python3-devel python3-pip git gcc gcc-c++
sudo dnf install libarchive-devel libcurl-devel
sudo dnf install qt6-qtbase-devel qt6-qttools-devel  # Optional
```

#### Linux (Arch Linux)
```bash
sudo pacman -S python python-pip git base-devel
sudo pacman -S libarchive curl
sudo pacman -S qt6-base qt6-tools  # Optional
```

#### Windows
- **Visual Studio Build Tools** or **Visual Studio Community** (for C++ compilation)
- **Git for Windows**
- **Python 3.8+** from python.org

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python git libarchive curl
```

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/userchrome-loader.git
cd userchrome-loader
```

### 2. Install Dependencies
```bash
# Install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Or use the build script
python build.py --install-deps
```

### 3. Build the Executable
```bash
# Build using the build script (recommended)
python build.py

# Or build manually with PyInstaller
pyinstaller main.spec
```

### 4. Find Your Executable
The built executable will be in the `dist/` directory:
- **Linux**: `dist/userchrome-loader`
- **Windows**: `dist/userchrome-loader.exe`
- **macOS**: `dist/UserChrome Loader.app`

## Detailed Build Process

### Method 1: Using the Build Script (Recommended)

The build script automates the entire build process and provides helpful feedback.

```bash
# Basic build
python build.py

# Build with debug information
python build.py --debug

# Build as directory instead of single file
python build.py --mode onedir

# Clean build artifacts only
python build.py --clean

# Install dependencies only
python build.py --install-deps

# Skip executable testing
python build.py --no-test

# Create installer package (when supported)
python build.py --installer
```

#### Build Script Options

- `--mode onefile`: Creates a single executable file (default)
- `--mode onedir`: Creates a directory with executable and dependencies
- `--debug`: Includes debug information and console output
- `--clean`: Removes build artifacts and cache files
- `--install-deps`: Installs required Python dependencies
- `--no-test`: Skips the executable testing phase
- `--installer`: Creates platform-specific installer packages

### Method 2: Manual Build with PyInstaller

If you prefer to build manually or need custom options:

```bash
# Clean previous builds
rm -rf build/ dist/ __pycache__/

# Install dependencies
pip install -r requirements.txt

# Build using spec file
pyinstaller --clean --noconfirm main.spec

# Or build directly (basic)
pyinstaller --onefile --windowed --name userchrome-loader src/launcher.py
```

### Method 3: Development Build

For development and testing:

```bash
# Install in development mode
pip install -e .

# Run directly from source
python src/launcher.py
```

## Platform-Specific Instructions

### Linux

#### Building on Linux
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install python3-dev libarchive-dev libcurl4-openssl-dev

# Clone and build
git clone https://github.com/your-username/userchrome-loader.git
cd userchrome-loader
python build.py
```

#### Creating Linux Packages

**AppImage** (recommended for distribution):
```bash
# After building the executable
# Download appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Create AppDir structure
mkdir -p UserChrome-Loader.AppDir/usr/bin
cp dist/userchrome-loader UserChrome-Loader.AppDir/usr/bin/
# Add .desktop file and icon
# Run appimagetool
./appimagetool-x86_64.AppImage UserChrome-Loader.AppDir
```

**DEB Package**:
```bash
# Install fpm
sudo apt install ruby ruby-dev
sudo gem install fpm

# Create package
fpm -s dir -t deb -n userchrome-loader -v 1.0.0 \
    --description "UserChrome CSS Loader" \
    --maintainer "Your Name <email@example.com>" \
    dist/userchrome-loader=/usr/bin/userchrome-loader
```

### Windows

#### Building on Windows
```bash
# Open Command Prompt or PowerShell as Administrator
# Install Python dependencies
pip install -r requirements.txt

# Build
python build.py
```

#### Creating Windows Installer

**Using Inno Setup**:
1. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Create an `.iss` script file
3. Compile with Inno Setup Compiler

**Using NSIS**:
1. Install [NSIS](https://nsis.sourceforge.io/)
2. Create an `.nsi` script file
3. Compile with NSIS

### macOS

#### Building on macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install dependencies
brew install python libarchive curl

# Clone and build
git clone https://github.com/your-username/userchrome-loader.git
cd userchrome-loader
python build.py
```

#### Creating macOS Installer

**DMG Creation**:
```bash
# After building
hdiutil create -volname "UserChrome Loader" -srcfolder dist/ -ov -format UDZO UserChrome-Loader.dmg
```

**Code Signing** (for distribution):
```bash
# Sign the app (requires Apple Developer account)
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" "dist/UserChrome Loader.app"

# Create signed DMG
hdiutil create -volname "UserChrome Loader" -srcfolder dist/ -ov -format UDZO UserChrome-Loader-Signed.dmg
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" UserChrome-Loader-Signed.dmg
```

## Troubleshooting

### Common Issues

#### 1. Import Errors During Build
```
ModuleNotFoundError: No module named 'PyQt6'
```
**Solution**: Install missing dependencies
```bash
pip install PyQt6 PyQt6-sip
```

#### 2. libarchive Not Found (Linux)
```
ImportError: Unable to find libarchive
```
**Solution**: Install system libarchive development package
```bash
# Ubuntu/Debian
sudo apt install libarchive-dev

# Fedora/RHEL
sudo dnf install libarchive-devel

# Arch Linux
sudo pacman -S libarchive
```

#### 3. pycurl Build Errors (Windows)
**Solution**: Install pre-compiled wheel
```bash
pip install --only-binary=pycurl pycurl
```

#### 4. Qt Platform Plugin Error
```
qt.qpa.plugin: Could not find the Qt platform plugin "xcb"
```
**Solution**: Install Qt platform plugins
```bash
# Linux
sudo apt install qt6-qpa-plugins

# Or set environment variable
export QT_QPA_PLATFORM=offscreen
```

#### 5. Permission Denied (macOS)
**Solution**: Make executable and handle Gatekeeper
```bash
chmod +x "dist/UserChrome Loader.app/Contents/MacOS/userchrome-loader"
xattr -cr "dist/UserChrome Loader.app"
```

#### 6. Large Executable Size
**Solutions**:
- Use `--mode onedir` instead of `--onefile`
- Exclude unnecessary modules in `main.spec`
- Use UPX compression (if available)

### Debug Build Issues

For debugging build problems:

```bash
# Build with debug information
python build.py --debug

# Test the executable manually
cd dist/
./userchrome-loader --help  # Linux/macOS
userchrome-loader.exe --help  # Windows
```

### PyInstaller Specific Issues

#### Hidden Imports
If modules are missing at runtime, add them to `main.spec`:
```python
hiddenimports=[
    'your.missing.module',
    'another.module',
]
```

#### Data Files
If resources are missing, add them to `main.spec`:
```python
datas=[
    ('path/to/data', 'destination'),
]
```

## Development Setup

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/your-username/userchrome-loader.git
cd userchrome-loader

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run from source
python src/launcher.py
```

### Testing Changes

```bash
# Test without building
python src/launcher.py

# Quick build test
python build.py --mode onedir --debug

# Full build test
python build.py
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the build process
5. Submit a pull request

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython/)
- [Python Packaging User Guide](https://packaging.python.org/)

## Support

If you encounter issues not covered in this guide:

1. Check the [Issues](https://github.com/your-username/userchrome-loader/issues) page
2. Search for similar problems
3. Create a new issue with:
   - Your operating system and version
   - Python version (`python --version`)
   - Complete error message
   - Steps to reproduce