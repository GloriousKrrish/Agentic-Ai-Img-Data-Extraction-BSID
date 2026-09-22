import json
import re
from typing import Dict, Any, List, Tuple

def normalize_key(k: str) -> str:
    return k.lower().replace("_", "").replace("-", "").replace(" ", "")

def normalize_val(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    try:
        clean_num = s.replace('$', '').replace(',', '').replace('₹', '').strip()
        num_float = float(clean_num)
        return f"{num_float:.2f}"
    except (ValueError, TypeError):
        pass
    return s.lower()

class V402Evaluator:
    def evaluate_field(self, expected_val: Any, actual_val: Any) -> str:
        if actual_val is None or str(actual_val).strip() == "":
            return "MISSING"
        exp_norm = normalize_val(expected_val)
        act_norm = normalize_val(actual_val)
        if exp_norm == act_norm:
            return "CORRECT"
        return "INCORRECT"

    def evaluate_document(self, gt_doc: Dict[str, Any], extracted_doc: Dict[str, Any]) -> Dict[str, Any]:
        gt_fields = gt_doc.get("fields", {})
        extracted_fields = extracted_doc.get("fields", {})

        # Map normalized keys to actual extracted keys
        norm_extracted = {normalize_key(k): (k, v) for k, v in extracted_fields.items()}

        correct = 0
        incorrect = 0
        missing = 0
        hallucinated = 0
        field_evals = {}

        for key, exp_val in gt_fields.items():
            norm_k = normalize_key(key)
            if norm_k not in norm_extracted:
                missing += 1
                field_evals[key] = {"expected": exp_val, "actual": None, "status": "MISSING"}
            else:
                actual_key, act_val = norm_extracted[norm_k]
                status = self.evaluate_field(exp_val, act_val)
                if status == "CORRECT":
                    correct += 1
                else:
                    incorrect += 1
                field_evals[key] = {"expected": exp_val, "actual": act_val, "status": status}

        gt_norm_keys = set(normalize_key(k) for k in gt_fields.keys())
        for key, act_val in extracted_fields.items():
            norm_k = normalize_key(key)
            if norm_k not in gt_norm_keys and norm_k not in ["serno", "invoiceimagelink", "lineitems"]:
                hallucinated += 1
                field_evals[key] = {"expected": None, "actual": act_val, "status": "HALLUCINATED"}

        total_gt = len(gt_fields)
        acc = (correct / total_gt * 100.0) if total_gt > 0 else 0.0

        return {
            "document_id": gt_doc.get("document_id"),
            "filename": gt_doc.get("filename"),
            "source_class": gt_doc.get("source_class", "INDEPENDENTLY_ANNOTATED_FIXTURE"),
            "total_gt_fields": total_gt,
            "correct": correct,
            "incorrect": incorrect,
            "missing": missing,
            "hallucinated": hallucinated,
            "field_accuracy_pct": round(acc, 2),
            "field_details": field_evals
        }

v402_evaluator = V402Evaluator()
