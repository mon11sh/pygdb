"""
Generic, reusable pagination helpers.

Curriculum — Module 7 (Generics): demonstrates `TypeVar` and `typing.Generic`
to build a container class and a helper function that work for ANY element
type while staying fully type-checked (`Page[Account]`, `Page[str]`, ...).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

# A single type variable stands in for "whatever element type this page holds".
T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """One page of results of element type ``T`` plus its paging metadata."""

    items: list[T]
    total: int
    skip: int
    limit: int

    @property
    def has_more(self) -> bool:
        """True when more items exist beyond this page."""
        return self.skip + len(self.items) < self.total

    @property
    def page_count(self) -> int:
        """Total number of pages for the current ``limit`` (0 if unbounded)."""
        if self.limit <= 0:
            return 0
        return (self.total + self.limit - 1) // self.limit

    def as_dict(self) -> dict:
        """JSON-friendly representation for API responses."""
        return {
            "items": list(self.items),
            "total": self.total,
            "skip": self.skip,
            "limit": self.limit,
            "has_more": self.has_more,
            "page_count": self.page_count,
        }


def paginate(items: Sequence[T], skip: int = 0, limit: int = 10) -> Page[T]:
    """Slice ``items`` into a ``Page[T]``.

    Generic over ``T``: the returned page holds the same element type as the
    input sequence. A ``limit`` of 0 means "no upper bound" (everything from
    ``skip`` onward).
    """
    if skip < 0 or limit < 0:
        raise ValueError("skip and limit must be non-negative")

    total = len(items)
    window = list(items[skip: skip + limit]) if limit else list(items[skip:])
    return Page(items=window, total=total, skip=skip, limit=limit)
