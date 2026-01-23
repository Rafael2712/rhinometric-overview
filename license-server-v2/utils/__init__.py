"""
Utilities package for Rhinometric License Server
"""
from .email_sender import send_license_email_with_attachments, generate_license_key

__all__ = ['send_license_email_with_attachments', 'generate_license_key']
