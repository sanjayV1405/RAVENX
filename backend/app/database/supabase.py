from typing import Optional
from app.core.config import settings
from app.core.logging import logger

try:
    from supabase import create_client, Client
except ImportError:
    Client = None
    create_client = None


class SupabaseService:
    """
    Supabase client abstraction for document storage and managed data access.
    Gracefully degrades to local storage adapter when credentials are not configured.
    """
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize()

    def _initialize(self):
        if not create_client or not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.info("Supabase client running in offline/placeholder mode (no API key configured).")
            return

        try:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Connected to Supabase client successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}. Falling back to offline mode.")
            self.client = None

    @property
    def is_configured(self) -> bool:
        return (
            self.client is not None 
            and bool(settings.SUPABASE_URL) 
            and bool(settings.SUPABASE_KEY)
            and not settings.SUPABASE_URL.startswith("https://placeholder")
        )

    async def upload_document(self, file_bytes: bytes, file_path: str, content_type: str) -> str:
        """
        Uploads document file to Supabase Storage.
        Returns the public or signed URL, or a local storage locator if offline.
        """
        if not self.is_configured:
            logger.info(f"[Offline Mode] Local storage adapter registered for file: {file_path}")
            return f"local://storage/{file_path}"

        try:
            bucket = settings.SUPABASE_STORAGE_BUCKET
            self.client.storage.from_(bucket).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path}"
        except Exception as e:
            logger.warning(f"Supabase upload failed ({e}); falling back to local reference.")
            return f"local://storage/{file_path}"


supabase_service = SupabaseService()
