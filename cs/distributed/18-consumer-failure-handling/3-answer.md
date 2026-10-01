# distributed/18-consumer-failure-handling — 정답

## 정답

### 1. 커밋이 한 점이라는 제약

- 커밋은 파티션마다 정수 하나다. "11..19는 끝났고 10만 빼고"를 표현할 수 없다.
- 그래서 실패한 메시지를 그 자리에 둔 채 뒤를 커밋하면 그 메시지는 잊힌다(유실). 커밋하지 않으면 뒤가 전부 막힌다.
- 다음으로 가려면 실패 메시지를 **커밋 전에 다른 곳으로 옮겨야** 한다. 그곳이 DLT·재시도 토픽이다.

### 2. 자동 커밋 + 즉사

| | 즉사 시점 커밋 | 재시작 지점 | 결과 |
|---|---|---|---|
| (a) 동기 처리 | 없음 | 0 (`auto.offset.reset=earliest`) | 중복 35건, 유실 0 |
| (b) 스레드풀 처리 | 100 | 100 | 유실 50건(50..99), 중복 0 |

- (a): 자동 커밋은 poll() 안에서 일어난다. 첫 배치를 처리하는 동안 다음 poll이 없었으므로 한 번도 커밋되지 않았다.
- (b): poll은 처리와 상관없이 앞으로 갔고, 그때마다 돌려준 위치가 커밋됐다.
- 실험 출력: `커밋된 오프셋=없음` / `처리 완료 50건 ... poll한 위치=100`, `커밋된 오프셋=100`.

### 3. "자동 커밋 = at-most-once"의 경계

- 맞는 경우: 처리를 poll과 분리해(다른 스레드·비동기) poll이 처리보다 앞서 가는 경우. 실험 (b).
- 틀린 경우: poll이 돌려준 레코드를 다음 poll·close 전에 모두 처리하는 경우. 이때 커밋 위치는 처리 위치를 앞지르지 않아 at-least-once다. 실험 (a).
- javadoc(4.1): 자동 커밋도 at-least-once를 줄 수 있으며, 조건은 "각 poll()이 돌려준 데이터를 다음 호출 전, 또는 close 전에 모두 소비"하는 것이다. 어기면 커밋 위치가 소비 위치를 앞질러 레코드를 놓친다.

### 4. poison pill — 재시도 vs DLT

- 같은 오프셋 재시도: 커밋 오프셋 10에서 멈춘다. lag은 10(끝 20 − 10)에서 줄지 않는다. 11..19의 정상 9건도 처리되지 않는다.
- DLT: 정상 19건 처리, `BAD` 1건은 DLT로, 커밋 오프셋 20, lag 0.
- 실험 출력이 그대로다: `커밋 오프셋=10 ... lag=10` / `DLT로 보냄 1건, 커밋 오프셋=20 ... lag=0`.

### 5. 블로킹 vs 논블로킹 재시도

| | 지키는 것 | 잃는 것 |
|---|---|---|
| 블로킹(같은 스레드에서 대기 후 재시도) | 파티션·키 순서 | 그동안 파티션 전체 정지, 대기가 길면 `max.poll.interval.ms` 초과 → 리밸런스 |
| 논블로킹(재시도 토픽) | 메인 파티션 진행 | 실패 메시지가 같은 키의 뒤 메시지보다 늦게 처리됨(순서) |

- 계좌 상태 전이처럼 순서가 의미를 바꾸면 논블로킹을 못 쓴다. 짧은 블로킹 재시도 → DLT + 알림. 단 DLT로 넘기고 뒤 메시지를 계속 처리하면 순서는 이미 깨진다. 같은 키 순서가 필수면 그 키의 뒤 메시지도 보류(정지·함께 격리)한 뒤 원인 수정 후 순서대로 재처리한다.

### 6. 처리 시간 > max.poll.interval.ms

- `commitSync()`가 `CommitFailedException`을 던진다. 실험 메시지: `Offset commit cannot be completed since the consumer is not part of an active group for auto partition assignment; it is likely that the consumer was kicked out of the group.`
- 소비자가 한도를 넘겨 스스로 그룹을 떠났다. 파티션을 다음에 읽는 소비자(다른 멤버 또는 다시 합류한 이 소비자)는 마지막 커밋부터 읽으므로 이 5건을 **다시 처리**할 수 있다(중복). 실험은 커밋 실패까지만 관찰했다. 정적 멤버(`group.instance.id`)라면 즉시가 아니라 세션 타임아웃 뒤 재할당된다(4.1 consumer 설정 문서).

### 7. 하트비트 vs max.poll.interval.ms

- 하트비트(별도 스레드)는 **프로세스·네트워크가 죽은 것**을 잡는다. `session.timeout.ms` 동안 하트비트가 없으면 죽은 것으로 본다.
- `max.poll.interval.ms`는 **살아 있지만 진척이 없는 것**(livelock, 처리가 너무 느림)을 잡는다. 하트비트는 계속 가도 poll이 안 오면 탈퇴한다.
- kafka-clients 4.1.0 기본값: `heartbeat.interval.ms`=3000, `session.timeout.ms`=45000, `max.poll.interval.ms`=300000, `max.poll.records`=500.

### 8. Spring DefaultErrorHandler 기본 동작

- 계속 실패하는 레코드: 재시도하다 **10번 실패하면** ERROR로 로그하고 넘어간다(그 레코드는 버려진다).
- 역직렬화 실패(`DeserializationException`) 등 fatal 예외: 재시도 없이 바로 복구자로 간다. 기본 복구자는 로그만 남긴다.
- 조용한 유실인 이유: 오프셋은 넘어갔고, 남는 것은 로그 한 줄이다. 알림도 재처리 경로도 없다.
- 막는 법: `DeadLetterPublishingRecoverer`로 DLT에 보낸다. DLT 유입에 알림을 걸고, 원본 위치(`kafka_dlt-original-*` 헤더)로 재처리 도구를 만든다.

### 9. 롤링 배포 때 리밸런스

- 볼 것: `kafka-consumer-groups.sh --describe --group … --state`가 리밸런스 상태를 오가는지, `--members`의 멤버 수 변화, 클라이언트 로그의 그룹 재합류·파티션 회수 반복, `CommitFailedException`.
- 줄이는 설정
  - `group.instance.id`(정적 멤버십) + 재시작 시간보다 긴 세션 타임아웃 → 같은 인스턴스가 돌아오면 리밸런스 없이 같은 파티션을 받는다.
  - 협력적 할당(`CooperativeStickyAssignor`) 또는 새 그룹 프로토콜(`group.protocol=consumer`, KIP-848 — Kafka 4.0 GA, 4.1.0 클라이언트 기본은 `classic`) → 옮길 파티션만 회수.
  - 배치 크기·처리 시간을 `max.poll.interval.ms` 안에 맞춘다.
- 반복 처리는 리밸런스가 남기는 정상 결과다. 처리 경로를 멱등하게 한다.

### 10. 한 파티션만 lag 고정

- 원인 후보: poison 메시지를 무한 재시도, `poll()` 단계 역직렬화 실패(`RecordDeserializationException`)를 넘기는 코드 없음, 그 파티션 처리 중 외부 호출이 매달려 있음.
- 확인
  - `kafka-consumer-groups.sh --describe --group …` → 그 파티션 CURRENT-OFFSET이 고정인지.
  - 같은 오프셋의 같은 예외가 로그에 반복되는지.
  - `kafka-console-consumer.sh --partition P --offset N --max-messages 1`로 그 메시지를 직접 본다.
- 응급: 메시지를 따로 보관한 뒤 그룹을 멈추고 `--reset-offsets --to-offset N+1 --execute`로 건너뛴다.
- 근본: 실패를 일시적/영구적으로 분류하고 영구 실패는 DLT로 보내 커밋한다. 역직렬화 실패를 잡는 경로(`RecordDeserializationException.offset()` 다음으로 `seek`, Spring은 `ErrorHandlingDeserializer`)를 둔다. DLT 알림을 건다.
