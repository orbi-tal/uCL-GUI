from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

class UpdateCheckWorkerSignals(QObject):
    """Signals for the update check worker"""
    
    # Signal for progress updates
    progress = pyqtSignal(str)
    
    # Signal for when the check is complete
    finished = pyqtSignal(dict)
    
    # Signal for errors
    error = pyqtSignal(str)


class UpdateCheckWorker(QRunnable):
    """Worker for checking updates in a background thread"""
    
    def __init__(self, mod_manager, github_api, gitlab_api, download_manager):
        super().__init__()
        self.mod_manager = mod_manager
        self.github_api = github_api
        self.gitlab_api = gitlab_api
        self.download_manager = download_manager
        
        # Create signals
        self.signals = UpdateCheckWorkerSignals()
        
    @pyqtSlot()
    def run(self):
        """Run the update check"""
        try:
            # Get all mods
            self.signals.progress.emit("Loading installed mods...")
            mods = self.mod_manager.get_all_mods()
            
            if not mods:
                self.signals.error.emit("No mods installed")
                return
                
            # Create update service
            from src.application.update_service import UpdateService
            
            update_service = UpdateService(
                download_manager=self.download_manager,
                mod_manager=self.mod_manager,
                github_api=self.github_api,
                gitlab_api=self.gitlab_api
            )
            
            # Check for updates
            self.signals.progress.emit("Checking repository status...")
            updates_data = update_service.check_for_updates()
            
            # Emit finished signal with the update data
            self.signals.finished.emit(updates_data)
            
        except Exception as e:
            self.signals.error.emit(f"Failed to check for updates: {str(e)}")


class UpdateApplyWorker(QRunnable):
    """Worker for applying updates in a background thread"""
    
    class Signals(QObject):
        """Signals for the update apply worker"""
        progress = pyqtSignal(str, int, int)  # message, current, total
        finished = pyqtSignal(int, list)  # success_count, failed_mods
        error = pyqtSignal(str)
    
    def __init__(self, mod_manager, github_api, gitlab_api, download_manager, mod_names):
        super().__init__()
        self.mod_manager = mod_manager
        self.github_api = github_api
        self.gitlab_api = gitlab_api
        self.download_manager = download_manager
        self.mod_names = mod_names
        
        # Create signals
        self.signals = self.Signals()
        
    @pyqtSlot()
    def run(self):
        """Run the update application"""
        try:
            # Create update service
            from src.application.update_service import UpdateService
            
            update_service = UpdateService(
                download_manager=self.download_manager,
                mod_manager=self.mod_manager,
                github_api=self.github_api,
                gitlab_api=self.gitlab_api
            )
            
            # Apply updates
            success_count = 0
            failed_mods = []
            
            total_mods = len(self.mod_names)
            
            for i, mod_name in enumerate(self.mod_names):
                # Emit progress signal
                self.signals.progress.emit(
                    f"Updating mod {i+1} of {total_mods}: {mod_name}",
                    i,
                    total_mods
                )
                
                try:
                    # Get mod info
                    mod = self.mod_manager.get_mod_info(mod_name)
                    if not mod:
                        failed_mods.append(f"{mod_name} (not found)")
                        continue
                        
                    # Apply update
                    success, message = update_service.apply_update(mod_name)
                    
                    if success:
                        success_count += 1
                    else:
                        failed_mods.append(f"{mod_name} ({message})")
                        
                except Exception as e:
                    failed_mods.append(f"{mod_name} ({str(e)})")
            
            # Emit finished signal
            self.signals.finished.emit(success_count, failed_mods)
            
        except Exception as e:
            self.signals.error.emit(f"Failed to apply updates: {str(e)}")