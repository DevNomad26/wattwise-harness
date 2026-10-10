# ⚡ WattWise Evaluation & Benchmarking Suite

This directory contains the automated evaluation framework for benchmarking the **WattWise Agentic Harness** (ReAct agent loop + MCP tool servers + domain skills) against the unassisted **Base `qwen3.5:4b`** model.

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Evaluation 1: Tariff & Math Reasoning Benchmark](#evaluation-1-tariff--math-reasoning-benchmark)
3. [Evaluation 2: Bill Photo Vision & State Extraction Benchmark](#evaluation-2-bill-photo-vision--state-extraction-benchmark)
4. [Running the Evaluations](#running-the-evaluations)
5. [Interactive Google Colab Notebook](#interactive-google-colab-notebook)
6. [Generated Reports & Output Files](#generated-reports--output-files)

---

## 🌟 Overview

Small language models (e.g. 4B parameters) notoriously struggle with floating-point arithmetic, multi-slab tariff calculations, and reading unstructured utility bills. The WattWise evaluation harness quantitatively measures how much accuracy, reliability, and precision are gained when pairing the LLM with deterministic MCP tools and structured domain skills.

---

## 📊 Evaluation 1: Tariff & Math Reasoning Benchmark

- **Runner Script:** [`eval/run_eval.py`](run_eval.py)
- **Dataset:** [`eval/dataset.json`](dataset.json)

### 🎯 What It Tests:
- **Multi-Slab Domestic Tariffs:** Calculates bills across diverse Indian states (Maharashtra, Gujarat, Rajasthan, Delhi, Karnataka) across various consumption slabs (40 to 500+ units).
- **Arithmetic Precision:** Evaluates fixed charges, energy charges, and state electricity duties.
- **Boundary Checks:** Tests if the model cleanly refuses or alerts the user when an unsupported state (e.g. Kerala) is requested, rather than hallucinating fake figures.
- **Solar Sizing & ROI:** Evaluates rooftop solar capacity estimation (kW) and payback periods based on monthly units consumption (`solar-roi-calculator` skill).

### ⚙️ How It Tests:
- **Base Model (Unassisted):** Receives the raw question directly through Ollama's `/api/generate` endpoint without any tools, calculator, or database lookups.
- **WattWise Harness:** Executes via `Session.ask()`, invoking the ReAct agent loop to query [`mcp_servers/tariff.py`](../mcp_servers/tariff.py) and [`mcp_servers/calculator.py`](../mcp_servers/calculator.py).
- **Scoring Engine:** Extracts numerical amounts using regular expressions and scores predictions against ground-truth values with a $\pm\text{Rs } 5$ tolerance.

---

## 👁️ Evaluation 2: Bill Photo Vision & State Extraction Benchmark

- **Runner Script:** [`eval/run_vision_eval.py`](run_vision_eval.py)
- **Dataset:** [`eval/bills_dataset.json`](bills_dataset.json)
- **Test Images:** [`eval/bills/`](bills/) (`bill_1.jpg` to `bill_6.webp`)

### 🎯 What It Tests:
- **State Identification:** Deduces the Indian state (Rajasthan, Maharashtra, Gujarat, Delhi, Karnataka) from company logos, addresses, and cities printed on the bill.
- **DISCOM Recognition:** Identifies the power distribution company (JVVNL, MSEDCL, PGVCL, BSES/Tata Power, BESCOM).
- **Structured Extraction:** Extracts meter readings, net billed units, and total payable amount into a validated `BillData` JSON schema vs. unstructured text.
- **Integrity Checks:** Evaluates automated sanity checks (e.g., verifying if $\text{Current Reading} - \text{Previous Reading} = \text{Billed Units}$ and flagging impossible jumps).

### ⚙️ How It Tests:
- **Base Model (Raw Vision):** Receives raw base64-encoded bill photos and attempts OCR in a single unassisted pass.
- **WattWise Harness:** Applies PIL image preprocessing (auto-contrast, sharpening, 1.6 MP A4 scaling), runs structured JSON extraction, and executes 2-step state derivation.

---

## 🚀 Running the Evaluations

### Option A: Accelerated on Google Colab (Recommended)
Running in Colab with a free **T4 GPU** completes all evaluations in **~2 to 3 minutes**:

1. Open [`eval/eval_colab.ipynb`](eval_colab.ipynb) in [Google Colab](https://colab.research.google.com/).
2. Select **Runtime > Change runtime type > T4 GPU**.
3. Run all cells sequentially. The notebook handles Ollama installation, model pulling, test execution, and inline report rendering.

### Option B: Running Locally

Make sure Ollama is running (`ollama serve` and `ollama pull qwen3.5:4b`), then run:

```bash
# 1. Run Tariff & Math Reasoning Benchmark
python eval/run_eval.py

# 2. Run Bill Photo Vision Benchmark
python eval/run_vision_eval.py
```

---

## 📁 Generated Reports & Output Files

| File | Description |
| :--- | :--- |
| [`eval/benchmark_report.md`](benchmark_report.md) | Summary markdown table comparing Base Model vs. Harness on tariff math. |
| [`eval/eval_results.json`](eval_results.json) | Detailed per-case execution logs, predictions, traces, and latency. |
| [`eval/vision_benchmark_report.md`](vision_benchmark_report.md) | Markdown table comparing state and factor extraction from bill photos. |
| [`eval/vision_eval_results.json`](vision_eval_results.json) | Full vision extraction outputs and score breakdowns. |
| [`eval/eval_colab.ipynb`](eval_colab.ipynb) | Ready-to-run Jupyter notebook for Google Colab. |
