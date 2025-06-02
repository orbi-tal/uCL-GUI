from typing import Dict, List, Any, Optional, Protocol, Tuple
from src.core.models import Profile, ImportEntry
from src.application.import_service import ImportService

class ManageImportsView(Protocol):
    """Protocol defining required methods for the manage imports view"""
    def show_imports(self, imports: List[ImportEntry]) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_success(self, message: str) -> None: ...
    def refresh_imports_list(self) -> None: ...
    def confirm_remove(self, message: str) -> bool: ...

class ManageImportsPresenter:
    """Presenter for managing imports"""

    def __init__(self, import_service: ImportService):
        self.import_service = import_service
        self.view: Optional[ManageImportsView] = None

    def set_view(self, view: ManageImportsView) -> None:
        """Set the view for this presenter"""
        self.view = view

    def load_imports(self, profile: Profile) -> None:
        """Load imports from userChrome.css"""
        if not self.view:
            return

        # Get imports
        imports = []
        if profile.has_userchrome:
            try:
                # Read userChrome.css content
                content = self.import_service.userchrome_manager.read_userchrome(profile)
                if content:
                    # Get imports from content
                    imports = self.import_service.userchrome_manager.get_imports(content)
            except Exception as e:
                self.view.show_error(f"Failed to load imports: {str(e)}")

        # Show in view
        self.view.show_imports(imports)

    def toggle_import(self, profile: Profile, import_path: str, refresh: bool = True) -> bool:
        """
        Toggle an import on or off

        Args:
            profile: The profile to modify
            import_path: The import path to toggle
            refresh: Whether to refresh the imports list after toggling
            
        Returns:
            bool: Whether the toggle operation was successful
        """
        if not self.view:
            return False

        # Toggle import
        success, message, is_enabled = self.import_service.toggle_import(
            profile, import_path)

        # Update UI
        if success:
            if refresh:
                status = "enabled" if is_enabled else "disabled"
                self.view.show_success(f"Import {status}: {import_path}")
                # Refresh the imports list
                self.load_imports(profile)
        else:
            self.view.show_error(message)

        return success

    def remove_import(self, profile: Profile, import_path: str, refresh: bool = True) -> bool:
        """
        Remove an import

        Args:
            profile: The profile to modify
            import_path: The import path to remove
            refresh: Whether to refresh the imports list after removing
            
        Returns:
            bool: Whether the remove operation was successful
        """
        if not self.view:
            return False

        # Remove import
        success, message = self.import_service.remove_import(
            profile, import_path)

        # Update UI
        if success:
            if refresh:
                self.view.show_success(message)
                # Refresh the imports list
                self.load_imports(profile)
        else:
            self.view.show_error(message)

        return success

    def remove_multiple_imports(self, profile: Profile, import_paths: List[str]) -> int:
        """
        Remove multiple imports at once

        Args:
            profile: The profile to modify
            import_paths: List of import paths to remove

        Returns:
            Number of successfully removed imports
        """
        if not self.view or not profile or not import_paths:
            return 0
        
        # Count how many imports were successfully removed
        success_count = 0
        
        # Process each import separately to properly handle mod folder deletion
        for import_path in import_paths:
            if not import_path:
                continue
            
            # Call the import service's remove_import method
            success, message = self.import_service.remove_import(profile, import_path)
            
            if success:
                success_count += 1
            else:
                self.view.show_error(message)
        
        # Refresh the imports list if at least one import was removed
        if success_count > 0:
            self.load_imports(profile)
            
        return success_count

    def toggle_multiple_imports(self, profile: Profile, import_paths: List[str]) -> int:
        """
        Toggle multiple imports at once

        Args:
            profile: The profile to modify
            import_paths: List of import paths to toggle

        Returns:
            Number of successfully toggled imports
        """
        if not self.view or not profile or not import_paths:
            return 0

        # Get current userChrome.css content
        content = self.import_service.userchrome_manager.read_userchrome(profile)
        if not content:
            self.view.show_error("Could not read userChrome.css")
            return 0

        # Count how many imports were successfully toggled
        success_count = 0

        # Toggle each import in the content
        for import_path in import_paths:
            if not import_path:
                continue

            # Check if the import exists in the current content
            if not self.import_service.userchrome_manager.has_import(content, import_path):
                self.view.show_error(f"Import not found: {import_path}")
                continue

            # Toggle the import in the content
            try:
                content = self.import_service.userchrome_manager.toggle_import(content, import_path)
                success_count += 1
            except Exception as e:
                self.view.show_error(f"Failed to toggle import {import_path}: {str(e)}")

        # Only write the file if at least one import was toggled
        if success_count > 0:
            try:
                # Write the updated content back to userChrome.css
                self.import_service.userchrome_manager.write_userchrome(profile, content)

                # Refresh the imports list
                self.load_imports(profile)
            except Exception as e:
                self.view.show_error(f"Failed to write userChrome.css: {str(e)}")
                return 0

        return success_count
