# distributed/19-message-types-channels-and-endpoints — 정답

## 정답

### 1. 명령 → 이벤트로 바꾸면

```text
  명령: 주문 ──PayOrder──▶ 결제 / ──AddPoint──▶ 포인트 / ──SendMail──▶ 메일   (주문이 받는 쪽을 안다)
  이벤트: 주문 ──OrderPlaced──▶ [토픽] ──▶ 결제·포인트·메일·(새) 쿠폰           (받는 쪽이 구독한다)
```

- 명령 구조에서는 발행자가 "누가 무엇을 할지"를 쥔다. 기능이 늘 때마다 발행자 코드와 배포가 따라온다.
- 이벤트 구조에서는 구독자가 "무엇에 반응할지"를 정한다. 구독자를 추가해도 발행자는 그대로다. 의존 방향이 뒤집힌다.
- 명령으로 남길 단계: 결과가 꼭 필요하고 책임자가 하나인 일. 예를 들어 "이 카드로 3000원 승인"은 결제 서비스 하나가 맡고, 주문 흐름이 그 결과를 기다린다.
- 이벤트 연쇄만으로 흐름을 짜면 전체 흐름이 한곳에 보이지 않는다는 비용이 있다(23번 주제).

### 2. 세 종류의 구분 기준

- 구분은 **의미와 책임**이다. 바이트 형식으로는 구분되지 않는다. EIP도 "명령 전용 메시지 타입은 없고, 명령을 담은 평범한 메시지"라고 적는다.
  - Command: 보낸 쪽이 할 일을 정한다.
  - Event: 일어난 사실만 알린다. 반응은 받는 쪽이 정한다.
  - Document: 데이터를 넘긴다. 무엇을 할지는 받는 쪽이 정한다.
- EIP의 Event vs Document 차이는 **시점과 내용**이다.
  - Event는 시점이 중요하고 내용은 덜 중요하다. 빈 이벤트도 많다. Message Expiration이 도움이 된다고 적는다.
  - Document는 내용이 중요하고 시점은 덜 중요하다. Guaranteed Delivery를 고려하고, 만료는 대개 고려 대상이 아니라고 적는다.

### 3. 공유 응답 채널의 짝짓기

(실험, Java 21 단일 프로세스 시뮬레이션, 2026-10-01)

```text
replies=100  FIFO matching wrong=85  correlation-id matching wrong=0  unmatched pending=0
replies=100  FIFO matching wrong=88  correlation-id matching wrong=0  unmatched pending=0
replies=100  FIFO matching wrong=95  correlation-id matching wrong=0  unmatched pending=0
```

- 순서로 짝지으면 100건 중 85~95건이 틀렸다(실행마다 다르다. 점검 재실행 12회에서는 80~96건). 응답자가 여럿이고 처리 시간이 다르면 응답 순서가 요청 순서와 달라진다.
- correlation ID로 짝지으면 0건이다. 응답자가 요청 ID를 응답의 correlation ID로 복사하고, 요청자가 대기표에서 찾는다.
- Return Address(응답 채널을 요청 헤더에 적기)와 함께 쓰면 응답자는 채널도 짝도 하드코딩하지 않는다.

### 4. Dead Letter vs Invalid Message

| | 누가 판단하나 | 예 |
|---|---|---|
| Dead Letter Channel | **메시징 시스템**이 배달할 수 없거나 배달하면 안 된다고 판단 | 만료, SQS 수신 횟수 한도 초과 |
| Invalid Message Channel | **수신자**가 받았지만 뜻을 모름 | 파싱 실패, 스키마 불일치 |

- 근거: EIP Dead Letter Channel·Invalid Message Channel 요약.
- 섞으면 "배달·재시도 문제(인프라)"와 "내용 오류(생산자 버그)"가 한 통에 들어간다. 원인을 가르기 어렵고, 재처리 방법도 다르다(배달 실패는 다시 보내면 될 수 있지만 내용 오류는 생산자를 고쳐야 한다).

### 5. 경쟁 소비자 vs 키 레인

(실험, Java 21 단일 프로세스 시뮬레이션, 2026-10-01)

```text
run 1  competing consumers:  354 / 2000 orders regressed   key-hash lanes: 0 / 2000
run 2  competing consumers:  334 / 2000 orders regressed   key-hash lanes: 0 / 2000
run 3  competing consumers:  339 / 2000 orders regressed   key-hash lanes: 0 / 2000
```

- (A) 2,000건 중 대략 330~360건이 역행했다(실행마다 다르다. 점검 재실행 12회에서는 314~376건). 같은 주문의 이벤트가 서로 다른 소비자에서 동시에 처리되고, 늦게 끝난 옛 이벤트가 새 상태를 덮어썼다.
- (B) 0건이다. 같은 주문의 이벤트는 한 레인의 한 스레드에서 발행 순서대로 처리된다.
- 이것이 Sequential Convoy다. 묶음(주문) 안은 차례로, 묶음끼리는 병렬로.

### 6. Kafka의 Sequential Convoy와 파티션 증설

- 키가 있고 파티션을 지정하지 않으면 기본 분할기가 `toPositive(murmur2(키 바이트)) % 파티션 수`로 파티션을 고른다(Kafka 4.1 `BuiltInPartitioner.partitionForKey`).
- 파티션 하나는 그룹 안 소비자 하나만 읽고, 파티션 안 순서는 쓴 순서다. 그래서 같은 키의 레코드는 한 소비자가 오프셋 순으로 받는다. 받은 레코드를 여러 작업 스레드에 넘기면 처리 순서는 다시 섞이므로, 소비자도 키(파티션) 단위로 직렬 처리해야 한다.
- 로컬 실험(Kafka 4.1.0)에서 `order-1`~`order-6`의 이벤트가 키별로 한 파티션에만, 오프셋 순으로 들어갔다.
- 파티션 수를 3 → 6으로 늘리면 `% 3`이 `% 6`이 되어 같은 키가 다른 파티션으로 갈 수 있다.
  - 옛 레코드는 옛 파티션에, 새 레코드는 새 파티션에 있다. 두 파티션을 서로 다른 소비자가 읽으면 새 레코드가 옛 레코드보다 먼저 처리될 수 있다.
  - 그래서 순서가 중요한 토픽은 파티션 수를 처음에 넉넉히 잡거나, 증설 시 옛 파티션을 다 소비한 뒤 넘어가는 절차를 둔다. 소비자 쪽 버전 검사도 함께 둔다.

### 7. 보관 기간 vs 유효 시한

- `retention.ms`는 **브로커가 레코드를 얼마나 보관하나**다. 이 명령이 언제까지 의미 있는지가 아니다. 보관 기간 안이면 30분 지난 명령도 그대로 소비된다. Kafka 4.1에는 메시지별 만료가 없으므로 `expiresAt` 헤더를 넣고 소비자가 검사한다.
- RabbitMQ: 메시지별 `expiration`(밀리초 문자열)을 지원하고, 큐 TTL과 둘 다 있으면 작은 값을 쓴다. 메시지별 TTL로 만료된 메시지는 **큐의 맨 앞에 왔을 때** 버려지거나 dead-letter된다(브로커는 이미 만료된 메시지를 배달하지 않는다. 다만 소켓에 쓴 뒤 도착 전에 만료되는 경합은 있다고 문서가 적으므로 소비자 쪽 검사도 둔다). 만료 메시지가 아직 만료되지 않은 메시지 뒤에 쌓여 있을 수 있다(RabbitMQ 문서 "Time-To-Live and Expiration").

### 8. 우선순위 기아

- 의심할 것: 소비자 풀 하나가 high 큐가 빌 때만 low를 읽는 구성. high 도착률이 처리 능력 이상이면 low는 처리되지 않는다(Azure Priority Queue 문서의 "lower-priority messages being continually delayed").
- 확인: low 큐 길이·가장 오래된 메시지 나이, high 큐가 비는 순간이 있는지, 소비자 처리율 대비 high 도착률.
- 대처: 우선순위별 소비자 풀 분리(low에도 최소 풀), 에이징, 입구 부하 깎기·처리 능력 증설.
- 에이징이 공짜가 아닌 이유(실험, Java 21 결정적 시뮬레이션, 과부하 1.2건/틱 도착·1건/틱 처리):

```text
strict   high done=1000  low done=0  low still waiting=200  avg low wait=- ticks
aging    high done=863  low done=137  low still waiting=63  avg low wait=248 ticks
```

- 에이징은 low 137건을 처리했지만 high 처리가 1,000 → 863건으로 줄었다. 과부하에서는 처리 능력 총량이 같으므로 누군가 기다린다. 우선순위는 누가 기다릴지를 정할 뿐이다.

### 9. 복구 뒤 낡은 명령 일괄 실행

- 원인: 명령에 유효 시한이 없었다. 소비자는 30분 전 명령과 방금 명령을 구분할 수 없었다. Kafka라면 보관 기간 안의 레코드는 그대로 전달된다.
- 겉봉(헤더) 층: 시한이 의미 있는 메시지에 `expiresAt`(또는 생성 시각 + 허용 지연)을 넣는다. 브로커가 만료를 지원하면(RabbitMQ `expiration`, Service Bus TTL) 함께 설정하고 dead-letter 채널을 지정한다.
- 소비자 코드 층: 처리 직전에 `now > expiresAt`이면 실행하지 않고 DLQ로 보낸다. 실험에서 만료 검사가 없으면 10건 모두 실행, 있으면 3건 실행·7건 DLQ였다. 업무 상태 검사(예약이 이미 취소됐으면 무시)를 함께 두면 시한이 없는 메시지도 막을 수 있다.
