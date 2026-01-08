from __future__ import annotations

import argparse
import sys
import time

from .config import load_config, load_settings, now_date_like_shell, resolve_config_path
from .curl_client import ensure_curl_exists
from .emailer import load_email_settings, send_match_email
from .zara import build_urls, check, extract_sku_states, seed


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="zara_watch")
    p.add_argument("--config", help="Path to config.json (overrides env/default)")
    return p.parse_args()


def main() -> int:
    ensure_curl_exists()

    args = parse_args()

    settings = load_settings()
    cfg_path = resolve_config_path(args.config)
    cfg = load_config(cfg_path)

    product_url, avail_url = build_urls(cfg)
    seed(product_url, settings)

    email_settings = load_email_settings()

    # Track last known state per watched SKU; email only when transitioning to "available"
    last_state: dict[int, str | None] = {sku: None for sku in cfg.watch_skus}

    while True:
        try:
            resp = check(avail_url, product_url, settings)
        except KeyboardInterrupt:
            print("\nInterrupted.", file=sys.stderr)
            return 130

        # Blocked/expired/garbage -> reseed
        if (not resp) or ("skusAvailability" not in resp):
            print(f"[{now_date_like_shell()}] reseeding...", file=sys.stderr)
            seed(product_url, settings)
            time.sleep(settings.sleep_seconds)
            continue

        sku_states = extract_sku_states(resp)

        # Detect transitions for watched SKUs
        for sku in cfg.watch_skus:
            new = sku_states.get(sku)  # None if missing
            old = last_state.get(sku)

            became_available = (new in cfg.valid_states) and (old not in cfg.valid_states)

            if became_available:
                detail = f"sku={sku} availability={new}"
                print(f"[{now_date_like_shell()}] MATCH {detail} {resp}", flush=True)

                if email_settings:
                    try:
                        send_match_email(
                            email_settings,
                            product_url=product_url,
                            product_id=cfg.product_id,
                            store_id=cfg.store_id,
                            detail=detail,
                            raw_payload=resp,
                        )
                        print(f"[{now_date_like_shell()}] email sent: {detail}", file=sys.stderr)
                    except Exception as e:
                        print(f"[{now_date_like_shell()}] email failed: {e}", file=sys.stderr)

            # Always update last seen state
            last_state[sku] = new

        # Optional: if you want to keep logging every poll, uncomment:
        # print(f"[{now_date_like_shell()}] {resp}", flush=True)

        time.sleep(settings.sleep_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
