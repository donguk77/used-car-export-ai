"""PDF 에서 키워드 + 주변 컨텍스트 추출. YAML 룰 검증용.

사용법:
    py -X utf8 scripts/read_pdf_excerpt.py docs/samples/dominican_republic/*.pdf "year"
    py -X utf8 scripts/read_pdf_excerpt.py <pdf_path> <keyword> [--ctx 200]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pymupdf  # type: ignore[import-untyped]


def extract(pdf_path: Path, keywords: list[str], ctx: int = 200) -> None:
    print(f"\n=== {pdf_path.name} ===")
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:  # noqa: BLE001
        print(f"  ! open failed: {e}")
        return

    full_text = "\n".join(page.get_text() for page in doc)
    print(f"  pages: {doc.page_count}, chars: {len(full_text):,}")
    doc.close()

    for kw in keywords:
        pat = re.compile(re.escape(kw), re.IGNORECASE)
        matches = list(pat.finditer(full_text))
        if not matches:
            print(f"\n  [no match] {kw!r}")
            continue
        print(f"\n  [{len(matches)} matches] {kw!r}")
        for i, m in enumerate(matches[:3]):  # top 3 only
            start = max(0, m.start() - ctx)
            end = min(len(full_text), m.end() + ctx)
            snippet = full_text[start:end].strip()
            snippet = re.sub(r"\s+", " ", snippet)
            print(f"    #{i + 1}: ...{snippet}...")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("keywords", nargs="+")
    ap.add_argument("--ctx", type=int, default=200)
    args = ap.parse_args()
    extract(args.pdf, args.keywords, args.ctx)


if __name__ == "__main__":
    main()
