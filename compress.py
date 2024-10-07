#!/usr/bin/env python3

import os
import sys
import mimetypes
import subprocess
from multiprocessing import Pool

# Maximum file size in bytes (3.5 MB)
MAX_SIZE = 3.5 * 1024 * 1024

# Supported file extensions
EXTENSIONS = {
    'pdf': 'application/pdf',
    'gif': 'image/gif',
    'mp3': 'audio/mpeg',
    'mp4': 'video/mp4',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'bmp': 'image/bmp',
    'tiff': 'image/tiff',
    'tif': 'image/tiff'
}

def process_path(input_path):
    if os.path.isdir(input_path):
        # Process directory
        for root, dirs, files in os.walk(input_path):
            file_paths = [os.path.join(root, f) for f in files]
            # Use multiprocessing for performance
            with Pool() as pool:
                pool.map(process_file, file_paths)
    elif os.path.isfile(input_path):
        # Process single file
        process_file(input_path)
    else:
        print(f"Invalid input: {input_path}")

def process_file(file_path):
    # Get file extension
    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    if ext in EXTENSIONS:
        # Check file size
        size = os.path.getsize(file_path)
        if size > MAX_SIZE:
            print(f"Compressing '{file_path}' ({size / (1024 * 1024):.2f} MB)...")
            compress_file(file_path, ext)
    else:
        pass  # Unsupported file type

def compress_file(file_path, ext):
    temp_file = f"{file_path}.tmp"

    try:
        if ext == 'pdf':
            # Compress PDF using Ghostscript
            cmd = [
                'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH',
                f"-sOutputFile={temp_file}", file_path
            ]
        elif ext in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif'):
            # Compress image using Pillow
            from PIL import Image
            with Image.open(file_path) as img:
                img.save(temp_file, optimize=True, quality=70)
        elif ext == 'mp3':
            # Compress MP3 using FFmpeg
            cmd = [
                'ffmpeg', '-i', file_path, '-b:a', '128k', '-y', temp_file
            ]
        elif ext == 'mp4':
            # Compress MP4 using FFmpeg
            cmd = [
                'ffmpeg', '-i', file_path, '-vcodec', 'libx264', '-b:v', '1000k',
                '-acodec', 'aac', '-b:a', '128k', '-y', temp_file
            ]
        else:
            print(f"Unsupported file extension: {ext}")
            return

        # Execute compression command if cmd is defined
        if 'cmd' in locals():
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Check new file size
        if os.path.exists(temp_file):
            new_size = os.path.getsize(temp_file)
            if new_size <= MAX_SIZE:
                os.replace(temp_file, file_path)
                print(f"File '{file_path}' compressed to {new_size / (1024 * 1024):.2f} MB.")
            else:
                os.remove(temp_file)
                print(f"Compressed file '{file_path}' is still larger than 3.5 MB.")
        else:
            print(f"Compression failed for '{file_path}'.")
    except Exception as e:
        print(f"Error compressing '{file_path}': {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compress_media.py <file_or_directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    process_path(input_path)
