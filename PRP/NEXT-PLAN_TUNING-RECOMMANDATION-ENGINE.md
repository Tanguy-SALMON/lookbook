Scoring weights walkthrough and tuning ideas

Below is a practical way to think about the current relevance dimensions and how to tune them. I’ll assume a representative baseline similar to what you documented (e.g., Color ≈ 25, Occasion ≈ 20, Style ≈ 15, plus other factors). Adjust exact numbers to match your code.
1) Typical scoring dimensions and why they matter

    Occasion/Activity match (intent fit): Ensures items are context-appropriate (party, yoga, business). Usually top-2 most important.
    Category fit: Makes sure we pick the right garment types (tops/bottoms/shoes) for an outfit. Critical to avoid mismatched results.
    Color harmony: Influences cohesion within an outfit and user preferences (e.g., “I want black”). High, but subordinate to intent/category.
    Style/aesthetic: Aligns with user tone (minimalist, sporty, elegant). Medium to high.
    Material/fabric: Matters for comfort/performance (yoga → stretch, business → wool/cotton blends). Medium.
    Formality level: Prevents mismatches (elevated vs casual). Medium to high.
    Seasonality/climate: If available, boosts relevance (hot weather → linen, cold → wool). Medium.
    Price/budget: If inferred or specified, weight should rise significantly. Variable.
    Availability/stock/size: Practical constraints; heavily negative if unavailable. Hard constraint or large penalty.
    Popularity/CTR: Behavioral signal that improves ranking robustness. Medium.
    Newness/recency: Helps freshness; small/medium.
    Brand constraints (if relevant): If user/merchant has brand preferences. Low to medium.

2) Suggested initial weight ranges (sum ≈ 100)

    Occasion/Activity: 20–25
    Category fit: 18–22
    Formality: 10–15
    Style: 10–15
    Color: 8–12
    Material/Fabric: 6–10
    Seasonality/Climate: 5–8
    Popularity/CTR: 4–8
    Newness: 2–5
    Price/Budget alignment: 0–25 (adaptive; see below)
    Availability/Size: Hard filter or -∞ penalty (don’t show if not purchasable)

Notes:

    Category fit should be closer to Occasion; it’s foundational.
    Color should not overpower intent/formality/category.
    Price/Budget is adaptive: when a budget is present, elevate its weight; otherwise keep it low.

3) Adaptive weighting strategy (context-aware tuning)

    If user states budget or “cheap/affordable/premium” intent:
        Increase Price/Budget weight to 18–25.
        Slightly reduce Color/Newness/Popularity to make room.
    If user emphasizes “color” (“all black”, “earth tones”):
        Increase Color weight to 15–20.
        Reduce Newness/Popularity/Seasonality a bit.
    If activity is performance-based (yoga/running):
        Increase Material to 12–18 and Style to sporty; reduce Newness.
    If formal event (wedding, gala):
        Raise Formality 15–20, Style to elegant; Color moderate; Material moderate (silk/wool blends).
    If the request is abstract (“I need something nice”):
        Default to generalist: Occasion 18, Category 20, Style 14, Formality 12, Popularity 8.

Implement by computing intent signals from the parser and mapping to a weight profile (a small ruleset or learned model mapping).
4) Intra-outfit cohesion vs. item-level relevance

    Current approach likely scores per-item then assembles outfits.
    Add outfit-level cohesion bonus:
        Color harmony score across items (+0–10).
        Style coherence across items (+0–8).
        Occasion/formality consistency across items (+0–8).
    Net effect: Avoids high-scoring but stylistically clashing item sets.

5) Negative signals and penalties

    Strong penalties for:
        Out-of-stock or missing size (-∞ or filter out).
        Hard rule conflicts (e.g., “no leather” in request; materials list includes leather) (-30 to -∞).
        Duplicated categories when the outfit expects diversity (e.g., two tops, no bottoms) (-10 to -20).
    Mild penalties for:
        Slight color clashes (-3 to -6).
        Slight over-budget when no budget is specified (-2 to -4).
        Very old products if freshness matters (-2 to -5).

6) Practical numeric example (party/dancing request)

    Occasion/Activity: 23
    Category: 20
    Formality: 12
    Style (party/elevated): 12
    Color (dark/metallics): 10
    Material (stretch/comfort): 8
    Popularity: 6
    Newness: 4
    Seasonality: 5
    Total: 100 baseline
    Outfit-level cohesion bonus: up to +20 (color/style/formality harmony)
    Availability: hard filter
    If user adds “budget 3,000 THB”, reallocate ~12–18 points to Price/Budget, subtract from Newness/Popularity/Color.

7) Data-driven tuning loop

    Set up offline evaluation:
        Create labeled scenarios (queries, preferred items/outfits from merchandisers).
        Compute NDCG@k / MRR / Precision@k on ranking.
    Online A/B testing:
        Compare baseline vs. adjusted weights for conversion rate, CTR on suggested items, add-to-cart rate.
    Auto-tuning:
        Use Bayesian optimization or coordinate ascent on weights with offline metrics as objective.
        Periodically refresh weights using most recent engagement data.

8) Robustness for LLM keyword variability

    Cap per-dimension contribution to avoid runaway scores from noisy keyword explosions.
    Normalize each dimension to [0, 1] before applying weights.
    Use sigmoid or clipped linear scoring for text-match sub-scores.

9) Cold-start and sparsity considerations

    If product lacks certain attributes (e.g., style), reduce that dimension’s weight proportionally to attribute coverage to avoid penalizing due to missing data.
    Backfill missing attributes via vision model predictions; track confidence and scale contribution by confidence.

10) Transparency and debugging

    Return a score breakdown per item/outfit (dimension → contribution).
    Log top-5 factors that led to selection to help merchandisers iterate rules.

11) Quick actions you can implement now

    Add an adaptive weight layer that:
        Detects budget → raises Price weight.
        Detects strong color intent → raises Color weight.
        Detects performance activity → raises Material/Comfort weight.
    Introduce outfit-level cohesion bonus.
    Enforce hard availability filter and stricter penalties for rule violations.
    Normalize and cap dimension scores; scale contributions by attribute confidence.
    Start a small offline evaluation set and run a grid search over a few weight profiles.

If you share your current exact weights and a couple of mis-ranking examples, I can propose a concrete revised weight vector and the specific penalty/bonus rules to fix those cases.
