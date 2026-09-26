# html/syntax/32 — `button` 의 `type` 과 폼 소유권: `form` 속성·`formaction`/`formmethod` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **서버가 받은 요청**이다 — 시도마다 「**요청이 갔나 · 어디로(메서드·경로) · `act` 는 무엇인가**」와 「**`submit`·`invalid` 가 났나**」로 답하라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 2번 페이지가 읽는 「명세 열」 파일(`html29b-32-spec.js`)은 **답이 들어 있어서** 이 파일에 싣지 않는다 — 정리·정답 파일에 있다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [21번 주제](../21-form-submission-model/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 폼 안의 단추 넷 · 폼 밖의 표본 아홉 (예측)

```html
<!-- html29b-32-accident.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>32 폼 안의 단추</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="주문" action="/r" method="post">
  <input id="수량" name="qty" value="1">
  <button id="더하기1">+</button>
  <button id="더하기2" type="button">+</button>
  <button id="열기" commandfor="창" command="show-modal">열기</button>
  <button id="열기2" type="button" commandfor="창" command="show-modal">열기</button>
</form>
<dialog id="창"><p>창</p></dialog>
<div id="표본">
  <button id="b1">type 없음</button>
  <button id="b2" type="submit">submit</button>
  <button id="b3" type="reset">reset</button>
  <button id="b4" type="button">button</button>
  <button id="b5" type="BUTTON">BUTTON</button>
  <button id="b6" type="zzz">zzz</button>
  <button id="b7" type="">빈 글자</button>
  <button id="b8" commandfor="창" command="show-modal">commandfor</button>
  <button id="b9" type="submit" commandfor="창" command="show-modal">submit + commandfor</button>
</div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
for (const id of ["더하기1", "더하기2"]) document.getElementById(id).addEventListener("click", () => {
  const q = document.getElementById("수량");
  q.value = String(Number(q.value) + 1);
  적기("손잡이가 올림 qty=" + q.value);
});
window.__표 = "종합";
const 뒤 = "JSON.stringify({ qty: document.getElementById('수량').value, 창: document.getElementById('창').open })";
window.__시도 = [
  { 이름: "type 없는 + 클릭", 단계: [["click", "#더하기1"]], 뒤 },
  { 이름: "type=button 인 + 클릭", 단계: [["click", "#더하기2"]], 뒤 },
  { 이름: "type 없는 commandfor 단추 클릭", 단계: [["click", "#열기"]], 뒤 },
  { 이름: "type=button 인 commandfor 단추 클릭", 단계: [["click", "#열기2"]], 뒤 },
  { 이름: "폼 밖 표본 b8 클릭", 단계: [["click", "#b8"]], 뒤 },
];
window.__종합 = 결과 => {
  const O = [];
  for (const r of 결과) {
    const S = r.뒤 ? JSON.parse(r.뒤) : null;
    O.push(칸(r.이름, 36) + "서버 " + r.요청.length + "번" + (r.필드 ? " " + r.서버.find(l => l.trim().startsWith("필드")).trim() : "")
      + " · 뒤 " + (S ? "qty=" + S.qty + " 창.open=" + S.창 : "(이동해서 없음)"));
  }
  O.push("");
  // 제출 단추인가 — 명세: 제출 단추가 아닌 button 은 제약 검증에서 빠진다 → willValidate 로 읽는다
  O.push(칸("id", 4) + 칸("속성", 56) + 칸(".type", 10) + "willValidate");
  for (const b of document.querySelectorAll("#표본 button")) {
    const 속성 = [...b.attributes].filter(a => a.name !== "id").map(a => a.name + "=" + JSON.stringify(a.value)).join(" ") || "(없음)";
    O.push(칸(b.id, 4) + 칸(속성, 56) + 칸(JSON.stringify(b.type), 10) + b.willValidate);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

- 다섯 시도 각각에서 서버는 무엇을 받았나? 페이지에 남았다면 `qty` 와 `창.open` 은?
- 표본 아홉의 `.type` 과 `willValidate` 는?

### 2. Enter 한 번 · 폼 열넷 (예측)

```html
<!-- html29b-32-implicit.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>32 Enter 와 단추 구성</title>
<script src="html29b-rec.js"></script>
<script src="html29b-32-spec.js"></script>
</head>
<body>
<div id="자리"></div>
<script>
addEventListener("submit", e => 적기("누른 " + (e.submitter ? e.submitter.value : "null")), true);
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
// 단추 구성 — [표시, 폼 앞(폼 밖)에 둘 것, 폼 안에 둘 것]
const 구성 = {
  A: ["단추 없음", "", ""],
  B: ["제출 단추", "", '<button name="act" value="go">보냄</button>'],
  C: ["type=button 만", "", '<button type="button" name="act" value="btn">단추</button>'],
  D: ["type=button 다음 제출 단추", "", '<button type="button" name="act" value="btn">단추</button><button name="act" value="go">보냄</button>'],
  E: ["type=reset 다음 제출 단추", "", '<button type="reset" name="act" value="rst">지움</button><button name="act" value="go">보냄</button>'],
  F: ["disabled 제출 단추 다음 제출 단추", "", '<button name="act" value="dis" disabled>보냄</button><button name="act" value="go">보냄</button>'],
  G: ["폼 앞의 form= 제출 단추 다음 안의 제출 단추", "OUT", '<button name="act" value="in">보냄</button>'],
};
const 자리 = document.getElementById("자리");
const 목록 = [];
for (const n of [1, 2]) for (const [k, [표시, 앞, 안]] of Object.entries(구성)) {
  const id = "f" + n + k;
  const 칸들 = '<input name="a" value="1">' + (n === 2 ? '<input name="b" value="2">' : "");
  자리.insertAdjacentHTML("beforeend", (앞 ? '<button form="' + id + '" name="act" value="out">밖</button>' : "")
    + '<form id="' + id + '" action="/r">' + 칸들 + 안 + "</form>");
  목록.push([id, n, k, 표시]);
}
window.__표 = "종합";
window.__시도 = 목록.map(([id, n, k, 표시]) => ({ 이름: id, 단계: [["enter", "#" + id + " input[name=a]"]] }));
window.__종합 = 결과 => {
  const O = [칸("폼", 5) + 칸("칸 수", 6) + 칸("단추 구성", 44) + 칸("제출", 6) + 칸("submitter", 11) + "서버가 받은 필드"];
  let 제출 = 0, 명세갈림 = 0;
  결과.forEach((r, i) => {
    const [id, n, k, 표시] = 목록[i];
    const s = r.기록.find(x => x.startsWith("누른 ")) || "";
    const 됨 = r.요청.length > 0;
    제출 += 됨; 명세갈림 += 됨 !== 명세제출[n + k];
    O.push(칸(id, 5) + 칸(String(n), 6) + 칸(표시, 44) + 칸(됨 ? "예" : "—", 6) + 칸(s ? s.slice(3) : "—", 11)
      + (됨 ? r.서버.find(l => l.trim().startsWith("필드")).trim().replace(/^필드\s+/, "") : "(요청 없음)"));
  });
  O.push("제출된 칸 = " + 제출 + " / " + 결과.length);
  O.push("명세 열과 갈린 칸 = " + 명세갈림 + " / " + 결과.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 폼마다 제출됐나, `submitter` 의 `value` 와 서버가 받은 필드는? 「제출된 칸 N / 14」의 N 은?
- 명세 열과 갈리는 칸이 있는가?

### 3. 단추 여섯의 폼 소유자 (예측)

```html
<!-- html29b-32-owner.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>32 단추의 폼 소유자</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="갑" action="/r"><input name="a" value="1"><button id="안단추" name="act" value="in">안</button></form>
<button id="밖단추" form="갑" name="act" value="out">밖</button>
<button id="없는폼단추" form="없음" name="act" value="none">없는 id</button>
<form id="을" action="/r2"><input name="b" value="2"><button id="을안갑" form="갑" name="act" value="inB">을 안</button></form>
<form id="겉" action="/r4"><input name="c" value="3"><form id="속" action="/r5"><button id="속단추" name="act" value="nest">속</button></form></form>
<button id="속가리킴" form="속" name="act" value="toNest">속을 가리킴</button>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 단추 = ["안단추", "밖단추", "없는폼단추", "을안갑", "속단추", "속가리킴"];
window.__표 = "종합";
window.__시도 = 단추.map(id => ({ 이름: id + " 클릭", 단계: [["click", "#" + id]] }));
window.__종합 = 결과 => {
  const O = [칸("단추", 12) + 칸("부모", 10) + 칸("form 속성", 10) + 칸("button.form", 13) + 칸("요청", 10) + "서버가 받은 필드"];
  결과.forEach((r, i) => {
    const b = document.getElementById(단추[i]);
    const 부모 = b.parentElement.tagName.toLowerCase() + (b.parentElement.id ? "#" + b.parentElement.id : "");
    O.push(칸(b.id, 12) + 칸(부모, 10) + 칸(b.getAttribute("form") || "(없음)", 10) + 칸(b.form ? "form#" + b.form.id : "null", 13)
      + 칸(r.요청.length ? r.요청.map(q => q.메서드 + " " + q.경로).join(",") : "없음", 10)
      + (r.요청.length ? r.서버.find(l => l.trim().startsWith("필드")).trim().replace(/^필드\s+/, "") : "—"));
  });
  O.push("form 개수 = " + document.forms.length + " · id = " + [...document.forms].map(f => f.id).join(" · "));
  return O.join("\n");
};
</script>
</body>
</html>
```

- 단추마다 `button.form` 과 눌렀을 때 서버가 받은 것은? `document.forms.length` 는?
- `--dump-dom` 에서 `<form id="속">` 은 보이나?

### 4. 한 폼 · 제출을 일으키는 열 가지 (예측)

```html
<!-- html29b-32-submitter.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>32 누가 제출했나</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r">
  <input id="q" name="q" value="1">
  <input id="빈" name="빈" required>
  <button id="첫" name="act" value="a" formaction="/r2" formmethod="post" formnovalidate>첫 단추</button>
  <button id="둘" name="act" value="b">둘째 단추</button>
  <button id="보통" type="button" name="act" value="c" formaction="/r3">type=button</button>
</form>
<form id="남" action="/r9"><button id="남단추">남의 단추</button></form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 폼 = "document.getElementById('폼')", $ = id => "document.getElementById('" + id + "')";
const 불러 = 식 => ["js", "(() => { try { " + 식 + "; 적기('반환됨'); } catch (e) { 적기('예외 ' + e.name); } return 1; })()"];
window.__표 = "종합";
window.__시도 = [
  { 이름: "첫 단추 클릭", 단계: [["click", "#첫"]] },
  { 이름: "둘째 단추 클릭", 단계: [["click", "#둘"]] },
  { 이름: "q 에서 Enter", 단계: [["enter", "#q"]] },
  { 이름: "requestSubmit()", 단계: [불러(폼 + ".requestSubmit()")] },
  { 이름: "requestSubmit(둘째)", 단계: [불러(폼 + ".requestSubmit(" + $("둘") + ")")] },
  { 이름: "requestSubmit(첫)", 단계: [불러(폼 + ".requestSubmit(" + $("첫") + ")")] },
  { 이름: "submit()", 단계: [불러(폼 + ".submit()")] },
  { 이름: "type=button 단추 클릭", 단계: [["click", "#보통"]] },
  { 이름: "requestSubmit(type=button 단추)", 단계: [불러(폼 + ".requestSubmit(" + $("보통") + ")")] },
  { 이름: "requestSubmit(남의 폼 단추)", 단계: [불러(폼 + ".requestSubmit(" + $("남단추") + ")")] },
];
window.__종합 = 결과 => {
  const O = [칸("시도", 34) + 칸("submit", 8) + 칸("invalid", 9) + 칸("요청", 11) + 칸("서버가 받은 필드", 30) + "호출"];
  for (const r of 결과) {
    const 필드 = r.요청.length ? r.서버.find(l => l.trim().startsWith("필드")).trim().replace(/^필드\s+/, "") : "—";
    const 호출 = r.기록.find(x => x === "반환됨" || x.startsWith("예외")) || "—";
    O.push(칸(r.이름, 34) + 칸(r.기록.some(x => x.startsWith("submit(")) ? "났다" : "—", 8) + 칸(r.기록.some(x => x.startsWith("invalid")) ? "났다" : "—", 9)
      + 칸(r.요청.length ? r.요청.map(q => q.메서드 + " " + q.경로).join(",") : "없음", 11) + 칸(필드, 30) + 호출);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

- 시도마다 `submit`·`invalid` 가 났나, 요청의 메서드·경로와 필드, 호출이 예외를 던졌다면 그 이름은?

### 5. `type` 없는 `button` 이 제출하는 이유 (왜)

- 명세의 `type` 누락 기본값은 어느 상태이고, 그 상태의 `button` 이 제출 단추가 되는 조건 셋은?

### 6. 폼 안의 `commandfor` 단추가 조용한 이유 (왜)

- 명세의 `button` 활성화 동작에서 `commandfor` 를 보는 단계는 어디이고, 그 앞에서 무엇이 돌아가나?

### 7. 기본 단추 (경계)

- 명세의 「기본 단추」 정의는? `type=button`·`type=reset`·`disabled` 단추·폼 앞의 `form=` 단추는 각각 그 정의에서 어떻게 되나?

### 8. Enter 와 제출자의 설정 (경계)

- Enter 로 제출할 때 `formaction`·`formmethod`·`formnovalidate`·`name`/`value` 는 어느 단추의 것이 쓰이나? 그 이유는?

### 9. `requestSubmit` 대 `submit()` (경계)

- 단추 없는 `requestSubmit()`·`requestSubmit(단추)`·`submit()` 이 검증·`submit` 이벤트·단추의 설정에서 각각 어떻게 갈리나? `requestSubmit` 이 예외를 던지는 두 조건은?

### 10. 명세·구현·관찰 가르기 (연결)

- 「`commandfor` 만 있는 단추의 `.type` 이 `"button"`」·「첫 제출 단추가 `disabled` 면 Enter 가 아무것도 안 한다」·「`form="없는id"` 단추는 소유자가 없다」는 각각 어느 층인가?

### 11. 정본 경계 긋기 (연결)

- 제출을 일으키는 것 열여섯 시도 · `input` 의 `form` 속성 · 누른 단추만 실린다 · 중첩 `form` · `dialog` 를 여는 것의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
