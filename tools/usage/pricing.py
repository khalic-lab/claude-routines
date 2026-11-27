#!/usr/bin/env python3
"""List-price table for measured token usage, and cost(record_models) -> dict.

The subscription pays the real bill; this reports the COMPARABLE number -- what the
same tokens would cost at the public Claude API list price -- labelled as such with a
`pricing_as_of` date so a stale table is visible rather than silently wrong.

Prices are USD per MILLION tokens, taken verbatim (never from memory) from the official
Anthropic pricing page, last checked 2026-11-28:
  https://platform.claude.com/docs/en/about-claude/pricing  (Model pricing + Prompt caching)

Cache columns follow the published multipliers relative to base input: 5m write = 1.25x,
1h write = 2x, cache read = 0.1x -- EXCEPT where the page names a lower cache-read rate:
0.025x on Claude Fable 5.2 and 5.1 ($0.20 and $0.25/MTok), 0.05x on Claude Opus 5.5 and
Claude Sonnet 5.5 ($0.20 and $0.10/MTok). Claude Fable 5 keeps the 0.1x default ($1.00).

Claude Haiku 5.5 is priced by prompt length: a REQUEST whose prompt (input + cache reads +
cache writes) is over 100,000 tokens pays a higher row, each request on its own. A record's
per-model totals cannot tell the two apart, so transcript.parse files such a request's tokens
under `usage_key()` -- the model id + LONG_PROMPT_SUFFIX -- and that key has its own row here.

An unknown model id costs null and lands in `missing_models`; known models still sum, so a
new model never zeroes a run's whole cost -- only its own slice. A dated snapshot id
(`claude-haiku-4-5-20251001`) falls back to its dateless row when it has none of its own.
Records keep the cost computed when they were written; a price change here does not
rewrite index/usage.
"""

import re

PRICING_AS_OF = "2026-11-28"

# model id -> USD / MTok for each token class. Keys match the record's per-model token keys.
PRICING = {
    # Opus tier ($5 / $25) -- the model the routines run heaviest on today.
    "claude-opus-4-8": {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.50},
    "claude-opus-4-7": {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.50},
    "claude-opus-5":   {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.50},
    # Opus 5.5 is cheaper than the rest of the Opus tier ($4 / $20).
    "claude-opus-5-5": {"input": 4.0, "output": 20.0, "cache_write_5m": 5.00, "cache_write_1h": 8.0, "cache_read": 0.20},
    # Sonnet tier. Sonnet 5.5 is priced like Sonnet 5 except its cache read (0.05x, $0.10).
    "claude-sonnet-5-5": {"input": 2.0, "output": 10.0, "cache_write_5m": 2.50, "cache_write_1h": 4.0, "cache_read": 0.10},
    "claude-sonnet-5":   {"input": 2.0, "output": 10.0, "cache_write_5m": 2.50, "cache_write_1h": 4.0, "cache_read": 0.20},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_write_5m": 3.75, "cache_write_1h": 6.0, "cache_read": 0.30},
    # Haiku 5.5 -- Watch's model since 2026-11-28. Two rows: prompts up to 100K tokens, and
    # the higher row for a request whose prompt is over 100K (see usage_key()).
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_write_5m": 0.125, "cache_write_1h": 0.20, "cache_read": 0.01},
    "claude-haiku-5-5 (long prompt)": {"input": 0.50, "output": 2.50, "cache_write_5m": 0.625, "cache_write_1h": 1.0, "cache_read": 0.05},
    # Haiku 4.5 -- Watch's model through 2026-10-04.
    # The transcript's message.model is the pinned snapshot id; the dateless alias is the
    # same model at the same price, so both keys resolve rather than one falling to null.
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0, "cache_write_5m": 1.25, "cache_write_1h": 2.0, "cache_read": 0.10},
    "claude-haiku-4-5":          {"input": 1.0, "output": 5.0, "cache_write_5m": 1.25, "cache_write_1h": 2.0, "cache_read": 0.10},
    # Fable tier -- for local Mac transcripts measured through this same parser. Fable 5.2 and
    # 5.1 read cache at 0.025x base input ($0.20 / $0.25); Fable 5 keeps the 0.1x default ($1.00).
    "claude-fable-5-2": {"input": 8.0, "output": 40.0, "cache_write_5m": 10.0, "cache_write_1h": 16.0, "cache_read": 0.20},
    "claude-fable-5-1": {"input": 10.0, "output": 50.0, "cache_write_5m": 12.50, "cache_write_1h": 20.0, "cache_read": 0.25},
    "claude-fable-5":   {"input": 10.0, "output": 50.0, "cache_write_5m": 12.50, "cache_write_1h": 20.0, "cache_read": 1.00},
}

# Models priced by prompt length -> the prompt size (tokens) a request must EXCEED to pay the
# long-prompt row, which PRICING carries under `<id>` + LONG_PROMPT_SUFFIX.
LONG_PROMPT_SUFFIX = " (long prompt)"
LONG_PROMPT_THRESHOLD = {"claude-haiku-5-5": 100_000}

_DATED = re.compile(r"-\d{8}$")


def base_id(model):
    """`claude-haiku-4-5-20251001` -> `claude-haiku-4-5`; any other id unchanged."""
    return _DATED.sub("", model) if isinstance(model, str) else model


def usage_key(model, prompt_tokens):
    """The `models` key one request's tokens are recorded under: the model id, or -- for a
    model priced by prompt length whose request prompt is over the threshold -- the id plus
    LONG_PROMPT_SUFFIX. `prompt_tokens` = input + cache reads + cache writes of that request."""
    threshold = LONG_PROMPT_THRESHOLD.get(base_id(model))
    if threshold is not None and prompt_tokens > threshold:
        return model + LONG_PROMPT_SUFFIX
    return model


def price_for(key):
    """PRICING row for a `models` key: exact match, else the dateless id (keeping any
    long-prompt suffix), else None."""
    price = PRICING.get(key)
    if price is None and isinstance(key, str):
        suffix = LONG_PROMPT_SUFFIX if key.endswith(LONG_PROMPT_SUFFIX) else ""
        core = key[: -len(suffix)] if suffix else key
        price = PRICING.get(base_id(core) + suffix)
    return price


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
        price = price_for(model)
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
