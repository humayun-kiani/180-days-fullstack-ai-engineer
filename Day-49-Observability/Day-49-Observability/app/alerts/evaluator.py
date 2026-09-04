# app/alerts/evaluator.py
# Alert rule evaluation engine

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class AlertSeverity(Enum):
    PAGE = "page"       # wake someone up
    TICKET = "ticket"   # fix during business hours
    INFO = "info"       # Slack notification only


class AlertState(Enum):
    OK = "ok"
    PENDING = "pending"       # condition true but not long enough
    FIRING = "firing"         # condition true long enough → alert
    RESOLVED = "resolved"     # was firing, now ok


@dataclass
class AlertRule:
    """
    A single alert rule.

    Fires when condition returns True for `for_seconds` consecutive seconds.
    """
    name: str
    description: str
    condition: Callable[[], bool]
    for_seconds: float           # how long condition must be true
    severity: AlertSeverity
    annotations: dict = field(default_factory=dict)

    # Runtime state
    state: AlertState = AlertState.OK
    condition_true_since: Optional[float] = None
    fired_at: Optional[float] = None
    resolved_at: Optional[float] = None
    fire_count: int = 0


class AlertEvaluator:
    """
    Evaluates alert rules and tracks their state.

    In production: send alerts to PagerDuty, OpsGenie, Slack.
    Here: track in memory and expose via API.
    """

    def __init__(self):
        self._rules: list[AlertRule] = []
        self._alert_history: list[dict] = []
        self._last_eval_time: float = 0.0

    def add_rule(self, rule: AlertRule) -> None:
        self._rules.append(rule)

    def evaluate_all(self) -> dict:
        """
        Evaluate all alert rules.
        Call this periodically (e.g., every 15 seconds).
        """
        now = time.time()
        self._last_eval_time = now
        results = []

        for rule in self._rules:
            result = self._evaluate_rule(rule, now)
            results.append(result)

        firing = [r for r in results if r["state"] == "firing"]
        return {
            "evaluated_at": now,
            "total_rules": len(self._rules),
            "firing": len(firing),
            "ok": len([r for r in results if r["state"] == "ok"]),
            "pending": len([r for r in results if r["state"] == "pending"]),
            "rules": results
        }

    def _evaluate_rule(self, rule: AlertRule, now: float) -> dict:
        """Evaluate a single rule and update its state."""
        try:
            condition_met = rule.condition()
        except Exception as e:
            condition_met = False

        if condition_met:
            if rule.condition_true_since is None:
                rule.condition_true_since = now
                rule.state = AlertState.PENDING

            elif (now - rule.condition_true_since) >= rule.for_seconds:
                if rule.state != AlertState.FIRING:
                    rule.state = AlertState.FIRING
                    rule.fired_at = now
                    rule.fire_count += 1
                    self._alert_history.append({
                        "event": "firing",
                        "rule": rule.name,
                        "severity": rule.severity.value,
                        "at": now,
                        "annotations": rule.annotations
                    })
                    self._send_alert(rule)
        else:
            if rule.state == AlertState.FIRING:
                rule.resolved_at = now
                self._alert_history.append({
                    "event": "resolved",
                    "rule": rule.name,
                    "at": now,
                    "duration_seconds": now - (rule.fired_at or now)
                })

            rule.state = AlertState.OK
            rule.condition_true_since = None

        return {
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity.value,
            "state": rule.state.value,
            "condition_true_since": rule.condition_true_since,
            "fire_count": rule.fire_count,
            "annotations": rule.annotations
        }

    def _send_alert(self, rule: AlertRule) -> None:
        """In production: call PagerDuty/Slack API. Here: print."""
        severity_emoji = {"page": "🚨", "ticket": "⚠️", "info": "ℹ️"}
        emoji = severity_emoji.get(rule.severity.value, "⚠️")
        print(
            f"\n  {emoji} ALERT FIRING [{rule.severity.value.upper()}]: {rule.name}\n"
            f"     {rule.description}\n"
            f"     Duration threshold: {rule.for_seconds}s\n"
        )

    def get_firing_alerts(self) -> list[dict]:
        return [
            {
                "name": r.name,
                "severity": r.severity.value,
                "description": r.description,
                "fired_at": r.fired_at,
                "fire_count": r.fire_count,
                "annotations": r.annotations
            }
            for r in self._rules
            if r.state == AlertState.FIRING
        ]

    def get_history(self, limit: int = 20) -> list[dict]:
        return list(reversed(self._alert_history))[:limit]