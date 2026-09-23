# css/syntax/18 — 마진 상쇄 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★ **답은 반드시 px 숫자로 적어라.** 「벌어진다」·「붙는다」는 답이 아니다 —
> 이 주제에서는 **「붙어 보인다」와 「상쇄됐다」가 다른 이야기**이기 때문이다.
> 간격의 정의: **위 상자의 `rect.bottom` 과 아래 상자의 `rect.top` 의 차이.**

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 두 상자 사이의 간격은 몇 px 인가 (예측)

```css
.a { height: 30px; margin-bottom: 20px; }
.b { height: 30px; margin-top: 20px; }
```

- `.a` 와 `.b` 사이의 간격은 몇 px 인가?
- `.a` 의 `margin-bottom` 을 `40px` 로 바꾸면 몇이 되는가?
- `.b` 의 `margin-top` 을 `0` 으로 바꾸면 몇이 되는가?
- 두 마진을 **패딩으로 바꾸면** 간격은 몇이 되는가, 왜 그런가?

### 2. 자식의 마진은 어디로 가는가 (예측)

```css
.p { width: 300px; background: yellow; }      /* 테두리·패딩 없음 */
.c { height: 30px; margin-top: 40px; }
```

```html
<div class="ruler"></div><div class="p"><div class="c"></div></div>
```

- 기준선과 `.p` 의 위쪽 사이 간격은 몇 px 인가?
- `.p` 의 `rect.height` 는 몇인가?
- `.c` 의 `rect.top` 은 `.p` 의 `rect.top` 과 같은가 다른가?
- 노란 배경은 마진 자리에 보이는가?

### 3. 빈 상자가 만드는 간격 (예측)

```css
.empty { margin: 30px 0; }   /* height·padding·border·내용 전부 없음 */
```

```html
<div class="b">위</div><div class="empty"></div><div class="b">아래</div>
```

- 「위」와 「아래」 사이의 간격은 몇 px 인가?
- `.empty` 의 `rect.height` 는 몇인가?
- `.empty` 에 `height: 1px` 을 주면 총 간격은 몇이 되는가?
- `.empty` 의 마진을 `50px 0` 으로 키우면 총 간격은 몇이 되는가?

### 4. 무엇이 상쇄를 막는가 (경계)

```css
/* 2번과 같은 상황에서 .p 에 하나씩 추가해 본다 */
.p1 { padding-top: 1px; }
.p2 { border-top: 1px solid; }
.p3 { display: flow-root; }
.p4 { overflow: hidden; }
.p5 { height: 60px; }
```

- 다섯 중 **막지 못하는** 것은 무엇인가?
- 그것이 막는 것은 **위쪽인가 아래쪽인가?**
- `padding`/`border` 로 막을 때 치르는 대가는 무엇인가?
- 다섯 중 **대가가 없는** 것은 무엇인가?

### 5. 음수 마진이 섞이면 (예측)

```css
.p { height: 40px; margin-bottom:  20px; }
.q { height: 40px; margin-top:    -40px; }
```

- `.p` 와 `.q` 사이의 간격은 몇 px 인가?
- `.q` 의 마진을 `-10px` 으로 바꾸면 몇이 되는가?
- `.p` 를 `-30px`, `.q` 를 `-10px` 으로 하면 몇이 되는가 — 합인가 아닌가?
- 양수와 음수가 섞였을 때의 규칙을 한 문장으로 말할 수 있는가?

### 6. 화면만 보고 판정할 수 있는가 (왜)

- `margin-bottom: 20px` + `margin-top: -25px` 인 두 상자는 화면에서 어떻게 보이는가?
- 그것을 `margin: 0` 인 두 상자와 눈으로 구분할 수 있는가?
- 상쇄 여부를 판정하는 올바른 방법은 무엇인가?

### 7. 상쇄가 아예 없는 자리 (예측)

```css
.stage { display: flex; flex-direction: column; }
.b     { height: 30px; }
```

```html
<div class="stage">
  <div class="b" style="margin-bottom:20px"></div>
  <div class="b" style="margin-top:20px"></div>
</div>
```

- 두 항목 사이의 간격은 몇 px 인가?
- `display: grid` 로 바꾸면 몇이 되는가?
- 이유를 「서식 문맥」이라는 말로 설명할 수 있는가?
- flex 항목 **안쪽**의 부모-자식 상쇄는 어떻게 되는가?

### 8. 측정 환경이 결과를 바꾼다 (경계)

- `margin-top: 40px` 인 요소를 `body` 의 첫 자식으로 두면 `rect.top` 은 몇인가 — `body` 기본 마진 8px 은 더해지는가?
- `<!doctype html>` 을 빼면 무엇이 달라지는가?
- 이 주제의 실험을 할 때 반드시 통제해야 하는 것 **둘**은 무엇인가?

### 9. 다른 주제와 잇기 (연결)

- 상쇄를 막는 BFC 의 **생성 조건 전체와 다른 효과 둘**은 목록의 몇 번 주제인가?
- `flow` 에서 마진이 새고 `flow-root` 에서 안 새는 이유를 `display` 의 **안쪽 값**으로 설명할 수 있는가?
- 마진 자리에 부모의 배경이 보이는 이유는 무엇인가(목록의 몇 번 주제)?
- 상쇄를 아예 피하고 간격을 주는 수단 **둘**을 대 보라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
