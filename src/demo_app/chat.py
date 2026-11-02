"""The chat seam: holds the conversation and talks to the model."""

import json
import re
from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import Literal, Protocol, TypedDict, cast

import openai

from demo_app import messages

_NAME = re.compile(r"[\w-]+")


Role = Literal["system", "user", "assistant"]
_ROLES = ("system", "user", "assistant")


class Message(TypedDict):
    role: Role
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

    def __init__(
        self,
        client: ModelClient,
        *,
        model: str,
        conversations: Path = Path("conversations"),
    ) -> None:
        self._client = client
        self._model = model
        self._conversations = conversations
        self._messages: list[Message] = []

    async def send(self, text: str) -> AsyncIterator[str]:
        """Stream the model's answer to the user's text, chunk by chunk.

        The turn joins the conversation only once the answer is complete: a
        failed turn raises ChatError and leaves the conversation as it was.
        """
        question: Message = {"role": "user", "content": text}
        answer: list[str] = []
        try:
            async for chunk in self._client.stream(
                model=self._model, messages=[*self._messages, question]
            ):
                answer.append(chunk)
                yield chunk
        except openai.APIConnectionError as error:
            raise ChatError(messages.MODEL_UNREACHABLE) from error
        except openai.NotFoundError as error:
            raise ChatError(messages.MODEL_MISSING.format(model=self._model)) from error
        except openai.APIError as error:
            raise ChatError(messages.MODEL_ERROR) from error
        self._messages += [question, {"role": "assistant", "content": "".join(answer)}]

    def save(self, name: str) -> None:
        """Write the conversation to `<name>.json` in the conversations folder."""
        path = self._path(name)
        self._conversations.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._messages, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def load(self, name: str) -> list[Message]:
        """Replace the conversation with the saved one, and return its messages.

        A missing or corrupt file raises ChatError and leaves the conversation
        as it was.
        """
        path = self._path(name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise ChatError(messages.CONVERSATION_MISSING.format(name=name)) from error
        except (OSError, ValueError) as error:
            raise ChatError(messages.CONVERSATION_CORRUPT.format(name=name)) from error
        loaded = _parse(data)
        if loaded is None:
            raise ChatError(messages.CONVERSATION_CORRUPT.format(name=name))
        self._messages = loaded
        return list(loaded)

    def _path(self, name: str) -> Path:
        if not _NAME.fullmatch(name):
            raise ChatError(messages.CONVERSATION_NAME_INVALID)
        return self._conversations / f"{name}.json"


def _parse(data: object) -> list[Message] | None:
    """The messages of a saved conversation, or None when it is not one."""
    if not isinstance(data, list):
        return None
    parsed: list[Message] = []
    for item in cast(list[object], data):
        if not isinstance(item, dict):
            return None
        fields = cast(dict[str, object], item)
        role, content = fields.get("role"), fields.get("content")
        if role in _ROLES and isinstance(content, str):
            parsed.append({"role": cast(Role, role), "content": content})
            continue
        return None
    return parsed
