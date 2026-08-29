# ============================================================
# app/calculator.py
# Back-of-envelope capacity estimation calculator
# ============================================================


def estimate_capacity(
    users: int,
    daily_active_rate: float = 0.1,
    writes_per_dau: float = 1.0,
    reads_per_dau: float = 10.0,
    bytes_per_write: int = 1000,
    retention_years: int = 5
) -> dict:
    """
    Back-of-envelope capacity estimation.

    Args:
        users: Total registered users
        daily_active_rate: Fraction of users active daily (0.1 = 10%)
        writes_per_dau: Average writes per daily active user
        reads_per_dau: Average reads per daily active user
        bytes_per_write: Average size of one write (bytes)
        retention_years: How long to keep data
    """
    dau = int(users * daily_active_rate)
    daily_writes = int(dau * writes_per_dau)
    daily_reads = int(dau * reads_per_dau)

    # QPS (queries per second)
    seconds_per_day = 86_400
    avg_write_qps = daily_writes / seconds_per_day
    avg_read_qps = daily_reads / seconds_per_day
    peak_write_qps = avg_write_qps * 3    # assume 3x peak
    peak_read_qps = avg_read_qps * 3

    # Storage
    bytes_per_day = daily_writes * bytes_per_write
    bytes_total = bytes_per_day * 365 * retention_years

    # Bandwidth
    write_bandwidth_bps = avg_write_qps * bytes_per_write
    read_bandwidth_bps = avg_read_qps * bytes_per_write    # approximate

    def human_bytes(b: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} PB"

    def human_num(n: float) -> str:
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f}B"
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(int(n))

    # Infrastructure recommendations
    infra = []
    if peak_write_qps > 10000:
        infra.append("Sharding required (write QPS > 10K)")
    elif peak_write_qps > 5000:
        infra.append("Multiple write DB instances needed")
    else:
        infra.append("Single primary DB sufficient for writes")

    if peak_read_qps > 100000:
        infra.append("CDN required (read QPS > 100K)")
    if peak_read_qps > 10000:
        infra.append("Redis caching required (read QPS > 10K)")
    if peak_read_qps > 5000:
        infra.append("Read replicas required (read QPS > 5K)")

    if bytes_total > 10 * 1024**4:    # > 10 TB
        infra.append("Object storage (S3) needed for data")
    if bytes_total > 1 * 1024**4:    # > 1 TB
        infra.append("Consider data archival strategy")

    api_servers = max(1, int(peak_read_qps / 5000))    # ~5K req/server
    cache_servers = max(0, int(peak_read_qps / 100000)) if peak_read_qps > 10000 else 0

    return {
        "users": {
            "total": human_num(users),
            "dau": human_num(dau),
            "dau_rate": f"{daily_active_rate*100:.0f}%"
        },
        "traffic": {
            "daily_writes": human_num(daily_writes),
            "daily_reads": human_num(daily_reads),
            "avg_write_qps": round(avg_write_qps, 1),
            "avg_read_qps": round(avg_read_qps, 1),
            "peak_write_qps": round(peak_write_qps, 1),
            "peak_read_qps": round(peak_read_qps, 1),
            "read_write_ratio": f"{reads_per_dau/writes_per_dau:.0f}:1"
        },
        "storage": {
            "per_write": human_bytes(bytes_per_write),
            "per_day": human_bytes(bytes_per_day),
            "per_year": human_bytes(bytes_per_day * 365),
            "total_retention": human_bytes(bytes_total)
        },
        "bandwidth": {
            "write_inbound": f"{human_bytes(write_bandwidth_bps)}/s",
            "read_outbound": f"{human_bytes(read_bandwidth_bps)}/s"
        },
        "infrastructure_needs": infra,
        "estimated_servers": {
            "api_servers": f"{api_servers}+ API servers",
            "cache_servers": f"{cache_servers}+ Redis nodes" if cache_servers else "Single Redis instance",
            "db_read_replicas": f"{max(1, int(peak_read_qps/5000))} read replicas" if peak_read_qps > 5000 else "Single DB"
        }
    }


def estimate_latency_budget(
    target_p99_ms: float = 200.0
) -> dict:
    """Break down a latency budget across components."""
    # Rough breakdown for a typical web request
    network_ms = min(target_p99_ms * 0.1, 20)     # network round trip
    load_balancer_ms = 1.0
    api_processing_ms = target_p99_ms * 0.15
    cache_lookup_ms = min(target_p99_ms * 0.05, 5)
    db_query_ms = target_p99_ms * 0.5
    response_serialize_ms = target_p99_ms * 0.05
    remaining = target_p99_ms - (
        network_ms + load_balancer_ms + api_processing_ms +
        cache_lookup_ms + db_query_ms + response_serialize_ms
    )

    return {
        "target_p99_ms": target_p99_ms,
        "breakdown": {
            "network_roundtrip": f"{network_ms:.1f}ms",
            "load_balancer": f"{load_balancer_ms:.1f}ms",
            "api_processing": f"{api_processing_ms:.1f}ms",
            "cache_lookup": f"{cache_lookup_ms:.1f}ms",
            "db_query_budget": f"{db_query_ms:.1f}ms",
            "serialization": f"{response_serialize_ms:.1f}ms",
            "buffer": f"{remaining:.1f}ms"
        },
        "recommendations": [
            f"DB query must complete in < {db_query_ms:.0f}ms",
            "Add cache if DB query > budget",
            f"Cache hit should save {db_query_ms:.0f}ms → total response < {target_p99_ms - db_query_ms:.0f}ms"
        ]
    }