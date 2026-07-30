"""
API-level tests: auth is enforced on the protected routes.

Firebase verification and the DB session are mocked; requests go through
the real FastAPI app.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from fastapi.testclient import TestClient

from app.main import app
from db import get_db
from db.models import User


CLAIMS = {
    'uid': 'firebase-uid-123',
    'sub': 'firebase-uid-123',
    'email': 'trader@example.com',
    'phone_number': '+15551234567',
}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_with_existing_user():
    user = User(
        id = uuid4(),
        firebase_uuid = CLAIMS['uid'],
        email = CLAIMS['email'],
        phone = CLAIMS['phone_number'],
        created_at = datetime.now(timezone.utc),
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.clear()


def test_chat_without_token_returns_401(client):
    response = client.post('/v0/trader/chat', json = {'query': 'how is NVDA doing?'})
    assert response.status_code == 401


def test_chat_with_invalid_token_returns_401(client, db_with_existing_user):
    with patch('core.auth.dependencies.verify_firebase_token', side_effect = ValueError('bad token')):
        response = client.post(
            '/v0/trader/chat',
            json = {'query': 'how is NVDA doing?'},
            headers = {'Authorization': 'Bearer garbage'},
        )
    assert response.status_code == 401


def test_me_without_token_returns_401(client):
    response = client.get('/v0/auth/me')
    assert response.status_code == 401


def test_me_with_valid_token_returns_profile(client, db_with_existing_user):
    with patch('core.auth.dependencies.verify_firebase_token', return_value = CLAIMS):
        response = client.get('/v0/auth/me', headers = {'Authorization': 'Bearer valid-token'})

    assert response.status_code == 200
    body = response.json()
    assert body['firebase_uuid'] == CLAIMS['uid']
    assert body['email'] == CLAIMS['email']
    assert body['phone'] == CLAIMS['phone_number']
    assert body['last_login'] is not None
    assert set(body.keys()) == {'id', 'firebase_uuid', 'email', 'phone', 'created_at', 'last_login'}
