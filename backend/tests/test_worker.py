import pytest

from app.worker import cpu_work, run_workload


@pytest.mark.parametrize("workload", ["io_light", "io_heavy", "unreliable"])
async def test_async_workloads_complete_without_failure(workload: str) -> None:
    await run_workload(
        {"workload": workload, "duration_ms": 0, "failure_probability": 0}
    )


async def test_cpu_workload_completes() -> None:
    await run_workload(
        {"workload": "cpu_light", "duration_ms": 1, "failure_probability": 0}
    )


async def test_forced_failure_is_deterministic() -> None:
    with pytest.raises(RuntimeError, match="Simulated workload failure"):
        await run_workload(
            {"workload": "unreliable", "duration_ms": 0, "failure_probability": 1}
        )


def test_cpu_work_handles_minimum_round() -> None:
    assert cpu_work(1) is None
