# web-api/19 — `passive` 와 스크롤 성능: 기본값이 바뀐 이유 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 「`passive` 면 `preventDefault` 가 무시된다」는 규칙의 첫 측정은 [15번 주제](../15-listener-registration/1-question.md), `cancelable`·`defaultPrevented` 는 [17번 주제](../17-stoppropagation-vs-preventdefault/1-question.md)가 정본이다. 여기는 **기본값 · 진짜 입력 · 콘솔**을 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 DOM 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★★ **이 편은 시간도 프레임도 재지 않았다** — 「성능」을 묻는 문항은 명세 설명 절과 Chromium 기록으로만 답한다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 옵션을 생략하고 일곱 대상 × 여섯 이벤트에 달면 (예측)

```js
// wa16b-19-q1.js
// 질문용 — 실행 대상 아님
// 옵션을 생략하고 달고, cancelable 인 합성 이벤트를 던져 preventDefault 가 먹히나 본다
대상.addEventListener(형, e => { e.preventDefault(); 답 = e.defaultPrevented; });
대상.dispatchEvent(new Event(형, { cancelable: true }));
// 대상: window · document · html · body · body 안의 div · 떼어 둔 div · head
// 형:   touchstart · touchmove · touchend · wheel · mousewheel · click
// 42 칸 — 어느 칸에서 답 이 false 인가?
```

- 42칸 가운데 `답` 이 `false` 인 칸을 전부 대라. 몇 칸인가?
- 그 칸들은 어떤 모양으로 모이는가?
- `head` 와 떼어 둔 `div` 는 어느 쪽인가?

### 2. 세 번째 인자만 바꾸면 (예측)

```js
// wa16b-19-q2.js
// 질문용 — 실행 대상 아님
// wheel 리스너를 window 와 body 안의 div 에 단다 — 세 번째 인자만 바꾼다
window.addEventListener('wheel', h);                         // 생략
window.addEventListener('wheel', h, false);
window.addEventListener('wheel', h, true);
window.addEventListener('wheel', h, {});
window.addEventListener('wheel', h, { capture: true });
window.addEventListener('wheel', h, { passive: undefined });
window.addEventListener('wheel', h, { once: true });
window.addEventListener('wheel', h, { passive: false });
window.addEventListener('wheel', h, { passive: true });
// 각 줄에서 preventDefault 가 먹히나? div 에서는?
```

- 아홉 줄 각각 `window` 와 `div` 에서 `preventDefault` 가 먹히나?
- 두 대상이 **같은 답**을 내는 줄은 어느 것인가?
- `false` 를 적은 줄의 `false` 는 무슨 칸으로 읽히나?

### 3. `body` 를 바꿔 끼우면 (예측)

```js
// wa16b-19-q3.js
// 질문용 — 실행 대상 아님
// ① 문서의 body 일 때 wheel 리스너(옵션 생략)를 달고 → 새 body 로 바꿔 끼워 떼어 낸 뒤 → 그 옛 body 에 던진다
// ② 떼어 둔 body 요소에 wheel 리스너(옵션 생략)를 달고 → 그것을 문서의 body 로 끼운 뒤 → 던진다
// 두 경우 각각 preventDefault 뒤 defaultPrevented 는?
```

- ①·② 각각 `defaultPrevented` 는?
- 둘이 말해 주는 「passive 가 정해지는 시점」은?

### 4. 진짜 휠 한 번 (예측)

```js
// wa16b-19-q4.js
// 질문용 — 실행 대상 아님
// body 높이 3000px · 안에 스크롤 상자 #상자 — 진짜 휠(아래로 100)을 한 번 굴린다
const 리스너 = e => { e.preventDefault(); 읽음 = [e.cancelable, e.defaultPrevented]; };
document.addEventListener('wheel', 리스너);                          // ①
document.addEventListener('wheel', 리스너, { passive: false });      // ②
window.addEventListener('wheel', 리스너);                            // ③
상자.addEventListener('wheel', 리스너);                              // ④ (상자 위에서 굴린다)
상자.addEventListener('wheel', 리스너, { passive: true });           // ⑤ (상자 위에서 굴린다)
document.addEventListener('scroll', 리스너);                         // ⑥
// 한 번에 하나씩 — 읽음 은? 문서나 상자가 움직였나?
```

- 여섯 경우 각각 리스너 안의 `cancelable` · `defaultPrevented` 와 「문서나 상자가 움직였나」를 적어라.
- ①·③ 의 `cancelable` 은 [15번 주제](../15-listener-registration/1-question.md)의 합성 이벤트와 **같은가**?
- ⑥ 은 무엇을 막을 수 있나?

### 5. 진짜 터치와 `touch-action` (예측)

```js
// wa16b-19-q5.js
// 질문용 — 실행 대상 아님
// 진짜 손가락: 대고 → 위로 100 끌고 → 뗀다
document.addEventListener('touchmove', 리스너);                          // ①
document.addEventListener('touchmove', 리스너, { passive: false });      // ②
document.addEventListener('touchstart', 리스너, { passive: false });     // ③
// ④ 리스너 없이, touch-action: none 인 상자 위에서 끈다
// 각각 cancelable · defaultPrevented · 문서가 움직였나?
```

- 네 경우 각각 `cancelable` · `defaultPrevented` · 「문서가 움직였나」를 적어라.
- ④ 에서 리스너는 몇 개 불리나? 문서는 움직이나?
- 끌기를 스크롤 대신 쓰려는 상자에 **자바스크립트 없이** 할 수 있는 일은?

### 6. 네 칸의 콘솔 (예측)

```js
// wa16b-19-q6.js
// 질문용 — 실행 대상 아님
// passive 리스너 안에서 preventDefault 를 네 번씩 부른다 — 모두 16 번
// ① document · 옵션 생략        · 진짜 휠 네 번
// ② #상자   · { passive: true } · 진짜 휠 네 번
// ③ document · 옵션 생략        · 합성 WheelEvent 네 번 (bubbles: true)
// ④ #상자   · { passive: true } · 합성 WheelEvent 네 번
// 콘솔(CDP Log 도메인)에 남는 줄은 몇 줄이고, 어느 칸이 몇 줄씩인가?
```

- 칸마다 몇 줄씩 남나? 모두 몇 줄인가?
- 출처(`source`)가 칸마다 무엇인가?
- 콘솔을 근거로 「무시된 곳이 없다」고 말할 수 있는가?

### 7. passive 리스너 안의 `cancelable` (경계)

- passive 리스너 안에서 합성 이벤트와 진짜 입력의 `cancelable` 은 각각 무엇이었나?
- 명세의 어느 절이 그 차이를 **허용**하나? 그것은 「해야 한다」인가 「할 수 있다」인가?
- 「`cancelable` 로 막을 수 있나 판정」이 입력 종류에 따라 맞고 틀리는 이유는?

### 8. 기본값을 왜 바꿨나 (왜)

- 문서 수준에 단 `wheel`·`touchmove` 리스너 하나가 **모든 스크롤**에 무엇을 요구하게 되나?
- 그런 리스너 대부분이 실제로 하는 일은?
- 그래서 **어느 자리만** 기본을 바꿨고, 되돌리려면 무엇을 적나?

### 9. 무엇을 쟀고 무엇을 안 쟀나 (경계)

- 이 편이 이 머신에서 **잰 것** 두 가지를 대라.
- **못 잰 것**은 무엇이고 왜 못 쟀나?
- 「지연이 5% 줄었다」는 문장은 **누구의** 측정인가? 이 문서에 그 수치를 어떻게 적어야 하나?

### 10. 세 층으로 가르기 (왜)

- 문서 수준 기본 passive 는 **지금** 명세 본문에 있는가? 어느 절인가?
- 그것은 **어디서 출발**했나? 이 판의 콘솔은 그것을 어떤 출처로 찍나?
- 진짜 입력에서 `cancelable` 을 `false` 로 보내는 것은 세 층 가운데 어디에 서는가?

### 11. 다른 주제와 잇기 (연결)

- [15번 주제](../15-listener-registration/1-question.md)가 「여덟 번 부른 `preventDefault` 가 두 줄로만 남았다」고 적은 것을 이 편의 문항 6으로 다시 설명하라.
- [17번 주제](../17-stoppropagation-vs-preventdefault/1-question.md)의 「막을 수 있나 / 막혔나」 두 속성이 이 편에서 어떻게 다시 쓰였나?
- `passive` 가 **동일성 키가 아니라는** 것은 어느 주제에서 쟀나? 그것이 이 편의 문항 2와 어떻게 이어지나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
