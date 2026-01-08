from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class AvailabilityEvent:
    timestamp_iso: str
    product_id: int
    store_id: int
    sku: int
    availability: str
    product_url: str


def append_event_csv(path: Path, event: AvailabilityEvent) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["timestamp_iso", "product_id", "store_id", "sku", "availability", "product_url"]
            )
        writer.writerow(
            [
                event.timestamp_iso,
                event.product_id,
                event.store_id,
                event.sku,
                event.availability,
                event.product_url,
            ]
        )


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
