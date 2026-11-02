"""The chat seam: holds the conversation and talks to the model."""

from collections.abc import AsyncIterator, Sequence
from typing import Literal, Protocol, TypedDict


class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class ModelClient(Protocol):
    """Streams a reply from an OpenAI-compatible model server."""

    def stream(
        self, *, model: str, messages: Sequence[Message]
    ) -> AsyncIterator[str]: ...


class Chat:
    """A conversation with one model, through a model client."""

    def __init__(self, client: ModelClient, *, model: str) -> None:
        self._client = client
        self._model = model
        self._messages: list[Message] = []

    async def send(self, text: str) -> AsyncIterator[str]:
        """Add the user's text and stream the model's answer, chunk by chunk."""
        self._messages.append({"role": "user", "content": text})
        async for chunk in self._client.stream(
            model=self._model, messages=list(self._messages)
        ):
            yield chunk
