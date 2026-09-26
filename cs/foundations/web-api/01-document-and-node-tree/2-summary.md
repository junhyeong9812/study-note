# web-api/01 — 문서와 노드 트리: `Node`·`Element`·`Text`·`Comment` 와 두 컬렉션 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 언어 문법은 [`../../languages/`](../../languages/) 에 있고, 여기는 **브라우저가 건네주는 객체와 그 계약**이다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「Node tree」·「Interface Node」·「Interface ParentNode」 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 그래서 이 문서는 **「이식성」을 주장하지 않는다.** 「두 엔진에서 확인했다」고 적지 않는다.\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. 기준은 **Baseline** 하나이고, 이 주제의 표면(`Node`·`childNodes`·`children`)은 **Baseline 추적 대상 자체가 아닐 만큼 오래된 것**이다([`../README.md`](../README.md) 의 「확인하지 못한 것」).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

**근거로 쓸 칸을 미리 가른다.**

| 안 흔들리는 칸 (근거로 쓴다) | 흔들리는 칸 (근거로 쓰지 않는다) |
|---|---|
| `--dump-dom` 이 뱉은 트리 문자열 · 노드 개수 · `nodeType` 값 · `nodeName` · API 반환값(`null` 포함) · 예외 이름과 메시지 | Chrome 판 번호 · `performance.now()` 수치 · 스크린샷 안티에일리어싱 |

이 주제의 블록에는 **흔들리는 칸이 하나도 없다** — 수치를 재는 자리가 없기 때문이다. 시간 수치는 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에만 나온다.

## 한눈에 — 쉽게 말하면

**★ 브라우저가 들고 있는 것은 「HTML 문자열」이 아니라 「노드로 만든 나무」다. 그리고 그 나무에는 눈에 안 보이는 가지가 잔뜩 있다.**

가계도에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 가계도 한 장 | `document` — 나무 전체를 들고 있는 뿌리 |
| 가계도에 그려진 사람 칸 | `Element` — `<p>`·`<div>` 같은 태그 |
| 칸 안에 적힌 이름 글씨 | `Text` — 글자만 담은 노드 |
| 연필로 흐리게 적어 둔 메모 | `Comment` — `<!-- -->` |
| 「사람만 세어 봐」 | `children` — 요소만 |
| 「칸이든 글씨든 메모든 다 세어 봐」 | `childNodes` — 전부 |
| 아직 가계도에 안 붙인 쪽지 | `DocumentFragment` — 트리 밖 임시 자루 |

- **같은 자리를 두 가지로 셀 수 있다.** 그래서 「자식이 몇이냐」는 **질문이 아니라 두 질문**이다.
- **소스의 줄바꿈과 들여쓰기가 노드가 된다.** 보기 좋게 쓴 들여쓰기가 `Text` 노드로 남는다.
- **가장 흔한 사고가 여기서 난다** — `firstChild` 를 「첫 번째 태그」로 읽는 것.

```text
   소스에 쓴 것                          브라우저가 만든 것
   <div id="box">                        <div id=box>
     <p>첫 문단</p>                        ├─ #text  "\n  "     <- 줄바꿈+들여쓰기
     <!-- 주석 -->                         ├─ <p>
     <p>둘째 문단</p>                       ├─ #text  "\n  "
   </div>                                 ├─ #comment " 주석 "
                                          ├─ #text  "\n  "
                                          ├─ <p>
                                          └─ #text  "\n"
   태그 2개로 보인다                       childNodes 7개 · children 2개
```

실무에서 이게 터지는 자리는 「**첫 번째 자식을 집어 온다**」다.\
`box.firstChild.textContent` 가 빈 문자열이 나와서 「데이터가 비었나」를 의심하는데, 사실은 **들여쓰기 공백을 집은 것**이다.\
**그런데 같은 마크업을 한 줄로 붙여 쓰면 그 사고가 안 난다** — 그래서 개발 중에는 멀쩡하다가 포매터를 돌린 뒤에 깨진다.

> **노드(node)** — DOM 나무의 점 하나. 요소만이 아니라 글자 덩어리·주석·문서 자신도 전부 노드다.\
> 예: `<p>가</p>` 는 노드 둘이다 — `<p>` 요소 하나와 그 안의 글자 `가` 하나.

> **요소(element)** — 노드 중에서 **태그로 만들어진 것**. `nodeType` 이 `1` 인 것.\
> 예: `<p>` 는 요소이고 그 안의 글자 `가` 는 요소가 아니다.

## 이 주제가 답하려는 질문

원고가 없는 플랫폼 주제라 「문제」 대신 이 세 질문을 둔다.

1. **브라우저가 실제로 들고 있는 나무는 어떤 모양인가.** 내가 쓴 소스와 어디가 다른가.
2. **`childNodes` 와 `children` 은 왜 둘인가.** 무엇이 한쪽에만 보이고, 그 차이가 어디서 사고가 되나.
3. **탐색 프로퍼티가 왜 쌍으로 있나.** `parentNode`/`parentElement` 처럼 짝지어진 것들이 **어디서 갈리나.**

## 이 갈래의 관측 창 — 보이지 않는 나무를 글자로 만든다

CSS 갈래에는 「무효한 선언이 조용히 버려진다」를 가르는 **진단 3창**이 있었다([CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)).\
이 갈래의 문제는 다르다 — **버려지는 것이 아니라 「내가 상상한 나무」와 「실제 나무」가 다른 것**이다. 그래서 창도 다르다.

```text
  창 1  --dump-dom          스크립트가 다 돌고 난 뒤의 나무를 '글자로' 뽑는다
        무엇을 답하나:  내 코드가 나무를 무엇으로 바꿨나
        소스와 나란히 놓으면 파서가 넣은 것과 API 가 바꾼 것이 갈라진다

  창 2  nodeType · nodeName · childNodes.length 대 children.length
        무엇을 답하나:  그 나무 안에 무엇이 들어 있나
        공백 텍스트 노드와 주석 노드가 여기서만 보인다

  창 3  같은 것을 두 번 읽기 (DOM 을 바꾸기 전 / 바꾼 뒤)
        무엇을 답하나:  내가 들고 있는 컬렉션이 살아 있나 죽어 있나
        02번 주제의 본체다

  ★ 창 4 는 주제마다 다르다.  01 은 ownerDocument,  04 는 '실행 흔적'.
```

- **창 1 은 지어낼 수 없다.** 브라우저가 뱉은 직렬화 문자열이고, 읽는 사람이 자기 머신에서 그대로 다시 던질 수 있다.
- **창 2 가 없으면 창 1 이 거짓말한다.** 직렬화된 HTML 에서는 공백 텍스트 노드가 **그냥 줄바꿈처럼 보인다** — 그것이 노드인지 아닌지는 `childNodes.length` 를 세어야 안다.
- **창 3 은 시간이 걸린 창**이다. 한 번만 읽으면 라이브와 정적이 **같은 답을 준다.**

## 동작 방식

### (0) 창 1 — 소스와 나무를 나란히 놓는다

**언제 쓰나** — 「내 스크립트가 무엇을 바꿨나」를 확인하는 모든 자리. **이 창을 먼저 세워야 나머지가 읽힌다.**

```html
<!-- ex01d.html -->
<!doctype html>
<meta charset="utf-8">
<title>01d</title>
<p id="hello">안녕</p>
<script>
const p = document.getElementById('hello');
p.textContent = '바뀐 글';
p.setAttribute('data-touched', 'yes');
p.after(document.createElement('hr'));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01d.html
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>01d</title>
</head><body><p id="hello" data-touched="yes">바뀐 글</p><hr>
<script>
const p = document.getElementById('hello');
p.textContent = '바뀐 글';
p.setAttribute('data-touched', 'yes');
p.after(document.createElement('hr'));
</script>
</body></html>
(exit 0)
```

그림 해설 (한 단계씩):

- **`<html>`·`<head>`·`<body>` 는 내가 안 썼다.** 파서가 넣었다 — 그 규칙이 정본인 곳은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **03번**(파서·오류 복구)이다. 여기서는 **그 결과 나무를 API 로 읽고 바꾸는 것**만 다룬다.
- **`<p>` 의 글자가 바뀌었고 `data-touched` 속성이 붙었고 `<hr>` 이 생겼다.** 소스에는 없는 것들이다 — `--dump-dom` 이 보여 주는 것은 **로드가 끝난 시점의 나무**이지 소스가 아니다.
- **`<script>` 자신도 나무에 남아 있다.** 스크립트는 「실행되고 사라지는 것」이 아니라 **요소 노드 하나**다.

비용 — 없음. 다만 **`--dump-dom` 은 한 시점의 스냅샷**이다. 타이머로 나중에 바뀌는 것은 안 보인다.

### (1) 노드의 종류 — `nodeType` 이라는 번호표

**언제 쓰나** — 컬렉션을 순회하다가 「이게 요소인가 글자인가」를 갈라야 할 때.

```html
<!-- ex01c.html -->
<!doctype html>
<meta charset="utf-8">
<title>01c</title>
<p id="p">문단</p>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const line = (label, n) => O.push(padw(label, 26) + 'nodeType=' + String(n.nodeType).padStart(2) +
  '  nodeName=' + n.nodeName);
line('document', document);
line('document.doctype', document.doctype);
line('document.documentElement', document.documentElement);
line('p 안의 텍스트', document.getElementById('p').firstChild);
line('새 주석', document.createComment('c'));
line('새 조각', document.createDocumentFragment());
O.push('');
const el = document.createElement('b');
const other = document.implementation.createHTMLDocument('다른 문서');
const alien = other.createElement('i');
O.push('el.ownerDocument === document      = ' + (el.ownerDocument === document));
O.push('alien.ownerDocument === document   = ' + (alien.ownerDocument === document));
O.push('alien.ownerDocument === other      = ' + (alien.ownerDocument === other));
document.body.appendChild(alien);
O.push('붙인 뒤 alien.ownerDocument === document = ' + (alien.ownerDocument === document));
O.push('');
const t = document.createTextNode('t'), c = document.createComment('c'), f = document.createDocumentFragment();
O.push('el  instanceof Node/Element/HTMLElement = ' + [el instanceof Node, el instanceof Element, el instanceof HTMLElement].join('/'));
O.push('t   instanceof Node/CharacterData/Element = ' + [t instanceof Node, t instanceof CharacterData, t instanceof Element].join('/'));
O.push('c   instanceof Node/CharacterData/Element = ' + [c instanceof Node, c instanceof CharacterData, c instanceof Element].join('/'));
O.push('f   instanceof Node/Element = ' + [f instanceof Node, f instanceof Element].join('/'));
O.push('document instanceof Node/Element = ' + [document instanceof Node, document instanceof Element].join('/'));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
document                  nodeType= 9  nodeName=#document
document.doctype          nodeType=10  nodeName=html
document.documentElement  nodeType= 1  nodeName=HTML
p 안의 텍스트             nodeType= 3  nodeName=#text
새 주석                   nodeType= 8  nodeName=#comment
새 조각                   nodeType=11  nodeName=#document-fragment

el.ownerDocument === document      = true
alien.ownerDocument === document   = false
alien.ownerDocument === other      = true
붙인 뒤 alien.ownerDocument === document = true

el  instanceof Node/Element/HTMLElement = true/true/true
t   instanceof Node/CharacterData/Element = true/true/false
c   instanceof Node/CharacterData/Element = true/true/false
f   instanceof Node/Element = true/false
document instanceof Node/Element = true/false
(exit 0)
```

그림 해설 (한 단계씩):

- **번호는 명세가 못 박은 상수**다. `1`·`3`·`8`·`9`·`10`·`11` 여섯이 오늘 만나는 전부다(`2`·`4`·`5`·`6`·`12` 는 명세에서 제거됐다).
- **`nodeName` 은 요소면 대문자 태그 이름**이고, 요소가 아니면 `#text`·`#comment`·`#document`·`#document-fragment` 처럼 **`#` 으로 시작하는 고정 문자열**이다.
- **`Text` 와 `Comment` 는 형제**다 — 둘 다 `CharacterData` 를 상속하고, 둘 다 `Element` 가 아니다.
- **`document` 자신도 노드**다(`nodeType = 9`). 하지만 **요소가 아니다** — 이 한 줄이 아래 (4)의 `null` 을 설명한다.

```text
                      Node  (nodeType · parentNode · childNodes 는 여기서 온다)
                        |
     +-------------+----+--------+----------------+
     |             |             |                |
  Element(1)  CharacterData  Document(9)   DocumentFragment(11)
     |             |
  HTMLElement   +--+----+
                |       |
             Text(3) Comment(8)
```

- **`Element` 가 주는 것과 `Node` 가 주는 것이 다르다.** `children`·`firstElementChild` 는 `Element` 쪽 계약(정확히는 `ParentNode` 믹스인)이고, `childNodes`·`firstChild` 는 `Node` 쪽이다.
- `DocumentFragment` 도 **`ParentNode`** 라서 `children` 을 갖는다 — 그래서 문서에 붙이기 전에도 똑같이 다룰 수 있다([03번 주제](../03-node-creation-insertion-removal/2-summary.md)).

비용 — 없음. `nodeType` 비교는 숫자 비교 하나다.

### (2) ★ `childNodes` 대 `children` — 공백과 주석이 어디에 보이나

**언제 쓰나** — 자식을 세거나 순회하는 모든 자리. **이 주제에서 가장 많이 틀리는 자리다.**

```html
<!-- ex01a.html -->
<!doctype html>
<meta charset="utf-8">
<title>01a</title>
<div id="box">
  <p>첫 문단</p>
  <!-- 주석 -->
  <p>둘째 문단</p>
</div>
<script>
const NT = {1:'ELEMENT_NODE', 3:'TEXT_NODE', 8:'COMMENT_NODE'};
const O = [];
const box = document.getElementById('box');
O.push('box.childNodes.length = ' + box.childNodes.length);
O.push('box.children.length   = ' + box.children.length);
O.push('');
box.childNodes.forEach((n, i) => {
  O.push('childNodes[' + i + ']  nodeType=' + n.nodeType + ' ' + NT[n.nodeType] +
         '  nodeName=' + n.nodeName + '  nodeValue=' + JSON.stringify(n.nodeValue));
});
O.push('');
for (let i = 0; i < box.children.length; i++) {
  O.push('children[' + i + ']    nodeName=' + box.children[i].nodeName);
}
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
box.childNodes.length = 7
box.children.length   = 2

childNodes[0]  nodeType=3 TEXT_NODE  nodeName=#text  nodeValue="\n  "
childNodes[1]  nodeType=1 ELEMENT_NODE  nodeName=P  nodeValue=null
childNodes[2]  nodeType=3 TEXT_NODE  nodeName=#text  nodeValue="\n  "
childNodes[3]  nodeType=8 COMMENT_NODE  nodeName=#comment  nodeValue=" 주석 "
childNodes[4]  nodeType=3 TEXT_NODE  nodeName=#text  nodeValue="\n  "
childNodes[5]  nodeType=1 ELEMENT_NODE  nodeName=P  nodeValue=null
childNodes[6]  nodeType=3 TEXT_NODE  nodeName=#text  nodeValue="\n"

children[0]    nodeName=P
children[1]    nodeName=P
(exit 0)
```

```text
   childNodes (7개)                       children (2개)
   +----------------------------+         +----------------------------+
   | 0 #text     "\n  "         |         | 0 <p>                      |
   | 1 <p>                      |         | 1 <p>                      |
   | 2 #text     "\n  "         |         |                            |
   | 3 #comment  " 주석 "       |         |                            |
   | 4 #text     "\n  "         |         |                            |
   | 5 <p>                      |         |                            |
   | 6 #text     "\n"           |         |                            |
   +----------------------------+         +----------------------------+
     Node 의 계약 — 전부 보인다              ParentNode 의 계약 — 요소만
```

그림 해설 (한 단계씩):

- **공백 텍스트 노드 4개와 주석 1개**가 차이의 전부다. 소스에서 태그 사이에 넣은 줄바꿈·들여쓰기가 그대로 노드가 된다.
- **`<p>` 두 개 사이에 공백 노드가 하나**다. 줄바꿈과 들여쓰기가 **연속된 한 덩어리**라 노드 하나로 묶인다.
- **앞뒤에도 하나씩** 있다 — `<div>` 바로 뒤의 줄바꿈과 `</div>` 바로 앞의 줄바꿈.
- **`nodeValue` 가 `null` 인 것이 요소**다. `Text`·`Comment` 만 값을 갖는다.

```html demo
<div id="box">
  <p>첫 문단</p>
  <!-- 주석 -->
  <p>둘째 문단</p>
</div>
<pre id="census"></pre>
<script>
  const 이름 = {1: 'Element', 3: 'Text', 8: 'Comment'};
  document.getElementById('census').textContent =
    [...document.getElementById('box').childNodes]
      .map((n, i) => i + ': ' + 이름[n.nodeType] + ' ' + JSON.stringify(n.nodeValue ?? n.nodeName))
      .join('\n') +
    '\nchildNodes ' + document.getElementById('box').childNodes.length +
    '개 / children ' + document.getElementById('box').children.length + '개';
</script>
<style>#census { background: #f1f5f9; padding: 8px; font: 12px/1.5 monospace; }</style>
```

> **보이는 것** — 회색 상자에 `childNodes` 일곱 줄이 번호와 함께 나오고, 홀수 자리는 전부 `Text "\n  "` 다. 맨 아래에 「childNodes 7개 / children 2개」가 찍힌다. 소스의 태그는 둘뿐인데 목록은 일곱 줄이다.\
> **바꿔 볼 것** — 소스의 `<div id="box">` 안을 **줄바꿈 없이 한 줄로** 붙여 쓰면 목록이 세 줄(`<p>`·주석·`<p>`)로 줄어든다 · `childNodes` 를 `children` 으로 바꾸면 두 줄만 남는다.

비용 — `childNodes` 는 **라이브 `NodeList`**, `children` 은 **라이브 `HTMLCollection`** 이다. 둘 다 잡아 두면 DOM 이 바뀔 때 따라 변한다([02번 주제](../02-element-queries-and-live-collections/2-summary.md)).

### (3) 탐색 쌍 — `Node` 판과 `Element` 판이 따로 있다

**언제 쓰나** — 형제·부모를 따라 걸어갈 때. **쌍 중 어느 쪽을 쓰느냐로 결과가 갈린다.**

```html
<!-- ex01b.html -->
<!doctype html>
<meta charset="utf-8">
<title>01b</title>
<div id="box">
  <p id="p1">첫 문단</p>
  <p id="p2">둘째 문단</p>
</div>
<script>
const show = n => n === null ? 'null'
  : n.nodeType === 1 ? '<' + n.nodeName.toLowerCase() + (n.id ? ' id=' + n.id : '') + '>'
  : n.nodeType === 9 ? '#document'
  : n.nodeType === 11 ? '#document-fragment'
  : n.nodeName + ' ' + JSON.stringify(n.nodeValue);
const O = [];
const box = document.getElementById('box'), p1 = document.getElementById('p1');
O.push('box.firstChild          = ' + show(box.firstChild));
O.push('box.firstElementChild   = ' + show(box.firstElementChild));
O.push('box.lastChild           = ' + show(box.lastChild));
O.push('box.lastElementChild    = ' + show(box.lastElementChild));
O.push('p1.nextSibling          = ' + show(p1.nextSibling));
O.push('p1.nextElementSibling   = ' + show(p1.nextElementSibling));
O.push('p1.parentNode           = ' + show(p1.parentNode));
O.push('p1.parentElement        = ' + show(p1.parentElement));
O.push('');
O.push('document.body.parentNode           = ' + show(document.body.parentNode));
O.push('document.body.parentElement        = ' + show(document.body.parentElement));
O.push('document.documentElement.parentNode    = ' + show(document.documentElement.parentNode));
O.push('document.documentElement.parentElement = ' + show(document.documentElement.parentElement));
O.push('');
const frag = document.createDocumentFragment();
const orphan = document.createElement('span');
frag.appendChild(orphan);
O.push('frag 안 span.parentNode    = ' + show(orphan.parentNode));
O.push('frag 안 span.parentElement = ' + show(orphan.parentElement));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
box.firstChild          = #text "\n  "
box.firstElementChild   = <p id=p1>
box.lastChild           = #text "\n"
box.lastElementChild    = <p id=p2>
p1.nextSibling          = #text "\n  "
p1.nextElementSibling   = <p id=p2>
p1.parentNode           = <div id=box>
p1.parentElement        = <div id=box>

document.body.parentNode           = <html>
document.body.parentElement        = <html>
document.documentElement.parentNode    = #document
document.documentElement.parentElement = null

frag 안 span.parentNode    = #document-fragment
frag 안 span.parentElement = null
(exit 0)
```

```text
   같은 자리를 두 이름으로 묻는다 — 위 출력의 앞 여덟 줄이 그 짝이다

   '첫째 자식'  +-- Node 판     firstChild          뭐든 첫째 (공백이 걸린다)
                +-- Element 판  firstElementChild   요소만

   '다음 형제'  +-- Node 판     nextSibling         다음 노드 (공백이 걸린다)
                +-- Element 판  nextElementSibling  다음 요소

   '부모'       +-- Node 판     parentNode          부모가 무엇이든
                +-- Element 판  parentElement       부모가 요소일 때만 ... 아니면 null
```

그림 해설 (한 단계씩):

- **쌍의 규칙은 하나**다 — 이름에 `Element` 가 들어가면 **텍스트·주석을 건너뛴다.**
- 쌍은 여섯이다 — `firstChild`/`firstElementChild` · `lastChild`/`lastElementChild` · `nextSibling`/`nextElementSibling` · `previousSibling`/`previousElementSibling` · `childNodes`/`children` · `parentNode`/`parentElement`.
- **부모 쌍만 성격이 다르다.** 「건너뛴다」가 아니라 「**부모가 요소가 아니면 `null`**」이다. 건너뛸 대상이 애초에 없다 — 부모는 하나뿐이니까.

### (4) ★ 나무의 꼭대기에서 둘이 갈린다

**언제 쓰나** — 조상을 타고 올라가는 반복문을 쓸 때. **여기서 무한 루프나 `null` 참조가 난다.**

```text
   #document                 nodeType 9 — 노드지만 '요소가 아니다'
      |
   <html>  = document.documentElement     <- 여기서 Element 판이 끊긴다
      |
   <body>
      |
   <div id=box>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,13p;15,16p'
document.body.parentNode           = <html>
document.body.parentElement        = <html>
document.documentElement.parentNode    = #document
document.documentElement.parentElement = null
frag 안 span.parentNode    = #document-fragment
frag 안 span.parentElement = null
(exit 0)
```

그림 해설 (한 단계씩):

- **`<html>` 에게도 부모는 있다** — `#document` 다. 「부모가 없어서」 `null` 인 것이 아니다.
- `parentElement` 가 `null` 인 이유는 「**부모가 요소가 아니어서**」다. 이 구분을 놓치면 「루트에 닿았다」를 잘못 판정한다.
- **같은 모양이 `DocumentFragment` 안에서도 난다.** 조각에 담긴 노드는 `parentNode` 가 조각(`nodeType 11`)이고 `parentElement` 는 `null` 이다 — 실측이 위 출력의 마지막 두 줄이다.
- 그래서 **조상 순회는 `parentElement` 로 쓰는 쪽이 안전하다.** `while (el = el.parentElement)` 는 `<html>` 에서 저절로 멈추는데, `parentNode` 로 쓰면 `#document` 를 거쳐 한 바퀴 더 돈다.

비용 — 없음. 다만 **요소만 필요하면 `closest()` 가 한 줄**이다([02번 주제](../02-element-queries-and-live-collections/2-summary.md)).

### (5) `ownerDocument` — 이 노드는 어느 문서의 것인가

**언제 쓰나** — `<template>`·`iframe`·`DOMParser` 처럼 **문서가 둘 이상** 등장할 때.

위 `ex01c` 출력의 가운데 네 줄이 근거다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,11p'
el.ownerDocument === document      = true
alien.ownerDocument === document   = false
alien.ownerDocument === other      = true
붙인 뒤 alien.ownerDocument === document = true
(exit 0)
```

```text
   other 문서                          document
   +-------------+                     +-------------+
   |   <i>       |   appendChild(i)    |   <body>    |
   |             |  --------------->   |     <i>     |
   +-------------+                     +-------------+
     ownerDocument = other               ownerDocument = document
                                         ★ 옮겨 담는 것이 아니라 '입양' 이라는 단계다
```

그림 해설 (한 단계씩):

- **모든 노드는 만들어질 때 문서 하나에 매인다.** `createElement` 를 부른 그 `document` 다.
- **다른 문서의 노드를 그냥 붙일 수 있다** — 명세가 삽입 과정에 **입양(adopt)** 을 넣어 뒀기 때문이다. 옛 DOM 에서 `WrongDocumentError` 를 던지던 자리가 지금은 자동으로 처리된다.
- 그래서 `ownerDocument` 가 답하는 것은 「지금 어디 붙어 있나」가 아니라 「**누가 만들었나 / 마지막으로 누가 입양했나**」다.
- 「문서에 붙어 있나」를 묻는 것은 **`isConnected`** 다 — 둘을 섞지 않는다.

비용 — 입양은 노드 **하위 트리 전체**를 훑는다. 큰 조각을 옮기면 그만큼 든다.

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
node.nodeType            // 1 요소 · 3 텍스트 · 8 주석 · 9 문서 · 10 doctype · 11 조각
node.nodeName            // 'DIV' · '#text' · '#comment' · '#document'
node.nodeValue           // Text·Comment 만 값을 갖는다. 요소는 null
node.ownerDocument       // 이 노드를 만든(또는 입양한) 문서
node.isConnected         // 지금 문서 트리에 붙어 있나

node.childNodes          // 라이브 NodeList — 전부
el.children              // 라이브 HTMLCollection — 요소만
node.firstChild          // el.firstElementChild
node.lastChild           // el.lastElementChild
node.nextSibling         // el.nextElementSibling
node.previousSibling     // el.previousElementSibling
node.parentNode          // el.parentElement
el.childElementCount     // = el.children.length
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
box.firstChild.textContent          // 들여쓰기 공백을 집을 수 있다
box.childNodes[0]                   // 위와 같은 것
for (const n of box.children) { n.nodeType }   // 항상 1 — 가를 필요가 없다
while (el = el.parentNode) { }      // #document 를 지나 한 바퀴 더 돈다
node.children                       // Text·Comment 노드에는 없다(undefined)
```

- **`children` 은 `ParentNode` 의 것**이라 `Element`·`Document`·`DocumentFragment` 에만 있다. 텍스트 노드에 `children` 을 물으면 `undefined` 다.
- **`childElementCount` 는 `children.length` 와 같은 값**이지만, 컬렉션 객체를 만들지 않는다는 뜻으로 읽는다.

### 어디서 헷갈리나

- **`nodeName` 의 대소문자**는 문서 종류에 달렸다. HTML 문서의 HTML 요소는 **대문자**(`P`)이고, SVG 요소나 XML 문서에서는 **원래 대소문자 그대로**다([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에 `SCRIPT,IMG,svg` 로 갈린 실측이 있다).
- **`tagName` 은 `Element` 에만 있고 `nodeName` 은 모든 노드에 있다.** 요소에서는 둘이 같은 값이다.
- **「자식이 없다」를 `firstChild === null` 로 판정하면 공백에 걸린다.** 요소 기준이면 `firstElementChild === null` 이나 `childElementCount === 0` 이다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `firstChild` 를 「첫 번째 태그」로 읽는다

실측에서 `box.firstChild` 는 **`#text "\n  "`** 였다. 예외도 경고도 없고, `textContent` 를 읽으면 공백 문자열이 나온다.\
**소스를 한 줄로 붙여 쓰면 같은 코드가 통과한다** — 그래서 포매터·템플릿 엔진을 바꾸는 순간 깨진다.

### 2. `childNodes.length` 로 「자식 요소 수」를 센다

실측에서 태그 둘인 `<div>` 의 `childNodes.length` 가 **7** 이었다.\
「항목이 2개인데 왜 7개로 나오지」는 대개 이 자리다.

### 3. `parentElement` 가 `null` 인 것을 「부모가 없다」로 읽는다

`document.documentElement.parentNode` 는 **`#document` 로 멀쩡히 있다.** 없는 것은 「**요소인 부모**」다.\
조각 안의 노드도 같은 모양이다 — `parentNode` 는 조각이고 `parentElement` 는 `null` 이다.

### 4. `ownerDocument` 와 `isConnected` 를 섞는다

`createElement` 로 갓 만든 노드는 **`ownerDocument` 가 이미 `document` 인데 `isConnected` 는 `false`** 다.\
「문서에 있나」를 `ownerDocument` 로 물으면 **항상 그렇다고 답한다.**

### 5. 주석 노드를 잊는다

`childNodes` 에는 **주석도 들어온다**(`nodeType 8`). 템플릿 엔진과 프레임워크가 **자리표시자로 주석을 심는 일이 흔해서**, 실제 페이지에서는 개발자가 안 쓴 주석 노드가 자주 있다.

### 6. `nodeName` 이 소문자일 거라 기대한다

HTML 문서의 HTML 요소는 **대문자**다. `n.nodeName === 'p'` 는 영원히 거짓이다. 비교할 것이면 `toLowerCase()` 를 걸거나 `matches('p')` 를 쓴다.

## 구현 세부사항 대 언어 보장

여기서 「언어 보장」은 **명세(WHATWG DOM·HTML)가 정한 것**이고, 「구현」은 **Blink 가 하는 것**이다.

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `nodeType` 상수 값(`1`·`3`·`8`·`9`·`10`·`11`) | **명세**(DOM §4.4 Interface `Node`) |
| `childNodes` 가 전부, `children` 이 요소만 | **명세**(DOM §4.2.6 `ParentNode`) |
| 둘 다 **라이브**인 것 | **명세** — 타입이 정한다. 구현 사정이 아니다 |
| `parentElement` 가 「부모가 요소가 아니면 `null`」 | **명세**(DOM §4.4) |
| 삽입할 때 다른 문서의 노드를 **입양**하는 것 | **명세**(DOM §4.2.3 「adopt」) |
| HTML 문서의 HTML 요소 `nodeName` 이 **대문자** | **명세**(DOM — `tagName` 은 HTML 문서의 HTML 요소에서 ASCII 대문자) |
| 소스의 줄바꿈·들여쓰기가 `Text` 노드가 되는 것 | **명세**(HTML 파싱 알고리즘). 트리 모양의 정본은 HTML 갈래다 |
| 연속된 공백이 **노드 하나로** 묶이는 것 | **명세**(파서가 문자들을 모아 한 텍스트 노드로 삽입) |
| `--dump-dom` 이 뱉는 **직렬화 형태**(속성 순서·빈 속성 `hidden=""`) | **명세**(HTML 직렬화 알고리즘) + **관찰**(Chrome 151) |
| `document.implementation.createHTMLDocument` 가 만든 문서의 구조 | **명세**. 다만 위 출력의 세부는 이 판의 관찰이다 |
| **`--dump-dom` 이 로드 완료 시점을 잡는 것** | **관찰**(Chrome 151 headless). 명세와 무관한 도구 동작이다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 자식 요소를 순회한다 | `children` · `firstElementChild` | `childNodes` (공백이 섞인다) |
| 글자까지 포함해 원본 그대로 훑는다 | `childNodes` | `children` (글자를 잃는다) |
| 조상을 타고 올라간다 | `closest()` · `parentElement` 루프 | `parentNode` 루프 (`#document` 를 지난다) |
| 노드 종류를 가른다 | `nodeType === 1` · `instanceof Element` | `nodeName` 문자열 비교 (대소문자) |
| 「문서에 붙어 있나」를 묻는다 | `isConnected` | `ownerDocument` |
| 자식이 비었는지 본다 | `childElementCount === 0` | `firstChild === null` |

판단 규칙 두 줄.

- **「글자와 주석이 나에게 의미가 있나」를 먼저 묻는다.** 없으면 `Element` 판을, 있으면 `Node` 판을 쓴다.
- **셋을 셀 때는 무엇을 세는지 이름으로 드러나게** 쓴다. `length` 라는 이름은 두 질문에 같은 얼굴을 하고 있다.

## 핵심 문장

- **브라우저가 들고 있는 것은 문자열이 아니라 노드 나무**다. `--dump-dom` 은 그 나무를 **다시 문자열로 그려 보여 주는 창**이고, 소스와 나란히 놓으면 파서와 내 코드가 한 일이 갈라진다.
- **노드는 요소만이 아니다** — `Text`(3)·`Comment`(8)·`Document`(9)·`DocumentFragment`(11)가 전부 노드다. 실측에서 태그 둘짜리 `<div>` 의 `childNodes` 가 **7개**였다.
- **소스의 들여쓰기가 텍스트 노드가 된다.** 연속된 공백은 **노드 하나**로 묶이고, 한 줄로 붙여 쓰면 아예 안 생긴다.
- **탐색 프로퍼티는 여섯 쌍**이고 규칙은 하나다 — 이름에 `Element` 가 들어가면 **글자와 주석을 건너뛴다.**
- **부모 쌍만 성격이 다르다** — 건너뛰는 게 아니라 「부모가 요소가 아니면 `null`」이다. 그래서 **`documentElement.parentElement` 가 `null`** 인데 `parentNode` 는 `#document` 로 있다.
- `ownerDocument` 가 답하는 것은 「**누가 만들었나**」이고 `isConnected` 가 답하는 것은 「**지금 붙어 있나**」다. 붙이는 순간 다른 문서의 노드도 **입양**된다.
- **「라이브냐 정적이냐」는 명세가 타입별로 못 박은 것**이다. `childNodes` 와 `children` 은 **둘 다 라이브**이고, 그것이 다음 주제의 출발점이다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 01번)
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md) — **조회와 라이브·정적의 정본.** 여기는 「나무에 무엇이 있나」까지, 그쪽은 「그것을 어떻게 찾고 그 결과가 살아 있나」부터
- [03번 주제](../03-node-creation-insertion-removal/2-summary.md) — **노드를 만들고 옮기는 것의 정본.** 여기는 「읽는 것」까지, 그쪽은 「바꾸는 것」부터
- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) — 같은 나무를 **문자열로 읽고 쓰는** 세 프로퍼티
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **03번**(파서·오류 복구) — **「파서가 어떤 트리를 만드나」의 정본.**\
  그쪽은 **마크업에서 트리가 나오는 규칙**까지, 여기는 **그 트리를 API 로 읽는 계약**부터다. 공백 텍스트 노드가 왜 생기는지는 그쪽, 그것이 `childNodes` 에 어떻게 보이는지는 여기다.
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **04번**(공백·텍스트·문자 참조) — **공백이 화면에서 축약되는 규칙의 정본.**\
  그쪽은 **공백이 어떻게 보이나**까지, 여기는 **그 공백이 노드로 몇 개 남나**부터다. 화면에서 하나로 합쳐 보이는 공백도 `childNodes` 에는 노드로 남아 있다
- JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **15번**(프로토타입 체인) — `Node`·`Element` 는 **JS 프로토타입 사슬**로 노출된다. 「`instanceof` 가 무엇을 보나」는 그쪽, 「어떤 인터페이스가 무엇을 주나」는 여기다
- [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md) — 이 갈래의 「관측 창」이 본뜬 **진단 3창**의 원본
- [`../../../../history/web/05-웹플랫폼-API.md`](../../../../history/web/05-웹플랫폼-API.md) — DOM 이 **언제 어떻게 표준이 됐나**. 여기는 오늘의 계약만

## 용어 풀이

- **노드(node)** — DOM 나무의 점 하나. 요소·글자·주석·문서·조각이 전부 노드다.
- **요소(element)** — 태그로 만들어진 노드. `nodeType` 이 `1`.
- **텍스트 노드(`Text`)** — 글자만 담은 노드. `nodeType` 이 `3`, `nodeValue` 에 글자가 들어 있다.
- **주석 노드(`Comment`)** — `<!-- -->`. `nodeType` 이 `8`. 프레임워크가 자리표시자로 자주 심는다.
- **문서 조각(`DocumentFragment`)** — 부모가 없는 임시 자루. `nodeType` 이 `11`. 삽입하면 **자식들만** 들어간다.
- **`ParentNode`** — `children`·`firstElementChild`·`append`·`prepend` 를 주는 믹스인. `Element`·`Document`·`DocumentFragment` 가 갖는다.
- **`NodeList`** — `childNodes`·`querySelectorAll` 이 돌려주는 목록 타입. **어디서 왔느냐에 따라 라이브이기도 정적이기도 하다**(02번).
- **`HTMLCollection`** — `children`·`getElementsBy*` 가 돌려주는 목록 타입. **언제나 라이브**다.
- **입양(adopt)** — 다른 문서의 노드를 이 문서 것으로 바꾸는 명세상의 단계. 삽입할 때 자동으로 일어난다.
- **`isConnected`** — 이 노드가 지금 문서 트리에 이어져 있나. `ownerDocument` 와 다른 질문이다.
- **직렬화(serialization)** — 나무를 다시 HTML 문자열로 그리는 것. `--dump-dom`·`innerHTML` 이 이것을 쓴다.

## 더 들어가면

- **`nodeType` 번호에 구멍이 있는 이유**는 역사다. `2`(속성)·`4`(CDATA)·`5`·`6`·`12` 는 DOM4 에서 제거됐고 번호만 남았다. **속성이 노드가 아니게 된 것**이 그중 가장 큰 변화이고, 그 결과가 [목록의 **06번 주제**](../06-attribute-vs-property/)가 다루는 「속성 대 성질」이다.
- **`Attr` 이 노드에서 빠진 자리**를 `NamedNodeMap` 이 아직 지키고 있다. `el.attributes` 는 오늘도 라이브 컬렉션이다.
- **`children` 은 원래 IE 의 확장**이었다. 표준이 아니었는데 실무에서 너무 많이 쓰여 DOM4 가 `ParentNode` 로 받아들였다 — 웹 표준이 「이미 쓰이는 것을 사후에 규정」하는 전형적인 모양이다.
- **공백 텍스트 노드를 없애는 표준 수단은 없다.** `normalize()` 는 인접한 텍스트 노드를 합칠 뿐 지우지 않는다. 빌드 단계에서 마크업을 줄여 없애거나, 읽는 쪽에서 `children` 을 쓰는 것이 유일한 대처다.
- **`Node` 는 `EventTarget` 을 상속한다.** 그래서 텍스트 노드에도 `addEventListener` 가 있다 — 쓰는 일은 거의 없지만, **이벤트 전파가 노드 사슬을 탄다**는 사실의 뿌리가 여기다(목록의 **16번 주제**).
