# html/syntax/21 — `<form>` 의 제출 모델: `action`/`method`/`enctype`·제출을 일으키는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **서버가 받은 요청**에 있다. 답할 때마다 「**질의**」·「**본문**」·「**`Content-Type`**」 중 **어느 칸**의 이야기인지, 그리고 페이지에서 **`submit`·`invalid` 가 났나**를 같이 적어라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 모든 페이지는 `html21b-rec.js`(`click`·`invalid`·`submit` 기록기 — [2-summary.md](2-summary.md) 의 「동작 방식」 첫머리)를 싣는다. 단추는 **진짜 마우스**로, Enter 는 **진짜 키**로 눌렀다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [05번 주제](../05-content-categories-and-models/1-question.md) · [17번 주제](../17-table-structure/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여덟 폼이 싣는 자리 (예측)

```html
<!-- html21b-21-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 무엇이 서버에 실리나</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="g1" action="/r" method="get"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b1">보냄</button></form>
<form id="g2" action="/r" method="get" enctype="multipart/form-data"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b2">보냄</button></form>
<form id="g3" action="/r" method="get" enctype="text/plain"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b3">보냄</button></form>
<form id="p1" action="/r" method="post"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b4">보냄</button></form>
<form id="p2" action="/r" method="post" enctype="multipart/form-data"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b5">보냄</button></form>
<form id="p3" action="/r" method="post" enctype="text/plain"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b6">보냄</button></form>
<form id="x1" action="/r" method="put"><input name="q" value="한 글"><button id="b7">보냄</button></form>
<form id="x2" method="post"><input name="q" value="한 글"><button id="b8">보냄</button></form>
<script>
window.__표 = "싣기";
window.__시도 = [
  { 이름: "GET · urlencoded(기본)", 단계: [["click", "#b1"]] },
  { 이름: "GET · multipart/form-data", 단계: [["click", "#b2"]] },
  { 이름: "GET · text/plain", 단계: [["click", "#b3"]] },
  { 이름: "POST · urlencoded(기본)", 단계: [["click", "#b4"]] },
  { 이름: "POST · multipart/form-data", 단계: [["click", "#b5"]] },
  { 이름: "POST · text/plain", 단계: [["click", "#b6"]] },
  { 이름: "method=put", 단계: [["click", "#b7"]] },
  { 이름: "action 없음 · POST", 단계: [["click", "#b8"]] },
];
</script>
</body>
</html>
```

- 여덟 시도 각각에서 서버가 받는 **메서드**는?
- 필드는 **질의**에 실리나 **본문**에 실리나?
- `Content-Type` 헤더는 각각 무엇인가?
- `POST · text/plain` 의 본문은 한 글자씩 무엇인가? `s` 값은 어떻게 적히나?
- `action` 이 없는 폼은 어디로 보내는가?

### 2. 열여섯 시도의 제출 (예측)

```html
<!-- html21b-21-trigger.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 제출을 일으키는 것</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="가" action="/r"><input name="q" value="1"><button id="가단추">보냄</button></form>
<form id="가빈" action="/r"><input name="q" required><button id="가빈단추">보냄</button></form>
<form id="나" action="/r"><input name="q" value="1"></form>
<form id="나빈" action="/r"><input name="q" required></form>
<form id="다" action="/r"><input name="q" value="1"><input name="r" value="2"></form>
<form id="라" action="/r"><input name="q" value="1"><input type="checkbox" name="c" checked></form>
<form id="마" action="/r"><input name="q" value="1"><button id="마단추" disabled>보냄</button></form>
<form id="바" action="/r"><input name="q" value="1"><button id="바단추" type="button">누름</button></form>
<form id="사" action="/r"><input name="q" value="1"><button id="사단추" type="zzz">누름</button></form>
<script>
window.__표 = "제출";
const 폼 = id => "document.getElementById('" + id + "')";
window.__시도 = [
  { 이름: "가 · 제출 단추 클릭", 단계: [["click", "#가단추"]] },
  { 이름: "가 · 칸에서 Enter", 단계: [["enter", "#가 [name=q]"]] },
  { 이름: "가 · form.submit()", 단계: [["js", 폼("가") + ".submit(); 1"]] },
  { 이름: "가 · form.requestSubmit()", 단계: [["js", 폼("가") + ".requestSubmit(); 1"]] },
  { 이름: "가빈 · 제출 단추 클릭", 단계: [["click", "#가빈단추"]] },
  { 이름: "가빈 · 칸에서 Enter", 단계: [["enter", "#가빈 [name=q]"]] },
  { 이름: "가빈 · form.submit()", 단계: [["js", 폼("가빈") + ".submit(); 1"]] },
  { 이름: "가빈 · form.requestSubmit()", 단계: [["js", 폼("가빈") + ".requestSubmit(); 1"]] },
  { 이름: "나 · 단추 없음 · 칸 하나 · Enter", 단계: [["enter", "#나 [name=q]"]] },
  { 이름: "나빈 · 단추 없음 · 칸 하나 · Enter", 단계: [["enter", "#나빈 [name=q]"]] },
  { 이름: "다 · 단추 없음 · 칸 둘 · Enter", 단계: [["enter", "#다 [name=q]"]] },
  { 이름: "라 · 단추 없음 · 칸+체크박스 · Enter", 단계: [["enter", "#라 [name=q]"]] },
  { 이름: "마 · disabled 단추 · Enter", 단계: [["enter", "#마 [name=q]"]] },
  { 이름: "바 · type=button 클릭", 단계: [["click", "#바단추"]] },
  { 이름: "바 · type=button · Enter", 단계: [["enter", "#바 [name=q]"]] },
  { 이름: "사 · type=zzz 클릭", 단계: [["click", "#사단추"]] },
];
</script>
</body>
</html>
```

- 각 시도에서 `submit` 이벤트가 나는가? `invalid` 는?
- 각 시도에서 서버가 받는 요청은 몇 번인가?
- `가 · 칸에서 Enter` 에서 `가단추` 의 `click` 의 `detail` 은 무엇인가?
- `가빈 · form.submit()` 에서 서버에 실리는 `q` 는?
- `라` 의 질의에는 무엇이 실리는가?

### 3. 단추가 덮으면 (예측)

```html
<!-- html21b-21-override.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 단추마다 덮기</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="겟폼" action="/r" method="get">
  <input name="q" value="한 글">
  <button id="기본">폼의 설정</button>
  <button id="덮음" formaction="/r2" formmethod="post">formaction · formmethod</button>
  <input type="submit" id="입력덮음" formaction="/r3" formmethod="post" value="input 쪽">
  <button id="글자" formmethod="post" formenctype="text/plain">formmethod · formenctype</button>
</form>
<form id="포스트폼" action="/r" method="post" enctype="text/plain">
  <input name="q" value="한 글">
  <button id="글자2">폼의 설정</button>
  <button id="빈덮음" formmethod="">formmethod=""</button>
</form>
<script>
const 폼 = id => "document.getElementById('" + id + "')";
window.__시도 = [
  { 이름: "겟폼 · 폼의 설정", 단계: [["click", "#기본"]] },
  { 이름: "겟폼 · button formaction·formmethod", 단계: [["click", "#덮음"]] },
  { 이름: "겟폼 · input formaction·formmethod", 단계: [["click", "#입력덮음"]] },
  { 이름: "겟폼 · formmethod=post formenctype=text/plain", 단계: [["click", "#글자"]] },
  { 이름: "겟폼 · requestSubmit(#덮음)", 단계: [["js", 폼("겟폼") + ".requestSubmit(" + 폼("덮음") + "); 1"]] },
  { 이름: "포스트폼 · 폼의 설정", 단계: [["click", "#글자2"]] },
  { 이름: "포스트폼 · formmethod=\"\"", 단계: [["click", "#빈덮음"]] },
];
</script>
</body>
</html>
```

- 일곱 시도 각각의 **메서드 · 경로 · `Content-Type`** 은?
- `겟폼 · formmethod=post formenctype=text/plain` 의 본문은 무엇인가?
- `포스트폼 · formmethod=""` 의 메서드와 질의는?

### 4. 입력이 속하는 폼 (예측)

```html
<!-- html21b-21-owner.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 어느 form 에 속하나</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="갑" action="/r"><input id="i1" name="안" value="1"><button id="갑단추">보냄</button></form>
<input id="i2" name="form속성" value="2" form="갑">
<input id="i3" name="그냥밖" value="3">
<form id="을" action="/r2"><input id="i4" name="을안인데갑" value="4" form="갑"></form>
<input id="i5" name="없는폼" value="5" form="없음">
<table><form id="병" action="/r3"><tr><td><input id="i6" name="표안" value="6"><input type="submit" id="병단추" value="보냄"></td></tr></form></table>
<form id="겉" action="/r4"><form id="속" action="/r5"><input id="i7" name="중첩" value="7"><button id="속단추">보냄</button></form></form>
<script>
window.__시도 = [
  { 이름: "갑의 단추", 단계: [["click", "#갑단추"]] },
  { 이름: "표 안의 form 병의 단추", 단계: [["click", "#병단추"]] },
  { 이름: "form 안의 form 의 단추", 단계: [["click", "#속단추"]] },
];
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
window.__끝 = () => {
  const O = [칸("id", 8) + 칸("name", 14) + 칸("부모", 10) + "input.form"];
  for (const i of document.querySelectorAll("input")) {
    const 부모 = i.parentElement.tagName.toLowerCase() + (i.parentElement.id ? "#" + i.parentElement.id : "");
    O.push(칸(i.id, 8) + 칸(i.name || "(없음)", 14) + 칸(부모, 10) + (i.form ? "form#" + i.form.id : "null"));
  }
  O.push("");
  O.push("form 개수 = " + document.forms.length + " · id = " + [...document.forms].map(f => f.id).join(" · "));
  O.push("form#병 의 자식 수 = " + document.getElementById("병").childNodes.length
    + " · form#병.elements.length = " + document.getElementById("병").elements.length);
  O.push("form#갑.elements = " + [...document.getElementById("갑").elements].map(e => e.id).join(" · "));
  return O.join("\n");
};
</script>
</body>
</html>
```

- `i1`\~`i7` 과 `병단추` 각각의 **부모**와 **`input.form`** 은?
- `document.forms.length` 는? `form#병` 의 자식 수와 `elements.length` 는?
- 세 단추를 각각 누르면 **경로**와 **필드**는?

### 5. 검증과 `curl` (예측)

```html
<!-- html21b-21-guard.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 클라이언트 검증</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="막음" action="/r" method="post">
  <input type="email" name="addr" value="아무 글자" required>
  <input type="number" name="age" value="-5" min="0">
  <button id="막음단추">보냄</button>
</form>
<form id="안막음" action="/r" method="post" novalidate>
  <input type="email" name="addr" value="아무 글자" required>
  <input type="number" name="age" value="-5" min="0">
  <button id="안막음단추">보냄</button>
</form>
<script>
window.__시도 = [
  { 이름: "검증 있음", 단계: [["click", "#막음단추"]] },
  { 이름: "novalidate", 단계: [["click", "#안막음단추"]] },
];
</script>
</body>
</html>
```

- 두 단추를 누르면 각각 페이지 기록과 서버 요청은?
- 같은 본문 `addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5` 를 `curl --data` 로 `/r` 에 보내면 서버의 필드는?

### 6. `form` 넷의 트리 (예측)

```html
<!-- html21b-21-ax.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 폼의 역할</title>
</head>
<body>
<form action="/r"><input name="q" aria-label="이름 없는 폼의 칸"></form>
<form action="/r" name="폼이름"><input name="q" aria-label="name 속성만 있는 폼의 칸"></form>
<form action="/r" aria-label="검색 조건"><input name="q" aria-label="aria-label 폼의 칸"></form>
<form action="/r" title="툴팁 제목"><input name="q" aria-label="title 폼의 칸"></form>
</body>
</html>
```

- CDP 접근성 트리에서 네 `form` 의 **역할**과 **이름**은?

### 7. GET 과 `enctype` (왜)

- 명세의 제출 알고리즘에서 GET 은 어느 단계로 가며, 그 단계는 무엇을 돌리는가?
- 그래서 GET 폼에 `multipart/form-data` 를 주면 파일은 어디로 가는가?

### 8. `submit()` 과 `requestSubmit()` (왜)

- 명세는 `submit()` 에서 온 제출을 어느 덩어리에서 빼는가?
- 스크립트로 보내면서 검증과 `submit` 리스너를 거치게 하려면 무엇을 부르는가?

### 9. Enter 가 제출하는 조건 (경계)

- 제출 단추 없이 아이디 칸과 비밀번호 칸만 있는 로그인 폼에서 Enter 는 무엇을 하는가?
- 체크박스·`type="button"` 단추는 그 조건의 어느 항에 드는가, 안 드는가?
- 기본 단추가 `disabled` 면 Enter 는 무엇을 하는가?

### 10. 명세·구현·관찰 가르기 (경계)

- 이 주제에서 **Chrome 이 명세와 갈린 자리**는 어디인가? 명세의 어느 문장과 갈리는가?
- 하네스가 「제출이 났나」를 가른 방법의 근거는 명세의 어느 문장이고, 그중 무엇이 관찰인가?
- 「검증이 돌았나」를 `invalid` 이벤트로 묻는 창이 **못 보는 것**은?

### 11. 이 판이 못 보는 것 (경계)

- 이름 없는 `form` 이 랜드마크가 아니라는 것을 이 판이 증명했는가? 그것은 제 몇의 상태인가?
- 서버가 「이 요청은 브라우저의 검증을 거쳤다」를 알 수 있는가? 근거가 된 블록은?

### 12. 정본 경계 긋기 (연결)

- `form` 안의 `form` 과 표 안의 `form` 이 **트리를 어떻게 바꾸나**의 정본은?
- Enter → `click` → `submit` 사슬과 그 `click` 을 막으면 무엇이 되나의 정본은?
- 폼과 같은 본문을 스크립트로 만드는 것 · `button` 의 `type` 과 `form` 속성 · 검증 상태의 정본은?
- HTTP `POST` 의 연혁은 어디에 있고, 거기에 본문 형식 절이 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
