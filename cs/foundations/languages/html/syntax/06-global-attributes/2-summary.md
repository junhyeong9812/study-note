# html/syntax/06 — 전역 속성: `id`/`class`/`title`/`hidden`/`data-*`/`contenteditable`/`translate` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Global attributes」](https://html.spec.whatwg.org/multipage/dom.html#global-attributes)·[「Embedding custom non-visible data」](https://html.spec.whatwg.org/multipage/dom.html#embedding-custom-non-visible-data-with-the-data-*-attributes)·[「Named access on the Window object」](https://html.spec.whatwg.org/multipage/nav-history-apis.html#named-access-on-the-window-object) 절. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **「이식성」을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 지원 상태는 **Baseline** 으로 읽는다. ★ 이 주제에서 **`hidden="until-found"` 와 `contenteditable="plaintext-only"` 둘만 최근 표면**이고 나머지는 20년 넘게 안정돼 있다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★ **이 주제의 본체는 창 ② (프로브)다** — 속성은 **트리에 담긴 이름·값**과 **IDL 프로퍼티가 답하는 값**이 갈리는 자리이고, 그 둘은 직렬화로는 안 보인다. 창 ① 은 「소스의 이름이 트리에서 어떻게 바뀌었나」를 보일 때만 쓴다. 창 넷의 정의는 [01번](../01-document-skeleton/2-summary.md) 의 「이 갈래의 창」 절에 있다.

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
| **흔들린다** | demo 의 높이 픽셀 | 글꼴·창 폭에 달렸다 |
| **안 흔들린다** | **속성 이름과 값 · `attributes` 목록의 순서** | 파싱 알고리즘이 명세에 있다 |
| **안 흔들린다** | `dataset` 키 · `classList` 목록 · `.hidden`/`.translate`/`.contentEditable` 값 | 반영 규칙이 명세에 있다 |
| **안 흔들린다** | 던진 대입의 예외 이름(`SyntaxError`) | 〃 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

## 한눈에 — 쉽게 말하면

**★ 전역 속성은 「어느 요소에나 붙는 스티커」다. 그런데 스티커마다 「붙인 대로 읽히는 것」과 「브라우저가 다시 해석하는 것」이 갈린다.**

이삿짐 상자에 붙이는 스티커에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 어느 상자에나 붙일 수 있는 스티커 | **전역 속성**(global attribute) |
| 집 안에 **하나뿐**이어야 할 이름표 | **`id`** |
| 여러 장 겹쳐 붙이는 분류 스티커 | **`class`** |
| 「열지 마시오」 딱지 | **`hidden`** |
| 상자에 직접 쓴 손글씨 메모 | **`data-*`** |
| 「여기에 덧써도 됩니다」 | **`contenteditable`** |
| 「번역하지 마시오」 | **`translate`** |
| 만져 보면 뜨는 말풍선 | **`title`** |
| 스티커에 적힌 글자 ↔ 짐꾼이 읽은 뜻 | **속성(attribute) ↔ IDL 프로퍼티(property)** |

- **스티커에 뭐라고 썼든 「열지 마시오」 딱지는 딱지다.** `hidden="false"` 도 숨긴다 — **불리언 속성**이다.
- **딱 하나 예외가 있다.** `hidden="until-found"` 만 **다른 처분**을 받는다.
- **손글씨 메모는 이름 규칙이 있다.** `data-Key` 라고 써도 트리에는 `data-key` 로 접힌다.

```text
  내가 쓴 속성                 트리에 담긴 것               IDL 이 답하는 것
  +-------------------+      +-------------------+      +----------------------+
  | hidden            | ==>  | hidden=""         | ==>  | .hidden = true       |
  | hidden="false"    | ==>  | hidden="false"    | ==>  | .hidden = true   ★   |
  | hidden="until-fo" | ==>  | hidden="until-fo" | ==>  | .hidden = "until-fo" |
  | (없음)             | ==>  | (없음)             | ==>  | .hidden = false      |
  +-------------------+      +-------------------+      +----------------------+
       소스                     창 ① 이 보는 것            창 ② 가 보는 것
```

```text
  세 층이 각각 다른 것을 한다

  ① 파서   — 속성 이름을 소문자로 접고, 중복된 이름은 뒤엣것을 버린다
             data-Key -> data-key    CLASS="위" class="아래" -> class="위"
  ② 트리   — 이름과 값을 문자열로 담는다. 모르는 이름도 그냥 담는다
             wat="1"  aria-nope="4"  onbogus="3"  전부 남는다
  ③ IDL    — 정해진 이름만 프로퍼티로 답한다. 그 밖은 통로가 없다
             el.hidden ○   el.dataset.ok ○   el.wat ✕(undefined)
```

실무에서 이게 터지는 자리는 **`data-userId` 를 써 놓고 `dataset.userId` 로 읽을 때**다.\
파서가 `data-userid` 로 접어 버려서 실제 키는 `userid` 다 — 그런데 **에러가 없다.** 그냥 `undefined` 다.

> **전역 속성(global attribute)** — 모든 HTML 요소에 쓸 수 있는 속성.\
> 예: `<div title="설명">` 도 `<td title="설명">` 도 된다.

> **IDL 프로퍼티(IDL property)** — 스크립트에서 `el.hidden` 처럼 읽는 자바스크립트 쪽 이름.\
> 예: 속성은 `contenteditable`(전부 소문자)이고 IDL 은 `contentEditable`(낙타 표기)이다.

## 이 주제가 답하려는 질문

1. **일곱 속성이 각각 무엇을 바꾸나.** 그리고 그 변화가 **어디서 관찰되나**(트리인가 렌더인가 IDL 인가).
2. **「불리언 속성」이라는 말의 정확한 뜻은 무엇인가.** `hidden="until-found"` 는 그 말을 깨뜨리나.
3. **`data-*` 의 이름 규칙은 어느 방향으로 도는가.** 마크업 → `dataset` 과 `dataset` → 마크업이 같은 규칙인가.

## 동작 방식

### (1) 창 ② — `hidden` 은 불리언인데 값 하나가 예외다

**언제 쓰나** — 요소를 감출 때. 그리고 「**값을 `false` 로 주면 안 숨겠지**」라고 생각할 때.

```text
===== 소스: html05b-hidden.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>hidden 의 값들</title>
</head>
<body>
<p id="h1" hidden>속성 이름만</p>
<p id="h2" hidden="">빈 문자열</p>
<p id="h3" hidden="false">false 라고 씀</p>
<p id="h4" hidden="until-found">until-found</p>
<p id="h5" hidden="hide-me">아무 값</p>
<p id="h6">속성이 없다</p>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
for (const id of ["h1","h2","h3","h4","h5","h6"]) {
  const e = document.getElementById(id);
  const s = getComputedStyle(e);
  o.push(id + "  getAttribute = " + pad(JSON.stringify(e.getAttribute("hidden")), 14)
    + " .hidden = " + pad(JSON.stringify(e.hidden), 15)
    + " display = " + pad(s.display, 6)
    + " content-visibility = " + s.contentVisibility);
}
o.push("");
o.push("typeof h1.hidden = " + typeof document.getElementById("h1").hidden
     + "   typeof h4.hidden = " + typeof document.getElementById("h4").hidden);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-hidden.html | nojs =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>hidden 의 값들</title>
</head>
<body>
<p id="h1" hidden="">속성 이름만</p>
<p id="h2" hidden="">빈 문자열</p>
<p id="h3" hidden="false">false 라고 씀</p>
<p id="h4" hidden="until-found">until-found</p>
<p id="h5" hidden="hide-me">아무 값</p>
<p id="h6">속성이 없다</p>
(exit 0)
```

```text
===== 소스: html05b-hidden.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>hidden 의 값들</title>
</head>
<body>
<p id="h1" hidden>속성 이름만</p>
<p id="h2" hidden="">빈 문자열</p>
<p id="h3" hidden="false">false 라고 씀</p>
<p id="h4" hidden="until-found">until-found</p>
<p id="h5" hidden="hide-me">아무 값</p>
<p id="h6">속성이 없다</p>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
for (const id of ["h1","h2","h3","h4","h5","h6"]) {
  const e = document.getElementById(id);
  const s = getComputedStyle(e);
  o.push(id + "  getAttribute = " + pad(JSON.stringify(e.getAttribute("hidden")), 14)
    + " .hidden = " + pad(JSON.stringify(e.hidden), 15)
    + " display = " + pad(s.display, 6)
    + " content-visibility = " + s.contentVisibility);
}
o.push("");
o.push("typeof h1.hidden = " + typeof document.getElementById("h1").hidden
     + "   typeof h4.hidden = " + typeof document.getElementById("h4").hidden);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-hidden.html | probe =====
h1  getAttribute = ""             .hidden = true            display = none   content-visibility = visible
h2  getAttribute = ""             .hidden = true            display = none   content-visibility = visible
h3  getAttribute = "false"        .hidden = true            display = none   content-visibility = visible
h4  getAttribute = "until-found"  .hidden = "until-found"   display = block  content-visibility = hidden
h5  getAttribute = "hide-me"      .hidden = true            display = none   content-visibility = visible
h6  getAttribute = null           .hidden = false           display = block  content-visibility = visible

typeof h1.hidden = boolean   typeof h4.hidden = string
(exit 0)
```

```text
   값              .hidden            display   content-visibility   결과
   +-------------+------------------+---------+--------------------+--------------+
   | (이름만)     | true (boolean)   | none    | visible            | 안 보인다     |
   | ""          | true             | none    | visible            | 안 보인다     |
   | "false"     | true      ★      | none    | visible            | 안 보인다     |
   | "hide-me"   | true             | none    | visible            | 안 보인다     |
   | "until-found"| "until-found" ★ | block   | hidden             | 자리는 있다   |
   | (속성 없음)  | false            | block   | visible            | 보인다       |
   +-------------+------------------+---------+--------------------+--------------+
```

그림 해설:

- **불리언 속성의 뜻은 「있으면 참, 없으면 거짓」이다.** 값은 안 본다 — `hidden="false"` 도 **숨긴다.**
- **트리에는 내가 쓴 값이 그대로 남는다.** 창 ① 이 `hidden="false"` 를 보여 준다. **버려진 것이 아니라 안 읽힌 것**이다.
- **`hidden` 없이 쓴 것은 `hidden=""` 로 직렬화된다** — 창 ① 의 첫 줄이 그렇다. [02번 주제](../02-elements-and-attributes/2-summary.md)의 불리언 속성 규칙 그대로다.
- ★★ **`until-found` 만 갈린다.** `.hidden` 의 **타입이 boolean 에서 string 으로 바뀌고**, 숨기는 방법도 `display: none` 이 아니라 **`content-visibility: hidden`** 이다. 그래서 **상자는 남고 내용만 안 그려진다** — 브라우저의 「페이지에서 찾기」가 이것을 찾아내 펼칠 수 있게 하려는 것이다.
- ★ **그러므로 `hidden` 은 순수한 불리언이 아니라 「열거 값이 하나 얹힌 불리언」이다.**

### (2) 창 ② — `id` 는 전역 이름을 만든다

**언제 쓰나** — `id` 를 짓는 모든 자리. **스크립트가 아직 없어도** 이 일은 일어난다.

```text
===== 소스: html05b-global-id.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>id 가 만드는 전역 이름</title>
</head>
<body>
<p id="인사">하나</p>
<p id="쌍둥이">첫째</p>
<p id="쌍둥이">둘째</p>
<a name="옛앵커">name 으로만 준 이름</a>
<img id="그림" src="a.gif" alt="">
<script>var 내가선언 = "내가 선언한 값";</script>
<p id="내가선언">같은 이름의 요소</p>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
const row = (k, v) => o.push(pad(k, 32) + "= " + v);
row("window.인사 ", String(window.인사));
row("window.인사 === getElementById ", String(window.인사 === document.getElementById("인사")));
row("window.쌍둥이 ", Object.prototype.toString.call(window.쌍둥이) + "  length = " + window.쌍둥이.length);
row("window.옛앵커 ", String(window.옛앵커));
row("window.그림 ", String(window.그림));
row("window.내가선언 ", JSON.stringify(window.내가선언));
row("'인사' in window ", String("인사" in window));
row("Object.keys(window) 에 있나 ", String(Object.keys(window).includes("인사")));
row("window 의 고유 속성인가 ", String(Object.getOwnPropertyDescriptor(window, "인사") !== undefined));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-global-id.html | probe =====
window.인사                     = [object HTMLParagraphElement]
window.인사 === getElementById  = true
window.쌍둥이                   = [object HTMLCollection]  length = 2
window.옛앵커                   = undefined
window.그림                     = [object HTMLImageElement]
window.내가선언                 = "내가 선언한 값"
'인사' in window                = true
Object.keys(window) 에 있나     = false
window 의 고유 속성인가         = false
(exit 0)
```

```text
   마크업                        window 에 생기는 것
   +------------------------+
   | <p id="인사">           | ==>  window.인사 === getElementById("인사")
   +------------------------+
   | <p id="쌍둥이"> x2      | ==>  window.쌍둥이 = HTMLCollection(length 2)
   +------------------------+
   | <a name="옛앵커">       | ==>  window.옛앵커 = undefined   ★ 안 생긴다
   +------------------------+
   | var 내가선언 = "…"      | ==>  내 선언이 이긴다  ★
   | <p id="내가선언">       |
   +------------------------+

   'in' 연산자로는 잡힌다        Object.keys 에는 안 나온다
   ('인사' in window === true)   (고유 속성이 아니다)
```

그림 해설:

- **`id` 를 지으면 그 이름의 전역 변수가 생긴다.** `window.인사` 가 바로 그 요소다 — 스크립트에서 아무것도 안 했는데.
- **중복 `id` 면 요소 하나가 아니라 `HTMLCollection` 이 온다.** 타입이 통째로 바뀐다.
- **`<a name>` 으로는 안 생긴다.** 이름 있는 접근은 `name` 속성에 대해 **`<form>`·`<img>`·`<embed>`·`<object>`·`<iframe>`** 에만 걸린다. `<a>` 는 그 목록에 없다.
- **내가 `var` 로 선언한 이름이 이긴다.** 그래서 「전역 변수가 생긴다」는 **덮어쓰기가 아니라 뒷자리**다.
- ★ **`Object.keys(window)` 에는 안 나오고 `window` 의 고유 속성도 아니다.** `in` 으로만 잡힌다 — 이 이름들은 **프록시처럼 동작하는 별도 객체**에 얹혀 있기 때문이다.
- ★ **그래서 「전역 변수를 쓰자」가 아니라 「이름이 충돌할 수 있다」로 읽는다.** `id="name"`·`id="location"` 같은 이름이 실제로 사고를 만든다.

### (3) 창 ①·② — `data-*` 의 이름은 두 번 바뀐다

**언제 쓰나** — 마크업에 값을 실어 스크립트로 꺼낼 때.

```text
===== 소스: html05b-dataset.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>data-* 의 이름 규칙</title>
</head>
<body>
<p id="d" data-Key="A" data-foo-bar="B" data-사용자="C" data-x1="D" data-="E" data--z="F" data-a-b-c="G">데이터 속성</p>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
const d = document.getElementById("d");
o.push("마크업에 쓴 속성 이름 = " + [...d.attributes].map(a => a.name).join(" "));
o.push("");
o.push("소스의 이름        트리의 이름        dataset 의 키");
const 소스 = ["data-Key","data-foo-bar","data-사용자","data-x1","data-","data--z","data-a-b-c"];
const 트리 = [...d.attributes].map(a => a.name).filter(n => n.startsWith("data-") || n === "data-");
const 키   = Object.keys(d.dataset);
for (let i = 0; i < 소스.length; i++) {
  o.push(pad(소스[i], 19) + pad(트리[i], 19) + JSON.stringify(키[i]) + "  = " + JSON.stringify(d.dataset[키[i]]));
}
o.push("");
o.push("d.dataset.Key = " + JSON.stringify(d.dataset.Key) + "   d.dataset.key = " + JSON.stringify(d.dataset.key));
o.push("");
o.push("쓰는 쪽 — 같은 규칙을 거꾸로 돈다");
const 던짐 = (설명, f) => { try { o.push("  " + pad(설명, 34) + "-> " + f()); } catch (e) { o.push("  " + pad(설명, 34) + "-> " + e.name); } };
던짐('dataset.newCamel = "1"',      () => { d.dataset.newCamel = "1"; return "속성 data-new-camel = " + JSON.stringify(d.getAttribute("data-new-camel")); });
던짐('dataset["has-dash"] = "1"',   () => { d.dataset["has-dash"] = "1"; return "속성 " + JSON.stringify(d.getAttribute("data-has-dash")); });
던짐('dataset["-lead"] = "1"',      () => { d.dataset["-lead"] = "1"; return "속성 " + JSON.stringify(d.getAttribute("data--lead")); });
던짐('setAttribute("data-CamelDirect")', () => { d.setAttribute("data-CamelDirect", "1"); return "트리의 이름 " + [...d.attributes].map(a => a.name).filter(n => n.toLowerCase().includes("camel")).join(" "); });
o.push("");
o.push("최종 dataset 키 = " + Object.keys(d.dataset).map(k => JSON.stringify(k)).join(" "));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-dataset.html | nojs =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>data-* 의 이름 규칙</title>
</head>
<body>
<p id="d" data-key="A" data-foo-bar="B" data-사용자="C" data-x1="D" data-="E" data--z="F" data-a-b-c="G" data-new-camel="1" data-cameldirect="1">데이터 속성</p>
(exit 0)
```

```text
===== 소스: html05b-dataset.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>data-* 의 이름 규칙</title>
</head>
<body>
<p id="d" data-Key="A" data-foo-bar="B" data-사용자="C" data-x1="D" data-="E" data--z="F" data-a-b-c="G">데이터 속성</p>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
const d = document.getElementById("d");
o.push("마크업에 쓴 속성 이름 = " + [...d.attributes].map(a => a.name).join(" "));
o.push("");
o.push("소스의 이름        트리의 이름        dataset 의 키");
const 소스 = ["data-Key","data-foo-bar","data-사용자","data-x1","data-","data--z","data-a-b-c"];
const 트리 = [...d.attributes].map(a => a.name).filter(n => n.startsWith("data-") || n === "data-");
const 키   = Object.keys(d.dataset);
for (let i = 0; i < 소스.length; i++) {
  o.push(pad(소스[i], 19) + pad(트리[i], 19) + JSON.stringify(키[i]) + "  = " + JSON.stringify(d.dataset[키[i]]));
}
o.push("");
o.push("d.dataset.Key = " + JSON.stringify(d.dataset.Key) + "   d.dataset.key = " + JSON.stringify(d.dataset.key));
o.push("");
o.push("쓰는 쪽 — 같은 규칙을 거꾸로 돈다");
const 던짐 = (설명, f) => { try { o.push("  " + pad(설명, 34) + "-> " + f()); } catch (e) { o.push("  " + pad(설명, 34) + "-> " + e.name); } };
던짐('dataset.newCamel = "1"',      () => { d.dataset.newCamel = "1"; return "속성 data-new-camel = " + JSON.stringify(d.getAttribute("data-new-camel")); });
던짐('dataset["has-dash"] = "1"',   () => { d.dataset["has-dash"] = "1"; return "속성 " + JSON.stringify(d.getAttribute("data-has-dash")); });
던짐('dataset["-lead"] = "1"',      () => { d.dataset["-lead"] = "1"; return "속성 " + JSON.stringify(d.getAttribute("data--lead")); });
던짐('setAttribute("data-CamelDirect")', () => { d.setAttribute("data-CamelDirect", "1"); return "트리의 이름 " + [...d.attributes].map(a => a.name).filter(n => n.toLowerCase().includes("camel")).join(" "); });
o.push("");
o.push("최종 dataset 키 = " + Object.keys(d.dataset).map(k => JSON.stringify(k)).join(" "));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-dataset.html | probe =====
마크업에 쓴 속성 이름 = id data-key data-foo-bar data-사용자 data-x1 data- data--z data-a-b-c

소스의 이름        트리의 이름        dataset 의 키
data-Key           data-key           "key"  = "A"
data-foo-bar       data-foo-bar       "fooBar"  = "B"
data-사용자        data-사용자        "사용자"  = "C"
data-x1            data-x1            "x1"  = "D"
data-              data-              ""  = "E"
data--z            data--z            "Z"  = "F"
data-a-b-c         data-a-b-c         "aBC"  = "G"

d.dataset.Key = undefined   d.dataset.key = "A"

쓰는 쪽 — 같은 규칙을 거꾸로 돈다
  dataset.newCamel = "1"            -> 속성 data-new-camel = "1"
  dataset["has-dash"] = "1"         -> SyntaxError
  dataset["-lead"] = "1"            -> SyntaxError
  setAttribute("data-CamelDirect")  -> 트리의 이름 data-new-camel data-cameldirect

최종 dataset 키 = "key" "fooBar" "사용자" "x1" "" "Z" "aBC" "newCamel" "cameldirect"
(exit 0)
```

```text
   소스의 이름        파서              트리의 이름       dataset 의 키
   +----------------+----------+      +---------------+  +------------+
   | data-Key       | 소문자로  | ==>  | data-key      |  | key        |
   | data-foo-bar   | 접는다    | ==>  | data-foo-bar  |  | fooBar     |
   | data-사용자     |          | ==>  | data-사용자    |  | 사용자      |
   | data-x1        |          | ==>  | data-x1       |  | x1         |
   | data-          |          | ==>  | data-         |  | ""         |
   | data--z        |          | ==>  | data--z       |  | Z      ★   |
   | data-a-b-c     |          | ==>  | data-a-b-c    |  | aBC        |
   +----------------+----------+      +---------------+  +------------+
        ①                                   ②                 ③
     대문자가 죽는 곳                                    하이픈+글자 -> 대문자
```

그림 해설:

- **① 파서가 속성 이름을 소문자로 접는다.** 이것은 `data-*` 만의 규칙이 아니라 **HTML 의 모든 속성 이름**에 걸린다([02번 주제](../02-elements-and-attributes/2-summary.md)).
- **③ `dataset` 키는 `-` 다음 글자를 대문자로 올려 만든다.** `data-foo-bar` → `fooBar`.
- ★ **그래서 `data-Key` 를 쓰고 `dataset.Key` 로 읽으면 `undefined` 다.** 대문자는 ① 에서 이미 죽었고 ③ 은 하이픈만 본다. **에러가 없다.**
- ★ **`data--z` 가 `Z` 가 된다.** 빈 조각 + `-z` 라서 규칙이 그대로 적용된다. `data-` 는 키가 **빈 문자열**이다.
- **거꾸로 도는 규칙은 더 엄격하다.** `dataset.newCamel = "1"` 은 `data-new-camel` 을 만들지만, `dataset["has-dash"]` 와 `dataset["-lead"]` 는 **`SyntaxError` 를 던진다.** ★ **읽기는 관대하고 쓰기는 던진다.**
- **`setAttribute("data-CamelDirect")` 는 통과한다** — 그리고 트리에 `data-cameldirect` 로 들어간다. `setAttribute` 도 HTML 요소에서는 이름을 소문자로 접기 때문이다.
- ★ `dataset` 자체의 동작은 **web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 07번이 정본**이다. 여기서는 **마크업에 쓴 이름이 어떻게 되나**까지만 본다.

### (4) 창 ② — `class` 는 공백으로 쪼개진 집합이다

**언제 쓰나** — 클래스를 여러 개 줄 때. 그리고 **템플릿이 문자열을 이어 붙여 공백이 겹칠 때.**

```text
===== 소스: html05b-class.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>class 의 공백과 중복</title>
</head>
<body>
<p id="c1" class="  a   b  a   c  ">공백 여러 개와 중복</p>
<p id="c2" class="">빈 값</p>
<p id="c3" class="Box box">대소문자만 다른 둘</p>
<p id="c4" CLASS="위" class="아래">중복 속성</p>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
for (const id of ["c1","c2","c3","c4"]) {
  const e = document.getElementById(id);
  o.push(id + "  className = " + pad(JSON.stringify(e.className), 22)
    + " classList = " + pad(JSON.stringify([...e.classList]), 20)
    + " length = " + e.classList.length);
}
o.push("");
o.push("c1.classList.contains('a') = " + document.getElementById("c1").classList.contains("a"));
o.push("c1 을 .a 로 잡히나         = " + (document.querySelectorAll("p.a").length) + "개");
o.push("c3 을 .box 로 잡히나       = " + (document.querySelectorAll("p.box").length) + "개  (.Box 는 "
       + document.querySelectorAll("p.Box").length + "개)");
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-class.html | nojs =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>class 의 공백과 중복</title>
</head>
<body>
<p id="c1" class="  a   b  a   c  ">공백 여러 개와 중복</p>
<p id="c2" class="">빈 값</p>
<p id="c3" class="Box box">대소문자만 다른 둘</p>
<p id="c4" class="위">중복 속성</p>
(exit 0)
```

```text
===== 소스: html05b-class.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>class 의 공백과 중복</title>
</head>
<body>
<p id="c1" class="  a   b  a   c  ">공백 여러 개와 중복</p>
<p id="c2" class="">빈 값</p>
<p id="c3" class="Box box">대소문자만 다른 둘</p>
<p id="c4" CLASS="위" class="아래">중복 속성</p>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
for (const id of ["c1","c2","c3","c4"]) {
  const e = document.getElementById(id);
  o.push(id + "  className = " + pad(JSON.stringify(e.className), 22)
    + " classList = " + pad(JSON.stringify([...e.classList]), 20)
    + " length = " + e.classList.length);
}
o.push("");
o.push("c1.classList.contains('a') = " + document.getElementById("c1").classList.contains("a"));
o.push("c1 을 .a 로 잡히나         = " + (document.querySelectorAll("p.a").length) + "개");
o.push("c3 을 .box 로 잡히나       = " + (document.querySelectorAll("p.box").length) + "개  (.Box 는 "
       + document.querySelectorAll("p.Box").length + "개)");
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-class.html | probe =====
c1  className = "  a   b  a   c  "     classList = ["a","b","c"]        length = 3
c2  className = ""                     classList = []                   length = 0
c3  className = "Box box"              classList = ["Box","box"]        length = 2
c4  className = "위"                   classList = ["위"]               length = 1

c1.classList.contains('a') = true
c1 을 .a 로 잡히나         = 1개
c3 을 .box 로 잡히나       = 1개  (.Box 는 1개)
(exit 0)
```

```text
   class="  a   b  a   c  "

   className  = "  a   b  a   c  "     <- 내가 쓴 글자 그대로
        ↓ 공백으로 쪼개고 중복을 버린다
   classList  = ["a", "b", "c"]        <- 3개
        ↓
   p.a 로 잡힌다 (1개)
```

그림 해설:

- **`className` 은 속성 문자열 그대로다.** 앞뒤 공백도 중복도 그대로 들고 있다.
- **`classList` 는 공백으로 쪼개고 중복을 버린 집합이다.** 다섯 자리로 쓴 `a b a c` 가 **3개**가 된다.
- **대소문자를 구분한다.** `class="Box box"` 는 **둘**이고 `.box` 와 `.Box` 가 각각 따로 잡힌다.
- ★ **`CLASS="위" class="아래"` 는 첫째가 이긴다** — 중복 속성은 **뒤엣것이 버려진다**([02번 주제](../02-elements-and-attributes/2-summary.md)). 「나중 것이 이긴다」고 외우면 틀린다.
- ★ `classList` 의 조작 API 는 **web-api 갈래의 07번이 정본**이다.

### (5) 창 ② — `contenteditable` 은 세 값 + 상속이다

**언제 쓰나** — 편집 가능한 영역을 만들 때. 그리고 `translate`·`title` 이 무엇을 바꾸는지 물을 때.

```text
===== 소스: html05b-editable.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>contenteditable·translate·title</title>
</head>
<body>
<div id="e1" contenteditable>이름만</div>
<div id="e2" contenteditable="true">true<span id="e2c">상속되나</span></div>
<div id="e3" contenteditable="false">false</div>
<div id="e4" contenteditable="plaintext-only">plaintext-only</div>
<div id="e5" contenteditable="nope">명세에 없는 값</div>
<div id="e6">속성 없음</div>
<p id="t1" translate="no">no</p>
<p id="t2" translate="yes">yes</p>
<p id="t3" translate="">빈 문자열</p>
<p id="t4" translate="nope">명세에 없는 값</p>
<p id="t5">속성 없음</p>
<abbr id="a1" title="Hypertext Markup Language">HTML</abbr>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
for (const id of ["e1","e2","e2c","e3","e4","e5","e6"]) {
  const e = document.getElementById(id);
  o.push(pad(id, 5) + " getAttribute = " + pad(JSON.stringify(e.getAttribute("contenteditable")), 18)
    + " .contentEditable = " + pad(JSON.stringify(e.contentEditable), 18)
    + " .isContentEditable = " + e.isContentEditable);
}
try { document.getElementById("e6").contentEditable = "bogus"; o.push("e6.contentEditable = 'bogus' 대입 -> 통과"); }
catch (err) { o.push("e6.contentEditable = 'bogus' 대입 -> " + err.name); }
o.push("");
for (const id of ["t1","t2","t3","t4","t5"]) {
  const e = document.getElementById(id);
  o.push(pad(id, 5) + " getAttribute = " + pad(JSON.stringify(e.getAttribute("translate")), 10) + " .translate = " + e.translate);
}
o.push("");
const a1 = document.getElementById("a1");
o.push("a1.title = " + JSON.stringify(a1.title) + "   a1 의 렌더 글자 = " + JSON.stringify(a1.innerText));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-editable.html | probe =====
e1    getAttribute = ""                 .contentEditable = "true"             .isContentEditable = true
e2    getAttribute = "true"             .contentEditable = "true"             .isContentEditable = true
e2c   getAttribute = null               .contentEditable = "inherit"          .isContentEditable = true
e3    getAttribute = "false"            .contentEditable = "false"            .isContentEditable = false
e4    getAttribute = "plaintext-only"   .contentEditable = "plaintext-only"   .isContentEditable = true
e5    getAttribute = "nope"             .contentEditable = "inherit"          .isContentEditable = false
e6    getAttribute = null               .contentEditable = "inherit"          .isContentEditable = false
e6.contentEditable = 'bogus' 대입 -> SyntaxError

t1    getAttribute = "no"       .translate = false
t2    getAttribute = "yes"      .translate = true
t3    getAttribute = ""         .translate = true
t4    getAttribute = "nope"     .translate = true
t5    getAttribute = null       .translate = true

a1.title = "Hypertext Markup Language"   a1 의 렌더 글자 = "HTML"
(exit 0)
```

```text
   contenteditable      .contentEditable      .isContentEditable
   +------------------+--------------------+--------------------+
   | (이름만)          | "true"             | true               |
   | "true"           | "true"             | true               |
   | "false"          | "false"            | false              |
   | "plaintext-only" | "plaintext-only"   | true               |
   | "nope"           | "inherit"      ★   | false              |
   | (속성 없음)       | "inherit"          | 부모를 따라간다 ★   |
   +------------------+--------------------+--------------------+

   <div contenteditable="true">  <span>  </div>
                                   └─ 속성이 없는데 isContentEditable = true
```

그림 해설:

- **세 값은 `true`·`false`·`plaintext-only` 다.** 이름만 쓰면 `true` 와 같다(불리언 속성이 **아니다** — 열거 속성이다).
- **`.contentEditable` 은 속성을, `.isContentEditable` 은 계산 결과를 답한다.** 뒤엣것이 **상속을 반영**한 값이다.
- **명세에 없는 값은 `inherit` 으로 떨어진다.** 「무효한 값의 기본 상태」다 — **에러도 경고도 없다.**
- **`el.contentEditable = "bogus"` 대입은 `SyntaxError` 를 던진다.** ★ **마크업은 조용하고 IDL 은 던진다** — `data-*` 와 같은 모양이다.
- **`translate`** — `no` 만 `false` 고 나머지는 전부 `true` 다. 빈 문자열도, 명세에 없는 값도, 속성이 없는 것도 `true`.
- **`title`** — `.title` 로 글자가 그대로 읽힌다. `innerText` 에는 **안 섞인다**(말풍선은 요소의 글자가 아니다).

★★ **`translate` 와 `title` 은 「못 잰 것」이 있다.** `.translate` 가 `false` 인 것은 봤지만, **번역 엔진이 실제로 그 요소를 건너뛰는지**는 이 환경에서 잴 수단이 없다. `title` 의 **말풍선이 뜨는 것**도 마찬가지다. 「안 돌려 봄」이 아니라 **측정 방법 자체가 없다.**

### (6) 창 ①·② — 알 수 없는 속성은 그냥 남는다

**언제 쓰나** — 오타를 냈을 때, 그리고 프레임워크가 자기 속성을 붙일 때.

```text
===== 소스: html05b-unknown.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>알 수 없는 속성과 알 수 없는 요소</title>
</head>
<body>
<p id="u1" wat="1" data-ok="2" onbogus="3" aria-nope="4" ID2="5">알 수 없는 속성</p>
<wat-element id="u2" mine="6">알 수 없는 요소</wat-element>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
const u1 = document.getElementById("u1");
o.push("u1 트리의 속성 = " + [...u1.attributes].map(a => a.name).join(" "));
for (const n of ["wat","data-ok","onbogus","aria-nope","id2"]) {
  o.push("  " + pad(n, 12) + "getAttribute = " + pad(JSON.stringify(u1.getAttribute(n)), 6)
    + "  el." + pad(n.replace(/-(\w)/g, (m, c) => c.toUpperCase()), 10) + "= " + u1[n.replace(/-(\w)/g, (m, c) => c.toUpperCase())]);
}
o.push("u1.dataset.ok = " + JSON.stringify(u1.dataset.ok) + "   (data-* 만 통로가 있다)");
o.push("");
const u2 = document.getElementById("u2");
o.push("u2.constructor.name = " + u2.constructor.name);
o.push("u2.tagName          = " + u2.tagName + "   localName = " + u2.localName);
o.push("u2 의 속성          = " + [...u2.attributes].map(a => a.name).join(" "));
o.push("u2 의 display       = " + getComputedStyle(u2).display);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-unknown.html | nojs =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>알 수 없는 속성과 알 수 없는 요소</title>
</head>
<body>
<p id="u1" wat="1" data-ok="2" onbogus="3" aria-nope="4" id2="5">알 수 없는 속성</p>
<wat-element id="u2" mine="6">알 수 없는 요소</wat-element>
(exit 0)
```

```text
===== 소스: html05b-unknown.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>알 수 없는 속성과 알 수 없는 요소</title>
</head>
<body>
<p id="u1" wat="1" data-ok="2" onbogus="3" aria-nope="4" ID2="5">알 수 없는 속성</p>
<wat-element id="u2" mine="6">알 수 없는 요소</wat-element>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
const u1 = document.getElementById("u1");
o.push("u1 트리의 속성 = " + [...u1.attributes].map(a => a.name).join(" "));
for (const n of ["wat","data-ok","onbogus","aria-nope","id2"]) {
  o.push("  " + pad(n, 12) + "getAttribute = " + pad(JSON.stringify(u1.getAttribute(n)), 6)
    + "  el." + pad(n.replace(/-(\w)/g, (m, c) => c.toUpperCase()), 10) + "= " + u1[n.replace(/-(\w)/g, (m, c) => c.toUpperCase())]);
}
o.push("u1.dataset.ok = " + JSON.stringify(u1.dataset.ok) + "   (data-* 만 통로가 있다)");
o.push("");
const u2 = document.getElementById("u2");
o.push("u2.constructor.name = " + u2.constructor.name);
o.push("u2.tagName          = " + u2.tagName + "   localName = " + u2.localName);
o.push("u2 의 속성          = " + [...u2.attributes].map(a => a.name).join(" "));
o.push("u2 의 display       = " + getComputedStyle(u2).display);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-unknown.html | probe =====
u1 트리의 속성 = id wat data-ok onbogus aria-nope id2
  wat         getAttribute = "1"     el.wat       = undefined
  data-ok     getAttribute = "2"     el.dataOk    = undefined
  onbogus     getAttribute = "3"     el.onbogus   = undefined
  aria-nope   getAttribute = "4"     el.ariaNope  = undefined
  id2         getAttribute = "5"     el.id2       = undefined
u1.dataset.ok = "2"   (data-* 만 통로가 있다)

u2.constructor.name = HTMLElement
u2.tagName          = WAT-ELEMENT   localName = wat-element
u2 의 속성          = id mine
u2 의 display       = inline
(exit 0)
```

```text
   소스                       트리          IDL
   +------------+           +--------+    +-------------------+
   | wat="1"    |  ==>      | 남는다  |    | el.wat = undefined |
   | onbogus="3"|  ==>      | 남는다  |    | 통로 없음           |
   | aria-nope  |  ==>      | 남는다  |    | 통로 없음           |
   | ID2="5"    |  ==>      | id2    |    | 통로 없음           |
   | data-ok="2"|  ==>      | 남는다  |    | el.dataset.ok ○ ★  |
   +------------+           +--------+    +-------------------+

   <wat-element> ==> HTMLElement · tagName WAT-ELEMENT · display inline
```

그림 해설:

- **트리는 모르는 이름도 담는다.** `getAttribute` 로 전부 읽힌다.
- **IDL 통로는 정해진 이름에만 있다.** `el.wat` 는 `undefined` 다 — **속성은 있는데 프로퍼티가 없다.**
- ★ **`data-*` 만 「내가 지은 이름」에 통로가 열려 있다.** 그것이 `data-*` 가 존재하는 이유다.
- **`ID2` 는 `id2` 로 접힌다** — 이름 접기가 아는 이름만의 규칙이 아님을 보여 준다.
- **알 수 없는 「요소」도 그냥 생긴다.** `HTMLUnknownElement` 가 아니라 **`HTMLElement`** 인 것은 이름에 하이픈이 있어 **커스텀 요소 이름 규칙**을 만족하기 때문이다. `display` 는 `inline` 이다.

### (7) demo — `hidden` 과 `until-found` 는 화면에서 다르게 숨는다

```html demo
<p class="숨김" hidden>hidden 으로 숨긴 문단</p>
<p class="찾기" hidden="until-found">hidden="until-found" 로 숨긴 문단</p>
<p class="보임">안 숨긴 문단</p>
<style>
  p { border: 2px solid #94a3b8; padding: 4px; margin: 4px 0; }
</style>
```

> **보이는 것** — 문단 셋 중 **첫째는 흔적도 없고**, 둘째는 **테두리만 남은 납작한 줄**로 보이며(글자가 안 그려진다), 셋째만 정상으로 보인다. 즉 `until-found` 는 **자리를 차지한 채** 내용만 감춘다.\
> **바꿔 볼 것** — `[hidden]` 에 CSS 로 `display: block` 을 주면 → **첫째가 되살아난다**(`.hidden` 은 여전히 `true` 인데 화면에는 보인다) · 값을 `until-fond` 로 오타 내면 → `until-found` 처럼 납작해지는 게 아니라 **그냥 사라진다**(`display: none`).
>
> *(Chrome 151 headless 실측, 창 폭 780: `hidden` 은 높이 0 · 상자 0개 / `until-found` 는 높이 12 · 상자 1개 / 안 숨긴 것은 높이 36)*

★ 「보이는 것」과 「바꿔 볼 것」의 단언을 **각각 따로 던져** 확인했다 — [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 두 블록이 있다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 일곱 속성의 값 꼴

```html
<div id="유일한이름"
     class="여러 개 공백으로"
     title="말풍선 글자"
     hidden
     data-user-id="42"
     contenteditable="true"
     translate="no">…</div>
```

### 금지 사례 — 값이 조용히 무시되는 자리

```html
<p hidden="false">숨겨진다 — 불리언이라 값을 안 본다</p>
<p data-userId="42">트리에는 data-userid 로 들어간다</p>
<p contenteditable="yes">명세에 없는 값 — inherit 으로 떨어진다</p>
<p translate="false">no 가 아니면 전부 번역 대상이다</p>
<p CLASS="위" class="아래">뒤엣것이 버려진다</p>
```

### 어디서 헷갈리나

- **`hidden` 은 불리언인데 `contenteditable` 은 아니다.** 앞엣것은 값을 안 보고, 뒤엣것은 값이 목록에 있어야 한다.
- **`translate` 의 기본은 `yes` 다.** 「안 쓰면 번역 안 되겠지」가 거꾸로다.
- **속성 이름은 소문자, IDL 은 낙타 표기.** `contenteditable` ↔ `contentEditable`.

## 어디서 틀리나

### 1. `hidden="false"` 로 되살리려 한다

**숨는다.** 불리언 속성은 값을 안 본다 — 없애야 보인다(`removeAttribute` 또는 `el.hidden = false`).

### 2. `data-userId` 를 `dataset.userId` 로 읽는다

**`undefined` 다.** 대문자는 파서가 접어 버렸다.\
★ **에러가 없어서 몇 시간을 다른 데서 찾는다.** 트리를 한 번 찍어 보면 1초에 끝난다.

### 3. `classList` 가 `className` 과 같은 줄 안다

`class="  a   b  a  "` 에서 `className` 은 **원문 그대로**고 `classList` 는 **3개짜리 집합**이다.\
★ 문자열을 이어 붙여 클래스를 만들 때 공백 겹침은 **`classList` 쪽에서는 아무 문제가 아니다** — 그래서 문자열 비교로 검사하면 헛다리를 짚는다.

### 4. 중복 속성에서 「나중 것이 이긴다」고 본다

**첫째가 이긴다.** `CLASS="위" class="아래"` 는 `class="위"` 가 된다.

### 5. `id` 가 전역 이름을 만드는 것을 모르고 쓴다

`id="name"`·`id="top"`·`id="location"` 같은 이름은 **기존 전역과 부딪힌다.**\
★ 반대로 「그러니 `window.버튼` 으로 쓰자」도 안 된다 — `Object.keys(window)` 에도 안 나오고, **같은 이름의 `var` 선언이 이긴다.**

### 6. 알 수 없는 속성을 「버려진다」고 본다

**남는다.** `getAttribute` 로 다 읽힌다. 다만 **IDL 통로가 없을 뿐**이다.\
★ [CSS 갈래](../../../css/syntax/README.md)와 정반대다 — CSS 는 모르는 선언을 **버리고**, HTML 은 **담는다.**

## 구현 세부사항 대 언어 보장

★ **HTML 은 명세가 오류 복구까지 정한 언어**라 「구현 정의」 칸이 작다. 세 층으로 갈라 적는다.

| 층 | 무엇을 보장하나 | 이 주제에서 |
|---|---|---|
| **명세(WHATWG HTML)** | 속성의 뜻·반영 규칙·`data-*` 이름 규칙 | `hidden` 이 불리언인 것 · `dataset` 의 양방향 규칙 · `translate` 의 기본이 `yes` 인 것 |
| **명세(파싱 알고리즘)** | 이름 소문자 접기 · 중복 속성 버리기 | `data-Key` → `data-key` · `CLASS`/`class` 에서 첫째가 남는 것 |
| **구현(Blink)** | 명세 구현 + 숨기는 **방법** | `until-found` 를 `content-visibility: hidden` 으로 구현한 것 |
| **이 판의 관찰** | Chrome 151 이 실제로 뱉은 것 | `display`·`content-visibility` 계산값 · `HTMLCollection` 타입 · `SyntaxError` 이름 |

**도구가 못 보는 것**

- **`translate` 가 실제로 하는 일.** 번역 엔진이 없어 **측정 수단 자체가 없다.** 잰 것은 `.translate` 가 답하는 값까지다.
- **`title` 의 말풍선.** headless 에는 뜰 자리가 없다. 잰 것은 `.title` 문자열과 「`innerText` 에 안 섞인다」까지다.
- **`contenteditable` 의 실제 편집.** 키 입력을 넣지 않았다 — `plaintext-only` 가 서식을 정말 막는지는 **안 던졌다.**
- **다른 엔진.** Chrome 하나뿐이라 이식성을 주장할 수 없다. 특히 **`until-found` 를 `content-visibility` 로 구현한 것은 Blink 의 선택**이고, 명세가 정한 것은 「찾기로 펼 수 있게 감춘다」는 **동작**이다.

## 언제 쓰고 언제 안 쓰나

- **`hidden` 은 CSS 로 이길 수 있다** — 그래서 CSS 프레임워크를 쓰는 문서에서는 `[hidden]` 의 UA 규칙이 **덮여 있을 수 있다.** demo 의 「바꿔 볼 것」이 그 실물이다.
- **`data-*` 는 「스크립트가 읽을 값」에만 쓴다** — 스타일 갈래는 클래스가 먼저다.
- **`id` 는 문서에 하나만** — 유일성은 **강제되지 않는다**([07번 주제](../07-id-and-fragments/2-summary.md)).
- **`translate="no"` 는 코드·상표·사람 이름에** — 기본이 「번역함」이므로 **끄는 쪽을 명시**한다.
- **`contenteditable` 로 편집기를 만들지 않는다** — 이 주제는 「속성이 무엇을 켜나」까지다. 그 위의 선택·입력 API 는 다른 갈래다.

## 핵심 문장

1. **전역 속성은 트리에 담기는 문자열이고, IDL 프로퍼티는 그것을 해석한 값이다. 둘을 갈라 읽어야 한다.**
2. **`hidden` 은 불리언이라 값을 안 본다 — 단 `until-found` 하나만 다른 처분을 받는다.**
3. **`id` 를 지으면 같은 이름의 전역이 생긴다. 중복이면 그 전역이 `HTMLCollection` 으로 바뀐다.**
4. **`data-*` 의 대문자는 파서가 죽인다. 읽기는 관대하고 쓰기는 `SyntaxError` 를 던진다.**
5. **알 수 없는 속성은 버려지지 않고 남는다 — CSS 와 정반대다.**

## 관련 자료

- [02번 주제 — 요소와 속성 문법](../02-elements-and-attributes/2-summary.md) — **불리언 속성·중복 속성·이름 접기의 정본이 그쪽이다.** 여기는 **그 규칙이 일곱 전역 속성에서 어떻게 드러나나**만 본다.
- [01번 주제 — 문서의 뼈대](../01-document-skeleton/2-summary.md) — 창 넷의 정의.
- [07번 주제 — `id` 와 조각 식별자](../07-id-and-fragments/2-summary.md) — **`id` 의 유일성과 URL 쪽 이야기는 그쪽이다.** 여기는 **전역 속성으로서의 `id`** 까지.
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **06번**·**07번** — **속성 대 성질, `dataset`·`classList` 의 API 는 그쪽이 정본이다.** 여기서는 **마크업에 쓴 이름이 어떻게 되나**만 보고 결론만 적었다.
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md)) — `[hidden]` 을 덮는 캐스케이드, 속성 선택자.
- 목록의 **20번 주제**(`lang`·`dir`) — **그쪽도 전역 속성**이지만 양방향 텍스트가 본체라 따로 세웠다.

## 용어 풀이

- **전역 속성(global attribute)** — 모든 HTML 요소에 쓸 수 있는 속성.
- **불리언 속성(boolean attribute)** — 있으면 참, 없으면 거짓. **값을 보지 않는다.** `hidden`·`disabled`·`checked`.
- **열거 속성(enumerated attribute)** — 정해진 값 목록 중 하나를 받는 속성. 목록에 없으면 **기본 상태**로 떨어진다. `contenteditable`·`translate`.
- **IDL 프로퍼티(IDL property)** — 스크립트에서 읽는 이름. 속성과 **이름도 타입도 다를 수 있다.**
- **반영(reflect)** — 속성과 IDL 프로퍼티가 서로 이어져 있는 것. 한쪽을 바꾸면 다른 쪽이 따라간다.
- **`dataset`** — `data-*` 속성을 낙타 표기 키로 보여 주는 통로.
- **`classList`** — `class` 를 공백으로 쪼갠 집합. 중복이 없다.
- **`content-visibility`** — 상자는 남기고 내용만 안 그리게 하는 CSS 속성. Blink 가 `until-found` 를 이것으로 구현했다.
- **이름 있는 접근(named access on Window)** — `id`(와 일부 요소의 `name`)가 `window` 의 이름이 되는 규칙.

## 더 들어가면

- **왜 `hidden` 에 열거 값을 얹었나** — 접힌 아코디언 안의 글자를 브라우저 「페이지에서 찾기」가 찾아내 펼쳐 주게 하려면, **「숨었지만 찾기에는 보이는」 제3의 상태**가 필요했다. `display: none` 으로는 그 상태를 만들 수 없다.
- **`data-*` 가 없던 시절에는** 사람들이 `<div rel="42">` 처럼 **다른 속성을 훔쳐 썼다.** 이 주제의 (6) 이 보여 주듯 트리는 그것도 담아 주므로 **동작은 했다** — 다만 검증기가 막았고 뜻이 충돌했다.
- **이름 있는 접근은 왜 아직 있나** — 1990년대 문서가 `document.폼이름` 으로 돌아가고 있기 때문이다. 03번의 「절대 멈추지 않는다」와 같은 집안의 결정이다.
