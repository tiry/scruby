"""Tests for reader components."""

import pytest
from pathlib import Path

from scruby.readers import (
    Reader,
    ReaderError,
    TextFileReader,
    reader_registry,
    get_reader_registry,
)


class TestReaderBaseClass:
    """Tests for the abstract Reader base class."""

    def test_reader_is_abstract(self):
        """Verify Reader cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Reader()

    def test_reader_requires_read_method(self):
        """Verify subclass must implement read() method."""
        
        class IncompleteReader(Reader):
            pass

        with pytest.raises(TypeError):
            IncompleteReader()


class TestReaderRegistry:
    """Tests for the reader registry."""

    def test_reader_registry_exists(self):
        """Verify registry is available."""
        assert reader_registry is not None
        assert reader_registry._component_type == "reader"

    def test_get_reader_registry(self):
        """Verify get_reader_registry function works."""
        registry = get_reader_registry()
        assert registry is reader_registry

    def test_text_file_reader_registered(self):
        """Verify TextFileReader is auto-registered."""
        assert reader_registry.is_registered("text_file")

    def test_create_reader_from_registry(self):
        """Create reader via factory."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        sample_file = fixtures_dir / "sample1.txt"
        
        reader = reader_registry.create("text_file", path=str(sample_file))
        assert isinstance(reader, TextFileReader)


class TestTextFileReaderSingleFile:
    """Tests for TextFileReader with single files."""

    def test_read_single_file(self):
        """Read a single text file successfully."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        sample_file = fixtures_dir / "sample1.txt"
        
        reader = TextFileReader(sample_file)
        docs = list(reader.read())
        
        assert len(docs) == 1
        assert "content" in docs[0]
        assert "metadata" in docs[0]

    def test_read_single_file_content(self):
        """Verify content is correct."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        sample_file = fixtures_dir / "sample1.txt"
        
        reader = TextFileReader(sample_file)
        docs = list(reader.read())
        
        assert "This is a sample text file for testing" in docs[0]["content"]
        assert "It contains multiple lines" in docs[0]["content"]

    def test_read_single_file_metadata(self):
        """Verify metadata includes filename and path."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        sample_file = fixtures_dir / "sample1.txt"
        
        reader = TextFileReader(sample_file)
        docs = list(reader.read())
        
        metadata = docs[0]["metadata"]
        assert metadata["filename"] == "sample1.txt"
        assert "sample1.txt" in metadata["path"]

    def test_read_nonexistent_file(self):
        """Handle missing file with ReaderError."""
        with pytest.raises(ReaderError) as exc_info:
            TextFileReader("nonexistent_file.txt")
        
        assert "Path not found" in str(exc_info.value)

    def test_read_file_with_string_path(self):
        """Test reading with string path instead of Path object."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        sample_file = str(fixtures_dir / "sample1.txt")
        
        reader = TextFileReader(sample_file)
        docs = list(reader.read())
        
        assert len(docs) == 1


class TestTextFileReaderDirectory:
    """Tests for TextFileReader with directories."""

    def test_read_directory(self):
        """Read all .txt files from directory."""
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_folder"
        
        reader = TextFileReader(fixtures_dir)
        docs = list(reader.read())
        
        assert len(docs) == 2

    def test_read_directory_multiple_files(self):
        """Verify all files are read."""
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_folder"
        
        reader = TextFileReader(fixtures_dir)
        docs = list(reader.read())
        
        filenames = [doc["metadata"]["filename"] for doc in docs]
        assert "file1.txt" in filenames
        assert "file2.txt" in filenames

    def test_read_directory_sorted(self):
        """Verify files read in sorted order."""
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_folder"
        
        reader = TextFileReader(fixtures_dir)
        docs = list(reader.read())
        
        filenames = [doc["metadata"]["filename"] for doc in docs]
        assert filenames == ["file1.txt", "file2.txt"]

    def test_read_directory_content(self):
        """Verify content of files from directory."""
        fixtures_dir = Path(__file__).parent / "fixtures" / "test_folder"
        
        reader = TextFileReader(fixtures_dir)
        docs = list(reader.read())
        
        contents = [doc["content"] for doc in docs]
        assert any("First file" in content for content in contents)
        assert any("Second file" in content for content in contents)

    def test_read_directory_no_txt_files(self):
        """Handle empty directory with ReaderError."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ReaderError) as exc_info:
                reader = TextFileReader(tmpdir)
                list(reader.read())
            
            assert "No .txt files found" in str(exc_info.value)

    def test_read_directory_only_txt(self):
        """Verify only .txt files are read (not .md, .py, etc.)."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create various file types
            (tmpdir_path / "file1.txt").write_text("Text file")
            (tmpdir_path / "file2.md").write_text("Markdown file")
            (tmpdir_path / "file3.py").write_text("Python file")
            
            reader = TextFileReader(tmpdir)
            docs = list(reader.read())
            
            # Should only read the .txt file
            assert len(docs) == 1
            assert docs[0]["metadata"]["filename"] == "file1.txt"


class TestTextFileReaderErrorHandling:
    """Tests for error handling in TextFileReader."""

    def test_read_corrupted_file(self):
        """Handle file read errors."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            # Create reader successfully
            reader = TextFileReader(temp_path)
            
            # Remove file to cause read error
            Path(temp_path).unlink()
            
            # Should raise ReaderError when trying to read
            with pytest.raises(ReaderError) as exc_info:
                list(reader.read())
            
            # Error message should indicate the path issue
            assert "Path is neither file nor directory" in str(exc_info.value)
        finally:
            # Cleanup if file still exists
            if Path(temp_path).exists():
                Path(temp_path).unlink()

    def test_different_encoding(self):
        """Test reading with different encoding."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        sample_file = fixtures_dir / "sample1.txt"
        
        # Should work with utf-8 (default)
        reader = TextFileReader(sample_file, encoding="utf-8")
        docs = list(reader.read())
        assert len(docs) == 1
