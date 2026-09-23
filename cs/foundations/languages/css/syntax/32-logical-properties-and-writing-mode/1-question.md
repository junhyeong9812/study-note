# css/syntax/32 — 논리 속성과 글쓰기 방향(`writing-mode`·`direction`·`inline-size`) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — **똑같은 선언이 화면의 어느 방향으로 가는지**를 맞히는 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 두 축의 정의 (왜)

- 인라인 축과 블록 축은 각각 무엇인가 — 「가로/세로」를 쓰지 않고 설명할 수 있는가?
- `writing-mode` 와 `direction` 은 각각 무엇을 정하는가?
- 둘 중 **축 자체를 바꾸는 것**은 어느 쪽인가?
- `inline-size` 와 `block-size` 는 `horizontal-tb` 에서 각각 무엇으로 풀리는가?

### 2. ★ 똑같은 선언, 다섯 판 (예측)

```css
/* 자식의 선언 — 다섯 판 모두 똑같다 */
inline-size: 100px;  block-size: 40px;
margin-inline-start: 20px;  margin-block-start: 10px;
border-inline-start: 6px solid;  padding-inline-end: 8px;
```

- `horizontal-tb` + `ltr` 에서 `margin-inline-start` 는 어느 물리 마진이 되는가?
- `writing-mode: vertical-rl` 에서는?
- `direction: rtl` 에서는?
- `vertical-rl` + `direction: rtl` 에서는?
- 이 네 답을 모으면 무엇을 알 수 있는가?
- `getComputedStyle` 로 이것을 확인할 수 있는가 — 무엇이 돌아오는가?

### 3. `direction` 과 `writing-mode` 는 같은 축인가 (경계)

```text
② writing-mode: vertical-rl            -> 상자 (250, 20)
⑤ writing-mode: vertical-rl + rtl      -> 상자 (250, 66)
```

- 두 판에서 **x 가 같고 y 만 다르다**는 사실이 말해 주는 것은 무엇인가?
- 아랍어 사이트와 일본어 세로쓰기는 각각 어느 속성을 쓰는가?
- 둘을 동시에 쓸 수 있는가?
- 실무에서 RTL 은 CSS 로 켜는가 마크업으로 켜는가, 왜 그런가?

### 4. ★ 물리와 논리를 같이 쓰면 (예측)

```css
.a { margin-inline-start: 20px; margin-left: 80px; }   /* ltr */
.b { margin-left: 80px; margin-inline-start: 20px; }   /* ltr */
.c { direction: rtl; }  /* .c 의 자식에 .a 와 같은 두 선언 */
.d { margin-inline-start: 20px; margin-top: 25px; }    /* ltr */
```

- `.a` 의 `margin-left` 계산값은 무엇인가?
- `.b` 는?
- `.c` 안에서는 두 선언이 어떻게 되는가 — 하나가 지는가 둘 다 사는가?
- `.d` 는?
- 「논리와 물리는 캐스케이드로 안 싸운다」는 말은 맞는가?
- 명시도가 다르면(논리 쪽이 클래스, 물리 쪽이 타입 선택자) 어떻게 되는가?
- 이 중 **언어를 바꿨을 때 터지는** 경우는 어느 것인가?

### 5. ★ flex 의 주축이 도는가 (예측)

```css
.f { display: flex; flex-direction: row;
     justify-content: flex-start; align-items: flex-start;
     width: 200px; height: 200px; }
.v { writing-mode: vertical-rl; }   /* 이 한 줄만 다른 판 */
```

- `.f` 안의 항목 둘은 가로로 늘어서는가 세로로 쌓이는가?
- `.f.v` 안에서는?
- `vertical-lr` 이면?
- `direction: rtl` 이면?
- `flex-direction: row` 를 「가로」가 아닌 말로 다시 정의할 수 있는가?
- `.f.v` 에서 항목의 x 가 160 인 이유는 무엇인가(컨테이너 200, 항목 폭 40)?

### 6. `inset-*` (예측)

```css
.x { position: absolute; inset-block-end: 10px; inset-inline-start: 15px; }
/* 부모는 200×120 */
```

- `horizontal-tb` 에서 상자는 어디에 놓이는가 — 계산값 `left`/`top` 으로 답하라.
- `writing-mode: vertical-rl` 에서는?
- `inset: 10px` 는 논리 단축인가 물리 단축인가?
- 논리 단축의 이름 두 개는 무엇인가?

### 7. `text-align: start` / `end` (예측)

```css
/* 컨테이너 200px */
.a { text-align: start; }             /* ltr */
.b { text-align: end; }               /* ltr */
.c { direction: rtl; text-align: start; }
.d { direction: rtl; text-align: left; }
```

- 네 경우 글자는 각각 왼쪽인가 오른쪽인가?
- `.c` 와 `.d` 가 갈리는 이유는 무엇인가?
- `getComputedStyle(c).textAlign` 은 무엇을 돌려주는가 — 그것으로 어느 쪽인지 알 수 있는가?
- 2번의 `margin-inline-start` 와 무엇이 다른가?

### 8. 대응표 (경계)

- `vertical-rl` 에서 `margin-inline-start`·`margin-inline-end`·`margin-block-start`·`margin-block-end` 는 각각 어느 물리 마진이 되는가?
- `width` 와 `height` 의 논리판 이름은 각각 무엇인가?
- `left` 의 논리판은 무엇인가?
- `margin-inline` 과 `margin-block` 은 각각 어느 두 방향의 단축인가?

### 9. 유효하지 않은 것 (경계)

```css
.a { margin-inline-top: 4px; }
.b { inline-size: auto-ish; }
.c { writing-mode: sideways-rl; }
.d { inset-inline: 5px; }
```

- 넷 중 `cssRules` 에 담기는 것은 무엇인가?
- `.a` 가 버려지는 이유는 「미지원」인가 「그런 속성이 없다」인가?
- `.c` 가 담겼다는 것이 「동작한다」는 뜻인가?
- `writing-mode` 를 `transition` 에 태우면 어떻게 되는가?

### 10. 다른 주제와 잇기 (연결)

- 유니코드·문자 인코딩의 정본은 어느 폴더인가?
- [24번](../24-flexbox-axes/)이 「축이 돈다」고만 적은 자리의 **왜**는 이 문서의 어느 절인가?
- 논리와 물리가 겨루는 규칙의 정본은 몇 번 주제인가?
- `row-gap` 은 이름이 물리인데 동작은 무엇 기준인가?
- 논리 속성의 Baseline 상태는 무엇이고, 그래서 결론은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
