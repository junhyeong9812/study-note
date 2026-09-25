# html/syntax/07 — `id` 와 조각 식별자: 문서 내 링크·`:target`·스크롤 앵커 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 이 주제는 **스크롤**과 **`:target`** 을 **갈라서** 답한다. 둘은 같이 움직이지만 같은 것이 아니다.
> ★ `scrollY` 는 **절댓값이 아니라** 「**0 인가 · 앞 값과 같은가**」로 답한다. 절댓값은 흔들리는 칸이다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [06번 주제](../06-global-attributes/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 문서를 조각만 바꿔 일곱 번 띄우면 (예측)

```html
<!-- html05b-fragment.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>조각 식별자가 찾는 것</title>
<style>
  body { margin: 0; }
  section { height: 700px; border-top: 2px solid #999; }
</style>
</head>
<body>
<section id="s1">첫째</section>
<section id="s2">둘째</section>
<section id="한글">한글 id</section>
<section id="s4"><a name="옛앵커">name 으로만 준 앵커</a></section>
<section id="쌍둥이">중복 첫째</section>
<section id="쌍둥이">중복 둘째</section>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const o = [];
  const t = document.querySelector(":target");
  o.push("location.hash   = " + JSON.stringify(location.hash));
  o.push("window.scrollY  = " + Math.round(window.scrollY));
  o.push(":target         = " + (t ? t.tagName.toLowerCase() + " / " + JSON.stringify(t.textContent.slice(0, 8)) : "null"));
  o.push("getElementById('쌍둥이') = " + JSON.stringify(document.getElementById("쌍둥이").textContent)
         + "   [id=쌍둥이] 는 " + document.querySelectorAll("[id='쌍둥이']").length + "개");
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
```

- 일곱 판의 `scrollY` 를 **0 인지 아닌지**로 예측하라.
- 일곱 판의 `:target` 을 각각 예측하라.
- `#한글` 로 띄웠을 때 `location.hash` 가 답하는 글자는 무엇인가?
- `#옛앵커`(`<a name>`)와 `#쌍둥이`(`id` 가 둘)는 어떻게 되는가?

### 2. 한 문서에서 조각을 여섯 번 갈아 끼우면 — 두 판 (예측)

```html
<!-- html05b-top.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>#top 과 빈 조각과 없는 조각</title>
<style>
  body { margin: 0; }
  section { height: 700px; border-top: 2px solid #999; }
</style>
</head>
<body>
<section id="s1">첫째</section>
<section id="s2">둘째</section>
<section id="top">id 가 top 인 칸</section>
<section id="s4">넷째</section>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
  const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
  const o = [];
  const 간다 = (h, 설명) => { location.hash = h; o.push(pad("location.hash = " + JSON.stringify(h), 34)
      + "scrollY = " + pad(String(Math.round(window.scrollY)), 6) + 설명); };
  o.push(pad("처음", 34) + "scrollY = " + Math.round(window.scrollY));
  간다("#s4", "맞는 id 가 있다");
  간다("#top", "id 가 top 인 칸이 있다");
  간다("#s4", "");
  간다("#", "빈 조각");
  간다("#s4", "");
  간다("#없는이름", "맞는 것이 아무것도 없다");
  o.push("");
  o.push("마지막 :target = " + document.querySelector(":target")
         + "   location.hash = " + JSON.stringify(decodeURIComponent(location.hash)));
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
```

```html
<!-- html05b-top-none.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>#top — 맞는 id 가 없을 때</title>
<style>
  body { margin: 0; }
  section { height: 700px; border-top: 2px solid #999; }
</style>
</head>
<body>
<section id="s1">첫째</section>
<section id="s2">둘째</section>
<section id="s3">셋째 — id 가 top 인 칸이 없다</section>
<section id="s4">넷째</section>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
  const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
  const o = [];
  const 간다 = (h, 설명) => { location.hash = h; o.push(pad("location.hash = " + JSON.stringify(h), 34)
      + "scrollY = " + pad(String(Math.round(window.scrollY)), 6) + 설명); };
  o.push(pad("처음", 34) + "scrollY = " + Math.round(window.scrollY));
  간다("#s4", "맞는 id 가 있다");
  간다("#top", "id 가 top 인 칸이 없다");
  간다("#s4", "");
  간다("#", "빈 조각");
  간다("#s4", "");
  간다("#없는이름", "맞는 것이 아무것도 없다");
  o.push("");
  o.push("마지막 :target = " + document.querySelector(":target")
         + "   location.hash = " + JSON.stringify(decodeURIComponent(location.hash)));
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
```

- 두 판이 다른 것은 **한 군데**다. 어디인가?
- 여섯 줄의 `scrollY` 를 두 판 각각 예측하라.
- 두 판이 갈리는 줄은 몇 번째인가?
- 마지막 `:target` 을 두 판 다 예측하라.

### 3. 네 가지 경계값 이름표 (예측)

```html
<!-- html05b-id-edge.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>id 값의 경계</title>
</head>
<body>
<p id="">빈 id</p>
<p id="a b">공백이 든 id</p>
<p id="3a">숫자로 시작하는 id</p>
<p id=" 앞뒤공백 ">앞뒤에 공백이 있는 id</p>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
const 본다 = (설명, f) => { try { o.push(pad(설명, 32) + "-> " + f()); } catch (e) { o.push(pad(설명, 32) + "-> " + e.name); } };
const 글자 = e => e === null ? "null" : JSON.stringify(e.textContent);
본다('getElementById("")',          () => 글자(document.getElementById("")));
본다('getElementById("a b")',       () => 글자(document.getElementById("a b")));
본다('getElementById("3a")',        () => 글자(document.getElementById("3a")));
본다('getElementById(" 앞뒤공백 ")', () => 글자(document.getElementById(" 앞뒤공백 ")));
본다('getElementById("앞뒤공백")',   () => 글자(document.getElementById("앞뒤공백")));
본다('querySelector("#3a")',        () => 글자(document.querySelector("#3a")));
본다('querySelector("[id=\'3a\']")', () => 글자(document.querySelector("[id='3a']")));
본다('querySelector("#\\\\33 a")',   () => 글자(document.querySelector("#\\33 a")));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
```

- 여덟 줄의 결과를 각각 예측하라.
- `getElementById("")` 는 무엇을 주는가?
- 공백이 든 이름은 찾을 수 있는가? 앞뒤 공백은 깎이는가?
- `querySelector("#3a")` 는 무엇을 하는가?

### 4. 유일성은 누가 강제하나 (왜)

- `id` 가 유일해야 한다고 정한 것은 누구인가?
- 중복이면 무엇이 일어나는가? 에러가 나는가?
- `getElementById` 가 주는 것은 몇 번째인가? 그 규칙은 어디 있는가?
- 같은 중복이 [06번 주제](../06-global-attributes/1-question.md)의 전역 이름에서는 어떤 모양으로 드러났는가?

### 5. 스크롤과 `:target` 이 갈리는 자리 (경계)

- 조각 식별자가 하는 일 둘을 대라.
- 그 둘이 **같이** 일어나는 경우와 **하나만** 일어나는 경우를 각각 대라.
- `:target` 은 한 문서에 몇 개까지 있을 수 있는가?
- 그래서 `:target` 으로 만들 수 없는 UI 는 무엇인가?

### 6. 아무것도 못 찾았을 때 셋 (경계)

- `#없는이름`·빈 `#`·`#top` 이 각각 어디로 가는가?
- 셋 중 **스크롤 위치를 안 바꾸는** 것은?
- `#top` 의 답이 문서에 따라 갈리는 이유는?
- 실패했을 때 `location.hash` 는 어떻게 되는가?

### 7. 옛 앵커의 오늘 (경계)

- `<a name="x">` 가 아직 하는 일은 무엇인가?
- `<a name="x">` 가 **하지 못하는** 일은 무엇인가?
- 그 둘이 갈리는 이유는 무엇인가?
- 새 문서에 써도 되는가?

### 8. 한글 이름표와 주소 (경계)

- 한글 `id` 로 문서 내 링크를 걸면 동작하는가?
- `location.hash` 가 답하는 글자는 내가 쓴 것과 같은가?
- 퍼센트 인코딩해서 넣은 것과 그냥 넣은 것의 결과가 같은가?
- `location.hash === "#한글"` 로 비교하면 무슨 일이 일어나는가?

### 9. 두 가지 찾기 (경계)

- `getElementById` 와 `querySelector("#…")` 는 무엇을 근거로 비교하는가?
- 둘이 갈리는 `id` 값을 하나 대라.
- 갈릴 때 뒤엣것은 무엇을 하는가?
- 그 상황을 우회하는 방법 둘을 대라.

### 10. 서버는 무엇을 받나 (연결)

- `/문서.html?tab=2#s2` 에서 서버가 받는 것은 어디까지인가?
- 그래서 `#` 상태를 서버 렌더에 쓸 수 있는가?
- `#` 을 바꾸면 문서를 다시 받는가?
- 이 답의 근거는 실행인가 명세인가?

### 11. 정본 경계 긋기 (연결)

- `:target` 을 선택자로 다루는 정본은 어느 갈래인가? 여기는 무엇까지인가?
- `getElementById`·`scrollIntoView` 라는 API 의 정본은 어느 갈래인가?
- 전역 속성으로서의 `id` 의 정본은 어느 주제인가?
- 바깥으로 나가는 링크(`target`·`rel`)의 정본은 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
