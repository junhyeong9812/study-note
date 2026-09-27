# html/syntax/34 — `img`: `alt`·`width`/`height`·`loading`/`decoding`/`fetchpriority` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 **「로드 전 상자 · 요청 시점 · 트리의 역할」** 세 가지다 — 칸마다 「**이미지가 오기 전 상자는 몇 × 몇인가 · 요청이 무엇보다 먼저 갔나 · 트리에 무엇으로 남나**」로 답하라. **몇 ms 인가는 묻지 않는다.**
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ `h/…` 경로의 그림은 **서버가 붙잡아 두었다가** 실행기가 `/go` 를 부를 때 풀어 준다 — 페이지의 `__전` 은 **풀기 전**, `__뒤` 는 **`load` 뒤**에 돈다. `/m?…` 은 서버 로그에 순서를 박는 **표지**다(하네스는 [33번 정답](../33-output-progress-meter/3-answer.md)).
> ★ 3번 페이지가 읽는 「명세 열」 파일(`html33b-34-alt-spec.js`)은 **답이 들어 있어서** 이 파일에 싣지 않는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [05번 주제](../05-content-categories-and-models/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 150px 칸 여섯 · 로드 전과 뒤 (예측)

```html
<!-- html33b-34-shift.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>34 로드 전후</title>
<style>
body { margin: 0; display: flex; gap: 10px; align-items: flex-start; }
.칸 { width: 150px; }
.칸 p { margin: 0; }
#D img { width: 100%; }
#E img, #F img { width: 100%; height: auto; }
</style>
</head>
<body>
<div class="칸" id="A"><img src="h/p300x150.png?k=A" width="300" height="150" alt="가"><p>아래</p></div>
<div class="칸" id="B"><img src="h/p300x150.png?k=B" width="300" alt="가"><p>아래</p></div>
<div class="칸" id="C"><img src="h/p300x150.png?k=C" alt="가"><p>아래</p></div>
<div class="칸" id="D"><img src="h/p300x150.png?k=D" width="300" height="150" alt="가"><p>아래</p></div>
<div class="칸" id="E"><img src="h/p300x150.png?k=E" width="300" height="150" alt="가"><p>아래</p></div>
<div class="칸" id="F"><img src="h/p300x150.png?k=F" alt="가"><p>아래</p></div>
<script>
// 표지 사이에 붙어 온 요청들은 서버에 닿는 순서가 흔들린다 — 그 묶음 안만 이름순으로 찍는다
const 묶음정렬 = 로그 => { const O = [], 묶음 = []; for (const l of [...로그, ""]) { if (l.startsWith("받음")) { 묶음.push(l); continue; } O.push(...묶음.sort()); 묶음.length = 0; if (l) O.push(l); } return O; };
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const 재기 = () => Object.fromEntries(["A", "B", "C", "D", "E", "F"].map(k => {
  const i = document.querySelector("#" + k + " img"), p = document.querySelector("#" + k + " p");
  const r = i.getBoundingClientRect();
  return [k, { 상자: r.width + "×" + r.height, 아래top: p.getBoundingClientRect().top, 비율: getComputedStyle(i).aspectRatio, complete: i.complete }];
}));
window.__칸목록 = [{ 이름: "1000×800 · dpr 1", 폭: 1000, 높이: 800, dpr: 1 }];
window.__전 = async () => { await 두틀(); return 재기(); };
window.__뒤 = async () => { await 두틀(); return 재기(); };
window.__종합 = 결과 => {
  const r = 결과[0], 속성 = { A: "width + height", B: "width 만", C: "없음", D: "width + height · CSS width:100%", E: "width + height · CSS width:100%; height:auto", F: "없음 · CSS width:100%; height:auto" };
  const O = 묶음정렬(r.로그).map(l => "  서버    " + l);
  O.push(칸("img", 48) + 칸("aspect-ratio 계산값", 22) + 칸("로드 전 상자", 16) + 칸("로드 뒤 상자", 16) + "아래 요소가 움직였나");
  let 움직임 = 0;
  for (const k of ["A", "B", "C", "D", "E", "F"]) {
    const a = r.전[k], b = r.뒤[k], 움직였나 = a.아래top !== b.아래top;
    움직임 += 움직였나;
    O.push(칸(k + " " + 속성[k], 48) + 칸(JSON.stringify(a.비율), 22) + 칸(a.상자, 16) + 칸(b.상자, 16)
      + (움직였나 ? "예" : "아니오") + " (" + a.아래top + " → " + b.아래top + ")");
  }
  O.push("로드 전 complete = " + ["A", "B", "C", "D", "E", "F"].map(k => r.전[k].complete).join(" · ") + " · 로드 뒤 = " + ["A", "B", "C", "D", "E", "F"].map(k => r.뒤[k].complete).join(" · "));
  O.push("움직인 칸 = " + 움직임 + " / 6");
  return O.join("\n");
};
</script>
</body>
</html>
```

- 여섯 `img` 각각의 `aspect-ratio` 계산값 · 로드 전 상자 · 로드 뒤 상자는? 아래 문단이 움직인 칸은 어느 것인가?

### 2. 위와 아래 · `eager` 와 `lazy` (예측)

```html
<!-- html33b-34-lazy.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>34 loading</title>
<style>
body { margin: 0; }
img { display: block; }
#멀리 { margin-top: 10000px; }
</style>
<script>
const 표지 = s => fetch("/m?" + s);
document.addEventListener("DOMContentLoaded", () => 표지("DOMContentLoaded"));
addEventListener("load", () => 표지("load"));
</script>
</head>
<body>
<img id="위e" src="h/p300x150.png?k=위-eager" width="300" height="150" alt="가">
<img id="위l" src="h/p300x150.png?k=위-lazy" width="300" height="150" alt="가" loading="lazy">
<div id="멀리">
<img id="아래e" src="h/p300x150.png?k=아래-eager" width="300" height="150" alt="가">
<img id="아래l" src="h/p300x150.png?k=아래-lazy" width="300" height="150" alt="가" loading="lazy">
</div>
<script>
// 표지 사이에 붙어 온 요청들은 서버에 닿는 순서가 흔들린다 — 그 묶음 안만 이름순으로 찍는다
const 묶음정렬 = 로그 => { const O = [], 묶음 = []; for (const l of [...로그, ""]) { if (l.startsWith("받음")) { 묶음.push(l); continue; } O.push(...묶음.sort()); 묶음.length = 0; if (l) O.push(l); } return O; };
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const 넷 = ["위e", "위l", "아래e", "아래l"];
const 상태 = () => Object.fromEntries(넷.map(k => [k, document.getElementById(k).complete]));
window.__칸목록 = [{ 이름: "1000×800 · dpr 1", 폭: 1000, 높이: 800, dpr: 1, 뒤단계: [
  ["js", "(async () => { await 표지('스크롤 전'); window.__스크롤전 = 상태(); const i = document.getElementById('아래l'); const 옴 = new Promise(r => i.addEventListener('load', r, { once: true })); i.scrollIntoView(); await 옴; await 표지('스크롤 뒤 아래-lazy load'); return 1; })()"],
] }];
window.__전 = async () => { await 두틀(); await 두틀(); await 표지("두 틀 뒤"); return 상태(); };
window.__뒤 = () => ({ 스크롤전: window.__스크롤전, 스크롤뒤: 상태() });
window.__종합 = 결과 => {
  const r = 결과[0];
  const O = 묶음정렬(r.로그).map(l => "  서버    " + l);
  const 순번 = k => r.로그.findIndex(l => l.includes("k=" + k));
  const 로드 = r.로그.indexOf("표지  load"), 문서 = r.로그.indexOf("표지  DOMContentLoaded");
  O.push("");
  const 스크롤 = r.로그.indexOf("표지  스크롤 전");
  O.push(칸("img", 16) + 칸("DOMContentLoaded 전", 22) + 칸("load 전", 10) + 칸("스크롤 전", 12) + "처음 우선순위 → 바뀐 우선순위");
  for (const k of ["위-eager", "위-lazy", "아래-eager", "아래-lazy"]) {
    const i = 순번(k), q = r.요청.find(x => x.경로.includes("k=" + k));
    O.push(칸(k, 16) + 칸(i >= 0 && i < 문서 ? "예" : "아니오", 22) + 칸(i >= 0 && i < 로드 ? "예" : "아니오", 10) + 칸(i >= 0 && i < 스크롤 ? "예" : "아니오", 12)
      + (q ? [q.처음우선순위, ...q.바뀐우선순위].join(" → ") : "—"));
  }
  O.push("스크롤 전 complete = " + JSON.stringify(r.뒤.스크롤전));
  O.push("load 전에 요청이 간 칸 = " + ["위-eager", "위-lazy", "아래-eager", "아래-lazy"].filter(k => 순번(k) >= 0 && 순번(k) < 로드).length + " / 4");
  return O.join("\n");
};
</script>
</body>
</html>
```

- 서버 로그에 네 요청과 표지들이 어떤 순서로 찍히나? 각 그림의 요청이 `DOMContentLoaded` · `load` · 스크롤보다 먼저였나?
- 각 요청의 처음 우선순위와 바뀐 우선순위는?

### 3. `alt` 셋 × 파일 있음/없음 (예측)

```html
<!-- html33b-34-alt.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>34 alt</title>
<script src="html33b-34-alt-spec.js"></script>
</head>
<body>
<div><img id="a1" src="i/p300x150.png"></div>
<div><img id="a2" src="i/p300x150.png" alt=""></div>
<div><img id="a3" src="i/p300x150.png" alt="파란 사각형"></div>
<div><img id="b1" src="i/nope-x.png"></div>
<div><img id="b2" src="i/nope-y.png" alt=""></div>
<div><img id="b3" src="i/nope-z.png" alt="파란 사각형"></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 여섯 = ["a1", "a2", "a3", "b1", "b2", "b3"];
window.__대상 = 여섯.map(k => [k, "#" + k]);
window.__끝 = () => {
  const O = [칸("img", 36) + 칸("상자", 12) + 칸("그려진 것", 10) + 칸("역할", 8) + 칸("이름", 16) + 칸("무시", 7) + "naturalWidth"];
  let 갈림 = 0, 전체 = 0;
  for (const k of 여섯) {
    const e = document.getElementById(k), r = e.getBoundingClientRect(), a = __AX[k];
    const 글자 = (k[0] === "a" ? "파일 있음" : "파일 없음(404)") + " · " + (e.hasAttribute("alt") ? "alt=" + JSON.stringify(e.alt) : "alt 없음");
    const 그림 = e.naturalWidth > 0 ? "그림" : r.width === 0 && r.height === 0 ? "0×0" : e.alt ? "글자" : "아이콘";
    const 이 = { 역할: a.역할, 이름: a.이름, 그림 };
    for (const c of ["역할", "이름", "그림"]) { 전체++; if (!명세[k][c].includes(이[c])) { 갈림++; O.push("  ↳ 명세 열과 갈림 — " + k + " " + c); } }
    O.push(칸(k + " " + 글자, 36) + 칸(r.width + "×" + r.height, 12) + 칸(그림, 10) + 칸(a.역할, 8) + 칸(JSON.stringify(a.이름), 16) + 칸(String(a.무시), 7) + e.naturalWidth);
  }
  O.push("(그려진 것 = naturalWidth 가 있으면 그림 · 0×0 · alt 글자가 있으면 글자 · 나머지는 아이콘)");
  O.push("명세 열과 갈린 칸 = " + 갈림 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 여섯 `img` 의 상자 크기 · 역할 · 이름 · 트리에서 무시되나는? 「명세 열과 갈린 칸 N / 18」의 N 은?

### 4. `fetchpriority` 셋 · `decoding` 둘 (예측)

```html
<!-- html33b-34-prio.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>34 fetchpriority 와 decoding</title>
<style>body { margin: 0; } img { display: block; } #멀리 { margin-top: 10000px; }</style>
</head>
<body>
<img src="h/p300x150.png?k=r1" width="300" height="150" alt="가">
<img src="h/p300x150.png?k=r2" width="300" height="150" alt="가" fetchpriority="high">
<img src="h/p300x150.png?k=r3" width="300" height="150" alt="가" fetchpriority="low">
<img src="h/p300x150.png?k=r4" width="300" height="150" alt="가" decoding="async">
<img src="h/p300x150.png?k=r5" width="300" height="150" alt="가" decoding="sync">
<div id="멀리"><img src="h/p300x150.png?k=r6" width="300" height="150" alt="가" fetchpriority="high"></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const 속성 = { r1: "(속성 없음)", r2: "fetchpriority=high", r3: "fetchpriority=low", r4: "decoding=async", r5: "decoding=sync", r6: "fetchpriority=high · 한참 아래" };
window.__칸목록 = [{ 이름: "1000×800 · dpr 1", 폭: 1000, 높이: 800, dpr: 1 }];
window.__전 = async () => { await 두틀(); await 두틀(); return 1; };
window.__종합 = 결과 => {
  const r = 결과[0];
  if (location.search === "?log") return r.로그.join("\n");      // html33b-tally.py 가 쓰는 판 — 서버 로그만
  const 앞 = r.로그.slice(0, r.로그.indexOf("풀어 줌")).filter(l => l.startsWith("받음")).length;
  const O = [칸("img", 36) + "처음 우선순위 → 바뀐 우선순위"];
  for (const k of Object.keys(속성)) {
    const q = r.요청.find(x => x.경로.endsWith("k=" + k));
    O.push(칸(k + " " + 속성[k], 36) + [q.처음우선순위, ...q.바뀐우선순위].join(" → "));
  }
  O.push("풀어 주기 전에 서버가 받은 이미지 = " + 앞 + " / " + Object.keys(속성).length + "  (★ 받은 순서는 판마다 흔들린다 — 따로 센다)");
  return O.join("\n");
};
</script>
</body>
</html>
```

- 여섯 요청의 처음 우선순위와 바뀐 우선순위는? `decoding` 둘은 속성 없는 것과 무엇이 다른가?
- 서버에 닿는 순서를 20 판 돌리면 몇 가지가 나올 것 같은가 — 한 가지라면 그 순서는?

### 5. `width`/`height` 가 비율이 되는 조건 (왜)

- 명세의 렌더링 절이 두 속성을 `aspect-ratio` 로 번역하는 조건 셋은? 번역된 값의 앞에 붙는 `auto` 는 무슨 뜻인가?

### 6. 속성 둘 + CSS `width:100%` 의 높이 (경계)

- 이 조합에서 높이를 정하는 선언은 어느 것인가 — 속성이 만드는 표현 힌트 둘과 작성자 CSS 한 줄로 설명하면? 비율이 높이를 정하게 하려면 무엇이 필요한가?

### 7. `loading=lazy` 를 쓸 자리 (경계)

- 이 판의 요청 로그로 보면 `lazy` 를 달지 말아야 할 그림은 어느 것인가? 이 판이 그 근거로 잰 것 둘과, 이 판이 **말할 수 없는** 것은?

### 8. `alt` 없음과 `alt=""` (경계)

- 트리의 역할·이름과 깨졌을 때의 자리가 어떻게 갈리나? 「`alt` 가 없으면 파일 이름이 읽힌다」는 말을 이 판은 어디까지 확인할 수 있나?

### 9. `complete` 로 로드 성공 가르기 (경계)

- 깨진 그림의 `complete` 는? 성공과 깨짐을 가르는 칸은?

### 10. `DOMContentLoaded`·`load` 와 지연 로딩 (연결)

- [08번](../08-script-loading/1-question.md)의 두 이벤트 위에 네 요청을 놓으면? 그 배치에서 `load` 가 기다린 그림과 안 기다린 그림은 무엇으로 갈리나?

### 11. 명세·구현·관찰 가르기 (연결)

- 「속성 둘이 `aspect-ratio` 로 번역되는 조건」·「첫 화면 `lazy` 의 우선순위 이름」·「`alt=""` 의 역할」·「깨진 그림의 상자 크기」·「서버에 닿는 순서」는 각각 명세·구현·관찰 중 어느 층이 정하나?

### 12. 정본 경계 긋기 (연결)

- `aspect-ratio` 의 `auto <ratio>` 뜻 · `object-fit` 으로 자르기 · `srcset`/`sizes` · 스크립트로 직접 지연 로딩하기의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
