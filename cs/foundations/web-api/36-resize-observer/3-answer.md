# web-api/36 — `ResizeObserver`: 관측 상자 세 종류와 무한 루프 경고 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 페이지는 같은 기계의 로컬 서버(A)에서 열었고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> ★ 명세는 **W3C Resize Observer 2020-02-11 WD 사본**과 **HTML(update the rendering · report an exception)** 을 받아 읽었다. 편집자 초안은 받지 않았다. **비용은 재지 않았다.**\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 상자 격자 21칸 · `resize` 수 · 배율 2 대조 · 첫 통지 · 루프 세 판 · 오류 문구 · 콘솔 두 창 | ★ **판에 매일 수 있는 칸** — `device-pixel-content-box` 값(브라우저의 실제 배율) |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 비용 · 살아 있는 문서의 실제 배율 변화 · SVG |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. (가) `border-box` 만 — 150×100 · (나) 아무도 안 불린다

**출력**

```text
$ python3 wa36b-net.py page wa36b-36-grid.html | sed -n '1,4p;8p'
box	width 100→120	padding 10→20	border 5→8	transform scale(2)	부모 폭 200→160	뷰포트 폭 1000→800	devicePixelRatio 1→2
content-box	○ 120×50	—	—	—	○ 80×50	○ 80×50	—
border-box	○ 150×80	○ 150×100	○ 136×86	—	○ 110×80	○ 110×80	—
device-pixel-content-box	○ 120×50	—	—	—	○ 80×50	○ 80×50	—
(exit 0)
```

**왜 그런가**

- **(가) `padding 10→20` — `border-box` 만 `○ 150×100`.** `box-sizing: content-box` 라 **내용 상자(100×50)는 그대로**다. 크기 변화는 **고른 상자에서만** 판정된다. `border 5→8` 도 같은 모양이다(`136×86`).
- **(나) `transform scale(2)` — 세 상자 다 `—`.** 화면에서는 두 배지만 **레이아웃 크기가 안 바뀌었다.** 09편 (9)의 `offsetWidth` 쪽(레이아웃)을 본다.

### 2. (가) RO 만 · (나) `resize` 와 RO 둘 다

**출력**

```text
$ python3 wa36b-net.py page wa36b-36-grid.html
box	width 100→120	padding 10→20	border 5→8	transform scale(2)	부모 폭 200→160	뷰포트 폭 1000→800	devicePixelRatio 1→2
content-box	○ 120×50	—	—	—	○ 80×50	○ 80×50	—
border-box	○ 150×80	○ 150×100	○ 136×86	—	○ 110×80	○ 110×80	—
device-pixel-content-box	○ 120×50	—	—	—	○ 80×50	○ 80×50	—
window resize 이벤트 수	0	0	0	0	0	1	0
변화 뒤 devicePixelRatio	1	1	1	1	1	1	2
콜백이 불린 칸 = 11 / 21
(exit 0)
```

**왜 그런가**

- **(가) `부모 폭 200→160` — 세 상자 다 `○ 80×50`(내용) 인데 `window resize 이벤트 수` 는 0.** 요소 크기가 바뀐 원인이 뷰포트가 아니다.
- **(나) `뷰포트 폭 1000→800` — `resize` 1 · RO 도 `○ 80×50`**(요소가 `10vw`). `resize` 는 **뷰포트의 일**이고, 요소 크기 변화를 알고 싶으면 RO 다.
- 격자 전체는 **콜백이 불린 칸 11 / 21**.

### 3. 넷 다 온다 — RO 는 셋이 `0×0` 으로

**출력**

```text
$ python3 wa36b-net.py page wa36b-36-first.html
관찰 대상	ResizeObserver 첫 통지	IntersectionObserver 첫 통지
보이는 100×50	○ 100×50	○ isIntersecting=true
width 0 · height 0	○ 0×0	○ isIntersecting=true
display: none	○ 0×0	○ isIntersecting=false
문서에 안 붙인 요소	○ 0×0	○ isIntersecting=false
(exit 0)
```

**왜 그런가**

- **RO 첫 통지는 네 대상 전부** — 보이는 것은 `100×50`, 나머지 셋(폭·높이 0 · `display: none` · 문서 밖)은 **`0×0`** 으로 왔다.
- **IO 도 넷 다** 왔다 — `width 0 · height 0` 은 `true`(자리가 뷰포트 안), `display: none` 과 문서 밖은 `false`.
- 그래서 첫 통지를 「크기가 바뀌었다」 · 「보이게 됐다」로 읽지 않는다. 명세 사본과의 관계는 A9.

### 4. 틀마다 `[콜백, 오류]` — 다섯 번, 여섯째 틀은 `[콜백]`

**출력**

```text
$ python3 wa36b-net.py console wa36b-36-loop.html
가 자기를 키움	[콜백,오류] [콜백,오류] [콜백,오류] [콜백,오류] [콜백,오류] [콜백]
나 자식을 키움	[콜백(A),콜백(B),콜백(C)]
다 부모를 키움	[콜백(C),오류] [콜백(P)]
오류 이벤트 수 = 6
첫 오류 — ErrorEvent · message 「ResizeObserver loop completed with undelivered notifications.」 · error = null · filename 이 이 문서 주소인가 = true · lineno = 0
대조용 예외까지 오류 이벤트 수 = 7
--- 콘솔 ---
Runtime.exceptionThrown · Uncaught · Error: 대조용 예외
    at http://127.0.0.1:<A>/wa36b-36-loop.html:44:28
(exit 0)
```

**왜 그런가**

- **가 줄 — `[콜백,오류]` × 5 뒤 `[콜백]`.** 콜백이 자기를 키우면 **같은 틀 안에서는 다시 안 알린다** — 자기는 자기보다 깊지 않기 때문이다. 못 알린 몫이 남으니 **오류 한 번**, 그리고 다음 틀에 다시 온다. 다섯 번 키운 뒤에는 바뀐 것이 없어 오류가 없다.

### 5. (가) 한 틀에 셋 다 · (나) 오류 한 번 뒤 다음 틀에 부모

**출력**

```text
$ python3 wa36b-net.py console wa36b-36-loop.html | sed -n '2,3p'
나 자식을 키움	[콜백(A),콜백(B),콜백(C)]
다 부모를 키움	[콜백(C),오류] [콜백(P)]
(exit 0)
```

**왜 그런가**

- **(가)** A → B → C 로 **매번 더 깊은 요소**가 바뀌었으니 같은 틀에서 다시 알렸다. 오류 없음.
- **(나)** C 를 받은 콜백이 **더 얕은** P 를 바꿨다 — 그 틀에서는 못 알리고 **오류 한 번**, 다음 틀에 `콜백(P)`.

### 6. `ErrorEvent` · 「`ResizeObserver loop completed with undelivered notifications.`」 · 콘솔에는 없었다

**출력**

```text
$ python3 wa36b-net.py console wa36b-36-loop.html | sed -n '5,$p'
첫 오류 — ErrorEvent · message 「ResizeObserver loop completed with undelivered notifications.」 · error = null · filename 이 이 문서 주소인가 = true · lineno = 0
대조용 예외까지 오류 이벤트 수 = 7
--- 콘솔 ---
Runtime.exceptionThrown · Uncaught · Error: 대조용 예외
    at http://127.0.0.1:<A>/wa36b-36-loop.html:44:28
(exit 0)
```

**왜 그런가**

- **`ErrorEvent` · `message` 전문 `ResizeObserver loop completed with undelivered notifications.` · `error = null` · `lineno = 0`.** 문구는 받은 사본 §3.4.6 과 **한 글자도 같다.** 던진 값이 없으니 `error` 는 비어 있다.
- ★★ **콘솔 — 물은 곳 둘(`Log.entryAdded` · `Runtime.exceptionThrown`)에 루프 오류는 0줄.** 같은 판에서 **대조로 던진 보통 예외는 `Runtime.exceptionThrown · Uncaught · Error: 대조용 예외`** 로 받았다 — 창이 열려 있었다는 증거다. HTML 은 콘솔 보고를 **「may」** 로 둔다 — **재량 안의 선택**이다.

### 7. 틀이 반드시 끝나게 · 끊긴 것은 다음 틀로

- 콜백이 자기나 조상을 바꿀 때마다 같은 틀에서 다시 돌면 **틀이 안 끝날 수 있다.** 「이번에 알린 것 중 가장 얕은 깊이보다 **깊은** 것만」이면 트리 깊이가 유한하니 **반드시 끝난다.**
- **버리지 않는다** — 남은 통지는 **오류 이벤트 한 번**과 함께 **다음 틀**에서 알린다(A4 의 여섯째 틀 · A5 의 `콜백(P)`).

### 8. 안 된다 — 에뮬레이션이 장치 픽셀 격자를 안 바꿨다

**출력**

```text
$ WA36B_DSF=2 python3 wa36b-net.py page wa36b-36-grid.html | sed -n '1p;4p;6p;8p'
box	width 100→120	padding 10→20	border 5→8	transform scale(2)	부모 폭 200→160	뷰포트 폭 1000→800	devicePixelRatio 1→2
device-pixel-content-box	○ 240×100	—	—	—	○ 160×100	○ 160×100	—
변화 뒤 devicePixelRatio	2	2	2	2	2	1	2
(exit 0)
```

**왜 그런가**

- **배율 2 로 띄운 브라우저에서는 장치 픽셀 상자가 `240×100`**(두 배)이다 — RO 는 **실제 배율**을 본다.
- **그런데 `devicePixelRatio 1→2`(CDP) 열은 두 판 다 `—`** 이고, 에뮬레이션 뒤 `devicePixelRatio` 는 **2 로 읽혔다**((1)의 `변화 뒤 devicePixelRatio` 줄). **값은 바뀌었는데 기준(장치 픽셀 격자)은 안 바뀐 것** — 제5의 상태다.
- 그래서 적을 수 있는 것은 「**CDP 로 에뮬레이션한 배율 변화는 장치 픽셀 상자를 안 움직였다**」까지다. 살아 있는 문서의 실제 배율 변화는 못 쟀다.

### 9. 첫 통지가 없어야 한다 — 판정은 하지 않는다

- 사본 §3.1 은 `lastReportedSizes` 를 **`[(0,0)]`** 으로 시작하고, `isActive()` 는 「지금 크기가 **그것과 다르면**」 참이다. 그대로면 **0×0 대상은 첫 통지가 없어야 한다.** Chrome 151 은 보냈다(A3).
- **판정하지 않는다** — 받은 사본은 **2020 년 첫 공개 초안**이고, 지금의 편집자 초안은 받지 않았다. 말할 수 있는 것은 「**이 사본의 알고리즘과 다르다**」까지다.

### 10. 잰 것은 「불렸나 · 몇 번」 — 비용은 안 쟀다

- **잰 것** — 변화마다 **콜백이 불렸나**(11 / 21) · **`resize` 가 몇 번**(뷰포트 변화 한 칸만 1) · 틀마다 콜백 · 오류 수.
- **안 잰 것** — 시간 · 메인 스레드 점유. 부모 변화는 **`resize` 로는 아예 안 잡히므로** 「싸다 / 비싸다」 이전에 **잡히나 / 안 잡히나**가 먼저 갈린다.

### 11. 같은 점 — 관찰 시작 한 번 · 다른 점 — 겹침 대 크기 · RO 는 레이아웃 쪽

- **같은 점** — `observe()` 만 해도 한 번 온다(A3 — IO 도 넷 다 왔다 · 35편 A1).
- **다른 점** — IO 는 **root 와의 겹침 비율이 줄을 넘을 때**, RO 는 **고른 상자의 크기가 바뀔 때**다. `transform` 으로 두 배가 되면 IO 의 비율은 바뀔 수 있지만 **RO 는 조용하다**(A1).
- **09편 (9)** — `offsetWidth`(레이아웃 크기)는 `scale(2)` 에도 230 그대로였다. **RO 는 그 레이아웃 쪽을 본다** — 그래서 `transform` 열이 전부 `—` 다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless(`--window-size=1000,800`) · Python 3 표준 라이브러리 `http.server`(서버 A). **엔진은 Chrome 하나다.**

★ **하네스** — 24편의 `wa24b-net.py`(전문은 [24번 주제](../24-document-lifecycle-events/2-summary.md)) 를 모듈로 불러 서버 · Chrome · CDP 를 그대로 쓰고, **페이지가 CDP 일을 부탁하는 창구**(`Runtime.addBinding`)를 더했다. 36\~39 네 편이 이 파일 하나를 쓴다.

```python
# wa36b-net.py
#!/usr/bin/env python3
"""web-api 36~39 — 24편 하네스(wa24b-net.py)의 서버·Chrome·CDP 부분을 그대로 빌려 쓰고,
「페이지가 하네스에게 CDP 일을 부탁하는 창구」 하나만 더한다.

사용:
  wa36b-net.py page <html>       A 에서 그 페이지를 열고 window.__끝() 이 돌려준 글을 찍는다
  wa36b-net.py console <html>    page 와 같고, 뒤에 콘솔 줄(Log 도메인 · 잡히지 않은 예외)을 찍는다

★ 부탁 창구 — 페이지는 window.__부탁(할일, 인자) 를 부른다(Runtime.addBinding). 하네스가 그 일을 CDP 로 하고
  결과를 window.__답(번호, 결과) 로 돌려준다. 할일:
    dpr {값}            Emulation.setDeviceMetricsOverride — 창 크기는 그대로 두고 devicePixelRatio 만
    폭 {w, h}           Emulation.setDeviceMetricsOverride — 뷰포트 크기(배율 1)
    원래대로            Emulation.clearDeviceMetricsOverride
    지표                Performance.getMetrics 의 LayoutCount · RecalcStyleCount
    누르기 {x, y}       Input.dispatchMouseEvent(누름 · 뗌) — 응답을 기다리지 않는다(페이지가 바쁜 동안 보낸다)
    숨기기 · 보이기     새 탭을 앞으로 띄운다 · 첫 탭을 앞으로 되돌리고 새 탭을 닫는다(24편 방식)
    추적시작 · 추적끝   Tracing(devtools.timeline) — 끝에서 렌더러 주 스레드의 이벤트 이름을 시각 순으로 돌려준다
★ 시각은 찍지 않는다 — 페이지가 「범주 · 참/거짓 · 순서」로 바꿔서 돌려준다(한 판 값은 근거가 아니다).
★ 환경변수 WA36B_DSF=2 — 브라우저를 --force-device-scale-factor=2 로 띄운다(36편의 대조 판).
★ --virtual-time-budget 을 쓰지 않는다 — 프레임과 타이머는 실제 시간으로 돈다(wa24b-net.py 의 --headless).
"""
import importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("wa24b_net", os.path.join(HERE, "wa24b-net.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
base.PROF = os.path.join(HERE, f".prof-wa36b-{os.getpid()}")
base.FLAGS = [f"--user-data-dir={base.PROF}" if f.startswith("--user-data-dir=") else f for f in base.FLAGS]
if os.environ.get("WA36B_DSF"):           # 36편 대조 — 브라우저를 처음부터 그 배율로 띄운다(에뮬레이션이 아니라)
    base.FLAGS.insert(0, "--force-device-scale-factor=" + os.environ["WA36B_DSF"])

HELPER = """
(() => {
  const 대기 = new Map(); let 번호 = 0;
  window.__부탁 = (할일, 인자 = {}) => new Promise(r => { 번호++; 대기.set(번호, r);
    __cdp(JSON.stringify({ 번호, 할일, 인자 })); });
  window.__답 = (n, 값) => { const r = 대기.get(n); 대기.delete(n); if (r) r(값); };
})();
"""
WATCH = ["FireAnimationFrame", "EventDispatch", "UpdateLayoutTree", "Layout", "ResizeObserver",
         "IntersectionObserverController::computeIntersections", "Paint", "PrePaint", "TimeStamp",
         "FunctionCall", "ParseHTML", "HitTest", "ScrollLayer", "Commit"]


class Page:
    def __init__(self, c, tid, sid):
        self.c, self.tid, self.sid, self.other, self.trace = c, tid, sid, None, None

    def do(self, 할일, 인자):
        c, sid = self.c, self.sid
        if 할일 == "dpr":
            c.send("Emulation.setDeviceMetricsOverride", {"width": 0, "height": 0,
                   "deviceScaleFactor": 인자["값"], "mobile": False}, sid)
        elif 할일 == "폭":
            c.send("Emulation.setDeviceMetricsOverride", {"width": 인자["w"], "height": 인자["h"],
                   "deviceScaleFactor": 1, "mobile": False}, sid)
        elif 할일 == "원래대로":
            c.send("Emulation.clearDeviceMetricsOverride", {}, sid)
        elif 할일 == "지표":
            m = {x["name"]: x["value"] for x in c.send("Performance.getMetrics", {}, sid)["metrics"]}
            return {"LayoutCount": m["LayoutCount"], "RecalcStyleCount": m["RecalcStyleCount"]}
        elif 할일 == "누르기":           # 응답을 기다리지 않는다 — 기다리면 페이지가 한가해질 때까지 막힌다
            for t in ("mousePressed", "mouseReleased"):
                c.n += 1
                c.ws.send(json.dumps({"id": c.n, "sessionId": sid, "method": "Input.dispatchMouseEvent",
                                      "params": {"type": t, "x": 인자["x"], "y": 인자["y"], "button": "left",
                                                 "clickCount": 1, "buttons": 1 if t == "mousePressed" else 0}}))
            return None
        elif 할일 == "숨기기":
            self.other = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        elif 할일 == "보이기":
            c.send("Target.activateTarget", {"targetId": self.tid})
            c.send("Target.closeTarget", {"targetId": self.other})
            self.other = None
        elif 할일 == "추적시작":
            c.send("Tracing.start", {"traceConfig": {"includedCategories": ["devtools.timeline"]},
                                     "transferMode": "ReportEvents"})
        elif 할일 == "추적끝":
            c.send("Tracing.end")
            c.wait("Tracing.tracingComplete")
            ev = [e for d in c.take("Tracing.dataCollected") for e in d["value"]]
            return names_between(ev, 인자.get("표", "wa36b"))
        else:
            raise RuntimeError("모르는 할일: " + 할일)
        return True


def names_between(ev, mark):
    """표지(console.timeStamp) 두 개 사이, 표지를 낸 스레드의 완결 이벤트 이름을 시작 시각 순으로."""
    marks = [e for e in ev if e.get("name") == "TimeStamp" and e.get("args", {}).get("data", {}).get("message") == mark]
    if len(marks) < 2:
        return ["(표지 %d개)" % len(marks)]
    pid, tid = marks[0]["pid"], marks[0]["tid"]
    t0, t1 = marks[0]["ts"], marks[-1]["ts"]
    got = sorted((e for e in ev if e.get("pid") == pid and e.get("tid") == tid and t0 < e.get("ts", 0) < t1
                  and e.get("name") in WATCH and e.get("ph") in ("X", "B", "I", "i")), key=lambda e: e["ts"])
    out = []
    for e in got:
        n = e["name"]
        if n == "EventDispatch":
            n += "(" + e.get("args", {}).get("data", {}).get("type", "?") + ")"
        if n == "FunctionCall":
            continue
        if n == "TimeStamp":            # 페이지가 console.timeStamp 로 남긴 자국은 「⟨글⟩」로
            n = "⟨" + e.get("args", {}).get("data", {}).get("message", "?") + "⟩"
        out.append(n)
    return out


def run(c, page, expr):
    """페이지의 식을 돌리며, 그동안 온 부탁(Runtime.bindingCalled)을 처리한다."""
    c.n += 1
    me = c.n
    c.ws.send(json.dumps({"id": me, "sessionId": page.sid, "method": "Runtime.evaluate",
                          "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
    while True:
        for k, e in enumerate(c.events):
            if e.get("id") == me:
                r = c.events.pop(k)
                if "error" in r:
                    raise RuntimeError(json.dumps(r["error"], ensure_ascii=False))
                r = r["result"]
                if "exceptionDetails" in r:
                    d = r["exceptionDetails"]
                    return "«예외 " + (d.get("exception", {}).get("description") or d.get("text", "?")) + "»"
                return r.get("result", {}).get("value")
        asks = [k for k, e in enumerate(c.events) if e.get("method") == "Runtime.bindingCalled"]
        if asks:
            p = json.loads(c.events.pop(asks[0])["params"]["payload"])
            val = page.do(p["할일"], p["인자"])
            if p["할일"] != "누르기":
                c.n += 1       # 답도 기다리지 않는다 — 페이지가 바쁘면 그때까지 막히므로 다음 사건을 계속 받는다
                c.ws.send(json.dumps({"id": c.n, "sessionId": page.sid, "method": "Runtime.evaluate",
                                      "params": {"expression": "window.__답(%d, %s)" % (p["번호"], json.dumps(val, ensure_ascii=False))}}))
            continue
        c.events.append(json.loads(c.ws.recv()))


def main():
    mode, html = sys.argv[1], sys.argv[2]
    a = base.server("A")
    url = f"http://127.0.0.1:{base.PORTS['A']}/" + html
    proc, c = base.start()
    try:
        tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
        for m in ("Page.enable", "Runtime.enable", "Log.enable", "Performance.enable"):
            c.send(m, sid=sid)
        c.send("Runtime.addBinding", {"name": "__cdp"}, sid)
        c.send("Page.addScriptToEvaluateOnNewDocument", {"source": HELPER}, sid)
        base.goto(c, sid, url)
        page = Page(c, tid, sid)
        print(run(c, page, "window.__끝()"))
        if mode == "console":
            print("--- 콘솔 ---")
            hide = lambda s: s.replace(f"127.0.0.1:{base.PORTS['A']}", "127.0.0.1:<A>")
            for e in c.take("Log.entryAdded", sid):
                print("Log ·", e["entry"]["source"], "·", e["entry"]["level"], "·", hide(e["entry"]["text"]))
            for e in c.take("Runtime.exceptionThrown", sid):
                d = e["exceptionDetails"]
                print("Runtime.exceptionThrown ·", d.get("text"), "·",
                      hide(str(d.get("exception", {}).get("description") or d.get("exception", {}).get("value"))))
    finally:
        base.stop(proc)
        a.shutdown()


if __name__ == "__main__":
    main()
```

```sh
# wa36b-36-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa36b-net.py page wa36b-36-grid.html
WA36B_DSF=2 python3 wa36b-net.py page wa36b-36-grid.html
python3 wa36b-net.py page wa36b-36-first.html
python3 wa36b-net.py console wa36b-36-loop.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 상자 격자 21칸(배율 1) | 캡처 3판 | 동작 방식 (1) · A1 · A2 · A10 |
| 같은 격자(배율 2 로 띄움) | 캡처 3판 | 동작 방식 (2) · A8 |
| 첫 통지 넷 × 관찰자 둘 | 캡처 3판 | 동작 방식 (3) · A3 · A9 |
| 루프 세 판 + 콘솔 두 창 + 대조 예외 | 캡처 3판 | 동작 방식 (4) · A4 \~ A7 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 0×0 대상의 첫 통지 | 온다 | 받은 2020 사본과 다르다 — 편집자 초안 대조가 남았다 |
| 루프 오류의 콘솔 보고 | 없음 | 명세가 「may」로 둔 자리 |
| CDP 배율 에뮬레이션과 장치 픽셀 상자 | 안 움직임 | 도구(CDP)의 성질 — 판이 오르면 달라질 수 있다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② 비용(시간). ③ SVG · 조각난 상자. ④ 편집자 초안 대조.
