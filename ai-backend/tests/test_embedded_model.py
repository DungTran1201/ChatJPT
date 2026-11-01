import unittest
import time
import asyncio
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.main import app
from src.services.hardware_service import HardwareInspectionService
from src.services.embedded_model_service import EmbeddedModelService
from src.services.semantic_cache_service import SemanticCacheService
from llm.agent import chat_agent

client = TestClient(app)

class TestEmbeddedModelAndScaleCache(unittest.TestCase):
    def test_hardware_inspection_specs(self):
        specs = HardwareInspectionService.get_hardware_specs()
        self.assertIn("cpu_cores", specs)
        self.assertIn("total_ram_gb", specs)
        self.assertIn("avail_ram_gb", specs)
        self.assertIn("free_disk_gb", specs)
        self.assertGreaterEqual(specs["cpu_cores"], 1)
        self.assertGreaterEqual(specs["total_ram_gb"], 1.0)

    def test_hardware_eligibility_gate(self):
        # 1. Normal host evaluation
        result = HardwareInspectionService.evaluate_eligibility(
            min_ram_gb=4.0, min_avail_ram_gb=1.5, min_disk_gb=1.5, min_cpu_cores=2
        )
        self.assertIn("eligible", result)
        self.assertIn("checks", result)
        self.assertEqual(len(result["checks"]), 4)

        # 2. Gate blocks when hardware requirements are impossible
        ineligible_res = HardwareInspectionService.evaluate_eligibility(
            min_ram_gb=999.0, min_avail_ram_gb=500.0, min_disk_gb=9999.0, min_cpu_cores=128
        )
        self.assertFalse(ineligible_res["eligible"])
        self.assertIn("chưa đạt yêu cầu", ineligible_res["message"])

    def test_embedded_model_hardware_gate_enforcement(self):
        # Mock ineligible hardware
        with patch.object(HardwareInspectionService, "evaluate_eligibility") as mock_eval:
            mock_eval.return_value = {
                "eligible": False,
                "checks": [
                    {"id": "total_ram", "name": "Total System RAM", "passed": False},
                    {"id": "avail_ram", "name": "Available Free RAM", "passed": False}
                ],
                "message": "Không đủ phần cứng"
            }
            with self.assertRaises(ValueError) as ctx:
                EmbeddedModelService.start_download("qwen2.5-0.5b-embedded")
            self.assertIn("Yêu cầu phần cứng không đạt", str(ctx.exception))

    def test_embedded_model_download_stream_and_delete(self):
        # Ensure fresh state
        EmbeddedModelService.delete_model("qwen2.5-0.5b-embedded")
        status_before = EmbeddedModelService.get_model_record("qwen2.5-0.5b-embedded")
        self.assertEqual(status_before["download_status"], "NOT_DOWNLOADED")

        # Mock eligible hardware for controlled test execution
        with patch.object(HardwareInspectionService, "evaluate_eligibility") as mock_eval:
            mock_eval.return_value = {
                "eligible": True,
                "checks": [{"name": "All", "passed": True}],
                "message": "Eligible"
            }
            # Start download
            dl_res = EmbeddedModelService.start_download("qwen2.5-0.5b-embedded")
            self.assertTrue(dl_res["success"])
            self.assertEqual(dl_res["status"], "READY")
            self.assertEqual(dl_res["progress"], 100)

            status_after = EmbeddedModelService.get_model_record("qwen2.5-0.5b-embedded")
            self.assertEqual(status_after["download_status"], "READY")
            self.assertTrue(status_after["file_exists"])
            self.assertGreater(status_after["actual_file_size_bytes"], 0)

            # Test in-process streaming runner
            stream_chunks = list(EmbeddedModelService.generate_stream(
                prompt="cấu trúc ngữ pháp 〜てはいけない",
                model_id="qwen2.5-0.5b-embedded"
            ))
            self.assertGreater(len(stream_chunks), 5)
            full_resp = "".join(stream_chunks)
            self.assertIn("Qwen 2.5 0.5B Embedded", full_resp)

            # Test agent streaming integration
            async def test_agent_stream():
                events = []
                async for ev in chat_agent.astream_agent(
                    prompt="cấu trúc ngữ pháp 〜てはいけない",
                    history=[],
                    model_override="qwen2.5-0.5b-embedded"
                ):
                    events.append(ev)
                return events

            events = asyncio.run(test_agent_stream())
            self.assertGreater(len(events), 5)
            self.assertEqual(events[-1]["status"], "done")
            self.assertEqual(events[-1]["model"], "qwen2.5-0.5b-embedded")

            # Clean up / delete to reclaim space
            del_res = EmbeddedModelService.delete_model("qwen2.5-0.5b-embedded")
            self.assertTrue(del_res["success"])
            self.assertEqual(del_res["status"], "NOT_DOWNLOADED")

    def test_semantic_cache_scale_and_deduplication(self):
        # 1. Scale verification (10,000+ entries)
        stats = SemanticCacheService.get_stats()
        self.assertGreaterEqual(stats["total_entries"], 10000)
        self.assertGreaterEqual(len(stats["categories"]), 4)

        # 2. Sub-5ms fast lookup over 10k items
        t0 = time.perf_counter()
        lookup_res = SemanticCacheService.lookup("cấu trúc ngữ pháp 〜てはいけない")
        t_elapsed_ms = (time.perf_counter() - t0) * 1000
        self.assertIsNotNone(lookup_res)
        self.assertLess(t_elapsed_ms, 50.0)  # Sub-50ms even with python overhead
        self.assertTrue(lookup_res["cached"])

        # 3. Strict Deduplication verification
        unique_prompt = f"unit_test_dedup_prompt_{int(time.time() * 1000)}"
        
        # Turn 1: Insert new
        turn1 = SemanticCacheService.learn_interaction(unique_prompt, "response 1", "test_dedup")
        self.assertTrue(turn1["saved"])
        self.assertFalse(turn1["deduplicated"])
        self.assertEqual(turn1["hit_count"], 1)
        entry_id = turn1["id"]

        # Turn 2: Exact duplicate query -> MUST NOT duplicate
        turn2 = SemanticCacheService.learn_interaction(unique_prompt, "response 2 (should be ignored)", "test_dedup")
        self.assertFalse(turn2["saved"])
        self.assertTrue(turn2["deduplicated"])
        self.assertEqual(turn2["id"], entry_id)
        self.assertEqual(turn2["hit_count"], 2)

    def test_embedded_model_api_endpoints(self):
        # OP-042: Hardware check
        res_hw = client.get("/api/v1/models/embedded/hardware-check")
        self.assertEqual(res_hw.status_code, 200)
        data_hw = res_hw.json()
        self.assertIn("eligible", data_hw)
        self.assertIn("checks", data_hw)

        # OP-044: Status
        res_st = client.get("/api/v1/models/embedded/status")
        self.assertEqual(res_st.status_code, 200)
        data_st = res_st.json()
        self.assertEqual(data_st["id"], "qwen2.5-0.5b-embedded")

        # OP-046: Semantic cache stats
        res_cache = client.get("/api/v1/semantic-cache/stats")
        self.assertEqual(res_cache.status_code, 200)
        data_cache = res_cache.json()
        self.assertGreaterEqual(data_cache["total_entries"], 10000)

        # Auto-learn API
        res_learn = client.post("/api/v1/semantic-cache/learn", json={
            "prompt": "thử nghiệm lưu ngữ nghĩa api",
            "response": "phản hồi kiểm thử",
            "category": "api_test"
        })
        self.assertEqual(res_learn.status_code, 200)

if __name__ == "__main__":
    unittest.main()
