"""Tests for writer components."""

import tempfile
from pathlib import Path

import pytest

from scruby.writers import (
    Writer,
    WriterError,
    TextFileWriter,
    StdoutWriter,
    writer_registry,
    get_writer_registry,
)


class TestWriterBaseClass:
    """Tests for the abstract Writer base class."""

    def test_writer_is_abstract(self):
        """Verify Writer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Writer()

    def test_writer_requires_write_method(self):
        """Verify subclass must implement write() method."""

        class IncompleteWriter(Writer):
            pass

        with pytest.raises(TypeError):
            IncompleteWriter()


class TestWriterRegistry:
    """Tests for the writer registry."""

    def test_writer_registry_exists(self):
        """Verify registry is available."""
        assert writer_registry is not None
        assert writer_registry._component_type == "writer"

    def test_get_writer_registry(self):
        """Verify get_writer_registry function works."""
        registry = get_writer_registry()
        assert registry is writer_registry

    def test_text_file_writer_registered(self):
        """Verify TextFileWriter is auto-registered."""
        assert writer_registry.is_registered("text_file")

    def test_stdout_writer_registered(self):
        """Verify StdoutWriter is auto-registered."""
        assert writer_registry.is_registered("stdout")

    def test_create_writer_from_registry(self):
        """Create writer via factory."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            writer = writer_registry.create("text_file", path=temp_path)
            assert isinstance(writer, TextFileWriter)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestTextFileWriterSingleFile:
    """Tests for TextFileWriter with single files."""

    def test_write_single_file(self):
        """Write document to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            writer = TextFileWriter(temp_path)
            document = {"content": "Test content"}

            writer.write(document)

            # Verify file was created
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_write_single_file_content(self):
        """Verify written content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            writer = TextFileWriter(temp_path)
            document = {"content": "Test content line 1\nTest content line 2"}

            writer.write(document)

            # Read and verify content
            content = Path(temp_path).read_text()
            assert content == "Test content line 1\nTest content line 2"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_write_creates_directory(self):
        """Verify parent dirs created if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "output.txt"

            writer = TextFileWriter(output_path)
            document = {"content": "Test content"}

            writer.write(document)

            # Verify file and directory exist
            assert output_path.exists()
            assert output_path.parent.exists()

    def test_write_overwrites_existing(self):
        """Verify file is overwritten."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Original content")
            temp_path = f.name

        try:
            writer = TextFileWriter(temp_path)
            document = {"content": "New content"}

            writer.write(document)

            # Verify new content
            content = Path(temp_path).read_text()
            assert content == "New content"
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestTextFileWriterDirectory:
    """Tests for TextFileWriter with directories."""

    def test_write_to_directory(self):
        """Write multiple documents to folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = TextFileWriter(tmpdir)

            doc1 = {"content": "Content 1", "metadata": {"filename": "file1.txt"}}
            doc2 = {"content": "Content 2", "metadata": {"filename": "file2.txt"}}

            writer.write(doc1)
            writer.write(doc2)

            # Verify both files exist
            assert (Path(tmpdir) / "file1.txt").exists()
            assert (Path(tmpdir) / "file2.txt").exists()

    def test_write_to_directory_uses_metadata_filename(self):
        """Verify filename from metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = TextFileWriter(tmpdir)

            document = {
                "content": "Test content",
                "metadata": {"filename": "custom_name.txt"},
            }

            writer.write(document)

            # Verify file created with correct name
            output_file = Path(tmpdir) / "custom_name.txt"
            assert output_file.exists()
            assert output_file.read_text() == "Test content"

    def test_write_to_directory_missing_filename(self):
        """Error if no filename in metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = TextFileWriter(tmpdir)

            document = {"content": "Test content", "metadata": {}}

            with pytest.raises(WriterError) as exc_info:
                writer.write(document)

            assert "filename" in str(exc_info.value).lower()

    def test_write_creates_output_directory(self):
        """Create directory if doesn't exist (when path ends with /)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pass as string with trailing slash to trigger directory mode
            output_dir_path = Path(tmpdir) / "new_output_dir"
            output_dir_str = str(output_dir_path) + "/"

            writer = TextFileWriter(output_dir_str)

            document = {"content": "Test", "metadata": {"filename": "test.txt"}}

            writer.write(document)

            # Verify directory and file created (without trailing slash in Path)
            assert output_dir_path.exists()
            assert (output_dir_path / "test.txt").exists()


class TestStdoutWriter:
    """Tests for StdoutWriter."""

    def test_write_to_stdout(self, capsys):
        """Write to stdout."""
        writer = StdoutWriter()
        document = {"content": "Test content"}

        writer.write(document)

        captured = capsys.readouterr()
        assert "Test content" in captured.out

    def test_write_to_stdout_with_metadata(self, capsys):
        """Display metadata when enabled."""
        writer = StdoutWriter(show_metadata=True)
        document = {"content": "Test content", "metadata": {"filename": "test.txt"}}

        writer.write(document)

        captured = capsys.readouterr()
        assert "Metadata" in captured.out
        assert "test.txt" in captured.out
        assert "Test content" in captured.out

    def test_write_to_stdout_without_metadata_display(self, capsys):
        """Don't display metadata when disabled."""
        writer = StdoutWriter(show_metadata=False)
        document = {"content": "Test content", "metadata": {"filename": "test.txt"}}

        writer.write(document)

        captured = capsys.readouterr()
        assert "Metadata" not in captured.out
        assert "Test content" in captured.out


class TestWriterErrorHandling:
    """Tests for error handling in writers."""

    def test_write_missing_content_key(self):
        """Handle document without content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = TextFileWriter(tmpdir)

            document = {"metadata": {"filename": "test.txt"}}

            with pytest.raises(WriterError) as exc_info:
                writer.write(document)

            assert "content" in str(exc_info.value).lower()

    def test_stdout_write_missing_content_key(self):
        """Handle document without content for stdout."""
        writer = StdoutWriter()

        document = {"metadata": {"filename": "test.txt"}}

        with pytest.raises(WriterError) as exc_info:
            writer.write(document)

        assert "content" in str(exc_info.value).lower()
