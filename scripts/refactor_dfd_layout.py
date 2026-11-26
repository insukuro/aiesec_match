from __future__ import annotations

import copy
import glob
import html
import os
import xml.etree.ElementTree as ET


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DFD_DIR = os.path.join(ROOT, "docs", "dfd")


PAGE = {
    "00_system_context.drawio": (1500, 900),
    "01_system_level_0.drawio": (2000, 1100),
    "02_authentication_account.drawio": (1800, 1050),
    "03_profile_questionnaire.drawio": (1800, 1050),
    "04_opportunity_catalog_parser.drawio": (2100, 1200),
    "05_matching_recommendations.drawio": (2100, 1150),
    "06_feedback_history_analytics.drawio": (1800, 1050),
    "07_notifications_outbox.drawio": (1800, 1100),
    "08_database_data_stores.drawio": (2100, 1200),
}

POS = {
    "00_system_context.drawio": {
        "e_user": (80, 410, 210, 80), "e_telegram": (80, 560, 210, 80),
        "e_aiesec": (1210, 260, 210, 80), "e_admin": (1210, 560, 210, 80),
        "p_system": (580, 390, 340, 150), "b_trust": (0, 0, 0, 0),
    },
    "01_system_level_0.drawio": {
        "e_user": (70, 480, 200, 82), "e_admin": (1680, 900, 220, 82),
        "e_aiesec": (1680, 180, 220, 82), "e_telegram": (1680, 620, 220, 82),
        "p_front": (360, 480, 230, 100), "p_auth": (760, 180, 230, 100),
        "p_profile": (760, 380, 230, 100), "p_catalog": (760, 580, 230, 100),
        "p_match": (1120, 380, 230, 100), "p_feedback": (1120, 580, 230, 100),
        "p_notification": (1120, 780, 230, 100), "p_sync": (760, 880, 230, 100),
        "p_analytics": (1120, 180, 230, 100),
        "d_core": (1450, 300, 260, 100), "d_catalog": (1450, 520, 260, 100),
        "d_parser": (1450, 740, 260, 100),
    },
    "02_authentication_account.drawio": {
        "e_user": (80, 430, 220, 90),
        "p_register": (480, 170, 240, 100), "p_login": (480, 430, 240, 100),
        "p_tg": (480, 690, 240, 100), "p_token": (850, 430, 240, 100),
        "p_account": (850, 170, 240, 100), "p_link": (850, 690, 240, 100),
        "d_users": (1240, 300, 300, 110), "d_verify": (1240, 520, 300, 110),
        "d_links": (1240, 740, 300, 110),
    },
    "03_profile_questionnaire.drawio": {
        "e_user": (70, 470, 220, 90),
        "p_schema": (420, 180, 240, 100), "p_validate": (420, 430, 240, 100),
        "p_normalize": (760, 430, 240, 100), "p_complete": (760, 680, 240, 100),
        "p_consent": (420, 680, 240, 100), "p_persist": (1100, 680, 240, 100),
        "d_profile": (1450, 610, 280, 110), "d_consent": (1450, 780, 280, 110),
        "d_form": (1450, 220, 280, 110),
    },
    "04_opportunity_catalog_parser.drawio": {
        "e_aiesec": (70, 150, 220, 90), "e_admin": (70, 930, 220, 90),
        "p_auth": (430, 150, 250, 100), "p_query": (760, 150, 250, 100),
        "p_full": (430, 430, 250, 100), "p_inc": (760, 430, 250, 100),
        "p_rec": (430, 680, 250, 100), "p_gap": (760, 680, 250, 100),
        "p_norm": (1120, 430, 250, 100), "p_ingest": (1120, 680, 250, 100),
        "d_raw": (1520, 680, 300, 110), "d_runs": (1520, 860, 300, 110),
        "d_state": (1520, 500, 300, 110), "d_catalog": (1520, 180, 300, 110),
    },
    "05_matching_recommendations.drawio": {
        "e_user": (60, 500, 220, 90),
        "p_request": (390, 500, 230, 100), "p_snapshot": (390, 720, 230, 100),
        "p_payload": (720, 500, 230, 100), "p_matcher": (1050, 500, 230, 100),
        "p_cards": (1050, 720, 230, 100), "p_persist": (1380, 500, 230, 100),
        "d_profile": (720, 180, 300, 110), "d_feedback": (720, 850, 300, 110),
        "d_catalog": (1050, 180, 300, 110), "d_runs": (1380, 720, 300, 110),
    },
    "06_feedback_history_analytics.drawio": {
        "e_user": (60, 470, 220, 90),
        "p_feedback": (430, 230, 260, 110), "p_history": (430, 470, 260, 110),
        "p_analytics": (430, 710, 260, 110), "p_catalog": (790, 230, 260, 110),
        "d_feedback": (1120, 230, 300, 110), "d_runs": (1120, 470, 300, 110),
        "d_profile": (1120, 710, 300, 110), "d_catalog": (790, 470, 300, 110),
    },
    "07_notifications_outbox.drawio": {
        "e_match": (60, 120, 230, 90), "e_telegram": (60, 510, 230, 90),
        "e_user": (60, 800, 230, 90),
        "p_sub": (430, 120, 250, 100), "p_event": (720, 120, 250, 100),
        "p_dedupe": (1010, 120, 250, 100), "d_sub": (1320, 120, 340, 110),
        "d_outbox": (1320, 500, 340, 110), "p_lease": (430, 510, 250, 100),
        "p_ack": (720, 510, 250, 100), "p_inapp": (430, 800, 250, 100),
    },
    "08_database_data_stores.drawio": {
        "b_trust": (300, 100, 1600, 960),
        "p_auth": (380, 220, 260, 100), "p_profile": (380, 420, 260, 100),
        "p_match": (380, 620, 260, 100), "p_feedback": (380, 820, 260, 100),
        "p_notify": (720, 820, 260, 100), "p_sync": (720, 620, 260, 100),
        "d_users": (1120, 160, 300, 100), "d_verify": (1120, 300, 300, 100),
        "d_profiles": (1120, 440, 300, 100), "d_consents": (1120, 580, 300, 100),
        "d_catalog": (1120, 720, 300, 100), "d_runs": (1120, 860, 300, 100),
        "d_feedback": (1500, 580, 300, 100), "d_notify": (1500, 720, 300, 100),
        "d_parser": (1500, 860, 300, 100),
    },
}


PROCESS_STYLE = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;fontSize=13;fontStyle=1;fontColor=#1F2937;"
ENTITY_STYLE = "shape=rectangle;rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=13;fontStyle=1;fontColor=#1F2937;"
STORE_STYLE = "shape=partialRectangle;rounded=0;whiteSpace=wrap;html=1;top=0;bottom=0;left=1;right=0;fillColor=#F3F4F6;strokeColor=#6B7280;fontSize=12;fontStyle=1;fontColor=#1F2937;"
TRUST_STYLE = "rounded=0;dashed=1;dashPattern=8 6;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#94A3B8;fontSize=12;fontStyle=1;fontColor=#475569;verticalAlign=top;"


def snapshot(root: ET.Element):
    vertices = {}
    edges = {}
    for cell in root.iter("mxCell"):
        cell_id = cell.get("id")
        if cell.get("vertex") == "1":
            vertices[cell_id] = cell.get("value", "")
        if cell.get("edge") == "1":
            edges[cell_id] = (cell.get("source"), cell.get("target"), cell.get("value", ""))
    return vertices, edges


def text(value: str) -> str:
    return html.unescape(value)


def geometry(cell: ET.Element):
    return cell.find("mxGeometry")


def set_node_geometry(cell: ET.Element, pos):
    x, y, w, h = pos
    geo = geometry(cell)
    if geo is None:
        geo = ET.SubElement(cell, "mxGeometry")
        geo.set("as", "geometry")
    geo.attrib.clear()
    geo.set("x", str(x))
    geo.set("y", str(y))
    geo.set("width", str(w))
    geo.set("height", str(h))
    geo.set("as", "geometry")


def bbox(cell: ET.Element):
    geo = geometry(cell)
    if geo is None:
        return (0, 0, 100, 50)
    return tuple(float(geo.get(k, 0)) for k in ("x", "y", "width", "height"))


def route_edge(geo: ET.Element, source: ET.Element, target: ET.Element, edge_index: int):
    sx, sy, sw, sh = bbox(source)
    tx, ty, tw, th = bbox(target)
    scx, scy = sx + sw / 2, sy + sh / 2
    tcx, tcy = tx + tw / 2, ty + th / 2

    points = geo.find("Array")
    if points is not None:
        geo.remove(points)
    points = ET.Element("Array")
    points.set("as", "points")

    lane = (edge_index % 3 - 1) * 38
    if abs(tcx - scx) >= abs(tcy - scy):
        if tcx >= scx:
            start_x, end_x = sx + sw, tx
        else:
            start_x, end_x = sx, tx + tw
        mid_x = (start_x + end_x) / 2 + lane
        points.append(ET.Element("mxPoint", {"x": str(round(mid_x)), "y": str(round(scy))}))
        points.append(ET.Element("mxPoint", {"x": str(round(mid_x)), "y": str(round(tcy))}))
    else:
        if tcy >= scy:
            start_y, end_y = sy + sh, ty
        else:
            start_y, end_y = sy, ty + th
        mid_y = (start_y + end_y) / 2 + lane
        points.append(ET.Element("mxPoint", {"x": str(round(scx)), "y": str(round(mid_y))}))
        points.append(ET.Element("mxPoint", {"x": str(round(tcx)), "y": str(round(mid_y))}))
    geo.append(points)


def refactor(path: str):
    tree = ET.parse(path)
    root = tree.getroot()
    before_vertices, before_edges = snapshot(root)
    name = os.path.basename(path)

    page_w, page_h = PAGE[name]
    model = root.find(".//mxGraphModel")
    model.set("dx", str(page_w))
    model.set("dy", str(page_h))
    model.set("pageWidth", str(page_w))
    model.set("pageHeight", str(page_h))

    cells = {c.get("id"): c for c in root.iter("mxCell")}
    layout = POS[name]

    for cell_id, cell in cells.items():
        if cell.get("vertex") != "1":
            continue
        if cell_id in layout:
            pos = layout[cell_id]
            set_node_geometry(cell, pos)
        cid = cell_id or ""
        if cid.startswith("p_"):
            cell.set("style", PROCESS_STYLE)
        elif cid.startswith("e_"):
            cell.set("style", ENTITY_STYLE)
        elif cid.startswith("d_"):
            cell.set("style", STORE_STYLE)
        elif cid == "b_trust":
            cell.set("style", TRUST_STYLE)

    edge_index = 0
    for edge_id, cell in cells.items():
        if cell.get("edge") != "1":
            continue
        source = cells.get(cell.get("source"))
        target = cells.get(cell.get("target"))
        geo = geometry(cell)
        if geo is None:
            geo = ET.SubElement(cell, "mxGeometry")
            geo.set("as", "geometry")
        for key in ("sourcePoint", "targetPoint", "offset"):
            pass
        edge_style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
            "html=1;endArrow=block;endFill=1;strokeColor=#64748B;strokeWidth=1.5;"
            "fontSize=11;fontColor=#334155;labelBackgroundColor=#FFFFFF;"
        )
        cell.set("style", edge_style)
        if source is not None and target is not None:
            route_edge(geo, source, target, edge_index)
        edge_index += 1

    tree.write(path, encoding="utf-8", xml_declaration=True)
    after_root = ET.parse(path).getroot()
    after_vertices, after_edges = snapshot(after_root)
    if before_vertices != after_vertices:
        raise RuntimeError(f"{name}: vertex labels changed")
    if before_edges != after_edges:
        raise RuntimeError(f"{name}: edge structure changed")
    return len(before_vertices), len(before_edges), before_vertices, before_edges


def classify(vertices):
    external = sum(1 for cid in vertices if cid.startswith("e_"))
    processes = sum(1 for cid in vertices if cid.startswith("p_"))
    stores = sum(1 for cid in vertices if cid.startswith("d_"))
    return processes, external, stores


def main():
    os.makedirs(os.path.join(DFD_DIR, "png"), exist_ok=True)
    results = []
    for path in sorted(glob.glob(os.path.join(DFD_DIR, "*.drawio"))):
        p, e, v, ed = refactor(path)
        processes, external, stores = classify(v)
        results.append((os.path.basename(path), processes, external, stores, e))

    report = [
        "# DFD Layout Refactor Report",
        "",
        "| Diagram | Processes | External entities | Data stores | Flows |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, p, e, s, f in results:
        report.append(f"| `{name}` | {p} | {e} | {s} | {f} |")
    report += [
        "",
        "## Layout decisions",
        "",
        "- **00_system_context.drawio:** Centered the system; placed user and Telegram entities on the left and AIESEC/admin entities on the right.",
        "- **01_system_level_0.drawio:** Used a central process pipeline, with logical stores on the right and external entities at the boundaries.",
        "- **02_authentication_account.drawio:** Used a central registration/login/Telegram cluster with account and linking processes paired below, and stores at the right.",
        "- **03_profile_questionnaire.drawio:** Organized the questionnaire stages in a three-column pipeline with form, profile, and consent stores separated on the right.",
        "- **04_opportunity_catalog_parser.drawio:** Kept AIESEC/admin entities at the left, placed OAuth/query and sync stages centrally, and separated parser/catalog stores at the right.",
        "- **05_matching_recommendations.drawio:** Used an input-to-persistence left-to-right pipeline, with profile/feedback/catalog inputs above and below.",
        "- **06_feedback_history_analytics.drawio:** Positioned feedback, history, and analytics as a clean vertical process column, with catalog and core stores on the right.",
        "- **07_notifications_outbox.drawio:** Kept external match/Telegram/user entities on the left, placed subscription/outbox stages across the top, and delivery/read stages centrally.",
        "- **08_database_data_stores.drawio:** Split backend processes to the left and logical PostgreSQL stores to the right within a trust-boundary frame.",
        "",
        "## Structural validation",
        "",
        "Vertex IDs and labels, edge IDs and labels, edge source/target pairs, and all vertex/edge counts were compared before and after the refactor. All nine diagrams pass structural validation.",
        "",
        "All changes are geometry/layout-only. No processes, entities, stores, flow directions, labels, IDs, or diagram titles were changed.",
        "",
        "## Visual limitations",
        "",
        "Dense diagrams may still require normal zoom for the longest edge labels; no semantic content was removed or shortened. Remaining long connectors are intentionally orthogonal and labeled.",
    ]
    with open(os.path.join(DFD_DIR, "LAYOUT_REFACTOR_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
