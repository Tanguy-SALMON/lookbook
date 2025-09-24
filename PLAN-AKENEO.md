Product Requirement Prompt (PRP): Lookbook Feature with Akeneo linkage
Objective

Add a “Lookbook” capability to the existing Lookbook-MPC project, including database schema, FastAPI CRUD, and a Next.js/shadcn admin UI. Expose “Link to Akeneo” and “Export to Akeneo” actions and two Akeneo-branded pages (Export, Settings). Functionality may be stubbed where integrations aren’t ready, but the UX must clearly convey that Lookbook features map to Akeneo attributes.
Scope

    Backend (FastAPI, MySQL, plain SQL):
        Tables: lookbooks, lookbook_products
        CRUD routes: /v1/lookbooks
        Actions: POST /v1/lookbooks/{id}/link-akeneo, POST /v1/lookbooks/{id}/export-akeneo
    Frontend (Next.js 15, App Router, shadcn/ui, Tailwind):
        Navbar icon for Lookbook
        Pages:
            /lookbook: list + actions
            /lookbook/new: create
            /lookbook/[id]: edit + products subpanel + link/export actions
            /lookbook/akeneo/export: branded page
            /lookbook/akeneo/settings: branded page
    Branding assets:
        Akeneo logo URL: https://gillcapital.cloud.akeneo.com/bundles/pimui/images/logo.svg
        Colors: primary #4E7BBE, accent #6D9EEB, light-bg #F5F8FE (approximate)

Constraints and Rules

    Keep to current repo patterns (Next.js App Router, shadcn/ui; FastAPI; plain SQL; no ORM).
    Server components by default; client components for forms and interactivity.
    Parameterized SQL; no secrets exposed to the browser.
    Graceful empty/error states; no crashes if backend down.
    Keep files small and readable; prefer co-location for speed.

Data Model (MySQL)

    lookbooks:
        id PK, slug UNIQUE, title, description, cover_image_key, is_active
        akeneo_lookbook_id, akeneo_score DECIMAL(5,2), akeneo_last_update DATETIME
        akeneo_sync_status ENUM('never','linked','pending','exported','failed') DEFAULT 'never'
        akeneo_last_error TEXT
        created_at, updated_at
    lookbook_products:
        (lookbook_id, product_sku) PK, position INT, note

API Contract

    GET /v1/lookbooks?limit&offset&q
    POST /v1/lookbooks {slug,title,description?,cover_image_key?,is_active?,akeneo_*?}
    GET /v1/lookbooks/{id}
    PUT /v1/lookbooks/{id} same body as POST
    DELETE /v1/lookbooks/{id}
    GET /v1/lookbooks/{id}/products
    POST /v1/lookbooks/{id}/products {product_sku, position?, note?}
    DELETE /v1/lookbooks/{id}/products/{sku}
    POST /v1/lookbooks/{id}/link-akeneo {akeneo_lookbook_id}
    POST /v1/lookbooks/{id}/export-akeneo // stub: sets status -> pending -> exported

Responses: JSON; use 4xx/5xx on errors; messages for actions.
Acceptance Criteria

    CRUD works end-to-end against MySQL.
    Admin UI:
        Navbar shows Lookbook icon; clicking opens /lookbook.
        List shows Akeneo columns (ID, Sync status) and Export/Link actions.
        Detail page edits meta and manages product SKUs.
        Export and Settings pages show Akeneo branding and explanatory text linking features to Akeneo attributes.
    No console errors; graceful handling when backend not ready.

Work Plan (Execution Steps)

    Database Migration

    Create schema/lookbooks.sql with both tables and indexes.
    Execute against MySQL dev DB.
    Verification:
        Show tables; describe columns.
        Insert a sample row and select it back.

    Backend: Router and Wiring

    Create file lookbook_mpc/api/lookbooks.py with:
        Connection helper reading MYSQL_* env vars.
        Pydantic models: LookbookIn, Lookbook, LookbookProductIn, LinkAkeneoIn.
        All endpoints listed in API Contract with parameterized SQL.
    Mount router in main.py: app.include_router(lookbooks.router).
    Verification:
        Run server; curl each endpoint; ensure JSON results and proper status codes.

    Next.js Rewrites and Env

    Update shadcn/next.config.js:
        Proxy /api/lookbook/:path* -> http://localhost:8000/v1/lookbooks/:path*
    Add .env.local example:
        NEXT_PUBLIC_AKENEO_LOGO=https://gillcapital.cloud.akeneo.com/bundles/pimui/images/logo.svg
        NEXT_PUBLIC_API_URL=http://localhost:8000

    UI: Navbar Entry

    In shadcn/app/layout.tsx add a Lookbook icon/button in the top navbar linking to /lookbook.

    Frontend Routes and Pages

    Create route structure:
        app/lookbook/page.tsx — list + actions (server fetch; table UI).
        app/lookbook/new/page.tsx — create form (client).
        app/lookbook/[id]/page.tsx — detail/edit + products (server fetch + small client forms).
        app/lookbook/akeneo/export/page.tsx — Akeneo-branded explanation and “Export All” stub button.
        app/lookbook/akeneo/settings/page.tsx — Akeneo-branded mappings and placeholder connection form.
    Components:
        Optional small components for StatusBadge and ProductListRow to keep files tidy.
    Verification:
        Navigate through pages; create a lookbook; add/remove product SKU; statuses update.

    Action Wiring

    “Link to Akeneo” button opens a small input for akeneo_lookbook_id and POSTs to /api/lookbook/{id}/link-akeneo.
    “Export to Akeneo” triggers POST to /api/lookbook/{id}/export-akeneo; on success, refresh page.
    Verification:
        Observe akeneo_sync_status changing; no page errors.

    Empty/Error States and A11y

    Tables show “No lookbooks yet” when empty.
    Try/catch around fetches with small error banners.
    Buttons have aria-labels; forms have labels.

    Visual Branding

    Use Akeneo logo URL from env where needed.
    Apply Akeneo palette to Export and Settings pages (primary #4E7BBE; light bg #F5F8FE).
    Verification: Pages visibly carry Akeneo branding and explanatory text that maps fields:
        akeneo_lookbook_id
        akeneo_score
        akeneo_last_update
        akeneo_sync_status

    Tests (lightweight)

    Backend: happy-path unit tests for create/list/update/delete using a test DB.
    Frontend: render tests for list and detail pages using mocked fetch.

    Documentation

    Update README: new Lookbook feature, routes, and how to run.
    Add short docs section explaining the Akeneo linkage and future export.