Project: Lookbook MPC – Admin Dashboard (shadcn/Next.js) matching the provided screenshot

Purpose: This PRP is a complete instruction manual for an AI coding assistant to implement the dashboard UI and wiring using the provided repo and docs. Follow steps in order. Generate production-ready code on first pass.
Diagnose

    Goal: Build the main Dashboard page in shadcn/Next.js 15 that visually matches the uploaded screenshot and surfaces live data from the Lookbook MPC backend.
    Inputs:
        Tech: Next.js 15 App Router, Tailwind, shadcn/ui, TypeScript-lite, Lucide icons.
        Backend endpoints and semantics from README.md, USER_GUIDE.md, SETUP_GUIDE.md.
        Services: Main API: 8000, Vision: 8001, Ollama: 11434; Next.js runs at 3000.
        Existing structure under shadcn/ (app/page.tsx, components/ui/*, globals.css, tailwind.config.js, next.config.js).
    Assumptions:
        Data contracts can be shaped by our frontend adapter functions.
        We’ll fetch via server components when possible; client components only for charts/interactive filters.
        Styling via Tailwind + shadcn primitives only.
    Unknowns:
        Exact API response shapes for some aggregate metrics. Use adapter functions to normalize. If missing, create temporary mock endpoints under /app/api/mock/* with TODO to swap to real.

Deliverables

    Dashboard layout and widgets matching the screenshot:
        Left column “profile card” with avatar, name, role, tags.
        Top greeting “Good morning Jhon” [sic per screenshot].
        Tabs/pills header: Dashboard, Calendar, Projects, Team, Documents.
        Action pills: Add widget, Date range picker, Add report.
        Main analytics card: Average hours/weeks with dot chart + onsite/remote donut stats.
        Row of three: Average work time line chart; Track your team semicircle gauge + totals; Talent recruitment list + “Join call”.
        Right sidebar:
            Search + quick icons.
            Salaries and incentive list with statuses (Waiting/Done/Failed).
            Salary calculator card with sliders/inputs and total “Take home pay”.
    Data integration:
        System Status ping indicators (Main API, Vision, Ollama).
        Stats: total products, analyzed items, recommendations, chat sessions, success/error rates.
        Activity feed with timestamps.
    Reusable chart components:
        Sparkline/line, dot heatmap, semicircle gauge, bar mini-chart.
    State:
        Global refresh interval env NEXT_PUBLIC_REFRESH_INTERVAL (default 30000).
        Manual Refresh button.
    Accessibility: keyboard focus, aria labels on interactive controls.
    Tests: basic render tests for components; API adapters with zod schema validation.
    Notes and TODOs for any shortcuts.

Constraints and Guidelines

    Use server components by default; create a small client “Charts” island.
    No CSS files beyond globals.css; all styling via Tailwind classes.
    Keep components <200 lines; split by card.
    TypeScript is allowed but keep types minimal. Use zod for runtime validation at API boundaries.
    Do not introduce external chart libs; implement simple SVG/Canvas charts or Tailwind-based bars.
    Env and rewrites: follow README next.config.js proxy to backend.
    Guardrails: No secrets in client. Handle failed fetches with graceful empty states.

Data Contracts (Adapters)

Implement adapter layer under shadcn/lib/data.ts:

    getSystemHealth(): GET /ready; shape:
        { mainApiOk: boolean, visionOk: boolean, ollamaOk: boolean }
    getDashboardStats(): aggregate via:
        GET /v1/ingest/stats
        GET /v1/recommendations/popular?limit=1
        GET /v1/chat/sessions (count)
        Return:
        { totalProducts, analyzedItems, recommendationsTotal, chatSessions, avgAnalysisTimeMs, successRatePct, errorRatePct, categoryDistribution: Array<{name, pct}>, recentActivity: Array<{id, type, message, ts, status}> }
    getPayroll(): temporary mock from /app/api/mock/payroll route:
        { items: Array<{ id, name, amount, dateLabel, status: "Waiting"|"Done"|"Failed", avatarUrl }> }
    getTeamStats(): mock or compute from backend categories:
        { totalMembers, byRole: [{role, count, color}] }
    getHiringStats(): mock list of candidates with images and match bars.

All adapters validate/transform with zod. If an endpoint is unavailable, return fallback with flags {stale: true}.
Step-by-Step Work Plan

    Project scaffolding and config

    Ensure shadcn/app structure exists; confirm rewrites in next.config.js per README.
    Add env defaults in .env.local.example for refresh interval and app name.

    Data layer

    Create lib/data.ts with fetchJson helper, zod schemas, and functions listed above.
    Create lib/utils.ts additions: cn, fmtPercent, fmtNumber, fmtCurrency.

    UI primitives and tokens

    Extend tailwind.config.js with semantic colors used in screenshot (mint, teal, navy, soft-gray, warning, success).
    Add shadcn/ui components if missing: badge, progress, input, avatar, dropdown-menu, card, button, tabs, tooltip, separator, switch.

    Charts island (client)

    components/charts/*:
        Sparkline.tsx – simple SVG line sparkline.
        DotsHeatmap.tsx – grid of circles with intensity.
        SemiGauge.tsx – semicircle with segments and center value.
        BarsMini.tsx – vertical bars with matched/not matched legend.

    Dashboard cards (server unless animated)

    components/dashboard/
        GreetingHeader.tsx – breadcrumbs, tabs, actions.
        ProfileCard.tsx – avatar, name/role, action icons.
        AvgHoursCard.tsx (client) – DotsHeatmap + 46.5 avg + onsite/remote panel.
        WorkTimeCard.tsx (client) – Sparkline with marker “8 Hours”.
        TrackTeamCard.tsx (client) – SemiGauge + role legend and totals.
        TalentRecruitmentCard.tsx (client) – avatars + BarsMini + “Join call”.
        SystemStatusCard.tsx – pings for Main API/Vision/Ollama.
        SalariesList.tsx – right sidebar list with statuses.
        SalaryCalculator.tsx (client) – inputs and computed total.
        ActivityFeed.tsx – recent events with colored dots.
    Compose them in app/page.tsx grid matching screenshot.

    Page implementation and layout

    app/layout.tsx already exists; ensure globals.css imports font classes and rounded-2xl look.
    app/page.tsx fetches data via adapter functions in parallel (Promise.all) on the server, passes to client charts where needed.

    Interactions

    Refresh button triggers router.refresh() and revalidation.
    Date range pill opens shadcn dropdown with presets; for now, non-functional placeholder with TODO.
    Salary calculator sliders/inputs update computed “Take home pay” instantly.

    Tests and validation

    Add tests/components/*.test.tsx basic render tests with Jest/RTL.
    Add unit tests for lib/data.ts adapter parsing with mock responses.

    Documentation

    Update README “Dashboard Features” to include new cards.
    Append PROJECT_KNOWLEDGE_BASE.md entry: components and data contracts.
    Inline TODOs for replacing mocks with real endpoints.

File-by-File Code Generation

    tailwind.config.js add colors

    Add:
        mint: #E8F6EF
        teal-600: #2FA39A
        navy-700: #164B63
        slate-100/#F3F5F7, slate-400, slate-600
        success: #22C55E
        warning: #F59E0B
        danger: #EF4444

    lib/data.ts

    Provide fetchJson with timeout and retry (2x).
    zod schemas:
        ReadySchema, IngestStatsSchema, ChatSessionsSchema, PayrollSchema, TeamStatsSchema, HiringSchema.
    Export functions: getSystemHealth, getDashboardStats, getPayroll, getTeamStats, getHiringStats.

    components/charts/Sparkline.tsx

    Client component props: data:number[], width, height, color, markerAtIndex?:number.

    components/charts/DotsHeatmap.tsx

    Props: rows, cols, values:number[] (0–1), dotColor, lowOpacity.

    components/charts/SemiGauge.tsx

    Render 180° arc with colored segments; center numeric label and caption.

    components/charts/BarsMini.tsx

    Render 20 bars; first n as “Matched” in green; rest in gray.

    components/dashboard/* cards

    Implement each card with Tailwind shades and shadcn Card primitives. Use screenshots’ layout cues: rounded-xl, soft drop shadows, paddings (p-5), gaps.

    app/page.tsx

    Server component. Parallel data fetching:
        const [health, stats, payroll, team, hiring] = await Promise.all([...])
    Grid layout:
        Main content 2/3 width; right sidebar 1/3 width.
        Provide responsive behavior for md/lg/2xl breakpoints akin to screenshot.

    app/api/mock/*

    /payroll/route.ts returns sample list matching screenshot names and statuses.
    /hiring/route.ts returns candidate list + match scores.
    These routes are a stopgap; guarded with “MOCK_DATA=1” env flag. If disabled, respond 404 to avoid shipping mocks to prod.

    Tests

    Basic tests for rendering of key cards and adapter parsing.

Commands

    Frontend dev:

bash

Copy
cd shadcn
npm install
npx shadcn-ui@latest add badge progress input avatar dropdown-menu card button tabs tooltip separator switch
npm run dev

    Run tests:

bash

Copy
cd shadcn
npm run test

Validation

    Manual:
        Open http://localhost:3000. Page loads with greeting, tabs, cards laid out like screenshot.
        Toggle refresh; data updates without full-page flash.
        If backend up, system status pings green; otherwise gray/red with tooltips.
        Salary calculator updates “Take home pay” immediately.
    API:
        With services running per SETUP_GUIDE, verify no console errors.
        If endpoints unavailable, mock data renders with subtle “stale” badge.

Non-Functional Requirements

    Performance: avoid heavy chart libs; prefer SVG.
    Accessibility: labels and focus states on search, buttons, toggles.
    Error handling: show inline empty states and retry links.
    Internationalization: number formatting via Intl.

Example Snippets

lib/data.ts fetch helper:

ts

Copy
// shadcn/lib/data.ts
import { z } from "zod";

const withTimeout = async <T>(p: Promise<T>, ms = 8000) =>
  await Promise.race([p, new Promise<never>((_, r) => setTimeout(() => r(new Error("timeout")), ms))]);

export async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await withTimeout(fetch(url, { ...init, cache: "no-store" }));
  if (!("ok" in res) || !(res as any).ok) throw new Error(`Fetch failed ${url}`);
  return (await (res as any).json()) as T;
}

// …define zod schemas and adapters as per PRP…

System status pill:

tsx

Copy
function StatusDot({ ok }: { ok: boolean }) {
  const color = ok ? "bg-emerald-500" : "bg-rose-500";
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${color}`} aria-hidden="true" />;
}

Right sidebar list item:

tsx

Copy
<Badge variant="outline" className={status === "Done" ? "text-emerald-600 border-emerald-300 bg-emerald-50" :
 status === "Waiting" ? "text-amber-600 border-amber-300 bg-amber-50" : "text-rose-600 border-rose-300 bg-rose-50"}>
  {status}
</Badge>

Refactor-Later Notes

    Replace mock /api/mock endpoints with real payroll/hiring sources when available.
    Consolidate chart primitives into a single Canvas renderer if animation is needed.
    Move hardcoded colors into a design tokens file.

Acceptance Criteria

    Visual parity with the provided screenshot within reasonable Tailwind/shadcn constraints.
    No console errors; degraded but functional rendering when backend is offline.
    All cards responsive and accessible; keyboard navigable.
    Data updates on interval and manual refresh.
    Lightweight charts render smoothly at 60fps on modern laptops.
