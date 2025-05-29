from typing import Dict, Any, Optional
from src.infrastructure.config_store import ConfigStore

class SettingsService:
    """Service for managing application settings"""

    def __init__(self, config_store: ConfigStore):
        self.config_store = config_store

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.config_store.get(key, default)

    def set_setting(self, key: str, value: Any) -> bool:
        """Set a setting value"""
        return self.config_store.set(key, value)

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        # Return a copy to prevent direct modification
        return dict(self.config_store.config)

    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI-specific settings"""
        return self.config_store.get_section("ui_settings")

    def set_ui_settings(self, settings: Dict[str, Any]) -> bool:
        """Set UI-specific settings"""
        return self.config_store.set_section("ui_settings", settings)

    def get_welcome_shown(self) -> bool:
        """Check if welcome dialog has been shown"""
        return self.get_setting("welcome_shown", False)

    def set_welcome_shown(self, shown: bool = True) -> bool:
        """Set whether welcome dialog has been shown"""
        return self.set_setting("welcome_shown", shown)

    def get_preferred_subfolder(self) -> Optional[str]:
        """Get preferred subfolder option"""
        return self.get_setting("preferred_subfolder")

    def set_preferred_subfolder(self, preference: str) -> bool:
        """Set preferred subfolder option"""
        return self.set_setting("preferred_subfolder", preference)
