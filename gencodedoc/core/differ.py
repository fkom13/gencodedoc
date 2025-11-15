"""Diff generation in multiple formats"""
import difflib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from ..models.snapshot import SnapshotDiff, DiffEntry
from ..models.config import DiffFormatConfig
from ..storage.snapshot_store import SnapshotStore


class DiffGenerator:
    """Generate diffs in various formats"""

    def __init__(self, config: DiffFormatConfig, store: SnapshotStore):
        self.config = config
        self.store = store

    def generate_diff(
        self,
        snapshot_diff: SnapshotDiff,
        format: Optional[str] = None
    ) -> str:
        """
        Generate diff in specified format

        Args:
            snapshot_diff: Diff between snapshots
            format: Output format (unified, json, ast)

        Returns:
            Formatted diff string
        """
        format = format or self.config.default

        if format == 'unified':
            return self._generate_unified(snapshot_diff)
        elif format == 'json':
            return self._generate_json(snapshot_diff)
        elif format == 'ast':
            return self._generate_ast(snapshot_diff)
        else:
            raise ValueError(f"Unknown diff format: {format}")

    def _generate_unified(self, diff: SnapshotDiff) -> str:
        """Generate unified diff format (like git diff)"""
        lines = []

        # Header
        lines.append(f"Diff from snapshot {diff.from_snapshot} to {diff.to_snapshot}")
        lines.append(f"Total changes: {diff.total_changes}")
        lines.append(f"Significance: {diff.significance_score:.2%}\n")

        # Added files
        if diff.files_added:
            lines.append(f"=== Added files ({len(diff.files_added)}) ===")
            for path in diff.files_added:
                lines.append(f"+ {path}")
            lines.append("")

        # Removed files
        if diff.files_removed:
            lines.append(f"=== Removed files ({len(diff.files_removed)}) ===")
            for path in diff.files_removed:
                lines.append(f"- {path}")
            lines.append("")

        # Modified files
        if diff.files_modified:
            lines.append(f"=== Modified files ({len(diff.files_modified)}) ===")
            for entry in diff.files_modified:
                lines.append(f"\n--- {entry.file_path}")

                # Get file contents
                old_content = self._get_file_content(entry.old_hash)
                new_content = self._get_file_content(entry.new_hash)

                if old_content and new_content:
                    # Generate unified diff
                    unified = difflib.unified_diff(
                        old_content.splitlines(keepends=True),
                        new_content.splitlines(keepends=True),
                        fromfile=f"a/{entry.file_path}",
                        tofile=f"b/{entry.file_path}",
                        lineterm='',
                        n=self.config.unified_context
                    )
                    lines.extend(unified)
                else:
                    lines.append("(Binary file or content not available)")

        return '\n'.join(lines)

    def _generate_json(self, diff: SnapshotDiff) -> str:
        """Generate JSON diff format"""
        result = {
            "from_snapshot": diff.from_snapshot,
            "to_snapshot": diff.to_snapshot,
            "total_changes": diff.total_changes,
            "significance_score": diff.significance_score,
            "changes": {
                "added": diff.files_added,
                "removed": diff.files_removed,
                "modified": []
            }
        }

        # Add modified files details
        for entry in diff.files_modified:
            mod_entry = {
                "file_path": entry.file_path,
                "status": entry.status,
                "old_hash": entry.old_hash,
                "new_hash": entry.new_hash
            }

            if self.config.json_include_content:
                old_content = self._get_file_content(entry.old_hash)
                new_content = self._get_file_content(entry.new_hash)

                if old_content and new_content:
                    mod_entry["old_content"] = old_content
                    mod_entry["new_content"] = new_content

            result["changes"]["modified"].append(mod_entry)

        return json.dumps(result, indent=2)

    def _generate_ast(self, diff: SnapshotDiff) -> str:
        """
        Generate AST-based semantic diff

        Note: This is a placeholder. Full AST diff would require
        language-specific parsers (tree-sitter, etc.)
        """
        lines = [
            "=== AST-based Semantic Diff ===",
            "(AST diff requires language-specific parsers)",
            "",
            "Summary:",
            f"  Files added: {len(diff.files_added)}",
            f"  Files removed: {len(diff.files_removed)}",
            f"  Files modified: {len(diff.files_modified)}",
            ""
        ]

        # For now, fall back to unified diff
        lines.append("Falling back to unified diff:")
        lines.append("")
        lines.append(self._generate_unified(diff))

        return '\n'.join(lines)

    def _get_file_content(self, file_hash: Optional[str]) -> Optional[str]:
        """Get file content from storage"""
        if not file_hash:
            return None

        try:
            compressed = self.store.db.get_content(file_hash)
            if not compressed:
                return None

            decompressed = self.store.compressor.decompress(compressed)
            return decompressed.decode('utf-8', errors='replace')
        except Exception:
            return None
