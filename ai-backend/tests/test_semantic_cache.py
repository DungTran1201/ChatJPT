import unittest
import asyncio
from src.services.semantic_cache_service import SemanticCacheService
from llm.agent import chat_agent, LangChainModelFactory, ModelQuotaTracker

class TestSemanticCacheAndFailover(unittest.TestCase):
    def test_text_normalization(self):
        # Full-width Japanese characters normalization via NFKC
        raw_jp = "Ｋｏｎｎｉｃｈｉｗａ！？　Ｓｅｎｓｅｉ"
        norm = SemanticCacheService.normalize_text(raw_jp)
        self.assertEqual(norm, "konnichiwa sensei")

    def test_similarity_computation(self):
        score_identical = SemanticCacheService.compute_similarity("konnichiwa", "konnichiwa")
        self.assertEqual(score_identical, 1.0)

        # Keyword matching
        score_keywords = SemanticCacheService.compute_similarity(
            "cho toi hoi tro tu wa va ga",
            "phan biet tro tu wa va ga",
            keywords_str="wa,ga,tro tu"
        )
        self.assertGreaterEqual(score_keywords, 0.45)

    def test_lookup_and_synthesize(self):
        # Synthesize offline Japanese explanation
        resp = SemanticCacheService.synthesize_offline_response("luyện tập kaiwa nhà hàng")
        self.assertIn("Kaiwa", resp)
        self.assertIn("すみません", resp)

        # Lookup should now hit cache
        hit = SemanticCacheService.lookup("luyện tập kaiwa nhà hàng", threshold=0.40)
        self.assertIsNotNone(hit)
        self.assertTrue(hit["cached"])
        self.assertGreaterEqual(hit["hit_count"], 1)

    def test_detect_provider_for_model(self):
        self.assertEqual(LangChainModelFactory.detect_provider_for_model("gemini-3.8-flash"), "gemini")
        self.assertEqual(LangChainModelFactory.detect_provider_for_model("llama-3.3-70b-versatile"), "groq")
        self.assertEqual(LangChainModelFactory.detect_provider_for_model("gpt-4o-mini"), "openai")
        self.assertEqual(LangChainModelFactory.detect_provider_for_model("claude-3-5-haiku"), "anthropic")
        self.assertEqual(LangChainModelFactory.detect_provider_for_model("qwen2.5-0.5b-cpu"), "ollama")
        self.assertEqual(LangChainModelFactory.detect_provider_for_model("offline-semantic-cache"), "offline")

    def test_quota_tracker_cooldown(self):
        model_name = "test-quota-model"
        self.assertTrue(ModelQuotaTracker.is_available(model_name))
        ModelQuotaTracker.record_quota_exhausted(model_name, retry_delay_seconds=60.0)
        self.assertFalse(ModelQuotaTracker.is_available(model_name))

    def test_astream_offline_semantic_cache(self):
        async def run_stream():
            events = []
            async for ev in chat_agent.astream_agent(
                prompt="xin chào sensei",
                history=[],
                model_override="offline-semantic-cache"
            ):
                events.append(ev)
            return events

        events = asyncio.run(run_stream())
        self.assertGreater(len(events), 5)
        self.assertEqual(events[-1]["status"], "done")
        self.assertEqual(events[-1]["model"], "offline-semantic-cache")

if __name__ == "__main__":
    unittest.main()
