# api-design/18-api-style-selection — API 스타일 고르기: REST·gRPC·GraphQL·WebSocket/SSE·메시지 큐 — 정리 (힌트)

## 해결하는 문제

"요즘은 gRPC가 빠르다더라", "GraphQL이 유연하다더라"처럼 유행으로 스타일을 고르면 나중에 되돌리기 어렵다.

```text
  잘못 고른 예                                   드러나는 시점
  브라우저 앱에 gRPC 서버를 바로 노출           → 브라우저가 직접 못 부른다 (gRPC-Web + 프록시 필요)
  공개 상품 조회를 GraphQL POST 하나로          → CDN·프록시 캐시가 하나도 안 먹는다
  주문 상태 변화를 1초 폴링으로                  → 사용자 수 × 1회/초 요청, 대부분 "변화 없음"
  결제 후 알림 10곳을 동기 RPC로 순차 호출       → 하나만 느려도 결제 응답이 느려진다
```

- 해법: 스타일을 **기능이 아니라 제약 조건**으로 고른다. 누가 부르나(브라우저·제3자·내부 서비스), 캐시가 필요한가, 서버가 먼저 보내야 하나, 호출자가 결과를 기다려야 하나.
- 쉬운 예: 연락 수단 고르기. 공지문(게시판 = REST + 캐시), 내선 전화(내부 RPC), 맞춤 주문서(GraphQL), 무전기(WebSocket), 우편함(메시지 큐). 같은 내용이라도 상대와 상황이 다르면 수단이 다르다.
- 똑같은 구조다. 실무 예: 한 서비스 안에서도 외부 공개 API는 REST, 내부 서비스 간은 gRPC, 모바일 화면 조합은 GraphQL이나 BFF, 실시간 알림은 SSE, 서비스 간 이벤트는 Kafka — 경계마다 다르게 고른다.

## 동작·원리

### 1. 다섯 스타일의 모양

```text
  REST      클라 ─ GET /orders/1 ─────────────────> 서버        자원 + HTTP 메서드 의미 + 캐시
  gRPC      클라 ─ OrderService.Get(id) (HTTP/2) ──> 서버        스키마(.proto) + 바이너리 + 스트리밍
  GraphQL   클라 ─ POST /graphql {query} ──────────> 서버        엔드포인트 하나 + 클라가 모양 지정
  WS / SSE  클라 <════ 연결 유지, 서버가 먼저 보냄 ═══ 서버        양방향(WS) / 서버→클라 단방향(SSE)
  메시지 큐  생산자 ─> [브로커] ─> 소비자                         비동기, 시간·공간 분리, 재처리
```

- *균일 인터페이스(uniform interface)*: 모든 자원을 같은 방식으로 다루게 하는 REST 제약. Fielding은 자원 식별·표현을 통한 조작·자기 서술 메시지·HATEOAS 네 제약으로 정의하고, HTTP에서는 모든 자원에 같은 메서드 집합(GET·PUT·DELETE…)을 쓰는 모습으로 드러난다. Fielding 2000 5.1.5는 이 제약이 전체 구조를 단순하게 하고 상호작용의 가시성(visibility)을 높이지만, 정보가 앱에 맞춘 형태가 아니라 표준 형태로 오가므로 **효율을 떨어뜨린다**는 트레이드오프를 함께 적는다. 공유 캐시 같은 중간자의 이득은 5.1.6(계층 시스템)에서 다룬다.
- *캐시 제약*: 응답이 캐시 가능한지 표시하게 해서 일부 상호작용을 아예 없앤다(Fielding 2000 5.1.4).
- *gRPC*: `.proto`로 서비스·메시지를 정의하고 HTTP/2 위에서 호출하는 RPC 프레임워크([15-rpc-and-grpc](../15-rpc-and-grpc/2-summary.md)).
- *SSE(Server-Sent Events)*: HTTP 응답을 끊지 않고 서버가 이벤트를 계속 흘려보내는 단방향 스트림. *WebSocket*: HTTP에서 업그레이드한 양방향 프레임 채널([network/38](../../network/38-websocket-sse-long-lived/2-summary.md)).

### 2. 선택 기준 — 질문 순서

```text
  ① 호출자가 결과를 기다려야 하나?
       아니오 ──> 메시지 큐 / 이벤트 (20)   ※ 결과는 나중에 웹훅·폴링·이벤트로
       예 ↓
  ② 서버가 먼저 보내야 하나(실시간 푸시)?
       예 ──> 서버→클라만: SSE   /  양방향 잦음: WebSocket   (또는 gRPC 스트리밍, 내부라면)
       아니오 ↓
  ③ 누가 부르나?
       브라우저·제3자·공개 ──> REST (+ HTTP 캐시·CDN, 도구·문서 생태계)
       자사 여러 화면이 서로 다른 모양 ──> GraphQL 또는 BFF (19)
       내부 서비스 간, 저지연·강타입·스트리밍 ──> gRPC
  ④ 공개 조회가 많고 캐시가 중요한가?
       예 ──> GET + 캐시 헤더가 되는 스타일 (REST, GraphQL이면 GET + persisted query)
```

- 이 순서는 이 노트의 정리다(표준이 정한 순서가 아니다). 하나의 시스템에 여러 답이 공존하는 것이 보통이다.

### 3. 비교표

| 기준 | REST | gRPC | GraphQL | WebSocket / SSE | 메시지 큐 |
|---|---|---|---|---|---|
| 브라우저에서 직접 | 예 | 아니오 — gRPC-Web + 프록시 | 예 | 예 | 아니오(보통 서버 뒤) |
| HTTP 캐시 | GET이면 표준 캐시 | 사실상 없음 | POST는 안 됨, GET이면 가능 | 해당 없음 | 해당 없음 |
| 계약 | OpenAPI(선택) | `.proto`(필수) | 스키마(필수) | 메시지 형식을 직접 정의 | 메시지 스키마(선택, 레지스트리) |
| 서버 푸시 | 없음(폴링·웹훅) | 서버·양방향 스트리밍 | Subscription(전송은 구현마다) | 핵심 기능 | 소비자에게 전달 |
| 결합 | 동기 | 동기 | 동기 | 연결 유지 | 비동기 — 생산자·소비자 독립 |

- gRPC-Web 근거: grpc/grpc-web README — 브라우저 클라이언트는 **특별한 프록시**(기본 Envoy)를 거쳐 gRPC 서비스에 붙는다. 지원 모드는 단항과 서버 스트리밍(`grpcwebtext` 모드일 때만), 클라이언트·양방향 스트리밍은 현재 미지원. gRPC 저장소 `doc/PROTOCOL-WEB.md`는 "브라우저 제약 때문에" 네이티브 gRPC와 다른 프로토콜을 쓴다고 적는다.
- POST 캐시 근거: RFC 9110 9.2.3 — GET·HEAD·POST의 캐시 의미를 정의하지만 **대부분의 캐시 구현은 GET·HEAD만 지원**한다. 9.3.3 — POST 응답은 명시적 신선도와 요청 URI와 같은 `Content-Location`이 있을 때만 캐시 가능하고, 그것도 이후 GET·HEAD에만 재사용되며 **POST 요청을 캐시된 POST 응답으로 채울 수는 없다**.

### 실험: 같은 조회를 REST GET · GraphQL POST · GraphQL GET으로

(실험, nginx 1.31.6(`nginx:alpine` 이미지) + node 22.23.2 백엔드, 일회용 컨테이너·전용 네트워크, 2026-10-04)

백엔드는 모든 응답에 `Cache-Control: public, max-age=60`을 붙이고 메서드·경로별 도달 횟수를 센다. nginx는 `proxy_cache`만 켜고 `proxy_cache_methods`는 기본값(GET HEAD)으로 뒀다.

```nginx
proxy_cache_path /tmp/cache keys_zone=api:1m;
location / {
  proxy_pass http://sn-ad-w17-backend:8080;
  proxy_cache api;                 # proxy_cache_methods 기본값 = GET HEAD
  add_header X-Cache-Status $upstream_cache_status always;
}
```

각 방식으로 같은 요청을 5번 보낸 결과(`X-Cache-Status`, `-`는 헤더 값 없음 = 캐시 대상 아님):

```text
REST  GET  /items/1          MISS HIT HIT HIT HIT
GQL   POST /graphql          - - - - -
GQL   GET  /graphql?query=   MISS HIT HIT HIT HIT
백엔드 도달 횟수: {"GET /items/1":1,"POST /graphql":5,"GET /graphql":1}
```

- 관찰: 응답 헤더가 똑같이 "60초 캐시해도 된다"고 말해도 POST는 5번 모두 백엔드까지 갔다. GET은 첫 번째만 갔다.
- 해석: 캐시 여부는 서버 헤더만이 아니라 **메서드**가 정한다. nginx 문서도 `proxy_cache_methods` 기본값을 `GET HEAD`로 적는다.
- GraphQL도 GET으로 보내면 캐시된다. graphql.org "Performance"는 GET이 보통 캐시 가능해 CDN을 쓸 수 있다고 하고, URL 길이 문제는 쿼리 대신 해시를 보내는 persisted query로 푼다고 한다. GraphQL over HTTP 초안은 GET을 쿼리에만 허용하고 뮤테이션 GET은 금지한다(405 권장).

### 4. 푸시가 필요한데 폴링하면

```text
  1초 폴링, 접속자 10,000명(예시)
  요청 = 10,000 req/s,  상태가 바뀌는 건 그중 극히 일부 → 대부분 "변화 없음" 응답
  지연 = 평균 0.5초(폴링 간격의 절반) + 처리 시간

  SSE: 연결 10,000개 유지, 변화가 있을 때만 이벤트 1건
```

- 폴링 비용은 `접속자 수 × (1 / 간격)`으로 는다. 간격을 늘리면 부하는 줄지만 지연이 는다 — 둘을 동시에 줄일 수 없다.
- 푸시는 요청 수 대신 **열린 연결 수**를 비용으로 낸다. 연결을 유지하는 프록시 타임아웃·LB 재조정·재접속 폭주를 따로 다뤄야 한다([network/38](../../network/38-websocket-sse-long-lived/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **캐시 키 = 해시 맵**: nginx 기본 `proxy_cache_key`는 `$scheme$proxy_host$request_uri`다. 요청 본문은 키에 없다 — POST 본문에 쿼리가 있는 GraphQL을 그대로 캐시하면 다른 쿼리가 같은 키가 된다. 그래서 캐시는 GET(쿼리가 URI에 있음)을 전제로 한다 → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **persisted query = 해시 → 문서 사전**: 클라이언트는 쿼리 문서의 해시만 보내고, 서버는 해시로 문서를 찾는다. URL이 짧아져 GET 캐시가 가능하고, 허용 목록 역할도 한다.
- **큐·로그**: 메시지 큐는 FIFO 큐(소비하면 지움), Kafka는 추가 전용 로그(오프셋으로 위치만 옮김) → [distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md).
- **폴링 vs 푸시 비용 모델**: 폴링은 시간에 비례하는 요청 수, 푸시는 동시 연결 수에 비례하는 메모리·파일 디스크립터.

## 적용 — 풀어나가는 법

### 1. 경계마다 따로 고른다

| 경계 | 흔한 선택 | 이유 |
|---|---|---|
| 외부 공개 API(제3자 개발자) | REST + OpenAPI | 어떤 언어·도구로도 부를 수 있고 HTTP 캐시·문서 생태계를 그대로 쓴다([21](../21-api-documentation-openapi/2-summary.md)) |
| 자사 웹·앱 → 백엔드 | REST, 화면별 조합이 많으면 BFF 또는 GraphQL | 화면마다 다른 모양 → [19](../19-api-gateway-and-bff/2-summary.md), [17](../17-graphql/2-summary.md) |
| 내부 서비스 ↔ 서비스(동기) | gRPC 또는 REST | 강타입 계약·코드 생성·데드라인·스트리밍 → [15-rpc-and-grpc](../15-rpc-and-grpc/2-summary.md) |
| 서비스 → 서비스(결과를 안 기다림) | 메시지 큐·이벤트 | 시간 분리, 재처리, 팬아웃 → [20](../20-messaging-protocols/2-summary.md) |
| 서버 → 브라우저 실시간 | SSE(단방향), WebSocket(양방향) | 폴링 부하·지연 제거 |

### 2. 결정 기록을 남긴다

- 고른 이유를 **제약 조건**으로 적는다: "브라우저가 부른다", "공개 조회 캐시가 필요하다", "결과를 기다리지 않는다".
- 제약이 바뀌면(예: 내부 전용이던 API를 파트너에게 공개) 스타일을 다시 판단한다 → [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md).

### 3. 진단 — 캐시가 먹는지 확인

```text
  curl -s -o /dev/null -D - https://api.example.com/items/1 | grep -i -E 'cache-control|age|x-cache'
  → 같은 요청 두 번째에 Age 증가·HIT가 보이면 캐시 적중
  POST라면 응답 헤더가 public이어도 공용 캐시 적중을 기대하지 않는다 (위 실험)
```

## 장애 시나리오와 대처

### 1. 브라우저에서 gRPC 서비스를 못 부른다 (⚠)

- **현상**: 프론트엔드 팀이 내부 gRPC 서비스를 직접 쓰려다 막힌다.
- **보이는 형태**: 브라우저 fetch로는 gRPC 요청을 만들 수 없다. gRPC-Web 클라이언트를 붙여도 프록시가 없으면 연결 실패.
- **원인**: 브라우저 제약 때문에 gRPC-Web은 네이티브 gRPC와 다른 프로토콜을 쓰고, 프록시가 둘을 변환한다(gRPC `PROTOCOL-WEB.md`). gRPC-Web은 클라이언트·양방향 스트리밍을 지원하지 않는다(grpc-web README).
- **대처**: 브라우저 앞에는 REST/JSON(또는 BFF)을 두고 내부는 gRPC를 유지하거나, Envoy 같은 gRPC-Web 프록시를 둔다. 양방향 스트리밍이 필요하면 WebSocket을 검토한다.

### 2. 트래픽이 늘었는데 CDN 적중률이 0이다 — 공개 조회를 GraphQL POST로 (⚠)

- **현상**: 상품 상세 같은 공개 조회가 모두 오리진까지 와서 DB 부하가 오른다.
- **보이는 형태**: CDN·프록시 로그의 캐시 상태가 전부 비어 있거나 MISS/BYPASS. 실험에서 POST 5번 = 백엔드 5번.
- **원인**: 대부분의 캐시는 GET·HEAD만 캐시한다(RFC 9110 9.2.3, nginx `proxy_cache_methods` 기본값). nginx 기본 캐시 키에는 요청 본문이 없다(설정으로 넣을 수는 있지만 RFC 9110 9.3.3상 POST 요청은 캐시된 POST 응답으로 채우지 않는다).
- **대처**: 공개 조회는 REST GET으로 따로 열거나, GraphQL을 GET + persisted query로 보낸다(실험에서 GET은 1번만 도달). 개인화 응답은 `Cache-Control: private`로 공용 캐시에서 뺀다.

### 3. 폴링 때문에 API 서버가 바쁘다 — 푸시가 필요한데 폴링 (⚠)

- **현상**: 접속자 수에 비례해 요청이 늘고, 대부분 "변화 없음" 응답이다. 사용자는 상태 변화가 늦게 보인다고 한다.
- **보이는 형태**: 같은 엔드포인트가 전체 요청의 대부분, 응답 본문 크기가 거의 같다.
- **원인**: 서버가 먼저 알려야 하는 정보를 클라이언트가 주기적으로 묻는다. 부하와 지연이 간격을 두고 맞바뀐다.
- **대처**: SSE·WebSocket으로 바꾸고 재접속 백오프를 둔다. 당장 못 바꾸면 조건부 요청(`ETag` + `If-None-Match` → 304)으로 본문 비용이라도 줄인다([network/34](../../network/34-http-caching/2-summary.md)).

### 4. 동기 호출 사슬이 길어져 한 곳의 지연이 전체로 번진다

- **현상**: 결제 API가 알림·포인트·추천 서비스를 동기로 부르고, 그중 하나만 느려도 결제가 느려진다.
- **원인**: 호출자가 결과를 기다릴 필요가 없는 일을 동기 RPC로 만들었다.
- **대처**: 결과를 기다리지 않는 후속 작업은 이벤트로 분리한다(outbox → 브로커, [distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md)). 대신 전달 보장·중복 처리를 설계해야 한다([20](../20-messaging-protocols/2-summary.md)).

## 핵심 문장

- API 스타일은 기능 목록이 아니라 제약으로 고른다: 누가 부르나, 결과를 기다리나, 서버가 먼저 보내나, 캐시가 필요한가.
- 대부분의 HTTP 캐시는 GET·HEAD만 저장한다. 같은 캐시 헤더라도 POST 응답은 재사용되지 않는다(실험: POST 5번 = 백엔드 5번, GET은 1번).
- 브라우저는 네이티브 gRPC를 직접 못 쓴다. gRPC-Web은 프록시가 필요하고 클라이언트·양방향 스트리밍을 지원하지 않는다.
- 폴링은 부하와 지연을 맞바꿀 뿐이다. 서버 푸시가 본질이면 SSE·WebSocket으로 비용을 "요청 수"에서 "열린 연결 수"로 옮긴다.
- 한 시스템 안에서도 경계마다 다른 스타일이 맞다.

## 관련 주제·근거

- 선행
  - [02-rest-and-resource-modeling](../02-rest-and-resource-modeling/2-summary.md) · [15-rpc-and-grpc](../15-rpc-and-grpc/2-summary.md) · [17-graphql](../17-graphql/2-summary.md) — 영역 표: [curriculum](../curriculum.md)
  - network [38-websocket-sse-long-lived](../../network/38-websocket-sse-long-lived/2-summary.md) — 오래 사는 연결의 동작
  - network [34-http-caching](../../network/34-http-caching/2-summary.md) · [36-http2-multiplexing](../../network/36-http2-multiplexing/2-summary.md)
- 후속·연결
  - [19-api-gateway-and-bff](../19-api-gateway-and-bff/2-summary.md) · [20-messaging-protocols](../20-messaging-protocols/2-summary.md) · [21-api-documentation-openapi](../21-api-documentation-openapi/2-summary.md) · [16-grpc-streaming-modes](../16-grpc-streaming-modes/2-summary.md)
  - distributed [17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) · [16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md)
  - network [47-cdn-and-edge](../../network/47-cdn-and-edge/2-summary.md)
- 문서
  - Fielding 2000 박사논문 5장 — 5.1.4 Cache, 5.1.5 Uniform Interface(효율 트레이드오프) <https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm>
  - RFC 9110 9.2.3 Methods and Caching(GET·HEAD·POST 정의, 대부분 구현은 GET·HEAD만), 9.3.3 POST(캐시 조건) <https://www.rfc-editor.org/rfc/rfc9110.html>
  - nginx `ngx_http_proxy_module` — `proxy_cache_methods` 기본 `GET HEAD`, `proxy_cache_key` 기본 `$scheme$proxy_host$request_uri` <https://nginx.org/en/docs/http/ngx_http_proxy_module.html>
  - grpc/grpc-web README(Envoy 프록시, 지원 모드) <https://github.com/grpc/grpc-web> · grpc/grpc `doc/PROTOCOL-WEB.md`
  - graphql.org "Performance"(GET 캐시, persisted queries) <https://graphql.org/learn/performance/> · GraphQL over HTTP Working Draft <https://http-spec.graphql.org/draft/>
- 실험 목록
  - REST GET · GraphQL POST · GraphQL GET 각 5회의 nginx 캐시 상태와 백엔드 도달 횟수 — nginx 1.31.6(`nginx:alpine`), node 22.23.2 백엔드·클라이언트, 일회용 컨테이너와 전용 네트워크. 사실 점검에서 다시 돌려 같은 출력
