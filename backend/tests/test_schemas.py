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
    benchmark = BenchmarkCreate(name="Simulation", job_count=100_000_000, mode=RunMode.simulation)
    assert benchmark.job_count == 100_000_000
