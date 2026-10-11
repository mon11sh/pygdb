-- Migration: add idempotency_keys table
-- Run this against an EXISTING transactions database (a fresh DB already gets
-- this table from transactions_schema.sql). Enables replay-safe money movement.
--
-- A key is first reserved (status IN_PROGRESS); the response is stored and status
-- flipped to COMPLETED once the operation finishes. A failed operation releases
-- (deletes) its IN_PROGRESS row so the client can retry.

CREATE TABLE IF NOT EXISTS idempotency_keys (
    idempotency_key VARCHAR(100) PRIMARY KEY,
    operation VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'IN_PROGRESS',
    response_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- If upgrading from the earlier single-response version of this table, add the
-- new columns in place:
ALTER TABLE idempotency_keys ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED';
ALTER TABLE idempotency_keys ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE idempotency_keys ALTER COLUMN response_json DROP NOT NULL;
