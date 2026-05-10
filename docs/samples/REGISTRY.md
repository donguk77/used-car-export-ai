# 공개 샘플 인덱스

이 파일은 `scripts/fetch_public_samples.py` 가 자동 생성합니다. 직접 편집하지 말고 `configs/samples_registry.yaml` 을 고치세요.

총 97 항목 · 카테고리 35 개


## algeria

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | Algeria Customs — 차량 수입 절차 | Direction Générale des Douanes (Algeria) | — | [열기](https://www.douane.gov.dz/) |
| 📄 PDF | Algeria Import — FIDI Customs Guide (2024-01) | FIDI Middle East & North Africa | 2024-01 | [원본](https://www.fidi.org/sites/default/files/public/2024-01/ALGERIA%20Import%20%E2%80%93%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/algeria/ALGERIA_Import_FIDI_Customs_Guide_2024-01.pdf) |
| 📄 PDF | Algeria Country Guide (2024-09) | IAM (International Association of Movers) | 2024-09 | [원본](https://iamovers.org/wp-content/uploads/2024/09/Algeria-Country-Guide-IAM.pdf) · [로컬](docs/samples/algeria/IAM_Algeria_Country_Guide_2024-09.pdf) |

**Notes:**

- **Algeria Customs — 차량 수입 절차** — 아랍어/프랑스어 사이트. ECTN 사전 등록 의무.
configs/rules/algeria.yaml — 사실상 신차만 통과.

## azerbaijan

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | Azerbaijan Customs — Single Window | State Customs Committee of Azerbaijan | — | [열기](https://customs.gov.az/en/) |
| 📄 PDF | Azerbaijan Import — FIDI Customs Guide (2022-01) | FIDI ADA Europe | 2022-01 | [원본](https://www.fidi.org/sites/default/files/public/2022-01/AZERBAIJAN%20Import%20%E2%80%93%20FIDI%20Customs%20Guide_0.pdf) · [로컬](docs/samples/azerbaijan/AZERBAIJAN_Import_FIDI_Customs_Guide.pdf) |
| 🔗 ref | Azerbaijan — WTO TFA Article 10.4 Members' Practices | World Customs Organization (WCO) | — | [열기](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/wto-atf/members-practices/art-10_4/azerbaijan-art-104.pdf?la=en) |
| 🔗 ref | Single Window in the Republic of Azerbaijan — UN/CEFACT Case Study | UNECE Centre for Trade Facilitation | — | [열기](https://unece.org/fileadmin/DAM/cefact/single_window/sw_cases/Download/Azerbaijan_eng.pdf) |

**Notes:**

- **Azerbaijan Customs — Single Window** — configs/rules/azerbaijan.yaml 의 pre_registration_system: Single_Window 출처.
러시아어 비즈니스 표준. 코카서스 SUV 시장.
- **Azerbaijan — WTO TFA Article 10.4 Members' Practices** — SSL local issuer cert 누락 (wcoomd.org). 브라우저 직접 다운로드 가능.
- **Single Window in the Republic of Azerbaijan — UN/CEFACT Case Study** — HTTP 403 (UA 차단). 브라우저 직접 다운로드 가능.

## bangladesh

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Bangladesh Exporter Guide (2024) | USDA Foreign Agricultural Service | 2024 | [원본](https://apps.fas.usda.gov/newgainapi/api/Report/DownloadReportByFileName?fileName=Exporter+Guide+Annual_Dhaka_Bangladesh_BG2024-0005.pdf) · [로컬](docs/samples/bangladesh/USDA_Bangladesh_Exporter_Guide_2024.pdf) |

## cambodia

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Cambodia Import — FIDI Customs Guide (2024-01) | FIDI Asia | 2024-01 | [원본](https://www.fidi.org/sites/default/files/public/2024-01/CAMBODIA%20Import%20-%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/cambodia/CAMBODIA_Import_FIDI_Customs_Guide_2024-01.pdf) |

## chile

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | Chile Customs — 차량 수입 절차 | Servicio Nacional de Aduanas de Chile (SNA) | — | [열기](https://www.aduana.cl/aduana/site/edic/base/port/inicio.html) |
| 🔗 ref | 한-칠레 FTA — C/O 양식 + 활용 가이드 | 한국-칠레 FTA 종합지원포털 | — | [열기](https://www.fta.go.kr/cl/) |
| 📄 PDF | Tributación aplicable a importación de vehículos usados (v4) | BCN — Biblioteca del Congreso Nacional de Chile | — | [원본](https://obtienearchivo.bcn.cl/obtienearchivo?id=repositorio/10221/19957/5/Tributacion+Importacion+vehiculos+usados_v4.pdf) · [로컬](docs/samples/chile/BCN_Chile_Tributacion_Vehiculos_Usados_v4.pdf) |

**Notes:**

- **Chile Customs — 차량 수입 절차** — configs/rules/chile.yaml 의 pre_registration_system: SNA 출처.
스페인어 사이트 / 영문 일부.
- **한-칠레 FTA — C/O 양식 + 활용 가이드** — FTA C/O 활용 시 차량 관세 우대. 양식이 일반 C/O 와 다름 — 별도 파일.
configs/rules/chile.yaml 의 fta_certificate_of_origin 출처.
- **Tributación aplicable a importación de vehículos usados (v4)** — 칠레 의회도서관 1차 자료. 1999년 이후 매년 reajustable (조정).
$7,503.55 USD 최대 추가세 + 차량 연식별 10% 감가.

## costa_rica

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | TICA — Sistema de Información para el Control Aduanero | Ministerio de Hacienda — TICA | — | [열기](https://www.hacienda.go.cr/contenido/12-tica) |
| 🔗 ref | 한-중미 FTA (2019 발효) — C/O 양식 + 6개국 활용 가이드 | 한국-중미 FTA 종합지원포털 | — | [열기](https://www.fta.go.kr/centralamerica/) |
| 📄 PDF | Costa Rica Import — FIDI Customs Guide (2024-01) | FIDI Latin America | 2024-01 | [원본](https://www.fidi.org/sites/default/files/public/2024-01/COSTA%20RICA%20Import%20-%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/costa_rica/COSTA_RICA_Import_FIDI_Customs_Guide.pdf) |

**Notes:**

- **TICA — Sistema de Información para el Control Aduanero** — 코스타리카 통관 시스템.
- **한-중미 FTA (2019 발효) — C/O 양식 + 6개국 활용 가이드** — 코스타리카·엘살바도르·온두라스·니카라과·파나마 + 과테말라.
FTA C/O 활용 시 자동차 관세 우대 큼.

## dominican_republic

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | Dominican Republic — Prohibited & Restricted Imports | U.S. Department of Commerce (Trade.gov) | — | [열기](https://www.trade.gov/country-commercial-guides/dominican-republic-prohibited-restricted-imports) |
| 🔗 ref | Requirements for Importing Vehicles to the Dominican Republic | Contadores Dominicanos (현지 회계법인) | — | [열기](https://contadoresdominicanos.com/en/post/customs/requirements-for-importing-vehicles-to-the-dominican-republic/) |
| 📄 PDF | Dominican Republic Import — FIDI Customs Guide (2024-10) | FIDI Latin America | 2024-10 | [원본](https://www.fidi.org/sites/default/files/public/2024-10/DOMINICAN%20REPUBLIC%20Import%20%E2%80%93%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/dominican_republic/DOMINICAN_REPUBLIC_Import_FIDI_Customs_Guide_2024-10.pdf) |

**Notes:**

- **Requirements for Importing Vehicles to the Dominican Republic** — Law 04-07 (2007.01.05) + Decree 671 (2002.08.27) 명시.
승용 5년 / 트럭 15년 / 엔진 200,000cc 한도.
- **Dominican Republic Import — FIDI Customs Guide (2024-10)** — docs/validation/findings.md

## egypt

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | Nafeza Portal — Advance Cargo Information (ACI) entry | Nafeza (Egyptian Single Window for Foreign Trade) | — | [열기](https://www.nafeza.gov.eg/en/) |
| 🔗 ref | Egyptian Customs Authority — Tariff & Procedures | Egyptian Customs Authority | — | [열기](https://www.customs.gov.eg/) |
| 🔗 ref | GOEIC — 수입 사전 검사 인증 | GOEIC (General Organization for Export & Import Control) | — | [열기](https://www.goeic.gov.eg/) |
| 📄 PDF | Egypt Import — FIDI Customs Guide (2024-01) | FIDI Middle East & North Africa | 2024-01 | [원본](https://www.fidi.org/sites/default/files/public/2024-01/EGYPT%20Import%20-%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/egypt/EGYPT_Import_FIDI_Customs_Guide.pdf) |

**Notes:**

- **Nafeza Portal — Advance Cargo Information (ACI) entry** — ACI 사전 등록 의무. 이집트 도착 모든 화물 적용. 직접 PDF 적고 JS 렌더링.
configs/rules/egypt.yaml 의 pre_registration_system: Nafeza_ACI 1차 출처.
- **Egyptian Customs Authority — Tariff & Procedures** — 차량 HS 분류 + 관세율 검색. 아랍어 우선 / 영어 일부.
- **GOEIC — 수입 사전 검사 인증** — 차량 인증 사전 검사 의무. 아랍어 사이트.

## fta_co

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | AK FTA Certificate of Origin Form | ASEAN Secretariat (Korea-ASEAN FTA) | — | [원본](https://akfta.asean.org/uploads/docs/akfta-certificate-of-origin-form.pdf) · [로컬](docs/samples/fta_co/AKFTA_certificate_of_origin_form.pdf) |
| 📄 PDF | ANNEX 5B — Format of the Certificate of Origin issued by Korea | KOTRA / fta.motir.go.kr | — | [원본](https://fta.motir.go.kr/webmodule/_PSD_FTA/sg/1/eng/CHAPTER5_Annex5B.pdf) · [로컬](docs/samples/fta_co/Korea_FTA_Annex5B_CO_format.pdf) |

## ghana

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | ICUMS — Ghana 통관 단일 시스템 | ICUMS (Integrated Customs Management System) | — | [열기](https://icums.gov.gh/) |
| 🔗 ref | GSA — Conformity Assessment for Imports | Ghana Standards Authority (GSA) | — | [열기](https://www.gsa.gov.gh/) |
| 🔗 ref | Ghana DVLA — 차량 등록·검사 | DVLA Ghana (Driver & Vehicle Licensing Authority) | — | [열기](https://www.dvla.gov.gh/) |
| 📄 PDF | Ghana Import — FIDI Customs Guide (2023-09) | FIDI Africa | 2023-09 | [원본](https://www.fidi.org/sites/default/files/public/2023-09/GHANA%20Import%20%E2%80%93%20FIDI%20Customs%20Guide_0.pdf) · [로컬](docs/samples/ghana/GHANA_Import_FIDI_Customs_Guide_2023-09.pdf) |

**Notes:**

- **ICUMS — Ghana 통관 단일 시스템** — configs/rules/ghana.yaml 의 pre_registration_system: ICUMS 출처.
Pre-Arrival Assessment Reporting (PAAR) 포함.
- **GSA — Conformity Assessment for Imports** — 차량 안전·환경 기준 검사 출처.
- **Ghana DVLA — 차량 등록·검사** — 도착 후 차량 등록 절차.

## incoterms

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Incoterms 2020 Introduction (English) — ICC Switzerland 무료 자료 | ICC Switzerland (영문 무료 introduction) | 2020 | [원본](https://www.icc-switzerland.ch/images/723e_inco2020_eng_intro.pdf) · [로컬](docs/samples/incoterms/ICC_Switzerland_Incoterms_2020_intro.pdf) |
| 🔗 ref | Incoterms 2020 본 페이지 (paywall €45/€69) | ICC International Chamber of Commerce | — | [열기](https://iccwbo.org/business-solutions/incoterms-rules/incoterms-2020/) |
| 🔗 ref | Incoterms 2020 Checklist & Flowcharts | ICC Sweden | — | [열기](https://icc.se/wp-content/uploads/2022/05/icc-incoterms-2020-checklist-int.pdf) |

**Notes:**

- **Incoterms 2020 Introduction (English) — ICC Switzerland 무료 자료** — ICC 본 PDF (€45/€69) 는 Phase 2 정식 구입 후 추가.
- **Incoterms 2020 본 페이지 (paywall €45/€69)** — 정식 책자 구매 필요.
- **Incoterms 2020 Checklist & Flowcharts** — 404 (URL 만료). icc.se 새 위치 확인 필요. ICC_Incoterms_2020_full.pdf 가 상위 자료라 우선순위 낮음.

## jordan

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | Jordan Customs eForms — 공식 폼 페이지 | Jordan Customs | — | [열기](https://www.customs.gov.jo/en/eForms.aspx) |
| 🔗 ref | Jordan Customs Tariff — HS Code 검색 | Jordan Customs | — | [열기](https://www.customs.gov.jo/en/Pages/CustomsTariff.aspx) |
| 📄 PDF | Jordan Import — FIDI Customs Guide (2024-01) | FIDI Middle East & North Africa | 2024-01 | [원본](https://www.fidi.org/sites/default/files/public/2024-01/JORDAN%20Import%20-%20FIDI%20Customs%20Guides_0.pdf) · [로컬](docs/samples/jordan/JORDAN_Import_FIDI_Customs_Guide.pdf) |

**Notes:**

- **Jordan Customs eForms — 공식 폼 페이지** — 영문 페이지 직접 PDF 적음. 아랍어 버전이 더 많음.
- **Jordan Customs Tariff — HS Code 검색** — 차량 배기량 기반 누진세 — 1500cc 이하 인기.

## kazakhstan

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | KGD — Customs procedures (English) | Kazakhstan State Revenue Committee (KGD) | — | [열기](https://kgd.gov.kz/en) |
| 🔗 ref | EAEU — Customs Tariff & Non-Tariff Regulation | Eurasian Economic Commission (EAEU) | — | [열기](https://eec.eaeunion.org/en/comission/department/dotr/) |
| 📄 PDF | Kazakhstan Import — FIDI Customs Guide (2024-07) | FIDI ADA (Asia) | 2024-07 | [원본](https://www.fidi.org/sites/default/files/public/2024-07/KAZAKHSTAN%20Import%20%E2%80%93%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/kazakhstan/KAZAKHSTAN_Import_FIDI_Customs_Guide.pdf) |
| 📄 PDF | Legal Provisions — Kazakhstan | Switzerland Global Enterprise | — | [원본](https://www.s-ge.com/sites/default/files/publication/free/legal-provisions-kazakhstan-s-ge-1703.pdf) · [로컬](docs/samples/kazakhstan/SGE_Legal_Provisions_Kazakhstan.pdf) |

**Notes:**

- **KGD — Customs procedures (English)** — 차량 통관 절차 + EAEU 통합 룰. 러시아어/카자흐어 우선.
- **EAEU — Customs Tariff & Non-Tariff Regulation** — 러시아·카자흐·키르기스·아르메니아·벨라루스 통합 룰. 우회수출 차단 핵심 출처.

## kenya

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | PUBLIC NOTICE — Validation of used motor vehicle importation documents | Kenya Bureau of Standards | 2025-07-05 | [원본](https://kebs.org/wp-content/uploads/2025/07/PUBLIC-NOTICE-VALIDATION-OF-USED-MOTOR-VEHICLES.pdf) · [로컬](docs/samples/kenya/KEBS_2025-07_validation_used_motor_vehicles.pdf) |
| 📄 PDF | NOTICE TO IMPORTERS OF USED/SECONDHAND MOTOR VEHICLES | Kenya Bureau of Standards | 2023-12-01 | [원본](https://www.kebs.org/wp-content/uploads/2023/12/NOTICE-TO-IMPORTERS-OF-USED-SECONDHAND-MOTOR-VEHICLES.pdf) · [로컬](docs/samples/kenya/KEBS_2023-12_notice_to_importers.pdf) |

## korea_customs

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | 수출신고필증 양식 (적재전, 갑지) — 한국 표준 양식 | 한국무역협회 KITA / OK FTA | — | [원본](https://okfta.kita.net/upload/downAtch?atchGbn=ONLINE&atchId=12807531&atchOrdr=0) · [로컬](docs/samples/korea_customs/KITA_export_declaration_form_loaded_pre.pdf) |
| 🔗 ref | 전자상거래 수출신고 안내 | 관세청 (Korea Customs Service) | — | [열기](https://www.customs.go.kr/common/nttFileDownload.do?fileKey=6a00ebb588d3f7e7b779add42c1e4181) |
| 📄 PDF | 유니패스 사용자 FAQ | 관세청 | 2023-11-17 | [원본](https://www.customs.go.kr/download/UNIPASS_FAQ_231117.pdf) · [로컬](docs/samples/korea_customs/UNIPASS_FAQ_2023-11-17.pdf) |
| 📄 PDF | 유니패스 FAQ (2021) | 관세청 | 2021-05-24 | [원본](https://www.customs.go.kr/download/UNIPASS_FAQ_210524.pdf) · [로컬](docs/samples/korea_customs/UNIPASS_FAQ_2021-05-24.pdf) |
| 📄 PDF | 관세청 상담 Q&A | 관세청 | — | [원본](http://www.customs.go.kr/download/_down/KCS_QnA.pdf) · [로컬](docs/samples/korea_customs/KCS_QnA.pdf) |
| 🔗 ref | 일반(비특혜) C/O 신청 양식 — 회원가입·로그인 필요 | 대한상공회의소 원산지증명센터 | — | [열기](https://cert.korcham.net/) |
| 🔗 ref | 수출신고필증 발급·조회 — 공인인증서 로그인 필요 | 관세청 UNI-PASS | — | [열기](https://unipass.customs.go.kr/csp/index.do) |
| 🔗 ref | 인보이스 서식(예시).xls — 가장 많이 사용하는 Commercial Invoice + Packing List 서식 | 삼일관세법인 | — | [열기](http://www.31customs.com/bbs/sub04_4/13841) |

**Notes:**

- **수출신고필증 양식 (적재전, 갑지) — 한국 표준 양식** — 우리 시스템이 자동 생성하는 수출신고 데이터 패키지 검증의 핵심 기준.
- **전자상거래 수출신고 안내** — 자동 다운로드 실패 (서버가 referer 검사). 브라우저로 직접 클릭해서
docs/samples/korea_customs/ 에 저장하면 됨.
- **일반(비특혜) C/O 신청 양식 — 회원가입·로그인 필요** — 인증서 로그인 필요. 발표 직전 시연용 계정 1개 만들 것.
- **수출신고필증 발급·조회 — 공인인증서 로그인 필요** — 인증서·관세사 위임 필요.
- **인보이스 서식(예시).xls — 가장 많이 사용하는 Commercial Invoice + Packing List 서식** — 페이지 클릭으로만 다운로드되는 Excel 첨부파일. 수동으로 한 번 받아 docs/samples/korea_customs/ 에 두면 좋음.

## kotra_country

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | 2026 케냐 진출전략 (디지털자료) | KOTRA Open Knowledge Repository | — | [열기](https://openknowledge.kotra.or.kr/handle/2014.oak/33862) |
| 🔗 ref | 수출, 더 이상 어렵지 않아요 — 온·오프라인 가이드북 | KOTRA | — | [열기](https://openknowledge.kotra.or.kr/handle/2014.oak/33740) |
| 🔗 ref | KOTRA — 국가별 진출전략 (요르단·UAE·이집트·카자흐 등) | KOTRA 해외경제정보드림 | — | [열기](https://news.kotra.or.kr/user/globalAllBbs/kotranews/list/2/globalBbsDataAllList.do?MENU_ID=180&CATE_TOTAL_CD=181) |

**Notes:**

- **2026 케냐 진출전략 (디지털자료)** — JS 렌더링. 직접 방문해서 PDF 다운로드.
- **KOTRA — 국가별 진출전략 (요르단·UAE·이집트·카자흐 등)** — 해외경제정보드림 → 진출전략 → 국가 선택. 신규 13개국 모두 가이드 존재.
각 국가 진출 시 시장 사이즈 + 규제 요약.

## kyrgyzstan

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Kyrgyz Republic — Country Commercial Guide (2020) | U.S. Department of Commerce — Country Commercial Guides | 2020 | [원본](https://www.export-u.com/CCGs/2020/Kyrgyz-Republic-2020-CCG.pdf) · [로컬](docs/samples/kyrgyzstan/USDoC_CCG_Kyrgyz_Republic_2020.pdf) |

## libya

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Advance Cargo Information (ACI) — Creation Manual (English) | Libya Customs Authority | 2024-07 | [원본](https://customs.gov.ly/wp-content/uploads/2024/07/ACI-Creation-English-Version.pdf) · [로컬](docs/samples/libya/Libya_ACI_2024-07_creation_manual_EN.pdf) |
| 📄 PDF | ACI — Registration for Importers (English) | Libya Customs Authority | 2024-07 | [원본](https://customs.gov.ly/wp-content/uploads/2024/07/ACI-Registration-for-Importers-English-Version.pdf) · [로컬](docs/samples/libya/Libya_ACI_2024-07_importer_registration_EN.pdf) |
| 📄 PDF | ACI — Registration for Exporters / Exporter Representatives (English) | Libya Customs Authority | 2024-07 | [원본](https://customs.gov.ly/wp-content/uploads/2024/07/ACI-Registration-for-Exporters-Exporter-Representatives-English-Version.pdf) · [로컬](docs/samples/libya/Libya_ACI_2024-07_exporter_registration_EN.pdf) |

## malaysia

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Malaysia Import — FIDI Customs Guide (2024-06) | FIDI Asia | 2024-06 | [원본](https://www.fidi.org/sites/default/files/public/2024-06/MALAYSIA%20Import%20%E2%80%93%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/malaysia/MALAYSIA_Import_FIDI_Customs_Guide_2024-06.pdf) |

## mexico

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | VUCEM — Mexico Single Window for Foreign Trade | VUCEM (Ventanilla Única de Comercio Exterior Mexicana) | — | [열기](https://www.ventanillaunica.gob.mx/vucem/index.htm) |
| 🔗 ref | SAT — Mexican Customs Procedures | SAT (Servicio de Administración Tributaria) — Aduanas | — | [열기](https://www.sat.gob.mx/aduanas) |
| 🔗 ref | Manual para la Importación y/o Exportación (스페인어) | SAT — Administración General de Aduanas | — | [열기](http://omawww.sat.gob.mx/informacion_fiscal/normatividad/Documents/Manual_Aduanas_espanol.pdf) |
| 🔗 ref | Manual de usuarios — trámite de internación temporal de vehículos | SAT — Administración General de Aduanas | — | [열기](http://omawww.sat.gob.mx/informacion_fiscal/normatividad/Documents/manual_importacion_vehiculos.pdf) |
| 📄 PDF | Decreto que regula la importación definitiva de vehículos usados (2024-07-04) | SNICE — Sistema Nacional de Información de Comercio Exterior | 2024-07-04 | [원본](https://www.snice.gob.mx/~oracle/SNICE_DOCS/Decreto_vehiculosusados-Usados_20240704-20240704.pdf) · [로컬](docs/samples/mexico/SNICE_Decreto_Vehiculos_Usados_2024-07-04.pdf) |

**Notes:**

- **VUCEM — Mexico Single Window for Foreign Trade** — 차량 사전 등록 의무. 스페인어.
- **SAT — Mexican Customs Procedures** — 일반 관세 적용 (한-멕시코 FTA 미체결).
- **Manual para la Importación y/o Exportación (스페인어)** — 자동 다운로드 실패 (sat.gob.mx 서버 외국 IP 차단 가능성).
브라우저로 직접 다운로드 후 docs/samples/mexico/ 에 저장 가능.
- **Manual de usuarios — trámite de internación temporal de vehículos** — 자동 다운로드 실패 (10060 timeout) — 수동 다운로드 가능.

## myanmar

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Myanmar Import — FIDI Customs Guide (2024-01) | FIDI Asia | 2024-01 | [원본](https://www.fidi.org/sites/default/files/public/2024-01/MYANMAR%20Import%20-%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/myanmar/MYANMAR_Import_FIDI_Customs_Guide_2024-01.pdf) |

## nigeria

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | NCS — B'Odogwu 통관 시스템 | Nigeria Customs Service (NCS) | — | [열기](https://www.customs.gov.ng/) |
| 🔗 ref | SONCAP — Standards Organisation of Nigeria Conformity Assessment Programme | Standards Organisation of Nigeria (SON) | — | [열기](https://son.gov.ng/soncap/) |
| 🔗 ref | Import Profile — Nigeria (SONCAP / NCS / Form M 통합 가이드) | Government of Pakistan — Ministry of Commerce | — | [열기](https://www.commerce.gov.pk/wp-content/uploads/2020/07/Import-Profile-Nigeria.pdf) |

**Notes:**

- **NCS — B'Odogwu 통관 시스템** — configs/rules/nigeria.yaml 의 pre_registration_system: NCS_BOdogwu 출처.
Form M (외환 송금 사전 신청) 의무.
- **SONCAP — Standards Organisation of Nigeria Conformity Assessment Programme** — 선적 전 인증 의무. Intertek/SGS/Cotecna 발행.
- **Import Profile — Nigeria (SONCAP / NCS / Form M 통합 가이드)** — HTTP 403 (UA 차단). 브라우저 직접 다운로드 가능.

## philippines

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Philippines Import — FIDI Customs Guide (2024-06) | FIDI Asia | 2024-06 | [원본](https://www.fidi.org/sites/default/files/public/2024-06/PHILIPPINES%20Import%20%E2%80%93%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/philippines/PHILIPPINES_Import_FIDI_Customs_Guide_2024-06.pdf) |

## psi

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | SGS PCA Nigeria Datasheet (Pre-Arrival Conformity Assessment) | SGS | — | [원본](https://www.sgs.com/en/-/media/sgscorp/documents/corporate/brochures/sgs-pca-nigeria-datasheet-a4-en-v21.cdn.en.pdf) · [로컬](docs/samples/psi/SGS_PCA_Nigeria_datasheet.pdf) |
| 📄 PDF | SONCAP Approved Fees (Aug 2022) | Standards Organisation of Nigeria (SON) | 2022-08 | [원본](https://son.gov.ng/wp-content/uploads/2022/08/SONCAP-Approved-Fees-Aug-2022.pdf) · [로컬](docs/samples/psi/SON_SONCAP_approved_fees_2022-08.pdf) |
| 🔗 ref | JEVIC — Pre-Shipment Inspection (Korea/Japan → Africa) | JEVIC (Japan Export Vehicle Inspection Center) | — | [열기](https://www.jevic.com/) |
| 🔗 ref | Intertek — Government Conformity Assessment (PSI) | Intertek | — | [열기](https://www.intertek.com/government/inspection/conformity-assessment/) |

**Notes:**

- **JEVIC — Pre-Shipment Inspection (Korea/Japan → Africa)** — 케냐·탄자니아·우간다·잠비아 등 의무. 한국 평택·인천에서 검사.
configs/rules/{kenya, tanzania}.yaml 의 psi_required: JEVIC 출처.
- **Intertek — Government Conformity Assessment (PSI)** — SONCAP (NG), PVOC (KE), 모잠비크 PCA 등 다국 인증.

## references_misc

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | 수출신고필증(수출면장) 보는 법 — 항목별 설명 | 트레드링스 (Tradlinx) blog | — | [열기](https://www.tradlinx.com/blog/guide/%EC%88%98%EC%B6%9C%EC%8B%A0%EA%B3%A0%ED%95%84%EC%A6%9D-%EC%88%98%EC%B6%9C%EB%A9%B4%EC%9E%A5-%EB%B3%B4%EB%8A%94-%EB%B2%95/) |
| 🔗 ref | Important information & Regulation by country for Japanese used cars | PicknBuy24 (일본 중고차 수출업체) | — | [열기](https://www.picknbuy24.com/regulation.html) |

**Notes:**

- **수출신고필증(수출면장) 보는 법 — 항목별 설명** — 양식 자체 + 각 항목 의미 한국어 해설. 우리가 자동 채울 필드 정의 시 참조.
- **Important information & Regulation by country for Japanese used cars** — 200+ 국가별 중고차 수입 규제 한눈에. 참조용 (도착국 추가 시 빠른 lookup).

## shipping_lines

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Example Maersk Bill of Lading | Maersk (via Africa CTN reference site) | — | [원본](https://africactn.com/staging/wp-content/uploads/2023/02/Example-Maersk-BIll-of-Lading.pdf) · [로컬](docs/samples/shipping_lines/Maersk_BL_example.pdf) |
| 📄 PDF | CMA CGM Paperless B/L — overview & format | CMA CGM | — | [원본](https://www.cma-cgm.com/assets/public/pdf/Paperless%20BL.pdf) · [로컬](docs/samples/shipping_lines/CMA_CGM_paperless_BL.pdf) |
| 🔗 ref | CMA CGM Shipping Instructions Format | CMA CGM | — | [열기](https://www.cma-cgm.com/static/CR/attachments/Shipping%20instructions%20format%20-%20CMA-CGM.pdf) |

**Notes:**

- **CMA CGM Shipping Instructions Format** — 404 (URL 만료). cma-cgm.com 사이트에서 "Shipping Instructions" 검색해서 새 URL 확인 필요.
대체로 Maersk_BL_example.pdf 와 CMA_CGM_paperless_BL.pdf 로 SI 양식 추정 가능.

## south_africa

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | ITAC — Import Control Application Forms (IE462 등) | ITAC — International Trade Administration Commission of South Africa | — | [열기](https://www.itac.org.za/pages/services/import--export-control/import-control/application-forms) |
| 📄 PDF | Importation of Motor Vehicles — Temporary Residents (1년 이상) | South African Embassy in Belgium | 2012-09 | [원본](http://www.southafrica.be/wp-content/uploads/2012/09/Importation-of-motor-vehicles-temporary-residents-longer-than-one-year.pdf) · [로컬](docs/samples/south_africa/SA_Embassy_Belgium_Vehicle_Import_Temporary_Residents.pdf) |
| 📄 PDF | South Africa Import — FIDI Customs Guide (2024-09) | FIDI South Africa | 2024-09 | [원본](https://www.fidi.org/sites/default/files/public/2024-09/SOUTH%20AFRICA%20Import%20%E2%80%93%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/south_africa/SOUTH_AFRICA_Import_FIDI_Customs_Guide_2024-09.pdf) |

**Notes:**

- **ITAC — Import Control Application Forms (IE462 등)** — 개별 IE462/IE362 PDF 직접 URL 은 404 (사이트 리뉴얼). Application Forms
페이지에서 최신 파일 다운로드 가능. LoA 첨부 없이 승인 안 됨.

## sri_lanka

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Sri Lanka Import — FIDI Customs Guide (2022-01) | FIDI Asia | 2022-01 | [원본](https://www.fidi.org/sites/default/files/public/2022-01/SRI%20LANKA%20Import%20%E2%80%93%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/sri_lanka/SRI_LANKA_Import_FIDI_Customs_Guide_2022-01.pdf) |
| 📄 PDF | National Imports Tariff Guide (NITG) 2024 — Preamble | Sri Lanka Customs Department | 2024-02 | [원본](https://www.customs.gov.lk/wp-content/uploads/2024/02/1.-Preamble-intergrated.pdf) · [로컬](docs/samples/sri_lanka/Sri_Lanka_Customs_NITG_2024_Preamble.pdf) |

## sudan

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | OFAC — Sudan Sanctions Program | U.S. Treasury OFAC | — | [열기](https://ofac.treasury.gov/sanctions-programs-and-country-information/sudan-sanctions) |
| 📄 PDF | OFAC FACRL-SU-01 — Sudan Sanctions Regulations | U.S. Treasury OFAC | — | [원본](https://ofac.treasury.gov/media/7246/download) · [로컬](docs/samples/sudan/OFAC_Sudan_FACRL_SU_01.pdf) |

**Notes:**

- **OFAC — Sudan Sanctions Program** — configs/rules/sudan.yaml 의 is_blocked + SANCTIONED_COUNTRIES 출처.
2023~ 내전 + OFAC 제재 영향. 직수출 자동 차단 정당화.
- **OFAC FACRL-SU-01 — Sudan Sanctions Regulations** — 2018.6.29 OFAC SSR 제거 후에도 Section 1245 NDAA 2012 + EAR 적용.
U.S. persons 거래 가능하지만 BIS 라이선스 필요 가능성.

## syria

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | Syria — Customs Laws & Import Regulations | ICRIC International (Federation of Removers) | — | [열기](https://icricinternational.org/wp-content/uploads/countries/syria/custom%20laws.pdf) |

**Notes:**

- **Syria — Customs Laws & Import Regulations** — 자동 fetch timeout — 브라우저 직접 다운로드 가능.
2025년 신규: 15년 이내 차량 허용, 디젤 금지, 외교관·외국인만 수입 가능.

## tanzania

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | TRA — TANCIS 통관 시스템 | Tanzania Revenue Authority (TRA) | — | [열기](https://www.tra.go.tz/) |
| 🔗 ref | TBS — 수입 차량 사전 신고 | Tanzania Bureau of Standards (TBS) | — | [열기](https://www.tbs.go.tz/) |
| 🔗 ref | TBS Detailed Inspection — Used Vehicles (2020) | Tanzania Bureau of Standards (TBS) | 2020 | [열기](https://tbs.go.tz/uploads/files/DI_USED_VEHICLES_-_2020.pdf) |
| 📄 PDF | Guideline for Pre-Shipment Verification of Conformity (PVoC) — 2025 | Tanzania Bureau of Standards (TBS) | 2025 | [원본](https://www.tbs.go.tz/uploads/files/GUIDELINE%20FOR%20PVOC%20PROGRAMME%20-%202025.pdf) · [로컬](docs/samples/tanzania/TBS_PVoC_Programme_Guideline_2025.pdf) |
| 📄 PDF | PVoC Harmonised Procedure (Summarised) | Tanzania Trade Portal | — | [원본](https://trade.tanzania.go.tz/media/PVoC_HARMONISED_PR0CEDURE_(SUMMARISED)_1.pdf) · [로컬](docs/samples/tanzania/TBS_PVoC_Harmonised_Procedure_Summary.pdf) |

**Notes:**

- **TRA — TANCIS 통관 시스템** — configs/rules/tanzania.yaml 의 pre_registration_system: TANCIS 출처.
- **TBS — 수입 차량 사전 신고** — TBS pre-shipment verification.
- **TBS Detailed Inspection — Used Vehicles (2020)** — SSL 인증서 hostname mismatch (tbs.go.tz vs www.tbs.go.tz).
중고차 specific 검사 매뉴얼 — RHD 의무 + roadworthiness 항목.
브라우저 직접 다운로드 가능. 우리 fetch 한 PVoC Programme Guideline
2025 + Harmonised Procedure 2종이 동일 내용 커버.

## thailand

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Thailand Import — FIDI Customs Guide (2024-07) | FIDI Asia | 2024-07 | [원본](https://www.fidi.org/sites/default/files/public/2024-07/THAILAND%20Import%20%20-%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/thailand/THAILAND_Import_FIDI_Customs_Guide_2024-07.pdf) |

## uae

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Dubai Customs — Customer Guide Booklet (English) | Dubai Customs | — | [원본](https://www.dubaicustoms.gov.ae/en/OpenData/Publications/Customer_Guide_Booklet_EN.pdf) · [로컬](docs/samples/uae/Dubai_Customs_customer_guide_EN.pdf) |
| 🔗 ref | Dubai Trade — Forms section | Dubai Trade | — | [열기](https://www.dubaitrade.ae/en/help/support-document/category/150-forms) |
| 🔗 ref | UAE FTA — VAT on Used Vehicles | UAE Federal Tax Authority | — | [열기](https://www.fta.gov.ae/en/) |
| 📄 PDF | United Arab Emirates Import — FIDI Customs Guide (2024-07) | FIDI UAE | 2024-07 | [원본](https://www.fidi.org/sites/default/files/public/2024-07/UNITED%20ARAB%20EMIRATES%20Import%20%E2%80%93%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/uae/UAE_Import_FIDI_Customs_Guide_2024-07.pdf) |

**Notes:**

- **Dubai Trade — Forms section** — 차량 declaration 포함 다양한 폼. 수동 탐색 필요.
- **UAE FTA — VAT on Used Vehicles** — 5% VAT 표준. Free Zone 거래는 면세 가능.

## vietnam

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 📄 PDF | Vietnam Import — FIDI Customs Guide (2024-07) | FIDI Asia | 2024-07 | [원본](https://www.fidi.org/sites/default/files/public/2024-07/VIETNAM%20Import%20%E2%80%93%20FIDI%20Customs%20Guide.pdf) · [로컬](docs/samples/vietnam/VIETNAM_Import_FIDI_Customs_Guide_2024-07.pdf) |

## zimbabwe

| 종류 | 제목 | 출처 | 발급일 | 링크 |
|------|------|------|--------|------|
| 🔗 ref | ZIMRA — Used Vehicle Import Procedures | Zimbabwe Revenue Authority (ZIMRA) | — | [열기](https://www.zimra.co.zw/) |
| 📄 PDF | Guide to Importing in Zimbabwe (2023-06) | Trade Zimbabwe | 2023-06 | [원본](https://tradezimbabwe.com/wp-content/uploads/2023/06/Guide_to_Importing_in_Zimbabwe.pdf) · [로컬](docs/samples/zimbabwe/TradeZimbabwe_Guide_to_Importing.pdf) |
| 📄 PDF | Zimbabwe Handbook (2018-05-17) — 환적·국경 절차 | Cross-Border Road Transport Agency (남아공) | 2018-05-17 | [원본](https://www.cbrta.co.za/uploads/files/2018-05-17-Zimbabwe-Handbook.pdf) · [로컬](docs/samples/zimbabwe/CBRTA_Zimbabwe_Handbook_2018-05-17.pdf) |

**Notes:**

- **ZIMRA — Used Vehicle Import Procedures** — ASYCUDA World 시스템 사용. Durban (남아공) 또는 Beira (모잠비크) 환적.
