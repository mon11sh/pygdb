-- ================================================================
-- Migration 002: Enforce UNIQUE(aadhar_number) on savings_account_details
--
-- Prevents the same 12-digit Aadhaar from being registered against more than
-- one savings account.
--
-- Safe to re-run: the constraint is only added if it does not already exist.
-- (Plain `ALTER TABLE ... ADD CONSTRAINT` errors if the constraint is present,
--  so it is guarded by a catalog check inside a DO block.)
-- ================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_savings_aadhar'
          AND conrelid = 'savings_account_details'::regclass
    ) THEN
        ALTER TABLE savings_account_details
            ADD CONSTRAINT uq_savings_aadhar UNIQUE (aadhar_number);
    END IF;
END
$$;
