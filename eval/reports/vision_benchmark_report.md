# 👁️ Vision Benchmark Report: State & Factor Extraction

**Model Evaluated:** `qwen3.5:4b`  
**Total Bill Photos:** 6  
**Date:** 2026-10-10 10:20:19

---

## 🏆 Key Metric Summary

| Metric | Base `qwen3.5:4b` Vision (Unassisted) | WattWise Vision Pipeline (Harness) | Gain |
| :--- | :---: | :---: | :---: |
| **State Identification Accuracy** | **66.7%** (4/6) | **100.0%** (6/6) | **+33.3%** |
| **DISCOM Recognition Accuracy** | **66.7%** (4/6) | **100.0%** (6/6) | **+33.3%** |
| **Structured JSON Schema** | ❌ Unstructured text | ✅ Strict `BillData` JSON schema | Machine readable |
| **Integrity & Sanity Checks** | ❌ None | ✅ Checked `Current - Prev = Units` | Flags anomalies |

---

## 📋 Bill-by-Bill State & Factor Extraction Results

| Bill | Ground Truth State | Base Model Detected State | Harness Detected State | Base Match | Harness Match | Units Extracted | Amount Due (Rs) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| `bill_1.jpg` | **Rajasthan** | Rajasthan | **Rajasthan** | ✅ | ✅ | 11223059.0 | Rs 95395671.0 |
| `bill_2.webp` | **Maharashtra** | Maharashtra | **Maharashtra** | ✅ | ✅ | N/A | Rs 600.0 |
| `bill_3.jpg` | **Maharashtra** | Not Identified | **Maharashtra** | ❌ | ✅ | N/A | Rs 790706190.0 |
| `bill_4.png` | **Gujarat** | Gujarat | **Gujarat** | ✅ | ✅ | 150.0 | Rs 655.25 |
| `bill_5.webp` | **Delhi** | Not Identified | **Delhi** | ❌ | ✅ | N/A | Rs 230.0 |
| `bill_6.webp` | **Karnataka** | Karnataka | **Karnataka** | ✅ | ✅ | N/A | Rs 302.0 |
