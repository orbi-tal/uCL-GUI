from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                           QHBoxLayout, QListWidget, QListWidgetItem, QCheckBox)
from PyQt6.QtCore import Qt

class CssSelectionDialog(QDialog):
    """Dialog for selecting CSS files to import"""

    def __init__(self, parent=None, css_files=None):
        super().__init__(parent)
        self.setWindowTitle("Select CSS Files to Import")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.css_files = css_files or []
        self.selected_files = []
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "No userChrome.css file was found in the import.\n"
            "Please select which CSS files you want to import:"
        )
        layout.addWidget(instructions)

        # File list
        self.file_list = QListWidget()
        for css_file in self.css_files:
            item = QListWidgetItem(css_file)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.file_list.addItem(item)
        layout.addWidget(self.file_list)

        # Select all/none buttons
        select_layout = QHBoxLayout()
        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all)
        select_none_button = QPushButton("Select None")
        select_none_button.clicked.connect(self.select_none)
        select_layout.addWidget(select_all_button)
        select_layout.addWidget(select_none_button)
        layout.addLayout(select_layout)

        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        ok_button = QPushButton("Import Selected Files")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

    def select_all(self):
        """Select all files"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)

    def select_none(self):
        """Deselect all files"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)

    def get_selected_files(self):
        """Get the list of selected files"""
        selected = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(self.css_files[i])
        return selected
