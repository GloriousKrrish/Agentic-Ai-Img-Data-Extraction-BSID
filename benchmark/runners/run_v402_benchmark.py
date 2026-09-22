import sys
import os
import time
import json
import requests
import argparse
from pathlib import Path

ROOT = Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main")
sys.path.insert(0, str(ROOT))

from benchmark.evaluators.v402_evaluator import v402_evaluator

BASE_URL = "http://127.0.0.1:8000"
DS_DIR = ROOT / "benchmark" / "datasets"
GT_DIR = ROOT / "benchmark" / "ground_truth"
REPORTS_DIR = ROOT / "benchmark" / "reports"

os.makedirs(REPORTS_DIR, exist_ok=True)

def run_v402_benchmark(mode="baseline"):
    print("==================================================")
    print(f"  v4.0.2 BENCHMARK RUNNER — MODE: {mode.upper()}")
    print("==================================================")

    gt_files = sorted(list(GT_DIR.glob("*.json")))
    print(f"Found {len(gt_files)} ground-truth document specifications.")

    doc_results = []
    confidence_buckets = {
        "0-50%": {"total": 0, "correct": 0},
        "50-70%": {"total": 0, "correct": 0},
        "70-80%": {"total": 0, "correct": 0},
        "80-90%": {"total": 0, "correct": 0},
        "90-95%": {"total": 0, "correct": 0},
        "95-100%": {"total": 0, "correct": 0}
    }

    class_counts = {"A": {"total": 0, "correct": 0}, "B": {"total": 0, "correct": 0}, "C": {"total": 0, "correct": 0}}

    for idx, gt_path in enumerate(gt_files, 1):
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        fn = gt_data["filename"]
        doc_id = gt_data["doc_id"]
        source_class = gt_data.get("source_class", "INDEPENDENTLY_ANNOTATED_FIXTURE")
        s_class = "A" if "REAL" in source_class else ("C" if "GENERATED" in source_class else "B")

        ds_path = DS_DIR / fn
        if not ds_path.exists():
            print(f"[{idx}/{len(gt_files)}] MISSING DATASET FILE: {fn}")
            continue

        print(f"\n[{idx}/{len(gt_files)}] PROCESSING: {doc_id} ({fn}) — Class {s_class}")

        mime_type = "image/png"
        if fn.endswith(".csv"):
            mime_type = "text/csv"
        elif fn.endswith(".xlsx"):
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif fn.endswith(".pdf"):
            mime_type = "application/pdf"

        with open(ds_path, "rb") as f:
            files = {"file": (fn, f.read(), mime_type)}

        t_start = time.time()
        res_up = requests.post(f"{BASE_URL}/api/jobs", files=files)
        if res_up.status_code != 201:
            print(f"  Upload failed: HTTP {res_up.status_code}")
            continue

        job_info = res_up.json()
        job_id = job_info.get("jobId") or job_info.get("job", {}).get("job_id")

        # Poll until terminal state
        job_final = None
        while time.time() - t_start < 90:
            j = requests.get(f"{BASE_URL}/api/jobs/{job_id}").json()
            st = j.get("status")
            if st in ["Completed", "Failed", "WaitingForReview"]:
                job_final = j
                break
            time.sleep(1.0)

        if not job_final:
            job_final = requests.get(f"{BASE_URL}/api/jobs/{job_id}").json()

        total_t = time.time() - t_start
        status = job_final.get("status")
        conf_val = job_final.get("confidence") or 95.0

        rows = job_final.get("rows", [])
        extracted_fields = rows[0].get("fields", {}) if rows else {}

        # Fetch Evidence
        res_ev = requests.get(f"{BASE_URL}/api/jobs/{job_id}/evidence").json()
        evidences = res_ev.get("evidences", {})

        # Evaluate against Ground Truth
        eval_res = v402_evaluator.evaluate_document(gt_data, {"fields": extracted_fields})
        eval_res["latency_sec"] = round(total_t, 2)
        eval_res["status"] = status
        eval_res["confidence"] = conf_val
        eval_res["evidence_count"] = len(evidences)

        # Bucket Confidence
        c_pct = conf_val
        b_key = "0-50%"
        if c_pct >= 95: b_key = "95-100%"
        elif c_pct >= 90: b_key = "90-95%"
        elif c_pct >= 80: b_key = "80-90%"
        elif c_pct >= 70: b_key = "70-80%"
        elif c_pct >= 50: b_key = "50-70%"

        confidence_buckets[b_key]["total"] += eval_res["total_gt_fields"]
        confidence_buckets[b_key]["correct"] += eval_res["correct"]

        class_counts[s_class]["total"] += eval_res["total_gt_fields"]
        class_counts[s_class]["correct"] += eval_res["correct"]

        doc_results.append(eval_res)
        print(f"  State={status}, Extracted={len(extracted_fields)}, Accuracy={eval_res['field_accuracy_pct']}%, Duration={total_t:.2f}s")

    # Generate Summary Metrics
    tot_docs = len(doc_results)
    tot_fields = sum(d["total_gt_fields"] for d in doc_results)
    tot_correct = sum(d["correct"] for d in doc_results)
    tot_incorrect = sum(d["incorrect"] for d in doc_results)
    tot_missing = sum(d["missing"] for d in doc_results)
    tot_hallucinated = sum(d["hallucinated"] for d in doc_results)

    field_acc = (tot_correct / tot_fields * 100.0) if tot_fields > 0 else 0.0
    hitl_count = sum(1 for d in doc_results if d["status"] == "WaitingForReview")
    hitl_rate = (hitl_count / tot_docs * 100.0) if tot_docs > 0 else 0.0
    avg_lat = sum(d["latency_sec"] for d in doc_results) / tot_docs if tot_docs > 0 else 0.0

    # Class A & B Accuracy (Independent)
    indep_total = class_counts["A"]["total"] + class_counts["B"]["total"]
    indep_correct = class_counts["A"]["correct"] + class_counts["B"]["correct"]
    indep_acc = (indep_correct / indep_total * 100.0) if indep_total > 0 else 0.0

    summary_metrics = {
        "mode": mode,
        "total_documents": tot_docs,
        "total_fields": tot_fields,
        "correct_fields": tot_correct,
        "incorrect_fields": tot_incorrect,
        "missing_fields": tot_missing,
        "hallucinated_fields": tot_hallucinated,
        "overall_field_accuracy_pct": round(field_acc, 2),
        "independent_accuracy_pct": round(indep_acc, 2),
        "hitl_rate_pct": round(hitl_rate, 2),
        "average_latency_sec": round(avg_lat, 2),
        "confidence_analysis": confidence_buckets,
        "class_breakdown": class_counts
    }

    # Save JSON files
    with open(REPORTS_DIR / f"v402_{mode}_document_results.json", "w", encoding="utf-8") as f:
        json.dump(doc_results, f, indent=2)

    with open(REPORTS_DIR / f"v402_{mode}_field_accuracy.json", "w", encoding="utf-8") as f:
        json.dump(summary_metrics, f, indent=2)

    with open(ROOT / "V4_0_2_DOCUMENT_RESULTS.json", "w", encoding="utf-8") as f:
        json.dump(doc_results, f, indent=2)

    with open(ROOT / "V4_0_2_FIELD_ACCURACY.json", "w", encoding="utf-8") as f:
        json.dump(summary_metrics, f, indent=2)

    # Generate Markdown Report
    report_filename = "V4_0_2_BASELINE_REPORT.md" if mode == "baseline" else "V4_0_2_IMPROVED_REPORT.md"
    report_path = ROOT / report_filename

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# v4.0.2 Benchmark Report ({mode.upper()})\n\n")
        f.write("## Summary Metrics\n\n")
        f.write(f"- **Total Documents Benchmarked**: {tot_docs}\n")
        f.write(f"- **Total Expected Ground Truth Fields**: {tot_fields}\n")
        f.write(f"- **Correct Fields**: {tot_correct}\n")
        f.write(f"- **Incorrect Fields**: {tot_incorrect}\n")
        f.write(f"- **Missing Fields**: {tot_missing}\n")
        f.write(f"- **Hallucinated Fields**: {tot_hallucinated}\n")
        f.write(f"- **Overall Field Accuracy**: `{field_acc:.2f}%`\n")
        f.write(f"- **Independent Field Accuracy (Class A & B)**: `{indep_acc:.2f}%`\n")
        f.write(f"- **HITL Rate**: `{hitl_rate:.2f}%` ({hitl_count}/{tot_docs})\n")
        f.write(f"- **Average Latency**: `{avg_lat:.2f}s` / document\n\n")

        f.write("## Provenance Breakdown\n\n")
        f.write("| Source Class | Provenance Description | Total Fields | Correct | Accuracy |\n")
        f.write("|---|---|---|---|---|\n")
        for sc in ["A", "B", "C"]:
            st = class_counts[sc]["total"]
            sc_corr = class_counts[sc]["correct"]
            sc_acc = (sc_corr / st * 100.0) if st > 0 else 0.0
            desc = "Source Class A (Real Reference)" if sc == "A" else ("Source Class B (Annotated Fixture)" if sc == "B" else "Source Class C (Project Fixture)")
            f.write(f"| Class {sc} | {desc} | {st} | {sc_corr} | `{sc_acc:.2f}%` |\n")

        f.write("\n## Confidence Calibration Bucketing\n\n")
        f.write("| Confidence Band | Total Fields | Correct Fields | Measured Accuracy |\n")
        f.write("|---|---|---|---|\n")
        for cb, data in confidence_buckets.items():
            cb_tot = data["total"]
            cb_corr = data["correct"]
            cb_acc = (cb_corr / cb_tot * 100.0) if cb_tot > 0 else 0.0
            f.write(f"| `{cb}` | {cb_tot} | {cb_corr} | `{cb_acc:.2f}%` |\n")

        f.write("\n## Per-Document Execution Breakdown\n\n")
        f.write("| Document ID | Filename | Class | Status | Fields | Accuracy | Latency |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for d in doc_results:
            sc_tag = "A" if "REAL" in d["source_class"] else ("C" if "GENERATED" in d["source_class"] else "B")
            f.write(f"| {d['document_id']} | `{d['filename']}` | Class {sc_tag} | {d['status']} | {d['total_gt_fields']} | `{d['field_accuracy_pct']}%` | `{d['latency_sec']}s` |\n")

    print(f"\nSaved report to {report_path}")
    return summary_metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="baseline", choices=["baseline", "improved"])
    args = parser.parse_args()
    run_v402_benchmark(args.mode)
