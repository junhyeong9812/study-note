# html/syntax/36 — `picture`: 아트 디렉션과 포맷 대체 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The picture element」·「The source element」](https://html.spec.whatwg.org/multipage/embedded-content.html#the-picture-element) 와 [「Images」 절](https://html.spec.whatwg.org/multipage/images.html)의 소스 고르기 — ★★★ **이 배치의 명세 사본에 이 절들이 없다**(네트워크를 쓰지 않는 배치라 새로 받지도 못했다). 그래서 **`source` 를 고르는 규칙의 명세층은 판정 보류**다. 사본에 있는 것 셋만 명세로 적는다 — [콘텐츠 카테고리의 「Embedded content」 목록](https://html.spec.whatwg.org/multipage/dom.html#embedded-content-category)(★ **`picture` 가 들어 있다**) · [Rendering 「Attributes for embedded content and images」](https://html.spec.whatwg.org/multipage/rendering.html#attributes-for-embedded-content-and-images)(★ 「`img` 의 **dimension attribute source** 의 `width`·`height`」 — 그 말의 **정의**는 사본에 없다) · [HTML-AAM](https://w3c.github.io/html-aam/) 의 `picture`·`source` 대응(★ **「Not mapped」** — 뜻은 「노출할 **필요가 없다**」 · 「그려지면 **`generic` 으로 대응해야 한다(SHOULD)**」). 사본은 앞 배치가 2026-09-26 에 받아 둔 것이다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 하네스는 [33번 주제](../33-output-progress-meter/3-answer.md)의 `## 실행 검증` 에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> ★★ **「AVIF 가 작다」 같은 포맷 비교는 하지 않는다** — (B) 가 묻는 것은 **어느 `source` 를 골라 무엇을 받았나**뿐이다.
> **버전** — HTML 에는 언어 버전이 없다. 이 배치는 지원 표를 따로 조회하지 않았다.
> **선행** — [35번 주제](../35-srcset-and-sizes/2-summary.md)(★ `srcset` 만 쓰면 **DPR 과 캐시로 브라우저가 후보를 고른다** · 창을 줄여도 큰 것을 유지했다).
> **경계** — **`video`/`audio` 의 `source` 목록**은 목록의 **37번 주제** · **`srcset`/`sizes` 의 계산**은 [35번](../35-srcset-and-sizes/2-summary.md) · **`width`/`height` 의 자리 예약**은 [34번](../34-img-alt-size-and-loading/2-summary.md) — 여기는 **`picture` 가 `srcset` 으로 안 되는 두 경우**까지.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)다 — 「어느 `source` 의 파일을 받았나 · 몇 번 요청했나」.** 자리 예약은 레이아웃 창, 트리는 창 ⑦ 로.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 · CDP 포트·프로필 경로·서버 포트 | 판이 오르면 · 출력에는 안 들어간다 |
| **안 흔들린다** | 받은 파일 · 요청 수 · `currentSrc` · 로드 전후 상자 · `aspect-ratio` 계산값 · 접근성 역할·이름 · 「N / M」 | 칸마다 새 탭 · 캐시 끔 · 캡처 세 판이 한 글자도 같았다([33번 정답](../33-output-progress-meter/3-answer.md)의 재대조) |
| ★ **흔들린다** | 함께 나간 두 요청(`k=p` · `k=s`)이 서버에 닿는 순서((2)) | 세 판 중 두 판에서 자리를 바꿨다 — 그래서 페이지가 **표지 사이 묶음 안만 이름순으로** 찍는다(표지와의 앞뒤는 안 흔들린다) |
| **안 흔들린다(이 머신)** | 깨진 `t3` 의 상자 높이 `24` | 대체 글자 한 줄의 높이 — 글꼴에 달린 칸 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | **어느 `source` 의 파일을 받았나** · 모르는 `type` 의 파일을 **요청조차 했나**((1)\~(3)) |
| **레이아웃**(`getBoundingClientRect` · `aspectRatio`) | 쓴다 | `source` 의 `width`/`height` 가 **로드 전 자리**를 바꾸나((4)) |
| **⑦ 접근성 트리** | 쓴다 | `picture`·`source`·`img` 가 트리에 **무엇으로** 남나((5)) |
| **① · ③ · ④ · ⑥** | **부적용** | 무관하다 — **잴 것이 없다** |

- ★★ **제5의 상태 — 「포맷 대체」를 진짜 새 포맷 없이 물었다.** 이 머신에 AVIF 인코더가 없다(아래 블록). 그래서 두 가지로 물었다 — **Chrome 이 아는 새 포맷**은 Chrome 의 `canvas` 로 만든 **WebP**, **모르는 포맷**은 **`type="image/x-nope"`**(없는 MIME). ★ 이 창이 못 보는 것 — **AVIF 를 실제로 받는 판.**
- ★ **18-A — 몇 군데 물었나.** (1) **6 칸 × 두 방식** · (2) **한 방향** · (3) **`picture` 다섯** · (4) **2 칸 × 두 방식** · (5) **노드 셋**. (3) 의 「요청 0」은 **모르는 `type` 의 `source` 두 개**를 물은 값이다.

```text
$ command -v cwebp avifenc
(exit 1)
```

```text
$ od -A d -c -N 16 i/f200.webp
0000000   R   I   F   F   T 002  \0  \0   W   E   B   P   V   P   8   X
0000016
(exit 0)
```

- **`cwebp`·`avifenc` 둘 다 없다**(`exit 1` · 출력 0 줄). WebP 는 [34번의 생성기](../34-img-alt-size-and-loading/2-summary.md)가 `canvas.toDataURL('image/webp')` 로 만들었고(머리 16 바이트가 `RIFF … WEBP`), **같은 판에서 `image/avif` 를 물으면 `image/png` 가 돌아왔다** — Chrome 의 `canvas` 는 AVIF 로 **인코딩하지 않는다.**

## 한눈에 — 쉽게 말하면

**★ `srcset` 은 「같은 사진의 사이즈별 인화본」, `picture` 는 「조건마다 다른 사진을 붙인 게시판」이다. 인화본 중 어느 것을 쓸지는 가게(브라우저)가 정하지만, 게시판의 「좁은 벽에는 정사각형」 쪽지는 가게가 어길 수 없다. 그리고 가게가 모르는 필름(모르는 `type`)으로 찍은 사진은 사 오지도 않는다.**

게시판 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **사이즈별 인화본** | `img srcset` — **같은 그림**의 크기만 다른 후보. 고르는 건 브라우저 |
| **조건별 쪽지** | `<source media="…">` — 조건이 맞으면 **그 `source`** · 다른 자르기(아트 디렉션) |
| **필름 종류 쪽지** | `<source type="…">` — 모르는 `type` 이면 **건너뛴다**(요청 0) |
| **위에서부터 읽기** | **처음 맞는 `source`** — 뒤에 더 좋은 게 있어도 |
| **액자** | 안의 **`img`** — 그림이 실제로 그려지는 곳 · `alt` 는 여기 |
| **액자 없는 게시판** | `img` 없는 `picture` — **아무것도 안 그리고 아무것도 안 받는다** |

- **정사각형을 받은 칸 — `picture` 2 / 6 · `srcset` 만 1 / 6** — `srcset` 만 쓴 쪽은 320 칸에서 **DPR 에 따라** 자르기가 바뀌었다((1)).
- ★★ **창을 줄이면 `picture` 는 정사각형을 새로 받았고, `srcset` 만은 그대로였다**((2)).
- ★★★ **모르는 `type` 의 `source` 는 파일을 요청조차 안 했다**(0) · **처음 맞는 `source` 를 썼다** · **깨진 `source` 파일은 `img` 의 `src` 로 넘어가지 않았다**((3)).

```text
  브라우저가 picture 를 읽는 순서 (이 판의 관찰)

  <picture>
    <source media type srcset>   ── 조건(media · type)이 맞나? ── 예 ─> 이 srcset 에서 고른다 ─┐
    <source …>                   ── 아니면 다음                                                 │
    <img src srcset alt>         ── 맞는 source 가 없으면 img 의 것                             │
  </picture>                                                                                    │
                                          그려지는 곳은 언제나 img ── currentSrc · alt · 상자 <─┘
  ★ 고른 뒤에 파일이 깨져도 다음 후보로 넘어가지 않는다 ((3) t3)
```

> **아트 디렉션(art direction)** — 화면 조건에 따라 **다른 자르기·다른 구도**의 그림을 보여 주는 것.\
> 예: 넓은 화면엔 가로로 긴 풍경, 좁은 화면엔 인물만 잘라 낸 정사각형.

## 이 주제가 답하려는 질문

1. **`srcset` 만으로 안 되고 `picture` 가 필요한 두 경우는 무엇인가** — 다른 자르기 · 다른 포맷.
2. **`picture` 는 `source` 를 어떻게 고르나** — 순서 · 모르는 `type` · 고른 뒤 깨졌을 때.
3. **`picture` 안에서 `alt`·`width`/`height` 는 어디에 붙나** — `source` 에 적으면 무엇이 달라지나.

## 동작 방식

### (1) 창 ⑤ — 경우 A · 아트 디렉션: `media` 대 `srcset` 만

**언제 쓰나** — 「좁은 화면엔 반드시 정사각형 자르기를」 을 `srcset` 으로 할지 `picture` 로 할지 가를 때.

같은 두 파일(가로 `c800x400` · 정사각 `c400x400`)을 **`picture`(`media="(max-width: 600px)"`)** 와 **`img srcset`(`400w`·`800w` · `sizes="100vw"`)** 에 주고, 뷰포트 셋 × DPR 둘에서 열었다.

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

```text
$ python3 html33b-run.py 격자 html33b-36-art.html
뷰포트 · dpr    picture(media) 가 받은 파일   img srcset 만 가 받은 파일
320 · dpr 1     c400x400.png                  c400x400.png
320 · dpr 2     c400x400.png                  c800x400.png
800 · dpr 1     c800x400.png                  c800x400.png
800 · dpr 2     c800x400.png                  c800x400.png
1400 · dpr 1    c800x400.png                  c800x400.png
1400 · dpr 2    c800x400.png                  c800x400.png
정사각형(c400x400)을 받은 칸 — picture 2 / 6 · srcset 만 1 / 6
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`media` 는 조건대로다** — `picture` 는 320 칸 **두 DPR 모두 정사각**, 800·1400 은 **가로**.
- ★★★ **`srcset` 만 쓴 쪽은 320 칸에서 DPR 에 따라 갈렸다** — dpr 1 은 **정사각**(`400/320 = 1.25 ≥ 1`), dpr 2 는 **가로**(`800/320 = 2.5 ≥ 2`). 브라우저에게 `srcset` 후보는 「**같은 그림의 크기**」라서, 필요한 밀도에 맞는 쪽을 **자르기와 상관없이** 골랐다([35번](../35-srcset-and-sizes/2-summary.md) (1) 과 같은 계산).
- ★★ **그래서 「좁은 화면엔 정사각」을 `srcset` 으로 적으면 레티나 폰에서 깨진다** — 이 판의 320·dpr 2 칸이 그 자리다.

### (2) 창 ⑤ — 창을 줄인 뒤

**언제 쓰나** — 「회전·창 크기 변경 뒤에 자르기가 따라오나」를 가를 때.

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

```text
$ python3 html33b-run.py 격자 html33b-36-resize.html
  서버    받음  i/c800x400.png?k=p
  서버    받음  i/c800x400.png?k=s
  서버    풀어 줌
  서버    표지  처음 · 1400 · picture c800x400.png?k=p · srcset 만 c800x400.png?k=s
  서버    받음  i/c400x400.png?k=p
  서버    표지  줄인 뒤 · 320 · picture c400x400.png?k=p · srcset 만 c800x400.png?k=s
  서버    표지  끝
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`picture` 는 줄인 뒤 정사각(`c400x400`)을 새로 받았다** — `media` 가 참이 되니 **다른 `source`** 가 골라졌다.
- ★★★ **`srcset` 만은 그대로 가로(`c800x400`)였다** — [35번](../35-srcset-and-sizes/2-summary.md) (4) 의 「큰 것을 받은 뒤 줄여도 다시 안 받는다」와 같은 모양이다. **`srcset` 은 같은 그림이라 큰 것을 계속 써도 된다**고 보는 셈이고, **`media` 는 다른 그림이라 바꿔야 한다.**
- ★ **이 둘의 차이가 명세의 문장인지는 판정 보류**다(선택 절이 사본에 없다) — 이 판의 Chrome 이 두 경우를 **다르게 다뤘다**까지가 관찰이다.

### (3) 창 ⑤ — 경우 B · 포맷 대체: `type` 과 순서

**언제 쓰나** — 「새 포맷을 먼저 주고 옛 포맷으로 대비」·「`source` 를 여러 개 줄 때 순서」·「파일이 없는 `source`」를 가를 때.

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

```text
$ python3 html33b-run.py 격자 html33b-36-type.html
picture                         서버가 받은 파일                  currentSrc        상자      naturalWidth
t1 x-nope, webp, img(png)       f200.webp                         f200.webp         200×100   200
t2 png, webp, img(png)          g200.png                          g200.png          200×100   200
t3 webp(파일 없음), img(png)    nope.webp                         nope.webp         1000×24   0
t4 x-nope, img(png)             f200.png                          f200.png          200×100   200
t5 img 없는 picture · webp      (없음)                            (img 없음)        0×0       —
type="image/x-nope" 인 source 의 파일(g200.png)을 받은 요청 = 0
서버가 받은 이미지 요청 = 4
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **모르는 `type` 의 `source` 는 파일을 요청조차 안 했다** — `x-nope` 둘(`t1`·`t4`)의 `g200.png` 요청이 **0.** 다섯 `picture` 에서 서버가 받은 이미지는 **4 개**뿐 — `picture` 마다 **하나씩**(img 없는 `t5` 는 0).
- ★★★ **아는 `type` 중 처음 맞는 것** — `t1` 은 `x-nope` 를 건너 **`webp`**, `t2` 는 첫 `source` 가 `image/png` 라 **`g200.png`**(뒤의 `webp` 는 안 봤다). **「더 좋은 포맷」을 고르는 게 아니라 위에서부터 처음 맞는 것이다.**
- ★★★ **고른 `source` 의 파일이 없으면 깨진 채로 끝났다** — `t3` 는 `nope.webp` 를 요청해 404 를 받고 **`img` 의 `f200.png` 를 요청하지 않았다**(`naturalWidth` 0 · 상자는 대체 글자 줄). `type` 은 「**이 포맷을 아나**」만 묻지 「**파일이 있나**」를 묻지 않는다.
- ★★ **`img` 없는 `picture` 는 아무것도 안 그리고 아무것도 안 받았다** — `t5` 는 요청 0 · 상자 **0×0**. **그리는 것은 `img` 다.**

```text
  다섯 picture 가 받은 것 (이 판)

  t1  x-nope ✕(요청 없음) → webp ✓ ─────────────── f200.webp
  t2  png ✓ ────────────────────── (webp 는 안 봄) ─ g200.png
  t3  webp ✓ → 404 ── (img 의 png 로 안 넘어감) ──── 깨짐
  t4  x-nope ✕(요청 없음) → (source 없음) → img ─── f200.png
  t5  webp ✓ … 그런데 img 가 없다 ─────────────────── 요청 0 · 0×0
```

### (4) 레이아웃 창 — `source` 의 `width`/`height`

**언제 쓰나** — 「좁은 화면용 정사각 `source` 인데 로드 전 자리가 가로 비율로 잡혀 밀린다」를 가를 때.

폭 300 칸에 **정사각 `source`(좁은 화면)** + **가로 `img`(800×400 속성)** 를 두고, 한쪽 `source` 에만 `width="400" height="400"` 을 달았다. 그림은 붙잡아 두고 로드 전·뒤를 쟀다.

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

```text
$ python3 html33b-run.py 격자 html33b-36-dims.html
[320 · dpr 1]
  picture                         고른 파일     로드 전 aspect-ratio  로드 전 상자  로드 뒤 상자  아래 요소가 움직였나
  q1 source 에 width/height 있음  c400x400.png  "auto 400 / 400"      300×300       300×300       아니오 (316 → 316)
  q2 source 에 width/height 없음  c400x400.png  "auto 800 / 400"      300×150       300×300       예 (522 → 672)
[1000 · dpr 1]
  picture                         고른 파일     로드 전 aspect-ratio  로드 전 상자  로드 뒤 상자  아래 요소가 움직였나
  q1 source 에 width/height 있음  c800x400.png  "auto 800 / 400"      300×150       300×150       아니오 (166 → 166)
  q2 source 에 width/height 없음  c800x400.png  "auto 800 / 400"      300×150       300×150       아니오 (372 → 372)
움직인 칸 = 1 / 4
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`source` 의 `width`/`height` 가 로드 전 비율을 바꿨다** — 320 칸의 `q1` 은 **`"auto 400 / 400"`** · 300×300 으로 자리를 잡아 **안 움직였다.** 속성이 없는 `q2` 는 `img` 의 **`"auto 800 / 400"`** 으로 300×150 을 잡았다가 정사각이 오며 **300×300 으로 늘어 아래가 150 내려갔다.** 움직인 칸 **1 / 4**.
- ★★ **1000 칸에서는 둘이 같다** — `source` 가 안 골라지니 `img` 의 속성이 쓰였다.
- ★ **명세 사본의 렌더링 절은 「`img` 의 dimension attribute source 의 `width`·`height`」라고만 적는다** — 그 **정의**(고른 `source` 인가)는 사본에 없어 판별은 **이 관찰까지**다. 이 판은 **고른 `source` 에 속성이 있으면 그것을, 없으면 `img` 의 것을** 썼다.

### (5) 창 ⑦ — `picture`·`source`·`img` 의 노드

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

```text
$ python3 html33b-form.py page html33b-36-ax.html
요소    역할            이름              무시
pic     generic         ""                false
src1    generic         ""                false
img1    image           "초록 사각형"     false
img1.currentSrc = f200.webp
display — picture inline · source inline
(exit 0)
```

```text
$ python3 html33b-form.py ax html33b-36-ax.html
RootWebArea    이름='36 picture 의 접근성 노드'
  generic        이름=''
    generic        이름=''
      generic        이름=''
      image          이름='초록 사각형'
(exit 0)
```

- ★★★ **이름을 가진 노드는 `img` 하나다** — `image` · 「초록 사각형」. **`alt` 는 `img` 에 적는다.** `source` 의 `title` 은 **이름이 되지 않았다.**
- ★★ **`picture`·`source` 는 `generic`** 으로 트리에 있다(무시 `false` · 이름 없음). HTML-AAM 은 둘 다 **「Not mapped」** — 뜻은 「노출할 **필요가 없다**」이고, 「작성자가 그리게 만든 판이면 **`generic` 으로 대응해야 한다(SHOULD)**」. 이 판의 두 요소는 **`display: inline`**(렌더링 절의 숨김 목록에 둘이 없다)이라 **그려지는** 판이다 — **명세와 어긋나지 않는다.**

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 다른 자르기 | `<picture><source media="(max-width: 600px)" srcset="sq.png" width="400" height="400"><img src="wide.png" width="800" height="400" alt="…"></picture>` | 조건대로 · 창이 바뀌면 따라온다 |
| 새 포맷 + 대비 | `<picture><source type="image/avif" srcset="a.avif"><source type="image/webp" srcset="a.webp"><img src="a.png" alt="…"></picture>` | 모르는 `type` 은 요청 0 · 처음 맞는 것 |
| 같은 그림의 크기만 | `<img srcset="… 400w, … 800w" sizes="…">` | `picture` 가 필요 없다([35번](../35-srcset-and-sizes/2-summary.md)) |

### 어디서 헷갈리나

- **`picture` 는 그리지 않는다** — 그리는 것은 **안의 `img`** 다. `img` 가 없으면 **아무것도 없다.**
- **`source` 는 순서가 뜻이다** — 가장 원하는 것을 **위에.**
- **`type` 은 파일을 검사하지 않는다** — 적은 포맷을 알면 **그 파일로 끝**이다.
- **`alt` 는 `img` 에만** — `source` 에 적을 자리가 없다.

## 어디서 틀리나

### 1. 「좁은 화면엔 정사각」을 `srcset` 의 `w` 후보로 적는다

**DPR 이 높은 폰에서 가로 그림을 받는다**((1) — 320·dpr 2). `picture` + `media` 로.

### 2. 좋은 포맷을 아래에 둔다

**위의 것이 먼저 맞으면 그것으로 끝**이다((3) `t2`).

### 3. 새 포맷 파일을 빼먹은 채 `source` 를 둔다

**깨진 그림**이 된다 — `img` 로 안 넘어간다((3) `t3`).

### 4. `picture` 에 스타일을 준다

크기·`object-fit` 은 **안의 `img`** 에 준다 — `picture` 는 `inline` 인 틀일 뿐이다((5) `display`).

### 5. 정사각 `source` 에 `width`/`height` 를 안 단다

**로드 전 자리가 `img` 의 가로 비율**로 잡혀 아래가 밀린다((4) `q2`).

### 6. `img` 없이 `source` 만 둔다

**아무것도 안 나온다**((3) `t5`).

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML · 콘텐츠 카테고리)** | `picture` 는 **임베디드 콘텐츠**다 | — |
| **명세(HTML · Rendering)** | 「`img` 의 **dimension attribute source**」의 `width`/`height` 가 차원 속성·`aspect-ratio` 로 — 정의는 사본에 없다 · `picture`·`source` 는 숨김 목록에 없다 | (4)·(5) |
| **명세(HTML-AAM)** | `picture`·`source` 는 Not mapped(필요 없음 · 그려지면 generic SHOULD) | (5) — **판별: 어긋나지 않는다** |
| **명세 — 판정 보류** | `source` 고르기 순서 · `media`/`type` 판정 · 창이 바뀐 뒤 다시 고르기 · 고른 뒤 깨졌을 때 · `img` 가 없을 때 — **이 배치의 사본에 절이 없다** | (1)\~(3) |
| **구현(Chrome)** | 모르는 `type` 은 요청 0 · 처음 맞는 것 · 깨져도 안 넘어감 · `media` 가 바뀌면 다시 받음(`srcset` 만은 유지) · `canvas` 가 AVIF 로 인코딩하지 않음 | (1)\~(3) |
| **이 판의 관찰** | 정사각을 받은 칸 **2 / 6 대 1 / 6** · 요청 **4 / 다섯 `picture`** · 움직인 칸 **1 / 4** | (1)·(3)·(4) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **AVIF 를 실제로 받는 판** | 이 머신에 AVIF 인코더가 없다 · `canvas` 도 안 만든다 — `type` 판정은 WebP 와 없는 MIME 으로만 물었다 |
| ★★ **그 선택이 명세의 규칙인가** | 선택 절이 사본에 없다 — 「이탈」도 「규칙대로」도 문장으로 확인하지 못했다 |
| **포맷마다 파일 크기·화질** | 이 편의 질문이 아니다 — 바이트 수는 인코더 설정 하나로 뒤집힌다 |

## 언제 쓰고 언제 안 쓰나

- **다른 자르기·구도가 필요할 때** — `picture` + `media`. 각 `source` 에 **`width`/`height`**.
- **새 포맷을 쓰되 모르는 브라우저를 대비할 때** — `picture` + `type`, **원하는 순서대로 위에서부터**, 마지막에 `img`.
- **같은 그림의 크기만 다를 때** — `picture` 를 쓰지 않는다. `img srcset sizes` 가 짧고, 브라우저가 DPR·캐시에 맞춰 고르게 둔다.
- **`alt` 는 `img` 에**, `picture` 에는 스타일을 주지 않는다.

## 핵심 문장

1. **`srcset` 후보는 「같은 그림의 크기」라서 브라우저가 DPR 에 맞춰 고른다 — 다른 자르기를 강제하려면 `picture` 의 `media` 가 필요하다.**
2. **이 판의 Chrome 은 창을 줄였을 때 `media` 로 고른 `picture` 는 다른 그림을 새로 받았고, `srcset` 만 쓴 `img` 는 큰 그림을 유지했다.**
3. **`picture` 는 위에서부터 처음 맞는 `source` 를 쓰고, 모르는 `type` 의 `source` 는 파일을 요청조차 하지 않는다.**
4. **고른 `source` 의 파일이 깨져도 `img` 의 `src` 로 넘어가지 않았다 — `type` 은 포맷만 묻지 파일을 검사하지 않는다.**
5. **그리는 것은 안의 `img` 다 — `alt` 는 거기 적고, `img` 가 없으면 아무것도 안 나오며, 고른 `source` 의 `width`/`height` 가 로드 전 자리를 정한다.**

## 관련 자료

- [35번 주제](../35-srcset-and-sizes/2-summary.md) — `srcset`/`sizes` 의 계산 · 창을 줄인 뒤 유지.
- [34번 주제](../34-img-alt-size-and-loading/2-summary.md) — `width`/`height` 의 자리 예약 · `alt` 의 역할 · 시험 이미지 생성기.
- [05번 주제](../05-content-categories-and-models/2-summary.md) — 콘텐츠 카테고리. ★ 그 편 (1) 의 그림은 임베디드 칸에 `picture(는 아님)` 이라 적었는데, **이 배치가 연 사본의 「Embedded content」 목록에는 `picture` 가 있다**(`audio canvas embed iframe img math object picture svg video`) — 그 편의 그림은 명세 정의를 옮긴 그림이라고 스스로 밝히므로 **다시 대조해 볼 자리**다.
- 목록의 **37번 주제**(`video`/`audio` 의 `source` 목록).

## 용어 풀이

- **아트 디렉션** — 조건에 따라 다른 자르기·구도의 그림을 보이는 것.
- **포맷 대체** — 새 포맷을 먼저 주고, 모르는 브라우저에는 옛 포맷을 주는 것.
- **`source`** — `picture`(와 `video`/`audio`) 안의 후보 목록 한 칸. 스스로는 그리지 않는다.
- **dimension attribute source** — `img` 의 `width`/`height` 를 **어디서 읽나**의 이름. 이 판은 「고른 `source` 에 있으면 그것」으로 관찰했다.
- **`generic`** — 뜻 없는 틀 역할. 이름을 갖지 않는다.

## 더 들어가면

- **AVIF 를 받는 판** — 인코더(`avifenc`)가 생기면 `type="image/avif"` 칸을 **진짜 파일로** 다시 던진다. 지금 표의 (3) 은 「아는 포맷(WebP)」과 「모르는 포맷(없는 MIME)」의 두 극으로만 물었다.
- **`source` 의 `sizes`** — `source` 도 `srcset` 에 `w` 서술자와 `sizes` 를 받는다. 이 판은 `source` 안의 `w` 계산을 던지지 않았다([35번](../35-srcset-and-sizes/2-summary.md)의 계산이 그대로일 것으로 보이지만 확인하지 않았다).
- **`media` 와 `type` 을 한 `source` 에 같이** — 둘 다 맞아야 쓰일 것이다. 이 판은 던지지 않았다.
