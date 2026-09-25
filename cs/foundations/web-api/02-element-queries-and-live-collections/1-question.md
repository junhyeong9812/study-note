# web-api/02 — 요소 조회: `querySelector` 계열과 `getElementsBy*`·라이브 대 정적 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 이 주제의 답은 거의 전부 「**그래서 `length` 가 몇이냐**」다. 시점을 같이 말하라 — 잡을 때 / 바꾼 뒤.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 넷을 잡아 두고 DOM 을 바꾸면 (예측)

```js
const byTag   = document.getElementsByTagName('li');
const byClass = document.getElementsByClassName('item');
const kids    = list.children;
const snap    = document.querySelectorAll('li');
// 여기까지 <li> 는 둘. 이제 <li class="item">C</li> 를 하나 붙인다
```

- 붙이기 **전후로** 네 `length` 를 각각 적어라.
- 이어서 첫 `<li>` 를 지우면 네 수는 어떻게 되는가?
- 마지막 시점의 `snap[0]` 은 무엇을 가리키고 `snap[0].isConnected` 는 무엇인가?
- 이 실험에서 **시점이 셋** 필요한 이유는 무엇인가?

### 2. 같은 타입에서 갈리는 것 (예측)

```js
const cn = box.childNodes;
const qs = box.querySelectorAll('span');
Object.prototype.toString.call(cn)
cn.constructor === qs.constructor
// 그 뒤 box 에 <span> 을 하나 붙인다
```

- 두 번째·세 번째 줄의 결과는 무엇인가?
- `<span>` 을 붙인 뒤 `cn.length` 와 `qs.length` 는 각각 몇인가?
- 「`NodeList` 는 정적이고 `HTMLCollection` 은 라이브」라는 요약은 어디가 틀렸는가?
- 그래서 라이브 여부를 판정할 때 무엇을 봐야 하는가?

### 3. 지우는 반복문 (예측)

```js
const live = wrap.getElementsByClassName('x');   // <p class="x"> 가 4개
for (let i = 0; i < live.length; i++) live[i].remove();
```

- 끝나고 나면 `wrap` 에 몇 개가 남고 그것은 무엇인가?
- `i` 가 어느 값까지 도는지 한 판씩 적어라.
- 같은 반복문을 `querySelectorAll` 로 바꾸면 결과가 어떻게 되는가?
- 라이브 컬렉션을 그대로 쓰면서 고치는 방법 두 가지는 무엇인가?

### 4. 기준 요소에 대고 물으면 (예측)

```html
<div id="outer">
  <p id="a">바깥 문단</p>
  <div id="inner"><p id="b">안쪽 문단</p></div>
</div>
```

```js
outer.querySelectorAll('div p')
outer.querySelectorAll(':scope > p')
outer.getElementById('a')
```

- 세 줄의 결과를 각각 예측하라.
- 첫 줄이 그렇게 나오는 이유를 「매치」와 「걸러내기」로 갈라 설명하라.
- 세 번째 줄이 그렇게 되는 이유는 무엇이고, 그 API 는 어느 인터페이스가 주는가?
- 문서에서 떼어낸 트리 안의 `id` 를 `document.getElementById` 로 찾으면?

### 5. 잘못된 선택자를 주면 (예측)

```js
document.querySelectorAll('div:has(')
document.getElementsByTagName('div:has(')
document.getElementsByClassName('.ok')
document.querySelectorAll(':is(.ok, ::bogus)')
```

- 네 줄이 각각 무엇을 돌려주거나 던지는가?
- 던지는 것이 있다면 그 예외의 `name`·타입·`code` 는 무엇인가?
- `catch (e) { if (e instanceof SyntaxError) }` 로 잡히는가?
- 같은 무효 선택자를 **스타일시트에 쓰면** 어떻게 되는가? 어느 갈래가 정본인가?

### 6. 다섯 API 의 반환 타입 (경계)

- `getElementById`·`getElementsByTagName`·`getElementsByClassName`·`querySelector`·`querySelectorAll` 의 반환 타입을 각각 대라.
- 그중 라이브인 것은 무엇이고, 「언제나 라이브인 타입」은 무엇인가?
- `HTMLCollection` 에 있고 `NodeList` 에 없는 것, 그 반대는 각각 무엇인가?
- 라이브 목록에 `map`·`filter` 를 걸려면 무엇을 해야 하는가?

### 7. `getElementById` 에 탐색 범위가 없는 이유 (왜)

- `getElementById` 가 `Document` 에만 있는 것은 어느 믹스인 때문인가?
- 「`id` 는 문서에서 유일하다」는 규칙과 이 설계는 어떻게 이어지는가?
- 그런데 같은 `id` 가 둘이면 무엇이 돌아오고, `querySelectorAll('#dup')` 는 몇 개를 주는가?
- `document.getElementById('x')` 와 `document.querySelector('#x')` 는 무엇이 다른가?

### 8. 정적 스냅샷이 들고 있는 것 (경계)

- 「정적」은 「낡았다」인가 「고정됐다」인가? 그 차이가 왜 중요한가?
- 스냅샷을 잡은 뒤 그 노드를 문서에서 지우면 스냅샷은 어떻게 되는가?
- 그것이 메모리 문제가 되는 경로는 무엇인가?
- 최신 상태가 필요하면 무엇을 해야 하는가?

### 9. 어느 쪽이 이득인가 (경계)

- 「지금 몇 개인가」를 계속 물어야 하는 화면에서는 어느 쪽이 나은가?
- 목록을 잡아 두고 순회하며 **바꾸는** 코드에서는 어느 쪽이 나은가?
- 반복문 조건에 `live.length` 를 두면 **명세상 무엇이 보장되는가**? 그 비용은 이 문서가 쟀는가?
- `[...live]` 한 줄이 하는 일을 한 문장으로 말하라.

### 10. 다른 주제와 잇기 (연결)

- 「라이브냐 정적이냐」가 **구현 최적화가 아니라 명세의 계약**이라는 말은 무슨 뜻인가?
- 무효한 선택자를 **API 는 던지고 스타일시트는 버리는** 차이는 무엇이 만들었는가?
- 선택자 문법 자체와 「그 선택자를 API 로 던진 계약」은 어느 갈래끼리 갈리는가?
- `innerHTML` 로 트리를 통째로 갈면 잡아 둔 라이브 컬렉션과 정적 스냅샷은 각각 어떻게 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
