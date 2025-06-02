# src/launcher.py
import sys
import os
import traceback
from typing import cast, Optional, Dict, Any

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
    
    try:
        file_manager = FileManager() if FileManager else None
        config_store = ConfigStore(os.path.join(config_dir, 'config.json')) if ConfigStore else None
        github_api = GitHubApi() if GitHubApi else None
        gitlab_api = GitLabApi() if GitLabApi else None
    except Exception as e:
        logger.error(f"Error initializing infrastructure components: {e}")

    # Initialize core components
    download_manager = None
    archive_processor = None
    userchrome_manager = None
    mod_manager = None
    profile_manager = None
    
    try:
        download_manager = DownloadManager() if DownloadManager else None
        archive_processor = ArchiveProcessor() if ArchiveProcessor else None
        userchrome_manager = UserChromeManager() if UserChromeManager else None
        mod_manager = ModManager() if ModManager else None
        if mod_manager:
            mod_manager.set_mods_file(os.path.join(config_dir, 'mods.json'))
        profile_manager = ProfileManager() if ProfileManager else None
    except Exception as e:
        logger.error(f"Error initializing core components: {e}")

    # Initialize application services
    settings_service = None
    profile_service = None
    import_service = None
    update_service = None
    
    try:
        if SettingsService and config_store:
            settings_service = SettingsService(config_store)
            
        if ProfileService and profile_manager and config_store:
            profile_service = ProfileService(profile_manager, config_store)
            
        if ImportService and all([download_manager, archive_processor, userchrome_manager, 
                                 mod_manager, file_manager, github_api, gitlab_api]):
            import_service = ImportService(
                download_manager,
                archive_processor,
                userchrome_manager,
                mod_manager,
                file_manager,
                github_api,
                gitlab_api
            )
            
        if UpdateService and all([download_manager, mod_manager, github_api, gitlab_api]):
            update_service = UpdateService(
                download_manager,
                mod_manager,
                github_api,
                gitlab_api
            )
    except Exception as e:
        logger.error(f"Error initializing application services: {e}")

    # Return all services
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

        # Check for required services
        missing_services = []
        for key in ['profile_service', 'settings_service', 'import_service']:
            if not services.get(key):
                missing_services.append(key)
                
        if missing_services:
            logger.critical(f"Missing required services: {', '.join(missing_services)}")
            error_dialog = safe_import('PyQt6.QtWidgets', 'QMessageBox')
            if error_dialog:
                msg = error_dialog()
                msg.setIcon(error_dialog.Icon.Critical)
                msg.setText("Application Error")
                msg.setInformativeText(f"Missing required components: {', '.join(missing_services)}")
                msg.setWindowTitle("Error")
                msg.exec()
            return 1

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
