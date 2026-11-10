import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.models import User
from app.core.security import hash_password

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not configured.")

if "social_media_test" not in TEST_DATABASE_URL:
    raise RuntimeError("Tests must use the social_media_test database.")

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def normal_user(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("TestPassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=False,
        role="user",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture()
def admin_user(db_session):
    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=hash_password("AdminPassword123"),
        full_name="Admin User",
        is_active=True,
        is_verified=True,
        role="admin",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture()
def user_token(client, normal_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


@pytest.fixture()
def admin_token(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "AdminPassword123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]