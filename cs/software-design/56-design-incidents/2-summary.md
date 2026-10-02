# software-design/56-design-incidents — 실사건: Therac-25(1985–87) · Healthcare.gov 출시(2013) — 정리 (힌트)

## 해결하는 문제

leaf 노트는 설계 결함을 **하나씩** 다룬다.\
공유 가변 상태는 19번, 불법 상태를 표현할 수 있는 타입은 24번, 계약은 23번, 에러 메시지는 17번이다.\
실제 사고에서는 결함 여러 개가 **한 줄로 이어져** 터진다.\
그리고 고리마다 "이건 다른 곳이 막아 주겠지"라는 가정이 하나씩 있다.

```text
  leaf 노트:  [재사용 가정] [공유 변수 경쟁] [카운터=플래그] [암호 같은 오류] [통합 지점 용량] [끝에서 끝 시험]  <- 각각 따로
  실사건:
    Therac-25       재사용한 코드 + 하드웨어 인터록 제거 -> 공유 변수 경쟁 -> 오류는 "pause", P 키로 진행 -> 과다 조사
    Healthcare.gov  요구·정책 미확정 -> 모듈별 계약·각자 용량 산정 -> 공유 진입점(EIDM) 병목 -> 끝에서 끝 시험 없이 출시
```

쉬운 예: 낡은 건물에 새 층을 올리는 공사다.\
옛 건물에는 기둥마다 보강재가 있었다. 새 설계는 "계산상 충분하다"며 보강재를 뺐다.\
옛 층에서 가져온 자재에는 "보강재가 있다"는 전제가 적혀 있지 않았다.\
새 층이 흔들리고 나서야 그 전제가 드러났다.

똑같은 구조다.\
Therac-25는 앞 기종(Therac-6·Therac-20)의 소프트웨어를 이어받았다. 앞 기종에는 하드웨어 안전 인터록이 있었다. Therac-25는 그 인터록 상당수를 소프트웨어에 맡겼다.\
같은 결함이 Therac-20에서는 퓨즈를 끊는 데서 그쳤고, Therac-25에서는 환자에게 과다 조사로 이어졌다(Leveson–Turner 1993).

이 노트는 공개된 조사 문서로 두 사건을 복원한다.
- **Therac-25(1985-06 ~ 1987-01)**: 방사선 치료기. 알려진 사고 6건, 모두 대량 과다 조사였고 사망·중상이 있었다. 1차 출처: Leveson–Turner, "An Investigation of the Therac-25 Accidents", IEEE Computer 26(7), 1993-07, pp. 18–41.
- **Healthcare.gov(2013-10-01 출시)**: 미국 연방 건강보험 거래소 웹사이트. 출시 첫날 신청서를 내고 플랜을 고른 사람이 6명이었다. 1차 출처: 미 GAO-14-694(2014-07-30), HHS OIG OEI-06-14-00350(2016-02).

  - *인터록(interlock)*: 조건이 맞지 않으면 위험한 동작을 물리적으로 막는 장치다. 예: 문이 열리면 전자레인지가 켜지지 않는다.
  - *조사 문서의 성격*: Leveson–Turner는 소송 기록과 미국·캐나다 규제 기관 자료 등 여러 출처에서 정보를 모았고, 원 문서 자체가 옳다는 보장은 없다고 적었다(논문 서두). AECL이 소프트웨어 설계에 독점권을 주장해, 소프트웨어 구조는 사고·수리·설계 변경 문서로 그린 "대략의 그림"이라고 밝혔다(사이드바). GAO·OIG는 정부 감사 기관 보고서다. 이 노트의 시각·수치는 이 세 문서에서만 가져왔고, 설계 관점의 해석은 "해석"으로 표시했다.

## 동작·원리

### 사건 1 — Therac-25 (1985-06 ~ 1987-01)

#### 무엇이 어디에 있었나 (원문)

```text
  Therac-6  (X선 전용, CGR 소프트웨어)
     │
     ├──> Therac-20 (CGR 직원이 이중 모드용으로 고침.
     │              X선 + 전자선, 독립 하드웨어 보호 회로·기계 인터록 유지)
     │        ┆
     │        ┆  전자선 모드용 루틴 일부를 빌려 옴
     │        ┆  (QA 책임자는 몰랐던 것으로 보임, 사고 관련 버그로 뒤에 드러남)
     │        ▼
     └──> Therac-25 ("같은 Therac-6 패키지"에서 시작. 20과 25는 공통 기반에서 독립 개발)
          (25 MeV 광자 + 여러 에너지의 전자선, 처음부터 컴퓨터 제어 전제)
            - 기존 하드웨어 안전 장치·인터록을 모두 복제하지는 않음 -> 안전을 소프트웨어가 더 많이 맡음
            - PDP-11 어셈블리, 한 사람이 몇 년에 걸쳐 작성, 전용 실시간 실행기(선점 스케줄러)
            - 작업은 0.1초마다 시작. 작업끼리 공유 변수로만 소통
            - "공유 메모리 동시 접근을 허용하고, 공유 변수 외에는 실질적 동기화가 없으며,
               변수의 test와 set이 나눌 수 없는(indivisible) 연산이 아니었다"
```

- 설치 대수: 11대(미국 5, 캐나다 6). 1987년 대대적 설계 변경을 위해 리콜됐다. 변경에는 소프트웨어 오류에 대비한 하드웨어 안전 장치가 포함됐다.
- 1983년 3월 AECL(제조사)의 안전 분석은 결함 트리 형태였고 소프트웨어를 사실상 뺐다. 가정 중 하나: "프로그래밍 오류는 광범위한 시험으로 줄었다. 남은 소프트웨어 오류는 분석에 포함하지 않는다."
- Therac-20에서도 관련 문제가 나중에 발견됐다. Therac-20은 하드웨어 인터록이 있어 부상이 없었고, 그래서 Therac-25 사고 전까지 아무도 알아채지 못했다.

  - *결함 트리(fault tree)*: "과다 조사" 같은 사고를 맨 위에 두고, 그것을 일으키는 사건을 AND·OR로 아래로 펼친 그림이다. 각 사건에 확률을 붙여 위험을 계산한다.

#### 타임라인 (원문, 날짜는 논문 표기)

```text
  1985-06-03  Kennestone(조지아주 Marietta) — 10 MeV 전자선 치료 중 환자가 "엄청난 열"을 느낌.
              물리학자 추정 15,000~20,000 rad 1~2회 (보통 1회 치료량은 200 rad 범위)
  1985-07-26  Hamilton(온타리오) — 5초 뒤 "H-tilt" 오류, 화면 "no dose", "treatment pause".
              운영자가 P(진행) 키로 네 번 더 시도. AECL 기술자 추정 13,000~17,000 rad
              AECL은 원인을 재현하지 못한 채 턴테이블 마이크로스위치를 의심, 수정 뒤
              "위험률이 최소 다섯 자릿수(five orders of magnitude) 개선"이라고 주장
  1985-12     Yakima(워싱턴주) — 오른쪽 엉덩이에 줄무늬 홍반. 당시 "원인 불명"으로 정리
  1986-03-21  Tyler(텍사스, ETCC) — "Malfunction 54"("dose input 2"), 화면은 6 MU 전달(요청 202 MU).
              운영자가 P 키로 진행. 사후 모의로 1초 안에 약 1 cm 면적에 16,500~25,000 rad 추정.
              환자는 5개월 뒤 사망. AECL은 재현 실패, "과다 조사는 불가능" — 기계는 4월 7일 복귀
  1986-04-11  Tyler 두 번째 — 다시 Malfunction 54. 환자는 1986-05-01 사망.
              병원 물리학자 Fritz Hager가 운영자와 함께 재현: "빠른 편집"이 열쇠.
              AECL 측정: 중심에서 25,000 rad
  1986-04-15  AECL이 사용자에게 "커서 UP 키의 키캡을 빼고 접점을 절연 테이프로 고정하라"는 서한
  1986-05-02  FDA가 Therac-25를 결함 제품으로 선언, 시정 조치 계획(CAP) 요구
  1987-01-17  Yakima 두 번째 — 처방 86 rad(필름 4 + 3 rad, 광자 79 rad). AECL 예비 측정으로
              필드라이트 위치에서 회당 4,000~5,000 rad, 두 번이면 8,000~10,000 rad 가능. 4월 사망
  1987-02-10  FDA "Notice of Adverse Findings" — 정기 치료 사용 중단 권고
  1987-07-21  AECL 다섯 번째이자 마지막 CAP — 하드웨어 단일 펄스 차단, 턴테이블 전위차계,
              선량 관련 중단은 모두 "suspend"(재입력 필수), 의미 있는 오류 메시지 등
```

- Hamilton 사고 원인은 끝내 확정되지 않았다. FDA의 Ed Miller는 Yakima 두 번째 사고와 같은 문제였을 것으로 보았다(1987-01-26 전화 회의 기록).
- 논문은 Hamilton 사고 뒤 캐나다 당국(CRPB)이 dose-rate 오작동 시 "pause" 대신 "suspend"로 바꾸라고 요구했지만, AECL은 재시도 최대 횟수를 5회에서 3회로 줄이는 데 그쳤다고 적는다.

#### 메커니즘 1 — Tyler: "입력 끝" 플래그와 8초 창 (원문 설명의 그림)

```text
  키보드 처리 작업                          Treat 작업의 Datent(자료 입력) 단계          Hand 작업
  ───────────────                          ──────────────────────────────          ────────
  운영자 'x'(X선) 입력, 명령 줄로 이동
  MEOS = [상위: X선 매개변수 | 하위: X선]
  "입력 완료" 플래그 = 1  ─────────────▶  플래그 보고 MEOS 상위 바이트로 매개변수 설정
                                          Magnet: 굽힘 자석 설정 (약 8초)
                                            └ Ptime이 첫 실행에서 "자석 설정 중" 플래그를 지움
                                              → 이후 편집 요청을 더는 확인하지 않음
  (8초 안에) 커서 UP, 'e'(전자선)로 수정,
  다시 명령 줄
  MEOS = [상위: 전자선 | 하위: 전자선]                                                   하위 바이트를 보고
                                          Datent는 이미 끝남 → 바뀐 상위 바이트를 못 봄       턴테이블을 전자선 위치로
                                          ─────────────────────────────────────────────
                                          결과: 매개변수는 X선(고전류), 턴테이블은 전자선 위치(표적 없음)
```

- 원문 요지
  - "입력 완료" 플래그는 커서가 명령 줄에 **한 번 닿았다**는 뜻이지 **지금 거기 있다**는 뜻이 아니었다. 논문은 이것을 잠재적 경쟁 조건(race condition)이라고 불렀다.
  - 매개변수(MEOS 상위 바이트)와 턴테이블 위치(하위 바이트)를 서로 다른 작업이 따로 읽었다. 둘이 어긋났는지 검사하는 코드는 없어 보였다.
  - 수정: 굽힘 자석 플래그를 Ptime 끝이 아니라 Magnet 끝(모든 자석 설정 뒤)에서 지운다. 커서가 명령 줄에 **없음**을 나타내는 공유 변수를 하나 더 두어, 켜져 있으면 Datent 단계에 머문다.
- 운영자 화면에는 수정한 값이 보였다. 기계 내부 상태만 옛 값이었다.

  - *MEOS(mode/energy offset)*: 모드·에너지를 담은 2바이트 공유 변수. 상위 바이트는 Datent가 매개변수를, 하위 바이트는 Hand 작업이 콜리메이터·턴테이블을 정하는 데 썼다.
  - *경쟁 조건*: 결과가 작업들이 실행되는 순서·시점에 따라 달라지는 결함이다.

#### 메커니즘 2 — Yakima: 1바이트 카운터를 "검사 필요" 플래그로 (원문 설명의 그림)

```text
  Set-Up Test (수백 번 다시 스케줄됨)              Housekeeper 작업의 Lmtchk
  ──────────────────────────────────              ─────────────────────────
  Class3 = Class3 + 1   (1바이트, 255 다음은 0)
                                                  if (Class3 != 0) Chkcol()   // 상부 콜리메이터 위치 검사
                                                  else  검사 건너뜀            // F$mal 9번 비트를 갱신 안 함
  if (F$mal == 0) → 치료 진행(Set-Up Done)

  256번째 패스마다 Class3 == 0  →  그 순간 운영자가 "set"을 누르면
  콜리메이터가 필드라이트 위치(표적 없음)인데도 25 MeV 전자선이 주사(scanning) 없이 켜짐
```

- 원문: "Class3 변수는 1바이트라 최댓값이 255다. 그래서 256번째 패스마다 넘쳐 0이 된다. 그때는 상부 콜리메이터를 검사하지 않는다."
- AECL의 수정: Set-Up Test가 Class3를 **증가시키지 않고 0이 아닌 고정값으로 설정**하게 바꿨다.
- 이 결함은 Tyler와 다른 코드 경로였다. AECL QA 책임자는 Tyler 뒤 계획했던(아직 설치 안 된) 변경이 있었다면 Yakima 사고를 막았을 것이라고 말했다(FDA 내부 보고서 인용).

#### 설계 관점으로 다시 보기 (해석)

| 사건 속 사실(원문) | 설계 결함의 이름 | 관련 leaf |
|---|---|---|
| Therac-6·20 코드를 재사용, 그 코드는 하드웨어 인터록이 있는 기계에서만 검증됨. 같은 결함이 Therac-20에서는 퓨즈만 끊음 | 재사용 모듈의 **숨은 가정**(보호 장치가 밖에 있다). 계약에 적히지 않은 전제 — unknown unknowns | [01-2](../01-complexity/2-summary.md) · [23-1](../23-design-by-contract/2-summary.md) |
| 작업 사이 소통이 공유 변수뿐, test와 set이 원자적이지 않음 | **공유 가변 상태**와 동기화 부재 — 실행 순서·타이밍 결합 | [19-4](../19-immutability-and-value-objects/2-summary.md) · [31-2](../31-antipatterns/2-summary.md) · [05](../05-connascence/2-summary.md) |
| "입력 완료" 플래그가 "한 번 닿음"과 "지금 있음"을 구분 못 함 | 상태를 **약한 표현**(플래그 하나)으로 — 의미가 다른 두 상태가 같은 값 | [24](../24-types-as-invariants/2-summary.md) |
| 1바이트 카운터를 "0이 아니면 검사"로 씀 | 불법·의도치 않은 상태(0)가 **표현 가능**한 인코딩. 의미 결합 | [24-3](../24-types-as-invariants/2-summary.md) · [05-2](../05-connascence/2-summary.md) |
| 매개변수와 턴테이블 위치의 불일치를 검사하는 코드 없음 | **불변식 검사 부재** — "모드와 기계 위치가 일치한다"를 아무도 소유하지 않음 | [23](../23-design-by-contract/2-summary.md) |
| "Malfunction 54", 설명서에 뜻 없음. "pause"는 P 키 하나로 진행 | 오류를 **삼키기 쉬운 처리** — fail-fast 대신 재시도 허용, 사람이 해석할 수 없는 메시지 | [15](../15-error-handling-design/2-summary.md) · [17-4](../17-error-messages-and-log-level-policy/2-summary.md) |
| 이온 챔버가 포화해 오히려 낮은 선량을 표시 | 측정이 실패하면 "정상"처럼 보이는 설계 — 실패의 가시화 실패(논문: 소프트웨어가 운영자에게 "거짓말"을 했다) | [15](../15-error-handling-design/2-summary.md) |
| 결함 트리가 소프트웨어를 빼고 근거 없는 확률을 붙임 | 품질 속성 분석이 실제 위험 요소를 제외 | [46](../46-quality-attributes-and-tradeoffs/2-summary.md) |
| 논문 교훈: "설계 결정의 이유를 기록해 이후 수정에서 무심코 되돌리지 않게" | 결정 근거 기록 | [47](../47-architecture-decision-records/2-summary.md) |
| 논문 교훈: 편집 후 재입력 생략·캐리지 리턴으로 확인 같은 **사용 편의** 기능이 안전을 깎음 | 품질 속성의 맞교환(사용성 vs 안전)을 명시하지 않음 | [46-1](../46-quality-attributes-and-tradeoffs/2-summary.md) |

- Leveson–Turner의 결론은 "소프트웨어 버그 하나"가 아니다. 논문은 기여 요인으로 관리 부실과 사고 보고 추적 절차 부재, 소프트웨어 과신과 하드웨어 인터록 제거, 미흡했던 것으로 보이는 소프트웨어 공학 관행, 비현실적 위험 평가를 든다. 그리고 "결함을 하나씩 고치는 것으로는 안전 문제가 풀리지 않았다"고 적는다.
- 해석: 설계 영역의 말로 옮기면, Therac-25는 **방어 계층 하나(하드웨어 인터록)를 빼면서 그 계층이 막아 주던 결함들의 계약을 다시 쓰지 않은** 사례다. 코드는 재사용됐지만 그 코드가 기대던 환경은 재사용되지 않았다.

### 사건 2 — Healthcare.gov 출시 (2013-10-01)

#### 무엇이 어디에 있었나 (원문)

```text
                      소비자 (브라우저)
                            │
                            ▼
               HealthCare.gov 웹사이트 (사용자 인터페이스)
                            │
                ┌───────────┴───────────┐
                ▼                       │
     EIDM — 계정 생성·신원 확인          │   모든 방문자가 여기를 거쳐야 함(QSSI는 이를 몰랐다고 진술)
     (QSSI, 여러 CMS 프로그램용으로 제작) │
                │                       │
                ▼                       ▼
     FFM — 연방 거래소 핵심 (CGI Federal)                  데이터 허브 (QSSI)
       · 자격 심사·가입(eligibility & enrollment)  ◀────▶   SSA·IRS·DHS·VA·DOD·Peace Corps·OPM,
       · 플랜 관리(plan management)                         주(州) 기관, 보험사와 정보 라우팅·검증
       · 재무 관리(financial management)
       저장소: MarkLogic NoSQL (2012-01 CMS가 기술 지시서로 지정)
```

- 계약: Federal Marketplace 계약 60건 중 55건이 기존 계약을 통해 발주됐다(OIG). FFM 구축에는 4개사가 제안했고 CGI Federal만 기술적으로 수용 가능했다(OIG).
- 첫 가입 기간에 연방 거래소를 쓴 주는 36개(주 협력 거래소 7 포함)였다(OIG).
- GAO: CMS는 "지원할 주의 수와 구성, 그리고 무엇보다 잠재 가입자 수 같은 핵심 기술 요구가 알려지지 않은 상태에서" FFM·데이터 허브 작업 지시를 냈다.

  - *FFM(federally facilitated marketplace)*: 주가 직접 거래소를 만들지 않은 경우 연방이 운영하는 거래소 시스템이다.
  - *EIDM(Enterprise Identity Management)*: 계정 생성과 신원 확인을 맡은 공용 시스템이다. Medicare 등 여러 CMS 프로그램을 위해 만들었다(OIG).

#### 타임라인 (원문)

```text
  2010-03     PPACA — 2014-01-01까지 건강보험 거래소 설립 요구
  2011-09     CMS가 FFM 개발 계약 (FFM·허브는 2011년, EIDM은 2012년 계약)
  2012-01     CMS가 기술 지시서(TDL)로 MarkLogic 플랫폼 사용 지시. CGI Federal은 경험 부족을 이유로 우려 표명
  2013-03     계약 문서 추정: 2013-09까지 FFM 65%, 데이터 허브 75%만 준비될 것
  2013-04     요구 분석·설계 단계 연장 (요구가 아직 바뀌는 중). CMS가 계약자에게 서면 우려 전달(4월·11월)
  2013-09     FFM 운영 준비 검토(ORR)를 3월에서 9월로 미룬 끝에 부분적으로만 실시 — 개발·시험은 그 뒤에도 계속
  2013-10-01  출시. 동시 사용자 250,000 — 미국 CTO는 예상 동시 사용자의 5배라고 설명.
              출시 2시간 안에 장애 시작. 첫날 신청서를 내고 플랜을 고른 소비자는 6명
  2013-11~12  가동률: 11월 초 42% → 11월 말 90% 이상. 12-01까지 개선. 동시 사용자 35,000명 이상을 다운 없이 처리
  2014-01     다른 회사(Accenture Federal Services)와 9,100만 달러 계약 — 2014-06 기준 1억 7,500만 달러 이상으로 증가
  2014-03-31  첫 가입 기간 종료 — 540만 명이 연방 거래소에서 플랜 선택
```

- 비용(GAO, 2011-09 ~ 2014-02): FFM 계약 의무액 5,600만 달러 → 2억 900만 달러 이상, 데이터 허브 3,000만 달러 → 약 8,500만 달러.
- GAO: "CMS는 Healthcare.gov가 성능 요구를 충족하는지 검증하지 않은 채 출시했다." 작업 지시 개발 기간이 끝날 때(2014-02) FFM 핵심 구성요소 셋 중 완료된 것은 플랜 관리 하나였다.
- OIG가 꼽은 가장 결정적 요인은 **명확한 리더십의 부재**였다. 결정 지연, 과업 불명확, 문제 규모를 알아채지 못한 것이 여기서 나왔다고 보았다.

#### 메커니즘 — 각자 맞는 부품, 맞지 않는 전체 (원문)

- **공유 진입점의 용량**: CMS와 계약자는 가장 시급한 성능 문제를 EIDM으로 보았다. OIG 인용 — "작은 1차선 진입로를 큰 고속도로에 붙인 것 같았다." QSSI는 모든 방문자가 EIDM을 거쳐야 한다는 것을 몰랐고 그래서 필요 용량을 낮게 잡았다고 진술했다. QSSI는 "anonymous shopper" 도구가 계정 없이 플랜을 보게 해 줄 것으로 믿었고, 그 도구가 출시 뒤로 미뤄져 EIDM 부하가 커졌다고도 진술했다. 그러나 CMS는 나중에 그 도구도 EIDM 계정 생성을 요구했을 것이라고 확인했다(OIG 33쪽).
- **병목이 다른 결함을 가림**: CMS 기술 관계자 — "FFM이 사실 더 큰 문제였지만, EIDM 문제를 넘기 전에는 FFM 코딩 문제의 규모를 볼 수 없었다."
- **끝에서 끝 시험 없음**: OIG — 부품이 너무 늦게 도착해 CMS는 부품끼리의 문제를 찾는 끝에서 끝(end-to-end) 시험을 끝내지 못했다. 한 계약자: "만들어지지 않은 것은 시험할 수 없다."
- **시스템 통합 책임자 없음**: 별도 통합 책임자를 두자는 제안이 여러 번 나왔지만 CMS 기술 리더십은 CMS 자신이 그 역할을 한다고 보았다. CGI Federal은 시스템 간 상호 의존을 풀려고 업무 요구 정의를 도와야 했다고 진술했다.
- **각자의 관제**: 출시 전 계약자들은 자기 시스템만 감시했고 다른 시스템을 볼 수 없었다. 시스템들은 함께 동작하는데 관제는 따로였다.
- **늦은 정책 결정**: 예 — "가족 중 한 명만 신원 확인이 필요한가, 모두 필요한가"가 개발 후반에 정해져 기술 명세가 바뀌었다(OIG).

#### 설계 관점으로 다시 보기 (해석)

| 사건 속 사실(원문) | 설계 결함의 이름 | 관련 leaf |
|---|---|---|
| 잠재 가입자 수를 모르는 채 발주, 성능 요구 검증 없이 출시 | 품질 속성을 **측정 가능한 시나리오**로 적지 않음 | [46-3](../46-quality-attributes-and-tradeoffs/2-summary.md) |
| 모든 방문자가 EIDM을 거친다는 사실을 EIDM 개발사가 모름 | 모듈 경계의 **계약에 부하·사용 조건이 없음**. 공유 진입점이 단일 병목 | [23](../23-design-by-contract/2-summary.md) · [45-3](../45-monolith-vs-microservices/2-summary.md) |
| EIDM은 여러 CMS 프로그램용 공용 시스템 | 여러 소비자가 공유하는 공통 모듈 — 어느 소비자의 부하·요구를 기준으로 만들었는지가 계약에 없음 | [11-2](../11-when-to-abstract/2-summary.md) |
| 정책·요구가 개발 후반까지 바뀜 | 변동성이 큰 결정이 경계 뒤에 숨겨지지 않고 여러 시스템에 퍼짐 | [04](../04-decompose-by-change/2-summary.md) |
| 부품은 각자 개발·시험, 끝에서 끝 시험 미완 | 부품 단위 초록이 전체 동작을 보증하지 않음 | [13-1](../13-refactoring/2-summary.md) · [41](../41-architecture-fitness-rules/2-summary.md) |
| 저장소 플랫폼을 계약 범위 안의 기술 지시서(TDL — 계약 비용을 바꿀 수 없는 지시)로 지정, 계약자의 경험 부족 우려에도 진행 | 맥락·결과를 검토·기록하지 않은 아키텍처 결정 | [47](../47-architecture-decision-records/2-summary.md) |
| 계약자마다 따로 관제, 전체를 보는 사람 없음 | 통합 지점의 관측 부재 | [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md) |
| 복구: "ruthless prioritization", 통합 관제 대시보드, 과부하 때 "waiting room" | 범위 축소, 통합 관측, 부하 차단 | [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md) |

- 해석: 설계 영역의 말로 옮기면, Healthcare.gov는 **부품 경계가 사람·계약 경계와 겹쳤는데 경계를 넘는 가정(누가 어디를 지나가나, 얼마나 오나)은 아무 계약에도 적히지 않은** 사례다. GAO·OIG는 주로 계약·관리 실패로 기술했다. 이 노트는 그것을 경계 계약의 관점으로 다시 읽었을 뿐이다.

### 두 사건을 나란히 (해석)

| | Therac-25 | Healthcare.gov |
|---|---|---|
| 각 부품은 | 앞 기종에서 "검증된" 코드 | 각 계약자가 자기 범위에서 개발 |
| 적히지 않은 가정 | 하드웨어 인터록이 밖에서 막아 준다 | 진입점 부하가 이 정도다, 부품은 제때 붙는다 |
| 가정이 깨진 지점 | 인터록 제거 + 공유 변수 경쟁 + 카운터 넘침 | 모든 방문자가 EIDM 통과 + 끝에서 끝 시험 없음 |
| 오류가 보인 모양 | 암호 같은 "Malfunction 54", "pause" 뒤 P 키, 포화로 낮게 표시된 선량 | 출시 2시간 안 장애, 첫날 6명 |
| 처음 내린 원인 판단 | 마이크로스위치(Hamilton), "과다 조사는 불가능"(Tyler) | 공개 설명은 "예상의 5배 접속" — OIG는 핵심 성능 문제도 있었다고 봄 |
| 결국 필요했던 것 | 소프트웨어와 독립인 하드웨어 차단, 오류 시 suspend, 의미 있는 메시지 | 통합 책임·통합 관제, 범위 축소, 대기실(부하 차단) |

- 두 사건 모두 첫 원인 판단이 좁았다. Leveson–Turner는 "근거 없이 사고 원인이 정해졌다고 믿은 것"과 "특정 오류 하나를 고치면 사고가 막힌다는 가정"을 실수로 꼽았다. OIG도 문제가 방문자 수만이 아니라 웹사이트 성능의 핵심 문제였다고 적었다.

### 실행 확인: Yakima의 1바이트 카운터 모형

이 노트는 실험 의무 대상이 아니다(명세 I7 — 종합 55·56 제외). 원래 코드는 PDP-11 어셈블리이고 공개되지 않았다. 아래는 논문 설명만 옮긴 **모형**이며 원 코드의 재현이 아니다.

```java
// Leveson–Turner 1993의 Yakima 설명을 옮긴 모형
static byte class3;                                   // 1바이트 공유 변수
static boolean collimatorInFieldLight = true;         // 콜리메이터가 아직 치료 위치가 아님
static boolean fmalBit9;                              // 오작동 표시

static void setUpTestBuggy() { class3++; }            // 증가: 256번째마다 0으로 돈다
static void setUpTestFixed() { class3 = 1; }          // AECL의 수정: 0이 아닌 고정값
static void lmtchk() {                                // Housekeeper의 검사
    if (class3 != 0) fmalBit9 = collimatorInFieldLight;   // Chkcol 실행
}

static int run(boolean fixed, int passes) {
    class3 = 0; int beamWouldStart = 0;
    for (int i = 1; i <= passes; i++) {
        if (fixed) setUpTestFixed(); else setUpTestBuggy();
        fmalBit9 = false;                             // 이 패스의 검사 결과를 새로 만든다고 가정
        lmtchk();
        if (!fmalBit9) beamWouldStart++;              // 이 순간 "set"을 누르면 치료가 진행되는 패스
    }
    return beamWouldStart;
}
```

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, `scratchpad/sd/56/e56/Class3Model.java`, 2026-10-02 — 결정적)

```text
passes=1024
buggy (byte++) : check skipped on 4 passes
fixed (=1)     : check skipped on 0 passes
(byte)255 + 1 = 0
```

관찰:
- 1,024번 중 4번, 곧 256번마다 한 번 검사가 빠졌다. 원문의 "256번째 패스마다"와 같다.
- 그 4번 외에는 검사가 늘 돌았다. 그래서 공장·병원에서 수천 시간 써도 드러나기 어렵다. FDA의 Miller는 두 사고 모두 "매우 좁은 시간 창 안의 운영자 행동"이 필요했다고 썼다(논문 인용).
- 수정판(고정값 1)은 0번이었다. 해석: "검사가 필요하다"는 boolean이어야 할 의미를, 넘칠 수 있는 카운터의 "0이 아님"으로 인코딩한 것이 결함의 뿌리다. 24번의 "불법 상태를 표현할 수 없게"가 바로 이것이다.
- 이 모형은 경쟁 조건(Housekeeper와 Set-Up Test가 동시에 도는 것)은 흉내 내지 않았다. 패스마다 순서대로 실행되는 단순화다.

## 쓰이는 자료구조·알고리즘

- **공유 변수 + 플래그 기반 동기화** — Therac-25 작업들은 공유 변수만으로 상태를 주고받았다. test와 set이 원자적이지 않으면 확인과 갱신 사이에 다른 작업이 끼어든다. Java라면 `AtomicBoolean.compareAndSet`·락으로 확인과 갱신을 한 연산으로 묶는다([19-4](../19-immutability-and-value-objects/2-summary.md)).
- **모듈러(고정 폭) 정수** — 1바이트 정수는 256을 법으로 돈다. `(byte)255 + 1 = 0`. 카운터를 "0이 아님 = 참"으로 쓰면 넘치는 순간 거짓이 된다.
- **상태 기계** — Treat 작업은 `Tphase` 값(1 자료 입력, 3 준비 시험, 2 준비 완료 …)으로 단계를 오갔다. 단계 전이 조건이 "플래그 하나"였던 것이 Tyler 결함의 자리다. 상태별 타입으로 전이를 표현하는 방법은 [24](../24-types-as-invariants/2-summary.md).
- **결함 트리** — 사고를 AND·OR 트리로 분해한 안전 분석. 1983년 분석은 소프트웨어 잎을 사실상 뺐다.
- **통합 그래프의 단일 진입점** — Healthcare.gov 출시 때는 방문자가 EIDM을 거쳐야 웹사이트 기능에 닿았다(OIG). 그래프에서 모든 경로가 지나는 노드(지배 노드)는 용량과 가용성의 상한이 된다. 직렬 의존의 가용성 곱셈은 [45-3](../45-monolith-vs-microservices/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 사고 보고서를 설계 관점으로 읽는 순서

1. **부품 목록과 출처**를 먼저 그린다. 무엇이 재사용됐고, 누가 만들었고, 어느 경계를 넘나.
2. 경계마다 **적히지 않은 가정**을 찾는다. "밖에서 막아 준다", "이만큼만 온다", "이 순서로 불린다".
3. 타임라인에서 **첫 원인 판단**과 그 근거를 본다. 재현 없이 원인을 정했나(Hamilton의 마이크로스위치).
4. 오류가 사람에게 **어떤 모양**으로 보였나. 무시할 수 있는 모양이었나(pause + P 키, Malfunction 54).
5. 수치·날짜는 원문에서만 가져오고, 설계 용어로 옮긴 부분은 해석으로 표시한다.

### 2. 내 시스템으로 옮길 점검 목록

- **Therac형 — 재사용과 공유 상태**
  - 재사용하는 모듈이 기대던 **바깥 보호 장치**를 목록으로 적는다(입력 검증, 상위 트랜잭션, 게이트웨이의 레이트 리밋 등). 새 환경에 그것이 있나.
  - 스레드·작업 사이 공유 플래그는 "확인 후 갱신"을 원자적으로 만든다. 가능하면 공유 가변 상태 자체를 없앤다(19·31).
  - "검사가 필요하다" 같은 의미는 전용 타입·boolean으로. 넘칠 수 있는 카운터의 부수 효과로 표현하지 않는다(24).
  - 두 값이 서로 일치해야 하면(모드와 기계 위치, 주문 상태와 결제 시각) 그 불변식을 한 곳이 소유하고 검사한다(23).
  - 위험한 동작 앞의 오류는 **suspend**(재입력·재확인 필수)로, 메시지는 사람이 읽을 수 있게(15·17).
  - 결정의 이유를 남긴다. "왜 이 인터록이 있나"가 사라지면 다음 수정에서 지워진다(47).
- **Healthcare.gov형 — 통합 경계**
  - 경계 계약에 기능뿐 아니라 **부하·사용 조건**을 적는다. "모든 방문자가 이 서비스를 지난다", "피크 동시 사용자 N"(46).
  - 모든 경로가 지나는 공유 진입점을 그래프에서 찾아 용량·장애 격리를 따로 설계한다(45-3).
  - 부품별 초록과 별개로 **끝에서 끝 시험**을 일정에 고정한다. 부품이 늦으면 범위를 줄인다.
  - 관제를 통합한다. 한 화면에서 진입점·핵심 시스템·외부 연동의 상태를 본다.
  - 큰 기술 결정(저장소 플랫폼)은 맥락·대안·결과를 기록하는 절차(ADR)를 거친다(47).

### 3. 코드 — 카운터 대신 의미를 타입으로 (Java 21)

```java
// 나쁨: "검사 필요"를 카운터의 0 아님으로 — 255 다음 0에서 의미가 뒤집힌다
byte class3 = 0;
void setUpTest() { class3++; }
boolean needsCheck() { return class3 != 0; }

// 좋음: 의미를 그대로 표현하고, 확인과 진행을 한 객체가 소유한다
enum CollimatorCheck { PENDING, PASSED, FAILED }

final class SetUp {
    private volatile CollimatorCheck check = CollimatorCheck.PENDING;
    void onCollimatorChecked(boolean inTreatmentPosition) {
        check = inTreatmentPosition ? CollimatorCheck.PASSED : CollimatorCheck.FAILED;
    }
    boolean mayStartBeam() {                       // 기본값이 "막음"(fail-safe)
        return check == CollimatorCheck.PASSED;
    }
}
```

- 요점은 두 가지다. 기본값이 "진행"이 아니라 "막음"이다. 그리고 "검사 통과"라는 상태가 명시적으로 존재해야 진행된다.
- 해석: 이런 소프트웨어 검사가 있어도 Leveson–Turner의 교훈은 소프트웨어를 유일한 안전 장치로 두지 말라는 것이다. 최종 CAP는 소프트웨어와 독립인 하드웨어 단일 펄스 차단 회로를 넣었다.

## 장애 시나리오와 대처

### 1. 재사용한 모듈이 옛 환경의 보호 장치를 가정한다 — Therac형

- **현상**: 다른 서비스에서 "수년간 문제없던" 모듈을 가져왔는데 새 환경에서만 사고가 난다.
- **보이는 형태**: 옛 환경에서는 무해한 증상(퓨즈 끊김, 게이트웨이의 400)이었던 것이 새 환경에서는 데이터 손상·사고가 된다. 옛 환경의 로그를 보면 같은 결함이 이미 있었다.
- **원인**: 모듈의 안전이 모듈 밖 장치(하드웨어 인터록, 상위 검증)에 기대고 있었는데 그 의존이 어디에도 적히지 않았다. Therac-20은 같은 소프트웨어 결함을 하드웨어 보호 회로가 막았다.
- **대처**: 재사용 전에 "이 모듈이 기대는 바깥 보호"를 목록으로 만든다. 없앤 보호 장치가 있으면 그 역할을 새 계층에 명시적으로 넣는다. 안전·금전처럼 손실이 큰 경로는 독립 방어선을 하나 더 둔다.

### 2. "완료" 플래그를 세운 뒤의 변경을 못 본다 — Tyler형

- **현상**: 화면에는 고친 값이 보이는데 시스템은 고치기 전 값으로 동작한다. 빠르게 조작할 때만 재현된다.
- **보이는 형태**: 재현이 어렵다(AECL은 처음에 재현하지 못했고, 병원 물리학자가 빠른 편집으로 재현했다). 두 내부 상태(매개변수·턴테이블)가 서로 어긋난다.
- **원인**: "입력 끝" 플래그가 한 번 서면 이후 편집을 확인하지 않았다. 확인과 갱신 사이에 다른 작업이 끼어드는 경쟁 조건이다.
- **대처**: 확정 직전에 **최종 값을 다시 읽어** 일치 여부를 검사한다. 확인과 확정을 원자적으로 묶는다. 일치해야 하는 두 상태는 불변식으로 검사하고, 어긋나면 진행하지 않는다.

### 3. 오류를 "잠시 멈춤"으로 처리해 사람이 넘긴다 — Therac형

- **현상**: 기계가 자주 멈추니 운영자가 습관적으로 진행 키를 누른다. 그 중 하나가 진짜 위험이었다.
- **보이는 형태**: "Malfunction 54"처럼 뜻을 알 수 없는 코드, 설명서에도 설명 없음. "treatment pause"와 낮은 선량 표시(실제로는 포화).
- **원인**: 위험 등급이 다른 오류를 같은 "pause"로 다뤘다. 메시지가 사람이 판단할 정보를 주지 않았다. 사용 편의(재입력 생략)가 안전보다 앞섰다.
- **대처**: 안전·금전에 관한 오류는 suspend(처음부터 재확인)로. 메시지에 무엇이 어긋났고 무엇을 해야 하는지 적는다(17). 알람 피로를 줄이려면 사소한 오류를 ERROR·pause로 올리지 않는다(17-1).

### 4. 모든 요청이 지나는 공용 진입점을 따로 용량 산정한다 — Healthcare.gov형

- **현상**: 출시 직후 로그인·가입이 안 된다. 뒤의 핵심 시스템 문제는 보이지도 않는다.
- **보이는 형태**: 진입점(EIDM)의 오류·지연이 먼저 폭증. 개발자도 진입점을 지나지 못해 뒤쪽 결함을 재현하지 못한다.
- **원인**: 진입점 개발사는 모든 방문자가 그곳을 거친다는 것을 몰랐다. 기능 계약은 있었지만 부하 계약이 없었다. (QSSI는 둘러보기 도구의 연기도 탓했지만, CMS는 그 도구도 계정 생성을 요구했을 것이라고 확인했다 — OIG.)
- **대처**: 아키텍처 그림에서 모든 경로가 지나는 노드를 찾아 피크 부하를 계약에 적는다. 그 노드는 별도로 부하 시험한다. 과부하 때 대기실·부하 차단으로 나머지를 지킨다([reliability/12](../../reliability/12-backpressure-and-load-shedding/2-summary.md)).

### 5. 부품은 각자 초록, 끝에서 끝 시험 없이 내보내고 원인을 하나로 닫는다

- **현상**: 각 팀은 자기 부품이 완료됐다고 보고했는데 출시 첫날 전체가 동작하지 않는다. 공개 설명은 "예상보다 많은 접속".
- **보이는 형태**: 출시 2시간 안 장애, 첫날 6명 가입. 각 계약자의 관제 화면은 자기 시스템만 보여 준다.
- **원인**: 부품 단위 시험이 부품 사이 계약 위반을 잡지 못했다. 끝에서 끝 시험이 일정 끝에 몰려 있다가 부품 지연으로 사라졌다. OIG는 문제가 방문자 수만이 아니라 웹사이트 성능의 핵심 문제였다고 적었다.
- **대처**: 끝에서 끝 시험을 첫 통합 가능 시점부터 반복한다. 부품이 늦으면 일정이 아니라 범위를 줄인다(복구 때의 "ruthless prioritization"). 사후 분석은 방아쇠(접속 수)와 원인(설계·통합 결함)을 나눠 적는다([reliability/26-incident-response-and-postmortem](../../reliability/26-incident-response-and-postmortem/2-summary.md)).

## 핵심 문장

- 실사건은 설계 결함 여러 개가 한 줄로 이어진 것이다. 고리마다 "다른 곳이 막아 준다"는 적히지 않은 가정이 있었다.
- Therac-25는 하드웨어 인터록을 빼고 안전을 소프트웨어에 더 맡겼다. 재사용한 코드가 기대던 보호 장치는 함께 오지 않았다. 같은 결함이 Therac-20에서는 퓨즈만 끊었다.
- Tyler 결함은 "입력 완료" 플래그가 이후 편집을 못 본 경쟁 조건이고, Yakima 결함은 1바이트 카운터가 256번째마다 0이 되어 검사를 건너뛴 것이다. 의미를 타입으로 표현하고 기본값을 "막음"으로 두면 이런 인코딩 결함을 줄일 수 있다.
- 오류를 무시할 수 있는 모양(pause + 진행 키, 뜻 모를 코드)으로 보이면 사람이 넘긴다. 위험한 오류는 재확인을 강제하고 읽을 수 있게 쓴다.
- Healthcare.gov는 각 부품의 계약에 부하·통과 경로가 적히지 않았고, 모든 방문자가 지나는 EIDM이 병목이 됐다. 끝에서 끝 시험 없이 출시했고 첫날 6명이 가입했다.
- 두 사건 모두 첫 원인 판단이 좁았다. 버그 하나·접속 수 하나로 닫지 않고 기여 요인 전체를 적어야 다음 사고를 막는다.

## 관련 주제·근거

- 선행: [55-design-symptom-index](../55-design-symptom-index/2-summary.md) — 이 사건들의 신호가 증상 색인의 어디에 있나
- 메커니즘 leaf
  - [24-types-as-invariants](../24-types-as-invariants/2-summary.md) — 불법 상태를 표현할 수 없게(Class3 카운터)
  - [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md) · [31-antipatterns](../31-antipatterns/2-summary.md) — 공유 가변 상태와 경쟁
  - [23-design-by-contract](../23-design-by-contract/2-summary.md) — 불변식·계약(모드와 위치 일치, 경계의 부하 조건)
  - [15-error-handling-design](../15-error-handling-design/2-summary.md) · [17-error-messages-and-log-level-policy](../17-error-messages-and-log-level-policy/2-summary.md) — pause vs suspend, Malfunction 54
  - [01-complexity](../01-complexity/2-summary.md) — unknown unknowns(재사용 코드의 숨은 가정)
  - [46-quality-attributes-and-tradeoffs](../46-quality-attributes-and-tradeoffs/2-summary.md) · [47-architecture-decision-records](../47-architecture-decision-records/2-summary.md) — 측정 가능한 품질 요구, 결정 기록
  - [45-monolith-vs-microservices](../45-monolith-vs-microservices/2-summary.md) — 직렬 의존과 공유 진입점
- 다른 영역
  - [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md) · [distributed/36-distributed-incidents](../../distributed/36-distributed-incidents/2-summary.md) · [database/57-db-incidents](../../database/57-db-incidents/2-summary.md) — 다른 관점의 실사건
  - [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) — 같은 부류(죽은 코드·플래그 재사용)의 실사건 Knight Capital(2012). 이 영역에서는 [54-2](../54-designing-for-deletion/2-summary.md)가 가리킨다
  - [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md) · [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md) · [reliability/26-incident-response-and-postmortem](../../reliability/26-incident-response-and-postmortem/2-summary.md)
- 1차 출처
  - Nancy G. Leveson, Clark S. Turner, "An Investigation of the Therac-25 Accidents", IEEE Computer 26(7), July 1993, pp. 18–41 — 원 지면 스캔 <https://www.cs.columbia.edu/~junfeng/08fa-e6998/sched/readings/therac25.pdf>, 저자 허락 재수록 HTML(같은 본문) <http://www.cse.msu.edu/~cse470/Public/Handouts/Therac/Therac_1.html>(1~5쪽). 사이드바("Therac-25 software development and design")는 원 지면 스캔에서 확인했다. 스캔의 OCR이 깨진 수치(결함 트리 확률·시험 시간 등)는 이 노트에 옮기지 않았다.
  - U.S. GAO, "Healthcare.gov: Ineffective Planning and Oversight Practices Underscore the Need for Improved Contract Management", GAO-14-694, 2014-07-30 <https://www.gao.gov/products/gao-14-694> — Highlights(의무액 증가, ORR 3월 → 9월, 수수료 약 26만 7천 달러 미지급, Accenture 9,100만 → 1억 7,500만 달러 이상), 6~7쪽(FFM·허브 구성), 23~26쪽(검토 지연, 65%·75% 추정, 성능 요구 미검증 출시, 핵심 구성요소 셋 중 하나만 완료)
  - HHS OIG, "HealthCare.gov: CMS Management of the Federal Marketplace — An OIG Case Study", OEI-06-14-00350, 2016-02 <https://oig.hhs.gov/oei/reports/oei-06-14-00350.pdf> — 요약(리더십 부재, 540만 명), 13쪽(계약 60건 중 55건), 16~17쪽(MarkLogic TDL), 19쪽(가족 신원 확인 정책), 22쪽(통합 책임자 부재), 27~28쪽(끝에서 끝 시험 미완, 36개 주, CGI Federal이 출시 연기를 요청하지 않음), 32~34쪽(동시 사용자 250,000·5배·첫날 6명, EIDM 병목, anonymous shopper, 관제 분리), 39쪽(11월 가동률 42% → 90% 이상, 동시 35,000명)
- 실험 목록
  - `scratchpad/sd/56/e56/Class3Model.java` — Yakima 1바이트 카운터 모형(논문 설명을 옮긴 것, 원 코드 재현 아님). JDK 21.0.12 temurin 컨테이너 `--cpus=2`, `java Class3Model.java`. 출력: 1,024패스 중 증가판 4회·수정판 0회 검사 누락, `(byte)255 + 1 = 0`.
