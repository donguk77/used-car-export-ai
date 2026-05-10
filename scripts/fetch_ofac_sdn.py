"""OFAC SDN XML 다운로드 → backend/data/ofac/sdn.xml 갱신.

매주 또는 수동 실행. Treasury.gov 가 일별 갱신.

사용법:
    py -X utf8 scripts/fetch_ofac_sdn.py
"""

from __future__ import annotations

import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "backend" / "data" / "ofac" / "sdn.xml"
SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"


def main() -> int:
    print(f"Downloading {SDN_URL} ...")
    ctx = ssl.create_default_context()
    req = urllib.request.Request(SDN_URL, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(req, timeout=180, context=ctx) as r:
            body = r.read()
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_bytes(body)
    print(f"  OK: {len(body):,} bytes saved to {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
