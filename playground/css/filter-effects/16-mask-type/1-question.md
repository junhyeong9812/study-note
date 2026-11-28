# css/filter-effects/16 — mask-type — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 흰 사각형과 검은 원을 담은 기본 마스크 (예측)

```html
<!-- 질문용 발췌 -->
<mask id="m">
  <rect width="100" height="100" fill="white"/>
  <circle cx="50" cy="50" r="30" fill="black"/>
</mask>
<rect width="100" height="100" fill="tomato" mask="url(#m)"/>
```

- 붉은 사각형은 화면에 어떤 모양으로 보이는가?

### 2. 같은 마스크에 `mask-type: alpha` 를 주면 (예측)

```html
<!-- 질문용 발췌 -->
<mask id="m" style="mask-type: alpha">
  <rect width="100" height="100" fill="white"/>
  <circle cx="50" cy="50" r="30" fill="black"/>
</mask>
<rect width="100" height="100" fill="tomato" mask="url(#m)"/>
```

- 1번과 비교해 붉은 사각형의 모양은 어떻게 달라지는가?

### 3. 회색 하나로 채운 마스크 (예측)

```html
<!-- 질문용 발췌 -->
<mask id="g">
  <rect width="100" height="100" fill="gray"/>
</mask>
<rect width="100" height="100" fill="tomato" mask="url(#g)"/>
```

- 붉은 사각형은 완전히 보이는가, 완전히 가려지는가, 아니면 그 사이인가?

### 4. 일반 `div` 에 건 `mask-type` (경계)

- `div { mask-type: alpha; }` 를 쓰면 그 `div` 의 모습은 어떻게 되는가?

### 5. `<svg>` 에 `mask-type` 을 써 두었을 때 (경계)

- `<svg style="mask-type: alpha">` 안에 있는 `<mask>` 는 어느 모드로 동작하는가?

### 6. 색 있는 아이콘을 마스크로 쓸 때 `alpha` 가 편한 까닭 (왜)

- 여러 색이 섞인 아이콘의 모양만 따내고 싶을 때 왜 `alpha` 가 `luminance` 보다 알맞은가?

### 7. 원본 예제가 시각 데모 대신 안내 박스만 두는 까닭 (왜)

- 이 항목의 예제가 일반 HTML 박스에 마스크 효과를 보여 주지 않는 까닭은 무엇인가?

### 8. `mask-type` 과 `mask-mode` (연결)

- 두 속성은 무엇을 똑같이 고르고, 어디에 쓰는지는 어떻게 다른가?

## 실습

### 실습 1. `mask-type` 안내 박스 만들기

**만들 것** — `mask-type` 이 SVG `<mask>` 요소 전용 속성이라는 것을 알리는 안내 박스 하나를 화면 가운데에 띄운다.

**요구 조건**

1. 문서는 HTML5 문서로, 언어는 한국어, 문자 인코딩은 UTF-8 로 둔다.
2. 브라우저 탭 제목에 속성 이름과 설명을 넣는다.
3. 본문에 `info` 클래스를 단 `div` 하나를 둔다.
4. 박스 안 문장은 「SVG <mask> 요소에 적용되는 속성입니다」이고, `<mask>` 가 태그로 해석되지 않고 글자 그대로 보여야 한다.
5. 박스 안 글자는 가운데 정렬한다.
6. 박스는 화면 가로 가운데에 놓이고, 위아래에 여백을 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="utf-8">
    <title><!-- TODO: 속성 이름과 설명 --></title>
    <style>
      .info {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        color: #475569;
        padding: 24px;
        border-radius: 8px;
        width: 260px;
        font-size: 14px;
        /* TODO: 글자 가운데 정렬 */
        /* TODO: 위아래 여백 + 가로 가운데 놓기 */
      }
    </style>
  </head>
  <body>
    <!-- TODO: info 박스 — <mask> 가 글자 그대로 보이게 -->
  </body>
</html>
```

**확인 방법** — 브라우저로 열어 박스가 가로 가운데에 놓였는지, 글자가 가운데 정렬됐는지, 문장 안에 `<mask>` 가 글자로 보이는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
