"""The Demo app's terminal UI."""

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Input, Static

from demo_app import messages
from demo_app.chat import Chat, ChatError
from demo_app.settings import ModelProfile
from demo_app.theme import NOTTE


class DemoApp(App[None]):
    """A terminal chat with a model."""

    TITLE = messages.APP_TITLE

    CSS = """
    #wordmark {
        dock: top;
        height: 3;
        padding: 1 2;
        background: $panel;
        color: $primary;
        text-style: bold;
    }
    #conversation {
        padding: 1 2;
    }
    .turn {
        margin-bottom: 1;
    }
    .user {
        color: $accent;
        text-style: bold;
    }
    .answer {
        color: $foreground;
    }
    .error {
        color: $error;
        text-style: bold;
    }
    #prompt {
        dock: bottom;
        margin: 0 1 1 1;
    }
    #status-bar {
        dock: bottom;
        height: 1;
        padding: 0 2;
        background: $panel;
        color: $foreground;
    }
    """

    def __init__(self, chat: Chat, profile: ModelProfile) -> None:
        super().__init__()
        self._chat = chat
        self._profile = profile

    def on_mount(self) -> None:
        self.register_theme(NOTTE)
        self.theme = NOTTE.name

    def compose(self) -> ComposeResult:
        yield Static(messages.WORDMARK, id="wordmark")
        yield Static(
            messages.STATUS_PROFILE.format(
                profile=messages.PROFILE_NAMES[self._profile.name],
                model=self._profile.model,
            ),
            id="status-bar",
        )
        yield Input(placeholder=messages.PROMPT_PLACEHOLDER, id="prompt")
        yield VerticalScroll(id="conversation")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        event.input.clear()
        event.input.disabled = True
        conversation = self.query_one("#conversation", VerticalScroll)
        await conversation.mount(
            Static(
                messages.USER_TURN.format(text=text),
                markup=False,
                classes="turn user",
            )
        )
        answer = Static("", markup=False, classes="turn answer")
        await conversation.mount(answer)
        self.run_worker(self._reply(text, answer), exclusive=True)

    async def _reply(self, text: str, answer: Static) -> None:
        conversation = self.query_one("#conversation", VerticalScroll)
        streamed = ""
        try:
            async for chunk in self._chat.send(text):
                streamed += chunk
                answer.update(streamed)
                conversation.scroll_end(animate=False)
        except ChatError as error:
            answer.update(str(error))
            answer.set_classes("turn error")
        finally:
            prompt = self.query_one("#prompt", Input)
            prompt.disabled = False
            prompt.focus()
            conversation.scroll_end(animate=False)
