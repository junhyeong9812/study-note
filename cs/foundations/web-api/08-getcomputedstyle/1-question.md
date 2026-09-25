# web-api/08 — `getComputedStyle`: 스크립트에서 계산값을 읽는다는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 비용을 묻는 문항에서는 **숫자를 외우지 마라.** 이 주제의 수치는 흔들린다 — **자릿수와 순위**만 답하면 된다.
> ★ `length` 의 **정확한 값도 외우지 마라.** Chrome 판과 그 문서의 커스텀 속성 수에 달린다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★ **「CSS 가 무엇을 계산하나」는 이 주제가 아니다.** 그것은 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)다. 여기는 **스크립트가 그것을 어떻게 읽나**뿐이다.
> ★ 선행은 [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)와 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 값이 온 곳이 넷일 때 (예측)

```html
<style>#sheet { font-size: 21px } #wins { color: blue !important }</style>
<div id="parent" style="color: rgb(0, 128, 0)"><span id="inherit">상속</span></div>
<div id="inline" style="color: red">인라인</div>
<div id="sheet">시트</div>
<div id="wins" style="color: red">시트가 important</div>
<div id="ua">아무도 안 건드림</div>
```

- 다섯 요소에 대해 `el.style` 과 `getComputedStyle` 두 칸을 각각 적어라.
- **어느 줄이 가장 위험한가**? 왜인가?
- 인라인에 `red` 라고 썼는데 계산값은 무슨 글자인가?
- 커스텀 속성(`--tone`)은 어느 칸에 보이는가?

### 2. 돌려받은 객체를 만져 보면 (예측)

```js
const cs = getComputedStyle(el);
cs.constructor.name           //  ?
cs.length                     //  ?   el.style.length 와 견주면?
cs.cssText                    //  ?
cs.color = 'lime'
cs.setProperty('color', 'lime')
cs.removeProperty('color')
cs.cssText = 'color: lime'
```

- 앞의 세 줄을 적어라.
- 뒤의 네 줄은 **예외인가 조용한가**? 이름은 무엇인가?
- 그것이 [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)의 `el.style` 과 어떻게 다른가?
- `cs.cssText` 가 빈 문자열인데 「값이 없다」로 읽으면 왜 틀리는가?

### 3. 읽는 문법 셋 (예측)

```js
cs.fontSize
cs['font-size']
cs.getPropertyValue('font-size')
cs.getPropertyValue('fontSize')
cs.fontsize
cs.getPropertyValue('zzz')
cs.getPropertyValue('--tone')
cs['--tone']
```

- 여덟 줄의 결과를 각각 적어라.
- **오타를 잡아 주는 창구**와 **조용히 빈 문자열을 주는 창구**를 가르라.
- 커스텀 속성은 어느 창구로만 읽히는가? 왜인가?
- `cs.length` 의 목록에 단축 이름(`margin`)이 있는가?

### 4. 상자가 없는 요소에 물으면 (경계)

```js
getComputedStyle(보이는요소).width      //  ?
getComputedStyle(display없음).width     //  ?
getComputedStyle(display없음).transform //  ?
const d = document.createElement('div');
getComputedStyle(d).width               //  ?
getComputedStyle(d).length              //  ?
el.remove();  getComputedStyle(el).color //  ?
```

- 여섯 줄의 결과를 각각 적어라.
- **`display: none` 과 「트리 밖」이 같은가**?
- `display: none` 에서 `color`·`fontSize`·`paddingTop` 은 어떤가?
- 그 차이를 한 문장으로 설명하라.

### 5. 의사 요소를 물으면 (경계)

```js
getComputedStyle(el, '::before').content
getComputedStyle(el, ':before').content
getComputedStyle(el, '::after').content
getComputedStyle(el, '::zzz').content
getComputedStyle(el, 'before').content
getComputedStyle(el, '').content
getComputedStyle(el).content
```

- 일곱 줄의 결과를 각각 적어라.
- **콜론이 없어도 되는가**?
- 모르는 이름을 주면 예외인가?
- 마지막 두 줄이 앞의 것들과 무엇이 다른가?

### 6. 라이브인가 스냅숏인가 (예측)

```js
const cs1 = getComputedStyle(a), cs2 = getComputedStyle(a);
cs1 === cs2                      //  ?
a.style === a.style              //  ?
a.style.color = 'red';   cs1.color        //  ?
a.classList.replace('narrow','wide');  cs1.width   //  ?
a.remove();   cs1.color   cs1.length      //  ?
document.body.appendChild(a);  cs1.color  //  ?
```

- 여섯 줄의 결과를 각각 적어라.
- **객체와 값 중 무엇이 라이브인가**?
- 떼었다 다시 붙이면 어떻게 되는가? 그것이 무엇을 뜻하는가?
- 값을 붙들어 두려면 무엇을 해야 하는가?

### 7. 계산값과 실제 상자 (경계)

```js
// .box { width: 200px; height: 40px; padding: 10px; border: 5px solid black }
#cb { box-sizing: content-box }   #bb { box-sizing: border-box }
#sc { transform: scale(2) }       #gone { display: none }
```

- 네 요소의 `getComputedStyle().width` 와 `getBoundingClientRect().width` 를 나란히 적어라.
- `cs.width` 가 넷 다 같은가? 상자는?
- `transform` 은 계산값에 섞이는가?
- 그래서 「보이나」를 계산값으로 판정하면 왜 틀리는가?

### 8. 계산값이 그대로인데 결과만 갈리는 자리 (경계)

```js
// #bar { display: flex; width: 200px }  #bar > div { flex: 1 1 0 }
// #long 에 긴 라틴 낱말 하나
long.style.overflow = 'hidden';
long.style.overflow = '';  long.style.minWidth = '0';
```

- 세 단계의 `cs.minWidth` 와 두 항목의 `rect.width` 를 적어라.
- **계산값이 바뀌지 않는 단계**가 있는가? 몇 번째인가?
- 같은 결과에 이르는 두 길 중 **왜 한쪽만 계산값에 흔적이 남는가**?
- 이 주제의 **창 ④** 를 `getBoundingClientRect` 로 정한 이유가 이것인가?

### 9. 얼마나 비싼가 (예측)

```js
// 400행 · 9판 중앙값
for (const d of rows) { d.style.paddingLeft = '1px'; sink += getComputedStyle(d).width; }
for (const d of rows) d.style.paddingLeft = '1px';
for (const d of rows) sink += getComputedStyle(d).width;
```

- 위 세 방식의 **자릿수 순위**를 매겨라.
- 비싼 것은 **읽기인가 쓰기인가 섞는 것인가**?
- 같은 쓰기 뒤에 `cs.color` 를 읽는 것과 `cs.width` 를 읽는 것의 순위는?
- 표에 `0.00` 이 보이면 무엇이라고 읽어야 하는가?

### 10. 왜 창 ④ 가 필요한가 (왜)

- CSS 갈래에서 `getComputedStyle` 은 진단 3창의 **몇째 창**이었나? 그 창은 무엇을 묻는가?
- 이 주제에서 그 창을 그대로 쓸 수 없는 이유는 무엇인가?
- 창 ① (`--dump-dom`)은 이 주제에서 무엇을 보여 주는가?
- 「계산값은 무엇이 선언됐나를 말하지 무엇이 일어나나를 말하지 않는다」를 실측 하나로 뒷받침하라.

### 11. 다른 주제와 잇기 (연결)

- [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)가 이 주제에 넘긴 질문을 한 문장으로 적어라.
- [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)와 이 주제의 **경계선**을 한 문장으로 그어라.
- 목록의 **10번 주제**(레이아웃 스래싱)가 이 주제의 어느 절에서 미리 드러났는가?
- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에서 물려받은 **측정 도구의 한계**는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
