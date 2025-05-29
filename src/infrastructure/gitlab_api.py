import json
import pycurl
import urllib.parse
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from src.core.exceptions import DownloadError

class GitLabApi:
    """Interface for GitLab API operations"""

    def __init__(self, instance: str = "https://gitlab.com"):
        self.instance = instance.rstrip('/')
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.curl.setopt(pycurl.TIMEOUT, 300)
        self.curl.setopt(pycurl.USERAGENT, "UserChrome-Loader/1.0")

    def __del__(self):
        if self.curl:
            self.curl.close()

    def fetch_api(self, api_url: str) -> Dict[str, Any]:
        """Fetch data from GitLab API"""
        buffer = BytesIO()

        try:
            self.curl.setopt(pycurl.URL, api_url)
            self.curl.setopt(pycurl.WRITEDATA, buffer)
            self.curl.perform()

            status_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
            if status_code >= 400:
                raise DownloadError(f"GitLab API error: {status_code}")

            return json.loads(buffer.getvalue().decode('utf-8'))

        except Exception as e:
            raise DownloadError(f"GitLab API request failed: {str(e)}")
        finally:
            buffer.close()

    def get_project_info(self, project_path: str) -> Dict[str, Any]:
        """
        Get project information

        Args:
            project_path: Path to the project (group/project)
        """
        encoded_path = urllib.parse.quote_plus(project_path)
        api_url = f"{self.instance}/api/v4/projects/{encoded_path}"
        return self.fetch_api(api_url)

    def get_latest_commit(self, project_id: int,
                         branch: str = "main") -> Dict[str, Any]:
        """Get the latest commit in a branch"""
        api_url = f"{self.instance}/api/v4/projects/{project_id}/repository/commits/{branch}"
        return self.fetch_api(api_url)

    def get_file_content(self, project_id: int, file_path: str,
                        ref: str = "main") -> Tuple[str, Dict[str, Any]]:
        """
        Get the content of a file

        Returns:
            Tuple of (content, file_info)
        """
        encoded_path = urllib.parse.quote_plus(file_path)
        api_url = f"{self.instance}/api/v4/projects/{project_id}/repository/files/{encoded_path}?ref={ref}"
        file_info = self.fetch_api(api_url)

        # Check if file info contains content
        if "content" not in file_info:
            raise DownloadError(f"No content for file: {file_path}")

        # Get the content (base64 encoded)
        import base64
        try:
            content = base64.b64decode(file_info["content"]).decode('utf-8')
            return content, file_info
        except Exception as e:
            raise DownloadError(f"Failed to decode file content: {str(e)}")

    def get_repository_tree(self, project_id: int, path: str = "",
                          ref: str = "main") -> List[Dict[str, Any]]:
        """Get the contents of a directory"""
        api_url = f"{self.instance}/api/v4/projects/{project_id}/repository/tree?path={path}&ref={ref}"
        return self.fetch_api(api_url)

    def get_download_url(self, project_id: int,
                        ref: str = "main") -> str:
        """Get URL for downloading a repository as a ZIP file"""
        return f"{self.instance}/api/v4/projects/{project_id}/repository/archive.zip?ref={ref}"
        
    def compare_commits(self, project_id: int, from_sha: str, to_sha: str) -> Dict[str, Any]:
        """
        Compare two commits and get the diff
        
        Args:
            project_id: GitLab project ID
            from_sha: Base commit SHA
            to_sha: Head commit SHA
            
        Returns:
            Dictionary with comparison information including diffs
        """
        api_url = f"{self.instance}/api/v4/projects/{project_id}/repository/compare?from={from_sha}&to={to_sha}"
        return self.fetch_api(api_url)

    def parse_gitlab_url(self, url: str) -> Dict[str, Any]:
        """
        Parse a GitLab URL to extract project information

        Returns:
            Dictionary with project path, instance URL, and other info
        """
        # Check if it's a GitLab URL
        if "gitlab" not in url:
            raise DownloadError("Not a GitLab URL")

        try:
            parsed = urllib.parse.urlparse(url)

            # Determine GitLab instance
            instance = f"{parsed.scheme}://{parsed.netloc}"

            # Split path components
            path_parts = [p for p in parsed.path.split('/') if p]

            if len(path_parts) < 2:
                raise DownloadError("Invalid GitLab URL format")

            # Extract project path (namespace/project)
            if path_parts[0] == '-':
                # Handle URLs with a dash prefix for personal namespaces
                if len(path_parts) < 2:
                    raise DownloadError("Invalid GitLab URL format")
                project_path = '/'.join(path_parts[1:3])
            else:
                project_path = '/'.join(path_parts[0:2])

            # Get file path if available
            file_path = None
            branch = "main"

            if len(path_parts) > 2:
                if path_parts[2] == 'blob' or path_parts[2] == 'tree':
                    if len(path_parts) > 3:
                        branch = path_parts[3]

                    if len(path_parts) > 4 and path_parts[2] == 'blob':
                        file_path = '/'.join(path_parts[4:])

            return {
                'instance': instance,
                'project_path': project_path,
                'branch': branch,
                'file_path': file_path
            }

        except Exception as e:
            raise DownloadError(f"Failed to parse GitLab URL: {str(e)}")
