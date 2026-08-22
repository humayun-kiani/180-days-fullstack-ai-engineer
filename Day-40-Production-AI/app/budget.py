# ============================================================
# app/budget.py
# Token budget tracking and enforcement
# ============================================================

import os
import time
from collections import defaultdict
from datetime import date


class TokenBudget:
    """Track and enforce token usage budgets."""

    def __init__(self):
        self.daily_limit = int(os.environ.get("DAILY_TOKEN_BUDGET", 500_000))
        self.per_user_hourly = int(os.environ.get("PER_USER_HOURLY_TOKENS", 5_000))
        self.per_request_max = 4_000

        self._daily_used = 0
        self._daily_date = date.today()
        self._user_used: dict[str, int] = defaultdict(int)
        self._user_hour: dict[str, int] = defaultdict(lambda: -1)

    def _reset_if_new_day(self):
        today = date.today()
        if today != self._daily_date:
            self._daily_used = 0
            self._daily_date = today

    def check(self, user_id: str, estimated_tokens: int) -> dict:
        """Return {"allowed": bool, "reason": str | None}."""
        self._reset_if_new_day()

        if estimated_tokens > self.per_request_max:
            return {"allowed": False, "reason": "request_too_large",
                    "limit": self.per_request_max, "requested": estimated_tokens}

        if self._daily_used + estimated_tokens > self.daily_limit:
            return {"allowed": False, "reason": "daily_budget_exceeded",
                    "daily_used": self._daily_used, "daily_limit": self.daily_limit}

        current_hour = int(time.time() // 3600)
        if self._user_hour[user_id] != current_hour:
            self._user_used[user_id] = 0
            self._user_hour[user_id] = current_hour

        if self._user_used[user_id] + estimated_tokens > self.per_user_hourly:
            return {"allowed": False, "reason": "user_hourly_exceeded",
                    "user_used": self._user_used[user_id],
                    "user_limit": self.per_user_hourly}

        return {"allowed": True}

    def record(self, user_id: str, tokens: int):
        self._reset_if_new_day()
        self._daily_used += tokens
        self._user_used[user_id] += tokens

    def stats(self) -> dict:
        return {
            "daily_used": self._daily_used,
            "daily_limit": self.daily_limit,
            "daily_remaining": self.daily_limit - self._daily_used,
            "daily_pct_used": round(self._daily_used / self.daily_limit * 100, 1),
            "est_daily_cost_usd": round(self._daily_used / 1000 * 0.003, 4)
        }