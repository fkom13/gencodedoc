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

    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get the history of a specific file across all snapshots.
        
        Returns a list of entries with snapshot info and whether the file changed.
        """
        # list_snapshots returns List[SnapshotMetadata] objects
        snapshots = self.store.list_snapshots(include_autosave=True)
        history = []
        prev_hash = None

        # Sort snapshots by ID to ensure chronological order
        snapshots.sort(key=lambda s: s.id)

        for snap in snapshots:
            snapshot = self.store.get_snapshot(snap.id)
            if not snapshot:
                continue

            file_entry = snapshot.get_file(file_path)
            if file_entry:
                current_hash = file_entry.hash
                changed = prev_hash is not None and current_hash != prev_hash
                first_seen = prev_hash is None

                history.append({
                    'snapshot_id': snap.id,
                    'tag': snap.tag or '',
                    'date': snap.created_at.isoformat() if hasattr(snap.created_at, 'isoformat') else str(snap.created_at),
                    'message': snap.message or '',
                    'hash': current_hash,
                    'size': file_entry.size,
                    'changed': changed,
                    'first_seen': first_seen
                })
                prev_hash = current_hash
            else:
                if prev_hash is not None:
                    # File existed before but was removed in this snapshot
                    history.append({
                        'snapshot_id': snap.id,
                        'tag': snap.tag or '',
                        'date': snap.created_at.isoformat() if hasattr(snap.created_at, 'isoformat') else str(snap.created_at),
                        'message': snap.message or '',
                        'hash': None,
                        'size': 0,
                        'changed': True,
                        'removed': True
                    })
                    prev_hash = None

        return history

    def search_in_snapshots(
        self,
        query: str,
        file_filter: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for text content across snapshots.
        
        Args:
            query: Text to search for
            file_filter: Optional glob pattern to filter files
            snapshot_ref: Optional snapshot to search in (default: all)
            case_sensitive: Case-sensitive search
        """
        import fnmatch
        results = []
        search_query = query if case_sensitive else query.lower()

        if snapshot_ref:
            # Resolve single snapshot
            snap = self.get_snapshot(snapshot_ref)
            if not snap:
                return []
            snapshots_to_search = [snap.metadata]
        else:
            snapshots_to_search = self.store.list_snapshots(include_autosave=False)

        seen_hashes = set()  # Avoid searching same content twice

        for snap_meta in snapshots_to_search:
            snapshot = self.store.get_snapshot(snap_meta.id)
            if not snapshot:
                continue

            for file_entry in snapshot.files:
                # Apply file filter
                if file_filter and not fnmatch.fnmatch(file_entry.path, file_filter):
                    continue

                # Skip already-searched content
                if file_entry.hash in seen_hashes:
                    continue
                seen_hashes.add(file_entry.hash)

                try:
                    # Get content directly
                    compressed = self.store.db.get_content(file_entry.hash)
                    if not compressed:
                        continue
                    content = self.store.compressor.decompress(compressed).decode('utf-8', errors='replace')
                    search_content = content if case_sensitive else content.lower()

                    if search_query in search_content:
                        # Find matching lines
                        matches = []
                        for i, line in enumerate(content.splitlines(), 1):
                            line_search = line if case_sensitive else line.lower()
                            if search_query in line_search:
                                matches.append({'line': i, 'content': line.strip()})
                                if len(matches) >= 5:  # Cap at 5 matches per file
                                    break

                        results.append({
                            'snapshot_id': snap_meta.id,
                            'tag': snap_meta.tag or '',
                            'file_path': file_entry.path,
                            'matches': matches,
                            'total_matches': sum(
                                1 for l in content.splitlines()
                                if search_query in (l if case_sensitive else l.lower())
                            )
                        })
                except Exception:
                    continue

                if len(results) >= 50:  # Cap total results
                    return results

        return results

    def generate_changelog(
        self,
        from_ref: str,
        to_ref: Optional[str] = None
    ) -> str:
        """
        Generate a Keep-a-Changelog formatted changelog between two snapshots.
        
        Args:
            from_ref: Source snapshot ID or tag
            to_ref: Target snapshot ID or tag (default: latest)
        """
        diff = self.diff_snapshots(from_ref, to_ref or 'current')

        # Get snapshot info for header
        from_snap = self.get_snapshot(from_ref)
        from_meta = from_snap.metadata if from_snap else None
        
        if to_ref and to_ref != 'current':
            to_snap = self.get_snapshot(to_ref)
            to_meta = to_snap.metadata if to_snap else None
            
            to_label = to_meta.tag if to_meta and to_meta.tag else f"Snapshot #{to_meta.id if to_meta else '?'}"
            to_date = to_meta.created_at.strftime("%Y-%m-%d") if to_meta else ""
        else:
            to_label = "current"
            to_date = datetime.now().strftime("%Y-%m-%d")

        from_label = from_meta.tag if from_meta and from_meta.tag else f"Snapshot #{from_meta.id if from_meta else from_ref}"

        lines = []
        lines.append(f"## [{to_label}] - {to_date}")
        lines.append(f"*Compared to {from_label}*")
        lines.append("")

        if diff.files_added:
            lines.append("### Added")
            for path in sorted(diff.files_added):
                lines.append(f"- `{path}`")
            lines.append("")

        if diff.files_modified:
            lines.append("### Changed")
            for entry in sorted(diff.files_modified, key=lambda e: e.file_path):
                lines.append(f"- `{entry.file_path}`")
            lines.append("")

        if diff.files_removed:
            lines.append("### Removed")
            for path in sorted(diff.files_removed):
                lines.append(f"- ~~`{path}`~~")
            lines.append("")

        # Summary line
        total = diff.total_changes
        lines.append(f"---")
        lines.append(f"*{len(diff.files_added)} added, {len(diff.files_modified)} changed, {len(diff.files_removed)} removed ({total} total changes, {diff.significance_score:.0%} significance)*")

        return "\n".join(lines)
