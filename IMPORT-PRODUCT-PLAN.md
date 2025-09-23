PRP: Product Import (Demo) – In-App Batch Import from Magento DB
Context

    Source: Magento DB (cos-magento-4) via MYSQL_SHOP_URL.
    Destination: App DB via lookbook_db_url.
    Existing adapters: MySQLShopCatalogAdapter (source), MySQLLookbookRepository (destination).
    Unique key: SKU. Upsert policy: update on conflict; no dry-run.
    Stock rule: import only where stock_qty > 0 and product is enabled.
    Scope: Import only ~5,000 enabled SKUs from a total of ~48,000.
    Frontend: React/Next.js + shadcn/ui.
    Backend: Python service (reuse adapters), expose simple HTTP endpoints.
    UX: No new admin page; keep it simple. Trigger from existing “Refresh” on /admin/products, open a minimal modal to configure and run import, with polling progress and finish-close button.
    Cursor: Use “last imported incremental ID” (source table primary key or source internal ID) to paginate. We will store/read this value from the app DB so “Resume from last” works.

Objectives (What to build)

    Minimal modal import UI launched from “Refresh”:
        Inputs:
            Batch size (default 100; max 1000).
            “Resume from last ID” toggle (default on). If off, “Start After ID” numeric input.
            “In stock only” fixed to true (hidden or disabled true; this is a demo).
        Buttons:
            Start Import
        Progress:
            Overall progress: discovered, processed, inserted, updated, errors, elapsed.
            Poll every 1s; show status “queued | running | completed | failed”.
        Completion:
            Summary and “Close” button.
    Backend endpoints:
        POST /api/admin/product-import/jobs
        GET /api/admin/product-import/jobs/:jobId
    Job execution:
        Python background task using existing adapters.
        Cursoring by source incremental ID (e.g., product_id). Store last_successful_source_id for resume.
        Upsert by SKU. Skip non-enabled or stock_qty <= 0 SKUs.
        Limit per job by input batch size.
    Persistence:
        product_import_jobs table (for job status and metrics).
        product_import_meta table (key/value) to store last_successful_source_id.

Non-Goals (Explicitly out of scope for now)

    Full admin page index/history.
    Advanced filters (category/price/date).
    Dry run preview.
    Scheduling, notifications, or downstream pipelines.
    Per-record error CSV.

Data Contracts

    product_import_jobs (app DB)
        id: UUID (pk)
        status: enum('queued','running','completed','failed')
        params: JSON
            limit: number
            resumeFromLast: boolean
            startAfterId: number | null
        metrics: JSON
            total_found: number
            processed: number
            inserted: number
            updated: number
            skipped: number
            errors_count: number
            elapsed_ms: number
            last_processed_source_id: number | null
        created_at, started_at, finished_at: datetime
        error_message: text (nullable)
    product_import_meta (key/value)
        key: string (pk) — use 'last_successful_source_id'
        value: string
    Source fetch contract (from MySQLShopCatalogAdapter):
        Provide a method to fetch products where:
            enabled = 1 (or equivalent)
            stock_qty > 0
            source_id > startAfterId
            order by source_id asc
            limit = requested batch size
        Returned fields used:
            source incremental ID (e.g., entity_id or product_id), sku, title, price, size_range, image_key, attributes, in_stock, season, url_key, product_created_at, stock_qty, category, color, material, pattern, occasion.
    Upsert contract (MySQLLookbookRepository):
        batch_upsert_products(products: List[dict])
        Conflict on SKU updates row.

API Specification

    POST /api/admin/product-import/jobs

    Request body:
        limit: number (default 100, max 1000)
        resumeFromLast: boolean (default true)
        startAfterId: number | null (required if resumeFromLast = false)
    Response 201:
        { jobId: string }

    GET /api/admin/product-import/jobs/:jobId

    Response 200:
        {
        id, status,
        params: { limit, resumeFromLast, startAfterId },
        metrics: {
        total_found, processed, inserted, updated, skipped, errors_count,
        elapsed_ms, last_processed_source_id
        },
        created_at, started_at, finished_at, error_message
        }

UX Flow (Modal on /admin/products)

    Click “Refresh”:
        Open modal “Import Products”.
        Inputs:
            Batch size [100]
            Resume from last [toggle ON]
            Start After ID [disabled when resume ON; enabled when OFF]
        “Start Import” -> POST job -> replace modal body with progress view.
    Progress view:
        Status chip (queued/running/completed/failed)
        Progress counts: processed/total_found (total_found may be unknown initially; show “—” then fill when known)
        Inserted, Updated, Skipped, Errors
        Elapsed time
        Poll GET every 1s.
    On completion:
        Show summary and “Close” button.

Implementation Plan (AI Work Plan Steps)

Backend (Python)

    Create migrations:
        Create product_import_jobs.
        Create product_import_meta (key/value).
    Implement repository layer for import metadata:
        get_meta(key), set_meta(key, value).
    Implement service: product_import_service.py
        create_job(params) -> jobId (insert with status queued).
        run_job(jobId):
            Update status=running, started_at.
            Resolve startAfterId:
                If resumeFromLast: read meta 'last_successful_source_id' (default 0).
                Else: use params.startAfterId.
            Fetch products from source with:
                enabled = true, stock_qty > 0
                source_id > startAfterId
                ORDER BY source_id ASC
                LIMIT = params.limit
            Map to product dicts (reuse logic from sync_100_products.py, fix indentation and guard None values).
            Call batch_upsert_products.
            Build metrics: total_found = len(fetched), processed = len(fetched), inserted/updated from repo response, skipped=0 (unless you filter during transform), errors_count.
            last_processed_source_id = max(source_id in fetched) or previous if none.
            On success:
                status=completed, finished_at, metrics, set_meta('last_successful_source_id', last_processed_source_id if any)
            On failure:
                status=failed, error_message, finished_at.
    Implement controller/HTTP endpoints:
        POST /api/admin/product-import/jobs
            Validate inputs (limit <= 1000; if resumeFromLast=false, require startAfterId).
            create_job -> spawn background runner (thread/async task) run_job(jobId).
            Return jobId.
        GET /api/admin/product-import/jobs/:jobId
            Return job row with metrics/params.
    Background execution:
        Use a simple thread/async task scheduler (since it’s a demo). Ensure thread-safe DB access.
    Update adapters if needed:
        Ensure MySQLShopCatalogAdapter has a method to fetch “enabled AND stock_qty > 0 AND source_id > X ORDER BY source_id ASC LIMIT N”.
        Ensure MySQLLookbookRepository.batch_upsert_products returns { upserted, updated, skus }.

Frontend (Next.js + shadcn/ui)
7) Add Import Modal component (opened from existing Refresh button on /admin/products):

    State: limit (100), resumeFromLast (true), startAfterId (''), jobId, job data, polling timer.
    Start Import:
        POST create job.
        Set jobId; start polling GET every 1000ms until status in ['completed','failed'].
    Render:
        Form (before job starts).
        Progress (after started): status, processed, inserted, updated, errors, elapsed, lastProcessedID.
        Completion summary and Close button.

    Wire the “Refresh” button to open the Modal:
        If you already use the button to do other refresh, change the label to “Import Products” or open the modal from a dropdown under Refresh.

Validation and Testing
9) Unit tests (service level):

    run_job with no data (should complete with zero processed).
    run_job with N products returns metrics and updates meta cursor.
    Failure path propagates error_message.

    Integration sanity:

    Start job via POST; observe GET polling moves from queued -> running -> completed.
    Confirm last_successful_source_id increases.
    Re-run with resume; should fetch next page.

Performance and Limits
11) Set default limit=100; max limit=1000 per job; concurrency limit=1 (no parallel jobs for demo).
12) Implement simple guard: if a job is running, new POST returns 409 or queues (your choice; for demo: allow one at a time and reject with message “Job already running”).
