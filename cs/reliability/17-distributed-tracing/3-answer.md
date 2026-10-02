# reliability/17-distributed-tracing — 정답

## 정답

### 1. 왜 트레이스인가

- 지표는 서비스별 집계라 요청 하나를 따라가지 못한다. 로그는 서비스마다 따로 있어 "누가 누구를 불렀고 누가 기다렸나"라는 인과가 없다.
- 트레이스는 요청 하나의 작업 구간(스팬)을 **부모 ID로 이은 트리**로 만든다. 시간축에 펼치면 전체 시간을 잡아먹은 구간(임계 경로)이 보인다.

### 2. traceparent 풀기

| 칸 | 값 | 뜻 |
|---|---|---|
| version | `00` | 현재 형식 |
| trace-id | `bd93…5e8e` (16바이트) | 트레이스 전체의 ID |
| parent-id | `671fbca3f1e17e51` (8바이트) | **보낸 쪽의 스팬 ID**(실험에서 `POST payment-svc /pay` CLIENT 스팬). 받는 쪽은 이것을 부모로 삼는다 |
| trace-flags | `03` | `01` sampled + `02` random trace-id(Trace Context Level 2) |

### 3. 스레드풀과 컨텍스트

(실험, OTel Java SDK 1.66.0)

```text
score-fraud (wrap 안 함) [INTERNAL] trace=06478e span=4624cb
GET /checkout [SERVER] trace=bd9397 span=7bdde6
  └ score-fraud (Context.wrap) [INTERNAL] trace=bd9397 span=672d86
```

- 그냥 넘기면: 작업 스레드의 Context가 비어 있어 **새 trace(06478e)의 루트**가 된다.
- 감싸면: 제출 시점의 Context가 따라가 `GET /checkout`의 자식이 된다(같은 trace bd9397).

### 4. baggage와 스팬 속성

- 들어가지 않는다. 실험에서 baggage 범위 안의 `SELECT orders` 스팬에 tenant가 없었다. baggage는 전파되는 값이고, 스팬 속성으로 넣는 것은 따로 해야 한다(이 SDK 구성에서).
- 하류는 `baggage` 헤더를 extract해 `Baggage.fromContext(ctx).getEntryValue("tenant")`로 읽는다. 실험의 `POST /pay` 스팬은 그 값을 직접 속성으로 넣어 `tenant=acme`가 찍혔다.

### 5. baggage 한도와 금지

- **하한(최소 요구)**이다. 결과가 64개 이하·8192바이트 이하면 모든 항목을 전파해야 한다(MUST). 넘으면 버릴 수 있다(MAY). 구현은 더 큰 한도를 둘 수 있다.
- 넣지 말 것: 이메일·토큰·개인정보. baggage는 하류 호출마다 실려 외부 API로도 나갈 수 있다(W3C Baggage 5절 Privacy). 또 밖에서 온 baggage는 꾸밀 수 있으므로 권한 판단 근거로 쓰지 않는다.

### 6. 배치 소비와 span link

- 첫 메시지를 부모로 삼으면: 메시지 1의 트레이스에 메시지 2·3의 처리 시간까지 들어간다. 메시지 2·3의 트레이스에는 처리 단계가 없다.
- 기본 방법: 처리 스팬은 생성 컨텍스트를 부모로 두지 않고, **메시지마다 그 생성 컨텍스트로 link**를 건다. 스팬은 부모가 하나뿐이라 배치에서는 링크가 유일한 연결 방법이다(OTel Messaging spans, Status: Development).

```text
process orders (batch 3) [CONSUMER] trace=436889 span=8ba34a links=[b55961/33ff82, 725b2d/f1fbfe, 8e4eee/6a9e4c]
```

### 7. head 샘플링 결과

(실험, 에러 여부 시드 고정 — trace ID는 무작위라 남는 수는 실행마다 다르다)

```text
기록된 트레이스 999/10000, 그중 에러 트레이스 25/212, 자식 스팬 999 (부모와 같은 결정)
```

- 남는 트레이스 약 10%(999, 점검 재실행 913·1007). 에러 트레이스는 212개 중 25개(약 12%, 재실행 20·26개) — 에러도 10% 안팎만 남는다.
- 자식은 `parentBased`라 부모의 sampled 결정을 따른다. 자식 스팬 수 = 루트 수(매 실행). `TraceIdRatioBased` 자체도 trace ID로 결정적으로 정하므로 같은 SDK 구현·같은 비율이면 같은 결정이다. 언어·버전이 다른 SDK 사이 일치는 명세가 보장하지 않는다(OTel 명세 호환성 경고).

### 8. head vs tail

| | head | tail |
|---|---|---|
| 결정 시점 | 루트 시작 | 스팬을 모은 뒤(기본 `decision_wait` 30s) |
| 장점 | 싸다, 앱에서 버리므로 전송량도 준다 | 에러·느린 트레이스를 골라 남긴다 |
| 단점 | 결과를 모름 → 에러 트레이스 대부분 유실 | 수집기 메모리, 전부 보낸 뒤 버림 |

- 수집기 여러 대: 한 트레이스의 스팬이 **모두 같은 인스턴스**에 가야 한다. 앞단에 trace ID 기준 load balancing exporter 계층을 둔다(tailsamplingprocessor README).

### 9. 200ms vs 2초

- 의심: 나머지 작업이 비동기 경계(스레드풀·`CompletableFuture`·큐)에서 컨텍스트를 잃고 **다른 루트 트레이스**로 흩어졌다.
- 확인: 같은 시각, 같은 서비스의 부모 없는 INTERNAL·CONSUMER 루트 스팬을 찾는다. 로그의 요청 ID와 각 스팬의 trace ID를 대조한다.
- 고치기: `Context.taskWrapping(executor)`, 메시지 헤더 inject/extract.

### 10. 게이트웨이 뒤 trace ID 변경

- 후보: 게이트웨이·프록시가 `traceparent`를 전달하지 않음(허용 목록), 다른 형식(B3 등)만 전파, 프록시가 자체 트레이싱으로 새 trace 시작.
- 확인: `curl -H 'traceparent: 00-<알려진 trace-id>-…-01'`로 보낸 뒤 서비스 로그·트레이스에서 그 trace-id가 나오는지, 서비스가 받은 헤더에 `traceparent`가 있는지 본다.
- 고치기: 경계마다 W3C 형식으로 통일하거나 복합 propagator로 두 형식을 함께 처리한다.
