from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QCheckBox,
                           QHBoxLayout, QApplication, QFrame, QWidget)
from src.ui.style.animated_button import DialogAnimatedButton
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QPalette
from src.ui.style.style import StyleSystem
from typing import Optional, cast

from typing import final

@final
class WelcomeDialog(QDialog):
    """Welcome dialog shown on first run"""

    # Add a signal for when the dialog is closed with result
    closed = pyqtSignal(bool, bool)  # (dont_show_again, was_accepted)

    def set_heading_font(self, label: QLabel) -> None:
        font = label.font()
        font.setBold(True)
        font.setFamily("Bricolage Grotesque")
        label.setFont(font)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to UserChrome Loader")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setObjectName("fluentDialog")

        # Get the current theme from the application
        app = cast(QApplication, QApplication.instance())
        if app:
            palette = app.palette()
            bg_color = palette.color(QPalette.ColorRole.Window).name()
            self.theme: str = "dark" if bg_color < "#808080" else "light"
        else:
            self.theme: str = "light"

        # Apply appropriate styling based on theme
        self.setup_ui()
        self.center_on_screen()
        self.apply_theme_styling()

        # Use a timer to ensure dialog appears on top after everything else is initialized
        _ = QTimer.singleShot(100, self.ensure_visibility)
        
        # Initialize instance variables
        self.dont_show_checkbox: Optional[QCheckBox] = None
        self.ok_button: Optional[DialogAnimatedButton] = None

    def apply_theme_styling(self) -> None:
        """Apply styling based on the current theme"""
        # Use the centralized styling from StyleSystem
        self.setStyleSheet(StyleSystem.get_welcome_dialog_style(self.theme))

    def setup_ui(self) -> None:
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Welcome title
        title_label = QLabel("Welcome to UserChrome Loader")
        title_label.setObjectName("welcomeTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "This tool helps you load custom CSS for your Zen Browser. It makes it easy to install and manage UserChrome customizations."
        )
        desc_label.setObjectName("welcomeDesc")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        # Add some spacing
        layout.addSpacing(10)

        # Features frame
        features_frame = QFrame()
        features_frame.setObjectName("featureFrame")
        features_layout = QVBoxLayout(features_frame)

        features_title = QLabel("Key Features:")
        features_title.setObjectName("getStartedTitle")
        features_layout.addWidget(features_title)

        # Features list
        colors = StyleSystem.get_colors(self.theme)
        features_text = (
            f"<ul style='margin-left: 15px; margin-top: 5px; color: {colors['text_primary']};'>"
            "<li style='margin-bottom: 8px;'>Import CSS files and folders with ease</li>"
            "<li style='margin-bottom: 8px;'>Install directly from GitHub and GitLab repositories</li>"
            "<li style='margin-bottom: 8px;'>Enable, disable, and manage your imports</li>"
            "<li style='margin-bottom: 8px;'>Automatically check for updates to installed mods</li>"
            "</ul>"
        )
        features_label = QLabel(features_text)
        features_label.setTextFormat(Qt.TextFormat.RichText)
        features_layout.addWidget(features_label)

        layout.addWidget(features_frame)

        # Getting started
        getting_started_frame = QFrame()
        getting_started_frame.setObjectName("featureFrame")
        getting_started_layout = QVBoxLayout(getting_started_frame)

        getting_started_title = QLabel("Getting Started:")
        getting_started_title.setObjectName("getStartedTitle")
        getting_started_layout.addWidget(getting_started_title)

        colors = StyleSystem.get_colors(self.theme)
        getting_started_label = QLabel(
            f"<span style='color: {colors['text_primary']};'>1. Select your Zen Browser installation and profile<br>2. Import CSS files or repositories<br>3. Enable/disable imports as needed<br>4. Enjoy your customized browser!</span>"
        )
        getting_started_label.setTextFormat(Qt.TextFormat.RichText)
        getting_started_label.setWordWrap(True)
        getting_started_layout.addWidget(getting_started_label)

        layout.addWidget(getting_started_frame)

        # Add some spacing
        layout.addSpacing(5)

        # Don't show again checkbox
        self.dont_show_checkbox = QCheckBox("Don't show this again")
        layout.addWidget(self.dont_show_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = DialogAnimatedButton("Get Started")
        _ = self.ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

        # Update styling for the current theme
        self.apply_theme_styling()

    def accept(self) -> None:  # override
        """Override the accept method to emit the closed signal"""
        if self.dont_show_checkbox:
            dont_show = self.dont_show_checkbox.isChecked()
            self.closed.emit(dont_show, True)
        super().accept()

    def reject(self) -> None:  # override
        """Override the reject method to emit the closed signal"""
        if self.dont_show_checkbox:
            dont_show = self.dont_show_checkbox.isChecked()
            self.closed.emit(dont_show, False)
        super().reject()

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:  # override
        """Handle dialog close event"""
        if self.dont_show_checkbox and a0:
            dont_show_again = self.dont_show_checkbox.isChecked()
            self.closed.emit(dont_show_again, False)
        super().closeEvent(a0)

    def center_on_screen(self) -> None:
        """Center the dialog on the screen"""
        app = cast(QApplication, QApplication.instance())
        if app:
            screen = app.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                
                window_geometry = self.frameGeometry()
                center_point = screen_geometry.center()
                
                window_geometry.moveCenter(center_point)
                self.move(window_geometry.topLeft())

    def ensure_visibility(self) -> None:
        """Ensure dialog is visible and on top of all windows"""
        self.show()
        self.raise_()
        self.activateWindow()

        # On some systems, we need to set the window state explicitly
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
