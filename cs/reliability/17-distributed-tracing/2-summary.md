# reliability/17-distributed-tracing — 트레이스·스팬·컨텍스트 전파·baggage·span link·샘플링 — 정리 (힌트)

## 해결하는 문제

주문 요청 하나가 게이트웨이 → 주문 → 재고·결제 → 외부 PG를 거친다. 그 요청이 3초 걸렸다.\
서비스마다 지표(16)를 보면 다들 "조금 느리다". 서비스마다 로그(15)를 보면 줄이 수만 개다. **이 요청의 3초가 어디서 쓰였는지**, 누가 누구를 불렀는지는 어느 한 서비스의 기록에도 없다.

```text
 트레이스가 없을 때                              트레이스가 있을 때
 gateway 로그: /checkout 3012ms                 GET /checkout ─────────────────────────── 3012ms
 order 로그:   create 2950ms                     ├ order.create ───────────────────────── 2950ms
 payment 로그: pay 2800ms                        │  ├ SELECT stock ─ 12ms
 stock 로그:   reserve 15ms                      │  └ payment.pay ─────────────────────── 2800ms
 → 이 넷이 같은 요청인지, 누가 기다렸는지 모른다   │     └ POST pg/approve ──────────────── 2750ms ← 여기
```

- *트레이스(trace)*: 요청 하나가 시스템을 지나며 한 일 전체. 같은 trace ID를 가진 스팬들의 묶음이다.
- *스팬(span)*: 이름이 붙은 작업 한 구간. 시작·끝 시각, 부모 스팬 ID, 속성(키-값), 이벤트, 상태(OK·ERROR)를 가진다.
- 스팬은 부모 ID로 이어져 **트리**가 된다. 트리를 시간축에 펼치면 어느 구간이 전체 시간을 잡아먹었는지 보인다.

쉬운 예: 공항 수하물 태그다. 가방 하나에 태그 번호 하나가 붙고, 환승 공항마다 "언제 받아 언제 넘겼다"를 같은 번호로 적는다. 가방이 늦으면 번호 하나로 어느 공항에서 머물렀는지 본다.\
똑같은 구조다.\
실무 예: Google Dapper(2010)는 이 모양을 대규모 운영 경험으로 정리한 대표 논문이다(논문 스스로 X-Trace·Magpie 같은 앞선 연구에서 영감을 받았다고 적는다). 지금은 OpenTelemetry로 스팬을 만들고 W3C Trace Context 헤더로 서비스 사이에 번호를 넘긴다.

## 동작·원리

### 1. 스팬 트리와 스팬 종류

```text
 trace=bd9397…
 GET /checkout            [SERVER]   ← 요청을 받은 쪽
   ├ SELECT orders        [CLIENT]   ← 이 프로세스가 밖(DB)을 부른 구간
   ├ score-fraud          [INTERNAL] ← 프로세스 안의 작업
   └ POST payment-svc     [CLIENT]
       └ POST /pay        [SERVER]   ← 다른 서비스(다른 프로세스)의 스팬, 같은 trace
```

- *span kind*: OpenTelemetry 스팬의 역할 표시. `SERVER`·`CLIENT`(동기 호출의 양 끝), `PRODUCER`·`CONSUMER`(메시지의 양 끝), `INTERNAL`.
- 한 호출은 보통 스팬 두 개다. 부르는 쪽의 `CLIENT` 스팬과 받는 쪽의 `SERVER` 스팬. 둘의 시간 차이는 서버 스팬 바깥에서 클라이언트가 본 시간이다. 네트워크·큐 대기가 주로 들지만, 계측에 따라 연결 수립·응답 본문 읽기도 들 수 있다(OTel HTTP 스팬 규약 "HTTP client span duration"). 정확한 원인은 따로 재 본다.

### 2. 컨텍스트 전파 — 프로세스 안과 프로세스 사이

```text
 프로세스 안: 현재 스팬은 Context(스레드에 붙은 저장소)에 있다
   요청 스레드 ── Context{span=GET /checkout}
        │ pool.submit(task)      ← 그냥 넘기면 작업 스레드의 Context는 비어 있다 → 새 트레이스
        │ pool.submit(Context.current().wrap(task)) ← 감싸면 부모가 따라간다
 프로세스 사이: 헤더에 실어 보낸다
   traceparent: 00-<trace-id 32hex>-<parent-id 16hex>-<flags 2hex>
   tracestate:  벤더별 추가 정보
   baggage:     tenant=acme
```

- *컨텍스트 전파(context propagation)*: 현재 trace ID·스팬 ID(그리고 baggage)를 다음 작업에 넘기는 것. 넘기지 않으면 다음 작업은 새 트레이스를 시작한다.
- W3C Trace Context(2021-11-23 Recommendation)의 `traceparent`
  - `version`: 현재 `00`.
  - `trace-id`: 16바이트. 트레이스 전체의 ID. 전부 0은 무효.
  - `parent-id`: 8바이트. **보낸 쪽의 스팬 ID**. 받는 쪽은 이것을 부모로 삼는다.
  - `trace-flags`: 8비트. 가장 낮은 비트가 `sampled`(보낸 쪽이 기록했을 수 있음).
  - Trace Context Level 2(2024-03-28 Candidate Recommendation Draft)는 두 번째 비트를 **random trace-id flag**로 정했다. trace-id의 오른쪽 7바이트가 무작위로 만들어졌다는 표시다. 아래 실험에서 OTel Java 1.66이 보낸 flags가 `03`(= sampled + random)이었다.
- Dapper 논문도 같은 구조다. 스레드가 추적 중인 흐름을 다루면 trace context를 thread-local에 붙이고, 콜백을 만들 때 만든 쪽의 context를 저장했다가 실행할 때 붙인다(2.2절 "Instrumentation points").

### 3. 실험: 스팬 트리, 스레드풀 경계, 서비스 경계

```java
Span root = t.spanBuilder("GET /checkout").setSpanKind(SpanKind.SERVER).startSpan();
try (Scope s = root.makeCurrent(); Scope b = Baggage.current().toBuilder().put("tenant", "acme").build().makeCurrent()) {
    t.spanBuilder("SELECT orders").setSpanKind(SpanKind.CLIENT).startSpan().end();
    pool.submit(() -> t.spanBuilder("score-fraud (wrap 안 함)").startSpan().end()).get();
    pool.submit(Context.current().wrap(() -> t.spanBuilder("score-fraud (Context.wrap)").startSpan().end())).get();
    Span call = t.spanBuilder("POST payment-svc /pay").setSpanKind(SpanKind.CLIENT).startSpan();
    try (Scope c = call.makeCurrent()) { prop.inject(Context.current(), headers, Map::put); }
    Context remote = prop.extract(Context.root(), headers, GET);              // 하류: 헤더만 받는다
    String tenant = Baggage.fromContext(remote).getEntryValue("tenant");
    t.spanBuilder("POST /pay").setSpanKind(SpanKind.SERVER).setParent(remote).setAttribute("tenant", tenant).startSpan().end();
    call.end();
}
root.end();
```

(실험, OpenTelemetry Java SDK 1.66.0, JDK 21.0.12 temurin, 컨테이너 `--cpus=2`, 2026-10-01 — ID는 실행마다 다르다)

```text
보낸 헤더: {traceparent=00-bd93975da603f605bbdf3cd60a1d5e8e-671fbca3f1e17e51-03, baggage=tenant=acme}
score-fraud (wrap 안 함) [INTERNAL] trace=06478e span=4624cb
GET /checkout [SERVER] trace=bd9397 span=7bdde6
  └ SELECT orders [CLIENT] trace=bd9397 span=2374b5
  └ score-fraud (Context.wrap) [INTERNAL] trace=bd9397 span=672d86
  └ POST payment-svc /pay [CLIENT] trace=bd9397 span=671fbc
    └ POST /pay [SERVER] trace=bd9397 span=fb02d0 tenant=acme
```

- 관찰 1 — 감싸지 않고 스레드풀에 넘긴 작업은 **다른 trace(06478e)의 루트**가 됐다. 트레이스가 조각났다.
- 관찰 2 — `Context.current().wrap(...)`으로 감싼 작업은 `GET /checkout`의 자식이 됐다.
- 관찰 3 — `traceparent`의 parent-id(`671fbca3…`)는 보낸 쪽 `CLIENT` 스팬의 ID다. 하류 `POST /pay`는 그것을 부모로 삼아 같은 trace에 붙었다.
- 관찰 4 — baggage `tenant=acme`가 헤더로 건너갔다. 그러나 baggage 범위 안에서 만든 `SELECT orders` 스팬에는 tenant 속성이 없다. 하류가 읽어 **직접** 속성으로 넣은 `POST /pay`에만 있다. baggage는 전파되는 값이지, 스팬 속성에 저절로 들어가지 않는다(이 SDK 구성에서).

### 4. Baggage — 업무 문맥을 하류로

- *baggage*: 요청과 함께 하류로 넘기는 키-값 목록(W3C Baggage, `baggage` 헤더). 테넌트·사용자 등급·실험군 같은 업무 문맥을 하류가 다시 조회하지 않고 쓰게 한다.
- W3C Baggage(2024-05-30 Candidate Recommendation Snapshot) 3.3.2 Limits
  - 플랫폼은 결과 baggage가 **64개 항목 이하이고 8192바이트 이하**면 모든 항목을 전파해야 한다(MUST).
  - 넘으면 항목을 버릴 수 있다(MAY). 어느 것을 버릴지는 구현이 정한다.
  - 이것은 최소 요구다. 더 큰 한도를 둘 수 있다.
- 주의
  - baggage는 **하류 호출마다 실린다**. 외부 API를 부를 때도 실려 나갈 수 있다. W3C Baggage 5절(Privacy Considerations)은 헤더 남용 위험을 평가해야 한다고 한다("Systems MUST assess the risk of header abuse"). 신뢰 경계를 넘을 때 민감 데이터를 걸러 내라는 취지다.
  - 신뢰 경계 밖에서 온 baggage는 검증 없이 권한 판단에 쓰지 않는다. 누구든 헤더를 꾸며 보낼 수 있다.

### 5. Span link — 부모가 여럿일 때

```text
 send orders #1 [PRODUCER] trace=b55961        (주문 요청 1의 트레이스)
 send orders #2 [PRODUCER] trace=725b2d        (주문 요청 2의 트레이스)
 send orders #3 [PRODUCER] trace=8e4eee        (주문 요청 3의 트레이스)
          ╲          │          ╱   link(부모가 아니라 "관련 있음")
 process orders (batch 3) [CONSUMER] trace=436889 (새 트레이스)
```

- 스팬의 부모는 하나뿐이다. 배치 소비 스팬 하나가 메시지 세 개를 처리하면 부모를 하나로 고를 수 없다.
  - 그중 하나를 부모로 삼으면 다른 둘의 트레이스에서는 처리 단계가 사라지고, 고른 트레이스는 남의 메시지 처리까지 포함해 왜곡된다.
- *span link*: 스팬이 다른 스팬 컨텍스트(다른 트레이스여도 된다)를 "관련 있음"으로 가리키는 것. 부모-자식과 달리 여러 개를 둘 수 있다.
- OpenTelemetry Messaging spans 의미 규약(상태 Development, 2026-10-01 열람)
  - "Process"·"Receive" 스팬은 처리한 메시지마다 그 메시지의 생성 컨텍스트로 **link를 건다**(SHOULD).
  - 링크가 기본 메커니즘인 이유: 배치에서는 스팬이 부모를 하나만 가질 수 있으므로 링크가 생산자·소비자를 잇는 유일한 방법이다.
  - 메시지가 하나일 때만 생성 컨텍스트를 "Process" 스팬의 부모로 삼을 수 있다(MAY).

(같은 실험)

```text
send orders #1 [PRODUCER] trace=b55961 span=33ff82
send orders #2 [PRODUCER] trace=725b2d span=f1fbfe
send orders #3 [PRODUCER] trace=8e4eee span=6a9e4c
process orders (batch 3) [CONSUMER] trace=436889 span=8ba34a links=[b55961/33ff82, 725b2d/f1fbfe, 8e4eee/6a9e4c]
```

### 6. 샘플링 — head와 tail

```text
 head 샘플링: 루트에서 결정 → flags의 sampled 비트로 하류에 전달 → 하류는 따른다
   요청 시작 ─[10% 주사위]─▶ 기록 / 버림   ← 이 요청이 에러로 끝날지 아직 모른다
 tail 샘플링: 스팬을 다 모은 뒤 결정
   스팬들 ─▶ 수집기 메모리(trace별로 기다림, 기본 30초) ─▶ "에러가 있나? 느린가?" ─▶ 남김 / 버림
```

- *head 샘플링*: 트레이스 시작 시점에 남길지 정한다. 싸고 단순하다. 결정은 `sampled` 비트로 전파되어 트레이스 전체가 같이 남거나 같이 버려진다.
  - OpenTelemetry SDK 기본 샘플러는 `ParentBased(root=AlwaysOn)`이다(OTel 명세 SDK 환경 변수 `OTEL_TRACES_SAMPLER` 기본 `parentbased_always_on`). 즉 설정하지 않으면 전부 기록한다.
  - `TraceIdRatioBased`는 trace ID로 결정적으로 정한다. 같은 SDK 구현이면 같은 ID에 같은 결정을 낸다. 단 정확한 알고리즘이 명세되지 않아 언어·버전이 다른 SDK 사이의 일치는 보장되지 않는다(OTel 명세 "Compatibility warnings for TraceIdRatioBased"). 명세 main은 이것을 `ProbabilitySampler`로 대체 예정(deprecated)이라고 적는다(2026-10-01 열람).
  - Dapper 첫 버전은 모든 프로세스에 균일 확률 1/1024를 썼다. 트래픽이 적은 서비스는 중요한 사건을 놓칠 수 있어, 원하는 초당 트레이스 수로 확률을 조절하는 적응형 샘플링으로 옮겨 가는 중이라고 적었다.
- *tail 샘플링*: 트레이스가 끝난 뒤(또는 일정 시간 기다린 뒤) 내용을 보고 정한다. 에러·느린 트레이스를 골라 남길 수 있다.
  - OTel Collector contrib `tailsamplingprocessor`: 정책(`status_code`·`latency`·`probabilistic` 등), `decision_wait` 기본 30s, `num_traces` 기본 50000. **한 트레이스의 스팬이 모두 같은 수집기 인스턴스로 가야** 한다(README).

### 7. 실험: head 샘플링 10%와 에러 트레이스

(같은 환경, `Sampler.parentBased(Sampler.traceIdRatioBased(0.1))`, 요청 10000개, 에러 2%(에러 여부의 난수 시드는 고정, trace ID는 실행마다 무작위), 2026-10-01)

```text
기록된 트레이스 999/10000, 그중 에러 트레이스 25/212, 자식 스팬 999 (부모와 같은 결정)
```

- 남는 수는 실행마다 다르다. trace ID가 무작위라 어느 트레이스가 10%에 드는지가 바뀐다. 점검 재실행 두 번에서 기록 913·1007개, 에러 트레이스 20·26개/212였다(같은 환경).

- 관찰 1: 기록 비율은 약 10%다. 자식 스팬도 정확히 루트 수만큼 남았다. 부모의 결정을 따랐기 때문이다.
- 관찰 2: 에러 트레이스 212개 중 **25개만** 남았다(세 번 실행에서 20~26개). 시작 시점의 주사위는 에러 여부를 모른다. 장애 조사에 필요한 트레이스의 약 88~91%가 사라졌다.
- 대처는 §적용 3(tail 샘플링으로 에러·느린 트레이스는 남기기)이다. 반대로 tail 샘플링은 수집기 메모리와 "같은 수집기로 모으기"라는 운영 비용을 낸다.

## 쓰이는 자료구조·알고리즘

- **스팬 트리** — 스팬마다 부모 ID(부모 포인터). 수집 뒤 `부모 ID → 자식 목록` 해시맵으로 트리를 다시 세운다(실험의 `printTrees`). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · 트리 순회는 [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md).
- **링크가 있는 DAG** — span link를 더하면 트레이스 사이를 잇는 방향 그래프가 된다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).
- **임계 경로(critical path)** — 트리에서 끝 시각을 결정한 자식 사슬을 따라 내려간다. 병렬 자식 중 가장 늦게 끝난 것만 전체 시간에 기여한다.
- **결정적 해시 샘플링** — trace ID의 해시로 비율 판정. 같은 구현이면 같은 ID에 같은 결정(SDK 사이 일치는 보장 안 됨). 15의 요청 ID 해시 샘플링과 같다.
- **문맥 저장소** — Context는 스레드에 붙은 불변 키-값 맵. 감싸기(`wrap`)는 만든 쪽의 맵을 실행 쪽에 잠깐 붙였다 떼는 것이다.

## 적용 — 풀어나가는 법

### 1. 순서

1. 자동 계측부터: OpenTelemetry Java 에이전트나 프레임워크 통합(Spring Boot의 Micrometer Tracing 등)으로 HTTP 서버·클라이언트·JDBC·메시징 스팬을 얻는다.
2. 경계마다 전파를 확인한다: 게이트웨이·프록시가 `traceparent`를 지우거나 새로 만들지 않는지, 메시지 헤더에 실리는지.
3. 비동기 경계(스레드풀·`CompletableFuture`·스케줄러)에 `Context.taskWrapping(executor)`를 건다.
4. 업무 속성을 스팬에 단다(주문 ID·테넌트). 스팬 속성은 지표 레이블과 달리 시계열 수를 늘리지 않으므로 개별 식별자를 둘 자리다(16과 대비). 단 민감 정보는 넣지 않는다.
5. 샘플링을 정한다: head 비율 또는 수집기 tail 정책(에러·느린 것 남기기). 둘을 겹치면 앱 head 샘플러가 버린 스팬은 수집기로 가지 않아 tail 정책이 볼 수 없다. 에러·느린 것을 tail로 고르려면 앱은 그 트레이스를 (head로 줄이지 않고) 수집기로 보내야 한다.
6. 로그에 trace ID를 넣어 로그 ↔ 트레이스를 오간다(15). 지표 히스토그램에 exemplar를 붙이면 그래프의 점에서 트레이스로 간다.

### 2. 비동기 경계와 메시지 헤더 (Java, OpenTelemetry API)

```java
// 스레드풀: 제출 시점의 Context를 실행 스레드로
ExecutorService pool = Context.taskWrapping(Executors.newFixedThreadPool(8));

// 메시지 보내기: 생성 컨텍스트를 헤더에 싣는다
Span send = tracer.spanBuilder("send orders").setSpanKind(SpanKind.PRODUCER).startSpan();
try (Scope s = send.makeCurrent()) {
    Map<String, String> h = new HashMap<>();
    propagator.inject(Context.current(), h, Map::put);
    producer.send(new ProducerRecord<>("orders", key, value, toKafkaHeaders(h)));
} finally { send.end(); }

// 배치 소비: 메시지마다 link, 부모는 두지 않는다
SpanBuilder b = tracer.spanBuilder("process orders").setSpanKind(SpanKind.CONSUMER).setNoParent();
for (ConsumerRecord<String, String> r : records) {
    Context c = propagator.extract(Context.root(), r.headers(), KAFKA_GETTER);
    b.addLink(Span.fromContext(c).getSpanContext());
}
Span process = b.startSpan();
```

### 3. tail 샘플링 — 에러·느린 것은 남기고 나머지는 10% (OTel Collector contrib, 설정 예)

```yaml
processors:
  tail_sampling:
    decision_wait: 30s
    policies:
      - { name: errors, type: status_code, status_code: { status_codes: [ERROR] } }
      - { name: slow,   type: latency,     latency: { threshold_ms: 2000 } }
      - { name: base,   type: probabilistic, probabilistic: { sampling_percentage: 10 } }
```

- 이 정책은 **결정 시점까지 수집기에 도착해 메모리에 남은 스팬**만 보고 고른다. 결정 뒤 늦게 온 스팬의 에러·지연은 이미 내린 결정을 바꾸지 않고, `num_traces`가 차면 결정 전에 밀려나는 트레이스도 생긴다(README). 그래서 "에러·느린 것은 모두 남는다"는 보장은 아니다.
- 수집기를 여러 대 두면 trace ID 기준으로 같은 인스턴스에 보내는 앞단(예: `loadbalancing` 내보내기)이 필요하다(tailsamplingprocessor README의 확장 안내).

### 4. 진단

```bash
# 헤더가 경계를 건너는지: 직접 traceparent를 넣고 하류 로그·트레이스에 같은 trace-id가 나오나
curl -s -H 'traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01' https://api.example.com/checkout -o /dev/null -w '%{http_code}\n'
# 프록시가 헤더를 지우는지 (Envoy·nginx 설정에서 traceparent 처리 확인)
kubectl logs deploy/order | jq -r 'select(.traceId=="4bf92f3577b34da6a3ce929d0e0e4736") | .message'
```

## 장애 시나리오와 대처

### 1. 비동기 경계에서 컨텍스트가 끊김 → 트레이스가 조각남

- 현상: 트레이스 화면에서 요청이 200ms에 끝난 것으로 보이는데 실제 응답은 2초다. 나머지 일은 이름 모를 루트 트레이스로 흩어져 있다.
- 보이는 형태: 위 실험의 `score-fraud (wrap 안 함)`처럼 부모 없는 루트 스팬이 많다. 큐 소비 스팬이 생산자와 다른 trace에 따로 있고 링크도 없다.
- 원인: Context는 스레드에 붙어 있다. 스레드풀·`CompletableFuture.supplyAsync`·스케줄러·메시지 큐를 건널 때 넘기지 않았다.
- 대처: `Context.taskWrapping`·`wrap`, 자동 계측이 지원하는 실행기 사용, 메시지 헤더 inject/extract. "부모 없는 INTERNAL 루트 스팬 비율"을 점검 지표로 둔다.

### 2. head 샘플링으로 에러 트레이스가 없다

- 현상: 장애 시각의 에러 요청 트레이스를 찾으니 대부분 없다.
- 보이는 형태: 위 실험처럼 10% 샘플링에서 에러 트레이스 212개 중 25개(세 번 실행 20~26개)만 남음. 에러율 지표는 높은데 에러 트레이스 검색 결과가 적다.
- 원인: 시작 시점에 결정하므로 결과(에러·지연)를 반영할 수 없다.
- 대처: 수집기 tail 샘플링으로 에러·느린 트레이스를 남긴다. 낮은 트래픽 서비스는 비율을 높이거나 적응형으로 둔다(Dapper의 관찰). 감사 근거로 트레이스를 쓰지 않는다(18).

### 3. 배치 소비에서 producer span을 부모로 삼아 트레이스 왜곡

- 현상: 주문 1의 트레이스에 주문 2·3의 처리 시간까지 들어 있다. 주문 2·3의 트레이스에는 처리 단계가 없다.
- 보이는 형태: 배치 처리 스팬 하나가 첫 메시지의 trace에 자식으로 붙어 있다.
- 원인: 스팬의 부모는 하나뿐인데 여러 메시지를 한 스팬으로 처리했다.
- 대처: 처리 스팬은 부모 없이(또는 소비 루프 스팬 아래) 만들고 메시지마다 span link를 건다(OTel Messaging 규약의 기본). 메시지별 처리 스팬을 따로 두면 그 스팬만 각 메시지의 자식으로 둘 수 있다.

### 4. 프록시·게이트웨이가 헤더를 지우거나 새로 만든다

- 현상: 게이트웨이 뒤부터 트레이스가 새로 시작한다. 프런트엔드에서 본 trace ID로 백엔드 기록이 안 나온다.
- 보이는 형태: 게이트웨이 스팬과 서비스 스팬의 trace ID가 다르다. 서비스가 받은 요청 헤더에 `traceparent`가 없다.
- 원인: 헤더 허용 목록에 없음, 다른 형식(B3 등)만 전파, 프록시가 자체 트레이싱으로 새 trace를 시작.
- 대처: 경계마다 전파 형식을 통일(W3C `traceparent`)하고, 필요하면 복합 propagator로 두 형식을 함께 읽고 쓴다. 위 진단 명령으로 경계별 확인.

### 5. baggage에 민감 정보·큰 값 → 외부 유출·헤더 비대

- 현상: 외부 결제사 요청 로그에 내부 사용자 이메일이 찍혀 있다는 연락을 받는다. 또는 일부 요청이 `431 Request Header Fields Too Large`로 실패한다.
- 보이는 형태: 나가는 요청 헤더의 `baggage`에 이메일·토큰. 헤더 크기 증가.
- 원인: baggage는 하류 호출마다 실린다. 항목을 계속 덧붙였다.
- 대처: 신뢰 경계(외부 호출)에서 baggage를 지운다. 민감 값은 넣지 않고 ID만. 항목 수·크기를 W3C 최소 한도(64개·8192바이트) 안으로 관리한다.

## 핵심 문장

- 트레이스는 요청 하나의 스팬 트리다. 스팬은 부모 ID로 이어지고, 시간축에 펼치면 어디서 시간을 썼는지 보인다.
- 컨텍스트는 프로세스 안에서는 스레드에 붙어 있고, 프로세스 사이에서는 `traceparent` 헤더로 간다. 둘 중 하나라도 넘기지 않으면 트레이스가 조각난다(실험: 감싸지 않은 스레드풀 작업이 새 루트가 됨).
- baggage는 하류로 업무 문맥을 넘기는 헤더다. W3C는 64개·8192바이트까지 전파를 요구하고, 하류 호출마다 실리므로 민감 정보를 넣지 않는다.
- 스팬의 부모는 하나라서, 배치 소비처럼 원인이 여럿이면 span link로 잇는다.
- head 샘플링은 결과를 모른 채 정한다. 실험에서 10% 샘플링은 에러 트레이스 212개 중 25개만 남겼다. 에러·느린 트레이스는 tail 샘플링으로 남긴다.

## 관련 주제·근거

- 선행
  - [16-metrics-and-golden-signals](../16-metrics-and-golden-signals/2-summary.md) — 지표가 "어디가 이상한가"를, 트레이스가 "이 요청은 왜"를 답한다
  - [15-logging](../15-logging/2-summary.md) — MDC와 같은 스레드 경계 문제, 요청 ID 해시 샘플링
- 후속·연결
  - [18-logs-traces-audit-roles](../18-logs-traces-audit-roles/2-summary.md) — 샘플링되는 트레이스는 감사 근거가 아니다
  - [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) · [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md) — 메시지 경계, 배치 소비
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md)
  - [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md) — 같은 헤더 전파 경로로 데드라인도 간다
  - [34-tail-latency-and-stragglers](../34-tail-latency-and-stragglers/2-summary.md) · [50-sidecar-ambassador-and-service-mesh](../50-sidecar-ambassador-and-service-mesh/2-summary.md)
- 명세·논문
  - W3C Trace Context (Recommendation 2021-11-23) — `traceparent` 형식, sampled 플래그 <https://www.w3.org/TR/trace-context/>
  - W3C Trace Context Level 2 (Candidate Recommendation Draft 2024-03-28) — random trace-id flag <https://www.w3.org/TR/trace-context-2/>
  - W3C Baggage (Candidate Recommendation Snapshot 2024-05-30) — 3.3.2 Limits(64 항목·8192바이트 MUST), 5 Privacy <https://www.w3.org/TR/baggage/>
  - OpenTelemetry Semantic Conventions — Messaging spans(Status: Development; 링크 기본, 배치에서 유일한 방법) <https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/>
  - OpenTelemetry Specification — Trace SDK(기본 `ParentBased(root=AlwaysOn)`, `TraceIdRatioBased` 결정적 해시·대체 예정), SDK 환경 변수 `OTEL_TRACES_SAMPLER`
  - Sigelman 외, "Dapper, a Large-Scale Distributed Systems Tracing Infrastructure", Google Technical Report dapper-2010-1 — thread-local trace context, 콜백의 context 저장, 균일 1/1024 샘플링과 적응형 샘플링 <https://research.google.com/archive/papers/dapper-2010-1.pdf>
  - OTel Collector contrib `processor/tailsamplingprocessor/README.md`(같은 인스턴스 요구, `decision_wait` 30s, `num_traces` 50000)
- 실험 목록
  - OpenTelemetry Java SDK 1.66.0(scratchpad `rel/15/Trace17.java`, 직접 만든 수집 exporter): ① 스팬 트리 + 스레드풀 wrap 유무 + W3C traceparent·baggage inject/extract ② 메시지 3개 → 배치 처리 스팬 link ③ `parentBased(traceIdRatioBased(0.1))` 10000 요청 중 에러 트레이스 보존 수 — JDK 21.0.12, `--cpus=2`
