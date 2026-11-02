"""The OpenAI-compatible model client, against a fake HTTP model server."""

import json

import httpx2
import pytest

from demo_app import messages
from demo_app.chat import Chat, ChatError
from demo_app.openai_client import OpenAIModelClient
from demo_app.settings import ModelProfile

PROFILE = ModelProfile(
    name="local", base_url="http://localhost:11434/v1", model="ministral-3:3b"
)


def sse(*contents: str) -> bytes:
    events = [
        {
            "id": "1",
            "object": "chat.completion.chunk",
            "created": 0,
            "model": PROFILE.model,
            "choices": [
                {"index": 0, "delta": {"content": content}, "finish_reason": None}
            ],
        }
        for content in contents
    ]
    lines = [f"data: {json.dumps(event)}\n\n" for event in events]
    return ("".join(lines) + "data: [DONE]\n\n").encode()


def chat_against(handler: httpx2.MockTransport) -> Chat:
    client = OpenAIModelClient(
        PROFILE, http_client=httpx2.AsyncClient(transport=handler)
    )
    return Chat(client, model=PROFILE.model)


async def test_answer_streams_from_the_server() -> None:
    requests: list[dict[str, object]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(json.loads(request.content))
        return httpx2.Response(
            200,
            content=sse("Ciao", "!"),
            headers={"content-type": "text/event-stream"},
        )

    chat = chat_against(httpx2.MockTransport(handler))

    chunks = [chunk async for chunk in chat.send("Ciao")]

    assert chunks == ["Ciao", "!"]
    assert requests[0]["model"] == "ministral-3:3b"
    assert requests[0]["stream"] is True
    assert requests[0]["messages"] == [{"role": "user", "content": "Ciao"}]


async def test_missing_model_on_the_server_is_reported() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            404, json={"error": {"message": "model 'ministral-3:3b' not found"}}
        )

    chat = chat_against(httpx2.MockTransport(handler))

    with pytest.raises(ChatError) as raised:
        _ = [chunk async for chunk in chat.send("Ciao")]

    assert str(raised.value) == messages.MODEL_MISSING.format(model="ministral-3:3b")


async def test_unreachable_server_is_reported() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("Connection refused", request=request)

    chat = chat_against(httpx2.MockTransport(handler))

    with pytest.raises(ChatError) as raised:
        _ = [chunk async for chunk in chat.send("Ciao")]

    assert str(raised.value) == messages.MODEL_UNREACHABLE
