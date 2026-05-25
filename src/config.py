from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()


def load_config(config_path: str = "configs/pipeline.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_taxonomy(taxonomy_path: str = "configs/label_taxonomy.yaml") -> dict:
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
