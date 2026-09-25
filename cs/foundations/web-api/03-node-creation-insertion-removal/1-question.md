# web-api/03 — 노드 생성·삽입·이동·제거: `createElement`·`append` 계열·`remove` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 답할 때는 「어디에 붙었나」만 말하지 말고 **「어디서 빠졌나」까지** 말한다. 이 주제의 절반이 그쪽에 있다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이미 트리에 있는 노드를 다른 곳에 넣으면 (예측)

```html
<div id="left"><span id="s1">옮길 것</span><span id="s2">남을 것</span></div>
<div id="right"><b id="b1">이미 있던 것</b></div>
```

```js
right.appendChild(s1);
```

- 이 한 줄 뒤 `left` 와 `right` 의 자식을 각각 적어라.
- 문서 안 `<span>` 의 개수는 몇으로 바뀌는가?
- `s1.parentElement.id` 는 전후로 무엇인가?
- 이것이 명세의 어느 단계 때문인가?

### 2. 두 메서드가 받는 것과 돌려주는 것 (예측)

```js
const r1 = box.appendChild(el);
const r2 = box.append(el2);
box.append('문자 1 ', document.createElement('i'), ' 문자 2');
box.appendChild('그냥 문자열');
```

- `r1` 과 `r2` 는 각각 무엇인가?
- 세 번째 줄 뒤 `box.childNodes.length` 와 `box.children.length` 는 각각 몇인가?
- 네 번째 줄은 무엇을 하는가?
- `box.append(el).classList.add('x')` 가 죽는 이유는 무엇인가?

### 3. 조각을 붙이고 나면 (예측)

```js
const frag = document.createDocumentFragment();
for (const name of ['가', '나', '다']) frag.appendChild(만든li(name));
list.appendChild(frag);
list.appendChild(frag);          // 한 번 더
```

- 첫 번째 `appendChild` 전후로 `frag.childNodes.length` 는 각각 몇인가?
- 그 뒤 `list.children.length` 는 몇인가?
- `list.querySelector('ul')` 로 조각 자신을 찾을 수 있는가?
- 네 번째 줄은 무슨 일을 하는가?

### 4. 다섯 메서드가 만드는 자리 (예측)

```js
box.prepend(p1);
b1.before(x1);
b1.after(x2);
b2.replaceWith(r1);
x1.remove();
```

- `<div id="box"><b id="b1">B1</b><b id="b2">B2</b></div>` 에서 시작해 한 줄씩 결과를 적어라.
- 부모에 대고 부르는 것과 자기 자신에 대고 부르는 것을 갈라라.
- `removeChild` 와 `remove()` 의 반환값은 각각 무엇인가?
- 다섯 중 문자열을 받는 것은 무엇인가?

### 5. 복제본이 물려받는 것 (예측)

```js
const deep = orig.cloneNode(true);       // <div id="orig" class="card" data-k="v"><b>깊은 것</b></div>
const shallow = orig.cloneNode(false);
const btnClone = btn.cloneNode(true);    // btn 에는 addEventListener 와 onclick 속성이 둘 다 있다
btnClone.click();
```

- `deep` 과 `shallow` 의 `childNodes.length` 는 각각 몇인가?
- `deep.id` 는 무엇이고 그것을 그대로 문서에 넣으면 무슨 일이 생기는가?
- `btnClone.click()` 에서 두 핸들러 중 **무엇이 불리고 무엇이 안 불리는가**?
- 그 차이를 한 문장으로 설명하라.

### 6. 만들기와 넣기는 다른 단계다 (경계)

- `createElement` 로 만든 직후의 `parentNode`·`isConnected`·`ownerDocument` 는 각각 무엇인가?
- 넣기 전까지 일어나지 **않는** 것은 무엇인가?
- `createTextNode('<b>x</b>')` 를 넣으면 화면에 무엇이 보이는가?
- 노드를 트리 밖에서 조립하는 것이 권장되는 이유는 무엇인가?

### 7. 왜 복사가 아니라 이동인가 (왜)

- DOM 나무의 어떤 성질이 「삽입은 이동」을 강제하는가?
- 이동일 때 따라가는 것(리스너·폼 입력값)과 복제일 때 안 따라가는 것을 대비하라.
- 이동이 값싸다는 일반 규칙의 **예외**가 실측에서 하나 나왔다. 무엇이고 무엇이 사라졌는가?
- 그 예외에서 이 문서가 **확인하지 못한 것**은 무엇인가?

### 8. 뗀 노드는 어디로 가나 (경계)

- `remove()` 한 노드를 `document.getElementById` 로 찾으면 무엇이 나오는가?
- 그 노드 자체는 살아 있는가? 무엇으로 확인하는가?
- 다시 넣을 수 있는가?
- 이것이 메모리 문제가 되는 경로는 무엇인가?

### 9. 삽입이 검사하지 않는 것 (경계)

- `p.appendChild(document.createElement('div'))` 의 결과 `outerHTML` 은 무엇인가?
- 같은 모양을 `innerHTML` 로 넣으면 결과가 어떻게 다른가?
- 두 결과가 다른 이유는 무엇이고, 각각 어느 규칙이 정본인가?
- 삽입 알고리즘이 **실제로 검사하는 것**은 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- 여기서 노드를 옮기면 [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 라이브 컬렉션과 정적 스냅샷은 각각 어떻게 되는가?
- 옛 3형제(`appendChild`·`insertBefore`·`removeChild`)와 새 메서드들의 **반환값 규약이 갈린** 이유는 무엇인가?
- `replaceChildren()` 이 `innerHTML = ''` 보다 권장되는 이유는 무엇인가?
- 「한 번에 넣는 것이 싸다」를 이 주제가 **주장하지 않은** 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
