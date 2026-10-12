from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SETTINGS = (
    "model_base_url",
    "model_name",
    "vision_model_name",
    "es_url",
    "litellm_url",
)
SECRET_SETTINGS = ("litellm_management_api_key", "litellm_management_master_key", "model_api_key")
URL_SETTINGS = ("model_base_url", "es_url", "litellm_url")


def default_config() -> dict[str, Any]:
    return {
        "data_dir": str(PROJECT_ROOT / ".local" / "runtime"),
        "model_base_url": "",
        "model_name": "",
        "vision_model_name": "",
        "es_url": "",
        "litellm_url": "",
        "litellm_management_api_key": "",
        "litellm_management_master_key": "",
        "model_api_key": "",
    }


def load_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load local runtime settings; secrets stay server-side and out of API output."""
    config = default_config()
    config_path = os.environ.get("PORTFOLIO_CONFIG", str(PROJECT_ROOT / ".local" / "runtime-config.json"))
    path = Path(config_path).expanduser()
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not read runtime config at {path}: {exc.__class__.__name__}") from exc
        if not isinstance(loaded, dict):
            raise RuntimeError("Runtime config must contain a JSON object")
        config.update({key: value for key, value in loaded.items() if key in (*PUBLIC_SETTINGS, *SECRET_SETTINGS, "data_dir")})
        # Preserve older ignored runtime config names as management-only aliases.
        config["litellm_management_api_key"] = loaded.get(
            "litellm_management_api_key", loaded.get("litellm_api_key", config["litellm_management_api_key"])
        )
        config["litellm_management_master_key"] = loaded.get(
            "litellm_management_master_key", loaded.get("litellm_master_key", config["litellm_management_master_key"])
        )
    config["litellm_management_api_key"] = os.environ.get(
        "PORTFOLIO_LITELLM_API_KEY", config.get("litellm_management_api_key", "")
    )
    config["litellm_management_master_key"] = os.environ.get(
        "PORTFOLIO_LITELLM_MASTER_KEY", config.get("litellm_management_master_key", "")
    )
    config["model_api_key"] = os.environ.get("PORTFOLIO_MODEL_API_KEY", config.get("model_api_key", ""))
    if overrides:
        config.update({key: value for key, value in overrides.items() if key in (*PUBLIC_SETTINGS, *SECRET_SETTINGS, "data_dir")})
        config["litellm_management_api_key"] = overrides.get(
            "litellm_management_api_key", overrides.get("litellm_api_key", config["litellm_management_api_key"])
        )
        config["litellm_management_master_key"] = overrides.get(
            "litellm_management_master_key", overrides.get("litellm_master_key", config["litellm_management_master_key"])
        )
    for key in (*PUBLIC_SETTINGS, *SECRET_SETTINGS):
        value = config.get(key, "")
        if not isinstance(value, str):
            raise RuntimeError(f"Runtime setting {key} must be a string")
        config[key] = value.strip()
    for key in URL_SETTINGS:
        if config[key]:
            _validate_endpoint(key, config[key])
    config["data_dir"] = str(Path(config["data_dir"]).expanduser())
    return config


def _validate_endpoint(key: str, value: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RuntimeError(f"Runtime endpoint {key} must be an http(s) URL without embedded credentials, query, or fragment")
