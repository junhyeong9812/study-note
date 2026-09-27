# html/syntax/35 — 반응형 이미지: `srcset`/`sizes` 의 두 서술자(`w`·`x`) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Images」 절](https://html.spec.whatwg.org/multipage/images.html)(`srcset` 파싱 · `sizes` 파싱 · 소스 선택) — ★★★ **이 배치의 명세 사본에 이 절이 없다.** 네트워크를 쓰지 않는 배치라 새로 받지도 못했다. 그래서 **후보를 고르는 규칙의 명세층은 전부 「사본에 절이 없어 판정 보류」다**. 이 편에서 「명세」로 적는 것은 사본에 있는 **렌더링 절의 `sizes=auto` 규칙 한 줄**뿐이다 — [Rendering 「Images」](https://html.spec.whatwg.org/multipage/rendering.html#images-3)의 `img:is([sizes="auto" i], [sizes^="auto," i]) { contain: size !important; contain-intrinsic-size: 300px 150px; }`.\
> ★★ **그래서 이 편은 「명세 ↔ Chrome 이탈」을 한 건도 세지 않는다** — 후보 선택은 흔히 **「UA 재량」이 크다**고 설명되지만, 그것도 이 배치가 **문장으로 확인하지 못한** 말이다. 표의 「비교 열」은 **명세가 아니라** 흔히 쓰는 설명(「밀도가 DPR 이상인 가장 작은 후보」)을 옮긴 **기준선**이다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 뷰포트 폭과 DPR 은 **CDP `Emulation.setDeviceMetricsOverride`** 로 칸마다 걸었고, 칸마다 **새 탭 · 캐시 끔**이다. 하네스는 [33번 주제](../33-output-progress-meter/3-answer.md)의 `## 실행 검증` 에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 이 배치는 지원 표를 따로 조회하지 않았다.
> **선행** — [34번 주제](../34-img-alt-size-and-loading/2-summary.md)(★ `width`/`height` 가 로드 전 자리를 잡는다 · `loading=lazy`).
> **경계** — **자르기가 다른 그림·다른 포맷을 고르는 것**은 [36번 주제](../36-picture-art-direction-and-format/2-summary.md)(`picture`) · **`video` 의 `source` 고르기**는 목록의 **37번 주제** · **`aspect-ratio`** 는 [CSS 31번](../../../css/syntax/31-intrinsic-sizing-and-aspect-ratio/2-summary.md) — 여기는 **한 `img` 가 후보 목록에서 무엇을 받나**까지.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)다 — 「어느 후보 파일을 받았나」.** `currentSrc` 는 그 짝으로 같이 찍는다(함께 찍은 칸에서는 늘 같았다).

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
| **안 흔들린다** | 서버가 받은 파일 · `currentSrc` · 상자 크기 · `naturalWidth` · 콘솔 문구 · 「갈린 칸 N / M」 | 칸마다 새 탭 · 캐시 끔 · 캡처 세 판이 한 글자도 같았다([33번 정답](../33-output-progress-meter/3-answer.md)의 재대조) |
| ★ **안 흔들린다(이 판)** | 창을 줄인 뒤 **다시 안 받는다** · 늘린 뒤 **다시 받는다**((4)) | 세 판이 같았다 — ★ 그래도 **구현의 선택**이다(보장이 아니다) |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | **어느 후보 파일을 받았나** · 몇 개를 받았나 · 창을 바꾼 뒤 **또 받았나** |
| **② 노드 프로브**(`currentSrc` · `naturalWidth` · `getBoundingClientRect`) | ★ **쓴다** | 고른 후보 · **밀도로 나눈 자연 폭** · 그려진 상자 |
| **CDP 콘솔 기록**(`Log.entryAdded`) | 쓴다 | `srcset` 을 **버린 후보**가 있나((3)) |
| **① · ③ · ④ · ⑥ · ⑦** | **부적용** | 무관하다 — **잴 것이 없다** |

- ★★ **제5의 상태 — 「명세가 무엇을 허용하나」를 「무엇을 골랐나」로만 물었다.** 명세 사본이 없어서 **규칙 쪽 창이 닫혀 있다.** 그 자리를 **흔히 쓰는 설명의 기준선(비교 열)** 과 견주는 것으로 채웠다 — 이 창이 못 보는 것은 「**그 선택이 허용 범위 안이냐**」다.
- ★ **18-A — 몇 군데 물었나.** (1) **6 칸** · (2) **8 칸** · (3) **9 칸 + 한 후보** · (4) **두 방향** · (5) **4 칸**. 비교 열과 견준 칸은 (1)·(2)의 **14 칸**이다.

## 한눈에 — 쉽게 말하면

**★ `srcset` 은 「사이즈별로 인화해 둔 사진 목록」, `sizes` 는 「이 사진이 들어갈 액자의 폭」이다. 브라우저는 액자 폭과 화면의 촘촘함(DPR)을 보고 목록에서 한 장을 고른다 — 액자 폭을 모르면 「화면 전체 폭」이라고 여긴다. 한번 큰 사진을 사 오면, 액자가 작아져도 작은 사진을 다시 사 오지 않는다.**

사진 인화점 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **사이즈별 인화 목록** | `srcset="a400.png 400w, a800.png 800w, a1600.png 1600w"` — **`w` 서술자 = 파일의 폭** |
| **액자 폭** | `sizes` — 레이아웃 전에 브라우저에게 **슬롯 폭**을 미리 알려 준다 |
| **액자 폭을 안 적음** | `sizes` 없음 → **`100vw`**((2)) |
| **화면의 촘촘함** | DPR — 슬롯 폭 × DPR 만큼의 픽셀이 필요하다 |
| **「1배·2배」로 인화** | `x` 서술자 — **크기가 고정된** 그림용((3)) |
| **큰 사진을 이미 삼** | 창을 줄여도 **다시 안 받는다**(이 판 · (4)) |

- **여섯 칸 전부 기준선(「밀도가 DPR 이상인 가장 작은 후보」)과 같았다**(0 / 6) — **받은 파일은 한 칸에 하나**(`src` 를 따로 받지 않았다)((1)).
- ★★★ **`sizes="100px"` 인데 CSS 폭이 800px 이면 400px 짜리를 800px 로 늘려 그린다** — `naturalWidth` 는 **100**((2)).
- ★★ **`w` 와 `x` 를 후보끼리 섞어도 버려지지 않았다** — 버려진 것은 **한 후보에 둘을 같이 쓴 것**뿐((3)).

```text
  한 칸의 계산 — 뷰포트 1400 · DPR 2 · sizes="(max-width: 600px) 100vw, 50vw"

  sizes ──> 슬롯 = 50vw = 700 CSS px
  후보 밀도 = 파일 폭 ÷ 슬롯        400/700 = 0.57   800/700 = 1.14   1600/700 = 2.29
  필요 밀도 = DPR 2                                                   └─ 2 이상인 첫 후보
  받은 파일 = a1600.png   ·   naturalWidth = 1600 ÷ 2.29 ≈ 699 (밀도로 나눈 자연 폭)
```

> **밀도(density)** — 그림 한 장이 CSS 픽셀 하나에 몇 픽셀을 쓰나. `w` 후보는 **파일 폭 ÷ 슬롯 폭**, `x` 후보는 **적힌 그대로**.\
> 예: 800px 파일을 400px 슬롯에 쓰면 밀도 2 — DPR 2 화면에 딱 맞는다.

## 이 주제가 답하려는 질문

1. **`sizes` 는 브라우저에게 무엇을 알려 주나** — 없으면, 틀리면 무엇을 받나.
2. **`w` 서술자와 `x` 서술자는 언제 나눠 쓰나** — 섞으면 어떻게 되나.
3. **한번 받은 뒤 창이 바뀌면 또 받나** — 그것은 누가 정하나(이 배치가 말할 수 있는 만큼).

## 동작 방식

### (1) 창 ⑤ — 뷰포트 셋 × DPR 둘

**언제 쓰나** — 「모바일에서 너무 큰 파일을 받는다」·「레티나에서 흐리다」를 가를 때.

`sizes` 가 **600px 이하면 100vw, 넘으면 50vw** 인 한 `img` 를, 칸마다 새 탭에서 **뷰포트 폭 · DPR 을 바꿔** 열었다. 「비교 열」은 **따로 둔 파일**이다.

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

```javascript
// html33b-35-rule.js
// 비교 열 — 흔히 설명되는 「밀도가 dpr 이상인 후보 가운데 가장 작은 것 · 없으면 가장 큰 것」.
// ★ 명세가 아니다. 이 배치의 명세 사본에는 이미지 소스 선택 절이 없다 — 이 열은 「그 설명대로면」의 기준일 뿐이다.
function 비교열(후보, 슬롯, dpr) {
  const 됨 = 후보.filter(([, w]) => w / 슬롯 >= dpr);
  return (됨.length ? 됨[0] : 후보[후보.length - 1])[0];
}
```

```text
$ python3 html33b-run.py 격자 html33b-35-grid.html
뷰포트 · dpr    슬롯 폭  밀도(400w · 800w · 1600w)   서버가 받은 파일  currentSrc  naturalWidth  비교 열
320 · dpr 1     320      1.25 · 2.5 · 5              a400.png          a400.png    320           a400.png
320 · dpr 2     320      1.25 · 2.5 · 5              a800.png          a800.png    320           a800.png
800 · dpr 1     400      1 · 2 · 4                   a400.png          a400.png    400           a400.png
800 · dpr 2     400      1 · 2 · 4                   a800.png          a800.png    400           a800.png
1400 · dpr 1    700      0.57 · 1.14 · 2.29          a800.png          a800.png    699           a800.png
1400 · dpr 2    700      0.57 · 1.14 · 2.29          a1600.png         a1600.png   699           a1600.png
(밀도 = 후보 폭 ÷ 슬롯 폭 · 비교 열 = 밀도가 dpr 이상인 후보 가운데 가장 작은 것 — 명세가 아니다)
받은 파일의 가짓수 = 3
비교 열과 갈린 칸 = 0 / 6
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **비교 열과 갈린 칸 0 / 6** — 이 판의 Chrome 은 여섯 칸 모두 「**밀도가 DPR 이상인 가장 작은 후보**」를 받았다. 받은 파일은 **세 가지**다.
- ★★★ **한 칸에 받은 파일은 하나다** — `src="i/a400.png"` 가 있어도 **따로 받지 않았다**(320·dpr 2 칸에서 `a800.png` 하나뿐).
- ★★ **`naturalWidth` 는 파일 폭이 아니다** — `a800.png` 을 받은 800 칸은 **400**, 1400 칸은 **699**. **파일 폭 ÷ 밀도**다(`800 ÷ (800/700)`). 그래서 `width`/`height` 속성이 없으면 그림은 **슬롯 폭으로** 그려진다.
- ★ **「기준선과 같았다」는 「명세가 그렇게 정한다」가 아니다** — 머리말대로 **선택 규칙의 명세층은 판정 보류**다. 이 판이 보인 것은 **이 판의 Chrome 이 여섯 칸에서 그렇게 골랐다**까지다.

```text
  받은 파일 (이 판)

               dpr 1          dpr 2
  320 (슬롯 320)  a400.png       a800.png      ← 슬롯이 같아도 DPR 이 두 배면 한 단계 위
  800 (슬롯 400)  a400.png       a800.png
  1400(슬롯 700)  a800.png       a1600.png
```

### (2) 창 ⑤ — `sizes` 가 없을 때 · 레이아웃과 다를 때

**언제 쓰나** — 「`sizes` 를 빼먹었다」·「`sizes` 와 CSS 폭이 안 맞는다」를 가를 때.

같은 후보 셋을 네 `img` 에 주고 **`sizes` 만** 바꿨다. `n2` 는 `sizes="100px"` 인데 **CSS 폭이 800px** 이다. 뷰포트 1000 에서 DPR 1·2 두 칸.

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

```text
$ python3 html33b-run.py 격자 html33b-35-sizes.html
[1000 · dpr 1]
  img                                 서버가 받은 파일    상자        naturalWidth  비교 열(슬롯 = sizes)
  n1 sizes 없음                       a1600.png           1000×500    1000          a1600.png (1000)
  n2 sizes=100px · CSS width:800px    a400.png            800×400     100           a400.png (100)
  n3 sizes=100px · CSS 폭 없음        a400.png            100×50      100           a400.png (100)
  n4 sizes=533px                      a800.png            533×266.5   533           a800.png (533)
[1000 · dpr 2]
  img                                 서버가 받은 파일    상자        naturalWidth  비교 열(슬롯 = sizes)
  n1 sizes 없음                       a1600.png           1000×500    1000          a1600.png (1000)
  n2 sizes=100px · CSS width:800px    a400.png            800×400     100           a400.png (100)
  n3 sizes=100px · CSS 폭 없음        a400.png            100×50      100           a400.png (100)
  n4 sizes=533px                      a1600.png           533×266.5   533           a1600.png (533)
비교 열과 갈린 칸 = 0 / 8
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`sizes` 가 없으면 슬롯은 `100vw`** — `n1` 의 `naturalWidth` 가 **1000**(뷰포트 폭)이고 받은 파일이 `a1600.png`. **작은 칸에 넣을 그림이면 큰 파일을 받는다.**
- ★★★ **`sizes` 가 레이아웃과 다르면 `sizes` 를 믿는다** — `n2` 는 **`a400.png` 을 받아 800×400 으로 늘려 그렸다**(`naturalWidth` 100 — 밀도 4 로 계산됐다). DPR 2 칸에서도 `a400.png` 이다 — **800 CSS px × 2 = 1600 기기 픽셀에 400px 파일**. 브라우저는 **레이아웃을 보고 고치지 않았다.**
- ★★ **CSS 폭이 없으면 `sizes` 가 곧 그려지는 폭이다** — `n3` 의 상자가 **100×50**. `n4`(`533px`)도 **533×266.5**.
- ★ **`sizes` 가 하는 일은 「레이아웃 전에 슬롯 폭을 약속하는 것」이다** — 그림 요청은 **레이아웃보다 먼저** 나갈 수 있어서([34번](../34-img-alt-size-and-loading/2-summary.md) (2) — `eager` 는 `DOMContentLoaded` 전에 나갔다) 브라우저가 CSS 폭을 알 수 없다. **약속이 틀리면 틀린 파일을 받는다.**

### (3) 창 ⑤ + 콘솔 — `x` 서술자 · 섞기 · 한 후보에 둘

**언제 쓰나** — 「아이콘·로고처럼 크기가 고정된 그림」·「`w` 와 `x` 를 섞어 썼다」를 가를 때.

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

```text
$ python3 html33b-run.py 격자 html33b-35-x.html
img                               dpr 1 받은 파일 · 상자        dpr 2 받은 파일 · 상자        dpr 3 받은 파일 · 상자
x1 1x · 2x                        d200.png · 200×100            d400.png · 200×100            d400.png · 200×100
x2 400w · 2x (sizes=200px)        a400.png · 200×100            a400.png · 200×100            a400.png · 200×100
x3 1x · 800w (sizes=200px)        a400.png · 400×200            a800.png · 200×100            a800.png · 200×100
콘솔 기록(세 칸 합쳐 서로 다른 것) —
  0 건
뒤늦게 온 요청 = 0
(exit 0)
```

한 후보에 **`800w 2x` 를 같이** 쓴 판은 따로 던졌다.

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

```text
$ python3 html33b-run.py 격자 html33b-35-drop.html
  서버    받음  i/a400.png?k=x4
  서버    풀어 줌
  서버    표지  끝
currentSrc = a400.png?k=x4
콘솔 기록 —
  Failed parsing 'srcset' attribute value since it has multiple 'x' descriptors or a mix of 'x' and 'w'/'h' descriptors.
  Dropped srcset candidate "i/a800.png?k=x4"
  Failed parsing 'srcset' attribute value since it has multiple 'x' descriptors or a mix of 'x' and 'w'/'h' descriptors.
  Dropped srcset candidate "i/a800.png?k=x4"
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`x` 서술자는 DPR 로만 고른다** — `x1` 은 dpr 1 에 `d200.png`, 2·3 에 `d400.png`. 상자는 **세 칸 다 200×100**(`d400.png` 은 밀도 2 로 계산돼 자연 폭 200). **`sizes` 가 없어도 된다** — 그래서 **크기가 고정된 그림**용이다.
- ★★★ **후보끼리 `w` 와 `x` 를 섞어도 버려지지 않았다** — `x2`(`400w` · `2x`)와 `x3`(`1x` · `800w`) 모두 **콘솔 0 건**이고 파일을 받았다. `x3` 은 dpr 1 에 `a400.png`(1x → 상자 **400×200**), 2·3 에 `a800.png`(800w ÷ 200 = 밀도 4 → **200×100**) — **두 서술자가 각자 밀도로 바뀌어 한 목록에서 경쟁했다.**
- ★★ **`x2` 는 세 칸 다 `a400.png`** — `400w ÷ 200 = 2` 와 `2x` 가 **같은 밀도 2** 라 앞의 것이 남았다(이 판의 관찰 — 같은 밀도끼리의 처리는 판정 보류).
- ★★★ **버려지는 것은 「한 후보에 서술자 둘」이다** — `800w 2x` 후보는 콘솔에 **「Failed parsing 'srcset' … a mix of 'x' and 'w'/'h' descriptors」 + 「Dropped srcset candidate」** 를 남기고 **빠졌다.** 남은 `a400.png 1x` 가 dpr 2 에서도 쓰였다(**후보가 하나뿐이면 그것**). 콘솔 두 줄이 **두 번** 찍혔다 — 이 판은 그 까닭을 파고들지 않았다.
- ★ **「`w` 와 `x` 를 섞으면 무효」는 이 판에서 성립하지 않았다** — 섞은 목록은 **동작했다.** 명세가 작성자에게 금지하는지는 **사본이 없어 판정 보류**다(그렇다면 「작성자 적합성」 문장이지 브라우저의 처리 문장이 아니다).

### (4) 창 ⑤ — 창을 바꾼 뒤

**언제 쓰나** — 「창을 줄였는데 큰 파일이 그대로다」·「회전·확대하면 다시 받나」를 가를 때.

`sizes="100vw"` 인 한 `img` 를 **큰 창에서 열고 줄인 판**과 **작은 창에서 열고 늘린 판**. 크기는 실행기가 `load` 뒤에 CDP 로 바꾼다. 페이지는 `resize` 뒤 **두 틀 × 2** 를 넘기고, 새 그림이 오고 있으면 그 `load` 까지 기다린 다음 표지를 보낸다.

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

```text
$ python3 html33b-run.py 격자 html33b-35-resize.html
[1400·dpr 2 → 320·dpr 1]
  서버    받음  i/a1600.png
  서버    풀어 줌
  서버    표지  처음 · 1400 · dpr 2 · currentSrc a1600.png
  서버    표지  바꾼 뒤 · 320 · dpr 1 · currentSrc a1600.png
  서버    표지  끝
  받은 이미지 수 = 1
[320·dpr 1 → 1400·dpr 2]
  서버    받음  i/a400.png
  서버    풀어 줌
  서버    표지  처음 · 320 · dpr 1 · currentSrc a400.png
  서버    받음  i/a1600.png
  서버    표지  바꾼 뒤 · 1400 · dpr 2 · currentSrc a1600.png
  서버    표지  끝
  받은 이미지 수 = 2
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **줄이면 다시 안 받았다** — `1400·dpr 2 → 320·dpr 1` 뒤에도 `currentSrc` 는 **`a1600.png`**, 받은 이미지 **1 개.**
- ★★★ **늘리면 다시 받았다** — `320·dpr 1 → 1400·dpr 2` 뒤에 **`a1600.png` 을 새로 받았다**(받은 이미지 **2 개**). ★ 이 칸이 **「창을 바꾼 뒤를 이 방법으로 볼 수 있다」의 대조**다 — 줄인 칸의 「안 받음」이 **기다림이 짧아서가 아님**을 보인다.
- ★★ **이것은 이 판 Chrome 의 선택이다** — 명세의 해당 절이 **사본에 없어** 「명세가 다시 받으라 하는가」를 말할 수 없다. 흔히 「**UA 재량**」이라 설명하는 자리이고, 이 판은 「**큰 것은 유지 · 작은 것은 갈아탐**」으로 골랐다.

```text
  창을 바꾼 뒤 (이 판)

  1400·dpr 2 에서 a1600 을 받음 ──> 320·dpr 1 로 줄임 ──> 그대로 a1600   (받은 것 1)
  320·dpr 1  에서 a400  을 받음 ──> 1400·dpr 2 로 늘림 ──> a1600 을 새로  (받은 것 2)
```

### (5) 창 ⑤ — `sizes="auto"`

**언제 쓰나** — 「`sizes` 를 매번 손으로 맞추기 싫다」·「`auto` 가 먹는 조건」을 가를 때.

CSS 폭 200px 인 `img` 셋과 CSS 폭이 없는 하나 · 뷰포트 1400 · DPR 1.

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

```text
$ python3 html33b-run.py 격자 html33b-35-auto.html
img                                         받은 파일   상자      contain · contain-intrinsic-size
u1 lazy · sizes=auto · CSS 200px            a400.png    200×150   size · 300px 150px
u2 (eager) · sizes=auto · CSS 200px         a1600.png   200×150   size · 300px 150px
u3 lazy · sizes="auto, 100vw" · CSS 200px   a400.png    200×150   size · 300px 150px
u4 lazy · sizes=auto · CSS 폭 없음          a400.png    300×150   size · 300px 150px
(비교 — 슬롯 200 이면 a400.png · 슬롯 300 이면 a400.png · 슬롯 1400(100vw) 이면 a1600.png)
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`lazy` 와 함께면 `auto` 가 레이아웃 폭을 슬롯으로 쓴다** — `u1` 은 **`a400.png`**(슬롯 200 이면 그것). **`lazy` 가 없으면**(`u2`) **`a1600.png`** — 슬롯 1400(100vw)일 때의 파일이다. `lazy` 는 요청을 **레이아웃 뒤로** 미루니 그때는 폭을 안다.
- ★★ **`"auto, 100vw"` 도 `lazy` 면 `auto` 로 읽혔다**(`u3` — `a400.png`). 뒤의 `100vw` 는 `auto` 를 모르는 브라우저를 위한 대비로 읽힌다(해석이다 — 이 판은 모르는 판을 던지지 않았다).
- ★★★ **`sizes=auto` 가 붙으면 상자가 `contain: size` 가 된다** — 네 칸 전부 `contain: size · contain-intrinsic-size: 300px 150px`. **CSS 폭이 없는 `u4` 는 300×150**, 폭 200 인 셋은 **200×150** — 높이가 그림 비율이 아니라 **150 에 붙는다.** 이것은 사본에 있는 **렌더링 절의 규칙 그대로**다(명세 열 — 판별). **`u2` 처럼 `auto` 가 안 먹는 칸에도** 선택자가 속성만 보니 붙는다.
- ★★ **그래서 `sizes=auto` 에는 `width`/`height` 속성이 필요하다** — [34번](../34-img-alt-size-and-loading/2-summary.md) (1) 의 자리 예약과 같은 이유로, 그리고 **`contain: size` 가 그림의 원래 크기를 무시하기** 때문이다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 폭이 바뀌는 그림 | `srcset="a400.png 400w, a800.png 800w" sizes="(max-width: 600px) 100vw, 50vw"` | 슬롯 × DPR 로 고른다 |
| 크기가 고정된 그림 | `srcset="d200.png 1x, d400.png 2x"` | DPR 로만 고른다 · `sizes` 불필요 |
| 폭을 레이아웃에 맡기기 | `loading="lazy" sizes="auto"` + `width`/`height` | `lazy` 가 **없으면** 100vw 로 떨어진다 |
| 대비 | `src="a400.png"` | `srcset` 이 먹는 판에서는 **따로 안 받는다** |

### 어디서 헷갈리나

- **`sizes` 는 CSS 가 아니다** — 약속일 뿐 레이아웃을 바꾸지 않는다. 다만 **CSS 폭이 없으면 그 폭으로 그려진다**((2) `n3`).
- **`naturalWidth` 는 밀도로 나눈 값이다** — 파일 폭을 알려면 `currentSrc` 의 파일을 봐야 한다.
- **한 후보에 `w` 와 `x` 를 같이 쓰면 그 후보만 조용히 빠진다** — 콘솔에만 남는다.
- **`sizes="auto"` 는 `loading="lazy"` 가 있어야 먹는다**((5)).

## 어디서 틀리나

### 1. `w` 서술자를 쓰고 `sizes` 를 빼먹는다

**100vw 로 계산돼** 작은 칸에도 큰 파일을 받는다((2) `n1`).

### 2. 레이아웃을 바꾸고 `sizes` 는 그대로 둔다

**작은 파일을 늘려 그린다**((2) `n2` — 400px 파일을 800px 로). 거꾸로면 쓸데없이 큰 파일을 받는다.

### 3. 로고를 `w` 서술자로 준다

크기가 고정이면 **`x` 서술자**가 짧고 맞다((3) `x1`).

### 4. 한 후보에 `800w 2x` 처럼 둘을 쓴다

**그 후보가 빠진다**((3) — 콘솔 「Dropped srcset candidate」). 에러는 없다.

### 5. 창을 줄이면 작은 파일로 갈아탈 거라 여긴다

이 판은 **안 갈아탔다**((4)). 그 동작에 기대는 설계(대역폭 절약 등)는 하지 않는다.

### 6. `sizes="auto"` 만 달고 `lazy`·`width`/`height` 를 뺀다

`lazy` 가 없으면 **100vw**, 속성이 없으면 상자가 **300×150 틀**에 붙는다((5)).

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML · Rendering)** | `img:is([sizes="auto" i], [sizes^="auto," i])` 에 `contain: size` · `contain-intrinsic-size: 300px 150px` | (5) — **판별: 맞다** |
| **명세 — 판정 보류** | `srcset`·`sizes` 파싱 · 소스 선택 · `sizes` 기본값 · 창이 바뀐 뒤 다시 고르기 · `auto` 가 먹는 조건 · 섞기의 적합성 — **이 배치의 사본에 「Images」 절이 없다** | (1)\~(5) |
| **구현(Chrome)** | 14 칸에서 「밀도 ≥ DPR 인 가장 작은 후보」 · `sizes` 없음 = 100vw · 줄이면 유지 · 늘리면 다시 받음 · 한 후보의 서술자 둘은 버리고 콘솔에 남김 · 같은 밀도는 앞의 것 | (1)\~(5) |
| **이 판의 관찰** | 비교 열과 갈린 칸 **0 / 6 · 0 / 8** · 한 칸에 받은 파일 하나 · 콘솔 두 줄이 두 번 | (1)\~(3) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **그 선택이 명세가 허용하는 범위 안인가** | 명세 사본에 선택 절이 없다 — **「이탈」도 「재량 안」도 문장으로 확인하지 못했다** |
| ★★ **느린 네트워크·절약 모드에서 다른 후보를 고르나** | 이 판은 네트워크 조건을 바꾸지 않았다 |
| **화면에 흐리게 보이나** | 픽셀을 안 봤다 — `n2` 의 「늘려 그림」은 **파일 폭과 상자 폭**으로만 말한다 |

## 언제 쓰고 언제 안 쓰나

- **`w` + `sizes`** — 레이아웃 폭이 뷰포트를 따라 바뀌는 그림(본문 사진·카드 썸네일). **`sizes` 를 레이아웃과 같이 고친다.**
- **`x`** — 크기가 고정된 그림(로고·아이콘·아바타).
- **`sizes="auto"`** — `lazy` 로 늦게 받아도 되는 그림에 **`width`/`height` 와 함께.**
- **`srcset` 만으로 「좁은 화면엔 다른 자르기」를 하지 않는다** — 브라우저가 DPR 로 다른 후보를 고를 수 있다((1) — 320·dpr 2 는 `a800.png`). 그것은 [36번 주제](../36-picture-art-direction-and-format/2-summary.md)(`picture`)다.

## 핵심 문장

1. **`srcset` 의 `w` 서술자는 파일 폭을, `sizes` 는 레이아웃 전에 슬롯 폭을 알려 준다 — 브라우저는 파일 폭 ÷ 슬롯 폭을 밀도로 삼아 DPR 과 견준다.**
2. **`sizes` 가 없으면 슬롯은 100vw 이고, `sizes` 가 레이아웃과 다르면 브라우저는 `sizes` 를 믿는다 — 틀린 약속은 틀린 파일을 받게 한다.**
3. **`x` 서술자는 DPR 로만 고르는 크기 고정 그림용이다 — 후보끼리 섞는 것은 이 판에서 동작했고, 한 후보에 둘을 쓰면 그 후보만 버려졌다.**
4. **이 판의 Chrome 은 큰 파일을 받은 뒤 창을 줄여도 작은 파일로 갈아타지 않았고, 늘리면 다시 받았다 — 구현의 선택이다.**
5. **`sizes="auto"` 는 `lazy` 와 함께일 때만 레이아웃 폭을 쓰고, 붙는 순간 상자가 `contain: size` 로 300×150 틀에 들어간다.**

## 관련 자료

- [34번 주제](../34-img-alt-size-and-loading/2-summary.md) — `width`/`height` 의 자리 예약 · `loading=lazy` 의 요청 시점.
- [33번 주제](../33-output-progress-meter/3-answer.md) — 이 묶음의 실행기 전문(뷰포트·DPR 을 거는 자리).
- [CSS 31번](../../../css/syntax/31-intrinsic-sizing-and-aspect-ratio/2-summary.md) — 내재적 크기 · `contain-intrinsic-size` 와 같은 집안의 「원래 크기」 이야기.
- [36번 주제](../36-picture-art-direction-and-format/2-summary.md)(`picture` — 다른 자르기·다른 포맷) · 목록의 **37번 주제**(`video` 의 `source`).

## 용어 풀이

- **후보(image candidate)** — `srcset` 의 쉼표로 가른 한 칸. 파일 주소 + 서술자.
- **`w` 서술자** — 그 파일의 폭(px). `sizes` 와 함께 밀도가 된다.
- **`x` 서술자** — 그 파일의 밀도를 바로 적은 것.
- **슬롯(slot) 폭** — 그림이 들어갈 자리의 CSS 폭. `sizes` 가 알려 준다.
- **DPR(device pixel ratio)** — CSS 픽셀 하나에 드는 기기 픽셀 수.
- **`currentSrc`** — 브라우저가 고른 후보의 주소.
- **`contain: size`** — 자손·내용을 보지 않고 크기를 정하는 봉쇄. `sizes=auto` 가 붙이는 규칙이다.

## 더 들어가면

- **명세의 「Images」 절을 받아 오면 다시 볼 것** — ① `sizes` 가 없을 때의 기본값 문장 · ② 같은 밀도 후보의 처리 · ③ 「환경이 바뀌면 다시 고른다」의 조건 · ④ 서술자를 섞는 것이 작성자 금지인지. 이 편의 표 「명세 — 판정 보류」 줄이 그 목록이다.
- **`h` 서술자** — 콘솔 문구에 `'w'/'h'` 가 보인다. 이 판은 던지지 않았다.
