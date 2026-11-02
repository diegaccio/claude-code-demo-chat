"""Test doubles shared by the chat-seam and UI-seam tests."""

from collections.abc import AsyncIterator, Sequence

import httpx2

from demo_app.chat import Message

# The request a model client error refers to.
REQUEST = httpx2.Request("POST", "http://localhost:11434/v1/chat/completions")


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
