# css/syntax/60 — `prefers-reduced-motion` 과 모션 접근성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **판단형이 섞인다** — 「어떻게 되나」뿐 아니라 「무엇을 남기고 무엇을 없애나」를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 선호를 켜면 이 애니메이션은 멈추는가 (예측)

```css
@keyframes slide { from { transform: translateX(0) } to { transform: translateX(200px) } }
#a { animation: slide 1s linear infinite; transition: transform 1s linear; }
```

- 사용자가 「동작 줄이기」를 켠 판에서 `getComputedStyle(a).animationName` 은 무엇인가?
- 실행 중인 애니메이션 개수는 몇 개인가?
- 그렇다면 브라우저는 이 선호로 무엇을 하는가?
- 테스트에서 이 결과를 보고 무엇이라 오해하기 쉬운가?

### 2. `reduce` 는 정확히 무엇을 요청하는가 (왜)

- 명세는 이 기능이 무엇을 감지한다고 쓰는가 — 어떤 형용사가 붙어 있는가?
- `reduce` 값의 설명에서 동사 두 개는 무엇인가?
- 대상이 되는 움직임은 어떤 사람들에게 무엇을 일으키는 것인가?
- 그렇다면 「모든 애니메이션 끄기」는 왜 요청의 오역인가?

### 3. 전면 차단은 무엇을 죽이는가 (예측)

```css
@media (prefers-reduced-motion: reduce) {
  #b { animation: none !important; transition: none !important; }
}
```

- 선호를 켠 판에서 `#b` 의 `transition-property` 계산값은 무엇이 되는가?
- 그 결과 사용자가 잃는 것은 무엇인가?
- 그래도 이 패턴이 쓸모 있는 경우가 있는가?

### 4. 무엇을 남기고 무엇을 없애나 (경계)

- 없애야 할 움직임 네 가지를 들 수 있는가?
- 남겨야 할 움직임 세 가지를 들 수 있는가?
- 둘을 가르는 기준 두 가지는 무엇인가?
- 불투명도 전환이 특별대우를 받는 이유는 무엇인가?

### 5. 두 형태 중 어느 쪽이 나은가 (왜)

```css
/* ① */  .card { transform: … }
         @media (prefers-reduced-motion: reduce) { .card { transform: none } }
/* ② */  .card { /* 정적 */ }
         @media (prefers-reduced-motion: no-preference) { .card { transform: … } }
```

- 새 애니메이션을 추가하면서 미디어 쿼리를 깜빡했을 때 각각 어떻게 되는가?
- `no-preference` 는 「움직여 달라」는 뜻인가?
- 선호가 「둘 다 아님」인 상태가 존재하는가 — 39번 주제의 `prefers-color-scheme` 과 같은가?

### 6. `scroll-behavior: smooth` 는 꺼지는가 (예측)

```css
html { scroll-behavior: smooth; }
```

- 선호를 켠 판에서 앵커 링크 이동은 즉시 점프하는가, 부드럽게 가는가?
- `scrollTo({ behavior: 'smooth' })` 는 어떻게 되는가?
- 고치려면 무엇을 써야 하고, 그것은 실제로 먹는가?

### 7. 이 기능이 못 막는 것 (경계)

- CSS 밖에 있어서 이 미디어 쿼리가 닿지 않는 것 네 가지를 들 수 있는가?
- 자동재생 영상은 어떻게 막는가?
- 스크롤 연동 애니메이션(58번)은 안전한가, 왜 그렇게 판단하는가?

### 8. WCAG 는 무엇을 요구하는가 (경계)

- 2.3.3 Animation from Interactions 의 요구 문장과 등급은 무엇인가?
- 그 기준이 `prefers-reduced-motion` 을 쓰라고 지정하는가?
- 같은 요구를 만족시키는 다른 수단은 무엇인가?
- 2.2.2 Pause, Stop, Hide 는 무엇에 대한 몇 등급 기준인가?

### 9. 측정은 어떻게 하는가 (연결)

- 이 환경에서 선호를 켜는 수단 두 가지는 무엇인가?
- 측정을 시작하기 전에 무엇부터 확인해야 하는가?
- 두 판을 비교할 때 조용히 틀린 결론이 나올 수 있는 함정 하나를 들 수 있는가?

### 10. 다른 주제와 잇기 (연결)

- 선호 미디어 기능 일반의 정본은 어느 주제인가, 이 주제는 그중 무엇만 다루는가?
- 뷰 전환(59번)을 `reduce` 에서 어떻게 바꾸는가?
- 진입·퇴장 전환(57번)을 `reduce` 에서 어떻게 바꾸는가?
- 다른 주제의 demo 블록에 `prefers-reduced-motion` 을 넣지 않는 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
