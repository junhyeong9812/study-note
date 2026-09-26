# html/syntax/36 — `picture`: 아트 디렉션과 포맷 대체 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 답은 「**어느 `source` 의 파일을 받았나 · 몇 번 요청했나**」다 — `picture` 마다 「**위에서부터 어느 `source` 가 맞고 · 서버는 무엇을 받고 · 무엇은 요청조차 안 했나**」로 답하라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 칸마다 실행기가 **새 탭 · 캐시 끔 · CDP 로 뷰포트·DPR** 을 건다. `h/…` 그림은 **`/go` 까지 붙잡혀** 있다(하네스는 [33번 정답](../33-output-progress-meter/3-answer.md)).
> ★ `f200.webp` 는 Chrome 의 `canvas` 로 만든 진짜 WebP 다. `image/x-nope` 는 **없는 MIME** 이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [35번 주제](../35-srcset-and-sizes/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `picture` 와 `srcset` 만 · 여섯 칸 (예측)

```html
<!-- html33b-36-art.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>36 아트 디렉션</title>
<style>body { margin: 0; } img { display: block; max-width: 100%; height: auto; }</style>
</head>
<body>
<picture id="p">
  <source media="(max-width: 600px)" srcset="i/c400x400.png?k=p">
  <img id="pi" src="i/c800x400.png?k=p" alt="가">
</picture>
<img id="s" alt="가" srcset="i/c400x400.png?k=s 400w, i/c800x400.png?k=s 800w" sizes="100vw">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
window.__칸목록 = [];
for (const 폭 of [320, 800, 1400]) for (const dpr of [1, 2]) window.__칸목록.push({ 이름: 폭 + " · dpr " + dpr, 폭, 높이: 800, dpr });
window.__뒤 = () => ({ p: document.getElementById("pi").currentSrc.split("/").pop(), s: document.getElementById("s").currentSrc.split("/").pop() });
window.__종합 = 결과 => {
  const O = [칸("뷰포트 · dpr", 16) + 칸("picture(media) 가 받은 파일", 30) + "img srcset 만 가 받은 파일"];
  const 받은 = (r, k) => r.로그.filter(l => l.startsWith("받음") && l.endsWith("k=" + k)).map(l => l.split("/").pop().split("?")[0]).join(",") || "(없음)";
  let 네모p = 0, 네모s = 0;
  for (const r of 결과) {
    const a = 받은(r, "p"), b = 받은(r, "s");
    네모p += a === "c400x400.png"; 네모s += b === "c400x400.png";
    O.push(칸(r.이름, 16) + 칸(a, 30) + b);
  }
  O.push("정사각형(c400x400)을 받은 칸 — picture " + 네모p + " / " + 결과.length + " · srcset 만 " + 네모s + " / " + 결과.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 여섯 칸에서 두 그림이 각각 받은 파일은? 정사각(`c400x400`)을 받은 칸은 두 방식에서 각각 몇 칸인가?

### 2. 1400 에서 320 으로 줄이기 (예측)

```html
<!-- html33b-36-resize.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>36 창을 줄인 뒤</title>
<style>body { margin: 0; } img { display: block; max-width: 100%; height: auto; }</style>
</head>
<body>
<picture>
  <source media="(max-width: 600px)" srcset="i/c400x400.png?k=p">
  <img id="pi" src="i/c800x400.png?k=p" alt="가">
</picture>
<img id="s" alt="가" srcset="i/c400x400.png?k=s 400w, i/c800x400.png?k=s 800w" sizes="100vw">
<script>
// 표지 사이에 붙어 온 요청들은 서버에 닿는 순서가 흔들린다 — 그 묶음 안만 이름순으로 찍는다
const 묶음정렬 = 로그 => { const O = [], 묶음 = []; for (const l of [...로그, ""]) { if (l.startsWith("받음")) { 묶음.push(l); continue; } O.push(...묶음.sort()); 묶음.length = 0; if (l) O.push(l); } return O; };
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const 표지 = s => fetch("/m?" + encodeURIComponent(s));
const 이름 = id => document.getElementById(id).currentSrc.split("/").pop();
const 기다림 = "(async () => { await 두틀(); await 두틀(); for (const id of ['pi', 's']) { const i = document.getElementById(id); if (!i.complete) await new Promise(r => i.addEventListener('load', r, { once: true })); } await 표지('줄인 뒤 · ' + innerWidth + ' · picture ' + 이름('pi') + ' · srcset 만 ' + 이름('s')); return 1; })()";
window.__칸목록 = [{ 이름: "1400·dpr 1 → 320·dpr 1", 폭: 1400, 높이: 800, dpr: 1, 뒤단계: [
  ["js", "표지('처음 · ' + innerWidth + ' · picture ' + 이름('pi') + ' · srcset 만 ' + 이름('s')).then(() => 1)"], ["크기", 320, 800, 1], ["js", 기다림]] }];
window.__종합 = 결과 => 묶음정렬(결과[0].로그).map(l => "  서버    " + l).join("\n");
</script>
</body>
</html>
```

- 서버 로그에 무엇이 어떤 순서로 찍히나? 줄인 뒤 두 그림의 `currentSrc` 는?

### 3. `picture` 다섯 (예측)

```html
<!-- html33b-36-type.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>36 포맷 대체</title>
<style>body { margin: 0; } img { display: block; }</style>
</head>
<body>
<picture>
  <source type="image/x-nope" srcset="i/g200.png?k=t1">
  <source type="image/webp" srcset="i/f200.webp?k=t1">
  <img id="t1" src="i/f200.png?k=t1" alt="가">
</picture>
<picture>
  <source type="image/png" srcset="i/g200.png?k=t2">
  <source type="image/webp" srcset="i/f200.webp?k=t2">
  <img id="t2" src="i/f200.png?k=t2" alt="가">
</picture>
<picture>
  <source type="image/webp" srcset="i/nope.webp?k=t3">
  <img id="t3" src="i/f200.png?k=t3" alt="가">
</picture>
<picture>
  <source type="image/x-nope" srcset="i/g200.png?k=t4">
  <img id="t4" src="i/f200.png?k=t4" alt="가">
</picture>
<picture id="빈">
  <source type="image/webp" srcset="i/f200.webp?k=t5">
</picture>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 줄 = { t1: "x-nope, webp, img(png)", t2: "png, webp, img(png)", t3: "webp(파일 없음), img(png)", t4: "x-nope, img(png)", t5: "img 없는 picture · webp" };
window.__칸목록 = [{ 이름: "1000 · dpr 1", 폭: 1000, 높이: 800, dpr: 1 }];
window.__뒤 = () => Object.fromEntries(["t1", "t2", "t3", "t4"].map(k => {
  const i = document.getElementById(k), r = i.getBoundingClientRect();
  return [k, { currentSrc: i.currentSrc.split("/").pop(), 상자: r.width + "×" + r.height, naturalWidth: i.naturalWidth }];
}).concat([["t5", { currentSrc: "(img 없음)", 상자: (r => r.width + "×" + r.height)(document.getElementById("빈").getBoundingClientRect()), naturalWidth: "—" }]]));
window.__종합 = 결과 => {
  const r = 결과[0];
  const O = [칸("picture", 32) + 칸("서버가 받은 파일", 34) + 칸("currentSrc", 18) + 칸("상자", 10) + "naturalWidth"];
  let 모름 = 0;
  for (const [k, 글자] of Object.entries(줄)) {
    const 받은 = r.로그.filter(l => l.startsWith("받음") && l.endsWith("k=" + k)).map(l => l.split("/").pop().split("?")[0]);
    O.push(칸(k + " " + 글자, 32) + 칸(받은.join(",") || "(없음)", 34) + 칸(r.뒤[k].currentSrc.split("?")[0], 18) + 칸(r.뒤[k].상자, 10) + r.뒤[k].naturalWidth);
  }
  O.push("type=\"image/x-nope\" 인 source 의 파일(g200.png)을 받은 요청 = " + r.로그.filter(l => l.startsWith("받음") && l.includes("g200.png") && (l.endsWith("k=t1") || l.endsWith("k=t4"))).length);
  O.push("서버가 받은 이미지 요청 = " + r.로그.filter(l => l.startsWith("받음")).length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 다섯 `picture` 각각에서 서버가 받은 파일 · `currentSrc` · 상자는? 서버가 받은 이미지 요청은 모두 몇 개인가?

### 4. `source` 에 단 `width`/`height` (예측)

```html
<!-- html33b-36-dims.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>36 source 의 width 와 height</title>
<style>body { margin: 0; } .틀 { width: 300px; } img { display: block; width: 100%; height: auto; }</style>
</head>
<body>
<div class="틀"><picture>
  <source media="(max-width: 600px)" srcset="h/c400x400.png?k=q1" width="400" height="400">
  <img id="q1" src="h/c800x400.png?k=q1" width="800" height="400" alt="가">
</picture><p id="q1아래">아래</p></div>
<div class="틀"><picture>
  <source media="(max-width: 600px)" srcset="h/c400x400.png?k=q2">
  <img id="q2" src="h/c800x400.png?k=q2" width="800" height="400" alt="가">
</picture><p id="q2아래">아래</p></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const 재기 = () => Object.fromEntries(["q1", "q2"].map(k => {
  const i = document.getElementById(k), r = i.getBoundingClientRect();
  return [k, { 상자: r.width + "×" + r.height, 비율: getComputedStyle(i).aspectRatio, 아래: document.getElementById(k + "아래").getBoundingClientRect().top, 파일: i.currentSrc.split("/").pop().split("?")[0] }];
}));
window.__칸목록 = [320, 1000].map(폭 => ({ 이름: 폭 + " · dpr 1", 폭, 높이: 800, dpr: 1 }));
window.__전 = async () => { await 두틀(); return 재기(); };
window.__뒤 = async () => { await 두틀(); return 재기(); };
window.__종합 = 결과 => {
  const 글자 = { q1: "source 에 width/height 있음", q2: "source 에 width/height 없음" };
  const O = [];
  let 움직임 = 0, 전체 = 0;
  for (const r of 결과) {
    O.push("[" + r.이름 + "]");
    O.push("  " + 칸("picture", 32) + 칸("고른 파일", 14) + 칸("로드 전 aspect-ratio", 22) + 칸("로드 전 상자", 14) + 칸("로드 뒤 상자", 14) + "아래 요소가 움직였나");
    for (const k of ["q1", "q2"]) {
      const a = r.전[k], b = r.뒤[k], m = a.아래 !== b.아래;
      전체++; 움직임 += m;
      O.push("  " + 칸(k + " " + 글자[k], 32) + 칸(b.파일, 14) + 칸(JSON.stringify(a.비율), 22) + 칸(a.상자, 14) + 칸(b.상자, 14) + (m ? "예" : "아니오") + " (" + a.아래 + " → " + b.아래 + ")");
    }
  }
  O.push("움직인 칸 = " + 움직임 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 두 칸(320 · 1000)에서 `q1`·`q2` 의 고른 파일 · 로드 전 `aspect-ratio` · 로드 전·뒤 상자는? 아래 문단이 움직인 칸은?

### 5. `picture` 의 접근성 노드 (예측)

```html
<!-- html33b-36-ax.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>36 picture 의 접근성 노드</title>
</head>
<body>
<picture id="pic">
  <source id="src1" type="image/webp" srcset="i/f200.webp" title="source 의 title">
  <img id="img1" src="i/f200.png" alt="초록 사각형">
</picture>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
window.__대상 = [["pic", "#pic"], ["src1", "#src1"], ["img1", "#img1"]];
window.__끝 = () => {
  const O = [칸("요소", 8) + 칸("역할", 16) + 칸("이름", 18) + "무시"];
  for (const [k] of __대상) { const a = __AX[k]; O.push(칸(k, 8) + 칸(a.역할, 16) + 칸(JSON.stringify(a.이름), 18) + a.무시); }
  O.push("img1.currentSrc = " + document.getElementById("img1").currentSrc.split("/").pop());
  O.push("display — picture " + getComputedStyle(document.getElementById("pic")).display + " · source " + getComputedStyle(document.getElementById("src1")).display);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 세 요소의 역할 · 이름 · 무시 여부는? 두 요소의 `display` 는?

### 6. `srcset` 만으로 아트 디렉션이 안 되는 이유 (왜)

- 브라우저가 `srcset` 후보를 무엇으로 여기기에 자르기를 지켜 주지 않나? 이 판의 어느 칸이 그것을 보였나?

### 7. `type` 이 묻는 것 (경계)

- `source` 의 `type` 은 무엇을 확인하고 무엇을 확인하지 않나? 그 차이가 드러난 두 `picture` 는?

### 8. 여러 `source` 의 순서 (경계)

- 맞는 `source` 가 둘 이상이면 무엇이 쓰이나? 「더 좋은 포맷」을 쓰게 하려면 어떻게 적어야 하나?

### 9. `picture` 에서 그리는 것 (경계)

- `alt`·크기 스타일·`width`/`height` 는 각각 어느 요소에 적나? `img` 를 빼면 무엇이 남나?

### 10. 콘텐츠 카테고리와 `picture` (연결)

- [05번](../05-content-categories-and-models/1-question.md)의 카테고리로 `picture` 는 어디에 드나 — 이 배치가 연 명세 사본의 목록으로 답하면?

### 11. 명세·구현·관찰 가르기 (연결)

- 「모르는 `type` 의 요청 수」·「깨진 `source` 뒤의 동작」·「`picture`·`source` 의 트리 역할」·「`source` 의 `width`/`height` 가 쓰이는 조건」·「`canvas` 의 AVIF」는 각각 명세·구현·관찰 중 어느 층이고, 이 배치가 판정할 수 있는 것은?

### 12. 정본 경계 긋기 (연결)

- `srcset`/`sizes` 의 계산 · 자리 예약 · `video` 의 `source` 목록의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
