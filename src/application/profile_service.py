import os
import sys
from typing import List, Optional, Dict, Any
from src.core.models import Profile
from src.core.profile import ProfileManager
from src.core.exceptions import ProfileError
from src.infrastructure.config_store import ConfigStore

class ProfileService:
    """Service for managing browser profiles"""

    def __init__(self, profile_manager: ProfileManager, config_store: ConfigStore):
        self.profile_manager = profile_manager
        self.config_store = config_store

    def get_browser_installations(self) -> Dict[str, str]:
        """Get all known browser installations"""
        return self.config_store.get_installations()

    def add_browser_installation(self, name: str, path: str) -> bool:
        """Add a Zen Browser installation"""
        if not os.path.exists(path):
            raise ProfileError(f"Installation path does not exist: {path}")
            
        # Only allow Zen Browser installations
        if 'zen' not in name.lower():
            raise ProfileError("Only Zen Browser installations are supported")

        return self.config_store.add_installation(name, path)

    def remove_browser_installation(self, name: str) -> bool:
        """Remove a browser installation"""
        return self.config_store.remove_installation(name)

    def get_profiles(self, installation_path: str) -> List[Profile]:
        """Get all profiles for a given browser installation"""
        return self.profile_manager.get_profiles(installation_path)

    def get_profile_by_name(self, installation_path: str, name: str) -> Optional[Profile]:
        """Get a profile by name"""
        return self.profile_manager.get_profile_by_name(installation_path, name)

    def get_default_profile(self, installation_path: str) -> Optional[Profile]:
        """Get the default profile"""
        return self.profile_manager.get_default_profile(installation_path)

    def select_profile(self, installation_path: str, profile_name: Optional[str] = None) -> Profile:
        """
        Select a profile by name or get the default

        Args:
            installation_path: Path to browser installation
            profile_name: Name of profile to select (None for default)

        Returns:
            Selected profile
        """
        if profile_name:
            profile = self.get_profile_by_name(installation_path, profile_name)
            if not profile:
                raise ProfileError(f"Profile not found: {profile_name}")
            return profile
        else:
            profile = self.get_default_profile(installation_path)
            if not profile:
                profiles = self.get_profiles(installation_path)
                if not profiles:
                    raise ProfileError(f"No profiles found in {installation_path}")
                return profiles[0]  # Return first profile if no default
            return profile

    def ensure_chrome_dir(self, profile: Profile) -> str:
        """Ensure chrome directory exists for profile"""
        return self.profile_manager.ensure_chrome_dir(profile)

    def save_last_profile(self, installation: str, profile_name: str) -> bool:
        """Save the last selected profile"""
        return self.config_store.set_last_selected_profile(installation, profile_name)

    def get_last_profile(self) -> Optional[Dict[str, str]]:
        """Get the last selected profile"""
        return self.config_store.get_last_selected_profile()

    def detect_browser_installations(self) -> Dict[str, str]:
        """
        Detect Zen Browser installations on the system

        Returns:
            Dictionary of installation names to paths
        """
        installations = {}
        home_dir = os.path.expanduser('~')

        # Initialize path variables
        zen_paths = []

        # Check for Zen Browser installations based on original code
        if sys.platform.startswith('linux'):
            # Linux-specific Zen Browser paths

            # Flatpak installation
            flatpak_path = os.path.join(
                home_dir,
                '.var',
                'app',
                'io.github.zen_browser.zen',
                '.zen'
            )
            if os.path.exists(flatpak_path):
                installations['Zen Browser (Flatpak)'] = flatpak_path

            # Standard installation
            standard_path = os.path.join(home_dir, '.zen')
            if os.path.exists(standard_path):
                installations['Zen Browser (Standard)'] = standard_path

            # Additional paths to check
            zen_paths = [
                '/usr/lib/zen-browser',
                '/usr/lib64/zen-browser',
                '/opt/zen-browser',
                os.path.expanduser('~/.local/share/zen-browser')
            ]

            # Check .local/share for other possible installations
            local_share = os.path.join(home_dir, '.local', 'share')
            if os.path.exists(local_share):
                for dir_name in os.listdir(local_share):
                    if 'zen' in dir_name.lower():
                        zen_path = os.path.join(local_share, dir_name)
                        if zen_path not in zen_paths:  # Avoid duplicates
                            zen_paths.append(zen_path)

            # Check snap installations
            snap_dir = os.path.join(home_dir, 'snap')
            if os.path.exists(snap_dir):
                for dir_name in os.listdir(snap_dir):
                    if 'zen' in dir_name.lower():
                        snap_path = os.path.join(snap_dir, dir_name, 'current')
                        if os.path.exists(snap_path):
                            installations[f'Zen Browser (Snap - {dir_name})'] = snap_path

        elif sys.platform == 'darwin':
            # macOS paths
            # Standard Zen Browser installation
            zen_dir = os.path.join(
                home_dir,
                'Library',
                'Application Support',
                'zen'
            )
            if os.path.exists(zen_dir):
                installations['Zen Browser'] = zen_dir

            # Typical application paths
            applications = '/Applications'
            zen_paths = [
                os.path.join(applications, 'Zen Browser.app', 'Contents', 'MacOS'),
                os.path.expanduser('~/Applications/Zen Browser.app/Contents/MacOS')
            ]

        elif sys.platform == 'win32':
            # Windows paths
            appdata = os.getenv('APPDATA')
            if appdata:
                zen_dir = os.path.join(appdata, 'zen')
                if os.path.exists(zen_dir):
                    installations['Zen Browser'] = zen_dir

            # Check typical installation directories
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')

            zen_paths = [
                os.path.join(program_files, 'Zen Browser'),
                os.path.join(program_files_x86, 'Zen Browser')
            ]

        # Check remaining zen paths
        for path in zen_paths:
            if os.path.exists(path) and path not in installations.values():
                # Check if this path contains profiles.ini or actual profile directories
                if self._is_valid_browser_installation(path):
                    installations[f'Zen Browser ({os.path.basename(path)})'] = path

        # Also add installations from config, but only keep Zen Browser installations
        saved_installations = self.config_store.get_installations()
        filtered_installations = {k: v for k, v in saved_installations.items() if 'zen' in k.lower()}
        installations.update(filtered_installations)

        # Print debug information about found installations
        print(f"Detected installations: {installations}")

        return installations

    def _is_valid_browser_installation(self, path: str) -> bool:
        """Check if a directory is a valid Zen Browser installation directory"""
        if not os.path.isdir(path):
            return False
        
        # Check for profiles.ini (Zen Browser uses this)
        if os.path.exists(os.path.join(path, 'profiles.ini')):
            return True
        
        # Check for profile directories specific to Zen Browser
        invalid_dirs = {'gmp-clearkey', 'default', 'browser', 'fonts', 'uninstall', 'lib', 'bin', 'share', 
                       'gmp', 'dictionaries', 'extensions', 'features', 'hyphenation', 'minidumps', 'saved-telemetry-pings'}
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                # Skip known non-profile directories
                if item.lower() in invalid_dirs:
                    continue
                # Look for profile directories that are specific to Zen Browser
                if (os.path.exists(os.path.join(item_path, 'prefs.js')) or 
                    os.path.exists(os.path.join(item_path, 'chrome')) or
                    item.startswith('Profile')):
                    return True
        
        return False
