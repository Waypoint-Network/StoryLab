#!/usr/bin/env python3
"""
core/aggregator.py — StoryLab Feed Aggregator
----------------------------------------------
Fetches all RSS/Atom feeds for a given config and stores articles to SQLite.

Usage:
    python core/aggregator.py --config travel_tech_ux
    python core/aggregator.py --config fan_atlas_insiders
    python core/aggregator.py --config longitude
    python core/aggregator.py --config travel_tech_ux --days 3
    python core/aggregator.py --config travel_tech_ux --dry-run
"""

import sqlite3
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import hashlib
import argparse
import importlib
import sys
import os
import ssl
import re as _re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# Add repo root to path so configs/ is importable
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# Windows consoles default to a legacy codepage that can't encode the
# ★ / ✓ / ✗ / — characters this script prints — force UTF-8 output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()

# Fallback for feeds with expired/self-signed certs (e.g. SportTechie)
_SSL_UNVERIFIED = ssl.create_default_context()
_SSL_UNVERIFIED.check_hostname = False
_SSL_UNVERIFIED.verify_mode = ssl.CERT_NONE

DB_PATH    = os.path.join(REPO_ROOT, "curation.db")
MAX_DAYS   = 90
MAX_ITEMS  = 50
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

NS = {
    "atom":    "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "media":   "http://search.yahoo.com/mrss/",
}


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            url_hash         TEXT    UNIQUE NOT NULL,
            source           TEXT    NOT NULL,
            category         TEXT    NOT NULL,
            title            TEXT    NOT NULL,
            url              TEXT    NOT NULL,
            summary          TEXT,
            published_date   TEXT,
            fetched_date     TEXT    NOT NULL,
            status           TEXT    DEFAULT 'new',
            relevance_score  INTEGER DEFAULT 0,
            story_type       TEXT,
            config           TEXT    NOT NULL DEFAULT 'travel_tech_ux',
            issue_tag        TEXT,
            notes            TEXT
        );

        CREATE TABLE IF NOT EXISTS fetch_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            source          TEXT,
            run_at          TEXT,
            items_added     INTEGER,
            config          TEXT,
            error           TEXT
        );
    """)
    conn.commit()


def fetch_feed(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CONTEXT) as resp:
            return resp.read()
    except ssl.SSLCertVerificationError:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_UNVERIFIED) as resp:
            return resp.read()


_INVALID_XML_CHARS = _re.compile(
    r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\uD800-\uDFFF\uFFFE\uFFFF]'
)

def sanitize_xml(xml_bytes):
    """Strip characters illegal in XML 1.0 to fix malformed feeds."""
    try:
        text = xml_bytes.decode("utf-8", errors="replace")
    except Exception:
        text = xml_bytes.decode("latin-1", errors="replace")
    return _INVALID_XML_CHARS.sub("", text).encode("utf-8")


def parse_date(date_str):
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return date_str


def text_or_none(el):
    if el is None:
        return None
    return (el.text or "").strip() or None


def strip_html(text):
    if not text:
        return text
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:600] + ("…" if len(text) > 600 else "")


def url_hash(url):
    return hashlib.sha256(url.encode()).hexdigest()


def parse_rss(xml_bytes, source, category):
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        return []
    articles = []
    for item in channel.findall("item")[:MAX_ITEMS]:
        title   = text_or_none(item.find("title"))
        link    = text_or_none(item.find("link"))
        pub     = text_or_none(item.find("pubDate"))
        summary = (
            text_or_none(item.find("description")) or
            text_or_none(item.find("{%s}encoded" % NS["content"]))
        )
        if not link:
            continue
        articles.append({
            "source":    source,
            "category":  category,
            "title":     title or "(no title)",
            "url":       link,
            "summary":   strip_html(summary),
            "published": parse_date(pub),
            "url_hash":  url_hash(link),
        })
    return articles


def parse_atom(xml_bytes, source, category):
    root = ET.fromstring(xml_bytes)
    tag = root.tag
    ns_prefix = ""
    if tag.startswith("{"):
        ns_prefix = tag[1:tag.index("}")]

    def find(el, tag_name):
        return el.find(f"{{{ns_prefix}}}{tag_name}" if ns_prefix else tag_name)

    articles = []
    entries = root.findall(f"{{{ns_prefix}}}entry" if ns_prefix else "entry")
    for entry in entries[:MAX_ITEMS]:
        title_el = find(entry, "title")
        title    = text_or_none(title_el)
        link = None
        for l in entry.findall(f"{{{ns_prefix}}}link" if ns_prefix else "link"):
            rel = l.get("rel", "alternate")
            href = l.get("href")
            if href and rel in ("alternate", ""):
                link = href
                break
        if not link:
            continue
        pub = (
            text_or_none(find(entry, "updated")) or
            text_or_none(find(entry, "published"))
        )
        summary_el = find(entry, "summary") or find(entry, "content")
        summary    = text_or_none(summary_el)
        articles.append({
            "source":    source,
            "category":  category,
            "title":     title or "(no title)",
            "url":       link,
            "summary":   strip_html(summary),
            "published": parse_date(pub),
            "url_hash":  url_hash(link),
        })
    return articles


def detect_and_parse(xml_bytes, source, category):
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        xml_bytes = sanitize_xml(xml_bytes)
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            raise ValueError(f"XML parse error: {e}")
    tag = root.tag.lower()
    if "feed" in tag:
        return parse_atom(xml_bytes, source, category)
    else:
        return parse_rss(xml_bytes, source, category)


def too_old(pub_str, max_days):
    if not pub_str:
        return False
    try:
        pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_days)
        return pub_dt < cutoff
    except Exception:
        return False


def run(config="travel_tech_ux", dry_run=False, max_days=MAX_DAYS):
    feeds_mod = importlib.import_module(f"configs.{config}.feeds")
    FEEDS = feeds_mod.FEEDS
    NO_RSS_SOURCES = getattr(feeds_mod, "NO_RSS_SOURCES", [])

    config_meta = importlib.import_module(f"configs.{config}")
    display_name = getattr(config_meta, "DISPLAY_NAME", config.capitalize())

    from core.scorer import score_article

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    total_added = 0
    now = datetime.now(timezone.utc).isoformat()

    print(f"\n{'='*60}")
    print(f"  StoryLab Aggregator — {display_name}")
    print(f"  Run: {now[:19]}Z")
    print(f"{'='*60}\n")

    all_feeds = list(FEEDS)
    for src in NO_RSS_SOURCES:
        ktn = src.get("kill_the_newsletter_feed", "").strip()
        if ktn:
            all_feeds.append((src["name"], ktn, "email-newsletter", src.get("notes", "")))

    for label, url, category, notes in all_feeds:
        print(f"  [{category}] {label}")
        try:
            xml_bytes = fetch_feed(url)
            articles  = detect_and_parse(xml_bytes, label, category)
            added = 0
            for art in articles:
                if too_old(art["published"], max_days):
                    continue
                relevance_score, story_type = score_article(
                    art["title"], art["summary"] or "", art["category"], config
                )
                if dry_run:
                    print(f"      [{relevance_score}★ {story_type}] {art['title'][:60]}")
                    added += 1
                    continue
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO articles
                          (url_hash, source, category, title, url, summary,
                           published_date, fetched_date, relevance_score, story_type, config)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        art["url_hash"], art["source"], art["category"],
                        art["title"], art["url"], art["summary"],
                        art["published"], now,
                        relevance_score, story_type, config
                    ))
                    if conn.execute("SELECT changes()").fetchone()[0] > 0:
                        added += 1
                except sqlite3.Error as e:
                    print(f"      DB error: {e}")
            conn.commit()
            print(f"      ✓ {len(articles)} fetched, {added} new added")
            conn.execute(
                "INSERT INTO fetch_log (source,run_at,items_added,config) VALUES (?,?,?,?)",
                (label, now, added, config)
            )
            total_added += added
        except urllib.error.URLError as e:
            msg = f"Network error: {e.reason}"
            print(f"      ✗ {msg}")
            conn.execute(
                "INSERT INTO fetch_log (source,run_at,items_added,config,error) VALUES (?,?,?,?,?)",
                (label, now, 0, config, msg)
            )
        except Exception as e:
            msg = str(e)
            print(f"      ✗ {msg}")
            conn.execute(
                "INSERT INTO fetch_log (source,run_at,items_added,config,error) VALUES (?,?,?,?,?)",
                (label, now, 0, config, msg)
            )
        conn.commit()

    print(f"\n{'='*60}")
    print(f"  Total new articles added: {total_added}")
    print(f"{'='*60}\n")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StoryLab RSS Aggregator")
    parser.add_argument("--config",  default="travel_tech_ux",
                         choices=["travel_tech_ux", "fan_atlas_insiders", "longitude"])
    parser.add_argument("--days",    type=int, default=MAX_DAYS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(config=args.config, dry_run=args.dry_run, max_days=args.days)
