"""The chat seam: holds the conversation and talks to the model."""

from collections.abc import AsyncIterator, Sequence
from typing import Literal, Protocol, TypedDict

import openai

from demo_app import messages


class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class ModelClient(Protocol):
    """Streams a reply from an OpenAI-compatible model server."""

    def stream(
        self, *, model: str, messages: Sequence[Message]
    ) -> AsyncIterator[str]: ...


class ChatError(Exception):
    """A failed turn; its text is ready to show the user."""


class Chat:
    """A conversation with one model, through a model client."""

    def __init__(self, client: ModelClient, *, model: str) -> None:
        self._client = client
        self._model = model
        self._messages: list[Message] = []

    async def send(self, text: str) -> AsyncIterator[str]:
        """Add the user's text and stream the model's answer, chunk by chunk."""
        self._messages.append({"role": "user", "content": text})
        answer: list[str] = []
        try:
            async for chunk in self._client.stream(
                model=self._model, messages=list(self._messages)
            ):
                answer.append(chunk)
                yield chunk
        except openai.APIConnectionError as error:
            raise ChatError(messages.MODEL_UNREACHABLE) from error
        except openai.NotFoundError as error:
            raise ChatError(messages.MODEL_MISSING.format(model=self._model)) from error
        self._messages.append({"role": "assistant", "content": "".join(answer)})
