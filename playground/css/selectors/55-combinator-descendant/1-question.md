# css/selectors/55 — (공백) 자손 결합자 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 중간 div 를 사이에 둔 두 p (예측)

```html
<!-- 질문용 발췌 -->
<div class="parent-d">
  <p>직접 자식 p</p>
  <div><p>손자 p</p></div>
</div>
<style>
  .parent-d p { color: #2563eb; background: #dbeafe; }
</style>
```

- 두 `p` 가운데 파란 글자·연한 파란 배경이 붙는 것은 어느 것인가?

### 2. 공백을 `>` 로 바꾸면 (예측)

```css
/* 질문용 발췌 — HTML 은 1번과 같다 */
.parent-d > p { color: #2563eb; background: #dbeafe; }
```

- 이번에는 두 `p` 가운데 어느 것이 꾸며지는가?

### 3. 공백의 자리를 옮긴 세 선택자 (예측)

```css
/* 질문용 발췌 — HTML 은 1번과 같다 */
.parent-d p  { }   /* 가 */
.parent-d.p  { }   /* 나 */
p .parent-d  { }   /* 다 */
```

- 가·나·다 가운데 1번 HTML 의 `p` 를 고르는 선택자는 어느 것인가?

### 4. 손자 p 가 부모가 div 인데도 매칭되는 까닭 (왜)

- `.parent-d p` 가 부모가 `.parent-d` 가 아닌 손자 `p` 까지 고르는 까닭은 무엇인가?

### 5. `.parent-d p` 가 닿는 범위의 가장자리 (경계)

- `.parent-d` 바깥에 있는 `p` 는 이 규칙에 매칭되는가?
- `p` 와 `.parent-d` 사이에 감싸는 요소가 열 겹 끼어 있으면 결과가 달라지는가?

### 6. 이 규칙이 꾸미는 요소는 어느 쪽인가 (경계)

- `.parent-d p { background: … }` 를 쓰면 `.parent-d` 상자 자신의 배경도 바뀌는가?

### 7. 상속만으로는 부족한 경우 (연결)

- `.parent-d { color: … }` 만 써도 안쪽 `p` 글자색은 바뀌는데, `p` 마다 배경과 여백을 주려면 왜 `.parent-d p` 가 필요한가?

### 8. 자손 결합자와 자식 결합자를 고르는 기준 (연결)

- 카드 안에 나중에 다른 부품이 끼워질 수 있을 때, 카드 바로 아래 `p` 만 꾸미려면 공백과 `>` 가운데 어느 쪽을 골라야 하는가?

## 실습

### 실습 1. 회색 상자 안의 모든 p 를 깊이 상관없이 강조하기

**만들 것** — 회색 상자 안에 직접 자식 `p` 하나와, 중간 `div` 에 싸인 손자 `p` 하나를 두고, 규칙 하나로 두 `p` 를 똑같이 강조한다.

**요구 조건**
1. `body` 안에 클래스 `parent-d` 를 가진 `div` 를 하나 둔다.
2. 그 `div` 의 직접 자식으로 「직접 자식 p」라는 글을 가진 `p` 를 둔다.
3. 같은 `div` 안에 중간 `div` 를 하나 더 두고, 그 안에 「손자 p」라는 글을 가진 `p` 를 둔다.
4. 시작 코드의 `.parent-d` 규칙은 그대로 두어 바깥 상자를 꾸민다.
5. 강조 규칙의 선택자 자리에 `.parent-d` 안의 모든 깊이의 `p` 를 고르는 선택자를 쓴다 — 자식 결합자 `>` 는 쓰지 않는다.
6. 그 규칙 하나로 직접 자식 `p` 와 손자 `p` 가 둘 다 강조되어야 한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>(공백) 자손 결합자</title>
<style>
  .parent-d {
    padding: 16px;
    background: #f3f4f6;
    border-radius: 8px;
  }
  /* TODO: ??? 자리에 .parent-d 안(모든 깊이)의 p 를 고르는 선택자를 쓴다 */
  ??? {
    color: #2563eb;
    font-weight: bold;
    padding: 8px;
    margin: 4px 0;
    background: #dbeafe;
    border-radius: 4px;
  }
</style>
</head>
<body>
  <!-- TODO: .parent-d 상자, 그 직접 자식 p, 중간 div 안의 손자 p 를 만든다 -->
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 회색 상자 안의 두 `p` 가 모두 굵은 파란 글자·연한 파란 배경인지 본다. 선택자를 `.parent-d > p` 로 잠깐 바꿔 손자 `p` 의 강조가 사라지는지도 견주어 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
