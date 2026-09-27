# css/syntax/25 — `flex` 단축의 세 값(`grow`/`shrink`/`basis`)과 크기 해결 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **칸이 몇 픽셀이 될지 손으로 계산할 수 있는지**를 묻는다.
> 계산이 필요한 문항은 **숫자를 끝까지 내 보라.** 「비슷하게 나뉜다」는 답이 아니다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `flex: 1` 과 `flex: auto` 는 몇 픽셀로 갈리는가 (예측)

```css
/* 컨테이너 600px. 항목 셋의 내용 크기는 8.02 / 32.02 / 96.02 px 다. */
.one i { flex: 1; }
.two i { flex: auto; }
```

- `.one` 의 세 칸은 각각 몇 px 인가?
- `.two` 의 세 칸은 각각 몇 px 인가 — 계산 과정을 쓸 수 있는가?
- 두 결과가 갈리는 원인이 되는 값은 세 값 중 **어느 하나**인가?
- 「탭 넷을 폭이 똑같게」가 목적이면 둘 중 무엇을 쓰는가?

### 2. 단축의 한 값 축약 (경계)

- `flex: 1` · `flex: auto` · `flex: none` 은 각각 세 롱핸드로 무엇인가?
- 아무것도 안 썼을 때의 초기값은 무엇인가?
- `flex: 30px` 은 세 롱핸드로 무엇인가 — 왜 `flex: 1` 과 자리가 다른가?
- `flex: 0%` 의 `flex-grow` 는 0 인가 1 인가, 왜 그런가?
- `flex: 1` 과 `flex-grow: 1` 은 같은 뜻인가?

### 3. 남는 공간은 어떻게 나뉘는가 (예측)

```css
/* 컨테이너 900px */
i:nth-child(1) { flex: 1 1 100px; }
i:nth-child(2) { flex: 1 1 200px; }
i:nth-child(3) { flex: 1 1 300px; }
```

- 자유 공간은 몇 px 인가?
- 세 칸의 최종 폭은 각각 몇 px 인가?
- `flex-grow` 를 `1 / 2 / 3` 으로 바꾸면 결과가 어떻게 되는가?
- `flex-grow` 는 `flex-basis` 에 비례해 가중되는가?

### 4. 모자라는 공간은 어떻게 깎이는가 (예측)

```css
/* 컨테이너 300px, 항목에 min-width: 0 이 이미 걸려 있다 */
i:nth-child(1) { flex: 0 1 100px; }
i:nth-child(2) { flex: 0 1 200px; }
i:nth-child(3) { flex: 0 1 300px; }
```

- 세 칸의 최종 폭은 각각 몇 px 인가?
- `flex-shrink` 가 셋 다 1 로 같은데 왜 깎이는 양이 다른가?
- basis 를 셋 다 200px 로 두고 `flex-shrink` 만 `1 / 2 / 3` 으로 주면 어떻게 되는가?
- 셋 중 하나에 `flex-shrink: 0` 이 있으면 그 칸은 어떻게 되는가?

### 5. ★ 본문이 컨테이너를 뚫는다 (예측)

```html
<div class="c">
  <div class="side">side</div>
  <div class="main"><pre>GET /api/v1/users/12345/preferences</pre></div>
</div>
<style>
  .c { display: flex; width: 300px; }
  .side { flex: 0 0 100px; }
  .main { flex: 1; }
</style>
```

- `.main` 의 폭은 200px 인가, 아니면 다른 값인가?
- `.main` 의 오른쪽 끝은 컨테이너 안인가 밖인가?
- `flex-shrink` 는 일을 하고 있는가, 안 하고 있는가?
- 이것을 고치는 한 줄은 무엇이고, 그 한 줄이 실제로 바꾸는 것은 무엇인가?
- `<pre>` 대신 평범한 문단이었다면 결과가 달랐겠는가, 왜 그런가?
- `flex-direction: column` 에서 같은 사고가 나면 고칠 속성 이름은 무엇인가?

### 6. `min-width` 의 기본값은 무엇인가 (왜)

- 일반 블록 상자와 flex 항목의 `min-width` 기본값은 각각 무엇인가?
- flex 항목에서 그 기본값은 무엇으로 풀리는가?
- 그 값이 「가장 긴 낱말의 폭」이 되는 경우와 「한 줄 전체의 폭」이 되는 경우를 가르는 것은 무엇인가?
- `getComputedStyle(el).minWidth` 로 이 사고를 진단할 수 있는가?

### 7. `width` 를 줬는데 안 먹는다 (경계)

```css
.item { flex: 0 0 50px; width: 100px; }
```

- 이 칸의 폭은 몇 px 인가?
- `flex: 0 0 auto; width: 100px` 이면 몇 px 인가?
- `flex-direction: column` 일 때 `flex-basis` 가 겨루는 상대는 `width` 인가 `height` 인가?
- `flex-basis: 100px` 인 항목에 `padding: 0 20px` 를 주면 바깥 폭은 몇 px 인가 — `box-sizing` 두 모드로 답하라.

### 8. `getComputedStyle` 은 무엇을 돌려주는가 (연결)

```css
.a { flex: 0 1 50%; }
.b { flex: 0 1 10em; }
```

- `getComputedStyle(a).flexBasis` 는 `50%` 인가 픽셀인가?
- `getComputedStyle(b).flexBasis` 는 `10em` 인가 픽셀인가 — 둘이 다른 이유는 무엇인가?
- 그 값이 그 칸의 실제 폭과 같다고 말할 수 있는가?
- 실제 폭을 알려면 무엇을 써야 하는가?

### 9. 상한에 걸린 항목이 섞이면 (예측)

```css
/* 컨테이너 600px */
i { flex: 1 1 0; }
i:nth-child(1) { max-width: 50px; }
```

- 세 칸의 폭은 각각 몇 px 인가?
- 「`flex: 1` 을 똑같이 줬는데 폭이 다르다」의 원인 두 가지는 무엇인가?
- `flex-grow` 세 값의 합이 1 보다 작으면(예: `0.2 / 0.3 / 0`) 자유 공간은 어떻게 되는가?

### 10. 유효하지 않은 값 (경계)

```css
.item { flex-grow: -1; }
.item2 { flex: 1 1 -10px; }
```

- 이 선언들은 어떻게 되는가 — 에러가 나는가?
- 그것을 어떻게 확인하는가(진단 3창 중 어느 창인가)?
- `overflow: hidden` 을 준 flex 항목은 5번의 사고가 나는가?
- 그때 `getComputedStyle(el).minWidth` 는 무엇을 돌려주는가?

### 11. 다른 주제와 잇기 (연결)

- 이 문서가 다루지 않는 「크기가 정해진 뒤의 배치」는 목록의 몇 번 주제인가?
- `min-width: auto` 가 풀리는 `min-content` 의 정의는 목록의 몇 번 주제가 정본인가?
- `gap` 은 자유 공간 계산의 어느 자리에 들어가는가?
- flex 항목끼리는 마진 상쇄가 일어나는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
