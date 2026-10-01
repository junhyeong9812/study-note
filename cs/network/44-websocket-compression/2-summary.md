# network/44-websocket-compression — permessage-deflate와 컨텍스트 유지(context takeover) — 정리 (힌트)

## 해결하는 문제

WebSocket은 연결 하나로 작은 메시지를 계속 주고받는다.\
채팅·시세·게임 상태 메시지는 대부분 비슷한 JSON이다.\
HTTP 응답처럼 `Content-Encoding`을 붙일 자리가 없다. 연결을 연 뒤에는 HTTP 헤더가 더 오가지 않기 때문이다.\
그래서 WebSocket 프레임 수준에서 압축을 따로 정했다. 그것이 **permessage-deflate**(RFC 7692)다.

쉬운 예: 매일 같은 양식의 보고서를 보낸다.\
보고서마다 따로 줄이면 양식 부분을 매번 새로 줄여야 한다.\
"어제 보고서를 참고해서 줄여도 된다"고 약속하면, 양식 부분은 "어제 것과 같음" 한 줄로 끝난다.\
대신 받는 쪽도 어제 보고서를 계속 들고 있어야 한다.

똑같은 구조다.\
**컨텍스트 유지(context takeover)** = 이전 메시지들을 압축 사전으로 계속 쓰는 것.\
압축률은 좋아지고, 그 대가로 **연결마다 사전 메모리**를 잡고 있어야 한다.

실무 예:
- `{"type":"tick","symbol":"AAPL","price":...}` 같은 메시지를 초당 수십 개 보내는 시세 서버.
- 동시 연결이 수만 개인 채팅 서버에서 압축을 켰더니 메모리가 연결 수에 비례해 치솟는다.

## 동작·원리

### 1. 협상 — 여는 핸드셰이크의 `Sec-WebSocket-Extensions`

```text
  Client                                                  Server
  GET /ws HTTP/1.1
  Upgrade: websocket
  Sec-WebSocket-Extensions: permessage-deflate;
                            client_max_window_bits    ---->
                                                          HTTP/1.1 101 Switching Protocols
                                                          Sec-WebSocket-Extensions:
                                                            permessage-deflate;
                                                            server_no_context_takeover
                                                   <----
  (이 연결에서 합의된 파라미터 = 서버 응답에 적힌 것)
```

- 클라이언트가 제안(offer)하고, 서버가 수락 응답(response)에 최종 파라미터를 적는다(RFC 7692 §5).
- 서버가 확장을 응답에 넣지 않으면 압축 없이 진행한다.
- 파라미터는 넷이다(§7).

```text
  파라미터                         뜻
  server_no_context_takeover      서버는 메시지마다 빈 윈도로 압축한다 (서버 -> 클라이언트 방향)
  client_no_context_takeover      클라이언트는 메시지마다 빈 윈도로 압축한다 (클라이언트 -> 서버)
  server_max_window_bits=N        서버 압축 윈도 <= 2^N 바이트 (N = 8..15)
  client_max_window_bits=N        클라이언트 압축 윈도 <= 2^N 바이트
```

- `client_` 접두 파라미터는 클라이언트의 압축기와 서버의 해제기를 설정한다. `server_` 접두는 그 반대다(§7).
- 윈도 크기를 정하지 않으면 최대 32,768바이트(2^15)다(§7.1.2).
- 제안에 `client_max_window_bits`가 없는데 서버 응답에 있으면 안 된다(MUST NOT, §7.1.2.2). 응답이 규칙을 어기면 클라이언트는 연결을 실패 처리해야 한다(MUST, §7).

### 2. 프레임 — RSV1 비트 하나로 "압축됨" 표시

```text
   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
  +-+-+-+-+-------+-+-------------+
  |F|R|R|R| opcode|M| Payload len |
  |I|S|S|S|       |A|             |
  |N|V|V|V|       |S|             |
  | |1|2|3|       |K|             |
  +-+-+-+-+-------+-+-------------+
  |1|1|0|0|   1   |0|      7      |   <- "Hello" 압축본 (RFC 7692 §7.2.3.1)
  +-+-+-+-+-------+-+-------------+
       ^
       RSV1 = 1 : 이 메시지는 압축됐다
```

- RFC 7692는 WebSocket 헤더의 RSV1을 "Per-Message Compressed" 비트로 쓴다(§6).
- 조각난 메시지에서는 **첫 프레임에만** RSV1을 켠다.
- 압축이 이득 없는 메시지는 RSV1을 끄고 원문 그대로 보낼 수 있다(§1). 이미 압축된 이미지 바이너리가 그 예다.
- RFC 6455 §5.2: RSV 비트는 확장을 협상하지 않았으면 0이어야 한다(MUST). 뜻을 모르는 비트가 켜져 오면 연결을 실패 처리한다(MUST).
  - *RSV(reserved) 비트*: 나중에 확장이 쓰라고 비워 둔 프레임 헤더 비트다.

### 3. 압축·해제 절차 — 꼬리 4바이트를 떼고 붙인다

```text
  송신: 메시지 --DEFLATE--> ... [빈 비압축 블록 00 00 ff ff] --꼬리 4바이트 제거--> 페이로드
  수신: 페이로드 --꼬리에 00 00 ff ff 붙임--> --INFLATE--> 메시지
```

- 송신 쪽은 DEFLATE로 압축하고 빈 비압축 블록으로 바이트 경계를 맞춘다. 그리고 끝의 `0x00 0x00 0xff 0xff`를 뗀다(§7.2.1).
  - zlib에서는 `Z_SYNC_FLUSH`가 이 빈 블록을 만든다(§7.3).
- 수신 쪽은 그 4바이트를 다시 붙이고 해제한다(§7.2.2).
- 예: "Hello" → `f2 48 cd c9 c9 07 00`(7바이트).

### 4. 컨텍스트 유지 — 이전 메시지를 사전으로

```text
  컨텍스트 유지 (기본)                         no_context_takeover
  msg1 "Hello" -> f2 48 cd c9 c9 07 00        msg1 "Hello" -> f2 48 cd c9 c9 07 00
  msg2 "Hello" -> f2 00 11 00 00              msg2 "Hello" -> f2 48 cd c9 c9 07 00
                  (msg1을 역참조, 5바이트)                    (매번 같은 7바이트)

  [LZ77 윈도: 최근 32KB]  연결이 살아 있는 동안 유지    메시지가 끝나면 비워도 됨
```

(RFC 7692 §7.2.3.2의 예)

- 기본은 컨텍스트 유지다. 송신 쪽은 이전 메시지에 쓴 LZ77 윈도를 이어 쓸 수 있다(MAY).
- 그래서 수신 쪽은 이전 메시지의 윈도로 해제해야 한다(MUST, §7.2.2). 즉 **양쪽 모두** 윈도를 연결 수명 동안 들고 있어야 한다.
- `*_no_context_takeover`가 합의되면, 그 방향의 송신자는 메시지마다 빈 윈도로 시작해야 한다(MUST, §7.2.1).
  - 그러면 수신자도 메시지 사이에 윈도를 보관할 필요가 없다(§7.1.1.1).
- 압축하지 않은 메시지(RSV1=0)는 윈도에 영향을 주지 않는다(§7.2.3.2).

  - *LZ77 슬라이딩 윈도*: DEFLATE가 "최근 처리한 입력"을 담아 두는 버퍼다. 다음 입력에서 같은 문자열을 찾으면 역참조로 바꾼다(RFC 7692 §7, RFC 1951).

### 5. 메모리 — 연결 수 × (압축기 + 해제기)

Node.js 문서가 인용한 zlib의 메모리 공식이다(`zlib/zconf.h`).

```text
  deflate(압축기) = (1 << (windowBits + 2)) + (1 << (memLevel + 9))
                  기본 windowBits=15, memLevel=8  ->  128K + 128K = 약 256KB
  inflate(해제기) = 1 << windowBits
                  기본 windowBits=15              ->  약 32KB
```

서버 한 연결이 양방향 컨텍스트를 모두 유지하면 대략 이렇다(계산 예시).

```text
  연결 1개   : deflate 256KB + inflate 32KB  ≈ 288KB  (+ 수 KB의 작은 객체)
  연결 1만개 : ≈ 2.8GB
  윈도·memLevel을 줄이면 (windowBits=10, memLevel=7):
             deflate = 4KB + 64KB = 68KB,  inflate = 1KB  ->  1만 연결 ≈ 0.7GB
```

- 윈도를 줄이면 압축률이 떨어진다. RFC 7692는 쓸 만한 압축률을 위해 1,024바이트 이상의 윈도를 권한다(RECOMMENDED, §7.3).
- `no_context_takeover`는 메시지 사이에 윈도를 들고 있을 의무를 없앤다. 실제로 메모리를 반납하는지는 구현에 달렸다.
  - Node `ws`는 메시지가 끝나면 zlib 스트림을 `reset()`만 한다(ws `lib/permessage-deflate.js`). zlib의 reset은 내부 상태를 해제·재할당하지 않는다(zlib manual `deflateReset`). 그래서 ws에서는 연결당 메모리가 그대로다.
  - 메모리를 확실히 줄이는 것은 윈도 비트·`memLevel` 축소나 압축 끄기다.

## 쓰이는 자료구조·알고리즘

- **LZ77 슬라이딩 윈도 딕셔너리** — 최근 N바이트를 원형 버퍼로 유지하고 그 안에서 일치를 찾는다. [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md)의 "창을 밀며 최근 구간만 본다"와 같은 구조다. 컨텍스트 유지는 이 창을 메시지 경계를 넘어 계속 민다는 뜻이다.
- **해시 체인** — zlib은 3바이트 해시로 윈도 안의 후보 위치를 찾는다. `memLevel`이 이 해시 테이블 크기를 정한다. 그래서 공식의 둘째 항이 `memLevel`에 달려 있다. [05-hashmap](../../data-structure/05-hashmap/2-summary.md) 참고.
- **허프만 부호** — DEFLATE의 둘째 단계다. 고정 부호(BTYPE=01)나 동적 부호(BTYPE=10)를 쓴다.
- **확장 협상 = 파라미터 교집합** — 클라이언트 제안 목록에서 서버가 지원하는 조합을 고른다. 결과는 "합의된 파라미터(agreed parameters)"다.
- **동시성 제한 큐** — Node `ws`는 zlib 호출 동시 개수를 제한하고(`concurrencyLimit`, 기본 10) 넘치면 줄 세운다.

## 적용 — 풀어나가는 법

### 1. 켤지부터 정한다

```text
  메시지가 반복적 텍스트(JSON)이고 대역폭이 비싸다   -> 켤 가치가 있다
  메시지가 이미 압축된 바이너리(이미지·protobuf+zstd) -> 이득 없음, 끈다
  동시 연결이 매우 많다                             -> 메모리 계산부터, 윈도·memLevel 축소
  비밀 + 사용자 입력이 같은 연결로 흐른다             -> 사이드채널 검토(43번)
```

Node `ws`는 **서버 기본값이 꺼짐**, 클라이언트 기본값이 켜짐이다(ws README).\
ws 문서는 압축이 성능·메모리 부담이 크니 정말 필요할 때만 켜라고 권한다.\
또 Linux에서 동시성이 높으면 zlib 때문에 메모리 단편화가 심해질 수 있으니 실제 부하로 시험하라고 경고한다.

### 2. 켠다면 메모리 상한을 먼저 건다

```js
import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({
  port: 8080,
  maxPayload: 1 * 1024 * 1024,      // 해제 후 메시지 크기 상한. ws 기본은 100 MiB
  perMessageDeflate: {
    serverNoContextTakeover: true,  // 서버 -> 클라이언트: 메시지마다 빈 윈도
    clientNoContextTakeover: true,  // 클라이언트 -> 서버: 메시지마다 빈 윈도(응답에 넣음)
    serverMaxWindowBits: 10,        // 서버 압축 윈도 1KB
    zlibDeflateOptions: { memLevel: 7, level: 3 },
    threshold: 1024,                // 이보다 작은 메시지는 압축 안 함(컨텍스트 유지 끈 경우)
    concurrencyLimit: 10,           // zlib 동시 호출 수
  },
});

wss.on('connection', (ws) => {
  // 실제로 무엇이 합의됐는지 로그로 남긴다
  console.log('negotiated:', ws.extensions);
});
```

- `threshold`는 **컨텍스트 유지를 끈 경우에만** 작은 메시지를 건너뛴다(ws 문서).
- 서버가 `clientNoContextTakeover`를 응답에 넣으면 클라이언트도 메시지마다 빈 윈도로 압축해야 한다. 서버는 해제용 윈도를 메시지 사이에 들고 있지 않아도 된다.

### 3. 협상 결과를 눈으로 본다

```bash
# 여는 핸드셰이크만 보내 101 응답의 확장 헤더를 확인한다
curl -s -i -N --max-time 3 \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  -H 'Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits' \
  http://localhost:8080/ | grep -i -E '^HTTP|sec-websocket-extensions'
```

- 브라우저에서는 개발자 도구 Network 탭에서 WS 연결의 응답 헤더를 본다. JS에서는 `socket.extensions` 문자열로 합의 결과를 읽는다.
- 브라우저 `WebSocket` API로는 압축 파라미터를 고를 수 없다. 서버 응답으로만 조절한다.

### 4. 메모리를 연결 수와 함께 본다

```js
setInterval(() => {
  const m = process.memoryUsage();
  console.log(JSON.stringify({
    conns: wss.clients.size,
    rssMB: Math.round(m.rss / 1e6),
    externalMB: Math.round(m.external / 1e6), // zlib 등 네이티브 메모리가 여기에 잡힌다
  }));
}, 10_000);
```

- 연결당 메모리 = (rss 증가분) / (연결 증가분). 이 값이 앞의 계산(수백 KB)에 가까우면 압축 컨텍스트가 주범이다.

## 장애 시나리오와 대처

### 1. 동시 연결이 많아지자 메모리가 폭증한다

- **현상**: 이벤트 때 동시 접속이 늘자 WebSocket 서버가 OOM으로 재시작한다.
- **보이는 형태**
  - 컨테이너 exit code 137(OOMKilled).
  - `rss`가 연결 수에 거의 정비례해 오른다. 연결당 수백 KB다.
  - 힙 스냅숏에는 잘 안 보이고 `external`·네이티브 메모리가 크다.
- **원인**: 컨텍스트 유지 + 기본 윈도(32KB) + 기본 `memLevel` → 연결마다 압축기 약 256KB + 해제기 약 32KB를 계속 들고 있다(zlib 공식).
- **대처**
  - `server_max_window_bits`와 `memLevel`을 줄인다.
  - `server_no_context_takeover`·`client_no_context_takeover`는 구현이 메시지마다 zlib 객체를 닫을 때만 메모리를 줄인다. `ws`는 reset만 하므로 줄지 않는다.
  - 압축 이득이 작으면 끈다.
  - 수용량 계산에 "연결당 메모리"를 넣는다.

### 2. 비밀이 든 메시지를 압축해 길이로 샌다

- **현상**: 보안 점검에서 "WebSocket 메시지 압축 + 사용자 입력 반영"이 지적된다.
- **보이는 형태**: 조용하다. 공격자가 같은 연결에 넣은 입력에 따라 메시지 길이가 1~2바이트씩 달라진다.
- **원인**
  - 컨텍스트 유지 중에는 **이전 메시지들까지** 같은 압축 사전이다.
  - 예: 서버가 앞서 보낸 메시지에 토큰이 있고, 뒤 메시지에 공격자가 조절한 문자열이 반영된다.
  - RFC 7692 §8은 이력 기반 압축과 보안 전송을 섞을 때 CRIME류 공격이 있다고 경고한다.
- **대처**
  - 비밀을 담은 메시지는 압축하지 않는다(RSV1=0으로 보낸다).
  - 또는 `server_no_context_takeover`로 메시지 간 사전 공유를 끊는다. 한 메시지 안에 비밀과 입력이 같이 있으면 이것으로도 부족하다.
  - 원리와 대처는 [43-compression-side-channels](../43-compression-side-channels/2-summary.md)와 같다.

### 3. 압축 폭탄 — 작은 프레임이 거대한 메시지로 풀린다

- **현상**: 특정 클라이언트가 연결한 직후 서버 메모리가 급증한다.
- **보이는 형태**: 페이로드는 수 KB인데 해제 결과가 수백 MB다. ws는 해제 중 `maxPayload`를 넘으면 `WS_ERR_UNSUPPORTED_MESSAGE_LENGTH` 에러와 종료 코드 1009(Message Too Big)를 쓴다(ws `lib/permessage-deflate.js`, API 문서).
- **원인**: DEFLATE는 반복 데이터를 극단적으로 줄인다. 해제 전에는 원래 크기를 알 수 없다.
- **대처**
  - 해제 후 크기 상한(`maxPayload`)을 서비스 필요에 맞게 낮춘다. ws 기본값 100 MiB는 대부분 서비스에 너무 크다.
  - 상한을 넘는 연결은 끊고 기록한다.

### 4. CPU가 튀고 메시지 지연이 늘어난다

- **현상**: 브로드캐스트가 많은 시간대에 p99 메시지 지연이 늘고 CPU가 포화된다.
- **보이는 형태**
  - 이벤트 루프 지연 지표 상승.
  - 프로파일에서 zlib deflate 호출 비중이 크다.
- **원인**
  - 같은 메시지를 연결마다 **따로** 압축한다. 컨텍스트 유지 중에는 연결마다 사전이 달라서 압축 결과를 재사용할 수 없다.
  - zlib 동시 호출은 `concurrencyLimit`에서 줄을 선다.
- **대처**
  - 브로드캐스트가 많으면 압축 수준(`level`)을 낮추거나 압축을 끈다.
  - `no_context_takeover`에서는 같은 메시지의 압축 결과가 연결마다 같아질 수 있다. 그래서 한 번 압축해 재사용할 여지가 생긴다(구현 지원 여부 [?]).

### 5. 협상이 깨져 연결 직후 끊긴다

- **현상**: 특정 프록시나 자체 구현 서버를 거치면 브라우저가 연결 직후 에러를 낸다.
- **보이는 형태**: 브라우저 콘솔의 WebSocket 연결 실패. 핸드셰이크 응답의 `Sec-WebSocket-Extensions` 값이 제안과 맞지 않는다.
- **원인**: 서버 응답이 RFC 규칙을 어겼다. 예: 제안에 없던 `client_max_window_bits`를 응답에 넣었거나, 같은 파라미터를 두 번 넣었다. 이런 응답이면 클라이언트는 연결을 실패 처리해야 한다(MUST, RFC 7692 §7).
- **대처**
  - 위 `curl` 핸드셰이크로 응답 헤더를 확인한다.
  - 서버 확장 구현을 고치거나 압축을 끈다.

## 핵심 문장

- permessage-deflate는 여는 핸드셰이크의 `Sec-WebSocket-Extensions`로 협상하고, 압축된 메시지는 첫 프레임의 RSV1 비트로 표시한다.
- 송신 쪽은 DEFLATE 결과 끝의 `00 00 ff ff`를 떼고, 수신 쪽은 그 4바이트를 붙여 해제한다.
- 기본은 컨텍스트 유지다. 이전 메시지가 사전이 되어 압축률이 좋아지는 대신, 양쪽이 연결 수명 동안 LZ77 윈도를 들고 있어야 한다.
- 메모리는 "연결 수 × (압축기 + 해제기)"다. zlib 기본값이면 압축기만 약 256KB라서, 연결이 많으면 윈도·`memLevel` 축소가 필요하다(`no_context_takeover`는 구현에 따라 메모리를 못 줄인다).
- 컨텍스트 유지는 여러 메시지를 한 압축 사전에 넣는다. 비밀과 사용자 입력이 한 연결로 흐르면 43번의 길이 사이드채널이 그대로 적용된다.

## 관련 주제·근거

- 선행
  - [38-websocket-sse-long-lived](../38-websocket-sse-long-lived/2-summary.md) — WebSocket 연결 수명. 저장소의 언어 노트 [languages/web-api/33-websocket](../../../languages/web-api/33-websocket/2-summary.md)
  - [39-http-content-encoding](../39-http-content-encoding/2-summary.md) — HTTP 압축 협상
  - `algorithm/33-lossless-compression-lz77-huffman` — 미작성([algorithm 커리큘럼](../../algorithm/curriculum.md))
- 연결
  - [43-compression-side-channels](../43-compression-side-channels/2-summary.md) — 압축 사이드채널 원리
- RFC 7692 Compression Extensions for WebSocket <https://www.rfc-editor.org/rfc/rfc7692>
  - §5 확장 협상 · §6 RSV1 비트 · §7 파라미터 4종 · §7.1.1 컨텍스트 유지 · §7.1.2 윈도 크기 · §7.2.1 압축 · §7.2.2 해제 · §7.2.3 예시 · §7.3 구현 노트 · §8 보안 고려(CRIME)
- RFC 6455 §5.2 Base Framing Protocol(RSV 비트) <https://www.rfc-editor.org/rfc/rfc6455>
- RFC 1951 DEFLATE
- Node.js `zlib` 문서 "Memory usage tuning" <https://nodejs.org/api/zlib.html>
- `ws` README "WebSocket compression"·API 문서(`perMessageDeflate`, `maxPayload`) <https://github.com/websockets/ws/blob/master/doc/ws.md>
- `ws` 소스 `lib/permessage-deflate.js`(no_context_takeover 시 `reset()`) <https://github.com/websockets/ws/blob/master/lib/permessage-deflate.js>
- zlib manual `deflateReset`·`inflateReset`(내부 상태를 해제하지 않음) <https://zlib.net/manual.html>
- RFC 9842 Compression Dictionary Transport(응답 간 사전 공유 — 정답 7의 예외) <https://www.rfc-editor.org/rfc/rfc9842>
