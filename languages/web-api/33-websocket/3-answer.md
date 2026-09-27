# web-api/33 — WebSocket: 핸드셰이크·프레임·닫힘 코드와 재연결 설계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 서버는 같은 기계의 로컬 서버(A)이고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> ★ **명세 원문(WHATWG WebSockets · RFC 6455)은 이 판에서 열지 못했다** — 「왜 그런가」는 관찰에서 읽은 것이고, 명세대로인지 판정하지 않는다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 가린 칸 |
|---|---|
| 요청 헤더 · 101 · 프레임 머리 · 닫힘 격자 · `close()` 표 · 침묵 서버 · 콘솔 문구 | ★ **가린 칸** — `Sec-WebSocket-Key`·Accept·마스킹 키(판마다 무작위 — 길이만) · `User-Agent`·`Accept-Language` |
| 캡처를 세 판 돌려 **한 글자도 같았다** | ★ **판에 매일 수 있는 칸** — 큰 메시지의 조각 크기 131000 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 평범한 `GET` — `Upgrade: websocket` · 버전 13 · 24자 키 · 압축 제안

**출력**

```text
$ python3 wa32b-net.py page wa32b-33-frames.html | sed -n '/^A 받은 요청/,/^    (서버가 계산한/p'
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
(exit 0)
```

**왜 그런가**

- **`GET /ws?… HTTP/1.1` · `Connection: Upgrade` · `Upgrade: websocket` · `Sec-WebSocket-Version: 13`** — HTTP 요청으로 시작한다. `Origin` 도 실린다.
- **`Sec-WebSocket-Key` 는 24자, 풀면 16바이트.** 그 밖의 `Sec-` 헤더는 **`Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits`** — 압축 제안이다. 서버가 101 에 안 돌려주자 `extensions` 는 `""` 였다(2-summary 의 (3)).
- 101 에는 **`Upgrade` · `Connection` · `Sec-WebSocket-Accept`** 셋 — Accept 가 맞는지는 `True` 로 찍었다.

### 2. `open` 없이 `error` → `1006` · `wasClean=false` — 이유는 콘솔에만

**출력**

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

**왜 그런가**

- **`error · readyState=3` → `close · code=1006 · wasClean=false · reason=""`.** 101 을 받고도 연결이 안 섰다.
- **콘솔만 이유를 말한다** — `Incorrect 'Sec-WebSocket-Accept' header value`. 페이지의 이벤트에는 이유가 없다.

### 3. `message` 는 둘 — 서버가 받은 첫 프레임은 pong · `"안녕"` 은 `81 86`

**출력**

```text
$ python3 wa32b-net.py page wa32b-33-frames.html | sed -n '/서버→브라우저  89/,$p'
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

**왜 그런가**

- **페이지의 `message` 는 글 하나 · 바이너리 하나**(2-summary 의 (3) 첫 블록) — ping 은 안 보였다.
- **서버가 받은 첫 프레임은 `8a 82` — pong**, 본문 `70 31`(`"p1"`) — 브라우저가 앱 몰래 답했다.
- **`"안녕"` → `81 86`** — `81` = FIN 1 · 글(1), `86` = **MASK 1** · 길이 6(UTF-8 바이트).
- **200바이트 → `81 fe 00 c8`** — 길이 칸 126(`7e` + MASK 비트 = `fe`) 뒤 2바이트 `00 c8` = 200.
- 브라우저가 보낸 프레임은 **둘째 바이트가 전부 `8x`/`fx`(MASK=1)**, 서버가 보낸 것은 **`0x`\~`1x`(MASK=0)**.

### 4. 넷은 그대로 · 코드 없음 → 1005 · 선로의 1005/1006 → 1006 과 답 1002 · TCP 끊음 → 1006

**출력**

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

**왜 그런가**

- **1000 · 1001 · 1008 · 4000 → 같은 코드 · `wasClean=true` · `reason="bye"`**, 브라우저는 같은 코드로 답했다.
- **코드 없는 close → 페이지는 `1005`** · 답도 본문 0바이트.
- ★★ **선로에 1005 · 1006 → 페이지는 `1006` · `wasClean=false` · `error` 1번 · 브라우저의 답은 `1002`** — 답 코드가 달라진 줄은 이 둘이다.
- ★★ **TCP 를 그냥 끊음 → `1006` · `wasClean=false` · `error` 0번** — 알린 것은 `close` 뿐이다.
- **선로의 코드와 `CloseEvent.code` 가 다른 칸 3 / 8.**

### 5. 인자 없음 · 1000 · 3000 · 4999 · 123바이트 이유는 받고, 1001 · 2999 · 5000 · 126바이트는 던진다

**출력**

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

**왜 그런가**

- **`1001` · `2999` · `5000` → `InvalidAccessError`**, **`"가"×42`(126바이트) → `SyntaxError`**. 받아 준 코드는 **1000 과 3000\~4999**(찍은 경계 안)였다.
- **`close()` → `1005`** — 코드 없는 close 가 선로에 가고 서버가 되돌려 준 결과(A4 의 코드 없음과 같은 칸).
- 던진 줄의 `CloseEvent.code=1000` 은 **뒤처리로 부른 `close(1000, "뒤처리")`** 의 것이다.

### 6. ① `1` · 이벤트 0 ② 답 없음 · `1` · `0` — 마지막은 `1006` · 브라우저의 ping 0개

**출력**

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

**왜 그런가**

- ★★★ **① `readyState=1` · 이벤트 `[]`** — 서버가 조용해도 페이지는 모른다.
- **② 답이 왔나 `false` · `readyState=1` · `bufferedAmount=0`** — `send` 는 막히지 않았다.
- ★★ **`close(4000)` 직후 `readyState=2`, 마지막 `CloseEvent` 는 `1006` · `wasClean=false`** — 서버가 close 에 **답하지 않고** 끊었기 때문이다. 앱이 고른 4000 은 페이지에 안 돌아왔다.
- ★★ **서버가 나중에 읽은 쌓인 프레임 — `"살아 있나"`(글)와 close(4000) 뿐.** 브라우저가 스스로 보낸 **ping 은 0개**다.

### 7. 키를 글자 그대로 + GUID → SHA-1 → base64

**출력**

```text
$ python3 wa32b-net.py accept d2EzMmItMzMta2V5LTE2Yg==
Sec-WebSocket-Key    = d2EzMmItMzMta2V5LTE2Yg==
키 + GUID            = d2EzMmItMzMta2V5LTE2Yg==258EAFA5-E914-47DA-95CA-C5AB0DC85B11
SHA-1 (16진)         = 7d8a36bb9314b94f55823abbbfd61af8e1d92ccc
Sec-WebSocket-Accept = fYo2u5MUuU9Vgjq7v9Ya+OHZLMw=
(exit 0)
```

```text
$ printf '%s' 'd2EzMmItMzMta2V5LTE2Yg==258EAFA5-E914-47DA-95CA-C5AB0DC85B11' | openssl dgst -sha1 -binary | base64
fYo2u5MUuU9Vgjq7v9Ya+OHZLMw=
(exit 0)
```

```text
$ grep -n '258EAFA5' /usr/lib/python3/dist-packages/websocket/_handshake.py
191:    value = f"{key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11".encode("utf-8")
(exit 0)
```

**왜 그런가**

- **키는 base64 글자 그대로** 이어 붙인다(`d2Ez…Yg==258EAFA5…`) — 풀지 않는다. SHA-1 20바이트를 base64 하면 **28글자**(`fYo2u5MUuU9Vgjq7v9Ya+OHZLMw=`) — 하네스와 `openssl` 이 같은 값을 냈다.
- **확인한 것** — **이 머신의 다른 구현**(`websocket-client` 의 `_handshake.py` 191행)이 **같은 GUID** 를 쓴다. **확인하지 못한 것** — **RFC 6455 원문의 그 문장**. 두 구현이 같다는 것은 **관찰**이지 명세의 인용이 아니다.

### 8. 선로에 실린 적 없다 — 서버가 실으면 브라우저가 1002 로 깼다

- **1005** — 선로의 close 에 **코드가 없었다**(A4 · A5). **1006** — **close 프레임 없이** 끊겼다(A4 · A6 · A2). 둘 다 **페이지가 붙인 번호**다.
- **서버가 선로에 1006(또는 1005)을 실으면** — 브라우저가 **`1002` 로 답하며 연결을 깼고**, 페이지는 `1006` · `wasClean=false` · `error` 1번을 받았다(A4). **선로에 싣는 번호로 다뤄지지 않았다** — 앱의 사유는 4000\~4999 를 쓴다.

### 9. 그대로 1048576 — 프레임 9개, 페이지는 모른다

**출력**

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

**왜 그런가**

- **`send` 가 돌아온 직후 `bufferedAmount === 1048576` 이 `true`**, 서버가 「받음」이라고 답한 때 **0**. `send` 는 큐에 넣고 돌아올 뿐이다.
- **선로에서는 9개 프레임** — 첫 `01 ff …`(FIN=0 · 글 · 131000바이트) · 가운데 opcode 0(이어짐) · 마지막 `80 fe 02 40`(FIN=1 · 576바이트). **페이지의 API 에는 조각이 없다** — 받는 쪽도 한 `message` 로 모은다. 조각 크기는 이 판의 관찰이다.

### 10. 신호는 `close` 뿐 — 박동은 앱이, 간격은 ops-patterns 01

- **끊김을 안 신호는 `close`(와 가끔 `error`)뿐**이었다(A4). **반쯤 열린 연결은 아무것도 안 줬다**(A6) — **앱이 박동(메시지)을 보내고 답이 없으면 닫고 다시 붙는다.** 브라우저는 ping 을 안 보냈다.
- **다시 붙는 간격은 ops-patterns 01 이 정본**이다 — 지수로 늘리고 **지터로 흩뿌린다**(동시에 끊긴 클라이언트들이 같은 순간에 몰리지 않게). 이 편은 백오프를 **재지 않았다.**
- **SSE 와 비교해 앱이 더 해야 하는 일** — ① **재연결 자체**(SSE 는 브라우저가 한다 — 32편 (2)) ② **이어 받기**(SSE 의 `Last-Event-ID` 같은 책갈피가 없다 — 메시지에 번호를 넣고 다시 붙을 때 앱이 보낸다). ③ 반쯤 열린 연결을 잡는 **박동**도 앱의 몫이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · Python 3 표준 라이브러리 `http.server`(핸드셰이크 뒤 소켓을 넘겨받아 프레임을 직접 읽고 쓴다) · OpenSSL(`openssl dgst -sha1`). **엔진은 Chrome 하나다.**

★ **하네스** — [32번 주제](../32-server-sent-events/2-summary.md)의 (1)(`wa32b-net.py` 의 `/ws`).

```sh
# wa32b-33-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa32b-net.py accept d2EzMmItMzMta2V5LTE2Yg==
python3 wa32b-net.py page wa32b-33-frames.html
python3 wa32b-net.py console wa32b-33-bad.html
python3 wa32b-net.py page wa32b-33-close.html
python3 wa32b-net.py page wa32b-33-codes.html
python3 wa32b-net.py page wa32b-33-silent.html
python3 wa32b-net.py page wa32b-33-buffer.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| Accept 계산(고정 키) · `openssl` · GUID | 캡처 3판 | 동작 방식 (2) · A7 |
| 핸드셰이크 · 프레임 | 캡처 3판 | 동작 방식 (3) · A1 · A3 |
| 틀린 Accept | 캡처 3판 | 동작 방식 (4) · A2 |
| 닫힘 코드 격자 | 캡처 3판 | 동작 방식 (5) · A4 · A8 |
| `close()` 인자 | 캡처 3판 | 동작 방식 (6) · A5 |
| 침묵 서버 · 박동 | 캡처 3판 | 동작 방식 (7) · A6 · A10 |
| `bufferedAmount` · 조각 | 캡처 3판 | 동작 방식 (8) · A9 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 선로의 1005/1006 에 대한 답 | 1002 | 브라우저가 고른 처리 |
| 큰 메시지 조각 | 131000바이트 | Chrome 이 고른 값 |
| 브라우저가 스스로 ping 을 보내나 | 3초 동안 0개 | 판이 오르면 달라질 수 있다 |
| 콘솔 문구 | `Incorrect 'Sec-WebSocket-Accept' header value` | Chrome 의 문구 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② `wss://` · `permessage-deflate` 수락 · 하위 프로토콜. ③ 백오프 재연결(설계 권고층 — ops-patterns 01). ④ 명세 원문 대조.
