from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from files.service import process_file
from core.dependencies import require_roles

router = APIRouter(prefix="/files", tags=["Files"])

@router.post(
    "/upload",
    dependencies=[Depends(require_roles(["admin", "operator"]))]
)
def upload(
    file: UploadFile,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "operator"]))
):
    file_id, status = process_file(db, file, user_id=1)
    return {"file_id": file_id, "status": status}
