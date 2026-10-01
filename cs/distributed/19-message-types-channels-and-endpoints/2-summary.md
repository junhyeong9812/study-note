# distributed/19-message-types-channels-and-endpoints — 메시지 종류·채널·소비 쪽 확장 — 정리 (힌트)

## 해결하는 문제

큐나 토픽을 쓰기 시작하면 "메시지를 보낸다"는 말 하나로는 설계가 정해지지 않는다.

```text
  같은 "주문 메시지"라도 묻는 것이 다르다
  ① 무엇을 담나?   "결제해라"(명령) / "주문됐다"(사실) / 주문서 자체(데이터)
  ② 누가 받나?     딱 한 곳 / 관심 있는 모두
  ③ 응답은?       어디로 보내고, 어느 요청의 응답인지 어떻게 아나
  ④ 언제까지 유효? 5초 뒤에 도착한 "재고 잡아라"를 실행해도 되나
  ⑤ 소비는?       소비자를 늘리면 순서는? 급한 메시지는?
```

이 다섯 질문에 이름을 붙인 것이 Hohpe–Woolf 『Enterprise Integration Patterns』(EIP, 2003)의 메시지 구성(Message Construction)·채널(Messaging Channels)·엔드포인트(Messaging Endpoints) 패턴이다.

쉬운 예: 회사 우편함이다.
- "이 서류에 서명해 주세요"는 **지시**다. 받는 사람이 한 명이고, 보낸 사람은 결과를 기대한다.
- "3층 회의실이 5층으로 옮겼습니다"는 **공지**다. 보는 사람이 누구든 상관없다.
- 우편물에는 "회신은 총무팀으로", "○월 ○일까지 유효" 같은 겉봉 정보가 붙는다.
- 우편물이 몰리면 담당자를 늘린다. 그런데 같은 건의 1차·2차 서류를 서로 다른 담당자가 처리하면 순서가 꼬인다.

똑같은 구조다.\
메시지 시스템에서도 메시지 종류·겉봉(헤더)·채널 모양·소비자 배치가 각각 다른 장애를 막는다.

실무 예:
- 주문 서비스가 "결제하라", "포인트 적립하라", "메일 보내라"를 하나씩 보낸다. 쿠폰 서비스가 생기자 주문 서비스를 또 고쳐야 한다.
- 응답 큐 하나를 여러 요청이 공유한다. 응답 순서가 섞여 A 고객의 조회 결과가 B 고객 화면에 뜬다.
- 소비자를 4대로 늘렸더니 일부 주문 상태가 `SHIPPED`에서 `PAID`로 되돌아간다.
- 장애 30분 뒤 소비자가 살아나자, 이미 취소된 "재고 예약" 명령 수천 건이 한꺼번에 실행된다.

## 동작·원리

### 1. 메시지 세 종류 — 무엇을 담나

```text
  종류       예                        보낸 쪽의 기대                 보통 쓰는 채널
  ───────── ───────────────────────── ───────────────────────────── ──────────────
  Command   PayOrder(o-1, 3000원)     "이 일을 해라" — 결과를 기대     P2P(받는 곳 하나)
  Event     OrderPlaced(o-1)          "이런 일이 있었다" — 누가 반응하든 무관   Pub-Sub
  Document  Order{o-1, items, addr}   "이 데이터를 넘긴다" — 무엇을 할지는 받는 쪽   P2P 또는 Pub-Sub
```

- *Command Message*: 다른 애플리케이션의 기능을 호출하려고 보내는 메시지. EIP는 "명령 전용 메시지 타입은 따로 없다. 명령을 담은 평범한 메시지일 뿐이다"라고 적는다.
- *Event Message*: 일어난 일을 알리는 메시지. EIP 기준으로 내용보다 **시점**이 중요하다. 비어 있는 이벤트도 많다. 도착했다는 사실만으로 반응하게 한다.
- *Document Message*: 데이터 구조 하나를 넘기는 메시지. EIP 기준으로 **내용**이 중요하고 시점은 덜 중요하다.
- 차이는 메시지 바이트가 아니라 **의미와 책임**이다. 같은 JSON이라도 이름이 `PayOrder`면 명령이고 `OrderPaid`면 사건이다.

결합 방향이 달라진다.

```text
  명령으로 짜면 — 발행자가 받는 쪽을 안다          이벤트로 짜면 — 구독자가 발행자를 안다
  주문 ──PayOrder──▶ 결제                         주문 ──OrderPlaced──▶ [orders 토픽]
      ──AddPoint──▶ 포인트                                                 ├──▶ 결제
      ──SendMail──▶ 메일                                                   ├──▶ 포인트
      ──IssueCoupon──▶ 쿠폰  ← 새 기능 = 주문 수정                          ├──▶ 메일
                                                                           └──▶ 쿠폰 ← 구독만 추가
```

- 명령은 보낸 쪽이 "누가 무엇을 할지" 정한다. 받는 쪽이 늘면 보낸 쪽 코드가 늘어난다.
- 이벤트는 받는 쪽이 "무엇에 반응할지" 정한다. 구독자가 늘어도 발행자는 그대로다.
- 그렇다고 이벤트가 늘 낫지는 않다.
  - 결과가 꼭 필요하고 책임자가 하나면(예: "이 카드로 3000원 승인") 명령이 의도를 더 분명히 드러낸다.
  - 이벤트 연쇄만으로 업무 흐름을 짜면 흐름이 코드 어디에도 한곳에 보이지 않는다. 이 선택은 23번(orchestration vs choreography)의 주제다.

### 2. 메시지 겉봉 — Correlation ID · Return Address · Expiration

```text
  요청자 A                                                        응답자
     │ request{ id=r-17, replyTo=reply.A, expiresAt=12:00:05, body }   │
     ├──────────────────────── requests 채널 ─────────────────────────▶│
     │                                                                 │ 처리
     │◀──────────────────────── reply.A 채널 ──────────────────────────┤
       reply{ correlationId=r-17, body }
     A의 대기표: { r-15 → 콜백1, r-16 → 콜백2, r-17 → 콜백3 }  ← correlationId로 찾는다
```

- *Request-Reply*: 단방향인 메시지로 요청과 응답을 주고받는 짝. EIP는 응답 채널을 대개("almost always") point-to-point로 둔다. 응답은 요청자에게만 의미가 있기 때문이다.
- *Return Address*: 요청 안에 "응답은 이 채널로"를 적는다. 응답자는 응답 채널을 하드코딩하지 않는다. EIP는 이것을 데이터가 아니라 헤더에 둔다.
- *Correlation Identifier*: 응답이 어느 요청의 것인지 알려 주는 값. 응답자가 요청의 request ID를 응답의 correlation ID로 복사한다.
  - 응답 채널 하나를 여러 요청이 공유하면(EIP의 "비동기 콜백" 방식) 이 값이 없으면 짝을 지을 수 없다.
- *Message Expiration*: 메시지가 쓸모 있는 시한. 시한이 지나면 소비자는 그 메시지를 "보내지 않은 것처럼" 무시한다(EIP).
  - 제품마다 다르다. RabbitMQ는 메시지별 `expiration` 속성(밀리초 문자열)이 있고, 큐 TTL과 둘 다 있으면 작은 쪽을 쓴다. 메시지별 TTL로 만료된 메시지는 **큐의 맨 앞에 왔을 때** 버려지거나 dead-letter된다(클래식 큐는 정책 변경 통지 때도). 브로커는 이미 만료된 메시지를 소비자에게 배달하지 않는다고 문서가 보장한다. 다만 소켓에 쓴 뒤 소비자에 닿기 전에 만료되는 경합은 있다고 같은 문서가 적는다. 그래서 소비자 쪽 시한 검사도 둔다(RabbitMQ 문서 "Time-To-Live and Expiration").
  - Azure Service Bus는 메시지·엔티티 중 이른 쪽에 만료하고, 설정했으면 dead-letter 채널로 보낸다(EIP 사이트의 Azure 예). 단 이미 잠금(lock)으로 받아 간 메시지는 시한이 지나도 그대로 처리·완료할 수 있다. 잠금이 풀리거나 포기(abandon)될 때 만료가 적용된다(Microsoft 문서 "Message expiration").
  - Kafka 4.1에는 메시지별 만료가 없다. 토픽의 `retention.ms`(브로커 기본 `log.retention.hours=168`, 로컬 4.1.0에서 확인)는 **보관 기간**이지 "이 명령이 언제까지 유효한가"가 아니다. 유효 시한은 헤더에 넣고 소비자가 검사한다.

#### 실험: 응답 짝짓기와 만료 검사

요청 100개를 공유 응답 채널로 받는다. 응답자 4개의 처리 시간이 0~2ms로 제각각이다. (A) "보낸 순서대로 온다"고 가정한 짝짓기와 (B) correlation ID 짝짓기를 비교했다. 이어서 TTL 0.5초 명령 7개와 60초 명령 3개를 넣고 소비자를 2초 멈췄다.

```java
// 응답자: 요청 ID를 응답의 correlation ID로 복사
replies.add(new Rep(r.id(), r.x() * r.x()));
// (B) 요청자: 대기표에서 correlation ID로 찾는다
Map<String, Req> pending = new HashMap<>();
for (Rep p : got) { Req r = pending.remove(p.correlationId()); if (r == null || p.result() != r.x() * r.x()) corrWrong++; }
// 만료 검사: 처리 직전에 본다
if (System.currentTimeMillis() > r.expiresAt()) expired++; else run++;
```

(실험, Java 21 eclipse-temurin 단일 프로세스 시뮬레이션, 2026-10-01) — 순서 섞임은 실행마다 다르다.

```text
replies=100  FIFO matching wrong=85  correlation-id matching wrong=0  unmatched pending=0
replies=100  FIFO matching wrong=88  correlation-id matching wrong=0  unmatched pending=0
replies=100  FIFO matching wrong=95  correlation-id matching wrong=0  unmatched pending=0
after 2s outage: no-expiry-check executed=10   with expiry check executed=3 expired->DLQ=7
```

- 응답자가 둘 이상이면 응답 순서는 요청 순서와 달라진다. 순서로 짝지으면 100건 중 85~95건이 틀렸다(위 3회). 점검 재실행 12회에서는 80~96건이었다.
- correlation ID로 찾으면 0건이다. 순서와 무관하다.
- 만료 검사가 없으면 시한이 지난 7건도 실행된다. 검사하면 3건만 실행하고 7건을 dead-letter로 돌린다.

### 3. 채널 — 누가 받나

```text
  Point-to-Point     생산자 ─▶ [큐] ─▶ 소비자 A 또는 B      한 메시지 = 소비자 하나
  Publish-Subscribe  생산자 ─▶ [토픽] ─┬▶ 구독 X (사본)      한 메시지 = 구독마다 한 부
                                       └▶ 구독 Y (사본)
  Datatype           orders.v1 / refunds.v1                 채널 하나 = 메시지 타입 하나
  Dead Letter        시스템이 배달 못 함(만료·배달 횟수 초과) ─▶ DLQ
  Invalid Message    받았지만 뜻을 모름(파싱 실패·스키마 불일치) ─▶ invalid 채널
```

- *Point-to-Point Channel*: 수신자가 여럿이어도 한 메시지는 하나만 가져간다. 수신자끼리 조율할 필요가 없다(EIP).
- *Publish-Subscribe Channel*: 구독자마다 사본을 준다. 각 구독자는 자기 사본을 한 번 소비한다(EIP).
- *Datatype Channel*: 타입마다 채널을 따로 둔다. 받는 쪽은 "어느 채널로 왔나"로 타입을 안다(EIP).
- *Dead Letter Channel*: **메시징 시스템**이 배달할 수 없거나 배달하면 안 된다고 판단한 메시지를 옮기는 곳(EIP). SQS는 수신 횟수가 한도에 닿으면 옮긴다(EIP 사이트의 SQS 예).
- *Invalid Message Channel*: **수신자**가 받았지만 처리할 수 없는 메시지를 옮기는 곳(EIP). 둘을 섞으면 "배달 실패"와 "내용 오류"가 한 통에 섞여 원인을 가리기 어렵다.
- Kafka 4.1에서는 이 구분이 소비자 그룹으로 나타난다.
  - 같은 그룹 안: 파티션 하나는 어느 순간 그룹 소비자 하나만 읽는다(Kafka 4.1 문서 Design 절 "consumed by exactly one consumer within each subscribing consumer group at any given time") → P2P처럼 동작.
  - 그룹이 여럿: 그룹마다 전체를 읽는다 → Pub-Sub처럼 동작.
  - 클래식 소비자 그룹에는 브로커가 옮겨 주는 DLQ가 없다. 소비자 프레임워크나 앱이 별도 토픽에 다시 쓴다(18번). Kafka Connect 싱크 커넥터에는 `errors.deadletterqueue.topic.name` 설정이 있다(EIP 사이트의 Kafka Connect 예).

### 4. 소비 쪽 확장 — 소비자를 늘리면 무엇이 깨지나

#### 4-1. Competing Consumers와 Queue-Based Load Leveling

```text
  생산 속도가 들쭉날쭉           큐가 완충                 소비자 여럿이 경쟁
  ▁▁█▁▁██▁▁▁█▁  ──────▶  [■■■■■■■■■■]  ──────▶  ┌ 소비자 1
                                                  ├ 소비자 2   (한 메시지는 하나만 가져감)
                                                  └ 소비자 3
```

- *Competing Consumers*: P2P 채널 하나에 소비자를 여럿 둬서 동시에 처리한다. Pub-Sub 채널에 소비자를 늘리면 사본만 늘어난다(EIP).
- *Queue-Based Load Leveling*: 큐를 버퍼로 두어 순간 부하가 뒤 서비스를 넘어뜨리지 않게 한다(Azure Architecture Center).
  - 평균 생산 속도가 소비 속도보다 크면 큐는 계속 자라고 지연이 는다. 버퍼는 순간 부하만 흡수한다(같은 문서).
  - 소비자를 자동으로 늘리기만 하고 뒤쪽 호출 속도를 묶지 않으면 과부하가 DB 같은 하위 의존성으로 옮겨 갈 뿐이다(같은 문서).
- Azure 문서는 경쟁 소비자에서 **메시지 순서가 보장되지 않는다**고 적는다. 작업이 "특정 순서로 실행되어야 할 때"는 이 패턴이 맞지 않는다고도 적는다.
- Kafka에서 경쟁 소비자는 파티션 단위다.
  - EIP 사이트의 Kafka 예: 파티션 각각이 P2P 채널이고, 소비자는 사실 경쟁하지 않고 미리 배정된 채널을 읽는다. 한 채널이 비어도 그 소비자가 다른 채널을 돕지 못한다. 그룹 안 경쟁 소비자 수는 파티션 수를 넘을 수 없다고 적는다.
  - 파티션 하나를 그룹 소비자 하나만 읽으므로(Design 절), 소비자가 파티션보다 많으면 남는 소비자는 받을 파티션이 없다.
  - Kafka 4.1에는 파티션 배정 없이 레코드 단위로 나눠 받는 **share group**(KIP-932)이 preview로 들어 있다. 레코드별 확인(ack)과 배달 횟수를 센다. 순서 있는 스트림이 아니라 한 건씩 처리할 때 쓰라고 업그레이드 노트가 적는다. `share.version=1`로 켜야 한다.

#### 4-2. 순서가 필요한 메시지 — Sequential Convoy

```text
  큐(발행 순서): o1:CREATED o1:PAID o1:SHIPPED o2:CREATED ...

  경쟁 소비자                                키 해시 → 레인(레인당 소비자 하나)
  소비자1: o1:PAID ──(지연)────▶ 상태=PAID ✘    레인 hash(o1)%4: o1:CREATED → o1:PAID → o1:SHIPPED
  소비자2: o1:SHIPPED ─▶ 상태=SHIPPED            레인 hash(o2)%4: o2:CREATED → ...
  → 늦게 끝난 PAID가 SHIPPED를 덮어씀          → 같은 주문은 한 줄로, 다른 주문끼리는 병렬
```

- *Sequential Convoy*: 관련 메시지를 범주 키(예: 주문 ID)로 묶고, 묶음 안은 하나씩 순서대로, 묶음끼리는 병렬로 처리한다(Azure Architecture Center).
  - Azure Service Bus는 message session(`SessionId`)으로 구현한다. 소비자가 세션 하나에 배타 락을 잡는다.
  - Kafka는 키 → 파티션으로 같은 효과를 낸다. 키가 있고 파티션을 지정하지 않으면 기본 분할기가 `toPositive(murmur2(키 바이트)) % 파티션 수`로 고른다(Kafka 4.1 `BuiltInPartitioner.partitionForKey` 소스).
- 키 고르기가 병렬도를 정한다. 너무 굵으면(고객 ID 하나에 그 고객의 주문 전부) 병렬이 줄고, 너무 잘면 순서를 지킬 의미가 없다(같은 문서).
- 묶음 안에서 처리가 계속 실패하는 메시지(poison)는 그 뒤 메시지를 모두 막는다. 재시도 상한 뒤 DLQ로 빼야 나머지가 흐른다(같은 문서).

#### 실험: 경쟁 소비자 vs 키 레인 — 상태 역행 개수

주문 2,000개마다 `CREATED(1) → PAID(2) → SHIPPED(3)` 이벤트 3개를 주문별 순서대로 큐에 넣었다. 처리 = "상태 := 이벤트의 상태"(흔한 덮어쓰기 모양), 10%의 메시지에 1ms 지연을 넣었다. 최종 상태가 `SHIPPED`가 아니면 역행으로 셌다.

```java
// (A) 경쟁 소비자: 한 큐에서 4개 스레드가 꺼낸다
for (int i = 0; i < WORKERS; i++) ex.submit(() -> { Ev e; while ((e = q.poll()) != null) work(e, st); });
// (B) 키 해시 → 레인 4개, 레인마다 스레드 하나
lanes.get(Math.floorMod(Integer.hashCode(e.orderId()), WORKERS)).add(e);
```

(실험, Java 21 eclipse-temurin 단일 프로세스 시뮬레이션, 2026-10-01) — 역행 개수는 실행마다 다르다.

```text
run 1  competing consumers:  354 / 2000 orders regressed   key-hash lanes: 0 / 2000
run 2  competing consumers:  334 / 2000 orders regressed   key-hash lanes: 0 / 2000
run 3  competing consumers:  339 / 2000 orders regressed   key-hash lanes: 0 / 2000
```

- 경쟁 소비자에서는 세 번 모두 2,000건 중 330~360건 정도가 `SHIPPED`가 아닌 상태로 끝났다. 점검 재실행 12회에서는 314~376건이었다.
- 키 레인에서는 0건이다. 같은 주문의 이벤트가 한 스레드에서 차례로 처리되기 때문이다.

#### 실험: Kafka 키 → 파티션

공용 Kafka에 파티션 3개 토픽 `w19-orders`를 만들고, `order-1`~`order-6` 키로 `CREATED`·`PAID`·`SHIPPED`를 차례로 18건 보냈다.

```bash
kafka-console-producer.sh --topic w19-orders --property parse.key=true --property key.separator=:
kafka-console-consumer.sh --topic w19-orders --from-beginning \
  --property print.partition=true --property print.key=true --property print.offset=true
```

(실험, Kafka 4.1.0 KRaft 단일 노드, 2026-10-01)

```text
Partition:0	Offset:0	order-2	CREATED
Partition:0	Offset:1	order-3	CREATED
Partition:0	Offset:2	order-6	CREATED
Partition:0	Offset:3	order-2	PAID
Partition:0	Offset:4	order-3	PAID
Partition:0	Offset:5	order-6	PAID
Partition:0	Offset:6	order-2	SHIPPED
Partition:0	Offset:7	order-3	SHIPPED
Partition:0	Offset:8	order-6	SHIPPED
Partition:1	Offset:0	order-1	CREATED
Partition:1	Offset:1	order-1	PAID
Partition:1	Offset:2	order-1	SHIPPED
Partition:2	Offset:0	order-4	CREATED
Partition:2	Offset:1	order-5	CREATED
Partition:2	Offset:2	order-4	PAID
Partition:2	Offset:3	order-5	PAID
Partition:2	Offset:4	order-4	SHIPPED
Partition:2	Offset:5	order-5	SHIPPED
```

- 같은 키는 한 파티션에만 있고, 파티션 안에서는 보낸 순서(오프셋 순)다.
- 키 6개가 3:1:2로 나뉘었다. 해시 분배는 키가 적으면 고르지 않다.

같은 토픽을 그룹 `w19-g`의 콘솔 소비자 2개로 읽었다.

```text
GROUP  TOPIC       PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG  CLIENT-ID
w19-g  w19-orders  0          9               9               0    console-consumer
w19-g  w19-orders  1          3               3               0    console-consumer
w19-g  w19-orders  2          6               6               0    console-consumer
== c1
      9 Partition:0
      3 Partition:1
== c2
      6 Partition:2
```

- 소비자 c1이 파티션 0·1(12건), c2가 파티션 2(6건)를 맡았다. 파티션 수 3을 소비자 2개로 나누면 한쪽이 더 받는다. 어느 소비자가 두 개를 받는지는 배정 순서에 따라 실행마다 다를 수 있다.

#### 4-3. Priority Queue와 Selective Consumer

```text
  단일 큐 + 우선순위              여러 큐 + 소비자 풀 분리
  [H H L H H L ...] ─▶ 힙         [high] ─▶ 소비자 풀 20개
   꺼낼 때 가장 높은 것            [low]  ─▶ 소비자 풀 4개
```

- *Priority Queue 패턴*: 메시지에 우선순위를 붙여 높은 것부터 처리한다. 단일 큐 방식과 우선순위별 여러 큐 방식이 있다(Azure Architecture Center).
  - 여러 큐를 소비자 풀 하나가 "높은 큐가 빌 때만 낮은 큐"로 읽으면 낮은 우선순위가 계속 밀려 처리되지 않을 수 있다(같은 문서).
  - 문서의 대책: 오래 기다린 메시지의 우선순위를 올린다(에이징), 우선순위별로 소비자 풀을 따로 둔다.
- *Selective Consumer*: 선택 값(헤더 등)을 보고 자기 기준에 맞는 메시지만 받는다(EIP).
  - P2P 채널에서 쓰면 선택적인 경쟁 소비자가 된다. 어떤 소비자의 기준에도 맞지 않는 메시지는 만료될 때까지 채널에 남는다(EIP).

#### 실험: 엄격한 우선순위 vs 에이징

이산 시간 시뮬레이션이다. 매 틱 high 1건, 5틱마다 low 1건이 도착하고, 소비자는 틱당 1건을 처리한다. 도착률(1.2건/틱)이 처리율(1건/틱)보다 큰 **과부하** 상황이다. 에이징은 "유효 우선순위 = 기본(10 또는 1) + 대기 틱/20"이다.

(실험, Java 21 eclipse-temurin 결정적 시뮬레이션, 1,000틱, 2026-10-01)

```text
strict   high done=1000  low done=0  low still waiting=200  avg low wait=- ticks
aging    high done=863  low done=137  low still waiting=63  avg low wait=248 ticks
```

- 엄격한 우선순위에서는 low가 1,000틱 동안 한 건도 처리되지 않았다(기아).
- 에이징은 low 137건을 처리했지만 그만큼 high 처리가 줄었다. 과부하에서는 누군가 기다린다. 우선순위는 누가 기다릴지를 정할 뿐이다.

## 쓰이는 자료구조·알고리즘

- **FIFO 큐** — P2P 채널, 경쟁 소비자, 부하 평준화 버퍼. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **우선순위 큐 = 힙** — 단일 큐 Priority Queue는 꺼낼 때 가장 높은 우선순위를 O(log n)에 얻는다. 에이징을 넣으면 우선순위가 시간에 따라 바뀌어 재정렬 비용이 든다. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **키 해시 → 파티션** — Kafka 기본 분할기 `murmur2(키) % 파티션 수`. 나머지 연산이라 **파티션 수를 바꾸면 같은 키가 다른 파티션으로 갈 수 있다.** 그 순간 키 단위 순서 보장이 경계에서 끊긴다. 해시는 [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), 노드 증감에 덜 흔들리는 분배는 [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md).
- **대기표(해시맵) + 타임아웃** — request-reply의 요청자는 `correlationId → 콜백`을 해시맵에 두고, 시한이 지난 항목을 지운다. 지우지 않으면 응답이 오지 않은 요청이 메모리에 쌓인다.
- **에이징** — 기다린 시간에 비례해 우선순위를 올려 기아를 막는 스케줄링 기법.

## 적용 — 풀어나가는 법

**1) 메시지 이름부터 정한다.** 명령은 명령형(`PayOrder`), 사건은 과거형(`OrderPaid`), 문서는 명사(`Order`)로 짓는다. 이름이 "누가 결정하나"를 드러낸다.

```java
// 겉봉(헤더)과 본문을 나눈다 — 헤더는 라우팅·상관·만료, 본문은 업무 데이터
record Envelope<T>(String messageId, String type, String correlationId,
                   String replyTo, Instant expiresAt, T body) {}

record PayOrder(String orderId, long amount) {}          // Command: 결제 서비스 하나가 받는다
record OrderPlaced(String orderId, Instant at) {}        // Event: 누가 듣든 발행자는 모른다
```

**2) 요청-응답은 대기표와 시한을 같이 둔다.**

```java
class Requester {
    private final Map<String, CompletableFuture<Reply>> pending = new ConcurrentHashMap<>();

    CompletableFuture<Reply> send(Request req, Duration timeout) {
        String id = UUID.randomUUID().toString();
        CompletableFuture<Reply> f = new CompletableFuture<Reply>()
            .orTimeout(timeout.toMillis(), TimeUnit.MILLISECONDS)
            .whenComplete((r, e) -> pending.remove(id));          // 성공·시간 초과 모두 대기표에서 지운다
        pending.put(id, f);
        channel.send(new Envelope<>(id, "Request", null, "reply.svcA", Instant.now().plus(timeout), req));
        return f;
    }

    void onReply(Envelope<Reply> m) {                          // 응답 채널 리스너
        CompletableFuture<Reply> f = pending.get(m.correlationId());
        if (f == null) { log.warn("late or unknown reply {}", m.correlationId()); return; }  // 이미 포기한 요청
        f.complete(m.body());
    }
}
```

**3) 소비자는 처리 전에 세 가지를 거른다.**

```java
void onMessage(Envelope<?> m) {
    if (m.expiresAt() != null && Instant.now().isAfter(m.expiresAt())) {
        deadLetter.send(m, "expired"); return;                 // 만료 → DLQ (실행하지 않는다)
    }
    Object cmd;
    try { cmd = decoder.decode(m); }
    catch (DecodeException e) { invalid.send(m, e.getMessage()); return; }   // 뜻을 모름 → invalid 채널
    if (!dedup.firstTime(m.messageId())) return;               // at-least-once 중복 → 멱등 처리
    handler.handle(cmd);
}
```

- 중복 제거는 [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)(reliability/13 멱등성 노트).

**4) 순서가 필요한 흐름은 키를 먼저 정한다.**
- "무엇의 순서인가"를 한 문장으로 쓴다(예: "같은 주문의 상태 이벤트"). 그 대상의 ID를 메시지 키로 쓴다.
- Kafka는 키로 파티션을 정하고, 파티션 수는 처음에 넉넉히 잡는다. 나중에 늘리면 키 → 파티션 대응이 바뀐다.
- 진단 명령(Kafka 4.1):

```bash
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic orders          # 파티션 수·리더·ISR
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group billing # 파티션별 배정·LAG
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic orders --from-beginning \
  --property print.key=true --property print.partition=true                           # 키가 어디로 갔나
```

**5) 우선순위는 큐를 나누고 풀을 나눈다.** 단일 큐 + 엄격한 우선순위는 과부하에서 낮은 쪽을 굶긴다. high·low 큐를 나누고 low에도 최소 소비자를 남긴다. low 대기 시간을 지표로 본다.

## 장애 시나리오와 대처

### 1. 이벤트와 명령을 혼동 → 구독자가 늘 때마다 발행자 수정 (결합 역전)

- **현상**: 새 기능(쿠폰·알림)을 붙일 때마다 주문 서비스 배포가 따라온다. 주문 서비스 장애가 무관한 기능까지 멈춘다.
- **보이는 형태**: 주문 서비스 코드에 `paymentClient.send(PayOrder)`, `pointClient.send(AddPoint)`, `mailClient.send(...)`가 줄줄이 있다. 받는 쪽 목록이 발행자 설정에 있다.
- **원인**: "일어난 일"을 알려야 할 자리에서 "할 일"을 하나씩 지시했다. 받는 쪽 목록을 발행자가 쥐고 있다.
- **대처**: 사실은 이벤트(`OrderPlaced`) 하나로 Pub-Sub 채널에 낸다. 받는 쪽이 구독한다. 결과가 꼭 필요한 한 단계(결제 승인)만 명령으로 남긴다.

### 2. Correlation ID 없는 요청-응답 → 응답 오매칭

- **현상**: 간헐적으로 다른 사용자의 결과가 보인다. 부하가 낮을 때는 재현되지 않는다.
- **보이는 형태**: 응답 채널 하나를 여러 요청이 공유한다. 로그에서 요청 순서와 응답 순서가 다르다. 위 실험에서 순서 짝짓기는 100건 중 80~96건이 틀렸다(재실행 포함).
- **원인**: 응답자가 둘 이상이거나 처리 시간이 다르면 응답 순서가 섞인다. 순서로 짝지으면 틀린다.
- **대처**: 요청마다 고유 ID를 넣고 응답자가 correlation ID로 복사하게 한다. 요청자는 대기표에서 ID로 찾는다. 대기표에는 시한을 둬서 오지 않는 응답이 쌓이지 않게 한다.

### 3. 경쟁 소비자로 순서가 필요한 메시지를 병렬 처리 → 상태 역행

- **현상**: 배송까지 끝난 주문이 `PAID`로 보인다. 소비자를 늘린 뒤부터 생겼다.
- **보이는 형태**: 상태 변경 로그에서 같은 주문의 이벤트 처리 시각이 발행 순서와 다르다. 위 실험에서 2,000건 중 310~380건 정도가 역행했다(재실행 포함).
- **원인**: 같은 주문의 이벤트가 서로 다른 소비자에게 가서 동시에 처리됐다. 늦게 끝난 옛 이벤트가 새 상태를 덮어썼다.
- **대처**
  - 주문 ID를 키로 한 Sequential Convoy(Kafka 키 파티셔닝, Service Bus 세션).
  - 소비자 쪽에서도 막는다. 상태 전이를 검사하거나(`PAID`는 `CREATED`에서만), 이벤트에 순번·버전을 넣고 더 작은 버전은 버린다. 브로커에 도착하기 전에 순서가 바뀔 수도 있기 때문이다(Azure Sequential Convoy 문서의 "Out-of-order message delivery").

### 4. 만료 없는 메시지 → 장애 복구 뒤 낡은 명령 일괄 실행

- **현상**: 소비자가 30분 멈췄다 살아나자, 이미 취소된 예약·만료된 쿠폰 발급 명령이 한꺼번에 실행된다.
- **보이는 형태**: 복구 직후 처리량 급증, 그 뒤 고객 문의·보상 처리 급증. 메시지 생성 시각과 처리 시각의 차이(지연)가 수십 분.
- **원인**: 메시지에 유효 시한이 없어 소비자가 낡은 명령과 새 명령을 구분하지 못했다. Kafka의 보관 기간(`retention`)은 유효 시한이 아니다.
- **대처**: 시한이 의미 있는 명령·이벤트에 `expiresAt`을 넣는다. 소비자는 처리 직전에 검사해 지난 것은 DLQ로 보낸다. RabbitMQ·Service Bus처럼 브로커가 만료를 지원하면 함께 쓴다. RabbitMQ는 만료된 메시지가 큐 맨 앞에 올 때 처리하므로, 뒤에 쌓인 만료 메시지가 바로 사라지지 않는다는 점을 감안한다.

### 5. 엄격한 우선순위 → 낮은 우선순위 기아

- **현상**: 프로모션 기간에 일반 고객 주문 처리가 몇 시간째 멈춰 있다.
- **보이는 형태**: low 큐 길이와 가장 오래된 메시지 나이가 계속 오른다. high 큐는 비지 않는다.
- **원인**: high 도착률이 처리 능력과 같거나 크다. 소비자가 high가 빌 때만 low를 읽는다.
- **대처**: 우선순위별 소비자 풀을 나누고 low에도 최소 풀을 둔다. 에이징을 넣는다. 근본적으로는 처리 능력을 늘리거나 입구에서 부하를 깎는다(위 실험: 과부하에서는 에이징도 high 처리를 줄인다).

## 핵심 문장

- 명령은 "이것을 해라"(보낸 쪽이 결정), 이벤트는 "이런 일이 있었다"(받는 쪽이 결정), 문서는 "이 데이터를 받아라"다.
- 이벤트로 바꾸면 결합 방향이 뒤집혀 구독자가 늘어도 발행자는 그대로다.
- 공유 응답 채널에서는 correlation ID가 없으면 응답을 짝지을 수 없다. 응답 순서는 요청 순서와 다를 수 있다.
- 경쟁 소비자는 처리량을 주는 대신 순서를 버린다. 순서가 필요하면 키로 묶어 묶음 안만 차례로 처리한다(Sequential Convoy, Kafka 키 파티셔닝).
- 메시지에 유효 시한을 두지 않으면 복구 뒤 낡은 명령이 실행된다. Kafka 보관 기간은 유효 시한이 아니다.
- 우선순위는 과부하에서 누가 기다릴지를 정할 뿐이다. 엄격한 우선순위는 낮은 쪽을 굶길 수 있다.

## 관련 주제·근거

- 선행
  - [17-queues-logs-and-delivery-semantics](../17-queues-logs-and-delivery-semantics/2-summary.md) — 큐 vs 로그, 전달 보장
  - [18-consumer-failure-handling](../18-consumer-failure-handling/2-summary.md)(재시도·DLQ·poison pill). 기존 원고 [server-design/07-async-messaging](../../systems/server-design/07-async-messaging.md) · [systems/kafka-consumer-failure](../../systems/kafka-consumer-failure/2-summary.md)
- 후속·연결
  - [34-message-routing-and-transformation](../34-message-routing-and-transformation/2-summary.md)(라우터·Aggregator·Resequencer) · [23-orchestration-vs-choreography](../23-orchestration-vs-choreography/2-summary.md)(명령 vs 이벤트 연쇄) · [21-kafka-internals](../21-kafka-internals/2-summary.md). 기존 원고 [systems/orchestration-choreography](../../systems/orchestration-choreography/2-summary.md)
  - api-design `20-messaging-protocols`(AMQP·MQTT·Kafka 프로토콜) — 미작성, [api-design/curriculum](../../api-design/curriculum.md)
  - reliability `13-idempotency` → [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)
  - [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md) · [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)
- 책·패턴 문서
  - G. Hohpe, B. Woolf, 『Enterprise Integration Patterns』, Addison-Wesley 2003 — 패턴 요약 페이지: Command Message, Event Message, Document Message, Request-Reply, Return Address, Correlation Identifier, Message Expiration, Point-to-Point Channel, Publish-Subscribe Channel, Datatype Channel, Dead Letter Channel, Invalid Message Channel, Competing Consumers(Kafka 예), Selective Consumer <https://www.enterpriseintegrationpatterns.com/patterns/messaging/>
  - Azure Architecture Center — Competing Consumers <https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers> · Queue-Based Load Leveling <https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling> · Priority Queue <https://learn.microsoft.com/en-us/azure/architecture/patterns/priority-queue> · Sequential Convoy <https://learn.microsoft.com/en-us/azure/architecture/patterns/sequential-convoy>
- 제품 문서·소스
  - RabbitMQ "Time-To-Live and Expiration" — 메시지별 `expiration`, 큐 TTL과의 최솟값, 큐 맨 앞에서 만료 처리 <https://www.rabbitmq.com/docs/ttl> (원문 markdown: rabbitmq/rabbitmq-website `docs/ttl.md`)
  - Microsoft Learn "Message expiration (Time to Live)" — 잠긴 메시지는 만료의 영향을 받지 않음, 잠금 해제·포기 시 적용 <https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-expiration>
  - Apache Kafka 4.1 — Design 절(파티션은 그룹 안 소비자 하나가 읽는다) <https://github.com/apache/kafka/blob/4.1/docs/design/design.md> · `BuiltInPartitioner.partitionForKey`(`toPositive(murmur2(key)) % numPartitions`) <https://github.com/apache/kafka/blob/4.1/clients/src/main/java/org/apache/kafka/clients/producer/internals/BuiltInPartitioner.java> · Producer configs `partitioner.class`·`partitioner.ignore.keys` <https://kafka.apache.org/41/generated/producer_config.html> · 4.1 업그레이드 노트(Queues for Kafka, KIP-932 preview, share group) <https://github.com/apache/kafka/blob/4.1/docs/getting-started/upgrade.md>
- 실험(scratchpad, 2026-10-01)
  - `CorrelationAndExpiry.java` — 공유 응답 채널 100건의 순서 짝짓기 vs correlation ID 짝짓기, 2초 정지 뒤 만료 검사(Java 21 단일 프로세스)
  - `OrderConvoy.java` — 주문 2,000개 × 3이벤트, 경쟁 소비자 4 vs 키 해시 레인 4의 상태 역행 수(Java 21)
  - `PriorityStarvation.java` — 과부하(1.2건/틱 도착, 1건/틱 처리)에서 엄격한 우선순위 vs 에이징(Java 21 결정적 시뮬레이션)
  - Kafka 4.1.0 KRaft 단일 노드 — 파티션 3개 토픽에 키 6개 × 3이벤트를 보내 파티션·오프셋 확인, 그룹 소비자 2개의 파티션 배정과 LAG(`kafka-consumer-groups --describe`)
