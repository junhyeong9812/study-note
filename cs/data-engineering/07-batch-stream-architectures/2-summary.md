# data-engineering/07-batch-stream-architectures — 배치·스트림 아키텍처: Lambda vs Kappa, 재처리 전략 — 정리 (힌트)

## 해결하는 문제

파생 데이터(대시보드 숫자·추천·검색 인덱스)에는 요구가 둘 있다.

```text
  요구 1  빨라야 한다        "방금 들어온 주문이 몇 초 안에 매출 그래프에 보여야 한다"
  요구 2  다시 계산할 수 있어야 한다  "버그를 고쳤다 → 지난 30일 숫자를 고친 코드로 다시 만들어야 한다"

  스트림 처리만 있고 원본 로그를 버린다  → 요구 1 O, 요구 2 X (과거를 다시 돌릴 입력이 없다)
  배치 처리만 있다                      → 요구 2 O, 요구 1 X (몇 시간 늦다)
```

- *재처리(reprocessing)*: 입력 데이터를 다시 처리해 출력을 다시 만드는 일. Kreps 2014: "Code will always change." 새 필드가 필요하거나 버그를 고치면 출력을 다시 만들어야 한다.
- *배치 처리*: 정해진 크기의 입력을 한꺼번에 읽어 결과를 만든다. *스트림 처리*: 끝이 없는 입력을 도착하는 대로 처리한다. 둘의 실행 모델은 [distributed/30](../../distributed/30-batch-and-stream-processing/2-summary.md)에서 다뤘다. 이 노트는 둘을 **어떻게 엮어** 위 두 요구를 맞추나를 다룬다.

쉬운 예: 가게의 매출 장부다.
- 낮에는 계산대 화면에 실시간 합계가 뜬다(빠르지만 반품·취소 반영이 엉성하다).
- 밤에 영수증 묶음(원본)을 다시 세서 장부를 확정한다.
- 계산 규칙이 바뀌면 보관해 둔 영수증으로 지난달 장부를 다시 쓴다. 영수증을 버렸다면 다시 쓸 수 없다.

똑같은 구조다.\
"영수증 보관 + 밤 재계산 + 낮 실시간 화면"을 두 시스템으로 나눈 것이 Lambda, "영수증 묶음 하나를 실시간으로도 읽고 다시 읽기도 하는" 것이 Kappa다.

실무 예:
- 광고 클릭 집계: 실시간 대시보드와 일별 정산 숫자가 다르다는 문의가 매일 온다.
- 집계 버그 수정 후 지난 한 달 재처리를 하려는데 Kafka 보존이 7일이다.

## 동작·원리

### 1. Lambda — 같은 로직을 두 경로에

```text
                      ┌──────── 배치 계층 ───────────────────────────┐
  불변 원본 로그 ──┬──> │ 전체 데이터로 몇 시간마다 다시 계산 → 배치 뷰      │──┐
  (master dataset)  │   └─────────────────────────────────────────────┘  │  질의 시점에
                    │   ┌──────── 실시간 계층 ──────────────────────────┐  ├─> 합친다
                    └─> │ 최근 몇 시간만 증분 계산 → 실시간 뷰             │──┘
                        └─────────────────────────────────────────────┘
  배치 뷰가 따라잡으면 그 구간의 실시간 결과는 버린다(배치가 덮어쓴다)
```

- Marz 2011 "How to beat the CAP theorem"(2011-10-13 게시)
  - "Query = Function(All Data)": 질의는 전체 데이터에 대한 함수다. 데이터는 불변이고 추가만 한다(CRUD → CR).
  - 배치 시스템이 질의를 미리 계산(precompute)하고, 몇 시간 늦는 구간은 실시간 계층(realtime layer)이 보완한다. 질의할 때 두 뷰를 합친다.
  - 실시간 계층이 틀려도 배치 계층이 결국 덮어쓴다. 원본이 불변이라 버그 있는 코드·잘못된 데이터에서 복구할 길이 남는다("human fault-tolerance").
  - 이 글은 "realtime layer"라는 이름을 쓴다("speed layer"는 글에 없다). "speed layer"는 Marz·Warren의 책 『Big Data』(Manning, 2015-04)의 3부 제목 "Speed layer"에 나온다(O'Reilly 목차, Internet Archive 2025 사본). 이 이름이 처음 쓰인 곳인지는 확인하지 않았다.
- Kreps 2014 "Questioning the Lambda Architecture"(O'Reilly Radar, 2014-07-02)
  - 좋은 점: 입력을 바꾸지 않고 보존하는 것, 재처리 문제를 드러낸 것.
  - 문제: "maintaining code that needs to produce the same result in two complex distributed systems is exactly as painful as it seems like it would be." 둘을 감싸는 추상화 프레임워크도 두 시스템의 공통 기능만 쓸 수 있고, 운영·디버깅 부담은 그대로라고 본다.

### 2. Kappa — 재생 가능한 로그 하나

```text
  Kafka 토픽(보존 = 재처리하고 싶은 기간)
  offset: 0 ─────────────────────────────────────────────> 끝
           │                                            ▲
           │   잡 v1 (그룹 v1) ──────────────────────────┘──> 출력 테이블 out_v1   ← 앱이 읽는 중
           └─> 잡 v2 (그룹 v2, 처음부터, 병렬도↑) ────────────> 출력 테이블 out_v2
  v2가 끝까지 따라잡으면: 앱이 out_v2를 읽게 전환 → v1 잡 중지 → out_v1 삭제
```

- Kreps가 제안한 순서(원문 1~4)
  1. 재처리하고 싶은 기간만큼 로그를 보존한다. "if you want to reprocess up to 30 days of data, set your retention in Kafka to 30 days."
  2. 재처리할 때 같은 잡의 두 번째 인스턴스를 로그 처음부터 시작하고, 출력을 **새 출력 테이블**로 보낸다.
  3. 두 번째 잡이 따라잡으면 앱을 새 테이블로 전환한다.
  4. 옛 잡을 멈추고 옛 출력 테이블을 지운다.
- 대가와 이점(같은 글)
  - 재처리 동안 출력 저장소가 **2배** 필요하고, 대량 쓰기를 견뎌야 한다.
  - 옛 테이블을 잠시 남기면 버튼 하나로 옛 로직으로 되돌릴 수 있다.
  - Kreps는 이를 "Kappa Architecture라 불러도 될지 모르겠다"며 이름을 붙였다. 핵심 이점은 효율이 아니라 **한 처리 프레임워크**로 개발·테스트·운영한다는 것이라고 정리한다.
- DDIA 1판 12장 "The Future of Data Systems"의 절 "Batch and Stream Processing"이 두 방식의 통합을 다룬다(절 제목은 O'Reilly 목차로 확인, 본문은 열지 못함).

#### 실험 A: 두 경로가 같은 날을 다르게 센다 (Java 모형)

- 모형 설정: 10-01(KST) 주문 1,000건 × 100원. 마지막 30건은 오프라인으로 3시간 늦게 도착(자정 넘김). 2%는 재시도로 두 번 전달. 4%는 나중에 취소됨.
  - 실시간 계층: 도착할 때마다 처리 시각의 날짜에 더한다(중복 제거 없음).
  - 배치 계층: 다음 날 원본 로그 전체로 이벤트 시각 날짜·`id` 중복 제거로 다시 계산.
  - Kappa: v1 코드는 취소를 빼지 않았다. v2로 고쳐 처음부터 다시 읽는다.

(실험, `eclipse-temurin:21-jdk` = OpenJDK 21.0.12, `Lambda07.java`, 외부 라이브러리 없음, 2026-10-07)

```text
[Lambda] 10-01 매출: 23:59 대시보드(속도 계층) = 99000, 다음 날 아침(배치 계층) = 100000, 속도 계층이 10-02에 넣은 10-01 주문 = 3000
[Kappa] 10-01 매출: v1(버그) = 100000, v2를 새 테이블에 = 96000, v2를 운영 테이블에 더함 = 196000
```

- Lambda: 같은 날의 숫자가 밤사이 99,000 → 100,000으로 바뀌었다. 실시간 경로는 늦은 30건(3,000)을 빼먹고 다음 날에 넣었고, 중복 20건(2,000)을 더했다. 두 오차가 일부 상쇄돼 차이가 작아 보인다.
- 해석: 두 경로가 **같은 로직**(이벤트 시각·중복 제거)이었다면 규칙 차이(중복 2,000원, 10-02로 잘못 넘긴 3,000원)는 사라졌을 것이다. 그래도 23:59에는 늦은 30건이 아직 도착하지 않았으니 그 시각의 값은 97,000원이고, 다음 날 100,000원과 잠시 다르다. 같은 로직은 규칙 차이를 없앨 뿐 도착 시점 차이는 없애지 못한다. 다른 시각 기준·다른 중복 처리를 쓴 두 코드베이스가 같은 지표를 내면 이런 차이가 매일 생긴다. 이 수치는 모형의 설정(늦음 3%, 중복 2%)이 만든 것이다.
- Kappa: 고친 v2를 **새 테이블**에 쓰면 96,000(정답). 운영 테이블에 더하면(증분 upsert를 그대로 재사용) 196,000이 됐다. 재처리 출력 위치를 잘못 고르면 숫자가 두 배 가까이 된다.

### 3. 보존 기간 = 재처리할 수 있는 과거의 한계

- Kafka는 소비자의 진행과 무관하게 보존 기간이 지난 세그먼트를 지운다. 판정은 세그먼트 단위이고, 세그먼트 안 **가장 큰 타임스탬프**로 정한다([distributed/21 §5](../../distributed/21-kafka-internals/2-summary.md)에서 멈춘 그룹의 미처리분이 사라지는 것을 보였다).
- Kafka 4.1 토픽 설정 `retention.ms` 기본 604800000(7일), `retention.bytes` 기본 -1(크기 제한 없음). 문서 표현으로 보존은 "an SLA on how soon consumers must read their data"다(Topic Configs).

#### 실험 B: 30일치 로그를 7일 보존으로 바꾼 뒤 "처음부터" 재처리

- 토픽 `w05-orders`(파티션 1개)를 `retention.ms=-1`(무제한), `segment.ms=86400000`(1일)으로 만들고, 레코드 타임스탬프(`CreateTime`)를 29일 전 ~ 오늘로 둔 주문 3,000건(하루 100건)을 발행했다. v1 그룹이 처음 계산했다. 그 뒤 보존을 7일로 바꾸고, 새 그룹 v2로 처음부터 다시 읽었다.

(실험, `apache/kafka:4.1.0` 단일 노드 KRaft 전용 컨테이너 `--network none`, 브로커 `log.retention.check.interval.ms=5000`, 클라이언트 kafka-clients 4.1.0으로 만든 `Exp07.java`, 2026-10-07)

```text
## 2) 30일치 3000건 발행
produced 3000 records, first day 2026-09-08T00:00:00Z
## 3) v1 잡(처음 계산)
v1: beginningOffset=0 endOffset=3000
v1: records=3000 revenue=300000 days=30 first=2026-09-08 last=2026-10-07
## 세그먼트 파일 수: 6
## 4) 보존 7일로 변경
## 세그먼트 파일 수: 3
w05-orders:0:2120                       ← kafka-get-offsets --time earliest
## 5) 버그 수정 뒤 Kappa 재처리: 새 그룹 v2가 처음부터
v2: beginningOffset=2120 endOffset=3000
v2: records=880 revenue=88000 days=9 first=2026-09-29 last=2026-10-07
-- 브로커 로그(줄임)
Deleting segment LogSegment(baseOffset=0, ..., largestRecordTimestamp=…) due to log retention time 604800000ms breach based on the largest record timestamp in the segment
Incremented log start offset to 2120 due to segment deletion
-- 지워진 세그먼트(base offset → 가장 큰 타임스탬프 날짜, UTC): 0 → 09-15, 723 → 09-22, 1427 → 09-29
```

- 관찰
  - v1이 계산한 30일 중, 재처리 v2는 9일치 880건만 읽을 수 있었다. 09-08~09-28 21일치는 더 이상 로그에 없다. **에러는 없었다.** 소비자는 로그 시작(2120)부터 정상적으로 읽고 끝났다.
  - 보존이 7일인데 9일치가 남았다. 남은 첫 세그먼트(2120~)의 가장 큰 타임스탬프가 7일 안이라 통째로 남았기 때문이다(세그먼트 단위 삭제).
  - 세그먼트가 30개(하루 1개)가 아니라 6개였다. Kafka 4.1.0 소스 `LogSegment.shouldRoll`·`timeWaitedForRoll`은 roll 여부를 **배치를 붙일 때** "들어오는 배치의 최대 타임스탬프 − 세그먼트 첫 배치의 최대 타임스탬프 > `segment.ms`"로 판정한다. 그래서 며칠치가 든 생산자 배치 하나는 한 세그먼트에 통째로 들어간다(지워진 세그먼트 크기 5~16 KB, 생산자 기본 `batch.size` 16 KB 안팎).
  - 같은 절차를 다시 두 번 돌리자(점검 재실행) 세그먼트 7·8개, 로그 시작 2005·2094, v2 995·906건·10일(09-28~10-07)이었다. 배치 경계가 실행마다 달라 **남는 날 수·건수는 실행마다 다르다**(이 설정에서 9~10일, 880~995건). 경향(앞부분이 에러 없이 사라짐, 7일보다 조금 더 남음)은 같았다.
- 해석: 재처리 잡이 "완료"라고 끝나도, 그 결과는 남은 구간만의 결과다. v2 출력으로 전환하면 9월 초 숫자가 **사라진다**. 전환 전에 v1·v2를 날짜별로 대조해야 하는 이유다.

### 4. 보존이 짧을 때의 선택지

| 방법 | 무엇을 다시 읽나 | 비용·주의 |
|---|---|---|
| 보존을 늘린다 | Kafka 로그 그대로 | 브로커 디스크. 오래된 세그먼트는 재처리 때만 읽혀 페이지 캐시를 흔든다([distributed/21 장애 5](../../distributed/21-kafka-internals/2-summary.md)) |
| 계층형 저장(tiered storage) | 오래된 세그먼트를 원격 저장소에 두고 같은 토픽 API로 | Kafka 4.1 토픽 설정 `remote.storage.enable`, `local.retention.ms`·`local.retention.bytes`(기본 -2 = `retention.*` 값을 따름). 원격 저장 플러그인이 필요하다 |
| 로그를 객체 저장소에 아카이브하고 배치로 재처리 | 아카이브 파일(날짜 파티션) | 실시간 잡과 배치 재처리 코드가 둘이 된다(Lambda의 문제가 일부 돌아온다). 배치 쪽은 파티션 덮어쓰기로 멱등하게([08번](../08-idempotent-pipelines-and-backfill/2-summary.md)) |
| compaction 토픽 | 키별로 최소한 최신 값(아직 정리 안 된 구간엔 옛 값도 남을 수 있다) | 이력 보존은 보장되지 않는다. 전체 이력이 아니라 "현재 상태"만 다시 만들 수 있다. 과거 날짜별 집계는 다시 못 만든다 |

- Kreps는 같은 글에서 로그 저장소를 "Kafka or some other system that will let you retain the full log … and that allows for multiple subscribers"라고 적었다. 토픽을 HDFS로 미러링하는 것은 괜찮지만 "you don't run your reprocessing there"라고 했다. 즉 셋째 줄(아카이브 + 배치 재처리)은 Kreps의 제안이 아니라 Lambda 쪽으로 한 걸음 돌아가는 선택이다(해석).

## 쓰이는 자료구조·알고리즘

- **세그먼트 로그 재생** — 토픽 파티션은 세그먼트 파일의 연속이고, 소비자는 오프셋만 바꿔 과거를 다시 읽는다. 두 번째 소비자는 "다른 위치를 가리키는 또 하나의 독자"일 뿐이다(Kreps 2014). [distributed/21](../../distributed/21-kafka-internals/2-summary.md)
- **오프셋 ↔ 타임스탬프 찾기** — "10월 1일부터 재처리"는 시각으로 시작 오프셋을 찾는 일이다. `kafka-get-offsets.sh --time`(실험 B는 `earliest`)·소비자 그룹 오프셋 재설정이 이것을 한다. 세그먼트·희소 인덱스 탐색은 distributed/21 §2.
- **윈도** — 이벤트 시간 텀블링·호핑·세션 윈도와 늦은 이벤트 처리. 재처리 결과가 처음과 같으려면 윈도가 이벤트 시간 기준이어야 한다. [distributed/30 §2](../../distributed/30-batch-and-stream-processing/2-summary.md)
- **해시 집합 중복 제거** — 실시간 경로의 at-least-once 중복(실험 A의 20건)을 이벤트 `id`로 거른다. [06번](../06-event-data-modeling/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 고르는 순서

1. 지연 요구가 몇 시간이어도 되나? → 배치 하나로 충분하다. Kreps도 지연에 민감하지 않으면 배치, 민감하면 스트림을 쓰고 "꼭 필요한 게 아니면 둘을 동시에 하지 말라"고 권한다.
2. 몇 초가 필요하고 재처리 기간을 로그 보존으로 감당할 수 있나? → Kappa. 보존 ≥ 최대 재처리 기간 + 여유.
3. 몇 초가 필요하고 재처리 기간이 길다(몇 년) → 스트림 + 아카이브 배치 재처리. 이때는 **같은 로직**을 쓰도록 강제한다(공유 라이브러리, 같은 SQL, 결과 대조 검사).

### 2. Kappa 재처리 실행 절차

```bash
# (1) 재처리 구간이 로그에 남아 있나: 보존 설정과 가장 오래된 오프셋·그 시각
kafka-configs.sh --bootstrap-server $B --describe --entity-type topics --entity-name orders
kafka-get-offsets.sh --bootstrap-server $B --topic orders --time earliest
kafka-console-consumer.sh --bootstrap-server $B --topic orders --partition 0 --offset <earliest> \
  --max-messages 1 --property print.timestamp=true
# (2) 새 그룹 이름 + 새 출력으로 v2를 처음부터 (운영 그룹·운영 출력을 재사용하지 않는다)
# (3) 따라잡는 정도: 그룹 lag
kafka-consumer-groups.sh --bootstrap-server $B --describe --group orders-agg-v2
```

```sql
-- (4) 전환 전 대조: 날짜별로 v1과 v2가 어디서 다른가
SELECT coalesce(a.day, b.day) AS day, a.revenue AS v1, b.revenue AS v2, b.revenue - a.revenue AS diff
FROM out_v1 a FULL JOIN out_v2 b ON a.day = b.day
WHERE a.revenue IS DISTINCT FROM b.revenue ORDER BY 1;
-- v2에 없는 날(실험 B의 09-08~09-28)이 보이면 보존 부족 → 전환하지 않는다

-- (5) 앱은 뷰를 읽는다. 전환 = 뷰 정의 교체 (옛 테이블은 되돌리기용으로 잠시 남긴다)
CREATE OR REPLACE VIEW daily_revenue AS SELECT day, revenue FROM out_v2;
```

- 재처리 잡의 병렬도는 파티션 수에 묶인다. 한 소비자 그룹 안에서 파티션 하나는 소비자 하나에만 배정된다([distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)). Kreps가 말한 "병렬도를 올려 빨리 끝내기"의 상한이다.
- 재처리 잡은 메일 발송·결제 호출 같은 부작용을 끈 설정으로 돈다. 프로젝션 재구축이 메일을 다시 보낸 사례 유형은 [distributed/22 장애 4](../../distributed/22-event-sourcing/2-summary.md)에 있다.

### 3. Lambda를 이미 운영 중이라면

- 두 경로의 결과를 날짜별로 대조하는 검사를 붙이고, 차이가 임계값을 넘으면 경고한다([10번](../10-data-quality-and-data-observability/2-summary.md) 품질 검사).
- 차이의 흔한 원천을 맞춘다: 시각 기준(이벤트 vs 처리), 시간대, 중복 제거, 늦은 이벤트 정책, 취소·환불 반영 시점.
- 질의 시점 병합 규칙("어제까지는 배치, 오늘은 실시간")의 경계 시각을 한 곳에 둔다.

## 장애 시나리오와 대처

### 1. 배치 경로와 스트림 경로의 결과가 다르다 → 같은 지표가 대시보드마다 다르다 (⚠)

- **현상**: 실시간 대시보드의 어제 매출과 아침 정산 리포트의 어제 매출이 다르다. 오늘 오후에 본 "오늘 매출"이 내일 아침에 바뀐다.
- **보이는 형태**: 날짜별 차이가 매일 1~3%쯤 난다(규모는 데이터마다 다르다). 실험 A: 23:59 99,000 → 다음 날 100,000.
- **원인**: 같은 지표를 두 코드베이스가 다른 규칙으로 계산한다. 실험 A에서는 실시간 경로가 처리 시각·중복 미제거를, 배치가 이벤트 시각·중복 제거를 썼다. Kreps가 지적한 "두 시스템에서 같은 결과를 내는 코드 유지"의 실패다.
- **대처**: 규칙을 한 곳으로 모은다(공유 라이브러리·같은 SQL). 가능하면 한 경로(Kappa 또는 배치 단일)로 줄인다. 두 경로를 유지하면 날짜별 대조 검사를 둔다.

### 2. 로그 보존 기간이 재처리 구간보다 짧다 → 과거를 다시 돌릴 수 없다 (⚠)

- **현상**: 집계 버그를 고치고 지난 30일을 재처리했는데, 재처리 잡은 "성공"했고 결과에는 최근 9~10일만 있다.
- **보이는 형태**: 재처리 출력의 날짜 수가 기대보다 적다. `kafka-get-offsets --time earliest`가 0이 아니다. 실험 B: v1 30일·3,000건 → v2 9일·880건(재실행 10일·906~995건), 에러 없음.
- **원인**: 보존(`retention.ms`)이 재처리하려는 기간보다 짧아 앞 세그먼트가 지워졌다. `auto.offset.reset=earliest`인 소비자는 남은 로그 시작부터 정상적으로 읽는다(기본값 `latest`면 끝부터 읽어 거의 아무것도 처리하지 않고, `none`이면 예외가 난다. Kafka 4.1 Consumer Configs).
- **대처**
  - 전환 전에 v1·v2 날짜별 대조로 빠진 구간을 찾고, 전환하지 않는다.
  - 빠진 구간은 아카이브(객체 저장소·웨어하우스 원본 적재 영역)에서 배치로 재계산한다.
  - 예방: 보존 ≥ 최대 재처리 기간 + 여유, 또는 계층형 저장·아카이브.

### 3. 재처리 잡이 운영 출력에 쓴다 → 하류에 이중으로 반영된다 (⚠)

- **현상**: 재처리를 돌린 직후 대시보드 매출이 거의 두 배가 됐다.
- **보이는 형태**: 재처리 구간의 값만 비정상적으로 크다. 실험 A: 정답 96,000 → 운영 테이블에 더해 196,000. 출력이 토픽이면 하류 소비자가 같은 이벤트를 두 번 받는다.
- **원인**: v2 잡이 운영 잡과 같은 출력(테이블·토픽)을 쓰도록 배포됐다. 출력 반영이 "더하기(증분)"였다면 값이 겹쳐 쌓인다.
- **대처**
  - 재처리 출력은 새 테이블·새 토픽으로 보내고, 따라잡은 뒤 읽기를 전환한다(Kreps 2단계).
  - 이미 섞였으면 운영 출력을 원본에서 다시 만든다. 출력 반영을 키·파티션 단위 덮어쓰기로 바꾸면 같은 사고에도 값이 겹치지 않는다(08번).

### 4. 재처리가 따라잡지 못한다

- **현상**: v2 재처리를 시작한 지 며칠이 지나도 lag가 줄지 않는다. 그동안 버그 있는 v1 결과가 계속 서비스된다.
- **보이는 형태**: `kafka-consumer-groups --describe`의 LAG가 일정하거나 는다. 출력 DB 쓰기 지연 상승.
- **원인 후보**: 파티션 수가 병렬도의 상한이다. 출력 DB가 대량 쓰기를 못 받는다(Kreps가 짚은 "high-volume writes" 요구).
- **대처**: 출력에 대량 적재 경로(배치 쓰기·인덱스 지연 생성)를 쓴다. 재처리 구간을 나눠 여러 잡으로 돌린다. 파티션 수는 토픽 설계 단계에서 재처리 병렬도까지 고려한다.

## 핵심 문장

- 파생 데이터는 빨라야 하고 다시 계산할 수 있어야 한다. 다시 계산하려면 입력 원본을 보존해야 한다.
- Lambda는 배치 계층과 실시간 계층에 같은 로직을 두 번 구현한다. 두 결과가 어긋나면 같은 지표가 화면마다 다르다.
- Kappa는 재생 가능한 로그 하나를 두고, 고친 잡을 처음부터 다시 돌려 새 출력에 쓴 뒤 읽기를 전환한다.
- 로그 보존 기간이 곧 재처리할 수 있는 과거의 한계다. 보존보다 긴 재처리는, 새 그룹이 `auto.offset.reset=earliest`로 시작하면(실험 B) 에러 없이 앞부분만 빠진 결과를 낸다. Kafka 4.1 기본값 `latest`면 로그 끝부터 읽고, `none`이면 예외가 난다.
- 재처리 출력은 운영 출력과 분리하고, 전환 전에 날짜별로 대조한다.

## 관련 주제·근거

- 선행
  - [05-change-data-capture](../05-change-data-capture/2-summary.md) — DB 변경을 재생 가능한 로그로
  - [distributed/30-batch-and-stream-processing](../../distributed/30-batch-and-stream-processing/2-summary.md) — 배치·스트림 실행 모델, 이벤트 시간, 워터마크
  - [distributed/21-kafka-internals](../../distributed/21-kafka-internals/2-summary.md) — 세그먼트, 보존, 멈춘 그룹의 데이터 소실
- 후속·연결
  - [06-event-data-modeling](../06-event-data-modeling/2-summary.md) — 이벤트 시각과 중복 제거
  - [08-idempotent-pipelines-and-backfill](../08-idempotent-pipelines-and-backfill/2-summary.md) — 배치 쪽 재계산을 멱등하게
  - [01-system-of-record-and-derived-data](../01-system-of-record-and-derived-data/2-summary.md) — 파생 = 원천 로그의 폴드
  - [distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)(소비자 그룹·전달 보장), [distributed/22](../../distributed/22-event-sourcing/2-summary.md)(재생과 부작용)
- 글·문서
  - Kreps, "Questioning the Lambda Architecture", O'Reilly Radar, 2014-07-02 — Lambda의 장점·문제, Kappa 4단계, 2배 저장, 단일 프레임워크 <https://www.oreilly.com/radar/questioning-the-lambda-architecture/>
  - Marz, "How to beat the CAP theorem", 2011-10-13 — Query = Function(All Data), 불변 데이터, 배치 계층 + realtime layer, human fault-tolerance <http://nathanmarz.com/blog/how-to-beat-the-cap-theorem.html>
  - Kafka 4.1 Consumer Configs — `auto.offset.reset`(기본 `latest`, `earliest`·`none`) <https://kafka.apache.org/41/configuration/consumer-configs/> · Design "Log Compaction"("at least the last known value") <https://kafka.apache.org/41/design/design/>
  - Kafka 4.1 Topic Configs — `retention.ms` 7일, `retention.bytes` -1, `segment.ms` 7일, `cleanup.policy`, `remote.storage.enable`, `local.retention.ms`·`local.retention.bytes` -2 <https://kafka.apache.org/41/configuration/topic-configs/>
  - Kafka 4.1.0 소스 `storage/src/main/java/org/apache/kafka/storage/internals/log/LogSegment.java` — `shouldRoll`·`timeWaitedForRoll`(세그먼트 roll을 배치 타임스탬프로 판정) <https://github.com/apache/kafka/blob/4.1.0/storage/src/main/java/org/apache/kafka/storage/internals/log/LogSegment.java>
  - Marz·Warren, 『Big Data: Principles and best practices of scalable realtime data systems』, Manning, 2015 — 3부 "Speed layer"(O'Reilly 목차, Internet Archive 2025 사본)
  - DDIA 1판 12장 "The Future of Data Systems" — 절 "Batch and Stream Processing"(O'Reilly 목차, Internet Archive 2024 사본으로 확인), 10장 "The Output of Batch Workflows"
- 실험 목록(scratchpad `de/05/exp07/`, 2026-10-07)
  - A `Lambda07.java` — OpenJDK 21.0.12, 실시간(처리 시각·중복 미제거) vs 배치(이벤트 시각·중복 제거), Kappa v2 출력을 새 테이블 vs 운영 테이블
  - B `Exp07.java` + `kafka-topics`·`kafka-configs`·`kafka-get-offsets` — `apache/kafka:4.1.0` 단일 노드 KRaft 전용 컨테이너 `sn-de-w05-kafka`(`--network none`), 30일 3,000건 → 보존 7일 변경 → 재처리 880건·9일, 세그먼트 6 → 3 (점검 재실행 2회: 7 → 2·8 → 2, 995·906건·10일)
