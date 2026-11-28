# css/selectors/50 — ::file-selector-button — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 버튼 규칙에 파란 배경을 주면 (예측)

```css
/* 질문용 발췌 */
.file-input { font-size: 14px; }
.file-input::file-selector-button { background: #3b82f6; color: white; }
```

- 화면에서 파란 배경이 칠해지는 범위는 입력 요소 전체인가, 그 안의 어느 부분인가?

### 2. 버튼 위에 마우스를 올리면 (예측)

```css
/* 질문용 발췌 */
.file-input::file-selector-button { background: #3b82f6; transition: background 0.2s; }
.file-input::file-selector-button:hover { background: #1d4ed8; }
```

- 마우스를 버튼에 올렸을 때 배경은 무엇으로, 어떤 빠르기로 바뀌는가?

### 3. 마우스를 입력 요소의 파일 이름 글자 위에 올리면 (예측)

```css
/* 질문용 발췌 */
.file-input::file-selector-button:hover { background: #1d4ed8; }
```

- 버튼이 아니라 파일 이름 글자 위에 마우스를 올리면 버튼 색은 어떻게 되는가?

### 4. 버튼을 클래스가 아니라 의사 요소로 고르는 까닭 (왜)

- 「파일 선택」 버튼에 `class` 를 달아 꾸미지 않고 `::file-selector-button` 을 쓰는 까닭은 무엇인가?

### 5. 원본 예제가 `font-size` 를 두 군데에 쓰는 까닭 (왜)

- 입력 요소 규칙과 버튼 규칙에 같은 `font-size` 를 따로 적는 까닭은 무엇인가?

### 6. 글자 입력칸에 쓰면 (경계)

- `input[type="text"]::file-selector-button` 에 스타일을 주면 무엇이 바뀌는가?

### 7. `:hover` 를 놓는 자리 (연결)

- `.file-input:hover::file-selector-button` 과 `.file-input::file-selector-button:hover` 는 각각 언제 맞는가?

### 8. 「통일된 스타일」과 `border: none` (연결)

- 브라우저마다 다른 기본 버튼을 하나로 맞추는 일에서 `border: none` 은 어떤 몫을 하는가?

## 실습

### 실습 1. 파일 선택 버튼을 파란 버튼으로 꾸미기

**만들 것** — 파일 입력 하나를 놓고, 그 안의 「파일 선택」 버튼만 둥근 파란 버튼으로 꾸며 마우스를 올리면 진한 색으로 서서히 바뀌게 한다.

**요구 조건**
1. 문서에 파일 선택 입력 하나를 놓고 `file-input` 클래스를 단다.
2. 입력 요소 전체(파일 이름 글자 포함)의 글자 크기를 입력 요소 규칙으로 정한다.
3. 버튼 부분에만 안쪽 여백 · 배경 · 글자색 · 테두리 제거 · 둥근 모서리 · 손가락 커서 · 글자 크기 · 오른쪽 여백 · 배경 전이를 건다.
4. 마우스를 버튼 위에 올렸을 때만 버튼 배경이 더 진한 색으로 바뀐다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>::file-selector-button 연습</title>
<style>
  /* TODO 1: 입력 요소 전체를 고르는 선택자를 쓰고 아래 선언을 넣는다
     font-size: 14px;
  */

  /* TODO 2: 입력 요소 안의 '파일 선택' 버튼만 고르는 선택자를 쓰고 아래 선언을 넣는다
     padding: 10px 20px;
     background: #3b82f6;
     color: white;
     border: none;
     border-radius: 8px;
     cursor: pointer;
     font-size: 14px;
     margin-right: 12px;
     transition: background 0.2s;
  */

  /* TODO 3: 그 버튼 위에 마우스가 있을 때만 맞는 선택자를 쓰고 아래 선언을 넣는다
     background: #1d4ed8;
  */
</style>
</head>
<body>
  <!-- TODO 4: 파일 선택 입력을 놓고 file-input 클래스를 단다 -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 버튼만 파랗고 둥근지, 파일 이름 글자가 버튼과 떨어져 있는지, 버튼에 마우스를 올리면 버튼만 진한 파랑으로 서서히 바뀌는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
