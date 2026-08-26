import uuid

import pytest

from app import generator


class FakeRedis:
    def __init__(self, values: dict[str, int], control: str | None = None) -> None:
        self.values = values
        self.control = control

    async def hget(self, _: str, field: str) -> int | None:
        return self.values.get(field)

    async def get(self, _: str) -> str | None:
        return self.control

    async def hincrby(self, _: str, field: str, amount: int) -> None:
        self.values[field] = self.values.get(field, 0) + amount


async def no_sleep(_: float) -> None:
    return None


def test_job_ids_are_stable_and_unique_per_index() -> None:
    run_id = uuid.uuid4()
    assert generator.job_id_for(run_id, 10) == generator.job_id_for(run_id, 10)
    assert generator.job_id_for(run_id, 10) != generator.job_id_for(run_id, 11)


async def test_simulation_resumes_from_existing_progress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {"submitted": 400_000, "completed": 396_000, "failed": 4_000}
    redis = FakeRedis(values)
    monkeypatch.setattr(generator.asyncio, "sleep", no_sleep)  # type: ignore[attr-defined]

    await generator._simulate(
        str(uuid.uuid4()),
        {"job_count": 1_000_000, "failure_probability": 0.01},
        redis,
    )

    assert values == {"submitted": 1_000_000, "completed": 990_000, "failed": 10_000}


async def test_cancelled_simulation_does_not_add_progress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {"submitted": 10, "completed": 10, "failed": 0}
    redis = FakeRedis(values, control="cancelled")
    monkeypatch.setattr(generator.asyncio, "sleep", no_sleep)  # type: ignore[attr-defined]

    await generator._simulate(
        str(uuid.uuid4()),
        {"job_count": 100, "failure_probability": 0},
        redis,
    )

    assert values == {"submitted": 10, "completed": 10, "failed": 0}
