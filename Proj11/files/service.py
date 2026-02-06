from sqlalchemy.orm import Session
from db.models import FileUpload, FileResult
from files.parser import parse_file

def process_file(
    db: Session,
    filename: str,
    content: str,
    file_type: str,
    user_id: int
):
    upload = FileUpload(
        filename=filename,
        file_type=file_type,
        uploaded_by=user_id
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    try:
        parsed = parse_file(content, file_type)
        result = FileResult(
            file_id=upload.id,
            normalized_data=parsed,
            error_report=None
        )
        upload.status = "SUCCESS"
    except Exception as e:
        result = FileResult(
            file_id=upload.id,
            normalized_data=None,
            error_report={"error": str(e)}
        )
        upload.status = "FAILED"

    db.add(result)
    db.commit()
    return upload.id
