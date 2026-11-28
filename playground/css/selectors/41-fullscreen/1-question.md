# css/selectors/41 — :fullscreen — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 박스를 클릭한 뒤 바뀌는 것 (예측)

```css
/* 질문용 발췌 */
.fs-demo { background: #1e293b; color: white; border-radius: 12px; }
.fs-demo:fullscreen { background: #0f172a; border-radius: 0; }
.fs-demo:fullscreen p { font-size: 32px; }
```

- `onclick="this.requestFullscreen()"` 인 `.fs-demo` 를 눌러 전체 화면이 되면, 배경 · 모서리 · 글자색 · 안내 문구 크기는 각각 어떻게 되나?

### 2. 같은 클래스의 박스가 둘일 때 (예측)

```html
<!-- 질문용 발췌 -->
<div class="fs-demo" id="a" onclick="this.requestFullscreen()"><p>A</p></div>
<div class="fs-demo" id="b" onclick="this.requestFullscreen()"><p>B</p></div>
```

- `#a` 만 클릭해 전체 화면이 되었을 때, `#b` 안의 `p` 에 `.fs-demo:fullscreen p` 규칙이 적용되나?

### 3. 전체 화면 규칙이 평소 규칙을 이기는 까닭 (왜)

- 두 규칙이 모두 `background` 를 정하는데, 전체 화면 중에 `.fs-demo:fullscreen` 쪽 값이 쓰이는 까닭은 무엇인가?

### 4. `:fullscreen` 규칙만으로는 전체 화면이 되지 않는다 (왜)

- `onclick` 을 지우고 CSS 만 남기면 박스가 전체 화면이 되지 않는 까닭은 무엇인가?

### 5. 전체 화면에서 나온 뒤 (경계)

- 전체 화면을 해제하면 배경 · 모서리 · 글자 크기는 어떻게 되며, 그렇게 되도록 따로 써야 할 코드가 있나?

### 6. 요소 뒤의 빈 영역 (경계)

- 전체 화면 요소 뒤에 깔린 배경을 `.fs-demo:fullscreen { background: … }` 로 바꿀 수 있나, 없다면 무엇을 써야 하나?

### 7. `:fullscreen` 과 `::backdrop` 의 콜론 수 (연결)

- 하나는 콜론 하나, 하나는 콜론 둘인 까닭은 두 선택자가 각각 무엇을 고르기 때문인가?

### 8. `:hover` 와 견주기 (연결)

- `:hover` 와 `:fullscreen` 은 둘 다 상태를 고르는데, 각 상태를 만드는 주체는 어떻게 다른가?

## 실습

### 실습 1. 클릭하면 전체 화면으로 커지는 안내 박스

**만들 것** — 누르면 전체 화면이 되고, 전체 화면인 동안에만 모양이 바뀌는 박스 하나를 만든다.

**요구 조건**
1. 박스를 클릭하면 클릭된 그 박스가 Fullscreen API 로 전체 화면이 된다.
2. 전체 화면인 동안에만 박스 배경이 더 어두운 색으로 바뀌고, 둥근 모서리가 각진 모서리가 된다.
3. 전체 화면인 동안에만 박스 안의 안내 문구(`p`)가 커진다.
4. 전체 화면이 아닐 때는 시작 코드의 평소 모양 그대로 보인다(되돌리는 코드를 쓰지 않는다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:fullscreen 연습</title>
<style>
  .fs-demo {
    width: 200px;
    height: 120px;
    background: #1e293b;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    cursor: pointer;
  }
  /* TODO: .fs-demo 가 전체 화면일 때만 맞는 선택자를 ??? 자리에 쓴다 */
  ??? {
    background: #0f172a;
    border-radius: 0;
  }
  /* TODO: 전체 화면인 .fs-demo 안의 p 만 맞는 선택자를 ??? 자리에 쓴다 */
  ??? {
    font-size: 32px;
  }
</style>
</head>
<body>
  <!-- TODO: 클릭되면 이 div 자신을 전체 화면으로 띄우는 코드를 onclick 에 쓴다 -->
  <div class="fs-demo" onclick="">
    <p>클릭하면 전체 화면</p>
  </div>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 박스를 누른다; 화면 전체가 되며 배경이 어두워지고 모서리가 각지고 문구가 커지는지, 전체 화면을 나오면 원래 작은 둥근 박스로 돌아오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
