"""The Demo app: wires the settings, the chat and the terminal UI."""

from demo_app.app import DemoApp
from demo_app.chat import Chat
from demo_app.openai_client import client_for
from demo_app.settings import Settings


def main() -> None:
    """Start the Demo app on the Model profile the settings choose."""
    profile = Settings().model_profile()
    chat = Chat(client_for(profile), model=profile.model)
    DemoApp(chat, profile).run()
