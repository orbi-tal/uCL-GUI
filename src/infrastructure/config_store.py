import os
import json
from typing import Any, Dict, Optional
from src.core.exceptions import FileOperationError

class ConfigStore:
    """Store and retrieve application configuration"""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self._load_config()

        # Create directory if it doesn't exist
        config_dir = os.path.dirname(config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not os.path.exists(self.config_file):
            return {}

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            # If file is corrupted or invalid, return empty config
            return {}

    def _save_config(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            raise FileOperationError(f"Failed to save configuration: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value"""
        self.config[key] = value
        return self._save_config()

    def remove(self, key: str) -> bool:
        """Remove a configuration value"""
        if key in self.config:
            del self.config[key]
            return self._save_config()
        return True

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a configuration section"""
        return self.config.get(section, {})

    def set_section(self, section: str, values: Dict[str, Any]) -> bool:
        """Set a configuration section"""
        self.config[section] = values
        return self._save_config()

    def get_last_selected_profile(self) -> Optional[Dict[str, str]]:
        """Get the last selected profile"""
        return self.get('last_profile')

    def set_last_selected_profile(self, installation: str, profile_name: str) -> bool:
        """Set the last selected profile"""
        return self.set('last_profile', {
            'installation': installation,
            'profile': profile_name
        })

    def get_installations(self) -> Dict[str, str]:
        """Get all known browser installations"""
        return self.get('installations', {})

    def add_installation(self, name: str, path: str) -> bool:
        """Add a browser installation"""
        installations = self.get_installations()
        installations[name] = path
        return self.set('installations', installations)

    def remove_installation(self, name: str) -> bool:
        """Remove a browser installation"""
        installations = self.get_installations()
        if name in installations:
            del installations[name]
            return self.set('installations', installations)
        return True
