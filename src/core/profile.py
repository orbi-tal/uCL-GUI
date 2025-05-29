import os
import json
from typing import List, Optional, Dict
from .models import Profile
from .exceptions import ProfileError

class ProfileManager:
    def get_profiles(self, installation_path: str) -> List[Profile]:
        """
        Get all profiles for a given browser installation
        """
        profiles = []

        print(f"\nLooking for profiles in: {installation_path}")

        if not os.path.exists(installation_path):
            print(f"Installation path does not exist: {installation_path}")
            return profiles

        # Find profiles.ini path
        profiles_ini_path = None

        # Check if the path is to profiles.ini directly
        if os.path.isfile(installation_path) and os.path.basename(installation_path) == "profiles.ini":
            profiles_ini_path = installation_path
        else:
            # Check for profiles.ini in the directory
            possible_ini = os.path.join(installation_path, "profiles.ini")
            if os.path.exists(possible_ini):
                profiles_ini_path = possible_ini

        if not profiles_ini_path:
            print(f"profiles.ini not found in {installation_path}, looking for profiles directly")
            return self._find_profiles_without_ini(installation_path)

        print(f"Using profiles.ini at: {profiles_ini_path}")

        # Parse profiles.ini
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(profiles_ini_path)

            print(f"Sections in profiles.ini: {config.sections()}")

            for section in config.sections():
                if section.startswith('Profile'):
                    try:
                        # Get profile details, similar to your original implementation
                        path = config.get(section, 'Path', fallback='')
                        is_relative = config.getboolean(section, 'IsRelative', fallback=True)
                        name = config.get(section, 'Name', fallback=os.path.basename(path) or section)
                        is_default = config.getboolean(section, 'Default', fallback=False)

                        # Construct full path
                        if is_relative and path:
                            profile_path = os.path.join(os.path.dirname(profiles_ini_path), path)
                        else:
                            profile_path = path

                        # Create profile object
                        profile = Profile(
                            path=profile_path,
                            name=name,  # Use the proper name
                            is_default=is_default
                        )

                        # Debug info
                        print(f"Found profile:")
                        print(f"  Section: {section}")
                        print(f"  Path: {profile_path}")
                        print(f"  Name: {name}")
                        print(f"  Is Default: {is_default}")

                        if os.path.exists(profile_path):
                            profiles.append(profile)
                        else:
                            print(f"Profile path does not exist: {profile_path}")

                    except Exception as e:
                        print(f"Error processing profile section {section}: {e}")

            return profiles

        except Exception as e:
            print(f"Failed to parse profiles.ini: {str(e)}")
            return self._find_profiles_without_ini(installation_path)


    def _find_zen_profiles(self, installation_path: str) -> List[Profile]:
        """Specifically look for Zen Browser profiles"""
        profiles = []

        print(f"\nLooking for profiles in: {installation_path}")

        # Common profile locations in Zen Browser
        profile_locations = [
            installation_path,
            os.path.join(installation_path, "Profiles"),
            os.path.join(installation_path, "profiles")
        ]

        for location in profile_locations:
            if not os.path.exists(location) or not os.path.isdir(location):
                continue

            print(f"Checking location: {location}")

            # Look for Profile folders
            for item in os.listdir(location):
                if item.startswith("Profile"):
                    profile_path = os.path.join(location, item)
                    if os.path.isdir(profile_path):
                        print(f"Found profile directory: {profile_path}")

                        # Create a profile
                        profile = Profile(
                            path=profile_path,
                            name=item,
                            is_default=False
                        )
                        profiles.append(profile)

        # If we found profiles, mark the first one as default
        if profiles and not any(p.is_default for p in profiles):
            profiles[0].is_default = True

        return profiles

    def _find_profiles_without_ini(self, installation_path: str) -> List[Profile]:
        """Find Zen Browser profiles without relying on profiles.ini"""
        profiles = []

        # Common profile locations to check
        profile_dirs = [
            installation_path,
            os.path.join(installation_path, "Profiles")
        ]

        # Directories that are NOT profiles
        invalid_dirs = {
            'gmp-clearkey', 'default', 'browser', 'fonts', 'uninstall', 
            'lib', 'bin', 'share', 'gmp', 'dictionaries', 'extensions',
            'features', 'hyphenation', 'minidumps', 'saved-telemetry-pings'
        }

        for profile_dir in profile_dirs:
            if os.path.exists(profile_dir) and os.path.isdir(profile_dir):
                # Look for directories that might be profiles
                for item in os.listdir(profile_dir):
                    item_path = os.path.join(profile_dir, item)
                    if os.path.isdir(item_path):
                        # Skip known non-profile directories
                        if item.lower() in invalid_dirs:
                            continue
                            
                        # Check if it's a valid profile directory
                        if self._is_valid_profile_directory(item_path):
                            profile = Profile(
                                path=item_path,
                                name=item,
                                is_default=False  # We don't know which is default
                            )
                            profiles.append(profile)

        # If we found exactly one profile, mark it as default
        if len(profiles) == 1:
            profiles[0].is_default = True

        return profiles

    def _can_create_chrome_dir(self, path: str) -> bool:
        """Check if we can create a chrome directory in this path"""
        return os.access(path, os.W_OK)

    def _is_valid_profile_directory(self, path: str) -> bool:
        """Check if a directory is a valid Zen Browser profile directory"""
        if not os.path.isdir(path):
            return False
            
        # Check for profile indicators
        profile_indicators = [
            'prefs.js',          # Browser preferences file
            'places.sqlite',     # Bookmarks and history database
            'cookies.sqlite',    # Cookies database
            'chrome',            # Chrome directory for CSS
            'extension-preferences.json',
            'sessionstore.jsonlz4'
        ]
        
        # A directory is considered a profile if it has at least one profile indicator
        # or if we can create a chrome directory in it
        for indicator in profile_indicators:
            if os.path.exists(os.path.join(path, indicator)):
                return True
                
        # If no indicators found, check if we can at least write to create chrome dir
        return self._can_create_chrome_dir(path)

    def _process_profile_section(self, profiles: List[Profile],
                                installation_path: str,
                                section_name: str,
                                section_data: Dict[str, str]) -> None:
        """Process a profile section from profiles.ini"""
        if not section_name.startswith('Profile'):
            return

        path = section_data.get('Path', '')

        # Debug raw data
        print(f"Raw profile data for {section_name}: {section_data}")

        # Handle relative paths
        is_relative = section_data.get('IsRelative', '1') == '1'
        if is_relative:
            if path:
                profile_path = os.path.join(installation_path, path)
            else:
                # Sometimes Path is empty - try to use Default to find the profile directory
                profile_number = section_name.replace('Profile', '')
                profile_path = os.path.join(installation_path, f"Profile{profile_number}")

                # If that doesn't exist, try common profile directories
                if not os.path.exists(profile_path):
                    for dir_name in ['Profiles', 'profiles']:
                        test_path = os.path.join(installation_path, dir_name, f"Profile{profile_number}")
                        if os.path.exists(test_path):
                            profile_path = test_path
                            break
        else:
            profile_path = path

        # Extract a meaningful name
        name = section_data.get('Name', '')
        if not name:
            # Use path as fallback name
            name = os.path.basename(profile_path)
            if not name or name == '.zen':
                # Use section name if path basename is empty
                name = f"Profile {section_name.replace('Profile', '')}"

        is_default = section_data.get('Default', '0') == '1'

        # Print debug info
        print(f"Processing profile: {name} at {profile_path} (Default: {is_default})")

        # Check if path exists or if we can create the profile directory
        if os.path.exists(profile_path):
            profiles.append(Profile(
                path=profile_path,
                name=name,
                is_default=is_default
            ))
        else:
            print(f"Profile path does not exist: {profile_path}")
            # Try to find the actual profile directory
            possible_dirs = [
                os.path.join(installation_path, f"Profile{section_name.replace('Profile', '')}"),
                os.path.join(installation_path, "Profiles", f"Profile{section_name.replace('Profile', '')}"),
                os.path.join(installation_path, "profiles", f"Profile{section_name.replace('Profile', '')}")
            ]

            for test_path in possible_dirs:
                if os.path.exists(test_path):
                    print(f"Found alternative profile path: {test_path}")
                    profiles.append(Profile(
                        path=test_path,
                        name=name,
                        is_default=is_default
                    ))
                    break


    def get_profile_by_name(self, installation_path: str, name: str) -> Optional[Profile]:
        """Get a profile by name"""
        profiles = self.get_profiles(installation_path)
        return next((p for p in profiles if p.name == name), None)

    def get_default_profile(self, installation_path: str) -> Optional[Profile]:
        """Get the default profile"""
        profiles = self.get_profiles(installation_path)
        return next((p for p in profiles if p.is_default), None)

    def ensure_chrome_dir(self, profile: Profile) -> str:
        """Ensure the chrome directory exists"""
        if not profile.has_chrome_dir:
            os.makedirs(profile.chrome_dir, exist_ok=True)
        return profile.chrome_dir
