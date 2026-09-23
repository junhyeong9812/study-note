# css/syntax/46 — 테두리·`border-radius`·`outline`·`box-shadow` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **좌표와 픽셀을 맞힐 수 있는지**를 묻는다.
> ★ **답을 숫자로 적어라.** "커진다"·"둥글어진다"는 답이 아니다. `rect.width` 가 몇인지, 그 좌표의 `(r,g,b)` 가 무엇인지 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 테두리가 안 보인다 — 상자 치수는 어떻게 되나 (예측)

```css
.a { width: 220px; padding: 6px; border-width: 8px; border-color: #dc2626; }
.b { width: 220px; padding: 6px; border-width: 8px; border-color: #dc2626; border-style: solid; }
```

- `.a` 의 `getComputedStyle().borderTopWidth` 는 무엇인가?
- `.a` 와 `.b` 의 `rect.width` 는 각각 몇인가?
- `.a` 에 나중에 `border-style: solid` 를 넣으면 레이아웃에 무슨 일이 일어나는가?
- `border-style: hidden` 으로 바꾸면 `.a` 와 같아지는가 `.b` 와 같아지는가?

### 2. 선언한 반지름과 그려진 반지름이 갈린다 (예측)

```css
.x { width: 200px; height: 200px; background: #cc0000; border-radius: 150px; }
.y { width: 200px; height: 200px; background: #cc0000; border-radius: 100px; }
```

- `.x` 의 `getComputedStyle().borderRadius` 는 무엇을 돌려주는가?
- `.x` 와 `.y` 를 렌더해 픽셀을 전부 비교하면 몇 개나 다른가 — 그리고 그 차이는 어디에 있는가?
- 축소 비율은 어떻게 정해지는가 — 한 변만 넘쳐도 네 모서리가 다 줄어드는가?
- 계산값 API 로 이 축소를 확인할 수 있는가?

### 3. `/` 가 가르는 두 반지름 (예측)

```css
.p { width: 200px; height: 200px; background: #cc0000; border-radius: 60px / 20px; }
```

- 위 변(`y=0`)에서 처음으로 **불투명한** 픽셀이 나오는 `x` 는 대략 몇인가?
- 왼 변(`x=0`)에서 처음으로 불투명한 픽셀이 나오는 `y` 는 대략 몇인가?
- `/` 앞뒤 중 어느 쪽이 가로 반지름인가?
- `border-radius` 에 쓸 수 있는 숫자는 최대 몇 개인가?

### 4. `outline` 과 `border` — 이웃의 `x` 좌표 (예측)

```css
b    { display: inline-block; width: 90px; height: 34px; }
.brd { border: 8px solid #dc2626; }
.out { outline: 8px solid #16a34a; }
```

- `.brd` 의 `rect.width` 와 바로 뒤 이웃의 `rect.left` 는 각각 몇인가(줄 시작 `x` 를 16 이라 하자)?
- `.out` 은 각각 몇인가?
- `.out` 의 초록 테가 이웃과 겹치는 지점의 픽셀은 초록인가, 이웃의 배경색인가?
- `outline-offset: 12px` 를 주면 이웃의 `x` 는 바뀌는가?

### 5. 그림자 두 개, 순서만 다르다 (예측)

```css
.a { box-shadow: 0 0 0 30px #ef4444, 0 0 0 15px #3b82f6; }
.b { box-shadow: 0 0 0 15px #3b82f6, 0 0 0 30px #ef4444; }
```

- `.a` 의 상자 왼쪽 8px 바깥 지점은 무슨 색인가?
- `.b` 의 같은 지점은 무슨 색인가?
- 상자 왼쪽 20px 바깥 지점은 두 판에서 각각 무슨 색인가?
- 이중 링을 만들려면 큰 것과 작은 것 중 어느 쪽을 먼저 써야 하는가?

### 6. 둥근 상자에 테를 두르면 (예측)

```css
.r { width: 100px; height: 100px; background: #1d4ed8; border-radius: 50px;
     outline: 6px solid #16a34a; }
```

- 상자의 왼쪽 위 모서리 좌표(`border box` 의 `(0,0)`) 픽셀은 초록인가 배경색인가?
- 왼쪽 한가운데에서 상자 바깥 4px 지점은 무슨 색인가?
- 같은 선언을 `border-radius: 0` 으로 바꾸면 모서리 바깥 지점은 무슨 색이 되는가?
- 이 동작은 명세가 보장하는 것인가, 이 브라우저에서 관찰한 것인가?

### 7. `spread` 는 `blur` 와 무엇이 다른가 (경계)

- `box-shadow: 0 0 0 15px red` 와 `box-shadow: 0 0 15px 0 red` 는 각각 어떻게 보이는가?
- `spread` 를 쓴 그림자와 `border` 는 화면에서 어떻게 구별되는가 — 그리고 레이아웃에서는?
- `inset` 을 붙이면 상자 바깥에는 무엇이 남는가?
- `box-shadow` 에 길이 값을 하나만 쓰면 어떻게 되는가?

### 8. 자리를 안 차지하는 것의 대가 (경계)

- `outline` 과 `box-shadow` 가 레이아웃 공간을 차지하지 않는다는 것을 어떤 두 숫자로 증명하는가?
- 그 대신 무엇이 문제가 되는가 — 이웃과 겹치면 누가 이기는가?
- 스크롤 영역(`scrollWidth`)은 그림자만큼 늘어나는가?
- 이 성질을 실무에서 일부러 쓰는 자리는 어디인가?

### 9. 조용히 버려진 선언을 어떻게 찾나 (왜)

- `border-radius: 50` 과 `box-shadow: 10px #f00` 은 왜 아무 에러도 안 내는가?
- 「진단 3창」의 세 창은 각각 무엇을 묻고, 위 두 선언은 어느 창에서 잡히는가?
- 규칙 자체는 살아남는가, 통째로 죽는가?
- 이 주제에서 `getComputedStyle` 이 **거짓 안심**을 주는 자리는 어디인가?

### 10. 다른 주제로 잇기 (연결)

- `border-radius` 가 자기 자식의 네모난 배경까지 자르는가 — 자르려면 무엇이 더 필요한가?
- 투명한 PNG 아이콘에 모양을 따라가는 그림자를 붙이려면 무엇을 쓰고, 그것은 목록의 몇 번 주제인가?
- `border-radius` 를 임의의 도형으로 일반화한 속성은 무엇이고 몇 번 주제인가?
- 반지름 비례 축소가 일어나는 것은 값 처리의 어느 단계이고, 그 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
