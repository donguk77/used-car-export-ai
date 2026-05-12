"""다국어 격식 메일 자동 작성 — 5 시나리오 × 5 언어.

docs/userflow_and_erd.md 시나리오 3 + competitor_analysis_and_features.md §2.3 차별화 2.
LLM provider 는 추상화돼 있어 .env 의 LLM_PROVIDER 로 anthropic / gemini / stub 스위치.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Literal

from app.models import Buyer, Country, ImportRule, User, Vehicle
from app.services.llm import LLMProvider, create_provider

Scenario = Literal["inquiry", "quote", "negotiate", "shipping", "dispute"]
Language = Literal["en", "es", "ar", "ru", "fr"]

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "es": "Spanish (Castilian)",
    "ar": "Modern Standard Arabic (MSA)",
    "ru": "Russian",
    "fr": "French",
}

SCENARIO_BRIEFS: dict[str, str] = {
    "inquiry": (
        "Initial reply to a buyer's first inquiry about a specific vehicle. "
        "Confirm vehicle availability, share key specs, mention indicative landing cost "
        "if `Estimated landing cost` section is provided, ask about destination port, "
        "preferred Incoterm, payment terms, and timeline."
    ),
    "quote": (
        "Provide a formal CIF/FOB quotation. **Use the `Estimated landing cost` section "
        "below as authoritative figures** — quote FOB Incheon, freight, insurance, "
        "destination duty/VAT, and total estimated landing cost line by line. "
        "Mention payment terms (T/T 100% advance), ETA from `Estimated shipping schedule`, "
        "and required documents per destination country rules. Add a one-line disclaimer "
        "that final duty depends on customs valuation."
    ),
    "negotiate": (
        "Respond to a buyer's price-cut request. Acknowledge the request, explain "
        "pricing rationale (inspection grade, low mileage, options), reference the "
        "`Estimated landing cost` section to show that FOB price is small portion of "
        "total (most cost is destination duty/freight/VAT), offer a small concession or "
        "bundle if reasonable, and emphasize quality + after-shipment support."
    ),
    "shipping": (
        "Notify the buyer that the vehicle has been loaded and shipped. **Use the "
        "`Estimated shipping schedule` section** — vessel/voyage TBA placeholders, "
        "ETD next 3-7 days from now, ETA per the schedule, port of discharge from buyer "
        "preferred port. Include B/L number placeholder and customs documents checklist "
        "required for arrival country."
    ),
    "dispute": (
        "Respond professionally to a buyer's complaint or claim (transit damage, "
        "missing accessory, condition mismatch). Acknowledge the concern empathetically, "
        "request photos and the inspection report, and propose a resolution path "
        "(insurance claim filing, partial refund, or replacement)."
    ),
}

# 28국 관세 추정 (tariff_matrix.md 기반).
# 각 항목: (duty_pct, vat_pct, addl_pct_or_note, total_estimate_pct_or_note, source)
COUNTRY_TARIFFS: dict[str, dict[str, str | float | None]] = {
    "DO": {"duty_pct": "base", "vat_pct": 18.0, "addl": "Selective Tax 15-80%",
           "total_pct_est": "40-100%", "source": "Trade.gov DO"},
    "CL": {"duty_pct": 6.0, "vat_pct": 19.0, "addl": "Additional Tax max $7,503 USD",
           "total_pct_est": "30-50%", "source": "BCN 의회도서관 + 한-칠레 FTA"},
    "MX": {"duty_pct": 10.0, "vat_pct": 16.0, "addl": "ISAN tax",
           "total_pct_est": "30%+", "source": "SNICE Decreto 2024-07"},
    "CR": {"duty_pct": 52.29, "vat_pct": 13.0, "addl": "gas tax + 한-중미 FTA 우대 가능",
           "total_pct_est": "50-70%", "source": "Trade.gov CR"},
    "KE": {"duty_pct": 25.0, "vat_pct": 16.0, "addl": "Excise duty 20%",
           "total_pct_est": "60%+", "source": "KEBS 2025-07"},
    "NG": {"duty_pct": "varies", "vat_pct": 7.5, "addl": "Form M + SONCAP $350 + levy",
           "total_pct_est": "35-70%", "source": "NCS + SGS PCA Nigeria"},
    "GH": {"duty_pct": 20.0, "vat_pct": 12.5, "addl": "NHIL 2.5% + ECOWAS 0.5% + AU 0.2%",
           "total_pct_est": "35-40%", "source": "GRA"},
    "TZ": {"duty_pct": 25.0, "vat_pct": 18.0, "addl": "Excise 5-30%",
           "total_pct_est": "45-70%", "source": "TBS PVoC 2025"},
    "ZA": {"duty_pct": "ITAC permit only", "vat_pct": None, "addl": "사실상 import 차단",
           "total_pct_est": "blocked", "source": "FIDI ZA 2024-09"},
    "ZW": {"duty_pct": "varies", "vat_pct": 14.5, "addl": "Excise + Bureau Veritas CBCA",
           "total_pct_est": "80%+", "source": "TradeZimbabwe + CBRTA"},
    "LY": {"duty_pct": "per-unit (컨테이너→대당)", "vat_pct": None,
           "addl": "EV/Euro 4+ 면제", "total_pct_est": "변동", "source": "LY ACI 2024-07"},
    "EG": {"duty_pct": 60.0, "vat_pct": 14.0, "addl": "Service fee 8%",
           "total_pct_est": "80%+", "source": "FIDI Egypt 2024-01"},
    "DZ": {"duty_pct": "base", "vat_pct": 19.0, "addl": "Vehicle Tax 5-160% (fiscal HP)",
           "total_pct_est": "변동, 사실상 신차만", "source": "FIDI DZ + IAM"},
    "JO": {"duty_pct": "weighted by cc", "vat_pct": 16.0, "addl": "친환경 우대 / 디젤 금지",
           "total_pct_est": "52%+", "source": "FIDI Jordan 2024-01"},
    "AE": {"duty_pct": 5.0, "vat_pct": 5.0, "addl": "+ 처리 수수료 / Free Zone 면세 가능",
           "total_pct_est": "10%+", "source": "Dubai Customs Guide 52p"},
    "SY": {"duty_pct": "varies", "vat_pct": None, "addl": "OFAC 제재 모니터링",
           "total_pct_est": "변동", "source": "ICRIC + 정세"},
    "KG": {"duty_pct": "EAEU rates", "vat_pct": 12.0, "addl": "우회 수출 모니터링",
           "total_pct_est": "변동", "source": "USDoC CCG 2020"},
    "KZ": {"duty_pct": "EAEU rates", "vat_pct": 12.0,
           "addl": "Excise (>3000cc 자국 룰) + 우회 모니터링",
           "total_pct_est": "변동", "source": "FIDI Kazakhstan + EAEU"},
    "AZ": {"duty_pct": "varies (HS 기반)", "vat_pct": 18.0, "addl": "도착항 inspection fee",
           "total_pct_est": "변동", "source": "FIDI Azerbaijan + WCO"},
    "MM": {"duty_pct": "n/a (blocked)", "vat_pct": None, "addl": "OFAC + 군부 정세",
           "total_pct_est": "blocked", "source": "OFAC FACRL-SU-01 + FIDI MM"},
    "KH": {"duty_pct": "60-125%", "vat_pct": 10.0, "addl": "Govt tax 10-50% (type/age/engine)",
           "total_pct_est": "70-175%", "source": "FIDI Cambodia 2024-01"},
    "VN": {"duty_pct": "70-150% (cars)", "vat_pct": 10.0, "addl": "Excise 10-150%",
           "total_pct_est": "200%+", "source": "FIDI Vietnam 2024-07"},
    "TH": {"duty_pct": "n/a (closed)", "vat_pct": None, "addl": "MOC 2019/2021 사실상 신차만",
           "total_pct_est": "200%+ (블록)", "source": "FIDI Thailand 2024-07"},
    "PH": {"duty_pct": 40.0, "vat_pct": 12.0, "addl": "Ad Valorem 15-100% (배기량)",
           "total_pct_est": "80-200%", "source": "FIDI Philippines 2024-06"},
    "MY": {"duty_pct": "150-300% (AP only)", "vat_pct": None,
           "addl": "AP (Approved Permit) 사실상 미발급",
           "total_pct_est": "blocked", "source": "FIDI Malaysia 2024-06"},
    "BD": {"duty_pct": "varies", "vat_pct": 15.0, "addl": "Supplementary duty (배기량)",
           "total_pct_est": "100-200%", "source": "USDA + JAAI"},
    "LK": {"duty_pct": "varies (재개방 후)", "vat_pct": 18.0, "addl": "Luxury tax 변동",
           "total_pct_est": "변동", "source": "Sri Lanka Customs NITG 2024"},
    "SD": {"duty_pct": "n/a (blocked)", "vat_pct": None, "addl": "OFAC 제재 + 내전",
           "total_pct_est": "blocked", "source": "OFAC FACRL-SU-01"},
}

# 28국 운임 + ETA 추정 (shipping_matrix.md 기반).
# 각 항목: (transit_days_min, transit_days_max, roro_usd_min, roro_usd_max, container_usd_min, container_usd_max, port)
COUNTRY_SHIPPING: dict[str, dict[str, str | int | None]] = {
    "DO": {"transit_min": 28, "transit_max": 35, "roro_min": 2000, "roro_max": 2800,
           "container_min": 3500, "container_max": 4500, "port": "Rio Haina",
           "note": "Panama Canal 경유"},
    "CL": {"transit_min": 22, "transit_max": 28, "roro_min": 2200, "roro_max": 3000,
           "container_min": 3800, "container_max": 5000, "port": "San Antonio",
           "note": "Pacific 직항"},
    "MX": {"transit_min": 14, "transit_max": 18, "roro_min": 1200, "roro_max": 1800,
           "container_min": 2500, "container_max": 3500, "port": "Manzanillo",
           "note": "Pacific 직항, 가장 짧음"},
    "CR": {"transit_min": 25, "transit_max": 32, "roro_min": 2000, "roro_max": 2800,
           "container_min": 3500, "container_max": 4500, "port": "Limón",
           "note": "Limón 카리브 / Caldera 태평양"},
    "KE": {"transit_min": 24, "transit_max": 30, "roro_min": 1500, "roro_max": 2000,
           "container_min": 2500, "container_max": 3500, "port": "Mombasa",
           "note": "RoRo 강세, JEVIC 검사 한국"},
    "NG": {"transit_min": 28, "transit_max": 33, "roro_min": 1800, "roro_max": 2400,
           "container_min": 3000, "container_max": 4000, "port": "Lagos (Apapa)",
           "note": "Suez 경유, 항만 혼잡 +14일"},
    "GH": {"transit_min": 30, "transit_max": 35, "roro_min": 1800, "roro_max": 2400,
           "container_min": 3000, "container_max": 4000, "port": "Tema",
           "note": "Suez 경유"},
    "TZ": {"transit_min": 26, "transit_max": 32, "roro_min": 1600, "roro_max": 2200,
           "container_min": 2800, "container_max": 3800, "port": "Dar es Salaam",
           "note": "JEVIC + TBS 검사 한국"},
    "ZA": {"transit_min": 30, "transit_max": 35, "roro_min": 1800, "roro_max": 2500,
           "container_min": 3200, "container_max": 4200, "port": "Durban",
           "note": "환적 허브 (잠비아·짐바브웨)"},
    "ZW": {"transit_min": 37, "transit_max": 45, "roro_min": None, "roro_max": None,
           "container_min": 4000, "container_max": 5500, "port": "Durban transit + road",
           "note": "내륙국 — 모잠비크 Beira 도 가능"},
    "LY": {"transit_min": 32, "transit_max": 40, "roro_min": 1800, "roro_max": 2400,
           "container_min": 3500, "container_max": 4500, "port": "Misrata",
           "note": "정세 + 보험료 ↑↑"},
    "EG": {"transit_min": 25, "transit_max": 28, "roro_min": 1400, "roro_max": 2000,
           "container_min": 2800, "container_max": 3800, "port": "Alexandria",
           "note": "Suez 인접"},
    "DZ": {"transit_min": 30, "transit_max": 35, "roro_min": 1600, "roro_max": 2200,
           "container_min": 3000, "container_max": 4000, "port": "Algiers",
           "note": "Suez + 지중해 횡단"},
    "JO": {"transit_min": 22, "transit_max": 28, "roro_min": 1400, "roro_max": 1800,
           "container_min": 2500, "container_max": 3500, "port": "Aqaba",
           "note": "단일항, ACID 사전등록"},
    "AE": {"transit_min": 18, "transit_max": 22, "roro_min": 1200, "roro_max": 1800,
           "container_min": 2200, "container_max": 3000, "port": "Jebel Ali",
           "note": "재수출 허브, 가장 저렴+빠름"},
    "SY": {"transit_min": 28, "transit_max": 35, "roro_min": 2500, "roro_max": 3500,
           "container_min": 4500, "container_max": 5500, "port": "Latakia",
           "note": "정세 + OFAC 모니터링 + 보험료 ↑↑"},
    "KG": {"transit_min": 35, "transit_max": 50, "roro_min": None, "roro_max": None,
           "container_min": 4000, "container_max": 6000, "port": "Bandar Abbas (transit)",
           "note": "Vladivostok 시베리아 횡단철도 + Almaty 환적"},
    "KZ": {"transit_min": 30, "transit_max": 45, "roro_min": None, "roro_max": None,
           "container_min": 3500, "container_max": 5500, "port": "Almaty (rail)",
           "note": "Vladivostok 시베리아 횡단철도 + EAEU 통합"},
    "AZ": {"transit_min": 40, "transit_max": 50, "roro_min": None, "roro_max": None,
           "container_min": 4500, "container_max": 6500, "port": "Baku",
           "note": "Caspian 해상 + 환적"},
    "MM": {"transit_min": 15, "transit_max": 22, "roro_min": None, "roro_max": None,
           "container_min": None, "container_max": None, "port": "Yangon (blocked)",
           "note": "OFAC 차단"},
    "KH": {"transit_min": 7, "transit_max": 12, "roro_min": 700, "roro_max": 1200,
           "container_min": 1500, "container_max": 2200, "port": "Sihanoukville",
           "note": "동남아 가장 짧음"},
    "VN": {"transit_min": 5, "transit_max": 10, "roro_min": 600, "roro_max": 1000,
           "container_min": 1200, "container_max": 2000, "port": "Hai Phong",
           "note": "최단 거리 (2,500 NM)"},
    "TH": {"transit_min": 8, "transit_max": 12, "roro_min": None, "roro_max": None,
           "container_min": None, "container_max": None, "port": "Laem Chabang (closed)",
           "note": "MOC 2019/2021 사실상 closed"},
    "PH": {"transit_min": 5, "transit_max": 8, "roro_min": 700, "roro_max": 1200,
           "container_min": 1400, "container_max": 2000, "port": "Manila",
           "note": "BIS Authority 사전 발급 필요"},
    "MY": {"transit_min": 10, "transit_max": 14, "roro_min": None, "roro_max": None,
           "container_min": None, "container_max": None, "port": "Port Klang (closed)",
           "note": "AP 라이선스 사실상 미발급"},
    "BD": {"transit_min": 18, "transit_max": 24, "roro_min": 1200, "roro_max": 1800,
           "container_min": 2000, "container_max": 2800, "port": "Chittagong",
           "note": "JAAI 사전 검사"},
    "LK": {"transit_min": 20, "transit_max": 26, "roro_min": 1400, "roro_max": 2000,
           "container_min": 2200, "container_max": 3000, "port": "Colombo",
           "note": "외환위기 후 보수적 (재개방)"},
    "SD": {"transit_min": None, "transit_max": None, "roro_min": None, "roro_max": None,
           "container_min": None, "container_max": None, "port": "Port Sudan (blocked)",
           "note": "OFAC E.O. 13412/13067"},
}

SYSTEM_PROMPT_TEMPLATE = """\
You are a professional Korean used-car export company representative writing a business email.

# Sender (use these EXACT values in the closing/signature — DO NOT use placeholders like [Company Name])
- Company name: {sender_company}
- Sender email: {sender_email}
- Sender phone: {sender_phone}
- Port of loading: {sender_port}, South Korea

# Recipient context
- Overseas buyer in {country_name_en} ({country_code}).
- Recipient's primary business language: {language_name}.

# Scenario brief
{scenario_brief}

# Style requirements — VERY IMPORTANT
- Tone: formal, courteous, business-appropriate for {language_name}.
- For Arabic: use Modern Standard Arabic, formal forms (أنتم).
- For Spanish: use formal "usted" register.
- For Russian: use formal "Вы".
- Use the buyer's contact name and company.
- Include all numerical facts EXACTLY as given (price, mileage, year, engine cc).
- Be concise but warm. No hard-sell language. No emoji.
- **CRITICAL: Body MUST be 250-400 words maximum** (longer responses get truncated).
- Escape newlines in JSON body as \\n (NOT actual newlines inside the string).

# Plain-text formatting — STRICT (this is a plain-text email, not a webpage)
- DO NOT use markdown bold (**text**, __text__) — write words plainly.
- DO NOT use markdown bullet stars (* item) — use a plain dash with space ("- item").
- DO NOT use markdown pipe tables (| col | col |) — write tables as label-value lines:
  Example for cost breakdown (use this exact label-value style):
    FOB Incheon ............ USD 10,500
    Ocean freight (RoRo) ... USD 2,100
    Marine insurance ....... USD   105
    --------------------------------------
    Total CIF Misrata ...... USD 12,705
- DO NOT use markdown headings (## Section). Use plain "Section:" label and a blank line.
- DO NOT leave bracketed placeholders like [Your Company] — fill in the sender info from above.

# Compliance / regulatory hints (use if relevant to scenario)
{compliance_hints}

# Output contract
Respond with ONLY a single JSON object — no commentary, no markdown fences:
{{
  "subject": "<email subject in target language, plain text — no markdown>",
  "body":    "<email body in target language, plain text — no markdown — multi-paragraph via \\n>"
}}
"""

USER_PROMPT_TEMPLATE = """\
# Vehicle
- Make / Model / Year: {make} {model} {year}
- VIN: {vin}
- Body type: {body_type}
- Engine: {engine_cc}cc {fuel_type}
- Transmission: {transmission}
- Steering: {steering}
- Mileage: {mileage_km} km
- Exterior color: {color_exterior}
- HS code: {hs_code}
- List price (USD): {list_price_usd}

# Buyer
- Company: {buyer_company}
- Contact person: {buyer_contact}
- Country: {buyer_country}
- Preferred port: {preferred_port}
- Preferred Incoterm: {preferred_incoterm}
- Preferred payment: {preferred_payment}

# Estimated landing cost (use as authoritative figures for `quote` scenario)
{landing_cost_block}

# Estimated shipping schedule (use for `shipping` scenario)
{shipping_block}

# Additional context
{extra_context}

Write the {scenario} email now in {language_name}. Respond with ONLY the JSON object.
"""


@dataclass
class MailRequest:
    scenario: Scenario
    language: Language
    vehicle: Vehicle
    buyer: Buyer
    country: Country
    rules: list[ImportRule] | None = None
    extra_context: str = ""
    sender: User | None = None  # 발신자 회사 정보 — signature placeholder 방지


@dataclass
class MailDraft:
    subject: str
    body: str
    scenario: str
    language: str
    provider: str
    model: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class MailWriter:
    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider or create_provider()

    def draft(self, req: MailRequest) -> MailDraft:
        system = self._render_system(req)
        user = self._render_user(req)
        result = self.provider.complete(system=system, user=user)
        subject, body = self._parse_json(result.text)
        # LLM 이 명시적 'no markdown' 지시를 자주 어김 (Gemini 2.5 특히 quote 시
        # markdown table 강제). 코드 단계서 강제 클리닝 + placeholder 치환.
        subject = _strip_markdown(subject)
        body = _strip_markdown(body)
        body = _replace_signature_placeholders(body, req.sender)
        return MailDraft(
            subject=subject,
            body=body,
            scenario=req.scenario,
            language=req.language,
            provider=result.provider,
            model=result.model,
        )

    # ── prompt rendering ────────────────────────────────────────────
    def _render_system(self, req: MailRequest) -> str:
        # sender fallback — User 객체 없으면 데모 default
        s = req.sender
        return SYSTEM_PROMPT_TEMPLATE.format(
            country_code=req.country.code,
            country_name_en=req.country.name_en,
            language_name=LANGUAGE_NAMES.get(req.language, req.language),
            scenario_brief=SCENARIO_BRIEFS[req.scenario],
            compliance_hints=self._compliance_hints(req),
            sender_company=(s.company_name if s else "Korean Used-Car Export Co."),
            sender_email=(s.email if s else "export@example.kr"),
            sender_phone=(s.phone if s and s.phone else "+82-32-555-0000"),
            sender_port=(s.port_of_loading if s else "Incheon"),
        )

    def _render_user(self, req: MailRequest) -> str:
        v = req.vehicle
        b = req.buyer
        return USER_PROMPT_TEMPLATE.format(
            make=v.make or "?",
            model=v.model or "?",
            year=v.year or "?",
            vin=v.vin or "?",
            body_type=v.body_type or "?",
            engine_cc=v.engine_cc or "?",
            fuel_type=v.fuel_type or "?",
            transmission=v.transmission or "A/T",
            steering=v.steering or "?",
            mileage_km=v.mileage_km or "?",
            color_exterior=v.color_exterior or "?",
            hs_code=v.hs_code or "?",
            list_price_usd=v.list_price_usd or "?",
            buyer_company=b.company_name or "?",
            buyer_contact=b.contact_person or "?",
            buyer_country=b.country_code,
            preferred_port=b.preferred_port or "?",
            preferred_incoterm=b.preferred_incoterm or "CIF",
            preferred_payment=b.preferred_payment or "T/T 100% advance",
            landing_cost_block=self._landing_cost_block(req),
            shipping_block=self._shipping_block(req),
            extra_context=req.extra_context or "(none)",
            scenario=req.scenario,
            language_name=LANGUAGE_NAMES.get(req.language, req.language),
        )

    def _landing_cost_block(self, req: MailRequest) -> str:
        """관세 추정 → AI quote/negotiate 시나리오에 인용."""
        cc = req.country.code
        t = COUNTRY_TARIFFS.get(cc)
        if not t:
            return f"- (no tariff data for {cc})"
        fob = float(req.vehicle.list_price_usd or 0)
        ship = COUNTRY_SHIPPING.get(cc, {})
        # freight 평균값 (RoRo 우선, 없으면 container)
        freight: int | None = None
        if ship.get("roro_min") is not None and ship.get("roro_max") is not None:
            freight = (int(ship["roro_min"]) + int(ship["roro_max"])) // 2
            freight_kind = "RoRo"
        elif ship.get("container_min") is not None and ship.get("container_max") is not None:
            freight = (int(ship["container_min"]) + int(ship["container_max"])) // 2
            freight_kind = "20FT Container"
        insurance = round(fob * 0.01, 2) if fob else None  # CIF 통상 1%

        lines = [f"- Destination: {cc}",
                 f"- FOB Incheon (Korea): USD {fob:,.0f}" if fob else "- FOB: ?",
                 f"- Freight ({freight_kind} 추정): USD {freight:,}" if freight else "- Freight: 추정 어려움",
                 f"- Marine insurance (CIF 1% 통상): USD {insurance:,.0f}" if insurance else ""]
        # 관세
        duty = t.get("duty_pct")
        vat = t.get("vat_pct")
        addl = t.get("addl")
        total_pct = t.get("total_pct_est")
        lines.extend([
            f"- Import duty: {duty}{'%' if isinstance(duty, (int, float)) else ''}",
            f"- VAT: {vat}%" if vat is not None else "- VAT: n/a",
            f"- Additional taxes: {addl}",
            f"- Total estimated landing burden: {total_pct} of CIF",
            f"- Source: {t.get('source')}",
        ])
        return "\n".join(line for line in lines if line)

    def _shipping_block(self, req: MailRequest) -> str:
        """ETA + 운임 + 항구 → AI shipping/inquiry 시나리오 인용."""
        cc = req.country.code
        s = COUNTRY_SHIPPING.get(cc)
        if not s:
            return f"- (no shipping data for {cc})"
        port = s.get("port") or "?"
        tmin, tmax = s.get("transit_min"), s.get("transit_max")
        eta = f"{tmin}-{tmax} days" if tmin and tmax else "n/a"
        roro = (f"USD {s['roro_min']:,}-{s['roro_max']:,}"
                if s.get("roro_min") and s.get("roro_max") else "n/a")
        cont = (f"USD {s['container_min']:,}-{s['container_max']:,}"
                if s.get("container_min") and s.get("container_max") else "n/a")
        return "\n".join([
            f"- Port of loading: Incheon (IIN), South Korea",
            f"- Port of discharge: {port}",
            f"- Estimated transit: {eta}",
            f"- RoRo freight (1 sedan, ~1.5m³): {roro}",
            f"- Container 20FT freight: {cont}",
            f"- Note: {s.get('note', '')}",
            "- Vessel/Voyage: TBA (B/L 발급 시 확정)",
        ])

    def _compliance_hints(self, req: MailRequest) -> str:
        c = req.country
        hints: list[str] = []
        if c.consular_legalization:
            hints.append(f"- {c.code} requires consular legalization of C/O & invoice.")
        if c.pre_registration_system:
            hints.append(f"- {c.code} requires pre-registration via {c.pre_registration_system}.")
        if c.is_high_risk:
            hints.append(f"- {c.code} flagged HIGH RISK; mention compliance/KYC carefully.")
        if c.is_russia_proxy_risk:
            hints.append(
                f"- {c.code} is in Russia-proxy risk zone; do NOT propose re-export to RU."
            )
        rules = req.rules or list(c.rules)
        for r in rules:
            if r.psi_required:
                hints.append(f"- Pre-shipment inspection required: {', '.join(r.psi_required)}.")
            if r.doc_translation_lang:
                hints.append(f"- Documents must be translated to {r.doc_translation_lang}.")
        return "\n".join(hints) if hints else "- (no specific compliance hints)"

    # ── parsing ──────────────────────────────────────────────────────
    def _parse_json(self, text: str) -> tuple[str, str]:
        cleaned = _strip_code_fence(text).strip()
        try:
            payload = json.loads(cleaned)
            return str(payload.get("subject", "")), str(payload.get("body", ""))
        except json.JSONDecodeError as e:
            # LLM 이 형식을 어김 — 라우트 레이어에서 502 로 변환됨
            raise MailDraftParseError(
                f"LLM did not return valid JSON ({e.msg} at pos {e.pos}). "
                f"Raw response preview: {text[:200]!r}"
            ) from e


class MailDraftParseError(ValueError):
    """LLM 응답이 약속한 JSON 형식이 아닐 때."""


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_code_fence(text: str) -> str:
    return _FENCE_RE.sub("", text)


# ── Post-processing: LLM 의 markdown 출력을 강제로 plain-text 화 ─────
_MD_BOLD_RE = re.compile(r"\*\*([^\*\n]+?)\*\*")
_MD_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*|\s)([^\*\n]+?)(?<!\s)\*(?!\*)")
_MD_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_MD_BULLET_RE = re.compile(r"^(\s*)\*\s+", re.MULTILINE)


def _strip_markdown(text: str) -> str:
    """LLM 이 어긴 markdown 을 plain-text 로 강제 변환.

    제거 대상:
      **bold** → bold
      *italic* → italic   (단, 단독 별표 bullet 은 -)
      ## 헤딩  → 헤딩      (# 자체만 제거)
      * item   → - item
      | col | col |  → 표 행을 'label: value' 또는 'label  value' 로 평탄화
    """
    if not text:
        return text
    # 1. bold/italic
    text = _MD_BOLD_RE.sub(r"\1", text)
    text = _MD_ITALIC_RE.sub(r"\1", text)
    # 2. heading 마커
    text = _MD_HEADING_RE.sub("", text)
    # 3. bullet '* item' → '- item'
    text = _MD_BULLET_RE.sub(r"\1- ", text)
    # 4. pipe table → label  value 형식
    text = _flatten_pipe_table(text)
    return text


def _flatten_pipe_table(text: str) -> str:
    """| col1 | col2 | 형식 표를 평탄한 'label  value' 라인으로 변환.

    Gemini 가 quote 시나리오에서 자주 사용. 메일 클라이언트는 markdown
    table 렌더링 안 하므로 raw `|` 가 깨져 보임.
    """
    lines = text.split("\n")
    out: list[str] = []
    in_table = False
    for line in lines:
        s = line.strip()
        # separator row: |---|---| 또는 | :--- | :--- |
        if re.match(r"^\|[\s:\-\|]+\|$", s):
            in_table = True
            continue  # 구분선 자체는 제거
        if s.startswith("|") and s.endswith("|") and "|" in s[1:-1]:
            cells = [c.strip() for c in s.strip("|").split("|")]
            cells = [c for c in cells if c]
            if len(cells) >= 2:
                # 첫 cell = label, 마지막 cell = value, 가운데는 하이픈으로
                label = cells[0]
                value = cells[-1]
                # 라벨 너비 맞춰 도트로 정렬 (28자)
                pad = max(2, 32 - len(label))
                out.append(f"{label} {'.' * pad} {value}")
                in_table = True
                continue
        in_table = False
        out.append(line)
    return "\n".join(out)


# 회사명 placeholder — LLM 이 자주 쓰는 패턴 (영/한/아랍/노/스/러시아 등)
_PLACEHOLDER_PATTERNS = [
    r"\[اسم\s+شرك[تي|ك]م\]",          # Arabic: [내/우리 회사명]
    r"\[اسم\s+الشركة\]",              # Arabic: [회사명]
    r"\[شركتك(?:م)?\]",                # Arabic short variant
    r"\[Your\s+Company(?:\s+Name)?\]",
    r"\[Company\s+Name\]",
    r"\[\[?\s*회사명\s*\]\]?",
    r"\[Nombre\s+de\s+la\s+Empresa\]",  # Spanish
    r"\[Название\s+компании\]",         # Russian
    r"\[Nom\s+de\s+l['’]entreprise\]",  # French
]


def _replace_signature_placeholders(body: str, sender: User | None) -> str:
    """LLM 이 signature 에 [회사명] 같은 placeholder 를 남기면 실제 회사명으로 치환."""
    if not sender or not sender.company_name:
        return body
    for pat in _PLACEHOLDER_PATTERNS:
        body = re.sub(pat, sender.company_name, body, flags=re.IGNORECASE)
    return body
