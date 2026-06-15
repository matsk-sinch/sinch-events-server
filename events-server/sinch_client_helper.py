import os
from pathlib import Path

from dotenv import dotenv_values
from sinch import SinchClient


def load_config() -> dict[str, str]:
    """
    Load configuration from environment variables, with optional .env file fallback.
    """
    current_dir = Path(__file__).resolve().parent
    env_file = current_dir / ".env"

    config: dict[str, str] = {}
    if env_file.exists():
        config.update({k: v for k, v in dotenv_values(env_file).items() if v is not None})

    for key, value in os.environ.items():
        if value:
            config[key] = value

    return config


def get_sinch_client(_config: dict) -> SinchClient:
    """
    Create and return a configured SinchClient instance.
    """
    return SinchClient()
