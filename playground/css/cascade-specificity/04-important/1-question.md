# css/cascade-specificity/04 — !important — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. ID 규칙과 `!important` 클래스 규칙이 한 문단에 걸리면 (예측)

```css
/* 질문용 발췌 */
#high-spec { color: red; font-size: 18px; }
.styled { color: #3b82f6 !important; font-weight: 700; }
/* <p id="high-spec" class="styled"> */
```

- 이 문단의 글자색 · 글자 크기 · 굵기는 각각 어느 규칙의 값이 되나?

### 2. 둘 다 `!important` 일 때 (예측)

```css
/* 질문용 발췌 */
#a { color: red !important; }
.b { color: blue !important; }
/* <p id="a" class="b"> */
```

- 이 문단의 글자색은 무엇이 되나?

### 3. 명시도도 같고 둘 다 `!important` 일 때 (예측)

```css
/* 질문용 발췌 */
.x { color: green !important; }
.y { color: orange !important; }
/* <p class="y x"> */
```

- 이 문단의 글자색은 무엇이 되나?

### 4. 진 쪽 규칙의 `font-size` 가 살아남는 까닭 (왜)

- `#high-spec` 규칙은 `color` 에서 졌는데 왜 같은 규칙의 `font-size` 는 그대로 적용되나?

### 5. `!important` 를 덮을 수 있는 범위 (경계)

- `!important` 로 강제된 값을 덮으려면 어떤 선언이 필요하고, 일반 선언으로는 어디까지 할 수 있나?

### 6. `!important` 남용이 유지보수를 망치는 까닭 (왜)

- 한 번 붙인 `!important` 가 왜 다른 곳에도 `!important` 를 부르게 되나?

### 7. 유틸리티 클래스와 서드파티 CSS (연결)

- `.hidden { display: none !important }` 와 서드파티 CSS 오버라이드는 왜 정당한 사용으로 꼽히고, 그 밖의 경우에는 무엇을 대신 해야 하나?

## 실습

### 실습 1. 명시도 낮은 클래스가 ID 를 이기는 데모 카드 만들기

**만들 것** — 문단 셋이 담긴 데모 상자를 만든다.
첫 문단에서 클래스 규칙의 글자색이 `!important` 덕분에 ID 규칙의 글자색을 이기는 모습을 보인다.

**요구 조건**

1. 데모 상자(`.imp-demo`) 안에 문단 셋을 둔다.
2. 첫 문단에는 id `high-spec` 과 class `styled` 를 함께 단다.
3. `#high-spec` 규칙은 글자색과 글자 크기를, `.styled` 규칙은 다른 글자색과 굵기를 선언한다(값은 시작 코드에 있다).
4. `.styled` 규칙의 **글자색 선언만** `!important` 로 표시해, 명시도가 더 높은 ID 규칙의 글자색을 이기게 한다.
5. 첫 문단의 글자 크기는 ID 규칙의 값이, 굵기는 클래스 규칙의 값이 그대로 적용되게 둔다(`!important` 를 붙이지 않는다).
6. 둘째 문단은 `.danger`, 셋째 문단은 `.warning` 클래스로 저마다 다른 색을 일반 선언으로만 준다.
7. 문단은 카드 모양으로 꾸미고, 마지막 문단의 아래 여백은 없앤다(시작 코드에 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>!important</title>
<style>
  #high-spec {
    color: red;
    font-size: 18px;
  }

  .styled {
    /* TODO: 글자색 #3b82f6 을, 명시도가 더 높은 #high-spec 의 color 를 이기도록 선언 */
    font-weight: 700;
  }

  .imp-demo { padding: 16px; background: #f1f5f9; border-radius: 8px; }
  .imp-demo p { padding: 14px; margin-bottom: 8px; background: white; border-radius: 6px; border: 2px solid #e2e8f0; }
  .imp-demo p:last-child { margin-bottom: 0; }
  .danger { color: #ef4444; font-weight: 600; }
  .warning { color: #f59e0b; font-weight: 600; font-size: 14px; }
</style>
</head>
<body>
  <div class="imp-demo">
    <p><!-- TODO: id high-spec 과 class styled 를 함께 단다 -->ID 선택자 (0,1,0,0) vs .styled !important</p>
    <p class="danger">!important는 다른 !important로만 덮을 수 있다</p>
    <p class="warning">⚠️ !important 남용 = 유지보수 지옥</p>
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 첫 문단이 빨강이 아니라 파랑이면서 크기는 커지고 굵은지 본다.
개발자 도구 스타일 패널에서 `#high-spec` 의 `color` 줄이 진 선언으로 표시되는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
