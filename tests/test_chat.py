"""The chat seam, with a fake model client in place of the model server."""

import json
from collections.abc import AsyncIterator
from pathlib import Path

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


async def test_saved_conversation_loads_back_and_the_chat_continues(
    tmp_path: Path,
) -> None:
    client = FakeModelClient(["Bene."])
    chat = Chat(client, model="ministral-3:3b", conversations=tmp_path)
    await collect(chat.send("Come stai?"))
    chat.save("lunedi")

    assert json.loads((tmp_path / "lunedi.json").read_text("utf-8")) == [
        {"role": "user", "content": "Come stai?"},
        {"role": "assistant", "content": "Bene."},
    ]

    other = Chat(client, model="ministral-3:3b", conversations=tmp_path)
    assert other.load("lunedi") == [
        {"role": "user", "content": "Come stai?"},
        {"role": "assistant", "content": "Bene."},
    ]
    await collect(other.send("E ora?"))

    assert client.requests[-1][1] == [
        {"role": "user", "content": "Come stai?"},
        {"role": "assistant", "content": "Bene."},
        {"role": "user", "content": "E ora?"},
    ]


def test_loading_a_missing_conversation_raises_a_readable_error(
    tmp_path: Path,
) -> None:
    chat = Chat(FakeModelClient(), model="m", conversations=tmp_path)

    with pytest.raises(ChatError) as raised:
        chat.load("assente")

    assert str(raised.value) == messages.CONVERSATION_MISSING.format(name="assente")


@pytest.mark.parametrize(
    "content",
    ["not json {", '{"role": "user"}', '[{"role": "boss", "content": "x"}]', "[1]"],
)
def test_loading_a_corrupt_conversation_raises_a_readable_error_and_keeps_the_chat(
    tmp_path: Path, content: str
) -> None:
    (tmp_path / "rotta.json").write_text(content, encoding="utf-8")
    chat = Chat(FakeModelClient(), model="m", conversations=tmp_path)

    with pytest.raises(ChatError) as raised:
        chat.load("rotta")

    assert str(raised.value) == messages.CONVERSATION_CORRUPT.format(name="rotta")


def test_a_name_that_could_leave_the_folder_is_refused(tmp_path: Path) -> None:
    chat = Chat(FakeModelClient(), model="m", conversations=tmp_path)

    with pytest.raises(ChatError) as raised:
        chat.save("../fuori")

    assert str(raised.value) == messages.CONVERSATION_NAME_INVALID
    assert not (tmp_path.parent / "fuori.json").exists()
