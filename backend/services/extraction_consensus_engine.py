"""
Phase 3: Extraction Consensus Engine
Reconciles candidate values across independent extraction methods (OCR, Vision AI, PDF Text, LLM).
Scores agreement, resolves discrepancies, and flags unresolved conflicts.
"""
from typing import List, Dict, Any, Tuple
from backend.agents.evidence_models import (
    CandidateValue, ConsensusResult
)

class ExtractionConsensusEngine:
    SOURCE_WEIGHTS = {
        "HUMAN_CORRECTION": 1.0,
        "PDF_TEXT": 0.95,
        "VISION": 0.90,
        "OCR": 0.85,
        "LLM": 0.85,
        "TABLE_STRUCTURE": 0.90,
        "CALCULATION": 0.95,
        "REGEX": 0.80,
        "INFERENCE": 0.70
    }

    def reconcile_field(
        self,
        field_key: str,
        candidates: List[CandidateValue]
    ) -> ConsensusResult:
        """
        Reconciles candidate values for a field across multiple extraction passes/sources.
        """
        if not candidates:
            return ConsensusResult(
                field_key=field_key,
                reconciled_value=None,
                consensus_score=0.0,
                has_conflict=False
            )

        if len(candidates) == 1:
            cand = candidates[0]
            return ConsensusResult(
                field_key=field_key,
                reconciled_value=cand.normalized_value or cand.raw_value,
                consensus_score=cand.confidence,
                agreed_sources=[cand.source_type],
                candidates=candidates,
                has_conflict=False
            )

        # Value frequency & weight scoring
        value_scores: Dict[str, float] = {}
        value_sources: Dict[str, List[str]] = {}
        value_raw_map: Dict[str, Any] = {}

        for cand in candidates:
            raw = str(cand.raw_value or "").strip()
            norm = str(cand.normalized_value) if cand.normalized_value is not None else raw
            clean_key = norm.lower().replace(',', '').replace('$', '').replace('₹', '')

            if not clean_key:
                continue

            w = self.SOURCE_WEIGHTS.get(cand.source_type, 0.8) * cand.confidence
            value_scores[clean_key] = value_scores.get(clean_key, 0.0) + w

            if clean_key not in value_sources:
                value_sources[clean_key] = []
            value_sources[clean_key].append(cand.source_type)

            if clean_key not in value_raw_map:
                value_raw_map[clean_key] = cand.normalized_value if cand.normalized_value is not None else raw

        if not value_scores:
            first = candidates[0]
            return ConsensusResult(
                field_key=field_key,
                reconciled_value=first.raw_value,
                consensus_score=first.confidence,
                candidates=candidates,
                has_conflict=False
            )

        # Rank values
        sorted_vals = sorted(value_scores.items(), key=lambda x: x[1], reverse=True)
        top_key, top_score = sorted_vals[0]
        selected_val = value_raw_map[top_key]
        agreed = value_sources[top_key]

        has_conflict = len(sorted_vals) > 1 and abs(sorted_vals[0][1] - sorted_vals[1][1]) < 0.3
        disagreed = []
        if has_conflict:
            disagreed = value_sources[sorted_vals[1][0]]

        consensus_score = round(min(1.0, top_score / float(len(candidates))), 2)

        return ConsensusResult(
            field_key=field_key,
            reconciled_value=selected_val,
            consensus_score=consensus_score,
            agreed_sources=agreed,
            disagreed_sources=disagreed,
            candidates=candidates,
            has_conflict=has_conflict,
            conflict_resolution="Weighted consensus selected top candidate" if has_conflict else "Full consensus agreement"
        )

extraction_consensus_engine = ExtractionConsensusEngine()
