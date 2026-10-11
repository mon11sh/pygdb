"""
Notification Storage Service - Async File-based Storage

Handles persistent storage of notifications using async file I/O.
Uses aiofiles for non-blocking file operations.

Author: GDB Architecture Team
"""

import json
import os
import html
import asyncio
import aiofiles
import aiofiles.os
from typing import List, Dict
from datetime import datetime
from app.config.settings import settings

DATA_FILE = settings.DATA_FILE

# Defense-in-depth bounds for stored fields (stored-XSS / abuse mitigation).
MAX_MESSAGE_LENGTH = 2000
MAX_RECIPIENT_LENGTH = 255

# NOTE (deferred / known remaining item): notifications are persisted in
# plaintext to `data/notifications.json`. PII-at-rest encryption for this file
# is a known remaining hardening item and is intentionally deferred here.


class NotificationStorage:
    """
    Async storage service for notifications.
    Uses aiofiles for non-blocking file I/O operations.
    """

    def __init__(self):
        """Initialize the storage backend.

        Creates the async lock that serializes read-modify-write cycles and
        ensures the data directory and notifications file exist before any
        request is served.
        """
        # Serializes read-modify-write cycles so concurrent add/clear/mark_all
        # operations within this process cannot race and lose data.
        self._lock = asyncio.Lock()
        # Ensure data directory exists synchronously at startup
        self._ensure_file_sync()

    def _ensure_file_sync(self):
        """Synchronous file check for initialization."""
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f:
                json.dump([], f)

    async def _ensure_file(self):
        """Async file check and creation."""
        if not await aiofiles.os.path.exists("data"):
            os.makedirs("data")
        if not await aiofiles.os.path.exists(DATA_FILE):
            async with aiofiles.open(DATA_FILE, "w") as f:
                await f.write(json.dumps([]))

    async def _read_data(self) -> List[Dict]:
        """Async read data from file."""
        try:
            async with aiofiles.open(DATA_FILE, "r") as f:
                content = await f.read()
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    async def _write_data(self, data: List[Dict]):
        """
        Async write data to file atomically.

        Writes to a temp file in the same directory and then os.replace() onto
        the target. os.replace is atomic on the same filesystem, so a crash mid
        write can never leave a truncated/partial notifications.json.
        """
        serialized = json.dumps(data, indent=2)
        directory = os.path.dirname(DATA_FILE) or "."
        tmp_path = f"{DATA_FILE}.{os.getpid()}.tmp"
        async with aiofiles.open(tmp_path, "w") as f:
            await f.write(serialized)
            await f.flush()
        # Atomically swap the fully-written temp file into place.
        os.replace(tmp_path, DATA_FILE)

    def _sanitize_message(self, message: str) -> str:
        """
        Escape angle brackets (and other HTML-significant chars) and bound the
        length before storing, so a stored message can't inject markup if the
        frontend ever renders it as HTML. Normal text (₹, letters, digits,
        parentheses, spaces) is left intact by html.escape.
        """
        if message is None:
            return message
        escaped = html.escape(message)
        return escaped[:MAX_MESSAGE_LENGTH]

    async def add_notification(self, recipient: str, message: str, type: str, mode: str = None):
        """Async add a new notification."""
        # Sanitize/bound untrusted fields (stored-XSS defense-in-depth).
        message = self._sanitize_message(message)
        if recipient is not None:
            recipient = recipient[:MAX_RECIPIENT_LENGTH]
        async with self._lock:
            data = await self._read_data()
            # Derive the next id from the current max so ids stay unique even after
            # some notifications have been cleared (len()+1 would collide).
            next_id = (max((n.get("id", 0) for n in data), default=0)) + 1
            new_note = {
                "id": next_id,
                "recipient": recipient,
                "message": message,
                "type": type,
                "mode": mode,
                "timestamp": datetime.now().isoformat(),
                "read": False
            }
            data.append(new_note)
            await self._write_data(data)

    async def get_notifications(self, recipient: str) -> List[Dict]:
        """Async get notifications for a specific recipient."""
        data = await self._read_data()
        # Filter by recipient (Account Number or Email)
        return [n for n in data if n["recipient"] == recipient]

    async def mark_all_as_read(self, recipient: str):
        """Async mark all notifications as read for a recipient."""
        async with self._lock:
            data = await self._read_data()
            for n in data:
                if n["recipient"] == recipient:
                    n["read"] = True
            await self._write_data(data)

    async def clear_notifications(self, recipient: str):
        """Async clear all notifications for a recipient."""
        async with self._lock:
            data = await self._read_data()
            # Keep only notifications that DON'T belong to this recipient
            filtered_data = [n for n in data if n["recipient"] != recipient]
            await self._write_data(filtered_data)


storage = NotificationStorage()
