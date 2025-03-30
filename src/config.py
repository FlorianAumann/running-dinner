import json
import os
from pathlib import Path

CONFIG_FILE_NAME = "config.json"


class ProjectConfig(object):
    # Google API key used for route planning and map generation
    google_api_key: str

    def __init__(self, google_api_key) -> None:
        self.google_api_key = google_api_key


class ConfigManager:
    def __init__(self) -> None:
        # Initialize the configuration loader
        self.config_file = Path(os.getcwd()) / CONFIG_FILE_NAME

    def load_config(self) -> ProjectConfig:
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text(encoding="utf-8"))
                return ProjectConfig(**data)
            except Exception as e:
                config = ProjectConfig()
                return config
        else:
            config = ProjectConfig()
            return config

    def save_config(self, config: ProjectConfig):
        try:
            self.config_file.write_text(json.dumps(config.__dict__))
        except Exception as e:
            return # Ignore for now