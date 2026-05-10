"""OFAC SDN List 로더 — XML 파일을 파싱해 in-memory set 으로 캐시.

출처: U.S. Treasury OFAC — https://www.treasury.gov/ofac/downloads/sdn.xml
스키마: https://ofac.treasury.gov/specially-designated-nationals-list-data-formats-data-schemas

사용:
    from app.services.ofac_loader import get_loader
    loader = get_loader()
    if loader.is_match(buyer.company_name):
        ...
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent  # backend/
DEFAULT_XML_PATH = ROOT / "data" / "ofac" / "sdn.xml"

# OFAC SDN XML 의 namespace (없을 수도 있음)
NS = {"sdn": "http://tempuri.org/sdnList.xsd"}


@dataclass(frozen=True)
class OFACEntry:
    uid: str
    name: str  # primary name (firstName + lastName 또는 entity name)
    type: str  # Individual / Entity / Vessel / Aircraft
    programs: tuple[str, ...]  # SDN, IRAN, CUBA, RUSSIA, NS-PLC 등


class OFACLoader:
    """SDN XML 파일을 파싱해 빠른 매칭용 인덱스를 만들어 캐시."""

    def __init__(self, xml_path: Path = DEFAULT_XML_PATH):
        self.xml_path = xml_path
        self._entries: list[OFACEntry] = []
        self._name_index: dict[str, OFACEntry] = {}  # normalized name → entry
        self._loaded = False

    def load(self) -> int:
        """파일 파싱. 리턴: 로드된 entry 수. 파일 없으면 0 + 경고."""
        if not self.xml_path.exists():
            logger.warning(f"OFAC SDN XML not found at {self.xml_path}; loader is empty.")
            self._loaded = True
            return 0

        try:
            tree = ET.parse(self.xml_path)
        except ET.ParseError as e:
            logger.error(f"OFAC SDN XML parse error: {e}")
            self._loaded = True
            return 0

        root = tree.getroot()
        # namespace 자동 감지 (root.tag 가 '{ns}sdnList' 형식)
        ns_match = re.match(r"\{([^}]+)\}", root.tag)
        ns_prefix = "{" + ns_match.group(1) + "}" if ns_match else ""

        for entry in root.iter(f"{ns_prefix}sdnEntry"):
            uid = self._text(entry, f"{ns_prefix}uid") or "?"
            sdn_type = self._text(entry, f"{ns_prefix}sdnType") or "Unknown"

            # 이름: Entity 면 lastName 만 / Individual 은 firstName + lastName
            first = self._text(entry, f"{ns_prefix}firstName") or ""
            last = self._text(entry, f"{ns_prefix}lastName") or ""
            name = f"{first} {last}".strip() or last or first
            if not name:
                continue

            # programs (SDN, IRAN, CUBA, RUSSIA-EO14024 등)
            program_list = entry.find(f"{ns_prefix}programList")
            programs: list[str] = []
            if program_list is not None:
                for prog in program_list.findall(f"{ns_prefix}program"):
                    if prog.text:
                        programs.append(prog.text)

            ofac_entry = OFACEntry(
                uid=uid,
                name=name,
                type=sdn_type,
                programs=tuple(programs),
            )
            self._entries.append(ofac_entry)
            normalized = self._normalize(name)
            self._name_index[normalized] = ofac_entry

        self._loaded = True
        logger.info(f"OFAC SDN loaded: {len(self._entries):,} entries from {self.xml_path}")
        return len(self._entries)

    @staticmethod
    def _text(elem: ET.Element, tag: str) -> str | None:
        child = elem.find(tag)
        return child.text.strip() if (child is not None and child.text) else None

    @staticmethod
    def _normalize(name: str) -> str:
        """매칭용 표준화: lowercase + 공백 정리 + 특수문자 제거."""
        s = name.lower().strip()
        s = re.sub(r"[^\w\s]", "", s)
        s = re.sub(r"\s+", " ", s)
        return s

    def is_match(self, name: str | None) -> OFACEntry | None:
        """정확 매치 (normalized). substring 매치는 false-positive 위험으로 미사용."""
        if not name or not self._loaded:
            return None
        return self._name_index.get(self._normalize(name))

    def stats(self) -> dict[str, int]:
        """통계 — startup 로그 + audit doc 용."""
        type_counts: dict[str, int] = {}
        program_counts: dict[str, int] = {}
        for e in self._entries:
            type_counts[e.type] = type_counts.get(e.type, 0) + 1
            for p in e.programs:
                program_counts[p] = program_counts.get(p, 0) + 1
        return {
            "total": len(self._entries),
            "by_type": type_counts,
            "by_program": dict(sorted(program_counts.items(), key=lambda x: -x[1])[:10]),
        }


@lru_cache(maxsize=1)
def get_loader() -> OFACLoader:
    """싱글턴 — 첫 호출 시 XML 파싱, 이후 메모리 hit."""
    loader = OFACLoader()
    loader.load()
    return loader
