# html/syntax/24 — `<input>` 타입 지도 ③ 선택·특수: `checkbox`/`radio`/`file`/`color`/`hidden`/`submit`/`image` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **서버가 받은 필드 목록**에 있다. 칸마다 「**실린다 / 아예 없다**」를 먼저 적고, 실리면 **무슨 값으로**인지 적어라. 「빈 값으로 실린다」와 「없다」는 다른 답이다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [21번 주제](../21-form-submission-model/1-question.md) · [22번 주제](../22-input-types-text/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 스무 칸의 값과 역할 (예측)

```html
<!-- html21b-24-sent.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>24 무엇이 실리나</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post">
<input type="checkbox" name="c1" value="예" checked>
<input type="checkbox" name="c2" value="예">
<input type="checkbox" name="c3" checked>
<input type="radio" name="r1" value="가">
<input type="radio" name="r1" value="나" checked>
<input type="radio" name="r2" value="가">
<input type="radio" name="r2" value="나">
<input type="radio" name="r3" checked>
<input type="file" name="f1">
<input type="hidden" name="h1" value="숨김">
<input type="hidden" name="_charset_" value="아무 값">
<input type="color" name="k1">
<input type="color" name="k2" value="red">
<input type="color" name="k3" value="#ABCDEF">
<input type="color" name="k4" value="아님">
<input type="text" name="x1" value="비활성" disabled>
<input type="text" name="x2" value="읽기 전용" readonly>
<input type="text" value="이름 없음">
<button type="button" name="b0" value="보통 단추">보통 단추</button>
<button id="보냄1" name="s" value="1">보냄 1</button>
<button id="보냄2" name="s" value="2">보냄 2</button>
<input type="image" id="그림" name="img" alt="그림 단추" width="40" height="20" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 요소들 = [...document.getElementById("폼").elements];
const 컨트롤 = [...document.querySelectorAll("#폼 input, #폼 button")];
컨트롤.forEach((e, k) => e.dataset.k = k);
window.__대상 = 컨트롤.map((e, k) => [k, "[data-k='" + k + "']"]);
window.__끝 = () => {
  const O = [칸("태그·type", 16) + 칸("name", 11) + 칸(".value", 16) + 칸(".checked", 9) + "역할"];
  for (const [k, e] of 컨트롤.entries()) {
    const 역할 = __AX[k].역할 || (__AX[k].무시 ? "(무시됨)" : "(없음)");
    O.push(칸(e.tagName.toLowerCase() + "·" + e.type, 16) + 칸(e.name || "(없음)", 11) + 칸(JSON.stringify(e.value), 16)
      + 칸(e.type === "checkbox" || e.type === "radio" ? String(e.checked) : "—", 9) + 역할);
  }
  O.push("");
  O.push("form.elements 의 개수 = " + 요소들.length + " · 폼 안의 input·button 개수 = " + 컨트롤.length);
  O.push("form.elements 에 없는 것 = " + 컨트롤.filter(e => !요소들.includes(e)).map(e => e.tagName.toLowerCase() + "·" + e.type).join(" · "));
  return O.join("\n");
};
window.__표 = "실린";
window.__칸목록 = [
  ["checkbox 체크됨 (value=예)", "c1"], ["checkbox 체크 안 됨", "c2"], ["checkbox 체크됨 (value 없음)", "c3"],
  ["radio 그룹 r1 (나 체크)", "r1"], ["radio 그룹 r2 (아무것도 안 고름)", "r2"], ["radio r3 (value 없음)", "r3"],
  ["file (고른 파일 없음)", "f1"], ["hidden", "h1"], ["hidden name=_charset_", "_charset_"],
  ["color (값 없음)", "k1"], ["color value=red", "k2"], ["color value=#ABCDEF", "k3"], ["color value=아님", "k4"],
  ["text disabled", "x1"], ["text readonly", "x2"], ["text (name 없음)", ""], ["button type=button", "b0"],
  ["제출 단추 s", "s"], ["image 단추의 img.x", "img.x"], ["image 단추의 img.y", "img.y"],
];
window.__시도 = [
  { 이름: "보냄 1 클릭", 단계: [["click", "#보냄1"]] },
  { 이름: "보냄 2 클릭", 단계: [["click", "#보냄2"]] },
  { 이름: "그림 단추 (7, 5) 클릭", 단계: [["clickat", "#그림", 7, 5]] },
  { 이름: "requestSubmit() · 제출자 없음", 단계: [["js", "document.getElementById('폼').requestSubmit(); 1"]] },
];
</script>
</body>
</html>
```

- 폼 안의 `input`·`button` 각각의 `.value`·`.checked`·CDP 역할은?
- `form.elements.length` 와 폼 안의 `input`·`button` 개수는 같은가? 다르면 무엇이 빠지나?

### 2. 네 가지 제출 (예측)

- 1번 폼을 `보냄 1` · `보냄 2` · 그림 단추의 왼쪽 위에서 (7, 5) · 제출자 없는 `requestSubmit()` 으로 각각 보내면, `__칸목록` 의 스무 칸 중 **어느 칸이 실리나**?
- 실리는 칸의 값은 각각 무엇인가? 특히 `c3` · `r3` · `_charset_` · `k2` · `k4` · `f1` 은?
- 네 제출 각각의 「실린 칸 N / 20」은?

### 3. multipart 의 빈 파일 칸 (예측)

```html
<!-- html21b-24-file.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>24 빈 파일 칸</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="멀티" action="/r" method="post" enctype="multipart/form-data">
<input type="file" name="f1">
<input type="checkbox" name="c1" value="예" checked>
<input type="checkbox" name="c2" value="예">
<button id="보냄" name="s" value="멀티">보냄</button>
</form>
<script>
window.__시도 = [{ 이름: "multipart · 파일 안 고름", 단계: [["click", "#보냄"]] }];
</script>
</body>
</html>
```

- 서버가 받는 부분은 몇 개이고, `f1` 부분의 `filename` 과 부분 `Content-Type` 은?

### 4. 라디오 여덟의 켜짐 (예측)

```html
<!-- html21b-24-radio.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>24 라디오 묶음</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="갑"><input type="radio" id="갑1" name="r" value="갑1" checked><input type="radio" id="갑2" name="r" value="갑2"></form>
<form id="을"><input type="radio" id="을1" name="r" value="을1" checked><input type="radio" id="을2" name="r" value="을2"></form>
<input type="radio" id="밖1" name="r" value="밖1" checked><input type="radio" id="밖2" name="r" value="밖2">
<input type="radio" id="밖갑" name="r" value="밖갑" form="갑">
<input type="radio" id="대1" name="R" value="대1" checked>
<div><input type="radio" id="두1" name="d" value="두1" checked><input type="radio" id="두2" name="d" value="두2" checked></div>
<script>
const 목록 = () => [...document.querySelectorAll("input[type=radio]")];
const 찍기 = () => 목록().filter(i => i.checked).map(i => i.id).join(" · ");
window.__시도 = [
  { 이름: "처음 상태", 단계: [], 뒤: "찍기()" },
  { 이름: "을2 클릭", 단계: [["click", "#을2"]], 뒤: "찍기()" },
  { 이름: "밖갑 클릭", 단계: [["click", "#밖갑"]], 뒤: "찍기()" },
  { 이름: "밖2 클릭", 단계: [["click", "#밖2"]], 뒤: "찍기()" },
];
</script>
</body>
</html>
```

- 처음 상태에서 켜진 라디오는?
- `을2` · `밖갑` · `밖2` 를 (각각 새 페이지에서) 누른 뒤 켜진 라디오는?

### 5. 항목 목록의 거름망 (왜)

- 명세의 「항목 목록 만들기」가 칸을 **건너뛰는** 조건 다섯은?
- `readonly` 는 그 목록에 있는가? 그래서 무엇이 되나?

### 6. `value` 없는 체크박스 (왜)

- 명세는 `value` 속성이 없는 체크박스·라디오의 값을 무엇으로 두는가?
- 그 값만 받은 서버가 알 수 없는 것은 무엇인가?

### 7. 그림 단추의 항목 (경계)

- 그림 단추가 실리는 조건과, 실릴 때 항목의 이름·값은?
- 그림 단추에 `name` 이 없으면 항목 이름은 무엇이 되나(명세)?

### 8. 라디오 그룹의 정의 (경계)

- 명세의 「라디오 단추 그룹」을 이루는 조건은?
- 트리에서 폼 밖에 있는 라디오가 어느 폼의 그룹에 드는 경우는? 4번의 어느 시도가 근거인가?

### 9. `color`·`file`·`hidden` 의 특수 규칙 (경계)

- 색 칸이 값을 못 읽으면 무엇이 되고, 빈 값이 될 수 있는가?
- 고른 파일이 없는 파일 칸은 항목 목록에 무엇을 넣는가?
- `hidden` 칸 중 값 대신 다른 것을 보내는 이름은?

### 10. 명세·구현·관찰 가르기 (경계)

- 이 주제에서 명세와 갈린 칸이 있었는가?
- `file`·`color`·`hidden` 의 역할은 HTML-AAM 에서 무엇이고, CDP 트리에서는 무엇인가?
- 「—」 칸이 「안 물어본 것」이 아님을 이 문서는 어떻게 보이는가?

### 11. 정본 경계 긋기 (연결)

- `disabled` 와 `readonly` 가 포커스·검증에서 갈리는 것의 정본은?
- 체크박스의 `click` 리스너 안에서 `checked` 가 이미 뒤집혀 있는 것의 정본은?
- 라디오 그룹에 이름을 주는 것 · 실제 파일 업로드 · `select` 의 다중 선택의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
