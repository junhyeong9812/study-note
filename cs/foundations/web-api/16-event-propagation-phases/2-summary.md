# web-api/16 — 전파 3단계: 캡처·타깃·버블과 `target` 대 `currentTarget` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★ **이 편의 본체는 창 ④ 를 늘린 「호출 순서 로그」다** — 리스너가 **몇 번** 불렸나(15편)가 아니라 **어느 순서로, 어느 단계에서, 누구 앞에서** 불렸나를 한 줄씩 적는다.\
> **기준 소스** — [WHATWG DOM Standard — Events](https://dom.spec.whatwg.org/#events) 의 「dispatch」·「invoke」·「inner invoke」 절과 [HTML Standard — The `Document` object](https://html.spec.whatwg.org/multipage/dom.html#the-document-object) 의 「`Document` 의 get the parent」 문장. 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. **클릭·포커스·마우스 이동은 CDP 로 넣은 진짜 입력**이고(아래 하네스), 같은 순서표를 **합성 이벤트로도 던져 견줬다.** 블록마다 명령이 배너로 실려 있고 사람이 옮겨 적지 않았다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. 이 편이 다루는 디스패치 절차는 DOM 표준의 현재 본문으로 읽는다. ★ **「타깃에서는 등록 순서대로 부른다」는 옛 설명이 있다** — 지금 본문과 이 판은 그렇지 않다((3)). **언제 바뀌었는지는 확인하지 않았다.**\
> **선행** — [15번 주제](../15-listener-registration/2-summary.md)(리스너 등록과 해제 — `capture` 가 **동일성 키**라는 것까지). 여기는 그 `capture` 가 **무엇을 하는지**의 정본이다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 편에는 흔들리는 칸이 없었다** — 세는 것이 전부 **호출 순서와 횟수**이고 시간을 안 잰다. 캡처를 네 번 돌려 **이 묶음(16\~19)의 93블록이 한 글자도 같았다.**

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 호출 순서표 14줄 · `eventPhase` · `target`/`currentTarget` · 비버블 격자 9줄 · 타깃 단계의 순서 · 합성과 진짜의 견줌 · 디스패치 도중 변경 · 함수 하나 세 자리 · `composedPath()` 가짓수 | 같은 판이면 결정적이다. **네 판이 한 글자도 같았다** |
| **안 흔들린다** | 진짜 입력의 좌표 | 매번 요소의 `getBoundingClientRect` 에서 계산해 넣는다. 손으로 적은 숫자가 없다 |
| **못 잰다** | 디스패치에 걸리는 **시간** | 이 편은 순서만 본다. **재지 않았다** |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | ★ **부적용** | 전파는 트리에 자국을 안 남긴다. 누가 불렸는지는 트리를 아무리 봐도 안 보인다 |
| 창 ② 노드 프로브 | 보조 | `e.bubbles` 처럼 **이벤트 객체의 성질**을 읽는 자리((4)·(5)) |
| 창 ③ 같은 것을 두 번 읽기 | ★ **제5의 상태 — 같은 질문을 다른 창으로 물었다** | 「같은 클릭」을 **세 가지로 던져**(`new MouseEvent` · `el.click()` · 진짜 클릭) 순서표가 같은지 견줬다((2)) |
| **창 ④ 디스패치 계수기 → 호출 순서 로그** | ★★ **본체** | 리스너마다 `currentTarget`·등록 단계·`eventPhase`·`target` 을 **불린 순서대로 한 줄씩** 적는다 |
| **진짜 입력(CDP)** | ★ **쓴다 — 입력 쪽** | 진짜 클릭 · 진짜 포커스 이동 · 진짜 마우스 이동. **`focus`·`mouseenter` 는 사람이 해야 나는 이벤트**라 합성으로 흉내 내지 않았다((4)) |
| 창 ⑤ 콘솔 | **부적용** | 이 편에는 경고를 내는 자리가 없다 |

- ★★ **제5의 상태를 왜 썼나** — 「합성 이벤트로 짠 실험이 진짜 입력과 같은 답을 내나」는 이 갈래에서 두 번 뒤집혔다([12번 주제](../12-shadow-dom/2-summary.md)의 `composed` · [14번 주제](../14-dialog-popover-scripting/2-summary.md)의 가벼운 닫기). 그래서 **같은 질문을 세 입력으로 물었다.** 이 편에서는 **순서가 한 줄도 안 갈렸다**((2)) — 갈린 것은 `isTrusted` 하나였다.

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| **이벤트 경로 자체** | 경로는 디스패치가 시작될 때 만들어지고 끝나면 비워진다. **리스너 안에서 `composedPath()` 로만** 보인다((6)) |
| **브라우저가 입력을 어느 요소에 떨어뜨렸나(히트 테스트)** | 결과(`e.target`)만 보인다. 왜 그 요소인지는 안 보인다((7)) |
| **디스패치에 걸린 시간** | 재지 않았다 |
| **스크린리더가 보는 것** | 접근성 트리는 이 편의 대상이 아니다 |

## 한눈에 — 쉽게 말하면

**★ 이벤트 하나는 「엘리베이터로 내려갔다가 다시 올라오는」 한 번의 왕복이다. 층마다 두 번 멈출 수 있다 — 내려갈 때(capture)와 올라올 때(bubble).**

건물 비유로 고정한다. 대응은 문서 끝까지 이것 하나다.

| 비유 | 실체 |
|---|---|
| **꼭대기층(옥상)** | `window` |
| 층층이 내려가는 **엘리베이터** | **캡처 단계** — `window` 에서 타깃 쪽으로 |
| **손님이 내린 층** | **타깃** — `e.target` |
| 다시 올라오는 엘리베이터 | **버블 단계** — 타깃에서 `window` 쪽으로 |
| 층마다 서 있는 **안내원** | 그 노드에 단 리스너 |
| 안내원이 「**지금 몇 층에 서 있나**」 | `e.currentTarget` |
| 안내원이 「**손님이 어느 층에서 내렸나**」 | `e.target` |
| 안내원이 「**내려가는 중인가 올라오는 중인가**」 | `e.eventPhase` (1 · 2 · 3) |
| **올라오는 엘리베이터가 없는 손님** | `bubbles: false` 인 이벤트(`focus`·`load`·`mouseenter`·`scroll`) — **내려가는 쪽에서만 만날 수 있다** |

- ★ **안내원마다 `currentTarget` 은 다르고 `target` 은 같다.** 손님은 한 명이다.
- ★ **올라오지 않는 손님도 내려갈 때는 모든 층을 지나간다.** 그래서 부모가 `focus` 를 잡으려면 **내려가는 쪽(capture)** 에서 기다리면 된다.

```text
   한 번의 클릭 — 내려갔다가 올라온다

   window            ①  capture                          ⑭  bubble
     document        ②  capture                        ⑬  bubble
       html          ③  capture                      ⑫  bubble
         body        ④  capture                    ⑪  bubble
           #바깥      ⑤  capture                  ⑩  bubble
             #가운데   ⑥  capture                ⑨  bubble
               #안쪽    ⑦  capture   ⑧  bubble        <- 타깃: 둘 다 eventPhase 2
                         \_____________/
                     내려가는 길              올라오는 길
                     eventPhase 1              eventPhase 3
```

## 이 주제가 답하려는 질문

1. **중첩된 요소에 리스너를 여럿 달면 어느 순서로 불리나** — 그리고 그때 `target`·`currentTarget`·`eventPhase` 는 각각 무엇인가.
2. **타깃 자신에 단 capture 리스너와 bubble 리스너는 누가 먼저인가.**
3. **버블하지 않는 이벤트(`focus`·`load`·`mouseenter`·`scroll`)를 부모에서 어떻게 잡나.**

## 동작 방식

### (1) ★★ 본체 — 진짜 클릭 한 번이 부르는 열네 줄

**언제 쓰나** — 「리스너가 왜 이 순서로 불리지?」·「`e.target` 이 왜 내가 단 요소가 아니지?」일 때.

**던진 것** — 세 겹(`#바깥 > #가운데 > #안쪽`)과 그 위 네 자리(`window`·`document`·`html`·`body`)에 **capture 와 bubble 을 하나씩** 달았다. 자리마다 **capture 를 먼저** 등록했다. 아래 (2)·(3)·(6)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa16b-16-order.html -->
<!doctype html>
<meta charset="utf-8">
<title>16-order</title>
<div id="바깥"><div id="가운데"><button id="안쪽">누름</button></div></div>
<p><button id="과녁">과녁</button></p>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null ? 'null' : n === window ? 'window' : n === document ? 'document'
  : n.id ? '#' + n.id : n.nodeName.toLowerCase();
const 단계 = ['0 NONE', '1 CAPTURING_PHASE', '2 AT_TARGET', '3 BUBBLING_PHASE'];

// ---- 가: 일곱 자리 × (capture, bubble) — 자리마다 capture 를 먼저 등록한다
const 판 = { 합성: [], 'click()': [], 진짜: [] };
let 지금 = null;
let 붙든이벤트 = null;
const 자리 = [window, document, document.documentElement, document.body, $('바깥'), $('가운데'), $('안쪽')];
for (const t of 자리) {
  for (const cap of [true, false]) {
    t.addEventListener('click', function (e) {
      if (!지금 || 지금 === '과녁') return;
      판[지금].push([이름(e.currentTarget), cap ? 'capture' : 'bubble', 단계[e.eventPhase],
                     이름(e.target), this === e.currentTarget, e.isTrusted]);
      붙든이벤트 = e;
    }, cap);
  }
}

// ---- 나: 타깃 한 자리에 bubble 과 capture 를 번갈아 등록한다
const 과녁판 = { 합성: [], 진짜: [] };
const 과녁 = $('과녁');
for (const [표, cap] of [['A', false], ['B', true], ['C', false], ['D', true]]) {
  과녁.addEventListener('click', e => {
    if (지금 && 지금.startsWith('과녁')) 과녁판[지금.slice(3)].push(표 + '(' + (cap ? 'capture' : 'bubble') + ', phase ' + e.eventPhase + ')');
  }, cap);
}
과녁.parentNode.addEventListener('click', e => {
  if (지금 && 지금.startsWith('과녁')) 과녁판[지금.slice(3)].push('부모 p(capture, phase ' + e.eventPhase + ')');
}, true);
과녁.parentNode.addEventListener('click', e => {
  if (지금 && 지금.startsWith('과녁')) 과녁판[지금.slice(3)].push('부모 p(bubble, phase ' + e.eventPhase + ')');
});

window.__단계 = [
  ['js', "지금 = '합성'; $('안쪽').dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); 1"],
  ['js', "지금 = 'click()'; $('안쪽').click(); 1"],
  ['js', "지금 = '진짜'; 1"],
  ['click', '#안쪽'],
  ['js', "지금 = '과녁-합성'; 과녁.dispatchEvent(new MouseEvent('click', { bubbles: true })); 1"],
  ['js', "지금 = '과녁-진짜'; 1"],
  ['click', '#과녁'],
  ['js', "지금 = null; 1"],
];

window.__끝 = () => {
  const O = [];
  O.push('가. 진짜 클릭 한 번 — 리스너가 불린 순서');
  O.push(padw('#', 4) + padw('currentTarget', 16) + padw('등록', 9) + padw('eventPhase', 20) + padw('target', 10) + 'this===currentTarget');
  판.진짜.forEach((r, i) => O.push(padw(String(i + 1), 4) + padw(r[0], 16) + padw(r[1], 9) + padw(r[2], 20) + padw(r[3], 10) + r[4]));
  O.push('');
  O.push('같은 순서표를 세 가지로 던져 견준다');
  const 줄 = r => r.slice(0, 5).join(' | ');
  let 갈림 = 0;
  const n = Math.max(판.진짜.length, 판.합성.length, 판['click()'].length);
  for (let i = 0; i < n; i++) {
    const a = 판.진짜[i], b = 판.합성[i], c = 판['click()'][i];
    if (!a || !b || !c || 줄(a) !== 줄(b) || 줄(a) !== 줄(c)) 갈림++;
  }
  O.push('  줄 수 — 진짜 ' + 판.진짜.length + ' · new MouseEvent ' + 판.합성.length + ' · el.click() ' + 판['click()'].length);
  O.push('  isTrusted — 진짜 ' + 판.진짜[0][5] + ' · new MouseEvent ' + 판.합성[0][5] + ' · el.click() ' + 판['click()'][0][5]);
  O.push('  세 판의 순서표가 갈린 줄 = ' + 갈림 + ' / ' + n);
  O.push('');
  O.push('디스패치가 끝난 뒤 붙들어 둔 이벤트 객체를 다시 읽으면');
  O.push('  e.target = ' + 이름(붙든이벤트.target) + ' · e.currentTarget = ' + 이름(붙든이벤트.currentTarget)
       + ' · e.eventPhase = ' + 붙든이벤트.eventPhase);
  O.push('');
  O.push('나. 타깃 한 자리에 A(bubble) B(capture) C(bubble) D(capture) 순서로 등록하고 누르면');
  O.push('  new MouseEvent : ' + 과녁판.합성.join(' → '));
  O.push('  진짜 클릭      : ' + 과녁판.진짜.join(' → '));
  return O.join('\n');
};
</script>
```

**하네스** — CDP 로 붙어 진짜 입력을 넣는다. 좌표는 **매번 요소의 `getBoundingClientRect` 에서 계산**하고, 기다림은 시간 상수가 아니라 **`Page.loadEventFired` 와 CDP 응답**이다. 17·18·19편도 이것을 쓴다.

```python
# wa16b-cdp.py
#!/usr/bin/env python3
"""CDP 로 헤드리스 Chrome 에 붙어 진짜 입력(마우스·휠·키)을 넣고 페이지가 적은 줄을 찍는다.

사용:
  wa16b-cdp.py page <html파일>
      페이지를 열고 load 를 기다린 뒤 window.__단계 (배열) 를 차례로 실행하고
      window.__끝() 이 돌려준 문자열을 표준 출력에 찍는다.
  wa16b-cdp.py log <html파일>
      같은 일을 한 뒤 콘솔 경고(Log.entryAdded)를 「출처 · 수준 · 문구」 한 줄씩 찍고 줄 수를 센다.
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
PROF = os.path.join(HERE, f".prof-wa16b-{os.getpid()}")
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


def start():
    shutil.rmtree(PROF, ignore_errors=True)
    proc = subprocess.Popen(["google-chrome"] + FLAGS,
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
    mode, path = sys.argv[1], sys.argv[2]
    frag = ""
    if "#" in path:                      # 파일#조각 — 조각은 페이지가 읽는다
        path, frag = path.split("#", 1)
        frag = "#" + frag
    url = "file://" + os.path.abspath(path) + frag
    proc, c = start()
    try:
        tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
        for m in ("Page.enable", "Runtime.enable", "Log.enable"):
            c.send(m, sid=sid)
        c.send("Page.navigate", {"url": url}, sid)
        c.wait("Page.loadEventFired", sid)
        steps = json.loads(evaluate(c, sid, "JSON.stringify(window.__단계 || [])"))
        for st in steps:
            if os.environ.get("WA16B_DEBUG"):
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
        proc.terminate()
        proc.wait()
        shutil.rmtree(PROF, ignore_errors=True)


if __name__ == "__main__":
    main()
```

```text
$ python3 wa16b-cdp.py page wa16b-16-order.html | sed -n '1,16p'
가. 진짜 클릭 한 번 — 리스너가 불린 순서
#   currentTarget   등록     eventPhase          target    this===currentTarget
1   window          capture  1 CAPTURING_PHASE   #안쪽     true
2   document        capture  1 CAPTURING_PHASE   #안쪽     true
3   html            capture  1 CAPTURING_PHASE   #안쪽     true
4   body            capture  1 CAPTURING_PHASE   #안쪽     true
5   #바깥           capture  1 CAPTURING_PHASE   #안쪽     true
6   #가운데         capture  1 CAPTURING_PHASE   #안쪽     true
7   #안쪽           capture  2 AT_TARGET         #안쪽     true
8   #안쪽           bubble   2 AT_TARGET         #안쪽     true
9   #가운데         bubble   3 BUBBLING_PHASE    #안쪽     true
10  #바깥           bubble   3 BUBBLING_PHASE    #안쪽     true
11  body            bubble   3 BUBBLING_PHASE    #안쪽     true
12  html            bubble   3 BUBBLING_PHASE    #안쪽     true
13  document        bubble   3 BUBBLING_PHASE    #안쪽     true
14  window          bubble   3 BUBBLING_PHASE    #안쪽     true
(exit 0)
```

- **열네 줄이 전부 불렸다** — 일곱 자리 × 두 단계.
- **1\~6 은 내려가는 길**이다. `window` 에서 시작해 `#가운데` 까지 **capture 리스너만** 불렸고 `eventPhase` 가 전부 **1(`CAPTURING_PHASE`)** 이다.
- ★ **7\~8 은 타깃**이다. `#안쪽` 의 capture 와 bubble 이 **둘 다 `eventPhase` 2(`AT_TARGET`)** 다. **타깃에서는 「캡처 단계」도 「버블 단계」도 아니다.**
- **9\~14 는 올라오는 길**이다. **bubble 리스너만** 불렸고 `eventPhase` 가 전부 **3(`BUBBLING_PHASE`)** 이다. 순서는 1\~6 을 **정확히 뒤집은 것**이다.
- ★ **`target` 은 열네 줄 모두 `#안쪽`** 이다. 바뀌는 것은 **`currentTarget`** 뿐이다.
- ★ **`this === currentTarget` 이 열네 줄 모두 `true`** — 보통 함수로 단 리스너의 `this` 는 **리스너를 단 자리**다(`target` 이 아니다). `this` 규칙의 정본은 JS 갈래의 [07번 주제](../../languages/js/syntax/07-this-binding-four-rules/2-summary.md)이고, 화살표 함수·`handleEvent` 의 `this` 는 [15번 주제](../15-listener-registration/2-summary.md)가 이미 쟀다.

```text
   ★ 세 가지 값 — 줄마다 무엇이 바뀌나

   줄   currentTarget   eventPhase         target
   --   -------------   ----------------   ------
   1    window          1 CAPTURING        #안쪽    <- target 은
   ...  (내려간다)      1                  #안쪽       끝까지 같다
   6    #가운데         1                  #안쪽
   7    #안쪽           2 AT_TARGET        #안쪽    <- 타깃에서는
   8    #안쪽           2 AT_TARGET        #안쪽       capture 도 bubble 도 2
   9    #가운데         3 BUBBLING         #안쪽
   ...  (올라간다)      3                  #안쪽
   14   window          3 BUBBLING         #안쪽

   바뀌는 칸은 currentTarget 과 eventPhase 둘뿐이다
```

```text
   어느 리스너가 어느 길에서 불리나

                         내려가는 길(1)    타깃(2)       올라오는 길(3)
   capture 로 단 것      불린다             불린다         안 불린다
   bubble 로 단 것       안 불린다          불린다         불린다

   ★ 타깃에서만 두 종류가 다 불린다
```

**명세가 정한 절차** — DOM 표준 「dispatch」는 경로를 한 번 만들고 **두 번 훑는다.**

```text
   DOM 「dispatch」 — 경로를 두 번 훑는다

   경로(path) = [ #안쪽, #가운데, #바깥, body, html, document, window ]

   1차: 경로를 거꾸로(window -> #안쪽)
        자리가 타깃이면 eventPhase = AT_TARGET, 아니면 CAPTURING_PHASE
        invoke(자리, "capturing")   -> capture 로 단 리스너만 부른다

   2차: 경로를 바로(#안쪽 -> window)
        자리가 타깃이면 eventPhase = AT_TARGET
        아니면 bubbles 가 false 면 건너뛴다, 참이면 BUBBLING_PHASE
        invoke(자리, "bubbling")    -> capture 가 아닌 리스너만 부른다

   끝: eventPhase = NONE · currentTarget = null
```

- ★ **「inner invoke」가 거르는 두 줄**이 표의 모양을 만든다 — 명세 원문은 「phase 가 "capturing" 인데 리스너의 capture 가 false 면 건너뛴다」와 「phase 가 "bubbling" 인데 capture 가 true 면 건너뛴다」다.
- ★ **2차에서 `bubbles` 를 보는 것은 타깃이 아닌 자리뿐**이다. 그래서 **버블하지 않는 이벤트도 타깃 자신의 bubble 리스너는 부른다**((4)의 「자식 자신」 칸).

비용 — 리스너를 **달 자리를 고르는 것**이 곧 **어느 단계에서 받을지 고르는 것**이다. 한 자리에 두 단계를 다 받고 싶으면 두 번 단다(그 둘은 [15번 주제](../15-listener-registration/2-summary.md)의 동일성 격자대로 **다른 줄**이다).

### (2) 같은 순서표를 세 가지로 던지면 — 제5의 상태

**언제 쓰나** — 「테스트에서 `dispatchEvent` 로 짠 순서가 실제 클릭과 같은가」일 때.

```text
$ python3 wa16b-cdp.py page wa16b-16-order.html | sed -n '18,21p'
같은 순서표를 세 가지로 던져 견준다
  줄 수 — 진짜 14 · new MouseEvent 14 · el.click() 14
  isTrusted — 진짜 true · new MouseEvent false · el.click() false
  세 판의 순서표가 갈린 줄 = 0 / 14
(exit 0)
```

- **줄 수가 셋 다 14** 이고, **순서표가 갈린 줄이 0 / 14** 다. 합성 `new MouseEvent('click', { bubbles: true })`·`el.click()`·진짜 클릭이 **같은 경로를 같은 순서로** 지났다.
- ★ **갈린 것은 `isTrusted` 하나**다 — 진짜만 `true` 다.
- ★ **그러나 「합성은 늘 진짜와 같다」로 일반화하지 마라.** 이 판에서 같았던 것은 **순서**다. **생성자 기본값**이 다르면 경로 자체가 달라진다 — `new MouseEvent('click')` 은 `bubbles` 가 `false` 다((5)). 그림자 경계에서는 `composed` 가 갈린다([12번 주제](../12-shadow-dom/2-summary.md)).

```text
   세 가지 입력 — 무엇이 같고 무엇이 다른가

                                   순서표     isTrusted   bubbles 기본값
   new MouseEvent('click', {bubbles:true})   같다   false       (직접 줬다)
   el.click()                      같다       false       true
   사람의 진짜 클릭(CDP)            같다       true        true

   ★ 순서는 경로가 정하고, 경로는 bubbles·composed 가 정한다
```

### (3) ★★ 타깃 한 자리에 capture 와 bubble 을 번갈아 달면

**언제 쓰나** — 「타깃에서는 등록 순서대로 부른다」는 설명을 봤을 때. **그 설명을 이 판에 던져 봤다.**

```text
$ python3 wa16b-cdp.py page wa16b-16-order.html | sed -n '26,28p'
나. 타깃 한 자리에 A(bubble) B(capture) C(bubble) D(capture) 순서로 등록하고 누르면
  new MouseEvent : 부모 p(capture, phase 1) → B(capture, phase 2) → D(capture, phase 2) → A(bubble, phase 2) → C(bubble, phase 2) → 부모 p(bubble, phase 3)
  진짜 클릭      : 부모 p(capture, phase 1) → B(capture, phase 2) → D(capture, phase 2) → A(bubble, phase 2) → C(bubble, phase 2) → 부모 p(bubble, phase 3)
(exit 0)
```

- 등록 순서는 **A(bubble) → B(capture) → C(bubble) → D(capture)** 였다.
- ★★ **불린 순서는 B → D → A → C** 다. **capture 둘이 먼저, bubble 둘이 나중**이고, 각 무리 안에서는 등록 순서다. **넷 다 `eventPhase` 2** 다.
- ★ **합성 클릭과 진짜 클릭이 같은 답**이다.
- **옛 설명(「타깃에서는 단계를 안 가리고 등록 순서」)은 이 판에 맞지 않는다.** 명세 본문도 그렇다 — (1)의 절차에서 **타깃 자리는 1차(capturing)에서 한 번, 2차(bubbling)에서 한 번** 불리고, 1차는 capture 리스너만, 2차는 나머지만 부른다.

```text
   타깃 한 자리 — 등록 순서와 불린 순서

   등록:   A(bubble)   B(capture)   C(bubble)   D(capture)

   1차(capturing) 에서 타깃을 부를 때   -> capture 만:   B  D
   2차(bubbling)  에서 타깃을 부를 때   -> 나머지만:     A  C

   불린 순서:  부모(capture) -> B -> D -> A -> C -> 부모(bubble)
              eventPhase:  1     2    2    2    2       3
```

- ★ **「타깃에서의 순서」를 코드가 기대하면 안 되는 이유**가 여기 있다 — 설명이 바뀐 적이 있는 자리다. 순서가 중요하면 **한 리스너 안에서 순서를 정해라.**

### (4) ★★ 버블하지 않는 이벤트 — 부모는 어디서 받을 수 있나

**언제 쓰나** — 「부모에 `focus` 리스너를 달았는데 안 불린다」일 때.

**던진 것** — 자식에게 아홉 가지 이벤트를 **진짜로** 일으켰다: 진짜 클릭(`click`·`focus`·`focusin`), 다른 곳 클릭(`blur`·`focusout`), 진짜 마우스 이동(`mouseenter`·`mouseover`), 그림 로드(`load`), 요소 스크롤(`scroll`). 부모·`document`·`window` 에는 capture 와 bubble 을 달고 **`target` 이 그 자식인 것만** 셌다(부모 자신에게 난 `mouseenter` 를 빼려고).

```html
<!-- wa16b-16-nobubble.html -->
<!doctype html>
<meta charset="utf-8">
<title>16-nobubble</title>
<style>
  #부모4 { height: 60px; }
  #자식4 { height: 50px; overflow: auto; } #자식4 > div { height: 300px; }
</style>
<p><button id="저쪽">저쪽</button></p>
<div id="부모1"><input id="자식1" value="입력칸"></div>
<div id="부모2"><span id="자식2">여기로 마우스를 옮긴다</span></div>
<div id="부모3"></div>
<div id="부모4"><div id="자식4"><div>긴 내용</div></div></div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 그림 = document.createElement('img');
그림.id = '자식3';

// 행: [이벤트 이름, 부모, 자식]
const 행 = [
  ['click', $('부모1'), $('자식1')],
  ['focus', $('부모1'), $('자식1')],
  ['blur', $('부모1'), $('자식1')],
  ['focusin', $('부모1'), $('자식1')],
  ['focusout', $('부모1'), $('자식1')],
  ['mouseenter', $('부모2'), $('자식2')],
  ['mouseover', $('부모2'), $('자식2')],
  ['load', $('부모3'), 그림],
  ['scroll', $('부모4'), $('자식4')],
];
const 칸 = {};
const 기다림 = {};
for (const [형, 부모, 자식] of 행) {
  const k = 형;
  칸[k] = { bubbles: '-', 자기: 0, 부모캡처: 0, 부모버블: 0, 문서캡처: 0, 창캡처: 0 };
  let 풀기;
  기다림[k] = new Promise(r => { 풀기 = r; });
  자식.addEventListener(형, e => { 칸[k].bubbles = e.bubbles; 칸[k].자기++; 풀기(); });
  // 부모·문서·창에서는 타깃이 그 자식인 것만 센다(부모 자신에게 난 mouseenter 등은 빼려고)
  부모.addEventListener(형, e => { if (e.target === 자식) 칸[k].부모캡처++; }, true);
  부모.addEventListener(형, e => { if (e.target === 자식) 칸[k].부모버블++; });
  document.addEventListener(형, e => { if (e.target === 자식) 칸[k].문서캡처++; }, true);
  window.addEventListener(형, e => { if (e.target === 자식) 칸[k].창캡처++; }, true);
}
window.__기다림 = k => 기다림[k].then(() => 1);

window.__단계 = [
  ['move', '#저쪽'],
  ['click', '#자식1'],          // click · focus · focusin
  ['js', "__기다림('focus')"],
  ['click', '#저쪽'],           // blur · focusout
  ['js', "__기다림('blur')"],
  ['move', '#자식2'],           // mouseenter · mouseover
  ['js', "__기다림('mouseenter')"],
  ['js', "$('부모3').appendChild(그림); 그림.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7' ; __기다림('load')"],
  ['js', "$('자식4').scrollTop = 40; __기다림('scroll')"],
];

window.__끝 = () => {
  const O = [];
  O.push('자식에서 난 이벤트를 부모·document·window 가 받았나 (받은 횟수)');
  O.push(padw('이벤트', 12) + padw('e.bubbles', 11) + padw('자식 자신', 10) + padw('부모 capture', 14)
       + padw('부모 bubble', 13) + padw('document capture', 18) + 'window capture');
  let 갈림 = 0;
  for (const [형] of 행) {
    const c = 칸[형];
    if ((c.부모캡처 > 0) !== (c.부모버블 > 0)) 갈림++;
    O.push(padw(형, 12) + padw(String(c.bubbles), 11) + padw(String(c.자기), 10) + padw(String(c.부모캡처), 14)
         + padw(String(c.부모버블), 13) + padw(String(c.문서캡처), 18) + c.창캡처);
  }
  O.push('');
  O.push('부모의 capture 칸과 bubble 칸이 갈린 줄 = ' + 갈림 + ' / ' + 행.length);
  return O.join('\n');
};
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-16-nobubble.html
자식에서 난 이벤트를 부모·document·window 가 받았나 (받은 횟수)
이벤트      e.bubbles  자식 자신 부모 capture  부모 bubble  document capture  window capture
click       true       1         1             1            1                 1
focus       false      1         1             0            1                 1
blur        false      1         1             0            1                 1
focusin     true       1         1             1            1                 1
focusout    true       1         1             1            1                 1
mouseenter  false      1         1             0            1                 1
mouseover   true       1         1             1            1                 1
load        false      1         1             0            1                 0
scroll      false      1         1             0            1                 1

부모의 capture 칸과 bubble 칸이 갈린 줄 = 5 / 9
(exit 0)
```

- **`e.bubbles` 가 `false` 인 것은 다섯** — `focus`·`blur`·`mouseenter`·`load`·`scroll`.
- ★★ **그 다섯 줄 전부에서 부모의 bubble 칸이 0 이고 capture 칸이 1** 이다. 마지막 줄 **「갈린 줄 = 5 / 9」가 정확히 그 다섯**이다.
- ★ **올라오지 않는 이벤트도 내려가는 길은 지난다** — 그래서 **부모의 capture 리스너**와 **`document` 의 capture 리스너**가 받는다.
- ★ **`focusin`·`focusout` 은 버블한다** — `focus`·`blur` 의 **버블하는 짝**이다. 부모에서 bubble 로 받고 싶으면 이쪽을 쓴다.
- **`mouseover` 는 버블한다** — `mouseenter` 의 버블하는 짝이다(다만 자식 사이를 옮길 때마다 또 난다 — [18번 주제](../18-event-delegation/2-summary.md)).
- ★★ **`load` 줄만 `window capture` 가 0** 이다. `document` 의 capture 는 받았는데 `window` 는 못 받았다 — 아래 (5)의 명세 문장 하나가 이것을 만든다.

```text
   부모가 자식의 이벤트를 받는 두 길

   bubbles: true  (click · focusin · focusout · mouseover)
      부모 capture  O        부모 bubble  O

   bubbles: false (focus · blur · mouseenter · load · scroll)
      부모 capture  O        부모 bubble  X   <- 올라오는 엘리베이터가 없다

   ★ 부모에서 focus 를 잡는 두 방법
      ① addEventListener('focus', f, true)    내려가는 길에서
      ② addEventListener('focusin', f)        버블하는 짝으로
```

```text
   진짜 입력이 무엇을 일으켰나 — 이 판의 순서

   마우스를 #저쪽 에 둔다
   #자식1 을 누른다        -> click · focus · focusin
   #저쪽 을 누른다         -> blur · focusout
   #자식2 로 옮긴다        -> mouseenter · mouseover
   그림을 붙이고 src 를 준다 -> load
   #자식4.scrollTop = 40   -> scroll

   ★ 각 단계 뒤에 「자식 자신의 리스너가 불렸나」를 프로미스로 기다렸다(시간 상수 없음)
```

### (5) `load` 는 `window` 까지 안 간다 — 명세 한 문장

**언제 쓰나** — 「`window` 에 capture 로 `load` 를 달면 모든 그림의 로드를 잡겠지」라고 생각했을 때.

- (4)의 `load` 줄 — **`document capture` 1 · `window capture` 0** 이다.
- ★ **HTML 표준이 `Document` 의 「get the parent」를 이렇게 정한다** — 「이벤트 타입이 `"load"` 이거나 문서에 브라우징 맥락이 없으면 **null**, 아니면 문서의 전역 객체(`window`)」.
- 그래서 **`load` 이벤트의 경로는 `document` 에서 끊긴다.** 그림의 `load` 가 `window` 의 `load` 리스너(페이지 로드용)를 **잘못 부르지 않게** 하려는 장치다.
- ★ **다른 이벤트는 `window` 까지 간다** — 같은 격자에서 `focus`·`scroll`·`mouseenter` 의 `window capture` 칸은 1 이다.

```text
   경로가 document 에서 끊기는 이벤트

   img 의 load:     img -> #부모3 -> body -> html -> document  (끝)
   img 의 focus:    ...                             -> document -> window

   ★ 명세: Document 의 get the parent 는 type 이 "load" 면 null
```

### (6) 디스패치가 끝난 뒤 이벤트 객체를 붙들고 있으면

**언제 쓰나** — 리스너에서 받은 `e` 를 `setTimeout`·`await` 뒤에 읽을 때.

```text
$ python3 wa16b-cdp.py page wa16b-16-order.html | sed -n '23,24p'
디스패치가 끝난 뒤 붙들어 둔 이벤트 객체를 다시 읽으면
  e.target = #안쪽 · e.currentTarget = null · e.eventPhase = 0
(exit 0)
```

- **`target` 은 남는다** — `#안쪽`.
- ★ **`currentTarget` 은 `null`** 이고 **`eventPhase` 는 0(`NONE`)** 이다. 명세의 dispatch 마지막 단계가 **둘을 지운다**.
- ★ **그래서 `await` 뒤에 `e.currentTarget` 을 읽으면 `null` 이다** — 리스너 첫 줄에서 `const 자리 = e.currentTarget` 으로 **받아 두어라.**

```text
   리스너 밖으로 나간 이벤트 객체

   리스너 안                  리스너 밖(디스패치가 끝난 뒤)
   e.target        #안쪽      e.target        #안쪽     <- 남는다
   e.currentTarget #안쪽      e.currentTarget null      <- 지워진다
   e.eventPhase    2          e.eventPhase    0         <- NONE

   고치는 법:  const 자리 = e.currentTarget;   await …;   자리.…
```

### (7) 생성자의 `bubbles` 기본값 · 문서 밖의 경로 · 글자를 눌렀을 때

**언제 쓰나** — 합성 이벤트로 테스트를 짤 때, 그리고 「`e.target` 이 왜 텍스트 노드가 아니지?」일 때.

**던진 것** — 가·나는 합성 이벤트, 다는 진짜 클릭이다.

```html
<!-- wa16b-16-more.html -->
<!doctype html>
<meta charset="utf-8">
<title>16-more</title>
<div id="부모"><p id="문단">그냥 글자 <b id="굵게">굵은 글자</b></p></div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === window ? 'window' : n === document ? 'document' : n.nodeType === 3 ? '#text'
  : n.id ? '#' + n.id : n.nodeName.toLowerCase();
const O = [];

O.push('가. 생성자로 만든 이벤트의 bubbles 기본값 — 부모의 bubble 리스너가 받나');
const 받음 = {};
$('부모').addEventListener('시험', e => { 받음[e.detail] = true; });
$('부모').addEventListener('click', e => { if (!e.isTrusted) 받음[e.detail] = true; });
const 만들기 = [
  ['new CustomEvent(t)', () => new CustomEvent('시험', { detail: 1 }), 1],
  ["new MouseEvent('click')", () => new MouseEvent('click', { detail: 2 }), 2],
  ["new MouseEvent('click', { bubbles: true })", () => new MouseEvent('click', { bubbles: true, detail: 3 }), 3],
];
O.push(padw('만든 꼴', 44) + padw('bubbles', 9) + '부모 bubble 리스너');
for (const [라벨, f, k] of 만들기) {
  const e = f();
  $('문단').dispatchEvent(e);
  O.push(padw(라벨, 44) + padw(String(e.bubbles), 9) + (받음[k] ? '받음' : '못 받음'));
}
O.push('');

O.push('나. 문서에 안 붙은 나무에서 던지면 — 경로');
const 떼어둔 = document.createElement('section');
const 아이 = document.createElement('span');
떼어둔.append(아이);
let 경로 = null;
아이.addEventListener('시험2', e => { 경로 = e.composedPath().map(이름).join(' → '); });
아이.dispatchEvent(new Event('시험2', { bubbles: true }));
O.push('  composedPath() = ' + 경로);
let 붙은경로 = null;
$('굵게').addEventListener('시험3', e => { 붙은경로 = e.composedPath().map(이름).join(' → '); });
$('굵게').dispatchEvent(new Event('시험3', { bubbles: true }));
O.push('  (견줌) 문서 안의 #굵게 에서 던지면 composedPath() = ' + 붙은경로);
O.push('');

const 진짜 = [];
document.addEventListener('click', e => { if (e.isTrusted) 진짜.push([e.target, e.currentTarget]); });
window.__단계 = [
  ['clickat', '#문단', 6, 6],
  ['click', '#굵게'],
];
window.__끝 = () => {
  O.push('다. 진짜 클릭 — 글자를 눌렀을 때 document 리스너가 본 target');
  O.push('  #문단 의 맨 앞 글자 위 → e.target = ' + 이름(진짜[0][0]) + ' · e.currentTarget = ' + 이름(진짜[0][1]));
  O.push('  #굵게 의 한가운데     → e.target = ' + 이름(진짜[1][0]) + ' · e.currentTarget = ' + 이름(진짜[1][1]));
  return O.join('\n');
};
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-16-more.html | sed -n '1,5p'
가. 생성자로 만든 이벤트의 bubbles 기본값 — 부모의 bubble 리스너가 받나
만든 꼴                                     bubbles  부모 bubble 리스너
new CustomEvent(t)                          false    못 받음
new MouseEvent('click')                     false    못 받음
new MouseEvent('click', { bubbles: true })  true     받음
(exit 0)
```

- ★★ **생성자로 만든 이벤트는 `bubbles` 가 기본 `false`** 다 — `new CustomEvent` 도, **`new MouseEvent('click')` 조차** 그렇다. 부모의 bubble 리스너가 **못 받는다.**
- **`{ bubbles: true }` 를 줘야** 받는다. 진짜 클릭은 처음부터 `true` 다.
- ★ **테스트가 초록인데 실제로는 다르게 도는 자리**다 — 거꾸로도 된다. 「부모가 못 받는다」는 합성 테스트는 **진짜 클릭에서는 받는다.**

```text
$ python3 wa16b-cdp.py page wa16b-16-more.html | sed -n '7,9p'
나. 문서에 안 붙은 나무에서 던지면 — 경로
  composedPath() = span → section
  (견줌) 문서 안의 #굵게 에서 던지면 composedPath() = #굵게 → #문단 → #부모 → body → html → document → window
(exit 0)
```

- **문서에 안 붙은 나무에서 던지면 경로가 그 나무에서 끝난다** — `span → section`. `document` 도 `window` 도 없다.
- **문서 안에서 던지면 `window` 까지 일곱 칸**이다.
- ★ **경로는 디스패치가 시작될 때 부모를 따라 올라가 만든다**(명세의 「get the parent」). 붙어 있지 않으면 올라갈 부모가 없다.

```text
$ python3 wa16b-cdp.py page wa16b-16-more.html | sed -n '11,13p'
다. 진짜 클릭 — 글자를 눌렀을 때 document 리스너가 본 target
  #문단 의 맨 앞 글자 위 → e.target = #문단 · e.currentTarget = document
  #굵게 의 한가운데     → e.target = #굵게 · e.currentTarget = document
(exit 0)
```

- ★ **글자 위를 눌러도 `e.target` 은 텍스트 노드가 아니라 그 글자를 담은 요소**(`#문단`)다. 굵은 글자 위를 누르면 `#굵게` 다.
- **`currentTarget` 은 리스너를 단 `document`** 다.
- 그래서 위임 리스너는 **`e.target` 이 「내가 기다리는 요소의 자식의 자식」일 수 있다**는 것을 전제로 짜야 한다 — [18번 주제](../18-event-delegation/2-summary.md)의 `closest()` 가 그 자리다.

```text
   e.target 은 「가장 깊은 요소」 — 텍스트 노드는 아니다

   <p id="문단">그냥 글자 <b id="굵게">굵은 글자</b></p>

   「그냥 글자」 위    -> e.target = #문단
   「굵은 글자」 위    -> e.target = #굵게

   위임 리스너가 <p> 를 원하면  e.target.closest('p')
```

### (8) 디스패치 도중에 바꾸면 — 경로는 고정, 리스너 목록은 자리마다 새로 읽는다

**언제 쓰나** — 리스너 안에서 DOM 을 옮기거나 다른 요소에 리스너를 붙이는 코드를 볼 때.

**던진 것** — 가는 **내려가는 길의 `#바깥` 이 아직 안 지난 `#가운데` 에 리스너를 더한다.** 나는 **타깃이 자기 capture 리스너에서 자기를 `#다른곳` 으로 옮긴다.** 둘 다 진짜 클릭이다.

```html
<!-- wa16b-16-live.html -->
<!doctype html>
<meta charset="utf-8">
<title>16-live</title>
<div id="바깥"><div id="가운데"><button id="안쪽">누름</button></div></div>
<div id="다른곳"></div>
<script>
const $ = id => document.getElementById(id);
const 이름 = n => n === null ? 'null' : n === window ? 'window' : n === document ? 'document'
  : n.id ? '#' + n.id : n.nodeName.toLowerCase();
const 로그 = [];
let 판 = null;
const 기록 = 표 => e => { if (판) 로그.push(표 + '@' + 이름(e.currentTarget)); };

// 가: 내려가는 길에서, 아직 안 지난 자리(#가운데)에 bubble 리스너를 더한다
$('바깥').addEventListener('click', e => {
  if (판 !== '가') return;
  로그.push('capture@#바깥 이 #가운데 에 bubble 리스너를 더함');
  $('가운데').addEventListener('click', e => { if (판 === '가') 로그.push('더한것@' + 이름(e.currentTarget)); });
}, true);

// 나: 타깃의 capture 리스너가 타깃을 문서에서 떼어 #다른곳 으로 옮긴다
$('안쪽').addEventListener('click', e => {
  if (판 !== '나') return;
  $('다른곳').append($('안쪽'));
  로그.push('capture@#안쪽 이 자기를 #다른곳 으로 옮김 · 지금 부모 = ' + 이름($('안쪽').parentNode));
}, true);
for (const id of ['바깥', '가운데', '다른곳']) $(id).addEventListener('click', 기록('bubble'));

const 줄 = [];
window.__한판 = k => { 판 = k; 로그.length = 0; return 1; };
window.__적기 = k => { 줄.push(k + '. ' + 로그.join(' → ')); 판 = null; return 1; };
window.__단계 = [
  ['js', "__한판('가')"], ['click', '#안쪽'], ['js', "__적기('가')"],
  ['js', "__한판('나')"], ['click', '#안쪽'], ['js', "__적기('나')"],
];
window.__끝 = () => ['진짜 클릭 — 디스패치 도중에 바꾸면', ...줄].join('\n');
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-16-live.html
진짜 클릭 — 디스패치 도중에 바꾸면
가. capture@#바깥 이 #가운데 에 bubble 리스너를 더함 → bubble@#가운데 → 더한것@#가운데 → bubble@#바깥
나. capture@#안쪽 이 자기를 #다른곳 으로 옮김 · 지금 부모 = #다른곳 → bubble@#가운데 → bubble@#바깥
(exit 0)
```

- ★ **가 — 아직 안 지난 자리에 더한 리스너는 이번 디스패치에서 불린다**(`더한것@#가운데`).
  [15번 주제](../15-listener-registration/2-summary.md)의 (8)은 「리스너 안에서 **같은 자리에** 더한 것은 이번 판에 안 들어온다」였다. **둘은 모순이 아니다** — 명세의 invoke 는 **자리에 도착할 때마다 그 자리의 목록을 복사**한다. 같은 자리는 이미 복사가 끝났고, 다음 자리는 아직이다.
- ★★ **나 — 타깃을 옮겨도 올라오는 길은 옛 조상**이다(`#가운데` → `#바깥`). 옮긴 뒤의 부모 `#다른곳` 은 **안 불렸다.** 경로는 **디스패치가 시작될 때 한 번 만들고** 도중에 다시 안 만든다.

```text
   경로와 목록 — 무엇이 언제 굳나

   디스패치 시작 ── 경로를 만든다 [#안쪽 #가운데 #바깥 body html document window]
        |                          이후로 안 바뀐다(나)
        v
   자리마다 도착할 때 ── 그 자리의 리스너 목록을 복사한다
                           이미 복사한 자리에 더한 것  -> 이번엔 안 불린다(15편 (8))
                           아직 안 온 자리에 더한 것   -> 불린다(가)
```

### (9) 함수 하나를 세 자리에 달면 · 경로는 한 가지 · 단계 번호

**언제 쓰나** — 「같은 핸들러를 여러 요소에 붙였는데 `this` 가 무엇이 되나」·「리스너마다 경로가 다르게 보이나」일 때.

```html
<!-- wa16b-16-same.html -->
<!doctype html>
<meta charset="utf-8">
<title>16-same</title>
<div id="바깥"><div id="가운데"><button id="안쪽">누름</button></div></div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null ? 'null' : n === window ? 'window' : n === document ? 'document'
  : n.id ? '#' + n.id : n.nodeName.toLowerCase();
const 줄 = [];
const 경로들 = new Set();
let 켬 = false;
// 함수 하나를 세 자리에 bubble 로 단다
function 하나(e) {
  if (!켬) return;
  줄.push(padw(이름(this), 10) + padw(이름(e.currentTarget), 16) + padw(이름(e.target), 10) + e.eventPhase);
}
for (const id of ['안쪽', '가운데', '바깥']) $(id).addEventListener('click', 하나);
// 열네 자리에서 본 composedPath() 가 몇 가지인가
for (const t of [window, document, document.documentElement, document.body, $('바깥'), $('가운데'), $('안쪽')]) {
  for (const cap of [true, false]) t.addEventListener('click', e => { if (켬) 경로들.add(e.composedPath().map(이름).join(' ')); }, cap);
}
window.__단계 = [['js', '켬 = true; 1'], ['click', '#안쪽'], ['js', '켬 = false; 1']];
window.__끝 = () => [
  '가. 함수 하나를 세 자리에 달고 진짜로 한 번 누르면',
  padw('this', 10) + padw('currentTarget', 16) + padw('target', 10) + 'eventPhase',
  ...줄,
  '',
  '나. 열네 리스너가 본 composedPath() — 서로 다른 것의 가짓수 = ' + 경로들.size,
  '   ' + [...경로들][0],
  '',
  '다. 단계 상수',
  '   Event.NONE=' + Event.NONE + ' · CAPTURING_PHASE=' + Event.CAPTURING_PHASE
    + ' · AT_TARGET=' + Event.AT_TARGET + ' · BUBBLING_PHASE=' + Event.BUBBLING_PHASE,
].join('\n');
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-16-same.html | sed -n '1,5p'
가. 함수 하나를 세 자리에 달고 진짜로 한 번 누르면
this      currentTarget   target    eventPhase
#안쪽     #안쪽           #안쪽     2
#가운데   #가운데         #안쪽     3
#바깥     #바깥           #안쪽     3
(exit 0)
```

- **함수 하나가 세 번 불렸다** — 등록한 자리마다 한 번씩이다([15번 주제](../15-listener-registration/2-summary.md)의 동일성 조건은 **한 자리 안의** 이야기라 여기서는 안 겹친다).
- **`this` 와 `currentTarget` 은 줄마다 그 자리**이고 **`target` 은 셋 다 `#안쪽`** 이다. `eventPhase` 는 타깃 자리만 2, 나머지는 3.
- ★ **그래서 같은 함수가 「어느 자리에서 불렸나」를 알려면 `this`(또는 `currentTarget`)를 보고, 「무엇이 눌렸나」를 알려면 `target` 을 본다.** 위임([18번 주제](../18-event-delegation/2-summary.md))은 이 둘이 **갈린다는 것**에 기댄다.

```text
   함수 하나 · 자리 셋 · 호출 셋

   하나(e) ── #안쪽   에 등록  ──▶  this=#안쪽    target=#안쪽   phase 2
          ── #가운데 에 등록  ──▶  this=#가운데  target=#안쪽   phase 3
          ── #바깥   에 등록  ──▶  this=#바깥    target=#안쪽   phase 3

   「어디서 불렸나」 = this / currentTarget        「무엇이 눌렸나」 = target
```

```text
$ python3 wa16b-cdp.py page wa16b-16-same.html | sed -n '7,8p'
나. 열네 리스너가 본 composedPath() — 서로 다른 것의 가짓수 = 1
   #안쪽 #가운데 #바깥 body html document window
(exit 0)
```

- ★ **열네 리스너가 본 `composedPath()` 는 한 가지뿐**이다 — `#안쪽 #가운데 #바깥 body html document window`. **경로는 디스패치 하나에 하나**이고, 어느 자리에서 물어도 같은 배열이다. 그림자 경계가 있어도 이것은 같다([12번 주제](../12-shadow-dom/2-summary.md)의 (14) — `open` 일 때 일곱 줄이 한 글자도 같았다).

```text
$ python3 wa16b-cdp.py page wa16b-16-same.html | sed -n '10,11p'
다. 단계 상수
   Event.NONE=0 · CAPTURING_PHASE=1 · AT_TARGET=2 · BUBBLING_PHASE=3
(exit 0)
```

- **단계 번호는 상수로 박혀 있다** — `NONE` 0 · `CAPTURING_PHASE` 1 · `AT_TARGET` 2 · `BUBBLING_PHASE` 3. `e.eventPhase === Event.AT_TARGET` 처럼 이름으로 견주면 읽기 쉽다.

```text
   eventPhase 네 값 — 언제 무엇인가

   0 NONE              디스패치 밖(시작 전 · 끝난 뒤 — (6))
   1 CAPTURING_PHASE   window 에서 타깃의 부모까지 내려가는 길
   2 AT_TARGET         타깃 자리(capture 리스너도 bubble 리스너도)
   3 BUBBLING_PHASE    타깃의 부모에서 window 까지 올라가는 길(bubbles 일 때만)
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   전파에 관여하는 표면

   등록할 때      addEventListener(type, f, true)            capture 로 단다
                  addEventListener(type, f, { capture: true })
                  addEventListener(type, f)                  bubble 로 단다(기본)

   리스너 안에서  e.target          손님이 내린 층(가장 깊은 요소)
                  e.currentTarget   지금 이 리스너가 달린 자리
                  e.eventPhase      1 CAPTURING · 2 AT_TARGET · 3 BUBBLING (밖에서는 0)
                  e.bubbles         올라오는 길이 있나
                  e.composedPath()  이번 경로 전체(그림자 경계는 12번 주제)

   만들 때        new Event(type, { bubbles: true })         기본은 false
```

### 어디서 헷갈리나

- **`capture: true` 는 「먼저 받는다」가 아니다** — 「**내려가는 길에서 받는다**」다. 타깃에 단 capture 는 **타깃 단계에서** 불린다((3)).
- **`e.target` 과 `this`** — 보통 함수의 `this` 는 **`currentTarget`** 이다((1)).
- **`eventPhase` 2 는 「캡처와 버블 사이」가 아니다** — 타깃 자리에서 불린 **모든** 리스너가 2 다.

## 어디서 틀리나

### 1. 부모에 `focus` 를 bubble 로 단다

**안 불린다.** `focus` 는 `bubbles: false` 다((4)). **capture 로 달거나 `focusin` 을 쓴다.** 에러도 경고도 없다 — 부모 리스너가 **그냥 조용하다.**

### 2. `window` 에 capture 로 `load` 를 달아 그림 로드를 다 잡으려 한다

**`load` 의 경로는 `document` 에서 끊긴다**((5)). `document` 에 capture 로 달아야 한다.

### 3. 타깃에서는 등록 순서대로 불린다고 믿는다

**이 판에서는 capture 무리가 먼저**였다((3)). 옛 설명과 다르다 — **순서에 기대지 말고** 한 리스너 안에서 정한다.

### 4. `new MouseEvent('click')` 으로 부모까지 가는 테스트를 짠다

**`bubbles` 기본값이 `false`** 라 부모가 못 받는다((7)). 진짜 클릭은 받는다 — **테스트와 실제가 반대로 갈린다.**

### 5. `await` 뒤에 `e.currentTarget` 을 읽는다

**`null`** 이다((6)). 리스너 첫 줄에서 받아 둔다.

### 6. 리스너 안에서 타깃을 옮기면 새 부모가 받는다고 믿는다

**옛 조상이 받는다**((8)). 경로는 디스패치 시작 때 굳는다.

### 7. `e.target` 이 리스너를 단 요소라고 믿는다

**가장 깊은 요소**다 — 단추 안의 `<span>` 을 누르면 `e.target` 은 `<span>` 이다. 리스너를 단 자리는 `currentTarget` 이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 경로를 **두 번 훑고**(거꾸로 한 번, 바로 한 번) 단계마다 capture/비capture 를 거르는 것 | **명세**(DOM — dispatch · invoke · inner invoke) |
| **타깃에서 capture 무리가 먼저**인 것 | **명세**(DOM — 타깃 자리가 1차에서 capture 만, 2차에서 나머지만 부른다) · **이 판도 그랬다**((3)) |
| 버블하지 않는 이벤트도 **타깃 자신의 bubble 리스너는 부르는** 것 | **명세**(DOM — 2차에서 `bubbles` 를 보는 것은 타깃이 아닌 자리뿐) |
| `load` 의 경로가 **`document` 에서 끊기는** 것 | **명세**(HTML — `Document` 의 get the parent) |
| 디스패치 뒤 `currentTarget` 이 `null`, `eventPhase` 가 0 | **명세**(DOM — dispatch 의 마지막 단계) |
| 한 디스패치의 `composedPath()` 가 **어느 리스너에서 물어도 같은** 것 | **명세**(DOM — 경로는 디스패치에 하나) · 이 판에서 열네 자리가 **한 가지**였다((9)) |
| 경로가 **시작 때 고정**되고, 리스너 목록은 **자리에 도착할 때** 복사되는 것 | **명세**(DOM — dispatch 가 경로를 먼저 만들고, invoke 가 자리마다 목록을 복사한다) · 이 판도 그랬다((8)) |
| 어느 이벤트가 `bubbles: false` 인가(`focus`·`blur`·`mouseenter`·`load`·`scroll`) | **각 이벤트를 정의한 명세**(UI Events · HTML · CSSOM View) · **이 판에서 `e.bubbles` 로 읽었다**((4)) |
| 글자를 눌러도 `e.target` 이 **요소**인 것 | ★ **히트 테스트는 이 문서가 명세로 확인하지 않았다** — **Chrome 151 의 관찰**로만 적는다((7)) |
| 합성과 진짜의 **순서표가 같은** 것 | ★ **이 판의 관찰**이다. 같았던 것은 **순서**뿐이고 `isTrusted` 는 갈렸다((2)) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 부모에서 자식의 포커스를 받는다 | `focusin`/`focusout` · 또는 `focus` 를 capture 로 | `focus` 를 bubble 로 |
| 부모에서 자식의 마우스 진입을 받는다 | `mouseover` + `relatedTarget` 거르기([18번 주제](../18-event-delegation/2-summary.md)) | `mouseenter` 를 bubble 로 |
| 페이지 안 그림들의 로드를 한 곳에서 | `document` 에 capture 로 `load` | `window` 에 capture 로 `load` |
| 누가 먼저 받아야 한다 | 조상에 capture 로 단다 | 타깃에서의 등록 순서에 기대기 |
| 리스너가 달린 자리를 알아야 한다 | `e.currentTarget`(또는 `function` 의 `this`) | `e.target` |
| 합성 이벤트로 버블을 흉내 낸다 | `{ bubbles: true }` 를 **명시** | 생성자 기본값 |
| 전파를 멈춘다 | [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md) | 리스너를 떼었다 붙였다 |

## 핵심 문장

1. **이벤트 하나는 `window` 에서 타깃으로 내려갔다가 다시 `window` 로 올라온다** — capture 리스너는 내려갈 때, bubble 리스너는 올라올 때 불린다.
2. **`target` 은 한 디스패치 내내 같고 `currentTarget` 만 바뀐다** — 보통 함수의 `this` 는 `currentTarget` 이다.
3. **타깃에서는 capture 도 bubble 도 `eventPhase` 2 이고, capture 무리가 먼저다**(이 판과 현재 명세).
4. **버블하지 않는 이벤트도 내려가는 길은 지난다** — 부모는 capture 로, 또는 버블하는 짝(`focusin`)으로 받는다.
5. **`load` 의 경로는 `document` 에서 끊긴다** — `window` 는 못 받는다.
6. **생성자로 만든 이벤트는 `bubbles: false` 가 기본**이다 — `new MouseEvent('click')` 도 그렇다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 16번)
- [15번 주제](../15-listener-registration/2-summary.md) — 리스너 등록과 해제. **그쪽은 `capture` 가 동일성 키라는 것까지, 여기는 `capture` 가 무엇을 하는지부터**
- [12번 주제](../12-shadow-dom/2-summary.md) — 그림자 경계에서의 재타기팅. **그쪽은 경계가 `e.target` 을 어떻게 바꾸나까지, 여기는 경계 없는 경로의 세 단계까지**
- [14번 주제](../14-dialog-popover-scripting/2-summary.md) — 진짜 입력(CDP) 하네스를 처음 세운 편. 합성 이벤트로 **한 칸도 안 움직인** 자리의 정본
- [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md) — 이 경로를 **어디서 끊나**의 정본
- [18번 주제](../18-event-delegation/2-summary.md) — 버블을 이용해 **조상 하나로 받는** 형태. (4)의 비버블 격자가 그쪽의 「위임이 깨지는 자리」가 된다
- [19번 주제](../19-passive-and-scroll/2-summary.md) — `passive` 가 무엇을 무효로 만드나
- [목록의 **21번 주제**](../21-custom-events/)(커스텀 이벤트) — `CustomEvent` 의 `bubbles`/`composed` 를 **내가 정할 때**의 정본
- JS 갈래 [07번 주제](../../languages/js/syntax/07-this-binding-four-rules/2-summary.md) — `this` 네 규칙. 리스너의 `this` 가 **호스트(DOM)가 정하는 칸**이라는 것

## 용어 풀이

- **경로(event path)** — 디스패치가 시작될 때 타깃에서 부모를 따라 올라가며 만든 목록. 끝나면 비워진다.
- **캡처 단계(capturing phase)** — 경로를 `window` 쪽에서 타깃 쪽으로 훑는 길. `eventPhase` 1.
- **타깃 단계(at target)** — 타깃 자리에서 리스너를 부르는 때. `eventPhase` 2. capture 리스너와 bubble 리스너가 **둘 다** 여기서 불린다.
- **버블 단계(bubbling phase)** — 타깃에서 `window` 쪽으로 올라가는 길. `eventPhase` 3. `bubbles: false` 면 없다.
- **`target`** — 이벤트가 일어난 가장 깊은 노드. 한 디스패치 내내 같다(그림자 경계에서는 [12번 주제](../12-shadow-dom/2-summary.md)).
- **`currentTarget`** — 지금 불리고 있는 리스너가 달린 자리. 디스패치가 끝나면 `null`.
- **`bubbles`** — 올라오는 길이 있나. 생성자 기본값은 `false`.
- **`focusin`/`focusout`** — `focus`/`blur` 의 버블하는 짝.
- **get the parent** — 명세에서 경로를 만들 때 「다음 부모는 누구인가」를 정하는 절차. `Document` 는 `load` 일 때 `null` 을 돌려준다.
- **`isTrusted`** — 브라우저가 사용자 입력으로 만든 이벤트면 `true`, 스크립트가 만든 것이면 `false`.
- **호출 순서 로그** — 리스너마다 한 줄씩 「누가·어느 단계에서·누구 앞에서」를 적는 관측. 이 편의 본체.

## 더 들어가면

- **그림자 경계를 넘는 경로**는 [12번 주제](../12-shadow-dom/2-summary.md)가 이미 쟀다 — `composedPath()` 는 어디서 보든 같고 **`e.target` 만 경계 밖에서 호스트로 바뀐다.** 이 편은 경계 없는 경로만 던졌다.
- **`stopPropagation()` 을 경로의 어디서 부르나**가 곧 「어디까지 가나」다 — [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md).
- **`mouseover` 가 자식 사이를 옮길 때마다 또 나는 것**과 그것을 `relatedTarget` 으로 거르는 것은 [18번 주제](../18-event-delegation/2-summary.md)에서 진짜 마우스로 쟀다.
- **「타깃에서는 등록 순서」가 언제 바뀌었나**는 확인하지 않았다. 이 편은 **지금 명세 본문과 이 판의 결과**만 적는다.
- **포인터 이벤트(`pointerdown` 등)의 경로와 `setPointerCapture`** 는 [목록의 **23번 주제**](../23-pointer-events/) 몫이라 던지지 않았다.
