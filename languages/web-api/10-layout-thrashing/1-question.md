# web-api/10 — 레이아웃 스래싱: 읽기·쓰기 교차로 나는 강제 동기 레이아웃 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★ **숫자를 외우지 마라.** 이 주제의 수치는 판마다 흔들린다 — 외울 것은 **자릿수와 순위**, 그리고 **무엇이 방아쇠인가**다.
> ★★★ **이 주제는 명세가 보장하지 않는 것이 본체다.** 「언제 레이아웃이 도는가」를 정한 문장은 없다. 그 사실을 답에 반드시 넣어라.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★ 선행은 [08번 주제](../08-getcomputedstyle/2-summary.md)(계산값 읽기)와 [09번 주제](../09-element-geometry/2-summary.md)(기하 읽기)다. **둘이 방아쇠 목록의 절반이다.**

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 순서만 바꾸면 (예측)

```js
// 400행 · 9판 중앙값. ①과 ②는 쓰기 횟수도 읽기 횟수도 같다.
① for (const d of rows) { d.style.paddingLeft = n + 'px'; sink += d.offsetWidth; }
② for (const d of rows) d.style.paddingLeft = n + 'px';
   for (const d of rows) sink += d.offsetWidth;
③ for (const d of rows) sink += d.offsetWidth;            // 읽기만
④ for (const d of rows) d.style.paddingLeft = n + 'px';   // 쓰기만
```

- 네 조건의 **자릿수 순위**를 매겨라.
- ② 는 ③ 과 ④ 의 합과 견주면 어떤가?
- **비싼 것은 읽기인가 쓰기인가 섞는 것인가**?
- ③ 과 ④ 의 수를 근거로 순위를 주장해도 되는가?

### 2. 읽기를 먼저 하면 (예측)

```js
⑤ for (const d of rows) sink += d.offsetWidth;
   for (const d of rows) d.style.paddingLeft = n + 'px';
⑥ 앞쪽 200행은 교차, 뒤쪽 200행은 묶음
```

- 두 조건이 ①·② 중 어느 쪽에 가까운지 적어라.
- ⑥ 의 결과가 말하는 것은 **임계점인가 비례인가**?
- 그래서 고치는 처방을 한 줄로 쓰면?

### 3. 분해능을 넘기려면 몇 번 (경계)

```js
// n 을 1 → 5 → 10 → 50 → 100 → 200 → 400 으로 키우며 교차·분리를 잰다
```

- `performance.now()` 의 **관측된 최소 양수 증분**은 얼마인가?
- 표에서 `0.10` 을 어떻게 읽어야 하는가?
- **분자가 자 위로 올라오면 충분한가**? 아니라면 무엇이 더 필요한가?
- 본문이 `n = 400` 을 고른 이유를 한 줄로 적어라.

### 4. 무엇이 「읽기」인가 (예측)

```js
el.offsetTop           el.getBoundingClientRect()     el.scrollTop
window.scrollY         document.elementFromPoint(5,5) el.innerText
el.textContent         el.className                   el.getAttribute('class')
el.matches('.r')       el.closest('#host')            document.querySelector('.r')
getComputedStyle(el)   getComputedStyle(el).width     getComputedStyle(el).color
el.checkVisibility()   el.style.paddingLeft           el.children.length
```

- 위를 **세 칸**(레이아웃까지 / 스타일 재계산까지 / 아무것도 안 돌림)으로 갈라라.
- **이름이 닮았는데 갈리는 짝**을 둘 이상 찾아라.
- 가장 비싼 것은 무엇이고 왜인가?
- 요소를 안 건드리는데도 방아쇠인 것이 있는가?

### 5. 무엇을 쓰느냐 (예측)

```js
// 읽는 것은 전부 one.offsetTop 하나로 고정
host.style.paddingLeft = …;   host.style.color = …;   one.style.color = …;
host.style.transform = …;     host.style.opacity = …;
```

- 다섯 조건의 **자릿수 순위**를 매겨라.
- **가장 비싼 것이 무엇인가**? 예상과 맞았는가?
- `host` 와 `one` 에 같은 속성을 썼는데 갈리는 이유는?
- 그래서 「읽기·쓰기를 섞지 마라」가 왜 반쪽짜리 처방인가?

### 6. 남의 요소를 읽으면 (예측)

```js
host.style.paddingLeft = …;  sink += one.offsetTop;                  // 같은 가지
host.style.paddingLeft = …;  sink += far.offsetTop;                  // 다른 가지
host.style.paddingLeft = …;  sink += document.body.offsetHeight;     // 문서 전체
```

- 세 줄의 결과를 견주어라.
- 이 결과가 「컴포넌트를 나눴으니 괜찮다」에 대해 말하는 것은?
- 왜 진단이 어려워지는가?

### 7. 창 ④ — 시간을 안 재고 보는 법 (왜)

```js
const 전 = t.offsetLeft;
host.style.paddingLeft = '50px';
const 후 = t.offsetLeft;        // 같은 tick 이다
```

- `전` 과 `후` 가 다른가? 그것이 무엇을 증명하는가?
- **왜 이 창이 시간 측정보다 원인에 가까운가**?
- `t.textContent` 와 `t.style.width` 는 이 창에서 어떻게 나오는가? 둘의 「바뀌었다」가 같은 뜻인가?
- 이 창만으로 방아쇠 목록을 만들 수 없는 이유는?

### 8. 쓰기는 어디에 쌓이나 (경계)

```js
host.style.paddingLeft = '10px';
host.style.paddingLeft = '20px';
host.style.paddingLeft = '30px';
t.offsetLeft                      //  ?
// 견주어 — 쓰기 사이마다 읽으면 무엇이 관측되나?
```

- 두 경우의 결과를 적어라.
- 중간 값 10 과 20 을 관측할 방법이 있는가?
- 「관측 가능하다는 것이 곧 비용이다」를 이 실험으로 설명하라.

### 9. 명세는 무엇을 보장하나 (왜)

- CSSOM View 가 `offsetTop` 에 대해 **요구하는 것**은 무엇인가?
- **「언제 레이아웃이 도는가」를 정한 명세 문장이 있는가**?
- 그래서 이 주제의 결론은 어떤 성격의 지식인가?
- 「`transform` 은 레이아웃을 안 더럽힌다」는 명세인가 구현인가?

### 10. 태스크와 프레임 (경계)

```js
// 쓰기는 이 tick, 읽기는 setTimeout(…, 0) 안에서
// 그리고 requestAnimationFrame 으로 나누면?
```

- 태스크를 가른 조건의 비용은 ①·② 중 어느 쪽인가? 왜인가?
- 태스크를 갈라서 **얻는 것**은 정확히 무엇인가?
- `requestAnimationFrame` 쪽은 이 도구로 관측됐는가? **안 됐다면 그것을 뭐라고 적어야 하는가**?
- `--dump-dom` 이 기다리는 끝은 어디까지인가?

### 11. 다른 주제와 잇기 (연결)

- [08번 주제](../08-getcomputedstyle/2-summary.md)의 어느 절이 이 주제의 씨앗이었는가?
- [09번 주제](../09-element-geometry/2-summary.md)의 표면 가운데 방아쇠가 아닌 것이 있는가?
- 이 주제의 실패를 **단위 테스트로 잡을 수 있는가**? 왜인가?
- 「`rect` 를 읽지 않고 보이는지 알기」는 어느 주제가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
