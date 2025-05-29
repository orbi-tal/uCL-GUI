from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                           QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt

class ConfirmDialog(QDialog):
    """Generic confirmation dialog"""

    def __init__(self, parent=None, title="Confirm", message="Are you sure?",
               ok_text="OK", cancel_text="Cancel"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.message = message
        self.ok_text = ok_text
        self.cancel_text = cancel_text
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        # Message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(message_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton(self.cancel_text)
        self.cancel_button.clicked.connect(self.reject)

        self.ok_button = QPushButton(self.ok_text)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)
