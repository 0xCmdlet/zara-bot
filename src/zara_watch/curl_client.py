from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class CurlResult:
    returncode: int
    stdout: str
    stderr: str


def ensure_curl_exists() -> None:
    if not shutil.which("curl"):
        print("curl not found in PATH", file=sys.stderr)
        raise SystemExit(127)


def run_curl(args: list[str]) -> CurlResult:
    p = subprocess.run(
        ["curl", *args],
        text=True,
        capture_output=True,
    )
    return CurlResult(p.returncode, p.stdout, p.stderr)