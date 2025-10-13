import json
import os
from importlib.resources import files
from typing import Any, Dict, Optional

from appdirs import user_config_dir
from loguru import logger


class SettingsManager:
    def __init__(self, filename: str, app_name: str, config_dir: Optional[str] = None):
        self.filename = filename
        self.app_name = app_name
        self.config_dir = os.path.join(user_config_dir(), app_name)
        self.user_config_path = os.path.join(self.config_dir, f"{filename}.json")
        self.settings: Dict[str, Any] = {}
        self.ensure_default_config()

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.settings.get(key, default)

    def load(self) -> None:
        self.settings.clear()
        try:
            with open(self.user_config_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            if isinstance(json_data, dict):
                self.settings.update(json_data)
            logger.info(f"Loaded settings from {self.user_config_path}")
        except FileNotFoundError:
            logger.warning(f"No user settings found at {self.user_config_path}")
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse settings ({e})")
        except Exception as e:
            logger.error(f"Unexpected error loading settings: {e}")

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.user_config_path), exist_ok=True)
            with open(self.user_config_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            logger.info(f"Settings saved to {self.user_config_path}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return self.settings

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SettingsManager":
        settings = cls(
            data.get("name", ""), data.get("path", ""), data.get("app_name", "")
        )
        settings.settings = data
        return settings

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SettingsManager):
            return False
        return self.settings == other.settings

    def ensure_default_config(self) -> None:
        try:
            default_path = files(f"{self.app_name}.data").joinpath(
                f"default_{self.filename}.json"
            )
        except Exception as e:
            logger.debug(f"No default config resource found: {e}")
            return

        if not default_path.exists():
            logger.debug(f"Default config file not found at {default_path}")
            return

        if not os.path.exists(self.user_config_path):
            os.makedirs(os.path.dirname(self.user_config_path), exist_ok=True)
            with (
                default_path.open("r", encoding="utf-8") as src,
                open(self.user_config_path, "w", encoding="utf-8") as dst,
            ):
                dst.write(src.read())
            logger.info(f"Default configuration copied to {self.user_config_path}")
