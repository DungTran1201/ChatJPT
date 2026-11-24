"""Semantic Cache Service — B-tree exact + FTS5 n-gram similarity lookup & deduplicated auto-learning."""

import re
import unicodedata
import uuid
from typing import Any, Dict, List, Optional, Set

from src.repositories.embedded_repo import EmbeddedRepository
from src.services.offline_responder import OfflineSenseiResponder


class SemanticCacheService:
    """Manages fast semantic Q&A caching over 10,000+ entries via EmbeddedRepository."""

    def __init__(
        self,
        repo: Optional[EmbeddedRepository] = None,
        responder: Optional[OfflineSenseiResponder] = None,
    ):
        self._repo = repo or EmbeddedRepository()
        self._responder = responder or OfflineSenseiResponder()

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes unicode (NFKC), lowercases, strips punctuation for robust matching."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKC", text).lower().strip()
        cleaned = re.sub(r'[!?,.:;~`"\(\)\[\]\{\}\<\>\\/\-_*+=#@$%^&|]', " ", normalized)
        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def get_tokens(cls, text: str) -> Set[str]:
        """Extracts individual word tokens and character bi-grams in a single normalization pass."""
        norm = cls.normalize_text(text)
        tokens: Set[str] = set(norm.split())
        compact = norm.replace(" ", "")
        for i in range(len(compact) - 1):
            tokens.add(compact[i : i + 2])
        return tokens

    @classmethod
    def compute_similarity(
        cls,
        query_norm: str,
        cached_norm: str,
        keywords_str: Optional[str] = None,
    ) -> float:
        if query_norm == cached_norm:
            return 1.0

        q_tokens = cls.get_tokens(query_norm)
        c_tokens = cls.get_tokens(cached_norm)
        if not q_tokens or not c_tokens:
            return 0.0

        jaccard = len(q_tokens & c_tokens) / len(q_tokens | c_tokens)

        keyword_bonus = 0.0
        if keywords_str:
            kw_list = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
            if kw_list:
                matched_kws = sum(1 for kw in kw_list if kw in query_norm)
                keyword_bonus = 0.35 * (matched_kws / len(kw_list))

        len_ratio = min(len(query_norm), len(cached_norm)) / max(len(query_norm), len(cached_norm))
        final_score = (jaccard * 0.7 + keyword_bonus) * (0.6 + 0.4 * len_ratio)
        return min(round(final_score, 3), 1.0)

    def lookup_entry(self, prompt: str, threshold: float = 0.45) -> Optional[Dict[str, Any]]:
        query_norm = self.normalize_text(prompt)
        if not query_norm:
            return None

        # 1. Exact B-tree lookup
        exact = self._repo.get_cache_exact(query_norm)
        if exact:
            self._repo.increment_hit_count(exact["id"])
            return {
                "id": exact["id"],
                "prompt_raw": exact["prompt_raw"],
                "response_text": exact["response_text"],
                "category": exact["category"],
                "similarity": 1.0,
                "hit_count": exact["hit_count"] + 1,
                "cached": True,
            }

        # 2. FTS5 candidate search
        candidates: List[Dict[str, Any]] = []
        raw_tokens = re.findall(r"[\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+", query_norm)
        meaningful_tokens = [t for t in raw_tokens if len(t) >= 2][:6]
        if meaningful_tokens:
            fts_expression = " OR ".join(f'"{t}"' for t in meaningful_tokens)
            try:
                candidates = self._repo.search_cache_fts(fts_expression, limit=50)
            except Exception:
                candidates = []

        # 3. LIKE fallback
        if not candidates:
            parts = query_norm.split()
            first_word = parts[0] if parts else ""
            if len(first_word) >= 3:
                candidates = self._repo.search_cache_like(f"%{first_word}%", limit=30)

        if not candidates:
            return None

        best_match = None
        best_score = 0.0
        for entry in candidates:
            score = self.compute_similarity(query_norm, entry["prompt_normalized"], entry.get("keywords"))
            if score > best_score:
                best_score = score
                best_match = entry

        if best_match and best_score >= threshold:
            self._repo.increment_hit_count(best_match["id"])
            return {
                "id": best_match["id"],
                "prompt_raw": best_match["prompt_raw"],
                "response_text": best_match["response_text"],
                "category": best_match["category"],
                "similarity": best_score,
                "hit_count": best_match["hit_count"] + 1,
                "cached": True,
            }
        return None

    def learn(self, prompt_raw: str, response_text: str, category: str = "learned_chat") -> Dict[str, Any]:
        if not prompt_raw or not response_text:
            return {"saved": False, "reason": "empty_content"}

        prompt_norm = self.normalize_text(prompt_raw)
        if not prompt_norm:
            return {"saved": False, "reason": "invalid_prompt"}

        existing = self._repo.get_cache_exact(prompt_norm)
        if existing:
            self._repo.increment_hit_count(existing["id"])
            return {
                "saved": False,
                "deduplicated": True,
                "id": existing["id"],
                "hit_count": existing["hit_count"] + 1,
                "message": "Đã ghi nhận tương tác và tăng tần suất (Deduplicated)",
            }

        c_id = str(uuid.uuid4())
        words = [w for w in prompt_norm.split() if len(w) >= 3][:8]
        self._repo.insert_cache_entry(
            cache_id=c_id,
            prompt_raw=prompt_raw,
            prompt_normalized=prompt_norm,
            category=category,
            response_text=response_text,
            keywords=", ".join(words),
        )
        return {
            "saved": True,
            "deduplicated": False,
            "id": c_id,
            "hit_count": 1,
            "message": "Đã tự động lưu trữ câu hỏi và câu trả lời vào Semantic Cache",
        }

    def stats(self) -> Dict[str, Any]:
        return self._repo.get_cache_stats()

    def synthesize_offline(self, prompt: str) -> str:
        resp, should_cache = self._responder.synthesize(prompt)
        if should_cache:
            try:
                self.learn(prompt, resp, category="synthesized_offline")
            except Exception:
                pass
        return resp

    # ------------------------------------------------------------------
    # Backward-compatible classmethod API for existing callers & tests
    # ------------------------------------------------------------------
    @classmethod
    def lookup(cls, prompt: str, threshold: float = 0.45) -> Optional[Dict[str, Any]]:
        return _default_semantic_cache.lookup_entry(prompt, threshold=threshold)

    @classmethod
    def learn_interaction(cls, prompt_raw: str, response_text: str, category: str = "learned_chat") -> Dict[str, Any]:
        return _default_semantic_cache.learn(prompt_raw, response_text, category=category)

    @classmethod
    def store(cls, prompt_raw: str, response_text: str, category: str = "general", keywords: str = "") -> str:
        res = cls.learn_interaction(prompt_raw, response_text, category)
        return res["id"]

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        return _default_semantic_cache.stats()

    @classmethod
    def synthesize_offline_response(cls, prompt: str) -> str:
        return _default_semantic_cache.synthesize_offline(prompt)


_default_semantic_cache = SemanticCacheService()
