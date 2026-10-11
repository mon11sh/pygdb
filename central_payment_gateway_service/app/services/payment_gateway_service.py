"""Service layer for the Central Payment Gateway.

Implements :class:`PaymentGatewayService`, a simulated third-party payment
gateway that processes payments (with idempotent replays, simulated latency,
and simulated random failures) and performs lightweight transfer validation.
Money is handled as ``Decimal`` and every outcome is audit-logged.
"""
import asyncio
import uuid
import random
import logging
from decimal import Decimal, ROUND_HALF_UP
from app.models.payment import (
    PaymentRequest,
    PaymentResponse,
    ValidationRequest,
    ValidationResponse,
)

# Audit logger for the payment gateway. Logs processed payments and rejections.
# No secrets/PII beyond the account ids and amount that the caller already owns.
logger = logging.getLogger("PaymentGatewayService")
if not logging.getLogger().handlers and not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Two-decimal money quantum for amount normalization.
_TWO_PLACES = Decimal("0.01")


class PaymentGatewayService:
    """Simulated third-party payment gateway.

    Provides a second-level validation and processing layer for transfers in the
    GDB ecosystem. Responsibilities:

    * Process payments with idempotent replay keyed by ``reference_id``.
    * Simulate real-world behaviour (network latency and occasional failures).
    * Reject invalid transfers (e.g. identical source/destination accounts).
    * Provide a lightweight, non-mutating validation check for the frontend.

    Note:
        The idempotency cache is an in-memory, per-process class attribute; a
        production deployment must back it with a shared/durable store so
        retries are deduped across instances and restarts.
    """

    # Per-process idempotency cache: reference_id -> PaymentResponse.
    # Declared at class scope on purpose: the FastAPI provider builds a fresh
    # PaymentGatewayService per request, so a shared (class-level) dict is what
    # lets retries with the same reference_id be deduped across requests.
    # NOTE: This is in-memory and per-process only. A production gateway must
    # back this with a shared/durable store (e.g. Redis/DB) so retries are
    # deduped across instances and restarts.
    _processed: dict = {}

    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Process a payment request and return its outcome.

        Replays a cached response for a previously seen ``reference_id`` to
        guarantee idempotency. Otherwise it simulates network latency, normalizes
        the amount to two decimal places, rejects transfers whose source and
        destination accounts are identical, simulates a rare gateway failure, and
        finally reports success. Every terminal outcome is audit-logged and, when
        a ``reference_id`` is present, cached for future replays.

        Args:
            request: The validated payment request to process.

        Returns:
            PaymentResponse: The processing result (success or failure) with a
            transaction id and gateway reference id.
        """
        # Idempotency: if we've already processed this reference_id, replay the
        # exact same response instead of processing (charging) again.
        if request.reference_id and request.reference_id in self._processed:
            logger.info(
                "[IDEMPOTENT REPLAY] reference_id=%s returning cached response",
                request.reference_id,
            )
            return self._processed[request.reference_id]

        # Simulate network latency (100ms - 500ms)
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Normalize money to 2 decimal places (amount is a Decimal, never float).
        amount = Decimal(request.amount).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        mode = request.mode.value if hasattr(request.mode, "value") else request.mode

        # 1. Basic Validation Logic
        # NOTE: amount > 0, upper bound, positive account ids and a valid mode are
        # now enforced by Pydantic on PaymentRequest (422 before we get here), so
        # the old manual `amount <= 0` check has been removed as dead code.
        if request.source_account_id == request.destination_account_id:
            response = PaymentResponse(
                success=False,
                transaction_id=request.reference_id or str(uuid.uuid4()),
                message="Invalid Transaction: Source and Destination cannot be same",
                gateway_ref_id=str(uuid.uuid4())
            )
            logger.warning(
                "[PAYMENT REJECTED] reference_id=%s source=%s dest=%s amount=%s mode=%s result=%s",
                request.reference_id, request.source_account_id,
                request.destination_account_id, amount, mode, response.message,
            )
            return self._remember(request.reference_id, response)

        # 2. Simulate Random Network Failures (1% chance)
        # In a real scenario, this would check against blacklists, fraud detection, etc.
        if random.random() < 0.01:
            response = PaymentResponse(
                success=False,
                transaction_id=request.reference_id or str(uuid.uuid4()),
                message="Gateway Error: Network Timeout",
                gateway_ref_id=str(uuid.uuid4())
            )
            logger.warning(
                "[PAYMENT REJECTED] reference_id=%s source=%s dest=%s amount=%s mode=%s result=%s",
                request.reference_id, request.source_account_id,
                request.destination_account_id, amount, mode, response.message,
            )
            return self._remember(request.reference_id, response)

        # 3. Success
        response = PaymentResponse(
            success=True,
            transaction_id=request.reference_id or str(uuid.uuid4()),
            message="Payment Processed Successfully",
            gateway_ref_id=str(uuid.uuid4())
        )
        logger.info(
            "[PAYMENT PROCESSED] reference_id=%s source=%s dest=%s amount=%s mode=%s result=%s",
            request.reference_id, request.source_account_id,
            request.destination_account_id, amount, mode, response.message,
        )
        return self._remember(request.reference_id, response)

    async def validate_transfer(self, request: ValidationRequest) -> ValidationResponse:
        """Second-level sanity check the frontend calls around a transfer. Purely a
        mock validation: it does NOT move money, charge, or dedupe. Amount and
        account bounds are already enforced by Pydantic (422 before we get here)."""
        valid = request.from_account != request.to_account
        message = (
            "Validation passed"
            if valid
            else "Invalid: source and destination cannot be the same"
        )
        logger.info(
            "[PAYMENT VALIDATED] transaction_id=%s from=%s to=%s amount=%s valid=%s",
            request.transaction_id, request.from_account,
            request.to_account, request.amount, valid,
        )
        return ValidationResponse(
            valid=valid, message=message, transaction_id=request.transaction_id
        )

    def _remember(self, reference_id, response: PaymentResponse) -> PaymentResponse:
        """Cache the response under its reference_id for idempotent replays."""
        if reference_id:
            self._processed[reference_id] = response
        return response


payment_service = PaymentGatewayService()
