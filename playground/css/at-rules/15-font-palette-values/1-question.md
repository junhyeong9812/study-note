# css/at-rules/15 — @font-palette-values — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 팔레트를 정의만 해 둔 문서 (예측)

```css
/* 질문용 발췌 */
@font-palette-values --custom-palette {
  font-family: 'Noto Color Emoji';
  base-palette: 0;
  override-colors: 0 #ff6b6b, 1 #4ecdc4;
}
.fpv-demo { font-size: 24px; }
```

- `.fpv-demo` 안의 🎨 이모지 색은 정의 전과 비교해 어떻게 되나?

### 2. 한 색만 바꾼 팔레트에서 나머지 색 (예측)

```css
/* 질문용 발췌 */
@font-palette-values --one {
  font-family: 'Noto Color Emoji';
  base-palette: 0;
  override-colors: 1 #4ecdc4;
}
```

- 이 팔레트를 적용하면 0번 색과 2번 색은 무엇으로 그려지나?

### 3. 정답 코드를 그대로 열면 보이는 상자 (예측)
- 정의와 `font-palette` 줄이 모두 주석 안에 있는 원본 예제를 브라우저로 열면 🎨 는 어떤 색으로 그려지나?

### 4. 팔레트 정의에 `font-family` 를 꼭 적는 까닭 (왜)
- 색 번호만 적으면 될 것 같은데 왜 대상 폰트 패밀리를 함께 적어야 하나?

### 5. 두 개의 「0」 (경계)
- `base-palette: 0` 의 0 과 `override-colors: 0 #ff6b6b` 의 0 은 각각 무엇을 가리키나?

### 6. 단색 폰트에 팔레트를 입히면 (경계)
- 보통 본문용 단색 폰트로 그려지는 글자에 `font-palette: --custom-palette;` 를 달면 무슨 일이 일어나나?

### 7. `@keyframes` 와 닮은 점 (연결)
- `@font-palette-values` 와 `@keyframes` 는 「정의」와 「사용」을 나누는 방식에서 어떻게 닮았나?

## 실습

### 실습 1. 컬러 이모지 팔레트를 정의하고 적용하는 데모 만들기

**만들 것** — 컬러 이모지 한 줄이 든 상자에, 이모지 폰트의 팔레트를 바꾸는 정의와 적용 줄을 써 넣는다.

**요구 조건**
1. `body` 안에 `class="fpv-demo"` 인 문단을 두고 내용은 「🎨 컬러 폰트 팔레트」로 한다.
2. `--custom-palette` 라는 이름으로 `@font-palette-values` 규칙을 정의한다.
3. 그 규칙의 대상 폰트는 `'Noto Color Emoji'` 다.
4. 출발 팔레트로 0번 내장 팔레트를 고른다.
5. 0번 색과 1번 색을 시작 코드 주석에 적힌 두 색으로 바꾼다(한 줄에 쉼표로 이어 적기).
6. `.fpv-demo` 에 `font-palette` 로 `--custom-palette` 를 적용하는 줄을 단다.
7. 정답 코드는 2~6의 정의와 적용 줄을 주석으로 감싼 개념 시연이다 — 다 쓴 뒤 같은 상태로 맞춰 두고, 주석을 풀어 직접 확인해 봐도 된다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>@font-palette-values</title>
  <style>
    /* 쓸 색: 0번 → #ff6b6b, 1번 → #4ecdc4 */
    /* TODO: @font-palette-values 로 --custom-palette 정의 (대상 폰트 · 출발 팔레트 · 바꿀 색) */

    .fpv-demo {
      font-size: 24px;
      padding: 16px;
      background: #f3f4f6;
      border-radius: 8px;
      /* TODO: 정의한 팔레트를 이 요소에 적용 */
    }
  </style>
</head>
<body>
  <!-- TODO: class="fpv-demo" 문단 -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 연회색 상자 안에 「🎨 컬러 폰트 팔레트」가 보이는지 본다. 주석을 풀었을 때 🎨 의 색이 달라지는지는 대상 폰트가 쓰이는 환경에서만 볼 수 있다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
