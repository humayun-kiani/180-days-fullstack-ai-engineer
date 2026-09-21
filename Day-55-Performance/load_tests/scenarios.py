# load_tests/scenarios.py
# Named load test scenarios — run different scenarios for different goals

SCENARIOS = {
    "smoke": {
        "description": "Smoke test — 1 user, verify nothing breaks",
        "users": 1,
        "spawn_rate": 1,
        "duration": "30s",
        "command": "locust -f locustfile.py --headless --users 1 --spawn-rate 1 --run-time 30s"
    },
    "load": {
        "description": "Normal load — 20 concurrent users",
        "users": 20,
        "spawn_rate": 2,
        "duration": "60s",
        "command": "locust -f locustfile.py --headless --users 20 --spawn-rate 2 --run-time 60s"
    },
    "stress": {
        "description": "Stress test — find breaking point",
        "users": 100,
        "spawn_rate": 10,
        "duration": "120s",
        "command": "locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 120s"
    },
    "spike": {
        "description": "Spike test — sudden burst of users",
        "users": 50,
        "spawn_rate": 50,  # all at once
        "duration": "30s",
        "command": "locust -f locustfile.py --headless --users 50 --spawn-rate 50 --run-time 30s"
    }
}

# Target metrics for TaskMind:
PERFORMANCE_TARGETS = {
    "p50_ms": 50,     # 50% of requests under 50ms
    "p95_ms": 200,    # 95% of requests under 200ms
    "p99_ms": 500,    # 99% of requests under 500ms
    "error_rate": 0.001,  # < 0.1% errors
    "min_rps": 100    # handle at least 100 requests/second
}

if __name__ == "__main__":
    import json
    print("TaskMind Load Test Scenarios:\n")
    for name, scenario in SCENARIOS.items():
        print(f"  {name.upper()}: {scenario['description']}")
        print(f"    {scenario['command']}")
        print()
    print("Performance Targets:")
    print(json.dumps(PERFORMANCE_TARGETS, indent=2))