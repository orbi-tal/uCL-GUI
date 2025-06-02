from typing import Dict, List, Any, Optional, Protocol, Tuple
from src.core.models import Profile, ModInfo
from src.application.import_service import ImportService
from src.application.settings import SettingsService

class ImportView(Protocol):
    """Protocol defining required methods for the import view"""
    def show_progress(self, message: str) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_success(self, message: str) -> None: ...
    def refresh_imports_list(self) -> None: ...
    def get_file_path(self) -> Optional[str]: ...
    def get_folder_path(self) -> Optional[str]: ...
    def get_subfolder_preference(self) -> str: ...

class ImportPresenter:
    """Presenter for import functionality"""

    def __init__(self, import_service: ImportService,
                settings_service: SettingsService):
        self.import_service = import_service
        self.settings_service = settings_service
        self.view: Optional[ImportView] = None

    def set_view(self, view: ImportView) -> None:
        """Set the view for this presenter"""
        self.view = view

    def handle_url_import(self, profile: Profile, url: str,
                        mod_name: Optional[str] = None) -> None:
        """Handle importing from a URL"""
        if not self.view:
            return

        # Show progress
        self.view.show_progress("Downloading from URL...")

        # Perform import
        success, message, mod_info = self.import_service.import_from_url(
            profile, url, mod_name)

        # Update UI
        if success:
            self.view.show_success(message)
            self.view.refresh_imports_list()
        else:
            self.view.show_error(message)

    def handle_file_import(self, profile: Profile) -> None:
        """Handle importing from a local file"""
        if not self.view:
            return

        # Get file path from view
        file_path = self.view.get_file_path()
        if not file_path:
            return

        # Show progress
        self.view.show_progress(f"Importing {os.path.basename(file_path)}...")

        # Perform import
        success, message, mod_info = self.import_service.import_from_file(
            profile, file_path)

        # Update UI
        if success:
            self.view.show_success(message)
            # Go to main menu after successful import
            self.view.go_to_menu()
        else:
            self.view.show_error(message)

    def handle_folder_import(self, profile: Profile) -> None:
        """Handle importing from a local folder"""
        if not self.view:
            return

        # Get folder path from view
        folder_path = self.view.get_folder_path()
        if not folder_path:
            return

        # Get subfolder preference
        subfolder_preference = self.view.get_subfolder_preference()
        if subfolder_preference is None:  # User cancelled the dialog
            return

        # Save preference for next time
        self.settings_service.set_setting("preferred_subfolder", subfolder_preference)

        # Show progress
        self.view.show_progress(f"Importing from {os.path.basename(folder_path)}...")

        # Perform import
        success, message, mod_info = self.import_service.import_from_directory(
            profile, folder_path)

        # Update UI
        if success:
            self.view.show_success(message)
            # Go to main menu after successful import
            self.view.go_to_menu()
        else:
            self.view.show_error(message)

    def select_css_files(self, css_files: List[str], extract_dir: str) -> List[str]:
        """
        Show a dialog to select which CSS files to import
        """
        if not self.view or not css_files:
            return []

        # Check if userChrome.css exists
        userchrome_files = [f for f in css_files if os.path.basename(f).lower() == 'userchrome.css']
        if userchrome_files:
            return userchrome_files

        # Get relative paths for display
        rel_css_files = [os.path.relpath(f, extract_dir) for f in css_files]

        # Show dialog to select files
        selected_files = self.view.select_css_files(rel_css_files)

        # Map selected relative paths back to full paths
        selected_indices = [rel_css_files.index(f) for f in selected_files if f in rel_css_files]
        return [css_files[i] for i in selected_indices]
