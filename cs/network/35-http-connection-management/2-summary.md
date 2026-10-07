# network/35-http-connection-management — HTTP 연결 관리: keep-alive·커넥션 풀·idle timeout 정렬 — 정리 (힌트)

## 해결하는 문제

HTTPS 요청 하나를 새 연결로 보내면 요청 전에 왕복이 여러 번 든다.\
TCP 3-way handshake에 1 RTT, TLS 1.3에 1 RTT가 더 든다(29번).\
요청 자체가 1 RTT면 연결 준비가 요청보다 비싸다.

쉬운 예: 고객센터에 질문이 다섯 개 있다.\
질문마다 전화를 끊고 다시 걸면 매번 연결음과 본인 확인을 거친다.\
한 번 연결한 채 다섯 개를 연달아 물으면 그 비용이 한 번뿐이다.

똑같은 구조다.\
전화 연결 = TCP+TLS 연결, 통화 유지 = keep-alive(지속 연결), 여러 상담원 회선을 미리 잡아 두기 = 커넥션 풀.

그런데 통화를 유지하면 새 문제가 생긴다.\
상담원(서버)은 한동안 말이 없으면 전화를 끊는다.\
내가 막 질문을 꺼내는 순간 상대가 끊으면 질문이 허공에 뜬다.\
이 "끊는 시점 불일치"가 간헐 502·`ECONNRESET`의 대표 원인이다.

실무 예:
- 서비스 간 호출에서 커넥션 풀을 안 쓰면 요청마다 연결을 새로 맺어 지연과 CPU가 는다.
- 로드밸런서 뒤 Node 서버가 가끔 502를 낸다. 원인이 LB와 서버의 idle timeout 순서인 경우가 흔하다.
- 트래픽이 몰리면 "풀에서 연결을 얻지 못해" 타임아웃이 난다.

## 동작·원리

### 1. 새 연결 vs 재사용

```text
  새 연결마다 (HTTPS, TLS 1.3)                 재사용 (keep-alive)
  Client            Server                    Client            Server
    |--- SYN ---------->|  1 RTT                 |                  |
    |<-- SYN/ACK -------|                        |  (이미 연결됨)     |
    |--- ACK, ClientHello ->|  1 RTT              |                  |
    |<-- ServerHello ... Finished                |                  |
    |--- Finished, GET /a -->|  1 RTT            |--- GET /b ------>|  1 RTT
    |<-- 200 ------------|                       |<-- 200 ----------|
       응답까지 3 RTT (요청 전송은 2 RTT 뒤)          응답까지 1 RTT (요청은 즉시)
```

- 연결 재사용은 TCP·TLS 핸드셰이크를 건너뛴다.
- 이미 커진 TCP 혼잡 윈도도 이어서 쓸 수 있다. 새 연결은 slow start부터 다시 시작한다(18번).
  - 단 리눅스 기본값(`tcp_slow_start_after_idle=1`)에서는 요청 사이 유휴가 RTO를 넘길 때마다 cwnd가 절반으로 줄고, min(IW, cwnd)에서 멈춘다(18번 §6). 오래 쉰 연결은 핸드셰이크만 아끼고 윈도 이득은 줄어든다.

### 2. HTTP/1.1 지속 연결 규칙

RFC 9112 §9.3을 줄인 것이다. 가장 최근 메시지를 보고 판단한다.

```text
  Connection: close 가 있다          -> 이 응답 뒤 닫힌다
  HTTP/1.1 이상이다                  -> 유지된다 (기본값)
  HTTP/1.0 + Connection: keep-alive -> 조건부로 유지
  그 밖                             -> 닫힌다
```

- HTTP/1.1은 **지속 연결이 기본**이다. `Connection: keep-alive`를 쓰지 않아도 된다.
- 연결을 유지하려면 모든 메시지가 스스로 길이를 알려야 한다(`Content-Length` 또는 chunked).
  - 그래서 서버는 요청 본문을 끝까지 읽거나, 응답 뒤 연결을 닫아야 한다(MUST).
  - 클라이언트도 연결을 재사용하려면 응답 본문을 끝까지 읽어야 한다(MUST).
  - 읽다 만 바이트가 남으면 다음 응답의 시작으로 오해되기 때문이다.
- *keep-alive(HTTP)*: 응답 뒤에도 TCP 연결을 닫지 않고 다음 요청에 쓰는 것이다. TCP keepalive(21번, 빈 연결 생존 확인 패킷)와는 다른 개념이다.

### 3. HTTP/1.1은 한 연결에 한 번에 요청 하나

```text
  연결 1: [GET /a ......응답 a......][GET /b ..응답 b..]
                 ^
                 a가 느리면 b는 기다린다 (head-of-line blocking)

  해결: 연결을 여러 개 연다
  연결 1: [GET /a ......응답 a......]
  연결 2: [GET /b ..응답 b..]
```

- HTTP/1.1 응답에는 요청 식별자가 없다. 응답은 요청 순서대로만 온다(RFC 9112 §9.2).
- 파이프라이닝(응답을 기다리지 않고 요청을 연달아 보내기)은 규격상 허용(MAY)이지만, 응답은 여전히 순서대로다(§9.3.2).
- 그래서 클라이언트는 연결을 여러 개 연다(§9.4). 브라우저는 보통 호스트당 최대 6개를 연다(HPBN "HTTP/1.X").
- RFC는 연결 수 상한을 정하지 않고 "보수적으로" 열라고만 한다(§9.4).
- 이 제약을 한 연결 안에서 푸는 것이 HTTP/2 다중화다(36번).

### 4. 커넥션 풀

```text
                     +--------------------- 커넥션 풀 (호스트별) ---------------------+
  요청 --> acquire -->| idle 목록  [c3][c1]      <- 반납된 연결 (keep-alive 중)          |
                     | 사용 중    (c2)(c4)                                            |
                     | 대기 큐    r7 -> r8 -> r9  <- 한도(maxPerRoute)에 걸린 요청        |
                     +-------------------------------------------------------------+
                              |                                  ^
                              v                                  |
                        idle 있으면 꺼내 씀                       응답 본문 다 읽고 release
                        없고 한도 미만이면 새로 연결
                        한도면 대기 -> 대기 시간 초과 시 예외
```

- *acquire / release*: 풀에서 연결을 빌리고 돌려주는 동작이다.
- 풀의 핵심 설정
  - 호스트(route)별 최대 연결 수, 전체 최대 연결 수
  - idle 연결을 얼마나 오래 둘지(idle timeout, keep-alive duration)
  - 연결의 최대 수명(TTL). idle이 아니어도 일정 시간이 지나면 교체한다
  - 연결을 기다리는 최대 시간(connection request timeout)
- 기본값은 라이브러리마다 크게 다르다.

```text
  라이브러리                   기본값                                             근거
  OkHttp ConnectionPool       idle 최대 5개, 5분 비활성 시 축출                        OkHttp 소스
  Apache HttpClient 5 풀      전체 25, 호스트당 5                                     HttpClient 5 소스
  JDK HttpClient              idle 보관 30초 (jdk.httpclient.keepalive.timeout)       JDK 문서
  Node http.Agent             keepAlive false, maxSockets 무제한, 스케줄링 lifo          Node 문서
  Node http.globalAgent       v19부터 keep-alive 켜짐, 5초 타임아웃                     Node 문서
```

### 5. idle timeout 경합 — 가장 흔한 간헐 오류

```text
  클라이언트 풀 idle 유지: 60초       서버 keep-alive timeout: 5초

  t=0     요청 -> 응답. 연결은 풀로 돌아감 (idle)
  t=5.000 서버: "5초 조용했다" -> close() -> FIN 전송 ------------+
  t=5.001 클라이언트: 풀에서 이 연결을 꺼내 GET /x 전송 ---+        |
                                                        \      |
                                        (FIN이 아직 도착 전) \    v
  t=5.002 서버 커널: 닫힌 소켓에 데이터 도착 -> RST 응답
  t=5.003 클라이언트: ECONNRESET / "socket hang up"
          LB가 클라이언트였다면 -> 사용자에게 502
```

- RFC 9112 §9.5가 바로 이 경우를 든다. 서버는 idle 연결을 닫는 중이고, 클라이언트는 같은 순간 새 요청을 보내기 시작한다.
- 누구 잘못도 아니다. 연결은 **어느 쪽이든 언제든 닫을 수 있다**(MAY, §9.5).
- 해법의 원칙: **재사용하는 쪽(그 구간의 클라이언트)이 먼저 idle 연결을 버린다.**
  - 즉 구간마다 "클라이언트 idle timeout < 서버 keep-alive timeout"으로 맞춘다.
  - AWS ALB 문서도 애플리케이션의 idle timeout을 LB보다 크게 두라고 권한다. 그렇지 않으면 LB가 502를 낼 수 있다고 적는다.

### 6. 구간마다 정렬한다

```text
  Browser ----(구간 A)----> LB ----(구간 B)----> App Server ----(구간 C)----> DB/외부 API

  구간 A: 브라우저 idle  <  LB idle timeout
  구간 B: LB idle        <  App keep-alive timeout       <- 가장 흔한 사고 지점
  구간 C: App 풀 idle    <  상류 서버 keep-alive timeout

  예: ALB idle 60초 (기본값) 이면 App keep-alive는 60초보다 길게 (예: 65초, 예시)
      Node server.keepAliveTimeout 기본 5초 -> 그대로 두면 구간 B가 역전된다
```

- 대표 기본값

```text
  구성요소                          기본값      근거
  AWS ALB 연결 idle timeout          60초       ALB 문서
  nginx keepalive_timeout (클라 쪽)   75초       nginx core 문서
  Node server.keepAliveTimeout       5초        Node 문서
```

- 서버가 idle 시간을 알려 주기도 한다. `Keep-Alive: timeout=N` 응답 헤더다. Node `http.Agent`는 이 힌트에서 1초(`agentKeepAliveTimeoutBuffer` 기본값)를 빼서 먼저 소켓을 닫는다(Node 문서).

### 7. 깔끔하게 닫기

- 닫으려는 쪽은 `Connection: close`를 보내는 것이 권장이다(SHOULD, RFC 9112 §9.6).
- 서버가 소켓을 곧바로 완전히 닫으면, 클라이언트가 뒤이어 보낸 데이터 때문에 RST가 나간다. 그 RST가 클라이언트가 아직 읽지 못한 마지막 응답까지 지울 수 있다(§9.6 "TCP reset problem").
- 그래서 서버는 단계적으로 닫는다.
  1. 쓰기 방향만 닫는다(half-close, FIN 전송).
  2. 상대의 FIN이 오거나 마지막 응답이 전달됐다고 볼 때까지 계속 읽는다.
  3. 그 뒤 완전히 닫는다.
- FIN·RST·half-close 자체는 [19번](../19-tcp-termination-fin-rst-half-open/2-summary.md)에서 다룬다.

## 쓰이는 자료구조·알고리즘

- **호스트별 풀 맵** — 키 = (스킴, 호스트, 포트, 프록시·TLS 설정), 값 = 그 목적지의 연결 목록이다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **idle 연결 덱(LIFO/FIFO)** — 반납된 연결을 쌓아 두고 꺼낸다.
  - LIFO는 가장 최근에 쓴 연결을 먼저 꺼낸다. 요청이 드물 때 서버가 이미 닫았을 연결을 고를 위험이 낮다.
  - FIFO는 가장 오래 쉰 연결을 먼저 꺼낸다. 열린 연결 수가 많이 유지된다.
  - Node `http.Agent`의 기본은 `lifo`다(v15.6부터). [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **대기 큐(FIFO)** — 한도에 걸린 요청을 줄 세운다. 대기 시간 초과로 끊는다.
- **LRU 축출** — nginx `upstream`의 `keepalive N`은 worker마다 idle 연결을 N개까지 두고, 넘치면 가장 오래 안 쓴 연결부터 닫는다(nginx 문서). [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- **카운팅 세마포어** — "호스트당 최대 N개"는 허가 N개짜리 세마포어와 같은 구조다. [systems/semaphore](../../systems/semaphore/2-summary.md)
- **타이머로 idle 축출** — 백그라운드 작업이 주기적으로 idle 시간을 넘긴 연결을 닫는다(Apache HttpClient `evictIdleConnections`, OkHttp 정리 작업).

## 적용 — 풀어나가는 법

### 1. 호출 경로의 모든 구간을 표로 적는다

```text
  구간        클라이언트 쪽 idle         서버 쪽 keep-alive       관계
  브라우저→LB   (브라우저 내부)            ALB 60초                -
  LB→App      ALB 60초                  App ?초                 App > 60초 여야 함
  App→외부API  풀 idle ?초               외부 서버 ?초            풀 idle < 외부 서버
```

- 모르는 칸은 문서에서 기본값을 찾거나, 아래 방법으로 잰다.

### 2. 재사용 여부와 연결 수를 잰다

```bash
# 한 번의 curl에서 새로 맺은 연결 수 — URL 두 개를 연달아 요청해 재사용 확인
curl -s -o /dev/null -o /dev/null -w '%{num_connects}\n' https://api.example.com/a https://api.example.com/b

# 서버 쪽: 8080 포트로 들어온 ESTABLISHED 연결 수
ss -H -tan state established '( sport = :8080 )' | wc -l   # -H: 머리줄 빼기

# 클라이언트 쪽: 상류 443 포트로 나간 연결과 타이머(-o)
ss -tanpo '( dport = :443 )'

# 서버가 idle 연결을 몇 초에 닫는지: 요청 하나 보내고 FIN 시각을 본다
tcpdump -nn -i any 'tcp port 8080 and (tcp[tcpflags] & (tcp-fin|tcp-rst) != 0)'
```

- `%{num_connects}`는 해당 전송에서 새로 맺은 연결 수다(curl 문서). 두 번째 URL에서 0이면 재사용됐다.

### 3. 코드에서 — Node

```js
const http = require('node:http');

// 서버: LB idle(예: ALB 60초)보다 길게
const server = http.createServer(handler);
server.keepAliveTimeout = 65_000;      // 기본 5000ms

// 클라이언트: 상류 서버보다 짧게 쉬게 하고, 재사용 소켓 실패는 멱등 요청만 재시도
const agent = new http.Agent({ keepAlive: true, maxSockets: 50, timeout: 30_000 });
function get(url, retried = false) {
  const req = http.get(url, { agent }, onResponse);
  req.on('error', (err) => {
    if (!retried && req.reusedSocket && err.code === 'ECONNRESET') get(url, true);
    else onError(err);
  });
}
```

- `req.reusedSocket`으로 "재사용 소켓에서 난 리셋"만 골라 재시도하는 방법은 Node 문서의 예시다. POST 같은 비멱등 요청에는 쓰지 않는다(33번).

### 4. 코드에서 — Java (Apache HttpClient 5)

```java
PoolingHttpClientConnectionManager cm = PoolingHttpClientConnectionManagerBuilder.create()
    .setMaxConnTotal(200)
    .setMaxConnPerRoute(50)
    .setDefaultConnectionConfig(ConnectionConfig.custom()
        .setValidateAfterInactivity(TimeValue.ofSeconds(2))  // 오래 쉰 연결은 쓰기 전 점검
        .setTimeToLive(TimeValue.ofMinutes(5))                 // 최대 수명
        .build())
    .build();

CloseableHttpClient client = HttpClients.custom()
    .setConnectionManager(cm)
    .evictIdleConnections(TimeValue.ofSeconds(30))            // 상류 keep-alive보다 짧게
    .setDefaultRequestConfig(RequestConfig.custom()
        .setConnectionRequestTimeout(Timeout.ofSeconds(1))     // 풀 대기 상한
        .build())
    .build();

try (CloseableHttpResponse res = client.execute(new HttpGet(url))) {
    EntityUtils.consume(res.getEntity());   // 본문을 끝까지 읽어야 연결이 풀로 돌아간다
}
```

### 5. 프록시(nginx) — 상류 연결 재사용

```nginx
upstream app {
    server 10.0.0.11:8080;
    keepalive 32;                  # worker당 idle 연결 최대 32개 (1.29.7부터 기본 활성)
}
server {
    location / {
        proxy_pass http://app;
        proxy_http_version 1.1;    # 1.29.7 전에는 기본이 1.0이라 명시 필요
        proxy_set_header Connection "";
    }
}
```

- nginx 1.29.7부터 상류 keepalive가 기본으로 켜지고 `proxy_http_version`의 기본이 1.1이 됐다(nginx 문서). 이전 버전은 위 두 줄이 있어야 재사용된다.

## 장애 시나리오와 대처

### 1. idle close 경합 — `socket hang up`·`Connection reset`·간헐 502

- **현상**: 트래픽이 적을 때 오히려 오류가 난다. 1% 미만의 요청이 무작위로 실패한다.
- **보이는 형태**
  - Node 클라이언트: `Error: socket hang up`, `code: 'ECONNRESET'`(Node 문서: 응답 전에 연결이 닫히면 이 오류).
  - Java: `java.net.SocketException: Connection reset`, Apache HttpClient의 `NoHttpResponseException`.
  - LB 뒤라면 사용자에게 502. AWS ALB는 "요청 처리 중 대상이 RST·FIN으로 닫음"을 502 원인으로 들고, 대상 keep-alive가 LB idle timeout보다 짧은지 확인하라고 적는다.
  - `tcpdump`에서 서버의 FIN 직후 클라이언트 요청 → 서버 RST 순서가 보인다.
- **원인**: 구간의 서버 keep-alive timeout이 클라이언트(또는 LB) idle timeout보다 짧다. 서버가 닫는 순간 클라이언트가 재사용한다(RFC 9112 §9.5).
- **대처**
  - 구간마다 "클라이언트 idle < 서버 keep-alive"로 맞춘다. 예: ALB 60초 뒤 Node면 `server.keepAliveTimeout`을 60초보다 크게.
  - 클라이언트 풀의 idle 축출을 서버 값보다 짧게 둔다.
  - 멱등 요청에 한해 "재사용 연결에서 난 리셋"은 한 번 재시도한다.

### 2. 풀 고갈 — 연결을 기다리다 타임아웃

- **현상**: 상류는 멀쩡한데 호출 쪽 지연이 급등하고 타임아웃이 쏟아진다.
- **보이는 형태**
  - Apache HttpClient 4.x: `ConnectionPoolTimeoutException: Timeout waiting for connection from pool`(4.5.x 소스). 5.x도 `connectionRequestTimeout`을 넘기면 연결 요청 타임아웃으로 실패한다(예외 이름은 버전별로 확인).
  - 풀 지표에서 leased = max, pending > 0이 계속된다.
  - 스레드 덤프에 풀 대기 스레드가 줄지어 있다.
- **원인**
  - 응답 본문을 끝까지 읽지 않거나 응답을 닫지 않아 연결이 반납되지 않는다(누수).
  - 상류가 느려져 연결이 오래 붙잡힌다. 호스트당 한도(Apache 기본 5)가 트래픽보다 작다.
  - 풀 대기 시간이 타임아웃 계산에 안 들어가 있어 실제 지연 = 대기 + 호출이 된다.
- **대처**
  - 응답을 `try-with-resources`로 닫고 본문을 소비한다.
  - 호스트당 한도를 부하에 맞추되, 상류 용량을 넘지 않게 한다.
  - 풀 대기 타임아웃을 짧게 두고 빠르게 실패시킨다([ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md)).
  - 타임아웃 층위는 reliability/07 타임아웃 분류에서 다룬다.

### 3. 재사용이 안 돼 요청마다 새 연결 — TIME_WAIT 폭증·포트 고갈

- **현상**: 초당 요청이 늘자 `connect()`가 실패한다. CPU 사용량도 높다.
- **보이는 형태**
  - `EADDRNOTAVAIL`(Cannot assign requested address).
  - `ss -tan state time-wait | wc -l` 값이 수만 단위다.
  - `curl -w '%{num_connects}'`가 매 요청 1이다.
- **원인**
  - 프록시가 상류에 HTTP/1.0으로 말해 연결을 매번 닫는다(nginx 1.29.7 이전 기본값).
  - 클라이언트가 keep-alive를 끈 에이전트를 쓴다(Node `http.Agent` 기본 `keepAlive: false`).
  - 응답을 끝까지 읽지 않아 라이브러리가 연결을 버린다.
- **대처**: 상류 keepalive를 켠다(`proxy_http_version 1.1`, `keepalive N`). 클라이언트 에이전트·풀을 공유한다. TIME_WAIT 자체는 20번(time-wait)에서 다룬다.

### 4. 연결이 너무 오래 살아 새 서버가 트래픽을 못 받는다

- **현상**: 서버를 늘렸는데 새 인스턴스의 CPU가 놀고, 기존 인스턴스만 뜨겁다. 또는 배포 뒤에도 옛 인스턴스로 요청이 간다.
- **보이는 형태**: 인스턴스별 연결 수·요청 수가 크게 불균형하다. 새 인스턴스의 `ss` 연결 수가 거의 0이다.
- **원인**: 클라이언트가 지속 연결을 무한히 재사용한다. 대상을 연결 수립 때 고르는 구간에서는 기존 연결이 옛 서버에 고정된다.
  - 연결 단위로 고르는 곳: L4 분산(NLB 등), 클라이언트가 대상 IP로 직접 붙는 DNS·클라이언트 측 분산.
  - L7 LB(ALB, nginx `upstream`)는 요청마다 대상을 고른다(AWS ALB 문서). 이 경우 클라이언트↔LB 연결이 오래 살아도 요청은 분산된다.
- **대처**
  - 연결에 최대 수명을 둔다. nginx `keepalive_time`(기본 1시간), `keepalive_requests`(기본 1000), ALB "HTTP client keepalive duration"(기본 3600초), 클라이언트 풀 TTL.
  - 서버 종료 시 `Connection: close`나 HTTP/2 `GOAWAY`로 클라이언트에게 재연결을 유도한다([ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md)).

### 5. 중간 장비가 idle 연결을 조용히 버림 — 다음 요청이 한참 멈춘다

- **현상**: 한동안 호출이 없던 뒤 첫 요청만 수십 초~수 분 멈췄다가 실패한다.
- **보이는 형태**: 읽기 타임아웃 또는 `ETIMEDOUT`. `tcpdump`에서 요청 패킷이 재전송만 반복되고 응답이 없다.
- **원인**: NAT·방화벽이 idle 연결 상태를 지웠다. 양 끝은 연결이 살아 있다고 믿는 half-open 상태다(19번). 이후 패킷은 버려진다.
- **대처**
  - 클라이언트 풀 idle 축출을 중간 장비의 idle timeout보다 짧게 둔다.
  - 필요하면 TCP keepalive나 앱 heartbeat로 상태를 유지한다(21번).
  - 쓰기 전 오래 쉰 연결을 점검한다(Apache `validateAfterInactivity`).

## 핵심 문장

- HTTP/1.1은 지속 연결이 기본이고, 재사용하려면 양쪽 모두 메시지를 끝까지 읽어야 한다.
- 연결은 어느 쪽이든 언제든 닫을 수 있어서, 서버가 idle 연결을 닫는 순간 클라이언트가 재사용하면 `ECONNRESET`·`socket hang up`·502가 난다.
- 구간마다 "재사용하는 쪽(클라이언트) idle < 받는 쪽(서버) keep-alive"로 정렬한다. ALB 60초 뒤 Node 기본 5초는 역전된 조합이다.
- 커넥션 풀은 호스트별 연결 목록 + 한도 + 대기 큐이고, 본문을 소비하지 않거나 응답을 닫지 않으면 연결이 반납되지 않아 풀이 고갈된다.
- 연결 단위로 분산하는 구간(L4·클라이언트 측)에서는 연결에 최대 수명을 두지 않으면 새 서버에 트래픽을 나누지 못한다.

## 관련 주제·근거

- 선행
  - `33-http-semantics` — [33-http-semantics](../33-http-semantics/2-summary.md)
  - [21-tcp-keepalive-and-user-timeout](../21-tcp-keepalive-and-user-timeout/2-summary.md)
  - `19-tcp-termination-fin-rst-half-open` — [19번](../19-tcp-termination-fin-rst-half-open/2-summary.md)
  - `29-tls-handshake` — 새 연결의 TLS 비용. [29번](../29-tls-handshake/2-summary.md)
- 후속
  - `36-http2-multiplexing` — 한 연결 안의 다중화. [36번](../36-http2-multiplexing/2-summary.md)
  - [20-time-wait-and-close-wait](../20-time-wait-and-close-wait/2-summary.md)
  - [46-load-balancers-and-proxies](../46-load-balancers-and-proxies/2-summary.md)
  - [reliability/07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md)
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) — 재사용 소켓 실패 재시도의 범위
- RFC 9112 HTTP/1.1 §9 Connection Management <https://www.rfc-editor.org/rfc/rfc9112>
  - §9.2 응답-요청 대응(순서) · §9.3 지속 연결 규칙 · §9.3.1 재시도 · §9.3.2 파이프라이닝 · §9.4 동시 연결 수 · §9.5 실패와 타임아웃(idle close 경합) · §9.6 종료와 TCP reset 문제 · §9.8 TLS 종료
- RFC 9110 §9.2.2 멱등과 자동 재시도 <https://www.rfc-editor.org/rfc/rfc9110>
- Grigorik, 『High Performance Browser Networking』 "HTTP/1.X" 장(keep-alive, 호스트당 6연결) <https://hpbn.co/http1x/>
- Node.js `http` 문서(`server.keepAliveTimeout`, `http.Agent` 옵션, `http.globalAgent`, `request.reusedSocket`, `socket hang up`) <https://nodejs.org/api/http.html>
- nginx `keepalive_timeout`·`keepalive_time`·`keepalive_requests` <https://nginx.org/en/docs/http/ngx_http_core_module.html> · `upstream keepalive` <https://nginx.org/en/docs/http/ngx_http_upstream_module.html> · `proxy_http_version` <https://nginx.org/en/docs/http/ngx_http_proxy_module.html>
- AWS ALB 개요(요청을 받은 뒤 리스너 규칙을 평가하고 대상 그룹에서 대상을 고름) <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html>
- AWS ALB 속성(연결 idle timeout 60초, HTTP client keepalive duration) <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html> · 문제 해결(502 원인) <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html>
- OkHttp `ConnectionPool` 소스 <https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/ConnectionPool.kt>
- Apache HttpClient 5 `PoolingHttpClientConnectionManager`·`ConnectionConfig` 소스 <https://github.com/apache/httpcomponents-client>
- JDK `java.net.http` 모듈 속성(`jdk.httpclient.keepalive.timeout`) <https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/module-summary.html>
- curl `-w` 변수(`num_connects`) <https://curl.se/docs/manpage.html>
