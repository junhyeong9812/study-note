# html/syntax/30 — 폼 상태·입력 보조 속성: `disabled`/`readonly`/`autofocus`/`autocomplete`/`inputmode` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **세 지점**이다 — 칸마다 「**제출에 실리나(서버) · 진짜 Tab 이 닿나 · `willValidate` 가 참인가**」로 답하라. 보조 속성은 「**IDL 이 무엇을 돌려주나 · 접근성 트리에 무엇이 남나**」로.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 1·4번 페이지가 읽는 「명세 열」 파일(`html29b-30-spec.js`·`html29b-30-hints-spec.js`)은 **답이 들어 있어서** 이 파일에 싣지 않는다 — 정리·정답 파일에 있다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [24번 주제](../24-input-types-choice-special/1-question.md) · [27번 주제](../27-fieldset-and-legend/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 속성 셋 · 대상 다섯 · 지점 셋 (예측)

```html
<!-- html29b-30-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>30 세 지점</title>
<script src="html29b-rec.js"></script>
<script src="html29b-30-spec.js"></script>
</head>
<body>
<button type="button" id="시작">시작</button>
<div id="자리"></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 속성 = ["없음", "disabled", "readonly"];
const 대상 = ["text", "checkbox", "select", "textarea", "button"];
const 만들기 = t => {
  if (t === "text") { const e = document.createElement("input"); e.value = "가"; return e; }
  if (t === "checkbox") { const e = document.createElement("input"); e.type = "checkbox"; e.checked = true; return e; }
  if (t === "select") { const e = document.createElement("select"); e.append(new Option("가", "가", true, true), new Option("나", "나")); return e; }
  if (t === "textarea") { const e = document.createElement("textarea"); e.textContent = "가"; return e; }
  const e = document.createElement("button"); e.type = "submit"; e.value = "가"; e.textContent = "단추"; return e;
};
속성.forEach((a, k) => {
  const f = document.createElement("form");
  f.id = "폼" + k; f.action = "/r"; f.method = "post";
  for (const t of 대상) {
    const e = 만들기(t);
    e.id = a + "-" + t; e.name = t;
    if (a !== "없음") e.setAttribute(a, "");
    f.append(e);
  }
  document.getElementById("자리").append(f);
});
const 탭 = [["js", "document.getElementById('시작').focus(); window.__간곳 = []; 1"]];
for (let i = 0; i < 18; i++) 탭.push(["keyhere", "Tab", "Tab", 9], ["js", "window.__간곳.push(document.activeElement.id || document.activeElement.tagName); 1"]);
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [
  ...속성.map((a, k) => ({ 이름: "폼" + k + "(" + a + ") · requestSubmit(그 폼의 button)",
    단계: [["js", "(() => { try { document.getElementById('폼" + k + "').requestSubmit(document.getElementById('" + a + "-button')); } catch (e) { 적기('예외 ' + e.name); } return 1; })()"]] })),
  { 이름: "Tab 열여덟 번", 단계: 탭, 뒤: "JSON.stringify({ 간곳: window.__간곳, 검증: Object.fromEntries([...document.querySelectorAll('#자리 [id]')].map(e => [e.id, e.willValidate])) })" },
];
window.__종합 = 결과 => {
  const 탭결과 = JSON.parse(결과[3].뒤);
  const 셈 = (a, t, 점) => {
    if (점 === "제출") { const r = 결과[속성.indexOf(a)]; return r.필드 ? r.필드.includes(t) : false; }
    if (점 === "포커스") return 탭결과.간곳.includes(a + "-" + t);
    return 탭결과.검증[a + "-" + t];
  };
  const 점들 = ["제출", "포커스", "검증"];
  const O = [(칸("속성 · 대상", 22) + 점들.map(p => 칸(p, 8)).join("")).trimEnd()];
  let 갈림 = 0, 전체 = 0, 명세갈림 = 0, 명세전체 = 0;
  for (const a of 속성) for (const t of 대상) {
    let 행 = 칸(a + " · " + t, 22);
    for (const p of 점들) {
      const v = 셈(a, t, p);
      if (a !== "없음") { 전체++; 갈림 += v !== 셈("없음", t, p); }
      명세전체++; 명세갈림 += v !== 명세[a][t][점들.indexOf(p)];
      행 += 칸(v ? "예" : "—", 8);
    }
    O.push(행.trimEnd());
  }
  O.push("(제출 = 서버가 받은 필드에 그 이름이 있나 · 포커스 = 진짜 Tab 열여덟 번 안에 닿았나 · 검증 = willValidate)");
  O.push("Tab 이 닿은 곳 = " + 탭결과.간곳.join(" → "));
  for (const k of [0, 1, 2]) O.push("폼" + k + " 의 기록 = " + (결과[k].기록.join(" → ") || "(없음)") + " · 서버 필드 = " + (결과[k].필드 ? (결과[k].필드.join(",") || "(빈 본문)") : "(요청 없음)"));
  O.push("「없음」과 갈린 칸 = " + 갈림 + " / " + 전체);
  O.push("명세 열과 갈린 칸 = " + 명세갈림 + " / " + 명세전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 45 칸 각각은 「예」인가 「—」인가? 「「없음」과 갈린 칸 N / 30」의 N 은?
- 폼1(`disabled`)의 `requestSubmit(disabled 단추)` 는 제출이 되나? 되면 서버 필드는?
- Tab 열여덟 번이 닿은 순서는?

### 2. `readonly` 칸 여덟과 짝 · `required` 와 겹친 세 폼 (예측)

```html
<!-- html29b-30-readonly.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>30 readonly 가 닿는 곳</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<div id="자리"></div>
<form id="가" action="/r" method="post"><input name="t" readonly required><button id="가보냄">보냄</button></form>
<form id="나" action="/r" method="post"><input name="c" type="checkbox" readonly required><button id="나보냄">보냄</button></form>
<form id="다" action="/r" method="post"><input name="t" required><button id="다보냄">보냄</button></form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
// [이름, 만들기, 진짜 키 편집, 값 읽기]
const 줄 = [
  ["text", () => Object.assign(document.createElement("input"), { value: "가" }), s => [["key", s, "End", "End", 35], ["type", s, "x"]], e => e.value],
  ["number", () => Object.assign(document.createElement("input"), { type: "number", value: "1" }), s => [["key", s, "ArrowUp", "ArrowUp", 38]], e => e.value],
  ["date", () => Object.assign(document.createElement("input"), { type: "date", value: "2026-01-01" }), s => [["key", s, "ArrowUp", "ArrowUp", 38]], e => e.value],
  ["range", () => Object.assign(document.createElement("input"), { type: "range", value: "50" }), s => [["key", s, "ArrowRight", "ArrowRight", 39]], e => e.value],
  ["checkbox", () => Object.assign(document.createElement("input"), { type: "checkbox" }), s => [["key", s, " ", "Space", 32, " "]], e => String(e.checked)],
  ["radio", () => Object.assign(document.createElement("input"), { type: "radio" }), s => [["key", s, " ", "Space", 32, " "]], e => String(e.checked)],
  ["select", () => { const e = document.createElement("select"); e.append(new Option("가", "가"), new Option("나", "나")); return e; }, s => [["key", s, "ArrowDown", "ArrowDown", 40]], e => e.value],
  ["textarea", () => Object.assign(document.createElement("textarea"), { value: "가" }), s => [["key", s, "End", "End", 35], ["type", s, "x"]], e => e.value],
];
const 자리 = document.getElementById("자리");
for (const [t, 만들기] of 줄) for (const 앞 of ["ro", "tw"]) {
  const e = 만들기(); e.id = 앞 + "-" + t; e.name = 앞 + t;
  if (앞 === "ro") e.setAttribute("readonly", "");
  자리.append(e);
}
const 편집 = 줄.flatMap(([t, , 키]) => [...키("#ro-" + t), ...키("#tw-" + t)]);
const 읽기 = "JSON.stringify(Object.fromEntries([...document.querySelectorAll('#자리 [id]')].map(e => [e.id, [e.type === 'checkbox' || e.type === 'radio' ? String(e.checked) : e.value, e.willValidate, e.matches(':read-only')]])))";
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [
  { 이름: "편집 전", 단계: [], 뒤: 읽기 },
  { 이름: "진짜 키로 편집", 단계: 편집, 뒤: 읽기 },
  { 이름: "가(text readonly required 빈 칸) · 보냄", 단계: [["js", "(() => { const i = document.getElementById('가').t; 적기('valueMissing=' + i.validity.valueMissing + ' · willValidate=' + i.willValidate + ' · :invalid=' + i.matches(':invalid')); return 1; })()"], ["click", "#가보냄"]] },
  { 이름: "나(checkbox readonly required 안 켬) · 보냄", 단계: [["js", "(() => { const i = document.getElementById('나').c; 적기('valueMissing=' + i.validity.valueMissing + ' · willValidate=' + i.willValidate + ' · :invalid=' + i.matches(':invalid')); return 1; })()"], ["click", "#나보냄"]] },
  { 이름: "다(text required 빈 칸 · readonly 없음) · 보냄", 단계: [["js", "(() => { const i = document.getElementById('다').t; 적기('valueMissing=' + i.validity.valueMissing + ' · willValidate=' + i.willValidate + ' · :invalid=' + i.matches(':invalid')); return 1; })()"], ["click", "#다보냄"]] },
];
window.__종합 = 결과 => {
  const A = JSON.parse(결과[0].뒤), B = JSON.parse(결과[1].뒤);
  const O = [칸("type", 10) + 칸("readonly 칸: 전 → 뒤", 30) + 칸("짝(속성 없음): 전 → 뒤", 30) + 칸("willValidate", 14) + ":read-only"];
  let 막음 = 0;
  for (const [t] of 줄) {
    const r = "ro-" + t, w = "tw-" + t;
    const 막았나 = A[r][0] === B[r][0] && A[w][0] !== B[w][0];
    막음 += 막았나;
    O.push(칸(t, 10) + 칸(JSON.stringify(A[r][0]) + " → " + JSON.stringify(B[r][0]), 30) + 칸(JSON.stringify(A[w][0]) + " → " + JSON.stringify(B[w][0]), 30)
      + 칸(A[r][1] + " / " + A[w][1], 14) + A[r][2] + " / " + A[w][2]);
  }
  O.push("(willValidate · :read-only 는 「readonly 칸 / 짝」)");
  O.push("readonly 가 사용자 편집을 막은 칸 = " + 막음 + " / " + 줄.length);
  O.push("");
  for (const r of 결과.slice(2)) O.push(r.이름 + "\n  페이지  " + r.기록.join(" → ") + "\n  서버    " + (r.요청.length ? r.서버.find(l => l.trim().startsWith("필드")).trim() : "(받은 요청 없음)"));
  return O.join("\n");
};
</script>
</body>
</html>
```

- 타입마다 진짜 키 편집 뒤의 값(`readonly` 칸 / 짝) · `willValidate` · `:read-only` 는? 「편집을 막은 칸 N / 8」의 N 은?
- 세 폼 각각의 `valueMissing` · `willValidate` · `:invalid` 와 제출 결과는?

### 3. `autofocus` 두 판 (예측)

```html
<!-- html29b-30-autofocus.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>30 autofocus</title>
</head>
<body>
<input id="a0">
<dialog id="창1"><input id="d0"><input id="d1" autofocus></dialog>
<dialog id="창2"><p>글</p><input id="e0"><input id="e1"></dialog>
<input id="a1" autofocus>
<input id="a2" autofocus>
<p id="p1">아래</p>
<script>
const 곳 = () => document.activeElement.id || document.activeElement.tagName;
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
window.__끝 = async () => {
  await 두틀();
  const O = ["주소의 조각 = " + JSON.stringify(location.hash) + " · document.hasFocus() = " + document.hasFocus()];
  O.push("로드 뒤 포커스 = " + 곳());
  const 창1 = document.getElementById("창1"), 창2 = document.getElementById("창2");
  창1.showModal(); O.push("창1.showModal() 뒤 = " + 곳()); 창1.close();
  창1.show();      O.push("창1.show() 뒤 = " + 곳()); 창1.close();
  창2.showModal(); O.push("창2.showModal() 뒤 (autofocus 없음) = " + 곳()); 창2.close();
  return O.join("\n");
};
</script>
</body>
</html>
```

- 그냥 열었을 때와 주소에 `#p1` 을 붙여 열었을 때, 각 줄의 포커스는?

### 4. `autocomplete` 열일곱 · `inputmode` 일곱 (예측)

```html
<!-- html29b-30-hints.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>30 autocomplete 와 inputmode</title>
<script src="html29b-30-hints-spec.js"></script>
</head>
<body>
<form id="f1">
  <input id="c1" autocomplete="email">
  <input id="c2" autocomplete="EMAIL">
  <input id="c3" autocomplete="shipping email">
  <input id="c4" autocomplete="Shipping email">
  <input id="c5" autocomplete="section-A billing tel">
  <input id="c6" autocomplete="home email">
  <input id="c7" autocomplete="home name">
  <input id="c8" autocomplete="email shipping">
  <input id="c9" autocomplete="e-mail">
  <input id="c10" autocomplete="off">
  <input id="c11" autocomplete="shipping off">
  <input id="c12" type="password" autocomplete="current-password webauthn">
  <input id="c13" autocomplete="">
  <input id="c14">
  <textarea id="c15" autocomplete="street-address"></textarea>
  <select id="c16" autocomplete="country"><option>가</option></select>
</form>
<form id="f2" autocomplete="off"><input id="c17"></form>
<div id="m">
  <input id="m1" inputmode="numeric">
  <input id="m2" inputmode="NUMERIC">
  <input id="m3" inputmode="decimal">
  <input id="m4" inputmode="none">
  <input id="m5" inputmode="zzz">
  <input id="m6">
  <input id="m7" type="number">
</div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 모두 = [...document.querySelectorAll("[id^=c], [id^=m]")].filter(e => /^[cm]\d+$/.test(e.id));
window.__대상 = 모두.map(e => [e.id, "#" + e.id]);
window.__끝 = () => {
  const O = [칸("id", 5) + 칸("속성 글자", 34) + 칸("IDL 값", 30) + 칸("명세 열", 30) + "접근성 노드의 속성"];
  let 갈림 = 0, 전체 = 0;
  const 트리이름 = new Set();
  for (const e of 모두) {
    const 자동 = e.id.startsWith("c");
    const 글자 = 자동 ? (e.hasAttribute("autocomplete") ? JSON.stringify(e.getAttribute("autocomplete")) : "(속성 없음)" + (e.form && e.form.id === "f2" ? " · form off" : ""))
                    : (e.hasAttribute("inputmode") ? "inputmode=" + JSON.stringify(e.getAttribute("inputmode")) : "(속성 없음)" + (e.type === "number" ? " · type=number" : ""));
    const 값 = 자동 ? e.autocomplete : e.inputMode;
    const 기대 = 명세값[e.id];
    전체++; 갈림 += 값 !== 기대;
    const 속성 = Object.entries(__AX[e.id].속성).map(([k, v]) => k + "=" + v);
    속성.forEach(x => 트리이름.add(x.split("=")[0]));
    O.push(칸(e.id, 5) + 칸(글자, 34) + 칸(JSON.stringify(값), 30) + 칸(JSON.stringify(기대), 30) + (속성.join(" ") || "(없음)"));
  }
  O.push("명세 열과 갈린 칸 = " + 갈림 + " / " + 전체);
  O.push("접근성 노드에 나온 속성 이름 = " + [...트리이름].sort().join(" · "));
  return O.join("\n");
};
</script>
</body>
</html>
```

- 칸마다 IDL 값(`autocomplete` · `inputMode`)은? 접근성 노드의 속성 이름에 두 속성의 흔적이 있는가?

### 5. `readonly` 가 붙지 않는 컨트롤 (왜)

- 명세가 `readonly` 를 텍스트 컨트롤에만 적용하는 이유로 드는 문장은? `select`·`button` 은 어떻게 다른가?

### 6. 두 문장이 부딪히는 자리 (경계)

- Checkbox 상태의 「적용되지 않는」 목록과 `readonly` 절의 제약 검증 문장을 나란히 두면 `readonly` 체크박스의 `willValidate` 는 어느 쪽으로 읽히나? 이 판의 Chrome 은?

### 7. `readonly` + `required` (경계)

- 빈 글자 칸과 안 켠 체크박스에서 각각 `valueMissing` 이 갈리는 명세 문장은? 둘 다 제출이 막히지 않은 이유는?

### 8. `requestSubmit` 과 비활성 단추 (경계)

- 명세의 `requestSubmit(단추)` 가 검사하는 두 조건은? 비활성 단추를 넘기면 그 단추의 `name` 은 왜 안 실리나?

### 9. `inputmode` 가 바꾸는 것 (경계)

- 「`inputmode="numeric"` 이면 숫자 자판이 뜬다」를 이 판은 확인했나? 이 판이 잰 것과 못 잰 것을 갈라 대면?

### 10. 명세·구현·관찰 가르기 (연결)

- 「`autocomplete="EMAIL"` 의 IDL 이 `"email"`」·「`readonly` 체크박스가 검증에서 빠진다」·「조각이 있으면 `autofocus` 가 안 먹는다」는 각각 어느 층인가?

### 11. 정본 경계 긋기 (연결)

- `disabled`/`readonly` 의 제출 · `fieldset[disabled]` · 포커스 순서와 `tabindex` · `dialog` 의 포커스 트랩 · `:read-only` 로 칠하기의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
