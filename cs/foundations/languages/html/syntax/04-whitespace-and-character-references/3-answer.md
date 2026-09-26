# html/syntax/04 — 공백·텍스트·문자 참조: 공백 축약·엔티티·`<pre>` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [CSS Text Level 3](https://drafts.csswg.org/css-text-3/#white-space-processing) 두 명세로 접지했다 — **이 주제는 두 명세에 걸쳐 있다.**\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★ **글자 대신 코드포인트로 읽는다.** 직렬화가 되쓰기를 한 번 더 하기 때문이다(A8).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 트리에는 그대로 있고 화면에서만 합쳐진다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-space.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>공백 축약</title>
<p id="p1">가     나
다</p>
<div id="d1">
  <span>가</span>
  <span>나</span>
</div>
<script>
const o = [];
const p1 = document.getElementById("p1");
const d1 = document.getElementById("d1");
o.push("p1 textContent = " + JSON.stringify(p1.textContent));
o.push("p1 innerText   = " + JSON.stringify(p1.innerText));
o.push("d1 childNodes  = " + d1.childNodes.length + "   children = " + d1.children.length);
o.push("d1 노드 목록   = " + [...d1.childNodes].map(n => n.nodeType === 3 ? "#text" + JSON.stringify(n.data) : n.nodeName).join(" | "));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-space.html | nojs =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>공백 축약</title>
</head><body><p id="p1">가     나
다</p>
<div id="d1">
  <span>가</span>
  <span>나</span>
</div>
(exit 0)
```

```text
===== 소스: html01b-space.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>공백 축약</title>
<p id="p1">가     나
다</p>
<div id="d1">
  <span>가</span>
  <span>나</span>
</div>
<script>
const o = [];
const p1 = document.getElementById("p1");
const d1 = document.getElementById("d1");
o.push("p1 textContent = " + JSON.stringify(p1.textContent));
o.push("p1 innerText   = " + JSON.stringify(p1.innerText));
o.push("d1 childNodes  = " + d1.childNodes.length + "   children = " + d1.children.length);
o.push("d1 노드 목록   = " + [...d1.childNodes].map(n => n.nodeType === 3 ? "#text" + JSON.stringify(n.data) : n.nodeName).join(" | "));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-space.html | probe =====
p1 textContent = "가     나\n다"
p1 innerText   = "가 나 다"
d1 childNodes  = 5   children = 2
d1 노드 목록   = #text"\n  " | SPAN | #text"\n  " | SPAN | #text"\n"
(exit 0)
```

**`textContent` 와 `innerText`**

- `textContent` = **`"가     나\n다"`** — 공백 다섯과 줄바꿈이 **그대로** 있다.
- `innerText` = **`"가 나 다"`** — 다섯 칸이 **한 칸**, 줄바꿈이 **한 칸**이 됐다.

**차이를 만든 것**

- ★ **CSS** 다. `white-space` 의 기본값 `normal` 이 **연속 공백과 줄바꿈을 한 칸으로** 그린다.
- **HTML 파서는 공백을 하나도 안 지운다** — `--dump-dom` 출력에 소스의 공백이 그대로 있는 것이 그 증거다.

**`childNodes` 와 `children`**

- `childNodes.length` = **5**, `children.length` = **2**.
- 목록 — `#text "\n  "` · `SPAN` · `#text "\n  "` · `SPAN` · `#text "\n"`.

**`d1.childNodes[0]`**

- **공백 텍스트 노드**(`"\n  "`)다. **첫 자식 요소가 아니다.**
- 첫 자식 요소를 잡으려면 `children[0]` 또는 `firstElementChild`.

### 2. `<pre>` 직후 줄바꿈 하나는 파서가 버린다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-pre.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>pre 가 바꾸는 것</title>
<pre id="a">
가     나
다</pre>
<pre id="b">

가</pre>
<textarea id="c">
값</textarea>
<script>
const o = [];
const j = id => JSON.stringify(document.getElementById(id).textContent);
o.push("pre#a textContent = " + j("a"));
o.push("pre#a innerText   = " + JSON.stringify(document.getElementById("a").innerText));
o.push("pre#b textContent = " + j("b"));
o.push("textarea#c value  = " + JSON.stringify(document.getElementById("c").value));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-pre.html | nojs =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>pre 가 바꾸는 것</title>
</head><body><pre id="a">가     나
다</pre>
<pre id="b">
가</pre>
<textarea id="c">값</textarea>
(exit 0)
```

```text
===== 소스: html01b-pre.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>pre 가 바꾸는 것</title>
<pre id="a">
가     나
다</pre>
<pre id="b">

가</pre>
<textarea id="c">
값</textarea>
<script>
const o = [];
const j = id => JSON.stringify(document.getElementById(id).textContent);
o.push("pre#a textContent = " + j("a"));
o.push("pre#a innerText   = " + JSON.stringify(document.getElementById("a").innerText));
o.push("pre#b textContent = " + j("b"));
o.push("textarea#c value  = " + JSON.stringify(document.getElementById("c").value));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-pre.html | probe =====
pre#a textContent = "가     나\n다"
pre#a innerText   = "가     나\n다"
pre#b textContent = "\n가"
textarea#c value  = "값"
(exit 0)
```

**`pre#a` 의 `textContent`**

- **`"가     나\n다"`** — 소스보다 **한 글자**(맨 앞 `\n`) 적다.

**`pre#b`**

- 줄바꿈을 **둘** 썼더니 **`"\n가"`** — **하나만** 사라졌다.

**`textarea#c` 의 `value`**

- **`"값"`** — 앞 줄바꿈이 없다. **`textarea` 도 같은 대우**다.

**CSS 인가 파서인가**

- ★ **파서**다. 근거는 **`--dump-dom` 출력**이다 — 직렬화된 트리의 `<pre>` 가 **`<pre id="a">가     나`** 로 **줄바꿈 없이 붙어 있다.**
- CSS 가 한 일이면 **트리에는 남아 있어야** 한다. 트리에서 없어졌으므로 **파싱 단계**다.
- 명세의 「in body」 규칙이 `pre`·`listing`·`textarea` 시작 태그 직후의 **줄바꿈 하나를 무시하라**고 적어 뒀다.

```text
   공백 축약        CSS 가 한다        트리에는 남는다        white-space 로 되돌아온다
   <pre> 첫 줄바꿈   ★ 파서가 한다      트리에서 사라진다      되돌릴 수 없다
```

### 3. 세미콜론이 없어도 풀리는 이름이 있다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-charref.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>문자 참조 세 꼴</title>
<p id="r1">&amp; &#38; &#x26;</p>
<p id="r2">&ampx</p>
<p id="r3">&amp;ampx</p>
<p id="r4">&notit;</p>
<p id="r5">5 &lt 3</p>
<p id="r6">a &lt; b</p>
<p id="r7">a < b</p>
<p id="r8">&unknownzz;</p>
<script>
const o = [];
const cp = s => [...s].map(c => "U+" + c.codePointAt(0).toString(16).toUpperCase().padStart(4,"0")).join(" ");
for (const id of ["r1","r2","r3","r4","r5","r6","r7","r8"]) {
  const t = document.getElementById(id).textContent;
  o.push(id + " 코드포인트 = " + cp(t));
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-charref.html | probe =====
r1 코드포인트 = U+0026 U+0020 U+0026 U+0020 U+0026
r2 코드포인트 = U+0026 U+0078
r3 코드포인트 = U+0026 U+0061 U+006D U+0070 U+0078
r4 코드포인트 = U+00AC U+0069 U+0074 U+003B
r5 코드포인트 = U+0035 U+0020 U+003C U+0020 U+0033
r6 코드포인트 = U+0061 U+0020 U+003C U+0020 U+0062
r7 코드포인트 = U+0061 U+0020 U+003C U+0020 U+0062
r8 코드포인트 = U+0026 U+0075 U+006E U+006B U+006E U+006F U+0077 U+006E U+007A U+007A U+003B
(exit 0)
```

**여덟 문단의 코드포인트**

| 소스 | 코드포인트 | 읽으면 |
|---|---|---|
| `&amp; &#38; &#x26;` | `U+0026 U+0020 U+0026 U+0020 U+0026` | `& & &` — **세 꼴이 같다** |
| `&ampx` | `U+0026 U+0078` | **`&x`** ★ |
| `&amp;ampx` | `U+0026 U+0061 U+006D U+0070 U+0078` | `&ampx` |
| `&notit;` | `U+00AC U+0069 U+0074 U+003B` | **`¬it;`** ★ |
| `5 &lt 3` | `U+0035 U+0020 U+003C U+0020 U+0033` | **`5 < 3`** ★ |
| `a &lt; b` | `U+0061 U+0020 U+003C U+0020 U+0062` | `a < b` |
| `a < b` | `U+0061 U+0020 U+003C U+0020 U+0062` | `a < b` — **맨 `<` 도 남는다** |
| `&unknownzz;` | `U+0026 … U+003B` | `&unknownzz;` — 그대로 |

**세미콜론 없이 풀리는 이유**

- 명세의 **이름 참조 표에 「세미콜론 없이도 매칭되는 이름」이 따로 표시**돼 있다. `&amp`·`&not`·`&lt` 가 거기 든다.
- **옛 문서를 깨지 않으려고** 남긴 화석이다.

**`&notit;`**

- **`¬it;`** 이다. `&not` 이 매칭돼 `U+00AC` 가 되고, `it;` 이 글자로 남았다.
- 파서는 **최장 일치**를 먼저 시도한다 — `&notin;` 같은 긴 이름이 있으므로 길게 읽어 보다가 실패하면 `&not` 으로 물러난다.

**맨 `<` 가 살아남는 이유**

- `<` 뒤에 **글자나 `/`·`!`·`?` 가 안 오면 태그가 아니다.** 여기서는 공백이라 **그냥 글자**로 남는다([03번 주제](../03-parser-and-error-recovery/3-answer.md) A6 와 같은 규칙).

### 4. 텍스트와 속성값의 규칙이 다르다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-charref-attr.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>텍스트와 속성값의 규칙이 다르다</title>
<p id="t1">?a=1&copy=3</p>
<a id="a1" href="?a=1&copy=3">링크</a>
<p id="t2">&copy 2026</p>
<a id="a2" href="?x=&copy 2026">링크2</a>
<script>
const o = [];
const cp = s => [...s].map(c => "U+" + c.codePointAt(0).toString(16).toUpperCase().padStart(4,"0")).join(" ");
const put = (k, s) => o.push(k + " = " + cp(s));
put("t1 텍스트", document.getElementById("t1").textContent);
put("a1 href  ", document.getElementById("a1").getAttribute("href"));
put("t2 텍스트", document.getElementById("t2").textContent);
put("a2 href  ", document.getElementById("a2").getAttribute("href"));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-charref-attr.html | probe =====
t1 텍스트 = U+003F U+0061 U+003D U+0031 U+00A9 U+003D U+0033
a1 href   = U+003F U+0061 U+003D U+0031 U+0026 U+0063 U+006F U+0070 U+0079 U+003D U+0033
t2 텍스트 = U+00A9 U+0020 U+0032 U+0030 U+0032 U+0036
a2 href   = U+003F U+0078 U+003D U+00A9 U+0020 U+0032 U+0030 U+0032 U+0036
(exit 0)
```

**`t1` 과 `a1`**

- **다르다.**

| | 소스 | 결과 |
|---|---|---|
| `t1` 텍스트 | `?a=1&copy=3` | **`?a=1©=3`** — `&copy` 가 풀렸다 |
| `a1` `href` | `?a=1&copy=3` | **`?a=1&copy=3`** — 그대로 |

**규칙**

- **속성값 안에서는 조건이 하나 더 있다** — 세미콜론 없는 이름 참조 뒤에 **`=` 또는 영숫자**가 오면 **풀지 않는다.**
- 웹에 이미 있는 `?…&copy=…` 류 URL 을 **살리려고** 들어간 예외다.

**`t2`·`a2` 에서 또 달라지는 이유**

| | 소스 | 결과 |
|---|---|---|
| `t2` 텍스트 | `&copy 2026` | `© 2026` |
| `a2` `href` | `?x=&copy 2026` | **`?x=© 2026`** — ★ 속성값에서도 풀렸다 |

- 뒤에 온 것이 **공백**이라 위 예외 조건(`=`·영숫자)에 안 걸렸다.

**「속성값에 쓰면 안전하다」**

- ★ **틀렸다.** 뒤 글자에 따라 갈린다.
- 결론 한 줄 — **`&` 는 어디에 쓰든 `&amp;` 로 쓴다.** 예외를 외우는 것보다 싸다.

### 5. 두 번 처리된다는 뜻

**각각 한 문장**

- **파서** — 소스의 공백을 **그대로 텍스트 노드에 담는다.** 아무것도 안 합친다.
- **CSS** — `white-space: normal` 이면 **연속 공백과 줄바꿈을 한 칸으로 그린다.** 트리는 안 건드린다.

**「공백이 사라졌다」가 틀린 이유**

- **트리에는 있다.** 실측 `textContent` 에 공백 다섯 개가 그대로 있었다. 화면에만 안 보이는 것이다.

**CSS 가 아니라 파서가 하는 일**

- **`<pre>`·`<textarea>` 시작 태그 직후의 줄바꿈 하나를 버리는 것** 하나뿐이다(A2).

**`white-space` 로 안 돌아오는 이유**

- **트리에서 이미 사라졌기** 때문이다. CSS 는 트리에 있는 것을 어떻게 그릴지만 정한다 — **없는 글자를 그릴 수는 없다.**

### 6. 인라인 요소 사이의 틈

**왜 생기나**

- 소스의 줄바꿈과 들여쓰기가 **공백 텍스트 노드**로 트리에 들어가고(A1 의 `childNodes = 5`), 그것이 렌더에서 **한 칸**이 된다.

**`margin: 0` 으로 안 없어지는 이유**

- **여백이 아니라 글자**이기 때문이다. `margin` 은 상자 사이를 조절하지 **텍스트 노드를 지우지 못한다.**

**없애는 방법 셋**

1. 줄바꿈을 **주석으로 삼킨다** — `</span><!--`, 줄바꿈, `--><span>`.
2. **닫는 꺾쇠를 다음 줄로** 내린다 — `<span>가</span\n><span>나</span>`.
3. 부모에 **`font-size: 0`** 을 주고 자식에서 되돌린다.

**오늘 권할 만한 것**

- **셋 다 아니다.** 부모를 **flex 나 grid** 로 만드는 쪽이다. 실측으로 대조했다.

```text
===== 소스: html01b-demo04c.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>인라인 사이의 틈 — flex 대조</title>
<body>
<div id="n"><span>가</span>
<span>나</span></div>
<div id="f"><span>가</span>
<span>나</span></div>
<style>
  div { font: 16px monospace; }
  span { background: #ddd; }
  #f { display: flex; }
</style>
<script>
const o = [];
const w = id => [...document.querySelectorAll("#" + id + " span")].map(s => s.getBoundingClientRect());
for (const id of ["n", "f"]) {
  const r = w(id);
  o.push("#" + id + "  childNodes = " + document.getElementById(id).childNodes.length
         + "   span1 right = " + r[0].right + "   span2 left = " + r[1].left
         + "   틈 = " + (r[1].left - r[0].right));
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-demo04c.html | probe =====
#n  childNodes = 3   span1 right = 22.734375   span2 left = 30.75   틈 = 8.015625
#f  childNodes = 3   span1 right = 22.734375   span2 left = 22.734375   틈 = 0
(exit 0)
```

- **`childNodes` 는 둘 다 3**(공백 노드가 그대로 있다)인데, 보통 블록에서는 두 `span` 사이가 **8.015625px** 벌어지고 **flex 에서는 `0`** 이다.
- ★ **공백 텍스트 노드가 사라진 것이 아니다** — flex 컨테이너가 **공백만 있는 자식을 항목으로 만들지 않아** 그려지지 않는 것이다.
- ★ 앞의 셋은 전부 **마크업을 읽기 어렵게** 만드는 관용구다. 레이아웃 방법의 정본은 CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **24번**·**27번**이다.

### 7. `&nbsp;` 의 자리

**보통 공백과 다른 점 둘**

1. **축약되지 않는다** — 여러 개를 쓰면 여러 칸이 그대로 보인다(demo 실측).
2. **줄이 갈리지 않는다** — `10&nbsp;kg` 은 두 줄로 나뉘지 않는다.

**여러 개 쓰면 문제되는 것**

- 보조 기술이 그것을 **글자로 읽거나** 이상한 곳에서 끊을 수 있고, **글꼴·폭이 바뀌면 여백이 흐트러진다.**

**이 환경에서 확인할 수 있는가**

- ★ **없다.** 스크린리더(NVDA·VoiceOver)가 없어 **「어떻게 읽히는지」는 실행 확인 불가**다 — **미실행**으로 적는다.
- 확인한 것은 **시각 쪽 절반**뿐이다 — demo 실측에서 `&nbsp;` 세 개가 **축약되지 않고 넓은 틈**으로 남았다(`innerText` 에 `U+00A0` 셋).

**대신 무엇을 쓰나**

- **CSS** — `margin`·`padding`·`gap`·`word-spacing`. 여백은 스타일이지 내용이 아니다.

### 8. `--dump-dom` 의 이스케이프는 내가 쓴 것이 아니다

**출력** (Chrome 151 headless — JS 로 트리에 넣고 직렬화한 것)

```text
===== 소스: html01b-serialize.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>직렬화가 되쓰는 것</title>
<p id="s">자리</p>
<script>
const NBSP = String.fromCharCode(160);
const s = document.getElementById("s");
s.textContent = "& < > " + NBSP + " \" '";
s.setAttribute("data-v", "& < > " + NBSP + " \" '");
</script>
===== dom html01b-serialize.html | nojs =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>직렬화가 되쓰는 것</title>
</head><body><p id="s" data-v="&amp; &lt; &gt; &nbsp; &quot; '">&amp; &lt; &gt; &nbsp; " '</p>
(exit 0)
```

**소스에 안 썼는데 나올 수 있는가**

- **있다.** 이 실험은 **소스에 `&amp;` 를 한 번도 안 썼고** JS 로 글자를 넣었는데, 출력에 `&amp;`·`&lt;`·`&gt;`·`&nbsp;` 가 나왔다.

**되쓰기 대상**

| | 되쓰이는 글자 |
|---|---|
| 텍스트 | `&` → `&amp;` · `<` → `&lt;` · `>` → `&gt;` · U+00A0 → `&nbsp;` (`"`·`'` 는 그대로) |
| 속성값 | 위 넷 + `"` → `&quot;` (★ 이 판에서는 `<`·`>` 도 되쓰였다) |

**명세와 관찰 가르기**

- **명세** — 텍스트의 네 글자, 속성값의 `&`·U+00A0·`"`.
- ★ **관찰**(Chrome 151) — **속성값의 `<`·`>`**. 근거로 쓰지 않는다.

**근거를 무엇으로 잡나**

- ★ **코드포인트**다. 이 주제의 블록이 전부 `U+XXXX` 로 찍힌 이유가 그것이다 — **되쓰기를 거치지 않는다.**
- 같은 이유로 프로브 출력에는 **되돌리는 `sed`** 를 걸어 뒀다(`## 실행 검증` 의 `probe`).

### 9. 화석을 남긴 이유

**한 문장**

- **웹에 이미 있는 수십억 개의 문서를 깨지 않으려고**다. 세미콜론 없이 `&amp` 를 쓴 페이지가 이미 많았다.

**03번 주제의 같은 집안**

- **`</br>` 이 `<br>` 이 되는 규칙**이다. 둘 다 「**옛 문서를 살리려고 명세에 박아 넣은 화석**」이다.

**새로 쓰는 문서에서는**

- **언제나 세미콜론을 쓴다.** 그리고 `&` 는 **언제나 `&amp;`** 로 쓴다.

**`&notit;` 을 읽는 순서**

```text
   &notit;  를 읽을 때

   [1] 가장 긴 이름부터 맞춰 본다      &notit;  -> 그런 이름 없음
   [2] 한 글자씩 줄이며 계속            &noti    -> 없음
   [3]                                  &not     -> ★ 있다 (세미콜론 없이도 허용)
   [4] U+00AC 를 내놓고 나머지는 글자   ¬ + "it;"
```

- **최장 일치**로 읽되, 매칭에 실패하면 **물러난다.**

### 10. 정본 경계

**공백 축약 규칙**

- ★ **정본은 CSS 갈래**다 — CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **51번**(`white-space`·줄바꿈).
- 여기는 「**HTML 이 무엇을 트리에 넣나**」까지 — 그리고 **파서가 하는 유일한 예외**(`<pre>` 첫 줄바꿈)까지.

**`childNodes`·`innerText` API**

- **web-api 갈래**가 정본이다. 여기는 **파서가 그런 트리를 만든다는 사실**까지.

**U+00A0 의 바이트**

- [`../../../../data-representation/`](../../../../data-representation/)(유니코드·인코딩)가 정본이다.
- 바이트를 글자로 바꾸는 **선언**(`meta charset`)은 목록의 **50번 주제**다. 이 주제는 **글자가 된 뒤**부터다.

**독립 주제인 이유**

- ★ **세 갈래 어디도 「마크업을 어떻게 쓸 것인가」에 답하지 않기** 때문이다.
- CSS 는 「어떻게 그릴까」, web-api 는 「어떻게 읽을까」, 인코딩은 「어떤 바이트일까」를 답한다.
- 여기가 답하는 것은 **「`&` 를 본문에 쓰려면 어떻게 타자하나」·「`<pre>` 안의 첫 줄은 왜 비나」** — **마크업을 쓰는 사람의 질문**이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 기본 창 폭 **780**. **엔진은 이것 하나다.** **마크업 검증기는 없다.**

**하네스** — 01\~04 네 주제가 공유한다. 블록의 배너에 적힌 `dom`·`probe`·`nojs` 가 이 셋이다.

```bash
# html01b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
```

- ★ **`probe` 의 마지막 `sed` 가 이 주제에서 특히 중요하다.** 프로브 출력은 `<pre>` 의 텍스트라 **직렬화가 `&`·`<`·`>` 를 되쓴다**(A8). 그것을 되돌린 것이고, **배너에 적혀 있으므로 그대로 다시 던질 수 있다.**
- ★ **그 `sed` 로도 U+00A0 은 안 돌아온다**(`&nbsp;` 는 목록에 없다). 그래서 이 주제의 프로브는 **코드포인트로 찍는다** — 되쓰기를 아예 안 거치게 하는 쪽이 낫다.
- ★ **`--virtual-time-budget` 은 쓰지 않는다**(정본 규칙).

**demo 블록 검증** — 문서의 `demo` 블록에 래퍼와 측정 프로브를 붙인 사본을 따로 띄워 `보이는 것` 을 확인했다.

```text
===== 소스: html01b-demo04a.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 04 검증</title>
<body>
<p class="src">가     나
다&nbsp;&nbsp;&nbsp;라</p>
<pre class="src">가     나
다</pre>
<style>
  .src { border: 1px solid #94a3b8; padding: 4px; font: 16px monospace; }
</style>
<script>
const o = [];
const cp = s => [...s].map(c => c === "\n" ? "\\n" : "U+" + c.codePointAt(0).toString(16).toUpperCase().padStart(4,"0")).join(" ");
const p = document.querySelector("p.src");
const pre = document.querySelector("pre.src");
o.push("창 폭                = " + window.innerWidth);
o.push("p   textContent 길이 = " + p.textContent.length);
o.push("p   innerText 코드점 = " + cp(p.innerText));
o.push("p   높이            = " + p.getBoundingClientRect().height);
o.push("pre textContent 길이 = " + pre.textContent.length);
o.push("pre innerText 코드점 = " + cp(pre.innerText));
o.push("pre 높이            = " + pre.getBoundingClientRect().height);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-demo04a.html | probe =====
창 폭                = 780
p   textContent 길이 = 13
p   innerText 코드점 = U+AC00 U+0020 U+B098 U+0020 U+B2E4 U+00A0 U+00A0 U+00A0 U+B77C
p   높이            = 34
pre textContent 길이 = 9
pre innerText 코드점 = U+AC00 U+0020 U+0020 U+0020 U+0020 U+0020 U+B098 \n U+B2E4
pre 높이            = 58
(exit 0)
```

- `p` 는 `textContent` **13글자**인데 `innerText` 코드포인트가 **9개** — 다섯 칸과 줄바꿈이 **각각 한 칸**이 됐고 `U+00A0` 셋은 **그대로** 남았다.
- `pre` 는 `textContent` **9글자**이고 `innerText` 에 공백 다섯과 `\n` 이 **그대로** 있다.
- 높이가 **34 대 58** — 한 줄과 두 줄이다. ★ **픽셀 자체는** 「**흔들리는 칸**」이므로 **두 상자가 갈린다는 사실**만 근거로 쓴다.

`바꿔 볼 것` 에 적은 두 단언도 따로 던졌다.

```text
===== 소스: html01b-demo04b.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 04 의 '바꿔 볼 것' 검증</title>
<body>
<p class="v1">가     나
다&nbsp;&nbsp;&nbsp;라</p>
<p class="v2">가     나
다   라</p>
<style>
  p  { border: 1px solid #94a3b8; padding: 4px; font: 16px monospace; }
  .v1 { white-space: pre; }
</style>
<script>
const o = [];
const cp = s => [...s].map(c => c === "\n" ? "\\n" : "U+" + c.codePointAt(0).toString(16).toUpperCase().padStart(4,"0")).join(" ");
const v1 = document.querySelector(".v1"), v2 = document.querySelector(".v2");
o.push("v1 (white-space: pre)  innerText 코드점 = " + cp(v1.innerText));
o.push("v1 높이 = " + v1.getBoundingClientRect().height);
o.push("v2 (nbsp 를 보통 공백으로) innerText 코드점 = " + cp(v2.innerText));
o.push("v2 높이 = " + v2.getBoundingClientRect().height);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-demo04b.html | probe =====
v1 (white-space: pre)  innerText 코드점 = U+AC00 U+0020 U+0020 U+0020 U+0020 U+0020 U+B098 \n U+B2E4 U+00A0 U+00A0 U+00A0 U+B77C
v1 높이 = 58
v2 (nbsp 를 보통 공백으로) innerText 코드점 = U+AC00 U+0020 U+B098 U+0020 U+B2E4 U+0020 U+B77C
v2 높이 = 34
(exit 0)
```

- `white-space: pre` 를 더하면 **`<pre>` 와 같은 모양**이 된다(공백 다섯 + `\n` 이 `innerText` 에 남고 높이가 58).
- `&nbsp;` 를 보통 공백으로 바꾸면 **`U+0020` 한 칸**으로 줄어든다(높이 34).

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 공백 축약 — `textContent` 대 `innerText` | 2 | 동작 방식 (1) · A1 · A5 |
| **`childNodes` 5 대 `children` 2** 와 노드 목록 | 2 | 동작 방식 (2) · A1 · A6 |
| `<pre>`·`<textarea>` 직후 줄바꿈(하나·둘) | 2 | 동작 방식 (3) · A2 |
| 문자 참조 여덟 경우의 코드포인트 | 2 | 동작 방식 (4) · A3 |
| **텍스트 대 속성값** 네 경우 | 2 | 동작 방식 (5) · A4 |
| 직렬화 되쓰기(텍스트·속성값 각 여섯 글자) | 2 | 동작 방식 (6) · A8 |
| **demo 블록**과 그 `바꿔 볼 것` 두 단언 | 2 | 동작 방식 (1) |
| **인라인 틈 — 보통 블록 대 flex** | 2 | A6 |
| demo 를 창 폭 520 과 780 에서 각각 | 1 | 값이 같아 **창 폭에 안 흔들린다**를 확인 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| **속성값 직렬화의 `<`·`>`** | `&lt;`·`&gt;` 로 되쓰임 | 명세가 정한 것은 `&`·U+00A0·`"` 뿐이다 |
| demo 의 높이 픽셀 | `34` · `58` | 글꼴·줄 높이에 달렸다 — **크고 작음만** 근거로 쓴다 |
| `--dump-dom` 의 줄바꿈 자리 | 소스의 텍스트 노드를 그대로 | 직렬화 + 도구 |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). ② **참조 이름 전수** — 명세의 이름 참조 표를 통째로 던져 보지 않았다. 이 주제가 던진 것은 여덟 경우뿐이다. ③ **`&#x110000;` 같은 범위 밖 숫자 참조·서로게이트 참조의 치환 규칙** — 이 배치에서 던지지 않았다. ④ **`<textarea>` 의 폼 제출 동작**(목록의 26번 주제).

**못 잰 것**(③의 「안 돌려 본 것」과 다르다) — **`&nbsp;` 가 보조 기술에 어떻게 읽히나.** 스크린리더가 없어 **측정 수단 자체가 없다.** 쪼개서 잰 조각은 **시각 쪽 절반**(축약되지 않는다는 것)뿐이고, A7 에 그렇게 적었다.

## 용어 풀이

- **텍스트 노드(text node)** — 글자를 담는 노드. `nodeType === 3`. 공백만 있는 것도 노드다.
- **공백 축약(white space collapsing)** — 연속 공백·줄바꿈을 한 칸으로 그리는 것. ★ **CSS 의 일**이다.
- **`white-space`** — 축약을 끄고 켜는 CSS 속성. `<pre>` 는 UA 스타일시트로 `pre` 를 받는다.
- **문자 참조(character reference)** — `&이름;`·`&#10진;`·`&#x16진;` 세 꼴. 셋이 같은 글자를 만든다.
- **이름 참조 표(named character reference table)** — 명세의 참조 이름 목록. **세미콜론 없이도 매칭되는 것**이 따로 표시돼 있다.
- **최장 일치(longest match)** — 참조 이름을 읽을 때 **가장 긴 후보부터** 맞춰 보는 방식.
- **`&nbsp;`(U+00A0)** — 축약되지 않고 줄도 안 갈리는 공백.
- **`textContent`** — 아래 모든 텍스트 노드를 **그대로** 이은 것. **트리를 본다.**
- **`innerText`** — **렌더된 결과**의 글자. 축약·숨김이 반영된다. **화면을 본다.**
- **직렬화(serialization)** — 트리를 다시 글자열로 되쓰는 것. **이스케이프를 새로 만든다.**
