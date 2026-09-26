# web-api/07 — `dataset`·`classList`·인라인 `style`: 스크립트가 만지는 세 표면 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이 주제에는 흔들리는 칸이 없다.** 수치를 재지 않으므로 **답은 전부 한 글자까지 고정**이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★ 선행은 [06번 주제](../06-attribute-vs-property/2-summary.md)다. 「`data-*` 와 `class` 는 반영이 아니다」까지는 안다고 본다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 마크업에서 `dataset` 으로 (예측)

```html
<div id="m" data-foo-bar="케밥" data-fooBar="소스에 대문자" data-x="짧은 것"
     data-="이름이 빈 것" data-1-2="숫자"></div>
```

```js
Object.keys(m.dataset)
m.dataset.fooBar
m.dataset.foobar
m.dataset['1-2']   m.dataset['12']
```

- 키 목록에 **몇 개**가 들어오는가? 각각 무엇인가?
- `data-fooBar` 라고 쓴 것은 어느 키가 되는가? **왜 그런가**?
- `data-1-2` 가 `dataset['12']` 가 **아닌** 이유는 무엇인가?
- `m.dataset === m.dataset` 은 무엇인가?

### 2. `dataset` 에 쓰면 무엇이 생기나 (예측)

```js
w.dataset.foo    = 'a';
w.dataset.fooBar = 'b';
w.dataset.fooBAR = 'c';
w.dataset.a1B2   = 'd';
w.dataset['foo-bar'] = 'e';
w.dataset['foo-Bar'] = 'f';
w.dataset['']    = 'g';
```

- 일곱 줄이 각각 **어떤 속성 이름**을 만드는가?
- **예외가 나는 줄**이 있는가? 무엇이고 왜인가?
- 셋째 줄이 둘째 줄과 갈리는 규칙을 한 문장으로 적어라.
- 여섯째 줄이 다섯째 줄과 달리 **안 던지는** 것이 왜 더 나쁜가?

### 3. `classList` 다섯 메서드 (예측)

```js
cl.add('c')          cl.add('a')       cl.add('d','e')
cl.remove('zz')      cl.remove('d','e')
cl.toggle('a')       cl.toggle('a', true)   cl.toggle('a', false)
cl.replace('b','q')  cl.replace('nope','r')
cl.contains('q')
```

- **무엇이 값을 돌려주고 무엇이 `undefined` 인가**?
- `toggle` 의 **두 번째 인자**는 무엇을 바꾸는가? 반환값은?
- `toggle('a', true)` 를 두 번 부르면 어떻게 되는가?
- `replace('nope','r')` 는 `r` 을 새로 넣는가?

### 4. 클래스 이름이 이상하면 (경계)

```js
cl.add('두 칸')
cl.add('')
cl.value = 'x  y'
c.className = '가 나 가'
cl.supports('가')
```

- 다섯 줄을 **담김 / 조용히 버려짐 / 예외** 셋으로 가르라.
- 예외가 나는 줄의 **이름**을 각각 적어라.
- 셋째·넷째 줄이 첫째·둘째 줄과 갈리는 이유는 무엇인가?
- 다섯째 줄은 왜 그런가? 어디서는 동작하는가?

### 5. `class` 속성의 공백 (경계)

```html
<div id="s" class="  두   칸   띄움  "></div>
```

```js
s.getAttribute('class')
s.classList.length   [...s.classList]
s.classList.value
s.classList.add('끝');   s.getAttribute('class')
```

- 네 줄의 결과를 각각 적어라.
- 어느 시점에 속성 문자열이 **바뀌는가**?
- 「아무 일도 안 시켰는데 문자열이 바뀐다」가 성립하는가?
- 그것이 위험해지는 경우를 하나 들어라.

### 6. 인라인 `style` 은 무엇과 같은 것인가 (예측)

```html
<div id="s" style="color: red; padding-left: 4px">인라인</div>
<div id="n">style 속성이 없다</div>
```

```js
s.getAttribute('style')      s.style.cssText
s.getAttribute('style') === s.style.cssText
s.style.length   s.style.item(0)
n.getAttribute('style')      n.style.cssText
n.style.color = 'teal';      n.getAttribute('style')
```

- 처음 두 줄이 **한 글자도 같은가**? 아니라면 무엇이 다른가?
- `style` 속성이 없는 요소의 `el.style` 은 무엇인가?
- 한 줄을 쓴 뒤에는 둘이 같아지는가?
- `s.style === s.style` 은 무엇인가?

### 7. 쓴 것이 어디로 갔나 (예측)

```js
t.style.color  = 'blue';
t.style.color  = 'bogus';
t.style.width  = '10';
t.style.colour = 'red';
t.style['--x'] = '9';
t.style.cssText = 'color:green;bogus:1;width:z';
```

- 여섯 줄을 **담김 / 조용히 버려짐 / 예외** 셋으로 가르라.
- **예외가 몇 줄인가**?
- 마지막 줄 뒤 `getAttribute('style')` 은 무엇인가?
- 커스텀 속성을 제대로 쓰려면 무엇을 써야 하는가?

### 8. 한 줄 쓰면 목록은 몇 줄이 되나 (경계)

```js
u.style.color = 'red';        // length ?
u.style.margin = '1px 2px';   // length ?
u.style.marginTop = '9px';    // length ?
u.style.margin = '';          // length ?
u.style.background = 'blue';  // length ?
u.getAttribute('style')
```

- 다섯 단계의 `length` 를 각각 적어라.
- 담기는 것과 직렬화되는 것이 **같은 모양인가**?
- 낱개 하나만 고치려고 단축을 쓰면 무엇이 깨지는가?
- 그 개수는 **흔들리는 칸인가**?

### 9. `el.style` 이 못 보는 것 (경계)

```html
<style>#sheet { color: rgb(0, 128, 0); font-size: 21px }</style>
<div id="sheet">스타일시트가 칠한 것</div>
```

```js
sh.getAttribute('style')   sh.style.color   sh.style.length
getComputedStyle(sh).color
```

- 네 줄의 결과를 각각 적어라.
- 화면은 초록인데 `el.style.length` 가 그 값인 이유는 무엇인가?
- 인라인이 있는 요소에서도 두 창구의 **값의 모양**이 다른가?
- 「지금 무슨 값인가」를 묻는 창구는 어느 주제인가?

### 10. 세 표면의 실패 방식 (왜)

- 셋 중 **예외를 던지는 자리**가 있는 표면과 없는 표면을 가르라.
- `el.style` 이 거의 전부 조용한 이유를 **CSS 의 설계**로 설명하라.
- 그래서 이 주제가 세운 **창 ④** 는 무엇을 하는 창인가?
- 창 1\~3 으로는 왜 「조용히 버려짐」이 안 잡히는가?

### 11. 다른 주제와 잇기 (연결)

- [06번 주제](../06-attribute-vs-property/2-summary.md)가 이 주제에 **넘긴 셋**은 각각 무엇인가?
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 「라이브」가 이 주제의 어느 객체에 걸리는가?
- [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)의 진단 3창 중 **어느 창**이 이 주제의 창 ④ 와 같은 일을 하는가?
- [08번 주제](../08-getcomputedstyle/2-summary.md)가 이 주제에서 넘겨받는 질문을 한 문장으로 적어라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
