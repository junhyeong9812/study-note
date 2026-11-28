# css/color-background/18 — repeating-radial-gradient() — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 가운데는 빨강, 가장자리 바로 안쪽은 흰색

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

반복 단위는 30px(빨강 0~15px, 흰색 15~30px)이다.
160px 정사각형을 원으로 자르면 중심에서 가장자리까지 80px 이다.
거리별로 0~15 빨강, 15~30 흰색, 30~45 빨강, 45~60 흰색, 60~75 빨강, 75~80 흰색이다.
그래서 한가운데는 빨강, 가장자리 바로 안쪽은 5px 만 보이는 얇은 흰 띠다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

정지점 목록이 덮는 30px 가 한 마디가 되어 중심에서 바깥으로 되풀이된다(2-summary 「동작 방식 (1)」).
가장자리까지의 거리 80px 은 `border-radius: 50%` 가 정한다(2-summary 「동작 방식 (5)」).

### 2. 진한 파랑 띠는 4개

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

반복 단위는 20px(밝은 파랑 0~10px, 진한 파랑 10~20px)이다.
가장자리까지 80px 이므로 마디가 정확히 4번 들어간다.
진한 띠는 10~20, 30~40, 50~60, 70~80 의 4개이고, 가장 바깥 띠가 진한 파랑이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

80 ÷ 20 = 4 마디이고, 마디마다 진한 띠가 하나씩 있다(2-summary 「동작 방식 (1)」 · 「(5)」).

### 3. 가운데 빨강 원 하나와 바깥 전체 흰색

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

반지름 15px 의 빨강 원이 하나 그려지고, 그 바깥은 판 끝까지 흰색이 된다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

`radial-gradient()` 는 정지점 목록을 되풀이하지 않고, 마지막 정지점(흰색 30px) 바깥을 마지막 색으로 채운다(2-summary 「어디서 틀리나 4」).

### 4. 섞일 거리가 0 이기 때문이다

정지점 사이에서는 앞 색이 뒤 색으로 서서히 섞인다.
두 정지점이 같은 위치에 있으면 섞일 구간의 길이가 0 이라 그 자리에서 색이 즉시 바뀐다.
근거: 2-summary 「동작 방식 (2)」.

### 5. 마디가 맞닿는 곳의 색이 이어지기 때문이다

한 마디의 끝은 다음 마디의 시작과 바로 맞닿는다.
끝 색과 시작 색이 다르면 맞닿는 곳에 선이 생기고, 같으면 색이 이어져 이음매가 보이지 않는다.
근거: 2-summary 「동작 방식 (3)」, 원본 팁.

### 6. 한 마디가 이미 전체를 덮기 때문이다

위치가 없으면 정지점이 0~100% 로 고르게 퍼져 반복 단위가 그라디언트 전체 길이가 된다.
되풀이할 자리가 남지 않으니 `radial-gradient()` 와 다를 바 없어 보인다.
근거: 2-summary 「어디서 틀리나 1」.

### 7. 서서히 바뀌지 않는다

원본 데이터에서 이 함수는 애니메이션 가능하지 않다.
그래서 `transition` 을 걸어도 그라디언트가 중간 단계 없이 바뀐다 (코드에서 읽은 것 — 렌더 실측 아님).
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 6」.

### 8. `circle` 은 고리의 모양, `border-radius` 는 판의 바깥 모양

`circle` 은 고리 하나하나를 동그랗게 만든다.
그라디언트 자체는 정사각형 상자 전체를 칠하므로, 판의 바깥 윤곽을 원으로 잘라 내는 일은 `border-radius: 50%` 가 한다.
둘이 함께 있어야 동그란 고리가 동그란 판 안에 담긴 과녁이 된다.
근거: 2-summary 「동작 방식 (4)」 · 「(5)」.

## 실습 정답

### 실습 1. 파랑 동심원과 빨강 과녁 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 첫 판을 원형 반복 방사형 그라디언트로 | `.circles { background: repeating-radial-gradient(circle, …) }` |
| 2. 같은 두께의 밝은 · 진한 파랑 띠 | `#3b82f6 0px, #3b82f6 10px, #1e40af 10px, #1e40af 20px` |
| 3. 경계가 딱 끊김 | `#3b82f6 10px, #1e40af 10px` (같은 위치 두 정지점) |
| 4. 빨강 · 흰 과녁, 가운데 빨강 | `.target { background: repeating-radial-gradient(circle, #ef4444 0px, …) }` |
| 5. 과녁 띠가 더 두꺼움 | `#ef4444 15px, white 15px, white 30px` |
| 6. 중심 위치를 적지 않음 | 두 함수 모두 `at` 이 없음 |
| 7. 가운데 글자 | `display: flex; align-items: center; justify-content: center;` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/color-background/reference/repeating-radial-gradient.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- 문서 루트: 한국어 페이지 -->
<head>
<!-- 메타 영역 시작 -->
<meta charset="utf-8">
<!-- 문자 인코딩: UTF-8 -->
<title>repeating-radial-gradient() - 방사형 그라디언트를 반복하여 동심원 패턴 등을 생성</title>
<!-- 브라우저 탭 제목 -->
<!--
  [색상 & 배경] repeating-radial-gradient()
  설명: 방사형 그라디언트를 반복하여 동심원 패턴 등을 생성
  구문: repeating-radial-gradient([<shape> <size> at <position>,]? <color-stop-list>)
  팁: 과녁, 레이더, 동심원 물결 효과에 활용. 반복 단위의 시작/끝 색상을 맞추면 매끄러운 반복.
-->
<style>
  /* .circles: 파랑 동심원 패턴 */
  .circles {
    background: repeating-radial-gradient(circle, #3b82f6 0px, #3b82f6 10px, #1e40af 10px, #1e40af 20px);  /* 원형, 10px 밝은 파랑 + 10px 진한 파랑 반복 */
    width: 160px;                                /* 가로 160px */
    height: 160px;                               /* 세로 160px */
    border-radius: 50%;                          /* 원형 */
    margin-bottom: 8px;                          /* 아래 여백 8px */
    display: flex;                               /* 플렉스 */
    align-items: center;                         /* 세로 가운데 */
    justify-content: center;                     /* 가로 가운데 */
    color: white;                                /* 흰 글씨 */
    font-weight: bold;                           /* 굵은 글씨 */
    text-shadow: 0 1px 3px rgba(0,0,0,0.5);      /* 검정 50% 투명 그림자 */
  }
  /* .target: 빨강-흰색 과녁 패턴 */
  .target {
    background: repeating-radial-gradient(circle, #ef4444 0px, #ef4444 15px, white 15px, white 30px);  /* 원형, 15px 빨강 + 15px 흰색 반복 */
    width: 160px;                                /* 가로 160px */
    height: 160px;                               /* 세로 160px */
    border-radius: 50%;                          /* 원형 */
    display: flex;                               /* 플렉스 */
    align-items: center;                         /* 세로 가운데 */
    justify-content: center;                     /* 가로 가운데 */
    font-weight: bold;                           /* 굵은 글씨 */
  }
</style>
</head>
<body>
  <!-- 동심원 -->
  <div class="circles">동심원</div>
  <!-- 과녁 -->
  <div class="target">과녁 패턴</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.circles { background: repeating-radial-gradient(circle, #3b82f6 0px, #3b82f6 10px, #1e40af 10px, #1e40af 20px); width: 160px; height: 160px; border-radius: 50%; margin-bottom: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; text-shadow: 0 1px 3px rgba(0,0,0,0.5); }
.target { background: repeating-radial-gradient(circle, #ef4444 0px, #ef4444 15px, white 15px, white 30px); width: 160px; height: 160px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 반복 단위의 길이는 마지막 정지점에서 첫 정지점을 뺀 값이다(동심원 20px, 과녁 30px).
- 띠의 경계를 또렷하게 하려고 앞 띠의 끝과 뒤 띠의 시작을 같은 위치에 둔다.
- 첫 정지점이 빨강 `0px` 이므로 과녁의 한가운데가 빨강이 된다.
- `at` 을 생략해 고리가 판의 가운데에서 퍼진다.
- 둥근 판의 윤곽은 그라디언트가 아니라 `border-radius: 50%` 가 만든다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
