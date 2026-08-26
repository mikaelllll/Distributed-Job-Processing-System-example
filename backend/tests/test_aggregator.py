from app.aggregator import percentile, reconcile_in_flight_metrics
from app.worker import LATENCY_BUCKETS_MS


def test_reconciles_stale_queue_counter_from_lifecycle_totals() -> None:
    queued, running, retrying, terminal = reconcile_in_flight_metrics(
        {
            "submitted": 10_000,
            "queued": 15,
            "running": 0,
            "retrying": 0,
            "completed": 10_000,
            "failed": 0,
        }
    )

    assert (queued, running, retrying, terminal) == (0, 0, 0, 10_000)


def test_accounts_for_running_and_retrying_jobs() -> None:
    queued, running, retrying, terminal = reconcile_in_flight_metrics(
        {
            "submitted": 100,
            "queued": 99,
            "running": 4,
            "retrying": 3,
            "completed": 80,
            "failed": 2,
            "cancelled": 1,
        }
    )

    assert (queued, running, retrying, terminal) == (13, 4, 3, 83)


def test_reconciliation_clamps_corrupt_negative_gauges() -> None:
    result = reconcile_in_flight_metrics(
        {"submitted": 10, "completed": 10, "running": -2, "retrying": -3}
    )
    assert result == (0, 0, 0, 10)


def test_percentiles_use_cumulative_latency_buckets() -> None:
    buckets = {str(bucket): 0 for bucket in LATENCY_BUCKETS_MS}
    buckets.update({"25": 50, "100": 95, "500": 100})
    assert percentile(buckets, 100, 0.50) == 25
    assert percentile(buckets, 100, 0.95) == 100
    assert percentile(buckets, 100, 0.99) == 500


def test_percentile_falls_back_to_largest_bucket() -> None:
    assert percentile({}, 1, 0.99) == LATENCY_BUCKETS_MS[-1]
