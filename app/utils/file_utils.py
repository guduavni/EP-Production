"""
File Upload and Management Utilities

This module provides utilities for handling file uploads, storage, and management.
"""
import os
import uuid
import magic
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app, request, abort
from werkzeug.datastructures import FileStorage
from typing import Tuple, Optional, Dict, Any

# Allowed file extensions for different file types
ALLOWED_EXTENSIONS = {
    'audio': {'mp3', 'wav', 'ogg', 'm4a', 'flac'},
    'image': {'jpg', 'jpeg', 'png', 'gif', 'webp'},
    'document': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
    'video': {'mp4', 'webm', 'mov', 'avi'}
}

# Maximum file sizes in bytes (default: 50MB for audio, 10MB for images, 20MB for documents, 100MB for videos)
MAX_FILE_SIZES = {
    'audio': 50 * 1024 * 1024,      # 50MB
    'image': 10 * 1024 * 1024,      # 10MB
    'document': 20 * 1024 * 1024,   # 20MB
    'video': 100 * 1024 * 1024      # 100MB
}

def get_upload_folder(subfolder: str = '') -> Path:
    """
    Get the absolute path to the upload folder.
    
    Args:
        subfolder: Optional subfolder within the uploads directory
        
    Returns:
        Path: Absolute path to the upload folder
    """
    upload_folder = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
    
    # Create the full path
    if subfolder:
        upload_folder = upload_folder / subfolder
    
    # Create the directory if it doesn't exist
    upload_folder.mkdir(parents=True, exist_ok=True)
    
    return upload_folder

def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename in lowercase.
    
    Args:
        filename: The name of the file
        
    Returns:
        str: The file extension in lowercase, or an empty string if no extension
    """
    return Path(filename).suffix.lower().lstrip('.')

def is_allowed_file(filename: str, file_type: str) -> bool:
    """
    Check if the file extension is allowed for the given file type.
    
    Args:
        filename: The name of the file
        file_type: The type of file ('audio', 'image', 'document', 'video')
        
    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    if file_type not in ALLOWED_EXTENSIONS:
        return False
        
    ext = get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS[file_type]

def validate_file(file_storage: FileStorage, file_type: str) -> Tuple[bool, str]:
    """
    Validate a file based on its extension and content type.
    
    Args:
        file_storage: The file storage object from Flask
        file_type: The expected file type ('audio', 'image', 'document', 'video')
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if file_storage is None or not file_storage.filename:
        return False, "No file selected"
    
    filename = secure_filename(file_storage.filename)
    
    # Check file extension
    if not is_allowed_file(filename, file_type):
        allowed_exts = ', '.join(ALLOWED_EXTENSIONS[file_type])
        return False, f"Invalid file type. Allowed types: {allowed_exts}"
    
    # Check file size
    max_size = MAX_FILE_SIZES.get(file_type, 10 * 1024 * 1024)  # Default to 10MB
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)  # Reset file pointer
    
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        return False, f"File is too large. Maximum size: {max_size_mb:.1f}MB"
    
    # Verify MIME type
    try:
        mime = magic.Magic(mime=True)
        file_storage.seek(0)
        mime_type = mime.from_buffer(file_storage.read(1024))
        file_storage.seek(0)  # Reset file pointer
        
        expected_mime_prefix = file_type + '/'
        if not mime_type.startswith(expected_mime_prefix):
            return False, f"Invalid file type. Expected {file_type} file"
            
    except Exception as e:
        current_app.logger.error(f"Error validating file MIME type: {e}")
        return False, "Error validating file type"
    
    return True, ""

def generate_unique_filename(filename: str) -> str:
    """
    Generate a unique filename to prevent overwriting existing files.
    
    Args:
        filename: The original filename
        
    Returns:
        str: A unique filename with a timestamp and random string
    """
    ext = get_file_extension(filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    random_str = str(uuid.uuid4().hex[:8])
    
    if ext:
        return f"{timestamp}_{random_str}.{ext}"
    return f"{timestamp}_{random_str}"

def save_uploaded_file(file_storage: FileStorage, subfolder: str = '', filename: str = None) -> Tuple[Optional[str], str]:
    """
    Save an uploaded file to the filesystem.
    
    Args:
        file_storage: The file storage object from Flask
        subfolder: Optional subfolder within the uploads directory
        filename: Optional custom filename (without path)
        
    Returns:
        tuple: (saved_file_path, error_message)
    """
    if file_storage is None or not file_storage.filename:
        return None, "No file provided"
    
    # Get the upload folder and ensure it exists
    upload_folder = get_upload_folder(subfolder)
    
    # Generate a secure filename if not provided
    if not filename:
        original_filename = secure_filename(file_storage.filename)
        filename = generate_unique_filename(original_filename)
    else:
        filename = secure_filename(filename)
    
    # Ensure the filename is unique
    file_path = upload_folder / filename
    counter = 1
    base_name, ext = os.path.splitext(filename)
    
    while file_path.exists():
        filename = f"{base_name}_{counter}{ext}"
        file_path = upload_folder / filename
        counter += 1
    
    try:
        # Save the file
        file_storage.save(str(file_path))
        return str(file_path.relative_to(current_app.root_path)), ""
    except Exception as e:
        current_app.logger.error(f"Error saving file: {e}")
        return None, f"Error saving file: {str(e)}"

def delete_file(file_path: str) -> Tuple[bool, str]:
    """
    Delete a file from the filesystem.
    
    Args:
        file_path: The path to the file to delete (relative to the app root)
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        abs_path = Path(current_app.root_path) / file_path
        
        # Prevent directory traversal
        if not abs_path.resolve().is_relative_to(Path(current_app.root_path)):
            return False, "Invalid file path"
            
        if abs_path.exists() and abs_path.is_file():
            abs_path.unlink()
            return True, ""
        return False, "File not found"
    except Exception as e:
        current_app.logger.error(f"Error deleting file {file_path}: {e}")
        return False, f"Error deleting file: {str(e)}"

def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a file.
    
    Args:
        file_path: The path to the file (relative to the app root)
        
    Returns:
        dict: File information or None if the file doesn't exist
    """
    try:
        abs_path = Path(current_app.root_path) / file_path
        
        # Prevent directory traversal
        if not abs_path.resolve().is_relative_to(Path(current_app.root_path)):
            return None
            
        if not abs_path.exists() or not abs_path.is_file():
            return None
            
        stats = abs_path.stat()
        
        return {
            'filename': abs_path.name,
            'path': str(abs_path.relative_to(current_app.root_path)),
            'size': stats.st_size,
            'size_human_readable': human_readable_size(stats.st_size),
            'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'mime_type': get_mime_type(abs_path)
        }
    except Exception as e:
        current_app.logger.error(f"Error getting file info for {file_path}: {e}")
        return None

def get_mime_type(file_path: Path) -> str:
    """
    Get the MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: The MIME type or 'application/octet-stream' if unknown
    """
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(str(file_path))
    except Exception as e:
        current_app.logger.error(f"Error getting MIME type for {file_path}: {e}")
        return 'application/octet-stream'

def human_readable_size(size_bytes: int) -> str:
    """
    Convert a file size in bytes to a human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        str: Human-readable file size (e.g., "1.5 MB")
    """
    if not isinstance(size_bytes, (int, float)) or size_bytes < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit = 0
    
    while size >= 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1
    
    return f"{size:.1f} {units[unit]}"

def get_audio_duration(file_path: str) -> Optional[float]:
    """
    Get the duration of an audio file in seconds.
    
    Args:
        file_path: Path to the audio file (relative to the app root)
        
    Returns:
        float: Duration in seconds, or None if an error occurs
    """
    try:
        import wave
        import contextlib
        
        abs_path = Path(current_app.root_path) / file_path
        
        # Prevent directory traversal
        if not abs_path.resolve().is_relative_to(Path(current_app.root_path)):
            return None
            
        if not abs_path.exists() or not abs_path.is_file():
            return None
            
        # Try to get duration using wave module (works for WAV files)
        try:
            with contextlib.closing(wave.open(str(abs_path), 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                return frames / float(rate)
        except:
            # Fall back to other methods for non-WAV files
            try:
                import mutagen
                audio = mutagen.File(str(abs_path))
                if audio is not None and hasattr(audio.info, 'length'):
                    return audio.info.length
            except:
                pass
                
        return None
    except Exception as e:
        current_app.logger.error(f"Error getting audio duration for {file_path}: {e}")
        return None
