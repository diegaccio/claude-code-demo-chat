"""The Demo app's terminal UI."""

from textual.app import App, ComposeResult
from textual.widgets import Static

from demo_app import messages
from demo_app.chat import Chat
from demo_app.settings import ModelProfile


class DemoApp(App[None]):
    """A terminal chat with a model."""

    def __init__(self, chat: Chat, profile: ModelProfile) -> None:
        super().__init__()
        self._chat = chat
        self._profile = profile

    def compose(self) -> ComposeResult:
        yield Static(
            messages.STATUS_PROFILE.format(
                profile=messages.PROFILE_NAMES[self._profile.name],
                model=self._profile.model,
            ),
            id="status-bar",
        )
