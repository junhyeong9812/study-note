# web-api/01 — 문서와 노드 트리: `Node`·`Element`·`Text`·`Comment` 와 두 컬렉션 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 답할 때는 「화면이 어떻게 보이나」가 아니라 「**`--dump-dom` 에 무엇이 남고 `length` 가 몇인가**」까지 말한다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 「다른 브라우저에서도 그렇다」는 여기서 주장하지 않는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 두 컬렉션의 길이 (예측)

```html
<div id="box">
  <p>첫 문단</p>
  <!-- 주석 -->
  <p>둘째 문단</p>
</div>
```

- `box.childNodes.length` 와 `box.children.length` 는 각각 몇인가?
- 두 수의 차이를 만든 노드들은 각각 무엇이고 몇 개씩인가?
- `<p>` 둘 사이의 줄바꿈과 들여쓰기는 노드 몇 개가 되는가?
- 같은 마크업을 **한 줄로 붙여 쓰면** 두 수가 어떻게 바뀌는가?

### 2. 첫째 자식을 집으면 (예측)

```js
box.firstChild
box.firstElementChild
box.childNodes[0].nodeValue
```

- 세 줄이 각각 무엇을 돌려주는가?
- `box.firstChild.textContent` 를 읽었을 때 빈 문자열이 나오는 이유는?
- 이 사고가 **개발 중에는 안 나다가 나중에 나는** 이유는 무엇인가?
- 「자식이 없다」를 판정하려면 무엇을 봐야 하는가?

### 3. 쌍의 두 이름이 답하는 것 (예측)

```js
p1.nextSibling
p1.nextElementSibling
p1.parentNode
p1.parentElement
```

- 네 줄이 각각 무엇을 돌려주는가?
- 이름에 `Element` 가 들어간 쪽과 안 들어간 쪽의 규칙을 한 문장으로 말하라.
- 부모 쌍이 나머지 다섯 쌍과 **성격이 다른** 이유는 무엇인가?
- 쌍은 모두 몇 개이고 무엇인가?

### 4. 나무 꼭대기에서 부모를 물으면 (예측)

```js
document.body.parentNode
document.body.parentElement
document.documentElement.parentNode
document.documentElement.parentElement
```

- 네 줄의 결과를 각각 예측하라.
- 갈리는 줄이 있다면 그 이유는 「부모가 없어서」인가?
- `while (el = el.parentNode)` 로 조상을 훑으면 무엇이 문제가 되는가?
- `DocumentFragment` 안에 있는 노드에서 같은 두 줄을 물으면?

### 5. `ownerDocument` 와 `isConnected` (예측)

```js
const el = document.createElement('b');
const other = document.implementation.createHTMLDocument('다른 문서');
const alien = other.createElement('i');
document.body.appendChild(alien);
```

- `el.ownerDocument === document` 와 `el.isConnected` 는 각각 무엇인가?
- `alien.ownerDocument` 는 붙이기 **전후로** 무엇을 가리키는가?
- 다른 문서의 노드를 그냥 붙였는데 예외가 안 나는 이유는 무엇인가?
- 「이 노드가 문서에 있나」를 물을 때 둘 중 무엇을 써야 하는가?

### 6. 번호표 여섯 개 (경계)

- `nodeType` 이 `1`·`3`·`8`·`9`·`10`·`11` 인 것은 각각 무엇인가?
- `2`·`4`·`5`·`6`·`12` 는 왜 비어 있는가?
- `nodeName` 이 `#` 으로 시작하는 것은 어떤 노드들인가?
- `nodeValue` 가 `null` 이 아닌 노드는 무엇인가?

### 7. `--dump-dom` 이 보여 주는 것 (경계)

- `--dump-dom` 의 출력은 **소스 파일**인가 **나무**인가? 무엇으로 그것을 알 수 있나?
- 소스에 `<html>`·`<head>`·`<body>` 를 안 썼는데 출력에 있는 이유는 무엇이고, 그 규칙의 정본은 어느 갈래인가?
- 스크립트가 붙인 `<hr>` 이 출력에 보이는 것은 이 도구의 어떤 성질 때문인가?
- 이 창이 **못 보는 것**은 무엇인가?

### 8. 공백 텍스트 노드가 안 생기는 자리 (왜)

- 태그 사이의 줄바꿈이 **노드가 되는데** 연속된 공백이 **여러 개가 아니라 하나**인 이유는 무엇인가?
- 마크업을 한 줄로 붙여 쓰면 공백 노드가 사라지는 이유는 무엇인가?
- 이미 생긴 공백 노드를 **표준 API 로 지우는 방법**이 있는가?
- 화면에서 공백이 하나로 합쳐 보이는 것과 노드가 남아 있는 것은 같은 이야기인가?

### 9. 무엇이 무엇을 상속하나 (경계)

```js
텍스트노드 instanceof Element
주석노드 instanceof CharacterData
조각 instanceof Node
document instanceof Element
```

- 네 줄의 결과를 말하고 그 계층을 그려라.
- `children` 이 텍스트 노드에는 없는 이유는 무엇인가?
- `childNodes` 는 어느 인터페이스가 주고 `children` 은 어느 인터페이스가 주는가?
- `DocumentFragment` 가 `children` 을 갖는 이유는 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- `childNodes` 와 `children` 이 **둘 다 라이브**라는 사실이 다음 주제에서 왜 출발점이 되는가?
- 「트리가 어떤 모양이 되나」와 「그 트리를 API 로 읽는다」의 경계는 어느 갈래끼리 갈리는가?
- `nodeName` 이 대문자인 것과 `SVG` 요소가 소문자인 것은 무엇이 다른 규칙인가?
- 「라이브냐 정적이냐」가 **구현 사정이 아니라 명세가 타입별로 정한 것**이라는 말은 무슨 뜻인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
