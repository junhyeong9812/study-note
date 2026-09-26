# web-api/28 — CORS: 단순 요청과 프리플라이트, 막는 것과 못 막는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「서버 요청 로그」 — 서버 B 가 받은 순서(OPTIONS 가 먼저 왔나)를 칸마다 서버에게 묻는 「프리플라이트 격자」다.** 메서드 4 × `Content-Type` 4 × 커스텀 헤더 2 = 32칸을 다른 출처로 던지고, 마지막 줄을 스크립트가 「OPTIONS 가 먼저 온 칸 N / 32」로 찍는다. 그 옆에 **프리플라이트가 거부되면 본 요청이 서버에 가나**를 서버 로그로 싣는다.\
> **기준 소스** — [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 「CORS-safelisted method」(**`GET`·`HEAD`·`POST`**) · 「CORS-safelisted request-header」(값이 **128바이트를 넘으면 거짓** · `content-type` 은 파싱한 MIME 의 본질이 **`application/x-www-form-urlencoded`·`multipart/form-data`·`text/plain`** 일 때만) · main fetch 의 프리플라이트 조건(「**use-CORS-preflight flag** 가 켜졌거나, unsafe-request flag 가 켜졌고 메서드가 안전 목록이 아니거나 **CORS-unsafe request-header names 가 비지 않았을 때**」) · 요청 절(「use-CORS-preflight flag 는 … **`ReadableStream` 을 요청에 쓰면** 켜진다」) · HTTP fetch 의 「**If preflightResponse is a network error, then return** preflightResponse」 · CORS-preflight fetch(OPTIONS 에 `Access-Control-Request-Method`·`-Headers` 를 싣는다 · 「CORS check 가 성공하고 **status 가 ok status** 여야」 · 메서드·헤더 목록 검사) · CORS-preflight cache(「max-age 가 없으면 **5**」 · 「imposed limit」) · 「CORS-safelisted response-header name」 · 「opaque filtered response」(**status 0 · header list 비움 · body null**) · Request 생성자(「mode 가 `no-cors` 인데 메서드가 안전 목록이 아니면 **TypeError**」 · 스트림 본문에 「`duplex` 가 없으면 TypeError」·「mode 가 `same-origin`·`cors` 가 아니면 TypeError」) · 요청 출처 직렬화(「redirect-taint 가 `same-origin` 이 아니면 **`"null"`**」). 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 페이지는 **서버 A**(`http://127.0.0.1`)에서 열었고 다른 출처는 **같은 기계의 다른 포트인 서버 B** 다. **바깥 인터넷으로는 한 번도 요청하지 않았다.** 하네스의 Chrome·CDP 쪽은 [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1)을 그대로 빌려 쓰고, **서버만 새로 세웠다**((1)).\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★★ **[25번 주제](../25-fetch-request-response/2-summary.md)의 (1)·(2)가 「막는 것은 응답 읽기」를 한 칸 쟀다** — 허용 헤더 없는 다른 출처 `POST` 가 페이지에서는 `TypeError 「Failed to fetch」` 인데 **서버 B 로그에는 「주문을 처리했다 · 200 을 보냈다 · 허용 헤더 없음」**, 이유는 콘솔에만. 여기서는 **그 칸을 다시 재지 않고 인용**한다. 이 편은 그 칸이 **언제 성립하고 언제 안 성립하나** — 프리플라이트가 붙으면 본 요청은 서버에 **가지도 않는다** — 로 넓힌다.\
> **경계** — ★ **보안 모델(CSRF 방어 설계·신뢰 경계)은 [`../../security/`](../../security/) 가 정본으로 걸려 있다.** 단 2026-09-26 현재 그 폴더는 해시·HMAC·OIDC·JWKS·신원·롤아웃 여섯 편이고 **CORS·CSRF 를 다루는 절은 없다**(`cors`·`csrf` 로 `grep` 해 0건). 그래서 여기는 **브라우저가 무엇을 막고 무엇을 못 막는지의 관찰**까지만 적고, 방어 설계는 그쪽이 생기면 넘긴다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome · Go**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

```text
$ go version
go version go1.27.1 linux/amd64
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 격자 32칸 · 격자 밖 여덟 칸 · 프리플라이트 거부 · `Max-Age` 세 판 · 노출 헤더 · `no-cors` · 리다이렉트 · Go 대비 · 콘솔 문구 | 캡처 세 판이 **한 글자도 같았다** |
| ★ **시간에 기댄 칸 하나** | `Max-Age` 헤더 **없음** 칸의 「OPTIONS 1번」 | 명세의 기본값은 **5초**다. 두 PUT 이 5초 안에 연달아 나갔기 때문에 캐시가 답했다. 루프백에서 넉넉하다 — 캡처 세 판 × 블록 안 세 판 모두 같았다 |
| **흔들린다** | Chrome·Go 판 번호 · 포트 | 포트는 출력에 안 나온다(`<A>`·`<B>` 로 바꿔 적는다) |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `res.status` · `res.type` · `res.headers.get()` · 오류 이름 |
| 창 ③ 같은 것을 두 번 읽기 | ★★ **쓴다** | **같은 주소에 같은 PUT 두 번** — 두 번째에 OPTIONS 가 또 오나((5)) |
| **창 ④ 서버 요청 로그 — 서버가 받은 순서** | ★★★ **본체** | OPTIONS 가 **먼저 왔나** · 본 요청이 **왔나** · `Access-Control-Request-*` 에 무엇이 실렸나 |
| ★ **「프리플라이트가 났나」를 페이지 대신 서버에게** | ★★ **같은 질문을 다른 창으로(제5의 상태)** | 페이지는 프리플라이트를 **볼 수 없다** — `then`/`catch` 만 받는다. 그래서 칸마다 **서버 B 에게 `/seen` 으로 물었다.** ★ 바꾼 창이 못 보는 것 — **브라우저 캐시가 답한 프리플라이트는 서버에 안 온다.** 「OPTIONS 가 안 왔다」가 **「안 보냈다」인지 「캐시가 답했다」인지**는 서버 창만으로는 못 가른다((5)은 같은 주소의 첫 번째가 왔다는 것으로 가른다) |
| 콘솔(CDP Log 도메인) | ★★ **쓴다** | `catch` 가 **말해 주지 않는** 거부 이유 |
| Go `net/http` 클라이언트 | ★ **대비** | 브라우저가 아닌 클라이언트는 **CORS 를 모른다**((9)) |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★ **프리플라이트가 드는 시간** | **재지 않았다.** 「왕복이 한 번 더 붙는다」는 서버 로그의 **줄 수**로만 봤다 — 지연이 몇 배인지는 이 판으로 말할 수 없다 |
| **HTTP/2 에서의 스트림 본문 업로드** | 이 서버는 HTTP/1.1 이다 — 스트림 본문은 **프리플라이트까지만 가고 본 요청은 `ERR_ALPN_NEGOTIATION_FAILED`** 였다((3)). HTTP/2 서버에서 본 요청이 어떻게 되는지는 못 봤다 |
| **`Max-Age` 의 상한** | 명세는 「imposed limit」 만 말한다. **이 판이 몇 초에서 자르는지는 재지 않았다**(600초는 두 요청 사이를 넘지 않는다) |
| **Private Network Access 같은 추가 검사** | 페이지도 서버도 루프백이라 그런 검사가 걸릴 자리가 없다 |

## 한눈에 — 쉽게 말하면

**★ CORS 는 「문지기가 답장을 읽을지 말지를 정하는 규칙」이다. 편지(단순 요청)는 그냥 부치고, 돌아온 답장에 「이 사람에게 보여 줘도 된다」는 도장이 없으면 페이지에게 안 보여 준다 — 편지는 이미 도착해 처리됐다. 다만 수상한 편지(PUT · 커스텀 헤더 · JSON)는 부치기 전에 「이런 편지를 보내도 되나」 하는 쪽지(프리플라이트)를 먼저 보내고, 답이 안 되면 편지를 아예 안 부친다.**

| 비유 | 실체 |
|---|---|
| 그냥 부치는 편지 | 단순 요청 — `GET`·`HEAD`·`POST` + 안전 목록 헤더뿐 |
| 답장에 찍힌 도장 | `Access-Control-Allow-Origin` |
| 도장 없으면 안 보여 줌 | CORS 거부 — **서버는 이미 처리했다**(25편) |
| 먼저 보내는 쪽지 | 프리플라이트 `OPTIONS` + `Access-Control-Request-Method`·`-Headers` |
| 쪽지 답이 「안 됨」 | **본 요청을 아예 안 보낸다** — 서버 로그에 OPTIONS 한 줄뿐 |
| 쪽지 답을 기억하는 기간 | `Access-Control-Max-Age` |
| 답장 중 보여 줄 칸 | `Access-Control-Expose-Headers` |

```text
   ★ 두 갈래 — 같은 「허용 안 됨」인데 서버가 겪은 일이 다르다 (이 판)

   단순 요청(POST text/plain)           프리플라이트가 붙는 요청(PUT)
   ────────────────────────────         ────────────────────────────────────
   페이지 ──POST──▶ 서버 B               페이지 ──OPTIONS──▶ 서버 B
                    처리했다 ★                                 답: 허용 없음
          ◀── 200 (도장 없음)                   ✕ 본 요청 안 감 ★
   catch TypeError                       catch TypeError
   서버 로그: POST 한 줄(25편)           서버 로그: OPTIONS 한 줄뿐((4))
```

## 이 주제가 답하려는 질문

1. **무엇이 프리플라이트를 부르나** — 메서드 · `Content-Type` 의 값 · 커스텀 헤더 · 본문의 종류.
2. **프리플라이트가 거부되면 서버에서 무슨 일이 있었나** — 25편의 「처리는 됐다」와 무엇이 다른가.
3. **프리플라이트 뒤의 규칙** — 답을 기억하는 기간 · 읽을 수 있는 응답 헤더 · `no-cors` · 리다이렉트.

## 동작 방식

### (1) 하네스 — 24편 하네스에 서버만 새로

**Chrome 을 띄우고 CDP 로 붙는 부분은 [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1) 전문을 한 글자도 안 바꾸고 `import` 한다.** 새로 세운 것은 서버다 — 28\~31 네 편이 같이 쓴다.

- **`/cors`**(28) — `OPTIONS` 에는 질의로 고른 답(`pf=ok`·`noacao`·`nomethod`·`redirect` · `ma=` 로 `Max-Age`)을 주고, 본 요청에는 `Access-Control-Allow-Origin`(기본은 **요청의 `Origin` 을 그대로**)과 `X-Secret`·`Content-Language` 를 붙여 준다.
- **`/seen?id=`** — 그 `id` 로 **무엇이 어떤 순서로 왔나**를 돌려준다. 페이지는 이것으로 **서버에게 물어** 격자를 채운다(로그에는 안 적는다).
- **`/c29`·`/setcookie`·`/note`**(29) · **`/echo`**(30·31 — 받은 `Content-Type`·본문 원문·직접 짠 multipart 파서의 결과).
- ★ 서버는 **IPv4·IPv6 둘 다** 받는다 — 29편이 `localhost` 로 부르기 때문이다. ★ 로그를 찍기 전에 **처리 중인 요청이 0 이 되기를 기다린다**(25편에서 잡은 흔들림).

```python
# wa28b-net.py
#!/usr/bin/env python3
"""web-api 28~31 — 24편 하네스(wa24b-net.py)의 Chrome·CDP 부분을 그대로 빌려 쓰고, 서버만 새로 세운다.

사용:
  wa28b-net.py page <html>          A 에서 그 페이지를 열고 window.__끝() 이 돌려준 글 → 서버 로그
  wa28b-net.py console <html>       page 와 같고, 서버 로그 앞에 콘솔(Log 도메인) 줄을 찍는다
  wa28b-net.py quiet <html>         page 와 같고, 서버 로그를 안 찍는다(페이지가 /seen 으로 물은 것만)
  wa28b-net.py cookie <html> [3p-block]
                                    29편 — 먼저 B 를 두 이름(127.0.0.1 · localhost)으로 한 번씩 「직접」 열어
                                    쿠키를 받게 한 뒤, A 에서 그 페이지를 연다(콘솔 · 서버 로그까지).
                                    3p-block 이면 그 탭에서 서드파티 쿠키를 막고 연다 ·
                                    compare 면 그대로 한 번 · 막고 한 번 돌려 갈린 줄만 찍는다
  wa28b-net.py form <html> <파일>   30편 — 파일 입력에 <파일> 을 넣고 __끝() 을 부른 뒤, 페이지의 폼을 제출시킨다
  wa28b-net.py blob <html> <파일>   31편 — 파일 입력에 <파일> 을 넣고 __끝() → 내려받기 → 다른 탭 · 떠난 뒤 · 닫은 뒤
  wa28b-net.py urllib               30편 대비 — 파이썬 urllib 로 A 의 /echo 에 본문 셋을 보낸다
  wa28b-net.py py                   30편 대비 — urllib 셋 + 파이썬 requests 의 multipart 둘
  wa28b-net.py go <프로그램.go>     28편 대비 — Go net/http 클라이언트가 B 에 허용 헤더 없는 POST 를 보낸다

★ 포트는 전부 0 — 운영체제가 고른다. 출력에는 서버 이름(A·B)만 쓰고 포트는 <A>·<B> 로 적는다.
★ 서버는 IPv4·IPv6 둘 다 받는다 — 「localhost」 로 부르면 브라우저가 ::1 로 먼저 올 수 있다.
★ 서버 로그 — 엔드포인트 요청만 적는다(페이지 파일·/seen 은 안 적는다).
  로그를 찍기 전에 처리 중인 요청이 0 이 되기를 기다린다(24편에서 잡은 흔들림).
★ multipart 경계(boundary)는 Chrome 이 판마다 새로 만든다 — 로그에 싣기 전에 뒤 16자를 <16자> 로 바꾼다.
"""
import http.server, importlib.util, json, os, re, shutil, socket, subprocess, sys, threading, time
import urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("wa24b_net", os.path.join(HERE, "wa24b-net.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
base.PROF = os.path.join(HERE, f".prof-wa28b-{os.getpid()}")
base.FLAGS = [f"--user-data-dir={base.PROF}" if f.startswith("--user-data-dir=") else f for f in base.FLAGS]
DL = os.path.join(HERE, f".dl-wa28b-{os.getpid()}")      # 31 — 내려받은 파일이 떨어지는 곳
WAIT = 30

LOG, LOCK = [], threading.Lock()
COND = threading.Condition(LOCK)
SEEN = {}                      # id → [그 id 로 온 요청의 메서드, ...]
NOTE = {}                      # id → 29 — 서버가 받은 쿠키 · 30 — 받은 Content-Type 과 파싱 결과
RAW = {}                       # id → 30 — 받은 본문(경계를 가린 한 줄)
PORTS = {}
ACTIVE = 0


def log(line):
    with LOCK:
        LOG.append(line)


def hide_ports(t):
    for p_name, p in PORTS.items():
        t = t.replace(f":{p}", f":<{p_name}>")
    return t


BOUNDARY = re.compile(r"(----WebKitFormBoundary)[0-9A-Za-z]{16}")
HEX32 = re.compile(r"\b[0-9a-f]{32}\b")          # 파이썬 requests 의 경계 — 16바이트 난수의 16진 32자


def hide_boundary(t):
    return HEX32.sub("<32자>", BOUNDARY.sub(r"\1<16자>", t))


def show_bytes(b):
    """본문 바이트를 한 줄로 — 줄바꿈은 \\r\\n 으로 보이게, 그 밖의 제어 바이트는 \\xNN 으로."""
    out = []
    for ch in b.decode("utf-8", "replace"):
        if ch == "\r":
            out.append("\\r")
        elif ch == "\n":
            out.append("\\n")
        elif ord(ch) < 0x20:
            out.append("\\x%02x" % ord(ch))
        else:
            out.append(ch)
    return hide_boundary("".join(out))


def parse_multipart(ctype, body):
    """직접 가른다 — Content-Type 의 boundary 로 본문을 쪼개 칸마다 이름·filename·Content-Type·값을 읽는다."""
    m = re.search(r"boundary=([^;]+)", ctype)
    if not m:
        return "boundary 가 Content-Type 에 없다 — 가를 수 없다"
    sep = b"--" + m.group(1).strip().encode()
    parts = body.split(sep)
    if len(parts) < 3 or not parts[-1].startswith(b"--"):
        return "boundary 로 갈라지지 않는다"
    got = []
    for p in parts[1:-1]:
        head, _, value = p.strip(b"\r\n").partition(b"\r\n\r\n")
        h = head.decode()
        name = re.search(r'name="([^"]*)"', h)
        fn = re.search(r'filename="([^"]*)"', h)
        ct = re.search(r"Content-Type: (.*)", h)
        binary = fn and ct and not ct.group(1).strip().startswith("text/")
        got.append((name.group(1) if name else "?") + ("[filename=" + fn.group(1) + "]" if fn else "")
                   + ("[" + ct.group(1).strip() + "]" if ct else "") + "="
                   + (f"<{len(value)}바이트>" if binary else value.decode("utf-8", "replace")))
    return "칸 %d개 · " % len(got) + " · ".join(got)


def parse_body(ctype, body):
    essence = ctype.split(";")[0].strip().lower()
    try:
        if essence == "multipart/form-data":
            return parse_multipart(ctype, body)
        if essence == "application/x-www-form-urlencoded":
            return "칸 " + json.dumps(urllib.parse.parse_qsl(body.decode(), keep_blank_values=True), ensure_ascii=False)
        if essence == "application/json":
            return "JSON " + json.dumps(json.loads(body), ensure_ascii=False)
        if essence.startswith("text/"):
            return "글 「" + body.decode() + "」"
        return "(Content-Type 으로 고를 파서 없음)"
    except Exception as e:
        return "파싱 실패 " + type(e).__name__


def server(name):
    class H(http.server.SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def __init__(self, *a, **k):
            super().__init__(*a, directory=HERE, **k)

        def log_message(self, *a):
            pass

        def q(self):
            u = urllib.parse.urlsplit(self.path)
            return u.path, dict(urllib.parse.parse_qsl(u.query))

        def shown(self):
            path, qs = self.q()
            rest = "&".join(f"{k}={v}" for k, v in qs.items())
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

        def origin(self):
            return self.headers.get("Origin")

        def acao(self, qs):
            """acao=none(붙이지 않음) · star(*) · origin(요청의 Origin 을 그대로) — 기본은 origin."""
            how = qs.get("acao", "origin")
            if how == "star":
                return [("Access-Control-Allow-Origin", "*")]
            if how == "origin" and self.origin():
                return [("Access-Control-Allow-Origin", self.origin())]
            return []

        # ------------------------------------------------------------ 요청 받기
        def do_OPTIONS(self):
            self.route("OPTIONS")

        def do_GET(self):
            self.route("GET")

        def do_POST(self):
            self.route("POST")

        def do_PUT(self):
            self.route("PUT")

        def do_DELETE(self):
            self.route("DELETE")

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
                    got = list(SEEN.get(i, []))
                return self.reply(200, json.dumps(got).encode(), extra=[("Access-Control-Allow-Origin", "*")])
            if path == "/note":                    # 29 — 그 id 의 요청에 실려 온 쿠키 — 로그에 안 적는다
                with LOCK:
                    got = NOTE.get(i, "(요청 안 옴)")
                return self.reply(200, json.dumps(got, ensure_ascii=False).encode(),
                                  extra=[("Access-Control-Allow-Origin", "*")])
            if path in ("/cors", "/c29", "/echo", "/setcookie"):
                with LOCK:
                    SEEN.setdefault(i, []).append(method)
                return getattr(self, path[1:])(method, qs)
            if method == "GET":
                return super().do_GET()
            return self.reply(405)

        # ------------------------------------------------------------ 28 — 프리플라이트
        def cors(self, method, qs):
            data = self.body()
            o = hide_ports(self.origin() or "(없음)")
            if method == "OPTIONS":
                log(f"{name} OPTIONS {self.shown()}  Origin={o}"
                    f" · Access-Control-Request-Method={self.headers.get('Access-Control-Request-Method', '(없음)')}"
                    f" · Access-Control-Request-Headers={self.headers.get('Access-Control-Request-Headers', '(없음)')}")
                pf = qs.get("pf", "ok")
                if pf == "redirect":
                    return self.reply(307, extra=[("Location", "/cors?id=" + qs.get("id", "") + "-pf")])
                extra = [] if pf == "noacao" else [("Access-Control-Allow-Origin", self.origin() or "*")]
                extra.append(("Access-Control-Allow-Methods", "GET" if pf == "nomethod" else "GET, POST, PUT, DELETE"))
                extra.append(("Access-Control-Allow-Headers", "content-type, x-a"))
                if "ma" in qs:
                    extra.append(("Access-Control-Max-Age", qs["ma"]))
                return self.reply(204, extra=extra)
            log(f"{name} {method} {self.shown()}  Origin={o}"
                f" · Content-Type={self.headers.get('Content-Type', '(없음)')}"
                f" · X-A={self.headers.get('X-A', '(없음)')} · 본문 {len(data)}바이트"
                + (" → 처리하지 않고 307 을 보냈다" if "redir" in qs else " → 처리했다"))
            if "redir" in qs:                      # 본 요청에 307 — 다음 자리는 redir 로 고른 서버
                to = f"http://127.0.0.1:{PORTS[qs['redir']]}/cors?id={qs.get('id', '')}-2"
                return self.reply(307, extra=[("Location", to)] + self.acao(qs))
            extra = self.acao(qs) + [("X-Secret", "s1"), ("Content-Language", "ko")]
            if "expose" in qs:
                extra.append(("Access-Control-Expose-Headers", qs["expose"]))
            return self.reply(200, b'{"cors":"ok"}', extra=extra)

        # ------------------------------------------------------------ 29 — 쿠키
        def setcookie(self, method, qs):
            """B 를 주소창으로 직접 연 것처럼 — 쿠키 넷을 준다."""
            cookies = ["lax=1; Path=/; SameSite=Lax",
                       "none=1; Path=/; SameSite=None; Secure",
                       "nosec=1; Path=/; SameSite=None",
                       "plain=1; Path=/"]
            page = b"<!DOCTYPE html><meta charset='utf-8'><title>set</title>"
            return self.reply(200, page, "text/html; charset=utf-8", [("Set-Cookie", c) for c in cookies])

        def c29(self, method, qs):
            ck = self.headers.get("Cookie")
            got = " ".join(sorted(ck.replace(";", " ").split())) if ck else "(쿠키 없음)"
            if method == "OPTIONS":
                log(f"{name} OPTIONS {self.shown()}  Cookie={got}")
                return self.reply(204, extra=self.acao(qs) + [("Access-Control-Allow-Headers", "x-a")]
                                  + ([("Access-Control-Allow-Credentials", "true")] if qs.get("acac") else []))
            with LOCK:
                NOTE[qs.get("id", "")] = got
            log(f"{name} {method} {self.shown()}  Origin={hide_ports(self.origin() or '(없음)')} · Cookie={got}")
            extra = self.acao(qs) + ([("Access-Control-Allow-Credentials", "true")] if qs.get("acac") else [])
            return self.reply(200, json.dumps({"cookie": got}).encode(), extra=extra)

        # ------------------------------------------------------------ 30 · 31 — 본문 받기
        def echo(self, method, qs):
            data = self.body()
            ct = self.headers.get("Content-Type", "(없음)")
            parsed = parse_body(ct, data)
            with LOCK:
                NOTE[qs.get("id", "")] = {"ct": hide_boundary(ct), "parse": parsed}
                RAW[qs.get("id", "")] = hide_boundary(show_bytes(data))
            log(f"{name} {method} {self.shown()}  Content-Type={hide_boundary(ct)} · 본문 {len(data)}바이트")
            if qs.get("raw") == "1":
                log(f"    원문 = {show_bytes(data)}")
            log(f"    서버 파싱 → {parsed}")
            if qs.get("save"):                     # 31 — 받은 바이트를 파일로(원본과 견준다)
                with open(os.path.join(DL, qs["save"]), "wb") as f:
                    f.write(data)
            page = b"<!DOCTYPE html><meta charset='utf-8'><title>echo</title>received"
            return self.reply(200, page, "text/html; charset=utf-8")

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


def wait_for(pred):
    with COND:
        return COND.wait_for(pred, timeout=WAIT)


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


# -------------------------------------------------------------------- CDP 도우미
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


def close_tab(c, tid):
    c.send("Target.closeTarget", {"targetId": tid})
    c.wait("Target.detachedFromTarget")


def set_files(c, sid, path):
    r = c.send("Runtime.evaluate", {"expression": "document.querySelector('input[type=file]')"}, sid)
    c.send("DOM.setFileInputFiles", {"files": [path], "objectId": r["result"]["objectId"]}, sid)


def quiet_frames(c, sid, n=3):
    """프레임이 n 번 연달아 올 때까지 — 앞선 태스크(이미지 디코드·이벤트)가 가라앉게."""
    base.evaluate(c, sid, "new Promise(r => { let k = %d; const f = () => --k ? requestAnimationFrame(f) : r(); "
                          "requestAnimationFrame(f); })" % n)


# -------------------------------------------------------------------- 모드
def mode_cookie(c, a_url, page, block=False):
    for host in ("127.0.0.1", "localhost"):            # B 를 두 이름으로 직접 연다 — 퍼스트 파티로 쿠키를 받는다
        tid, sid = open_tab(c, f"http://{host}:{PORTS['B']}/setcookie")
        print(f"B 를 {host} 로 직접 열었다 → 그 자리의 쿠키 통 = "
              + json.dumps(sorted(base.evaluate(c, sid, "document.cookie").split("; "))))
        close_tab(c, tid)
    with LOCK:
        LOG.clear()
    tid, sid = open_tab(c)
    if block:                                          # 이 탭에서 서드파티 쿠키를 막는다(CDP 가 주는 스위치)
        c.send("Network.enable", sid=sid)
        c.send("Network.setCookieControls", {"enableThirdPartyCookieRestriction": True,
               "disableThirdPartyCookieMetadata": True, "disableThirdPartyCookieHeuristics": True}, sid)
        print("이 탭 — Network.setCookieControls(enableThirdPartyCookieRestriction: true)")
    base.goto(c, sid, a_url + page)
    print(base.evaluate(c, sid, "window.__끝()"))
    print_console(c, sid)
    print_log()


def mode_cookie_compare(c, a_url, page):
    """같은 격자를 두 탭에서 — 그대로 한 번, 서드파티 쿠키를 막고 한 번. 갈린 줄만 찍는다."""
    for host in ("127.0.0.1", "localhost"):
        tid, sid = open_tab(c, f"http://{host}:{PORTS['B']}/setcookie")
        close_tab(c, tid)
    rows = []
    for block in (False, True):
        tid, sid = open_tab(c)
        if block:
            c.send("Network.enable", sid=sid)
            c.send("Network.setCookieControls", {"enableThirdPartyCookieRestriction": True,
                   "disableThirdPartyCookieMetadata": True, "disableThirdPartyCookieHeuristics": True}, sid)
        base.goto(c, sid, a_url + page)
        rows.append(base.evaluate(c, sid, "window.__끝()").split("\n")[1:-1])   # 머리 줄 · 마지막 합계 줄은 뺀다
        close_tab(c, tid)
    if len(rows[0]) != len(rows[1]):
        raise RuntimeError("줄 수가 어긋났다")
    moved = [(x, y) for x, y in zip(*rows) if x != y]
    for x, y in moved:
        print("그대로 " + x)
        print("막음   " + y)
    print(f"서드파티 쿠키를 막자 바뀐 칸 = {len(moved)} / {len(rows[0])}")
    with LOCK:
        LOG.clear()


def mode_form(c, a_url, page, path):
    tid, sid = open_tab(c, a_url + page)
    set_files(c, sid, os.path.join(HERE, path))
    print(base.evaluate(c, sid, "window.__끝()"))
    c.events.clear()
    base.evaluate(c, sid, "document.forms[0].requestSubmit(), 0")
    c.wait("Page.loadEventFired", sid)                # 폼 제출로 새 문서(/echo 의 응답)가 섰다
    print("폼 제출 뒤 주소 = " + hide_ports(base.evaluate(c, sid, "location.href")))
    with LOCK:
        x, y = RAW.get("fetch"), RAW.get("form")
    print(f"두 원문(경계 뒤 16자를 가린 것)이 한 글자도 같나 = {x is not None and x == y}")
    print_log()


def mode_blob(c, a_url, page, path):
    os.makedirs(DL, exist_ok=True)
    c.send("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": DL, "eventsEnabled": True})
    t1, s1 = open_tab(c, a_url + page)
    set_files(c, s1, os.path.join(HERE, path))
    print(base.evaluate(c, s1, "window.__끝()"))
    # 내려받기 — 페이지가 <a download> 를 누른다. 끝났다는 신호는 Browser.downloadProgress 의 completed
    c.events.clear()
    base.evaluate(c, s1, "window.__내려받기()")
    will = c.wait("Browser.downloadWillBegin")
    while c.wait("Browser.downloadProgress")["state"] != "completed":
        pass
    got = os.path.join(DL, will["suggestedFilename"])
    same = open(got, "rb").read() == open(os.path.join(HERE, path), "rb").read()
    print(f"내려받기 → 제안된 이름 {will['suggestedFilename']} · 떨어진 파일 {os.path.getsize(got)}바이트"
          f" · 원본과 바이트가 같나 = {same}")
    url = base.evaluate(c, s1, "window.__남긴URL")
    probe = "window.__읽기(%s)" % json.dumps(url)
    t2, s2 = open_tab(c, a_url + "wa28b-31-other.html")
    print("다른 탭(같은 출처 A) → " + base.evaluate(c, s2, probe))
    t3, s3 = open_tab(c, BASES["B"] + "/wa28b-31-other.html")
    print("다른 탭(다른 출처 B) → " + base.evaluate(c, s3, probe))
    c.events.clear()
    base.goto(c, s1, a_url + "wa28b-31-other.html")   # 첫 탭이 다른 문서로 떠난다
    print("첫 탭이 다른 문서로 떠난 뒤, 다른 탭(A) → " + base.evaluate(c, s2, probe))
    back(c, s1)                                        # 뒤로 — 떠난 문서가 그대로 되살아났나(bfcache)
    print("첫 탭에서 뒤로 → 스크립트 상태(window.__남긴URL)가 남아 있나 = "
          + str(base.evaluate(c, s1, "typeof window.__남긴URL === 'string'")))
    close_tab(c, t1)
    print("첫 탭을 닫은 뒤, 다른 탭(A) → " + base.evaluate(c, s2, probe))
    # 넷째 탭 — unload 리스너를 단 문서(24편: bfcache 에서 빠진다)가 만든 URL 을, 그 문서가 떠난 뒤에
    t4, s4 = open_tab(c, a_url + "wa28b-31-other.html")
    url4 = base.evaluate(c, s4, "addEventListener('unload', () => {}); URL.createObjectURL(new Blob(['x']))")
    print("넷째 탭(unload 리스너를 단 문서)이 만든 URL — 떠나기 전, 다른 탭(A) → "
          + base.evaluate(c, s2, "window.__읽기(%s)" % json.dumps(url4)))
    base.goto(c, s4, a_url + "wa28b-31-other.html")
    print("                                             떠난 뒤, 다른 탭(A) → "
          + base.evaluate(c, s2, "window.__읽기(%s)" % json.dumps(url4)))
    for t in (t2, t3, t4):
        close_tab(c, t)
    with open(os.path.join(DL, "up.png"), "rb") as up, open(os.path.join(HERE, path), "rb") as src:
        print(f"서버가 body: file 로 받아 저장한 바이트가 원본과 같나 = {up.read() == src.read()}")
    print_log()


def back(c, sid):
    h = c.send("Page.getNavigationHistory", {}, sid)
    c.events.clear()
    c.send("Page.navigateToHistoryEntry", {"entryId": h["entries"][h["currentIndex"] - 1]["id"]}, sid)
    base.되살아남(c, sid)


def mode_py(a_url):
    import requests
    mode_urllib(a_url, log_too=False)
    for label, head in (("files= 만", {}), ("files= + Content-Type: multipart/form-data 지정",
                                           {"Content-Type": "multipart/form-data"})):
        r = requests.post(a_url + "echo?id=py", files={"f": ("n.txt", b"x", "text/plain")}, data={"a": "1"},
                          headers=head)
        print(f"requests.post({label}) → status {r.status_code} · 보낸 Content-Type = "
              + hide_boundary(r.request.headers["Content-Type"]))
    print_log()


def mode_urllib(a_url, log_too=True):
    for label, data, head in (("urlencode 한 바이트", b"a=1&b=%ED%95%9C", {}),
                              ("JSON 바이트", json.dumps({"a": 1}).encode(), {}),
                              ("JSON 바이트 + Content-Type 지정", json.dumps({"a": 1}).encode(),
                               {"Content-Type": "application/json"})):
        req = urllib.request.Request(a_url + "echo?id=py", data=data, headers=head)
        with urllib.request.urlopen(req) as r:
            print(f"urlopen({label}) → status {r.status} · 보낸 Content-Type = {req.get_header('Content-type')}")
    if log_too:
        print_log()


def mode_go(prog):
    env = dict(os.environ, GOFLAGS="-mod=mod")
    r = subprocess.run(["go", "run", prog, f"http://127.0.0.1:{PORTS['B']}/cors?acao=none&id=go"],
                       cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env)
    print(r.stdout, end="")
    print(f"(go run exit {r.returncode})")
    print_log()


def main():
    base.signal.signal(base.signal.SIGTERM, lambda *a: sys.exit(143))
    mode = sys.argv[1]
    a, b = server("A"), server("B")
    a_url = f"http://127.0.0.1:{PORTS['A']}/"
    BASES.update(A=f"http://127.0.0.1:{PORTS['A']}", B=f"http://127.0.0.1:{PORTS['B']}",
                 B사이트밖=f"http://localhost:{PORTS['B']}")
    try:
        if mode == "urllib":
            return mode_urllib(a_url)
        if mode == "py":
            return mode_py(a_url)
        if mode == "go":
            return mode_go(sys.argv[2])
        proc, c = base.start()
        try:
            if mode in ("page", "console", "quiet"):
                tid, sid = open_tab(c, a_url + sys.argv[2])
                print(base.evaluate(c, sid, "window.__끝()"))
                if mode == "console":
                    print_console(c, sid)
                if mode != "quiet":
                    print_log()
            elif mode == "cookie":
                if sys.argv[3:] == ["compare"]:
                    mode_cookie_compare(c, a_url, sys.argv[2])
                else:
                    mode_cookie(c, a_url, sys.argv[2], sys.argv[3:] == ["3p-block"])
            elif mode == "form":
                mode_form(c, a_url, sys.argv[2], sys.argv[3])
            elif mode == "blob":
                mode_blob(c, a_url, sys.argv[2], sys.argv[3])
            else:
                sys.exit("모드는 page | console | quiet | cookie | form | blob | urllib | go")
        finally:
            base.stop(proc)
    finally:
        shutil.rmtree(DL, ignore_errors=True)
        a.shutdown()
        b.shutdown()


if __name__ == "__main__":
    main()
```

### (2) ★★★ 본체 — 프리플라이트 격자: OPTIONS 가 먼저 온 칸

**언제 쓰나** — 「같은 코드인데 어떤 요청은 OPTIONS 가 먼저 가고 어떤 요청은 안 간다」 · 「`Content-Type` 하나 바꿨더니 서버 로그가 두 줄이 됐다」일 때.

**던진 것** — 다른 출처 B 에 **메서드 4 × `Content-Type` 4 × 커스텀 헤더(없음 / `X-A: 1`) = 32칸.** B 의 `OPTIONS` 답은 **넉넉하게**(메서드 넷 · 헤더 `content-type, x-a` 허용) 해 두어서 **본 요청이 늘 나간다** — 그래야 「프리플라이트가 붙었나」만 고립된다. 칸마다 주소(`id`)가 달라 **프리플라이트 캐시가 칸끼리 안 겹친다.**

```html
<!-- wa28b-28-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>28 grid</title>
<script>
// 메서드 4 × Content-Type 4 × 커스텀 헤더 2 — 다른 출처 B 에 보내고, B 가 받은 순서를 B 에게 묻는다
// (B 의 OPTIONS 답은 넉넉하다 — 메서드 넷 · 헤더 content-type, x-a 를 허용한다. 칸마다 주소가 달라 캐시가 안 겹친다)
const 메서드 = ["GET", "POST", "PUT", "DELETE"];
const 종류 = ["text/plain", "application/x-www-form-urlencoded", "multipart/form-data", "application/json"];
const 헤더 = ["없음", "X-A"];
const 너비 = t => [...t].reduce((n, ch) => n + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const 한줄 = (칸들, 폭) => {
  if (칸들.length !== 폭.length) throw new Error("칸 수가 어긋났다");
  return 칸들.map((c, k) => k === 칸들.length - 1 ? c : c + " ".repeat(Math.max(폭[k] - 너비(c), 1))).join("");
};
window.__끝 = async () => {
  const 폭 = [8, 35, 6, 26, 0];
  const O = [한줄(["메서드", "Content-Type", "헤더", "B 가 받은 순서", "페이지"], 폭)];
  let 먼저 = 0, 칸수 = 0;
  for (const m of 메서드) for (const t of 종류) for (const h of 헤더) {
    const id = "g" + 칸수++;
    const headers = { "Content-Type": t };
    if (h === "X-A") headers["X-A"] = "1";
    const init = { method: m, headers };
    if (m !== "GET") init.body = "x";
    let 페이지;
    try { 페이지 = "status " + (await fetch(window.__B + "/cors?id=" + id, init)).status; }
    catch (e) { 페이지 = e.name; }
    const 받음 = await (await fetch("/seen?id=" + id)).json();
    if (받음[0] === "OPTIONS") 먼저++;
    O.push(한줄([m, t, h, 받음.join(" → ") || "(없음)", 페이지], 폭));
  }
  O.push("OPTIONS 가 먼저 온 칸 = " + 먼저 + " / " + 칸수);
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py quiet wa28b-28-grid.html
메서드  Content-Type                       헤더  B 가 받은 순서            페이지
GET     text/plain                         없음  GET                       status 200
GET     text/plain                         X-A   OPTIONS → GET            status 200
GET     application/x-www-form-urlencoded  없음  GET                       status 200
GET     application/x-www-form-urlencoded  X-A   OPTIONS → GET            status 200
GET     multipart/form-data                없음  GET                       status 200
GET     multipart/form-data                X-A   OPTIONS → GET            status 200
GET     application/json                   없음  OPTIONS → GET            status 200
GET     application/json                   X-A   OPTIONS → GET            status 200
POST    text/plain                         없음  POST                      status 200
POST    text/plain                         X-A   OPTIONS → POST           status 200
POST    application/x-www-form-urlencoded  없음  POST                      status 200
POST    application/x-www-form-urlencoded  X-A   OPTIONS → POST           status 200
POST    multipart/form-data                없음  POST                      status 200
POST    multipart/form-data                X-A   OPTIONS → POST           status 200
POST    application/json                   없음  OPTIONS → POST           status 200
POST    application/json                   X-A   OPTIONS → POST           status 200
PUT     text/plain                         없음  OPTIONS → PUT            status 200
PUT     text/plain                         X-A   OPTIONS → PUT            status 200
PUT     application/x-www-form-urlencoded  없음  OPTIONS → PUT            status 200
PUT     application/x-www-form-urlencoded  X-A   OPTIONS → PUT            status 200
PUT     multipart/form-data                없음  OPTIONS → PUT            status 200
PUT     multipart/form-data                X-A   OPTIONS → PUT            status 200
PUT     application/json                   없음  OPTIONS → PUT            status 200
PUT     application/json                   X-A   OPTIONS → PUT            status 200
DELETE  text/plain                         없음  OPTIONS → DELETE         status 200
DELETE  text/plain                         X-A   OPTIONS → DELETE         status 200
DELETE  application/x-www-form-urlencoded  없음  OPTIONS → DELETE         status 200
DELETE  application/x-www-form-urlencoded  X-A   OPTIONS → DELETE         status 200
DELETE  multipart/form-data                없음  OPTIONS → DELETE         status 200
DELETE  multipart/form-data                X-A   OPTIONS → DELETE         status 200
DELETE  application/json                   없음  OPTIONS → DELETE         status 200
DELETE  application/json                   X-A   OPTIONS → DELETE         status 200
OPTIONS 가 먼저 온 칸 = 26 / 32
(exit 0)
```

- ★★★ **OPTIONS 가 먼저 온 칸 26 / 32.** 안 붙은 **여섯 칸**은 전부 **`GET`·`POST` × `text/plain`·`application/x-www-form-urlencoded`·`multipart/form-data` × 헤더 없음**이다.
- ★★ **`application/json` 하나로 `GET` 도 프리플라이트가 붙는다** — 메서드가 안전해도 `Content-Type` 값이 안전 목록 밖이면 붙는다(`GET` 에는 본문이 없는데도 **헤더만으로** 붙었다).
- ★★ **`X-A` 가 붙은 16칸은 전부 붙는다** — 안전 목록 밖의 이름이면 값과 무관하다.
- ★ **`PUT`·`DELETE` 는 16칸 전부** 붙는다 — 안전한 메서드는 `GET`·`HEAD`·`POST` 뿐이다.
- ★ **`multipart/form-data` 는 boundary 가 없는데도 안전 목록**이다 — 명세는 값을 **파싱한 MIME 의 본질**만 본다(30편이 이 값을 손으로 쓰면 무엇이 깨지는지 잰다).
- 페이지 칸은 **32칸 모두 `status 200`** — 본 요청이 다 나갔고 다 읽혔다. **페이지만 봐서는 어느 칸에 왕복이 하나 더 붙었는지 모른다** — 서버에게 물어야 보인다.

```text
   ★ 프리플라이트를 부르는 세 문 — 하나라도 열리면 붙는다 (이 판 32칸)

   메서드          GET · POST ──────────── 안전        PUT · DELETE ──▶ 붙음
   Content-Type    text/plain ·
                   x-www-form-urlencoded ·
                   multipart/form-data ─── 안전        application/json ──▶ 붙음
   커스텀 헤더     없음 ────────────────── 안전        X-A ──▶ 붙음

   세 문이 모두 「안전」인 칸 = 2 × 3 × 1 = 6    나머지 26 칸 → OPTIONS 가 먼저
```

### (3) ★★ 격자 밖의 칸 — 헤더 값의 모양과 스트림 본문

**`Content-Type` 의 「값」도 검사 대상**이고, **본문의 종류만으로** 붙는 칸이 있다.

```html
<!-- wa28b-28-edge.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>28 edge</title>
<script>
// 격자 밖의 칸 — 헤더 값의 모양 · 안전 목록 헤더 · ReadableStream 본문. 다른 출처 B 에 POST 하고 B 가 받은 순서를 묻는다
const 흐름 = () => new ReadableStream({ start(c) { c.enqueue(new TextEncoder().encode("x")); c.close(); } });
const 칸 = [
  ["Content-Type: text/plain;charset=UTF-8", { headers: { "Content-Type": "text/plain;charset=UTF-8" }, body: "x" }],
  ["Content-Type: TEXT/PLAIN", { headers: { "Content-Type": "TEXT/PLAIN" }, body: "x" }],
  ["Content-Type: text/plain + 매개변수로 129바이트", { headers: { "Content-Type": "text/plain; p=" + "a".repeat(115) }, body: "x" }],
  ["Accept: application/json", { headers: { "Accept": "application/json" }, body: "x" }],
  ["Accept-Language: ko", { headers: { "Accept-Language": "ko" }, body: "x" }],
  ["본문 ReadableStream · duplex 없음", { headers: { "Content-Type": "text/plain" }, body: 흐름() }],
  ["본문 ReadableStream · duplex: 'half'", { headers: { "Content-Type": "text/plain" }, body: 흐름(), duplex: "half" }],
  ["본문 ReadableStream · mode: 'no-cors'", { headers: { "Content-Type": "text/plain" }, body: 흐름(), duplex: "half", mode: "no-cors" }],
];
window.__끝 = async () => {
  const O = [];
  let k = 0;
  for (const [이름, init] of 칸) {
    const id = "e" + k++;
    let 페이지;
    try { 페이지 = "status " + (await fetch(window.__B + "/cors?id=" + id, { method: "POST", ...init })).status; }
    catch (e) { 페이지 = e.name + " 「" + e.message + "」"; }
    const 받음 = await (await fetch("/seen?id=" + id)).json();
    O.push(이름 + "\n    B 가 받은 순서 = " + (받음.join(" → ") || "(없음)") + " · 페이지 = " + 페이지);
  }
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py console wa28b-28-edge.html
Content-Type: text/plain;charset=UTF-8
    B 가 받은 순서 = POST · 페이지 = status 200
Content-Type: TEXT/PLAIN
    B 가 받은 순서 = POST · 페이지 = status 200
Content-Type: text/plain + 매개변수로 129바이트
    B 가 받은 순서 = OPTIONS → POST · 페이지 = status 200
Accept: application/json
    B 가 받은 순서 = POST · 페이지 = status 200
Accept-Language: ko
    B 가 받은 순서 = POST · 페이지 = status 200
본문 ReadableStream · duplex 없음
    B 가 받은 순서 = (없음) · 페이지 = TypeError 「Failed to execute 'fetch' on 'Window': The `duplex` member must be specified for a request with a streaming body」
본문 ReadableStream · duplex: 'half'
    B 가 받은 순서 = OPTIONS · 페이지 = TypeError 「Failed to fetch」
본문 ReadableStream · mode: 'no-cors'
    B 가 받은 순서 = (없음) · 페이지 = TypeError 「Failed to execute 'fetch' on 'Window': If request is made from ReadableStream, mode should be"same-origin" or "cors"」
--- 콘솔 ---
network · error · Failed to load resource: net::ERR_ALPN_NEGOTIATION_FAILED
--- 서버 로그 ---
B POST /cors?id=e0  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 1바이트 → 처리했다
B POST /cors?id=e1  Origin=http://127.0.0.1:<A> · Content-Type=TEXT/PLAIN · X-A=(없음) · 본문 1바이트 → 처리했다
B OPTIONS /cors?id=e2  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=POST · Access-Control-Request-Headers=content-type
B POST /cors?id=e2  Origin=http://127.0.0.1:<A> · Content-Type=text/plain; p=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa · X-A=(없음) · 본문 1바이트 → 처리했다
B POST /cors?id=e3  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 1바이트 → 처리했다
B POST /cors?id=e4  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 1바이트 → 처리했다
B OPTIONS /cors?id=e6  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=POST · Access-Control-Request-Headers=(없음)
(exit 0)
```

- **`text/plain;charset=UTF-8` 과 대문자 `TEXT/PLAIN` 은 안전하다** — 본질이 `text/plain` 이다.
- ★★ **값이 129바이트면 붙는다** — `text/plain` 인데도 OPTIONS 가 먼저 왔다(`Access-Control-Request-Headers=content-type`). 명세의 「**값이 128바이트를 넘으면 안전 목록이 아니다**」 그대로다.
- **`Accept`·`Accept-Language` 는 안 붙는다** — 안전 목록 헤더다. ★ 서버 로그를 보면 이 둘의 `Content-Type` 은 **`text/plain;charset=UTF-8`** — 문자열 본문에 브라우저가 붙인 것이다(30편).
- ★★★ **스트림 본문은 커스텀 헤더가 없어도 붙는다** — `duplex: 'half'` 칸의 OPTIONS 에 **`Access-Control-Request-Headers=(없음)`** 이다. 붙인 이유가 헤더가 아니라 **본문의 종류**라는 증거다(명세: `ReadableStream` 을 쓰면 use-CORS-preflight flag). 그런데 **본 요청은 서버에 안 왔고** 페이지는 `TypeError 「Failed to fetch」`, 콘솔은 **`net::ERR_ALPN_NEGOTIATION_FAILED`** — 이 판의 Chrome 은 HTTP/1.1 서버로 스트림 본문을 **안 보낸다**(구현의 성질 — 명세 문장이 아니다).
- ★ **`duplex` 를 빼면 · `no-cors` 로 하면 보내기 전에 `TypeError`** 이고 서버에는 **아무것도 안 왔다** — Request 생성자 단계다.

```text
   스트림 본문 한 번 (이 판) — 붙은 이유가 헤더가 아니다

   페이지 ──OPTIONS (Request-Headers 없음)──▶ 서버 B        ← 스트림이라서 붙었다
          ◀── 204 넉넉한 답
   페이지 ──POST (스트림)──✕ ERR_ALPN_NEGOTIATION_FAILED     서버 B 로그: OPTIONS 한 줄뿐
   catch TypeError 「Failed to fetch」
```

### (4) ★★★ 프리플라이트가 거부되면 본 요청은 서버에 안 간다

**[25번 주제](../25-fetch-request-response/2-summary.md)의 (2)와 짝이다.** 거기서는 단순 `POST` 가 **처리된 뒤** 읽기만 막혔다. 여기서는 프리플라이트가 붙는 `PUT 「주문」` 을 세 가지 답으로 던진다.

```html
<!-- wa28b-28-answers.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>28 deny</title>
<script>
// 프리플라이트의 답을 셋으로 — 넉넉한 답 · 허용 출처 없는 답 · PUT 을 허용 목록에 안 넣은 답. 본 요청은 전부 PUT 「주문」
const 칸 = [
  ["가. OPTIONS 답이 넉넉함", "/cors?id=d1&pf=ok"],
  ["나. OPTIONS 답에 Access-Control-Allow-Origin 없음", "/cors?id=d2&pf=noacao"],
  ["다. OPTIONS 답의 Allow-Methods 가 GET 뿐", "/cors?id=d3&pf=nomethod"],
];
window.__끝 = async () => {
  const O = [];
  for (const [이름, 길] of 칸) {
    let 페이지;
    try { 페이지 = "then · status " + (await fetch(window.__B + 길, { method: "PUT", body: "주문" })).status; }
    catch (e) { 페이지 = "catch · " + e.name + " 「" + e.message + "」"; }
    O.push(이름 + " → " + 페이지);
  }
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py console wa28b-28-answers.html
가. OPTIONS 답이 넉넉함 → then · status 200
나. OPTIONS 답에 Access-Control-Allow-Origin 없음 → catch · TypeError 「Failed to fetch」
다. OPTIONS 답의 Allow-Methods 가 GET 뿐 → catch · TypeError 「Failed to fetch」
--- 콘솔 ---
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/cors?id=d2&pf=noacao' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/cors?id=d3&pf=nomethod' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Method PUT is not allowed by Access-Control-Allow-Methods in preflight response.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
B OPTIONS /cors?id=d1&pf=ok  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=(없음)
B PUT /cors?id=d1&pf=ok  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 6바이트 → 처리했다
B OPTIONS /cors?id=d2&pf=noacao  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=(없음)
B OPTIONS /cors?id=d3&pf=nomethod  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=(없음)
(exit 0)
```

- ★★★ **거부된 두 칸(나·다)은 서버 로그에 `OPTIONS` 한 줄뿐이다 — `PUT` 이 없다.** 주문은 서버에 **닿지도 않았다.** 25편의 「주문을 처리했다 · 허용 헤더 없음」과 정반대다. 명세 — HTTP fetch 는 **프리플라이트 응답이 network error 면 그것을 그대로 돌려주고 끝난다.**
- ★★ **페이지 쪽은 셋 다 같은 모양의 실패다** — `catch · TypeError 「Failed to fetch」`. 25편의 「처리된 뒤 막힌 칸」과 **글자가 같다.** 스크립트는 **「서버가 처리했다」와 「서버에 안 갔다」를 가를 수 없다.**
- ★ **이유는 콘솔에만, 그리고 콘솔은 둘을 가른다** — 나는 「**Response to preflight request** doesn't pass access control check: No 'Access-Control-Allow-Origin' header …」, 다는 「**Method PUT is not allowed by Access-Control-Allow-Methods** in preflight response.」.
- 넉넉한 답(가)의 `PUT` 은 `Content-Type=text/plain;charset=UTF-8` 로 닿았다 — 문자열 본문이다.

```text
   「CORS 로 막혔다」의 두 얼굴 — 서버가 겪은 일 (이 판)

                      페이지가 받은 것                 서버 로그
   25편 단순 POST     catch TypeError 「Failed to fetch」   POST · 처리했다 · 200     ★ 일어났다
   28편 PUT 거부      catch TypeError 「Failed to fetch」   OPTIONS 한 줄              ★ 안 일어났다
                      ─────────── 글자가 같다 ───────────
```

### (5) ★★ `Access-Control-Max-Age` — 두 번째 PUT 에 OPTIONS 가 또 오나

**같은 주소에 같은 PUT 을 두 번.** 프리플라이트 답의 `Max-Age` 를 세 가지로. **하네스를 세 번 새로 띄워**(브라우저·프로필이 매번 새것) 판 수로 본다.

```html
<!-- wa28b-28-maxage.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>28 maxage</title>
<script>
// 같은 주소에 같은 PUT 을 두 번 — 프리플라이트 답의 Access-Control-Max-Age 를 셋으로. B 가 OPTIONS 를 몇 번 받았나
const 칸 = [["Max-Age: 600", "m1&ma=600"], ["Max-Age: 0", "m2&ma=0"], ["Max-Age 헤더 없음", "m3"]];
window.__끝 = async () => {
  const O = [];
  for (const [이름, 뒤] of 칸) {
    for (let k = 0; k < 2; k++) await fetch(window.__B + "/cors?id=" + 뒤, { method: "PUT", body: "x" });
    const id = 뒤.split("&")[0];
    const 받음 = await (await fetch("/seen?id=" + id)).json();
    O.push(이름 + " — PUT 두 번 → B 가 받은 순서 = " + 받음.join(" → ") +
           " · OPTIONS " + 받음.filter(m => m === "OPTIONS").length + "번");
  }
  return O.join("\n");
};
</script>
```

```text
$ for k in 1 2 3; do python3 wa28b-net.py quiet wa28b-28-maxage.html; done
Max-Age: 600 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 0 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → OPTIONS → PUT · OPTIONS 2번
Max-Age 헤더 없음 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 600 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 0 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → OPTIONS → PUT · OPTIONS 2번
Max-Age 헤더 없음 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 600 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 0 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → OPTIONS → PUT · OPTIONS 2번
Max-Age 헤더 없음 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
(exit 0)
```

- ★★ **세 판 모두 같다** — `600` 은 **OPTIONS 1번**(두 번째 PUT 은 캐시가 답했다), **`0` 은 2번**(매번 묻는다), **헤더 없음도 1번**.
- ★★ **「헤더가 없으면 캐시 안 한다」가 아니다** — 명세는 **없으면 5초**다. 두 PUT 이 5초 안에 이어져서 1번이었다. **시간에 기댄 칸**이다(머리말 표).
- ★ **캐시가 답한 두 번째 OPTIONS 는 서버에 흔적이 없다** — 서버 창은 「안 왔다」만 안다. 그것을 「캐시가 답했다」로 읽는 근거는 **같은 주소의 첫 PUT 에는 OPTIONS 가 왔다**는 것이다(머리말 창 표의 제5의 상태).

```text
   같은 PUT 두 번 — 서버 B 가 받은 줄 (세 판 모두)

   Max-Age: 600    OPTIONS · PUT · ─────── PUT       ← 두 번째는 캐시가 답했다
   Max-Age: 0      OPTIONS · PUT · OPTIONS · PUT     ← 매번 묻는다
   헤더 없음       OPTIONS · PUT · ─────── PUT       ← 기본 5초 안이라 캐시
```

### (6) ★ `Access-Control-Expose-Headers` — 응답에 있어도 못 읽는 헤더

**응답 헤더는 도착했다 — 스크립트에게 보여 주지 않을 뿐이다.** B 는 세 번 다 `X-Secret: s1` 을 보냈다.

```html
<!-- wa28b-28-expose.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>28 expose</title>
<script>
// B 의 응답에는 X-Secret · Content-Language · Content-Type · Content-Length 가 실려 온다. 페이지는 무엇을 읽나
const 읽기 = async (이름, 길) => {
  const res = await fetch(window.__B + 길);
  const 값 = ["x-secret", "content-language", "content-type", "content-length"]
    .map(h => h + "=" + JSON.stringify(res.headers.get(h))).join(" · ");
  return 이름 + "\n    " + 값 + "\n    순회한 이름 = " + JSON.stringify([...res.headers.keys()]);
};
window.__끝 = async () => [
  await 읽기("가. Access-Control-Expose-Headers 없음", "/cors?id=x1"),
  await 읽기("나. Access-Control-Expose-Headers: X-Secret", "/cors?id=x2&expose=X-Secret"),
  await 읽기("다. Access-Control-Expose-Headers: *", "/cors?id=x3&expose=*"),
].join("\n");
</script>
```

```text
$ python3 wa28b-net.py page wa28b-28-expose.html
가. Access-Control-Expose-Headers 없음
    x-secret=null · content-language="ko" · content-type="application/json" · content-length="13"
    순회한 이름 = ["content-language","content-length","content-type"]
나. Access-Control-Expose-Headers: X-Secret
    x-secret="s1" · content-language="ko" · content-type="application/json" · content-length="13"
    순회한 이름 = ["content-language","content-length","content-type","x-secret"]
다. Access-Control-Expose-Headers: *
    x-secret="s1" · content-language="ko" · content-type="application/json" · content-length="13"
    순회한 이름 = ["access-control-allow-origin","access-control-expose-headers","content-language","content-length","content-type","date","server","x-secret"]
--- 서버 로그 ---
B GET /cors?id=x1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · X-A=(없음) · 본문 0바이트 → 처리했다
B GET /cors?id=x2&expose=X-Secret  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · X-A=(없음) · 본문 0바이트 → 처리했다
B GET /cors?id=x3&expose=*  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · X-A=(없음) · 본문 0바이트 → 처리했다
(exit 0)
```

- ★★ **노출 헤더가 없으면 `get('x-secret')` 은 `null`** 이고, 순회되는 이름은 `content-language`·`content-length`·`content-type` **셋뿐**이다 — 안전 목록 응답 헤더다. `Date`·`Server` 도 안 보인다.
- **`X-Secret` 을 적으면 그것만 더 보인다.** **`*` 이면 전부**(`access-control-allow-origin`·`date`·`server` 까지) — 자격 증명이 없는 요청이라 `*` 가 통했다(자격 증명이 있으면 `*` 가 안 된다는 것은 명세 예시의 문장 — 29편).
- 25편의 `Set-Cookie` 는 **금지 응답 헤더**라 같은 출처에서도 `null` 이었다. 이쪽은 **다른 출처일 때만** 걸리는 칸이다.

### (7) `mode: 'no-cors'` — 서버는 받고, 페이지는 빈 상자를 받는다

```html
<!-- wa28b-28-nocors.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>28 nocors</title>
<script>
// mode: 'no-cors' — 허용 헤더 없는 B 에 POST. 응답에서 무엇이 보이나 · 붙인 헤더는 가나 · PUT 은 되나
const 이름 = e => e.name + " 「" + e.message + "」";
window.__끝 = async () => {
  const O = [];
  const res = await fetch(window.__B + "/cors?id=n1&acao=none",
                          { method: "POST", mode: "no-cors", body: "주문 3건", headers: { "X-A": "1" } });
  O.push("가. then · type=" + res.type + " · status=" + res.status + " · ok=" + res.ok +
         " · 헤더 이름 = " + JSON.stringify([...res.headers.keys()]) + " · text() = " + JSON.stringify(await res.text()));
  try { await fetch(window.__B + "/cors?id=n2&acao=none", { method: "PUT", mode: "no-cors", body: "x" }); O.push("나. PUT → then"); }
  catch (e) { O.push("나. PUT → " + 이름(e)); }
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py page wa28b-28-nocors.html
가. then · type=opaque · status=0 · ok=false · 헤더 이름 = [] · text() = ""
나. PUT → TypeError 「Failed to execute 'fetch' on 'Window': 'PUT' is unsupported in no-cors mode.」
--- 서버 로그 ---
B POST /cors?id=n1&acao=none  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 11바이트 → 처리했다
(exit 0)
```

- ★★ **`then` 이다 — 그런데 `type=opaque · status=0 · ok=false`, 헤더 이름 `[]`, `text()` 는 `""`.** 명세의 opaque filtered response(**status 0 · 헤더 비움 · 본문 null**) 그대로다. **허용 헤더가 없는데 `catch` 가 아니다.**
- ★★★ **서버 B 는 「주문 3건」을 받아 처리했다** — 25편과 같은 모양이다. 페이지는 **성공했는지조차 모른다**(status 0).
- ★ **붙인 `X-A: 1` 은 서버에 안 왔다**(`X-A=(없음)`) — 예외도 없다. `no-cors` 의 헤더 guard 는 안전 목록 밖의 헤더를 **조용히 버린다.**
- **`PUT` 은 보내기 전에 `TypeError 「… 'PUT' is unsupported in no-cors mode.」`** — 서버 로그에 없다.

```text
   no-cors 한 번 — 페이지와 서버 B (이 판)

   페이지 ──POST 「주문 3건」 (X-A 는 버려짐)──▶ 서버 B  처리했다 ★
          ◀── 200 (허용 헤더 없음)
   then · type=opaque · status=0 · 헤더 [] · 본문 ""      ← 성공했는지도 모른다
```

### (8) ★ 리다이렉트와 프리플라이트

**프리플라이트가 붙는 `PUT`(`X-A` 헤더)** 을 셋으로. 가·나는 **본 요청**이 307 을 받고, 다는 **프리플라이트**가 307 을 받는다.

```html
<!-- wa28b-28-redirect.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>28 redirect</title>
<script>
// 프리플라이트가 붙는 PUT(X-A 헤더) — 본 요청이 307 을 받으면 · 프리플라이트가 307 을 받으면
const 칸 = [
  ["가. 본 요청이 307 → 같은 B 의 다른 주소", "/cors?id=r1&redir=B"],
  ["나. 본 요청이 307 → 페이지의 출처 A", "/cors?id=r2&redir=A"],
  ["다. 프리플라이트가 307", "/cors?id=r3&pf=redirect"],
];
window.__끝 = async () => {
  const O = [];
  for (const [이름, 길] of 칸) {
    let 페이지;
    try {
      const res = await fetch(window.__B + 길, { method: "PUT", body: "x", headers: { "X-A": "1" } });
      페이지 = "then · status " + res.status + " · redirected=" + res.redirected + " · url 의 경로 = " + new URL(res.url).pathname + new URL(res.url).search;
    } catch (e) { 페이지 = "catch · " + e.name + " 「" + e.message + "」"; }
    O.push(이름 + " → " + 페이지);
  }
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py console wa28b-28-redirect.html
가. 본 요청이 307 → 같은 B 의 다른 주소 → then · status 200 · redirected=true · url 의 경로 = /cors?id=r1-2
나. 본 요청이 307 → 페이지의 출처 A → then · status 200 · redirected=true · url 의 경로 = /cors?id=r2-2
다. 프리플라이트가 307 → catch · TypeError 「Failed to fetch」
--- 콘솔 ---
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/cors?id=r3&pf=redirect' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: Redirect is not allowed for a preflight request.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
B OPTIONS /cors?id=r1&redir=B  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
B PUT /cors?id=r1&redir=B  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=1 · 본문 1바이트 → 처리하지 않고 307 을 보냈다
B OPTIONS /cors?id=r1-2  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
B PUT /cors?id=r1-2  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=1 · 본문 1바이트 → 처리했다
B OPTIONS /cors?id=r2&redir=A  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
B PUT /cors?id=r2&redir=A  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=1 · 본문 1바이트 → 처리하지 않고 307 을 보냈다
A OPTIONS /cors?id=r2-2  Origin=null · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
A PUT /cors?id=r2-2  Origin=null · Content-Type=text/plain;charset=UTF-8 · X-A=1 · 본문 1바이트 → 처리했다
B OPTIONS /cors?id=r3&pf=redirect  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
(exit 0)
```

- ★★ **본 요청의 307 은 따라간다 — 그리고 새 주소에 프리플라이트가 또 붙는다**(가 — `r1` 에 OPTIONS·PUT, 따라간 `r1-2` 에 **또** OPTIONS·PUT). 두 주소 모두에서 서버가 PUT 을 받았다(첫 주소는 처리 없이 307 만 줬다).
- ★★ **다른 출처로 넘어갔다 돌아오면 `Origin` 이 `null` 이 된다**(나 — 페이지의 출처 A 로 돌아왔는데 A 가 받은 것은 **`Origin=null`**). 명세의 「redirect-taint 가 `same-origin` 이 아니면 `"null"`」 그대로다. 이 서버는 `Origin` 을 그대로 되돌려 주도록 짰기 때문에(`Access-Control-Allow-Origin: null`) 통과했다.
- ★ **프리플라이트가 307 이면 실패** — 콘솔 「**Redirect is not allowed for a preflight request.**」, 서버에는 OPTIONS 한 줄뿐. 명세 — 프리플라이트 응답은 **ok status**(200\~299)여야 한다.

```text
   리다이렉트 둘 — 서버가 받은 줄 (이 판)

   가. B/r1   OPTIONS · PUT(307) ─▶ B/r1-2  OPTIONS · PUT       ← 새 주소마다 다시 묻는다
   나. B/r2   OPTIONS · PUT(307) ─▶ A/r2-2  OPTIONS · PUT       ← A 가 받은 Origin = null
   다. B/r3   OPTIONS(307) ✕                                     ← 프리플라이트는 따라가지 않는다
```

### (9) 대비 — Go `net/http` 클라이언트는 CORS 를 모른다

**같은 서버 B · 허용 헤더 없음**에 브라우저가 아닌 클라이언트로 `POST` 한다.

```go
// wa28b-28-client.go
// 브라우저가 아닌 클라이언트 — 허용 헤더 없는 B 에 같은 POST 를 보내고 응답을 읽는다
package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

func main() {
	res, err := http.Post(os.Args[1], "text/plain", strings.NewReader("주문 4건"))
	if err != nil {
		fmt.Println("오류", err)
		return
	}
	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)
	fmt.Printf("status %d · Access-Control-Allow-Origin=%q · 본문 %s\n",
		res.StatusCode, res.Header.Get("Access-Control-Allow-Origin"), body)
}
```

```text
$ python3 wa28b-net.py go wa28b-28-client.go
status 200 · Access-Control-Allow-Origin="" · 본문 {"cors":"ok"}
(go run exit 0)
--- 서버 로그 ---
B POST /cors?acao=none&id=go  Origin=(없음) · Content-Type=text/plain · X-A=(없음) · 본문 11바이트 → 처리했다
(exit 0)
```

- ★★ **Go 는 응답을 그냥 읽는다** — `status 200 · Access-Control-Allow-Origin="" · 본문 {"cors":"ok"}`. 허용 헤더가 없다는 것이 **아무 뜻도 없다.** 서버 로그의 `Origin=(없음)` — 브라우저가 아니면 `Origin` 도 안 붙는다.
- ★★★ **그래서 CORS 는 서버를 지키는 장치가 아니다** — 브라우저가 **다른 출처의 페이지에게 응답을 보여 줄지**를 정하는 규칙이다. `curl`·서버 코드·스크립트는 이 규칙 밖에 있다. Go `net/http` 서버 쪽에도 CORS 는 표준 동작이 아니라 **직접 헤더를 붙이는 미들웨어**의 몫이다(Go 갈래 46번 `net/http` 서버·미들웨어 · 47번 클라이언트 — 둘 다 폴더는 아직 없다).

```text
   같은 서버 B 의 같은 응답 — 클라이언트 둘

   서버 B          POST 처리했다 · 200 · 허용 헤더 없음      (둘 다 같다)
   브라우저 페이지 catch TypeError                           ← 브라우저가 읽기를 막았다(25편)
   Go 클라이언트   status 200 · 본문을 읽었다                ← 막을 주체가 없다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   요청 쪽 (브라우저가 정한다 — 스크립트는 고를 수 없다)
     단순 요청     메서드 GET·HEAD·POST  +  헤더가 전부 안전 목록  +  본문이 스트림이 아님
                   Content-Type 은 text/plain · application/x-www-form-urlencoded · multipart/form-data 만 (값 ≤ 128바이트)
     프리플라이트  OPTIONS  +  Access-Control-Request-Method  +  Access-Control-Request-Headers(안전 목록 밖의 이름들)

   응답 쪽 (서버가 붙인다)
     Access-Control-Allow-Origin     출처 하나 또는 *        ← 없으면 읽기 거부
     Access-Control-Allow-Methods    프리플라이트 답에        ← 본 요청의 메서드가 있어야
     Access-Control-Allow-Headers    프리플라이트 답에        ← 안전 목록 밖의 헤더 이름이 있어야
     Access-Control-Max-Age          프리플라이트 답에        ← 없으면 5초
     Access-Control-Expose-Headers   본 응답에                ← 안전 목록 밖의 응답 헤더를 보여 줄 때

   fetch 옵션
     mode: "cors"(기본) · "no-cors"(opaque — status 0) · "same-origin"(다른 출처면 거부)
```

### 어디서 헷갈리나

- **「CORS 에러가 났으니 서버에는 아무 일도 없었다」는 반만 맞다** — 프리플라이트가 붙었으면 맞고((4)), 단순 요청이면 틀리다(25편).
- **`GET` 도 프리플라이트가 붙는다** — `application/json` 헤더 하나로((2)).
- **`multipart/form-data` 는 안전 목록이다** — boundary 가 없어도((2)).
- **`no-cors` 는 「CORS 를 끄는 스위치」가 아니다** — 응답을 **빈 상자**로 바꿀 뿐이다((7)).

## 어디서 틀리나

### 1. CORS 오류가 나면 서버에서는 아무 일도 없었다고 믿는다

**단순 요청은 처리된 뒤 읽기만 막힌다**(25편). 되돌릴 수 없는 엔드포인트는 **서버가** `Origin`·토큰으로 막아야 한다 — 방어 설계는 [`../../security/`](../../security/) 의 몫이다(아직 절이 없다).

### 2. 「JSON API 니까 프리플라이트가 늘 막아 준다」고 믿는다

**`Content-Type` 을 `text/plain` 으로 바꾸면 단순 요청이 된다**((2)) — 본문이 JSON 이어도 브라우저는 모른다. 30편의 「`JSON.stringify` 만 넘기면 `text/plain;charset=UTF-8`」이 바로 그 칸이다. 서버가 `Content-Type` 을 안 보고 JSON 으로 파싱하면 **프리플라이트 없는 JSON 요청**을 받는다.

### 3. 프리플라이트 거부와 단순 요청 거부를 같은 것으로 로그에서 찾는다

**페이지 쪽 글자는 같고**(`Failed to fetch`) **서버 로그는 한 줄(OPTIONS)과 처리 줄로 다르다**((4)). 서버 로그에서 「주문이 들어왔나」를 찾을 때 **OPTIONS 만 있고 본 요청이 없는 줄**을 따로 봐야 한다.

### 4. `Max-Age` 를 안 주면 프리플라이트가 매번 난다고 믿는다

**기본 5초**다((5)). 매번 묻게 하려면 `0` 을 적는다.

### 5. 응답 헤더를 보냈으니 페이지가 읽을 수 있다고 믿는다

**`Access-Control-Expose-Headers` 에 없으면 `null`** 이다((6)) — 예외도 없다.

### 6. 「CORS 가 귀찮으니 `no-cors`」

**`status 0` · 본문 `""`** 을 받는다((7)). 게다가 **커스텀 헤더는 조용히 버려진다** — 인증 헤더를 붙였다고 믿으면 서버에서만 들통난다.

### 7. CORS 가 API 를 보호한다고 믿는다

**브라우저가 아닌 클라이언트는 그냥 읽는다**((9)). CORS 는 **다른 출처의 페이지**가 응답을 읽는 것만 막는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 안전 목록 메서드 `GET`·`HEAD`·`POST` · 안전 목록 `Content-Type` 셋 · 128바이트 · 안전 목록 밖 헤더 → 프리플라이트 | **명세**(Fetch — CORS-safelisted method · CORS-safelisted request-header · main fetch 조건) · 이 판도 그랬다((2)·(3)) |
| ★ 프리플라이트가 network error 면 **본 요청을 안 보낸다** | **명세**(HTTP fetch — 「preflightResponse 가 network error 면 그것을 돌려준다」) · ★ **서버 로그가 증명**((4)) |
| 스트림 본문은 커스텀 헤더 없이도 프리플라이트 | **명세**(use-CORS-preflight flag) · 이 판도 그랬다((3)) |
| ★ HTTP/1.1 서버로 스트림 본문을 **안 보낸다**(`ERR_ALPN_NEGOTIATION_FAILED`) | ★ **Chrome 의 성질** — 명세 문장이 아니다 |
| `Max-Age` 가 없으면 5초 · 상한은 구현이 정함 | **명세**(CORS-preflight cache) · 5초 안의 두 번째가 캐시였던 것은 **이 판의 관찰**((5)) |
| 안전 목록 응답 헤더 · 노출 헤더 · `*` | **명세**(CORS-safelisted response-header name · Expose-Headers) · 이 판도 그랬다((6)) |
| `no-cors` → opaque(status 0 · 헤더·본문 없음) · 안전 목록 밖 메서드는 `TypeError` | **명세**(opaque filtered response · Request 생성자) · 이 판도 그랬다((7)) |
| 다른 출처를 거쳐 오면 `Origin: null` | **명세**(요청 출처 직렬화 — redirect-taint) · 이 판도 그랬다((8)) |
| 프리플라이트에 307 → 실패 | **명세**(CORS-preflight fetch — ok status 여야) · 콘솔 문구는 **Chrome 의 글자** |
| 콘솔의 CORS 문구 · `Failed to fetch` | ★ **Chrome 의 글자** — 명세는 `TypeError` 만 정한다 |
| 브라우저 밖의 클라이언트는 CORS 를 모른다 | **CORS 의 정의**(브라우저의 fetch 알고리즘) · Go 로 관찰((9)) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 다른 출처 API 를 페이지에서 읽기 | 서버가 `Access-Control-Allow-Origin` 을 정확한 출처로 | 「`no-cors` 로 우회」 |
| 프리플라이트 왕복을 줄이기 | `Access-Control-Max-Age` · 단순 요청으로 설계할 수 있으면 그쪽 | 캐시를 믿고 **보안 판단**을 미룸 |
| 되돌릴 수 없는 다른 출처 요청 | 서버의 `Origin`·토큰 검사 | 「브라우저가 막아 주겠지」 |
| 커스텀 응답 헤더를 페이지가 읽어야 | `Access-Control-Expose-Headers` 에 이름 | 「보냈으니 보인다」 |
| 이미지·스크립트처럼 읽을 필요 없는 다른 출처 요청 | `no-cors`(opaque 로 충분할 때만) | 본문이 필요한데 `no-cors` |

## 핵심 문장

1. **프리플라이트를 부르는 문은 셋이다** — 안전하지 않은 메서드 · 안전 목록 밖의 `Content-Type` 값 · 안전 목록 밖의 헤더 이름(OPTIONS 가 먼저 온 칸 26 / 32). 스트림 본문이 넷째다.
2. **프리플라이트가 거부되면 본 요청은 서버에 가지도 않는다** — 서버 로그에 OPTIONS 한 줄뿐. 단순 요청은 처리된 뒤 읽기만 막힌다(25편).
3. **페이지는 둘을 가를 수 없다** — 둘 다 `TypeError 「Failed to fetch」`. 이유는 콘솔에만.
4. **프리플라이트 답은 기억된다** — `Max-Age` 가 없어도 5초.
5. **CORS 는 브라우저가 다른 출처 페이지에게 응답을 보여 줄지의 규칙이다** — 브라우저 밖의 클라이언트는 그냥 읽는다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 28번)
- [25번 주제](../25-fetch-request-response/2-summary.md) — ★ **「막는 것은 응답 읽기」의 첫 실측**(단순 `POST` 가 처리됐다 · 금지 헤더). 그쪽은 **단순 요청 한 칸**, 여기는 **프리플라이트가 붙는 칸과 그 규칙**
- [24번 주제](../24-document-lifecycle-events/2-summary.md) — 하네스의 Chrome·CDP 부분 전문((1))
- [29번 주제](../29-credentials-and-cookies/2-summary.md) — 자격 증명(쿠키)이 붙으면 `*` 가 왜 안 되나
- [30번 주제](../30-request-body-and-content-type/2-summary.md) — 본문 종류가 정하는 `Content-Type` — 여기 (2)의 「`text/plain` 이면 단순 요청」과 만난다
- [`../../security/`](../../security/) — **보안 모델의 정본 자리.** 그쪽은 해시·서명·신원 같은 **프리미티브**(2026-09-26 현재 CORS·CSRF 절은 없다), 여기는 **브라우저가 막는 것과 못 막는 것의 관찰**
- [HTML 21번 주제](../../languages/html/syntax/21-form-submission-model/2-summary.md) — 폼 제출은 **CORS 이전부터 있던 다른 출처 요청**이다(폼은 응답을 스크립트에게 주지 않는다)

## 용어 풀이

- **출처(origin)** — 스킴 + 호스트 + 포트. `127.0.0.1:<A>` 와 `127.0.0.1:<B>` 는 **다른 출처**다.
- **CORS** — 다른 출처의 응답을 **스크립트에게 보여 줄지** 서버의 헤더로 정하는 브라우저의 규칙.
- **단순 요청** — 프리플라이트 없이 바로 가는 요청(안전 목록 메서드·헤더·본문).
- **프리플라이트** — 본 요청 전에 브라우저가 보내는 `OPTIONS`. 답이 허용하지 않으면 본 요청을 안 보낸다.
- **안전 목록(safelisted)** — 명세가 「프리플라이트 없이 보내도 된다」고 정한 메서드·헤더(값)의 목록.
- **프리플라이트 캐시** — 프리플라이트 답을 `Max-Age` 초(없으면 5초) 동안 기억하는 것.
- **opaque 응답** — `no-cors` 로 받은 다른 출처 응답. status 0 · 헤더와 본문이 안 보인다.
- **redirect-taint** — 리다이렉트가 다른 출처를 거쳤는지. `same-origin` 이 아니면 `Origin` 이 `null` 이 된다.
- **프리플라이트 격자** — 메서드 × `Content-Type` × 헤더 32칸 × 「OPTIONS 가 먼저 왔나」. 이 편의 본체.

## 더 들어가면

- **`Access-Control-Allow-Methods: *`·`Allow-Headers: *`** 는 자격 증명이 없을 때만 와일드카드로 읽힌다(명세의 메서드·헤더 검사 문장) — 던지지 않았다.
- **`HEAD`** 는 안전 목록이지만 격자에 넣지 않았다.
- **HTTP/2 서버에서의 스트림 업로드**와 **`Max-Age` 상한**은 이 판으로 못 본다(머리말 「도구가 못 보는 것」).
