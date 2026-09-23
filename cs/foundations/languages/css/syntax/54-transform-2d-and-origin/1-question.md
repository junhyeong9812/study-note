# css/syntax/54 — `transform` 2D·`transform-origin`·개별 변환 속성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 답은 **좌표**다 — 「돌아간다」가 아니라 「**어느 좌표로 가는가**」를 답하라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 형제는 따라 움직이는가 (예측)

```css
b { display: inline-block; width: 80px; height: 40px; }
.t { transform: translateX(60px) scale(1.5); }   /* 셋 중 가운데에만 준다 */
```

- 세 번째 상자의 `getBoundingClientRect().left` 는 변환 없는 경우와 같은가 다른가?
- 변환한 상자의 `offsetWidth` 와 `getBoundingClientRect().width` 는 각각 얼마인가?
- 두 값이 다른 이유를 파이프라인 단계로 설명할 수 있는가?
- 변환으로 상자가 오른쪽 밖으로 나가면 문서에 가로 스크롤바가 생기는가?

### 2. 두 상자는 어디에 놓이는가 (예측)

```css
b { position: absolute; left: 100px; top: 100px; width: 80px; height: 40px; }
.tr { transform: translateX(100px) rotate(45deg); }
.rt { transform: rotate(45deg) translateX(100px); }
```

- 두 상자의 **중심** 좌표는 각각 어디인가?
- 두 중심의 세로 차이는 얼마이고, 그 값이 어디서 나오는가?
- 두 상자의 `getBoundingClientRect()` **크기**는 같은가 다른가?
- 크기만 봐서는 왜 둘을 구분할 수 없는가?
- 시계 바늘처럼 「가운데를 축으로 뻗어 나가는」 모양을 만들려면 어느 순서를 쓰는가?

### 3. 압정을 옮기면 (예측)

```css
b { position: absolute; left: 100px; top: 100px; width: 80px; height: 40px;
    transform: rotate(90deg); }
/* transform-origin 을 각각 기본 / 0 0 / right bottom 으로 준다 */
```

- `transform-origin` 을 안 적었을 때의 **계산값**은 무엇인가?
- 세 경우의 `rect.left`·`rect.top` 은 각각 어떻게 달라지는가?
- 세 경우의 `rect` **크기**는 같은가 다른가?
- `transform-origin: top right` 를 200×80 상자에 주면 계산값은 무엇으로 나오는가?

### 4. 선언 순서를 거꾸로 쓰면 (예측)

```css
.p1 { translate: 100px; rotate: 45deg; }
.p2 { rotate: 45deg; translate: 100px; }
.p3 { translate: 100px; transform: rotate(45deg); }
.p4 { transform: translateX(100px) rotate(45deg); }
```

- 넷의 `getBoundingClientRect().left` 는 각각 얼마인가?
- `.p1` 과 `.p2` 가 같은 이유는 무엇인가?
- `.p3` 이 `.p4` 와 같다는 사실에서 **개별 속성과 `transform` 의 앞뒤**를 알 수 있는가?
- `.p3` 의 `getComputedStyle(el).transform` 은 무엇을 돌려주는가?
- 명세가 정한 네 항의 합성 순서를 적을 수 있는가?

### 5. `%` 는 무엇의 절반인가 (경계)

```css
.outer  { width: 500px; }
.outer2 { width: 200px; }
b { width: 80px; transform: translateX(50%); }   /* 둘 안에 하나씩 */
```

- 두 상자의 `rect.left` 는 같은가 다른가, 몇 px 인가?
- `50%` 는 무엇의 50% 인가?
- `position: absolute; left: 50%; transform: translateX(-50%)` 가 가운데 정렬이 되는 이유를 두 기준으로 설명할 수 있는가?
- 이 「기준이 무엇인가」의 정본은 어느 주제인가?

### 6. 왜 `<span>` 은 안 움직이는가 (경계)

```css
span { transform: translateX(60px) scale(2); }
```

- `getComputedStyle(span).transform` 은 무엇을 돌려주는가?
- `getBoundingClientRect()` 는 변환 없는 `<span>` 과 같은가 다른가?
- 이 증상은 진단 3창 중 어디에서 잡히는가?
- `display: inline-block` 으로 바꾸면 어떻게 되는가?
- 같은 인라인인데 `<img>` 는 왜 움직이는가?

### 7. `transform` 하나에 딸려 오는 것 (연결)

```css
.wrap { transform: translateZ(0); }
```

- 이 선언이 **만드는** 것 둘은 무엇인가?
- `.wrap` 안에 `position: fixed` 자식이 있으면 무슨 일이 일어나는가, 그 정본은 어느 주제인가?
- 이 선언이 **안 만드는** 것 하나는 무엇인가?
- `.wrap` 안에 `float` 자식이 있을 때 `.wrap` 의 높이는 어떻게 되는가?
- 세 가지(쌓임 맥락·포함 블록·BFC)가 같은 축이 아니라는 것을 어떻게 확인했는가?

### 8. 계산값에서 각도를 읽을 수 있는가 (왜)

```css
.a { transform: rotate(30deg); }
.b { transform: translateX(30px) rotate(30deg) scale(2, .5); }
.c { rotate: 30deg; }
```

- 셋의 `getComputedStyle(el).transform` 은 각각 무엇인가?
- `matrix(a, b, c, d, e, f)` 의 여섯 수는 각각 무엇을 뜻하는가?
- `.b` 의 계산값에서 「`rotate(30deg)` 를 썼다」를 되읽을 수 있는가?
- JS 로 현재 각도를 알아야 한다면 무엇을 쓰는 편이 나은가?

### 9. 이 호버는 왜 이동을 잃는가 (경계)

```css
.a       { transform: translateX(50px); }
.a:hover { transform: rotate(10deg); }
```

- 호버했을 때 상자는 어디에 있는가?
- `transform` 이 누적되지 않는 이유는 무엇인가?
- 이동을 유지하면서 회전만 더하는 방법 두 가지를 들 수 있는가?
- 애니메이션에서 이 문제가 특히 자주 나는 이유는 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- 같은 이동을 `left` 로 만들 때와 `transform` 으로 만들 때 무엇이 다른가, 정본은 어느 주제인가?
- 애니메이션에서 회전과 이동을 따로 제어하고 싶다면 무엇을 쓰는가?
- `scale(0)` 으로 요소를 숨기면 그 자리는 어떻게 되는가?
- 3D 함수를 하나라도 쓰면 계산값의 형태가 어떻게 바뀌는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
