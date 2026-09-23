# css/syntax/29 — Grid 영역: `grid-template-areas`·이름 붙은 라인 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형과 경계형 반반**이다 — **도면이 유효한가**와 **무효일 때 무엇이 보이나**가 값의 중심이라서다.
> 선행: [**27번**](../27-grid-track-sizing/)(트랙 정의) · [**28번**](../28-grid-placement/)(라인 번호 배치).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 도면을 읽는다 (예측)

```css
.g { display: grid;
     grid-template-columns: 100px 1fr;
     grid-template-rows: 32px 64px 32px;
     grid-template-areas: "hd hd"
                          "sb mn"
                          ".  ft"; }
```

- 격자는 몇 행 몇 열인가?
- `hd` 는 어느 칸들을 덮는가?
- `.` 자리에는 무엇이 놓이는가?
- 이 도면이 **트랙의 크기**를 정하는가?

### 2. 도면이 무효가 되는 세 조건 (경계)

```css
.a { grid-template-areas: "a a b" "a c c"; }
.b { grid-template-areas: "a a"   "b b b"; }
.c { grid-template-areas: "a b a"; }
```

- 셋 다 무효인가, 각각 어느 규칙을 어겼는가?
- 무효일 때 **그 줄만** 버려지는가, 선언 전체가 버려지는가?
- 무효라는 것을 어디서 확인하는가(두 자리를 말하라)?
- 「진단 3창」의 세 단계는 각각 무엇을 보는가?

### 3. 무효일 때 화면에 무엇이 보이나 (예측)

```css
.bad { grid-template-columns: repeat(3, 100px);
       grid-template-rows: 30px 30px;
       grid-template-areas: "a a b" "a c c"; }   /* 무효 */
.a { grid-area: a; } .b { grid-area: b; } .c { grid-area: c; }
```

- 항목 셋은 화면에서 사라지는가?
- 어디에 놓이는가, 셋이 서로 겹치는가?
- `gridTemplateColumns` 계산값에 무슨 일이 생기는가?
- `grid-area: a` 의 `a` 는 무엇으로 읽히게 되는가 — 네 단계로 설명하라

### 4. `.` 의 정확한 뜻 (경계)

- `.` 하나와 `...` 은 각각 몇 칸인가?
- `. . .` 은 몇 칸인가?
- `.` 자리에 `grid-area` 를 안 준 항목이 들어가는가?
- 계산값에서 `...` 은 어떻게 직렬화되는가?

### 5. 이름 붙은 라인 (예측)

```css
.g { grid-template-columns:
       [full-start] 50px [main-start] 100px 100px [main-end] 50px [full-end]; }
```

- `grid-column: main` 은 어느 칸들을 덮는가?
- `grid-column: main-start / main-end` 와 같은가?
- 이 선언의 `gridTemplateColumns` 계산값에 라인 이름이 나오는가?
- 번호로 쓰면 같은 자리를 무엇이라고 쓰는가?

### 6. `-start`/`-end` 접미사 규칙 (왜)

```css
.g { grid-template-columns: 50px [main-start] 100px 100px [main-end] 50px;
     grid-template-rows:    30px [main-start] 40px [main-end] 30px; }
.m { grid-area: main; }
```

- `grid-template-areas` 를 한 줄도 안 썼는데 `grid-area: main` 이 듣는가?
- 반대 방향(도면이 라인 이름을 만드는 것)도 성립하는가?
- `[main-start]` 만 있고 `[main-end]` 가 없으면 어떻게 되는가?
- 행 쪽 이름을 지우면 상자는 어디로 가는가?

### 7. 이름이 겹치면 (예측)

```css
.g { grid-template-columns: [hd-start] 100px [hd-end] 100px 100px;
     grid-template-areas: "x  hd hd"
                          "x  y  y"; }
.h { grid-area: hd; }
```

- 도면이 이기는가, 라인 이름이 이기는가?
- 라인 이름을 `100px [hd-start] 100px [hd-end] 100px` 로 옮기면 결과가 바뀌는가?
- 두 결과를 한 규칙으로 설명하면 무엇인가?
- 실무에서 이 상황의 처방은 무엇인가?

### 8. `grid-area` 의 네 얼굴 (경계)

- `grid-area: hd` · `grid-area: 2 / 1` · `grid-area: 2 / 1 / 3 / 3` 은 각각 무엇을 뜻하는가?
- 번호와 이름을 한 선언에 섞어 쓸 수 있는가?
- 이름 하나만 썼을 때 그 이름이 **네 축 전부**에 들어가는가?
- 그것이 3번의 「항목이 행·열 양쪽으로 밀려난다」와 어떻게 이어지는가?

### 9. 도면을 쓰는 자리와 안 쓰는 자리 (연결)

- 중단점마다 배치를 바꿀 때 도면의 무엇이 유리한가?
- 항목 수가 정해지지 않은 목록에 도면을 쓸 수 있는가?
- 도면 방식이 `order`·`dense` 보다 접근성에서 나은 이유는 무엇인가?
- 카드 내부 줄을 카드끼리 맞추는 것은 도면으로 되는가?

### 10. 무엇이 보장이고 무엇이 관찰인가 (경계)

- 「직사각형이 아니면 무효」는 명세인가 구현인가?
- 「`...` 이 계산값에서 `.` 하나로 접힌다」는 어느 쪽인가?
- 무효한 도면이 `cssRules` 에서 빈 문자열로 보이는 것은 어느 쪽인가?
- 버전이 올랐을 때 다시 찍어야 하는 칸은 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- 도면이 안 정하는 것(트랙 크기)은 목록의 몇 번 주제가 정본인가?
- `grid-area` 네 값의 순서는 몇 번 주제가 정본인가?
- 도면이 만든 라인 이름을 자식 격자가 물려받게 하려면 무엇이 필요한가?
- 「선언 하나가 통째로 버려진다」는 규칙의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
