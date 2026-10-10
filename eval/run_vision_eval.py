"""Vision evaluation runner: Compares Base qwen3.5:4b vs. WattWise Vision Harness
on state identification, DISCOM recognition, and bill data extraction from images.

Usage:
    python eval/run_vision_eval.py
"""

import asyncio
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
import urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
import mcp_servers.vision as vision_server

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("VISION_MODEL", os.environ.get("MAIN_MODEL", "qwen3.5:4b"))
os.environ["VISION_MODEL"] = MODEL
os.environ["MAIN_MODEL"] = MODEL
vision_server.VISION_MODEL = MODEL
DATASET_FILE = ROOT / "eval" / "bills_dataset.json"


BILLS_DIR = ROOT / "eval" / "bills"
RESULTS_FILE = ROOT / "eval" / "vision_eval_results.json"
REPORT_FILE = ROOT / "eval" / "vision_benchmark_report.md"

ALL_STATES = ["Rajasthan", "Maharashtra", "Gujarat", "Delhi", "Karnataka", "Tamil Nadu", "Uttar Pradesh", "West Bengal", "Punjab", "Haryana", "Kerala", "Telangana", "Andhra Pradesh", "Madhya Pradesh"]


def encode_image_base64(image_path: Path) -> str:
    """Read image and return base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def query_raw_ollama_vision(prompt: str, image_path: Path, model: str = MODEL) -> tuple[str, float]:
    """Direct unassisted vision prompt to Ollama."""
    url = f"{OLLAMA_HOST}/api/generate"
    b64_img = encode_image_base64(image_path)
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "images": [b64_img],
        "stream": False,
        "options": {"temperature": 0.0}
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
            elapsed = round(time.time() - start, 2)
            return data.get("response", ""), elapsed
    except Exception as exc:
        elapsed = round(time.time() - start, 2)
        return f"Error querying vision model: {exc}", elapsed


def detect_state_from_text(text: str) -> str | None:
    """Find Indian state mentioned in the text."""
    for st in ALL_STATES:
        if re.search(rf"\b{re.escape(st)}\b", text, re.IGNORECASE):
            return st
    return None


def run_harness_vision_extraction(image_path: Path) -> tuple[dict, str, float]:
    """Run WattWise structured vision extraction pipeline with two-step state derivation."""
    start = time.time()
    try:
        result_json_str = vision_server.extract_bill_data(str(image_path))
        data = json.loads(result_json_str)

        elapsed = round(time.time() - start, 2)
        state_found = data.get("state")
        return data, state_found or "Unknown", elapsed
    except Exception as exc:
        elapsed = round(time.time() - start, 2)
        return {"error": str(exc)}, "Error", elapsed


async def run_vision_evaluation():
    print("=" * 70)
    print(f"👁️ WattWise Vision Benchmark: State Guessing & Bill Extraction ({MODEL})")
    print("=" * 70)

    if not DATASET_FILE.exists():
        print(f"Error: Dataset not found at {DATASET_FILE}")
        return

    with open(DATASET_FILE, "r") as f:
        cases = json.load(f)

    print(f"Loaded {len(cases)} bill test cases from {DATASET_FILE.name}.\n")

    results = []

    for idx, case in enumerate(cases, 1):
        case_id = case["id"]
        filename = case["filename"]
        expected_state = case["state"]
        expected_discoms = case.get("expected_discom_keywords", [])
        image_path = BILLS_DIR / filename

        print(f"[{idx}/{len(cases)}] Evaluating: {case_id} ({filename}) | Expected State: {expected_state}")

        if not image_path.exists():
            print(f"   ❌ Image file not found: {image_path}\n")
            continue

        # 1. Base Vision Model (Unassisted)
        print(f"   ➔ Running Base {MODEL} Vision (Direct raw photo prompt)...", end="", flush=True)
        base_prompt = case["prompt"]
        base_answer, base_time = query_raw_ollama_vision(base_prompt, image_path)
        base_detected_state = detect_state_from_text(base_answer)
        base_state_correct = (base_detected_state or "").lower() == expected_state.lower()
        base_discom_correct = any(d.lower() in base_answer.lower() for d in expected_discoms)
        print(f" Done ({base_time}s)")

        # 2. WattWise Vision Harness (Structured OCR + Preprocessing + 2-step State Derivation)
        print(f"   ➔ Running WattWise Vision Pipeline (PIL Preprocessing + Schema + State Mapping)...", end="", flush=True)
        harness_data, harness_detected_state, harness_time = run_harness_vision_extraction(image_path)
        harness_state_correct = (harness_detected_state or "").lower() == expected_state.lower()
        
        harness_discom = str(harness_data.get("discom") or "")
        harness_discom_correct = any(d.lower() in harness_discom.lower() for d in expected_discoms)
        print(f" Done ({harness_time}s)")

        # Units and amount extracted
        units_extracted = harness_data.get("units")
        amount_extracted = harness_data.get("total_amount_due")
        warnings = harness_data.get("warnings", [])

        score_base = "✅ PASS" if base_state_correct else "❌ FAIL"
        score_harness = "✅ PASS" if harness_state_correct else "❌ FAIL"
        print(f"   State Guess: Base = {score_base} ({base_detected_state or 'None'}) | Harness = {score_harness} ({harness_detected_state})\n")

        results.append({
            "id": case_id,
            "filename": filename,
            "ground_truth_state": expected_state,
            "expected_discoms": expected_discoms,
            "base_state": base_detected_state or "Not Identified",
            "base_state_correct": base_state_correct,
            "base_discom_correct": base_discom_correct,
            "base_time": base_time,
            "base_raw_output": base_answer,
            "harness_state": harness_detected_state,
            "harness_state_correct": harness_state_correct,
            "harness_discom": harness_discom or "Not Extracted",
            "harness_discom_correct": harness_discom_correct,
            "harness_units": units_extracted,
            "harness_amount": amount_extracted,
            "harness_warnings": warnings,
            "harness_time": harness_time
        })

    # Summary Statistics
    total_cases = len(results)
    base_state_passes = sum(1 for r in results if r["base_state_correct"])
    harness_state_passes = sum(1 for r in results if r["harness_state_correct"])

    base_discom_passes = sum(1 for r in results if r["base_discom_correct"])
    harness_discom_passes = sum(1 for r in results if r["harness_discom_correct"])

    base_state_acc = (base_state_passes / total_cases) * 100 if total_cases > 0 else 0
    harness_state_acc = (harness_state_passes / total_cases) * 100 if total_cases > 0 else 0

    base_discom_acc = (base_discom_passes / total_cases) * 100 if total_cases > 0 else 0
    harness_discom_acc = (harness_discom_passes / total_cases) * 100 if total_cases > 0 else 0

    # Save Results JSON
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed vision eval results saved to {RESULTS_FILE}")

    # Generate Markdown Report
    report_content = f"""# 👁️ Vision Benchmark Report: State & Factor Extraction

**Model Evaluated:** `{MODEL}`  
**Total Bill Photos:** {total_cases}  
**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}

---

## 🏆 Key Metric Summary

| Metric | Base `{MODEL}` Vision (Unassisted) | WattWise Vision Pipeline (Harness) | Gain |
| :--- | :---: | :---: | :---: |
| **State Identification Accuracy** | **{base_state_acc:.1f}%** ({base_state_passes}/{total_cases}) | **{harness_state_acc:.1f}%** ({harness_state_passes}/{total_cases}) | **+{harness_state_acc - base_state_acc:.1f}%** |
| **DISCOM Recognition Accuracy** | **{base_discom_acc:.1f}%** ({base_discom_passes}/{total_cases}) | **{harness_discom_acc:.1f}%** ({harness_discom_passes}/{total_cases}) | **+{harness_discom_acc - base_discom_acc:.1f}%** |
| **Structured JSON Schema** | ❌ Unstructured text | ✅ Strict `BillData` JSON schema | Machine readable |
| **Integrity & Sanity Checks** | ❌ None | ✅ Checked `Current - Prev = Units` | Flags anomalies |

---

## 📋 Bill-by-Bill State & Factor Extraction Results

| Bill | Ground Truth State | Base Model Detected State | Harness Detected State | Base Match | Harness Match | Units Extracted | Amount Due (Rs) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
"""

    for r in results:
        b_icon = "✅" if r["base_state_correct"] else "❌"
        h_icon = "✅" if r["harness_state_correct"] else "❌"
        units_str = str(r["harness_units"]) if r["harness_units"] is not None else "N/A"
        amount_str = f"Rs {r['harness_amount']}" if r["harness_amount"] is not None else "N/A"
        report_content += f"| `{r['filename']}` | **{r['ground_truth_state']}** | {r['base_state']} | **{r['harness_state']}** | {b_icon} | {h_icon} | {units_str} | {amount_str} |\n"

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Benchmark Markdown report generated at {REPORT_FILE}")

    print("\n" + "=" * 70)
    print(f"FINAL RESULT: Base State Accuracy = {base_state_acc:.1f}% | Harness State Accuracy = {harness_state_acc:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_vision_evaluation())
