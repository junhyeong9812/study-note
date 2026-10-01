# distributed/18-consumer-failure-handling — 컨슈머 실패 처리: 커밋 순서·재시도·DLT·poison pill·리밸런스 — 정리 (힌트)

## 해결하는 문제

발행 쪽이 메시지를 안전하게 로그에 넣었어도, 소비 쪽에서 세 가지가 일어난다.

```text
  [로그] ──poll──> 소비자 ──처리──> DB
                    │  ① 처리 도중 죽는다         → 어디부터 다시 읽나 (커밋 위치)
                    │  ② 이 메시지는 몇 번 해도 실패한다 → 뒤 메시지가 전부 막힌다 (poison pill)
                    │  ③ 처리가 너무 느리다        → 그룹이 "죽었다"고 보고 파티션을 뺏는다 (리밸런스)
```

- 발행 쪽 보장은 "로그에 들어갔다"까지다. "처리됐다"는 소비자가 만든다.
- 소비 쪽 설계는 결국 세 결정이다.
  - 처리와 커밋을 어떤 순서로 할까.
  - 실패한 메시지를 다시 할까, 치울까, 어디로 치울까.
  - 느린 처리를 그룹의 생존 판정과 어떻게 맞출까.

쉬운 예: 은행 창구다.
- 번호표 순서대로 부른다. 한 손님의 서류가 계속 반려되는데 창구 직원이 그 손님만 붙잡고 있으면 뒤 손님이 모두 기다린다.
- 그래서 "서류 미비" 손님은 옆 상담석으로 보내고 다음 번호를 부른다.

똑같은 구조다.\
같은 메시지를 무한히 재시도하면 파티션이 멈춘다. 영구 실패는 옆(DLT)으로 치우고 다음 오프셋으로 간다.

실무 예:
- 역직렬화가 안 되는 메시지 하나 때문에 파티션 lag이 몇 시간째 그대로다.
- 배치 처리가 길어진 날 컨슈머 로그에 `CommitFailedException`이 쏟아지고 같은 메시지가 반복 처리된다.

기초(Kafka는 pull·보존형이라 커밋 시점이 중심, 인박스, 재시도 토픽 계단, 리밸런싱 처방)는 원본 [systems/kafka-consumer-failure](../../systems/kafka-consumer-failure/2-summary.md)에 있다. 이 노트는 실험으로 그 동작을 확인하고 빈 곳을 채운다.

## 동작·원리

### 1. 커밋 순서 — 17번의 결론과 자동 커밋의 실제

17번 실험의 결론: 처리 전 커밋은 유실(at-most-once), 처리 후 커밋은 중복(at-least-once)이다([17번 §3](../17-queues-logs-and-delivery-semantics/2-summary.md)).

자동 커밋(`enable.auto.commit=true`, kafka-clients 4.1.0 기본값)은 어느 쪽일까? **처리 방식에 따라 갈린다.**

```text
  자동 커밋이 커밋하는 값 = "지금까지 poll()이 돌려준 위치"
  커밋하는 때           = poll() 안에서(auto.commit.interval.ms가 지났으면), close() 때, 리밸런스로 그룹에 다시 들어가기 직전

  (A) poll 루프 안에서 동기 처리                    (B) 처리를 다른 스레드로 넘기고 poll 계속
  poll → [0..49] 처리 0..34 ─X                    poll → [0..9] 넘김 → poll → [10..19] 넘김 → ... poll → [90..99]
       다음 poll 전에 죽음 → 이 배치는 커밋 안 됨         poll이 진행할 때마다 위치 커밋 (처리는 50건에서 멈춤) ─X
  재시작: 앞 커밋부터 → 중복 (at-least-once)          재시작: 100부터 → 50..99 유실 (at-most-once)
```

- KafkaConsumer javadoc(4.1): 자동 커밋도 at-least-once가 될 수 있다. 조건은 "poll()이 돌려준 데이터를 다음 poll() 호출이나 close() **전에** 모두 소비하는 것"이다. 아니면 커밋 위치가 소비 위치를 앞질러 레코드를 놓친다.

#### 실험: 자동 커밋 + 프로세스 강제 종료

- 100건 토픽, `auto.commit.interval.ms=100`. 크래시는 `Runtime.getRuntime().halt(1)`로 JVM을 즉시 끝냈다(`close()`를 부르지 않으므로 마지막 자동 커밋도 없다).
- (A) `max.poll.records=50`, poll 루프에서 레코드당 30ms 처리, 35건째에 halt.
- (B) `max.poll.records=10`, 처리를 단일 스레드 풀에 넘기고(레코드당 30ms) 계속 poll, 첫 레코드부터 1.5초 뒤 halt.

```java
// (B)의 핵심 — poll은 계속 앞으로 가고, 처리는 뒤에서 따라간다
for (ConsumerRecord<String,String> r : c.poll(Duration.ofMillis(100))) {
    ex.submit(() -> { sleep(30); done.incrementAndGet(); });
}
```

```text
(실험, Kafka 4.1.0 KRaft 단일 노드, kafka-clients 4.1.0, 2026-10-01)
[auto-sync] 35건 처리 후 강제 종료(halt)
[resume w18-g-sync] 커밋된 오프셋=없음(auto.offset.reset=earliest → 0부터)
[auto-async] 처리 완료 50건에서 강제 종료(halt), 그때 poll한 위치=100
[resume w18-g-async] 커밋된 오프셋=100 → 이 오프셋부터 다시 읽는다
```

- (A): 첫 배치를 처리하는 동안 다음 poll이 없어서 커밋이 한 번도 일어나지 않았다. 재시작하면 0부터 다시 읽고, 처리한 35건이 중복된다.
- (B): 처리는 50건에서 멈췄는데 커밋은 100까지 갔다. 50..99의 50건이 처리되지 않은 채 지나간다.
  - 50은 "1.5초 ÷ 레코드당 30ms"에서 나온 타이밍 값이라 실행마다 조금 다를 수 있다. 사실 점검 때 다시 돌렸을 때도 50·100이 나왔다. 커밋이 처리를 앞지른다는 모양은 같다.
- 참고: 원본 「오프셋 커밋 순서 함정」의 "자동 커밋은 사실상 처리 전 커밋(at-most-once)"은 (B)처럼 처리를 poll과 분리했을 때의 이야기다. poll 루프 안에서 동기로 처리하면 자동 커밋은 at-least-once다(위 javadoc과 실험 (A)).

### 2. 실패를 나누고 다르게 다룬다

```text
  실패 종류            예                                   다룰 곳
  ─────────────────────────────────────────────────────────────────────────────
  일시적(transient)    DB 커넥션 끊김, 타임아웃, 429, 락 대기     재시도 (백오프)
  영구적(permanent)    역직렬화 실패, 스키마 불일치, 검증 실패     재시도 없이 DLT
  모름                 NPE 같은 버그                          횟수 제한 재시도 후 DLT + 알림
```

- *poison pill*: 처리할 때마다 실패하는 메시지. 같은 오프셋을 계속 재시도하면 그 파티션의 뒤 메시지가 전부 멈춘다.
- *DLT(Dead Letter Topic)*: 끝까지 실패한 메시지를 따로 옮겨 두는 토픽. 옮긴 뒤 원래 오프셋을 커밋하고 다음으로 간다.

#### 실험: poison pill — 같은 오프셋 재시도 vs DLT

- 20건 토픽, 오프셋 10이 `BAD`(처리하면 예외).
- retry 정책: 실패하면 `seek(tp, 같은 오프셋)`으로 다시 읽는다. 데모라 5회에서 멈췄다(실서비스의 무한 재시도를 흉내).
- dlt 정책: 실패하면 `w18-poison-dlt`로 보내고 오프셋을 커밋한다.

```java
} catch (IllegalArgumentException e) {
    if (policy.equals("retry")) { c.seek(tp, r.offset()); continue outer; }   // 같은 메시지부터 다시
    dlt.send(new ProducerRecord<>("w18-poison-dlt", r.value())).get();       // 옮기고
    c.commitSync(Map.of(tp, new OffsetAndMetadata(r.offset() + 1)));         // 넘어간다
}
```

```text
(실험, Kafka 4.1.0 KRaft 단일 노드, 2026-10-01)
[poison-retry] 5회 실패, 이 데모는 여기서 멈춘다
[poison-retry] 정상 처리 10건, 실패 시도 5회, DLT로 보냄 0건, 커밋 오프셋=10, 끝 오프셋=20 → lag=10
[poison-dlt] 정상 처리 19건, 실패 시도 0회, DLT로 보냄 1건, 커밋 오프셋=20, 끝 오프셋=20 → lag=0
```

- retry: 오프셋 10에서 커밋이 멈췄다. 뒤의 정상 메시지 9건(11..19)이 하나도 처리되지 않았고 lag이 10에서 줄지 않는다.
- dlt: 정상 19건을 다 처리하고 `BAD` 1건만 DLT로 갔다.

#### 블로킹 재시도 vs 논블로킹 재시도

```text
  블로킹: 같은 스레드에서 기다렸다 다시           논블로킹: 재시도 토픽으로 넘기고 다음으로
  main: [9][10✗ 1s 2s 4s][11][12]           main:     [9][10✗→retry-1s][11][12]   ← 안 막힘
         순서 지킴 / 파티션 정지                  retry-1s: [10✗→retry-2s]  → ... → DLT
         max.poll.interval.ms 넘으면 리밸런스     같은 키의 10이 11·12보다 늦게 처리됨 → 순서 깨짐
```

- 순서가 중요하면(같은 계좌의 상태 전이) 논블로킹을 못 쓴다. 짧은 블로킹 재시도 후 DLT + 알림이 기본이다(원본 「재시도 계층 설계」).
- 블로킹 재시도의 총 대기 시간은 `max.poll.interval.ms`보다 짧아야 한다(다음 절).

### 3. 리밸런스 — 그룹은 언제 "죽었다"고 보나

```text
  (classic 프로토콜, kafka-clients 4.1.0 기본)
  하트비트 스레드 ──3s마다──> 그룹 코디네이터      session.timeout.ms(45s) 동안 끊기면 → 죽음
  poll() 호출 간격 ───────────────────────────    max.poll.interval.ms(5분)를 넘으면 → 스스로 그룹 탈퇴
                                                  → 파티션 재할당(정적 멤버는 세션 타임아웃 뒤) → 이 멤버의 commitSync는 실패
```

- 위 수치는 kafka-clients 4.1.0 기본값이다(`heartbeat.interval.ms`=3000, `session.timeout.ms`=45000, `max.poll.interval.ms`=300000, `max.poll.records`=500, `ConsumerConfig` 기본값 출력).
- 하트비트는 별도 스레드라 프로세스가 살아 있으면 계속 간다. 처리가 오래 걸려 poll이 늦는 "살아 있지만 진척 없는" 상태는 `max.poll.interval.ms`로 잡는다(javadoc "livelock").
- 그 시간을 넘기면 소비자가 스스로 그룹을 떠나고, 이후 `commitSync()`는 `CommitFailedException`을 던진다(javadoc).

#### 실험: 처리 시간 > max.poll.interval.ms

- `max.poll.interval.ms=3000`, `max.poll.records=5`. 5건을 받고 5초 동안 처리한 뒤 `commitSync()`.

```text
(실험, Kafka 4.1.0 KRaft 단일 노드, kafka-clients 4.1.0, 2026-10-01)
[slow] group.protocol=(기본값)
[slow] 5건 받음, 처리에 5초 걸림
[slow] 커밋 실패: CommitFailedException: Offset commit cannot be completed since the consumer is not part of an active group for auto partition assignment; it is likely that the consumer was kicked out of the group.
```

- 처리한 5건의 커밋이 실패했다. 이 파티션을 다음에 읽는 소비자(다른 멤버, 또는 다시 합류한 이 소비자)는 마지막 커밋부터 읽으므로 5건이 다시 처리될 수 있다. 실험 출력은 커밋 실패까지만 보여 준다.
- *리밸런스 폭풍*: 느린 처리 → 탈퇴 → 리밸런스 → 다시 받은 큰 배치도 느림 → 또 탈퇴. 그룹 전체가 리밸런스만 반복한다.
- 줄이는 장치
  - `max.poll.records`를 줄이거나 처리 시간을 줄인다. 또는 `max.poll.interval.ms`를 늘린다(장애 감지가 그만큼 늦어진다).
  - *정적 멤버십*: `group.instance.id`를 주면 재시작한 같은 인스턴스가 같은 멤버로 돌아온다. 더 긴 세션 타임아웃과 함께 쓰면 재시작마다 리밸런스가 일어나지 않는다(`group.instance.id` 설정 문서).
  - *협력적(cooperative) 리밸런스*: 옮겨야 할 파티션만 회수한다. 4.1.0 기본 `partition.assignment.strategy`는 `[RangeAssignor, CooperativeStickyAssignor]`다.
  - 새 그룹 프로토콜(KIP-848, `group.protocol=consumer`)은 Kafka 4.0에서 GA다(upgrade 노트). 다만 kafka-clients 4.1.0의 기본 `group.protocol`은 `classic`이다(기본값 출력).

## 쓰이는 자료구조·알고리즘

- **오프셋 커밋 = 파티션별 정수 하나** — 내부 토픽 `__consumer_offsets`에 (그룹, 토픽, 파티션) → 오프셋으로 저장된다. 커밋은 "이 번호 앞까지 끝났다"는 한 점이라, 중간 하나만 빼고 끝났다는 표현이 불가능하다. 그래서 실패 메시지는 커밋 전에 치워야(DLT) 다음으로 갈 수 있다.
- **재시도 큐(지연 토픽 계단)** — `main → retry-1s → retry-10s → retry-1m → DLT`. 토픽마다 지연이 고정된 FIFO라 우선순위 큐 없이 지연 재시도를 만든다. 대가는 키 순서.
- **지수 백오프 + 상한** — 대기 = min(초기값 × 배수^n, 상한). 일시 장애가 회복될 시간을 주면서 재시도가 몰리지 않게 한다.
- **파티션 할당(assignor)** — 그룹 멤버 집합이 바뀔 때마다 파티션→멤버 매핑을 다시 계산한다. sticky 계열은 이전 매핑과의 차이를 최소화한다.
- **인박스 = 처리한 ID 집합** — 재처리가 오면 유니크 제약으로 걸러 낸다([17번 §적용 3](../17-queues-logs-and-delivery-semantics/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. 자동 커밋을 쓸지 정한다. 처리를 poll 루프 안에서 동기로 하면 자동 커밋도 at-least-once다. 처리를 다른 스레드로 넘기면 반드시 수동 커밋으로 바꾸고 **처리 완료한 오프셋까지만** 커밋한다.
2. 처리 경로를 멱등하게 만든다(인박스·조건부 UPDATE). 리밸런스·재시작이 일어나면 중복이 온다.
3. 예외를 일시적/영구적으로 분류한다. 역직렬화 실패는 영구로 본다.
4. 재시도 정책: 순서가 필요하면 짧은 블로킹 재시도 → DLT. 순서가 필요 없으면 재시도 토픽.
5. DLT에 알림과 재처리 도구를 붙인다. 원본 토픽·파티션·오프셋·예외를 헤더에 남긴다.
6. `max.poll.records × 레코드당 최악 처리 시간 + 블로킹 재시도 총 대기` < `max.poll.interval.ms`를 확인한다.

### 2. 순수 kafka-clients — 분류 + DLT + 처리 후 커밋 (Java)

```java
for (ConsumerRecord<String, byte[]> r : c.poll(Duration.ofMillis(500))) {
    TopicPartition tp = new TopicPartition(r.topic(), r.partition());
    try {
        retryTransient(() -> handler.handle(decode(r.value())), 3, Duration.ofMillis(200)); // 짧은 블로킹 재시도
    } catch (PermanentFailure | TransientExhausted e) {
        ProducerRecord<String, byte[]> d = new ProducerRecord<>(r.topic() + ".DLT", r.key(), r.value());
        d.headers().add("orig-offset", Long.toString(r.offset()).getBytes())
                   .add("error", e.toString().getBytes());
        dltProducer.send(d).get();                         // DLT 저장을 확인한 뒤에야
    }
    c.commitSync(Map.of(tp, new OffsetAndMetadata(r.offset() + 1)));   // 다음으로 넘어간다
}
```

- 레코드마다 `commitSync`는 느리다. 배치 끝에서 한 번 커밋해도 된다. 그 대신 크래시 시 중복 창이 배치만큼 커진다.

### 3. Spring for Apache Kafka

- `DefaultErrorHandler` 기본: 실패한 레코드를 다시 시도하고, **10번 실패하면** 레코드를 ERROR로 로그하고 넘어간다. `DeserializationException`·`MessageConversionException`·`ClassCastException` 등은 *fatal*로 분류돼 재시도 없이 바로 복구자(recoverer)로 간다(Spring for Apache Kafka 참조 문서 "Handling Exceptions").
  - "로그하고 넘어간다"는 그 레코드를 버린다는 뜻이다. `DeadLetterPublishingRecoverer`를 주면 DLT로 보낸다.
- `@RetryableTopic`(논블로킹 재시도) 기본 백오프는 `FixedBackOffPolicy`, **최대 3회 시도, 1000ms 간격**이다. `attempts`는 첫 시도를 포함한다(참조 문서 "Non-Blocking Retries › Features").

```java
@RetryableTopic(attempts = "4",
        backOff = @BackOff(delay = 1000, multiplier = 3.0),
        exclude = { DeserializationException.class, ValidationException.class })  // 영구 실패는 바로 DLT
@KafkaListener(topics = "orders")
public void consume(OrderEvent e) { orderService.apply(e); }

@DltHandler
public void dlt(OrderEvent e) {
    alerts.notify("orders DLT", e.orderId());   // DLT는 알림 대상이다 (원본 위치는 kafka_dlt-original-* 헤더에 있다)
}
```

- 역직렬화는 리스너보다 앞의 `poll()` 단계에서 일어난다. 순수 kafka-clients 4.1은 이때 `RecordDeserializationException`(파티션·오프셋을 담음)을 던지고, 앱이 그 오프셋을 넘기지(`seek`) 않으면 같은 자리에서 계속 실패한다. Spring에서는 `ErrorHandlingDeserializer`로 감싸 실패를 리스너 쪽 오류 처리(fatal 분류 → DLT)로 넘긴다(참조 문서 "Handling Exceptions").

### 4. 진단 명령

```bash
# 파티션별 커밋 위치·lag — lag이 한 파티션만 그대로면 poison pill 의심
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group orders-app
# 멤버·할당·상태 — 리밸런스 반복 중이면 상태가 PreparingRebalance/CompletingRebalance를 오간다
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group orders-app --members
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group orders-app --state
# 멈춘 오프셋의 메시지 직접 보기
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic orders --partition 3 --offset 1042 --max-messages 1
```

## 장애 시나리오와 대처

### 1. 처리 전 커밋 → 유실 (⚠)

- **현상**: 주문 일부가 정산에 반영되지 않았는데 에러 로그도 없다.
- **보이는 형태**: 커밋 오프셋·lag은 정상이고, 원천 대비 처리 건수만 모자란다. 컨슈머 재시작·OOM 시각과 겹친다.
- **원인**: 처리 전에 커밋했거나, 자동 커밋인데 처리를 다른 스레드로 넘겼다. 실험 (B)에서 50건이 처리되지 않았는데 커밋은 100까지 갔다.
- **대처**: 처리 완료한 오프셋까지만 수동 커밋한다. 비동기 처리라면 파티션별로 "연속으로 끝난 가장 큰 오프셋"을 추적해 그 다음 번호를 커밋한다. 원천과 결과의 건수 대사(reconciliation)를 둔다.

### 2. 처리 후 커밋 실패 → 중복 (⚠)

- **현상**: 같은 메시지가 두 번 처리된다. 처리 시간이 긴 날에 몰린다.
- **보이는 형태**: `CommitFailedException: Offset commit cannot be completed since the consumer is not part of an active group ...`(앞부분만 옮김 — 전문은 §2 실험 출력, kafka-clients 4.1.0 `ConsumerCoordinator`). 커밋 요청이 브로커에서 `UNKNOWN_MEMBER_ID`·`ILLEGAL_GENERATION`으로 거절되는 경로에서는 같은 예외가 다른 문구 "Commit cannot be completed since the group has already rebalanced and assigned the partitions to another member. ..."(앞부분, `CommitFailedException` 기본 생성자)로 나온다. 클라이언트 로그에 `consumer poll timeout has expired ... max.poll.interval.ms ...` 경고.
- **원인**: 처리 중 `max.poll.interval.ms`를 넘겨 그룹에서 빠졌고, 처리한 결과의 커밋이 거부됐다. 새 소유자가 마지막 커밋부터 다시 처리할 수 있다. 실험에서 5초 처리 > 3초 한도로 재현됐다.
- **대처**: 처리 경로를 멱등하게 한다. `max.poll.records`를 줄이거나 처리 시간을 줄인다. 오래 걸리는 작업은 `pause()`하고 별도 스레드로 돌리되 poll은 계속 부른다.

### 3. poison 메시지로 파티션 정지 (⚠)

- **현상**: 한 파티션만 lag이 몇 시간째 그대로다. 다른 파티션은 정상이다.
- **보이는 형태**: `--describe`에서 그 파티션의 CURRENT-OFFSET이 고정. 같은 오프셋의 같은 예외 스택이 로그에 반복. 실험에서 커밋이 오프셋 10에 멈추고 lag 10이 줄지 않았다.
- **원인**: 영구 실패 메시지를 무한 재시도한다. 또는 `poll()` 단계의 역직렬화 실패(`RecordDeserializationException`)를 잡아 그 오프셋을 넘기는 코드가 없다.
- **대처**: 영구 실패는 재시도 없이 DLT로 보내고 커밋한다. 순수 클라이언트면 `RecordDeserializationException`의 `offset()` 다음으로 `seek`하고 원본 바이트를 DLT에 남긴다. Spring이면 `ErrorHandlingDeserializer`를 쓴다. 급하면 그 오프셋을 확인한 뒤 `--reset-offsets --to-offset <N+1>`로 건너뛰고, 건너뛴 메시지는 따로 보관해 재처리한다.

### 4. 리밸런스 폭풍 (⚠)

- **현상**: 처리량이 0에 가깝고 그룹 상태가 계속 리밸런스 중이다. 배포 때마다 몇 분씩 소비가 멈춘다.
- **보이는 형태**: `--describe --state`가 `PreparingRebalance`·`CompletingRebalance`를 오간다. 멤버 로그에 그룹 재합류·파티션 회수가 반복되고 `CommitFailedException`이 섞인다.
- **원인**: 배치 처리 시간이 `max.poll.interval.ms`를 넘는다. 또는 롤링 배포로 멤버가 하나씩 빠졌다 들어오며 매번 전체 리밸런스가 일어난다.
- **대처**: 배치 크기와 처리 시간을 맞춘다. `group.instance.id`(정적 멤버십)로 재시작이 리밸런스를 부르지 않게 한다. 협력적 assignor나 새 그룹 프로토콜(KIP-848)로 회수 범위를 줄인다.

### 5. DLT가 조용히 쌓인다

- **현상**: 몇 주 뒤 "일부 주문이 처리 안 됐다"는 문의로 DLT에 수천 건이 있는 것을 발견한다.
- **보이는 형태**: DLT 토픽의 log-end-offset이 꾸준히 오르는데 알림이 없다. Spring `DefaultErrorHandler` 기본 설정이면 DLT도 없이 ERROR 로그 한 줄만 남기고 넘어간다.
- **원인**: DLT를 종착지로 다뤘다. 유입 알림과 재처리 수단이 없다.
- **대처**: DLT 유입 건수에 알림을 건다. 원본 위치·예외를 헤더에 남기고, 원인을 고친 뒤 DLT를 원래 토픽으로 되돌리는 재처리 도구를 둔다. 재처리도 멱등 처리 경로를 탄다.

## 핵심 문장

- 커밋은 "이 번호 앞까지 끝났다"는 한 점이다. 처리보다 앞서면 유실, 뒤처지면 중복이다.
- 자동 커밋은 poll 시점에 그때까지 돌려준 위치를 커밋한다. poll 루프 안 동기 처리면 at-least-once, 처리를 다른 스레드로 넘기면 유실이 생긴다(실험: 중복 35건 vs 유실 50건).
- 영구 실패를 같은 오프셋에서 재시도하면 파티션 전체가 멈춘다. DLT로 옮기고 커밋해야 다음으로 간다.
- 논블로킹 재시도 토픽은 파티션을 안 막는 대신 같은 키의 순서를 깬다.
- 처리 시간이 `max.poll.interval.ms`를 넘으면 소비자가 그룹에서 빠지고 커밋이 거부된다. 그 배치는 다음에 그 파티션을 읽는 소비자가 다시 처리할 수 있다(정적 멤버 `group.instance.id`는 즉시 재할당되지 않고 세션 타임아웃 뒤 재할당 — 4.1 consumer 설정 문서).

## 관련 주제·근거

- 선행
  - [17-queues-logs-and-delivery-semantics](../17-queues-logs-and-delivery-semantics/2-summary.md) — 전달 보장, 커밋 순서 실험, 멱등 소비
  - 원본 [systems/kafka-consumer-failure](../../systems/kafka-consumer-failure/2-summary.md) — pull·보존형 전제, 인박스, 재시도 계층, 리밸런싱 함정
- 후속·연결
  - [21-kafka-internals](../21-kafka-internals/2-summary.md) — 오프셋·세그먼트·보존(보존이 짧으면 lag이 큰 그룹은 메시지를 잃는다)
  - [19-message-types-channels-and-endpoints](../19-message-types-channels-and-endpoints/2-summary.md) — Dead Letter·Invalid Message 채널, Competing Consumers
  - [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md) — 발행 쪽 재시도
- Kafka 4.1
  - KafkaConsumer javadoc — "Automatic Offset Committing", 자동 커밋의 at-least-once 조건, "Detecting Consumer Failures"(livelock, `max.poll.interval.ms`, `CommitFailedException`) <https://kafka.apache.org/41/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html>
  - `ConsumerConfig` 설정 문서 `group.instance.id`·`max.poll.interval.ms`, 기본값(kafka-clients 4.1.0 `configDef()` 출력)
  - 문서 4.5 The Consumer(Static Membership), 4.6 Message Delivery Semantics(소스 `docs/design.html` @ 4.1.0), Upgrade 4.0(KIP-848 GA) <https://kafka.apache.org/41/documentation.html>
- Spring for Apache Kafka 참조 문서(2026-10-01 열람판)
  - Handling Exceptions — `DefaultErrorHandler` 10회, fatal 예외 목록 <https://docs.spring.io/spring-kafka/reference/kafka/annotation-error-handling.html>
  - Non-Blocking Retries › Features — 기본 3회·1000ms <https://docs.spring.io/spring-kafka/reference/retrytopic/features.html>
- 교재: DDIA 1판 11장 — 소비자 오프셋, 처리 실패와 재전달
- 실험 목록(공용 `sn-dw-kafka` = Kafka 4.1.0 KRaft 단일 노드, `eclipse-temurin:21-jdk` + kafka-clients 4.1.0, `Consumer18.java`)
  - 자동 커밋 + 동기 처리 + halt(35건째): 커밋 없음 → 0부터 재처리(중복 35)
  - 자동 커밋 + 스레드풀 처리 + halt(1.5초): 처리 50, 커밋 100 → 유실 50
  - poison pill(오프셋 10): 같은 오프셋 재시도는 커밋 10·lag 10에서 정지, DLT 정책은 19건 처리 + DLT 1건·lag 0
  - `max.poll.interval.ms=3000`에서 5초 처리 → `CommitFailedException`
