import sys
from typing import Dict, List, Any, Optional, Protocol, Tuple
from src.core.models import Profile
from src.application.profile_service import ProfileService
from src.application.settings import SettingsService

class MainView(Protocol):
    """Protocol defining required methods for the main view"""
    def show_profiles(self, profiles: List[Profile]) -> None: ...
    def show_installations(self, installations: Dict[str, str]) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_success(self, message: str) -> None: ...
    def navigate_to_page(self, page_name: str) -> None: ...
    def show_welcome_dialog(self, set_welcome_shown_callback=None) -> bool: ...

class MainPresenter:
    """Presenter for the main application window"""

    def __init__(self, profile_service: ProfileService,
               settings_service: SettingsService):
        self.profile_service = profile_service
        self.settings_service = settings_service
        self.view: Optional[MainView] = None
        self.current_installation: Optional[str] = None
        self.current_profile: Optional[Profile] = None

    def set_view(self, view: MainView) -> None:
        """Set the view for this presenter"""
        self.view = view

    def initialize(self) -> None:
        """Initialize the presenter"""
        if not self.view:
            return

        # Detect browser installations first
        installations = self.profile_service.detect_browser_installations()

        # Update stored installations
        for name, path in installations.items():
            self.profile_service.add_browser_installation(name, path)

        # Get all installations (including user-added ones)
        all_installations = self.profile_service.get_browser_installations()

        # Show installations in the view
        self.view.show_installations(all_installations)

        # Check if welcome dialog should be shown
        welcome_shown = self.settings_service.get_setting("welcome_shown", False)

        # Show the appropriate page based on state
        if not welcome_shown:
            # Show welcome dialog and handle result
            # The view will call set_welcome_shown via the callback
            # We don't exit if the user dismisses the dialog - we continue to the main UI
            self.view.show_welcome_dialog(self.set_welcome_shown)

        # Determine which page to show
        if not all_installations:
            self.view.navigate_to_page("installation")
        else:
            # Try to load last profile
            last_profile = self.profile_service.get_last_profile()
            if last_profile:
                try:
                    installation = last_profile.get("installation")
                    profile_name = last_profile.get("profile")

                    if installation in all_installations:
                        self.select_installation(installation)
                        if profile_name:
                            self.select_profile(profile_name)
                            self.view.navigate_to_page("main_menu")
                            return
                except Exception:
                    pass

            # If no last profile or loading failed, go to installation page
            self.view.navigate_to_page("installation")

    def add_installation(self, name: str, path: str) -> bool:
        """Add a browser installation"""
        success = self.profile_service.add_browser_installation(name, path)
        if success and self.view:
            # After adding installation, select it and navigate to profile page
            self.select_installation(name)
        return success

    def load_installations(self) -> None:
        """Load browser installations"""
        installations = self.profile_service.get_browser_installations()

        if self.view:
            self.view.show_installations(installations)

    def select_installation(self, installation_name: str) -> bool:
        """Select a browser installation"""
        installations = self.profile_service.get_browser_installations()

        if installation_name not in installations:
            if self.view:
                self.view.show_error(f"Installation not found: {installation_name}")
            return False

        installation_path = installations[installation_name]

        try:
            # Load profiles for this installation
            profiles = self.profile_service.get_profiles(installation_path)

            if not profiles:
                if self.view:
                    self.view.show_error(f"No profiles found in {installation_name}")
                return False

            # Set current installation
            self.current_installation = installation_name

            # Show profiles in the view
            if self.view:
                self.view.show_profiles(profiles)

            return True

        except Exception as e:
            if self.view:
                self.view.show_error(f"Failed to load profiles: {str(e)}")
            return False


    def select_profile(self, profile_name: str) -> bool:
        """Select a profile by name"""
        if not self.current_installation:
            if self.view:
                self.view.show_error("No installation selected")
            return False

        installations = self.profile_service.get_browser_installations()
        installation_path = installations[self.current_installation]

        try:
            # Get profile
            profile = self.profile_service.get_profile_by_name(installation_path, profile_name)

            if not profile:
                if self.view:
                    self.view.show_error(f"Profile not found: {profile_name}")
                return False

            # Set current profile
            self.current_profile = profile

            # Save as last selected profile
            self.profile_service.save_last_profile(self.current_installation, profile_name)

            return True

        except Exception as e:
            if self.view:
                self.view.show_error(f"Failed to select profile: {str(e)}")
            return False

    def go_to_menu(self) -> None:
        """Navigate to main menu"""
        if self.view:
            self.view.navigate_to_page("main_menu")

    def go_to_import(self) -> None:
        """Navigate to import page"""
        if self.view:
            self.view.navigate_to_page("import")

    def go_to_manage(self) -> None:
        """Navigate to manage imports page"""
        if self.view:
            self.view.navigate_to_page("manage_imports")

    def set_welcome_shown(self) -> None:
        """Mark welcome dialog as shown"""
        self.settings_service.set_welcome_shown(True)
        
        # After setting welcome shown, let's refresh the UI
        if self.view:
            # Determine which page to show based on available installations
            installations = self.profile_service.get_browser_installations()
            if not installations:
                self.view.navigate_to_page("installation")
            else:
                self.view.navigate_to_page("main_menu")
