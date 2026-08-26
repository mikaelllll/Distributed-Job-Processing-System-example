from app.aggregator import reconcile_in_flight_metrics


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

    assert (queued, running, retrying, terminal) == (10, 4, 3, 83)
