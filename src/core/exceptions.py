class UserChromeLoaderError(Exception):
    """Base exception for UserChrome Loader"""
    pass

class ValidationError(UserChromeLoaderError):
    """Error for validation failures"""
    pass

class DownloadError(UserChromeLoaderError):
    """Error for download failures"""
    pass

class FileOperationError(UserChromeLoaderError):
    """Error for file operation failures"""
    pass

class ProfileError(UserChromeLoaderError):
    """Error for profile-related issues"""
    pass

class ImportError(UserChromeLoaderError):
    """Error for import-related issues"""
    pass

class CircularImportError(ImportError):
    """Error for circular import detection"""
    pass

class ArchiveError(UserChromeLoaderError):
    """Error for archive extraction failures"""
    pass
