"""FastAPI dependency providers for the transactions service.

Wires the service layer to the active persistence backend: repository providers
resolve the concrete repositories from the configured database provider, and the
service factories inject those repositories into deposit, withdraw, transfer,
transaction-log, and transfer-limit services for use as route `Depends(...)`.
"""

from fastapi import Depends
from app.repositories.transaction_repository import (
    TransactionRepositoryInterface as FundTransferRepository,
)
from app.repositories.transaction_log_repository import TransactionLogRepositoryInterface
from app.repositories.transfer_limit_repository import TransferLimitRepositoryInterface
from app.services.transfer_service import TransferService as FundTransferService
from app.services.deposit_service import DepositService
from app.services.withdraw_service import WithdrawService
from app.services.transaction_log_service import TransactionLogService
from app.services.transfer_limit_service import TransferLimitService


def get_fund_transfer_repository() -> FundTransferRepository:
    """Resolve the TransactionRepository from the active database provider
    (chosen by settings.DATABASE_PROVIDER). Imported lazily so selecting a
    non-SQL provider never loads SQLAlchemy."""
    from app.database.db import get_provider
    return get_provider().transaction_repository()


def get_transaction_log_repository() -> TransactionLogRepositoryInterface:
    """Resolve the TransactionLogRepository from the active database provider."""
    from app.database.db import get_provider
    return get_provider().transaction_log_repository()


def get_transfer_limit_repository() -> TransferLimitRepositoryInterface:
    """Resolve the TransferLimitRepository from the active database provider."""
    from app.database.db import get_provider
    return get_provider().transfer_limit_repository()


def get_fund_transfer_service(
    repo: FundTransferRepository = Depends(get_fund_transfer_repository),
    log_repo: TransactionLogRepositoryInterface = Depends(get_transaction_log_repository),
    limit_repo: TransferLimitRepositoryInterface = Depends(get_transfer_limit_repository),
) -> FundTransferService:
    """Build a TransferService wired to the transaction, log, and limit repositories.

    Args:
        repo: Transaction repository for the active provider.
        log_repo: Transaction log repository for the active provider.
        limit_repo: Transfer limit repository for the active provider.

    Returns:
        A configured TransferService instance.
    """
    return FundTransferService(repo, log_repo, limit_repo)


def get_deposit_service(
    log_repo: TransactionLogRepositoryInterface = Depends(get_transaction_log_repository)
) -> DepositService:
    """Build a DepositService wired to the transaction log repository.

    Args:
        log_repo: Transaction log repository for the active provider.

    Returns:
        A configured DepositService instance.
    """
    return DepositService(log_repo)


def get_withdraw_service(
    log_repo: TransactionLogRepositoryInterface = Depends(get_transaction_log_repository)
) -> WithdrawService:
    """Build a WithdrawService wired to the transaction log repository.

    Args:
        log_repo: Transaction log repository for the active provider.

    Returns:
        A configured WithdrawService instance.
    """
    return WithdrawService(log_repo)


def get_transaction_log_service(
    repo: TransactionLogRepositoryInterface = Depends(get_transaction_log_repository)
) -> TransactionLogService:
    """Build a TransactionLogService wired to the transaction log repository.

    Args:
        repo: Transaction log repository for the active provider.

    Returns:
        A configured TransactionLogService instance.
    """
    return TransactionLogService(repo)


def get_transfer_limit_service(
    repo: TransferLimitRepositoryInterface = Depends(get_transfer_limit_repository)
) -> TransferLimitService:
    """Build a TransferLimitService wired to the transfer limit repository.

    Args:
        repo: Transfer limit repository for the active provider.

    Returns:
        A configured TransferLimitService instance.
    """
    return TransferLimitService(repo)
