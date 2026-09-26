# web-api/09 — 요소 기하: `getBoundingClientRect`·`offset*`/`client*`/`scroll*` 과 좌표계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **절대 좌표를 외우지 마라.** 이 주제의 수치는 **창 크기에 달려 있다** — 정답 파일의 모든 출력은 `--window-size=1000,800` 에서 잰 것이다. 외울 것은 **어느 수가 변하고 어느 수가 안 변하나**다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★ **「CSS 가 상자를 어떻게 정하나」는 이 주제가 아니다.** 그것은 [CSS 15번 주제](../../languages/css/syntax/15-box-model-and-box-sizing/2-summary.md)다. 여기는 **스크립트가 그것을 어떻게 읽나**뿐이다.
> ★ 선행은 [08번 주제](../08-getcomputedstyle/2-summary.md)와 [CSS 15번 주제](../../languages/css/syntax/15-box-model-and-box-sizing/2-summary.md)다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 스크롤을 세 번 움직이면 (예측)

```html
<div id="head" style="height: 500px"></div>
<div id="scroller" style="width:300px; height:200px; overflow:auto; border:5px; padding:10px">
  <div id="inner" style="position: relative; width: 600px; height: 800px">
    <div id="t" style="position:absolute; top:250px; left:120px; width:100px; height:60px; overflow:auto">
      <div style="width: 300px; height: 300px"></div>
    </div>
  </div>
</div>
```

```js
sc.scrollTop = 100;   // 조상 스크롤러를 굴린다
scrollTo(0, 200);     // 창을 굴린다
t.scrollTop = 50;     // 자기 안쪽을 민다
```

- 세 단계마다 `t.getBoundingClientRect().top` · `t.offsetTop` · `t.scrollTop` 이 각각 어떻게 되는지 적어라.
- **어느 값이 한 번도 안 변하는가**? 왜인가?
- 마지막 단계에서 **아무 칸도 안 변하는 이유**는 무엇인가?
- `rect.top + scrollY` 는 무엇인가? `offsetTop` 인가?

### 2. 중간 요소의 `position` 만 바꾸면 (예측)

```html
<div id="a" style="margin-top:60px; padding:10px">
  <div id="b" style="margin-top:20px; padding:5px">
    <div id="c">여기</div>
  </div>
</div>
```

```js
b.style.position = 'static' | 'relative' | 'absolute' | 'fixed' | 'sticky';
c.offsetParent   //  ?
c.offsetTop      //  ?
```

- 다섯 값에 대해 두 줄을 각각 적어라.
- **다섯 중 몇 가지가 서로 다른 답을 주는가**?
- `static` 일 때 `offsetParent` 는 무엇이 되는가? 왜인가?
- 이 실험이 말하는 「`offsetTop` 을 쓰기 전에 반드시 할 일」은 무엇인가?

### 3. `offsetParent` 가 `null` 이 되는 자리 (경계)

```js
c.style.position = 'fixed';        c.offsetParent  c.offsetTop  //  ?
a.style.display = 'none';          c.offsetParent  c.offsetWidth //  ?
document.createElement('div')      .offsetParent                 //  ?
document.body.offsetParent                                       //  ?
document.documentElement.offsetParent                            //  ?
```

- 다섯 줄을 각각 적어라.
- **`offsetParent` 가 `null` 인데 `offsetTop` 에 값이 있는 줄**이 있는가? 그 값은 무엇 기준인가?
- `body` 가 `null` 이라는 사실이 **어떤 반복문을 성립시키는가**?

### 4. 세 계열이 각각 어느 칸을 재나 (예측)

```html
<div class="box">내용 200x60 · padding 10 · border 5</div>
<div id="sc" class="box" style="overflow:auto">넘치는 내용 400x300</div>
```

```js
el.offsetWidth  el.clientWidth  el.scrollWidth  el.getBoundingClientRect().width
```

- 보통 `.box` 의 네 값을 적어라.
- `#sc` 에서 **어느 값만 달라지는가**? 몇 px 달라지는가? 왜인가?
- **마진은 어느 값에 들어 있는가**?
- `scrollWidth` 와 `clientWidth` 가 같아지는 경우는 언제인가?

### 5. 같은 상자를 잰 두 수의 눈금 (경계)

```css
#frac { width: 100.6px; height: 40.4px; padding: 3.3px; border: 2.2px; margin-top: 8.6px }
```

```js
frac.offsetWidth   frac.getBoundingClientRect().width
frac.offsetTop     frac.getBoundingClientRect().top
```

- 네 값을 적어라.
- **왜 한쪽만 소수인가**? 명세가 정한 것인가?
- 두 계열을 섞어서 간격을 구하면 무엇이 생기는가?

### 6. `transform` 을 주면 (예측)

```css
#tr  { transform: scale(2) }
#rot { transform: rotate(45deg) }        /* 둘 다 .box 와 같은 치수다 */
```

```js
tr.offsetWidth    tr.getBoundingClientRect().width
rot.offsetWidth   rot.getBoundingClientRect().width
```

- 네 값을 적어라.
- **어느 계열이 변환을 반영하는가**? 왜 그쪽만인가?
- 45도 돌린 상자의 `rect.width` 는 **무엇을 잰 값**인가? 폭과 높이가 같아지는 이유는?

### 7. 상자가 하나가 아닌 것 (경계)

```js
줄을넘긴span.getClientRects().length          //  ?
줄을넘긴span.getBoundingClientRect().height   //  ?
보통div.getClientRects().length               //  ?
const r = el.getBoundingClientRect();
el.style.marginLeft = '100px';
r.left                                        //  ?
el.getBoundingClientRect().left               //  ?
```

- 다섯 줄을 각각 적어라.
- `getBoundingClientRect()` 가 조각이 여럿일 때 돌려주는 것은 무엇인가?
- **돌려받은 객체는 라이브인가 스냅숏인가**? [08번 주제](../08-getcomputedstyle/2-summary.md)의 계산값 객체와 견주면?

### 8. `display: none` 과 트리 밖 (경계)

```js
getComputedStyle(숨긴요소).width   //  08번에서 확인한 것
숨긴요소.offsetWidth                //  ?
숨긴요소.getBoundingClientRect()    //  ?
트리밖요소.offsetWidth              //  ?
```

- 네 줄을 적어라.
- [08번 주제](../08-getcomputedstyle/2-summary.md)에서 `display: none` 과 트리 밖은 **답이 갈렸다.** 여기서는 어떤가?
- 그 차이를 한 문장으로 설명하라.

### 9. 읽은 좌표를 도로 넣어 보면 (예측)

```js
const r = t.getBoundingClientRect();
document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);   //  ?
let y = 0, e = t; while (e.offsetParent) { y += e.offsetTop; e = e.offsetParent; }
document.elementFromPoint(누적x, y);                                      //  ?
// 위 두 줄을 스크롤 전과 scrollTo(0, 250) 뒤에 각각
```

- 네 경우(두 좌표 × 두 상태)의 결과를 적어라.
- **스크롤 전에 둘이 같은 답을 주는 것이 왜 위험한가**?
- 뷰포트 밖으로 나간 점을 물으면 무엇이 오는가?
- 이 창이 앞의 세 창과 **무엇이 다른가**?

### 10. 왜 창 ④ 가 이것인가 (왜)

- [08번 주제](../08-getcomputedstyle/2-summary.md)의 창 ④ 는 무엇이었나? 이 주제와 어떤 관계인가?
- 창 ① (`--dump-dom`)은 이 주제에서 무엇을 보여 주는가?
- 이 주제에서 **부적용인 창**은 무엇이고 왜인가?
- 「읽기만 하는 창」의 한계를 한 문장으로 적어라.

### 11. 좌표를 옮기려면 (연결)

- 뷰포트 좌표를 문서 좌표로 바꾸는 식을 적어라.
- 그 식이 **성립하지 않는 경우**는 언제인가?
- 「화면에 보이나」를 이 주제의 값으로 판정하면 왜 부족한가? 무엇이 정본인가?
- 이 주제의 읽기들이 [목록의 **10번 주제**](../10-layout-thrashing/)와 어떻게 이어지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
