# web-api/35 — `IntersectionObserver`: 루트·`rootMargin`·`threshold` 와 지연 로딩 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — `getBoundingClientRect()` 로 「화면 안에 있나」를 직접 재는 것은 [09번 주제](../09-element-geometry/1-question.md), `scroll` 리스너와 passive 는 [19번 주제](../19-passive-and-scroll/1-question.md)가 물었다. 마크업 쪽 `loading="lazy"` 는 **HTML 갈래 34번**(폴더는 아직 없다)이다. 여기는 **콜백이 언제 · 무엇을 들고 오나**와 **root·여백이 무엇을 바꾸나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다(`innerHeight` 713). **명세 원문은 이 판에서 열지 못했다. 비용은 재지 않았다.** 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 안 보이는 요소를 `observe` 하면 (예측)

```js
// wa32b-35-q1.js
// 질문용 — 실행 대상 아님
// 요소는 뷰포트 바닥보다 300px 아래에 있다(보이지 않는다)
const io = new IntersectionObserver(es => 적기(es.length, es[0].isIntersecting, es[0].intersectionRatio));
io.observe(요소);
// 스크롤하지 않고 기다리면 — 콜백이 오나? 온다면 무엇을 적나?
```

- 콜백이 오나? 온다면 무엇을?

### 2. 뷰포트보다 큰 요소와 `threshold` (예측)

```js
// wa32b-35-q2.js
// 질문용 — 실행 대상 아님
// 요소 높이 1200px · 뷰포트 높이 713px
new IntersectionObserver(콜백, { threshold: 1 }).observe(요소);
// 아래 300 밖 → 아래 100 밖 → 위 100 들어옴 → 바닥에서 50 위까지 → 맨 위에 붙음 → 위로 100 지나감
// 관찰 시작 뒤 여섯 자리에서 — 콜백이 오는 자리는? threshold 를 0.5 로 바꾸면?
```

- 콜백이 오는 자리는? 0.5 로 바꾸면?

### 3. 음수 `rootMargin` 과 비율 (예측)

```js
// wa32b-35-q3.js
// 질문용 — 실행 대상 아님
// 요소 300×200 · 왼쪽 끝이 뷰포트 왼쪽 끝에 붙어 있다 · 뷰포트 폭은 요소보다 넓다
new IntersectionObserver(콜백, { threshold: 0, rootMargin: "-50px" }).observe(요소);
// 요소의 위 100px 이 뷰포트 바닥 위로 들어온 자리에서 — intersectionRatio 는?
// rootMargin 을 "0px" · "200px" 로 바꾸면 그 자리에서 무엇이 오나?
```

- 그 자리의 비율은? 여백을 바꾸면?

### 4. `scroll` · rAF · IO 의 순서와 호출 수 (예측)

```js
// wa32b-35-q4.js
// 질문용 — 실행 대상 아님
addEventListener("scroll", () => 적기("scroll"), { passive: true });
new IntersectionObserver(() => 적기("IO"), { threshold: [0, 0.25, 0.5, 0.75, 1] }).observe(요소);
적기("scrollTo 부름");
scrollTo(0, y);                      // 요소가 보이기 시작하는 자리
적기("scrollTo 돌아옴");
requestAnimationFrame(() => 적기("rAF"));
// 적히는 순서는?
// 그리고 — 휠 제스처 한 번으로 1200px 을 굴리는 동안 scroll 리스너와 IO 콜백 중 어느 쪽이 더 많이 불리나?
```

- 적히는 순서는? 더 많이 불리는 쪽은?

### 5. root 가 `overflow` 상자일 때 (예측)

```js
// wa32b-35-q5.js
// 질문용 — 실행 대상 아님
// 300px 높이 overflow:auto 상자 안 · 요소는 상자 안쪽 500px 자리(높이 100) · 상자는 뷰포트 안에 통째로 보인다
new IntersectionObserver(적기("root=상자"),   { root: 상자, rootMargin: "100px" }).observe(요소);
new IntersectionObserver(적기("root=뷰포트"), { rootMargin: "100px" }).observe(요소);
// 상자.scrollTop = 0 → 150 → 300 → 700 — 자리마다 어느 관찰자가 무엇을 적나?
```

- 네 자리에서 두 관찰자가 적는 것은?

### 6. iframe 안의 `rootMargin` (예측)

```js
// wa32b-35-q6.js
// 질문용 — 실행 대상 아님
// 같은 출처 iframe 하나와 다른 출처 iframe 하나를 뷰포트 바닥 아래 100px 에 둔다
// 각 iframe 안에서(root 를 안 준다 — 최상위 뷰포트)
new IntersectionObserver(첫알림, { rootMargin: "0px" }).observe(요소);
new IntersectionObserver(첫알림, { rootMargin: "200px" }).observe(요소);
// 두 iframe 의 네 첫 알림 — isIntersecting 은?
```

- 네 첫 알림의 `isIntersecting` 은?

### 7. 겹치는데 `isIntersecting` 이 `false` 인 자리 (왜)

- 격자에서 **비율이 0 보다 큰데** `isIntersecting` 이 `false` 로 온 칸이 있다면, 그 칸들의 관찰자에게 공통으로 없는 것은? 이 편은 그것이 명세대로라고 **주장하나**? 그래서 코드에서는 무엇으로 「보이나」를 판단하나?

### 8. 「IO 는 스크롤 리스너보다 싸다」 (경계)

- 이 편이 **잰 것**과 **재지 않은 것**을 갈라 답하라. 바꾼 창(호출 수)이 못 보는 것은?

### 9. 노출 집계 — 「50% 이상이 1초」 (경계)

- IO 콜백만으로 셀 수 없는 이유는? 그 형태에 가시성(`visibilityState`)을 같이 넣은 이유는?

### 10. 다른 주제와 잇기 (연결)

- [09번 주제](../09-element-geometry/1-question.md) (10)의 「`scroll` 마다 `getBoundingClientRect()`」 방식과 IO 는 **언제 알려 주나**가 어떻게 다른가? 매 프레임 값이 필요한 일(패럴랙스)에는 어느 쪽인가?
- 무한 스크롤 목록이 스크롤 상자 안에 있을 때 root 를 무엇으로 주나 — 문항 5의 어느 줄이 근거인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
