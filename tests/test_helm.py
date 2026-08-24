import os
import sqlite3
import tempfile
import unittest
import json
from unittest.mock import patch

from core.aggregator import init_db
from core.ai_summary import ensure_ai_tables, generate_flywheel_brief, generate_summary
from core.helm import (build_payload, create_signal_from_article, ensure_helm_tables,
                       get_signal, prepare_signals_from_approved_brief, publish_approved_brief, publish_signals,
                       save_signal, signal_external_id)


class FakeResponse:
    status = 200
    headers = {}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def getcode(self): return self.status


class FakeOpenAIResponse(FakeResponse):
    def __init__(self, summary="Source-backed summary.", rationale="Review the cited source material."):
        self.payload = json.dumps({"output": [{"content": [{"type": "output_text", "text": json.dumps({
            "summary_text": summary, "rationale_text": rationale,
        })}]}]}).encode("utf-8")
    def read(self): return self.payload


class HelmSignalTests(unittest.TestCase):
    def setUp(self):
        self.db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db.close()
        self.conn = sqlite3.connect(self.db.name)
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)
        self.conn.execute("""INSERT INTO articles
            (url_hash, source, category, title, url, summary, published_date, fetched_date, relevance_score, story_type, config)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", ("abc123", "Test source", "nil_case_study", "A real source", "https://example.test/source", "A factual RSS summary.", "2026-08-13T15:00:00Z", "2026-08-13T16:00:00Z", 5, "case-study", "fan_atlas_insiders"))
        self.conn.commit()
        self.article_id = self.conn.execute("SELECT id FROM articles").fetchone()[0]

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db.name)

    def approved_signal(self):
        created = create_signal_from_article(self.conn, "fan_atlas_insiders", self.article_id)["signal"]
        result = save_signal(self.conn, "fan_atlas_insiders", created["id"], {
            "title": "A real source", "summary": "A factual RSS summary.", "topic": "nil-policy",
            "signal_type": "market_signal", "primary_domain": "institutional",
            "flywheel_domains": ["institutional", "mobilizer"], "opportunity_risk": "opportunity",
            "confidence": "high", "relevance_score": 120, "recommendation": "Review the source before outreach.",
            "signal_status": "new", "review_status": "approved",
            "role_impacts": {"executive": {"relevance": 90, "why_it_matters": "It changes the institutional context.", "recommended_attention": "Review implications.", "urgency": "soon"}},
        })
        self.assertTrue(result["ok"], result)
        return result["signal"]

    def test_stable_external_id_and_domain_mapping(self):
        first = create_signal_from_article(self.conn, "fan_atlas_insiders", self.article_id)
        second = create_signal_from_article(self.conn, "fan_atlas_insiders", self.article_id)
        self.assertEqual(first["signal"]["external_id"], second["signal"]["external_id"])
        self.assertEqual(first["signal"]["primary_domain"], "institutional")
        self.assertEqual(signal_external_id("fan_atlas_insiders", self.article_id, "abc123"), first["signal"]["external_id"])

    def test_payload_validation_and_construction(self):
        signal = self.approved_signal()
        payload = build_payload(signal)
        self.assertEqual(payload["signals"][0]["relevance_score"], 100)
        self.assertEqual(payload["signals"][0]["primary_domain"], "institutional")
        self.assertIn("executive", payload["signals"][0]["role_impacts"])

    @patch.dict(os.environ, {"HELM_STRATEGY_ENDPOINT": "https://waypoint-helm-v1.nateleigh.chatgpt.site/api/integrations/strategy-lab/signals", "HELM_STRATEGY_API_KEY": "test-secret"}, clear=False)
    def test_successful_publish_and_duplicate_safe_retry(self):
        signal = self.approved_signal()
        requests = []
        def opener(req, timeout):
            requests.append(req)
            return FakeResponse()
        first = publish_signals(self.conn, "fan_atlas_insiders", [signal["id"]], opener=opener)
        second = publish_signals(self.conn, "fan_atlas_insiders", [signal["id"]], opener=opener)
        self.assertTrue(first["ok"])
        self.assertTrue(second["ok"])
        self.assertEqual(len(requests), 2)
        self.assertEqual(get_signal(self.conn, "fan_atlas_insiders", signal["id"])["helm_publish_status"], "published")

    @patch.dict(os.environ, {"HELM_STRATEGY_ENDPOINT": "https://waypoint-helm-v1.nateleigh.chatgpt.site/api/integrations/strategy-lab/signals", "HELM_STRATEGY_API_KEY": "test-secret"}, clear=False)
    def test_successful_batch_publication(self):
        first = self.approved_signal()
        self.conn.execute("""INSERT INTO articles
            (url_hash, source, category, title, url, summary, published_date, fetched_date, relevance_score, story_type, config)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", ("second-source", "Second source", "fandom_identity", "Another source", "https://example.test/second", "Another factual RSS summary.", "2026-08-13T15:00:00Z", "2026-08-13T16:00:00Z", 5, "trend-signal", "fan_atlas_insiders"))
        self.conn.commit()
        second_article_id = self.conn.execute("SELECT MAX(id) FROM articles").fetchone()[0]
        second = create_signal_from_article(self.conn, "fan_atlas_insiders", second_article_id)["signal"]
        second = save_signal(self.conn, "fan_atlas_insiders", second["id"], {**second, "review_status": "approved"})["signal"]
        requests = []
        result = publish_signals(self.conn, "fan_atlas_insiders", [first["id"], second["id"]], opener=lambda req, timeout: (requests.append(req) or FakeResponse()))
        self.assertTrue(result["ok"])
        self.assertEqual(result["published"], 2)
        self.assertEqual(len(requests), 1)

    def test_missing_settings_and_authentication_failure_are_safe(self):
        signal = self.approved_signal()
        with patch.dict(os.environ, {"HELM_STRATEGY_ENDPOINT": "", "HELM_STRATEGY_API_KEY": ""}, clear=False):
            missing = publish_signals(self.conn, "fan_atlas_insiders", [signal["id"]])
        self.assertFalse(missing["ok"])
        self.assertIn("not configured", missing["message"])
        from urllib.error import HTTPError
        with patch.dict(os.environ, {"HELM_STRATEGY_ENDPOINT": "https://waypoint-helm-v1.nateleigh.chatgpt.site/api/integrations/strategy-lab/signals", "HELM_STRATEGY_API_KEY": "test-secret"}, clear=False):
            auth = publish_signals(self.conn, "fan_atlas_insiders", [signal["id"]], opener=lambda req, timeout: (_ for _ in ()).throw(HTTPError(req.full_url, 401, "Unauthorized", {}, None)))
        self.assertFalse(auth["ok"])
        self.assertEqual(get_signal(self.conn, "fan_atlas_insiders", signal["id"])["helm_publish_status"], "failed")

    def test_batch_limit_and_unapproved_signal(self):
        signal = create_signal_from_article(self.conn, "fan_atlas_insiders", self.article_id)["signal"]
        self.assertFalse(publish_signals(self.conn, "fan_atlas_insiders", [signal["id"]])["ok"])
        self.assertFalse(publish_signals(self.conn, "fan_atlas_insiders", list(range(101)))["ok"])


    def test_approved_brief_prepares_source_signals_without_publishing(self):
        ensure_ai_tables(self.conn)
        self.conn.execute("""INSERT INTO flywheel_briefs
            (config, flywheel_group, generated_at, source_article_ids, what_changed,
             why_it_matters, suggested_next_step, supporting_material, review_status)
            VALUES (?,?,?,?,?,?,?,?,?)""", ("fan_atlas_insiders", "Institutional", "2026-08-13T16:00:00Z",
            f"[{self.article_id}]", "One source changed.", "Review it.", "Validate it.", "[]", "approved"))
        self.conn.commit()
        brief_id = self.conn.execute("SELECT MAX(id) FROM flywheel_briefs").fetchone()[0]
        result = prepare_signals_from_approved_brief(self.conn, "fan_atlas_insiders", brief_id)
        self.assertTrue(result["ok"])
        self.assertEqual(result["prepared"], 1)
        signal = get_signal(self.conn, "fan_atlas_insiders", result["signal_ids"][0])
        self.assertEqual(signal["review_status"], "draft")
        self.assertEqual(signal["helm_publish_status"], "not_published")

    def test_unapproved_brief_cannot_prepare_sources(self):
        ensure_ai_tables(self.conn)
        self.conn.execute("""INSERT INTO flywheel_briefs
            (config, flywheel_group, generated_at, source_article_ids, what_changed,
             why_it_matters, suggested_next_step, supporting_material, review_status)
            VALUES (?,?,?,?,?,?,?,?,?)""", ("fan_atlas_insiders", "Institutional", "2026-08-13T16:00:00Z",
            f"[{self.article_id}]", "One source changed.", "Review it.", "Validate it.", "[]", "draft"))
        self.conn.commit()
        brief_id = self.conn.execute("SELECT MAX(id) FROM flywheel_briefs").fetchone()[0]
        result = prepare_signals_from_approved_brief(self.conn, "fan_atlas_insiders", brief_id)
        self.assertFalse(result["ok"])
        self.assertIn("Approve", result["message"])

    def test_daily_briefs_only_include_never_before_briefed_sources(self):
        first = generate_flywheel_brief(self.conn, "fan_atlas_insiders", "Institutional")
        self.assertTrue(first["ok"])
        self.assertEqual(first["brief"]["source_article_ids"], [self.article_id])
        repeat = generate_flywheel_brief(self.conn, "fan_atlas_insiders", "Institutional")
        self.assertFalse(repeat["ok"])
        self.assertEqual(repeat["error"], "no_new_articles")
        self.conn.execute("""INSERT INTO articles
            (url_hash, source, category, title, url, summary, published_date, fetched_date, relevance_score, story_type, config)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", ("new-source", "New source", "nil_case_study", "A new source", "https://example.test/new", "New factual RSS summary.", "2026-08-13T17:00:00Z", "2026-08-13T17:00:00Z", 5, "case-study", "fan_atlas_insiders"))
        self.conn.commit()
        later = generate_flywheel_brief(self.conn, "fan_atlas_insiders", "Institutional")
        self.assertTrue(later["ok"])
        self.assertEqual(len(later["brief"]["source_article_ids"]), 1)
        self.assertEqual(later["brief"]["new_source_article_ids"], later["brief"]["source_article_ids"])

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False)
    def test_daily_and_weekly_summaries_track_separate_new_source_histories(self):
        opener = lambda req, timeout: FakeOpenAIResponse()
        monday_daily = generate_summary(self.conn, "fan_atlas_insiders", "Institutional", "daily", opener=opener)
        self.assertTrue(monday_daily["ok"])
        self.assertEqual(monday_daily["article_count"], 1)
        no_repeat = generate_summary(self.conn, "fan_atlas_insiders", "Institutional", "daily", opener=opener)
        self.assertFalse(no_repeat["ok"])
        self.assertEqual(no_repeat["error"], "no_new_articles")
        weekly = generate_summary(self.conn, "fan_atlas_insiders", "Institutional", "weekly", opener=opener)
        self.assertTrue(weekly["ok"])
        self.assertEqual(weekly["article_count"], 1)
        self.conn.execute("""INSERT INTO articles
            (url_hash, source, category, title, url, summary, published_date, fetched_date, relevance_score, story_type, config)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", ("ai-new-source", "New source", "nil_case_study", "A new source", "https://example.test/new-ai", "New factual RSS summary.", "2026-08-13T17:00:00Z", "2026-08-13T17:00:00Z", 5, "case-study", "fan_atlas_insiders"))
        self.conn.commit()
        tuesday_daily = generate_summary(self.conn, "fan_atlas_insiders", "Institutional", "daily", opener=opener)
        self.assertTrue(tuesday_daily["ok"])
        self.assertEqual(tuesday_daily["article_count"], 1)
        next_weekly = generate_summary(self.conn, "fan_atlas_insiders", "Institutional", "weekly", opener=opener)
        self.assertTrue(next_weekly["ok"])
        self.assertEqual(next_weekly["article_count"], 1)

    @patch.dict(os.environ, {"HELM_STRATEGY_ENDPOINT": "https://waypoint-helm-v1.nateleigh.chatgpt.site/api/integrations/strategy-lab/signals", "HELM_STRATEGY_API_KEY": "test-secret"}, clear=False)
    def test_approved_brief_publishes_one_evidence_backed_signal(self):
        ensure_ai_tables(self.conn)
        self.conn.execute("""INSERT INTO flywheel_briefs
            (config, flywheel_group, generated_at, source_article_ids, freshness_date, what_changed,
             why_it_matters, suggested_next_step, supporting_material, review_status)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", ("fan_atlas_insiders", "Institutional", "2026-08-13T16:00:00Z",
            f"[{self.article_id}]", "2026-08-13T15:00:00Z", "One source changed.", "Review it.", "Validate it.",
            '[{"title":"A real source","source":"Test source","url":"https://example.test/source","published_date":"2026-08-13T15:00:00Z","exact_rss_summary":"A factual RSS summary."}]', "approved"))
        self.conn.commit()
        brief_id = self.conn.execute("SELECT MAX(id) FROM flywheel_briefs").fetchone()[0]
        requests = []
        result = publish_approved_brief(self.conn, "fan_atlas_insiders", brief_id, opener=lambda req, timeout: (requests.append(req) or FakeResponse()))
        self.assertTrue(result["ok"])
        self.assertEqual(len(requests), 1)
        body = requests[0].data.decode("utf-8")
        self.assertIn(f"strategy-lab:fan_atlas_insiders:brief:{brief_id}", body)
        self.assertIn("https://example.test/source", body)
        self.assertIn("[INSTITUTIONAL] Fan Atlas flywheel brief", body)
        self.assertIn("Primary Helm domain: institutional", body)
        self.assertIn('"primary_domain":"institutional"', body)
        status = self.conn.execute("SELECT helm_publish_status FROM flywheel_briefs WHERE id=?", (brief_id,)).fetchone()[0]
        self.assertEqual(status, "published")


if __name__ == "__main__":
    unittest.main()
