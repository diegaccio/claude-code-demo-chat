from collections.abc import AsyncIterator, Sequence

from demo_app.chat import Chat, Message


class FakeModelClient:
    """Stands in for the OpenAI-compatible model server."""

    def __init__(self, chunks: Sequence[str] = ()) -> None:
        self.chunks = list(chunks)
        self.requests: list[tuple[str, list[Message]]] = []

    async def stream(
        self, *, model: str, messages: Sequence[Message]
    ) -> AsyncIterator[str]:
        self.requests.append((model, list(messages)))
        for chunk in self.chunks:
            yield chunk


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
