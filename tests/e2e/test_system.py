from __future__ import annotations

import time
from collections.abc import Iterator

import httpx
import pytest

API = "http://127.0.0.1:8000"
FRONTEND = "http://127.0.0.1:3000"


@pytest.fixture(scope="session")
def client() -> Iterator[httpx.Client]:
    with httpx.Client(base_url=API, timeout=10) as value:
        yield value


@pytest.fixture
def created_runs(client: httpx.Client) -> Iterator[list[str]]:
    run_ids: list[str] = []
    yield run_ids
    for run_id in run_ids:
        response = client.delete(f"/api/v1/runs/{run_id}")
        assert response.status_code in {204, 404}


def create_run(
    client: httpx.Client,
    created_runs: list[str],
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "E2E benchmark",
        "job_count": 20,
        "mode": "benchmark",
        "producer_concurrency": 5,
        "target_rate": 1_000,
        "workload": "io_light",
        "duration_ms": 1,
        "failure_probability": 0,
        "max_retries": 2,
    }
    payload.update(overrides)
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 201, response.text
    run = response.json()
    created_runs.append(run["id"])
    return run


def wait_for_status(
    client: httpx.Client,
    run_id: str,
    expected: set[str],
    timeout: float = 60,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    last: dict[str, object] = {}
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/runs/{run_id}")
        assert response.status_code == 200, response.text
        last = response.json()
        if last["status"] in expected:
            return last
        time.sleep(0.25)
    pytest.fail(f"Run {run_id} did not reach {expected}; last response: {last}")


def assert_exact_accounting(run: dict[str, object]) -> None:
    metrics = run["final_metrics"]
    assert isinstance(metrics, dict)
    assert metrics["completed"] + metrics["failed"] == run["job_count"]
    assert metrics["queued"] == 0
    assert metrics["running"] == 0
    assert metrics["retrying"] == 0
    assert metrics["stream_finished"] == 1


def test_health_frontend_and_observability(client: httpx.Client) -> None:
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {
        "status": "ok",
        "checks": {"postgres": True, "redis": True},
    }
    assert client.get("/health/live").json() == {"status": "ok"}
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "# HELP" in metrics.text
    frontend = httpx.get(FRONTEND, timeout=10)
    assert frontend.status_code == 200
    assert "Distributed Job Observatory" in frontend.text


@pytest.mark.parametrize("mode", ["audit", "benchmark"])
@pytest.mark.parametrize("workload", ["io_light", "io_heavy", "cpu_light"])
def test_real_execution_matrix(
    client: httpx.Client,
    created_runs: list[str],
    mode: str,
    workload: str,
) -> None:
    run = create_run(client, created_runs, mode=mode, workload=workload)
    completed = wait_for_status(client, str(run["id"]), {"completed"})
    assert_exact_accounting(completed)
    assert completed["final_metrics"]["completed"] == 20  # type: ignore[index]
    assert completed["final_metrics"]["failed"] == 0  # type: ignore[index]
    assert len(completed["snapshots"]) >= 1  # type: ignore[arg-type]


def test_retries_and_dead_letter_accounting(
    client: httpx.Client, created_runs: list[str]
) -> None:
    run = create_run(
        client,
        created_runs,
        job_count=8,
        workload="unreliable",
        failure_probability=1,
        max_retries=1,
    )
    completed = wait_for_status(client, str(run["id"]), {"completed"})
    assert_exact_accounting(completed)
    metrics = completed["final_metrics"]
    assert isinstance(metrics, dict)
    assert metrics["completed"] == 0
    assert metrics["failed"] == 8
    assert metrics["retries"] == 8
    assert metrics["dead_lettered"] == 8


def test_extreme_scale_simulation_accounting(
    client: httpx.Client, created_runs: list[str]
) -> None:
    run = create_run(
        client,
        created_runs,
        job_count=1_000_001,
        mode="simulation",
        failure_probability=0,
    )
    completed = wait_for_status(client, str(run["id"]), {"completed"})
    assert_exact_accounting(completed)


@pytest.mark.parametrize(
    "overrides",
    [
        {"job_count": 100_000, "mode": "simulation"},
        {"job_count": 1_000_001, "mode": "benchmark"},
        {"failure_probability": 1.1},
        {"max_retries": 11},
        {"producer_concurrency": 0},
    ],
)
def test_invalid_requests_are_rejected(client: httpx.Client, overrides: dict[str, object]) -> None:
    payload = {
        "name": "Invalid E2E run",
        "job_count": 10,
        "mode": "benchmark",
        "producer_concurrency": 1,
        "target_rate": 100,
        "workload": "io_light",
        "duration_ms": 1,
        "failure_probability": 0,
        "max_retries": 1,
        **overrides,
    }
    assert client.post("/api/v1/runs", json=payload).status_code == 422


def test_completed_event_stream_closes(
    client: httpx.Client, created_runs: list[str]
) -> None:
    run = create_run(client, created_runs, job_count=5)
    wait_for_status(client, str(run["id"]), {"completed"})
    with client.stream("GET", f"/api/v1/runs/{run['id']}/events") as response:
        body = "\n".join(response.iter_lines())
    assert response.status_code == 200
    assert '"stream_finished": 1' in body


def test_cancel_stops_an_active_run(
    client: httpx.Client, created_runs: list[str]
) -> None:
    run = create_run(
        client,
        created_runs,
        job_count=5_000,
        target_rate=100,
        duration_ms=50,
    )
    wait_for_status(client, str(run["id"]), {"producing", "running"})
    response = client.post(f"/api/v1/runs/{run['id']}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    cancelled = wait_for_status(client, str(run["id"]), {"cancelled"})
    assert cancelled["completed_at"] is not None


def test_delete_active_run_stops_and_removes_it(
    client: httpx.Client, created_runs: list[str]
) -> None:
    run = create_run(
        client,
        created_runs,
        job_count=5_000,
        target_rate=100,
        duration_ms=50,
    )
    run_id = str(run["id"])
    wait_for_status(client, run_id, {"producing", "running"})
    assert client.delete(f"/api/v1/runs/{run_id}").status_code == 204
    created_runs.remove(run_id)
    assert client.get(f"/api/v1/runs/{run_id}").status_code == 404
    assert all(item["id"] != run_id for item in client.get("/api/v1/runs").json())
