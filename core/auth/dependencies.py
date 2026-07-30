"""
FastAPI dependency for Firebase-backed authentication.

The frontend signs up/in with the Firebase Web SDK and sends the Firebase
ID token on every request as 'Authorization: Bearer <token>'. This backend
verifies the token and JIT-provisions/updates the local users row:
Firebase stores all credentials, we only keep the profile.
"""

import logging

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.auth.firebase import verify_firebase_token
from db import get_db
from db.models import User

logger = logging.getLogger(__name__)

# auto_error = False so a missing header becomes our own 401 (FastAPI's default is a 403)
bearer_scheme = HTTPBearer(auto_error = False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = detail,
        headers = {'WWW-Authenticate': 'Bearer'},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the Firebase ID token from the Authorization header into a local User.

    - 401 if the token is missing, invalid, or expired
    - 403 if the user exists but is archived (soft deleted)
    - creates the users row on first sight, updates last_login (and email/phone
      if they changed in Firebase) on every authenticated request
    """
    if credentials is None or not credentials.credentials:
        raise _unauthorized('Not authenticated')

    try:
        claims = verify_firebase_token(credentials.credentials)
    except Exception:
        logger.exception('Firebase ID token verification failed')
        raise _unauthorized('Invalid or expired authentication token') from None

    firebase_uuid = claims.get('uid') or claims.get('sub')
    if not firebase_uuid:
        raise _unauthorized('Authentication token has no user id')

    email = claims.get('email')
    phone = claims.get('phone_number')
    now = datetime.now(timezone.utc)

    user = db.query(User).filter(User.firebase_uuid == firebase_uuid).first()

    if user is None:
        if not email:
            # users.email is NOT NULL: only email-bearing sign-in methods are supported
            raise _unauthorized('Authentication token has no email claim')
        user = User(firebase_uuid = firebase_uuid, email = email, phone = phone, last_login = now)
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            # Two concurrent first requests raced on the unique constraint;
            # fall through and treat the winner's row as an existing user.
            db.rollback()
            user = db.query(User).filter(User.firebase_uuid == firebase_uuid).first()
            if user is None:
                logger.exception('User provisioning failed for firebase_uuid=%s', firebase_uuid)
                raise

    if user.archived_at is not None:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'User account is archived',
        )

    user.last_login = now
    if email and user.email != email:
        user.email = email
    if phone and user.phone != phone:
        user.phone = phone
    db.commit()
    db.refresh(user)
    return user
