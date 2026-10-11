/*
Transaction Service - Database Schema

Creates two tables:
1. fund_transfers - Tracks all fund transfer operations
2. transaction_logging - Logs all transaction activities

Common fields for both tables:
- id: Primary key (BIGSERIAL)
- created_at: Record creation timestamp
- updated_at: Record last update timestamp
*/

-- ========================================
-- TABLE 1: FUND TRANSFERS
-- ========================================
-- Tracks all fund transfer operations between accounts

CREATE TABLE IF NOT EXISTS fund_transfers (
    id BIGSERIAL PRIMARY KEY,
    from_account BIGINT NOT NULL,
    to_account BIGINT NOT NULL,
    transfer_amount NUMERIC(15, 2) NOT NULL,
    transfer_mode VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_transfer_amount CHECK (transfer_amount > 0),
    CONSTRAINT chk_from_not_equal_to CHECK (from_account <> to_account),
    CONSTRAINT chk_transfer_mode CHECK (
        transfer_mode IN ('NEFT', 'RTGS', 'IMPS', 'UPI')
    )
);

-- Indexes for fund_transfers
CREATE INDEX IF NOT EXISTS idx_fund_transfers_from_account ON fund_transfers(from_account);
CREATE INDEX IF NOT EXISTS idx_fund_transfers_to_account ON fund_transfers(to_account);
CREATE INDEX IF NOT EXISTS idx_fund_transfers_created_at ON fund_transfers(created_at);

-- ========================================
-- TABLE 2: TRANSACTION LOGGING
-- ========================================
-- Logs all transaction activities (withdraw, deposit, transfer)

CREATE TABLE IF NOT EXISTS transaction_logging (
    id BIGSERIAL PRIMARY KEY,
    account_number BIGINT NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    reference_id BIGINT,
    description VARCHAR(255),
    mode VARCHAR(20),
    status VARCHAR(20) DEFAULT 'SUCCESS',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_transaction_amount CHECK (amount > 0),
    CONSTRAINT chk_transaction_type CHECK (
        transaction_type IN ('WITHDRAW', 'WITHDRAWAL', 'DEPOSIT', 'TRANSFER')
    ),
    CONSTRAINT chk_transaction_status CHECK (
        status IN ('SUCCESS', 'FAILED', 'PENDING')
    )
);

-- Indexes for transaction_logging
CREATE INDEX IF NOT EXISTS idx_transaction_logging_account ON transaction_logging(account_number);
CREATE INDEX IF NOT EXISTS idx_transaction_logging_type ON transaction_logging(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transaction_logging_created_at ON transaction_logging(created_at);

-- ========================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ========================================

-- Trigger for fund_transfers updated_at
CREATE OR REPLACE FUNCTION update_fund_transfers_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_fund_transfers_updated_at
BEFORE UPDATE ON fund_transfers
FOR EACH ROW
EXECUTE FUNCTION update_fund_transfers_timestamp();

-- Trigger for transaction_logging updated_at
CREATE OR REPLACE FUNCTION update_transaction_logging_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_transaction_logging_updated_at
BEFORE UPDATE ON transaction_logging
FOR EACH ROW
EXECUTE FUNCTION update_transaction_logging_timestamp();

-- ========================================
-- TABLE 3: TRANSFER LIMITS
-- ========================================
-- Stores daily and transaction limits based on privilege
CREATE TABLE IF NOT EXISTS transfer_limits (
    privilege VARCHAR(20) PRIMARY KEY,
    daily_limit NUMERIC(15, 2) NOT NULL,
    per_transaction_limit NUMERIC(15, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABLE 4: IDEMPOTENCY KEYS
-- ========================================
-- Stores the result of a money-movement request keyed by a client-supplied
-- idempotency key, so retries/replays return the original result instead of
-- executing the operation twice (prevents double-spend).
-- A key is first reserved (status IN_PROGRESS, no response yet); the response is
-- filled in and status flipped to COMPLETED once the operation finishes. A row
-- that stays IN_PROGRESS is released (deleted) if the operation fails, so the
-- client can retry.
CREATE TABLE IF NOT EXISTS idempotency_keys (
    idempotency_key VARCHAR(100) PRIMARY KEY,
    operation VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'IN_PROGRESS',
    response_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
