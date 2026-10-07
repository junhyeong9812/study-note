# data-engineering/16-de-symptom-index — 증상 사전: 잡은 성공했는데 0행·합계 2배·과거 리포트가 바뀜·대시보드마다 다른 숫자·컬럼이 갑자기 NULL·WAL 디스크 풀·삭제했는데 남아 있음·재처리 불가 → 보이는 형태·원인 후보·확인 방법·leaf — 정리 (힌트)

## 해결하는 문제

이 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"grain이 다른 행을 한 팩트에 넣었다 → 합계 줄이 섞인다 → 매출이 2배"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 숫자 하나다. "대시보드 9월 매출이 결제 DB의 2배", "어제 날짜가 비어 있는데 잡은 초록", "지난달 지역별 매출이 바뀌었다".

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                                  이 노트 (역방향)
  모델·파이프라인 --> 깨지는 조건 --> 어긋난 숫자          숫자 --> 보이는 형태 --> 원인 후보 --> 확인 방법 --> leaf
  "append 잡을 재실행하면 행이 2배"                      "정확히 2배다. 먼저 파티션 안 중복 행과 재시도 기록"
```

쉬운 예: 은행 계좌의 월말 대사(對査)다.\
가계부 잔액과 통장 잔액이 다르면, 차이가 **얼마인지**부터 본다.\
차이가 정확히 한 건 금액이면 한 번 빠뜨린 것이다. 두 배면 두 번 적은 것이다. 매달 같은 금액이면 자동이체 하나를 빠뜨린 것이다.

똑같은 구조다.\
데이터 파이프라인의 장애는 크래시로 보이지 않는다. **잡은 초록인데 숫자가 틀린** 모양으로 보인다([README](../README.md) 머리 문단).\
그래서 에러 메시지 대신 **어긋남의 모양**(0, 정수배, 일정 비율, 특정 값에서 평평, 날짜 경계, 과거만)이 첫 단서다.

실무 예:
- 재무팀이 "대시보드가 결제 DB와 12만 원 다르다"고 한다. 오케스트레이터는 전부 초록이다. 로그에는 에러가 없다.
- 이때 볼 것은 로그가 아니라 **원천과 적재본의 파티션별 행 수·합계 대조**다. 차이의 모양이 원인 후보를 고른다.

  - *역색인*: "leaf → 증상" 목록을 "증상 → leaf" 목록으로 뒤집은 것([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
  - *leaf 표기 `NN-k`*: 이 영역 NN번 노트의 「장애 시나리오와 대처」 k번째 시나리오다. 예: `08-1` = [08](../08-idempotent-pipelines-and-backfill/2-summary.md)의 시나리오 1(append 재실행 → 행 2배).
  - *대조(reconciliation)*: 같은 사실을 두 곳에서 세어 맞춰 보는 검사. 여기서는 원천(기록 시스템)과 파생본(웨어하우스·마트·검색 인덱스)의 행 수·합계를 파티션(날짜)별로 비교한다.
    - 흔한 오해: "잡이 성공했으니 데이터도 맞다." 잡의 성공은 "SQL이 오류 없이 끝났다"는 뜻이다. 0행 `INSERT`도 성공이다([10-1](../10-data-quality-and-data-observability/2-summary.md)).

## 동작·원리

### 0. 증상 지도 — 어느 단계의 가정이 깨졌나

```text
   증상                              깨진 가정                                  단계(노트)                       절
   ────                              ────────                                  ─────────                        ──
   잡은 성공했는데 0행·일부만          "입력이 왔고, 다 실렸다"                     적재·관측(10, 08, 07)              1
   합계가 2배(정수배)·이상한 비율        "한 행 = 한 사실, 한 번만, 더해도 되는 값"      grain·멱등·가산성(03, 08, 13, 07, 04)  2
   합계가 조금 적다                   "버린 행이 없다"                            변환·조인·늦은 데이터(02, 03, 04, 08)  3
   과거 리포트가 바뀜                 "확정된 과거는 그대로다"                      이력·규칙·시각(04, 08, 06)           4
   대시보드마다 다른 숫자              "같은 이름 = 같은 정의·같은 시각"              경로·정의·시간대(07, 06, 15, 01)     5
   컬럼이 갑자기 NULL·"기타" 급증       "상류 스키마·값 집합이 그대로다"               계약·품질(09, 10, 11)               6
   소비자 역직렬화 실패·재생 때만 실패    "옛 레코드도 새 코드로 읽힌다"                호환성(09)                         7
   WAL 디스크 풀·CDC 끊김              "소비자가 따라오고 있다"                     CDC 슬롯(05)                       8
   삭제했는데 남아 있음                "원천을 지우면 사본도 지워진다"               삭제 전파(12, 05, 11, 01)            9
   재처리 불가                        "원천을 다시 읽을 수 있다"                    보존·원본(07, 01, 02, 05, 14)        10
   느려짐·비용 증가                   "분석과 운영이 자원을 나누지 않는다"           저장소·모델(02, 08, 13, 14, 12)       11
   "왜 틀렸나"를 못 찾음·주인 없음      "누가 무엇을 어디서 만드는지 안다"             계보·조직(11, 06, 15, 13, 10)        12
```

- 커리큘럼 16번 행이 든 여덟 증상이 1·2·4·5·6·8·9·10절의 머리다. 3·7·11·12절은 leaf 시나리오의 나머지 증상이다.
- 다른 영역 색인과 겹치는 곳
  - SQLSTATE·DB 에러 문구, `pg_wal` 증가의 엔진 쪽 원인(아카이브 실패 등)은 [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md)가 정본이다.
  - 메시지 중복·유실·순서 역전의 전달 쪽 원인은 [distributed/35-distributed-symptom-index](../../distributed/35-distributed-symptom-index/2-summary.md)가 정본이다.
  - 이 노트는 그 증상이 **분석 숫자로 어떻게 보이는가**와 모델·파이프라인 쪽 원인을 맡는다.

### 0-1. 색인을 쓰기 전에 확보할 것

```text
  ① 대조 숫자   원천 vs 적재본의 파티션(날짜)별 행 수·합계 — "얼마나, 어느 날짜에" 어긋났나
  ② 잡 기록     실행 시각·재시도 횟수·적재 행 수(INSERT n)·입력 파일 수와 크기
  ③ 시각 축     이벤트 시각 / 수집 시각 / 처리 시각 중 무엇으로 날짜를 잘랐나, 어느 시간대인가
  ④ 변경 이력   상류 스키마 버전, 변환 코드 배포, 백필·재처리 실행, 차원 갱신 시각
```

- ①이 없으면 2·3절을 가를 수 없다. "적다"와 "2배"는 처방이 반대다.
- ③이 없으면 4·5절을 가를 수 없다. 날짜 경계에서만 어긋나는 숫자는 대부분 시각 축 문제다([06-1](../06-event-data-modeling/2-summary.md) · [06-5](../06-event-data-modeling/2-summary.md)).
- ④는 "언제부터"를 준다. 숫자가 바뀐 날과 배포·백필 날이 겹치면 원인 후보가 크게 준다([11-2](../11-data-lineage/2-summary.md)).

### 0-2. 어긋남의 모양으로 먼저 가른다

```text
  적재본 / 원천 (같은 파티션)
     │
     ├─ 0                                  ──▶ 빈 입력·경로 변경·지운 뒤 못 씀            1절
     ├─ 정확히 2, 3 …(정수배)                ──▶ 재실행 append·grain 혼합·이력 행 곱         2절
     ├─ 1보다 약간 큼(1.0x), 키 중복           ──▶ 경계 중복·재전송·삭제 미반영               2절 · 9절
     ├─ 1보다 약간 작음, 날마다 들쭉날쭉         ──▶ 필터·inner join·늦은 데이터              3절
     ├─ 원천은 느는데 적재본이 같은 값에서 평평    ──▶ 고정 한도에서 잘림(파일·시트·배치 크기)      1절 · 17 사건 1
     ├─ 며칠 합계는 같고 날짜별로만 다름          ──▶ 시각 축·시간대                          4절 · 5절
     ├─ 행 수 같고 합계만 일정 비율로 다름         ──▶ 의미·규칙 변경(부가세, 요율)               4절 · 6절
     └─ 총합은 같고 분포(지역·세그먼트)만 다름     ──▶ 차원 덮어쓰기·NULL·키 쪼개짐              4절 · 6절
```

#### 실험: 파티션 대조 결과를 모양으로 분류한다 (`Reconcile.java`)

원천과 적재본의 파티션별 (행 수, 합계)를 받아 위 그림의 규칙으로 모양을 붙였다. 데이터는 합성이고, 분류 규칙은 이 노트가 만든 모형이다(어떤 도구의 기능이 아니다). 각 줄은 leaf 실험이나 사건의 어긋남을 흉내 냈다.

```java
static String shape(Part p, Map<Long, Integer> dstCountFreq) {
    if (p.srcRows == p.dstRows && p.srcSum == p.dstSum) return "OK";
    if (p.srcRows > 0 && p.dstRows == 0) return "ZERO        -> 빈 입력·경로 변경 (10-1)";
    if (p.srcRows > 0 && p.dstRows > p.srcRows && p.dstRows % p.srcRows == 0 && p.dstSum == p.srcSum * (p.dstRows / p.srcRows))
        return "MULTIPLE x" + (p.dstRows / p.srcRows) + " -> append 재실행·grain 혼합 (08-1, 03-1)";
    if (p.dstRows < p.srcRows && dstCountFreq.get(p.dstRows) > 1)
        return "PLATEAU     -> 고정 한도에서 잘림 (17 사건 1)";
    if (p.dstRows < p.srcRows) return "MISSING " + (p.srcRows - p.dstRows) + " -> 필터·inner join·늦은 데이터 (02-3, 03-3, 08-4)";
    if (p.dstRows > p.srcRows) return "EXTRA " + (p.dstRows - p.srcRows) + "   -> 경계 중복·삭제 미반영 (05-3, 05-4)";
    return "VALUE       -> 행 수 같고 값만 다름: 의미·규칙 변경 (09-5, 08-2)";
}
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--rm --pull never --network none --cpus=2`, i7-13700HX, 2026-10-07)

```text
ds     src_rows dst_rows   src_sum    dst_sum  shape
10-01     1000     1000    250000     250000  OK
10-02     1000     2000    250000     500000  MULTIPLE x2 -> append 재실행·grain 혼합 (08-1, 03-1)
10-03     1000        0    250000          0  ZERO        -> 빈 입력·경로 변경 (10-1)
10-04     1000      964    250000     241000  MISSING 36 -> 필터·inner join·늦은 데이터 (02-3, 03-3, 08-4)
10-05    80000    65535  20000000   16383750  PLATEAU     -> 고정 한도에서 잘림 (17 사건 1)
10-06    90000    65535  22500000   16383750  PLATEAU     -> 고정 한도에서 잘림 (17 사건 1)
10-07     1000     1003    250000     250750  EXTRA 3   -> 경계 중복·삭제 미반영 (05-3, 05-4)
10-08     1000     1000    250000     227273  VALUE       -> 행 수 같고 값만 다름: 의미·규칙 변경 (09-5, 08-2)
```

- 관찰: 행 수와 합계 두 숫자만으로 여덟 파티션이 일곱 모양으로 갈렸다. 10-05·10-06은 원천이 80,000 → 90,000으로 늘었는데 적재본이 둘 다 65,535에서 멈췄다. "늘어나는 입력 + 같은 값에서 평평한 출력"은 한도의 표지다.
- 한계(모형): 규칙은 **후보**를 고를 뿐 원인을 확정하지 않는다. 예를 들어 정수배는 append 재실행([08-1](../08-idempotent-pipelines-and-backfill/2-summary.md))일 수도, 이력 테이블 조인의 곱([13-3](../13-data-vault/2-summary.md))일 수도 있다. grain 혼합([03-1](../03-dimensional-modeling/2-summary.md))은 행 수가 정확한 배수가 아닐 수 있어 이 규칙에 안 걸릴 수 있다. 03번 실험 데이터라면 상세 1,200행 + 합계 줄 600행 = 1,800행(1.5배)이고 합계는 2배라, 이 규칙으로는 `EXTRA 600`이 된다(계산 — 이 실험에 넣어 돌린 것은 아니다). 다음 절의 확인 방법으로 좁힌다.
- 정수배 규칙 앞의 `p.srcRows > 0`은 원천 0행 · 적재본 양수인 파티션에서 `%`가 0으로 나누지 않게 막는다(Java 정수 나눗셈은 `ArithmeticException`). 그런 파티션은 `EXTRA`로 간다. 이 조건이 없던 판에 원천 0행 · 적재 5행 파티션을 넣어 돌리면 `/ by zero`로 멈췄고, 넣은 판은 `EXTRA 5`를 냈다(재실행, 같은 환경). 위 여덟 줄의 출력은 두 판이 같다.
- 10-08의 227,273은 250,000 ÷ 1.1의 반올림(부가세 10% 포함 → 제외, 예시)이다. 행 수가 같아 행 수 검사로는 안 보이고 합계·분포 검사로만 보인다([09-5](../09-data-contracts-and-schema-registry/2-summary.md)).

### 1. 잡은 성공했는데 0행·일부만 실렸다

```text
  대시보드에 어제가 비었다 / 숫자가 반토막 — 오케스트레이터는 초록
     │
     ├─ 적재 행 수 0, INSERT 0 0, exit=0 ─────────────────▶ 상류 빈 파일·경로·파티션 이름 변경          10-1
     ├─ 0행 사고 뒤 며칠간 반토막이 경보 없이 지나감 ─────────▶ 이상값이 기준선(EWMA)을 오염              10-5
     ├─ 새벽 몇 분간만 0·빈칸, 그때 받은 리포트가 나감 ───────▶ DELETE·INSERT를 따로 커밋                 08-5
     ├─ 원천은 느는데 적재 행 수가 같은 값에서 평평 ──────────▶ 파일·시트·배치의 고정 한도에서 절단          17 사건 1
     └─ 재처리 잡 성공, 결과 날짜 수가 기대보다 적음 ─────────▶ 로그 보존이 재처리 구간보다 짧음            07-2 (10절)
```

| 보이는 형태 (숫자·지표·로그) | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 감사 테이블 `rows_loaded = 0`, 적재 로그 `INSERT 0 0`, 잡 `exit=0`. 데이터 기준 신선도(`now() - max(event_time)`) 2일 이상 | 상류 내보내기가 빈 파일을 만들었다. 경로·파티션 이름이 바뀌어 아무것도 못 읽었다. SQL은 0행을 오류로 보지 않는다 | 입력 파일 목록·크기, 적재 행 수 이력, `max(event_time)` | [10-1](../10-data-quality-and-data-observability/2-summary.md) |
| 0행 사고 직후부터 볼륨 경보가 며칠 조용하다. 감시 밴드 폭이 갑자기 넓어졌다(10번 실험 ±6,377 → ±13,813) | 이상으로 판정한 값까지 평균·분산 갱신에 넣었다 | 기준선 계산에 들어간 날짜 목록, 사고일 제외 표시 유무 | [10-5](../10-data-quality-and-data-observability/2-summary.md) |
| 잡 실행 시각과 겹치는 짧은 0·빈칸(08번 실험 6b: 덮어쓰는 중 읽기 0건) | DELETE와 INSERT가 각각 자동 커밋됐다. INSERT가 실패하면 파티션이 빈 채로 남는다 | 잡 SQL의 트랜잭션 경계, 잡 실패 이력과 빈 파티션 대조 | [08-5](../08-idempotent-pipelines-and-backfill/2-summary.md) |
| 파일·배치별 적재 행 수가 특정 값(예: 65,535)에서 반복된다. 원천 행 수는 계속 는다 | 중간 형식·버퍼·API 페이지의 행 한도에서 조용히 잘렸다 | 파일별 원천 행 수 vs 적재 행 수, 적재 행 수의 최빈값 | [17 사건 1](../17-de-incidents/2-summary.md) |

- 처방의 방향: 0행·볼륨 급감은 **차단** 검사로 둔다(경고가 아니라 하류 게시를 막는다 — [10](../10-data-quality-and-data-observability/2-summary.md) 3절). 신선도는 잡 실행 시각이 아니라 데이터 안의 이벤트 시각으로 잰다([10-2](../10-data-quality-and-data-observability/2-summary.md)).

### 2. 합계가 2배(정수배)다

먼저 **배수가 정수인지**, 그리고 **어느 축에서만 부푸는지**를 본다. 모든 축에서 같은 배수면 행 복제가 유력하고, 특정 차원·특정 지표에서만 부풀면 조인 곱이 유력하다.

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 재시도가 있던 날 일 매출·주문 수가 정확히 2배(또는 재시도 횟수 배). 같은 `ds`에 행 여러 개(08번 실험: 1행 → 2행, 25,000 → 50,000) | 출력이 `INSERT`(append)라 재실행마다 쌓인다 | `SELECT ds, count(*) … GROUP BY ds HAVING count(*) > 1`, 스케줄러 재시도 기록 | [08-1](../08-idempotent-pipelines-and-backfill/2-summary.md) |
| 매출 `SUM`이 원천의 2.00배. 팩트에 `line_no = 0` "합계 줄"이 섞임. grain 키 중복 검사는 통과 | 한 팩트에 서로 다른 grain(상세 줄 + 주문 합계) | grain 문장 대조, `line_no`·행 유형별 합계 | [03-1](../03-dimensional-modeling/2-summary.md) |
| 배송비만 2배(03번 실험 1,350,000 → 2,700,000), 상품 매출은 맞다. 상세 줄 많은 주문이 많은 지역일수록 더 부풂 | 주문 grain 값이 상세 grain과 조인되며 줄 수만큼 복제 | 리포트 SQL에서 팩트–팩트 직접 조인 여부 | [03-2](../03-dimensional-modeling/2-summary.md) |
| 월말 잔액이 실제의 수십 배(30일 같은 잔액이면 정확히 30배) | 반가산 지표(잔액)를 시간 축으로 `SUM` | 지표의 가산성 표시, 기간 집계 함수 | [03-5](../03-dimensional-modeling/2-summary.md) |
| 마트의 고객 한도 합이 원천의 몇 배, 한 고객이 여러 행(13번 실험 3 × 2 = 6행, 12,000 vs 3,000) | Satellite 둘을 최신 행 고르기 없이 키로 조인 → 이력 행끼리 곱 | 마트에서 "키당 1행" 검사, PIT 사용 여부 | [13-3](../13-data-vault/2-summary.md) |
| 재처리 직후 대시보드 매출이 거의 2배(07번 실험 96,000 → 196,000), 재처리 구간만 | 재처리 잡이 운영 출력(테이블·토픽)에 더했다 | 재처리 잡의 출력 대상, 출력 반영 방식(증분 vs 덮어쓰기) | [07-3](../07-batch-stream-architectures/2-summary.md) |
| 9월 매출이 결제 합보다 많다. 한 팩트가 차원 두 행에 맞음(04번 실험 `matched_rows 2`, 900 → 1,800) | SCD Type 2 유효 기간 겹침 | 04번 진단 (1)(2): `tstzrange … && …`, `lead(valid_from)` 이웃 대조 | [04-2](../04-slowly-changing-dimensions/2-summary.md) |
| "현재 고객 수"가 원천보다 많다. as-is 리포트에서 한 고객이 두 지역 | 현재 행 플래그(`is_current`)가 둘인 멤버 | 04번 진단 (3): `WHERE is_current GROUP BY … HAVING count(*) > 1` | [04-4](../04-slowly-changing-dimensions/2-summary.md) |
| 초기 적재 직후 같은 PK 행이 둘(덧붙이는 하류), 원천보다 조금 많음 | CDC 스냅샷과 스트림 시작 위치의 경계 중복 | PK 중복 검사, 스냅샷 시점 vs 슬롯 생성 위치 | [05-3](../05-change-data-capture/2-summary.md) |
| 네트워크가 불안정했던 날 주문 수가 2% 많음(06번 실험 2,040행 vs 2,000) | 생산자 재전송 + 이벤트 ID 없음 | 내용이 같은 행 묶음 수, 봉투에 `id`가 있나 | [06-2](../06-event-data-modeling/2-summary.md) |

- 배수가 아니라 **말이 안 되는 비율**(월간 전환율 62%, 실제 0.0232)이면 비가산 지표(비율)를 `SUM`·`AVG`한 것이 첫 후보다. 일별 전환율 컬럼의 집계 함수와 팩트에 분자·분모가 있는지 확인한다([03-4](../03-dimensional-modeling/2-summary.md)).
- 하지 말 것: 리포트 SQL에 `DISTINCT`를 붙여 숫자를 맞춘다. grain 혼합·조인 곱은 그대로 남고, 진짜로 같은 값인 서로 다른 사건까지 지운다(06번 실험: 내용 기반 제거가 2,002건을 2,000건으로).

### 3. 합계가 조금 적다 — 에러 없이 빠진다

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 잡 성공. `src_rows 10000 / dw_rows 9964`. 일자별로 매일 1~2행씩 빠짐 | 변환 단계가 형식이 다른 행을 필터로 걸러 냈다. 거부 수를 아무도 세지 않았다 | 원천 vs 웨어하우스 일자별 행 수·합계, 거부 행 테이블 유무 | [02-3](../02-oltp-olap-and-warehouse/2-summary.md) |
| 신상품 출시 주 카테고리별 매출 합 < 결제 합(03번 실험 inner join 합 12,217,500 vs 팩트 합 13,217,500). 카테고리 표에는 빠진 흔적 없음 | 차원 키 매칭 실패(NULL) + inner join | 팩트의 NULL·`-1` 차원 키 수, inner vs left join 합계 차 | [03-3](../03-dimensional-modeling/2-summary.md) |
| 특정 고객의 며칠 치 매출이 지역별 리포트에서 빠짐(04번 실험 `matched_rows 0`) | SCD Type 2 유효 기간 빈틈 | 04번 진단 (2)의 `gap`, 마지막 행만 닫혀 현재 행이 없는 멤버는 진단 (4) | [04-3](../04-slowly-changing-dimensions/2-summary.md) |
| 어제 매출이 원천보다 조금 적고 일주일이 지나도 안 맞음(08번 실험 10-01 원천 107 vs 마트 100) | 늦게 온 행의 이벤트 날짜 파티션을 재계산하지 않음 | `ingested_at > last_run_at`인 행의 이벤트 날짜 분포 | [08-4](../08-idempotent-pipelines-and-backfill/2-summary.md) |
| 초기 적재 직후 적재 시각 근처의 행 몇 개가 없다 | CDC 스냅샷·스트림 경계의 누락 | 원천과 하류의 PK 차집합(`EXCEPT`) | [05-3](../05-change-data-capture/2-summary.md) |
| 키 폐기 다음 날 지난 분기 매출이 줄었다(12번 실험 103,000 → 32,000) | 보존·집계에 남겨야 할 금액을 지울 연락처와 같은 주체 키로 암호화 + 복호 실패 행을 건너뛰는 집계 | 복호 실패 행 수, 암호화 범위 설계 | [12-4](../12-data-retention-and-erasure/2-summary.md) |

- 처방의 방향: "버린 행"을 0이 아닌 숫자로 남긴다. 거부 행 테이블과 거부 수 지표([02-3](../02-oltp-olap-and-warehouse/2-summary.md)), `-1`(Unknown) 차원 행과 그 수([03-3](../03-dimensional-modeling/2-summary.md)), 복호 실패 수([12-4](../12-data-retention-and-erasure/2-summary.md)).

### 4. 과거 리포트가 바뀐다

먼저 **무엇이 바뀌었나**를 본다. 총합은 그대로이고 분포만 바뀌었으면 차원(속성)이, 총합이 바뀌었으면 팩트 계산(규칙·시각)이 원인 후보다.

```text
  "지난달 숫자가 달라졌어요"
     │
     ├─ 총합 그대로, 지역·등급별 분포만 이동 ─────────────▶ 차원을 Type 1로 덮어씀           04-1
     ├─ 월말 며칠 매출이 이번 달 바뀐 속성으로 잡힘 ─────────▶ 늦게 온 팩트가 현재 행에 붙음     04-5
     ├─ 백필 기간 지표가 일정 비율로 이동(−17%) ───────────▶ 현재 규칙으로 과거를 재계산       08-2
     ├─ 날짜별 값만 바뀌고 며칠 합계는 거의 같음 ───────────▶ 처리 시각으로 날짜를 자름          06-1
     └─ 오늘 오후의 "오늘 매출"이 내일 아침 바뀜 ───────────▶ 실시간 경로와 배치 경로의 규칙 차   07-1 (5절)
```

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 팩트 행 수·합계 그대로, 지역별 분포만 이동(04번 실험 8월 seoul 300 → 행 없음, busan 700 → 1,000). 차원에 `updated_at`이 최근인 행 | SCD Type 1 덮어쓰기로 이력 소실 | 리포트에 쓰인 차원 속성의 SCD 유형, 차원 행의 최근 갱신 | [04-1](../04-slowly-changing-dimensions/2-summary.md) |
| 지난달 말 매출 일부가 이번 달 바뀐 지역으로(04번 실험 8/30 판매가 `customer_key 102`) | 팩트 적재가 대리 키를 `is_current`로 찾음 | 팩트의 사건 시각 vs 붙은 차원 행의 유효 기간 | [04-5](../04-slowly-changing-dimensions/2-summary.md) |
| 마감된 9월 수수료가 백필 뒤 바뀜(08번 실험 90,000 → 75,000) | 규칙(요율)이 코드 상수거나 "현재" 값으로 조인 | 백필 전 스냅샷과 비교(08번 진단의 `fee_before_backfill`) | [08-2](../08-idempotent-pipelines-and-backfill/2-summary.md) |
| 날짜별 값이 원천의 이벤트 시각 기준과 다르지만 며칠 합계는 거의 같음(06번 실험 10-01 998건, 진실 1,000). 재처리하면 또 바뀜 | 처리 시각·적재 시각으로 날짜를 자름 | 집계 SQL의 날짜 컬럼, 자정 전후 행의 세 시각 비교 | [06-1](../06-event-data-modeling/2-summary.md) |

- 숫자가 바뀐 것을 **재현**하려면 그때의 상태가 있어야 한다. 마감 리포트를 스냅샷 테이블로 남기거나, 레이크하우스면 태그로 고정한다([14-3](../14-lakehouse-table-formats/2-summary.md)). 만료된 스냅샷으로는 "그때 숫자"를 다시 뽑지 못한다.

### 5. 대시보드마다 숫자가 다르다

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 실시간 대시보드의 어제 매출 ≠ 아침 정산 리포트, 날짜별 차이 매일 1~3%(데이터마다 다름. 07번 실험 23:59 99,000 → 다음 날 100,000) | 같은 지표를 두 코드베이스(속도·배치 계층)가 다른 규칙으로 계산 | 두 경로의 날짜 기준·중복 제거 규칙 비교, 날짜별 대조 | [07-1](../07-batch-stream-architectures/2-summary.md) |
| BI 도구의 "10월 1일" ≠ 배치 리포트. 한쪽의 이른 아침 매출이 다른 쪽 전날로(06번 실험 KST 00~09시 375건). 날짜별 차이는 그날과 다음 날 이른 아침 매출의 차라, 하루 매출이 고르면 거의 상쇄되고 새벽 매출이 출렁이는 날·기간 양 끝 날짜에서 크게 보인다 | 한 도구는 UTC 자정, 다른 도구는 KST 자정 | 각 도구의 세션 시간대, 저장 타입(`timestamp` vs `timestamptz`) | [06-5](../06-event-data-modeling/2-summary.md) |
| 같은 회의에서 활성 사용자가 505·183·580(15번 실험 같은 로그로 118~580). 각 팀 SQL은 맞다 | 도메인을 넘나드는 다의어("활성")의 전역 정의 부재 | 지표 정의(식·기간·소유 도메인) 대조 | [15-2](../15-data-mesh-and-data-products/2-summary.md) |
| CRM과 주문 DB의 고객 등급이 다르다. 양쪽 다 직접 수정 화면 | 같은 사실에 쓰기 경로가 둘(원천 미정) | 사실(컬럼)별 원천 역할표, 양방향 동기화 잡 유무 | [01-1](../01-system-of-record-and-derived-data/2-summary.md) |
| 목록 화면 금액 ≠ 상세 화면(01번 실험 `mismatched 50, diff_sum 25000`). 새 기능 경로에서만 | 비정규화 사본의 갱신 경로 누락 | 원천 vs 사본 `EXCEPT`, 쓰기 경로별 사본 갱신 여부 | [01-3](../01-system-of-record-and-derived-data/2-summary.md) |
| 대시보드 합계 ≠ 운영 DB | 변환 실패 행 무음 스킵(3절과 같은 원인) | 일자별 행 수·합계 대조 | [02-3](../02-oltp-olap-and-warehouse/2-summary.md) |
| "어제 매출"이 실은 그제 숫자. 대시보드는 "최근 업데이트: 방금" | 신선도를 잡 실행 시각으로 표시 | `max(event_time)`과 표시 시각 비교 | [10-2](../10-data-quality-and-data-observability/2-summary.md) |
| 매출이 하루 사이 약 10% 하락, 주문 수는 그대로 | 스키마는 같고 의미만 변경(부가세 포함 → 제외, 예시) | 주문당 평균 금액 분포, 계약의 "의미" 칸 변경 이력 | [09-5](../09-data-contracts-and-schema-registry/2-summary.md) |

- 두 숫자 중 어느 쪽이 맞는지 정하려면 **원천**이 정해져 있어야 한다. 원천이 둘이면 판정 규칙이 없다([01-1](../01-system-of-record-and-derived-data/2-summary.md)).

### 6. 컬럼이 갑자기 NULL이다 · "기타"가 급증한다

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 지역별 대시보드가 특정 날부터 "(NULL)" 하나로. 잡 성공, 에러 없음. `region` NULL 비율 0% → 100% | 상류가 필드 이름 변경(`region` → `region_code`). JSON 경로 접근은 없는 키를 NULL로 | 원천 키 집합 diff(새 키 등장), 날짜별 NULL 비율 | [09-1](../09-data-contracts-and-schema-registry/2-summary.md) |
| 주문 상태 "기타"가 0% → 33% | enum 새 값 + `CASE … ELSE '기타'` | 허용값 검사, 상태별 고유값 목록 diff | [09-2](../09-data-contracts-and-schema-registry/2-summary.md) |
| 합계·주문 수는 그대로인데 세그먼트별 "알 수 없음"이 커짐(10번 실험 customer_id NULL 0% → 40%) | 필드 이름 변경·조인 키 형식 변경·수집 SDK 버그 등(실험은 원인까지 보이지 않음) | 컬럼별 NULL 비율을 같은 요일 기준선과, 계보로 상류 추적 | [10-3](../10-data-quality-and-data-observability/2-summary.md) |
| 상류가 컬럼을 지운 지 사흘 뒤 지역별 대시보드가 빔. 하류 일부는 오류, 일부는 NULL로 성공 | 변경 전에 하류 목록을 볼 수 없었다(컬럼 수준 계보 없음) | 컬럼 수준 계보의 하류 BFS(INDIRECT 간선 포함) | [11-1](../11-data-lineage/2-summary.md) |
| 카테고리 매출에 "Unknown"(`-1`) 몫이 커짐 | 차원 적재가 팩트보다 늦음(늦게 온 차원) | `-1` 행 수 지표, 차원·팩트 적재 시각 | [03-3](../03-dimensional-modeling/2-summary.md) |

### 7. 소비자가 역직렬화에 실패한다 · 재생할 때만 실패한다

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 생산자 배포 직후 소비자 lag 누적, 로그에 역직렬화 예외 반복(별도 reader 스키마로 읽는 Avro 소비자라면 `missing required field` 꼴. 기본 `GenericRecord` 소비자는 없는 필드를 쓰는 앱 코드에서 드러날 수 있다) | 호환성 검사 `NONE` — 기본값 없는 필드 추가·필수 필드 삭제가 그대로 등록 | subject 호환성 설정, 실패 레코드의 스키마 ID | [09-3](../09-data-contracts-and-schema-registry/2-summary.md) |
| 운영 소비자는 멀쩡, 새 소비자를 `earliest`로 붙이거나 재처리하면 특정 오프셋에서 실패(최신 스키마를 reader로 고정한 소비자 기준). 실패 레코드의 스키마 ID가 오래된 버전 | 비transitive `BACKWARD` — 새 버전이 직전 버전과만 검사됨 | 버전 이력의 모든 쌍 호환성, 실패 오프셋의 스키마 ID | [09-4](../09-data-contracts-and-schema-registry/2-summary.md) |

### 8. WAL 디스크가 찬다 · CDC가 조용히 끊긴다

```text
  운영 PG 디스크 사용률이 며칠에 걸쳐 꾸준히 상승
     │
     ├─ pg_replication_slots: active=f, inactive_since 며칠 전, wal_status=extended ─▶ 소비자 없는 슬롯이 WAL 보존   05-1
     │                                                                              (디스크가 이미 찼다면 database/19 장애 2)
     ├─ 디스크는 안 찼는데 하류가 어느 시점부터 멈춤, wal_status=lost ──────────────▶ max_slot_wal_keep_size 초과로 슬롯 무효화   05-5
     └─ (MySQL) 커넥터가 재시작 실패, "새 스냅샷 필요" ────────────────────────────▶ binlog 보존 만료                   05-2 (10절)
```

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| `active=f`, `retained` 수십~수백 GB, `pg_ls_waldir()` 합계가 `max_wal_size`보다 훨씬 큼(05번 실험 48 MB → 160 MB) | 커넥터가 죽었거나 내려간 뒤 슬롯을 지우지 않음. 슬롯은 `restart_lsn` 이후 WAL을 붙든다 | 05번 적용 §2의 슬롯 쿼리(`pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)`), `pg_ls_waldir()` 합계 | [05-1](../05-change-data-capture/2-summary.md) |
| `wal_status=lost`, `invalidation_reason=wal_removed`, 서버 로그 `invalidating obsolete replication slot`, 커넥터 쪽 `can no longer get changes from replication slot` | 커넥터 지연이 `max_slot_wal_keep_size`를 넘어 슬롯 무효화 | `safe_wal_size` 추이, 하류의 마지막 반영 시각 | [05-5](../05-change-data-capture/2-summary.md) |

- 엔진 쪽 원인(아카이브 실패 등)과 디스크가 찼을 때의 처리는 [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md) 장애 2·[database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md)가 정본이다.
- 상한(`max_slot_wal_keep_size`)은 슬롯 때문에 WAL이 무한정 쌓이는 위험을 줄인다. 대신 소비자가 상한보다 더 뒤처지면 체크포인트 때 슬롯이 무효화(`lost`)될 수 있다([05](../05-change-data-capture/2-summary.md) 6절). 슬롯이 따라잡으면 끊기지 않고, 디스크는 슬롯 말고 다른 이유(아카이브 실패 등)로도 찰 수 있다. 상한을 걸었다면 `safe_wal_size` 경보가 짝이다.

### 9. 삭제했는데 남아 있다

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 삭제 완료로 답한 사람의 정보가 분석 대시보드·검색에 보임(12번 실험 원천 0행, 파생 다섯 테이블에 잔존) | 삭제가 원천 한 곳에서 끝남. 사본 목록·경로별 절차 없음 | 계보 기반 사본 목록으로 잔존 탐색, 사본별 삭제 ack | [12-1](../12-data-retention-and-erasure/2-summary.md) |
| 장기 보존 토픽·이벤트 저장소에 평문 PII, 삭제 요청을 처리할 수 없음 | 불변 로그에 개인정보를 섞음 | 토픽·이벤트 스키마의 PII 필드 목록 | [12-2](../12-data-retention-and-erasure/2-summary.md) |
| 키를 지웠는데 어느 서비스에서 여전히 연락처가 보임(12번 실험: 메모리의 키 사본으로 복호 성공) | 키 캐시·로그에 찍힌 키·백업된 키 저장소 | 키 캐시 TTL, 키 저장소 백업 보존 기한 | [12-5](../12-data-retention-and-erasure/2-summary.md) |
| 원천에서 지운 상품이 검색·집계에 계속 나옴. 하류 `count(*)`가 원천보다 많고 차이가 시간에 따라 커짐(05번 실험 원천 6행·650 → 하류 9행·950) | CDC 소비자가 `op=d`·tombstone을 무시하거나 null 값 레코드를 건너뜀 | 원천 vs 하류 행 수 추이, 소비 코드의 delete 분기 | [05-4](../05-change-data-capture/2-summary.md) |
| 마케팅 도구에서 삭제 요청자에게 메일이 나감. 계보 도구에 그 내보내기의 컬럼 계보가 "미상" | `SELECT *` 내보내기를 정적 파싱이 펼치지 못함 | PII 컬럼 하류 DIRECT 순회, "미상" 노드 목록 | [11-3](../11-data-lineage/2-summary.md) |
| 운영자가 인덱스에서 숨긴 상품이 다음 재색인 뒤 다시 보임(반대 방향의 "남아 있음") | 파생본만 고쳤다. 재구축은 원천을 다시 접는다 | 원천의 해당 행 상태(`visible`) | [01-2](../01-system-of-record-and-derived-data/2-summary.md) |

- "원천 `count(*) = 0`"은 삭제 완료의 증거가 아니다. 사본 목록 전체에서 확인 검색을 돌린 결과가 증거다([12-1](../12-data-retention-and-erasure/2-summary.md) 대처).

### 10. 재처리할 수 없다

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 30일 재처리 잡이 "성공", 결과에는 최근 9~10일만(07번 실험 v1 30일·3,000건 → v2 9일·880건, 재실행 10일·906~995건 — 실행마다 다름, 에러 없음). `kafka-get-offsets --time earliest`가 0이 아님 | 보존(`retention.ms`)이 재처리 구간보다 짧아 앞 세그먼트 삭제 | 토픽의 가장 이른 오프셋·시각 vs 재처리 시작 시각 | [07-2](../07-batch-stream-architectures/2-summary.md) |
| 프로젝터 버그를 고쳤는데 조회 모델을 재구축할 수 없음 | 원천 이벤트 보존 기간이 재구축 요구보다 짧음, 원천이 현재 상태만 있음 | 원천의 보존 기간·가장 오래된 기록 | [01-4](../01-system-of-record-and-derived-data/2-summary.md) |
| 3개월 전부터의 변환 버그를 고쳤는데 과거를 다시 계산할 수 없음 | 변환 전 원본을 남기지 않은 ETL | raw 층 존재 여부·보존 기간 | [02-4](../02-oltp-olap-and-warehouse/2-summary.md) |
| (MySQL) 주말 동안 내려 둔 커넥터가 다시 안 뜸, "새 스냅샷이 필요" 오류 | binlog 보존 기간(`binlog_expire_logs_seconds`) 만료 | 커넥터가 저장한 binlog 위치 vs `SHOW BINARY LOGS` | [05-2](../05-change-data-capture/2-summary.md) |
| "9월 말 기준으로 다시 뽑아 달라"는 `TIMESTAMP AS OF` 쿼리 실패 | 스냅샷 만료 정책이 재현 요구보다 짧음 | 테이블의 가장 오래된 스냅샷 시각, 태그 유무 | [14-3](../14-lakehouse-table-formats/2-summary.md) |
| v2 재처리를 시작한 지 며칠이 지나도 LAG가 줄지 않음 | 파티션 수가 병렬도 상한, 출력 DB가 대량 쓰기를 못 받음 | `kafka-consumer-groups --describe`의 LAG 추이, 출력 DB 쓰기 지연 | [07-4](../07-batch-stream-architectures/2-summary.md) |

- 원인은 두 갈래다. 대부분은 **다시 읽을 원본이 없거나 보존 기간이 요구보다 짧다**. [07-4](../07-batch-stream-architectures/2-summary.md)만 다르다. 원본은 있는데 재처리 처리량(파티션 수·출력 DB 쓰기)이 따라잡지 못한다. 재처리 요구 기간(얼마나 과거까지 다시 돌려야 하나)을 정하고, 원천 보존·raw 층·아카이브·스냅샷 태그를 그 기간에 맞춘다.

### 11. 느려진다 · 비용이 계속 는다

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 매일 아침 9시 무렵 주문 API p99가 몇 배(02번 실험 0.40~0.52 ms → 1.45~2.78 ms). `pg_stat_activity`에 BI 계정의 긴 `GROUP BY` | 운영 DB에서 분석 쿼리 | `pg_stat_activity`의 계정·시작 시각, 리포트 일정 | [02-1](../02-oltp-olap-and-warehouse/2-summary.md) |
| 리포트용 팔로워에서 `canceling statement due to conflict with recovery`, 재생 지연 증가 | 긴 조회와 리더 vacuum 기록 재생의 충돌 | 팔로워의 `pg_last_wal_receive_lsn()`과 `pg_last_wal_replay_lsn()` 차이(`now() - pg_last_xact_replay_timestamp()`는 리더에 쓰기가 없어도 커져 단독 증거가 아니다) | [02-2](../02-oltp-olap-and-warehouse/2-summary.md) |
| 1년치 백필 시작 뒤 운영 p99·복제 지연 상승, 정규 잡 밀림 | 백필이 원천을 직접 대량 읽기, 파티션 동시 실행 과다 | 백필 동시 실행 수, 원천 DB I/O·`replay_lag` | [08-3](../08-idempotent-pipelines-and-backfill/2-summary.md) |
| 고객 리포트가 새 원천이 붙을 때마다 느려짐. `EXPLAIN`에 조인 수십 단(13번 실험 k=32에서 실행 156~206ms vs 마트 1.6~1.9ms) | Satellite 폭증 + 볼트 직접 조회 | 리포트 쿼리의 조인 수, PIT·마트 유무 | [13-2](../13-data-vault/2-summary.md) |
| Satellite 행 수가 매일 원천 행 수만큼 증가 | hashdiff에 매번 바뀌는 컬럼, 컬럼 순서·NULL 표기 불일치(후보) | payload가 같은 연속 행 찾기 | [13-5](../13-data-vault/2-summary.md) |
| 쿼리 계획이 실행보다 오래 걸림, 파티션당 파일 수만(14번 모형 실험 파일 10 → 100,000개에서 계획 0.02~0.06 ms → 63~81 ms) | 작은 파일 폭증 | 메타데이터 테이블의 `file_count`·평균 파일 크기 | [14-1](../14-lakehouse-table-formats/2-summary.md) |
| 행 수는 그대로인데 버킷 용량·비용이 매달 증가, compaction 뒤에도 안 줄어듦 | 스냅샷 미만료 — 옛 스냅샷이 옛 파일을 붙듦 | `snapshots` 수·가장 오래된 `committed_at` | [14-2](../14-lakehouse-table-formats/2-summary.md) |
| 같은 테이블에 쓰는 잡 둘이 가끔 실패, 재시도 증가(14번 모형 실험 8 작성자 400커밋에 시도 1,371~1,847번) | 낙관적 동시성 커밋 충돌 | 엔진 로그의 커밋 충돌 예외, 잡별 쓰기 파티션 겹침 | [14-4](../14-lakehouse-table-formats/2-summary.md) |
| 정리 작업 직후 일부 쿼리가 "파일 없음"으로 실패 | 고아 파일 삭제의 보존 간격이 쓰기 잡 시간보다 짧음 | 매니페스트가 가리키는 파일 vs 실제 나열 | [14-5](../14-lakehouse-table-formats/2-summary.md) |
| 로그·이벤트 저장 비용이 매달 증가, 5년 전 탈퇴 회원 로그가 남음 | 데이터 종류별 보존 기한 없음 | 기한 없는 데이터셋 수 | [12-3](../12-data-retention-and-erasure/2-summary.md) |

### 12. "이 숫자 왜 틀렸나"를 못 찾는다 · 주인이 없다

| 보이는 형태 | 원인 후보 | 확인 방법 | leaf |
|---|---|---|---|
| 경영 대시보드 매출이 재무보다 3% 낮다. 분석가가 SQL을 하나씩 열어 본다. 값 경로(`amount`)만 따라가 못 찾음 | 필터·조인 키·그룹 키 쪽 변화(11번 실험: 매출 하나에 영향을 주는 원천 컬럼 다섯) | 상류 BFS(INDIRECT 포함) + 원천 컬럼별 관측 지표를 거리 순으로 | [11-2](../11-data-lineage/2-summary.md) |
| 계보 화면에 없어진 잡이 보이고 새 잡은 없음 | 정적 선언만, 런타임 연동이 일부 도구에만 | Run 이벤트가 없는 잡·데이터셋, 연동된 잡 비율 | [11-4](../11-data-lineage/2-summary.md) |
| "이번 달 등급 강등이 왜 늘었나"에 답할 수 없음. 하루 안에 올랐다 내려간 회원은 안 보임 | 상태 스냅샷만 보냄 — 변경과 사유가 생산자 안에서 사라짐 | 이벤트에 이전 값·새 값·사유가 있나 | [06-4](../06-event-data-modeling/2-summary.md) |
| `event_time > received_at`인 "미래" 이벤트(06번 실험 5건, 최대 2시간 59분 58초 앞섬) | 클라이언트 시계를 믿음 | `event_time - received_at` 분포 | [06-3](../06-event-data-modeling/2-summary.md) |
| 데이터 품질 채널에 하루 수십 건 경고, 아무도 안 봄(10번 실험 고정 ±5% 규칙: 정상 39일 중 21일 경보) | 계절성·성장을 모르는 고정 임계 | 규칙별 경보 수·대응률 | [10-4](../10-data-quality-and-data-observability/2-summary.md) |
| 새 지표 하나에 몇 주, 소비 팀이 원천 DB를 직접 조회 | 중앙 팀 병목 | 요청 티켓 대기 시간, 원천 직접 조회 계정 | [15-1](../15-data-mesh-and-data-products/2-summary.md) |
| owner 없음·읽기 0회 테이블이 쌓임(15번 실험 카탈로그 7개 중 3개가 어느 제품의 출력도 아님) | 거버넌스(전역 규칙의 자동 집행) 없이 분산 | 카탈로그의 owner·계약 필드, 읽기 수 | [15-3](../15-data-mesh-and-data-products/2-summary.md) |
| 팀마다 다른 스케줄러·저장소·품질 도구 | 셀프서비스 플랫폼 없이 분산 | 도메인별 인프라 목록·비용 | [15-4](../15-data-mesh-and-data-products/2-summary.md) |
| 월말 정산 잡이 "테이블 없음"으로 실패하거나 이전 값으로 조용히 계산 | 은퇴한 데이터 제품을 소비자 확인 없이 삭제 | 소비자 등록·계보의 하류 | [15-5](../15-data-mesh-and-data-products/2-summary.md) |
| 볼트는 다 지었는데 대시보드가 하나도 없음, 분석가가 원천 DB를 직접 조회 | 마트 없이 모델만 도입 | 볼트 테이블 조회 수, 원천 복제본의 분석 쿼리 | [13-4](../13-data-vault/2-summary.md) |
| "고객 수"가 CRM보다 많음, 한 고객의 매출이 둘로(13번 실험 `' c001 '` 200, `'C001'` 100) | 비즈니스 키 정규화 누락 → Hub 행 둘 | 정규화한 키로 묶었을 때 2행 이상인 묶음 | [13-1](../13-data-vault/2-summary.md) |

### 13. 증상별 "하지 말 것" 한 줄

```text
  0행·초록           "잡이 성공했으니 상류 문제"로 넘기기 ─ 잡 성공 ≠ 행 수. 대조 숫자를 먼저.
  2배               DISTINCT로 맞추기 ─ grain·조인 곱은 남고 진짜 사건까지 지운다.
  적다              재실행으로 맞추기 ─ append 잡이면 이번엔 2배가 된다(08-1).
  과거가 바뀜        "이번 숫자가 맞다"로 덮기 ─ 그때의 규칙·속성으로 계산했나부터.
  대시보드마다 다름   한쪽 캐시를 지우고 새로고침 ─ 정의·시각 축·원천 중 무엇이 다른지가 먼저.
  NULL 급증          COALESCE(x, '알 수 없음')로 숨기기 ─ 상류 변경을 늦게 알게 될 뿐이다.
  WAL 디스크 풀      pg_wal 파일을 손으로 지우기 ─ DB 손상 위험. 슬롯부터(database/19 장애 2).
  삭제했는데 남음     원천 count=0으로 닫기 ─ 사본 목록 전체에서 확인 검색.
  재처리 불가        "처음부터" 재처리 성공을 완료로 보기 ─ 결과 날짜 수·건수를 v1과 대조.
```

## 쓰이는 자료구조·알고리즘

- **역색인**: 증상 → leaf 목록([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
- **집합 차·반조인(anti-join)**: 원천과 사본의 키 대조(`EXCEPT`, `NOT EXISTS`). 누락은 원천 − 사본, 잔존은 사본 − 원천이다. `EXCEPT`는 중복 행을 없애므로 같은 키가 사본에 두 번 있어도 차집합은 비어 있다. 중복은 키별 `count(*) > 1`이나 `EXCEPT ALL`로 본다([01](../01-system-of-record-and-derived-data/2-summary.md) 자료구조 절, [05](../05-change-data-capture/2-summary.md) 적용 §4, [12](../12-data-retention-and-erasure/2-summary.md)).
- **해시 집계**: 파티션별 `count(*)`·`sum()` 대조, 그룹별 `HAVING count(*) > 1` 중복 검사.
- **구간 겹침 검사**: SCD Type 2 유효 기간의 `tstzrange … && …`와 `lead()` 이웃 대조([04](../04-slowly-changing-dimensions/2-summary.md), 구간 비교 — [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md), 커리큘럼 번호 42).
- **이동 평균·EWMA**: 볼륨 기준선과 밴드([10](../10-data-quality-and-data-observability/2-summary.md)).
- **그래프 BFS**: 계보 DAG의 하류(영향 범위)·상류(원인 후보) 순회([11](../11-data-lineage/2-summary.md), [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)).
- **LSN 차이**: `pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)`는 두 WAL 위치 사이의 바이트 거리다. 슬롯이 붙든 WAL 양의 추정치로 쓴다. 실제 `pg_wal` 디렉터리 크기는 세그먼트 단위로 남고 다른 보존 사유(`wal_keep_size`·아카이브 실패 등)도 더해지므로 `pg_ls_waldir()` 합계로 따로 잰다([05](../05-change-data-capture/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 증상을 받으면 이 순서로

```text
  1. 숫자를 숫자로 받는다      "이상해요"가 아니라 "9월, 대시보드 X, 결제 DB Y" (어느 화면, 어느 기간, 어느 원천과 비교)
  2. 파티션별 대조            원천 vs 적재본의 행 수·합계를 날짜별로. 0-2절 그림으로 모양을 붙인다
  3. 언제부터                 어긋남이 시작된 파티션 ↔ 배포·스키마 변경·백필·재처리·차원 갱신 시각
  4. 어느 축에서만              총합인가, 특정 차원·특정 지표에서만인가 (2절·4절의 갈림)
  5. leaf로 가서 확인 방법 실행  표의 "확인 방법" 칸 — 원인을 확정하는 쿼리를 돌리고 나서 고친다
  6. 고친 뒤 다시 대조          처방 후 2번 대조가 0이 됐나. 같은 검사를 파이프라인에 남긴다(10번)
```

### 2. 첫 진단 세트 (PostgreSQL 17 기준 SQL 모양)

```sql
-- (1) 파티션별 행 수·합계 대조 — 대부분 증상의 출발점
SELECT coalesce(s.ds, t.ds) AS ds, s.rows AS src_rows, t.rows AS dst_rows,
       s.amt AS src_sum, t.amt AS dst_sum
FROM (SELECT event_date AS ds, count(*) AS rows, sum(amount) AS amt FROM src_orders GROUP BY 1) s
FULL JOIN (SELECT ds, count(*) AS rows, sum(amount) AS amt FROM fct_orders GROUP BY 1) t USING (ds)
WHERE s.rows IS DISTINCT FROM t.rows OR s.amt IS DISTINCT FROM t.amt
ORDER BY ds;

-- (2) 키 중복 — 2배·경계 중복
SELECT order_id, count(*) FROM fct_orders GROUP BY order_id HAVING count(*) > 1 LIMIT 20;

-- (3) 누락·잔존 — 키 차집합 (같은 DB에 사본이 있을 때)
SELECT order_id FROM src_orders EXCEPT SELECT order_id FROM fct_orders;   -- 빠진 것
SELECT order_id FROM fct_orders EXCEPT SELECT order_id FROM src_orders;   -- 남은 것(삭제 미반영 후보)

-- (4) 신선도와 NULL 비율 — 0행·NULL 급증
SELECT now() - max(event_time) AS lag FROM fct_orders;
SELECT ds, round(100.0 * count(*) FILTER (WHERE region IS NULL) / count(*), 1) AS null_pct
FROM fct_orders GROUP BY ds ORDER BY ds DESC LIMIT 14;

-- (5) 슬롯 — WAL 디스크
SELECT slot_name, active, inactive_since, wal_status,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained, safe_wal_size
FROM pg_replication_slots;
```

- (1)의 `FULL JOIN`은 한쪽에만 있는 파티션(적재본에 날짜가 통째로 없음 = 0행)도 잡는다. `IS DISTINCT FROM`은 NULL과 숫자를 "다름"으로 본다.
- (3)은 원천과 사본이 다른 저장소면 쓸 수 없다. 그때는 양쪽에서 키를 내보내 비교하거나, 키 해시의 파티션별 합으로 범위를 좁힌다(해석).
- 각 쿼리의 테이블·컬럼 이름은 예시다. 실제 진단 쿼리와 출력 읽는 법은 각 leaf의 적용 절에 있다(05 §2, 04 §4, 08 §4, 10 §2).

### 3. 대조를 파이프라인에 남긴다 — 고친 뒤에도

- 2절 (1)을 적재 직후 단계로 두고, 어긋나면 하류 게시를 막는다(차단). 거부 행·`-1` 행·복호 실패 수처럼 "버린 것의 수"를 지표로 낸다.
- 위 `Reconcile.java`의 모양 분류는 경보 문구를 고르는 데 쓴다. "MULTIPLE x2"는 재시도 기록을, "PLATEAU"는 파일 크기·행 한도를 먼저 보라는 뜻이다(후보이지 확정이 아니다).
- 대조 잡이 원천 DB를 직접 대량으로 읽으면 그 자체가 [02-1](../02-oltp-olap-and-warehouse/2-summary.md)이 된다. 복제본·적재 영역에서 읽는다.

### 4. leaf로 간다

- 숫자가 2배·적다·0: [03](../03-dimensional-modeling/2-summary.md) · [08](../08-idempotent-pipelines-and-backfill/2-summary.md) · [10](../10-data-quality-and-data-observability/2-summary.md) · [02](../02-oltp-olap-and-warehouse/2-summary.md)
- 과거가 바뀐다·시각: [04](../04-slowly-changing-dimensions/2-summary.md) · [06](../06-event-data-modeling/2-summary.md) · [08](../08-idempotent-pipelines-and-backfill/2-summary.md) · [14](../14-lakehouse-table-formats/2-summary.md)
- 경로·정의: [07](../07-batch-stream-architectures/2-summary.md) · [15](../15-data-mesh-and-data-products/2-summary.md) · [01](../01-system-of-record-and-derived-data/2-summary.md)
- 스키마·NULL: [09](../09-data-contracts-and-schema-registry/2-summary.md) · [10](../10-data-quality-and-data-observability/2-summary.md) · [11](../11-data-lineage/2-summary.md)
- CDC·WAL: [05](../05-change-data-capture/2-summary.md)
- 삭제: [12](../12-data-retention-and-erasure/2-summary.md) · [11](../11-data-lineage/2-summary.md) · [05](../05-change-data-capture/2-summary.md)
- 실제 사고로 이어진 모양: [17](../17-de-incidents/2-summary.md)

## 장애 시나리오와 대처

증상 색인을 **잘못 읽어** 생기는 장애다.

### 1. "잡이 초록이니 데이터는 맞다"로 조사를 닫는다 ⚠

- **현상**: 대시보드에 어제가 비었다는 문의에 "파이프라인 정상"으로 답한다. 이틀 뒤 재무 마감에서 차이가 드러난다.
- **보이는 형태**: 오케스트레이터 전부 성공. 적재 로그 `INSERT 0 0`. 감사 테이블 행 수 0.
- **원인**: 잡 상태를 데이터 상태로 읽었다. SQL은 0행을 오류로 보지 않는다([10-1](../10-data-quality-and-data-observability/2-summary.md)).
- **대처**: 첫 확인을 "파티션별 대조"로 바꾼다(적용 §2 (1)). 0행·볼륨 급감은 차단 검사로 둔다. 신선도는 `max(event_time)`으로 표시한다.

### 2. 합계 2배를 `DISTINCT`로 맞춘다

- **현상**: 매출이 2배라는 보고에 리포트 SQL에 `DISTINCT`를 붙였다. 숫자는 맞아 보인다. 한 달 뒤 주문 수가 실제보다 적다는 보고가 온다.
- **보이는 형태**: `DISTINCT` 뒤 행 수가 원천보다 적다. 같은 금액·같은 시각의 서로 다른 주문이 하나로 합쳐졌다.
- **원인**: 2배의 원인(append 재실행·grain 혼합·조인 곱)을 찾지 않고 결과를 덮었다. 내용 기반 중복 제거는 진짜로 같은 내용의 다른 사건까지 지운다([06-2](../06-event-data-modeling/2-summary.md)).
- **대처**: 2절 표로 원인을 확정한다. 재실행이면 파티션 덮어쓰기([08-1](../08-idempotent-pipelines-and-backfill/2-summary.md)), grain이면 팩트 분리([03-1](../03-dimensional-modeling/2-summary.md)), 조인 곱이면 drill-across·PIT([03-2](../03-dimensional-modeling/2-summary.md) · [13-3](../13-data-vault/2-summary.md)). 중복 제거는 이벤트 ID 같은 식별자로만 한다.

### 3. "숫자가 적다"에 잡을 다시 돌린다 ⚠

- **현상**: 어제 매출이 원천보다 적어 잡을 수동 재실행했다. 이번엔 원천보다 많다.
- **보이는 형태**: 재실행 뒤 같은 파티션의 행 수가 원래 적재분 + 새 적재분. 차이가 "적다"에서 "거의 2배"로 바뀌었다.
- **원인**: 적은 이유(늦은 데이터·필터)를 확인하지 않았고, 잡이 append였다([08-1](../08-idempotent-pipelines-and-backfill/2-summary.md) · [08-4](../08-idempotent-pipelines-and-backfill/2-summary.md)).
- **대처**: 재실행 전에 잡이 덮어쓰기(멱등)인지 확인한다. 적은 이유가 늦은 데이터면 그 이벤트 날짜 파티션을 덮어쓰기로 다시 계산한다.

### 4. WAL 디스크 풀에 `pg_wal` 파일을 지우거나, 상한만 걸고 끝낸다 ⚠

- **현상**: 운영 DB 디스크 경보에 운영자가 오래된 WAL 파일을 손으로 지우려 한다. 또는 `max_slot_wal_keep_size`만 걸고 닫는다. 며칠 뒤 하류 데이터가 멈춘 것을 안다.
- **보이는 형태**: 앞의 경우 DB 손상 위험(database/19 장애 2). 뒤의 경우 `wal_status=lost`, 하류 마지막 반영 시각이 며칠 전([05-5](../05-change-data-capture/2-summary.md)).
- **원인**: WAL을 붙든 주체(비활성 슬롯)를 보지 않았다. 상한은 슬롯의 무한 보존을 막는 대신, 멈춘 소비자의 슬롯을 무효화할 수 있게 할 뿐이다.
- **대처**: `pg_replication_slots`로 비활성 슬롯을 찾는다. 커넥터를 살리거나, 쓰지 않는 슬롯이면 `pg_drop_replication_slot()`. 상한을 건다면 `safe_wal_size` 경보와 재스냅샷 절차를 함께 둔다([05-1](../05-change-data-capture/2-summary.md)).

### 5. 삭제 확인을 원천 `count(*) = 0`으로 닫는다 ⚠

- **현상**: 삭제 요청 처리 후 원천 조회 0행을 근거로 "완료"를 회신했다. 한 달 뒤 그 사람이 마케팅 메일을 받았다고 항의한다.
- **보이는 형태**: 원천 0행, 웨어하우스·검색 인덱스·내보내기 테이블에 잔존([12-1](../12-data-retention-and-erasure/2-summary.md) · [11-3](../11-data-lineage/2-summary.md)).
- **원인**: 사본 목록(계보)이 없었다. CDC 소비자가 삭제 이벤트를 놓쳤을 수도 있다([05-4](../05-change-data-capture/2-summary.md)).
- **대처**: 계보로 사본 목록을 만들고 사본별 삭제 ack를 받는다. 마지막 단계로 사본 전체에서 확인 검색을 돌린다. "미상" 계보 노드는 삭제 대상에 보수적으로 넣는다.

## 핵심 문장

- 데이터 파이프라인의 장애는 크래시가 아니라 **초록인데 틀린 숫자**로 보인다. 첫 단서는 에러 메시지가 아니라 원천 대조의 어긋남 모양이다.
- 0은 빈 입력, 정수배는 중복 적재·조인 곱, 약간 적음은 필터·조인 누락·늦은 데이터, 같은 값에서 평평함은 고정 한도의 후보다. 모양은 후보를 고를 뿐이고, 확정은 leaf의 확인 쿼리로 한다.
- 과거 숫자가 바뀌면 총합이 같은지부터 본다. 분포만 바뀌면 차원 덮어쓰기, 총합이 바뀌면 규칙·시각 축이 후보다.
- 대시보드마다 숫자가 다르면 정의·시각 축·원천 중 무엇이 다른지를 먼저 찾는다. 원천이 둘이면 어느 쪽이 맞는지 판정할 규칙이 없다.
- 멈춘 CDC 소비자의 슬롯은 상한이 없으면 WAL을 쌓아 디스크를 채울 수 있고, 상한이 있으면 슬롯 무효화(CDC 끊김)로 갈 수 있다. 삭제는 원천이 아니라 사본 목록 전체에서 확인해야 끝난다.
- 재처리는 원본이 남아 있는 기간까지만 가능하다. 보존 기간·raw 층·스냅샷 태그를 재처리 요구 기간에 맞춘다.

## 관련 주제·근거

- 이 영역 leaf: [01](../01-system-of-record-and-derived-data/2-summary.md) · [02](../02-oltp-olap-and-warehouse/2-summary.md) · [03](../03-dimensional-modeling/2-summary.md) · [04](../04-slowly-changing-dimensions/2-summary.md) · [05](../05-change-data-capture/2-summary.md) · [06](../06-event-data-modeling/2-summary.md) · [07](../07-batch-stream-architectures/2-summary.md) · [08](../08-idempotent-pipelines-and-backfill/2-summary.md) · [09](../09-data-contracts-and-schema-registry/2-summary.md) · [10](../10-data-quality-and-data-observability/2-summary.md) · [11](../11-data-lineage/2-summary.md) · [12](../12-data-retention-and-erasure/2-summary.md) · [13](../13-data-vault/2-summary.md) · [14](../14-lakehouse-table-formats/2-summary.md) · [15](../15-data-mesh-and-data-products/2-summary.md)
- 후속: [17](../17-de-incidents/2-summary.md)(이 증상들이 실제 사고가 된 모습)
- 다른 영역 색인: [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md)(SQLSTATE·`pg_wal` 증가의 엔진 쪽) · [distributed/35-distributed-symptom-index](../../distributed/35-distributed-symptom-index/2-summary.md)(중복·유실·순서) · [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md)(지연·에러·연쇄 장애) · [architecture/22-arch-symptom-index](../../architecture/22-arch-symptom-index/2-summary.md)(합계 불일치의 표현·하드웨어 쪽)
- 겹치는 노트: [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md)(장애 2 WAL 디스크 풀) · [database/34-large-backfill-and-batch-dml](../../database/34-large-backfill-and-batch-dml/2-summary.md) · [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) · [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) · [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md) · [security/27-pii-classification-masking-retention](../../security/27-pii-classification-masking-retention/2-summary.md)
- 데이터 분석 쪽(품질 검사·표본): [data-analysis/18-data-cleaning-and-quality](../../data-analysis/18-data-cleaning-and-quality/2-summary.md) · [data-analysis/02-sampling-and-bias](../../data-analysis/02-sampling-and-bias/2-summary.md)
- 근거: 각 표의 수치는 해당 leaf의 실험·장애 시나리오에서 옮겼다(leaf 표기 `NN-k`). 도구 동작(PostgreSQL 17 슬롯 뷰, Kafka 보존, Confluent 호환성 모드, Iceberg 유지보수)의 1차 출처는 각 leaf의 「관련 주제·근거」에 있다.
- 실험 목록
  - `Reconcile.java` — eclipse-temurin:21-jdk(OpenJDK 21.0.12), docker `--rm --pull never --network none --cpus=2 -u`, 합성 파티션 8개: 행 수·합계 두 숫자로 어긋남 모양(OK·MULTIPLE·ZERO·MISSING·PLATEAU·EXTRA·VALUE) 분류
