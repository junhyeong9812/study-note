# css/syntax/58 — 스크롤 연동 애니메이션: `animation-timeline`·`scroll()`/`view()`·`timeline-scope` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 「스크롤 몇 px 에서 값이 얼마인가」와 「안 움직일 때 어떤 모양으로 안 움직이나」를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 막대는 다르게 움직이는가 (예측)

```css
@keyframes grow { from { width: 0 } to { width: 100% } }
.bar { animation-name: grow; animation-timing-function: linear;
       animation-fill-mode: both; animation-timeline: scroll(root block); }
#b1 { animation-duration: auto }
#b2 { animation-duration: 1s }
#b3 { animation-duration: 100s }
```

- 문서 높이 3000·뷰포트 357 일 때 `scrollY = 250` 에서 세 막대의 폭은 각각 얼마인가?
- 세 값이 같다면 그 값은 무엇으로 계산된 것인가?
- 이 애니메이션 객체의 `currentTime` 을 읽으면 어떤 단위가 나오는가?
- 그렇다면 속도를 바꾸려면 무엇을 건드려야 하는가?

### 2. 안 움직이는 네 가지는 서로 다른가 (예측)

```css
/* 기본 너비 40px · 키프레임 from 0 to 200px · fill-mode: both */
#t2 { animation-timeline: scroll(root inline) }   /* 가로 스크롤이 없다 */
#t3 { animation-timeline: none }
#t6 { animation-timeline: --nope }                /* 그런 이름이 없다 */
#t7 { animation-timeline: scroll(self block) }    /* 자기는 스크롤 컨테이너가 아니다 */
```

- 넷 중 화면에 `40px` 로 보이는 것과 `200px` 로 보이는 것은 각각 어느 것인가?
- 「끝 상태로 박히는」 쪽은 왜 그렇게 되는가?
- `getAnimations()[0].timeline` 과 `.currentTime` 을 읽으면 두 무리가 어떻게 갈리는가?
- `animation-fill-mode` 를 `none` 으로 바꾸면 무엇이 달라지는가?

### 3. `view()` 의 0% 는 어느 스크롤 위치인가 (예측)

```text
스크롤포트 높이 300 · 요소 높이 100 · 요소가 내용 맨 위에서 600 지점
```

- 진행률 0% 와 100% 가 되는 `scrollTop` 은 각각 얼마인가?
- 구간의 길이는 무엇과 무엇의 합인가?
- `scrollTop = 0` 에서 진행률을 읽으면 무엇이 나오는가?
- 명세는 0%/100% 에 대해 어떤 단서를 달아 두었는가?

### 4. `view-timeline-inset` 이 왜 안 먹는가 (경계)

```css
.card { animation-timeline: view(); view-timeline-inset: 50px; }
```

- 이 선언에서 inset 은 적용되는가?
- 계산값을 읽으면 `view-timeline-inset` 은 무엇으로 나오는가?
- 같은 효과를 내려면 어떻게 써야 하는가(두 가지)?
- 이 실패가 「에러가 없는 언어」의 어느 유형인가?

### 5. 스크롤러 밖의 막대 (예측)

```css
#wrap { timeline-scope: --sc; }
#sc   { overflow-y: auto; scroll-timeline-name: --sc; }   /* #wrap 의 자식 */
#outA { animation-timeline: --sc; }                       /* #wrap 의 자식 */
#outB { animation-timeline: scroll(nearest block); }      /* #wrap 의 자식 */
#farA { animation-timeline: --sc; }                       /* #wrap 밖 */
```

- 셋 중 실제로 움직이는 것은 무엇인가?
- 안 움직이는 둘은 각각 어떤 모양으로 안 움직이는가?
- `timeline-scope` 를 지우면 `#outA` 는 어느 쪽이 되는가?
- `timeline-scope` 는 타임라인을 만드는가?

### 6. `scroll()` 의 인자 (왜)

- 인자를 둘 다 생략하면 무엇으로 해석되는가?
- `nearest` 는 자기 자신을 포함하는가?
- `block`/`inline` 과 `y`/`x` 는 언제 갈리는가?
- 붙을 스크롤 컨테이너가 하나도 없으면 무슨 일이 일어나는가?

### 7. 만드는 속성과 쓰는 속성 (경계)

- 타임라인을 **만드는** 속성과 **쓰는** 속성의 이름을 각각 들 수 있는가?
- `scroll-timeline-name` 이 붙은 요소의 이름은 누구에게 보이는가?
- `view()` 에 `nearest`/`root`/`self` 자리가 없는 이유는 무엇인가?

### 8. 지금 써도 되는가 (경계)

- 이 기능의 Baseline 은 무엇이고, 빠져 있는 엔진은 어디인가?
- 그 엔진에서 `animation-timeline: scroll(root)` 선언은 어떻게 되는가?
- 그래서 어떤 연출에는 써도 되고 어떤 연출에는 쓰면 안 되는가?

### 9. 대체 수단과의 관계 (연결)

- `scroll` 이벤트나 `IntersectionObserver` 로 같은 연출을 만들 수 있는가?
- CSS 쪽이 공짜로 주는 것 세 가지를 들 수 있는가?
- 「더 빠르다」고 말하려면 무엇을 재야 하는가?

### 10. 다른 주제와 잇기 (연결)

- `transition` 을 스크롤에 묶을 수 있는가?
- 스크롤 컨테이너가 무엇인지는 어느 주제가 정본인가?
- 모션에 민감한 사용자에게 스크롤 연동 연출은 안전한가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
