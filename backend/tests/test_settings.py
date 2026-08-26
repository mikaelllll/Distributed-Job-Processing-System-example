import pytest

from app.config import Settings


def test_cors_origins_accept_comma_separated_configuration() -> None:
    settings = Settings(cors_origins="https://one.example, https://two.example")  # type: ignore[arg-type]
    assert settings.cors_origins == ["https://one.example", "https://two.example"]


def test_cors_origins_accept_comma_separated_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://one.example, https://two.example")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["https://one.example", "https://two.example"]


def test_default_worker_prefetch_is_bounded() -> None:
    settings = Settings()
    assert 1 <= settings.worker_prefetch <= 1_000
