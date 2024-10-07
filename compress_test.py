import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the functions from the compression script
from compress_media import process_file, compress_file, MAX_SIZE

class TestCompressMedia(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Supported extensions
        self.supported_files = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'mp3': 'audio/mpeg',
            'mp4': 'video/mp4',
        }

        # Create test files
        self.test_files = {}
        for ext, mime in self.supported_files.items():
            file_path = os.path.join(self.test_dir, f'test_large.{ext}')
            with open(file_path, 'wb') as f:
                f.seek(int(MAX_SIZE) + 1)  # Create file larger than MAX_SIZE
                f.write(b'\0')
            self.test_files[ext] = file_path

        # Create an unsupported file
        self.unsupported_file = os.path.join(self.test_dir, 'test.txt')
        with open(self.unsupported_file, 'w') as f:
            f.write('This is a test.')

    def tearDown(self):
        # Remove temporary directory and files
        shutil.rmtree(self.test_dir)

    @patch('compress_media.compress_file')
    def test_process_file_supported_large(self, mock_compress_file):
        """Test that process_file calls compress_file for supported large files."""
        for ext, file_path in self.test_files.items():
            with self.subTest(ext=ext):
                process_file(file_path)
                mock_compress_file.assert_called_with(file_path, ext)
                mock_compress_file.reset_mock()

    @patch('compress_media.compress_file')
    def test_process_file_supported_small(self, mock_compress_file):
        """Test that process_file does not call compress_file for small files."""
        for ext in self.supported_files.keys():
            file_path = os.path.join(self.test_dir, f'test_small.{ext}')
            with open(file_path, 'wb') as f:
                f.seek(int(MAX_SIZE) - 1)  # Create file smaller than MAX_SIZE
                f.write(b'\0')
            process_file(file_path)
            mock_compress_file.assert_not_called()
            mock_compress_file.reset_mock()

    def test_process_file_unsupported(self):
        """Test that process_file does nothing for unsupported files."""
        process_file(self.unsupported_file)
        # Since compress_file is not called, nothing to assert
        # We can check that no exceptions are raised

    @patch('compress_media.subprocess.run')
    def test_compress_file_pdf(self, mock_subprocess_run):
        """Test compress_file function for PDF files."""
        file_path = self.test_files['pdf']
        compress_file(file_path, 'pdf')
        mock_subprocess_run.assert_called_once()
        args = mock_subprocess_run.call_args[0][0]
        self.assertIn('gs', args[0])

    @patch('compress_media.subprocess.run')
    def test_compress_file_mp3(self, mock_subprocess_run):
        """Test compress_file function for MP3 files."""
        file_path = self.test_files['mp3']
        compress_file(file_path, 'mp3')
        mock_subprocess_run.assert_called_once()
        args = mock_subprocess_run.call_args[0][0]
        self.assertIn('ffmpeg', args[0])
        self.assertIn('-b:a', args)

    @patch('compress_media.subprocess.run')
    def test_compress_file_mp4(self, mock_subprocess_run):
        """Test compress_file function for MP4 files."""
        file_path = self.test_files['mp4']
        compress_file(file_path, 'mp4')
        mock_subprocess_run.assert_called_once()
        args = mock_subprocess_run.call_args[0][0]
        self.assertIn('ffmpeg', args[0])
        self.assertIn('-vcodec', args)

    @patch('compress_media.Image.open')
    def test_compress_file_image(self, mock_image_open):
        """Test compress_file function for image files."""
        file_path = self.test_files['jpg']
        mock_image = MagicMock()
        mock_image_open.return_value.__enter__.return_value = mock_image
        compress_file(file_path, 'jpg')
        mock_image.save.assert_called_once()

    @patch('os.path.getsize')
    def test_compress_file_size_check(self, mock_getsize):
        """Test that compress_file replaces the file if size is acceptable."""
        file_path = self.test_files['pdf']
        temp_file = f"{file_path}.tmp"

        # Mock sizes
        mock_getsize.side_effect = [int(MAX_SIZE) + 1000, int(MAX_SIZE) - 1000]

        with patch('compress_media.os.replace') as mock_replace:
            compress_file(file_path, 'pdf')
            mock_replace.assert_called_with(temp_file, file_path)

    @patch('os.path.getsize')
    def test_compress_file_size_exceeds(self, mock_getsize):
        """Test that compress_file removes temp file if size exceeds MAX_SIZE."""
        file_path = self.test_files['pdf']
        temp_file = f"{file_path}.tmp"

        # Mock sizes
        mock_getsize.side_effect = [int(MAX_SIZE) + 1000, int(MAX_SIZE) + 2000]

        with patch('compress_media.os.remove') as mock_remove:
            compress_file(file_path, 'pdf')
            mock_remove.assert_called_with(temp_file)

    def test_error_handling(self):
        """Test that compress_file handles exceptions properly."""
        file_path = self.test_files['pdf']
        with patch('compress_media.subprocess.run', side_effect=Exception('Test Exception')):
            compress_file(file_path, 'pdf')
            # Expect the function to handle the exception and continue

if __name__ == '__main__':
    unittest.main()
