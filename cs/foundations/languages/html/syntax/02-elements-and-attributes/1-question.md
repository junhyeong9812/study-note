# html/syntax/02 — 요소와 속성 문법: 빈 요소·태그 생략·불리언 속성·따옴표 규칙 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 답할 때는 **「트리에 무엇이 담겼나」와 「속성이 몇 개인가」까지** 말한다 — 둘은 다른 창이다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [01번 주제](../01-document-skeleton/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 슬래시가 붙은 태그 넷 (예측)

```html
<!-- html01b-void-slash.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>빈 요소와 슬래시</title>
<p>줄1<br>줄2<br/>줄3<br />줄4</p>
<img src="a.gif" alt="그림"/>
<div class="d"/>여기는 div 안인가?</div>
<span/>뒤</span>
```

- 트리에서 `br` 요소는 몇 개이고 각각 어떻게 직렬화되는가?
- `<div class="d"/>` 뒤의 글자는 div 안인가 밖인가?
- `<span/>뒤</span>` 에서 `뒤` 는 어디에 있는가?
- 이 파일에서 `/` 가 실제로 바꾼 것은 몇 개인가?

### 2. 닫지 않은 태그들 (예측)

```html
<!-- html01b-omit.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>태그 생략</title>
<p>첫 문단
<p>둘째 문단
<ul>
  <li>가
  <li>나
</ul>
<table>
  <tr><td>a<td>b
  <tr><td>c<td>d
</table>
<dl><dt>용어<dd>뜻<dt>용어2<dd>뜻2</dl>
```

- `p`·`li`·`td`·`dt` 는 각각 **무엇이** 닫아 주는가?
- 소스에 없는데 트리에 생긴 요소는 무엇인가?
- 이 파일의 마크업은 유효한가, 아니면 파서가 고친 것인가?
- 둘을 가르는 기준은 무엇인가?

### 3. 다섯 개의 버튼 (예측)

```html
<!-- html01b-boolean.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>불리언 속성</title>
<button id="b1" disabled>속성 이름만</button>
<button id="b2" disabled="">빈 문자열</button>
<button id="b3" disabled="false">false 라고 씀</button>
<button id="b4" DISABLED="DISABLED">대문자</button>
<button id="b5">속성이 없다</button>
<script>
const o = [];
for (const id of ["b1","b2","b3","b4","b5"]) {
  const e = document.getElementById(id);
  o.push(id + "  getAttribute('disabled') = " + JSON.stringify(e.getAttribute("disabled"))
            + "   .disabled = " + e.disabled);
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
```

- 다섯 버튼의 `.disabled` 를 각각 예측하라.
- `getAttribute("disabled")` 가 돌려주는 값은 각각 무엇인가?
- 트리로 직렬화하면 첫 버튼의 속성은 어떻게 적히는가?
- 비활성을 끄는 방법은 무엇인가?

### 4. 대문자로 쓴 태그와 두 번 쓴 속성 (예측)

```html
<!-- html01b-case-dup.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>대소문자와 중복 속성</title>
<P ID="c1" CLASS="Box Big" DATA-Key="Val">대문자로 쓴 태그</P>
<p id="c2" title="첫" title="둘" TITLE="셋">중복 속성</p>
<script>
const o = [];
const c1 = document.getElementById("c1");
o.push("c1 tagName   = " + c1.tagName + "      localName = " + c1.localName);
o.push("c1 속성 이름 = " + [...c1.attributes].map(a => a.name).join(", "));
o.push("c1 class 값  = " + JSON.stringify(c1.getAttribute("class")));
o.push("c1 dataset.key = " + JSON.stringify(c1.dataset.key));
const c2 = document.getElementById("c2");
o.push("c2 속성 개수 = " + c2.attributes.length
       + "   title = " + JSON.stringify(c2.getAttribute("title")));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
```

- `tagName`·`localName`·속성 이름·속성 값 중 대소문자가 바뀌는 것은 어느 것인가?
- `dataset` 으로는 무엇이라고 읽는가?
- `c2` 의 속성은 **몇 개**이고 `title` 은 무엇인가?
- 이 사실을 `--dump-dom` 만으로 알 수 있는가?

### 5. 따옴표를 뺀 세 링크 (예측)

```html
<!-- html01b-unquoted.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>따옴표 없는 속성값</title>
<a id="u1" href=/search?q=a&b title=hello>1</a>
<a id="u2" href=/a/b title=hello world>2</a>
<a id="u3" href=/a/b class=x/y>3</a>
<script>
const o = [];
for (const id of ["u1","u2","u3"]) {
  const e = document.getElementById(id);
  o.push(id + " 속성 = " + [...e.attributes].map(a => a.name + "=" + JSON.stringify(a.value)).join("  "));
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
```

- 세 링크의 속성 목록을 각각 예측하라.
- 내가 쓴 적 없는 속성이 생기는가? 생긴다면 그 값은 무엇인가?
- `class=x/y` 의 `/` 는 값의 일부인가?
- 따옴표 없는 값에 넣으면 안 되는 글자를 셋 대라.

### 6. 「빈 요소」와 「생략 가능 태그」 (경계)

- 이 둘의 정의 차이를 한 문장으로 답하라.
- `br` 과 `li` 는 각각 어느 쪽인가?
- 빈 요소의 목록은 어디서 정해지는가? 내가 늘릴 수 있는가?
- `<div></div>` 와 `<div />` 중 「빈 상자」를 만드는 것은?

### 7. 불리언 속성이 값을 안 보는 이유 (왜)

- `disabled="false"` 가 참인 것을 명세의 어느 규정으로 설명하는가?
- 콘텐츠 속성과 IDL 속성이 각각 무엇을 돌려주는가?
- 템플릿에서 불리언 속성을 안전하게 다루는 형태는 무엇인가?
- `aria-*` 속성은 같은 규칙을 따르는가?

### 8. 중복 속성이 보이지 않는 이유 (경계)

- 버려진 속성의 흔적이 `--dump-dom` 에 남지 않는 이유는?
- 이것을 진단하려면 어느 창을 써야 하는가?
- 「첫 것이 이긴다」가 **보안** 표면이 되는 경우를 설명하라.
- 같은 규칙이 적용되는 다른 자리를 01번 주제에서 하나 찾아라.

### 9. 파스 오류라는 이름 (왜)

- 명세가 `<div />`·중복 속성을 「parse error」라 부르는데 파싱은 왜 안 멈추는가?
- 「파스 오류」와 「무효한 마크업」과 「파싱 실패」 셋의 관계를 정리하라.
- 이 주제의 블록에서 `(exit N)` 이 전부 같은 값인 이유는?
- 그렇다면 무효를 잡아 주는 것은 무엇인가?

### 10. 소스와 트리를 가르기 (연결)

- 이 주제에서 **내가 쓴 것과 트리가 달라진** 자리를 다섯 대라.
- 그중 `--dump-dom` 으로 보이는 것과 안 보이는 것을 갈라라.
- 「소스가 맞다」와 「렌더된 것이 맞다」가 다른 검사인 이유를 이 주제의 예로 답하라.
- 03번 주제가 다루는 「오류 복구」와 이 주제가 다루는 것의 경계는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
