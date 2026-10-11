"""
Read-only account analytics in a functional-programming style.

Curriculum — Module 9 (Functional Programming): derives summaries from a
collection of accounts using ``map`` / ``filter`` / ``reduce`` and ``lambda``
instead of imperative loops. Also covers Module 8 (structured data) via CSV
export/import helpers.
"""

from __future__ import annotations

import csv
import io
from functools import reduce
from typing import Any, Iterable


def account_field(account: Any, name: str, default: Any = None) -> Any:
    """Read a field from an account whether it is a dict or an object.

    Keeps the functional helpers below agnostic to how accounts are shaped
    (repositories return ``AccountDetailsResponse`` objects; tests may pass
    plain dicts).
    """
    if isinstance(account, dict):
        return account.get(name, default)
    return getattr(account, name, default)


def active_accounts(accounts: Iterable[Any]) -> list[Any]:
    """``filter`` — keep only the active accounts."""
    return list(filter(lambda a: bool(account_field(a, "is_active", False)), accounts))


def total_balance(accounts: Iterable[Any]) -> float:
    """``map`` + ``reduce`` — sum the balances across accounts."""
    balances = map(lambda a: float(account_field(a, "balance", 0) or 0), accounts)
    return reduce(lambda running, amount: running + amount, balances, 0.0)


def count_by_privilege(accounts: Iterable[Any]) -> dict[str, int]:
    """``reduce`` — fold the accounts into a ``{privilege: count}`` histogram."""

    def tally(counts: dict[str, int], account: Any) -> dict[str, int]:
        """Accumulate one account into the running privilege histogram.

        Args:
            counts: The accumulator mapping privilege label to running count.
            account: The account whose ``privilege`` field is tallied.

        Returns:
            The same ``counts`` mapping with this account's privilege
            incremented (``"UNKNOWN"`` when the field is absent).
        """
        key = str(account_field(account, "privilege", "UNKNOWN"))
        counts[key] = counts.get(key, 0) + 1
        return counts

    return reduce(tally, accounts, {})


def summarize(accounts: list[Any]) -> dict[str, Any]:
    """Combine the functional helpers into one portfolio summary."""
    active = active_accounts(accounts)
    return {
        "total_accounts": len(accounts),
        "active_accounts": len(active),
        "total_balance": round(total_balance(active), 2),
        "by_privilege": count_by_privilege(accounts),
    }


def to_csv(accounts: Iterable[Any]) -> str:
    """Export accounts as CSV text (Module 8: structured data handling)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["account_number", "name", "privilege", "balance", "is_active"])
    rows = map(
        lambda a: [
            account_field(a, "account_number"),
            account_field(a, "name"),
            account_field(a, "privilege"),
            account_field(a, "balance"),
            account_field(a, "is_active"),
        ],
        accounts,
    )
    writer.writerows(rows)
    return buffer.getvalue()
