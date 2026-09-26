# html/syntax/28 — 검증 속성: `required`/`pattern`/`min`/`max`/`step`/`minlength`/`maxlength` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **`validity` 깃발**이다(`validationMessage` 문구가 아니다). 칸마다 「**그 속성의 깃발이 켜지나 / 값이 고쳐지나 / 아무 일도 없나**」 셋 중 하나로 답하라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 1번 페이지가 읽는 「명세 열」 파일(`html25b-28-spec.js`)은 **답이 들어 있어서** 이 파일에 싣지 않는다 — 정리·정답 파일에 있다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [23번 주제](../23-input-types-number-date/1-question.md) · [21번 주제](../21-form-submission-model/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 속성 일곱 × 타입 여섯 (예측)

```html
<!-- html25b-28-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>28 속성과 타입</title>
<script src="html25b-28-spec.js"></script>
</head>
<body>
<div id="자리"></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 타입 = ["text", "email", "number", "date", "checkbox", "range"];
// [속성, 속성값, 깃발, 타입별 스크립트 값]  — 값은 「그 속성이 먹는다면 깃발이 켜질」 값으로 골랐다
const 줄 = [
  ["required", "", "valueMissing", { text: "", email: "", number: "", date: "", checkbox: null, range: "" }],
  ["pattern", "x+", "patternMismatch", { text: "abc", email: "a@b.c", number: "5", date: "2026-01-01", checkbox: null, range: "50" }],
  ["min", "5|2026-01-02", "rangeUnderflow", { text: "1", email: "a@b.c", number: "1", date: "2026-01-01", checkbox: null, range: "1" }],
  ["max", "5|2026-01-01", "rangeOverflow", { text: "9", email: "a@b.c", number: "9", date: "2026-01-02", checkbox: null, range: "9" }],
  ["step", "2", "stepMismatch", { text: "3", email: "a@b.c", number: "3", date: "2026-01-02", checkbox: null, range: "3" }],
  ["minlength", "20", "tooShort", { text: "a", email: "a@b.c", number: "1", date: "2026-01-01", checkbox: null, range: "50" }],
  ["maxlength", "1", "tooLong", { text: "abc", email: "a@b.co", number: "123", date: "2026-01-01", checkbox: null, range: "50" }],
];
const 자리 = document.getElementById("자리");
for (const [속성, 속성값, , 값들] of 줄) {
  for (const t of 타입) {
    const i = document.createElement("input");
    i.type = t; i.id = 속성 + "-" + t;
    const [보통, 날짜] = 속성값.split("|");
    i.setAttribute(속성, t === "date" && 날짜 ? 날짜 : 보통);
    if (속성 === "step" && t === "date") i.min = "2026-01-01";   // 눈금의 기준을 못 박는다
    const 대조 = document.createElement("input");                 // 같은 타입 · 같은 값 · 같은 편집 — 속성만 없다
    대조.type = t; 대조.id = "대조-" + i.id;
    if (속성 === "step" && t === "date") 대조.min = "2026-01-01";
    자리.append(i, 대조);
    if (값들[t] !== null) { i.value = 값들[t]; 대조.value = 값들[t]; }   // 스크립트로 넣는다
  }
}
// 사용자 편집 — minlength·maxlength 줄만 (진짜 키 입력)
const 편집 = [];
for (const 속성 of ["minlength", "maxlength"]) {
  for (const 앞 of ["#", "#대조-"]) {
    const 샵 = t => 앞 + 속성 + "-" + t;
    if (속성 === "minlength") { 편집.push(["type", 샵("text"), "b"], ["type", 샵("email"), "d"], ["type", 샵("number"), "2"]); }
    else { for (const t of ["text", "email", "number"]) 편집.push(["key", 샵(t), "End", "End", 35], ["keyhere", "Backspace", "Backspace", 8]); }
    편집.push(["key", 샵("date"), "ArrowUp", "ArrowUp", 38], ["key", 샵("checkbox"), " ", "Space", 32, " "], ["key", 샵("range"), "ArrowRight", "ArrowRight", 39]);
  }
}
const 뒤 = "JSON.stringify(Object.fromEntries([...document.querySelectorAll('#자리 input')].map(i => [i.id, { v: i.value, c: i.checked, f: Object.fromEntries(['valueMissing','patternMismatch','rangeUnderflow','rangeOverflow','stepMismatch','tooShort','tooLong'].map(k => [k, i.validity[k]])) }])))";
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [
  { 이름: "편집 없음 (스크립트 값만)", 단계: [], 뒤 },
  { 이름: "minlength·maxlength 줄을 진짜 키로 편집한 뒤", 단계: 편집, 뒤 },
];
window.__종합 = 결과 => {
  const O = [];
  let 명세갈림 = 0;
  for (const r of 결과) {
    const S = JSON.parse(r.뒤);
    O.push("── " + r.이름);
    O.push((칸("속성 \\ 타입", 12) + 타입.map(t => 칸(t, 11)).join("")).trimEnd());
    let 무시 = 0, 전체 = 0;
    for (const [속성, , 깃발, 값들] of 줄) {
      let 행글 = 칸(속성, 12);
      for (const t of 타입) {
        const id = 속성 + "-" + t, s = S[id];
        const 켬 = s.f[깃발], 바뀜 = s.v !== S["대조-" + id].v;
        const 먹음 = 켬 || 바뀜;
        무시 += !먹음; 전체++;
        if (r === 결과[결과.length - 1] && 먹음 !== 명세[t].includes(속성)) 명세갈림++;
        행글 += 칸(켬 ? "깃발" : 바뀜 ? "값 " + s.v : "·", 11);
      }
      O.push(행글.trimEnd());
    }
    O.push("무시된 칸 = " + 무시 + " / " + 전체 + "  (「깃발」= 그 속성의 validity 깃발이 켜짐 · 「값 N」= 깃발 없이 값이 N 으로 고쳐짐(속성 없는 짝과 다름) · 「·」= 아무 일 없음)");
    O.push("");
  }
  const 편집뒤 = JSON.parse(결과[1].뒤);
  O.push("편집 뒤의 값 — " + ["minlength", "maxlength"].map(a => a + ": " + 타입.map(t => t + "=" + JSON.stringify(편집뒤[a + "-" + t].v) + (t === "checkbox" ? "(checked=" + 편집뒤[a + "-" + t].c + ")" : "")).join(" ")).join("\n              "));
  O.push("명세의 적용 목록과 갈린 칸(편집 뒤) = " + 명세갈림 + " / " + 줄.length * 타입.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 「편집 없음」 판에서 마흔두 칸 각각은 깃발이 켜지나 · 값이 쌍둥이와 달라지나 · 아무 일도 없나? 「무시된 칸 N / 42」의 N 은?
- `minlength`·`maxlength` 두 줄을 진짜 키로 편집한 판에서는 어느 칸이 바뀌고 N 은?
- 명세의 적용 목록과 갈린 칸은 몇 개인가?

### 2. `step` 칸 열일곱 (예측)

```html
<!-- html25b-28-step.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>28 눈금의 기준</title>
</head>
<body>
<input id="n1" type="number" min="1" step="2">
<input id="n2" type="number" min="1" step="2">
<input id="n3" type="number" min="1" step="2" value="4">
<input id="n4" type="number" step="2" value="3">
<input id="n5" type="number" step="2" value="3">
<input id="n6" type="number" step="2" value="3">
<input id="n7" type="number" step="2">
<input id="n8" type="number" min="1" step="2">
<input id="a2" type="number" step="0.5" value="1.3">
<input id="a2s" type="number" step="0.5">
<input id="t1" type="time" step="900" value="13:07">
<input id="t2" type="time" step="900">
<input id="t3" type="time" step="900" min="13:00" value="13:07">
<input id="d1" type="date" step="7" min="2026-09-07" value="2026-09-10">
<input id="d2" type="date" step="7" value="2026-09-10">
<input id="r1" type="range" min="1" step="2" value="4">
<input id="r2" type="range" min="1" step="2">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const $ = id => document.getElementById(id);
// 스크립트로 넣는 값 — [id, 값]
const 스크립트 = [["n1", "4"], ["n2", "5"], ["n5", "4"], ["n6", "5"], ["n7", "3"], ["a2s", "1.3"], ["t2", "13:07"], ["r2", "4"]];
for (const [id, v] of 스크립트) $(id).value = v;
const 모두 = [...document.querySelectorAll("input")];
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [{ 이름: "n8 에 진짜 키로 4 를 친다", 단계: [["type", "#n8", "4"]],
  뒤: "JSON.stringify(Object.fromEntries([...document.querySelectorAll('input')].map(i => [i.id, [i.value, i.validity.stepMismatch]])))" }];
window.__종합 = 결과 => {
  const S = JSON.parse(결과[0].뒤);
  const O = [칸("id", 4) + 칸("속성", 58) + 칸("값을 넣은 길", 17) + 칸(".value", 14) + "stepMismatch"];
  for (const i of 모두) {
    const 속성 = [...i.attributes].filter(a => a.name !== "id").map(a => a.name + "=" + JSON.stringify(a.value)).join(" ");
    const 스 = 스크립트.find(([id]) => id === i.id);
    const 길 = i.id === "n8" ? "진짜 키 \"4\"" : 스 ? "스크립트 " + JSON.stringify(스[1]) : "속성만";
    O.push(칸(i.id, 4) + 칸(속성, 58) + 칸(길, 17) + 칸(JSON.stringify(S[i.id][0]), 14) + S[i.id][1]);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

- 칸마다 `.value` 와 `stepMismatch` 는?
- 같은 `min=1 step=2` 에 `4` 를 스크립트(`n1`)·속성(`n3`)·진짜 키(`n8`)로 넣은 세 칸은 서로 다른가?

### 3. `pattern` 열 개와 JS 셋 (예측)

```html
<!-- html25b-28-pattern.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>28 pattern 의 감싸기</title>
</head>
<body>
<input id="p1" pattern="a|bc">
<input id="p2" pattern="a|bc">
<input id="p3" pattern="a|bc">
<input id="p4" pattern="[a-z-]+">
<input id="p5" pattern="[a-z\-]+">
<input id="p6" pattern="[\p{L}--[a-z]]+">
<input id="p7" pattern="[\p{L}--[a-z]]+">
<input id="p8" pattern="\p{L}+">
<input id="p9" pattern="abc">
<input id="p10" pattern="x+">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 값 = { p1: "a", p2: "bc", p3: "abc", p4: "1", p5: "1", p6: "ABC가", p7: "abc", p8: "가나", p9: "ABC", p10: "" };
for (const [id, v] of Object.entries(값)) document.getElementById(id).value = v;
const 던짐 = f => { try { return String(f()); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };
window.__콘솔 = true;
window.__끝 = () => {
  const O = [칸("id", 5) + 칸("pattern", 20) + 칸(".value", 10) + "patternMismatch"];
  for (const i of document.querySelectorAll("input")) {
    O.push(칸(i.id, 5) + 칸(i.getAttribute("pattern"), 20) + 칸(JSON.stringify(i.value), 10) + i.validity.patternMismatch);
  }
  O.push("");
  O.push("같은 글자를 JS 로 — 감싸지 않으면");
  O.push("  /a|bc/v.test(\"abc\")        = " + 던짐(() => /a|bc/v.test("abc")));
  O.push("  /^a|bc$/v.test(\"abc\")      = " + 던짐(() => /^a|bc$/v.test("abc")));
  O.push("  /^(?:a|bc)$/v.test(\"abc\")  = " + 던짐(() => /^(?:a|bc)$/v.test("abc")));
  O.push("");
  O.push("[a-z-] 를 플래그별로 컴파일하면");
  for (const f of ["", "u", "v"]) O.push("  new RegExp(\"[a-z-]\", " + JSON.stringify(f) + ")  → " + 던짐(() => new RegExp("[a-z-]", f)));
  O.push("");
  O.push("콘솔 기록(Log.entryAdded) " + __LOG.length + "줄");
  for (const s of __LOG) O.push("  " + s);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 칸마다 `patternMismatch` 는?
- 세 JS 식의 결과와 `new RegExp("[a-z-]", …)` 의 세 플래그 결과는?
- 콘솔 기록은 몇 줄이고 무엇에 관한 것인가?

### 4. 길이 제한과 편집 (예측)

```html
<!-- html25b-28-length.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>28 길이 제한과 편집</title>
</head>
<body>
<input id="m1" maxlength="3">
<input id="m2" maxlength="3">
<input id="m3" minlength="5">
<input id="m4" minlength="5">
<input id="m5" maxlength="3">
<textarea id="m6" maxlength="3">abcdef</textarea>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const $ = id => document.getElementById(id);
$("m1").value = "abcdef";
$("m4").value = "ab";
$("m5").value = "abcdef";
const 설명 = {
  m1: "스크립트 \"abcdef\" → (둘째 시도) End + Backspace",
  m2: "(둘째 시도) 진짜로 \"abcdef\" 를 친다",
  m3: "(둘째 시도) 진짜로 \"ab\" 를 친다",
  m4: "스크립트 \"ab\"",
  m5: "스크립트 \"abcdef\" → (둘째 시도) End + Backspace → 스크립트 \"abcdef\"",
  m6: "자식 텍스트 \"abcdef\"",
};
window.__표 = "종합";
window.__뒤숨김 = true;
const 뒤 = "JSON.stringify(Object.fromEntries(['m1','m2','m3','m4','m5','m6'].map(id => { const e = document.getElementById(id); return [id, [e.value, e.validity.tooLong, e.validity.tooShort]]; })))";
window.__시도 = [
  { 이름: "편집 없음", 단계: [], 뒤 },
  { 이름: "진짜 키로 편집", 단계: [
    ["key", "#m1", "End", "End", 35], ["keyhere", "Backspace", "Backspace", 8],
    ["type", "#m2", "abcdef"], ["type", "#m3", "ab"],
    ["key", "#m5", "End", "End", 35], ["keyhere", "Backspace", "Backspace", 8], ["js", "document.getElementById('m5').value = 'abcdef'; 1"],
  ], 뒤 },
];
window.__종합 = 결과 => {
  const O = [];
  for (const r of 결과) {
    const S = JSON.parse(r.뒤);
    O.push("── " + r.이름);
    O.push(칸("id", 4) + 칸("속성", 14) + 칸(".value", 10) + 칸("tooLong", 9) + 칸("tooShort", 9) + "무엇을 했나");
    for (const id of Object.keys(S)) {
      const e = $(id), a = e.hasAttribute("maxlength") ? "maxlength=3" : "minlength=5";
      O.push(칸(id, 4) + 칸(a, 14) + 칸(JSON.stringify(S[id][0]), 10) + 칸(String(S[id][1]), 9) + 칸(String(S[id][2]), 9) + 설명[id]);
    }
    O.push("");
  }
  return O.join("\n").trimEnd();
};
</script>
</body>
</html>
```

- 두 시도(편집 없음 · 진짜 키로 편집) 각각에서 `m1`\~`m6` 의 `.value` · `tooLong` · `tooShort` 는?

### 5. 속성과 타입의 짝 (왜)

- `number` 에 준 `pattern`, `text` 에 준 `min` 이 아무 일도 안 하는 근거는 명세의 어느 목록인가?
- `range` 에 `required` 가 적용 목록에서 빠진 이유는? `checkbox` 에는 무엇이 남나?

### 6. `step` 의 기준값 (왜)

- 명세가 step base 를 고르는 순서는?
- [23번](../23-input-types-number-date/2-summary.md)의 (4) 가 「속성으로 준 값에 `stepMismatch` 를 안 켠다」로 본 `a2`·`a6` 을 이 순서로 다시 설명하면?

### 7. `pattern` 의 컴파일 (왜)

- 명세가 패턴을 `^(?:` 와 `)$` 로 감싸는 두 이유는?
- `v` 로 컴파일이 실패하면 무엇이 되고, 그 사실은 어디에 남나?

### 8. 입력 제한과 검증 (경계)

- `maxlength` 가 **사용자의 입력을 막는 것**과 **`tooLong` 을 켜는 것**은 명세에서 어떻게 다른 문장인가?
- 서버에서 불러온 긴 값을 `maxlength` 칸에 채운 폼은 사용자가 손대기 전에 제출이 막히나?

### 9. `range` 와 `number` 의 눈금 밖 값 (경계)

- 명세는 `range` 와 `number` 의 step mismatch 를 각각 「반올림해야 한다 / 해도 된다」 중 무엇으로 적나? 이 판은?
- `min=1 step=2` 인 `range` 에 `4` 를 넣으면 왜 `5` 인가?

### 10. 클라이언트 검증이면 충분한가 (경계)

- 이 주제의 속성을 다 달아도 서버 검증이 필요한 이유를 [21번](../21-form-submission-model/2-summary.md)의 측정과 이 주제의 측정으로 각각 대면?

### 11. 명세·구현·관찰 가르기 (경계)

- 이 주제에서 명세와 갈린 칸은? 23번의 「갈림」은 어느 층으로 옮겨야 하나?
- 「사용자의 초과 입력을 막는다」·「무효한 `pattern` 을 콘솔에 남긴다」·「`number` 를 반올림하지 않는다」는 각각 어느 층인가?

### 12. 정본 경계 긋기 (연결)

- 검증이 언제 도나 · `curl` 우회 · `:user-invalid` · `setCustomValidity` · `u`/`v` 의 차이의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
