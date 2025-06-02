# src/launcher.py
import sys
import os
from typing import cast
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir

# Add the project's parent directory to Python's path
project_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_parent)

# Import core classes
from src.core.download import DownloadManager
from src.core.archive import ArchiveProcessor
from src.core.userchrome import UserChromeManager
from src.core.mod import ModManager
from src.core.profile import ProfileManager

# Import infrastructure classes
from src.infrastructure.file_manager import FileManager
from src.infrastructure.config_store import ConfigStore
from src.infrastructure.github_api import GitHubApi
from src.infrastructure.gitlab_api import GitLabApi

# Create a dummy logger class instead of importing
class Logger:
    """Dummy logger class that does nothing"""
    def __init__(self, log_dir="", app_name=""):
        pass
    def debug(self, message): pass
    def info(self, message): pass
    def warning(self, message): pass
    def error(self, message): pass
    def critical(self, message): pass
    def exception(self, message): pass
    def set_level(self, level): pass

# Import application services
from src.application.import_service import ImportService
from src.application.profile_service import ProfileService
from src.application.update_service import UpdateService
from src.application.settings import SettingsService

# Import UI components
from src.ui.main_window import MainWindow
from src.ui.presenters.main_presenter import MainPresenter
from src.ui.presenters.import_presenter import ImportPresenter
from src.ui.presenters.manage_imports_presenter import ManageImportsPresenter
from src.ui.style import StyleSystem, install_icons

def setup_application():
    """Set up the application dependencies and services"""
    # Determine config directory
    if sys.platform == 'win32':
        config_dir = os.path.join(os.environ.get('APPDATA', ''), 'UserChromeLoader')
    else:
        config_dir = os.path.join(os.path.expanduser('~'), '.config', 'userchrome-loader')

    # Create config directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    # No longer creating logs directory by default

    # Initialize infrastructure components
    file_manager = FileManager()
    config_store = ConfigStore(os.path.join(config_dir, 'config.json'))
    github_api = GitHubApi()
    gitlab_api = GitLabApi()
    logger = Logger()  # Dummy logger that does nothing

    # Initialize core components
    download_manager = DownloadManager()
    archive_processor = ArchiveProcessor()
    userchrome_manager = UserChromeManager()
    mod_manager = ModManager()
    mod_manager.set_mods_file(os.path.join(config_dir, 'mods.json'))
    profile_manager = ProfileManager()

    # Initialize application services
    settings_service = SettingsService(config_store)
    profile_service = ProfileService(profile_manager, config_store)
    import_service = ImportService(
        download_manager,
        archive_processor,
        userchrome_manager,
        mod_manager,
        file_manager,
        github_api,
        gitlab_api
    )
    update_service = UpdateService(
        download_manager,
        mod_manager,
        github_api,
        gitlab_api
    )

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
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("UserChrome Loader")
    app.setApplicationDisplayName("UserChrome Loader")
    app.setOrganizationName("Orbital")

    # Install icons and set application icon
    icons_dir = install_icons(app)
    QDir.addSearchPath("icons", icons_dir)

    # Ensure the application icon is set
    from src.ui.style.icons import set_app_icon
    set_app_icon(app)

    # Apply Fluent UI styling - using light theme explicitly
    StyleSystem.apply_style(app, theme="light")

    # Set up services
    services = setup_application()

    # Create presenters
    main_presenter = MainPresenter(
        profile_service=cast(ProfileService, services['profile_service']),
        settings_service=cast(SettingsService, services['settings_service'])
    )
    import_presenter = ImportPresenter(
        import_service=cast(ImportService, services['import_service']),
        settings_service=cast(SettingsService, services['settings_service'])
    )
    manage_presenter = ManageImportsPresenter(
        import_service=cast(ImportService, services['import_service'])
    )

    # Create main window
    window = MainWindow()

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
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
