from __future__ import annotations

import json
import sys
from typing import Any

from .config import Config, Settings, now_date_like_shell
from .curl_client import run_curl


def build_urls(cfg: Config) -> tuple[str, str]:
    # NOTE: product_url is only needed for Referer + seeding cookies.
    if cfg.product_url:
        product_url = cfg.product_url
    else:
        # Fallback: keep your earlier hardcoded path, but inject the product id.
        product_url = (
            "https://www.zara.com/de/de/"
            "mantel-mit-wollanteil-und-kunstfellkragen-zw-collection-p03736251.html"
            f"?v1={cfg.product_id}"
        )

    avail_url = (
        "https://www.zara.com/itxrest/1/catalog/store/"
        f"{cfg.store_id}/product/id/{cfg.product_id}/availability"
    )
    return product_url, avail_url


def seed(product_url: str, settings: Settings) -> None:
    args: list[str] = ["-sS", "-o", "/dev/null"]

    if settings.proxy:
        args += ["--proxy", settings.proxy]

    args += [
        "-c",
        settings.cookie_jar,
        "-b",
        settings.cookie_jar,
        product_url,
        "-H",
        f"User-Agent: {settings.ua}",
        "-H",
        "Accept-Language: de-DE,de;q=0.9",
        "--connect-timeout",
        str(settings.connect_timeout),
        "--max-time",
        str(settings.max_time),
    ]

    res = run_curl(args)
    if res.returncode != 0:
        print(
            f"[{now_date_like_shell()}] seed failed (rc={res.returncode}): {res.stderr.strip()}",
            file=sys.stderr,
        )
        raise SystemExit(res.returncode)


def check(avail_url: str, product_url: str, settings: Settings) -> str:
    args: list[str] = ["-sS"]

    if settings.proxy:
        args += ["--proxy", settings.proxy]

    args += [
        "-b",
        settings.cookie_jar,
        avail_url,
        "-H",
        f"User-Agent: {settings.ua}",
        "-H",
        "Accept: */*",
        "-H",
        f"Referer: {product_url}",
        "-H",
        "Accept-Language: de-DE,de;q=0.9",
        "--connect-timeout",
        str(settings.connect_timeout),
        "--max-time",
        str(settings.max_time),
    ]

    res = run_curl(args)
    return res.stdout if res.returncode == 0 else ""


def extract_sku_states(resp: str) -> dict[int, str]:
    """
    Parse Zara availability payload and return {sku: availability_state}.

    If resp is empty/non-json/unexpected, returns {}.
    """
    if not resp:
        return {}

    try:
        data: Any = json.loads(resp)
    except json.JSONDecodeError:
        return {}

    if not isinstance(data, dict):
        return {}

    skus = data.get("skusAvailability")
    if not isinstance(skus, list):
        return {}

    out: dict[int, str] = {}
    for item in skus:
        if not isinstance(item, dict):
            continue

        sku_val = item.get("sku")
        state = item.get("availability")

        if not isinstance(state, str):
            continue

        if isinstance(sku_val, int):
            out[sku_val] = state
        elif isinstance(sku_val, str) and sku_val.isdigit():
            out[int(sku_val)] = state

    return out


def response_has_match(resp: str, cfg: Config) -> tuple[bool, str]:
    """
    Returns (is_match, detail_string).

    Zara payload example:
      {"skusAvailability":[{"sku":491652552,"availability":"in_stock"}]}
    """
    if not resp:
        return False, "empty response"

    try:
        data: Any = json.loads(resp)
    except json.JSONDecodeError:
        return False, "non-json response"

    skus = data.get("skusAvailability") if isinstance(data, dict) else None
    if not isinstance(skus, list):
        return False, "missing skusAvailability"

    for item in skus:
        if not isinstance(item, dict):
            continue

        sku_val = item.get("sku")
        state = item.get("availability")

        if isinstance(sku_val, int) and isinstance(state, str):
            if sku_val in cfg.watch_skus and state in cfg.valid_states:
                return True, f"sku={sku_val} availability={state}"

        if isinstance(sku_val, str) and sku_val.isdigit() and isinstance(state, str):
            sku_int = int(sku_val)
            if sku_int in cfg.watch_skus and state in cfg.valid_states:
                return True, f"sku={sku_int} availability={state}"

    return False, "no watched sku in valid state"
