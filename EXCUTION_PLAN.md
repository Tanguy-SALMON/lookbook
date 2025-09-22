Execute top-to-bottom.

Junior (quick, high-impact)

    Cap output length and temperature globally
        Set max tokens small for speed:
            In all Python calls to Ollama: num_predict = 192–256
            Temperature = 0.2–0.3 for deterministic decoding
        Bad: num_predict=1000. Good: num_predict=256.
    Switch to streaming and reuse client
        Replace any non-streamed calls with streamed JSON-lines (httpx AsyncClient, keep-alive).
        Reuse one AsyncClient across calls (do not create per request).
    Increase timeouts a bit
        read timeout 180s; connect 5s; write 180s (only matters for long responses).
        This avoids flaky “✗ ()” empty errors due to tight timeouts.
    Reduce iterations in benchmarks and warm up model
        repeat_count = 3 per prompt.
        Make first call a warmup (short prompt, e.g., “OK”) to load the model into memory.
    Use smaller models consistently
        Verify tag equals what CLI uses:
            ollama list
            Ensure you’re benchmarking the same variant (e.g., qwen3:4b-q4_K_M vs qwen3:4b default).
        Bad: unknowingly using an int8/unfused variant. Good: consistent quant with CLI.
    Ensure local host and no proxy
        Python must hit http://localhost:11434
        export NO_PROXY=localhost,127.0.0.1 (avoid corporate proxy slowdown).
    Pin the new benchmark file
        Replace scripts/benchmark_models.py with the streamlined version I gave you.
        Run: poetry run python scripts/benchmark_models.py --models qwen3:4b --repeat 3 --max-tokens 256

Pro (system + code tuning)
8. Set num_thread explicitly

    Physical cores only (not logical/HT). Example for 8-core CPU:
        options["num_thread"] = 8
    Test 6–8 to find sweet spot. Too high can slow due to contention.

    Keep ctx modest
        If you set num_ctx elsewhere, keep to 2048 for small models unless needed. Big contexts slow decoding.
    Warm cache and keep model loaded

    Don’t unload between runs. Avoid restarting Ollama frequently.
    First call after machine boot is slow; ignore its timing.

    Fix CPU measurement noise

    If you log CPU, sample with interval: psutil.cpu_percent(interval=0.2)
    Prime with proc.cpu_percent(None) before sampling.

    Add retry/backoff and log errors

    Retry 2x with 0.6s, 1.2s backoff on Timeout/TransportError.
    Log HTTP status and first 200 chars of body on non-200 responses.

    Make tests representative and short

    Replace long verbose prompts with concise ones.
    Keep a balanced set: 5–7 prompts max to reduce CPU heat/thermal throttling in loops.

    Compare apples-to-apples to CLI

    CLI test:
        ollama run qwen3:4b -p "First date outfit ideas" --num-predict 256
    Your Python should match speed after streaming + options + warmed model.

    Disk and memory checks

    Ensure models directory is on fast SSD (default ~/.ollama/models).
    Free RAM: close other heavy apps during benchmark.

Advanced (optional but powerful)
16. CPU governor and thermals (Ubuntu)

    sudo apt-get install linux-tools-common linux-tools-generic
    sudo cpupower frequency-set -g performance
    Ensure adequate cooling; watch frequency in htop. Throttling = sudden slowdowns at later runs.

    Quantization choice

    Use q4_K_M or similar fast quant for small CPUs (often faster than higher-bit quant for real throughput).
    If you accidentally pulled a bf16/fp16, it will crawl on CPU.

    Model selection sanity

    Try distilled/smaller models tailored for speed:
        qwen2.5:1.5b-instruct-q4_K_M
        phi-3.5-mini-instruct
        llama3.2:1b or 3b instruct quantized
    Benchmark and pick the best speed/quality compromise for your UX.

    Separate TTFT vs throughput KPIs in reports

    TTFT (time-to-first-token) highlights latency; tokens/sec shows steady-state decoder speed. Report both.

    Production service considerations

    Keep Ollama as a long-lived service.
    If you multiplex requests, limit concurrency to N=cores/2 on CPU to avoid contention.
    For web handlers, push streamed responses to clients to improve perceived speed.

    Optional: Pre-tokenize system prompts

    Keep system/instructions minimal. Long system prompts hurt TTFT; reuse short templates.

Concrete tasks for your repo (execute in this order)

    Replace benchmark file
        Overwrite scripts/benchmark_models.py with the streaming version I sent.
        Set defaults:
            repeat=3, max_tokens=256, temperature=0.3, retries=2, timeout=180.
            Pass --num-thread <physical_cores> for your box.
    Add a shared Ollama client utility (for all Python callers)
        Create a small Python module e.g., lookbook_mpc/services/ollama_client.py with:
            Async httpx client (keep-alive)
            generate_stream(model, prompt, options)
            sensible defaults: num_predict=256, temperature=0.3, top_p=0.9, repeat_penalty=1.05, optional num_thread
            expose a helper run_infer(prompt, max_tokens=256) that returns TTFT, text, t_total
        Replace scattered direct http calls to Ollama in your project to use this shared client.
    Normalize all callers to streaming
        scripts/chat_demo.py, start_chat_server.py, test_chat_* scripts:
            Switch to streaming and begin forwarding chunks to stdout/websocket immediately.
            Keep the same temperature/max_tokens defaults for consistency.
    Add a warmup step on service start
        In start_chat_server.py (or main.py depending on entrypoint):
            On startup, call run_infer("OK") once per active model tag you use.
            Log TTFT for warmup separately; ignore for metrics.
    Update test-benchmark runner
        Simplify scripts/run_benchmark.py to call the new benchmark with:
            poetry run python scripts/benchmark_models.py --models qwen3:4b --repeat 3 --max-tokens 256 --num-thread
        Store artifacts under benchmark_results/* and prune old runs.
    Confirm model tags
        Run: ollama list
        Decide the exact model/tag to standardize (e.g., qwen3:4b-q4_K_M if available).
        Update any hardcoded model names in code and docs.
    Environment tweaks on the host
        export NO_PROXY=localhost,127.0.0.1
        Disable any HTTP proxies in the shell where services run.
        Optional performance governor:
            sudo cpupower frequency-set -g performance
    Quick validation loop
        CLI single prompt (apples-to-apples):
            time ollama run qwen3:4b -p "First date outfit ideas" --num-predict 256
        Python single prompt:
            poetry run python scripts/benchmark_models.py --models qwen3:4b --repeat 1 --prompts "First date outfit ideas" --max-tokens 256
        Compare TTFT and total time. They should be close after streaming changes.
    Trim prompts set for speed tests
        Keep 5–7 short, representative prompts. Remove verbose or redundant ones.
        Target outputs ~120–220 tokens.
    Instrument minimal system stats (optional)

    Log psutil.cpu_percent(interval=0.2) and psutil.virtual_memory().available before/after the first and last run only (not per run) to avoid overhead and noise.

    Roll out to all chat entrypoints

    Make sure chat endpoints in scripts/test_api.py, scripts/test_chat_* use the shared client and streaming.
    For web/UI outputs (docs/demo.html), stream chunks to the browser if possible; otherwise chunk buffer flush.

    Document new defaults

    Update QUICK_START.md and README.md:
        Default num_predict=256, temperature=0.3, streaming enabled.
        How to override per environment variable or CLI flag.
        Known slowdowns: long system prompts, big contexts, high temperature.

    Optional: Try smaller models for UX speed

    Benchmark:
        qwen2.5:1.5b-instruct-q4_K_M
        phi-3.5-mini-instruct
        llama3.2:3b-instruct-q4_K_M
    If quality is acceptable for your COS use case, standardize on the fastest model.

    Gate long generations

    Implement a server-side guardrail: if a prompt is long or user asks for big lists, cap max_tokens to 192 for that response.
    Add a “More details” follow-up mode to request longer output only on demand.
