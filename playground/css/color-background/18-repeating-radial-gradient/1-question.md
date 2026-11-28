# css/color-background/18 — repeating-radial-gradient() — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 15px 빨강 + 15px 흰색 과녁의 가운데와 가장자리 (예측)

```css
/* 질문용 발췌 */
.target {
  width: 160px; height: 160px; border-radius: 50%;
  background: repeating-radial-gradient(circle, #ef4444 0px, #ef4444 15px, white 15px, white 30px);
}
```

- 원의 한가운데는 무슨 색이고, 원의 가장자리 바로 안쪽 띠는 무슨 색인가?

### 2. 10px 씩 번갈아 나오는 파랑 동심원 (예측)

```css
/* 질문용 발췌 */
.circles {
  width: 160px; height: 160px; border-radius: 50%;
  background: repeating-radial-gradient(circle, #3b82f6 0px, #3b82f6 10px, #1e40af 10px, #1e40af 20px);
}
```

- 중심에서 원의 가장자리까지 진한 파랑(`#1e40af`) 띠는 몇 개가 보이는가?

### 3. `repeating-` 를 떼어 내면 (예측)

- 퀴즈 1 의 코드에서 함수 이름만 `radial-gradient` 로 바꾸면 원판은 어떤 모습이 되는가?

### 4. 같은 위치에 정지점 두 개를 두는 까닭 (왜)

- `#ef4444 15px, white 15px` 처럼 두 색을 같은 위치에 두면 왜 경계가 흐려지지 않고 딱 끊기는가?

### 5. 시작 색과 끝 색을 맞추라는 팁 (왜)

- 반복 단위의 시작 색과 끝 색을 같게 맞추면 왜 반복이 매끄러워지는가?

### 6. 정지점에 위치를 안 적으면 (경계)

- `repeating-radial-gradient(circle, red, white)` 처럼 위치 없이 쓰면 왜 반복이 눈에 띄지 않는가?

### 7. 그라디언트를 서서히 바꾸기 (경계)

- `:hover` 에서 띠 색을 바꾼 다른 `repeating-radial-gradient()` 를 주고 `transition` 을 걸면 색이 서서히 바뀌는가?

### 8. 둥근 판 모양은 누가 만드나 (연결)

- 과녁 예제가 정사각형이 아니라 동그란 판으로 보이는 데 그라디언트의 `circle` 과 `border-radius` 는 각각 어떤 몫을 하는가?

## 실습

### 실습 1. 파랑 동심원과 빨강 과녁 만들기

**만들 것** — 둥근 판 두 개를 만들고, 하나는 두 가지 파랑이 번갈아 나오는 동심원, 다른 하나는 빨강과 흰색이 번갈아 나오는 과녁으로 칠한다.

**요구 조건**
1. 첫 판(`.circles`)의 배경을 원형(`circle`) 반복 방사형 그라디언트로 칠한다.
2. 첫 판의 반복 단위는 밝은 파랑 띠와 진한 파랑 띠 두 개이고, 두 띠의 두께는 같다.
3. 띠와 띠의 경계는 섞이지 않고 딱 끊긴다(같은 위치에 정지점 두 개).
4. 두 번째 판(`.target`)도 같은 함수로 빨강 띠와 흰 띠가 번갈아 나오는 과녁을 만들고, 한가운데는 빨강이다.
5. 과녁의 띠는 첫 판의 띠보다 두껍다(두께는 시작 코드 주석의 값을 쓴다).
6. 두 판 모두 중심 위치를 따로 적지 않아 고리가 판의 가운데에서 퍼진다.
7. 각 판 가운데에 글자(「동심원」, 「과녁 패턴」)가 놓인다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>repeating-radial-gradient() 연습</title>
<style>
  .circles {
    /* TODO: 원형 반복 방사형 그라디언트
       색: #3b82f6(밝은 파랑) · #1e40af(진한 파랑), 띠 두께 각 10px */
    width: 160px;
    height: 160px;
    border-radius: 50%;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    text-shadow: 0 1px 3px rgba(0,0,0,0.5);
  }
  .target {
    /* TODO: 원형 반복 방사형 그라디언트
       색: #ef4444(빨강) · white, 띠 두께 각 15px, 가운데는 빨강 */
    width: 160px;
    height: 160px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
  }
</style>
</head>
<body>
  <div class="circles">동심원</div>
  <div class="target">과녁 패턴</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 두 판에 띠가 일정한 두께로 되풀이되는지, 경계가 흐리지 않고 또렷한지, 과녁의 한가운데가 빨강인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
