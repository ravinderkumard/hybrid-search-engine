import yaml
import os
from pathlib import Path

def load_config(config_path: str = "config/config.yaml") -> dict:
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = Path(__file__).resolve().parents[1] / config_file

    with open(config_file, "r") as file:
        config = yaml.safe_load(file)
        # print(config)
    return config
