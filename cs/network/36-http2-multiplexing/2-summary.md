# network/36-http2-multiplexing — HTTP/2 다중화: 스트림·프레임·HPACK·흐름 제어, 그리고 TCP HoL — 정리 (힌트)

## 해결하는 문제

HTTP/1.1 연결 하나는 한 번에 요청 하나만 나른다(35번).\
앞 응답이 느리면 뒤 요청이 줄 서서 기다린다.\
그래서 브라우저는 호스트당 연결을 여러 개(보통 6개) 연다. 연결마다 핸드셰이크와 slow start 비용이 든다.\
게다가 요청마다 거의 같은 헤더(쿠키·User-Agent)를 텍스트로 반복해 보낸다.

쉬운 예: 트럭 한 대가 한 번에 한 집 물건만 싣는다면, 여러 집 배송에는 트럭 여러 대가 필요하다.\
대신 한 트럭에 여러 집 상자를 섞어 싣고 상자마다 "몇 번 주문" 라벨을 붙이면 트럭 한 대로 된다.\
받는 쪽은 라벨을 보고 주문별로 다시 모은다.

똑같은 구조다.\
트럭 = TCP 연결 하나, 상자 = 프레임, 주문 번호 라벨 = 스트림 ID.\
HTTP/2는 요청·응답을 프레임으로 잘라 한 연결 위에 섞어 보낸다(다중화).

실무 예:
- 페이지 하나가 자원 수십 개를 받을 때 연결 하나로 동시에 받는다.
- gRPC는 HTTP/2 위에서 동작한다. 연결 하나에 호출 수백 개가 동시에 흐른다.
- 대신 TCP 세그먼트 하나를 잃으면, 그 뒤에 도착한 데이터를 기다리는 **모든** 스트림이 함께 멈춘다. HTTP/3가 나온 이유다(37번).

## 동작·원리

### 1. 계층 — 의미는 같고 선 위의 모양만 바뀐다

```text
  +-------------------------------------------------+
  | HTTP 의미론 (메서드, 상태 코드, 헤더)   RFC 9110    |
  +-------------------------------------------------+
  | HTTP/2 프레이밍: 스트림 · 프레임 · HPACK  RFC 9113  |
  +-------------------------------------------------+
  | TLS (ALPN = "h2")                                |
  +-------------------------------------------------+
  | TCP  (바이트 스트림 하나, 순서 보장)                 |
  +-------------------------------------------------+
```

- 메서드·경로·상태는 `:method`, `:path`, `:status` 같은 가상 헤더로 실린다(RFC 9113 §8.3).
- 필드 이름은 소문자여야 한다(§8.2.1).
- 연결 단위 헤더(`Connection`, `Keep-Alive`, `Transfer-Encoding` 등)는 HTTP/2에서 쓰면 안 된다(§8.2.2). 연결 관리는 프레임이 대신한다.

### 2. 연결 시작

```text
  Client                                           Server
  TLS ClientHello (ALPN: h2, http/1.1)  -------->
                                        <--------  TLS ... (ALPN 선택: h2)
  "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"  (24바이트 preface)
  SETTINGS                              -------->
                                        <--------  SETTINGS
  SETTINGS(ACK)                         <------->  SETTINGS(ACK)
  HEADERS (stream 1: GET /)             -------->   (preface 직후 바로 보내도 됨)
```

- `https`에서는 TLS의 ALPN으로 `h2`를 고른다(§3.2). 추가 왕복이 없다(29번).
- 양쪽이 연결 preface를 보낸다. 클라이언트는 고정 24바이트 문자열 + SETTINGS, 서버는 SETTINGS다(§3.4).
- 평문(`http`)에서 `Upgrade: h2c`로 올라가는 방식은 거의 쓰이지 않아 RFC 9113에서 폐기됐다(§3.1). 평문 HTTP/2는 "사전 지식(prior knowledge)"으로만 시작한다(§3.3).

### 3. 프레임 — 모든 것의 단위

```text
   0                   1                   2                   3
  +-----------------------------------------------+
  |                 Length (24)                   |   payload 길이 (기본 최대 16,384)
  +---------------+---------------+---------------+
  |   Type (8)    |   Flags (8)   |
  +-+-------------+---------------+-------------------------------+
  |R|                 Stream Identifier (31)                      |   0이면 연결 전체용
  +=+=============================================================+
  |                   Frame Payload ...                           |
  +---------------------------------------------------------------+
            고정 9바이트 헤더 (RFC 9113 §4.1)
```

```text
  타입            코드   쓰임
  DATA           0x0   본문 조각 (흐름 제어 대상은 이것뿐)
  HEADERS        0x1   헤더 블록 (HPACK 압축) — 스트림을 연다
  PRIORITY       0x2   RFC 7540 우선순위 (신호 체계는 폐기)
  RST_STREAM     0x3   스트림 하나만 즉시 중단
  SETTINGS       0x4   연결 설정 교환
  PUSH_PROMISE   0x5   서버 푸시 예고
  PING           0x6   왕복 측정·연결 생존 확인
  GOAWAY         0x7   "새 스트림 그만" — 연결 종료 예고
  WINDOW_UPDATE  0x8   흐름 제어 창 늘리기
  CONTINUATION   0x9   큰 헤더 블록의 이어짐
```

- 페이로드가 16,384바이트(2^14)보다 크면 상대가 `SETTINGS_MAX_FRAME_SIZE`로 허락했을 때만 보낸다(§4.1, §6.5.2).

### 4. 다중화 — 한 연결에 스트림을 섞는다

```text
  TCP 연결 하나 위의 프레임 순서 (시간 →)

  [H s1][H s3][D s1][D s3][H s5][D s1][D s5][D s3 END][D s1 END][D s5 END]

   s1 = GET /index.html     s3 = GET /app.js     s5 = GET /logo.png
   H = HEADERS, D = DATA, END = END_STREAM 플래그
```

- *스트림(stream)*: 요청 하나와 그 응답이 오가는 논리 통로다. 한 연결 안에 여러 개가 동시에 열린다.
- 스트림 ID 규칙(§5.1.1)
  - 클라이언트가 연 스트림은 홀수, 서버가 연 스트림(푸시)은 짝수다.
  - 새 스트림 ID는 이전보다 커야 하고, 재사용할 수 없다.
  - 31비트를 다 쓰면 새 연결을 연다. 서버는 GOAWAY로 새 연결을 유도할 수 있다.
- 스트림 상태를 줄이면 이렇다(§5.1).

```text
  idle --HEADERS--> open --END_STREAM(한쪽)--> half-closed --END_STREAM(다른 쪽)--> closed
                     |                                                             ^
                     +------------------------ RST_STREAM ----------------------------+
```

- `RST_STREAM`은 **스트림 하나만** 끊는다. HTTP/1.1에서 요청 하나를 취소하려면 연결을 끊어야 했던 것과 다르다.

### 5. 동시 스트림 한도

- 각 끝점은 `SETTINGS_MAX_CONCURRENT_STREAMS`로 "상대가 동시에 열 수 있는 스트림 수"를 제한한다(§5.1.2, §6.5.2).
  - 초기값은 무제한이다. RFC는 100 이상을 권한다.
  - nginx `http2_max_concurrent_streams`의 기본값은 128이다.
- open·half-closed 스트림이 한도에 들어간다.
- 한도를 넘는 HEADERS를 받으면 스트림 오류(`PROTOCOL_ERROR` 또는 `REFUSED_STREAM`)로 거절한다(MUST).
- 그래서 클라이언트는 한도에 걸리면 **자기 쪽에서 요청을 줄 세운다.** 이 대기가 지연으로 보인다.

### 6. 흐름 제어 — 스트림별·연결별 신용

```text
  수신자 창(window) = "지금 더 받을 수 있는 바이트"

  초기: 스트림 창 65,535 / 연결 창 65,535  (§6.9.2)

  송신 DATA 16KB  ->  스트림 창 -16KB, 연결 창 -16KB
  수신 측이 읽고 나서 WINDOW_UPDATE(+16KB) 전송  ->  창 복구
  창이 0이면 그 스트림(또는 연결 전체)의 DATA 전송 중단
```

- 흐름 제어는 **DATA 프레임에만** 적용된다. 제어 프레임은 막히지 않는다(§5.2.1).
- 한 구간(hop) 단위다. 프록시가 끼면 양쪽 구간이 따로 흐름 제어한다.
- 창이 BDP(대역폭 × 왕복 시간)보다 작으면 처리량이 창 크기에 묶인다(§5.2.3). 03번 BDP와 같은 원리다.
  - 예: 창 65,535바이트, RTT 100ms면 최대 약 65,535 × 8 / 0.1 ≈ 5.2Mbps다(예시 계산).
- 받는 쪽은 TCP 버퍼에서 프레임을 제때 읽어야 한다. 안 읽으면 WINDOW_UPDATE도 못 읽어 교착이 생길 수 있다(MUST, §5.2.2).
- *BDP(bandwidth-delay product)*: 경로를 가득 채우는 데 필요한 "날아가는 중인" 데이터 양이다.

### 7. HPACK — 헤더 압축

```text
  인덱스 공간 (RFC 7541 §2.3.3)

  [ 1 .. 61 ] 정적 테이블       [ 62 .. ] 동적 테이블 (연결마다, FIFO)
   1  :authority                 62  user-agent: Mozilla/5.0 ...   <- 가장 최근
   2  :method GET                63  cookie: sid=abc...
   3  :method POST               ...
   8  :status 200                     <- 크기 초과 시 오래된 것부터 축출
  ...
  61  www-authenticate

  첫 요청:  cookie: sid=abc  -> 리터럴로 보내고 동적 테이블에 추가
  다음 요청: cookie: sid=abc  -> "63번" 인덱스 하나로 보냄
```

- 정적 테이블은 자주 쓰는 헤더 61개로 고정이다(RFC 7541 Appendix A).
- 동적 테이블은 연결마다 따로 두고 FIFO로 관리한다. 새 항목이 가장 낮은 번호를 받는다(§2.3.2).
  - 항목 크기 = 이름 길이 + 값 길이 + 32바이트다(§4.1).
  - 최대 크기의 초기값은 `SETTINGS_HEADER_TABLE_SIZE` 4,096바이트다(RFC 9113 §6.5.2).
- 문자열은 고정 허프만 코드로 줄일 수 있다(RFC 7541 §5.2, Appendix B).
- 왜 gzip이 아닌가: 압축 결과 길이로 비밀(쿠키)을 추측하는 CRIME 공격 때문이다. HPACK은 헤더 필드 전체가 일치해야 이득이 나게 설계했다(RFC 7541 §1, §7.1).
  - 민감한 값은 "never indexed" 리터럴로 보내 동적 테이블에 넣지 않게 할 수 있다(§6.2.3, §7.1.3).
- 부작용: 동적 테이블은 **프레임을 받은 순서대로** 갱신돼야 한다. 그래서 HEADERS 처리 순서가 연결 전체에 묶인다. HTTP/3는 이 문제로 QPACK을 새로 만들었다(37번).

### 8. TCP 수준 head-of-line blocking

```text
  송신: [s1 D][s3 D][s5 D][s1 D]  ->  TCP 세그먼트 #10 #11 #12 #13
  네트워크: #11 (s3 데이터) 손실

  수신 커널 TCP 버퍼:
    #10 도착 -> 앱에 전달
    #11 없음  -> #12, #13은 도착했지만 **순서가 비어 앱에 못 넘김**
                 (s5, s1 프레임도 같이 대기)
    ... 재전송된 #11 도착 (최소 1 RTT 뒤) -> 그제서야 #11 #12 #13 한꺼번에 전달
```

- HTTP/2는 HTTP 층의 HoL(응답 순서 대기)은 없앴다.
- 하지만 모든 스트림이 **TCP 바이트 스트림 하나**를 공유한다. TCP는 순서를 지켜야 앱에 넘기므로, 한 세그먼트 손실이 무관한 스트림까지 멈춘다.
- HPBN "HTTP/2" 장은 두 가지를 짚는다. TCP 수준 HoL이 남는다. 손실 시 혼잡 윈도가 줄어 **연결 전체**의 처리량이 떨어진다.
- 그래서 손실이 잦은 망(모바일 등)에서는 연결 6개로 나눈 HTTP/1.1보다 연결 1개인 HTTP/2가 더 나쁠 수 있다. 연결이 여럿이면 손실이 그중 하나에만 영향을 주기 때문이다.
- TCP 재전송·손실 복구는 16번에서 다룬다.

### 9. GOAWAY — 연결을 깔끔하게 끝내는 법

```text
  Server                                             Client
  GOAWAY(last=2^31-1, NO_ERROR)  -------->   "곧 닫는다. 새 스트림 그만"
        ... 최소 1 RTT 기다림 (이미 날아오는 요청 처리) ...
  GOAWAY(last=7, NO_ERROR)       -------->   "7번까지만 처리한다"
                                             stream 9, 11 은 처리 안 됨
                                             -> 새 연결에서 재시도해도 안전
        ... 1~7번 스트림 완료 후 연결 종료 ...
```

- GOAWAY에는 "처리했거나 처리할 수도 있는 마지막 스트림 ID"가 들어 있다(§6.8).
  - 그보다 큰 ID의 스트림은 처리되지 않았다. **비멱등 요청도** 새 연결에서 재시도해도 된다(§8.7).
  - 그 이하인데 완료되지 않은 스트림은 멱등 요청만 재시도할 수 있다(§6.8).
- 받은 쪽은 그 연결에 새 스트림을 열면 안 된다(MUST NOT).
- 끝점(서버 포함)은 연결을 닫기 전에 항상 GOAWAY를 보내는 것이 권고다(SHOULD, §6.8). 보내지 않으면 클라이언트는 어떤 요청이 처리됐는지 모른다.
- `RST_STREAM(REFUSED_STREAM)`도 "처리 전에 거절했다"는 보증이라 재시도해도 안전하다(§8.7).
- AWS ALB는 HTTP/2 연결 하나에서 요청이 10,000개를 넘으면 GOAWAY를 보내고 연결을 닫는다(ALB 문제 해결 문서).

### 10. 우선순위

- RFC 7540의 우선순위 트리(의존 관계 + 가중치)는 복잡하고 구현이 들쭉날쭉해 RFC 9113에서 신호 체계가 폐기됐다(§5.3.1~§5.3.2).
- 대안은 RFC 9218 "Extensible Prioritization"이다. `Priority` 헤더의 `u`(긴급도 0~7, 기본 3)와 `i`(점진 처리 여부)로 신호한다.

## 쓰이는 자료구조·알고리즘

- **HPACK 정적 테이블(배열) + 동적 테이블(크기 제한 FIFO 링 버퍼)** — 인덱스로 헤더를 참조하고, 크기를 넘으면 오래된 항목부터 버린다(RFC 7541 §2.3, §4.4). [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **허프만 코딩(고정 코드표)** — 자주 나오는 문자에 짧은 비트열을 준다(RFC 7541 Appendix B).
- **우선순위 트리(RFC 7540, 폐기)** — 스트림 의존 관계를 트리로 두고 가중치로 대역폭을 나눴다. 지금은 RFC 9218의 긴급도 등급(0~7)으로 바뀌었다. RFC 9218 §10은 높은 긴급도부터 보내고, 같은 긴급도 안에서는 비점진 응답은 스트림 ID 오름차순, 점진(`i`) 응답은 대역폭을 나눠 보내라고 권한다. 그래서 서버는 긴급도별 큐를 두는 모양이 된다.
- **신용 기반 흐름 제어 카운터** — 스트림별·연결별 창 크기를 정수로 들고, DATA 전송 시 빼고 WINDOW_UPDATE 수신 시 더한다(RFC 9113 §6.9).
- **스트림 상태 기계** — idle / open / half-closed / closed 전이를 프레임과 플래그가 일으킨다(§5.1).
- **스트림 ID 단조 증가 카운터** — 재사용하지 않으므로 소진되면 새 연결이 필요하다.

## 적용 — 풀어나가는 법

### 1. HTTP/2가 실제로 쓰이는지 확인한다

```bash
# ALPN 결과와 HTTP 버전
curl -sv --http2 -o /dev/null https://api.example.com/ 2>&1 | grep -iE 'ALPN|HTTP/2'
curl -s -o /dev/null -w '%{http_version}\n' https://api.example.com/

# 프레임 단위로 보기 (nghttp2 도구)
nghttp -nv https://api.example.com/

# 부하 시험: 연결 수(-c)와 연결당 동시 스트림(-m)을 바꿔 가며
h2load -n 10000 -c 4 -m 100 https://api.example.com/

# 서버가 광고하는 SETTINGS(MAX_CONCURRENT_STREAMS 등) — nghttp -v 출력의 SETTINGS 프레임
```

- 암호화된 프레임을 Wireshark로 보려면 클라이언트에서 TLS 키를 파일로 떨군다(`SSLKEYLOGFILE` 환경 변수를 지원하는 curl·브라우저).

### 2. 코드에서

Java — JDK HttpClient는 HTTP/2를 먼저 시도하고, 안 되면 HTTP/1.1로 내려간다.

```java
HttpClient client = HttpClient.newBuilder()
    .version(HttpClient.Version.HTTP_2)
    .build();
HttpResponse<String> res = client.send(
    HttpRequest.newBuilder(URI.create("https://api.example.com/")).build(),
    HttpResponse.BodyHandlers.ofString());
System.out.println(res.version());   // HTTP_2 또는 HTTP_1_1
```

Node — `http2` 모듈. 세션(연결) 하나에 여러 스트림을 연다.

```js
const http2 = require('node:http2');
const session = http2.connect('https://api.example.com');
session.on('goaway', (code, lastStreamID) => {
  // lastStreamID보다 큰 스트림의 요청은 처리되지 않았다 -> 새 세션에서 재시도
  console.warn('GOAWAY', code, lastStreamID);
});
for (const p of ['/a', '/b', '/c']) {
  const req = session.request({ ':path': p });   // 같은 TCP 연결 위의 서로 다른 스트림
  req.on('response', (h) => console.log(p, h[':status']));
  req.end();
}
```

### 3. 서버·프록시 설정에서 볼 것

1. HTTP/2 활성화: nginx는 `http2 on;`(1.25.1부터 이 지시어, 기본 off).
2. 동시 스트림 한도: nginx `http2_max_concurrent_streams`(기본 128). gRPC 서버도 비슷한 설정이 있다.
3. 흐름 제어 창: 대용량 전송이 느리면 초기 창·연결 창을 늘린다.
4. 연결 수명: 긴 연결은 새 서버로 부하가 안 퍼진다(35번). 최대 요청 수·수명을 두고 GOAWAY로 넘긴다.
5. L4 로드밸런서 뒤 gRPC: 연결 하나에 호출이 몰려 특정 서버만 뜨거워진다. L7 분산이나 클라이언트 측 분산을 쓴다(api-design/15 gRPC에서 다룸).

## 장애 시나리오와 대처

### 1. 패킷 손실 한 번에 모든 요청이 멈춘다 — TCP HoL

- **현상**: 모바일·해외 사용자에게서 페이지 로딩이 들쭉날쭉하다. HTTP/2로 바꾼 뒤 p99 지연이 오히려 나빠졌다.
- **보이는 형태**
  - 브라우저 타임라인에서 서로 무관한 자원들이 **같은 순간** 멈췄다가 한꺼번에 도착한다.
  - `ss -ti`에서 해당 연결의 `retrans`가 늘어 있다. `tcpdump`에 재전송 세그먼트가 보인다.
- **원인**: 모든 스트림이 TCP 연결 하나를 공유한다. 세그먼트 하나가 빠지면 커널이 뒤 세그먼트를 앱에 넘기지 못한다. 재전송이 올 때까지, 뒤 세그먼트에 데이터가 실린 스트림은 모두 기다린다.
- **대처**
  - HTTP/3(QUIC)를 함께 제공한다. 스트림별로 순서를 지켜 손실이 해당 스트림에만 영향을 준다(37번).
  - 손실 복구가 빠른 혼잡 제어·TCP 설정을 검토한다(16·18번).
  - 큰 다운로드와 지연에 민감한 API를 다른 연결로 나누는 것도 방법이다.

### 2. GOAWAY를 제대로 처리하지 않아 배포·연결 교체 때 요청이 실패한다

- **현상**: 서버 배포나 LB 연결 교체 순간마다 소수 요청이 실패한다. 재시도해도 실패하는 경우가 섞인다.
- **보이는 형태**
  - gRPC: `UNAVAILABLE` 상태. 클라이언트 로그에 GOAWAY 수신 메시지가 있다.
  - 클라이언트가 GOAWAY 뒤에도 같은 연결에 새 스트림을 연다. 서버가 무시하거나 오류로 답한다.
  - 서버가 GOAWAY 없이 연결을 끊어, 클라이언트가 어떤 요청이 처리됐는지 모른다.
- **원인**
  - 서버: 종료 시 GOAWAY를 보내지 않거나, 1회로 곧바로 마지막 ID를 확정해 이미 날아오던 요청을 버렸다.
  - 클라이언트: GOAWAY의 last-stream-id를 보지 않고 모든 진행 중 요청을 실패 처리했다. 또는 재시도 대상이 아닌 요청(ID ≤ last, 비멱등)까지 재시도했다.
  - AWS ALB처럼 연결당 요청 수 상한(10,000)으로 주기적으로 GOAWAY를 보내는 중간자도 있다.
- **대처**
  - 서버: 2단계 GOAWAY(먼저 2^31−1, 1 RTT 이상 뒤 실제 last ID)를 보내고 진행 중 스트림을 마친 뒤 닫는다(RFC 9113 §6.8). [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md)
  - 클라이언트: last-stream-id보다 큰 스트림은 새 연결에서 재시도한다(비멱등도 안전, §8.7). 그 이하 미완료 스트림은 멱등 요청만 재시도한다.
  - GOAWAY를 받은 연결에는 새 스트림을 열지 않는다. 대부분의 라이브러리가 하지만, 커스텀 풀·프록시는 확인한다.

### 3. 동시 스트림 한도에 걸려 요청이 줄 선다

- **현상**: 서버 CPU는 한가한데 클라이언트 지연이 늘어난다. 동시 호출이 많은 배치·팬아웃 서비스에서 심하다.
- **보이는 형태**
  - 클라이언트 쪽에 "대기 중" 요청이 쌓인다. 요청 시작 시각과 실제 전송 시각 사이에 간격이 있다.
  - 한도를 무시한 구현은 `RST_STREAM(REFUSED_STREAM)`을 받는다.
  - `nghttp -v`로 서버 SETTINGS의 `SETTINGS_MAX_CONCURRENT_STREAMS` 값이 작다(예: 100·128).
- **원인**: 연결 하나에 동시에 열 수 있는 스트림이 상대 설정으로 제한된다(RFC 9113 §5.1.2). 클라이언트가 연결을 하나만 쓴다.
- **대처**
  - 클라이언트가 HTTP/2 연결을 여러 개 두고 나눠 쓴다(연결 풀).
  - 서버 한도를 올리되, 스트림당 메모리와 처리 동시성도 같이 본다.
  - 하류 한도를 초과하는 팬아웃은 호출 측에서 동시성을 제한한다([ops-patterns/03-bulkhead](../../ops-patterns/03-bulkhead/2-summary.md)).

### 4. 흐름 제어 창이 작아 대용량 전송이 느리다

- **현상**: 대역폭이 넉넉한 원거리 구간에서 HTTP/2 다운로드가 HTTP/1.1보다 느리다.
- **보이는 형태**: 처리량이 대략 "창 크기 ÷ RTT"에서 평평하다. 프레임 로그에 WINDOW_UPDATE를 기다리는 공백이 반복된다.
- **원인**: 스트림·연결 창이 BDP보다 작다. 초기값 65,535바이트 그대로면 원거리에서 금방 창이 바닥난다(RFC 9113 §5.2.3).
- **대처**: 받는 쪽이 초기 창(`SETTINGS_INITIAL_WINDOW_SIZE`)과 연결 창(WINDOW_UPDATE로)을 BDP 이상으로 늘린다. 메모리 한도와 균형을 맞춘다.

### 5. 스트림 취소를 악용한 서비스 거부 — Rapid Reset

- **현상**: 요청 수는 평소와 비슷한데 서버 CPU·메모리가 치솟는다.
- **보이는 형태**: 연결 하나에서 HEADERS 직후 RST_STREAM이 초고속으로 반복된다. 동시 스트림 수는 낮게 유지되는데 처리 작업은 계속 생긴다.
- **원인**: 스트림을 열자마자 취소하면 동시 스트림 한도에 걸리지 않는다. 서버는 취소된 요청의 작업을 이미 시작했다. CVE-2023-44487(2023년 8~10월 실제 공격)이 이 방식이다.
- **대처**: 서버·프록시를 패치한다. 연결당 취소 비율·속도에 상한을 두고 넘으면 GOAWAY로 연결을 닫는다.

## 핵심 문장

- HTTP/2는 요청·응답을 9바이트 헤더의 프레임으로 잘라 스트림 ID를 붙이고, 한 TCP 연결 위에 섞어 보낸다.
- HTTP 층의 head-of-line blocking은 없앴지만, 모든 스트림이 TCP 바이트 스트림 하나를 공유하므로 세그먼트 하나의 손실이 그 뒤 데이터를 기다리는 모든 스트림을 멈춘다.
- 동시 스트림 수는 상대의 `SETTINGS_MAX_CONCURRENT_STREAMS`로, 전송량은 스트림별·연결별 흐름 제어 창(초기 65,535)으로 제한된다.
- HPACK은 정적 테이블 61개 + 연결별 FIFO 동적 테이블로 반복 헤더를 인덱스 하나로 줄이고, CRIME 같은 길이 사이드채널을 피하도록 설계됐다.
- GOAWAY의 last-stream-id보다 큰 스트림은 처리되지 않았으므로 비멱등 요청도 새 연결에서 재시도해도 안전하다.

## 관련 주제·근거

- 선행
  - `35-http-connection-management` — [35번](../35-http-connection-management/2-summary.md)
  - `29-tls-handshake` — ALPN `h2`. [29번](../29-tls-handshake/2-summary.md)
  - `33-http-semantics` — [33번](../33-http-semantics/2-summary.md)
- 후속
  - `37-http3-quic` — 스트림 독립으로 TCP HoL 해소. [37번](../37-http3-quic/2-summary.md)
  - [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) · [18-tcp-congestion-control](../18-tcp-congestion-control/2-summary.md) · [03-latency-bandwidth-bdp](../03-latency-bandwidth-bdp/2-summary.md)
  - [40-chunked-and-streaming-responses](../40-chunked-and-streaming-responses/2-summary.md) — HTTP/2 DATA 프레임 스트리밍
  - `api-design/15-rpc-and-grpc` — 미작성([api-design 커리큘럼](../../api-design/curriculum.md))
- RFC 9113 HTTP/2 <https://www.rfc-editor.org/rfc/rfc9113>
  - §3.1 `h2`·`h2c` 폐기 · §3.2~§3.4 시작과 preface · §4.1 프레임 형식 · §5.1 스트림 상태 · §5.1.1 스트림 ID · §5.1.2 동시성
  - §5.2 흐름 제어(원칙·교착·성능) · §5.3 우선순위(7540 체계 폐기) · §6.5.2 SETTINGS 초기값 · §6.8 GOAWAY · §6.9 WINDOW_UPDATE
  - §8.2.1~§8.2.2 필드 규칙·연결 단위 헤더 금지 · §8.3 가상 헤더 · §8.7 요청 신뢰성(REFUSED_STREAM, GOAWAY)
- RFC 7541 HPACK <https://www.rfc-editor.org/rfc/rfc7541>
  - §2.3 인덱스 테이블 · §4.1 항목 크기 · §4.4 축출 · §5.2 허프만 · §6.2.3 never indexed · §7.1 CRIME류 공격 · Appendix A 정적 테이블
- RFC 9218 Extensible Prioritization Scheme for HTTP §4 <https://www.rfc-editor.org/rfc/rfc9218>
- CVE-2023-44487 (HTTP/2 Rapid Reset) <https://www.cve.org/CVERecord?id=CVE-2023-44487>
- Grigorik, 『High Performance Browser Networking』 "HTTP/2" 장 <https://hpbn.co/http2/>
- nginx `ngx_http_v2_module`(`http2`, `http2_max_concurrent_streams`) <https://nginx.org/en/docs/http/ngx_http_v2_module.html>
- AWS ALB 문제 해결(HTTP/2 연결당 10,000요청 뒤 GOAWAY) <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html>
- Node.js `http2` 문서 <https://nodejs.org/api/http2.html>
- nghttp2 도구(`nghttp`, `h2load`) <https://nghttp2.org/documentation/>
