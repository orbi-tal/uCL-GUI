import os
import shutil
import stat
import time
import platform
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from ..core.models import Profile, ModInfo, ImportEntry
from ..core.download import DownloadManager
from ..core.archive import ArchiveProcessor
from ..core.userchrome import UserChromeManager
from ..core.mod import ModManager
from ..infrastructure.file_manager import FileManager
from ..infrastructure.github_api import GitHubApi
from ..infrastructure.gitlab_api import GitLabApi
from ..core.exceptions import ImportError, ValidationError
import re
import tempfile
import subprocess
import platform
import os
import shutil
import time
import traceback
import traceback

class ImportService:
    """Service for importing UserChrome customizations"""

    def __init__(self, download_manager: DownloadManager,
                archive_processor: ArchiveProcessor,
                userchrome_manager: UserChromeManager,
                mod_manager: ModManager,
                file_manager: FileManager,
                github_api: GitHubApi,
                gitlab_api: GitLabApi):
        self.download_manager = download_manager
        self.archive_processor = archive_processor
        self.userchrome_manager = userchrome_manager
        self.mod_manager = mod_manager
        self.file_manager = file_manager
        self.github_api = github_api
        self.gitlab_api = gitlab_api

    def import_from_url(self, profile: Profile, url: str,
                      mod_name: Optional[str] = None) -> Tuple[bool, str, Optional[ModInfo]]:
        """
        Import CSS from a URL into the selected profile

        Returns:
            Tuple of (success, message, mod_info)
        """
        try:
            # Validate URL
            if not self.download_manager.validate_url(url):
                raise ValidationError(f"Invalid URL: {url}")

            # Determine URL type and handle accordingly
            if "github.com" in url:
                return self._import_from_github(profile, url, mod_name)
            elif "gitlab.com" in url:
                return self._import_from_gitlab(profile, url, mod_name)
            else:
                return self._import_from_direct_url(profile, url, mod_name)
        except Exception as e:
            return False, f"GitLab import failed: {str(e)}", None

    def _import_from_github(self, profile: Profile, url: str,
                         mod_name: Optional[str] = None) -> Tuple[bool, str, Optional[ModInfo]]:
        """Import from GitHub URL"""
        try:
            # Download content from GitHub
            temp_path, mod_info = self.download_manager.handle_github_url(url)

            if not mod_name:
                mod_name = mod_info.name

            # Get commit hash for version tracking
            try:
                # Parse GitHub URL to get owner/repo info
                parts = url.split("github.com/", 1)[1].split("/")
                if len(parts) >= 2:
                    owner = parts[0]
                    repo = parts[1]
                    branch = "main"  # Default branch
                    
                    # If URL specifies a branch, extract it
                    if len(parts) > 3 and parts[2] in ["blob", "tree"]:
                        branch = parts[3]
                    
                    # Get latest commit hash
                    latest_commit = self.github_api.get_latest_commit(owner, repo, branch)
                    commit_sha = latest_commit.get("sha", "")
                    
                    if commit_sha:
                        mod_info.set_commit_hash(commit_sha)
                        # Update metadata with GitHub info
                        mod_info.metadata.update({
                            "type": "github",
                            "owner": owner,
                            "repo": repo,
                            "branch": branch
                        })
            except Exception:
                # If we can't get commit info, continue without it
                pass

            # Process the downloaded content
            if self.archive_processor.is_archive(temp_path):
                # Process the archive
                extract_dir = self.archive_processor.extract_archive(temp_path)

                # Find CSS files
                is_valid, css_files = self.archive_processor.validate_extracted_content(extract_dir)
                if not is_valid:
                    self.file_manager.remove_directory(extract_dir)
                    os.remove(temp_path)
                    raise ImportError("No CSS files found in the archive")

                # Import the CSS files
                return self._import_extracted_files(profile, css_files, extract_dir, mod_name, url, mod_info)
            else:
                # Single file - check if it's CSS
                if not temp_path.lower().endswith('.css'):
                    os.remove(temp_path)
                    raise ImportError(f"Not a CSS file: {os.path.basename(temp_path)}")

                # Import the single file
                return self._import_single_file(profile, temp_path, mod_name, url, mod_info)

        except Exception as e:
            return False, f"GitHub import failed: {str(e)}", None

    def _import_from_gitlab(self, profile: Profile, url: str,
                            mod_name: Optional[str] = None) -> Tuple[bool, str, Optional[ModInfo]]:
        """Import from GitLab URL"""
        try:
            # Parse GitLab URL
            gitlab_info = self.gitlab_api.parse_gitlab_url(url)

            # Get project info to get ID
            project_info = self.gitlab_api.get_project_info(gitlab_info['project_path'])
            project_id = project_info['id']

            # Get commit hash for version tracking
            mod_info = None
            try:
                # Get latest commit hash
                latest_commit = self.gitlab_api.get_latest_commit(project_id, gitlab_info['branch'])
                commit_sha = latest_commit.get("id", "")
            except Exception:
                commit_sha = ""

            # Determine what to download
            if gitlab_info['file_path'] and gitlab_info['file_path'].lower().endswith('.css'):
                # Single CSS file
                content, file_info = self.gitlab_api.get_file_content(
                    project_id, gitlab_info['file_path'], gitlab_info['branch'])

                # Save to temp file
                temp_path = self.file_manager.create_temp_file(suffix=".css")
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                # Create mod info
                file_name = os.path.basename(gitlab_info['file_path'])
                if not mod_name:
                    mod_name = file_name

                mod_info = ModInfo(
                    name=mod_name,
                    source_url=url,
                    files=[file_name]
                )

                # Set commit info
                if commit_sha:
                    mod_info.set_commit_hash(commit_sha)
                    mod_info.metadata.update({
                        "type": "gitlab",
                        "project_id": project_id,
                        "project_path": gitlab_info['project_path'],
                        "branch": gitlab_info['branch']
                    })

                # Import the single file
                return self._import_single_file(profile, temp_path, mod_name, url, mod_info)
            else:
                # Repository download
                download_url = self.gitlab_api.get_download_url(project_id, gitlab_info['branch'])

                # Download zip to temp location
                temp_path = self.file_manager.create_temp_file(suffix=".zip")
                self.download_manager.download_file(download_url, temp_path)

                # Create mod info
                if not mod_name:
                    mod_name = project_info['name']

                mod_info = ModInfo(
                    name=mod_name,
                    source_url=url,
                    metadata={
                        "type": "gitlab",
                        "project_id": project_id,
                        "project_path": gitlab_info['project_path'],
                        "branch": gitlab_info['branch']
                    }
                )

                # Set commit info
                if commit_sha:
                    mod_info.set_commit_hash(commit_sha)

                # Process the archive
                extract_dir = self.archive_processor.extract_archive(temp_path)

                # Find CSS files
                is_valid, css_files = self.archive_processor.validate_extracted_content(extract_dir)
                if not is_valid:
                    self.file_manager.remove_directory(extract_dir)
                    os.remove(temp_path)
                    raise ImportError("No CSS files found in the archive")

                # Import the CSS files
                return self._import_extracted_files(profile, css_files, extract_dir, mod_name, url, mod_info)

        except Exception as e:
            return False, f"Failed to import files: {str(e)}", None

    def _import_from_direct_url(self, profile: Profile, url: str,
                                mod_name: Optional[str] = None) -> Tuple[bool, str, Optional[ModInfo]]:
        """Import from direct URL"""
        try:
            # Download file to temp location
            temp_fd, temp_path = tempfile.mkstemp(prefix="userchrome_")
            os.close(temp_fd)

            self.download_manager.download_file(url, temp_path)

            # Get file name from URL for mod name if not provided
            if not mod_name:
                file_name = os.path.basename(url.split('?')[0])  # Remove URL parameters
                mod_name = file_name

            # Create ModInfo
            mod_info = ModInfo(
                name=mod_name,
                source_url=url,
                files=[]  # Initialize with empty list to avoid NoneType errors
            )

            # Process the downloaded content
            if self.archive_processor.is_archive(temp_path):
                # Process the archive
                extract_dir = self.archive_processor.extract_archive(temp_path)

                # Find CSS files
                is_valid, css_files = self.archive_processor.validate_extracted_content(extract_dir)
                if not is_valid:
                    self.file_manager.remove_directory(extract_dir)
                    os.remove(temp_path)
                    raise ImportError("No CSS files found in the archive")

                # Import the CSS files
                return self._import_extracted_files(profile, css_files, extract_dir, mod_name, url, mod_info)
            elif temp_path.lower().endswith('.css'):
                # Single CSS file
                return self._import_single_file(profile, temp_path, mod_name, url, mod_info)
            else:
                # Not a CSS file or archive
                os.remove(temp_path)
                raise ImportError(f"Unsupported file type: {os.path.basename(url)}")

        except Exception as e:
            return False, f"URL import failed: {str(e)}", None

    def _import_single_file(self, profile: Profile, css_file: str,
                            mod_name: str, source_url: str,
                            mod_info: Optional[ModInfo] = None) -> Tuple[bool, str, Optional[ModInfo]]:
        """Import a single CSS file"""
        try:
            # Make sure chrome directory exists
            chrome_dir = self.userchrome_manager.ensure_chrome_dir(profile)

            # Generate target path
            file_name = os.path.basename(css_file)
            sanitized_name = self.file_manager.sanitize_filename(file_name)
            target_path = os.path.join(chrome_dir, sanitized_name)

            # Copy the file
            self.file_manager.copy_file(css_file, target_path, overwrite=True)

            # Clean up temporary file
            os.remove(css_file)

            # Update userChrome.css
            success = self._update_userchrome(profile, sanitized_name)

            # Update or create mod info
            if not mod_info:
                mod_info = ModInfo(
                    name=mod_name,
                    source_url=source_url,
                    files=[sanitized_name]  # Initialize with the sanitized filename
                )
            else:
                # Initialize files list if needed
                if not hasattr(mod_info, 'files') or mod_info.files is None:
                    mod_info.files = []
                
                # Ensure the file is in the list
                if sanitized_name not in mod_info.files:
                    mod_info.files.append(sanitized_name)

            # Save mod info
            self.mod_manager.save_mod_info(mod_info)

            return True, f"Successfully imported {file_name}", mod_info

        except Exception as e:
            return False, f"Failed to import file: {str(e)}", None

    def _import_extracted_files(self, profile: Profile, css_files: List[str],
                             extract_dir: str, mod_name: str, source_url: str,
                             mod_info: Optional[ModInfo] = None) -> Tuple[bool, str, Optional[ModInfo]]:
        """Import CSS files from an extracted archive"""
        try:
            # Check if userChrome.css exists in the extracted files
            userchrome_files = [f for f in css_files if os.path.basename(f).lower() == 'userchrome.css']

            # Import ALL CSS files, not just userChrome.css
            css_files_to_import = css_files
            
            # Keep track of main userChrome.css files separately for the import statement
            if userchrome_files:
                # Get relative paths for display
                rel_css_files = [os.path.relpath(f, extract_dir) for f in css_files]
                
                # We need to provide a way to select files without requiring UI interaction
                # For now, just use all CSS files
                css_files_to_import = css_files

            # Make sure chrome directory exists
            chrome_dir = self.userchrome_manager.ensure_chrome_dir(profile)

            # Create a subdirectory for the mod
            sanitized_name = self.file_manager.sanitize_filename(mod_name)
            mod_dir = os.path.join(chrome_dir, sanitized_name)

            # Create directory if it doesn't exist
            self.file_manager.create_directory(mod_dir)

            # Copy CSS files
            imported_files = []

            # Determine the repository root directory (e.g., "Pineapple-Fried-main")
            repo_dirs = set()
            for css_file in css_files_to_import:
                rel_path = os.path.relpath(css_file, extract_dir)
                first_dir = rel_path.split(os.path.sep)[0]
                repo_dirs.add(first_dir)
            
            repo_root_dir = next(iter(repo_dirs)) if len(repo_dirs) == 1 else None

            # Use the css_files_to_import that we've already determined
            for css_file in css_files_to_import:
                # Get relative path within extract directory
                rel_path = os.path.relpath(css_file, extract_dir)
                
                # Remove the repository root directory from the path if it exists
                if repo_root_dir and rel_path.startswith(repo_root_dir + os.path.sep):
                    rel_path = os.path.relpath(rel_path, repo_root_dir)

                # Create target path
                target_path = os.path.join(mod_dir, rel_path)

                # Create directory structure if needed
                target_dir = os.path.dirname(target_path)
                self.file_manager.create_directory(target_dir)

                # Copy the file
                self.file_manager.copy_file(css_file, target_path, overwrite=True)

                # Add to imported files list
                import_path = os.path.join(sanitized_name, rel_path).replace('\\', '/')
                imported_files.append(import_path)

            # Clean up temporary files after copying is complete
            # Copy additional CSS files referenced in userChrome.css
            # Get the content of main userChrome.css to find referenced files
            if userchrome_files:
                for userchrome_file in userchrome_files:
                    try:
                        with open(userchrome_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Find all imports in the userChrome.css file
                        import_pattern = re.compile(r'@import\s+(?:url\([\'"]?)?([^\'"\)]+)[\'"]?\)?;')
                        for match in import_pattern.finditer(content):
                            import_path = match.group(1).strip()
                            
                            # Convert relative path to absolute
                            userchrome_dir = os.path.dirname(userchrome_file)
                            abs_import_path = os.path.normpath(os.path.join(userchrome_dir, import_path))
                            
                            # Find this file or directory in the extracted content
                            if os.path.exists(abs_import_path):
                                if os.path.isdir(abs_import_path):
                                    # If it's a directory, make sure we copy all files in it
                                    for root, _, files in os.walk(abs_import_path):
                                        for file in files:
                                            if file.lower().endswith('.css'):
                                                full_path = os.path.join(root, file)
                                                if full_path not in css_files_to_import:
                                                    css_files_to_import.append(full_path)
                                else:
                                    # It's a file, make sure it's in our list
                                    if abs_import_path not in css_files_to_import and abs_import_path.lower().endswith('.css'):
                                        css_files_to_import.append(abs_import_path)
                    except Exception:
                        pass  # Silently ignore import processing errors
            
            # Clean up temporary files
            
            # Update userChrome.css for the main CSS files (not imported by others)
            # Always add the main userChrome.css file as an import if it exists
            if len(userchrome_files) > 0:
                # If we have userChrome.css, import that
                for css_file in userchrome_files:
                    rel_path = os.path.relpath(css_file, extract_dir)
                    # Remove the repository root directory from the path if it exists
                    if repo_root_dir and rel_path.startswith(repo_root_dir + os.path.sep):
                        rel_path = os.path.relpath(rel_path, repo_root_dir)
                    import_path = os.path.join(sanitized_name, rel_path).replace('\\', '/')
                    self._update_userchrome(profile, import_path)
            else:
                # Otherwise, find main CSS files that aren't imported by others
                main_css_files = self._find_main_css_files(css_files_to_import, extract_dir)
                if not main_css_files:
                    main_css_files = css_files_to_import
                
                for css_file in main_css_files:
                    rel_path = os.path.relpath(css_file, extract_dir)
                    # Remove the repository root directory from the path if it exists
                    if repo_root_dir and rel_path.startswith(repo_root_dir + os.path.sep):
                        rel_path = os.path.relpath(rel_path, repo_root_dir)
                    import_path = os.path.join(sanitized_name, rel_path).replace('\\', '/')
                    self._update_userchrome(profile, import_path)
                    
            # Now remove the extract directory after we've done all our processing
            self.file_manager.remove_directory(extract_dir)

            # Update or create mod info
            if not mod_info:
                mod_info = ModInfo(
                    name=mod_name,
                    source_url=source_url,
                    files=imported_files.copy()  # Use copy to avoid reference issues
                )
            else:
                # Ensure files attribute exists
                if not hasattr(mod_info, 'files') or mod_info.files is None:
                    mod_info.files = []
                
                # Add all imported files
                for file_path in imported_files:
                    if file_path not in mod_info.files:
                        mod_info.files.append(file_path)

            # Save mod info
            self.mod_manager.save_mod_info(mod_info)

            return True, f"Successfully imported {len(imported_files)} files", mod_info

        except Exception as e:
            return False, f"Failed to import files: {str(e)}", None


    def _find_main_css_files(self, css_files: List[str], extract_dir: str) -> List[str]:
        """Find CSS files that are not imported by other CSS files"""
        # Track which files are imported by others
        imported_by_others = set()

        # Check all CSS files for imports
        for css_file in css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find all imports in this file
                imports = self.userchrome_manager.get_imports(content)

                for import_entry in imports:
                    # Resolve the import path relative to this file
                    file_dir = os.path.dirname(css_file)
                    import_path = os.path.normpath(os.path.join(file_dir, import_entry.path))

                    # If this import points to another CSS file in our list, mark it
                    if import_path in css_files:
                        imported_by_others.add(import_path)

            except Exception as e:
                # If we can't read the file, just continue
                continue

        # Return files that aren't imported by others
        return [f for f in css_files if f not in imported_by_others]

    def _update_userchrome(self, profile: Profile, import_path: str) -> bool:
        """Add import to userChrome.css file"""
        try:
            # Read existing content or create new
            content = self.userchrome_manager.read_userchrome(profile)
            if not content:
                content = "/* UserChrome.css */\n\n"

            # Check if import already exists
            has_import = self.userchrome_manager.has_import(content, import_path)

            # Add import if it doesn't exist
            if not has_import:
                content = self.userchrome_manager.add_import(content, import_path)
                self.userchrome_manager.write_userchrome(profile, content)
            
            return True
        except Exception as e:
            return False

    def import_from_file(self, profile: Profile, file_path: str,
                        mod_name: Optional[str] = None) -> Tuple[bool, str, Optional[ModInfo]]:
        """Import a local CSS file"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Use file name as mod name if not provided
            if not mod_name:
                mod_name = os.path.basename(file_path)

            # Check if it's an archive
            if self.archive_processor.is_archive(file_path):
                # Process the archive
                # Extract archive
                extract_dir = self.archive_processor.extract_archive(file_path)

                # Find CSS files
                is_valid, css_files = self.archive_processor.validate_extracted_content(extract_dir)
                if not is_valid:
                    self.file_manager.remove_directory(extract_dir)
                    raise ImportError("No CSS files found in the archive")

                # Import the CSS files
                return self._import_extracted_files(profile, css_files, extract_dir, mod_name, None)
            elif file_path.lower().endswith('.css'):
                # Create a temporary copy of the file
                temp_path = self.file_manager.create_temp_file(suffix=".css")
                self.file_manager.copy_file(file_path, temp_path)

                # Import the single file
                return self._import_single_file(profile, temp_path, mod_name, None)
            else:
                # Not a CSS file or archive
                raise ImportError(f"Unsupported file type: {os.path.basename(file_path)}")

        except Exception as e:
            return False, f"File import failed: {str(e)}", None

    def import_from_directory(self, profile: Profile, dir_path: str,
                            mod_name: Optional[str] = None) -> Tuple[bool, str, Optional[ModInfo]]:
        """Import CSS files from a local directory"""
        try:
            # Check if directory exists
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                raise FileNotFoundError(f"Directory not found: {dir_path}")

            # Use directory name as mod name if not provided
            if not mod_name:
                mod_name = os.path.basename(dir_path)

            # Find CSS files
            css_files = self.archive_processor.find_css_files(dir_path)
            if not css_files:
                raise ImportError(f"No CSS files found in {dir_path}")

            # Create a temporary directory for processing
            temp_dir = self.file_manager.create_temp_directory()

            # Copy the directory structure to the temp directory
            for css_file in css_files:
                # Get relative path within source directory
                rel_path = os.path.relpath(css_file, dir_path)

                # Create target path
                target_path = os.path.join(temp_dir, rel_path)

                # Create directory structure if needed
                target_dir = os.path.dirname(target_path)
                self.file_manager.create_directory(target_dir)

                # Copy the file
                self.file_manager.copy_file(css_file, target_path)

            # Find the CSS files in the temp directory
            temp_css_files = self.archive_processor.find_css_files(temp_dir)

            # Import the CSS files
            return self._import_extracted_files(profile, temp_css_files, temp_dir, mod_name, None)

        except Exception as e:
            return False, f"Directory import failed: {str(e)}", None

    def _delete_directory_forcefully(self, directory_path: str) -> bool:
        """
        Force delete a directory using multiple methods.
        
        Args:
            directory_path: Path to the directory to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        # This method is no longer used, but kept for backward compatibility
        # The direct system command approach is now used in remove_import
        return False
    
    def _print_directory_tree(self, directory_path, indent="  ", is_last=True, prefix=""):
        """Print a directory tree structure with file details"""
        # This method is no longer used, but kept for backward compatibility
        pass
    
    def remove_import(self, profile: Profile, import_path: str) -> Tuple[bool, str]:
        """Remove an import from userChrome.css and delete associated mod folders"""
        try:
            # Read existing content
            content = self.userchrome_manager.read_userchrome(profile)
            if not content:
                return False, "No userChrome.css file exists"

            # Check if import exists
            import_exists = self.userchrome_manager.has_import(content, import_path)
            if not import_exists:
                return False, f"Import not found: {import_path}"

            # Get mod name from import path
            # Import path is typically in the format: mod_name/file.css or mod_name/subfolder/file.css
            mod_name = import_path.split('/')[0] if '/' in import_path else import_path
            
            # Sanitize the mod name the same way it's done during import
            sanitized_mod_name = self.file_manager.sanitize_filename(mod_name)

            # Remove the import from userChrome.css
            updated_content = self.userchrome_manager.remove_import(content, import_path)

            # Write updated content
            self.userchrome_manager.write_userchrome(profile, updated_content)

            # Check if there are any remaining imports from the same mod
            remaining_imports = []
            for imp in self.userchrome_manager.get_imports(updated_content):
                imp_mod_name = imp.path.split('/')[0] if '/' in imp.path else imp.path
                if imp_mod_name == mod_name:
                    remaining_imports.append(imp.path)
            
            # Only delete the mod directory if there are no remaining imports from it
            if not remaining_imports:
                # Delete the mod folder in chrome directory
                mod_dir = os.path.join(profile.chrome_dir, sanitized_mod_name)
                
                if os.path.exists(mod_dir):
                    # First try using direct OS commands to delete the directory
                    try:
                        if platform.system() == "Windows":
                            # On Windows, use rd /s /q
                            cmd = ["cmd", "/c", "rd", "/s", "/q", os.path.normpath(mod_dir)]
                            subprocess.run(cmd, check=False)
                        else:
                            # On Unix-like systems, use rm -rf
                            cmd = ["rm", "-rf", mod_dir]
                            subprocess.run(cmd, check=False, capture_output=True, text=True)
                        
                        # Check if the deletion worked
                        if not os.path.exists(mod_dir):
                            pass  # Successfully removed
                        else:
                            # Try the Python methods as fallback
                            try:
                                shutil.rmtree(mod_dir, ignore_errors=True)
                                if not os.path.exists(mod_dir):
                                    pass  # Successfully removed
                            except Exception:
                                pass  # Already handled with ignore_errors=True
                    except Exception:
                        # Try the fallback method
                        try:
                            shutil.rmtree(mod_dir, ignore_errors=True)
                        except Exception:
                            pass  # Already handled with ignore_errors=True
                
                # Also remove the mod info from the mods.json file
                try:
                    # Use original mod_name (not sanitized) for mod_info lookup
                    self.mod_manager.remove_mod(mod_name)
                except Exception:
                    pass  # Continue even if mod info removal fails
                
                return True, f"Successfully removed import and associated files for: {import_path}"
            else:
                return True, f"Successfully removed import for: {import_path} (mod folder retained for remaining imports)"

        except Exception as e:
            return False, f"Failed to remove import: {str(e)}"

    def toggle_import(self, profile: Profile, import_path: str) -> Tuple[bool, str, bool]:
        """
        Toggle an import on or off

        Returns:
            Tuple of (success, message, is_enabled)
        """
        try:
            # Read existing content
            content = self.userchrome_manager.read_userchrome(profile)
            if not content:
                return False, "No userChrome.css file exists", False

            # Check if import exists
            if not self.userchrome_manager.has_import(content, import_path):
                return False, f"Import not found: {import_path}", False

            # Toggle the import
            updated_content = self.userchrome_manager.toggle_import(content, import_path)

            # Write updated content
            self.userchrome_manager.write_userchrome(profile, updated_content)

            # Determine if it's now enabled or disabled
            imports = self.userchrome_manager.get_imports(updated_content)
            for import_entry in imports:
                if self.userchrome_manager._normalize_import_path(import_entry.path) == \
                    self.userchrome_manager._normalize_import_path(import_path):
                    return True, f"Successfully toggled import", import_entry.enabled

            return True, f"Successfully toggled import", False

        except Exception as e:
            return False, f"Failed to toggle import: {str(e)}", False

    def get_imports(self, profile: Profile) -> List[ImportEntry]:
        """Get all imports from userChrome.css"""
        # Read existing content
        content = self.userchrome_manager.read_userchrome(profile)
        if not content:
            return []

        # Get all imports
        return self.userchrome_manager.get_imports(content)

    def select_css_files(self, css_files: List[str], extract_dir: str) -> List[str]:
        """
        Select which CSS files to import.
        This is a placeholder that should be overridden by the UI layer.
        """
        # Default implementation: if userChrome.css exists, only import that
        userchrome_files = [f for f in css_files if os.path.basename(f).lower() == 'userchrome.css']
        if userchrome_files:
            return userchrome_files

        # Otherwise, return all CSS files
        return css_files
