import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class Profile:
    """Represents a browser profile"""
    path: str
    name: str
    is_default: bool = False

    def __post_init__(self):
        # Ensure name is never empty
        if not self.name:
            self.name = os.path.basename(self.path) or "Unnamed Profile"

    @property
    def chrome_dir(self) -> str:
        return os.path.join(self.path, "chrome")

    @property
    def userchrome_path(self) -> str:
        return os.path.join(self.chrome_dir, "userChrome.css")

    @property
    def has_chrome_dir(self) -> bool:
        return os.path.exists(self.chrome_dir)

    @property
    def has_userchrome(self) -> bool:
        return os.path.exists(self.userchrome_path)

    def __str__(self) -> str:
        return f"Profile(name='{self.name}', path='{self.path}', default={self.is_default})"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class ModInfo:
    """Information about an installed mod"""
    name: str
    source_url: Optional[str] = None
    version: Optional[str] = None
    installed_date: datetime = field(default_factory=datetime.now)
    files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_file(self, file_path: str) -> None:
        if file_path not in self.files:
            self.files.append(file_path)
    
    @property
    def commit_hash(self) -> Optional[str]:
        """Get the commit hash for this mod (used as version)"""
        return self.metadata.get("latest_commit")
    
    @property
    def display_version(self) -> str:
        """Get a display-friendly version string"""
        if self.commit_hash:
            return self.commit_hash[:8]  # Short commit hash
        elif self.version:
            return self.version
        else:
            return "Unknown"
    
    def set_commit_hash(self, commit_hash: str) -> None:
        """Set the commit hash for this mod"""
        if not self.metadata:
            self.metadata = {}
        self.metadata["latest_commit"] = commit_hash
        # Also set version to commit hash for consistency
        self.version = commit_hash[:8]

@dataclass
class ImportEntry:
    """Represents an import in the userChrome.css file"""
    path: str
    enabled: bool = True
    line_number: Optional[int] = None

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)
