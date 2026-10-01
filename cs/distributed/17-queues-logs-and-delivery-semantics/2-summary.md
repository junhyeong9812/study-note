# distributed/17-queues-logs-and-delivery-semantics — 큐와 로그, 전달 보장(at-most/at-least/effectively-once), 순서 — 정리 (힌트)

## 해결하는 문제

서비스 A가 서비스 B에게 "주문이 생겼다"를 비동기로 넘긴다. 가운데에 브로커가 있다.
이 경로의 어느 지점에서든 프로세스가 죽거나 응답이 사라질 수 있다(03번 부분 실패).

```text
  주문 서비스 ──send──> [브로커] ──deliver──> 정산 서비스 ──> 정산 DB
       ① 응답 유실?           ② 복제 전 장애?        ③ 처리 후, 위치 저장 전 크래시?
```

- ①에서 응답을 못 받은 발행자는 다시 보낼지 정해야 한다. 다시 보내면 중복, 안 보내면 유실 가능.
- ③에서 소비자가 "어디까지 처리했나"를 언제 저장하느냐가 유실이냐 중복이냐를 가른다.
- 그래서 메시징에는 세 가지 질문이 늘 붙는다.
  - 메시지가 사라질 수 있나(유실)?
  - 두 번 처리될 수 있나(중복)?
  - 보낸 순서대로 처리되나(순서)?

쉬운 예: 등기 우편이다.
- 우체국이 "배달했다"는 확인을 못 받으면 다시 배달하러 간다. 받는 사람은 같은 편지를 두 번 받을 수 있다.
- 여러 집배원이 나눠 배달하면 먼저 부친 편지가 늦게 도착할 수 있다.

똑같은 구조다.\
"확인을 못 받으면 다시 보낸다"를 택하면 중복이 생기고, 일을 나눠 병렬로 처리하면 전체 순서가 깨진다.

실무 예:
- 결제 완료 이벤트가 두 번 소비돼 포인트가 두 번 적립된다.
- "주문 생성"보다 "주문 취소"가 먼저 처리돼 취소가 무시된다.
- 배포 중 컨슈머가 재시작된 뒤 몇백 건이 다시 처리된다.

기초(언제 비동기로 가나, 큐는 완충일 뿐이다, 백프레셔, 메시지 나이 알림)는 원본 [systems/server-design/07-async-messaging](../../systems/server-design/07-async-messaging.md) §1·§3에 있다. 이 노트는 전달 보장과 순서를 판다.

## 동작·원리

### 1. 큐와 로그 — 메시지를 "지우느냐, 위치만 옮기느냐"

```text
  큐 (RabbitMQ·SQS 류)                     로그 (Kafka 류)
  ┌───┬───┬───┬───┐                        파티션 0: [0][1][2][3][4][5][6] ──> 뒤에만 붙인다
  │m1 │m2 │m3 │m4 │ ← 브로커가 메시지별로        ▲           ▲
  └───┴───┴───┴───┘   전달·ack를 추적          그룹 billing   그룹 analytics
   ack 받으면 삭제                             (오프셋 3)      (오프셋 6)
   소비자끼리 나눠 가짐                         각 그룹이 전체를 자기 속도로 읽는다
```

- *큐*: 브로커가 메시지마다 "누구에게 줬나, ack가 왔나"를 기억한다. ack가 오면 지운다. 같은 큐의 소비자들은 메시지를 나눠 가진다(작업 분배).
- *로그*: 메시지를 뒤에 붙이기만 하고, 소비해도 지우지 않는다. 보존 기간(Kafka `retention.ms`)이나 크기(`retention.bytes`)를 넘은 세그먼트를 통째로 지운다(compact 토픽은 키별 최신 값을 적어도 하나 남긴다 — 옛 값은 백그라운드 압축 때 지워져 그 전까지는 남아 있을 수 있다, 21번).
  - *오프셋(offset)*: 파티션 안에서 메시지마다 붙는 단조 증가 번호. 파티션 밖에서는 의미가 없다.
  - *컨슈머 그룹*: 같은 `group.id`를 쓰는 소비자 묶음. 그룹 안에서는 파티션 하나를 한 소비자만 맡고, 그룹끼리는 서로 독립이다(Kreps 외 2011 §3.2).
- 로그에서 브로커가 소비자에 대해 기억하는 것은 그룹별 **커밋된 오프셋 숫자 하나**(파티션마다)다. 메시지별 ack 상태는 없다.
- 그래서 로그는 재처리(오프셋 되감기)와 새 소비자 추가가 쉽다. 큐는 메시지별 재전달·우선순위·지연 전달 같은 "작업 하나하나" 관리가 쉽다.
- 경계가 흐려지고 있다: Kafka 4.1은 *share group*(KIP-932, "Queues for Kafka")을 **미리보기(preview)** 로 넣었다. 파티션을 한 소비자에게 묶지 않고 여럿이 나눠 읽으며, 레코드별 ack와 전달 시도 횟수를 센다(Kafka 4.1 upgrade 노트). 기본으로는 꺼져 있고 `share.version=1`로 켠다.

실험(아래 §5 공용 환경)에서 같은 토픽을 그룹 두 개로 읽으면 둘 다 15건 전부를 받았다.
  - 단 커밋 위치가 없는 새 그룹은 `auto.offset.reset`을 따른다. Kafka 4.1 기본값은 `latest`라 기존 레코드를 건너뛴다. 처음부터 읽으려면 `earliest`(콘솔 컨슈머는 `--from-beginning`)를 준다(실험, Kafka 4.1.0 공용 노드, 2026-10-01: 3건 있는 토픽을 새 그룹이 기본값으로 읽으면 0건, `--from-beginning`이면 3건).

```text
(실험, Kafka 4.1.0 KRaft 단일 노드 공용 sn-dw-kafka, 2026-10-01 정합 점검 때 다시 돌림)
# 3파티션 토픽에 키 A·D·F로 5건씩(15건) 넣은 뒤, 새 그룹 두 개를 차례로 시작
# kafka-console-consumer.sh --topic w-cons-groups --group <그룹> --from-beginning --timeout-ms 8000
== w-cons-billing (--from-beginning)   F1 F2 F3 F4 F5 A1 A2 A3 A4 A5 D1 D2 D3 D4 D5
== w-cons-analytics (--from-beginning) F1 F2 F3 F4 F5 A1 A2 A3 A4 A5 D1 D2 D3 D4 D5
# 같은 명령에서 --from-beginning만 뺀 새 그룹(기본 auto.offset.reset=latest)
== w-cons-latest                       Processed a total of 0 messages
```

- 두 그룹 모두 `--from-beginning`(= `auto.offset.reset=earliest`)으로 시작했다. 그래서 각자 15건 전부를 받았다.
- 기본값으로 시작한 `w-cons-latest`는 0건을 받았다. `kafka-consumer-groups.sh --describe`로 보면 세 파티션 모두 CURRENT-OFFSET 5 = LOG-END-OFFSET 5, 즉 기존 레코드를 건너뛴 위치가 커밋됐다.
- 파티션끼리의 출력 순서(F·A·D)는 실행마다 다를 수 있다. 같은 키(같은 파티션) 안의 순서만 유지된다. 실험 뒤 토픽과 그룹 세 개를 지웠다.

### 2. 전달 보장 세 가지 — "언제 위치를 저장하나"가 정한다

```text
  at-most-once (처리 전에 위치 저장)          at-least-once (처리 후에 위치 저장)
  poll ─> commit(50) ─> 처리 0..34 ─X 크래시   poll ─> 처리 0..9 ─> commit(10) ─> ... ─> 처리 30..34 ─X
  재시작: 50부터 읽음                          재시작: 30부터 읽음
  → 35..49 처리 안 됨 = 유실                    → 30..34 다시 처리 = 중복
```

- *at-most-once*: 많아야 한 번. 유실될 수 있고 중복은 없다.
- *at-least-once*: 적어도 한 번. 유실은 없고 중복될 수 있다.
- *exactly-once*: 정확히 한 번. Kafka 문서는 이 말이 "작은 글씨를 읽어야 하는" 주장이라고 적는다. 소비자·발행자 장애, 소비자 여럿, 디스크 유실 경우까지 성립하는지 봐야 한다는 뜻이다(Kafka 4.1 문서 4.6 Message Delivery Semantics).
- 같은 문서가 위 그림의 두 순서를 그대로 at-most-once·at-least-once로 정의한다.
- 전달 보장은 **두 반쪽**으로 나뉜다(4.6).
  - 발행 쪽: 메시지가 로그에 "커밋"됐나. Kafka에서 커밋은 그 파티션 ISR 전원이 받은 것이다(21번).
  - 소비 쪽: 소비자가 처리와 위치 저장을 어떤 순서로 하나.

### 3. 실험: 커밋 순서별 유실·중복 개수

- 100건을 넣은 토픽(파티션 1개)을 `max.poll.records=50`으로 읽는다. 35건 처리 뒤 "크래시"한다.
- 크래시는 커밋 없이 `close()`하는 것으로 흉내 냈다(그룹을 정상 탈퇴하므로 실제 크래시보다 재할당이 빠르다). 두 번째 실행이 끝까지 읽는다.
- 코드 핵심(`Delivery17.java`)

```java
if (commitBefore) {                                   // 처리 전 커밋: 받은 배치 끝까지
    long next = list.get(list.size() - 1).offset() + 1;
    c.commitSync(Map.of(tp, new OffsetAndMetadata(next)));
}
int n = 0;
for (ConsumerRecord<String,String> r : list) {
    if (n == 35) break;                               // 35건 처리 후 크래시
    processed.merge(r.value(), 1, Integer::sum); n++;
    if (!commitBefore && n % 10 == 0)                 // 처리 후 커밋: 10건마다
        c.commitSync(Map.of(tp, new OffsetAndMetadata(r.offset() + 1)));
}
```

```text
(실험, Kafka 4.1.0 KRaft 단일 노드, kafka-clients 4.1.0, 2026-10-01)
[w17-g-before] 1회차 배치 50건 받음, 35건 처리 후 크래시, 커밋된 오프셋=OffsetAndMetadata{offset=50, ...}
[w17-g-before] 2회차 시작 오프셋=50, 50건 처리
[w17-g-before] 처리 호출 85회, 고유 85건, 유실 15건, 중복 0건
[w17-g-after] 1회차 배치 50건 받음, 35건 처리 후 크래시, 커밋된 오프셋=OffsetAndMetadata{offset=30, ...}
[w17-g-after] 2회차 시작 오프셋=30, 70건 처리
[w17-g-after] 처리 호출 105회, 고유 100건, 유실 0건, 중복 5건
```

- 관찰
  - 처리 전 커밋: 커밋한 50과 처리한 35 사이의 15건(35..49)이 사라졌다.
  - 처리 후 커밋: 마지막 커밋(30) 뒤에 처리한 5건(30..34)이 다시 처리됐다.
- 해석: 이 실험처럼 오프셋이 연속이고 순서대로 처리한 구간에서는 유실 개수 = "커밋 위치 − 실제 처리 위치", 중복 개수 = "실제 처리 위치 − 커밋 위치"다(압축·트랜잭션 마커가 있으면 오프셋 차 ≠ 레코드 수). 커밋을 자주 할수록 중복 창은 줄지만 0은 되지 않는다.

### 4. effectively-once — 어디까지가 "정확히 한 번"인가

at-least-once 위에서 중복을 **결과에서** 없애는 것을 흔히 *effectively-once*라 부른다. 범위가 셋으로 다르다.

```text
  범위                         장치                                  보장되는 것
  ─────────────────────────────────────────────────────────────────────────────────────
  프로듀서 → 파티션 로그        멱등 프로듀서(PID + 시퀀스 번호)          한 프로듀서 세션의 재시도가 로그에 중복을 안 만든다
  Kafka → (처리) → Kafka       트랜잭션 + read_committed                출력 레코드와 입력 오프셋 커밋이 함께 반영·폐기된다
  Kafka → 외부 DB             멱등 소비(인박스·조건부 UPDATE·업서트)     같은 메시지를 두 번 처리해도 결과가 한 번과 같다
```

- *멱등 프로듀서*: 브로커가 프로듀서마다 ID(PID)를 주고, 메시지에 붙은 시퀀스 번호로 재전송 중복을 걸러 낸다(Kafka 4.1 문서 4.6).
  - 새 프로듀서 인스턴스는 새 PID를 받으므로 **한 프로듀서 세션 안에서만** 보장된다(KIP-98).
  - kafka-clients 4.1.0 기본값은 `acks=all`, `enable.idempotence=true`다(실험에서 `ProducerConfig` 기본값 출력으로 확인). `acks`를 1로 바꾸는 등 충돌 설정을 주고 멱등을 명시하지 않으면 조용히 꺼진다(`enable.idempotence` 설정 문서).
- *트랜잭션*: 여러 파티션에 쓴 레코드와 소비 오프셋을 한 단위로 커밋하거나 폐기한다. 오프셋도 내부 토픽에 저장되는 메시지라 같은 트랜잭션에 넣을 수 있다(4.6).
  - 기본 `isolation.level=read_uncommitted` 소비자는 폐기된 트랜잭션의 레코드도 본다. `read_committed`만 걸러 낸다.
- **외부 DB에 쓰는 순간** 트랜잭션은 그 쓰기를 묶지 못한다. Kafka 문서의 처방은 "오프셋을 출력과 같은 곳에 저장하라"다(4.6). 실무에서는 멱등 소비가 같은 효과를 낸다.

실험 — 트랜잭션 하나는 5건 쓰고 abort, 다음 하나는 5건 쓰고 commit했다.

```text
(실험, Kafka 4.1.0 KRaft 단일 노드, 2026-10-01)
[tx] read_uncommitted → 10건 [aborted-0@0, ..., aborted-4@4, committed-0@6, ..., committed-4@10]
[tx] read_committed   → 5건 [committed-0@6, committed-1@7, committed-2@8, committed-3@9, committed-4@10]
```

- 오프셋 5와 11이 비어 있다. 트랜잭션의 끝(abort·commit)을 표시하는 *컨트롤 레코드*가 그 자리를 차지했고, 소비자에게는 넘어오지 않는다.
- 해석: "폐기된 것은 안 보인다"는 소비자 설정에 달려 있다. 기본값 그대로면 abort된 5건이 그대로 처리된다.

### 5. 순서 — 파티션 안에서만

```text
  발행: A1 D1 F1 A2 D2 F2 ... (키 A·D·F)
           │ hash(key) % 3
  파티션 0: D1 D2 D3 D4 D5
  파티션 1: A1 A2 A3 A4 A5        각 파티션 안 순서 = 발행 순서
  파티션 2: F1 F2 F3 F4 F5
           │ 소비자는 파티션별로 묶어서 가져온다
  소비: A1 A2 A3 A4 A5 F1 F2 F3 F4 F5 D1 D2 D3 D4 D5   ← 키 사이의 순서는 사라졌다(파티션 묶음 순서는 실행마다 다르다)
```

```text
(실험, Kafka 4.1.0 KRaft 단일 노드, 파티션 3개, 2026-10-01)
[order] 발행 순서 : A1 D1 F1 A2 D2 F2 A3 D3 F3 A4 D4 F4 A5 D5 F5
[order] 소비 순서 : A1 A2 A3 A4 A5 F1 F2 F3 F4 F5 D1 D2 D3 D4 D5
[order] 키→파티션 : {A=1, D=0, F=2}
```

- 파티션을 어느 순서로 가져오는지는 실행마다 다르다. 사실 점검 때 같은 코드를 다시 돌리니 `F1..F5 A1..A5 D1..D5` 순서로 나왔다. 변하지 않은 것은 각 키 안의 순서(A1→A5)와 키→파티션 배치뿐이다.

- Kafka는 파티션 안의 순서만 보장한다. 같은 키는 기본 파티셔너가 `murmur2(키) % 파티션 수`로 같은 파티션에 보낸다(kafka-clients `Utils.murmur2`·`toPositive`로 위 배치를 계산해 확인).
- 같은 키 안에서도 순서가 깨지는 경우
  - 파티션 수를 늘리면 `% N`의 N이 바뀌어 키가 다른 파티션으로 간다. 옛 파티션에 남은 메시지와 새 파티션의 메시지가 동시에 소비될 수 있다.
  - 멱등을 끄고 `max.in.flight.requests.per.connection`이 1보다 크면, 재시도된 배치가 뒤 배치보다 늦게 들어갈 수 있다. 멱등을 켜면 5 이하의 어떤 값에서도 순서를 지킨다. 상한이 5인 이유는 브로커가 프로듀서마다 최근 배치 5개까지만 기억하기 때문이다(`enable.idempotence`·`max.in.flight.requests.per.connection` 설정 문서).
  - 소비 쪽에서 재시도 토픽으로 넘기면 그 메시지는 같은 키의 뒤 메시지보다 늦게 처리된다(18번).
  - Kafka 4.1 share group은 파티션을 여럿이 나눠 읽으므로 순서를 기대하지 않는 처리용이다(upgrade 노트).

## 쓰이는 자료구조·알고리즘

- **append-only 로그 + 오프셋** — 쓰기는 끝에만, 읽기는 "오프셋 N부터". 소비 상태가 숫자 하나라 브로커가 메시지별 상태를 들고 있지 않는다. 세그먼트·인덱스 구조는 [21-kafka-internals](../21-kafka-internals/2-summary.md).
- **해시 분할** — `murmur2(키) % N`. 같은 키 → 같은 파티션 → 키 안 순서. N이 바뀌면 배치가 바뀐다(일관 해싱이 아님). [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)와 대비.
- **(PID, 시퀀스 번호) 중복 제거** — 브로커가 프로듀서별 최근 배치(최대 5개)의 시퀀스를 기억해 같은 번호의 재전송을 버린다. TCP가 시퀀스 번호로 재전송 중복을 버리는 것과 같은 발상이다([network/16-tcp-reliability-retransmission](../../network/16-tcp-reliability-retransmission/2-summary.md)).
- **유니크 인덱스 = 처리한 메시지 ID 집합** — 인박스 테이블의 PK가 "이미 본 ID인가"를 O(log n)으로 판정한다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)의 집합과 같은 역할을 DB가 트랜잭션과 함께 해 준다.

## 적용 — 풀어나가는 법

### 1. 결정 순서

1. **유실과 중복 중 무엇을 견딜 수 있나** — 결제·정산·재고면 유실은 안 된다 → at-least-once + 멱등 소비. 지표 샘플링처럼 일부 빠져도 되면 at-most-once도 된다.
2. **순서가 필요한 최소 단위**를 키로 잡는다 — 주문 ID, 계좌 ID. 전체 순서가 필요하면 파티션 1개(확장 포기)다.
3. **발행 쪽**: 기본값(`acks=all`, 멱등 켜짐)을 유지한다. 토픽 `min.insync.replicas`를 2 이상으로 둔다(21번).
4. **소비 쪽**: 자동 커밋을 끄고 처리 후 커밋하거나, 자동 커밋이면 poll 루프 안에서 동기 처리한다(18번 실험).
5. **중복 흡수**: 생산자가 만든 안정적 메시지 ID로 인박스 또는 조건부 UPDATE·업서트.

### 2. at-least-once 소비 루프 (Java, kafka-clients 4.1)

```java
props.put("enable.auto.commit", "false");
try (KafkaConsumer<String, String> c = new KafkaConsumer<>(props)) {
    c.subscribe(List.of("orders"));
    while (running) {
        ConsumerRecords<String, String> recs = c.poll(Duration.ofMillis(500));
        for (ConsumerRecord<String, String> r : recs) {
            handler.handle(r);          // 멱등해야 한다 — 크래시하면 마지막 커밋 위치부터 다시 온다(배치 앞부분도 재처리)
        }
        if (!recs.isEmpty()) c.commitSync();   // 처리 끝난 뒤 커밋
    }
}
```

### 3. 멱등 소비 — 인박스 (PostgreSQL)

```sql
CREATE TABLE inbox (message_id text PRIMARY KEY, processed_at timestamptz DEFAULT now());

BEGIN;
WITH ins AS (                                    -- 이미 있으면 0행 → ins가 빈다
  INSERT INTO inbox (message_id) VALUES ($1) ON CONFLICT DO NOTHING RETURNING 1
)
UPDATE account SET points = points + $2
 WHERE id = $3 AND EXISTS (SELECT 1 FROM ins);   -- 처음 본 메시지일 때만 적립, 같은 트랜잭션
COMMIT;
```

- (확인, PostgreSQL 17 일회용 컨테이너, 2026-10-01) 같은 `message_id`로 두 번 실행하면 `points`는 10 한 번만 올랐다.

- `message_id`는 생산자가 만든 ID를 쓴다. Kafka 오프셋은 같은 내용이 다시 발행되면 달라지므로 맞지 않는다.

### 4. 진단 명령

```bash
# 그룹별 커밋 위치와 lag (파티션마다)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group w17-g-after
#  GROUP        TOPIC    PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
#  w17-g-after  w17-pay  0          100             100             0      (실험 출력)

# 파티션 수·리더·ISR
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic orders
```

- 재처리가 필요하면 그룹을 멈추고 `kafka-consumer-groups.sh --reset-offsets --to-datetime ... --execute`로 위치를 되돌린다. 되돌린 구간은 전부 다시 처리되므로 멱등이 전제다.

## 장애 시나리오와 대처

### 1. at-least-once → 중복 소비 (⚠)

- **현상**: 포인트가 두 번 적립되고, 알림 메일이 두 번 간다.
- **보이는 형태**: 같은 이벤트 ID의 처리 로그가 두 줄이다. 배포·재시작 시각에 몰려 있다. 컨슈머 로그에 리밸런스(파티션 회수·그룹 재합류 로그) 직후 같은 오프셋 구간을 다시 읽은 흔적이 있다.
- **원인**: 처리 후 커밋 전에 프로세스가 죽거나 파티션이 다른 소비자로 넘어갔다. 실험에서 30..34의 5건이 그렇게 다시 처리됐다.
- **대처**: 커밋을 자주 하는 것으로는 0이 안 된다. 인박스·조건부 UPDATE로 처리를 멱등하게 만든다. 외부 부작용(메일·결제 API)은 멱등 키를 같이 보낸다.

### 2. 파티션 간 순서 역전 (⚠)

- **현상**: "주문 취소"가 "주문 생성"보다 먼저 처리돼 무시되고, 취소된 주문이 배송된다.
- **보이는 형태**: 같은 주문의 이벤트가 서로 다른 파티션에 있다(`kafka-console-consumer --property print.partition=true`). 처리 시각이 이벤트 발생 순서와 다르다.
- **원인**: 키 없이 발행했거나(파티션이 배치마다 바뀜), 키를 주문 ID가 아닌 다른 값으로 잡았다. Kafka는 파티션 사이 순서를 보장하지 않는다.
- **대처**: 순서가 필요한 단위를 키로 쓴다. 순서에 기대지 않도록 이벤트에 버전을 넣고 낡은 이벤트를 버린다(`UPDATE ... WHERE version < :v`) — 원본 07 §4.

### 3. 파티션 수를 늘린 직후 같은 키의 순서가 깨진다

- **현상**: 파티션 증설 직후 몇 분 동안 같은 주문의 이벤트가 뒤섞여 처리된다.
- **보이는 형태**: 같은 키가 증설 전에는 파티션 1, 뒤에는 파티션 4에 있다.
- **원인**: `murmur2(키) % N`에서 N이 바뀌었다. 옛 파티션에 밀린 메시지와 새 파티션의 메시지를 다른 소비자가 동시에 처리한다.
- **대처**: 순서가 중요한 토픽은 처음부터 파티션을 넉넉히 잡는다. 늘려야 하면 옛 파티션의 lag이 0이 될 때까지 발행을 멈추거나, 새 토픽으로 옮긴다.

### 4. "exactly-once를 켰는데" 외부 DB에 중복이 생긴다

- **현상**: Kafka 트랜잭션·`processing.guarantee=exactly_once_v2`를 켰는데 DB 행이 두 번 들어간다.
- **보이는 형태**: Kafka 출력 토픽에는 중복이 없는데 DB에는 있다.
- **원인**: 트랜잭션은 Kafka 안의 쓰기와 오프셋만 묶는다. 외부 DB 쓰기는 그 밖이다. 트랜잭션이 abort되고 재시도되면 DB 쓰기는 이미 한 번 일어난 뒤다.
- **대처**: DB 쓰기를 멱등하게 하거나, 오프셋을 DB에 같은 트랜잭션으로 저장하고 시작할 때 거기서 `seek`한다(4.6의 처방).

### 5. 기본 `read_uncommitted` 소비자가 폐기된 트랜잭션을 처리한다

- **현상**: 트랜잭션 프로듀서가 abort한 주문이 다운스트림에서 처리됐다.
- **보이는 형태**: 출력 토픽 오프셋에 구멍(컨트롤 레코드 자리)이 있고, abort된 레코드 내용이 소비 로그에 찍힌다. 실험에서 `read_uncommitted`는 10건을 모두 받았다.
- **원인**: 소비자 기본 `isolation.level`이 `read_uncommitted`다(kafka-clients 4.1.0 기본값 출력으로 확인).
- **대처**: 트랜잭션 토픽을 읽는 소비자에는 `isolation.level=read_committed`를 준다.

## 핵심 문장

- 큐는 메시지별 ack를 추적하고 지우며, 로그는 지우지 않고 그룹별 오프셋 숫자 하나만 둔다.
- 처리 전에 위치를 저장하면 at-most-once(유실), 처리 후에 저장하면 at-least-once(중복)다. 실험에서 같은 크래시가 유실 15건, 중복 5건을 만들었다.
- "exactly-once"는 범위를 붙여야 참이다. 멱등 프로듀서는 한 프로듀서 세션의 재시도를, 트랜잭션은 Kafka 안의 쓰기와 오프셋을 묶는다. 외부 DB는 멱등 소비로 맞춘다.
- Kafka의 순서 보장은 파티션 안까지다. 순서가 필요한 단위를 키로 잡고, 파티션 수 변경은 그 보장을 흔든다.
- 트랜잭션 레코드를 걸러 내는 것은 소비자의 `read_committed` 설정이다. 기본값은 `read_uncommitted`다.

## 관련 주제·근거

- 선행
  - [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md) — 발행 쪽 유실을 막는 아웃박스
  - [03-partial-failure-and-timeouts](../03-partial-failure-and-timeouts/2-summary.md) — 응답이 없을 때 결과를 모른다
  - 원본 [systems/server-design/07-async-messaging](../../systems/server-design/07-async-messaging.md) — 큐 vs 로그 표, 큐는 완충, 백프레셔, 멱등 3방법
- 후속
  - [18-consumer-failure-handling](../18-consumer-failure-handling/2-summary.md) — 자동 커밋의 실제 의미, 재시도·DLT·poison pill·리밸런스
  - [21-kafka-internals](../21-kafka-internals/2-summary.md) — 발행 쪽 "커밋"(ISR·acks)과 세그먼트
  - [22-event-sourcing](../22-event-sourcing/2-summary.md) — 로그를 원천으로 삼기
  - [30-batch-and-stream-processing](../30-batch-and-stream-processing/2-summary.md) — 로그 위의 스트림 처리
  - [19-message-types-channels-and-endpoints](../19-message-types-channels-and-endpoints/2-summary.md) — 채널·소비 패턴
- 교재·논문
  - DDIA 1판 11장 Stream Processing — 메시징 시스템, AMQP/JMS 방식 vs 로그 기반 브로커, 소비자 오프셋
  - Kreps·Narkhede·Rao, "Kafka: a Distributed Messaging System for Log Processing", NetDB 2011 — pull 모델, 컨슈머 그룹, "Kafka only guarantees at-least-once delivery"(당시 기준) <https://notes.stephenholiday.com/Kafka.pdf>
- Kafka 4.1 문서
  - 4.6 Message Delivery Semantics — 세 보장의 정의, 처리/위치 저장 순서, 멱등 프로듀서(PID·시퀀스), 트랜잭션과 isolation level, 외부 시스템은 오프셋을 출력과 같은 곳에 <https://kafka.apache.org/41/documentation.html#semantics> (소스: `docs/design.html` @ 4.1.0)
  - Upgrade 4.1.0 — share group(KIP-932) preview, `share.version=1` <https://kafka.apache.org/41/documentation.html#upgrade> (소스: `docs/upgrade.html` @ 4.1.0)
  - `ProducerConfig` 설정 문서 `acks`·`enable.idempotence`·`max.in.flight.requests.per.connection`(kafka-clients 4.1.0 `configDef()` 출력)
- KIP-98 Exactly Once Delivery and Transactional Messaging — "idempotent production within a single producer session" <https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging>
- 실험 목록(공용 `sn-dw-kafka` = Kafka 4.1.0 KRaft 단일 노드, 클라이언트는 `eclipse-temurin:21-jdk` 컨테이너 + kafka-clients 4.1.0, `--network container:sn-dw-kafka`)
  - 커밋 순서별 유실·중복(100건, 35건 처리 후 크래시): 처리 전 커밋 유실 15·중복 0, 처리 후 커밋 유실 0·중복 5
  - 트랜잭션 abort 5 + commit 5: `read_uncommitted` 10건, `read_committed` 5건, 오프셋 5·11은 컨트롤 레코드
  - 3파티션·키 A/D/F 발행 순서 vs 소비 순서, 키→파티션 {A=1, D=0, F=2}
  - 그룹 두 개(`--from-beginning`)가 같은 토픽 15건을 각각 전부 읽음, 기본값(`latest`) 새 그룹은 0건(정합 점검 때 토픽 `w-cons-groups`·그룹 `w-cons-*`로 다시 돌리고 삭제) · kafka-clients 4.1.0 기본값(`acks=all`·`enable.idempotence=true`·`isolation.level=read_uncommitted`·`enable.auto.commit=true`)
