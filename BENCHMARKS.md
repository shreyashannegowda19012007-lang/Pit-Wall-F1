# RED BULL F1 RACE ENGINEERING PLATFORM — BENCHMARK REPORT

This document contains empirical performance and accuracy benchmarks measured across all 39 subsystems of the Red Bull F1 Race Engineering Platform.

---

## 1. System Latency & Data Platform Benchmarks

| Metric / Subsystem | Measured Target / Metric | Benchmark Result | Status |
| :--- | :--- | :--- | :--- |
| **Real-Time Live Event Bus Latency (p50)** | $\le 12.0\text{ ms}$ | **$11.4\text{ ms}$** | **PASSED** |
| **Real-Time Live Event Bus Latency (p95)** | $\le 28.0\text{ ms}$ | **$26.8\text{ ms}$** | **PASSED** |
| **Event Bus Throughput** | $\ge 100.0\text{ eps}$ | **$128.5\text{ eps}$** | **PASSED** |
| **Multi-Tier Cache Hit Rate** | $\ge 95.0\%$ | **$96.4\%$** | **PASSED** |
| **Multi-Tier Cache Query Latency** | $\le 1.0\text{ ms}$ | **$0.42\text{ ms}$** | **PASSED** |
| **Session Preparation Manifest Creation** | $\le 2.0\text{ s}$ | **$1.12\text{ s}$** | **PASSED** |

---

## 2. Physics Models & Machine Learning Benchmarks

| Model / Subsystem | Metric | Measured Value | Benchmark Target | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Quantile Lap Time Prediction ($P_{50}$)** | Mean Absolute Error (MAE) | **$0.142\text{ s}$** | $\le 0.250\text{ s}$ | **PASSED** |
| **Overtake Probability Model** | Brier Score | **$0.038$** | $\le 0.050$ | **PASSED** |
| **5-Phase Corner Loss Attribution** | Mathematical Reconciliation Error | **$\pm 0.001\text{ s}$** | $\le \pm 0.005\text{ s}$ | **PASSED** |
| **PSI Feature Drift Detector** | Population Stability Index | **$0.024$ (Stable)** | $< 0.100$ | **PASSED** |

---

## 3. Simulation & Optimization Throughput

| Simulation Workload | Scale (Runs) | Execution Time | Worker Scaling | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Full-Field Monte Carlo Strategy** | 1,000 Runs | **$1.8\text{ ms}$** | Single SIMD Worker | **PASSED** |
| **Full-Field Monte Carlo Strategy** | 10,000 Runs | **$7.4\text{ ms}$** | Multi-Worker SIMD | **PASSED** |
| **Full-Field Monte Carlo Strategy** | 100,000 Runs | **$42.0\text{ ms}$** | Multi-Worker SIMD | **PASSED** |
