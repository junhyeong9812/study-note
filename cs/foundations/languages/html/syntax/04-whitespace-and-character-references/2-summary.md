# html/syntax/04 — 공백·텍스트·문자 참조: 공백 축약·엔티티·`<pre>` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Character references」](https://html.spec.whatwg.org/multipage/syntax.html#character-references)·[「Tokenizing character references」](https://html.spec.whatwg.org/multipage/parsing.html#tokenizing-character-references)·[「The pre element」](https://html.spec.whatwg.org/multipage/grouping-content.html#the-pre-element), 그리고 **공백 축약은 CSS 쪽**([CSS Text Level 3 의 `white-space` 처리 모델](https://drafts.csswg.org/css-text-3/#white-space-processing)). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 산출이 **조용히 실패**하고 WebKit 은 없다. 이 갈래는 **「이식성」을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 문자 참조의 이름 목록과 파싱 규칙은 **HTML5 이후 고정**돼 있다.
> **선행** — [03번 주제](../03-parser-and-error-recovery/2-summary.md). 파서가 트리를 만드는 규칙 위에서 **텍스트 노드가 어떤 모양이 되는가**를 본다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
===== google-chrome --version =====
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 · 실행 시각 · 프로세스 id | 판이 오르면 바뀐다 |
| **흔들린다** | 스크린샷 픽셀의 안티에일리어싱 | GPU·글꼴 래스터라이저에 달렸다 |
| **흔들린다** | demo 검증의 **높이 픽셀**(`34`·`58`) | 글꼴·줄 높이에 달렸다 — **크고 작음만** 근거로 쓴다 |
| **안 흔들린다** | **`--dump-dom` 트리 전체** | 파싱 알고리즘이 명세에 있다 |
| **안 흔들린다** | **텍스트 노드의 코드포인트 목록** · `childNodes.length` | 〃 |
| **안 흔들린다** | `textContent` 의 글자 수 · `innerText` 의 값 | 파싱 + CSS 처리 모델 |
| **안 흔들린다** | 블록의 `(exit N)` (**전부 0**) | 파서는 실패하지 않는다 |

★ 이 주제는 **코드포인트로 찍는다.** 글자로 찍으면 `&nbsp;` 와 보통 공백이 눈으로 구분이 안 되고, **직렬화가 한 번 더 되쓰기** 때문이다(아래 (6)).

## 한눈에 — 쉽게 말하면

**★ 공백은 두 번 처리된다. 파서가 트리에 넣을 때 한 번, CSS 가 그릴 때 한 번. 둘은 다른 일이다.**

받아쓴 원고를 인쇄하는 과정에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 받아쓴 원고 (띄어쓰기 그대로) | **텍스트 노드**(`textContent`) |
| 조판해서 인쇄한 지면 (여러 칸이 한 칸으로) | **렌더 결과**(`innerText`) |
| 「여기는 원고 그대로 찍어라」 표시 | **`<pre>`**(`white-space: pre`) |
| 「이 자리는 붙여서 찍어라」 특수 공백 | **`&nbsp;`**(U+00A0) |
| 원고에 쓴 약어를 풀어 쓴 것 | **문자 참조**(`&amp;`·`&#38;`·`&#x26;`) |

- **트리에는 내가 쓴 공백이 그대로 있다.** 줄바꿈도 연속 공백도 **안 지워진다.**
- **화면에서 한 칸으로 합쳐지는 것은 CSS 가 하는 일**이다. `white-space` 를 바꾸면 안 합쳐진다.
- 그래서 **「공백이 사라졌다」는 틀린 말**이다 — **트리에는 있고 화면에만 없다.**

```text
   소스              텍스트 노드 (트리)          화면 (렌더)
   가     나         "가     나\n다"             "가 나 다"
   다                 ^^^^^ 공백 5개 그대로       ^^ 한 칸으로

   창 ②  textContent  ->  원고를 본다
   창 ③  innerText    ->  지면을 본다
        ★ 이 둘을 갈라 보는 것이 이 주제의 전부다
```

실무에서 이게 터지는 자리는 **인라인 요소 사이의 줄바꿈**이다.\
`<span>` 을 줄 바꿔 나열하면 **사이에 한 칸이 생긴다** — 소스의 줄바꿈이 텍스트 노드로 남아 렌더에서 한 칸이 되기 때문이다.\
그리고 **`children.length` 와 `childNodes.length` 가 다르다** — 공백 텍스트 노드가 셋 끼어 있다.

> **텍스트 노드(text node)** — 트리에서 글자를 담는 노드. `nodeType` 이 `3`.\
> 예: `<div>\n  <span>가</span>\n</div>` 의 `div` 는 **자식이 셋**이다(공백 · span · 공백).

> **문자 참조(character reference)** — `&이름;`·`&#10진;`·`&#x16진;` 세 꼴로 글자 하나를 적는 표기.\
> 예: `&amp;` · `&#38;` · `&#x26;` 는 전부 `&` 한 글자다.

> **`&nbsp;`(no-break space, U+00A0)** — 줄바꿈이 안 일어나고 **축약되지 않는** 공백.\
> 예: `10&nbsp;kg` 은 `10` 과 `kg` 이 다른 줄로 갈라지지 않는다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. **소스의 공백은 어디까지 남고 어디서 합쳐지나.** 트리와 화면 중 어디서 일어나는 일인가.
2. **`childNodes` 와 `children` 은 왜 다른가.** 그 차이가 코드를 무는 자리는 어디인가.
3. **`<pre>` 는 정확히 무엇을 바꾸나.** 그리고 파서가 `<pre>` 에만 하는 일이 따로 있나.
4. **문자 참조는 어디서 풀리고 어디서 안 풀리나.** 세미콜론을 빼면 무슨 일이 일어나나.

★ 관찰 수단은 [01번 주제](../01-document-skeleton/2-summary.md)에서 세운 **창 ②**(`childNodes`·`textContent`)와 **창 ③**(`innerText` 대 `textContent`)다.\
**이 주제는 창 ③ 이 본체**다 — 「소스가 맞다」와 「렌더된 것이 맞다」가 **다른 검사**라는 것의 가장 선명한 실물이다.

## 동작 방식

### (1) 창 ③ — 공백은 트리에 남고 화면에서만 합쳐진다

**언제 쓰나** — 「빈칸이 왜 사라졌나」·「왜 한 칸이 더 생겼나」를 물을 때마다.

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

```text
   소스                        트리 (textContent)        화면 (innerText)
   가     나                   "가     나\n다"            "가 나 다"
   다                           ^^^^^ 5칸 그대로           ^ 한 칸
                                      ^^ 줄바꿈 그대로      ^ 한 칸

   파서가 하는 일:  글자를 그대로 텍스트 노드에 넣는다      <- 아무것도 안 합친다
   CSS 가 하는 일:  white-space: normal 이면 연속 공백·줄바꿈을 한 칸으로
```

그림 해설 (한 단계씩):

- **`--dump-dom` 에 소스의 공백이 그대로 있다.** 파서는 공백을 **하나도 안 지운다.**
- **합치는 것은 CSS 다.** `white-space` 의 기본값 `normal` 이 **연속 공백과 줄바꿈을 한 칸으로** 만든다.
- ★ 그래서 **이 규칙은 엄밀히 말하면 HTML 규칙이 아니라 CSS 규칙**이다. `white-space: pre` 를 주면 같은 트리가 다르게 그려진다(아래 (3)).
- **창 ②(`textContent`)와 창 ③(`innerText`)이 다른 답을 준다** — 이 주제에서 두 창을 반드시 함께 쓴다.

화면으로 보면 이렇다.

```html demo
<p class="src">가     나
다&nbsp;&nbsp;&nbsp;라</p>
<pre class="src">가     나
다</pre>
<style>
  .src { border: 1px solid #94a3b8; padding: 4px; font: 16px monospace; }
</style>
```

> **보이는 것** — 위 상자는 **한 줄**로 「가 나 다   라」가 나온다. 소스의 다섯 칸과 줄바꿈이 **각각 한 칸**으로 합쳐지고, `&nbsp;` 세 개는 **합쳐지지 않아 넓은 틈**이 남는다. 아래 `<pre>` 상자는 **두 줄**이고 다섯 칸이 **그대로** 보인다.\
> **바꿔 볼 것** — `.src` 에 `white-space: pre` 를 더하기(위 상자가 아래와 똑같아진다) · `&nbsp;` 를 보통 공백으로 바꾸기(넓은 틈이 한 칸으로 줄어든다)

*(Chrome 151 headless 실측 — 창 폭 780 에서, 래퍼를 붙인 사본의 `p` 는 `textContent` 길이 **13** · `innerText` 코드포인트 `U+AC00 U+0020 U+B098 U+0020 U+B2E4 U+00A0 U+00A0 U+00A0 U+B77C` · 높이 **34**, `pre` 는 `textContent` 길이 **9** · `innerText` 에 공백 다섯과 줄바꿈이 그대로 · 높이 **58** 이었다. 높이 픽셀은 「흔들리는 칸」이므로 **두 상자의 높이가 갈린다는 사실**만 근거로 쓴다. 검증 블록은 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.)*

비용 — 없음.

### (2) 창 ② — `childNodes` 에는 공백 텍스트 노드가 보인다

**언제 쓰나** — `children[0]` 과 `childNodes[0]` 중 무엇을 쓸지 고를 때.

(1)의 프로브가 같이 찍은 것이 근거다.

```text
   소스                           d1 의 자식들
   <div id="d1">
     <span>가</span>              #text "\n  "     <- 공백 노드
     <span>나</span>              SPAN
   </div>                         #text "\n  "     <- 공백 노드
                                  SPAN
                                  #text "\n"       <- 공백 노드

   childNodes.length = 5      children.length = 2
                   ^ 텍스트 포함            ^ 요소만
```

그림 해설 (한 단계씩):

- **`childNodes` 는 텍스트 노드까지 센다.** 소스를 들여쓰기만 해도 **공백 노드가 셋** 생긴다.
- **`children` 은 요소만** 센다 — 그래서 **둘의 개수가 다르다.**
- ★ 그래서 **`el.childNodes[0]` 이 첫 자식 요소가 아니다.** 들여쓴 마크업에서는 거의 항상 **공백 텍스트 노드**다.
- **마크업을 한 줄로 붙여 쓰면**(`<div><span>가</span><span>나</span></div>`) 공백 노드가 안 생긴다 — **소스 서식이 트리를 바꾼다.**
- ★ DOM API 표면(`childNodes`·`children`·`firstElementChild`)의 정본은 **web-api 갈래**다. 여기는 **파서가 그런 트리를 만든다는 사실**까지다.

비용 — 없음. **`children` 이나 `firstElementChild` 를 쓰면** 이 자리 전체가 사라진다.

### (3) `<pre>` 가 바꾸는 것 — 그리고 파서가 `<pre>` 에만 하는 일

**언제 쓰나** — 코드 블록·ASCII 그림을 넣을 때.

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

```text
   소스                       트리 (textContent)         왜
   <pre id="a">
   가     나                  "가     나\n다"             ★ <pre> 바로 뒤 줄바꿈 하나가
   다</pre>                                                 파서 단계에서 사라졌다

   <pre id="b">
                              "\n가"                      두 개면 하나만 사라진다
   가</pre>

   <textarea id="c">
   값</textarea>              value = "값"                textarea 도 같은 대우
```

그림 해설 (한 단계씩):

- **`<pre>` 는 CSS 로 `white-space: pre` 를 받는다** — 연속 공백과 줄바꿈이 그대로 그려진다. `innerText` 가 `textContent` 와 **같아진다.**
- ★ **그런데 파서가 따로 하는 일이 하나 있다** — **`<pre>` 시작 태그 바로 뒤의 줄바꿈 하나를 버린다.** 실측에서 `<pre id="a">` 의 `textContent` 가 `"가     나\n다"` 로, **앞의 `\n` 이 없다.**
- **두 개를 쓰면 하나만 사라진다**(`pre#b` 가 `"\n가"`). 곧 **딱 하나**를 버린다.
- **`<textarea>` 도 같은 대우**다 — 실측 `value` 가 `"값"`(앞 줄바꿈 없음).
- ★ 이것이 **「공백 축약은 CSS 일」의 유일한 예외**다. 이 한 가지는 **파서가 한다.**

> **왜 그런 규칙이 있나** — `<pre>` 를 쓸 때 여는 태그와 내용을 **같은 줄에 붙여 쓰기가 불편**하기 때문이다.\
> 그래서 「줄을 바꿔 써도 첫 줄이 비지 않게」 해 주는 편의 규칙이 명세에 들어갔다.

비용 — 없음. **`<pre>` 안의 첫 줄을 일부러 비우고 싶으면 줄바꿈을 두 번** 쓴다.

### (4) 문자 참조 세 꼴과 「세미콜론을 빼면」

**언제 쓰나** — `&`·`<` 를 글자로 쓸 때, URL 을 본문에 적을 때.

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

```text
   소스           코드포인트                          무슨 일이 일어났나
   &amp;          U+0026                              이름 참조
   &#38;          U+0026                              10진 참조
   &#x26;         U+0026                              16진 참조   -> 셋이 같다

   &ampx          U+0026 U+0078       = "&x"          ★ 세미콜론이 없어도 &amp 가 잡히고
                                                          남은 x 가 글자로 붙었다
   &amp;ampx      U+0026 U+0061 U+006D U+0070 U+0078
                                      = "&ampx"       세미콜론을 쓰면 딱 거기까지
   &notit;        U+00AC U+0069 U+0074 U+003B
                                      = "¬it;"        ★ &not 이 잡혀 ¬ 가 됐다
   5 &lt 3        U+0035 U+0020 U+003C U+0020 U+0033
                                      = "5 < 3"       ★ 세미콜론 없이도 풀렸다
   a &lt; b       "a < b"                             정상
   a < b          "a < b"                             ★ 맨 < 도 글자로 남는다
   &unknownzz;    U+0026 … U+003B     = "&unknownzz;" 모르는 이름은 그대로
```

그림 해설 (한 단계씩):

- **세 꼴은 완전히 같다.** `&amp;`·`&#38;`·`&#x26;` 가 전부 `U+0026` 하나다.
- ★ **세미콜론 없이도 풀리는 이름이 있다.** 명세에 「**세미콜론 없이도 매칭되는 이름 목록**」이 따로 있고, `&amp`·`&not`·`&lt` 가 거기 든다.
- 그래서 **`&ampx` 가 `&x` 가 된다** — `&amp` 까지 잡고 `x` 를 남긴다. **내가 쓰려던 글자열과 다르다.**
- **`&notit;` → `¬it;`** 은 그 규칙이 만드는 가장 유명한 함정이다. `&not` 이 잡히고 `it;` 이 글자로 남는다.
- **모르는 이름은 그대로 남는다**(`&unknownzz;`) — 버려지지도, 에러가 나지도 않는다.
- ★ **맨 `<` 도 글자로 남는다**(`a < b`). `<` 뒤에 글자가 안 오면 태그가 아니기 때문이다([03번 주제](../03-parser-and-error-recovery/2-summary.md) (6)).

비용 — 없음. **`&` 를 글자로 쓸 때는 언제나 `&amp;`** 로 쓰면 이 자리 전체가 사라진다.

### (5) ★ 텍스트와 속성값의 규칙이 다르다

**언제 쓰나** — URL 에 `&` 가 든 링크를 쓸 때. **이 절이 이 주제의 가장 놀라운 자리다.**

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

```text
   같은 글자열 "?a=1&copy=3" 을 텍스트와 속성값에 각각 넣으면

   텍스트     ?a=1&copy=3   ->  U+003F 61 3D 31 [U+00A9] 3D 33   = "?a=1©=3"
                                                  ^^^^^^^ ★ © 가 돼 버렸다
   속성값     href="?a=1&copy=3"
                             ->  … U+0026 63 6F 70 79 3D 33      = "?a=1&copy=3"
                                    ^^^^^^ ★ 그대로 남았다

   그런데 뒤에 오는 글자가 다르면 또 갈린다

   텍스트     &copy 2026    ->  "© 2026"
   속성값     href="?x=&copy 2026" -> "?x=© 2026"     ★ 속성값에서도 풀렸다
```

그림 해설 (한 단계씩):

- **속성값 안에서는 규칙이 하나 더 있다** — 세미콜론 없는 이름 참조 뒤에 **`=` 나 영숫자**가 오면 **풀지 않는다.**
- 그래서 `href="?a=1&copy=3"` 은 **안 깨진다.** 이 예외가 **웹에 이미 있는 수많은 URL 을 살리려고** 들어간 것이다.
- ★ **그러나 같은 글자열을 본문 텍스트에 쓰면 깨진다** — 실측에서 `©=3` 이 됐다.
- **뒤에 공백이 오면 속성값에서도 풀린다**(`?x=© 2026`). 곧 **「속성값이면 안전하다」는 틀린 일반화**다.
- 결론 한 줄 — **`&` 는 어디에 쓰든 `&amp;` 로 쓴다.** 예외를 외우는 것보다 싸다.

비용 — 없음.

### (6) 직렬화가 되쓰는 것 — 창 ① 이 보여 주는 것은 소스가 아니다

**언제 쓰나** — `--dump-dom` 출력을 근거로 쓸 때. **이 주제가 그 한계를 드러낸다.**

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

```text
   JS 로 텍스트에 넣은 것            직렬화된 것
   &     ->  &amp;
   <     ->  &lt;
   >     ->  &gt;
   U+00A0 -> &nbsp;
   "     ->  "        (텍스트에서는 그대로)
   '     ->  '

   속성값에서는 " 도 &quot; 가 된다
```

그림 해설 (한 단계씩):

- **직렬화는 트리를 다시 글자열로 되쓰면서 이스케이프를 새로 만든다.** 소스에 `&amp;` 를 안 썼어도 **출력에는 생긴다.**
- ★ 그래서 **`--dump-dom` 출력의 `&nbsp;` 를 보고 「소스에 `&nbsp;` 를 썼구나」로 읽으면 틀린다** — U+00A0 이 거기 있다는 뜻일 뿐이다.
- ★ **이 주제의 블록을 코드포인트로 찍은 이유**가 이것이다. 코드포인트는 **되쓰기를 거치지 않는다.**
- Chrome 151 은 **속성값에서 `<`·`>` 까지** 이스케이프했다. 텍스트 쪽 네 글자(`&`·`<`·`>`·U+00A0)는 명세가 정한 것이고, **속성값의 `<`·`>` 는 이 판의 관찰**이다.

비용 — 없음. **근거는 코드포인트로 잡는다.**

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 문자 참조 세 꼴과 반드시 써야 하는 자리

```text
&amp;   &#38;   &#x26;        세 꼴이 같다 (이름 / 10진 / 16진)

반드시 써야 하는 자리
  텍스트에서   &  ->  &amp;          안 쓰면 뒤 글자에 따라 다른 글자가 된다
  텍스트에서   <  ->  &lt;           뒤에 글자가 오면 태그로 읽힌다
  속성값에서   &  ->  &amp;          뒤에 공백이 오면 풀린다
  속성값에서   "  ->  &quot;         겹따옴표로 감쌌을 때
```

### 금지 사례 — 텍스트에서 하면 안 되는 것

```text
&ampx                    "&x" 가 된다      (세미콜론 없는 이름이 잡힌다)
&notit;                  "¬it;" 가 된다
?a=1&copy=3              "?a=1©=3" 이 된다  (속성값이면 안 깨진다 — 규칙이 다르다)
<pre>
첫 줄</pre>              첫 줄바꿈 하나가 파서에서 사라진다
<span>가</span>
<span>나</span>          사이에 한 칸이 생긴다 (소스 줄바꿈)
```

### 어디서 헷갈리나

- **「공백이 축약된다」는 CSS 규칙**이다. 트리에는 그대로 있다.
- **「`<pre>` 는 공백을 보존한다」도 CSS 규칙**이다. 다만 **첫 줄바꿈 삭제만 파서**가 한다.
- **`childNodes[0]` 은 첫 자식 요소가 아니다.**
- **속성값과 텍스트의 문자 참조 규칙이 다르다** — 속성값 쪽이 **더 관대하지 않고 더 까다롭다**(안 푸는 조건이 더 있다).
- **`--dump-dom` 의 `&amp;`·`&nbsp;` 는 내가 쓴 것이 아닐 수 있다.**

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. 「공백이 사라졌다」고 말한다

**안 사라졌다.** 실측에서 `textContent` 가 `"가     나\n다"` 로 **공백 다섯 개와 줄바꿈이 그대로** 있었다.\
사라진 것처럼 보이는 것은 **CSS 가 그렇게 그린 것**이다. `white-space` 를 바꾸면 돌아온다.

### 2. 인라인 요소를 줄 바꿔 나열하고 「왜 틈이 생기나」 한다

실측에서 `<div>` 의 `childNodes` 가 **5개**(요소 2 + 공백 텍스트 3)였다.\
그 공백 노드가 렌더에서 **한 칸**이 된다. 「`margin: 0` 을 줬는데 틈이 있다」의 원인이다.

### 3. `childNodes[0]` 으로 첫 자식을 잡는다

들여쓴 마크업에서는 거의 항상 **공백 텍스트 노드**다. `children[0]`·`firstElementChild` 를 쓴다.

### 4. `<pre>` 첫 줄이 비는 줄 알고 줄바꿈을 두 번 쓴다

**하나는 파서가 지운다.** 실측에서 `<pre>` 바로 뒤 줄바꿈 하나가 `textContent` 에 없었고, 두 개를 쓰니 하나가 남았다.\
★ **이것만 CSS 가 아니라 파서가 하는 일**이라 `white-space` 를 바꿔도 안 돌아온다.

### 5. URL 을 본문에 그대로 붙여 넣는다

실측에서 `?a=1&copy=3` 이 **`?a=1©=3`** 이 됐다.\
★ **같은 글자열을 `href` 에 넣으면 안 깨진다** — 그래서 「링크는 되는데 본문 글자만 이상하다」가 되어 **원인을 찾기 어렵다.**

### 6. `--dump-dom` 의 `&amp;` 를 소스로 읽는다

실측에서 JS 로 넣은 `&` 가 출력에 `&amp;` 로, U+00A0 이 `&nbsp;` 로 나왔다.\
★ **소스에 그렇게 쓴 적이 없다.** 근거로 쓸 것은 **코드포인트**다.

## 구현 세부사항 대 언어 보장

★ **이 주제는 두 명세에 걸쳐 있다** — 참조 해석과 `<pre>` 첫 줄은 **HTML**, 공백 축약은 **CSS** 다.\
그래서 「누가 보장하나」 칸에 **명세 이름을 갈라 적는다.**

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 파서가 공백을 **하나도 안 지우는 것** | **HTML 명세**(토크나이저) |
| **연속 공백·줄바꿈이 한 칸으로 그려지는 것** | ★ **CSS 명세**(css-text-3 의 `white-space` 처리 모델). **HTML 규칙이 아니다** |
| `<pre>` 가 공백을 보존하는 것 | **CSS**(UA 스타일시트의 `white-space: pre`) |
| ★ **`<pre>`·`<textarea>` 직후 줄바꿈 하나가 사라지는 것** | **HTML 명세**(「in body」의 `pre`/`textarea` 규칙). **이것만 파서가 한다** |
| `childNodes` 에 공백 텍스트 노드가 들어가는 것 | **HTML 명세**(트리 구축) + **DOM 명세**(`childNodes` 의 정의) |
| 문자 참조 세 꼴이 같은 것 | **HTML 명세**(named/decimal/hex) |
| **세미콜론 없는 이름이 매칭되는 것** | **HTML 명세**(「without a semicolon」 목록이 named character reference 표에 있다) |
| **속성값에서 `=`·영숫자가 뒤따르면 안 푸는 것** | **HTML 명세**(「character reference in attribute value state」의 예외) |
| 모르는 이름이 글자 그대로 남는 것 | **HTML 명세** |
| 텍스트 직렬화가 `&`·`<`·`>`·U+00A0 을 되쓰는 것 | **HTML 명세**(직렬화) |
| **속성값 직렬화가 `<`·`>` 까지 되쓰는 것** | ★ **관찰**(Chrome 151). 근거로 쓰지 않는다 |
| demo 검증의 **높이 픽셀**(34·58) | ★ **관찰 + 환경**(글꼴·창 폭 520px). **크고 작음만** 근거로 쓴다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| `&` 를 글자로 쓴다 | **언제나 `&amp;`** | 맨 `&`(뒤 글자에 따라 갈린다) |
| `<` 를 글자로 쓴다 | `&lt;` | 맨 `<`(뒤에 글자가 오면 태그다) |
| 붙여야 할 두 낱말이 있다 | `&nbsp;` | 보통 공백(줄이 갈린다) |
| 여백을 넓히고 싶다 | **CSS**(`margin`·`padding`·`word-spacing`) | `&nbsp;` 를 여러 개 |
| 코드·ASCII 그림을 싣는다 | `<pre>` | `<div>` + `<br>` |
| 인라인 요소를 나란히 둔다 | 줄바꿈을 **주석으로 삼키거나** flex·grid 로 | 그냥 줄 바꿔 나열 |
| 첫 자식 요소를 잡는다 | `firstElementChild` | `childNodes[0]` |
| 글자열을 근거로 싣는다 | **코드포인트** | 눈으로 본 글자 |

판단 규칙 두 줄.

- **「트리에 무엇이 들었나」와 「화면에 무엇이 보이나」를 늘 갈라 묻는다.** 이 주제의 사고는 전부 그 둘을 섞는 데서 난다.
- **참조는 예외를 외우지 말고 전부 이스케이프한다.** 예외가 텍스트와 속성값에서 서로 다르다.

## 핵심 문장

- **파서는 공백을 하나도 안 지운다.** 합치는 것은 **CSS** 다 — 실측에서 `textContent` 에 공백 다섯 개가 그대로 있었다.
- **`childNodes` 와 `children` 이 다르다** — 들여쓴 마크업에서 실측 **5 대 2**. 공백 텍스트 노드가 셋 끼었다.
- **`<pre>` 직후 줄바꿈 하나는 파서가 버린다** — ★ **이 한 가지만 CSS 가 아니라 HTML 이 하는 일**이다.
- **문자 참조 세 꼴은 완전히 같다.** `&amp;`·`&#38;`·`&#x26;` 전부 `U+0026`.
- **세미콜론 없이도 풀리는 이름이 있다** — 실측 `&ampx` → `"&x"`, `&notit;` → `"¬it;"`.
- **텍스트와 속성값의 규칙이 다르다** — 같은 `?a=1&copy=3` 이 **텍스트에서는 `©=3` 이 되고 `href` 에서는 안 깨졌다.** 다만 뒤에 공백이 오면 **속성값에서도 풀린다.**
- **`--dump-dom` 의 `&amp;`·`&nbsp;` 는 내가 쓴 것이 아닐 수 있다** — 직렬화가 만든 것이다. 근거는 **코드포인트**로 잡는다.

## 관련 자료

- [`../README.md`](../README.md) — HTML 문법·API 주제 목록(이 주제는 04번)
- [01번 주제](../01-document-skeleton/2-summary.md) — **창 넷의 정본.** `<head>` 안의 **공백**이 왜 `head` 를 안 닫는지가 거기와 여기의 접점이다
- [02번 주제](../02-elements-and-attributes/2-summary.md) — 속성값 문법의 정본. 여기는 **그 안의 문자 참조**만
- [03번 주제](../03-parser-and-error-recovery/2-summary.md) — **파서가 트리를 만드는 규칙의 정본.**\
  표 안의 공백이 **밀려나지 않는** 이유가 거기와 여기의 접점이다
- [`../../../../data-representation/`](../../../../data-representation/) — **유니코드·인코딩의 정본.**\
  「U+00A0 이 무엇인가」·「UTF-8 이 어떻게 바이트가 되나」는 거기, 여기는 **`&nbsp;` 라는 마크업 수단과 참조 문법**만
- 목록의 **20번 주제**(`lang`·`dir`·양방향 텍스트) — 텍스트가 **어느 방향으로 그려지나**의 정본
- 목록의 **50번 주제**(`meta charset`) — 바이트를 글자로 바꾸는 단계의 정본. 이 주제는 **글자가 된 뒤**부터
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **51번**(`text-wrapping`·`white-space`) — ★ **공백 축약 규칙의 정본은 그쪽**이다. 여기는 「**HTML 이 무엇을 트리에 넣나**」까지
- web-api 갈래 — `childNodes`·`children`·`textContent`·`innerText` 라는 **API 표면의 정본**. 여기는 **파서가 그런 트리를 만든다는 사실**까지

## 용어 풀이

- **텍스트 노드(text node)** — 트리에서 글자를 담는 노드. `nodeType === 3`. 공백만 있는 것도 노드다.
- **공백 축약(white space collapsing)** — 연속 공백·줄바꿈을 한 칸으로 그리는 것. ★ **CSS 의 일**이다.
- **`white-space`** — 그 축약을 끄고 켜는 CSS 속성. `<pre>` 는 UA 스타일시트로 `pre` 를 받는다.
- **문자 참조(character reference)** — `&이름;`·`&#10진;`·`&#x16진;` 세 꼴. 셋이 같은 글자를 만든다.
- **이름 참조 표(named character reference table)** — 명세에 실린 참조 이름 목록. **세미콜론 없이도 매칭되는 것**이 따로 표시돼 있다.
- **`&nbsp;`(U+00A0)** — 축약되지 않고 줄도 안 갈리는 공백.
- **`textContent`** — 요소 아래 모든 텍스트 노드를 **그대로** 이은 것. **트리를 본다.**
- **`innerText`** — **렌더된 결과**의 글자. 축약·숨김이 반영된다. **화면을 본다.**
- **직렬화(serialization)** — 트리를 다시 글자열로 되쓰는 것. **이스케이프를 새로 만든다.**

## 더 들어가면

- **이름 참조 표는 명세가 고정 목록으로 싣고 JSON 으로도 배포**한다(이 판에서 전수로 던져 보지는 않았다). 파서는 그것을 **최장 일치**로 읽는다. `&notin;` 이 있어서 `&notit;` 을 읽을 때도 일단 길게 시도해 보고 실패하면 `&not` 으로 물러난다.
- **「세미콜론 없이도 매칭」이 남은 이유**는 [03번 주제](../03-parser-and-error-recovery/2-summary.md)의 `</br>` 과 같다 — **웹에 이미 있는 문서를 깨지 않으려고** 화석을 명세에 박아 넣은 것이다. 새로 쓰는 문서에서는 **언제나 세미콜론을 쓴다.**
- **`&nbsp;` 로 여백을 만드는 것은 접근성 문제**가 된다. 스크린리더가 그것을 글자로 읽거나 이상한 곳에서 끊을 수 있다. ★ **이 환경에서는 확인할 수 없다**(스크린리더가 없다) — **미실행**이다. 여백은 CSS 로 준다.
- **인라인 요소 사이의 틈을 없애는 관용구**가 몇 개 있다 — 줄바꿈을 주석으로 삼키기(`</span><!--\n--><span>`), 닫는 꺾쇠를 다음 줄로 내리기, 부모에 `font-size: 0`, 그리고 오늘의 답인 **flex·grid**. 앞의 셋은 전부 **「공백 텍스트 노드를 안 만들거나 안 그리게」** 하는 것이다.
- **`<textarea>` 의 값은 속성이 아니라 자식 텍스트**다. 그래서 첫 줄바꿈 삭제 규칙이 여기에도 적용된다. 그 요소의 정본은 목록의 **26번 주제**다.
