"""
Authentication utilities for admin access.

Stub implementation for development.
"""

from typing import Dict


def get_current_admin_user() -> Dict:
    """Get current admin user (stub implementation)."""
    return {"id": "admin", "username": "admin", "role": "admin"}