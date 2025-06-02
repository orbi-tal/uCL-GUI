from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar)
from PyQt6.QtCore import Qt

class LoadingDialog(QDialog):
    """Dialog shown during long operations"""

    def __init__(self, parent=None, message="Please wait..."):
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setModal(True)

        # Qt6 uses different flag names than Qt5
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setFixedSize(300, 100)

        # Remove close button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        self.setup_ui(message)

    def setup_ui(self, message):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        # Message
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        # Progress bar (indeterminate)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)

    def set_message(self, message):
        """Update the displayed message"""
        self.message_label.setText(message)
