import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                           QLabel, QComboBox, QStackedWidget, QHBoxLayout,
                           QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
                           QProgressBar, QCheckBox, QMenu, QToolButton, QSplitter,
                           QFormLayout, QSpacerItem, QSizePolicy, QDialog,
                           QInputDialog, QStyle, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QItemSelectionModel, QRect
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QScreen, QColor, QKeyEvent, QPalette
from typing import Optional, final, Any
from src.core.models import Profile, ImportEntry

from src.ui.style.animated_button import AnimatedButton
from src.ui.presenters.main_presenter import MainPresenter
from src.ui.presenters.import_presenter import ImportPresenter
from src.ui.presenters.manage_imports_presenter import ManageImportsPresenter
from src.ui.dialogs.welcome_dialog import WelcomeDialog
from src.ui.dialogs.confirm_dialog import ConfirmDialog
from src.ui.dialogs.subfolder_dialog import SubfolderDialog
from src.ui.dialogs.file_dialogs import FileDialogs
from src.ui.dialogs.loading_dialog import LoadingDialog
from src.ui.workers.url_import_worker import UrlImportWorker
from src.ui.style.style import StyleSystem

@final
class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UserChrome Loader")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        self.resize(550, 450)  # Match the size of the WelcomeDialog
        self.setObjectName("fluentWindow")
        
        # Set window icon explicitly for this window
        from PyQt6.QtGui import QIcon
        from pathlib import Path
        
        # Try different potential locations for the icon file
        icon_locations = [
            Path("dist/icons/app.ico"),
            Path("dist/icons/app.icns"),
            Path("assets/icon.ico"),
            Path("assets/icon.icns"),
            Path("assets/icon.svg"),
        ]
        
        # Find the first icon that exists
        for path in icon_locations:
            if path.exists():
                self.setWindowIcon(QIcon(str(path)))
                break
        
        # Center the window on the screen
        self.center_on_screen()
        
        # Ensure window stays centered when user resizes it
        self.was_maximized = False

        # Initialize presenters
        self.main_presenter = None
        self.import_presenter = None
        self.manage_presenter = None
        
        # Initialize instance variables
        self.settings_service = None
        self.stacked_widget = None
        
        # Get the current theme
        app = QApplication.instance()
        if app:
            palette = app.palette()
            bg_color = palette.color(QPalette.ColorRole.Window).name()
            self.theme = "dark" if bg_color < "#808080" else "light"
        else:
            self.theme = "light"
        self.progress_bar = None
        self.installation_combo = None
        self.custom_path_edit = None
        self.browse_button = None
        self.add_installation_button = None
        self.profile_list = None
        self.back_to_installation_button = None
        self.select_profile_button = None
        self.import_button = None
        self.manage_button = None
        self.check_updates_button = None
        self.profile_info_label = None
        self.change_profile_button = None
        self.import_type_combo = None
        self.choose_button = None
        self.url_edit = None
        self.url_submit_button = None
        self.back_to_menu_button = None
        self.loading_dialog = None
        self.import_worker = None
        self.imports_list = None
        self.toggle_import_button = None
        self.remove_import_button = None
        self.back_to_menu_from_manage_button = None
        self.update_worker = None
        self.update_apply_worker = None

        # Initialize UI
        self.setup_ui()

    def set_presenters(self, main_presenter: MainPresenter,
                      import_presenter: ImportPresenter,
                      manage_presenter: ManageImportsPresenter) -> None:
        """Set presenters for this view"""
        self.main_presenter = main_presenter
        self.import_presenter = import_presenter
        self.manage_presenter = manage_presenter

        # Keep a reference to settings service for convenience
        if main_presenter:
            self.settings_service = main_presenter.settings_service

        # Initialize
        if self.main_presenter:
            self.main_presenter.initialize()

    def setup_ui(self):
        """Set up the main window UI"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Add pages
        self.setup_welcome_page()
        self.setup_installation_page()
        self.setup_profile_page()
        self.setup_main_menu_page()
        self.setup_import_page()
        self.setup_manage_imports_page()

        # Status bar
        self.statusBar().showMessage("Ready")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
        # Apply consistent styling
        self.apply_theme_styling()

    def setup_welcome_page(self):
        """Set up welcome page"""
        # Welcome page is handled by WelcomeDialog
        welcome_page = QWidget()
        self.stacked_widget.addWidget(welcome_page)



    def setup_installation_page(self):
        """Set up installation selection page"""
        installation_page = QWidget()
        layout = QVBoxLayout(installation_page)

        # Title
        title_label = QLabel("Select Zen Browser Installation")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_font.setFamily("Bricolage Grotesque")
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Installation selection
        self.installation_combo = QComboBox()
        self.installation_combo.currentTextChanged.connect(self.handle_installation_selection)
        layout.addWidget(self.installation_combo)

        # Add custom installation
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Or add a custom path:"))
        self.custom_path_edit = QLineEdit()
        custom_layout.addWidget(self.custom_path_edit)
        self.browse_button = AnimatedButton("Browse...")
        self.browse_button.clicked.connect(self.browse_installation)
        self.browse_button.setFixedHeight(36)
        custom_layout.addWidget(self.browse_button)
        layout.addLayout(custom_layout)

        # Add button
        self.add_installation_button = AnimatedButton("Add Installation", fill_width=True)
        self.add_installation_button.setProperty("accent", "true")
        self.add_installation_button.clicked.connect(self.add_installation)
        self.add_installation_button.setFixedHeight(36)
        layout.addWidget(self.add_installation_button)

        # Spacer
        layout.addStretch()

        self.stacked_widget.addWidget(installation_page)

    def setup_profile_page(self):
        """Set up profile selection page"""
        profile_page = QWidget()
        layout = QVBoxLayout(profile_page)

        # Title
        title_label = QLabel("Select Profile")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_font.setFamily("Bricolage Grotesque")
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Profile selection
        self.profile_list = QListWidget()
        self.profile_list.itemDoubleClicked.connect(self.handle_profile_selection)
        layout.addWidget(self.profile_list)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)  # Add spacing for buttons

        self.back_to_installation_button = AnimatedButton("Back")
        self.back_to_installation_button.clicked.connect(self.go_to_installation)
        self.back_to_installation_button.setFixedHeight(36)
        button_layout.addWidget(self.back_to_installation_button)

        button_layout.addStretch()

        self.select_profile_button = AnimatedButton("Select Profile")
        self.select_profile_button.setProperty("accent", "true")
        self.select_profile_button.clicked.connect(self.handle_profile_selection)
        self.select_profile_button.setFixedHeight(36)
        button_layout.addWidget(self.select_profile_button)

        layout.addLayout(button_layout)

        self.stacked_widget.addWidget(profile_page)

    def setup_main_menu_page(self):
        """Set up main menu page"""
        main_menu_page = QWidget()
        layout = QVBoxLayout(main_menu_page)

        # Title
        title_label = QLabel("UserChrome Loader")
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_font.setFamily("Bricolage Grotesque")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Add spacing for buttons
        layout.setSpacing(25)

        # Buttons
        self.import_button = AnimatedButton("Import CSS", fill_width=True)
        self.import_button.setFixedHeight(50)
        self.import_button.setProperty("accent", "true")
        self.import_button.clicked.connect(self.go_to_import)
        layout.addWidget(self.import_button)

        self.manage_button = AnimatedButton("Manage Imports", fill_width=True)
        self.manage_button.setFixedHeight(50)
        self.manage_button.setProperty("accent", "true")
        self.manage_button.clicked.connect(self.go_to_manage)
        layout.addWidget(self.manage_button)

        self.check_updates_button = AnimatedButton("Check for Updates", fill_width=True)
        self.check_updates_button.setFixedHeight(50)
        self.check_updates_button.setProperty("accent", "true")
        self.check_updates_button.clicked.connect(self.check_for_updates)
        layout.addWidget(self.check_updates_button)

        # Profile info
        self.profile_info_label = QLabel()
        layout.addWidget(self.profile_info_label)

        # Change profile
        self.change_profile_button = AnimatedButton("Change Profile", fill_width=True)
        self.change_profile_button.setProperty("changeProfile", "true")
        self.change_profile_button.clicked.connect(self.go_to_profile)
        self.change_profile_button.setFixedHeight(40)
        layout.addWidget(self.change_profile_button)

        self.stacked_widget.addWidget(main_menu_page)

    def setup_import_page(self):
        """Set up import page"""
        import_page = QWidget()
        layout = QVBoxLayout(import_page)

        # Title
        title_label = QLabel("Import CSS")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_font.setFamily("Bricolage Grotesque")
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Import options
        self.import_type_combo = QComboBox()
        self.import_type_combo.addItems(["Single CSS File", "Mod Folder"])
        layout.addWidget(self.import_type_combo)

        # Choose file/folder button
        self.choose_button = AnimatedButton("Choose Local File/Folder", fill_width=True)
        self.choose_button.clicked.connect(self.handle_local_import)
        self.choose_button.setFixedHeight(40)
        layout.addWidget(self.choose_button)
        
        # Add spacing for buttons
        layout.setSpacing(20)

        # URL import section
        url_label = QLabel("Or import from URL:")
        layout.addWidget(url_label)

        # URL input
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Enter URL to CSS file, GitHub repository, or GitLab repository")
        layout.addWidget(self.url_edit)

        # URL submit button
        self.url_submit_button = AnimatedButton("Import from URL", fill_width=True)
        self.url_submit_button.setProperty("accent", "true")
        self.url_submit_button.clicked.connect(self.handle_url_import)
        self.url_submit_button.setFixedHeight(40)
        layout.addWidget(self.url_submit_button)

        # Back button
        self.back_to_menu_button = AnimatedButton("Back to Menu", fill_width=True)
        self.back_to_menu_button.clicked.connect(self.go_to_menu)
        self.back_to_menu_button.setFixedHeight(40)
        layout.addWidget(self.back_to_menu_button)

        self.stacked_widget.addWidget(import_page)

    def handle_local_import(self):
        """Handle importing from a local file or folder"""
        import_type = self.import_type_combo.currentIndex()

        if import_type == 0:  # Single CSS file
            # Get file path
            file_path = self.get_file_path()
            if not file_path:
                return  # User cancelled

            # Handle file import
            if self.import_presenter and self.main_presenter and self.main_presenter.current_profile:
                self.import_presenter.handle_file_import(self.main_presenter.current_profile)
        else:  # Mod folder
            # Get folder path
            folder_path = self.get_folder_path()
            if not folder_path:
                return  # User cancelled

            # Handle folder import
            if self.import_presenter and self.main_presenter and self.main_presenter.current_profile:
                self.import_presenter.handle_folder_import(self.main_presenter.current_profile)

    # src/ui/main_window.py - import the worker
    from src.ui.workers.url_import_worker import UrlImportWorker

    # src/ui/main_window.py - update handle_url_import method
    def handle_url_import(self):
        """Handle importing from a URL"""
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Please enter a URL to import from.")
            return

        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL (must start with http:// or https://).")
            return

        if not self.import_presenter or not self.main_presenter or not self.main_presenter.current_profile:
            QMessageBox.warning(self, "Error", "No profile selected.")
            return

        # Create and show loading dialog
        self.loading_dialog = LoadingDialog(self, "Grabbing the Import from your URL")
        self.loading_dialog.show()

        # Create worker thread
        self.import_worker = UrlImportWorker(
            self.import_presenter.import_service,
            self.main_presenter.current_profile,
            url
        )

        # Connect signals
        self.import_worker.progress.connect(self.loading_dialog.set_message)
        self.import_worker.finished.connect(self.handle_url_import_finished)

        # Start worker
        self.import_worker.start()

    def handle_url_import_finished(self, success: bool, message: str, mod_info: dict) -> None:
        """Handle URL import completion"""
        # Close loading dialog
        if hasattr(self, 'loading_dialog') and self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        # Show result
        if success:
            self.show_success(message)
            # Refresh imports list if we're on the manage imports page
            if self.stacked_widget.currentIndex() == 5:  # Manage imports page
                if self.manage_presenter and self.main_presenter and self.main_presenter.current_profile:
                    self.manage_presenter.load_imports(self.main_presenter.current_profile)
            # Go to main menu after successful import
            self.go_to_menu()
        else:
            self.show_error(message)

    def setup_manage_imports_page(self):
        """Set up manage imports page"""
        self.manage_imports_page = QWidget()
        self.stacked_widget.addWidget(self.manage_imports_page)
        
        # Create layout
        manage_imports_layout = QVBoxLayout(self.manage_imports_page)
        
        # Title
        title_label = QLabel("Manage Imports")
        title_label.setObjectName("pageTitle")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_font.setFamily("Bricolage Grotesque")
        title_label.setFont(title_font)
        manage_imports_layout.addWidget(title_label)

        # Instructions label
        instructions = QLabel("Select multiple imports using Ctrl+click, Shift+click, or by dragging with the mouse. Press Delete to remove selected imports, Ctrl+T to toggle them.")
        manage_imports_layout.addWidget(instructions)

        # Create a custom QListWidget with key event handling
        class KeyListWidget(QListWidget):
            def keyPressEvent(self, e: Optional[QKeyEvent]) -> None:  # type: ignore
                # Get reference to MainWindow instance
                main_window = None
                parent = self.parent()
                while parent is not None:
                    if isinstance(parent, MainWindow):
                        main_window = parent
                        break
                    parent = parent.parent()
                
                # Check for Delete key
                if e is not None and e.key() == Qt.Key.Key_Delete and main_window is not None:
                    main_window.remove_selected_imports()
                    return
                # Check for Ctrl+T
                if e is not None and e.key() == Qt.Key.Key_T and e.modifiers() & Qt.KeyboardModifier.ControlModifier and main_window is not None:
                    main_window.toggle_selected_imports()
                    return
                # Otherwise, pass to parent implementation
                super().keyPressEvent(e)

        # Imports list with multi-selection enabled
        self.imports_list = KeyListWidget()
        self.imports_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        manage_imports_layout.addWidget(self.imports_list)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)  # Add spacing for buttons

        self.toggle_import_button = AnimatedButton("Toggle Selected Imports")
        self.toggle_import_button.clicked.connect(self.toggle_selected_imports)
        self.toggle_import_button.setFixedHeight(36)
        button_layout.addWidget(self.toggle_import_button)

        self.remove_import_button = AnimatedButton("Remove Selected Imports")
        self.remove_import_button.clicked.connect(self.remove_selected_imports)
        self.remove_import_button.setFixedHeight(36)
        button_layout.addWidget(self.remove_import_button)

        manage_imports_layout.addLayout(button_layout)
        manage_imports_layout.setSpacing(20)  # Add spacing for buttons

        # Back button
        self.back_to_menu_from_manage_button = AnimatedButton("Back to Menu", fill_width=True)
        self.back_to_menu_from_manage_button.clicked.connect(self.go_to_menu)
        self.back_to_menu_from_manage_button.setFixedHeight(40)
        manage_imports_layout.addWidget(self.back_to_menu_from_manage_button)

    def handle_installation_selection(self, installation_name: str) -> None:
        """Handle selection of a browser installation"""
        if not installation_name or not self.main_presenter:
            return

        # Select the installation and load profiles
        if self.main_presenter.select_installation(installation_name):
            # After selecting installation, navigate to profile page
            self.stacked_widget.setCurrentIndex(2)  # Index for profile page

    def browse_installation(self):
        """Browse for a custom installation path"""
        installation_path = FileDialogs.get_folder(self, "Select Zen Browser Installation Directory")
        if installation_path:
            self.custom_path_edit.setText(installation_path)

    def add_installation(self):
        """Add a custom installation path"""
        path = self.custom_path_edit.text().strip()

        # If the path is empty, show a warning
        if not path:
            QMessageBox.warning(self, "Missing Path", "Please enter a path or browse for a directory.")
            return

        # Validate path
        if not os.path.exists(path):
            QMessageBox.warning(self, "Invalid Path", f"The path '{path}' does not exist.")
            return

        # Get a name for the installation
        name, ok = QInputDialog.getText(self, "Installation Name",
                                      "Enter a name for this installation:",
                                      QLineEdit.EchoMode.Normal, os.path.basename(path))
        if not ok or not name:
            return

        # Add the installation through the presenter
        if self.main_presenter:
            if self.main_presenter.add_installation(name, path):
                # This will select the installation and navigate to the profile page
                self.statusBar().showMessage(f"Added installation: {name}")
            else:
                self.statusBar().showMessage("Failed to add installation")

    def go_to_installation(self):
        """Navigate to installation page"""
        self.stacked_widget.setCurrentIndex(1)  # Index for installation page

    def go_to_profile(self):
        """Navigate to profile selection page"""
        # Make sure profiles are loaded
        if self.main_presenter and self.main_presenter.current_installation:
            self.main_presenter.select_installation(self.main_presenter.current_installation)

        # Navigate to profile page
        self.stacked_widget.setCurrentIndex(2)  # Index for profile page

    def handle_profile_selection(self):
        """Handle selection of a profile"""
        item = self.profile_list.currentItem()
        if not item or not self.main_presenter:
            return

        # Get original profile name stored in user role
        profile_name = item.data(Qt.ItemDataRole.UserRole)
        if not profile_name:
            # Fallback to displayed text if no user data
            profile_name = item.text()

        if self.main_presenter.select_profile(profile_name):
            self.go_to_menu()

    def go_to_menu(self):
        """Navigate to main menu"""
        self.stacked_widget.setCurrentIndex(3)  # Index for main menu page

    def go_to_import(self):
        """Navigate to import page"""
        self.stacked_widget.setCurrentIndex(4)  # Index for import page

    # src/ui/main_window.py - update go_to_manage method

    def go_to_manage(self):
        """Navigate to manage imports page"""
        # Load imports before showing the page
        if self.main_presenter and self.main_presenter.current_profile:
            if self.manage_presenter:
                self.manage_presenter.load_imports(self.main_presenter.current_profile)

        # Navigate to the page
        self.stacked_widget.setCurrentIndex(5)  # Index for manage imports page

    def check_for_updates(self):
        """Check for updates to installed mods"""
        # Show loading dialog while checking for updates
        from src.ui.dialogs.loading_dialog import LoadingDialog
        from src.ui.workers.update_worker import UpdateCheckWorker
        from PyQt6.QtCore import QThreadPool
        
        # Check if import_presenter is set
        if not hasattr(self, 'import_presenter') or self.import_presenter is None:
            self.show_error("Import presenter not initialized")
            return
            
        # Create and show loading dialog
        self.loading_dialog = LoadingDialog(self, "Checking for updates...")
        self.loading_dialog.show()
        
        # Get mod manager from the import_presenter's import service
        mod_manager = self.import_presenter.import_service.mod_manager
        
        # Initialize components
        from src.infrastructure.github_api import GitHubApi
        from src.infrastructure.gitlab_api import GitLabApi
        
        # Use the download manager from the import service
        download_manager = self.import_presenter.import_service.download_manager
        github_api = GitHubApi()
        gitlab_api = GitLabApi()
        
        # Create worker
        self.update_worker = UpdateCheckWorker(
            mod_manager=mod_manager,
            download_manager=download_manager,
            github_api=github_api,
            gitlab_api=gitlab_api
        )
        
        # Connect signals
        self.update_worker.signals.progress.connect(self.loading_dialog.set_message)
        self.update_worker.signals.finished.connect(self._handle_update_check_finished)
        self.update_worker.signals.error.connect(self._handle_update_check_error)
        
        # Start the worker thread
        QThreadPool.globalInstance().start(self.update_worker)
    
    def _apply_updates(self, mod_names: list) -> None:
        """Apply updates to the selected mods"""
        if not mod_names:
            return
            
        # Check if import_presenter is set
        if not hasattr(self, 'import_presenter') or self.import_presenter is None:
            self.show_error("Import presenter not initialized")
            return
            
        # Show loading dialog while applying updates
        from src.ui.dialogs.loading_dialog import LoadingDialog
        from src.ui.workers.update_worker import UpdateApplyWorker
        from PyQt6.QtCore import QThreadPool
        
        # Create loading dialog
        self.loading_dialog = LoadingDialog(self, f"Updating {len(mod_names)} mods...")
        self.loading_dialog.show()
        
        # Get mod manager from the import_presenter's import service
        mod_manager = self.import_presenter.import_service.mod_manager
        
        # Initialize services
        from src.infrastructure.github_api import GitHubApi
        from src.infrastructure.gitlab_api import GitLabApi
        
        # Use the download manager from the import service
        download_manager = self.import_presenter.import_service.download_manager
        github_api = GitHubApi()
        gitlab_api = GitLabApi()
        
        # Create worker
        self.update_apply_worker = UpdateApplyWorker(
            mod_manager=mod_manager,
            download_manager=download_manager,
            github_api=github_api,
            gitlab_api=gitlab_api,
            mod_names=mod_names
        )
        
        # Connect signals
        self.update_apply_worker.signals.progress.connect(
            lambda msg, curr, total: self.loading_dialog.set_message(msg)
        )
        self.update_apply_worker.signals.finished.connect(self._handle_update_apply_finished)
        self.update_apply_worker.signals.error.connect(self._handle_update_apply_error)
        
        # Start the worker thread
        QThreadPool.globalInstance().start(self.update_apply_worker)
        
    def _handle_update_check_finished(self, updates_data: dict) -> None:
        """Handle when update check is finished"""
        # Close the loading dialog
        if hasattr(self, 'loading_dialog') and self.loading_dialog is not None:
            self.loading_dialog.close()
            
        # Check if any updates are available
        has_updates = any(info.get('has_update', False) for info in updates_data.values())
        
        if not has_updates:
            self.show_success("All mods are up to date")
            return
        
        # Show update dialog with diff information
        from src.ui.dialogs.update_dialog import UpdateDialog
        update_dialog = UpdateDialog(self)
        update_dialog.set_update_data(updates_data)
        update_dialog.updates_applied.connect(self._apply_updates)
        update_dialog.exec()
        
    def _handle_update_check_error(self, error_message: str) -> None:
        """Handle error during update check"""
        # Close the loading dialog
        if hasattr(self, 'loading_dialog') and self.loading_dialog is not None:
            self.loading_dialog.close()
            
        # Show error message
        self.show_error(error_message)
        
    def _handle_update_apply_finished(self, success_count: int, failed_mods: list) -> None:
        """Handle when update application is finished"""
        # Close the loading dialog
        if hasattr(self, 'loading_dialog') and self.loading_dialog is not None:
            self.loading_dialog.close()
            
        # Show results
        total_mods = success_count + len(failed_mods)
        if success_count == total_mods:
            self.show_success(f"Successfully updated {success_count} mods")
        elif success_count > 0:
            self.show_success(f"Updated {success_count} mods, {len(failed_mods)} failed:\n" + 
                             "\n".join(failed_mods))
        else:
            self.show_error(f"Failed to update mods:\n" + "\n".join(failed_mods))
            
        # Refresh the imports list
        self.refresh_imports_list()
        
    def _handle_update_apply_error(self, error_message: str) -> None:
        """Handle error during update application"""
        # Close the loading dialog
        if hasattr(self, 'loading_dialog') and self.loading_dialog is not None:
            self.loading_dialog.close()
            
        # Show error message
        self.show_error(error_message)

    def show_progress(self, message: str) -> None:
        """Show progress message and bar"""
        self.statusBar().showMessage(message)
        self.progress_bar.setVisible(True)

    def show_error(self, message: str) -> None:
        """Show error message"""
        self.statusBar().showMessage(f"Error: {message}")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", message)

    def show_success(self, message: str) -> None:
        """Show success message"""
        self.statusBar().showMessage(message)
        self.progress_bar.setVisible(False)

    def refresh_imports_list(self):
        """Refresh the list of imports"""
        # This would typically involve calling the presenter
        # to get the current list of imports and update the UI
        pass

    def get_file_path(self):
        """Get a file path from the user"""
        return FileDialogs.get_css_file(self)

    def get_folder_path(self):
        """Get a folder path from the user"""
        folder_path = FileDialogs.get_folder(self, "Select Folder")
        if folder_path:
            # Update the custom path field if we got a path from the dialog
            self.custom_path_edit.setText(folder_path)
        return folder_path

    def get_subfolder_preference(self):
        """Get the subfolder preference from the user"""
        # Get previous preference
        previous = self.settings_service.get_setting("preferred_subfolder") if hasattr(self, "settings_service") else None

        # Create and show dialog
        dialog = SubfolderDialog(self, default_option=previous)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selection = dialog.get_selection()
            return selection if selection is not None else ""
        return ""

    def navigate_to_page(self, page_name: str) -> None:
        """Navigate to a specific page by name"""
        page_indices = {
            "welcome": 0,
            "installation": 1,
            "profile": 2,
            "main_menu": 3,
            "import": 4,
            "manage_imports": 5
        }

        if page_name in page_indices:
            if page_name == "welcome":
                # Display welcome dialog instead of navigating to the welcome page
                self.show_welcome_dialog()
            else:
                self.stacked_widget.setCurrentIndex(page_indices[page_name])

    def show_welcome_dialog(self, set_welcome_shown_callback=None) -> bool:  # type: ignore
        """
        Show the welcome dialog

        Args:
            set_welcome_shown_callback: Optional callback to mark welcome as shown

        Returns:
            True if the dialog was accepted, False otherwise
        """
        from src.ui.dialogs.welcome_dialog import WelcomeDialog

        dialog = WelcomeDialog(self)
        # Ensure dialog appears on top and is active
        dialog.setWindowState(dialog.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)

        # Track whether the dialog was accepted
        was_accepted = [False]

        def handle_dialog_closed(dont_show_again, accepted):
            """Handle dialog closed signal"""
            if set_welcome_shown_callback:
                # Always call the callback to mark welcome as shown,
                # regardless of the dont_show_again checkbox
                set_welcome_shown_callback()
            was_accepted[0] = accepted

        # Connect the closed signal
        dialog.closed.connect(handle_dialog_closed)

        # Show the dialog
        result = dialog.exec()
        
        # The dialog.exec() result is more reliable than the signal
        # If exec() returns accepted (1), use that
        if result:
            was_accepted[0] = True
            
        # For the welcome dialog, always return True to prevent app exit
        # This allows the user to proceed to the main window
        return True

    def handle_welcome_dialog_closed(self, dont_show_again: bool, accepted: bool) -> None:
        """Handle welcome dialog closed"""
        if self.main_presenter:
            if dont_show_again:
                self.main_presenter.set_welcome_shown()

            # Navigate to installation page after welcome dialog
            self.navigate_to_page("installation")

    def show_installations(self, installations: dict) -> None:  # type: ignore
        """Show the list of installations in the combo box"""
        self.installation_combo.clear()
        for name, path in installations.items():
            self.installation_combo.addItem(name, path)  # Store path as user data

    def show_profiles(self, profiles: list) -> None:  # type: ignore
        """Show the list of profiles in the list widget"""
        self.profile_list.clear()

        # Sort profiles by default status and name
        sorted_profiles = sorted(profiles, key=lambda p: (not p.is_default, p.name))

        for profile in sorted_profiles:
            # Create a more informative display name
            display_name = profile.name

            # Add default indicator
            if profile.is_default:
                display_name = f"✓ {display_name} (Default)"

            # Add chrome info
            if profile.has_userchrome:
                display_name += " [userChrome.css exists]"
            elif profile.has_chrome_dir:
                display_name += " [chrome dir exists]"

            # Create list item
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, profile.name)  # Store original name for selection

            # Set tooltip with path
            item.setToolTip(f"Path: {profile.path}")

            self.profile_list.addItem(item)

        # Update status
        if profiles:
            self.statusBar().showMessage(f"Found {len(profiles)} profiles")
        else:
            self.statusBar().showMessage("No profiles found")

    def show_imports(self, imports: list) -> None:  # type: ignore
        """Show the list of imports in the list widget"""
        self.imports_list.clear()

        if not imports:
            self.statusBar().showMessage("No imports found")
            return

        for import_entry in imports:
            # Create a display string
            status = "Enabled" if import_entry.enabled else "Disabled"
            display_text = f"{import_entry.path} [{status}]"

            # Create list item
            item = QListWidgetItem(display_text)

            # Store the import path as user data
            item.setData(Qt.ItemDataRole.UserRole, import_entry.path)

            # Set color based on enabled status
            if not import_entry.enabled:
                item.setForeground(Qt.GlobalColor.gray)

            self.imports_list.addItem(item)

        self.statusBar().showMessage(f"Found {len(imports)} imports")

    def toggle_selected_imports(self):
        """Toggle all selected imports"""
        selected_items = self.imports_list.selectedItems()
        if not selected_items or not self.manage_presenter or not self.main_presenter:
            return

        # Get import paths from selected items
        import_paths = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in selected_items
        ]

        # Skip empty paths
        import_paths = [path for path in import_paths if path]

        if not import_paths:
            return

        # Confirm if multiple items are selected
        if len(import_paths) > 1:
            reply = QMessageBox.question(
                self,
                "Confirm Toggle",
                f"Are you sure you want to toggle these {len(import_paths)} imports?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Show progress
        self.show_progress(f"Toggling {len(import_paths)} imports...")

        # Toggle all imports at once
        success_count = 0
        if self.manage_presenter and self.main_presenter and self.main_presenter.current_profile:
            success_count = self.manage_presenter.toggle_multiple_imports(
                self.main_presenter.current_profile, import_paths)

        # Show success message
        self.show_success(f"Successfully toggled {success_count} imports")

    def remove_selected_imports(self):
        """Remove all selected imports"""
        selected_items = self.imports_list.selectedItems()
        if not selected_items or not self.manage_presenter or not self.main_presenter:
            return

        # Get import paths from selected items
        import_paths = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in selected_items
        ]

        # Skip empty paths
        import_paths = [path for path in import_paths if path]

        if not import_paths:
            return

        # Confirm removal
        message = (f"Are you sure you want to remove these {len(import_paths)} imports?"
                   if len(import_paths) > 1 else
                   f"Remove import: {import_paths[0]}?")

        if not self.confirm_remove(message):
            return

        # Show progress
        self.show_progress(f"Removing {len(import_paths)} imports...")

        # Count successful removals
        success_count = 0

        # Instead of removing imports one by one, we'll have a single method
        # that removes all selected imports at once
        if self.manage_presenter and self.main_presenter and self.main_presenter.current_profile:
            success_count = self.manage_presenter.remove_multiple_imports(
                self.main_presenter.current_profile, import_paths)

        # Show success message
        self.show_success(f"Successfully removed {success_count} imports")

    def confirm_remove(self, message: str) -> bool:
        """Confirm before removing an import"""
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def select_css_files(self, css_files: list) -> list:  # type: ignore
        """Show a dialog to select CSS files"""
        from src.ui.dialogs.css_selection_dialog import CssSelectionDialog
        dialog = CssSelectionDialog(self, css_files)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selected_files()
        return []
        
    def center_on_screen(self):
        """Center the window on the screen"""
        # Get the screen's geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Calculate the center position
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        
        # Move window rectangle's center point to screen's center point
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
        
        # Store initial size for reference
        if not hasattr(self, 'initial_size'):
            self.initial_size = self.size()
            
    def apply_theme_styling(self) -> None:
        """Apply styling based on the current theme"""
        # Use the centralized styling from StyleSystem
        self.setStyleSheet(StyleSystem.get_main_window_style(self.theme))
