# html/syntax/04 — 공백·텍스트·문자 참조: 공백 축약·엔티티·`<pre>` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 이 주제는 **트리와 화면을 갈라서** 답한다 — 「`textContent` 는 무엇이고 `innerText` 는 무엇인가」까지.
> ★ 글자로 답하지 말고 **코드포인트**로 답한다. `&nbsp;` 와 보통 공백은 눈으로 구분되지 않는다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [03번 주제](../03-parser-and-error-recovery/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 칸과 줄바꿈은 어디로 가나 (예측)

```html
<!-- html01b-space.html -->
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
```

- `p1` 의 `textContent` 와 `innerText` 를 각각 예측하라.
- 둘이 다르다면 그 차이를 만든 것은 HTML 인가 CSS 인가?
- `d1` 의 `childNodes.length` 와 `children.length` 는 각각 얼마인가?
- `d1.childNodes[0]` 은 무엇인가?

### 2. `<pre>` 안의 첫 줄 (예측)

```html
<!-- html01b-pre.html -->
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
```

- `pre#a` 의 `textContent` 를 예측하라. 소스와 몇 글자가 다른가?
- `pre#b` 는 어떻게 다른가?
- `textarea#c` 의 `value` 는 무엇인가?
- 이 차이를 만든 것은 CSS 인가 파서인가? 그렇게 판단한 근거는?

### 3. 앰퍼샌드 여덟 줄 (예측)

```html
<!-- html01b-charref.html -->
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
```

- 여덟 문단의 코드포인트를 각각 예측하라.
- 세미콜론이 없는데도 풀리는 것이 있는가? 있다면 왜인가?
- `&notit;` 은 무엇이 되는가?
- 맨 `<` 는 왜 살아남는가?

### 4. 같은 글자열을 텍스트와 속성값에 (예측)

```html
<!-- html01b-charref-attr.html -->
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
```

- `t1` 의 텍스트와 `a1` 의 `href` 는 같은가, 다른가?
- 다르다면 그 규칙은 무엇인가?
- `t2`·`a2` 에서는 왜 또 달라지는가?
- 「속성값에 쓰면 안전하다」는 맞는 말인가?

### 5. 공백이 두 번 처리된다는 뜻 (왜)

- 파서가 하는 일과 CSS 가 하는 일을 각각 한 문장으로 답하라.
- 「공백이 사라졌다」가 틀린 말인 이유는?
- 이 주제에서 **CSS 가 아니라 파서**가 하는 일은 무엇 하나인가?
- 그것이 `white-space` 로 되돌려지지 않는 이유는?

### 6. 인라인 요소 사이의 틈 (경계)

- `<span>` 을 줄 바꿔 나열하면 왜 틈이 생기는가?
- `margin: 0` 으로 없어지지 않는 이유는?
- 그 틈을 없애는 방법을 셋 대라.
- 그중 오늘 권할 만한 것은 무엇인가?

### 7. `&nbsp;` 를 언제 쓰나 (경계)

- `&nbsp;` 와 보통 공백이 다른 점 둘을 대라.
- 여백을 넓히려고 `&nbsp;` 를 여러 개 쓰면 무엇이 문제인가?
- 그 문제를 이 환경에서 확인할 수 있는가?
- 대신 무엇을 쓰는가?

### 8. `--dump-dom` 의 `&amp;` (경계)

- 소스에 `&amp;` 를 안 썼는데 출력에 나올 수 있는가?
- 텍스트와 속성값에서 되쓰기 대상이 되는 글자를 각각 대라.
- 그중 명세가 정한 것과 이 판의 관찰인 것을 갈라라.
- 그래서 이 주제의 근거를 무엇으로 잡아야 하는가?

### 9. 세미콜론 없는 매칭이 남은 이유 (왜)

- 명세가 그 목록을 유지하는 이유를 한 문장으로 답하라.
- 03번 주제의 어떤 규칙이 같은 집안인가?
- 새로 쓰는 문서에서는 어떻게 해야 하는가?
- 파서가 `&notit;` 을 읽을 때 어떤 순서로 시도하는가?

### 10. 정본 경계 긋기 (연결)

- 공백 축약 규칙의 정본은 어느 갈래인가? 여기는 무엇까지인가?
- `childNodes`·`innerText` 라는 API 의 정본은 어느 갈래인가?
- U+00A0 이 어떤 바이트가 되는지는 어느 갈래인가?
- 이 주제가 세 갈래와 겹치면서도 독립 주제인 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
