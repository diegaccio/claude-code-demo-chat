from pathlib import Path

import pytest

from demo_app.settings import ModelProfile, Settings


@pytest.fixture(autouse=True)
def no_settings_in_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)  # no .env file here
    for name in ("MODEL_PROFILE", "LOCAL_BASE_URL", "LOCAL_MODEL"):
        monkeypatch.delenv(name, raising=False)


def test_local_model_profile_is_the_default() -> None:
    settings = Settings()

    assert settings.model_profile() == ModelProfile(
        name="local",
        base_url="http://localhost:11434/v1",
        model="ministral-3:3b",
    )


def test_local_model_profile_reads_its_server_and_model_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOCAL_BASE_URL", "http://ollama:11434/v1")
    monkeypatch.setenv("LOCAL_MODEL", "llama3.2:3b")

    settings = Settings()

    assert settings.model_profile() == ModelProfile(
        name="local", base_url="http://ollama:11434/v1", model="llama3.2:3b"
    )


def test_settings_are_read_from_a_local_env_file_shaped_like_the_example(
    tmp_path: Path,
) -> None:
    (tmp_path / ".env").write_text(
        "MODEL_PROFILE=local\n"
        "LOCAL_BASE_URL=http://localhost:11434/v1\n"
        "LOCAL_MODEL=llama3.2:3b\n"
        "SRH_BASE_URL=\n"
        "SRH_MODEL=qwen3.6-35b-a3b\n",
        encoding="utf-8",
    )

    assert Settings().model_profile().model == "llama3.2:3b"
