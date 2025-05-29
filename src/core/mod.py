import os
import json
from typing import List, Optional, Dict
from datetime import datetime
from .models import ModInfo
from .exceptions import FileOperationError

class ModManager:
    """Manage installed mods and their information"""

    def __init__(self):
        self.mods_file = None

    def set_mods_file(self, path: str) -> None:
        """Set the path to the mods info file"""
        self.mods_file = path

        # Create directory if it doesn't exist
        mods_dir = os.path.dirname(path)
        if not os.path.exists(mods_dir):
            os.makedirs(mods_dir, exist_ok=True)

    def save_mod_info(self, mod_info: ModInfo) -> bool:
        """Save information about an installed mod"""
        if not self.mods_file:
            raise FileOperationError("Mods file path not set")

        # Get existing mods
        mods = self.get_all_mods()

        # Update or add mod info
        for i, mod in enumerate(mods):
            if mod.name == mod_info.name:
                mods[i] = mod_info
                break
        else:
            # Mod not found, add it
            mods.append(mod_info)

        # Save back to file
        return self._save_mods(mods)

    def get_mod_info(self, name: str) -> Optional[ModInfo]:
        """Get information about a specific mod by name"""
        if not self.mods_file:
            raise FileOperationError("Mods file path not set")

        # Get all mods
        mods = self.get_all_mods()

        # Find the mod by name
        for mod in mods:
            if mod.name == name:
                return mod

        return None

    def get_all_mods(self) -> List[ModInfo]:
        """Get information about all installed mods"""
        if not self.mods_file:
            raise FileOperationError("Mods file path not set")

        if not os.path.exists(self.mods_file):
            return []

        try:
            with open(self.mods_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert JSON to ModInfo objects
            mods = []
            for mod_data in data:
                # Convert installed_date string to datetime
                if "installed_date" in mod_data and mod_data["installed_date"]:
                    try:
                        mod_data["installed_date"] = datetime.fromisoformat(mod_data["installed_date"])
                    except ValueError:
                        mod_data["installed_date"] = datetime.now()

                # Create ModInfo object
                mods.append(ModInfo(**mod_data))

            return mods

        except Exception as e:
            # If file doesn't exist or is invalid, return empty list
            return []

    def remove_mod(self, name: str) -> bool:
        """Remove a mod from the tracking file"""
        if not self.mods_file:
            raise FileOperationError("Mods file path not set")

        # Get existing mods
        mods = self.get_all_mods()

        # Filter out the mod to remove
        mods = [mod for mod in mods if mod.name != name]

        # Save back to file
        return self._save_mods(mods)

    def _save_mods(self, mods: List[ModInfo]) -> bool:
        """Save mods list to file"""
        try:
            # Convert ModInfo objects to serializable dictionaries
            mod_dicts = []
            for mod in mods:
                mod_dict = mod.__dict__.copy()

                # Convert datetime to string
                if isinstance(mod_dict["installed_date"], datetime):
                    mod_dict["installed_date"] = mod_dict["installed_date"].isoformat()

                mod_dicts.append(mod_dict)

            # Save to file
            with open(self.mods_file, 'w', encoding='utf-8') as f:
                json.dump(mod_dicts, f, indent=2)

            return True

        except Exception as e:
            raise FileOperationError(f"Failed to save mods file: {str(e)}")
