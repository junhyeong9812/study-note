# web-api/13 — 커스텀 요소 수명주기: `customElements.define`·`connected`/`disconnected`/`attributeChanged`·업그레이드 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★ **마크업 갈래와의 경계** — HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **10번** 이 커스텀 요소를 **맛보기로** 다룬다(파서가 만든 요소가 `define` 으로 살아나는 것까지). **여기는 그 수명주기 전부**다 — 넷의 순서, 업그레이드의 세 경로, 생성자 규칙, 이름 규칙.\
> **기준 소스** — [WHATWG HTML Living Standard — Custom elements](https://html.spec.whatwg.org/multipage/custom-elements.html) 의 「Custom element conformance」·「`CustomElementRegistry`」·「Upgrades」·「Custom element reactions」 절과 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「Mutation algorithms」. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. **콘솔 블록 하나만 `--enable-logging=stderr` 로 따로 받았다** — 이 주제의 가장 중요한 사실이 **콘솔에만** 남기 때문이다((6)).\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** 특히 **내장 요소 확장(`is=`)은 엔진마다 갈리는 표면**이다.\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `customElements` 는 오래된 표면이고 **`customElements.getName()`·`connectedMoveCallback`·`moveBefore()` 는 새 표면**이다(아래 「구현 세부사항 대 언어 보장」).\
> **선행** — [12번 주제](../12-shadow-dom/2-summary.md)(그림자 경계)와 [03번 주제](../03-node-creation-insertion-removal/2-summary.md)(삽입·이동·제거가 무엇인가).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 시간도 좌표도 안 재고 **순서만** 재기 때문이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 모든 콜백 **순서** · `constructor.name` · `matches(':defined')` · 이름 규칙의 통과/거절 · 예외 **이름** · `observedAttributes` 가 읽힌 **횟수** | 명세가 절차로 정해 둔 것이다. **두 판을 돌려 한 글자도 같았다** |
| **흔들린다** | Chrome 판 번호 · 예외의 **문구** · 콘솔 줄의 **파일 줄 번호** | **이름은 명세, 문구는 구현**이다 |
| ★ **합쳐진다** | **콘솔 경고·에러의 줄 수** | Chrome 이 **같은 자리에서 난 것을 합친다.** 「안 보인다」를 「안 났다」로 읽으면 안 된다 |
| **못 잰다** | **페이지를 떠날 때 `disconnectedCallback` 이 오나** | 문서가 이미 없어 관측 자체가 성립하지 않는다((7)) |
| **못 잰다** | 가비지 컬렉션이 콜백을 내나 | GC 시점을 이 도구로 몰 수 없다 |
| **부적용** | `--dump-dom` 트리로 「업그레이드됐나」 보기 | 업그레이드는 **직렬화에 자국을 안 남긴다** — 태그 이름이 처음부터 끝까지 같다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

## 한눈에 — 쉽게 말하면

**★ 커스텀 요소는 「새 태그를 만드는 것」이 아니다. 파서는 아무 태그나 이미 만들어 두고, `define` 이 나중에 그 껍데기에 알맹이를 채운다.**

부품이 먼저 오고 설명서가 나중에 오는 조립 공장에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 설명서가 없어도 **부품은 이미 라인에 올라와 있다** | 파서가 `<my-card>` 를 `HTMLElement` 로 만들어 둔다 |
| **설명서가 도착한다** | `customElements.define('my-card', MyCard)` |
| 라인 위의 부품을 **전부 되돌아가 조립한다** | 업그레이드 — 문서 안의 요소를 전부 훑는다 |
| **창고에 쌓인 부품은 그냥 둔다** | 문서 밖 트리는 업그레이드되지 않는다 |
| 창고 것도 **지금 조립해 달라고 부른다** | `customElements.upgrade(노드)` |
| 조립 **순서가 정해져 있다** | observedAttributes → constructor → attributeChanged → connected |
| **조립대 위에서는 부품에 손대면 안 된다** | 생성자에서 속성·자식을 만들면 안 된다 |
| 어겨도 **알람이 안 울리고 불량품만 나온다** | `HTMLUnknownElement` 가 돌아온다. 예외는 콘솔에만 |
| 설명서는 **한 번 등록하면 못 바꾼다** | 같은 이름·같은 클래스를 두 번 등록하면 `NotSupportedError` |
| **라인에서 내려도 폐기 신호는 아니다** | `disconnectedCallback` 은 소멸자가 아니다 |

```text
   한 태그가 지나가는 두 갈래 길

   ① 파서가 먼저 만든다 (define 이 나중)
      <my-card>  --파서-->  HTMLElement (':defined' 는 false)
                 --define--> observedAttributes -> constructor
                             -> attributeChanged(초기 속성 전부) -> connected

   ② define 이 먼저다 (createElement 가 나중)
      createElement --> constructor
      setAttribute  --> attributeChanged   (내가 부른 만큼만)
      appendChild   --> connected

   ★ 같은 클래스인데 '초기 속성에 콜백이 오나' 가 갈린다 — ① 만 온다
```

## 이 주제가 답하려는 질문

1. **`define` 한 줄이 무엇을 언제 부르나** — 넷의 순서가 고정인가, 그리고 **동기인가.**
2. **업그레이드는 어디까지 미치나** — 문서 밖의 요소는? `upgrade()` 는 무엇을 더 하나?
3. **생성자에서 하면 안 되는 일을 어기면 무엇이 보이나** — 예외인가, 조용한가.

## 이 갈래의 관측 창 — ★ 본체는 창 ④ 다

**★ 이 주제의 본체는 창 ④(「콜백을 전부 로그로 받아 순서를 본다」)다.** 창 ① 은 이 주제에서 **부적용**이다 — 업그레이드는 직렬화에 자국을 남기지 않는다.

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋 위에 이 주제의 창 **둘**을 얹는다.

```text
  창 1  --dump-dom            스크립트가 다 돈 뒤의 트리를 글자로
        ★ 부적용 — <my-card> 는 업그레이드 전에도 뒤에도 같은 글자다
  창 2  노드 단위 프로브        constructor.name · matches(':defined') · customElements.get()
  창 3  같은 것을 두 번 읽기    define 전에 한 번 / 뒤에 한 번 — 같은 노드가 클래스를 갈아입는다
  ★ 창 4 (이 주제의 본체)  콜백을 전부 로그 배열로 받아 '순서' 를 본다
        무엇을 답하나:  '무엇이 불렸나' 가 아니라 '무엇이 몇 번째로 불렸나'
        왜 필요한가:    이 주제의 사실이 전부 순서다. 한 시점만 보면 넷이 구분되지 않는다
  ★ 창 5 (이 주제가 더 세운 것)  콘솔
        무엇을 답하나:  생성자 규칙을 어겼을 때의 예외 전문
        왜 필요한가:    반환값에도 없고 try/catch 에도 안 잡힌다. 오직 여기에만 남는다
  ★ 못 재는 창  페이지를 떠날 때의 disconnectedCallback
        문서가 이미 없어 로그를 뱉을 자리가 없다. (7) 에서 성질로만 적는다
```

- ★★ **창 ⑤ 는 「제5의 상태」의 대응책**이다. 세 창이 전부 정상인데(요소가 만들어지고, 문서에 붙고, 태그 이름도 맞다) **그 요소가 죽어 있는** 경우가 있다((6)).

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| **페이지를 떠날 때 콜백이 오나** | 로그를 뱉을 문서가 이미 없다. 「안 왔다」와 「못 봤다」를 이 도구로는 못 가른다 |
| **가비지 컬렉션이 콜백을 내나** | GC 시점을 못 몬다. 명세가 「안 낸다」로 정해 두었을 뿐이다 |
| **콘솔에 안 남은 경고가 안 난 것인가** | Chrome 이 같은 자리를 합친다. 줄 수를 세는 근거로 쓰면 안 된다 |
| 다른 엔진의 동작 | 엔진이 하나뿐이다. 특히 **`is=` 는 엔진마다 갈린다** |
| 업그레이드의 **비용** | 재지 않았다. 이 문서는 성능을 한 줄도 주장하지 않는다 |
| 스크린리더가 커스텀 요소를 **어떻게 읽는지** | 접근성 트리는 보조 기술의 **입력**이지 출력이 아니다 |

## 동작 방식

### (1) `define` 하기 전 — 파서는 이미 만들어 두었다

**언제 쓰나** — 스크립트가 늦게 오는 페이지에서 「그 전에는 무엇인가」를 따질 때.

**던진 것** — 아래 (2)\~(4)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-13-order.html -->
<!doctype html>
<meta charset="utf-8">
<title>13-order</title>
<my-card id="파서" 라벨="처음값" 안본다="이것도">파서가 먼저 만든 것</my-card>
<script>
const O = [];
const 로그 = [];
const $ = id => document.getElementById(id);

O.push('define 하기 전 — 파서가 만들어 둔 요소의 정체');
O.push('  constructor.name          = ' + $('파서').constructor.name);
O.push('  instanceof HTMLElement    = ' + ($('파서') instanceof HTMLElement));
O.push('  matches(":defined")       = ' + $('파서').matches(':defined'));
O.push('  customElements.get("my-card") = ' + customElements.get('my-card'));
O.push('  ★ 알 수 없는 태그가 아니다 — HTMLElement 로는 이미 살아 있다. 「업그레이드 안 된 것」일 뿐이다.');
O.push('  참고: 하이픈 없는 알 수 없는 태그는 ' + document.createElement('zzznope').constructor.name + ' 이다.');
O.push('');

class MyCard extends HTMLElement {
  static get observedAttributes() { 로그.push('static observedAttributes 를 읽는다'); return ['라벨']; }
  constructor() { super(); 로그.push('constructor'); }
  connectedCallback() { 로그.push('connectedCallback'); }
  disconnectedCallback() { 로그.push('disconnectedCallback'); }
  adoptedCallback() { 로그.push('adoptedCallback'); }
  attributeChangedCallback(이름, 옛값, 새값) {
    로그.push('attributeChangedCallback ' + 이름 + ' ' + JSON.stringify(옛값) + ' -> ' + JSON.stringify(새값));
  }
}
로그.push('(define 을 부르기 직전)');
customElements.define('my-card', MyCard);
로그.push('(define 이 돌아온 직후)');

O.push('define("my-card", MyCard) 한 줄이 만든 순서');
로그.forEach((l, i) => O.push('  ' + String(i + 1).padStart(2) + '. ' + l));
O.push('');
O.push('  ★ 업그레이드는 define 이 돌아오기 전에 끝난다 — 동기다.');
O.push('  ★ 순서가 고정이다: observedAttributes -> constructor -> attributeChanged(초기 속성) -> connected.');
O.push('  ★ 안본다="이것도" 는 observedAttributes 에 없어 한 줄도 안 남겼다.');
O.push('');
O.push('업그레이드 뒤');
O.push('  constructor.name    = ' + $('파서').constructor.name);
O.push('  matches(":defined") = ' + $('파서').matches(':defined'));
O.push('  자식 텍스트는 그대로 = ' + JSON.stringify($('파서').textContent));
O.push('  customElements.get("my-card") = ' + customElements.get('my-card').name);
O.push('  customElements.getName(MyCard) = ' + customElements.getName(MyCard));
O.push('');

O.push('define 한 뒤에 만들면 — 순서가 달라진다');
로그.length = 0;
const 새것 = document.createElement('my-card');
로그.push('(createElement 가 돌아온 직후)');
새것.setAttribute('라벨', '나중값');
로그.push('(setAttribute 가 돌아온 직후)');
document.body.appendChild(새것);
로그.push('(appendChild 가 돌아온 직후)');
로그.forEach((l, i) => O.push('  ' + String(i + 1).padStart(2) + '. ' + l));
O.push('  ★ 이쪽은 constructor 가 먼저고 속성·연결은 내가 부른 만큼만 난다.');
O.push('  ★ 「초기 속성에도 attributeChangedCallback 이 온다」는 업그레이드 경로의 성질이다.');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-order.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
define 하기 전 — 파서가 만들어 둔 요소의 정체
  constructor.name          = HTMLElement
  instanceof HTMLElement    = true
  matches(":defined")       = false
  customElements.get("my-card") = undefined
  ★ 알 수 없는 태그가 아니다 — HTMLElement 로는 이미 살아 있다. 「업그레이드 안 된 것」일 뿐이다.
  참고: 하이픈 없는 알 수 없는 태그는 HTMLUnknownElement 이다.
(exit 0)
```

- ★★ **알 수 없는 태그가 아니다.** `constructor.name` 이 **`HTMLElement`** 이고 `instanceof HTMLElement` 가 `true` 다. **DOM 에 이미 살아 있다.**
- **`matches(':defined')` 만 `false`** 다 — 「아직 업그레이드 안 된 것」이라는 표시가 여기에만 있다.
- ★ **하이픈이 없는 알 수 없는 태그는 다르다** — `zzznope` 는 **`HTMLUnknownElement`** 다. **하이픈 하나가 「앞으로 커스텀 요소가 될 수 있다」는 예약**이고, 파서가 그 약속을 지켜 `HTMLElement` 로 만들어 둔다.
- **`customElements.get('my-card')` 는 `undefined`** 다 — 아직 아무도 등록하지 않았다.

```text
   하이픈 하나가 가르는 것

   <zzznope>   ->  HTMLUnknownElement     영영 업그레이드될 수 없다
   <my-card>   ->  HTMLElement            ':defined' 는 false — 기다리는 중이다
                    |
                    +-- define 이 오면 --> MyCard  (같은 노드다. 새로 안 만든다)

   ★ 파서는 define 을 기다리지 않는다. 껍데기를 먼저 만들어 둔다
```

### (2) ★ 본체 — `define` 한 줄이 만든 순서

**언제 쓰나** — 「생성자에서 속성을 읽어도 되나」 같은 질문이 나올 때. **답은 전부 순서에 있다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-order.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,19p'
define("my-card", MyCard) 한 줄이 만든 순서
   1. (define 을 부르기 직전)
   2. static observedAttributes 를 읽는다
   3. constructor
   4. attributeChangedCallback 라벨 null -> "처음값"
   5. connectedCallback
   6. (define 이 돌아온 직후)

  ★ 업그레이드는 define 이 돌아오기 전에 끝난다 — 동기다.
  ★ 순서가 고정이다: observedAttributes -> constructor -> attributeChanged(초기 속성) -> connected.
  ★ 안본다="이것도" 는 observedAttributes 에 없어 한 줄도 안 남겼다.
(exit 0)
```

- ★★★ **순서가 고정이다** — `observedAttributes` → `constructor` → `attributeChangedCallback`(초기 속성) → `connectedCallback`.
- ★★ **업그레이드는 `define` 이 돌아오기 전에 끝난다.** 마지막 줄이 「(define 이 돌아온 직후)」인 것이 그 증거다 — **동기다.** `define` 다음 줄에서 곧바로 인스턴스를 써도 된다.
- ★ **`observedAttributes` 가 가장 먼저 읽힌다.** 그래야 「어떤 속성을 감시할지」를 알고 초기 속성을 훑을 수 있다.
- ★★ **초기 속성에도 `attributeChangedCallback` 이 온다** — `라벨="처음값"` 이 `null -> "처음값"` 으로 한 번 왔다. **그런데 `안본다="이것도"` 는 한 줄도 안 남겼다** — `observedAttributes` 에 없어서다.
- **`connectedCallback` 이 마지막**이다. 그래서 「DOM 에 붙었을 때 할 일」을 거기에 쓴다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-order.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '21,26p'
업그레이드 뒤
  constructor.name    = MyCard
  matches(":defined") = true
  자식 텍스트는 그대로 = "파서가 먼저 만든 것"
  customElements.get("my-card") = MyCard
  customElements.getName(MyCard) = my-card
(exit 0)
```

- **업그레이드 뒤에도 같은 노드다** — `id` 도 자식 텍스트도 그대로이고 **클래스만 갈아입었다.** 새로 만들어 바꿔 끼운 것이 아니다.
- **`customElements.getName(MyCard)` 로 역방향 조회**도 된다.

```text
   업그레이드는 노드를 바꾸지 않는다

   전   <my-card id="파서" 라벨="처음값">파서가 먼저 만든 것</my-card>
        constructor.name = HTMLElement   ':defined' = false
              |
              |  define('my-card', MyCard)   <- 같은 노드의 프로토타입을 갈아 끼운다
              v
   후   <my-card id="파서" 라벨="처음값">파서가 먼저 만든 것</my-card>
        constructor.name = MyCard        ':defined' = true

   ★ 창 ① 로 보면 전후가 한 글자도 같다 — 그래서 창 ① 이 부적용이다
```

### (3) `define` 을 먼저 하면 순서가 달라진다

**언제 쓰나** — 컴포넌트를 스크립트로 만들어 쓸 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-order.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '28,36p'
define 한 뒤에 만들면 — 순서가 달라진다
   1. constructor
   2. (createElement 가 돌아온 직후)
   3. attributeChangedCallback 라벨 null -> "나중값"
   4. (setAttribute 가 돌아온 직후)
   5. connectedCallback
   6. (appendChild 가 돌아온 직후)
  ★ 이쪽은 constructor 가 먼저고 속성·연결은 내가 부른 만큼만 난다.
  ★ 「초기 속성에도 attributeChangedCallback 이 온다」는 업그레이드 경로의 성질이다.
(exit 0)
```

- **`constructor` 가 맨 먼저**고, 그 다음은 **내가 부른 만큼만** 난다 — `setAttribute` 한 번에 `attributeChangedCallback` 한 번, `appendChild` 에 `connectedCallback` 한 번.
- ★★ **「초기 속성에도 콜백이 온다」는 업그레이드 경로의 성질이다.** 이 경로에는 「초기 속성」이라는 것이 아예 없다 — 요소가 만들어질 때는 속성이 하나도 없기 때문이다.
- ★ **그래서 두 경로가 같은 코드를 다르게 돌린다.** 서버 렌더한 마크업을 하이드레이션할 때(①)와 클라이언트에서 만들 때(②)가 **콜백 횟수부터 다르다.**

```text
   같은 컴포넌트, 두 경로의 콜백 장부

   ① 파서 + define            ② createElement + setAttribute + appendChild
   ---------------------      --------------------------------------------
   observedAttributes  1      observedAttributes  1  (define 때 이미 끝났다)
   constructor         1      constructor         1
   attributeChanged    N      attributeChanged    내가 부른 횟수만큼
        (초기 속성 N개 전부)
   connected           1      connected           1

   ★ 속성이 셋 달린 마크업이면 ① 은 attributeChanged 가 3번, ② 는 0번으로 시작한다
```

### (4) 업그레이드가 미치는 범위 — 문서 안뿐이다

**언제 쓰나** — `DocumentFragment`·`<template>`·떼어 놓은 트리를 쓸 때.

**던진 것** — 아래 (5)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-13-upgrade.html -->
<!doctype html>
<meta charset="utf-8">
<title>13-upgrade</title>
<div id="자리"></div>
<script>
const O = [];
const 로그 = [];
const $ = id => document.getElementById(id);
const 비우기 = () => { const v = JSON.stringify(로그); 로그.length = 0; return v; };

class Late extends HTMLElement {
  static observedAttributes = ['라벨'];
  constructor() { super(); 로그.push('constructor'); }
  connectedCallback() { 로그.push('connected'); }
  disconnectedCallback() { 로그.push('disconnected'); }
  adoptedCallback() { 로그.push('adopted'); }
  attributeChangedCallback(n, o, v) { 로그.push('attrChanged ' + n + ' ' + JSON.stringify(o) + '->' + JSON.stringify(v)); }
}

O.push('문서에 없는 요소는 define 해도 업그레이드되지 않는다');
const 밖 = document.createElement('div');
밖.innerHTML = '<late-el id="떼어낸" 라벨="ㄱ"></late-el>';
O.push('  define 전 constructor.name = ' + 밖.children[0].constructor.name);
customElements.define('late-el', Late);
O.push('  define 직후 로그 = ' + 비우기() + ' · constructor.name = ' + 밖.children[0].constructor.name);
O.push('  ★ 「문서 안의 요소」만 자동으로 업그레이드된다 — 떼어 놓은 트리는 그대로다.');
O.push('');
O.push('직접 재촉하는 두 길');
customElements.upgrade(밖);
O.push('  customElements.upgrade(밖) 뒤 로그 = ' + 비우기());
O.push('    constructor.name = ' + 밖.children[0].constructor.name + ' · connected 는 안 불렸다(문서에 없으니까)');
$('자리').appendChild(밖.children[0]);
O.push('  그 요소를 문서에 붙이면 로그 = ' + 비우기());
const 밖2 = document.createElement('div');
밖2.innerHTML = '<late-el id="붙여서" 라벨="ㄴ"></late-el>';
$('자리').appendChild(밖2);
O.push('  upgrade() 없이 그냥 붙이면 로그 = ' + 비우기() + '  <- 붙이는 순간 업그레이드된다');
O.push('');
O.push('static observedAttributes 는 언제 읽히나');
let 읽힌횟수 = 0;
class Watch extends HTMLElement {
  static get observedAttributes() { 읽힌횟수++; return ['보는것']; }
  attributeChangedCallback(n, o, v) { 로그.push('attrChanged ' + n); }
}
customElements.define('watch-el', Watch);
O.push('  define 직후 읽힌 횟수 = ' + 읽힌횟수);
const w = document.createElement('watch-el');
$('자리').appendChild(w);
w.setAttribute('보는것', '1'); w.setAttribute('보는것', '2'); w.setAttribute('안보는것', 'x');
O.push('  요소를 만들고 속성을 세 번 바꾼 뒤 읽힌 횟수 = ' + 읽힌횟수 + ' · 로그 = ' + 비우기());
Watch.observedAttributes;
O.push('  ★ define 시점에 한 번만 읽는다 — 나중에 목록을 바꿔도 소용없다.');
O.push('');
O.push('whenDefined 와 :defined');
O.push('  이미 정의된 것: customElements.whenDefined("late-el") 은 Promise 이고 값은 아래에서 확인한다');
const 아직 = document.createElement('div');
아직.innerHTML = '<never-el id="영영">아직 정의 안 된 것</never-el>';
$('자리').appendChild(아직);
O.push('  never-el 의 matches(":defined") = ' + $('영영').matches(':defined')
     + ' · constructor.name = ' + $('영영').constructor.name);
const 순서 = [];
customElements.whenDefined('late-el').then(c => 순서.push('late-el 해결 -> ' + c.name));
customElements.whenDefined('never-el').then(c => 순서.push('never-el 해결 -> ' + c.name));
순서.push('(동기 코드가 여기까지 왔다)');
setTimeout(async () => {
  await 0; await 0;
  순서.push('(마이크로태스크가 다 돈 뒤 — 여기까지가 late-el 몫이다)');
  customElements.define('never-el', class NeverEl extends HTMLElement {});
  await 0; await 0;
  O.push('  ' + 순서.join('\n  '));
  O.push('  never-el 을 define 한 뒤 matches(":defined") = ' + $('영영').matches(':defined')
       + ' · constructor.name = ' + $('영영').constructor.name);
  O.push('  ★ whenDefined 는 이미 정의됐으면 곧바로, 아니면 define 될 때 풀린다 — 기다리는 쪽 코드가 같아진다.');
  document.body.appendChild(Object.assign(document.createElement('script'),
    {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
}, 0);
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-upgrade.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,10p'
문서에 없는 요소는 define 해도 업그레이드되지 않는다
  define 전 constructor.name = HTMLElement
  define 직후 로그 = [] · constructor.name = HTMLElement
  ★ 「문서 안의 요소」만 자동으로 업그레이드된다 — 떼어 놓은 트리는 그대로다.

직접 재촉하는 두 길
  customElements.upgrade(밖) 뒤 로그 = ["constructor","attrChanged 라벨 null->\"ㄱ\""]
    constructor.name = Late · connected 는 안 불렸다(문서에 없으니까)
  그 요소를 문서에 붙이면 로그 = ["connected"]
  upgrade() 없이 그냥 붙이면 로그 = ["constructor","attrChanged 라벨 null->\"ㄴ\"","connected"]  <- 붙이는 순간 업그레이드된다
(exit 0)
```

- ★★ **`define` 은 「문서 안의 요소」만 훑는다.** 문서에 안 붙인 `<div>` 안의 요소는 로그가 `[]` 이고 `constructor.name` 이 그대로 `HTMLElement` 다.
- **`customElements.upgrade(노드)` 가 그 부분 트리를 지금 업그레이드한다** — `constructor` 와 `attributeChangedCallback` 이 나고 **`connectedCallback` 은 안 난다**(문서에 없으니까).
- **그 요소를 문서에 붙이면 그제야 `connectedCallback`** 이 난다.
- **`upgrade()` 없이 그냥 붙여도 된다** — 붙이는 순간 셋이 한꺼번에 난다.
- ★ **그래서 `upgrade()` 가 필요한 자리는 좁다** — 「문서에 붙이기 전에 인스턴스의 메서드를 써야 할 때」뿐이다.

```text
   업그레이드의 세 경로

   ① define 이 온다        문서 안의 요소 전부       ctor + attrChanged + connected
   ② upgrade(노드)         그 부분 트리만            ctor + attrChanged   (connected 는 없다)
   ③ 문서에 붙인다          붙는 그 노드              ctor + attrChanged + connected

   ★ ② 만 connected 가 빠진다 — '연결' 은 문서에 있어야 성립하기 때문이다
```

### (5) `observedAttributes` 는 `define` 때 한 번만 읽힌다

**언제 쓰나** — 감시할 속성 목록을 동적으로 만들고 싶을 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-upgrade.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,15p'
static observedAttributes 는 언제 읽히나
  define 직후 읽힌 횟수 = 1
  요소를 만들고 속성을 세 번 바꾼 뒤 읽힌 횟수 = 1 · 로그 = ["attrChanged 보는것","attrChanged 보는것"]
  ★ define 시점에 한 번만 읽는다 — 나중에 목록을 바꿔도 소용없다.
(exit 0)
```

- **`define` 직후 읽힌 횟수가 1** 이고, **요소를 만들고 속성을 세 번 바꾼 뒤에도 1** 이다.
- ★★ **한 번만 읽는다.** 그래서 **나중에 목록을 바꿔도 소용없다.** `static get` 으로 써 놓으면 동적일 것 같은데 **실제로는 `define` 시점의 값이 굳는다.**
- **목록에 없는 속성은 콜백을 안 낸다** — `안보는것` 을 바꿨는데 로그가 두 줄뿐이다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-upgrade.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '17,25p'
whenDefined 와 :defined
  이미 정의된 것: customElements.whenDefined("late-el") 은 Promise 이고 값은 아래에서 확인한다
  never-el 의 matches(":defined") = false · constructor.name = HTMLElement
  (동기 코드가 여기까지 왔다)
  late-el 해결 -> Late
  (마이크로태스크가 다 돈 뒤 — 여기까지가 late-el 몫이다)
  never-el 해결 -> NeverEl
  never-el 을 define 한 뒤 matches(":defined") = true · constructor.name = NeverEl
  ★ whenDefined 는 이미 정의됐으면 곧바로, 아니면 define 될 때 풀린다 — 기다리는 쪽 코드가 같아진다.
(exit 0)
```

- **`whenDefined` 는 이미 정의됐으면 곧바로, 아니면 `define` 될 때 풀린다** — 기다리는 쪽 코드가 **두 경우에 같아진다.**
- **`:defined` 와 `constructor.name` 이 함께 바뀐다** — 「업그레이드됐나」를 CSS 로도(`:defined`) JS 로도 물을 수 있다.
- ★ **`:defined` 로 「아직 안 된 것」을 숨기는 관용구**가 여기서 나온다 — `my-el:not(:defined) { visibility: hidden }`. **이 문서는 그 CSS 를 던지지 않았다.**

```text
   whenDefined 가 풀리는 두 시점

   이미 정의됨    whenDefined('late-el')  ---> 곧바로 (마이크로태스크 한 번 뒤)
   아직 아님      whenDefined('never-el') ---> define('never-el') 이 올 때

   기다리는 쪽 코드
   await customElements.whenDefined('my-el');   <- 두 경우에 한 글자도 같다
   el.내메서드();

   ★ '언제 올지 모른다' 를 호출 쪽이 안 다뤄도 되게 만드는 것이 이 API 의 값이다
```

```text
   '살아났나' 를 묻는 세 창구

   el.matches(':defined')          그 요소가 업그레이드됐나
   customElements.get('my-el')     그 이름이 등록됐나          (요소가 없어도 답한다)
   el.constructor.name             어느 클래스를 입고 있나

   ★ 셋이 서로 다른 것을 묻는다. 내장 요소는 등록 없이도 ':defined' 다
```

### (6) ★ 창 ⑤ — 생성자 규칙을 어기면 예외가 「안 온다」

**언제 쓰나** — 「생성자에서 속성을 붙이면 안 된다」를 실제로 어겨 볼 때.

**던진 것** — 아래 블록 둘도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-13-ctor.html -->
<!doctype html>
<meta charset="utf-8">
<title>13-ctor</title>
<div id="자리"></div>
<script>
const O = [];
const $ = id => document.getElementById(id);
const 잡기 = fn => { try { return { 예외: null, 값: fn() }; } catch (e) { return { 예외: e.name + ' 「' + e.message + '」', 값: null }; } };
const 한줄 = (라벨, r, 더) => O.push('  ' + 라벨 + (r.예외 === null ? '예외 없음' : r.예외) + (더 ? ' · ' + 더(r.값) : ''));

class 속성붙임 extends HTMLElement { constructor() { super(); this.setAttribute('만든속성', '값'); } }
class 자식만듦 extends HTMLElement { constructor() { super(); this.appendChild(document.createElement('b')); } }
class 슈퍼없음 extends HTMLElement { constructor() { } }
class 일부러던짐 extends HTMLElement { constructor() { super(); throw new Error('생성자가 일부러 터진다'); } }
class 착한것 extends HTMLElement { constructor() { super(); this.멤버 = 1; } }
customElements.define('bad-attr', 속성붙임);
customElements.define('bad-child', 자식만듦);
customElements.define('no-super', 슈퍼없음);
customElements.define('bad-throw', 일부러던짐);
customElements.define('ok-el', 착한것);

O.push('생성자 규칙을 어기고 createElement 로 만들면');
const 정체 = v => (v === null ? 'null' : v.constructor.name + ' · tagName=' + v.tagName);
한줄('속성을 붙이면         = ', 잡기(() => document.createElement('bad-attr')), 정체);
한줄('자식을 만들면         = ', 잡기(() => document.createElement('bad-child')), 정체);
한줄('super() 를 안 부르면  = ', 잡기(() => document.createElement('no-super')), 정체);
한줄('생성자가 던지면       = ', 잡기(() => document.createElement('bad-throw')), 정체);
한줄('규칙을 지키면         = ', 잡기(() => document.createElement('ok-el')), 정체);
O.push('  ★ 호출한 쪽에는 예외가 안 온다. 돌아온 것이 HTMLUnknownElement 로 바뀔 뿐이다.');
O.push('  ★ 예외 전문은 콘솔에만 남는다 — 아래 콘솔 블록이 그 자리다.');
O.push('');

O.push('그 요소를 문서에 넣으면 어떻게 되나');
const 망가진 = document.createElement('bad-attr');
$('자리').appendChild(망가진);
O.push('  constructor.name = ' + 망가진.constructor.name
     + ' · matches(":defined") = ' + 망가진.matches(':defined')
     + ' · isConnected = ' + 망가진.isConnected);
O.push('  ★ 「실패 상태」로 굳는다 — 나중에 upgrade() 를 불러도 안 살아난다.');
const 전 = 망가진.constructor.name;
customElements.upgrade(망가진);
O.push('  customElements.upgrade(망가진) 뒤 constructor.name = ' + 전 + ' -> ' + 망가진.constructor.name);
O.push('');

O.push('new 로 직접 부르면 — 검사가 없다');
const a = new 속성붙임(), b = new 자식만듦();
O.push('  new 속성붙임()  tagName=' + a.tagName + ' 속성수=' + a.attributes.length + ' · 예외 없음');
O.push('  new 자식만듦()  tagName=' + b.tagName + ' 자식수=' + b.childNodes.length + ' · 예외 없음');
한줄('new 슈퍼없음()  = ', 잡기(() => new 슈퍼없음()));
O.push('  ★ 「생성자에서 하면 안 되는 일」을 강제하는 것은 생성자가 아니라 createElement 쪽이다.');
O.push('');

O.push('파서·innerHTML 로 만들면 — 검사가 아예 없다');
const d = document.createElement('div');
d.innerHTML = '<bad-attr></bad-attr><bad-child></bad-child>';
document.body.appendChild(d);
O.push('  bad-attr  = ' + d.children[0].constructor.name + ' · 속성수=' + d.children[0].attributes.length);
O.push('  bad-child = ' + d.children[1].constructor.name + ' · 자식수=' + d.children[1].childNodes.length);
O.push('  ★ 업그레이드 경로에는 「속성·자식을 만들면 안 된다」 검사가 없다 — 같은 클래스가 길에 따라 다르게 산다.');
O.push('  ★ 그래서 규칙은 「어기면 터진다」가 아니라 「어기면 어떤 길에서는 조용히 죽는다」로 외운다.');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-ctor.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
생성자 규칙을 어기고 createElement 로 만들면
  속성을 붙이면         = 예외 없음 · HTMLUnknownElement · tagName=BAD-ATTR
  자식을 만들면         = 예외 없음 · HTMLUnknownElement · tagName=BAD-CHILD
  super() 를 안 부르면  = 예외 없음 · HTMLUnknownElement · tagName=NO-SUPER
  생성자가 던지면       = 예외 없음 · HTMLUnknownElement · tagName=BAD-THROW
  규칙을 지키면         = 예외 없음 · 착한것 · tagName=OK-EL
  ★ 호출한 쪽에는 예외가 안 온다. 돌아온 것이 HTMLUnknownElement 로 바뀔 뿐이다.
  ★ 예외 전문은 콘솔에만 남는다 — 아래 콘솔 블록이 그 자리다.
(exit 0)
```

- ★★★ **호출한 쪽에는 예외가 안 온다.** 네 가지를 전부 어겼는데 `try/catch` 가 한 번도 안 걸렸다.
- ★★★ **대신 돌아온 것이 `HTMLUnknownElement` 로 바뀐다.** 태그 이름은 `BAD-ATTR` 그대로다 — **겉은 멀쩡하고 알맹이만 없다.**
- ★ **이것이 이 주제의 제5의 상태다** — 요소가 만들어지고, 문서에 붙고, 태그 이름도 맞다. **세 창이 전부 정상인데 그 요소는 죽어 있다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-ctor.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,13p'
그 요소를 문서에 넣으면 어떻게 되나
  constructor.name = HTMLUnknownElement · matches(":defined") = false · isConnected = true
  ★ 「실패 상태」로 굳는다 — 나중에 upgrade() 를 불러도 안 살아난다.
  customElements.upgrade(망가진) 뒤 constructor.name = HTMLUnknownElement -> HTMLUnknownElement
(exit 0)
```

- **「실패 상태」로 굳는다** — `matches(':defined')` 가 `false` 이고 **나중에 `upgrade()` 를 불러도 안 살아난다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --enable-logging=stderr --dump-dom wa12b-13-ctor.html 2>&1 >/dev/null | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sed 's#, source: file://[^ ]*/# · #'
"Uncaught NotSupportedError: Failed to execute 'createElement' on 'Document': The result must not have attributes" · wa12b-13-ctor.html (24)
"Uncaught NotSupportedError: Failed to execute 'createElement' on 'Document': The result must not have children" · wa12b-13-ctor.html (25)
"Uncaught ReferenceError: Must call super constructor in derived class before accessing 'this' or returning from derived constructor" · wa12b-13-ctor.html (13)
"Uncaught Error: 생성자가 일부러 터진다" · wa12b-13-ctor.html (14)
"Uncaught NotSupportedError: Failed to execute 'createElement' on 'Document': The result must not have attributes" · wa12b-13-ctor.html (34)
(exit 0)
```

- ★★★ **예외 전문은 콘솔에만 있다.** `The result must not have attributes` · `The result must not have children` 가 그 문장이다. **명세가 「생성자가 돌고 난 결과에 속성이나 자식이 있으면 안 된다」고 정해 두었고, 어기면 그 예외를 「보고」하고 실패 상태의 요소를 돌려준다.**
- ★★ **`--enable-logging=stderr` 없이는 이 주제의 핵심이 통째로 안 보인다.** 창 ⑤ 를 세운 이유가 이것이다.
- ★ **콘솔 줄 수를 세는 근거로 쓰지 마라** — Chrome 이 같은 자리를 합친다(15번 주제의 실측이 그렇다).

```text
   세 창이 전부 정상인데 그 요소는 죽어 있다

   창 ①  --dump-dom        <bad-attr 만든속성="값"></bad-attr>   멀쩡해 보인다
   창 ②  tagName            "BAD-ATTR"                           맞다
   창 ②  isConnected        true                                 문서에 있다
   창 ②  matches(':defined') false                               ★ 여기만 다르다
   창 ⑤  콘솔               NotSupportedError 로 막혔다는 말이 여기에만 있다

   ★ 제5의 상태 — 값이 틀린 것이 아니라 '무엇을 기준으로 본 값이냐' 가 다르다
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-ctor.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '15,19p'
new 로 직접 부르면 — 검사가 없다
  new 속성붙임()  tagName=BAD-ATTR 속성수=1 · 예외 없음
  new 자식만듦()  tagName=BAD-CHILD 자식수=1 · 예외 없음
  new 슈퍼없음()  = ReferenceError 「Must call super constructor in derived class before accessing 'this' or returning from derived constructor」
  ★ 「생성자에서 하면 안 되는 일」을 강제하는 것은 생성자가 아니라 createElement 쪽이다.
(exit 0)
```

- ★★ **`new` 로 직접 부르면 검사가 아예 없다.** 속성도 자식도 그대로 붙는다. **강제하는 것은 생성자가 아니라 `createElement` 쪽**이다.
- **`super()` 를 안 부른 것만 `ReferenceError`** 다 — 그것은 자바스크립트 자체의 규칙이라 어디서든 터진다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-ctor.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '21,25p'
파서·innerHTML 로 만들면 — 검사가 아예 없다
  bad-attr  = 속성붙임 · 속성수=1
  bad-child = 자식만듦 · 자식수=1
  ★ 업그레이드 경로에는 「속성·자식을 만들면 안 된다」 검사가 없다 — 같은 클래스가 길에 따라 다르게 산다.
  ★ 그래서 규칙은 「어기면 터진다」가 아니라 「어기면 어떤 길에서는 조용히 죽는다」로 외운다.
(exit 0)
```

- ★★★ **업그레이드 경로에는 그 검사가 아예 없다.** `innerHTML` 로 파싱해 만든 요소는 **속성도 자식도 달린 채로 멀쩡히 업그레이드됐다.**
- ★★ **그래서 규칙을 「어기면 터진다」로 외우면 틀린다.** 정확한 문장은 **「어기면 `createElement` 경로에서만, 그것도 조용히 죽는다」** 이다. 파서로 만든 페이지에서는 멀쩡히 돌던 컴포넌트가 **스크립트로 만드는 순간 죽는다.**

```text
   같은 클래스가 길에 따라 다르게 산다

   document.createElement('bad-attr')   -> HTMLUnknownElement   콘솔에만 예외
   new 속성붙임()                        -> BAD-ATTR (속성 1개)   검사 없음
   innerHTML 로 파싱 + 업그레이드        -> 속성붙임 (속성 1개)    검사 없음

   ★ '규칙' 이 강제되는 자리는 셋 중 하나뿐이고, 그 하나가 조용하다
```

### (7) `disconnectedCallback` 은 언제 오고 언제 안 오나

**언제 쓰나** — 리스너·타이머를 정리하는 자리를 정할 때.

**던진 것** — 아래 블록 둘도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-13-life.html -->
<!doctype html>
<meta charset="utf-8">
<title>13-life</title>
<div id="가"><m-el id="옮길것"></m-el></div>
<div id="나"></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const 로그 = [];
const 비우기 = () => { const v = JSON.stringify(로그); 로그.length = 0; return v; };
const 행 = (라벨, 값, 뒷말) => O.push(padw(라벨, 40) + padw(값, 40) + (뒷말 || ''));
const $ = id => document.getElementById(id);

class M extends HTMLElement {
  connectedCallback() { 로그.push('connected'); }
  disconnectedCallback() { 로그.push('disconnected'); }
  adoptedCallback() { 로그.push('adopted'); }
}
class Mv extends HTMLElement {
  connectedCallback() { 로그.push('connected'); }
  disconnectedCallback() { 로그.push('disconnected'); }
  connectedMoveCallback() { 로그.push('connectedMove'); }
}
customElements.define('m-el', M);
customElements.define('mv-el', Mv);
const e = $('옮길것'), 가 = $('가'), 나 = $('나');

O.push('disconnectedCallback 은 언제 오고 언제 안 오나');
O.push(padw('무엇을 했나', 40) + padw("로그", 40) + '뜻');
비우기();
나.appendChild(e);                    행('다른 부모로 appendChild', 비우기(), '옮기기는 뗐다 붙이기다');
가.appendChild(e);                    행('원래 부모로 다시 appendChild', 비우기(), '');
가.appendChild(e);                    행('같은 부모에 또 appendChild', 비우기(), '제자리인데도 한 쌍이 난다');
가.style.display = 'none';            행('display:none 으로 숨기면', 비우기(), 'isConnected=' + e.isConnected);
가.style.display = '';
e.remove();                           행('remove()', 비우기(), '');
가.appendChild(e); 비우기();
가.innerHTML = '';                    행('부모의 innerHTML = ""', 비우기(), '');
const 겉 = document.createElement('div');
비우기();
겉.appendChild(document.createElement('m-el'));
행('문서 밖 div 에 붙이면', 비우기(), 'connected 가 안 온다');
겉.remove();                          행('그 div 를 버리면', 비우기(), 'disconnected 도 안 온다');
const h = document.createElement('div');
document.body.appendChild(h);
const r = h.attachShadow({ mode: 'open' });
비우기();
r.innerHTML = '<m-el id="그림자안"></m-el>';
행('그림자 트리 안에 만들면', 비우기(), '그림자도 「연결」이다');
h.remove();                           행('호스트를 떼면', 비우기(), '');
const 딴문서 = document.implementation.createHTMLDocument('딴것');
document.body.appendChild(h); 비우기();
딴문서.body.appendChild(h);
행('다른 문서로 옮기면', 비우기(), 'adopted 가 가운데 낀다');
O.push('');

O.push('moveBefore — 떼지 않고 옮기는 새 표면');
O.push('  Element.prototype.moveBefore 가 있나 = ' + (typeof Element.prototype.moveBefore));
const m1 = document.createElement('m-el'), m2 = document.createElement('mv-el');
가.appendChild(m1); 나.appendChild(m2); 비우기();
가.moveBefore(m2, null);
행('connectedMoveCallback 이 있는 요소', 비우기(), 'disconnected 가 안 난다');
비우기();
나.moveBefore(m1, null);
행('connectedMoveCallback 이 없는 요소', 비우기(), '옛 코드를 위해 한 쌍을 낸다');
O.push('');
O.push('★ 「안 불리는 자리」 정리');
O.push('  1. 문서(또는 그림자)에 붙은 적이 없으면 connected 도 disconnected 도 안 온다.');
O.push('  2. display:none·visibility:hidden 은 아무 콜백도 안 낸다 — 연결은 그대로다.');
O.push('  3. connectedMoveCallback 을 정의하면 moveBefore 가 disconnected 를 안 낸다.');
O.push('  4. 페이지를 떠날 때(탭 닫기·이동)는 안 온다 — 이 문서의 도구로는 그 순간을 못 본다(못 잰 것).');
O.push('  5. 가비지 컬렉션은 콜백을 내지 않는다 — 「소멸자」가 아니다.');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,13p'
disconnectedCallback 은 언제 오고 언제 안 오나
무엇을 했나                             로그                                    뜻
다른 부모로 appendChild                 ["disconnected","connected"]            옮기기는 뗐다 붙이기다
원래 부모로 다시 appendChild            ["disconnected","connected"]            
같은 부모에 또 appendChild              ["disconnected","connected"]            제자리인데도 한 쌍이 난다
display:none 으로 숨기면                []                                      isConnected=true
remove()                                ["disconnected"]                        
부모의 innerHTML = ""                   ["disconnected"]                        
문서 밖 div 에 붙이면                   []                                      connected 가 안 온다
그 div 를 버리면                        []                                      disconnected 도 안 온다
그림자 트리 안에 만들면                 ["connected"]                           그림자도 「연결」이다
호스트를 떼면                           ["disconnected"]                        
다른 문서로 옮기면                      ["disconnected","adopted","connected"]  adopted 가 가운데 낀다
(exit 0)
```

- ★★ **옮기기는 「뗐다 붙이기」다.** 다른 부모로 `appendChild` 하면 **`disconnected` 와 `connected` 가 한 쌍**으로 난다. **같은 부모에 다시 붙여도** 난다 — 제자리인데도 한 쌍이다.
- **`display: none` 은 아무 콜백도 안 낸다** — 「연결」은 **트리에 있나**이지 **보이나**가 아니다.
- **문서 밖 `<div>` 에 붙이면 `connected` 가 안 온다.** 그 `<div>` 를 버려도 `disconnected` 가 안 온다 — **붙은 적이 없으면 뗄 것도 없다.**
- ★ **그림자 트리 안도 「연결」이다** — `attachShadow` 한 루트에 넣으면 `connected` 가 나고, 호스트를 떼면 `disconnected` 가 난다([12번 주제](../12-shadow-dom/2-summary.md)의 `isConnected` 가 그 짝이다).
- **다른 문서로 옮기면 `disconnected` → `adopted` → `connected`** 다 — `adoptedCallback` 이 가운데 낀다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '15,18p'
moveBefore — 떼지 않고 옮기는 새 표면
  Element.prototype.moveBefore 가 있나 = function
connectedMoveCallback 이 있는 요소      ["connectedMove"]                       disconnected 가 안 난다
connectedMoveCallback 이 없는 요소      ["disconnected","connected"]            옛 코드를 위해 한 쌍을 낸다
(exit 0)
```

- ★★ **`moveBefore()` 는 떼지 않고 옮긴다** — 그런데 **`connectedMoveCallback` 을 정의한 요소만** 그 혜택을 본다. 정의하지 않은 요소에는 **옛 코드를 위해 `disconnected`/`connected` 한 쌍을 그대로 낸다.**
- ★ **새 표면이다.** 이 문서는 **Chrome 151 에서 이렇게 된다**까지만 말한다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '20,25p'
★ 「안 불리는 자리」 정리
  1. 문서(또는 그림자)에 붙은 적이 없으면 connected 도 disconnected 도 안 온다.
  2. display:none·visibility:hidden 은 아무 콜백도 안 낸다 — 연결은 그대로다.
  3. connectedMoveCallback 을 정의하면 moveBefore 가 disconnected 를 안 낸다.
  4. 페이지를 떠날 때(탭 닫기·이동)는 안 온다 — 이 문서의 도구로는 그 순간을 못 본다(못 잰 것).
  5. 가비지 컬렉션은 콜백을 내지 않는다 — 「소멸자」가 아니다.
(exit 0)
```

- ★★★ **`disconnectedCallback` 은 소멸자가 아니다.** 페이지를 떠날 때 안 오고, 가비지 컬렉션도 콜백을 안 낸다. **「정리」를 거기에만 걸면 탭을 닫는 순간 아무 일도 안 일어난다.**
- ★ **페이지를 떠날 때의 관측은 「못 잰 것」이다** — 로그를 뱉을 문서가 이미 없다. 명세가 「안 낸다」로 정해 두었고, 이 문서는 **그 사실을 실행으로 확인하지 못했다.**

```text
   disconnectedCallback 이 오는가 — 전수

   remove()                      -> 온다
   부모의 innerHTML = ""          -> 온다
   다른 부모로 옮기기              -> 온다 (connected 와 한 쌍)
   같은 부모에 다시 붙이기          -> 온다 (제자리인데도)
   다른 문서로 옮기기              -> 온다 (adopted 가 가운데)
   호스트를 떼기 (그림자 안)        -> 온다
   display: none                 -> 안 온다
   붙은 적이 없는 요소를 버리기     -> 안 온다
   moveBefore + connectedMove    -> 안 온다 (그쪽이 대신 온다)
   페이지를 떠나기                 -> 안 온다 (이 문서는 못 쟀다)
   가비지 컬렉션                   -> 안 온다 (소멸자가 아니다)
```

### (8) 이름 규칙 — 하이픈 하나가 전부가 아니다

**언제 쓰나** — 이름을 지을 때. **여기서 `SyntaxError` 로 막힌다.**

**던진 것** — 아래 (9)·(10)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-13-name.html -->
<!doctype html>
<meta charset="utf-8">
<title>13-name</title>
<div id="자리"></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const 잡기 = fn => { try { fn(); return '통과'; } catch (e) { return e.name + ' 「' + e.message + '」'; } };

O.push('이름 규칙 — 무엇이 valid custom element name 인가');
O.push(padw('던진 이름', 22) + '결과');
for (const n of ['my-el', 'x-', 'a-b-c', 'my-EL', 'My-El', 'myel', '-el', '1-el', 'font-face',
                 'annotation-xml', 'my-el2', 'my-엘']) {
  O.push(padw(JSON.stringify(n), 22) + 잡기(() => customElements.define(n, class extends HTMLElement {})));
}
O.push('');
O.push('  ★ 하이픈 하나가 전부가 아니다 — 소문자로 시작해야 하고 대문자가 섞이면 안 되며 예약된 이름이 있다.');
O.push('  ★ 예약어 목록(annotation-xml·font-face 등)은 SVG·MathML 이 이미 쓰는 이름이다.');
O.push('');

O.push('같은 이름·같은 클래스를 두 번 등록하면');
class 한번만 extends HTMLElement {}
O.push('  처음 등록          = ' + 잡기(() => customElements.define('once-el', 한번만)));
O.push('  같은 이름을 또     = ' + 잡기(() => customElements.define('once-el', class extends HTMLElement {})));
O.push('  같은 클래스를 다른 이름에 = ' + 잡기(() => customElements.define('twice-el', 한번만)));
O.push('  ★ 이름도 클래스도 한 번씩만 쓸 수 있다. 되돌리는 API 는 없다.');
O.push('');

O.push('클래스가 아닌 것을 넘기면');
O.push('  함수 선언          = ' + 잡기(() => customElements.define('fn-el', function () {})));
O.push('  화살표 함수        = ' + 잡기(() => customElements.define('arrow-el', () => {})));
O.push('  HTMLElement 를 안 물려받은 클래스 = ' + 잡기(() => customElements.define('plain-el', class {})));
O.push('  객체                = ' + 잡기(() => customElements.define('obj-el', {})));
O.push('  ★ 통과한 둘은 define 이 봐준 것이지 쓸 수 있다는 뜻이 아니다 — 만들 때 드러난다:');
O.push('    document.createElement("plain-el") 의 결과 = ' + document.createElement('plain-el').constructor.name);
O.push('    document.createElement("fn-el")    의 결과 = ' + document.createElement('fn-el').constructor.name);
O.push('    (콘솔에 예외 전문이 남는다 — 13-ctor 와 같은 모양이다)');
O.push('');
O.push('  ★ 이름에 아스키가 아닌 글자를 써도 된다 — 다만 첫 글자는 아스키 소문자여야 한다:');
O.push('    "my-엘" = ' + 잡기(() => customElements.define('my-엘2', class extends HTMLElement {}))
     + ' · "엘-my" = ' + 잡기(() => customElements.define('엘-my', class extends HTMLElement {})));
O.push('');

O.push('내장 요소 확장(customized built-in) 은 이 판에서 되나');
class 내단추 extends HTMLButtonElement {}
O.push('  define("my-btn", 내단추, {extends: "button"}) = ' + 잡기(() => customElements.define('my-btn', 내단추, { extends: 'button' })));
const b = document.createElement('button', { is: 'my-btn' });
document.getElementById('자리').appendChild(b);
O.push('  createElement("button", {is:"my-btn"}) 의 constructor.name = ' + b.constructor.name
     + ' · outerHTML = ' + b.outerHTML);
O.push('  matches(":defined") = ' + b.matches(':defined'));
O.push('  ★ Chrome 은 된다 — 그런데 이것은 엔진마다 갈리는 표면이라 이 문서가 이식성을 주장하지 않는다.');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-name.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,17p'
이름 규칙 — 무엇이 valid custom element name 인가
던진 이름             결과
"my-el"               통과
"x-"                  통과
"a-b-c"               통과
"my-EL"               SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "my-EL" is not a valid custom element name」
"My-El"               SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "My-El" is not a valid custom element name」
"myel"                SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "myel" is not a valid custom element name」
"-el"                 SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "-el" is not a valid custom element name」
"1-el"                SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "1-el" is not a valid custom element name」
"font-face"           SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "font-face" is not a valid custom element name」
"annotation-xml"      SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "annotation-xml" is not a valid custom element name」
"my-el2"              통과
"my-엘"               통과

  ★ 하이픈 하나가 전부가 아니다 — 소문자로 시작해야 하고 대문자가 섞이면 안 되며 예약된 이름이 있다.
  ★ 예약어 목록(annotation-xml·font-face 등)은 SVG·MathML 이 이미 쓰는 이름이다.
(exit 0)
```

- **통과** — `my-el`·`x-`·`a-b-c`·`my-el2`·`my-엘`.
- **거절** — 대문자가 섞인 것(`my-EL`·`My-El`) · 하이픈이 없는 것(`myel`) · 하이픈으로 시작하는 것(`-el`) · 숫자로 시작하는 것(`1-el`) · **예약된 이름**(`font-face`·`annotation-xml`).
- ★★ **`my-엘` 이 통과한다.** 이름이 아스키로만 돼 있어야 한다는 규칙은 없다 — **첫 글자가 아스키 소문자여야** 하고 **대문자가 없어야** 할 뿐이다. `엘-my` 는 첫 글자 때문에 막힌다(아래 (10)에 그 줄이 있다).
- ★ **예약어는 SVG·MathML 이 이미 쓰는 이름**이다. `font-face`·`annotation-xml`·`missing-glyph` 등 일곱 개가 명세에 나열돼 있다.
- **거절은 전부 `SyntaxError`** 다 — 이름 문제와 등록 문제가 **예외 이름으로 갈린다**(등록 문제는 (9)).

```text
   예외 이름 하나가 원인을 가른다

   SyntaxError        이름이 규칙에 안 맞는다        -> 이름을 고친다
   NotSupportedError  이미 쓴 이름이거나 클래스다     -> 중복 등록을 막는다
   TypeError          생성자가 아닌 것을 넘겼다       -> 넘긴 값을 고친다

   ★ 셋을 '정의가 안 된다' 로 뭉뚱그리면 고칠 자리를 못 찾는다
```

```text
   valid custom element name 의 조건

   [a-z] 로 시작한다        -> '-el' · '1-el' · '엘-my' 가 막힌다
   하이픈을 하나 이상 담는다  -> 'myel' 이 막힌다
   아스키 대문자가 없다      -> 'my-EL' · 'My-El' 이 막힌다
   예약어가 아니다           -> 'font-face' · 'annotation-xml' 이 막힌다

   ★ 나머지 글자는 아스키가 아니어도 된다 — 'my-엘' 이 통과한다
```

### (9) 두 번 등록하면 — 되돌리는 API 가 없다

**언제 쓰나** — 핫 리로드·테스트에서 같은 모듈을 두 번 읽을 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-name.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '19,23p'
같은 이름·같은 클래스를 두 번 등록하면
  처음 등록          = 통과
  같은 이름을 또     = NotSupportedError 「Failed to execute 'define' on 'CustomElementRegistry': the name "once-el" has already been used with this registry」
  같은 클래스를 다른 이름에 = NotSupportedError 「Failed to execute 'define' on 'CustomElementRegistry': this constructor has already been used with this registry」
  ★ 이름도 클래스도 한 번씩만 쓸 수 있다. 되돌리는 API 는 없다.
(exit 0)
```

- **같은 이름을 두 번** → `NotSupportedError`. **같은 클래스를 다른 이름에** 써도 `NotSupportedError`.
- ★★ **이름도 클래스도 한 번씩만 쓸 수 있고, 되돌리는 API 가 없다.** `customElements.undefine()` 같은 것은 없다.
- ★ **그래서 핫 리로드에서 깨진다.** 실무 처방은 **`customElements.get(이름)` 으로 먼저 확인하고 이미 있으면 건너뛰는 것**이다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-name.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '25,36p'
클래스가 아닌 것을 넘기면
  함수 선언          = 통과
  화살표 함수        = TypeError 「Failed to execute 'define' on 'CustomElementRegistry': constructor argument is not a constructor」
  HTMLElement 를 안 물려받은 클래스 = 통과
  객체                = TypeError 「Failed to execute 'define' on 'CustomElementRegistry': parameter 2 is not of type 'Function'.」
  ★ 통과한 둘은 define 이 봐준 것이지 쓸 수 있다는 뜻이 아니다 — 만들 때 드러난다:
    document.createElement("plain-el") 의 결과 = HTMLUnknownElement
    document.createElement("fn-el")    의 결과 = HTMLUnknownElement
    (콘솔에 예외 전문이 남는다 — 13-ctor 와 같은 모양이다)

  ★ 이름에 아스키가 아닌 글자를 써도 된다 — 다만 첫 글자는 아스키 소문자여야 한다:
    "my-엘" = 통과 · "엘-my" = SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "엘-my" is not a valid custom element name」
(exit 0)
```

- **화살표 함수와 객체는 `TypeError`** 로 막힌다 — 생성자가 아니기 때문이다.
- ★★ **그런데 평범한 `function` 선언과 `HTMLElement` 를 안 물려받은 `class` 는 통과한다.** `define` 은 「생성자인가」만 보고 「`HTMLElement` 의 자손인가」는 안 본다.
- ★ **통과는 「쓸 수 있다」가 아니다** — 만들어 보면 **`HTMLUnknownElement`** 가 돌아오고 예외 전문은 **콘솔에만** 남는다((6)과 같은 모양이다).
- **「통과도 출력이다」** — 통과한 문이 무엇을 만들었는지 다시 읽어야 한다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-name.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '38,42p'
내장 요소 확장(customized built-in) 은 이 판에서 되나
  define("my-btn", 내단추, {extends: "button"}) = 통과
  createElement("button", {is:"my-btn"}) 의 constructor.name = 내단추 · outerHTML = <button is="my-btn"></button>
  matches(":defined") = true
  ★ Chrome 은 된다 — 그런데 이것은 엔진마다 갈리는 표면이라 이 문서가 이식성을 주장하지 않는다.
(exit 0)
```

- **내장 요소 확장(`is=`)은 이 판에서 된다** — `define(..., { extends: 'button' })` 이 통과하고 `createElement('button', { is: 'my-btn' })` 이 서브클래스를 준다.
- ★ **이것은 엔진마다 갈리는 표면이다.** 이 문서는 **Chrome 151 에서 이렇게 된다**까지만 말하고 이식성을 주장하지 않는다.
- **`outerHTML` 에 `is="my-btn"` 이 남는다** — 직렬화하고 다시 파싱해도 같은 것이 선다.

```text
   CustomElementRegistry 는 두 방향 장부다

   이름 -> 클래스       customElements.get('my-card')   -> MyCard
   클래스 -> 이름       customElements.getName(MyCard)  -> 'my-card'

   두 칸 다 한 번 쓰면 못 지운다:
   define('my-card', 다른것)  -> NotSupportedError  (이름 칸이 찼다)
   define('other',  MyCard)  -> NotSupportedError  (클래스 칸이 찼다)

   ★ undefine() 은 없다. 핫 리로드가 여기서 깨진다
```

```text
   내장 요소를 확장하는 두 길

   자율(autonomous)          <my-btn>            안에 <button> 을 넣는다
                             HTMLElement 를 확장   어느 엔진에서나 된다

   내장 확장(customized)     <button is="my-btn"> 키보드·폼 동작을 공짜로 받는다
                             HTMLButtonElement 를 확장   ★ 엔진이 갈린다

   ★ 이 문서는 Chrome 151 에서 뒤엣것이 '된다' 까지만 말한다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
// wa12b-13-form.js
// 정의한다
class MyEl extends HTMLElement {
  static observedAttributes = ['라벨'];        // static getter 로 써도 같다
  constructor() { super(); /* 여기서는 속성도 자식도 만들지 않는다 */ }
  connectedCallback() { }
  disconnectedCallback() { }
  adoptedCallback() { }
  connectedMoveCallback() { }                  // 있으면 moveBefore 가 이쪽만 부른다
  attributeChangedCallback(이름, 옛값, 새값) { }
}
customElements.define('my-el', MyEl);
customElements.define('my-btn', 내단추, { extends: 'button' });   // 내장 요소 확장

// 묻는다
customElements.get('my-el')        // 클래스 또는 undefined
customElements.getName(MyEl)       // 이름 또는 null
customElements.whenDefined('my-el')  // Promise<클래스>
customElements.upgrade(노드)         // 그 부분 트리를 지금 업그레이드한다
el.matches(':defined')

// 만든다
document.createElement('my-el');
document.createElement('button', { is: 'my-btn' });
new MyEl();                        // 검사가 없다 — 권하지 않는다
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
// wa12b-13-bad.js
// 1. 생성자에서 속성을 붙인다 — createElement 가 조용히 HTMLUnknownElement 를 돌려준다
constructor() { super(); this.setAttribute('role', 'button'); }
connectedCallback() { this.setAttribute('role', 'button'); }     // 이것이 맞다

// 2. 생성자에서 자식을 만든다 — 같은 사고다
constructor() { super(); this.innerHTML = '<b>제목</b>'; }
connectedCallback() { if (!this.초기화됨) { this.innerHTML = '<b>제목</b>'; this.초기화됨 = true; } }

// 3. observedAttributes 를 나중에 바꾼다 — define 시점에 한 번만 읽는다
MyEl.observedAttributes = ['새로운것'];          // 아무 일도 안 일어난다

// 4. connectedCallback 이 한 번만 불릴 거라 믿는다
connectedCallback() { this.리스너달기(); }       // 옮길 때마다 또 달린다
disconnectedCallback() { this.리스너떼기(); }    // 짝을 맞춘다

// 5. disconnectedCallback 을 소멸자로 쓴다
// 페이지를 떠날 때는 안 불린다. 탭을 닫아도 안 불린다

// 6. define 을 두 번 부른다 — 되돌리는 API 가 없다
customElements.define('my-el', 버전1);
customElements.define('my-el', 버전2);           // NotSupportedError 로 막힌다

// 7. 정의되기 전의 요소를 곧바로 쓴다
document.querySelector('my-el').내메서드();       // 아직 HTMLElement 다
customElements.whenDefined('my-el').then(() => { });   // 이것이 맞다
```

### 어디서 헷갈리나

- **`constructor` 와 `connectedCallback`** — 앞엣것은 **한 번**, 뒤엣것은 **붙을 때마다**다.
- **`observedAttributes` 의 `static`** — 인스턴스 것이 아니라 **클래스 것**이고 **`define` 때 한 번** 읽힌다.
- **`upgrade()` 와 `whenDefined()`** — 앞엣것은 **요소를 지금 살리는 것**, 뒤엣것은 **정의를 기다리는 것**이다.
- **`:defined` 와 `customElements.get()`** — 앞엣것은 **그 요소가 살아났나**, 뒤엣것은 **그 이름이 등록됐나**.
- **`disconnectedCallback` 과 소멸자** — 이름이 닮았는데 **페이지를 떠날 때는 안 온다.**

## 어디서 틀리나

```text
   connected / disconnected 는 짝으로 쓴다

   connectedCallback()     { this.ac = new AbortController();
                             addEventListener(..., { signal: this.ac.signal }); }
   disconnectedCallback()  { this.ac.abort(); }

   옮길 때마다 한 쌍이 나므로 두 줄이 자동으로 맞는다.
   ★ 한쪽만 쓰면 옮길 때마다 리스너가 쌓인다 — [목록의 **20번 주제**](../20-listener-lifetime/)가 그 정본이다
```

### 1. 생성자에서 속성이나 자식을 만든다

(6)에서 `createElement` 가 **예외 없이 `HTMLUnknownElement`** 를 돌려줬다. 예외 전문은 **콘솔에만** 있다. 그리고 **파서로 만들면 멀쩡히 돈다** — 그래서 개발 중에는 안 걸리고 나중에 터진다.

### 2. 「어기면 터진다」로 외운다

(6)의 세 경로가 전부 다르다. `new` 도 `innerHTML` 도 검사가 없다.

### 3. `observedAttributes` 를 나중에 바꾼다

(5)에서 읽힌 횟수가 **`define` 직후 1, 그 뒤로도 1** 이었다. 목록은 그때 굳는다.

### 4. `connectedCallback` 이 한 번만 불릴 거라 믿는다

(7)에서 **같은 부모에 다시 붙여도 한 쌍**이 났다. 리스너를 거기서 달면 **옮길 때마다 또 달린다.** `disconnectedCallback` 과 짝을 맞춘다.

### 5. `disconnectedCallback` 을 소멸자로 쓴다

**페이지를 떠날 때 안 온다.** 서버에 보낼 것이 있으면 [목록의 **34번 주제**](../34-send-beacon-and-keepalive/)(`sendBeacon`)와 [목록의 **24번 주제**](../24-document-lifecycle-events/)(`visibilitychange`)를 쓴다.

### 6. 문서 밖 트리가 업그레이드될 줄 안다

(4)에서 로그가 `[]` 였다. `<template>` 의 `content` 안도 마찬가지다.

### 7. 이름에 대문자를 쓴다

(8)에서 `My-El` 이 `SyntaxError` 다. HTML 태그 이름은 소문자로 정규화되므로 **대문자가 들어갈 자리가 없다.**

### 8. 같은 모듈을 두 번 읽는다

(9)에서 `NotSupportedError` 다. **되돌리는 API 가 없으므로** `customElements.get()` 으로 먼저 본다.

### 9. 정의되기 전의 요소에 메서드를 부른다

(1)에서 그때는 **`HTMLElement`** 다. `whenDefined()` 로 기다린다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 콜백 넷의 **순서**(observedAttributes → ctor → attrChanged → connected) | **명세**(HTML — upgrade an element) |
| 업그레이드가 **동기**인 것(`define` 이 돌아오기 전에 끝난다) | **명세** |
| **초기 속성에도 `attributeChangedCallback` 이 오는** 것 | **명세**(업그레이드 경로 한정) |
| **문서 안의 요소만** 자동 업그레이드되는 것 | **명세**(shadow-including descendants of document) |
| `upgrade()` 가 **`connectedCallback` 을 안 내는** 것 | **명세**(연결은 문서에 있어야 성립한다) |
| `observedAttributes` 가 **`define` 때 한 번만** 읽히는 것 | **명세** |
| 생성자 결과에 **속성·자식이 있으면 안 되는** 것과 **그것을 `createElement` 경로에서만 검사**하는 것 | **명세**(create an element for a token vs. upgrade) |
| 실패한 요소가 **`HTMLUnknownElement`** 로 돌아오는 것 | **명세**("failed" custom element state) |
| 이름 규칙(첫 글자·하이픈·대문자·예약어) | **명세**(valid custom element name) |
| 같은 이름·같은 클래스의 **재등록 금지** | **명세** |
| `disconnectedCallback` 이 **페이지 이탈에 안 오는** 것 | **명세.** ★ **이 문서는 실행으로 확인하지 못했다**(못 잰 것) |
| 가비지 컬렉션이 콜백을 **안 내는** 것 | **명세.** ★ **확인하지 못했다** |
| ★ **예외의 「문구」** | **구현.** 이름은 명세, 문구는 구현이다 |
| ★ **콘솔 경고·에러가 합쳐지는 것** | **구현.** 줄 수를 근거로 쓰면 안 된다 |
| ★ **내장 요소 확장(`is=`)** | **명세에는 있는데 엔진이 갈린다.** Chrome 151 의 관찰로만 적었다 |
| ★ **`connectedMoveCallback`·`moveBefore()`·`customElements.getName()`** | **새 표면.** 다른 엔진에서 던지지 않았다 |
| 커스텀 요소의 **비용** | **안 쟀다.** 이 문서는 성능을 주장하지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 초기화를 한 번만 한다 | `constructor` + 플래그 | `connectedCallback` 에 그냥 쓰기(옮길 때마다 또 돈다) |
| DOM 을 만든다 | `connectedCallback` | `constructor`(조용히 죽는다) |
| 속성을 읽어 상태를 세운다 | `attributeChangedCallback` | `constructor`(그 시점에는 속성이 있을 수도 없을 수도 있다) |
| 리스너를 단다 | `connectedCallback` + `disconnectedCallback` 짝 | 한쪽만 쓰기 |
| 정리한다(서버 보고 포함) | [목록의 **24번 주제**](../24-document-lifecycle-events/)·[목록의 **34번 주제**](../34-send-beacon-and-keepalive/) | `disconnectedCallback`(페이지 이탈에 안 온다) |
| 정의를 기다린다 | `customElements.whenDefined()` | `setTimeout` 으로 짐작하기 |
| 떼어 놓은 트리를 살린다 | `customElements.upgrade()` | 문서에 붙였다 떼기 |
| 안 살아난 것을 숨긴다 | `:not(:defined)` CSS | JS 로 폴링하기 |
| 같은 모듈이 두 번 읽힐 수 있다 | `customElements.get()` 으로 먼저 확인 | 그냥 `define`(`NotSupportedError`) |
| 단추를 컴포넌트로 만든다 | 커스텀 요소 + 안에 `<button>` | `<button>` 에 `attachShadow`([12번 주제](../12-shadow-dom/2-summary.md)에서 막힌다) |
| 내장 요소를 확장한다 | **신중하게.** 엔진이 갈린다 | 이식성을 전제하기 |

## 핵심 문장

```text
   한 커스텀 요소의 일생 — 시간선

   파서가 만든다         HTMLElement · ':defined' = false
        |
   define 이 온다        observedAttributes -> ctor -> attrChanged(초기) -> connected
        |
   속성이 바뀐다          attrChanged           (목록에 있는 것만)
        |
   옮긴다                 disconnected + connected   (moveBefore + connectedMove 면 한 번)
        |
   문서를 바꾼다          disconnected + adopted + connected
        |
   뗀다                   disconnected
        |
   페이지를 떠난다        (아무것도 안 온다 — 이 문서는 못 쟀다)
        |
   가비지 컬렉션          (아무것도 안 온다)
```

1. **파서는 `define` 을 기다리지 않는다** — 하이픈이 든 태그를 `HTMLElement` 로 먼저 만들어 둔다.
2. **`define` 한 줄이 순서 넷을 동기로 돌린다** — observedAttributes → ctor → attrChanged(초기 속성) → connected.
3. **초기 속성에 콜백이 오는 것은 업그레이드 경로의 성질**이다. `createElement` 경로에는 초기 속성이 없다.
4. **업그레이드는 문서 안에만 미친다.** `upgrade()` 는 `connectedCallback` 을 안 낸다.
5. **`observedAttributes` 는 `define` 때 한 번 읽히고 굳는다.**
6. **생성자 규칙 위반은 예외가 아니라 `HTMLUnknownElement`** 다. 전문은 **콘솔에만** 있고 **경로에 따라 검사조차 없다.**
7. **`connectedCallback`/`disconnectedCallback` 은 옮길 때마다 한 쌍씩 난다** — 제자리로 붙여도 난다.
8. **`disconnectedCallback` 은 소멸자가 아니다** — 페이지 이탈에도 GC 에도 안 온다.
9. **이름은 아스키 소문자로 시작하고 하이픈을 담고 대문자가 없어야 한다.** 나머지 글자는 아스키가 아니어도 된다.
10. **등록은 되돌릴 수 없다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 13번)
- [12번 주제](../12-shadow-dom/2-summary.md) — ★ **짝이 되는 주제.** 그쪽은 **경계**, 여기는 **수명주기**다. `<button>` 에 `attachShadow` 가 막히는 문제의 실무 해법이 이 주제다
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **10번** — 커스텀 요소 **맛보기**. 「파서가 만든 요소가 `define` 으로 살아난다」까지가 거기고, **수명주기 전부는 여기**다
- [03번 주제](../03-node-creation-insertion-removal/2-summary.md) — **삽입이 이동이라는 것**의 정본. `disconnected`/`connected` 가 한 쌍으로 나는 이유가 거기 있다
- [06번 주제](../06-attribute-vs-property/2-summary.md) — `attributeChangedCallback` 은 **속성(attribute)** 쪽만 본다. 프로퍼티에 써도 안 온다
- [01번 주제](../01-document-and-node-tree/2-summary.md) — 나무를 보는 창 셋
- [목록의 **24번 주제**](../24-document-lifecycle-events/)(문서 수명주기 이벤트) · [목록의 **34번 주제**](../34-send-beacon-and-keepalive/)(`sendBeacon`) — **떠날 때** 무엇을 쓰나. `disconnectedCallback` 의 빈자리를 메운다
- 목록의 **37번 주제**(`MutationObserver`) — 커스텀 요소 없이 「DOM 이 바뀌었다」를 잡는 길
- [목록의 **21번 주제**](../21-custom-events/)(`CustomEvent`) — 컴포넌트가 바깥에 알리는 법
- JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **16번** — `class`·`extends`·`super()` 의 정본. **`super()` 를 안 부르면 나는 `ReferenceError` 는 그쪽 규칙**이다

## 용어 풀이

- **커스텀 요소(custom element)** — 이름에 하이픈이 든, 스크립트가 클래스를 등록해 쓰는 요소.
- **업그레이드(upgrade)** — 이미 만들어진 요소의 **프로토타입을 등록된 클래스로 갈아 끼우고** 콜백을 부르는 절차. **새 노드를 만들지 않는다.**
- **수명주기 콜백(lifecycle callback)** — `constructor`·`connectedCallback`·`disconnectedCallback`·`adoptedCallback`·`attributeChangedCallback`. 여기에 `connectedMoveCallback` 이 새로 붙었다.
- **`observedAttributes`** — 감시할 속성 이름 배열. **`static` 이고 `define` 때 한 번** 읽힌다.
- **실패 상태(failed custom element state)** — 생성자가 규칙을 어겼을 때 요소가 빠지는 상태. `HTMLUnknownElement` 가 되고 **다시 살아나지 않는다.**
- **`:defined`** — 업그레이드가 끝난 요소를 잡는 의사 클래스. 내장 요소는 전부 `:defined` 다.
- **내장 요소 확장(customized built-in)** — `is=` 로 `<button>` 같은 내장 요소를 확장하는 방식. **엔진이 갈린다.**
- **`connectedMoveCallback`** — `moveBefore()` 로 옮길 때 `disconnected`/`connected` 대신 불리는 새 콜백.
- **제5의 상태** — 세 창이 전부 정상인데 결과만 다른 것. 이 주제에서는 **생성자 규칙을 어긴 요소**가 그렇다.
- **못 잰 것** — 도구가 그 순간을 볼 수 없어 확인하지 못한 것. 이 주제에서는 **페이지 이탈 시점**이 그렇다.

## 더 들어가면

- **`ElementInternals`**(`this.attachInternals()`)는 커스텀 요소에 **암묵 역할·상태·폼 참여**를 준다. `formAssociated = true` 와 짝이다. **던지지 않았다.**
- **커스텀 상태(`:state()`)** 는 `internals.states` 로 켜고 CSS 로 잡는다. **던지지 않았다.**
- **스코프드 레지스트리**(`new CustomElementRegistry()` 를 그림자마다)는 「같은 이름을 여러 번」 문제의 근본 해법이다. **던지지 않았다.**
- **`customElements.whenDefined` 의 거절** — 이름이 유효하지 않으면 Promise 가 **거절**된다. 이 문서는 유효한 이름만 던졌다.
- **`<template>` 의 `content` 안**은 다른 문서라 업그레이드 대상이 아니다. 꺼내 붙이는 순간 `adoptedCallback` 이 낄 수 있다 — **이 문서는 그 경로를 따로 찍지 않았다.**
- **접근성** — 커스텀 요소는 기본 역할이 없다. `role` 을 주거나 `ElementInternals` 로 붙여야 한다. **스크린리더가 실제로 어떻게 읽는지는 이 도구로 못 본다.**
