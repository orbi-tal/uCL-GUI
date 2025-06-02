from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import os
import tempfile
import zipfile
import shutil
from src.core.models import ModInfo
from src.core.download import DownloadManager
from src.core.mod import ModManager
from src.infrastructure.github_api import GitHubApi
from src.infrastructure.gitlab_api import GitLabApi

class UpdateService:
    """Service for checking and applying updates to installed mods"""

    def __init__(self, download_manager: DownloadManager,
                mod_manager: ModManager,
                github_api: GitHubApi,
                gitlab_api: GitLabApi):
        self.download_manager = download_manager
        self.mod_manager = mod_manager
        self.github_api = github_api
        self.gitlab_api = gitlab_api

    def check_for_updates(self) -> Dict[str, Dict[str, Any]]:
        """
        Check for updates to all installed mods with detailed diff information

        Returns:
            Dictionary of mod names to update info dictionaries containing:
            - 'has_update': bool
            - 'message': str
            - 'commit_info': dict with commit details
            - 'diff_info': list of changed files or HTML diff
            - 'source_type': str indicating the source (github, gitlab, etc.)
            - 'commit_url': URL to view the commit (if available)
        """
        results = {}

        # Get all mods
        mods = self.mod_manager.get_all_mods()

        for mod in mods:
            # Skip mods without a source URL
            if not mod.source_url:
                results[mod.name] = {
                    'has_update': False,
                    'message': "No source URL",
                    'source_type': "unknown"
                }
                continue

            # Check based on source type
            if "github.com" in mod.source_url:
                update_info = self._check_github_update(mod)
                update_info['source_type'] = "github"
            elif "gitlab.com" in mod.source_url:
                update_info = self._check_gitlab_update(mod)
                update_info['source_type'] = "gitlab"
            else:
                update_info = self._check_direct_update(mod)
                update_info['source_type'] = "direct"

            results[mod.name] = update_info

        return results

    def _check_github_update(self, mod: ModInfo) -> Dict[str, Any]:
        """
        Check for updates to a GitHub-sourced mod with detailed diff information
        Focus on CSS file changes only for meaningful updates
        
        Returns:
            Dictionary with update information
        """
        result = {
            'has_update': False,
            'message': "",
            'commit_info': {},
            'diff_info': [],
            'commit_url': ""
        }
        
        # Check if we have GitHub metadata
        metadata = mod.metadata or {}

        if metadata.get("type") != "github":
            # Try to parse from URL
            try:
                parts = mod.source_url.split("github.com/", 1)[1].split("/")
                if len(parts) < 2:
                    result['message'] = "Invalid GitHub URL format"
                    return result

                owner = parts[0]
                repo = parts[1]
                branch = "main"  # Default to main if not specified

                # If we have more parts, look for branch
                if len(parts) > 3 and parts[2] in ["blob", "tree"]:
                    branch = parts[3]

            except Exception:
                result['message'] = "Failed to parse GitHub URL"
                return result
        else:
            # Use metadata
            owner = metadata.get("owner")
            repo = metadata.get("repo")
            branch = metadata.get("branch", "main")

            if not all([owner, repo]):
                result['message'] = "Incomplete GitHub metadata"
                return result

        try:
            # Get latest commit
            latest_commit = self.github_api.get_latest_commit(owner, repo, branch)
            latest_commit_sha = latest_commit.get("sha", "")
            
            # If no new commit, return early
            if "latest_commit" in metadata and metadata["latest_commit"] == latest_commit_sha:
                result['message'] = f"Already up to date (v{latest_commit_sha[:8]})"
                return result
            
            # Check if we have a previous commit to compare
            if "latest_commit" not in metadata:
                # First time checking - consider it an update
                result['has_update'] = True
                result['message'] = f"Version {latest_commit_sha[:8]} available"
                
                # Format commit info
                commit_info = {}
                commit_info['sha'] = latest_commit_sha
                commit_info['message'] = latest_commit.get("commit", {}).get("message", "No commit message")
                
                author_info = latest_commit.get("commit", {}).get("author", {})
                commit_info['author'] = author_info.get("name", "Unknown")
                
                # Format date
                date_str = author_info.get("date", "")
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        commit_info['date'] = date_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        commit_info['date'] = date_str
                else:
                    commit_info['date'] = "Unknown date"
                
                result['commit_info'] = commit_info
                result['commit_url'] = f"https://github.com/{owner}/{repo}/commit/{latest_commit_sha}"
                result['diff_info'] = ["Initial version - no previous version to compare"]
                
                return result
            
            # We have a previous commit - check for CSS file changes
            previous_commit = metadata["latest_commit"]
            try:
                # Get list of changed files
                comparison = self.github_api.compare_commits(owner, repo, previous_commit, latest_commit_sha)
                
                # Filter for CSS files only
                css_files_changed = []
                all_files_changed = []
                
                for file_info in comparison.get("files", []):
                    filename = file_info.get("filename", "")
                    file_data = {
                        "filename": filename,
                        "status": file_info.get("status", ""),
                        "additions": file_info.get("additions", 0),
                        "deletions": file_info.get("deletions", 0)
                    }
                    
                    all_files_changed.append(file_data)
                    
                    # Check if it's a CSS file
                    if filename.lower().endswith('.css'):
                        css_files_changed.append(file_data)
                
                # Only show update if CSS files have changed
                if css_files_changed:
                    result['has_update'] = True
                    result['message'] = f"CSS changes in v{latest_commit_sha[:8]} ({len(css_files_changed)} CSS files modified)"
                    result['diff_info'] = css_files_changed
                else:
                    # No CSS changes, but show what did change
                    result['has_update'] = False
                    if all_files_changed:
                        non_css_files = [f['filename'] for f in all_files_changed if not f['filename'].lower().endswith('.css')]
                        result['message'] = f"No CSS changes (only {', '.join(non_css_files[:3])}{'...' if len(non_css_files) > 3 else ''})"
                    else:
                        result['message'] = "No meaningful changes detected"
                    result['diff_info'] = all_files_changed
                
                # Format commit info regardless
                commit_info = {}
                commit_info['sha'] = latest_commit_sha
                commit_info['message'] = latest_commit.get("commit", {}).get("message", "No commit message")
                
                author_info = latest_commit.get("commit", {}).get("author", {})
                commit_info['author'] = author_info.get("name", "Unknown")
                
                # Format date
                date_str = author_info.get("date", "")
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        commit_info['date'] = date_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        commit_info['date'] = date_str
                else:
                    commit_info['date'] = "Unknown date"
                
                result['commit_info'] = commit_info
                result['commit_url'] = f"https://github.com/{owner}/{repo}/commit/{latest_commit_sha}"
                
            except Exception as e:
                # If we can't get detailed diff, assume there might be changes
                result['has_update'] = True
                result['message'] = f"Version {latest_commit_sha[:8]} available (could not check file changes)"
                result['diff_info'] = ["Could not retrieve detailed file changes"]
                
                # Still populate commit info
                commit_info = {}
                commit_info['sha'] = latest_commit_sha
                commit_info['message'] = latest_commit.get("commit", {}).get("message", "No commit message")
                
                author_info = latest_commit.get("commit", {}).get("author", {})
                commit_info['author'] = author_info.get("name", "Unknown")
                
                # Format date
                date_str = author_info.get("date", "")
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        commit_info['date'] = date_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        commit_info['date'] = date_str
                else:
                    commit_info['date'] = "Unknown date"
                
                result['commit_info'] = commit_info
                result['commit_url'] = f"https://github.com/{owner}/{repo}/commit/{latest_commit_sha}"
            
            return result

        except Exception as e:
            result['message'] = f"Update check failed: {str(e)}"
            return result

    def _check_gitlab_update(self, mod: ModInfo) -> Dict[str, Any]:
        """
        Check for updates to a GitLab-sourced mod with detailed diff information
        Focus on CSS file changes only for meaningful updates
        
        Returns:
            Dictionary with update information
        """
        result = {
            'has_update': False,
            'message': "",
            'commit_info': {},
            'diff_info': [],
            'commit_url': ""
        }
        
        # Check if we have GitLab metadata
        metadata = mod.metadata or {}
        project_id = None
        project_path = None
        
        if metadata.get("type") != "gitlab":
            # Try to parse from URL
            try:
                gitlab_info = self.gitlab_api.parse_gitlab_url(mod.source_url)
                project_path = gitlab_info['project_path']
                branch = gitlab_info['branch']

                # Get project info
                project_info = self.gitlab_api.get_project_info(project_path)
                project_id = project_info['id']

            except Exception as e:
                result['message'] = f"Failed to parse GitLab URL: {str(e)}"
                return result
        else:
            # Use metadata
            project_id = metadata.get("project_id")
            project_path = metadata.get("project_path")
            branch = metadata.get("branch", "main")

            if not project_id:
                result['message'] = "Incomplete GitLab metadata"
                return result

        try:
            # Get latest commit
            latest_commit = self.gitlab_api.get_latest_commit(project_id, branch)
            latest_commit_sha = latest_commit.get("id", "")
            
            # If no new commit, return early
            if "latest_commit" in metadata and metadata["latest_commit"] == latest_commit_sha:
                result['message'] = f"Already up to date (v{latest_commit_sha[:8]})"
                return result
            
            # Check if we have a previous commit to compare
            if "latest_commit" not in metadata:
                # First time checking - consider it an update
                result['has_update'] = True
                result['message'] = f"Version {latest_commit_sha[:8]} available"
                
                # Format commit info
                commit_info = {}
                commit_info['sha'] = latest_commit_sha
                commit_info['message'] = latest_commit.get("message", "No commit message")
                commit_info['author'] = latest_commit.get("author_name", "Unknown")
                
                # Format date
                date_str = latest_commit.get("created_at", "")
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        commit_info['date'] = date_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        commit_info['date'] = date_str
                else:
                    commit_info['date'] = "Unknown date"
                
                result['commit_info'] = commit_info
                
                # Add commit URL - construct GitLab web URL
                if project_path:
                    result['commit_url'] = f"https://gitlab.com/{project_path}/-/commit/{latest_commit_sha}"
                
                result['diff_info'] = ["Initial version - no previous version to compare"]
                return result
            
            # We have a previous commit - check for CSS file changes
            previous_commit = metadata["latest_commit"]
            try:
                # Get list of changed files using GitLab API
                comparison = self.gitlab_api.compare_commits(project_id, previous_commit, latest_commit_sha)
                
                # Filter for CSS files only
                css_files_changed = []
                all_files_changed = []
                
                for file_info in comparison.get("diffs", []):
                    old_path = file_info.get("old_path", "")
                    new_path = file_info.get("new_path", "")
                    
                    # Determine status
                    if old_path == "/dev/null":
                        status = "added"
                        filename = new_path
                    elif new_path == "/dev/null":
                        status = "removed"
                        filename = old_path
                    elif old_path != new_path:
                        status = "renamed"
                        filename = f"{old_path} → {new_path}"
                    else:
                        status = "modified"
                        filename = new_path
                    
                    file_data = {
                        "filename": filename,
                        "status": status
                    }
                    
                    all_files_changed.append(file_data)
                    
                    # Check if it's a CSS file
                    if filename.lower().endswith('.css') or (new_path and new_path.lower().endswith('.css')):
                        css_files_changed.append(file_data)
                
                # Only show update if CSS files have changed
                if css_files_changed:
                    result['has_update'] = True
                    result['message'] = f"CSS changes in v{latest_commit_sha[:8]} ({len(css_files_changed)} CSS files modified)"
                    result['diff_info'] = css_files_changed
                else:
                    # No CSS changes, but show what did change
                    result['has_update'] = False
                    if all_files_changed:
                        non_css_files = [f['filename'] for f in all_files_changed if not f['filename'].lower().endswith('.css')]
                        result['message'] = f"No CSS changes (only {', '.join(non_css_files[:3])}{'...' if len(non_css_files) > 3 else ''})"
                    else:
                        result['message'] = "No meaningful changes detected"
                    result['diff_info'] = all_files_changed
                
                # Format commit info regardless
                commit_info = {}
                commit_info['sha'] = latest_commit_sha
                commit_info['message'] = latest_commit.get("message", "No commit message")
                commit_info['author'] = latest_commit.get("author_name", "Unknown")
                
                # Format date
                date_str = latest_commit.get("created_at", "")
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        commit_info['date'] = date_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        commit_info['date'] = date_str
                else:
                    commit_info['date'] = "Unknown date"
                
                result['commit_info'] = commit_info
                
                # Add commit URL - construct GitLab web URL
                if project_path:
                    result['commit_url'] = f"https://gitlab.com/{project_path}/-/commit/{latest_commit_sha}"
                
            except Exception as e:
                # If we can't get detailed diff, assume there might be changes
                result['has_update'] = True
                result['message'] = f"Version {latest_commit_sha[:8]} available (could not check file changes)"
                result['diff_info'] = ["Could not retrieve detailed file changes"]
                
                # Still populate commit info
                commit_info = {}
                commit_info['sha'] = latest_commit_sha
                commit_info['message'] = latest_commit.get("message", "No commit message")
                commit_info['author'] = latest_commit.get("author_name", "Unknown")
                
                # Format date
                date_str = latest_commit.get("created_at", "")
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        commit_info['date'] = date_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        commit_info['date'] = date_str
                else:
                    commit_info['date'] = "Unknown date"
                
                result['commit_info'] = commit_info
                
                # Add commit URL - construct GitLab web URL
                if project_path:
                    result['commit_url'] = f"https://gitlab.com/{project_path}/-/commit/{latest_commit_sha}"
            
            return result

        except Exception as e:
            result['message'] = f"Update check failed: {str(e)}"
            return result

    def _check_direct_update(self, mod: ModInfo) -> Dict[str, Any]:
        """Check for updates to a direct URL mod"""
        # For direct URLs, we can use the HTTP headers to check for changes
        result = {
            'has_update': False,
            'message': "Update checking not fully supported for direct URLs",
            'commit_info': {},
            'diff_info': [],
            'commit_url': ""
        }
        
        # Check if we have ETag or Last-Modified stored
        metadata = mod.metadata or {}
        etag = metadata.get("etag")
        last_modified = metadata.get("last_modified")
        
        if not (etag or last_modified):
            result['message'] = "No previous version information available"
            return result
            
        try:
            # Use the download manager to check headers
            headers = self.download_manager.get_url_headers(mod.source_url)
            
            new_etag = headers.get("ETag")
            new_last_modified = headers.get("Last-Modified")
            
            # Compare etags if available
            if etag and new_etag and etag != new_etag:
                result['has_update'] = True
                result['message'] = "New version available (ETag changed)"
                
                # Basic commit info for display
                result['commit_info'] = {
                    'message': "Content updated",
                    'author': "Unknown",
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'sha': new_etag
                }
                
                result['diff_info'] = ["Content has changed, but detailed diff information is not available for direct URLs"]
                result['commit_url'] = mod.source_url
                
            # Compare last-modified if available
            elif last_modified and new_last_modified and last_modified != new_last_modified:
                result['has_update'] = True
                result['message'] = "New version available (Last-Modified changed)"
                
                # Basic commit info for display
                result['commit_info'] = {
                    'message': "Content updated",
                    'author': "Unknown",
                    'date': new_last_modified,
                    'sha': ""
                }
                
                result['diff_info'] = ["Content has changed, but detailed diff information is not available for direct URLs"]
                result['commit_url'] = mod.source_url
            else:
                result['message'] = "Already up to date"
                
            return result
            
        except Exception as e:
            result['message'] = f"Update check failed: {str(e)}"
            return result

    def apply_update(self, mod_name: str) -> Tuple[bool, str]:
        """
        Apply an update to a mod

        Returns:
            Tuple of (success, message)
        """
        # Get mod info
        mod = self.mod_manager.get_mod_info(mod_name)
        if not mod:
            return False, f"Mod not found: {mod_name}"

        # Check if mod has a source URL
        if not mod.source_url:
            return False, "No source URL for this mod"

        # Re-download from source
        try:
            # First check for updates to confirm there's something to update
            if "github.com" in mod.source_url:
                update_info = self._check_github_update(mod)
                if not update_info.get('has_update', False):
                    return False, "Already up to date"
                return self._apply_github_update(mod)
            elif "gitlab.com" in mod.source_url:
                update_info = self._check_gitlab_update(mod)
                if not update_info.get('has_update', False):
                    return False, "Already up to date"
                return self._apply_gitlab_update(mod)
            else:
                update_info = self._check_direct_update(mod)
                if not update_info.get('has_update', False):
                    return False, "Already up to date"
                return self._apply_direct_update(mod)

        except Exception as e:
            return False, f"Update failed: {str(e)}"

    def _apply_github_update(self, mod: ModInfo) -> Tuple[bool, str]:
        """Apply update to a GitHub-sourced mod"""
        metadata = mod.metadata or {}
        
        # Extract GitHub repository information
        if metadata.get("type") != "github":
            # Try to parse from URL
            try:
                parts = mod.source_url.split("github.com/", 1)[1].split("/")
                if len(parts) < 2:
                    return False, "Invalid GitHub URL format"

                owner = parts[0]
                repo = parts[1]
                branch = "main"  # Default to main if not specified

                # If we have more parts, look for branch
                if len(parts) > 3 and parts[2] in ["blob", "tree"]:
                    branch = parts[3]
            except Exception:
                return False, "Failed to parse GitHub URL"
        else:
            # Use metadata
            owner = metadata.get("owner")
            repo = metadata.get("repo")
            branch = metadata.get("branch", "main")

            if not all([owner, repo]):
                return False, "Incomplete GitHub metadata"
        
        try:
            # Get latest commit to update metadata
            latest_commit = self.github_api.get_latest_commit(owner, repo, branch)
            latest_commit_sha = latest_commit.get("sha", "")
            
            # Create download URL
            download_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
            
            # Use download manager to get the repository
            temp_file = tempfile.mktemp(suffix=".zip")
            
            # Download the zip file
            self.download_manager.download_file(download_url, temp_file)
            
            # Extract the zip to a temporary directory
            temp_dir = tempfile.mkdtemp(prefix="userchrome_update_")
            
            # Extract archive
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the extracted directory (usually repo-branch)
            extracted_dirs = [d for d in os.listdir(temp_dir) 
                            if os.path.isdir(os.path.join(temp_dir, d))]
            
            if not extracted_dirs:
                return False, "No files found in downloaded archive"
            
            extracted_dir = os.path.join(temp_dir, extracted_dirs[0])
            
            # Copy files to replace existing mod
            for file_path in mod.files:
                # Get the destination directory
                dest_dir = os.path.dirname(file_path)
                
                # Get source files
                if os.path.exists(extracted_dir):
                    # Look for CSS files in the extracted directory
                    css_files = []
                    for root, _, files in os.walk(extracted_dir):
                        for file in files:
                            if file.lower().endswith('.css'):
                                css_files.append(os.path.join(root, file))
                    
                    if css_files:
                        for css_file in css_files:
                            rel_path = os.path.relpath(css_file, extracted_dir)
                            dest_path = os.path.join(dest_dir, rel_path)
                            
                            # Create directory if it doesn't exist
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            
                            # Copy the file
                            shutil.copy2(css_file, dest_path)
            
            # Update mod info with new commit info
            metadata["latest_commit"] = latest_commit_sha
            metadata["last_updated"] = datetime.now().isoformat()
            
            # If it wasn't a GitHub mod before, update metadata
            if metadata.get("type") != "github":
                metadata["type"] = "github"
                metadata["owner"] = owner
                metadata["repo"] = repo
                metadata["branch"] = branch
            
            mod.metadata = metadata
            self.mod_manager.save_mod_info(mod)
            
            # Clean up temporary files
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            return True, f"Updated {mod.name} to latest version"
            
        except Exception as e:
            return False, f"GitHub update failed: {str(e)}"

    def _apply_gitlab_update(self, mod: ModInfo) -> Tuple[bool, str]:
        """Apply update to a GitLab-sourced mod"""
        
        metadata = mod.metadata or {}
        project_id = None
        project_path = None
        branch = "main"
        
        # Extract GitLab repository information
        if metadata.get("type") != "gitlab":
            # Try to parse from URL
            try:
                gitlab_info = self.gitlab_api.parse_gitlab_url(mod.source_url)
                project_path = gitlab_info['project_path']
                branch = gitlab_info['branch']

                # Get project info
                project_info = self.gitlab_api.get_project_info(project_path)
                project_id = project_info['id']

            except Exception as e:
                return False, f"Failed to parse GitLab URL: {str(e)}"
        else:
            # Use metadata
            project_id = metadata.get("project_id")
            project_path = metadata.get("project_path")
            branch = metadata.get("branch", "main")

            if not project_id:
                return False, "Incomplete GitLab metadata"
        
        try:
            # Get latest commit to update metadata
            latest_commit = self.gitlab_api.get_latest_commit(project_id, branch)
            latest_commit_sha = latest_commit.get("id", "")
            
            # Create download URL
            download_url = self.gitlab_api.get_download_url(project_id, branch)
            
            # Use download manager to get the repository
            temp_file = tempfile.mktemp(suffix=".zip")
            
            # Download the zip file
            self.download_manager.download_file(download_url, temp_file)
            
            # Extract the zip to a temporary directory
            temp_dir = tempfile.mkdtemp(prefix="userchrome_update_")
            
            # Extract archive
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the extracted directory
            extracted_dirs = [d for d in os.listdir(temp_dir) 
                            if os.path.isdir(os.path.join(temp_dir, d))]
            
            if not extracted_dirs:
                return False, "No files found in downloaded archive"
            
            extracted_dir = os.path.join(temp_dir, extracted_dirs[0])
            
            # Copy files to replace existing mod
            for file_path in mod.files:
                # Get the destination directory
                dest_dir = os.path.dirname(file_path)
                
                # Get source files
                if os.path.exists(extracted_dir):
                    # Look for CSS files in the extracted directory
                    css_files = []
                    for root, _, files in os.walk(extracted_dir):
                        for file in files:
                            if file.lower().endswith('.css'):
                                css_files.append(os.path.join(root, file))
                    
                    if css_files:
                        for css_file in css_files:
                            rel_path = os.path.relpath(css_file, extracted_dir)
                            dest_path = os.path.join(dest_dir, rel_path)
                            
                            # Create directory if it doesn't exist
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            
                            # Copy the file
                            shutil.copy2(css_file, dest_path)
            
            # Update mod info with new commit info
            metadata["latest_commit"] = latest_commit_sha
            metadata["last_updated"] = datetime.now().isoformat()
            
            # If it wasn't a GitLab mod before, update metadata
            if metadata.get("type") != "gitlab":
                metadata["type"] = "gitlab"
                metadata["project_id"] = project_id
                metadata["project_path"] = project_path
                metadata["branch"] = branch
            
            mod.metadata = metadata
            self.mod_manager.save_mod_info(mod)
            
            # Clean up temporary files
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            return True, f"Updated {mod.name} to latest version"
            
        except Exception as e:
            return False, f"GitLab update failed: {str(e)}"

    def _apply_direct_update(self, mod: ModInfo) -> Tuple[bool, str]:
        """Apply update to a direct URL mod"""
        
        if not mod.source_url:
            return False, "No source URL"
            
        try:
            # Download the file to a temporary location
            temp_file = tempfile.mktemp(suffix=os.path.splitext(mod.source_url)[1])
            
            # Download the file
            self.download_manager.download_file(mod.source_url, temp_file)
            
            # Get headers to store ETag and Last-Modified
            headers = self.download_manager.get_url_headers(mod.source_url)
            etag = headers.get("ETag", "")
            last_modified = headers.get("Last-Modified", "")
            
            # Update all mod files with the new content
            for file_path in mod.files:
                # If it's a CSS file, copy it directly
                if os.path.splitext(temp_file)[1].lower() == '.css':
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(temp_file, file_path)
            
            # Update mod metadata
            metadata = mod.metadata or {}
            metadata["etag"] = etag
            metadata["last_modified"] = last_modified
            metadata["last_updated"] = datetime.now().isoformat()
            
            mod.metadata = metadata
            self.mod_manager.save_mod_info(mod)
            
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            return True, f"Updated {mod.name} to latest version"
            
        except Exception as e:
            return False, f"Direct URL update failed: {str(e)}"
