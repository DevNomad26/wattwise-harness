#  WattWise

**WattWise** is an open-source, locally-hosted AI verification system that acts as your personal electricity bill auditor. 

By leveraging an original **Model Harness** and strict **Agent Skills**, WattWise allows consumers to securely audit their electricity bills for mathematical errors, impossible consumption readings, and tariff mistakes—all without sacrificing their personal data privacy.

---

##  The Problem We Solve & Data Privacy
Electricity bills are notoriously difficult to decipher, and mistakes by distribution companies (DISCOMs) are common. Consumers often overpay because they cannot mathematically verify complex tariff structures, slab rates, or net-metering (solar) adjustments. 

Because electricity bills contain sensitive personal addresses, account numbers, and financial data, uploading them to third-party cloud APIs (like OpenAI or Anthropic) is a privacy risk.

**WattWise solves this by running 100% locally on your machine.** We use open-weight models (`qwen3.5:4b`) running on Ollama, ensuring your data never leaves your computer.

---

## Architecture & Open-Source AI

### 1. The Model Harness
Small language models (like 4B parameters) are incredibly fast and fit on consumer hardware, but they suffer from hallucinations and struggle with floating-point math. 
To solve this, we built an original, multi-turn conversational **ReAct Agent Harness**. Our harness intercepts hallucinations, maintains a persistent session history across turns, and acts as the strict orchestrator between the LLM and the real world.

### 2. Agent Skills
Instead of relying on prompt engineering, the agent dynamically loads custom **Skills** formatted to a standard `SKILL.md` structure. This enables complex, multi-step workflows such as:
- `bill-checker`: Validates physically impossible consumption rates and billing discrepancies.
- `complaint-letter`: Drafts automated formal dispute and refund notices to DISCOMs.
- `solar-roi-calculator`: Estimates rooftop solar capacity (kW), generation, and payback periods.
- `energy-saving-advisor`: Recommends appliance-level actions to reduce usage and drop to cheaper tariff slabs.
- `explain-bill`: Breaks down fixed charges, energy slabs, and duties in clear, plain language.

---

## 📊 Evaluations & Benchmarks

We rigorously benchmarked our Model Harness against an unassisted Base `qwen3.5:4b` model to prove the effectiveness of our architecture. 
Using our evaluation suite, the WattWise Harness completely eliminates arithmetic hallucinations and achieves very good accuracy on ground-truth tariff lookups.

For full benchmark methodology and interactive Colab setup, see the [Evaluation Suite Guide (`eval/README.md`)](eval/README.md).

### 📑 Evaluation Reports & Results
- [Benchmark Report (`eval/reports/benchmark_report.md`)](eval/reports/benchmark_report.md): Summary comparison table on multi-slab tariff math and arithmetic accuracy.
- [Evaluation Results (`eval/reports/eval_results.json`)](eval/reports/eval_results.json): Full per-case traces, tool invocations, predictions, and latencies.
- [Vision Benchmark Report (`eval/reports/vision_benchmark_report.md`)](eval/reports/vision_benchmark_report.md): State identification, DISCOM recognition, and factor extraction accuracy from bill photos.
- [Vision Evaluation Results (`eval/reports/vision_eval_results.json`)](eval/reports/vision_eval_results.json): Raw extraction outputs, JSON schema validation logs, and integrity checks.

---

## 📂 Project Structure

```text
wattwise-harness/
├── api/                  # FastAPI backend server and persistent session management
├── wattwise/             # The core Agentic Model Harness (Execution Loop & Ollama Client)
├── mcp_servers/          # External tools (Safe Calculator, Tariff DB, Vision OCR Engine)
├── skills/               # Reusable agent workflows (SKILL.md format)
├── eval/                 # Benchmarking and accuracy testing suite
├── frontend/             # Modern React + Vite web client (Dark mode, Trace Inspector)
├── data/                 # Static JSON databases (Electricity rates across Indian states)
├── cli.py                # Interactive command-line chat interface
└── qwen-16k.Modelfile    # Configuration to build the 16K context window local model
```

---

## 🛠️ Quick Start & Local Setup

### 1. Build the Custom 16K Context AI Model
Electricity bills contain massive amounts of OCR text. To prevent the local LLM from running out of memory, we must increase its context window to 16,000 tokens.
Make sure you have [Ollama](https://ollama.com/) installed, then run:
```bash
ollama pull qwen3.5:4b
ollama create qwen3.5:4b-16k -f qwen-16k.Modelfile
```

### 2. Setup the Python Backend
```bash
python -m venv .venv
source .venv/bin/activate  # Or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure your environment
cp .env.example .env
```

---

## Running WattWise

You have two options to run WattWise: The beautiful Web UI or the interactive Terminal CLI.

### Option A: The Web UI (Frontend + Backend)
You will need two terminal windows.

**Terminal 1 (Backend API):**
```bash
python -m uvicorn api.server:app --port 8000
```

**Terminal 2 (React Frontend):**
```bash
cd frontend
npm install
npm run dev
```
*Then open `http://localhost:5173` in your browser!*

### Option B: Interactive CLI
If you prefer the terminal, you can chat with the agent directly (and even pass images):
```bash
python cli.py
```
*(Type your questions or hit Enter when prompted for a bill photo path).*

---

## Team Members

Built with ❤️ by a team from **MNIT Jaipur**:
- **Udayan Amipara** (MNIT Jaipur - CSE)
- **Akash Wadhvani** (MNIT Jaipur - CSE)
- **Naman Sawnani** (MNIT Jaipur - ECE)

## License
This project is licensed under the MIT License.