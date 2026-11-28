# css/selectors/35 — :local-link — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 두 링크가 든 네비게이션 (예측)

```html
<!-- 질문용 발췌 — 이 문서의 주소는 page.html -->
<nav class="ll-nav">
  <a href="#section1" class="ll-link">섹션 1</a>
  <a href="https://example.com" class="ll-link">외부 링크</a>
</nav>
<style>
  .ll-link { background: #f3f4f6; }
  .ll-link:local-link { background: #22c55e; }
</style>
```

- `:local-link` 를 지원하는 브라우저라면 원본의 설명대로 어느 링크의 배경이 녹색이 되는가?

### 2. 호버와 묶어 쓴 규칙 (예측)

```css
/* 질문용 발췌 */
.ll-link:hover, .ll-link:local-link { font-weight: bold; }
```

- `:local-link` 를 모르는 브라우저에서 링크에 마우스를 올리면 글자가 굵어지는가?

### 3. 네비게이션 강조에 쓰는 까닭 (왜)

- 「현재 페이지」 링크를 강조할 때 `.ll-link:local-link` 가 손으로 단 `.current` 클래스보다 덜어 주는 일은 무엇인가?

### 4. 지원이 제한적인 선택자를 실제 사이트에 쓸 때 (왜)

- 원본 팁이 지원이 제한적이라고 경고하는데, 현재 페이지 표시가 꼭 보여야 하는 사이트에서는 왜 다른 방법을 함께 둬야 하는가?

### 5. 같은 네비게이션을 example.com 문서에 넣으면 (경계)

- 「외부 링크」(`https://example.com`)는 어떤 문서에 놓였을 때 `:local-link` 에 매칭될 수 있는가?

### 6. 프래그먼트가 붙은 링크의 매칭 범위 (경계)

- 주소창이 프래그먼트 없는 `page.html` 일 때 `#section1` 링크가 매칭된다는 원본의 주장은 어디서 의심을 받는가?

### 7. `:target` 과의 차이 (연결)

- `#section1` 링크를 눌렀을 때 `:local-link` 가 꾸미는 요소와 `:target` 이 꾸미는 요소는 각각 무엇인가?

### 8. `href` 없는 `<a>` (연결)

- `<a class="ll-link">이름</a>` 처럼 `href` 가 없는 요소는 왜 `:local-link` 의 후보조차 되지 못하는가?

## 실습

### 실습 1. 현재 위치를 강조하는 네비게이션

**만들 것** — 같은 페이지 앵커 링크와 외부 링크를 나란히 놓고, 현재 문서를 가리키는 링크만 강조되는 네비게이션을 만든다.

**요구 조건**
1. `nav.ll-nav` 는 플렉스 컨테이너로 안의 링크를 가로 한 줄로 늘어놓고, 링크 사이에 간격을 둔다.
2. 첫 링크는 같은 페이지의 `#section1` 을 가리키고 「섹션 1」이라고 적힌다.
3. 둘째 링크는 외부 사이트 `https://example.com` 을 가리키고 「외부 링크」라고 적힌다.
4. 두 링크 모두 `ll-link` 클래스를 갖고, 밑줄 없는 회색 버튼 모양이 기본이다(꾸밈 값은 시작 코드에 있다).
5. `ll-link` 중 현재 페이지 URL 을 가리키는 링크만 녹색 배경 · 흰 글자 · 굵은 글씨로 바뀐다 — 이 조건은 의사 클래스 하나로 고른다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:local-link 연습</title>
<style>
  .ll-nav {
    /* TODO: 플렉스 컨테이너로 만든다 */
    gap: 8px;
  }
  .ll-link {
    padding: 8px 16px;
    border-radius: 6px;
    text-decoration: none;
    background: #f3f4f6;
    color: #374151;
  }
  /* TODO: .ll-link 중 현재 페이지 URL 을 가리키는 링크를 고르는 선택자 */ {
    background: #22c55e;
    color: white;
    font-weight: bold;
  }
</style>
</head>
<body>
  <nav class="ll-nav">
    <a href="" class="ll-link">섹션 1</a>      <!-- TODO: 같은 페이지 앵커 -->
    <a href="" class="ll-link">외부 링크</a>   <!-- TODO: 외부 사이트 -->
  </nav>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 두 링크가 가로로 나란한지 본다. `:local-link` 를 지원하는 브라우저라면 「섹션 1」만 녹색이어야 하고, 지원하지 않는 브라우저라면 둘 다 회색이다(지원 여부는 확인 필요). 주소 끝에 `#section1` 을 붙였을 때와 뗐을 때를 비교해 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
