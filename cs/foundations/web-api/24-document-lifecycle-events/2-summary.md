# web-api/24 — 문서 수명주기 이벤트: `DOMContentLoaded`/`load`·`visibilitychange`·`pagehide`/`pageshow` 와 bfcache — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 를 늘린 「떠날 때」 격자다** — 떠나는 방법 여덟 가지(링크 · 새로 고침 · 탭 닫기 두 가지 · 뒤로 · 앞으로 · 다른 탭이 앞으로 · 돌아옴) × 이벤트 여섯(`beforeunload` · `pagehide` · `unload` · `visibilitychange` · `pageshow` · `load`)을 **리스너 없는 쪽과 `unload` 리스너 하나 단 쪽** 두 판으로 채우고, bfcache 에 못 들어간 이유는 **CDP 의 `Page.backForwardCacheNotUsed`** 로 받는다.\
> **기준 소스** — [WHATWG HTML — Document lifecycle](https://html.spec.whatwg.org/multipage/document-lifecycle.html) 의 「unload a document」(page showing 이면 **`pagehide`** → 가시성을 **`hidden` 으로** → salvageable 이 거짓이면 **`unload`**) · 크롬 쪽 설명은 [Deprecating the unload event](https://developer.chrome.com/docs/web-platform/deprecating-unload)(Chrome 115 부터 `Permissions-Policy: unload` · 2026 년 v146\~v154 사이 모든 출처로 단계적 확대). ★ **HTML 명세에서 「`unload` 리스너가 있으면 bfcache 에 못 들어간다」는 문장은 찾지 못했다** — 그 조건은 **브라우저 구현**이다(아래 「구현 세부사항 대 언어 보장」). 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 페이지는 **로컬 서버 A(`http://127.0.0.1`)** 에서 열었다(`file://` 는 오류가 muted 되고 `fetch` 가 막힌다). 링크는 **CDP 로 넣은 진짜 마우스**로 누르고, 뒤로·앞으로는 `Page.navigateToHistoryEntry`, 탭 닫기는 `Target.closeTarget` 과 `Page.close`, 탭 전환은 `Target.createTarget`·`Target.activateTarget` 로 했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — [16번 주제](../16-event-propagation-phases/2-summary.md)(전파 — `load` 는 `window` 에서 받는다). ★★ **`DOMContentLoaded` 와 `load` 의 순서, `defer`·모듈·`async` 가 어디에 끼는지는 [HTML 08번 주제](../../languages/html/syntax/08-script-loading/2-summary.md)의 (1)·(2)가 쟀다** — 여기서는 **다시 재지 않고 인용**하고, **이미지 한 장을 서버가 붙잡았을 때** 한 칸만 더한다((6)).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 「떠날 때」 격자 전 칸 · CDP 이유 · 페이지가 받은 이유 · 문서별 순서 두 줄 · 이미지 순서 로그 | 캡처 세 판이 **한 글자도 같았다** |
| ★ **흔들려서 안 실었다** | **두 문서가 섞인 순서** — 뒤로 갈 때 둘째쪽 `pagehide` 가 첫쪽 `pageshow` **뒤에** 적힌 판이 있었다 | 두 문서는 서로 다른 렌더러에서 돈다. 그래서 순서는 **한 문서 안에서만** 싣는다 |
| ★ **흔들렸다가 고쳤다** | 떠난 문서의 **늦게 적힌 줄**이 빠지는 것 | 도착한 문서의 `pageshow` 만 기다리면 떠난 문서의 `pagehide` 를 놓친다. **기록이 animation frame 20장 연달아 그대로일 때까지** 기다리게 고쳤다 |
| ★ **판에 따라 바뀔 수 있다** | `unload` 가 **불리나** | Chrome 이 `unload` 를 **페이지 로드 비율로** 끄는 중이다(위 기준 소스). 이 판에서는 세 판 모두 불렸다 |

```text
   왜 두 문서가 섞인 순서는 안 싣나 — 뒤로 한 번 (시험판에서 본 모양)

   둘째쪽(떠남)   beforeunload ···················· pagehide p=true → hidden → freeze
   첫쪽(돌아옴)            resume → visible → pageshow p=true
                  ★ 두 줄이 서로 다른 렌더러에서 적힌다 — 사이에 끼는 자리는 판마다 달라도 된다
                    한 문서 안의 순서(각 줄)만 싣는다
```

| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `document.readyState` · `img.complete`((6)) |
| 창 ③ 같은 것을 두 번 읽기 | ★ **쓴다 — 하네스 안에서** | 문서마다 심은 표(`window.__문서`)를 떠나기 전과 뒤에 읽어 **같은 문서가 되살아났나**를 가른다 |
| **창 ④ 디스패치 계수기 → 「떠날 때」 격자** | ★★★ **본체** | 어느 떠남에서 어느 이벤트가 · `persisted` 가 무엇으로 |
| **CDP `Page.backForwardCacheNotUsed`** | ★★ **쓴다 — bfcache 창** | **왜** 못 들어갔나 |
| ★ **페이지의 `notRestoredReasons`** | ★ **같은 질문을 다른 창으로(제5의 상태)** | 같은 「왜」를 페이지가 물으면 무엇을 받나 — **`masked`** 만 받았다((4)) |
| 서버 요청 로그 | ★ **쓴다** | 이미지를 **붙잡았다가 놓은 때**((6)) |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **모바일의 백그라운드 전환 · 앱 전환 · 프로세스 강제 종료** | 이 판은 **헤드리스 데스크톱**이다. 운영체제가 탭을 얼리거나 죽이는 경로가 없다. 「탭 전환」은 **새 탭을 여는 것**으로만 흉내 냈다((5)) |
| **탭 폐기(discard)** | CDP 에 그 명령이 없다. `Page.setWebLifecycleState` 는 `frozen`/`active` 만 준다 |
| **사용자가 창을 닫는 것** | 두 CDP 명령으로 흉내 냈고, **둘이 다르게 굴었다**((3)) — 진짜 닫기가 어느 쪽인지는 모른다 |
| **bfcache 가 「빠르다」** | **재지 않았다.** 되살아났나(`persisted`)만 봤다 |

## 한눈에 — 쉽게 말하면

**★ 떠나는 페이지는 「짐을 싸서 창고에 넣을지(bfcache), 버릴지」를 브라우저가 정한다. 넣으면 돌아올 때 그대로 꺼내 와서 `load` 없이 `pageshow(persisted=true)` 만 준다. 「떠날 때」를 잡는 이벤트는 여럿인데, 격자에서 모든 떠남에 빠짐없이 난 것은 `visibilitychange → hidden` 하나였다.**

| 비유 | 실체 |
|---|---|
| 짐을 창고에 넣는다 | bfcache(뒤로·앞으로 캐시) — 문서를 **통째로** 얼려 둔다 |
| 창고에서 꺼내 온다 | 뒤로·앞으로에서 되살아남 — `pageshow` 의 `persisted=true` · `load` 없음 |
| 「창고에 넣을 거야?」 표 | `pagehide` 의 `persisted` |
| 문 닫고 나간다 | `unload` — **창고에 안 넣을 때만** 난다 |
| 「뒤돌아보지 마」 표지 한 장 | `unload` 리스너 — 이 판의 Chrome 은 **그것 하나로 창고에 안 넣었다** |
| 불이 꺼진다 | `visibilitychange → hidden` — 떠나든 탭만 가리든 난다 |

```text
   ★ 링크로 떠날 때 — 떠나는 문서가 받는 순서 (이 판)

   리스너 없음     beforeunload → pagehide(persisted=true)  → visibilitychange hidden → freeze
                   (창고에 들어갔다 — 뒤로 오면 resume → visible → pageshow(persisted=true))

   unload 있음     beforeunload → pagehide(persisted=false) → visibilitychange hidden → unload
                   (버려졌다 — 뒤로 오면 DOMContentLoaded → load → pageshow(persisted=false))
```

## 이 주제가 답하려는 질문

1. **「떠날 때」를 어느 이벤트로 잡아야 하나** — 링크 · 새로 고침 · 탭 닫기 · 뒤로 · 탭 전환에서 각 이벤트가 나나.
2. **bfcache 로 되살아난 페이지에서 무엇이 안 나나** — `load` 는? `pageshow` 는 무엇을 말하나?
3. **무엇이 bfcache 를 막나 · 누가 그것을 말해 주나** — `unload` 리스너 · `Cache-Control: no-store` · `Permissions-Policy`.

## 동작 방식

### (1) 하네스 — 서버 둘과 Chrome 을 한 프로세스에서

**24\~27 이 같이 쓰는 하네스다.** 서버 A(페이지·같은 출처) · 서버 B(다른 출처) · 아무도 안 듣는 포트를 띄우고, 헤드리스 Chrome 에 CDP 로 붙는다. **포트는 전부 운영체제가 고르고 출력에는 이름(A·B)만** 나온다. 「천천히」는 시간이 아니라 **신호**다 — 서버는 `/go` 를 받을 때까지 다음 단계로 안 가고, 페이지는 `/state?wait=…` 로 서버가 그 단계에 이를 때까지 기다린다.

```python
# wa24b-net.py
#!/usr/bin/env python3
"""web-api 24~27 — 로컬 서버 둘(A·B)과 헤드리스 Chrome(CDP)을 한 프로세스에서 몬다.

사용:
  wa24b-net.py page <html>        A 에서 그 페이지를 열고 window.__끝() (async) 이 돌려준 글을 찍은 뒤
                                  「서버 로그」를 찍는다
  wa24b-net.py console <html>     page 와 같고, 서버 로그 앞에 콘솔(Log 도메인) 줄을 찍는다
  wa24b-net.py quiet <html>       page 와 같고, 서버 로그를 안 찍는다(페이지가 /state 로 물은 것만)
  wa24b-net.py life <html>        24편 — 페이지의 window.__판 = [[판 이름, [줄, ...]], ...] 의 줄마다
                                  새 탭에서 준비 → 동작을 하고 「떠날 때」 격자를 찍는다
  wa24b-net.py urllib             25편 대비 — 파이썬 urllib 로 A 의 /status 를 부른다

★ 포트는 전부 0 — 운영체제가 고른다. 출력에는 서버 이름(A·B)만 쓰고, Host 헤더의 포트는 <A>·<B> 로 적는다.
★ 페이지는 file:// 가 아니라 A(http://127.0.0.1)에서 연다 — file:// 면 fetch 가 막히고 오류가 muted 된다.
  페이지에는 window.__B(다른 출처 서버) · window.__없는곳(아무도 안 듣는 포트)을 문서보다 먼저 심는다.
★ 「천천히」는 시간이 아니라 신호다 — 서버는 /go 를 받을 때까지 다음 청크·다음 단계로 안 간다.
  페이지는 /state?wait=… 로 서버가 그 단계에 이를 때까지 기다린다. sleep 상수가 없다.
★ 서버 로그 — 엔드포인트 요청만 적는다(페이지·/state·/go 는 안 적는다). 한 요청의 줄은 그 요청 번호(id)로 묶인다.
"""
import http.server, json, os, select, shutil, signal, socket, subprocess, sys, threading, time
import urllib.error, urllib.parse, urllib.request
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
PROF = os.path.join(HERE, f".prof-wa24b-{os.getpid()}")
FLAGS = ["--headless", "--disable-gpu", "--no-sandbox", "--window-size=1000,800",
         "--remote-debugging-port=0", f"--user-data-dir={PROF}", "about:blank"]
WAIT = 30                      # 신호를 기다리는 상한(초) — 넘으면 「안 옴」으로 적는다(정상 판에서는 안 닿는다)

LOG, LOCK = [], threading.Lock()
STATE = {}                     # id → {"arrived", "sent", "done", "go", "note"}
COND = threading.Condition(LOCK)
PORTS = {}                     # 이름 → 포트 (출력에 안 나간다)
ACTIVE = 0                     # 지금 처리 중인 요청 수 — 로그를 찍기 전에 0 이 되기를 기다린다


def log(line):
    with LOCK:
        LOG.append(line)


def st(i):
    return STATE.setdefault(i, {"arrived": False, "sent": 0, "done": False, "go": 0, "note": []})


def bump(i, **kw):
    with COND:
        s = st(i)
        for k, v in kw.items():
            s[k] = v
        COND.notify_all()


def wait_for(pred):
    with COND:
        return COND.wait_for(pred, timeout=WAIT)


def peer_closed(sock):
    """상대가 연결을 닫았나 — 읽을 것이 있고(select) 들여다본 바이트가 0 이면 닫힌 것이다(기다리지 않는다)."""
    r, _, _ = select.select([sock], [], [], 0)
    if not r:
        return False
    try:
        return sock.recv(1, socket.MSG_PEEK) == b""
    except OSError:
        return True


def server(name):
    class H(http.server.SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def __init__(self, *a, **k):
            super().__init__(*a, directory=HERE, **k)

        def log_message(self, *a):
            pass

        def translate_path(self, path):
            for pre in ("/nostore/", "/nounload/"):
                if path.startswith(pre):
                    path = path[len(pre) - 1:]
            return super().translate_path(path)

        def end_headers(self):
            if self.path.startswith("/nostore/"):        # 24 — 주 문서에 Cache-Control: no-store
                self.send_header("Cache-Control", "no-store")
            if self.path.startswith("/nounload/"):       # 24 — 이 문서에서 unload 를 끈다
                self.send_header("Permissions-Policy", "unload=()")
            super().end_headers()

        # ---------------------------------------------------------------- 공용
        def q(self):
            u = urllib.parse.urlsplit(self.path)
            return u.path, dict(urllib.parse.parse_qsl(u.query))

        def reply(self, code, body=b"", ctype="application/json", extra=()):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in extra:
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def shown(self):
            """경로 + 질의(id 는 뺀다 — 요청 번호일 뿐이다)."""
            path, qs = self.q()
            rest = "&".join(f"{k}={v}" for k, v in qs.items() if k != "id")
            return path + ("?" + rest if rest else "")

        def do_OPTIONS(self):
            log(f"{name} OPTIONS {self.shown()}  (프리플라이트) · Access-Control-Request-Headers="
                f"{self.headers.get('Access-Control-Request-Headers', '(없음)')}")
            self.reply(204)

        def do_GET(self):
            self.route("GET", b"")

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            self.route("POST", self.rfile.read(n))

        def route(self, method, body):
            global ACTIVE
            with COND:
                ACTIVE += 1
            try:
                self.route1(method, body)
            finally:
                with COND:
                    ACTIVE -= 1
                    COND.notify_all()

        def route1(self, method, body):
            path, qs = self.q()
            i = qs.get("id", "")
            if path == "/state":                   # 기다림 창구 — 로그에 안 적는다
                want = qs.get("wait", "")
                if want == "arrived":
                    ok = wait_for(lambda: st(i)["arrived"])
                elif want == "done":
                    ok = wait_for(lambda: st(i)["done"])
                elif want == "closed":
                    ok = wait_for(lambda: st(i).get("closed") or st(i)["done"])
                elif want.startswith("sent:"):
                    k = int(want[5:])
                    ok = wait_for(lambda: st(i)["sent"] >= k or st(i)["done"])
                else:
                    ok = True
                with LOCK:
                    s = dict(st(i))
                s["timeout"] = not ok
                return self.reply(200, json.dumps(s, ensure_ascii=False).encode(),
                                  extra=[("Access-Control-Allow-Origin", "*")])
            if path == "/go":                      # 다음 단계로 가라 — 로그에 안 적는다
                with COND:
                    st(i)["go"] += 1
                    COND.notify_all()
                return self.reply(204, extra=[("Access-Control-Allow-Origin", "*")])
            if path == "/status":
                code = int(qs.get("code", "200"))
                self.reply(code, json.dumps({"status": code}).encode())
                log(f"{name} {method} {self.shown()}  → {code} 응답을 끝까지 보냈다")
                return
            if path == "/order":
                acao = qs.get("acao") == "1"
                text = body.decode()
                origin = self.headers.get("Origin", "(없음)")
                for p_name, p in PORTS.items():
                    origin = origin.replace(f"127.0.0.1:{p}", f"127.0.0.1:<{p_name}>")
                log(f"{name} {method} {self.shown()}  Origin={origin}"
                    f" · 본문 「{text}」 → 주문을 처리했다 · 200 을 보냈다 · 허용 헤더 {'있음' if acao else '없음'}")
                return self.reply(200, json.dumps({"order": "ok"}).encode(),
                                  extra=[("Access-Control-Allow-Origin", "*")] if acao else ())
            if path == "/headers":
                want = qs.get("show", "").split(",")
                names = [k for k, _ in self.headers.items()]
                log(f"{name} {method} {self.shown()}  받은 헤더 이름(보낸 그대로) = " + " · ".join(names))
                for w in want:
                    v = self.headers.get(w)
                    if v is not None:
                        for p_name, p in PORTS.items():
                            v = v.replace(f"127.0.0.1:{p}", f"127.0.0.1:<{p_name}>")
                    log(f"    {w} = {v if v is not None else '(안 왔다)'}")
                return self.reply(200, b'{"ok":1}', extra=[("X-Visible", "v1"), ("Set-Cookie", "srv=1; Path=/")])
            if path == "/img":                     # 24 — /go 를 받을 때까지 이미지를 안 준다
                bump(i, arrived=True)
                log(f"{name} {method} {self.shown()}  도착 — /go 를 기다린다")
                ok = wait_for(lambda: st(i)["go"] >= 1)
                gif = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b")
                self.reply(200, gif, "image/gif")
                log(f"{name}   {'go 를 받고 ' if ok else 'go 안 옴 — '}이미지를 보냈다")
                return bump(i, done=True)
            if path == "/chunks":
                return self.chunks(i, qs, method)
            if path == "/work":
                return self.work(i, qs, method)
            return super().do_GET() if method == "GET" else self.reply(405)

        # ---------------------------------------------------------------- 26 · 27
        def wait_go(self, i, k):
            """/go 가 k 번 올 때까지 기다린다. 기다리는 동안 상대가 연결을 닫으면 그것을 한 번 적는다.
            (50ms 는 깨어나 소켓을 들여다보는 간격일 뿐 — 결과는 go 와 닫힘이라는 사건이 정한다)"""
            end = time.monotonic() + WAIT
            while time.monotonic() < end:
                with COND:
                    if st(i)["go"] >= k:
                        return True
                    COND.wait(0.05)
                if not st(i).get("closed") and peer_closed(self.connection):
                    bump(i, closed=True)
                    log(f"{name}   상대가 연결을 닫은 것을 알았다")
            return False

        def put(self, i, data):
            """data 를 쓴다. 상대가 닫은 연결이면 커널이 첫 바이트를 일단 받아 주므로,
            상대의 RST 가 돌아와 오류가 날 때까지 한 바이트씩 더 써 본다. 오류 이름(없으면 None)을 돌려준다."""
            try:
                self.wfile.write(data)
                self.wfile.flush()
                if not st(i).get("closed"):
                    return None
                end = time.monotonic() + WAIT
                while time.monotonic() < end:
                    select.select([self.connection], [], [], 0.05)
                    self.connection.send(b" ")
                return "끝내 오류 없음"
            except OSError as e:
                return type(e).__name__

        def chunks(self, i, qs, method):
            """헤더는 곧바로, 청크 n 개와 끝 표시는 /go 를 하나 받을 때마다 하나씩 보낸다."""
            n = int(qs.get("n", "5"))
            bump(i, arrived=True)
            log(f"{name} {method} {self.shown()}  도착")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            self.wfile.flush()
            if qs.get("split") == "1":     # 「가나\n」 을 글자 중간에서 쪼갠다 — 2 · 2 · 3 바이트
                whole = "가나\n".encode()
                pieces = [whole[:2], whole[2:4], whole[4:]]
            else:
                pieces = [f"줄{k + 1}\n".encode() for k in range(n)]
            err = None
            for k, p in enumerate(pieces + [None]):
                if not self.wait_go(i, k + 1):
                    err = "go 안 옴"
                    break
                if p is not None:
                    bump(i, sent=k + 1)          # 쓰기 「전에」 센다 — 페이지가 받았을 때는 이미 올라가 있다
                err = self.put(i, b"0\r\n\r\n" if p is None else b"%x\r\n%s\r\n" % (len(p), p))
                if err:
                    break
            if err:
                log(f"{name}   쓰기 실패 ({err}) — 청크 {st(i)['sent']}/{len(pieces)} 째에서")
                self.close_connection = True
            else:
                log(f"{name}   청크 {len(pieces)}개와 끝 표시까지 썼다")
            bump(i, done=True, write=err or "오류 없음")

        def work(self, i, qs, method):
            """27 — 도착 → (/go 를 기다려) 처리 끝 → 응답 쓰기."""
            bump(i, arrived=True)
            log(f"{name} {method} {self.shown()}  도착 — 처리 시작")
            ok = self.wait_go(i, 1)
            log(f"{name}   처리 끝 (주문을 기록했다)" if ok else f"{name}   go 안 옴")
            body = b'{"work":"done"}'
            head = (b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: %d\r\n\r\n"
                    % len(body))
            err = self.put(i, head + body)
            log(f"{name}   응답 쓰기 실패 ({err})" if err else f"{name}   응답을 썼다 (오류 없음)")
            if err:
                self.close_connection = True
            bump(i, done=True, write=err or "오류 없음")

    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    s.daemon_threads = True
    PORTS[name] = s.server_address[1]
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def dead_port():
    """아무도 안 듣는 포트 — 잠깐 묶었다가 놓는다."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


# -------------------------------------------------------------------- CDP
class Cdp:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, suppress_origin=True)
        self.n = 0
        self.events = []

    def send(self, method, params=None, sid=None):
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(method + " " + json.dumps(r["error"], ensure_ascii=False))
                return r.get("result", {})
            self.events.append(r)

    def wait(self, method, sid=None):
        while True:
            for k, e in enumerate(self.events):
                if e.get("method") == method and (sid is None or e.get("sessionId") == sid):
                    return self.events.pop(k).get("params", {})
            self.events.append(json.loads(self.ws.recv()))

    def take(self, method, sid=None):
        got = [e.get("params", {}) for e in self.events
               if e.get("method") == method and (sid is None or e.get("sessionId") == sid)]
        self.events = [e for e in self.events
                       if not (e.get("method") == method and (sid is None or e.get("sessionId") == sid))]
        return got


def start():
    shutil.rmtree(PROF, ignore_errors=True)
    proc = subprocess.Popen(["google-chrome"] + FLAGS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    port_file = os.path.join(PROF, "DevToolsActivePort")
    for _ in range(400):          # 브라우저가 CDP 를 열 때까지 — 순서만 기다린다(값에는 안 들어간다)
        try:
            port = open(port_file).read().split()[0]
            v = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"))
            return proc, Cdp(v["webSocketDebuggerUrl"])
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("CDP 가 안 열렸다")


def stop(proc):
    # 자기가 띄운 프로세스만 끝낸다. 자식(렌더러 등)이 프로필을 놓을 때까지 기다린 뒤 지운다.
    proc.terminate()
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    for _ in range(100):
        busy = subprocess.run(["pgrep", "-f", "--", "--user-data-dir=" + PROF],
                              stdout=subprocess.DEVNULL).returncode == 0
        if not busy:
            break
        time.sleep(0.05)
    shutil.rmtree(PROF, ignore_errors=True)


def evaluate(c, sid, expr):
    r = c.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True}, sid)
    if "exceptionDetails" in r:
        d = r["exceptionDetails"]
        return "«예외 " + (d.get("exception", {}).get("description") or d.get("text", "?")) + "»"
    return r.get("result", {}).get("value")


def open_tab(c, bases):
    tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    for m in ("Page.enable", "Runtime.enable", "Log.enable"):
        c.send(m, sid=sid)
    c.send("Page.addScriptToEvaluateOnNewDocument", {"source": "window.__B = %s; window.__없는곳 = %s;"
           % (json.dumps(bases["B"]), json.dumps(bases["없는곳"]))}, sid)
    return tid, sid


def goto(c, sid, url):
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)


def print_log():
    wait_for(lambda: ACTIVE == 0)          # 응답을 다 쓰고 로그를 남길 때까지(클라이언트는 헤더만 받고도 돌아온다)
    print("--- 서버 로그 ---")
    with LOCK:
        lines = LOG[:]
        LOG.clear()
    for line in lines:
        print(line)
    if not lines:
        print("(받은 요청 없음)")


# -------------------------------------------------------------------- 24 — 떠나고 돌아오기
def 너비(t):
    return sum(2 if ord(ch) > 0x1100 else 1 for ch in t)


def 칸(t, w):
    return t + " " * max(w - 너비(t), 1)


def click(c, sid, sel):
    xy = evaluate(c, sid, "(() => { const r = document.querySelector(%s).getBoundingClientRect();"
                          " return [r.x + r.width / 2, r.y + r.height / 2]; })()" % json.dumps(sel))
    c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": xy[0], "y": xy[1]}, sid)
    for t in ("mousePressed", "mouseReleased"):
        c.send("Input.dispatchMouseEvent", {"type": t, "x": xy[0], "y": xy[1], "button": "left",
               "clickCount": 1, "buttons": 1 if t == "mousePressed" else 0}, sid)


def 되살아남(c, sid):
    """뒤로·앞으로 — bfcache 에서 되살아나면 load 가 안 난다. 「새 문서가 섰다」는 frameNavigated 로 받고
    readyState 가 complete 가 될 때까지 기다린다."""
    c.wait("Page.frameNavigated", sid)
    evaluate(c, sid, "new Promise(r => document.readyState === 'complete' ? r() :"
                     " addEventListener('load', () => r(), { once: true }))")


def act(c, tabs, base, a):
    """tabs = {"첫": (tid, sid), "둘": (tid, sid) 또는 없음}. 동작 하나를 한다."""
    tid, sid = tabs["첫"]
    c.events.clear()                     # 앞 동작의 이벤트가 다음 기다림에 잘못 걸리지 않게
    if a[0] == "누르기":                 # 링크를 진짜 마우스로 누르고 새 문서의 load 를 기다린다
        click(c, sid, a[1])
        c.wait("Page.loadEventFired", sid)
    elif a[0] == "새로고침":
        c.send("Page.reload", {}, sid)
        c.wait("Page.loadEventFired", sid)
    elif a[0] in ("뒤로", "앞으로"):
        h = c.send("Page.getNavigationHistory", {}, sid)
        k = h["currentIndex"] + (-1 if a[0] == "뒤로" else 1)
        c.send("Page.navigateToHistoryEntry", {"entryId": h["entries"][k]["id"]}, sid)
        되살아남(c, sid)
    elif a[0] in ("닫기", "Page.close"):
        if a[0] == "닫기":
            c.send("Target.closeTarget", {"targetId": tid})
        else:                            # CDP 설명 — 「beforeunload 훅이 있으면 돌리며 닫으려 한다」
            c.send("Page.close", {}, sid)
        c.wait("Target.detachedFromTarget")
        tabs["첫"] = None
    elif a[0] == "새탭":                 # 새 탭이 앞으로 온다 — 첫 탭은 뒤로 간다
        t2, s2 = open_tab(c, BASES)
        goto(c, s2, base + "wa24b-24-second.html")
        tabs["둘"] = (t2, s2)
    elif a[0] == "돌아옴":
        c.send("Target.activateTarget", {"targetId": tid})
        c.send("Target.closeTarget", {"targetId": tabs["둘"][0]})
        c.wait("Target.detachedFromTarget")
        tabs["둘"] = None
    else:
        raise RuntimeError("모르는 동작: " + a[0])


COLS = ["beforeunload", "pagehide", "unload", "visibilitychange", "pageshow", "load"]


def cells(rec, x, y, has_unload):
    """x = 동작 전의 문서, y = 동작 뒤 그 탭의 문서(같은 탭에서 새 문서가 섰을 때만)."""
    def of(doc):
        return [r["글"] for r in rec if r["문서"] == doc]
    gx, gy = of(x), (of(y) if y else None)
    out = []
    for col in COLS[:4]:
        hit = [g for g in gx if g.split()[0] == col]
        if col == "unload" and not has_unload:
            out.append("(리스너 없음)")
        elif not hit:
            out.append("—")
        else:
            out.append(" · ".join(g.split(" ", 1)[1] if " " in g else "○" for g in hit))
    for col in COLS[4:]:
        if gy is None:
            out.append("(새 문서 없음)")
            continue
        hit = [g for g in gy if g.split()[0] == col]
        out.append(" · ".join(g.split(" ", 1)[1] if " " in g else "○" for g in hit) if hit else "—")
    return out


def grid24(c, base, page):
    tid, sid = open_tab(c, BASES)
    goto(c, sid, base + page)
    plans = json.loads(evaluate(c, sid, "JSON.stringify(window.__판)"))
    c.send("Target.closeTarget", {"targetId": tid})
    c.wait("Target.detachedFromTarget")
    table = {}
    for pname, rows in plans:
        print(f"[{pname}]")
        head = ["동작"] + COLS + ["CDP 가 말한 bfcache 불가 이유"]
        widths = [18, 14, 18, 14, 18, 16, 16, 0]
        print("".join(칸(h, w) for h, w in zip(head, widths)).rstrip())
        for row in rows:
            tabs = {"첫": open_tab(c, BASES), "둘": None}
            goto(c, tabs["첫"][1], base + row["시작"])
            for a in row["준비"]:
                act(c, tabs, base, a)
            sid = tabs["첫"][1]
            has_unload = evaluate(c, sid, "window.__unload있음 === true")
            evaluate(c, sid, "localStorage.clear()")
            x = evaluate(c, sid, "window.__문서")
            act(c, tabs, base, row["동작"])
            why = []
            for e in c.take("Page.backForwardCacheNotUsed"):
                for w in e.get("notRestoredExplanations", []):
                    why.append(f"{w['reason']}({w['type']})")
            if tabs["첫"]:
                reader = tabs["첫"]
                y = evaluate(c, reader[1], "window.__문서")
                y = None if (y == x or row["동작"][0] in ("새탭", "돌아옴")) else y
            else:                          # 닫은 탭 — 같은 출처의 새 탭에서 읽는다
                reader = open_tab(c, BASES)
                goto(c, reader[1], base + "wa24b-24-second.html")
                y = None
            if tabs["둘"] and row["동작"][0] == "새탭":
                reader = tabs["둘"]         # 뒤로 간 탭은 animation frame 이 안 돈다 — 앞의 탭에서 읽는다
            rec = json.loads(evaluate(c, reader[1], "window.__가라앉음()"))
            cs = cells(rec, x, y, has_unload)
            if len(cs) != len(COLS):
                raise RuntimeError("칸 수가 어긋났다")
            table[(pname, row["이름"])] = cs
            print("".join(칸(v, w) for v, w in zip([row["이름"]] + cs + [", ".join(why) or "—"], widths)).rstrip())
            if row.get("순서"):            # 문서마다 받은 순서 — 한 문서 안의 순서만 싣는다(문서끼리 섞인 순서는 흔들린다)
                for doc, label in ((x, "떠난 문서"), (y, "도착한 문서")):
                    if doc:
                        ev = [r["글"] for r in rec if r["문서"] == doc]
                        print(f"    {label}({next(r['쪽'] for r in rec if r['문서'] == doc)})  " + " → ".join(ev))
            if row.get("묻기") and tabs["첫"]:
                print("    페이지에게 물음  " + str(evaluate(c, tabs["첫"][1], row["묻기"])))
            for t in {tabs["첫"], tabs["둘"], reader} - {None}:
                c.send("Target.closeTarget", {"targetId": t[0]})
        print()
    (p1, rows1), (p2, _) = plans[:2]
    hit = total = 0
    for row in rows1:
        a1, a2 = table[(p1, row["이름"])], table[(p2, row["이름"])]
        for k, col in enumerate(COLS):
            if col == "unload":
                continue
            total += 1
            hit += a1[k] != a2[k]
    print(f"unload 리스너가 바꾼 칸(unload 열 제외) = {hit} / {total}")


BASES = {}


def main():
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(143))
    mode = sys.argv[1]
    a, b = server("A"), server("B")
    base = f"http://127.0.0.1:{PORTS['A']}/"
    BASES.update(B=f"http://127.0.0.1:{PORTS['B']}", 없는곳=f"http://127.0.0.1:{dead_port()}")
    if mode == "urllib":
        for code in (200, 404, 500):
            try:
                with urllib.request.urlopen(base + f"status?code={code}") as r:
                    print(f"urlopen /status?code={code} → 돌아옴 · status {r.status}")
            except urllib.error.HTTPError as e:
                print(f"urlopen /status?code={code} → 예외 {type(e).__name__} 「{e.code} {e.reason}」")
        print_log()
        return
    proc, c = start()
    try:
        tid, sid = open_tab(c, BASES)
        if mode == "quiet":             # 서버 로그 없이 — 페이지가 /state 로 서버에게 직접 물은 것만
            goto(c, sid, base + sys.argv[2])
            print(evaluate(c, sid, "window.__끝()"))
        elif mode in ("page", "console"):
            goto(c, sid, base + sys.argv[2])
            print(evaluate(c, sid, "window.__끝()"))
            if mode == "console":      # 콘솔(Log 도메인)에 브라우저가 적은 줄 — 포트는 이름으로 바꾼다
                print("--- 콘솔 ---")
                for e in c.take("Log.entryAdded", sid):
                    t = e["entry"]["text"]
                    for p_name, p in list(PORTS.items()) + [("없는곳", BASES["없는곳"].rsplit(":", 1)[1])]:
                        t = t.replace(f"127.0.0.1:{p}", f"<{p_name}>")
                    print(e["entry"]["source"], "·", e["entry"]["level"], "·", t)
            print_log()
        elif mode == "life":
            c.send("Target.closeTarget", {"targetId": tid})
            grid24(c, base, sys.argv[2])
        else:
            sys.exit("모드는 page | console | quiet | life | urllib")
    finally:
        stop(proc)
        a.shutdown()
        b.shutdown()


if __name__ == "__main__":
    main()
```

- ★ 24편은 `life` 모드 — **줄마다 새 탭**을 열어 시작 쪽을 띄우고, 준비 동작 뒤 **기록을 비우고** 잴 동작을 한다. 그래서 앞 줄의 bfcache 항목이 다음 줄로 안 샌다.
- ★ 「떠난 문서」와 「도착한 문서」는 문서마다 심은 **표**(`crypto.randomUUID()`)로 가른다. **되살아난 문서는 같은 표를 들고 있다** — 그것이 곧 「같은 문서」라는 증거다(창 ③).

### (2) ★★★ 본체 — 「떠날 때」 격자, 리스너 없음

**언제 쓰나** — 「닫을 때 저장」·「떠날 때 분석 전송」을 어느 이벤트에 달지 정할 때.

**던진 것** — 기록기(localStorage 에 한 줄씩)를 단 두 쪽. 첫쪽은 둘째쪽으로 가는 링크 하나.

```js
// wa24b-24-rec.js
// 24편 — 문서 수명주기 이벤트를 localStorage 의 「기록」에 한 줄씩 적는다(같은 출처면 새로고침·새 탭에서도 남는다)
// ★ 이 파일은 unload 리스너를 달지 않는다 — 다는 쪽은 페이지가 직접 단다
window.__문서 = crypto.randomUUID();              // 문서마다 다른 표 — 되살아난 문서면 같은 값이 남아 있다
const 쪽 = document.title;
function 적기(글) {
  const 기록 = JSON.parse(localStorage.getItem("기록") || "[]");
  기록.push({ 쪽, 문서: window.__문서, 글 });
  localStorage.setItem("기록", JSON.stringify(기록));
}
document.addEventListener("DOMContentLoaded", () => 적기("DOMContentLoaded"));
addEventListener("load", () => 적기("load"));
addEventListener("pageshow", e => 적기("pageshow persisted=" + e.persisted));
addEventListener("pagehide", e => 적기("pagehide persisted=" + e.persisted));
addEventListener("beforeunload", () => 적기("beforeunload"));
document.addEventListener("visibilitychange", () => 적기("visibilitychange " + document.visibilityState));
document.addEventListener("freeze", () => 적기("freeze"));
document.addEventListener("resume", () => 적기("resume"));
// 가라앉히기 — 기록이 animation frame 20장 연달아 그대로일 때까지 기다린다(다른 문서가 늦게 적는 줄까지 받으려고)
window.__가라앉음 = () => new Promise(r => {
  let 앞 = localStorage.getItem("기록"), n = 0;
  (function 한장() {
    const 지금 = localStorage.getItem("기록");
    if (지금 === 앞) n++; else { n = 0; 앞 = 지금; }
    if (n >= 20) r(지금 || "[]"); else requestAnimationFrame(한장);
  })();
});
```

```html
<!-- wa24b-24-first.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>첫쪽</title>
<script src="wa24b-24-rec.js"></script>
<p><a id="go" href="wa24b-24-second.html">다음 쪽으로</a></p>
```

```html
<!-- wa24b-24-second.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>둘째쪽</title>
<script src="wa24b-24-rec.js"></script>
<p>둘째 쪽</p>
```

```html
<!-- wa24b-24-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>격자</title>
<script>
// 「떠날 때」 격자 — 줄마다 새 탭에서 시작 → 준비 → (기록을 비우고) 동작 → 가라앉힌 뒤 기록을 읽는다
// 앞의 두 판을 칸마다 견준다 — 리스너 없음(first) · unload 리스너 있음(unload)
const 이유 = "JSON.stringify(performance.getEntriesByType('navigation')[0].notRestoredReasons?.reasons ?? null)";
const 줄 = 시작 => [
  { 이름: "링크로 떠나기",     시작, 준비: [],                            동작: ["누르기", "#go"] },
  { 이름: "새로 고침",         시작, 준비: [],                            동작: ["새로고침"] },
  { 이름: "탭 닫기(Target)",   시작, 준비: [],                            동작: ["닫기"] },
  { 이름: "탭 닫기(Page)",     시작, 준비: [],                            동작: ["Page.close"] },
  { 이름: "뒤로(둘째→첫)",     시작, 준비: [["누르기", "#go"]],           동작: ["뒤로"], 묻기: 이유 },
  { 이름: "앞으로(첫→둘째)",   시작, 준비: [["누르기", "#go"], ["뒤로"]], 동작: ["앞으로"], 묻기: 이유 },
  { 이름: "다른 탭을 앞으로",  시작, 준비: [],                            동작: ["새탭"] },
  { 이름: "그 탭에서 돌아옴",  시작, 준비: [["새탭"]],                    동작: ["돌아옴"] },
];
const 순서도 = (판, 이름) => 판.map(r => r.이름 === 이름 ? { ...r, 순서: true } : r);
const 뒤앞 = 시작 => 줄(시작).filter(r => r.이름.startsWith("뒤로") || r.이름.startsWith("앞으로"));
window.__판 = [
  ["리스너 없음", 순서도(줄("wa24b-24-first.html"), "뒤로(둘째→첫)")],
  ["unload 있음", 순서도(줄("wa24b-24-unload.html"), "앞으로(첫→둘째)")],
  ["unload 있음 + Permissions-Policy: unload=()", 뒤앞("nounload/wa24b-24-unload.html")],
  ["리스너 없음 + Cache-Control: no-store",       뒤앞("nostore/wa24b-24-first.html")],
];
</script>
```

```text
$ python3 wa24b-net.py life wa24b-24-grid.html | sed -n '1,14p'
[리스너 없음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
링크로 떠나기     ○            persisted=true    (리스너 없음) hidden            persisted=false ○              —
새로 고침         ○            persisted=false   (리스너 없음) hidden            persisted=false ○              —
탭 닫기(Target)   —            persisted=false   (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
탭 닫기(Page)     ○            persisted=false   (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
뒤로(둘째→첫)    ○            persisted=true    (리스너 없음) hidden            persisted=true  —              —
    떠난 문서(둘째쪽)  beforeunload → pagehide persisted=true → visibilitychange hidden → freeze
    도착한 문서(첫쪽)  resume → visibilitychange visible → pageshow persisted=true
    페이지에게 물음  null
앞으로(첫→둘째)  ○            persisted=true    (리스너 없음) hidden            persisted=true  —              —
    페이지에게 물음  null
다른 탭을 앞으로  —            —                (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
그 탭에서 돌아옴  —            —                (리스너 없음) visible           (새 문서 없음)  (새 문서 없음)  —
(exit 0)
```

- ★★★ **`visibilitychange → hidden` 은 떠남 여섯 줄과 「다른 탭을 앞으로」까지 일곱 줄 전부에서** 났다. **`pagehide` 는 탭만 가렸을 때(다른 탭을 앞으로) 안 났다.**
- ★★ **링크로 떠날 때 `pagehide` 가 `persisted=true`** — 떠나는 순간 **창고에 넣기로** 했다. 새로 고침과 탭 닫기는 `false` 다.
- ★★ **뒤로·앞으로에서 `pageshow persisted=true` 이고 `load` 가 없다** — 되살아났다. 떠난 문서의 순서는 `beforeunload → pagehide(persisted=true) → visibilitychange hidden → freeze`, 돌아온 문서는 **`resume → visibilitychange visible → pageshow(persisted=true)`** 다.
- **`DOMContentLoaded` 도 `load` 도 다시 안 난다** — 「초기화는 `load` 에서」라고 짠 코드는 뒤로 돌아온 페이지에서 **안 돈다.**
- ★ **HTML 명세의 순서와 같다** — 「unload a document」가 **`pagehide` → 가시성 `hidden` → (salvageable 이 거짓이면) `unload`** 로 적는다. `beforeunload` 가 그 앞에, `freeze` 는 그 뒤에 왔다.

```text
   떠남 × 이벤트 — 리스너 없는 쪽 (이 판 8줄)

                       beforeunload  pagehide        visibilitychange   돌아온 문서
   링크로 떠나기       ○             ○ p=true        hidden             (둘째쪽 새로 load)
   새로 고침           ○             ○ p=false       hidden             새로 load
   탭 닫기(Target)     —  ★          ○ p=false       hidden             —
   탭 닫기(Page)       ○             ○ p=false       hidden             —
   뒤로 · 앞으로       ○             ○ p=true        hidden             ★ pageshow p=true · load 없음
   다른 탭을 앞으로    —             — ★             hidden             —
   그 탭에서 돌아옴    —             —               visible            —

   ★ 빠짐없이 난 열 = visibilitychange (떠남 여섯 + 가림 하나)
```

### (3) ★★ 탭 닫기 — 두 CDP 명령이 다르게 굴었다

```text
$ python3 wa24b-net.py life wa24b-24-grid.html | sed -n '1,2p;5,6p;16,17p;20,21p'
[리스너 없음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
탭 닫기(Target)   —            persisted=false   (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
탭 닫기(Page)     ○            persisted=false   (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
[unload 있음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
탭 닫기(Target)   —            persisted=false   ○            hidden            (새 문서 없음)  (새 문서 없음)  —
탭 닫기(Page)     ○            persisted=false   ○            hidden            (새 문서 없음)  (새 문서 없음)  —
(exit 0)
```

- ★★ **`Target.closeTarget` 은 `beforeunload` 를 안 부르고, `Page.close` 는 부른다.** 나머지(`pagehide persisted=false` · `hidden` · `unload`)는 같다. CDP 설명이 `Page.close` 를 「beforeunload 훅이 있으면 돌리며 닫으려 한다」로 적는다.
- ★ **그래서 「닫을 때 `beforeunload` 가 온다」는 이 판에서 닫는 방법에 달렸다.** 사용자가 창을 닫는 것이 어느 쪽과 같은지는 **이 도구가 못 본다**(머리말 표).
- **두 방법 다 `pagehide` 와 `visibilitychange → hidden` 은 났다.**

```text
   탭 닫기 — 두 CDP 명령 (이 판)

                      beforeunload   pagehide     visibilitychange   unload(리스너 있으면)
   Target.closeTarget   ✕              ○ p=false    hidden             ○
   Page.close           ○              ○ p=false    hidden             ○
   ★ 갈린 칸은 beforeunload 하나 — 「닫을 때 확인 창」은 닫는 경로에 달렸다
```

### (4) ★★★ `unload` 리스너 하나 — bfcache 에서 빠진다

**던진 것** — 첫쪽에 `unload` 리스너 **한 줄**만 더한 쪽으로 같은 여덟 줄.

```html
<!-- wa24b-24-unload.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>첫쪽u</title>
<script src="wa24b-24-rec.js"></script>
<script>
addEventListener("unload", () => 적기("unload"));
window.__unload있음 = true;
</script>
<p><a id="go" href="wa24b-24-second.html">다음 쪽으로</a></p>
```

```text
$ python3 wa24b-net.py life wa24b-24-grid.html | sed -n '16,29p'
[unload 있음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
링크로 떠나기     ○            persisted=false   ○            hidden            persisted=false ○              —
새로 고침         ○            persisted=false   ○            hidden            persisted=false ○              —
탭 닫기(Target)   —            persisted=false   ○            hidden            (새 문서 없음)  (새 문서 없음)  —
탭 닫기(Page)     ○            persisted=false   ○            hidden            (새 문서 없음)  (새 문서 없음)  —
뒤로(둘째→첫)    ○            persisted=false   (리스너 없음) hidden            persisted=false ○              BrowsingInstanceNotSwapped(Circumstantial), UnloadHandlerExistsInMainFrame(PageSupportNeeded)
    페이지에게 물음  [{"reason":"masked"}]
앞으로(첫→둘째)  ○            persisted=false   ○            hidden            persisted=false ○              BrowsingInstanceNotSwapped(Circumstantial)
    떠난 문서(첫쪽u)  beforeunload → pagehide persisted=false → visibilitychange hidden → unload
    도착한 문서(둘째쪽)  DOMContentLoaded → load → pageshow persisted=false
    페이지에게 물음  [{"reason":"masked"}]
다른 탭을 앞으로  —            —                —            hidden            (새 문서 없음)  (새 문서 없음)  —
그 탭에서 돌아옴  —            —                —            visible           (새 문서 없음)  (새 문서 없음)  —
(exit 0)
```

- ★★★ **`unload` 를 단 쪽은 링크로 떠날 때 `pagehide persisted=false`** 이고 **`unload` 가 불렸다.** 뒤로 돌아오면 **`DOMContentLoaded → load → pageshow(persisted=false)`** — 처음부터 다시 만들었다.
- ★★★ **CDP 가 이유를 말한다** — 뒤로(첫쪽u 로 돌아옴): **`UnloadHandlerExistsInMainFrame(PageSupportNeeded)`** 와 `BrowsingInstanceNotSwapped(Circumstantial)`.
- ★★ **옆 쪽까지 빠졌다** — `unload` 가 없는 **둘째쪽도** 앞으로 올 때 되살아나지 못했다(`BrowsingInstanceNotSwapped` 하나). 뒤로 떠날 때 둘째쪽의 `pagehide` 도 `persisted=false` 다. 이 편은 그 이유를 **CDP 가 준 이름 이상으로 풀지 않았다.**
- ★★ **페이지에게 같은 것을 물으면 `[{"reason":"masked"}]`** — `performance.getEntriesByType("navigation")[0].notRestoredReasons` 가 **이유를 가렸다.** CDP 는 두 이름을 줬다. **같은 질문을 다른 창으로 물었더니 답의 세기가 달랐다**(제5의 상태).
- **`unload` 열을 빼고 두 판이 갈린 칸 7 / 40** — 아래 (5)의 집계 줄.

```text
   뒤로 — 첫쪽에 unload 리스너가 있을 때와 없을 때

   없음    첫쪽 ─(링크)─▶ 둘째쪽      첫쪽: pagehide p=true ─▶ 창고
           둘째쪽 ─(뒤로)─▶ 첫쪽      첫쪽: resume → visible → pageshow p=true     load 없음

   있음    첫쪽u ─(링크)─▶ 둘째쪽     첫쪽u: pagehide p=false → hidden → unload ─▶ 버림
           둘째쪽 ─(뒤로)─▶ 첫쪽u     첫쪽u: DOMContentLoaded → load → pageshow p=false
                                     CDP: UnloadHandlerExistsInMainFrame · BrowsingInstanceNotSwapped
```

### (5) bfcache 를 막는 것 · 안 막는 것 — `Permissions-Policy` 와 `no-store`

```text
$ python3 wa24b-net.py life wa24b-24-grid.html | sed -n '31,$p'
[unload 있음 + Permissions-Policy: unload=()]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
뒤로(둘째→첫)    ○            persisted=true    (리스너 없음) hidden            persisted=true  —              —
    페이지에게 물음  null
앞으로(첫→둘째)  ○            persisted=true    —            hidden            persisted=true  —              —
    페이지에게 물음  null

[리스너 없음 + Cache-Control: no-store]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
뒤로(둘째→첫)    ○            persisted=true    (리스너 없음) hidden            persisted=true  —              —
    페이지에게 물음  null
앞으로(첫→둘째)  ○            persisted=true    (리스너 없음) hidden            persisted=true  —              —
    페이지에게 물음  null

unload 리스너가 바꾼 칸(unload 열 제외) = 7 / 40
(exit 0)
```

- ★★ **`Permissions-Policy: unload=()` 를 준 문서는 `unload` 리스너가 있어도 `unload` 가 안 불리고**(앞으로 줄의 `unload` 열이 `—`) **bfcache 에 들어갔다**(`persisted=true` · 이유 없음). Chrome 의 설명 그대로 — 「사이트가 `unload` 를 끄는(opt-out) 정책」이다.
- ★★ **`Cache-Control: no-store` 인 주 문서도 이 판에서는 되살아났다**(`persisted=true` · 이유 없음). CDP 의 이유 목록에는 `MainResourceHasCacheControlNoStore` 라는 이름이 **있다** — 이 판에서는 그것이 **안 걸렸다.** ★ **「`no-store` 면 bfcache 에 안 들어간다」를 전제로 두지 마라** — 조건은 브라우저가 정하고 판마다 바뀐다.
- 마지막 줄 **`unload 리스너가 바꾼 칸(unload 열 제외) = 7 / 40`** — 앞의 두 판(여덟 줄 × 다섯 열)을 스크립트가 칸마다 견줬다.

```text
   뒤로·앞으로에서 되살아났나 — 네 판 (이 판)

   판                                       뒤로       앞으로     CDP 이유
   리스너 없음                              ○ p=true   ○ p=true   —
   unload 있음                              ✕          ✕          UnloadHandlerExistsInMainFrame · BrowsingInstanceNotSwapped
   unload 있음 + Permissions-Policy unload=()  ○        ○          —   (unload 도 안 불림)
   리스너 없음 + Cache-Control: no-store    ○          ○          —   ★ 이 판에서는 막지 않았다
```

### (6) `DOMContentLoaded` 대 `load` — 서버가 이미지를 붙잡으면

**[HTML 08번 주제](../../languages/html/syntax/08-script-loading/2-summary.md)의 (1)이 `defer`·모듈은 `DOMContentLoaded` 앞, `async` 는 어디든, `load` 는 `readyState=complete` 를 쟀다.** 여기서 더하는 한 칸 — **서버가 `/go` 를 받을 때까지 이미지를 안 주고, `DOMContentLoaded` 리스너가 그 `/go` 를 준다.** 시간이 아니라 순서로 묶었으므로 **`load` 가 이미지를 기다린다면 반드시 이 순서**가 나와야 한다.

```html
<!-- wa24b-24-order.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>순서</title>
<script>
window.__O = [];
const 적 = 글 => __O.push(글 + " · readyState=" + document.readyState);
적("파싱 중 스크립트");
document.addEventListener("DOMContentLoaded", () => {
  적("DOMContentLoaded · 이미지 complete=" + document.getElementById("im").complete);
  fetch("/go?id=img24");                           // 이제야 서버가 이미지를 보낸다
});
addEventListener("load", () => 적("load · 이미지 complete=" + document.getElementById("im").complete));
window.__끝 = async () => __O.join("\n");
</script>
<script defer src="wa24b-24-defer.js"></script>
<img id="im" src="/img?id=img24" alt="">
<script>
document.getElementById("im").addEventListener("load", () => 적("img load"));
</script>
```

```js
// wa24b-24-defer.js
// 24편 — defer 스크립트(파싱이 끝난 뒤, DOMContentLoaded 앞에 돈다)
window.__O.push("defer 스크립트 실행 · readyState=" + document.readyState);
```

```text
$ python3 wa24b-net.py page wa24b-24-order.html
파싱 중 스크립트 · readyState=loading
defer 스크립트 실행 · readyState=interactive
DOMContentLoaded · 이미지 complete=false · readyState=interactive
img load · readyState=interactive
load · 이미지 complete=true · readyState=complete
--- 서버 로그 ---
A GET /img  도착 — /go 를 기다린다
A   go 를 받고 이미지를 보냈다
(exit 0)
```

- ★★ **`DOMContentLoaded` 때 이미지는 아직(`complete=false`)** — 트리는 다 섰고 `defer` 도 돌았지만 이미지는 서버가 붙잡고 있다.
- ★★ **`load` 는 이미지가 온 뒤에야** 났다(`img load` → `load` · `complete=true` · `readyState=complete`). 서버 로그가 **「go 를 받고 이미지를 보냈다」** 로 그 사이를 증명한다.
- **`defer` 스크립트는 `readyState=interactive` 에서, `DOMContentLoaded` 앞**에 — 08편과 같다.

```text
   파싱 ─▶ defer 실행 ─▶ DOMContentLoaded ─(이 리스너가 /go)─▶ 서버가 이미지를 보냄 ─▶ img load ─▶ load
           interactive    interactive                                                             complete
   ★ load 는 「이미지까지」를 기다린다 — 초기화에 DOM 만 필요하면 DOMContentLoaded 로 충분하다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   document  DOMContentLoaded · visibilitychange(document.visibilityState: 'visible' | 'hidden') · freeze · resume
   window    load · beforeunload · pagehide(e.persisted) · pageshow(e.persisted) · unload
   읽기      document.readyState('loading' | 'interactive' | 'complete')
             performance.getEntriesByType('navigation')[0].notRestoredReasons   (이 판은 masked 만 줬다)
   헤더      Permissions-Policy: unload=()        이 문서에서 unload 를 끈다(Chrome)

   관용구 — 떠날 때 저장
     document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') 저장(); });
     addEventListener('pagehide', e => { 저장(); });                  ← unload 대신
     addEventListener('pageshow', e => { if (e.persisted) 되살아남(); });  ← load 대신 「돌아왔다」
```

### 어디서 헷갈리나

```text
   「떠날 때」 무엇을 달까 — 이 판의 격자에서 고른 것

   저장·전송          visibilitychange(hidden)   ← 떠남 여섯 + 탭 가림, 빠짐없이
                      + pagehide                 ← 떠남에서만(탭 가림 ✕)
   돌아옴             pageshow(e.persisted)      ← load 는 되살아날 때 없다
   확인 창            beforeunload              ← 닫는 경로에 따라 없다
   쓰지 않음          unload                    ← 불려도 bfcache 에서 빠진다(이 판의 Chrome)
```

- **`pagehide` 는 `unload` 의 새 이름이 아니다** — `persisted` 로 「창고에 넣나」를 알려 주고, 넣을 때는 `unload` 가 **안 난다**((2)·(4)).
- **`pageshow` 는 처음 열 때도 난다**(`persisted=false`) — 되살아남만 가르려면 `persisted` 를 본다.
- **`beforeunload` 는 닫는 방법에 따라 안 날 수 있다**((3)).

## 어디서 틀리나

### 1. 「떠날 때 저장」을 `unload` 에 단다

**이 판의 Chrome 에서는 불리긴 했다** — 대신 **그 페이지와 옆 페이지가 bfcache 에서 빠졌다**((4)). 그리고 Chrome 은 `unload` 를 단계적으로 끄는 중이다. `pagehide`·`visibilitychange` 에 단다.

### 2. 초기화를 `load` 에만 둔다

**뒤로 돌아온 페이지에서는 `load` 가 없다**((2)). 「돌아왔을 때 새로 고쳐야 하는 것」(로그인 상태·장바구니 수)은 **`pageshow` 의 `persisted`** 로 받는다.

### 3. `beforeunload` 로 「닫힘」을 센다

**`Target.closeTarget` 으로 닫으면 `beforeunload` 가 안 났다**((3)). **탭만 가릴 때도 안 난다**((2)). 세려면 `visibilitychange → hidden` 이다.

### 4. `pagehide` 만 달아 두면 탭 전환도 잡힌다고 믿는다

**다른 탭을 앞으로 가져왔을 때 `pagehide` 는 없었다**((2)) — `visibilitychange` 만 났다. 모바일에서는 그대로 앱이 죽을 수 있다(이 편은 **못 쟀다**).

### 5. 「`no-store` 면 bfcache 에 안 들어간다」를 전제로 둔다

**이 판에서는 들어갔다**((5)). bfcache 적격 조건은 **브라우저 구현**이다 — 확인은 CDP 의 `backForwardCacheNotUsed` 로 한다.

### 6. `notRestoredReasons` 가 원인을 말해 줄 것이라 믿는다

**이 판에서 페이지가 받은 것은 `masked` 하나**였다((4)). 원인 분석은 개발자 도구(CDP)로 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `pagehide` → 가시성 `hidden` → (salvageable 이 거짓일 때만) `unload` 순서 | **명세**(HTML — unload a document) · 이 판도 그랬다((2)·(4)) |
| 되살아나면 `pageshow` 가 `persisted=true` · `load` 없음 | **명세의 틀**(page transition 이벤트의 `persisted`) · 이 판도 그랬다((2)) |
| ★ **`unload` 리스너가 있으면 bfcache 에 못 들어감** | ★ **Chrome 구현**(CDP 이유 `UnloadHandlerExistsInMainFrame`) — HTML 명세에서 이 문장은 찾지 못했다 |
| ★ `unload` 없는 **옆 쪽까지** 빠진 것(`BrowsingInstanceNotSwapped`) | ★ **이 판의 관찰** |
| ★ `no-store` 주 문서가 들어간 것 | ★ **이 판의 관찰** — 조건은 Chrome 이 판마다 바꾼다 |
| `Permissions-Policy: unload=()` 가 `unload` 를 끄는 것 | **Chrome 문서**(Chrome 115 부터) · 이 판도 그랬다((5)) |
| `unload` 가 불리나 | ★ **Chrome 이 페이지 로드 비율로 끄는 중** — 이 판에서는 불렸다 |
| `Target.closeTarget` 이 `beforeunload` 를 안 부르는 것 | ★ **도구의 성질** |
| `notRestoredReasons` 가 `masked` 인 것 | ★ **이 판의 관찰** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 떠날 때 저장·전송 | `visibilitychange → hidden` (+ `pagehide`) | `unload` · `beforeunload` |
| 「저장 안 한 변경이 있어요」 확인 창 | `beforeunload` — **변경이 있을 때만 달고 없으면 뗀다** | 늘 달아 두기 |
| 돌아왔을 때 새로 고치기 | `pageshow` + `e.persisted` | `load` |
| DOM 만 있으면 되는 초기화 | `DOMContentLoaded` 또는 `defer` | `load`(이미지까지 기다린다) |
| bfcache 에서 왜 빠졌나 | CDP `Page.backForwardCacheNotUsed` | `notRestoredReasons` 만 믿기 |

## 핵심 문장

1. **떠남 여섯 가지와 탭 가림에서 빠짐없이 난 것은 `visibilitychange → hidden` 하나**다.
2. **`pagehide` 의 `persisted` 가 「창고(bfcache)에 넣나」** 를 말하고, 넣을 때는 `unload` 가 없다.
3. **되살아난 문서는 `load` 없이 `resume → visible → pageshow(persisted=true)`** 만 받는다.
4. **이 판의 Chrome 은 `unload` 리스너 하나로 그 쪽을 bfcache 에서 뺐다** — CDP 이유 `UnloadHandlerExistsInMainFrame`. 이것은 명세가 아니라 구현이다.
5. **`load` 는 이미지까지 기다린다** — 서버가 붙잡은 이미지가 오기 전에는 안 났다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 24번)
- [HTML 08번 주제](../../languages/html/syntax/08-script-loading/2-summary.md) — **스크립트 실행 시점과 `DOMContentLoaded`·`load` 순서의 정본.** 그쪽은 `defer`/`async`/모듈, 여기는 **떠날 때와 돌아올 때**
- [16번 주제](../16-event-propagation-phases/2-summary.md) — `load` 가 버블하지 않는 이벤트라는 것
- [20번 주제](../20-listener-lifetime/2-summary.md) — 리스너가 문서를 붙드는 것(누수). bfcache 의 문서는 **통째로** 남는다
- [목록의 **34번 주제**](../34-send-beacon-and-keepalive/) — `sendBeacon`(떠날 때 보내기)
- [25번 주제](../25-fetch-request-response/2-summary.md) — 같은 하네스로 네트워크 묶음을 시작한다

## 용어 풀이

- **bfcache(뒤로·앞으로 캐시)** — 떠난 문서를 **통째로 얼려** 두었다가 뒤로·앞으로에서 되살리는 브라우저 캐시.
- **`persisted`** — `pagehide`·`pageshow` 의 필드. 창고에 넣나(넣었던 것이 돌아왔나).
- **salvageable** — HTML 명세의 문서 상태. 거짓이면 `unload` 가 난다.
- **`visibilitychange`** — 문서가 보이다가 안 보이게(또는 반대로) 됐다는 알림. `document.visibilityState`.
- **`freeze`/`resume`** — 문서가 얼려졌다/풀렸다(Page Lifecycle). bfcache 에 넣을 때와 꺼낼 때 났다.
- **`notRestoredReasons`** — 페이지가 「왜 안 되살아났나」를 묻는 창. 이 판은 `masked` 만 줬다.
- **`Permissions-Policy: unload=()`** — 그 문서에서 `unload` 를 끄는 응답 헤더(Chrome).
- **「떠날 때」 격자** — 떠나는 방법 × 이벤트를 두 판으로 채운 표. 이 편의 본체.

## 더 들어가면

- **iframe 안의 `unload`**(`UnloadHandlerExistsInSubFrame`)는 던지지 않았다.
- **`beforeunload` 로 확인 창을 띄우는 것**(`preventDefault()`)은 헤드리스에서 대화 상자를 다뤄야 해서 던지지 않았다.
- **Chrome 의 `unload` 기본값 변경**이 이 판에 걸렸는지는 페이지 로드마다 다를 수 있다 — 판이 오르면 (4)를 다시 찍는다.
