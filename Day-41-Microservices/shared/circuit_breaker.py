# ============================================================
# shared/circuit_breaker.py
# Circuit breaker for service-to-service calls
# ============================================================

import time
from enum import Enum
from dataclasses import dataclass, field


class CircuitState(Enum):
    CLOSED = "closed"        # Normal — calls go through
    OPEN = "open"            # Tripped — calls blocked
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    State transitions:
      CLOSED → (N failures in window) → OPEN
      OPEN → (timeout elapsed) → HALF_OPEN
      HALF_OPEN → (M successes) → CLOSED
      HALF_OPEN → (any failure) → OPEN
    """
    service_name: str
    failure_threshold: int = 5
    timeout_seconds: float = 30.0
    success_threshold: int = 2

    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failures: int = field(default=0, init=False)
    _successes: int = field(default=0, init=False)
    _last_failure: float = field(default=0.0, init=False)

    def is_open(self) -> bool:
        """Return True if circuit is open (calls should be blocked)."""
        if self.state == CircuitState.OPEN:
            if time.time() - self._last_failure >= self.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self._successes = 0
                return False    # Allow test call
            return True
        return False

    def on_success(self):
        self._failures = 0
        if self.state == CircuitState.HALF_OPEN:
            self._successes += 1
            if self._successes >= self.success_threshold:
                self.state = CircuitState.CLOSED

    def on_failure(self):
        self._failures += 1
        self._last_failure = time.time()
        if self._failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def status(self) -> dict:
        return {
            "service": self.service_name,
            "state": self.state.value,
            "failures": self._failures,
            "failure_threshold": self.failure_threshold
        }


# Global circuit breakers for each service dependency
AUTH_CIRCUIT = CircuitBreaker("auth-service")
AI_CIRCUIT = CircuitBreaker("ai-service")