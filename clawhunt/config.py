import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def build_database_url(config: Dict[str, Any]) -> str:
    db = config["database"]
    return db["url_template"].format(
        user=db["user"], password=db["password"], host=db["host"], port=db["port"], name=db["name"]
    )


def build_redis_url(config: Dict[str, Any]) -> str:
    redis = config["redis"]
    return redis["url_template"].format(host=redis["host"], port=redis["port"], db=redis["db"])


def setup_environment(config: Dict[str, Any], root: Path) -> None:
    os.environ.setdefault("DATABASE_URL", build_database_url(config))
    os.environ.setdefault("POSTGRES_DB", config["database"]["name"])
    os.environ.setdefault("POSTGRES_USER", config["database"]["user"])
    os.environ.setdefault("POSTGRES_PASSWORD", config["database"]["password"])
    os.environ.setdefault("REDIS_URL", build_redis_url(config))
    os.environ.setdefault("AUTH_TOKEN_SECRET", config["auth"]["token_secret"])
    os.environ.setdefault("CLAWHUNT_AUTH_STORE", config["auth"]["store"])
    
    oa = config["openagents"]
    os.environ.setdefault("OPENAGENTS_WORKSPACE_API_URL", oa["workspace_api_url"])
    os.environ.setdefault("OPENAGENTS_WORKSPACE_ID", oa.get("workspace_id") or "")
    os.environ.setdefault("OPENAGENTS_AGENT", oa["agent"])
    os.environ.setdefault("OPENAGENTS_POLL_INTERVAL_SECONDS", str(oa["poll_interval_seconds"]))
    os.environ.setdefault("OPENAGENTS_TIMEOUT_SECONDS", str(oa["timeout_seconds"]))


def find_venv_python(root: Path, config: Dict[str, Any]) -> Optional[str]:
    venv_dir = config["paths"]["venv_dir"]
    for path in [root / venv_dir / "Scripts" / "python.exe", root / venv_dir / "bin" / "python"]:
        if path.exists():
            return str(path)
    return None


def find_node() -> str:
    for path in [
        Path("D:/Program Files/nodejs/node.exe"),
        Path("C:/Program Files/nodejs/node.exe"),
        Path(os.environ.get("PROGRAMFILES", "")) / "nodejs" / "node.exe",
    ]:
        if path.exists():
            return str(path)
    return "node"