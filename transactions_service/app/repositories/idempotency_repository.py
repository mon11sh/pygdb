"""
Idempotency Repository

Makes money-movement replay-safe using a client-supplied idempotency key.

Flow (insert-first, so concurrent duplicates cannot both execute):
  1. reserve(key)         -> INSERT ... ON CONFLICT DO NOTHING
                             True  = we claimed the key, proceed with the operation
                             False = key already exists (a duplicate request)
  2a. on success:  complete(key, response)  -> store response, mark COMPLETED
  2b. on failure:  release(key)             -> delete our IN_PROGRESS reservation
                                               so the client can safely retry
  3. get_completed_response(key) -> the stored response iff the key is COMPLETED

A duplicate request (reserve == False) returns the COMPLETED response if the
first one finished, otherwise it is rejected as "in progress" rather than
executing the money movement a second time.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime

from app.database.db import database
from app.exceptions.database_exception import DatabaseException

logger = logging.getLogger(__name__)


class IdempotencyRepositoryInterface(ABC):
    """Provider-agnostic data-access CONTRACT for idempotency keys.

    reserve() MUST fail CLOSED on a real DB error (raise DatabaseException):
    for money movement we never proceed without a confirmed reservation.
    A duplicate key returns False (already exists), not an error.
    """

    @abstractmethod
    async def reserve(self, idempotency_key: str, operation: str) -> bool:
        """True if this caller claimed the key, False if it already exists."""

    @abstractmethod
    async def get_completed_response(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Stored response iff the key exists AND is COMPLETED, else None."""

    @abstractmethod
    async def complete(self, idempotency_key: str, response: Dict[str, Any]) -> None:
        """Store the response and mark the key COMPLETED."""

    @abstractmethod
    async def release(self, idempotency_key: str) -> None:
        """Delete an IN_PROGRESS reservation so the client can retry."""


class IdempotencyRepository(IdempotencyRepositoryInterface):
    """Stores and retrieves idempotent operation responses (insert-first).

    asyncpg / postgres / supabase implementation. Method are static so the
    money-movement services can call them at the class level
    (``IdempotencyRepository.reserve(...)``)."""

    @staticmethod
    async def reserve(idempotency_key: str, operation: str) -> bool:
        """
        Atomically claim the key. Returns True if this caller reserved it (first
        time seen), False if it already exists (a duplicate/concurrent request).

        Fails CLOSED on a DB error: for money movement we must never proceed
        without a confirmed reservation, since a failed-open path would let two
        concurrent duplicates both execute. On DB error we raise so the caller
        aborts and surfaces a 5xx rather than moving money twice. No row was
        committed on this path, so the key is not left dangling.

        NOTE (TOCTOU limitation): this makes the reservation itself fail-closed,
        but full cross-service atomicity (e.g. SELECT ... FOR UPDATE spanning the
        account service) is out of scope; a narrow window between reserve and the
        downstream debit/credit still exists.
        """
        query = """
            INSERT INTO idempotency_keys (idempotency_key, operation, status, created_at, updated_at)
            VALUES ($1, $2, 'IN_PROGRESS', $3, $3)
            ON CONFLICT (idempotency_key) DO NOTHING
        """
        conn = await database.get_connection()
        try:
            result = await conn.execute(query, idempotency_key, operation, datetime.utcnow())
            # asyncpg returns "INSERT 0 1" when a row was inserted, "INSERT 0 0" on conflict.
            return result.strip().endswith(" 1")
        except Exception as e:
            logger.error(f"❌ Idempotency reserve failed for {idempotency_key}: {e}")
            raise DatabaseException("Failed to reserve idempotency key")
        finally:
            await database._pool.release(conn)

    @staticmethod
    async def get_completed_response(idempotency_key: str) -> Optional[Dict[str, Any]]:
        """
        Return the stored response iff the key exists AND is COMPLETED.
        Returns None if the key is unknown or still IN_PROGRESS.
        """
        query = "SELECT status, response_json FROM idempotency_keys WHERE idempotency_key = $1"
        conn = await database.get_connection()
        try:
            row = await conn.fetchrow(query, idempotency_key)
            if row and row["status"] == "COMPLETED" and row["response_json"]:
                return json.loads(row["response_json"])
            return None
        except Exception as e:
            logger.error(f"❌ Idempotency lookup failed for {idempotency_key}: {e}")
            return None
        finally:
            await database._pool.release(conn)

    @staticmethod
    async def complete(idempotency_key: str, response: Dict[str, Any]) -> None:
        """Store the response and mark the key COMPLETED."""
        query = """
            UPDATE idempotency_keys
            SET response_json = $2, status = 'COMPLETED', updated_at = $3
            WHERE idempotency_key = $1
        """
        conn = await database.get_connection()
        try:
            await conn.execute(
                query,
                idempotency_key,
                json.dumps(response, default=str),
                datetime.utcnow(),
            )
        except Exception as e:
            # The operation already succeeded; failing to record the response is
            # non-fatal (a later replay simply re-runs). Log loudly.
            logger.error(f"❌ Failed to complete idempotency key {idempotency_key}: {e}")
        finally:
            await database._pool.release(conn)

    @staticmethod
    async def release(idempotency_key: str) -> None:
        """
        Delete our IN_PROGRESS reservation after a failed operation so the client
        can retry with the same key. Only deletes rows still IN_PROGRESS to avoid
        ever removing a COMPLETED result.
        """
        query = "DELETE FROM idempotency_keys WHERE idempotency_key = $1 AND status = 'IN_PROGRESS'"
        conn = await database.get_connection()
        try:
            await conn.execute(query, idempotency_key)
        except Exception as e:
            logger.error(f"❌ Failed to release idempotency key {idempotency_key}: {e}")
        finally:
            await database._pool.release(conn)
