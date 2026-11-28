# css/filter-effects/19 — shape-image-threshold — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 135deg 그라데이션에 임계값 0.5 (예측)

```css
/* 질문용 발췌 — .shape 는 100px × 100px 정사각형 */
.shape {
  float: left;
  width: 100px;
  height: 100px;
  shape-outside: linear-gradient(135deg, rgba(0,0,0,1), rgba(0,0,0,0));
  shape-image-threshold: 0.5;
}
```

- 정사각형 안에서 도형이 되는 부분은 어떤 모양이고 어느 쪽에 있나?
- 그 옆 글 줄의 시작 위치는 위에서 아래로 갈수록 어떻게 바뀌나?

### 2. 같은 코드에서 임계값만 0.0 과 1.0 으로 바꾸면 (예측)

- 임계값이 `0.0` 일 때와 `1.0` 일 때 도형의 크기는 각각 어떻게 되나?
- `1.0` 일 때 글은 상자의 보이는 배경과 어떤 관계로 놓이나?

### 3. 시작색의 색만 바꾸면 (예측)

```css
/* 질문용 발췌 — 1번에서 시작색만 바꾼 것 */
.shape {
  shape-outside: linear-gradient(135deg, rgba(255,0,0,1), rgba(0,0,0,0));
  shape-image-threshold: 0.5;
}
```

- 1번과 비교해 도형의 윤곽은 달라지나?

### 4. `background` 에 그라데이션을 또 칠하는 까닭 (왜)

- `shape-outside` 에 그라데이션이 있는데 왜 `background` 에 같은 방향의 그라데이션을 한 번 더 칠하나?

### 5. 알파가 0 아니면 1 뿐인 이미지 (경계)

- 배경이 완전히 투명하고 그림은 완전히 불투명한 이미지에서 임계값을 0.2 에서 0.8 로 바꾸면 무엇이 달라지나?

### 6. float 을 지우면 (경계)

- `.shape` 에서 `float: left` 만 지우면 `shape-image-threshold` 는 여전히 효과가 있나?

### 7. 「이상」과 「초과」의 차이 (경계)

- 기본값 `0.0` 을 「이상」으로 읽을 때와 「초과」로 읽을 때, 투명한 배경을 가진 이미지의 도형은 어떻게 달라지나?

### 8. `transition` 과 부모에 준 값 (연결)

- 이 속성을 `transition` 으로 0.0 에서 0.5 로 바꿀 수 있나, 그리고 부모 `.wrap` 에 준 값은 `.shape` 에 닿나?

## 실습

### 실습 1. 그라데이션의 진한 쪽만 글이 피해 가는 float 도형 만들기

**만들 것** — 왼쪽에 띄운 정사각형 하나와 그 옆을 흐르는 문단을 만든다.
정사각형의 알파 그라데이션에서 절반 이상 불투명한 부분만 도형이 되어, 글이 그 윤곽을 따라 감싸게 한다.

**요구 조건**
1. `.wrap` 안에 빈 `.shape` 요소 하나와 문단 `p` 하나를 이 차례로 둔다.
2. `.shape` 를 왼쪽에 띄워 문단이 그 오른쪽을 따라 흐르게 한다.
3. `.shape` 의 도형을 `135deg` 방향 선형 그라데이션의 알파로 정한다 — 시작은 완전 불투명한 검정, 끝은 완전 투명한 검정이다.
4. 알파가 절반(0.5) 이상인 부분만 도형에 넣는다.
5. 눈에 보이는 색은 `shape-outside` 와 따로 `background` 로 칠한다(시작 코드에 채워 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="utf-8">
    <title>shape-image-threshold 실습</title>
    <style>
      .wrap {
        max-width: 300px;
        margin: 20px auto;
        font-size: 14px;
        line-height: 1.6;
        color: #374151;
      }
      .shape {
        /* TODO: 왼쪽에 띄운다 */
        width: 100px;
        height: 100px;
        /* TODO: 135deg 알파 그라데이션(불투명 검정 → 투명 검정)을 도형으로 쓴다 */
        /* TODO: 알파 0.5 를 경계로 도형을 자른다 */
        background: linear-gradient(135deg, #06b6d4, transparent);
        margin-right: 12px;
        border-radius: 8px;
      }
    </style>
  </head>
  <body>
    <!-- TODO: .wrap 안에 .shape 와 문단을 둔다 -->
  </body>
</html>
```

**확인 방법** — 브라우저로 파일을 열어, 위쪽 줄은 상자 오른쪽 가까이에서 시작하고 아래로 갈수록 글이 왼쪽으로 들어오는지 본다. 임계값을 `0.0` · `1.0` 으로 바꿔 글 줄의 시작 위치가 달라지는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
