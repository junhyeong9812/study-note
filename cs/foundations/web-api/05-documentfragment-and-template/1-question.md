# web-api/05 — `DocumentFragment` 와 `<template>` 복제: 일괄 삽입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 비용을 묻는 문항에서는 **숫자를 외우지 마라.** 이 주제의 수치는 흔들린다 — **자릿수와 순위**만 답하면 된다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★ 선행은 [03번 주제](../03-node-creation-insertion-removal/2-summary.md)다. 「삽입은 이동」을 알고 있다고 본다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 조각을 붙이고 나서 조각을 보면 (예측)

```js
const frag = document.createDocumentFragment();
for (const t of ['가', '나', '다']) frag.appendChild(만든li(t));
const back = host.appendChild(frag);
host.appendChild(frag);
```

- `frag.nodeType` 과 `frag.nodeName` 은 각각 무엇인가?
- 마지막 두 줄 뒤 `host.children.length` 는 몇인가?
- `back` 은 무엇이고 `back.childNodes.length` 는 몇인가?
- `host.querySelector` 로 조각 자신을 찾을 수 있는가?

### 2. 같은 셋을 두 경로로 넣으면 (예측)

```js
hostA.appendChild(세개를_담은_조각);
for (const t of ['가','나','다']) hostB.appendChild(만든li(t));
```

- `hostA.innerHTML` 과 `hostB.innerHTML` 을 비교하면 어떻게 되는가?
- 두 경로를 **결과 트리만 보고** 구분할 수 있는가?
- `MutationObserver` 를 붙여 두면 각각 레코드를 몇 개 받는가?
- 그래서 조각이 실제로 줄이는 것은 무엇이라고 말해야 하는가?

### 3. `<template>` 안을 밖에서 찾으면 (예측)

```html
<template id="tpl"><li class="row">항목</li><li class="row">항목</li></template>
<li class="row" id="real">본 문서에 있는 것</li>
```

```js
tpl.childNodes.length
document.querySelector('#tpl li')
document.querySelectorAll('.row').length
tpl.content.ownerDocument === document
```

- 네 줄의 결과를 각각 예측하라.
- `--dump-dom` 으로 찍은 트리에는 틀의 내용이 **보이는가**?
- 그 문서의 `defaultView`·`documentElement` 는 무엇인가?
- 창 ① 과 창 ② 로는 왜 이 사실이 안 잡히는가?

### 4. 틀 안의 `<script>` 와 `<img>` (예측)

```html
<template id="tpl"><script>C.tplScript++</script><img src="(유효한 data URI)" onload="C.tplImg++"></template>
<div id="plain"><script>C.plainScript++</script><img src="(같은 것)" onload="C.plainImg++"></div>
```

- 파싱이 끝난 시점에 `C.tplScript` 와 `C.plainScript` 는 각각 몇인가?
- 틀 안 `<img>` 의 `complete`·`naturalWidth`·`currentSrc` 는 각각 무엇인가?
- 그 `<script>`·`<img>` 노드는 트리에 **있는가**?
- `host.appendChild(tpl.content.cloneNode(true))` 한 뒤에는 무엇이 달라지는가?

### 5. 세 가지 복제 (예측)

```js
tpl.content.cloneNode(true)
document.importNode(tpl.content, true)
document.importNode(tpl.content)
document.adoptNode(프레임안의_p)
```

- 네 줄의 결과를 `ownerDocument`·`childNodes.length`·**원본이 남는가**로 나누어 적어라.
- 셋째 줄이 첫째 줄과 갈리는 이유는 무엇인가?
- `cloneNode` 로 만든 것을 그대로 `appendChild` 하면 `ownerDocument` 는 어떻게 되는가?
- 그래서 `cloneNode` 와 `importNode` 중 무엇을 쓸지가 실제로 갈리는 경우는 언제인가?

### 6. 비용 (예측)

```js
// 2000개 항목을 네 방식으로 · 그리고 삽입 사이에 offsetHeight 를 읽는 조건으로
for (…) host.appendChild(만든li());
const f = frag(); for (…) f.appendChild(만든li()); host.appendChild(f);
for (…) { host.appendChild(만든li()); sink += host.offsetHeight; }
```

- 앞의 두 방식의 **자릿수 순위**를 매겨라.
- 부모가 트리 밖(detached)이면 순위가 달라지는가?
- 세 번째 방식만 크게 다르다면 그 원인은 **삽입 횟수인가 다른 것인가**?
- 이 문서가 「조각을 쓰면 빨라진다」를 **주장하지 않는** 이유는 무엇인가?

### 7. 틀이 안 도는 이유 (왜)

- `<script>` 가 안 돈 것과 `<img>` 가 요청조차 안 한 것은 **같은 원인인가**?
- 그 원인을 한 문장으로 적어라.
- `display: none` 인 `<div>` 안의 `<script>` 는 도는가? 둘의 차이는 무엇인가?
- `<template>` 을 XSS 방어에 쓰면 안 되는 이유를 실측으로 설명하라.

### 8. 04번과 결과가 반대인 자리 (경계)

- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)는 「파서가 만든 `script` 는 자리를 옮겨도 안 돈다」를 실측했다. 여기서는 복제해 붙이자 **돌았다.** 무엇이 갈랐는가?
- 「이미 시작된」 표시는 언제 찍히는가?
- `createElement('script')` 로 만든 것은 어느 쪽과 같은가?
- 두 실측을 하나의 규칙으로 묶어 적어라.

### 9. 조각과 틀을 언제 안 쓰나 (경계)

- 한 번만 쓸 묶음에 `<template>` 을 쓰면 무엇이 번거로워지는가?
- 여러 번 찍을 것에 조각을 쓰면 무엇이 터지는가?
- `host.appendChild(tpl.content)` 가 **첫 렌더에서는 잘 되는** 이유는 무엇인가?
- 조각을 비우지 않고 자식만 넘기려면 어떻게 쓰는가?

### 10. 다른 주제와 잇기 (연결)

- [03번 주제](../03-node-creation-insertion-removal/2-summary.md)의 「삽입은 이동」이 조각에도 그대로 적용되는 자리를 짚어라.
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 조회 범위 규칙으로 「틀 안이 안 잡힌다」를 설명하라.
- [목록의 **10번 주제**](../10-layout-thrashing/)(레이아웃 스래싱)가 이 주제의 비용 측정에서 미리 드러난 자리는 어디인가?
- 목록의 **37번 주제**(`MutationObserver`)를 이 주제가 **근거로** 쓴 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
