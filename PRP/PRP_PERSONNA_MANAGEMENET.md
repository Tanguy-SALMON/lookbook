PRP: Agent Admin Page (Shadcn Admin Backend) — Persona Management with Templates

    Context and objectives

    Problem: We need a simple, shippable UI to create and edit “Sales Agent Personas” using the 10 behavioral attributes, with presets (e.g., Obama-like, Kennedy-like) and a freeform notes field. This enables rapid A/B testing and consistent behavior in the Lookbook-MPC system.
    Users/personas: Internal admins, product managers, sales ops; later power users.
    Goals:
        Create, edit, duplicate, and delete agent personas.
        Edit 10 attributes (short text each) + overall notes.
        Apply preset templates (2–3 to start).
        Minimal controls: global verbosity and decisiveness sliders.
        Preview sample response using the persona config.
    Non-goals:
        Full RBAC, audit history, or workflow approvals.
        Complex multi-tenant or versioning.
        Import/export beyond simple JSON copy.

    Requirements

    Functional
        List page: table of personas with name, preset, updated_at; actions (edit, duplicate, delete).
        Create/Edit page: 10 attributes (short textareas), overall notes (large textarea), name, optional preset select, verbosity (0–2), decisiveness (0–2), Save/Preview/Reset-to-neutral.
        Apply preset fills all fields; user may tweak then save.
        Preview pane shows a synthetic “sample reply” per persona to validate tone.
        Backend CRUD endpoints for personas.
    Non-functional
        UI: Shadcn/UI components with Next.js app in shadcn/.
        Usability: Low cognitive load; clear labels; inline help.
        Accessibility: Keyboard focus, labels, ARIA where needed.
        Performance: P95 < 200ms on list, < 300ms on save (local dev).
    Acceptance criteria
        Can create a persona from blank or preset and save it.
        Can edit any field and see preview update.
        Can duplicate a persona and edit the copy.
        Can delete a persona with confirmation.
        Preset application overwrites current fields with confirmation.

    Architecture and interfaces

    Stack: Next.js (app dir), Shadcn/UI, React, TypeScript. Backend served by the same Next.js (API routes) or proxied to FastAPI. For V1 keep API in Next.js to ship fast, then mirror to FastAPI.
    Data model (Persona)
        id: string (UUID)
        name: string
        preset_name?: "obama_like" | "kennedy_like" | "friendly_stylist"
        attributes: object with 10 short strings:
            core_style
            framing
            motivational_drivers
            emotional_register
            interpersonal_stance
            rhetorical_techniques
            risk_posture
            objection_handling
            practical_cues
            deployment_rules
        notes: string
        verbosity: 0 | 1 | 2
        decisiveness: 0 | 1 | 2
        updated_at: datetime
    Backend API (Next.js API routes for V1)
        GET /api/personas → list
        POST /api/personas → create
        GET /api/personas/:id → get
        PATCH /api/personas/:id → update
        DELETE /api/personas/:id → delete
        POST /api/personas/:id/apply_preset → body: { preset_name }
    Preview API
        POST /api/personas/:id/preview → body: { prompt } returns: { sample:string }
        For V1, generate sample deterministically on the server using rules (no external LLM call required). Later wire to MCP/LLM.
    Storage
        V1: JSON file or in-memory store for demo.
        V2: Persist in Lookbook DB (SQLite/MySQL). Table personas.

    Work plan (AI-executable steps)
    Step 1: Create data types and presets

    Add shadcn/lib/persona/types.ts with Persona interface and constants for attribute keys.
    Add shadcn/lib/persona/presets.ts exporting 3 presets (see section 8).
    Add simple in-memory repository shadcn/lib/persona/store.ts (Map or JSON file read/write).

Step 2: Implement Next.js API routes

    Create shadcn/app/api/personas/route.ts for GET (list) and POST (create).
    Create shadcn/app/api/personas/[id]/route.ts for GET, PATCH, DELETE.
    Create shadcn/app/api/personas/[id]/apply_preset/route.ts for POST to apply preset.
    Create shadcn/app/api/personas/[id]/preview/route.ts for POST to return sample text using a deterministic formatter function.

Step 3: Admin navigation and pages

    Add sidebar nav item “Personas” under Admin.
    Create shadcn/app/admin/personas/page.tsx — list page.
    Create shadcn/app/admin/personas/new/page.tsx — create page.
    Create shadcn/app/admin/personas/[id]/page.tsx — edit page.

Step 4: UI components (Shadcn)

    Create components:
        PersonaForm.tsx: form with fields: name, preset select, 10 textareas, notes, sliders (verbosity, decisiveness), buttons (Apply Preset, Reset, Save, Preview).
        PersonaList.tsx: data table with Row actions (Edit, Duplicate, Delete).
        PersonaPreview.tsx: right-side panel showing sample response. Accepts persona and a fixed test prompt (e.g., “Recommend an outfit for a summer outdoor event under ฿3000.”).
    Use Shadcn components: Card, Input, Textarea, Select, Button, Slider, Dialog (confirm delete), Toast.

Step 5: Form logic

    On preset change: show confirm dialog “Apply preset and overwrite current fields?” Yes overwrites attributes + notes + preset_name; keep name as-is unless blank.
    Reset to neutral: fill attributes with neutral defaults (short, balanced language), clear preset_name.
    Save: POST or PATCH to API; toast on success/failure.
    Duplicate: from list page, action builds a new persona client-side (copy + “(Copy)”) and POST.

Step 6: Preview generation

    Implement shadcn/lib/persona/preview.ts: function generateSample(persona, prompt) that creates a short synthetic response:
        Use verbosity to adjust length.
        Use decisiveness to adjust hedging vs. imperative tone.
        Weave in key phrases from core_style, rhetorical_techniques, practical_cues.
    API route calls generateSample and returns sample. UI shows live preview on demand.

Step 7: Validation and hints

    Enforce length: each attribute 1–2 sentences, max 240 chars; notes max 2000 chars.
    Client-side helper text for each attribute: “1–2 sentences describing behaviors and phrases to use/avoid.”
    Validate name required, unique on create (store layer checks).

Step 8: Tests (minimal but real)

    Unit (frontend utils): preview generator tone changes with sliders; preset application overwrites as expected.
    API route tests (Next.js API handlers): CRUD works; apply_preset updates attributes; preview returns 200 with sample.
    Snapshot test: rendering PersonaForm with preset loads fields correctly.

Step 9: Wiring to backend (optional V1.5)

    Add sync endpoint to FastAPI to upsert persona into app DB for system-wide use: POST /v1/personas (mirror schema).
    From Next.js after save, optionally forward to FastAPI (feature flag).

Step 10: Docs and examples

    Update README.md Admin section: Personas feature overview, endpoints, screenshots placeholder.
    Add example persona JSON payloads for the 3 presets.
    Add cURL examples for CRUD.

    Code patterns and examples

    Example Persona JSON

json

Copy
{
  "id": "uuid-123",
  "name": "Obama-like",
  "preset_name": "obama_like",
  "attributes": {
    "core_style": "Reflective, inclusive, narrative; careful qualifiers.",
    "framing": "Acknowledge trade-offs; propose balanced options and shared path forward.",
    "motivational_drivers": "Hope, fairness, shared responsibility; long-term benefits.",
    "emotional_register": "Calm, reassuring, occasionally wry.",
    "interpersonal_stance": "Active listening; paraphrase and validate before advising.",
    "rhetorical_techniques": "Story, parallelism, context; cite sources when relevant.",
    "risk_posture": "Incremental; stress-test assumptions; phase plans.",
    "objection_handling": "Empathetic reframing and principled compromise.",
    "practical_cues": "Ask 1–2 clarifying questions; provide 2–3 options with trade-offs.",
    "deployment_rules": "Use in complex, ambiguous, multi-stakeholder scenarios."
  },
  "notes": "Use 'we' language and emphasize civic duty; avoid overclaiming.",
  "verbosity": 2,
  "decisiveness": 1,
  "updated_at": "2025-09-22T08:00:00Z"
}

    Example list response

json

Copy
{ "items": [ { "id":"...", "name":"Obama-like", "preset_name":"obama_like", "updated_at":"..." } ] }

    Example cURL

bash

Copy
# Create
curl -X POST http://localhost:3000/api/personas \
  -H "Content-Type: application/json" \
  -d @persona_obama.json

# Apply preset
curl -X POST http://localhost:3000/api/personas/UUID/apply_preset \
  -H "Content-Type: application/json" \
  -d '{"preset_name":"kennedy_like"}'

# Preview
curl -X POST http://localhost:3000/api/personas/UUID/preview \
  -H "Content-Type: application/json" \
  -d '{"prompt":"I need an outfit for a summer outdoor event under ฿3000."}'

    Test plan

    Unit
        presets.ts: contains required keys; values are non-empty.
        preview.ts:
            decisiveness=0 adds hedging (“might,” “consider”); decisiveness=2 uses imperatives.
            verbosity=0 returns ~1–2 sentences; verbosity=2 returns ~3–5 sentences.
        store.ts: unique name enforcement throws on duplicates.
    API integration
        Create → Get → Update → Delete lifecycle.
        apply_preset overwrites attributes and notes, sets preset_name.
        preview returns 200 and non-empty sample.
    UI
        PersonaForm loads preset into fields; Reset clears to neutral.
        Save disabled until name present; toasts on success.
        Duplicate creates new row with “(Copy)”.
    Coverage goal: Basic critical paths; no need for exhaustive e2e in V1.

    Observability and ops

    Log UI actions: persona_created, persona_updated, preset_applied, preview_clicked.
    API metrics: requests_count by route, status_code; simple console logs in V1.
    Feature flag: FORWARD_TO_FASTAPI=false (default). If true, POST mirror to FastAPI.

    Guardrails

    Content limits: enforce max lengths to keep prompts lean.
    Security: No PII; admin-only route protection (reuse existing admin auth).
    Preset overwrite confirmation to prevent accidental data loss.
    Notes field is freeform but do not allow HTML; sanitize input.

    Review gates

    Gate A: After Step 4 (UI skeleton + API stubs), review UX and fields.
    Gate B: After Step 6 (Preview working), review tone outputs with 3 presets.
    Gate C: After Step 8 (tests), final polish and docs.

    Deliverables

    Code: Types, presets, store, API routes, pages, components.
    Tests: utils + API + basic UI snapshot.
    Docs: README section + sample JSON + cURL.
    Screens: Personas list, Create/Edit with Preview.

Preset templates (2–3 to start)

    Obama-like

    Core communication style: Reflective, inclusive, narrative; careful qualifiers.
    Framing: Acknowledge trade-offs; propose balanced options and shared path.
    Motivational drivers: Hope, fairness, shared responsibility.
    Emotional register: Calm, reassuring, occasionally wry.
    Interpersonal stance: Active listening; paraphrase and validate before advising.
    Rhetorical techniques: Story, parallelism, context; cite sources when relevant.
    Risk posture: Incremental; stress-test assumptions; phased delivery.
    Objection handling: Empathetic reframing; principled compromise.
    Practical cues: Ask 1–2 clarifying questions; provide 2–3 options with trade-offs.
    Deployment rules: Use for complex, ambiguous, multi-stakeholder scenarios.
    Notes: Use “we” language; avoid overclaiming; emphasize durable wins.
    Sliders: verbosity=2, decisiveness=1.

    Kennedy-like

    Core communication style: Crisp, imperative, quotable.
    Framing: Mission, deadline, first step.
    Motivational drivers: Courage, excellence, pride in hard goals.
    Emotional register: High-energy optimism.
    Interpersonal stance: Directive, charismatic; ask for alignment.
    Rhetorical techniques: Antithesis, aphorisms, short lines.
    Risk posture: Audacious; time-bound commitments.
    Objection handling: Recenter mission; convert difficulty into urgency.
    Practical cues: 3-step plan; minimal hedging.
    Deployment rules: Launches, turnarounds, momentum building.
    Notes: Prefer short paragraphs; state deadlines and commitments.
    Sliders: verbosity=1, decisiveness=2.

    Friendly Stylist (retail/fashion tuned)

    Core communication style: Warm, upbeat, conversational; practical tips.
    Framing: Occasion-first; budget- and size-aware suggestions.
    Motivational drivers: Confidence, comfort, self-expression.
    Emotional register: Encouraging, positive, approachable.
    Interpersonal stance: Collaborative; invites preferences and feedback.
    Rhetorical techniques: Benefit-forward phrasing; simple, vivid language.
    Risk posture: Low-risk; suggest affordable alternatives and try-ons.
    Objection handling: Offer size/fit workarounds; care instructions; easy returns.
    Practical cues: Recommend 3–5 looks; include size notes and swap options.
    Deployment rules: Everyday shoppers, gifting assistance, post-purchase styling.
    Notes: Use Thai Baht; include care tips; avoid technical jargon.
    Sliders: verbosity=2, decisiveness=1.

Neutral defaults (for Reset)

    Core communication style: Clear, professional, concise.
    Framing: State problem, propose 2–3 options, recommend one.
    Motivational drivers: Practical value and convenience.
    Emotional register: Calm and friendly.
    Interpersonal stance: Helpful and respectful.
    Rhetorical techniques: Plain language; minimal jargon.
    Risk posture: Balanced; note key risks briefly.
    Objection handling: Address concern directly and suggest an alternative.
    Practical cues: Confirm requirements; summarize next steps.
    Deployment rules: General-purpose interactions.
    Sliders: verbosity=1, decisiveness=1.

Implementation notes

    Attribute labels in UI must match the 10-factor names to keep cognitive load low.
    Show helper hint under each textarea: “1–2 sentences; behaviors to use/avoid.”
    Preview prompt fixed string for demo; later allow custom prompt input.
    Ensure Shadcn styling matches the rest of Admin dashboard.

Hand-off checklist for the code editor

    Create types.ts, presets.ts, preview.ts, store.ts.
    Implement API routes as specified (CRUD, apply_preset, preview).
    Build pages and components (list, form, preview panel).
    Add minimal tests from Step 8.
    Add README section with cURL examples and JSON samples.
    Wire nav link “Personas” in the admin sidebar.

If you want, I can also provide the exact TypeScript interfaces, sample Next.js API route handlers, and the PersonaForm JSX scaffold in a follow-up message so your editor can code it directly.
