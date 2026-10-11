"""
Pytest configuration for test suite.
Database initialization is handled by FastAPI's lifespan context manager.
"""

import pytest


# Pytest configuration
# The app's lifespan in main.py handles database init/close when AsyncClient is created


@pytest.fixture(autouse=True)
def _bypass_internal_auth():
    """Bypass the internal API key dependency for in-process tests.

    Both test suites import the same `app` object from app.main, so registering
    the dependency override here covers TestClient(app) and ASGITransport(app=app).
    """
    from app.main import app
    from app.dependencies.internal_auth import verify_internal_api_key
    app.dependency_overrides[verify_internal_api_key] = lambda: True
    yield
    app.dependency_overrides.pop(verify_internal_api_key, None)