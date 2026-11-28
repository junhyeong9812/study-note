# css/visual/02 — text-shadow — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 오프셋이 모두 0 인 세 겹 그림자 (예측)

```css
/* 질문용 발췌 */
.neon { text-shadow: 0 0 10px #ff00ff, 0 0 30px #ff00ff, 0 0 60px #ff00ff; color: #fff; }
```

- 그림자는 글자의 어느 쪽으로 치우쳐 보이나?
- 글자에서 가까운 곳과 먼 곳 가운데 어디가 더 진한 핑크로 보이나?

### 2. 네 대각선 방향 1px 그림자 (예측)

```css
/* 질문용 발췌 */
.outline { text-shadow: -1px -1px 0 #3b82f6, 1px -1px 0 #3b82f6, -1px 1px 0 #3b82f6, 1px 1px 0 #3b82f6; color: white; }
```

- 흰 글자 둘레는 어떻게 보이나?

### 3. 부모에만 준 그림자 (예측)

```html
<!-- 질문용 발췌 -->
<div style="text-shadow: 2px 2px 0 gray">
  <p>첫째</p>
  <p style="text-shadow: none">둘째</p>
</div>
```

- 「첫째」와 「둘째」 가운데 그림자가 붙는 글자는 무엇인가?

### 4. 네온을 같은 색 여러 겹으로 만드는 까닭 (왜)

- 흐림이 큰 그림자 한 겹이 아니라 흐림을 달리한 여러 겹을 쌓는 까닭은 무엇인가?

### 5. 엠보스에서 두 그림자의 방향이 반대인 까닭 (왜)

- 밝은 그림자와 어두운 그림자를 서로 반대쪽으로 미는 까닭은 무엇인가?

### 6. 그림자를 키우는 값 (경계)

- `box-shadow` 처럼 그림자 자체를 넓히는 값을 `text-shadow` 에도 줄 수 있나?

### 7. 마우스를 올렸을 때 서서히 빛나기 (경계)

- `transition` 으로 `text-shadow` 의 흐림을 0 에서 크게 서서히 바꿀 수 있나?

### 8. `box-shadow` 와 나누어 쓰기 (연결)

- 카드 상자 둘레의 그림자와 카드 제목 글자의 그림자는 각각 어느 속성으로 주나?

## 실습

### 실습 1. 어두운 무대에 네온 · 엠보스 · 외곽선 글자 세우기

**만들 것** — 어두운 상자 안에 글자 셋을 세로로 가운데 맞춰 놓고, 각 글자에 `text-shadow` 로 네온 · 엠보스 · 외곽선 효과를 준다.

**요구 조건**

1. `.text-demos` 상자 안에 `NEON` · `Emboss` · `Outline` 세 글자 블록이 위에서 아래로 놓인다(구조와 꾸밈은 시작 코드에 있다).
2. `.neon` — 같은 핑크 그림자 세 겹을 쉼표로 잇는다. 세 겹 모두 오프셋은 0 이고, 흐림만 10 → 30 → 60 으로 커진다.
3. `.emboss` — 그림자 두 겹. 반투명 흰 그림자는 오른쪽 아래로 1씩, 반투명 검은 그림자는 왼쪽 위로 1씩 민다. 둘 다 흐림은 0 이다.
4. `.outline` — 같은 파란 그림자 네 겹. 왼쪽 위 · 오른쪽 위 · 왼쪽 아래 · 오른쪽 아래 네 대각선으로 1씩 밀고, 흐림은 0 이다.
5. 그림자 색은 시작 코드의 주석에 적힌 색을 쓴다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-shadow 연습</title>
  <style>
    .text-demos {
      display: flex;
      flex-direction: column;
      gap: 16px;
      align-items: center;
      padding: 20px;
      background: #1a1a2e;
      border-radius: 12px;
      max-width: 280px;
      margin: 0 auto;
    }
    .neon {
      /* TODO: text-shadow — 핑크 #ff00ff 세 겹 (오프셋 0, 흐림 10px / 30px / 60px) */
      color: #fff;
      font-size: 32px;
      font-weight: bold;
      letter-spacing: 8px;
    }
    .emboss {
      /* TODO: text-shadow — 흰색 rgba(255,255,255,0.3) 은 오른쪽 아래 1px, 검정 rgba(0,0,0,0.5) 은 왼쪽 위 1px, 흐림 0 */
      color: #6b7280;
      font-size: 24px;
      font-weight: bold;
    }
    .outline {
      /* TODO: text-shadow — 파랑 #3b82f6 네 대각선 방향 1px, 흐림 0 */
      color: white;
      font-size: 24px;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <div class="text-demos">
    <div class="neon">NEON</div>
    <div class="emboss">Emboss</div>
    <div class="outline">Outline</div>
  </div>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 `NEON` 둘레가 핑크로 번져 빛나는지, `Emboss` 가장자리에 밝은 선과 어두운 선이 반대쪽에 있는지, `Outline` 이 파란 테두리를 둘렀는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
