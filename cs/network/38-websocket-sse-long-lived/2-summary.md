# network/38-websocket-sse-long-lived — 오래 사는 연결: WebSocket·SSE·롱폴링 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

HTTP는 기본적으로 "클라이언트가 묻고 서버가 답한다"는 구조다.\
서버는 먼저 말을 걸 수 없다.\
그런데 채팅 메시지, 주문 상태 변경, 주가, 알림은 **서버 쪽에서 먼저 생긴다**.

쉬운 예: 택배 도착을 알고 싶다.

```text
  (1) 짧은 폴링   : 1분마다 경비실에 "왔어요?" 전화 -> 대부분 "아직요"
  (2) 롱폴링      : 전화해서 "오면 그때 말해 주세요" 하고 끊지 않고 기다림
                    -> 오면 답 듣고 끊고, 바로 다시 전화
  (3) SSE         : 경비실이 방송을 켜 두고 도착할 때마다 한 줄씩 읽어 줌 (한 방향)
  (4) WebSocket   : 경비실과 무전기를 하나씩 나눠 가짐 (양방향)
```

똑같은 구조다.\
"서버가 먼저 말할 통로를 어떻게 열어 두나"가 이 주제의 전부다.

실무 예:
- 채팅·협업 편집은 양방향이 필요해서 WebSocket을 쓴다.
- 대시보드·알림·LLM 토큰 스트리밍은 서버→클라이언트 한 방향이라 SSE로 충분한 경우가 많다.
- 방화벽·프록시가 까다로운 환경에서는 롱폴링이 여전히 최후의 대안이다.

대가도 같다.\
연결이 **오래 산다**는 것 자체가 새 장애를 만든다.\
중간의 LB·프록시가 "조용한 연결"을 끊고, 서버를 재배포하면 끊긴 연결들이 거의 동시에 다시 붙으려 한다.

## 동작·원리

### 1. 네 가지 방식을 시간축으로 비교

```text
  짧은 폴링          C --req--> S  (없음)      C --req--> S (없음)     C --req--> S (있음!)
                     <--200 []--              <--200 []--             <--200 [ev]--
                     |<-- 주기 -->|           이벤트가 주기 사이에 나면 최대 한 주기 늦음

  롱폴링             C --req-----------(서버가 붙잡고 기다림)----------> 이벤트 발생
                     <--------------------------------200 [ev]--------
                     C --req (즉시 다시)---------------------------->  ...

  SSE                C --GET Accept: text/event-stream------------------>
                     <--200 Content-Type: text/event-stream (응답이 끝나지 않음)
                     <-- data: ev1 \n\n
                     <-- data: ev2 \n\n        ... 서버가 원할 때마다 한 블록씩

  WebSocket          C --GET Upgrade: websocket--> S
                     <--101 Switching Protocols--
                     <=========== 같은 TCP 위에서 프레임 양방향 ===========>
```

- 짧은 폴링은 구현이 가장 쉽다. 대신 빈 응답이 대부분이고, 지연은 폴링 주기만큼 생긴다.
- 롱폴링은 "응답을 늦게 주는" 방식이다. 이벤트 한 건마다 요청·응답이 한 번씩 끝난다.
- SSE는 "응답을 끝내지 않는" 방식이다. 평범한 HTTP 응답 하나가 계속 흐른다.
- WebSocket은 HTTP로 시작해서 **다른 프로토콜로 갈아탄다**. 그 뒤로는 HTTP가 아니다.

### 2. 롱폴링 — 응답을 붙잡아 둔다 (RFC 6202)

```text
  Client                                   Server
  GET /events?since=41  ---------------->   (41 이후 이벤트 없음 -> 요청을 보류)
                                            ...
                                            이벤트 42 발생
                        <----------------   200 [42]
  GET /events?since=42  ---------------->   (바로 다시 요청)
                                            ...  30초 동안 아무 일 없음
                        <----------------   200 []   (타임아웃 응답 -> 클라이언트는 다시 요청)
```

RFC 6202 §2.2가 정리한 문제:
- **헤더 오버헤드**: 이벤트마다 요청·응답 헤더 전체가 오간다.
- **최대 지연**: 응답을 받은 직후 다음 요청이 도착하기 전에 이벤트가 나면 기다려야 한다. 최대 지연은 네트워크 편도 3번(응답 → 다음 요청 → 응답)을 넘는다.
- **자원 점유**: 클라이언트마다 TCP 연결과 **보류 중인 HTTP 요청**이 하나씩 잡혀 있다. 게이트웨이·프록시에서는 요청 수 한도가 먼저 걸리기 쉽다.

타임아웃 값(RFC 6202 §5.5):
- 너무 길면 서버의 408이나 프록시의 504를 받는다.
- RFC는 "실험상 120초까지 성공했지만 일반적으로 30초가 더 안전하다"고 적는다.

### 3. SSE — 끝나지 않는 응답 하나 (WHATWG HTML §9.2)

와이어 형식은 줄 단위 텍스트다.

```text
  HTTP/1.1 200 OK
  Content-Type: text/event-stream
  Cache-Control: no-store

  : keepalive                    <- ':'로 시작하면 주석 (무시됨)
  retry: 5000                    <- 재연결 대기 시간(ms)을 바꿈
  id: 41
  event: order
  data: {"id":7,
  data:  "state":"PAID"}         <- data 줄 여러 개는 \n으로 이어 붙음
                                 <- 빈 줄 = 이벤트 하나 발송
  id: 42
  data: hello
                                 <- 빈 줄
```

- **빈 줄이 이벤트의 끝이다.** 스트림이 빈 줄 전에 끝나면 그 미완성 이벤트는 버린다(§9.2.6).
- `event:`가 없으면 이벤트 타입은 `message`다.
- 스트림은 **항상 UTF-8**이다. 다른 인코딩을 지정할 방법이 없다.

자동 재연결이 SSE의 핵심 기능이다.

```text
  EventSource                                   Server
  GET /stream                     ------------>
                                  <------------ id: 41 / data ...
                                  <------------ id: 42 / data ...
        (연결 끊김)  readyState = CONNECTING, error 이벤트
        reconnection time 만큼 대기 (초기값은 구현 정의, "수 초 정도")
  GET /stream
  Last-Event-ID: 42               ------------>  서버가 43부터 이어 보내면 유실 0
```

- 브라우저는 마지막으로 받은 `id:`를 기억한다. 다시 붙을 때 `Last-Event-ID` 요청 헤더로 보낸다(§9.2.4).
- **이어 보낼지는 서버 몫이다.** 서버가 이 헤더를 무시하면 중간 이벤트가 유실되거나 중복된다.
- 재연결을 멈추게 하는 방법(§9.2.3)
  - 응답 상태가 200이 아니거나 `Content-Type`이 `text/event-stream`이 아니면 연결을 "fail"한다. 다시 붙지 않는다.
  - 명세 서론은 `204 No Content`로 재연결을 멈추게 할 수 있다고 적는다.
  - 네트워크 오류로 끊기거나 서버가 응답을 정상 종료하면 다시 붙는다.
- 명세는 재연결 대기에 지수 백오프를 **넣을 수도 있다**(might)고만 적는다. 강제가 아니다.

  - *reconnection time*: 끊긴 뒤 다시 붙기까지 기다리는 시간이다. 서버가 `retry:` 필드로 바꿀 수 있다.

### 4. WebSocket — HTTP에서 갈아탄다 (RFC 6455)

핸드셰이크(RFC 6455 §1.3, §4):

```text
  GET /chat HTTP/1.1
  Host: server.example.com
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==      <- 무작위 16바이트의 base64
  Origin: https://app.example.com
  Sec-WebSocket-Version: 13

  HTTP/1.1 101 Switching Protocols
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
        = base64( SHA-1( Key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11" ) )
```

- `Sec-WebSocket-Accept`는 "내가 WebSocket을 진짜 이해한다"는 증명이다. 캐시나 일반 HTTP 서버가 우연히 101을 흉내 내지 못하게 한다.
- 101 뒤로 이 TCP 연결은 더 이상 HTTP가 아니다.
- 특정 사이트의 페이지만 받으려는 서버는 `Origin`을 확인해야 한다(SHOULD, §10.2). 원치 않는 출처면 403 같은 HTTP 오류로 거절한다(§4.2.2). 이것을 빼먹으면 다른 사이트의 스크립트가 사용자 쿠키로 연결을 연다.

프레임 구조(§5.2):

```text
   0               1               2               3
  +-+-+-+-+-------+-+-------------+-------------------------------+
  |F|R|R|R| opcode|M| Payload len |  확장 길이 (len=126이면 16비트, |
  |I|S|S|S|  (4)  |A|     (7)     |            127이면 64비트)     |
  |N|V|V|V|       |S|             |                               |
  +-+-+-+-+-------+-+-------------+-------------------------------+
  |  Masking-key (MASK=1일 때 4바이트)  |  Payload ...              |
  +-----------------------------------+---------------------------+

  opcode  0x0 이어짐   0x1 텍스트   0x2 바이너리
          0x8 close    0x9 ping     0xA pong      (0x8 이상 = 제어 프레임)
```

- **FIN**: 메시지의 마지막 조각이면 1이다. 큰 메시지는 여러 프레임으로 쪼갤 수 있다.
- **MASK**: 클라이언트→서버 프레임은 **반드시 마스킹한다**(MUST, §5.1). 서버→클라이언트는 마스킹하지 않는다(MUST NOT).
  - 이유는 중간 프록시 캐시 오염 공격 방어다(§10.3). TLS 위에서도 마스킹한다.
- 제어 프레임의 페이로드는 125바이트 이하다(§5.5).

생존 확인과 종료:

```text
  ping (0x9) --------------------->
             <--------------------- pong (0xA)  ping에 응답 (MUST, §5.5.2), 같은 데이터를 담음 (§5.5.3)

  close(1000 "bye") -------------->
                    <-------------- close(1000)
  그 뒤 TCP 종료 (보통은 서버가 먼저 닫는다 — SHOULD, §7.1.1. TIME_WAIT를 서버가 지게 하려는 것)
```

- ping을 받으면 pong으로 답해야 한다(MUST). 요청 없이 보내는 pong은 한 방향 heartbeat다.
- 브라우저 `WebSocket` API에는 ping을 보내는 메서드가 없다. 브라우저 쪽 heartbeat가 필요하면 앱 메시지로 만든다.

close 코드(§7.4.1, IANA 등록부):

```text
  1000 정상 종료              1001 going away (서버 종료·페이지 이탈)
  1002 프로토콜 오류          1003 받을 수 없는 데이터 형식
  1006 비정상 종료 — close 프레임 없이 끊김. 선로에 절대 실리지 않는 "로컬 표시용" 값
  1008 정책 위반              1009 메시지가 너무 큼
  1011 서버 내부 오류         1012 Service Restart · 1013 Try Again Later (IANA 등록)
```

- **1006을 보면 "상대가 close를 못 보냈다"는 뜻이다.** 원인은 TCP 끊김, 프록시 타임아웃, 프로세스 강제 종료 등이다. 1006 자체는 원인을 알려 주지 않는다.

### 5. 중간 장비가 보는 오래 사는 연결

```text
  Browser ---- (NAT) ---- LB/프록시 ---- 앱 서버
                          idle timer: "마지막 바이트 이후 N초" 지나면 양쪽 연결을 닫음
```

- nginx `proxy_read_timeout` 기본값은 60초다. WebSocket 프록시에서도 상류가 60초 동안 아무것도 안 보내면 연결을 닫는다(nginx "WebSocket proxying").
- AWS ALB의 connection idle timeout 기본값도 60초다. 범위는 1~4000초다(ALB 문서).
- 그래서 오래 사는 연결은 **타임아웃보다 짧은 주기로 무언가를 보내야** 한다.
  - WebSocket: ping 프레임이나 앱 heartbeat
  - SSE: 주석 줄(`:`). 명세는 "레거시 프록시 대비로 15초 정도마다" 보내라고 권한다(§9.2.7).
- nginx가 WebSocket을 중계하려면 hop-by-hop 헤더인 `Upgrade`·`Connection`을 명시해서 넘겨야 한다.

```nginx
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;               # 1.29.7 전 버전에는 필요(기본이 1.0)
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;              # 또는 서버가 주기적으로 ping
}
```

  - *hop-by-hop 헤더*: 한 구간(홉)에만 의미가 있는 헤더다. 프록시는 기본적으로 다음 구간에 넘기지 않는다.

### 6. HTTP/2 위에서는

- HTTP/2는 `Upgrade`·`Connection` 헤더를 금지한다(RFC 9113 §8.2.2). 그래서 HTTP/1.1식 WebSocket 핸드셰이크를 그대로 못 쓴다.
- RFC 8441이 "확장 CONNECT"(`:protocol = websocket`)로 HTTP/2 스트림 하나를 WebSocket으로 쓰는 방법을 정했다. 서버가 `SETTINGS_ENABLE_CONNECT_PROTOCOL`로 지원을 알린다.
- SSE는 평범한 응답이라 HTTP/2 스트림 하나로 그대로 흐른다.
  - HTTP/1.1에서 브라우저는 호스트당 동시 연결 수를 제한한다. MDN은 이 한도를 6으로 적고, 탭 여러 개가 SSE를 열면 금방 찬다고 경고한다.
  - HTTP/2에서는 동시 스트림 수를 서버가 `SETTINGS_MAX_CONCURRENT_STREAMS`로 정한다. RFC 9113 §6.5.2는 100 이상을 권한다.

### 7. 셋 중 무엇을 고르나

```text
                    롱폴링              SSE                     WebSocket
  방향              서버->클라(요청마다)  서버->클라               양방향
  전송              일반 HTTP           일반 HTTP 응답 스트림     101 뒤 전용 프레임
  재연결            앱이 다시 요청       브라우저 자동 + Last-Event-ID  앱이 직접 구현
  데이터            아무거나            UTF-8 텍스트             텍스트·바이너리
  프록시 친화       좋음                좋음(버퍼링만 끄면)       Upgrade 지원 필요
  서버 자원         요청 보류 1개/클라   응답 스트림 1개/클라       연결 1개/클라
```

## 쓰이는 자료구조·알고리즘

- **브로드캐스트 팬아웃 = 구독 맵 + 연결별 송신 큐**
  - `topic -> Set<Connection>` 해시 맵으로 "누구에게 보낼지"를 찾는다. [해시맵](../../data-structure/05-hashmap/2-summary.md)
  - 연결마다 **유한 크기 송신 큐**를 둔다. 느린 클라이언트 하나 때문에 전체 브로드캐스트가 막히지 않게 한다.
  - 큐가 차면 정책을 고른다. 오래된 것 버리기, 최신 상태만 남기기(병합), 그 연결 끊기 중 하나다. [큐·덱](../../data-structure/04-queue-deque/2-summary.md) · 링 버퍼는 미작성([data-structure 영역 표](../../data-structure/curriculum.md))
- **재연결 백오프 = 지수 증가 + 무작위 지터**
  - RFC 6455 §7.2.3은 첫 재연결을 무작위로 늦추고(예: 0~5초), 실패하면 절단 이진 지수 백오프로 늘리라고 권한다(SHOULD).
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md)
- **이벤트 로그 + 커서(Last-Event-ID)** — 서버가 최근 이벤트를 번호 순서로 보관하면, 재연결한 클라이언트의 커서 이후부터 다시 보낼 수 있다. 크기를 제한한 순차 로그(링 버퍼)가 흔한 구현이다.
- **WebSocket 프레임 파서 = 상태 기계** — 헤더 2바이트 → 확장 길이 → 마스킹 키 → 페이로드 순서로 읽는다. 길이 접두 프레이밍의 한 예다(24 `application-protocol-framing` — 영역 표의 연결 노트 [systems/resp-protocol](../../systems/resp-protocol/2-summary.md)).
- **SSE 파서 = 줄 단위 상태 기계** — 필드 버퍼 3개(data·event·id)를 채우다가 빈 줄에서 발송한다.

## 적용 — 풀어나가는 법

### 1. 먼저 방향을 묻는다

1. 클라이언트도 실시간으로 자주 보내나? → WebSocket
2. 서버만 흘리면 되나? → SSE (재연결·커서가 공짜)
3. 중간 장비가 Upgrade·장시간 응답을 못 버티나? → 롱폴링

### 2. 경로 위 모든 idle timeout을 적는다

```text
  브라우저 -> CDN -> ALB(60s) -> nginx(proxy_read_timeout 60s) -> 앱
  heartbeat 주기 < 가장 짧은 idle timeout  (예: 25초 (예시))
```

### 3. 코드

SSE 서버 — Spring MVC `SseEmitter`:

```java
@GetMapping(path = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter stream(@RequestHeader(value = "Last-Event-ID", required = false) String lastId) {
    SseEmitter emitter = new SseEmitter(30 * 60_000L);  // 타임아웃(ms). 30분 (예시). 끊기면 클라이언트가 재연결
    replayAfter(lastId, emitter);                      // 커서 이후 이벤트를 먼저 다시 보냄
    registry.add(emitter);
    emitter.onCompletion(() -> registry.remove(emitter));
    emitter.onTimeout(() -> registry.remove(emitter));
    return emitter;
}
// 보낼 때
emitter.send(SseEmitter.event().id("42").name("order").data(json));
// heartbeat: 주석 줄
emitter.send(SseEmitter.event().comment("keepalive"));
```

SSE 클라이언트 — 브라우저:

```js
const es = new EventSource('/stream');          // Last-Event-ID는 브라우저가 알아서 보냄
es.addEventListener('order', (e) => render(JSON.parse(e.data), e.lastEventId));
es.onerror = () => console.log('readyState', es.readyState); // 0이면 재연결 중, 2면 포기
```

WebSocket 클라이언트 — 지터 백오프 재연결:

```js
let attempt = 0;
function connect() {
  const ws = new WebSocket('wss://api.example.com/ws');
  ws.onopen = () => { attempt = 0; };
  ws.onclose = (e) => {
    if (e.code === 1000) return;                            // 정상 종료면 멈춤
    const cap = Math.min(30_000, 1000 * 2 ** attempt++);   // 상한 30초 (예시)
    setTimeout(connect, Math.random() * cap);               // full jitter
  };
}
connect();
```

WebSocket heartbeat — Java `java.net.http.WebSocket`(JDK 11+) 클라이언트가 ping을 보내는 예:

```java
WebSocket ws = HttpClient.newHttpClient().newWebSocketBuilder()
    .buildAsync(URI.create("wss://api.example.com/ws"), listener).join();
scheduler.scheduleAtFixedRate(
    () -> ws.sendPing(ByteBuffer.allocate(0)), 20, 20, TimeUnit.SECONDS);  // 20초 (예시)
```

### 4. 진단 명령

```bash
# SSE: 버퍼링 없이 흘러오는지 본다 (-N = 출력 버퍼링 끔)
curl -N -H 'Accept: text/event-stream' https://api.example.com/stream

# WebSocket 핸드셰이크만 확인 (101이 오면 성공). --http1.1: HTTP/2에는 Upgrade 핸드셰이크가 없다(RFC 9113 §8.2.2)
curl -i --http1.1 -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
     -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
     https://api.example.com/ws

# 대화형 WebSocket
wscat -c wss://api.example.com/ws

# 서버에 붙은 장수 연결 수
ss -tnH state established '( sport = :443 )' | wc -l   # -H: 헤더 줄 빼고 센다
```

## 장애 시나리오와 대처

### 1. LB·프록시 idle timeout에 조용히 끊긴다

- **현상**: 대화가 없는 채팅방·대시보드가 정확히 일정 시간(예: 60초) 뒤 끊긴다. 바쁜 방은 멀쩡하다.
- **보이는 형태**
  - 브라우저 `CloseEvent.code === 1006`(close 프레임 없이 끊김)
  - SSE는 `error` 이벤트 뒤 `readyState`가 0(재연결 중)이 되고, 서버 로그에 같은 사용자의 재접속이 주기적으로 찍힌다.
  - 끊기는 간격이 경로 위 타임아웃 값(nginx `proxy_read_timeout` 60s, ALB 60s)과 같다.
- **원인**: 중간 장비는 "마지막 데이터 이후 N초"로 연결을 닫는다. 조용한 연결은 살아 있어도 닫힌다.
- **대처**
  - 가장 짧은 idle timeout보다 짧은 주기로 heartbeat를 보낸다. WebSocket은 ping, SSE는 주석 줄이다.
  - 또는 경로 위 타임아웃을 늘린다. 둘 다 할 때는 "heartbeat 주기 < 모든 타임아웃"을 문서로 남긴다.
  - nginx의 타임아웃은 "데이터를 보내지 않은 시간" 기준이다(문서). 데이터가 없는 TCP keepalive 탐침으로는 L7 프록시의 타이머가 리셋된다고 기대하기 어렵다. 앱 계층 heartbeat를 쓴다(21번).
  - ALB는 HTTP/2 PING 프레임으로는 idle timeout이 리셋되지 않는다고 명시한다(ALB 문서).

### 2. 서버 재배포 → 재연결 폭풍

- **현상**: 배포 직후 CPU·인증 서버·DB가 튄다. 새 인스턴스가 뜨자마자 과부하로 다시 죽는다.
- **보이는 형태**
  - 연결 수 그래프가 0으로 떨어졌다가 수 초 안에 수직으로 복귀한다.
  - 핸드셰이크 요청(101)·인증 요청이 한 순간에 몰린다.
- **원인**
  - 인스턴스가 연결 수만 개를 동시에 끊는다.
  - 클라이언트가 고정 간격이나 즉시 재연결을 하면 모두 같은 순간에 돌아온다.
  - RFC 6455 §7.2.3이 바로 이 상황을 서비스 거부와 같다고 경고한다.
- **대처**
  - 클라이언트: 첫 재연결을 무작위로 늦추고, 실패 시 지수 백오프 + 지터를 쓴다(RFC 6455 §7.2.3).
  - 서버: 종료할 때 한꺼번에 끊지 말고 **나눠서 드레이닝**한다. close 코드 1001(going away)이나 1012(Service Restart)로 "정상적인 재시작"임을 알린다. [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md)
  - SSE는 `retry:`로 대기 시간을 넓히고, 서버가 상태 코드로 거절해 재연결을 늦추는 방법도 있다.

### 3. SSE 이벤트가 한참 뒤 한꺼번에 도착한다

- **현상**: 로컬에서는 실시간인데 운영에서는 수십 초 뒤 몰아서 온다.
- **보이는 형태**: `curl -N`으로 원 서버를 직접 치면 즉시 오고, 프록시를 거치면 늦다.
- **원인**
  - nginx `proxy_buffering`이 기본 `on`이라 응답을 버퍼에 모은다.
  - 압축 필터(gzip)가 블록을 채울 때까지 내보내지 않는 경우도 있다(39번).
- **대처**
  - SSE 경로에 `proxy_buffering off;` 또는 응답 헤더 `X-Accel-Buffering: no`를 준다(nginx proxy 모듈 문서).
  - `text/event-stream`을 압축 대상에서 뺀다.
  - 자세한 원리는 [40 chunked·스트리밍](../40-chunked-and-streaming-responses/2-summary.md) 장애 시나리오 2.

### 4. 재연결 후 이벤트가 빠지거나 두 번 온다

- **현상**: 네트워크가 잠깐 끊긴 사용자만 알림 하나를 못 받았다. 또는 같은 알림이 두 번 떴다.
- **보이는 형태**: 서버 로그의 재연결 요청에 `Last-Event-ID: 42`가 있는데 서버가 처음부터(또는 현재부터) 보냈다.
- **원인**: `id:`를 안 붙였거나, 서버가 `Last-Event-ID`를 무시했다. WebSocket은 이 장치가 아예 없다.
- **대처**
  - 이벤트에 단조 증가 ID를 붙이고, 서버는 최근 N개를 보관해 커서 이후부터 다시 보낸다.
  - 보관 범위를 넘으면 "전체 다시 불러오기" 신호를 보낸다.
  - 클라이언트는 이벤트 ID로 중복을 거른다(멱등 처리).

### 5. 느린 소비자 하나가 서버 메모리를 먹는다

- **현상**: 브로드캐스트 서버의 힙이 계속 늘다가 OOM으로 죽는다.
- **보이는 형태**: 연결별 대기 바이트(`WebSocket.bufferedAmount`, 서버 쪽 송신 큐 길이)가 한두 연결에서만 크다. `ss -tm`에서 그 소켓의 송신 큐(Send-Q)가 차 있다.
- **원인**: 모바일 약전계 클라이언트가 못 읽는다. 서버가 쓰기 가능 여부를 안 보고 계속 큐에 쌓는다.
- **대처**
  - 연결별 큐에 상한을 둔다. 넘으면 오래된 메시지를 버리거나 그 연결을 끊는다(close 1008 또는 1013).
  - 역압 원리는 [40번](../40-chunked-and-streaming-responses/2-summary.md)과 [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md).

## 핵심 문장

- 롱폴링은 응답을 **늦게** 주고, SSE는 응답을 **끝내지 않고**, WebSocket은 HTTP에서 **다른 프로토콜로 갈아탄다**.
- SSE는 브라우저가 자동 재연결하고 `Last-Event-ID`로 커서를 보내 준다. 이어 보낼지는 서버가 구현해야 한다.
- WebSocket은 101 핸드셰이크 뒤 프레임을 주고받는다. 클라이언트 프레임은 마스킹하고, ping에는 pong으로 답해야 한다.
- 오래 사는 연결은 경로 위 **가장 짧은 idle timeout**보다 자주 무언가를 보내야 살아남는다.
- 재연결은 지터를 넣은 지수 백오프로 흩어야 한다. 그렇지 않으면 재배포가 곧 자기 자신에 대한 서비스 거부가 된다.

## 관련 주제·근거

- 선행
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — keep-alive·idle timeout 정렬.
  - [21-tcp-keepalive-and-user-timeout](../21-tcp-keepalive-and-user-timeout/2-summary.md) — TCP keepalive vs 앱 heartbeat.
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — 끊김 감지·half-open
- 후속·관련
  - [40-chunked-and-streaming-responses](../40-chunked-and-streaming-responses/2-summary.md) — 스트리밍 응답·프록시 버퍼링·역압
  - [36-http2-multiplexing](../36-http2-multiplexing/2-summary.md) · [44-websocket-compression](../44-websocket-compression/2-summary.md)
  - `46-load-balancers-and-proxies` — [systems/server-design/02-request-path.md](../../systems/server-design/02-request-path.md)
  - [languages/web-api/32-server-sent-events](../../../languages/web-api/32-server-sent-events/2-summary.md) — 브라우저 `EventSource` 실측
  - [languages/web-api/33-websocket](../../../languages/web-api/33-websocket/2-summary.md) — 브라우저 `WebSocket` 핸드셰이크·프레임 실측
  - [issue/cross-cutting/network/half-open-liveness-watchdog](../../../issue/cross-cutting/network/half-open-liveness-watchdog/2-summary.md)
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) · [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md)
- RFC 6455 The WebSocket Protocol <https://www.rfc-editor.org/rfc/rfc6455>
  - §1.3·§4 핸드셰이크(GUID, `Sec-WebSocket-Accept`) · §5.1 마스킹 MUST · §5.2 프레임 · §5.5 제어 프레임(125바이트) · §5.5.2 ping/pong
  - §7.1.1 TCP 종료 · §7.2.3 비정상 종료 후 재연결 백오프 · §7.4.1 close 코드 · §10.2 Origin · §10.3 마스킹 이유
- IANA WebSocket Close Code Number Registry(1012·1013 등) <https://www.iana.org/assignments/websocket/websocket.xhtml>
- RFC 8441 Bootstrapping WebSockets with HTTP/2 <https://www.rfc-editor.org/rfc/rfc8441>
- RFC 9113 HTTP/2 §6.5.2 `SETTINGS_MAX_CONCURRENT_STREAMS` · §8.2.2 연결 전용 헤더 금지 <https://www.rfc-editor.org/rfc/rfc9113>
- RFC 6202 Long Polling and Streaming §2.2 문제점 · §5.5 타임아웃 <https://www.rfc-editor.org/rfc/rfc6202>
- WHATWG HTML §9.2 Server-sent events(§9.2.3 처리 모델 · §9.2.4 `Last-Event-ID` · §9.2.6 해석 · §9.2.7 작성 주의) <https://html.spec.whatwg.org/multipage/server-sent-events.html>
- MDN `EventSource`(HTTP/1.1 연결 수 한도 경고) <https://developer.mozilla.org/en-US/docs/Web/API/EventSource>
- nginx "WebSocket proxying" <https://nginx.org/en/docs/http/websocket.html> · `ngx_http_proxy_module`(`proxy_read_timeout`·`proxy_buffering`·`X-Accel-Buffering`) <https://nginx.org/en/docs/http/ngx_http_proxy_module.html>
- AWS ALB connection idle timeout <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html>
- Grigorik, 『High Performance Browser Networking』 "WebSocket" 장 <https://hpbn.co/websocket/> · "Server-Sent Events" 장
