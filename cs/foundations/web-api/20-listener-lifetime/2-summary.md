# web-api/20 — 리스너 수명: `once`·`signal` 로 해제하기와 누수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ⑥ 「GC 창」이다** — 떼어 낸 노드에 `FinalizationRegistry` 를 걸고 `gc()` 를 불러 **콜백이 불렸나(= 회수됐나)** 를 판마다 센다. 「리스너가 노드를 붙들고 있나」를 **힙 스냅샷이 아니라 회수 여부로** 물었다(제5의 상태 — 아래 창 표).\
> ★★ **이 편은 바이트를 재지 않았다.** 「누수가 메모리를 얼마나 먹나」는 이 문서의 주장 범위 밖이다. 잰 것은 **회수됐나(참/거짓) × 10판**뿐이다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「add an event listener」(이미 abort 된 signal 이면 그냥 돌아간다 · signal 에 「리스너를 지우는」 abort 단계를 단다) · 「signal abort」·「run the abort steps」(abort 알고리즘을 먼저 돌리고 **그다음** `abort` 이벤트) · `AbortSignal.timeout()`·`any()` · 「3.2.1 Garbage collection」 절. 회수 창의 명세 근거는 [JS 갈래 23번 주제](../../languages/js/syntax/23-map-set-and-weak-collections/2-summary.md)의 (5)가 정본이다(ECMA-262 — 「어떤 객체가 회수된다는 보장을 하지 않는다」). 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. GC 격자만 Chrome 을 **`--js-flags=--expose-gc`** 로 띄워 페이지에 `gc()` 를 열었다. 하네스는 아래 (1)에 전문이 있다([16번 주제](../16-event-propagation-phases/2-summary.md)의 하네스에 단계 몇 개와 `--gc` 를 더한 판이다).\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★★ [15번 주제](../15-listener-registration/2-summary.md)가 **이 편의 절반**이다 — 동일성 키(타입·콜백·`capture`)와 안 지워지는 4 / 14칸, `once` 가 **부르기 직전에** 지워지는 것, `signal` 하나로 세 자리를 떼는 것, 이미 abort 된 signal 로는 **등록이 안 되는 것(호출 0회)** 을 거기서 쟀다. 여기는 그것을 **다시 재지 않고 인용**하고, **「리스너가 무엇을 붙드나」** 를 GC 로 묻는다. `AbortController` 자체는 JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **41번**이 정본이다.\
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
| **안 흔들린다** | `signal` 쪽 모든 호출 횟수 · `reason` 의 이름과 문구 · `aborted` 값 | 캡처 세 판이 **한 글자도 같았다** |
| ★★ **안 흔들렸지만 성질의 근거로 쓰지 않는다** | GC 격자의 **「불린 판 / 10판」** — 이 판에서 전부 `10/10` 아니면 `0/10` 이었다 | ★ **명세가 보장하는 것은 「강하게 붙잡힌 것은 회수되지 않는다」 쪽뿐**이다(`0/10` 칸). `10/10` 칸은 **이 판의 V8 이 `gc()` 한 번에 거뒀다**는 관찰이다([JS 23번 주제](../../languages/js/syntax/23-map-set-and-weak-collections/2-summary.md)의 (5)와 같은 선 긋기) |
| ★ **흔들려도 되는 칸** | GC 격자의 **「gc() 뒤 몇 번째 틱」** 블록 | 명세가 콜백의 시점을 묶지 않는다. 이 판에서는 세 번 다 같았지만 **그 숫자에 결론을 세우지 않는다** — 그래서 블록을 따로 뗐다 |
| ★ **못 잰다** | 리스너 하나가 붙드는 **바이트** · 누수가 **얼마나** 느리게 만드나 | 힙 스냅샷도 시간도 재지 않았다. **안 돌려 본 것이 아니라 이 편의 창이 그것을 못 본다** |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | 떼어 낸 노드는 트리에 없다. 리스너는 원래 트리에 자국을 안 남긴다 |
| 창 ② 노드 프로브 | **부적용** | 떼어 낸 노드를 가리키는 순간 **그 참조가 노드를 살린다** — 물으려는 것을 물음이 망친다 |
| 창 ③ 같은 것을 두 번 읽기 | **부적용** | — |
| 창 ④ 디스패치 계수기 | ★ **쓴다** | `signal`·`any`·`timeout` 뒤 **몇 번 불렸나**((5)\~(7)) |
| **창 ⑥ GC 창 — `FinalizationRegistry` + `gc()`** | ★★★ **본체** | 떼어 낸 노드가 **회수됐나**((2)\~(4)) |
| 창 ⑤ 콘솔 | **부적용** | 누수는 경고를 안 낸다 |

- ★★★ **제5의 상태 — 「새나」를 바이트가 아니라 회수 여부로 물었다.** 「리스너가 노드를 붙든다」는 보통 힙 스냅샷으로 확인한다. 이 편은 그 창을 열지 않고 **같은 질문을 `FinalizationRegistry` 로** 물었다 — 노드가 회수되면 콜백이 불린다.
- ★ **바꾼 창이 못 보는 것** — ① **무엇이** 노드를 붙들었나(경로)는 안 보인다. 칸을 **하나씩 바꿔 가며** 원인을 가른 것이 그 대신이다. ② **몇 바이트**인지 안 보인다. ③ `0/10` 은 「20틱 안에 안 불렸다」이지 「영원히 안 회수된다」가 아니다 — 다만 `0/10` 칸은 **전부 강한 참조가 남아 있는 칸**이라 명세상 회수될 수 없다.

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★ **누수의 크기(바이트)·속도 영향** | 힙 스냅샷·성능 추적을 안 열었다. **이 편은 크기를 주장하지 않는다** |
| **무엇이 붙들었나(보존 경로)** | GC 창은 「회수됐나」만 말한다. 경로는 칸을 바꿔 가며 **간접으로** 갈랐다 |
| **지금 달려 있는 리스너 목록** | 표준에 그런 API 가 없다([15번 주제](../15-listener-registration/2-summary.md)) |
| **`gc()` 없는 평소의 GC 시점** | `--expose-gc` 로 **억지로** 부른 판이다. 평소에 언제 거두는지는 이 편이 모른다 |

## 한눈에 — 쉽게 말하면

**★ 리스너는 「기억하는 쪽지」다. 쪽지를 어디에 붙였느냐가 수명을 정한다. 노드 자신에게 붙인 쪽지는 노드와 함께 버려지지만, `window` 처럼 오래 사는 곳에 붙인 쪽지는 그 안에 적힌 노드를 끝까지 살려 둔다.**

| 비유 | 실체 |
|---|---|
| 쪽지 | 리스너 함수(클로저) |
| 쪽지에 적힌 이름 | 클로저가 가리키는 변수 — 여기서는 노드 `n` |
| 쪽지를 붙인 게시판 | 리스너를 단 대상(`n` 자신 · `window` · `document`) |
| 게시판이 사라지면 쪽지도 사라진다 | 대상이 회수되면 그 리스너 목록도 함께 간다 |
| 오래 사는 게시판 | `window`·`document` — 페이지가 살아 있는 한 산다 |
| 쪽지를 떼는 세 방법 | `removeEventListener` · `once` · `signal` + `abort()` |
| 게시판 여러 곳의 쪽지를 한 줄로 묶은 끈 | `AbortSignal` 하나 |

- ★ **누수는 「리스너가 있다」가 아니라 「오래 사는 곳의 리스너가 짧게 살아야 할 것을 가리킨다」** 는 모양이다((2)).
- ★ **떼는 방법이 틀리면 쪽지는 그대로다** — `capture` 를 안 맞추고 지우면 에러도 없이 남는다([15번 주제](../15-listener-registration/2-summary.md)의 4 / 14칸이 **여기서 누수가 된다**, (2)).

```text
   떼어 낸 노드 n 을 누가 붙드나

   노드 자신에 단 리스너                       window 에 단 리스너
   ─────────────────────                       ─────────────────────
      n ──리스너 목록──▶ f                        window ──리스너 목록──▶ f
      ▲                  │                          (페이지가 사는 한 산다)   │
      └────── 클로저 ────┘                                                    │
                                                  n ◀──────── 클로저 ────────┘
   n 과 f 가 서로만 가리킨다
   → 바깥에서 닿는 길이 없다 → 회수된다         window 에서 n 까지 길이 있다 → 안 회수된다
```

## 이 주제가 답하려는 질문

1. **리스너 하나가 어떤 객체 그래프를 붙드나** — 노드를 떼면 회수되는 경우와 안 되는 경우를 무엇이 가르나.
2. **떼는 세 방법(`removeEventListener`·`once`·`signal`)이 각각 무엇을 풀어 주나** — 그리고 어디서 조용히 실패하나.
3. **`AbortSignal` 하나로 여러 리스너를 한 번에 떼는 형태**는 어떻게 도나 — 이미 abort 된 신호 · `abort` 이벤트의 순서 · `any`·`timeout`.

## 동작 방식

### (1) 하네스 — 진짜 입력과 `--gc`

**던진 것** — 이 묶음(20\~23)의 모든 CDP 블록은 아래 하네스 하나로 받았다. [16번 주제](../16-event-propagation-phases/2-summary.md)의 하네스에 **마우스·터치 한 동작씩 보내는 단계 · 날것의 키 이벤트 · CDP 의 조합 흉내(`ime`·`insert`) · `--gc`** 를 더했고, 끝낼 때 **자기가 띄운 프로세스만** 끝낸 뒤 **자기 프로필을 놓을 때까지 기다려** 지운다.

```python
# wa20b-cdp.py
#!/usr/bin/env python3
"""CDP 로 헤드리스 Chrome 에 붙어 진짜 입력(마우스·휠·키)을 넣고 페이지가 적은 줄을 찍는다.

사용:
  wa20b-cdp.py page [--gc] <html파일>
      페이지를 열고 load 를 기다린 뒤 window.__단계 (배열) 를 차례로 실행하고
      window.__끝() 이 돌려준 문자열을 표준 출력에 찍는다.
  wa20b-cdp.py log [--gc] <html파일>
      같은 일을 한 뒤 콘솔 경고(Log.entryAdded)를 「출처 · 수준 · 문구」 한 줄씩 찍고 줄 수를 센다.
  --gc 를 주면 Chrome 을 --js-flags=--expose-gc 로 띄운다(페이지에 gc() 가 생긴다).
  <html파일> 뒤에 #조각 을 붙이면 그 조각을 주소에 실어 연다(페이지가 location.hash 로 읽는다).

단계 꼴:
  ["js",    식]                 페이지 안에서 식을 평가한다(프로미스면 끝까지 기다린다)
  ["click", 선택자]             그 요소의 getBoundingClientRect 한가운데를 진짜 마우스로 누른다
  ["clickat", 선택자, dx, dy]   그 요소의 왼쪽 위 모서리에서 (dx, dy) 떨어진 점을 누른다
  ["move",  선택자]             그 한가운데로 진짜 마우스를 옮긴다
  ["moveat", 선택자, dx, dy]    그 요소의 왼쪽 위 모서리에서 (dx, dy) 떨어진 점으로 옮긴다
  ["wheel", 선택자, 세로량]     그 한가운데로 마우스를 옮긴 뒤 진짜 휠을 굴린다
  ["key",   key, code, 가상키코드, 글자]  진짜 키를 누르고 뗀다(글자가 있으면 keyDown 에 싣는다)
  ["tap",   선택자]             그 한가운데를 손가락으로 댔다 뗀다(끌지 않는다)
  ["touch", 선택자, 세로량]     그 한가운데에 손가락을 대고 위로 세로량만큼 다섯 번에 나눠 끈 뒤 뗀다
  ["mouse", 종류, 선택자, dx, dy, 덧인자]
                                마우스 이벤트 하나(mouseMoved·mousePressed·mouseReleased)를 보낸다.
                                dx 가 null 이면 한가운데. 덧인자(사전)는 CDP 인자에 그대로 얹는다(button·buttons·pointerType 등)
  ["touchpt", 종류, 선택자, dx, dy]
                                터치 이벤트 하나(touchStart·touchMove·touchEnd)를 보낸다. touchEnd 는 점 없이 보낸다
  ["rawkey", 인자사전]          Input.dispatchKeyEvent 를 그 인자로 한 번 보낸다(누르기·떼기를 따로 적는다)
  ["ime", 글자, 선택시작, 선택끝]  Input.imeSetComposition — 조합 중인 글자를 바꾼다(CDP 가 흉내 내는 조합)
  ["insert", 글자]              Input.insertText — 조합을 그 글자로 확정한다(CDP 가 흉내 내는 확정)

  선택자가 「js:」로 시작하면 그 뒤를 요소를 돌려주는 식으로 평가한다(그림자 안의 요소를 가리킬 때).
★ 좌표는 매번 요소의 getBoundingClientRect 에서 새로 계산한다(손으로 적은 숫자가 없다).
★ 기다림은 시간 상수가 아니라 이벤트다 — Page.loadEventFired 를 받은 뒤에 시작하고,
  CDP 의 Input.dispatch* 는 렌더러가 입력을 처리한 뒤에 응답한다.
  페이지 쪽 기다림(스크롤이 끝났나 등)은 페이지가 프로미스로 돌려준다.
★ 포트는 0 — Chrome 이 빈 포트를 고르고 프로필의 DevToolsActivePort 에 적는다.
★ 브라우저는 자기 프로필 경로로 띄우고 자기가 띄운 프로세스만 끝낸다.
"""
import json, os, shutil, signal, subprocess, sys, time, urllib.request
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
PROF = os.path.join(HERE, f".prof-wa20b-{os.getpid()}")
FLAGS = ["--headless", "--disable-gpu", "--no-sandbox", "--window-size=1000,800",
         "--remote-debugging-port=0", f"--user-data-dir={PROF}", "about:blank"]


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
            for i, e in enumerate(self.events):
                if e.get("method") == method and (sid is None or e.get("sessionId") == sid):
                    return self.events.pop(i).get("params", {})
            self.events.append(json.loads(self.ws.recv()))


def start(extra):
    shutil.rmtree(PROF, ignore_errors=True)
    proc = subprocess.Popen(["google-chrome"] + extra + FLAGS,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    port_file = os.path.join(PROF, "DevToolsActivePort")
    for _ in range(400):          # 브라우저가 CDP 를 열 때까지 — 순서만 기다린다(값에는 안 들어간다)
        try:
            port = open(port_file).read().split()[0]
            v = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"))
            return proc, Cdp(v["webSocketDebuggerUrl"])
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("CDP 가 안 열렸다")


def evaluate(c, sid, expr):
    r = c.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True,
                                    "returnByValue": True, "userGesture": False}, sid)
    if "exceptionDetails" in r:
        d = r["exceptionDetails"]
        return "«예외 " + (d.get("exception", {}).get("description") or d.get("text", "?")) + "»"
    return r.get("result", {}).get("value")


def center(c, sid, sel, off=None):
    at = "[r.x + r.width / 2, r.y + r.height / 2]" if off is None else \
         "[r.x + %s, r.y + %s]" % (json.dumps(off[0]), json.dumps(off[1]))
    el = sel[3:] if sel.startswith("js:") else "document.querySelector(" + json.dumps(sel) + ")"
    xy = evaluate(c, sid, "(() => { const r = (" + el + ").getBoundingClientRect(); return " + at + "; })()")
    if not isinstance(xy, list):
        raise RuntimeError("좌표를 못 얻었다: " + sel + " " + str(xy))
    return xy


def main():
    # timeout 등으로 SIGTERM 을 받아도 finally 가 돌아 자기 브라우저와 프로필을 치우게 한다
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(143))
    args = sys.argv[1:]
    extra = []
    if "--gc" in args:
        args.remove("--gc")
        extra = ["--js-flags=--expose-gc"]
    mode, path = args[0], args[1]
    frag = ""
    if "#" in path:                      # 파일#조각 — 조각은 페이지가 읽는다
        path, frag = path.split("#", 1)
        frag = "#" + frag
    url = "file://" + os.path.abspath(path) + frag
    proc, c = start(extra)
    try:
        tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
        for m in ("Page.enable", "Runtime.enable", "Log.enable"):
            c.send(m, sid=sid)
        c.send("Page.navigate", {"url": url}, sid)
        c.wait("Page.loadEventFired", sid)
        steps = json.loads(evaluate(c, sid, "JSON.stringify(window.__단계 || [])"))
        for st in steps:
            if os.environ.get("WA20B_DEBUG"):
                print("단계", st, file=sys.stderr, flush=True)
            kind = st[0]
            if kind == "js":
                v = evaluate(c, sid, st[1])
                if isinstance(v, str) and v.startswith("«예외"):
                    raise RuntimeError(st[1] + " -> " + v)
            elif kind in ("click", "clickat"):
                x, y = center(c, sid, st[1], st[2:4] if kind == "clickat" else None)
                c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y}, sid)
                for t in ("mousePressed", "mouseReleased"):
                    c.send("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left",
                           "clickCount": 1, "buttons": 1 if t == "mousePressed" else 0}, sid)
            elif kind in ("move", "moveat"):
                x, y = center(c, sid, st[1], st[2:4] if kind == "moveat" else None)
                c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y}, sid)
            elif kind == "wheel":
                x, y = center(c, sid, st[1])
                c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y}, sid)
                c.send("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": x, "y": y,
                       "deltaX": 0, "deltaY": st[2]}, sid)
            elif kind == "key":
                # ["key", key, code, 가상키코드, 글자] — 누르고 뗀다
                for t in ("keyDown", "keyUp"):
                    prm = {"type": t, "key": st[1], "code": st[2],
                           "windowsVirtualKeyCode": st[3], "nativeVirtualKeyCode": st[3]}
                    if t == "keyDown" and len(st) > 4 and st[4]:
                        prm["text"] = st[4]
                    c.send("Input.dispatchKeyEvent", prm, sid)
            elif kind == "tap":
                x, y = center(c, sid, st[1])
                c.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}, sid)
                c.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}, sid)
            elif kind == "touch":
                x, y = center(c, sid, st[1])
                c.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}, sid)
                for k in range(1, 6):
                    c.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y - st[2] * k / 5}]}, sid)
                c.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}, sid)
            elif kind == "mouse":
                off = None if st[3] is None else st[3:5]
                x, y = center(c, sid, st[2], off)
                prm = {"type": st[1], "x": x, "y": y}
                prm.update(st[5] if len(st) > 5 else {})
                c.send("Input.dispatchMouseEvent", prm, sid)
            elif kind == "touchpt":
                if st[1] == "touchEnd":
                    c.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}, sid)
                else:
                    off = None if st[3] is None else st[3:5]
                    x, y = center(c, sid, st[2], off)
                    c.send("Input.dispatchTouchEvent", {"type": st[1], "touchPoints": [{"x": x, "y": y}]}, sid)
            elif kind == "rawkey":
                c.send("Input.dispatchKeyEvent", st[1], sid)
            elif kind == "ime":
                c.send("Input.imeSetComposition", {"text": st[1], "selectionStart": st[2], "selectionEnd": st[3]}, sid)
            elif kind == "insert":
                c.send("Input.insertText", {"text": st[1]}, sid)
            else:
                raise RuntimeError("모르는 단계: " + kind)
        out = evaluate(c, sid, "window.__끝()")
        if mode == "page":
            print(out)
        elif mode == "log":
            n = 0
            for e in c.events:
                if e.get("method") == "Log.entryAdded" and e.get("sessionId") == sid:
                    en = e["params"]["entry"]
                    print(en.get("source"), "·", en.get("level"), "·", en.get("text"))
                    n += 1
            print(f"(Log 도메인 항목 {n} 줄)")
        else:
            sys.exit("모드는 page | log")
    finally:
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


if __name__ == "__main__":
    main()
```

### (2) ★★★ 본체 — 떼어 낸 노드가 회수되나 · 12칸 × 10판

**언제 쓰나** — 「화면에서 지운 컴포넌트가 메모리에 남는다」·「`once` 를 썼으니 새지 않겠지」를 확인하고 싶을 때.

**던진 것** — 판마다 `<p>` 하나를 문서에 붙이고, 칸마다 **한 가지**만 해 둔 뒤 떼어 낸다. 그 노드에 `FinalizationRegistry` 를 걸고, 잡을 한 번 넘긴 뒤 `gc()` 를 부르고, **20틱** 안에 콜백이 불리나를 본다. 칸마다 10판. 칸끼리 섞이지 않게 **판마다 이벤트 형 이름을 새로** 지었다(`형1`, `형2` …).

```html
<!-- wa20b-20-gc.html -->
<!doctype html>
<meta charset="utf-8">
<title>20-gc</title>
<div id="자리"></div>
<script>
// 떼어 낸 노드가 회수되나 — FinalizationRegistry 콜백이 불렸나를 판마다 센다.
// 이 페이지는 --js-flags=--expose-gc 로 띄운 Chrome 에서만 돈다(gc() 가 있어야 한다).
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const 판수 = 10, 기다림 = 20;
const 틱 = () => new Promise(r => setTimeout(r, 0));
const 전역배열 = [];

// 칸마다: 노드 n 을 받아 무엇이 n 을 붙들게 할지 정한다. 형은 칸마다 다르다(칸끼리 안 섞이게).
const 칸들 = [
  ['리스너 없음',                                  (n, 형) => {}],
  ['노드 자신에 단 리스너 · 클로저가 n',           (n, 형) => { n.addEventListener(형, () => n.textContent); }],
  ['window 에 단 리스너 · 클로저가 n',             (n, 형) => { addEventListener(형, () => n.textContent); }],
  ['window · once · 한 번 던진 뒤',                (n, 형) => { addEventListener(형, () => n.textContent, { once: true }); dispatchEvent(new Event(형)); }],
  ['window · once · 안 던짐',                      (n, 형) => { addEventListener(형, () => n.textContent, { once: true }); }],
  ['window · signal · abort() 뒤',                 (n, 형) => { const c = new AbortController(); addEventListener(형, () => n.textContent, { signal: c.signal }); c.abort(); }],
  ['window · removeEventListener 뒤',              (n, 형) => { const f = () => n.textContent; addEventListener(형, f); removeEventListener(형, f); }],
  ['window · capture:true 로 달고 옵션 없이 remove', (n, 형) => { const f = () => n.textContent; addEventListener(형, f, true); removeEventListener(형, f); }],
  ['window · 이미 abort 된 signal 로 등록',         (n, 형) => { addEventListener(형, () => n.textContent, { signal: AbortSignal.abort() }); }],
  ['window 리스너가 n 대신 id 문자열만 기억',        (n, 형) => { const id = n.id; addEventListener(형, () => document.getElementById(id)); }],
  ['리스너 함수를 전역 배열이 붙듦 · 노드 자신에 단 것', (n, 형) => { const f = () => n.textContent; n.addEventListener(형, f); 전역배열.push(f); }],
  ['리스너 없음 · 노드를 전역 배열이 붙듦',          (n, 형) => { 전역배열.push(n); }],
];

// 부모 상자를 떼어 내고, 부모에 콜백을 건다 — 리스너의 클로저는 자식 하나만 가리킨다
const 부모칸들 = [
  ['리스너 없음',                                  (자식, 형) => {}],
  ['window 리스너의 클로저가 자식 하나를 가리킴',   (자식, 형) => { addEventListener(형, () => 자식.textContent); }],
];

let 번호 = 0;
async function 한판(만들기, 부모를보나) {
  let 불림 = false;
  const 명부 = new FinalizationRegistry(() => { 불림 = true; });
  const 형 = '형' + (++번호);
  (() => {
    const 상자 = document.createElement('div');
    const n = document.createElement('p');
    n.id = 'n' + 번호; n.textContent = 'x';
    상자.appendChild(n);
    document.getElementById('자리').appendChild(상자);
    만들기(n, 형);
    명부.register(부모를보나 ? 상자 : n, '값');
    상자.remove();
  })();
  await 틱(); gc();
  let t = 0;
  for (; t < 기다림 && !불림; t++) { await 틱(); if (!불림) gc(); }
  return { 불림, t };
}

const 줄 = [], 틱줄 = [];
async function 돌리기(표, 부모를보나, 머리) {
  for (const [라벨, 만들기] of 표) {
    let n = 0; const ts = [];
    for (let i = 0; i < 판수; i++) { const r = await 한판(만들기, 부모를보나); if (r.불림) n++; ts.push(r.불림 ? r.t : '-'); }
    줄.push([머리, 라벨, n]);
    틱줄.push(padw(머리 + ' · ' + 라벨, 58) + ts.join(' '));
  }
}
window.__단계 = [['js', '(async () => { await 돌리기(칸들, false, "노드"); await 돌리기(부모칸들, true, "부모"); return 1; })()']];
window.__끝 = () => {
  const O = [];
  O.push('떼어 낸 노드에 FinalizationRegistry 를 걸고 gc() — 콜백이 불린 판 / ' + 판수 + '판');
  O.push(padw('무엇을 보나 · 칸', 62) + '불린 판');
  for (const [머리, 라벨, n] of 줄) O.push(padw(머리 + ' · ' + 라벨, 62) + n + '/' + 판수);
  O.push('');
  O.push('모든 판에서 불린 칸 = ' + 줄.filter(r => r[2] === 판수).length + ' / ' + 줄.length
       + ' · 한 판도 안 불린 칸 = ' + 줄.filter(r => r[2] === 0).length + ' / ' + 줄.length);
  O.push('');
  O.push('콜백이 불린 판에서 — gc() 뒤 몇 번째 틱이었나 (- = ' + 기다림 + '틱 안에 안 불림)');
  for (const s of 틱줄) O.push(s);
  return O.join('\n');
};
</script>
```

```text
$ python3 wa20b-cdp.py page --gc wa20b-20-gc.html | sed -n '1,18p'
떼어 낸 노드에 FinalizationRegistry 를 걸고 gc() — 콜백이 불린 판 / 10판
무엇을 보나 · 칸                                              불린 판
노드 · 리스너 없음                                            10/10
노드 · 노드 자신에 단 리스너 · 클로저가 n                     10/10
노드 · window 에 단 리스너 · 클로저가 n                       0/10
노드 · window · once · 한 번 던진 뒤                          10/10
노드 · window · once · 안 던짐                                0/10
노드 · window · signal · abort() 뒤                           10/10
노드 · window · removeEventListener 뒤                        10/10
노드 · window · capture:true 로 달고 옵션 없이 remove         0/10
노드 · window · 이미 abort 된 signal 로 등록                  10/10
노드 · window 리스너가 n 대신 id 문자열만 기억                10/10
노드 · 리스너 함수를 전역 배열이 붙듦 · 노드 자신에 단 것     0/10
노드 · 리스너 없음 · 노드를 전역 배열이 붙듦                  0/10
부모 · 리스너 없음                                            10/10
부모 · window 리스너의 클로저가 자식 하나를 가리킴            0/10

모든 판에서 불린 칸 = 8 / 14 · 한 판도 안 불린 칸 = 6 / 14
(exit 0)
```

- ★★★ **「노드 자신에 단 리스너」는 회수된다(10/10)** — 클로저가 `n` 을 가리키는데도 그렇다. `n` 과 리스너가 **서로만** 가리키는 고리이고, 바깥에서 그 고리로 오는 길이 없다.
- ★★★ **같은 클로저를 `window` 에 달면 안 회수된다(0/10).** `window` 는 페이지가 사는 한 살고, 그 리스너 목록이 클로저를, 클로저가 `n` 을 붙든다. **누수의 모양은 이것 하나다.**
- **`once` 는 「불린 뒤」에만 풀어 준다** — 한 번 던진 칸은 10/10, **안 던진 칸은 0/10.** 오지 않는 이벤트에 단 `once` 는 **영영 남는다.**
- **`signal` + `abort()` · `removeEventListener`** — 둘 다 10/10.
- ★★ **`capture: true` 로 달고 옵션 없이 지운 칸은 0/10** 이다. [15번 주제](../15-listener-registration/2-summary.md)가 「에러도 경고도 없이 안 지워진다」고 잰 그 칸이 **여기서 누수가 된다.**
- **이미 abort 된 signal 로 단 칸은 10/10** — 등록 자체가 안 됐으니 붙들 것이 없다(15편의 「호출 0회」와 같은 사실을 GC 창으로 다시 본 것).
- ★ **`window` 리스너가 `n` 대신 `id` 문자열만 기억한 칸은 10/10** — 쪽지에 **노드가 아니라 이름을** 적으면 그 노드를 살리지 않는다.
- **대조군 둘** — 리스너 함수를 **전역 배열이** 붙들면 노드 자신에 단 것이어도 0/10(클로저가 `n` 을 살린다), 노드를 전역 배열에 넣으면 리스너가 없어도 0/10.

```text
   ★ 회수 여부는 「리스너가 있나」가 아니라 「오래 사는 곳에서 n 까지 길이 있나」

   칸                                        오래 사는 곳 ──▶ … ──▶ n      회수
   리스너 없음                               (길 없음)                      10/10
   n 자신에 단 리스너                        (길 없음 — n ⇄ f 고리뿐)       10/10
   window 리스너 → 클로저 → n               window ▶ f ▶ n                  0/10
   window · once · 안 던짐                   window ▶ f ▶ n                  0/10
   window · capture 안 맞춰 remove          window ▶ f ▶ n (안 지워짐)      0/10
   window · once 던진 뒤 / signal / remove  (지워짐 → 길 끊김)              10/10
   window 리스너가 id 문자열만               window ▶ f ▶ "n7"(문자열)       10/10
   전역 배열 → f → n                         전역 ▶ f ▶ n                    0/10
   전역 배열 → n                             전역 ▶ n                        0/10
```

**「몇 번째 틱이었나」** — 같은 실행의 뒷부분이다. ★ **흔들려도 되는 칸으로 선언한 블록**이다.

```text
$ python3 wa20b-cdp.py page --gc wa20b-20-gc.html | sed -n '20,34p'
콜백이 불린 판에서 — gc() 뒤 몇 번째 틱이었나 (- = 20틱 안에 안 불림)
노드 · 리스너 없음                                        1 1 1 1 1 1 1 1 1 1
노드 · 노드 자신에 단 리스너 · 클로저가 n                 1 1 1 1 1 1 1 1 1 1
노드 · window 에 단 리스너 · 클로저가 n                   - - - - - - - - - -
노드 · window · once · 한 번 던진 뒤                      1 1 1 1 1 1 1 1 1 1
노드 · window · once · 안 던짐                            - - - - - - - - - -
노드 · window · signal · abort() 뒤                       1 1 1 1 1 1 1 1 1 1
노드 · window · removeEventListener 뒤                    1 1 1 1 1 1 1 1 1 1
노드 · window · capture:true 로 달고 옵션 없이 remove     - - - - - - - - - -
노드 · window · 이미 abort 된 signal 로 등록              1 1 1 1 1 1 1 1 1 1
노드 · window 리스너가 n 대신 id 문자열만 기억            1 1 1 1 1 1 1 1 1 1
노드 · 리스너 함수를 전역 배열이 붙듦 · 노드 자신에 단 것 - - - - - - - - - -
노드 · 리스너 없음 · 노드를 전역 배열이 붙듦              - - - - - - - - - -
부모 · 리스너 없음                                        1 1 1 1 1 1 1 1 1 1
부모 · window 리스너의 클로저가 자식 하나를 가리킴        - - - - - - - - - -
(exit 0)
```

- 이 판에서는 **회수된 칸이 전부 첫 틱**이었다. 그래도 **이 숫자에 기대지 마라** — 명세가 콜백 시점을 묶지 않는다([JS 23번 주제](../../languages/js/syntax/23-map-set-and-weak-collections/2-summary.md)의 (6)이 node 에서 그 흔들림을 따로 쟀다).

### (3) ★★ 자식 하나가 부모째 붙든다 — 리스너가 붙드는 「그래프」

**언제 쓰나** — 「클로저에는 작은 버튼 하나만 넣었는데?」일 때.

**던진 것** — (2)의 같은 실행 끝의 두 줄이다. **상자(부모)를 떼어 내고 부모에** 콜백을 걸었다. `window` 리스너의 클로저는 **자식 `<p>` 하나만** 가리킨다.

```text
$ python3 wa20b-cdp.py page --gc wa20b-20-gc.html | sed -n '1,2p;15,16p'
떼어 낸 노드에 FinalizationRegistry 를 걸고 gc() — 콜백이 불린 판 / 10판
무엇을 보나 · 칸                                              불린 판
부모 · 리스너 없음                                            10/10
부모 · window 리스너의 클로저가 자식 하나를 가리킴            0/10
(exit 0)
```

- **리스너가 없으면 부모는 10/10 회수.**
- ★★★ **클로저가 자식 하나만 가리켜도 부모가 0/10** 이다. 떼어 낸 자식은 여전히 `parentNode` 로 부모를 가리키고, 부모는 **자기 자식 전부**를 가리킨다.

```text
   리스너 하나가 붙드는 객체 그래프

   window ─▶ 리스너 f ─▶ (클로저) ─▶ 자식 p
                                      │ parentNode
                                      ▼
                                  떼어 낸 상자 div ─▶ 그 안의 나머지 자식 전부

   ★ 「노드 하나」가 아니라 「그 노드가 속한 떼어 낸 서브트리 전체」다
```

- ★ **크기는 재지 않았다** — 서브트리가 클수록 많이 붙든다는 것은 **그래프의 모양**에서 나오는 말이고, 바이트 수치는 이 편에 없다.

### (4) 떼는 세 방법이 각각 무엇을 풀어 주나

(2)의 칸들을 방법별로 다시 읽으면 이렇다. [15번 주제](../15-listener-registration/2-summary.md)의 (7)이 「떼는 세 가지 길」을 호출 횟수로 쟀고, 여기는 **그 결과가 메모리 쪽에서 어떻게 보이나**를 붙인다.

```text
   방법                           풀어 주나(회수)   조용히 실패하는 자리
   removeEventListener(t, f, c)   10/10             c(capture) 를 안 맞추면 0/10 — 에러 없음
   { once: true }                 던진 뒤 10/10     이벤트가 안 오면 0/10 — 영영 남는다
   { signal } + abort()           10/10             이미 abort 된 신호로 달면 등록 자체가 안 됨(10/10)
```

- ★ **`signal` 은 「참조도 `capture` 도 다시 안 적는다」** — 그래서 첫 번째 줄의 실패가 **원리상 없다**(15편의 결론).

```text
   누수를 가르는 물음 셋 — (2)의 칸을 따라가면

   ① 리스너를 단 곳이 떼어 낸 노드보다 오래 사나?  ── 아니오 ─▶ (노드 자신) 새지 않는다
        │ 예 (이 판에서는 window)
        ▼
   ② 클로저가 떼어 낸 노드(또는 그 자손)를 가리키나? ── 아니오 ─▶ (id 문자열만) 새지 않는다
        │ 예
        ▼
   ③ 그 리스너가 지금 목록에서 빠졌나?             ── 예 ─▶ (once 불림 · abort · 맞춘 remove) 새지 않는다
        │ 아니오 (once 안 불림 · capture 안 맞춤)
        ▼
      샌다 — 떼어 낸 서브트리 전체
```
- ★ **`once` 는 「해제 도구」가 아니라 「일회용」이다** — 해제는 **불렸을 때의 부산물**일 뿐이다.

### (5) ★★ `AbortSignal` 하나 · 리스너 다섯 · 그리고 이미 abort 된 신호

**언제 쓰나** — 컴포넌트가 여기저기 단 리스너를 한 번에 거두고 싶을 때.

```html
<!-- wa20b-20-signal.html -->
<!doctype html>
<meta charset="utf-8">
<title>20-signal</title>
<div id="겉"><button id="속">단추</button></div>
<script>
const O = [];
const $ = id => document.getElementById(id);
const 잡기 = fn => { try { return '예외 없음 · ' + fn(); } catch (e) { return e.name + ' 「' + e.message + '」'; } };

O.push('가. AbortSignal 하나 · 리스너 다섯 (대상 넷 · 형 둘)');
const 지휘 = new AbortController();
let 셈 = 0;
const 달기 = (t, 형) => t.addEventListener(형, () => 셈++, { signal: 지휘.signal });
달기($('겉'), '가'); 달기($('속'), '가'); 달기(document, '가'); 달기(window, '가'); 달기($('겉'), '나');
const 던지기 = () => { 셈 = 0; for (const t of [$('겉'), $('속'), document, window]) t.dispatchEvent(new Event('가')); $('겉').dispatchEvent(new Event('나')); return 셈; };
O.push('  abort 전 — 네 대상에 가 · 겉에 나 를 던지면 호출 = ' + 던지기());
지휘.abort();
O.push('  abort() 한 번 뒤 — 같은 것을 던지면 호출 = ' + 던지기());
O.push('');

O.push('나. 이미 abort 된 signal 로 등록하면');
let z = 0;
O.push('  addEventListener 의 결과 = ' + 잡기(() => String($('겉').addEventListener('다', () => z++, { signal: 지휘.signal }))));
$('겉').dispatchEvent(new Event('다'));
O.push('  던진 뒤 호출 = ' + z);
O.push('');

O.push('다. abort 이벤트 리스너 안에서 같은 형을 던지면');
const 둘 = new AbortController();
let w = 0, 안에서 = '-';
$('겉').addEventListener('라', () => w++, { signal: 둘.signal });
둘.signal.addEventListener('abort', () => { w = 0; $('겉').dispatchEvent(new Event('라')); 안에서 = w; });
둘.abort();
O.push('  abort 이벤트 리스너 안에서 던진 라 의 호출 = ' + 안에서);
O.push('');

O.push('라. abort 의 이유');
const 셋 = new AbortController();
셋.abort();
const 넷 = new AbortController();
넷.abort('그만');
O.push('  abort() 인자 없음 → reason = ' + 셋.signal.reason.name + ' 「' + 셋.signal.reason.message + '」');
O.push('  abort("그만")     → reason = ' + JSON.stringify(넷.signal.reason));
O.push('  AbortSignal.abort().aborted = ' + AbortSignal.abort().aborted);
O.push('');

O.push('마. AbortSignal.any — 둘 중 하나를 abort');
const 갑 = new AbortController(), 을 = new AbortController();
const 합 = AbortSignal.any([갑.signal, 을.signal]);
let a = 0;
$('겉').addEventListener('마', () => a++, { signal: 합 });
$('겉').dispatchEvent(new Event('마'));
O.push('  abort 전 호출 = ' + a);
갑.abort();
a = 0;
$('겉').dispatchEvent(new Event('마'));
O.push('  갑.abort() 뒤 호출 = ' + a + ' · 합.aborted = ' + 합.aborted + ' · 을.signal.aborted = ' + 을.signal.aborted);
O.push('  합.reason === 갑.signal.reason → ' + (합.reason === 갑.signal.reason));
O.push('');

O.push('바. AbortSignal.timeout(0) — abort 이벤트를 기다린 뒤');
window.__바 = () => {
  const 시한 = AbortSignal.timeout(0);
  let b = 0;
  $('겉').addEventListener('바', () => b++, { signal: 시한 });
  O.push('  등록 직후(같은 잡) aborted = ' + 시한.aborted);
  return new Promise(r => 시한.addEventListener('abort', () => {
    $('겉').dispatchEvent(new Event('바'));
    O.push('  abort 이벤트 뒤 aborted = ' + 시한.aborted + ' · reason = ' + 시한.reason.name + ' · 던진 바 의 호출 = ' + b);
    r(1);
  }, { once: true }));
};

window.__단계 = [['js', '__바()']];
window.__끝 = () => O.join('\n');
</script>
```

```text
$ python3 wa20b-cdp.py page wa20b-20-signal.html | sed -n '1,7p'
가. AbortSignal 하나 · 리스너 다섯 (대상 넷 · 형 둘)
  abort 전 — 네 대상에 가 · 겉에 나 를 던지면 호출 = 5
  abort() 한 번 뒤 — 같은 것을 던지면 호출 = 0

나. 이미 abort 된 signal 로 등록하면
  addEventListener 의 결과 = 예외 없음 · undefined
  던진 뒤 호출 = 0
(exit 0)
```

- **대상 넷 · 형 둘에 흩어진 다섯 리스너가 `abort()` 한 번에 전부 빠졌다**(5 → 0).
- ★ **이미 abort 된 signal 로 등록하면 — 예외도 반환값도 없다**(`undefined`). **던져도 0회**다. DOM 의 add an event listener 가 **「signal 이 abort 됐으면 그냥 돌아가라」** 로 정한다. [15번 주제](../15-listener-registration/2-summary.md)의 (7)이 같은 0회를 쟀다.
- ★★ **그래서 「abort 한 컨트롤러를 다음 마운트에 재사용」하면 조용히 아무것도 안 달린다.** 마운트마다 **새 컨트롤러**가 필요하다.

```text
   signal 하나가 묶는 것 — 대상 넷 · 형 둘 · 리스너 다섯

                          지휘 = new AbortController()
                                   │ 지휘.signal
        ┌──────────────┬───────────┼──────────────┬──────────────┐
        ▼              ▼           ▼              ▼              ▼
     #겉 '가'       #속 '가'    document '가'   window '가'     #겉 '나'
                                   │
                        지휘.abort() 한 번 ─▶ 다섯 줄이 각 명부에서 빠진다
```

```text
   마운트마다 새 컨트롤러 — 재사용하면 두 번째부터 조용히 안 달린다

   연결 ①  끈 = new AbortController()   window.addEventListener(…, { signal: 끈.signal })   ✔ 달림
   분리 ①  끈.abort()                                                                         ✔ 빠짐
   연결 ②  (같은 끈을 재사용)           window.addEventListener(…, { signal: 끈.signal })   ✕ 예외 없이 안 달림
   연결 ②' 끈 = new AbortController()   …                                                     ✔ 달림
```

### (6) `abort` 이벤트 안에서는 이미 떨어져 있다

```text
$ python3 wa20b-cdp.py page wa20b-20-signal.html | sed -n '9,10p'
다. abort 이벤트 리스너 안에서 같은 형을 던지면
  abort 이벤트 리스너 안에서 던진 라 의 호출 = 0
(exit 0)
```

- ★ **`abort` 이벤트 리스너 안에서 던지면 0회** 다. DOM 의 run the abort steps 가 **abort 알고리즘(리스너 지우기)을 먼저 전부 돌리고, 그다음에 `abort` 이벤트를 쏜다.**

```text
   signal abort 의 순서 (DOM — signal abort · run the abort steps)

   ① abort reason 을 정한다(인자 없으면 AbortError DOMException)
   ② abort 알고리즘을 전부 돈다   ← addEventListener 가 달아 둔 「리스너 지우기」가 여기
   ③ 알고리즘 목록을 비운다
   ④ abort 이벤트를 쏜다         ← 여기서 던지면 이미 없다
```

```text
$ python3 wa20b-cdp.py page wa20b-20-signal.html | sed -n '12,15p'
라. abort 의 이유
  abort() 인자 없음 → reason = AbortError 「signal is aborted without reason」
  abort("그만")     → reason = "그만"
  AbortSignal.abort().aborted = true
(exit 0)
```

- **인자 없이 `abort()` 하면 `reason` 은 `AbortError`**, 인자를 주면 **그 값 그대로**(문자열도 된다).
- `AbortSignal.abort()` 는 **처음부터 abort 된** 신호를 만든다 — (2)의 「이미 abort 된 signal 로 등록」 칸이 이것으로 만든 것이다.

### (7) `AbortSignal.any` · `AbortSignal.timeout` — 판별만

**언제 쓰나** — 「사용자가 닫거나 5초가 지나면 둘 다 떼라」일 때. **정본은 목록의 27번 주제**(네트워크 쪽 취소와 타임아웃)이고, 여기는 **리스너 해제에 쓸 수 있나**만 판별한다.

```text
$ python3 wa20b-cdp.py page wa20b-20-signal.html | sed -n '17,20p'
마. AbortSignal.any — 둘 중 하나를 abort
  abort 전 호출 = 1
  갑.abort() 뒤 호출 = 0 · 합.aborted = true · 을.signal.aborted = false
  합.reason === 갑.signal.reason → true
(exit 0)
```

- **`any([갑, 을])` 은 하나만 abort 돼도 abort 되고**, 거기 단 리스너가 빠진다(1 → 0). **을은 멀쩡하다** — 묶음은 한 방향이다.
- **`합.reason` 은 `갑.signal.reason` 과 같은 객체**다 — DOM 이 의존 신호에 **원본의 abort reason 을 그대로** 넣는다.

```text
$ python3 wa20b-cdp.py page wa20b-20-signal.html | sed -n '22,24p'
바. AbortSignal.timeout(0) — abort 이벤트를 기다린 뒤
  등록 직후(같은 잡) aborted = false
  abort 이벤트 뒤 aborted = true · reason = TimeoutError · 던진 바 의 호출 = 0
(exit 0)
```

- ★ **`timeout(0)` 도 같은 잡 안에서는 아직 abort 가 아니다**(`false`). DOM 이 「timeout 뒤 **타이머 태스크 소스에 태스크를 큐에 넣어** abort」로 정한다. `abort` 이벤트 뒤에는 `TimeoutError` 이고 리스너는 빠졌다.

```text
   any 와 timeout — 한 줄 정리

   AbortSignal.any([a, b])   a 나 b 가 abort 되면 따라서 abort · reason 은 원본 것
   AbortSignal.timeout(ms)   ms 뒤 「태스크로」 abort · reason = TimeoutError
                              같은 잡 안에서는 timeout(0) 도 아직 aborted=false

   ★ 둘 다 addEventListener 의 signal 자리에 그대로 들어간다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   떼는 꼴
     el.removeEventListener(type, f, { capture })   달 때의 type · f · capture 를 그대로
     el.addEventListener(type, f, { once: true })    한 번 불리면 스스로
     el.addEventListener(type, f, { signal })        signal 이 abort 되면 스스로

   신호 만들기
     const c = new AbortController();  c.signal  c.abort(reason?)
     AbortSignal.abort(reason?)        처음부터 abort 된 신호
     AbortSignal.any([s1, s2])         하나라도 abort 되면
     AbortSignal.timeout(ms)           ms 뒤 태스크로

   관용구 — 마운트마다 새 컨트롤러
     연결될 때   this.끈 = new AbortController(); window.addEventListener('resize', f, { signal: this.끈.signal });
     떨어질 때   this.끈.abort();
```

### 어디서 헷갈리나

- **`once` 는 해제 보장이 아니다** — 안 불리면 안 풀린다((2)).
- **abort 한 컨트롤러는 다시 쓸 수 없다** — 조용히 아무것도 안 달린다((5)).
- **`abort` 이벤트 안에서는 이미 떨어져 있다**((6)).

## 어디서 틀리나

### 1. 컴포넌트를 지웠으니 메모리도 풀렸다고 믿는다

**`window`·`document` 에 단 리스너가 그 컴포넌트의 노드를 클로저로 가리키면 안 풀린다**((2)의 0/10). 떼는 짝을 맞추거나 `signal` 로 묶는다.

### 2. 클로저에 버튼 하나만 넣었으니 그것만 남는다고 믿는다

**떼어 낸 서브트리 전체가 남는다**((3)). 자식은 `parentNode` 로 부모를 가리킨다.

### 3. `capture: true` 로 단 것을 옵션 없이 지운다

**안 지워지고, 그래서 샌다**((2)의 0/10). 에러도 경고도 없다 — [15번 주제](../15-listener-registration/2-summary.md)의 동일성 격자.

### 4. `once` 면 알아서 치워진다고 믿는다

**불려야 치워진다**((2)). 오지 않는 이벤트(`transitionend` 가 안 오는 경우 등)에 단 `once` 는 남는다.

### 5. abort 한 컨트롤러를 다음에도 쓴다

**등록 자체가 안 된다 — 예외도 없다**((5)). 리스너가 **안 붙은 것을 못 알아챈다.**

### 6. `abort` 이벤트에서 「마지막으로 한 번」 리스너를 부르려 한다

**이미 떼어진 뒤다**((6)).

### 7. 「누수가 메모리를 N MB 먹는다」고 적는다

**이 편은 재지 않았다.** 회수됐나(참/거짓)만 쟀다. 크기는 힙 스냅샷으로 **그 페이지에서** 재야 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 이미 abort 된 signal 로는 **등록이 안 되고 예외도 없는** 것 | **명세**(DOM — add an event listener) · 이 판도 그랬다((5)) |
| `abort()` 가 리스너를 **먼저 지우고 그다음 `abort` 이벤트**를 쏘는 것 | **명세**(DOM — signal abort · run the abort steps) · 이 판도 그랬다((6)) |
| `any` 의 reason 이 **원본의 것**인 것 · `timeout` 이 **태스크로** abort 하고 `TimeoutError` 인 것 | **명세**(DOM — create a dependent abort signal · `timeout()`) |
| **강하게 붙잡힌 노드는 회수되지 않는** 것(`0/10` 칸) | **명세**(ECMA-262 의 도달 가능성 — [JS 23번 주제](../../languages/js/syntax/23-map-set-and-weak-collections/2-summary.md)) |
| **안 붙잡힌 노드가 `gc()` 한 번에 회수되는** 것(`10/10` 칸) | ★ **이 판의 관찰.** 명세는 회수를 **보장하지 않는다** |
| 콜백이 **첫 틱**에 불린 것 | ★ **이 판의 관찰 — 흔들려도 되는 칸** |
| `window` 리스너 목록이 클로저를 **강하게** 붙드는 것 | ★ 명세의 「event listener list」가 콜백을 **가진다**는 모형에서 따라 나오고, **이 판에서 0/10 으로 관찰**했다. 이 문서는 Blink 의 추적 방식을 확인하지 않았다 |
| **`gc()` 가 페이지에 있는** 것 | ★ **구현.** `--js-flags=--expose-gc` 로 연 V8 의 디버깅 표면이다. 평소 페이지에는 없다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 컴포넌트가 `window`·`document` 에 리스너를 단다 | **마운트마다 새 `AbortController`** + 떨어질 때 `abort()` | 떨어질 때 `removeEventListener` 를 손으로 맞추기 |
| 한 번만 받는다 | `{ once: true }` | 「치워 주겠지」 — 안 오면 남는다 |
| 사용자 동작 **또는** 시간 초과로 끝낸다 | `AbortSignal.any([c.signal, AbortSignal.timeout(ms)])` | 타이머와 컨트롤러를 따로 관리 |
| 리스너가 노드를 알아야 한다 | 그 노드 **자신**에 달기 · 또는 위임([18번 주제](../18-event-delegation/2-summary.md)) | 오래 사는 곳에 달고 클로저로 노드를 쥐기 |
| 「샜나」를 확인한다 | 떼어 낸 노드에 `FinalizationRegistry` + `--expose-gc` 의 `gc()` (이 편의 창) · 힙 스냅샷 | 콘솔 경고를 기다리기(안 난다) |

## 핵심 문장

1. **누수는 「오래 사는 곳의 리스너 → 클로저 → 떼어 낸 노드」라는 길 하나의 모양**이다 — 노드 자신에 단 리스너는 고리일 뿐이라 회수됐다.
2. **리스너 하나가 붙드는 것은 노드 하나가 아니라 그 노드가 속한 떼어 낸 서브트리**다.
3. **`capture` 를 안 맞춘 `remove`·안 불린 `once` 는 조용히 샌다** — 에러가 없다.
4. **`signal` 하나로 여러 대상·여러 형의 리스너를 한 번에 뗀다.** 이미 abort 된 신호로는 **등록이 안 되고 예외도 없다.**
5. **`abort()` 는 리스너를 먼저 지우고 `abort` 이벤트를 나중에 쏜다.**
6. **이 편은 회수 여부만 쟀다** — 바이트는 재지 않았고, `10/10` 은 이 판의 관찰이다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 20번)
- [15번 주제](../15-listener-registration/2-summary.md) — **동일성 키 · `once` · `signal` 의 호출 횟수 정본.** 여기는 그것이 **메모리 쪽에서 어떻게 보이나**
- [13번 주제](../13-custom-element-lifecycle/2-summary.md) — 연결·분리 콜백. 「연결될 때 달고 떨어질 때 떼는」 짝이 이 편의 관용구가 서는 자리
- [18번 주제](../18-event-delegation/2-summary.md) — 위임. 리스너를 **오래 사는 곳 하나에** 두면서 노드를 쥐지 않는 형태
- [JS 갈래 23번 주제](../../languages/js/syntax/23-map-set-and-weak-collections/2-summary.md) — **`WeakRef`·`FinalizationRegistry`·회수 보장의 정본.** 그쪽은 node 의 `gc()`, 여기는 **브라우저 페이지의 `gc()`**
- JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **41번** — `AbortController`/`AbortSignal` 의 언어 쪽 정본(아직 폴더 없음)
- 목록의 **27번 주제** — `AbortSignal.timeout()`/`any()` 의 네트워크 쪽 정본
- [`../../memory-management/README.md`](../../memory-management/README.md) — 힙·가비지 컬렉션의 원리 노트. 그쪽은 **힙이 무엇인가**, 여기는 **리스너가 무엇을 붙드나**

## 용어 풀이

- **클로저** — 함수가 만들어질 때 보이던 변수를 기억하는 것. 리스너 안에서 `n` 을 쓰면 그 리스너가 `n` 을 붙든다.
- **도달 가능성** — 오래 사는 뿌리(전역·`window` 등)에서 참조를 따라가 닿을 수 있나. 닿으면 회수되지 않는다.
- **떼어 낸 서브트리** — 문서에서 뗐지만 참조가 남아 있는 노드 묶음. 자식에서 부모로 `parentNode` 가 이어진다.
- **`FinalizationRegistry`** — 등록한 객체가 회수된 뒤 콜백을 불러 주는 표준 객체. 이 편의 GC 창.
- **`gc()`** — `--expose-gc` 로 연 V8 의 디버깅 함수. 평소 페이지에는 없다.
- **abort 알고리즘** — 신호에 달린 「abort 되면 할 일」 목록. `addEventListener` 가 여기에 「리스너 지우기」를 단다.
- **의존 신호** — `AbortSignal.any` 가 만드는 신호. 원본 신호가 abort 되면 따라간다.
- **GC 창(창 ⑥)** — 「회수됐나」를 참/거짓으로 묻는 관측. 이 편의 본체.

## 더 들어가면

- **힙 스냅샷으로 보존 경로를 보는 법**(CDP `HeapProfiler`)은 쓰지 않았다 — 이 편은 칸을 바꿔 가며 경로를 **간접으로** 갈랐다.
- **`handleEvent` 객체를 리스너로 단 경우**도 같은 그래프 규칙일 것이지만 **던지지 않았다.**
- **`onclick` 같은 속성 핸들러**는 다른 표면이라 이 격자에 넣지 않았다.
- **iframe·다른 문서로 옮긴 노드**의 수명은 이 편 밖이다.
