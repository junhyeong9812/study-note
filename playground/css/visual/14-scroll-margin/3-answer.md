# css/visual/14 — scroll-margin — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 16px — 스냅 영역의 시작이 카드보다 16px 앞이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
카드 2 의 왼쪽 모서리는 컨테이너 왼쪽 끝에서 16px 안쪽에 선다 (코드에서 읽은 것 — 렌더 실측 아님).
카드 2 의 왼쪽 위치는 콘텐츠 기준 180 이고, 스크롤은 164 에 멈춘다.

**왜 그런가**
`scroll-margin` 의 왼쪽 16px 때문에 카드 2 의 스냅 영역은 카드보다 16px 앞에서 시작한다.
`start` 정렬은 그 스냅 영역의 시작을 컨테이너 시작에 맞추므로, 카드 자체는 16px 안쪽에 남는다.
164 는 스크롤 범위(0~340) 안이라 막히지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「(2)」 · 「(4)」.

### 2. 0px — `scroll-margin` 은 배치를 바꾸지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
카드 사이에 틈은 생기지 않고 카드 셋이 붙어 있다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`scroll-margin` 은 멈출 자리를 계산할 때 쓰는 스냅 영역만 넓힌다.
카드의 크기와 자리, 카드 사이 간격은 그대로다.
발췌에 `gap` 이나 `margin` 이 없으므로 틈은 0 이다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 3. 아니다 — 카드 1 은 왼쪽 끝에 붙어 있다

카드 1 을 16px 안쪽에 두려면 스크롤 위치가 -16 이어야 한다.
스크롤 위치는 0 보다 작아질 수 없으므로 카드 1 은 0 에 머물러 컨테이너 왼쪽 끝에 붙는다 (코드에서 읽은 것 — 렌더 실측 아님).
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 4. 달라지지 않는다 — `start` 정렬은 시작 쪽 마진만 쓴다

`start` 정렬은 스냅 영역의 시작(왼쪽) 모서리를 맞춘다.
오른쪽 마진은 스냅 영역의 끝 쪽을 넓힐 뿐이라 `start` 정렬의 멈출 자리에는 드러나지 않는다.
오른쪽 마진은 `end` 정렬일 때 멈출 자리를 바꾼다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 3」.

### 5. 자식마다 따로 줄 수 있기 때문이다

`scroll-margin` 은 그 값을 단 자식의 스냅 영역만 넓히므로 카드마다 다른 값을 줄 수 있다.
컨테이너에 다는 `scroll-padding` 은 스냅포트를 줄여 모든 자식의 멈출 자리를 한꺼번에 옮긴다.
그래서 개별 자식을 미세 조정하는 데는 자식에 다는 `scroll-margin` 이 맞는다.
근거: 2-summary 「어디서 틀리나 2」 · 「언제 쓰고 언제 안 쓰나」.

### 6. 정확히 스냅 위치에 멈춰야 16px 차이가 드러나기 때문이다

`mandatory` 는 스크롤이 끝나면 반드시 스냅 위치 가운데 하나에 멈추게 한다.
그래야 카드가 늘 계산된 자리(스냅 영역 시작 = 컨테이너 시작)에 서고, 16px 안쪽이라는 차이가 매번 같은 모습으로 보인다.
스냅이 없으면 사용자가 손을 뗀 아무 자리에나 멈추므로 `scroll-margin` 이 무엇을 바꿨는지 알아보기 어렵다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」. 「알아보기 어렵다」는 판단은 (원본에 근거 없음 — 추론).

### 7. `scroll-padding` 은 스냅포트, `scroll-margin` 은 스냅 영역

스냅 계산은 컨테이너 쪽 상자(스냅포트)와 자식 쪽 상자(스냅 영역)의 모서리를 맞춘다.
`scroll-padding` 은 컨테이너에 달아 스냅포트를 안쪽으로 줄인다.
`scroll-margin` 은 자식에 달아 스냅 영역을 바깥으로 넓힌다.
근거: 2-summary 「동작 방식 (2)」의 스냅포트 풀이 · 「어디서 틀리나 2」 · 「용어 풀이」.

### 8. `margin` 은 배치를, `scroll-margin` 은 스크롤이 멈출 자리를 바꾼다

`margin` 은 요소 둘레에 실제 공간을 만들어 다른 요소의 자리를 밀어낸다.
`scroll-margin` 은 배치를 건드리지 않고, 스냅할 때 쓰는 스냅 영역만 넓힌다.
값을 푸는 꼴(1~4개, 위 · 오른쪽 · 아래 · 왼쪽)은 같다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 1」.

## 실습 정답

### 실습 1. 카드 하나하나가 조금 안쪽에 멈추는 가로 스냅 캐러셀

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 가로 배치 · 가로 스크롤 | `.snap-container { display: flex; overflow-x: auto; }` |
| 2. 카드가 줄어들지 않음 | `.snap-item { flex-shrink: 0; }` |
| 3. 가로 방향 강제 스냅 | `.snap-container { scroll-snap-type: x mandatory; }` |
| 4. 시작 모서리에 스냅 | `.snap-item { scroll-snap-align: start; }` |
| 5. 위아래 0, 좌우 16px 스크롤 마진 | `.snap-item { scroll-margin: 0 16px; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/visual/reference/scroll-margin.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- 문서 언어: 한국어 -->
<head>
  <meta charset="utf-8">
  <!-- 문자 인코딩: UTF-8 -->
  <title>scroll-margin - 스크롤 스냅 시 자식 요소의 스냅 영역에 마진을 추가합니다</title>
  <!--
    [시각 효과] scroll-margin
    설명: 스크롤 스냅 시 자식 요소의 스냅 영역에 마진을 추가합니다
    구문: scroll-margin: <length>{1,4}
    팁: 개별 자식 요소의 스냅 위치를 미세 조정. scroll-padding은 컨테이너, scroll-margin은 자식 요소에 설정하는 차이.
  -->
  <style>
    /* .snap-container: 가로 스냅 캐러셀 컨테이너 */
    .snap-container {
      scroll-snap-type: x mandatory;              /* 가로 방향 강제 스냅 - 항상 스냅 포인트에 멈춤 */
      display: flex;                              /* 자식 가로 배치 */
      overflow-x: auto;                           /* 가로 스크롤 자동 */
      border-radius: 12px;                        /* 모서리 둥글게 */
      width: 200px;                               /* 너비 200px - 아이템보다 좁아 스크롤 발생 */
      margin: 20px auto;                          /* 위아래 20px, 가로 중앙 */
    }
    /* .snap-item: 스냅 대상 아이템 - 좌우 마진으로 스냅 위치 미세 조정 */
    .snap-item {
      scroll-snap-align: start;                   /* 컨테이너 시작점에 스냅 정렬 */
      scroll-margin: 0 16px;                      /* 위아래 0, 좌우 16px - 스냅 위치를 16px 안쪽으로 조정 */
      min-width: 180px;                           /* 최소 너비 180px - 가로 길이 확보 */
      height: 100px;                              /* 높이 100px */
      display: flex;                              /* 플렉스 - 텍스트 가운데 */
      align-items: center;                        /* 세로 중앙 */
      justify-content: center;                    /* 가로 중앙 */
      color: white;                               /* 흰 글자 */
      font-size: 28px;                            /* 큰 숫자 28px */
      font-weight: bold;                          /* 굵게 */
      flex-shrink: 0;                             /* 축소 방지 - 가로 스크롤 유지 */
      border-radius: 8px;                         /* 모서리 둥글게 */
    }
  </style>
</head>
<body>
  <!-- scroll-margin으로 스냅 위치 미세 조정 데모 -->
  <div class="snap-container">
    <!-- 가로 스냅 컨테이너 -->
    <div class="snap-item" style="background:#06b6d4">1</div>
    <!-- 청록 카드 1 -->
    <div class="snap-item" style="background:#8b5cf6">2</div>
    <!-- 보라 카드 2 -->
    <div class="snap-item" style="background:#f59e0b">3</div>
    <!-- 주황 카드 3 -->
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.snap-container { scroll-snap-type: x mandatory; display: flex; overflow-x: auto; border-radius: 12px; width: 200px; margin: 20px auto; }
.snap-item { scroll-snap-align: start; scroll-margin: 0 16px; min-width: 180px; height: 100px; display: flex; align-items: center; justify-content: center; color: white; font-size: 28px; font-weight: bold; flex-shrink: 0; border-radius: 8px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 스냅은 두 쪽이 다 있어야 한다 — 컨테이너의 `scroll-snap-type` 과 자식의 `scroll-snap-align`.
- `scroll-margin` 은 자식에 달고, 카드 사이 틈은 만들지 않는다.
- 컨테이너 200px 보다 카드 셋의 너비가 커야 스크롤이 생기므로 `flex-shrink: 0` 으로 카드 너비를 지킨다.
- `start` 정렬이라 실제로 멈출 자리를 바꾸는 것은 왼쪽 16px 이다.
- 카드 1 은 스크롤 0 에 막혀 왼쪽 끝에 붙고, 카드 3 은 최대 스크롤에 막혀 계산과 다른 자리에 선다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
