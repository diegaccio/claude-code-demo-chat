"""The UI seam, driven with Textual's pilot."""

from textual.widgets import Static

from demo_app.app import DemoApp
from demo_app.chat import Chat
from demo_app.settings import ModelProfile
from tests.fakes import FakeModelClient

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
