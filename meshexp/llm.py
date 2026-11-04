"""Thin wrapper over the Anthropic Messages API with usage and cost tracking.

The API key is read from the ANTHROPIC_API_KEY environment variable by the SDK. It is never
passed, stored or logged by this code.
"""
from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass, field

from .prices import cost_usd


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class CostTracker:
    cap_usd: float | None = None
    spent_usd: float = 0.0
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, model: str, usage) -> float:
        tin = getattr(usage, "input_tokens", 0) or 0
        tout = getattr(usage, "output_tokens", 0) or 0
        cr = getattr(usage, "cache_read_input_tokens", 0) or 0
        cw = getattr(usage, "cache_creation_input_tokens", 0) or 0
        c = cost_usd(model, tin, tout, cr, cw)
        with self._lock:
            self.spent_usd += c
            self.calls += 1
            self.tokens_in += tin + cr + cw
            self.tokens_out += tout
        return c

    def check(self) -> None:
        if self.cap_usd is not None and self.spent_usd >= self.cap_usd:
            raise BudgetExceeded(f"Spend cap reached: ~${self.spent_usd:.2f} >= ${self.cap_usd:.2f}")


class LLM:
    def __init__(self, model: str, effort: str | None, max_tokens: int, tracker: CostTracker):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise SystemExit("ANTHROPIC_API_KEY is not set. Export it in your shell (never commit it), or use --mode mock.")
        import anthropic  # imported lazily so mock mode needs no SDK configuration
        self.client = anthropic.Anthropic(max_retries=6)
        self.model, self.effort, self.max_tokens, self.tracker = model, effort, max_tokens, tracker

    def create(self, system: str, messages: list, tools: list | None = None, json_schema: dict | None = None):
        self.tracker.check()
        kw = dict(model=self.model, max_tokens=self.max_tokens, system=system, messages=messages)
        cfg = {}
        if self.effort:
            cfg["effort"] = self.effort
        if json_schema:
            cfg["format"] = {"type": "json_schema", "schema": json_schema}
        if cfg:
            kw["output_config"] = cfg
        if tools:
            kw["tools"] = tools
        resp = self.client.messages.create(**kw)
        cost = self.tracker.add(self.model, resp.usage)
        usage = {"model": self.model, "input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens,
                 "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
                 "cost_usd_est": round(cost, 6)}
        return resp, usage


def parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {}


def response_text(resp) -> str:
    return "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
