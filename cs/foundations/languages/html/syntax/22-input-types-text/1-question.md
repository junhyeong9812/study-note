# html/syntax/22 — `<input>` 타입 지도 ① 텍스트 계열: `text`/`password`/`email`/`url`/`tel`/`search` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 본체는 **창 ②(`validity`·`.value`)** 다. 답할 때마다 「**무효인가**」·「**값이 다듬어졌나**」 중 **어느 칸**의 이야기인지 적어라. ★ `validationMessage` 문구는 근거가 아니다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [21번 주제](../21-form-submission-model/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 열여덟 칸의 검사와 손질 (예측)

```html
<!-- html21b-22-types.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>22 텍스트 계열 타입</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post" novalidate>
<input id="t1" name="t1" type="text" value="줄&#10;바꿈">
<input id="t2" name="t2" type="text" value=" 앞뒤 공백 ">
<input id="s1" name="s1" type="search" value="검색어">
<input id="p1" name="p1" type="password" value="비밀">
<input id="e1" name="e1" type="email" value="a@b">
<input id="e2" name="e2" type="email" value="a">
<input id="e3" name="e3" type="email" value=" a@b.kr ">
<input id="e4" name="e4" type="email" value="한@b.kr">
<input id="e5" name="e5" type="email" value="a@-b.kr">
<input id="e6" name="e6" type="email" value="a@b.kr, c@d.kr">
<input id="e7" name="e7" type="email" value="a@b.kr, c@d.kr" multiple>
<input id="u1" name="u1" type="url" value="http://x">
<input id="u2" name="u2" type="url" value="x">
<input id="u3" name="u3" type="url" value="javascript:alert(1)">
<input id="u4" name="u4" type="url" value=" http://한글.kr/경로 ">
<input id="n1" name="n1" type="tel" value="아무 글자!">
<input id="n2" name="n2" type="tel" value="010-1234-5678">
<input id="n3" name="n3" type="tel" value="12&#10;34">
<button id="보냄">보냄</button>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const J = v => JSON.stringify(v);
const 칸들 = [...document.querySelectorAll("#폼 input")];
window.__대상 = 칸들.map(i => [i.id, "#" + i.id]);
window.__시도 = [{ 이름: "novalidate 로 전부 보내기", 단계: [["click", "#보냄"]] }];
window.__끝 = () => {
  const O = [칸("id", 4) + 칸("type", 9) + 칸("value 속성", 22) + 칸(".value", 22) + 칸("typeMismatch", 13) + 칸("checkValidity()", 16) + "역할"];
  for (const i of 칸들) {
    O.push(칸(i.id, 4) + 칸(i.type, 9) + 칸(J(i.getAttribute("value")), 22) + 칸(J(i.value), 22)
      + 칸(String(i.validity.typeMismatch), 13) + 칸(String(i.checkValidity()), 16) + __AX[i.id].역할);
  }
  O.push("");
  O.push("validationMessage 전문 (비어 있지 않은 것만)");
  for (const i of 칸들) if (i.validationMessage) O.push("  " + i.id + "  " + i.validationMessage);
  O.push("");
  const 틀림 = 칸들.filter(i => i.validity.typeMismatch);
  O.push("typeMismatch 인 칸 = " + 틀림.map(i => i.id).join(" · ") + " → " + 틀림.length + " / " + 칸들.length);
  const tel = 칸들.filter(i => i.type === "tel");
  O.push("tel 에서 무효가 된 칸 = " + tel.filter(i => !i.checkValidity()).length + " / " + tel.length);
  const 바뀜 = 칸들.filter(i => i.value !== i.getAttribute("value"));
  O.push("value 속성과 .value 가 다른 칸 = " + 바뀜.map(i => i.id).join(" · ") + " → " + 바뀜.length + " / " + 칸들.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 열여덟 칸 각각의 `validity.typeMismatch` 와 `checkValidity()` 는?
- `.value` 가 `value` 속성 글자와 달라지는 칸은 어디이고, 각각 무엇으로 바뀌나?
- 여섯 타입 각각의 CDP 접근성 역할은?

### 2. 같은 파일을 다른 로케일로 (예측)

- 1번 파일을 `de-DE` 로케일의 Chrome 으로 띄우면 `typeMismatch` 가 켜지는 칸은 달라지는가?
- `validationMessage` 는 달라지는가? `e5` 의 문구는 다른 칸과 무엇이 다른가?

### 3. `novalidate` 로 전부 보내면 (예측)

- 1번 폼의 단추를 누르면 서버에 실리는 `t1`·`t2`·`e2`·`e3`·`e7`·`u4`·`n3`·`p1` 은 각각 무엇인가?

### 4. 두 타입과 직렬화 (예측)

```html
<!-- html21b-22-dump.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>22 속성과 프로퍼티</title>
</head>
<body>
<input id="글" type="text" value="속성값">
<input id="비" type="password" value="속성값">
<input id="빈" type="password">
<script>
for (const id of ["글", "비", "빈"]) document.getElementById(id).value = "스크립트값";
document.body.append(Object.assign(document.createElement("pre"), {
  textContent: ["글", "비", "빈"].map(id => id + " .value = " + document.getElementById(id).value
    + " · .defaultValue = " + JSON.stringify(document.getElementById(id).defaultValue)).join("\n")
}));
</script>
</body>
</html>
```

- `--dump-dom` 이 찍는 세 `input` 의 `value` 속성은? `<pre>` 에는 무엇이 찍히나?
- `#글`(text)과 `#비`(password)는 직렬화에서 다른가?

### 5. `email` 의 정규식 (왜)

- 명세가 「valid email address」를 정하는 정규식에서 `@` 뒤 부분은 어떤 꼴인가? 그래서 `a@b` 는?
- 명세는 이 정의를 RFC 5322 에 대해 무엇이라 부르고, 그 이유로 무엇을 드는가?

### 6. `tel` 과 문법 (왜)

- 명세는 `tel` 이 문법을 강제하지 않는 이유를 무엇이라 적는가?
- 형식을 강제해야 하는 시스템에게 명세가 권하는 두 수단은?

### 7. 공백을 지우는 타입 (경계)

- 여섯 타입 중 **앞뒤 공백**을 지우는 타입은? **줄바꿈**만 지우는 타입은?
- `email multiple` 은 무엇을 지우나?

### 8. `url` 이 통과시키는 것 (경계)

- `type="url"` 의 제약 줄은 무엇이고, 그래서 `javascript:alert(1)` 은 유효한가?
- 그 값을 받아 링크로 다시 쓰는 서버는 무엇을 해야 하나?

### 9. 명세·구현·관찰 가르기 (경계)

- `password` 의 역할은 HTML-AAM 에서 무엇이고, 이 판의 CDP 트리에서는 무엇인가?
- `validationMessage` 의 글자는 누가 정하나? 명세의 getter 는 무엇을 돌려주라고 하나?

### 10. 이 판이 못 보는 것 (경계)

- `tel`·`email` 이 모바일에서 여는 자판을 이 판이 잴 수 없는 이유는? 그것은 제 몇의 상태인가?
- 자동완성·비밀번호 관리자를 못 재는 이유는?

### 11. 정본 경계 긋기 (연결)

- `value` 속성과 `.value` 가 갈리는 이유의 정본은?
- `:invalid`·`:user-invalid` 로 칠하는 것, `pattern`·`minlength`, `autocomplete`·`inputmode` 의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
