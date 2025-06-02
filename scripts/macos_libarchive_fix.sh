#!/bin/bash
# macOS libarchive fix script
# This script helps fix issues with libarchive on macOS by setting up necessary paths
# and copying required libraries to the application bundle.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_info() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    print_error "This script is for macOS only."
    exit 1
fi

# Check if homebrew is installed
if ! command -v brew &> /dev/null; then
    print_error "Homebrew is not installed. Please install it first."
    echo "Visit https://brew.sh for installation instructions."
    exit 1
fi

# Install libarchive if not already installed
if ! brew list libarchive &> /dev/null; then
    print_info "Installing libarchive via Homebrew..."
    brew install libarchive
else
    print_info "libarchive is already installed."
fi

# Get libarchive path
LIBARCHIVE_PATH=$(brew --prefix libarchive)
print_info "libarchive is installed at: $LIBARCHIVE_PATH"

# Set PKG_CONFIG_PATH
export PKG_CONFIG_PATH="$LIBARCHIVE_PATH/lib/pkgconfig"
print_info "Set PKG_CONFIG_PATH to $PKG_CONFIG_PATH"

# Create a temporary Python script to test libarchive
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import libarchive
    import libarchive.public
    print(f"libarchive module found at: {libarchive.__file__}")
    print("libarchive import successful!")
except ImportError as e:
    print(f"Failed to import libarchive: {e}")
    sys.exit(1)
EOF

# Test if libarchive can be imported
print_info "Testing libarchive import..."
if python3 $TEMP_SCRIPT; then
    print_success "libarchive is properly installed and can be imported."
else
    print_error "libarchive import test failed."
    
    # Try to fix by installing libarchive-c
    print_info "Attempting to install libarchive-c Python package..."
    pip3 install libarchive-c
    
    # Test again
    if python3 $TEMP_SCRIPT; then
        print_success "libarchive is now properly installed and can be imported."
    else
        print_error "libarchive installation failed. Please check your Python environment."
        exit 1
    fi
fi

# Remove temporary script
rm $TEMP_SCRIPT

# Fix app bundle if it exists
APP_PATH="dist/userchrome-loader-macos.app"
if [ -d "dist" ] && [ -d "$APP_PATH" ]; then
    print_info "Found app bundle at $APP_PATH, applying fixes..."
    
    # Create lib directory in app bundle
    mkdir -p "$APP_PATH/Contents/MacOS/lib"
    
    # Copy libarchive libraries to app bundle
    cp -P "$LIBARCHIVE_PATH/lib/libarchive"*.dylib "$APP_PATH/Contents/MacOS/lib/"
    
    # Check if the copy was successful
    if [ -f "$APP_PATH/Contents/MacOS/lib/libarchive.dylib" ]; then
        print_success "Successfully copied libarchive libraries to app bundle."
    else
        print_error "Failed to copy libarchive libraries to app bundle."
    fi
    
    # Make the libraries executable
    chmod +x "$APP_PATH/Contents/MacOS/lib/"*.dylib
    
    # Create a script to set up environment variables when launching the app
    cat > "$APP_PATH/Contents/MacOS/launcher" << 'EOF'
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export DYLD_LIBRARY_PATH="$DIR/lib:$DYLD_LIBRARY_PATH"
if [ -f "$DIR/userchrome-loader.bin" ]; then
    "$DIR/userchrome-loader.bin" "$@"
else
    echo "Error: executable not found"
    exit 1
fi
EOF
    
    # Make the launcher script executable
    chmod +x "$APP_PATH/Contents/MacOS/launcher"
    
    # Rename the original executable if it exists
    if [ -f "$APP_PATH/Contents/MacOS/userchrome-loader" ]; then
        mv "$APP_PATH/Contents/MacOS/userchrome-loader" "$APP_PATH/Contents/MacOS/userchrome-loader.bin"
        mv "$APP_PATH/Contents/MacOS/launcher" "$APP_PATH/Contents/MacOS/userchrome-loader"
    else
        print_info "Executable not found in expected location, skipping rename."
    fi
    
    print_success "App bundle has been fixed to include libarchive libraries."
    
    # Zip the fixed app bundle
    print_info "Creating zip archive of the fixed app bundle..."
    if [ -d "dist" ]; then
        (cd dist && zip -r userchrome-loader-macos.zip userchrome-loader-macos.app)
    else
        print_error "dist directory not found, can't create zip"
    fi
    
    print_success "Fixed app bundle has been zipped as dist/userchrome-loader-macos.zip"
else
    print_info "App bundle not found at $APP_PATH, skipping app bundle fix."
fi

print_success "macOS libarchive fix completed successfully."
echo ""
echo "If you're using PyInstaller, remember to set these environment variables:"
echo "export PKG_CONFIG_PATH=\"$PKG_CONFIG_PATH\""
echo "export DYLD_LIBRARY_PATH=\"$LIBARCHIVE_PATH/lib:\$DYLD_LIBRARY_PATH\""