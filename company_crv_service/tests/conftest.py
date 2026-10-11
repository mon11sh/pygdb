import sys
from pathlib import Path

import pytest

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def _bypass_internal_auth():
    from app.main import app
    from app.dependencies.internal_auth import verify_internal_api_key
    app.dependency_overrides[verify_internal_api_key] = lambda: True
    yield
    app.dependency_overrides.pop(verify_internal_api_key, None)
