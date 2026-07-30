"""
Firebase-backed authentication for the API.
"""

from core.auth.dependencies import bearer_scheme, get_current_user
from core.auth.firebase import init_firebase, verify_firebase_token


__all__ = ['bearer_scheme', 'get_current_user', 'init_firebase', 'verify_firebase_token']
