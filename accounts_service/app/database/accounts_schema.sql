-- ================================================================
-- ACCOUNTS SERVICE DATABASE SCHEMA
-- Database: gdb_accounts_db
-- Purpose: Manage accounts, balances, and account details
-- ================================================================

-- ================================================================
-- ENUM TYPES
-- ================================================================
CREATE TYPE gender_enum AS ENUM ('Male', 'Female', 'Others');

-- ================================================================
-- MAIN ACCOUNTS TABLE
-- ================================================================
CREATE TABLE accounts (
    id BIGSERIAL PRIMARY KEY,
    account_number BIGSERIAL UNIQUE NOT NULL,
    account_type VARCHAR(10) NOT NULL CHECK (account_type IN ('SAVINGS', 'CURRENT')),
    name VARCHAR(255) NOT NULL,
    pin_hash VARCHAR(255) NOT NULL,
    balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0),
    privilege VARCHAR(10) NOT NULL CHECK (privilege IN ('PREMIUM', 'GOLD', 'SILVER')),
    bank_name VARCHAR(255) NOT NULL DEFAULT 'Global Digital Bank',
    bank_branch VARCHAR(255) NOT NULL DEFAULT 'Main Branch',
    ifsc_code VARCHAR(20) NOT NULL DEFAULT 'GDB0000001',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    activated_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for active accounts
CREATE INDEX IF NOT EXISTS idx_accounts_is_active ON accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_accounts_account_type ON accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_accounts_privilege ON accounts(privilege);
CREATE INDEX IF NOT EXISTS idx_accounts_account_number ON accounts(account_number);

-- ================================================================
-- SAVINGS ACCOUNT DETAILS TABLE
-- Specific to SAVINGS accounts
-- ================================================================
CREATE TABLE savings_account_details (
    id BIGSERIAL PRIMARY KEY,
    account_number BIGINT NOT NULL UNIQUE REFERENCES accounts(account_number) ON DELETE CASCADE,
    date_of_birth DATE NOT NULL,
    gender gender_enum NOT NULL,
    phone_no VARCHAR(20) NOT NULL,
    aadhar_number VARCHAR(12) NOT NULL UNIQUE CHECK (LENGTH(aadhar_number) = 12 AND aadhar_number ~ '^[0-9]{12}$'),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for date of birth (age verification queries)
CREATE INDEX IF NOT EXISTS idx_savings_dob ON savings_account_details(date_of_birth);
CREATE INDEX IF NOT EXISTS idx_savings_phone ON savings_account_details(phone_no);
CREATE INDEX IF NOT EXISTS idx_savings_account_number ON savings_account_details(account_number);


-- ================================================================
-- CURRENT ACCOUNT DETAILS TABLE
-- Specific to CURRENT accounts
-- ================================================================
CREATE TABLE current_account_details (
    id BIGSERIAL PRIMARY KEY,
    account_number BIGINT NOT NULL UNIQUE REFERENCES accounts(account_number) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    website VARCHAR(255),
    registration_no VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for registration lookup
CREATE INDEX IF NOT EXISTS idx_current_registration ON current_account_details(registration_no);
CREATE INDEX IF NOT EXISTS idx_current_account_number ON current_account_details(account_number);

-- ================================================================
-- SEQUENCES FOR ACCOUNT NUMBER GENERATION
-- Start from 1000 instead of 1
-- ================================================================
CREATE SEQUENCE account_number_seq START WITH 1000 INCREMENT BY 1;

-- ================================================================
-- FUNCTION TO UPDATE updated_at TIMESTAMP
-- ================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER accounts_update_timestamp BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER savings_details_update_timestamp BEFORE UPDATE ON savings_account_details
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER current_details_update_timestamp BEFORE UPDATE ON current_account_details
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================================
-- VIEW FOR ACCOUNT SUMMARY
-- Combines account info with type-specific details
-- ================================================================
CREATE VIEW account_summary AS
SELECT 
    a.account_number,
    a.account_type,
    a.name,
    a.balance,
    a.privilege,
    a.is_active,
    a.activated_date,
    a.closed_date,
    CASE 
        WHEN a.account_type = 'SAVINGS' THEN s.date_of_birth
        ELSE NULL 
    END AS date_of_birth,
    CASE 
        WHEN a.account_type = 'SAVINGS' THEN s.phone_no
        ELSE NULL 
    END AS phone_no,
    CASE 
        WHEN a.account_type = 'CURRENT' THEN c.company_name
        ELSE NULL 
    END AS company_name,
    CASE 
        WHEN a.account_type = 'CURRENT' THEN c.registration_no
        ELSE NULL 
    END AS registration_no
FROM accounts a
LEFT JOIN savings_account_details s ON a.account_number = s.account_number
LEFT JOIN current_account_details c ON a.account_number = c.account_number;

-- ================================================================
-- END OF ACCOUNTS SCHEMA
-- ================================================================
