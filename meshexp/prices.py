"""Published Anthropic API list prices, USD per million tokens (MTok).

Source: https://docs.anthropic.com/en/docs/about-claude/pricing  (checked 3 Nov 2026).
These are used only for *estimates*. Your actual bill is whatever the Claude Console shows.
"""
PRICE_SOURCE = "https://docs.anthropic.com/en/docs/about-claude/pricing (checked 3 Nov 2026)"

# model id: (input, output, cache_read, cache_write_5m)
PRICES_USD_PER_MTOK = {
    "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125),   # prompts up to 100k tokens
    "claude-sonnet-5-5": (2.00, 10.00, 0.10, 2.50),
    "claude-opus-5-5": (4.00, 20.00, 0.20, 5.00),
    "claude-haiku-4-5": (1.00, 5.00, 0.10, 1.25),
    "claude-sonnet-4-6": (3.00, 15.00, 0.30, 3.75),
}

# Indicative mid-market rate on 3 Nov 2026 (GBP/USD ~1.342). Override with --usd-to-gbp.
USD_TO_GBP = 0.745


def price_for(model: str) -> tuple[float, float, float, float]:
    if model not in PRICES_USD_PER_MTOK:
        raise KeyError(f"No price for {model!r}; add it to meshexp/prices.py from the pricing page.")
    return PRICES_USD_PER_MTOK[model]


def cost_usd(model: str, input_tokens: int, output_tokens: int, cache_read: int = 0, cache_write: int = 0) -> float:
    i, o, cr, cw = price_for(model)
    return (input_tokens * i + output_tokens * o + cache_read * cr + cache_write * cw) / 1e6
