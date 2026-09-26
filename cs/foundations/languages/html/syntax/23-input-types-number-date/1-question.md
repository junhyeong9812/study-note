# html/syntax/23 — `<input>` 타입 지도 ② 숫자·날짜: `number`/`range`/`date`/`time`/`datetime-local`/`month`/`week` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **세 자리**로 갈린다 — **화면에 보이는 글자**(창 ⑦) · **`.value`**(창 ②) · **서버가 받은 값**(창 ⑤). 답할 때마다 어느 자리의 이야기인지 적어라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 로케일을 따로 적지 않은 블록은 전부 **ko-KR** 로 띄웠다. 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다.
> 선행 — [22번 주제](../22-input-types-text/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 로케일을 바꾸는 두 방법 (예측)

```html
<!-- html21b-23-lang.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>23 로케일 확인</title>
<body>
<input id="e" type="email" value="a">
<script>
document.body.append(Object.assign(document.createElement("script"), { type: "text/plain",
  textContent: "\n--OUT\nnavigator.language = " + navigator.language
    + "\nvalidationMessage = " + document.getElementById("e").validationMessage
    + "\n(1234.5).toLocaleString() = " + (1234.5).toLocaleString() + "\nOUT--\n" }));
</script>
```

- 이 머신(기계 로케일 ko-KR)에서 `google-chrome --lang=de-DE --dump-dom` 으로 띄우면 세 줄은 각각 무엇인가?
- `LANGUAGE=de_DE google-chrome --dump-dom` 으로 띄우면?

### 2. 같은 폼을 두 로케일로 (예측)

```html
<!-- html21b-23-locale.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>23 두 로케일</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post" novalidate>
<input id="d" name="d" type="date" value="2026-09-26" aria-label="날짜">
<input id="t" name="t" type="time" value="13:05" aria-label="시각">
<input id="dt" name="dt" type="datetime-local" value="2026-09-26T13:05" aria-label="날짜와 시각">
<input id="m" name="m" type="month" value="2026-09" aria-label="달">
<input id="w" name="w" type="week" value="2026-W39" aria-label="주">
<input id="n" name="n" type="number" value="1234.5" step="any" aria-label="수">
<input id="r" name="r" type="range" aria-label="범위">
<input id="k1" name="k1" type="number" step="any" aria-label="입력한 수 1">
<input id="k2" name="k2" type="number" step="any" aria-label="입력한 수 2">
<button id="보냄">보냄</button>
</form>
<script>
window.__준비 = [["type", "#k1", "1,5"], ["type", "#k2", "1.5"]];
window.__칸 = ["d", "t", "dt", "m", "w", "n", "r", "k1", "k2"];
window.__보냄 = "#보냄";
</script>
</body>
</html>
```

- ko-KR 과 de-DE 에서 아홉 칸 각각의 **화면 글자**는?
- 두 로케일에서 서버가 받는 아홉 값은 각각 무엇이고, 갈리는 칸이 있는가?
- 두 판의 `Accept-Language` 헤더는?

### 3. `.value` 와 `valueAs*` (예측)

```html
<!-- html21b-23-values.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>23 값과 valueAs</title>
</head>
<body>
<input id="d1" type="date" value="2026-09-26">
<input id="d2" type="date" value="2026-02-30">
<input id="d3" type="date" value="26.09.2026">
<input id="t1" type="time" value="13:05:30.5">
<input id="dt1" type="datetime-local" value="2026-09-26 13:05">
<input id="m1" type="month" value="2026-09">
<input id="w1" type="week" value="2026-W53">
<input id="w2" type="week" value="2026-W39">
<input id="n1" type="number" value="010-1234-5678">
<input id="n2" type="number" value="01012345678">
<input id="n3" type="number" value="1e3">
<input id="n4" type="number" value=" 12 ">
<time id="시각" datetime="2026-02-30">2월 30일</time>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const J = v => JSON.stringify(v);
const 시도 = f => { try { return String(f()); } catch (e) { return e.name + " 「" + e.message + "」"; } };
window.__끝 = () => {
  const O = [칸("id", 5) + 칸("value 속성", 18) + 칸(".value", 22) + 칸("valueAsNumber", 16) + "valueAsDate"];
  for (const i of document.querySelectorAll("input")) {
    O.push(칸(i.id, 5) + 칸(J(i.getAttribute("value")), 18) + 칸(J(i.value), 22) + 칸(String(i.valueAsNumber), 16)
      + 시도(() => i.valueAsDate === null ? "null" : i.valueAsDate.toISOString()));
  }
  const 비움 = [...document.querySelectorAll("input")].filter(i => i.getAttribute("value") && i.value === "");
  O.push("속성 값이 있는데 .value 가 빈 문자열이 된 칸 = " + 비움.map(i => i.id).join(" · ") + " → " + 비움.length + " / " + document.querySelectorAll("input").length);
  O.push("");
  const n1 = document.getElementById("n1");
  O.push("n1 에 스크립트로 넣기");
  O.push("  n1.value = \"010-1234\" 뒤 .value = " + (n1.value = "010-1234", J(n1.value)));
  O.push("  n1.valueAsNumber = 101234 뒤 .value = " + (n1.valueAsNumber = 101234, J(n1.value)));
  O.push("  n1.valueAsDate = new Date(0) → " + 시도(() => { n1.valueAsDate = new Date(0); return "예외 없음"; }));
  O.push("");
  const t = document.getElementById("시각");
  O.push("time 요소 datetime=\"2026-02-30\" → .dateTime = " + J(t.dateTime));
  O.push("date 입력 value=\"2026-02-30\" → .value = " + J(document.getElementById("d2").value));
  return O.join("\n");
};
</script>
</body>
</html>
```

- 열두 칸 각각의 `.value` · `valueAsNumber` · `valueAsDate` 는?
- `n1.valueAsDate = new Date(0)` 은 무엇을 내는가?
- `time` 요소의 `.dateTime` 과 `d2` 의 `.value` 는 각각 무엇인가?

### 4. `number` 에 전화번호를 쳐 넣으면 (예측)

```html
<!-- html21b-23-phone.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>23 number 에 전화번호</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post" novalidate>
<input id="n1" name="n1" type="number" aria-label="number 1">
<input id="n2" name="n2" type="number" aria-label="number 2">
<input id="t1" name="t1" type="tel" aria-label="tel 1">
<input id="t2" name="t2" type="tel" aria-label="tel 2">
<button id="보냄">보냄</button>
</form>
<script>
const 칸들 = ["n1", "n2", "t1", "t2"];
const 입력 = [["type", "#n1", "010-1234"], ["type", "#n2", "0101234"], ["type", "#t1", "010-1234"], ["type", "#t2", "0101234"]];
window.__읽기 = () => 칸들.map(id => {
  const e = document.getElementById(id);
  return id + " .value=" + JSON.stringify(e.value) + " badInput=" + e.validity.badInput + " valueAsNumber=" + e.valueAsNumber;
}).join(" · ");
window.__시도 = [
  { 이름: "입력만 하고 읽기", 단계: 입력, 뒤: "__읽기()" },
  { 이름: "입력하고 보내기", 단계: [...입력, ["click", "#보냄"]] },
  { 이름: "n2·t2 에서 위쪽 화살표 한 번", 단계: [...입력, ["key", "#n2", "ArrowUp", "ArrowUp", 38], ["key", "#t2", "ArrowUp", "ArrowUp", 38]], 뒤: "__읽기()" },
];
</script>
</body>
</html>
```

- 첫 시도의 네 칸 `.value` · `badInput` · `valueAsNumber` 는?
- 둘째 시도에서 서버에 실리는 네 값은?
- 셋째 시도의 위쪽 화살표 뒤 `n2`·`t2` 의 `.value` 는?

### 5. `range` 와 범위·눈금 깃발 (예측)

```html
<!-- html21b-23-range.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>23 범위와 눈금</title>
</head>
<body>
<input id="r1" type="range">
<input id="r2" type="range" min="0" max="10">
<input id="r3" type="range" min="0" max="5" step="2">
<input id="r4" type="range" value="">
<input id="r5" type="range" value="abc">
<input id="r6" type="range" value="200">
<input id="r7" type="range" min="10" max="0">
<input id="a1" type="number" min="0" max="10" value="11">
<input id="a2" type="number" step="0.5" value="1.3">
<input id="a2s" type="number" step="0.5">
<input id="a3" type="number" value="1.5">
<input id="a4" type="date" min="2026-01-01" value="2025-12-31">
<input id="a5" type="date" step="7" min="2026-09-07" value="2026-09-10">
<input id="a6" type="time" step="900" value="13:07">
<input id="a6s" type="time" step="900">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const J = v => JSON.stringify(v);
document.getElementById("a2s").value = "1.3";      // 스크립트로 넣은 값
document.getElementById("a6s").value = "13:07";
const 깃발 = ["rangeUnderflow", "rangeOverflow", "stepMismatch", "badInput", "valueMissing"];
window.__끝 = () => {
  const O = [칸("id", 4) + 칸("속성", 52) + 칸(".value", 14) + "켜진 validity 깃발"];
  for (const i of document.querySelectorAll("input")) {
    const 속성 = [...i.attributes].filter(a => a.name !== "id").map(a => a.name + "=" + J(a.value)).join(" ");
    const 켜짐 = 깃발.filter(k => i.validity[k]);
    O.push(칸(i.id, 4) + 칸(속성, 52) + 칸(J(i.value), 14) + (켜짐.join(" · ") || "(없음)"));
  }
  O.push("");
  O.push("validationMessage 전문 (비어 있지 않은 것만)");
  for (const i of document.querySelectorAll("input")) if (i.validationMessage) O.push("  " + i.id + "  " + i.validationMessage);
  O.push("");
  O.push("a2 와 a2s · a6 와 a6s 는 값이 같다 — 차이는 속성으로 넣었나 스크립트로 넣었나");
  for (const [x, y] of [["a2", "a2s"], ["a6", "a6s"]]) {
    const X = document.getElementById(x), Y = document.getElementById(y);
    O.push("  " + x + " stepMismatch = " + X.validity.stepMismatch + " · " + y + " stepMismatch = " + Y.validity.stepMismatch);
  }
  const 범위 = [...document.querySelectorAll("input[type=range]")];
  O.push("");
  O.push("range 에서 .value 가 빈 문자열인 칸 = " + 범위.filter(i => i.value === "").length + " / " + 범위.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 일곱 `range` 칸의 `.value` 는?
- `a1`\~`a6s` 에서 켜지는 `validity` 깃발은?
- `a2` 와 `a2s`, `a6` 와 `a6s` 는 서로 같은가?

### 6. 표시 형식과 제출 형식 (왜)

- 명세의 「폼 컨트롤의 현지화에 관한 구현 노트」는 표시 형식과 제출 형식을 어떤 관계로 두는가?
- 그 문장이 **사람이 친 글자의 해석**까지 로케일과 무관하게 만드는가? 2번의 어느 칸이 근거인가?

### 7. `type=number` 와 숫자로 된 글자 (왜)

- 명세는 `type=number` 가 알맞지 않은 입력의 예로 무엇을 들고, 판단 기준으로 무엇을 제시하는가?
- 그런 입력에 명세가 권하는 대안은?

### 8. `range` 의 기본값과 넘침 (경계)

- `range` 의 기본값과, 최댓값을 넘는 값이 들어왔을 때 명세가 UA 에게 요구하는 것은?
- 같은 넘침을 `number` 는 어떻게 다루는가?

### 9. 명세·구현·관찰 가르기 (경계)

- 속성으로 넣은 값과 스크립트로 넣은 값의 `stepMismatch` 가 갈린 것은 명세와 구현 중 어느 쪽이 가른 것인가? 명세의 어느 줄로 설명되는가?
- 화면 형식이 페이지의 `lang` 을 따랐나, 사용자 로케일을 따랐나? 그것은 명세인가 구현인가?

### 10. 이 판이 못 보는 것 (경계)

- 날짜 칸의 화면 글자를 픽셀 대신 무엇으로 물었나? 그것은 제 몇의 상태이고, 그 창이 못 보는 것은?
- 달력 선택 창과 모바일 날짜 휠을 못 재는 이유는?

### 11. 정본 경계 긋기 (연결)

- `time` 요소의 `datetime` 이 검증되지 않는다는 것의 정본은? 여기서 무엇과 대비했나?
- `min`/`max`/`step` 이 눈금을 만드는 규칙의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
