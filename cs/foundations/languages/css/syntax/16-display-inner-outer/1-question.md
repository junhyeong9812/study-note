# css/syntax/16 — `display` 의 내부/외부 값 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제는 **「이 문법이 이 엔진에서 되나」를 묻는 문법 지도형**이라 예측형 비율이 높다.
> §2-1 규칙 6의 「코드블록 붙는 예측형 6개 이하」 상한보다 **문항 총수 쪽을 양보**했다 — 독립 실패 모드가 그만큼 많다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `display` 한 낱말은 무엇 둘을 정하는가 (왜)

- `display: inline-block` 은 **바깥**과 **안**에 각각 무엇을 정하는가?
- `display: block` 을 두 값으로 풀어 쓰면 무엇인가?
- `display: flow-root` 를 두 값으로 풀어 쓰면 무엇인가?
- `inline-block` 과 `flow-root` 가 **공유하는 값**은 무엇인가?

### 2. 이 선언들은 파싱되는가 (예측)

```css
.a { display: block flow; }
.b { display: inline flow-root; }
.c { display: flow; }
.d { display: flow block; }
```

- 넷 중 **버려지는 것**이 있는가?
- 각각의 `getComputedStyle(el).display` 는 무엇을 돌려주는가?
- `.c` 처럼 안쪽 값만 썼을 때 바깥 값은 무엇으로 채워지는가?
- `.d` 처럼 순서를 뒤집으면 결과가 달라지는가?

### 3. 이 선언들은 버려지는가 (예측)

```css
.a { display: block block; }
.b { display: flex flow; }
.c { display: inline-block flow; }
.d { display: block table-row; }
```

- 넷 중 유효한 것이 있는가?
- 버려졌다는 것을 **어떻게 확인**할 수 있는가 — `getComputedStyle` 만으로 되는가?
- 버려졌을 때 콘솔에 에러나 경고가 나오는가?

### 4. 두 값이 그대로 남는 경우 (경계)

- `display: block ruby` 의 계산값은 무엇인가?
- `display: inline flow list-item` 의 계산값은 무엇인가?
- 어떤 값은 옛 한 낱말로 접히고 어떤 값은 두 값으로 남는가 — 그 기준은 무엇인가?
- 이 사실이 "두 값 문법이 진짜로 파싱된다"의 증거가 되는 이유는 무엇인가?

### 5. 인라인 상자에 `width` 를 주면 (예측)

```css
.a { display: inline flow;      width: 120px; }
.b { display: inline flow-root; width: 120px; }
```

- `.a` 의 `rect.width` 는 선언한 120px 을 반영하는가?
- `.b` 는 어떤가?
- 두 결과가 갈리는 이유를 **바깥 값과 안쪽 값**이라는 말로 설명할 수 있는가?
- `.a` 의 `getComputedStyle().width` 는 무엇을 돌려주는가?

### 6. `display: contents` 는 무엇을 없애는가 (예측)

```html
<div class="flex">
  <div class="wrap" style="display: contents"><div>B</div><div>C</div></div>
</div>
```

- 이 래퍼의 `getBoundingClientRect()` 는 무엇을 돌려주는가?
- `B` 와 `C` 는 무엇이 되는가?
- 래퍼에 준 `background`·`border`·`padding` 은 어떻게 되는가?
- 이 래퍼는 **접근성 트리**에서도 사라지는가?

### 7. 숨기는 세 가지 — 레이아웃 (예측)

```css
.a { display: none; }
.b { visibility: hidden; }
.c { content-visibility: hidden; }
```

- 셋 중 **자리를 차지하는** 것은 무엇인가?
- 셋 중 **자기 배경과 테두리가 화면에 그려지는** 것은 무엇인가?
- `height` 선언을 지우면 셋의 높이는 각각 어떻게 되는가?

### 8. 숨기는 세 가지 — 접근성 트리 (경계)

- `display: none` 요소는 접근성 트리에 남는가?
- `visibility: hidden` 요소는 어떤가?
- `content-visibility: hidden` 요소와 **그 안의 글자**는 각각 어떤가?
- "화면에서 사라진다"와 "보조 기술이 못 읽는다"는 같은 말인가?

### 9. 왜 마진이 새는가 (연결)

- `display: block` 을 줬는데 자식의 마진이 부모 밖으로 새는 이유를 **안쪽 값**으로 설명할 수 있는가?
- 그것을 막으려면 안쪽 값을 무엇으로 바꿔야 하는가?
- 그 값의 **바깥 값까지 포함한 옛 한 낱말 이름**은 무엇인가?
- 서식 문맥의 정본은 목록의 몇 번 주제인가?

### 10. 다른 주제와 잇기 (연결)

- `display: flex` 를 두 값으로 풀면 무엇이고, flex 의 축과 정렬을 다루는 정본은 몇 번 주제인가?
- `display` 를 `none` ↔ `block` 으로 전환에 태울 수 없었던 이유는 무엇인가?
- flex 컨테이너의 자식에 `display: inline` 을 주면 무슨 일이 일어나는가?
- `content-visibility` 의 Baseline 상태는 무엇이고, 그것이 실무에서 뜻하는 바는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
