#!/usr/bin/env python3
"""List-price table for measured token usage, and cost(record_models) -> dict.

The subscription pays the real bill; this reports the COMPARABLE number -- what the
same tokens would cost at the public Claude API list price -- labelled as such with a
`pricing_as_of` date so a stale table is visible rather than silently wrong.

Prices are USD per MILLION tokens, taken verbatim (never from memory) from the official
Anthropic pricing page on 2026-09-13:
  https://platform.claude.com/docs/en/about-claude/pricing  (Model pricing + Prompt caching)

Cache columns follow the published multipliers relative to base input: 5m write = 1.25x,
1h write = 2x, cache read = 0.1x -- EXCEPT where the page names a lower cache-read rate.
Claude Fable 5.1's cache read is 0.025x base ($0.25/MTok, an addition over Fable 5); Claude
Fable 5 keeps the 0.1x default ($1.00/MTok). That is the only per-model deviation below.

An unknown model id costs null and lands in `missing_models`; known models still sum, so a
new model never zeroes a run's whole cost -- only its own slice.
"""

PRICING_AS_OF = "2026-09-13"

# model id -> USD / MTok for each token class. Keys match the record's per-model token keys.
PRICING = {
    # Opus tier ($5 / $25) -- the model the routines run heaviest on today.
    "claude-opus-4-8": {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.50},
    "claude-opus-4-7": {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.50},
    "claude-opus-5":   {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.50},
    # Sonnet tier.
    "claude-sonnet-5":   {"input": 2.0, "output": 10.0, "cache_write_5m": 2.50, "cache_write_1h": 4.0, "cache_read": 0.20},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_write_5m": 3.75, "cache_write_1h": 6.0, "cache_read": 0.30},
    # Haiku -- the second model the routines run on (Watch, and Haiku-tier writers).
    # The transcript's message.model is the pinned snapshot id; the dateless alias is the
    # same model at the same price, so both keys resolve rather than one falling to null.
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0, "cache_write_5m": 1.25, "cache_write_1h": 2.0, "cache_read": 0.10},
    "claude-haiku-4-5":          {"input": 1.0, "output": 5.0, "cache_write_5m": 1.25, "cache_write_1h": 2.0, "cache_read": 0.10},
    # Fable tier -- for local Mac transcripts measured through this same parser. Fable 5.1's
    # cache read is 0.025x base input ($0.25/MTok); Fable 5 keeps the 0.1x default ($1.00).
    "claude-fable-5-1": {"input": 10.0, "output": 50.0, "cache_write_5m": 12.50, "cache_write_1h": 20.0, "cache_read": 0.25},
    "claude-fable-5":   {"input": 10.0, "output": 50.0, "cache_write_5m": 12.50, "cache_write_1h": 20.0, "cache_read": 1.00},
}


def cost(record_models):
    """Cost a record's `models` map at list price.

    `record_models`: {model_id: {input, cache_write_5m, cache_write_1h, cache_read, output, ...}}
    (extra keys such as `messages` are ignored). Returns the record's `cost_usd_list` block:
    {total, by_model: {id: usd|None}, pricing_as_of, missing_models: [ids]}.
    """
    by_model = {}
    missing = []
    total = 0.0
    for model, toks in (record_models or {}).items():
        price = PRICING.get(model)
        if price is None:
            by_model[model] = None
            missing.append(model)
            continue
        usd = (
            toks.get("input", 0) * price["input"]
            + toks.get("cache_write_5m", 0) * price["cache_write_5m"]
            + toks.get("cache_write_1h", 0) * price["cache_write_1h"]
            + toks.get("cache_read", 0) * price["cache_read"]
            + toks.get("output", 0) * price["output"]
        ) / 1_000_000.0
        # round to the cent floor of what we report; keep full precision in `total`.
        by_model[model] = round(usd, 6)
        total += usd
    return {
        "total": round(total, 6),
        "by_model": by_model,
        "pricing_as_of": PRICING_AS_OF,
        "missing_models": missing,
    }
