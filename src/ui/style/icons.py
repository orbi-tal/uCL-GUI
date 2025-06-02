import os
import sys
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, Qt

class IconProvider:
    """
    Provides SVG icons for the application
    """
    
    @staticmethod
    def get_svg_icon(svg_content, color="#FFFFFF", size=16):
        """
        Create a QIcon from SVG content with the specified color
        
        Args:
            svg_content: SVG XML content
            color: Color to use for the SVG (hex format)
            size: Size of the icon
            
        Returns:
            QIcon object
        """
        # Replace color placeholders
        svg_content = svg_content.replace('{{color}}', color)
        
        # Ensure SVG has proper XML headers
        if not svg_content.strip().startswith('<?xml'):
            svg_content = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' + svg_content
        
        # Create QIcon from the SVG content
        byte_array = QByteArray(svg_content.encode('utf-8'))
        pixmap = QPixmap()
        
        # Load the SVG data
        if not pixmap.loadFromData(byte_array, "SVG"):
            # Fallback to a simple colored square if loading fails
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor(color))
        
        # Scale if needed
        if not pixmap.isNull() and (pixmap.width() != size or pixmap.height() != size):
            pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
        return QIcon(pixmap)
    
    @staticmethod
    def get_check_icon(color="#4762FF", size=16):
        """Get a macOS-style checkmark icon"""
        svg = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
            <path fill="{{color}}" d="M6.5 12.5l-4-4 1.4-1.4 2.6 2.6 6-6 1.4 1.4z"/>
        </svg>
        '''
        return IconProvider.get_svg_icon(svg, color, size)
    
    @staticmethod
    def get_dot_icon(color="#4762FF", size=16):
        """Get a macOS-style dot icon for radio buttons"""
        svg = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
            <circle cx="8" cy="8" r="4.5" fill="{{color}}"/>
        </svg>
        '''
        return IconProvider.get_svg_icon(svg, color, size)
    
    @staticmethod
    def get_arrow_icon(color="#6E7175", size=16):
        """Get a macOS-style arrow icon for dropdown menus"""
        svg = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
            <path stroke="{{color}}" stroke-width="1.5" fill="none" d="M12.5 5.5L8 10 3.5 5.5"/>
        </svg>
        '''
        return IconProvider.get_svg_icon(svg, color, size)
    
    @staticmethod
    def get_close_icon(color="#6E7175", size=16):
        """Get a macOS-style close (X) icon"""
        svg = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
            <path d="M12 4.7L11.3 4 8 7.3 4.7 4 4 4.7 7.3 8 4 11.3 4.7 12 8 8.7 11.3 12 12 11.3 8.7 8z" fill="{{color}}"/>
        </svg>
        '''
        return IconProvider.get_svg_icon(svg, color, size)
    
    @staticmethod
    def get_import_icon(color="#4762FF", size=16):
        """Get a macOS-style import/download icon"""
        svg = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
            <path fill="{{color}}" d="M8 12L3 7h3V2h4v5h3L8 12z"/>
            <path fill="{{color}}" d="M14 14H2v-3h2v1h8v-1h2v3z"/>
        </svg>
        '''
        return IconProvider.get_svg_icon(svg, color, size)
    
    @staticmethod
    def get_settings_icon(color="#4762FF", size=16):
        """Get a macOS-style settings/gear icon"""
        svg = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
            <path fill="{{color}}" d="M8 11.5a3.5 3.5 0 100-7 3.5 3.5 0 000 7z"/>
            <path fill="{{color}}" d="M15 8.5l-1.8-3-2.2.7-1-1 .7-2.2-3-1.8L6.5 3l-2 .5L3 1l-3 1.8.7 2.2-1 1L1.5 4l-1.8 3 2 1.2V10l-2 1.2 1.8 3 2.2-.7 1 1-.7 2.2 3 1.8 1.2-2 2-.5 1.5 2.5 3-1.8-.7-2.2 1-1 2.2.7 1.8-3-2-1.2V9.7l2-1.2zM8 10a2 2 0 110-4 2 2 0 010 4z" opacity=".5"/>
        </svg>
        '''
        return IconProvider.get_svg_icon(svg, color, size)
    
    @staticmethod
    def get_add_icon(color="#4762FF", size=16):
        """Get a macOS-style plus/add icon"""
        svg = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
            <path d="M8 2a1 1 0 011 1v4h4a1 1 0 010 2H9v4a1 1 0 01-2 0V9H3a1 1 0 010-2h4V3a1 1 0 011-1z" fill="{{color}}"/>
        </svg>
        '''
        return IconProvider.get_svg_icon(svg, color, size)
    
    @staticmethod
    def get_back_icon(color="#4762FF", size=16):
        """Get a macOS-style back/left arrow icon"""
        svg = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
            <path d="M10.5 12.5L6 8l4.5-4.5" stroke="{{color}}" stroke-width="1.5" fill="none"/>
        </svg>
        '''
        return IconProvider.get_svg_icon(svg, color, size)
    
    @staticmethod
    def save_icons_to_files(directory):
        """
        Save all icons as PNG files to the specified directory
        
        Args:
            directory: Directory path to save icons to
        """
        os.makedirs(directory, exist_ok=True)
        
        # Define icons to save with Zen Browser inspired colors
        icons = {
            "check.png": IconProvider.get_check_icon("#4762FF", 24),
            "dot.png": IconProvider.get_dot_icon("#4762FF", 24),
            "arrow.png": IconProvider.get_arrow_icon("#6E7175", 24),
            "close.png": IconProvider.get_close_icon("#6E7175", 24),
            "import.png": IconProvider.get_import_icon("#4762FF", 24),
            "settings.png": IconProvider.get_settings_icon("#4762FF", 24),
            "add.png": IconProvider.get_add_icon("#4762FF", 24),
            "back.png": IconProvider.get_back_icon("#4762FF", 24),
        }
        
        # Save each icon
        for filename, icon in icons.items():
            path = os.path.join(directory, filename)
            pixmap = icon.pixmap(24, 24)
            if not pixmap.isNull():
                pixmap.save(path)
            else:
                # Create a fallback colored square if pixmap is null
                fallback = QPixmap(24, 24)
                color = "#4762FF" if "back" in filename or "check" in filename or "dot" in filename or "import" in filename or "settings" in filename or "add" in filename else "#6E7175"
                fallback.fill(QColor(color))
                fallback.save(path)
            
        return [os.path.join(directory, name) for name in icons.keys()]

def set_app_icon(app):
    """
    Set the application icon
    
    Args:
        app: QApplication instance
    
    Returns:
        True if icon was set successfully, False otherwise
    """
    # Platform-specific icons
    icon_path = None
    
    # Try different potential locations for the icon file
    icon_locations = [
        # First try dist/icons which is where our generator puts them
        Path("dist/icons/app.ico"),
        Path("dist/icons/app.icns"),
        # Then try the assets directory
        Path("assets/icon.ico"),
        Path("assets/icon.icns"),
        Path("assets/icon.svg"),
        # Then try relative to the executable in frozen mode
        Path(getattr(sys, '_MEIPASS', '.')) / "assets" / "icon.ico",
        Path(getattr(sys, '_MEIPASS', '.')) / "assets" / "icon.icns",
        Path(getattr(sys, '_MEIPASS', '.')) / "assets" / "icon.svg",
    ]
    
    # Find the first icon that exists
    for path in icon_locations:
        if path.exists():
            icon_path = path
            break
    
    if icon_path:
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
        return True
    
    return False

def install_icons(app):
    """
    Install icons for the application
    
    Args:
        app: QApplication instance
    
    Returns:
        Path to the icons directory
    """
    # Create temporary directory for icons if needed
    temp_dir = os.path.join(os.path.expanduser('~'), '.userchrome-loader', 'icons')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save icons to files
    IconProvider.save_icons_to_files(temp_dir)
    
    # Set application icon
    set_app_icon(app)
    
    # Return the path to the icons directory
    return temp_dir