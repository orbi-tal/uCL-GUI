import os
import tempfile
import zipfile
import tarfile
import shutil
from typing import List, Optional, Tuple, Set
from .exceptions import ArchiveError

class ArchiveProcessor:
    """Handle archive extraction and processing"""

    def __init__(self):
        self.supported_extensions = {
            '.zip': self._extract_zip,
            '.xpi': self._extract_zip,  # XPI is just a ZIP
            '.tar': self._extract_tar,
            '.tar.gz': self._extract_tar,
            '.tgz': self._extract_tar,
            '.tar.bz2': self._extract_tar,
            '.tbz2': self._extract_tar
        }

    def is_archive(self, file_path: str) -> bool:
        """Check if a file is a supported archive"""
        if not os.path.isfile(file_path):
            return False

        file_lower = file_path.lower()

        for ext in self.supported_extensions:
            if file_lower.endswith(ext):
                return True

        return False

    def extract_archive(self, archive_path: str,
                       extract_dir: Optional[str] = None) -> str:
        """
        Extract an archive to a directory

        Args:
            archive_path: Path to the archive file
            extract_dir: Directory to extract to (creates temp dir if not provided)

        Returns:
            Path to the extracted directory
        """
        if not self.is_archive(archive_path):
            raise ArchiveError(f"Unsupported archive format: {archive_path}")

        # Create extraction directory if not provided
        if not extract_dir:
            extract_dir = tempfile.mkdtemp(prefix="userchrome_extract_")

        # Find the appropriate extraction method
        file_lower = archive_path.lower()
        for ext, extract_func in self.supported_extensions.items():
            if file_lower.endswith(ext):
                try:
                    return extract_func(archive_path, extract_dir)
                except Exception as e:
                    # Clean up on failure
                    if not os.path.exists(extract_dir):
                        shutil.rmtree(extract_dir, ignore_errors=True)
                    raise ArchiveError(f"Failed to extract archive: {str(e)}")

        # This should never happen due to the is_archive check
        raise ArchiveError(f"Unsupported archive format: {archive_path}")

    def _extract_zip(self, archive_path: str, extract_dir: str) -> str:
        """Extract a ZIP archive"""
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            # Check for dangerous paths (path traversal)
            for file_info in zip_ref.infolist():
                file_path = file_info.filename
                if file_path.startswith('/') or '..' in file_path:
                    raise ArchiveError(f"Potentially unsafe path in archive: {file_path}")

            # Extract all files
            zip_ref.extractall(extract_dir)

        return extract_dir

    def _extract_tar(self, archive_path: str, extract_dir: str) -> str:
        """Extract a TAR archive (including compressed variants)"""
        mode = 'r'
        if archive_path.lower().endswith(('.tar.gz', '.tgz')):
            mode = 'r:gz'
        elif archive_path.lower().endswith(('.tar.bz2', '.tbz2')):
            mode = 'r:bz2'

        with tarfile.open(archive_path, mode) as tar_ref:
            # Check for dangerous paths
            for member in tar_ref.getmembers():
                file_path = member.name
                if file_path.startswith('/') or '..' in file_path:
                    raise ArchiveError(f"Potentially unsafe path in archive: {file_path}")

            # Extract all files
            tar_ref.extractall(extract_dir)

        return extract_dir

    def find_css_files(self, directory: str) -> List[str]:
        """Find all CSS files in a directory (recursive)"""
        css_files = []

        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.css'):
                    css_files.append(os.path.join(root, file))

        return css_files

    def validate_extracted_content(self, extract_dir: str) -> Tuple[bool, List[str]]:
        """
        Validate extracted content to ensure it contains usable CSS files

        Returns:
            Tuple of (is_valid, css_file_list)
        """
        # Find all CSS files
        css_files = self.find_css_files(extract_dir)

        # Check if there are any CSS files
        if not css_files:
            return False, []

        return True, css_files
