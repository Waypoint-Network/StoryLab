"""Local, reviewed publishing of Strategy Lab signals to The Helm.

This module deliberately owns only the outbound publishing seam.  It never
changes an article or brief and it makes no request until an operator has
approved a signal and configured the two local Helm environment variables.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from urllib import error, request
from urllib.parse import urlparse

from core.ai_summary import load_dotenv

PAYLOAD_VERSION = 1
MAX_BATCH_SIGNALS = 100
MAX_BATCH_BYTES = 1024 * 1024
DOMAINS = {"institutional", "mobilizer", "product", "fan_graph"}
OPPORTUNITY_RISKS = {"opportunity", "risk", "mixed", "neutral"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
SIGNAL_STATUSES = {"new", "reviewed", "accepted", "dismissed", "superseded"}
URGENCIES = {"now", "soon", "watch", "none"}
REVIEW_STATUSES = {"draft", "reviewed", "approved"}
ROLE_IDS = {"executive", "bizdev", "marketing", "technology", "projects", "production"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def clamp_score(value):
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 0


def signal_external_id(config, article_id, url_hash):
    """Stable per local article, including an immutable source fingerprint."""
    fingerprint = (url_hash or hashlib.sha256(str(article_id).encode()).hexdigest())[:16]
    return f"strategy-lab:{config}:article:{article_id}:{fingerprint}"


def domain_from_article(config, category):
    """Use the existing display-layer group mapping; do not rewrite categories."""
    try:
        module = __import__(f"configs.{config}", fromlist=["CATEGORY_GROUPS"])
        group = getattr(module, "CATEGORY_GROUPS", {}).get(category, category)
    except ImportError:
        group = category
    return {
        "Institutional": "institutional", "Mobilizer": "mobilizer",
        "Product": "product", "Fan Graph": "fan_graph",
        "institutional": "institutional", "mobilizer": "mobilizer",
        "product": "product", "fan_graph": "fan_graph",
    }.get(group, "institutional")


def ensure_helm_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS helm_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config TEXT NOT NULL,
            article_id INTEGER NOT NULL,
            external_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            topic TEXT,
            signal_type TEXT NOT NULL DEFAULT 'market_signal',
            primary_domain TEXT NOT NULL,
            flywheel_domains TEXT NOT NULL,
            opportunity_risk TEXT NOT NULL DEFAULT 'neutral',
            confidence TEXT NOT NULL DEFAULT 'medium',
            relevance_score INTEGER NOT NULL DEFAULT 0,
            recommendation TEXT,
            signal_status TEXT NOT NULL DEFAULT 'new',
            role_impacts TEXT NOT NULL DEFAULT '{}',
            review_status TEXT NOT NULL DEFAULT 'draft',
            reviewed_at TEXT,
            helm_publish_status TEXT NOT NULL DEFAULT 'not_published',
            helm_published_at TEXT,
            helm_last_attempt_at TEXT,
            helm_last_error TEXT,
            helm_payload_version INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(config, article_id)
        );
    """)
    conn.commit()


def _article_row(conn, config, article_id):
    return conn.execute("""
        SELECT id, url_hash, title, summary, source, url, published_date, fetched_date,
               relevance_score, category
        FROM articles WHERE id = ? AND config = ?
    """, (article_id, config)).fetchone()


def create_signal_from_article(conn, config, article_id):
    ensure_helm_tables(conn)
    article = _article_row(conn, config, article_id)
    if not article:
        return {"ok": False, "message": "Source article not found."}
    existing = conn.execute("SELECT id FROM helm_signals WHERE config = ? AND article_id = ?", (config, article_id)).fetchone()
    if existing:
        return {"ok": True, "signal": get_signal(conn, config, existing[0]), "existing": True}
    primary = domain_from_article(config, article[9])
    created = now_iso()
    conn.execute("""
        INSERT INTO helm_signals (config, article_id, external_id, title, summary, topic,
            primary_domain, flywheel_domains, relevance_score, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (config, article[0], signal_external_id(config, article[0], article[1]), article[2],
          article[3] or "", article[9], primary, json.dumps([primary]),
          clamp_score((article[8] or 0) * 20), created, created))
    conn.commit()
    return {"ok": True, "signal": get_signal(conn, config, conn.execute("SELECT last_insert_rowid()").fetchone()[0])}


def prepare_signals_from_approved_brief(conn, config, brief_id):
    """Turn an approved brief's source snapshot into local Helm drafts.

    The brief is not transmitted as one synthetic signal: Helm receives its
    original source-backed items, each with a stable ID. An operator still
    writes role impacts and approves each item before it can be published.
    """
    from core.ai_summary import ensure_ai_tables

    ensure_ai_tables(conn)
    brief = conn.execute("""
        SELECT source_article_ids, review_status FROM flywheel_briefs
        WHERE id = ? AND config = ?
    """, (brief_id, config)).fetchone()
    if not brief:
        return {"ok": False, "message": "Brief not found."}
    if brief["review_status"] != "approved":
        return {"ok": False, "message": "Approve the brief before preparing its sources for Helm."}
    article_ids = _parse_json(brief["source_article_ids"], [])
    if not article_ids:
        return {"ok": False, "message": "This brief does not contain source articles."}
    prepared, existing, signal_ids = 0, 0, []
    for article_id in article_ids:
        result = create_signal_from_article(conn, config, article_id)
        if not result.get("ok"):
            continue
        signal_ids.append(result["signal"]["id"])
        if result.get("existing"):
            existing += 1
        else:
            prepared += 1
    return {
        "ok": True, "prepared": prepared, "existing": existing,
        "signal_ids": signal_ids,
        "message": f"Prepared {prepared} new source signal(s) for Helm; {existing} were already prepared. Review and approve the individual signals before publishing.",
    }


def _parse_json(value, fallback):
    try:
        return json.loads(value) if value else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback


def get_signal(conn, config, signal_id):
    ensure_helm_tables(conn)
    row = conn.execute("""
        SELECT hs.*, a.source AS source_name, a.url AS source_url,
               a.published_date, a.fetched_date
        FROM helm_signals hs JOIN articles a ON a.id = hs.article_id
        WHERE hs.id = ? AND hs.config = ?
    """, (signal_id, config)).fetchone()
    if not row:
        return None
    result = dict(row)
    result["flywheel_domains"] = _parse_json(result["flywheel_domains"], [])
    result["role_impacts"] = _parse_json(result["role_impacts"], {})
    return result


def list_signals(conn, config):
    ensure_helm_tables(conn)
    rows = conn.execute("""
        SELECT hs.*, a.source AS source_name, a.url AS source_url, a.published_date, a.fetched_date
        FROM helm_signals hs JOIN articles a ON a.id = hs.article_id
        WHERE hs.config = ? ORDER BY hs.updated_at DESC, hs.id DESC
    """, (config,)).fetchall()
    return [{**dict(row), "flywheel_domains": _parse_json(row["flywheel_domains"], []),
             "role_impacts": _parse_json(row["role_impacts"], {})} for row in rows]


def list_article_candidates(conn, config):
    ensure_helm_tables(conn)
    rows = conn.execute("""
        SELECT a.id, a.title, a.summary, a.source, a.url, a.published_date,
               a.relevance_score, a.category, hs.id AS signal_id
        FROM articles a LEFT JOIN helm_signals hs ON hs.article_id = a.id AND hs.config = a.config
        WHERE a.config = ? ORDER BY a.relevance_score DESC, a.published_date DESC LIMIT 250
    """, (config,)).fetchall()
    return [dict(row) for row in rows]


def validate_signal(signal):
    errors = []
    for field in ("external_id", "title", "summary", "source_name"):
        if not str(signal.get(field) or "").strip():
            errors.append(f"{field} is required")
    if not str(signal.get("observed_at") or signal.get("fetched_date") or signal.get("published_date") or "").strip():
        errors.append("observed_at is required")
    primary = signal.get("primary_domain")
    domains = signal.get("flywheel_domains") or []
    if primary not in DOMAINS:
        errors.append("primary_domain must be a valid domain")
    if not isinstance(domains, list) or not domains or any(domain not in DOMAINS for domain in domains):
        errors.append("flywheel_domains must contain valid domains")
    elif primary not in domains:
        errors.append("primary_domain must be included in flywheel_domains")
    if signal.get("opportunity_risk") not in OPPORTUNITY_RISKS:
        errors.append("opportunity_risk is invalid")
    if signal.get("confidence") not in CONFIDENCE_LEVELS:
        errors.append("confidence is invalid")
    if signal.get("signal_status") not in SIGNAL_STATUSES:
        errors.append("status is invalid")
    for role, impact in (signal.get("role_impacts") or {}).items():
        if role not in ROLE_IDS:
            errors.append(f"unknown role: {role}")
            continue
        if not isinstance(impact, dict) or not str(impact.get("why_it_matters") or "").strip() or not str(impact.get("recommended_attention") or "").strip():
            errors.append(f"{role} needs why_it_matters and recommended_attention")
        if impact.get("urgency") not in URGENCIES:
            errors.append(f"{role} has invalid urgency")
    return errors


def save_signal(conn, config, signal_id, changes):
    current = get_signal(conn, config, signal_id)
    if not current:
        return {"ok": False, "message": "Signal not found."}
    allowed = {"title", "summary", "topic", "signal_type", "primary_domain", "flywheel_domains",
               "opportunity_risk", "confidence", "relevance_score", "recommendation", "signal_status",
               "role_impacts", "review_status"}
    updated = {**current, **{key: value for key, value in changes.items() if key in allowed}}
    updated["relevance_score"] = clamp_score(updated.get("relevance_score"))
    updated["flywheel_domains"] = list(dict.fromkeys(updated.get("flywheel_domains") or []))
    updated["role_impacts"] = {key: value for key, value in (updated.get("role_impacts") or {}).items() if value}
    for impact in updated["role_impacts"].values():
        if "relevance" in impact and str(impact["relevance"]).strip():
            impact["relevance"] = clamp_score(impact["relevance"])
    if updated.get("review_status") not in REVIEW_STATUSES:
        return {"ok": False, "message": "Review status must be draft, reviewed, or approved."}
    errors = validate_signal(updated)
    if errors:
        return {"ok": False, "message": "; ".join(errors)}
    reviewed_at = now_iso() if updated["review_status"] in {"reviewed", "approved"} else None
    conn.execute("""
        UPDATE helm_signals SET title=?, summary=?, topic=?, signal_type=?, primary_domain=?,
            flywheel_domains=?, opportunity_risk=?, confidence=?, relevance_score=?, recommendation=?,
            signal_status=?, role_impacts=?, review_status=?, reviewed_at=?, updated_at=?
        WHERE id=? AND config=?
    """, (updated["title"], updated["summary"], updated.get("topic"), updated["signal_type"],
          updated["primary_domain"], json.dumps(updated["flywheel_domains"]), updated["opportunity_risk"],
          updated["confidence"], updated["relevance_score"], updated.get("recommendation"),
          updated["signal_status"], json.dumps(updated["role_impacts"]), updated["review_status"],
          reviewed_at, now_iso(), signal_id, config))
    conn.commit()
    return {"ok": True, "signal": get_signal(conn, config, signal_id)}


def build_payload(signal):
    observed_at = signal.get("fetched_date") or signal.get("published_date") or now_iso()
    payload_signal = {
        "external_id": signal["external_id"], "title": signal["title"], "summary": signal["summary"],
        "source": {"name": signal["source_name"], "url": signal.get("source_url") or None,
                   "published_at": signal.get("published_date") or None},
        "observed_at": observed_at, "topic": signal.get("topic") or "industry-signal",
        "signal_type": signal.get("signal_type") or "market_signal",
        "primary_domain": signal["primary_domain"], "flywheel_domains": signal["flywheel_domains"],
        "opportunity_risk": signal["opportunity_risk"], "confidence": signal["confidence"],
        "relevance_score": clamp_score(signal["relevance_score"]), "recommendation": signal.get("recommendation") or "Review the attached source evidence before deciding whether to act.",
        "status": signal["signal_status"], "role_impacts": signal["role_impacts"],
    }
    return {"signals": [payload_signal]}


def connection_settings():
    load_dotenv()
    return os.environ.get("HELM_STRATEGY_ENDPOINT", "").strip(), os.environ.get("HELM_STRATEGY_API_KEY", "").strip()


def connection_diagnostics():
    """Safe configuration evidence for the local operator; never expose keys."""
    load_dotenv()
    raw_endpoint = os.environ.get("HELM_STRATEGY_ENDPOINT", "")
    raw_key = os.environ.get("HELM_STRATEGY_API_KEY", "")
    endpoint = raw_endpoint.strip()
    parsed = urlparse(endpoint)
    return {
        "configuration_loaded": bool(endpoint and raw_key.strip()),
        "key_exists": bool(raw_key),
        "key_length": len(raw_key),
        "key_has_edge_whitespace": raw_key != raw_key.strip(),
        "key_fingerprint": hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:12] if raw_key else None,
        "destination": {"scheme": parsed.scheme, "hostname": parsed.hostname, "path": parsed.path},
        "runtime": "trusted local Python backend",
        "method": "POST",
        "authorization": "present" if raw_key.strip() else "missing",
    }


def _validate_endpoint(endpoint):
    parsed = urlparse(endpoint)
    if parsed.scheme != "https":
        return "HELM_STRATEGY_ENDPOINT must use https."
    if parsed.hostname != "waypoint-helm-v1.nateleigh.chatgpt.site":
        return "HELM_STRATEGY_ENDPOINT has an unexpected hostname."
    if parsed.path != "/api/integrations/strategy-lab/signals":
        return "HELM_STRATEGY_ENDPOINT has an unexpected path."
    if parsed.query or parsed.fragment:
        return "HELM_STRATEGY_ENDPOINT must not include a query string or fragment."
    return None


def _sanitize_response_body(response):
    try:
        body = response.read(2048).decode("utf-8", errors="replace").strip()
    except Exception:
        return None
    if not body:
        return None
    # Prevent accidental key reflection by an upstream error page.
    return re.sub(r"(?i)(bearer\s+|api[_-]?key[\s:=]+)[^\s\"']+", r"\1[REDACTED]", body)[:600]


def _http_failure_details(exc):
    headers = exc.headers or {}
    ray_id = headers.get("cf-ray") or headers.get("CF-Ray")
    response_body = _sanitize_response_body(exc)
    cloudflare_block = bool(ray_id) or "cloudflare" in (response_body or "").lower() or "error 1010" in (response_body or "").lower()
    return {
        "category": "cloudflare_access" if cloudflare_block else ("authentication" if exc.code in (401, 403) else "http_response"),
        "received_http_response": True,
        "status": exc.code,
        "response_body": response_body,
        "cloudflare_ray_id": ray_id,
    }


def _failure_message(details):
    parts = [f"Helm returned HTTP {details['status']} ({details['category']})."]
    if details.get("response_body"):
        parts.append(f"Response: {details['response_body']}")
    if details.get("cloudflare_ray_id"):
        parts.append(f"Cloudflare Ray ID: {details['cloudflare_ray_id']}")
    return " ".join(parts)


def _record_attempt(conn, signal_ids, status, error_message=None):
    now = now_iso()
    conn.executemany("""
        UPDATE helm_signals SET helm_publish_status=?, helm_last_attempt_at=?, helm_last_error=?,
            helm_published_at=CASE WHEN ?='published' THEN ? ELSE helm_published_at END,
            helm_payload_version=? WHERE id=?
    """, [(status, now, error_message, status, now, PAYLOAD_VERSION, signal_id) for signal_id in signal_ids])
    conn.commit()


def _record_brief_attempt(conn, brief_id, status, error_message=None):
    now = now_iso()
    conn.execute("""
        UPDATE flywheel_briefs SET helm_publish_status=?, helm_last_attempt_at=?, helm_last_error=?,
            helm_published_at=CASE WHEN ?='published' THEN ? ELSE helm_published_at END,
            helm_payload_version=? WHERE id=?
    """, (status, now, error_message, status, now, PAYLOAD_VERSION, brief_id))
    conn.commit()


def _send_payload(endpoint, api_key, encoded, opener):
    endpoint_error = _validate_endpoint(endpoint)
    if endpoint_error:
        return {"ok": False, "message": endpoint_error, "diagnostics": connection_diagnostics()}
    req = request.Request(endpoint, data=encoded, method="POST", headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json",
    })
    try:
        with opener(req, timeout=15) as response:
            code = getattr(response, "status", response.getcode())
            if not 200 <= code < 300:
                raise error.HTTPError(endpoint, code, "Helm rejected the request", response.headers, None)
    except error.HTTPError as exc:
        details = _http_failure_details(exc)
        return {"ok": False, "message": _failure_message(details), "diagnostics": {**connection_diagnostics(), **details}}
    except error.URLError as exc:
        reason = str(getattr(exc, "reason", "network error"))
        return {"ok": False, "message": f"Could not reach Helm ({reason}). No HTTP response was received.", "diagnostics": {**connection_diagnostics(), "category": "network", "received_http_response": False}}
    except TimeoutError:
        return {"ok": False, "message": "Helm request timed out. No HTTP response was received; it is safe to retry.", "diagnostics": {**connection_diagnostics(), "category": "timeout", "received_http_response": False}}
    return {"ok": True}


def publish_signals(conn, config, signal_ids, opener=request.urlopen):
    if not signal_ids or len(signal_ids) > MAX_BATCH_SIGNALS:
        return {"ok": False, "message": "Select between 1 and 100 signals."}
    signals = [get_signal(conn, config, signal_id) for signal_id in signal_ids]
    if any(signal is None for signal in signals):
        return {"ok": False, "message": "One or more selected signals were not found."}
    if any(signal["review_status"] != "approved" for signal in signals):
        return {"ok": False, "message": "Only approved signals can be published."}
    errors = [f"{signal['title']}: {'; '.join(validate_signal(signal))}" for signal in signals if validate_signal(signal)]
    if errors:
        return {"ok": False, "message": " | ".join(errors)}
    payload = {"signals": [build_payload(signal)["signals"][0] for signal in signals]}
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_BATCH_BYTES:
        return {"ok": False, "message": "The selected batch exceeds the 1 MB Helm limit."}
    endpoint, api_key = connection_settings()
    if not endpoint or not api_key:
        return {"ok": False, "message": "Helm connection is not configured. Set HELM_STRATEGY_ENDPOINT and HELM_STRATEGY_API_KEY in .env."}
    result = _send_payload(endpoint, api_key, encoded, opener)
    if not result["ok"]:
        _record_attempt(conn, signal_ids, "failed", result["message"])
        return result
    _record_attempt(conn, signal_ids, "published")
    return {"ok": True, "published": len(signal_ids), "message": f"Published {len(signal_ids)} approved signal(s) to Helm."}


def publish_approved_brief(conn, config, brief_id, opener=request.urlopen):
    """Publish one approved brief with all of its source citations as evidence.

    This is the normal Strategy Lab -> Helm path. Article-level signals remain
    available for exceptional cases, but never need to be reviewed one by one.
    """
    from core.ai_summary import get_latest_flywheel_brief, ensure_ai_tables

    ensure_ai_tables(conn)
    row = conn.execute("SELECT flywheel_group, review_status FROM flywheel_briefs WHERE id=? AND config=?", (brief_id, config)).fetchone()
    if not row:
        return {"ok": False, "message": "Brief not found."}
    if row["review_status"] != "approved":
        return {"ok": False, "message": "Approve the brief before publishing it to Helm."}
    brief = get_latest_flywheel_brief(conn, config, row["flywheel_group"])
    if not brief or brief["id"] != brief_id:
        return {"ok": False, "message": "Only the current brief for this flywheel can be published."}
    sources = brief["supporting_material"]
    if not sources:
        return {"ok": False, "message": "This brief has no source evidence."}
    domain = domain_from_article(config, row["flywheel_group"])
    citations = "\n".join(f"- {item['title']} | {item['source']} | {item['url']}" for item in sources)
    signal = {
        "external_id": f"strategy-lab:{config}:brief:{brief_id}",
        "title": f"[{row['flywheel_group'].upper()}] Fan Atlas flywheel brief",
        "summary": (
            "STRATEGY LAB FLYWHEEL CLASSIFICATION\n"
            f"Brief home: {row['flywheel_group']}\n"
            f"Primary Helm domain: {domain}\n\n"
            f"WHAT CHANGED\n{brief['what_changed']}\n\n"
            f"WHY IT MATTERS\n{brief['why_it_matters']}\n\n"
            f"SUPPORTING SOURCES\n{citations}"
        ),
        "source_name": "Strategy Lab flywheel brief",
        "source_url": sources[0].get("url"),
        "published_date": brief.get("freshness_date"), "fetched_date": brief.get("generated_at"),
        "topic": f"fan-atlas-{domain}-brief", "signal_type": "intelligence_brief",
        "primary_domain": domain, "flywheel_domains": [domain],
        "opportunity_risk": "neutral", "confidence": "medium", "relevance_score": 100,
        "recommendation": brief["suggested_next_step"], "signal_status": "reviewed", "role_impacts": {},
    }
    encoded = json.dumps(build_payload(signal), separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_BATCH_BYTES:
        return {"ok": False, "message": "This brief exceeds the 1 MB Helm limit."}
    endpoint, api_key = connection_settings()
    if not endpoint or not api_key:
        return {"ok": False, "message": "Helm connection is not configured. Set HELM_STRATEGY_ENDPOINT and HELM_STRATEGY_API_KEY in .env."}
    result = _send_payload(endpoint, api_key, encoded, opener)
    if not result["ok"]:
        _record_brief_attempt(conn, brief_id, "failed", result["message"])
        return result
    _record_brief_attempt(conn, brief_id, "published")
    return {"ok": True, "message": "Published this approved evidence-backed brief to Helm.", "external_id": signal["external_id"]}
