# css/syntax/31 — 내재적 크기(`min-content`/`max-content`/`fit-content`)와 `aspect-ratio` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 「내용만큼」이 몇 px 인지, 그리고 **비율이 언제 깨지는지**를 맞히는 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 글, 네 가지 폭 (예측)

```css
/* 부모 400px, 글은 "hi javascript ok", font: 16px monospace */
.a { width: min-content; }
.b { width: max-content; }
.c { width: fit-content; }
.d { width: auto; }
```

- 네 상자의 폭을 큰 순서로 늘어놓을 수 있는가?
- `.a` 는 몇 줄이 되는가?
- `.c` 와 `.b` 의 폭이 같은 이유는 무엇인가?
- 부모를 `80px` 로 줄이면 네 값이 각각 어떻게 바뀌는가?

### 2. `fit-content` 의 공식 (왜)

- `fit-content` 를 `min-content`·`max-content`·「쓸 수 있는 공간」 세 가지로 쓴 공식은 무엇인가?
- `fit-content` 가 `max-content` 보다 커질 수 있는가?
- `fit-content` 가 `min-content` 보다 작아질 수 있는가?
- 셋 중 **부모 크기에 영향을 받는 것**은 어느 것인가?

### 3. `min-content` 를 정하는 것 (예측)

```text
① "hi javascript ok"
② "hi flex-basis ok"
③ <pre>GET /api/v1/users/12345/preferences</pre>
```

- 셋의 `min-content` 폭은 각각 대략 얼마인가 — 어느 조각이 기준인가?
- ②가 ①보다 작은 이유는 무엇인가?
- ③의 `min-content` 와 `max-content` 는 같은가 다른가, 왜 그런가?
- 「`min-content` = 가장 긴 낱말」이라는 외움이 틀리는 두 경우는?

### 4. ★ 25번의 사고가 여기서 풀린다 (연결)

- 일반 블록 자식·flex 항목·grid 항목의 `min-width` 기본값은 각각 무엇인가?
- flex 항목에서 그 기본값은 무엇으로 풀리는가?
- 그래서 `<pre>` 를 담은 flex 항목이 안 줄어드는 이유를 한 줄로 설명할 수 있는가?
- 고치는 방법 두 갈래는 무엇인가(바닥을 내리는 쪽 / 내용을 바꾸는 쪽)?

### 5. ★★ `fit-content(150px)` 는 되는가 (경계)

```css
.x { width: fit-content(150px); }
```

- 이 선언은 Chrome 151 에서 동작하는가?
- 동작하지 않는다면 **어느 단계에서** 실패하는가 — 진단 3창 중 어느 창이 답하는가?
- `getComputedStyle(x).width` 로 이것을 진단할 수 있는가?
- Baseline 은 이것에 대해 무엇이라고 하는가?
- 같은 의도를 지금 표현하는 두 줄은 무엇인가?

### 6. `width: auto` 와 `fit-content` (예측)

```css
/* 같은 글, 같은 부모(400px). 상자 종류만 다르다 */
.b1 { display: block; width: auto; }
.b2 { float: left; width: auto; }
.b3 { position: absolute; width: auto; }
.b4 { display: inline-block; width: auto; }
```

- 네 상자의 폭은 각각 몇 px 인가?
- 왜 첫째만 다른가 — `auto` 의 뜻이 상자마다 다른가?
- 「글자만큼만 넓은 배지」를 블록으로 만들려면 무엇을 쓰는가?
- 옛날에 `display: inline-block` 을 쓰던 관용구가 무엇을 대신한 것이었는가?

### 7. `aspect-ratio` 는 어느 축을 기준으로 하나 (예측)

```css
.r1 { aspect-ratio: 16/9; width: 320px; }
.r2 { aspect-ratio: 16/9; height: 90px; width: auto; }
.r3 { aspect-ratio: 16/9; }                        /* 블록, 부모 400px */
.r4 { aspect-ratio: 16/9; width: 320px; height: 200px; }
```

- 넷의 폭 × 높이는 각각 얼마인가?
- `.r4` 에서 비율은 지켜지는가 — 선언은 계산값에 남아 있는가?
- 둘 다 `auto` 인 블록(`.r3`)에서는 어느 축이 먼저 정해지는가?

### 8. ★ 비율은 언제 깨지는가 (예측)

```css
.card { aspect-ratio: 1/1; width: 120px; }
```

- 내용이 짧을 때와 아주 길 때, 상자의 높이는 각각 몇 px 인가?
- 비율이 깨지는 이유를 「내용 기반 최소 크기」라는 말로 설명할 수 있는가?
- 고치는 방법 셋은 무엇이고 **부작용이 각각 어떻게 다른가**?
- 고친 뒤 `scrollHeight` 는 120 인가 그보다 큰가 — 그것이 뜻하는 바는?
- `min-height: 200px` 를 같이 주면 무슨 일이 일어나는가?
- 이 사고가 **실서비스에서 늦게 발견되는** 이유는 무엇인가?

### 9. 유효하지 않은 값 (경계)

```css
.a1 { aspect-ratio: 0 / 1; }
.a2 { aspect-ratio: -1; }
.a3 { aspect-ratio: 1.5; }
.a4 { width: fit-content(150px); }
```

- 넷 중 `cssRules` 에 담기는 것은 무엇인가?
- 담기고도 **아무 일도 안 하는** 것이 있는가?
- `.a3` 은 계산값으로 무엇이 되는가?
- 「담겼다」와 「먹었다」를 가르는 방법은 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- `fr` 과 `minmax()` 는 목록의 몇 번 주제인가?
- `width` 가 재는 칸(내용 칸인가 테두리까지인가)은 몇 번 주제가 정본인가?
- 「어디서 줄바꿈되는가」(`word-break`·`overflow-wrap`·`hyphens`)의 정본은 몇 번 주제인가?
- `overflow-wrap: anywhere` 와 `overflow-wrap: break-word` 중 `min-content` 를 실제로 줄이는 것은 어느 쪽인가?
- 그 사실을 쓰면 25번의 사고를 `min-width: 0` 없이 고칠 수 있는가 — 대신 무엇을 잃는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
