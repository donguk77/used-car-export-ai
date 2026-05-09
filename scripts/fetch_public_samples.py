"""configs/samples_registry.yaml 의 공개 샘플·1차 자료를 docs/samples/ 로 다운로드.

사용법:
    py -X utf8 scripts/fetch_public_samples.py
    py -X utf8 scripts/fetch_public_samples.py --category kenya  # 특정 카테고리만
    py -X utf8 scripts/fetch_public_samples.py --force          # 기존 파일 덮어쓰기

산출:
    docs/samples/<category>/<filename>     # type=pdf
    docs/samples/REGISTRY.md               # 모든 항목 (pdf + ref) 인덱스
"""

from __future__ import annotations

import argparse
import ssl
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "configs" / "samples_registry.yaml"
SAMPLES_DIR = ROOT / "docs" / "samples"

# 일부 정부 사이트가 default Python User-Agent 를 차단해서 브라우저 UA 사용.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Connection": "close",
}

# customs.go.kr 등 일부 사이트는 약한 TLS 설정 → 호환 컨텍스트.
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.set_ciphers("DEFAULT@SECLEVEL=1")


def load_registry() -> list[dict]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return list(data.get("samples") or [])


def download(url: str, dest: Path, timeout: int = 30) -> int:
    """단일 URL → 파일. 다운로드한 바이트 수 리턴, 실패 시 raise."""
    req = urllib.request.Request(url, headers=HEADERS)
    ctx = _SSL_CTX if url.startswith("https://") else None
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        body = resp.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    return len(body)


def fetch_pdf(entry: dict, *, force: bool) -> tuple[str, str]:
    """리턴: (status, message) — status ∈ {ok, skip, fail}."""
    category = entry["category"]
    filename = entry["filename"]
    dest = SAMPLES_DIR / category / filename

    if dest.exists() and not force:
        return "skip", f"already exists ({dest.stat().st_size:,} bytes)"

    try:
        size = download(entry["url"], dest)
        return "ok", f"{size:,} bytes"
    except urllib.error.HTTPError as e:
        return "fail", f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return "fail", f"URL error: {e.reason}"
    except Exception as e:  # noqa: BLE001
        return "fail", f"{type(e).__name__}: {e}"


def write_registry_md(entries: list[dict]) -> None:
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_cat[e["category"]].append(e)

    lines: list[str] = []
    lines.append("# 공개 샘플 인덱스\n")
    lines.append(
        "이 파일은 `scripts/fetch_public_samples.py` 가 자동 생성합니다. "
        "직접 편집하지 말고 `configs/samples_registry.yaml` 을 고치세요.\n"
    )
    lines.append(f"총 {len(entries)} 항목 · 카테고리 {len(by_cat)} 개\n")

    for cat in sorted(by_cat):
        lines.append(f"\n## {cat}\n")
        lines.append("| 종류 | 제목 | 출처 | 발급일 | 링크 |")
        lines.append("|------|------|------|--------|------|")
        for e in by_cat[cat]:
            kind = "📄 PDF" if e.get("type") == "pdf" else "🔗 ref"
            title = e.get("title", "(no title)")
            org = e.get("source_org", "?")
            issued = e.get("issued", "—")
            if e.get("type") == "pdf":
                local = f"docs/samples/{cat}/{e['filename']}"
                link = f"[원본]({e['url']}) · [로컬]({local})"
            else:
                link = f"[열기]({e['url']})"
            lines.append(f"| {kind} | {title} | {org} | {issued} | {link} |")

        # 카테고리별 notes 섹션
        notes_entries = [e for e in by_cat[cat] if e.get("notes")]
        if notes_entries:
            lines.append("\n**Notes:**\n")
            for e in notes_entries:
                lines.append(f"- **{e.get('title','?')}** — {e['notes'].strip()}")

    out = SAMPLES_DIR / "REGISTRY.md"
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n  ✓ wrote {out.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", help="이 카테고리만 받기")
    parser.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")
    args = parser.parse_args()

    entries = load_registry()
    if args.category:
        entries = [e for e in entries if e["category"] == args.category]

    pdf_entries = [e for e in entries if e.get("type") == "pdf"]
    ref_entries = [e for e in entries if e.get("type") == "ref"]

    print(f"  Registry: {len(entries)} entries  ({len(pdf_entries)} pdf, {len(ref_entries)} ref)")
    print()

    counts = {"ok": 0, "skip": 0, "fail": 0}
    failures: list[str] = []
    for e in pdf_entries:
        status, msg = fetch_pdf(e, force=args.force)
        counts[status] += 1
        icon = {"ok": "✓", "skip": "·", "fail": "✗"}[status]
        cat = e["category"]
        fn = e["filename"]
        print(f"  {icon} [{cat}] {fn:55s}  {msg}")
        if status == "fail":
            failures.append(f"{cat}/{fn}: {msg}")

    print(f"\n  download: {counts['ok']} new, {counts['skip']} cached, {counts['fail']} failed")

    write_registry_md(entries)

    if failures:
        print("\n  ✗ failures:")
        for f in failures:
            print(f"    - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
