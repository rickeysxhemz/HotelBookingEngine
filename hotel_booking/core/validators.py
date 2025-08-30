"""
Security validators for file uploads and other security-sensitive operations
"""
import os
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_file_extension(value):
    """Validate file extension for uploads"""
    allowed_extensions = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.gif'])
    ext = os.path.splitext(value.name)[1].lower()
    
    if ext not in allowed_extensions:
        raise ValidationError(
            f'File extension {ext} is not allowed. Allowed extensions: {", ".join(allowed_extensions)}'
        )


def validate_file_size(value):
    """Validate file size for uploads"""
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)  # 5MB default
    
    if value.size > max_size:
        raise ValidationError(
            f'File size {value.size} bytes exceeds maximum allowed size of {max_size} bytes'
        )


def validate_image_file(value):
    """Comprehensive validation for image files"""
    validate_file_extension(value)
    validate_file_size(value)
    
    # Additional validation for image files
    try:
        from PIL import Image
        img = Image.open(value)
        img.verify()
    except Exception:
        raise ValidationError('Invalid image file or corrupted image')


def validate_secure_filename(filename):
    """Validate filename for security"""
    # Remove path traversal attempts
    filename = os.path.basename(filename)
    
    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        if char in filename:
            raise ValidationError(f'Filename contains dangerous character: {char}')
    
    return filename
