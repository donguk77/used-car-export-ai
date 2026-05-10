"""컴플라이언스 자동 검사 — 러시아 우회 / OFAC / Yestrade.

docs/userflow_and_erd.md 시나리오 2, used_car_export_research_v2.md §4.3.
2025.10 부산경찰청 적발 사례 자동 차단이 핵심 후크.

OFAC·Yestrade 실제 API 통합은 Phase 2. PoC 단계는 인메모리 stub.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from app.models import Buyer, Vehicle

Severity = Literal["clean", "warning", "blocked"]

# 직접 차단 국가 (대외무역법 + EU/US 제재)
DIRECT_BLOCKED_COUNTRIES: set[str] = {"RU", "BY", "KP", "IR"}

# 러시아 우회 위험 EAEU/CIS 국가 (전략물자 자가판정 대상)
RUSSIA_PROXY_COUNTRIES: set[str] = {"KG", "KZ", "TJ", "AM", "UZ"}

# OFAC/EU 제재 적용국 — direct_blocked 까진 아니지만 사전 조회·문서 추가 필요
# (시리아: 2024.5 OFAC 부분 완화, 여전히 SDN 다수; 수단: 2023~ 내전 + OFAC;
#  쿠바·미얀마 동일 카테고리)
SANCTIONED_COUNTRIES: set[str] = {"SY", "SD", "CU", "MM"}

# 우회수출 의심 차량 속성 — 「전략물자 수출입고시」 별표 2의2 (2024.2.24 개정)
RUSSIA_PROXY_ENGINE_CC_LIMIT: int = 2000
RUSSIA_PROXY_PRICE_USD_LIMIT: float = 50_000
RUSSIA_PROXY_BLOCKED_FUELS: set[str] = {"EV", "BEV", "HEV", "PHEV", "Hybrid"}

# findings #042 — OFAC SDN List 자동 통합:
# backend/data/ofac/sdn.xml (28MB, 18,947 entries) 를 startup 시 in-memory
# 로드. RUSSIA-EO14024 6,392 entries 1위 + 자동차 관련 83 entries (SERVIAUTOS,
# AUTO EXPRESS DORADOS 등). scripts/fetch_ofac_sdn.py 로 갱신.
# Demo 용 stub 은 fallback (XML 파일 없을 때).
_OFAC_SDN_DEMO_NAMES: set[str] = {
    "blocked entity sample llc",
    "test sanctioned co",
}

# findings #043 — Yestrade 우려거래자 (한국 산업통상자원부 무역안보관리원).
# 정식 통합은 사업자 인증서 + Yestrade 가입 필요 — Phase 2.
# 공개 자료: 부산경찰청 2025.10 적발 사례 (KG·KZ 우회 수출), 산자부 보도자료.
# 매칭은 buyer.tax_id 기반 (회사명 보다 정확).
_YESTRADE_DEMO_TAX_IDS: set[str] = {
    # 부산경찰청 2025.10 적발 — 키르기스스탄 우회 수출 의심 사업자 (가명)
    # 실제 사업자번호는 비공개 — 우리 stub 은 demo 용
    "DEMO-YESTRADE-001",
    "DEMO-YESTRADE-002",
}


@dataclass
class Finding:
    severity: Severity
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class ComplianceReport:
    overall: Severity
    score: int  # 0~100, 낮을수록 위험
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall,
            "score": self.score,
            "findings": [f.to_dict() for f in self.findings],
        }


def check(buyer: Buyer, vehicle: Vehicle | None = None) -> ComplianceReport:
    """바이어 + (선택) 차량 → 종합 컴플라이언스 리포트."""
    findings: list[Finding] = []

    _check_direct_blocked(buyer, findings)
    _check_sanctioned_country(buyer, findings)
    _check_russia_proxy(buyer, vehicle, findings)
    _check_ofac(buyer, findings)
    _check_yestrade(buyer, findings)
    _check_dual_use_strategic_items(buyer, vehicle, findings)

    overall = _summarize(findings)
    score = _score(findings)
    return ComplianceReport(overall=overall, score=score, findings=findings)


def _check_direct_blocked(buyer: Buyer, findings: list[Finding]) -> None:
    if buyer.country_code in DIRECT_BLOCKED_COUNTRIES:
        findings.append(
            Finding(
                severity="blocked",
                code="direct_export_blocked",
                message=f"Direct export to {buyer.country_code} prohibited (대외무역법/제재).",
            )
        )


def _check_sanctioned_country(buyer: Buyer, findings: list[Finding]) -> None:
    if buyer.country_code in SANCTIONED_COUNTRIES:
        findings.append(
            Finding(
                severity="warning",
                code="sanctioned_country",
                message=(
                    f"{buyer.country_code} subject to OFAC/EU sanctions — "
                    "pre-clearance check + consular legalization required."
                ),
            )
        )


def _check_russia_proxy(buyer: Buyer, vehicle: Vehicle | None, findings: list[Finding]) -> None:
    if buyer.country_code not in RUSSIA_PROXY_COUNTRIES:
        return

    findings.append(
        Finding(
            severity="warning",
            code="russia_proxy_country",
            message=(
                f"Buyer in {buyer.country_code} (EAEU/CIS) — Russia re-export risk; "
                "End-User Certificate recommended."
            ),
        )
    )

    if vehicle is None:
        return

    blockers: list[str] = []
    if vehicle.engine_cc and vehicle.engine_cc > RUSSIA_PROXY_ENGINE_CC_LIMIT:
        blockers.append(f">{RUSSIA_PROXY_ENGINE_CC_LIMIT}cc internal combustion")
    if vehicle.fuel_type and vehicle.fuel_type in RUSSIA_PROXY_BLOCKED_FUELS:
        blockers.append(f"fuel={vehicle.fuel_type} (HEV/EV strategic items)")
    if vehicle.list_price_usd and float(vehicle.list_price_usd) > RUSSIA_PROXY_PRICE_USD_LIMIT:
        blockers.append(f"price>${RUSSIA_PROXY_PRICE_USD_LIMIT:.0f}")

    if blockers:
        findings.append(
            Finding(
                severity="blocked",
                code="russia_proxy_strategic",
                message=(
                    "Strategic-item criteria met → 산업통상자원부 상황허가 필요: "
                    + ", ".join(blockers)
                ),
            )
        )


def _check_ofac(buyer: Buyer, findings: list[Finding]) -> None:
    """OFAC SDN match. Phase 1: in-memory XML loader (18,947 entries).
    Phase 2: 매주 cron 으로 sdn.xml 자동 갱신 + fuzzy match (현재 exact 만)."""
    name = (buyer.company_name or "").strip()
    if not name:
        return
    # 1. 정식 OFAC SDN 로더 (실 데이터 18,947 entries)
    try:
        from app.services.ofac_loader import get_loader  # lazy import — circular 방지
        match = get_loader().is_match(name)
        if match:
            findings.append(
                Finding(
                    severity="blocked",
                    code="ofac_sdn_match",
                    message=(
                        f"OFAC SDN list match: '{match.name}' "
                        f"(uid={match.uid}, type={match.type}, "
                        f"programs={','.join(match.programs)})"
                    ),
                )
            )
            return
    except Exception:  # noqa: BLE001
        pass  # loader 실패 시 stub 으로 fallback
    # 2. Demo stub fallback (XML 파일 없을 때)
    if name.lower() in _OFAC_SDN_DEMO_NAMES:
        findings.append(
            Finding(
                severity="blocked",
                code="ofac_sdn_match_stub",
                message=f"OFAC SDN match (stub): {buyer.company_name}",
            )
        )


def _check_yestrade(buyer: Buyer, findings: list[Finding]) -> None:
    if buyer.tax_id and buyer.tax_id in _YESTRADE_DEMO_TAX_IDS:
        findings.append(
            Finding(
                severity="blocked",
                code="yestrade_concerned",
                message=f"Yestrade 우려거래자: tax_id={buyer.tax_id}",
            )
        )


def _check_dual_use_strategic_items(
    buyer: Buyer, vehicle: Vehicle | None, findings: list[Finding]
) -> None:
    """신규 바이어 + 단기 거래 + 큰 차량 = HIGH 패턴 (러시아 우회 전형)."""
    if vehicle is None or buyer.country_code not in RUSSIA_PROXY_COUNTRIES:
        return
    is_new_buyer = (buyer.total_orders or 0) == 0
    is_high_value = vehicle.list_price_usd and float(vehicle.list_price_usd) > 30_000
    if is_new_buyer and is_high_value:
        findings.append(
            Finding(
                severity="warning",
                code="new_buyer_high_value",
                message=(
                    "New buyer in Russia-proxy country with high-value vehicle — "
                    "manual KYC review recommended."
                ),
            )
        )


def _summarize(findings: list[Finding]) -> Severity:
    if any(f.severity == "blocked" for f in findings):
        return "blocked"
    if any(f.severity == "warning" for f in findings):
        return "warning"
    return "clean"


def _score(findings: list[Finding]) -> int:
    score = 100
    for f in findings:
        if f.severity == "blocked":
            score -= 50
        elif f.severity == "warning":
            score -= 15
    return max(score, 0)
