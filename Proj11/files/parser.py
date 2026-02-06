import json
import csv
import xml.etree.ElementTree as ET
from io import StringIO

def parse_file(content: str, file_type: str):
    if file_type == "json":
        return json.loads(content)

    if file_type == "csv":
        reader = csv.DictReader(StringIO(content))
        return list(reader)

    if file_type == "xml":
        root = ET.fromstring(content)
        return [{child.tag: child.text for child in root}]

    raise ValueError("Unsupported file type")
