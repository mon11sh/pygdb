"""
Curriculum-coverage tests.

Exercises the concepts added to close syllabus gaps:
- Module 7  (Generics):    app.utils.pagination.Page / paginate
- Module 9  (Functional):  app.utils.analytics map/filter/reduce helpers
- Module 8  (CSV I/O):     analytics.to_csv + csv.DictReader round-trip
- Module 13 (PyTest):      @pytest.mark.parametrize + fixtures
"""

import csv
import io

import pytest

from app.utils.pagination import Page, paginate
from app.utils import analytics


# --------------------------------------------------------------------------
# Module 7 — Generics: Page[T] / paginate
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "skip, limit, expected_items, expected_has_more",
    [
        (0, 2, [1, 2], True),
        (2, 2, [3, 4], True),
        (4, 2, [5], False),
        (0, 10, [1, 2, 3, 4, 5], False),
        (0, 0, [1, 2, 3, 4, 5], False),   # limit 0 == unbounded
        (10, 2, [], False),               # skip past the end
    ],
)
def test_paginate_windows(skip, limit, expected_items, expected_has_more):
    page = paginate([1, 2, 3, 4, 5], skip=skip, limit=limit)
    assert page.items == expected_items
    assert page.total == 5
    assert page.has_more is expected_has_more


def test_paginate_is_generic_over_element_type():
    page: Page[str] = paginate(["a", "b", "c"], skip=1, limit=1)
    assert isinstance(page, Page)
    assert page.items == ["b"]
    assert page.page_count == 3        # ceil(3 / 1)


@pytest.mark.parametrize("skip, limit", [(-1, 2), (0, -1)])
def test_paginate_rejects_negative(skip, limit):
    with pytest.raises(ValueError):
        paginate([1, 2, 3], skip=skip, limit=limit)


# --------------------------------------------------------------------------
# Module 9 — Functional analytics (map / filter / reduce)
# --------------------------------------------------------------------------
def _acc(number, privilege, balance, is_active=True):
    return {
        "account_number": number,
        "name": f"Account {number}",
        "privilege": privilege,
        "balance": balance,
        "is_active": is_active,
    }


@pytest.fixture
def accounts():
    return [
        _acc(1000, "GOLD", 50000, True),
        _acc(1001, "SILVER", 0, True),
        _acc(1002, "PREMIUM", 125000, False),
        _acc(1003, "GOLD", 7500, True),
    ]


@pytest.mark.parametrize(
    "sample, expected_total",
    [
        ([], 0.0),
        ([_acc(1, "GOLD", 100)], 100.0),
        ([_acc(1, "GOLD", 100), _acc(2, "SILVER", 250)], 350.0),
    ],
)
def test_total_balance(sample, expected_total):
    assert analytics.total_balance(sample) == expected_total


def test_active_accounts_filters(accounts):
    active = analytics.active_accounts(accounts)
    assert len(active) == 3
    assert all(a["is_active"] for a in active)


def test_count_by_privilege(accounts):
    assert analytics.count_by_privilege(accounts) == {
        "GOLD": 2,
        "SILVER": 1,
        "PREMIUM": 1,
    }


def test_summarize(accounts):
    summary = analytics.summarize(accounts)
    assert summary["total_accounts"] == 4
    assert summary["active_accounts"] == 3
    # active balances only: 50000 + 0 + 7500
    assert summary["total_balance"] == 57500.0
    assert summary["by_privilege"]["GOLD"] == 2


def test_analytics_reads_object_attributes():
    """account_field works on objects (attributes), not just dicts."""
    class Acct:
        privilege = "GOLD"
        balance = 200
        is_active = True

    a = Acct()
    assert analytics.total_balance([a]) == 200.0
    assert analytics.active_accounts([a]) == [a]      # same instance → list eq holds
    assert analytics.count_by_privilege([a]) == {"GOLD": 1}


# --------------------------------------------------------------------------
# Module 8 — CSV export + import round-trip
# --------------------------------------------------------------------------
def test_to_csv_roundtrip(accounts):
    text = analytics.to_csv(accounts)
    reader = csv.DictReader(io.StringIO(text))       # CSV *reading*
    rows = list(reader)
    assert len(rows) == 4
    assert rows[0]["privilege"] == "GOLD"
    assert rows[2]["is_active"] == "False"
