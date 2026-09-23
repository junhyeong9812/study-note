# css/syntax/57 — `@starting-style` 과 진입·퇴장 전환: `display`/`overlay` 를 전환에 태우기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **전환이 걸리나 안 걸리나, 그것을 무엇으로 아나**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 드롭다운은 왜 열릴 때만 튀는가 (예측)

```css
.drop { display: none; opacity: 0; transition: opacity 1s linear; }
.menu:hover .drop { display: block; opacity: 1; }
```

- 마우스를 올렸을 때 상자는 1초에 걸쳐 나타나는가?
- 마우스를 뗐을 때는 어떻게 되는가?
- 두 방향이 다르다면 무엇이 그 차이를 만드는가?
- 콘솔에 에러나 경고가 찍히는가?

### 2. 한 프레임만 존재하는 상태를 무엇으로 보는가 (왜)

- `getComputedStyle` 로 시작 스타일을 볼 수 있는가?
- `document.styleSheets[0].cssRules` 에는 무엇이 보이는가?
- 「전환이 아예 시작되지 않았다」를 재현 가능하게 증명하려면 무엇을 읽어야 하는가?
- 그 값이 손으로 계산한 것이 아니라 엔진이 만든 것임을 어떻게 아는가?

### 3. 이 둘 중 어느 쪽이 전환되는가 (예측)

```css
/* d1 */  .x { opacity: 0.8; }
          @starting-style { .x { opacity: 0.2; } }

/* d2 */  @starting-style { .y { opacity: 0.2; } }
          .y { opacity: 0.8; }
```

- 두 요소 모두 `display: none` → `block` 으로 나타난다. 전환이 걸리는 쪽은 어디인가?
- 안 걸리는 쪽은 시작값이 얼마가 되는가?
- 이 결과를 명세의 어떤 문장으로 설명할 수 있는가?
- 습관으로 만들면 이 사고를 안 내는 규칙은 무엇인가?

### 4. 명시도와 중요도가 끼면 (예측)

```css
/* d3 */  @starting-style { .z { opacity: 0.2; } }   #z { opacity: 0.8; }
/* d4 */  @starting-style { #w { opacity: 0.2; } }   .w { opacity: 0.8; }
/* d5 */  @starting-style { .v { opacity: 0.2 !important; } }   .v { opacity: 0.8; }
```

- 셋 중 전환이 걸리는 것은 몇 개인가?
- `@starting-style` 안에 있다는 사실이 사다리 어디에 끼어드는가?
- 시작 스타일을 계산할 때의 우선순위를 네 단계로 적을 수 있는가?

### 5. 이미 보이는 요소에 걸면 (경계)

- 처음부터 화면에 있던 요소에 `@starting-style` 을 주고 클래스를 토글하면 시작값은 무엇이 되는가?
- 그 조건을 명세는 무엇이라고 부르는가?
- `@starting-style` 이 실제로 쓰이는 경우는 구체적으로 어떤 둘인가?

### 6. 퇴장에서 `display` 는 언제 뒤집히는가 (예측)

```css
[popover] { opacity: 1;
            transition: opacity .6s linear, display .6s allow-discrete; }
[popover]:not(:popover-open) { opacity: 0; }
```

- 이산 속성은 전환의 몇 % 지점에서 뒤집힌다고 명세가 말하는가?
- 그런데 실제로 `display` 는 몇 ms 에 `none` 이 되는가?
- 왜 그 규칙의 예외가 되는가?
- `allow-discrete` 를 빼면 마우스를 뗀 뒤 몇 ms 에 사라지는가?

### 7. `overlay` 를 빼면 무엇이 달라지는가 (경계)

- `display` 를 붙들었는데도 팝오버가 「닫히다가 뒤로 숨는」 이유는 무엇인가?
- `overlay` 의 값을 저자가 직접 지정할 수 있는가?
- 그 속성은 무엇을 붙들어 주는가?
- `overlay` 를 지원하지 않는 엔진에서는 무엇이 깨지는가?

### 8. 두 형태는 정말 같은가 (왜)

- `@starting-style { .a { … } }` 와 `.a { @starting-style { … } }` 의 결과는 같은가?
- 중첩 형태의 명시도는 무엇으로 정해지는가?
- CSSOM(`cssRules`)에서 둘은 어떻게 다르게 보이는가?

### 9. 지금 써도 되는가 (경계)

- `@starting-style`·`transition-behavior`·`overlay` 세 기능의 Baseline 은 각각 무엇인가?
- 셋 중 지원이 가장 좁은 것은 무엇이고 그 엔진은 어디인가?
- 지원 안 되는 엔진에서 이 CSS 는 깨지는가, 조용히 다르게 도는가?

### 10. 다른 주제와 잇기 (연결)

- `height: auto` 로 펴지는 아코디언에 `@starting-style` 을 주면 전환이 걸리는가?
- 전환이 도는 동안의 값을 `!important` 로 덮을 수 있는가?
- 등장할 때 여러 지점을 들르게 하려면 무엇을 써야 하는가?
- 모션에 민감한 사용자에게 이 진입·퇴장 연출을 어떻게 바꿔 주는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
