# html/syntax/06 — 전역 속성: `id`/`class`/`title`/`hidden`/`data-*`/`contenteditable`/`translate` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★ **이 주제의 본체는 창 ② (프로브)다.** 창 ① 은 「소스의 이름이 트리에서 어떻게 바뀌었나」를 보일 때만 쓴다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 다섯은 숨고 `until-found` 하나만 자리를 남긴다

**출력** (Chrome 151 headless)

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

**왜 그런가**

- **`hidden` 은 불리언 속성이다** — **있으면 참**이고 값은 안 본다. 그래서 `hidden="false"`·`hidden="hide-me"` 도 `.hidden` 이 `true` 이고 `display` 가 `none` 이다.
- **`until-found` 하나만 갈린다.** `.hidden` 의 **타입이 boolean 에서 string 으로 바뀌고**, `display` 는 `block` 인 채 **`content-visibility` 가 `hidden`** 이 된다. **상자는 남고 내용만 안 그려진다.**
- **트리에는 내가 쓴 값이 그대로 남는다.** 창 ① 이 `hidden="false"` 를 보여 준다 — **버려진 것이 아니라 안 읽힌 것**이다.
- **첫째 문단은 `hidden=""` 로 직렬화된다.** 불리언 속성을 이름만 써도 트리에는 **빈 문자열 값**으로 담긴다([02번 주제](../02-elements-and-attributes/3-answer.md)).
- ★ 마지막 줄이 이 실험의 핵심이다 — **`typeof h1.hidden = boolean` 인데 `typeof h4.hidden = string`.** 한 프로퍼티가 값에 따라 타입을 바꾼다.

### 2. 같은 이름의 전역이 생긴다 — 중복이면 타입까지 바뀐다

**출력**

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

**왜 그런가**

- **`id` 를 지으면 `window` 에 그 이름의 접근이 생긴다.** `window.인사 === document.getElementById("인사")` 가 `true` 다. 스크립트가 아무것도 안 했는데.
- **같은 이름이 둘이면 `HTMLCollection` 이 온다**(`length = 2`). **타입이 통째로 바뀐다** — 요소 하나를 기대한 코드가 여기서 깨진다.
- **`<a name="옛앵커">` 는 같은 일을 하지 않는다**(`undefined`). 이름 있는 접근이 `name` 을 보는 것은 **`<form>`·`<img>`·`<embed>`·`<object>`·`<iframe>`** 뿐이고 `<a>` 는 그 목록에 없다. ★ 다만 `<a name>` 이 **조각 식별자로는 아직 먹는다**([07번 주제](../07-id-and-fragments/3-answer.md)) — **두 규칙이 다르다.**
- **`var 내가선언` 이 이긴다.** 같은 이름의 전역 변수를 선언하면 그 값이 나온다. 그러니 이 이름들은 **덮어쓰기가 아니라 뒷자리**다.
- **`Object.keys(window)` 에 없고 고유 속성도 아닌데 `in` 으로는 잡힌다.** 이 이름들은 `window` 자신이 아니라 그 **프로토타입 사슬에 있는 별도 객체**(`WindowProperties`)에 얹혀 있기 때문이다. 그래서 **열거되지 않는다.**
- ★ **읽는 법** — 「전역 변수를 공짜로 얻었다」가 아니라 「**내 `id` 가 전역 이름과 부딪힐 수 있다**」로 읽는다.

### 3. 대문자는 파서가 죽이고, `dataset` 은 하이픈만 본다

**출력**

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

**왜 그런가**

| 소스 | 트리 | `dataset` 키 | 왜 |
|---|---|---|---|
| `data-Key` | `data-key` | `key` | **파서가 이름을 소문자로 접는다** |
| `data-foo-bar` | `data-foo-bar` | `fooBar` | `-` 다음 글자를 대문자로 |
| `data-사용자` | `data-사용자` | `사용자` | 한글은 접을 대문자가 없다 |
| `data-x1` | `data-x1` | `x1` | 그대로 |
| `data-` | `data-` | `""` | 빈 이름도 키가 된다 |
| `data--z` | `data--z` | `Z` | 빈 조각 + `-z` → 대문자 |
| `data-a-b-c` | `data-a-b-c` | `aBC` | 하이픈 둘이 각각 올린다 |

- **단계는 둘이다.** ① 파서가 **속성 이름 전체를 소문자로** 접고(이것은 `data-*` 만의 규칙이 아니다), ② `dataset` 이 **`data-` 를 떼고 `-` 다음 글자를 올린다.**
- **대문자가 죽는 곳은 ①** 이다. 그래서 `d.dataset.Key` 는 `undefined` 이고 `d.dataset.key` 가 `"A"` 를 준다.
- **거꾸로 도는 길은 더 엄격하다.** `dataset.newCamel = "1"` 은 `data-new-camel` 을 만들지만, `dataset["has-dash"]` 와 `dataset["-lead"]` 는 **`SyntaxError` 를 던진다.** ★ **읽기는 관대하고 쓰기는 던진다.**
- **`setAttribute("data-CamelDirect", …)` 는 통과하고 트리에 `data-cameldirect` 로 들어간다** — HTML 요소에서는 `setAttribute` 도 이름을 소문자로 접기 때문이다. 그래서 최종 `dataset` 키가 `cameldirect` 다.
- ★ `dataset` 자체의 API 는 web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **07번이 정본**이다. 여기서 본 것은 **마크업에 쓴 이름이 어떻게 되나**까지다.

### 4. `className` 은 원문, `classList` 는 집합

**출력**

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

**왜 그런가**

- **`className` 은 속성 문자열 그대로다** — `"  a   b  a   c  "` 의 앞뒤 공백도 중복도 들고 있다.
- **`classList` 는 공백으로 쪼개고 중복을 버린다** — `["a","b","c"]`, `length = 3`.
- **`class=""` 는 `classList` 가 빈 것이다**(`length = 0`). 「빈 문자열도 한 개」가 아니다.
- **대소문자를 구분한다.** `class="Box box"` 는 둘이고 `.box` 와 `.Box` 가 각각 **1개씩** 잡힌다.
- **중복 속성은 첫째가 남는다.** `CLASS="위" class="아래"` → `className = "위"`. 파서가 **이름을 접은 뒤 이미 있는 이름이면 뒤엣것을 버린다**([02번 주제](../02-elements-and-attributes/3-answer.md)). 창 ① 의 덤프에도 `class="위"` 하나만 있다.
- ★ **「나중 것이 이긴다」는 CSS 의 규칙이지 HTML 속성의 규칙이 아니다.** 둘을 섞으면 여기서 틀린다.

### 5. 세 값 + 상속 · `no` 만 거짓 · 말풍선은 글자가 아니다

**출력**

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

**왜 그런가**

- **`contenteditable` 은 열거 속성이다** — 값이 `true`·`false`·`plaintext-only` 중 하나여야 한다. **이름만 쓴 것은 `true` 와 같다.**
- **`.contentEditable` 은 속성을, `.isContentEditable` 은 계산 결과를 답한다.** 속성이 없는 `e2c` 가 `.contentEditable = "inherit"` 인데 `.isContentEditable = true` 다 — **부모(`e2`)가 편집 가능이라 상속했다.**
- **명세에 없는 값(`"nope"`)은 `inherit` 으로 떨어진다.** 트리에는 `"nope"` 가 그대로 남아 있는데 IDL 은 **기본 상태**를 답한다. **에러도 경고도 없다.**
- **IDL 대입은 던진다.** `e6.contentEditable = "bogus"` 가 **`SyntaxError`** 다. ★ **마크업은 조용하고 IDL 은 던진다** — A3 의 `dataset` 과 같은 모양이다.
- **`translate` 는 `no` 만 `false` 다.** 빈 문자열도, `"nope"` 도, **속성이 없는 것도 `true`** 다. 다섯 중 `false` 는 **하나**. ★ 기본이 「번역함」이므로 **끄는 쪽을 명시**해야 한다.
- **`title`** — `.title` 로 글자가 그대로 읽히고, `innerText` 는 `"HTML"` 뿐이다. **말풍선은 요소의 글자가 아니다.**

### 6. 속성은 남고 통로만 없다 — 모르는 요소도 그냥 생긴다

**출력**

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

**왜 그런가**

- **트리는 모르는 이름도 담는다.** `wat`·`onbogus`·`aria-nope`·`id2` 가 전부 남고 `getAttribute` 로 읽힌다.
- **IDL 통로는 정해진 이름에만 있다.** `el.wat`·`el.ariaNope` 는 전부 `undefined` 다 — **속성은 있는데 프로퍼티가 없다.**
- ★ **`data-*` 만 「내가 지은 이름」에 통로가 열려 있다**(`u1.dataset.ok = "2"`). 그것이 `data-*` 가 존재하는 이유다.
- **`ID2` 는 `id2` 로 접힌다.** 이름 접기가 **아는 이름만의 규칙이 아니다.**
- **`<wat-element>` 는 `HTMLElement` 다.** `HTMLUnknownElement` 가 아닌 것은 이름에 **하이픈이 있어 유효한 커스텀 요소 이름**이기 때문이다. `tagName` 은 대문자 `WAT-ELEMENT`, `localName` 은 소문자다.
- **`display` 는 `inline`** — UA 스타일시트에 그 이름이 없으니 초기값이 그대로 온다.
- ★ **CSS 와 정반대다.** CSS 는 모르는 선언을 **조용히 버리고**, HTML 은 **조용히 담는다.** 그래서 두 갈래의 진단 창이 다르다.

### 7. 「있으면 참」이고, `until-found` 는 그 위에 얹힌 열거 값이다

**왜 그런가**

- **불리언 속성의 조건** — **속성이 존재하면 참, 없으면 거짓.** 값은 보지 않는다.
- **`until-found` 는 정의를 깨뜨리지 않는다.** `.hidden` 이 `true` 라는 점은 같고(숨는다), **숨기는 방법**만 다르다. 명세는 `hidden` 을 「**불리언처럼 쓰이지만 `until-found` 라는 상태가 하나 더 있는 열거 속성**」으로 정의한다.
- **그 값이 필요했던 이유** — 접힌 아코디언 안의 글자를 브라우저 「페이지에서 찾기」가 찾아내 펼쳐 주려면, **「숨었지만 찾기에는 보이는」 제3의 상태**가 필요했다. `display: none` 으로는 그 상태를 만들 수 없다.
- **`contenteditable` 은 불리언 속성이 아니다.** 열거 속성이고, 이름만 쓴 것이 `true` 와 같을 뿐이다. 증거는 A5 — **값에 따라 `false` 가 될 수 있다**(`contenteditable="false"`). 불리언이면 그게 불가능하다.

### 8. 두 단계를 거치고, 대문자는 첫 단계에서 죽는다

**왜 그런가**

```text
  마크업 data-Foo-Bar
        │
        │ ① 파서 — 속성 이름을 소문자로 접는다   <- 대문자가 여기서 죽는다
        ▼
  트리   data-foo-bar
        │
        │ ② dataset — `data-` 를 떼고 `-` 다음 글자를 대문자로
        ▼
  키     fooBar
```

- **거꾸로 도는 길은 같은 규칙이 아니다.** 되돌리는 쪽(`dataset.fooBar = …` → `data-foo-bar`)은 대칭이지만, **입력 검사가 붙는다** — 키에 `-` 가 들어가면 `SyntaxError` 다.
- **그래서 왕복이 항상 성립하지 않는다.** 마크업 `data-Foo` 로 시작하면 `dataset.foo` 가 되고, 거기서 다시 마크업을 만들면 `data-foo` 다 — **원래 글자로 못 돌아온다.**

### 9. 세 가지가 서로 다른 단계에서 무시된다

**왜 그런가**

| 무엇 | 무시되는 단계 | 트리에 흔적 |
|---|---|---|
| `hidden="false"` 의 값 | **반영** — 불리언이라 값을 읽지 않는다 | **남는다**(`hidden="false"`) |
| `contenteditable="nope"` | **반영** — 열거 목록에 없어 기본 상태로 | **남는다**(`contenteditable="nope"`) |
| `CLASS="위" class="아래"` 의 뒤엣것 | **파싱** — 같은 이름이 이미 있어 버려진다 | ★ **안 남는다** |

- **셋 중 트리에 흔적이 없는 것은 중복 속성뿐이다.** 앞의 둘은 **담겼는데 안 읽힌 것**이고, 마지막은 **애초에 안 담긴 것**이다.
- ★ **이 구분이 디버깅을 가른다.** `--dump-dom` 으로 보이면 「읽는 쪽」을 의심하고, 안 보이면 「쓰는 쪽」을 의심한다.

### 10. 못 잰 것은 `translate` 의 효과와 `title` 의 말풍선이다

**왜 그런가**

- **`translate`** — 이 환경에 번역 엔진이 없다. 잰 것은 **`.translate` 가 답하는 값**까지이고, 「번역기가 실제로 그 요소를 건너뛴다」는 **던져 볼 수단 자체가 없다.**
- **`title`** — headless 에는 말풍선이 뜰 자리가 없다. 잰 것은 **`.title` 문자열**과 「`innerText` 에 안 섞인다」까지다.
- **「안 돌려 봤다」와 다르다.** 안 돌려 본 것은 **돌리면 답이 나오는데 안 한 것**이고, 못 잰 것은 **측정 방법 자체가 전제를 요구해 성립하지 않는 것**이다.
- **잴 수 없는 것을 단언하면** 이 갈래의 유일한 근거(「돌려 본 것만 적는다」)가 무너진다. 그래서 두 항목은 **쪼개서 잰 조각**만 적었다.
- ★ 이 주제에는 「**부적용인 창**」도 있다 — 창 ④(`compatMode`·`doctype`)는 전역 속성이 문서 모드를 바꾸지 않으므로 **잴 것이 없다.**

### 11. 정본 경계

**왜 그런가**

| 무엇 | 정본 | 여기는 |
|---|---|---|
| `dataset`·`classList`·`getAttribute` 대 IDL | web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **06번**·**07번** | **API 는 그쪽.** 여기는 **마크업에 쓴 이름이 어떻게 되나**까지 |
| 불리언 속성·중복 속성·이름 접기 | [02번 주제](../02-elements-and-attributes/3-answer.md) | 그쪽이 규칙의 정본. 여기는 **일곱 전역 속성에서 어떻게 드러나나** |
| `id` 의 유일성·`#조각`·`:target` | [07번 주제](../07-id-and-fragments/3-answer.md) | 그쪽은 **URL 과 스크롤**, 여기는 **전역 속성으로서의 `id`** |
| `[hidden]` 을 덮는 캐스케이드·속성 선택자 | CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md)) | CSS 가 HTML 을 이기는 자리 |

- **`lang`·`dir` 이 여기 없는 이유** — 둘도 전역 속성이지만 **양방향 텍스트와 언어 태그**가 본체라 분량이 따로 선다. [목록의 **20번 주제**](../20-lang-dir-and-bidi/)가 그것이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 기본 창 폭 **780**. **엔진은 이것 하나다.** **번역 엔진도 스크린리더도 없다.**

**하네스** — 05\~08 네 주제가 공유한다. 블록의 배너에 적힌 `dom`·`probe`·`nojs` 가 그 함수들이다.

```bash
# html05b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
serve() { python3 html05b-server.py >"$1" 2>&1 & echo $!; }
```

- ★ **`nojs` 를 쓴 블록은 「트리에 담긴 이름·값」을 보이려는 것**이다. 프로브 스크립트가 덤프 끝에 붙으면 읽을 것이 묻히므로 `<script>` 부터 잘라 낸다 — **자르는 명령이 배너에 적혀 있으므로 그대로 다시 던질 수 있다.**
- ★ **`--virtual-time-budget` 은 쓰지 않는다**(정본 규칙).

**demo 블록 검증** — 문서의 `demo` 블록에 래퍼와 측정 프로브를 붙인 사본을 따로 띄워 `보이는 것` 을 확인했다.

```text
===== 소스: html05b-demo06a.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 06 검증</title>
<body>
<p class="숨김" hidden>hidden 으로 숨긴 문단</p>
<p class="찾기" hidden="until-found">hidden="until-found" 로 숨긴 문단</p>
<p class="보임">안 숨긴 문단</p>
<style>
  p { border: 2px solid #94a3b8; padding: 4px; margin: 4px 0; }
</style>
<script>
const o = [];
const 폭 = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const 칸 = (s, n) => s + " ".repeat(Math.max(0, n - 폭(s)));
o.push("창 폭 = " + window.innerWidth);
for (const [sel, 이름] of [[".숨김","hidden"],[".찾기",'hidden="until-found"'],[".보임","안 숨김"]]) {
  const e = document.querySelector(sel), s = getComputedStyle(e), r = e.getBoundingClientRect();
  o.push(칸(이름, 22) + " display = " + 칸(s.display, 6)
    + " content-visibility = " + 칸(s.contentVisibility, 8)
    + " 높이 = " + 칸(String(Math.round(r.height)), 4)
    + " 상자 개수 = " + e.getClientRects().length);
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html05b-demo06a.html | probe =====
창 폭 = 780
hidden                 display = none   content-visibility = visible  높이 = 0    상자 개수 = 0
hidden="until-found"   display = block  content-visibility = hidden   높이 = 12   상자 개수 = 1
안 숨김                display = block  content-visibility = visible  높이 = 36   상자 개수 = 1
(exit 0)
```

- **`hidden` 은 상자가 0개**다 — 레이아웃에서 아예 빠진다.
- **`until-found` 는 상자 1개에 높이 12** — 테두리 2 + 안쪽 여백 4 가 위아래로 잡힌 값이고 **글자 줄은 없다**(안 숨긴 것은 36). `content-visibility: hidden` 이 **내용만 안 그린 것**이다.
- 픽셀 자체는 **흔들리는 칸**이므로 「0 / 납작 / 정상」 세 단계만 근거로 쓴다.

`바꿔 볼 것` 에 적은 두 단언도 따로 던졌다.

```text
===== 소스: html05b-demo06b.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 06 의 '바꿔 볼 것' 검증</title>
<body>
<p class="css" hidden>hidden 인데 CSS 로 되살린 문단</p>
<p class="틀린값" hidden="until-fond">오타 난 값</p>
<style>
  p { border: 2px solid #94a3b8; padding: 4px; margin: 4px 0; }
  .css[hidden] { display: block; }
</style>
<script>
const o = [];
const 폭 = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const 칸 = (s, n) => s + " ".repeat(Math.max(0, n - 폭(s)));
o.push("창 폭 = " + window.innerWidth);
for (const [sel, 이름] of [[".css","CSS 로 display:block 을 덮음"],[".틀린값",'hidden="until-fond" (오타)']]) {
  const e = document.querySelector(sel), s = getComputedStyle(e);
  o.push(칸(이름, 30) + " .hidden = " + 칸(JSON.stringify(e.hidden), 8)
    + " display = " + 칸(s.display, 6)
    + " content-visibility = " + 칸(s.contentVisibility, 8)
    + " 높이 = " + Math.round(e.getBoundingClientRect().height));
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html05b-demo06b.html | probe =====
창 폭 = 780
CSS 로 display:block 을 덮음   .hidden = true     display = block  content-visibility = visible  높이 = 36
hidden="until-fond" (오타)     .hidden = true     display = none   content-visibility = visible  높이 = 0
(exit 0)
```

- **CSS 로 `[hidden]` 에 `display: block` 을 주면 되살아난다** — `.hidden` 은 `true` 인 채 `display` 가 `block` 이고 높이가 36 이다. ★ **`hidden` 은 UA 스타일시트 한 줄이라 캐스케이드로 이길 수 있다.**
- **`until-fond` 로 오타 내면 그냥 숨는다** — `display: none`, 높이 0. **열거 목록에 없는 값이라 불리언 쪽으로 떨어진 것**이고, 경고는 없다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `hidden` 여섯 값 — 트리와 IDL | 2 | 동작 방식 (1) · A1 · A7 |
| **`id` 가 만드는 전역 이름** 아홉 가지 | 2 | 동작 방식 (2) · A2 |
| `data-*` 일곱 이름 + 쓰는 쪽 네 시도 | 2 | 동작 방식 (3) · A3 · A8 |
| `class` 네 가지 — 공백·중복·대소문자·중복 속성 | 2 | 동작 방식 (4) · A4 · A9 |
| `contenteditable` 여섯 · `translate` 다섯 · `title` | 2 | 동작 방식 (5) · A5 · A7 |
| 알 수 없는 속성 다섯 · 알 수 없는 요소 | 2 | 동작 방식 (6) · A6 |
| **demo 블록**과 그 `바꿔 볼 것` 두 단언 | 2 | 동작 방식 (7) |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| **`until-found` 를 구현한 방법** | `content-visibility: hidden` | 명세가 정한 것은 **동작**이지 이 속성이 아니다 |
| `<wat-element>` 의 인터페이스 | `HTMLElement` | 커스텀 요소 이름 규칙에 달렸다 |
| demo 의 높이 픽셀 | `0` · `12` · `36` | 글꼴·테두리·여백에 달렸다 |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). ② **`contenteditable` 의 실제 편집** — 키 입력을 넣지 않았다. `plaintext-only` 가 서식 붙여넣기를 정말 막는지는 안 던졌다. ③ **`hidden="until-found"` 를 「페이지에서 찾기」로 펼치는 것** — headless 에서 찾기 UI 를 부를 수단을 쓰지 않았다. ④ **`lang`·`dir`** — [목록의 **20번 주제**](../20-lang-dir-and-bidi/) 몫이다.

**못 잰 것**(「안 돌려 본 것」과 다르다) — ① **`translate` 가 실제로 하는 일.** 번역 엔진이 없어 측정 수단 자체가 없다. 쪼개서 잰 조각은 **`.translate` 가 답하는 값**뿐이다. ② **`title` 의 말풍선.** headless 에는 뜰 자리가 없다. 조각은 **`.title` 문자열**과 「`innerText` 에 안 섞인다」뿐이다.

**부적용인 창** — **창 ④(`document.compatMode`·`document.doctype`).** 전역 속성은 문서 모드를 바꾸지 않아 **잴 것이 없다**(「재 봤더니 같았다」가 아니다).

## 용어 풀이

- **전역 속성(global attribute)** — 모든 HTML 요소에 쓸 수 있는 속성.
- **불리언 속성(boolean attribute)** — 있으면 참, 없으면 거짓. 값을 보지 않는다.
- **열거 속성(enumerated attribute)** — 정해진 값 목록 중 하나를 받는다. 목록에 없으면 **기본 상태**로 떨어진다.
- **기본 상태(invalid value default)** — 열거 속성에 무효한 값이 왔을 때 대신 쓰이는 상태. `contenteditable` 은 `inherit`.
- **IDL 프로퍼티(IDL property)** — 스크립트에서 읽는 이름. 속성과 이름도 타입도 다를 수 있다.
- **반영(reflect)** — 속성과 IDL 프로퍼티가 이어져 있는 것.
- **`dataset`** — `data-*` 속성을 낙타 표기 키로 보여 주는 통로.
- **`classList`** — `class` 를 공백으로 쪼갠 집합. 중복이 없다.
- **`content-visibility`** — 상자는 남기고 내용만 안 그리게 하는 CSS 속성.
- **이름 있는 접근(named access on Window)** — `id`(와 일부 요소의 `name`)가 `window` 의 이름이 되는 규칙. **열거되지 않는다.**
- **`HTMLCollection`** — 요소들의 라이브 목록. 중복 `id` 의 전역 접근이 이것을 준다.
