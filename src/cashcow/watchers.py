"""File watchers for CashCow entity files."""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional, Set

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .storage import YamlEntityLoader
from .validation import EntityValidator


class EntityFileHandler(FileSystemEventHandler):
    """Handler for entity file system events."""

    def __init__(self, callback: Callable[[str, str], None],
                 validator: Optional[EntityValidator] = None):
        """Initialize handler.

        Args:
            callback: Function to call on file changes (event_type, file_path)
            validator: Optional validator to validate changed files
        """
        self.callback = callback
        self.validator = validator or EntityValidator()
        self.last_modified: Dict[str, float] = {}

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = event.src_path
        if not file_path.endswith('.yaml'):
            return

        # Debounce rapid changes
        now = time.time()
        if file_path in self.last_modified:
            if now - self.last_modified[file_path] < 1.0:  # 1 second debounce
                return

        self.last_modified[file_path] = now
        self.callback('modified', file_path)

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = event.src_path
        if file_path.endswith('.yaml'):
            self.callback('created', file_path)

    def on_deleted(self, event):
        """Handle file deletion events."""
        if event.is_directory:
            return

        file_path = event.src_path
        if file_path.endswith('.yaml'):
            self.callback('deleted', file_path)


class EntityFileWatcher:
    """Monitors entity files for changes and provides validation."""

    def __init__(self, entities_dir: str = "entities",
                 auto_validate: bool = True,
                 git_integration: bool = True):
        """Initialize file watcher.

        Args:
            entities_dir: Directory to watch for entity files
            auto_validate: Whether to automatically validate changed files
            git_integration: Whether to integrate with git for change tracking
        """
        self.entities_dir = Path(entities_dir)
        self.auto_validate = auto_validate
        self.git_integration = git_integration

        self.observer = Observer()
        self.validator = EntityValidator()
        self.loader = YamlEntityLoader(self.entities_dir)

        # Change tracking
        self.file_hashes: Dict[str, str] = {}
        self.change_log: list = []

        # Callbacks
        self.on_file_change_callbacks: Set[Callable] = set()
        self.on_validation_error_callbacks: Set[Callable] = set()

        # Setup handler
        self.handler = EntityFileHandler(self._handle_file_change, self.validator)

    def start(self):
        """Start watching for file changes."""
        if not self.entities_dir.exists():
            self.entities_dir.mkdir(parents=True)

        self.observer.schedule(self.handler, str(self.entities_dir), recursive=True)
        self.observer.start()

        # Initial scan
        self._scan_existing_files()

        print(f"Started watching {self.entities_dir} for changes...")

    def stop(self):
        """Stop watching for file changes."""
        self.observer.stop()
        self.observer.join()
        print("Stopped file watcher")

    def add_change_callback(self, callback: Callable[[str, str, dict], None]):
        """Add callback for file changes.

        Args:
            callback: Function(event_type, file_path, metadata) to call on changes
        """
        self.on_file_change_callbacks.add(callback)

    def add_validation_error_callback(self, callback: Callable[[str, str], None]):
        """Add callback for validation errors.

        Args:
            callback: Function(file_path, error_message) to call on validation errors
        """
        self.on_validation_error_callbacks.add(callback)

    def get_change_log(self, limit: int = 10) -> list:
        """Get recent change log.

        Args:
            limit: Maximum number of changes to return

        Returns:
            List of recent changes
        """
        return self.change_log[-limit:]

    def validate_all_files(self) -> Dict[str, list]:
        """Validate all entity files.

        Returns:
            Dictionary of file_path -> list of validation errors
        """
        errors = {}

        for yaml_file in self.entities_dir.rglob("*.yaml"):
            try:
                entity = self.loader.load_entity(yaml_file)
                file_errors = self.validator.validate_entity(entity)
                if file_errors:
                    errors[str(yaml_file)] = file_errors
            except Exception as e:
                errors[str(yaml_file)] = [str(e)]

        return errors

    def _handle_file_change(self, event_type: str, file_path: str):
        """Handle file change events."""

        # Log the change
        change_record = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'file_path': file_path,
            'file_name': Path(file_path).name
        }
        self.change_log.append(change_record)

        # Validate if auto-validation is enabled
        if self.auto_validate and event_type in ['modified', 'created']:
            self._validate_file(file_path)

        # Git integration
        if self.git_integration:
            self._track_git_changes(file_path, event_type)

        # Call registered callbacks
        for callback in self.on_file_change_callbacks:
            try:
                callback(event_type, file_path, change_record)
            except Exception as e:
                print(f"Error in change callback: {e}")

    def _validate_file(self, file_path: str):
        """Validate a specific file."""
        try:
            entity = self.loader.load_entity(Path(file_path))
            errors = self.validator.validate_entity(entity)

            if errors:
                error_msg = f"Validation errors in {file_path}:\n" + "\n".join(errors)
                print(f"⚠ {error_msg}")

                # Call validation error callbacks
                for callback in self.on_validation_error_callbacks:
                    try:
                        callback(file_path, error_msg)
                    except Exception as e:
                        print(f"Error in validation callback: {e}")
            else:
                print(f"✓ {file_path} validated successfully")

        except Exception as e:
            error_msg = f"Error validating {file_path}: {e}"
            print(f"❌ {error_msg}")

            for callback in self.on_validation_error_callbacks:
                try:
                    callback(file_path, error_msg)
                except Exception as e:
                    print(f"Error in validation callback: {e}")

    def _scan_existing_files(self):
        """Scan existing files and build initial state."""
        for yaml_file in self.entities_dir.rglob("*.yaml"):
            # Calculate file hash for change detection
            try:
                with open(yaml_file) as f:
                    content = f.read()
                    import hashlib
                    file_hash = hashlib.md5(content.encode()).hexdigest()
                    self.file_hashes[str(yaml_file)] = file_hash
            except Exception as e:
                print(f"Error reading {yaml_file}: {e}")

    def _track_git_changes(self, file_path: str, event_type: str):
        """Track changes using git (if available)."""
        try:
            import subprocess
            from pathlib import Path

            # Check if we're in a git repo
            result = subprocess.run(['git', 'rev-parse', '--git-dir'],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return

            # Get relative path
            rel_path = Path(file_path).relative_to(Path.cwd())

            # Add to git staging (optional)
            if event_type in ['modified', 'created']:
                subprocess.run(['git', 'add', str(rel_path)],
                             capture_output=True)

        except Exception as e:
            # Git integration is optional, so just log errors
            print(f"Git integration error: {e}")


class AsyncEntityWatcher:
    """Async version of entity file watcher."""

    def __init__(self, entities_dir: str = "entities"):
        """Initialize async watcher.

        Args:
            entities_dir: Directory to watch
        """
        self.entities_dir = Path(entities_dir)
        self.watcher = EntityFileWatcher(entities_dir, auto_validate=False)
        self.validation_queue = asyncio.Queue()

    async def start(self):
        """Start async watcher."""
        # Start file watcher
        self.watcher.start()

        # Add callback for validation queue
        self.watcher.add_change_callback(self._queue_validation)

        # Start validation worker
        asyncio.create_task(self._validation_worker())

    async def stop(self):
        """Stop async watcher."""
        self.watcher.stop()

    def _queue_validation(self, event_type: str, file_path: str, metadata: dict):
        """Queue file for async validation."""
        if event_type in ['modified', 'created']:
            asyncio.create_task(self.validation_queue.put((file_path, metadata)))

    async def _validation_worker(self):
        """Worker to process validation queue."""
        while True:
            try:
                file_path, metadata = await self.validation_queue.get()

                # Validate file
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.watcher._validate_file, file_path)

                self.validation_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in validation worker: {e}")


def create_file_watcher(entities_dir: str = "entities",
                       auto_validate: bool = True,
                       git_integration: bool = True) -> EntityFileWatcher:
    """Create and configure a file watcher.

    Args:
        entities_dir: Directory to watch
        auto_validate: Enable automatic validation
        git_integration: Enable git integration

    Returns:
        Configured EntityFileWatcher instance
    """
    return EntityFileWatcher(entities_dir, auto_validate, git_integration)


def start_watching(entities_dir: str = "entities",
                  auto_validate: bool = True,
                  git_integration: bool = True):
    """Start watching entity files (blocking).

    Args:
        entities_dir: Directory to watch
        auto_validate: Enable automatic validation
        git_integration: Enable git integration
    """
    watcher = create_file_watcher(entities_dir, auto_validate, git_integration)
    watcher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()


if __name__ == "__main__":
    # Demo usage
    print("Starting CashCow file watcher...")
    start_watching()
