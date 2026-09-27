# web-api/34 — `navigator.sendBeacon` 과 이탈 시점 전송: `fetch` 의 `keepalive` 와의 관계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 서버는 같은 기계의 로컬 서버(A·B)이고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 keepalive · fetch group terminated · 64 kibibytes 한도 · 본문 추출(앞 배치의 사본)로 접지했다. **Beacon 명세와 HTML 의 page dismissal 문장은 열지 못했다.**\
> **엔진은 Chrome 하나 · 서버는 localhost 다** — **이식성과 먼 서버의 결과를 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 격자 40칸(5판) · 동기 결과 · 64KiB · `Content-Type` · 8 MiB | ★ **판에 매일 수 있는 칸** — 「닿았다」 전부(localhost) |
| 판 안 5판 · 캡처 세 판이 **한 글자도 같았다** · 판마다 갈린 칸 0 / 40 | **못 잰 것** — 먼 서버 · 모바일 · 사용자의 창 닫기 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 전부 닿는다 — 탭 닫기에서 보통 `fetch` 만 연결이 끊긴다

**출력**

```text
$ python3 wa32b-net.py leave wa32b-34-grid.html 5 | sed -n '1,24p'
떠날 때 한 번 보낸 요청 — 서버에 닿은 판 / 5판 · (닿은 판 중 응답 때 연결이 살아 있던 판)
방법	자리	링크로 떠나기	탭 닫기(Page.close)
fetch	visibilitychange	5/5 (살아 5/5)	5/5 (살아 0/5)
fetch	pagehide	5/5 (살아 5/5)	5/5 (살아 0/5)
fetch	beforeunload	5/5 (살아 5/5)	5/5 (살아 0/5)
fetch	unload	5/5 (살아 0/5)	5/5 (살아 0/5)
keepalive	visibilitychange	5/5 (살아 5/5)	5/5 (살아 5/5)
keepalive	pagehide	5/5 (살아 5/5)	5/5 (살아 5/5)
keepalive	beforeunload	5/5 (살아 5/5)	5/5 (살아 5/5)
keepalive	unload	5/5 (살아 5/5)	5/5 (살아 5/5)
beacon	visibilitychange	5/5 (살아 5/5)	5/5 (살아 5/5)
beacon	pagehide	5/5 (살아 5/5)	5/5 (살아 5/5)
beacon	beforeunload	5/5 (살아 5/5)	5/5 (살아 5/5)
beacon	unload	5/5 (살아 5/5)	5/5 (살아 5/5)
img	visibilitychange	5/5 (살아 5/5)	5/5 (살아 5/5)
img	pagehide	5/5 (살아 5/5)	5/5 (살아 5/5)
img	beforeunload	5/5 (살아 5/5)	5/5 (살아 5/5)
img	unload	5/5 (살아 5/5)	5/5 (살아 5/5)
xhr	visibilitychange	5/5	0/5
xhr	pagehide	5/5	0/5
xhr	beforeunload	0/5	0/5
xhr	unload	0/5	0/5
한 판이라도 서버에 안 닿은 칸 = 6 / 40
판마다 갈린 칸(0 < 닿은 판 < 5) = 0 / 40
(exit 0)
```

**왜 그런가**

- **(가) 보통 `fetch` · `pagehide`** — 링크 `5/5 (살아 5/5)` · 탭 닫기 **`5/5 (살아 0/5)`**: **닿았는데 응답 전에 끊겼다.**
- **(나) `keepalive` · (다) `sendBeacon`** — 두 방식 모두 **`5/5 (살아 5/5)`**.
- **`unload` 에서 부른 (가)** — **링크로 떠나도 `살아 0/5`** · 탭 닫기도 `0/5`.
- 마지막 두 줄 — **안 닿은 칸 6 / 40(전부 동기 XHR)** · 판마다 갈린 칸 **0 / 40**.

### 2. 링크의 vis · pagehide 두 칸만 돌아오고 닿는다 — 나머지 여섯 칸은 `NetworkError`

**출력**

```text
$ python3 wa32b-net.py leave wa32b-34-grid.html 5 | sed -n '/^--- 부른 자리/,$p'
--- 부른 자리에서 페이지가 적은 동기 결과(첫 판) ---
beacon	visibilitychange	sendBeacon → true	sendBeacon → true
beacon	pagehide	sendBeacon → true	sendBeacon → true
beacon	beforeunload	sendBeacon → true	sendBeacon → true
beacon	unload	sendBeacon → true	sendBeacon → true
xhr	visibilitychange	동기 XHR status 204	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
xhr	pagehide	동기 XHR status 204	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
xhr	beforeunload	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
xhr	unload	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」	던짐 NetworkError 「Failed to execute 'send' on 'XMLHttpRequest': Failed to load '<URL>': Synchronous XHR in page dismissal. See https://www.chromestatus.com/feature/4664843055398912 for more details.」
(exit 0)
```

**왜 그런가**

- **링크로 떠날 때 `visibilitychange` · `pagehide` → `동기 XHR status 204`**, 서버에도 닿았다(A1 표의 `xhr` 줄 `5/5`).
- **그 밖의 여섯 칸 → `NetworkError` 「… `Synchronous XHR in page dismissal.` …」** · 서버에 **안 닿았다**(`0/5`). 이유는 문구가 말한다 — **떠나는 중의 동기 XHR 을 Chrome 이 거절했다.** 명세 문장은 열지 못했다.

### 3. 65536 까지 · 합으로 — 넘으면 keepalive 는 `TypeError`, beacon 은 `false`

**출력**

```text
$ python3 wa32b-net.py page wa32b-34-limit.html
keepalive 65536바이트            → then status 204
keepalive 65537바이트            → catch TypeError 「Failed to fetch」
keepalive 없이 65537바이트       → then status 204
sendBeacon 65536바이트           → true
sendBeacon 65537바이트           → false
(서버가 keepalive 40000바이트를 붙잡고 있는 동안 — 한 줄에 한 번씩)
  keepalive 25536바이트          → then status 204
  keepalive 25537바이트          → catch TypeError 「Failed to fetch」
  sendBeacon 25536바이트         → true
  sendBeacon 25537바이트         → false
keepalive + ReadableStream 본문  → catch TypeError 「Failed to execute 'fetch' on 'Window': Keepalive request cannot have a ReadableStream body.」
--- 서버 로그 ---
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 65536바이트
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 65537바이트
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 65536바이트
A POST /beacon?hold=1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 40000바이트
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 25536바이트
A POST /beacon?hold=1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 40000바이트
A POST /beacon?hold=1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 40000바이트
A POST /beacon  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 25536바이트
A POST /beacon?hold=1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 40000바이트
(exit 0)
```

**왜 그런가**

- **keepalive 65536 `then` · 65537 `TypeError 「Failed to fetch」`**(서버 로그에 없다 — 안 보냈다) · **keepalive 없이 65537 은 된다.**
- **`sendBeacon` 65536 `true` · 65537 `false`**.
- ★★ **keepalive 40000 이 붙잡혀 있는 동안 — keepalive 25536 `then` · 25537 `TypeError` · beacon 25536 `true` · 25537 `false`.** 한도는 **합**이다.
- **keepalive + `ReadableStream` → `TypeError`**(`Keepalive request cannot have a ReadableStream body.`).

### 4. 전부 `true` · 전부 `POST` — B 의 `Blob(application/json)` 에만 `OPTIONS` 가 먼저 왔고 `POST` 는 안 갔다

**출력**

```text
$ python3 wa32b-net.py console wa32b-34-types.html
같은 출처 A	글	sendBeacon → true
같은 출처 A	Blob(type 없음)	sendBeacon → true
같은 출처 A	Blob(text/plain)	sendBeacon → true
같은 출처 A	Blob(application/json)	sendBeacon → true
같은 출처 A	URLSearchParams	sendBeacon → true
같은 출처 A	FormData	sendBeacon → true
다른 출처 B	글	sendBeacon → true
다른 출처 B	Blob(type 없음)	sendBeacon → true
다른 출처 B	Blob(text/plain)	sendBeacon → true
다른 출처 B	Blob(application/json)	sendBeacon → true
다른 출처 B	URLSearchParams	sendBeacon → true
다른 출처 B	FormData	sendBeacon → true
다른 출처 B	keepalive fetch(application/json)	catch TypeError 「Failed to fetch」
--- 콘솔 ---
javascript · error · Access to resource at 'http://127.0.0.1:<B>/beacon?id=%EB%8B%A43&body=Blob(application%2Fjson)' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/beacon?id=kj&body=keepalive-json' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
A POST /beacon?body=글  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · 본문 3바이트
A POST /beacon?body=Blob(type 없음)  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 3바이트
A POST /beacon?body=Blob(text/plain)  Origin=http://127.0.0.1:<A> · Content-Type=text/plain · 본문 3바이트
A POST /beacon?body=Blob(application/json)  Origin=http://127.0.0.1:<A> · Content-Type=application/json · 본문 7바이트
A POST /beacon?body=URLSearchParams  Origin=http://127.0.0.1:<A> · Content-Type=application/x-www-form-urlencoded;charset=UTF-8 · 본문 3바이트
A POST /beacon?body=FormData  Origin=http://127.0.0.1:<A> · Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 133바이트
B POST /beacon?body=글  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · 본문 3바이트
B POST /beacon?body=Blob(type 없음)  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · 본문 3바이트
B POST /beacon?body=Blob(text/plain)  Origin=http://127.0.0.1:<A> · Content-Type=text/plain · 본문 3바이트
B OPTIONS /beacon?body=Blob(application/json)  Origin=http://127.0.0.1:<A> · Access-Control-Request-Headers=content-type → 허용 헤더 없이 204
B POST /beacon?body=URLSearchParams  Origin=http://127.0.0.1:<A> · Content-Type=application/x-www-form-urlencoded;charset=UTF-8 · 본문 3바이트
B POST /beacon?body=FormData  Origin=http://127.0.0.1:<A> · Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 133바이트
B OPTIONS /beacon?body=keepalive-json  Origin=http://127.0.0.1:<A> · Access-Control-Request-Headers=content-type → 허용 헤더 없이 204
(exit 0)
```

**왜 그런가**

- **반환값은 열두 줄 모두 `true`.** 메서드는 전부 **`POST`**.
- **`Content-Type`** — 글 `text/plain;charset=UTF-8` · 타입 없는 `Blob` **없음** · `Blob` 의 `type` 그대로 · `URLSearchParams` `application/x-www-form-urlencoded;charset=UTF-8` · `FormData` multipart.
- ★★ **B 의 `Blob(application/json)` → `OPTIONS`(`Access-Control-Request-Headers=content-type`)만 오고 `POST` 없음** — 프리플라이트가 거부됐다. 페이지는 `true` 를 받았고 이유는 **콘솔에만** 있다.

### 5. 떠나지 않음 · 링크는 끝까지 — 탭 닫기는 가운데서 잘린다

**출력**

```text
$ python3 wa32b-net.py big
떠나지 않음(하네스가 직접 부름) → 헤더가 서버에 닿았나 = True
pagehide 에서 부르고 링크로 떠남 → 헤더가 서버에 닿았나 = True
pagehide 에서 부르고 탭 닫기(Page.close) → 헤더가 서버에 닿았나 = True
--- 서버 로그 ---
A POST /big?case=머묾  Content-Length=8388608 · 본문을 끝까지 받았나 = True · 받은 것이 있나 = True
A POST /big?case=링크  Content-Length=8388608 · 본문을 끝까지 받았나 = True · 받은 것이 있나 = True
A POST /big?case=닫기  Content-Length=8388608 · 본문을 끝까지 받았나 = False · 받은 것이 있나 = True
(exit 0)
```

**왜 그런가**

- **① ② → `끝까지 받았나 = True`**, **③ 탭 닫기 → `False` · `받은 것이 있나 = True`** — 헤더는 닿았고 본문이 **가운데서** 끊겼다.
- ②가 산 것은 **링크 이동의 문서가 bfcache 에 살아 있었기 때문**으로 읽는다(A6). 8 MiB 는 keepalive 로는 못 보낸다(A3).

### 6. fetch group terminated — keepalive 가 false 인 fetch 를 끊는다 · 가른 것은 「파괴됐나」

- **Fetch 명세** — fetch group 이 terminated 되면 **controller 가 있고 · 아직 done 이 아니고 · keepalive 가 false 인** fetch record 의 controller 를 terminate 한다. 탭 닫기는 문서를 파괴한다 → 진행 중이던 보통 `fetch` 가 끊겼다. **요청은 이미 선에 올라 닿은 뒤**였으므로 서버 쪽에서는 「응답을 놓을 때 소켓이 닫혀 있음」으로 보였다.
- **링크로 떠날 때 산 이유** — 그 문서는 **bfcache 에 들어가 파괴되지 않았다**(24편 (2) — 링크 이동의 `pagehide persisted=true`). **`unload` 리스너를 단 문서만** bfcache 에 못 들어가 파괴됐고(24편 (4)) 그래서 **`unload` 줄은 링크에서도 `살아 0/5`** 였다. **「떠났나」가 아니라 「파괴됐나」가 갈랐다**(31편 (5)과 같은 경계). terminate 를 누가 부르는지의 HTML 문장은 열지 못했다.

### 7. 「큐에 넣었다」 — 「보냈다」·「받았다」가 아니다

- **말하는 것** — 브라우저가 그 요청을 **받아 들였다**(한도 안이다 — 넘으면 `false`, A3).
- **말하지 않는 것** — **서버에 갔나 · 서버가 받았나.** A4 의 **다른 출처 B · `Blob(application/json)`** 줄이 경계다 — `true` 였는데 **`POST` 는 끝내 안 갔다**(프리플라이트 거부). 응답도 못 읽으므로 **페이지는 실패를 알 방법이 없다.**

### 8. 아직 안 끝난 keepalive 요청 본문의 합 — keepalive 와 beacon 이 같이 쓴다

- **한 요청의 한도가 아니라 합**이다 — 40000 이 붙잡혀 있으면 새 요청은 **25536 까지**였다(A3). 명세 — 「contentLength 와 **아직 안 끝난 keepalive 요청들의 본문 길이 합**이 64 kibibytes 보다 크면 network error」.
- **따로 안 쓴다** — 붙잡힌 것은 **keepalive fetch** 였는데 **`sendBeacon` 도 같은 25536/25537 경계**에서 갈렸다. **끝난 요청은 통에서 빠진다**(한도 안의 요청이 끝난 뒤에는 다시 65536 이 된다).

### 9. `visibilitychange → hidden` — `unload` 는 bfcache 를 막고 · 보통 `fetch` 를 끊는다

- **24편 (2)** — `visibilitychange → hidden` 은 **떠남 여섯 줄과 「다른 탭을 앞으로」까지 7행 전부**에서 났고, **`pagehide` 는 가림에서 안 났다.** 떠날 때와 가릴 때를 한 자리에서 잡는 것은 `visibilitychange → hidden` 이다.
- **`unload` 를 피할 이유** — ① **24편 (4) — `unload` 리스너 하나가 문서를 bfcache 에서 뺀다.** ② **이 편 (1) — 그래서 링크 이동에서도 문서가 파괴돼 보통 `fetch` 가 끊겼다**(`살아 0/5`). 그리고 24편은 Chrome 이 `unload` 를 **단계적으로 끄는 중**이라 적었다.

### 10. 「따라잡지 못했다」는 같은 성질 — 먼 서버의 결과는 주장하지 않는다

- **27편** — `fetch()` 를 부른 그 잡에서 `abort()` 해도 **요청이 먼저 선에 오른 판**이 있었다. **이 편의 「보통 `fetch` 도 닿았다」도 같은 모양**이다 — **문서가 파괴되는 일이 요청이 선에 오르는 일을 따라잡지 못했다.** localhost 라 오르는 데 거의 시간이 안 든다.
- **주장하지 않는 것** — **먼 서버 · 느린 선에서도 닿는다**는 것. 큰 본문은 이미 **가운데서 잘렸다**(A5) — 선이 느리면 작은 요청도 그쪽이 될 수 있다. **닿아야 하는 것은 keepalive/beacon 으로 보내고, 서버 쪽 멱등 처리로 지킨다.**

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · Python 3 표준 라이브러리 `http.server`(서버 A·B). **엔진은 Chrome 하나 · 서버는 localhost 다.**

★ **하네스** — [32번 주제](../32-server-sent-events/2-summary.md)의 (1)(`wa32b-net.py` 의 `leave` · `big` 모드와 `/beacon`·`/big`). 격자는 칸마다 **새 탭**이다 — 앞 칸의 문서가 뒤 칸에 안 남는다.

```sh
# wa32b-34-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서(격자 다섯 판은 몇 분 걸린다)
python3 wa32b-net.py leave wa32b-34-grid.html 5
python3 wa32b-net.py big
python3 wa32b-net.py page wa32b-34-limit.html
python3 wa32b-net.py console wa32b-34-types.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 떠날 때 전송 격자 40칸 | **판 안 5판** × 캡처 3판 | 동작 방식 (1) · A1 · A6 · A9 · A10 |
| 동기 결과(localStorage) | 캡처 3판(각 첫 판) | 동작 방식 (2) · A2 |
| 64KiB | 캡처 3판 | 동작 방식 (3) · A3 · A8 |
| 8 MiB 세 경우 | 캡처 3판 | 동작 방식 (4) · A5 |
| `Content-Type` · 교차 출처 | 캡처 3판 | 동작 방식 (5) · A4 · A7 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 「닿았다」 32칸 | 5/5 | localhost — 선이 느리면 달라질 수 있다 |
| 링크 이동에서 보통 `fetch` 가 산 것 | 살아 5/5 | bfcache 에 들어가느냐는 구현(24편) |
| 동기 XHR 을 거절하는 자리 | 여섯 칸 | Chrome 의 page dismissal 판정 |
| `sendBeacon` 의 한도 · `false` | 합 64KiB | Beacon 명세는 열지 못했다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② 먼 서버 · 지연을 넣은 선. ③ `fetchLater()`. ④ 모바일 백그라운드 전환.
