from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QScrollArea, QWidget, QTextBrowser,
                           QCheckBox, QFrame, QListWidget, QListWidgetItem,
                           QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from src.ui.style.style import StyleSystem

class UpdateDialog(QDialog):
    """Dialog showing update information with diffs between versions"""

    # Signal when updates are applied
    updates_applied = pyqtSignal(list)  # List of mod names that were updated

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Updates Available")
        self.resize(800, 600)
        self.updates_to_apply = []
        self.mod_update_info = {}  # Will store update info for each mod
        self.theme = "light"  # Default theme
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI"""
        main_layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Updates Available")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_font.setFamily("Bricolage Grotesque")
        header_label.setFont(header_font)
        main_layout.addWidget(header_label)

        # Description
        desc_label = QLabel(
            "The following mods have updates available. Select which ones to update."
        )
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)

        # Splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Left side - list of mods with updates
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self.updates_list = QListWidget()
        self.updates_list.setMinimumWidth(250)
        self.updates_list.currentRowChanged.connect(self.show_update_details)
        list_layout.addWidget(self.updates_list)

        # Select all checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        list_layout.addWidget(self.select_all_checkbox)

        splitter.addWidget(list_widget)

        # Right side - update details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)

        # Details header
        details_header = QLabel("Update Details")
        details_header_font = QFont(header_font)
        details_header_font.setFamily("Bricolage Grotesque")
        details_header.setFont(details_header_font)
        details_layout.addWidget(details_header)

        # Mod name and version
        self.mod_name_label = QLabel()
        details_font = QFont()
        details_font.setBold(True)
        details_font.setFamily("Bricolage Grotesque")
        self.mod_name_label.setFont(details_font)
        details_layout.addWidget(self.mod_name_label)

        # Version info
        self.version_info_label = QLabel()
        version_font = QFont()
        version_font.setItalic(True)
        self.version_info_label.setFont(version_font)
        details_layout.addWidget(self.version_info_label)

        # Commit info
        self.commit_info_label = QLabel()
        self.commit_info_label.setWordWrap(True)
        details_layout.addWidget(self.commit_info_label)

        # Diff display
        diff_label = QLabel("Changes:")
        details_layout.addWidget(diff_label)

        self.diff_browser = QTextBrowser()
        self.diff_browser.setOpenExternalLinks(True)
        details_layout.addWidget(self.diff_browser, 1)

        splitter.addWidget(details_widget)

        # Set initial sizes
        splitter.setSizes([300, 500])

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # Bottom buttons
        button_layout = QHBoxLayout()

        self.update_button = QPushButton("Update Selected")
        self.update_button.clicked.connect(self.apply_updates)
        self.update_button.setEnabled(False)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

    def set_update_data(self, updates_data):
        """
        Set the update data to display

        Args:
            updates_data: Dictionary mapping mod names to update info dictionaries
                         Each update info should contain:
                         - 'has_update': bool
                         - 'message': str
- 'commit_info': dict with keys like 'message', 'author', 'date'
                         - 'diff_info': list of changed files or HTML diff content
                         - 'source_type': 'github', 'gitlab', etc.
        """
        self.updates_list.clear()
        self.mod_update_info = updates_data
        
        for mod_name, update_info in updates_data.items():
            if update_info.get('has_update', False):
                item = QListWidgetItem(mod_name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                self.updates_list.addItem(item)
        
        # Enable/disable update button based on available updates
        self.update_button.setEnabled(self.updates_list.count() > 0)
        
        # Select the first item if available
        if self.updates_list.count() > 0:
            self.updates_list.setCurrentRow(0)
    
    def show_update_details(self, row):
        """Show details for the selected update"""
        if row < 0:
            self.mod_name_label.setText("")
            self.version_info_label.setText("")
            self.commit_info_label.setText("")
            self.diff_browser.setHtml("")
            return
        
        mod_name = self.updates_list.item(row).text()
        update_info = self.mod_update_info.get(mod_name, {})
        
        self.mod_name_label.setText(mod_name)
        
        # Show version info
        commit_info = update_info.get('commit_info', {})
        if commit_info:
            commit_sha = commit_info.get('sha', '')
            has_update = update_info.get('has_update', False)
            
            if commit_sha:
                if has_update:
                    version_text = f"Update available: v{commit_sha[:8]}"
                    self.version_info_label.setStyleSheet(StyleSystem.get_status_style("info", self.theme))
                else:
                    version_text = f"Current version: v{commit_sha[:8]} (up to date)"
                    self.version_info_label.setStyleSheet(StyleSystem.get_status_style("success", self.theme))
            else:
                version_text = "Version: Unknown"
                self.version_info_label.setStyleSheet(StyleSystem.get_status_style("default", self.theme))
            
            self.version_info_label.setText(version_text)
        else:
            self.version_info_label.setText("Version: Unknown")
            self.version_info_label.setStyleSheet(StyleSystem.get_status_style("default", self.theme))
        
        # Show commit info
        if commit_info:
            commit_message = commit_info.get('message', 'No commit message')
            commit_author = commit_info.get('author', 'Unknown')
            commit_date = commit_info.get('date', 'Unknown date')
            
            commit_text = f"Latest commit: {commit_message}\n"
            commit_text += f"By: {commit_author} on {commit_date}"
            
            self.commit_info_label.setText(commit_text)
        else:
            self.commit_info_label.setText("No commit information available")
        
        # Show diff info
        diff_info = update_info.get('diff_info', [])
        if isinstance(diff_info, str):
            # If it's a string, assume it's HTML content
            self.diff_browser.setHtml(diff_info)
        elif isinstance(diff_info, list):
            # If it's a list, assume it's a list of changed files
            diff_html = "<h3>Changed Files:</h3><ul>"
            for file_info in diff_info:
                if isinstance(file_info, dict):
                    filename = file_info.get('filename', 'Unknown file')
                    status = file_info.get('status', '')
                    
                    color = "#000000"
                    if status == 'added':
                        color = "#008800"
                        status_text = "Added"
                    elif status == 'modified':
                        color = "#0000FF"
                        status_text = "Modified"
                    elif status == 'removed':
                        color = "#FF0000"
                        status_text = "Removed"
                    else:
                        status_text = status.capitalize() if status else ""
                    
                    diff_html += f'<li><span style="color: {color};">{filename}</span>'
                    if status_text:
                        diff_html += f' ({status_text})'
                    diff_html += '</li>'
                else:
                    diff_html += f'<li>{file_info}</li>'
            
            diff_html += "</ul>"
            
            # Add commit URL if available
            source_type = update_info.get('source_type', '')
            commit_url = update_info.get('commit_url', '')
            if commit_url:
                diff_html += f'<p><a href="{commit_url}">View changes on {source_type.capitalize()}</a></p>'
            
            # Add note about CSS-only filtering
            has_update = update_info.get('has_update', False)
            non_css_files = update_info.get('non_css_files', [])
            if not has_update and len(non_css_files) > 0:
                diff_html += '<p><em>Note: Only CSS file changes trigger updates for UserChrome mods.</em></p>'
            
            self.diff_browser.setHtml(diff_html)
        else:
            self.diff_browser.setHtml("<p>No diff information available</p>")
    
    def toggle_select_all(self, state):
        """Toggle selection of all items"""
        for i in range(self.updates_list.count()):
            item = self.updates_list.item(i)
            item.setCheckState(Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked)
    
    def apply_updates(self):
        """Apply the selected updates"""
        self.updates_to_apply = []
        
        for i in range(self.updates_list.count()):
            item = self.updates_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.updates_to_apply.append(item.text())
        
        if self.updates_to_apply:
            self.updates_applied.emit(self.updates_to_apply)
            self.accept()
    
    def get_selected_updates(self):
        """Get list of selected mod names to update"""
        return self.updates_to_apply