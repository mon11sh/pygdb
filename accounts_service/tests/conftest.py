"""
Pytest Configuration and Fixtures

Global fixtures for all tests in the accounts service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime


@pytest.fixture(autouse=True)
def _bypass_internal_auth():
    from app.main import app
    from app.dependencies.internal_auth import verify_internal_api_key
    app.dependency_overrides[verify_internal_api_key] = lambda: True
    yield
    app.dependency_overrides.pop(verify_internal_api_key, None)


@pytest.fixture
def mock_db():
    """Mock database connection with proper transaction support."""
    # Create proper dict response for fetchrow
    db_row = {
        'account_number': 1000,
        'name': 'John Doe',
        'account_type': 'SAVINGS',
        'balance': Decimal('50000.00'),
        'privilege': 'GOLD',
        'is_active': True,
        'activated_date': datetime.now(),
        'closed_date': None
    }
    
    db = AsyncMock()
    
    # Create a mock connection that's returned from transaction context
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=1000)
    mock_conn.execute = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=db_row)
    
    # Create proper async context manager for transactions
    class AsyncTransactionContext:
        def __init__(self, conn):
            self.conn = conn
            
        async def __aenter__(self):
            return self.conn
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False
    
    db.transaction = MagicMock(return_value=AsyncTransactionContext(mock_conn))
    db.fetch = AsyncMock(return_value=[])
    db.fetch_one = AsyncMock(return_value=db_row)
    db.fetchrow = AsyncMock(return_value=db_row)
    db.fetchval = AsyncMock(return_value=1000)
    db.execute = AsyncMock()
    
    return db


@pytest.fixture
def mock_pool():
    """Mock connection pool."""
    pool = AsyncMock()
    return pool


@pytest.fixture
def mock_repository():
    """Mock repository for service tests."""
    return AsyncMock()


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
