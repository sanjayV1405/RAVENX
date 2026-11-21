import os
from typing import Dict, Any
from app.utils.file_validators import validate_file_metadata, calculate_sha256
from app.core.logging import logger


class IngestionStage:
    """
    Stage 1: Document Ingestion & Validation
    - Validates file integrity, signature, and size constraints.
    - Computes checksum to guarantee document immutability.
    - Resolves metadata for downstream extraction stages.
    """

    @classmethod
    async def process(cls, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        logger.info(f"[Pipeline Stage 1: Ingestion] Validating document: {filename}")
        file_size = len(file_bytes)
        ext, mime_type = validate_file_metadata(filename, file_size)
        checksum = calculate_sha256(file_bytes)

        return {
            "filename": filename,
            "extension": ext,
            "mime_type": mime_type,
            "size_bytes": file_size,
            "checksum": checksum,
            "status": "validated",
        }

