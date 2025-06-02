import os
import platform
import subprocess
from PyQt6.QtWidgets import QApplication, QStyle
from PyQt6.QtGui import QColor, QPalette, QFontDatabase
from PyQt6.QtCore import Qt, QSettings

class StyleSystem:
    """
    Modern styling system for the application
    """

    # Modern color palette based on macOS, Fluent UI and Zen-browser app
    COLORS = {
        # Light theme
        "light": {
            "accent": "#F76F53",         # Zen Browser accent color - used for highlights
            "accent_hover": "#F85E3E",   # Slightly darker accent
            "accent_pressed": "#F94D29", # Even darker accent
            "text_primary": "#2E2E2E",   # Zen Browser button color in light mode
            "text_secondary": "#5A5A5A", # Medium gray for secondary text
            "text_disabled": "#AAAAAA",  # Light gray for disabled text
            "background_primary": "#F2F0E3", # Zen Browser light mode background
            "background_secondary": "#E8E6D9", # Slightly darker background
            "background_tertiary": "#DEDCD0", # Tertiary background
            "border": "#D1CFC0",         # Light border color
            "divider": "#E2E0D3",        # Subtle divider
            "button": "#2E2E2E",         # Button color in light mode (now dark)
            "button_text": "#F2F0E3",    # Button text color in light mode
            "change_profile_button": "#E6E4D7", # Change profile button in light mode
            "change_profile_text": "#1F1F1F",   # Opposite text color for change profile button in light mode
            "error": "#E05252",          # Soft red
            "success": "#52B788",        # Soft green
            "warning": "#F7B05B",        # Amber
            "info": "#5B91F7",           # Light blue
            "shadow": "#00000028",       # Standard shadow (40 alpha)
        },
        # Dark theme - Zen Browser dark style
        "dark": {
            "accent": "#F76F53",         # Zen Browser accent color - used for highlights
            "accent_hover": "#F85E3E",   # Slightly lighter accent
            "accent_pressed": "#F94D29", # Even lighter accent
            "text_primary": "#D1CFC0",   # Zen Browser button color in dark mode
            "text_secondary": "#A9A798", # Light gray for secondary text
            "text_disabled": "#7F7D70",  # Medium gray for disabled text
            "background_primary": "#1F1F1F", # Zen Browser dark mode background
            "background_secondary": "#2A2A2A", # Slightly lighter background
            "background_tertiary": "#363636", # Medium dark gray
            "border": "#444444",         # Medium gray border
            "divider": "#383838",        # Subtle divider
            "button": "#D1CFC0",         # Button color in dark mode (now light)
            "button_text": "#1F1F1F",    # Button text color in dark mode
            "change_profile_button": "#363636", # Change profile button in dark mode
            "change_profile_text": "#F2F0E3",   # Opposite text color for change profile button in dark mode
            "error": "#F97171",          # Soft red
            "success": "#52D399",        # Soft green
            "warning": "#FBCF44",        # Amber
            "info": "#60A5FA",           # Light blue
            "shadow": "#00000028",       # Standard shadow (40 alpha)
        }
    }

    @staticmethod
    def detect_system_theme():
        """
        Detect the system theme (light or dark)

        Returns:
            str: "light" or "dark"
        """
        system = platform.system()

        if system == "Darwin":  # macOS
            try:
                # Check macOS dark mode
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True, text=True
                )
                return "dark" if result.stdout.strip() == "Dark" else "light"
            except Exception:
                return "light"

        elif system == "Windows":  # Windows
            try:
                # Check Windows dark mode
                settings = QSettings("HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", QSettings.Format.NativeFormat)
                return "dark" if settings.value("AppsUseLightTheme") == 0 else "light"
            except Exception:
                return "light"

        elif system == "Linux":  # Linux
            try:
                # Try to detect GNOME dark mode
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                    capture_output=True, text=True
                )
                if "dark" in result.stdout.lower():
                    return "dark"

                # Try alternative GNOME setting
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                    capture_output=True, text=True
                )
                return "dark" if "dark" in result.stdout.lower() else "light"
            except Exception:
                return "light"

        # Default to light theme
        return "light"

    @staticmethod
    def apply_style(app, theme="auto"):
        """
        Apply the modern style to the application

        Args:
            app: QApplication instance
            theme: "light", "dark", or "auto" (detect from system)
        """
        # Auto-detect theme if set to "auto"
        if theme == "auto":
            theme = StyleSystem.detect_system_theme()

        if theme not in ["light", "dark"]:
            theme = "light"

        # Set application palette
        StyleSystem._set_palette(app, theme)

        # Load Bricolage Grotesque fonts before applying stylesheet
        StyleSystem.load_bricolage_fonts()

        # Apply stylesheet
        app.setStyleSheet(StyleSystem._get_stylesheet(theme))

    @staticmethod
    def get_zen_header_style():
        """Returns CSS class for Zen Browser style header"""
        return "zen-header"

    @staticmethod
    def get_zen_subheader_style():
        """Returns CSS class for Zen Browser style subheader"""
        return "zen-subheader"

    @staticmethod
    def get_zen_card_style():
        """Returns CSS class for Zen Browser style card"""
        return "zen-card"
    
    @staticmethod
    def get_status_style(status_type, theme="light"):
        """
        Get styling for status indicators (success, error, warning, info)
        
        Args:
            status_type: One of 'success', 'error', 'warning', 'info'
            theme: 'light' or 'dark'
            
        Returns:
            CSS style string
        """
        colors = StyleSystem.get_colors(theme)
        
        if status_type == "success":
            return f"color: {colors['success']}; font-weight: bold;"
        elif status_type == "error":
            return f"color: {colors['error']}; font-weight: bold;"
        elif status_type == "warning":
            return f"color: {colors['warning']}; font-weight: bold;"
        elif status_type == "info":
            return f"color: {colors['info']}; font-weight: bold;"
        else:
            return f"color: {colors['text_primary']};"
    
    @staticmethod
    def get_dialog_style(theme="light"):
        """
        Get styling for dialog windows
        
        Args:
            theme: 'light' or 'dark'
            
        Returns:
            CSS style string
        """
        colors = StyleSystem.get_colors(theme)
        
        return f"""
            #fluentDialog {{
                background-color: {colors["background_primary"]};
                border-radius: 6px;
            }}
            #dialogTitle {{
                font-family: -apple-system, "SF Pro Text", "Segoe UI", sans-serif;
                font-size: 28px;
                font-weight: 300;
                color: {colors["accent"]};
            }}
            #dialogDesc {{
                font-size: 14px;
                color: {colors["text_primary"]};
            }}
            #contentFrame {{
                background-color: {colors["background_secondary"]};
                border-radius: 6px;
                padding: 10px;
            }}
        """
    
    @staticmethod
    def get_main_window_style(theme="light"):
        """
        Get styling for main window
        
        Args:
            theme: 'light' or 'dark'
            
        Returns:
            CSS style string
        """
        colors = StyleSystem.get_colors(theme)
        
        return f"""
            #fluentWindow {{
                background-color: {colors["background_primary"]};
                border-radius: 6px;
            }}
            QLabel#pageTitle {{
                font-family: -apple-system, "SF Pro Text", "Segoe UI", sans-serif;
                font-size: 24px;
                font-weight: 300;
                color: {colors["accent"]};
            }}
            QLabel#pageDescription {{
                font-size: 14px;
                color: {colors["text_primary"]};
                margin-bottom: 10px;
            }}
            QFrame#contentFrame {{
                background-color: {colors["background_secondary"]};
                border-radius: 6px;
                padding: 10px;
            }}
            QLabel#sectionTitle {{
                font-weight: bold;
                font-size: 16px;
                color: {colors["text_primary"]};
            }}
            QListWidget {{
                background-color: {colors["background_secondary"]};
                border-radius: 4px;
                border: 1px solid {colors["border"]};
                padding: 5px;
            }}
            QComboBox {{
                background-color: {colors["background_secondary"]};
                border-radius: 4px;
                border: 1px solid {colors["border"]};
                padding: 5px;
                color: {colors["text_primary"]};
            }}
            QLineEdit {{
                background-color: {colors["background_secondary"]};
                border-radius: 4px;
                border: 1px solid {colors["border"]};
                padding: 5px;
                color: {colors["text_primary"]};
            }}
        """
    
    @staticmethod
    def get_welcome_dialog_style(theme="light"):
        """
        Get styling for welcome dialog
        
        Args:
            theme: 'light' or 'dark'
            
        Returns:
            CSS style string
        """
        colors = StyleSystem.get_colors(theme)
        
        return f"""
            #fluentDialog {{
                background-color: {colors["background_primary"]};
                border-radius: 6px;
            }}
            #welcomeTitle {{
                font-family: -apple-system, "SF Pro Text", "Segoe UI", sans-serif;
                font-size: 28px;
                font-weight: 300;
                color: {colors["accent"]};
            }}
            #welcomeDesc {{
                font-size: 14px;
                color: {colors["text_primary"]};
            }}
            #featureFrame {{
                background-color: {colors["background_secondary"]};
                border-radius: 6px;
                padding: 10px;
            }}
            #getStartedTitle {{
                font-weight: bold;
                font-size: 16px;
                color: {colors["text_primary"]};
            }}
        """
    
    @staticmethod
    def get_animated_button_style(bg_color, fg_color, theme="light"):
        """
        Get styling for animated buttons
        
        Args:
            bg_color: Background color
            fg_color: Foreground (text) color
            theme: 'light' or 'dark'
            
        Returns:
            CSS style string with hover and pressed states
        """
        # Create hover and pressed colors with more noticeable differences
        bg_hover = StyleSystem._adjust_color_brightness(bg_color, 1.2)  # 20% brighter
        bg_pressed = StyleSystem._adjust_color_brightness(bg_color, 0.8)  # 20% darker
        
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {fg_color};
                border: none;
                border-radius: 12px;
                padding: 8px 14px;
                min-height: 30px;
                min-width: 80px;
                font-weight: 500;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
            }}
            QPushButton:pressed {{
                background-color: {bg_pressed};
            }}
        """
    
    @staticmethod
    def _adjust_color_brightness(color, factor):
        """
        Adjust color brightness by the given factor
        
        Args:
            color: Color in hex format (#RRGGBB)
            factor: Brightness factor (>1 for brighter, <1 for darker)
            
        Returns:
            Adjusted color in hex format
        """
        # Remove # if present
        if color.startswith("#"):
            color = color[1:]
            
        # Convert hex to RGB
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # Adjust brightness
        r = min(255, max(0, int(r * factor)))
        g = min(255, max(0, int(g * factor)))
        b = min(255, max(0, int(b * factor)))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def get_colors(theme="light"):
        """Get color palette for the specified theme"""
        if theme not in ["light", "dark"]:
            theme = "light"
        return StyleSystem.COLORS[theme]

    @staticmethod
    def _set_palette(app, theme):
        """Set application color palette"""
        palette = QPalette()
        colors = StyleSystem.COLORS[theme]

        # Set application palette colors
        if theme == "light":
            palette.setColor(QPalette.ColorRole.Window, QColor(colors["background_primary"]))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text_primary"]))
            palette.setColor(QPalette.ColorRole.Base, QColor(colors["background_tertiary"]))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["background_secondary"]))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["background_primary"]))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors["text_primary"]))
            palette.setColor(QPalette.ColorRole.Text, QColor(colors["text_primary"]))
            palette.setColor(QPalette.ColorRole.Button, QColor(colors["background_secondary"]))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text_primary"]))
            palette.setColor(QPalette.ColorRole.Link, QColor(colors["accent"]))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["accent"]))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor(colors["background_primary"]))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text_primary"]))
            palette.setColor(QPalette.ColorRole.Base, QColor(colors["background_tertiary"]))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["background_secondary"]))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["background_secondary"]))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors["text_primary"]))
            palette.setColor(QPalette.ColorRole.Text, QColor(colors["text_primary"]))
            palette.setColor(QPalette.ColorRole.Button, QColor(colors["background_secondary"]))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text_primary"]))
            palette.setColor(QPalette.ColorRole.Link, QColor(colors["accent"]))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["accent"]))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))

        # Set disabled state colors
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(colors["text_disabled"]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(colors["text_disabled"]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(colors["text_disabled"]))

        # Apply palette
        app.setPalette(palette)

    @staticmethod
    def load_bricolage_fonts():
        """Load Bricolage Grotesque fonts from the bundled fonts directory."""
        font_dir = os.path.join(os.path.dirname(__file__), "fonts")
        for fname in os.listdir(font_dir):
            if fname.lower().endswith(".ttf") or fname.lower().endswith(".otf"):
                QFontDatabase.addApplicationFont(os.path.join(font_dir, fname))

    @staticmethod
    def _get_stylesheet(theme):
        """Generate the stylesheet based on the theme"""
        colors = StyleSystem.COLORS[theme]

        return f"""
        /* Global styles */
        * {{
            font-family: "Bricolage Grotesque", "SF Pro Text", "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
            font-size: 10pt;
        }}

        /* Headings */
        QLabel[title="true"], .zen-header, .large-text, QLabel.heading, QLabel[heading="true"] {{
            font-weight: bold !important;
            font-family: "Bricolage Grotesque", "SF Pro Text", "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
        }}

        /* Main Window */
        QMainWindow {{
            background-color: {colors["background_primary"]};
            color: {colors["text_primary"]};
        }}

        /* Push Buttons - macOS style */
        QPushButton {{
            background-color: {colors["button"]};
            color: {colors["button_text"]};
            border: none;
            border-radius: 12px;
            padding: 8px 14px;
            min-height: 30px;
            min-width: 80px;
            font-weight: 500;
            outline: none;
            /* Drop shadow is applied via QGraphicsDropShadowEffect in code */
        }}
        
        /* Change Profile Button */
        QPushButton[changeProfile="true"] {{
            background-color: {colors["change_profile_button"]};
            color: {colors["change_profile_text"]};
            border: none;
        }}

        QPushButton:hover, QPushButton[accent="true"]:hover {{
            /* No color change, just scale up */
        }}

        QPushButton:pressed, QPushButton[accent="true"]:pressed {{
            /* No color change, just scale up slightly more */
        }}

        QPushButton:disabled, QPushButton[accent="true"]:disabled {{
            color: {colors["text_disabled"]};
            background-color: {colors["button"]};
            border: none;
            opacity: 0.7;
        }}

        /* Accent Buttons - Zen Browser style */
        QPushButton[accent="true"] {{
            background-color: {colors["button"]};
            color: {colors["button_text"]};
            border: none;
            border-radius: 12px;
            padding: 8px 12px;
            font-weight: 500;
            outline: none;
            /* Drop shadow is applied via QGraphicsDropShadowEffect in code */
        }}

        /* QComboBox - macOS style */
        QComboBox {{
            background-color: {colors["background_secondary"]};
            color: {colors["text_primary"]};
            border: 0.5px solid {colors["border"]};
            border-radius: 12px;
            padding: 6px 10px;
            min-width: 6em;
        }}

        QComboBox:hover {{
            background-color: {colors["background_tertiary"]};
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: right center;
            width: 20px;
            border-left: none;
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors["background_primary"]};
            color: {colors["text_primary"]};
            border: 1px solid {colors["border"]};
            selection-background-color: {colors["accent"]};
            selection-color: white;
            border-radius: 12px;
        }}

        /* QLineEdit - macOS style */
        QLineEdit {{
            background-color: {colors["background_secondary"]};
            color: {colors["text_primary"]};
            border: 0.5px solid {colors["border"]};
            border-radius: 12px;
            padding: 8px 10px;
            selection-background-color: {colors["accent"]};
            selection-color: white;
        }}

        QLineEdit:focus {{
            border: 1px solid {colors["accent"]};
            background-color: {colors["background_primary"]};
        }}

        QLineEdit:disabled {{
            color: {colors["text_disabled"]};
            background-color: {colors["background_tertiary"]};
        }}

        /* QCheckBox - macOS style */
        QCheckBox {{
            color: {colors["text_primary"]};
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 0.5px solid {colors["border"]};
            border-radius: 4px;
            background-color: {colors["background_secondary"]};
        }}

        QCheckBox::indicator:checked {{
            background-color: {colors["accent"]};
            image: url(checkmark.svg);
            border: none;
        }}

        QCheckBox::indicator:hover {{
            border: 0.5px solid {colors["accent"]};
            background-color: {colors["background_tertiary"]};
        }}

        /* QRadioButton - macOS style */
        QRadioButton {{
            color: {colors["text_primary"]};
            spacing: 8px;
        }}

        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 0.5px solid {colors["border"]};
            border-radius: 9px;
            background-color: {colors["background_secondary"]};
        }}

        QRadioButton::indicator:checked {{
            background-color: {colors["background_primary"]};
            border: 4px solid {colors["accent"]};
        }}

        QRadioButton::indicator:hover {{
            border: 0.5px solid {colors["accent"]};
            background-color: {colors["background_tertiary"]};
        }}

        /* QListWidget - macOS style */
        QListWidget {{
            background-color: {colors["background_secondary"]};
            color: {colors["text_primary"]};
            border: 0.5px solid {colors["border"]};
            border-radius: 8px;
            padding: 2px;
        }}

        QListWidget::item {{
            padding: 8px 12px;
            border-radius: 10px;
            margin: 2px 4px;
        }}

        QListWidget::item:hover {{
            background-color: {colors["background_tertiary"]};
        }}

        QListWidget::item:selected {{
            background-color: {colors["background_tertiary"]};
            color: {colors["text_primary"]};
            border-left: 3px solid {colors["accent"]};
        }}

        /* QTabWidget and QTabBar - macOS style */
        QTabWidget::pane {{
            border: none;
            background-color: {colors["background_primary"]};
        }}

        QTabBar::tab {{
            background-color: transparent;
            color: {colors["text_secondary"]};
            border: none;
            padding: 8px 16px;
            min-width: 80px;
            font-weight: 500;
            margin-bottom: 2px;
        }}

        QTabBar::tab:selected {{
            color: {colors["accent"]};
            border-bottom: 2px solid {colors["accent"]};
        }}

        QTabBar::tab:hover:!selected {{
            color: {colors["text_primary"]};
        }}

        /* QProgressBar */
        QProgressBar {{
            border: 1px solid {colors["border"]};
            border-radius: 8px;
            background-color: {colors["background_secondary"]};
            text-align: center;
            color: {colors["text_primary"]};
            min-height: 12px;
        }}

        QProgressBar::chunk {{
            background-color: {colors["accent"]};
            width: 10px;
        }}

        /* QScrollBar - macOS style */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 8px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background-color: {colors["text_disabled"]};
            min-height: 20px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {colors["text_secondary"]};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background-color: transparent;
            height: 8px;
            margin: 0;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {colors["text_disabled"]};
            min-width: 20px;
            border-radius: 4px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {colors["text_secondary"]};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* QStatusBar - macOS style */
        QStatusBar {{
            background-color: {colors["background_primary"]};
            color: {colors["text_secondary"]};
            border-top: 0.5px solid {colors["divider"]};
            min-height: 24px;
            font-size: 9pt;
        }}

        /* QMenuBar - macOS style */
        QMenuBar {{
            background-color: {colors["background_primary"]};
            border-bottom: 0.5px solid {colors["divider"]};
            min-height: 24px;
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
            margin: 1px 2px;
        }}

        QMenuBar::item:selected {{
            background-color: rgba({int(colors["accent"][1:3], 16)}, {int(colors["accent"][3:5], 16)}, {int(colors["accent"][5:7], 16)}, 0.1);
            color: {colors["accent"]};
        }}

        /* QMenu - macOS style */
        QMenu {{
            background-color: {colors["background_primary"]};
            border: 0.5px solid {colors["border"]};
            border-radius: 8px;
            padding: 5px;
        }}

        QMenu::item {{
            padding: 6px 25px 6px 20px;
            border-radius: 6px;
            margin: 2px;
        }}

        QMenu::item:selected {{
            background-color: {colors["accent"]};
            color: white;
        }}

        QMenu::separator {{
            height: 0.5px;
            background-color: {colors["divider"]};
            margin: 4px 6px;
        }}

        /* QDialog - macOS style */
        QDialog {{
            background-color: {colors["background_primary"]};
            color: {colors["text_primary"]};
            border-radius: 12px;
        }}

        /* QToolTip - macOS style */
        QToolTip {{
            background-color: {colors["background_secondary"]};
            color: {colors["text_primary"]};
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            opacity: 0.95;
            font-size: 9.5pt;
        }}

        /* QGroupBox - macOS style */
        QGroupBox {{
            border: 0.5px solid {colors["border"]};
            border-radius: 12px;
            margin-top: 1.5ex;
            padding-top: 1ex;
            font-weight: 600;
            background-color: {colors["background_secondary"]};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {colors["text_primary"]};
            font-size: 10pt;
        }}

        /* QHeaderView (for tables) - macOS style */
        QHeaderView::section {{
            background-color: {colors["background_secondary"]};
            color: {colors["text_secondary"]};
            padding: 8px;
            border: none;
            border-bottom: 0.5px solid {colors["border"]};
            font-weight: 600;
            font-size: 9.5pt;
        }}

        /* QTableView - macOS style */
        QTableView {{
            background-color: {colors["background_primary"]};
            color: {colors["text_primary"]};
            gridline-color: {colors["divider"]};
            border: 0.5px solid {colors["border"]};
            border-radius: 8px;
            alternate-background-color: {colors["background_secondary"]};
        }}

        QTableView::item {{
            padding: 8px;
            border-bottom: 0.5px solid {colors["divider"]};
        }}

        QTableView::item:selected {{
            background-color: {colors["background_tertiary"]};
            color: {colors["text_primary"]};
        }}

        /* QLabel - macOS style */
        QLabel {{
            color: {colors["text_primary"]};
        }}

        QLabel[secondary="true"] {{
            color: {colors["text_secondary"]};
            font-size: 9.5pt;
        }}

        QLabel[title="true"] {{
            color: {colors["text_primary"]};
            font-weight: 600;
            font-size: 13pt;
        }}

        QLabel[subtitle="true"] {{
            color: {colors["text_secondary"]};
            font-size: 11pt;
        }}

        /* QSplitter */
        QSplitter::handle {{
            background-color: {colors["divider"]};
        }}

        QSplitter::handle:horizontal {{
            width: 1px;
        }}

        QSplitter::handle:vertical {{
            height: 1px;
        }}

        /* QToolBar - macOS style */
        QToolBar {{
            background-color: {colors["background_primary"]};
            border-bottom: 0.5px solid {colors["divider"]};
            spacing: 4px;
            min-height: 36px;
        }}

        QToolBar::separator {{
            width: 0.5px;
            background-color: {colors["divider"]};
            margin: 0 8px;
        }}

        /* QToolButton - macOS style */
        QToolButton {{
            background-color: transparent;
            color: {colors["text_primary"]};
            border: none;
            border-radius: 6px;
            padding: 6px;
        }}

        QToolButton:hover {{
            background-color: {colors["background_tertiary"]};
        }}

        QToolButton:pressed {{
            background-color: {colors["background_secondary"]};
        }}

        /* macOS Window Buttons - Close, Minimize, Maximize */
        QPushButton[macosBtn="close"] {{
            background-color: #FF5F57;
            border: none;
            border-radius: 6px;
            min-width: 12px;
            min-height: 12px;
            max-width: 12px;
            max-height: 12px;
        }}

        QPushButton[macosBtn="minimize"] {{
            background-color: #FFBD2E;
            border: none;
            border-radius: 6px;
            min-width: 12px;
            min-height: 12px;
            max-width: 12px;
            max-height: 12px;
        }}

        QPushButton[macosBtn="maximize"] {{
            background-color: #28C940;
            border: none;
            border-radius: 6px;
            min-width: 12px;
            min-height: 12px;
            max-width: 12px;
            max-height: 12px;
        }}

        /* macOS-style Toolbar */
        QFrame[macosToolbar="true"] {{
            background-color: {colors["background_secondary"]};
            border-bottom: 0.5px solid {colors["border"]};
            min-height: 38px;
            padding: 4px 8px;
        }}

        /* Special Classes - macOS/Zen Browser inspired */
        .accent-text {{
            color: {colors["accent"]};
        }}

        .error-text {{
            color: {colors["error"]};
        }}

        .success-text {{
            color: {colors["success"]};
        }}

        .warning-text {{
            color: {colors["warning"]};
        }}

        .large-text {{
            font-size: 14pt;
        }}

        .bold-text {{
            font-weight: 600;
        }}

        .card {{
            background-color: {colors["background_secondary"]};
            border-radius: 10px;
            padding: 16px;
        }}

        .zen-header {{
            font-weight: 600;
            font-size: 20pt;
            color: {colors["text_primary"]};
        }}

        .zen-subheader {{
            font-size: 12pt;
            color: {colors["text_secondary"]};
        }}

        /* Zen Browser Card Style */
        .zen-card {{
            background-color: {colors["background_secondary"]};
            border-radius: 12px;
            padding: 20px;
        }}

        /* Fluent-style Shadow */
        .shadow {{
            border: none;
            background-color: {colors["background_primary"]};
        }}

        /* Zen Browser Navigation Button */
        QPushButton[zen-nav="true"] {{
            background-color: transparent;
            color: {colors["accent"]};
            border: none;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 8px;
            text-align: left;
        }}

        QPushButton[zen-nav="true"]:hover {{
            background-color: rgba({int(colors["accent"][1:3], 16)}, {int(colors["accent"][3:5], 16)}, {int(colors["accent"][5:7], 16)}, 0.1);
        }}

        QPushButton[zen-nav="true"]:pressed {{
            background-color: rgba({int(colors["accent"][1:3], 16)}, {int(colors["accent"][3:5], 16)}, {int(colors["accent"][5:7], 16)}, 0.2);
        }}

        /* Zen Browser Search Field */
        QLineEdit[zen-search="true"] {{
            background-color: {colors["background_secondary"]};
            border-radius: 18px;
            padding: 8px 12px 8px 36px;
            font-size: 11pt;
            min-height: 36px;
        }}

        /* macOS-style Sidebar */
        QListWidget[macos-sidebar="true"] {{
            background-color: {colors["background_secondary"]};
            border: none;
            padding: 8px 0px;
        }}

        QListWidget[macos-sidebar="true"]::item {{
            padding: 8px 16px;
            border-radius: 6px;
            margin: 2px 8px;
        }}

        QListWidget[macos-sidebar="true"]::item:selected {{
            background-color: rgba({int(colors["accent"][1:3], 16)}, {int(colors["accent"][3:5], 16)}, {int(colors["accent"][5:7], 16)}, 0.2);
            color: {colors["accent"]};
        }}
        """
