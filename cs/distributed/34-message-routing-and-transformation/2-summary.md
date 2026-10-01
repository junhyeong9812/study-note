# distributed/34-message-routing-and-transformation — 메시지 라우팅·변환: 파이프·필터, 라우터, Aggregator, Claim Check — 정리 (힌트)

## 해결하는 문제

19번에서 메시지 종류와 채널을 정했다. 실제 통합 흐름에서는 메시지가 한 채널에서 다른 채널로 그냥 넘어가지 않는다.

```text
  주문 메시지 하나가 겪는 일
  [수신] → 복호화 → 인증 → 중복 제거 → 품목별로 쪼개기 → 품목마다 다른 창고로 보내기
        → 창고 응답 모으기 → 순서 되맞추기 → 회계 시스템 형식으로 바꾸기 → [송신]
```

- 이 단계를 한 서비스 안에 몰아 넣으면 재사용·순서 변경·단계별 확장이 어렵다(Azure Pipes and Filters 문서의 "monolithic module" 문제).
- 단계를 나누면 "어디로 보낼까(라우팅)", "어떻게 모을까(집계)", "어떤 형식으로 바꿀까(변환)"가 각각 별도 부품이 된다. EIP(Hohpe–Woolf 2003)의 Message Routing·Message Transformation 패턴이 그 부품 목록이다.

쉬운 예: 택배 분류 센터다.
- 컨베이어(파이프) 위로 상자가 흘러가고, 각 작업대(필터)는 한 가지 일만 한다.
- 주소를 보고 지역별 레일로 보낸다(라우터). 묶음 상자는 풀어서 낱개로 보낸다(Splitter).
- 같은 주문의 상자가 다 오면 한 번에 내보낸다(Aggregator). 한 상자가 안 오면 언제까지 기다릴지 정해야 한다.
- 너무 큰 짐은 레일에 올리지 않고 보관소에 맡긴 뒤 보관증만 보낸다(Claim Check).

똑같은 구조다.\
메시지 통합에서도 부품마다 고유한 장애가 있다. 기다림이 끝나지 않는 Aggregator, 브로커 한도를 넘는 큰 메시지, 공유 상태 때문에 병렬화가 안 되는 필터, 모든 팀을 묶는 공용 모델이 그 예다.

실무 예:
- 주문을 품목별로 나눠 처리하고 다시 모으는 Aggregator의 메모리가 매일 조금씩 늘다가 OOM이 난다.
- 첨부 파일이 포함된 이벤트를 Kafka로 보내다 `RecordTooLargeException`이 나는데, 배치 스크립트는 성공으로 끝난다.
- "전사 공통 Customer 모델"에 필드 하나를 추가하려면 열 개 팀의 합의가 필요하다.

## 동작·원리

### 1. Pipes and Filters — 작은 단계를 채널로 잇는다

```text
  ┌─────────┐ 파이프 ┌──────┐ 파이프 ┌──────────┐ 파이프 ┌──────────┐
  │ 복호화   │──────▶│ 인증  │──────▶│ 중복 제거 │──────▶│ 다음 단계 │
  └─────────┘       └──────┘       └──────────┘       └──────────┘
   필터: 입력 포트 하나, 출력 포트 하나. 다른 필터를 모른다.
```

- *Filter*: 입력 파이프에서 메시지를 받아 처리하고 출력 파이프로 내보내는 단계. 인터페이스가 같아 순서를 바꾸거나 빼거나 더할 수 있다(EIP Pipes and Filters).
- *Pipe*: 필터를 잇는 채널. 라우팅이나 다른 로직을 하지 않는다(Azure Pipes and Filters).
- 처리량은 가장 느린 필터가 정한다. 느린 필터만 여러 인스턴스로 늘릴 수 있다(Azure).
- 조건: 필터는 독립적이고 대개 상태가 없다(Azure: "typically stateless").
  - 필터들이 같은 DB 행·같은 메모리 맵을 고치면, 한 필터를 여러 인스턴스로 늘릴 때 그 공유 상태가 경합 지점이 된다. 순서를 바꾸면 결과가 달라질 수도 있다. 파이프라인의 장점(독립 확장·재배열)이 사라진다.
- 실패 처리: 필터가 결과를 다음 파이프에 낸 뒤 "완료" 표시 전에 죽으면, 다시 실행된 인스턴스가 같은 메시지를 또 낸다. 그래서 필터는 멱등이어야 하고, 파이프라인은 중복을 걸러야 한다(Azure "Idempotency"·"Repeated messages").

### 2. 라우팅 — 어디로 보내나

```text
  Content-Based Router          Message Filter              Recipient List
  msg ─▶ [type?] ┬▶ widget 창고   msg ─▶ [조건?] ─▶ 통과      msg ─▶ [수신자 계산] ┬▶ 신용평가 A
                 ├▶ gadget 창고               └▶ 버림                            └▶ 신용평가 B
                 └▶ 기타          (출력 채널 하나)              (메시지 내용 기준, 동적 목록)

  Splitter                     Aggregator                     Resequencer
  주문{3품목} ─▶ 품목1·2·3        품목1·2·3 ─▶ 주문 결과 하나      5,2,4,1,3 ─▶ 1,2,3,4,5

  Scatter-Gather = Recipient List(또는 Pub-Sub) + Aggregator     Routing Slip = 메시지에 경로 목록을 붙임
```

- *Content-Based Router*: 메시지 내용(필드 존재·값)을 보고 채널 하나로 보낸다. EIP는 라우터가 자주 고쳐야 하는 지점이 되기 쉬우니 규칙을 관리하기 쉽게 만들라고 적는다.
- *Message Filter*: 출력 채널이 하나인 라우터. 조건에 맞으면 통과, 아니면 버린다(EIP).
- *Recipient List*: 수신자 목록을 메시지마다 계산하고, 목록의 각 채널에 사본을 보낸다. 예: 큰 주문만 신용평가 기관 여러 곳에 묻기(EIP).
- *Splitter*: 반복 요소를 가진 메시지 하나를 요소별 메시지로 쪼갠다(EIP).
- *Aggregator*: 관련 메시지를 모아 완전한 묶음이 되면 메시지 하나로 내보내는 **상태 있는 필터**(EIP). 설계할 세 가지:
  - *상관(correlation)*: 어떤 메시지가 한 묶음인가(예: `orderId`).
  - *완료 조건(completeness condition)*: 언제 내보내나.
  - *집계 알고리즘*: 어떻게 하나로 합치나.
- EIP가 든 완료 조건 전략: 모두 올 때까지 기다림(Wait for All), 시간 제한(Time Out), 첫 번째 응답(First Best), 시간 제한 + 기준 넘는 응답이 오면 조기 종료(Time Out with Override), 외부 사건(External Event).
  - "모두 기다림"은 메시지 하나가 빠지거나 늦으면 묶음 전체가 멈춘다. EIP는 제한 시간 안에 다 오지 않으면 오류를 내야 한다고 적는다.
  - Apache Camel 문서(aggregate EIP)는 "완료 조건은 필수이며 설정해야 한다"고 적는다. 여러 조건을 섞으면 먼저 충족된 것이 이긴다.
- *Resequencer*: 순서가 뒤섞여 도착한 관련 메시지를 버퍼에 모아 정해진 순서로 내보내는 상태 있는 필터. 출력 채널도 순서를 지켜야 한다(EIP).
  - Camel은 배치 모드(기본: 최대 100개 또는 1초마다 모아 정렬)와 스트림 모드(다음 기대 순번이 오면 바로 내보냄, 간격 감지)를 둔다(Camel resequence EIP 문서).
- *Scatter-Gather*: 요청을 여러 수신자에게 뿌리고 Aggregator로 응답을 하나로 모은다. Recipient List로 보내면 수신자를 통제하고, Pub-Sub으로 보내면 누가 응답할지 통제를 내려놓는다(경매 방식, EIP).
- *Routing Slip*: 처리 단계 목록을 메시지에 붙인다. 각 단계는 일을 마치고 목록의 다음 단계로 보낸다. 단계 순서가 메시지마다 다를 때 쓴다(EIP).

#### 실험: 완료 조건 없는 Aggregator의 메모리

주문 10만 개를 3조각으로 나눠 보내고, 조각마다 2%를 유실시켰다. (A) "3조각이 다 오면 내보냄"만, (B) 여기에 "첫 조각 뒤 5,000틱이 지나면 부분 묶음을 오류 채널로" 타임아웃을 더했다.

```java
List<Part> g = buffer.computeIfAbsent(p.orderId(), k -> new ArrayList<>());   // 상관 키 → 버퍼
g.add(p);
if (g.size() == p.total()) { buffer.remove(p.orderId()); completed++; }        // 완료 조건: 크기
if (timeout && o % 1000 == 0)                                                  // 주기적으로 오래된 묶음을 내보낸다
    buffer.entrySet().removeIf(e -> now - e.getValue().get(0).at() > 5_000);    // (실제 코드는 iterator로 세면서 지운다)
```

(실험, Java 21 eclipse-temurin 결정적 시뮬레이션(seed 42), 2026-10-01)

```text
  timeout=false after  25000 orders: buffered groups=1477
  timeout=false after  50000 orders: buffered groups=2981
  timeout=false after  75000 orders: buffered groups=4418
  timeout=false after 100000 orders: buffered groups=5872
aggregator timeout=false completed=94125  timed-out->error channel=0  groups still buffered=5872
  timeout=true  after  25000 orders: buffered groups=163
  timeout=true  after  50000 orders: buffered groups=181
  timeout=true  after  75000 orders: buffered groups=147
  timeout=true  after 100000 orders: buffered groups=153
aggregator timeout=true  completed=94125  timed-out->error channel=5719  groups still buffered=153
```

- 조각 하나라도 빠질 확률은 1 − 0.98³ ≈ 5.9%다. 10만 주문 중 5,872개가 미완성으로 남았다.
- 타임아웃이 없으면 미완성 묶음이 트래픽에 비례해 계속 쌓였다(1,477 → 5,872). 영원히 완료되지 않는 묶음이다.
- 타임아웃이 있으면 버퍼가 150~180개 근처에서 머물렀다. 5,719개는 오류 채널로 나가 사람이나 보정 로직이 처리할 수 있다.

#### 실험: 힙으로 만든 Resequencer와 빠진 번호

순번 1~20 중 7번을 빼고 섞어 보냈다. 최소 힙에 넣고 맨 위가 "다음 기대 순번"이면 내보낸다.

```java
heap.add(s);
while (!heap.isEmpty() && heap.peek() == next) { out.add(heap.poll()); next++; }
```

(실험, Java 21 결정적 시뮬레이션(seed 7), 2026-10-01)

```text
resequencer arrivals=[15, 13, 18, 19, 17, 2, 10, 20, 4, 5, 16, 14, 6, 8, 12, 1, 11, 3, 9]
  emitted=[1, 2, 3, 4, 5, 6]  held in heap=13 (waiting for #7)
  gap timeout: skip #7 -> error channel
  emitted=[1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]  held in heap=0
```

- 7번이 오지 않자 8~20번 13개가 힙에 묶였다. 빠진 번호 하나가 뒤 전체를 막는다.
- "간격 타임아웃"으로 7번을 건너뛰고 오류 채널에 기록하자 나머지가 순서대로 나갔다.

### 3. 변환 — 어떤 형식으로 바꾸나

```text
  Message Translator   A 형식 ─▶ [변환] ─▶ B 형식            (GoF Adapter의 메시징판)
  Content Enricher     {zip} ─▶ [조회: 계산·환경·외부 시스템] ─▶ {zip, state}
  Content Filter       {큰 문서} ─▶ [필요한 필드만] ─▶ {작은 문서}
  Claim Check          {큰 payload} ─▶ [저장소에 맡김] ─▶ {claimCheck=키}  ...  [키로 찾아옴] ─▶ {payload}
  Normalizer           형식 X·Y·Z ─▶ [라우터 → 형식별 Translator] ─▶ 공통 형식
  Canonical Data Model 앱마다 "자기 형식 ↔ 공통 모델" 변환기 하나씩
```

- *Message Translator*: 한 데이터 형식을 다른 형식으로 바꾸는 필터. EIP는 GoF의 Adapter와 같은 역할이라고 적는다.
- *Content Enricher*: 메시지 안의 키로 외부 자원을 조회해 빠진 데이터를 덧붙인다. 출처는 계산, 환경(예: 현재 시각), 다른 시스템(가장 흔함)이다(EIP).
  - 다른 시스템을 조회하므로 그 시스템의 지연·장애가 파이프라인에 들어온다.
- *Claim Check*: payload를 영속 저장소에 맡기고, 뒤 단계에는 그것을 찾을 키(보관증)만 보낸다. 필요한 단계가 Content Enricher로 되찾는다(EIP).
  - Azure 문서의 주의점: 저장소 쓰기와 보관증 발행은 서로 다른 시스템이라 원자적이지 않다. **payload 쓰기가 성공한 뒤에만** 보관증을 발행한다. 그 반대 순서면 소비자가 풀 수 없는 참조를 받는다. 쓰기 뒤 발행 전에 실패하면 고아 payload가 남는다. 재시도로 같은 보관증이 두 번 올 수 있으니 멱등 소비자로 받는다.
  - payload 수명의 주인을 정한다. 메시지 만료와 payload 보존 기간을 맞춰, 유효한 보관증이 지워진 데이터를 가리키지 않게 한다(Azure).
- *Normalizer*: 의미는 같고 형식만 다른 메시지를 라우터로 형식을 판별해 각 Translator로 보낸 뒤 공통 형식으로 맞춘다. EIP의 예는 1,700곳이 넘는 제휴사의 시청 정보를 받는 유료 방송 사업자다.
- *Canonical Data Model*: 어떤 앱에도 속하지 않는 공통 데이터 모델을 두고, 각 앱은 그 형식으로 주고받는다(EIP).
  - EIP의 계산: 앱끼리 서로 다 주고받으면 직접 변환기는 n(n − 1)개, 공통 모델은 2n개다. 앱 2개면 2 vs 4, 3개면 6 vs 6, 6개면 30 vs 12.
  - 앱이 많을수록 유리하다. 대가는 공통 모델 자체가 참여하는 팀 전부의 의존 대상이 된다는 것이다(아래 장애 4).
- *Messaging Bridge*: 서로 다른 메시징 인프라(MSMQ·RabbitMQ·Service Bus 등)의 대응 채널을 이어 메시지를 옮긴다(EIP, Azure). 두 기술의 제약을 함께 감안해야 한다. Azure 예: 최대 메시지 크기가 MSMQ 4MB, Azure Storage queue 64KB.

#### 실험: Kafka 메시지 크기 한도와 Claim Check

공용 Kafka 4.1.0에 토픽 `w34-orders`를 만들고 콘솔 프로듀서로 2,000,000바이트 한 줄을 보냈다. 프로듀서 기본 `max.request.size`는 1,048,576바이트(Kafka 4.1 producer 설정 문서), 브로커 기본 `message.max.bytes`는 1,048,588바이트다(로컬 `kafka-configs --describe --all`로 확인).

(실험, Kafka 4.1.0 KRaft 단일 노드, 2026-10-01)

```text
--- 2,000,000 bytes
[2026-10-01 01:01:39,392] ERROR Error when sending message to topic w34-orders with key: null, value: 2000000 bytes with error: (org.apache.kafka.clients.producer.internals.ErrorLoggingCallback)
org.apache.kafka.common.errors.RecordTooLargeException: The message is 2000088 bytes when serialized which is larger than 1048576, which is the value of the max.request.size configuration.
exit=0
--- 900,000 bytes
w34-orders:0:1
```

- 2MB는 프로듀서 쪽에서 거절됐다. 900KB는 들어가 오프셋 1까지 찼다.
- 콘솔 프로듀서의 종료 코드는 **0**이었다. 스크립트가 종료 코드만 보면 실패를 놓친다.

프로듀서 한도만 5MB로 올리면 이번에는 브로커가 거절한다.

```text
org.apache.kafka.common.errors.RecordTooLargeException: The request included a message larger than the max message size the server will accept.
exit=0
w34-orders:0:1
```

Claim Check로 바꿨다. payload를 Redis(`w34:blob:<sha256 앞 16자>`, 객체 저장소 대용)에 맡기고 참조만 보냈다.

```text
consumed: {"orderId":"o-77","claimCheck":"w34:blob:be8889d3b8893c11","bytes":2000000} (75 bytes)
STRLEN 2000000
sha(payload)=be8889d3b8893c11 expected=be8889d3b8893c11
w34-orders:0:3
```

- 브로커에는 75바이트만 들어갔다. 소비자는 키로 2,000,000바이트를 되찾고 해시로 무결성을 확인했다.
- 첫 시도에서 payload 저장 명령이 문법 오류(`ERR syntax error`)로 실패했는데, 스크립트가 그 결과를 확인하지 않고 참조 메시지를 발행했다. 그 메시지(오프셋 1)의 보관증으로 조회하면 `STRLEN 0`이었다. "payload 쓰기 성공을 확인한 뒤에만 발행"이 왜 필요한지 그대로 보여 준 실패다.

### 4. 관측 — Wire Tap과 Message Store

```text
  Wire Tap:       [입력] ─▶ (고정 Recipient List) ┬▶ 원래 채널 → 원래 소비자
                                                 └▶ 보조 채널 → 감시·디버깅
  Message Store:  모든 메시지(또는 핵심 필드: ID·채널·시각)를 중앙 저장소에 복사
```

- *Wire Tap*: 출력이 둘인 고정 Recipient List. 원래 흐름을 바꾸지 않고 P2P 채널의 메시지를 들여다본다(EIP).
- *Message Store*: 메시지 정보를 중앙에 모아 보고·분석한다. 사본 전송은 "보내고 잊기"라 주 흐름을 늦추지 않지만 네트워크 트래픽이 는다. 그래서 전체가 아니라 메시지 ID·채널·시각 같은 핵심 필드만 남기기도 한다(EIP).
- 개인정보가 든 메시지를 그대로 복사하면 보조 채널이 새 유출 경로가 된다. 탭에서 민감 필드를 빼거나(Content Filter), 민감 payload는 Claim Check로 빼 둔다(Azure Claim Check의 보안 용도).

## 쓰이는 자료구조·알고리즘

- **파이프라인(함수 합성)** — 필터 = 입력 하나·출력 하나인 함수, 파이프라인 = 함수 합성. 상태가 없으면 단계별로 독립 확장·재배열할 수 있다.
- **상관 키 → 버퍼 맵(Aggregator)** — `Map<correlationId, List<Message>>`. 완료 조건이 묶음을 꺼내고, 타임아웃이 오래된 묶음을 치운다. 영속 저장소에 두면 재시작에도 묶음이 남는다(Camel의 `AggregationRepository`). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **재정렬 버퍼 = 최소 힙(Resequencer)** — 들어온 순번을 힙에 넣고, 맨 위가 다음 기대 순번이면 꺼낸다. 삽입·꺼내기 O(log n). 빠진 번호는 간격 타임아웃으로 건너뛴다. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **규칙 표(라우터)** — Content-Based Router의 조건 → 채널 표. 규칙이 많아지면 설정 가능한 규칙 엔진이 된다(EIP).
- **콘텐츠 해시(Claim Check)** — payload의 해시를 키나 검증값으로 쓰면 같은 payload의 중복 저장을 줄이고 무결성을 확인할 수 있다.

## 적용 — 풀어나가는 법

**1) 흐름을 그림으로 먼저 그린다.** 각 상자에 EIP 이름을 붙인다(Splitter, Router, Aggregator…). 이름이 붙으면 그 부품의 장애(완료 조건·순서·크기)를 체크리스트로 바로 확인할 수 있다.

**2) Aggregator는 세 가지를 코드에 명시한다.**

```java
// Apache Camel Java DSL 예시 — 상관 키, 집계 전략, 완료 조건 두 개(먼저 충족된 쪽이 이김)
from("kafka:order-items")
    .aggregate(header("orderId"), new ItemsToOrder())     // 상관 + 집계 알고리즘
        .completionSize(header("itemCount"))              // 다 모이면
        .completionTimeout(30_000)                        // 그 키에 30초 동안 새 조각이 없으면 부분 묶음으로
    .to("direct:order-assembled");
```

- Camel의 `completionTimeout`은 **비활동** 타임아웃이다. 그 상관 키에 정해진 시간 동안 새 메시지가 집계되지 않으면 완료한다(Camel aggregate EIP 문서). 위 실험의 "첫 조각 뒤 5,000틱"과는 기준점이 다르다. 조각이 띄엄띄엄 계속 오면 묶음이 더 오래 남을 수 있다.
- 타임아웃으로 나온 부분 묶음은 정상 결과와 구분한다(헤더에 완료 사유를 남기고 별도 채널로).
- 버퍼를 메모리에만 두면 재시작에서 묶음을 잃는다. 잃으면 안 되는 흐름은 영속 저장소를 쓴다.
- 지표: 버퍼에 있는 묶음 수, 가장 오래된 묶음의 나이, 타임아웃 수.

**3) 큰 payload는 크기로 분기한다.**

```java
// 생산자: 크기가 기준을 넘으면 Claim Check
byte[] body = serialize(order);
if (body.length > 256 * 1024) {                                    // 기준은 예시 값
    String key = "orders/" + sha256Hex(body);
    objectStore.put(key, body);                                    // 1) 먼저 맡기고 성공을 확인
    producer.send(new ProducerRecord<>("orders", order.id(),
        serialize(new ClaimCheck(key, body.length, sha256Hex(body))))).get();   // 2) 그다음 보관증 발행, 실패 확인
} else {
    producer.send(new ProducerRecord<>("orders", order.id(), body)).get();
}
```

- `send(...).get()`처럼 전송 결과를 확인한다. 위 실험에서 콘솔 프로듀서는 실패해도 종료 코드 0이었다.
- payload 보존 기간 ≥ 메시지 보존 기간 + 재처리 여유. 누가 언제 지우는지 정한다.
- 진단:

```bash
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-name 1 --describe --all | grep message.max.bytes
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type topics --entity-name orders --describe   # 토픽별 max.message.bytes
kafka-get-offsets.sh --bootstrap-server localhost:9092 --topic orders                                    # 실제로 들어갔나
```

**4) 필터는 상태를 밖으로 뺀다.** 필터 안의 공유 맵·공유 행 갱신을 없애고, 필요한 문맥은 메시지에 싣는다(Azure "Context and state"). 상태가 꼭 필요한 단계(Aggregator·Resequencer)는 상관 키로 파티셔닝해 키마다 한 인스턴스가 맡게 한다(19번 Sequential Convoy).

**5) 공통 모델은 범위를 좁힌다.** 전사 하나의 모델 대신, 팀 사이 경계에서 공개 계약(Published Language)을 두고 각 팀 내부 모델은 자유롭게 둔다. 변환은 경계의 Translator가 맡는다.

## 장애 시나리오와 대처

### 1. Aggregator 완료 조건 부재 → 영원히 기다리는 부분 묶음이 메모리에 누적

- **현상**: 집계 서비스 메모리가 하루 단위로 조금씩 늘다가 OOM으로 재시작한다. 재시작 뒤 일부 주문이 "처리 중"에서 멈춰 있다.
- **보이는 형태**: 힙 덤프에 상관 키 맵이 크다. 버퍼 묶음 수가 트래픽에 비례해 증가한다. 위 실험에서 타임아웃 없이 10만 주문 뒤 5,872개 묶음이 남았다.
- **원인**: 조각 하나가 유실·지연되면 "모두 기다림" 조건이 끝내 충족되지 않는다. 타임아웃·외부 사건 같은 두 번째 완료 조건이 없었다.
- **대처**: 완료 조건을 둘 이상 둔다(크기 + 시간). 시간 초과 묶음은 오류 채널로 보내 보정한다(실험: 버퍼 150~180개 유지, 5,719개 오류 채널). 버퍼 묶음 수와 가장 오래된 묶음 나이를 경보로 건다. 재시작에 견디려면 영속 저장소에 둔다.

### 2. 큰 payload를 브로커에 직접 → 크기 한도 초과·브로커 디스크 압박 (Claim Check 누락)

- **현상**: 특정 주문(첨부 많은 주문)만 이벤트가 나가지 않는다. 또는 브로커 디스크·복제 트래픽이 갑자기 늘고 다른 토픽 지연이 오른다.
- **보이는 형태**: 프로듀서 로그 `RecordTooLargeException: The message is ... larger than 1048576, which is the value of the max.request.size configuration`, 프로듀서 한도를 올렸으면 `... larger than the max message size the server will accept`. 도구의 종료 코드는 0일 수 있다(실험).
- **원인**: Kafka 4.1 기본 한도(프로듀서 1,048,576바이트, 브로커 1,048,588바이트)를 넘는 payload를 그대로 실었다. 한도를 올려 통과시키면 큰 메시지가 브로커 메모리·디스크·복제 대역폭을 차지한다(Azure Claim Check "Broker resource pressure").
- **대처**: 기준 크기를 넘으면 Claim Check(객체 저장소 + 참조 메시지). 순서: payload 저장 성공 확인 → 참조 발행 → 전송 결과 확인. 참조에 해시를 넣어 무결성을 확인한다. 압축이나 Splitter + Aggregator도 대안이다(Azure "Alternatives").

### 3. 필터 사이 공유 상태 → 파이프라인 병렬화 불가

- **현상**: 느린 단계 인스턴스를 늘렸는데 처리량이 오르지 않거나, 늘린 뒤부터 결과가 가끔 틀린다.
- **보이는 형태**: 공유 DB 행 락 대기, 같은 캐시 키에 대한 경합, 인스턴스 수와 무관하게 평평한 처리량 그래프.
- **원인**: 필터들이 같은 상태(카운터·맵·행)를 읽고 고친다. 필터가 독립이 아니게 되어 확장하면 경합이, 재배열하면 결과 변화가 생긴다.
- **대처**: 상태는 메시지에 싣거나, 상태 있는 단계를 키로 파티셔닝해 키마다 한 인스턴스가 맡게 한다. 꼭 공유해야 하는 상태는 그 상태의 주인 단계 하나로 모은다. 필터는 멱등으로 만든다(재실행·중복 대비).

### 4. Canonical 모델 강제 → 전사 공용 모델이 모든 팀 변경을 막는다

- **현상**: 한 팀이 주문에 필드 하나를 추가하려고 몇 주째 아키텍처 회의를 한다. 팀들이 공용 모델을 우회하는 비공식 필드(`extra`·`metadata` 맵)를 쓰기 시작한다.
- **보이는 형태**: 공용 스키마 저장소의 변경 요청 대기열이 길다. 공용 모델 버전 업에 전 팀 배포가 묶인다. 스키마 안에 팀별 선택 필드가 계속 붙는다.
- **원인**: 변환기 수(2n vs n(n − 1))를 줄이는 이점만 보고 공용 모델을 전사 범위로 강제했다. 참여 팀 전부가 같은 모델에 의존하므로 한 팀의 변경 비용이 다른 팀들로 퍼진다.
- **대처**: 공용 모델의 범위를 경계 계약으로 좁힌다(필요한 팀 사이의 Published Language). 내부 모델은 팀마다 두고 경계 Translator로 바꾼다. 계약은 버전을 두고 하위 호환 규칙(필드 추가만 허용 등)을 정한다.

### 5. Resequencer가 빠진 번호에서 멈춤

- **현상**: 특정 키의 처리가 멈추고 그 뒤 메시지가 쌓인다. 같은 키의 다른 메시지는 다 도착해 있다.
- **보이는 형태**: Resequencer 버퍼 크기 증가, "다음 기대 순번"이 한 값에 고정. 위 실험에서 7번이 오지 않아 13개가 묶였다.
- **원인**: 앞 단계에서 한 메시지가 유실·DLQ로 빠졌는데 Resequencer는 그 번호를 계속 기다린다.
- **대처**: 간격 타임아웃(일정 시간 뒤 빠진 번호를 건너뛰고 기록), 앞 단계 DLQ와 Resequencer 상태를 함께 본다. 건너뛴 번호는 보정 흐름으로 처리한다.

## 핵심 문장

- Pipes and Filters는 처리를 독립 필터로 나눠 채널로 잇는다. 필터가 상태를 공유하면 독립 확장·재배열이라는 장점이 사라진다.
- 라우터는 "어디로", 변환기는 "어떤 형식으로", Aggregator·Resequencer는 "언제 내보낼지"를 맡는다. 마지막 둘은 상태 있는 필터라 버퍼를 가진다.
- Aggregator에는 완료 조건이 둘 이상 필요하다. "모두 기다림"만 두면 조각 하나의 유실이 영원히 남는 버퍼가 된다.
- Kafka 4.1 기본 한도는 프로듀서 1,048,576바이트·브로커 1,048,588바이트다. 큰 payload는 Claim Check로 빼고, 저장 성공을 확인한 뒤 보관증을 발행한다.
- 공통 데이터 모델은 변환기 수를 n(n − 1)에서 2n으로 줄이지만, 범위가 넓으면 여러 팀의 변경을 한데 묶는 병목이 된다.

## 관련 주제·근거

- 선행
  - [19-message-types-channels-and-endpoints](../19-message-types-channels-and-endpoints/2-summary.md) — 메시지 종류·채널·Sequential Convoy
  - [23-orchestration-vs-choreography](../23-orchestration-vs-choreography/2-summary.md). 기존 원고 [systems/orchestration-choreography](../../systems/orchestration-choreography/2-summary.md)
- 연결
  - domain-modeling `18-context-mapping`(Published Language·ACL) — 미작성, [domain-modeling/curriculum](../../domain-modeling/curriculum.md)
  - [18-consumer-failure-handling](../18-consumer-failure-handling/2-summary.md)(DLQ·poison), [30-batch-and-stream-processing](../30-batch-and-stream-processing/2-summary.md)(윈도·워터마크로 모으기)
  - reliability `13-idempotency` → [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)
  - [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- 책·패턴 문서
  - G. Hohpe, B. Woolf, 『Enterprise Integration Patterns』, Addison-Wesley 2003 — 패턴 요약 페이지: Pipes and Filters, Content-Based Router, Message Filter, Recipient List, Splitter, Aggregator(상관·완료 조건·집계, 완료 전략 5가지), Resequencer, Scatter-Gather, Routing Slip, Message Translator, Content Enricher, Claim Check, Normalizer(1,700 제휴사), Canonical Data Model(2/4·6/6·30/12), Messaging Bridge, Wire Tap, Message Store <https://www.enterpriseintegrationpatterns.com/patterns/messaging/>
  - Azure Architecture Center — Pipes and Filters <https://learn.microsoft.com/en-us/azure/architecture/patterns/pipes-and-filters> · Claim Check <https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check> · Messaging Bridge <https://learn.microsoft.com/en-us/azure/architecture/patterns/messaging-bridge>
- 제품 문서
  - Apache Camel — Aggregate EIP("Completion is mandatory", 여러 완료 조건 중 먼저 충족된 것, `AggregationRepository`) <https://camel.apache.org/components/next/eips/aggregate-eip.html> · Resequence EIP(배치 기본 100개·1초, 스트림 모드) <https://camel.apache.org/components/next/eips/resequence-eip.html> (원문: apache/camel `core/camel-core-engine/src/main/docs/modules/eips/pages/`)
  - Apache Kafka 4.1 Producer configs — `max.request.size` 기본 1048576 <https://kafka.apache.org/41/generated/producer_config.html> · 브로커 `message.max.bytes` 기본 1048588(로컬 4.1.0 `kafka-configs --describe --all`)
- 실험(scratchpad, 2026-10-01)
  - Kafka 4.1.0 KRaft 단일 노드(토픽 `w34-orders`) — 2,000,000바이트 전송: 프로듀서 한도 거절, 프로듀서 한도 5MB로 올리면 브로커 거절, 두 경우 모두 콘솔 프로듀서 종료 코드 0, 900,000바이트는 성공
  - Claim Check — payload를 공용 Redis 7.4.9(`w34:blob:<sha>`)에 맡기고 75바이트 참조만 Kafka로, 소비 뒤 STRLEN·해시 확인. 저장 실패 뒤 발행된 참조는 `STRLEN 0`
  - `AggregatorResequencer.java` — 주문 10만 × 3조각·2% 유실에서 완료 조건(크기만 vs 크기+타임아웃)별 버퍼 묶음 수, 최소 힙 Resequencer의 빠진 번호 대기와 간격 타임아웃(Java 21, 결정적 seed)
