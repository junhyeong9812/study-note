# web-api/12 — Shadow DOM: `attachShadow`·캡슐화 경계·슬롯 할당·`::part` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **마크업 갈래와의 경계** — HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **10번** 은 `template`·`slot`·선언적 Shadow DOM 을 **마크업으로** 다루고, 여기는 **그것을 만들고 들여다보는 API** 다.
> ★ 이 파일의 코드 블록은 **질문용 스텁**이다 — 실행 대상이 아니며, 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★ 선행은 [01번 주제](../01-document-and-node-tree/2-summary.md)(노드 트리)와 [05번 주제](../05-documentfragment-and-template/2-summary.md)(`<template>`)다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 트리를 글자로 뽑으면 (예측)

```html
<!-- wa12b-12-q1a.html -->
<div id="열림"></div>
<div id="닫힘"></div>
<div id="선언"><template shadowrootmode="open"><b>선언적</b></template><span>라이트 자식</span></div>
<script>
  열림.attachShadow({mode: 'open'}).innerHTML = '<b>스크립트로 만든 것</b>';
  닫힘.attachShadow({mode: 'closed'}).innerHTML = '<b>닫힌 것</b>';
</script>
```

- `--dump-dom` 의 `<body>` 줄에 **무엇이 찍히는가**? 세 상자 각각.
- `#선언` 안의 `<template>` 은 어떻게 되는가?
- 그래서 이 주제에서 **창 ① 은 무엇인가**?
- 「트리를 봤는데 없더라」를 근거로 써도 되는가?

### 2. 경계를 넘겨 꺼내려면 (예측)

```js
// wa12b-12-q2a.js
열림.shadowRoot.innerHTML                              //  ?
닫힘.shadowRoot                                        //  ?
열림.getHTML()                                         //  ?
열림.getHTML({ serializableShadowRoots: true })        //  ?
열림.getHTML({ shadowRoots: [열림.shadowRoot] })       //  ?
열림.shadowRoot.serializable                           //  ?
```

- 여섯 줄을 적어라.
- **넷째 줄이 비는 이유**는 무엇인가? 어떻게 하면 나오는가?
- 꺼낸 문자열의 **모양**은 무엇인가? 그것이 뜻하는 것은?

### 3. `open` 과 `closed` (예측)

```js
// wa12b-12-q3a.js
host.shadowRoot        root.mode        root.host
root.querySelector('b')
document.querySelector('#안쪽b')
// closed 로 만든 뒤 attachShadow 의 반환값으로 안을 고쳐 쓰면?
// 안쪽 요소의 getRootNode().host 는?
```

- 두 모드에서 각각 적어라.
- **갈리는 줄이 몇 개인가**?
- **`closed` 가 보안 장치인가**? 근거 둘을 대라.

### 4. `attachShadow` 가 거절하는 자리 (경계)

```js
// wa12b-12-q4a.js
host.attachShadow({ mode: 'open' });   // 이미 붙어 있는 호스트에 또
document.createElement('div').attachShadow({});
document.createElement('div').attachShadow();
for (const t of ['div','span','p','h1','section','my-el','input','br','table','button','img'])
  document.createElement(t).attachShadow({ mode: 'open' });
```

- 앞의 세 줄이 **예외인가 조용한가**? 이름은?
- 마지막 줄에서 **되는 것과 안 되는 것**을 갈라라.
- 이 주제에서 **조용하지 않은 유일한 자리**가 여기인 이유는?

### 5. 안팎이 서로 찾으면 (예측)

```js
// wa12b-12-q5a.js
document.querySelector('#안문단')       document.getElementById('안문단')
document.querySelectorAll('.표적').length   // 같은 class 가 안·밖·슬롯자식에 하나씩
root.querySelector('#안문단')           root.querySelector('#바깥문단')
안.closest('body')                      안.closest('#host')
```

- 일곱 줄을 적어라.
- **경계가 한 방향인가 양방향인가**?
- `closest('#host')` 가 `null` 인 이유는?
- 그림자마다 같은 `id` 를 써도 되는 이유가 여기서 나오는가?

### 6. 경계를 건너는 길 (경계)

```js
// wa12b-12-q6a.js
안.getRootNode()                  안.getRootNode().host
안.getRootNode({ composed: true }) 안.ownerDocument   안.isConnected
root.parentNode    host.childNodes.length   host.firstElementChild
```

- 여덟 줄을 적어라.
- **트리는 둘인데 문서는 몇 개인가**?
- `root.parentNode` 가 `null` 인 것이 무엇을 뜻하는가?
- 「막힌다」는 무엇에 대한 이야기인가 — 선택자인가 참조인가?

### 7. 스타일이 새나 (예측)

```css
/* wa12b-12-q7a.css */
body { color: rgb(0,100,0); font-size: 21px }
p { color: rgb(200,0,0) }
.테두리 { border: 3px solid blue }
```

```js
// wa12b-12-q7b.js
// 그림자 안에 <p class="테두리">, <i>, 그리고 슬롯에 배정된 <b class="테두리">
getComputedStyle(안쪽p).color · .borderTopWidth · .fontSize
getComputedStyle(슬롯자식).color · .borderTopWidth
```

- 다섯 값을 적어라.
- **무엇이 막히고 무엇이 넘어오는가**? 둘은 같은 길인가?
- 슬롯에 배정된 자식이 바깥 규칙을 받는 이유는?
- 안쪽 시트의 규칙이 바깥 문단을 건드리는가?

### 8. `::part` (경계)

```css
/* wa12b-12-q8a.css */
#host::part(핵심)   { color: magenta }
#host::part(없는이름) { color: rgb(1,2,3) }
```

```js
// wa12b-12-q8b.js
getComputedStyle(part를단요소).color      //  ?
getComputedStyle(part없는요소).color      //  ?
document.styleSheets[0].cssRules          //  ::part 규칙이 담겨 있는가?
```

- 세 줄을 적어라.
- `part` 이름이 틀리면 **예외인가 조용한가**?
- 규칙이 「담겼는데 아무것도 안 잡는」 상태가 될 수 있는가?

### 9. 슬롯 할당 (경계)

```html
<!-- wa12b-12-q9a.html -->
<div id="host">
  <span slot="머리" id="머리자식">…</span>
  <b id="익명">…</b>
  <span slot="없는칸" id="미아">…</span>
</div>
<!-- 그림자: <slot name="머리"></slot><slot><i>기본 내용</i></slot> -->
```

```js
// wa12b-12-q9b.js
머리슬롯.assignedNodes()   기본슬롯.assignedNodes()   기본슬롯.assignedElements()
머리자식.assignedSlot.name   익명.assignedSlot.name   미아.assignedSlot
미아.getBoundingClientRect().width
```

- 일곱 줄을 적어라.
- **`assignedNodes` 와 `assignedElements` 의 길이가 왜 다른가**?
- `slot="없는칸"` 오타는 어떻게 드러나는가?

### 10. 배정과 기본 내용 (경계)

```js
// wa12b-12-q10a.js
익명.parentElement   익명.getRootNode()   host.children.length   root.children.length
// 배정된 요소를 전부 떼면 기본 내용이 나오는가?
```

- 네 줄을 적어라.
- **배정이 이동인가 투영인가**? 근거는?
- 요소를 다 뗐는데 기본 내용이 안 나온다면 원인은 무엇인가?
- 그 원인을 어떻게 진단하는가?

### 11. 왜 창 ④ 가 필요한가 (왜)

- 이 주제에서 창 ① 이 막히는 것이 **도구의 흠인가 명세의 결과인가**?
- 창 ④ 가 하는 일을 한 문장으로 적어라.
- 창 ④ 가 요구하는 **허락**은 무엇인가?
- 이 주제에서 **부적용인 창**은 무엇인가?

### 12. 다른 주제와 잇기 (연결)

- HTML 갈래의 **10번** 과 이 주제의 경계선을 한 문장으로 그어라.
- 이벤트의 `e.target` 이 호스트로 오는 현상의 이름은? **정본은 어느 주제인가**?
- [10번 주제](../10-layout-thrashing/2-summary.md)와 견주면 이 주제는 **명세 쪽인가 구현 쪽인가**?
- [05번 주제](../05-documentfragment-and-template/2-summary.md)의 `DocumentFragment` 와 `ShadowRoot` 는 어떤 관계인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
