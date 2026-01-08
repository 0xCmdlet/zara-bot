from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

DEFAULT_CONFIG_PATH = Path("config.json")
ENV_CONFIG_PATH = "ZARA_WATCH_CONFIG"


def now_date_like_shell() -> str:
    return datetime.now().ctime()


def resolve_config_path(cli_path: str | None) -> Path:
    if cli_path:
        return Path(cli_path)
    env_path = os.getenv(ENV_CONFIG_PATH)
    if env_path:
        return Path(env_path)
    return DEFAULT_CONFIG_PATH


@dataclass(frozen=True)
class Settings:
    ua: str
    proxy: str
    cookie_jar: str
    connect_timeout: int
    max_time: int
    sleep_seconds: float


def load_settings() -> Settings:
    load_dotenv()

    ua = os.getenv(
        "UA",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36",
    )
    proxy = os.getenv("PROXY", "")
    jar = os.getenv("COOKIE_JAR", "jar.txt")

    connect_timeout = int(os.getenv("CONNECT_TIMEOUT", "10"))
    max_time = int(os.getenv("MAX_TIME", "15"))
    sleep_seconds = float(os.getenv("SLEEP_SECONDS", "5"))

    return Settings(
        ua=ua,
        proxy=proxy,
        cookie_jar=jar,
        connect_timeout=connect_timeout,
        max_time=max_time,
        sleep_seconds=sleep_seconds,
    )


@dataclass(frozen=True)
class Config:
    product_id: int
    store_id: int
    watch_skus: set[int]
    valid_states: set[str]
    product_url: str | None = None


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    try:
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[{now_date_like_shell()}] config error ({path}): {e}", file=sys.stderr)
        raise SystemExit(2)

    try:
        cfg = Config(
            product_id=int(raw["product_id"]),
            store_id=int(raw["store_id"]),
            watch_skus={int(x) for x in raw.get("watch_skus", [])},
            valid_states={str(x) for x in raw.get("valid_states", [])},
            product_url=raw.get("product_url"),
        )
    except Exception as e:
        print(f"[{now_date_like_shell()}] invalid config schema ({path}): {e}", file=sys.stderr)
        raise SystemExit(2)

    # minimal validation that prevents "runs forever but never matches"
    if not cfg.watch_skus:
        print(f"[{now_date_like_shell()}] watch_skus must not be empty", file=sys.stderr)
        raise SystemExit(2)
    if not cfg.valid_states:
        print(f"[{now_date_like_shell()}] valid_states must not be empty", file=sys.stderr)
        raise SystemExit(2)

    return cfg