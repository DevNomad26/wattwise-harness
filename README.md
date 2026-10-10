# WattWise Harness ⚡

WattWise is an agentic electricity bill auditor and energy advisor powered by local LLMs (via Ollama) and Model Context Protocol (MCP) servers. It verifies meter readings against state tariff slabs, identifies overcharges and billing anomalies, drafts consumer complaints, and calculates solar rooftop ROI.

---

## 🏗️ Architecture

- **Frontend (`frontend/`)**: Modern React + Vite web client with dark/light mode, chat history stored in `localStorage`, quick-action chips, markdown rendering, and collapsible sidebar.
- **Backend API (`api/`)**: FastAPI server providing `/api/health`, `/api/chat`, and `/api/sessions/{session_id}` with multipart bill upload support.
- **Agent Loop (`wattwise/`)**: ReAct agent execution loop with reasoning failsafe interception and dynamic skill loader.
- **MCP Servers (`mcp_servers/`)**:
  - `vision.py`: Preprocessing & OCR bill data extraction.
  - `tariff.py`: Domestic tariff slab engine.
  - `calculator.py`: Safe arithmetic evaluator.
- **Skills (`skills/`)**: Internal skills for bill checking, complaints, solar ROI, and tariff explanation.
- **Eval Harness (`eval/`)**: Benchmark suite comparing Base `qwen3.5:4b` vs. WattWise Agent.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com/) running locally:
  ```bash
  ollama run qwen3.5:4b
  ```

### 2. Backend Setup
Create your virtual environment and install dependencies:
```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

Start the FastAPI backend:
```bash
uvicorn api.server:app --port 8000 --reload
```

### 3. Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📊 Running Evaluations (Local or Google Colab)

For detailed information on the benchmark methodologies, see [`eval/README.md`](file:///c:/Users/sawna/OneDrive/Documents/Development/My_Projects/wattwise-harness/eval/README.md).

### Local Evaluation
```bash
# 1. Run Tariff & Math Reasoning Benchmark
python eval/run_eval.py

# 2. Run Bill Photo Vision Benchmark
python eval/run_vision_eval.py
```

### Accelerated GPU Evaluation on Google Colab
1. Upload or open [`eval/eval_colab.ipynb`](file:///c:/Users/sawna/OneDrive/Documents/Development/My_Projects/wattwise-harness/eval/eval_colab.ipynb) in [Google Colab](https://colab.research.google.com/).
2. Select **Runtime > Change runtime type > T4 GPU**.
3. Run all cells to benchmark Base `qwen3.5:4b` vs. WattWise ReAct Harness and export the benchmark markdown reports.


---

## 💻 CLI Usage

You can also run WattWise directly from the terminal:
```bash
# Interactive mode
python cli.py

# Single question
python cli.py "What is the domestic electricity bill for 250 units in Rajasthan?"

# Bill photo check
python cli.py "Is my bill correct?" --image "path/to/bill.jpg"
```

---

## 🧪 Testing

Run backend test suite:
```bash
pytest
```