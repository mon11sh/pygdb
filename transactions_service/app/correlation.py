"""Correlation context — re-exported from the shared gdb_common package.

Kept as app.correlation so the integration/httpx clients keep importing it while
the actual context lives in gdb_common (Phase 3.1)."""

from gdb_common.observability import (  # noqa: F401
    correlation_id_ctx,
    current_correlation_id,
    new_correlation_id,
)
