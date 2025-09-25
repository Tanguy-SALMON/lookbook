Proposed stack for “lookbook-MPC”

    Core: FastAPI + Pydantic + SQLAlchemy + Alembic.
    LLMs via Ollama: qwen2.5-vl:7b for vision, qwen3 for intent parsing, rules text, rationales.
    MCP compatibility: expose an MCP server alongside the API so LLM clients can call tools/resources per Model Context Protocol Anthropic MCP.

High-level architecture

    Services
        lookbook-mpc-api (FastAPI): REST and optional WebSocket chat; also hosts the MCP server adapter.
        lookbook-mpc-vision (sidecar): wraps your VisionAnalyzer/Ollama; HTTP or gRPC endpoint; can scale separately.
    Adapters
        ShopCatalogAdapter (read-only MySQL to Magento).
        LookbookRepo (SQLite by default; switchable via DB URL).
        IntentParser (Ollama qwen3 with few-shot rules).
        ImageLocator (builds S3 URLs: S3_BASE_URL + file_name; optional proxy endpoint for CORS).
    Domain
        Entities: Item, Attributes, Outfit, Lookbook, Rule, Intent.
        Use-cases: IngestItems, RecommendOutfits, BuildLookbook, ChatTurn.

S3/Magento images

    Query Magento for sku + gc_swatchimage; store only the image key (e.g., e341e…jpg).
    Derive URL on demand: image_url = S3_BASE_URL + "/" + image_key.
    Optionally proxy as GET /images/{key} that 302-redirects or streams for CORS control.

Functional requirements

    Ingestion
        Pull in-stock items from Magento query you provided; build image URLs; send to Vision sidecar (qwen2.5-vl:7b) for attributes: category, color, material, pattern, season, occasion, fit/plus-size.
        Persist shadow item records and tags in Lookbook DB.
    Intent understanding
        Map free text to constraints:
            “I want to do yoga” → activity=yoga, category=athleisure, comfort=high, stretch materials.
            “Restaurant this weekend, attractive for $50” → occasion=dinner, budget<=50, elevated casual, weekend=next.
            “I am fat, look slim” → slimming rules (dark/monochrome, vertical lines, structured layers, mid/high rise).
    Rules engine & recommendation
        Compose 3–7 outfits meeting constraints (category/price/size/availability/color/silhouette).
        Provide rationale text (qwen3) and confidence.
    APIs
        POST /v1/ingest/items {limit?, since?} → 202
        POST /v1/recommendations {text_query, budget?, size?, week?, preferences?} → {outfits, rationale, constraints_used}
        GET /v1/lookbooks/{id}, POST /v1/lookbooks, POST /v1/chat {session_id?, message}
        GET /v1/images/{key} → 302 to S3 or stream
    MCP tools (served by the same process)
        tool.recommend_outfits(query, budget?, size?) → outfits
        tool.search_items(filters) → items
        tool.ingest_batch(limit?) → status
        resources: lookbook schema, OpenAPI doc, rules catalog.

Non-functional requirements (demo-focused)

    Architecture: Clean Architecture (ports/adapters); domain isolated from frameworks; swappable adapters (DB, LLM, vision).
    Config: all via env (MYSQL_SHOP_URL, LOOKBOOK_DB_URL, OLLAMA_HOST, OLLAMA_VISION_MODEL, OLLAMA_TEXT_MODEL, S3_BASE_URL).
    Security: no hardcoded creds; protect admin endpoints; sanitize LLM inputs; prompt-injection hygiene.
    Reliability: timeouts/retries for Ollama; graceful degradation (rule-only if LLM down); idempotent ingestion.
    Testability: unit tests (intent parsing, rules, outfit builder), integration tests with SQLite and stubbed vision/LLM.
    Observability: structured logs, request IDs, basic health (/health, /ready); log LLM latency and model names.
    Portability: default Lookbook DB = SQLite; interchangeable with MySQL/Postgres via URL.
    MCP readiness: tools/resources versioned; schemas stable; align with MCP Python server library.

Naming & layout (CNS)

    Repo: lookbook-mpc
    Package: lookbook_mpc
    Structure:
        lookbook_mpc/domain/{entities.py, use_cases.py}
        lookbook_mpc/adapters/{db_shop.py, db_lookbook.py, vision.py, intent.py, images.py}
        lookbook_mpc/services/{rules.py, recommender.py}
        lookbook_mpc/api/{routers/*.py, mcp_server.py}
        migrations/, tests/, scripts/
    Env: .env.example documenting required vars.

Process & deployment notes

    Run vision sidecar next to API (docker-compose): both point to the same Ollama daemon; pin models: qwen2.5-vl:7b, qwen3.
    For demo, use FastAPI BackgroundTasks for ingestion; for scale, use a queue (Redis/RQ or Celery).
    Your vision_analyzer.py: add import re, fix indentation, make model/config/env-driven, and expose a simple POST /analyze endpoint in the sidecar.