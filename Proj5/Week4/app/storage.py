from models import ReportName,Report
from typing import Dict
from datetime import datetime


_id = 0
_report: Dict[int,Report]={}


def create_report(report_data:ReportName) -> Report:
    global _id
    _id+=1
    
    report = Report(
        id = _id,
        name = report_data.name,
        status= "Pending",
        content=None,
        created_at= datetime.utcnow().isoformat()
    )
    
    _report[report.id] = report
    return report

