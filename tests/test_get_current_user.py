"""
Unit tests for core.auth.get_current_user.

Firebase verification and the DB session are mocked: no network, no database.
"""

from unittest.mock import MagicMock, patch

import pytest

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError

from core.auth.dependencies import get_current_user
from db.models import User


CLAIMS = {
    'uid': 'firebase-uid-123',
    'sub': 'firebase-uid-123',
    'email': 'trader@example.com',
    'phone_number': '+15551234567',
}


def bearer(token = 'valid-token'):
    return HTTPAuthorizationCredentials(scheme = 'Bearer', credentials = token)


def fake_db(existing_user = None):
    """MagicMock standing in for a Session; query().filter().first() -> existing_user."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = existing_user
    return db


def existing_user(**overrides):
    user = User(
        firebase_uuid = CLAIMS['uid'],
        email = CLAIMS['email'],
        phone = CLAIMS['phone_number'],
    )
    for key, value in overrides.items():
        setattr(user, key, value)
    return user


class TestMissingOrInvalidToken:
    def test_missing_credentials_returns_401(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials = None, db = fake_db())
        assert exc_info.value.status_code == 401

    def test_empty_token_returns_401(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials = bearer(token = ''), db = fake_db())
        assert exc_info.value.status_code == 401

    def test_invalid_token_returns_401(self):
        with patch('core.auth.dependencies.verify_firebase_token', side_effect = ValueError('bad token')):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials = bearer(), db = fake_db())
        assert exc_info.value.status_code == 401

    def test_token_without_uid_returns_401(self):
        with patch('core.auth.dependencies.verify_firebase_token', return_value = {'email': 'a@b.com'}):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials = bearer(), db = fake_db())
        assert exc_info.value.status_code == 401


class TestFirstSight:
    def test_creates_user_from_token_claims(self):
        db = fake_db(existing_user = None)
        with patch('core.auth.dependencies.verify_firebase_token', return_value = CLAIMS):
            user = get_current_user(credentials = bearer(), db = db)

        added = db.add.call_args.args[0]
        assert added is user
        assert user.firebase_uuid == CLAIMS['uid']
        assert user.email == CLAIMS['email']
        assert user.phone == CLAIMS['phone_number']
        assert user.last_login is not None
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(user)

    def test_new_user_without_email_returns_401(self):
        claims = {'uid': 'no-email-uid'}
        db = fake_db(existing_user = None)
        with patch('core.auth.dependencies.verify_firebase_token', return_value = claims):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials = bearer(), db = db)
        assert exc_info.value.status_code == 401
        db.add.assert_not_called()

    def test_provisioning_race_falls_back_to_winner_row(self):
        winner = existing_user()
        db = fake_db()
        db.query.return_value.filter.return_value.first.side_effect = [None, winner]
        db.commit.side_effect = [IntegrityError('INSERT INTO users', None, Exception('duplicate key')), None]

        with patch('core.auth.dependencies.verify_firebase_token', return_value = CLAIMS):
            user = get_current_user(credentials = bearer(), db = db)

        assert user is winner
        db.rollback.assert_called_once()
        assert user.last_login is not None


class TestExistingUser:
    def test_updates_last_login(self):
        user = existing_user(last_login = None)
        db = fake_db(existing_user = user)
        with patch('core.auth.dependencies.verify_firebase_token', return_value = CLAIMS):
            result = get_current_user(credentials = bearer(), db = db)

        assert result is user
        assert user.last_login is not None
        db.add.assert_not_called()
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(user)

    def test_updates_email_and_phone_when_changed_in_firebase(self):
        user = existing_user(email = 'old@example.com', phone = '+15550000000')
        db = fake_db(existing_user = user)
        with patch('core.auth.dependencies.verify_firebase_token', return_value = CLAIMS):
            get_current_user(credentials = bearer(), db = db)

        assert user.email == CLAIMS['email']
        assert user.phone == CLAIMS['phone_number']

    def test_keeps_email_and_phone_when_claims_absent(self):
        user = existing_user()
        db = fake_db(existing_user = user)
        claims = {'uid': CLAIMS['uid']}
        with patch('core.auth.dependencies.verify_firebase_token', return_value = claims):
            get_current_user(credentials = bearer(), db = db)

        assert user.email == CLAIMS['email']
        assert user.phone == CLAIMS['phone_number']

    def test_archived_user_returns_403_without_updates(self):
        from datetime import datetime, timezone

        user = existing_user(archived_at = datetime.now(timezone.utc), last_login = None)
        db = fake_db(existing_user = user)
        with patch('core.auth.dependencies.verify_firebase_token', return_value = CLAIMS):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials = bearer(), db = db)

        assert exc_info.value.status_code == 403
        assert user.last_login is None
        db.commit.assert_not_called()


class TestVerifyFirebaseToken:
    def test_initializes_firebase_lazily_and_delegates_to_verify_id_token(self):
        from core.auth.firebase import verify_firebase_token

        with (
            patch('core.auth.firebase.init_firebase') as mock_init,
            patch('core.auth.firebase.firebase_auth.verify_id_token', return_value = CLAIMS) as mock_verify,
        ):
            claims = verify_firebase_token('some-token')

        assert claims == CLAIMS
        mock_init.assert_called_once()
        mock_verify.assert_called_once_with('some-token')
