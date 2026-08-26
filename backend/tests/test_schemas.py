import pytest
from pydantic import ValidationError

from app.models import RunMode
from app.schemas import BenchmarkCreate


def test_regular_benchmark_configuration() -> None:
    benchmark = BenchmarkCreate(name="Load test", job_count=10_000)
    assert benchmark.mode == RunMode.benchmark
    assert benchmark.max_retries == 3


def test_large_real_run_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BenchmarkCreate(name="Too large", job_count=100_000_000, mode=RunMode.benchmark)


def test_large_simulation_is_allowed() -> None:
    benchmark = BenchmarkCreate(
        name="Simulation", job_count=100_000_000, mode=RunMode.simulation
    )
    assert benchmark.job_count == 100_000_000


def test_small_simulation_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BenchmarkCreate(
            name="Misleading simulation", job_count=100_000, mode=RunMode.simulation
        )


@pytest.mark.parametrize("mode", [RunMode.audit, RunMode.benchmark])
def test_real_modes_accept_public_limit(mode: RunMode) -> None:
    benchmark = BenchmarkCreate(name="Boundary", job_count=1_000_000, mode=mode)
    assert benchmark.job_count == 1_000_000


@pytest.mark.parametrize("workload", ["io_light", "io_heavy", "cpu_light", "unreliable"])
def test_all_workloads_are_accepted(workload: str) -> None:
    assert BenchmarkCreate(name="Workload", job_count=1, workload=workload).workload == workload


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("job_count", 0),
        ("producer_concurrency", 0),
        ("producer_concurrency", 501),
        ("target_rate", 0),
        ("duration_ms", -1),
        ("duration_ms", 60_001),
        ("failure_probability", -0.1),
        ("failure_probability", 1.1),
        ("max_retries", -1),
        ("max_retries", 11),
    ],
)
def test_numeric_boundaries_are_rejected(field: str, value: int | float) -> None:
    payload = {"name": "Invalid", "job_count": 1, field: value}
    with pytest.raises(ValidationError):
        BenchmarkCreate(**payload)
