# web-api/32 — 서버 보내기 이벤트: `EventSource`·자동 재연결·`Last-Event-ID` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「서버 요청 로그」다 — 서버가 받은 `Last-Event-ID` 헤더와 페이지가 받은 번호를 한 줄에 대조하는 「재연결 · 유실 격자」.** 서버는 이벤트 1\~10 을 보내다 4 번째 뒤에서 끊는다. 칸은 `id:` 있음/없음 × `retry:` 지정/없음 × 서버가 다시 붙은 요청을 (이어 보냄 / 처음부터 / 현재부터) 다루는 방식 — **12칸**이다. 그 옆에 **「다시 붙나」 표**(응답 모양 8가지)와 **형식 표**(`event:` · 여러 줄 `data:` · 빈 줄 없는 마지막 블록)를 싣는다.\
> ★★ **기준 소스 — 명세 원문을 이 판에서 열지 못했다.** 서버 보내기 이벤트의 정본은 [WHATWG HTML — Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html) 절인데, 이 배치는 **외부 네트워크를 쓰지 않았고** 앞 배치가 받아 둔 명세 사본(Fetch · Streams · DOM · File API · XHR)에 그 절이 없다. 그래서 **이 편의 규칙 서술은 전부 「이 판의 관찰」이고, 「명세대로다 / 명세에서 벗어났다」는 판정을 하지 않는다**(가이드 규칙 5). 명세 쪽 확인은 「더 들어가면」에 숙제로 남긴다. 기준일 2026-09-26.\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 페이지는 로컬 서버 A(`http://127.0.0.1`)에서 열었고(`file://` 는 오류가 muted 된다 — 가이드 규칙 34), 서버는 **파이썬 표준 라이브러리로 직접 짠 SSE 응답**이다(아래 (1)).\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★ **[25번 주제](../25-fetch-request-response/2-summary.md)** — 「서버 요청 로그」 창과 상태 코드. 여기서는 그 창을 **연결이 여러 번 오는 요청**에 쓴다. ★ **[26번 주제](../26-response-body-streaming/2-summary.md)** — `fetch` 본문을 청크로 읽는 쪽. SSE 는 **같은 「끝나지 않는 응답」을 브라우저가 대신 파싱하고 대신 다시 붙는** 쪽이다(아래 「언제 쓰고」).\
> **경계** — ★ **교차 출처 `EventSource` 와 `withCredentials`** 는 재지 않았다 — 응답 읽기를 막는 규칙은 [28번 주제](../28-cors-simple-and-preflight/2-summary.md), 쿠키가 실리는 조건은 [29번 주제](../29-credentials-and-cookies/2-summary.md)가 `fetch` 로 쟀다. ★ **「SSE 가 WebSocket 보다 가볍다」는 이 편이 주장하지 않는다 — 재지 않았다**(가이드 규칙 4). 연혁은 [`../../../../history/web/05-웹플랫폼-API.md`](../../../../history/web/05-웹플랫폼-API.md) §4 가 정본인데, **그 절은 WebSocket · WebRTC 만 다루고 서버 보내기 이벤트 절은 아직 없다**(`grep` 으로 확인했다).\
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
| **안 흔들린다** | 격자 12칸의 받은 번호 · `Last-Event-ID` · 유실 · 중복 · `readyState` 전이 · 「다시 붙나」 표 · 형식 표 · 콘솔 문구 | 캡처 세 판이 **한 글자도 같았다** |
| ★ **흔들리게 만들지 않았다** | **재연결 간격** | 밀리초를 찍지 않고 **「서버가 끊은 뒤 다음 연결까지 1000ms 이상이었나」 참/거짓**만 찍었다(한 판 값은 근거가 아니다 — 가이드 규칙 24) |
| ★ **판에 매일 수 있는 칸** | 「헤더 없이 한 번 끊음」의 **곧바로 온 두 번째 연결** | `EventSource` 의 재연결이 아니라 **그 아래 층의 재시도**로 읽힌다((3)) — 원인은 재지 않았다 |
| **흔들린다** | Chrome 판 번호 · 포트 | 포트는 출력에 안 나온다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `readyState` 전이 · `MessageEvent` 의 `type`·`data`·`lastEventId` |
| 창 ③ 같은 것을 두 번 읽기 | **부적용** | — |
| **창 ④ 서버 요청 로그 — 연결마다 `Last-Event-ID` 와 도착 시각** | ★★★ **본체** | 몇 번 다시 붙었나 · 무엇을 들고 왔나 · 끊긴 뒤 얼마 만에 왔나(참/거짓) |
| ★ **「다시 붙었나」를 두 창으로** | ★★ **제5의 상태 — 같은 질문을 다른 창으로** | 페이지의 `error` 횟수와 서버가 받은 연결 수가 **갈린 칸이 있다**((3)의 「한 번 끊음」). ★ 서버 창이 못 보는 것 — **그 두 번째 연결을 누가 만들었나**(브라우저의 어느 층인가) |
| 콘솔(Log 도메인) | ★ **쓴다** | `text/plain` 을 거절한 문구 · 500 · 빈 응답 |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **명세 문장** | 원문을 열지 못했다(머리말). 이 편은 **관찰만** 적는다 |
| **실제 네트워크의 끊김**(모바일 전환 · 프록시가 연결을 자름) | 서버가 **스스로 끊는 것**으로만 흉내 냈다 |
| **기본 재연결 간격이 정확히 몇 ms 인가** | 재지 않았다 — 「1000ms 이상」 참/거짓까지다 |
| **탭이 숨겨지거나 bfcache 에 들어갔을 때의 연결** | 던지지 않았다 |
| **같은 출처 연결 수 한도**(HTTP/1.1 에서 오래 붙는 연결이 쌓이면) | 던지지 않았다 |

## 한눈에 — 쉽게 말하면

**★ `EventSource` 는 「책갈피를 꽂아 두는 라디오 연재」다. 방송국(서버)이 회차마다 번호(`id:`)를 붙여 읽어 주면, 라디오(브라우저)가 들은 마지막 번호를 책갈피로 꽂아 둔다. 전파가 끊기면 라디오가 알아서 다시 주파수를 맞추고(재연결), 방송국에 「몇 회까지 들었어요」(`Last-Event-ID`)라고 말한다. 그 뒤를 이어 읽어 줄지는 방송국 마음이다 — 책갈피를 무시하면 처음부터 다시 듣거나(중복), 그사이 지나간 회차를 놓친다(유실).**

| 비유 | 실체 |
|---|---|
| 회차 번호 | 이벤트의 `id:` 줄 |
| 책갈피 | 브라우저가 들고 있는 last event ID — 다시 붙을 때 `Last-Event-ID` 요청 헤더로 보낸다 |
| 다시 주파수 맞추기 | 자동 재연결 — 앱 코드가 안 한다 |
| 「몇 초 뒤에 다시 틀어라」 | `retry:` 줄 — 재연결 간격을 바꾼다 |
| 방송 종료 안내 | 다시 붙은 요청에 **204** — 재연결이 멈춘다 |
| 이어 읽기는 방송국 몫 | `Last-Event-ID` 로 **이어 줄지는 서버가 정한다** — 브라우저는 헤더만 보낸다 |

```text
   끊김 한 번 — 책갈피를 들고 다시 온다 (이 판)

   브라우저                                   서버
   연결 ① ─ GET /sse ────────────────────────▶  (Last-Event-ID 없음)
          ◀── id:1 … id:4 ─── 끊음
   (책갈피 = "4")   ··· 재연결 간격 ···
   연결 ② ─ GET /sse  Last-Event-ID: 4 ──────▶  이어 줄지는 서버가 정한다
          ◀── 이어 보냄 5…10   → 유실 0 · 중복 0
          ◀── 처음부터 1…10    → 중복 1~4
          ◀── 현재부터 7…10    → 유실 5·6
```

## 이 주제가 답하려는 질문

1. **연결이 끊기면 누가 다시 붙고, 무엇을 들고 오나** — `Last-Event-ID` 는 언제 실리고 언제 비나.
2. **유실 · 중복은 어디서 생기나** — 브라우저 쪽인가, 서버가 그 헤더를 다루는 방식인가.
3. **무엇이 재연결을 멈추나** — 상태 코드 · `Content-Type` · 네트워크 오류가 각각 무엇을 하나.

## 동작 방식

### (1) 하네스 — 24편 하네스에 서버만 새로

**Chrome 을 띄우고 CDP 로 붙는 부분은 [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1) 전문을 한 글자도 안 바꾸고 `import` 한다** — 28편 (1)과 같은 방식이다. 새로 세운 것은 서버다 — **32\~35 네 편이 같이 쓴다.**

- **`/sse`**(32 격자) — 이벤트 1\~10 을 `id:` 와 함께(또는 없이) 보내다 `cut` 번째 뒤에서 끊는다. 두 번째 연결은 `mode` 대로(이어 보냄 · 처음부터 · 현재부터) 10 까지 보내고 끊는다. **세 번째 연결에는 204** — 재연결을 멈추게 해서 한 칸이 끝난다.
- **`/sse1`**(32 「다시 붙나」) · **`/ssefmt`**(32 형식).
- **`/ws`**(33) — 핸드셰이크 · 프레임 읽기/쓰기 · 마스킹 풀기를 **표준 라이브러리만으로** 직접 짰다. **`/beacon`·`/big`**(34) — 받은 요청을 적고, 응답을 붙잡았다 놓으며 「그때 연결이 살아 있었나」를 적는다.
- **`/seen?id=`** — 그 `id` 로 **몇 번 · 무엇을 들고 · 언제** 왔나를 돌려준다. 페이지는 이것으로 **서버에게 물어** 격자를 채운다. **`/go?id=`** — 붙잡은 응답을 놓게 한다(24편의 「천천히는 시간이 아니라 신호다」).
- ★ **시각은 찍지 않는다** — 서버는 도착·끊음 시각을 들고 있지만, 페이지는 **「간격 ≥ 1000ms」 참/거짓**으로만 바꿔 찍는다.

```python
# wa32b-net.py
#!/usr/bin/env python3
"""web-api 32~35 — 24편 하네스(wa24b-net.py)의 Chrome·CDP 부분을 그대로 빌려 쓰고, 서버만 새로 세운다.

사용:
  wa32b-net.py page <html>          A 에서 그 페이지를 열고 window.__끝() 이 돌려준 글 → 서버 로그
  wa32b-net.py console <html>       page 와 같고, 서버 로그 앞에 콘솔(Log 도메인) 줄을 찍는다
  wa32b-net.py quiet <html>         page 와 같고, 서버 로그를 안 찍는다(페이지가 /seen 으로 물은 것만)
  wa32b-net.py leave <html> <판 수> 34편 — 떠날 때 전송 격자(페이지의 window.__칸 을 칸마다 새 탭에서)
  wa32b-net.py scroll <html>        35편 — 페이지의 __끝() 을 부르되, 페이지가 부탁하면 CDP 로 진짜 스크롤을 넣는다
  wa32b-net.py accept <키>          33편 — Sec-WebSocket-Accept 를 계산만 한다(브라우저 없이)

★ 포트는 전부 0 — 운영체제가 고른다. 출력에는 서버 이름(A·B)만 쓰고 포트는 <A>·<B> 로 적는다.
★ 서버 로그 — 엔드포인트 요청만 적는다(페이지 파일·/seen·/go 는 안 적는다).
  로그를 찍기 전에 처리 중인 요청이 0 이 되기를 기다린다(24편에서 잡은 흔들림).
★ 시각은 찍지 않는다 — 「간격이 X ms 이상이었나」 참/거짓만 찍는다(한 판 값은 근거가 아니다).
★ WebSocket 서버는 표준 라이브러리만으로 직접 짰다 — 핸드셰이크 · 프레임 읽기/쓰기 · 마스킹 풀기.
  무작위인 칸(Sec-WebSocket-Key · 마스킹 키 · 가려진 바이트)은 로그에 싣기 전에 가린다.
"""
import base64, hashlib, http.server, importlib.util, json, os, re, socket, struct, sys, threading, time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("wa24b_net", os.path.join(HERE, "wa24b-net.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
base.PROF = os.path.join(HERE, f".prof-wa32b-{os.getpid()}")
base.FLAGS = [f"--user-data-dir={base.PROF}" if f.startswith("--user-data-dir=") else f for f in base.FLAGS]
WAIT = 30
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

LOG, LOCK = [], threading.Lock()
COND = threading.Condition(LOCK)
SEEN = {}                      # id → [{"t": 도착 시각, "lei": Last-Event-ID, "end": 닫은 시각, ...}, ...]
GO = {}                        # id → /go 받은 횟수
PORTS = {}
ACTIVE = 0


def log(line):
    with LOCK:
        LOG.append(line)


def hide_ports(t):
    for p_name, p in PORTS.items():
        t = t.replace(f":{p}", f":<{p_name}>")
    return t


def hide_boundary(t):
    """multipart 경계 — Chrome 이 판마다 새로 만든다. 뒤 16자를 가린다(28편 하네스와 같은 규칙)."""
    return re.sub(r"(----WebKitFormBoundary)[0-9A-Za-z]{16}", r"\1<16자>", t)


def accept_of(key):
    return base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()


def hexs(b):
    return " ".join("%02x" % x for x in b)


def server(name):
    class H(http.server.SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        NAME = name

        def __init__(self, *a, **k):
            super().__init__(*a, directory=HERE, **k)

        def log_message(self, *a):
            pass

        def q(self):
            u = urllib.parse.urlsplit(self.path)
            return u.path, dict(urllib.parse.parse_qsl(u.query))

        def shown(self):
            path, qs = self.q()
            rest = "&".join(f"{k}={v}" for k, v in qs.items() if k != "id")
            return path + ("?" + rest if rest else "")

        def reply(self, code, body=b"", ctype="application/json", extra=()):
            self.send_response(code)
            if body or code not in (204, 304):
                self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in extra:
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self.route("OPTIONS")

        def do_GET(self):
            self.route("GET")

        def do_POST(self):
            self.route("POST")

        def body(self):
            n = int(self.headers.get("Content-Length", 0) or 0)
            return self.rfile.read(n) if n else b""

        def route(self, method):
            global ACTIVE
            with COND:
                ACTIVE += 1
            try:
                self.route1(method)
            finally:
                with COND:
                    ACTIVE -= 1
                    COND.notify_all()

        def route1(self, method):
            path, qs = self.q()
            i = qs.get("id", "")
            if path == "/seen":                    # 그 id 로 무엇이 왔나 — 로그에 안 적는다
                with LOCK:
                    got = [dict(x) for x in SEEN.get(i, [])]
                return self.reply(200, json.dumps(got, ensure_ascii=False).encode(),
                                  extra=[("Access-Control-Allow-Origin", "*")])
            if path == "/go":                      # 붙잡은 응답을 놓아라 — 로그에 안 적는다
                with COND:
                    GO[i] = GO.get(i, 0) + 1
                    COND.notify_all()
                return self.reply(204, extra=[("Access-Control-Allow-Origin", "*")])
            if path in ("/sse", "/sse1", "/ssefmt"):
                return getattr(self, path[1:])(method, qs, i)
            if path == "/ws":
                return self.ws(qs, i)
            if path == "/beacon":
                return self.beacon(method, qs, i)
            if path == "/big":
                return self.big(method, qs, i)
            if method == "GET":
                return super().do_GET()
            return self.reply(405)

        def arrive(self, i, **kw):
            with COND:
                rec = {"t": time.monotonic(), **kw}
                SEEN.setdefault(i, []).append(rec)
                COND.notify_all()
                return rec

        # ------------------------------------------------------------ 32 — 서버 보내기 이벤트
        def sse_head(self, code=200, ctype="text/event-stream"):
            self.send_response(code)
            if ctype:
                self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            if code == 204:
                self.send_header("Content-Length", "0")
            self.end_headers()
            self.close_connection = True

        def sse(self, method, qs, i):
            """이벤트 1~10 을 보내다 cut 번째 뒤에서 끊는다. 두 번째 연결은 mode 대로 이어 보내고 10 까지 간 뒤 끊는다.
            세 번째 연결에는 204 — 재연결을 멈추게 한다.
              ids=1|0        이벤트마다 id: 를 붙이나
              retry=ms|none  첫 연결 첫머리에 retry: 를 보내나
              mode=resume    Last-Event-ID 다음 번호부터 · restart 늘 1 부터 · current 끊긴 동안 지나간 둘을 건너뛴다"""
            lei = self.headers.get("Last-Event-ID")
            with LOCK:
                k = len(SEEN.get(i, []))
            rec = self.arrive(i, lei=lei)
            if k >= 2:
                self.sse_head(204, None)
                rec["end"] = time.monotonic()
                return
            cut, mode = int(qs.get("cut", "4")), qs.get("mode", "resume")
            if k == 0:
                start, stop = 1, cut
            elif mode == "resume":
                start, stop = (int(lei) + 1 if lei and lei.isdigit() else 1), 10
            elif mode == "restart":
                start, stop = 1, 10
            else:                                   # current — 끊긴 동안 cut+1, cut+2 가 지나갔다
                start, stop = cut + 3, 10
            self.sse_head()
            out = []
            if k == 0 and qs.get("retry", "none") != "none":
                out.append(f"retry: {qs['retry']}\n\n")
            for n in range(start, stop + 1):
                out.append((f"id: {n}\n" if qs.get("ids", "1") == "1" else "") + f"data: {n}\n\n")
            self.wfile.write("".join(out).encode())
            self.wfile.flush()
            rec["end"] = time.monotonic()

        def sse1(self, method, qs, i):
            """재연결하나 — 응답 모양 하나씩. 첫 연결에만 그 모양을 주고, 두 번째 연결부터는 204(멈춤)."""
            with LOCK:
                k = len(SEEN.get(i, []))
            rec = self.arrive(i, lei=self.headers.get("Last-Event-ID"))
            kind = qs.get("kind", "ok")
            drops = int(kind[4:] or "1") if kind.startswith("drop") else 0
            if kind.startswith("drop") and k < drops:   # 헤더도 안 보내고 연결을 끊는다 — 네트워크 오류
                self.close_connection = True
                self.connection.shutdown(socket.SHUT_RDWR)
                rec["end"] = time.monotonic()
                return
            if k >= max(drops, 1):
                self.sse_head(204, None)
                rec["end"] = time.monotonic()
                return
            if kind == "204":
                self.sse_head(204, None)
            elif kind == "500":
                self.sse_head(500)
            elif kind == "plain":
                self.sse_head(200, "text/plain")
                self.wfile.write(b"id: 1\ndata: 1\n\n")
            elif kind == "charset":
                self.sse_head(200, "text/event-stream; charset=utf-8")
                self.wfile.write(b"id: 1\ndata: 1\n\n")
            else:                                   # ok — 이벤트 하나 보내고 끊는다
                self.sse_head()
                self.wfile.write(b"retry: 100\nid: 1\ndata: 1\n\n")
            rec["end"] = time.monotonic()

        def ssefmt(self, method, qs, i):
            """형식 — event: 이름 · 여러 줄 data: · 주석 줄 · id 만 있는 블록 · 빈 줄 없이 끝나는 마지막 블록."""
            with LOCK:
                k = len(SEEN.get(i, []))
            self.arrive(i, lei=self.headers.get("Last-Event-ID"))
            if k >= 1:
                return self.sse_head(204, None)
            self.sse_head()
            self.wfile.write(("retry: 100\n\n"
                              ": 이 줄은 주석이다\n\n"
                              "data: 첫째\n\n"
                              "event: tick\ndata: 이름 붙은 것\n\n"
                              "data: 한 줄\ndata: 두 줄\n\n"
                              "id: 7\n\n"
                              "data:앞 공백 없음\n\n"
                              "data:  앞 공백 둘\n\n"
                              "event: tick\nid: 8\ndata: 마지막 블록 — 빈 줄 없이 끝난다\n").encode())

        # ------------------------------------------------------------ 33 — WebSocket
        OPS = {0: "이어짐", 1: "텍스트", 2: "바이너리", 8: "close", 9: "ping", 10: "pong"}

        def ws_send(self, op, payload=b""):
            """서버 → 브라우저 프레임 — FIN=1 · 마스킹 없음(서버는 가리지 않는다) · 125바이트 이하만."""
            frame = bytes([0x80 | op, len(payload)]) + payload
            self.wfile.write(frame)
            shown = hexs(frame) if len(frame) <= 16 else hexs(frame[:16]) + f" … (모두 {len(frame)}바이트)"
            log(f"{self.NAME} 서버→브라우저  {shown}   ← FIN=1 opcode={op}({self.OPS[op]}) MASK=0 길이={len(payload)}")

        def ws_recv(self, timeout=5):
            """브라우저 → 서버 프레임 하나. 마스킹 키와 가려진 바이트는 판마다 무작위라 로그에서 가린다."""
            self.connection.settimeout(timeout)
            try:
                h = self.rfile.read(2)
                if len(h) < 2:
                    return None, "연결이 닫혔다(0바이트)"
                fin, op, mask, n = h[0] >> 7, h[0] & 15, h[1] >> 7, h[1] & 127
                ext = b""
                if n == 126:
                    ext = self.rfile.read(2)
                    n = struct.unpack(">H", ext)[0]
                elif n == 127:
                    ext = self.rfile.read(8)
                    n = struct.unpack(">Q", ext)[0]
                key = self.rfile.read(4) if mask else b""
                data = self.rfile.read(n)
                plain = bytes(x ^ key[j % 4] for j, x in enumerate(data)) if mask else data
            except socket.timeout:
                return None, f"{timeout}초 동안 프레임 없음"
            finally:
                self.connection.settimeout(None)
            return (op, plain, fin), (f"{hexs(h)}{(' ' + hexs(ext)) if ext else ''} <마스킹 키 4바이트> <가려진 본문 {n}바이트>"
                                 f"   ← FIN={fin} opcode={op}({self.OPS.get(op, '?')}) MASK={mask} 길이={n}")

        def ws_show(self, op, plain):
            if op == 8:
                code = struct.unpack(">H", plain[:2])[0] if len(plain) >= 2 else None
                why = plain[2:].decode()
                why = repr(why) if len(why) <= 20 else f"{why[:4]!r}… ({len(plain) - 2}바이트)"
                return f"close 코드={code if code is not None else '(없음)'} 이유={why}"
            if op == 1:
                s = plain.decode()
                return f"글 {s!r}" if len(s) <= 20 else f"글 {s[:8]!r}… ({len(s)}글자)"
            if len(plain) > 16:
                return f"{len(plain)}바이트"
            return f"바이트 {hexs(plain)}"

        def ws_read_log(self, timeout=5):
            got, how = self.ws_recv(timeout)
            if got is None:
                log(f"{self.NAME} 브라우저→서버  {how}")
                return None
            log(f"{self.NAME} 브라우저→서버  {how}")
            log(f"{self.NAME}                풀어낸 본문 = {self.ws_show(got[0], got[1])}")
            return got

        def ws(self, qs, i):
            s = qs.get("s", "frames")
            key = self.headers.get("Sec-WebSocket-Key", "")
            self.arrive(i)
            if qs.get("show") == "1":           # 핸드셰이크 요청 원문 — 무작위인 키만 가린다
                log(f"{self.NAME} 받은 요청 원문(헤더 순서 그대로)")
                log(f"    {self.requestline}")
                for k, v in self.headers.items():
                    if k == "Sec-WebSocket-Key":
                        v = f"<{len(v)}자 — base64 를 풀면 {len(base64.b64decode(v))}바이트>"
                    elif k in ("User-Agent", "Accept-Language"):
                        v = "<생략>"
                    log(f"    {k}: {hide_ports(v)}")
            acc = "AAAAAAAAAAAAAAAAAAAAAAAAAAA=" if s == "badaccept" else accept_of(key)
            head = ("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                    f"Sec-WebSocket-Accept: {acc}\r\n\r\n")
            self.close_connection = True
            self.wfile.write(head.encode())
            if qs.get("show") == "1":
                log(f"{self.NAME} 보낸 응답 원문")
                for line in head.split("\r\n")[:-2]:
                    log("    " + (line if not line.startswith("Sec-WebSocket-Accept") else
                                  "Sec-WebSocket-Accept: <28자 — 서버가 계산한 값>"))
                log(f"    (서버가 계산한 Accept 가 base64(SHA-1(키 + GUID)) 와 같나 = {acc == accept_of(key)})")
            try:
                getattr(self, "ws_" + s.split("-")[0])(qs, i, s)
            except (OSError, ValueError) as e:
                log(f"{self.NAME} ({type(e).__name__})")
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        def ws_badaccept(self, qs, i, s):
            got, how = self.ws_recv(3)
            log(f"{self.NAME} 틀린 Accept 를 보낸 뒤 브라우저→서버  {how if got is None else how}")

        def ws_frames(self, qs, i, s):
            self.ws_send(9, b"p1")                # ping — 페이지 API 에는 안 보인다
            self.ws_read_log()                      # 브라우저가 알아서 돌려준 pong
            self.ws_send(1, "서버가 보낸 글".encode())
            self.ws_send(2, bytes([1, 2, 3]))
            self.ws_read_log()                      # 페이지의 send("안녕")
            self.ws_read_log()                      # 페이지의 send(Uint8Array)
            self.ws_read_log()                      # 페이지의 send("x".repeat(200)) — 길이 126 꼴
            self.ws_send(8, struct.pack(">H", 1000) + b"done")
            self.ws_read_log()                      # 브라우저의 close 답

        def ws_close(self, qs, i, s):
            """서버가 먼저 닫는다 — s=close-1000 · close-none(코드 없음) · close-tcp(프레임 없이 TCP 를 끊음)."""
            how = s.split("-", 1)[1]
            if how == "tcp":
                log(f"{self.NAME} 서버가 close 프레임 없이 TCP 를 끊었다")
                return
            self.ws_send(8, b"" if how == "none" else struct.pack(">H", int(how)) + b"bye")
            self.ws_read_log(3)

        def ws_client(self, qs, i, s):
            """페이지가 먼저 닫는다 — 서버는 받은 close 를 그대로 돌려준다."""
            got = self.ws_read_log()
            if got and got[0] == 8:
                self.ws_send(8, got[1])

        def ws_silent(self, qs, i, s):
            """반쯤 열린 연결을 흉내 — 소켓은 연 채로, 읽지도 쓰지도 않는다. /go 가 오면 쌓인 프레임을 읽는다."""
            log(f"{self.NAME} 서버가 입을 닫았다(소켓은 연 채)")
            ok = wait_for(lambda: GO.get(i, 0) >= 1)
            log(f"{self.NAME} /go 를 받고 쌓인 프레임을 읽는다" if ok else f"{self.NAME} go 안 옴")
            while self.ws_read_log(1):
                pass

        def ws_buffer(self, qs, i, s):
            """큰 메시지 하나를 FIN=1 이 올 때까지 조각째 받고, 다 받았으면 글로 답한다."""
            total, sizes = 0, []
            while True:
                got, how = self.ws_recv(10)
                if got is None:
                    log(f"{self.NAME} 브라우저→서버  {how}")
                    return
                if not sizes or got[2]:
                    log(f"{self.NAME} 브라우저→서버  {how}")
                total += len(got[1])
                sizes.append(len(got[1]))
                if got[2]:
                    break
            log(f"{self.NAME} 한 메시지 = 프레임 {len(sizes)}개 · 합 {total}바이트 · 크기 {sorted(set(sizes), reverse=True)}")
            self.ws_send(1, f"받음 {total}바이트".encode())
            got = self.ws_read_log()
            if got and got[0] == 8:
                self.ws_send(8, got[1])

        # ------------------------------------------------------------ 34 — 떠날 때 전송
        def big(self, method, qs, i):
            """34 — 큰 본문. 헤더만 받고 /go 가 올 때까지 본문을 안 읽는다(버퍼가 차면 올리기가 멈춘다).
            go 뒤에 읽을 수 있는 만큼 읽어 Content-Length 와 견준다."""
            want = int(self.headers.get("Content-Length", 0) or 0)
            rec = self.arrive(i, method=method, want=want)
            wait_for(lambda: GO.get(i, 0) >= 1)
            got = 0
            self.connection.settimeout(3)
            try:
                while got < want:
                    b = self.rfile.read1(min(65536, want - got))
                    if not b:
                        break
                    got += len(b)
            except OSError:
                pass
            with COND:
                rec["got"] = got
                COND.notify_all()
            log(f"{self.NAME} {method} {self.shown()}  Content-Length={want} · 본문을 끝까지 받았나 = {got == want}"
                f" · 받은 것이 있나 = {got > 0}")
            self.close_connection = True
            try:
                self.reply(204)
            except OSError:
                pass

        def beacon(self, method, qs, i):
            """받은 요청을 적는다. hold=1 이면 /go 를 받을 때까지 응답을 붙잡고, 놓는 순간 연결이 살아 있었나를 적는다."""
            data = self.body() if method == "POST" else b""
            ct = hide_boundary(self.headers.get("Content-Type", "(없음)"))
            o = hide_ports(self.headers.get("Origin", "(없음)"))
            rec = self.arrive(i, method=method, ct=ct, n=len(data))
            if method == "OPTIONS":
                log(f"{self.NAME} OPTIONS {self.shown()}  Origin={o} · Access-Control-Request-Headers="
                    f"{self.headers.get('Access-Control-Request-Headers', '(없음)')} → 허용 헤더 없이 204")
                return self.reply(204)
            if qs.get("quiet") != "1":
                log(f"{self.NAME} {method} {self.shown()}  Origin={o} · Content-Type={ct} · 본문 {len(data)}바이트")
            if qs.get("hold") == "1":
                wait_for(lambda: GO.get(i, 0) >= 1)
                with COND:
                    rec["alive"] = not base.peer_closed(self.connection)
                    COND.notify_all()
            try:
                return self.reply(204)
            except OSError:                        # 떠난 쪽이 이미 끊었다 — 위에서 적었다
                self.close_connection = True

    class S(http.server.ThreadingHTTPServer):
        address_family = socket.AF_INET6

        def server_bind(self):
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            super().server_bind()

    s = S(("::", 0), H)
    s.daemon_threads = True
    PORTS[name] = s.server_address[1]
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def wait_for(pred, timeout=WAIT):
    with COND:
        return COND.wait_for(pred, timeout=timeout)


def print_log():
    wait_for(lambda: ACTIVE == 0)
    print("--- 서버 로그 ---")
    with LOCK:
        lines = LOG[:]
        LOG.clear()
    for line in lines:
        print(line)
    if not lines:
        print("(받은 요청 없음)")


def print_console(c, sid):
    print("--- 콘솔 ---")
    got = c.take("Log.entryAdded", sid)
    for e in got:
        t = hide_ports(e["entry"]["text"])
        print(e["entry"]["source"], "·", e["entry"]["level"], "·", t)
    if not got:
        print("(콘솔 줄 없음)")


BASES = {}


def open_tab(c, url=None):
    tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    for m in ("Page.enable", "Runtime.enable", "Log.enable"):
        c.send(m, sid=sid)
    c.send("Page.addScriptToEvaluateOnNewDocument",
           {"source": "".join(f"window.__{k} = {json.dumps(v)};" for k, v in BASES.items())}, sid)
    if url:
        base.goto(c, sid, url)
    return tid, sid


# -------------------------------------------------------------------- 34 — 떠날 때 전송 격자
def arrived(i):
    return any(r.get("method") != "OPTIONS" for r in SEEN.get(i, []))


def leave_grid(c, a_url, page, rounds):
    tid, sid = open_tab(c, a_url + page)
    hows, ats, leaves = (base.evaluate(c, sid, f"window.__{k}") for k in ("방법", "자리", "떠남"))
    c.send("Target.closeTarget", {"targetId": tid})
    c.wait("Target.detachedFromTarget")
    got = {}
    for r in range(rounds):
        for how in hows:
            for at in ats:
                for lv in leaves:
                    i = f"p{r}-{how}-{at}-{lv}"
                    tid, sid = open_tab(c, a_url + f"wa32b-34-leave.html?how={how}&at={at}&id={i}")
                    c.events.clear()
                    if lv == "링크":
                        base.click(c, sid, "#go")
                        c.wait("Page.loadEventFired", sid)
                    else:
                        c.send("Page.close", {}, sid)
                        c.wait("Target.detachedFromTarget")
                    ok = wait_for(lambda: arrived(i), timeout=2)      # 안 오면 2초 뒤 「안 옴」
                    time.sleep(0.5)                                     # 떠난 쪽이 연결을 끊을 틈
                    with COND:
                        GO[i] = 1
                        COND.notify_all()
                    hold = how != "xhr"
                    if ok and hold:
                        wait_for(lambda: "alive" in next(x for x in SEEN[i] if x.get("method") != "OPTIONS"), 5)
                    rec = next((x for x in SEEN.get(i, []) if x.get("method") != "OPTIONS"), {})
                    got.setdefault((how, at, lv), []).append((ok, rec.get("alive") if hold else None))
                    if lv == "링크":
                        c.send("Target.closeTarget", {"targetId": tid})
                        c.wait("Target.detachedFromTarget")
    tid, sid = open_tab(c, a_url + "wa32b-34-next.html")
    page_says = json.loads(base.evaluate(c, sid, "JSON.stringify(Object.fromEntries(Object.entries(localStorage)))"))
    print(f"떠날 때 한 번 보낸 요청 — 서버에 닿은 판 / {rounds}판 · (닿은 판 중 응답 때 연결이 살아 있던 판)")
    print("\t".join(["방법", "자리"] + [{"링크": "링크로 떠나기", "닫기": "탭 닫기(Page.close)"}[lv] for lv in leaves]))
    cut = shaky = 0
    for how in hows:
        for at in ats:
            row = [how, at]
            for lv in leaves:
                xs = got[(how, at, lv)]
                n = sum(1 for ok, _ in xs if ok)
                alive = [a for ok, a in xs if ok and a is not None]
                cell = f"{n}/{rounds}" + (f" (살아 {sum(alive)}/{len(alive)})" if alive else "")
                cut += n < rounds
                shaky += 0 < n < rounds
                row.append(cell)
            if len(row) != 2 + len(leaves):
                raise RuntimeError("칸 수가 어긋났다")
            print("\t".join(row))
    total = len(hows) * len(ats) * len(leaves)
    print(f"한 판이라도 서버에 안 닿은 칸 = {cut} / {total}")
    print(f"판마다 갈린 칸(0 < 닿은 판 < {rounds}) = {shaky} / {total}")
    print("--- 부른 자리에서 페이지가 적은 동기 결과(첫 판) ---")
    for how in ("beacon", "xhr"):
        for at in ats:
            print("\t".join([how, at] + [page_says.get(f"결과-p0-{how}-{at}-{lv}", "(안 적힘)") for lv in leaves]))


def big_leave(c, a_url):
    """8 MiB 를 보통 fetch 로 — 떠나지 않을 때 · 링크로 떠날 때 · 탭을 닫을 때. 서버는 go 뒤에야 본문을 읽는다."""
    for lv in ("머묾", "링크", "닫기"):
        i = "big-" + lv
        tid, sid = open_tab(c, a_url + f"wa32b-34-big.html?id={i}")
        c.events.clear()
        if lv == "머묾":
            base.evaluate(c, sid, "window.__보내기(), 0")
        elif lv == "링크":
            base.click(c, sid, "#go")
            c.wait("Page.loadEventFired", sid)
        else:
            c.send("Page.close", {}, sid)
            c.wait("Target.detachedFromTarget")
        ok = wait_for(lambda: bool(SEEN.get(i)), timeout=2)
        time.sleep(0.5)                                         # 떠난 쪽이 연결을 끊을 틈
        with COND:
            GO[i] = 1
            COND.notify_all()
        if ok:
            wait_for(lambda: "got" in SEEN[i][0], 10)
        print({"머묾": "떠나지 않음(하네스가 직접 부름)", "링크": "pagehide 에서 부르고 링크로 떠남",
               "닫기": "pagehide 에서 부르고 탭 닫기(Page.close)"}[lv]
              + f" → 헤더가 서버에 닿았나 = {ok}")
        if lv != "닫기":
            c.send("Target.closeTarget", {"targetId": tid})
            c.wait("Target.detachedFromTarget")
    print_log()


def main():
    base.signal.signal(base.signal.SIGTERM, lambda *a: sys.exit(143))
    mode = sys.argv[1]
    if mode == "accept":
        key = sys.argv[2]
        print(f"Sec-WebSocket-Key    = {key}")
        print(f"키 + GUID            = {key}{GUID}")
        print(f"SHA-1 (16진)         = {hashlib.sha1((key + GUID).encode()).hexdigest()}")
        print(f"Sec-WebSocket-Accept = {accept_of(key)}")
        return
    a, b = server("A"), server("B")
    a_url = f"http://127.0.0.1:{PORTS['A']}/"
    BASES.update(A=f"http://127.0.0.1:{PORTS['A']}", B=f"http://127.0.0.1:{PORTS['B']}")
    try:
        proc, c = base.start()
        try:
            if mode in ("page", "console", "quiet"):
                tid, sid = open_tab(c, a_url + sys.argv[2])
                print(base.evaluate(c, sid, "window.__끝()"))
                if mode == "console":
                    print_console(c, sid)
                if mode != "quiet":
                    print_log()
            elif mode == "scroll":             # 35 — 준비 → CDP 휠 제스처 1200px → 결과
                tid, sid = open_tab(c, a_url + sys.argv[2])
                print(base.evaluate(c, sid, "window.__준비()"))
                c.send("Input.synthesizeScrollGesture", {"x": 500, "y": 300, "yDistance": -1200, "speed": 1200,
                                                         "gestureSourceType": "mouse"}, sid)
                print("CDP Input.synthesizeScrollGesture — yDistance -1200 · speed 1200 · mouse")
                print(base.evaluate(c, sid, "window.__결과()"))
            elif mode == "big":
                big_leave(c, a_url)
            elif mode == "leave":
                leave_grid(c, a_url, sys.argv[2], int(sys.argv[3]))
            else:
                sys.exit("모드는 page | console | quiet | leave | scroll | accept")
        finally:
            base.stop(proc)
    finally:
        a.shutdown()
        b.shutdown()


if __name__ == "__main__":
    main()
```

### (2) ★★★ 본체 — 재연결 · 유실 격자

```html
<!-- wa32b-32-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>32 grid</title>
<script>
// 재연결 · 유실 격자 — 서버는 이벤트 1~10 을 보내다 4 번째 뒤에서 끊는다(연결 ①).
// 연결 ② 는 mode 대로 이어 보내고 10 까지 간 뒤 끊는다. 연결 ③ 에는 204 — 재연결이 멈춘다.
// 칸마다 EventSource 하나 — 받은 번호 · 서버가 받은 Last-Event-ID · 재연결 간격(참/거짓)
const 칸들 = [];
for (const ids of ["1", "0"]) for (const retry of ["200", "none"]) for (const mode of ["resume", "restart", "current"])
  칸들.push({ ids, retry, mode });
const 한칸 = (x, k) => new Promise(r => {
  const id = "g" + k;
  const es = new EventSource(`/sse?id=${id}&ids=${x.ids}&retry=${x.retry}&mode=${x.mode}&cut=4`);
  const 받음 = [], 상태 = [es.readyState];
  es.onopen = () => 상태.push(es.readyState);
  es.onmessage = e => 받음.push(Number(e.data));
  es.onerror = () => { 상태.push(es.readyState); if (es.readyState === 2) r({ id, 받음, 상태 }); };
});
window.__끝 = async () => {
  const 줄 = [], 이름 = { resume: "이어 보냄", restart: "처음부터", current: "현재부터" };
  let 샌칸 = 0, 갈린쌍 = 0;
  const 간격표 = {};
  for (const [k, x] of 칸들.entries()) {
    const { id, 받음, 상태 } = await 한칸(x, k);
    const 서버 = await (await fetch("/seen?id=" + id)).json();
    const lei = 서버.map(s => s.lei ?? "없음");
    const 간격 = 서버.slice(1).map((s, j) => (s.t - 서버[j].end) * 1000 >= 1000);
    const 유실 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].filter(n => !받음.includes(n));
    const 중복 = 받음.filter((n, j) => 받음.indexOf(n) !== j);
    if (유실.length || 중복.length) 샌칸++;
    간격표[x.ids + x.mode + x.retry] = JSON.stringify(간격);
    const 칸 = ["id:" + (x.ids === "1" ? "있음" : "없음"), "retry:" + (x.retry === "none" ? "없음" : x.retry),
      이름[x.mode], "받음 " + JSON.stringify(받음), "Last-Event-ID " + JSON.stringify(lei),
      "유실 " + JSON.stringify(유실), "중복 " + JSON.stringify(중복), "간격≥1000ms " + JSON.stringify(간격),
      "readyState " + 상태.join("→")];
    if (칸.length !== 9) throw new Error("칸 수");
    줄.push(칸.join("\t"));
  }
  for (const ids of ["1", "0"]) for (const mode of ["resume", "restart", "current"])
    if (간격표[ids + mode + "200"] !== 간격표[ids + mode + "none"]) 갈린쌍++;
  줄.push(`유실이나 중복이 있는 칸 = ${샌칸} / ${칸들.length}`);
  줄.push(`retry: 200 의 유무로 「간격≥1000ms」 가 갈린 쌍 = ${갈린쌍} / ${칸들.length / 2}`);
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa32b-net.py quiet wa32b-32-grid.html
id:있음	retry:200	이어 보냄	받음 [1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 []	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
id:있음	retry:200	처음부터	받음 [1,2,3,4,1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 [1,2,3,4]	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
id:있음	retry:200	현재부터	받음 [1,2,3,4,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 [5,6]	중복 []	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
id:있음	retry:없음	이어 보냄	받음 [1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 []	간격≥1000ms [true,true]	readyState 0→1→0→1→0→2
id:있음	retry:없음	처음부터	받음 [1,2,3,4,1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 []	중복 [1,2,3,4]	간격≥1000ms [true,true]	readyState 0→1→0→1→0→2
id:있음	retry:없음	현재부터	받음 [1,2,3,4,7,8,9,10]	Last-Event-ID ["없음","4","10"]	유실 [5,6]	중복 []	간격≥1000ms [true,true]	readyState 0→1→0→1→0→2
id:없음	retry:200	이어 보냄	받음 [1,2,3,4,1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","없음","없음"]	유실 []	중복 [1,2,3,4]	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
id:없음	retry:200	처음부터	받음 [1,2,3,4,1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","없음","없음"]	유실 []	중복 [1,2,3,4]	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
id:없음	retry:200	현재부터	받음 [1,2,3,4,7,8,9,10]	Last-Event-ID ["없음","없음","없음"]	유실 [5,6]	중복 []	간격≥1000ms [false,false]	readyState 0→1→0→1→0→2
id:없음	retry:없음	이어 보냄	받음 [1,2,3,4,1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","없음","없음"]	유실 []	중복 [1,2,3,4]	간격≥1000ms [true,true]	readyState 0→1→0→1→0→2
id:없음	retry:없음	처음부터	받음 [1,2,3,4,1,2,3,4,5,6,7,8,9,10]	Last-Event-ID ["없음","없음","없음"]	유실 []	중복 [1,2,3,4]	간격≥1000ms [true,true]	readyState 0→1→0→1→0→2
id:없음	retry:없음	현재부터	받음 [1,2,3,4,7,8,9,10]	Last-Event-ID ["없음","없음","없음"]	유실 [5,6]	중복 []	간격≥1000ms [true,true]	readyState 0→1→0→1→0→2
유실이나 중복이 있는 칸 = 10 / 12
retry: 200 의 유무로 「간격≥1000ms」 가 갈린 쌍 = 6 / 6
(exit 0)
```

- ★★★ **유실이나 중복이 있는 칸 10 / 12.** 없던 칸은 **`id:` 있음 × 이어 보냄** 두 칸(`retry:` 200 · 없음)뿐이다.
- ★★★ **브라우저는 책갈피를 들고 왔다 — 이어 줄지는 서버가 정했다.** `id:` 있는 여섯 칸 전부에서 서버가 받은 헤더는 `["없음","4","10"]` 이다 — 첫 연결에는 없고, 두 번째에 **마지막으로 받은 `id` 인 `4`**, 세 번째에 `10`. 그런데 **같은 헤더를 받고도** 「처음부터」는 1\~4 를 **중복**, 「현재부터」는 5·6 을 **유실**했다.
- ★★ **`id:` 가 없으면 책갈피가 없다** — 서버가 받은 헤더는 세 연결 모두 `없음` 이다. 그래서 「이어 보냄」 서버도 **어디서 이을지 몰라 1 부터** 보냈고 1\~4 가 중복됐다. ★ **「현재부터」는 `id:` 가 있든 없든 똑같이 5·6 을 잃었다** — 책갈피를 무시하는 서버에게는 책갈피가 아무 일도 안 한다.
- ★★ **`retry: 200` 의 유무로 「간격 ≥ 1000ms」 가 갈린 쌍 6 / 6** — 지정한 판은 `[false,false]`, 안 한 판은 `[true,true]`. **`retry:` 가 재연결 간격을 바꿨다.** 기본 간격이 몇 ms 인지는 **재지 않았다**(1000ms 이상이었다는 것까지).
- **`readyState` 는 열두 칸 모두 `0→1→0→1→0→2`** — 연결 중(0) → 열림(1) → 끊겨 **다시 연결 중(0)** → 열림 → 다시 0 → 204 를 받고 **닫힘(2)**. 끊겼을 때 `error` 는 났지만 **닫히지 않고 0 으로 돌아갔다** — `error` 는 「끝났다」가 아니다.

```text
   readyState — 한 칸의 전이 (이 판, 12칸 모두 같음)

   0 CONNECTING ──open──▶ 1 OPEN ──(서버가 끊음) error──▶ 0 CONNECTING ··· 재연결 간격 ···
        ──open──▶ 1 OPEN ──(끊음) error──▶ 0 ──(204) error──▶ 2 CLOSED
   ★ error 는 세 번 — 앞의 둘은 0 으로 돌아갔고, 마지막 하나만 2 였다
     「끝났나」는 onerror 가 아니라 readyState === 2 로 본다
```

```text
   재연결 · 유실 격자 — 12칸 (이 판)

                           이어 보냄        처음부터         현재부터
   id:있음 · 헤더 4 를 받음   유실 0 중복 0     중복 1~4         유실 5·6
   id:없음 · 헤더 없음        중복 1~4 ★       중복 1~4         유실 5·6
                           (어디서 이을지 모름)
   ★ retry: 는 어느 칸의 번호도 안 바꿨다 — 바꾼 것은 간격(≥1000ms 참/거짓)뿐
   ★ 유실 · 중복을 없앤 것 = 「id: 를 붙인다」 + 「서버가 Last-Event-ID 를 존중한다」 둘 다
```

### (3) ★★ 무엇이 재연결을 멈추나 — 응답 모양 8가지

**첫 연결에만** 그 모양을 주고, 다시 오면 204 로 멈추게 한다. 그래서 **「서버가 받은 연결 2 이상」 = 다시 붙었다**이다.

```html
<!-- wa32b-32-stop.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>32 stop</title>
<script>
// 첫 연결의 응답 모양 하나씩 — 브라우저가 다시 붙나? (두 번째로 오면 서버는 204 로 멈춘다)
// 서버가 받은 연결 수 · open 이 났나 · 받은 data · readyState 전이 · 연결 사이 간격(참/거짓)
const 모양 = [
  ["200 text/event-stream — 하나 보내고 끊음", "ok"],
  ["200 text/event-stream; charset=utf-8", "charset"],
  ["204 No Content", "204"],
  ["500", "500"],
  ["200 text/plain", "plain"],
  ["헤더 없이 연결을 끊음 — 한 번", "drop1"],
  ["헤더 없이 연결을 끊음 — 두 번 연달아", "drop2"],
  ["헤더 없이 연결을 끊음 — 세 번 연달아", "drop3"],
];
const 한칸 = (kind, k) => new Promise(r => {
  const id = "s" + k, es = new EventSource(`/sse1?id=${id}&kind=${kind}`);
  const 상태 = [es.readyState], 받음 = []; let 열림 = 0;
  es.onopen = () => { 열림++; 상태.push(es.readyState); };
  es.onmessage = e => 받음.push(e.data);
  es.onerror = () => { 상태.push(es.readyState); if (es.readyState === 2) r({ id, 상태, 받음, 열림 }); };
});
window.__끝 = async () => {
  const 줄 = []; let 다시 = 0;
  for (const [k, [말, kind]] of 모양.entries()) {
    const { id, 상태, 받음, 열림 } = await 한칸(kind, k);
    const 서버 = await (await fetch("/seen?id=" + id)).json(), n = 서버.length;
    const 간격 = 서버.slice(1).map((s, j) => (s.t - 서버[j].end) * 1000 >= 1000);
    if (n > 1) 다시++;
    const 칸 = [말, "서버가 받은 연결 " + n, "open " + 열림 + "번", "받은 data " + JSON.stringify(받음), "readyState " + 상태.join("→"), "간격≥1000ms " + JSON.stringify(간격)];
    if (칸.length !== 6) throw new Error("칸 수");
    줄.push(칸.join("\t"));
  }
  줄.push(`다시 붙은 모양 = ${다시} / ${모양.length}`);
  return 줄.join("\n");
};
</script>
```

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

- ★★ **다시 붙은 모양 5 / 8.** 정상 스트림이 끝난 둘(`text/event-stream` · `; charset=utf-8`)과 **헤더 없이 끊은 셋**이 다시 붙었다. **204 · 500 · `text/plain` 은 한 번으로 끝났다** — `readyState` 가 `0→2`, `open` 0번.
- ★★ **204 는 첫 연결에서도 멈춘다.** 격자에서는 「세 번째 연결을 끝내는 신호」로 썼지만, 처음부터 204 를 주면 **한 번도 안 열리고 닫힌다.** 서버가 「더 보낼 것 없다」를 말하는 방법이다.
- ★★ **500 도 재연결을 안 했다.** 「서버 오류니 잠시 뒤 다시」가 아니다 — **다시 붙게 하려면 200 으로 열었다가 끊어야** 했다. 콘솔은 `Failed to load resource … status of 500` 한 줄뿐이다.
- ★★ **`Content-Type: text/plain` 이면 `error` 하나로 닫힌다** — 콘솔 문구가 이유를 말한다: `EventSource's response has a MIME type ("text/plain") that is not "text/event-stream". Aborting the connection.` **`; charset=utf-8` 이 붙은 `text/event-stream` 은 통과했다.**
- ★★★ **「헤더 없이 한 번 끊음」은 서버가 연결 2개를 받았는데 페이지는 `error` 를 한 번도 못 봤다**(`readyState 0→2` — 마지막 204 의 `error` 하나뿐). 그리고 두 연결 사이 간격이 **1000ms 미만**(`[false]`)이다 — 재연결 간격을 기다린 `EventSource` 의 재연결이 아니다. **두 번 · 세 번 연달아 끊으면** 첫 간격은 여전히 `false`, 그 뒤부터 `true` 이고 `error` 가 그만큼 난다(`0→0→2` · `0→0→0→2`). **첫 한 번은 `EventSource` 아래 층이 조용히 다시 보낸 것**으로 읽힌다 — **어느 층인지는 재지 않았다**(머리말 「판에 매일 수 있는 칸」). ★ 콘솔의 `net::ERR_EMPTY_RESPONSE` 는 **세 줄**인데 끊음은 모두 **여섯 번**(한 번 + 두 번 + 세 번)이다 — **줄 수가 끊음 수와 다르다**는 것까지만 적는다(어느 끊음이 줄을 안 남겼는지는 줄에 표시가 없다).

```text
   「헤더 없이 끊음」 — 두 창이 본 것 (이 판)

                 서버가 받은 연결   간격≥1000ms       페이지의 error(끝의 204 몫 제외)
   한 번 끊음    2                  [false]           0     ← 서버는 「왔다」, 페이지는 「몰랐다」
   두 번 연달아  3                  [false,true]      1
   세 번 연달아  4                  [false,true,true] 2
   ★ 곧바로(false) 온 연결에는 error 가 없었다 — EventSource 의 재연결 모양이 아니다
```

```text
   다시 붙나 — 첫 응답의 모양별 (이 판)

   200 text/event-stream 을 열었다가 끊음      ○ 다시 붙는다 (error → readyState 0)
   헤더 없이 끊음(네트워크 오류)              ○ 다시 붙는다  ★ 첫 번은 error 없이 곧바로
   204                                       ✕ 닫힌다 (readyState 2) — 서버가 멈추는 신호
   500                                       ✕ 닫힌다
   200 text/plain                            ✕ 닫힌다 — 콘솔: MIME type … Aborting
   ★ 「다시 붙게 하려면」 = 연결을 열어 둔 채 끊겨야 한다. 오류 코드는 멈추는 쪽이다
```

### (4) 형식 — `event:` · 여러 줄 `data:` · 빈 줄 없는 마지막 블록

```html
<!-- wa32b-32-format.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>32 format</title>
<script>
// 한 응답 안의 블록들 — message 리스너와 tick 리스너가 각각 무엇을 받나
window.__끝 = () => new Promise(r => {
  const es = new EventSource("/ssefmt?id=f"), 줄 = [];
  const 적기 = 쪽 => e => 줄.push(`${쪽}\ttype=${e.type}\tdata=${JSON.stringify(e.data)}\tlastEventId=${JSON.stringify(e.lastEventId)}`);
  es.onmessage = 적기("onmessage");
  es.addEventListener("tick", 적기("tick 리스너"));
  es.onerror = () => { if (es.readyState === 2) r(줄.join("\n")); };
});
</script>
```

```text
$ python3 wa32b-net.py quiet wa32b-32-format.html
onmessage	type=message	data="첫째"	lastEventId=""
tick 리스너	type=tick	data="이름 붙은 것"	lastEventId=""
onmessage	type=message	data="한 줄\n두 줄"	lastEventId=""
onmessage	type=message	data="앞 공백 없음"	lastEventId="7"
onmessage	type=message	data=" 앞 공백 둘"	lastEventId="7"
(exit 0)
```

- **`event: tick` 블록은 `onmessage` 가 아니라 `tick` 리스너로만** 왔다(`type=tick`). 이름 없는 블록은 `type=message`.
- **`data:` 두 줄은 `\n` 으로 이어 한 이벤트**가 됐다(`"한 줄\n두 줄"`).
- ★ **`id: 7` 만 있는 블록은 이벤트를 안 냈다** — 그런데 **그 뒤 이벤트들의 `lastEventId` 가 `"7"`** 이 됐다. 책갈피만 옮긴 블록이다.
- ★ **콜론 뒤 공백은 하나만 떼였다** — `data:앞 공백 없음` → `"앞 공백 없음"`, `data:  앞 공백 둘` → `" 앞 공백 둘"`.
- ★★ **빈 줄 없이 끝난 마지막 블록(`id: 8`)은 아예 안 왔다.** 블록은 **빈 줄이 와야 한 이벤트로 끝난다** — 서버가 마지막 이벤트 뒤에 빈 줄을 안 쓰고 끊으면 **그 이벤트는 조용히 사라진다.**
- **주석 줄(`:` 로 시작)은 아무것도 안 냈다** — 연결을 살려 두는 심장 박동으로 쓰는 자리다.

```text
   한 응답 안의 블록 → 이벤트 (이 판)

   : 주석                          → (없음)
   data: 첫째 ⏎⏎                   → message "첫째"
   event: tick ⏎ data: … ⏎⏎        → tick 리스너만
   data: 한 줄 ⏎ data: 두 줄 ⏎⏎     → message "한 줄\n두 줄"
   id: 7 ⏎⏎                        → (없음) · 이후 lastEventId = "7"
   … data: 마지막 ⏎ (빈 줄 없이 끊김) → ✕ 안 옴
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   브라우저   const es = new EventSource(url, { withCredentials })
              es.readyState   0 CONNECTING · 1 OPEN · 2 CLOSED
              es.onopen · es.onmessage · es.onerror · es.addEventListener("이름", f)
              es.close()                               ← 앱이 멈추는 유일한 방법
   서버 응답  200 · Content-Type: text/event-stream
              한 블록 = 줄들 + 빈 줄
                data: 값      (여러 줄이면 \n 으로 잇는다)
                event: 이름   (없으면 message)
                id: 값        (책갈피 — 다시 붙을 때 Last-Event-ID 로 온다)
                retry: ms     (재연결 간격)
                : 주석
   멈추기     서버 — 204 · 오류 코드 · 다른 Content-Type   /   앱 — es.close()
```

### 어디서 헷갈리나

- **`onerror` 는 「끝났다」가 아니다** — 대개 `readyState` 가 **0 으로 돌아가 다시 붙는 중**이다((2)). 끝났는지는 `readyState === 2` 로 본다.
- **`event:` 를 붙이면 `onmessage` 로 안 온다**((4)).
- **`Last-Event-ID` 는 브라우저가 보내지만, 이어 주는 것은 서버다**((2)).

## 어디서 틀리나

### 1. 「`EventSource` 는 알아서 다시 붙으니 이벤트를 안 잃는다」

**12칸 중 10칸이 잃거나 겹쳤다**((2)). 다시 붙는 것은 브라우저가 하지만, **어디서부터 보낼지는 서버가 정한다.** `id:` 를 붙이고 · 서버가 `Last-Event-ID` 다음부터 보내야 둘 다 0 이다.

### 2. 서버가 이벤트에 `id:` 를 안 붙인다

**다시 붙은 요청에 헤더가 없다**((2)) — 서버가 이어 주고 싶어도 어디서 이을지 모른다.

### 3. 서버가 끝났다는 뜻으로 연결을 그냥 닫는다

**다시 붙는다**((3)) — 닫힌 스트림은 끊김으로 읽힌다. 끝을 알리려면 **다시 온 요청에 204**를 준다(또는 앱이 `es.close()`).

### 4. 잠깐 장애라 500 을 주면 브라우저가 알아서 다시 올 것이라 믿는다

**500 에서는 안 다시 왔다**((3)). 그 연결은 거기서 끝나고, 되살리는 것은 앱 코드의 몫이 된다.

### 5. 응답 `Content-Type` 을 `text/plain` 으로 둔다(프레임워크 기본값)

**`error` 하나로 닫힌다** — 콘솔에만 이유가 있다((3)).

### 6. 마지막 이벤트 뒤에 빈 줄을 안 쓰고 끊는다

**그 이벤트가 사라진다**((4)) — 에러도 경고도 없다.

### 7. `onerror` 에서 「실패했다」고 알리고 새 `EventSource` 를 만든다

**브라우저도 다시 붙는 중이라 연결이 둘이 된다** — `readyState` 가 0 이면 기다리고, **2 일 때만** 앱이 나선다((2)의 전이).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 끊기면 다시 붙고 `Last-Event-ID` 에 마지막 `id` 를 싣는다 | ★ **이 판의 관찰** — 명세 원문은 열지 못했다 |
| `retry:` 가 재연결 간격을 바꾼다 | ★ **이 판의 관찰**(1000ms 참/거짓) |
| 204 · 500 · `text/plain` 은 재연결 없이 닫힌다 · `charset` 이 붙은 `text/event-stream` 은 된다 | ★ **이 판의 관찰** — 콘솔 문구는 Chrome 의 것 |
| 헤더 없이 한 번 끊으면 `error` 없이 곧바로 다시 온다 | ★ **이 판의 관찰 — 그 아래 층의 재시도로 읽힌다.** 어느 층인지 재지 않았다 |
| 블록은 빈 줄로 끝나야 이벤트가 된다 · `event:` · 여러 줄 `data:` · 공백 하나 떼기 | ★ **이 판의 관찰** |
| **이어 보낼지는 서버가 정한다** | **설계** — 브라우저가 하는 일은 헤더를 싣는 데서 끝났다((2)) |
| 기본 재연결 간격 · 교차 출처 · 연결 수 한도 | ★ **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 서버 → 브라우저 한 방향 알림 · 진행 상황 · 시세 | `EventSource` + `id:` + `Last-Event-ID` 를 존중하는 서버 | `id:` 없이 보내기 |
| 끝났음을 알리기 | 다시 온 요청에 **204** · 또는 앱이 `es.close()` | 그냥 닫기(다시 붙는다) |
| 끊긴 동안의 것을 잃으면 안 된다 | 서버가 **`id` 로 다시 찾을 수 있게 보관** · 「이어 보냄」 | 「현재부터」(지나간 것은 없다) |
| 브라우저 → 서버로도 자주 말해야 | [33번 주제](../33-websocket/2-summary.md) WebSocket | SSE + 요청마다 `fetch`(두 통로를 따로 관리) |
| 응답을 청크로 직접 다뤄야(요청 본문 · 헤더를 직접) | [26번 주제](../26-response-body-streaming/2-summary.md) `fetch` 스트리밍 | `EventSource`(요청 메서드·헤더를 고를 수 없다) |

- ★ **「가볍다」로 고르지 마라** — 이 편은 비용을 재지 않았다. 고르는 근거는 **방향**(한 방향이면 SSE)과 **재연결을 누가 하나**(SSE 는 브라우저, WebSocket 은 앱)다.

## 핵심 문장

1. **`EventSource` 는 끊기면 알아서 다시 붙고, 마지막 `id` 를 `Last-Event-ID` 로 들고 온다** — 거기까지가 브라우저의 일이다.
2. **유실·중복을 없애는 것은 서버다** — 12칸 중 10칸이 잃거나 겹쳤고, 0 인 칸은 `id:` + 「이어 보냄」뿐이었다.
3. **`retry:` 는 간격을 바꾸고 번호는 안 바꾼다.**
4. **다시 붙게 하는 것은 「열렸다가 끊김」이고, 멈추게 하는 것은 204 · 오류 코드 · 다른 `Content-Type`** 이다.
5. **빈 줄로 끝나지 않은 마지막 블록은 조용히 사라진다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 32번)
- [25번 주제](../25-fetch-request-response/2-summary.md) — 「서버 요청 로그」 창과 상태 코드. 여기는 그 창을 **여러 번 오는 연결**에 쓴다
- [26번 주제](../26-response-body-streaming/2-summary.md) — `fetch` 본문을 직접 청크로 읽는 쪽. 여기는 **브라우저가 파싱하고 다시 붙는** 쪽
- [28번 주제](../28-cors-simple-and-preflight/2-summary.md) · [29번 주제](../29-credentials-and-cookies/2-summary.md) — 교차 출처 · 쿠키. 여기서는 재지 않았다
- [33번 주제](../33-websocket/2-summary.md) — 양방향 · 재연결을 앱이 하는 쪽
- [`../../../../history/web/05-웹플랫폼-API.md`](../../../../history/web/05-웹플랫폼-API.md) §4 — 통신 API 의 연혁. 그쪽은 **WebSocket 이 왜 들어왔나**까지이고 **서버 보내기 이벤트 절은 아직 없다.** 여기는 **끊겼을 때 무엇이 남나**

## 용어 풀이

- **서버 보내기 이벤트(SSE)** — `text/event-stream` 응답을 끝내지 않고 이어 쓰는 방식. 브라우저 쪽 객체가 `EventSource`.
- **블록** — 빈 줄로 끝나는 줄 묶음. 한 블록이 이벤트 하나가 된다(`data:` 가 있을 때).
- **`id:` · last event ID** — 이벤트의 책갈피. 브라우저가 기억했다가 다시 붙을 때 `Last-Event-ID` 요청 헤더로 보낸다.
- **`retry:`** — 재연결 간격(밀리초).
- **재연결 · 유실 격자** — 끊김 한 번을 `id:` · `retry:` · 서버 방식 12칸으로 바꿔 받은 번호와 헤더를 대조한 표. 이 편의 본체.
- **이어 보냄 / 처음부터 / 현재부터** — 다시 붙은 요청을 서버가 다루는 세 방식(이 편이 서버 쪽에 만든 스위치).

## 더 들어가면

- ★★ **명세 원문 대조** — [HTML 의 server-sent events 절](https://html.spec.whatwg.org/multipage/server-sent-events.html)을 열어 **204 · 오류 코드 · `Content-Type` 거절 · 재연결 · 빈 줄 규칙**이 명세 문장인지 확인하는 일이 남았다. 이 편의 관찰이 명세대로인지 **판정하지 않았다.**
- **교차 출처 `EventSource`**(`withCredentials`) — 28·29편의 규칙이 그대로인지 던지지 않았다.
- **연결 수 한도 · bfcache · 숨긴 탭** — 던지지 않았다.
