# distributed/35-distributed-symptom-index — 증상 사전: 중복·유실·순서 역전·리더 둘·오래된 읽기·블로킹·음수 시간 → 보이는 형태·원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

분산 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"비동기 복제에서 리더가 OK한 뒤 팔로워가 받기 전에 승격한다 → 확인된 쓰기가 사라진다"처럼 쓴다.\
장애 현장에서는 반대 방향이 필요하다.\
손에 든 것은 고객 문의 한 줄("포인트가 두 번 들어왔어요"), 로그 한 줄(`etcdserver: request timed out`), 그래프 한 장(LAG 0인데 주문이 `PENDING`)뿐이다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                          이 노트 (역방향)
  원인 --> 메커니즘 --> 증상                   증상 --> 보이는 형태 --> 흔한 원인 --> 첫 진단 --> leaf
  "처리 후 커밋 전에 죽으면 다시 읽는다"         "같은 이벤트 ID가 두 줄이다. 커밋 시점부터 본다"
```

쉬운 예: 자동차 정비소의 "소리로 찾기" 표다.\
"브레이크 밟을 때 끼익" → 패드 마모부터 본다. "시동 걸 때 딸깍딸깍" → 배터리부터 본다.\
표는 고치지 않는다. **어디를 먼저 열어 볼지**만 정한다.

똑같은 구조다.\
"같은 효과가 두 번"이면 재시도·재전달·두 소유자 셋 중 하나다.\
"확인받았는데 없다"면 비동기 승격·커밋 순서·보존 기간·LWW 넷 중 하나인 경우가 많다.\
표가 각각의 첫 진단과 leaf를 알려 준다.

실무 예:
- 같은 사건이 층마다 **다른 이름**으로 보인다. etcd 과반 상실은 서버에서 `etcdserver: request timed out`, Go 클라이언트에서 `context deadline exceeded`, 사용자에게는 "설정 저장 실패"다.
- 분산 증상의 상당수는 **에러가 없다.** LWW로 사라진 쓰기, 처리 전 커밋으로 빠진 메시지, 늦은 set으로 고착된 캐시는 로그 한 줄 남기지 않는다.
- 같은 말이 **범위**에 따라 뜻이 다르다. "exactly-once"는 Kafka 안 경로의 보장이고, 외부 DB 쓰기는 그 밖이다.

## 동작·원리

### 0. 증상이 올라오는 길 — 어느 층이 만든 말인가

```text
  +---------------------------------------------------------------------------+
  | 사용자·업무     "두 번 결제됨" "주문했는데 목록에 없음" "지운 게 다시 보임"     |
  +---------------------------------------------------------------------------+
  | 애플리케이션     HTTP 504, 사가 PENDING, 상태 전이 위반, 대사 불일치            |
  +---------------------------------------------------------------------------+
  | 클라이언트 라이브러리  context deadline exceeded, CommitFailedException,        |
  |                 NotEnoughReplicasException, UnavailableException          |
  +---------------------------------------------------------------------------+
  | 프로토콜·서버    etcd/raft 로그(became candidate), Kafka 브로커 로그(Truncating), |
  |                 ISR·term·offset·revision 지표                               |
  +---------------------------------------------------------------------------+
  | 시간·네트워크    NTP 동기 상태, 시계 오프셋, 분할, 패킷 유실, GC·VM 정지         |
  +---------------------------------------------------------------------------+
```

- 아래층 사건이 위층 이름으로 **번역**된다. 번역하면서 정보가 줄어든다.
  - 예: 과반을 잃은 etcd 3.6.5는 서버에서 `etcdserver: request timed out`(`server/etcdserver/errors/errors.go`)을 낸다. 클라이언트가 자기 기한을 먼저 넘기면 Go의 `context deadline exceeded`만 남는다.
- 보장은 **층마다 따로** 있다. 프로토콜 보장(Raft 커밋), 클라이언트 라이브러리 기본값(Kafka 소비자 `isolation.level`), 애플리케이션 책임(멱등 처리)을 섞어 읽지 않는다.
- 그래서 색인을 쓰기 전에 세 가지를 확보한다.
  - **원문**: 예외 체인 전체, 서버 로그 줄, 제품과 판(etcd 3.6.5, Kafka 4.1.0 등).
  - **모양**: 즉시 실패인가, 몇 초 멈춘 뒤 실패인가, 에러 없이 값만 틀렸나.
  - **시각**: 배포·재시작·리밸런스·페일오버·윤초·NTP 변경·GC 멈춤과 겹치나. 분산 증상은 대개 "무언가 바뀐 순간"에 몰린다.

  - *색인(index)*: 찾을 말 → 그 말이 나오는 위치 목록. 이 노트에서는 증상 → leaf 장애 절이다.
  - *첫 진단*: 원인을 확정하는 조사가 아니라, 가설을 가장 빨리 가르는 확인 한 가지다.

### 1. 일곱 증상의 지도

커리큘럼이 정한 일곱 증상이 뼈대다. 각 증상 아래 원인 가족이 몇 개씩 있다.

```text
  증상                원인 가족(몇 개만)                               첫 갈림길
  ─────────────────   ──────────────────────────────────────────────   ─────────────────────────
  중복 처리           재시도 · 재전달(at-least-once) · 두 소유자          같은 ID인가, 다른 ID인가
  유실                비동기 승격 · 커밋 순서 · 보존 기간 · LWW · 이중 쓰기 원천엔 있나, 전달 경로 어디서 끊겼나
  순서 역전           벽시계 정렬 · 키/파티션 · 병렬 소비 · 릴레이 여럿  같은 키가 같은 파티션·소비자로 갔나
  리더 둘             분할 · 리스+멈춤 · 락 만료 · 상태 잃은 노드        펜싱 번호가 쓰기에 실렸나
  오래된 읽기         복제 지연 · 정족수 불일치 · 캐시 · 프로젝션 지연     어느 경로(복제본·캐시·뷰)로 읽었나
  블로킹·진행 없음     2PC in-doubt · 과반 상실 · poison · 완료 조건 없음  누가 무엇을 기다리나
  음수 시간·시계       벽시계 경과 · 시계 어긋남 · 시계 역행 · 윤초        벽시계를 어디에 썼나
```

- 일곱 칸 밖에도 자주 나오는 무리가 있다. **부하 증폭·폭주**(재시도 폭풍, 선거 폭풍, 무효화 폭풍)와 **누적·크기**(툼스톤, 슬롯, 버퍼)다. §8·§9에 둔다.
- 한 사건이 여러 칸에 걸친다. 분할 하나가 리더 둘 → 유실 → 오래된 읽기로 번진다(GitHub 2018, [36](../36-distributed-incidents/2-summary.md)).

### 2. 중복 처리 — 같은 효과가 두 번

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 결제사 정산에 같은 카드·금액 승인이 몇 초 간격으로 여러 건. 내부엔 `HttpTimeoutException` 뒤 재시도 로그 | 응답 지연·유실을 실패로 단정, 멱등 키 없이 재전송 | 요청 로그에 멱등 키가 있나, 재시도가 같은 키를 썼나 | [03 §1](../03-partial-failure-and-timeouts/2-summary.md) · [01 §2](../01-why-distributed-and-fallacies/2-summary.md) |
| 멱등 키가 있는데 같은 키가 저장소에 두 줄, 또는 키만 다른 같은 요청 둘 | 재시도마다 새 키, "조회 후 삽입", 키와 결과를 다른 트랜잭션에, 키 보존 < 재시도 기간 | 키 표의 유일 제약, 키 생성 위치(재시도 루프 안인가) | [03 §5](../03-partial-failure-and-timeouts/2-summary.md) |
| 같은 이벤트 ID 처리 로그 두 줄. 배포·재시작·리밸런스 시각에 몰림 | at-least-once 재전달: 처리 후 커밋 전에 죽거나 파티션이 넘어감 | 컨슈머 로그의 리밸런스 시각, 중복 구간 오프셋 | [17 §1](../17-queues-logs-and-delivery-semantics/2-summary.md) · [25 §1](../25-impossibility-results/2-summary.md) |
| `CommitFailedException: Offset commit cannot be completed since the consumer is not part of an active group ...`, WARN `consumer poll timeout has expired ...` (kafka-clients 4.1.0) | 처리 시간이 `max.poll.interval.ms`를 넘어 그룹에서 빠짐 → 새 소유자가 다시 처리 | 배치당 처리 시간 vs `max.poll.interval.ms`, `max.poll.records` | [18 §2](../18-consumer-failure-handling/2-summary.md) |
| 같은 이벤트 id로 하위 처리 두 줄, outbox 릴레이 재시작 직후 | outbox는 at-least-once. 발행 후 표시 전 크래시 | 릴레이 표시 커밋 단위, 재시작 횟수 | [16 §3](../16-outbox-and-dual-write/2-summary.md) |
| 대조(reconciliation) 배치 직후 같은 상태 이벤트가 두 번 | dispatch log: 발행 후 로그 전 크래시 | 배치 회차별 재발행 건수 | [29 §3](../29-outbox-vs-dispatch-log/2-summary.md) |
| Kafka 출력 토픽엔 중복이 없는데 외부 DB엔 두 행 | 트랜잭션·`exactly_once_v2`의 범위는 Kafka 안. DB 쓰기는 그 밖 | 부작용(DB·메일·API)이 트랜잭션 경계 밖인가 | [17 §4](../17-queues-logs-and-delivery-semantics/2-summary.md) · [25 §1](../25-impossibility-results/2-summary.md) |
| 중복 제거 표가 있는데도 드물게 중복. 처리 결과는 있는데 `processed_event`에 ID 없음 | 처리와 중복 제거 기록을 다른 트랜잭션으로 커밋 | 두 쓰기가 한 트랜잭션인가 | [25 §2](../25-impossibility-results/2-summary.md) |
| 같은 배치·메일·결제가 두 번. 두 노드에 "리더가 됨" 로그, GC 로그에 TTL보다 긴 멈춤 | 느림을 죽음으로 판단, 리스·락 만료 뒤 옛 소유자가 계속 일함 | GC·VM 정지 시각과 리스 TTL 비교 | [02 §1](../02-system-and-failure-models/2-summary.md) · [10 §2](../10-leader-election/2-summary.md) · §5 |
| 재시작 뒤 같은 주문의 결제를 두 번 시도, 걸음 로그가 처음부터 다시 | 사가 진행 상태가 메모리에만 | 사가 표에 걸음 기록이 있나, 참가자 호출에 멱등 키가 있나 | [15 §4](../15-saga/2-summary.md) |
| 읽기 모델 재구축 시각에 외부 발송 API 호출 폭증, 고객이 옛 알림을 다시 받음 | 부작용 핸들러를 순수 프로젝션과 함께 재생 | 재생 모드에서 부작용이 꺼지나 | [22 §4](../22-event-sourcing/2-summary.md) |
| 같은 배치를 다시 돌렸더니 출력 파티션 사이에 중복 또는 누락 | map·reduce가 비결정적(시각·난수·외부 조회) + 태스크 재실행 | 함수 안 `now()`·난수·외부 호출 | [30 §5](../30-batch-and-stream-processing/2-summary.md) |
| 트랜잭션 프로듀서가 abort한 레코드가 하위에서 처리됨, 출력 토픽 오프셋에 구멍 | 소비자 기본 `isolation.level=read_uncommitted`(kafka-clients 4.1.0) | 소비자 설정의 `isolation.level` | [17 §5](../17-queues-logs-and-delivery-semantics/2-summary.md) |
| `duplicate key value violates unique constraint` (PostgreSQL), upsert면 남의 행을 조용히 덮음 | ID 생성기 문제(시계 역행, worker ID 중복) — "같은 ID로 다른 것" | 두 ID를 해독(worker·ms·순번) | [13 §1](../13-distributed-id-generation/2-summary.md) · [13 §2](../13-distributed-id-generation/2-summary.md) |

- 첫 갈림길은 **ID가 같은가**다.
  - 같은 요청·이벤트 ID가 두 번 처리됐으면 재시도·재전달이다. 처리 쪽 멱등으로 막는다.
  - ID가 다른데 같은 일이 두 번이면 두 소유자(§5)나 키 재발급이다.
  - 같은 ID인데 **다른 것**이면 ID 생성기 문제다.

### 3. 유실 — 확인받았는데 없다, 원천엔 있는데 하위엔 없다

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 페일오버 뒤 "성공" 응답을 받은 주문이 없다. 새 리더의 마지막 위치(오프셋·LSN·GTID)가 옛 리더보다 뒤 | 비동기 복제 + 승격. 분할 중 쓰기를 받은 쪽(A 선택)이 승격되면 그 창의 쓰기가 사라짐 | 옛 리더와 새 리더의 마지막 위치 비교, 옛 리더 로그(binlog 등) 보존 | [06 §3](../06-replication-strategies/2-summary.md) · [08 §3](../08-cap-and-pacelc/2-summary.md) |
| 프로듀서는 성공 콜백, 컨슈머엔 없음. 돌아온 옛 리더 로그에 `Truncating partition ... TruncationState(offset=N ...)`·`Truncating to offset N` (Kafka 4.1.0) | `acks=1`, 또는 ISR이 리더 하나 + `min.insync.replicas=1` | 프로듀서 `acks`, 토픽 `min.insync.replicas`, 장애 전후 `--under-replicated-partitions` | [21 §1](../21-kafka-internals/2-summary.md) |
| DB 주문 수 > 토픽 메시지 수. 배포·재시작 시각의 주문에 몰림, 오류 로그 없음 | 이중 쓰기: 커밋 후 발행 전 크래시 | 원천과 토픽 건수 대조 | [16 §1](../16-outbox-and-dual-write/2-summary.md) |
| 사건형 소비자 처리 수 < 원천 승인 수. 대조 배치는 "재발행 0건" | dispatch log 대조는 현재 상태만 봄 → 지나간 중간 전이를 못 찾음 | 사건형 이벤트가 outbox를 타나 | [29 §1](../29-outbox-vs-dispatch-log/2-summary.md) |
| 커밋 오프셋·lag은 정상인데 원천 대비 처리 건수가 모자람. 재시작·OOM 시각과 겹침 | 처리 전 커밋, 자동 커밋 + 다른 스레드로 처리 넘김 | 커밋 호출 위치, `enable.auto.commit` | [18 §1](../18-consumer-failure-handling/2-summary.md) |
| 재시작 뒤 LAG 0인데 주문 다수가 결제조차 안 됨 | 인자 없는 `commitSync()`가 poll 묶음 전체를 커밋 | 커밋 호출의 오프셋 인자 | [23 §3](../23-orchestration-vs-choreography/2-summary.md) |
| 멈췄던 그룹을 켰더니 처리 건수가 거의 없음. 브로커 로그 `Deleting segment ... due to log retention time ...ms breach ...`, `Incremented log start offset to N due to segment deletion` (Kafka 4.1.0) | 보존 기간 < 그룹 정지 시간. 보존은 커밋 위치를 보지 않음 | 그룹 CURRENT-OFFSET vs 로그 시작 오프셋, `auto.offset.reset` | [21 §3](../21-kafka-internals/2-summary.md) |
| 두 사용자가 동시에 고쳤는데 한쪽 수정이 흔적 없이 사라짐, 둘 다 성공 응답 | LWW(마지막 쓰기 승리), 다중 리더 충돌, "램포트 값 큰 쪽 승" | 감사 로그(쓰기 요청)와 최종 상태 대조 | [24 §1](../24-conflict-resolution-and-crdt/2-summary.md) · [06 §1](../06-replication-strategies/2-summary.md) · [05 §4](../05-logical-clocks/2-summary.md) |
| 방금 고친 값이 저장되지 않음. Cassandra `WRITETIME()`이 현재보다 미래 | LWW 타임스탬프가 앞선 시계에서 나옴 | 노드·클라이언트 시계 오프셋 | [24 §2](../24-conflict-resolution-and-crdt/2-summary.md) · [04 §3](../04-physical-clocks-and-ntp/2-summary.md) |
| 인스턴스를 이미지 복제로 늘린 뒤 카운터가 실제보다 작음 | G-Counter 칸 주인(actor id) 중복 → max가 한쪽을 삼킴 | 인스턴스별 actor id | [24 §5](../24-conflict-resolution-and-crdt/2-summary.md) |
| 실시간 집계 < 다음 날 배치. WARN `Skipping record for expired window. ...`, `dropped-records-total` 증가 (Kafka Streams 4.1.0) | 윈도 끝 + grace 뒤 도착한 이벤트를 버림 | 이벤트 시간과 도착 시간 차이의 분포 | [30 §1](../30-batch-and-stream-processing/2-summary.md) |
| 리더 교체가 두 번 이어진 직후, 커밋됐다고 응답한 쓰기가 없음 | 직접 구현한 Raft가 이전 term 항목을 과반 복제만으로 커밋(논문 그림 8) | 커밋 규칙이 현재 term 항목만 세나 | [11 §3](../11-consensus-raft/2-summary.md) |
| 디스크를 잃은 노드를 같은 ID로 다시 넣은 뒤 커밋된 항목이 사라지거나 두 값이 선택됨 | 영속 상태(`currentTerm`·`votedFor`·로그, Paxos의 np·na·va)를 잃은 노드가 다시 투표 | 그 노드의 데이터 디렉터리 이력 | [02 §3](../02-system-and-failure-models/2-summary.md) · [11 §5](../11-consensus-raft/2-summary.md) · [28 §2](../28-consensus-paxos/2-summary.md) |
| 원천은 바뀌었는데 뷰의 일부 행만 몇 주째 옛 값, LAG 0 | 원천 이벤트 발행 실패(이중 쓰기) 또는 프로젝터가 실패 이벤트를 건너뜀 | 원천과 뷰 행 대조 | [20 §4](../20-data-ownership-and-cross-service-queries/2-summary.md) |
| 몇 주 뒤 "일부 주문이 처리 안 됐다" → DLT에 수천 건. Spring `DefaultErrorHandler` 기본이면 DLT도 없이 ERROR 로그 한 줄 | DLT를 종착지로 다룸, 유입 알림 없음 | DLT log-end-offset 추이, 에러 핸들러 설정 | [18 §5](../18-consumer-failure-handling/2-summary.md) |
| 첨부 많은 주문만 이벤트가 안 나감. `RecordTooLargeException: The message is N bytes when serialized which is larger than 1048576, which is the value of the max.request.size configuration.` (kafka-clients 4.1.0). 콘솔 도구 종료 코드는 0일 수 있음 | Claim Check 없이 큰 payload를 브로커에 직접 | 프로듀서 콜백의 예외를 확인하나 | [34 §2](../34-message-routing-and-transformation/2-summary.md) |

- 첫 갈림길은 **원천에 있나**다.
  - 원천(DB)에도 없으면 저장 계층의 유실(승격·LWW·Raft 버그)이다.
  - 원천엔 있고 하위에 없으면 전달 경로(이중 쓰기·커밋 순서·보존·윈도)다. 경로의 각 지점 건수를 차례로 센다.
- 유실의 상당수는 **오류 로그가 없다.** 건수 대사(원천 vs 결과)가 사실상 유일한 탐지 수단인 경우가 많다.

### 4. 순서 역전 — 결과가 원인보다 먼저

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `created_at` 정렬에서 배송이 주문보다 먼저. 에러 없음 | 노드마다 다른 벽시계로 순서를 정함 | 정렬 기준이 벽시계인가 | [05 §1](../05-logical-clocks/2-summary.md) |
| "주문 취소"가 "주문 생성"보다 먼저 처리됨. 같은 주문의 이벤트가 서로 다른 파티션에(`kafka-console-consumer --property print.partition=true`) | 키 없이 발행, 키를 주문 ID가 아닌 값으로 | 레코드 키와 파티션 | [17 §2](../17-queues-logs-and-delivery-semantics/2-summary.md) |
| 파티션 증설 직후 몇 분간 같은 키의 이벤트가 뒤섞임 | `murmur2(키) % N`에서 N이 바뀜 | 증설 전후 같은 키의 파티션 | [17 §3](../17-queues-logs-and-delivery-semantics/2-summary.md) |
| 소비자가 `OrderShipped`를 `OrderPaid`보다 먼저 받음, 키별 seq가 줄어듦 | outbox 릴레이 여럿이 같은 aggregate 행을 나눠 집음 | 릴레이 인스턴스 수, 메시지 키 = aggregate id인가 | [16 §2](../16-outbox-and-dual-write/2-summary.md) |
| 배송까지 끝난 주문이 `PAID`로 보임. 소비자를 늘린 뒤부터 | 경쟁 소비자가 같은 주문 이벤트를 병렬 처리 | 같은 키가 한 소비자로 가나(Sequential Convoy) | [19 §3](../19-message-types-channels-and-endpoints/2-summary.md) |
| 새로고침마다 댓글 수가 3 → 2 → 3 | 요청마다 다른 복제본 → monotonic reads 위반 | 로드밸런서의 복제본 선택 | [07 §3](../07-consistency-models/2-summary.md) |
| 재시작한 노드의 새 이벤트가 옛 이벤트보다 작은 시계 값 | 램포트 시계 값이 메모리에만 있어 0부터 | 재기동 직후 그 노드의 시계 값 | [05 §2](../05-logical-clocks/2-summary.md) |
| 분명 "주문 → 배송"인데 동시로 판정 | 논리 시계가 특정 경로(배치·웹훅·사람)에서 전파되지 않음 | 그 경로 메시지에 시계 헤더가 있나 | [05 §5](../05-logical-clocks/2-summary.md) |
| 두 트랜잭션의 커밋 타임스탬프가 실제 순서와 반대 | 시계 오차가 설정 상한(ε, max-offset)을 넘음 | 시계 오프셋 지표 vs 상한 | [26 §1](../26-hybrid-clocks-and-truetime/2-summary.md) |
| ID 정렬이 생성 순서와 다름(역순 ID) | Snowflake 시계 역행 | 역행 시각(NTP step·재시작) | [13 §1](../13-distributed-id-generation/2-summary.md) |
| 소비자가 30분 멈췄다 살아나자 취소된 예약 명령이 한꺼번에 실행 | 메시지에 유효 시한 없음. Kafka `retention`은 유효 시한이 아님 | 메시지 생성 시각과 처리 시각 차이 | [19 §4](../19-message-types-channels-and-endpoints/2-summary.md) |

- 첫 갈림길은 **순서의 근거가 무엇이었나**다.
  - 벽시계였다면 시계 문제(§7)다.
  - 브로커 순서였다면 "같은 키 → 같은 파티션 → 한 소비자"가 어디서 깨졌는지 본다.
  - 어느 쪽이든 소비자 쪽 방어(버전·seq 비교로 낡은 것 버리기)를 함께 둔다.

### 5. 리더 둘 — 두 소유자가 동시에 쓴다

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 정족수 없는 두 대짜리 주·대기에서 링크가 끊기자 양쪽이 쓰기를 받음, 복구 후 데이터가 갈라짐 | 분할을 설계에서 뺌("CA 시스템"), 하트비트만으로 선출 | 진행 측을 정하는 규칙(과반·증인)이 있나 | [10 §1](../10-leader-election/2-summary.md) · [08 §1](../08-cap-and-pacelc/2-summary.md) |
| etcd 안: 분할 직후 옛 리더 쪽 쓰기가 `context deadline exceeded` | 합의 그룹은 소수 쪽 쓰기를 커밋하지 않음. 옛 리더가 잠깐 자기를 리더로 앎 | `etcdctl endpoint status`의 IS LEADER·RAFT TERM | [10 §1](../10-leader-election/2-summary.md) |
| 리스가 끝난 옛 리더가 몇 초 뒤 깨어나 작업을 이어감. GC `Pause Full`·VM 정지 | 리스는 "보유자가 스스로 멈춘다"를 가정 | GC 로그, 리더 기한 < 저장소 TTL인가 | [10 §2](../10-leader-election/2-summary.md) · [02 §1](../02-system-and-failure-models/2-summary.md) |
| 정산 결과에 다른 서버 값이 덮여 있음. 락 로그상 둘 다 정상 획득 | GC 멈춤 중 락 만료, fencing 없음 | 자원이 토큰(revision·epoch)을 검사하나 | [12 §1](../12-coordination-and-fencing/2-summary.md) |
| 같은 락 키에 두 클라이언트의 `SET NX` 성공 로그, 서버 시각 변경 기록 또는 페일오버 직후 | Redis 키 만료는 벽시계, Redlock 시계 가정, 비동기 복제로 새 주 서버에 락 키 없음 | 서버 시각 변경·페일오버 시각 | [12 §2](../12-coordination-and-fencing/2-summary.md) |
| 같은 배치가 세 번 돎. 만료 뒤 늦게 깨어난 A의 `DEL`이 B의 락을 지움 | 해제가 소유자를 확인하지 않음 | 해제 코드가 고유값을 비교하나 | [12 §3](../12-coordination-and-fencing/2-summary.md) |
| ZooKeeper 세션 만료(`Expired`) 뒤에도 작업 로그가 이어짐, etcd라면 keepalive 실패 뒤 lease TTL -1 | 세션·lease 종료를 클라이언트가 늦게 앎 | 만료 이벤트 핸들러가 작업을 멈추나 | [12 §4](../12-coordination-and-fencing/2-summary.md) |
| 설정 서버가 새 테일을 정한 뒤에도 일부 클라이언트가 옛 값 | 끊긴 옛 테일이 계속 읽기에 답함(체인 복제의 split brain) | 테일 리스, 클라이언트가 세대 번호를 확인하나 | [27 §5](../27-chain-replication-and-striping/2-summary.md) |
| 옛 writer 쪽에서 `LedgerFenced` | 새 writer가 원장을 복구하며 펜싱함 — **펜싱이 일한 증거** | 그 엔트리 결과는 원장이 닫힌 뒤 읽어 확인 | [27 §4](../27-chain-replication-and-striping/2-summary.md) |
| 같은 term에 두 후보가 과반을 주장 | 영속 상태를 잃은 노드가 다시 투표 | 데이터 디렉터리 교체 이력 | [11 §5](../11-consensus-raft/2-summary.md) |
| 같은 번호의 서로 다른 accept 요청이 로그에 있음(Paxos) | 시계로 만든 제안 번호가 두 서버에서 같음 — 번호 유일성 가정이 깨짐 | 제안 번호 생성 방식(라운드, 서버 ID) | [28 §3](../28-consensus-paxos/2-summary.md) |
| 오토스케일 인스턴스가 기존 인스턴스와 같은 ID를 만듦 | worker ID 고정·무작위 → ID 공간의 두 소유자 | 중복 ID의 worker 필드와 호스트 | [13 §2](../13-distributed-id-generation/2-summary.md) |
| 다수결로 받았는데 옛 값·틀린 값 | crash 모델 프로토콜에 거짓말하는 노드 | 노드마다 같은 키 값 비교 | [31 §1](../31-byzantine-and-blockchain/2-summary.md) |

- 첫 갈림길은 **쓰기에 단조 증가 번호가 실려 있었나**다.
  - 실려 있고 자원이 검사했다면 낡은 쪽은 거절됐다(`LedgerFenced`처럼 오류로 보인다).
  - 없다면 두 쓰기가 모두 받아들여졌다. 겹친 시간 동안의 쓰기를 대사로 찾는다.
- 리더 둘은 합의 저장소 **안**과 **밖**을 구분한다. etcd 안의 옛 리더는 커밋하지 못한다. 그러나 etcd로 선출한 애플리케이션 리더는 펜싱 없이는 겹칠 수 있다.

### 6. 오래된 읽기 — 옛 값, 되살아난 값

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 저장 직후 목록에 없음, 새로고침하면 생김. 팔로워 읽기에서만 | 복제 지연 + 쓰기는 리더·읽기는 팔로워 | 지연 지표(Redis 오프셋 차이, PostgreSQL `replay_lag`) | [06 §4](../06-replication-strategies/2-summary.md) · [07 §1](../07-consistency-models/2-summary.md) |
| 쿠폰 한도 300장인데 1000장 넘게, 재고 음수. 에러 없음 | 남은 수량을 복제본·캐시에서 읽음, "읽기 → 판단 → 쓰기" 사이 끼어듦 | 판단이 쓰기 연산 하나 안에 있나(`INCR`, 조건부 `UPDATE`, etcd `Txn`) | [07 §2](../07-consistency-models/2-summary.md) |
| 이미지 업로드 후 큐 작업자가 읽으니 `not found`, 재시도하면 됨 | 저장소 복제와 큐 전달이 다른 경로 | 메시지에 버전이 실렸나 | [07 §4](../07-consistency-models/2-summary.md) |
| 같은 키를 읽을 때마다 새 값과 옛 값이 번갈아, 안 읽히는 키는 몇 주째 옛 값 | 리더리스에서 읽기 복구 누락, anti-entropy 안 돎 | R+W와 N, repair 마지막 실행 | [06 §2](../06-replication-strategies/2-summary.md) |
| R=W=2(N=3)인데 분할 중·직후 방금 쓴 값이 안 보임 | sloppy quorum: 대체 노드에 W를 채움 | hinted handoff·repair 완료 여부 | [09 §1](../09-quorums/2-summary.md) |
| 쓰기는 타임아웃 실패였는데 값이 보였다 사라졌다 함 | W 미만 복제본에만 쓰임, 되돌려지지 않음 | 테이블의 `read_repair` 설정 | [09 §3](../09-quorums/2-summary.md) |
| 지운 행·장바구니 상품이 몇 주 뒤 다시 보임 | 툼스톤 정리 뒤 오래 끊겼던 복제본이 옛 값을 퍼뜨림(Cassandra "zombie"), 합집합 병합 | 그 노드가 `gc_grace_seconds`(5.0 기본 864000초)보다 오래 끊겼나 | [09 §4](../09-quorums/2-summary.md) · [24 §3](../24-conflict-resolution-and-crdt/2-summary.md) |
| 방금 저장한 값을 다른 화면에서 조회하면 옛 값, 드물고 재현 어려움 | 시계 오차 상한 초과(외부 일관성 위반), VM 정지 뒤 낡은 시계 | 시계 오프셋, 앞쪽 점프 경고 | [26 §1](../26-hybrid-clocks-and-truetime/2-summary.md) · [26 §3](../26-hybrid-clocks-and-truetime/2-summary.md) |
| 일부 키만 TTL 내내 옛 값. 삭제 로그 뒤에 같은 키의 set 로그 | 늦은 set이 삭제를 덮어씀 | 키별 삭제·set 시각 | [32 §1](../32-distributed-cache-consistency/2-summary.md) |
| 특정 지역·클러스터에서만 옛 값이 안 사라짐, 배포·설정 변경 뒤부터 | 무효화 유실·잘못된 라우팅 | 무효화 표본 측정, 무효화 소비자 LAG | [32 §3](../32-distributed-cache-consistency/2-summary.md) |
| 주문 직후 목록에 없음. 프로젝터 그룹 LAG 증가 | 복제 뷰·프로젝션은 비동기 | 프로젝터 그룹 LAG, 뷰 최신 version | [20 §3](../20-data-ownership-and-cross-service-queries/2-summary.md) · [22 §5](../22-event-sourcing/2-summary.md) |
| 2f+1대에서 f+1 응답을 받았는데 옛 값 | 나쁜 노드 하나 + 뒤처진 정직 노드 하나 | 신뢰 모델(crash vs 비잔틴) | [31 §1](../31-byzantine-and-blockchain/2-summary.md) |
| ZooKeeper `sync` + 읽기 뒤에도 드물게 옛 값 | `sync` + 읽기는 엄밀한 선형화가 아님(Internals 문서) | 그 읽기가 정말 선형화를 요구하나 | [07 §1](../07-consistency-models/2-summary.md) |

- 첫 갈림길은 **어느 경로로 읽었나**다. 리더·복제본·캐시·뷰 중 어디였는지 요청 단위로 남긴다.
- "지운 것이 되살아났다"는 오래된 읽기의 특수형이다. 툼스톤은 그 삭제를 **복제본들이 다 받았다고 확인된 뒤에** 정리해야 되살아나지 않는다([24 §3](../24-conflict-resolution-and-crdt/2-summary.md)).

### 7. 블로킹·진행 없음 — 누가 무엇을 기다리나

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 특정 행을 갱신하는 요청만 멈춤, 읽기는 정상. `ERROR: canceling statement due to lock timeout`(PostgreSQL, `lock_timeout` 설정 시) | 2PC 참가자가 YES 뒤 코디네이터를 잃음(in-doubt) | `pg_prepared_xacts`(MySQL `XA RECOVER`), `pg_locks`의 pid 없는 락 | [14 §1](../14-two-phase-commit/2-summary.md) · [25 §4](../25-impossibility-results/2-summary.md) |
| 몇 주 뒤 테이블이 부풂, `VACUUM VERBOSE`에 `dead but not yet removable` | 방치된 prepared·XA 트랜잭션 | `pg_prepared_xacts`의 `prepared` 시각 | [14 §2](../14-two-phase-commit/2-summary.md) |
| JTA `HeuristicMixedException`·`HeuristicRollbackException`, 대사 불일치 | in-doubt 참가자를 사람이 한쪽만 결정 | 결정 로그와 다른 참가자 상태 | [14 §3](../14-two-phase-commit/2-summary.md) |
| 샤드 하나가 느려지자 여러 샤드 트랜잭션 전부 지연 | 2PC는 참가자 전원의 YES가 필요 | prepare 응답 지연 분포 | [14 §4](../14-two-phase-commit/2-summary.md) |
| 3대 중 2대가 죽자 쓰기 전부 실패. `etcdserver: request timed out`, `context deadline exceeded`, `etcd_server_has_leader 0` (etcd 3.6.5) | Raft는 과반 없이 결정하지 않음(설계된 동작) | `etcdctl endpoint status`(leader 0), 장애 도메인 | [11 §1](../11-consensus-raft/2-summary.md) · [25 §3](../25-impossibility-results/2-summary.md) |
| 특정 AZ의 앱만 etcd 호출이 몇 초 걸리다 실패, 그 노드 프로세스는 멀쩡 | 그 노드가 소수 쪽에 갇힘 | 그 노드의 피어 연결, 클라이언트 엔드포인트 목록 | [08 §2](../08-cap-and-pacelc/2-summary.md) |
| 노드 둘이 동시에 내려가자 쓰기 실패. `Not enough replicas available for query at consistency QUORUM (2 required but only 1 alive)` (Cassandra Java 드라이버 4.x `UnavailableException`) | 살아 있는 복제본 < 필요 정족수 | 노드 상태, 복제본의 장애 도메인 배치 | [09 §2](../09-quorums/2-summary.md) |
| 브로커 점검 중 프로듀서 오류·지연. `NotEnoughReplicasException`(메시지: `Messages are rejected since there are fewer in-sync replicas than required.`) 또는 그 전의 `TimeoutException` (Kafka 4.1.0) | ISR < `min.insync.replicas` | `kafka-topics --describe --under-min-isr-partitions` | [21 §2](../21-kafka-internals/2-summary.md) |
| Redis 쓰기가 `-NOREPLICAS Not enough good replicas to write.` (Redis 7.4 `src/server.c`) | `min-replicas-to-write`를 만족하는 복제본 부족 — 유실 창을 묶으려고 고른 거절 | `INFO replication`의 복제본 수·지연 | [08 §3](../08-cap-and-pacelc/2-summary.md) · [06 §3](../06-replication-strategies/2-summary.md) |
| 합의 요청이 끝나지 않고 재시도만, 제안 번호만 빠르게 커짐 | 결투하는 제안자(livelock) | 제안자가 몇인가, 리더가 있나 | [28 §1](../28-consensus-paxos/2-summary.md) |
| 분할 중 소수 쪽 Paxos 요청 전부 멈춤 | 과반 promise를 못 모음(의도된 동작) | 분할 여부 | [28 §5](../28-consensus-paxos/2-summary.md) |
| 확장 작업 중 클러스터가 쓰기를 못 함. `member list`에 `unstarted` 투표 멤버 | 투표 멤버 수가 늘어 과반 기준이 오름 | 멤버 목록, learner로 추가했나 | [11 §4](../11-consensus-raft/2-summary.md) |
| 결제는 됐는데 주문이 몇 시간째 "처리 중". 컨슈머 LAG 0, 오류 없음 | 코레오그래피: 커밋 후 발행 전 크래시 + 재전달을 "중복이니 무시" | 오래된 `PENDING` 질의, correlation ID 추적 | [23 §1](../23-orchestration-vs-choreography/2-summary.md) |
| 사가 표에 `COMPENSATING`이 오래 머묾, 같은 보상 요청이 계속 실패 | 보상 트랜잭션 실패(버그면 재시도로 안 풀림) | 보상 실패 로그의 원인 | [15 §1](../15-saga/2-summary.md) |
| 조정자 장애 동안 사가 중간 단계가 쌓임 | 오케스트레이터 단일 장애점 | 조정자 헬스 체크, 사가 표 단계별 건수 | [23 §2](../23-orchestration-vs-choreography/2-summary.md) |
| 한 파티션만 lag 몇 시간째 그대로, 같은 오프셋 같은 예외 반복 | poison 메시지 무한 재시도, `RecordDeserializationException` 미처리 | `kafka-consumer-groups --describe`의 고정된 CURRENT-OFFSET | [18 §3](../18-consumer-failure-handling/2-summary.md) |
| 처리량 0에 가깝고 그룹이 `PreparingRebalance`·`CompletingRebalance`를 오감 | 처리 시간 > `max.poll.interval.ms`, 롤링 배포마다 전체 리밸런스 | `kafka-consumer-groups --describe --state` | [18 §4](../18-consumer-failure-handling/2-summary.md) |
| 특정 키 처리가 멈추고 뒤 메시지가 쌓임, "다음 기대 순번"이 고정 | Resequencer가 유실·DLQ로 빠진 번호를 기다림 | 앞 단계 DLQ에 그 번호가 있나 | [34 §5](../34-message-routing-and-transformation/2-summary.md) |
| 집계 서비스 메모리가 조금씩 늘다 OOM, 재시작 뒤 일부 주문 "처리 중" | Aggregator 완료 조건이 "모두 도착" 하나뿐 | 버퍼 묶음 수·가장 오래된 묶음 나이 | [34 §1](../34-message-routing-and-transformation/2-summary.md) |
| 어떤 윈도 결과도 안 나옴, 입력은 정상 | 유휴 입력 하나가 워터마크(최솟값)를 붙잡음 | 연산자의 현재 이벤트 시간, 입력별 최근 이벤트 | [30 §3](../30-batch-and-stream-processing/2-summary.md) |
| 하류 하나가 멈추자 호출하는 서비스 전부 멈춤. 스레드 덤프에 같은 원격 호출 `WAITING`이 풀 크기만큼, 에러 로그는 조용 | 타임아웃 없는 호출 | 스레드 덤프 | [01 §1](../01-why-distributed-and-fallacies/2-summary.md) |
| low 큐 길이와 가장 오래된 메시지 나이가 계속 오름 | 엄격한 우선순위 → 기아 | 우선순위별 도착률 vs 처리 능력 | [19 §5](../19-message-types-channels-and-endpoints/2-summary.md) |
| outbox 미발행 건수가 줄지 않는데 토픽엔 같은 페이로드가 수백 번 | 배치 끝 표시 + 같은 지점에서 반복 크래시 | 릴레이 재시작 주기, 가장 오래된 미발행 나이 | [16 §4](../16-outbox-and-dual-write/2-summary.md) |
| 쓰기 p50이 몇 배로 뛰고 읽기(테일)는 멀쩡 | 체인 중간 노드가 느림 | 노드별 처리 시간 | [27 §1](../27-chain-replication-and-striping/2-summary.md) |
| 배포 직후 오래된 계좌 조회·프로젝션 재구축 실패. `UnrecognizedPropertyException: Unrecognized field "amount" ...`(Jackson) | 이벤트 스키마 변경, 업캐스터 없음 | 실패 이벤트의 `schema_ver` | [22 §1](../22-event-sourcing/2-summary.md) |
| 오래된 계좌일수록 느리고 몇 년 된 계좌는 타임아웃 | 스냅샷 없이 처음부터 재생 | 스트림 길이 분포 | [22 §2](../22-event-sourcing/2-summary.md) |
| 순간 부하에 ID 발급 p99가 튐 | ms당 순번(4096개) 고갈 → 다음 ms까지 대기 | 대기 횟수 지표 | [13 §4](../13-distributed-id-generation/2-summary.md) |
| 특정 데이터센터 쓰기 p50이 몇 ms 오름 | commit wait ≈ 2ε, ε 증가 | 시각 인프라 상태 | [26 §4](../26-hybrid-clocks-and-truetime/2-summary.md) |

- 첫 갈림길은 **설계된 멈춤인가, 고장인가**다.
  - 과반 상실·ISR 부족·정족수 미달은 "틀린 답 대신 멈춤"을 고른 결과다. 고칠 것은 노드 복구와 배치(장애 도메인)이고, 강제로 진행시키면 커밋된 데이터를 잃을 수 있다([11 §1](../11-consensus-raft/2-summary.md)).
  - in-doubt 2PC·poison·Resequencer·Aggregator는 "기다리는 대상이 영영 안 올 수 있는" 구조다. 기다림에 상한(타임아웃·DLQ·사람 결정 절차)이 있는지 본다.

### 8. 음수 시간·시계 증상

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 윤초·NTP step 순간 일부 요청 오류. Go면 `panic: invalid argument to Int63n`(`math/rand`), Java면 `IllegalArgumentException: bound must be positive`(JDK 21 `RandomSupport`) | 벽시계 차이로 경과 시간을 재서 음수가 됨 | 경과 시간 계산에 쓰인 시계(Go 1.9 이전 `time.Now()`, Java `currentTimeMillis`) | [04 §1](../04-physical-clocks-and-ntp/2-summary.md) · [36](../36-distributed-incidents/2-summary.md) |
| 특정 서버에서만 "토큰이 아직 유효하지 않음"(JWT `nbf`/`iat`), TLS `certificate is not yet valid`류 | 발급자 시계가 빠르거나 검증자 시계가 느림 | 두 노드의 NTP 오프셋 | [04 §2](../04-physical-clocks-and-ntp/2-summary.md) |
| 몇 주 뒤 로그 순서·토큰 만료·일별 경계가 어긋남. `node_timex_sync_status` 0, `node_timex_maxerror_seconds`가 16 s에서 멈춤 | NTP(UDP 123)가 막혀 시계가 천천히 벌어짐 | `timedatectl`의 동기 상태·마지막 동기 시각 | [04 §4](../04-physical-clocks-and-ntp/2-summary.md) |
| 사용자가 바꾼 값이 가끔 되돌아감, 빠른 노드를 거친 쓰기가 계속 이김 | LWW + 시계 어긋남 | 같은 키 값들의 타임스탬프와 실제 순서 | [04 §3](../04-physical-clocks-and-ntp/2-summary.md) · [24 §2](../24-conflict-resolution-and-crdt/2-summary.md) |
| `duplicate key` 또는 ID 역순, NTP 점프·VM 이동·재시작 직후 | Snowflake 시계 역행 + 재시작으로 `lastTs` 잃음 | 중복 ID 해독, 역행 감지 지표 | [13 §1](../13-distributed-id-generation/2-summary.md) |
| 타임스탬프가 실제보다 수 초~수 분 미래, 물리 성분은 멈추고 논리 성분만 오름 | 앞선 시계 하나가 HLC를 미래로 끌고 감 | 받은 타임스탬프 vs 자기 시계 + 상한 | [26 §2](../26-hybrid-clocks-and-truetime/2-summary.md) |
| 윤초 전후 하루 동안 노드 간 오프셋이 수백 ms, 노드 종료·재시작 증가 | 노드마다 다른 윤초 처리(smearing vs 계단) | 노드별 시각 소스 | [26 §5](../26-hybrid-clocks-and-truetime/2-summary.md) |
| 장애 뒤 같은 입력을 다시 돌렸더니 시간대별 집계가 다름 | 처리 시간(서버 벽시계) 윈도 | 윈도가 이벤트 시간인가 | [30 §4](../30-batch-and-stream-processing/2-summary.md) |

- 첫 갈림길은 **벽시계를 무엇에 썼나**다.
  - 경과 시간이면 단조 시계로 바꾼다.
  - 순서면 논리 시계·단일 리더 순번으로 바꾼다(§4).
  - 시각 자체가 필요하면(만료·`nbf`·로그) NTP 상태를 감시하고 허용 오차를 둔다.

### 9. 부하 증폭·폭주와 누적 — 일곱 칸 밖의 무리

**부하 증폭·폭주** — 고치려는 동작(재시도·재선출·무효화·재해시)이 부하를 더한다.

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 하류 요청률이 상류의 몇 배, 타임아웃률과 재시도율이 같이 오름 | 꼬리보다 짧은 타임아웃 + 재시도 | 재시도 예산·백오프·지터 유무 | [03 §3](../03-partial-failure-and-timeouts/2-summary.md) · [36](../36-distributed-incidents/2-summary.md) |
| 게이트웨이 504와 동시에 안쪽에서 수 초 뒤 "완료" 로그 | 타임아웃 계층 역전, 취소 미전파 | 계층별 타임아웃 값 | [03 §4](../03-partial-failure-and-timeouts/2-summary.md) |
| 주 DB가 잠깐 느렸을 뿐인데 자동 페일오버, 양쪽에만 있는 쓰기 | 탐지 문턱이 지연 꼬리보다 짧음, 또는 승격 대상 범위가 앱 한계를 넘음 | 페일오버 로그, 승격 범위 설정 | [03 §2](../03-partial-failure-and-timeouts/2-summary.md) · [36](../36-distributed-incidents/2-summary.md) |
| 장애 없는데 리더가 자주 바뀜. `etcd_server_leader_changes_seen_total` 증가, 로그 `became candidate`·`is starting a new election`·`lost leader` (etcd raft v3.6.0), 같은 시각 `etcd_disk_wal_fsync_duration_seconds` 꼬리 | 선거 타임아웃이 RTT·fsync 꼬리보다 짧음, 멤버마다 다른 값 | RTT·fsync 지연 측정 | [02 §2](../02-system-and-failure-models/2-summary.md) · [10 §3](../10-leader-election/2-summary.md) · [11 §2](../11-consensus-raft/2-summary.md) |
| 잠깐 고립됐던 노드가 돌아오자 리더가 바뀜, 그 노드 term이 더 큼 | PreVote 꺼짐 | `--pre-vote` 설정(etcd 3.6 기본 켜짐) | [10 §4](../10-leader-election/2-summary.md) |
| 락이 풀리는 순간 조정 서비스 요청이 치솟음 | 모든 대기자가 같은 키를 watch(herd) | watch 대상이 바로 앞 순번인가 | [12 §5](../12-coordination-and-fencing/2-summary.md) |
| 대량 무효화 직후 같은 SELECT 수백 개 동시, DB 커넥션 대기 | 무효화 폭풍(삭제 직후 miss가 모두 DB로) | miss율과 DB 동시 쿼리 수 | [32 §2](../32-distributed-cache-consistency/2-summary.md) |
| 캐시 서버 한 대 장애 뒤 다른 캐시 서버들이 차례로 과부하 | 재해시로 핫키가 이웃에 몰림 | 죽은 서버 키의 행방 | [32 §4](../32-distributed-cache-consistency/2-summary.md) |
| 쓰기 0건인데 Redis 무효화 메시지 급증, `tracking_total_keys`가 상한에 붙음 | 추적 테이블 상한 초과 → 가짜 무효화 | `INFO stats`, `tracking-table-max-keys` | [32 §5](../32-distributed-cache-consistency/2-summary.md) |
| 토픽 메시지 급증, 새 이벤트는 거의 없음 | 릴레이·대조 배치의 반복 재발행 | 회차별 재발행 건수가 같은가 | [29 §2](../29-outbox-vs-dispatch-log/2-summary.md) · [16 §4](../16-outbox-and-dual-write/2-summary.md) |
| 원천이 커지자 대조 배치가 주기 안에 안 끝나고 겹쳐 돎 | 원천 전량 스캔 | 배치 실행 시간 vs 주기 | [29 §4](../29-outbox-vs-dispatch-log/2-summary.md) |
| 분산 추적에 같은 하류 스팬이 수십~수백 개 | 루프 안 원격 호출, API Composition의 N+1 | 요청당 하류 호출 수 | [01 §3](../01-why-distributed-and-fallacies/2-summary.md) · [20 §2](../20-data-ownership-and-cross-service-queries/2-summary.md) |
| 같은 correlation ID로 A → B → C → A 이벤트 반복 | 코레오그래피 순환 | 구독 관계 카탈로그 | [23 §4](../23-orchestration-vs-choreography/2-summary.md) |
| 재처리 그룹 하나 때문에 다른 그룹·프로듀서 지연 증가, 브로커 디스크 읽기 I/O 급증 | 오래된 세그먼트 읽기가 페이지 캐시를 밀어냄 | 브로커 디스크 읽기, 그룹별 lag | [21 §5](../21-kafka-internals/2-summary.md) |
| 한 태스크만 수십 배 오래, 그 태스크만 스필 | 스큐된 키 | 태스크별 입력 건수 | [30 §2](../30-batch-and-stream-processing/2-summary.md) |
| bookie 몇 대만 디스크가 참 / 느린 bookie가 계속 밀림 | 스트라이프 배치 편중 / Qa < Qw로 느린 복제본을 안 기다림 | bookie별 저장량·큐 | [27 §3](../27-chain-replication-and-striping/2-summary.md) · [27 §2](../27-chain-replication-and-striping/2-summary.md) |
| BFT 클러스터 처리량 저하, VIEW-CHANGE 반복 | 나쁜 주가 일을 늦춤 | 뷰 변경 원인 | [31 §5](../31-byzantine-and-blockchain/2-summary.md) |

**누적·크기** — 지우지 못하는 것이 쌓인다.

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 메시지 메타데이터가 본문보다 커짐 | 벡터 시계 칸이 노드 id마다 늘어남 | 벡터 칸 수 추이 | [05 §3](../05-logical-clocks/2-summary.md) |
| 특정 키 읽기가 점점 느려지고 응답이 커짐, 형제 수십 개 | 버전 context 없이 쓰는 클라이언트, 정리 규칙 없는 OR-Set | 형제·툼스톤 수 | [24 §4](../24-conflict-resolution-and-crdt/2-summary.md) |
| 글자 수는 적은데 공동 편집 문서 상태가 수 MB / 아무도 안 쓰는데 문서가 큼 | 시퀀스 CRDT 툼스톤·이력 / 프레즌스를 문서에 기록 | 상태 크기 / 글자 수, 갱신 종류 | [33 §3](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md) · [33 §5](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md) |
| DB 디스크가 꾸준히 참. `pg_replication_slots`에 `active = f`, `retained_wal` 증가 | 버려진 CDC 슬롯이 WAL을 붙잡음 | 슬롯 목록·지연 | [16 §5](../16-outbox-and-dual-write/2-summary.md) |
| 보존 7일인데 Kafka 디스크가 안 줄어듦 | 미래 타임스탬프, 쓰기가 적어 세그먼트가 안 끊김 | 세그먼트 최대 타임스탬프, `segment.ms` | [21 §4](../21-kafka-internals/2-summary.md) |
| 프런트에서 받은 ID로 조회하면 "없는 주문", 끝 몇 자리만 다름 | 64비트 ID를 JS `Number`로 읽음(2^53−1 초과) | 서버 ID vs 브라우저 ID | [13 §3](../13-distributed-id-generation/2-summary.md) |
| 경쟁사가 ID로 가입 시점·발급 속도를 추정, 번호 공백을 "삭제"로 오해 | 시각을 앞에 둔 ID, 블록 할당 공백 | 외부 노출 ID 정책 | [13 §5](../13-distributed-id-generation/2-summary.md) |

### 10. 설계·구조에서 오는 증상

장애라기보다 **구조가 만든 반복 증상**이다. 같은 모양이 계속 나오면 이 표로 온다.

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 새 기능마다 주문 서비스 배포가 따라옴 | 이벤트 자리에 명령을 하나씩 보냄(결합 역전) | 받는 쪽 목록을 발행자가 쥐고 있나 | [19 §1](../19-message-types-channels-and-endpoints/2-summary.md) |
| 간헐적으로 다른 사용자의 결과가 보임 | Correlation ID 없이 순서로 응답을 짝지음 | 응답 채널 공유 여부 | [19 §2](../19-message-types-channels-and-endpoints/2-summary.md) |
| 다른 팀 배포 직후 내 API가 `ERROR: column c.full_name does not exist` | 공유 DB 직접 조회(분산 모놀리스) | 스택 트레이스가 가리키는 표의 소유 팀 | [20 §1](../20-data-ownership-and-cross-service-queries/2-summary.md) |
| 단계 인스턴스를 늘려도 처리량이 평평 | 필터 사이 공유 상태 | 공유 행 락·캐시 키 경합 | [34 §3](../34-message-routing-and-transformation/2-summary.md) |
| 필드 하나 추가에 몇 주 회의, `extra` 맵 증가 | 전사 Canonical 모델 강제 | 공용 스키마 변경 대기열 | [34 §4](../34-message-routing-and-transformation/2-summary.md) |
| 페일오버 뒤 장애가 끝났는데 계속 느림 | 리더가 원거리 리전에 남음(평시 L vs C) | DB 호출 지연 = 리전 간 왕복인가 | [08 §4](../08-cap-and-pacelc/2-summary.md) · [36](../36-distributed-incidents/2-summary.md) |
| 페일오버 뒤 일부 앱만 `Connection refused`·`No route to host`(옛 IP) | IP 고정, 이름 조회 캐시, 풀의 옛 연결 | 앱의 DNS 캐시·풀 최대 수명 | [01 §4](../01-why-distributed-and-fallacies/2-summary.md) |
| 역직렬화 실패·체크섬 불일치·설명 안 되는 값 | crash 모델 밖의 손상(비트 뒤집힘·펌웨어) | 애플리케이션 체크섬 | [02 §4](../02-system-and-failure-models/2-summary.md) |
| 모든 복제본이 같은 틀린 결과를 확정 | 같은 코드의 같은 버그(독립 장애 가정 붕괴) | 구현 다양성 | [31 §3](../31-byzantine-and-blockchain/2-summary.md) |
| 감사 로그 검사는 "정상"인데 외부 기록과 다름 | 해시 사슬을 한 곳에서 다시 계산 | 머리 해시를 다른 신뢰 영역과 비교 | [31 §4](../31-byzantine-and-blockchain/2-summary.md) |
| 확인했다고 본 결제가 사슬에서 사라짐 | 확정 깊이 부족, 계산량 과반 | 기다린 블록 수 z | [31 §2](../31-byzantine-and-blockchain/2-summary.md) |
| 동시 입력 뒤 사용자마다 다른 문서 / 병합 뒤 글자가 뒤섞임 / 커서가 튐 | OT 변환 함수 버그 / 끼워짐(interleaving) / 정수 커서 | 문서 해시 비교, 알고리즘 종류, 커서 저장 방식 | [33 §1](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md) · [33 §2](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md) · [33 §4](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md) |
| 재고 합계가 실제보다 많음, 취소가 몰린 날 더 벌어짐 | 동시 사가가 읽어 둔 옛 값으로 보상(lost update) | 보상이 절대값인가 상대 연산인가 | [15 §3](../15-saga/2-summary.md) |
| "주문 완료" 메일이 나간 뒤 결제 실패로 취소 | 보상 불가 작업을 피벗 앞에 둠 | 걸음 분류(보상 가능·피벗·재시도) | [15 §2](../15-saga/2-summary.md) |
| 잔액 음수 계좌, 이벤트 목록엔 이상 없음 | 기대 버전 검사 없이 이벤트 추가 | (stream_id, version) 유일 제약 | [22 §3](../22-event-sourcing/2-summary.md) |

### 11. 오독 사전 — 이렇게 읽으면 틀린다

증상을 잘못 읽으면 조사가 엉뚱한 곳에서 끝난다. 자주 나오는 오독과 반증 신호다.

| 오독 | 실제 | 반증 신호 | leaf |
|---|---|---|---|
| "타임아웃 = 실패" | 타임아웃은 **결과 모름**이다. 요청이 처리됐을 수 있다 | 상대 시스템에 그 요청의 흔적(결제 승인, 일부 복제본의 값) | [03 §1](../03-partial-failure-and-timeouts/2-summary.md) · [09 §3](../09-quorums/2-summary.md) · [28 §4](../28-consensus-paxos/2-summary.md) |
| "`CommitFailedException`·`LedgerFenced` = 처리 실패" | 커밋·확인이 거부됐을 뿐, 처리나 쓰기 일부는 이미 일어났을 수 있다 | 하류에 그 결과가 있나 | [18 §2](../18-consumer-failure-handling/2-summary.md) · [27 §4](../27-chain-replication-and-striping/2-summary.md) |
| "exactly-once를 켰으니 중복은 없다" | Kafka 설계 문서의 exactly-once는 Kafka → Kafka 경로(트랜잭션 프로듀서 + `read_committed`)의 보장이다. 외부 DB·메일은 그 밖 | 출력 토픽엔 없고 외부 저장소엔 있는 중복 | [17 §4](../17-queues-logs-and-delivery-semantics/2-summary.md) · [25 §1](../25-impossibility-results/2-summary.md) |
| "프로듀서 멱등성을 켰으니 중복 발행은 없다" | 한 프로듀서 세션 안의 재시도 중복만 막는다. 새 프로세스의 재발행(outbox 재시작)은 못 막는다 | 릴레이 재시작 직후 같은 이벤트 id | [16 §3](../16-outbox-and-dual-write/2-summary.md) |
| "LAG 0이니 다 처리됐다" | LAG은 커밋 위치와 로그 끝의 차이다. 처리 전 커밋·통째 커밋·"중복이니 무시"면 LAG 0으로 유실된다 | 원천 vs 결과 건수 대사 | [18 §1](../18-consumer-failure-handling/2-summary.md) · [23 §1](../23-orchestration-vs-choreography/2-summary.md) · [23 §3](../23-orchestration-vs-choreography/2-summary.md) |
| "`acks=all`이니 유실은 없다" | ISR이 리더 하나로 줄고 `min.insync.replicas=1`이면 리더 혼자 받고 성공한다 | 장애 전후 under-replicated, 토픽 `min.insync.replicas` | [21 §1](../21-kafka-internals/2-summary.md) |
| "R+W>N이니 항상 최신을 읽는다" | sloppy quorum은 숫자만 맞고 집합이 안 겹칠 수 있다. 실패한 쓰기는 일부 복제본에 남는다 | 분할·hinted handoff 시각과 겹침 | [09 §1](../09-quorums/2-summary.md) · [09 §3](../09-quorums/2-summary.md) |
| "락(리스)을 잡았으니 나 혼자다" | 멈춘 프로세스는 만료를 모른다. 자원 쪽 검사(fencing)가 없으면 겹친다 | GC·VM 정지와 만료 시각 겹침 | [12 §1](../12-coordination-and-fencing/2-summary.md) · [10 §2](../10-leader-election/2-summary.md) |
| "복제본이 같은 값으로 수렴했으니 잃은 것은 없다" | LWW는 한쪽을 버리고 수렴한다. 수렴과 보존은 다르다 | 감사 로그의 쓰기 수 vs 최종 상태 | [06 §1](../06-replication-strategies/2-summary.md) · [24 §1](../24-conflict-resolution-and-crdt/2-summary.md) |
| "쓰기 성공 = 어디서 읽어도 보인다" | 최종 일관성 저장소는 그것을 약속하지 않는다 | 복제본·캐시 경로에서만 재현 | [07 §1](../07-consistency-models/2-summary.md) · [07 §4](../07-consistency-models/2-summary.md) |
| "과반 상실로 쓰기가 거부되니 etcd 버그다" | 설계된 C 선택이다. 강제 진행은 커밋된 데이터를 잃을 수 있다 | `etcd_server_has_leader 0`과 노드 수 | [11 §1](../11-consensus-raft/2-summary.md) · [08 §2](../08-cap-and-pacelc/2-summary.md) · [25 §3](../25-impossibility-results/2-summary.md) |
| "리더 교체가 잦으니 네트워크 문제다" | 느린 디스크 fsync도 하트비트를 놓치게 한다(etcd Tuning 문서) | `etcd_disk_wal_fsync_duration_seconds` 꼬리 | [10 §3](../10-leader-election/2-summary.md) · [02 §2](../02-system-and-failure-models/2-summary.md) |
| "Kafka `retention`이 메시지 유효 기간이다" | 보존은 저장 기간이다. 업무상 만료는 메시지의 `expiresAt`으로 따로 둔다 | 복구 뒤 낡은 명령 일괄 실행 | [19 §4](../19-message-types-channels-and-endpoints/2-summary.md) · [21 §3](../21-kafka-internals/2-summary.md) |
| "멱등 키가 있으니 중복은 없다" | 키 생성 위치·원자적 삽입·같은 트랜잭션·보존 기간이 모두 맞아야 한다 | 같은 키 두 줄 | [03 §5](../03-partial-failure-and-timeouts/2-summary.md) |
| "램포트 값이 크면 나중에 쓴 것이다" | 램포트는 →의 한 방향만 보장한다. 동시 쓰기에도 값 차이가 생긴다 | 벡터 비교 결과 "동시" | [05 §4](../05-logical-clocks/2-summary.md) |
| "`time.Now()` 두 번의 차이 = 경과 시간" | 벽시계는 뒤로 갈 수 있다(윤초·NTP step). Go 1.9부터는 `Time`에 단조 시계가 함께 담겨 `Sub`가 그것을 쓴다 | 음수 duration, 윤초·NTP 변경 시각 | [04 §1](../04-physical-clocks-and-ntp/2-summary.md) · [36](../36-distributed-incidents/2-summary.md) |
| "2PC를 쓰면 가용성이 높아진다" | 2PC는 참가자 전원의 YES가 필요하다. 가장 느린 참가자가 전체를 정한다 | prepare 지연 | [14 §4](../14-two-phase-commit/2-summary.md) · [14 §1](../14-two-phase-commit/2-summary.md) |
| "에러 로그가 없으니 정상이다" | LWW·처리 전 커밋·늦은 set·윈도 밖 이벤트(WARN만)는 ERROR를 남기지 않는다 | 대사·표본 비교 | §3 · §6 |
| "트리거를 없앴으니 끝났다" | 지속 효과(재시도·캐시 비움 등)가 남으면 트리거가 사라져도 회복하지 않는다(metastable) | 트리거 제거 뒤에도 높은 지연·타임아웃률 | [36](../36-distributed-incidents/2-summary.md) |

## 쓰이는 자료구조·알고리즘

**역색인과 결정 트리** — 이 노트 자체가 자료구조다.

```text
  역색인(inverted index)              결정 트리(첫 갈림길)
  ────────────────────────            ───────────────────────────────
  "중복"   -> [03§1, 03§5, 17§1, ...]   중복?  ── ID 같음 ── 재시도·재전달 → 처리 멱등
  "유실"   -> [06§3, 21§1, 16§1, ...]          └ ID 다름 ── 두 소유자 → 펜싱
  "리더 둘" -> [10§1, 12§1, 27§5, ...]   유실?  ── 원천에 없음 ── 저장 계층
                                              └ 원천에 있음 ── 전달 경로 건수 세기
```

- 색인의 칸(posting list)은 leaf 장애 절이다. 같은 절이 여러 증상 칸에 들어간다(예: [02 §1](../02-system-and-failure-models/2-summary.md)은 중복과 리더 둘 모두).

**적은 수의 처방이 많은 증상을 덮는다.** 아래 표는 색인을 거꾸로 접은 것이다.

| 구조 | 막는 증상 | 대표 leaf |
|---|---|---|
| 단조 증가 번호(term·epoch·fencing token·offset·version·seq) + 받는 쪽 비교 | 리더 둘, 순서 역전, 낡은 이벤트 덮어쓰기, 옛 소유자 쓰기 | [10](../10-leader-election/2-summary.md) · [12](../12-coordination-and-fencing/2-summary.md) · [17](../17-queues-logs-and-delivery-semantics/2-summary.md) · [27](../27-chain-replication-and-striping/2-summary.md) |
| 멱등 키 집합(유일 제약 + 처리와 같은 트랜잭션) | 중복 결제, 재전달 중복, outbox·대조 배치 중복 | [03](../03-partial-failure-and-timeouts/2-summary.md) · [17](../17-queues-logs-and-delivery-semantics/2-summary.md) · [25](../25-impossibility-results/2-summary.md) |
| 정족수 교집합(과반, R+W>N, ISR ≥ min.insync) | 리더 둘, 확인된 쓰기 유실, 오래된 읽기 | [09](../09-quorums/2-summary.md) · [11](../11-consensus-raft/2-summary.md) · [21](../21-kafka-internals/2-summary.md) |
| 추가 전용 로그를 원천으로(outbox·CDC·WAL) | 이중 쓰기 유실, 무효화 유실, 뷰 영구 어긋남 | [16](../16-outbox-and-dual-write/2-summary.md) · [32](../32-distributed-cache-consistency/2-summary.md) · [20](../20-data-ownership-and-cross-service-queries/2-summary.md) |
| 단조 시계·논리 시계(램포트·벡터·HLC) | 음수 duration, 인과 역전, 동시 쓰기 유실 감지 | [04](../04-physical-clocks-and-ntp/2-summary.md) · [05](../05-logical-clocks/2-summary.md) · [26](../26-hybrid-clocks-and-truetime/2-summary.md) |
| 병합 가능한 자료형(CRDT, 버전 벡터 + 형제) | LWW 유실, 다중 리더 충돌 | [24](../24-conflict-resolution-and-crdt/2-summary.md) · [33](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md) |
| 기다림의 상한(타임아웃·DLQ·완료 조건 둘·사람 결정 절차) | 블로킹·진행 없음 | [01](../01-why-distributed-and-fallacies/2-summary.md) · [14](../14-two-phase-commit/2-summary.md) · [18](../18-consumer-failure-handling/2-summary.md) · [34](../34-message-routing-and-transformation/2-summary.md) |
| 재시도 예산·지수 백오프·지터 | 부하 증폭, metastable | [03](../03-partial-failure-and-timeouts/2-summary.md) · [36](../36-distributed-incidents/2-summary.md) |

- 표가 짧다는 것이 요점이다. 증상은 많지만 원인은 몇 개의 가정 위반으로 모인다. "시간은 앞으로만 간다", "응답이 없으면 죽었다", "한 번 보내면 한 번 도착한다", "쓰면 바로 보인다"가 그 가정들이다.

## 적용 — 풀어나가는 법

### 1. 모양으로 1차 분류한다

```text
  1. 원문·모양·시각을 모은다 (§0)
  2. 일곱 칸 중 어디인가?  중복 / 유실 / 순서 / 리더 둘 / 옛 값 / 멈춤 / 시계
     둘 이상이면 시간순으로 놓는다 (예: 분할 → 리더 둘 → 유실)
  3. 그 칸의 "첫 갈림길"을 확인한다 (각 표 아래 글)
  4. 표에서 행을 고르고 첫 진단을 실행한다
  5. leaf 장애 절로 가서 대처를 읽는다
  6. 같은 증상이 조용히 다시 생길 수 있으면 지표·대사를 단다 (아래 4)
```

### 2. 첫 진단 세트 — 제품별

etcd 3.6.5 (아래 첫 명령은 이 작업의 공용 3노드에서 실행해 표의 열을 확인했다):

```bash
# 리더·term·raft index를 한 표로. IS LEADER가 아무도 true가 아니면 과반 상실 의심
etcdctl --endpoints=$EPS endpoint status -w table
etcdctl --endpoints=$EPS endpoint health
etcdctl --endpoints=$EPS member list -w table      # unstarted·learner 확인
# 지표: etcd_server_has_leader, etcd_server_leader_changes_seen_total,
#       etcd_disk_wal_fsync_duration_seconds
```

Kafka 4.1.0 (`/opt/kafka/bin/` 도구):

```bash
kafka-topics.sh --bootstrap-server $BS --describe --under-replicated-partitions   # ISR 축소
kafka-topics.sh --bootstrap-server $BS --describe --under-min-isr-partitions      # 쓰기 거부 구간
kafka-consumer-groups.sh --bootstrap-server $BS --describe --group $G            # 파티션별 CURRENT-OFFSET·LAG
kafka-consumer-groups.sh --bootstrap-server $BS --describe --group $G --state    # 리밸런스 상태
kafka-console-consumer.sh --bootstrap-server $BS --topic $T --from-beginning \
  --property print.key=true --property print.partition=true                     # 키 → 파티션
```

- 두 `kafka-topics` 명령은 문제가 없으면 아무것도 출력하지 않는다(이 작업의 공용 Kafka 4.1.0 단일 노드에서 실행해 확인).

Redis 7.4 / PostgreSQL 17 / 시계:

```bash
redis-cli INFO replication          # role, connected_slaves, 복제본별 offset·lag
redis-cli INFO stats                # tracking_total_keys 등
psql -c "SELECT gid, prepared, owner, database FROM pg_prepared_xacts ORDER BY prepared"
psql -c "SELECT slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) FROM pg_replication_slots"
timedatectl                         # System clock synchronized: yes/no
chronyc tracking                    # chrony를 쓰는 호스트라면
```

### 3. 대사 쿼리 — 조용한 증상을 숫자로

유실·중복·순서 역전은 에러가 없으니 **원천과 결과를 맞대어** 찾는다.\
아래는 PostgreSQL 17 문법이다. `orders`(원천)와 `processed_event`(소비자가 처리한 이벤트 기록)가 있다고 하자(예시 스키마).

```sql
-- (1) 유실: 원천엔 있는데 처리 기록이 없는 주문
SELECT o.id FROM orders o
LEFT JOIN processed_event p ON p.event_id = 'order-' || o.id
WHERE p.event_id IS NULL AND o.created_at < now() - interval '10 minutes';

-- (2) 중복: 같은 이벤트 ID가 두 번 이상 처리됨 (유일 제약이 없을 때)
SELECT event_id, count(*) FROM processed_event GROUP BY event_id HAVING count(*) > 1;

-- (3) 순서 역전: 같은 주문에서 처리 순서대로 볼 때 seq가 줄어든 곳
SELECT order_id, seq, prev_seq FROM (
  SELECT order_id, seq, lag(seq) OVER (PARTITION BY order_id ORDER BY processed_at, id) AS prev_seq
  FROM processed_event) t
WHERE seq < prev_seq;
```

- (1)의 10분은 정상 지연을 빼는 여유다(예시). 실제 값은 전달 지연 p99를 재서 고른다.
- (1)은 이벤트 ID 규칙(`order-<id>`)을 안다고 가정한다. 규칙이 없으면 원천 키를 이벤트에 함께 싣는다.
- 일회용 PostgreSQL 17.11 컨테이너에서 예시 데이터(주문 4건, 처리 기록 6줄)로 세 쿼리가 각각 유실 1건·중복 1건·역전 1건을 찾는 것을 확인했다(관련 주제·근거의 "실행 확인").

### 4. 조용한 증상을 지표로 바꾼다 — 소비자 쪽 가드

에러가 없는 증상은 **소비자가 스스로 세면** 지표가 된다. 처리를 막지 않고 세기만 하는 가드다(Java 21).

```java
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/** 키별 마지막 버전을 기억해 중복·역전을 센다. 메모리 맵은 예시 — 운영에서는 처리와 같은 트랜잭션의 표에 둔다. */
final class SymptomGuard {
    enum Verdict { APPLY, DUPLICATE, STALE }

    private final ConcurrentHashMap<String, Long> lastVersion = new ConcurrentHashMap<>();
    final LongAdder duplicates = new LongAdder();   // 같은 버전 재도착 → at-least-once 재전달
    final LongAdder stale = new LongAdder();        // 더 작은 버전 도착 → 순서 역전

    Verdict check(String key, long version) {
        Verdict[] out = {Verdict.APPLY};
        lastVersion.compute(key, (k, cur) -> {
            if (cur == null || version > cur) return version;           // 새 것: 적용
            out[0] = (version == cur) ? Verdict.DUPLICATE : Verdict.STALE;
            return cur;                                                  // 기존 값 유지
        });
        if (out[0] == Verdict.DUPLICATE) duplicates.increment();
        if (out[0] == Verdict.STALE) stale.increment();
        return out[0];
    }

    public static void main(String[] args) {
        SymptomGuard g = new SymptomGuard();
        long[] arrivals = {1, 2, 2, 4, 3, 5};       // 2는 재전달, 3은 4 뒤에 늦게 옴
        for (long v : arrivals) System.out.println("order-7 v" + v + " -> " + g.check("order-7", v));
        System.out.println("duplicates=" + g.duplicates.sum() + " stale=" + g.stale.sum());
    }
}
```

(실행 확인, eclipse-temurin:21-jdk 컨테이너, 2026-10-01)

```text
order-7 v1 -> APPLY
order-7 v2 -> APPLY
order-7 v2 -> DUPLICATE
order-7 v4 -> APPLY
order-7 v3 -> STALE
order-7 v5 -> APPLY
duplicates=1 stale=1
```

- v2가 두 번 온 것은 재전달(중복)로, 4 뒤에 온 3은 순서 역전으로 세었다. 처리는 막지 않았으므로 지표가 오르는 것만으로 §2·§4의 조용한 증상을 알아챈다.
- 같은 버전 재도착(DUPLICATE)과 더 작은 버전(STALE)을 나눠 세는 이유: 처방이 다르다. 앞은 처리 멱등, 뒤는 키 → 파티션 → 소비자 경로 점검이다.
- 메모리 맵은 프로세스가 죽으면 사라지고, 파티션이 다른 소비자로 넘어가면 그쪽은 모른다. 운영에서는 처리와 같은 트랜잭션의 표(키, 마지막 버전)로 옮긴다([17 §2](../17-queues-logs-and-delivery-semantics/2-summary.md)의 `WHERE version < :v`).

### 5. leaf로 간다

- 표의 leaf 링크는 그 노트의 「장애 시나리오와 대처」 번호다. 대처·재현 실험·진단 명령은 그쪽이 정본이다.
- 여러 칸에 걸친 실제 사건은 [36](../36-distributed-incidents/2-summary.md)에서 사건 단위로 본다. DB 쪽 증상(SQLSTATE·풀 고갈 등)은 [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md)로 간다.

## 장애 시나리오와 대처

이 노트의 장애는 **색인을 잘못 쓰는 것**이다. 증상을 엉뚱한 칸에 넣거나, 첫 진단을 건너뛰고 대처로 가면 생긴다.

### 1. 중복 결제 조사를 "타임아웃 났으니 실패였다"로 닫는다

- **현상**: 고객은 두 번 청구됐다고 하는데, 내부 로그는 첫 시도가 `HttpTimeoutException`으로 "실패"라서 중복이 아니라고 결론 낸다.
- **보이는 형태**: 결제사 정산 파일엔 승인 두 건. 내부엔 실패 1 + 성공 1.
- **원인**: 타임아웃을 실패로 읽었다(§11 첫 줄). 첫 요청은 결제사에서 처리됐다.
- **대처**: 타임아웃 건은 `UNKNOWN`으로 두고 상대 시스템 조회로 확정한다. 재시도엔 같은 멱등 키. 이미 난 중복은 대사로 찾아 환불한다([03 §1](../03-partial-failure-and-timeouts/2-summary.md)).

### 2. "exactly-once 설정 확인"으로 중복 조사를 닫는다

- **현상**: DB에 같은 행이 두 번 들어갔다. 조사자는 `processing.guarantee=exactly_once_v2`가 켜져 있는 것을 보고 "Kafka 쪽은 아니다"라며 다른 곳을 뒤진다.
- **보이는 형태**: 출력 토픽엔 중복이 없다. DB에만 있다.
- **원인**: 보장의 범위를 오독했다. 트랜잭션은 Kafka 안의 쓰기와 오프셋만 묶는다.
- **대처**: 부작용이 트랜잭션 밖인지부터 본다. DB 쓰기를 멱등하게 하거나 오프셋을 DB에 같은 트랜잭션으로 저장한다([17 §4](../17-queues-logs-and-delivery-semantics/2-summary.md)).

### 3. LAG 0을 보고 유실 조사를 닫는다

- **현상**: "주문이 처리 안 됐다"는 문의에, 운영자가 컨슈머 그룹 LAG 0을 보여 주며 "다 소비했다"고 답한다.
- **보이는 형태**: LAG 0, 오류 없음. 원천엔 `PENDING`이 수십 건.
- **원인**: LAG은 커밋 위치일 뿐이다. 처리 전 커밋, 인자 없는 `commitSync()`, "중복이니 무시"가 모두 LAG 0으로 유실을 만든다.
- **대처**: 원천과 결과의 건수 대사를 먼저 돌린다(적용 3). 그다음 커밋 위치 코드를 본다([18 §1](../18-consumer-failure-handling/2-summary.md) · [23 §1](../23-orchestration-vs-choreography/2-summary.md) · [23 §3](../23-orchestration-vs-choreography/2-summary.md)).

### 4. 리더 교체 급증을 선거 타임아웃만 키워 덮는다

- **현상**: `leader_changes_seen_total`이 오르자 선거 타임아웃을 크게 늘렸다. 교체는 줄었지만, 진짜 리더 장애 때 재선출이 오래 걸려 쓰기가 오래 멈춘다.
- **보이는 형태**: 교체 횟수는 줄었는데 `etcd_disk_wal_fsync_duration_seconds` 꼬리는 그대로 길다.
- **원인**: 원인(디스크 fsync 지연)을 보지 않고 증상(교체)만 눌렀다.
- **대처**: RTT와 fsync 꼬리를 먼저 잰다. 디스크를 분리·우선순위 조정하고, 타임아웃은 etcd Tuning 기준(RTT의 10배 이상)으로 모든 멤버에 같게 둔다([10 §3](../10-leader-election/2-summary.md) · [02 §2](../02-system-and-failure-models/2-summary.md)).

### 5. 과반 상실을 "etcd가 고장"으로 읽고 한 대로 강제 진행한다

- **현상**: 3대 중 2대가 내려가 쓰기가 실패하자, 남은 한 대를 새 클러스터로 강제로 띄웠다. 나중에 다른 노드를 살렸더니 일부 키 값이 서로 다르다.
- **보이는 형태**: 처음엔 `etcdserver: request timed out`·`etcd_server_has_leader 0`. 강제 진행 뒤엔 노드 간 revision·값 불일치.
- **원인**: 설계된 멈춤(C 선택)을 고장으로 읽었다. 남은 한 대가 마지막 커밋을 모두 갖고 있다는 보장이 없다.
- **대처**: 먼저 내려간 노드를 살려 과반을 되찾는다. 과반을 영구히 잃었으면 etcd 재해 복구 절차(스냅샷 복원)를 따른다([11 §1](../11-consensus-raft/2-summary.md)).

### 6. 오래된 값을 캐시 TTL 줄이기로만 대응한다

- **현상**: "저장했는데 옛 값이 보인다"는 문의에 캐시 TTL을 줄였다. 증상이 그대로이거나 DB 부하만 늘었다.
- **보이는 형태**: TTL을 줄여도 팔로워 읽기 경로에서 계속 재현된다. 또는 일부 키만 TTL 끝까지 옛 값이다.
- **원인**: 오래된 읽기의 경로를 가르지 않았다. 복제 지연([06 §4](../06-replication-strategies/2-summary.md)), 늦은 set 고착([32 §1](../32-distributed-cache-consistency/2-summary.md)), 프로젝션 지연([20 §3](../20-data-ownership-and-cross-service-queries/2-summary.md))은 대처가 다르다.
- **대처**: 요청마다 읽은 경로(리더·복제본·캐시·뷰)를 남기고 §6의 첫 갈림길부터 간다.

## 핵심 문장

- 분산 증상은 일곱 칸(중복·유실·순서 역전·리더 둘·오래된 읽기·블로킹·음수 시간)과 두 무리(부하 증폭·누적)로 거의 다 분류된다. 각 칸에는 원인을 가르는 첫 갈림길이 하나씩 있다.
- 증상을 받으면 원문·모양·시각을 먼저 모은다. 같은 사건이 서버·클라이언트 라이브러리·애플리케이션에서 다른 말로 보인다.
- 분산 증상의 상당수는 에러가 없다. LWW·처리 전 커밋·늦은 set·보존 삭제는 건수 대사와 표본 비교로만 드러나는 경우가 많다.
- 타임아웃은 실패가 아니라 "모름"이고, exactly-once는 범위가 있는 보장이며, LAG 0은 처리 완료가 아니다.
- 멈춤 중에는 설계된 것(과반 상실·ISR 부족)이 있다. 그것을 강제로 풀면 멈춤이 데이터 손실로 바뀔 수 있다.
- 증상은 많지만 처방은 적다. 단조 증가 번호, 멱등 키, 정족수 교집합, 로그 원천, 단조·논리 시계, 기다림의 상한이 대부분을 덮는다.

## 관련 주제·근거

- 선행(이 영역 전체 — 색인의 원천)
  - 모델·시간: [01](../01-why-distributed-and-fallacies/2-summary.md) · [02](../02-system-and-failure-models/2-summary.md) · [03](../03-partial-failure-and-timeouts/2-summary.md) · [25](../25-impossibility-results/2-summary.md) · [04](../04-physical-clocks-and-ntp/2-summary.md) · [05](../05-logical-clocks/2-summary.md) · [26](../26-hybrid-clocks-and-truetime/2-summary.md)
  - 복제·일관성: [06](../06-replication-strategies/2-summary.md) · [07](../07-consistency-models/2-summary.md) · [08](../08-cap-and-pacelc/2-summary.md) · [09](../09-quorums/2-summary.md) · [24](../24-conflict-resolution-and-crdt/2-summary.md) · [27](../27-chain-replication-and-striping/2-summary.md) · [33](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md)
  - 합의·조정: [10](../10-leader-election/2-summary.md) · [11](../11-consensus-raft/2-summary.md) · [12](../12-coordination-and-fencing/2-summary.md) · [13](../13-distributed-id-generation/2-summary.md) · [28](../28-consensus-paxos/2-summary.md) · [31](../31-byzantine-and-blockchain/2-summary.md)
  - 분산 트랜잭션·데이터 흐름: [14](../14-two-phase-commit/2-summary.md) · [15](../15-saga/2-summary.md) · [16](../16-outbox-and-dual-write/2-summary.md) · [17](../17-queues-logs-and-delivery-semantics/2-summary.md) · [18](../18-consumer-failure-handling/2-summary.md) · [21](../21-kafka-internals/2-summary.md) · [22](../22-event-sourcing/2-summary.md) · [23](../23-orchestration-vs-choreography/2-summary.md) · [29](../29-outbox-vs-dispatch-log/2-summary.md) · [30](../30-batch-and-stream-processing/2-summary.md) · [32](../32-distributed-cache-consistency/2-summary.md)
  - 통합·메시징: [19](../19-message-types-channels-and-endpoints/2-summary.md) · [20](../20-data-ownership-and-cross-service-queries/2-summary.md) · [34](../34-message-routing-and-transformation/2-summary.md)
- 후속: [36](../36-distributed-incidents/2-summary.md) — 여러 칸에 걸친 실사건(GitHub 2018, Cloudflare 2017, AWS EBS 2011, metastable failure)
- 다른 영역
  - [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md) — DB 증상 사전(SQLSTATE·풀·ORM). 이 노트와 같은 형식
  - [database/57-db-incidents](../../database/57-db-incidents/2-summary.md) · [os/38-os-incidents](../../os/38-os-incidents/2-summary.md)
  - [ops-patterns/failure-modes](../../ops-patterns/failure-modes/2-summary.md) — 실패 카탈로그 F-01~25
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) · [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)
- 메시지 원문 출처(이 노트가 직접 대조한 것 — 각 leaf가 실험 출력으로 확인한 문구는 그 leaf가 출처)
  - etcd v3.6.5 `server/etcdserver/errors/errors.go`(`etcdserver: request timed out`, `etcdserver: no leader`, `etcdserver: leader changed`), `api/v3rpc/rpctypes/error.go`(gRPC `Unavailable` 코드) <https://github.com/etcd-io/etcd/tree/v3.6.5>
  - etcd raft v3.6.0(etcd 3.6.5 `server/go.mod`의 판) `raft.go`(`%x became candidate at term %d`, `%x is starting a new election at term %d`), `node.go`(`raft.node: %x lost leader %x at term %d`) <https://github.com/etcd-io/raft/tree/v3.6.0>
  - Kafka 4.1.0 `clients/.../protocol/Errors.java`(`NOT_ENOUGH_REPLICAS`), `clients/.../consumer/internals/ConsumerCoordinator.java`·`AbstractCoordinator.java`(`CommitFailedException` 문구, `consumer poll timeout has expired`), `clients/.../producer/KafkaProducer.java`(`RecordTooLargeException` 문구), `storage/.../log/UnifiedLog.java`(`Deleting segment ... due to log retention time ...`, `Incremented log start offset to ... due to ...`, `Truncating to offset`), `core/.../server/AbstractFetcherThread.scala`(`Truncating partition ... with ...`), `streams/.../AbstractKStreamTimeWindowAggregateProcessor.java`(`Skipping record for expired window.`) <https://github.com/apache/kafka/tree/4.1.0>
  - Cassandra Java 드라이버 4.x `UnavailableException.java` <https://github.com/apache/cassandra-java-driver>
  - PostgreSQL REL_17_STABLE `src/backend/tcop/postgres.c`(`canceling statement due to lock timeout`), `src/backend/access/nbtree/nbtinsert.c`(`duplicate key value violates unique constraint`)
  - Redis 7.4 `src/server.c`(`-NOREPLICAS Not enough good replicas to write.`)
  - Go `src/math/rand/rand.go`(`invalid argument to Int63n`), `src/context/context.go`(`context deadline exceeded`), Go 1.9 릴리스 노트 "Transparent Monotonic Time support" <https://go.dev/doc/go1.9>
  - OpenJDK 21 `jdk/internal/util/random/RandomSupport.java`(`bound must be positive`)
- 실행 확인(실험 의무는 면제된 종합 편 — 적용 절의 명령·코드가 실제로 도는지 확인한 것)
  - etcd 3.6.5 공용 3노드: `etcdctl endpoint status -w table` 열 이름(IS LEADER, RAFT TERM, RAFT INDEX, ERRORS) 확인
  - Kafka 4.1.0 공용 단일 노드: `--under-replicated-partitions`·`--under-min-isr-partitions`가 정상 상태에서 빈 출력
  - 일회용 PostgreSQL 17 컨테이너: 적용 3의 대사 쿼리 셋
  - eclipse-temurin:21-jdk: 적용 4의 `SymptomGuard`
