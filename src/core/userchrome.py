import os
import re
import shutil
from typing import List, Optional, Tuple, Dict, Set
from .models import Profile, ImportEntry
from .exceptions import FileOperationError, CircularImportError

class UserChromeManager:
    """Manages UserChrome CSS files and import statements"""

    # Updated regex patterns for import statements
    # These patterns match both quoted and unquoted URLs
    IMPORT_PATTERN = re.compile(r'@import\s+url\([\'"]?(.+?)[\'"]?\);')
    COMMENTED_IMPORT_PATTERN = re.compile(r'/\*\s*@import\s+url\([\'"]?(.+?)[\'"]?\);\s*\*/')

    def read_userchrome(self, profile):
        """Read the userChrome.css file content"""
        if not profile.has_userchrome:
            return None

        try:
            with open(profile.userchrome_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with another encoding if UTF-8 fails
            with open(profile.userchrome_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            raise FileOperationError(f"Failed to read userChrome.css: {str(e)}")

    def write_userchrome(self, profile: Profile, content: str) -> bool:
        """Write content to userChrome.css file"""
        try:
            # Ensure chrome directory exists
            os.makedirs(profile.chrome_dir, exist_ok=True)

            # Write the file
            with open(profile.userchrome_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True
        except Exception as e:
            raise FileOperationError(f"Failed to write userChrome.css: {str(e)}")

    def backup_userchrome(self, profile: Profile) -> Optional[str]:
        """
        Create a backup of userChrome.css

        Returns:
            Path to the backup file or None if no userChrome.css exists
        """
        if not profile.has_userchrome:
            return None

        try:
            backup_path = f"{profile.userchrome_path}.backup"
            shutil.copy2(profile.userchrome_path, backup_path)
            return backup_path
        except Exception as e:
            raise FileOperationError(f"Failed to create backup: {str(e)}")

    def restore_from_backup(self, profile: Profile) -> bool:
        """Restore userChrome.css from backup"""
        backup_path = f"{profile.userchrome_path}.backup"

        if not os.path.exists(backup_path):
            raise FileOperationError("Backup file does not exist")

        try:
            shutil.copy2(backup_path, profile.userchrome_path)
            return True
        except Exception as e:
            raise FileOperationError(f"Failed to restore backup: {str(e)}")

    def cleanup_backup(self, profile: Profile) -> bool:
        """Delete backup file"""
        backup_path = f"{profile.userchrome_path}.backup"

        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
                return True
            except Exception as e:
                raise FileOperationError(f"Failed to delete backup: {str(e)}")

        return True  # No backup to delete

    def get_imports(self, content):
        """Extract all imports from userChrome.css content"""
        imports = []
        seen_paths = set()

        # Find all active imports
        for match in self.IMPORT_PATTERN.finditer(content):
            path = match.group(1)
            normalized_path = self._normalize_import_path(path)
            start_pos = match.start()
            line_number = content[:start_pos].count('\n') + 1

            # Check if this import is inside a comment block
            is_commented = False
            for comment_match in re.finditer(r'/\*.*?\*/', content, re.DOTALL):
                if comment_match.start() <= start_pos < comment_match.end():
                    is_commented = True
                    break

            # Only add if we haven't seen this path before
            if normalized_path not in seen_paths:
                imports.append(ImportEntry(
                    path=path,
                    enabled=not is_commented,
                    line_number=line_number
                ))
                seen_paths.add(normalized_path)

        # Find all commented (disabled) imports that weren't already found
        for match in self.COMMENTED_IMPORT_PATTERN.finditer(content):
            path = match.group(1)
            normalized_path = self._normalize_import_path(path)
            start_pos = match.start()
        
            # Only add if we haven't seen this path before
            if normalized_path not in seen_paths:
                imports.append(ImportEntry(
                    path=path,
                    enabled=False,
                    line_number=content[:start_pos].count('\n') + 1
                ))
                seen_paths.add(normalized_path)

        # Debug output
        print(f"Found {len(imports)} imports in userChrome.css:")
        for imp in imports:
            print(f"  - {imp.path} (enabled: {imp.enabled}, line: {imp.line_number})")

        return imports

    def has_import(self, content: str, import_path: str) -> bool:
        """Check if an import for the given path exists (enabled or disabled)"""
        # Normalize path for comparison
        import_path = self._normalize_import_path(import_path)

        imports = self.get_imports(content)
        for import_entry in imports:
            normalized_path = self._normalize_import_path(import_entry.path)
            if normalized_path == import_path:
                return True

        return False

    def _normalize_import_path(self, path: str) -> str:
        """Normalize an import path for comparison"""
        # Replace backslashes with forward slashes
        path = path.replace('\\', '/')

        # Remove leading ./ if present
        if path.startswith('./'):
            path = path[2:]

        return path.strip()

    def add_import(self, content: str, import_path: str) -> str:
        """Add an import statement to userChrome.css content"""
        if self.has_import(content, import_path):
            return content  # Already exists

        # Find the position to insert the import
        last_import_pos = self._get_last_import_position(content)

        if last_import_pos >= 0:
            # Insert after the last import
            return (content[:last_import_pos] +
                   f'\n@import url("{import_path}");' +
                   content[last_import_pos:])
        else:
            # No existing imports, add at the beginning
            return f'@import url("{import_path}");\n\n{content}'

    def toggle_import(self, content: str, import_path: str) -> str:
        """Toggle an import on or off"""
        # Normalize path for comparison
        import_path = self._normalize_import_path(import_path)

        # Pattern for the specific import
        pattern = re.compile(
            rf'(/\*\s*)?@import\s+url\(["\']({re.escape(import_path)})["\']\);(\s*\*/)?'
        )

        def toggle_replacement(match):
            if match.group(1) is not None:
                # It's commented out, uncomment it
                return f'@import url("{match.group(2)}");'
            else:
                # It's not commented out, comment it
                return f'/* @import url("{match.group(2)}"); */'

        return pattern.sub(toggle_replacement, content)

    def remove_import(self, content: str, import_path: str) -> str:
        """Remove an import statement from userChrome.css content"""
        # Normalize path for comparison
        import_path = self._normalize_import_path(import_path)

        # Pattern for the specific import (with or without comment)
        pattern = re.compile(
            rf'(/\*\s*)?@import\s+url\(["\']({re.escape(import_path)})["\']\);(\s*\*/)?'
        )

        # First find all matches to handle line endings properly
        matches = list(pattern.finditer(content))
        if not matches:
            return content  # No matches

        # Process in reverse order to not affect offsets
        result = content
        for match in reversed(matches):
            start, end = match.span()

            # Find the full line(s) to remove
            line_start = result.rfind('\n', 0, start) + 1
            line_end = result.find('\n', end)
            if line_end == -1:
                line_end = len(result)

            # Remove the line(s)
            result = result[:line_start] + result[line_end:]

        return result

    def _get_last_import_position(self, content: str) -> int:
        """Get the position after the last import statement"""
        imports = []

        # Find all imports (normal and commented)
        for match in self.IMPORT_PATTERN.finditer(content):
            imports.append((match.start(), match.end()))

        for match in self.COMMENTED_IMPORT_PATTERN.finditer(content):
            imports.append((match.start(), match.end()))

        if not imports:
            return -1

        # Sort by end position
        imports.sort(key=lambda x: x[1])

        # Return the position after the last import
        _, last_pos = imports[-1]

        # Find the end of the line
        line_end = content.find('\n', last_pos)
        if line_end == -1:
            return len(content)

        return line_end

    def check_circular_imports(self, profile: Profile, new_import_path: str,
                             processed_paths: Optional[Set[str]] = None) -> bool:
        """
        Check for circular imports when adding a new import

        Returns:
            True if a circular import is detected
        """
        if processed_paths is None:
            processed_paths = set()

        # Normalize paths for comparison
        new_import_path = self._normalize_import_path(new_import_path)

        # Add current path to processed paths
        processed_paths.add(new_import_path)

        # Build the full path to the imported file
        import_file_path = os.path.join(profile.chrome_dir, new_import_path)

        # Check if the imported file exists
        if not os.path.isfile(import_file_path):
            return False  # File doesn't exist, no imports to check

        try:
            # Read the content of the imported file
            with open(import_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Get all imports from the file
            imports = self.get_imports(content)

            for import_entry in imports:
                path = self._normalize_import_path(import_entry.path)

                # Check if this path has already been processed (circular import)
                if path in processed_paths:
                    return True

                # Recursively check this import
                if self.check_circular_imports(profile, path, processed_paths):
                    return True

            return False

        except Exception:
            # If we can't read the file, assume no circular imports
            return False

    def ensure_chrome_dir(self, profile):
        """Ensure the chrome directory exists"""
        chrome_dir = profile.chrome_dir
        if not os.path.exists(chrome_dir):
            os.makedirs(chrome_dir, exist_ok=True)
        return chrome_dir
