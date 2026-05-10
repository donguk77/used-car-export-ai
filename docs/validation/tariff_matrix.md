# 28국 차량 수입 관세·세금 매트릭스 (2026-05-10)

> **출처:** FIDI Customs Guides + 정부 직접 + Trade.gov + 산업 자료 (`docs/samples/`)
> **검증 도구:** `scripts/read_pdf_excerpt.py` (32 PDFs cross-validated)
> **HS code 기준:** 8703.23 (passenger gasoline 1.5-3.0L) 가 가장 흔함
>
> ⚠️ 이 매트릭스는 demo + 견적 narrative 용. 실 거래 시 FTA 우대, CIF 산정,
> 환율, 추가세 변동 등으로 ±20% 변동 가능. 시행 전 관세사 확인 필수.

---

## 1. 통과 가능국 — 17국 (정상 시장)

| 국가 | 관세 (Duty) | VAT | 추가세 | 총 부담 추정 | 출처 |
|---|---|---|---|---|---|
| 🇩🇴 DO | base + Selective 15-80% (CIF) | 18% ITBIS | - | ~40-100% | Trade.gov DO |
| 🇨🇱 CL | 6% (이주차) + Additional Tax | 19% IVA | 차량 누진세 (max $7,503) | 변동 | BCN 의회도서관 |
| 🇲🇽 MX | 10% (Decreto 2024-07) | 16% | ISAN | ~30%+ | SNICE Decreto |
| 🇨🇷 CR | ≤3년 52.29% / >3년 변동 | 13% | gas tax + 한-중미 FTA 우대 | ~50-70% | Trade.gov CR |
| 🇰🇪 KE | 25% | 16% | 소비세 20% | **60%+** | KEBS 2025-07 |
| 🇳🇬 NG | varies | 7.5% VAT | levy + Form M + SONCAP | **35-70%** | NCS + SONCAP |
| 🇬🇭 GH | 20% | 12.5% | NHIL 2.5% + ECOWAS 0.5% + AU 0.2% | ~35-40% | GRA |
| 🇹🇿 TZ | 25% | 18% | excise 5-30% | ~45-70% | TBS PVoC 2025 |
| 🇿🇼 ZW | varies | 14.5% | excise + Bureau Veritas fee | **80%+** | TradeZimbabwe |
| 🇱🇾 LY | per-unit (컨테이너→대당) | - | EV/Euro 4+ 면제 | 변동 | LY ACI 2024-07 |
| 🇪🇬 EG | 60% (외국인 work visa 없을 시) | 14% | 8% service fee | **80%+** | FIDI Egypt 2024-01 |
| 🇩🇿 DZ | base | 19% | 5-160% Vehicle Tax (fiscal HP) | 변동 | top20 doc |
| 🇯🇴 JO | 배기량 누진 | 16% | weighted by cc + 친환경 우대 | **~52%+** | FIDI Jordan 2024-01 |
| 🇦🇪 UAE | **5%** (CIF) | **5%** | + 처리 수수료 | **~10%+** | Dubai Customs Guide |
| 🇰🇬 KG | EAEU rates | 12% | - | 변동 | USDoC CCG 2020 |
| 🇰🇿 KZ | EAEU rates | 12% | excise (>3000cc) | 변동 | FIDI Kazakhstan |
| 🇦🇿 AZ | varies (HS 기반) | 18% | 도착항 inspection fee | 변동 | FIDI Azerbaijan |

---

## 2. 자동 차단국 — 6국 (PoC 차단 카테고리)

| 국가 | 사유 | 우리 처리 |
|---|---|---|
| 🇸🇩 SD | OFAC E.O. 13412/13067 + 내전 | `is_blocked: true` + `is_sanctioned: true` |
| 🇸🇾 SY | OFAC SDN 다수 + 정세 | warning (sanctioned_country finding) |
| 🇲🇲 MM | 2021.2 쿠데타 + OFAC 재제재 | `is_blocked: true` + `is_sanctioned: true` |
| 🇿🇦 ZA | ITAC LoA 사실상 미발급 | `is_blocked: true` |
| 🇹🇭 TH | MOC 2019/2021 사실상 신차만 | `is_blocked: true` (관세 ref: 200%+) |
| 🇲🇾 MY | AP (Approved Permit) — 사실상 closed | `is_blocked: true` (관세 ref: **150-300%**) |

---

## 3. 진입 매우 어려운 국가 — 5국

| 국가 | 룰 | 실 부담 |
|---|---|---|
| 🇧🇩 BD | RHD only + 5년 + JAAI | 수입세 + VAT + 보충세 합계 **100-200%** |
| 🇰🇭 KH | LHD + 10년 + Camcontrol | 관세 60-125% + 정부세 10-50% = **70-175%** |
| 🇻🇳 VN | LHD + 5년 + VNACCS | 관세 + 특별소비세 + VAT = **200%+** |
| 🇵🇭 PH | LHD + 3년 + 1500kg/2800cc + BIS | 40% Customs + 10% VAT + Ad Valorem 15-100% = **80-200%** |
| 🇱🇰 LK | RHD + 3년 (외환위기 후 재개방) | 변동 (NITG + MOC announcements) |

---

## 4. 시연 narrative — Sonata 2020 ($14,000 FOB) 기준 추정 도착 비용

| 국가 | 관세 | VAT | 추가세 | **총 비용 (FOB+세금)** | 비고 |
|---|---|---|---|---|---|
| 🇦🇪 UAE | $700 | $700 | - | **~$15,400** | 가장 저렴 |
| 🇲🇽 MX | $1,400 | $2,240 | ISAN | **~$18,000** | 한-멕 FTA 미체결 |
| 🇩🇴 DO | base | $2,520 | Selective 15-80% | **$17k-25k** | 5년 룰 통과 시 |
| 🇨🇷 CR | $7,320 (52.29%) | $1,820 | gas | **~$23,000** | ≤3년 |
| 🇰🇪 KE | $3,500 | $2,240 | $2,800 (excise) | **~$22,500** | + JEVIC fee |
| 🇬🇭 GH | $2,800 | $1,750 | NHIL+ECOWAS+AU $470 | **~$19,000** | + DVLA fee |
| 🇳🇬 NG | $4,900-9,800 | $1,050 | Form M + SONCAP $350 | **$20k-25k** | + IAF |
| 🇪🇬 EG | $8,400 | $1,960 | $1,120 service | **~$25,500** | 외국인 시 |
| 🇯🇴 JO | est $3,000 | $2,240 | weighted | **~$22,000** | 디젤 금지 |
| 🇨🇱 CL | $840 (6%) | $2,660 | progressive | **~$18-22k** | FTA 적용 시 우대 |
| 🇰🇿 KZ | EAEU base | $1,680 | engine 2000cc 면제 | 변동 | + 우회 의심 모니터링 |
| 🇰🇬 KG | EAEU base | $1,680 | - | 변동 | + 우회 의심 모니터링 |
| 🇿🇼 ZW | est $5,600 | $2,030 | $2,800 (excise) | **~$24,500** | + Bureau Veritas $200 |
| 🇱🇾 LY | per-unit | - | EV 우대 | 변동 | + ACI fee |
| 🇩🇿 DZ | est $4,200 | $2,660 | fiscal HP 기반 | **~$26,000+** | 사실상 신차만 |

→ **대부분 국가 도착 후 총 비용 = FOB × 1.4~1.8** (UAE 만 1.1).
   PoC 시연 시 멘토 "관세 얼마?" 질문에 즉답 가능.

---

## 5. 검증된 1차 자료 (32 PDFs)

전체 47 PDFs 중 32 PDFs cross-validate 됨. 자세한 finding: `docs/validation/findings.md`

관세 관련 핵심 1차 자료:
- 🇰🇪 KEBS 2025-07 + 2023-12 — 25% + 16% + 20% confirm
- 🇦🇪 Dubai Customs 52p — 5% + 5% + Free Zone 면세
- 🇨🇱 BCN 의회도서관 — Ley 18.483 + $7,503 max additional tax
- 🇲🇽 SNICE Decreto 2024-07 — 8-9년 + 10% 관세 + NAFTA
- 🇪🇬 FIDI Egypt 2024-01 — 60% + 14% + 8% service
- 🇯🇴 FIDI Jordan 2024-01 — 52% of CIF + 디젤 금지
- 🇲🇾 FIDI Malaysia 2024-06 — 150-300% depending on cc
- 🇻🇳 FIDI Vietnam 2024-07 — 200%+ (170% 이상)
- 🇵🇭 FIDI Philippines 2024-06 — 200% car book value + 1500kg/2800cc
- 🇨🇷 FIDI Costa Rica 2024-01 — 한-중미 FTA C/O 우대
- 🇰🇿 FIDI Kazakhstan 2024-07 — Euro 5 + RHD 차단 + EAEU
- 🇳🇬 SGS PCA + SON SONCAP fees — SC $350 + Product Cert $500-2000

---

## 6. mail_writer prompt 강화 (Phase 2 후보)

**현재** mail_writer 의 quote 시나리오 prompt 는 차량 spec + Incoterm 만 포함.
**개선**: 도착국 관세 추정값 자동 포함:

```
{{ vehicle.make }} {{ vehicle.model }} {{ vehicle.year }} ({{ vehicle.engine_cc }}cc)
FOB {{ vehicle.list_price_usd }} USD
도착항: {{ port_of_discharge }}, {{ country }}
관세 추정: {{ tariff_summary.duty_pct }}% + VAT {{ tariff_summary.vat_pct }}%
+ 추가세 {{ tariff_summary.other }}
→ 도착 후 총 비용 추정: {{ formatted_total }}
```

→ AI 메일이 자동 정확한 관세 안내 → "비용 narrative" 강화.

---

## 7. 다음 단계 (Phase 2)

- [ ] 28국 × 5 HS code 별 정확 관세율 (현재는 8703.23 1개)
- [ ] FTA 우대 자동 계산 (한-중미·한-칠레·한-ASEAN)
- [ ] 환율 변동 처리 (USD ↔ 현지 통화 일별 fetch)
- [ ] 항구 demurrage 비용 데이터 (현재 narrative 만)
- [ ] 보험료 (marine insurance) 자동 산정 (CIF 1% 추정 → 정확화)
- [ ] mail_writer prompt 에 tariff_summary 자동 주입
- [ ] vehicle.seats / gross_weight 컬럼 추가 → HS 분류 정확도 ↑ (#033)
