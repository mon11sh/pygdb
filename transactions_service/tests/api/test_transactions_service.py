"""
Transactions Service API Tests
Tests endpoints using FastAPI app and mocked dependencies.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from jose import jwt
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.enums import TransactionType

from app.config.settings import settings

# Must match settings because lifespan overwrites any manual set_jwt_config
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

def create_test_token(role: str = "MANAGER", login_id: str = "TEST_USER", sub: str = "1000"):
    """Create a valid JWT token for testing with specific role."""
    payload = {
        "sub": sub,
        "login_id": login_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@pytest.fixture
def mock_db():
    """Robust mock for database across all repositories."""
    mock_db_obj = MagicMock()
    mock_conn = AsyncMock()
    
    # Default success behaviors
    mock_conn.fetchval.return_value = 123
    mock_conn.fetchrow.return_value = None
    mock_conn.execute.return_value = "DONE"
    mock_conn.fetch.return_value = []
    
    # Return the SAME connection mock by default for each test
    mock_db_obj.get_connection = AsyncMock(return_value=mock_conn)
    
    mock_pool = MagicMock()
    mock_pool.release = AsyncMock()
    mock_db_obj._pool = mock_pool

    targets = [
        "app.repositories.transaction_log_repository.database",
        "app.repositories.transfer_limit_repository.database",
        "app.repositories.transaction_repository.database"
    ]
    
    with patch(targets[0], mock_db_obj), \
         patch(targets[1], mock_db_obj), \
         patch(targets[2], mock_db_obj):
        yield mock_db_obj, mock_conn

@pytest.fixture(autouse=True)
def _configure_jwt_for_this_file():
    """Point the JWT validator at the real settings secret before every test.

    create_test_token signs with settings.JWT_SECRET_KEY, but conftest configures
    the validator with a different ('test-secret') key. The two match only after
    some other test file's TestClient triggers the app lifespan (which sets this
    same secret) — which is why this file passed in the full suite but FAILED when
    run alone. Setting it here makes real validation deterministic in isolation.
    Scoped to this file (function-autouse), so no cross-file blast radius.
    """
    from gdb_common.auth_dependencies import set_jwt_config
    set_jwt_config(settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    yield

@pytest.fixture(autouse=True)
def mock_auth():
    """Legacy no-op kept for signature compatibility (patches auth_service's local
    JWTValidator, which the routes do not use — real validation is what runs)."""
    with patch("security.jwt_validation.JWTValidator.validate_token") as mock:
        yield mock

@pytest.fixture
def manager_headers():
    token = create_test_token(role="MANAGER")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers():
    token = create_test_token(role="ADMIN")
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
class TestTransactionsService:
    """Test suite for Transactions Service API"""

    BASE_URL = "/api/v1"

    async def test_positive_deposit(self, mock_db, manager_headers, mock_auth):
        """POSITIVE: Deposit with valid amount"""
        db_obj, mock_conn = mock_db
        mock_auth.return_value = {"role": "MANAGER", "login_id": "TEST", "sub": "1000"}
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.deposit_service.account_service_client") as mock_client:
                mock_client.validate_account = AsyncMock(return_value={"id": 1003, "balance": 5000, "status": "ACTIVE", "name": "John Doe"})
                mock_client.credit_account = AsyncMock(return_value={"new_balance": 6000})
                
                response = await client.post(
                    f"{self.BASE_URL}/deposits",
                    headers=manager_headers,
                    params={"account_number": 1003, "amount": 1000}
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["status"] == "SUCCESS"
                assert data["new_balance"] == 6000.0

    async def test_negative_deposit_no_auth(self):
        """NEGATIVE: Deposit without auth token"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"{self.BASE_URL}/deposits",
                params={"account_number": 1003, "amount": 1000}
            )
            assert response.status_code == 401

    async def test_negative_deposit_nonexistent_account(self, mock_db, manager_headers, mock_auth):
        """NEGATIVE: Deposit to non-existent account"""
        db_obj, mock_conn = mock_db
        mock_auth.return_value = {"role": "MANAGER", "login_id": "TEST", "sub": "1000"}
        from app.exceptions.transaction_exceptions import AccountNotFoundException
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.deposit_service.account_service_client") as mock_client:
                mock_client.validate_account = AsyncMock(side_effect=AccountNotFoundException("Account not found"))
                
                response = await client.post(
                    f"{self.BASE_URL}/deposits",
                    headers=manager_headers,
                    params={"account_number": 9999, "amount": 1000}
                )
                assert response.status_code == 404

    async def test_negative_deposit_invalid_amount(self, mock_db, manager_headers, mock_auth):
        """NEGATIVE: Deposit with invalid amount"""
        db_obj, mock_conn = mock_db
        mock_auth.return_value = {"role": "MANAGER", "login_id": "TEST", "sub": "1000"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.deposit_service.account_service_client") as mock_client:
                mock_client.validate_account = AsyncMock(return_value={"id": 1003, "balance": 5000, "status": "ACTIVE"})
                
                response = await client.post(
                    f"{self.BASE_URL}/deposits",
                    headers=manager_headers,
                    params={"account_number": 1003, "amount": -1000}
                )
                assert response.status_code == 400

    async def test_positive_withdraw_correct_pin(self, mock_db, manager_headers, mock_auth):
        """POSITIVE: Withdraw with correct PIN"""
        db_obj, mock_conn = mock_db
        mock_auth.return_value = {"role": "MANAGER", "login_id": "TEST", "sub": "1000"}
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.withdraw_service.account_service_client") as mock_client:
                mock_client.validate_account = AsyncMock(return_value={"id": 1003, "balance": 5000, "status": "ACTIVE"})
                mock_client.verify_pin = AsyncMock(return_value=True)
                mock_client.debit_account = AsyncMock(return_value={"new_balance": 4500})
                
                response = await client.post(
                    f"{self.BASE_URL}/withdrawals",
                    headers=manager_headers,
                    params={"account_number": 1003, "amount": 500, "pin": "9640"}
                )
                assert response.status_code == 201
                assert response.json()["new_balance"] == 4500.0

    async def test_negative_withdraw_wrong_pin(self, mock_db, manager_headers, mock_auth):
        """NEGATIVE: Withdraw with wrong PIN"""
        db_obj, mock_conn = mock_db
        mock_auth.return_value = {"role": "MANAGER", "login_id": "TEST", "sub": "1000"}
        from app.exceptions.transaction_exceptions import InvalidPINException
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.withdraw_service.account_service_client") as mock_client:
                mock_client.validate_account = AsyncMock(return_value={"id": 1003, "balance": 5000, "status": "ACTIVE"})
                mock_client.verify_pin = AsyncMock(side_effect=InvalidPINException("Invalid PIN"))

                response = await client.post(
                    f"{self.BASE_URL}/withdrawals",
                    headers=manager_headers,
                    params={"account_number": 1003, "amount": 500, "pin": "0000"}
                )
                assert response.status_code == 401

    async def test_positive_transfer_valid(self, mock_db, manager_headers, mock_auth):
        """POSITIVE: Transfer between valid accounts"""
        db_obj, mock_conn = mock_db
        mock_auth.return_value = {"role": "MANAGER", "login_id": "TEST", "sub": "1000"}
        
        # Sequentially mocked responses for limits and count
        mock_conn.fetchrow.side_effect = [
            {"total": 0}, # get_daily_used_amount (Decimal(0))
            {"cnt": 0},   # get_daily_transaction_count (0)
            {             # get_transfer_rule
                'daily_limit': 100000.0,
                'per_transaction_limit': 50000.0,
                'created_at': datetime.utcnow()
            }
        ]
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.transfer_service.account_service_client") as mock_client:
                mock_client.validate_account = AsyncMock(side_effect=[
                    {"id": 1003, "balance": 5000, "status": "ACTIVE", "privilege": "GOLD"},
                    {"id": 1004, "balance": 1000, "status": "ACTIVE", "privilege": "SILVER"}
                ])
                mock_client.verify_pin = AsyncMock(return_value=True)
                mock_client.debit_account = AsyncMock(return_value={"new_balance": 4500})
                mock_client.credit_account = AsyncMock(return_value={"new_balance": 1500})
                
                # Comprehensive Payment Gateway mock
                with patch("app.services.transfer_service.payment_gateway_client") as mock_gw:
                    mock_gw.validate_payment = AsyncMock(return_value=True)
                    mock_gw.process_payment = AsyncMock(return_value={"status": "SUCCESS", "gateway_id": "GW123"})
                    
                    response = await client.post(
                        f"{self.BASE_URL}/transfers",
                        headers=manager_headers,
                        params={
                            "from_account": 1003,
                            "to_account": 1004,
                            "amount": 500,
                            "pin": "9640"
                        }
                    )
                    assert response.status_code == 201

    async def test_positive_get_transaction_logs(self, admin_headers):
        """POSITIVE: Get transaction logs.

        Overrides the auth + service dependencies (FastAPI's canonical test seam)
        rather than mocking asyncpg. The old asyncpg mocks were silently ignored
        under the inmemory provider that CI uses, so the endpoint returned leaked
        cross-test in-memory rows (3, not 2). Overriding the service makes this
        deterministic and provider-independent.
        """
        from gdb_common.auth_dependencies import get_current_user
        from app.dependencies.providers import get_transaction_log_service

        now = datetime.utcnow().isoformat()
        canned = {
            "account_number": 1003,
            "logs": [
                {"id": 1, "account_number": 1003, "amount": 1000.0,
                 "transaction_type": "DEPOSIT", "created_at": now, "updated_at": None},
                {"id": 2, "account_number": 1003, "amount": 200.0,
                 "transaction_type": "WITHDRAWAL", "created_at": now, "updated_at": None},
            ],
            "skip": 0, "limit": 50, "has_more": False, "total_count": 2,
        }

        class _FakeLogService:
            async def get_transaction_logs(self, **kwargs):
                return canned

        app.dependency_overrides[get_current_user] = lambda: {"role": "ADMIN", "login_id": "TEST", "user_id": 1}
        app.dependency_overrides[get_transaction_log_service] = lambda: _FakeLogService()
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"{self.BASE_URL}/transaction-logs/1003", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert "logs" in data
            assert len(data["logs"]) == 2
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_transaction_log_service, None)

    async def test_positive_get_transfer_limits(self, admin_headers):
        """POSITIVE: Get transfer limits.

        Same rationale as get_transaction_logs: the old asyncpg mocks were ignored
        under the inmemory provider, so the GOLD transfer rule wasn't found and the
        endpoint 404'd. Override the service dependency for a deterministic result.
        """
        from gdb_common.auth_dependencies import get_current_user
        from app.dependencies.providers import get_transfer_limit_service

        canned = {
            "account_number": 1003, "privilege": "GOLD",
            "daily_limit": 50000.0, "daily_used": 0.0, "daily_remaining": 50000.0,
            "transaction_limit": 25000, "transactions_today": 0, "transactions_remaining": 25000,
        }

        class _FakeLimitService:
            async def get_transfer_limit(self, account_number):
                return canned

        app.dependency_overrides[get_current_user] = lambda: {"role": "ADMIN", "login_id": "TEST", "user_id": 1}
        app.dependency_overrides[get_transfer_limit_service] = lambda: _FakeLimitService()
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"{self.BASE_URL}/transfer-limits/1003", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["privilege"] == "GOLD"
            assert data["daily_limit"] == 50000.0
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_transfer_limit_service, None)


@pytest.mark.asyncio
class TestIdempotency:
    """Idempotency-Key behaviour on money movement (deposit path)."""

    BASE_URL = "/api/v1"

    async def test_replay_returns_stored_result_without_moving_money(self, manager_headers, mock_auth):
        """A completed key replays its stored response and does NOT credit again."""
        mock_auth.return_value = {"role": "MANAGER", "login_id": "TEST", "sub": "1000"}
        stored = {
            "status": "SUCCESS", "transaction_id": 42, "account_number": 1003,
            "amount": 1000.0, "transaction_type": "DEPOSIT", "new_balance": 6000.0,
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.deposit_service.IdempotencyRepository") as mock_idem, \
                 patch("app.services.deposit_service.account_service_client") as mock_client:
                mock_idem.get_completed_response = AsyncMock(return_value=stored)
                mock_client.credit_account = AsyncMock()

                response = await client.post(
                    f"{self.BASE_URL}/deposits",
                    headers={**manager_headers, "Idempotency-Key": "key-abc"},
                    params={"account_number": 1003, "amount": 1000},
                )

                assert response.status_code == 201
                assert response.json() == stored
                mock_client.credit_account.assert_not_called()  # money not moved on replay

    async def test_duplicate_in_progress_conflicts(self, manager_headers, mock_auth):
        """A concurrent duplicate (key reserved, not yet completed) returns 409."""
        mock_auth.return_value = {"role": "MANAGER", "login_id": "TEST", "sub": "1000"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.deposit_service.IdempotencyRepository") as mock_idem, \
                 patch("app.services.deposit_service.account_service_client") as mock_client:
                mock_idem.get_completed_response = AsyncMock(return_value=None)
                mock_idem.reserve = AsyncMock(return_value=False)  # already reserved by another request
                mock_client.credit_account = AsyncMock()

                response = await client.post(
                    f"{self.BASE_URL}/deposits",
                    headers={**manager_headers, "Idempotency-Key": "key-abc"},
                    params={"account_number": 1003, "amount": 1000},
                )

                assert response.status_code == 409
                mock_client.credit_account.assert_not_called()  # money not moved for a duplicate

    async def test_no_release_after_money_moved(self, mock_db, manager_headers, mock_auth):
        """Regression (C2): a failure AFTER funds move must NOT release the key,
        otherwise a same-key retry would move the money a second time."""
        mock_auth.return_value = {"role": "MANAGER", "login_id": "TEST", "sub": "1000"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.deposit_service.IdempotencyRepository") as mock_idem, \
                 patch("app.services.deposit_service.account_service_client") as mock_client:
                mock_idem.get_completed_response = AsyncMock(return_value=None)
                mock_idem.reserve = AsyncMock(return_value=True)   # we own the key
                mock_idem.complete = AsyncMock()
                mock_idem.release = AsyncMock()
                mock_client.validate_account = AsyncMock(return_value={"balance": 5000, "name": "John"})
                # Credit succeeds (money moved), but returns a bad shape so a later
                # step raises — exactly the post-money-movement failure path.
                mock_client.credit_account = AsyncMock(return_value="NOT_A_DICT")

                response = await client.post(
                    f"{self.BASE_URL}/deposits",
                    headers={**manager_headers, "Idempotency-Key": "key-moved"},
                    params={"account_number": 1003, "amount": 1000},
                )

                assert response.status_code >= 400          # the request reports failure
                mock_idem.release.assert_not_called()       # but the key is NOT released -> retry can't double-spend

