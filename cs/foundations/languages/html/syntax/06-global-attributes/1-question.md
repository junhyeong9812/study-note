# html/syntax/06 — 전역 속성: `id`/`class`/`title`/`hidden`/`data-*`/`contenteditable`/`translate` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 이 주제는 **트리에 담긴 문자열**과 **IDL 프로퍼티가 답하는 값**을 갈라서 답한다. 둘은 자주 다르다.
> ★ 「무시된다」로 뭉뚱그리지 말고 **어느 단계에서 무시되는지**까지 적어라 — 파서인가, 반영인가, 렌더인가.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [02번 주제](../02-elements-and-attributes/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 속성에 값을 여섯 가지로 주면 (예측)

```html
<!-- html05b-hidden.html -->
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
```

- 여섯 문단이 각각 보이는지 안 보이는지 예측하라.
- `.hidden` 이 답하는 값을 여섯 줄 다 예측하라. **타입까지** 적어라.
- 여섯 중 `display` 가 `none` 이 아닌 것이 있는가?
- `--dump-dom` 이 보여 줄 첫째 문단의 속성은 어떤 꼴인가?

### 2. 이름표를 붙이기만 했는데 (예측)

```html
<!-- html05b-global-id.html -->
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
```

- 아홉 줄의 출력을 각각 예측하라.
- 같은 이름이 둘일 때 돌아오는 것의 **타입**은?
- `<a name="…">` 은 같은 일을 하는가?
- `Object.keys` 에 안 나오는데 `in` 으로는 잡힌다면 그 이름은 어디에 사는가?

### 3. 일곱 가지 이름의 사용자 정의 속성 (예측)

```html
<!-- html05b-dataset.html -->
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
```

- 소스의 이름 일곱이 트리에서 어떤 이름이 되는지 예측하라.
- 그 각각의 `dataset` 키를 예측하라.
- `d.dataset.Key` 와 `d.dataset.key` 중 값을 주는 쪽은?
- 거꾸로 `dataset` 에 키를 넣는 네 가지 시도는 각각 어떻게 되는가?

### 4. 공백과 중복이 든 분류 스티커 (예측)

```html
<!-- html05b-class.html -->
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
```

- 네 문단의 `className` 과 `classList` 를 각각 예측하라.
- `classList.length` 를 넷 다 예측하라.
- `Box` 와 `box` 는 같은 것인가?
- 같은 이름의 속성이 두 번 적혔을 때 남는 것은 어느 쪽인가?

### 5. 편집·번역·말풍선 세 속성 (예측)

```html
<!-- html05b-editable.html -->
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
```

- `contenteditable` 여섯 경우의 `.contentEditable` 과 `.isContentEditable` 을 예측하라.
- 속성이 없는 `e2c` 가 `true` 가 될 수 있는가?
- `translate` 다섯 경우의 `.translate` 를 예측하라. **몇 개가 `false` 인가?**
- `title` 의 글자가 `innerText` 에 섞이는가?

### 6. 아무도 모르는 이름의 속성과 요소 (예측)

```html
<!-- html05b-unknown.html -->
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
```

- 다섯 속성이 트리에 남는지 예측하라.
- `el.wat`·`el.ariaNope` 가 각각 무엇을 답하는가?
- `ID2` 는 트리에서 어떤 이름이 되는가?
- `<wat-element>` 의 `constructor.name` 과 `display` 를 예측하라.

### 7. 「불리언 속성」의 정확한 뜻 (왜)

- 불리언 속성이 참이 되는 조건을 한 문장으로 답하라.
- `hidden="until-found"` 는 그 정의를 깨뜨리는가?
- 깨뜨리지 않는다면 그 값은 어떻게 설명되는가?
- `contenteditable` 은 불리언 속성인가?

### 8. 이름이 두 번 바뀌는 길 (경계)

- 마크업의 `data-Foo-Bar` 가 `dataset` 키가 되기까지 몇 단계를 거치는가?
- 각 단계에서 무엇이 바뀌는가?
- 대문자가 죽는 것은 어느 단계인가?
- 거꾸로 도는 길(스크립트 → 마크업)은 같은 규칙인가?

### 9. 「무시된다」의 세 가지 (경계)

- `hidden="false"` 의 값이 무시되는 것은 어느 단계인가?
- `contenteditable="nope"` 는 어떻게 처리되는가? 값이 남는가?
- `CLASS="위" class="아래"` 에서 사라지는 쪽은 어느 단계에서 사라지는가?
- 셋 중 **트리에 흔적이 남지 않는** 것은 무엇인가?

### 10. 무엇을 못 재나 (경계)

- 이 주제에서 **측정 수단 자체가 없는** 항목 둘을 대라.
- 그 둘에 대해 이 문서가 잰 것은 무엇까지인가?
- 「안 돌려 봤다」와 「못 잰다」는 무엇이 다른가?
- 잴 수 없는 것을 「이렇게 된다」로 적으면 무엇이 무너지는가?

### 11. 정본 경계 긋기 (연결)

- `dataset`·`classList` 라는 API 의 정본은 어느 갈래인가?
- 불리언 속성·중복 속성 규칙의 정본은 어느 주제인가?
- `id` 의 유일성과 `#조각` 이야기의 정본은 어느 주제인가?
- `lang`·`dir` 도 전역 속성인데 이 주제에 없는 이유는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
