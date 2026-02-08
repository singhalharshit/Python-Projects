import hashlib
from sqlalchemy.orm import Session
from db.models import FileUpload, FileResult
from files.parser import parse
from files.validator import validate
from files.normalizer import normalize

def checksum(content: bytes):
    return hashlib.sha256(content).hexdigest()

def process_file(db: Session, file, user_id: int):
    content = file.file.read()
    hash_val = checksum(content)

    existing = db.query(FileUpload).filter_by(checksum=hash_val).first()
    if existing:
        return existing.id, "DUPLICATE"

    upload = FileUpload(
        filename=file.filename,
        checksum=hash_val,
        status="PROCESSING",
        uploaded_by=user_id
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    try:
        rows = parse(content.decode(), file.filename.split(".")[-1])
        valid, invalid = validate(rows)
        normalized = normalize(valid)

        result = FileResult(
            file_id=upload.id,
            success_rows=normalized,
            failed_rows=invalid
        )
        upload.status = "SUCCESS"

    except Exception as e:
        result = FileResult(
            file_id=upload.id,
            success_rows=[],
            failed_rows=[{"error": str(e)}]
        )
        upload.status = "FAILED"

    db.add(result)
    db.commit()
    return upload.id, upload.status
