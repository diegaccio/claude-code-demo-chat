"""Settings: the Model profiles read from the environment and a local .env."""

from pathlib import Path

import pytest

from demo_app.settings import ModelProfile, Settings

# A placeholder: the real SRH URL lives only in the local .env.
PLACEHOLDER_URL = "http://srh.example.test/v1"


@pytest.fixture(autouse=True)
def no_settings_in_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)  # no .env file here
    for name in (
        "MODEL_PROFILE",
        "LOCAL_BASE_URL",
        "LOCAL_MODEL",
        "SRH_BASE_URL",
        "SRH_MODEL",
    ):
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


def test_one_setting_selects_the_srh_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROFILE", "srh")
    monkeypatch.setenv("SRH_BASE_URL", PLACEHOLDER_URL)

    assert Settings().model_profile() == ModelProfile(
        name="srh",
        base_url=PLACEHOLDER_URL,
        model="qwen3.6-35b-a3b",
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )


def test_srh_url_is_read_from_the_local_env_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        f"MODEL_PROFILE=srh\nSRH_BASE_URL={PLACEHOLDER_URL}\n", encoding="utf-8"
    )

    assert Settings().model_profile().base_url == PLACEHOLDER_URL


def test_srh_url_has_no_default() -> None:
    assert Settings().srh_base_url is None


def test_srh_profile_without_a_url_has_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROFILE", "srh")
    monkeypatch.setenv("SRH_BASE_URL", "")

    assert Settings().model_profile().base_url is None


def test_local_profile_has_no_extra_options() -> None:
    assert Settings().model_profile().extra_body == {}
