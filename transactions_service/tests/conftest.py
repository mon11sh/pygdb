# -*- coding: utf-8 -*-
"""
Pytest configuration and fixtures for transaction service tests.

Initializes JWT configuration and provides test client.
"""

import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

# Import JWT configuration from Auth Service (same as main.py does)
auth_service_path = str(Path(__file__).parent.parent.parent / "auth_service" / "app")
if auth_service_path not in sys.path:
    sys.path.insert(0, auth_service_path)

try:
    from gdb_common.auth_dependencies import set_jwt_config
except ImportError:
    # Fallback if auth_service is in different location
    auth_service_parent = str(Path(__file__).parent.parent.parent / "auth_service")
    if auth_service_parent not in sys.path:
        sys.path.insert(0, auth_service_parent)
    from app.security.auth_dependencies import set_jwt_config


@pytest.fixture(scope="session", autouse=True)
def setup_jwt_config():
    """Initialize JWT config for all tests."""
    set_jwt_config("test-secret-key-for-testing-only", "HS256")
    yield


@pytest.fixture
def client():
    """FastAPI test client with JWT config initialized."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    """Sample authorization headers with valid JWT token."""
    # This is a pre-generated test token with admin role
    return {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDAwIiwibG9naW5faWQiOiJBRE1JTiIsInJvbGUiOiJBRE1JTiIsImlhdCI6MTczNzEwOTMzMCwiZXhwIjoyMzMxMzExODAwLCJqdGkiOiJlMjk5ZWE5Ny1hNmI3LTRjMTAtOWY1NS1kMjNiZjFmNTIyZDAifQ.pR30TRGxJ5-ZtHMxOuUKSoiVKLYKqxaUvlJTL6M0agc"
    }
