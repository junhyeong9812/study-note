# api-design/20-messaging-protocols — 메시징 프로토콜: AMQP·MQTT·Kafka, 브로커 vs RPC, QoS·ack 모델 — 정리 (힌트)

## 해결하는 문제

RPC는 "상대가 지금 살아 있고, 지금 처리하고, 지금 답한다"를 전제로 한다.

```text
  RPC (동기)
  주문 서비스 ── 호출 ──> 알림 서비스 (죽어 있음)  → 주문 요청도 실패하거나 타임아웃까지 대기

  브로커 (비동기)
  주문 서비스 ── 발행 ──> [브로커: 저장] ── 나중에 ──> 알림 서비스 (살아나면 가져감)
  → 보내는 쪽과 받는 쪽이 같은 시각에 살아 있을 필요가 없다
```

- *메시지 브로커*: 생산자가 보낸 메시지를 받아 저장하고, 소비자에게 전달하는 중간 서버. 둘을 **시간**(동시에 살아 있을 필요 없음)과 **공간**(서로 주소를 몰라도 됨)으로 떼어 놓는다.
- 대신 새 질문이 생긴다: **브로커가 메시지를 언제 "전달 끝"으로 치나?** 이 경계가 ack(확인 응답) 모델이고, 잘못 잡으면 유실이나 중복이 난다.
  - *ack(acknowledgement)*: 받는 쪽이 "받았다/처리했다"고 알려 보내는 쪽이 메시지를 지우거나 재전송을 멈추게 하는 신호.
- 쉬운 예: 등기 우편. 우체국(브로커)이 보관하다가 수취인이 서명(ack)하면 배달 완료다. 서명을 문 앞에서 받고 상자를 열기 전에 잃어버리면(처리 전 ack) 내용물은 사라진다. 상자를 다 열고 서명하려는데 서명 직전에 쓰러지면(처리 후 ack 실패) 우체국은 다시 배달한다(중복).
- 똑같은 구조다. 실무 예: IoT 센서는 MQTT, 업무 작업 큐는 AMQP(RabbitMQ), 이벤트 스트림은 Kafka — 프로토콜마다 "전달 끝"의 정의와 연결 감시 방식이 다르다.

## 동작·원리

### 1. 세 프로토콜의 모양

```text
  AMQP 0-9-1 (RabbitMQ)   생산자 ─> [exchange] ─binding─> [queue] ─push─> 소비자 ─ basic.ack ─> 큐에서 삭제
  MQTT 5.0                발행자 ─PUBLISH(topic, QoS)─> [broker] ─PUBLISH─> 구독자   (구간마다 QoS 핸드셰이크)
  Kafka                   생산자 ─Produce─> [partition 로그] <─Fetch(pull)─ 소비자 ─ 오프셋 커밋 ─> 위치만 저장
```

- **AMQP 0-9-1**(RabbitMQ "AMQP 0-9-1 Model Explained")
  - 생산자는 *exchange*로 보내고, exchange가 *binding* 규칙에 따라 *queue*로 복사한다. exchange 종류: direct·fanout·topic·headers.
  - 소비는 구독(push, 권장)이나 `basic.get`(pull, 문서가 "매우 비효율적"이라 함).
  - 연결 하나에 *channel* 여러 개를 다중화한다.
- **MQTT 5.0**(OASIS 표준, 2019-03-07)
  - 토픽 이름 기반 발행/구독. 가벼운 헤더로 센서·모바일을 겨냥한다.
  - QoS는 **구간마다** 따로다 — 발행자→브로커, 브로커→구독자. 구독자가 받는 QoS = min(발행 QoS, 브로커가 허락한 최대 QoS)(MQTT-3.8.4-8).
- **Kafka**(Apache Kafka 4.1 문서)
  - TCP 위 이진 프로토콜, 모든 API가 요청-응답 쌍이다. 연결 하나 안에서는 보낸 순서대로 처리·응답한다.
  - 소비자가 가져가는(pull) 방식이다. 브로커는 메시지를 지우지 않고, 소비자 그룹이 **어디까지 읽었나(오프셋)**만 커밋한다([distributed/21](../../distributed/21-kafka-internals/2-summary.md)).

### 2. "전달 끝"의 정의 — ack 모델 비교

```text
  MQTT QoS 0  발행자 ── PUBLISH ──> 수신자                     응답 없음, 재전송 없음 → 0번 또는 1번
  MQTT QoS 1  발행자 ── PUBLISH ──> 수신자 ── PUBACK ──>        PUBACK 전까지 재전송 → 1번 이상(중복 가능)
  MQTT QoS 2  발행자 ── PUBLISH ──> ── PUBREC <── ── PUBREL ──> ── PUBCOMP <──   → 정확히 1번(그 구간)

  AMQP 자동 ack   브로커가 보내는 순간 전달 끝 → 소비자가 처리 전에 죽으면 유실
  AMQP 수동 ack   소비자가 basic.ack 보낼 때 끝 → ack 전에 채널·연결이 닫히면 자동 재큐잉(redelivered=true)

  Kafka 커밋 전 처리   처리 → 커밋 사이에 죽으면 다시 읽음 → 중복 (at-least-once)
  Kafka 처리 전 커밋   커밋 → 처리 사이에 죽으면 건너뜀 → 유실 (at-most-once)
```

- MQTT 5.0 4.3.1: QoS 0은 "하부 네트워크의 능력에 따라 전달"된다. 받는 쪽은 응답하지 않고 보내는 쪽은 재시도하지 않는다. 1장 개요는 유실이 생길 수 있고, 다음 값이 곧 오는 주변 센서 값 같은 데 쓸 수 있다고 적는다.
- RabbitMQ "Consumer Acknowledgements and Publisher Confirms"
  - 자동 ack = "fire-and-forget". 보낸 직후 전달 성공으로 친다 — 안전하지 않다.
  - 수동 ack(`basic.ack`·`basic.nack`·`basic.reject`). ack 안 된 전달은 채널·연결이 닫히면 자동으로 재큐잉되고 `redeliver` 플래그가 켜진다.
  - `basic.qos` prefetch로 ack 안 된 메시지 수를 제한한다. 문서는 100~300 범위가 보통 좋은 처리량을 낸다고 한다.
  - 생산자 쪽 확인은 *publisher confirms*(`confirm.select`). 지속 메시지·내구 큐면 디스크에 쓴 뒤 `basic.ack`를 보낸다.
- Kafka 4.1 생산자 기본값: `acks=all`(모든 ISR 복제본이 받아야 성공), `enable.idempotence=true`, `retries=2147483647`, `delivery.timeout.ms=120000`. 소비자 기본값: `enable.auto.commit=true`, `auto.commit.interval.ms=5000`, `auto.offset.reset=latest`.
  - 자동 커밋은 처리 완료와 무관하게 **주기적으로** 위치를 커밋한다. 그래서 처리 중 장애 시 유실·중복 어느 쪽도 날 수 있다(distributed/17 실험).

### 실험: 커밋 여부가 "다음에 무엇을 받나"를 정한다 (Kafka)

(실험, apache/kafka 4.1.0 단일 노드 KRaft 일회용 컨테이너, 전용 네트워크, 기본 CLI 도구, 2026-10-04)

토픽 `orders`(파티션 1)에 `m1`~`m10`을 넣고, 두 소비자 그룹이 각각 3개씩 두 번 읽었다. `g-manual`은 `enable.auto.commit=false`로 커밋 없이 종료(= 처리 후 커밋 전에 죽음), `g-auto`는 기본값(m1~m3를 출력한 뒤 정상 종료하면서 커밋 = 처리 뒤 커밋).

```text
kafka-console-consumer.sh --topic orders --group g-manual --from-beginning --max-messages 3 \
    --consumer-property enable.auto.commit=false        # 두 번 실행
kafka-console-consumer.sh --topic orders --group g-auto   --from-beginning --max-messages 3   # 두 번 실행
```

```text
== 그룹 g-manual (enable.auto.commit=false, 커밋 안 하고 종료) 1회차
m1
m2
m3
Processed a total of 3 messages
== g-manual 2회차
m1
m2
m3
Processed a total of 3 messages
== 그룹 g-auto (기본값, 종료 시 커밋) 1회차
m1
m2
m3
Processed a total of 3 messages
== g-auto 2회차
m4
m5
m6
Processed a total of 3 messages

GROUP TOPIC PARTITION CURRENT-OFFSET LOG-END-OFFSET LAG
g-auto orders 0 6 10 4
```

- 관찰
  - 커밋하지 않은 그룹은 다시 m1부터 받았다 → 이미 처리했다면 **중복**.
  - 커밋한 그룹은 m4부터 받았다 → 1회차에서 m1~m3 처리에 실패했다면 그 셋은 이 그룹에서 **다시 오지 않는다**(유실).
  - `g-manual`은 커밋한 오프셋이 없어 `--describe`에 오프셋 행이 나오지 않았다.
- 해석: Kafka에서 "ack"는 오프셋 커밋이다. 커밋을 처리 **뒤**에 두면 at-least-once(중복은 소비자가 멱등으로 흡수), **앞**에 두면 at-most-once다. `--from-beginning`은 커밋된 오프셋이 없을 때만 의미가 있다 — `g-auto` 2회차는 커밋 위치에서 이어 읽었다.
- 이 실험이 보인 것은 **커밋된 위치가 다음 실행의 시작점**이라는 것까지다. `g-auto`는 처리 뒤에 커밋됐으니 정상 경로다. 만약 커밋이 처리보다 먼저 일어나고(자동 커밋 주기가 처리 완료보다 앞섬) 그 처리가 실패했다면, 같은 위치 이동이 그 메시지의 **유실**이 된다 — 이 실험은 처리 실패를 만들지 않았다.
- 처리 중 장애를 실제로 일으키고 유실·중복 **개수**를 센 실험은 [distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)에 있다. 여기서는 프로토콜별 ack 위치 비교만 한다.

### 3. 오래 사는 연결의 끊김 감지

```text
  TCP만으로는         상대가 전원이 나가면 OS가 알아채기까지 오래 걸린다
                     (RabbitMQ 문서: 리눅스 기본 설정에서 약 11분)
  MQTT 5.0           Keep Alive × 1.5 안에 아무 패킷도 없으면 서버가 연결을 닫는다 (MQTT-3.1.2-22)
                     → 비정상 종료면 Will 메시지를 대신 발행
  AMQP(RabbitMQ)     heartbeat 타임아웃: 서버 제안 기본값 60초(문서는 5~20초가 대부분 환경에 최적이라 함),
                     그 절반 간격으로 보내고 2번 놓치면 연결 종료
  Kafka(classic)     session.timeout.ms 기본 45초, heartbeat.interval.ms 3초 → 넘기면 리밸런스
```

- 앱 계층 하트비트가 없거나 너무 길면, 죽은 소비자가 메시지(AMQP의 unacked, Kafka의 파티션)를 붙잡은 채 오래 남는다.
- 너무 짧으면 GC 정지·순간 지연에도 연결이 끊겨 재연결·리밸런스가 잦아진다. 둘 사이 균형이다([network/21](../../network/21-tcp-keepalive-and-user-timeout/2-summary.md)).

### 4. 브로커 vs RPC — 언제 무엇을

| | RPC(REST·gRPC) | 브로커(AMQP·MQTT·Kafka) |
|---|---|---|
| 호출자가 결과를 기다림 | 예 | 아니오(결과는 별도 경로) |
| 받는 쪽 장애 시 | 호출 실패 | 브로커에 쌓였다가 나중에 처리 |
| 팬아웃(한 이벤트 → 여러 소비자) | 호출자가 N번 호출 | 브로커가 복사(fanout·구독·소비자 그룹) |
| 흐름 제어 | 호출자가 속도 결정 | 소비자가 속도 결정(prefetch·pull) |
| 실패 처리 | 재시도·타임아웃 | ack·재전송·DLQ·멱등 소비 |

## 쓰이는 자료구조·알고리즘

- **큐(FIFO)**: AMQP 큐는 ack되면 지운다 → [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **추가 전용 로그 + 오프셋**: Kafka 파티션은 지우지 않는 로그이고 소비자는 위치(정수)만 저장한다. 같은 로그를 여러 그룹이 각자 다른 위치에서 읽는다 → [distributed/21](../../distributed/21-kafka-internals/2-summary.md).
- **토픽 필터 매칭**: MQTT 토픽은 `/`로 나뉜 계층이고 `+`(한 단계)·`#`(여러 단계) 와일드카드를 쓴다(MQTT 5.0 4.7). 구독 필터를 트라이로 두면 토픽 단계별로 매칭할 수 있다 → [data-structure/09-trie](../../data-structure/09-trie/2-summary.md).
- **패킷 식별자 + 상태 기계**: MQTT QoS 1·2는 패킷 ID별로 "PUBACK 대기", "PUBREC 받음 → PUBREL 보냄 → PUBCOMP 대기" 상태를 세션에 기억한다. QoS 2의 4단계가 그 구간의 중복 전달을 막는다.
- **unacked 집합 + 배달 태그**: AMQP 채널은 단조 증가하는 delivery tag로 ack 안 된 메시지를 추적한다. `multiple=true`면 그 태그까지 한꺼번에 ack한다.

## 적용 — 풀어나가는 법

### 1. 프로토콜 고르기

| 상황 | 흔한 선택 |
|---|---|
| 배터리·대역폭이 작은 장치, 불안정한 망, 수많은 토픽 구독 | MQTT |
| 작업 분배(일꾼 여러 명), 라우팅 규칙, 메시지별 ack·재큐잉 | AMQP(RabbitMQ) |
| 이벤트 기록을 오래 두고 여러 그룹이 각자 다시 읽기, 높은 처리량, 파티션 내 순서 | Kafka |

### 2. ack 위치 정하기 — 기본은 "처리 후 ack + 멱등 소비"

```java
// Kafka(kafka-clients 4.x) — 처리 후 커밋. 중복은 멱등 처리로 흡수한다.
props.put("enable.auto.commit", "false");
while (running) {
    ConsumerRecords<String, String> recs = consumer.poll(Duration.ofMillis(500));
    for (ConsumerRecord<String, String> r : recs) {
        handleIdempotently(r.key(), r.value());   // 같은 이벤트 ID면 건너뜀 (인박스 테이블 등)
    }
    consumer.commitSync();                        // 처리 뒤 커밋 → at-least-once
}
```

- AMQP라면 자동 ack 대신 수동 ack, 처리 성공 뒤 `basicAck`, 영구 실패는 `basicNack(requeue=false)`로 DLX에 보낸다. prefetch를 꼭 건다(무제한이면 소비자 메모리에 쌓인다).
- MQTT라면 잃으면 안 되는 메시지는 QoS 1 이상 + 수신 측 중복 제거. QoS 2는 그 구간만 정확히 한 번이다 — 앱 처리까지 보장하지는 않는다.
- 생산자 쪽도 확인을 받는다: AMQP publisher confirms, Kafka `acks=all`(4.1 기본값).

### 3. 진단

```text
  Kafka    kafka-consumer-groups.sh --describe --group <g>    → CURRENT-OFFSET · LOG-END-OFFSET · LAG
  RabbitMQ 큐별 ready / unacked 수, redelivered 비율       → unacked가 계속 많으면 소비자 정지·ack 누락
  MQTT     브로커의 세션별 inflight(QoS 1·2 미완료) 수, 연결 끊김(keep alive 초과) 로그
```

## 장애 시나리오와 대처

### 1. 결제 완료 이벤트가 가끔 사라진다 — MQTT QoS 0 (⚠)

- **현상**: 대부분 도착하지만 망이 흔들릴 때 일부 메시지가 오지 않는다. 에러 로그는 없다.
- **보이는 형태**: 발행 수와 수신 수의 차이. 재전송 흔적도 없다.
- **원인**: QoS 0은 응답도 재전송도 없다(MQTT 5.0 4.3.1). 발행 QoS가 1이어도 구독을 QoS 0으로 하면 그 구간은 QoS 0이다(min 규칙).
- **대처**: 잃으면 안 되는 메시지는 발행·구독 모두 QoS 1 이상 + 수신 측 메시지 ID 중복 제거. QoS 0은 다음 값이 곧 오는 센서 값처럼 잃어도 되는 데만.

### 2. 장애 뒤 일부 주문이 처리되지 않았다 — 처리 전 ack (⚠)

- **현상**: 소비자 재시작 뒤 일부 메시지가 영영 처리되지 않았다.
- **보이는 형태**: 브로커 기준으로는 소비 완료(큐 비었음, 오프셋 전진, lag 0). 하위 DB에는 결과가 없다.
- **원인**: AMQP 자동 ack, Kafka 처리 전 커밋(또는 자동 커밋이 처리보다 먼저 일어남). 커밋된 위치가 이미 넘어가 있어 다시 오지 않는다(실험의 `g-auto`가 2회차에 m4부터 받은 것과 같은 위치 이동).
- **대처**: 수동 ack·처리 후 커밋. 유실 없는 대신 중복이 생기므로 멱등 소비를 함께 둔다.

### 3. 같은 알림이 두 번 갔다 — 처리 후 ack 실패 (⚠)

- **현상**: 배포·리밸런스 직후 같은 메시지가 다시 처리된다.
- **보이는 형태**: AMQP `redelivered=true`, Kafka에서 같은 오프셋을 두 번 처리한 로그. 실험의 `g-manual`처럼 같은 메시지를 다시 받는다.
- **원인**: 처리는 끝났는데 ack·커밋 전에 연결이 끊겼다. at-least-once의 정상 동작이다.
- **대처**: 메시지 ID(또는 업무 키)로 멱등 처리 — 인박스 테이블, 유일 제약. 외부 부작용(메일·결제)은 멱등 키를 함께 보낸다([05](../05-idempotency-keys/2-summary.md), [reliability/13](../../reliability/13-idempotency/2-summary.md)).

### 4. 죽은 소비자가 메시지를 오래 붙잡는다 — 끊김 감지 지연 (⚠)

- **현상**: 소비자 서버가 전원 장애로 죽었는데 몇 분 동안 그 소비자 몫의 메시지가 처리되지 않는다.
- **보이는 형태**: RabbitMQ unacked가 줄지 않음, Kafka 해당 파티션 lag 증가, MQTT 세션이 살아 있는 것처럼 보임.
- **원인**: TCP는 상대가 사라진 것을 늦게 안다(RabbitMQ 문서: 리눅스 기본 약 11분). 앱 계층 하트비트가 꺼졌거나 너무 길다.
- **대처**: 하트비트를 켜고 적당히 짧게(RabbitMQ는 서버 제안 기본값이 60초이고 문서는 5~20초를 대부분 환경의 최적 범위로 든다. MQTT Keep Alive, Kafka `session.timeout.ms`). 너무 짧으면 GC 정지에도 끊기므로 처리 시간 분포를 보고 정한다.

### 5. 소비자 메모리가 터진다 — prefetch 무제한

- **현상**: 큐에 메시지가 몰리자 소비자 힙이 가득 찬다.
- **원인**: AMQP prefetch를 걸지 않아 브로커가 ack 안 된 메시지를 끝없이 밀어 넣었다.
- **대처**: `basic.qos` prefetch 설정(RabbitMQ 문서: 보통 100~300). Kafka는 pull이라 `max.poll.records` 등으로 한 번에 가져오는 양을 정한다.

## 핵심 문장

- 브로커는 생산자와 소비자를 시간·공간으로 떼어 놓는다. 대신 "언제 전달이 끝났나"(ack 위치)를 정해야 한다.
- 처리 전 ack는 유실(at-most-once), 처리 후 ack는 중복(at-least-once)을 낳는다. 실무 기본은 처리 후 ack + 멱등 소비다.
- MQTT QoS는 구간마다 따로이고, 구독자가 받는 QoS는 발행 QoS와 허락된 최대 QoS 중 작은 값이다. QoS 0은 응답·재전송이 없다.
- Kafka의 ack는 오프셋 커밋이다. 커밋하지 않으면 다시 받고(실험: m1부터 다시), 커밋하면 이어 받는다(m4부터).
- TCP만으로는 죽은 상대를 늦게 안다. 앱 계층 하트비트(MQTT Keep Alive, AMQP heartbeat, Kafka 세션 타임아웃)가 감지 시간을 정한다.

## 관련 주제·근거

- 선행
  - [09-async-apis-and-webhooks](../09-async-apis-and-webhooks/2-summary.md) · [18-api-style-selection](../18-api-style-selection/2-summary.md) — 영역 표: [curriculum](../curriculum.md)
  - distributed [17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) — 전달 보장과 커밋 순서 실험
- 후속·연결
  - distributed [18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md) · [21-kafka-internals](../../distributed/21-kafka-internals/2-summary.md) · [16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) · [19-message-types-channels-and-endpoints](../../distributed/19-message-types-channels-and-endpoints/2-summary.md)
  - [systems/kafka-consumer-failure](../../systems/kafka-consumer-failure/2-summary.md) — 기존 원고
  - reliability [13-idempotency](../../reliability/13-idempotency/2-summary.md) · [12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)
  - network [21-tcp-keepalive-and-user-timeout](../../network/21-tcp-keepalive-and-user-timeout/2-summary.md)
- 명세·문서
  - MQTT Version 5.0 OASIS Standard(2019-03-07) — 4.3 QoS 흐름, MQTT-3.1.2-22 Keep Alive × 1.5, MQTT-3.8.4-8 min QoS, 3.3.1.1 DUP <https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html>
  - RabbitMQ "AMQP 0-9-1 Model Explained" <https://www.rabbitmq.com/tutorials/amqp-concepts> · "Consumer Acknowledgements and Publisher Confirms" <https://www.rabbitmq.com/docs/confirms> · "Detecting Dead TCP Connections with Heartbeats" <https://www.rabbitmq.com/docs/heartbeats> · AMQP 0-9-1 명세 원문(GitHub 이전) <https://github.com/rabbitmq/amqp-0.9.1-spec>
  - Apache Kafka 4.1 — Protocol <https://kafka.apache.org/41/design/protocol/> · Producer configs(`acks`·`enable.idempotence`·`retries`·`delivery.timeout.ms`) <https://kafka.apache.org/41/configuration/producer-configs/> · Consumer configs(`enable.auto.commit`·`auto.commit.interval.ms`·`auto.offset.reset`·`session.timeout.ms`·`heartbeat.interval.ms`) <https://kafka.apache.org/41/configuration/consumer-configs/>
- 실험 목록
  - Kafka 소비자 그룹 두 개(커밋 없음 vs 기본 자동 커밋)로 3개씩 두 번 읽어 재전달·건너뜀 확인, `kafka-consumer-groups.sh --describe` — apache/kafka 4.1.0 단일 노드 KRaft 일회용 컨테이너(`--cpus=2`, 메모리 1GB 제한), 전용 네트워크. 사실 점검에서 같은 명령으로 다시 돌려 같은 출력
  - 생산자·소비자 기본값(`acks`·`enable.idempotence`·`retries`·`delivery.timeout.ms`·`enable.auto.commit`·`auto.commit.interval.ms`·`auto.offset.reset`·`session.timeout.ms`·`heartbeat.interval.ms`)은 사실 점검에서 같은 이미지의 kafka-clients 4.1.0 `ProducerConfig`·`ConsumerConfig` 설정 표를 출력해 대조했다
  - MQTT·AMQP는 쓸 수 있는 브로커 이미지가 없어 실험하지 않았다 — 명세·공식 문서로 대신했다
