# 📊 Benchmark Report: WattWise Harness vs. Base `qwen3.5:4b`

**Total Test Cases:** 12  
**Date:** 2026-10-10 09:22:57

---

## 🏆 Summary Comparison

| Metric | Base `qwen3.5:4b` (Unassisted) | WattWise Harness (Agent + MCP) | Improvement |
| :--- | :---: | :---: | :---: |
| **Accuracy Score** | **8.3%** (1/12) | **75.0%** (9/12) | **+66.7%** |
| **Average Latency** | 81.27s | 8.77s | Multi-step tool calls |
| **Tariff Knowledge** | Frequent Hallucinations | 100% Ground Truth Verified | Exact database lookup |
| **Arithmetic Precision** | Approximate / Prone to errors | Exact (`calculator.py` MCP) | Deterministic math |

---

## 📋 Detailed Case-by-Case Breakdown

| Case ID | Category | Ground Truth | Base Model Prediction | Harness Prediction | Base | Harness |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| `tariff_mh_150` | tariff_math | Rs 1494.16 | No match | Rs 1494.16 | ❌ | ✅ |
| `tariff_mh_80` | tariff_math | Rs 645.97 | No match | Rs 645.97 | ❌ | ✅ |
| `tariff_mh_350` | tariff_math | Rs 4616.88 | No match | Rs 4616.88 | ❌ | ✅ |
| `tariff_gj_180` | tariff_math | Rs 758.43 | No match | Rs 758.42 | ❌ | ✅ |
| `tariff_gj_40` | tariff_math | Rs 140.30 | Rs 50.00 | Rs 140.30 | ❌ | ✅ |
| `tariff_rj_250` | tariff_math | Rs 1622.50 | No match | Rs 1622.50 | ❌ | ✅ |
| `tariff_rj_90` | tariff_math | Rs 497.50 | No match | Rs 497.50 | ❌ | ✅ |
| `tariff_delhi_250` | tariff_math | Rs 866.25 | No match | Rs 866.25 | ❌ | ✅ |
| `tariff_delhi_500` | tariff_math | Rs 2257.50 | No match | Rs 708.00 | ❌ | ❌ |
| `tariff_ka_200` | tariff_math | Rs 1264.40 | No match | Rs 1264.40 | ❌ | ✅ |
| `tariff_unsupported_state` | boundary_check | Unsupported Notice | Hallucinated figures | Failed Notice | ❌ | ❌ |
| `solar_roi_300` | solar_roi | 2.0-3.0 kW | 3.0 kW | Failed | ✅ | ❌ |
