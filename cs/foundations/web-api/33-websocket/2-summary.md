# web-api/33 — WebSocket: 핸드셰이크·프레임·닫힘 코드와 재연결 설계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「서버 요청 로그」를 바이트까지 내린 「선로 덤프」다** — 파이썬 표준 라이브러리로 **직접 짠** 서버가 핸드셰이크 요청 원문 · 자기가 보낸 101 응답 · 오가는 **프레임의 머리 바이트(16진)** 를 적는다. 그 옆에 페이지가 받은 이벤트(`open` · `message` · `error` · `close`)를 나란히 놓고, **「닫힘 코드 격자」**(서버가 닫는 방법 8가지 → `CloseEvent.code`·`wasClean`)로 **선로의 코드와 페이지의 코드가 갈리는 칸**을 센다.\
> ★★ **기준 소스 — 명세 원문을 이 판에서 열지 못했다.** 브라우저 API 는 [WHATWG WebSockets](https://websockets.spec.whatwg.org/), 선로 규칙은 [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455) 가 정본인데, 이 배치는 **외부 네트워크를 쓰지 않았고** 앞 배치의 명세 사본에 둘 다 없다. 앞 배치의 **Fetch 사본**에서 확인한 것은 한 가지다 — 「WebSocket 객체는 연결을 세우는 과정에서 **특별한 종류의 fetch**(요청 mode `"websocket"`)를 시작하고, **연결을 얻고 세우는 절차는 이제 WebSockets 명세에 정의돼 있다**」. 매직 GUID 는 **이 머신의 다른 구현**(파이썬 `websocket-client` 의 `_handshake.py`)이 같은 값을 쓰는 것까지 확인했다(아래 (2)). 그 밖의 규칙 서술은 전부 **이 판의 관찰**이고, 명세대로인지 **판정하지 않는다**(가이드 규칙 5). 기준일 2026-09-26.\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 서버는 **`websockets` 패키지를 쓰지 않았다**(설치돼 있지 않다 — (2)의 첫 블록). 쓰지 않는 쪽이 원시 바이트를 보여 주기 좋다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★ **[32번 주제](../32-server-sent-events/2-summary.md)** — 한 방향 · **브라우저가 다시 붙는** 쪽. 여기는 양방향 · **앱이 다시 붙어야 하는** 쪽이다. 하네스는 32편 (1)이다.\
> **경계** — ★★ **재연결의 백오프(지수 + 지터)는 설계 권고층이다** — 정본은 [`../../../ops-patterns/01-retry-backoff/`](../../../ops-patterns/01-retry-backoff/2-summary.md)(고정 간격 · 지수 백오프 · **지터가 동시에 몰린 재시도를 흩뿌린다** · 재시도 예산). 여기서는 **「끊김을 감지하는 신호가 무엇이냐」** 한 칸만 잰다((7)). ★ 연혁(RFC 6455 확정 · IETF 이관)은 [`../../../../history/web/05-웹플랫폼-API.md`](../../../../history/web/05-웹플랫폼-API.md) §4 의 「WebSocket: 양방향 영속 연결」 절이 정본이다 — 그쪽은 **폴링 대비와 핸드셰이크 한 줄**까지, 여기는 **그 핸드셰이크와 프레임을 바이트로**. ★ **「WebSocket 이 SSE 보다 무겁다/가볍다」는 재지 않았다.**\
> 이 본문은 Claude 작성이다(원고 없음). 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 요청 헤더의 이름·순서·값 · 101 응답 · 프레임 머리 바이트 · 풀어낸 본문 · 닫힘 코드 격자 · `close()` 인자 표 · 침묵 서버 · 콘솔 문구 | 캡처 세 판이 **한 글자도 같았다** |
| ★ **흔들리게 만들지 않았다** | **`Sec-WebSocket-Key` · `Sec-WebSocket-Accept` · 마스킹 키 · 가려진 본문** | 판마다 무작위다 — 하네스가 **출력 전에 가리고 길이만** 찍는다. 계산이 맞는지는 **「서버가 계산한 Accept 가 base64(SHA-1(키 + GUID)) 와 같나 = True」** 로, 계산 자체는 **고정한 키 하나로** 따로 보인다((2)) |
| ★ **가린 칸** | `User-Agent` · `Accept-Language` | 판 번호 · 이 머신의 언어 설정이 박힌다 — 주제 밖이라 `<생략>` |
| ★ **판에 매일 수 있는 칸** | 큰 메시지를 쪼개는 **조각 크기 131000** | Chrome 이 고른 값이다((8)) — 세 판 같았지만 보장이 아니다 |
| **흔들린다** | Chrome 판 번호 · 포트 | 포트는 출력에 안 나온다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `readyState` · `protocol` · `extensions` · `bufferedAmount` · `CloseEvent` 의 `code`·`wasClean`·`reason` |
| 창 ③ 같은 것을 두 번 읽기 | **부적용** | — |
| **창 ④ 서버 요청 로그 → 선로 덤프** | ★★★ **본체** | 요청 원문 · 101 · 프레임 머리(FIN · opcode · MASK · 길이) · 브라우저가 **스스로** 보낸 프레임(pong · close 답) |
| ★ **「ping 이 왔나」를 서버 창으로** | ★★ **제5의 상태 — 같은 질문을 다른 창으로** | 페이지에는 ping · pong 을 볼 API 가 없다 — **서버가 받은 pong 프레임**으로 답했다. ★ 서버 창이 못 보는 것 — **브라우저가 그 pong 을 언제 만들었나**(페이지 태스크와의 순서) |
| ★ **「반쯤 열린 연결」을 침묵 서버로** | ★★ **제5의 상태** | 진짜 네트워크 단절 대신 **소켓을 연 채 입을 닫는 서버**로 물었다((7)). ★ 바꾼 창이 못 보는 것 — **운영체제 TCP 가 언제 포기하나**(keepalive · 재전송 한도) |
| 콘솔(Log 도메인) | ★ **쓴다** | 틀린 Accept 의 거절 문구 |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **명세 문장** | 원문을 열지 못했다(머리말) |
| **진짜 반쯤 열린 연결**(케이블이 뽑힘 · NAT 가 조용히 버림) | 서버의 침묵으로만 흉내 냈다 |
| **`permessage-deflate` 가 켜진 프레임** | 브라우저는 제안했지만 서버가 **안 받았다**((3)) — 압축된 프레임은 못 봤다 |
| **`wss://`(TLS)** | 평문 `ws://` 만 던졌다 |
| **백오프가 실제로 부하를 흩뿌리나** | 재지 않았다 — ops-patterns 01 의 몫 |

## 한눈에 — 쉽게 말하면

**★ WebSocket 은 「안내 데스크에서 시작해 직통 전화로 바뀌는 통화」다. 처음엔 평범한 접수 창구(HTTP)에 「직통으로 바꿔 주세요」(`Upgrade: websocket`) 하고 암호 쪽지(`Sec-WebSocket-Key`)를 낸다. 창구가 쪽지에 정해진 도장(GUID)을 찍어 되돌려 주면(`Sec-WebSocket-Accept`) 그때부터 같은 선이 직통 전화가 된다. 전화에서는 말 한 마디마다 봉투(프레임)에 넣고, 브라우저 쪽이 보내는 봉투는 늘 가림막(마스킹)을 씌운다. 끊을 때는 「이만 끊을게요, 사유는 …」(close 프레임)를 주고받는데 — 선이 그냥 끊기면 아무 말도 못 들은 것이다.**

| 비유 | 실체 |
|---|---|
| 접수 창구에 「직통으로」 | `GET` + `Connection: Upgrade` + `Upgrade: websocket` + `Sec-WebSocket-Version: 13` |
| 암호 쪽지 · 도장 찍은 답 | `Sec-WebSocket-Key`(16바이트의 base64) · `Sec-WebSocket-Accept` = base64(SHA-1(키 + GUID)) |
| 직통으로 바뀜 | `101 Switching Protocols` — 그 뒤로 같은 TCP 연결 위에 프레임 |
| 봉투 | 프레임 — FIN · opcode(1 글 · 2 바이너리 · 8 close · 9 ping · 10 pong) · MASK · 길이 |
| 브라우저 봉투의 가림막 | MASK=1 · 4바이트 마스킹 키 — 서버 쪽은 MASK=0 |
| 「이만 끊을게요, 사유는」 | close 프레임(코드 2바이트 + 이유) — 받은 쪽이 같은 코드로 답한다 |
| 선이 그냥 끊김 | `CloseEvent.code = 1006` — **선로에는 없는 코드**, 브라우저가 만든다 |

```text
   HTTP 로 시작해 프로토콜이 바뀐다 (이 판 — 같은 TCP 연결 하나)

   브라우저                                               서버(직접 짠 것)
   GET /ws HTTP/1.1  Connection: Upgrade  Upgrade: websocket
   Sec-WebSocket-Version: 13  Sec-WebSocket-Key: <24자> ──────▶  Accept = base64(SHA-1(키 + GUID))
            ◀────── HTTP/1.1 101 Switching Protocols  Sec-WebSocket-Accept: <28자>
   ─── 여기부터 HTTP 가 아니다 — 프레임 ───
            ◀────── 89 02 "p1"          ping (페이지에는 안 보인다)
   8a 82 <키> …  ──────────────────────▶  pong (브라우저가 스스로)
   81 86 <키> "안녕" ──────────────────▶  글 · MASK=1
            ◀────── 88 06 03 e8 "done"  close 1000
   88 86 <키> 03 e8 "done" ───────────▶  같은 코드로 답
```

## 이 주제가 답하려는 질문

1. **HTTP 요청이 어떻게 WebSocket 연결이 되나** — 요청 · 101 · Accept 계산, 그리고 **틀리면** 무엇이 보이나.
2. **선로에서 무엇이 오가나** — 프레임 머리 · 마스킹 · ping/pong · close 답.
3. **끊긴 것을 페이지는 무엇으로 아나** — `CloseEvent.code` 가 선로와 갈리는 칸 · 반쯤 열린 연결 · 재연결을 누가 하나.

## 동작 방식

### (1) 하네스 — 32편 (1)의 `/ws`

**서버는 [32번 주제](../32-server-sent-events/2-summary.md)의 (1) `wa32b-net.py` 의 `/ws` 다.** `http.server` 가 요청 머리를 읽고 나면 **같은 소켓을 넘겨받아** 101 을 쓰고, 그 뒤로는 프레임을 직접 읽고 쓴다.

- **`ws_recv`** — 머리 2바이트 → 길이가 126 이면 2바이트 · 127 이면 8바이트 더 → MASK=1 이면 4바이트 키 → 본문을 **키로 XOR 해서** 푼다. 로그에는 **머리 바이트(16진)** 와 **풀어낸 본문**만 싣고, 키와 가려진 본문은 **길이만** 적는다.
- **`ws_send`** — FIN=1 · MASK=0 · 길이 125 이하. 보낸 바이트를 16진으로 적는다.
- 시나리오는 질의 `s=` 로 고른다 — `frames` · `close-<코드>` · `client` · `badaccept` · `silent` · `buffer`.

### (2) ★★ Accept 계산 — 고정한 키 하나로

**`websockets` 패키지가 있나부터** — 없다. `websocket`(하이픈 없는 쪽)은 **CDP 에 붙는 클라이언트**로 하네스가 쓰는 것이다.

```text
$ python3 -c "import importlib.util as u; print('websockets', u.find_spec('websockets')); print('websocket(CDP 클라이언트)', u.find_spec('websocket') is not None)"
websockets None
websocket(CDP 클라이언트) True
(exit 0)
```

**키를 고정하면 계산이 결정적이다** — 16바이트 `wa32b-33-key-16b` 의 base64 를 키로 준다.

```text
$ python3 wa32b-net.py accept d2EzMmItMzMta2V5LTE2Yg==
Sec-WebSocket-Key    = d2EzMmItMzMta2V5LTE2Yg==
키 + GUID            = d2EzMmItMzMta2V5LTE2Yg==258EAFA5-E914-47DA-95CA-C5AB0DC85B11
SHA-1 (16진)         = 7d8a36bb9314b94f55823abbbfd61af8e1d92ccc
Sec-WebSocket-Accept = fYo2u5MUuU9Vgjq7v9Ya+OHZLMw=
(exit 0)
```

**다른 도구로 같은 계산** — `openssl` 로 SHA-1 을 내고 `base64` 로 싼다.

```text
$ printf '%s' 'd2EzMmItMzMta2V5LTE2Yg==258EAFA5-E914-47DA-95CA-C5AB0DC85B11' | openssl dgst -sha1 -binary | base64
fYo2u5MUuU9Vgjq7v9Ya+OHZLMw=
(exit 0)
```

**GUID 는 이 머신의 다른 구현도 같은 값을 쓴다** — CDP 클라이언트 `websocket-client` 의 핸드셰이크 코드.

```text
$ grep -n '258EAFA5' /usr/lib/python3/dist-packages/websocket/_handshake.py
191:    value = f"{key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11".encode("utf-8")
(exit 0)
```

- ★★ **Accept = base64(SHA-1(키 + GUID))** — 하네스와 `openssl` 이 **같은 28글자**(`fYo2u5MUuU9Vgjq7v9Ya+OHZLMw=`)를 냈다. 키는 **base64 글자 그대로** 이어 붙인다(풀지 않는다).
- **GUID `258EAFA5-E914-47DA-95CA-C5AB0DC85B11`** — 이 판에서는 **두 구현이 같은 값을 쓴다**는 것까지 확인했다. RFC 원문은 열지 못했다.

### (3) ★★★ 본체 — 핸드셰이크 한 번과 프레임

```html
<!-- wa32b-33-frames.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>33 frames</title>
<script>
// 핸드셰이크 한 번 · 프레임 주고받기 — 페이지가 본 것(이벤트)과 서버가 본 것(원시 바이트)을 나란히
window.__끝 = () => new Promise(r => {
  const 줄 = [], ws = new WebSocket(`ws://${location.host}/ws?id=h&show=1&s=frames`);
  ws.binaryType = "arraybuffer";
  줄.push("new WebSocket 직후 readyState=" + ws.readyState + " · protocol=" + JSON.stringify(ws.protocol));
  ws.onopen = () => 줄.push("open · readyState=" + ws.readyState + " · extensions=" + JSON.stringify(ws.extensions));
  ws.onmessage = e => {
    if (typeof e.data === "string") {
      줄.push("message 글 " + JSON.stringify(e.data));
      ws.send("안녕");
    } else {
      줄.push("message 바이너리 [" + new Uint8Array(e.data).join(",") + "]");
      ws.send(new Uint8Array([4, 5, 6]));
      ws.send("x".repeat(200));
    }
  };
  ws.onerror = () => 줄.push("error");
  ws.onclose = e => {
    줄.push(`close · code=${e.code} · wasClean=${e.wasClean} · reason=${JSON.stringify(e.reason)} · readyState=${ws.readyState}`);
    r(줄.join("\n"));
  };
});
</script>
```

```text
$ python3 wa32b-net.py page wa32b-33-frames.html
new WebSocket 직후 readyState=0 · protocol=""
open · readyState=1 · extensions=""
message 글 "서버가 보낸 글"
message 바이너리 [1,2,3]
close · code=1000 · wasClean=true · reason="done" · readyState=3
--- 서버 로그 ---
A 받은 요청 원문(헤더 순서 그대로)
    GET /ws?id=h&show=1&s=frames HTTP/1.1
    Host: 127.0.0.1:<A>
    Connection: Upgrade
    Pragma: no-cache
    Cache-Control: no-cache
    User-Agent: <생략>
    Upgrade: websocket
    Origin: http://127.0.0.1:<A>
    Sec-WebSocket-Version: 13
    Accept-Encoding: gzip, deflate, br, zstd
    Accept-Language: <생략>
    Sec-WebSocket-Key: <24자 — base64 를 풀면 16바이트>
    Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits
A 보낸 응답 원문
    HTTP/1.1 101 Switching Protocols
    Upgrade: websocket
    Connection: Upgrade
    Sec-WebSocket-Accept: <28자 — 서버가 계산한 값>
    (서버가 계산한 Accept 가 base64(SHA-1(키 + GUID)) 와 같나 = True)
A 서버→브라우저  89 02 70 31   ← FIN=1 opcode=9(ping) MASK=0 길이=2
A 브라우저→서버  8a 82 <마스킹 키 4바이트> <가려진 본문 2바이트>   ← FIN=1 opcode=10(pong) MASK=1 길이=2
A                풀어낸 본문 = 바이트 70 31
A 서버→브라우저  81 14 ec 84 9c eb b2 84 ea b0 80 20 eb b3 b4 eb … (모두 22바이트)   ← FIN=1 opcode=1(텍스트) MASK=0 길이=20
A 서버→브라우저  82 03 01 02 03   ← FIN=1 opcode=2(바이너리) MASK=0 길이=3
A 브라우저→서버  81 86 <마스킹 키 4바이트> <가려진 본문 6바이트>   ← FIN=1 opcode=1(텍스트) MASK=1 길이=6
A                풀어낸 본문 = 글 '안녕'
A 브라우저→서버  82 83 <마스킹 키 4바이트> <가려진 본문 3바이트>   ← FIN=1 opcode=2(바이너리) MASK=1 길이=3
A                풀어낸 본문 = 바이트 04 05 06
A 브라우저→서버  81 fe 00 c8 <마스킹 키 4바이트> <가려진 본문 200바이트>   ← FIN=1 opcode=1(텍스트) MASK=1 길이=200
A                풀어낸 본문 = 글 'xxxxxxxx'… (200글자)
A 서버→브라우저  88 06 03 e8 64 6f 6e 65   ← FIN=1 opcode=8(close) MASK=0 길이=6
A 브라우저→서버  88 86 <마스킹 키 4바이트> <가려진 본문 6바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=6
A                풀어낸 본문 = close 코드=1000 이유='done'
(exit 0)
```

**요청 원문**

- ★★ **`GET … HTTP/1.1` · `Connection: Upgrade` · `Upgrade: websocket` · `Sec-WebSocket-Version: 13` · `Origin`** — 평범한 HTTP 요청이다. `Origin` 이 실린다 — **서버가 출처를 보고 거절할 수 있다**는 뜻이다(이 서버는 안 봤다).
- ★ **`Sec-WebSocket-Key` 는 24자 — base64 를 풀면 16바이트.** 판마다 새로 만든다.
- ★ **`Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits`** — 브라우저가 **압축을 제안**했다. 서버가 101 에 그 헤더를 안 돌려주자 **페이지의 `extensions` 는 `""`** 이다. 제안은 서버가 받아야 켜진다.

**101 과 그 뒤**

- **`101 Switching Protocols` 에 `Upgrade` · `Connection` · `Sec-WebSocket-Accept` 셋** — 그 뒤로 같은 TCP 위에 프레임이 오간다. 페이지의 `open` 은 여기서 났다(`readyState=1`).

**프레임**

- ★★★ **브라우저가 보낸 프레임은 전부 MASK=1** — `8a 82` · `81 86` · `82 83` · `81 fe` · `88 86` 의 **둘째 바이트 최상위 비트가 1** 이다(`82`=1000 0010 → MASK 1 · 길이 2). **서버가 보낸 프레임은 전부 MASK=0**(`89 02` · `81 14` · `82 03` · `88 06`).
- ★★ **첫 바이트 = FIN + opcode** — `81` 은 FIN=1 · 글(1), `82` 바이너리(2), `88` close(8), `89` ping(9), `8a` pong(10).
- ★★ **ping 은 페이지에 안 보였다** — `message` 는 **글 하나 · 바이너리 하나** 둘뿐이다. 그런데 **서버는 곧바로 pong(`8a 82`, 본문 `70 31` = `"p1"`)** 을 받았다 — **브라우저가 앱 몰래 답했다.**
- ★ **글은 UTF-8 바이트 길이**다 — `"안녕"` 은 6(`81 86`), 서버의 `"서버가 보낸 글"` 은 20(`81 14`).
- ★ **200바이트 글은 길이 칸이 `7e`(126)** 이고 뒤 2바이트 `00 c8`(=200)이 진짜 길이다 — 머리가 `81 fe 00 c8`. 126 이상이면 길이를 따로 싣는다.
- **닫기** — 서버가 `88 06 03 e8 "done"`(1000 · `done`)을 보내자 **브라우저가 같은 코드 · 같은 이유로 답했다**(`88 86 …` → `close 코드=1000 이유='done'`). 페이지는 `close · code=1000 · wasClean=true · reason="done"`.

```text
   프레임 머리 2바이트 읽는 법 (이 판의 바이트로)

   81 86 ……            1000 0001 │ 1000 0110
                       F   op=1   │ M  len=6       FIN=1 · 글 · MASK=1 · 6바이트 → 뒤에 키 4바이트
   81 fe 00 c8 ……      1000 0001 │ 1111 1110 + 00 c8
                                  │ M  len=126 → 다음 2바이트가 길이(200)
   89 02 70 31         1000 1001 │ 0000 0010      FIN=1 · ping · MASK=0 · 2바이트 "p1"
   ★ 브라우저 → 서버는 둘째 바이트가 늘 8x/fx(MASK=1) · 서버 → 브라우저는 0x~7x(MASK=0)
```

### (4) ★★ Accept 가 틀리면

```html
<!-- wa32b-33-bad.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>33 bad</title>
<script>
// 서버가 101 은 주되 Sec-WebSocket-Accept 를 틀리게 준다 — 페이지는 무엇을 받나
window.__끝 = () => new Promise(r => {
  const 줄 = [], ws = new WebSocket(`ws://${location.host}/ws?id=b&s=badaccept`);
  ws.onopen = () => 줄.push("open");
  ws.onerror = () => 줄.push("error · readyState=" + ws.readyState);
  ws.onclose = e => { 줄.push(`close · code=${e.code} · wasClean=${e.wasClean} · reason=${JSON.stringify(e.reason)}`); r(줄.join("\n")); };
});
</script>
```

```text
$ python3 wa32b-net.py console wa32b-33-bad.html
error · readyState=3
close · code=1006 · wasClean=false · reason=""
--- 콘솔 ---
network · error · WebSocket connection to 'ws://127.0.0.1:<A>/ws?id=b&s=badaccept' failed: Error during WebSocket handshake: Incorrect 'Sec-WebSocket-Accept' header value
--- 서버 로그 ---
A 틀린 Accept 를 보낸 뒤 브라우저→서버  연결이 닫혔다(0바이트)
(exit 0)
```

- ★★ **`open` 없이 `error`(그때 `readyState=3`) → `close · code=1006 · wasClean=false · reason=""`.** 101 을 받았는데도 **연결이 안 선 것**으로 끝났다.
- ★★ **콘솔이 이유를 말한다** — `Error during WebSocket handshake: Incorrect 'Sec-WebSocket-Accept' header value`. **페이지의 이벤트에는 이유가 없다** — 코드 1006 과 `wasClean=false` 뿐이다.
- **서버 쪽** — 틀린 Accept 를 보낸 뒤 **브라우저는 프레임 하나 없이 연결을 닫았다**(0바이트).

### (5) ★★★ 닫힘 코드 격자 — 선로의 코드 대 페이지의 코드

```html
<!-- wa32b-33-close.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>33 close</title>
<script>
// 닫힘 코드 격자 — 서버가 먼저 닫는 방법 하나씩. 페이지가 받은 CloseEvent 를 선로에 실린 코드와 견준다
const 방법 = [["1000", 1000], ["1001", 1001], ["1008", 1008], ["4000", 4000],
              ["none", null], ["1005", 1005], ["1006", 1006], ["tcp", null]];
const 이름 = { none: "코드 없는 close 프레임", tcp: "close 프레임 없이 TCP 를 끊음" };
const 한칸 = (how, k) => new Promise(r => {
  const ws = new WebSocket(`ws://${location.host}/ws?id=c${k}&s=close-${how}`);
  let 오류 = 0;
  ws.onerror = () => 오류++;
  ws.onclose = e => r({ code: e.code, wasClean: e.wasClean, reason: e.reason, 오류 });
});
window.__끝 = async () => {
  const 줄 = []; let 갈림 = 0;
  for (const [k, [how, 선로]] of 방법.entries()) {
    const x = await 한칸(how, k);
    if (x.code !== 선로) 갈림++;
    const 칸 = [이름[how] ?? `close 프레임 코드 ${how}`, "선로의 코드 " + (선로 ?? "(없음)"),
      "CloseEvent.code " + x.code, "wasClean " + x.wasClean, "reason " + JSON.stringify(x.reason), "error 이벤트 " + x.오류];
    if (칸.length !== 6) throw new Error("칸 수");
    줄.push(칸.join("\t"));
  }
  줄.push(`선로의 코드와 CloseEvent.code 가 다른 칸 = ${갈림} / ${방법.length}`);
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa32b-net.py page wa32b-33-close.html
close 프레임 코드 1000	선로의 코드 1000	CloseEvent.code 1000	wasClean true	reason "bye"	error 이벤트 0
close 프레임 코드 1001	선로의 코드 1001	CloseEvent.code 1001	wasClean true	reason "bye"	error 이벤트 0
close 프레임 코드 1008	선로의 코드 1008	CloseEvent.code 1008	wasClean true	reason "bye"	error 이벤트 0
close 프레임 코드 4000	선로의 코드 4000	CloseEvent.code 4000	wasClean true	reason "bye"	error 이벤트 0
코드 없는 close 프레임	선로의 코드 (없음)	CloseEvent.code 1005	wasClean true	reason ""	error 이벤트 0
close 프레임 코드 1005	선로의 코드 1005	CloseEvent.code 1006	wasClean false	reason ""	error 이벤트 1
close 프레임 코드 1006	선로의 코드 1006	CloseEvent.code 1006	wasClean false	reason ""	error 이벤트 1
close 프레임 없이 TCP 를 끊음	선로의 코드 (없음)	CloseEvent.code 1006	wasClean false	reason ""	error 이벤트 0
선로의 코드와 CloseEvent.code 가 다른 칸 = 3 / 8
--- 서버 로그 ---
A 서버→브라우저  88 05 03 e8 62 79 65   ← FIN=1 opcode=8(close) MASK=0 길이=5
A 브라우저→서버  88 85 <마스킹 키 4바이트> <가려진 본문 5바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=5
A                풀어낸 본문 = close 코드=1000 이유='bye'
A 서버→브라우저  88 05 03 e9 62 79 65   ← FIN=1 opcode=8(close) MASK=0 길이=5
A 브라우저→서버  88 85 <마스킹 키 4바이트> <가려진 본문 5바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=5
A                풀어낸 본문 = close 코드=1001 이유='bye'
A 서버→브라우저  88 05 03 f0 62 79 65   ← FIN=1 opcode=8(close) MASK=0 길이=5
A 브라우저→서버  88 85 <마스킹 키 4바이트> <가려진 본문 5바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=5
A                풀어낸 본문 = close 코드=1008 이유='bye'
A 서버→브라우저  88 05 0f a0 62 79 65   ← FIN=1 opcode=8(close) MASK=0 길이=5
A 브라우저→서버  88 85 <마스킹 키 4바이트> <가려진 본문 5바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=5
A                풀어낸 본문 = close 코드=4000 이유='bye'
A 서버→브라우저  88 00   ← FIN=1 opcode=8(close) MASK=0 길이=0
A 브라우저→서버  88 80 <마스킹 키 4바이트> <가려진 본문 0바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=0
A                풀어낸 본문 = close 코드=(없음) 이유=''
A 서버→브라우저  88 05 03 ed 62 79 65   ← FIN=1 opcode=8(close) MASK=0 길이=5
A 브라우저→서버  88 82 <마스킹 키 4바이트> <가려진 본문 2바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=2
A                풀어낸 본문 = close 코드=1002 이유=''
A 서버→브라우저  88 05 03 ee 62 79 65   ← FIN=1 opcode=8(close) MASK=0 길이=5
A 브라우저→서버  88 82 <마스킹 키 4바이트> <가려진 본문 2바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=2
A                풀어낸 본문 = close 코드=1002 이유=''
A 서버가 close 프레임 없이 TCP 를 끊었다
(exit 0)
```

- ★★★ **선로의 코드와 `CloseEvent.code` 가 다른 칸 3 / 8.**
- ★★ **1000 · 1001 · 1008 · 4000 은 그대로** — `wasClean=true` · `reason="bye"`. 브라우저는 **같은 코드 · 같은 이유로 답했다**(서버 로그).
- ★★ **코드 없는 close(본문 0바이트) → 페이지는 `1005`**, 브라우저의 답도 **본문 0바이트**. **1005 는 「코드가 없었다」를 뜻하는, 페이지 쪽에서 붙인 번호**다.
- ★★★ **TCP 를 그냥 끊으면 → `1006` · `wasClean=false`** — 선로에는 아무 코드도 없었다. **1006 은 브라우저가 만든 코드다.** 그리고 **`error` 이벤트는 0번**이다 — 이 칸에서 끊김을 알린 것은 `close` 뿐이다.
- ★★ **서버가 선로에 1005 · 1006 을 실어 보내면 → 페이지는 `1006` · `wasClean=false` · `error` 1번**, 그리고 **브라우저는 `1002` 로 답했다**(서버 로그). 이 두 번호는 **선로에 실으면 안 되는 번호로 다뤄졌다** — 브라우저가 프로토콜 오류로 보고 연결을 깼다.

```text
   닫힘 코드 — 선로 대 페이지 (이 판 8칸)

   서버가 선로에 실은 것     브라우저의 답       CloseEvent.code   wasClean   error
   close 1000/1001/1008/4000  같은 코드·이유      같은 코드          true       0
   close (코드 없음)          close (코드 없음)   1005 ★            true       0
   close 1005 · 1006          close 1002 ★        1006 ★            false      1
   (TCP 끊음 — 프레임 없음)   —                   1006 ★            false      0
   ★ 1005 · 1006 은 페이지 쪽 번호 — 선로에 실린 적이 없는 것을 말해 준다
```

### (6) ★★ 페이지가 먼저 닫을 때 — `close()` 가 받아 주는 코드

```html
<!-- wa32b-33-codes.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>33 codes</title>
<script>
// 페이지가 먼저 닫는다 — ws.close(코드, 이유) 가 받아 주는 것 · 던지는 것
const 시도 = [[], [1000], [1001], [3000, "앱"], [4999], [2999], [5000], [1000, "가".repeat(41)], [1000, "가".repeat(42)]];
const 한칸 = (args, k) => new Promise(r => {
  const ws = new WebSocket(`ws://${location.host}/ws?id=k${k}&s=client`);
  ws.onopen = () => {
    let 결과;
    try { ws.close(...args); 결과 = "받음"; }
    catch (e) { 결과 = `던짐 ${e.name}`; ws.close(1000, "뒤처리"); }
    ws.onclose = e => r(`${결과}\t→ CloseEvent.code=${e.code} · wasClean=${e.wasClean}`);
  };
});
window.__끝 = async () => {
  const 줄 = [];
  for (const [k, args] of 시도.entries()) {
    const 보임 = args.length === 2 && args[1].length > 5 ? [args[0], `"가"×${args[1].length} (UTF-8 ${new TextEncoder().encode(args[1]).length}바이트)`] : args.map(a => JSON.stringify(a));
    줄.push(`ws.close(${보임.join(", ")})\t` + await 한칸(args, k));
  }
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa32b-net.py page wa32b-33-codes.html | sed -n '1,9p'
ws.close()	받음	→ CloseEvent.code=1005 · wasClean=true
ws.close(1000)	받음	→ CloseEvent.code=1000 · wasClean=true
ws.close(1001)	던짐 InvalidAccessError	→ CloseEvent.code=1000 · wasClean=true
ws.close(3000, "앱")	받음	→ CloseEvent.code=3000 · wasClean=true
ws.close(4999)	받음	→ CloseEvent.code=4999 · wasClean=true
ws.close(2999)	던짐 InvalidAccessError	→ CloseEvent.code=1000 · wasClean=true
ws.close(5000)	던짐 InvalidAccessError	→ CloseEvent.code=1000 · wasClean=true
ws.close(1000, "가"×41 (UTF-8 123바이트))	받음	→ CloseEvent.code=1000 · wasClean=true
ws.close(1000, "가"×42 (UTF-8 126바이트))	던짐 SyntaxError	→ CloseEvent.code=1000 · wasClean=true
(exit 0)
```

- ★★ **`close(1001)` · `close(2999)` · `close(5000)` → `InvalidAccessError` 를 던진다.** 받아 준 것은 **인자 없음 · 1000 · 3000 · 4999** 다 — 이 판에서 페이지가 고를 수 있는 코드는 **1000 과 3000\~4999**(경계 둘을 찍은 것)였다. **1001(떠남) · 1008(정책 위반) 같은 번호는 서버만** 보낼 수 있었다((5)).
- ★ **이유는 UTF-8 123바이트까지** — `"가"×41`(123바이트)은 받고 `"가"×42`(126바이트)는 **`SyntaxError`**. 서버 로그에서 123바이트 이유가 든 close 는 본문 **125바이트**(코드 2 + 이유 123) — 제어 프레임 한 개에 들어가는 길이다.
- **`close()` 인자 없음 → 선로에 코드 없는 close** → 서버가 그대로 되돌려 주자 **페이지는 `1005`**((5)와 같은 칸).
- 던진 줄은 뒤처리로 `close(1000, "뒤처리")` 를 불러 닫았다 — 그래서 `CloseEvent.code=1000`.

### (7) ★★★ 끊김을 감지하는 신호 — 반쯤 열린 연결은 `close` 가 안 온다

**서버가 소켓을 연 채 읽지도 쓰지도 않는다** — 진짜 네트워크 단절(케이블 · NAT)의 흉내다(머리말 제5의 상태).

```html
<!-- wa32b-33-silent.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>33 silent</title>
<script>
// 서버가 소켓을 연 채 입을 닫는다(반쯤 열린 연결의 흉내) — 페이지는 무엇으로 알아채나
const 쉬기 = ms => new Promise(r => setTimeout(r, ms));
window.__끝 = async () => {
  const 줄 = [], 사건 = [];
  const ws = new WebSocket(`ws://${location.host}/ws?id=q&s=silent`);
  ws.onerror = () => 사건.push("error");
  ws.onmessage = e => 사건.push("message " + e.data);
  const 닫힘 = new Promise(r => ws.onclose = e => { 사건.push(`close code=${e.code} wasClean=${e.wasClean}`); r(); });
  await new Promise(r => ws.onopen = r);
  await 쉬기(3000);
  줄.push(`서버가 입을 닫고 3초 — readyState=${ws.readyState} · 그동안 온 이벤트 ${JSON.stringify(사건)}`);
  // 앱이 만든 심장 박동 — 보내고 1초 안에 답이 없으면 끊겼다고 본다
  const 전 = 사건.length;
  ws.send("살아 있나");
  await 쉬기(1000);
  const 답 = 사건.length > 전;
  줄.push(`심장 박동을 보내고 1초 — 답이 왔나=${답} · readyState=${ws.readyState} · bufferedAmount=${ws.bufferedAmount}`);
  if (!답) { ws.close(4000, "박동 없음"); 줄.push(`ws.close(4000) 직후 readyState=${ws.readyState}`); }
  await fetch("/go?id=q");          // 서버가 쌓인 프레임을 읽게 한다
  await 닫힘;
  줄.push("마지막 이벤트 " + JSON.stringify(사건.slice(전)));
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa32b-net.py page wa32b-33-silent.html
서버가 입을 닫고 3초 — readyState=1 · 그동안 온 이벤트 []
심장 박동을 보내고 1초 — 답이 왔나=false · readyState=1 · bufferedAmount=0
ws.close(4000) 직후 readyState=2
마지막 이벤트 ["close code=1006 wasClean=false"]
--- 서버 로그 ---
A 서버가 입을 닫았다(소켓은 연 채)
A /go 를 받고 쌓인 프레임을 읽는다
A 브라우저→서버  81 8d <마스킹 키 4바이트> <가려진 본문 13바이트>   ← FIN=1 opcode=1(텍스트) MASK=1 길이=13
A                풀어낸 본문 = 글 '살아 있나'
A 브라우저→서버  88 8f <마스킹 키 4바이트> <가려진 본문 15바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=15
A                풀어낸 본문 = close 코드=4000 이유='박동 없음'
A 브라우저→서버  1초 동안 프레임 없음
(exit 0)
```

- ★★★ **서버가 입을 닫고 3초 — `readyState=1` · 이벤트 0개.** 페이지는 **아무것도 모른다.** 끊김을 알리는 신호가 `close`(와 `error`)뿐인데 **둘 다 안 왔다.**
- ★★ **브라우저는 그동안 ping 을 한 번도 안 보냈다** — 서버가 나중에 쌓인 프레임을 읽어 보니 **앱이 보낸 `"살아 있나"` 와 close 뿐**이다. **알아채는 것은 앱의 몫**이다.
- ★★ **앱의 심장 박동** — 보내고 1초 안에 답이 없으니 `close(4000, "박동 없음")` 을 불렀다. `readyState` 는 **곧바로 2(닫는 중)**. **그런데 마지막 `CloseEvent` 는 `1006` · `wasClean=false`** — 서버가 close 에 **답하지 않고** TCP 를 끊었기 때문이다. **앱이 4000 으로 닫아도, 상대가 답하지 않으면 페이지가 받는 코드는 1006** 이다.
- ★ `send` 하고 1초 뒤 `bufferedAmount=0` — 작은 메시지는 서버가 안 읽는데도 브라우저 쪽 큐에서 빠졌다(운영체제 버퍼로 넘어간 것으로 읽힌다). **서버가 안 읽어도 `send` 는 막히지 않았다.**

```text
   끊김을 아는 신호 — 이 판에서 페이지가 받은 것

   서버가 close 를 보냄              close(그 코드) · wasClean true
   서버가 TCP 를 끊음                close 1006 · wasClean false
   ★ 서버(또는 선)가 그냥 조용해짐    아무것도 안 옴 — readyState 1 그대로
        → 앱이 박동을 보내고 답을 기다려야 안다
        → 브라우저는 ping 을 안 보냈다(서버 로그 0개)
```

**그래서 재연결 설계는** — ① **`close` 에서** 다시 붙는다(32편과 달리 **브라우저가 대신 안 한다**) ② **앱이 박동(글 메시지)을 보내 반쯤 열린 연결을 잡는다** ③ 다시 붙는 간격은 **지수로 늘리고 지터를 섞는다** — ③은 **설계 권고층**이고 정본은 [`../../../ops-patterns/01-retry-backoff/`](../../../ops-patterns/01-retry-backoff/2-summary.md)다(그쪽의 핵심 측정: **지터 없는 지수 백오프는 동시에 끊긴 클라이언트들을 흩뿌리지 못한다**). **이 편은 백오프를 재지 않았다.**

```text
   재연결 설계 — 이 판이 잰 칸(★)과 설계 권고층

   ★ close 이벤트 ──▶ 앱이 새 WebSocket(재연결은 앱의 일)
   ★ 박동 타임아웃 ──▶ close(4000) → 상대가 답 안 하면 1006 → 재연결
     대기 = min(상한, 기본 × 2^n) × 무작위(0~1)     ← ops-patterns 01 (지수 + 지터)
     다시 열리면 n = 0 · 32편의 Last-Event-ID 같은 「이어 받기」는 앱이 직접(메시지에 번호)
```

### (8) ★ `bufferedAmount` — `send` 가 돌아왔다 ≠ 보냈다

```html
<!-- wa32b-33-buffer.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>33 buffer</title>
<script>
// send() 는 기다리지 않는다 — 큰 메시지를 보낸 직후와 서버가 다 받았다고 답한 뒤의 bufferedAmount
window.__끝 = () => new Promise(r => {
  const 줄 = [], ws = new WebSocket(`ws://${location.host}/ws?id=u&s=buffer`), 크기 = 1 << 20;
  ws.onopen = () => {
    ws.send("a".repeat(크기));
    줄.push(`send(${크기}바이트 글) 가 돌아온 직후 — bufferedAmount === ${크기} : ${ws.bufferedAmount === 크기}`);
  };
  ws.onmessage = e => {
    줄.push(`서버의 답 ${JSON.stringify(e.data)} 를 받은 때 — bufferedAmount = ${ws.bufferedAmount}`);
    ws.close(1000);
  };
  ws.onclose = e => { 줄.push(`close code=${e.code}`); r(줄.join("\n")); };
});
</script>
```

```text
$ python3 wa32b-net.py page wa32b-33-buffer.html
send(1048576바이트 글) 가 돌아온 직후 — bufferedAmount === 1048576 : true
서버의 답 "받음 1048576바이트" 를 받은 때 — bufferedAmount = 0
close code=1000
--- 서버 로그 ---
A 브라우저→서버  01 ff 00 00 00 00 00 01 ff b8 <마스킹 키 4바이트> <가려진 본문 131000바이트>   ← FIN=0 opcode=1(텍스트) MASK=1 길이=131000
A 브라우저→서버  80 fe 02 40 <마스킹 키 4바이트> <가려진 본문 576바이트>   ← FIN=1 opcode=0(이어짐) MASK=1 길이=576
A 한 메시지 = 프레임 9개 · 합 1048576바이트 · 크기 [131000, 576]
A 서버→브라우저  81 17 eb b0 9b ec 9d 8c 20 31 30 34 38 35 37 36 … (모두 25바이트)   ← FIN=1 opcode=1(텍스트) MASK=0 길이=23
A 브라우저→서버  88 82 <마스킹 키 4바이트> <가려진 본문 2바이트>   ← FIN=1 opcode=8(close) MASK=1 길이=2
A                풀어낸 본문 = close 코드=1000 이유=''
A 서버→브라우저  88 02 03 e8   ← FIN=1 opcode=8(close) MASK=0 길이=2
(exit 0)
```

- ★★ **1 MiB 글을 `send` 한 직후 `bufferedAmount === 1048576` 이 `true`** — `send` 는 **큐에 넣고 곧바로 돌아왔다.** 서버가 「받음」이라고 답한 때는 **0**.
- ★ **Chrome 은 1 MiB 한 메시지를 프레임 9개로 쪼갰다** — 첫 프레임 `01 ff …`(FIN=0 · 글) · 가운데는 opcode 0(이어짐) · 마지막 `80 fe 02 40`(FIN=1 · 576바이트). 조각 크기 **131000** 은 이 판의 관찰이다(머리말 「판에 매일 수 있는 칸」). **페이지의 `message` 는 조각을 모른다** — 서버 쪽도 한 메시지로 모아 답했다.

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   const ws = new WebSocket("ws://…" 또는 "wss://…", [하위 프로토콜들])
   ws.readyState    0 CONNECTING · 1 OPEN · 2 CLOSING · 3 CLOSED
   ws.binaryType    "blob"(기본) · "arraybuffer"
   ws.send(글 | ArrayBuffer | 타입 배열 | Blob)      ← 기다리지 않는다 · bufferedAmount 가 는다
   ws.close([코드], [이유])     코드 = 1000 · 3000~4999 (이 판에서 받아 준 것) · 이유 ≤ UTF-8 123바이트
   ws.onopen · onmessage(e.data) · onerror · onclose(e.code · e.wasClean · e.reason)
   ws.protocol · ws.extensions  ← 서버가 101 에 돌려준 것
   ── 페이지에 없는 것 ── ping/pong 을 보내거나 보는 API · 재연결 · 「받았다」 확인
```

### 어디서 헷갈리나

- **`error` 는 이유를 안 준다** — 이유는 콘솔에만 있다((4)). 코드는 `close` 에서 읽는다.
- **1005 · 1006 은 선로에 없던 것**을 말한다((5)) — 로그에 1006 이 찍히면 **「상대가 close 를 안 보냈다」** 로 읽는다.
- **`close(1001)` 은 페이지가 못 부른다**((6)) — 떠날 때 1001 을 보내고 싶으면 서버가 알아서 판단해야 한다.

## 어디서 틀리나

### 1. `onerror` 에서 원인을 읽으려 한다

**이유가 없다**((4)) — 핸드셰이크 실패도 코드 1006 과 `wasClean=false` 뿐이다. 콘솔을 보거나 서버 로그를 본다.

### 2. 「`close` 가 안 왔으니 연결은 살아 있다」

**반쯤 열린 연결은 `close` 가 안 온다**((7)) — 3초 동안 `readyState=1`. 앱이 박동을 보내고 답을 기다려야 안다.

### 3. 「브라우저가 알아서 ping 으로 연결을 지킨다」

**이 판에서 브라우저는 ping 을 한 번도 안 보냈다**((7)). 서버가 보낸 ping 에 **답만** 했다((3)).

### 4. 끊기면 브라우저가 다시 붙는다고 믿는다(SSE 처럼)

**안 붙는다** — WebSocket 은 `close` 로 끝이다. 재연결은 앱 코드이고, 그 간격은 [백오프 + 지터](../../../ops-patterns/01-retry-backoff/2-summary.md)로 흩뿌린다.

### 5. `ws.close(1001)` 로 「페이지를 떠난다」를 알린다

**`InvalidAccessError`** 를 던진다((6)). 페이지는 1000 과 3000\~4999 만 골랐다.

### 6. `send()` 가 돌아왔으니 서버가 받았다고 믿는다

**큐에 넣었을 뿐이다**((8)) — 1 MiB 를 보낸 직후 `bufferedAmount` 가 그대로 1048576 이었다. 「받았다」는 **서버가 답해야** 안다.

### 7. 서버에서 `1006` 을 보내 「비정상 종료」를 알린다

**브라우저가 프로토콜 오류로 보고 1002 로 깼다**((5)). 1005 · 1006 은 선로에 싣지 않는다 — 앱 코드는 4000\~4999 를 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| Accept = base64(SHA-1(키 + GUID)) · GUID 값 | ★ **이 판의 관찰** — 두 구현이 같은 계산 · 같은 값. RFC 원문은 열지 못했다 |
| WebSocket 연결은 mode `"websocket"` 인 fetch 로 시작한다 | **명세**(Fetch — 앞 배치의 사본에서 확인) |
| 브라우저 → 서버 프레임은 MASK=1 · 서버 → 브라우저는 MASK=0 | ★ **이 판의 관찰**(서버는 이 하네스가 그렇게 짰다) |
| 페이지가 ping 을 못 보고 브라우저가 pong 을 답한다 | ★ **이 판의 관찰** |
| 틀린 Accept → `error` · 1006 · 콘솔 문구 | ★ **이 판의 관찰** — 문구는 Chrome 의 것 |
| 코드 없는 close → 1005 · TCP 끊김 → 1006 · 선로의 1005/1006 → 1002 로 답 | ★ **이 판의 관찰** |
| `close()` 가 받는 코드 · 이유 123바이트 | ★ **이 판의 관찰**(경계 둘씩 찍었다) |
| 브라우저가 스스로 ping 을 안 보냈다 | ★ **이 판의 관찰**(3초 동안) |
| 큰 메시지를 131000바이트 조각으로 | ★ **이 판의 관찰** — Chrome 이 고른 값 |
| 재연결 · 백오프 · 지터 | **설계**(ops-patterns 01) — 브라우저가 하지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 양방향 · 잦은 메시지(채팅 · 협업 편집 · 게임) | WebSocket + 앱의 박동 + 백오프 재연결 | 박동 없이 `close` 만 믿기 |
| 서버 → 브라우저 한 방향이고 끊긴 동안의 것을 이어 받아야 | [32번 주제](../32-server-sent-events/2-summary.md) SSE(`Last-Event-ID`) | WebSocket 으로 이어 받기를 새로 짜기 |
| 앱이 연결을 닫을 때 | `close(1000)` · 앱 사유는 `close(4000~4999, 이유)` | `close(1001)`(던진다) |
| 서버가 비정상 종료를 알릴 때 | 1008 · 1011 · 4000번대 | 1005 · 1006(선로에 싣는 번호가 아니다) |
| 보낸 양 조절 | `bufferedAmount` 를 보고 쌓이면 멈춤 | `send` 를 막히는 호출로 믿기 |

## 핵심 문장

1. **WebSocket 은 HTTP 요청으로 시작한다** — `Upgrade: websocket` + 키 → 서버가 **base64(SHA-1(키 + GUID))** 로 답하면 101 뒤로 같은 선이 프레임이 된다. 틀리면 `error` · 1006 이고 **이유는 콘솔에만** 있다.
2. **브라우저가 보낸 프레임은 전부 MASK=1** 이었고, **ping 은 페이지에 안 보이며 브라우저가 몰래 pong 한다.**
3. **1005 · 1006 은 페이지 쪽 번호다** — 선로에 코드가 없거나 close 가 없었다는 뜻. 선로의 코드와 페이지의 코드가 **8칸 중 3칸** 갈렸다.
4. **반쯤 열린 연결은 아무 이벤트도 안 준다** — 끊김을 아는 신호는 `close` 뿐이고, **브라우저는 ping 을 안 보냈다.** 그래서 박동과 재연결은 앱의 일이다.
5. **재연결 간격은 설계 권고층(지수 + 지터)** 이다 — ops-patterns 01 이 정본이고, 이 편은 재지 않았다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 33번)
- [32번 주제](../32-server-sent-events/2-summary.md) — 하네스 (1) · 한 방향 · **브라우저가 다시 붙는** 쪽
- [`../../../ops-patterns/01-retry-backoff/`](../../../ops-patterns/01-retry-backoff/2-summary.md) — **재시도 간격의 정본**(고정 · 지수 · 지터 · 예산). 그쪽은 **얼마나 기다렸다 다시 하나**, 여기는 **언제 다시 해야 하는지를 무엇으로 아나**
- [`../../../../history/web/05-웹플랫폼-API.md`](../../../../history/web/05-웹플랫폼-API.md) §4 「WebSocket: 양방향 영속 연결」 — 연혁(RFC 6455 · IETF 이관). 그쪽은 **왜 들어왔나**, 여기는 **바이트로 무엇이 오가나**
- [Python 06 — 문자열·bytes·유니코드](../../languages/python/syntax/06-strings-bytes-unicode/2-summary.md) — 하네스가 프레임을 푸는 `bytes`·`decode` 쪽 문법
- [28번 주제](../28-cors-simple-and-preflight/2-summary.md) — 요청에 실린 `Origin`. WebSocket 에는 CORS 가 없고 **출처 확인은 서버가 `Origin` 을 보고 한다**(이 서버는 안 봤다)

## 용어 풀이

- **핸드셰이크** — `Upgrade` 요청 → `101 Switching Protocols`. 그 뒤로 같은 TCP 연결이 WebSocket 이 된다.
- **`Sec-WebSocket-Key` / `Sec-WebSocket-Accept`** — 브라우저가 보낸 16바이트 난수의 base64 / 서버가 그것에 GUID 를 붙여 SHA-1 한 뒤 base64 한 값.
- **프레임** — WebSocket 의 봉투. 머리(FIN · opcode · MASK · 길이) + (마스킹 키) + 본문.
- **opcode** — 0 이어짐 · 1 글 · 2 바이너리 · 8 close · 9 ping · 10 pong.
- **마스킹** — 4바이트 키로 본문을 XOR 한 것. 이 판에서는 브라우저 → 서버 쪽에만 있었다.
- **close 프레임 · 닫힘 코드** — 코드 2바이트 + 이유. 받은 쪽이 같은 코드로 답하면 `wasClean=true`.
- **1005 · 1006** — 페이지가 붙이는 번호. 코드 없는 close / close 없이 끊김.
- **반쯤 열린 연결** — 한쪽이 사라졌는데 다른 쪽은 모르는 연결. 이 편은 침묵 서버로 흉내 냈다.
- **선로 덤프** — 서버가 오가는 바이트를 16진으로 적은 로그. 이 편의 본체.

## 더 들어가면

- ★★ **명세 원문 대조** — WHATWG WebSockets(`close()` 의 코드 검사 · 이유 길이 · `CloseEvent` 값)와 RFC 6455(Accept 계산 · 마스킹 · 예약 코드 1005/1006)를 열어 이 편의 관찰을 **명세 문장과 맞대는 일**이 남았다.
- **`permessage-deflate`** — 서버가 받으면 프레임의 RSV1 비트와 본문이 달라진다. 던지지 않았다.
- **`wss://` · 하위 프로토콜(`Sec-WebSocket-Protocol`)** — 던지지 않았다.
- **`WebSocketStream`**(스트림 기반 API — 역압을 프라미스로) — 이 판의 Chrome 에서 던지지 않았다.
