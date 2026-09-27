# web-api/36 — `ResizeObserver`: 관측 상자 세 종류와 무한 루프 경고 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 세 계열이 테두리 · `transform` 을 포함하나는 [09번 주제](../09-element-geometry/1-question.md), 관찰 시작의 첫 알림은 [35번 주제](../35-intersection-observer/1-question.md)(IO)가 물었다. 렌더링 단계 안의 순서는 [38번 주제](../38-request-animation-frame/1-question.md)다. 여기는 **무엇이 바뀌면 오나**와 **콜백 안에서 크기를 바꾸면 무엇이 나나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 명세는 **W3C Resize Observer 2020 WD 사본**과 HTML 을 받아 읽었다(편집자 초안은 못 봤다). **비용은 재지 않았다.**
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 상자 셋과 `padding` · `transform` (예측)

```js
// wa36b-36-q1.js
// 질문용 — 실행 대상 아님
// 요소: width 100px · height 50px · padding 10px · border 5px · box-sizing: content-box
for (const box of ["content-box", "border-box", "device-pixel-content-box"])
  new ResizeObserver(es => 적기(box, es[0])).observe(요소, { box });
// 첫 통지가 지나간 뒤 한 번씩(칸마다 새 요소로):
요소.style.padding = "20px";          // (가)
요소.style.transform = "scale(2)";    // (나)
// (가)·(나) 각각에서 — 세 관찰자 중 누가 불리나? 불린 쪽이 받는 크기는?
```

- (가)·(나) 각각 누가 불리고, 무엇을 받나?

### 2. 부모 폭 · 뷰포트 폭과 `resize` 이벤트 (예측)

```js
// wa36b-36-q2.js
// 질문용 — 실행 대상 아님
// .p { width: 200px } 안의 요소 { width: 50% } · 다른 판에서는 요소 { width: 10vw } (뷰포트 폭 1000)
addEventListener("resize", () => 적기("window resize"));
new ResizeObserver(() => 적기("ResizeObserver")).observe(요소);
부모.style.width = "160px";                 // (가) 부모 폭만 줄인다
// (나) 하네스가 CDP 로 뷰포트 폭을 1000 → 800 으로 바꾼다
// (가)·(나) 각각에서 — 무엇이 적히나?
```

- (가)·(나) 각각 무엇이 적히나?

### 3. 아무것도 안 바꾸고 관찰만 시작하면 (예측)

```js
// wa36b-36-q3.js
// 질문용 — 실행 대상 아님
// 관찰을 시작하기만 하고 아무것도 안 바꾼다 — 틀 세 장을 기다린다
const 대상들 = [보이는_100x50, 폭0_높이0, display_none, 문서에_안_붙인_요소];
for (const t of 대상들) {
  new ResizeObserver(es => 적기("RO", es[0].contentRect)).observe(t);
  new IntersectionObserver(es => 적기("IO", es[0].isIntersecting)).observe(t);
}
// 대상마다 — RO 의 첫 통지가 오나? 온다면 무슨 크기로? IO 는?
```

- 네 대상에서 RO · IO 의 첫 통지는?

### 4. 콜백이 관찰 대상 자신을 키울 때 (예측)

```js
// wa36b-36-q4.js
// 질문용 — 실행 대상 아님
addEventListener("error", e => 적기("error 이벤트", e.message));
let n = 0;
new ResizeObserver(() => {
  적기("콜백");
  if (n++ < 5) 요소.style.width = (100 + n) + "px";   // 관찰 대상 자신을 1px 키운다
}).observe(요소);
// 틀(렌더링 단계)마다 무엇이 적히나 — 모든 틀이 끝날 때까지?
```

- 틀마다 적히는 것은?

### 5. 자식을 키울 때와 부모를 키울 때 (예측)

```js
// wa36b-36-q5.js
// 질문용 — 실행 대상 아님
// (가) A > B > C 세 겹을 한 관찰자로 다 관찰 · A 의 높이를 한 번 바꾼다 · 콜백은 받은 요소의 「자식」 높이를 바꾼다
// (나) P > C 두 겹을 한 관찰자로 다 관찰 · C 의 높이를 한 번 바꾼다 · C 를 받은 콜백은 「부모」 P 의 폭을 바꾼다
// 각각 — 그 틀 안에서 콜백이 몇 번 불리나(받은 요소는)? error 이벤트가 나나? 다음 틀에서는?
```

- (가)·(나) 각각 그 틀과 다음 틀에서 무엇이?

### 6. 문항 4 의 `error` 리스너가 받는 것 (예측)

- 문항 4 의 `error` 리스너가 무언가를 받는다면 — 어떤 생성자의 이벤트이고 `message` 는 전문으로 무엇인가? `error` 칸은? 그리고 **개발자 콘솔**에도 찍히나 — 확인하려면 무엇을 대조로 같이 던져야 하나?

### 7. 한 틀 안의 반복을 끊는 규칙 (왜)

- 받은 사본 §3.6.1 은 한 틀 안에서 도는 RO 반복을 **무엇으로** 끊나? 그 규칙이면 왜 반드시 끝나나? 끊긴 통지는 어떻게 되나?

### 8. `devicePixelRatio` 를 CDP 로 2 로 바꿨더니 격자가 비었다 (경계)

- 그 칸이 비었다는 것에서 「RO 는 배율 변화를 못 잡는다」고 결론 내도 되나? 무엇을 대조로 던져서 무엇을 확인했나?

### 9. 0×0 인 대상과 받은 명세 사본 (경계)

- 받은 사본의 `lastReportedSizes` 초기값과 `isActive()` 로 읽으면 0×0 대상의 첫 통지는 어떻게 돼야 하나? 문항 3 의 관찰과 맞대어, 이 편은 무엇을 **판정하고** 무엇을 **판정하지 않나** — 왜?

### 10. 「RO 가 `resize` 보다 싸다」 (경계)

- 이 편이 **잰 것**과 **재지 않은 것**을 갈라 답하라.

### 11. 다른 주제와 잇기 (연결)

- [35번 주제](../35-intersection-observer/1-question.md)의 IO 와 **같은 점**(관찰 시작) 하나와 **다른 점**(무엇이 바뀌면 오나) 하나는?
- [09번 주제](../09-element-geometry/1-question.md) (9)의 「`transform` 은 한쪽에만 섞인다」에서 RO 는 **어느 쪽**을 보나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
