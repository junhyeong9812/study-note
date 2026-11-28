# css/layout/20 — overflow-inline — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 고정 폭 상자에 줄바꿈 없는 긴 문장 (예측)

```css
/* 질문용 발췌 */
.box { width: 200px; overflow-inline: auto; }
.content { white-space: nowrap; }
```

- 문장이 상자 폭보다 길 때, 상자에는 어느 방향의 스크롤바가 생기는가?

### 2. 같은 상자에서 `nowrap` 을 지우면 (예측)

```css
/* 질문용 발췌 */
.box { width: 200px; overflow-inline: auto; }
.content { /* white-space 지정 없음 */ }
```

- 띄어쓰기가 있는 같은 긴 문장을 넣으면 인라인 방향 스크롤바가 생기는가?

### 3. 세로쓰기 상자의 `overflow-inline: auto` (예측)

```css
/* 질문용 발췌 */
.box { writing-mode: vertical-rl; height: 200px; overflow-inline: auto; }
.content { white-space: nowrap; }
```

- 이 상자에서 스크롤은 화면의 어느 축으로 생기는가?

### 4. 이 속성을 「논리적 속성」이라 부르는 이유 (왜)

- `overflow-inline` 이 가로나 세로 대신 「인라인 방향」으로 정의된 까닭은 무엇인가?

### 5. `hidden` 과 `clip` 이 갈리는 지점 (경계)

- 둘 다 넘친 부분을 자르는데, 원본 설명에서 둘을 가르는 차이는 무엇인가?

### 6. 넘치지 않는 내용에서 `scroll` 과 `auto` (경계)

- 내용이 상자 안에 다 들어갈 때 두 값의 겉모습은 어떻게 다른가?

### 7. 부모에 준 값과 자식, 그리고 전환 효과 (경계)

- 부모 상자에 `overflow-inline: auto` 를 주면 자식 요소의 넘침 처리도 같아지는가?

### 8. `overflow-x` 와의 다리 (연결)

- 수평 쓰기 모드 문서에서 `overflow-inline` 은 어떤 물리적 속성과 같은 일을 하며, 세로쓰기로 바뀌면 그 대응은 어떻게 되는가?

## 실습

### 실습 1. 인라인 방향으로 넘칠 때만 스크롤되는 상자 만들기

**만들 것** — 고정 폭 상자 안에 긴 문장 한 줄을 넣고, 문장이 넘칠 때만 인라인 방향으로 밀어 볼 수 있게 만든다.

**요구 조건**
1. `.box` 상자 안에 `.content` 요소 하나를 두고, 거기에 상자 폭보다 긴 문장을 넣는다.
2. `.content` 의 문장은 줄바꿈되지 않고 한 줄로 이어져야 한다.
3. `.box` 는 물리 방향 속성(`overflow-x`)이 아니라 논리적 속성으로 넘침을 다룬다.
4. `.box` 는 인라인 방향으로 넘칠 때만 스크롤바를 보인다.
5. `.box` 의 폭은 고정되어 넘침이 생겨야 한다 (시작 코드에 이미 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>overflow-inline 실습</title>
<style>
  .box {
    /* TODO: 인라인 방향으로 넘칠 때만 스크롤되게 한다 (논리적 속성) */
    width: 200px;
    background: #f1f5f9;
    padding: 8px;
    border: 2px solid #3b82f6;
    border-radius: 4px;
  }
  .content {
    /* TODO: 줄바꿈을 막아 한 줄로 이어지게 한다 */
  }
</style>
</head>
<body>
<div class="box">
  <div class="content">인라인 방향으로 넘치는 매우 긴 콘텐츠입니다.</div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 문장이 한 줄로 이어지는지, 상자 안에서 가로로 밀어 문장 끝까지 볼 수 있는지 본다. 문장을 짧게 줄이면 스크롤바가 사라지는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
