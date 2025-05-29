import json
import pycurl
import traceback
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from src.core.exceptions import DownloadError

class GitHubApi:
    """Interface for GitHub API operations"""

    def __init__(self):
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.curl.setopt(pycurl.TIMEOUT, 300)
        self.curl.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.curl.setopt(pycurl.HTTPHEADER, ["Accept: application/vnd.github.v3+json"])

    def __del__(self):
        if self.curl:
            self.curl.close()

    def fetch_api(self, api_url: str) -> Dict[str, Any]:
        """Fetch data from GitHub API"""
        buffer = BytesIO()

        try:
            print(f"DEBUG: GitHub API request to {api_url}")
            self.curl.setopt(pycurl.URL, api_url)
            self.curl.setopt(pycurl.WRITEDATA, buffer)
            self.curl.perform()

            status_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
            print(f"DEBUG: GitHub API response status: {status_code}")
            
            if status_code >= 400:
                response_data = buffer.getvalue().decode('utf-8')
                print(f"DEBUG: GitHub API error response: {response_data}")
                raise DownloadError(f"GitHub API error: {status_code}, Response: {response_data[:200]}")

            response_data = buffer.getvalue().decode('utf-8')
            result = json.loads(response_data)
            print(f"DEBUG: GitHub API response length: {len(response_data)} bytes")
            
            return result

        except Exception as e:
            print(f"ERROR: GitHub API request failed: {str(e)}")
            print(f"ERROR: {traceback.format_exc()}")
            raise DownloadError(f"GitHub API request failed: {str(e)}")
        finally:
            buffer.close()

    def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information"""
        print(f"DEBUG: Getting repository info for {owner}/{repo}")
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        result = self.fetch_api(api_url)
        print(f"DEBUG: Repo info retrieved, default branch: {result.get('default_branch', 'unknown')}")
        return result

    def get_latest_commit(self, owner: str, repo: str,
                        branch: str = "main") -> Dict[str, Any]:
        """Get the latest commit in a branch"""
        print(f"DEBUG: Getting latest commit for {owner}/{repo} branch {branch}")
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
        result = self.fetch_api(api_url)
        print(f"DEBUG: Latest commit: {result.get('sha', 'unknown')[:10]}")
        return result

    def get_file_content(self, owner: str, repo: str, path: str,
                       branch: str = "main") -> Tuple[str, Dict[str, Any]]:
        """
        Get the content of a file

        Returns:
            Tuple of (content, file_info)
        """
        print(f"DEBUG: Getting file content for {owner}/{repo}/{path} (branch: {branch})")
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        file_info = self.fetch_api(api_url)

        # Check if it's a file
        if file_info.get("type") != "file":
            print(f"ERROR: Not a file: {path}, type: {file_info.get('type')}")
            raise DownloadError(f"Not a file: {path}")

        # Get the content
        download_url = file_info.get("download_url")
        if not download_url:
            print(f"ERROR: No download URL for file: {path}")
            raise DownloadError(f"No download URL for file: {path}")

        print(f"DEBUG: Downloading file from {download_url}")
        # Download the file content
        buffer = BytesIO()
        try:
            self.curl.setopt(pycurl.URL, download_url)
            self.curl.setopt(pycurl.WRITEDATA, buffer)
            self.curl.perform()

            status_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
            print(f"DEBUG: File download status: {status_code}")
            
            if status_code >= 400:
                raise DownloadError(f"GitHub download error: {status_code}")

            content = buffer.getvalue().decode('utf-8')
            print(f"DEBUG: Downloaded {len(content)} bytes of content")
            return content, file_info

        except Exception as e:
            print(f"ERROR: GitHub file download failed: {str(e)}")
            print(f"ERROR: {traceback.format_exc()}")
            raise DownloadError(f"GitHub file download failed: {str(e)}")
        finally:
            buffer.close()

    def get_directory_contents(self, owner: str, repo: str,
                             path: str, branch: str = "main") -> List[Dict[str, Any]]:
        """Get the contents of a directory"""
        if path.startswith('/'):
            path = path[1:]  # Remove leading slash

        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        contents = self.fetch_api(api_url)

        # Check if it's a list (directory) or a single item (file)
        if not isinstance(contents, list):
            raise DownloadError(f"Not a directory: {path}")

        return contents

    def get_download_url(self, owner: str, repo: str,
                       branch: str = "main") -> str:
        """Get URL for downloading a repository as a ZIP file"""
        url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        print(f"DEBUG: GitHub repo download URL: {url}")
        return url
        
    def compare_commits(self, owner: str, repo: str, 
                      base: str, head: str) -> Dict[str, Any]:
        """
        Compare two commits and get the diff
        
        Args:
            owner: Repository owner
            repo: Repository name
            base: Base commit SHA
            head: Head commit SHA
            
        Returns:
            Dictionary with comparison information
        """
        api_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}"
        return self.fetch_api(api_url)
