# web-api/36 — `ResizeObserver`: 관측 상자 세 종류와 무한 루프 경고 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「디스패치 계수기」([24번 주제](../24-document-lifecycle-events/2-summary.md)의 창 ④)를 변화마다 돌린 「상자 격자」다** — 관측 상자(`content-box` · `border-box` · `device-pixel-content-box`) × 변화 일곱(`width` · `padding` · `border` · `transform: scale` · 부모 폭 · 뷰포트 폭 · `devicePixelRatio`) = **21칸**마다 **콜백이 불렸나 · 받은 크기**를 적고, 같은 변화에서 **`window` 의 `resize` 이벤트 수**를 옆줄에 센다. 스크립트가 **「콜백이 불린 칸 N / M」** 을 마지막 줄로 찍는다.\
> **기준 소스** — ① [W3C Resize Observer](https://www.w3.org/TR/resize-observer/) — **받은 사본은 2020-02-11 First Public Working Draft** 다(「Latest published version」이 그 판이다). §3.1 `ResizeObservation`(`lastReportedSizes` 를 `[(0,0)]` 으로 시작) · §3.4.6 「Deliver Resize Loop Error」(메시지 문자열) · §3.6.1 깊이로 루프를 끊는 단계. ② [HTML — update the rendering](https://html.spec.whatwg.org/multipage/webappapis.html#update-the-rendering) — 지금은 **HTML 쪽이** 「Gather active resize observations at depth」 · 「deliver resize loop error」를 렌더링 단계 안에 직접 적는다. ③ HTML 「report an exception」 — 콘솔은 「**may** report exception to a developer console」. 받아서 읽은 것만 적었다(기준일 2026-09-26). ★ **편집자 초안(drafts.csswg.org)은 받지 않았다** — 이번 배치가 받기로 한 곳(WHATWG · w3c.github.io · wicg.github.io · W3C TR)에 없다. 그래서 **(3)의 이탈은 「2020 WD 사본과 다르다」까지만 말한다.**\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless(`--window-size=1000,800`)에서 받은 것이다. 하네스는 [32번 주제](../32-server-sent-events/2-summary.md)가 빌려 쓴 24편의 `wa24b-net.py` 에 **「페이지가 CDP 일을 부탁하는 창구」** 하나를 더한 `wa36b-net.py` 다(전문은 [3-answer.md](3-answer.md)의 `## 실행 검증`). 뷰포트 폭과 `devicePixelRatio` 는 그 창구로 **CDP `Emulation.setDeviceMetricsOverride`** 를 불러 바꿨다. `--virtual-time-budget` 은 쓰지 않았다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★ **[09번 주제](../09-element-geometry/2-summary.md)** — 세 계열(`offset*`·`client*`·`getBoundingClientRect`)이 **테두리 · 스크롤바 · `transform`** 을 각각 포함하나. 여기서는 그것을 **읽는** 대신 **바뀌면 알려 달라고** 한다. 그리고 (9)의 「`transform` 은 한쪽에만 섞인다」가 여기 격자의 `transform` 열로 다시 나온다.\
> **경계** — ★★★ **「RO 가 `resize` 이벤트보다 싸다」는 이 편이 주장하지 않는다 — 재지 않았다**(가이드 규칙 4). 센 것은 **불렸나 · 몇 번**이다. ★ 렌더링 단계 안에서 RO 가 **어디에 끼나**는 [38번 주제](../38-request-animation-frame/2-summary.md)의 (1)이 Tracing 으로 잰다 — 여기서는 루프 경고에 필요한 만큼만 쓴다.\
> 이 본문은 Claude 작성이다(원고 없음). 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 상자 격자 21칸 · `resize` 수 · `devicePixelRatio` 줄 · 배율 2 대조 판 · 첫 통지 여덟 칸 · 루프 세 판의 틀별 묶음 · 오류 문구 · 콘솔 두 창 | 캡처 세 판이 **한 글자도 같았다** |
| ★ **판에 매일 수 있는 칸** | `device-pixel-content-box` 의 값 | 브라우저의 **실제 배율**(`--force-device-scale-factor`)에 매인다 — (2) |
| **흔들린다** | Chrome 판 번호 · 포트 | 포트는 출력에서 `<A>` 로 가렸다 |

- 재대조에서 정규화하는 칸은 **없다.** 위 표에 없는 차이는 전부 고칠 것이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | 트리는 안 바뀐다 — 바뀌는 것은 상자의 크기다 |
| 창 ② 노드 프로브 | ★ **쓴다** | `ResizeObserverEntry` 의 `contentBoxSize` · `borderBoxSize` · `devicePixelContentBoxSize` · `ErrorEvent` 의 칸들 |
| 창 ③ 같은 것을 두 번 읽기 | ★ **쓴다** | 같은 요소를 **상자 셋**으로 · 같은 격자를 **배율 1 과 배율 2** 두 브라우저로 · 같은 대상을 **RO 와 IO** 로 |
| **창 ④ 디스패치 계수기 → 상자 격자** | ★★★ **본체** | 변화마다 콜백이 **불렸나 · 무엇을 들고** · 틀마다 **몇 번 · 오류가 몇 번** |
| ★★ **`devicePixelRatio` 에뮬레이션** | ★★ **제5의 상태 — 기준만 다른 것** | CDP 로 `devicePixelRatio` 를 2 로 바꾸니 **값은 2 가 됐는데 장치 픽셀 상자는 안 움직였다.** 그래서 같은 질문을 **다른 창**(브라우저를 처음부터 배율 2 로 띄우기)으로 물었다 — (2). ★ 바꾼 창이 못 보는 것 — **한 문서가 사는 동안 배율이 바뀌는 순간**(창을 다른 모니터로 옮기기 · 확대) |
| 콘솔(Log · `Runtime.exceptionThrown`) | ★ **쓴다 — 침묵이 결론** | 루프 오류가 콘솔로도 가나 — **물은 곳 둘, 루프 오류에 답한 곳 0**. 대조로 던진 보통 예외는 받았다 — (4) |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **비용 — 시간 · 메인 스레드 점유** | **재지 않았다**(머리말) |
| ★★ **편집자 초안의 알고리즘** | 받지 않았다(머리말) — (3)의 판정이 거기서 멈춘다 |
| **살아 있는 문서에서 실제 배율이 바뀌는 순간** | 헤드리스에 모니터가 없다 — 배율은 띄울 때 정했다 |
| **SVG 요소 · `display: contents` · 인라인 요소** | 던지지 않았다 — 받은 사본은 SVG 를 「bounding box」로 따로 잰다고 적는다 |

## 한눈에 — 쉽게 말하면

**★ `ResizeObserver` 는 「옷 치수를 재 주는 재단사에게 맡긴 쪽지」다. 「이 사람 치수가 바뀌면 알려 줘요」라고 적되, 치수를 어디서 재는지(`content-box` = 몸통만 · `border-box` = 겉옷까지 · `device-pixel-content-box` = 몸통을 화면 점 단위로)를 고른다. 겉옷만 두꺼워지면 몸통 쪽지는 조용하다. 거울에 비친 모습이 두 배로 커져도(`transform`) 재단사는 실제 치수가 안 바뀌었으니 아무 말도 안 한다. 방(창)의 크기가 바뀌었다는 방송(`resize` 이벤트)은 방이 바뀔 때만 나오고, 옆 사람이 자리를 좁혀 내 옷이 줄어든 것은 재단사만 안다.**

| 비유 | 실체 |
|---|---|
| 어디서 재나 | `observe(요소, { box })` — `content-box`(기본) · `border-box` · `device-pixel-content-box` |
| 거울에 비친 크기 | `transform` — 레이아웃 크기를 안 바꾼다 → 통지 없음 |
| 방 크기 방송 | `window` 의 `resize` 이벤트 — 뷰포트가 바뀔 때만 |
| 옆 사람이 자리를 좁힘 | 부모 폭이 줄어 요소가 줄어듦 — `resize` 는 조용하고 RO 만 안다 |
| 치수를 재자마자 옷을 고침 | 콜백 안에서 관측 대상 크기를 바꿈 → 같은 틀에서는 **더 깊은 요소만** 다시 알린다 |

```text
   변화 일곱 × 상자 셋 (이 판 · box-sizing: content-box · 100×50 · padding 10 · border 5)

                      content  border  device-px   window resize
   width 100→120        ○        ○        ○            0
   padding 10→20        —        ○        —            0
   border 5→8           —        ○        —            0
   transform scale(2)   —        —        —            0     ← 레이아웃 크기가 그대로
   부모 폭 200→160      ○        ○        ○            0     ← 창 크기 이벤트로는 안 잡힌다
   뷰포트 폭 1000→800   ○        ○        ○            1     ← 요소가 10vw 일 때
   devicePixelRatio 1→2 —        —        —            0     ★ 에뮬레이션은 장치 픽셀을 안 바꿨다 — (2)
```

## 이 주제가 답하려는 질문

1. **무엇이 바뀌면 콜백이 오나** — 상자 셋 × 변화 일곱. `resize` 이벤트와는 어디서 갈리나.
2. **처음 `observe` 하면 오나** — 크기가 0 인 요소 · 안 그려진 요소 · 문서 밖 요소는.
3. **콜백 안에서 크기를 바꾸면** — 한 틀에 몇 번 도나 · 루프 경고는 어디로 · 무엇이라고 오나.

## 동작 방식

### (1) ★★★ 본체 — 상자 격자

**변화마다 새 요소를 만들고** 상자마다 관찰자 하나(모두 셋)로 관찰을 시작한다. **첫 통지가 지나간 뒤** 변화를 하나 주고 틀 세 장을 기다린다.

```html
<!-- wa36b-36-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>36 grid</title>
<style>
  body { margin: 0; }
  .p { width: 200px; margin: 10px; }
  .t { width: 100px; height: 50px; padding: 10px; border: 5px solid #789; box-sizing: content-box; background: #cde; }
  .p.half .t { width: 50%; }
  .p.vw .t { width: 10vw; }
</style>
<script>
// 상자 격자 — 관측 상자(box 옵션) 셋 × 크기에 닿을 법한 변화 일곱(뷰포트와 devicePixelRatio 는 하네스가 CDP 로 바꾼다)
// 변화마다 새 요소를 만들고 관찰자 셋(상자마다 하나)으로 관찰을 시작한 뒤, 첫 통지가 지나가면 변화를 하나 준다
// 한 칸 = 그 변화 뒤에 그 관찰자가 받은 크기(inlineSize×blockSize) · 안 불렸으면 —
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
const 상자들 = ["content-box", "border-box", "device-pixel-content-box"];
const 칸이름 = { "content-box": "contentBoxSize", "border-box": "borderBoxSize", "device-pixel-content-box": "devicePixelContentBoxSize" };
const 변화들 = [
  ["width 100→120", async (t, p) => { t.style.width = "120px"; }],
  ["padding 10→20", async (t, p) => { t.style.padding = "20px"; }],
  ["border 5→8", async (t, p) => { t.style.borderWidth = "8px"; }],
  ["transform scale(2)", async (t, p) => { t.style.transform = "scale(2)"; }],
  ["부모 폭 200→160", async (t, p) => { p.style.width = "160px"; }],
  ["뷰포트 폭 1000→800", async (t, p) => { await __부탁("폭", { w: 800, h: 800 }); }],
  ["devicePixelRatio 1→2", async (t, p) => { await __부탁("dpr", { 값: 2 }); }],
];
let 창크기 = 0;
addEventListener("resize", () => 창크기++);
window.__끝 = async () => {
  const 줄 = [["box", ...변화들.map(x => x[0])].join("\t")];
  const 표 = Object.fromEntries(상자들.map(b => [b, []]));
  const 창줄 = ["window resize 이벤트 수"], 배율줄 = ["변화 뒤 devicePixelRatio"];
  let 불림 = 0, 칸수 = 0;
  for (const [이름, 바꾸기] of 변화들) {
    const p = document.createElement("div"), t = document.createElement("div");
    p.className = 이름.startsWith("부모") ? "p half" : 이름.startsWith("뷰포트") ? "p vw" : "p"; t.className = "t";
    p.append(t); document.body.append(p);
    const 받음 = {}, ros = [];
    for (const b of 상자들) {
      받음[b] = [];
      const ro = new ResizeObserver(es => { for (const e of es) { const s = e[칸이름[b]][0]; 받음[b].push(`${s.inlineSize}×${s.blockSize}`); } });
      ro.observe(t, { box: b }); ros.push(ro);
    }
    await 틀(); await 틀();
    for (const b of 상자들) 받음[b] = [];
    창크기 = 0;
    await 바꾸기(t, p);
    await 틀(); await 틀(); await 틀();
    for (const b of 상자들) { 칸수++; if (받음[b].length) 불림++; 표[b].push(받음[b].length ? "○ " + 받음[b].join(" · ") : "—"); }
    창줄.push(String(창크기)); 배율줄.push(String(devicePixelRatio));
    for (const ro of ros) ro.disconnect();
    p.remove();
    if (/^(뷰포트|device)/.test(이름)) { await __부탁("원래대로"); await 틀(); await 틀(); }
  }
  for (const b of 상자들) { if (표[b].length !== 변화들.length) throw new Error("칸 수"); 줄.push([b, ...표[b]].join("\t")); }
  줄.push(창줄.join("\t")); 줄.push(배율줄.join("\t"));
  줄.push(`콜백이 불린 칸 = ${불림} / ${칸수}`);
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-36-grid.html
box	width 100→120	padding 10→20	border 5→8	transform scale(2)	부모 폭 200→160	뷰포트 폭 1000→800	devicePixelRatio 1→2
content-box	○ 120×50	—	—	—	○ 80×50	○ 80×50	—
border-box	○ 150×80	○ 150×100	○ 136×86	—	○ 110×80	○ 110×80	—
device-pixel-content-box	○ 120×50	—	—	—	○ 80×50	○ 80×50	—
window resize 이벤트 수	0	0	0	0	0	1	0
변화 뒤 devicePixelRatio	1	1	1	1	1	1	2
콜백이 불린 칸 = 11 / 21
(exit 0)
```

- ★★★ **콜백이 불린 칸 11 / 21.** 나머지 10칸은 **크기에 닿을 것 같은 변화인데도** 조용했다.
- ★★★ **`transform: scale(2)` 열은 세 상자 전부 `—`** — 화면에서는 두 배로 보이지만 **레이아웃 크기는 그대로**다. [09번 주제](../09-element-geometry/2-summary.md) (9)에서 `offsetWidth` 는 `transform` 을 안 보고 `getBoundingClientRect()` 만 봤다 — **RO 는 앞쪽(레이아웃 크기)을 본다.**
- ★★ **`padding` · `border` 열은 `border-box` 만 `○`** — `box-sizing: content-box` 라 **내용 상자는 그대로**다. 크기가 바뀌었는지는 **고른 상자에서만** 판정된다. 받은 크기도 상자마다 다르다(`width 100→120` 에서 `120×50` · `150×80` · `120×50`).
- ★★★ **`부모 폭 200→160` 은 세 상자 다 `○` 인데 `resize` 이벤트는 0.** 요소는 부모의 50% 라 100 → 80 으로 줄었다. **창 크기 이벤트로는 원리상 안 잡히는 변화**다.
- ★★ **`뷰포트 폭 1000→800` 만 `resize` 가 1** — 요소가 `10vw` 라 RO 도 같이 불렸다. **`resize` 는 뷰포트의 일**이고 요소 크기와는 **따로 논다.**
- ★★ **`devicePixelRatio 1→2` 는 세 상자 다 `—`** — 그런데 **`변화 뒤 devicePixelRatio` 줄은 `2`** 다. 값은 바뀌었다. 이것이 (2)다.

### (2) ★★ 제5의 상태 — `devicePixelRatio` 는 2 가 됐는데 장치 픽셀 상자는 그대로

CDP 에뮬레이션으로 배율을 바꾸는 대신 **브라우저를 처음부터 배율 2 로 띄워**(`--force-device-scale-factor=2`) **같은 격자**를 던졌다. 줄은 머리 · 장치 픽셀 상자 · `devicePixelRatio` 만 잘랐다.

```text
$ WA36B_DSF=2 python3 wa36b-net.py page wa36b-36-grid.html | sed -n '1p;4p;6p;8p'
box	width 100→120	padding 10→20	border 5→8	transform scale(2)	부모 폭 200→160	뷰포트 폭 1000→800	devicePixelRatio 1→2
device-pixel-content-box	○ 240×100	—	—	—	○ 160×100	○ 160×100	—
변화 뒤 devicePixelRatio	2	2	2	2	2	1	2
(exit 0)
```

- ★★★ **배율 2 로 띄운 판에서는 `device-pixel-content-box` 가 `240×100`**(CSS 픽셀 120×50 의 두 배)이다. **배율 1 판은 `120×50`** 이었다((1)). 상자는 **실제 화면 배율**을 따른다.
- ★★★ **그런데 두 판 모두 `devicePixelRatio 1→2` 열은 `—`** 이고, 배율 2 판의 `뷰포트 폭` 열 아래 `devicePixelRatio` 는 **`1`** 이다(뷰포트 에뮬레이션이 배율을 1 로 덮었다) — **그 칸의 장치 픽셀 상자는 여전히 `160×100`**(두 배)이다.
- ★★ **CDP 의 `devicePixelRatio` 에뮬레이션은 스크립트가 읽는 값만 바꾸고 장치 픽셀 격자는 안 바꿨다.** 에러도 경고도 없다 — 값(`devicePixelRatio = 2`)도 그럴듯하다. **틀린 것은 값이 아니라 그 값이 무엇을 기준으로 한 것이냐**다(가이드 규칙 3 의 제5의 상태).
- ★ 그래서 이 편은 「RO 는 배율 변화를 못 잡는다」고 **적지 않는다** — 잰 것은 「**에뮬레이션한 배율 변화는** 장치 픽셀 상자를 안 움직였다」이다. 살아 있는 문서에서 실제 배율이 바뀌는 순간은 **못 쟀다**(머리말).

```text
   같은 요소 · 같은 격자 — 브라우저 둘 (이 판)

                               배율 1 로 띄움         배율 2 로 띄움
   width 100→120 의 device-px   120×50                 240×100      ← 실제 배율을 따른다
   CDP 로 devicePixelRatio=2    —  (값은 2)            —  (값은 2)   ← 격자는 안 바뀌었다
   ★ 「값이 바뀌었다」와 「기준이 바뀌었다」는 다른 사건이다
```

### (3) ★★ 첫 통지 — 크기가 0 이어도 왔다

관찰을 시작하기만 하고 **아무것도 안 바꾼다.** 같은 대상에 [35번 주제](../35-intersection-observer/2-summary.md)의 IO 도 같이 건다.

```html
<!-- wa36b-36-first.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>36 first</title>
<style> body { margin: 0; } .t { width: 100px; height: 50px; background: #cde; } </style>
<script>
// 관찰을 시작하기만 하고 아무것도 안 바꾼다 — 대상 넷에 ResizeObserver 와 IntersectionObserver 를 같이 건다
// 한 칸 = 틀 세 장 동안 받은 첫 통지(ResizeObserver 는 contentRect 의 폭×높이 · IntersectionObserver 는 isIntersecting)
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
const 대상들 = [
  ["보이는 100×50", () => { const d = document.createElement("div"); d.className = "t"; document.body.append(d); return d; }],
  ["width 0 · height 0", () => { const d = document.createElement("div"); d.style.cssText = "width:0;height:0"; document.body.append(d); return d; }],
  ["display: none", () => { const d = document.createElement("div"); d.className = "t"; d.style.display = "none"; document.body.append(d); return d; }],
  ["문서에 안 붙인 요소", () => { const d = document.createElement("div"); d.className = "t"; return d; }],
];
window.__끝 = async () => {
  const 줄 = [["관찰 대상", "ResizeObserver 첫 통지", "IntersectionObserver 첫 통지"].join("\t")];
  for (const [이름, 만들기] of 대상들) {
    const t = 만들기(), ro받음 = [], io받음 = [];
    const ro = new ResizeObserver(es => { for (const e of es) ro받음.push(`○ ${e.contentRect.width}×${e.contentRect.height}`); });
    const io = new IntersectionObserver(es => { for (const e of es) io받음.push(`○ isIntersecting=${e.isIntersecting}`); });
    ro.observe(t); io.observe(t);
    await 틀(); await 틀(); await 틀();
    줄.push([이름, ro받음.join(" · ") || "—", io받음.join(" · ") || "—"].join("\t"));
    ro.disconnect(); io.disconnect(); t.remove();
  }
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-36-first.html
관찰 대상	ResizeObserver 첫 통지	IntersectionObserver 첫 통지
보이는 100×50	○ 100×50	○ isIntersecting=true
width 0 · height 0	○ 0×0	○ isIntersecting=true
display: none	○ 0×0	○ isIntersecting=false
문서에 안 붙인 요소	○ 0×0	○ isIntersecting=false
(exit 0)
```

- ★★★ **네 대상 전부 RO 첫 통지가 왔다** — 크기 `0×0` 인 셋(폭·높이 0 · `display: none` · 문서에 안 붙인 요소)까지. IO 도 넷 다 왔다(35편 (1)의 「관찰 시작 한 번」과 같은 모양).
- ★★ **받은 사본(2020 WD)과 다르다.** §3.1 은 `ResizeObservation` 을 만들 때 `lastReportedSizes` 를 **`[(0,0)]`** 으로 두고, `isActive()` 는 「지금 크기가 **그것과 다르면** 참」이다. 그대로 읽으면 **0×0 인 대상은 첫 통지가 없어야 한다.** Chrome 151 은 보냈다.
- ★ **이것을 「Chrome 의 이탈」로 판정하지 않는다** — 받은 사본이 **2020 년 초안**이고 편집자 초안은 받지 않았다(머리말). **말할 수 있는 것은 「이 사본의 알고리즘과 Chrome 151 이 다르다」까지**다. 코드에서는 **첫 통지가 0×0 으로도 온다고 보고** 받는다 — 「보이게 됐다」로 읽지 않는다.
- ★ IO 쪽 — `width 0 · height 0` 은 `isIntersecting=true`, `display: none` 과 문서 밖은 `false` 였다. 면적이 0 이어도 **뷰포트 안에 자리가 있으면** 교차로 쳤다(이 판의 관찰 · IO 의 몫은 35편).

### (4) ★★★ 루프 경고 — 콜백 안에서 크기를 바꾸면

세 판이다. **틀 번호는 rAF 가 올린다** — HTML 의 update the rendering 에서 rAF 콜백이 **RO 보다 먼저** 돌기 때문이다(순서의 실측은 [38번 주제](../38-request-animation-frame/2-summary.md) (1)). 칸 `[…]` 하나가 틀 하나다.

```html
<!-- wa36b-36-loop.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>36 loop</title>
<style> body { margin: 0; } div { width: 100px; height: 20px; } </style>
<script>
// 콜백 안에서 크기를 바꾼다 — 무엇을 바꾸느냐(자기 · 자식 · 부모)에 따라 한 틀 안에서 콜백이 몇 번 불리고 오류 이벤트가 몇 번 나나
// 틀 번호는 rAF 가 올린다(렌더링 단계에서 rAF 가 ResizeObserver 보다 먼저 돈다 — HTML 의 update the rendering)
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
let 틀번호 = 0, 기록 = [];
const 세기 = () => { 틀번호++; requestAnimationFrame(세기); };
requestAnimationFrame(세기);
const 오류들 = [];
addEventListener("error", e => { 오류들.push(e); 기록.push(`틀${틀번호} 오류`); });
const 나무 = 깊이 => { let top = null, cur = document.body; const 줄 = []; for (let k = 0; k < 깊이; k++) { const d = document.createElement("div"); cur.append(d); 줄.push(d); cur = d; } return 줄; };
const 틀별 = () => { const m = new Map(); for (const s of 기록) { const [f, what] = s.split(" "); if (!m.has(f)) m.set(f, []); m.get(f).push(what); }
  return [...m.values()].map(v => "[" + v.join(",") + "]").join(" "); };
window.__끝 = async () => {
  const 줄 = [];
  // 가 — 관찰 대상 자신을 콜백마다 1px 키운다(다섯 번까지)
  { const [a] = 나무(1); let n = 0;
    const ro = new ResizeObserver(es => { 기록.push(`틀${틀번호} 콜백`); if (n++ < 5) a.style.width = (100 + n) + "px"; });
    ro.observe(a); await 틀(); await 틀(); await 틀(); await 틀();
    ro.disconnect(); a.remove(); 줄.push("가 자기를 키움\t" + 틀별()); 기록 = []; }
  // 나 — 세 겹(A > B > C)을 다 관찰하고, A 를 한 번 키운다. 콜백은 받은 요소의 자식을 키운다
  { const [A, B, C] = 나무(3); const 이름 = new Map([[A, "A"], [B, "B"], [C, "C"]]); let 켬 = false;
    const ro = new ResizeObserver(es => { 기록.push(`틀${틀번호} 콜백(${es.map(e => 이름.get(e.target)).join("")})`);
      if (!켬) return; for (const e of es) { const 자식 = e.target.firstElementChild; if (자식) 자식.style.height = "30px"; } });
    for (const x of [A, B, C]) ro.observe(x);
    await 틀(); await 틀(); 기록 = []; 켬 = true;
    A.style.height = "40px"; await 틀(); await 틀();
    ro.disconnect(); A.remove(); 줄.push("나 자식을 키움\t" + 틀별()); 기록 = []; }
  // 다 — 두 겹(P > C)을 다 관찰하고, C 를 한 번 키운다. C 를 받은 콜백은 부모 P 를 키운다
  { const [P, C] = 나무(2); const 이름 = new Map([[P, "P"], [C, "C"]]); let 켬 = false;
    const ro = new ResizeObserver(es => { 기록.push(`틀${틀번호} 콜백(${es.map(e => 이름.get(e.target)).join("")})`);
      if (!켬) return; for (const e of es) if (e.target === C) P.style.width = "150px"; });
    ro.observe(P); ro.observe(C);
    await 틀(); await 틀(); 기록 = []; 켬 = true;
    C.style.height = "40px"; await 틀(); await 틀(); await 틀();
    ro.disconnect(); P.remove(); 줄.push("다 부모를 키움\t" + 틀별()); 기록 = []; }
  const e = 오류들[0];
  줄.push(`오류 이벤트 수 = ${오류들.length}`);
  줄.push(`첫 오류 — ${e.constructor.name} · message 「${e.message}」 · error = ${e.error} · filename 이 이 문서 주소인가 = ${e.filename === location.href} · lineno = ${e.lineno}`);
  // 대조 — 보통 예외 하나를 잡지 않고 던진다(콘솔 창이 이것은 받는지)
  setTimeout(() => { throw new Error("대조용 예외"); }, 0); await 틀();
  줄.push(`대조용 예외까지 오류 이벤트 수 = ${오류들.length}`);
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py console wa36b-36-loop.html
가 자기를 키움	[콜백,오류] [콜백,오류] [콜백,오류] [콜백,오류] [콜백,오류] [콜백]
나 자식을 키움	[콜백(A),콜백(B),콜백(C)]
다 부모를 키움	[콜백(C),오류] [콜백(P)]
오류 이벤트 수 = 6
첫 오류 — ErrorEvent · message 「ResizeObserver loop completed with undelivered notifications.」 · error = null · filename 이 이 문서 주소인가 = true · lineno = 0
대조용 예외까지 오류 이벤트 수 = 7
--- 콘솔 ---
Runtime.exceptionThrown · Uncaught · Error: 대조용 예외
    at http://127.0.0.1:<A>/wa36b-36-loop.html:44:28
(exit 0)
```

- ★★★ **가 자기를 키움 — 틀마다 `[콜백,오류]`** 가 다섯 번, 여섯째 틀에 `[콜백]`. **한 틀에 콜백은 한 번만** 돌았다 — 콜백이 자기를 키우면 같은 틀 안에서 **다시 알리지 않고 다음 틀로 미룬다.** 그 미룰 때마다 **오류 이벤트가 한 번** 났다.
- ★★★ **나 자식을 키움 — 한 틀 안에 `[콜백(A),콜백(B),콜백(C)]`**, 오류 없음. **더 깊은 요소는 같은 틀에서 다시 알렸다.**
- ★★★ **다 부모를 키움 — `[콜백(C),오류]` 뒤 다음 틀에 `[콜백(P)]`.** 부모는 **더 얕으니** 같은 틀에서 못 알리고 오류 한 번과 함께 다음 틀로 갔다.
- ★★★ **오류 문구 전문 — `ResizeObserver loop completed with undelivered notifications.`** 받은 사본 §3.4.6 의 문자열과 **한 글자도 같다.** `window` 의 `error` 이벤트로 왔고 **`ErrorEvent`** 다. `error` 칸은 `null`(던진 값이 없다) · `lineno` 는 0 · `filename` 은 이 문서 주소였다.
- ★★★ **콘솔에는 안 왔다** — 물은 곳 둘(`Log.entryAdded` · `Runtime.exceptionThrown`) 어디에도 루프 오류가 없다. **같은 판에서 던진 보통 예외는 `Runtime.exceptionThrown` 으로 받았다**(대조 — 가이드 규칙 34 의 「오게 만든 판」). HTML 의 report an exception 은 콘솔을 「**may**」로 둔다 — **알리지 않은 것은 재량 안의 선택**이다.

```text
   한 틀 안의 RO 단계 (받은 사본 §3.6.1 · HTML update the rendering 의 모양)

   깊이 ← 0
   반복:  스타일·레이아웃 → 「깊이보다 깊은」 대상 중 크기가 바뀐 것을 모은다
          없으면 끝
          있으면 콜백 → 깊이 ← 이번에 알린 것 중 가장 얕은 깊이
   남은 것(더 얕아서 못 알린 것)이 있으면 → ErrorEvent 「ResizeObserver loop completed …」 → 다음 틀로

   가 자기를 키움   깊이 d 의 A 가 또 바뀜 → A 는 d 보다 깊지 않다 → 남음 → 오류 → 다음 틀
   나 자식을 키움   A(1) → B(2) → C(3) — 매번 더 깊다 → 한 틀에 셋 다
   다 부모를 키움   C(2) 가 P(1) 을 바꿈 → P 는 얕다 → 남음 → 오류 → 다음 틀에 P
```

- ★ **깊이로 끊는 이유** — 콜백이 자기(또는 조상)를 바꿀 때마다 같은 틀에서 다시 돌면 **틀이 끝나지 않는다.** 「더 깊은 것만」이면 문서의 깊이가 유한하므로 **반드시 끝난다.** 끝나지 못한 몫은 버리지 않고 **다음 틀로 넘긴다** — 가의 여섯째 틀에서 콜백이 여전히 온 이유다.

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   const ro = new ResizeObserver((entries, observer) => { … });
   ro.observe(요소, { box: "content-box" | "border-box" | "device-pixel-content-box" });   ← 기본 content-box
   ro.unobserve(요소) · ro.disconnect()
   entry.target · entry.contentRect(옛 표면 — 내용 상자의 DOMRectReadOnly)
   entry.contentBoxSize[0] · entry.borderBoxSize[0] · entry.devicePixelContentBoxSize[0]
        → { inlineSize, blockSize }   ← 가로/세로가 아니라 글쓰기 방향 기준
```

### 어디서 헷갈리나

- **`transform` 은 통지가 없다**((1)).
- **`padding`·`border` 는 `border-box` 로 봐야 보인다**((1)).
- **`resize` 이벤트는 뷰포트만** — 부모 때문에 줄어든 것은 RO 만 안다((1)).
- **첫 통지는 0×0 으로도 온다**((3)).
- **크기 배열은 `[0]`** 이다 — 조각난 상자(다단 등)를 위해 배열로 설계됐다. 이 편은 조각을 던지지 않았다.

## 어디서 틀리나

### 1. 요소 크기 변화를 `window` 의 `resize` 로 잡는다

**부모 폭 변화에 `resize` 는 0**이었다((1)). 사이드바를 접어 본문이 넓어지는 것 · 글자가 늘어 카드가 커지는 것은 **창 크기와 무관**하다.

### 2. `transform` 애니메이션 중인 요소를 RO 로 따라간다

**통지가 안 온다**((1)). 화면상 크기가 필요하면 `getBoundingClientRect()`(09편 (9))로 읽는다.

### 3. `padding` 을 바꾸는 컴포넌트를 기본 상자로 관찰한다

**기본은 `content-box`** 라 내용 크기가 안 바뀌면 조용하다((1)). 겉 크기가 필요하면 `{ box: "border-box" }`.

### 4. 콜백 안에서 관찰 대상을 다시 키운다

**틀마다 오류 한 번 + 한 번씩만 돈다**((4) 가). 크기를 **맞추는** 코드라면 목표값에 이르면 멈추게 하고, 부모를 건드리지 않는다((4) 다).

### 5. 루프 오류를 콘솔에서 찾는다

**이 판의 콘솔에는 안 나왔다**((4)). `window` 의 `error` 이벤트로 온다 — 오류 수집기가 `window.onerror` 를 쓰면 **이 문구가 수집기에 쌓인다.** 문구로 걸러 낼 때는 **전문을 그대로** 비교한다.

### 6. 첫 통지를 「크기가 바뀌었다」로 처리한다

**`observe` 만 해도 온다 — 0×0 이어도**((3)).

### 7. CDP 로 배율을 바꿔 장치 픽셀 로직을 시험한다

**값만 바뀌고 장치 픽셀 상자는 그대로**였다((2)). 배율이 걸린 시험은 **브라우저를 그 배율로 띄워서** 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 루프 오류 문구 `ResizeObserver loop completed with undelivered notifications.` | ★ **명세**(받은 사본 §3.4.6) — 이 판의 문자열과 같다 |
| 한 틀 안에서 더 깊은 것만 다시 알리고, 못 알린 것은 오류와 함께 다음 틀로 | ★ **명세**(§3.6.1 · HTML update the rendering) — 가 · 나 · 다 세 판이 그대로다 |
| `transform` 은 통지가 없다 · `padding` 은 `border-box` 만 | ★ **명세**의 상자 정의(내용 영역 · 테두리 영역) + **이 판의 관찰** |
| 루프 오류가 콘솔에 안 나온다 | ★ **재량 안의 선택** — HTML 이 콘솔을 「may」로 둔다 |
| 0×0 대상에도 첫 통지 | ★ **이 판의 관찰 — 받은 2020 WD 사본과 다르다**(편집자 초안은 못 봤다) |
| `device-pixel-content-box` 가 실제 배율을 따른다 · CDP 배율 에뮬레이션은 그것을 안 바꾼다 | ★ **이 판의 관찰**(도구의 성질 포함) |
| `resize` 이벤트는 뷰포트 변화에만 | **명세**(HTML 「run the resize steps」 — CSSOM View) + 이 판의 관찰 |
| 비용 | ★ **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 컨테이너 폭에 따라 차트 · 캔버스를 다시 그리기 | RO(`content-box`) — 그리기는 콜백에서 다음 rAF 로 미룬다 | `window` 의 `resize`(부모 변화를 못 본다) |
| 캔버스를 화면 점에 딱 맞추기 | RO(`device-pixel-content-box`) — 실제 배율을 따른다((2)) | `contentRect × devicePixelRatio` 를 손으로 계산 |
| 겉 크기(테두리 포함)가 필요 | `{ box: "border-box" }` | 기본 상자 |
| `transform` 으로 움직이는 요소의 화면상 크기 | `getBoundingClientRect()`(09편) | RO(통지가 없다) |
| 콘텐츠 크기에 맞춰 부모를 조정 | 콜백에서 **다음 rAF** 에 조정 · 목표값이면 멈춤 | 콜백에서 곧바로 부모 크기를 바꿈(오류 · 다음 틀로 밀림) |

## 핵심 문장

1. **RO 는 「고른 상자의 레이아웃 크기」가 바뀌면 알린다** — 21칸 중 11칸. `transform` 은 레이아웃 크기가 아니라서 조용하다.
2. **`window` 의 `resize` 는 뷰포트의 일이다** — 부모 폭이 요소를 줄여도 0 이었다.
3. **첫 통지는 관찰 시작만으로 온다 — 0×0 이어도**(받은 2020 사본과는 다르다).
4. **콜백 안의 크기 변화는 같은 틀에서 「더 깊은 것」만 다시 알리고, 나머지는 `ResizeObserver loop completed with undelivered notifications.` 와 함께 다음 틀로 간다.** 콘솔이 아니라 `window` 의 `error` 이벤트다.
5. **CDP 배율 에뮬레이션은 `devicePixelRatio` 값만 바꿨다** — 장치 픽셀 상자는 브라우저의 실제 배율을 따른다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 36번)
- [09번 주제](../09-element-geometry/2-summary.md) — 세 계열이 테두리 · `transform` 을 포함하나를 **읽는** 쪽. 여기는 **바뀌면 알림을 받는** 쪽
- [35번 주제](../35-intersection-observer/2-summary.md) — 관찰자 짝. 「관찰 시작 한 번」이 같고, 알리는 조건(겹침 대 크기)이 다르다
- [38번 주제](../38-request-animation-frame/2-summary.md) — 렌더링 단계 안에서 rAF · RO · IO 의 순서를 Tracing 으로 잰 정본
- [10번 주제](../10-layout-thrashing/2-summary.md) — 폴링으로 `offsetWidth` 를 읽는 쪽의 비용(여기서는 비용을 재지 않았다)
- [24번 주제](../24-document-lifecycle-events/2-summary.md) — 창 ④ 디스패치 계수기의 정본

## 용어 풀이

- **`ResizeObserver`(RO)** — 요소의 **고른 상자 크기**가 바뀌면 렌더링 단계 안에서 알려 주는 관찰자.
- **관측 상자(`box`)** — 어느 상자의 크기를 볼지. `content-box`(내용) · `border-box`(테두리까지) · `device-pixel-content-box`(내용을 장치 픽셀로).
- **`inlineSize` · `blockSize`** — 글쓰기 방향 기준의 가로 · 세로. 가로쓰기에서는 폭 · 높이다.
- **깊이** — 문서 트리에서 요소까지의 조상 수. RO 의 루프 끊기가 이것으로 판정한다.
- **루프 오류** — 한 틀에 다 못 알린 통지가 남았을 때 나는 `ErrorEvent`. 문구는 명세가 정한다.
- **상자 격자** — 관측 상자 셋 × 변화 일곱 = 21칸. 이 편의 본체.
- **배율(device scale factor)** — CSS 픽셀 하나가 화면 점 몇 개인가. `devicePixelRatio` 로 읽는다.

## 더 들어가면

- ★★ **편집자 초안 대조** — 0×0 대상의 첫 통지가 초안에서 어떻게 정해졌는지 맞대는 일이 남았다((3)).
- **조각난 상자**(다단 · 페이지 나눔)에서 크기 배열이 둘 이상이 되는가 — 던지지 않았다.
- **SVG 요소** — 사본은 bounding box 로 잰다고 적는다. 던지지 않았다.
