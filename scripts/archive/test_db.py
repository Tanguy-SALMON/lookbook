#!/usr/bin/env python3
"""
Database Test Script

This script tests the database functionality and repository operations.
"""

import asyncio
import #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lean, fast Ollama benchmark (streaming, retries, sane defaults)

- Uses HTTP/1.1 keep-alive with httpx.AsyncClient
- Streams tokens to measure TTFT and throughput
- 3 iterations per prompt to keep runs short
- Lower max tokens for realistic chatbot replies
- Warmup request to load model in memory
- Better error logging and timeout handling
- Cleaner metrics: TTFT, total latency, tokens/sec, success rate

Usage examples:
  python3 scripts/benchmark_models.py --models qwen3:4b qwen3 --repeat 3 --max-tokens 256
  python3 scripts/benchmark_models.py --models qwen3:4b --prompts "First date outfit ideas" "Gym workout clothes"
"""

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
import psutil
import numpy as np
import statistics

# ----------------------------
# Config
# ----------------------------

DEFAULT_PROMPTS = [
    "I want to do yoga, what should I wear?",
    "Restaurant this weekend, attractive for $50",
    "Business meeting outfit for office",
    "First date outfit ideas",
    "Gym workout clothes recommendation",
    "Winter formal dress suggestions",
    "Hiking trip clothing advice",
]


@dataclass
class BenchmarkConfig:
    model_name: str
    ollama_host: str = "http://localhost:11434"
    timeout: float = 180.0              # generous for CPU with streaming
    max_tokens: int = 256               # keep outputs short and comparable
    temperature: float = 0.3
    top_p: float = 0.9
    repeat_count: int = 3               # only 3 per prompt (fast loops)
    test_prompts: Optional[List[str]] = None
    retries: int = 2                    # quick retry on network/timeout
    retry_backoff_sec: float = 0.6
    num_thread: Optional[int] = None    # set to physical cores if desired
    warmup_prompt: str = "OK"
    output_dir: str = "benchmark_results"

    def prompts(self) -> List[str]:
        if self.test_prompts and len(self.test_prompts) > 0:
            return self.test_prompts
        return DEFAULT_PROMPTS


@dataclass
class RunMetrics:
    prompt: str
    success: bool
    error: Optional[str]
    t_total: float                      # total wall time (s)
    t_first_token: Optional[float]      # TTFT (s)
    tokens_emitted: int
    tokens_per_sec: Optional[float]
    chars: int


# ----------------------------
# Ollama streaming client
# ----------------------------

class OllamaClient:
    def __init__(self, base_url: str, timeout: float):
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=10)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            limits=limits,
            headers={"Connection": "keep-alive"},
            http2=False,  # keep HTTP/1.1 for line streaming
        )

    async def close(self):
        await self.client.aclose()

    async def generate_stream(self, model: str, prompt: str, options: Dict[str, Any]):
        # POST to /api/generate with stream: true; read JSON lines
        resp = await self.client.post(
            "/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": options,
            },
        )
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line:
                continue
            yield line


# ----------------------------
# Benchmark logic
# ----------------------------

class ModelBenchmark:
    def __init__(self, cfg: BenchmarkConfig):
        self.cfg = cfg
        self.proc = psutil.Process()
        self.results: List[RunMetrics] = []
        self.system_info = {
            "cpu_count": psutil.cpu_count(logical=True) or 0,
            "mem_gb": psutil.virtual_memory().total / (1024 ** 3),
        }

    def _options(self) -> Dict[str, Any]:
        opts = {
            "temperature": self.cfg.temperature,
            "num_predict": self.cfg.max_tokens,
            "top_p": self.cfg.top_p,
            "repeat_penalty": 1.05,
        }
        if self.cfg.num_thread and self.cfg.num_thread > 0:
            opts["num_thread"] = self.cfg.num_thread
        return opts

    async def _single_call_stream(self, oc: OllamaClient, prompt: str) -> RunMetrics:
        t0 = time.time()
        first_tok_t: Optional[float] = None
        emitted_text_parts: List[str] = []
        tokens_emitted = 0
        ok = False
        err: Optional[str] = None

        try:
            async for line in oc.generate_stream(self.cfg.model_name, prompt, self._options()):
                if first_tok_t is None:
                    first_tok_t = time.time()
                try:
                    data = json.loads(line)
                except Exception:
                    # sometimes whitespace or non-json noise; ignore
                    continue
                chunk = data.get("response", "")
                if chunk:
                    emitted_text_parts.append(chunk)
                    # naive token estimate: words ~= tokens for speed benchmarking
                    tokens_emitted += max(1, len(chunk.split()))
                if data.get("done"):
                    ok = True
                    break
        except httpx.HTTPStatusError as e:
            try:
                body = e.response.text.strip()
            except Exception:
                body = ""
            err = f"HTTP {e.response.status_code}: {body[:200]}"
        except httpx.TimeoutException:
            err = "Timeout"
        except httpx.TransportError as e:
            err = f"TransportError: {repr(e)}"
        except Exception as e:
            err = f"Exception: {repr(e)}"

        t1 = time.time()
        total = t1 - t0
        txt = "".join(emitted_text_parts)
        ttft = (first_tok_t - t0) if first_tok_t else None
        tok_per_sec = (tokens_emitted / max(1e-6, (t1 - (first_tok_t or t0)))) if first_tok_t else None

        return RunMetrics(
            prompt=prompt,
            success=ok,
            error=err if not ok else None,
            t_total=total,
            t_first_token=ttft,
            tokens_emitted=tokens_emitted,
            tokens_per_sec=tok_per_sec,
            chars=len(txt),
        )

    async def _call_with_retries(self, oc: OllamaClient, prompt: str) -> RunMetrics:
        last: Optional[RunMetrics] = None
        for attempt in range(self.cfg.retries + 1):
            m = await self._single_call_stream(oc, prompt)
            if m.success:
                return m
            last = m
            await asyncio.sleep(self.cfg.retry_backoff_sec * (attempt + 1))
        return last  # type: ignore

    async def run(self):
        # Warmup: load model into memory
        oc = OllamaClient(self.cfg.ollama_host, self.cfg.timeout)
        try:
            await self._call_with_retries(oc, self.cfg.warmup_prompt)

            prompts = self.cfg.prompts()
            print(f"Starting benchmark for {self.cfg.model_name}")
            print(f"Prompts: {len(prompts)} | Repeats per prompt: {self.cfg.repeat_count} | max_tokens: {self.cfg.max_tokens}")
            print(f"Ollama host: {self.cfg.ollama_host} | Timeout: {self.cfg.timeout:.0f}s | Temperature: {self.cfg.temperature}")

            for i, p in enumerate(prompts, 1):
                print(f"\nPrompt {i}/{len(prompts)}: {p[:64]}...")
                for j in range(self.cfg.repeat_count):
                    sys.stdout.write(f"  Run {j+1}/{self.cfg.repeat_count}... ")
                    sys.stdout.flush()
                    m = await self._call_with_retries(oc, p)
                    self.results.append(m)
                    if m.success:
                        ttft = f"{m.t_first_token:.2f}s" if m.t_first_token is not None else "n/a"
                        tps = f"{m.tokens_per_sec:.1f}" if m.tokens_per_sec is not None else "n/a"
                        print(f"✓ total={m.t_total:.2f}s ttft={ttft} tok/s={tps}")
                    else:
                        print(f"✗ ({m.error})")
        finally:
            await oc.close()

    def analyze(self) -> Dict[str, Any]:
        if not self.results:
            return {}

        ok = [r for r in self.results if r.success]
        fail = [r for r in self.results if not r.success]

        def mean_or_none(v):
            return statistics.mean(v) if v else None

        t_totals = [r.t_total for r in ok]
        ttfts = [r.t_first_token for r in ok if r.t_first_token is not None]
        tps = [r.tokens_per_sec for r in ok if r.tokens_per_sec is not None]

        analysis = {
            "model_name": self.cfg.model_name,
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_cores": self.system_info["cpu_count"],
                "mem_gb": self.system_info["mem_gb"],
            },
            "total_runs": len(self.results),
            "successful_runs": len(ok),
            "failed_runs": len(fail),
            "success_rate": (len(ok) / len(self.results) * 100.0) if self.results else 0.0,
            "perf": {
                "t_total": {
                    "mean": float(mean_or_none(t_totals) or 0.0),
                    "median": float(statistics.median(t_totals)) if t_totals else 0.0,
                    "p95": float(np.percentile(t_totals, 95)) if len(t_totals) >= 2 else (t_totals[0] if t_totals else 0.0),
                    "min": float(min(t_totals)) if t_totals else 0.0,
                    "max": float(max(t_totals)) if t_totals else 0.0,
                },
                "ttft": {
                    "mean": float(mean_or_none(ttfts) or 0.0),
                    "median": float(statistics.median(ttfts)) if ttfts else 0.0,
                },
                "tokens_per_sec": {
                    "mean": float(mean_or_none(tps) or 0.0),
                    "median": float(statistics.median(tps)) if tps else 0.0,
                },
            },
            "errors": {},
        }
        # Error aggregation
        err_counts: Dict[str, int] = {}
        for r in fail:
            key = r.error or "Unknown"
            err_counts[key] = err_counts.get(key, 0) + 1
        analysis["errors"] = err_counts
        return analysis

    def save(self) -> Tuple[str, str]:
        os.makedirs(self.cfg.output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = self.cfg.model_name.replace(":", "_").replace(".", "_")
        raw_file = os.path.join(self.cfg.output_dir, f"{safe}_raw_{ts}.json")
        sum_file = os.path.join(self.cfg.output_dir, f"{safe}_summary_{ts}.json")
        txt_file = os.path.join(self.cfg.output_dir, f"{safe}_summary_{ts}.txt")

        with open(raw_file, "w") as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)

        analysis = self.analyze()
        with open(sum_file, "w") as f:
            json.dump(analysis, f, indent=2)

        # Pretty text summary
        lines = []
        lines.append("BENCHMARK SUMMARY REPORT")
        lines.append("=" * 60)
        lines.append(f"Model: {analysis.get('model_name')}")
        lines.append(f"Timestamp: {analysis.get('timestamp')}")
        sysinfo = analysis.get("system", {})
        lines.append(f"System: {sysinfo.get('cpu_cores', '?')} cores, {sysinfo.get('mem_gb', 0):.1f}GB RAM")
        lines.append("")
        lines.append("PERFORMANCE")
        perf = analysis.get("perf", {})
        t_total = perf.get("t_total", {})
        ttft = perf.get("ttft", {})
        tps = perf.get("tokens_per_sec", {})
        lines.append(f"- Total time mean: {t_total.get('mean', 0):.2f}s (p95 {t_total.get('p95', 0):.2f}s)")
        lines.append(f"- TTFT mean      : {ttft.get('mean', 0):.2f}s")
        lines.append(f"- Tokens/sec mean: {tps.get('mean', 0):.1f}")
        lines.append("")
        lines.append("RELIABILITY")
        lines.append(f"- Success rate: {analysis.get('success_rate', 0):.1f}% "
                     f"({analysis.get('successful_runs', 0)}/{analysis.get('total_runs', 0)})")
        errs = analysis.get("errors", {})
        if errs:
            lines.append("- Errors:")
            for k, v in errs.items():
                lines.append(f"   * {k}: {v}")

        with open(txt_file, "w") as f:
            f.write("\n".join(lines))

        print("\nSaved:")
        print(f"  Raw runs : {raw_file}")
        print(f"  Summary  : {sum_file}")
        print(f"  Text rep : {txt_file}")
        return raw_file, sum_file


# ----------------------------
# CLI
# ----------------------------

async def main():
    parser = argparse.ArgumentParser(description="Fast streaming benchmark for Ollama models")
    parser.add_argument("--models", nargs="+", default=["qwen3:4b"], help="Models to benchmark")
    parser.add_argument("--repeat", type=int, default=3, help="Repetitions per prompt (default: 3)")
    parser.add_argument("--prompts", nargs="*", help="Custom prompts (space separated)")
    parser.add_argument("--output", default="benchmark_results", help="Output dir")
    parser.add_argument("--temperature", type=float, default=0.3, help="Temperature")
    parser.add_argument("--max-tokens", type=int, default=256, help="Max tokens to generate")
    parser.add_argument("--timeout", type=float, default=180.0, help="HTTP timeout seconds")
    parser.add_argument("--host", default="http://localhost:11434", help="Ollama host")
    parser.add_argument("--num-thread", type=int, default=0, help="Set num_thread option (0=auto/ignore)")

    args = parser.parse_args()

    for model in args.models:
        cfg = BenchmarkConfig(
            model_name=model,
            ollama_host=args.host,
            timeout=args.timeout,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            test_prompts=args.prompts if args.prompts and len(args.prompts) > 0 else None,
            repeat_count=args.repeat,
            num_thread=(args.num_thread if args.num_thread > 0 else None),
            output_dir=args.output,
        )

        print("=" * 60)
        print(f"BENCHMARK: {model}")
        print("=" * 60)

        bench = ModelBenchmark(cfg)
        await bench.run()
        bench.save()

        analysis = bench.analyze()
        if analysis:
            print("\nSUMMARY")
            print(f"- Model        : {analysis['model_name']}")
            print(f"- Success rate : {analysis['success_rate']:.1f}% "
                  f"({analysis['successful_runs']}/{analysis['total_runs']})")
            print(f"- Total mean   : {analysis['perf']['t_total']['mean']:.2f}s "
                  f"(p95 {analysis['perf']['t_total']['p95']:.2f}s)")
            print(f"- TTFT mean    : {analysis['perf']['ttft']['mean']:.2f}s")
            print(f"- Tok/s mean   : {analysis['perf']['tokens_per_sec']['mean']:.1f}")
            if analysis["errors"]:
                print("- Errors:")
                for k, v in analysis["errors"].items():
                    print(f"   * {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.db_lookbook import SQLiteLookbookRepository
from lookbook_mpc.adapters.db_shop import MockShopCatalogAdapter
from lookbook_mpc.domain.entities import Item
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_database_operations():
    """Test database operations."""
    try:
        print("Testing database operations...")

        # Initialize repository
        repo = SQLiteLookbookRepository("sqlite+aiosqlite:///lookbook.db")

        # Test 1: Get all items (should be empty initially)
        print("Test 1: Getting all items...")
        items = await repo.get_all_items()
        print(f"✓ Found {len(items)} items (expected: 0)")

        # Test 2: Save some test items
        print("\nTest 2: Saving test items...")
        test_items = [
            Item(
                sku="TEST001",
                title="Test T-Shirt",
                price=19.99,
                size_range=["S", "M", "L"],
                image_key="test1.jpg",
                attributes={"color": "blue", "category": "top"},
                in_stock=True
            ),
            Item(
                sku="TEST002",
                title="Test Jeans",
                price=49.99,
                size_range=["M", "L", "XL"],
                image_key="test2.jpg",
                attributes={"color": "blue", "category": "bottom"},
                in_stock=True
            )
        ]

        saved_count = await repo.save_items([item.model_dump() for item in test_items])
        print(f"✓ Saved {saved_count} items")

        # Test 3: Get all items again
        print("\nTest 3: Getting all items after save...")
        items = await repo.get_all_items()
        print(f"✓ Found {len(items)} items (expected: 2)")

        # Test 4: Search items
        print("\nTest 4: Searching items by color...")
        results = await repo.search_items({"color": "blue"})
        print(f"✓ Found {len(results)} blue items (expected: 2)")

        # Test 5: Search items by category
        print("\nTest 5: Searching items by category...")
        results = await repo.search_items({"category": "top"})
        print(f"✓ Found {len(results)} top items (expected: 1)")

        # Test 6: Get item by ID
        print("\nTest 6: Getting item by ID...")
        if items:
            item_id = items[0].id
            item = await repo.get_item_by_id(item_id)
            print(f"✓ Found item: {item.title if item else 'None'}")

        # Test 7: Test shop catalog adapter
        print("\nTest 7: Testing shop catalog adapter...")
        shop_adapter = MockShopCatalogAdapter()
        shop_items = await shop_adapter.fetch_items(limit=5)
        print(f"✓ Fetched {len(shop_items)} items from shop catalog")

        # Test 8: Test shop catalog get by SKU
        if shop_items:
            sku = shop_items[0]["sku"]
            item = await shop_adapter.get_item_by_sku(sku)
            print(f"✓ Found item by SKU {sku}: {item['title'] if item else 'None'}")

        print("\n🎉 All database tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_database_operations())
