# network/40-chunked-and-streaming-responses — 끝을 모르는 응답: chunked·HTTP/2 DATA·스트리밍·백프레셔 — 정리 (힌트)

## 해결하는 문제

TCP는 바이트 스트림이다.\
"응답 본문이 어디서 끝나는지"를 TCP는 알려 주지 않는다(24번 프레이밍).\
HTTP/1.1이 한 연결로 요청을 여러 번 주고받으려면 본문의 끝을 따로 표시해야 한다.

가장 쉬운 방법은 `Content-Length: 1234`처럼 **미리 길이를 적는** 것이다.\
그런데 길이를 미리 모르는 응답이 많다.

- DB 커서로 100만 행을 CSV로 내보낸다.
- LLM이 토큰을 하나씩 만든다.
- 압축 결과 크기는 압축을 끝내야 안다.

길이를 알려고 전부 메모리에 모으면 두 가지를 잃는다.\
**첫 바이트가 늦어지고**, 응답 크기만큼 **메모리를 먹는다**.

쉬운 예: 이삿짐을 트럭으로 보낸다.\
짐이 몇 상자인지 몰라도 된다.\
상자마다 "이 상자는 30kg"이라고 붙여 보내다가, 마지막에 "빈 상자 = 끝"을 보낸다.

똑같은 구조다.\
chunked는 조각마다 길이를 붙이고, 길이 0인 조각으로 끝을 알린다.

실무 예:
- 대용량 CSV·엑셀 내보내기, 로그 tail, SSE, LLM 스트리밍 응답
- 서버가 만들어 내는 속도보다 클라이언트가 읽는 속도가 느리면, 그 차이를 누가 어디에 쌓아 두는지가 곧 장애 지점이다(백프레셔).

## 동작·원리

### 1. HTTP/1.1이 본문 끝을 정하는 세 가지 방법 (RFC 9112 §6.3)

```text
  우선순위  헤더                          끝을 아는 방법
  1        Transfer-Encoding: chunked    길이 0인 마지막 청크까지 읽음
  2        Content-Length: N             N바이트 읽음
  3        (응답에서) 둘 다 없음            서버가 연결을 닫을 때까지 읽음 -> 연결 재사용 불가
```

- `Transfer-Encoding`과 `Content-Length`가 **둘 다** 오면 Transfer-Encoding이 이긴다.
  - RFC 9112 §6.3은 이런 메시지를 요청 스머글링 시도로 의심하고 오류로 다루라고 한다(ought to). 중계자가 전달한다면 Content-Length를 먼저 지워야 한다(MUST).
  - *요청 스머글링*: 앞단 프록시와 뒷단 서버가 본문 끝을 다르게 해석하는 틈을 노려, 한 요청 안에 다른 요청을 숨겨 넣는 공격이다.

### 2. chunked 와이어 형식 (RFC 9112 §7.1)

```text
  HTTP/1.1 200 OK
  Content-Type: text/csv
  Transfer-Encoding: chunked
  Trailer: X-Row-Count                   <- (선택) 뒤에 올 트레일러 이름 예고
                                         <- 빈 줄 = 헤더 끝
  1f\r\n                                 <- 청크 크기(16진수) = 31바이트
  id,name\r\n1,kim\r\n2,lee\r\n3,park\r\n  <- 31바이트 데이터
  \r\n                                   <- 청크 데이터 뒤 CRLF
  10\r\n                                 <- 16바이트
  4,choi\r\n5,jung\r\n
  \r\n
  0\r\n                                  <- last-chunk: 크기 0 = 본문 끝
  X-Row-Count: 5\r\n                     <- 트레일러 필드 (선택)
  \r\n                                   <- 빈 줄 = 메시지 끝
```

- 청크 = `크기(16진) CRLF 데이터 CRLF`다. 크기가 앞에 붙는 **길이 접두 프레이밍**이다.
- 크기 0 청크가 오고, 선택적 트레일러가 오고, 빈 줄로 메시지가 끝난다.
- 수신자는 chunked를 반드시 해독할 수 있어야 한다(MUST). 청크 크기 숫자가 매우 클 수 있으니 정수 넘침에 대비해야 한다(MUST).
- chunked는 **홉마다** 다시 짜인다. 프록시는 청크 경계를 바꿀 수 있다. 그래서 청크 경계에 의미(예: "한 청크 = 한 이벤트")를 두면 안 된다.
  - RFC 9112 §7.1.1도 청크 확장은 중계자가 지우거나 다시 쓸 수 있다고 적는다.

**불완전 메시지** (RFC 9112 §8):

```text
  chunked인데 0 청크를 못 받고 연결이 끊김        -> 불완전
  Content-Length: 100인데 60바이트 뒤 끊김         -> 불완전
  둘 다 없고 연결 종료로 끝남                     -> 완전으로 간주 (TLS의 불완전 종료는 예외)
```

- 클라이언트는 불완전 응답을 **불완전하다고 기록해야** 한다(MUST).
- 이것이 스트리밍 도중 서버가 "실패"를 알리는 거의 유일한 방법이다. 아래 4절.

### 3. HTTP/2 — chunked가 없다, DATA 프레임이 있다 (RFC 9113)

```text
  stream 1:  HEADERS (:status 200, content-type ...)
             DATA   (길이 16384)
             DATA   (길이 16384)
             DATA   (길이 802, END_STREAM)          <- 본문 끝
        또는
             HEADERS (트레일러, END_STREAM)          <- 트레일러로 끝낼 수도 있음

  실패 시:   RST_STREAM (error code INTERNAL_ERROR 0x2)  <- 이 스트림만 즉시 중단
```

- HTTP/2 메시지는 HEADERS 한 개 + DATA 0개 이상 + (선택) 트레일러 HEADERS로 이루어진다(§8.1).
- 마지막 프레임에 `END_STREAM` 플래그가 붙으면 본문 끝이다. 프레임마다 길이 필드가 있으니 별도의 chunked가 필요 없다.
- `Transfer-Encoding` 헤더를 보내면 오히려 **잘못된 메시지**로 취급된다(§8.2.2). 예외로 요청의 `TE: trailers`만 허용된다.
- 도중 실패는 `RST_STREAM`으로 그 스트림만 끊는다. 같은 연결의 다른 스트림은 산다. HTTP/1.1처럼 연결 전체를 버릴 필요가 없다.

**HTTP/2 흐름 제어** (§5.2, §6.9):

```text
  수신자가 "이만큼 받을 수 있다"(창) 신용을 준다
  초기 창 = 65,535 바이트 (스트림별 + 연결 전체)
  송신자: DATA를 보낼 때마다 창에서 차감, 0이 되면 멈춤
  수신자: 애플리케이션이 읽어 가면 WINDOW_UPDATE로 창을 다시 늘려 줌
```

- DATA 프레임만 흐름 제어를 받는다. 제어 프레임은 막히지 않는다.
- 흐름 제어는 **한 홉** 사이에서만 동작한다. 클라이언트↔프록시, 프록시↔서버가 각각 따로다.

### 4. 스트리밍 응답과 "잠긴 상태 코드"

```text
  시간 ---->
  [상태줄 200][헤더] | [청크1][청크2][청크3] ... [0 청크]
                    ^
                    이 순간 헤더가 나감 = 상태 코드 확정
                    이후 에러가 나도 500으로 바꿀 수 없다
```

- 상태 코드는 헤더와 함께 **맨 앞**에 나간다. 스트리밍은 결과를 다 알기 전에 본문을 시작하는 것이다.
- 그래서 도중 에러를 알리는 수단이 제한된다.

```text
  HTTP/1.1  : 0 청크를 보내지 않고 연결을 끊는다     -> 클라이언트가 "불완전"으로 인식
  HTTP/2    : RST_STREAM(INTERNAL_ERROR)            -> 그 스트림만 오류
  트레일러   : 끝에 상태를 싣는다 (gRPC의 grpc-status)  -> 중계자가 버릴 수 있음(RFC 9110 §6.5.1)
  본문 규약  : 마지막 이벤트로 {"done":true} / {"error":...}를 보낸다
```

- **가장 나쁜 선택은 에러를 삼키고 0 청크로 정상 종료하는 것**이다. 클라이언트는 잘린 데이터를 완전한 데이터로 믿는다.
- gRPC는 상태를 트레일러(`grpc-status`)로 보낸다. 성공(OK)이어도 트레일러에 실어야 한다(gRPC PROTOCOL-HTTP2 문서). 예외로, 본문 없이 곧바로 실패하는 호출은 헤더 블록 하나에 상태를 담는 Trailers-Only 응답을 쓸 수 있다.

### 5. 백프레셔 — 느린 소비자는 어디에 쌓이나

```text
  [생산자: DB 커서/LLM] -> [앱 버퍼] -> [소켓 송신 버퍼] -> TCP 창 -> [프록시 버퍼] -> ... -> [클라이언트]
                          ^                ^                         ^
                          여기가 무한이면  커널이 꽉 차면              nginx proxy_buffering on:
                          OOM             write가 막히거나           메모리 버퍼 -> 임시 파일
                                          (논블로킹) 실패            (기본 최대 1024m)
```

- 클라이언트가 느리면 TCP 수신 창이 줄고(17번), 서버 커널의 송신 버퍼가 찬다.
- 그다음 반응은 앱의 I/O 모델에 따라 다르다.
  - **블로킹 I/O(서블릿 `OutputStream`)**: `write()`가 막힌다. 생산도 자연히 멈춘다. 대신 스레드 하나가 그동안 묶인다.
  - **Node.js 스트림**: `write()`가 `false`를 돌려준다. `'drain'` 이벤트까지 쓰기를 멈춰야 한다. 무시하고 계속 쓰면 Node가 청크를 **메모리에 계속 쌓는다**(Node `stream` 문서). 상대가 안 읽으면 영원히 안 비워질 수 있어 원격 공격 경로가 된다고 문서가 경고한다.
  - **리액티브(Reactor 등)**: 소비자가 요청한 개수(demand)만큼만 생산한다.
- 중간 프록시가 응답을 버퍼링하면 앱 쪽 백프레셔가 **끊긴다**. 프록시가 대신 빨리 받아 주기 때문이다. 대신 프록시의 메모리·디스크가 쌓인다.

  - *백프레셔(backpressure)*: 받는 쪽이 느릴 때 "천천히 보내라"는 신호가 보내는 쪽까지 거슬러 올라가는 것이다.

### 6. 프록시 버퍼링과 스트리밍

- nginx `proxy_buffering`의 기본값은 `on`이다(nginx proxy 모듈 문서).
  - 켜져 있으면 상류 응답을 버퍼에 최대한 빨리 받아 두고, 넘치면 임시 파일에 쓴다.
  - 꺼져 있으면 받는 즉시 동기적으로 클라이언트에 넘긴다.
- 응답 헤더 `X-Accel-Buffering: no`로 응답별로 끌 수 있다.
- 요청 방향도 같다. `proxy_request_buffering on`(기본)이면 요청 본문 전체를 받은 뒤 상류로 보낸다. 대용량 업로드 스트리밍에 영향을 준다(42번).

## 쓰이는 자료구조·알고리즘

- **청크 = 길이 접두 프레이밍** — 조각마다 길이를 먼저 적는다. 수신측 파서는 "크기 줄 → 데이터 → CRLF → 반복 → 0 → 트레일러 → 빈 줄" 상태 기계다. 24번 프레이밍의 연결 노트 [systems/resp-protocol](../../systems/resp-protocol/2-summary.md)과 같은 계열이다.
- **유한 버퍼(bounded buffer)** — 생산자와 소비자 사이에 크기 상한이 있는 큐를 둔다. 가득 차면 생산자가 기다린다. 이것이 백프레셔의 자료구조적 실체다. [큐·덱](../../data-structure/04-queue-deque/2-summary.md) · [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md)
- **신용 기반 흐름 제어(credit-based)** — HTTP/2 창은 "보낼 수 있는 바이트 신용"이다. 보내면 차감, WINDOW_UPDATE로 충전한다. TCP 수신 창(17번)과 같은 발상을 스트림 단위로 한 번 더 한 것이다.
- **하이워터마크(high-water mark)** — Node 스트림은 내부 버퍼가 이 값을 넘으면 `write()`가 `false`를 돌려준다. 바이트 스트림 기본값은 Node.js 22부터 64KiB(Windows는 16KiB)이고, 21 이하는 16KiB다(Node 문서 History). 실제 값은 `stream.getDefaultHighWaterMark(false)`로 확인한다.

## 적용 — 풀어나가는 법

### 1. 스트리밍할지 먼저 정한다

```text
  길이를 안다 & 작다         -> Content-Length (버퍼링해도 됨)
  길이를 모른다 / 크다       -> 스트리밍 (HTTP/1.1이면 chunked 자동)
  도중 실패를 알려야 한다     -> 본문 규약(마지막 레코드) + 비정상 종료 둘 다
```

### 2. 코드

Java — Spring MVC `StreamingResponseBody`로 CSV 내보내기:

```java
@GetMapping(value = "/export.csv", produces = "text/csv")
public ResponseEntity<StreamingResponseBody> export() {
    StreamingResponseBody body = out -> {
        try (Stream<Order> rows = repo.streamAll()) {       // DB 커서: 전부 메모리에 올리지 않음
            Writer w = new BufferedWriter(new OutputStreamWriter(out, UTF_8));
            rows.forEach(o -> { try { w.write(o.toCsvLine()); } catch (IOException e) { throw new UncheckedIOException(e); } });
            w.flush();
        }
        // 여기서 예외가 나면 이미 200이 나갔다 -> 컨테이너가 연결을 비정상 종료(0 청크 없음)해야 한다
    };
    return ResponseEntity.ok().header("X-Accel-Buffering", "no").body(body);
}
```

- 블로킹 `OutputStream`이라 클라이언트가 느리면 `write`가 막히고 DB 읽기도 멈춘다. 자연스러운 백프레셔다.

Node.js — `drain`을 지키는 스트리밍과 도중 실패:

```js
const http = require('node:http');

http.createServer(async (req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/x-ndjson' }); // 길이 없음 -> chunked
  try {
    for await (const row of db.cursor()) {
      if (!res.write(JSON.stringify(row) + '\n')) {
        await new Promise((r) => res.once('drain', r));   // 버퍼가 비워질 때까지 생산 중지
      }
    }
    res.end(JSON.stringify({ done: true }) + '\n');       // 본문 규약상 "정상 끝" 표시
  } catch (err) {
    console.error(err);
    res.destroy(err);          // 0 청크 없이 연결 종료 -> 클라이언트가 불완전으로 인식
  }
}).listen(8080);
```

- 가장 간단한 방법은 `stream.pipeline(source, res, cb)`이다. 백프레셔와 오류 시 정리를 대신 해 준다.

브라우저 — 스트림 소비와 완결 확인:

```js
const res = await fetch('/export.ndjson');
const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
let sawDone = false;
for (;;) {
  const { value, done } = await reader.read();   // 서버가 중간에 끊으면 여기서 TypeError
  if (done) break;
  if (value.includes('"done":true')) sawDone = true; // 단순화: 실무는 줄 단위 파싱
}
if (!sawDone) throw new Error('응답이 완결되지 않았다');
```

### 3. 진단 명령

```bash
# 청크를 해독하지 않고 원형 그대로 보기 (크기 줄과 0 청크 확인)
curl -s --raw --http1.1 -i https://api.example.com/export.csv | head -20

# 버퍼링 없이 흐르는지 (도착 시각 확인)
curl -sN https://api.example.com/stream | while read l; do echo "$(date +%T.%N) $l"; done

# 잘린 응답: curl 종료 코드 18
curl -sS -o /dev/null https://api.example.com/export.csv; echo "exit=$?"
#   curl: (18) transfer closed with outstanding read data remaining    (chunked가 0 청크 없이 끊김)
#   curl: (18) transfer closed with 95 bytes remaining to read         (Content-Length보다 짧음)

# HTTP/2 스트림 리셋: curl 종료 코드 92 (CURLE_HTTP2_STREAM)
curl -sS --http2 -o /dev/null https://api.example.com/export.csv; echo "exit=$?"
```

- 위 두 개의 (18) 메시지는 curl 8.5.0에 로컬 소켓 서버로 재현해 확인한 출력이다.

## 장애 시나리오와 대처

### 1. 스트림 시작 후 에러 → 200인데 본문이 잘렸다

- **현상**: 내보내기 파일이 가끔 중간에서 끊겨 있다. 모니터링의 상태 코드는 전부 200이다.
- **보이는 형태**
  - 서버 로그: 헤더를 보낸 뒤의 예외(DB 타임아웃 등). 액세스 로그는 200.
  - curl `(18) transfer closed with outstanding read data remaining`
  - Chrome `net::ERR_INCOMPLETE_CHUNKED_ENCODING`(HTTP/1.1), HTTP/2에서는 스트림 리셋 오류
  - 최악: 서버가 예외를 삼키고 정상 종료해서 **아무 오류 없이** 잘린 파일이 저장된다.
- **원인**: 헤더가 나간 순간 상태 코드는 확정이다. 이후 실패는 상태 코드로 알릴 수 없다.
- **대처**
  - 시작 전에 판정 가능한 실패(권한·입력 검증·자원 포화)는 **헤더를 보내기 전에** 검사해 4xx·5xx로 끝낸다.
  - 시작 후 실패는 **비정상 종료**로 끝낸다. HTTP/1.1은 0 청크 없이 연결을 끊고, HTTP/2는 RST_STREAM을 보낸다.
  - 본문 규약에 "정상 끝" 표식(마지막 레코드, 행 수, 체크섬)을 넣고 클라이언트가 확인한다.
  - 액세스 로그에 "응답 완결 여부·보낸 바이트"를 함께 남긴다. 상태 코드만으로는 이 장애가 안 보인다.
  - 사례: [issue/cross-cutting/network/http-streaming-status-locked](../../../issue/cross-cutting/network/http-streaming-status-locked/2-summary.md)

### 2. 프록시 버퍼링 → 스트림이 한꺼번에 도착

- **현상**: 진행률·SSE·LLM 토큰이 실시간으로 안 오고, 끝나거나 몇 KB가 모일 때 한 번에 온다.
- **보이는 형태**: `curl -N`으로 앱 서버를 직접 치면 한 줄씩 오고, nginx를 거치면 몰려서 온다.
- **원인**: nginx `proxy_buffering on`(기본)이 상류 응답을 모았다가 보낸다. 압축 필터도 블록 단위로 모은다(39번).
- **대처**
  - 해당 location에 `proxy_buffering off;`, 또는 앱이 `X-Accel-Buffering: no`를 보낸다.
  - 스트림 응답을 압축에서 빼거나 이벤트마다 flush한다.
  - CDN·LB에도 응답 버퍼링 옵션이 있는지 경로 전체를 확인한다.

### 3. 느린 소비자 → 서버 메모리 누적

- **현상**: 대용량 다운로드가 몰리면 서버 RSS가 치솟고 OOM으로 죽는다. 빠른 클라이언트만 있을 때는 멀쩡하다.
- **보이는 형태**
  - Node: `res.writableLength`가 수백 MB. 힙 스냅샷에 Buffer가 가득하다.
  - `ss -tm`에서 해당 소켓의 송신 큐(Send-Q)가 꽉 차 있다.
- **원인**: `write()`의 `false`를 무시하고 계속 썼다. 또는 전체 결과를 리스트로 모은 뒤 쓴다. 생산 속도 > 네트워크 소비 속도라 차이가 앱 메모리에 쌓인다.
- **대처**
  - `drain`을 기다리거나 `pipeline`을 쓴다. 자바는 DB 커서 + 블로킹 스트림, 리액티브는 demand 기반으로 쓴다.
  - 연결별 쓰기 대기 상한과 전송 타임아웃을 둔다(nginx `send_timeout` 기본 60초는 "두 번의 쓰기 사이" 기준이다).
  - 프록시 버퍼링을 켠 경우에는 프록시의 임시 파일(`proxy_max_temp_file_size` 기본 1024m)과 디스크 사용량을 본다.

### 4. `Content-Length`와 실제 길이가 다르다

- **현상**: 응답을 가끔 못 읽는다. 연결 재사용 뒤 다음 요청이 이상한 응답을 받는다.
- **보이는 형태**: curl `(18) transfer closed with N bytes remaining to read`, Chrome `net::ERR_CONTENT_LENGTH_MISMATCH`
- **원인**
  - 압축·문자 인코딩 변환 전의 길이를 헤더에 적었다.
  - 또는 스트리밍 중 예외로 덜 보냈다.
  - 길이가 실제보다 짧으면 남은 바이트가 **다음 응답의 시작**으로 읽혀 응답이 어긋날 수 있다.
- **대처**: 길이를 모르면 Content-Length를 쓰지 말고 chunked(또는 HTTP/2)에 맡긴다. 길이는 최종 바이트를 만든 뒤에 계산한다.

### 5. chunked를 모르는 수신자 → 본문 0바이트

- **현상**: 같은 요청이 curl로는 되는데 앱 클라이언트로는 서버가 빈 본문을 받는다.
- **원인**: 클라이언트가 요청 본문을 chunked로 보냈고, 수신 서버는 Content-Length만 읽는다.
- **대처**: 송신측에서 길이를 확정해 Content-Length를 보내거나, 수신측이 411(Length Required)로 명시 거절한다. RFC 9112 §6.3도 일부 서비스가 chunked 요청에 411을 준다고 적는다.
  - 사례: [issue/cross-cutting/network/chunked-vs-content-length](../../../issue/cross-cutting/network/chunked-vs-content-length/2-summary.md)

## 핵심 문장

- HTTP/1.1 본문 끝은 chunked > Content-Length > 연결 종료 순으로 정해진다. chunked는 조각마다 16진 길이를 붙이고 0 청크로 끝낸다.
- HTTP/2에는 chunked가 없다. DATA 프레임의 길이와 END_STREAM이 끝을 알리고, 도중 실패는 RST_STREAM으로 그 스트림만 끊는다.
- 헤더가 나가면 상태 코드는 잠긴다. 시작 후 실패는 **비정상 종료**로 알리고, 에러를 삼킨 정상 종료는 조용한 데이터 손상이다.
- 느린 소비자의 차이는 어딘가에 쌓인다. `write()`의 신호(블로킹·`false`·demand)를 따라 생산을 멈추고, 그 신호를 끊는 프록시 버퍼링을 의식한다.
- 청크 경계는 홉마다 바뀔 수 있다. 의미 있는 경계(이벤트·레코드)는 본문 안의 규약으로 만든다.

## 관련 주제·근거

- 선행
  - 24 `application-protocol-framing` — 연결 노트 [systems/resp-protocol](../../systems/resp-protocol/2-summary.md)
  - [33-http-semantics](../33-http-semantics/2-summary.md) · [36-http2-multiplexing](../36-http2-multiplexing/2-summary.md)
  - `reliability/12-backpressure-and-load-shedding` — 연결 노트 [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md)([reliability 영역 표](../../reliability/README.md))
  - [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) — TCP 수신 창.
- 후속·관련
  - [38-websocket-sse-long-lived](../38-websocket-sse-long-lived/2-summary.md) — SSE는 끝나지 않는 스트리밍 응답
  - [39-http-content-encoding](../39-http-content-encoding/2-summary.md) — 압축과 chunked의 결합, 압축기 버퍼링
  - [42-large-file-upload-patterns](../42-large-file-upload-patterns/2-summary.md) — 요청 방향 스트리밍·`proxy_request_buffering`
  - [issue/cross-cutting/network/chunked-vs-content-length](../../../issue/cross-cutting/network/chunked-vs-content-length/2-summary.md)
  - [issue/cross-cutting/network/http-streaming-status-locked](../../../issue/cross-cutting/network/http-streaming-status-locked/2-summary.md)
  - [languages/web-api/26-response-body-streaming](../../../languages/web-api/26-response-body-streaming/2-summary.md) — 브라우저 `ReadableStream` 쪽
- RFC 9112 HTTP/1.1 <https://www.rfc-editor.org/rfc/rfc9112>
  - §6.1 Transfer-Encoding · §6.3 본문 길이 결정(TE+CL 충돌, 411 언급) · §7.1 chunked · §7.1.1 청크 확장 · §7.1.2 트레일러 · §8 불완전 메시지
- RFC 9113 HTTP/2 <https://www.rfc-editor.org/rfc/rfc9113>
  - §5.2 흐름 제어 원칙(초기 창 65,535) · §6.1 DATA · §6.4 RST_STREAM · §6.9 WINDOW_UPDATE · §7 오류 코드 · §8.1 메시지 프레이밍 · §8.2.2 연결 전용 헤더 금지
- RFC 9110 §6.5 트레일러(§6.5.1 사용 제한) <https://www.rfc-editor.org/rfc/rfc9110>
- gRPC over HTTP/2(`grpc-status` 트레일러) <https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md>
- nginx `ngx_http_proxy_module`(`proxy_buffering`·`X-Accel-Buffering`·`proxy_max_temp_file_size`·`proxy_request_buffering`) <https://nginx.org/en/docs/http/ngx_http_proxy_module.html> · `ngx_http_core_module`(`send_timeout`·`chunked_transfer_encoding`) <https://nginx.org/en/docs/http/ngx_http_core_module.html>
- Node.js `stream`(`writable.write()` 반환값·`'drain'`·기본 highWaterMark) <https://nodejs.org/api/stream.html>
- libcurl 오류 코드(`CURLE_PARTIAL_FILE` 18 · `CURLE_HTTP2_STREAM` 92) <https://curl.se/libcurl/c/libcurl-errors.html>
- Chromium `net_error_list.h`(`INCOMPLETE_CHUNKED_ENCODING`·`CONTENT_LENGTH_MISMATCH`) <https://chromium.googlesource.com/chromium/src/+/main/net/base/net_error_list.h>
