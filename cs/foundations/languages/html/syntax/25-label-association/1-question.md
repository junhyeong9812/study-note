# html/syntax/25 — `label` 연결과 폼 필드 이름: `for`/`id`·감싸기·클릭 위임 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **두 창을 함께** 봐야 선다 — 칸이 받은 `click` 기록(몇 번 · 어느 순서 · 켜졌나)과 접근성 트리의 이름. 한쪽만 답하면 반쪽이다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [22번 주제](../22-input-types-text/1-question.md) · [24번 주제](../24-input-types-choice-special/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 연결 방식마다의 세 물음 (예측)

```html
<!-- html25b-25-link.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>25 라벨 연결</title>
</head>
<body>
<p><label id="L1" for="c1">동의 1</label> <input type="checkbox" id="c1"></p>
<p><label id="L2"><span id="T2">동의 2</span> <input type="checkbox" id="c2"></label></p>
<p><label id="L3" for="c3"><span id="T3">동의 3</span> <input type="checkbox" id="c3"></label></p>
<p><label id="L4" for="없는아이디"><span id="T4">동의 4</span> <input type="checkbox" id="c4"></label></p>
<p><div id="D5">상자</div><label id="L5" for="D5"><span id="T5">동의 5</span> <input type="checkbox" id="c5"></label></p>
<p><label id="L6"><span id="T6">동의 6</span> <input type="checkbox" id="c6a"> <input type="checkbox" id="c6b"></label></p>
<p><span id="T7">동의 7</span> <input type="checkbox" id="c7"></p>
<p><span id="T8">동의 8</span> <input type="checkbox" id="c8" aria-label="동의 8"></p>
<script>
const 행 = [
  ["for/id", "#L1", "c1"], ["감싸기", "#T2", "c2"], ["감싸기 + for 같은 칸", "#T3", "c3"],
  ["감싸기 + for 가 없는 id", "#T4", "c4"], ["감싸기 + for 가 div", "#T5", "c5"],
  ["감싼 안의 첫째 input", "#T6", "c6a"], ["감싼 안의 둘째 input", "#T6", "c6b"],
  ["라벨 없음 (옆 글자)", "#T7", "c7"], ["aria-label 만", "#T8", "c8"],
];
window.__기록 = [];
for (const i of document.querySelectorAll("input")) {
  i.addEventListener("click", e => __기록.push(i.id + (e.isTrusted ? "" : "(합성)")));
}
const 뒤 = id => "(() => { const i = document.getElementById('" + id + "'); return JSON.stringify({ 클릭: __기록.filter(x => x.startsWith('" + id + "')).length, 켜짐: i.checked, 포커스: document.activeElement.id || document.activeElement.tagName }); })()";
window.__표 = "종합";
window.__시도 = 행.map(([이름, 누를곳, id]) => ({ 이름, 단계: [["click", 누를곳]], 뒤: 뒤(id) }));
window.__대상 = 행.map(([, , id]) => [id, "#" + id]);
window.__내부 = true;
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
window.__종합 = 결과 => {
  const O = [칸("연결 방식", 26) + 칸("글자 클릭 → input", 22) + 칸("접근 가능한 이름", 18) + 칸("nameFrom", 16) + 칸("labels", 7) + "label.control"];
  let 끊김 = 0, 전체 = 0;
  for (const [k, [이름, , id]] of 행.entries()) {
    const r = JSON.parse(결과[k].뒤);
    const i = document.getElementById(id);
    const 라벨 = document.querySelector("label:has(#" + id + "), label[for='" + id + "']");
    const 컨트롤 = [...document.querySelectorAll("label")].filter(l => l.control === i).map(l => l.id).join(",") || "—";
    const 이름값 = __AX[id].이름;
    const 출처 = (__INT[id] && __INT[id].속성.nameFrom) || "(없음)";
    const 칸들 = [r.클릭 > 0 && r.켜짐, 이름값 !== "", i.labels.length > 0];
    끊김 += 칸들.filter(x => !x).length; 전체 += 3;
    O.push(칸(이름, 26) + 칸("click " + r.클릭 + "번 · " + (r.켜짐 ? "켜짐" : "그대로"), 22) + 칸(JSON.stringify(이름값), 18)
      + 칸(출처, 16) + 칸(String(i.labels.length), 7) + 컨트롤);
  }
  O.push("");
  O.push("끊긴 칸 = " + 끊김 + " / " + 전체 + "  (칸 셋 — 글자 클릭이 켰나 · 이름이 있나 · labels 가 1 이상인가)");
  return O.join("\n");
};
</script>
</body>
</html>
```

- 시도마다 페이지를 새로 열고 `행` 의 「누를곳」을 **진짜 마우스로** 한 번 누른다. 칸마다 그 칸이 받은 `click` 횟수 · 체크 상태 · 포커스는?
- 칸마다 접근 가능한 이름 · `nameFrom` · `labels.length` · 그 칸을 `control` 로 가진 라벨은?
- 「끊긴 칸 N / 27」의 N 은?

### 2. 진짜 클릭 한 번이 부르는 리스너 (예측)

```html
<!-- html25b-25-click.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>25 클릭 위임</title>
</head>
<body>
<p><label id="감쌈"><span id="감쌈글자">알림 받기</span> <input type="checkbox" id="감쌈칸"></label></p>
<p><label id="가리킴" for="가리킴칸">알림 받기</label> <input type="checkbox" id="가리킴칸"></p>
<p><label id="부름"><span id="부름글자">알림 받기</span> <input type="checkbox" id="부름칸"></label></p>
<p><label id="거름"><span id="거름글자">알림 받기</span> <input type="checkbox" id="거름칸"></label></p>
<p><label id="막음"><span id="막음글자">알림 받기</span> <input type="checkbox" id="막음칸"></label></p>
<p><label id="안쪽">
  <span id="안쪽글자">알림</span>
  <input type="checkbox" id="안쪽칸">
  <a id="안쪽링크" href="#없음">약관</a>
  <a id="안쪽앵커">href 없는 a</a>
  <button type="button" id="안쪽단추">도움말</button>
</label></p>
<p><label id="앞단추"><span id="앞단추글자">알림</span> <button type="button" id="앞단추단추">도움말</button> <input type="checkbox" id="앞단추칸"></label></p>
<script>
window.__기록 = [];
const 적 = s => __기록.push(s);
const 이름 = n => n === window ? "window" : n.id || n.nodeName;
for (const 곳 of [window, ...document.querySelectorAll("label, input")]) {
  곳.addEventListener("click", e => 적("click @" + 이름(e.currentTarget) + " target=" + 이름(e.target)
    + " isTrusted=" + e.isTrusted + " detail=" + e.detail + (e.target.type === "checkbox" ? " checked=" + e.target.checked : "")), 곳 === window);
}
for (const i of document.querySelectorAll("input")) i.addEventListener("change", () => 적("change @" + i.id + " checked=" + i.checked));
// 부름 — 라벨 리스너가 스스로 input.click() 을 부른다
document.getElementById("부름").addEventListener("click", () => document.getElementById("부름칸").click());
// 거름 — 라벨 자신을 향한 click 만 넘긴다
document.getElementById("거름").addEventListener("click", e => { if (e.target !== document.getElementById("거름칸")) { e.preventDefault(); document.getElementById("거름칸").click(); } });
// 막음 — 라벨의 click 을 막는다
document.getElementById("막음").addEventListener("click", e => { if (e.target.id === "막음글자") e.preventDefault(); });
const 뒤 = ids => "__기록.join('\\n          ') + '\\n          → ' + " + JSON.stringify(ids) + ".map(id => id + '.checked=' + document.getElementById(id).checked).join(' · ')";
window.__시도 = [
  { 이름: "감싼 라벨의 글자", 단계: [["click", "#감쌈글자"]], 뒤: 뒤(["감쌈칸"]) },
  { 이름: "for 로 가리킨 라벨", 단계: [["click", "#가리킴"]], 뒤: 뒤(["가리킴칸"]) },
  { 이름: "감싼 라벨의 체크박스 자체", 단계: [["click", "#감쌈칸"]], 뒤: 뒤(["감쌈칸"]) },
  { 이름: "라벨 리스너가 input.click() 을 부름", 단계: [["click", "#부름글자"]], 뒤: 뒤(["부름칸"]) },
  { 이름: "라벨 리스너가 걸러서 부름", 단계: [["click", "#거름글자"]], 뒤: 뒤(["거름칸"]) },
  { 이름: "라벨 click 에서 preventDefault", 단계: [["click", "#막음글자"]], 뒤: 뒤(["막음칸"]) },
  { 이름: "라벨 안의 span", 단계: [["click", "#안쪽글자"]], 뒤: 뒤(["안쪽칸"]) },
  { 이름: "라벨 안의 a[href]", 단계: [["click", "#안쪽링크"]], 뒤: 뒤(["안쪽칸"]) },
  { 이름: "라벨 안의 href 없는 a", 단계: [["click", "#안쪽앵커"]], 뒤: 뒤(["안쪽칸"]) },
  { 이름: "라벨 안의 button", 단계: [["click", "#안쪽단추"]], 뒤: 뒤(["안쪽칸"]) },
  { 이름: "button 이 체크박스 앞에 있는 라벨의 글자", 단계: [["click", "#앞단추글자"]], 뒤: 뒤(["앞단추칸"]) },
];
</script>
</body>
</html>
```

- 「감싼 라벨의 글자」 · 「for 로 가리킨 라벨」 · 「감싼 라벨의 체크박스 자체」를 (각각 새 페이지에서) 한 번 누르면 기록은 어떤 줄들이 어떤 순서로 남나? 각 줄의 `target` · `isTrusted` · `detail` 은?
- 세 시도 뒤의 `checked` 는?

### 3. 라벨 리스너가 칸을 누르면 (예측)

- 2번 소스의 「라벨 리스너가 input.click() 을 부름」 · 「라벨 리스너가 걸러서 부름」 · 「라벨 click 에서 preventDefault」 세 시도의 기록과 끝의 `checked` 는?
- 첫째 시도에서 라벨의 리스너는 몇 번 불리고, 그중 `input.click()` 이 실제로 무언가를 한 것은 몇 번인가?

### 4. 라벨 안에서 누른 자리 (예측)

- 2번 소스의 `안쪽` 라벨에서 `span` · `a[href]` · `href` 없는 `a` · `button` 을 (각각) 누르면 `안쪽칸.checked` 는?
- `앞단추` 라벨의 글자를 누르면 둘째 `click` 은 어디로 가고 `앞단추칸.checked` 는?

### 5. 이름의 출처 (예측)

```html
<!-- html25b-25-name.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>25 이름의 출처</title>
</head>
<body>
<p><label>수량 <input id="n1" value="3"></label></p>
<p><label for="n2">앞</label> <input id="n2"> <label for="n2">뒤</label></p>
<p><label for="n3">라벨</label> <input id="n3" aria-label="에어리아"></p>
<p><span id="s4">가리킨 글자</span> <label for="n4">라벨</label> <input id="n4" aria-labelledby="s4"></p>
<p><input id="n5" title="제목"></p>
<p><input id="n6" placeholder="자리표시"></p>
<p><label for="n7">라벨</label> <input id="n7" title="제목"></p>
<p><label><input type="checkbox" id="n8"> 매일 <select id="s8"><option>3</option><option selected>5</option></select> 번</label></p>
<p><label for="n9" hidden>숨은 라벨</label> <input id="n9"></p>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 행 = [
  ["n1", "감싼 라벨 + 자기 value=3"], ["n2", "for 로 가리킨 라벨 둘"], ["n3", "라벨 + aria-label"],
  ["n4", "라벨 + aria-labelledby"], ["n5", "title 만"], ["n6", "placeholder 만"],
  ["n7", "라벨 + title"], ["n8", "감싼 라벨 안에 select"], ["n9", "hidden 라벨"],
];
window.__대상 = 행.map(([id]) => [id, "#" + id]);
window.__내부 = true;
window.__끝 = () => {
  const O = [칸("id", 4) + 칸("무엇을", 26) + 칸("이름", 16) + 칸("설명", 8) + 칸("nameFrom", 16) + 칸("CDP 이름 출처", 26) + "labels"];
  for (const [id, 무엇] of 행) {
    const a = __AX[id], n = __INT[id];
    O.push(칸(id, 4) + 칸(무엇, 26) + 칸(JSON.stringify(a.이름), 16) + 칸(JSON.stringify(a.설명), 8)
      + 칸((n && n.속성.nameFrom) || "(없음)", 16) + 칸(a.이름출처 || "(없음)", 26) + document.getElementById(id).labels.length);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

- 칸마다의 이름 · 설명 · `nameFrom` · `labels` 는?
- `n1` 의 이름에 자기 값 `3` 이 들어가나? `n9` 의 `labels` 와 이름은?

### 6. 연결된 컨트롤을 정하는 두 문장 (왜)

- 명세는 라벨의 연결된 컨트롤을 어떤 두 문장으로 정하고, 둘의 우선은?
- 「감싸기 + `for` 가 없는 `id`」가 칸을 품고도 끊기는 이유를 그 문장으로 설명하면?

### 7. 라벨 안의 요소와 활성화 동작 (왜)

- 명세가 라벨의 활성화 동작을 「아무것도 하지 않는다」로 정한 경우는?
- `href` 없는 `a` 가 그 경우에 안 드는 이유는?
- 라벨이 감싼 첫 요소가 단추면 무슨 일이 생기고, 명세의 어떤 콘텐츠 모델 규칙이 그것을 막으려 하나?

### 8. `isTrusted` 와 `target` (경계)

- 라벨이 보낸 `click` 과 사용자가 누른 `click` 을 `isTrusted` 로 가를 수 있나? 무엇으로 가르나?
- 명세는 두 번째 `click` 을 **요구**하나?

### 9. `aria-label` 과 라벨 (경계)

- `aria-label` 만 단 칸과 라벨을 단 칸은 세 물음 중 무엇이 같고 무엇이 다른가?
- 라벨과 `aria-label` 을 함께 달면 이름은 어느 쪽이고 `labels` 는?

### 10. 명세·구현·관찰 가르기 (경계)

- 이 주제에서 명세와 갈린 칸이 있었나?
- 「라벨을 누르면 칸에 `click` 이 간다」·「그 `click` 이 `isTrusted=true`」·「`hidden` 라벨은 이름을 안 준다」는 각각 어느 층인가?

### 11. 이 판이 못 보는 것 (경계)

- 스크린리더가 칸을 뭐라고 읽는지를 이 판이 못 보는 이유는?
- 명세가 「플랫폼마다 다를 수 있다」고 한 자리를 이 판은 몇 개의 플랫폼에서 쟀나?

### 12. 정본 경계 긋기 (연결)

- 이벤트가 경로를 도는 순서 · `preventDefault` 가 기본 동작을 막는 것의 정본은?
- 이름 출처 순서 전체 · 칸 묶음의 이름의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
