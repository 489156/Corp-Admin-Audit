# 3-Layer Auditable Specification & Substantive Human Oversight (`I2/I3`)

본 문서는 `Corp-Admin-Audit`의 3대 모듈(`fin_ksox_auditor`, `leg_timeline_auditor`, `ir_disclosure_auditor`)이 공통으로 준수하는 **A·B·C 3층 감사 명세 및 `I2/I3` 인적 감독 실질성 검증 규약**을 정의합니다.

---

## 1. 3층 감사 아키텍처 (Three-Layer Audit Architecture)

| 계층 | 명칭 | 작동 원리 | 우회/비활성화 가능 여부 |
| :--- | :--- | :--- | :--- |
| **Layer A** | **사전 전제조건 하드게이트 (Precondition Hard-Gate)** | 최저임금 미달, 법정보호 휴직 불이익(`E-231`), 기시행 강행규정 위반, 원장 미연결 허위 수치 감지 시 확정 산출물 생성을 원천 차단하며, 미확정 변수는 `@soft_compute`를 통해 `🟧 ⏳ 미산정` 객체로 안전 격리함 | **불가 (Hard Block)** |
| **Layer B** | **요건별 양방향 근거 리포트 (Symmetric Evidence Report)** | (1) 재경: 12개월 인건비·4대보험·퇴직충당 요인별 증감 분해표<br>(2) 법무: 현행 사내규정 vs 개정 법령 1:1 신구조문 대비표<br>(3) IR: 초안 채택 긍정 지표 vs 원장 내 미채택 리스크 지표 1:1 대칭 카드 | 기본 제공 (Transparent by Design) |
| **Layer C** | **제거 불가능 왜곡·남용 탐지 (Non-Removable Abuse & Distortion Detection)** | (1) 재경: 목표예산 맞춤 역산 조작 지수($GSI \in [0.70, 1.05]$) 및 `W-251`<br>(2) 법무: 강행규정 개정 해태 및 독소조항 탐지<br>(3) IR: 선택적 공시 및 워싱 지수($SDI > +1.0\sigma$) 탐지 | **비활성화 절대 불가 (`allow_disable=False` 고정)** |

---

## 2. 인적 감독 실질성 게이트 (`I2/I3` Substantive Oversight Sign-Off)

단순 체크박스 클릭('확인함')에 의한 **고무도장 결재(Rubber-Stamping)**를 차단하기 위해, C층 경보가 발령된 안건을 예외 확정(Override)하려는 책임자(CFO, CLO, IRO)는 반드시 다음 2가지 구조화 필드를 최소 20자 이상 입력해야 하며, 이는 이전 로그의 해시(`prev_hash`)와 연결된 SHA-256 불변 감사 체인에 영구 기록됩니다.

- **`I2` (Independent External Evidence / 리포트 외 독립 판단 근거):** 시스템 리포트 내부 문구의 단순 복사가 아닌, 외부 회계법인/법무법인 자문 의견서 번호, 노사협의회 회의록 문서번호, 이사회 결의 번호 등 독립적 검증 근거.
- **`I3` (Counter-Argument & Remediation Plan / 반론 및 사후 보완 계획):** 경고된 리스크(충당부채 부족분, 미개정 조문, 미공시 부정 지표)를 언제·어떻게 해소할 것인지에 관한 구체적 실행 일정 및 주석 공시 계획.
