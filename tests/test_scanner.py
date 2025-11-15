"""Tests for file scanner"""
import pytest
from pathlib import Path
from gencodedoc.core.scanner import FileScanner
from gencodedoc.models.config import ProjectConfig


def test_scanner_initialization():
    """Test scanner initialization"""
    config = ProjectConfig(project_path=Path.cwd())
    scanner = FileScanner(config)

    assert scanner.config == config
    assert scanner.filter is not None


def test_file_hash_calculation(tmp_path):
    """Test file hash calculation"""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    hash_result = FileScanner._calculate_file_hash(test_file)

    # SHA256 of "Hello, World!"
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert hash_result == expected


def test_scan_directory(tmp_path):
    """Test directory scanning"""
    # Create test structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
    (tmp_path / "README.md").write_text("# Test")

    config = ProjectConfig(project_path=tmp_path)
    scanner = FileScanner(config)

    files = scanner.scan()

    assert len(files) >= 3  # At least our test files


def test_binary_detection(tmp_path):
    """Test binary file detection"""
    # Create text file
    text_file = tmp_path / "text.txt"
    text_file.write_text("Hello")

    # Create binary file
    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(b'\x00\x01\x02\x03')

    from gencodedoc.utils.filters import BinaryDetector

    assert not BinaryDetector.is_binary(text_file)
    assert BinaryDetector.is_binary(binary_file)
