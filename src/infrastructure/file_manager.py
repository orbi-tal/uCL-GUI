import os
import shutil
import tempfile
from typing import List, Optional, Tuple
from src.core.exceptions import FileOperationError

class FileManager:
    """Manages file operations securely and efficiently"""

    def create_directory(self, path: str) -> bool:
        """Create directory and all parent directories if they don't exist"""
        try:
            os.makedirs(path, exist_ok=True)
            
            # Verify directory was created
            if not os.path.exists(path):
                raise FileOperationError(f"Failed to create directory: {path} (directory not found after creation)")
                
            if not os.path.isdir(path):
                raise FileOperationError(f"Failed to create directory: {path} (path exists but is not a directory)")
                
            return True
        except Exception as e:
            raise FileOperationError(f"Failed to create directory {path}: {str(e)}")

    def copy_file(self, source: str, destination: str,
                 overwrite: bool = False) -> bool:
        """
        Copy a file from source to destination

        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite if destination exists
        """
        if not os.path.exists(source):
            raise FileOperationError(f"Source file does not exist: {source}")

        if os.path.exists(destination) and not overwrite:
            raise FileOperationError(f"Destination file already exists: {destination}")

        try:
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(destination)
            self.create_directory(dest_dir)

            # Get source file size for verification
            source_size = os.path.getsize(source)
            
            if source_size == 0:
                # Source file is empty but we'll copy it anyway
                pass

            # Copy the file
            shutil.copy2(source, destination)
            
            # Verify copy succeeded
            if not os.path.exists(destination):
                raise FileOperationError(f"Copy failed: Destination file not found: {destination}")
                
            dest_size = os.path.getsize(destination)
            if dest_size != source_size:
                raise FileOperationError(f"Copy verification failed: Size mismatch - source: {source_size}, destination: {dest_size}")
                
            return True
        except Exception as e:
            raise FileOperationError(f"Failed to copy file: {str(e)}")

    def copy_directory(self, source: str, destination: str,
                      overwrite: bool = False) -> bool:
        """
        Copy a directory from source to destination

        Args:
            source: Source directory path
            destination: Destination directory path
            overwrite: Whether to overwrite if destination exists
        """
        if not os.path.exists(source):
            raise FileOperationError(f"Source directory does not exist: {source}")

        if os.path.exists(destination) and not overwrite:
            raise FileOperationError(f"Destination directory already exists: {destination}")

        try:
            # If destination exists and overwrite is True, remove it first
            if os.path.exists(destination) and overwrite:
                if os.path.isdir(destination):
                    shutil.rmtree(destination)
                else:
                    os.remove(destination)

            # Copy directory
            shutil.copytree(source, destination)
            return True
        except Exception as e:
            raise FileOperationError(f"Failed to copy directory: {str(e)}")

    def remove_file(self, path: str) -> bool:
        """Remove a file"""
        if not os.path.exists(path):
            return True  # Already gone

        if not os.path.isfile(path):
            raise FileOperationError(f"Not a file: {path}")

        try:
            os.remove(path)
            return True
        except Exception as e:
            raise FileOperationError(f"Failed to remove file: {str(e)}")

    def remove_directory(self, path: str) -> bool:
        """Remove a directory and all its contents"""
        if not os.path.exists(path):
            return True  # Already gone

        if not os.path.isdir(path):
            raise FileOperationError(f"Not a directory: {path}")

        try:
            # Remove the directory
            shutil.rmtree(path)
            
            # Verify removal
            if os.path.exists(path):
                raise FileOperationError(f"Failed to remove directory: {path} (still exists after removal)")
                
            return True
        except Exception as e:
            raise FileOperationError(f"Failed to remove directory: {str(e)}")

    def create_temp_file(self, prefix: str = "userchrome_",
                        suffix: str = "") -> str:
        """Create a temporary file and return its path"""
        try:
            fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
            os.close(fd)
            return temp_path
        except Exception as e:
            raise FileOperationError(f"Failed to create temporary file: {str(e)}")

    def create_temp_directory(self, prefix: str = "userchrome_") -> str:
        """Create a temporary directory and return its path"""
        try:
            return tempfile.mkdtemp(prefix=prefix)
        except Exception as e:
            raise FileOperationError(f"Failed to create temporary directory: {str(e)}")

    def check_file_permissions(self, path: str) -> bool:
        """Check if a file is readable and writable"""
        if not os.path.exists(path):
            return True  # File doesn't exist, we'll create it

        return os.access(path, os.R_OK | os.W_OK)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename by removing invalid characters"""
        # Replace characters that are not allowed in filenames
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        return filename

    def get_file_extension(self, path: str) -> str:
        """Get file extension (lowercase)"""
        _, ext = os.path.splitext(path)
        return ext.lower()

    def cleanup_empty_folders(self, root_dir: str) -> int:
        """
        Remove empty folders recursively

        Returns:
            Number of directories removed
        """
        count = 0

        if not os.path.isdir(root_dir):
            return count

        # Walk bottom-up so we can check if directories become empty
        for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
            if not dirnames and not filenames and dirpath != root_dir:
                try:
                    os.rmdir(dirpath)
                    count += 1
                except OSError:
                    # Directory might not be empty or could be locked
                    pass

        return count
