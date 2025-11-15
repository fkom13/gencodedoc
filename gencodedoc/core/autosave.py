"""Intelligent autosave system"""
import time
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..models.config import ProjectConfig
from .versioning import VersionManager


class AutosaveHandler(FileSystemEventHandler):
    """File system event handler for autosave"""

    def __init__(self, manager: 'AutosaveManager'):
        self.manager = manager
        self.last_event = datetime.now()

    def on_modified(self, event):
        if event.is_directory:
            return

        # Debounce events (ignore if too frequent)
        now = datetime.now()
        if (now - self.last_event).total_seconds() < 1:
            return

        self.last_event = now
        self.manager.on_file_change()


class AutosaveManager:
    """Manages intelligent autosave"""

    def __init__(self, config: ProjectConfig, version_manager: VersionManager):
        self.config = config
        self.version_manager = version_manager

        self.observer: Optional[Observer] = None
        self.timer_thread: Optional[threading.Thread] = None
        self.running = False

        self.last_save = datetime.now()
        self.changes_detected = False

    def start(self) -> None:
        """Start autosave"""
        if not self.config.autosave.enabled:
            return

        self.running = True
        mode = self.config.autosave.mode

        if mode == 'timer':
            self._start_timer_mode()
        elif mode == 'diff':
            self._start_diff_mode()
        elif mode == 'hybrid':
            self._start_hybrid_mode()

    def stop(self) -> None:
        """Stop autosave"""
        self.running = False

        if self.observer:
            self.observer.stop()
            self.observer.join()

        if self.timer_thread:
            self.timer_thread.join()

    def _start_timer_mode(self) -> None:
        """Start timer-based autosave"""
        interval = self.config.autosave.timer.interval

        def timer_loop():
            while self.running:
                time.sleep(interval)
                if self.running:
                    self._create_autosave('timer')

        self.timer_thread = threading.Thread(target=timer_loop, daemon=True)
        self.timer_thread.start()

    def _start_diff_mode(self) -> None:
        """Start diff-based autosave"""
        # Watch file system
        self.observer = Observer()
        handler = AutosaveHandler(self)
        self.observer.schedule(
            handler,
            str(self.config.project_path),
            recursive=True
        )
        self.observer.start()

        # Periodic check thread
        check_interval = self.config.autosave.diff_threshold.check_interval

        def check_loop():
            while self.running:
                time.sleep(check_interval)
                if self.running and self.changes_detected:
                    if self._should_save_diff():
                        self._create_autosave('diff_threshold')
                        self.changes_detected = False

        self.timer_thread = threading.Thread(target=check_loop, daemon=True)
        self.timer_thread.start()

    def _start_hybrid_mode(self) -> None:
        """Start hybrid autosave (timer OR diff)"""
        # Watch file system
        self.observer = Observer()
        handler = AutosaveHandler(self)
        self.observer.schedule(
            handler,
            str(self.config.project_path),
            recursive=True
        )
        self.observer.start()

        def hybrid_loop():
            while self.running:
                time.sleep(60)  # Check every minute

                if not self.running:
                    break

                now = datetime.now()
                time_since_save = (now - self.last_save).total_seconds()

                # Check max interval
                if time_since_save >= self.config.autosave.hybrid.max_interval:
                    self._create_autosave('hybrid_max_interval')

                # Check min interval + changes
                elif (time_since_save >= self.config.autosave.hybrid.min_interval and
                      self.changes_detected and
                      self._should_save_diff()):
                    self._create_autosave('hybrid_threshold')
                    self.changes_detected = False

        self.timer_thread = threading.Thread(target=hybrid_loop, daemon=True)
        self.timer_thread.start()

    def on_file_change(self) -> None:
        """Called when file changes detected"""
        self.changes_detected = True

    def _should_save_diff(self) -> bool:
        """Check if changes are significant enough to save"""
        try:
            # Get latest snapshot
            latest = self.version_manager.store.db.get_latest_snapshot()
            if not latest:
                return True  # No previous snapshot, save

            # Compare with current state
            diff = self.version_manager.diff_snapshots(
                str(latest['id']),
                'current'
            )

            # Check threshold
            threshold = (
                self.config.autosave.diff_threshold.threshold
                if self.config.autosave.mode == 'diff'
                else self.config.autosave.hybrid.threshold
            )

            return diff.significance_score >= threshold

        except Exception:
            return False

    def _create_autosave(self, trigger_type: str) -> None:
        """Create an autosave snapshot"""
        try:
            self.version_manager.create_snapshot(
                message=f"Autosave ({trigger_type})",
                is_autosave=True,
                trigger_type=trigger_type
            )
            self.last_save = datetime.now()

            # Cleanup old autosaves
            max_keep = self.config.autosave.retention.max_autosaves
            self.version_manager.cleanup_old_autosaves(max_keep)

        except Exception as e:
            print(f"Autosave failed: {e}")
