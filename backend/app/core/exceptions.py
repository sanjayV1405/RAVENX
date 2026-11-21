from fastapi import HTTPException, status


class RavenXException(HTTPException):
    """Base exception for RavenX AI application errors."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class DocumentNotFoundError(RavenXException):
    def __init__(self, document_id: str):
        super().__init__(
            detail=f"Document with ID '{document_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class UnsupportedFileTypeError(RavenXException):
    def __init__(self, extension: str, allowed: list):
        super().__init__(
            detail=f"File extension '.{extension}' is not supported. Allowed formats: {', '.join(allowed)}",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )


class FileSizeLimitExceededError(RavenXException):
    def __init__(self, max_size_mb: float):
        status_code = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
        super().__init__(
            detail=f"File exceeds maximum permissible upload size limit of {max_size_mb} MB.",
            status_code=status_code
        )


class InspectionStageError(RavenXException):
    def __init__(self, stage_name: str, message: str):
        super().__init__(
            detail=f"Inspection error in stage '{stage_name}': {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

