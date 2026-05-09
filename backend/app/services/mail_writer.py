"""다국어 격식 메일 자동 작성 — 5 시나리오 × 5 언어.

docs/userflow_and_erd.md 시나리오 3 + competitor_analysis_and_features.md §2.3 차별화 2.
LLM provider 는 추상화돼 있어 .env 의 LLM_PROVIDER 로 anthropic / gemini / stub 스위치.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Literal

from app.models import Buyer, Country, ImportRule, Vehicle
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
        "Confirm vehicle availability, share key specs, ask about destination port, "
        "preferred Incoterm, payment terms, and timeline."
    ),
    "quote": (
        "Provide a formal CIF/FOB quotation. Include vehicle specs, FOB Incheon and "
        "CIF [destination port] prices when available, payment terms (T/T 100% advance), "
        "estimated shipping window, and required documents per destination country rules."
    ),
    "negotiate": (
        "Respond to a buyer's price-cut request. Acknowledge the request, explain "
        "pricing rationale (inspection grade, low mileage, options), offer a small "
        "concession or bundle if reasonable, and emphasize quality + after-shipment support."
    ),
    "shipping": (
        "Notify the buyer that the vehicle has been loaded and shipped. Include B/L "
        "number placeholder, vessel name placeholder, ETD, ETA, port of discharge, "
        "and the customs documents checklist required for arrival country."
    ),
    "dispute": (
        "Respond professionally to a buyer's complaint or claim (transit damage, "
        "missing accessory, condition mismatch). Acknowledge the concern empathetically, "
        "request photos and the inspection report, and propose a resolution path "
        "(insurance claim filing, partial refund, or replacement)."
    ),
}

SYSTEM_PROMPT_TEMPLATE = """\
You are a professional Korean used-car export company representative writing a business email.

# Sender context
- Korean SME used-car exporter (small business, 1-3 employees, Incheon-based).
- Operates on top of marketplaces like 오토위니 / BeForward.
- Default port of loading: Incheon (IIN), South Korea.

# Recipient context
- Overseas buyer in {country_name_en} ({country_code}).
- Recipient's primary business language: {language_name}.

# Scenario brief
{scenario_brief}

# Style requirements
- Tone: formal, courteous, business-appropriate for {language_name}.
- For Arabic: use Modern Standard Arabic, formal forms (أنتم).
- For Spanish: use formal "usted" register.
- For Russian: use formal "Вы".
- Use the buyer's contact name and company.
- Include all numerical facts EXACTLY as given (price, mileage, year, engine cc).
- Be concise but warm. No hard-sell language. No emoji.

# Compliance / regulatory hints (use if relevant to scenario)
{compliance_hints}

# Output contract
Respond with ONLY a single JSON object — no commentary, no markdown fences:
{{
  "subject": "<email subject in target language>",
  "body":    "<email body in target language, plain text, multi-paragraph allowed via \\n>"
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
        return SYSTEM_PROMPT_TEMPLATE.format(
            country_code=req.country.code,
            country_name_en=req.country.name_en,
            language_name=LANGUAGE_NAMES.get(req.language, req.language),
            scenario_brief=SCENARIO_BRIEFS[req.scenario],
            compliance_hints=self._compliance_hints(req),
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
            extra_context=req.extra_context or "(none)",
            scenario=req.scenario,
            language_name=LANGUAGE_NAMES.get(req.language, req.language),
        )

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
        except json.JSONDecodeError:
            # LLM 이 형식을 어겼을 때 fallback — 본문 그대로 body 로
            return "(no subject parsed)", text


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_code_fence(text: str) -> str:
    return _FENCE_RE.sub("", text)
