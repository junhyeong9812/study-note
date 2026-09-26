# web-api/11 — 스크롤 제어: `scrollTo`/`scrollBy`/`scrollIntoView`·스크롤 컨테이너 찾기·위치 복원 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **절대 좌표를 외우지 마라.** 스크롤 상한은 **뷰포트 높이에 달려 있다** — 정답 파일의 출력은 전부 `--window-size=1000,800` 에서 잰 것이다. 외울 것은 **누가 굴러가나**와 **무엇이 조용히 실패하나**다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★ **「무엇이 스크롤 컨테이너가 되나」는 이 주제가 아니다.** 그것은 [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)다. 여기는 **스크립트가 그것을 어떻게 찾아 굴리나**뿐이다.
> ★ 선행은 [09번 주제](../09-element-geometry/2-summary.md)(`scrollTop` 을 **읽는** 쪽)와 [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 문서를 굴리는 것은 누구인가 (예측)

```js
// 표준 모드 (<!doctype html> 있음)
scrollTo(0, 300);
document.documentElement.scrollTop   //  ?
document.body.scrollTop              //  ?
document.body.scrollTop = 700;  scrollY   //  ?
document.scrollingElement                 //  ?
document.compatMode                       //  ?
```

- 다섯 줄을 적어라.
- **doctype 을 지우면** 같은 코드가 어떻게 달라지는가?
- 어느 읽기가 **두 모드에서 똑같이 동작하는가**?
- 옛 코드에 `document.body.scrollTop || document.documentElement.scrollTop` 이 있는 이유는?

### 2. 같은 일을 시키는 네 표면 (예측)

```js
sc.scrollTop = 120;
sc.scrollTo(30, 60);
sc.scrollTo({ top: 200 });
sc.scrollBy(10, 25);
sc.scrollBy({ top: -25 });
```

- 다섯 줄 뒤의 `sc.scrollTop` 과 `sc.scrollLeft` 를 각각 추적해 적어라.
- **두 인자 꼴과 객체 꼴의 축 순서**가 어떻게 다른가?
- `scrollTo({top: 200})` 뒤에 `scrollLeft` 는 어떻게 되는가? 왜인가?

### 3. 범위 밖 값을 넣으면 (예측)

```js
sc.scrollTop = -50;       //  ?
sc.scrollTop = 999999;    //  ?
sc.scrollTop = 'abc';     //  ?
sc.scrollTop = 100.4;     //  ?
안굴러가는요소.scrollTop = 100;   //  ?
```

- 다섯 줄의 되읽은 값을 적어라.
- **예외가 나는 줄이 있는가**?
- 상한은 무엇으로 정해지는가?
- 마지막 줄의 실패를 **어떻게 진단하는가**?

### 4. `scrollIntoView` 가 무엇을 움직이나 (예측)

```html
<div id="outer" style="overflow:auto">
  <div id="mid" style="padding:10px">            <!-- overflow: visible -->
    <div id="inner" style="overflow:auto"> … <div id="t">목표</div> … </div>
  </div>
</div>
```

```js
t.scrollIntoView();
scrollY  outer.scrollTop  inner.scrollTop  mid.scrollTop   //  ?
```

- 네 값 가운데 **몇 개가 움직이는가**?
- 안 움직이는 것은 무엇이고 왜인가?
- 한 요소만 보고 판정하면 **무엇을 놓치는가**?

### 5. 옵션이 정하는 것 (예측)

```js
t.scrollIntoView();                      t.scrollIntoView(true);
t.scrollIntoView(false);                 t.scrollIntoView({ block: 'start' });
t.scrollIntoView({ block: 'center' });   t.scrollIntoView({ block: 'end' });
t.scrollIntoView({ block: 'nearest' });
```

- 일곱 줄을 **같은 결과끼리 묶어라.**
- 불리언 인자는 어느 옵션과 같은가?
- **`nearest` 와 `end` 가 같은 결과를 주는 경우**는 언제인가? 언제 갈리는가?

### 6. 어떤 `overflow` 가 굴러가나 (경계)

```js
for (const v of ['visible', 'hidden', 'clip', 'auto', 'scroll']) {
  inner.style.overflow = v;  t.scrollIntoView();
  // inner.scrollTop · outer.scrollTop
}
```

- 다섯 값에서 `inner` 가 굴러가는지 적어라.
- **화면이 같은데 갈리는 짝**은 무엇인가?
- `inner` 가 안 굴러갈 때 **그 몫은 어디로 가는가**?

### 7. 스크롤 컨테이너를 스크립트로 찾기 (왜)

```js
const oy = getComputedStyle(e).overflowY;
(oy === 'auto' || oy === 'scroll' || oy === 'hidden') && e.scrollHeight > e.clientHeight
```

- 이 규칙에 **조건이 둘인 이유**를 적어라.
- 이 규칙으로 조상 사슬을 훑으면 **놓치는 것**이 있는가?
- `<html>` 의 `overflowY` 계산값은 무엇인가? 그런데 문서는 굴러가는가?
- 사슬의 마지막 칸을 무엇으로 메우는가?

### 8. `behavior: 'smooth'` (예측)

```js
sc.scrollTo({ top: 500, behavior: 'auto' });    sc.scrollTop   //  ?
sc.scrollTo({ top: 500 });                      sc.scrollTop   //  ?
sc.scrollTo({ top: 500, behavior: 'smooth' });  sc.scrollTop   //  ?
// #css { scroll-behavior: smooth } 인 상자에서
css.scrollTop = 500;                            css.scrollTop  //  ?
css.scrollTo({ top: 500, behavior: 'instant' }); css.scrollTop //  ?
```

- 다섯 줄을 적어라.
- **CSS 한 줄이 스크립트의 무엇을 바꾸는가**?
- `instant` 는 무엇을 하는가?
- 도착을 기다리려면 무엇이 필요한가?

### 9. 도착은 관측됐는가 (경계)

```js
sc.scrollTo({ top: 500, behavior: 'smooth' });
// 부른 직후 · 동기 루프 200ms 뒤 · setTimeout 0 뒤 · 한 겹 더 뒤
```

- 네 지점의 `scrollTop` 을 적어라.
- **동기 루프로 기다리면 왜 안 되는가**?
- 이 도구가 기다리는 끝은 어디까지인가?
- 그래서 이 항목은 **「안 돌려 본 것」인가 「못 잰 것」인가**?

### 10. 위치 복원 (경계)

```js
history.scrollRestoration            //  ?
history.scrollRestoration = 'manual';    //  ?
history.scrollRestoration = 'zzz';       //  예외인가? 되읽으면?
```

- 세 줄을 적어라.
- 이 속성이 **하는 일**을 한 문장으로 적어라. 복원 기능인가?
- 뒤로 가기에서 위치가 **튀는 진짜 원인**은 무엇인가?
- 이 문서가 그 순간을 관측했는가?

### 11. 다른 주제와 잇기 (연결)

- [09번 주제](../09-element-geometry/2-summary.md)와 이 주제의 경계선을 한 문장으로 그어라.
- 스크롤 핸들러 안에서 좌표를 읽으면 어느 주제가 시작되는가?
- 이 주제의 쓰기 가운데 **예외를 던지는 것**이 하나라도 있는가? 그 사실이 뜻하는 것은?
- 「보이나」를 스크롤 위치로 판정하지 않는 법은 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
