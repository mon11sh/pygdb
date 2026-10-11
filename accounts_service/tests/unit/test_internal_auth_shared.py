"""Shared internal-API-key verifier tests (gdb_common, Phase 3.1 / C-2)."""

import pytest
from fastapi import HTTPException

from gdb_common.internal_auth import make_internal_api_key_verifier


@pytest.fixture
def verify():
    return make_internal_api_key_verifier(lambda: "correct-key")


async def test_accepts_correct_key(verify):
    assert await verify("correct-key") is True


@pytest.mark.parametrize("bad", [None, "", "wrong-key"])
async def test_rejects_bad_key(verify, bad):
    with pytest.raises(HTTPException) as exc:
        await verify(bad)
    assert exc.value.status_code == 401
