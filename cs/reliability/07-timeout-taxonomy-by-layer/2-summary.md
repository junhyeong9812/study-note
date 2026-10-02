# reliability/07-timeout-taxonomy-by-layer — 호출 하나에 달린 타임아웃의 종류와 포함 관계 — 정리 (힌트)

## 해결하는 문제

"타임아웃 3초를 걸었다"는 말은 불완전하다. **무엇을** 3초 기다리는지가 빠져 있다.\
HTTP 호출 하나에는 시간이 흐르는 구간이 여럿 있고, 라이브러리의 "timeout" 하나는 그중 일부만 덮는다.

```text
 개발자 생각: "타임아웃 3초 걸었으니 최악 3초"
 실제:
   풀에서 커넥션 대기 30 s (HikariCP 기본) ─┐
   connect: SYN이 버려짐 → 커널 재전송 약 131 s ─┤  이 구간들이 "3초"에 안 들어 있으면
   본문이 300ms마다 1바이트씩 → 읽기 idle 1 s는 영원히 안 터짐 ─┘  최악은 3초가 아니다
```

- *구간 타임아웃*: 호출의 한 구간(연결, 첫 바이트, 바이트 사이 등)만 재는 상한.
- *전체(call) 타임아웃*: 호출 시작부터 본문 끝까지 전체를 재는 상한. 라이브러리에 따라 없거나 기본이 꺼져 있다.

쉬운 예: 택배 배송 약속이다.
- "기사님이 출발한 뒤 3시간 안에 오면 된다"고만 정하면, 물류센터에서 하루 대기한 시간은 안 센다.
- "트럭이 10분마다 조금씩이라도 움직이면 괜찮다"고 정하면, 하루 종일 조금씩 움직이는 트럭은 끝나지 않는다.
- 필요한 것은 "주문부터 문 앞까지 이틀"이라는 전체 약속과, 구간별 약속을 함께 두는 것이다.

똑같은 구조다.\
실무 예: 방화벽에 막힌 호출이 2분 넘게 스레드를 잡는 사고, 천천히 흘러오는 응답(slow drip)이 끝나지 않는 사고, 배포 직후 새 TLS 연결 때문에만 나는 타임아웃(AWS Builders' Library 사례).

## 동작·원리

### 1. 호출 하나의 시간 조각

```text
 [호출 밖]  커넥션 idle 수명 · 최대 수명(maxLifetime) ─ 풀의 연결을 언제 닫나(idle은 놀고 있는 시간, 최대 수명은 연결의 나이)
 ───────────────────────────────────────────────────────────────────────────────
 [호출]
  ① 풀 획득 대기          연결을 빌리려고 줄 선다           풀 acquire 타임아웃
  ② DNS 조회              이름 → 주소                       (대개 전체에만 포함)
  ③ TCP connect           SYN → SYN-ACK → ACK               connect 타임아웃
  ④ TLS 핸드셰이크         인증서·키 교환                     TLS 타임아웃 / connect에 포함되기도
  ⑤ 요청 쓰기              헤더 + 본문 전송                   write 타임아웃
  ⑥ 첫 바이트(응답 헤더)    서버 처리 시간 대부분이 여기        response-header 타임아웃
  ⑦ 본문 읽기              바이트가 띄엄띄엄 온다              read(idle) 타임아웃 = 바이트 "사이" 간격
 ───────────────────────────────────────────────────────────────────────────────
  ①~⑦ 전체                                                  call / total 타임아웃 (있다면)
```

- ②~④는 새 연결을 맺을 때만 생긴다. 재사용 연결이면 건너뛴다. 그래서 첫 요청·배포 직후에만 느린 현상이 나온다.
- ⑦의 read 타임아웃은 대개 **바이트 사이 간격**이다. 바이트가 조금씩이라도 오면 다시 센다. 총 시간의 상한이 아니다.
  - AWS Builders' Library는 Linux `SO_RCVTIMEO`가 끝에서 끝까지의 타임아웃으로 쓰기에 맞지 않는다고 적는다. Java는 이것을 그대로 노출한다(`Socket.setSoTimeout`).
- ①은 소켓 바깥이다. 라이브러리의 HTTP 타임아웃에 들어가지 않는 경우가 많다. 실제 지연 = 대기 + 호출이다.
  - *풀 획득 대기(acquire wait)*: 풀의 연결이 모두 빌려 나가 있을 때 반납을 기다리는 시간. HikariCP는 `connectionTimeout`(기본 30000ms)이 이 값이다(HikariCP README).

### 2. 라이브러리마다 다른 이름·기본값·포함 범위

| 라이브러리(버전) | 설정 | 기본값 | 덮는 구간 |
|---|---|---|---|
| JDK `HttpClient` (21) | `connectTimeout` | 비어 있음(설정 안 하면 상한 없음) | ③(새 연결일 때만) |
| | `HttpRequest.timeout` | 무한 | 응답을 받을 때까지 — 실험상 ⑥까지, ⑦ 미포함(아래 실험 B) |
| OkHttp 4.12 | `connectTimeout` · `readTimeout` · `writeTimeout` | 10 s · 10 s · 10 s | ③(TCP connect만 — ④는 개별 읽기마다 `readTimeout`) · ⑦ 개별 읽기 · ⑤ 개별 쓰기 |
| | `callTimeout` | 0(없음) | DNS·연결·요청 본문 쓰기·서버 처리·응답 본문 읽기 전체, 리다이렉트·재시도 포함 |
| Go `net/http` (1.23) | `Client.Timeout` | 0(없음, `DefaultClient`) | 연결·리다이렉트·본문 읽기까지 전체 |
| | `DefaultTransport` Dialer `Timeout` · `TLSHandshakeTimeout` · `ResponseHeaderTimeout` | 30 s · 10 s · 0 | ②③(Dialer `Timeout`은 필요하면 DNS 조회도 포함 — `net/dial.go`) · ④ · 요청을 다 쓴 뒤 ⑥(본문 제외) |
| undici(Node `fetch`) | `connectTimeout` · `headersTimeout` · `bodyTimeout` | 10 s · 300 s · 300 s | ③(HTTPS면 ④ TLS까지 — `lib/core/connect.js`가 `secureConnect`에서 타이머를 끈다) · ⑥ · ⑦ 청크 사이 간격 |
| Envoy | cluster `connect_timeout` | 5 s | ③ + 상류 TLS면 ④ 포함 |
| | route `timeout` | 15 s | 하류 요청을 **다 받은 뒤**부터 상류의 완전한 응답까지 |
| | `stream_idle_timeout` · `idle_timeout`(HTTP) · `max_connection_duration` | 5 min · 1 h · 0(무제한) | 스트림 무활동 · 연결 무활동 · 연결 수명 |
| HikariCP | `connectionTimeout` · `idleTimeout` · `maxLifetime` | 30 s · 10 min · 30 min | ① · 풀의 놀고 있는 연결(`minimumIdle < maximumPoolSize`일 때만 적용 — 기본은 둘이 같아 적용 안 됨) · 연결 최대 수명(나이 기준, 사용 중인 연결은 반납될 때 닫힘) |

- 출처: JDK 21 API(`HttpClient.connectTimeout()` — 설정 안 했으면 Optional이 비어 있다, `HttpRequest.Builder.timeout` — 설정 안 하면 무한), OkHttp 4.12.0 `OkHttpClient.kt`, `go doc net/http`(go1.23.12), undici `docs/api/Client.md`(main, 2026-10-01 열람), Envoy FAQ "How do I configure timeouts?", HikariCP README.
- OkHttp 4.12 `connectTimeout`은 문서상 "TCP 소켓을 연결할 때"만 적용된다. 소스(`RealConnection.kt`)는 connect 전에 소켓 `soTimeout = readTimeout`을 걸고 그다음 TLS `startHandshake()`를 하므로, ④는 전체 상한이 아니라 개별 읽기 상한(`readTimeout`)의 지배를 받는다.
- 같은 이름이 다른 것을 뜻한다. "read timeout"은 OkHttp에서는 개별 읽기, undici에서는 `bodyTimeout`(청크 사이), JDK `HttpClient`에는 따로 없다.
- **기본이 무한인 것**: JDK `HttpClient`의 요청 timeout, Go `DefaultClient`의 `Timeout`, OkHttp `callTimeout`. 전체 상한을 직접 걸지 않으면 없다.

### 3. 실험 A: connect 타임아웃이 없을 때 — SYN이 버려지면 얼마나 멈추나

- SYN을 버리는 상대: `accept()`를 하지 않는 서버의 accept 큐를 가득 채웠다. 리눅스는 accept 큐가 차면 새 SYN을 버린다(원리는 [network/15-tcp-handshake-and-backlog](../../network/15-tcp-handshake-and-backlog/2-summary.md) 「큐가 가득 찼을 때」).
- 컨테이너마다 `net.ipv4.tcp_syn_retries`를 바꿨다(`docker run --sysctl`). 작성 환경 커널은 7.0이고 `tcp_syn_linear_timeouts=4`였다.

```java
ServerSocket ss = new ServerSocket(18091, 1, InetAddress.getByName("127.0.0.1")); // backlog 1, accept 안 함
// ... 연결 둘로 accept 큐를 채운다
s.connect(addr, 1000);   // (a) connect 타임아웃 1초
s.connect(addr);         // (b) 타임아웃 없음(0 = 무한, OS 재전송 한도까지)
```

(실험, JDK 21.0.12 Temurin, 리눅스 7.0.0, 컨테이너 `--cpus=2`, 2026-10-01)

```text
tcp_syn_retries=2 tcp_syn_linear_timeouts=4
채움 0: 연결됨 5ms
채움 1: 연결됨 0ms
채움 2: 300ms 안에 안 됨 → 큐가 찼다
connect(timeout=1000ms): 1001ms 뒤 java.net.SocketTimeoutException: Connect timed out
connect(타임아웃 없음): 7202ms 뒤 java.net.ConnectException: Connection timed out
tcp_syn_retries=3 tcp_syn_linear_timeouts=4
connect(timeout=1000ms): 1001ms 뒤 java.net.SocketTimeoutException: Connect timed out
connect(타임아웃 없음): 19726ms 뒤 java.net.ConnectException: Connection timed out
tcp_syn_retries=5 tcp_syn_linear_timeouts=4
connect(timeout=1000ms): 1000ms 뒤 java.net.SocketTimeoutException: Connect timed out
connect(타임아웃 없음): 68223ms 뒤 java.net.ConnectException: Connection timed out
```

(3·5의 "채움" 줄은 2와 같아 생략했다.) `tcp_syn_retries=2`일 때 tcpdump로 본 마지막 연결의 SYN(포트 58866)은 이렇다.

```text
1790834713.884854 IP 127.0.0.1.58866 > 127.0.0.1.18091: Flags [S], seq 2482382544, ...
1790834714.909764 IP 127.0.0.1.58866 > 127.0.0.1.18091: Flags [S], seq 2482382544, ...
1790834715.933771 IP 127.0.0.1.58866 > 127.0.0.1.18091: Flags [S], seq 2482382544, ...
1790834716.957772 IP 127.0.0.1.58866 > 127.0.0.1.18091: Flags [S], seq 2482382544, ...
1790834717.981783 IP 127.0.0.1.58866 > 127.0.0.1.18091: Flags [S], seq 2482382544, ...
1790834719.005756 IP 127.0.0.1.58866 > 127.0.0.1.18091: Flags [S], seq 2482382544, ...
```

- 관찰 1: connect 타임아웃 1초는 세 경우 모두 1.0초에 끝났다. 없으면 7.2초·19.7초·68.2초였다.
- 관찰 2: SYN은 처음 것 포함 6개(재전송 5번)가 약 1초 간격으로 나갔고, 약 7.2초에 포기했다. 커널 `tcp_timer.c`(리눅스 master)의 SYN-SENT 포기 조건은 둘 중 먼저 오는 것이다. (a) 재전송 수 ≥ `tcp_syn_retries + tcp_syn_linear_timeouts` (b) 첫 SYN 뒤 경과 시간 ≥ 지수 백오프 모델 시간 `(2^(tcp_syn_retries+1) - 1) × 초기 RTO`(1초 기준 retries=2면 7초). retries=2에서는 (b)가 먼저 와서 재전송 5번에서 끝났다. 선형 구간에서는 RTO를 두 배로 늘리지 않는다(ip-sysctl: 1, 1, 1, 1, 1, 2, 4, …).
- 계산(해석): 타이머는 1,2,3,4,5,7,11,19,35,67,131초에 울리고, 위 (a)·(b) 중 하나가 처음 참이 되는 타이머에서 포기한다. 2 → 7초, 3 → 19초, 5 → 67초다. 측정값(7.2·19.7·68.2)과 맞는다. 기본값 6이면 마지막 재전송이 67초, 포기는 **131초**다 — ip-sysctl 문서 `tcp_syn_retries`("67seconds … till the last retransmission", "final timeout … after 131seconds")·network/15와 같다(6은 이번에 직접 재지 않았다).

### 4. 실험 B: 읽기(idle) 타임아웃 vs 전체 타임아웃 — slow drip

- 서버 `/drip`: 헤더를 즉시 보내고 본문 20바이트를 300ms마다 1바이트씩(약 6초). `/slowhead`: 2초 뒤에 헤더.
- 클라이언트 넷: (1) `Socket` + `setSoTimeout(1000)`만 (2) JDK `HttpClient` 요청 timeout 1초 → `/drip` (3) 같은 설정 → `/slowhead` (4) (1)에 전체 데드라인 1.5초를 직접 얹은 것.

```java
// (4) 전체 데드라인: 남은 시간으로 매번 SO_TIMEOUT을 줄인다
long deadline = start + 1500;
while (true) {
    long left = deadline - System.currentTimeMillis();
    if (left <= 0) throw new SocketTimeoutException("전체 데드라인 초과");
    s.setSoTimeout((int) Math.min(1000, left));   // idle 1s와 남은 전체 중 작은 쪽
    if (in.read() == -1) break;
}
```

(실험, JDK 21.0.12 Temurin, HTTP/1.1, 127.0.0.1, 2026-10-01 — t는 각 시도의 시작 기준)

```text
t= 6017ms (1) SO_TIMEOUT=1s만: 타임아웃 없이 끝까지 받음, 78바이트
t= 6150ms (2) HttpClient timeout=1s /drip: 완료 status=200 본문 20바이트
t= 1011ms (3) HttpClient timeout=1s /slowhead: java.net.http.HttpTimeoutException: request timed out
t= 1502ms (4) idle 1s + 전체 1.5s: Read timed out
```

같은 서버 모양을 Node 18.19.1 `fetch` + `AbortSignal.timeout(1000)`으로 부르면:

```text
t=  251ms 헤더 받음 status=200
t= 1040ms 중단: TimeoutError The operation was aborted due to timeout
```

- 관찰 1: 바이트 사이 간격(300ms)이 1초보다 짧으니 `SO_TIMEOUT`은 한 번도 터지지 않았다. 6초가 걸렸다(78바이트 = 헤더 포함).
- 관찰 2: JDK `HttpClient`의 요청 timeout 1초도 `/drip`에서는 터지지 않고 6.15초(재실행 6.21초) 뒤 200으로 끝났다. 헤더가 2초 늦은 `/slowhead`에서는 1.0초에 터졌다. 이 환경(JDK 21.0.12, `BodyHandlers.ofString`)에서 요청 timeout은 **응답 헤더까지**만 덮었다. API 문서는 "응답을 받지 못하면(If the response is not received)"이라고만 적는다.
- 관찰 3: 전체 데드라인을 직접 얹은 (4)는 1.5초에 끊겼다. Node의 `AbortSignal`은 본문을 읽는 도중에도 1.04초(재실행 1.03초)에 끊었다 — 신호가 본문 읽기까지 걸려 있다.
- 해석: "읽기 타임아웃만 있다"는 것은 "조금씩이라도 오면 영원히 기다린다"는 뜻이다. 전체 상한이 따로 필요하다.

### 5. 새 연결 비용이 타임아웃에 들어가는 순간 — AWS 사례

- AWS Builders' Library(Brooker)의 사례: 의존 서비스 호출 타임아웃을 약 20ms로 아주 짧게 잡았다. 평소에는 타임아웃이 없었는데 **배포 직후에만** 조금씩 났다.
- 원인: 타이머에 새 보안 연결(TLS) 수립이 들어 있었다. 이 연결은 다음 요청부터 재사용되므로, 새 서버가 투입된 직후 첫 요청들만 20ms를 넘었다.
- 처음에는 연결을 새로 맺는 경우 타임아웃을 늘려 우회했고, 나중에는 트래픽을 받기 전 시작 단계에서 연결을 미리 맺어 문제를 없앴다.
- 같은 글은 DNS나 TLS 핸드셰이크를 덮지 않는 타임아웃 구현도 있다고 적는다. 그래서 잘 검증된 클라이언트의 내장 타임아웃을 우선 쓰고, 직접 만들면 소켓 옵션의 정확한 의미를 확인하라고 한다.

## 쓰이는 자료구조·알고리즘

- **타이머 힙·타이머 휠** — 연결·요청마다 타이머가 붙는다. 수만 개를 싸게 관리하려고 Netty·커널은 타이머 휠 계열을 쓴다. data-structure 26 `timer-structures`(미작성, [data-structure 커리큘럼](../../data-structure/curriculum.md)), 힙은 [data-structure/07-heap](../../data-structure/07-heap/2-summary.md).
- **지수 백오프(SYN 재전송)** — 커널의 SYN 재전송은 선형 몇 번 뒤 RTO를 두 배씩 늘린다(실험 A).
- **커넥션 풀 = 대기 큐 + 자원 집합** — 빌릴 연결이 없으면 대기 큐에 선다. 대기 상한이 ① 타임아웃이다. [network/35-http-connection-management](../../network/35-http-connection-management/2-summary.md) §4.
- **상태 기계(TCP)** — connect 타임아웃은 SYN-SENT 상태의 체류 상한이다.

## 적용 — 풀어나가는 법

### 1. 호출마다 표를 채운다

| 구간 | 설정 이름(우리 라이브러리) | 값 | 근거 |
|---|---|---|---|
| ① 풀 획득 | | | 남은 예산 이하 |
| ③④ 연결·TLS | | | 같은 리전 RTT 몇 배 + 핸드셰이크 |
| ⑥ 첫 바이트 | | | 하류 p99.x |
| ⑦ 읽기 idle | | | 스트리밍이면 필수 |
| 전체 | | | 상위 데드라인에서 받은 남은 예산 |

- 빈칸이 있으면 그 구간의 실제 상한은 "라이브러리 기본값" 또는 "OS 기본값"이다. 둘 다 찾아 적는다.
- 전체 값이 어떤 구간 값보다 짧으면, 그 구간 타임아웃은 이 호출에서 먼저 발동하지 못한다(전체가 먼저 끊는다). 구간 값이 의미를 가지려면 전체가 더 길어야 한다. 전체를 정하는 법은 [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md).

### 2. 코드 — OkHttp(구간 + 전체)

```java
OkHttpClient client = new OkHttpClient.Builder()
        .connectTimeout(Duration.ofMillis(500))   // ③ (예시)
        .readTimeout(Duration.ofSeconds(2))        // ⑦ 개별 읽기 간격
        .writeTimeout(Duration.ofSeconds(2))       // ⑤
        .callTimeout(Duration.ofSeconds(3))        // 전체: DNS~본문 끝, 재시도·리다이렉트 포함
        .build();
```

### 3. 코드 — JDK `HttpClient`(전체 상한이 없으므로 직접)

```java
HttpClient c = HttpClient.newBuilder().connectTimeout(Duration.ofMillis(500)).build();
HttpRequest req = HttpRequest.newBuilder(uri).timeout(Duration.ofSeconds(2)).build(); // 헤더까지
// 본문은 스트림으로 받아 남은 시간을 직접 검사한다(실험 B의 (4)와 같은 방식)
HttpResponse<InputStream> r = c.send(req, HttpResponse.BodyHandlers.ofInputStream());
try (InputStream in = r.body()) {
    byte[] buf = new byte[8192];
    for (int n; (n = in.read(buf)) != -1; ) {
        if (deadline.expired()) throw new TimeoutException("본문 읽기 중 데드라인 초과");
        sink.write(buf, 0, n);
    }
}
```

- 주의: 이 검사는 `read()`가 돌아와야 실행된다. 바이트가 완전히 멈추면 `read()`에서 막힌다. 막힌 읽기를 끊으려면 별도 타이머가 스트림을 닫아야 한다.

### 4. 코드 — Node `fetch`(신호 하나가 본문까지)

```ts
const res = await fetch(url, { signal: AbortSignal.timeout(remainingMs) });
const body = await res.text();   // 같은 신호가 본문 읽기도 끊는다(실험 B)
```

### 5. 진단

```bash
# 시작부터 각 단계 끝까지의 누적 시간(초). 구간 시간은 차이로 구한다(TLS = tls - tcp)
curl -s -o /dev/null -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://api.example.com/x
# connect에서 멈춘 연결(SYN-SENT)과 재전송 타이머
ss -tanoi state syn-sent
# SYN 재전송 한도
sysctl net.ipv4.tcp_syn_retries net.ipv4.tcp_syn_linear_timeouts
# 자바 스레드가 어디서 멈췄나: connect / read
jcmd <pid> Thread.print | grep -A5 -E 'Net.connect|SocketDispatcher.read|NioSocketImpl'
```

## 장애 시나리오와 대처

### 1. connect 타임아웃 미설정 → 방화벽 DROP에 2분 멈춤 (⚠ 커리큘럼)

- 현상: 보안 그룹 변경 직후 호출이 2분 넘게 멈췄다가 실패한다. 그 사이 스레드 풀이 마른다.
- 보이는 형태: `ss`에 SYN-SENT 연결이 쌓인다. 스레드 덤프에 `Net.connect`에서 멈춘 스레드. 결국 `ConnectException: Connection timed out`.
- 원인: connect 상한이 OS 기본(재전송 한도)이다. 기본 `tcp_syn_retries=6`이면 리눅스 6.5+에서 약 131초다(실험 A의 계산, network/15).
- 대처: 모든 클라이언트에 connect 타임아웃(실험 A: 1초로 1.0초에 끝남). `tcp_syn_retries`를 줄이는 것은 호스트 전체에 영향이 있어 마지막 수단이다.

### 2. 읽기(idle) 타임아웃만 있다 → slow drip이 끝나지 않는다 (⚠ 커리큘럼)

- 현상: 상대 서버가 과부하로 응답을 아주 천천히 흘린다. 호출이 수십 초~수 분 걸리는데 타임아웃 에러는 없다.
- 보이는 형태: 지연 분포에 아주 긴 꼬리, 에러율은 낮다. 스레드 덤프에 소켓 `read`.
- 원인: read 타임아웃은 바이트 사이 간격이다(실험 B (1)). JDK `HttpClient`의 요청 timeout은 이 환경에서 헤더까지만 덮었다(실험 B (2)).
- 대처: 전체 타임아웃을 따로 건다(OkHttp `callTimeout`, Go `Client.Timeout`, Node `AbortSignal`, 직접 구현 (4)).

### 3. 풀 대기가 타임아웃에 안 들어간다 → 실제 지연 = 대기 + 호출 (⚠ 커리큘럼)

- 현상: 호출 타임아웃은 2초인데 사용자 지연이 30초를 넘는다.
- 보이는 형태: 풀 지표의 대기 수·대기 시간 증가(Micrometer로 내보낸 HikariCP `hikaricp.connections.pending` — Prometheus 이름 `hikaricp_connections_pending`), `SQLTransientConnectionException`("<풀 이름> - Connection is not available, request timed out after 30000ms (total=…, active=…, idle=…, waiting=…)" — HikariCP dev 브랜치 `HikariPool.createTimeoutException`, ms 값은 실제 경과 시간).
- 원인: 풀 acquire 상한은 별도 설정이고 HikariCP 기본은 30초다.
- 대처: acquire 상한을 남은 예산 이하로 자른다. 풀이 마르는 원인(느린 쿼리·누수)을 먼저 찾는다([network/35](../../network/35-http-connection-management/2-summary.md) 장애 2, [database/22](../../database/22-database-side-timeouts/2-summary.md) 장애 1).

### 4. 배포 직후에만 타임아웃 — 새 연결(TLS)이 짧은 타임아웃을 넘는다

- 현상: 평소엔 0인 타임아웃이 배포·스케일아웃 직후 몇 분만 생긴다.
- 보이는 형태: 새 인스턴스 쪽에 몰린다. `curl -w`로 보면 `time_appconnect - time_connect`(TLS 구간, 값은 시작부터의 누적이라 차이로 본다)가 평소 요청 시간보다 크다.
- 원인: 타임아웃이 연결 수립까지 포함하는데 값이 재사용 연결 기준으로 잡혀 있다(AWS 사례).
- 대처: 시작 단계에서 연결을 미리 맺는다(워밍업). 연결 수립 구간과 요청 구간 타임아웃을 나눈다.

### 5. 커넥션 idle 수명 불일치 — 다음 요청이 끊긴 연결을 쓴다

- 현상: 한동안 조용하다가 첫 요청이 `Connection reset`·`socket hang up`·502로 실패한다.
- 원인: 클라이언트 풀의 idle 수명이 중간 장비·서버의 idle timeout보다 길다. 호출 밖 타임아웃의 정렬 문제다.
- 대처: 클라이언트 idle < 서버·장비 idle. 자세한 정렬은 [network/35-http-connection-management](../../network/35-http-connection-management/2-summary.md) §5·§6.

## 핵심 문장

- "타임아웃"은 구간 이름과 함께 말해야 한다. 풀 대기·DNS·connect·TLS·쓰기·첫 바이트·읽기 idle·전체는 서로 다른 상한이다.
- connect 타임아웃이 없으면 SYN이 버려질 때 커널 재전송 한도까지 멈춘다. 실험에서 재전송 2·3·5회 설정이 7.2·19.7·68.2초였고, 기본 6회면 약 131초다.
- 읽기 타임아웃은 대개 바이트 사이 간격이라 천천히 흐르는 응답을 끊지 못한다. JDK `HttpClient` 요청 timeout도 실험에서 응답 헤더까지만 덮었다.
- 전체 상한은 기본이 꺼져 있는 경우가 많다(JDK 요청 timeout, Go `DefaultClient`, OkHttp `callTimeout`). 직접 건다.
- 풀 획득 대기는 HTTP·쿼리 타임아웃 밖에 있다. 실제 지연은 대기 + 호출이다.

## 관련 주제·근거

- 선행
  - [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md)
  - [network/15-tcp-handshake-and-backlog](../../network/15-tcp-handshake-and-backlog/2-summary.md) — connect가 끝나는 세 가지 방법, SYN 재전송 시간
  - [network/29-tls-handshake](../../network/29-tls-handshake/2-summary.md) — ④ 구간의 왕복 수
  - [network/35-http-connection-management](../../network/35-http-connection-management/2-summary.md) — 풀·idle timeout 정렬
  - [network/21-tcp-keepalive-and-user-timeout](../../network/21-tcp-keepalive-and-user-timeout/2-summary.md) — 보내는 중 멈춘 연결
- 후속·연결
  - [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md) — 구간 값을 예산에서 나누기
  - [database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md) — DB 쪽 층별 타임아웃 지도
  - [35-timeout-design-worksheet](../35-timeout-design-worksheet/2-summary.md) — Envoy 설정으로 옮기기
- 문서·소스
  - Envoy FAQ "How do I configure timeouts?" — connect_timeout 기본 5 s·상류 TLS 포함, route timeout 기본 15 s·요청을 다 받은 뒤 시작, stream_idle_timeout 5 min, HTTP idle_timeout 1 h, max_connection_duration 0 <https://www.envoyproxy.io/docs/envoy/latest/faq/configuration/timeouts>
  - JDK 21 API `java.net.http.HttpClient.Builder.connectTimeout`(재사용 연결엔 효과 없음), `HttpClient.connectTimeout()`(미설정 시 빈 Optional), `HttpRequest.Builder.timeout`(미설정 = 무한)
  - OkHttp 4.12.0 `okhttp/src/main/kotlin/okhttp3/OkHttpClient.kt` — call 0, connect·read·write 10_000ms, callTimeout이 덮는 범위
  - Go 1.23 `net/http` 문서(`Client.Timeout`, `Transport.ResponseHeaderTimeout`·`TLSHandshakeTimeout`, `DefaultTransport`)
  - Cloudflare 블로그 "The complete guide to Go net/http timeouts" — 타임아웃은 Deadline으로 구현되어 데이터 송수신마다 리셋되지 않는다, `Client.Timeout`은 리다이렉트까지 포함 <https://blog.cloudflare.com/the-complete-guide-to-golang-net-http-timeouts/>
  - undici `docs/api/Client.md` — bodyTimeout·headersTimeout 300e3, connectTimeout 10e3, keepAliveTimeout 4e3
  - HikariCP README — connectionTimeout 30000, idleTimeout 600000, maxLifetime 1800000
  - AWS Builders' Library, Marc Brooker, "Timeouts, retries, and backoff with jitter" — SO_RCVTIMEO의 한계, DNS·TLS를 덮지 않는 구현, 20ms 타임아웃과 새 TLS 연결 사례 <https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/> (원 주소가 JS 렌더링 페이지로 바뀌어 web.archive.org 2024 사본으로 열람)
  - 리눅스 `net/ipv4/tcp_timer.c`(master) — SYN-SENT 최대 재전송 = syn_retries + syn_linear_timeouts, 선형 구간에서 RTO 미증가
- 실험 목록
  - A `ConnHang.java` — accept 큐를 채운 리스너에 connect(타임아웃 1s / 없음), `tcp_syn_retries` 2·3·5, tcpdump로 재전송 간격 확인. JDK 21.0.12 컨테이너 `--cpus=2`, 커널 7.0.0
  - B `Drip.java` — slow drip·slow header 서버에 SO_TIMEOUT만 / JDK HttpClient timeout / 직접 전체 데드라인. `drip.mjs` — Node 18.19.1 `fetch` + `AbortSignal.timeout`
