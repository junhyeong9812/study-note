# web-api/38 — `requestAnimationFrame` 과 프레임 예산 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「디스패치 계수기」를 시간 축에 세운 두 장이다** — ① **렌더 단계 안 위치 로그**(한 태스크에서 `scrollTo` · 폭 쓰기 · rAF 등록을 한꺼번에 하고, 다음 렌더링 단계에서 누가 어느 순서로 불리나를 **콜백의 `console.timeStamp` 자국 + CDP Tracing 이벤트 이름**을 한 줄에 섞어 읽는다)와 ② **rAF 간격 격자**(콜백 안의 바쁨 0 · 10 · 20 · 30 · 100ms × 다섯 판 — 칸 = 그 판에서 가장 많았던 **간격 범주**). ★ **시간은 찍지 않는다** — 간격은 「16.7ms 의 몇 배 근처였나」 범주로만, 나머지는 **순서 · 참/거짓 · 횟수**다(가이드 규칙 24).\
> **기준 소스** — [HTML — update the rendering](https://html.spec.whatwg.org/multipage/webappapis.html#update-the-rendering)(렌더링 단계의 순서 · 「Filter non-renderable documents」 · 「rendering opportunity」 · 60Hz 예의 「about 16.7ms」) · [HTML — animation frames](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#animation-frames)(「run the animation frame callbacks」 — **시작할 때의 핸들 목록**만 돈다) · [W3C Intersection Observer](https://w3c.github.io/IntersectionObserver/) §3.2.4(IO 알림은 **태스크**로 건다). 받아서 읽은 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless(`--window-size=1000,800`)에서 받은 것이다. 하네스는 [36번 주제](../36-resize-observer/3-answer.md)의 `wa36b-net.py` — 부탁 창구로 **Tracing**(`devtools.timeline`) · **`Performance.getMetrics`** · **새 탭 띄우기**를 불렀다. ★★★ **`--virtual-time-budget` 을 쓰지 않았다** — 가상 시간에서는 rAF 간격이 실제가 아니다. 이 판의 프레임은 **실제 시간**으로 돈다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** ★ **헤드리스에는 모니터가 없다** — 이 편의 프레임 간격은 **화면 주사율이 아니라 헤드리스 Chrome 이 스스로 만든 박자**다.\
> **선행** — ★★ **[10번 주제](../10-layout-thrashing/2-summary.md)** — 읽기 · 쓰기 교차가 레이아웃을 강제한다. 그 편 (7)은 「**rAF 로 미루면? — 이 도구로는 못 잰다**」로 끝났다 — 여기서 그것을 **`LayoutCount`** 로 잰다((5)). ★★ [CSS 갈래 56번](../../languages/css/syntax/56-rendering-pipeline-and-will-change/2-summary.md) — 스타일 → 레이아웃 → 페인트 → 합성 **네 공정**과 `LayoutCount` · Tracing 의 쓰는 법. 여기서는 그 공정들 **사이에 스크립트 콜백이 어디 끼나**를 본다.\
> **경계** — ★★★ **「rAF 가 60fps 를 보장한다」는 이 편이 주장하지 않는다** — 명세도 「**does not mandate any particular model**」이라 적는다. ★★ [`history/web/04-브라우저-엔진.md`](../../../../history/web/04-브라우저-엔진.md) 는 **엔진의 계보**(Trident · Gecko · WebKit · Blink)를 다루고 **렌더 파이프라인 절은 없다**(`grep` 으로 확인 — 「렌더링(레이아웃) 엔진」이라는 낱말 풀이까지다). 파이프라인의 공정은 CSS 56편, **그 안에서의 스크립트 자리**가 여기다. ★ `Promise.then` · `setTimeout(0)` · rAF 셋의 순서와 마이크로태스크가 렌더를 굶기는 자리는 목록의 **40번 주제**(폴더는 아직 없다)의 몫이다.\
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
| **안 흔들린다** | 위치 로그 두 판(자국 + Tracing 이름) · 간격 격자 25칸 · 숨김 한 줄 · timestamp 두 줄 · `LayoutCount` 12칸 | 캡처 세 판이 **한 글자도 같았다** |
| ★★ **판에 매일 수 있는 칸** | **간격 범주** | 실제 시간이다 — 기계가 바쁘면 범주가 한 칸 옮을 수 있다. 그래서 **범주의 경계에서 먼 조건**(0 · 10 · 30 · 100ms)을 골랐다. ★ 20ms 는 경계(1.5배 = 25ms)에서 5ms 떨어져 있다 — 세 판 모두 `≈1` 이었다 |
| **흔들린다** | Chrome 판 번호 · 포트 | 출력에 안 나온다 |

- 재대조에서 정규화하는 칸은 **없다.**

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | ★ `--dump-dom` 은 프레임을 제대로 기다리지 않는다(10편 (7) — 판마다 rAF 가 0\~2번) |
| 창 ② 노드 프로브 | ★ **쓴다** | rAF 가 받은 `timestamp` 인자 · `visibilityState` · `offsetWidth` |
| 창 ③ 같은 것을 두 번 읽기 | ★ **쓴다** | 같은 방아쇠를 **읽기 없이 / 읽고** 두 판 · 같은 쓰기 20번을 **네 모양**으로 |
| **창 ④ 디스패치 계수기 → 위치 로그 · 간격 격자** | ★★★ **본체** | 콜백이 **어느 순서로** · **몇 틀 간격으로** · 숨었을 때 **몇 번** |
| ★★ **Tracing 이벤트 이름 · `LayoutCount`** | ★★ **제5의 상태 — 같은 질문을 다른 창으로** | 「레이아웃이 **언제 · 몇 번** 돌았나」를 스크립트는 못 본다. 브라우저의 **자기 기록**(Tracing 의 `UpdateLayoutTree` · `Layout` · `Paint`, `Performance.getMetrics` 의 `LayoutCount`)으로 물었다. ★ 바꾼 창이 못 보는 것 — **합성 스레드의 일**(Tracing 은 렌더러 주 스레드만 걸렀다) · 화면에 **실제로 나간 틀** |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **실제 화면의 주사율 · 틀 떨굼** | 헤드리스에 모니터가 없다 — 간격은 헤드리스의 박자다 |
| ★★ **한 틀의 예산이 정확히 몇 ms 인가** | ms 를 근거로 쓰지 않았다 — 「바쁨이 이만큼이면 범주가 옮았나」만 본다 |
| **합성 스레드 · GPU** | Tracing 을 렌더러 주 스레드로 걸렀다 |
| **숨은 탭에서 틀이 「느려지는」지 「멈추는」지의 긴 경향** | 숨김은 setInterval 세 번(약 0.3초) 동안만 봤다 |

## 한눈에 — 쉽게 말하면

**★ 브라우저는 「그림 한 장을 넘기는 만화가」다. 한 장을 그리기 직전에 「그리기 전에 부를 사람 명단」(rAF)을 한 번 훑어 부르고, 그다음 치수를 재고(스타일 · 레이아웃) · 치수가 바뀐 사람에게 알리고(RO) · 그림을 그린다(페인트). 명단은 훑기 시작할 때의 명단이라, 불려 온 사람이 「다음에도 불러 줘」라고 적으면 다음 장에서 불린다. 한 사람이 30ms 를 붙들고 있으면 다음 장이 그만큼 늦게 온다. 커튼이 쳐지면(탭 숨김) 아무도 안 보니 그리기를 멈춘다.**

| 비유 | 실체 |
|---|---|
| 그리기 전 명단 | rAF 콜백 목록 — 렌더링 단계 안에서, 스타일 · 레이아웃보다 **앞** |
| 명단을 훑기 시작할 때의 명단 | 「run the animation frame callbacks」가 **처음의 핸들 목록**만 돈다 → 안에서 건 rAF 는 다음 틀 |
| 한 장 넘기는 박자 | 「rendering opportunity」 — 명세는 모델을 강제하지 않고 60Hz 예(약 16.7ms)만 든다 |
| 한 사람이 붙들고 있음 | 콜백 안의 바쁨 → 간격이 늘어난다(≈2 · ≥5) |
| 커튼 | `visibilityState` 가 `hidden` → 「Filter non-renderable documents」에서 빠진다 |

```text
   한 태스크에서 scrollTo · 폭 쓰기 · rAF 등록 → 다음 렌더링 단계 (이 판 · Tracing + 자국)

   태스크          ScrollLayer · ⟨태스크 끝⟩
   렌더링 단계     scroll 이벤트 · (scrollend)
                   FireAnimationFrame → ⟨rAF⟩
                   UpdateLayoutTree → Layout                ← 스타일 · 레이아웃
                   PrePaint · 교차 계산 → ⟨ResizeObserver⟩
                   PrePaint · 교차 계산 → Paint              ← 페인트
   다음 태스크     ⟨IntersectionObserver⟩                    ← IO 알림은 태스크로 온다
```

## 이 주제가 답하려는 질문

1. **rAF 콜백은 렌더링 단계의 어디에서 불리나** — `scroll` · RO · IO · 스타일 · 레이아웃 · 페인트와의 순서.
2. **한 틀에 쓸 수 있는 시간을 넘기면 무엇이 보이나** — 간격 범주 · 숨김 · 안에서 건 rAF.
3. **rAF 로 미루는 것이 무엇을 줄이나** — 레이아웃 횟수로.

## 동작 방식

### (1) ★★★ 본체 ① — 렌더 단계 안 위치 로그

아래쪽 화면 밖의 `#i`(IO) · 폭을 쓸 `#r`(RO) · `scroll` 리스너 · rAF. **콜백마다 `console.timeStamp` 로 자국**을 남기고, 하네스가 두 표지 사이의 **렌더러 주 스레드 Tracing 이벤트 이름**과 자국을 시각 순으로 한 줄에 섞어 돌려준다(이름이 같으면 이어진 것을 하나로 줄였다). 판 나는 폭을 쓴 **바로 뒤에 `offsetWidth` 를 읽는다.**

```html
<!-- wa36b-38-order.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>38 order</title>
<style>
  body { margin: 0; height: 4000px; }
  #r { width: 100px; height: 40px; background: #cde; }
  #i { position: absolute; top: 1500px; width: 100px; height: 40px; background: #dce; }
</style>
<div id="r"></div><div id="i"></div>
<script>
// 한 태스크에서 방아쇠 셋을 한꺼번에 당긴다 — scrollTo(scroll 이벤트 · #i 가 뷰포트로 들어옴) · #r 의 폭 쓰기(ResizeObserver) · rAF 등록
// 콜백마다 console.timeStamp 로 자국을 남기고, 렌더러 주 스레드의 Tracing 이벤트 이름과 한 줄에 섞어 시각 순으로 읽는다
// 판 나 는 태스크 안에서 폭을 쓴 뒤 곧바로 offsetWidth 를 읽는다
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
const r = document.getElementById("r"), i = document.getElementById("i");
let 켬 = false, 끝냄 = null;
const 자국 = s => 켬 && console.timeStamp(s);
addEventListener("scroll", () => 자국("scroll"));
new ResizeObserver(() => 자국("ResizeObserver")).observe(r);
new IntersectionObserver(es => { if (켬 && es[0].isIntersecting) { 자국("IntersectionObserver"); setTimeout(끝냄, 0); } }).observe(i);
const 줄임 = a => a.filter((x, k) => x !== a[k - 1]);
const 한판 = async (이름, 읽기) => {
  scrollTo(0, 0); r.style.width = "100px"; await 틀(); await 틀();
  await __부탁("추적시작"); await 틀();
  const 다됨 = new Promise(res => { 끝냄 = res; });
  켬 = true;
  console.timeStamp("wa36b");
  scrollTo(0, 1500 - innerHeight + 100);
  r.style.width = "140px";
  if (읽기) 자국("offsetWidth=" + r.offsetWidth);
  requestAnimationFrame(() => 자국("rAF"));
  자국("태스크 끝");
  await 다됨;
  console.timeStamp("wa36b"); 켬 = false;
  const 이름들 = await __부탁("추적끝", { 표: "wa36b" });
  return `${이름}\t${줄임(이름들).join(" → ")}`;
};
window.__끝 = async () => [await 한판("가 쓰기만", false), await 한판("나 쓰고 곧바로 읽기", true)].join("\n");
</script>
```

```text
$ python3 wa36b-net.py page wa36b-38-order.html
가 쓰기만	ScrollLayer → ⟨태스크 끝⟩ → EventDispatch(scroll) → ⟨scroll⟩ → EventDispatch(scrollend) → FireAnimationFrame → ⟨rAF⟩ → UpdateLayoutTree → Layout → PrePaint → IntersectionObserverController::computeIntersections → ⟨ResizeObserver⟩ → PrePaint → IntersectionObserverController::computeIntersections → Paint → IntersectionObserverController::computeIntersections → ⟨IntersectionObserver⟩
나 쓰고 곧바로 읽기	ScrollLayer → UpdateLayoutTree → Layout → ⟨offsetWidth=140⟩ → ⟨태스크 끝⟩ → EventDispatch(scroll) → ⟨scroll⟩ → EventDispatch(scrollend) → FireAnimationFrame → ⟨rAF⟩ → PrePaint → IntersectionObserverController::computeIntersections → ⟨ResizeObserver⟩ → PrePaint → IntersectionObserverController::computeIntersections → Paint → IntersectionObserverController::computeIntersections → ⟨IntersectionObserver⟩
(exit 0)
```

- ★★★ **순서 — `⟨scroll⟩` → `FireAnimationFrame → ⟨rAF⟩` → `UpdateLayoutTree → Layout` → `⟨ResizeObserver⟩` → `Paint` → `⟨IntersectionObserver⟩`.** HTML 의 update the rendering 이 적은 순서 — **scroll 단계 → rAF 콜백 → 스타일 · 레이아웃과 RO 반복 → IO 갱신 → 그리기** — 와 **그대로 맞는다.**
- ★★★ **rAF 는 스타일 · 레이아웃보다 앞이다** — 그래서 rAF 안에서 쓴 스타일은 **같은 틀의 레이아웃 한 번**에 들어간다. 반대로 **rAF 안에서 기하를 읽으면** 아직 레이아웃 전이라 그 자리에서 강제로 돈다(10편의 일).
- ★★ **`⟨ResizeObserver⟩` 는 `Layout` 뒤 · `Paint` 앞** — 크기가 정해진 뒤에 알리고, 콜백이 크기를 바꾸면 **같은 틀 안에서 다시 레이아웃**한다([36번 주제](../36-resize-observer/2-summary.md) (4)의 반복).
- ★★ **`⟨IntersectionObserver⟩` 는 `Paint` 뒤** — 교차 계산(`IntersectionObserverController::computeIntersections`)은 틀 안에서 했지만 **알림은 태스크로** 왔다. IO 명세 §3.2.4 가 「Queue a task on the IntersectionObserver task source」다. [35번 주제](../35-intersection-observer/2-summary.md) (4)의 `scroll → rAF → IO` 가 이 줄의 일부다.
- ★★ **판 나 — `UpdateLayoutTree → Layout` 이 태스크 안(`⟨offsetWidth=140⟩` 앞)으로 옮겨 갔고, 렌더링 단계에서는 사라졌다.** 태스크에서 이미 레이아웃을 끝냈으니 틀에서 할 일이 없다. 읽기가 레이아웃을 「**당겨 온다**」는 것이 한 줄로 보인다.
- ★ **`scrollend` 가 같은 틀에서 났다** — 즉시 스크롤(`scrollTo`)이라 끝도 바로였다(이 판의 관찰 — 명세는 CSSOM View 의 몫이고 받지 않았다).

### (2) ★★★ 본체 ② — rAF 간격 격자

rAF 가 rAF 를 이어 거는 고리를 조건마다 **다섯 판(판마다 간격 20개)**. 간격은 **이웃한 두 콜백이 받은 `timestamp` 인자의 차**를 16.7ms 의 몇 배인가로 범주를 매긴다 — `≈1`(1.5배 미만) · `≈2`(2.5배 미만) · `3~4` · `≥5`. 칸은 그 판에서 가장 많았던 범주다.

```html
<!-- wa36b-38-gap.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>38 gap</title>
<script>
// rAF 간격 격자 — rAF 가 rAF 를 이어 거는 고리를 조건마다 다섯 판(판마다 간격 20개) 돌린다
// 간격 = 이웃한 두 콜백이 받은 timestamp 인자의 차 · 16.7ms 의 몇 배인가로 범주를 매긴다(ms 는 찍지 않는다)
//   ≈1 (1.5배 미만) · ≈2 (2.5배 미만) · 3~4 (5배 미만) · ≥5
// 한 판의 결과 = 간격 20개 중 가장 많은 범주 · 칸 = 다섯 판의 결과
const 바쁨 = ms => { const t = performance.now(); while (performance.now() - t < ms) {} };
const 범주 = d => { const x = d / (1000 / 60); return x < 1.5 ? "≈1" : x < 2.5 ? "≈2" : x < 5 ? "3~4" : "≥5"; };
const 고리 = (n, 콜백안) => new Promise(끝 => {
  const ts = [];
  const 한장 = t => { ts.push(t); if (ts.length > n) return 끝(ts); 콜백안(); requestAnimationFrame(한장); };
  requestAnimationFrame(한장);
});
const 최빈 = a => { const m = {}; for (const x of a) m[x] = (m[x] || 0) + 1; return Object.entries(m).sort((p, q) => q[1] - p[1])[0][0]; };
const 조건들 = [["보통", () => {}], ["콜백 안에서 10ms 바쁨", () => 바쁨(10)], ["콜백 안에서 20ms 바쁨", () => 바쁨(20)], ["콜백 안에서 30ms 바쁨", () => 바쁨(30)], ["콜백 안에서 100ms 바쁨", () => 바쁨(100)]];
window.__끝 = async () => {
  const 줄 = [["조건", "판1", "판2", "판3", "판4", "판5"].join("\t")];
  for (const [이름, 일] of 조건들) {
    const 칸 = [];
    for (let k = 0; k < 5; k++) { const ts = await 고리(20, 일); 칸.push(최빈(ts.slice(1).map((t, j) => 범주(t - ts[j])))); }
    줄.push([이름, ...칸].join("\t"));
  }
  // 탭 숨김 — 새 탭을 앞으로 띄워 이 탭을 뒤로 보낸다(24편 방식). 그동안 rAF 고리가 몇 번 도나
  let 호출 = 0, 켬 = true; const 돌기 = () => { 호출++; if (켬) requestAnimationFrame(돌기); }; requestAnimationFrame(돌기);
  await new Promise(r => setTimeout(r, 200));
  const 보일때 = 호출 > 0;
  const 숨음 = new Promise(r => addEventListener("visibilitychange", r, { once: true }));
  await __부탁("숨기기"); await 숨음;
  const 숨김시작 = 호출, 상태 = document.visibilityState;
  let 타이머 = 0; await new Promise(r => { const id = setInterval(() => { if (++타이머 === 3) { clearInterval(id); r(); } }, 100); });
  const 숨김동안 = 호출 - 숨김시작;
  const 보임 = new Promise(r => addEventListener("visibilitychange", r, { once: true }));
  await __부탁("보이기"); await 보임;
  const 돌아온때 = 호출; await new Promise(r => setTimeout(r, 200)); 켬 = false;
  줄.push(`탭 숨김\t보일 때 200ms 동안 rAF 가 돌았나 = ${보일때} · 숨긴 뒤 visibilityState = ${상태} · 숨긴 동안(setInterval 100ms 세 번) rAF 호출 = ${숨김동안}번 · 되돌린 뒤 200ms 동안 돌았나 = ${호출 > 돌아온때}`);
  // rAF 안에서 건 rAF · 한 태스크에서 건 rAF 둘
  const 둘 = await new Promise(r => { const t = []; requestAnimationFrame(a => t.push(a)); requestAnimationFrame(b => { t.push(b); r(t); }); });
  const 안팎 = await new Promise(r => requestAnimationFrame(a => requestAnimationFrame(b => r([a, b]))));
  줄.push(`한 태스크에서 건 rAF 둘이 같은 timestamp 를 받았나 = ${둘[0] === 둘[1]}`);
  줄.push(`rAF 안에서 건 rAF 가 더 큰 timestamp 를 받았나 = ${안팎[1] > 안팎[0]}`);
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-38-gap.html | sed -n '1,6p'
조건	판1	판2	판3	판4	판5
보통	≈1	≈1	≈1	≈1	≈1
콜백 안에서 10ms 바쁨	≈1	≈1	≈1	≈1	≈1
콜백 안에서 20ms 바쁨	≈1	≈1	≈1	≈1	≈1
콜백 안에서 30ms 바쁨	≈2	≈2	≈2	≈2	≈2
콜백 안에서 100ms 바쁨	≥5	≥5	≥5	≥5	≥5
(exit 0)
```

- ★★★ **보통 · 10ms — 다섯 판 다 `≈1`**, **30ms — 다섯 판 다 `≈2`**, **100ms — 다섯 판 다 `≥5`.** 콜백 안의 일이 길어지면 **다음 틀이 그만큼 늦게 온다.** 프레임 예산을 넘긴 증상이 **「간격이 늘어난다」** 로 보인다 — 에러도 경고도 없다.
- ★★ **20ms 는 `≈1`** 이다 — 16.7ms 보다 길게 붙들었는데 간격은 **25ms 미만**이었다. 이 헤드리스는 **다음 틀을 16.7ms 의 배수(33.3ms)까지 미루지 않고** 일이 끝나는 대로 곧 다음 틀을 냈다는 뜻이다. ★ **실제 화면(주사율에 묶인 틀)에서도 그런지는 못 쟀다**(머리말) — 명세도 「30 으로 떨어뜨릴 **수도** 있다」고만 적는다.
- ★ 이것은 **몇 fps 인가**가 아니다 — 범주는 「몇 배 근처였나」뿐이다. **「rAF 가 60fps 를 보장한다」는 이 격자로도 명세로도 서지 않는다.**

```text
   콜백 안의 바쁨 → 간격 범주 (이 판 · 다섯 판 모두 같았다)

   바쁨    0      10     20     30     100 ms
   범주    ≈1     ≈1     ≈1     ≈2     ≥5
           └── 예산 안 ──┘      └ 한 틀 이상 밀림 ┘
   ★ 20 이 ≈1 인 것 — 이 헤드리스는 틀을 16.7 배수로 맞추지 않았다
```

### (3) ★★★ 탭이 숨으면 rAF 가 멈춘다 · 안에서 건 rAF 는 다음 틀

하네스가 **새 탭을 앞으로 띄워** 이 탭을 뒤로 보낸다([24번 주제](../24-document-lifecycle-events/2-summary.md) 방식). 숨은 동안은 **`setInterval` 100ms 가 세 번 울릴 때까지** 기다린다.

```text
$ python3 wa36b-net.py page wa36b-38-gap.html | sed -n '7,$p'
탭 숨김	보일 때 200ms 동안 rAF 가 돌았나 = true · 숨긴 뒤 visibilityState = hidden · 숨긴 동안(setInterval 100ms 세 번) rAF 호출 = 0번 · 되돌린 뒤 200ms 동안 돌았나 = true
한 태스크에서 건 rAF 둘이 같은 timestamp 를 받았나 = true
rAF 안에서 건 rAF 가 더 큰 timestamp 를 받았나 = true
(exit 0)
```

- ★★★ **숨긴 동안 rAF 호출 0번** — 같은 동안 **`setInterval` 은 세 번 울렸다**(그래서 숨김 구간이 끝났다). 되돌리자 다시 돌았다(`true`). 명세의 update the rendering 은 첫머리 「**Filter non-renderable documents**」에서 **`visibility state` 가 `"hidden"` 인 문서를 뺀다** — rAF 는 렌더링 단계 **안**에 있으니 같이 멈춘다. **타이머는 렌더링 단계 밖**이라 계속 돈다.
- ★★ **한 태스크에서 건 rAF 둘은 같은 `timestamp`** — 같은 틀에서 같은 「틀 시각」을 받는다.
- ★★ **rAF 안에서 건 rAF 는 더 큰 `timestamp`** — 다음 틀이다. 「run the animation frame callbacks」는 **시작할 때의 핸들 목록(callbackHandles)** 만 돈다 — 도중에 붙은 것은 이번 목록에 없다. ★ **마이크로태스크와 정반대**다 — JS 36편 (2)의 체크포인트는 「**비어 있지 않은 동안**」 돌아 도중에 붙은 것까지 같은 비우기에서 돌렸다.

### (4) 프레임 예산 — 명세가 말하는 것과 말하지 않는 것

- 명세 — 「rendering opportunity」는 **하드웨어 주사율 · 성능 조절 · 가시성**으로 정해지고, **「This specification does not mandate any particular model」**. 예로 「60Hz 면 **about 16.7ms** 마다 · 못 따라가면 30 으로 · 안 보이면 4 로 **또는 더 적게**」를 든다.
- ★★ 그래서 **「한 틀 16.7ms」는 명세의 보장이 아니라 60Hz 화면의 예**다. 이 편이 잰 것은 **「콜백이 길어지면 다음 틀이 밀린다」**(2)와 **「숨으면 0 번」**(3)이다. 이 판의 숨김은 「4 로 떨어뜨림」이 아니라 **0**이었다 — 「Filter non-renderable documents」 쪽이 먼저 걸린다.
- ★ **틀 하나 안에는 rAF 말고도 일이 있다** — (1)의 줄에서 rAF 뒤에 스타일 · 레이아웃 · RO · 페인트가 이어졌다. **rAF 콜백의 몫은 예산의 일부**다. 몇 ms 가 남는지는 재지 않았다.

### (5) ★★ rAF 로 미루면 레이아웃이 몇 번 도나 — `LayoutCount`

10편 (7)이 「이 도구로는 못 잰다」고 남긴 자리다. 요소 20개의 폭을 쓰는 네 모양 앞뒤로 **`Performance.getMetrics` 의 `LayoutCount`** 를 읽는다(틀 두 장씩 기다린 뒤). 모양마다 세 번.

```html
<!-- wa36b-38-layout.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>38 layout</title>
<style> body { margin: 0; } .b { width: 100px; height: 10px; background: #cde; } </style>
<div id="host"></div>
<script>
// 레이아웃 횟수 — CDP Performance.getMetrics 의 LayoutCount 를 일의 앞뒤로 읽는다(시간은 안 잰다)
// 가 쓰기·읽기를 20번 번갈아 · 나 쓰기 20번 뒤 읽기 1번 · 다 쓰기 20번만(읽지 않고 다음 틀에 맡김) · 라 아무것도 안 함
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
const host = document.getElementById("host");
for (let k = 0; k < 20; k++) host.append(Object.assign(document.createElement("div"), { className: "b" }));
const bs = [...host.children];
const 판들 = [
  ["가 쓰기·읽기 20번 교차", w => { for (const b of bs) { b.style.width = w + "px"; b.offsetWidth; } }],
  ["나 쓰기 20번 → 읽기 1번", w => { for (const b of bs) b.style.width = w + "px"; bs[0].offsetWidth; }],
  ["다 쓰기 20번 → 다음 틀", w => { for (const b of bs) b.style.width = w + "px"; }],
  ["라 아무것도 안 함", w => {}],
];
window.__끝 = async () => {
  const 줄 = [];
  let w = 100;
  for (const [이름, 일] of 판들) {
    const 값 = [];
    for (let k = 0; k < 3; k++) {
      await 틀(); await 틀();
      const 앞 = await __부탁("지표");
      일(++w);
      await 틀(); await 틀();
      const 뒤 = await __부탁("지표");
      값.push(뒤.LayoutCount - 앞.LayoutCount);
    }
    줄.push(`${이름}\tLayoutCount 증가(세 번) = ${값.join(" · ")}`);
  }
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-38-layout.html
가 쓰기·읽기 20번 교차	LayoutCount 증가(세 번) = 20 · 20 · 20
나 쓰기 20번 → 읽기 1번	LayoutCount 증가(세 번) = 1 · 1 · 1
다 쓰기 20번 → 다음 틀	LayoutCount 증가(세 번) = 1 · 1 · 1
라 아무것도 안 함	LayoutCount 증가(세 번) = 0 · 0 · 0
(exit 0)
```

- ★★★ **가 교차 20번 → `LayoutCount` +20** · **나 쓰기 20 → 읽기 1 → +1** · **다 쓰기만 하고 틀에 맡김 → +1** · **라 → 0.** 세 번 다 같았다.
- ★★★ **다가 이 편의 답이다** — 쓰기만 하고 읽지 않으면 **틀의 렌더링 단계가 레이아웃을 한 번** 돌린다((1)의 판 가). **rAF 로 「읽기를 미룬다」는 것은 곧 이 모양**이다 — 쓰기를 모아 두고 틀에 맡긴다. 교차(가)에 비해 **20 → 1**.
- ★ **나와 다가 같은 1** — 레이아웃이 도는 **자리**만 다르다(나는 태스크 안, 다는 틀 안 — (1)의 판 나 · 가). 횟수로는 같다. **시간은 재지 않았다.**

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   const id = requestAnimationFrame(timestamp => { … });   ← 한 번만 불린다(이어 가려면 다시 건다)
   cancelAnimationFrame(id)
   timestamp — 이 틀의 시각(같은 틀의 콜백은 같은 값) · performance.now() 와 같은 눈금
```

### 어디서 헷갈리나

- **한 번 걸면 한 번이다** — `setInterval` 이 아니다. 고리는 콜백 안에서 다시 건다.
- **안에서 건 rAF 는 다음 틀**이다((3)).
- `timestamp` 는 「지금」이 아니라 「**이 틀의 시각**」이다 — 콜백 안에서 오래 일해도 같은 값이다((3)).
- **숨은 탭에서는 안 불린다**((3)) — 타이머는 불린다.

## 어디서 틀리나

### 1. 「rAF 는 60fps 를 보장한다」

**명세가 강제하지 않는다**((4)). 이 판에서도 콜백이 30ms 를 쓰면 간격이 `≈2` 로 늘었다((2)).

### 2. rAF 로 애니메이션 시간을 센다 — 호출 수 × 16.7

**틀이 밀리면 틀린다**((2)). 진행은 **`timestamp` 의 차**로 계산한다.

### 3. 숨은 탭에서도 rAF 로 상태를 갱신한다(폴링 · 타이머 대용)

**0번 불린다**((3)). 탭이 가려져도 돌아야 하는 일은 rAF 에 두지 않는다 — 돌아왔을 때 따라잡는 형태로.

### 4. rAF 안에서 기하를 먼저 읽고 쓴다 — 「rAF 안이니 싸다」

rAF 는 **레이아웃 전**이다((1)). 앞 틀의 쓰기가 남아 있으면 **읽기가 그 자리에서 레이아웃을 당긴다**(판 나의 모양). 읽기 → 쓰기 순서, 교차 금지(10편).

### 5. rAF 안에서 rAF 를 걸어 「같은 틀에서 한 번 더」를 기대한다

**다음 틀**이다((3)). 같은 틀 안에서 한 번 더 돌 일은 그냥 함수로 부른다.

### 6. `--virtual-time-budget` 으로 rAF 간격을 잰다

가상 시간에서는 **틀 간격이 실제가 아니다**(머리말). 이 편은 가상 시간을 쓰지 않았다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| scroll → rAF → 스타일 · 레이아웃(+RO 반복) → IO 갱신 → 그리기 | ★ **명세**(HTML update the rendering) — 이 판의 Tracing 줄이 그대로다 |
| IO 알림은 그리기 뒤의 태스크 | ★ **명세**(IO §3.2.4 — 태스크로 건다) + 이 판의 관찰 |
| 숨은 탭에서 rAF 0번 | ★ **명세**(Filter non-renderable documents) + 이 판의 관찰(0.3초 구간) |
| 같은 틀의 rAF 는 같은 `timestamp` · 안에서 건 rAF 는 다음 틀 | ★ **명세**(run the animation frame callbacks 의 핸들 목록 · frameTimestamp) |
| 한 틀 = 약 16.7ms | ★ **명세의 예일 뿐**(「does not mandate」) |
| 바쁨 20ms 가 `≈1` — 틀을 16.7 배수로 맞추지 않음 | ★ **이 판(헤드리스)의 관찰** — 재량 안의 선택 |
| `scrollend` 가 같은 틀 | ★ **이 판의 관찰** — CSSOM View 는 받지 않았다 |
| `LayoutCount` 20 / 1 / 1 / 0 | ★ **이 판의 관찰**(구현의 계수기) |
| 시간 · fps | ★ **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 스크립트 애니메이션(매 틀 값이 바뀜) | rAF + `timestamp` 차로 진행 계산 | `setInterval(16)` |
| 여러 곳의 스타일 쓰기를 한 번의 레이아웃으로 | 쓰기를 모아 rAF 에서 한 번에 · 읽기는 그 전에 | 읽기 · 쓰기 교차(10편) |
| `transform` · `opacity` 만 바꾸는 움직임 | CSS 애니메이션 · Web Animations(CSS 56편 — 주 스레드가 안 돈다) | rAF 로 매 틀 `left` 쓰기 |
| 숨은 탭에서도 이어져야 하는 일 | 타이머 · 서버 쪽 · 돌아왔을 때 따라잡기 | rAF |
| 급하지 않은 뒷일 | [39번 주제](../39-idle-scheduling/2-summary.md)의 `requestIdleCallback` · `scheduler.postTask` | rAF(틀마다 예산을 먹는다) |

## 핵심 문장

1. **rAF 는 렌더링 단계 안, 스타일 · 레이아웃보다 앞에서 불린다** — `scroll` 뒤, RO · 페인트 앞, IO 알림은 그 뒤 태스크.
2. **콜백이 길어지면 다음 틀이 밀린다** — 30ms 는 `≈2`, 100ms 는 `≥5`(다섯 판 모두). 이것이 예산 초과의 증상이다.
3. **숨은 탭에서 rAF 는 멈춘다** — 명세가 숨은 문서를 렌더링에서 뺀다. 타이머는 돈다.
4. **한 틀의 rAF 들은 같은 시각을 받고, 안에서 건 rAF 는 다음 틀이다.**
5. **읽지 않고 틀에 맡기면 레이아웃은 한 번이다** — 교차 20번의 `LayoutCount` +20 이 +1 로.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 38번)
- [10번 주제](../10-layout-thrashing/2-summary.md) — 읽기 · 쓰기 교차의 정본. 그 편이 못 잰 「rAF 로 미루면」을 여기서 `LayoutCount` 로 쟀다
- [CSS 갈래 56번](../../languages/css/syntax/56-rendering-pipeline-and-will-change/2-summary.md) — 파이프라인 네 공정과 측정 도구의 정본. 여기는 그 공정 사이의 **스크립트 자리**
- [`history/web/04-브라우저-엔진.md`](../../../../history/web/04-브라우저-엔진.md) — 엔진 계보(Trident · Gecko · WebKit · Blink). **파이프라인 절은 없다** — 그쪽은 「어느 엔진이 어떻게 이어졌나」까지, 여기는 「한 틀 안에서 무엇이 먼저인가」부터
- [35번 주제](../35-intersection-observer/2-summary.md) · [36번 주제](../36-resize-observer/2-summary.md) — 같은 렌더링 단계의 관찰자 둘
- [24번 주제](../24-document-lifecycle-events/2-summary.md) — 탭 숨김(`visibilitychange`)의 정본과 「새 탭을 앞으로」 방식
- [JS 갈래 36번](../../languages/js/syntax/36-event-loop-and-microtasks/2-summary.md) — 마이크로태스크 체크포인트(도중에 붙은 것까지 비운다 — rAF 와 정반대)
- 목록의 **40번 주제**(마이크로태스크 대 태스크 대 렌더 — 폴더는 아직 없다)

## 용어 풀이

- **`requestAnimationFrame`(rAF)** — 다음 렌더링 단계에서 스타일 · 레이아웃 전에 한 번 불러 달라는 예약.
- **렌더링 단계(update the rendering)** — HTML 이 정한, 틀마다 도는 단계 목록. scroll · rAF · 스타일 · 레이아웃 · RO · IO · 그리기 순.
- **rendering opportunity** — 브라우저가 그림을 한 장 낼 수 있는 때. 모델은 명세가 강제하지 않는다.
- **틀(frame) 시각** — 같은 틀의 rAF 콜백이 모두 받는 `timestamp`.
- **프레임 예산** — 한 틀 안에서 스크립트가 쓸 수 있는 시간. 60Hz 면 16.7ms 에서 브라우저의 일을 뺀 것.
- **간격 범주** — rAF 간격을 16.7ms 의 몇 배 근처인가로 나눈 것(`≈1` · `≈2` · `3~4` · `≥5`). 이 편은 ms 대신 이것을 적는다.
- **`LayoutCount`** — CDP `Performance.getMetrics` 가 주는 레이아웃 누적 횟수.

## 더 들어가면

- **실제 화면의 주사율과 틀 떨굼** — 헤드풀 · 모니터가 있어야 한다. 이 판은 못 쟀다.
- **Long Animation Frames(LoAF)** — 긴 틀을 스크립트로 보고받는 API. 목록이 성능 측정 갈래로 보냈다.
- **숨은 탭의 긴 경향** — 0.3초 너머 몇 분을 두면 타이머 쪽도 조절된다(이 판은 던지지 않았다).
