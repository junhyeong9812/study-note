# html/syntax/29 — 제약 검증: 유효성 상태·`novalidate`·`:valid`/`:user-invalid` 의 관계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **`matches()` 의 참·거짓과 서버가 받은 필드**다(검증 풍선의 문구가 아니다). 의사 클래스는 칸마다 「**맞나 / 안 맞나**」로, 제출은 「**서버가 몇 번 받았나 · 무엇을 받았나**」로 답하라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 1번 페이지가 읽는 「명세 열」 파일(`html29b-29-spec.js`)은 **답이 들어 있어서** 이 파일에 싣지 않는다 — 정리·정답 파일에 있다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [28번 주제](../28-validation-attributes/1-question.md) · [21번 주제](../21-form-submission-model/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 칸 셋 · 의사 클래스 넷 · 시점 여섯 (예측)

```html
<!-- html29b-29-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>29 의사 클래스와 시점</title>
<script src="html29b-rec.js"></script>
<script src="html29b-29-spec.js"></script>
</head>
<body>
<form id="f" action="/r" method="post">
  <input id="r" name="r" required>
  <input id="e" name="e" type="email" value="ab">
  <input id="ok" name="ok" required value="가">
  <button id="보냄">보냄</button>
</form>
<script>
addEventListener("change", e => 적기("change(" + e.target.id + ")"), true);
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 상태 = { r: "빈 required", e: "type=email 값 ab", ok: "required 값 가" };
const 의사 = [":valid", ":invalid", ":user-valid", ":user-invalid"];
// 칸의 유효 여부는 시점마다 그대로 둔다 — 스크립트·키 입력 모두 같은 쪽의 값을 넣는다
const 대입 = { r: "", e: "cd", ok: "나" };
const 키 = {
  r: id => [["type", "#" + id, "x"], ["keyhere", "Backspace", "Backspace", 8]],
  e: id => [["key", "#" + id, "End", "End", 35], ["type", "#" + id, "d"]],
  ok: id => [["key", "#" + id, "End", "End", 35], ["type", "#" + id, "다"]],
};
const 시점 = [
  ["T1", "로드 직후", id => []],
  ["T2", "스크립트 대입 뒤", id => [["js", "document.getElementById('" + id + "').value = " + JSON.stringify(대입[id]) + "; 1"]]],
  ["T3", "진짜 키 입력 뒤(포커스 중)", id => 키[id](id)],
  ["T4", "진짜 키 입력 → Tab", id => [...키[id](id), ["keyhere", "Tab", "Tab", 9]]],
  ["T5", "제출 단추 클릭 뒤", id => [["click", "#보냄"]]],
  ["T6", "제출 단추 클릭 → reset()", id => [["click", "#보냄"], ["js", "document.getElementById('f').reset(); 1"]]],
];
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [];
for (const [t, , 단계] of 시점) for (const id of Object.keys(상태)) {
  const e = "document.getElementById('" + id + "')";
  window.__시도.push({ 이름: t + " " + id, 단계: 단계(id),
    뒤: "JSON.stringify({ v: " + e + ".value, m: " + JSON.stringify(의사) + ".map(p => " + e + ".matches(p)) })" });
}
window.__종합 = 결과 => {
  const S = Object.fromEntries(결과.map(r => [r.이름, JSON.parse(r.뒤)]));
  const O = [(칸("칸 · 의사 클래스", 30) + 시점.map(([t]) => 칸(t, 5)).join("")).trimEnd()];
  let 갈림 = 0, 전체 = 0, 명세갈림 = 0, 명세전체 = 0;
  for (const id of Object.keys(상태)) {
    의사.forEach((p, k) => {
      let 행 = 칸(id + " " + p, 30);
      for (const [t] of 시점) {
        const 맞음 = S[t + " " + id].m[k];
        if (t !== "T1") { 전체++; 갈림 += 맞음 !== S["T1 " + id].m[k]; }
        명세전체++; 명세갈림 += 맞음 !== 명세맞음(id, t, p);
        행 += 칸(맞음 ? "예" : "·", 5);
      }
      O.push(행.trimEnd());
    });
  }
  O.push("");
  const 기록 = Object.fromEntries(결과.map(r => [r.이름, r.기록]));
  for (const [t, 설명] of 시점) O.push(t + " = " + 설명 + " · 값 " + Object.keys(상태).map(id => id + "=" + JSON.stringify(S[t + " " + id].v)).join(" ")
    + " · change 이벤트 " + Object.keys(상태).map(id => id + "=" + 기록[t + " " + id].filter(x => x.startsWith("change")).length).join(" "));
  O.push("로드 직후(T1)와 갈린 칸 = " + 갈림 + " / " + 전체);
  O.push("명세 열과 갈린 칸 = " + 명세갈림 + " / " + 명세전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 72 칸 각각은 맞나 안 맞나? 「로드 직후(T1)와 갈린 칸 N / 60」의 N 은?
- `T4` 에서 세 칸의 `change` 이벤트는 각각 몇 번인가?
- 명세 열(user validity 가 서는 문장 + Selectors 4)과 갈리는 칸이 있는가? 있다면 어느 칸이고 왜 그런가?

### 2. 같은 무효 값의 다섯 시도 (예측)

```html
<!-- html29b-29-submit.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>29 검증을 건너는 길</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="가" action="/r" method="post">
  <input type="email" name="addr" value="아무 글자" required>
  <input type="number" name="age" value="-5" min="0">
  <button id="가보냄">보냄</button>
  <button id="가건넘" formnovalidate>formnovalidate 단추</button>
</form>
<form id="나" action="/r" method="post" novalidate>
  <input type="email" name="addr" value="아무 글자" required>
  <input type="number" name="age" value="-5" min="0">
  <button id="나보냄">보냄</button>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 깃발 = id => "(() => { const f = document.getElementById('" + id + "'); 적기('깃발 addr.typeMismatch=' + f.addr.validity.typeMismatch + ' · age.rangeUnderflow=' + f.age.validity.rangeUnderflow + ' · form:invalid=' + f.matches(':invalid')); return 1; })()";
window.__표 = "종합";
window.__시도 = [
  { 이름: "가 · 보냄 클릭", 단계: [["js", 깃발("가")], ["click", "#가보냄"]] },
  { 이름: "가 · formnovalidate 단추 클릭", 단계: [["js", 깃발("가")], ["click", "#가건넘"]] },
  { 이름: "나(novalidate) · 보냄 클릭", 단계: [["js", 깃발("나")], ["click", "#나보냄"]] },
  { 이름: "가 · 속성을 지운 뒤 보냄 클릭", 단계: [["js", "(() => { const f = document.getElementById('가'); f.addr.removeAttribute('required'); f.addr.type = 'text'; f.age.removeAttribute('min'); return 1; })()"], ["js", 깃발("가")], ["click", "#가보냄"]] },
  { 이름: "가 · fetch(URLSearchParams(FormData(가)))", 단계: [["js", 깃발("가")], ["js", "fetch('/r', { method: 'POST', body: new URLSearchParams(new FormData(document.getElementById('가'))) }).then(r => { 적기('fetch 응답 ' + r.status); return 1; })"]] },
];
window.__종합 = 결과 => {
  const O = [칸("시도", 42) + 칸("submit", 8) + 칸("invalid", 9) + 칸("서버 요청", 10) + "서버가 받은 addr · age"];
  let 받음 = 0;
  for (const r of 결과) {
    const 필드 = r.서버.find(l => l.trim().startsWith("필드"));
    받음 += r.요청.length > 0;
    O.push(칸(r.이름, 42) + 칸(r.기록.some(x => x.startsWith("submit")) ? "났다" : "—", 8)
      + 칸(String(r.기록.filter(x => x.startsWith("invalid")).length) + "번", 9) + 칸(r.요청.length + "번", 10)
      + (필드 ? 필드.trim().replace(/^필드\s+/, "") : "(없음)"));
  }
  O.push("서버가 무효한 값을 받은 시도 = " + 받음 + " / " + 결과.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 시도마다 `submit`·`invalid` 가 났나, 서버는 몇 번 받았나, 받은 `addr`·`age` 는?
- 시도마다 제출 직전에 적은 깃발 세 개는?

### 3. 스크립트로 묻는 검증 일곱 시도 (예측)

```html
<!-- html29b-29-api.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>29 스크립트로 묻는 검증</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="다" action="/r" method="post">
  <input id="c1" name="c1" value="가">
  <input id="c2" name="c2" required>
  <input id="c3" name="c3" type="email" value="ab">
  <button id="다보냄">보냄</button>
</form>
<form id="라" action="/r" method="post" novalidate>
  <input id="d1" name="d1" required>
  <button id="라보냄">보냄</button>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
document.getElementById("라").addEventListener("submit", e => e.preventDefault());
const $ = "document.getElementById";
const 적어 = 식 => ["js", "(() => { 적기(" + 식 + "); return 1; })()"];
const 사용자 = "'user-invalid=' + (['c1','c2','c3','d1'].filter(id => document.getElementById(id).matches(':user-invalid')).join(',') || '(없음)') + ' · 포커스=' + (document.activeElement.id || document.activeElement.tagName)";
window.__표 = "종합";
window.__시도 = [
  { 이름: "다.checkValidity()", 단계: [적어("'반환 ' + " + $ + "('다').checkValidity()"), 적어(사용자)] },
  { 이름: "다.reportValidity()", 단계: [적어("'반환 ' + " + $ + "('다').reportValidity()"), 적어(사용자)] },
  { 이름: "라(novalidate · submit 을 막음) · 보냄 클릭", 단계: [["click", "#라보냄"], 적어(사용자)] },
  { 이름: "c2 에 포커스만 주고 Tab", 단계: [["js", $ + "('c2').focus(); 1"], ["keyhere", "Tab", "Tab", 9], 적어(사용자)] },
  { 이름: "c2·c3 을 채우고 c1.setCustomValidity('이유') · 보냄", 단계: [
    ["js", $ + "('c2').value = '나'; " + $ + "('c3').value = 'a@b.c'; " + $ + "('c1').setCustomValidity('이유'); 1"],
    적어("'c1.customError=' + " + $ + "('c1').validity.customError + ' · c1:invalid=' + " + $ + "('c1').matches(':invalid')"), ["click", "#다보냄"]] },
  { 이름: "같은 뒤 c1 을 진짜 키로 고치고 보냄", 단계: [
    ["js", $ + "('c2').value = '나'; " + $ + "('c3').value = 'a@b.c'; " + $ + "('c1').setCustomValidity('이유'); 1"],
    ["type", "#c1", "다"], 적어("'c1.value=' + " + $ + "('c1').value + ' · c1.customError=' + " + $ + "('c1').validity.customError"), ["click", "#다보냄"]] },
  { 이름: "같은 뒤 setCustomValidity('') · 보냄", 단계: [
    ["js", $ + "('c2').value = '나'; " + $ + "('c3').value = 'a@b.c'; " + $ + "('c1').setCustomValidity('이유'); " + $ + "('c1').setCustomValidity(''); 1"],
    적어("'c1.customError=' + " + $ + "('c1').validity.customError"), ["click", "#다보냄"]] },
];
window.__종합 = 결과 => {
  const O = [];
  for (const r of 결과) {
    O.push(r.이름);
    O.push("  페이지  " + r.기록.join(" → "));
    O.push("  서버    " + (r.요청.length ? r.요청.map(q => q.메서드 + " " + q.경로).join(", ") + " · " + r.서버.find(l => l.trim().startsWith("필드")).trim() : "(받은 요청 없음)"));
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

- 시도마다 페이지 기록(`invalid` 수 · 반환값 · `:user-invalid` 인 칸 · 포커스)과 서버가 받은 것은?

### 4. `:invalid` 가 로드 직후부터 맞는 이유 (왜)

- `:invalid` 가 읽는 것과 `:user-invalid` 가 하나 더 읽는 것은 각각 무엇인가?

### 5. `novalidate` 폼인데 깃발이 서는 이유 (왜)

- 명세의 제출 알고리즘에서 `novalidate` 가 끄는 단계는 어디이고, 깃발은 왜 그대로인가?

### 6. 도장이 찍히는 자리와 지워지는 자리 (경계)

- 명세에서 user validity 를 참으로 두는 문장 둘과 거짓으로 두는 문장 하나는?
- 제출 시도가 도장을 찍는 단계는 검증 단계보다 앞인가 뒤인가? 그 순서가 만드는 결과는?

### 7. 원래대로 돌아온 편집 (경계)

- 빈 칸에 `x` 를 쳤다 지우고 Tab 으로 떠났을 때, 명세의 focus update steps 문장대로면 도장이 찍히나? 이 판은?
- 그 칸을 「명세 이탈」로 세지 않은 이유는?

### 8. `checkValidity` 대 `reportValidity` (경계)

- 두 호출이 같은 것과 갈리는 것은? 둘 중 `:user-invalid` 를 켜는 쪽이 있는가?

### 9. 서버 검증을 대체할 수 없다 (경계)

- 이 판이 서버에 무효한 값을 보낸 길 넷과 [21번](../21-form-submission-model/2-summary.md)의 한 길을 대면? 서버가 그 다섯을 가를 칸이 있나?
- 명세의 「Security」 절은 이 결과를 어떻게 적나?

### 10. 명세·구현·관찰 가르기 (연결)

- 「`reportValidity()` 가 첫 무효 칸으로 포커스를 옮긴다」·「`novalidate` 폼의 제출 시도가 `:user-invalid` 를 켠다」·「원래대로 돌아온 편집에 도장」은 각각 어느 층인가?

### 11. 정본 경계 긋기 (연결)

- 속성이 어느 깃발을 켜나 · 검증이 언제 도나 · `:user-invalid` 의 CSS 쪽 · `setCustomValidity` 자체 · `fetch` 본문의 정본은 각각 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
