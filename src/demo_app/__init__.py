from demo_app.app import DemoApp
from demo_app.chat import Chat
from demo_app.openai_client import OpenAIModelClient
from demo_app.settings import Settings


def main() -> None:
    """Start the Demo app on the Model profile the settings choose."""
    profile = Settings().model_profile()
    chat = Chat(OpenAIModelClient(profile), model=profile.model)
    DemoApp(chat, profile).run()
