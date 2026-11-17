"""Reproducible Benchmarking Script measuring p50, p95, p99 API latency across concurrency levels."""

import asyncio
import time
import statistics
import uuid
import httpx

from agentops_api.main import app
from agentops_api.seed import DEMO_API_KEY_RAW


async def benchmark_workload(client: httpx.AsyncClient, concurrency: int, total_requests: int):
    """Run concurrent OTLP ingestion requests and measure latencies."""
    latencies = []
    sem = asyncio.Semaphore(concurrency)

    async def single_request():
        async with sem:
            trace_id = uuid.uuid4().hex
            payload = {
                "spans": [
                    {
                        "trace_id": trace_id,
                        "span_id": uuid.uuid4().hex[:16],
                        "name": "benchmark.span",
                        "start_time_unix_nano": int(time.time() * 1e9),
                        "end_time_unix_nano": int(time.time() * 1e9) + 50000000,
                        "attributes": {
                            "gen_ai.system": "benchmark",
                            "gen_ai.request.model": "bench-v1",
                            "gen_ai.usage.input_tokens": 100,
                            "gen_ai.usage.output_tokens": 50,
                            "gen_ai.operation.name": "chat"
                        }
                    }
                ]
            }
            t0 = time.time()
            res = await client.post(
                "/api/v1/telemetry/v1/traces",
                json=payload,
                headers={"X-AgentOps-Api-Key": DEMO_API_KEY_RAW}
            )
            elapsed_ms = (time.time() - t0) * 1000
            if res.status_code == 200:
                latencies.append(elapsed_ms)

    tasks = [single_request() for _ in range(total_requests)]
    t_start = time.time()
    await asyncio.gather(*tasks)
    total_duration = time.time() - t_start

    latencies.sort()
    n = len(latencies)
    p50 = statistics.median(latencies) if n else 0
    p95 = latencies[int(n * 0.95)] if n else 0
    p99 = latencies[int(n * 0.99)] if n else 0
    rps = round(n / total_duration, 1) if total_duration > 0 else 0

    return {
        "concurrency": concurrency,
        "completed": n,
        "duration_sec": round(total_duration, 2),
        "rps": rps,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2)
    }


async def main():
    print("==========================================================")
    print("  AgentOps Concurrency & Ingestion Performance Benchmark  ")
    print("==========================================================")
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", timeout=30.0) as client:
        workloads = [
            (1, 20),
            (10, 50),
            (25, 100),
            (50, 150),
            (100, 200)
        ]
        
        for conc, total in workloads:
            result = await benchmark_workload(client, conc, total)
            print(f"Concurrency: {result['concurrency']:3d} | Total: {result['completed']:3d} reqs | "
                  f"Throughput: {result['rps']:6.1f} req/s | "
                  f"p50: {result['p50_ms']:5.2f}ms | p95: {result['p95_ms']:5.2f}ms | p99: {result['p99_ms']:5.2f}ms")


if __name__ == "__main__":
    asyncio.run(main())
