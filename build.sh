#!/bin/bash
# Build script for UserChrome Loader (Unix systems)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="UserChrome Loader"
APP_VERSION="1.0.0"
PYTHON_MIN_VERSION="3.8"

# Functions
print_header() {
    echo -e "${CYAN}${BOLD}================================${NC}"
    echo -e "${CYAN}${BOLD} $1${NC}"
    echo -e "${CYAN}${BOLD}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    required_version="3.8"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python $python_version is installed, but $required_version or higher is required"
        exit 1
    fi
    
    print_success "Python $python_version found"
}

check_git() {
    if ! command -v git &> /dev/null; then
        print_warning "Git is not installed (optional for building)"
    else
        print_success "Git found"
    fi
}

install_dependencies() {
    print_header "Installing Dependencies"
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_info "Installing from requirements.txt..."
        python3 -m pip install -r requirements.txt
    else
        print_info "Installing basic dependencies..."
        python3 -m pip install PyQt6 pyinstaller pycurl libarchive-c
    fi
    
    print_success "Dependencies installed"
}

clean_build() {
    print_header "Cleaning Previous Build"
    
    # Remove build artifacts
    rm -rf build/
    rm -rf dist/
    rm -rf __pycache__/
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Build artifacts cleaned"
}

build_executable() {
    print_header "Building Executable"
    
    # Check if spec file exists
    if [ -f "main.spec" ]; then
        print_info "Using spec file: main.spec"
        python3 -m PyInstaller --clean --noconfirm main.spec
    else
        print_info "Building without spec file"
        python3 -m PyInstaller \
            --onefile \
            --windowed \
            --name userchrome-loader \
            --hidden-import PyQt6.QtWidgets \
            --hidden-import PyQt6.QtCore \
            --hidden-import PyQt6.QtGui \
            --hidden-import PyQt6.sip \
            --hidden-import pycurl \
            --hidden-import libarchive \
            src/launcher.py
    fi
    
    print_success "Build completed"
}

test_executable() {
    print_header "Testing Executable"
    
    if [ -f "dist/userchrome-loader" ]; then
        print_info "Testing executable..."
        
        # Make executable
        chmod +x dist/userchrome-loader
        
        # Test if it can start (with timeout)
        if timeout 5s dist/userchrome-loader --help >/dev/null 2>&1; then
            print_success "Executable test passed"
        else
            print_warning "Executable test failed or timed out (may be GUI-only)"
        fi
        
        # Show file info
        file_size=$(du -h dist/userchrome-loader | cut -f1)
        print_info "Executable size: $file_size"
        print_info "Location: $(pwd)/dist/userchrome-loader"
    else
        print_error "Executable not found in dist/"
        exit 1
    fi
}

create_appimage() {
    print_header "Creating AppImage"
    
    if ! command -v appimagetool &> /dev/null; then
        print_warning "appimagetool not found, skipping AppImage creation"
        print_info "To create AppImage, install appimagetool:"
        print_info "wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        print_info "chmod +x appimagetool-x86_64.AppImage"
        return
    fi
    
    # Create AppDir structure
    mkdir -p UserChrome-Loader.AppDir/usr/bin
    cp dist/userchrome-loader UserChrome-Loader.AppDir/usr/bin/
    
    # Create desktop file
    cat > UserChrome-Loader.AppDir/userchrome-loader.desktop << EOF
[Desktop Entry]
Name=UserChrome Loader
Exec=userchrome-loader
Icon=userchrome-loader
Type=Application
Categories=Utility;
EOF
    
    # Create AppRun
    cat > UserChrome-Loader.AppDir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/userchrome-loader" "$@"
EOF
    chmod +x UserChrome-Loader.AppDir/AppRun
    
    # Create AppImage
    appimagetool UserChrome-Loader.AppDir UserChrome-Loader.AppImage
    
    if [ -f "UserChrome-Loader.AppImage" ]; then
        print_success "AppImage created: UserChrome-Loader.AppImage"
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --clean             Clean build artifacts only"
    echo "  --deps              Install dependencies only"
    echo "  --no-test           Skip executable testing"
    echo "  --appimage          Create AppImage (Linux only)"
    echo "  --debug             Enable debug output"
    echo ""
    echo "Examples:"
    echo "  $0                  # Full build"
    echo "  $0 --clean          # Clean only"
    echo "  $0 --deps           # Install deps only"
    echo "  $0 --appimage       # Build and create AppImage"
}

main() {
    local clean_only=false
    local deps_only=false
    local no_test=false
    local create_appimage_flag=false
    local debug=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_usage
                exit 0
                ;;
            --clean)
                clean_only=true
                shift
                ;;
            --deps)
                deps_only=true
                shift
                ;;
            --no-test)
                no_test=true
                shift
                ;;
            --appimage)
                create_appimage_flag=true
                shift
                ;;
            --debug)
                debug=true
                set -x
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Show header
    echo -e "${BOLD}${CYAN}$APP_NAME Build Script${NC}"
    echo -e "${CYAN}Version $APP_VERSION${NC}"
    echo ""
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    # Check system requirements
    check_python
    check_git
    
    if [ "$clean_only" = true ]; then
        clean_build
        exit 0
    fi
    
    if [ "$deps_only" = true ]; then
        install_dependencies
        exit 0
    fi
    
    # Full build process
    install_dependencies
    clean_build
    build_executable
    
    if [ "$no_test" = false ]; then
        test_executable
    fi
    
    if [ "$create_appimage_flag" = true ]; then
        create_appimage
    fi
    
    # Success message
    print_header "Build Complete"
    print_success "$APP_NAME built successfully!"
    print_info "Executable location: $(pwd)/dist/userchrome-loader"
    
    if [ "$create_appimage_flag" = true ] && [ -f "UserChrome-Loader.AppImage" ]; then
        print_info "AppImage location: $(pwd)/UserChrome-Loader.AppImage"
    fi
}

# Run main function with all arguments
main "$@"