# data-engineering/17-de-incidents — 정답

## 정답

### 1. 공통점과 세 축

- 공통점: 세 사건 모두 공개 자료가 서비스 정지가 아니라 틀리거나 빠진 숫자로 적는다(PHE의 적재 잡이 성공으로 표시됐는지는 공개 자료에 없다). 원천(검사 결과·고객 데이터·신용 보고서)과 파생본(집계·모델·점수) 사이의 한 단계에서 틀렸고, 그 출력을 원천이나 다른 계산과 대조하는 장치가 있어야 보였다(해석).
- 세 축

| 사건 | 유형 | 보이는 축 | 장치 |
|---|---|---|---|
| PHE | 누락 — 행이 빠짐 | 행 수(볼륨) | 파일별 행 수 대조, 한도 접근 경보 |
| Unity | 불량 입력 — 행은 있고 값이 나쁨 | 출처별 분포·유효 비율 | 출처별 품질 관문, 재구축 가능한 원본 |
| Equifax | 계산 오류 — 입력은 맞고 출력이 틀림 | 다른 계산과의 차이, 출력 분포 | 이전 중 그림자 비교, 출력 계보 |

### 2. PHE 표의 합과 두 날짜 축

- 여덟 칸 합: 957 + 744 + 757 + 0 + 1,415 + 3,049 + 4,133 + 4,786 = 15,841.
- 마지막 세 칸: 3,049 + 4,133 + 4,786 = 11,968. 발표문의 "over 75% (11,968)"와 맞다(≈ 75.6%).
- 첫 문단(배경 정보 절 첫 문단도 같다)의 "between 25 September and 2 October"는 표의 둘째 열(GOV.UK에 보고될 예정이던 날)이다. 표 바로 위 문장의 "identified via Pillar 2 testing between 24 September and 1 October"는 첫째 열(기록일)이다. 기록일의 숫자는 다음 날 공개 숫자로 흘러간다("flow though into following day's published numbers").
- 같은 건을 기록일·보고일·검체 날짜 중 무엇으로 세느냐에 따라 기간이 하루씩 다르다([06](../06-event-data-modeling/2-summary.md) 세 시각 축). 대시보드는 검체 날짜 기준으로 고쳐졌다.

### 3. 공식 자료와 언론 보도

- 공식 자료(PHE 발표·Hansard)가 뒷받침하는 것
  - 원인: 일부 파일이 "exceeded the maximum file size"(PHE). "a failure in the automated transfer of files from the labs to PHE's data systems", "a PHE legacy system"(Hancock).
  - 조치: "splits large files", 전 시스템 종단 간 점검.
- 언론 보도(BBC)에만 있는 것: 검사 기관이 CSV로 보냈고, PHE가 Excel 템플릿(XLS 형식)으로 모았으며, 템플릿당 약 65,000행·약 1,400건이 한도였다는 설명.
- XLS 시트의 65,536행 한도 자체는 Microsoft 문서로 확인된다. "PHE가 XLS를 썼다"는 BBC 보도 수준이다.
- 계산: 65,535 데이터 행 ÷ 1,400건 ≈ 46.8 → 건당 약 47행. 실제 건당 행 수는 공개 자료에서 확인하지 못했다.

### 4. `xls_cap.py`의 결과

- 처음 평평해지는 날: d6. 적재 21,845건(= 65,535행 ÷ 건당 3행). d6~d8 모두 21,845에서 멈췄다.
- 누락: d6 2,155 → d7 5,155 → d8 8,155로 날마다 커졌다. d5까지는 0이었다.
- 조용한 절단 판은 오류가 없었다. 실패를 알린 것은 행 수 대조뿐이다(`FAIL rows 65535/72000` 등).
- 파일을 나눈 판은 d6~d8을 두 파일로 나눠 전 건(24,000·27,000·30,000)을 실었다. PHE 조치 "splits large files"와 같은 방향이다.
- 말할 수 없는 것: PHE의 실제 파일 구조·건당 행 수·날짜별 건수. 누락 합계 15,465가 15,841과 비슷한 것은 우연이다. 모형은 모양(한도 전 무사 → 평평한 적재와 커지는 누락)만 보인다.

### 5. Unity의 두 문제와 영향

- 두 문제(준비 원고, CEO)
  - "a fault in our platform that resulted in reduced accuracy for our Audience PinPointer tool"
  - "we lost the value of a portion of our data training due, in part, to us ingesting bad data from a large customer"
- 영향: 2022년 약 $110M(10-Q "approximately $110.0 million in 2022, with no carry-over impacts in 2023"). CFO 원고: 2분기 약 60%, 3분기 30%, 4분기 10%. 연간 매출 가이던스를 $1,350M ~ $1,425M로 낮췄다.
- 밝히지 않은 것: 불량 데이터의 형식·필드, 플랫폼 결함의 기술 내용, 두 문제 각각의 영향 몫.

### 6. 회복 순서와 출처별 관문

- 연결(해석)
  - 모델은 학습 데이터의 파생본이다. 불량 입력이 섞인 파생본은 깨끗한 원천에서 다시 만들어야 고쳐진다([01](../01-system-of-record-and-derived-data/2-summary.md) — 파생 = 원천의 폴드).
  - "data rebuilding"은 불량 출처를 뺀 학습 데이터를 원본에서 다시 만드는 일, 즉 백필·재계산이다([08](../08-idempotent-pipelines-and-backfill/2-summary.md)). 원본이 없으면 불가능하다([02-4](../02-oltp-olap-and-warehouse/2-summary.md)).
  - 어느 모델이 어느 출처·기간의 데이터로 학습했는지 알아야 다시 만들 범위를 정한다([11](../11-data-lineage/2-summary.md) 실행 단위 계보).
- 실험 (2)
  - 전체: 15,000행 중 유효 10,500행(70%). 어느 출처가 문제인지 안 보인다.
  - 출처별: cust_0·1·2는 100%, cust_big만 25% → `QUARANTINE`. 학습 행은 9,000.

### 7. 두 Equifax 사건

- security/30의 사건은 2017년 Apache Struts 미패치로 인한 **침해**(개인정보 유출)다. 이 노트의 사건은 2022년 **신용점수 계산 오류**다. 공격자도 유출도 없다.
- 원천: 소비자 신용 보고서 데이터. 파생본: 그 데이터로 계산한 날짜 기반 속성과 신용점수(CFPB 동의 명령 ¶100 — 틀린 속성 일부도 팔렸다).
- "Information in consumer credit reports was not changed"가 중요한 이유: 이 오류가 원천을 바꾸지 않았다면 고친 코드로 속성·점수를 다시 계산할 수 있다("바뀌지 않았다"는 보고서 정보가 정확하다는 증명은 아니다). 남는 문제는 이미 나간 점수의 영향 파악이다(발표문: "collaborating with our customers to determine the actual impact").
- 후속(10-K): 2023년 1월 CFPB 집행 부서 조사 통보 → 2025년 1월 동의 명령. $15M 민사 제재금은 USIS 사업부의 소비자 이의 처리 조사와 이 코딩 문제 조사를 **함께** 종결하는 금액이다. 코딩 문제 몫은 따로 밝혀져 있지 않다.

### 8. 그림자 비교의 결과

- 100,000개 입력 중 10,808개(10.81%)가 다른 점수를 받았고, 모두 차이가 25점 이상이었다.
- 이유: 예시 버그는 한도 사용률 90% 이상(0~100 중 11개 값, 약 10.9%)에서만 단위를 잘못 읽는다. 그 구간에서는 사용률이 1/10로 줄어 점수가 크게 오른다.
- 권하는 이유: 나머지 약 89%는 두 계산이 같았다. 문제가 일부 입력 구간에만 있으면 전체 평균은 작게 움직여 묻힐 수 있다. 같은 입력을 두 계산에 넣어 하나씩 비교하면 구간과 규모가 바로 보인다(해석 — 모형).

### 9. 재적재한 날 머리 숫자가 튐

- PHE 발표문: "Today and yesterday's headline number are large due to the backlog of cases flowing through the total reporting process."
- 원인: 늦게 들어온 건을 처리(보고) 날짜에 붙여 셌다. 이벤트 날짜로 보면 지난 며칠이 조금씩 늘었을 뿐이다([06-1](../06-event-data-modeling/2-summary.md)).
- 처방: 집계는 이벤트 날짜(검체 날짜)로 하고, 해당 과거 파티션을 덮어쓰기로 다시 계산한다([08-4](../08-idempotent-pipelines-and-backfill/2-summary.md)). 보고일 숫자를 보일 때는 "밀린 건 n건 포함"을 표시한다.
