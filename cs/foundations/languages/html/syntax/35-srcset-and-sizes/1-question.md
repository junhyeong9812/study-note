# html/syntax/35 — 반응형 이미지: `srcset`/`sizes` 의 두 서술자(`w`·`x`) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 「**서버가 어느 후보 파일을 받았나**」다 — 칸마다 「**슬롯 폭은 얼마 · 후보마다 밀도는 얼마 · 그래서 받은 파일은**」으로 답하라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 칸(`__칸목록`)마다 실행기가 **새 탭**을 열고 **캐시를 끄고** CDP 로 **뷰포트 폭·DPR** 을 건다. `__뒤` 는 `load` 뒤, `뒤단계` 의 `["크기", …]` 는 그 자리에서 뷰포트를 다시 건다(하네스는 [33번 정답](../33-output-progress-meter/3-answer.md)).
> ★ 1·2·5번 페이지가 읽는 「비교 열」 파일(`html33b-35-rule.js`)은 이 파일에 싣지 않는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [34번 주제](../34-img-alt-size-and-loading/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 뷰포트 셋 × DPR 둘 (예측)

```html
<!-- html33b-35-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>35 후보 고르기</title>
<script src="html33b-35-rule.js"></script>
<style>
body { margin: 0; }
.틀 { width: 50vw; }
@media (max-width: 600px) { .틀 { width: 100vw; } }
.틀 img { width: 100%; height: auto; }
</style>
</head>
<body>
<div class="틀"><img id="g" alt="가"
  srcset="i/a400.png 400w, i/a800.png 800w, i/a1600.png 1600w"
  sizes="(max-width: 600px) 100vw, 50vw"
  src="i/a400.png"></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 후보 = [["a400.png", 400], ["a800.png", 800], ["a1600.png", 1600]];
window.__칸목록 = [];
for (const 폭 of [320, 800, 1400]) for (const dpr of [1, 2]) window.__칸목록.push({ 이름: 폭 + " · dpr " + dpr, 폭, 높이: 800, dpr });
window.__뒤 = () => {
  const i = document.getElementById("g");
  return { currentSrc: i.currentSrc.split("/").pop(), 상자폭: i.getBoundingClientRect().width, naturalWidth: i.naturalWidth, dpr: devicePixelRatio, 슬롯: i.getBoundingClientRect().width };
};
window.__종합 = 결과 => {
  const O = [칸("뷰포트 · dpr", 16) + 칸("슬롯 폭", 9) + 칸("밀도(400w · 800w · 1600w)", 28) + 칸("서버가 받은 파일", 18) + 칸("currentSrc", 12) + 칸("naturalWidth", 14) + "비교 열"];
  let 갈림 = 0;
  const 받은것 = new Set();
  for (const r of 결과) {
    const 파일 = r.로그.filter(l => l.startsWith("받음")).map(l => l.split("/").pop());
    const 슬롯 = r.뒤.슬롯, 밀도 = 후보.map(([, w]) => +(w / 슬롯).toFixed(2));
    const 비교 = 비교열(후보, 슬롯, r.dpr);
    갈림 += 파일.join(",") !== 비교;
    파일.forEach(f => 받은것.add(f));
    O.push(칸(r.이름, 16) + 칸(String(슬롯), 9) + 칸(밀도.join(" · "), 28) + 칸(파일.join(",") || "(없음)", 18) + 칸(r.뒤.currentSrc, 12) + 칸(String(r.뒤.naturalWidth), 14) + 비교);
  }
  O.push("(밀도 = 후보 폭 ÷ 슬롯 폭 · 비교 열 = 밀도가 dpr 이상인 후보 가운데 가장 작은 것 — 명세가 아니다)");
  O.push("받은 파일의 가짓수 = " + 받은것.size);
  O.push("비교 열과 갈린 칸 = " + 갈림 + " / " + 결과.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 여섯 칸 각각의 슬롯 폭 · 서버가 받은 파일 · `naturalWidth` 는? 한 칸에 받은 파일은 몇 개인가?

### 2. `sizes` 넷 (예측)

```html
<!-- html33b-35-sizes.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>35 sizes</title>
<script src="html33b-35-rule.js"></script>
<style>body { margin: 0; } img { display: block; } #n2 { width: 800px; }</style>
</head>
<body>
<img id="n1" alt="가" srcset="i/a400.png?k=n1 400w, i/a800.png?k=n1 800w, i/a1600.png?k=n1 1600w">
<img id="n2" alt="가" srcset="i/a400.png?k=n2 400w, i/a800.png?k=n2 800w, i/a1600.png?k=n2 1600w" sizes="100px">
<img id="n3" alt="가" srcset="i/a400.png?k=n3 400w, i/a800.png?k=n3 800w, i/a1600.png?k=n3 1600w" sizes="100px">
<img id="n4" alt="가" srcset="i/a400.png?k=n4 400w, i/a800.png?k=n4 800w, i/a1600.png?k=n4 1600w" sizes="533px">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 후보 = [["a400.png", 400], ["a800.png", 800], ["a1600.png", 1600]];
const 넷 = { n1: ["sizes 없음", 1000], n2: ["sizes=100px · CSS width:800px", 100], n3: ["sizes=100px · CSS 폭 없음", 100], n4: ["sizes=533px", 533] };
window.__칸목록 = [1, 2].map(dpr => ({ 이름: "1000 · dpr " + dpr, 폭: 1000, 높이: 800, dpr }));
window.__뒤 = () => Object.fromEntries(Object.keys(넷).map(k => {
  const i = document.getElementById(k), r = i.getBoundingClientRect();
  return [k, { currentSrc: i.currentSrc.split("/").pop(), 상자: r.width + "×" + r.height, naturalWidth: i.naturalWidth }];
}));
window.__종합 = 결과 => {
  const O = [];
  let 갈림 = 0, 전체 = 0;
  for (const r of 결과) {
    O.push("[" + r.이름 + "]");
    O.push("  " + 칸("img", 36) + 칸("서버가 받은 파일", 20) + 칸("상자", 12) + 칸("naturalWidth", 14) + "비교 열(슬롯 = sizes)");
    for (const [k, [글자, 슬롯]] of Object.entries(넷)) {
      const 파일 = r.로그.filter(l => l.startsWith("받음") && l.endsWith("k=" + k)).map(l => l.split("/").pop().split("?")[0]);
      const 비교 = 비교열(후보, 슬롯, r.dpr);
      전체++; 갈림 += 파일.join(",") !== 비교;
      O.push("  " + 칸(k + " " + 글자, 36) + 칸(파일.join(",") || "(없음)", 20) + 칸(r.뒤[k].상자, 12) + 칸(String(r.뒤[k].naturalWidth), 14) + 비교 + " (" + 슬롯 + ")");
    }
  }
  O.push("비교 열과 갈린 칸 = " + 갈림 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 두 칸(DPR 1 · 2)에서 네 `img` 가 받은 파일 · 상자 · `naturalWidth` 는?

### 3. `x` 서술자 · 섞기 · 한 후보에 둘 (예측)

```html
<!-- html33b-35-x.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>35 x 서술자</title>
<style>body { margin: 0; } img { display: block; }</style>
</head>
<body>
<img id="x1" alt="가" srcset="i/d200.png?k=x1 1x, i/d400.png?k=x1 2x">
<img id="x2" alt="가" srcset="i/a400.png?k=x2 400w, i/a800.png?k=x2 2x" sizes="200px">
<img id="x3" alt="가" srcset="i/a400.png?k=x3 1x, i/a800.png?k=x3 800w" sizes="200px">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 셋 = { x1: "1x · 2x", x2: "400w · 2x (sizes=200px)", x3: "1x · 800w (sizes=200px)" };
window.__칸목록 = [1, 2, 3].map(dpr => ({ 이름: "1000 · dpr " + dpr, 폭: 1000, 높이: 800, dpr }));
window.__뒤 = () => Object.fromEntries(Object.keys(셋).map(k => {
  const i = document.getElementById(k), r = i.getBoundingClientRect();
  return [k, { currentSrc: i.currentSrc.split("/").pop(), 상자: r.width + "×" + r.height }];
}));
window.__종합 = 결과 => {
  const O = [(칸("img", 34) + 결과.map(r => 칸("dpr " + r.dpr + " 받은 파일 · 상자", 30)).join("")).trimEnd()];
  for (const [k, 글자] of Object.entries(셋)) {
    O.push(칸(k + " " + 글자, 34) + 결과.map(r => {
      const 파일 = r.로그.filter(l => l.startsWith("받음") && l.endsWith("k=" + k)).map(l => l.split("/").pop().split("?")[0]);
      return 칸((파일.join(",") || "(없음)") + " · " + r.뒤[k].상자, 30);
    }).join("").trimEnd());
  }
  const 콘솔 = new Set(결과.flatMap(r => r.콘솔));
  O.push("콘솔 기록(세 칸 합쳐 서로 다른 것) —"); if (!콘솔.size) O.push("  0 건"); for (const t of 콘솔) O.push("  " + t);
  return O.join("\n");
};
</script>
</body>
</html>
```

```html
<!-- html33b-35-drop.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>35 한 후보에 서술자 둘</title>
<style>body { margin: 0; } img { display: block; }</style>
</head>
<body>
<img id="x4" alt="가" srcset="i/a800.png?k=x4 800w 2x, i/a400.png?k=x4 1x" src="i/d200.png?k=x4">
<script>
window.__칸목록 = [{ 이름: "1000 · dpr 2", 폭: 1000, 높이: 800, dpr: 2 }];
window.__뒤 = () => document.getElementById("x4").currentSrc.split("/").pop();
window.__종합 = 결과 => {
  const r = 결과[0];
  return [...r.로그.map(l => "  서버    " + l), "currentSrc = " + r.뒤, "콘솔 기록 —", ...(r.콘솔.length ? r.콘솔.map(t => "  " + t) : ["  0 건"])].join("\n");
};
</script>
</body>
</html>
```

- 첫 페이지의 세 `img` 가 DPR 1·2·3 에서 받은 파일과 상자는? 콘솔에 무엇이 남나?
- 둘째 페이지의 `currentSrc` 와 콘솔 기록은?

### 4. 창을 바꾼 뒤 (예측)

```html
<!-- html33b-35-resize.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>35 창 크기를 바꾼 뒤</title>
<style>body { margin: 0; } img { display: block; width: 100%; height: auto; }</style>
</head>
<body>
<img id="r" alt="가" srcset="i/a400.png 400w, i/a800.png 800w, i/a1600.png 1600w" sizes="100vw">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const 표지 = s => fetch("/m?" + encodeURIComponent(s));
// 크기를 바꾼 뒤 — resize 를 받고 두 틀을 넘긴 다음, 그사이 currentSrc 가 바뀌었으면 새 그림의 load 까지 기다린다
const 기다림 = "(async () => { await 두틀(); await 두틀(); const i = document.getElementById('r'); if (!i.complete) await new Promise(r => i.addEventListener('load', r, { once: true })); await 표지('바꾼 뒤 · ' + innerWidth + ' · dpr ' + devicePixelRatio + ' · currentSrc ' + i.currentSrc.split('/').pop()); return 1; })()";
const 시작 = "(async () => { const i = document.getElementById('r'); await 표지('처음 · ' + innerWidth + ' · dpr ' + devicePixelRatio + ' · currentSrc ' + i.currentSrc.split('/').pop()); return 1; })()";
window.__칸목록 = [
  { 이름: "1400·dpr 2 → 320·dpr 1", 폭: 1400, 높이: 800, dpr: 2, 뒤단계: [["js", 시작], ["크기", 320, 800, 1], ["js", 기다림]] },
  { 이름: "320·dpr 1 → 1400·dpr 2", 폭: 320, 높이: 800, dpr: 1, 뒤단계: [["js", 시작], ["크기", 1400, 800, 2], ["js", 기다림]] },
];
window.__뒤 = () => document.getElementById("r").currentSrc.split("/").pop();
window.__종합 = 결과 => {
  const O = [];
  for (const r of 결과) {
    O.push("[" + r.이름 + "]");
    for (const l of r.로그) O.push("  서버    " + l);
    O.push("  받은 이미지 수 = " + r.로그.filter(l => l.startsWith("받음")).length);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

- 두 칸 각각에서 서버 로그에 무엇이 어떤 순서로 찍히나? 받은 이미지는 몇 개인가?

### 5. `sizes="auto"` 넷 (예측)

```html
<!-- html33b-35-auto.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>35 sizes=auto</title>
<script src="html33b-35-rule.js"></script>
<style>body { margin: 0; } img { display: block; } .좁게 { width: 200px; }</style>
</head>
<body>
<img id="u1" class="좁게" alt="가" loading="lazy" sizes="auto" srcset="i/a400.png?k=u1 400w, i/a800.png?k=u1 800w, i/a1600.png?k=u1 1600w">
<img id="u2" class="좁게" alt="가" sizes="auto" srcset="i/a400.png?k=u2 400w, i/a800.png?k=u2 800w, i/a1600.png?k=u2 1600w">
<img id="u3" class="좁게" alt="가" loading="lazy" sizes="auto, 100vw" srcset="i/a400.png?k=u3 400w, i/a800.png?k=u3 800w, i/a1600.png?k=u3 1600w">
<img id="u4" alt="가" loading="lazy" sizes="auto" srcset="i/a400.png?k=u4 400w, i/a800.png?k=u4 800w, i/a1600.png?k=u4 1600w">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 넷 = { u1: "lazy · sizes=auto · CSS 200px", u2: "(eager) · sizes=auto · CSS 200px", u3: "lazy · sizes=\"auto, 100vw\" · CSS 200px", u4: "lazy · sizes=auto · CSS 폭 없음" };
window.__칸목록 = [{ 이름: "1400 · dpr 1", 폭: 1400, 높이: 800, dpr: 1 }];
window.__뒤 = async () => {
  for (const k of Object.keys(넷)) { const i = document.getElementById(k); if (!i.complete) await new Promise(r => i.addEventListener("load", r, { once: true })); }
  return Object.fromEntries(Object.keys(넷).map(k => {
    const i = document.getElementById(k), r = i.getBoundingClientRect(), s = getComputedStyle(i);
    return [k, { 상자: r.width + "×" + r.height, contain: s.contain, cis: s.containIntrinsicSize }];
  }));
};
window.__종합 = 결과 => {
  const r = 결과[0];
  const O = [칸("img", 44) + 칸("받은 파일", 12) + 칸("상자", 10) + "contain · contain-intrinsic-size"];
  for (const [k, 글자] of Object.entries(넷)) {
    const 파일 = r.로그.filter(l => l.startsWith("받음") && l.endsWith("k=" + k)).map(l => l.split("/").pop().split("?")[0]);
    O.push(칸(k + " " + 글자, 44) + 칸(파일.join(",") || "(없음)", 12) + 칸(r.뒤[k].상자, 10) + r.뒤[k].contain + " · " + r.뒤[k].cis);
  }
  O.push("(비교 — 슬롯 200 이면 " + 비교열([["a400.png", 400], ["a800.png", 800], ["a1600.png", 1600]], 200, 1) + " · 슬롯 300 이면 " + 비교열([["a400.png", 400], ["a800.png", 800], ["a1600.png", 1600]], 300, 1) + " · 슬롯 1400(100vw) 이면 " + 비교열([["a400.png", 400], ["a800.png", 800], ["a1600.png", 1600]], 1400, 1) + ")");
  return O.join("\n");
};
</script>
</body>
</html>
```

- 네 `img` 가 받은 파일 · 상자 · `contain` · `contain-intrinsic-size` 는?

### 6. `sizes` 가 브라우저에 알려 주는 것 (왜)

- 브라우저가 CSS 의 실제 폭 대신 `sizes` 를 쓰는 까닭은? [34번](../34-img-alt-size-and-loading/1-question.md)의 요청 시점과 어떻게 이어지나?

### 7. `w` 와 `x` 를 나눠 쓰는 때 (경계)

- 어떤 그림에 `x` 를, 어떤 그림에 `w` + `sizes` 를 쓰나? 둘을 **후보끼리** 섞을 때와 **한 후보에 같이** 쓸 때 이 판에서 각각 무엇이 일어났나?

### 8. `naturalWidth` 가 알려 주는 것 (경계)

- `w` 후보를 고른 `img` 의 `naturalWidth` 는 무엇을 나타내나 — 받은 파일의 폭과 어떤 관계인가? 속성 없이 그리면 그 값이 어디에 쓰이나?

### 9. 한번 받은 뒤 (경계)

- 이 판의 Chrome 이 창을 바꾼 뒤 한 일을 두 방향으로 대면? 그것을 「명세가 그렇게 정한다」로 적을 수 있나 — 이 배치가 가진 근거로?

### 10. 명세·구현·관찰 가르기 (연결)

- 「`sizes` 기본값」·「`sizes=auto` 가 붙은 상자의 크기 규칙」·「창을 줄인 뒤의 동작」·「섞은 목록의 처리」·「같은 밀도 후보 중 무엇이 남나」는 각각 명세·구현·관찰 중 어느 층이고, 이 배치가 판정할 수 있는 것은?

### 11. 정본 경계 긋기 (연결)

- 자리 예약과 지연 로딩 · 좁은 화면에 다른 자르기 · 포맷 대체 · `video` 의 `source` 고르기의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
