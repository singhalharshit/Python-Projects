REQUIRED_FIELDS = {"id", "name", "value"}

def validate(rows: list):
    valid, invalid = [], []
    for row in rows:
        if REQUIRED_FIELDS.issubset(row.keys()):
            valid.append(row)
        else:
            invalid.append({"row": row, "error": "Missing fields"})
    return valid, invalid
