# AgentOps Concurrency & Latency Benchmarks

Measured using the automated benchmark harness (`tests/benchmark_concurrency.py`).
*Environment: Windows 11, Python 3.13.7 (Asyncio & HTTPX ASGI Transport).*

## Empirical Results

| Concurrency Level | Total Requests | Throughput (req/s) | p50 Latency (ms) | p95 Latency (ms) | p99 Latency (ms) |
|---|---|---|---|---|---|
| **1 worker** | 20 | **63.1 req/s** | 14.10 ms | 52.79 ms | 52.79 ms |
| **10 workers** | 50 | **43.4 req/s** | 37.00 ms | 926.79 ms | 1,148.29 ms |
| **25 workers** | 100 | **45.9 req/s** | 173.03 ms | 1,634.21 ms | 2,171.31 ms |
| **50 workers** | 150 | **42.6 req/s** | 600.16 ms | 2,664.68 ms | 3,388.16 ms |
| **100 workers**| 200 | **42.0 req/s** | 1,245.01 ms | 3,730.13 ms | 4,374.04 ms |

## Benchmark Analysis & Key Insights
1. **Low-Concurrency Efficiency**: At baseline concurrency, telemetry ingestion achieves median latency of **14.10 ms** with throughput over **63 req/s**.
2. **High-Concurrency Resilience**: Under high burst loads (100 concurrent workers sending 200 batched spans), the FastAPI asynchronous event loop maintains steady throughput of **~42 req/s** without connection dropping or unhandled exceptions.
3. **Synthetic vs Live Labeling**: All synthetic demonstration traces and test data are explicitly tagged with `is_synthetic = True`, ensuring zero conflation with live customer telemetry.
