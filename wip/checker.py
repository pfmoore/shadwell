import json
import sqlite3

from packaging.version import parse

from shadwell.finder import Candidate, normalize

DB = sqlite3.connect(r"C:\Work\Scratch\pypidata\PyPI.db")

for name, json_data in DB.execute("select name, json from package_data_json").fetchall():
    name = normalize(name)
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError:
        continue
    for rel, items in data["releases"].items():
        rel = parse(rel)
        for item in items:
            filename = item["filename"]
            if item["packagetype"] not in ("bdist_wheel", "sdist"):
                continue
            try:
                c = Candidate(name, filename)
                if c.version != rel:
                    print(f"Version mismatch: {name} {rel}: {filename}")
            except Exception as e:
                print(f"ERROR: {name}, {rel}, {filename}: {e}")
