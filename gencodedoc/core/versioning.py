"""Version management and snapshot operations"""
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..models.config import ProjectConfig
from ..models.snapshot import Snapshot, SnapshotDiff, DiffEntry
from ..storage.snapshot_store import SnapshotStore
from .scanner import FileScanner


class VersionManager:
    """Manages snapshots and versioning"""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.scanner = FileScanner(config)

        # Initialize storage
        storage_path = config.project_path / config.storage_path
        self.store = SnapshotStore(
            storage_path=storage_path,
            project_path=config.project_path,  # ✅ NOUVEAU
            compression_level=config.compression_level
        )

    def create_snapshot(
        self,
        message: Optional[str] = None,
        tag: Optional[str] = None,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        is_autosave: bool = False,
        trigger_type: str = 'manual'
    ) -> Snapshot:
        """
        Create a new snapshot

        Args:
            message: Optional commit message
            tag: Optional tag for easy reference (e.g., 'before-refactor')
            include_paths: Specific paths to include
            exclude_paths: Specific paths to exclude
            is_autosave: Whether this is an autosave
            trigger_type: What triggered the snapshot

        Returns:
            Created snapshot
        """
        # Scan files
        files = self.scanner.scan(
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            include_binary=False
        )

        # Create snapshot
        snapshot = self.store.create_snapshot(
            files=files,
            message=message,
            tag=tag,
            is_autosave=is_autosave,
            trigger_type=trigger_type
        )

        return snapshot

    def list_snapshots(
        self,
        limit: Optional[int] = None,
        include_autosave: bool = True
    ) -> List[Snapshot]:
        """List all snapshots"""
        metadata_list = self.store.list_snapshots(limit, include_autosave)

        # Convert to full snapshots
        snapshots = []
        for metadata in metadata_list:
            if metadata.id:
                snapshot = self.store.get_snapshot(metadata.id)
                if snapshot:
                    snapshots.append(snapshot)

        return snapshots

    def get_snapshot(self, snapshot_ref: str) -> Optional[Snapshot]:
        """
        Get snapshot by ID or tag

        Args:
            snapshot_ref: Snapshot ID (number) or tag (string)

        Returns:
            Snapshot or None
        """
        # Try as ID first
        try:
            snapshot_id = int(snapshot_ref)
            return self.store.get_snapshot(snapshot_id)
        except ValueError:
            # Try as tag
            return self.store.get_snapshot_by_tag(snapshot_ref)

    def restore_snapshot(
        self,
        snapshot_ref: str,
        target_dir: Optional[Path] = None,
        force: bool = False
    ) -> bool:
        """
        Restore a snapshot

        Args:
            snapshot_ref: Snapshot ID or tag
            target_dir: Where to restore (default: project root)
            force: Overwrite existing files

        Returns:
            True if successful
        """
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot or not snapshot.metadata.id:
            return False

        if target_dir is None:
            target_dir = self.config.project_path

        return self.store.restore_snapshot(
            snapshot_id=snapshot.metadata.id,
            target_dir=target_dir,
            force=force
        )

    def delete_snapshot(self, snapshot_ref: str) -> bool:
        """Delete a snapshot"""
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot or not snapshot.metadata.id:
            return False

        self.store.delete_snapshot(snapshot.metadata.id)
        return True

    def diff_snapshots(
        self,
        from_ref: str,
        to_ref: str = "current"
    ) -> SnapshotDiff:
        """
        Compare two snapshots

        Args:
            from_ref: Source snapshot (ID or tag)
            to_ref: Target snapshot (ID, tag, or 'current')

        Returns:
            Diff between snapshots
        """
        # Get source snapshot
        from_snapshot = self.get_snapshot(from_ref)
        if not from_snapshot:
            raise ValueError(f"Snapshot '{from_ref}' not found")

        # Get target snapshot or current state
        if to_ref == "current":
            # Scan current state
            current_files = self.scanner.scan()
            to_files = {f.path: f for f in current_files}
            to_id = 0  # Special ID for current
        else:
            to_snapshot = self.get_snapshot(to_ref)
            if not to_snapshot:
                raise ValueError(f"Snapshot '{to_ref}' not found")
            to_files = {f.path: f for f in to_snapshot.files}
            to_id = to_snapshot.metadata.id or 0

        from_files = {f.path: f for f in from_snapshot.files}

        # Calculate diff
        diff = SnapshotDiff(
            from_snapshot=from_snapshot.metadata.id or 0,
            to_snapshot=to_id
        )

        # Find added files
        diff.files_added = [
            path for path in to_files.keys()
            if path not in from_files
        ]

        # Find removed files
        diff.files_removed = [
            path for path in from_files.keys()
            if path not in to_files
        ]

        # Find modified files
        for path in from_files.keys():
            if path in to_files:
                if from_files[path].hash != to_files[path].hash:
                    diff.files_modified.append(
                        DiffEntry(
                            file_path=path,
                            status='modified',
                            old_hash=from_files[path].hash,
                            new_hash=to_files[path].hash
                        )
                    )

        diff.total_changes = (
            len(diff.files_added) +
            len(diff.files_removed) +
            len(diff.files_modified)
        )

        # Calculate significance score
        total_files = max(len(from_files), len(to_files), 1)
        diff.significance_score = diff.total_changes / total_files

        return diff

    def cleanup_old_autosaves(self, max_keep: int = 50) -> int:
        """Clean up old autosaves"""
        return self.store.cleanup_old_autosaves(max_keep)
