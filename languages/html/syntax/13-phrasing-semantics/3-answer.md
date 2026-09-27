# html/syntax/13 — 구절 시맨틱: `strong`/`em`/`b`/`i`/`mark`/`small`/`code`/`kbd`/`samp`/`abbr` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였고 사람이 옮겨 적지 않았다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **이 주제의 본체는 창 ② × 창 ⑦ 의 대조다.** 모양은 창 ② 로, 의미는 창 ⑦ 로만 보인다(A7).
> ★★ **스크린리더가 역할을 받아 무엇을 하는지는 못 본다**(A9).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 짝끼리 스타일 다섯 칸이 전부 같다 — `strong`·`b` 는 700, 고정폭 셋은 13px

**출력**

```text
$ python3 html13b-cdp.py page html13b-13-grid.html
열 요소의 계산 스타일(창 ②)과 접근성 역할(창 ⑦)
요소        weight  style   family      size       background        역할
<strong>  700     normal  sans-serif  16px       rgba(0, 0, 0, 0)  strong
<b>       700     normal  sans-serif  16px       rgba(0, 0, 0, 0)  generic
<em>      400     italic  sans-serif  16px       rgba(0, 0, 0, 0)  emphasis
<i>       400     italic  sans-serif  16px       rgba(0, 0, 0, 0)  generic
<code>    400     normal  monospace   13px       rgba(0, 0, 0, 0)  code
<kbd>     400     normal  monospace   13px       rgba(0, 0, 0, 0)  generic
<samp>    400     normal  monospace   13px       rgba(0, 0, 0, 0)  generic
<mark>    400     normal  sans-serif  16px       rgb(255, 255, 0)  mark
<small>   400     normal  sans-serif  13.3333px  rgba(0, 0, 0, 0)  generic
<abbr>    400     normal  sans-serif  16px       rgba(0, 0, 0, 0)  Abbr
<span>    400     normal  sans-serif  16px       rgba(0, 0, 0, 0)  generic

「똑같아 보이는 짝」끼리 견주면 — 어느 칸이 갈리나
  strong 대 b      갈린 열 = 역할
  em 대 i          갈린 열 = 역할
  code 대 kbd      갈린 열 = 역할
  code 대 samp     갈린 열 = 역할
  kbd 대 samp      갈린 열 없음

스타일 칸 갈림 = 0 / 25 · 역할 칸 갈림 = 4 / 5
갈린 칸 = 4 / 30
(exit 0)
```

**왜 그런가**

- **`<strong>`·`<b>` 둘 다 700** 이다. 명세 UA 스타일시트가 `b, strong { font-weight: bolder; }` **한 줄로 둘을 묶는다** — 부모 400 에서 한 단계 굵게 가서 700 이다.
- **`<em>`·`<i>` 둘 다 `italic`** — `cite, dfn, em, i, var { font-style: italic; }` 한 줄이다.
- **`<code>`·`<kbd>`·`<samp>` 는 `monospace` 에 `13px`** 이다. 명세는 `font-family: monospace` 만 주고, **13px 은 Chrome 의 고정폭 기본 크기**다(구현).
- **`<small>` 은 `13.3333px`** — `font-size: smaller` 로 16 에서 한 단계 아래다.
- **`<mark>` 는 `rgb(255, 255, 0)`** — 명세의 `mark { background: yellow; color: black; }` 이다.

### 2. 갈린 칸 = 4 / 30 — 넷 다 역할 열이다

**출력** — 1번과 같은 실행의 마지막 줄들이다(위 블록). 역할이 **트리 그대로**라는 것은 스크립트 없이 찍은 트리로 확인한다.

```text
$ python3 html13b-cdp.py ax html13b-13-grid.html
RootWebArea    이름='13 보이는 것 대 의미'
  paragraph      이름=''
    strong         이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    emphasis       이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    code           이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    mark           이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    Abbr           이름='월드 와이드 웹'
      StaticText     이름='WWW'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
(exit 0)
```

**왜 그런가**

- **역할이 붙는 것은 `strong`·`emphasis`·`code`·`mark` 넷**이다. **`<b>`·`<i>`·`<kbd>`·`<samp>`·`<small>` 은 `<span>` 과 같은 `generic`** 이다.
- ★★★ **갈린 칸은 30 중 4, 전부 역할 열**이다. 스타일 25칸은 0 이다. **「보이는 것은 같고 의미만 다르다」가 스크립트가 센 숫자 하나로 선다.**
- **`kbd`/`samp` 짝만 0칸** — 둘 다 모양도 역할도 같다. 이 판에서 **둘을 가를 창이 없다.**
- ★ **`<abbr>` 는 `Abbr`** 로 찍혔다. HTML-AAM 은 「**대응 역할 없음**」(계산 역할 `html-abbr`)이라고 적는다 — **Chrome 이 빈자리를 내부 이름으로 채운 것**이다. `<kbd>` 도 HTML-AAM 에서는 「대응 역할 없음」인데 **Chrome 은 `generic` 으로** 채웠다. 같은 「없음」을 구현이 **두 가지로** 채운 셈이다.

### 3. `b` 는 700 → 900 → 900, `small` 은 계속 줄고 `kbd` 는 안 준다

**출력**

```text
$ python3 html13b-cdp.py page html13b-13-more.html | sed -n '1,12p'
(가) 겹쳐 쓰면 — bolder·smaller 는 「더」라서 쌓인다
  #b1   font-weight = 700  역할 = generic
  #b2   font-weight = 900  역할 = generic
  #b3   font-weight = 900  역할 = generic
  #s1   font-weight = 700  역할 = strong
  #s2   font-weight = 900  역할 = strong
  #e1   font-style = italic  역할 = emphasis   level 같은 속성 = {}
  #e2   font-style = italic  역할 = emphasis   level 같은 속성 = {}
  #k1   font-size = 13px      역할 = generic
  #k2   font-size = 13px      역할 = generic
  #m1   font-size = 13.3333px 역할 = generic
  #m2   font-size = 11.1111px 역할 = generic
(exit 0)
```

**왜 그런가**

- ★★ **`bolder` 는 「700」이 아니라 「한 단계 더」다.** 700 안에서 한 단계 더 가면 900 이고, **900 이 끝이라 셋째 겹은 900 에 머문다.**
- **`smaller` 도 「한 단계 아래」라 겹칠수록 준다**(16 → 13.33 → 11.11).
- ★ **`<kbd>` 안의 `<kbd>` 는 13 → 13** 이다. 바깥 `<kbd>` 가 이미 고정폭 기본 크기(13px)로 시작했고, 안쪽은 **같은 고정폭이라 그 크기를 그대로** 받는다.
- ★★ **겹친 수는 역할에 안 나타난다.** 안쪽 `<strong>`·`<em>` 도 `strong`·`emphasis` 그대로이고 **속성은 빈 `{}`** 다. 명세는 「조상 `strong` 의 수가 중요도」·「조상 `em` 의 수가 강세」라고 적는데, **그 수는 트리의 모양으로만 남는다.** `italic` 은 겹쳐도 `italic` 이라 **화면에도 안 보인다.**

### 4. 스타일을 지운 `strong` 은 `strong`, 스타일을 입힌 `span` 은 `generic`

**출력**

```text
$ python3 html13b-cdp.py page html13b-13-more.html | sed -n '14,16p'
(나) 모양과 의미를 엇갈리게 — 스타일을 지운 strong · 스타일을 입힌 span
  #민strong  font-weight = 400  역할 = strong
  #굵span    font-weight = 700  역할 = generic
(exit 0)
```

**왜 그런가**

- ★★★ **역할은 태그가 정하고 CSS 는 역할에 손이 안 닿는다.** 굵기를 400 으로 지워도 `strong`, 굵기를 700 으로 입혀도 `generic` 이다.
- 그래서 「중요한데 굵게 보이면 안 된다」 → **`<strong>` + CSS**, 「굵게만」 → **CSS 만**. 둘을 섞을 이유가 없다.

### 5. `<abbr>` 에서는 이름, `<span>` 에서는 설명 — `title` 이 없으면 밑줄도 없다

**출력**

```text
$ python3 html13b-cdp.py page html13b-13-more.html | sed -n '18,21p'
(다) title 은 무엇이 되나 — 이름인가 설명인가
  #abbr   역할 = Abbr     이름 = "월드 와이드 웹"  설명 = ""   text-decoration = underline dotted
  #span   역할 = generic  이름 = ""          설명 = "월드 와이드 웹"   text-decoration = none solid
  #맨abbr  역할 = Abbr     이름 = ""          설명 = ""   text-decoration = none solid
(exit 0)
```

**왜 그런가**

- ★★ **같은 `title` 이 요소에 따라 다른 칸에 들어갔다.** HTML-AAM 의 `<abbr>`·`<dfn>` 용 `title` 줄은 「플랫폼 API 에서 **이름**에 연결」이고, 일반 `title` 줄은 「이름 **또는** 설명 **또는** 대응 없음 — 이름 계산 절이 정한다」다.
- **`<span>` 은 `generic` 이라 이름을 가질 수 없다** — 그래서 설명으로 갔다. 규칙 전체는 목록의 **43번 주제**다.
- ★ **`title` 없는 `<abbr>` 는 `text-decoration = none`** 이다. UA 스타일시트의 선택자가 `abbr[title]` 이라 **속성이 있어야 점선이 걸린다.**

### 6. 뜻은 「부가 설명」인데 역할은 `generic` 이다

- 명세 — 「`small` 요소는 **깨알 글씨 같은 부가 설명**(side comments such as small print)을 나타낸다」. 면책·경고·법적 제한·저작권이 전형이다. ★ 그리고 「**`em`·`strong` 이 준 강조를 깎지 않는다**」고 따로 적는다.
- ★★ **그 뜻은 역할로 드러나지 않는다** — (1) 에서 `generic` 이었다. HTML-AAM 도 `small` → `generic` 이다. **그 뜻을 지키는 것은 쓰는 사람의 규율뿐**이다 — 어느 창도 「부가 설명이 아닌 곳에 썼다」를 잡지 않는다.
- **겹치면 계속 준다**(A3 — 16 → 13.33 → 11.11). 「조금만 작게」 하려고 겹쳐 쓰면 **글씨가 읽을 수 없을 만큼 작아지는데 아무도 안 막는다.** 크기가 목적이면 CSS 다.

### 7. 창 ② 의 「같다」도 맞는 답이다 — 제5의 상태

- **틀린 답이 아니다.** 창 ② 는 **모양**을 묻는 창이고 모양은 정말로 같다(스타일 25칸 0).
- 같은 질문(「`b` 와 `strong` 은 같은가」)을 창 ⑦ 로 다시 물은 것은 **제5의 상태 — 「같은 질문을 다른 창으로 물었다」다**. 창을 바꾸자 답이 「역할이 다르다」로 바뀌었다. ★ **그래서 「같은가」라는 질문에는 「어느 창으로?」가 붙어야 답이 선다.**
- **창 ①(`--dump-dom`)은 쓴 태그 이름을 그대로 돌려줄 뿐**이다 — 의미를 못 본다(요약 (3)). **창 ③(`innerText`/`textContent`)은 둘 다 태그를 벗긴 글자**라 의미가 한 글자도 안 남는다(요약 (7)).
- **창 ④·⑤·⑥ 은 부적용이다** — 구절 요소는 문서 모드도, 요청도, 렌더 차단도 안 바꾼다. 「재 봤더니 같았다」가 아니라 **잴 것이 없다.**

### 8. 대응은 HTML-AAM, `Abbr`·`13px` 는 구현

- **`strong` → `strong` 역할은 HTML-AAM** 이 정한다(「strong role」). Chrome 의 트리는 **그 구현**이다.
- ★ **`Abbr` 는 구현이다.** HTML-AAM 은 `<abbr>` 에 「No corresponding role」(계산 역할 `html-abbr`)이라고 적는다. **ARIA 에 `Abbr` 라는 역할은 없다** — Chrome 내부 역할 이름이 CDP 로 새어 나온 것이다.
- **`<code>` 의 `13px` 은 구현(설정값)** 이다. 명세 렌더링 절은 `font-family: monospace` 만 기대한다.
- ★ **렌더링 절의 값도 「보장」이라기보다 「기대」다** — 명세가 `expected` 로 적는 권고다. 이 판이 그 권고를 그대로 따랐다는 것이 **관찰**이다.

### 9. 「읽는다」와 「SEO」는 둘 다 이 판에서 못 잰다

- **못 쓴다.** 이 판에 NVDA·VoiceOver·Orca 가 없다. 접근성 트리는 보조 기술의 **입력**이다 — 「`strong` 역할이 넘어간다」까지가 관찰이고 「힘주어 읽는다」는 **그 뒤의 일**이다.
- ★★ **SEO 주장은 「못 잰 것」(제3의 상태)** 이다. 「잴 것이 없다」가 아니다 — 검색 엔진이 무엇을 하는지는 **존재하는 동작인데 이 머신에 그것을 잴 도구가 없다.** 그래서 이 문서는 그 주장을 **한 줄도 하지 않는다.**
- **안 보여 준다.** CDP 는 Chrome 의 **내부 트리**다. HTML-AAM 이 적는 **MSAA·UIA·ATK·AX 의 값**(예: `kbd` 의 「텍스트 속성 `font-family:monospace`」)은 그 아래 층이다.

### 10. 정본 경계

- **구절 콘텐츠 카테고리** — [05번 주제](../05-content-categories-and-models/2-summary.md). 여기는 그 안의 요소들이 **무엇을 뜻하고 무엇에 대응되나**부터.
- **UA 스타일시트의 캐스케이드 자리** — CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **01번**([캐스케이드와 우선순위](../../../css/syntax/01-cascade-and-priority/2-summary.md)).
- **`title` 이 이름/설명 중 어디로 가나의 전체 규칙** — 목록의 **43번 주제**(접근 가능한 이름 계산).
- **다음 편** — [14번 주제](../14-quotation-edits-and-time/2-summary.md) 가 `blockquote`/`q`/`cite`·`ins`/`del`·`time` 을 잇는다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.**\
★★ **보조 기술 없음.** NVDA·VoiceOver·Orca 가 설치돼 있지 않다.

**CDP 하네스 — 새로 짰다.** [11번 주제](../11-sectioning-and-landmarks/3-answer.md)의 덤프기를 뿌리로 삼되 세 가지를 바꿨다.
① **기다림을 시간 상수에서 이벤트로** — 형제 판은 `time.sleep(1.2)` 뒤에 물었다. 이 판은 **`Page.loadEventFired` 를 받은 뒤에** 묻는다.
② **요소 하나의 노드를 따로 받는다**(`page` 모드) — 페이지가 `window.__대상` 에 선택자를 적어 두면 하네스가 요소마다 역할·이름·설명을 받아 `window.__AX` 로 넣어 주고, **표 짜기와 칸 세기는 페이지 스크립트가 한다.** 그래서 「갈린 칸 N / M」을 사람이 안 센다.
③ **무시된(ignored) 노드는 건너뛰되 그 자식은 따라간다** — 형제 판은 역할 이름으로 거르고 있었다.
★ 이 머신의 헤드리스 Chrome 은 **CDP 가 기본으로 열려 있지 않다** — 하네스가 `--remote-debugging-port` 로 직접 띄운다.

```python
# html13b-cdp.py
#!/usr/bin/env python3
"""CDP 로 헤드리스 Chrome 에 붙어 창 ⑦(접근성 트리)을 연다.

사용:
  html13b-cdp.py ax   <url|파일>   접근성 트리 전체를 트리 순서로 찍는다
  html13b-cdp.py page <url|파일>   페이지의 window.__대상 = [[열쇠, 선택자], ...] 마다
                              접근성 노드(역할·이름·설명·무시 여부)를 받아 window.__AX 로 넣고
                              window.__끝() 이 돌려준 문자열을 찍는다(표 짜기·칸 세기는 페이지가 한다)

★ 기다림은 시간 상수가 아니라 이벤트다 — Page.loadEventFired 를 받은 뒤에 묻는다.
★ CDP 포트와 프로필 경로는 실행마다 무작위다 — 출력에는 안 들어간다.
"""
import json, os, random, shutil, subprocess, sys, time, urllib.request
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 19900 + random.randint(10, 89)
PROF = os.path.join(HERE, f".prof-{PORT}")
FLAGS = ["--headless", "--disable-gpu", "--no-sandbox", "--window-size=1000,800",
         "--force-renderer-accessibility", f"--remote-debugging-port={PORT}",
         f"--user-data-dir={PROF}", "about:blank"]


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

    def post(self, method, params=None, sid=None):
        """응답을 안 기다리고 보낸다 — 디버거 대기 중인 새 창은 run 전까지 답을 안 한다."""
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))

    def wait(self, method, sid=None, pred=lambda p: True):
        """이미 받아 둔 이벤트부터 뒤지고, 없으면 올 때까지 막고 기다린다."""
        while True:
            for i, e in enumerate(self.events):
                if e.get("method") == method and (sid is None or e.get("sessionId") == sid) \
                        and pred(e.get("params", {})):
                    return self.events.pop(i).get("params", {})
            self.events.append(json.loads(self.ws.recv()))


def start():
    shutil.rmtree(PROF, ignore_errors=True)
    proc = subprocess.Popen(["google-chrome"] + FLAGS,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(200):          # 브라우저가 CDP 를 열 때까지 — 순서만 기다린다(값에는 안 들어간다)
        try:
            v = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version"))
            return proc, Cdp(v["webSocketDebuggerUrl"])
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("CDP 가 안 열렸다")


def open_page(c, url):
    tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable"):
        c.send(m, sid=sid)
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)
    return sid


def evaluate(c, sid, expr):
    r = c.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True,
                                    "returnByValue": True}, sid)
    if "exceptionDetails" in r:
        d = r["exceptionDetails"]
        return "«예외 " + (d.get("exception", {}).get("description") or d.get("text", "?")) + "»"
    return r.get("result", {}).get("value")


def val(node, key):
    return (node.get(key) or {}).get("value", "")


def ax_of(c, sid, selector):
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    nid = c.send("DOM.querySelector", {"nodeId": root, "selector": selector}, sid)["nodeId"]
    if not nid:
        return {"없음": True}
    nodes = c.send("Accessibility.getPartialAXTree",
                   {"nodeId": nid, "fetchRelatives": True}, sid)["nodes"]
    n = next(x for x in nodes if x.get("backendDOMNodeId") and
             x["backendDOMNodeId"] == backend(c, sid, nid))
    kids = [x for x in nodes if x.get("parentId") == n["nodeId"]]
    props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])}
    return {"역할": val(n, "role"), "이름": val(n, "name"), "설명": val(n, "description"),
            "무시": bool(n.get("ignored")), "속성": props,
            "표지": [val(x, "name") for x in kids if val(x, "role") == "ListMarker"]}


def backend(c, sid, nid):
    return c.send("DOM.describeNode", {"nodeId": nid}, sid)["node"]["backendNodeId"]


def dump_tree(c, sid):
    nodes = c.send("Accessibility.getFullAXTree", {}, sid)["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    SKIP = {"InlineTextBox"}

    def walk(n, d):
        role = val(n, "role")
        ignored = n.get("ignored")
        if role not in SKIP and not ignored:
            name = val(n, "name")
            props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])
                     if p["name"] == "level" or (p["name"] == "url" and role == "link")}
            extra = " ".join(f"{k}={v}" for k, v in props.items())
            print(f"{'  ' * d}{role:14} 이름={name!r} {extra}".rstrip())
            d += 1
        for ch in n.get("childIds", []):
            if ch in by:
                walk(by[ch], d)

    for n in nodes:
        if not n.get("parentId"):
            walk(n, 0)


def main():
    mode, url = sys.argv[1], sys.argv[2]
    if "://" not in url:
        url = "file://" + os.path.abspath(url)
    proc, c = start()
    try:
        sid = open_page(c, url)
        if mode == "ax":
            dump_tree(c, sid)
        elif mode == "page":
            targets = evaluate(c, sid, "JSON.stringify(window.__대상 || [])")
            ax = {k: ax_of(c, sid, s) for k, s in json.loads(targets)}
            evaluate(c, sid, "window.__AX = " + json.dumps(ax, ensure_ascii=False))
            print(evaluate(c, sid, "window.__끝()"))
        else:
            sys.exit("모드는 ax | page")
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(PROF, ignore_errors=True)


if __name__ == "__main__":
    main()
```

**캡처 조립기** — 이 배치(13\~16)가 공유한다. 블록마다 **한 번만 돌려 받아 둔 뒤** 자르는 필터를 건다(파이프를 크롬에 물리지 않는다 — 규칙 19-A).

```bash
# capture.sh
#!/usr/bin/env bash
# html13b 묶음(HTML 13~16) — 문서에 실을 블록을 전부 파일로 받는다.
#   사용: ./capture.sh [출력디렉토리]    (기본 blocks)
# ★ 출력 디렉토리를 첫머리에서 절대경로로 정규화한다(규칙 25).
# ★ set -o pipefail — 없으면 파이프 뒤 명령의 종료 코드가 기록된다.
# ★ 자르는 명령은 배너에 적되 실행에는 파이프를 물리지 않는다 — 전부 받아 둔 뒤 필터를 건다.
# ★ grep -c 를 블록의 마지막 명령으로 두지 않는다(0건이면 exit 1).
# ★ 표준 출력만 싣는다 — 표준 오류는 버린다(규칙 18).
set -o pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${1:-blocks}"
case $OUT_DIR in /*) ;; *) OUT_DIR="$HERE/$OUT_DIR" ;; esac
SRC="$HERE/src"
RAW="$OUT_DIR/.raw"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR" "$RAW"
cd "$SRC" || exit 1

CH="google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800"
MARK="sed -n '/^--OUT\$/,/^OUT--\$/{//!p}'"

run() {  # run <열쇠> <명령문자열> — 한 번만 돌려 표준 출력과 종료 코드를 받아 둔다
  local key="$1" cmd="$2"
  if [ ! -f "$RAW/$key.rc" ]; then
    eval "$cmd" > "$RAW/$key.out" 2>/dev/null
    printf '%s' "$?" > "$RAW/$key.rc"
  fi
}

# 출력 블록 — 코드펜스째 뱉는다. 배너 = 실제로 던진 명령 + (있으면) 자르는 필터.
out_block() {  # out_block <블록이름> <열쇠> <배너명령> <명령> [필터]
  local name="$1" key="$2" banner="$3" cmd="$4" pipe="$5" rc
  run "$key" "$cmd"
  rc="$(cat "$RAW/$key.rc")"
  {
    printf '```text\n'
    if [ -n "$pipe" ]; then
      printf '$ %s | %s\n' "$banner" "$pipe"
      eval "cat '$RAW/$key.out' | $pipe"
    else
      printf '$ %s\n' "$banner"
      cat "$RAW/$key.out"
    fi
    printf '(exit %s)\n' "$rc"
    printf '```\n'
  } > "$OUT_DIR/$name.txt"
}

dom()  { out_block "$1" "dom-$2" "$CH --dump-dom $2 2>/dev/null" "$CH --dump-dom $2" "$3"; }
cdp()  { out_block "$1" "cdp-$2-$3" "python3 html13b-cdp.py $2 $3" "python3 html13b-cdp.py $2 $3" "$4"; }
link() { local k="${3:-}"; out_block "$1" "link-$2${k:+-$(basename "$k")}" "python3 html13b-link.py $2${k:+ $k}" \
          "python3 html13b-link.py $2${k:+ $k}" "$4"; }

# 소스 삽입용 블록 — 원고의 ```html 펜스 안에 들어가므로 펜스로 감싸지 않는다.
# 배너는 여기서만 찍는다(basename — 규칙 28). 원고에 손으로 쓰면 이중 배너가 된다.
src_html() { { printf '<!-- %s -->\n' "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_py()   { { printf '# %s\n'        "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_sh()   { { printf '# %s\n'        "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }

out_block ver ver "google-chrome --version" "google-chrome --version"

# ------------------------------------------------------------ 13 구절 시맨틱
src_html 13-grid-src     html13b-13-grid.html
cdp      13-grid-out     page html13b-13-grid.html
cdp      13-grid-ax      ax   html13b-13-grid.html
dom      13-grid-dom     html13b-13-grid.html "sed -n '/^<p>\$/,/^<\/p>\$/p'"
src_html 13-more-src     html13b-13-more.html
cdp      13-more-a       page html13b-13-more.html "sed -n '1,12p'"
cdp      13-more-b       page html13b-13-more.html "sed -n '14,16p'"
cdp      13-more-c       page html13b-13-more.html "sed -n '18,21p'"
cdp      13-more-d       page html13b-13-more.html "sed -n '23,25p'"
src_html 13-demo-src     html13b-13-demo.html
src_html 13-democheck-src html13b-13-democheck.html
dom      13-democheck-out html13b-13-democheck.html "$MARK"

# ------------------------------------------------------------ 14 인용·편집·시각
src_html 14-q-src        html13b-14-q.html
cdp      14-q-a          page html13b-14-q.html "sed -n '1,13p'"
cdp      14-q-b          page html13b-14-q.html "sed -n '15,24p'"
cdp      14-q-ax         ax   html13b-14-q.html
dom      14-q-dom        html13b-14-q.html "grep '^<p id='"
src_html 14-cite-src     html13b-14-cite.html
cdp      14-cite-a       page html13b-14-cite.html "sed -n '1,10p'"
cdp      14-cite-b       page html13b-14-cite.html "sed -n '12,23p'"
cdp      14-cite-ax      ax   html13b-14-cite.html
src_html 14-time-src     html13b-14-time.html
cdp      14-time-out     page html13b-14-time.html
out_block 14-time-console console-14-time \
  "echo \"콘솔 줄 수 = \$($CH --enable-logging=stderr --dump-dom html13b-14-time.html 2>&1 >/dev/null | grep -c ':CONSOLE:')\"" \
  "echo \"콘솔 줄 수 = \$($CH --enable-logging=stderr --dump-dom html13b-14-time.html 2>&1 >/dev/null | grep -c ':CONSOLE:')\""
src_html 14-double-src   html13b-14-double.html
cdp      14-double-out   page html13b-14-double.html
cdp      14-double-ax    ax   html13b-14-double.html
src_html 14-demo-src     html13b-14-demo.html
cdp      14-demo-ax      ax   html13b-14-demo.html

# ------------------------------------------------------------ 15 목록
src_html 15-num-src      html13b-15-num.html
cdp      15-num-a        page html13b-15-num.html "sed -n '1,13p'"
cdp      15-num-b        page html13b-15-num.html "sed -n '15,17p'"
src_html 15-tree-src     html13b-15-tree.html
dom      15-tree-dom     html13b-15-tree.html
cdp      15-tree-ax      ax   html13b-15-tree.html
src_html 15-demo-src     html13b-15-demo.html
cdp      15-demo-ax      ax   html13b-15-demo.html
src_html 15-democheck-src html13b-15-democheck.html
cdp      15-democheck-ax ax   html13b-15-democheck.html

# ------------------------------------------------------------ 16 링크
src_html 16-href-src     d/html13b-16-href.html
link     16-href-a       page d/html13b-16-href.html "sed -n '1,18p'"
link     16-href-b       page d/html13b-16-href.html "sed -n '20,21p'"
link     16-href-c       page d/html13b-16-href.html "sed -n '23,29p'"
link     16-href-log     page d/html13b-16-href.html "sed -n '30,\$p'"
src_html 16-rel-src      html13b-16-rel.html
src_html 16-dest-src     html13b-16-dest.html
link     16-rel-log      rel "" "sed -n '1,39p'"
link     16-rel-grid     rel "" "sed -n '41,\$p'"
src_html 16-dl-src       html13b-16-dl.html
link     16-dl-out       download
link     16-dl-ax        ax html13b-16-dl.html

# ------------------------------------------------------------ 하네스 (3-answer 실행 검증)
src_py   cdp-py          html13b-cdp.py
src_py   link-py         html13b-link.py
src_sh   capture-sh      ../capture.sh
```

**demo 블록** — [2-summary.md](2-summary.md) 의 `demo` 를 **같은 마크업 + 측정 프로브**로 던졌다.

```html
<!-- html13b-13-democheck.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 13 검증</title>
<body>
<p><b>굵은 글씨</b> · <strong>굵은 글씨</strong></p>
<p><i>기울인 글씨</i> · <em>기울인 글씨</em></p>
<p><kbd>Ctrl+C</kbd> · <samp>Ctrl+C</samp> · <code>Ctrl+C</code></p>
<script>
const O = ["창 폭 = " + window.innerWidth];
for (const e of document.querySelectorAll("b, strong, i, em, kbd, samp, code")) {
  const r = e.getBoundingClientRect(), s = getComputedStyle(e);
  O.push(("<" + e.localName + ">").padEnd(9) + "상자 = " + (r.width.toFixed(2) + " x " + r.height.toFixed(2)).padEnd(16)
    + "font = " + s.fontWeight + " " + s.fontStyle + " " + s.fontSize + " " + s.fontFamily);
}
document.body.appendChild(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html13b-13-democheck.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
창 폭 = 1000
<b>      상자 = 63.38 x 24.00   font = 700 normal 16px "Noto Sans CJK KR"
<strong> 상자 = 63.38 x 24.00   font = 700 normal 16px "Noto Sans CJK KR"
<i>      상자 = 78.09 x 24.00   font = 400 italic 16px "Noto Sans CJK KR"
<em>     상자 = 78.09 x 24.00   font = 400 italic 16px "Noto Sans CJK KR"
<kbd>    상자 = 39.00 x 19.00   font = 400 normal 13px monospace
<samp>   상자 = 39.00 x 19.00   font = 400 normal 13px monospace
<code>   상자 = 39.00 x 19.00   font = 400 normal 13px monospace
(exit 0)
```

- **짝끼리 상자 크기가 소수 둘째 자리까지 같다.** 「바꿔 볼 것」의 단언(굵기를 지워도 `strong` 이 남는다)은 요약 (5)·A4 가 던진 것이다.
- ★ 이 블록의 **상자 크기와 글꼴 이름은 머신 사이에서 흔들린다**(설치된 글꼴). 같은 머신에서는 세 판이 같았다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **열 요소 격자**(창 ② + 창 ⑦ + 갈린 칸 집계) | 3 | 동작 방식 (1) · A1 · A2 |
| **같은 파일의 접근성 트리 전체** | 3 | 동작 방식 (2) · A2 |
| **같은 파일의 `--dump-dom`** | 3 | 동작 방식 (3) · A7 |
| **겹치기·엇갈리기·`title`·창 ③** | 3 | 동작 방식 (4)\~(7) · A3\~A5 |
| **demo 검증** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `<abbr>` 의 역할 이름 | **`Abbr`**(내부 이름) | HTML-AAM 은 「대응 없음」 — 구현이 채운 이름이라 판마다 다를 수 있다 |
| `<kbd>` 의 역할 | **`generic`** | 〃 |
| 고정폭 기본 크기 | **13px** | 브라우저 설정값이다 |
| UA 스타일시트의 `bolder`·`smaller`·`italic`·`yellow` | 명세 기대값 그대로 | 렌더링 절은 권고다 |
| `generic` 의 `title` → 설명 | 그대로 | 이름 계산 구현 |

**안 돌려 본 것** — ① **Firefox·Safari 의 역할 대응**(엔진이 없다). ② **`role` 속성으로 역할을 덮어쓴 경우**(`<b role="strong">`) — 목록의 **42번 주제**가 정본이다. ③ **`<dfn>`·`<var>`·`<u>`·`<s>`** — 이 주제의 열 요소 밖이다. 탐색 중 한 번 찍어 본 트리에서 `<s>` 가 **`deletion`** 으로, `<dfn>` 이 **`term`** 으로 나왔으나(HTML-AAM 과 같다) 캡처 블록으로 싣지 않았으므로 **본문 근거로 쓰지 않는다.**

**못 잰 것**(「안 돌려 본 것」과 다르다) — ① **스크린리더의 발화 전부**(A9). ② **검색 엔진의 처리**(A9) — 이 머신에 그것을 잴 도구가 없다. ③ **플랫폼 접근성 API 층**(MSAA·UIA·ATK·AX) — CDP 는 그 위의 내부 트리까지다.

**부적용인 창** — **창 ④(`compatMode`) · 창 ⑤(요청 로그) · 창 ⑥(`renderBlockingStatus`).** 구절 요소는 문서 모드·요청·렌더 차단 어느 것도 바꾸지 않는다 — **잴 것이 없다.**

## 용어 풀이

- **접근성 역할(role)** — 보조 기술에게 넘기는 「이 조각은 무엇이다」라는 이름표.
- **`generic`** — 뜻 없는 묶음의 역할. 이름을 가질 수 없다.
- **HTML-AAM** — HTML 요소·속성의 역할·플랫폼 API 대응을 정한 W3C 명세.
- **`bolder` / `smaller`** — 부모 값에서 한 단계 굵게/작게. 겹치면 쌓인다.
- **제5의 상태** — 같은 질문을 **다른 창으로 물어** 답을 얻은 것. 이 주제에서는 「같은가」를 창 ② 대신 창 ⑦ 로 물었다.
- **제3의 상태(못 잰 것)** — 존재하는 동작인데 잴 도구가 없는 것. 이 주제의 스크린리더·검색 엔진이 그렇다.
