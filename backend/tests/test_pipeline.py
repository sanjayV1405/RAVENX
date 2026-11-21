import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal
from app.services.document_service import DocumentService
from app.services.inspection_service import InspectionService

async def main():
    print("Initializing test...", flush=True)
    db = SessionLocal()
    try:
        print("Uploading document...", flush=True)
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_multipage.pdf")
        with open(fixture_path, "rb") as f:
            pdf_bytes = f.read()

        doc, is_duplicate = await DocumentService.upload_document(
            db=db,
            filename="enterprise_agreement.pdf",
            file_bytes=pdf_bytes
        )
        print(f"Document uploaded: {doc.filename} (ID: {doc.id}, is_duplicate: {is_duplicate})", flush=True)

        print("Executing inspection...", flush=True)
        inspection = await InspectionService.create_inspection(
            db=db,
            document_id=doc.id,
            ai_provider="deepseek",
            user_guidelines="Strict table alignment check"
        )
        print(f"Inspection executed: Status={inspection.status}, Stage={inspection.current_stage}", flush=True)
        print(f"Report Summary: {inspection.summary}", flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
    finally:
        db.close()
        print("Test finished successfully.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())

