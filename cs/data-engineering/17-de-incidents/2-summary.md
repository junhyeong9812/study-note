# data-engineering/17-de-incidents — 실사건: 영국 PHE 양성 결과 15,841건 누락(2020-10) · Unity 불량 데이터 적재와 Audience Pinpointer(2022) · Equifax 신용점수 계산 오류(2022) — 파이프라인 관점 — 정리 (힌트)

## 해결하는 문제

세 사건은 모두 **숫자가 틀리거나 빠진** 사고다. 공개 자료가 적는 것은 침입이나 서비스 정지가 아니라 빠진 건수·나빠진 학습 데이터·잘못 계산된 점수다.

```text
  PHE 2020-10     검사 기관 결과 파일 → 중앙 시스템 적재 ── 파일이 "maximum file size"를 넘음 ──▶ 15,841건이 일일 집계에서 빠지고 접촉 추적 전달이 늦어짐
  Unity 2022      고객 데이터 → 광고 모델 학습 ─────────── 대형 고객의 불량 데이터 적재 ───────▶ 학습 데이터 가치 일부 상실 + 플랫폼 결함 → 2022년 매출 영향 약 $110M
  Equifax 2022    신용 데이터 → 점수 계산(레거시 서버) ───── 레거시 환경의 "coding issue" ────────▶ 약 3주간 일부 속성·점수 오계산, 25점 이상 이동 30만 명 미만
```

쉬운 예: 정수기 필터다.\
물은 계속 나온다. 수도꼭지는 고장 나지 않았다. 그런데 필터가 막혀 일부만 걸러지거나(누락), 오염된 물이 섞이거나(불량 입력), 필터 자체가 잘못 끼워져 있다(계산 오류).\
물이 나오는지가 아니라 **나온 물을 재는 장치**가 있어야 안다.

똑같은 구조다.\
세 사건 모두 "잡이 성공했나"를 묻는 감시로는 잡기 어려운 모양이다. 행 수·출처별 품질·계산 결과를 **원천이나 다른 계산과 대조하는 장치**가 있어야 보인다(해석).

실무 예:
- 사내 정산 파이프라인이 CSV를 받아 중간 형식으로 변환한 뒤 적재한다. 중간 형식에 행 한도가 있으면 PHE와 같은 모양이 된다.
- 여러 고객사 데이터를 모아 추천·광고 모델을 학습한다. 한 고객사의 데이터가 깨지면 Unity와 같은 모양이 된다.
- 계산 서버의 코드를 바꿨다. 바뀐 계산의 결과를 이전 결과와 비교하지 않으면 Equifax처럼 일부 점수가 몇 주간 틀린 채 나갈 수 있다(해석).

  - *1차 출처*: 당사자나 감독 기관이 직접 쓴 문서 — 정부 발표문, 의회 의사록, 회사의 SEC 공시·실적 발표문·보도자료. 이 노트는 날짜·수치를 원문 그대로 옮기고, 원문에 없는 연결은 "해석"이라고 표시한다. 언론 보도는 "2차 출처"로 따로 밝힌다.
  - *증상 → 사건*: 이 노트의 사건은 [16](../16-de-symptom-index/2-summary.md)의 증상(1절 잡은 성공했는데 일부만, 6절 분포 이상, 4절·5절 숫자가 바뀜)이 실제 사고가 된 모습이다.
  - Equifax 2017년 침해(Apache Struts 미패치)는 **다른 사건**이다. 그것은 [security/30-security-incidents](../../security/30-security-incidents/2-summary.md) 사건 2가 다룬다. 이 노트의 Equifax는 2022년 신용점수 계산 오류다.

## 동작·원리

### 사건 1 — 영국 PHE: 파일 크기 한도로 양성 결과가 집계에서 빠짐 (발견 2020-10-02 밤 · 발표 2020-10-04)

출처
- Public Health England, "PHE statement on delayed reporting of COVID-19 cases", GOV.UK, 2020-10-04 게시·10-05 갱신("Added background information") <https://www.gov.uk/government/news/phe-statement-on-delayed-reporting-of-covid-19-cases>(2026-10-07 열람).
- 영국 하원 의사록(Hansard) 2020-10-05 "Covid-19 Update", 보건장관 Matt Hancock 발언 — hansard.parliament.uk 웹 페이지는 2026-10-07에 접근 차단(Cloudflare 확인 페이지)이라 의회 Hansard API(`hansard-api.parliament.uk/search/contributions/Spoken.json`, 토론 ID `3DFBFED6-4B2E-4E70-9658-9D66EFB1E5DF`)로 발언 원문을 읽었다.
- 2차 출처: BBC News, Leo Kelion, "Excel: Why using Microsoft's tool caused Covid-19 results to be lost", 2020-10-05 <https://www.bbc.com/news/technology-54423988>. XLS 형식에 관한 내용은 이 보도에만 있고 위 두 공식 자료에는 없다.
- 형식 한도: Microsoft Support, "What to do if a data set is too large for the Excel grid" — ".xls file format has a limit of 65,536 rows in each sheet, while the .xlsx file format has a limit of 1,048,576 rows per sheet" <https://support.microsoft.com/en-us/office/what-to-do-if-a-data-set-is-too-large-for-the-excel-grid-976e6a34-9756-48f4-828c-ca80b3d0e15c>(2026-10-07 열람).
- 이 사건의 데이터 분석 쪽(표·스프레드시트 관점)은 data-analysis 영역의 사건 노트 [data-analysis/28-da-incidents](../../data-analysis/28-da-incidents/2-summary.md)가 맡는다. 여기서는 파이프라인 관점만 다룬다.

#### 사실 (원문)

- PHE 발표: "A technical issue was identified overnight on Friday 2 October in the data load process that transfers COVID-19 positive lab results into reporting dashboards." 15,841건(9월 25일 ~ 10월 2일)이 보고된 일일 확진자 수에 포함되지 않았다.
- 검사받은 사람은 결과를 정상적으로 받았고, 양성이면 자가격리 안내를 받았다. 빠진 것은 **보고 집계와 접촉 추적 시스템으로의 전달**이다. 남은 건은 10월 3일 오전 1시까지 접촉 추적 시스템으로 옮겼다.
- 원인(배경 정보 절): "The technical issue was caused by the fact that some files containing positive test results exceeded the maximum file size that takes these data files and loads then into central systems."
- 조치(같은 절): "A rapid mitigation has been put in place that splits large files and a full end to end review of all systems has also been instigated". 또 "There are already a number of automated and manual checks that happen throughout."
- 대시보드: "The dashboard on GOV.UK has now been updated and the correct number of cases by specimen date is shown in the cases section. Today and yesterday's headline number are large due to the backlog of cases flowing through the total reporting process."
- 날짜별 표(원문 그대로)

```text
  Date (recorded – flow though into     Expected reported date     Cases that were not included
  following day's published numbers)    for GOV.UK                 on the expected data
  24/09/2020                            25/09/2020                    957
  25/09/2020                            26/09/2020                    744
  26/09/2020                            27/09/2020                    757
  27/09/2020                            28/09/2020                      0
  28/09/2020                            29/09/2020                  1,415
  29/09/2020                            30/09/2020                  3,049
  30/09/2020                            01/10/2020                  4,133
  01/10/2020                            02/10/2020                  4,786
```

- 계산: 여덟 칸의 합은 15,841이다. 마지막 세 칸(보고 예정 9/30 ~ 10/2)의 합은 11,968이다. 발표문의 "over 75% (11,968) relate to cases that should have been reported between 30 September and 2 October"와 맞는다(11,968 ÷ 15,841 ≈ 75.6%).
- Hansard(Hancock, 2020-10-05): "This was due to a failure in the automated transfer of files from the labs to PHE's data systems." 또 "The problem emerged in a PHE legacy system. We had already decided in July to replace this system". 오전 9시 기준 해당 건의 51%가 접촉 추적 목적으로 (다시) 연락을 받았다고 말했다("contacted a second time for contact tracing purposes").
- Hansard(Hancock, 같은 날 답변): "the challenge of a maximum file size error is that it would not necessarily have appeared on that sort of flow chart".
- 2차 출처(BBC): 검사 기관은 결과를 CSV로 보냈다. PHE는 이를 자동으로 Excel 템플릿에 모아 중앙 시스템에 올렸다. PHE 개발자가 XLS 형식을 골라 템플릿 하나가 약 65,000행만 담을 수 있었다. 검사 결과 하나가 여러 행을 만들어 템플릿당 약 1,400건이 한도였다고 보도했다. 대응으로 데이터를 더 작은 묶음으로 나눠 템플릿 수를 늘렸다고 했다.

#### 원리 — 한도 있는 중간 형식 + 조용한 절단

```text
  검사 기관 CSV (한도 없음)          중간 형식 (행 한도 있음)           중앙 시스템·대시보드·접촉 추적
  ┌────────────────────┐   변환   ┌──────────────────────┐   적재   ┌───────────────────────┐
  │ 행 1                │ ───────▶ │ 행 1 … 행 한도까지      │ ───────▶ │ 받은 만큼만 집계          │
  │ …                   │          │ (넘친 행은 버려짐)      │          │ 잡은 "성공"              │
  │ 행 N  (N > 한도)     │          └──────────────────────┘          └───────────────────────┘
  └────────────────────┘                  ▲
                                          └ 경고·예외 없이 잘리면 아무 단계도 실패하지 않는다
```

- 파일당 건수가 날마다 늘면, 한도에 닿기 전까지는 아무 문제가 없다. 닿는 날부터 **넘친 만큼이 매일 더 많이** 빠진다. PHE 표에서 누락이 최근 날짜에 몰린 모양과 같다(해석 — 실제 파일별 건수는 공개 자료에 없다).
- 두 날짜 축이 나온다. 발표 첫 문단과 배경 정보 절 첫 문단은 "between 25 September and 2 October"(보고 예정일)라고 적는다. 표 바로 위 문장은 "The delayed reporting are all positive cases identified via Pillar 2 testing between 24 September and 1 October"(기록일)라고 적는다. 같은 15,841건을 다른 날짜 축으로 센 것이다(표의 두 열이 그 두 축이다). 대시보드는 "by specimen date"(검체 날짜)로 고쳐졌고, 머리 숫자(headline)는 밀린 건이 한꺼번에 들어와 커졌다. 어느 시각 축으로 날짜를 자르느냐에 따라 같은 사건이 다른 날의 숫자가 된다([06](../06-event-data-modeling/2-summary.md) 1절 · [06-1](../06-event-data-modeling/2-summary.md)).
  - *검체 날짜(specimen date)*: 검체를 채취한 날. 이벤트 시각에 해당한다. 보고일은 처리 시각에 가깝다(해석).

#### 실험: XLS 행 한도로 잘리는 적재를 행 수 대조로 잡는다 (`xls_cap.py`)

검사 결과 1건이 3행(예시)을 만들고, 날마다 건수가 늘어나는 합성 CSV를 만들었다. 중간 형식은 XLS 시트 한도(시트당 65,536행 — Microsoft 문서)를 흉내 내 넘친 행을 경고 없이 버린다. 그중 1행을 머리글로 두는 것은 모형의 가정이다. 실제 PHE 시스템의 구조·건수를 재현한 것이 아니다.

```python
XLS_MAX_ROWS = 65_536          # Microsoft: .xls 시트당 65,536행
ROWS_PER_CASE = 3              # (예시) 검사 결과 1건이 만드는 행 수

def to_template(csv_text, max_rows=XLS_MAX_ROWS, split=False):
    rows = list(csv.reader(io.StringIO(csv_text)))
    header, body = rows[0], rows[1:]
    cap = max_rows - 1                       # 머리글 1행
    if not split:
        return [[header] + body[:cap]]       # 넘친 행은 버려진다
    return [[header] + body[i:i + cap] for i in range(0, len(body), cap)]

# 대조: 원천 CSV 데이터 행 수 vs 중간 형식에 실린 데이터 행 수
loaded_rows = sum(len(t) - 1 for t in to_template(text))
check = "OK" if loaded_rows == src_rows else f"FAIL rows {loaded_rows}/{src_rows}"
```

(실험, Python 3.12.3 표준 라이브러리(`csv`·`io`), 호스트 i7-13700HX, 2026-10-07 — 결정적 입력이라 매번 같은 출력)

```text
day   src_rows  src_cases | naive_loaded  missing | split_files split_loaded | check
d1     27,000     9,000 |        9,000        0 |           1        9,000 | OK
d2     36,000    12,000 |       12,000        0 |           1       12,000 | OK
d3     45,000    15,000 |       15,000        0 |           1       15,000 | OK
d4     54,000    18,000 |       18,000        0 |           1       18,000 | OK
d5     63,000    21,000 |       21,000        0 |           1       21,000 | OK
d6     72,000    24,000 |       21,845    2,155 |           2       24,000 | FAIL rows 65535/72000
d7     81,000    27,000 |       21,845    5,155 |           2       27,000 | FAIL rows 65535/81000
d8     90,000    30,000 |       21,845    8,155 |           2       30,000 | FAIL rows 65535/90000
total missing (naive) = 15,465 of 156,000 cases
cases per template at cap = 21,845 (ROWS_PER_CASE=3)
```

- 관찰
  - d5까지는 한도(65,535 데이터 행 = 21,845건) 아래라 아무 일도 없다. d6부터 적재 건수가 21,845에서 **평평**해지고, 빠진 건수가 날마다 커진다(2,155 → 5,155 → 8,155).
  - 조용한 절단 판(naive)에는 오류가 없다. 행 수 대조(`check`)만 d6부터 `FAIL`을 냈다.
  - 파일을 한도 아래로 나누는 판(split)은 d6~d8을 두 파일로 나눠 전 건을 실었다. PHE 발표문의 조치("splits large files")와 같은 방향이다.
- 해석: 모형의 누락 합계(15,465)가 PHE의 15,841과 비슷한 것은 입력을 그렇게 고른 결과가 아니라 우연이다. 이 모형은 수치가 아니라 **모양**(한도 전 무사 → 한도 후 평평한 적재와 커지는 누락 → 대조로만 보임)을 보인다.
- 템플릿당 건수는 건당 행 수에 반비례한다. 건당 3행이면 21,845건이다. BBC가 전한 "about 1,400 cases"가 되려면 건당 약 47행이어야 한다(65,535 ÷ 1,400 ≈ 46.8 — 계산). 실제 건당 행 수는 공개 자료에서 확인하지 못했다 `[?]`.

#### 막았을 장치 (해석)

- 행 수 대조(control total): 생산자가 보낸 행 수(또는 파일의 실제 행 수)와 적재된 행 수를 파일마다 맞추고, 다르면 적재를 거부한다([10](../10-data-quality-and-data-observability/2-summary.md) 볼륨 축, [02-3](../02-oltp-olap-and-warehouse/2-summary.md) 거부 수 세기).
- 계약: 중간 형식의 한도를 계약·설계 문서에 적고, 입력 규모 추세가 한도에 다가가면 경보한다([09](../09-data-contracts-and-schema-registry/2-summary.md) — SLA·품질 기대). Hancock이 말한 대로 "maximum file size error"는 흐름도에 보이지 않는다. 한도는 따로 적어 둬야 보인다.
- 형식: 중간 단계에 행 한도가 있는 표 형식을 쓰지 않는다. 원천 CSV를 그대로 적재 영역(raw)에 두고 DB로 직접 적재한다([02](../02-oltp-olap-and-warehouse/2-summary.md) ELT).
- 관측: "적재 건수가 같은 값에서 평평한데 입력은 는다"를 경보 규칙으로 둔다([16](../16-de-symptom-index/2-summary.md) 0-2절 PLATEAU).
- leaf: [10-1](../10-data-quality-and-data-observability/2-summary.md) · [02-3](../02-oltp-olap-and-warehouse/2-summary.md) · [06-1](../06-event-data-modeling/2-summary.md) · [08-4](../08-idempotent-pipelines-and-backfill/2-summary.md)(늦게 들어온 건을 검체 날짜 파티션에 다시 계산)

### 사건 2 — Unity: 대형 고객의 불량 데이터 적재와 Audience Pinpointer 정확도 저하 (2022년 2~3월 · 발표 2022-05-10)

출처
- Unity Software Inc., Form 8-K, Exhibit 99.1 "Unity Announces First Quarter 2022 Financial Results", 2022-05-10 <https://www.sec.gov/Archives/edgar/data/1810806/000181080622000017/a2022q1ex-991.htm>(SEC EDGAR, 2026-10-07 열람).
- Unity Software Inc., Form 10-Q(2022-03-31 분기), 2022-05-10 제출 <https://www.sec.gov/Archives/edgar/data/1810806/000181080622000018/unity-20220331.htm> — 경영진 논의(Operate Solutions) 절.
- Unity Q1 2022 실적 발표 준비 원고(Prepared Remarks, 8쪽 PDF) — investors.unity.com에 게시된 문서. 원 주소(s26.q4cdn.com)는 2026-10-07에 403이라 Internet Archive 사본으로 읽었다 <https://web.archive.org/web/20220715003005/https://s26.q4cdn.com/977690160/files/doc_financials/2022/q1/Q1-2022-Prepared-Remarks.pdf>. 2022-05-13 보관본(`Q2-2022-Prepared-Remarks_F.pdf`라는 이름으로 같은 분기 자료에 링크됨)도 아래 인용 문단이 같다.

#### 사실 (원문)

- 실적 발표(2022-05-10): 1분기 매출 $320.1M(전년 대비 36% 증가). Operate Solutions 매출 $184.0M(26% 증가). 연간 가이던스를 낮췄다 — "lowering guidance for the full year ending December 31, 2022 due to challenges with monetization products that we expect to impact 2022". 2022년 매출 가이던스 $1,350M ~ $1,425M(22% ~ 28% 성장), 2분기 $290M ~ $295M.
- 10-Q(경영진 논의): "During the three months ended March 31, 2022, we experienced challenges with our Operate products that negatively affected revenue in February and March and that we expect to persist through the third quarter and have minimal impact in the fourth. These challenges with our Operate products, which included the consequences of ingesting bad data from a large customer, reduced the efficacy of such products. We see these challenges as temporary and not structural and expect them to impact our business by approximately $110.0 million in 2022, with no carry-over impacts in 2023."
- 준비 원고(CEO John Riccitiello): "we built more for growth and less for resiliency." 두 문제를 들었다.
  - "The first was a fault in our platform that resulted in reduced accuracy for our Audience PinPointer tool". 원고 안에서 제품 이름 표기가 "PinPointer"와 "Pinpointer"로 섞여 있다.
  - "The second is that we lost the value of a portion of our data training due, in part, to us ingesting bad data from a large customer."
- 같은 원고: 회복은 "data rebuilding, model training and improvement and then revenue recovery" 순서로 진행된다고 했다. 대응으로 "We are deploying monitoring, alerting and recovery systems and processes to promptly mitigate future complex data issues."
- 같은 원고(CFO Luis Visoso): $110M 영향 중 "roughly 60% impacting the second quarter, 30% third quarter and 10% the fourth quarter". 원래 연간 가이던스는 상단 기준 36% 성장이었다.
- 공개 자료가 밝히지 않은 것: 불량 데이터가 어떤 형식·필드에서 어떻게 깨졌는지, 플랫폼 결함의 기술적 내용, 두 문제가 각각 매출 영향의 얼마인지. 이 노트는 그 부분을 추정하지 않는다.

#### 원리 — 학습 데이터도 파생 데이터의 원천이다 (해석)

```text
  고객 A ─┐
  고객 B ─┼──▶ 적재 ──▶ 학습 데이터 ──▶ 모델(타기팅·입찰) ──▶ 광고 성과 ──▶ 매출(수익 배분)
  대형 고객 X ┘   (불량)        │                    │
                              └ 일부 가치 상실 ──────┴── "data rebuilding → model training" 순서로만 회복
```

- 모델은 학습 데이터의 **파생본**이다. 불량 입력이 학습 데이터에 섞이면 모델을 고치는 길은 깨끗한 입력으로 다시 학습하는 것뿐이다. 원고의 회복 순서(데이터 재구축 → 재학습 → 매출 회복)가 이 의존 순서와 같다([01](../01-system-of-record-and-derived-data/2-summary.md)의 "파생본은 원천에서 다시 만든다" — 해석).
- 출처 하나가 전체에서 차지하는 비중이 크면, 그 출처의 품질 문제가 전체 분포를 움직인다. 행 수·합계 검사만으로는 안 보일 수 있다. 출처별로 나눠 재는 검사가 필요하다([10](../10-data-quality-and-data-observability/2-summary.md) 분포 축 — 해석).
- 원고는 "monitoring, alerting and recovery systems"를 대응으로 들었다. [10](../10-data-quality-and-data-observability/2-summary.md)의 관측 5축과 [08](../08-idempotent-pipelines-and-backfill/2-summary.md)의 다시 돌리기(재구축)가 이 셋에 대응한다(해석).

#### 막았을 장치 (해석)

- 출처별 품질 관문: 학습 입력에 들어가기 전에 출처(고객)별로 유효 행 비율·분포를 재고, 기준을 넘는 출처는 격리한다(아래 적용 §2 실험 (2), [10](../10-data-quality-and-data-observability/2-summary.md) 3절 차단 vs 경고).
- 계약: 외부 고객 데이터에도 필드 의미·허용값·품질 기대를 적은 계약을 두고, 위반을 적재 시점에 거부한다([09](../09-data-contracts-and-schema-registry/2-summary.md)).
- 원본 보존과 재구축: 원본(raw)과 학습 스냅샷을 남겨, 불량 출처를 뺀 학습 데이터를 다시 만들 수 있게 한다([02-4](../02-oltp-olap-and-warehouse/2-summary.md) · [08](../08-idempotent-pipelines-and-backfill/2-summary.md)). 어느 모델이 어느 출처·기간의 데이터로 학습했는지 계보로 남긴다([11](../11-data-lineage/2-summary.md) 실행(Run) 단위 계보).
- leaf: [10-3](../10-data-quality-and-data-observability/2-summary.md)(합계는 멀쩡한데 분포가 바뀜) · [09-5](../09-data-contracts-and-schema-registry/2-summary.md)(스키마는 같고 의미만 다름) · [11-2](../11-data-lineage/2-summary.md)(왜 틀렸나 추적)

### 사건 3 — Equifax: 레거시 서버의 코딩 문제로 신용점수 계산 오류 (2022-03-17 ~ 04-06 또는 04-08 · 발표 2022-08-02)

출처
- Equifax, "Equifax Statement on Recent Coding Issue", 2022-08-02 <https://www.equifax.com/newsroom/all-news/-/story/equifax-statement-on-recent-coding-issue/>(2026-10-07 열람).
- Equifax Inc., Form 10-K(2022 회계연도), 2023-02-23 제출 <https://www.sec.gov/Archives/edgar/data/33185/000003318523000012/efx-20221231.htm> — "CFPB Matters".
- Equifax Inc., Form 10-K(2024 회계연도), 2025-02-20 제출 <https://www.sec.gov/Archives/edgar/data/33185/000003318525000025/efx-20241231.htm> — "CFPB Matters".
- 미 소비자금융보호국(CFPB), Consent Order, File No. 2025-CFPB-0002, 2025-01-17 제출 <https://files.consumerfinance.gov/f/documents/cfpb_equifax-inc-consent-order_2025-01.pdf> — 원 주소는 2026-10-07에 403이라 Internet Archive 사본(2025-01-17 보관)으로 읽었다(2026-10-07). ¶99~101·108·109.

#### 사실 (원문)

- 발표(2022-08-02): "Equifax identified a coding issue within a legacy, on-premise server environment in the U.S. slated to be migrated to the new Equifax Cloud™ infrastructure. This issue, which was in place over a period of a few weeks, impacted how some credit scores were calculated. The issue took place between March 17 and April 6. We can confirm the issue was fixed on April 6. Information in consumer credit reports was not changed as a result of this issue."
- 영향: "Our data shows that less than 300,000 consumers experienced a score shift of 25 points or more. While the score may have shifted, a score shift does not necessarily mean that a consumer's credit decision was negatively impacted." 그 기간에 신용을 신청한 소비자의 점수는 대부분 이동이 없었다고 했다.
- 같은 발표는 6월 투자자 행사에서 CEO Mark Begor가 한 말의 전문을 실었다: "We had a coding issue that was a mistake made by our technology team, in one of our legacy applications that resulted in some scores going out that had incorrect data in it." 언론 보도가 그 발언을 맥락 없이 인용했다는 해명과 함께다.
- 대응: "we are accelerating the migration of this environment to the Equifax Cloud, which will provide additional controls and monitoring that will help to detect and prevent similar issues in the future." 영향 파악은 "We are collaborating with our customers to determine the actual impact to consumers."
- 10-K(2022 회계연도): 2023년 1월 CFPB가 집행 부서에서 이 코딩 문제("impacted how some credit scores were calculated during a three-week period in 2022")를 조사하겠다고 알려 왔다.
- CFPB 동의 명령 ¶100: 2022-03-17 Online Model Server(OMS)의 코드 변경으로, 날짜 기반 속성(예: 신용카드 60일 연체 이력 여부)을 그때의 날짜가 아니라 고정된 날짜로 계산했다. 점수 모델이 이 잘못된 속성에 적용돼 일부 점수가 틀렸고, 회사는 틀린 점수와 일부 틀린 속성을 팔았다. "This coding error persisted until April 8, 2022." — Equifax 발표의 수정일(4월 6일)과 다르다. 이 노트는 어느 쪽이 맞는지 판정하지 않는다.
- 같은 명령 ¶108: CFPB는 회사가 "introduced 'test code' in a production environment in a scoring model server"라고 적었다. ¶101: 10점 이상 낮게 계산된 소비자 60만 명 이상, 25점 이상 하락 139,000명(¶109는 "more than 100,000"이 25점 넘게 하락이라고 적는다). Equifax 발표의 "30만 명 미만"은 방향을 밝히지 않은 "score shift of 25 points or more"라, CFPB의 하락 기준 숫자와 같은 셈인지 알 수 없다.
- 10-K(2024 회계연도): 2025년 1월 CFPB와 동의 명령(consent order)을 맺었다. 이 명령은 USIS 사업부의 소비자 이의 처리 조사와 이 코딩 문제 조사를 **함께** 종결했고, 민사 제재금 $15M을 요구한다. 회사는 일부 업무 관행을 바꾸기로 했다. $15M 중 코딩 문제에 해당하는 몫은 10-K에 나뉘어 있지 않다.

#### 원리 — 원천은 그대로이고 파생 계산이 틀렸다

```text
  신용 보고서 데이터(원천) ──▶ 속성·점수 계산(레거시 서버, 약 3주간 코딩 문제) ──▶ 속성·점수(파생) ──▶ 대출 기관의 결정
          변경 없음                              ✗                                 일부 틀림           영향은 고객사와 함께 파악
```

- 발표문은 "Information in consumer credit reports was not changed"라고 적는다. 이 오류가 원천(신용 보고서 정보)을 바꾸지는 않았고, 그 원천에서 계산한 **파생값**(날짜 기반 속성과 점수 — CFPB ¶100)이 틀렸다. "바뀌지 않았다"는 보고서 정보가 정확하다는 증명은 아니다. 원천이 이 오류로 바뀌지 않았다면 파생값은 고친 코드로 다시 계산할 수 있다([01](../01-system-of-record-and-derived-data/2-summary.md) · [08](../08-idempotent-pipelines-and-backfill/2-summary.md) — 해석).
- 어려운 쪽은 **이미 나간** 파생값이다. 틀린 점수(일부는 속성도)는 그 기간 동안 대출 기관의 결정에 쓰였다. 누가 어떤 점수를 받아 어떤 결정을 했는지 추적하려면, 언제 어떤 계산(코드 버전·환경)으로 만든 값이 누구에게 나갔는지의 기록이 필요하다([11](../11-data-lineage/2-summary.md) 실행 단위 계보 — 해석). 발표문의 "collaborating with our customers to determine the actual impact"가 그 추적이다.
- CFPB가 적은 경위는 운영 환경의 점수 서버에 들어간 "test code"다(¶108). 발표문은 그 환경을 "이전 예정 레거시 환경"이라고 적지만, 당시 새 환경이 같은 계산을 함께 돌리고 있었는지, 결과를 비교하는 장치가 있었는지는 공개 자료에 없다. 이 노트가 **제안하는** 탐지책은 바뀐 계산과 이전 계산(또는 새 환경)을 같은 입력으로 돌려 차이를 세는 것이다(그림자 비교 — [07-1](../07-batch-stream-architectures/2-summary.md)의 "두 경로 대조"와 같은 장치, 해석).

#### 막았을 장치 (해석)

- 분포 관측: 일별 점수 분포(평균·분위·구간별 비율)를 기준선과 비교한다. 수십만 명의 25점 이상 이동은 분포 지표로 보일 수 있다. 다만 공개 자료는 그 이동이 전체 분포에서 얼마나 컸는지 밝히지 않는다([10](../10-data-quality-and-data-observability/2-summary.md) 분포 축 · [10-3](../10-data-quality-and-data-observability/2-summary.md)).
- 그림자 비교: 운영에 올리는 계산 변경은 이전 계산과 같은 입력으로 함께 돌려 차이를 센다. 이전 중인 환경이면 새 환경과도 같은 방식으로 비교한다(아래 적용 §2 실험 (3)).
- 출력 기록: 점수마다 계산 코드 버전·환경·시각을 남겨, 오류 기간에 나간 값을 바로 골라낸다([11](../11-data-lineage/2-summary.md) · [06](../06-event-data-modeling/2-summary.md)의 봉투 필드 — version·source).
- leaf: [10-3](../10-data-quality-and-data-observability/2-summary.md) · [07-1](../07-batch-stream-architectures/2-summary.md) · [11-2](../11-data-lineage/2-summary.md) · [08-2](../08-idempotent-pipelines-and-backfill/2-summary.md)(과거 값을 다시 계산할 때 그때의 규칙과 고친 코드를 구분)

### 세 사건을 나란히 (해석)

| | 무엇이 깨졌나 | 어디서 | 공개된 숫자 | 보이게 했을 장치 | leaf |
|---|---|---|---|---|---|
| PHE 2020 | 파일이 최대 크기를 넘어 일부 결과가 적재되지 않음 | 검사 기관 파일 → 중앙 시스템 적재(레거시) | 15,841건, 그중 11,968건이 마지막 3일 | 파일별 행 수 대조, 한도 접근 경보 | [10-1](../10-data-quality-and-data-observability/2-summary.md) · [02-3](../02-oltp-olap-and-warehouse/2-summary.md) · [06-1](../06-event-data-modeling/2-summary.md) |
| Unity 2022 | 두 문제 — 플랫폼 결함 → Audience Pinpointer 정확도 저하, 대형 고객의 불량 데이터 적재("in part") → 학습 데이터 가치 일부 상실 | 고객 데이터 → 학습 → 광고 모델 | 2022년 매출 영향 약 $110M(2Q 60%·3Q 30%·4Q 10%) | 출처별 품질 관문, 분포 관측, 재구축 가능한 원본 | [10-3](../10-data-quality-and-data-observability/2-summary.md) · [09](../09-data-contracts-and-schema-registry/2-summary.md) · [11](../11-data-lineage/2-summary.md) |
| Equifax 2022 | 레거시 서버의 코딩 문제(CFPB: 운영 서버의 "test code")로 속성·점수 계산 오류 | 신용 데이터 → 점수 계산(이전 예정 환경) | 약 3주간, 25점 이상 이동 30만 명 미만(Equifax) | 점수 분포 관측, 이전 중 그림자 비교, 출력 계보 | [10-3](../10-data-quality-and-data-observability/2-summary.md) · [07-1](../07-batch-stream-architectures/2-summary.md) · [11-2](../11-data-lineage/2-summary.md) |

- 공통점: 세 사건 모두 공개 자료가 서비스 정지가 아니라 틀리거나 빠진 숫자로 적는다(PHE에서 적재 잡이 성공으로 표시됐는지는 공개 자료에 없다). 원천(검사 결과·고객 데이터·신용 보고서)과 파생본(집계·모델·점수) 사이의 단계에서 틀렸고, 그 단계의 출력을 원천이나 다른 계산과 **대조하는 장치**가 있어야 보였다.
- 공통점 2: 세 사건 모두 문제를 **레거시** 단계에 두거나(PHE "legacy system", Equifax "legacy, on-premise server environment") **회복력**의 부족으로 설명한다(Unity "less for resiliency"). 교체 예정 시스템일수록 관측·대조 투자가 미뤄지기 쉽다는 읽기는 해석이다.
- 차이: PHE는 **누락**(행이 빠짐 — 행 수로 보임), Unity는 **불량 입력**(행은 있는데 값이 나쁨 — 분포로 보임), Equifax는 **계산 오류**(입력은 맞는데 출력이 틀림 — 다른 계산과의 대조로 보임)다. 장치가 다른 축에 있다.

## 쓰이는 자료구조·알고리즘

- **행 수 대조(control total)**: 보낸 쪽이 센 수와 받은 쪽이 센 수를 맞춘다. PHE형 누락의 1차 장치([10](../10-data-quality-and-data-observability/2-summary.md) 볼륨 축).
- **출처별 그룹 집계**: `GROUP BY source`로 유효 비율·분포를 나눠 잰다. 큰 출처 하나의 문제가 전체 평균에 묻히지 않게 한다(Unity형).
- **분포 비교**: 기준선 대비 평균·분위·구간별 비율, 이동 평균·EWMA([10](../10-data-quality-and-data-observability/2-summary.md)).
- **그림자 비교(차분)**: 같은 입력에 두 구현을 돌려 결과 차이를 센다(Equifax형, [07](../07-batch-stream-architectures/2-summary.md)의 두 경로 대조).
- **계보 그래프 순회**: 오류 기간의 출력이 어느 하류(고객·모델·대시보드)로 갔는지 찾는다([11](../11-data-lineage/2-summary.md), [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 내 파이프라인으로 옮길 점검 목록

```text
  □ 단계마다 입력 행 수와 출력 행 수를 세고, 차이(거부·필터)를 0이 아닌 숫자로 남기나?         (PHE)
  □ 중간 형식·버퍼·API 페이지에 행·크기 한도가 있나? 한도를 문서에 적고, 입력 추세가 다가가면 경보하나?  (PHE)
  □ 같은 사건을 어느 날짜(검체·기록·보고)로 세는지 정해 두었나? 밀린 건이 들어올 때 어느 날짜에 붙나?   (PHE · 06)
  □ 외부·고객 데이터를 출처별로 나눠 품질을 재고, 기준 밖 출처를 격리할 수 있나?                (Unity)
  □ 불량 출처를 뺀 학습·집계 데이터를 원본에서 다시 만들 수 있나? 어느 모델이 어느 데이터로 학습했나?  (Unity · 01 · 11)
  □ 계산을 옮기는 동안 옛 환경과 새 환경의 결과를 같은 입력으로 비교하나?                       (Equifax)
  □ 출력값마다 계산 코드 버전·환경·시각이 남아, 오류 기간에 나간 값을 골라낼 수 있나?             (Equifax · 11)
```

### 2. 실험: 세 사건형 장치의 모형 (`LoadGuards.java`)

세 장치를 합성 데이터로 돌렸다. (1)의 숫자는 위 `xls_cap.py`의 d5·d6 **건수**를 행 수 자리에 옮겨 온 예시다(검사 결과 1건 = 1행으로 둔 셈). (2)의 큰 고객 불량 비율 75%와 (3)의 레거시 버그는 예시다. 세 회사의 실제 시스템을 재현한 것이 아니다.

```java
// (1) PHE형: 생산자가 보낸 행 수(control total)와 적재된 행 수를 맞춘다
String verdict = b.loadedRows == b.declaredRows ? "OK" : "REJECT (missing " + (b.declaredRows - b.loadedRows) + ")";

// (2) Unity형: 출처별로 유효 행 비율을 재고, 기준 아래인 출처는 학습 입력에서 격리
long valid = e.getValue().stream().filter(r -> r.value >= 0 && r.value <= 1).count();
boolean ok = (double) valid / e.getValue().size() >= minValidRatio;

// (3) Equifax형: 이전 중 레거시 계산과 새 계산을 같은 입력으로 돌려 차이를 센다(그림자 비교)
int correct = score(utilPct, months, false);
int legacy = score(utilPct, months, true);      // 레거시 쪽에만 있는 버그(예시)
if (Math.abs(correct - legacy) >= threshold) shifted++;

static int score(int utilPct, int months, boolean bug) {
    int util = bug && utilPct >= 90 ? utilPct / 10 : utilPct;   // 예시 버그: 90% 이상에서 단위를 잘못 읽음
    return Math.max(300, Math.min(850, 700 - 2 * util + Math.min(months, 120) / 2));
}
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--rm --pull never --network none --cpus=2 -u`, i7-13700HX, 2026-10-07 — 고정 시드라 매번 같은 출력)

```text
(1) control total
  lab_a    declared= 21,000 loaded= 21,000  OK
  lab_b    declared= 24,000 loaded= 21,845  REJECT (missing 2155)
(2) per-source validity gate (min 99%)
  cust_0     rows= 3,000 valid=100.0%  use
  cust_1     rows= 3,000 valid=100.0%  use
  cust_2     rows= 3,000 valid=100.0%  use
  cust_big   rows= 6,000 valid= 25.0%  QUARANTINE
  training rows kept=9,000 of 15,000
(3) shadow compare legacy vs new
  inputs=100,000  differ=10,808  |diff|>=25: 10,808 (10.81%)
```

- 관찰
  - (1) 행 수 대조는 잘린 파일을 적재 단계에서 거부했다. 조용한 절단이 "REJECT"라는 보이는 실패로 바뀐다.
  - (2) 전체로 보면 15,000행 중 유효 행이 9,000 + 1,500 = 10,500(70%)이다. 출처별로 나누면 cust_big 하나가 25%라는 것이 바로 보인다. 격리 뒤 학습 행은 9,000이다.
  - (3) 예시 버그는 한도 사용률 90% 이상 입력에서만 나서 10.81%의 입력이 다른 점수를 받았다. 나머지 89%는 두 계산이 같았다. 문제가 일부 입력 구간에만 있으면 전체 평균은 크게 움직이지 않을 수 있어, 입력 전수에 대한 그림자 비교가 더 직접적인 장치다(해석).
- 이 모형의 임계값(99%, 25점)은 예시다. 25점은 Equifax 발표문이 영향 규모를 말할 때 쓴 기준을 빌렸을 뿐, 그 회사의 탐지 기준이 아니다.

### 3. 사건 뒤 복구 순서 (세 사건의 공통 — 해석)

```text
  1. 오류 기간을 확정한다       시작(첫 FAIL·첫 분포 이탈) ~ 끝(수정 배포)
  2. 영향받은 출력을 고른다      그 기간·그 경로로 나간 값 (계보·출력 기록)
  3. 원천에서 다시 계산한다      파티션 덮어쓰기로 — 재실행이 2배를 만들지 않게(08-1)
  4. 숫자가 바뀐 것을 알린다     어느 날짜 축으로 다시 붙였는지(PHE의 검체 날짜), 머리 숫자가 왜 튀는지
  5. 같은 검사를 파이프라인에 남긴다
```

## 장애 시나리오와 대처

### 1. 중간 단계의 한도에서 입력이 조용히 잘린다 — PHE형

- **현상**: 정산·집계 대시보드의 최근 며칠 숫자가 원천보다 적다. 차이가 날마다 커진다. 잡은 모두 성공이다.
- **보이는 형태**: 파일·배치별 적재 행 수가 같은 값(예: 65,535)에서 반복된다. 원천 행 수는 계속 는다(`xls_cap.py` d6~d8: 21,845에서 평평, 누락 2,155 → 8,155).
- **원인**: 중간 형식·버퍼·API 페이지의 행·크기 한도. 넘친 부분을 경고 없이 버린다.
- **대처**: 파일별 행 수 대조로 적재를 거부한다. 한도 없는 형식으로 바꾸거나 한도 아래로 나눈다. 빠진 건은 원천에서 이벤트 날짜(검체 날짜) 파티션으로 다시 적재하고, 머리 숫자가 한꺼번에 튀는 이유를 함께 알린다([08-4](../08-idempotent-pipelines-and-backfill/2-summary.md)).

### 2. 한 출처의 불량 데이터가 모델·집계 전체를 흐린다 — Unity형

- **현상**: 추천·광고 모델의 성과 지표가 몇 주에 걸쳐 떨어진다. 코드 배포는 없었다.
- **보이는 형태**: 전체 행 수·합계는 정상이다. 출처별로 나누면 큰 고객 하나의 유효 비율·분포가 크게 다르다(실험 (2): cust_big 25%).
- **원인**: 출처를 구분하지 않은 품질 검사, 학습 입력에 대한 차단 관문 없음.
- **대처**: 출처별 품질 관문을 학습 입력 앞에 둔다. 불량 출처를 뺀 학습 데이터를 원본에서 다시 만들고 재학습한다. 어느 모델이 어느 출처·기간의 데이터로 학습했는지 계보로 남긴다([11](../11-data-lineage/2-summary.md) · [02-4](../02-oltp-olap-and-warehouse/2-summary.md)).

### 3. 이전 예정 레거시 환경에서만 계산이 틀린다 — Equifax형

- **현상**: 같은 고객의 점수·등급이 어떤 요청에서는 다르게 나간다. 원천 데이터는 그대로다.
- **보이는 형태**: 오류 기간 동안 점수 분포의 일부 구간이 움직인다. 두 환경을 같은 입력으로 비교하면 특정 입력 구간에서만 차이가 난다(실험 (3): 10.81%의 입력).
- **원인**: 운영 계산 서버에 들어간 코드 결함(Equifax 사례에서 CFPB가 적은 경위는 운영 환경의 "test code" — ¶108). 바뀐 계산의 결과를 이전 계산과 비교하는 장치가 없으면 이런 결함이 몇 주간 보이지 않을 수 있다(해석 — Equifax에 그런 장치가 있었는지는 공개 자료에 없다).
- **대처**: 이전 기간 동안 그림자 비교를 상시로 돌린다. 출력마다 코드 버전·환경을 기록해 오류 기간의 값을 골라내고, 그 값을 받은 하류(고객)에 알린다([07-1](../07-batch-stream-architectures/2-summary.md) · [11-2](../11-data-lineage/2-summary.md)).

### 4. 복구 재적재가 머리 숫자를 한꺼번에 튀게 한다

- **현상**: 누락분을 다시 넣은 날, 대시보드의 "오늘 신규"가 평소의 몇 배다. 사람들이 급증으로 오해한다.
- **보이는 형태**: 보고일 기준 숫자만 튄다. 이벤트 날짜(검체 날짜) 기준으로 보면 지난 며칠이 조금씩 늘었을 뿐이다. PHE 발표문은 "Today and yesterday's headline number are large due to the backlog"라고 적었다.
- **원인**: 늦게 들어온 건을 처리 날짜에 붙여 셌다([06-1](../06-event-data-modeling/2-summary.md)).
- **대처**: 집계는 이벤트 날짜로 하고, 해당 과거 파티션을 덮어쓰기로 다시 계산한다([08-4](../08-idempotent-pipelines-and-backfill/2-summary.md)). 보고일 숫자를 함께 보이면 "밀린 건 n건 포함"을 표시한다.

### 5. 틀린 값이 누구에게 나갔는지 모른다

- **현상**: 계산 버그를 고쳤는데, 버그 기간에 나간 값의 목록을 만들 수 없다. 영향 파악에 몇 주가 걸린다.
- **보이는 형태**: 출력 테이블에 계산 시각·코드 버전이 없다. 하류(고객사·모델·대시보드) 목록이 사람 기억에만 있다.
- **원인**: 실행 단위 계보·출력 기록이 없다. Equifax 발표문의 "collaborating with our customers to determine the actual impact"가 이 단계다(해석).
- **대처**: 출력마다 실행 ID·코드 버전·시각을 남긴다. 계보 그래프의 하류 순회로 영향 범위를 만든다([11-1](../11-data-lineage/2-summary.md) · [11-2](../11-data-lineage/2-summary.md)).

## 핵심 문장

- 세 사건 모두 공개 자료가 서비스 정지가 아니라 틀리거나 빠진 숫자로 적는다. 원천과 파생본 사이의 한 단계가 틀렸고, 그 단계의 출력을 대조하는 장치가 있어야 보였다.
- PHE: 일부 파일이 "maximum file size"를 넘어 15,841건이 일일 집계에서 빠지고 접촉 추적 전달이 늦어졌다. 그중 11,968건(75% 이상)이 마지막 3일분이었다. 행 수 대조가 이 모양(한도 전 무사 → 한도 후 평평한 적재와 커지는 누락)을 잡는다. XLS 형식이라는 설명은 언론 보도(BBC)에 있고 공식 발표에는 없다.
- Unity: 원고가 든 두 문제는 플랫폼 결함(Audience Pinpointer 정확도 저하)과 학습 데이터 가치 일부 상실(그 원인의 일부가 대형 고객의 불량 데이터 적재)이다. 회사는 2022년 매출 영향을 약 $110M로 공시했다. 출처별 품질 관문과 다시 만들 수 있는 원본이 장치다.
- Equifax: 이전 예정 레거시 서버의 코딩 문제로 2022-03-17부터 일부 속성·신용점수가 잘못 계산됐다. 끝난 날은 Equifax 발표가 04-06, CFPB 동의 명령이 04-08로 다르다. Equifax 발표 기준 25점 이상 이동한 소비자는 30만 명 미만이었다. 이 오류가 신용 보고서 정보(원천)를 바꾸지는 않았다. 이후 CFPB 조사를 거쳐 2025년 1월 다른 조사와 함께 $15M 제재금의 동의 명령으로 종결됐다(10-K).
- 누락은 행 수로, 불량 입력은 출처별 분포로, 계산 오류는 다른 계산과의 비교로 보인다. 장치가 서로 다른 축에 있다.

## 관련 주제·근거

- 선행: [16](../16-de-symptom-index/2-summary.md)(증상 역색인)
- 사건별 leaf: [01](../01-system-of-record-and-derived-data/2-summary.md) · [02](../02-oltp-olap-and-warehouse/2-summary.md) · [06](../06-event-data-modeling/2-summary.md) · [07](../07-batch-stream-architectures/2-summary.md) · [08](../08-idempotent-pipelines-and-backfill/2-summary.md) · [09](../09-data-contracts-and-schema-registry/2-summary.md) · [10](../10-data-quality-and-data-observability/2-summary.md) · [11](../11-data-lineage/2-summary.md)
- 다른 영역 사건: [security/30-security-incidents](../../security/30-security-incidents/2-summary.md)(Equifax 2017 침해 — 이 노트와 다른 사건) · [database/57-db-incidents](../../database/57-db-incidents/2-summary.md) · [distributed/36-distributed-incidents](../../distributed/36-distributed-incidents/2-summary.md) · [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md) · [architecture/23-arch-incidents](../../architecture/23-arch-incidents/2-summary.md)
- 데이터 분석 쪽(PHE 사건의 표·스프레드시트 관점): [data-analysis/28-da-incidents](../../data-analysis/28-da-incidents/2-summary.md) 사건 4
- 1차 출처
  - PHE, "PHE statement on delayed reporting of COVID-19 cases", GOV.UK 2020-10-04(10-05 갱신) — 본문·배경 정보 절·날짜별 표 <https://www.gov.uk/government/news/phe-statement-on-delayed-reporting-of-covid-19-cases>
  - UK Parliament Hansard, House of Commons 2020-10-05 "Covid-19 Update"(Matt Hancock) — Hansard API 검색 결과의 발언 원문(토론 ID `3DFBFED6-4B2E-4E70-9658-9D66EFB1E5DF`)
  - Microsoft Support, "What to do if a data set is too large for the Excel grid" — .xls 65,536행·.xlsx 1,048,576행
  - Unity, Form 8-K Ex. 99.1(2022-05-10) · Form 10-Q(2022-03-31 분기, 2022-05-10 제출) · Q1 2022 Prepared Remarks(Internet Archive 사본)
  - Equifax, "Equifax Statement on Recent Coding Issue"(2022-08-02) · Form 10-K 2022 회계연도(2023-02-23)·2024 회계연도(2025-02-20) "CFPB Matters"
  - CFPB, Consent Order 2025-CFPB-0002(2025-01-17) ¶99~101·108·109 — Internet Archive 사본 <https://files.consumerfinance.gov/f/documents/cfpb_equifax-inc-consent-order_2025-01.pdf>
- 2차 출처: BBC News, Leo Kelion, 2020-10-05 "Excel: Why using Microsoft's tool caused Covid-19 results to be lost"(XLS·템플릿·약 1,400건)
- 열지 못한 것: CFPB의 2025년 Equifax 관련 보도자료(consumerfinance.gov 403). 동의 명령 원문은 Internet Archive 사본으로 읽었다.
- 실험 목록
  - `xls_cap.py` — Python 3.12.3 표준 라이브러리(`csv`·`io`), 호스트: 합성 CSV 8일치를 XLS 시트 한도(65,536행) 모형으로 옮겨 조용한 절단 vs 파일 나누기, 행 수 대조
  - `LoadGuards.java` — eclipse-temurin:21-jdk(OpenJDK 21.0.12), docker `--rm --pull never --network none --cpus=2 -u`: (1) 행 수 대조 (2) 출처별 유효 비율 관문 (3) 레거시 vs 새 계산 그림자 비교
