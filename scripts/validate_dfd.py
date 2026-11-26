#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DFD = ROOT / "docs" / "dfd"
files = sorted(DFD.glob("*.drawio"))

counts = {"process": 0, "store": 0, "external": 0, "flow": 0}
errors = []

for path in files:
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:
        errors.append(f"{path.name}: XML parse error: {exc}")
        continue

    ids = set()
    vertices = {}
    edges = []
    for cell in root.findall(".//mxCell"):
        cid = cell.get("id")
        if cid is None:
            continue
        if cid in ids:
            errors.append(f"{path.name}: duplicate id {cid}")
        ids.add(cid)
        if cell.get("vertex") == "1":
            style = cell.get("style", "")
            label = cell.get("value", "")
            if "ellipse" in style:
                kind = "process"
            elif "partialRectangle" in style:
                kind = "store"
            elif "shape=rectangle" in style:
                kind = "external"
            elif "dashed=1" in style:
                kind = "boundary"
            else:
                kind = "other"
            if kind in counts:
                counts[kind] += 1
            vertices[cid] = kind
        if cell.get("edge") == "1":
            edges.append(cell)
            counts["flow"] += 1

    for edge in edges:
        eid = edge.get("id", "<missing>")
        label = edge.get("value", "").strip()
        source = edge.get("source")
        target = edge.get("target")
        if not label:
            errors.append(f"{path.name}: unlabeled edge {eid}")
        if source not in vertices:
            errors.append(f"{path.name}: edge {eid} source missing: {source}")
        if target not in vertices:
            errors.append(f"{path.name}: edge {eid} target missing: {target}")

print(f"Files parsed: {len(files)}")
print(f"Processes: {counts['process']}")
print(f"Data stores: {counts['store']}")
print(f"External entities: {counts['external']}")
print(f"Data flows: {counts['flow']}")
print("Errors:", len(errors))
for error in errors:
    print("- " + error)
raise SystemExit(1 if errors or len(files) != 9 else 0)
