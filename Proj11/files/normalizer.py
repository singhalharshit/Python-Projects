def normalize(rows: list):
    for r in rows:
        r["value"] = float(r["value"])
    return rows
