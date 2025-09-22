Plan (theory-first, minimal changes)

    Where to hook
        Your router delegates to ChatTurn (use case) which calls IntentParser + Recommender + Lookbook + Rules.
        Add a lightweight “Persona/Strategy” module that:
            Injects a system-style directive (tone, goals, constraints) into each turn.
            Optionally rewrites the outgoing reply for tone/style consistency.
            Optionally biases the recommender (e.g., push margin, promo, new arrivals) via RulesEngine flags.
    What to store
        Per-session strategy config in sessions[session_id]["context"]["strategy"]:
            tone: friendly | luxury | concise | playful | Thai-first | bilingual.
            objectives: upsell_accessories, increase_AOV, clear_aging_stock, push_promo.
            guardrails: avoid_discounts, avoid_push_if_budget.
            style: sentence_length, emojis, CTA strength.
        Marketing calendar/promos: a static dict or fetched daily (cron) that sets default strategy (e.g., “Mid-Season Sale → highlight 20% off category X”).
    How it flows (simple)
        On request:
            Merge default strategy + session overrides + AB test bucket.
            Build a compact system directive string from strategy.
            Pass this to IntentParser or ChatTurn so it’s considered when crafting replies.
        On recommendations:
            Pass strategy flags to RulesEngine/OutfitRecommender to bias results.
        Before returning:
            Run a small “tone post-processor” that reformats the reply to match style (CTA, sentence length, bilingual line, emojis policy).
    Minimal changes to your code
        Add a StrategyService with:
            get_strategy(session_id) → dict
            build_system_directive(strategy) → str
            apply_reply_tone(reply, strategy) → str
        In chat_turn():
            Resolve strategy.
            Attach to request (e.g., request.meta.system_directive).
            After chat_use_case.execute(), post-process response.replies[0]["message"] with StrategyService.apply_reply_tone().
            Save strategy into session context for continuity.
    Marketing bias examples
        Junior:
            If objectives.include("upsell_accessories"): after recommender returns outfits, append 1–2 accessories with simple CTA.
        Pro:
            Weight ranking: score += w_marginmargin + w_newnessis_new + w_stock*stock_age
            Pull weights from strategy.
        Advanced:
            Contextual A/B: different tones per cohort (returning vs new customers), log conversion proxy (clicks on PDP, add-to-cart), adjust next-turn strength.

Concrete examples

    Strategy dict example
        Good:
            {"tone":"luxury_concise","lang":"th_en","objectives":["raise_aov","promote_new_arrivals"],"guardrails":["no_hard_discount_push"],"style":{"max_sentences":3,"cta":"soft","emojis":false}}
        Bad:
            {"tone":"nice"} // too vague, not actionable
    System directive built from strategy (short and cheap)
        Good:
            “Persona: Premium fashion advisor. Tone: concise, elegant, no emojis. Goals: raise AOV via subtle accessories; highlight new arrivals. Guardrails: if user mentions budget, avoid upsell. Language: answer in Thai if user Thai, else English. Keep to 3 sentences max. Always end with one soft CTA.”
        Bad:
            “You are a helpful assistant who sells clothes.” // no constraints or goals
    Tone post-processor rules
        Good:
            Limit to N sentences.
            Ensure last sentence is a CTA of chosen strength (soft: “Would you like me to add the belt?” vs hard: “Add to cart now”).
            For bilingual: if user message contains Thai characters, prepend Thai line, then English line.
        Bad:
            Blindly append promo text to all replies (annoying, non-contextual).
    Recommender biasing examples
        Junior:
            If “raise_aov”: after top-3 outfits, append “Matching accessories” section with 1–2 items with price ≤ 20% of outfit price.
        Pro:
            Re-rank: score = base + 0.2new_arrival + 0.15margin_band + 0.1inventory_pressure - 0.1price_distance_from_budget.
        Advanced:
            If last user click = accessories, increase accessories exposure next turn.

Where to put it in your file

    In chat.py (Router)
        Add StrategyService init near other services.
        Before calling chat_use_case.execute(request):
            Build strategy and attach to request (you may need to extend ChatRequest to have meta/system_directive or strategy).
        After getting response:
            response.replies[0]["message"] = StrategyService.apply_reply_tone(...)
            Optionally add “marketing_explanations” in response for analytics/debug (behind a debug flag).
    In RulesEngine/OutfitRecommender
        Accept optional strategy: Dict[str, Any]
        Use simple weights.

Lightweight data contracts

    Extend ChatRequest (domain/entities) to include:
        session_id: str
        message: str
        meta: Optional[Dict[str, Any]] = {"strategy_override": {...}} // allow runtime override for testing
    Extend ChatResponse:
        replies: List[{type, message}]
        outfits: Optional[List[Outfit]]
        debug: Optional[{strategy, re_rank_factors}] // hidden by default

Low-tech implementation approach (fits your tool constraints)

    No extra infra; keep everything in-process.
    Store strategies in memory per session; resettable via new endpoint:
        POST /v1/chat/sessions/{session_id}/strategy {tone, objectives, guardrails}
    Add a GET /v1/chat/strategy-presets for marketing to choose from.

Preset examples for COS

    Junior:
        “Concise helper”
            Tone: concise, friendly, no emojis, 2–3 sentences, soft CTA.
            Objective: highlight bestsellers.
    Pro:
        “New Arrivals Spotlight”
            Tone: minimalist luxury, no emojis, Thai-first, 2 sentences + soft CTA.
            Objectives: promote_new_arrivals, raise_aov.
    Advanced:
        “Event Promo”
            Tone: energetic, 3–4 sentences, medium CTA, allow one promo mention.
            Objectives: push_event_promo("Mid-Season Sale"), clear_aging_stock(category=X).

Mermaid (request flow with strategy)

mermaid

Copy
graph TD
A[Client] --> B[/POST /v1/chat/]
B --> C{Get/merge strategy}
C --> D[Build system directive]
D --> E[ChatTurn execute (intent+rec)]
E --> F[Re-rank with strategy weights]
F --> G[Tone post-processor]
G --> H[Response + outfits]
B --> I[sessions[ctx] update]

What to test (CLI)

    Set strategy
        curl -X POST http://localhost:8000/v1/chat/sessions/test-session/strategy -d '{"tone":"luxury_concise","objectives":["raise_aov","promote_new_arrivals"],"style":{"max_sentences":3,"cta":"soft","emojis":false},"lang":"th_en"}' -H "Content-Type: application/json"
    Chat
        curl -X POST http://localhost:8000/v1/chat -d '{"session_id":"test-session","message":"Need dinner outfit, budget 2500 THB"}' -H "Content-Type: application/json"
        Expect: concise, Thai/English, soft CTA, accessories only if budget allows.

Junior / Pro / Advanced guidance

    Junior
        Add StrategyService.
        Extend ChatRequest to accept strategy_override.
        Post-process reply to enforce tone and CTA.
    Pro
        Add /strategy endpoints (set/get).
        Bias recommender scoring with strategy weights.
        Add AB bucket in sessions to test tones (A: friendly, B: luxury).
    Advanced
        Track proxy metrics (clicked PDPs per reply, accessory attach rate).
        Feedback loop: if no clicks for 3 turns, reduce upsell strength.
        Time-based presets from marketing calendar (cron to load JSON daily).

Optional: I can review chat.py integration points and sketch minimal code diffs (Python-only skeletons) if you want.
