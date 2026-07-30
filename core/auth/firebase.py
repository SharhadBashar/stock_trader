"""
Lazy firebase_admin initialization and Firebase ID token verification.

The Admin SDK is initialized on first use (not at import time) so that
modules can be imported without Firebase credentials being present.
"""

import threading

import firebase_admin

from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from settings import GOOGLE_APPLICATION_CREDENTIALS


_init_lock = threading.Lock()


def init_firebase() -> firebase_admin.App:
    """Return the default firebase_admin app, initializing it on first use."""
    with _init_lock:
        try:
            return firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
            return firebase_admin.initialize_app(cred)


def verify_firebase_token(token: str) -> dict:
    """Verify a Firebase ID token and return its decoded claims.

    Raises whatever firebase_admin raises for invalid/expired/revoked tokens;
    callers are expected to translate that into an HTTP 401.
    """
    init_firebase()
    return firebase_auth.verify_id_token(token)
