# domain-modeling/28-dm-incidents — 실사건: Mars Climate Orbiter 단위 불일치(1999) · Post Office Horizon 회계 불일치(2000~) · Azure 윤일(2012) · 시간대 규칙 변경(2022~23) — 정리 (힌트)

## 해결하는 문제

leaf 노트는 모델링 결함을 **하나씩** 다룬다.\
단위 없는 숫자는 03·12번, 원장을 고쳐 쓰는 문제는 24번, 대사는 25번, 날짜 산술은 13번이다.\
실제 사고에서는 결함 하나가 **아무도 확인하지 않는 경계**를 넘어 오래 쌓인다.\
그리고 "그쪽은 맞게 하고 있겠지", "시스템은 견고하다"는 가정이 그 경계를 지킨다고 믿어진다.

```text
  leaf 노트:  [단위 없는 숫자] [인터페이스 명세] [원장 사후 수정] [대사·정정] [중복 기록] [날짜 산술] [tz 규칙]  <- 각각 따로
  실사건:
    MCO 1999        지상 SW가 lbf·s로 씀 -> 명세는 N·s -> 항법은 N·s로 읽음 -> 9개월 누적 -> 궤도 약 170 km 낮음
    Horizon         지점 화면과 본사 원장이 어긋나는 버그들 -> 시스템이 알리지 않음 -> 부족액은 SPM이 메움(계약)
    Azure 2012      "연도 + 1" -> 2013-02-29 -> 인증서 생성 실패 -> 하드웨어 고장으로 오인 -> 연쇄
    tz 2022~23      정부가 며칠 전 DST를 바꿈 -> 판이 연달아 나옴 -> 저장된 미래 시각의 뜻이 바뀜
```

쉬운 예: 두 나라 사이의 택배다.\
보내는 쪽은 상자 무게를 파운드로 적었다. 받는 쪽은 킬로그램으로 읽었다.\
송장 양식에는 "kg"이라고 쓰여 있었다. 아무도 그 칸을 검사하지 않았다.\
상자 하나는 문제없었다. 같은 실수가 상자 수백 개에 쌓이자 트럭이 넘쳤다.

똑같은 구조다.\
MCO의 지상 소프트웨어는 추력 효과를 파운드힘·초로 파일에 썼다. 파일 명세는 뉴턴·초를 요구했다.\
한 번의 오차는 작았다. 같은 기동이 예상보다 10~14배 자주 일어나며 9개월 동안 쌓였다(MIB 보고서).

이 노트는 공개된 1차 문서로 네 사건을 복원한다.
- **Mars Climate Orbiter(1999-09-23 소실)**: 1차 출처 NASA MCO Mishap Investigation Board, *Phase I Report*, 1999-11-10.
- **Post Office Horizon(Legacy Horizon 2000~2010, Horizon Online 2010~)**: 영국 우체국 지점 회계 시스템. 1차 출처 *Bates and Others v Post Office Ltd (No 6) "Horizon Issues"* [2019] EWHC 3408 (QB), Fraser J, 2019-12-16(판결문 PDF, 313쪽).
- **Windows Azure(2012-02-29)**: 1차 출처 Microsoft Azure Team, "Summary of Windows Azure Service Disruption on Feb 29th, 2012"(azure.microsoft.com 블로그).
- **시간대 규칙 변경(2022 멕시코, 2023 레바논)**: 1차 출처 IANA tz database `NEWS`(판별 변경 기록). 이것은 장애 보고서가 아니라 **규칙 변경 기록**이다. 실제 시스템 영향의 수치는 1차 출처에 없어 이 노트에 싣지 않는다.

  - *조사 문서의 성격*: MIB 보고서는 MPL(Mars Polar Lander) 착륙 전에 낸 1단계 보고서라 MPL 권고가 함께 있다. Horizon 판결은 민사 집단소송의 한 쟁점("Horizon Issues") 판결이다. 형사 유죄 판결의 재심 등 이후 절차는 이 판결의 범위가 아니어서 다루지 않는다. Azure 글은 회사가 직접 쓴 사후 분석이다.
  - 이 노트의 시각·수치는 위 문서에서만 가져왔다. 모델링 관점의 해석은 "해석"으로 표시했다.
  - 커리큘럼 행은 Horizon을 "1999~"로 적었다. 판결문 [1]은 "The Post Office introduced a computer system called Horizon in 2000 across all its branches"라고 쓴다. 이 노트는 판결문을 따른다.

## 동작·원리

### 사건 1 — Mars Climate Orbiter (1998-12-11 발사 ~ 1999-09-23 소실)

#### 무엇이 어디에 있었나 (원문)

```text
  우주선 (LMA가 운용)                         지상 (우주선 운영 쪽 소프트웨어)             JPL 운영 항법팀
  ┌─────────────────────┐   원격 측정    ┌──────────────────────────────┐  AMD 파일  ┌────────────────────┐
  │ AMD 기동             │ ─────────────▶ │ SM_FORCES ("Small Forces")    │ ─────────▶ │ 궤도 결정 소프트웨어 │
  │ (반작용 휠 포화 해소) │                │ impulse bit 를 lbf·s 로 씀 ✗  │            │ N·s 로 가정하고 읽음 │
  │ 탑재 SW: 미터 단위 ✓ │                └──────────────────────────────┘            └────────────────────┘
  └─────────────────────┘                          ▲
                                                   │ Software Interface Specification(SIS):
                                                   │ AMD 파일의 형식과 단위 = N·s  (지켜지지 않음)
```

- 근본 원인(보고서 문장): "the failure to use metric units in the coding of a ground software file, 'Small Forces,' used in trajectory models."
- SIS는 AMD 파일의 형식과 단위를 정의했고 N·s를 요구했다. 데이터는 lbf·s로 보고됐다. 항법 소프트웨어는 그 데이터로 추력 효과를 **4.45배**(1 pound force = 4.45 Newtons) 과소평가했다.
- 탑재 AMD 소프트웨어는 미터 단위로 계산해 맞았다. 잘못된 모델링은 지상 소프트웨어에서만 일어났다(기여 원인 1).
- AMD 기동은 운영 항법팀 예상보다 **10~14배** 자주 일어났다. MCO의 태양 전지판이 기체에 비대칭이라 태양 복사압으로 각운동량이 더 많이 쌓였다(MGS는 대칭). 이를 줄이려던 매일 180° 회전("barbecue" 모드)은 시스템 공학 검토 뒤 운영 계획에서 빠졌다. 이 결정과 그 영향은 운영 항법팀에 전달되지 않았다(기여 원인 4).
- 처음 4개월은 AMD 파일을 궤도 결정에 쓰지 못했다. 파일 형식 오류와 잘못된 쿼터니언(자세 데이터) 명세 때문이다. 그동안 항법팀은 계약사의 이메일로 AMD 시점만 받아 스스로 모델링했다. 1999년 4월에야 올바른 형식의 파일을 쓰기 시작했고, 일주일 안에 과소평가를 가리키는 이상 데이터가 보였다(기여 원인 1).
- 관측의 한계: AMD 추력의 주 성분이 지구–우주선 시선(line of sight)에 수직이었다. 항법팀은 도플러로 시선 방향만 직접 관측할 수 있어, 체계적 오차가 궤도 추정에 남았지만 드러나지 않았다(기여 원인 1).

  - *AMD(Angular Momentum Desaturation)*: 반작용 휠에 쌓인 각운동량을 추력기 분사로 풀어 주는 기동이다. 분사할 때마다 궤도가 조금씩 바뀐다.
  - *impulse bit*: 추력기 한 번 분사의 충격량(힘 × 시간) 모델값이다. 단위는 N·s(미터법) 또는 lbf·s(영국 단위).
  - *SIS(Software Interface Specification)*: 두 소프트웨어 사이에 주고받는 파일의 형식·단위 명세다. 도메인 모델링으로 치면 두 컨텍스트 사이의 **공표된 언어(Published Language)** 계약이다(해석, [18](../18-context-mapping/2-summary.md)).

#### 타임라인 (원문, 시각은 보고서 표기)

| 날짜·시각 | 사건 |
|---|---|
| 1998-12-11 | 발사 |
| 1999 봄~여름 | 실무 수준에서 항법 해 사이 불일치 우려. AMD 이벤트의 기대·관측 도플러 잔차가 비공식적으로만 보고됨. 도플러만 쓴 해는 꾸준히 행성에 더 가까운 진입을 가리켰고, 이 불일치는 해소되지 않음 |
| 1999-04 | 올바른 형식의 AMD 파일 사용 시작. 일주일 안에 과소평가를 가리키는 이상 데이터 |
| 1999-09-08 | 마지막 계획 궤도 보정 TCM-4 계산. 목표 첫 근점 고도 226 km |
| 1999-09-15 | TCM-4 실행 |
| TCM-4 ~ MOI 사이 한 주 | 궤도 결정상 첫 근점 거리가 150~170 km로 줄어듦 |
| MOI 약 1시간 전 | 더 정확한 추적 데이터 처리 완료. 첫 근점 고도가 110 km까지 낮게 계산됨. 생존 가능한 최저 고도는 80 km |
| 1999-09-23 09:00:46 UTC | MOI 엔진 점화 |
| 1999-09-23 09:04:52 UTC | 화성 엄폐로 신호 소실 — 예측보다 49초 일찍. 예측 엄폐 21분 뒤 재획득 실패. 09-25까지 시도 |
| 1999-09-27 | 운영 항법팀이 우주선 엔지니어와 ΔV 모델링 불일치를 논의 |
| 1999-09-29 | 소형 힘 ΔV가 4.45배 낮게 보고됐음을 발견. AMD 파일의 impulse bit가 N·s가 아니라 lb-sec |
| 사후 | 보정한 ΔV로 다시 추정한 첫 근점 57 km — 생존하기에 너무 낮다고 판단 |
| 1999-10-15 | NASA MCO MIB 설치 |
| 1999-11-10 | Phase I 보고서 |

- 보고서 요약: 화성 진입 시점에 궤도가 계획보다 약 170 km 낮았다. 우주선은 대기에서 파괴됐거나 대기를 빠져나가 태양 궤도로 갔다.
- 비상 기동 TCM-5가 MOI 직전 구두로 논의됐지만 실행되지 않았다. 준비(분석·시험·절차)가 안 돼 있었고, 탑재 MOI 일정이 우선이었다(기여 원인 3).
- 기여 원인 8개(보고서 목록): ① 우주선 속도 변화의 모델링 오류 미탐지 ② 항법팀이 우주선에 익숙하지 않음 ③ TCM-5 미실행 ④ 개발→운영 전환의 시스템 공학 미흡 ⑤ 프로젝트 요소 간 소통 부족 ⑥ 운영 항법팀 인력 부족 ⑦ 교육 부족 ⑧ 검증·확인(V&V)이 지상 소프트웨어를 충분히 다루지 않음.
- 기여 원인 8의 구체: SIS는 만들어졌지만 small forces 지상 소프트웨어의 개발·시험에 제대로 쓰이지 않았다. 명세 준수를 확인하는 끝에서 끝 시험이 이뤄진 것으로 보이지 않았다.

#### 메커니즘 — 단위가 이름에도 타입에도 없는 숫자 (원문 설명의 그림)

```text
  실제 충격량          파일에 적힌 숫자               받는 쪽이 읽은 값
  10 N·s (예시)  ──▶   2.248  (lbf·s로 적음)   ──▶   2.248 N·s  (N·s로 가정)
                       단위 표기 없음                   실제의 1/4.45

  AMD 1회:  오차 작음
  AMD × (예상의 10~14배 빈도) × 9개월:  궤도 추정이 실제보다 높게 -> 실제 근점은 더 낮음
```

#### 모델링 관점으로 다시 보기 (해석)

- **값 객체에 단위가 없었다**: 숫자 하나가 경계를 넘었고, 단위는 명세 문서에만 있었다. 단위를 값과 함께 들고 다니면(값 객체·필드 이름·스키마) 받는 쪽이 검사할 자리가 생긴다([03-2](../03-ubiquitous-language/2-summary.md) · [04](../04-entities-and-value-objects/2-summary.md) · [12-3](../12-time-money-and-units/2-summary.md)).
- **공표된 언어를 검증하지 않았다**: SIS가 계약이었지만 계약 테스트가 없었다. 하류(항법)는 상류(지상 SW) 출력을 그대로 믿는 순응자였다([18](../18-context-mapping/2-summary.md)). 번역·검사 계층이 있었다면 범위 검사로 잡을 기회가 있었다([19](../19-anti-corruption-layer/2-summary.md)).
- **모델 가정이 조용히 바뀌었다**: "barbecue" 모드 삭제는 AMD 빈도라는 입력 분포를 바꿨다. 그 결정이 하류에 전달되지 않았다. 같은 단어(AMD 이벤트)를 쓰지만 팀마다 다른 빈도를 가정한 상태다([03](../03-ubiquitous-language/2-summary.md) · [16](../16-bounded-contexts/2-summary.md)).
- **신호는 있었는데 분류되지 않았다**: 4월의 이상 데이터, 도플러 해의 불일치가 비공식 보고에 머물렀다. 25번의 말로는 "차이를 사건으로 남기지 않았다"([25-5](../25-reconciliation/2-summary.md)).

### 사건 2 — Post Office Horizon (Legacy Horizon 2000~2010 · Horizon Online 2010~)

#### 무엇이 어디에 있었나 (원문)

```text
  지점(SPM이 운영)                                    본사 쪽
  ┌──────────────────────────────┐                ┌────────────────────────────────┐
  │ Horizon 카운터                │  거래 데이터    │ 백엔드(POLSAP·Credence 등)       │
  │  - 거래 기록                  │ ─────────────▶ │  - 지점 회계                     │
  │  - 기간 마감·잔액 맞추기       │                │  - 고객사(로또 등) 데이터와 대조   │
  │  - 차이(discrepancy) 처리     │ ◀───────────── │  - Transaction Correction(TC) 발행│
  └──────────────────────────────┘    TC          └────────────────────────────────┘
          ▲                                                   ▲
          │ Fujitsu(개발·운영사): SSC·APPSUP·특권 사용자 권한으로 거래 데이터 삽입·수정·삭제·재구성 가능 (판결 [1003])
```

- 판결문 [1]: 우체국은 2000년 모든 지점에 Horizon을 도입했다. 2010년 온라인판(Horizon Online, HNG-X)으로 바뀌었고 이전 판은 Legacy Horizon이라 부른다. 원고(전·현직 지점장 SPM)의 주장은 두 판 모두 신뢰할 수 없어 설명되지 않는 부족액·차이가 지점 회계에 생겼다는 것이다. 우체국은 시스템이 견고하다고 맞섰다.
- 판결문 [963]: 2017년 HNG-A가 됐고 완전히 다른 Windows 플랫폼에서 돈다. 판결문 [964]: 이 판결은 소송 대상 기간에 대한 **역사적 분석**이며 2019년 12월 현재의 HNG-A에 대한 판단이 아니라고 밝힌다.

  - *SPM(subpostmaster)*: 우체국과 계약해 지점을 운영하는 사람이다. 판결 [824]: 기간 마감의 지점 거래 명세(BTS)에 부족액이 나오면 계약상 SPM이 그 돈을 "make good"(우체국에 지급)하거나 "settle centrally"(분할 납부)해야 했다.
  - *Transaction Correction(TC)*: 본사가 지점 회계를 정정하려고 보내는 거래다. 판결은 TC가 Horizon 시스템의 일부가 **아니라고** 본다("TCs are not part of the Horizon system", [970] · [977]).
  - *PEAK·KEL*: Fujitsu의 사고 기록(PEAK)과 알려진 오류 기록(KEL)이다. 판결은 이 내부 문서를 사실 확인의 주요 근거로 썼다([940]).

#### 판결의 결론 (원문 요지, 문단 번호)

| 쟁점 | 판결 | 문단 |
|---|---|---|
| 버그가 지점 회계 차이를 일으킬 수 있었나 | 가능했고, 실제로 여러 차례 일어났다(Legacy·HNG-X, HNG-A는 고립된 사례만) | [968]~[969] |
| 얼마나 | 피고 측 전문가(Worden)도 지점 회계에 지속 차이를 낸 버그가 최소 12개라는 강한 증거를 인정. 원고 측 전문가(Coyne) 표는 29개(그중 지속 영향 21개라고 반대신문에서 설명). 소송 전 우체국이 인정한 버그는 2개 | [970] · [676] · [794] |
| Horizon이 SPM에게 버그를 알렸나 | "No, the Horizon system did not alert SPMs". 일부 버그는 수년간 발견되지 않음 | [973] |
| 견고했나 | Legacy Horizon은 "not remotely robust". HNG-X는 조금 나았지만 견고성이 의문. HNG-A는 훨씬 견고 | [975]~[976] |
| 차이가 Horizon 때문일 가능성 | 2000~2017년(Legacy·HNG-X)에 지점 부족액이 Horizon 때문일 **실질적 위험**이 있었다 — "극히 낮다"는 우체국 주장 기각 | [978] |
| TC 규모 | 소송 대상 기간 중 많은 해에 연 10만 건 이상 | [971] |
| 원격으로 데이터를 바꿀 수 있었나 | Fujitsu: 삽입·수정·삭제, 수정 배포, 재구성 모두 "yes" — SPM이 모르게, 동의 없이도. 우체국: Global User로 지점에 있을 때 거래 삽입만 | [1003] · [1005] |
| 그 권한에 통제·로그가 있었나 | 권한 통제는 있었지만 역할이 매우 넓고 통제되지 않았다. 적절한 로그가 없었다 | [1008] |

#### 메커니즘 1 — Receipts and Payments Mismatch 버그 (HNG-X, 2010)

판결 [428]이 인용한 회의 문서(issue notes)의 설명이다. 재판 서류 색인의 날짜는 2012-10-17이지만, 판결은 관련 문서가 2010-09-29자라 2010년 문서일 가능성이 높다고 본다.

```text
  기간 마감(rollover) 중 차이 발견
       │
       ▼
  "차이를 Local Suspense로 옮길까요?"  ── 지점이 취소 누름 ──▶  지점 화면의 차이 = 0 으로
       │                                                     (POLSAP·Credence에는 그대로)
       ▼
  같은 세션에서 마감을 다시 진행
       │
       ▼
  지점: "잔액이 맞았다"             본사: 차이가 남음
  => Receipts and Payments mismatch — 지점 화면에는 경고 없음, 다음 기간으로 이월
```

- 문서의 영향 서술: "circa 40 Branches since migration onto Horizon Online, with an overall cash value of circa £20k loss". "At this time we have not communicated with branches affected"라고 적었다. 문제는 그해 5월에 시작됐다("an issue which began in May").
- 영향 항목에 "The branch has appeared to have balanced, whereas in fact they could have a loss or a gain", "Our accounting systems will be out of sync with what is recorded at the branch"가 있다.
- 오류 코드가 생성돼 Fujitsu는 영향 지점을 가려낼 수 있었지만 지점에는 보이지 않았다.
- 문서는 해결안 셋을 비교했다. 채택된 것은 둘째(본사가 차이 계정의 값을 고객 계정으로 옮겨 정상 절차로 회수·환불)였다([431]). 첫째안(Fujitsu가 지점 회계에 값을 직접 써 넣기)에 대해서는 문서 스스로 "significant data integrity concerns", "tampering" 의심 위험을 적었다.

#### 메커니즘 2 — Dalmellington 버그 (Branch Outreach, HNG-X)

- 판결 [446]: 강제 로그아웃 때 Post Log On 스크립트가 제대로 닫히지 않아 처리 스택에 남았다. Pouch Delivery 스크립트는 스택이 비지 않은 것을 보고 끝나지 않았다고 판단해 마지막 부분을 반복했다. 송금 거래 기록과 영수증 출력이 반복돼 **같은 파우치 ID가 중복 기록**됐다. 파우치 바코드 ID는 유일해야 한다.
- 판결 [447]: Dalmellington의 SPM은 핵심 지점에서 아웃리치 지점으로 £8,000을 보냈다. 이체가 4번 복제돼 아웃리치 지점에 £32,000(4 × £8,000) 수령이 기록됐고 £24,000의 차이가 생겼다. 몇 주 뒤 TC로 정정됐다.
- 판결 [448]: Fujitsu 조사에서 지난 5년간 88개 지점 112건. 연도별: 2010-02~2011-01 65건, 2011 6건, 2012 9건, 2013 7건, 2014 9건, 2015 16건.
- 판결 [450]: Fujitsu 측 증인은 이 버그가 "사용자가 같은 일을 여러 번 한 것처럼 보이게" 했다고 말했다.

#### 메커니즘 3 — 두 시스템 사이 자동 연계 없음 (Ping fix)

- 판결 [943]~[945]: 로또 단말은 Camelot 시스템, 판매 지점 회계는 Horizon이었고 Camelot 판매가 Horizon으로 전자 전송되지 않았다. 차이는 TC로 정정됐다.
- 로또 관련 TC 금액: 2007년 약 £22.8m, 2008년 £12.5m, 2009년 £12.0m, 2010년 £11.3m, 2011년 £4.5m. 연계를 자동화한 Ping fix가 들어온 2012년에는 £1m 아래.
- 판결은 이것을 SPM의 부주의를 고친 것이 아니라 Horizon 기능의 결함을 고친 것이라고 판단했다([945]).

#### 모델링 관점으로 다시 보기 (해석)

- **한 사실, 두 장부, 대사의 방향**: 지점 화면과 본사 원장이 같은 사실을 따로 들었다. 둘이 어긋나면 어느 쪽이 정본인지, 차이를 누가 책임지는지가 도메인 규칙이다. 부족액을 지점이 메우는 구조([824]~[825])에서는 원인이 시스템 쪽이어도 차이가 지점의 채무로 처리된다. 25번의 "차이를 자동으로 한쪽에 맞춘다"와 같은 모양이다([25-5](../25-reconciliation/2-summary.md)).
- **원장을 밖에서 고칠 수 있었다**: 거래 데이터를 지점이 모르게 삽입·수정·삭제할 수 있었고 로그가 부족했다([1003]·[1008]). 24번의 "정정은 역분개, UPDATE·DELETE 금지"와 22번의 "결정 근거를 업무 데이터로"가 지키려는 것이 이 경우의 증명 가능성이다([24-2](../24-double-entry-ledger/2-summary.md) · [22](../22-decision-log-and-provenance/2-summary.md)).
- **같은 ID의 중복 기록**: Dalmellington은 유일해야 할 파우치 ID가 반복 기록된 사건이다. 업무 키 `UNIQUE`(멱등 전표)라면 두 번째 기록을 거절할 수 있는 자리다. 판결은 그런 검사가 어디에 있었어야 했는지는 다루지 않는다([24-5](../24-double-entry-ledger/2-summary.md) · [09-4](../09-domain-events/2-summary.md)).
- **시스템이 알리지 않았다**: 지점 화면에는 "맞았다"만 보였다. 15번의 "조용히 버린다", 21번의 "조용히 틀린 뷰"와 같은 모양이다([15-4](../15-basic-modeling-exercises/2-summary.md) · [21-3](../21-cqrs/2-summary.md)).

### 사건 3 — Windows Azure 윤일 (2012-02-28 16:00 PST ~ 03-01 02:15 PST)

#### 무엇이 어디에 있었나 (원문)

```text
  클러스터(서버 약 1000대) ── Fabric Controller(FC)
     서버 ── Host Agent(HA)  ◀── 심장 박동 ──▶  VM 안의 Guest Agent(GA)
                                               GA 초기화 첫 단계: "transfer certificate" 생성
                                               valid-from = 그날 자정(UST), valid-to = "연도 + 1"
```

- 원문: "The leap day bug is that the GA calculated the valid-to date by simply taking the current date and adding one to its year." 윤일에 만든 인증서의 valid-to는 2013-02-29, 없는 날짜라 인증서 생성이 실패했다.
- 인증서를 못 만든 GA는 종료한다. HA는 GA를 25분 기다린 뒤 VM OS를 다시 초기화하고 재시작한다.
- 깨끗한 VM(고객 코드가 돈 적 없는 VM)이 연속 3번 타임아웃하면 HA는 **하드웨어 문제**로 판단해 서버를 HI(Human Investigate) 상태로 보고한다. FC는 그 서버의 VM을 다른 서버로 옮긴다(service healing). 옮긴 서버에서 같은 버그가 재현돼 HI가 연쇄됐다.
- FC에는 HI 임계치가 있어 넘으면 클러스터 전체가 HI와 비슷한 상태가 되고 자동 업데이트·service healing이 멈춘다.
- 원문 표기 "UST"는 글에 적힌 그대로다.

#### 타임라인 (원문, 시각은 글의 PST 표기)

| 시각 | 사건 |
|---|---|
| 02-28 4:00PM PST (00:00 UST 02-29) | 새 VM의 GA가 인증서 생성 시도 — 버그 즉시 발동. 스토리지 클러스터는 GA가 없어 영향 없음 |
| 5:15PM | FC·HA·GA 새 버전 배포 중이던 클러스터에서 서버 HI 임계치 도달 — 정확히 75분 뒤(25분 타임아웃 × 3) |
| 6:38PM | 개발자가 버그 식별 |
| 6:55PM | 전 세계 모든 클러스터의 서비스 관리 기능 차단(글: "the first time we've ever taken this step" — 이런 조치는 처음) |
| ~10:00PM | 수정 GA 시험·배포 계획 |
| 11:20PM | 수정 GA 코드 준비 |
| 02-29 1:50AM | 시험 클러스터 시험 완료 |
| 2:11AM | 운영 클러스터 하나 배포 성공 → 전 클러스터로 배포 |
| 2:47AM | 배포 초기 단계였던 7개 클러스터에 옛 HA + 새 HA용 네트워킹 플러그인(비호환) 묶음을 동시 배포 — 건강하던 VM까지 네트워크 단절(2차 장애) |
| 3:40AM | 수정 HA 묶음 재시험(이번엔 VM 연결 확인 포함) |
| 5:23AM | 대부분 클러스터의 서비스 관리 복구 공지 |
| 5:40AM | 7개 클러스터에 수정본 동시 배포 시작 |
| 8:00AM | 7개 클러스터 대부분 운영 재개. 손상 상태 서버는 하루 종일 수작업 복구 |
| 03-01 2:15AM | 모든 서비스 정상 마지막 공지 |

- 영향: Compute와 의존 서비스(ACS, Service Bus, SQL Azure Portal, Data Sync). Storage·SQL Azure는 영향 없음.
- 보상: 영향 여부와 관계없이 Compute·Access Control·Service Bus·Caching 고객 전체에 해당 청구 월 33% 크레딧.
- 글이 든 개선: 날짜·시각 버그를 잡는 시험과 코드 분석 도구 강화, GA 결함을 하드웨어 결함과 구분, 75분 긴 타임아웃 뒤에야 드러난 GA 실패를 빨리 분류(fail fast).

#### 모델링 관점으로 다시 보기 (해석)

- **날짜를 "필드 셋"으로 다뤘다**: "1년 뒤"는 도메인 개념(달력 산술)인데 연도 필드에 1을 더하는 구현으로 바꿨다. 윤일이 아닌 날에는 결과가 같아서 평소 시험으로 갈리지 않는다([13-5](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [26-5](../26-advanced-modeling-exercises/2-summary.md), 아래 실행 확인 A).
- **실패의 뜻을 한 비트로 줄였다**: GA는 "연결 안 됨"만 남겼고, HA는 그 침묵을 하드웨어 고장으로 해석했다. 15번의 "결과를 boolean 하나로 준다"의 운영판이다([15-5](../15-basic-modeling-exercises/2-summary.md)).
- **복구 동작이 결함을 퍼뜨렸다**: service healing은 VM을 옮겼고 옮긴 곳에서 같은 날짜 계산이 다시 실패했다. 결함이 데이터(날짜)에 있는데 위치(서버)를 바꿨다.

### 사건 4 — 시간대 규칙 변경 (tzdb 2022f·2023a~c)

1차 출처는 tz 데이터베이스의 `NEWS` 파일이다. 장애 보고서가 아니라 **규칙이 언제, 얼마나 앞두고 바뀌었는지**의 기록이다.

| 판(배포 시각, NEWS 표기) | 변경 |
|---|---|
| 2022f (2022-10-28 18:04:57 -0700) | 멕시코는 2022년 이후 DST를 하지 않음(미국 국경 인근 제외). Chihuahua는 **2022-10-30**에 연중 -06으로 |
| 2023a (2023-03-22 12:39:33 -0700) | 이집트가 다시 DST(4월 마지막 금요일~10월 마지막 목요일). 팔레스타인 2023년 DST 시작을 3-25 → 4-29로 미룸 등 |
| 2023b (2023-03-23 19:50:38 -0700) | 레바논이 올해 3월 25/26일이 아니라 **4월 20/21일**에 DST 시작 |
| 2023c (2023-03-28 12:42:14 -0700) | "Model Lebanon's DST chaos by reverting data to tzdb 2023a." — 2023b의 레바논 변경을 되돌림 |

- Chihuahua 변경은 시행 이틀 전 판에 실렸다. 레바논은 2023b가 3월 23일, 원래 전환일(3월 25/26일) 이틀 전에 나왔고, 닷새 뒤(3월 28일) 2023c가 되돌렸다.
- 이 판들을 받기 전에 "그 지역 현지 시각"으로 잡힌 미래 예약을 UTC 순간으로만 저장했다면, 판이 바뀔 때 그 순간의 현지 시각 뜻이 바뀐다(해석, [13-1](../13-instant-vs-local-time-and-tz-rules/2-summary.md)).
- 실제 시스템이 몇 건 어긋났는지는 이 1차 출처에 없다. 이 노트는 그 수치를 쓰지 않는다.

#### 모델링 관점으로 다시 보기 (해석)

- **규칙은 외부가 바꾼다**: 시간대 규칙은 정부가 정하고 며칠 전에 바뀔 수 있다. 자체 구현할 대상이 아니라 일반 서브도메인이다([17-1](../17-subdomains/2-summary.md)).
- **미래는 의도로 저장한다**: "2023-04-01 09:00 Asia/Beirut"(현지 시각 + tz ID)가 원본이고 UTC 순간은 파생값이다. 판이 바뀌면 재계산한다([13-1](../13-instant-vs-local-time-and-tz-rules/2-summary.md)).
- **규칙에도 판이 있다**: 요율표처럼 tz 규칙도 판을 기록해야 "그때 어떤 규칙으로 계산했나"에 답한다([23](../23-versioned-rules-and-effective-dating/2-summary.md)).

### 네 사건을 나란히 (해석)

| | MCO | Horizon | Azure 2012 | tz 2022~23 |
|---|---|---|---|---|
| 경계를 넘은 것 | 단위 없는 숫자 | 같은 거래의 두 장부 | "1년 뒤"라는 날짜 계산 | 외부가 정한 규칙 |
| 적혀 있던 계약 | SIS: N·s | 지점 회계 = 본사 회계 | (없음 — 연도 + 1) | 판별 NEWS |
| 확인하지 않은 가정 | "상대는 명세대로 쓴다" | "시스템은 견고해 부족액의 원인일 가능성이 극히 낮다"(우체국 주장, [1]·[978]) | "타임아웃 3번 = 하드웨어 고장" | (저장 방식에 달림) |
| 신호 | 도플러 잔차·이상 데이터 | 설명 안 되는 부족액, PEAK·KEL | 75분 뒤 HI 연쇄 | 판 공지 |
| 이 영역의 대응 leaf | 03 · 04 · 12 · 18 · 19 | 22 · 24 · 25 · 09 | 13 · 15 · 26 | 13 · 17 · 23 |

### 실행 확인: 네 메커니즘의 모형

사건 설명을 옮긴 **모형**이다. 원 코드의 재현이 아니다.

```java
// A. Azure: valid-to = 연도 + 1 (2012-02-29)
LocalDate.of(today.getYear() + 1, today.getMonthValue(), today.getDayOfMonth());  // 직접 산술
Calendar c = new GregorianCalendar(TimeZone.getTimeZone("UTC")); c.clear();
c.set(today.getYear() + 1, Calendar.FEBRUARY, 29);                                 // lenient 기본값
today.plusYears(1);                                                                 // 달력 산술

// B. MCO: 받는 쪽이 N·s로 가정 / 단위를 함께 보냄
static final double LBF_TO_N = 4.4482216152605;   // = 0.45359237 kg × 9.80665 m/s²
record Impulse(double value, Unit unit) {
    double toNs() { return unit == Unit.N_S ? value : value * LBF_TO_N; }
}

// D. Dalmellington: 같은 파우치 ID 4번 기록 — 키 검사 유무
if (seen.add(r[0])) withKey += Long.parseLong(r[1]); else rejected++;
```

(실험, JDK 21.0.12 temurin 일회용 컨테이너 `--cpus=2 --network none`, 2026-10-03)

```text
java 21.0.12
== A. 연도 + 1 (Azure 2012 설명의 모형)
naive LocalDate.of(y+1,m,d) -> DateTimeException: Invalid date 'February 29' as '2013' is not a leap year
lenient GregorianCalendar(2013,FEB,29) = 2013-03-01T00:00:00Z
plusYears(1) = 2013-02-28
2012-02-28: naive=2013-02-28 plusYears=2013-02-28
2012-01-01..2031-12-31 중 naive가 실패하는 날 수 = 5
== B. 단위 없는 숫자 (MCO 설명의 모형)
실제 10.000 N·s, 파일 숫자 2.248, 받는 쪽 해석 2.248 N·s, 비율 4.4482
단위를 함께 보낸 경우 toNs() = 10.000 N·s
== C. 지점 화면 vs 본사 원장 (Horizon 2010 issue notes 설명의 모형)
지점 화면 차이=0 (지점은 '맞았다'고 봄)
본사 원장 차이=-500
대사(본사-지점) 차이=-500 -> 다음 기간으로 이월
== D. 같은 파우치 ID 반복 기록 (Dalmellington 설명의 모형)
키 검사 없음: 받은 금액=32000, 보낸 금액=8000, 차이=24000
파우치 ID 유일 검사: 받은 금액=8000, 거절=3
```

관찰:
- A: 같은 "연도 + 1"이 API에 따라 **예외**(java.time), **조용히 3월 1일**(lenient `Calendar`), **2월 28일**(`plusYears`)로 갈렸다. Azure 글은 "invalid date that caused the certificate creation to fail"이라고만 적었다. 어느 API였는지는 글에 없다. 20년(2012~2031) 동안 직접 산술이 실패하는 날은 5일(윤일)뿐이었다. 평소 시험이 이 결함을 못 잡는 이유다.
- B: 받는 쪽 값은 실제의 1/4.4482였다. 보고서는 이 계수를 4.45로 적었다. 계수 4.4482216152605는 국제 파운드 0.45359237 kg × 표준 중력 가속도 9.80665 m/s²로 계산한 값이다(실행 `python3 -c "print(0.45359237*9.80665)"` → `4.4482216152605`).
- C: 지점 쪽 차이만 0으로 바뀌면 지점 화면은 "맞았다"를 보여 주고, 본사와의 대사에서만 차이가 남는다. 금액 -500은 예시다.
- D: 판결 [447]의 숫자(£8,000이 4번 → £32,000, 차이 £24,000)가 키 검사 없이 그대로 나왔고, 파우치 ID 유일 검사로 나머지 3번이 거절됐다. 실제 시스템에서 유일성을 어디서 검사해야 했는지는 판결의 범위가 아니다.

## 쓰이는 자료구조·알고리즘

- **단위가 붙은 값(값 객체)**: 숫자와 단위를 한 타입으로 묶고 변환을 한 곳에 둔다([04](../04-entities-and-value-objects/2-summary.md) · [12](../12-time-money-and-units/2-summary.md)).
- **달력 산술**: `plusYears`·`plusMonths`는 없는 날짜를 그달 말일로 맞춘다(실행 확인 A). 직접 필드 산술은 윤일에서 예외나 조용한 이월이 된다([13](../13-instant-vs-local-time-and-tz-rules/2-summary.md)).
- **유일 키(멱등)**: 업무 ID 집합에 이미 있으면 거절한다. DB에서는 `UNIQUE` 제약([24](../24-double-entry-ledger/2-summary.md)).
- **양쪽 대사**: 두 장부를 같은 키로 맞춰 한쪽에만 있음·금액 불일치를 분류한다([25](../25-reconciliation/2-summary.md)).
- **tz 규칙 표와 판**: 지역별 오프셋 전환 목록이 판별로 바뀐다([13](../13-instant-vs-local-time-and-tz-rules/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 사고 보고서를 모델링 관점으로 읽는 순서

1. **경계를 찾는다**: 어떤 값·사실이 어느 팀·시스템 사이를 넘었나(파일, 두 장부, 에이전트 사이).
2. **계약을 찾는다**: 그 경계에 무엇이 적혀 있었나(SIS, 회계 규칙, 없음).
3. **확인하지 않은 가정을 찾는다**: 누가 무엇을 "당연히 맞다"고 믿었나.
4. **신호와 분류를 찾는다**: 이상 신호가 있었나, 누가 그것을 무엇으로 분류했나(비공식 보고, 사용자 탓, 하드웨어 고장).
5. **원문과 해석을 나눈다**: 시각·수치는 원문 그대로, 모델링 해석은 표시한다.

### 2. 내 시스템으로 옮길 점검 목록

- MCO형
  - 경계를 넘는 숫자 필드마다 단위가 이름·타입·스키마 중 하나에 있나(`impulseNs`, `Duration`, `Money`)?
  - 하류가 상류 출력의 범위·단위를 검사하는 계약 테스트가 있나([18-1](../18-context-mapping/2-summary.md))?
- Horizon형
  - 같은 사실을 두 장부가 들고 있다면, 정기 대사가 있고 차이를 **사건으로** 남기나([25-2](../25-reconciliation/2-summary.md) · [25-5](../25-reconciliation/2-summary.md))?
  - 운영자·개발사가 원장 행을 바꿀 수 있나? 바꿀 수 있다면 역분개로만, 누가 언제 무엇을 했는지 남나([24-2](../24-double-entry-ledger/2-summary.md))?
  - 같은 업무 ID가 두 번 기록될 수 있나([24-5](../24-double-entry-ledger/2-summary.md))?
- Azure형
  - 날짜 계산을 필드 산술로 하는 곳이 있나? 윤일·말일·DST 전환일을 고정 `Clock`으로 시험하나([13-5](../13-instant-vs-local-time-and-tz-rules/2-summary.md))?
  - 실패가 "응답 없음" 하나로 뭉개져 다른 원인으로 분류되지 않나([15-5](../15-basic-modeling-exercises/2-summary.md))?
- tz형
  - 미래 일정의 원본이 현지 시각 + tz ID인가? 런타임 tzdata 판을 기록하고, 판 갱신 때 재계산하나([13-1](../13-instant-vs-local-time-and-tz-rules/2-summary.md))?

### 3. 코드 — 경계의 숫자에 단위를, 날짜 계산은 달력에 (Java 21)

```java
// 경계를 넘는 값: 숫자만 보내지 않는다
public record Impulse(double value, Unit unit) {
    public enum Unit { N_S, LBF_S }
    public double toNewtonSeconds() {
        return switch (unit) {                       // default 없음: 단위 추가 시 컴파일 오류
            case N_S -> value;
            case LBF_S -> value * 4.4482216152605;
        };
    }
}

// "1년 뒤": 필드 산술 대신 달력 산술
LocalDate validTo = validFrom.plusYears(1);          // 2012-02-29 -> 2013-02-28
```

- `switch` 식에 `default`를 두지 않으면 enum 상수를 빠뜨렸을 때 컴파일 오류다([11-3](../11-state-machines-in-domain/2-summary.md)).
- "윤일의 1년 뒤"가 2월 28일인지 3월 1일인지는 도메인 규칙이다. `plusYears`의 선택(말일로 맞춤)이 업무 규칙과 같은지 확인한다(실행 확인 A).

## 장애 시나리오와 대처

### 1. 경계를 넘는 숫자에 단위가 없다 — MCO형

- **현상**: 외부·다른 팀에서 받은 값으로 계산한 결과가 서서히, 또는 일정한 배율로 어긋난다.
- **보이는 형태**: 예외 없음. 독립 계산(MCO의 도플러만 쓴 해)과 꾸준히 다른 방향의 차이. 틀린 비율이 알려진 환산 계수와 같다(4.45).
- **원인**: 단위가 명세 문서에만 있고 값·이름·타입에는 없었다. 받는 쪽이 검사할 자리가 없었다.
- **대처**: 값 객체·필드 이름·스키마에 단위를 넣는다. 받는 쪽에 범위 검사와 계약 테스트를 둔다([03-2](../03-ubiquitous-language/2-summary.md) · [12-3](../12-time-money-and-units/2-summary.md) · [18-1](../18-context-mapping/2-summary.md)).

### 2. 두 장부가 어긋나는데 한쪽만 "맞았다"를 본다 — Horizon형

- **현상**: 현장(지점)은 잔액이 맞았다고 보는데 본사 원장에는 차이가 남고, 다음 기간에 설명 안 되는 부족액이 된다.
- **보이는 형태**: 현장 화면에 경고 없음. 본사만 보는 오류 코드나 대사 차이. 2010년 문서의 표현으로 "the branch has appeared to have balanced".
- **원인**: 같은 사실을 두 장부가 들었고, 한쪽 장부만 바뀌는 경로(취소 후 재진행)가 있었다. 차이를 사건으로 공유하는 경로가 없었다.
- **대처**: 정본을 정하고 대사로 차이를 분류해 **양쪽에** 보인다. 차이를 한쪽 책임으로 자동 정정하지 않는다. 원인이 정해지기 전에는 미결 사건으로 둔다([25-5](../25-reconciliation/2-summary.md)).

### 3. 원장을 밖에서 고친다 — Horizon형

- **현상**: 회계 차이를 두고 분쟁이 생겼는데 "누가, 언제, 무엇을 바꿨나"를 증명할 수 없다.
- **보이는 형태**: 특권 사용자가 거래를 삽입·수정할 수 있는 권한이 있고, 그 사용 로그가 없다(판결 [1003]·[1008]).
- **원인**: 원장을 수정 가능한 표로 다뤘다. 정정 경로와 기록 경로가 분리되지 않았다.
- **대처**: 원장은 추가만 한다. 정정은 역분개 + 재분개, 누가 왜 했는지 같은 트랜잭션에 남긴다. UPDATE·DELETE는 권한과 트리거로 막는다([24-2](../24-double-entry-ledger/2-summary.md) · [22](../22-decision-log-and-provenance/2-summary.md)).

### 4. 같은 업무 기록이 반복되는데 사용자 실수로 보인다 — Dalmellington형

- **현상**: 같은 송금·충전이 여러 번 기록돼 차이가 생긴다. 기록만 보면 사용자가 버튼을 여러 번 누른 것처럼 보인다.
- **보이는 형태**: 같은 업무 ID(파우치 ID·주문 ID)의 기록 2건 이상. 판결 [450]의 증언 "the bug had the effect of making it look as though a user was simply doing something multiple times".
- **원인**: 유일해야 할 업무 ID를 저장 단계에서 검사하지 않았다. 중단된 처리의 재시도·재실행이 기록을 반복했다.
- **대처**: 업무 키에 `UNIQUE`, 이미 들어간 중복은 지우지 않고 역분개한다([24-5](../24-double-entry-ledger/2-summary.md)). "사용자가 두 번 했다"로 닫기 전에 같은 키의 기록 경로를 본다.

### 5. 날짜 필드 산술 + 실패 오분류 — Azure형

- **현상**: 윤일·말일에만 생성·갱신이 실패하고, 실패가 다른 원인(하드웨어·네트워크)으로 분류돼 복구 동작이 결함을 퍼뜨린다.
- **보이는 형태**: 특정 날짜 0시(UTC)부터 시작. 긴 타임아웃 뒤에야 경보(Azure: 75분). 여러 서버로 번지는 같은 실패.
- **원인**: "1년 뒤"를 연도 필드 + 1로 계산했다. 실패 원인을 남기지 않아 상위 계층이 침묵을 하드웨어 고장으로 해석했다.
- **대처**: 달력 산술을 쓰고 윤일·DST 전환일을 고정 시험 날짜로 둔다([13-5](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [26-5](../26-advanced-modeling-exercises/2-summary.md)). 실패 결과에 원인을 실어 보낸다([15-5](../15-basic-modeling-exercises/2-summary.md)).

## 핵심 문장

- (해석) 네 사건 모두 결함은 **확인하지 않은 경계**에서 생겼다: 단위 없는 숫자(MCO), 두 장부(Horizon), 날짜 필드 산술(Azure), 외부가 바꾸는 규칙(tz).
- MCO의 근본 원인은 지상 소프트웨어 파일 "Small Forces"가 명세(N·s)와 달리 lbf·s를 쓴 것이고, 항법은 추력 효과를 4.45배 과소평가했다. 오차는 예상보다 10~14배 잦은 기동으로 9개월간 쌓였다.
- Horizon 판결은 버그가 지점 회계 차이를 실제로 여러 차례 일으켰고, 시스템이 SPM에게 알리지 않았으며, Fujitsu가 지점 모르게 거래 데이터를 바꿀 수 있었다고 판단했다.
- Azure 2012는 "연도 + 1"로 만든 2013-02-29가 인증서 생성을 실패시켰고, 그 실패가 하드웨어 고장으로 분류돼 연쇄됐다.
- tz 규칙은 시행 며칠 전에 바뀌고 되돌려지기도 한다(2022f·2023b·2023c). 미래 일정은 현지 시각 + tz ID로 저장한다.
- 사고 보고서의 시각·수치는 원문 그대로 옮기고, 모델링 해석은 해석이라고 표시한다.

## 관련 주제·근거

- 선행: [27-dm-symptom-index](../27-dm-symptom-index/2-summary.md) — 증상 → leaf 역색인
- 이어지는 leaf
  - MCO: [03-ubiquitous-language](../03-ubiquitous-language/2-summary.md) · [04-entities-and-value-objects](../04-entities-and-value-objects/2-summary.md) · [12-time-money-and-units](../12-time-money-and-units/2-summary.md) · [18-context-mapping](../18-context-mapping/2-summary.md) · [19-anti-corruption-layer](../19-anti-corruption-layer/2-summary.md)
  - Horizon: [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) · [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) · [25-reconciliation](../25-reconciliation/2-summary.md) · [09-domain-events](../09-domain-events/2-summary.md)
  - Azure·tz: [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [15-basic-modeling-exercises](../15-basic-modeling-exercises/2-summary.md) · [17-subdomains](../17-subdomains/2-summary.md) · [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md) · [26-advanced-modeling-exercises](../26-advanced-modeling-exercises/2-summary.md)
- 다른 영역 실사건: [software-design/56-design-incidents](../../software-design/56-design-incidents/2-summary.md) · [database/57-db-incidents](../../database/57-db-incidents/2-summary.md) · [distributed/36-distributed-incidents](../../distributed/36-distributed-incidents/2-summary.md) · [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md)
- 다루지 않은 사건: Zune 30(2008-12-31) 윤년 정지는 1차 출처를 확인하지 못해 싣지 않았다([13-5](../13-instant-vs-local-time-and-tz-rules/2-summary.md)에 요약과 `[?]`).
- 1차 출처
  - NASA, *Mars Climate Orbiter Mishap Investigation Board Phase I Report*, 1999-11-10 <https://llis.nasa.gov/llis_lib/pdf/1009464main1_0641-mr.pdf> — Executive Summary, §2 MCO Mishap, §4 Root Cause, §5 Contributing Causes 1~8
  - *Bates and Others v Post Office Ltd (Judgment No.6 "Horizon Issues")* [2019] EWHC 3408 (QB), 2019-12-16 <https://www.judiciary.uk/wp-content/uploads/2019/12/bates-v-post-office-judgment.pdf> — [1], [428]~[432], [445]~[450], [676], [794], [824]~[825], [940], [943]~[945], [963]~[964], [968]~[978], [1003]~[1008]. 기술 부록(Technical Appendix)은 이 PDF에 없어 읽지 못했다
  - Microsoft Azure Team, "Summary of Windows Azure Service Disruption on Feb 29th, 2012" <https://azure.microsoft.com/en-us/blog/summary-of-windows-azure-service-disruption-on-feb-29th-2012/>
  - IANA tz database `NEWS` — Release 2022f, 2023a, 2023b, 2023c <https://data.iana.org/time-zones/tzdb/NEWS>
- 실험 목록
  - 네 메커니즘 모형: `scratchpad/dm/27/e28/Incidents.java` — JDK 21.0.12 temurin 일회용 컨테이너(`sn-dm-w27-e28`, `--cpus=2 --network none`, `--rm`). `docker run --rm --name sn-dm-w27-e28 --cpus=2 --network none -v $PWD:/w -w /w eclipse-temurin:21-jdk java Incidents.java`. 출력 `e28/out.txt`.
  - lbf → N 계수: `python3 -c "print(0.45359237*9.80665)"` → `4.4482216152605`(호스트 Python 3).
