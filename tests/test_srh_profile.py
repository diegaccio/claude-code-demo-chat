"""The SRH Model profile: selection, per-profile options, missing URL."""

import json
from pathlib import Path

import httpx2
import pytest
from textual.widgets import Static

from demo_app import messages
from demo_app.app import DemoApp
from demo_app.chat import Chat, ChatError
from demo_app.openai_client import client_for
from demo_app.settings import ModelProfile, Settings
from tests.fakes import FakeModelClient

# A placeholder: the real SRH URL lives only in the local .env.
PLACEHOLDER_URL = "http://srh.example.test/v1"
THINKING_OFF: dict[str, object] = {"chat_template_kwargs": {"enable_thinking": False}}

SRH_PROFILE = ModelProfile(
    name="srh",
    base_url=PLACEHOLDER_URL,
    model="qwen3.6-35b-a3b",
    extra_body=THINKING_OFF,
)
LOCAL_PROFILE = ModelProfile(
    name="local", base_url="http://localhost:11434/v1", model="ministral-3:3b"
)


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


def test_one_setting_selects_the_srh_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PROFILE", "srh")
    monkeypatch.setenv("SRH_BASE_URL", PLACEHOLDER_URL)

    assert Settings().model_profile() == SRH_PROFILE


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


def chat_for(profile: ModelProfile, requests: list[dict[str, object]]) -> Chat:
    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(json.loads(request.content))
        event = {
            "id": "1",
            "object": "chat.completion.chunk",
            "created": 0,
            "model": profile.model,
            "choices": [
                {"index": 0, "delta": {"content": "Ok"}, "finish_reason": None}
            ],
        }
        body = f"data: {json.dumps(event)}\n\ndata: [DONE]\n\n".encode()
        return httpx2.Response(
            200, content=body, headers={"content-type": "text/event-stream"}
        )

    client = client_for(
        profile, http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    )
    return Chat(client, model=profile.model)


async def test_srh_requests_carry_the_profile_extra_options() -> None:
    requests: list[dict[str, object]] = []

    chunks = [chunk async for chunk in chat_for(SRH_PROFILE, requests).send("Ciao")]

    assert chunks == ["Ok"]
    assert requests[0]["model"] == "qwen3.6-35b-a3b"
    assert requests[0]["chat_template_kwargs"] == {"enable_thinking": False}


async def test_local_requests_carry_no_extra_options() -> None:
    requests: list[dict[str, object]] = []

    _ = [chunk async for chunk in chat_for(LOCAL_PROFILE, requests).send("Ciao")]

    assert "chat_template_kwargs" not in requests[0]


async def test_srh_profile_without_a_url_reports_it_readably() -> None:
    profile = ModelProfile(name="srh", base_url=None, model="qwen3.6-35b-a3b")
    chat = Chat(client_for(profile), model=profile.model)

    with pytest.raises(ChatError) as raised:
        _ = [chunk async for chunk in chat.send("Ciao")]

    assert str(raised.value) == messages.SRH_URL_MISSING


async def test_status_bar_names_the_srh_profile_never_its_url() -> None:
    app = DemoApp(Chat(FakeModelClient(), model=SRH_PROFILE.model), SRH_PROFILE)
    async with app.run_test():
        status = str(app.query_one("#status-bar", Static).render())

    assert status == "Profilo: SRH · qwen3.6-35b-a3b"
    assert "srh.example.test" not in status
