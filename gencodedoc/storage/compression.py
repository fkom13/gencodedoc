"""Compression utilities using zstandard"""
import zstandard as zstd
from typing import Tuple

class Compressor:
    """File content compression"""

    def __init__(self, level: int = 3):
        """
        Initialize compressor

        Args:
            level: Compression level (1-22, default 3)
        """
        self.level = max(1, min(22, level))
        self._compressor = zstd.ZstdCompressor(level=self.level)
        self._decompressor = zstd.ZstdDecompressor()

    def compress(self, data: bytes) -> Tuple[bytes, int, int]:
        """
        Compress data

        Returns:
            (compressed_data, original_size, compressed_size)
        """
        original_size = len(data)
        compressed = self._compressor.compress(data)
        compressed_size = len(compressed)

        return compressed, original_size, compressed_size

    def decompress(self, data: bytes) -> bytes:
        """Decompress data"""
        return self._decompressor.decompress(data)

    def compress_file(self, file_path: str) -> Tuple[bytes, int, int]:
        """
        Compress file content

        Returns:
            (compressed_data, original_size, compressed_size)
        """
        with open(file_path, 'rb') as f:
            data = f.read()
        return self.compress(data)
