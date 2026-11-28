# css/visual/02 — text-shadow — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 어느 쪽으로도 치우치지 않고, 가까운 곳이 더 진하다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
그림자는 한쪽으로 치우치지 않고 글자 둘레 사방으로 고르게 번진다.
글자 가까운 곳은 세 겹이 모두 겹쳐 진한 핑크로, 먼 곳은 흐림 60px 인 겹만 닿아 옅은 핑크로 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
세 겹 모두 오프셋이 `0 0` 이라 그림자 중심이 글자 자리 그대로다.
흐림이 10 → 30 → 60 으로 커지므로 퍼지는 범위가 겹마다 넓어지고, 가까운 영역일수록 더 많은 겹이 쌓인다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 파란 테두리를 두른 것처럼 보인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
흰 글자 둘레에 1px 두께의 또렷한 파란 선이 둘러진 것처럼 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
같은 파란색 복사본 네 개가 네 대각선 방향으로 1px 씩 밀려 글자 가장자리 바깥을 덮는다.
흐림이 0 이라 번지지 않고 선처럼 또렷하다.
근거: 2-summary 「동작 방식 (4)」.

### 3. 「첫째」에만 붙는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
「첫째」 글자에는 회색 그림자가 붙고, 「둘째」에는 붙지 않는다.

**왜 그런가**
`text-shadow` 는 상속되므로 지정하지 않은 「첫째」는 부모의 `2px 2px 0 gray` 를 이어받는다.
「둘째」는 `text-shadow: none` 을 직접 지정해 상속값을 대신했다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 3」.

### 4. 가까운 곳은 진하고 바깥은 넓게 퍼지는 빛을 함께 얻기 위해서다

한 겹만으로는 흐림이 작으면 번짐이 좁고, 흐림이 크면 글자 근처가 옅어진다.
흐림을 달리한 같은 색 그림자를 겹치면 작은 흐림이 글자 근처를 진하게, 큰 흐림이 바깥을 넓게 맡아 네온 사인 같은 빛이 된다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 5. 한 방향에서 빛이 비친 것처럼 보이게 하려고

한쪽 가장자리에 밝은 선, 반대쪽 가장자리에 어두운 선이 생기면 빛이 한 방향에서 온 듯 읽혀 글자가 입체로 보인다.
두 그림자 모두 흐림 0 이라 선이 또렷하고, 알파가 있어 바탕색과 섞인다.
솟아 보이는지 파여 보이는지는 방향 배치에 달렸고, 맞바꾸면 반대로 읽힌다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 6. 줄 수 없다 — `spread-radius` 가 없다

`text-shadow` 의 문법에는 `spread-radius` 자리가 없다. 이것이 `box-shadow` 와의 차이다.
그림자를 두껍게 보이려면 흐림을 키우거나 여러 방향으로 여러 겹을 쌓는다(외곽선 효과가 그 예다).
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 1」.

### 7. 바꿀 수 있다 — 애니메이션 가능한 속성이다

`text-shadow` 는 애니메이션 가능한 속성이라, `transition: text-shadow` 를 걸면 흐림 0 과 큰 값 사이가 서서히 채워진다.
근거: 2-summary 「동작 방식 (6)」.

### 8. 상자 둘레는 `box-shadow`, 글자는 `text-shadow`

`box-shadow` 는 상자 둘레에 그림자를 그리고 spread 값이 있다.
`text-shadow` 는 글자 모양을 따라 그림자를 그리고 상속된다.
그래서 카드 상자에는 `box-shadow`, 제목 글자에는 `text-shadow` 를 준다.
근거: 2-summary 「언제 쓰고 언제 안 쓰나」 · 「용어 풀이」.

## 실습 정답

### 실습 1. 어두운 무대에 네온 · 엠보스 · 외곽선 글자 세우기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 세 글자 블록을 세로로 가운데 맞춰 놓기 | `.text-demos` 의 `display: flex` · `flex-direction: column` · `align-items: center`, `<div class="neon">` · `.emboss` · `.outline` |
| 2. 네온 — 같은 핑크 세 겹, 오프셋 0, 흐림 10 → 30 → 60 | `.neon { text-shadow: 0 0 10px #ff00ff, 0 0 30px #ff00ff, 0 0 60px #ff00ff; }` |
| 3. 엠보스 — 흰색 오른쪽 아래, 검정 왼쪽 위, 흐림 0 | `.emboss { text-shadow: 1px 1px 0 rgba(255,255,255,0.3), -1px -1px 0 rgba(0,0,0,0.5); }` |
| 4. 외곽선 — 같은 파랑 네 대각선, 흐림 0 | `.outline { text-shadow: -1px -1px 0 #3b82f6, 1px -1px 0 #3b82f6, -1px 1px 0 #3b82f6, 1px 1px 0 #3b82f6; }` |
| 5. 주석에 적힌 색 쓰기 | 세 `text-shadow` 선언의 색 값 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/visual/reference/visual--text-shadow.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- 문서 언어: 한국어 -->
<head>
  <meta charset="utf-8">
  <!-- 문자 인코딩: UTF-8 -->
  <title>text-shadow - 텍스트에 그림자 효과를 추가합니다</title>
  <!--
    [시각 효과] text-shadow
    설명: 텍스트에 그림자 효과를 추가합니다
    구문: text-shadow: none | <shadow>#
    팁: 네온 효과는 여러 겹의 blur가 큰 그림자로 구현. spread-radius는 없음(box-shadow와 차이). 상속되므로 부모에 설정하면 자식 텍스트에도 적용.
  -->
  <style>
    /* .text-demos: 어두운 무대에 그림자 효과 텍스트 묶음 */
    .text-demos {
      display: flex;                              /* 플렉스 */
      flex-direction: column;                     /* 세로 배치 */
      gap: 16px;                                  /* 글자 사이 16px */
      align-items: center;                        /* 가로 중앙 정렬 */
      padding: 20px;                              /* 안쪽 여백 20px */
      background: #1a1a2e;                        /* 어두운 남보라 배경 - 네온 효과 강조 */
      border-radius: 12px;                        /* 모서리 둥글게 */
      max-width: 280px;                           /* 최대 너비 280px */
      margin: 0 auto;                             /* 가로 중앙 */
    }
    /* .neon: 다겹 핫핑크 글로우 - 네온 사인 느낌 */
    .neon {
      text-shadow: 0 0 10px #ff00ff, 0 0 30px #ff00ff, 0 0 60px #ff00ff;  /* 10/30/60px 점점 퍼지는 핑크 글로우 - 네온 사인 효과 */
      color: #fff;                                /* 흰 글자 - 글로우 색과 대비 */
      font-size: 32px;                            /* 글자 32px */
      font-weight: bold;                          /* 굵게 */
      letter-spacing: 8px;                        /* 자간 8px - 네온 사인다운 간격 */
    }
    /* .emboss: 위/아래 두 그림자로 양각/음각 느낌 */
    .emboss {
      text-shadow: 1px 1px 0 rgba(255,255,255,0.3), -1px -1px 0 rgba(0,0,0,0.5);  /* 흰 그림자(우하단) + 검은 그림자(좌상단) - 입체 양각 */
      color: #6b7280;                             /* 회색 글자 */
      font-size: 24px;                            /* 글자 24px */
      font-weight: bold;                          /* 굵게 */
    }
    /* .outline: 4방향 그림자로 텍스트 외곽선 효과 (스트로크 대체) */
    .outline {
      text-shadow: -1px -1px 0 #3b82f6, 1px -1px 0 #3b82f6, -1px 1px 0 #3b82f6, 1px 1px 0 #3b82f6;  /* 4방향 1px 파란 그림자 - 텍스트 외곽선 효과 */
      color: white;                               /* 흰 글자 */
      font-size: 24px;                            /* 글자 24px */
      font-weight: bold;                          /* 굵게 */
    }
  </style>
</head>
<body>
  <!-- text-shadow 응용 효과 데모 -->
  <div class="text-demos">
    <!-- 어두운 무대 -->
    <div class="neon">NEON</div>
    <!-- 네온 사인 효과 -->
    <div class="emboss">Emboss</div>
    <!-- 양각 입체 효과 -->
    <div class="outline">Outline</div>
    <!-- 외곽선 효과 -->
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.text-demos { display: flex; flex-direction: column; gap: 16px; align-items: center; padding: 20px; background: #1a1a2e; border-radius: 12px; max-width: 280px; margin: 0 auto; }
.neon { text-shadow: 0 0 10px #ff00ff, 0 0 30px #ff00ff, 0 0 60px #ff00ff; color: #fff; font-size: 32px; font-weight: bold; letter-spacing: 8px; }
.emboss { text-shadow: 1px 1px 0 rgba(255,255,255,0.3), -1px -1px 0 rgba(0,0,0,0.5); color: #6b7280; font-size: 24px; font-weight: bold; }
.outline { text-shadow: -1px -1px 0 #3b82f6, 1px -1px 0 #3b82f6, -1px 1px 0 #3b82f6, 1px 1px 0 #3b82f6; color: white; font-size: 24px; font-weight: bold; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 세 효과 모두 그림자를 쉼표로 여러 겹 잇는 `<shadow>#` 의 응용이다.
- 네온은 오프셋 0 으로 사방에 고르게 번지게 하고, 흐림만 키워 진함과 퍼짐을 함께 만든다.
- 엠보스는 밝은 그림자와 어두운 그림자를 반대 방향으로 밀어 빛 방향을 흉내 낸다.
- 외곽선은 spread 가 없는 대신 네 대각선 방향 복사본으로 테두리를 만든다.
- 어두운 배경과 흰 글자색은 그림자 색과의 대비를 키워 효과가 잘 드러나게 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
