# web-api/13 — 커스텀 요소 수명주기: `customElements.define`·`connected`/`disconnected`/`attributeChanged`·업그레이드 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **마크업 갈래와의 경계** — HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **10번** 은 커스텀 요소를 **맛보기로** 다루고, 여기는 **수명주기 전부**다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★ 선행은 [12번 주제](../12-shadow-dom/2-summary.md)(그림자 경계)와 [03번 주제](../03-node-creation-insertion-removal/2-summary.md)(삽입이 이동이라는 것)다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `define` 을 부르기 전에 그 태그는 무엇인가 (예측)

```html
<!-- wa12b-13-q1.html -->
<my-card id="파서" 라벨="처음값" 안본다="이것도">파서가 먼저 만든 것</my-card>
<script>
  // 아직 define 을 안 불렀다
  파서.constructor.name          //  ?
  파서 instanceof HTMLElement    //  ?
  파서.matches(':defined')       //  ?
  customElements.get('my-card')  //  ?
  document.createElement('zzznope').constructor.name   //  ?
</script>
```

- 다섯 줄을 적어라.
- **하이픈이 든 태그와 안 든 태그**가 왜 갈리는가?
- 「아직 정의 안 됨」이라는 사실은 **어느 한 줄에만** 나타나는가?

### 2. `define` 한 줄이 무엇을 몇 번째로 부르나 (예측)

```js
// wa12b-13-q2.js
class MyCard extends HTMLElement {
  static get observedAttributes() { 로그('observedAttributes 를 읽는다'); return ['라벨']; }
  constructor() { super(); 로그('constructor'); }
  connectedCallback() { 로그('connectedCallback'); }
  attributeChangedCallback(n, o, v) { 로그('attributeChangedCallback ' + n); }
}
로그('(define 을 부르기 직전)');
customElements.define('my-card', MyCard);
로그('(define 이 돌아온 직후)');
```

- 로그가 몇 줄이고 **어떤 순서**인가?
- 마지막 줄이 무엇인지가 **무엇을 증명하는가**?
- `안본다="이것도"` 는 로그에 남는가?

### 3. `define` 을 먼저 하고 나서 만들면 (예측)

```js
// wa12b-13-q3.js
// 위와 같은 클래스인데 이번에는 define 을 먼저 하고 나서 만든다
const 새것 = document.createElement('my-card');   로그('(createElement 가 돌아온 직후)');
새것.setAttribute('라벨', '나중값');              로그('(setAttribute 가 돌아온 직후)');
document.body.appendChild(새것);                  로그('(appendChild 가 돌아온 직후)');
```

- 로그를 순서대로 적어라.
- **2번과 갈리는 칸**은 무엇인가?
- 그 차이가 **서버 렌더와 클라이언트 렌더**에서 무엇을 뜻하는가?

### 4. 문서 밖에 있는 요소는 (예측)

```js
// wa12b-13-q4.js
const 밖 = document.createElement('div');          // 문서에 안 붙인 조각이다
밖.innerHTML = '<late-el id="떼어낸" 라벨="ㄱ"></late-el>';
customElements.define('late-el', Late);            // 여기서 로그가 나오나?
customElements.upgrade(밖);                        // 그 다음에는?
document.body.appendChild(밖.children[0]);         // 그 다음에는?
```

- 세 자리에서 각각 무엇이 찍히는가?
- `upgrade()` 가 **안 부르는 콜백**은 무엇이고 왜인가?
- `upgrade()` 를 꼭 써야 하는 자리는 어디인가?

### 5. `observedAttributes` 는 언제 읽히나 (경계)

- `static get` 으로 써 놓으면 **부를 때마다** 읽히는가?
- 읽힌 횟수를 세면 몇인가?
- 그래서 **나중에 목록을 바꾸면** 어떻게 되는가?

### 6. 생성자 규칙을 어기면 (예측)

```js
// wa12b-13-q6.js
class 속성붙임 extends HTMLElement { constructor() { super(); this.setAttribute('만든속성', '값'); } }
class 자식만듦 extends HTMLElement { constructor() { super(); this.appendChild(document.createElement('b')); } }
class 슈퍼없음 extends HTMLElement { constructor() { } }
customElements.define('bad-attr', 속성붙임);
customElements.define('bad-child', 자식만듦);
customElements.define('no-super', 슈퍼없음);

document.createElement('bad-attr')        //  ?
document.createElement('bad-child')       //  ?
document.createElement('no-super')        //  ?
new 속성붙임()                             //  ?
const d = document.createElement('div');
d.innerHTML = '<bad-attr></bad-attr>';    //  ?
```

- 다섯 줄이 각각 **무엇을 돌려주는가**? 예외인가 조용한가?
- **예외 전문은 어디에 있는가**?
- 세 경로(`createElement` · `new` · 파싱) 가운데 **검사가 있는 곳은 몇 개인가**?

### 7. 이름과 등록이 거절되는 자리 (예측)

```js
// wa12b-13-q7.js
for (const 이름 of ['my-el', 'x-', 'a-b-c', 'my-EL', 'My-El', 'myel', '-el', '1-el',
                   'font-face', 'annotation-xml', 'my-el2', 'my-엘', '엘-my'])
  customElements.define(이름, class extends HTMLElement {});

customElements.define('once-el', 한번만);
customElements.define('once-el', class extends HTMLElement {});   //  ?
customElements.define('twice-el', 한번만);                        //  ?
customElements.define('arrow-el', () => {});                      //  ?
customElements.define('plain-el', class {});                      //  ?
```

- 열세 이름 가운데 **통과하는 것과 막히는 것**을 갈라라.
- 이름 문제와 등록 문제는 **예외 이름이 같은가**?
- 통과한 `plain-el` 과 `fn-el` 은 **쓸 수 있는가**?

### 8. `disconnectedCallback` 이 안 오는 자리 (경계)

- **온다** — `remove()` · `innerHTML = ""` · 다른 부모로 옮기기 · 같은 부모에 다시 붙이기 · 다른 문서로 옮기기 · 호스트를 떼기.
- **안 온다** — 무엇이 더 있는가? **다섯을 대라.**
- 그래서 「정리」를 이 콜백에만 걸면 무엇이 안 되는가?
- `moveBefore()` 가 이 이야기를 어떻게 바꾸는가?

### 9. 같은 노드가 클래스를 갈아입는다는 것 (왜)

- 업그레이드가 **새 노드를 만들지 않는다**는 근거를 대라.
- 그래서 이 주제에서 **창 ① 이 부적용인** 이유는?
- 업그레이드가 **동기**라는 것은 왜 중요한가?

### 10. 왜 창 ⑤ 가 필요한가 (왜)

- 이 주제에서 **창 ④ 가 답하는 것**은 무엇인가?
- 창 ⑤ 가 없으면 **무엇이 통째로 안 보이는가**?
- 「콘솔에 두 줄뿐이니 두 번 났다」로 읽어도 되는가?
- 이 주제에서 **못 재는 것**은 무엇인가?

### 11. 실무의 짝 맞추기 (경계)

- `connectedCallback` 에서 리스너를 달면 **무엇이 잘못되는가**? 어떻게 고치는가?
- 컴포넌트를 `<button>` 으로 만들 수 없는 이유와 그 해법은?
- 같은 모듈이 두 번 읽힐 수 있는 환경에서 `define` 을 어떻게 부르는가?

### 12. 다른 주제와 잇기 (연결)

- [12번 주제](../12-shadow-dom/2-summary.md)와 이 주제의 경계선을 한 문장으로 그어라.
- [03번 주제](../03-node-creation-insertion-removal/2-summary.md)의 어느 사실이 **콜백이 한 쌍으로 나는 이유**인가?
- [06번 주제](../06-attribute-vs-property/2-summary.md)의 구분이 `attributeChangedCallback` 에 어떻게 걸리는가?
- 「떠날 때」를 잡는 정본은 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
