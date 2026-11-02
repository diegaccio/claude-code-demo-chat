"""The chat seam, with a fake model client in place of the model server."""

from collections.abc import AsyncIterator

import httpx2
import openai
import pytest

from demo_app import messages
from demo_app.chat import Chat, ChatError
from tests.fakes import REQUEST, FakeModelClient


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


async def test_missing_model_raises_a_readable_error_naming_the_model() -> None:
    not_found = openai.NotFoundError(
        "model 'ministral-3:3b' not found",
        response=httpx2.Response(404, request=REQUEST),
        body=None,
    )
    chat = Chat(FakeModelClient(error=not_found), model="ministral-3:3b")

    with pytest.raises(ChatError) as raised:
        await collect(chat.send("Ciao!"))

    assert str(raised.value) == messages.MODEL_MISSING.format(model="ministral-3:3b")
    assert "ministral-3:3b" in str(raised.value)


async def test_after_a_failed_turn_the_chat_goes_on_without_it() -> None:
    client = FakeModelClient(error=openai.APIConnectionError(request=REQUEST))
    chat = Chat(client, model="ministral-3:3b")
    with pytest.raises(ChatError):
        await collect(chat.send("Ci sei?"))

    client.error = None
    client.chunks = ["Eccomi."]
    chunks = await collect(chat.send("Ci sei ora?"))

    assert chunks == ["Eccomi."]
    assert client.requests[-1][1] == [{"role": "user", "content": "Ci sei ora?"}]


async def test_any_other_server_error_raises_a_readable_error() -> None:
    server_error = openai.InternalServerError(
        "boom", response=httpx2.Response(500, request=REQUEST), body=None
    )
    chat = Chat(FakeModelClient(error=server_error), model="ministral-3:3b")

    with pytest.raises(ChatError) as raised:
        await collect(chat.send("Ciao!"))

    assert str(raised.value) == messages.MODEL_ERROR


async def test_persona_switch_changes_the_system_prompt_sent() -> None:
    client = FakeModelClient(["Ok"])
    chat = Chat(client, model="ministral-3:3b")

    confirmation = chat.use_persona("pirata")
    await collect(chat.send("Ciao!"))
    chat.use_persona("poeta")
    await collect(chat.send("E ora?"))

    assert confirmation == messages.PERSONA_SWITCHED.format(name="pirata")
    assert client.requests[0][1][0] == {
        "role": "system",
        "content": messages.PERSONAS["pirata"],
    }
    assert client.requests[1][1][0] == {
        "role": "system",
        "content": messages.PERSONAS["poeta"],
    }
    assert client.requests[1][1][1:] == [
        {"role": "user", "content": "Ciao!"},
        {"role": "assistant", "content": "Ok"},
        {"role": "user", "content": "E ora?"},
    ]


async def test_without_a_persona_no_system_prompt_is_sent() -> None:
    client = FakeModelClient(["Ok"])
    await collect(Chat(client, model="m").send("Ciao!"))

    assert client.requests[0][1] == [{"role": "user", "content": "Ciao!"}]


@pytest.mark.parametrize("name", ["", "sconosciuta"])
def test_missing_or_unknown_persona_lists_the_available_ones(name: str) -> None:
    chat = Chat(FakeModelClient(), model="m")

    with pytest.raises(ChatError) as raised:
        chat.use_persona(name)

    for persona in messages.PERSONAS:
        assert persona in str(raised.value)
