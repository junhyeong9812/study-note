# distributed/34-message-routing-and-transformation — 정답

## 정답

### 1. Pipes and Filters의 이점과 공유 상태

- 얻는 것(EIP, Azure Pipes and Filters)
  - 필터를 다시 조합해 새 파이프라인을 만든다(재사용).
  - 필터 순서를 바꾸거나 빼거나 더한다. 필터 자체는 고치지 않는다.
  - 느린 필터만 여러 인스턴스로 늘린다(처리량은 가장 느린 필터가 정한다). 무거운 필터는 다른 하드웨어에 둔다.
- 공유 상태가 생기면
  - 독립 확장이 사라진다. 인스턴스를 늘려도 공유 행·맵에서 경합한다.
  - 재배열 자유가 사라진다. 필터 순서가 공유 상태를 읽고 쓰는 순서를 바꿔 결과가 달라질 수 있다.
  - 대처: 문맥은 메시지에 싣고, 꼭 필요한 상태는 주인 단계 하나에 모으거나 키로 파티셔닝한다.

### 2. 세 라우터 비교

| | 출력 | 수신자를 정하는 것 |
|---|---|---|
| Content-Based Router | 여러 채널 중 **하나** | 메시지 내용(필드 존재·값) |
| Message Filter | 채널 **하나**(통과 또는 버림) | 조건 |
| Recipient List | 목록의 채널 **여럿**에 사본 | 메시지마다 계산한 수신자 목록 |

- 근거: EIP 각 패턴 요약.
- Scatter-Gather = 요청을 여러 수신자에게 뿌리는 쪽(Recipient List 또는 Pub-Sub 채널) + 응답을 모으는 Aggregator. Recipient List로 뿌리면 수신자를 통제하고, Pub-Sub으로 뿌리면 통제를 내려놓는다(경매 방식).

### 3. Aggregator의 세 가지와 "모두 기다림"의 약점

- 세 가지(EIP): 상관(어느 메시지가 한 묶음인가), 완료 조건(언제 내보내나), 집계 알고리즘(어떻게 합치나).
- 완료 전략 다섯: Wait for All, Time Out, First Best, Time Out with Override, External Event.

```text
  주문 o-7 → Splitter → 조각 1 ─────▶ 도착 ✔
                       조각 2 ─────▶ 도착 ✔
                       조각 3 ──✘ (유실)
  Aggregator 버퍼: { o-7: [1, 2] } ── 기다림 ── 기다림 ── ... (끝나지 않음)
```

- 조각 하나가 빠지거나 늦으면 묶음 전체가 멈춘다. EIP는 제한 시간 안에 다 오지 않으면 오류를 내야 한다고 적는다. 비동기 흐름에서는 "얼마나 기다려야 유실인가"를 정하기 어렵다는 점도 적는다.

### 4. 완료 조건 없는 Aggregator의 버퍼

(실험, Java 21 결정적 시뮬레이션(seed 42), 2026-10-01 — 출력 일부 발췌, 전체는 서머리 2절)

```text
  timeout=false after  25000 orders: buffered groups=1477
  timeout=false after  50000 orders: buffered groups=2981
  timeout=false after  75000 orders: buffered groups=4418
  timeout=false after 100000 orders: buffered groups=5872
aggregator timeout=false completed=94125  timed-out->error channel=0  groups still buffered=5872
  timeout=true  after 100000 orders: buffered groups=153
aggregator timeout=true  completed=94125  timed-out->error channel=5719  groups still buffered=153
```

- 예상치: 묶음이 미완성일 확률 1 − 0.98³ ≈ 5.88% → 약 5,880개. 실험 5,872개.
- 트래픽이 두 배면 미완성 묶음도 대략 두 배로 쌓인다. 실험에서 2.5만 → 10만 주문 동안 1,477 → 5,872로 비례해 늘었다. 끝나지 않는 묶음이라 시간이 갈수록 계속 커진다.
- 타임아웃(첫 조각 뒤 5,000틱)을 더하면 버퍼가 150~180개 근처에 머문다. 5,719개는 오류 채널로 나가 보정할 수 있다. 완료 건수(94,125)는 같다.

### 5. Kafka 크기 한도

(실험, Kafka 4.1.0 KRaft 단일 노드, 2026-10-01)

```text
org.apache.kafka.common.errors.RecordTooLargeException: The message is 2000088 bytes when serialized which is larger than 1048576, which is the value of the max.request.size configuration.
exit=0
```

- 프로듀서 기본 `max.request.size`(1,048,576바이트)에 걸려 `RecordTooLargeException`. 직렬화 크기는 2,000,088바이트였다.
- 콘솔 프로듀서의 종료 코드는 0이었다. 종료 코드만 보는 스크립트는 실패를 놓친다.
- 프로듀서 한도만 5MB로 올리면 브로커 기본 `message.max.bytes`(1,048,588바이트, 로컬 확인)에 걸린다.

```text
org.apache.kafka.common.errors.RecordTooLargeException: The request included a message larger than the max message size the server will accept.
exit=0
```

- 두 경우 모두 오프셋은 늘지 않았다(`w34-orders:0:1` 그대로).

### 6. Claim Check의 순서와 수명

- 저장소 쓰기와 보관증 발행은 다른 시스템이라 한 트랜잭션이 아니다(Azure Claim Check).
- 올바른 순서: payload 저장 → 성공 확인 → 보관증 발행 → 발행 결과 확인.
- 반대로 하거나 저장 실패를 확인하지 않으면, 소비자는 **풀 수 없는 참조**를 받는다. 로컬 실험에서 저장 명령이 `ERR syntax error`로 실패했는데 참조가 발행됐고, 소비자가 그 키를 조회하자 `STRLEN 0`이었다.
- 저장 뒤 발행 전에 실패하면 고아 payload가 남는다. 정리 작업이 필요하다. 재시도로 같은 보관증이 두 번 올 수 있으니 소비자는 멱등이어야 한다.
- 수명: payload 삭제 주인을 정하고, 메시지 만료·보존 기간과 맞춘다. 유효한 보관증이 지워진 payload를 가리키지 않게 한다(Azure).
- 무결성: 보관증에 해시를 넣어 소비자가 확인한다(실험: `sha(payload)=be8889d3b8893c11 expected=be8889d3b8893c11`).

### 7. Resequencer와 힙

- 필요한 연산은 "버퍼에서 가장 작은 순번 보기·꺼내기"와 "임의 순번 넣기"다. 최소 힙은 둘 다 O(log n)이고 맨 위를 O(1)에 본다. 맨 위가 다음 기대 순번이면 꺼내 내보내고 반복한다.
- 순번 하나가 오지 않으면 그 뒤 전부가 힙에 묶인다. 실험(seed 7)에서 7번이 빠지자 `emitted=[1, 2, 3, 4, 5, 6]  held in heap=13 (waiting for #7)`.
- 풀어 주기: 간격 타임아웃으로 빠진 번호를 건너뛰고 오류 채널에 기록한다. 실험에서 그 뒤 8~20번이 순서대로 나갔다. Camel의 스트림 모드도 간격 감지와 타임아웃을 쓴다. 앞 단계 DLQ를 함께 보고 빠진 메시지를 보정한다.

### 8. 변환기 수와 공용 모델의 함정

- 직접 변환: n(n − 1). 앱 6개 → 30개, 2개 → 2개.
- 공용 모델: 2n(앱마다 들어오는 쪽·나가는 쪽). 앱 6개 → 12개, 2개 → 4개. 3개면 6 vs 6으로 같다. 근거: EIP Canonical Data Model.
- 앱이 적으면 공용 모델이 오히려 많고, 많을수록 유리하다.
- 전사 범위로 강제하면: 필드 하나 추가에도 참여 팀 전부의 합의·배포가 필요해진다. 팀들이 `extra` 맵 같은 우회 필드를 쓰기 시작해 모델의 의미가 흐려진다. 대처는 경계 계약(Published Language)으로 범위를 좁히고, 내부 모델은 팀별로 두고, 계약에 버전과 하위 호환 규칙을 두는 것이다.

### 9. Aggregator OOM 진단

- 볼 것
  - 지표: 버퍼에 있는 묶음 수, 가장 오래된 묶음 나이, 완료·타임아웃 건수. 묶음 수가 트래픽에 비례해 늘고 줄지 않으면 미완성 묶음 누적이다.
  - 힙 덤프: 상관 키 맵(`Map<correlationId, List<...>>`)이 가장 큰 보유자인지, 그 안의 묶음 생성 시각이 오래됐는지.
  - 앞 단계: Splitter 이후 유실·DLQ로 빠진 조각이 있는지.
- 원인: 완료 조건이 "다 모임" 하나뿐이라 조각이 빠진 묶음이 영원히 남는다.
- 고침: 완료 조건을 둘 이상(크기 + 시간). 시간 초과 묶음은 오류 채널로 보내 보정한다. 버퍼 묶음 수·가장 오래된 묶음 나이에 경보를 건다. 재시작에서도 묶음을 잃으면 안 되면 영속 저장소에 둔다(Camel `AggregationRepository` 같은 구조).
