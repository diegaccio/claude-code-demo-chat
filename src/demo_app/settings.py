"""Settings, read from the environment and from a local `.env` file."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProfileName = Literal["local", "srh"]


@dataclass(frozen=True)
class ModelProfile:
    """Which model server and model the Demo app talks to."""

    name: ProfileName
    base_url: str | None  # None: the profile's server URL is not configured
    model: str
    # Extra options sent with every request to this profile's server.
    extra_body: dict[str, object] = field(default_factory=dict)


class Settings(BaseSettings):
    """The Demo app's settings; names match `.env.example`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_profile_name: ProfileName = Field(
        default="local", validation_alias="MODEL_PROFILE"
    )
    local_base_url: str = "http://localhost:11434/v1"
    local_model: str = "ministral-3:3b"
    srh_base_url: str | None = None  # read only from the local .env
    srh_model: str = "qwen3.6-35b-a3b"

    def model_profile(self) -> ModelProfile:
        """The active Model profile."""
        if self.model_profile_name == "srh":
            return ModelProfile(
                name="srh",
                base_url=self.srh_base_url or None,
                model=self.srh_model,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
        return ModelProfile(
            name="local", base_url=self.local_base_url, model=self.local_model
        )
