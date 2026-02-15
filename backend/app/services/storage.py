"""
Supabase Storage service — handles PDF uploads and signed URL generation.
"""

from __future__ import annotations

from supabase import create_client, Client

from app.config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BUCKET_NAME = "lab-reports"


# ---------------------------------------------------------------------------
# Singleton client
# ---------------------------------------------------------------------------
_client: Client | None = None


def _get_supabase() -> Client:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set to use storage"
            )
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def upload_pdf(
    file_bytes: bytes,
    filename: str,
    user_id: str,
) -> str:
    """
    Upload a PDF to Supabase Storage.

    Args:
        file_bytes: Raw PDF content bytes.
        filename: Original filename from the user.
        user_id: Clerk user ID for namespacing.

    Returns:
        The storage path (e.g. "user_abc123/report_xyz.pdf").
    """
    # Namespace uploads by user to prevent collisions
    import uuid as _uuid

    safe_name = f"{_uuid.uuid4().hex}_{filename}"
    storage_path = f"{user_id}/{safe_name}"

    client = _get_supabase()
    client.storage.from_(BUCKET_NAME).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": "application/pdf"},
    )

    return storage_path


async def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a signed URL for downloading a stored PDF.

    Args:
        storage_path: The path returned from upload_pdf.
        expires_in: URL validity in seconds (default 1 hour).

    Returns:
        A time-limited signed URL.
    """
    client = _get_supabase()
    result = client.storage.from_(BUCKET_NAME).create_signed_url(
        path=storage_path,
        expires_in=expires_in,
    )
    return result["signedURL"]


async def delete_pdf(storage_path: str) -> None:
    """
    Delete a PDF from Supabase Storage.

    Args:
        storage_path: The path to delete.
    """
    client = _get_supabase()
    client.storage.from_(BUCKET_NAME).remove([storage_path])
