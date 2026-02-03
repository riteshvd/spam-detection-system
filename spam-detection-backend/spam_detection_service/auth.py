# spam_detection_service/auth.py
"""
Authentication utilities for JWT tokens
"""

import os
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

# ===== JWT CONFIGURATION =====

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# ===== CREDENTIALS =====
# In production, use database for authentication

ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'spam-detection-2025')

def validate_credentials(username, password):
    """Validate user credentials"""
    if username == ADMIN_USER and password == ADMIN_PASS:
        return True
    return False

def log_auth_attempt(username, success):
    """Log authentication attempts"""
    if success:
        logger.info(f"✓ User {username} authenticated successfully")
    else:
        logger.warning(f"✗ Failed authentication attempt for user: {username}")
