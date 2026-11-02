"""The UI seam, driven with Textual's pilot."""

from pathlib import Path

import openai
from textual.pilot import Pilot
from textual.widgets import Input, Static

from demo_app import messages
from demo_app.app import DemoApp
from demo_app.chat import Chat
from demo_app.settings import ModelProfile
from tests.fakes import REQUEST, FakeModelClient

PROFILE = ModelProfile(
    name="local", base_url="http://localhost:11434/v1", model="ministral-3:3b"
)


def demo_app(client: FakeModelClient | None = None) -> DemoApp:
    chat = Chat(client or FakeModelClient(), model=PROFILE.model)
    return DemoApp(chat, PROFILE)


def text_of(app: DemoApp, selector: str) -> str:
    return str(app.query_one(selector, Static).render())


async def test_status_bar_names_the_model_profile() -> None:
    app = demo_app()
    async with app.run_test():
        assert text_of(app, "#status-bar") == "Profilo: locale · ministral-3:3b"


async def test_header_shows_the_base_digitale_wordmark_in_the_notte_theme() -> None:
    app = demo_app()
    async with app.run_test():
        assert text_of(app, "#wordmark") == "Base Digitale"
        assert app.theme == "notte"
        assert app.current_theme.background == "#14091F"
        assert app.current_theme.primary == "#E0336E"
        assert app.current_theme.panel == "#3A0A2A"
        assert app.current_theme.surface == "#22102F"
        assert app.current_theme.accent == "#8C8CFF"


async def test_sent_message_and_streamed_answer_appear_in_the_chat() -> None:
    app = demo_app(FakeModelClient(["Ciao", ", sono qui."]))
    async with app.run_test() as pilot:
        await pilot.click("#prompt")
        await pilot.press(*"Ciao", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()

        turns = [str(w.render()) for w in app.query(".turn").results(Static)]
        assert turns == ["Tu: Ciao", "Ciao, sono qui."]
        assert app.query_one("#prompt", Input).value == ""


async def test_model_error_appears_in_the_chat_and_the_app_keeps_running() -> None:
    client = FakeModelClient(error=openai.APIConnectionError(request=REQUEST))
    app = demo_app(client)
    async with app.run_test() as pilot:
        await pilot.click("#prompt")
        await pilot.press(*"Ciao", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert text_of(app, ".error") == messages.MODEL_UNREACHABLE
        prompt = app.query_one("#prompt", Input)
        assert not prompt.disabled
        assert prompt.has_focus

        client.error = None
        client.chunks = ["Eccomi."]
        await pilot.press(*"Ci sei?", "enter")
        await app.workers.wait_for_complete()
        await pilot.pause()

        turns = [str(w.render()) for w in app.query(".turn").results(Static)]
        assert turns[-1] == "Eccomi."


async def type_command(app: DemoApp, pilot: Pilot[None], text: str) -> None:
    await pilot.click("#prompt")
    await pilot.press(*text, "enter")
    await app.workers.wait_for_complete()
    await pilot.pause()


def turns_of(app: DemoApp) -> list[str]:
    return [str(w.render()) for w in app.query(".turn").results(Static)]


async def test_save_and_load_commands_restore_the_conversation(
    tmp_path: Path,
) -> None:
    client = FakeModelClient(["Ciao", " a te."])
    chat = Chat(client, model=PROFILE.model, conversations=tmp_path)
    app = DemoApp(chat, PROFILE)
    async with app.run_test() as pilot:
        await type_command(app, pilot, "Ciao")
        await type_command(app, pilot, "/save prova")
        assert turns_of(app)[-1] == messages.CONVERSATION_SAVED.format(name="prova")

        await type_command(app, pilot, "/load prova")

        assert turns_of(app) == [
            "Tu: Ciao",
            "Ciao a te.",
            messages.CONVERSATION_LOADED.format(name="prova"),
        ]
        await type_command(app, pilot, "Ancora")
        assert [m["content"] for m in client.requests[-1][1]] == [
            "Ciao",
            "Ciao a te.",
            "Ancora",
        ]


async def test_loading_a_missing_or_corrupt_file_shows_a_message_and_keeps_running(
    tmp_path: Path,
) -> None:
    (tmp_path / "rotta.json").write_text("nope", encoding="utf-8")
    chat = Chat(FakeModelClient(), model=PROFILE.model, conversations=tmp_path)
    app = DemoApp(chat, PROFILE)
    async with app.run_test() as pilot:
        await type_command(app, pilot, "/load assente")
        assert text_of(app, ".error") == messages.CONVERSATION_MISSING.format(
            name="assente"
        )

        await type_command(app, pilot, "/load rotta")
        assert turns_of(app)[-1] == messages.CONVERSATION_CORRUPT.format(name="rotta")
        assert not app.query_one("#prompt", Input).disabled


async def test_a_command_without_a_name_explains_its_usage(tmp_path: Path) -> None:
    chat = Chat(FakeModelClient(), model=PROFILE.model, conversations=tmp_path)
    app = DemoApp(chat, PROFILE)
    async with app.run_test() as pilot:
        await type_command(app, pilot, "/save")

        assert turns_of(app) == [messages.CONVERSATION_NAME_USAGE]
