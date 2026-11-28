# css/box-model/20 — padding-block — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 값을 두 개 준 `padding-block` (예측)

```css
/* 질문용 발췌 — 기본 가로 쓰기 */
.box { padding-block: 10px 40px; }
```

- 이 박스의 위쪽 패딩과 아래쪽 패딩은 각각 몇 px 인가?

### 2. 블록과 인라인을 함께 준 박스 (예측)

```css
/* 질문용 발췌 — 기본 가로 쓰기 */
.box { padding-block: 30px; padding-inline: 16px; }
```

- 이 박스의 위 · 아래 · 왼쪽 · 오른쪽 패딩은 각각 몇 px 인가?

### 3. 퍼센트 값의 크기 (예측)

```css
/* 질문용 발췌 — 기본 가로 쓰기 */
.parent { width: 400px; height: 1000px; }
.child  { padding-block: 10%; }
```

- `.child` 의 위쪽 패딩은 몇 px 이 되나?

### 4. 물리적 속성 대신 논리적 속성을 쓰는 까닭 (왜)

- `padding-top` · `padding-bottom` 으로도 같은 결과가 나오는데 왜 `padding-block` 이라는 논리적 속성이 따로 있나?

### 5. 세로 쓰기에서의 `padding-block` (경계)

- `writing-mode: vertical-rl` 인 요소에서 `padding-block` 의 여백은 박스의 어느 변들에 붙나?

### 6. 음수 값을 준 `padding-block` (경계)

- `padding-block: -10px` 을 쓰면 박스의 위아래 여백은 어떻게 되나?

### 7. 부모에 준 `padding-block` 과 자식 (경계)

- 부모에 `padding-block: 20px` 을 주면 그 안의 자식 요소들도 각자 위아래 패딩 20px 을 갖게 되나?

### 8. `padding` 단축 속성과의 관계 (연결)

- 가로 쓰기에서 `padding-block: 30px; padding-inline: 16px;` 과 같은 결과를 내는 `padding` 한 줄은 무엇이고, 쓰기 모드가 바뀌면 둘은 어떻게 달라지나?

## 실습

### 실습 1. 위아래가 두툼한 파란 라벨 박스 만들기

**만들 것** — 「padding-block」이라는 글자가 든 박스 하나를 만들고, 위아래와 좌우 안쪽 여백을 논리적 단축 속성만으로 정한다.

**요구 조건**
1. `body` 안에 클래스가 `box` 인 `div` 하나를 두고, 글자 「padding-block」을 넣는다.
2. 블록 방향 양끝(가로 쓰기에서 위아래) 여백은 단축 속성 하나에 값 하나로 같게 준다.
3. 인라인 방향 양끝(가로 쓰기에서 좌우) 여백도 논리적 단축 속성 하나에 값 하나로 같게 준다.
4. 두 여백의 크기는 시작 코드의 TODO 주석에 적힌 값을 쓴다 — 위아래가 좌우보다 두툼해야 한다.
5. `padding-top` · `padding-left` 같은 물리적 패딩 속성은 쓰지 않는다.
6. 배경 · 글자색 · 모서리 같은 꾸밈은 시작 코드에 채워진 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>padding-block 연습</title>
<style>
.box {
  /* TODO: 블록 방향 양끝 여백 30px (논리적 단축 속성, 값 하나) */
  /* TODO: 인라인 방향 양끝 여백 16px (논리적 단축 속성, 값 하나) */
  background: #3b82f6;
  color: white;
  border-radius: 4px;
}
</style>
</head>
<body>
<!-- TODO: 클래스 box 인 div 에 글자 「padding-block」 -->

</body>
</html>
```

**확인 방법** — 브라우저로 열고 개발자 도구에서 `.box` 를 골라 박스 모델 그림의 padding 이 위아래 30, 좌우 16 인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
