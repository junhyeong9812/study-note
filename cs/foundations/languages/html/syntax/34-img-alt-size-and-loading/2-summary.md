# html/syntax/34 — `img`: `alt`·`width`/`height`·`loading`/`decoding`/`fetchpriority` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [Rendering 「Attributes for embedded content and images」](https://html.spec.whatwg.org/multipage/rendering.html#attributes-for-embedded-content-and-images)(★ **`width`·`height` 는 차원 속성 `width`·`height` 로, 그리고 둘 다 있으면 `aspect-ratio: auto w / h` 로 번역된다** — 「map to the aspect-ratio property (using dimension rules)」), [Rendering 「Images」](https://html.spec.whatwg.org/multipage/rendering.html#images-3)(★ 그림이 없을 때 — **`alt` 가 없으면 아이콘 · 글자를 나타내면 글자 · 아무것도 안 나타내면 크기 0**), [HTML-AAM](https://w3c.github.io/html-aam/) 의 `img` 대응(★ **`alt` 가 공백뿐이면 `none`/`presentation`**)과 「img 의 이름 계산」(★ **`alt` → `title` → figcaption 조건 → 이름 없음** — 파일 이름은 없다). **명세 본문은 앞 배치가 2026-09-26 에 받아 둔 사본**(`rendering` · HTML-AAM)으로 읽었다 — 이 배치는 네트워크를 쓰지 않았다.\
> ★★ **`img` 요소 절 · `loading` 속성(지연 로딩) 절 · `fetchpriority` 절은 이 배치의 사본에 없다** — 그래서 `loading`·`decoding`·`fetchpriority` 의 **명세층은 판정 보류**이고, 이 편은 그 셋을 **요청 순서·시점 참/거짓과 CDP 의 우선순위**로만 적는다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 하네스는 [33번 주제](../33-output-progress-meter/3-answer.md)의 `## 실행 검증` 에 있다(29번 하네스 + 이 묶음의 실행기).\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> ★★★ **성능 수치는 없다** — 「`lazy` 가 LCP 를 나쁘게 한다」·「`fetchpriority` 가 빨리 받는다」 같은 **시간 주장을 하지 않는다.** 이 편이 재는 것은 **요청이 갔나 · 무엇보다 먼저 갔나 · 우선순위 이름** 셋뿐이다.
> **버전** — HTML 에는 언어 버전이 없다. 이 배치는 지원 표를 따로 조회하지 않았다.
> **선행** — [05번 주제](../05-content-categories-and-models/2-summary.md)(★ `img` 는 **흐름·구절·임베디드** — 문단 안에 섞인다).
> **경계** — **`aspect-ratio` 속성 자체**는 [CSS 31번](../../../css/syntax/31-intrinsic-sizing-and-aspect-ratio/2-summary.md)(★ 「`auto <ratio>` — 원래 비율이 있으면 그것을, 없으면 이 비율을」), **`object-fit` 으로 상자 안에 맞추기**는 [CSS 44번](../../../css/syntax/44-backgrounds-and-object-fit/2-summary.md) · **`srcset`/`sizes`** 는 [35번 주제](../35-srcset-and-sizes/2-summary.md) · **`DOMContentLoaded`/`load` 의 정의**는 [08번](../08-script-loading/2-summary.md) · **`IntersectionObserver` 로 직접 지연 로딩하기**는 [web-api 35번](../../../../web-api/35-intersection-observer/2-summary.md) — 여기는 **`img` 속성이 상자와 요청에 무엇을 하나**까지.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)와 레이아웃 창(`getBoundingClientRect`)이다** — 이미지를 서버가 **`/go` 까지 붙잡아 두고** 로드 **전**과 **뒤**를 같은 탭에서 잰다. `alt` 는 창 ⑦ 로.

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
| ★ **흔들린다** | **표지 사이에 붙어 온 요청들이 서버에 닿는 순서**((1)·(2)) | 세 판 중 한 판에서 `위-eager`·`아래-eager` 가 자리를 바꿨다 — 그래서 페이지가 **표지 사이 묶음 안만 이름순으로** 찍는다(표지와의 앞뒤는 안 흔들린다) |
| ★ **흔들린다** | **붙잡힌 여섯 요청이 서버에 닿는 순서**((4)) | 20 판에 **한 가지가 아니었다**(첫 판은 일곱 가지) — 그래서 한 판의 순서를 싣지 않고 **가짓수를 센다**(규칙 11) · 그 블록의 판 수 칸은 재대조에서도 흔들린다 |
| **안 흔들린다** | 로드 전후의 상자 크기 · `aspect-ratio` 계산값 · 「움직인 칸 N / M」 · 요청이 `DOMContentLoaded`·`load`·스크롤보다 먼저 왔나 · CDP 의 처음 우선순위 · 접근성 역할·이름 | 캡처 세 판이 한 글자도 같았다([33번 정답](../33-output-progress-meter/3-answer.md)의 재대조) |
| **안 흔들린다(이 머신)** | 깨진 이미지 `alt` 글자 상자의 폭 `94.09375` | **글꼴에 달린 칸**이다 — 다른 머신에서는 다를 수 있다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | 이미지 요청이 **갔나 · 어느 표지(`DOMContentLoaded`·`load`·스크롤)보다 먼저 갔나**((2)·(4)) |
| **레이아웃**(`getBoundingClientRect` · `getComputedStyle(img).aspectRatio`) | ★ **쓴다 — 본체** | 로드 **전** 상자가 자리를 잡았나 · **아래 요소가 움직였나**(참/거짓)((1)) |
| **CDP `Network.requestWillBeSent` 의 `initialPriority`** | ★ **쓴다** | 요청이 **어느 우선순위 이름**으로 나갔나 · 나중에 바뀌었나((2)·(4)) |
| **⑦ 접근성 트리** | 쓴다 | `alt` 셋이 만드는 **역할 · 이름**((3)) |
| **① · ③ · ④ · ⑥** | **부적용** | 무관하다 — **잴 것이 없다** |

- ★★ **제5의 상태 — 「레이아웃 시프트」를 수치 대신 참/거짓으로 물었다.** `PerformanceObserver('layout-shift')` 의 **점수 합**은 한 판의 수치라 근거가 못 된다(규칙 24). 대신 **이미지가 오기 전과 뒤에 아래 요소의 `top` 이 달라졌나**를 물었다 — 그리고 「전」을 확실히 잡으려고 **서버가 이미지를 붙잡아 둔다.**
- ★★ **제5의 상태 — 「`fetchpriority` 가 먹나」를 시간이 아니라 우선순위 이름으로 물었다.** CDP 가 요청마다 **처음 우선순위**(`initialPriority`)와 **바뀐 우선순위**를 알려 준다. 서버에 닿는 **순서**는 흔들려서 **20 판의 가짓수**로 따로 셌다((4)).
- ★ **18-A — 몇 군데 물었나.** (1) 은 **여섯 `img` × 로드 전·뒤** · (2) 는 **네 `img` × 표지 셋** · (3) 은 **여섯 `img` × 명세 열 셋 = 18 칸** · (4) 는 **여섯 `img`** 와 **20 판**.

## 한눈에 — 쉽게 말하면

**★ `width`/`height` 는 「사진이 오기 전에 앨범에 붙여 둔 빈 액자」다. 액자가 있으면 사진이 와도 옆 사진들이 밀리지 않는다. `loading=lazy` 는 「넘길 때 가서 사진을 사 오기」 — 첫 장에 쓰면 첫 장부터 늦게 사 온다. `alt` 는 「사진이 없을 때 액자에 붙는 설명 쪽지」 — 빈 쪽지(`alt=""`)는 「이건 장식」이라는 뜻이다.**

사진 앨범 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **빈 액자** | `width` + `height` → 로드 **전에** 상자 크기 · `aspect-ratio: auto 300 / 150` |
| **폭만 적은 액자** | `width` 만 → 로드 전 **높이 0** — 사진이 오면 아래가 밀린다 |
| **액자를 늘리면서 세로 치수는 그대로 둔 것** | 속성 둘 + CSS `width:100%` 만 → **높이가 150 에 고정**돼 **찌그러진다** · `height:auto` 가 필요하다((1)) |
| **넘길 때 가서 사 오기** | `loading=lazy` — 첫 장이면 **`DOMContentLoaded` 뒤**에야 요청 · 한참 뒤 장이면 **스크롤 전까지 요청 없음** |
| **설명 쪽지** | `alt="설명"` — 역할 `image` · 이름 = 그 글자 · 깨지면 **글자**가 그려진다 |
| **빈 쪽지** | `alt=""` — 역할 **`none`** · 트리에서 **무시** · 깨지면 **0×0** |
| **쪽지 없음** | `alt` 없음 — 역할 `image` · **이름 없음**(파일 이름도 아니다) · 깨지면 **16×16** 상자 |

- **움직인 칸 3 / 6** — `width` 만 · 속성 없음 · 속성 없이 `width:100%; height:auto`((1)).
- ★★★ **속성 둘 + `width:100%` 만 주면 150×150 으로 찌그러졌다** — 비율 번역이 있어도 **`height` 속성이 높이를 먼저 박는다**((1) D).
- ★★ **`load` 전에 요청이 간 칸 3 / 4** — 한참 아래의 `lazy` 하나만 스크롤 뒤((2)).

```text
  로드 전의 상자 — 150px 칸에 300×150 그림 (이 판)

    속성                           로드 전      로드 뒤      아래가 움직였나
    width + height                 300×150      300×150      아니오
    width 만                       300×0        300×150      예
    없음                           0×0          300×150      예
    둘 + CSS width:100%            150×150      150×150      아니오   ← 찌그러짐(높이가 속성 150)
    둘 + CSS width:100%;height:auto 150×75      150×75       아니오   ← 비율대로
    없음 + CSS width:100%;height:auto 150×0     150×75       예
```

> **레이아웃 시프트(layout shift)** — 늦게 온 내용이 자리를 차지하면서 **이미 그려진 요소를 밀어내는 것.**\
> 예: 사진이 오면서 그 아래 문단이 150px 내려간다.

## 이 주제가 답하려는 질문

1. **`width`/`height` 를 적으면 로드 전에 무엇이 달라지나** — 반응형 CSS(`width:100%`)와 겹치면 어떻게 되나.
2. **`loading=lazy` 는 요청을 언제로 미루나** — 첫 화면의 이미지에 쓰면 무엇이 늦어지나(시간이 아니라 순서로).
3. **`alt` 없음 · `alt=""` · `alt="설명"` 은 트리와 깨진 화면에서 어떻게 갈리나** — `decoding`·`fetchpriority` 는 요청에 무엇을 남기나.

## 예시 데이터 — 이 묶음이 공유하는 것

34\~36번의 시험 이미지는 캡처가 **매번 스크래치패드에서 새로 만든다**(PNG 는 표준 라이브러리, WebP 는 Chrome 의 `canvas`). 파일 이름에는 **크기만** 적었다 — `p300x150.png` 은 300×150. 전부 **한 색으로 칠한** 그림이고 **내용은 묻지 않는다.** 저장소에는 들어가지 않는다.

```text
$ python3 html33b-make-images.py
canvas.toDataURL('image/webp') 가 돌려준 형식 = image/webp
canvas.toDataURL('image/avif') 가 돌려준 형식 = image/png
(exit 0)
```

```text
$ stat -c '%s %n' i/*
5020 i/a1600.png
574 i/a400.png
1572 i/a800.png
1059 i/c400x400.png
1574 i/c800x400.png
262 i/d200.png
574 i/d400.png
261 i/f200.png
604 i/f200.webp
261 i/g200.png
390 i/p300x150.png
(exit 0)
```

★ **바이트 수는 이 편의 근거가 아니다** — 「어느 포맷이 작다」는 주장을 하지 않는다(생성기의 설정 하나로 뒤집힌다).

## 동작 방식

### (1) 레이아웃 창 — 여섯 `img` 의 로드 전과 뒤

**언제 쓰나** — 「이미지가 뜨면서 글이 밀린다」·「`width`/`height` 를 적었는데 반응형에서 찌그러진다」를 가를 때.

폭 150px 칸 여섯 개에 **같은 300×150 그림**을 넣고 속성·CSS 만 바꿨다. 이미지는 **`h/` 경로라 서버가 붙잡는다** — 실행기가 `DOMContentLoaded` 뒤 두 틀을 기다려 **로드 전**을 재고, `/go` 로 풀어 준 뒤 `load` 를 기다려 **로드 뒤**를 잰다.

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

```text
$ python3 html33b-run.py 격자 html33b-34-shift.html
  서버    받음  h/p300x150.png?k=A
  서버    받음  h/p300x150.png?k=B
  서버    받음  h/p300x150.png?k=C
  서버    받음  h/p300x150.png?k=D
  서버    받음  h/p300x150.png?k=E
  서버    받음  h/p300x150.png?k=F
  서버    풀어 줌
  서버    표지  끝
img                                             aspect-ratio 계산값   로드 전 상자    로드 뒤 상자    아래 요소가 움직였나
A width + height                                "auto 300 / 150"      300×150         300×150         아니오 (155 → 155)
B width 만                                      "auto"                300×0           300×150         예 (24 → 155)
C 없음                                          "auto"                0×0             300×150         예 (24 → 155)
D width + height · CSS width:100%               "auto 300 / 150"      150×150         150×150         아니오 (155 → 155)
E width + height · CSS width:100%; height:auto  "auto 300 / 150"      150×75          150×75          아니오 (80 → 80)
F 없음 · CSS width:100%; height:auto            "auto"                150×0           150×75          예 (24 → 80)
로드 전 complete = false · false · false · false · false · false · 로드 뒤 = true · true · true · true · true · true
움직인 칸 = 3 / 6
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **속성이 둘 다 있으면 로드 전에 비율이 선다** — `aspect-ratio` 계산값이 **`"auto 300 / 150"`**(A · D · E). 하나뿐이면(B) 또는 없으면(C · F) **`"auto"`**. 명세 — 「두 속성이 **둘 다 있고** 차원 값으로 파싱되며 **퍼센트가 아니면** `aspect-ratio: auto w / h` 의 표현 힌트로 쓴다」.
- ★★★ **움직인 칸 3 / 6** — B(`300×0 → 300×150`) · C(`0×0 → 300×150`) · F(`150×0 → 150×75`). 셋 다 **로드 전 높이가 0** 이었다.
- ★★★ **D 는 안 움직였는데 찌그러졌다** — `150×150`. 속성은 `aspect-ratio` 로만 번역되는 게 아니라 **차원 속성 `width: 300px`·`height: 150px`** 로도 번역된다(명세 — 「map to the dimension properties」). CSS `width:100%` 가 **폭만** 덮으니 높이는 **속성의 150px 그대로**이고, 높이가 정해져 있으면 비율은 쓸 데가 없다. **E 처럼 `height:auto` 를 함께 줘야** 비율이 높이를 정한다(`150×75`).
- ★★ **A 는 칸(150px)을 넘쳤다** — `300×150`. 속성은 **최소 크기가 아니라 그냥 크기**다.
- ★ **로드 전 `complete` 는 여섯 다 `false`** — 「로드 전」을 잰 것이 맞다는 확인 칸이다.

```text
  width/height 속성이 CSS 로 번역되는 두 갈래 (명세 · 이 판)

  <img width=300 height=150>
     │
     ├─ 차원 속성 ──> width: 300px ; height: 150px     (표현 힌트 — 작성자 CSS 가 이긴다)
     │
     └─ 둘 다 있으면 ──> aspect-ratio: auto 300 / 150  (원래 비율이 오면 그것 · 오기 전엔 이 비율)

  작성자 CSS  width:100%              → 폭만 덮임 · 높이 150px 남음 → 150×150 (찌그러짐)
  작성자 CSS  width:100%; height:auto → 둘 다 덮임 · 비율이 높이를 정함 → 150×75
```

★ 이 번역의 **CSS 쪽 뜻**(`auto <ratio>` 가 「원래 비율이 있으면 그것, 없으면 이것」)은 [CSS 31번](../../../css/syntax/31-intrinsic-sizing-and-aspect-ratio/2-summary.md)이 정본이다. 그 편은 `img` 의 속성 번역을 **재지 않았다** — 이 편의 (1) 이 그 첫 측정이다.

### (2) 창 ⑤ — 네 `img` 의 요청 시점

**언제 쓰나** — 「첫 화면 사진에 `loading=lazy` 를 달았다」·「한참 아래 사진이 `load` 를 늦추나」를 가를 때.

화면 안(위)과 **10000px 아래**에 `eager`·`lazy` 를 하나씩 두었다. 페이지가 **`DOMContentLoaded`·`load` 때 표지를 서버에 보낸다** — 서버 로그의 **순서**가 곧 답이다. 이미지는 붙잡혀 있다가 실행기가 두 틀 뒤 `/go` 로 푼다. 마지막에 한참 아래 `lazy` 로 **스크롤**하고 그 `load` 를 기다린다.

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

```text
$ python3 html33b-run.py 격자 html33b-34-lazy.html
  서버    받음  h/p300x150.png?k=아래-eager
  서버    받음  h/p300x150.png?k=위-eager
  서버    표지  DOMContentLoaded
  서버    받음  h/p300x150.png?k=위-lazy
  서버    표지  두 틀 뒤
  서버    풀어 줌
  서버    표지  load
  서버    표지  스크롤 전
  서버    받음  h/p300x150.png?k=아래-lazy
  서버    표지  스크롤 뒤 아래-lazy load
  서버    표지  끝

img             DOMContentLoaded 전   load 전   스크롤 전   처음 우선순위 → 바뀐 우선순위
위-eager        예                    예        예          Medium → High
위-lazy         아니오                예        예          Low
아래-eager      예                    예        예          Medium
아래-lazy       아니오                아니오    아니오      Low
스크롤 전 complete = {"위e":true,"위l":true,"아래e":true,"아래l":false}
load 전에 요청이 간 칸 = 3 / 4
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **첫 화면의 `lazy` 는 `DOMContentLoaded` 뒤에 요청됐다** — `eager` 둘은 그 앞. 그리고 우선순위가 **`Low`** 로 나가 **끝까지 `Low`** 였다. 같은 자리의 `eager` 는 **`Medium → High`** — 한참 아래 `eager` 는 `Medium` 에서 안 올라갔으니 **화면 안이라서 올라간 것**으로 읽힌다(Chrome 의 동작 — 명세가 아니다).
- ★★★ **한참 아래의 `eager` 도 `DOMContentLoaded` 전에 요청됐다** — 안 보여도 받는다(우선순위 `Medium` 에서 안 올라갔다).
- ★★★ **한참 아래의 `lazy` 는 `load` 뒤, 스크롤 뒤에야 요청됐다** — **`load` 전에 요청이 간 칸 3 / 4.** 그래서 이 그림은 `load` 를 **기다리게 하지 않았다**([08번](../08-script-loading/2-summary.md)의 「`DOMContentLoaded` 는 이미지를 안 기다리고 `load` 는 그 뒤」에서 `load` 가 기다리는 것은 **요청된 이미지**뿐이었다).
- ★★ **「첫 화면 `lazy` 는 LCP 를 나쁘게 한다」는 이 판이 잰 것이 아니다** — 잰 것은 「**`eager` 보다 늦게 · `DOMContentLoaded` 뒤에 · 낮은 우선순위로 요청이 나갔다**」는 순서와 이름이다. 그것이 화면에 몇 ms 로 나타나는지는 **네트워크·캐시·서버에 달려** 이 판이 말할 수 없다.
- ★ **지연 로딩이 「화면에서 얼마나 가까우면」 요청하는지는 재지 않았다** — 10000px 은 **확실히 먼 자리**로 고른 것이다. 그 거리는 Chrome 이 정하는 값이고(명세 사본에 절이 없다) 이 판은 경계를 찾지 않았다.

```text
  서버 로그의 순서 (이 판 · 세 판 같음)

  위-eager 요청 ─┐
  아래-eager 요청 ┘  ← 파서가 img 를 만나는 대로
  ── DOMContentLoaded ──
  위-lazy 요청       ← 레이아웃이 「화면 안」을 알려 준 뒤
  ── (두 틀) ── 풀어 줌 ──
  ── load ──        ← 요청된 세 장이 다 온 뒤
  ── 스크롤 ──
  아래-lazy 요청     ← 화면 가까이 온 뒤에야
```

### (3) 창 ⑦ + 레이아웃 창 — `alt` 셋 × 파일 있음/없음

**언제 쓰나** — 「장식 이미지에 `alt` 를 뭐라고 쓰나」·「`alt` 를 빼먹으면 스크린 리더가 무엇을 읽나」·「깨진 이미지가 자리를 얼마나 먹나」를 가를 때.

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

```javascript
// html33b-34-alt-spec.js
// 명세 열 — 칸마다 [허용되는 값…]
// 역할: HTML-AAM — img 는 image(ARIA 1.3 의 이름 · 옛 이름 img) · alt 가 공백뿐이면 none 또는 presentation
// 이름: HTML-AAM 「img 의 이름 계산」 — alt 를 쓴다(비어 있어도) · alt 가 없으면 title · 그것도 없으면 figcaption 조건 · 그 밖에는 이름 없음
// 그려진 것: Rendering 「Images」 — 그림이면 그림 · 그림이 아니고 alt 가 없으면 아이콘(글자 없이) · 글자를 나타내면 그 글자 · 아무것도 안 나타내면 0×0
const 명세 = {
  a1: { 역할: ["image", "img"], 이름: [""], 그림: ["그림"] },
  a2: { 역할: ["none", "presentation"], 이름: [""], 그림: ["그림"] },
  a3: { 역할: ["image", "img"], 이름: ["파란 사각형"], 그림: ["그림"] },
  b1: { 역할: ["image", "img"], 이름: [""], 그림: ["아이콘"] },
  b2: { 역할: ["none", "presentation"], 이름: [""], 그림: ["0×0"] },
  b3: { 역할: ["image", "img"], 이름: ["파란 사각형"], 그림: ["글자"] },
};
```

```text
$ python3 html33b-form.py page html33b-34-alt.html
img                                 상자        그려진 것 역할    이름            무시   naturalWidth
a1 파일 있음 · alt 없음             300×150     그림      image   ""              false  300
a2 파일 있음 · alt=""               300×150     그림      none    ""              true   300
a3 파일 있음 · alt="파란 사각형"    300×150     그림      image   "파란 사각형"   false  300
b1 파일 없음(404) · alt 없음        16×16       아이콘    image   ""              false  0
b2 파일 없음(404) · alt=""          0×0         0×0       none    ""              true   0
b3 파일 없음(404) · alt="파란 사각형" 94.09375×24 글자      image   "파란 사각형"   false  0
(그려진 것 = naturalWidth 가 있으면 그림 · 0×0 · alt 글자가 있으면 글자 · 나머지는 아이콘)
명세 열과 갈린 칸 = 0 / 18
(exit 0)
```

- ★★★ **명세 열과 갈린 칸 0 / 18.**
- ★★★ **`alt=""` 는 역할 `none` · 트리에서 무시(`무시 true`)** — 파일이 있어도 없어도 같다. HTML-AAM — 「`alt` 가 공백뿐이면 **`none` 또는 `presentation`**」. **「이 그림은 장식이다」의 표시**다.
- ★★★ **`alt` 가 없으면 역할은 `image` 인데 이름이 `""`** — Chrome 의 트리는 **파일 이름을 이름으로 쓰지 않았다.** HTML-AAM 의 이름 계산 — `alt` → `title` → figcaption 조건 → 「그 밖에는 **이름이 없다**」. ★ 「스크린 리더가 파일 이름을 읽는다」는 말이 있다면 그것은 **보조 기술 쪽의 선택**이고 이 판은 **못 잰다**(트리까지만 본다).
- ★★ **깨졌을 때 자리** — `alt` 없음 **16×16**(아이콘 자리로 읽힌다 — 픽셀은 안 봤다) · `alt=""` **0×0** · `alt="파란 사각형"` **글자 상자 94×24**. 명세의 렌더링 절 — 「`alt` 가 없으면 … 아이콘」 · 「**아무것도 안 나타내면 자연 크기 0**」 · 「글자를 나타내면 **그 글자를 가진 구절 요소**로」.
- ★ **`complete` 는 깨진 셋도 `true`** — `complete` 는 「다 받았나」가 아니라 「**더 할 일이 없나**」다. 깨짐은 **`naturalWidth === 0`** 으로 가른다.

### (4) 창 ⑤ + CDP 우선순위 — `fetchpriority`·`decoding` 여섯

**언제 쓰나** — 「`fetchpriority=high` 를 달면 먼저 받나」·「`decoding=async` 가 요청에 무엇을 하나」를 가를 때.

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

```text
$ python3 html33b-run.py 격자 html33b-34-prio.html
img                                 처음 우선순위 → 바뀐 우선순위
r1 (속성 없음)                      Medium → High
r2 fetchpriority=high               High
r3 fetchpriority=low                Low
r4 decoding=async                   Medium → High
r5 decoding=sync                    Medium → High
r6 fetchpriority=high · 한참 아래   High
풀어 주기 전에 서버가 받은 이미지 = 6 / 6  (★ 받은 순서는 판마다 흔들린다 — 따로 센다)
뒤늦게 온 요청 = 0
(exit 0)
```

붙잡힌 여섯 요청이 **서버에 닿는 순서**를 20 판 돌려 셌다.

```text
$ python3 html33b-tally.py 20
  6 판  r2 r1 r6 r4 r5 r3
  5 판  r2 r6 r1 r4 r5 r3
  4 판  r2 r1 r4 r6 r5 r3
  2 판  r1 r2 r4 r6 r5 r3
  1 판  r1 r2 r6 r4 r5 r3
  1 판  r1 r4 r2 r6 r3 r5
  1 판  r6 r2 r1 r4 r5 r3
판 = 20 · 순서의 가짓수 = 7
r3(fetchpriority=low)이 마지막인 판 = 19 / 20
r2(fetchpriority=high)가 r1(속성 없음)보다 먼저인 판 = 16 / 20
(exit 0)
```

- ★★★ **`fetchpriority=high` 는 처음부터 `High`, `low` 는 `Low` 에 머물렀다** — 속성이 없는 화면 안 그림은 **`Medium → High`**(나중에 올라감), 한참 아래의 `high` 는 **처음부터 `High`**(화면 밖이어도).
- ★★★ **`decoding` 은 요청에 흔적이 없다** — `async`·`sync` 둘 다 속성 없는 것과 **같은 `Medium → High`**. `decoding` 은 **받은 뒤 그림을 푸는 때**의 힌트라 요청 창에는 **잴 것이 없다**(18-B — 「부적용」). 푸는 때 자체는 이 판이 **못 쟀다.**
- ★★★ **서버에 닿는 순서는 흔들린다** — 20 판에 **여러 가지**가 나왔다. 그래도 `low`(`r3`)는 **거의 늘 마지막**이었고 `high`(`r2`)는 **대부분 속성 없는 것(`r1`)보다 먼저**였다 — ★ **「늘」이 아니다**(블록의 판 수를 보라). 이 판 수는 재대조에서도 흔들리는 칸이다.
- ★ **「`fetchpriority=high` 가 빨리 받는다」는 이 판의 결론이 아니다** — 잰 것은 **우선순위 이름**과 **순서의 경향**이다. 시간은 안 쟀다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 자리 예약 | `<img width="300" height="150" …>` | 로드 전 `300×150` · `aspect-ratio: auto 300 / 150` |
| 반응형 + 자리 예약 | 속성 둘 + CSS `width:100%; height:auto` | 비율대로(`150×75`) — **`height:auto` 를 빼면 찌그러진다** |
| 늦게 받기 | `loading="lazy"` | 첫 화면이면 `DOMContentLoaded` 뒤 · `Low` |
| 장식 | `alt=""` | `none` · 트리에서 무시 |
| 먼저 받기 힌트 | `fetchpriority="high"` | 처음 우선순위 `High` |

### 어디서 헷갈리나

- **속성은 「비율」만이 아니라 「크기」도 준다** — CSS 로 폭만 바꾸면 높이는 속성값에 남는다.
- **`alt` 없음과 `alt=""` 는 정반대다** — 없음은 「이름 없는 그림」, 빈 문자열은 「그림이 아님(장식)」.
- **`complete === true` 는 성공이 아니다** — 깨져도 `true` 다.
- **`decoding` 은 요청 순서를 바꾸지 않는다** — 받은 뒤의 이야기다.

## 어디서 틀리나

### 1. 반응형이라며 `width`/`height` 속성을 지운다

**로드 전 높이가 0** 이 되어 아래가 밀린다((1) B · C · F). 속성은 두고 CSS 로 `width:100%; height:auto`.

### 2. 속성 둘 + `width:100%` 만 준다

**찌그러진다**((1) D — `150×150`). `height:auto` 를 함께.

### 3. 첫 화면의 큰 그림에 `loading=lazy` 를 단다

**요청이 `DOMContentLoaded` 뒤로 · `Low` 로** 밀린다((2)). 첫 화면 그림은 `lazy` 를 빼고, 필요하면 `fetchpriority=high`((4)).

### 4. 장식 그림에서 `alt` 를 빼 버린다

「**이름 없는 그림**」이 트리에 남는다((3) `a1`). 장식이면 **`alt=""`**.

### 5. `complete` 로 로드 성공을 판정한다

깨진 것도 `true` 다((3)). **`naturalWidth`** 를 본다.

### 6. `fetchpriority` 로 받는 순서를 「보장」했다고 여긴다

**순서는 판마다 흔들린다**((4) — 20 판의 가짓수). 힌트다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML · Rendering)** | `width`/`height` → 차원 속성 **그리고** (둘 다 · 퍼센트 아님이면) `aspect-ratio: auto w / h` — 둘 다 **표현 힌트**(작성자 CSS 가 이긴다) | (1) |
| **명세(HTML · Rendering)** | 그림이 없을 때 — `alt` 없음은 아이콘 · 글자는 글자 · 아무것도 안 나타내면 크기 0 | (3) |
| **명세(HTML-AAM)** | `alt=""` → `none`/`presentation` · 이름 = `alt` → `title` → figcaption → **없음** | (3) |
| **명세 — 판정 보류** | `img` 요소 절 · 지연 로딩 절 · `fetchpriority` 절 · `decoding` — **이 배치의 사본에 없다** | (2)·(4) |
| **구현(Chrome)** | 첫 화면 `lazy` 를 레이아웃 뒤에 요청 · `Low` 로 · 우선순위 이름(`Low`/`Medium`/`High`)과 화면 안 **승격** · 깨진 `alt` 없음 그림의 **16×16** | (2)·(3)·(4) |
| **이 판의 관찰** | 움직인 칸 **3 / 6** · `load` 전 요청 **3 / 4** · 명세 열과 갈린 칸 **0 / 18** · 서버 순서 20 판에 여러 가지 | (1)\~(4) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **LCP·로드 시간** | 시간을 안 쟀다 — 네트워크·캐시·서버에 달린 값이라 이 판의 한 수치는 근거가 안 된다(규칙 24) |
| ★★ **`decoding` 이 푸는 때** | 요청 창에 흔적이 없다 · 디코드 타이밍은 이 판의 창에 안 잡힌다 |
| ★★ **스크린 리더가 `alt` 없는 그림에서 무엇을 읽나** | 트리까지만 본다 — 파일 이름을 읽는 것은 **보조 기술의 선택**이다 |
| **지연 로딩의 거리 문턱** | Chrome 이 정하는 값 · 이 판은 경계를 찾지 않았다 |

## 언제 쓰고 언제 안 쓰나

- **`width`/`height`** — **언제나.** 반응형이면 CSS 에 `width:100%`(또는 `max-width:100%`)와 **`height:auto`** 를 함께.
- **`loading="lazy"`** — **첫 화면 밖**의 그림에. 첫 화면·히어로 그림에는 쓰지 않는다((2)).
- **`fetchpriority="high"`** — 첫 화면의 **가장 중요한 그림 하나**에. 여러 장에 뿌리면 힌트의 뜻이 사라진다(해석이다 — 이 판은 여러 장의 경쟁을 재지 않았다).
- **`alt`** — 정보가 있는 그림은 **그 정보**를, 장식은 **`alt=""`** 를. **빼먹지 않는다.**
- **`decoding`** — 요청에는 아무 일도 안 한다. 필요를 모르면 적지 않는다.

## 핵심 문장

1. **`width`/`height` 속성은 크기와 비율 두 가지로 번역된다 — 둘 다 있으면 로드 전에 `aspect-ratio: auto w / h` 로 자리를 잡아 아래가 밀리지 않는다.**
2. **반응형으로 폭을 바꿀 때는 `height:auto` 를 함께 줘야 비율이 높이를 정한다 — 안 주면 속성의 높이가 남아 찌그러진다.**
3. **`loading=lazy` 는 첫 화면 그림의 요청을 `DOMContentLoaded` 뒤로, 낮은 우선순위로 민다 — 한참 아래 그림은 스크롤 전까지 요청조차 안 해 `load` 를 기다리게 하지 않는다.**
4. **`alt=""` 는 「장식」이라 트리에서 빠지고, `alt` 가 없으면 이름 없는 그림이 남는다 — Chrome 의 트리는 파일 이름을 이름으로 쓰지 않았다.**
5. **`fetchpriority` 는 요청의 우선순위 이름을 바꾸고, `decoding` 은 요청에 흔적이 없다 — 서버에 닿는 순서는 판마다 흔들린다.**

## 관련 자료

- [05번 주제](../05-content-categories-and-models/2-summary.md) — `img` 의 콘텐츠 카테고리(흐름·구절·임베디드).
- [08번 주제](../08-script-loading/2-summary.md) — `DOMContentLoaded` 와 `load` · 창 ⑤ 의 처음.
- [33번 주제](../33-output-progress-meter/3-answer.md) — 이 묶음의 실행기·이미지 생성기 전문.
- [CSS 31번](../../../css/syntax/31-intrinsic-sizing-and-aspect-ratio/2-summary.md) — `aspect-ratio` 의 `auto <ratio>` 뜻 — 경계: **그쪽은 속성 자체, 여기는 `img` 의 HTML 속성이 그것으로 번역되는 자리.**
- [CSS 44번](../../../css/syntax/44-backgrounds-and-object-fit/2-summary.md) — `object-fit` — 경계: **(1) D 의 찌그러짐을 「자르기」로 바꾸는 것은 그쪽.**
- [35번 주제](../35-srcset-and-sizes/2-summary.md)(`srcset`/`sizes`) · [web-api 35번](../../../../web-api/35-intersection-observer/2-summary.md)(`IntersectionObserver` — 스크립트로 직접 지연 로딩).

## 용어 풀이

- **표현 힌트(presentational hint)** — HTML 속성이 CSS 선언처럼 쓰이는 것. 작성자 CSS 보다 **약하다.**
- **차원 속성(dimension property)** — `width`·`height` 같은 크기 속성. `img` 의 속성이 그리로 번역된다.
- **레이아웃 시프트** — 늦게 온 내용이 이미 그려진 요소를 밀어내는 것.
- **지연 로딩(lazy loading)** — 화면 가까이 올 때까지 요청을 미루는 것.
- **처음 우선순위(`initialPriority`)** — CDP 가 알려 주는, 요청이 나갈 때의 우선순위 이름.
- **`complete`** — 이미지가 더 할 일이 없는가. 깨져도 참이다.

## 더 들어가면

- **`loading=lazy` 와 스크립트** — 지연 로딩은 스크립트가 꺼진 문서에서 달라진다는 설명이 흔하다. 이 판은 **스크립트를 끈 판을 던지지 않았고** 명세 절도 사본에 없다.
- **`fetchpriority` 가 `link rel=preload`·`fetch()` 에도 있다** — 같은 이름의 힌트다. 이 판은 `img` 만 쟀다.
- **`object-fit: cover` 로 D 를 고치기** — 찌그러짐 대신 잘라 채운다([CSS 44번](../../../css/syntax/44-backgrounds-and-object-fit/2-summary.md)). 자리 예약은 그대로다.
