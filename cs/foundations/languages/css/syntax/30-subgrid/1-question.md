# css/syntax/30 — `subgrid`: 부모 트랙을 자식이 잇는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 특히 **`getComputedStyle` 이 무엇을 돌려주나**가 다른 Grid 주제와 갈리는 자리라 그것을 많이 묻는다.
> 선행 셋: [**27번**](../27-grid-track-sizing/)(트랙 정의) · [**28번**](../28-grid-placement/)(`span`) · [**29번**](../29-grid-template-areas/)(라인 이름).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 왜 중첩 격자로는 안 되나 (왜)

```css
.row  { display: grid; grid-template-columns: 1fr 1fr;
        grid-template-rows: auto auto; }
.card { display: grid; grid-row: span 2; grid-template-rows: auto auto; }
/* 카드 둘: 왼쪽은 제목이 한 줄, 오른쪽은 두 줄 */
```

- 두 카드의 「본문」은 같은 줄에 놓이는가?
- 안 놓인다면 그 이유를 「격자가 몇 개인가」로 설명할 수 있는가?
- 어긋난 정도를 무엇으로 재는가?
- `align-items` 를 써서 해결할 수 있는가?

### 2. `subgrid` 가 하는 일 (왜)

- `subgrid` 는 「줄을 맞춰 주는 기능」인가?
- 한 문장으로 말하면 무엇을 하는 기능인가?
- 위 예제에 `grid-template-rows: subgrid` 를 주면 부모의 행 크기는 그대로인가?
- 그 변화가 「맞춰지는」 메커니즘과 어떻게 이어지는가?

### 3. 성립 조건 셋 (경계)

- `subgrid` 가 뜻을 가지려면 무엇이 셋 갖춰져야 하는가?
- 셋 중 빠졌을 때 **계산값에 안 드러나는** 것은 어느 것인가?
- 부모가 격자가 아니면 계산값은 무엇이 되는가?
- `grid-row: span N` 을 안 줬을 때 카드 안의 제목과 본문은 어떻게 되는가?

### 4. 계산값이 무엇을 돌려주나 (예측)

```css
.outer { display: grid; grid-template-columns: 100px 100px 100px 100px; }
.sub   { display: grid; grid-column: 2 / 4; grid-template-columns: subgrid; }
```

- `getComputedStyle(.sub).gridTemplateColumns` 는 무엇을 돌려주는가?
- px 이 나오는가?
- 대괄호 개수는 무엇을 뜻하는가?
- 실제 트랙 폭이 궁금하면 어디를 읽어야 하는가?

### 5. 덮는 만큼만 (예측)

- 위 `.sub` 에 항목 셋을 넣으면 셋째는 어디에 놓이는가?
- `grid-column: 2 / 4` 를 `1 / -1` 로 바꾸면 계산값과 배치가 어떻게 바뀌는가?
- `grid-template-columns: subgrid` 를 지우면 항목 셋은 어떻게 놓이는가?
- 이 세 결과의 차이를 무엇으로 확인했는가?

### 6. `gap` (예측)

```css
.outer { display: grid; gap: 30px; grid-template-columns: 100px 100px 100px; }
.sub   { display: grid; grid-column: 1 / -1; grid-template-columns: subgrid; }
.z     { column-gap: 0; }   /* .sub 에 더한 것 */
```

- `.sub` 의 `columnGap` 계산값은 무엇인가?
- 그런데 화면의 간격은 얼마인가?
- `.z` 처럼 `column-gap: 0` 을 주면 트랙 폭은 어떻게 되는가?
- 왜 그렇게 되는가 — 부모의 `gap` 자리는 어디로 갔는가?

### 7. 라인 이름 (예측)

```css
.outer { grid-template-columns: [a] 100px [b] 100px [c] 100px [d]; }
.sub   { display: grid; grid-column: 1 / -1; grid-template-columns: subgrid; }
.m     { grid-column: b; }
```

- `.m` 은 어디에 놓이는가?
- `.sub` 의 계산값에 `[b]` 라는 이름이 보이는가?
- 안 보인다면 빈 대괄호는 무슨 뜻인가?
- 서브그리드가 **자기 이름**을 더하면 계산값은 어떻게 되는가?

### 8. 진단 (경계)

- 「`subgrid` 를 썼는데 여전히 어긋난다」에서 가장 먼저 읽을 값은 무엇인가?
- 계산값이 `none`·`subgrid [] []`·`38px 19px` 셋이면 각각 무슨 뜻인가?
- 가장 흔한 원인은 무엇인가?
- 이 진단은 [27번](../27-grid-track-sizing/)의 「진단 3창」과 무엇이 다른가?

### 9. 무효한 형태 (경계)

- `grid-template-rows: subgrid 100px` 은 유효한가?
- 그것을 어떻게 확인했는가?
- `subgrid` 뒤에 붙일 수 있는 것은 무엇인가?
- 두 축 다 서브그리드로 만들려면 어떻게 쓰는가?

### 10. 언제 쓰고 언제 안 쓰나 (연결)

- 이 기능의 본래 자리 두 가지를 들 수 있는가?
- 중첩 격자로 충분한 경우는 언제인가?
- `display: contents` 로 래퍼를 없애는 옛 기법과 무엇이 다른가?
- 그 옛 기법이 못 하는 것은 무엇인가?

### 11. 버전과 보장 (경계)

- `subgrid` 의 Baseline 은 무엇이고 언제부터인가?
- Grid 본체와 얼마나 차이가 나는가?
- 「`gap` 을 물려받는다」는 명세인가 구현인가?
- 「계산값이 `subgrid [] [] []` 형태로 온다」는 어느 쪽인가?

### 12. 다른 주제와 잇기 (연결)

- `subgrid` 의 전제가 되는 `span` 의 정본은 몇 번 주제인가?
- 라인 이름과 도면의 정본은 몇 번 주제인가?
- `gap` 의 정본은 몇 번 주제이고 여기서는 무엇까지만 다루는가?
- 「정렬로는 이 문제가 안 풀린다」에서 정렬의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
