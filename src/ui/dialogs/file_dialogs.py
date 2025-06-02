from PyQt6.QtWidgets import QFileDialog
from typing import Optional, List, Tuple

class FileDialogs:
    """Utility class for file selection dialogs"""

    @staticmethod
    def get_css_file(parent=None) -> Optional[str]:
        """Open file dialog to select a CSS file"""
        options = QFileDialog.Option.ReadOnly

        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Select CSS File",
            "",
            "CSS Files (*.css);;All Files (*)",
            options=options
        )

        return file_path if file_path else None

    @staticmethod
    def get_css_files(parent=None) -> List[str]:
        """Open file dialog to select multiple CSS files"""
        options = QFileDialog.Option.ReadOnly

        file_paths, _ = QFileDialog.getOpenFileNames(
            parent,
            "Select CSS Files",
            "",
            "CSS Files (*.css);;All Files (*)",
            options=options
        )

        return file_paths

    @staticmethod
    def get_archive_file(parent=None) -> Optional[str]:
        """Open file dialog to select an archive file"""
        options = QFileDialog.Option.ReadOnly

        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Select Archive File",
            "",
            "Archives (*.zip *.xpi *.tar *.tar.gz *.tgz *.tar.bz2 *.tbz2);;All Files (*)",
            options=options
        )

        return file_path if file_path else None

    @staticmethod
    def get_folder(parent=None, caption="Select Folder") -> Optional[str]:
        """Open file dialog to select a folder"""
        folder_path = QFileDialog.getExistingDirectory(
            parent,
            caption,
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        return folder_path if folder_path else None

    @staticmethod
    def get_save_path(parent=None, caption="Save File",
                    default_name="", filter="") -> Optional[str]:
        """Open save file dialog"""
        options = QFileDialog.Option.DontConfirmOverwrite

        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            caption,
            default_name,
            filter,
            options=options
        )

        return file_path if file_path else None
