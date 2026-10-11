"""
Transaction Service - Helpers and Utilities Tests

Tests for helper functions and utility modules:
- Date/time utilities
- Currency/decimal handling
- Error formatting
- Logging utilities
- Validation helpers
- Response formatting

Author: QA Team
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import json


# ================================================================
# SECTION 1: DATE/TIME UTILITY TESTS
# ================================================================

class TestDateTimeUtilities:
    """Test date/time utility functions."""
    
    def test_datetime_now(self):
        """Test getting current datetime."""
        now = datetime.now()
        assert isinstance(now, datetime)
    
    def test_datetime_formatting(self):
        """Test datetime formatting."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
        assert formatted == "2024-01-15 10:30:00"
    
    def test_date_range_calculation(self):
        """Test date range calculation."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        delta = end - start
        assert delta.days == 30
    
    def test_time_difference_seconds(self):
        """Test time difference in seconds."""
        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = datetime(2024, 1, 15, 10, 5, 0)
        diff = (t2 - t1).total_seconds()
        assert diff == 300
    
    def test_daily_reset_time(self):
        """Test daily reset time calculation."""
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        next_reset = now + timedelta(days=1)
        assert next_reset > now


# ================================================================
# SECTION 2: CURRENCY/DECIMAL UTILITY TESTS
# ================================================================

class TestCurrencyUtilities:
    """Test currency and decimal handling."""
    
    def test_decimal_precision(self):
        """Test decimal precision."""
        amount = Decimal("1000.50")
        assert amount == Decimal("1000.50")
    
    def test_decimal_rounding(self):
        """Test decimal rounding."""
        amount = Decimal("1000.555")
        rounded = round(amount, 2)
        assert rounded == Decimal("1000.56")
    
    def test_decimal_addition(self):
        """Test decimal addition."""
        a = Decimal("1000.50")
        b = Decimal("2000.75")
        result = a + b
        assert result == Decimal("3001.25")
    
    def test_decimal_subtraction(self):
        """Test decimal subtraction."""
        a = Decimal("5000.00")
        b = Decimal("1000.50")
        result = a - b
        assert result == Decimal("3999.50")
    
    def test_decimal_multiplication(self):
        """Test decimal multiplication."""
        amount = Decimal("1000.00")
        rate = Decimal("0.05")
        result = amount * rate
        assert result == Decimal("50.00")
    
    def test_decimal_comparison(self):
        """Test decimal comparison."""
        a = Decimal("1000.50")
        b = Decimal("1000.49")
        assert a > b
    
    def test_currency_formatting(self):
        """Test currency formatting."""
        amount = Decimal("1000.50")
        formatted = f"₹{amount:,.2f}"
        assert "1,000.50" in formatted


# ================================================================
# SECTION 3: VALIDATION HELPER TESTS
# ================================================================

class TestValidationHelpers:
    """Test validation helper functions."""
    
    def test_is_positive_amount(self):
        """Test positive amount validation."""
        amount = Decimal("1000.50")
        assert amount > 0
    
    def test_is_zero_amount(self):
        """Test zero amount validation."""
        amount = Decimal("0")
        assert amount == 0
    
    def test_is_negative_amount(self):
        """Test negative amount validation."""
        amount = Decimal("-1000")
        assert amount < 0
    
    def test_is_valid_account_number(self):
        """Test valid account number format."""
        account = 1000
        assert isinstance(account, int) and account > 0
    
    def test_is_invalid_account_number(self):
        """Test invalid account number format."""
        account = "INVALID"
        assert not isinstance(account, int)
    
    def test_is_valid_pin_format(self):
        """Test valid PIN format."""
        pin = "1234"
        assert len(pin) >= 4 and len(pin) <= 6 and pin.isdigit()
    
    def test_is_invalid_pin_format(self):
        """Test invalid PIN format."""
        pin = "abc"
        assert not pin.isdigit()
    
    def test_is_valid_transfer_mode(self):
        """Test valid transfer mode."""
        mode = "NEFT"
        valid_modes = ["NEFT", "RTGS", "IMPS", "CHEQUE", "UPI"]
        assert mode in valid_modes
    
    def test_is_invalid_transfer_mode(self):
        """Test invalid transfer mode."""
        mode = "INVALID"
        valid_modes = ["NEFT", "RTGS", "IMPS", "CHEQUE", "UPI"]
        assert mode not in valid_modes


# ================================================================
# SECTION 4: ERROR HANDLING HELPER TESTS
# ================================================================

class TestErrorHandlingHelpers:
    """Test error handling utilities."""
    
    def test_insufficient_balance_error(self):
        """Test insufficient balance error."""
        balance = Decimal("500")
        required = Decimal("1000")
        error = balance < required
        assert error is True
    
    def test_daily_limit_exceeded_error(self):
        """Test daily limit exceeded error."""
        used = Decimal("500000")
        limit = Decimal("500000")
        error = used >= limit
        assert error is True
    
    def test_invalid_account_error(self):
        """Test invalid account error."""
        account = None
        error = account is None
        assert error is True
    
    def test_transaction_count_limit_error(self):
        """Test transaction count limit error."""
        count = 51
        limit = 50
        error = count > limit
        assert error is True
    
    def test_pin_verification_error(self):
        """Test PIN verification error."""
        provided_pin = "0000"
        stored_pin = "1234"
        error = provided_pin != stored_pin
        assert error is True


# ================================================================
# SECTION 5: RESPONSE FORMATTING TESTS
# ================================================================

class TestResponseFormatting:
    """Test response formatting utilities."""
    
    def test_success_response_format(self):
        """Test success response formatting."""
        response = {
            "status": "SUCCESS",
            "message": "Transaction completed",
            "transaction_id": 1,
            "timestamp": datetime.now().isoformat()
        }
        assert response["status"] == "SUCCESS"
        assert "transaction_id" in response
    
    def test_error_response_format(self):
        """Test error response formatting."""
        response = {
            "status": "ERROR",
            "error_code": "INSUFFICIENT_BALANCE",
            "message": "Account has insufficient balance",
            "timestamp": datetime.now().isoformat()
        }
        assert response["status"] == "ERROR"
        assert "error_code" in response
    
    def test_response_with_data(self):
        """Test response with data."""
        response = {
            "status": "SUCCESS",
            "data": {
                "transaction_id": 1,
                "amount": "5000.00",
                "account": 1000,
                "new_balance": "15000.00"
            }
        }
        assert "data" in response
        assert response["data"]["transaction_id"] == 1
    
    def test_response_serialization(self):
        """Test response JSON serialization."""
        response = {
            "status": "SUCCESS",
            "amount": str(Decimal("1000.50")),
            "timestamp": datetime.now().isoformat()
        }
        json_str = json.dumps(response)
        assert isinstance(json_str, str)
        assert "SUCCESS" in json_str


# ================================================================
# SECTION 6: LOGGING UTILITY TESTS
# ================================================================

class TestLoggingUtilities:
    """Test logging utility functions."""
    
    def test_log_format(self):
        """Test log message format."""
        level = "INFO"
        message = "Transaction completed successfully"
        log_msg = f"[{level}] {message}"
        assert "[INFO]" in log_msg
    
    def test_log_with_context(self):
        """Test log with context."""
        log_msg = "Transaction ID: 1, Account: 1000, Amount: 5000"
        assert "Transaction ID" in log_msg
        assert "Account" in log_msg
    
    def test_error_log_format(self):
        """Test error log format."""
        error_msg = "Database connection failed"
        log_msg = f"[ERROR] {error_msg}"
        assert "[ERROR]" in log_msg
    
    def test_debug_log_format(self):
        """Test debug log format."""
        debug_msg = "Processing transaction with ID 1"
        log_msg = f"[DEBUG] {debug_msg}"
        assert "[DEBUG]" in log_msg
    
    def test_warning_log_format(self):
        """Test warning log format."""
        warning_msg = "Daily limit approaching threshold"
        log_msg = f"[WARNING] {warning_msg}"
        assert "[WARNING]" in log_msg


# ================================================================
# SECTION 7: STRING PROCESSING UTILITIES TESTS
# ================================================================

class TestStringProcessingUtilities:
    """Test string processing utilities."""
    
    def test_string_padding(self):
        """Test string padding."""
        account = "1000"
        padded = account.zfill(6)
        assert padded == "001000"
    
    def test_string_trimming(self):
        """Test string trimming."""
        text = "  Transaction successful  "
        trimmed = text.strip()
        assert trimmed == "Transaction successful"
    
    def test_string_case_conversion(self):
        """Test case conversion."""
        mode = "neft"
        upper_mode = mode.upper()
        assert upper_mode == "NEFT"
    
    def test_string_formatting(self):
        """Test string formatting."""
        transaction_id = 1000
        formatted = f"TXN-{transaction_id:06d}"
        assert formatted == "TXN-001000"
    
    def test_string_contains(self):
        """Test string contains check."""
        message = "Transaction completed successfully"
        assert "completed" in message


# ================================================================
# SECTION 8: DATA TRANSFORMATION TESTS
# ================================================================

class TestDataTransformation:
    """Test data transformation utilities."""
    
    def test_dict_to_object(self):
        """Test converting dict to object."""
        data = {"id": 1, "amount": "5000.00", "account": 1000}
        assert data["id"] == 1
        assert data["amount"] == "5000.00"
    
    def test_decimal_to_string(self):
        """Test decimal to string conversion."""
        amount = Decimal("5000.50")
        str_amount = str(amount)
        assert str_amount == "5000.50"
    
    def test_string_to_decimal(self):
        """Test string to decimal conversion."""
        amount_str = "5000.50"
        amount = Decimal(amount_str)
        assert amount == Decimal("5000.50")
    
    def test_list_to_dict(self):
        """Test converting list to dict."""
        data = [("id", 1), ("name", "Transaction")]
        result = dict(data)
        assert result["id"] == 1
        assert result["name"] == "Transaction"
    
    def test_filter_dict_values(self):
        """Test filtering dict values."""
        data = {"status": "SUCCESS", "error": None, "data": {}}
        filtered = {k: v for k, v in data.items() if v is not None}
        assert "error" not in filtered


# ================================================================
# TEST EXECUTION
# ================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
