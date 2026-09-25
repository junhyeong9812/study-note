# html/syntax/08 — 스크립트 로딩: `defer`/`async`/`type=module`/`nomodule`·배치 위치 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The `script` element」](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)·[「Scripts that will execute when the document has finished parsing」](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element:attr-script-defer)·[「document.write()」](https://html.spec.whatwg.org/multipage/dynamic-markup-insertion.html#document.write()) 절. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **「이식성」을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 지원 상태는 **Baseline** 으로 읽는다. `defer` 는 20년 넘었고 `type=module`/`nomodule` 은 2017\~2018 에 자리 잡았다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★ **이 주제의 본체는 창 ② (프로브)다** — 실행 순서는 트리에도 렌더에도 안 나타나고 **로그 배열로만** 보인다. 여기에 이 주제는 **「서버 요청 로그」를 창 하나로 더 쓴다** — 「실행 안 됐다」와 「**받아 오지도 않았다**」가 그것으로만 갈린다. 창 넷의 정의는 [01번](../01-document-skeleton/2-summary.md) 의 「이 갈래의 창」 절에 있다.
> ★★★ **이 주제에는 관찰 한계가 있다** — `--dump-dom` 이 기다려 주는 범위가 곧 이 문서가 볼 수 있는 범위다. 아래 (6) 이 그 한계를 잰다.

**이 판의 Chrome**

```text
===== google-chrome --version =====
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 · 실행 시각 | 판이 오르면 바뀐다 |
| **흔들린다** | **`async` 스크립트의 자리** | 내려받기 경주라 **판마다 바뀐다** — 그래서 **가짓수**로 센다 |
| **안 흔들린다** | `defer`·`type=module`·평범한 스크립트의 **서로 간 순서** | 명세가 정한다 |
| **안 흔들린다** | 각 시점의 `document.readyState` 와 트리의 `data-mark` 개수 | 〃 |
| **안 흔들린다** | `document.write` 의 성공·실패와 콘솔 경고 문구 | 〃 |
| **안 흔들린다** | 모듈이 **몇 번** 평가되나 · 어느 파일이 **요청되나** | 〃 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

## 한눈에 — 쉽게 말하면

**★ 네 조합이 정하는 것은 「언제 받나」가 아니라 「언제 실행하나」와 「순서를 보장하나」 둘이다.**

벽을 쌓는 공사 현장에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 벽돌을 아래부터 쌓는 인부 | **HTML 파서** |
| 쌓다 말고 자재가 올 때까지 **손을 놓는 것** | **평범한 `<script src>`**(파싱을 막는다) |
| 「자재는 지금 부르되 **벽 다 쌓은 뒤** 적어 준 순서대로」 | **`defer`** |
| 「오는 대로 **아무 때나** 끼워 넣어라」 | **`async`** |
| 「나는 `defer` 와 같은데 **새 규격 자재**다」 | **`type="module"`** |
| 「**새 규격을 못 쓰는 현장**에서만 뜯어라」 | **`nomodule`** |
| 벽이 다 섰다고 외치는 것 | **`DOMContentLoaded`** |
| 페인트까지 말랐다고 외치는 것 | **`load`** |

- **평범한 스크립트는 파싱을 막는다.** `<head>` 에 두면 **본문이 아직 하나도 없는** 상태에서 돈다.
- **`defer` 와 `type=module` 은 파싱을 안 막고 `DOMContentLoaded` 앞에서 돈다.** 그래서 **트리가 다 있다.**
- **`async` 만 순서를 보장하지 않는다.** 같은 문서를 40번 돌리면 자리가 **두 가지**로 갈린다.

```text
  문서를 위에서 아래로 읽는 동안 무슨 일이 일어나나

  파싱 시작
    │
    ├─ <script src>            파싱을 멈추고 받아서 바로 실행   ← 트리 0개
    ├─ <script defer src>      받기만 하고 계속 읽는다
    ├─ <script async src>      받기만 하고 계속 읽는다
    ├─ <script type=module>    받기만 하고 계속 읽는다
    │
    ├─ <body> 를 다 읽는다                                    ← 트리 3개
    ├─ </body> 앞의 <script src>   파싱을 멈추고 실행
    │
  파싱 끝
    ├─ defer 들을 문서 순서대로 실행
    ├─ module 들을 문서 순서대로 실행
    ├─ DOMContentLoaded
    │
    ├─ async 는 이 선 어디에든 끼어든다  ★ 유일하게 자리가 안 정해진다
    │
  모든 자원 로드 끝
    └─ load
```

실무에서 이게 터지는 자리는 **분석 스크립트를 `async` 로 붙였는데 전역이 없다고 할 때**다.\
`async` 두 개가 서로를 기다려 주지 않아서 **먼저 온 쪽이 먼저 돈다** — 내가 쓴 순서와 무관하다.\
그리고 더 나쁜 것은 **`document.write` 가 `defer`·`async` 에서 조용히 아무 일도 안 하는 것**이다 — **예외도 안 난다.**

> **파싱 차단(parser-blocking)** — 스크립트를 받아 실행할 때까지 파서가 멈추는 것.\
> 예: `<head>` 의 평범한 `<script src>` 가 느리면 **본문이 한 글자도 안 그려진다.**

> **`DOMContentLoaded`** — HTML 파싱과 `defer`·모듈 실행이 끝났을 때 나는 이벤트.\
> 예: 이미지가 아직 안 왔어도 이 이벤트는 난다.

## 이 주제가 답하려는 질문

1. **네 조합을 한 문서에 섞으면 실행 순서가 어떻게 되나.** 그리고 그 순서 중 **무엇이 보장이고 무엇이 관찰인가.**
2. **배치 위치(`<head>` 대 `</body>` 앞)가 무엇을 바꾸나.**
3. **`defer`/`async` 에서 `document.write` 는 어떻게 되나.** 실패가 어떻게 드러나나.

## 동작 방식

### (1) 창 ② — 네 조합을 한 문서에 섞는다

**언제 쓰나** — 이 주제의 본체. **한 문서에 전부 넣어야** 상대 순서가 보인다.

평범·`defer`·`async`·`type=module`·`nomodule` 과 인라인 둘을 **한 문서**에 담고, 각 스크립트가 **자기 이름 + 그 시점의 트리 노드 수 + `readyState`** 를 로그에 찍게 했다.\
★ `async` 는 자리가 안 정해지므로 **그 파일만 서버가 0.5초 늦게 준다** — 그래야 이 블록이 결정적이 된다.

```text
===== 소스: html05b-order.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>네 조합을 한 문서에 섞는다</title>
<script src="html05b-log.js"></script>
<script src="html05b-classic.js"></script>
<script defer src="html05b-defer.js"></script>
<script async src="html05b-async-slow.js"></script>
<script type="module" src="html05b-module.mjs"></script>
<script nomodule src="html05b-nomodule.js"></script>
<script>window.__mark("인라인(head)");</script>
</head>
<body>
<div data-mark="1">본문 1</div>
<div data-mark="2">본문 2</div>
<div data-mark="3">본문 3</div>
<script src="html05b-bodyend.js"></script>
<script>
window.__mark("인라인(</body> 앞)");
document.addEventListener("DOMContentLoaded", () => window.__mark("DOMContentLoaded"));
window.addEventListener("load", () => {
  window.__mark("load");
  setTimeout(() => {
    window.__mark("setTimeout 0");
    const q = document.createElement("pre");
    q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
    document.body.appendChild(q);
  }, 0);
});
</script>
</body>
</html>
===== dom http://127.0.0.1:18705/html05b-order.html | probe =====
평범(head)              트리의 data-mark = 0   readyState = loading
인라인(head)            트리의 data-mark = 0   readyState = loading
평범(</body> 앞)        트리의 data-mark = 3   readyState = loading
인라인(</body> 앞)      트리의 data-mark = 3   readyState = loading
defer                   트리의 data-mark = 3   readyState = interactive
type=module             트리의 data-mark = 3   readyState = interactive
DOMContentLoaded        트리의 data-mark = 3   readyState = interactive
async(늦게 오는 파일)   트리의 data-mark = 3   readyState = interactive
load                    트리의 data-mark = 3   readyState = complete
setTimeout 0            트리의 data-mark = 3   readyState = complete
(exit 0)
```

```text
   실행 순서                     트리의 data-mark   readyState
   +---------------------------+------------------+---------------+
   | 1  평범(head)              | 0                | loading       |
   | 2  인라인(head)            | 0                | loading       |
   | 3  평범(</body> 앞)        | 3                | loading       |
   | 4  인라인(</body> 앞)      | 3                | loading       |
   | 5  defer                  | 3                | interactive   |
   | 6  type=module            | 3                | interactive   |
   | 7  DOMContentLoaded       | 3                | interactive   |
   | 8  async(늦게 오는 파일)    | 3                | interactive   |
   | 9  load                   | 3                | complete      |
   | 10 setTimeout 0           | 3                | complete      |
   +---------------------------+------------------+---------------+
                              ★ nomodule 은 목록에 없다
```

그림 해설 (한 단계씩):

- **1·2 는 트리의 `data-mark` 가 0 이다.** `<head>` 에서 돌았으므로 **본문이 아직 하나도 없다.** 여기서 `document.querySelector("본문요소")` 를 하면 `null` 이다.
- **3·4 는 3 이다.** `</body>` 앞이라 본문이 다 있다. ★ **배치 위치가 바꾸는 것이 이것**이다 — 실행 시점이 아니라 **그 시점에 트리에 무엇이 있나**.
- **5·6 은 파싱이 끝난 뒤다**(`readyState` 가 `interactive`). `defer` 가 먼저, `type=module` 이 다음 — **문서에 적은 순서 그대로**다.
- **7 `DOMContentLoaded` 가 5·6 뒤다.** ★ **`defer` 와 모듈은 `DOMContentLoaded` 를 기다리게 한다.**
- **8 `async` 가 `DOMContentLoaded` 뒤로 밀렸다** — 이 판에서 그 파일을 0.5초 늦게 줬기 때문이다. **빨리 왔으면 앞쪽 어디든 들어간다**(아래 (2)).
- **`nomodule` 이 목록에 없다.** 모듈을 아는 브라우저는 `nomodule` 붙은 스크립트를 **실행하지 않는다.** ★ 그런데 **「실행만 안 한 것」인지 「받아 오지도 않은 것」인지**는 이 창으로 안 갈린다 — (5) 가 그것을 가른다.

### (2) 창 ② — `async` 만 자리가 안 정해진다

**언제 쓰나** — 「순서를 보장하나」를 물을 때. **한 판만 보면 보장으로 오해한다.**

`async` 파일을 **늦추지 않은 판**을 만들어 **40번** 돌리고, 순서를 **`sort -u` 로 가짓수만** 셌다.

```text
===== for i in $(seq 1 40); do dom http://127.0.0.1:18705/html05b-order-race.html | probe | awk '{printf "%s ", $1}'; echo; done | sort -u | awk '{print "  " $0} END {print "가짓수 = " NR}' =====
  평범(head) 인라인(head) 평범(</body> 인라인(</body> async(빨리 defer type=module DOMContentLoaded load setTimeout 
  평범(head) 인라인(head) 평범(</body> 인라인(</body> defer type=module DOMContentLoaded async(빨리 load setTimeout 
가짓수 = 2
(exit 0)
```

```text
   40판을 돌려 서로 다른 순서가 몇 가지인가

   가짓수 = 2

   ① … 인라인(</body> 앞)  async(빨리)  defer  type=module  DOMContentLoaded …
   ② … 인라인(</body> 앞)  defer  type=module  DOMContentLoaded  async(빨리) …
                                    ↑ async 만 자리를 옮긴다
```

그림 해설:

- **두 가지뿐이고 그 둘의 차이는 `async` 한 줄의 자리다.** 나머지 아홉 줄은 **40판 전부 같은 자리**였다.
- ★★ **「여러 번 돌렸더니 같았다」는 보장이 아니다** — 그래서 **가짓수를 세는 쪽**을 택했다. 가짓수 1 이면 「이 판에서는 안 갈렸다」, 2 이상이면 **「보장이 없다」의 실증**이다.
- **`async` 가 두 자리 다 `DOMContentLoaded` 앞뒤에 걸친다.** 그러므로 **`async` 스크립트 안에서 「DOM 이 다 있다」를 가정할 수 없다.**

두 `async` 를 나란히 두면 **문서 순서를 아예 안 본다.**

```text
===== 소스: html05b-race.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>async 두 개는 문서 순서를 안 본다</title>
<script src="html05b-log.js"></script>
<script async src="html05b-async-slow.js"></script>
<script async src="html05b-async-fast.js"></script>
</head>
<body>
<div data-mark="1">본문</div>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
===== dom http://127.0.0.1:18705/html05b-race.html | probe =====
async(빨리 오는 파일)   트리의 data-mark = 1   readyState = interactive
async(늦게 오는 파일)   트리의 data-mark = 1   readyState = interactive
(exit 0)
```

- 문서에는 **늦게 오는 파일이 먼저** 적혀 있는데 **빨리 온 쪽이 먼저 실행**됐다. `async` 가 보는 것은 **도착 시각**뿐이다.

### (3) 창 ② — `document.write` 는 `defer`/`async` 에서 조용히 죽는다

**언제 쓰나** — 옛 광고·분석 코드를 `defer`/`async` 로 바꿔 달 때.

같은 `document.write` 한 줄을 **평범·`defer`·`async`** 세 스크립트에 넣고, **예외가 나는지**와 **트리에 실제로 들어갔는지**를 따로 읽었다.

```text
===== 소스: html05b-write.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>document.write 와 defer·async</title>
</head>
<body>
<p id="앞">앞</p>
<script src="html05b-write-plain.js"></script>
<script defer src="html05b-write-defer.js"></script>
<script async src="html05b-write-async.js"></script>
<p id="뒤">뒤</p>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const 폭 = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
  const 칸 = (s, n) => s + " ".repeat(Math.max(0, n - 폭(s)));
  const o = [];
  for (const k of ["평범", "defer", "async"]) o.push(칸(k, 8) + " -> " + window.__결과[k]);
  o.push("트리의 <b> 개수 = " + document.querySelectorAll("b").length
         + "   글자 = " + JSON.stringify([...document.querySelectorAll("b")].map(b => b.textContent)));
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
===== dom http://127.0.0.1:18705/html05b-write.html | probe =====
평범     -> 예외 없이 통과
defer    -> 예외 없이 통과
async    -> 예외 없이 통과
트리의 <b> 개수 = 1   글자 = ["평범한 스크립트가 쓴 글"]
(exit 0)
```

```text
   무엇이           예외가 났나        트리에 <b> 가 생겼나
   +---------+------------------+---------------------+
   | 평범     | 안 났다           | 생겼다               |
   | defer   | 안 났다      ★    | 안 생겼다       ★    |
   | async   | 안 났다      ★    | 안 생겼다       ★    |
   +---------+------------------+---------------------+
                  트리의 <b> 개수 = 1
```

★★ **세 줄이 전부 「예외 없이 통과」다.** 「통과했으니 됐겠지」로 읽으면 **두 건의 무음 실패**를 놓친다.\
실제로 일어난 일은 **콘솔에만** 있다.

```text
===== google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr --dump-dom http://127.0.0.1:18705/html05b-write.html 2>&1 >/dev/null | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sort =====
"Failed to execute 'write' on 'Document': It isn't possible to write into a document from an asynchronously-loaded external script unless it is explicitly opened.", source: http://127.0.0.1:18705/html05b-write-async.js (2)
"Failed to execute 'write' on 'Document': It isn't possible to write into a document from an asynchronously-loaded external script unless it is explicitly opened.", source: http://127.0.0.1:18705/html05b-write-defer.js (2)
(exit 0)
```

그림 해설:

- **`defer`·`async` 스크립트의 `document.write` 는 아무 일도 안 한다.** 예외를 던지지 않고 **호출이 무시된다.**
- **경고는 콘솔로만 나온다** — `--enable-logging=stderr` 를 붙여야 보인다. ★ **따로 물어야 보이는 출력**이다.
- **왜 막나** — `defer`/`async` 는 **파싱이 끝난 뒤**에 도는데, 그때 `document.write` 를 허용하면 **이미 만든 문서를 지우고 다시 여는 것**이 된다. 그래서 명세가 **무시**하도록 정했다.
- ★ **이 주제에서 가장 위험한 자리다.** 코드도 그대로, 예외도 없음, 화면만 다름.

### (4) 창 ② — 모듈은 한 번만 평가된다

**언제 쓰나** — 같은 모듈을 여러 군데서 부를 때.

같은 `.mjs` 를 **세 번**(`src` 두 번 + `import` 한 번), 같은 `.js` 를 **두 번** 부르게 했다.

```text
===== 소스: html05b-once.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>모듈은 한 번만 평가된다</title>
</head>
<body>
<script type="module" src="html05b-once.mjs"></script>
<script type="module" src="html05b-once.mjs"></script>
<script type="module">import "./html05b-once.mjs";</script>
<script src="html05b-once.js"></script>
<script src="html05b-once.js"></script>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
===== dom http://127.0.0.1:18705/html05b-once.html | probe =====
html05b-once.js 의 본문이 평가됐다
html05b-once.js 의 본문이 평가됐다
html05b-once.mjs 의 본문이 평가됐다
(exit 0)
```

```text
   같은 파일을 여러 번 불렀을 때 본문이 몇 번 평가되나

   html05b-once.mjs   src 2번 + import 1번  ->  1번  ★
   html05b-once.js    src 2번               ->  2번
```

그림 해설:

- **모듈은 한 번만 평가된다.** 같은 URL 은 **모듈 맵**에 한 번만 올라간다 — 세 번 불러도 본문이 한 번만 돈다.
- **평범한 스크립트는 부른 만큼 돈다.** 두 번 부르면 두 번 돈다.
- ★ **그래서 모듈에서는 「최상위 코드가 초기화」가 성립한다.** 평범한 스크립트에서는 성립하지 않는다.
- ★ **모듈 안의 `import`·라이브 바인딩·순환 의존은 이 주제 밖이다** — JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **42번**·**44번**이 정본이다. 여기는 **마크업이 그 모듈을 어떻게 켜나**까지다.

### (5) 창 ② — 속성이 조용히 무시되는 네 자리

**언제 쓰나** — 「일단 `defer` 를 붙여 두자」 할 때. **붙였다고 먹는 것이 아니다.**

인라인 스크립트에 `defer`·`async` 를 붙이고, `defer async` 와 `type="module" async` 를 함께 준 네 경우를 **한 문서**에 담았다.\
★ 뒤의 두 파일은 **서버가 0.5초 늦게 준다** — 그래야 「`DOMContentLoaded` 앞이냐 뒤냐」로 갈린다(`defer` 면 앞, `async` 면 뒤).

```text
===== 소스: html05b-attr-edge.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>인라인에 붙인 defer·async 와 속성 조합</title>
<script src="html05b-log.js"></script>
<script defer>window.__mark("인라인에 defer");</script>
<script async>window.__mark("인라인에 async");</script>
<script defer async src="html05b-both-slow.js"></script>
<script type="module" async src="html05b-modasync-slow.mjs"></script>
</head>
<body>
<div data-mark="1">본문 1</div>
<div data-mark="2">본문 2</div>
<div data-mark="3">본문 3</div>
<script>
document.addEventListener("DOMContentLoaded", () => window.__mark("DOMContentLoaded"));
window.addEventListener("load", () => {
  window.__mark("load");
  setTimeout(() => {
    const q = document.createElement("pre");
    q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
    document.body.appendChild(q);
  }, 0);
});
</script>
</body>
</html>
===== dom http://127.0.0.1:18705/html05b-attr-edge.html | probe =====
인라인에 defer          트리의 data-mark = 0   readyState = loading
인라인에 async          트리의 data-mark = 0   readyState = loading
DOMContentLoaded        트리의 data-mark = 3   readyState = interactive
defer 와 async 를 함께  트리의 data-mark = 3   readyState = interactive
type=module + async     트리의 data-mark = 3   readyState = interactive
load                    트리의 data-mark = 3   readyState = complete
(exit 0)
```

```text
   무엇                         실행 자리                    읽는 법
   +---------------------------+---------------------------+------------------+
   | 인라인에 defer             | 트리 0개 · loading         | 무시된다 ★        |
   | 인라인에 async             | 트리 0개 · loading         | 무시된다 ★        |
   | DOMContentLoaded          | 트리 3개 · interactive     | 경계선            |
   | defer 와 async 를 함께     | 경계선 뒤                  | async 가 이긴다 ★  |
   | type=module + async       | 경계선 뒤                  | async 가 이긴다 ★  |
   +---------------------------+---------------------------+------------------+
```

그림 해설:

- **인라인에 붙인 `defer`·`async` 는 무시된다.** 파싱 도중 **그 자리에서 바로** 돌았다(트리 0개·`loading`). 두 속성은 **외부 스크립트 전용**이다.
- **`defer async` 를 같이 주면 `async` 가 이긴다.** 0.5초 늦게 온 파일이 **`DOMContentLoaded` 뒤**에 돌았다 — `defer` 였다면 앞이었을 것이다.
- **`type="module"` 에 `async` 를 붙이면 의미가 바뀐다.** 모듈은 기본이 `defer` 처럼인데 이 판에서는 **경계선 뒤**로 갔다.
- ★ **`type="module"` 자체는 인라인에도 먹는다** — (4) 의 세 번째 줄이 인라인 모듈이었고 그 `import` 가 실제로 돌았다. **`defer`/`async` 와 갈린다.**

### (6) 새 창 — 요청 로그로만 갈리는 것

**언제 쓰나** — 「실행이 안 됐다」의 원인을 물을 때. **안 받아 온 것**과 **받아 놓고 안 돈 것**은 창 ② 로 구분되지 않는다.

서버가 남긴 요청 기록을 그대로 읽었다.

```text
===== grep -o '/html05b-[^ ]*' html05b-srv.log | sort | uniq -c =====
     41 /html05b-async-fast.js
      2 /html05b-async-slow.js
      1 /html05b-attr-edge.html
     41 /html05b-bodyend.js
      1 /html05b-both-slow.js
     41 /html05b-classic.js
     41 /html05b-defer.js
     43 /html05b-log.js
      1 /html05b-modasync-slow.mjs
     41 /html05b-module.mjs
      1 /html05b-once.html
      1 /html05b-once.js
      1 /html05b-once.mjs
     40 /html05b-order-race.html
      1 /html05b-order.html
      1 /html05b-race.html
      2 /html05b-write-async.js
      2 /html05b-write-defer.js
      2 /html05b-write-plain.js
      2 /html05b-write.html
(exit 0)
```

```text
   파일                        요청된 횟수
   html05b-log.js              42
   html05b-classic.js          41
   html05b-defer.js            41
   html05b-module.mjs          41
   html05b-async-fast.js       41
   html05b-bodyend.js          41
   html05b-nomodule.js         (목록에 없다)  ★
   html05b-once.mjs            1
   html05b-once.js             1
```

그림 해설:

- **`nomodule` 파일은 한 번도 요청되지 않았다.** 「받아서 안 돌린 것」이 아니라 **아예 안 받아 온 것**이다 — 대역폭을 안 쓴다.
- **같은 모듈을 세 번 불렀는데 요청은 1번이다**(`once.mjs`). 모듈 맵이 URL 단위라 **네트워크도 한 번**이다.
- **같은 평범한 스크립트를 두 번 불렀는데도 요청이 1번이다**(`once.js`). ★ 그런데 **평가는 두 번 됐다**((4)) — **「요청 1번」은 「평가 1번」이 아니다.** 모듈의 「한 번만」은 **평가** 쪽 보장이고, 이쪽은 같은 URL 을 다시 받지 않은 것뿐이다.
- ★★ **이 블록이 없으면 「`nomodule` 이 안 돈다」까지만 말할 수 있다.** 창 하나가 더 필요했던 이유다.

### (7) ★★★ 이 주제의 관찰 한계 — `--dump-dom` 이 어디까지 기다리나

**언제 쓰나** — 이 문서의 **모든 출력**을 읽기 전에. **이 한계 밖의 것은 이 문서가 못 본다.**

`load` 뒤에 마이크로태스크 하나와 `setTimeout` 일곱(0·1·5·10·20·50·200ms)을 걸고, **덤프에 무엇까지 찍히나**를 **세 판** 읽었다.

```text
===== for i in 1 2 3; do dom html05b-wait.html | grep -o 'class="늦게">[^<]*' | sed 's/.*>//' | tr '\n' ' '; echo; done =====
파싱 중 동기 load 마이크로태스크 setTimeout 0 
파싱 중 동기 load 마이크로태스크 setTimeout 0 
파싱 중 동기 load 마이크로태스크 setTimeout 0 
(exit 0)
```

```text
   무엇이                        덤프에 찍혔나
   +--------------------------+--------------+
   | 파싱 중 동기               | 찍힌다        |
   | load                     | 찍힌다        |
   | 마이크로태스크              | 찍힌다        |
   | setTimeout 0             | 찍힌다        |
   | setTimeout 1             | 안 찍힌다 ★   |
   | setTimeout 5 · 10 · 20   | 안 찍힌다     |
   | setTimeout 50 · 200      | 안 찍힌다     |
   +--------------------------+--------------+
        세 판이 한 글자도 같았다
```

그림 해설:

- **`--dump-dom` 은 `load` 와 그 뒤의 마이크로태스크, 그리고 `setTimeout(…, 0)` 까지 기다린다.**
- ★★ **경계는 0 과 1 사이다.** `setTimeout(…, 1)` 부터는 못 기다린다 — 「100ms 는 못 기다린다」보다 훨씬 이르다.
- **그래서 이 갈래의 프로브는 전부 `load` 뒤 `setTimeout(…, 0)` 에서 찍는다.** 그 안에 못 들어오는 것은 **이 도구로 관찰 불가**다.
- ★ **이 한계 때문에 못 잰 것** — 지연 로딩·`requestIdleCallback`·긴 네트워크 대기 뒤의 동작. 이 주제의 `async` 실험이 **0.5초 지연**을 쓸 수 있었던 것은 그 지연이 **`load` 안에 들어가기 때문**이다.
- ★ **`--virtual-time-budget` 으로 늘리지 않는다** — 가상 시간이 먼저 다 흘러 **「아무 일도 안 일어남」이 찍히는** 사고가 이 저장소에 실측으로 남아 있다.

### demo 블록을 두지 않는 이유

★ 이 주제는 **`demo` 블록을 두지 않는다.** `demo` 는 **외부 파일에 기대지 않는 자기완결 블록**이어야 하는데(`render-rules.md`), `defer`·`async`·`type=module`·`nomodule` 은 **전부 외부 스크립트에만 붙는 속성**이다. 인라인 스크립트에 붙이면 **무시된다** — 즉 자기완결 블록으로는 이 주제를 보일 수 없다.\
대신 이 문서의 모든 출력이 **소스 전문과 함께** 실려 있어 그대로 다시 던질 수 있다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 다섯 가지

```html
<script src="a.js"></script>
<script defer src="a.js"></script>
<script async src="a.js"></script>
<script type="module" src="a.mjs"></script>
<script nomodule src="a-legacy.js"></script>
```

### 금지 사례 — 속성이 조용히 무시되는 자리

```html
<script defer>console.log("인라인에 defer 는 무시된다")</script>
<script async>console.log("인라인에 async 도 무시된다")</script>
<script defer async src="a.js"></script>
<script defer type="module" src="a.mjs"></script>
```

- 앞의 둘은 **인라인이라 무시**된다. `defer async` 를 같이 쓰면 **`async` 가 이기고**, `type="module"` 에 `async` 를 붙여도 **`async` 가 이긴다** — 네 경우를 (5) 에서 던져 확인했다.
- `type="module"` 에 `defer` 를 더하는 것은 **아무 일도 안 한다** — 이미 그렇게 동작한다(이 배치에서 따로 던지지는 않았다).
- ★ **`type="module"` 자체는 인라인에도 먹는다.**

### 어디서 헷갈리나

- **`defer` 는 「나중에 받는다」가 아니다.** 받는 것은 바로 시작하고 **실행만 미룬다.**
- **`type="module"` 은 암묵 `defer` 다.** 그런데 `async` 를 붙이면 **`async` 처럼 된다.**
- **`nomodule` 은 「구형 브라우저용」이다.** 오늘 새로 쓸 일이 거의 없다.

## 어디서 틀리나

### 1. `<head>` 의 평범한 스크립트에서 DOM 을 찾는다

**`null` 이다.** (1) 의 첫 줄에서 트리의 노드가 **0개**였다.\
★ 「스크립트를 `</body>` 앞에 두라」는 옛 처방은 **이것 하나를 피하려는 것**이었고, 지금은 `defer` 가 같은 일을 더 잘한다.

### 2. `async` 에 순서를 기대한다

**보장이 없다.** 40판에서 자리가 **두 가지**로 갈렸다.\
★ 「몇 번 돌려 봤는데 항상 같더라」는 근거가 못 된다 — **가짓수를 세라.**

### 3. `document.write` 를 `defer`/`async` 로 옮기고 「통과했다」고 읽는다

**예외가 안 난다.** 그런데 **아무 일도 안 일어난다.**\
★ 이 주제에서 가장 위험한 자리다. **콘솔을 따로 봐야** 드러난다.

### 4. `type="module"` 에 `defer` 를 붙인다

**아무 일도 안 한다.** 이미 그렇게 동작한다.\
★ 반대로 `async` 를 붙이면 **의미가 바뀐다** — 순서 보장을 버린다.

### 5. 「`nomodule` 파일도 어차피 받아 온다」고 본다

**안 받아 온다.** 요청 로그에 **한 줄도 없다**((6)).

### 6. 「모듈을 두 번 부르면 두 번 돈다」고 본다

**한 번만 돈다.** `src` 두 번 + `import` 한 번 = **평가 1회**((4)).\
★ 평범한 스크립트는 **요청이 1번이어도 평가는 2번**이다. 두 수를 섞지 마라.

## 구현 세부사항 대 언어 보장

★ **HTML 은 명세가 오류 복구까지 정한 언어**라 「구현 정의」 칸이 작다. 세 층으로 갈라 적는다.

| 층 | 무엇을 보장하나 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 평범·`defer`·모듈의 **상대 순서** | (1) 의 1\~7 번 줄 |
| **명세(HTML)** | `async` 는 **순서를 보장하지 않는다** | (2) 의 가짓수 2 가 그 실증 |
| **명세(HTML)** | `defer`/`async` 에서 `document.write` 무시 | (3) 의 무음 실패 |
| **명세(HTML)** | `nomodule` 은 **모듈을 아는 브라우저에서 실행하지 않는다** | (1) 에 없는 줄 |
| **명세(HTML/JS)** | 같은 URL 의 모듈은 **한 번만** 평가 | (4) |
| **명세(HTML)** | `defer`/`async` 는 **외부 스크립트에만** · 둘 다 주면 `async` | (5) |
| **구현(Blink)** | 명세 구현 + **안 받아 오는 것** | `nomodule` 파일을 아예 요청하지 않는 것 |
| **구현(Blink)** | 콘솔 경고의 **문구** | (3) 의 경고 문장 |
| **이 판의 관찰** | Chrome 151 이 실제로 뱉은 것 | `async` 의 가짓수 2 · `--dump-dom` 의 경계 |

**도구가 못 보는 것**

- ★★★ **`setTimeout(…, 1)` 이후.** (7) 이 잰 한계다. 이 문서는 **`load` + 마이크로태스크 + `setTimeout(…, 0)`** 까지만 본다.
- **내려받기 시각 자체.** 이 배치는 **실행 순서**만 로그로 찍었고 **언제 요청이 나갔나**는 안 봤다(요청 **횟수**만 봤다).
- **`nomodule` 이 실제로 쓰이는 브라우저.** 모듈을 모르는 엔진이 없어 **그쪽 절반을 못 던졌다.**
- **다른 엔진.** Chrome 하나뿐이라 이식성을 주장할 수 없다. 특히 **`async` 가 갈리는 가짓수는 이 머신·이 서버의 관찰**이다.

## 언제 쓰고 언제 안 쓰나

- **기본은 `defer`** — 파싱을 안 막고 순서가 보장되고 DOM 이 다 있다.
- **`async` 는 「아무것에도 안 기대는 것」에만** — 서로 참조하지 않고 DOM 도 안 보는 분석 스크립트류.
- **`type="module"` 은 그 자체로 `defer`** — 따로 붙일 필요가 없다.
- **`nomodule` 은 오늘 새로 쓰지 않는다** — 받아 오지도 않으니 해롭지는 않지만 쓸 일이 없다.
- **`</body>` 앞 배치는 `defer` 로 대체한다** — 실행 시점은 비슷한데 **받기를 더 일찍 시작**한다.
- **`document.write` 는 쓰지 않는다** — 평범한 스크립트에서만 동작하고, 그 자리가 곧 파싱 차단이다.

## 핵심 문장

1. **네 조합이 정하는 것은 「언제 실행하나」와 「순서를 보장하나」 둘이다.**
2. **평범한 스크립트는 파싱을 막고, `defer`·모듈은 파싱 뒤 `DOMContentLoaded` 앞에서 문서 순서대로 돈다.**
3. **`async` 만 자리가 안 정해진다 — 40판에서 가짓수가 2였다.**
4. **`defer`/`async` 의 `document.write` 는 예외 없이 무시된다. 콘솔에만 남는다.**
5. **`nomodule` 파일은 실행만 안 되는 게 아니라 요청도 안 된다 — 요청 로그로만 갈린다.**
6. **인라인 `<script>` 에 붙인 `defer`·`async` 는 무시되고, `defer async` 는 `async` 가 이긴다.**
7. **`--dump-dom` 은 `setTimeout(…, 0)` 까지만 기다린다. 그것이 이 주제의 관찰 한계다.**

## 관련 자료

- [03번 주제 — 파서와 오류 복구](../03-parser-and-error-recovery/2-summary.md) — **파싱 차단이 왜 파서를 멈추게 하나**는 그쪽의 트리 만들기 절차 위에 선다.
- [01번 주제 — 문서의 뼈대](../01-document-skeleton/2-summary.md) — `<head>` 와 `<body>` 의 경계, 창 넷의 정의.
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **42번**·**44번** — **모듈 안의 `import`/`export`·라이브 바인딩·순환 의존·동적 `import` 는 그쪽이 정본이다.** 여기는 **마크업이 그 모듈을 어떻게 켜나**까지.
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **04번** — `innerHTML` 로 넣은 `<script>` 가 왜 안 도는지는 그쪽 표면이다.
- 목록의 **09번 주제**(스타일시트·리소스 힌트) — **스타일시트가 렌더를 막는 것**과 `preload` 는 그쪽이다. 여기는 **스크립트만**.
- 목록의 **10번 주제**(`template`) — `<template>` 안의 스크립트는 안 돈다.

## 용어 풀이

- **파싱 차단(parser-blocking)** — 스크립트를 받아 실행할 때까지 파서가 멈추는 것.
- **`defer`** — 받기는 지금, 실행은 **파싱이 끝난 뒤 문서 순서대로.** 외부 스크립트에만 먹는다.
- **`async`** — 받기는 지금, 실행은 **받는 대로.** 순서 보장이 없다.
- **`type="module"`** — 모듈로 평가한다. **암묵으로 `defer` 처럼** 동작한다.
- **`nomodule`** — 모듈을 아는 브라우저에서는 **실행하지 않는다**(이 판에서는 **받아 오지도 않았다**).
- **`DOMContentLoaded`** — HTML 파싱과 `defer`·모듈 실행이 끝났을 때 나는 이벤트.
- **`load`** — 이미지·스타일시트까지 모든 자원이 끝났을 때 나는 이벤트.
- **`document.readyState`** — `loading` → `interactive` → `complete` 세 단계.
- **모듈 맵(module map)** — URL 마다 모듈을 한 번만 올려 두는 표. 「한 번만 평가된다」의 근거.
- **`document.write`** — 파싱 중인 문서에 글자를 끼워 넣는 옛 API. 파싱이 끝난 뒤에는 무시된다.

## 더 들어가면

- **왜 `async` 에 순서를 안 주었나** — `async` 의 목적이 「**기다리지 않는 것**」이기 때문이다. 순서를 보장하려면 먼저 온 것을 **붙들고 있어야** 하는데, 그러면 `defer` 와 같아진다.
- **`nomodule` 이 왜 필요했나** — 2017\~2018 무렵 **모듈을 아는 브라우저와 모르는 브라우저가 공존**했다. 모르는 쪽은 `type="module"` 을 **모르는 타입이라 건너뛰고**, 아는 쪽은 `nomodule` 을 건너뛴다 — **한 문서로 두 벌을 배달하는 장치**였다.
- **`document.write` 를 왜 아예 없애지 않았나** — 옛 문서가 그것으로 돌아가기 때문이다. [03번 주제](../03-parser-and-error-recovery/2-summary.md)의 「절대 멈추지 않는다」와 같은 집안의 결정이다. 대신 **위험한 자리에서만 무시**하도록 좁혔다.
