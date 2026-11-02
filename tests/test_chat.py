from collections.abc import AsyncIterator, Sequence

import httpx2
import openai
import pytest

from demo_app import messages
from demo_app.chat import Chat, ChatError, Message


class FakeModelClient:
    """Stands in for the OpenAI-compatible model server."""

    def __init__(
        self, chunks: Sequence[str] = (), *, error: Exception | None = None
    ) -> None:
        self.chunks = list(chunks)
        self.error = error
        self.requests: list[tuple[str, list[Message]]] = []

    async def stream(
        self, *, model: str, messages: Sequence[Message]
    ) -> AsyncIterator[str]:
        self.requests.append((model, list(messages)))
        for chunk in self.chunks:
            yield chunk
        if self.error is not None:
            raise self.error


REQUEST = httpx2.Request("POST", "http://localhost:11434/v1/chat/completions")


async def collect(stream: AsyncIterator[str]) -> list[str]:
    return [chunk async for chunk in stream]


async def test_answer_streams_in_chunks_from_the_model() -> None:
    client = FakeModelClient(["Ciao", ", come ", "stai?"])
    chat = Chat(client, model="ministral-3:3b")

    chunks = await collect(chat.send("Ciao!"))

    assert chunks == ["Ciao", ", come ", "stai?"]
    assert client.requests == [
        ("ministral-3:3b", [{"role": "user", "content": "Ciao!"}])
    ]


async def test_next_turn_sends_the_whole_conversation_so_far() -> None:
    client = FakeModelClient(["Bene", ", grazie."])
    chat = Chat(client, model="ministral-3:3b")
    await collect(chat.send("Come stai?"))

    await collect(chat.send("E tu?"))

    assert client.requests[-1][1] == [
        {"role": "user", "content": "Come stai?"},
        {"role": "assistant", "content": "Bene, grazie."},
        {"role": "user", "content": "E tu?"},
    ]


async def test_unreachable_server_raises_a_readable_error() -> None:
    client = FakeModelClient(error=openai.APIConnectionError(request=REQUEST))
    chat = Chat(client, model="ministral-3:3b")

    with pytest.raises(ChatError) as raised:
        await collect(chat.send("Ciao!"))

    assert str(raised.value) == messages.MODEL_UNREACHABLE
