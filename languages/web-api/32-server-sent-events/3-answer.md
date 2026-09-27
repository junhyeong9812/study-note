# web-api/32 — 서버 보내기 이벤트: `EventSource`·자동 재연결·`Last-Event-ID` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 서버는 같은 기계의 로컬 서버(A)이고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> ★ **명세 원문(HTML 의 server-sent events 절)은 이 판에서 열지 못했다** — 아래 「왜 그런가」는 전부 **관찰에서 읽은 것**이고, 명세대로인지 판정하지 않는다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 격자 12칸 · 「다시 붙나」 8줄 · 형식 표 · 콘솔 문구 | ★ **판에 매일 수 있는 칸** — 「한 번 끊음」의 곧바로 온 두 번째 연결(아래 층의 재시도로 읽힌다) |
| 캡처를 세 판 돌려 **한 글자도 같았다** · 간격은 ms 가 아니라 참/거짓 | **못 잰 것** — 기본 재연결 간격의 값 · 교차 출처 · 연결 수 한도 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 헤더는 셋 다 `4` — 이어 준 것은 서버다

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-32-grid.html | sed -n '1p;4p;7p;13,14p'
id:있음	retry:200	이어 보냄	받음 [1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 []	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
id:있음	retry:없음	이어 보냄	받음 [1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 []	간격≥1000ms [true,true]	readyState 0→1→0→1→0→2
id:없음	retry:200	이어 보냄	받음 [1,2,3,4,1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","없음","없음"]	유실 []	중복 [1,2,3,4]	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
유실이나 중복이 있는 칸 = 10 / 12
retry: 200 의 유무로 「간격≥1000ms」 가 갈린 쌍 = 6 / 6
(exit 0)
```

**왜 그런가**

- **(가) `id:` + 이어 보냄 → `[1…10]` · 헤더 `["없음","4","10"]` · 유실 0 · 중복 0.** 브라우저가 마지막으로 받은 `id` 4 를 들고 왔고, 서버가 5 부터 보냈다.
- **(나) `id:` 없음 → 헤더가 세 번 다 `없음`** — 이어 줄 근거가 없어 서버가 1 부터 보냈고 **1\~4 가 중복**됐다(위 블록의 셋째 줄).
- **(다) `id:` + 현재부터 → 헤더는 (가)와 똑같이 `4`** 인데 **5·6 이 유실**됐다(전체 격자 — 2-summary 의 (2)). 헤더는 같고 **서버의 선택만** 달랐다.
- 마지막 두 줄 — **유실이나 중복이 있는 칸 10 / 12**, `retry:` 로 간격이 갈린 쌍 6 / 6.

### 2. `retry: 200` 은 `false`, 없으면 `true` — 번호는 그대로

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-32-grid.html | sed -n '1p;4p;7p;13,14p'
id:있음	retry:200	이어 보냄	받음 [1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 []	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
id:있음	retry:없음	이어 보냄	받음 [1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 []	간격≥1000ms [true,true]	readyState 0→1→0→1→0→2
id:없음	retry:200	이어 보냄	받음 [1,2,3,4,1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","없음","없음"]	유실 []	중복 [1,2,3,4]	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
유실이나 중복이 있는 칸 = 10 / 12
retry: 200 의 유무로 「간격≥1000ms」 가 갈린 쌍 = 6 / 6
(exit 0)
```

**왜 그런가**

- 첫 줄(`retry:200`)은 **`간격≥1000ms [false,false]`**, 둘째 줄(`retry:없음`)은 **`[true,true]`** — 나머지 칸(받은 번호 · 헤더 · 유실 · 중복)은 **한 글자도 같다.**
- **`retry:` 는 재연결 간격만 바꿨다.** 기본 간격이 정확히 몇 ms 인지는 재지 않았다(1000ms 이상까지).

### 3. 다시 붙은 것은 「열렸다가 끊김」과 네트워크 오류 — 204 · 500 · `text/plain` 은 닫혔다

**출력**

```text
$ python3 wa32b-net.py console wa32b-32-stop.html
200 text/event-stream — 하나 보내고 끊음	서버가 받은 연결 2	open 1번	받은 data ["1"]	readyState 0→1→0→2	간격≥1000ms [false]
200 text/event-stream; charset=utf-8	서버가 받은 연결 2	open 1번	받은 data ["1"]	readyState 0→1→0→2	간격≥1000ms [true]
204 No Content	서버가 받은 연결 1	open 0번	받은 data []	readyState 0→2	간격≥1000ms []
500	서버가 받은 연결 1	open 0번	받은 data []	readyState 0→2	간격≥1000ms []
200 text/plain	서버가 받은 연결 1	open 0번	받은 data []	readyState 0→2	간격≥1000ms []
헤더 없이 연결을 끊음 — 한 번	서버가 받은 연결 2	open 0번	받은 data []	readyState 0→2	간격≥1000ms [false]
헤더 없이 연결을 끊음 — 두 번 연달아	서버가 받은 연결 3	open 0번	받은 data []	readyState 0→0→2	간격≥1000ms [false,true]
헤더 없이 연결을 끊음 — 세 번 연달아	서버가 받은 연결 4	open 0번	받은 data []	readyState 0→0→0→2	간격≥1000ms [false,true,true]
다시 붙은 모양 = 5 / 8
--- 콘솔 ---
network · error · Failed to load resource: the server responded with a status of 500 (Internal Server Error)
javascript · error · EventSource's response has a MIME type ("text/plain") that is not "text/event-stream". Aborting the connection.
network · error · Failed to load resource: net::ERR_EMPTY_RESPONSE
network · error · Failed to load resource: net::ERR_EMPTY_RESPONSE
network · error · Failed to load resource: net::ERR_EMPTY_RESPONSE
--- 서버 로그 ---
(받은 요청 없음)
(exit 0)
```

**왜 그런가**

- **다시 붙은 모양 5 / 8** — `text/event-stream`(과 `; charset=utf-8`)을 열었다 끊은 둘, 헤더 없이 끊은 셋.
- **204 · 500 · `text/plain` → 연결 1 · `open` 0번 · `0→2`.** `text/plain` 은 콘솔이 이유를 말했다(`MIME type ("text/plain") that is not "text/event-stream". Aborting the connection.`).
- ★ **「한 번 끊음」은 연결 2 인데 `error` 가 없다**(`0→2` 의 2 는 마지막 204 의 것). 간격도 `[false]` — 재연결 간격을 안 기다렸다. **두 번 · 세 번이면** 첫 간격만 `false` 이고 그 뒤로 `error` 와 `true` 가 붙는다 — A8.

### 4. `message` 넷 · `tick` 하나 — `id: 7` 은 책갈피만, 마지막 블록은 사라짐

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-32-format.html
onmessage	type=message	data="첫째"	lastEventId=""
tick 리스너	type=tick	data="이름 붙은 것"	lastEventId=""
onmessage	type=message	data="한 줄\n두 줄"	lastEventId=""
onmessage	type=message	data="앞 공백 없음"	lastEventId="7"
onmessage	type=message	data=" 앞 공백 둘"	lastEventId="7"
(exit 0)
```

**왜 그런가**

- **`event: tick` → `tick` 리스너만**(`type=tick`), 이름 없는 블록 → `onmessage`.
- **`data:` 두 줄 → `"한 줄\n두 줄"`** 하나.
- **`id: 7` 블록은 이벤트를 안 냈지만** 그 뒤 `lastEventId` 가 `"7"` 이 됐다.
- **콜론 뒤 공백은 하나만 떼였다**(`" 앞 공백 둘"`).
- ★★ **빈 줄 없이 끝난 `id: 8` 블록은 아예 안 왔다** — 블록은 빈 줄로 끝나야 한다.
- 주석 줄은 아무것도 안 냈다.

### 5. `0→1→0→1→0→2`

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-32-grid.html | sed -n '1p;4p;7p;13,14p'
id:있음	retry:200	이어 보냄	받음 [1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 []	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
id:있음	retry:없음	이어 보냄	받음 [1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 []	간격≥1000ms [true,true]	readyState 0→1→0→1→0→2
id:없음	retry:200	이어 보냄	받음 [1,2,3,4,1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","없음","없음"]	유실 []	중복 [1,2,3,4]	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
유실이나 중복이 있는 칸 = 10 / 12
retry: 200 의 유무로 「간격≥1000ms」 가 갈린 쌍 = 6 / 6
(exit 0)
```

**왜 그런가**

- 줄마다 마지막 칸 **`readyState 0→1→0→1→0→2`** — 연결 중 → 열림 → **끊겨 다시 연결 중(0)** → 열림 → 다시 0 → 204 로 **닫힘(2)**.
- ★ **`error` 는 두 번 다 `0` 에서 났고, 닫힌 것은 세 번째 `error` 뿐이다** — `onerror` 는 「끝났다」가 아니다.

### 6. 서버가 「현재부터」를 골랐다

- **헤더(`4`)는 제대로 왔다.** 잃게 한 것은 **서버가 그 헤더를 무시하고 지금 시점부터 보낸 것**이다 — 끊긴 동안 지나간 5·6 은 어디에도 없다.
- 그래서 **`id:` 는 필요조건일 뿐**이다. 유실 0 을 만든 칸은 **`id:` + 서버가 `id` 로 지난 이벤트를 다시 찾아 이어 보냄** 둘이 다 있을 때뿐이었다(12칸 중 2칸). 서버가 지난 이벤트를 보관하지 않으면 이어 줄 수 없다 — **그건 서버 설계의 몫**이다.

### 7. `id:` 를 안 붙인 칸 — 헤더가 끝까지 없었다

- **`id:` 없는 여섯 칸 전부 헤더가 `["없음","없음","없음"]`** 이었다. 브라우저에게 책갈피가 없으니 보낼 것도 없다.
- 그때 「이어 보냄」 서버의 최선은 **처음부터**였다 — 그래서 **1\~4 가 중복**됐다. 헤더 없이 이으려면 서버가 **다른 방법으로**(질의 문자열 · 세션) 위치를 알아야 한다.

### 8. 서버의 연결 수와 페이지의 `error` 가 갈렸다 — 누가 만들었는지는 주장하지 않는다

**출력**

```text
$ python3 wa32b-net.py console wa32b-32-stop.html | sed -n '1,9p'
200 text/event-stream — 하나 보내고 끊음	서버가 받은 연결 2	open 1번	받은 data ["1"]	readyState 0→1→0→2	간격≥1000ms [false]
200 text/event-stream; charset=utf-8	서버가 받은 연결 2	open 1번	받은 data ["1"]	readyState 0→1→0→2	간격≥1000ms [true]
204 No Content	서버가 받은 연결 1	open 0번	받은 data []	readyState 0→2	간격≥1000ms []
500	서버가 받은 연결 1	open 0번	받은 data []	readyState 0→2	간격≥1000ms []
200 text/plain	서버가 받은 연결 1	open 0번	받은 data []	readyState 0→2	간격≥1000ms []
헤더 없이 연결을 끊음 — 한 번	서버가 받은 연결 2	open 0번	받은 data []	readyState 0→2	간격≥1000ms [false]
헤더 없이 연결을 끊음 — 두 번 연달아	서버가 받은 연결 3	open 0번	받은 data []	readyState 0→0→2	간격≥1000ms [false,true]
헤더 없이 연결을 끊음 — 세 번 연달아	서버가 받은 연결 4	open 0번	받은 data []	readyState 0→0→0→2	간격≥1000ms [false,true,true]
다시 붙은 모양 = 5 / 8
(exit 0)
```

**왜 그런가**

- **「한 번 끊음」 — 서버는 연결 2 를 받았는데 페이지의 `error` 는 0 번**(`0→2` 의 `error` 는 마지막 204 의 것), 간격은 `[false]`.
- **같은 질문(「다시 붙었나」)을 두 창에 물었더니 답이 갈렸다**(제5의 상태). 서버 창은 「왔다」를, 페이지 창은 「안 끊겼다」를 말한다.
- **이 편은 누가 그 두 번째 연결을 만들었는지 주장하지 않는다** — `error` 도 재연결 간격도 없었으니 **`EventSource` 의 재연결로는 안 읽힌다**는 데까지다. 두 번 · 세 번 연달아 끊으면 두 번째부터는 `error` 와 `true` 가 붙어 `EventSource` 의 재연결 모양이 된다.

### 9. 멈춘 것은 204 · 500 · 앱의 `close()` — 서버가 닫는 것은 멈춤이 아니다

- **서버가 연결을 닫기 → 다시 붙는다**(A3). **204 → 멈춘다** · **500 → 멈춘다**(A3). **`es.close()` → 앱이 멈춘다**(형태 절).
- ★ **`onerror` 에서 새 `EventSource` 를 만들면** — 그때 `readyState` 는 대개 **0**(다시 붙는 중)이다(A5). 브라우저도 붙는 중이라 **연결이 둘**이 된다. **`readyState === 2` 일 때만** 앱이 새로 만든다.

### 10. 다른 주제와 잇기

- **26편 스트리밍으로 받으면 앱이 직접** — ① **블록을 파싱**(빈 줄 경계 · `data:` 잇기 · 마지막 미완성 블록 버리기 — A4 가 브라우저가 대신 한 일) ② **끊기면 다시 요청하면서 마지막 `id` 를 싣기**(`Last-Event-ID` 를 직접 헤더로). 대신 메서드·헤더·본문을 마음대로 고를 수 있다.
- **댈 수 있는 것** — **방향**(서버 → 브라우저 한 방향이면 된다)과 **재연결을 누가 하나**(SSE 는 브라우저가 한다 · WebSocket 은 앱이 해야 한다 — 33편). **댈 수 없는 것** — **「더 가볍다」·「더 빠르다」** — 이 편은 비용을 **재지 않았다.**

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · Python 3 표준 라이브러리 `http.server`(서버 A·B). **엔진은 Chrome 하나다.**

★ **하네스** — 2-summary 의 (1)(`wa32b-net.py` — 24편 (1)의 Chrome·CDP 부분을 `import` 하고 서버만 새로). 격자는 페이지가 칸마다 `EventSource` 하나를 만들고, 끝나면 `/seen` 으로 **서버에게 물어** 헤더와 시각을 받는다.

```sh
# wa32b-32-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서(서버 A·B 와 Chrome 을 하네스가 띄운다)
python3 wa32b-net.py quiet wa32b-32-grid.html
python3 wa32b-net.py console wa32b-32-stop.html
python3 wa32b-net.py quiet wa32b-32-format.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 재연결 · 유실 격자 12칸 | 캡처 3판 | 동작 방식 (2) · A1 · A2 · A5 · A6 · A7 |
| 「다시 붙나」 8줄 + 콘솔 | 캡처 3판 | 동작 방식 (3) · A3 · A8 · A9 |
| 형식 | 캡처 3판 | 동작 방식 (4) · A4 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 「한 번 끊음」의 곧바로 온 두 번째 연결 | `error` 없음 · 간격 `false` | 아래 층의 재시도로 읽힌다 — 판·네트워크 스택에 매인다 |
| 기본 재연결 간격 | 1000ms 이상 | 값은 재지 않았다 |
| 콘솔 문구 | `MIME type … Aborting the connection.` | Chrome 의 문구다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② 교차 출처 · `withCredentials`. ③ 명세 원문 대조.
