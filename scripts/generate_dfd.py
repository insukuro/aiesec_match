#!/usr/bin/env python3
import html
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "dfd"
OUT.mkdir(parents=True, exist_ok=True)

EXTERNAL = "shape=rectangle;rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;"
PROCESS = "ellipse;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;"
STORE = "shape=partialRectangle;whiteSpace=wrap;html=1;top=0;bottom=0;left=1;right=0;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;"
BOUNDARY = "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#999999;strokeWidth=1;dashed=1;verticalAlign=top;spacingTop=8;fontSize=10;fontColor=#666666;"
EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#44546A;fontSize=10;labelBackgroundColor=#FFFFFF;"


def esc(value):
    return html.escape(str(value), quote=True)


def make_diagram(name, nodes, edges, trust_boundaries=None, width=1400, height=900):
    mxfile = ET.Element("mxfile", host="app.diagrams.net", modified="2026-11-27", agent="reverse-engineering-generator", version="24.7.17", type="device")
    diagram = ET.SubElement(mxfile, "diagram", id=name, name=name)
    model = ET.SubElement(diagram, "mxGraphModel", dx="1600", dy="1000", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth=str(width), pageHeight=str(height), math="0", shadow="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    def add_node(item):
        nid, kind, label, x, y, w, h = item
        style = {"external": EXTERNAL, "process": PROCESS, "store": STORE}[kind]
        cell = ET.SubElement(root, "mxCell", id=nid, value=esc(label), style=style, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"})

    for b in trust_boundaries or []:
        bid, label, x, y, w, h = b
        cell = ET.SubElement(root, "mxCell", id=bid, value=esc(label), style=BOUNDARY, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"})

    for item in nodes:
        add_node(item)

    for eid, source, target, label in edges:
        cell = ET.SubElement(root, "mxCell", id=eid, value=esc(label), style=EDGE, edge="1", parent="1", source=source, target=target)
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})

    ET.indent(mxfile, space="  ")
    ET.ElementTree(mxfile).write(OUT / (name + ".drawio"), encoding="utf-8", xml_declaration=True)


make_diagram("00_system_context", [
    ("e_user", "external", "User", 30, 350, 130, 70),
    ("e_telegram", "external", "Telegram Bot / WebApp", 30, 560, 160, 70),
    ("e_aiesec", "external", "AIESEC External API", 1110, 180, 180, 70),
    ("e_admin", "external", "Parser Administrator", 1110, 620, 180, 70),
    ("p_system", "process", "AIESEC Match\nSystem", 510, 330, 260, 180),
], [
    ("f1", "e_user", "p_system", "credentials / profile / feedback / preferences"),
    ("f2", "p_system", "e_user", "JWT / recommendations / analytics / notifications"),
    ("f3", "e_telegram", "p_system", "Telegram initData / link codes / chat metadata"),
    ("f4", "p_system", "e_telegram", "lease / ack / notification payload"),
    ("f5", "e_aiesec", "p_system", "opportunity data / GraphQL responses"),
    ("f6", "p_system", "e_aiesec", "OAuth credentials / GraphQL queries"),
    ("f7", "e_admin", "p_system", "sync trigger / token management"),
    ("f8", "p_system", "e_admin", "sync state / health / diagnostics"),
], [("b_trust", "External boundaries", 420, 80, 440, 620)])

make_diagram("01_system_level_0", [
    ("e_user", "external", "User", 20, 330, 130, 70),
    ("e_admin", "external", "Parser Administrator", 1180, 710, 180, 70),
    ("e_aiesec", "external", "AIESEC External API", 1180, 120, 180, 70),
    ("e_telegram", "external", "Telegram Consumer", 1180, 350, 180, 70),
    ("p_front", "process", "1.0 Frontend /\nUser Interaction", 180, 330, 160, 80),
    ("p_auth", "process", "2.0 Authentication &\nAccount Management", 390, 150, 190, 80),
    ("p_profile", "process", "3.0 Profile & Consent\nManagement", 390, 310, 190, 80),
    ("p_catalog", "process", "4.0 Opportunity Catalog\nManagement", 390, 470, 190, 80),
    ("p_match", "process", "5.0 Matching &\nRecommendations", 650, 310, 190, 80),
    ("p_feedback", "process", "6.0 Feedback &\nHistory", 650, 470, 190, 80),
    ("p_notification", "process", "7.0 Notifications &\nSubscriptions", 650, 630, 190, 80),
    ("p_sync", "process", "8.0 Data\nSynchronization", 390, 630, 190, 80),
    ("p_analytics", "process", "9.0 Analytics", 650, 150, 190, 80),
    ("d_core", "store", "core.*\nusers, profiles, consents, runs, feedback", 880, 200, 240, 110),
    ("d_catalog", "store", "catalog.*\nopportunities, requirements, sync state", 880, 420, 240, 110),
    ("d_parser", "store", "parser.*\nopportunities, sync_runs, sync_state", 880, 640, 240, 100),
], [
    ("f1", "e_user", "p_front", "UI input / profile / feedback"),
    ("f2", "p_front", "e_user", "responses / cards / history / metrics"),
    ("f3", "p_front", "p_auth", "auth requests / JWT bearer"),
    ("f4", "p_auth", "p_front", "access token / account data"),
    ("f5", "p_front", "p_profile", "profile body / consent actions"),
    ("f6", "p_profile", "p_front", "profile / schema / completeness"),
    ("f7", "p_profile", "d_core", "profile versions / consents"),
    ("f8", "d_core", "p_profile", "current profile / consent records"),
    ("f9", "p_front", "p_match", "recommendation filters / idempotency key"),
    ("f10", "p_match", "p_front", "ranked groups / run state"),
    ("f11", "p_match", "d_catalog", "catalog cards / requirements"),
    ("f12", "p_match", "d_core", "runs / recommendation items"),
    ("f13", "p_front", "p_feedback", "feedback / history filters"),
    ("f14", "p_feedback", "p_front", "feedback lists / history events"),
    ("f15", "p_feedback", "d_core", "feedback / event activity"),
    ("f16", "p_notification", "d_core", "subscriptions / outbox"),
    ("f17", "d_core", "p_notification", "outbox leases / ack state"),
    ("f18", "p_notification", "e_telegram", "leased payload / delivery ack"),
    ("f19", "p_sync", "e_aiesec", "GraphQL query / OAuth data"),
    ("f20", "e_aiesec", "p_sync", "raw opportunity records"),
    ("f21", "p_sync", "d_parser", "normalized rows / sync runs / state"),
    ("f22", "p_catalog", "d_catalog", "canonical catalog / sync watermark"),
    ("f23", "d_catalog", "p_match", "open opportunity records"),
    ("f24", "p_front", "p_analytics", "analytics period"),
    ("f25", "p_analytics", "p_front", "aggregated metrics"),
    ("f26", "d_core", "p_analytics", "runs / feedback / profile data"),
    ("f27", "e_admin", "p_sync", "sync trigger / token update"),
])

make_diagram("02_authentication_account", [
    ("e_user", "external", "User / Telegram WebApp", 20, 330, 160, 70),
    ("p_register", "process", "2.1 Register Account", 260, 160, 170, 70),
    ("p_login", "process", "2.2 Password Login", 260, 300, 170, 70),
    ("p_tg", "process", "2.3 Verify Telegram\ninitData", 260, 440, 170, 70),
    ("p_token", "process", "2.4 Issue / Validate\nJWT", 500, 300, 170, 70),
    ("p_account", "process", "2.5 Account Changes", 730, 180, 170, 70),
    ("p_link", "process", "2.6 Telegram Identity\nLinking", 730, 420, 170, 70),
    ("d_users", "store", "core.users / identities /\npassword_credentials", 1000, 180, 220, 110),
    ("d_verify", "store", "core.email_verifications /\npassword_reset_tokens", 1000, 390, 220, 110),
    ("d_links", "store", "core.link_codes", 1000, 590, 220, 70),
], [
    ("f1", "e_user", "p_register", "email / password"),
    ("f2", "e_user", "p_login", "email / password"),
    ("f3", "e_user", "p_tg", "Telegram initData"),
    ("f4", "p_register", "p_token", "new user identity"),
    ("f5", "p_login", "p_token", "verified user id"),
    ("f6", "p_tg", "p_token", "verified Telegram identity"),
    ("f7", "p_token", "e_user", "access JWT / expiry"),
    ("f8", "p_register", "d_users", "user / identity / password hash"),
    ("f9", "p_login", "d_users", "credential lookup"),
    ("f10", "d_users", "p_login", "password hash / user status"),
    ("f11", "p_tg", "d_users", "Telegram external id lookup / create"),
    ("f12", "d_users", "p_tg", "identity / user record"),
    ("f13", "e_user", "p_account", "password / email / account deletion"),
    ("f14", "p_account", "d_users", "credential / identity / soft-delete update"),
    ("f15", "p_account", "d_verify", "email verification code hash"),
    ("f16", "d_verify", "p_account", "verification state"),
    ("f17", "e_user", "p_link", "link code"),
    ("f18", "p_link", "d_links", "link code / Telegram chat metadata"),
    ("f19", "d_links", "p_link", "code owner / expiry"),
    ("f20", "p_link", "d_users", "Telegram identity / chat update"),
])

make_diagram("03_profile_questionnaire", [
    ("e_user", "external", "User", 20, 300, 130, 70),
    ("p_schema", "process", "3.1 Load Form &\nConsent Schema", 220, 180, 170, 70),
    ("p_validate", "process", "3.2 Validate Profile\n& Age", 220, 340, 170, 70),
    ("p_normalize", "process", "3.3 Normalize Profile\nFields", 440, 340, 170, 70),
    ("p_complete", "process", "3.4 Calculate\nCompleteness", 660, 340, 170, 70),
    ("p_consent", "process", "3.5 Manage Consents", 660, 180, 170, 70),
    ("p_persist", "process", "3.6 Persist Profile\nVersions", 880, 340, 170, 70),
    ("d_profile", "store", "core.profiles /\nprofile_versions", 1120, 300, 220, 110),
    ("d_consent", "store", "core.consents", 1120, 150, 220, 70),
    ("d_form", "store", "form_schema.v2.yaml /\nconsents.v1.yaml", 440, 40, 220, 80),
], [
    ("f1", "e_user", "p_schema", "form / consent request"),
    ("f2", "d_form", "p_schema", "schema / field options / consent versions"),
    ("f3", "p_schema", "e_user", "form schema / consent schema / options"),
    ("f4", "e_user", "p_validate", "profile body / If-Match version"),
    ("f5", "p_validate", "p_normalize", "validated profile fields"),
    ("f6", "p_normalize", "p_complete", "JSON profile snapshot"),
    ("f7", "p_complete", "p_persist", "profile data / completeness"),
    ("f8", "p_persist", "d_profile", "new version / birth date / completeness"),
    ("f9", "d_profile", "p_persist", "current version / existing snapshot"),
    ("f10", "p_persist", "e_user", "profile / version / updated_at"),
    ("f11", "e_user", "p_consent", "consent kind / version"),
    ("f12", "d_form", "p_consent", "required consent version"),
    ("f13", "p_consent", "d_consent", "acceptance / revocation"),
    ("f14", "d_consent", "p_consent", "accepted consent records"),
])

make_diagram("04_opportunity_catalog_parser", [
    ("e_aiesec", "external", "AIESEC GraphQL API", 20, 300, 170, 70),
    ("e_admin", "external", "Parser Administrator", 20, 520, 170, 70),
    ("p_auth", "process", "4.1 OAuth / Token\nRefresh", 230, 150, 170, 70),
    ("p_query", "process", "4.2 Build GraphQL\nQueries", 230, 300, 170, 70),
    ("p_full", "process", "4.3 Full Strategy", 450, 180, 150, 70),
    ("p_inc", "process", "4.4 Incremental Strategy", 450, 300, 150, 70),
    ("p_rec", "process", "4.5 Reconcile Strategy", 450, 420, 150, 70),
    ("p_gap", "process", "4.6 Gap Filling", 630, 420, 150, 70),
    ("p_norm", "process", "4.7 Normalize /\nActuality / Target", 630, 300, 170, 70),
    ("p_ingest", "process", "4.8 Upsert / Close\nMissing", 850, 300, 170, 70),
    ("d_raw", "store", "parser.opportunities", 1110, 180, 220, 90),
    ("d_runs", "store", "parser.sync_runs", 1110, 310, 220, 70),
    ("d_state", "store", "parser.sync_state", 1110, 420, 220, 70),
    ("d_catalog", "store", "catalog.opportunity_v1 /\nrequirements", 1110, 530, 220, 100),
], [
    ("f1", "e_aiesec", "p_auth", "OAuth / GraphQL authorization response"),
    ("f2", "p_auth", "e_aiesec", "OAuth credentials / access token"),
    ("f3", "e_admin", "p_auth", "token / refresh-token management"),
    ("f4", "p_query", "e_aiesec", "paginated GraphQL opportunity query"),
    ("f5", "e_aiesec", "p_query", "raw opportunity records / schema"),
    ("f6", "p_full", "p_norm", "full-query rows"),
    ("f7", "p_inc", "p_norm", "incremental rows / since watermark"),
    ("f8", "p_rec", "p_gap", "slim rows / newly found ids"),
    ("f9", "p_gap", "e_aiesec", "full opportunity ids"),
    ("f10", "e_aiesec", "p_gap", "gap-fill opportunity records"),
    ("f11", "p_gap", "p_norm", "gap-filled records"),
    ("f12", "p_norm", "p_ingest", "normalized / actuality-checked rows"),
    ("f13", "p_ingest", "d_raw", "upsert / close / reopen operations"),
    ("f14", "d_raw", "p_ingest", "known ids / open opportunity state"),
    ("f15", "p_ingest", "d_runs", "sync status / stats / error"),
    ("f16", "p_full", "d_state", "last_full_at / last_incremental_at"),
    ("f17", "p_inc", "d_state", "incremental watermark"),
    ("f18", "p_rec", "d_state", "last_reconcile_at"),
    ("f19", "d_state", "p_inc", "previous incremental watermark"),
    ("f20", "d_raw", "d_catalog", "UNVERIFIED direct export / migration population"),
])

make_diagram("05_matching_recommendations", [
    ("e_user", "external", "User", 20, 300, 130, 70),
    ("p_request", "process", "5.1 Validate Consent &\nCreate Run", 200, 300, 170, 70),
    ("p_snapshot", "process", "5.2 Prepare Profile\nSnapshot", 420, 180, 170, 70),
    ("p_payload", "process", "5.3 Build Matcher\nPayload", 420, 360, 170, 70),
    ("p_matcher", "process", "5.4 Matcher: Route /\nFilter / Score", 680, 300, 190, 90),
    ("p_cards", "process", "5.5 Attach Catalog\nCards", 910, 300, 170, 70),
    ("p_persist", "process", "5.6 Persist Run &\nItems", 1120, 300, 170, 70),
    ("d_profile", "store", "core.profiles /\nprofile_versions", 420, 30, 220, 90),
    ("d_feedback", "store", "core.feedback", 420, 520, 220, 70),
    ("d_catalog", "store", "catalog.opportunity_v1 /\nrequirements", 910, 150, 220, 100),
    ("d_runs", "store", "core.recommendation_runs /\nrecommendation_items", 1120, 470, 220, 100),
], [
    ("f1", "e_user", "p_request", "filters / limit / idempotency key"),
    ("f2", "p_request", "d_profile", "consent / profile lookup"),
    ("f3", "d_profile", "p_snapshot", "profile body / completeness"),
    ("f4", "p_snapshot", "p_payload", "privacy-hashed profile snapshot"),
    ("f5", "d_feedback", "p_payload", "hidden / disliked exclusions"),
    ("f6", "p_payload", "p_matcher", "profile snapshot / filters / limit / explain"),
    ("f7", "d_catalog", "p_matcher", "open catalog / opportunity requirements"),
    ("f8", "p_matcher", "p_cards", "groups / scores / labels / reasons"),
    ("f9", "d_catalog", "p_cards", "opportunity cards / requirements"),
    ("f10", "p_cards", "p_persist", "filtered recommendation groups"),
    ("f11", "p_persist", "d_runs", "run state / items / watermark"),
    ("f12", "d_runs", "p_persist", "idempotent existing run"),
    ("f13", "p_persist", "e_user", "recommendation run / ranked cards"),
])

make_diagram("06_feedback_history_analytics", [
    ("e_user", "external", "User", 20, 300, 130, 70),
    ("p_feedback", "process", "6.1 Receive / Remove\nFeedback", 220, 180, 180, 70),
    ("p_history", "process", "6.2 Build Activity\nHistory", 220, 380, 180, 70),
    ("p_analytics", "process", "6.3 Aggregate\nAnalytics", 500, 280, 180, 70),
    ("p_catalog", "process", "6.4 Resolve\nOpportunity Cards", 500, 500, 180, 70),
    ("d_feedback", "store", "core.feedback", 760, 160, 220, 70),
    ("d_runs", "store", "core.recommendation_runs /\nrecommendation_items", 760, 280, 220, 100),
    ("d_profile", "store", "core.profiles /\nprofile_versions", 760, 430, 220, 100),
    ("d_catalog", "store", "catalog.opportunity_v1 /\nrequirements", 760, 570, 220, 100),
], [
    ("f1", "e_user", "p_feedback", "opened / liked / disliked / hidden / applied"),
    ("f2", "p_feedback", "d_feedback", "feedback records / run id / opportunity id"),
    ("f3", "d_feedback", "p_feedback", "feedback lists"),
    ("f4", "d_catalog", "p_catalog", "opportunity cards"),
    ("f5", "p_catalog", "p_feedback", "catalog-backed feedback cards"),
    ("f6", "p_feedback", "e_user", "liked / hidden opportunity lists"),
    ("f7", "e_user", "p_history", "history type / date range / pagination"),
    ("f8", "d_runs", "p_history", "completed recommendation events"),
    ("f9", "d_feedback", "p_history", "feedback events"),
    ("f10", "p_history", "e_user", "chronological history page"),
    ("f11", "e_user", "p_analytics", "period / date range"),
    ("f12", "d_profile", "p_analytics", "profile completeness / interests"),
    ("f13", "d_runs", "p_analytics", "recommendation distributions / counts"),
    ("f14", "d_feedback", "p_analytics", "activity events / feedback signals"),
    ("f15", "p_analytics", "e_user", "profile / programme / activity metrics"),
])

make_diagram("07_notifications_outbox", [
    ("e_match", "external", "Matching / Run Creation", 20, 300, 180, 70),
    ("e_telegram", "external", "Telegram Consumer", 1120, 430, 180, 70),
    ("e_user", "external", "User / In-App UI", 1120, 180, 180, 70),
    ("p_sub", "process", "7.1 Check Subscription", 260, 300, 170, 70),
    ("p_event", "process", "7.2 Create Outbox\nEvent", 470, 300, 170, 70),
    ("p_dedupe", "process", "7.3 Dedupe by\nUser + Run", 680, 300, 170, 70),
    ("d_sub", "store", "core.subscriptions", 470, 110, 220, 70),
    ("d_outbox", "store", "core.notification_outbox", 680, 470, 220, 100),
    ("p_lease", "process", "7.4 Lease Notifications", 900, 430, 170, 70),
    ("p_ack", "process", "7.5 Update Sent /\nFailed State", 900, 600, 170, 70),
    ("p_inapp", "process", "7.6 In-App Read\nState", 900, 180, 170, 70),
], [
    ("f1", "e_match", "p_sub", "succeeded run id / top matches"),
    ("f2", "d_sub", "p_sub", "subscription / min score / channels"),
    ("f3", "p_sub", "p_event", "notification-eligible run"),
    ("f4", "p_event", "p_dedupe", "run payload / dedupe key"),
    ("f5", "p_dedupe", "d_outbox", "pending event / payload / dedupe key"),
    ("f6", "d_outbox", "p_dedupe", "existing dedupe result"),
    ("f7", "e_telegram", "p_lease", "consumer lease request"),
    ("f8", "p_lease", "d_outbox", "lease / attempts / locked_until"),
    ("f9", "d_outbox", "p_lease", "leased notification payload"),
    ("f10", "p_lease", "e_telegram", "notification payload / chat id"),
    ("f11", "e_telegram", "p_ack", "delivery result / error"),
    ("f12", "p_ack", "d_outbox", "sent or failed / sent_at"),
    ("f13", "e_user", "p_inapp", "notification list / read request"),
    ("f14", "d_outbox", "p_inapp", "notification payload / read state"),
    ("f15", "p_inapp", "e_user", "notification page / unread count"),
])

make_diagram("08_database_data_stores", [
    ("p_auth", "process", "2.0 Auth &\nAccounts", 40, 120, 170, 70),
    ("p_profile", "process", "3.0 Profiles &\nConsents", 40, 260, 170, 70),
    ("p_match", "process", "5.0 Matching", 40, 400, 170, 70),
    ("p_feedback", "process", "6.0 Feedback / History", 40, 540, 170, 70),
    ("p_notify", "process", "7.0 Notifications", 40, 680, 170, 70),
    ("p_sync", "process", "4.0 Parser Sync", 40, 820, 170, 70),
    ("d_users", "store", "core.users / identities /\npassword_credentials", 330, 70, 250, 100),
    ("d_verify", "store", "core.password_reset_tokens /\nemail_verifications", 330, 200, 250, 100),
    ("d_profiles", "store", "core.profiles / profile_versions", 330, 330, 250, 100),
    ("d_consents", "store", "core.consents", 330, 460, 250, 70),
    ("d_catalog", "store", "catalog.opportunity_v1 /\nopportunity_requirement_v1", 700, 330, 300, 100),
    ("d_runs", "store", "core.recommendation_runs /\nrecommendation_items", 700, 470, 300, 100),
    ("d_feedback", "store", "core.feedback", 700, 610, 300, 70),
    ("d_notify", "store", "core.subscriptions /\nnotification_outbox / link_codes", 700, 710, 300, 100),
    ("d_parser", "store", "parser.opportunities / sync_runs /\nsync_state", 700, 840, 300, 100),
], [
    ("f1", "p_auth", "d_users", "create / lookup / update auth identity"),
    ("f2", "d_users", "p_auth", "credentials / identities / account state"),
    ("f3", "p_auth", "d_verify", "verification / reset code hashes"),
    ("f4", "d_verify", "p_auth", "verification state"),
    ("f5", "p_profile", "d_profiles", "profile snapshots / versions / completeness"),
    ("f6", "d_profiles", "p_profile", "current / historical profile data"),
    ("f7", "p_profile", "d_consents", "consent acceptance / revocation"),
    ("f8", "d_consents", "p_profile", "consent version records"),
    ("f9", "p_match", "d_runs", "run state / item scores / reasons"),
    ("f10", "d_runs", "p_match", "existing or latest run data"),
    ("f11", "p_match", "d_catalog", "catalog / requirement reads"),
    ("f12", "d_catalog", "p_match", "open opportunities / requirements"),
    ("f13", "p_feedback", "d_feedback", "feedback signals"),
    ("f14", "d_feedback", "p_feedback", "feedback lists / event history"),
    ("f15", "p_feedback", "d_runs", "history reads"),
    ("f16", "d_runs", "p_feedback", "completed runs"),
    ("f17", "p_notify", "d_notify", "subscription / outbox / link-code writes"),
    ("f18", "d_notify", "p_notify", "subscription / leases / ack state"),
    ("f19", "p_sync", "d_parser", "opportunity rows / sync runs / state"),
    ("f20", "d_parser", "p_sync", "known ids / previous watermarks"),
], [("b_trust", "PostgreSQL schemas / service trust boundary", 280, 40, 760, 950)], 1080, 1030)
