# css/responsive/05 — Fluid Typography — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 뷰포트 300px 에서 제목 크기 (예측)

```css
/* 질문용 발췌 — 1rem = 16px 로 둔다 */
.fluid-heading { font-size: clamp(1.25rem, 1rem + 2vw, 2.5rem); }
```

- 뷰포트 너비가 300px 일 때 제목의 계산된 글자 크기는 몇 px 인가?

### 2. 아주 좁을 때와 아주 넓을 때의 본문 (예측)

```css
/* 질문용 발췌 — 1rem = 16px 로 둔다 */
.fluid-body { font-size: clamp(0.875rem, 0.75rem + 0.5vw, 1.125rem); }
```

- 뷰포트 너비가 320px 일 때 본문 글자 크기는 몇 px 인가?
- 뷰포트 너비가 1600px 일 때 본문 글자 크기는 몇 px 인가?

### 3. 양 끝을 정하고 가운데 식 구하기 (예측)

```css
/* 질문용 발췌 — 뷰포트 320px 에서 16px, 1120px 에서 24px 이 되게 하려 한다 (1rem = 16px) */
.lead { font-size: clamp(1rem, /* ? */, 1.5rem); }
```

- `/* ? */` 자리에 들어갈 `rem + vw` 꼴의 이상적 값은 무엇인가?

### 4. 이상적 값에 `rem` 을 섞는 까닭 (왜)

- 이상적 값을 `3vw` 하나로 쓰지 않고 `1rem + 2vw` 처럼 `rem` 을 섞으면 무엇이 달라지는가?

### 5. 미디어 쿼리와 비교한 「브레이크포인트 없이」 (연결)

- 미디어 쿼리로 너비마다 `font-size` 를 바꾸는 방식과 `clamp()` 방식은 창을 천천히 넓힐 때 글자가 변하는 모양이 어떻게 다른가?

### 6. 캡션이 실제로 움직이는 구간 (경계)

- `.fluid-caption` 의 `clamp(0.7rem, 0.6rem + 0.3vw, 0.85rem)` 은 뷰포트 너비가 대략 몇 px 에서 몇 px 사이일 때만 크기가 변하는가?

### 7. 주석의 「20px ~ 40px」 이 맞지 않게 되는 경우 (경계)

- 정답 코드 주석의 「20px ~ 40px 사이 유동」이라는 설명은 어떤 조건이 바뀌면 틀리게 되는가?

### 8. 고정 `12px` 글자와 `clamp()` 글자 (연결)

- 사용자가 브라우저 기본 글꼴 크기를 키우면 `.formula-code` 의 글자와 `.fluid-heading` 의 글자는 각각 어떻게 반응하는가?

## 실습

### 실습 1. 제목 · 본문 · 캡션이 화면 너비를 따라 커지는 유동 타이포 데모

**만들 것** — 제목 · 본문 · 캡션 세 단계 글자가 미디어 쿼리 없이 뷰포트 너비를 따라 부드럽게 커지고 줄어드는 예시 상자와, `clamp()` 구조를 보여 주는 공식 상자를 만든다.

**요구 조건**
1. 루트 `.fluid-type-demo` 안에 예시 상자 `.fluid-example` 과 공식 상자 `.fluid-formula` 를 차례로 둔다.
2. 예시 상자에는 제목(`h2.fluid-heading`) · 본문(`p.fluid-body`) · 캡션(`span.fluid-caption`) 을 차례로 둔다.
3. 제목은 `clamp()` 로 최소 `1.25rem`, 최대 `2.5rem` 사이에서, 이상적 값 `1rem + 2vw` 를 따라 변한다.
4. 본문은 `clamp()` 로 최소 `0.875rem`, 최대 `1.125rem` 사이에서, 이상적 값 `0.75rem + 0.5vw` 를 따라 변한다.
5. 캡션은 `clamp()` 로 최소 `0.7rem`, 최대 `0.85rem` 사이에서, 이상적 값 `0.6rem + 0.3vw` 를 따라 변한다.
6. 공식 상자에는 제목 「clamp() 구조」 와 공식 코드(`code.formula-code`) 를 둔다.
7. 공식 코드는 공백과 줄바꿈을 그대로 보존하는 블록으로 보여 화살표 줄이 맞춰진 채 놓인다.
8. 미디어 쿼리는 쓰지 않는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Fluid Typography 연습</title>
<style>
  .fluid-type-demo { font-family: system-ui, sans-serif; }
  .fluid-example { background: #f8fafc; border-radius: 12px; padding: 24px; margin-bottom: 16px; }
  .fluid-heading {
    /* TODO: 최소 1.25rem · 이상적 1rem + 2vw · 최대 2.5rem */
    color: #1e293b; margin: 0 0 12px 0; line-height: 1.2;
  }
  .fluid-body {
    /* TODO: 최소 0.875rem · 이상적 0.75rem + 0.5vw · 최대 1.125rem */
    color: #475569; line-height: 1.6; margin: 0 0 8px 0;
  }
  .fluid-caption {
    /* TODO: 최소 0.7rem · 이상적 0.6rem + 0.3vw · 최대 0.85rem */
    color: #94a3b8;
  }
  .fluid-formula { background: #1e293b; border-radius: 8px; padding: 14px; }
  .formula-title { font-size: 12px; font-weight: 700; color: #f59e0b; margin-bottom: 8px; }
  .formula-code {
    font-size: 12px; color: #e2e8f0; line-height: 1.6;
    /* TODO: 공백 · 줄바꿈 보존, 블록으로 표시 */
  }
</style>
</head>
<body>
<div class="fluid-type-demo">
  <!-- TODO: 예시 상자 — 제목 h2 · 본문 p · 캡션 span -->

  <!-- TODO: 공식 상자 — 제목 div 와 아래 공식 코드를 담은 code -->
  <!--
font-size: clamp(최소값, 이상적값, 최대값);

/* 예시 */
font-size: clamp(1rem, 0.5rem + 2vw, 2.5rem);
           ↑         ↑              ↑
      16px 이하   뷰포트 비례     40px 이상
      로 줄지 않음  크기 계산     으로 커지지 않음
  -->
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열고 창 너비를 천천히 줄였다 늘려 본다. 개발자 도구에서 제목 · 본문 · 캡션의 계산된 `font-size` 가 너비를 따라 끊김 없이 변하다가 양 끝에서 멈추는지, 공식 코드의 화살표 줄이 줄바꿈과 공백을 지킨 채 보이는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
