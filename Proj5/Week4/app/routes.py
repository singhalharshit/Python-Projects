from fastapi import APIRouter
from models import ReportName, Report
from storage import create_report

router = APIRouter()

@router.post('/reports')
def create_reports(report_name:ReportName) -> Report:
    return create_report(report_name)
    