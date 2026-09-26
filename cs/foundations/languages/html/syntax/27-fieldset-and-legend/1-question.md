# html/syntax/27 — `fieldset`/`legend` 와 그룹 비활성화 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **칸마다 네 물음**(`:disabled` · 포커스 · 진짜 클릭 · 제출)이다. 한 칸의 네 답이 **서로 어긋나는지**도 예측해 보라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 1번 페이지가 읽는 「명세 열」 파일(`html25b-27-spec.js`)은 **답이 들어 있어서** 이 파일에 싣지 않는다 — 정리·정답 파일에 있다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [25번 주제](../25-label-association/1-question.md) · [24번 주제](../24-input-types-choice-special/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 비활성 `fieldset` 안팎의 열네 칸 (예측)

```html
<!-- html25b-27-spread.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>27 비활성화가 퍼지는 곳</title>
<script src="html25b-rec.js"></script>
<script src="html25b-27-spec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post">
<fieldset id="바깥" disabled>
  <legend>첫 범례 <input name="lg1" id="lg1" value="첫 범례 안"></legend>
  <legend>둘째 범례 <input name="lg2" id="lg2" value="둘째 범례 안"></legend>
  <input name="i1" id="i1" value="입력">
  <input name="rq" id="rq" required>
  <input type="checkbox" name="c1" id="c1">
  <select name="s1" id="s1"><option>가</option></select>
  <textarea name="t1" id="t1">글</textarea>
  <button name="b1" id="b1" value="안쪽 단추">안쪽 단추</button>
  <fieldset id="안쪽">
    <legend>안쪽 범례 <input name="lg3" id="lg3" value="안쪽 범례 안"></legend>
    <input name="i2" id="i2" value="안쪽 입력">
  </fieldset>
  <a href="#x" id="a1">링크</a>
  <span tabindex="0" id="sp">tabindex 글자</span>
</fieldset>
<fieldset id="뒤범례" disabled>
  <div>앞 div</div>
  <legend>첫 자식 아닌 범례 <input name="lg4" id="lg4" value="첫 자식 아닌 범례 안"></legend>
</fieldset>
<input name="o1" id="o1" value="바깥 입력">
<button id="보냄" name="보냄" value="1">보냄</button>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
// [표시, id, 제출 칸이 성립하나] — 명세 열은 html25b-27-spec.js 가 따로 든다
const 행 = [
  ["첫 legend 안의 input", "lg1", true],
  ["둘째 legend 안의 input", "lg2", true],
  ["input", "i1", true],
  ["required 인데 빈 input", "rq", true],
  ["checkbox", "c1", true],
  ["select", "s1", true],
  ["textarea", "t1", true],
  ["button (제출 단추)", "b1", false],
  ["안쪽 fieldset 의 legend 안 input", "lg3", true],
  ["안쪽 fieldset 의 input", "i2", true],
  ["a[href]", "a1", false],
  ["span[tabindex]", "sp", false],
  ["첫 자식이 아닌 첫 legend 안 input", "lg4", true],
  ["fieldset 밖 input", "o1", true],
];
window.__받음 = [];
document.getElementById("c1").checked = true;
for (const [, id] of 행) document.getElementById(id).addEventListener("click", e => { __받음.push(id); if (id === "a1" || id === "b1") e.preventDefault(); });
const 뒤 = id => "JSON.stringify({ 받음: __받음.includes('" + id + "'), 켜짐: document.getElementById('" + id + "').checked === true })";
window.__표 = "종합";
window.__시도 = [
  ...행.map(([이름, id]) => ({ 이름: "클릭 " + 이름, 단계: [["click", "#" + id]], 뒤: 뒤(id) })),
  { 이름: "보냄", 단계: [["click", "#보냄"]] },
];
window.__종합 = 결과 => {
  const 필드 = 결과[결과.length - 1].필드 || [];
  const O = [칸("칸", 34) + 칸(":disabled", 10) + 칸("focus()", 9) + 칸("클릭", 9) + 칸("실림", 9) + 칸("명세", 9) + "명세와"];
  let 퍼짐 = 0, 전체 = 0, 갈림 = 0;
  for (const [k, [이름, id, 제출]] of 행.entries()) {
    const 명세 = 명세상비활성[id];
    const e = document.getElementById(id);
    const 비활성 = e.matches(":disabled");
    e.focus(); const 포커스 = document.activeElement === e; e.blur();
    const r = JSON.parse(결과[k].뒤);
    const 클릭 = r.받음;
    const 실림 = 제출 ? 필드.includes(id) : null;
    const 막힘 = [비활성, !포커스, !클릭, 실림 === null ? null : !실림];
    const 셈 = 막힘.filter(x => x !== null);
    퍼짐 += 셈.filter(x => x).length; 전체 += 셈.length;
    const 같나 = 셈.every(x => x === 명세);
    if (!같나) 갈림++;
    O.push(칸(이름, 34) + 칸(비활성 ? "매치" : "—", 10) + 칸(포커스 ? "감" : "안 감", 9) + 칸(클릭 ? "받음" : "안 받음", 9)
      + 칸(실림 === null ? "(부적용)" : 실림 ? "실림" : "—", 9) + 칸(명세 ? "disabled" : "아님", 9) + (같나 ? "같다" : "★ 갈림"));
  }
  O.push("");
  O.push("fieldset 자신의 :disabled — 바깥=" + document.getElementById("바깥").matches(":disabled") + " · 안쪽=" + document.getElementById("안쪽").matches(":disabled") + " · 뒤범례=" + document.getElementById("뒤범례").matches(":disabled"));
  O.push("퍼진 칸 = " + 퍼짐 + " / " + 전체 + "  (disabled 처럼 군 칸 — :disabled 매치 · 포커스 안 감 · 클릭 안 받음 · 안 실림)");
  O.push("명세 열과 갈린 행 = " + 갈림 + " / " + 행.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 칸마다 `:disabled` 매치 · `focus()` 뒤 `activeElement` 가 그 칸인가 · 진짜로 눌렀을 때 그 칸의 `click` 리스너가 불리나는?
- `보냄` 을 누르면 제출이 일어나나? 일어나면 서버가 받는 필드는?
- 세 `fieldset` 자신의 `:disabled` 는? 「퍼진 칸 N / 53」의 N 은?

### 2. 묶음 아홉의 이름 (예측)

```html
<!-- html25b-27-name.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>27 묶음의 이름</title>
</head>
<body>
<fieldset id="f1"><legend>배송 방법</legend><label><input type="radio" name="r1" id="r1"> 택배</label><label><input type="radio" name="r1"> 방문</label></fieldset>
<fieldset id="f2"><div>안내 글</div><legend>배송 방법</legend><label><input type="radio" name="r2"> 택배</label></fieldset>
<fieldset id="f3"><div><legend>배송 방법</legend></div><label><input type="radio" name="r3"> 택배</label></fieldset>
<fieldset id="f4"><legend>첫 범례</legend><legend>둘째 범례</legend><label><input type="radio" name="r4"> 택배</label></fieldset>
<fieldset id="f5" aria-label="에어리아 이름"><legend>배송 방법</legend><label><input type="radio" name="r5"> 택배</label></fieldset>
<fieldset id="f6" title="제목 이름"><label><input type="radio" name="r6"> 택배</label></fieldset>
<fieldset id="f7"><label><input type="radio" name="r7"> 택배</label></fieldset>
<div id="f8" role="radiogroup" aria-labelledby="h8"><span id="h8">배송 방법</span><label><input type="radio" name="r8"> 택배</label></div>
<div id="f9"><span>배송 방법</span><label><input type="radio" name="r9"> 택배</label></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 행 = [
  ["f1", "legend 가 첫 자식"], ["f2", "legend 앞에 div"], ["f3", "legend 가 div 안(자식 아님)"],
  ["f4", "legend 둘"], ["f5", "aria-label + legend"], ["f6", "title 만"], ["f7", "이름 없음"],
  ["f8", "div role=radiogroup + aria-labelledby"], ["f9", "그냥 div"],
];
window.__대상 = 행.map(([id]) => [id, "#" + id]);
window.__내부 = true;
window.__끝 = () => {
  const O = [칸("id", 4) + 칸("무엇을", 38) + 칸("역할", 12) + 칸("이름", 18) + "nameFrom"];
  for (const [id, 무엇] of 행) {
    const a = __AX[id], n = __INT[id];
    O.push(칸(id, 4) + 칸(무엇, 38) + 칸(a.역할 || (a.무시 ? "(무시됨)" : "(없음)"), 12) + 칸(JSON.stringify(a.이름), 18) + ((n && n.속성.nameFrom) || "(없음)"));
  }
  const 이름있는묶음 = 행.filter(([id]) => __AX[id].이름 !== "").length;
  O.push("");
  O.push("이름이 있는 묶음 = " + 이름있는묶음 + " / " + 행.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 묶음마다의 역할 · 이름 · `nameFrom` 은?
- 「이름이 있는 묶음 N / 9」의 N 은?

### 3. 비활성의 정의 (왜)

- 명세가 「폼 컨트롤이 disabled 다」라고 정한 두 조건은?
- 속성이 없는 안쪽 `fieldset` 이 `:disabled` 에 매치하는 이유는?

### 4. `legend` 안의 칸 (왜)

- 예외가 되는 것은 정확히 어떤 요소의 자손인가? 「첫 자식」과 「첫 `legend` 자식」은 어떻게 다른가?
- 안쪽 `fieldset` 의 첫 `legend` 안에 있는 칸이 예외가 못 되는 이유는?

### 5. 비활성 칸과 제출·검증 (왜)

- 비활성 칸이 제출에 안 실리는 것은 명세의 어느 단계인가?
- 비활성 묶음 안의 `required` 빈 칸이 제출을 막지 않는 이유는?

### 6. 진짜 클릭과 `click()` (경계)

- 비활성 칸에 진짜 클릭이 `click` 리스너를 부르지 않는 것은 명세의 어느 문장인가?
- 스크립트의 `click()` 은 비활성 칸에서 어떻게 되나(명세)?

### 7. 비활성 묶음 안의 링크와 `tabindex` (경계)

- 비활성 묶음 안에서도 포커스·클릭이 되는 요소는? 왜인가?

### 8. 라디오 묶음의 이름 (경계)

- `legend` 를 `div` 로 감싸면 이름과 비활성 예외는 각각 어떻게 되나?
- `fieldset` 없이 라디오 묶음에 이름을 주는 형태는?

### 9. 명세·구현·관찰 가르기 (경계)

- 이 주제에서 명세와 갈린 행이 있었나? 한 칸의 네 물음이 서로 어긋난 줄은?
- 스크린리더가 묶음 이름을 읽는다는 것을 이 판은 어디까지 보였나?

### 10. 정본 경계 긋기 (연결)

- `disabled` 와 `readonly` 가 갈리는 세 지점 · `:disabled` 의 선택자 쪽 · 칸 하나의 이름의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
