PRP/PDP: lookbook‑MPC (execution plan)
1) Objective & scope

    Build a FastAPI-based recommendation microservice for fashion lookbooks that:
        Ingests catalog items (read-only Magento MySQL + S3 image keys).
        Uses a vision sidecar (Ollama qwen2.5-vl:7b) to tag items.
        Parses user intents (Ollama qwen3) and composes outfits via rules.
        Exposes REST + MCP tools; includes a minimal chat test page.

2) Assumptions & deps

    Ollama daemon available; models: qwen2.5-vl:7b (vision), qwen3 (text).
    Shop DB: Magento (read-only). Lookbook DB: SQLite by default (switchable).
    Images served as S3_BASE_URL + image_key, with optional proxy/redirect.

3) Canonical Naming & Structure (CNS)

    Repo: lookbook-mpc
    Package: lookbook_mpc
    Layout:
        lookbook_mpc/domain/{entities.py,use_cases.py}
        lookbook_mpc/services/{rules.py,recommender.py}
        lookbook_mpc/adapters/{db_shop.py,db_lookbook.py,vision.py,intent.py,images.py}
        lookbook_mpc/api/{routers/{ingest.py,reco.py,chat.py,images.py}, mcp_server.py}
        migrations/, tests/, scripts/
    Models: OLLAMA_VISION_MODEL=qwen2.5-vl:7b, OLLAMA_TEXT_MODEL=qwen3

4) Config (env)

    MYSQL_SHOP_URL, LOOKBOOK_DB_URL (sqlite:///lookbook.db default), OLLAMA_HOST, OLLAMA_VISION_MODEL, OLLAMA_TEXT_MODEL, S3_BASE_URL, TZ, LOG_LEVEL

5) Milestones (step-by-step for codegen)

    M1. Scaffold + quality
        Create FastAPI app, pyproject, ruff/black/mypy/pytest, .env.example, health endpoints (/health,/ready).
        Add CNS directories and empty modules; wire logging with request IDs.
    M2. Domain entities (Pydantic/SQLAlchemy)
        Item(id, sku, title, price, size_range, image_key, attrs JSON)
        Outfit(id, title, rationale, intent_tags JSON)
        OutfitItem(outfit_id, item_id, role)
        Rule(id, name, intent, constraints JSON)
        Event(optional)
        Provide Pydantic schemas mirroring public API models.
    M3. Lookbook DB + migrations (Alembic)
        Create tables, indexes (by color, category, price), FKs; seed basic rules (yoga, dinner-$50, slimming).
    M4. ShopCatalogAdapter (MySQL, read-only)
        Implement query you provided to fetch in-stock SKUs + image_key (gc_swatchimage).
        Map to shadow items with derived image_url = S3_BASE_URL + "/" + image_key.
    M5. Vision sidecar + adapter
        Wrap VisionAnalyzer as HTTP service: POST /analyze {image_url|image_bytes} → {color, description, attributes}.
        Fix vision_analyzer.py: add “import re”, correct indentation; make model/timeouts/env-driven.
        Adapter VisionProviderOllama calls sidecar; batch ingestion with BackgroundTasks.
    M6. Intent parser (qwen3 via Ollama)
        Implement LLMIntentParser with a deterministic JSON schema output. Prompt template:
            System: “You convert fashion requests into constraints.”
            User: free text; require JSON only: {intent, activity?, occasion?, budget_max?, objectives[], palette?, formality?, timeframe?, size?}
        Include few-shot examples for:
            “I want to do yoga”
            “Restaurant this weekend, attractive for $50”
            “I am fat, I want something to look slim”
    M7. Rules engine + recommender
        rules.py maps normalized intents to constraints (categories, materials, silhouettes, palettes, price caps).
        recommender.py: candidate filtering (SQL + attrs), outfit assembly (top/bottom/shoes/outer), scoring (fit to constraints), fallback when sparse inventory.
        Have rationale generator using qwen3 with concise bullet justification.
    M8. APIs
        POST /v1/ingest/items {limit?, since?} → 202
        POST /v1/recommendations {text_query, budget?, size?, week?} → {outfits:[{items:[{item_id,role}], rationale, score}], constraints_used}
        POST /v1/chat {session_id?, message} → {session_id, replies:[...], outfits?}
        GET /v1/images/{key} → 302 to S3 or stream
        OpenAPI documented; JSON examples provided.
    M9. MCP server
        Tools:
            recommend_outfits(query, budget?, size?) → outfits
            search_items(filters) → items
            ingest_batch(limit?) → status
        Resources: openapi.json, rules_catalog.json, schemas.
        Run MCP in same process; version tools.
    M10. Minimal chat UI (demo)
        Static HTML page served at /demo: simple chat box calling /v1/chat; render outfit cards with image URLs.
    M11. Tests
        Unit: intent parsing (golden JSON), rules mapping, outfit assembly logic.
        Integration: ingest small fixture set, call /recommendations for the three example queries; assert non-empty outfits and constraint compliance.
        Contract: pydantic schema validation on API responses.
    M12. Deploy
        docker-compose with services: api, vision, ollama; preload models; env wired.
        Optional Nginx for static and proxy; configure CORS.

6) Key prompts (ready-to-use)

    Vision (sidecar) prompt (JSON-only)
        System: “You are a fashion vision tagger. Output strict JSON only.”
        User: include tag or URL; ask for:
            {"color":"", "category":"", "material":"", "pattern":"", "style":"", "season":"", "occasion":"", "fit":"", "plus_size":true/false, "description":""}
        Temperature 0; set max tokens ~256.
    Intent parser (qwen3) prompt
        System: “You convert a shopper request into structured constraints. Output JSON only. Unknown fields = null.”
        User text; Response schema:
            {"intent":"recommend_outfits","activity":null|"yoga","occasion":null|"dinner","budget_max":null|number,"objectives":["slimming"],"palette":null|["dark","monochrome"],"formality":"casual|elevated|athleisure","timeframe":"this_weekend|next_week", "size":null|"XL"}
        Few-shots for the 3 example queries.
    Rationale prompt (qwen3)
        “Given items and constraints, write a 2–3 sentence rationale. JSON: {"rationale": "..."}”

7) API schemas (concise)

    POST /v1/recommendations request

{
  "text_query": "I want to do yoga",
  "budget": 80,
  "size": "L",
  "week": "2025-W40",
  "preferences": {"palette": ["dark"]}
}

    Response

{
  "constraints_used": {"activity":"yoga","formality":"athleisure","budget_max":80},
  "outfits": [
    {
      "items": [
        {"item_id": 123, "sku":"1295990003", "role":"top", "image_url":"..."},
        {"item_id": 456, "sku":"1295990011", "role":"bottom", "image_url":"..."}
      ],
      "score": 0.82,
      "rationale": "Stretch fabrics and breathable top suited for yoga; monochrome keeps it sleek."
    }
  ]
}

8) DB sketch (SQLAlchemy models)

    Item: id PK, sku, title, price, size_range, image_key, attrs JSON, in_stock bool
    Outfit: id PK, title, intent_tags JSON, rationale
    OutfitItem: outfit_id FK, item_id FK, role
    Rule: id PK, name, intent, constraints JSON
    Indexes: item.color, item.attrs->category, price

9) Magento + S3 adapter notes

    Use your SQL to fetch (sku, image_key) for in-stock + enabled.
    Store only image_key; compute image_url on response: f"{S3_BASE_URL}/{image_key}".
    Optional: GET /v1/images/{key} returns 302 redirect to S3 URL for easy embedding and CORS control.

10) Guardrails & NFRs

    No secrets in code; env-only.
    Timeouts and retries for Ollama calls; fail closed with informative errors.
    Input validation on all endpoints; JSON-only LLM outputs with strict parsing.
    Logging: request_id, model, latency; health/readiness endpoints.
    Portability: SQLite default; switch to MySQL/Postgres by LOOKBOOK_DB_URL.
    MCP tool versioning and stable schemas for integration.