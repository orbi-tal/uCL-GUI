# src/launcher.py
import sys
import os
import traceback
from typing import cast, Optional, Dict, Any, Union

# Add the project's parent directory to Python's path
project_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_parent)

# Robust import helper
def safe_import(module_name, class_name=None, fallback=None):
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        return getattr(module, class_name) if class_name else module
    except ImportError as e:
        print(f"Error importing {module_name}.{class_name if class_name else ''}: {e}")
        traceback.print_exc()
        return fallback
    except Exception as e:
        print(f"Unexpected error importing {module_name}.{class_name if class_name else ''}: {e}")
        traceback.print_exc()
        return fallback

# Import Qt core components
QApplication = safe_import('PyQt6.QtWidgets', 'QApplication')
QDir = safe_import('PyQt6.QtCore', 'QDir')

# Import core classes
DownloadManager = safe_import('src.core.download', 'DownloadManager')
ArchiveProcessor = safe_import('src.core.archive', 'ArchiveProcessor')
UserChromeManager = safe_import('src.core.userchrome', 'UserChromeManager')
ModManager = safe_import('src.core.mod', 'ModManager')
ProfileManager = safe_import('src.core.profile', 'ProfileManager')

# Import infrastructure classes
FileManager = safe_import('src.infrastructure.file_manager', 'FileManager')
ConfigStore = safe_import('src.infrastructure.config_store', 'ConfigStore')
GitHubApi = safe_import('src.infrastructure.github_api', 'GitHubApi')
GitLabApi = safe_import('src.infrastructure.gitlab_api', 'GitLabApi')

# Create a dummy logger class instead of importing
class Logger:
    """Dummy logger class that does nothing"""
    def __init__(self, log_dir="", app_name=""):
        pass
    def debug(self, message): print(f"DEBUG: {message}")
    def info(self, message): print(f"INFO: {message}")
    def warning(self, message): print(f"WARNING: {message}")
    def error(self, message): print(f"ERROR: {message}")
    def critical(self, message): print(f"CRITICAL: {message}")
    def exception(self, message): print(f"EXCEPTION: {message}")
    def set_level(self, level): pass

# Import application services
ImportService = safe_import('src.application.import_service', 'ImportService')
ProfileService = safe_import('src.application.profile_service', 'ProfileService')
UpdateService = safe_import('src.application.update_service', 'UpdateService')
SettingsService = safe_import('src.application.settings', 'SettingsService')

# Import UI components
MainWindow = safe_import('src.ui.main_window', 'MainWindow')
MainPresenter = safe_import('src.ui.presenters.main_presenter', 'MainPresenter')
ImportPresenter = safe_import('src.ui.presenters.import_presenter', 'ImportPresenter')
ManageImportsPresenter = safe_import('src.ui.presenters.manage_imports_presenter', 'ManageImportsPresenter')
StyleSystem = safe_import('src.ui.style', 'StyleSystem')
install_icons = safe_import('src.ui.style', 'install_icons')

def setup_application():
    """Set up the application dependencies and services"""
    # Determine config directory
    if sys.platform == 'win32':
        config_dir = os.path.join(os.environ.get('APPDATA', ''), 'UserChromeLoader')
    else:
        config_dir = os.path.join(os.path.expanduser('~'), '.config', 'userchrome-loader')

    # Create config directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    
    # Initialize logger
    logger = Logger()
    logger.info(f"Starting UserChrome Loader, config directory: {config_dir}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"System platform: {sys.platform}")
    logger.info(f"Python path: {sys.path}")
    
    # Make sure libarchive modules are available
    try:
        import libarchive
        import libarchive.public
        logger.info(f"libarchive loaded successfully from: {libarchive.__file__}")
    except ImportError as e:
        logger.error(f"Failed to import libarchive: {e}")
        # Continue anyway, we'll handle it gracefully

    # Initialize infrastructure components
    file_manager = None
    config_store = None
    github_api = None
    gitlab_api = None
    settings_service = None
    profile_service = None
    import_service = None
    update_service = None
    
    try:
        # Use dummy implementations if imports failed
        if not FileManager:
            class DummyFileManager:
                def create_directory(self, path): return True
                def copy_file(self, src, dest): return True
                def write_file(self, path, content): return True
                def read_file(self, path): return ""
            file_manager = DummyFileManager()
            logger.warning("Using dummy FileManager")
        else:
            file_manager = FileManager()
        
        if not ConfigStore:
            class DummyConfigStore:
                def __init__(self, path): self.config = {}
                def get(self, key, default=None): return default
                def set(self, key, value): pass
                def save(self): pass
            config_store = DummyConfigStore(os.path.join(config_dir, 'config.json'))
            logger.warning("Using dummy ConfigStore")
        else:
            config_store = ConfigStore(os.path.join(config_dir, 'config.json'))
        
        github_api = GitHubApi() if GitHubApi else None
        gitlab_api = GitLabApi() if GitLabApi else None
    except Exception as e:
        logger.error(f"Error initializing infrastructure components: {e}")
        traceback.print_exc()

    # Initialize core components
    download_manager = None
    archive_processor = None
    userchrome_manager = None
    mod_manager = None
    profile_manager = None
    
    try:
        # Create basic implementations for core components if imports failed
        if not DownloadManager:
            class DummyDownloadManager:
                def download_url(self, url, dest_path): return dest_path
                def get_file_content(self, url): return b""
            download_manager = DummyDownloadManager()
            logger.warning("Using dummy DownloadManager")
        else:
            download_manager = DownloadManager()
        
        if not ArchiveProcessor:
            class DummyArchiveProcessor:
                def is_archive(self, file_path): return False
                def extract_archive(self, archive_path, extract_dir=None): return extract_dir or ""
                def find_css_files(self, directory): return []
                def validate_extracted_content(self, extract_dir): return False, []
            archive_processor = DummyArchiveProcessor()
            logger.warning("Using dummy ArchiveProcessor")
        else:
            archive_processor = ArchiveProcessor()
        
        if not UserChromeManager:
            class DummyUserChromeManager:
                def check_chrome_dir(self, profile_dir): return True
                def create_chrome_dir(self, profile_dir): return True
                def check_userchrome_css(self, profile_dir): return True
            userchrome_manager = DummyUserChromeManager()
            logger.warning("Using dummy UserChromeManager")
        else:
            userchrome_manager = UserChromeManager()
        
        if not ModManager:
            class DummyModManager:
                def set_mods_file(self, path): pass
                def get_all_mods(self): return []
                def add_mod(self, mod): return True
                def remove_mod(self, mod_id): return True
            mod_manager = DummyModManager()
            logger.warning("Using dummy ModManager")
        else:
            mod_manager = ModManager()
            mod_manager.set_mods_file(os.path.join(config_dir, 'mods.json'))
        
        if not ProfileManager:
            class DummyProfileManager:
                def get_profiles(self, installation_path): return []
                def get_firefox_install_path(self): return ""
            profile_manager = DummyProfileManager()
            logger.warning("Using dummy ProfileManager")
        else:
            profile_manager = ProfileManager()
    except Exception as e:
        logger.error(f"Error initializing core components: {e}")
        traceback.print_exc()
        
    # Set up application services
    try:
        # Create application services, using fallbacks if needed
        if not SettingsService:
            class InitialDummySettingsService:
                def __init__(self, config_store):
                    self.config_store = config_store
                def get_setting(self, key, default=None):
                    return default
                def set_setting(self, key, value):
                    pass
                def save_settings(self):
                    pass
            settings_service = InitialDummySettingsService(config_store)
            logger.warning("Using dummy SettingsService")
        else:
            settings_service = SettingsService(config_store)
    
        if not ProfileService:
            class InitialDummyProfileService:
                def __init__(self, profile_manager, config_store):
                    self.profile_manager = profile_manager
                    self.config_store = config_store
                def get_profiles(self):
                    return []
                def get_default_profile(self):
                    return None
            profile_service = InitialDummyProfileService(profile_manager, config_store)
            logger.warning("Using dummy ProfileService")
        else:
            profile_service = ProfileService(profile_manager, config_store)
    
        # Create import service using available components
        if not ImportService:
            class InitialDummyImportService:
                def __init__(self, *args):
                    pass
                def import_from_url(self, url, profile):
                    return False, "Import service unavailable"
                def import_from_file(self, file_path, profile):
                    return False, "Import service unavailable"
                def get_all_imports(self):
                    return []
            import_service = InitialDummyImportService()
            logger.warning("Using dummy ImportService")
        else:
            # Use all available components or suitable defaults
            import_service = ImportService(
                download_manager,
                archive_processor,
                userchrome_manager,
                mod_manager,
                file_manager,
                github_api or None,
                gitlab_api or None
            )
    
        if not UpdateService:
            class InitialDummyUpdateService:
                def __init__(self, *args):
                    pass
                def check_for_updates(self):
                    return False, None
                def update_mod(self, mod_id):
                    return False, "Update service unavailable"
            update_service = InitialDummyUpdateService()
            logger.warning("Using dummy UpdateService")
        else:
            update_service = UpdateService(
                download_manager,
                mod_manager,
                github_api or None,
                gitlab_api or None
            )
    except Exception as e:
        logger.error(f"Error initializing application services: {e}")
        traceback.print_exc()

    # Log service status
    logger.info(f"Services initialized - settings: {'OK' if settings_service is not None else 'FAILED'}, " +
                f"profile: {'OK' if profile_service is not None else 'FAILED'}, " +
                f"import: {'OK' if import_service is not None else 'FAILED'}, " +
                f"update: {'OK' if update_service is not None else 'FAILED'}")
    
    # Ensure none of the critical services are None
    if settings_service is None:
        logger.critical("Settings service failed to initialize - using minimal implementation")
        # Create minimal settings service to prevent crashes
        class FallbackSettingsService:
            def __init__(self, config_store):
                self.config_store = config_store
            def get_setting(self, key, default=None):
                return default
            def set_setting(self, key, value):
                pass
            def save_settings(self):
                pass
        settings_service = FallbackSettingsService(config_store)
        
    if profile_service is None:
        logger.critical("Profile service failed to initialize - using minimal implementation")
        # Create minimal profile service to prevent crashes
        class FallbackProfileService:
            def __init__(self, profile_manager, config_store):
                self.profile_manager = profile_manager
                self.config_store = config_store
            def get_profiles(self):
                return []
            def get_default_profile(self):
                return None
        profile_service = FallbackProfileService(profile_manager, config_store)
        
    if import_service is None:
        logger.critical("Import service failed to initialize - using minimal implementation")
        # Create minimal import service to prevent crashes
        class FallbackImportService:
            def __init__(self, *args):
                pass
            def import_from_url(self, url, profile):
                return False, "Import service unavailable"
            def import_from_file(self, file_path, profile):
                return False, "Import service unavailable"
            def get_all_imports(self):
                return []
        import_service = FallbackImportService()
        
    if update_service is None:
        logger.critical("Update service failed to initialize - using minimal implementation")
        # Create minimal update service to prevent crashes
        class FallbackUpdateService:
            def __init__(self, *args):
                pass
            def check_for_updates(self):
                return False, None
            def update_mod(self, mod_id):
                return False, "Update service unavailable"
        update_service = FallbackUpdateService()
    
    # Return all services (with guaranteed non-None values)
    return {
        'settings_service': settings_service,
        'profile_service': profile_service,
        'import_service': import_service,
        'update_service': update_service,
        'file_manager': file_manager,
        'logger': logger
    }

def main():
    """Main application entry point"""
    try:
        # Create Qt application
        if not QApplication:
            print("CRITICAL ERROR: QApplication could not be imported")
            return 1
            
        app = QApplication(sys.argv)
        app.setApplicationName("UserChrome Loader")
        app.setApplicationDisplayName("UserChrome Loader")
        app.setOrganizationName("Orbital")

        # Set up services first to check dependencies
        services = setup_application()
        logger = services.get('logger', Logger())

        # Install icons and set application icon
        icons_dir = None
        if install_icons:
            try:
                icons_dir = install_icons(app)
                if icons_dir and QDir:
                    QDir.addSearchPath("icons", icons_dir)
            except Exception as e:
                logger.error(f"Error installing icons: {e}")
                
        # Ensure the application icon is set
        try:
            set_app_icon = safe_import('src.ui.style.icons', 'set_app_icon')
            if set_app_icon:
                set_app_icon(app)
        except Exception as e:
            logger.error(f"Error setting application icon: {e}")

        # Apply Fluent UI styling - using light theme explicitly
        if StyleSystem:
            try:
                StyleSystem.apply_style(app, theme="light")
            except Exception as e:
                logger.error(f"Error applying style: {e}")

        # All services should be available now (even if they're dummy implementations)
        # Just log if any are using fallbacks
        fallback_services = []
        for key in ['profile_service', 'settings_service', 'import_service']:
            service = services.get(key)
            if service and service.__class__.__name__.startswith('Dummy'):
                fallback_services.append(key)
                
        if fallback_services:
            logger.warning(f"Using fallback implementations for: {', '.join(fallback_services)}")
            # We'll continue with fallback implementations rather than stopping

        # Create presenters
        try:
            main_presenter = MainPresenter(
                profile_service=services['profile_service'],
                settings_service=services['settings_service']
            ) if MainPresenter else None
            
            import_presenter = ImportPresenter(
                import_service=services['import_service'],
                settings_service=services['settings_service']
            ) if ImportPresenter else None
            
            manage_presenter = ManageImportsPresenter(
                import_service=services['import_service']
            ) if ManageImportsPresenter else None

            # Create main window
            window = MainWindow() if MainWindow else None
            
            if all([window, main_presenter, import_presenter, manage_presenter]):
                # Connect presenters to window
                main_presenter.set_view(window)
                import_presenter.set_view(window)
                manage_presenter.set_view(window)

                # Set presenters in window
                window.set_presenters(
                    main_presenter,
                    import_presenter,
                    manage_presenter
                )

                # Show window
                window.show()

                # Start application
                return app.exec()
            else:
                logger.critical("Failed to initialize UI components")
                return 1
                
        except Exception as e:
            logger.critical(f"Error creating UI: {e}")
            traceback.print_exc()
            return 1
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
