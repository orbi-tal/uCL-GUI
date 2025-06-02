# <img src="assets/icon.png" height="32px" alt="uCL GUI Logo"/> uCL GUI

A user-friendly tool to manage custom CSS files for [Zen Browser](https://zen-browser.app/).
Best used with mods following [uCL standards](https://github.com/greeeen-dev/userchrome-loader/).

## Features

- Import CSS files in multiple ways:
  - Single CSS files
  - Entire mod folders
  - Directly from GitHub repositories
  - From direct URL links
- Comprehensive import management:
  - Enable/disable specific imports
  - Remove individual imports or all at once
  - Organize imports in subfolders
- Automatic update checking:
  - Check for updates on GitHub-hosted mods
  - Easy one-click updates
  - Update notifications
- Profile management:
  - Support for multiple profiles
  - Automatic profile detection
- Cross-platform support:
  - Windows, macOS, Linux
  - Standard and Flatpak installations on Linux

## Building from Source

### Quick Build

```bash
# Linux/macOS
./build.sh

# Windows
build.bat

# Or using Python directly
python build.py
```

### Prerequisites

- **Python 3.8+** (3.10+ recommended)
- **Git** (optional, for cloning)
- **Platform-specific dependencies**:
  - **Linux**: `libarchive-dev`, `libcurl4-openssl-dev`
  - **Windows**: Visual Studio Build Tools
  - **macOS**: Xcode Command Line Tools

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/userchrome-loader.git
cd userchrome-loader

# Install dependencies
pip install -r requirements.txt

# Build executable
python build.py
```

### Build Options

```bash
# Different build modes
python build.py --mode onefile    # Single executable (default)
python build.py --mode onedir     # Directory with dependencies

# Development options
python build.py --debug           # Debug build with console
python build.py --clean           # Clean build artifacts
python build.py --install-deps    # Install dependencies only
python build.py --no-test         # Skip executable testing

# Icon generation
python build.py --icons                            # Generate application icons
python build.py --icons --source-image custom.png  # Use custom source image
python build.py --icons --icon-output custom/path  # Custom output directory

# Platform-specific
./build.sh --appimage            # Create AppImage (Linux)
python build.py --installer      # Create installer (when supported)
```

### Output Locations

- **Linux**: `dist/userchrome-loader-linux`
- **Windows**: `dist/userchrome-loader-windows.exe`
- **macOS**: `dist/userchrome-loader-macos.app`

For detailed build instructions, see [BUILD.md](BUILD.md).

## Usage

1. **Profile Selection**
   - Select between standard or Flatpak installation (Linux only)
   - Choose which profile to modify
   - Application checks if profile is in use

2. **Importing CSS**
   - Multiple import methods available:
     - Single CSS file import
     - Mod folder import
     - Direct URL import
     - GitHub repository import

   - For single files:
     - Select local CSS file or paste URL
     - File is validated and copied to chrome directory

   - For mod folders:
     - Select local folder or GitHub repository URL
     - Choose organization method:
       - Direct copy to chrome directory
       - Create subfolder for organization
     - Supports modular structures with multiple CSS files

   - For GitHub imports:
     - Paste repository URL
     - Automatically detects main CSS file
     - Downloads and organizes additional resources
     - Tracks version for updates

3. **Managing Imports**
   - View all current imports with status
   - Enable/disable specific imports
   - Remove individual imports and associated files
   - Check for updates on URL-based imports
   - Batch update available mods
   - Remove all imports with cleanup

4. **Update Management**
   - Check for updates on imported mods
   - View available updates with changelogs
   - Select which mods to update
   - Automatic backup before updating
   - Version tracking for each mod

## License

UserChrome Loader is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
