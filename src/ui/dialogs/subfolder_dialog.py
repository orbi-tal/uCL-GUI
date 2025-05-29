from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                           QHBoxLayout, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt

class SubfolderDialog(QDialog):
    """Dialog for choosing subfolder preferences"""

    IMPORT_ALL = "import_all"
    IMPORT_MAIN = "import_main"
    SELECT_MANUALLY = "select_manually"

    def __init__(self, parent=None, default_option=None):
        super().__init__(parent)
        self.setWindowTitle("Import Options")
        self.default_option = default_option or self.IMPORT_MAIN
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("How would you like to import CSS files?")
        layout.addWidget(title_label)

        # Radio buttons
        self.button_group = QButtonGroup(self)

        self.import_all_radio = QRadioButton(
            "Import all CSS files (creates imports for every CSS file)"
        )
        self.import_main_radio = QRadioButton(
            "Import only main CSS files (skips files that are imported by others)"
        )
        self.select_manually_radio = QRadioButton(
            "Let me select which files to import"
        )

        self.button_group.addButton(self.import_all_radio, 1)
        self.button_group.addButton(self.import_main_radio, 2)
        self.button_group.addButton(self.select_manually_radio, 3)

        layout.addWidget(self.import_all_radio)
        layout.addWidget(self.import_main_radio)
        layout.addWidget(self.select_manually_radio)

        # Set default option
        if self.default_option == self.IMPORT_ALL:
            self.import_all_radio.setChecked(True)
        elif self.default_option == self.IMPORT_MAIN:
            self.import_main_radio.setChecked(True)
        else:
            self.select_manually_radio.setChecked(True)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

    def get_selection(self) -> str:
        """Get the selected option"""
        if self.import_all_radio.isChecked():
            return self.IMPORT_ALL
        elif self.import_main_radio.isChecked():
            return self.IMPORT_MAIN
        else:
            return self.SELECT_MANUALLY
