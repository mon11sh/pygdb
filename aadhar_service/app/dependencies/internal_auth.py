"""Inter-service authentication dependency (shared key via gdb_common, M-3)."""
from app.config.settings import settings
from gdb_common.internal_auth import make_internal_api_key_verifier

# Preserves `from app.dependencies.internal_auth import verify_internal_api_key`.
verify_internal_api_key = make_internal_api_key_verifier(lambda: settings.INTERNAL_API_KEY)
