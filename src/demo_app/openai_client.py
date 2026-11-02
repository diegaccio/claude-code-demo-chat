"""The model client for OpenAI-compatible servers, such as Ollama and SRH."""

from collections.abc import AsyncIterator, Sequence

import httpx2
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from demo_app.chat import ChatError, Message, ModelClient
from demo_app.messages import SRH_URL_MISSING
from demo_app.settings import ModelProfile

# Local servers ignore the key, but the SDK requires one.
_UNUSED_API_KEY = "not-needed"


class OpenAIModelClient:
    """Streams answers from the model server of a Model profile."""

    def __init__(
        self,
        profile: ModelProfile,
        *,
        base_url: str,
        http_client: httpx2.AsyncClient | None = None,
    ) -> None:
        self._extra_body = profile.extra_body
        self._client = AsyncOpenAI(
            api_key=_UNUSED_API_KEY,
            base_url=base_url,
            max_retries=0,  # report a failure at once, in the chat
            http_client=http_client,
        )

    async def stream(
        self, *, model: str, messages: Sequence[Message]
    ) -> AsyncIterator[str]:
        """Yield the non-empty text deltas of the server's streamed answer."""
        response = await self._client.chat.completions.create(
            model=model,
            messages=[_to_openai(message) for message in messages],
            stream=True,
            extra_body=self._extra_body or None,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class UnconfiguredModelClient:
    """Stands in for a profile without a server URL: every turn fails readably."""

    async def stream(
        self, *, model: str, messages: Sequence[Message]
    ) -> AsyncIterator[str]:
        """Fail the turn with a ChatError saying the server URL is missing."""
        raise ChatError(SRH_URL_MISSING)
        yield  # unreachable: makes this an async generator


def client_for(
    profile: ModelProfile, *, http_client: httpx2.AsyncClient | None = None
) -> ModelClient:
    """The model client for a Model profile."""
    if profile.base_url is None:
        return UnconfiguredModelClient()
    return OpenAIModelClient(
        profile, base_url=profile.base_url, http_client=http_client
    )


def _to_openai(message: Message) -> ChatCompletionMessageParam:
    match message["role"]:
        case "system":
            return {"role": "system", "content": message["content"]}
        case "user":
            return {"role": "user", "content": message["content"]}
        case "assistant":
            return {"role": "assistant", "content": message["content"]}
