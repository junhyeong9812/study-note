# web-api/38 — `requestAnimationFrame` 과 프레임 예산 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 읽기 · 쓰기 교차의 비용은 [10번 주제](../10-layout-thrashing/1-question.md), 파이프라인 네 공정은 [CSS 갈래 56번](../../languages/css/syntax/56-rendering-pipeline-and-will-change/1-question.md), 마이크로태스크 줄은 [JS 갈래 36번](../../languages/js/syntax/36-event-loop-and-microtasks/1-question.md)이 물었다. 여기는 **rAF 가 렌더링 단계의 어디에 끼나**와 **틀을 넘기면 무엇이 보이나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 헤드리스 단일 엔진**의 관찰이다(모니터가 없다 — 간격은 헤드리스의 박자다). **시간은 찍지 않았다** — 간격은 범주로만.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 한 태스크에서 당긴 방아쇠 셋 (예측)

```js
// wa36b-38-q1.js
// 질문용 — 실행 대상 아님
addEventListener("scroll", () => 적기("scroll"));
new ResizeObserver(() => 적기("ResizeObserver")).observe(r);
new IntersectionObserver(es => es[0].isIntersecting && 적기("IntersectionObserver")).observe(i);   // i 는 아래쪽 화면 밖
// 한 태스크에서:
scrollTo(0, i 가_보이는_자리);
r.style.width = "140px";
requestAnimationFrame(() => 적기("rAF"));
적기("태스크 끝");
// 적히는 순서는? 렌더러의 스타일 재계산 · 레이아웃 · 페인트는 그 사이 어디에 끼나?
// (나) r.style.width 를 쓴 바로 뒤에 r.offsetWidth 를 읽으면 — 스타일 재계산 · 레이아웃이 어디로 옮겨 가나?
```

- 적히는 순서와 스타일 · 레이아웃 · 페인트의 자리는? (나)에서는?

### 2. 콜백 안의 바쁨과 간격 (예측)

```js
// wa36b-38-q2.js
// 질문용 — 실행 대상 아님
const 한장 = t => { 기록(t); 바쁨(X); requestAnimationFrame(한장); };   // 바쁨(X) = X ms 동안 동기 루프
requestAnimationFrame(한장);
// 이웃한 두 콜백이 받은 timestamp 의 차를 16.7ms 의 몇 배인가로 — ≈1 · ≈2 · 3~4 · ≥5
// X = 0 · 10 · 20 · 30 · 100 각각에서 가장 많은 범주는?
```

- X 마다 가장 많은 범주는?

### 3. 숨은 탭 · 같은 틀 · 안에서 건 rAF (예측)

```js
// wa36b-38-q3.js
// 질문용 — 실행 대상 아님
// (가) rAF 고리를 돌리다가 하네스가 새 탭을 앞으로 띄운다(이 탭은 뒤로) — 그동안 setInterval 100ms 가 세 번 울릴 때까지 rAF 는 몇 번?
// (나) 한 태스크에서 requestAnimationFrame(a) · requestAnimationFrame(b) — a 와 b 가 받는 timestamp 는 같나?
// (다) requestAnimationFrame(a) 안에서 requestAnimationFrame(b) — b 의 timestamp 는 a 와 같나 · 큰가?
```

- (가)\~(다) 각각은?

### 4. 쓰기 20번의 네 모양과 `LayoutCount` (예측)

```js
// wa36b-38-q4.js
// 질문용 — 실행 대상 아님
// 요소 20개 · CDP Performance.getMetrics 의 LayoutCount 를 일의 앞뒤(틀 두 장을 기다린 뒤)로 읽는다
for (const b of bs) { b.style.width = w + "px"; b.offsetWidth; }      // (가)
for (const b of bs) b.style.width = w + "px"; bs[0].offsetWidth;       // (나)
for (const b of bs) b.style.width = w + "px";                          // (다) 읽지 않는다
                                                                       // (라) 아무것도 안 한다
// 각각 LayoutCount 는 얼마 늘어나나?
```

- 네 모양 각각 몇씩 늘어나나?

### 5. 숨은 탭과 렌더링 단계 (왜)

- 문항 3 (가)의 결과를 명세의 update the rendering 에서 **어느 단계**가 정하나? 같은 동안 `setInterval` 은 왜 계속 울리나?

### 6. rAF 콜백 목록을 도는 방식 (왜)

- 「run the animation frame callbacks」는 콜백을 돌기 전에 **무엇을 먼저 받아 두나**? 그것이 문항 3 (다)의 결과를 어떻게 정하나? JS 36편의 마이크로태스크 체크포인트는 같은 상황(도중에 붙은 일)에서 어떻게 도나?

### 7. 「rAF 는 60fps 를 보장한다」 (경계)

- 명세는 틀의 박자에 대해 무엇을 **강제하고 무엇을 예로만** 드나? 이 편이 잰 것과 **말할 수 없는 것**을 갈라 답하라.

### 8. 가상 시간 · 헤드리스 · ms (경계)

- 이 편이 `--virtual-time-budget` 을 쓰지 않은 이유는? 간격을 ms 가 아니라 범주로 적은 이유는? 헤드리스라서 못 잰 것은?

### 9. 10편이 못 잰 것 (연결)

- [10번 주제](../10-layout-thrashing/1-question.md) (7)은 「rAF 로 미루면 싸지나」를 왜 못 쟀나? 이 편은 **무엇으로 · 어떤 수**로 답했나 — 그리고 그 수가 말하지 **않는** 것은?

### 10. 관찰자 둘과 이 줄 (연결)

- [35번 주제](../35-intersection-observer/1-question.md) (4)의 `scroll → rAF → IO` 와 [36번 주제](../36-resize-observer/1-question.md) (4)의 「틀 번호는 rAF 가 올린다」는 문항 1 의 줄 어디에 놓이나? IO 알림이 페인트 **뒤**인 이유는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
