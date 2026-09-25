# web-api/05 — `DocumentFragment` 와 `<template>` 복제: 일괄 삽입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 언어 문법은 [`../../languages/`](../../languages/) 에 있고, 여기는 **브라우저가 건네주는 객체와 그 계약**이다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「Interface `DocumentFragment`」·「Mutation algorithms」·「`cloneNode`」·「`importNode`」·「`adoptNode`」 절과 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/scripting.html#the-template-element) 의 「The `template` element」 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 그래서 이 문서는 **「이식성」을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `DocumentFragment` 는 DOM Level 1(1998) 부터 있었고 `<template>` 은 HTML5 후기에 들어와 오늘 모든 현행 엔진에 있다.\
> **선행** — [03번 주제](../03-node-creation-insertion-removal/2-summary.md)(노드 생성·삽입·제거). 거기서 「조각은 넣으면 빈다」까지 봤고, 여기는 **묶음 삽입 설계와 `<template>`** 부터다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 있다** — 삽입 비용을 재기 때문이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 결과 트리 문자열 · 자식 수 · `ownerDocument` 동일성 · `isConnected` · **실행 횟수**(`script`·`img`) · **`MutationObserver` 레코드 수** | 전부 명세가 정한 절차의 결과다 |
| **안 흔들린다** | 시간 표의 **자릿수와 순위** | 세 판 모두 같았다 |
| **흔들린다** | `performance.now()` 의 **개별 수치**(중앙값·최소·최대 전부) | 판마다 달라진다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- **수치를 인용할 때는 「몇 판을 어떻게 쟀나」를 같이 적는다** — 한 파일 안에서 **9판**을 돌려 **중앙값**을 쓰고 최소·최대를 함께 실었다.
- ★ **`performance.now()` 는 Chrome 에서 100마이크로초 단위로 뭉개진다**([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) 실측). 표에 `0.00`·`0.10` 이 보이면 「0 이다」가 아니라 「**이 도구의 분해능 아래다**」로 읽는다.
- **재대조에서 수치 칸만 정규화**한다. 위 표에 없는 것은 정규화하지 않는다.

## 한눈에 — 쉽게 말하면

**★ 둘 다 「본 문서 밖의 자리」다. 조각은 한 번 쓰고 비는 쟁반이고, `<template>` 은 몇 번이든 찍어 쓰는 거푸집이다.**

주방에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 접시를 **쟁반에 모아** 한 번에 나른다 | `DocumentFragment` — 넣고 나면 쟁반만 빈 채 남는다 |
| 쟁반은 **식탁에 안 올린다** | 조각 자신은 트리에 안 들어간다 |
| 붕어빵 **틀** | `<template>` — 안의 반죽은 먹는 것이 아니다 |
| 틀은 **불에 안 올린다** | `<template>` 안의 `<script>`·`<img>` 는 **안 돈다** |
| 틀에서 **하나 찍어 낸다** | `template.content.cloneNode(true)` — 틀은 그대로 남는다 |
| 찍어 낸 것을 **접시에 올린다** | 삽입 — 그 순간 본 문서의 것이 된다 |

- **조각은 일회용이고 틀은 재사용이다.** 이 한 줄이 둘의 차이 전부다.
- **틀 안은 본 문서가 아니다.** 그래서 `document.querySelector` 로 안 잡히고, 스크립트도 이미지도 안 돈다.
- ★ **「조각에 모아 넣으면 빠르다」는 이 판에서 재현되지 않았다.** 재고 나서 결론을 적었다 — 아래 (6)에 있다.

```text
   본 문서                        본 문서 밖
   +---------------------+       +---------------------------+
   | document            |       | DocumentFragment          |
   |   <ul id=host>      |  <--- |   <li> <li> <li>          |  넣으면 자식만 간다.
   |                     |       |   (넣고 나면 빈다)         |  쟁반은 남고 빈다
   +---------------------+       +---------------------------+
             ^
             |                   +---------------------------+
             +------ 복제 ------ | <template>.content        |
                                 |   <li class=row>          |  ★ 다른 '문서' 에 산다
                                 |   (찍어도 안 줄어든다)      |    script·img 가 안 돈다
                                 +---------------------------+
```

실무에서 이게 터지는 자리는 **목록 렌더링**이다.\
「틀을 `document.querySelector('#tpl .row')` 로 잡아 고치자」고 쓰면 **`null` 이 나온다.**\
**에러 메시지가 「왜 없는지」를 말해 주지 않아서** 오타를 의심하다가 한참 헤맨다.

> **`DocumentFragment`** — 부모 없는 임시 노드 자루. 삽입하면 **자식들만** 옮겨 가고 자신은 빈다.\
> 예: `li` 셋을 담아 `list.appendChild(frag)` 하면 `list` 에 `li` 셋이 생기고 자루는 빈다.

> **`<template>`** — 파서가 만들되 **본 트리에 넣지 않는** 요소. 내용은 `template.content` 라는 조각 안에 따로 있다.\
> 예: `<template><li>항목</li></template>` 은 화면에 아무것도 안 그린다.

> **불활성 문서(inert document)** — 브라우징 문맥이 없어 스크립트·리소스 요청이 일어나지 않는 문서.\
> 예: `template.content.ownerDocument` 가 그런 문서다 — `defaultView` 가 `null` 이다.

## 이 주제가 답하려는 질문

1. **조각에 모아 한 번에 넣는 것은 무엇을 줄이나.** 그리고 그것이 정말 「빠름」인가.
2. **`<template>` 안은 왜 안 잡히고 왜 안 도나.** 둘이 같은 이유인가 다른 이유인가.
3. **복제하는 방법이 셋인데**(`cloneNode`·`importNode`·`adoptNode`) 무엇이 다른가.

## 이 갈래의 관측 창 — ★ 창 4 는 `ownerDocument`

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋에 이 주제의 창을 하나 더 얹는다.

```text
  창 1  --dump-dom             결과 트리를 글자로
  창 2  childNodes.length      무엇이 몇 개인가
  창 3  두 번 읽기              조작 전후를 같은 프로브로
  ★ 창 4 (이 주제 고유)  ownerDocument 동일성 — 'n.ownerDocument === document'
        무엇을 답하나:  이 노드가 '어느 문서' 소속인가
        이 한 창이 세 가지를 한꺼번에 설명한다
          - querySelector 로 왜 안 잡히나
          - script·img 가 왜 안 도나
          - cloneNode 와 importNode 가 왜 갈리나
  ★ 창 5 (빌려 쓴다)  04번의 전역 실행 계수기 — '트리에 있나' 가 아니라 '돌았나'
  ★ 창 6 (빌려 쓴다)  04번의 performance.now() 9판 중앙값 — 비용
```

- **창 4 를 먼저 정한 것이 이 주제의 설계**다. `<template>` 의 세 가지 증상은 **원인이 하나**인데, `--dump-dom` 으로도 `childNodes.length` 로도 그 하나가 안 보인다.
- **창 5 없이는 「안 돌았다」를 증명할 수 없다.** 노드는 트리에 **있으므로** 창 1·2 는 정상이라고 답한다.
- ★ **창 6 의 결과가 이 주제의 가장 뜻밖의 칸**이었다 — 아래 (6).

## 동작 방식

### (1) 조각 — 넣으면 비고, 결과 트리는 반복 삽입과 같다

**언제 쓰나** — 여러 노드를 한 번에 넣을 때. **그리고 「왜 두 번째 삽입이 아무 일도 안 하지」를 만날 때.**

```html
<!-- wa05b-05-frag.html -->
<!doctype html>
<meta charset="utf-8">
<title>05-frag</title>
<ul id="host"></ul>
<ul id="hostA"></ul>
<ul id="hostB"></ul>
<script>
const O = [];
const li = t => Object.assign(document.createElement('li'), {textContent: t});
const host = document.getElementById('host');
const frag = document.createDocumentFragment();
for (const t of ['가', '나', '다']) frag.appendChild(li(t));
O.push('DocumentFragment      nodeType = ' + frag.nodeType + '   nodeName = ' + frag.nodeName +
       '   isConnected = ' + frag.isConnected);
O.push('붙이기 전   frag.childNodes.length = ' + frag.childNodes.length +
       '   host.children.length = ' + host.children.length);
const back = host.appendChild(frag);
O.push('붙인 뒤     frag.childNodes.length = ' + frag.childNodes.length +
       '   host.children.length = ' + host.children.length);
O.push('host.innerHTML = ' + host.innerHTML);
O.push('appendChild(frag) 반환값 === frag = ' + (back === frag) + '   반환값.childNodes.length = ' + back.childNodes.length);
host.appendChild(frag);
O.push('빈 frag 를 다시 붙이면 host.children.length = ' + host.children.length + '   (아무 일도 안 한다)');
O.push('');

const A = document.getElementById('hostA'), B = document.getElementById('hostB');
const f2 = document.createDocumentFragment();
for (const t of ['가', '나', '다']) f2.appendChild(li(t));
A.appendChild(f2);
for (const t of ['가', '나', '다']) B.appendChild(li(t));
O.push('조각에 모아 한 번  hostA.innerHTML = ' + A.innerHTML);
O.push('반복 appendChild   hostB.innerHTML = ' + B.innerHTML);
O.push('두 문자열이 같은가 = ' + (A.innerHTML === B.innerHTML));
O.push('childNodes.length  A = ' + A.childNodes.length + '   B = ' + B.childNodes.length);
O.push('outerHTML 바이트 길이  A = ' + A.outerHTML.length + '   B = ' + B.outerHTML.length +
       '   (id 만 다르다)');
O.push('');

const recA = [], recB = [];
new MutationObserver(rs => { for (const r of rs) recA.push(r.addedNodes.length); })
  .observe(A, {childList: true});
new MutationObserver(rs => { for (const r of rs) recB.push(r.addedNodes.length); })
  .observe(B, {childList: true});
const f3 = document.createDocumentFragment();
for (const t of ['라', '마', '바']) f3.appendChild(li(t));
A.appendChild(f3);
for (const t of ['라', '마', '바']) B.appendChild(li(t));
queueMicrotask(() => {
  O.push('조각을 붙였을 때  childList 레코드 = ' + recA.length + '개   addedNodes = [' + recA.join(',') + ']');
  O.push('반복 appendChild  childList 레코드 = ' + recB.length + '개   addedNodes = [' + recB.join(',') + ']');
  O.push('두 결과 트리는 여전히 같은가 = ' + (A.innerHTML === B.innerHTML));
  O.push('A.children.length = ' + A.children.length + '   B.children.length = ' + B.children.length);
  document.body.appendChild(Object.assign(document.createElement('script'),
    {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
});
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-frag.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
DocumentFragment      nodeType = 11   nodeName = #document-fragment   isConnected = false
붙이기 전   frag.childNodes.length = 3   host.children.length = 0
붙인 뒤     frag.childNodes.length = 0   host.children.length = 3
host.innerHTML = <li>가</li><li>나</li><li>다</li>
appendChild(frag) 반환값 === frag = true   반환값.childNodes.length = 0
빈 frag 를 다시 붙이면 host.children.length = 3   (아무 일도 안 한다)
(exit 0)
```

```text
   붙이기 전                    host.appendChild(frag)        붙인 뒤
   frag                                                       frag
    +- <li>가              ----- 자식들만 옮겨 간다 ----->      (비었다)
    +- <li>나                                                  host
    +- <li>다                                                   +- <li>가
   host  (비었다)                                               +- <li>나
                                                                +- <li>다
   ★ appendChild 의 반환값은 frag 자신이고, 그 frag 는 이미 비어 있다
```

그림 해설 (한 단계씩):

- **조각의 `nodeType` 은 11** 이고 `nodeName` 은 `#document-fragment` 다. 요소가 아니다.
- **자식들만 옮겨 가고 조각은 빈다** — 3 에서 **0** 이 됐다. 이것도 [03번 주제](../03-node-creation-insertion-removal/2-summary.md)의 「삽입은 이동」과 같은 규칙이다.
- **반환값은 넣은 노드(즉 조각 자신)** 인데 그 조각은 이미 비어 있다 — `반환값.childNodes.length` 가 **0** 이다. 체이닝해서 다시 쓰려던 코드가 여기서 조용히 아무 일도 안 한다.
- **빈 조각을 다시 붙이면 아무 일도 안 난다.** 에러도 없다.

비용 — 조각을 만드는 것 자체는 싸다. 비교는 (6)에서 잰다.

### (2) 결과 트리가 같다 — 그러면 조각은 무엇을 바꾸나

**언제 쓰나** — 「조각을 쓰면 뭐가 달라지나」를 설명해야 할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-frag.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,12p'
조각에 모아 한 번  hostA.innerHTML = <li>가</li><li>나</li><li>다</li>
반복 appendChild   hostB.innerHTML = <li>가</li><li>나</li><li>다</li>
두 문자열이 같은가 = true
childNodes.length  A = 3   B = 3
outerHTML 바이트 길이  A = 50   B = 50   (id 만 다르다)
(exit 0)
```

```text
   같은 세 항목을 두 경로로 넣었다

   경로 A   frag 에 셋 모으고  hostA.appendChild(frag)       한 번의 삽입
   경로 B   hostB.appendChild 를 세 번                        세 번의 삽입

   결과 트리:   <li>가</li><li>나</li><li>다</li>   ← 한 글자도 같다
   childNodes:  3 대 3                              ← 같다
   outerHTML 길이: 50 대 50                         ← 같다

   ★ 결과로는 두 경로를 구분할 수 없다. 갈리는 것은 '과정' 이다
```

그림 해설 (한 단계씩):

- **결과 트리가 문자열 단위로 같다.** 그래서 「조각을 썼나」를 **결과에서는 알 수 없다.**
- 그러면 무엇이 다른가 — **트리를 바꾼 횟수**다. 그것을 재는 창이 `MutationObserver` 다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-frag.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,17p'
조각을 붙였을 때  childList 레코드 = 1개   addedNodes = [3]
반복 appendChild  childList 레코드 = 3개   addedNodes = [1,1,1]
두 결과 트리는 여전히 같은가 = true
A.children.length = 6   B.children.length = 6
(exit 0)
```

```text
   같은 세 항목을 넣었을 때 관찰자가 받은 레코드

   조각을 붙였을 때   childList 레코드 1개   addedNodes = [3]
   반복 appendChild   childList 레코드 3개   addedNodes = [1,1,1]

   ★ 이것이 조각이 실제로 줄이는 것이다 — '삽입 사건의 수'
      결과 트리는 같고, 관찰자가 보는 사건 수만 1/3 이 된다
```

- ★ 조각이 줄이는 것은 「**삽입 사건의 수**」다. `MutationObserver`·커스텀 요소 반응·프레임워크의 변경 감지가 전부 이 수를 센다(목록의 **37번 주제**·**13번 주제**).
- **이 수는 흔들리지 않는다** — 시간과 달리 명세가 정한 절차의 결과다. 그래서 **비용 이야기보다 이쪽이 더 단단한 근거**다.
- 시간이 줄어드는지는 **별개의 질문**이고 (6)에서 따로 잰다.

### (3) ★ `<template>` — 안이 「다른 문서」에 산다

**언제 쓰나** — 목록 항목의 틀을 마크업으로 두고 싶을 때. **그리고 「틀 안이 안 잡힌다」를 만날 때.**

```html
<!-- wa05b-05-template.html -->
<!doctype html>
<meta charset="utf-8">
<title>05-template</title>
<template id="tpl"><li class="row">항목</li><li class="row">항목</li></template>
<li class="row" id="real">본 문서에 있는 것</li>
<ul id="host"></ul>
<script>
const O = [];
const tpl = document.getElementById('tpl');
const host = document.getElementById('host');
O.push('tpl.childNodes.length          = ' + tpl.childNodes.length + '   (본 트리에서 template 은 비어 있다)');
O.push('tpl.content.nodeType           = ' + tpl.content.nodeType + '   nodeName = ' + tpl.content.nodeName);
O.push('tpl.content.childNodes.length  = ' + tpl.content.childNodes.length);
O.push('document.querySelector("#tpl li")   = ' + document.querySelector('#tpl li'));
O.push('document.querySelectorAll(".row")   = ' + document.querySelectorAll('.row').length + '개  ' +
       '(본 문서에 있는 것만)');
O.push('tpl.content.querySelectorAll(".row") = ' + tpl.content.querySelectorAll('.row').length + '개');
O.push('tpl.innerHTML                  = ' + JSON.stringify(tpl.innerHTML));
O.push('');

const inner = tpl.content.firstElementChild;
O.push('tpl.ownerDocument === document                = ' + (tpl.ownerDocument === document));
O.push('tpl.content.ownerDocument === document        = ' + (tpl.content.ownerDocument === document));
O.push('inner.ownerDocument === document              = ' + (inner.ownerDocument === document));
O.push('tpl.content.ownerDocument.defaultView         = ' + tpl.content.ownerDocument.defaultView);
O.push('tpl.content.ownerDocument.documentElement     = ' + tpl.content.ownerDocument.documentElement);
O.push('tpl.content.ownerDocument.URL                 = ' + JSON.stringify(tpl.content.ownerDocument.URL));
O.push('inner.isConnected = ' + inner.isConnected + '   inner.getBoundingClientRect().width = ' +
       inner.getBoundingClientRect().width);
O.push('');

const copy = tpl.content.cloneNode(true);
O.push('cloneNode(true) 한 조각.ownerDocument === document = ' + (copy.ownerDocument === document));
host.appendChild(copy);
O.push('붙인 뒤 host.children.length = ' + host.children.length);
O.push('붙인 노드.ownerDocument === document = ' + (host.firstElementChild.ownerDocument === document) +
       '   isConnected = ' + host.firstElementChild.isConnected);
O.push('붙인 뒤 document.querySelectorAll(".row") = ' + document.querySelectorAll('.row').length + '개');
O.push('tpl.content.childNodes.length = ' + tpl.content.childNodes.length + '   (원본은 안 줄었다)');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
tpl.childNodes.length          = 0   (본 트리에서 template 은 비어 있다)
tpl.content.nodeType           = 11   nodeName = #document-fragment
tpl.content.childNodes.length  = 2
document.querySelector("#tpl li")   = null
document.querySelectorAll(".row")   = 1개  (본 문서에 있는 것만)
tpl.content.querySelectorAll(".row") = 2개
tpl.innerHTML                  = "<li class=\"row\">항목</li><li class=\"row\">항목</li>"
(exit 0)
```

```text
   창 ① --dump-dom 으로 본 트리
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '1,6p'
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>05-template</title>
<template id="tpl"><li class="row">항목</li><li class="row">항목</li></template>
</head><body><li class="row" id="real">본 문서에 있는 것</li>
<ul id="host"><li class="row">항목</li><li class="row">항목</li></ul>
(exit 0)
```

그림 해설 (한 단계씩):

- **`tpl.childNodes.length` 가 0** 이다. 파서가 내용을 **`template` 의 자식으로 넣지 않았다.**
- 내용은 **`tpl.content`** 라는 `DocumentFragment` 안에 있다 — `nodeType` 이 **11** 이다.
- **`document.querySelector('#tpl li')` 가 `null`** 이고 `document.querySelectorAll('.row')` 도 본 문서의 **1개**만 센다.
- ★ **직렬화된 트리에는 내용이 보인다.** `--dump-dom` 이 `<template>` 태그 안에 내용을 찍는다 — **창 ① 만 보면 「본 트리에 있다」로 읽힌다.** 이것이 창 ① 의 사각지대다.

**그러면 왜 안 잡히나 — 창 ④ 로 묻는다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,15p'
tpl.ownerDocument === document                = true
tpl.content.ownerDocument === document        = false
inner.ownerDocument === document              = false
tpl.content.ownerDocument.defaultView         = null
tpl.content.ownerDocument.documentElement     = null
tpl.content.ownerDocument.URL                 = "about:blank"
inner.isConnected = false   inner.getBoundingClientRect().width = 0
(exit 0)
```

```text
   ownerDocument 로 물으면 한 줄로 갈린다

   tpl            ownerDocument === document   true    ← 본 문서의 요소다
   tpl.content    ownerDocument === document   false   ← ★ 다른 문서다
   그 안의 <li>   ownerDocument === document   false

   그 '다른 문서' 는
     defaultView     = null        ← window 가 없다 (브라우징 문맥이 없다)
     documentElement = null        ← <html> 조차 없다
     URL             = about:blank

   ★ 이 한 칸이 '왜 안 잡히나' 와 '왜 안 도나' 를 동시에 설명한다
```

- **명세가 「template contents owner document」라는 별도의 문서를 만들라고 정한다.** 구현이 고른 동작이 아니다.
- `querySelector` 는 **자기 문서 안**만 본다. 다른 문서에 있으니 안 잡히는 것이 당연하다([02번 주제](../02-element-queries-and-live-collections/2-summary.md)).
- **`getBoundingClientRect().width` 가 0** 이다 — 렌더 트리에 없다. `isConnected` 도 `false` 다.

**찍어 내면 본 문서의 것이 된다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '17,21p'
cloneNode(true) 한 조각.ownerDocument === document = false
붙인 뒤 host.children.length = 2
붙인 노드.ownerDocument === document = true   isConnected = true
붙인 뒤 document.querySelectorAll(".row") = 3개
tpl.content.childNodes.length = 2   (원본은 안 줄었다)
(exit 0)
```

- **복제본의 `ownerDocument` 는 아직 다른 문서**인데, **붙이는 순간 본 문서로 입양**된다(`true` 로 바뀐다).
- **원본은 안 줄어든다** — `tpl.content.childNodes.length` 가 그대로 2 다. 조각과 갈리는 자리가 정확히 여기다.
- 붙인 뒤에는 `document.querySelectorAll('.row')` 가 **3개**를 센다.

비용 — 복제는 하위 트리 크기에 비례한다. (6)에서 잰다.

### (4) ★ 틀 안은 돌지 않는다 — 창 ⑤ 로 증명한다

**언제 쓰나** — 「사용자 마크업을 `<template>` 에 담으면 안전한가」를 판단할 때.

```html
<!-- wa05b-05-inert.html -->
<!doctype html>
<meta charset="utf-8">
<title>05-inert</title>
<script>window.C = {tplScript: 0, tplImg: 0, plainScript: 0, plainImg: 0};</script>
<template id="tpl"><script>window.C.tplScript++;</script><img id="ti" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" onload="window.C.tplImg++"></template>
<div id="plain"><script>window.C.plainScript++;</script><img id="pi" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" onload="window.C.plainImg++"></div>
<div id="host"></div>
<script>
const O = [];
const tpl = document.getElementById('tpl');
const ti = tpl.content.querySelector('#ti');
const pi = document.getElementById('pi');
const host = document.getElementById('host');
const 파싱직후 = {tplScript: C.tplScript, plainScript: C.plainScript,
                  script노드: tpl.content.querySelector('script').tagName};
host.appendChild(tpl.content.cloneNode(true));
window.addEventListener('load', () => setTimeout(() => {
  O.push('같은 마크업을 template 안과 보통 div 안에 하나씩 두었다');
  O.push('파싱이 끝난 시점 script 실행 횟수   template 안 = ' + 파싱직후.tplScript +
         '   보통 div 안 = ' + 파싱직후.plainScript);
  O.push('load 뒤 template 안 img   complete = ' + ti.complete + '   naturalWidth = ' + ti.naturalWidth +
         '   currentSrc = ' + JSON.stringify(ti.currentSrc));
  O.push('load 뒤 보통 div 안 img   complete = ' + pi.complete + '   naturalWidth = ' + pi.naturalWidth +
         '   currentSrc 길이 = ' + pi.currentSrc.length);
  O.push('template 안 script 노드 자체는 있나 = ' + 파싱직후.script노드 +
         '   img 노드 = ' + ti.tagName + '   (둘 다 트리에 있다)');
  O.push('');
  O.push('cloneNode(true) 로 복제해 본 문서에 붙인 뒤 (load 까지 기다렸다)');
  const ci = host.querySelector('img'), cs = host.querySelector('script');
  O.push('script 실행 횟수 = ' + C.tplScript + '   (붙이기 전에는 ' + 파싱직후.tplScript + ' 이었다)');
  O.push('붙인 img   complete = ' + ci.complete + '   naturalWidth = ' + ci.naturalWidth +
         '   onload 횟수 = ' + C.tplImg);
  O.push('붙인 script 의 textContent = ' + JSON.stringify(cs.textContent));
  O.push('host.children.length = ' + host.children.length + '   C = ' + JSON.stringify(C));
  document.body.appendChild(Object.assign(document.createElement('script'),
    {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
}, 0));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-inert.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,5p'
같은 마크업을 template 안과 보통 div 안에 하나씩 두었다
파싱이 끝난 시점 script 실행 횟수   template 안 = 0   보통 div 안 = 1
load 뒤 template 안 img   complete = true   naturalWidth = 0   currentSrc = ""
load 뒤 보통 div 안 img   complete = true   naturalWidth = 1   currentSrc 길이 = 78
template 안 script 노드 자체는 있나 = SCRIPT   img 노드 = IMG   (둘 다 트리에 있다)
(exit 0)
```

```text
   같은 마크업을 두 자리에 두고 '돌았나' 를 셌다

                        script 실행    img naturalWidth    img currentSrc
   보통 <div> 안          1              1                  (78자 data URI)
   <template> 안          0              0                  ""     ← 요청 자체가 없다

   노드는?   tpl.content.querySelector('script') = SCRIPT   ← 트리에는 있다
             tpl.content.querySelector('img')    = IMG

   ★ 창 ①·② 는 '있다' 라고 답한다. '안 돌았다' 는 창 ⑤ 만 말한다
```

그림 해설 (한 단계씩):

- **`<script>` 가 한 번도 안 돌았다**(0). 노드는 트리에 있다.
- **`<img>` 는 요청조차 없었다** — `currentSrc` 가 **빈 문자열**이고 `naturalWidth` 가 **0** 이다. 「불러오다 실패」가 아니라 「**시작도 안 했다**」다.
- ★ **`complete` 는 `true` 다.** 이미지가 다 왔다는 뜻이 아니라 **할 일이 없다는 뜻**이다 — 이 프로퍼티만 보고 판단하면 정반대로 읽는다.
- 이유는 (3)의 한 칸이다 — **브라우징 문맥이 없는 문서**에서는 스크립트 준비도 리소스 가져오기도 일어나지 않는다.

**그런데 찍어서 붙이면 돈다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-inert.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '7,11p'
cloneNode(true) 로 복제해 본 문서에 붙인 뒤 (load 까지 기다렸다)
script 실행 횟수 = 1   (붙이기 전에는 0 이었다)
붙인 img   complete = true   naturalWidth = 1   onload 횟수 = 1
붙인 script 의 textContent = "window.C.tplScript++;"
host.children.length = 2   C = {"tplScript":1,"tplImg":1,"plainScript":1,"plainImg":1}
(exit 0)
```

```text
   cloneNode(true) 로 복제해 본 문서에 붙였더니

   script 실행 횟수   0  ->  1        ★ 돈다
   img naturalWidth   0  ->  1        ★ 실제로 가져왔다

   04번의 '이미 시작된' 표시와 대비하라
     파서가 본 문서에 만든 <script>  ->  표시가 찍혀 있어 옮겨도 안 돈다
     <template> 안의 <script>        ->  준비된 적이 없으니 표시도 없다. 붙이면 돈다
```

- ★ **「`<template>` 에 담으면 안전하다」는 틀렸다.** 담는 동안만 안전하고 **찍어 붙이는 순간 실행된다.**
- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)가 실측한 「파싱으로 만들어진 `script` 는 옮겨도 안 돈다」와 **결과가 반대**다. 같은 「파서가 만든 `script`」인데 갈린다 — **준비(prepare) 단계를 지났느냐**가 축이다.
- 그래서 **`<template>` 은 XSS 방어 수단이 아니다.** 방어는 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)의 결론대로 **문자열을 마크업으로 안 넣는 것**이다.

### (5) `cloneNode`·`importNode`·`adoptNode` — 셋이 하는 일

**언제 쓰나** — 틀에서 찍어 낼 때, 그리고 `<iframe>` 의 노드를 가져올 때.

```html
<!-- wa05b-05-clone.html -->
<!doctype html>
<meta charset="utf-8">
<title>05-clone</title>
<template id="tpl"><li class="row">항목</li><li class="row">항목</li></template>
<iframe id="fr" srcdoc="<p id=p1>프레임 안 문단</p><p id=p2>또 하나</p>"></iframe>
<div id="h1"></div><div id="h2"></div><div id="h3"></div>
<script>
const O = [];
const tpl = document.getElementById('tpl');
const c = tpl.content.cloneNode(true);
const i1 = document.importNode(tpl.content, true);
const i0 = document.importNode(tpl.content);
O.push('cloneNode(true)        ownerDocument === document = ' + (c.ownerDocument === document) +
       '   childNodes = ' + c.childNodes.length);
O.push('importNode(content, true)  ownerDocument === document = ' + (i1.ownerDocument === document) +
       '   childNodes = ' + i1.childNodes.length);
O.push('importNode(content)        (두 번째 인자 생략)        ' +
       '   childNodes = ' + i0.childNodes.length);
O.push('원본 tpl.content.childNodes = ' + tpl.content.childNodes.length + '   (둘 다 원본을 안 건드린다)');
document.getElementById('h1').appendChild(c);
document.getElementById('h2').appendChild(i1);
O.push('둘 다 붙인 뒤 h1.innerHTML === h2.innerHTML = ' +
       (document.getElementById('h1').innerHTML === document.getElementById('h2').innerHTML));
O.push('붙인 뒤 h1 자식.ownerDocument === document = ' +
       (document.getElementById('h1').firstElementChild.ownerDocument === document) +
       '   (삽입이 입양을 대신 해 준다)');
O.push('');
window.addEventListener('load', () => setTimeout(() => {
  const fd = document.getElementById('fr').contentDocument;
  const p1 = fd.getElementById('p1'), p2 = fd.getElementById('p2');
  const 복사 = document.importNode(p1, true);
  O.push('다른 문서(iframe)의 노드를 가져온다 — 프레임 안 <p> 수 = ' + fd.querySelectorAll('p').length);
  O.push('importNode(p1, true)   결과.ownerDocument === document = ' + (복사.ownerDocument === document) +
         '   원본 p1 은 프레임에 남았나 = ' + (p1.ownerDocument === fd));
  const 이동 = document.adoptNode(p2);
  O.push('adoptNode(p2)          결과 === p2 = ' + (이동 === p2) +
         '   p2.ownerDocument === document = ' + (p2.ownerDocument === document));
  O.push('adoptNode 뒤 프레임 안 <p> 수 = ' + fd.querySelectorAll('p').length + '   (원본이 빠졌다)');
  document.getElementById('h3').append(복사, 이동);
  O.push('h3.innerHTML = ' + document.getElementById('h3').innerHTML);
  O.push('h3 자식 둘의 ownerDocument === document = ' +
         [...document.getElementById('h3').children].map(e => e.ownerDocument === document).join(', '));
  document.body.appendChild(Object.assign(document.createElement('script'),
    {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
}, 0));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-clone.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
cloneNode(true)        ownerDocument === document = false   childNodes = 2
importNode(content, true)  ownerDocument === document = true   childNodes = 2
importNode(content)        (두 번째 인자 생략)           childNodes = 0
원본 tpl.content.childNodes = 2   (둘 다 원본을 안 건드린다)
둘 다 붙인 뒤 h1.innerHTML === h2.innerHTML = true
붙인 뒤 h1 자식.ownerDocument === document = true   (삽입이 입양을 대신 해 준다)
(exit 0)
```

```text
                      새 노드를 만드나   결과의 ownerDocument   원본은
   cloneNode(true)      만든다            원본과 같은 문서       그대로
   importNode(n, true)  만든다            내 문서                그대로
   adoptNode(n)         ★ 안 만든다       내 문서                ★ 옮겨진다(빠진다)

   ★ importNode 의 두 번째 인자를 생략하면 얕다 — childNodes 가 0 이다
```

그림 해설 (한 단계씩):

- **`cloneNode` 와 `importNode` 의 유일한 차이는 결과의 `ownerDocument`** 다. 그런데 **붙이는 순간 삽입이 입양을 대신 해 주므로**, 곧바로 붙일 것이면 **결과 트리가 같다**(출력의 `h1.innerHTML === h2.innerHTML` 이 `true`).
- ★ **`importNode(node)` 는 얕다.** `cloneNode` 와 달리 두 번째 인자를 자주 빠뜨리는 자리다 — 실측에서 `childNodes` 가 **0** 이었다.
- **`adoptNode` 는 복사가 아니라 이동**이다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-clone.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,13p'
다른 문서(iframe)의 노드를 가져온다 — 프레임 안 <p> 수 = 2
importNode(p1, true)   결과.ownerDocument === document = true   원본 p1 은 프레임에 남았나 = true
adoptNode(p2)          결과 === p2 = true   p2.ownerDocument === document = true
adoptNode 뒤 프레임 안 <p> 수 = 1   (원본이 빠졌다)
h3.innerHTML = <p id="p1">프레임 안 문단</p><p id="p2">또 하나</p>
h3 자식 둘의 ownerDocument === document = true, true
(exit 0)
```

- **`importNode` 는 원본을 프레임에 남긴다**(`p1.ownerDocument === fd` 가 `true`).
- **`adoptNode` 는 원본을 빼 간다** — 프레임 안 `<p>` 수가 2 에서 **1** 로 줄었다.
- 붙인 뒤에는 둘 다 본 문서의 것이 된다.

비용 — 깊은 복제는 하위 트리 크기에 비례한다. 절대 수치는 이 문서가 재지 않았다.

### (6) ★ 비용 — 「조각이 빠르다」를 다시 쟀다

**언제 쓰나** — 「조각에 모아 넣으면 빠르다」를 말하기 전에.

[04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)가 이미 한 번 쟀고 **재현되지 않았다.** 이 문서는 그 사실을 이어받아 **조건을 셋으로 늘려 다시 쟀다.**

```html
<!-- wa05b-05-cost.html -->
<!doctype html>
<meta charset="utf-8">
<title>05-cost</title>
<template id="tpl"><li class="row"><b>항목</b></li></template>
<ul id="host"></ul>
<script>
const N = 9, COUNT = 2000, LAY = 400;
const O = [];
const tpl = document.getElementById('tpl');
const host = document.getElementById('host');
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const med = a => a.slice().sort((x, y) => x - y)[(a.length - 1) >> 1];
const mk = () => { const li = document.createElement('li'); li.className = 'row';
                   li.appendChild(Object.assign(document.createElement('b'), {textContent: '항목'})); return li; };
const bench = (label, fn, host2) => {
  const t = [];
  for (let r = 0; r < N; r++) {
    (host2 || host).textContent = '';
    const s = performance.now();
    fn();
    t.push(performance.now() - s);
  }
  O.push(padw(label, 40) + '중앙값 ' + med(t).toFixed(2).padStart(8) + ' ms' +
         '   최소 ' + Math.min(...t).toFixed(2).padStart(8) + '   최대 ' + Math.max(...t).toFixed(2).padStart(8));
};
const detached = document.createElement('ul');

O.push('일괄 삽입 — ' + COUNT + '개 항목 · ' + N + '판의 중앙값 · 부모가 트리 안');
O.push('');
bench('반복 appendChild', () => { for (let i = 0; i < COUNT; i++) host.appendChild(mk()); });
bench('DocumentFragment 에 모아 한 번', () => { const f = document.createDocumentFragment();
  for (let i = 0; i < COUNT; i++) f.appendChild(mk()); host.appendChild(f); });
bench('template 복제를 항목마다 붙이기', () => { for (let i = 0; i < COUNT; i++) host.appendChild(tpl.content.cloneNode(true)); });
bench('template 복제를 조각에 모아 한 번', () => { const f = document.createDocumentFragment();
  for (let i = 0; i < COUNT; i++) f.appendChild(tpl.content.cloneNode(true)); host.appendChild(f); });
O.push('');
O.push('같은 것을 부모가 트리 밖(detached)일 때');
bench('반복 appendChild (트리 밖 부모)', () => { for (let i = 0; i < COUNT; i++) detached.appendChild(mk()); }, detached);
bench('DocumentFragment (트리 밖 부모)', () => { const f = document.createDocumentFragment();
  for (let i = 0; i < COUNT; i++) f.appendChild(mk()); detached.appendChild(f); }, detached);
O.push('');

O.push('삽입 사이에 레이아웃이 도는 조건 — ' + LAY + '개 항목 · ' + N + '판의 중앙값');
O.push('   (항목을 넣을 때마다 host.offsetHeight 를 읽어 레이아웃을 강제한다)');
O.push('');
let sink = 0;
bench('반복 appendChild + 매번 offsetHeight', () => {
  for (let i = 0; i < LAY; i++) { host.appendChild(mk()); sink += host.offsetHeight; } });
bench('조각에 모아 한 번 + 끝에 한 번만', () => {
  const f = document.createDocumentFragment();
  for (let i = 0; i < LAY; i++) f.appendChild(mk());
  host.appendChild(f); sink += host.offsetHeight; });
bench('반복 appendChild + 끝에 한 번만', () => {
  for (let i = 0; i < LAY; i++) host.appendChild(mk()); sink += host.offsetHeight; });
O.push('');
O.push('sink = ' + (sink > 0) + '   (읽은 값을 버리지 않았다는 확인)');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-cost.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,10p'
일괄 삽입 — 2000개 항목 · 9판의 중앙값 · 부모가 트리 안

반복 appendChild                        중앙값     2.80 ms   최소     2.60   최대     6.30
DocumentFragment 에 모아 한 번          중앙값     3.20 ms   최소     2.90   최대     4.60
template 복제를 항목마다 붙이기         중앙값     2.40 ms   최소     2.10   최대     3.40
template 복제를 조각에 모아 한 번       중앙값     2.70 ms   최소     2.40   최대     3.20

같은 것을 부모가 트리 밖(detached)일 때
반복 appendChild (트리 밖 부모)         중앙값     2.30 ms   최소     2.10   최대     3.80
DocumentFragment (트리 밖 부모)         중앙값     2.70 ms   최소     2.30   최대     3.50
(exit 0)
```

```text
   일괄 삽입 — 2000개 항목 · 9판의 중앙값 (수치는 흔들린다. 자릿수와 순위만 읽어라)

   반복 appendChild                 ~3 ms 대
   DocumentFragment 에 모아 한 번    ~3 ms 대     ★ 같은 자릿수
   template 복제를 항목마다          ~3 ms 대
   template 복제를 조각에 모아       ~3 ms 대
   부모가 트리 밖일 때도 둘 다       ~3 ms 대     ★ 조건을 바꿔도 안 갈렸다

   세 판을 돌렸더니 순위가 판마다 뒤집혔다 — 신호가 잡음보다 작다
```

그림 해설 (한 단계씩):

- ★ **「조각이 빠르다」는 이 측정에서 다시 재현되지 않았다.** 04번의 결과를 그대로 확인한 것이다.
- **부모가 트리 밖(`detached`)일 때도 안 갈렸다** — 04번이 「못 찾았다」고 적어 둔 조건을 실제로 던져 본 것인데 **여기서도 아니었다.**
- **`template` 복제도 `createElement` 반복과 같은 자릿수**였다.

**그런데 갈리는 조건이 하나 있었다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-cost.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,19p'
삽입 사이에 레이아웃이 도는 조건 — 400개 항목 · 9판의 중앙값
   (항목을 넣을 때마다 host.offsetHeight 를 읽어 레이아웃을 강제한다)

반복 appendChild + 매번 offsetHeight    중앙값    34.70 ms   최소    33.60   최대    95.70
조각에 모아 한 번 + 끝에 한 번만        중앙값     6.20 ms   최소     5.80   최대    10.50
반복 appendChild + 끝에 한 번만         중앙값     6.80 ms   최소     5.80   최대    11.40

sink = true   (읽은 값을 버리지 않았다는 확인)
(exit 0)
```

```text
   삽입 사이에 레이아웃이 도는 조건 — 400개 항목 · 9판의 중앙값

   반복 appendChild + 매번 offsetHeight   ~40~50 ms    ★ 한 자릿수 크다
   조각에 모아 한 번 + 끝에 한 번만        ~6~7 ms
   반복 appendChild + 끝에 한 번만         ~6~7 ms     ★ 조각 없이도 같다

   ★ 이기는 것은 '조각' 이 아니라 '읽기를 안 섞는 것' 이다
      아래 두 줄은 삽입 횟수가 400 대 1 인데 시간이 같다
```

- ★★ **결론이 직관과 다르다.** 비싼 것은 **삽입 횟수가 아니라 읽기·쓰기 교차**였다. 아래 두 줄은 **삽입을 400번 한 쪽과 1번 한 쪽**인데 시간이 같다.
- **그래서 이 문서는 「조각을 쓰면 빨라진다」를 주장하지 않는다.** 주장하는 것은 두 가지다 — **삽입 사건 수가 1/N 이 된다**(위 (2), 안 흔들리는 근거)와 **읽기를 섞지 마라**(목록의 **10번 주제**).
- **`performance.now()` 의 분해능은 100마이크로초**다. 이 표의 어떤 칸도 그 아래로 내려가지 않았으므로 여기서는 분해능이 문제되지 않았다.

비용 — 이 절 자체가 비용이다. **9판·중앙값·최소·최대**를 실었고 **자릿수와 순위만 결론으로** 쓴다.

```html demo
<template id="tpl-demo"><li class="chip">찍어 낸 항목</li></template>
<ul id="list-demo"></ul>
<button id="stamp">틀에서 하나 찍기</button>
<style>
  #list-demo { min-height: 24px; border: 2px dashed #94a3b8; padding: 6px; margin-bottom: 8px; }
  .chip { background: #2563eb; color: #fff; padding: 2px 8px; border-radius: 6px; margin: 2px 0; list-style: none; }
</style>
<script>
  document.getElementById('stamp').onclick = () =>
    document.getElementById('list-demo').appendChild(
      document.getElementById('tpl-demo').content.cloneNode(true));
</script>
```

> **보이는 것** — 처음에는 점선 상자가 **비어 있다.** `<template>` 안에 `<li>` 가 하나 있는데도 화면에 안 그려진다. 버튼을 누를 때마다 파란 알약 모양의 「찍어 낸 항목」이 상자 안에 **하나씩 쌓인다.** 몇 번을 눌러도 틀은 줄지 않는다.\
> **바꿔 볼 것** — `content.cloneNode(true)` 를 `content` 로 바꾸면 **첫 번째만 항목이 생기고 두 번째부터는 아무 일도 안 일어난다**(조각이 비기 때문이다 — 위 (1)의 실측과 같은 일이다) · `cloneNode(true)` 를 `cloneNode(false)` 로 바꾸면 **아무것도 안 생긴다**(얕은 복제라 자식이 안 온다).

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
document.createDocumentFragment()        // 빈 조각
new DocumentFragment()                   // 같은 것 (생성자도 있다)

frag.appendChild(node)                   // 조각에 담는다
parent.appendChild(frag)                 // 자식들만 옮겨 가고 조각이 빈다

tpl.content                              // DocumentFragment · 다른 문서 소속
tpl.content.cloneNode(true)              // 찍어 낸다 (원본은 그대로)
document.importNode(tpl.content, true)   // 찍어 내며 내 문서로 입양한다
document.adoptNode(node)                 // 복사 없이 소속만 옮긴다 (원본이 빠진다)

frag.querySelector(sel)                  // 조각 안을 찾는다 (document 로는 못 찾는다)
frag.getElementById(id)                  // 조각에도 있다
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
list.appendChild(frag); list.appendChild(frag);   // 두 번째는 아무 일도 안 한다
const f = frag(); loop { host.appendChild(f); }   // 첫 판만 동작한다
document.querySelector('#tpl li');                // null — 다른 문서에 있다
host.appendChild(tpl.content);                    // 틀이 비어 버린다 (두 번 못 쓴다)
document.importNode(tpl.content);                 // 얕다 — 자식이 안 온다
tpl.innerHTML = '<li>x</li>';                     // content 에 들어간다 (자식이 아니다)
```

- ★ **`host.appendChild(tpl.content)` 가 가장 조용한 사고**다. 첫 번째 목록은 잘 그려지고 **두 번째부터 빈다.**
- **`replaceChildren(...frag.childNodes)`** 처럼 조각의 자식을 **펼쳐** 넘기면 조각을 안 비우고 쓸 수 있다.

### 어디서 헷갈리나

- **`template` 과 `template.content` 는 다른 것**이다. 앞은 본 문서의 요소, 뒤는 다른 문서의 조각이다.
- **`<template>` 은 「숨긴 마크업」이 아니다.** `display: none` 과 전혀 다르다 — 그쪽은 본 문서에 있고 스크립트도 돈다.
- **`cloneNode` 의 인자도 `importNode` 의 두 번째 인자도** 「깊게」인데, `importNode` 만 기본값이 얕다.
- **조각은 요소가 아니다.** `frag.innerHTML` 은 없다. `frag.firstElementChild` 는 있다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 중 다섯이 **에러 없이 조용히 어긋난다.**

### 1. 같은 조각을 두 번 붙인다

첫 번째에서 **조각이 비므로** 두 번째는 아무 일도 안 한다. 실측에서 `childNodes.length` 가 3 에서 **0** 이 됐다.

### 2. `tpl.content` 를 그대로 붙인다

**틀이 비어 버린다.** 복제를 붙였어야 한다. 첫 렌더는 성공하므로 **재렌더에서야 드러난다.**

### 3. `document.querySelector` 로 틀 안을 찾는다

**`null` 이다.** 다른 문서에 있다. `tpl.content.querySelector` 를 써야 한다.

### 4. `<template>` 에 담으면 안전하다고 믿는다

**담는 동안만** 안전하다. 실측에서 복제해 붙이자 `script` 가 **돌았고** `img` 가 **받아졌다.**

### 5. `--dump-dom` 트리를 보고 「본 트리에 있다」고 읽는다

직렬화는 `<template>` **태그 안에 내용을 찍는다.** 창 ① 만으로는 안 갈린다 — **창 ④ 가 필요하다.**

### 6. 「조각을 쓰면 빨라진다」를 근거 없이 적는다

실측에서 **같은 자릿수**였고 판마다 순위가 뒤집혔다. 재지 않고 말하면 그게 날조다.

## 구현 세부사항 대 언어 보장

여기서 「언어 보장」은 **명세(WHATWG DOM·HTML)가 정한 것**이고, 「구현」은 **Blink 가 하는 것**이다.

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 조각을 넣으면 **자식들만** 들어가고 조각이 비는 것 | **명세**(DOM 「insert」 — 조각이면 자식을 전부 옮긴다) |
| 조각의 `nodeType` 이 **11** 인 것 | **명세**(DOM 「Node」 상수표) |
| `template.content` 가 **별도의 문서** 소속인 것 | **명세**(HTML 「template contents owner document」) |
| 그 문서에 **브라우징 문맥이 없어** 스크립트·리소스가 안 도는 것 | **명세**(HTML — 그 문서는 브라우징 문맥이 없다) |
| 복제한 `<script>` 를 붙이면 **도는 것** | **명세**(HTML 「prepare the script element」 — 준비된 적 없으므로 「이미 시작된」 표시가 없다) |
| `cloneNode` 결과가 **원본과 같은 문서** 소속인 것 | **명세**(DOM 「clone a node」 — node document 를 쓴다) |
| `importNode` 가 **입양까지** 하는 것 · 기본이 **얕은** 것 | **명세**(DOM `importNode(node, deep = false)`) |
| `adoptNode` 가 **원본을 옮기는** 것 | **명세**(DOM 「adopt」) |
| 삽입이 **입양을 대신 해 주는** 것 | **명세**(DOM 「pre-insert」 가 adopt 를 부른다) |
| `MutationObserver` 레코드가 **1개 대 3개**인 것 | **명세**(DOM — 조각 삽입은 한 번의 childList 변경이다) |
| `img.complete` 가 요청 전에도 **`true`** 인 것 | **명세**(HTML — 할 일이 없으면 `complete` 다). 직관과 반대이므로 근거로 쓰지 않는다 |
| **`--dump-dom` 이 template 내용을 찍는 것** | **명세**(HTML 직렬화가 `content` 를 찍는다) + Chrome 의 출력 형식 |
| **모든 시간 수치** | **관찰**. 재현되는 것은 자릿수와 순위뿐이다 |
| `performance.now()` 가 **100마이크로초**로 뭉개지는 것 | **구현**(Blink 의 타이머 정책) |
| `getComputedStyle().length` 같은 **개수 값** | 이 주제에서는 쓰지 않았다([08번 주제](../08-getcomputedstyle/2-summary.md)의 몫) |

**도구가 못 보는 것**

- **`--dump-dom`**(창 ①)은 「돌았나」를 못 본다. `<template>` 안의 `script`·`img` 가 **트리에 그대로 찍힌다.**
- **`childNodes.length`**(창 ②)도 못 본다. 개수는 정상이다.
- **`ownerDocument`**(창 ④)는 「안 돌았다」를 **설명**하지만 **증명**하지는 않는다 — 증명은 창 ⑤(실행 계수기)다.
- **`performance.now()`**(창 ⑥)는 100마이크로초 아래를 못 본다. 그리고 **판마다 순위가 뒤집히는 구간에서는 아무것도 말해 주지 않는다.**
- **이 환경은 엔진이 하나**다. 「모든 브라우저가 그렇다」는 이 문서가 못 보는 것이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 노드 여러 개를 한 번에 넣는다 | `append(a, b, c)` · `DocumentFragment` | 반복문 안에서 조각 하나 돌려 쓰기 |
| 같은 모양을 **여러 번** 찍는다 | `<template>` + `content.cloneNode(true)` | 조각(한 번 쓰면 빈다) |
| 마크업으로 틀을 두고 싶다 | `<template>` | `display: none` 인 `<div>`(스크립트·이미지가 돈다) |
| 다른 문서의 노드를 **복사**해 온다 | `importNode(n, true)` | `cloneNode` 뒤 소속을 신경 쓰기(삽입이 해 준다) |
| 다른 문서의 노드를 **옮겨** 온다 | `adoptNode(n)` | 원본이 남을 거라 기대하기 |
| 틀 안을 찾는다 | `tpl.content.querySelector(...)` | `document.querySelector('#tpl ...')` |
| 목록을 빠르게 그린다 | **읽기를 안 섞는다** | 「조각을 쓰면 빨라진다」에 기대기 |
| 신뢰할 수 없는 마크업을 다룬다 | 문자열을 마크업으로 안 넣는다 | `<template>` 에 담아 두기(찍으면 돈다) |

판단 규칙 두 줄.

- **「이것을 몇 번 쓸 것인가」를 먼저 묻는다.** 한 번이면 조각, 여러 번이면 틀이다.
- **「이 노드는 어느 문서 소속인가」를 묻는다.** 안 잡히는 것·안 도는 것이 대개 그 한 칸에서 설명된다.

## 핵심 문장

- **조각은 넣으면 빈다.** 자식들만 옮겨 가고 자신은 트리에 안 들어간다 — 그래서 같은 조각을 두 번 붙이면 두 번째는 아무 일도 안 한다.
- **`<template>` 의 내용은 `content` 안에, 그것도 별도의 문서에 있다.** `document.querySelector` 로 안 잡히는 것이 그 한 칸의 결과다 — 실측에서 `ownerDocument === document` 가 **`false`** 였다.
- **그 문서에는 브라우징 문맥이 없어** `<script>` 가 안 돌고 `<img>` 는 **요청조차 없다**(`currentSrc` 가 빈 문자열). 실측 실행 횟수가 **0 대 1** 이었다.
- ★ **그러나 복제해서 붙이면 돈다**(0 → 1). `<template>` 은 XSS 방어 수단이 아니다.
- **`cloneNode` 와 `importNode` 의 차이는 결과의 `ownerDocument` 하나**이고, 곧바로 붙일 것이면 삽입이 입양을 대신 해 주므로 결과가 같다. **`importNode` 는 기본이 얕다.**
- **`adoptNode` 는 복사가 아니라 이동**이다 — 원본이 원래 문서에서 빠진다.
- **조각과 반복 삽입의 결과 트리는 한 글자도 같다.** 갈리는 것은 `MutationObserver` 레코드 수(**1 대 3**)다 — 이것이 조각이 실제로 줄이는 것이다.
- ★ **「조각이 빠르다」는 이 판에서도 재현되지 않았다.** 갈린 조건은 조각의 유무가 아니라 **읽기·쓰기 교차**였고, 삽입 400번과 1번의 시간이 같았다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 05번)
- [03번 주제](../03-node-creation-insertion-removal/2-summary.md) — **삽입의 의미**가 정본. 그쪽은 「넣기는 옮기기」까지, 여기는 **묶음 삽입 설계와 틀**부터
- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) — **비용 측정 방법과 XSS 실행 계수기**의 정본. 그쪽의 창 넷·다섯을 여기서 빌려 썼고, **「조각이 빠르다」가 재현 안 된 사실**도 그쪽에서 이어받았다
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md) — `querySelector` 가 **어느 범위**를 보는지의 정본. 틀 안이 안 잡히는 것은 그 규칙의 결과다
- [01번 주제](../01-document-and-node-tree/2-summary.md) — `nodeType`·`ownerDocument`·`isConnected` 의 정본
- 목록의 **10번 주제**(레이아웃 스래싱) — **읽기·쓰기 교차 비용**의 정본. 여기는 그 비용이 삽입 비용을 덮는다는 사실만 보인다
- 목록의 **12번 주제**(Shadow DOM) — 선언적 Shadow DOM 이 `<template shadowrootmode>` 로 온다. **경계의 다른 종류**다
- 목록의 **13번 주제**(커스텀 요소 수명주기) — 틀을 찍어 붙일 때 **업그레이드가 언제 도는가**는 그쪽
- 목록의 **37번 주제**(`MutationObserver`) — 여기서 근거로 쓴 **레코드 수**의 정본
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **10번**(`<template>`·`<slot>` 마크업) — **마크업으로서의 `<template>`** 은 그쪽. 여기는 **스크립트가 그것을 어떻게 다루나**만
- JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **01번**(값과 타입) — `null` 과 `undefined` 의 의미 차이는 그쪽

## 용어 풀이

- **`DocumentFragment`** — 부모 없는 임시 노드 자루. 삽입하면 자식들만 옮겨 가고 자신은 빈다. `nodeType` 은 11.
- **`<template>`** — 파서가 만들되 내용을 본 트리에 넣지 않는 요소. 내용은 `content` 안에 있다.
- **template contents owner document** — `template.content` 가 소속된 별도의 문서. 명세가 이름 붙인 것이다.
- **브라우징 문맥(browsing context)** — 문서를 띄우는 창·프레임. 이것이 없으면 스크립트도 리소스 요청도 없다.
- **불활성(inert)** — 스크립트·리소스가 돌지 않는 상태. 이 문서에서는 틀 안의 성질을 가리킨다.
- **입양(adopt)** — 노드의 소속 문서를 바꾸는 절차. 삽입이 자동으로 불러 준다.
- **`importNode`** — 복사 + 입양. 두 번째 인자를 안 주면 얕다.
- **`adoptNode`** — 복사 없이 소속만 바꾼다. 원본이 원래 자리에서 빠진다.
- **`MutationObserver`** — 트리 변경을 레코드로 모아 알려 주는 관찰자. 이 문서에서는 **삽입 사건 수**를 세는 데 썼다.
- **`complete`(이미지)** — 「할 일이 남았나」를 답하는 플래그. **「받아졌나」가 아니다.**
- **분해능(resolution)** — 측정 도구가 구분할 수 있는 최소 간격. `performance.now()` 는 100마이크로초.
- **중앙값(median)** — 여러 판을 크기순으로 늘어놓았을 때 가운데 값.

## 더 들어가면

- **`<template>` 이 왜 필요했나** — 그전에는 틀을 `<script type="text/template">` 안에 문자열로 넣었다. 그러면 **파싱이 안 된 문자열**이라 찍을 때마다 `innerHTML` 을 불러야 했고, 그것이 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)의 파싱 비용과 XSS 면적을 그대로 떠안았다. `<template>` 은 **파싱은 한 번, 실행은 안 함**을 동시에 준다.
- **`DocumentFragment` 는 생성자로도 만든다** — `new DocumentFragment()` 가 `document.createDocumentFragment()` 와 같다. 후자가 더 오래된 이름이다.
- **조각의 자식을 비우지 않고 쓰는 법** — `host.append(...frag.children)` 처럼 펼쳐 넘기면 조각은 비지만, `[...frag.children]` 으로 먼저 배열에 담아 두면 참조가 남는다. 다만 **삽입은 여전히 이동**이므로 조각에서는 빠진다([03번 주제](../03-node-creation-insertion-removal/2-summary.md)).
- **선언적 Shadow DOM** 은 `<template shadowrootmode="open">` 으로 쓴다 — 그때는 파서가 **틀을 그림자 트리로 바꿔 버리므로** `content` 가 남지 않는다. 이 문서는 그 경우를 다루지 않았다(목록의 **12번 주제**).
- ★ **(6)의 결과를 일반 규칙으로 읽지 마라.** 이 환경은 headless Chrome 한 대이고 항목이 2000개다. 말할 수 있는 것은 「**이 조건에서 조각의 이득이 잡음 아래였다**」까지다. 반대로 **읽기·쓰기 교차의 한 자릿수 차이**는 세 판 모두 같은 방향이었으므로 그쪽은 결론으로 쓴다.
