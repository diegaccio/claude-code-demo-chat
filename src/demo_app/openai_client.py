"""The model client for OpenAI-compatible servers, such as Ollama."""

from collections.abc import AsyncIterator, Sequence

import httpx2
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from demo_app.chat import Message
from demo_app.settings import ModelProfile

# Local servers ignore the key, but the SDK requires one.
_UNUSED_API_KEY = "not-needed"


class OpenAIModelClient:
    """Streams answers from the model server of a Model profile."""

    def __init__(
        self, profile: ModelProfile, *, http_client: httpx2.AsyncClient | None = None
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=_UNUSED_API_KEY,
            base_url=profile.base_url,
            max_retries=0,  # report a failure at once, in the chat
            http_client=http_client,
        )

    async def stream(
        self, *, model: str, messages: Sequence[Message]
    ) -> AsyncIterator[str]:
        response = await self._client.chat.completions.create(
            model=model, messages=[_to_openai(message) for message in messages], stream=True
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def _to_openai(message: Message) -> ChatCompletionMessageParam:
    match message["role"]:
        case "system":
            return {"role": "system", "content": message["content"]}
        case "user":
            return {"role": "user", "content": message["content"]}
        case "assistant":
            return {"role": "assistant", "content": message["content"]}
