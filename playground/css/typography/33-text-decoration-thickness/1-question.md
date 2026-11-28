# css/typography/33 — text-decoration-thickness — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 글자 크기를 두 배로 키우면 (예측)

```css
/* 질문용 발췌 */
.a { text-decoration: underline; text-decoration-thickness: 2px;   font-size: 18px; }
.b { text-decoration: underline; text-decoration-thickness: 0.1em; font-size: 18px; }
.c { text-decoration: underline; text-decoration-thickness: 10%;   font-size: 18px; }
/* 세 요소 모두 font-size 를 36px 로 바꾼다 */
```

- 바꾸기 전과 후에 세 요소의 밑줄 두께는 각각 몇 px 인가?

### 2. 밑줄을 켜지 않고 두께만 주면 (예측)

```css
/* 질문용 발췌 */
p { text-decoration-thickness: 5px; font-size: 18px; }
```

- 이 `p` 의 글자 아래에는 무엇이 보이는가?

### 3. 호버에 두께를 바꾸는 링크 (예측)

```css
/* 질문용 발췌 */
a { text-decoration: underline; text-decoration-thickness: 1px;
    transition: text-decoration-thickness .3s; }
a:hover { text-decoration-thickness: 4px; }
```

- 마우스를 올렸다가 뗄 때 밑줄은 어떻게 바뀌는가?

### 4. 제목과 본문이 섞인 문서에서 em 이나 % 를 권하는 까닭 (왜)
- 크기가 다른 글자에 같은 스타일을 줄 때 px 보다 em · % 가 나은 이유는 무엇인가?

### 5. 값을 하나도 주지 않은 밑줄의 두께 (경계)
- 두께를 지정하지 않은 밑줄의 두께는 누가 정하고, 그 두께가 어떤 브라우저에서나 같다고 기대할 수 있는가?

### 6. 부모에 준 두께와 자식 요소의 값 (경계)
- 부모에 `text-decoration-thickness: 3px` 을 주고 자식에는 아무것도 주지 않았을 때, 자식 요소의 이 속성 값은 무엇인가?

### 7. from-font 와 글꼴의 관계 (연결)
- 같은 `from-font` 를 쓴 두 문단의 밑줄 두께가 다를 수 있다면, 그 차이는 무엇과 연결되는가?

### 8. text-decoration 과 이 속성의 역할 나누기 (연결)
- `text-decoration: underline` 과 `text-decoration-thickness` 는 각각 무엇을 맡고, 둘은 어떻게 함께 쓰이는가?

## 실습

### 실습 1. 두께가 다른 밑줄 세 단락 만들기

**만들 것** — 같은 글자 크기의 세 단락에 밑줄을 긋고, 밑줄 두께만 얇게 · 중간 · 두껍게 다르게 한다.

**요구 조건**
1. 세 단락(`.thin` · `.medium` · `.thick`)에 모두 밑줄 장식을 켠다.
2. 밑줄 두께는 `text-decoration-thickness` 로만 정한다 — 글자 크기는 세 단락이 같게 둔다.
3. 각 단락의 두께는 단락 글자 안 괄호에 적힌 값을 따른다 — `.thin` 이 가장 얇고, `.thick` 이 가장 두껍고, `.medium` 이 그 사이다.
4. 두께는 글자 크기와 상관없는 고정 길이 단위로 쓴다.
5. 글자 크기와 단락 사이 간격은 시작 코드에 있는 값을 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-decoration-thickness 연습</title>
  <style>
    .thin {
      /* TODO: 밑줄을 켠다 */
      /* TODO: 얇은 두께 */
      font-size: 18px;
      margin-bottom: 4px;
    }

    .medium {
      /* TODO: 밑줄을 켠다 */
      /* TODO: 중간 두께 */
      font-size: 18px;
      margin-bottom: 4px;
    }

    .thick {
      /* TODO: 밑줄을 켠다 */
      /* TODO: 두꺼운 두께 */
      font-size: 18px;
    }
  </style>
</head>
<body>
  <p class="thin">Thin (1px) 얇은 밑줄</p>
  <p class="medium">Medium (3px) 중간 밑줄</p>
  <p class="thick">Thick (5px) 두꺼운 밑줄</p>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 세 단락의 글자 크기는 같고 밑줄 두께만 위에서 아래로 점점 굵어지는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
