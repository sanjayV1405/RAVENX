from typing import Optional
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.corrected_document import CorrectedDocumentResponse, ApplyCorrectionRequest
from app.correction_engine.correction_service import CorrectionService
from app.models.finding import Finding
from app.core.exceptions import RavenXException

router = APIRouter()


@router.post(
    "/inspections/{inspection_id}/correct",
    response_model=CorrectedDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Corrected Document",
    description="Applies accepted findings to generate a brand new corrected document in the original format without modifying the source."
)
def generate_corrected_document(
    inspection_id: str,
    payload: Optional[ApplyCorrectionRequest] = None,
    db: Session = Depends(get_db)
):
    selected_ids = payload.selected_finding_ids if payload else None
    corr_doc = CorrectionService.apply_corrections(
        db=db,
        inspection_id=inspection_id,
        selected_finding_ids=selected_ids
    )
    
    response_data = CorrectedDocumentResponse.model_validate(corr_doc)
    response_data.download_url = f"/api/v1/inspections/{inspection_id}/corrected/download"
    return response_data


@router.get(
    "/inspections/{inspection_id}/corrected",
    response_model=CorrectedDocumentResponse,
    summary="Get Corrected Document Metadata"
)
def get_corrected_document_info(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    corr_doc = CorrectionService.get_corrected_document(db, inspection_id)
    if not corr_doc:
        raise RavenXException(detail="No corrected document generated yet for this inspection.", status_code=404)

    response_data = CorrectedDocumentResponse.model_validate(corr_doc)
    response_data.download_url = f"/api/v1/inspections/{inspection_id}/corrected/download"
    return response_data


@router.get(
    "/inspections/{inspection_id}/corrected/download",
    summary="Download Corrected Document",
    description="Downloads the newly generated, corrected document binary in its original file format."
)
def download_corrected_document(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    file_bytes, filename, mime_type = CorrectionService.get_corrected_document_bytes(db, inspection_id)
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(file_bytes)),
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@router.get(
    "/inspections/{inspection_id}/corrected/preview",
    summary="Inline Preview of Corrected Document",
    description="Serves the corrected document inline for in-browser visual inspection."
)
def preview_corrected_document(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    file_bytes, filename, mime_type = CorrectionService.get_corrected_document_bytes(db, inspection_id)
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Content-Length": str(len(file_bytes)),
        }
    )


@router.post(
    "/inspections/{inspection_id}/accept-all",
    summary="Accept All Detected Findings",
    description="Batch accepts all detected findings for an inspection, readying them for one-click correction."
)
def accept_all_findings(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    count = db.query(Finding).filter(
        Finding.inspection_id == inspection_id
    ).update({"user_status": "accepted"}, synchronize_session=False)
    db.commit()
    return {"message": f"Successfully accepted {count} findings.", "accepted_count": count}


@router.post(
    "/inspections/{inspection_id}/reject-all",
    summary="Reject All Detected Findings",
    description="Batch rejects all detected findings for an inspection."
)
def reject_all_findings(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    count = db.query(Finding).filter(
        Finding.inspection_id == inspection_id
    ).update({"user_status": "rejected"}, synchronize_session=False)
    db.commit()
    return {"message": f"Successfully rejected {count} findings.", "rejected_count": count}
