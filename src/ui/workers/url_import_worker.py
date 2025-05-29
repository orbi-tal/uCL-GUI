from PyQt6.QtCore import QThread, pyqtSignal
import traceback
from typing import Tuple, Optional
from src.core.models import Profile, ModInfo

class UrlImportWorker(QThread):
    """Worker thread for URL imports"""

    # Signals for progress and completion
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str, object)  # success, message, mod_info

    def __init__(self, import_service, profile, url):
        super().__init__()
        self.import_service = import_service
        self.profile = profile
        self.url = url

    def run(self):
        """Run the import operation"""
        try:
            # Emit initial progress
            self.progress.emit(f"Downloading from {self.url}")
            
            # Check if this is a GitHub URL
            if "github.com" in self.url:
                # Handle GitHub specific progress updates
                self.progress.emit("Downloading GitHub repository...")
            
            # Perform import
            success, message, mod_info = self.import_service.import_from_url(
                self.profile, self.url)

            # Validate the result
            if success and mod_info is not None:
                if not hasattr(mod_info, 'files') or not mod_info.files:
                    self.progress.emit("Warning: No files were imported")
                    self.finished.emit(False, "Import failed: No files were imported", mod_info)
                else:
                    self.progress.emit(f"Successfully imported {len(mod_info.files)} file(s)")
                    self.finished.emit(success, message, mod_info)
            else:
                self.progress.emit(f"Import failed: {message}")
                self.finished.emit(success, message, mod_info)

        except Exception as e:
            # Handle any exceptions
            self.finished.emit(False, f"Import failed: {str(e)}", None)
