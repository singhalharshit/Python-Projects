import csv, json
from io import StringIO

def parse(content: str, file_type: str):
    if file_type == "json":
        return json.loads(content)
    if file_type == "csv":
        return list(csv.DictReader(StringIO(content)))
    raise ValueError("Unsupported file type")
