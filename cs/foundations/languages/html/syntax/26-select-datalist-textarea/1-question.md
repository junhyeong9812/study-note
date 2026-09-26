# html/syntax/26 — `select`/`option`/`optgroup`·`datalist`·`textarea` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **서버가 받은 필드 목록과 바이트**에 있다. 칸마다 「**실린다 / 아예 없다 / 빈 값으로 실린다**」를 먼저 가르고, 실리면 **몇 번 · 무슨 값으로**인지 적어라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [24번 주제](../24-input-types-choice-special/1-question.md) · [04번 주제](../04-whitespace-and-character-references/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `select` 열 개의 선택 상태 (예측)

```html
<!-- html25b-26-sent.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>26 무엇이 실리나</title>
<script src="html25b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post">
<select name="s1"><option value="a">가</option><option value="b">나</option></select>
<select name="s2"><option value="a" disabled>가</option><option value="b">나</option></select>
<select name="s3" multiple><option value="a">가</option><option value="b">나</option></select>
<select name="s4" multiple><option value="a" selected>가</option><option value="b">나</option><option value="c" selected>다</option></select>
<select name="s5"><option>  가   나  </option></select>
<select name="s6"><option value="" selected>고르세요</option><option value="b">나</option></select>
<select name="s7"><option value="a" selected>가</option><option value="b" selected>나</option></select>
<select name="s8" size="3"><option value="a">가</option><option value="b">나</option></select>
<select name="s9"><option value="a" disabled>가</option><option value="b" disabled>나</option></select>
<select name="s10"><option label="짧게">긴 글자</option></select>
<input name="d1" id="d1" list="목록">
<datalist id="목록"><option value="서울"></option><option value="부산"></option><input name="d2" value="목록 안의 칸"></datalist>
<textarea name="t1" value="속성 값">
첫 줄
둘째 줄</textarea>
<textarea name="t2" id="t2"></textarea>
<button id="보냄" name="b" value="보냄">보냄</button>
<button id="멀티" name="b" value="멀티" formenctype="multipart/form-data">멀티</button>
</form>
<script>
document.getElementById("t2").value = "첫\r둘\r\n셋\n넷";
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
window.__끝 = () => {
  const O = [칸("name", 5) + 칸("multiple·size", 15) + 칸(".value", 12) + 칸("selectedIndex", 14) + "selectedOptions"];
  for (const e of document.querySelectorAll("select")) {
    O.push(칸(e.name, 5) + 칸((e.multiple ? "multiple" : "—") + (e.hasAttribute("size") ? " size=" + e.size : ""), 15) + 칸(JSON.stringify(e.value), 12)
      + 칸(String(e.selectedIndex), 14) + JSON.stringify([...e.selectedOptions].map(o => o.value)));
  }
  O.push("");
  O.push("datalist 안의 input — willValidate=" + document.querySelector("[name=d2]").willValidate + " · form.elements 에 있나=" + [...document.getElementById("폼").elements].includes(document.querySelector("[name=d2]")));
  return O.join("\n");
};
window.__표 = "실린";
window.__칸목록 = [
  ["select · 고른 것 없음", "s1"], ["select · 첫 option 이 disabled", "s2"], ["select multiple · 고른 것 없음", "s3"],
  ["select multiple · 둘 고름", "s4"], ["select · value 없는 option", "s5"], ["select · value=\"\" 고름", "s6"],
  ["select · selected 둘", "s7"], ["select size=3 · 고른 것 없음", "s8"], ["select · option 전부 disabled", "s9"], ["option label=짧게 · 글자=긴 글자", "s10"],
  ["input list · 목록 밖 값", "d1"], ["datalist 안의 input", "d2"], ["textarea (자식 텍스트)", "t1"], ["textarea (스크립트 값)", "t2"],
];
window.__시도 = [
  { 이름: "목록 밖 값을 치고 보냄 클릭", 단계: [["type", "#d1", "목록에 없는 곳"], ["click", "#보냄"]] },
  { 이름: "목록 밖 값을 치고 멀티 클릭", 단계: [["type", "#d1", "목록에 없는 곳"], ["click", "#멀티"]] },
];
</script>
</body>
</html>
```

- `select` 마다 `.value` · `selectedIndex` · `selectedOptions` 의 값들은?
- `datalist` 안의 `input` 의 `willValidate` 와, 그것이 `form.elements` 에 있는가?

### 2. 목록 밖 글자를 치고 보내면 (예측)

- 1번 폼의 `d1` 에 「목록에 없는 곳」을 진짜로 치고 `보냄`(urlencoded)·`멀티`(multipart)를 각각 누르면, `__칸목록` 의 열네 칸 중 어느 칸이 실리나?
- `s4` 는 본문에 어떤 모양으로 실리나? `s5` · `s6` · `s7` · `s10` 의 값은?
- `t1` · `t2` 의 줄바꿈은 본문에서 무슨 바이트가 되나?

### 3. `textarea` 다섯의 세 시점 (예측)

```html
<!-- html25b-26-textarea.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>26 textarea 의 값</title>
</head>
<body>
<form id="폼">
<textarea id="t1" value="속성 값">
첫 줄
둘째 줄</textarea>
<textarea id="t2">

앞에 빈 줄</textarea>
<textarea id="t3">원래</textarea>
<textarea id="t4">원래</textarea>
<textarea id="t5"></textarea>
</form>
<script>
const J = v => JSON.stringify(v);
const t = id => document.getElementById(id);
const O = [];
const 찍기 = (무엇) => {
  O.push("── " + 무엇);
  for (const id of ["t1", "t2", "t3", "t4", "t5"]) {
    const e = t(id);
    O.push("  " + id + "  .value=" + J(e.value) + "  textContent=" + J(e.textContent) + "  defaultValue=" + J(e.defaultValue)
      + "  getAttribute('value')=" + J(e.getAttribute("value")) + "  textLength=" + e.textLength);
  }
};
찍기("파싱 직후");
t("t3").textContent = "바뀐 자식";          // 스크립트가 값을 건드린 적 없는 칸의 자식을 바꾼다
t("t4").value = "스크립트 값";              // 값을 먼저 넣고
t("t4").textContent = "바뀐 자식";          // 그다음 자식을 바꾼다
t("t5").value = "첫\r둘\r\n셋\n넷";
찍기("스크립트가 t3 자식 · t4 값→자식 · t5 값을 바꾼 뒤");
t("폼").reset();
찍기("form.reset() 뒤");
t("t4").value = "스크립트 값";
document.body.append(Object.assign(document.createElement("script"), { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
window.__끝 = () => O.join("\n");
</script>
</body>
</html>
```

- 세 시점(파싱 직후 · 스크립트가 바꾼 뒤 · `form.reset()` 뒤)마다 `t1`\~`t5` 의 `.value` · `textContent` · `defaultValue` · `getAttribute('value')` · `textLength` 는?
- 스크립트가 끝난 뒤 `--dump-dom` 에 `t2` 와 `t4` 는 어떻게 직렬화되나?

### 4. `optgroup`·`datalist`·`textarea` 의 트리 (예측)

```html
<!-- html25b-26-ax.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>26 트리</title>
</head>
<body>
<label>하나 <select><optgroup label="과일"><option>사과</option><option selected>배</option></optgroup><optgroup label="채소" disabled><option>무</option></optgroup></select></label>
<label>여럿 <select multiple><optgroup label="과일"><option selected>사과</option><option>배</option></optgroup><option>기타</option></select></label>
<label>줄임 <select><option label="짧게">긴 글자</option></select></label>
<label>도시 <input list="목록"></label><datalist id="목록"><option value="서울"></option><option value="부산"></option></datalist>
<label>메모 <textarea></textarea></label>
</body>
</html>
```

- 접근성 트리에서 두 `select` 는 어떤 층으로 찍히고, `optgroup` 의 이름은? `disabled` 인 `optgroup` 의 선택지에는 무엇이 붙나?
- `줄임` 의 선택지 이름은? `datalist` 는 트리 어디에 있나?

### 5. 단일 `select` 의 「안 고름」 (왜)

- 명세의 selectedness setting algorithm 이 첫 선택지를 고르는 조건은? `size=3` 이면 왜 안 도나?
- 서버가 「사용자가 아무것도 안 골랐다」를 알려면 마크업을 어떻게 해야 하나?

### 6. `option` 의 값과 이름 (왜)

- `value` 가 없는 `option` 의 값은 명세상 무엇이고, 공백은 어떻게 되나?
- `label` 속성은 값과 트리 이름 중 무엇을 바꾸나?

### 7. `textarea` 의 값이 사는 자리 (왜)

- 원 값 · API 값 · 값은 각각 어디에 쓰이고 줄바꿈이 어떻게 다른가?
- 자식 텍스트를 바꿨을 때 `.value` 가 따라오는 조건은?
- 첫 줄바꿈이 파서에서 사라지는데 직렬화가 되살리지 않으면 무슨 일이 생기나?

### 8. `datalist` 의 두 문장 (경계)

- `datalist` 조상을 가진 칸에 걸린 명세 문장 둘은? 이 판은 각각 지켰나?
- `datalist` 로 입력을 제한할 수 있나? 제한이 필요하면?

### 9. 명세·구현·관찰 가르기 (경계)

- 이 주제에서 명세와 갈린 칸은 몇 개이고 어디인가?
- 「단일 `select` 를 `combobox` → `MenuListPopup` 으로 찍는다」는 어느 층인가?

### 10. 이 판이 못 보는 것 (경계)

- 선택 창·자동완성 줄을 이 판이 못 보는 이유는?
- `wrap="hard"` 의 결과를 이 판이 싣지 않은 이유는?

### 11. 정본 경계 긋기 (연결)

- 「안 실린다」를 증명하는 격자 방식 · 첫 줄바꿈을 파서가 지우는 것의 정본은?
- 필수 `select` 의 빈 선택지 · `textarea` 의 `maxlength` 는 어디서 다루나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
