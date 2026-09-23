# css/syntax/59 — 뷰 전환: `view-transition-name`·`::view-transition-*` 의사 요소 트리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 「무슨 의사 요소가 몇 개 생기나」와 「실패했을 때 어디에 나타나나」를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 전환에서 의사 요소는 몇 개 생기는가 (예측)

```html
<div id="card">카드</div>   <!-- view-transition-name: card -->
<div id="plain">다른 것</div>  <!-- 이름 없음 -->
```

```js
document.startViewTransition(() => { card.classList.add('big'); plain.classList.add('big'); });
```

- `document.getAnimations()` 의 `pseudoElement` 를 전부 뽑으면 몇 종이 나오는가?
- `#plain` 은 어느 의사 요소에 들어가는가?
- 아무것도 안 바뀌는 대상에도 애니메이션이 만들어지는가?
- 이름을 지우면 의사 요소가 몇 종으로 줄어드는가?

### 2. 트리를 그릴 수 있는가 (왜)

- 다섯 종류의 의사 요소를 부모-자식 관계로 그릴 수 있는가?
- 위치·크기를 애니메이션하는 것은 어느 층인가?
- 사라짐·나타남(불투명도)을 맡는 것은 어느 층인가?
- `image-pair` 가 `isolation: isolate` 를 쓰는 이유는 무엇인가?

### 3. `duration` 을 어디에 주는가 (예측)

```css
::view-transition-group(card) { animation-duration: 1s; }
```

- 이 선언만 했을 때 `::view-transition-old(card)` 의 `animation-duration` 계산값은 얼마인가?
- `animation-duration` 은 상속되는 속성인가?
- 그렇다면 왜 따라오는가?
- `::view-transition-group(root)` 은 어떻게 되는가?

### 4. 기본 전환의 이징은 무엇인가 (경계)

- 기본 지속 시간은 얼마인가?
- `effect.getTiming().easing` 과 `effect.getKeyframes()[0].easing` 이 다르게 나온다면 어느 쪽이 실제로 도는가?
- 실제 값이 등속인지 아닌지를 무엇으로 판정했는가?

### 5. 같은 이름이 둘이면 (예측)

```js
other.style.viewTransitionName = 'card';     // card 는 이미 다른 요소가 쓰고 있다
const vt = document.startViewTransition(() => { card.classList.toggle('big'); });
```

- `vt.ready` 는 resolve 되는가 reject 되는가, 된다면 무슨 오류인가?
- `vt.updateCallbackDone` 과 `vt.finished` 는 각각 어떻게 되는가?
- DOM 변경은 적용되는가?
- 화면에서 이 실패를 알아챌 수 있는가?

### 6. 일부러 건너뛴 것과 구별할 수 있는가 (경계)

- `vt.skipTransition()` 을 부르면 `ready` 는 무슨 오류로 reject 되는가?
- 이름 충돌로 죽은 경우와 오류 이름이 같은가?
- 두 경우 모두 `finished` 는 어떻게 되는가?

### 7. 전환 중에 진짜 요소는 어떤 상태인가 (예측)

- 전환이 도는 동안 `getComputedStyle(card).width` 는 옛 값인가 새 값인가?
- `card.getBoundingClientRect()` 는?
- `visibility` 는 어떻게 되어 있는가?
- 그렇다면 「지금 전환 중인가」를 무엇으로 판정해야 하는가?

### 8. 멈추는 구간은 어디인가 (왜)

- `startViewTransition()` 을 부르면 콜백은 같은 프레임에 실행되는가?
- 콜백 안에서 잰 좌표는 옛 것인가 새 것인가?
- 그렇다면 「멈추는 것」은 정확히 무엇인가?
- 콜백 안에서 서버 응답을 기다리면 화면에 무엇이 보이는가?

### 9. 지금 써도 되는가 (경계)

- 같은 문서 뷰 전환의 Baseline 은 무엇이고 언제 그렇게 됐는가?
- 문서 간 전환(`@view-transition`)의 Baseline 은 무엇이고 빠진 엔진은 어디인가?
- 둘을 같은 기능으로 다루면 안 되는 이유는 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- 같은 요소가 제자리에서 색만 바뀌는 경우에도 뷰 전환을 써야 하는가?
- 전환 중의 겹침 순서는 문서의 `z-index` 를 따르는가?
- 뷰 전환의 진행률은 시간에서 오는가 스크롤에서 오는가?
- 모션에 민감한 사용자에게 뷰 전환은 왜 특히 조심할 대상인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
