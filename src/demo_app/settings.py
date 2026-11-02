"""Settings, read from the environment and from a local `.env` file."""

from dataclasses import dataclass
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProfileName = Literal["local"]


@dataclass(frozen=True)
class ModelProfile:
    """Which model server and model the Demo app talks to."""

    name: ProfileName
    base_url: str
    model: str


class Settings(BaseSettings):
    """The Demo app's settings; names match `.env.example`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_profile_name: ProfileName = Field(
        default="local", validation_alias="MODEL_PROFILE"
    )
    local_base_url: str = "http://localhost:11434/v1"
    local_model: str = "ministral-3:3b"

    def model_profile(self) -> ModelProfile:
        """The active Model profile."""
        return ModelProfile(
            name=self.model_profile_name,
            base_url=self.local_base_url,
            model=self.local_model,
        )
