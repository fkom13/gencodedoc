"""Version management and snapshot operations"""
import tarfile
import io
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models.config import ProjectConfig
from ..models.snapshot import Snapshot, SnapshotDiff, DiffEntry
from ..storage.snapshot_store import SnapshotStore
from .scanner import FileScanner

logger = logging.getLogger(__name__)


class VersionManager:
    """Manages snapshots and versioning"""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.scanner = FileScanner(config)

        # Initialize storage
        storage_path = config.project_path / config.storage_path
        self.store = SnapshotStore(
            storage_path=storage_path,
            project_path=config.project_path,
            compression_level=config.compression_level,
            compression_enabled=config.compression_enabled
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

    # ────────────────────────────────────────────
    # File content viewing
    # ────────────────────────────────────────────

    def get_file_content_at_version(
        self,
        snapshot_ref: str,
        file_path: str
    ) -> Optional[str]:
        """
        Get the content of a specific file at a specific snapshot version

        Args:
            snapshot_ref: Snapshot ID or tag
            file_path: Relative path of the file

        Returns:
            File content as string, or None if not found
        """
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot:
            raise ValueError(f"Snapshot '{snapshot_ref}' not found")

        file_entry = snapshot.get_file(file_path)
        if not file_entry:
            raise ValueError(f"File '{file_path}' not found in snapshot '{snapshot_ref}'")

        content = self.store.get_file_content(file_entry.hash)
        if content is None:
            logger.warning(f"Content for hash {file_entry.hash} not found in store")
        return content

    def list_files_at_version(
        self,
        snapshot_ref: str,
        pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all files present in a specific snapshot version

        Args:
            snapshot_ref: Snapshot ID or tag
            pattern: Optional glob pattern to filter files

        Returns:
            List of file info dicts with path, size, hash
        """
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot:
            raise ValueError(f"Snapshot '{snapshot_ref}' not found")

        if pattern:
            files = snapshot.get_files_matching([pattern])
        else:
            files = snapshot.files

        return [
            {
                'path': f.path,
                'size': f.size,
                'hash': f.hash,
                'mode': f.mode
            }
            for f in sorted(files, key=lambda x: x.path)
        ]

    # ────────────────────────────────────────────
    # Restore operations
    # ────────────────────────────────────────────

    def restore_snapshot(
        self,
        snapshot_ref: str,
        target_dir: Optional[Path] = None,
        force: bool = False,
        file_filters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Restore a snapshot (full or partial)

        Args:
            snapshot_ref: Snapshot ID or tag
            target_dir: Where to restore (default: project root)
            force: Overwrite existing files
            file_filters: Optional list of glob patterns/paths to restore selectively

        Returns:
            Dict with restore details: restored_count, skipped_count, files_restored
        """
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot or not snapshot.metadata.id:
            raise ValueError(f"Snapshot '{snapshot_ref}' not found")

        if target_dir is None:
            target_dir = self.config.project_path

        # Determine which files to restore
        if file_filters:
            files_to_restore = snapshot.get_files_matching(file_filters)
        else:
            files_to_restore = snapshot.files

        restored = []
        skipped = []

        for file_entry in files_to_restore:
            target_path = target_dir / file_entry.path

            # Check if file exists
            if target_path.exists() and not force:
                skipped.append(file_entry.path)
                continue

            # Restore file
            if self.store.restore_file(file_entry.hash, target_path):
                target_path.chmod(file_entry.mode)
                restored.append(file_entry.path)
            else:
                logger.warning(f"Failed to restore {file_entry.path}")
                skipped.append(file_entry.path)

        return {
            'restored_count': len(restored),
            'skipped_count': len(skipped),
            'total_files': len(files_to_restore),
            'files_restored': restored,
            'files_skipped': skipped
        }

    # ────────────────────────────────────────────
    # Export operations
    # ────────────────────────────────────────────

    def export_snapshot(
        self,
        snapshot_ref: str,
        output_path: Path,
        archive: bool = False,
        file_filters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Export a snapshot to a folder or tar.gz archive

        Args:
            snapshot_ref: Snapshot ID or tag
            output_path: Target folder or archive path (.tar.gz)
            archive: If True, create a .tar.gz archive
            file_filters: Optional glob/path filters

        Returns:
            Dict with export details
        """
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot or not snapshot.metadata.id:
            raise ValueError(f"Snapshot '{snapshot_ref}' not found")

        # Determine which files to export
        if file_filters:
            files_to_export = snapshot.get_files_matching(file_filters)
        else:
            files_to_export = snapshot.files

        if archive:
            return self._export_as_archive(snapshot, files_to_export, output_path)
        else:
            return self._export_as_folder(snapshot, files_to_export, output_path)

    def _export_as_folder(
        self,
        snapshot: Snapshot,
        files: list,
        output_path: Path
    ) -> Dict[str, Any]:
        """Export snapshot files to a folder"""
        output_path.mkdir(parents=True, exist_ok=True)
        exported = []
        failed = []

        for file_entry in files:
            target = output_path / file_entry.path
            content_bytes = self.store.get_file_content_bytes(file_entry.hash)

            if content_bytes is not None:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content_bytes)
                target.chmod(file_entry.mode)
                exported.append(file_entry.path)
            else:
                failed.append(file_entry.path)

        tag = snapshot.metadata.tag or str(snapshot.metadata.id)
        return {
            'snapshot': tag,
            'format': 'folder',
            'output_path': str(output_path),
            'exported_count': len(exported),
            'failed_count': len(failed),
            'files_exported': exported,
            'files_failed': failed
        }

    def _export_as_archive(
        self,
        snapshot: Snapshot,
        files: list,
        output_path: Path
    ) -> Dict[str, Any]:
        """Export snapshot as tar.gz archive"""
        output_path = Path(str(output_path))
        if not str(output_path).endswith('.tar.gz'):
            output_path = output_path.with_suffix('.tar.gz')

        output_path.parent.mkdir(parents=True, exist_ok=True)
        exported = []
        failed = []

        with tarfile.open(str(output_path), 'w:gz') as tar:
            for file_entry in files:
                content_bytes = self.store.get_file_content_bytes(file_entry.hash)

                if content_bytes is not None:
                    info = tarfile.TarInfo(name=file_entry.path)
                    info.size = len(content_bytes)
                    info.mode = file_entry.mode
                    tar.addfile(info, io.BytesIO(content_bytes))
                    exported.append(file_entry.path)
                else:
                    failed.append(file_entry.path)

        tag = snapshot.metadata.tag or str(snapshot.metadata.id)
        return {
            'snapshot': tag,
            'format': 'tar.gz',
            'output_path': str(output_path),
            'exported_count': len(exported),
            'failed_count': len(failed),
            'archive_size': output_path.stat().st_size if output_path.exists() else 0,
            'files_exported': exported,
            'files_failed': failed
        }

    # ────────────────────────────────────────────
    # Diff & cleanup
    # ────────────────────────────────────────────

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
        to_ref: str = "current",
        file_filters: Optional[List[str]] = None
    ) -> SnapshotDiff:
        """
        Compare two snapshots

        Args:
            from_ref: Source snapshot (ID or tag)
            to_ref: Target snapshot (ID, tag, or 'current')
            file_filters: Optional list of glob patterns to filter diff results

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

        # Apply file filters if provided
        if file_filters:
            diff = diff.filter_by_paths(file_filters)

        return diff

    def cleanup_old_autosaves(self, max_keep: int = 50) -> int:
        """Clean up old autosaves"""
        return self.store.cleanup_old_autosaves(max_keep)

    def cleanup_expired_autosaves(self, delete_after_days: int) -> int:
        """Clean up expired autosaves"""
        return self.store.db.cleanup_expired_autosaves(delete_after_days)

    def cleanup_orphaned_contents(self) -> int:
        """Clean up orphaned file contents from the database"""
        return self.store.db.cleanup_orphaned_contents()
