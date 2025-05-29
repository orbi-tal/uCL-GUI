import os
import json
import pycurl
import tempfile
from io import BytesIO
from typing import Optional, Dict, Tuple, List, Any
from urllib.parse import urlparse
from .models import ModInfo
from .exceptions import DownloadError, ValidationError

class DownloadManager:
    def __init__(self):
        self.curl = None
        self.setup_curl()

    def setup_curl(self):
        """Set up libcurl for downloads"""
        if self.curl:
            self.curl.close()
            
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.curl.setopt(pycurl.TIMEOUT, 300)
        self.curl.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.curl.setopt(pycurl.SSL_VERIFYPEER, 1)  # Verify SSL certificates
        self.curl.setopt(pycurl.SSL_VERIFYHOST, 2)  # Verify hostname

    def cleanup(self):
        """Clean up resources"""
        if self.curl:
            self.curl.close()
            self.curl = None

    def validate_url(self, url: str) -> bool:
        """Validate if a URL is properly formatted and supported"""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme in ['http', 'https'], parsed.netloc])
        except Exception:
            return False

    def download_file(self, url: str, destination: str) -> bool:
        """Download a file from URL to destination path"""
        if not self.validate_url(url):
            raise ValidationError(f"Invalid URL: {url}")

        try:
            # Reset curl options to ensure clean state
            self.setup_curl()
            
            # Set up download with progress tracking
            with open(destination, 'wb') as f:
                self.curl.setopt(pycurl.URL, url)
                self.curl.setopt(pycurl.WRITEDATA, f)
                self.curl.setopt(pycurl.FOLLOWLOCATION, 1)  # Follow redirects
                self.curl.setopt(pycurl.MAXREDIRS, 5)  # Maximum redirects
                self.curl.setopt(pycurl.CONNECTTIMEOUT, 30)  # 30 seconds connect timeout
                self.curl.setopt(pycurl.TIMEOUT, 300)  # 5 minutes total timeout
                self.curl.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                # Perform the request
                self.curl.perform()

                # Check HTTP status code
                status_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
                if status_code >= 400:
                    raise DownloadError(f"HTTP error: {status_code}")
                    
                # Check download size
                size = os.path.getsize(destination)
                
                if size == 0:
                    raise DownloadError(f"Downloaded file is empty: {destination}")

                return True
        except Exception as e:
            if os.path.exists(destination):
                os.remove(destination)
            raise DownloadError(f"Download failed: {str(e)}")

    def download_and_validate(self, url: str, validation_func=None) -> Tuple[str, Any]:
        """
        Download a file to a temporary location and validate it

        Args:
            url: The URL to download
            validation_func: Optional function to validate the downloaded content

        Returns:
            Tuple of (temp_file_path, validation_result)
        """
        if not self.validate_url(url):
            raise ValidationError(f"Invalid URL: {url}")

        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(prefix="userchrome_")
        os.close(temp_fd)

        try:
            self.download_file(url, temp_path)

            # Validate if needed
            validation_result = None
            if validation_func:
                validation_result = validation_func(temp_path)

            return temp_path, validation_result

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise DownloadError(f"Download and validation failed: {str(e)}")

    def handle_github_url(self, url: str) -> Tuple[str, ModInfo]:
        """
        Handle GitHub URL by determining if it's a file, directory, or repository

        Returns:
            Tuple of (temp_file_path, mod_info)
        """
        if not "github.com" in url:
            raise ValidationError("Not a GitHub URL")

        try:
            # Parse GitHub URL to identify its type
            parts = url.split("github.com/", 1)[1].split("/")

            if len(parts) < 2:
                raise ValidationError("Invalid GitHub URL format")

            owner = parts[0]
            repo = parts[1]

            # Identify if it's a raw URL
            if "raw.githubusercontent.com" in url:
                return self._handle_github_raw_file(url)

            # Check if it's a specific file or directory
            if len(parts) > 4 and parts[2] == "blob":
                branch = parts[3]
                path = "/".join(parts[4:])
                return self._handle_github_file(owner, repo, branch, path)

            # Check if it's a repository root
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            repo_info = self._fetch_github_api(api_url)

            default_branch = repo_info.get("default_branch", "main")
            return self._handle_github_repo(owner, repo, default_branch)

        except ValidationError:
            raise
        except Exception as e:
            raise DownloadError(f"Failed to process GitHub URL: {str(e)}")

    def _fetch_github_api(self, api_url: str) -> Dict:
        """Fetch data from GitHub API"""
        buffer = BytesIO()

        try:
            self.curl.setopt(pycurl.URL, api_url)
            self.curl.setopt(pycurl.WRITEDATA, buffer)
            self.curl.setopt(pycurl.HTTPHEADER, ["Accept: application/vnd.github.v3+json"])
            self.curl.perform()

            status_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
            if status_code >= 400:
                raise DownloadError(f"GitHub API error: {status_code}")

            return json.loads(buffer.getvalue().decode('utf-8'))

        except Exception as e:
            raise DownloadError(f"GitHub API request failed: {str(e)}")
        finally:
            buffer.close()

    def _handle_github_raw_file(self, url: str) -> Tuple[str, ModInfo]:
        """Handle a raw GitHub file URL"""
        # Extract file name from URL
        file_name = url.split("/")[-1]

        # Download file to temp location
        temp_fd, temp_path = tempfile.mkstemp(prefix="userchrome_")
        os.close(temp_fd)

        try:
            self.download_file(url, temp_path)

            # Create ModInfo
            mod_info = ModInfo(
                name=file_name,
                source_url=url,
                files=[file_name]
            )

            return temp_path, mod_info

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise DownloadError(f"Failed to download GitHub file: {str(e)}")

    def _handle_github_file(self, owner: str, repo: str,
                          branch: str, path: str) -> Tuple[str, ModInfo]:
        """Handle a GitHub file referenced by path"""
        # Convert to raw URL
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        return self._handle_github_raw_file(raw_url)

    def _handle_github_repo(self, owner: str, repo: str,
                          branch: str) -> Tuple[str, ModInfo]:
        """Handle a GitHub repository (download as zip)"""
        # Create zip download URL
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"

        # Download zip to temp location
        temp_fd, temp_path = tempfile.mkstemp(prefix="userchrome_", suffix=".zip")
        os.close(temp_fd)

        try:
            # First check if URL is accessible
            success = self.download_file(zip_url, temp_path)
            
            if not success:
                raise DownloadError(f"Failed to download from {zip_url}")
                
            # Verify the file was actually downloaded and has content
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise DownloadError(f"Downloaded file is empty or does not exist: {temp_path}")

            # Create ModInfo
            mod_info = ModInfo(
                name=repo,
                source_url=f"https://github.com/{owner}/{repo}",
                version=branch,
                metadata={
                    "type": "github",
                    "owner": owner,
                    "repo": repo,
                    "branch": branch
                }
            )

            return temp_path, mod_info

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise DownloadError(f"Failed to download GitHub repository: {str(e)}")

    def get_url_headers(self, url: str) -> Dict[str, str]:
        """
        Get HTTP headers from a URL without downloading the content
        
        Args:
            url: The URL to check
            
        Returns:
            Dictionary of HTTP headers
        """
        if not self.validate_url(url):
            raise ValidationError(f"Invalid URL: {url}")
            
        # Set up headers buffer
        header_buffer = BytesIO()
        
        try:
            # Configure curl to only get headers
            self.curl.setopt(pycurl.URL, url)
            self.curl.setopt(pycurl.NOBODY, 1)  # Don't download body
            self.curl.setopt(pycurl.HEADERFUNCTION, header_buffer.write)
            self.curl.perform()
            
            # Reset for future requests
            self.curl.setopt(pycurl.NOBODY, 0)
            
            # Get status code
            status_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
            if status_code >= 400:
                raise DownloadError(f"HTTP error: {status_code}")
                
            # Parse headers
            header_text = header_buffer.getvalue().decode('utf-8')
            headers = {}
            
            for line in header_text.splitlines():
                line = line.strip()
                if line and ':' in line:
                    name, value = line.split(':', 1)
                    headers[name.strip()] = value.strip()
                    
            return headers
            
        except Exception as e:
            raise DownloadError(f"Failed to get headers: {str(e)}")
        finally:
            header_buffer.close()
    
    def _check_github_updates(self, mod_info: ModInfo) -> Tuple[bool, Optional[str]]:
        """Check if a GitHub-sourced mod has updates available"""
        metadata = mod_info.metadata

        if not metadata or metadata.get("type") != "github":
            return False, "Not a GitHub mod"

        owner = metadata.get("owner")
        repo = metadata.get("repo")
        current_branch = metadata.get("branch")

        if not all([owner, repo, current_branch]):
            return False, "Incomplete GitHub metadata"

        try:
            # Check commits to see if there are new ones
            api_url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={current_branch}&per_page=1"
            commits = self._fetch_github_api(api_url)

            if not commits or not isinstance(commits, list) or len(commits) == 0:
                return False, "Failed to fetch commit information"

            latest_commit_sha = commits[0].get("sha")

            # If we have the latest commit stored, compare
            if "latest_commit" in metadata:
                if metadata["latest_commit"] == latest_commit_sha:
                    return False, "Already up to date"

            # There's an update
            return True, latest_commit_sha

        except Exception as e:
            return False, f"Update check failed: {str(e)}"
