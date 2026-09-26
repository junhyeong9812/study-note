# web-api/03 — 노드 생성·삽입·이동·제거: `createElement`·`append` 계열·`remove` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 언어 문법은 [`../../languages/`](../../languages/) 에 있고, 여기는 **브라우저가 건네주는 객체와 그 계약**이다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「Mutation algorithms」(pre-insert·insert·remove)·「Interface `ParentNode`」·「Interface `ChildNode`」·「`cloneNode`」 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 그래서 이 문서는 **「이식성」을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `append`·`prepend`·`before`·`after`·`replaceWith`·`remove` 는 DOM4 에서 들어온 것으로 오늘 모든 현행 엔진에 있다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

**근거로 쓸 칸을 미리 가른다.**

| 안 흔들리는 칸 (근거로 쓴다) | 흔들리는 칸 (근거로 쓰지 않는다) |
|---|---|
| 전후 트리 문자열 · 자식 수 · `parentElement.id` · 반환값(`undefined` 포함) · 예외 이름과 메시지 | Chrome 판 번호 · `performance.now()` 수치 |

이 주제의 블록에도 **흔들리는 칸이 없다.** 삽입 비용을 재는 것은 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)의 몫이다.

## 한눈에 — 쉽게 말하면

**★ DOM 에서 「넣는다」는 언제나 「옮긴다」다. 복사는 따로 시켜야만 일어난다.**

이사에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 가구를 **새로 사 온다** | `createElement`·`createTextNode` — 아직 아무 방에도 없다 |
| 가구를 **다른 방으로 옮긴다** | 이미 트리에 있는 노드를 `appendChild` — **원래 방에서 사라진다** |
| 가구를 **하나 더 만들어 둔다** | `cloneNode` — 이것만이 복사다 |
| 짐을 **이삿짐 상자에 모아** 한 번에 들인다 | `DocumentFragment` — 넣고 나면 **상자만 빈 채 남는다** |
| 가구를 **방에서 내놓는다** | `remove()` — 버려지는 것이 아니라 **복도에 놓인다** |

- **「넣기」에 복사는 없다.** 노드는 **부모가 하나**라는 규칙 하나로 전부 설명된다.
- **`append` 와 `appendChild` 는 이름만 비슷하다.** 받는 것도 돌려주는 것도 다르다.
- **뗀 노드는 사라지지 않는다.** 변수가 붙들고 있으면 살아 있고, 다시 넣을 수 있다.

```text
   before                                  right.appendChild(s1)      after
   <div id=left>                                                      <div id=left>
     <span id=s1>  "옮길 것"      ---- s1 을 right 에 넣는다 ---->        <span id=s2>
     <span id=s2>  "남을 것"                                             <span id=s1> <- 여기로 왔다
   <div id=right>                                                     <div id=right>
     <b id=b1>                                                          <b id=b1>
                                                                        <span id=s1>
   ★ left 에서 s1 이 '사라진다'. 복사가 아니라 이동이다
```

실무에서 이게 터지는 자리는 **목록 재정렬**이다.\
「원본은 그대로 두고 미리보기에 하나 더 붙이자」고 `preview.appendChild(item)` 을 쓰면 **원본에서 없어진다.**\
**에러도 경고도 없고** 화면에는 「**하나만 보인다**」로 나타난다 — 그래서 「왜 원본이 비었지」를 한참 헤맨다.

> **노드의 부모는 하나**(single parent) — DOM 나무는 **그래프가 아니라 나무**다. 한 노드가 두 자리에 동시에 있을 수 없다.\
> 예: `<span>` 을 다른 `<div>` 에 넣으면 원래 `<div>` 에서 빠진다.

> **`DocumentFragment`** — 부모가 없는 임시 자루. 삽입하면 **자루 자신은 안 들어가고 자식들만** 옮겨 간다.\
> 예: `li` 셋을 담아 `list.appendChild(frag)` 하면 `list` 에 `li` 셋이 생기고 자루는 빈다.

## 이 주제가 답하려는 질문

1. **「넣는다」는 정확히 무슨 일인가.** 이미 트리에 있던 노드를 넣으면 무엇이 일어나나.
2. **비슷한 이름의 메서드들이 왜 이렇게 많은가.** `append` 와 `appendChild` 는 무엇이 다른가.
3. **뗀 노드는 어디로 가나.** 그리고 복제하면 무엇이 따라오고 무엇이 안 따라오나.

## 이 갈래의 관측 창 — 트리를 전후로 그린다

[01번 주제](../01-document-and-node-tree/2-summary.md)의 창 셋 중 **창 1 을 두 번 쓰는 것**이 이 주제의 방식이다.

```text
  창 1  --dump-dom             결과 트리를 글자로
  창 2  childNodes.length      무엇이 몇 개인가
  창 3  두 번 읽기              02번 주제의 본체
  ★ 창 4 (이 주제 고유)  '같은 트리 출력기' 로 조작 전후를 두 번 그린다
        무엇을 답하나:  한 번의 호출이 '어디서 빠지고 어디에 붙었나'
        한쪽만 그리면 '붙었다' 만 보이고 '빠졌다' 를 못 본다
```

- **전후를 같은 출력기로 그리는 것이 핵심**이다. 붙은 쪽만 보면 **복사와 이동이 똑같아 보인다.**
- 이 문서의 트리 그림은 전부 **그 출력기가 뱉은 것**이고, 손으로 그린 것이 아니다.

## 동작 방식

### (0) 만들기 셋 — 아직 아무 데도 없는 노드

**언제 쓰나** — 화면에 새 것을 그릴 때. 만들기와 넣기는 **별개의 단계**다.

```html
<!-- ex03a.html -->
<!doctype html>
<meta charset="utf-8">
<title>03a</title>
<div id="box"></div>
<script>
const O = [];
const box = document.getElementById('box');
const el = document.createElement('span');
const txt = document.createTextNode('텍스트 노드');
const frag = document.createDocumentFragment();
O.push('createElement 결과       isConnected=' + el.isConnected + '  parentNode=' + el.parentNode);
O.push('createTextNode 결과      nodeType=' + txt.nodeType + '  data=' + JSON.stringify(txt.data));
O.push('createDocumentFragment   nodeType=' + frag.nodeType + '  nodeName=' + frag.nodeName);
O.push('');
const r1 = box.appendChild(el);
O.push('appendChild 반환값 === 넣은 노드 = ' + (r1 === el));
const el2 = document.createElement('b');
const r2 = box.append(el2);
O.push('append 반환값 = ' + r2);
O.push('');
box.append('문자 1 ', document.createElement('i'), ' 문자 2');
O.push('append 뒤 box.innerHTML = ' + box.innerHTML);
O.push('append 뒤 box.childNodes.length = ' + box.childNodes.length +
       '   box.children.length = ' + box.children.length);
O.push('');
try { box.appendChild('그냥 문자열'); }
catch (e) { O.push('appendChild("문자열") -> ' + e.constructor.name + ': ' + e.message); }
O.push('append("문자열") -> ' + (() => { const d = document.createElement('div'); d.append('문자열'); return 'ok, childNodes[0].nodeType=' + d.childNodes[0].nodeType; })());
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
createElement 결과       isConnected=false  parentNode=null
createTextNode 결과      nodeType=3  data="텍스트 노드"
createDocumentFragment   nodeType=11  nodeName=#document-fragment

appendChild 반환값 === 넣은 노드 = true
append 반환값 = undefined

append 뒤 box.innerHTML = <span></span><b></b>문자 1 <i></i> 문자 2
append 뒤 box.childNodes.length = 5   box.children.length = 3

appendChild("문자열") -> TypeError: Failed to execute 'appendChild' on 'Node': parameter 1 is not of type 'Node'.
append("문자열") -> ok, childNodes[0].nodeType=3
(exit 0)
```

```text
   document.createElement('span')        Element,  isConnected = false, parentNode = null
   document.createTextNode('글자')        Text,     nodeType 3
   document.createDocumentFragment()     Fragment, nodeType 11

           만들기                 넣기
   [ 새 노드 ]  --------->  [ 트리 안의 자리 ]
     parentNode = null        parentNode = 그 부모
     isConnected = false      isConnected = true
   ★ 만들기만 해서는 화면에 아무 일도 안 난다
```

그림 해설 (한 단계씩):

- **만든 노드는 `ownerDocument` 가 이미 `document` 인데 `isConnected` 는 `false`** 다([01번 주제](../01-document-and-node-tree/2-summary.md)).
- **넣기 전까지는 렌더도 스타일 계산도 없다.** 그래서 조립은 트리 밖에서 하는 쪽이 싸다.
- `createTextNode` 는 **글자를 글자로만** 넣는 유일한 생성기다 — 마크업으로 해석되지 않는다([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)).

비용 — 만들기 자체는 싸다. 비싼 것은 **넣은 뒤에 따라오는 스타일·레이아웃**이다([목록의 **10번 주제**](../10-layout-thrashing/)).

### (1) ★ `append` 와 `appendChild` — 이름만 비슷하다

**언제 쓰나** — 자식을 끝에 붙일 때. **셋이 갈린다 — 받는 것 · 돌려주는 것 · 여러 개.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '5,6p'
appendChild 반환값 === 넣은 노드 = true
append 반환값 = undefined
(exit 0)
```

```text
                    appendChild(node)            append(...nodes)
   받는 것           노드 하나만                   노드와 문자열을 몇 개든
   문자열을 주면      TypeError                     Text 노드로 바꿔 넣는다
   돌려주는 것        넣은 노드 (체이닝 가능)        undefined
   어디에 있나        Node (아주 오래된 것)          ParentNode (DOM4)
```

그림 해설 (한 단계씩):

- **`appendChild` 는 넣은 노드를 돌려준다.** 그래서 `const el = box.appendChild(document.createElement('b'))` 가 된다.
- **`append` 는 아무것도 안 돌려준다**(`undefined`). 체이닝을 기대하면 조용히 `undefined` 에 프로퍼티를 찾다가 `TypeError` 가 난다.
- **`append` 는 문자열을 받는다.** 실측에서 `box.append('문자 1 ', <i>, ' 문자 2')` 한 줄이 노드 셋을 만들었다 — 그 문자열은 **마크업이 아니라 글자**로 들어간다.
- **`appendChild('문자열')` 은 던진다** — `parameter 1 is not of type 'Node'`. 이 자리만 시끄럽게 실패한다.

비용 — 같다. 차이는 편의와 계약이지 성능이 아니다.

### (2) ★ 삽입이 곧 이동 — 이 주제의 본체

**언제 쓰나** — 이미 화면에 있는 요소를 다른 곳에 넣을 때. **여기서 「원본이 사라졌다」가 난다.**

```html
<!-- ex03b.html -->
<!doctype html>
<meta charset="utf-8">
<title>03b</title>
<div id="left"><span id="s1">옮길 것</span><span id="s2">남을 것</span></div>
<div id="right"><b id="b1">이미 있던 것</b></div>
<script>
const O = [];
const tree = (n, d) => {
  let s = '';
  for (const c of n.childNodes) {
    if (c.nodeType === 1) {
      s += '  '.repeat(d) + '<' + c.nodeName.toLowerCase() + (c.id ? ' id=' + c.id : '') + '>\n' + tree(c, d + 1);
    } else if (c.nodeType === 3 && c.nodeValue.trim()) {
      s += '  '.repeat(d) + '"' + c.nodeValue.trim() + '"\n';
    }
  }
  return s;
};
const s1 = document.getElementById('s1'), right = document.getElementById('right');
O.push('=== 옮기기 전 ===');
O.push('<div id=left>\n' + tree(document.getElementById('left'), 1) + '<div id=right>\n' + tree(right, 1));
O.push('s1.parentElement.id = ' + s1.parentElement.id);
O.push('');
const liveSpans = document.getElementsByTagName('span');
const snapSpans = document.querySelectorAll('span');
const 위치 = c => [...c].map(e => e.parentElement.id).join(',');
const 옮기기전 = 'live=[' + 위치(liveSpans) + ']  snap=[' + 위치(snapSpans) + ']';
const returned = right.appendChild(s1);
O.push('=== right.appendChild(s1) 한 뒤 ===');
O.push('<div id=left>\n' + tree(document.getElementById('left'), 1) + '<div id=right>\n' + tree(right, 1));
O.push('s1.parentElement.id = ' + s1.parentElement.id);
O.push('반환값 === s1 = ' + (returned === s1) + '   문서 안 span 수 = ' + liveSpans.length);
O.push('');
O.push('옮기기 전  ' + 옮기기전);
O.push('옮긴 뒤    live=[' + 위치(liveSpans) + ']  snap=[' + 위치(snapSpans) + ']');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,11p'
=== 옮기기 전 ===
<div id=left>
  <span id=s1>
    "옮길 것"
  <span id=s2>
    "남을 것"
<div id=right>
  <b id=b1>
    "이미 있던 것"

s1.parentElement.id = left
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '13,24p'
=== right.appendChild(s1) 한 뒤 ===
<div id=left>
  <span id=s2>
    "남을 것"
<div id=right>
  <b id=b1>
    "이미 있던 것"
  <span id=s1>
    "옮길 것"

s1.parentElement.id = right
반환값 === s1 = true   문서 안 span 수 = 2
(exit 0)
```

```text
   s1 을 right 에 넣는 한 줄이 두 가지 일을 한다

   1) left 에서 s1 을 '뺀다'      <- 명세의 remove 단계.  내가 안 시켰는데 일어난다
   2) right 의 끝에 s1 을 '넣는다'

   그래서 문서 안 <span> 수는 2 그대로다.  하나 늘지 않는다
```

그림 해설 (한 단계씩):

- **`left` 에서 `s1` 이 통째로 사라졌다.** 트리 출력기가 전후를 같은 형식으로 그려서 **빠진 쪽이 눈에 보인다.**
- **문서 안 `<span>` 수가 2 그대로**다 — 복사였다면 3 이 됐을 것이다. 이 한 줄이 「이동」의 결정적 증거다.
- **명세가 그렇게 정해 뒀다.** 삽입 알고리즘이 「노드에 부모가 있으면 먼저 제거한다」를 **첫 단계**로 갖는다. 구현이 고른 동작이 아니다.
- **`appendChild` 의 반환값이 `s1` 자신**이다 — 옮겨진 노드를 그대로 돌려준다.
- 복사를 원하면 **`cloneNode(true)`** 를 명시해야 한다(아래 (5)).

**잡아 둔 컬렉션은 이 이동을 어떻게 볼까** — [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 창 3 을 여기에 겹친다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '26,27p'
옮기기 전  live=[left,left]  snap=[left,left]
옮긴 뒤    live=[left,right]  snap=[right,left]
(exit 0)
```

```text
   옮기기 전   live = [left, left]     snap = [left, left]
   옮긴 뒤     live = [left, right]    snap = [right, left]
                      ^^^^^^^^^^^^            ^^^^^^^^^^^^
                      문서 순서로 다시 정렬     ★ 잡을 때의 순서 그대로

   개수는 둘 다 2 다 — 이동은 '멤버십' 을 안 바꾼다. 바꾸는 것은 '순서' 다
```

- **라이브 컬렉션은 문서 순서로 다시 줄을 선다.** 첫 칸이 이제 `left` 에 남은 `s2` 다.
- **정적 스냅샷은 잡을 때의 순서를 지킨다.** 첫 칸이 여전히 `s1` 이고, 그 `s1` 은 이제 `right` 에 있다.
- 그래서 **「인덱스로 꺼내 쓰는 코드」가 이동 뒤에 조용히 다른 것을 집는다.** 개수가 그대로라 검사로도 안 잡힌다.

비용 — 이동은 **노드를 다시 만들지 않는다.** 리스너·상태(폼 값·스크롤)가 그대로 따라간다. 복사는 그렇지 않다. **다만 예외가 하나 있고 아래 (6)에서 잰다.**

```html demo
<div class="row">
  <div class="bin">왼쪽 <span class="chip" id="chip">옮길 칩</span></div>
  <div class="bin" id="right">오른쪽</div>
</div>
<button id="go">right.appendChild(chip)</button>
<style>
  .row { display: flex; gap: 12px; margin-bottom: 8px; }
  .bin { flex: 1; border: 2px dashed #94a3b8; padding: 8px; min-height: 40px; }
  .chip { background: #2563eb; color: #fff; padding: 2px 8px; border-radius: 999px; }
</style>
<script>
  document.getElementById('go').onclick = () =>
    document.getElementById('right').appendChild(document.getElementById('chip'));
</script>
```

> **보이는 것** — 왼쪽 점선 상자 안에 파란 알약 모양의 「옮길 칩」이 있다. 버튼을 누르면 그 칩이 **왼쪽에서 사라지고** 오른쪽 상자의 「오른쪽」 글자 뒤에 나타난다. 왼쪽에는 「왼쪽」이라는 글자만 남는다. 다시 눌러도 더 변하지 않는다.\
> **바꿔 볼 것** — `appendChild(chip)` 을 `appendChild(chip.cloneNode(true))` 로 바꾸면 **왼쪽에도 남고 오른쪽에도 생겨 칩이 둘**이 된다(실측으로 확인했다) · `right.prepend(chip)` 으로 바꾸면 「오른쪽」 글자 **앞**에 붙는다.

### (3) 자리를 지정하는 다섯 — `prepend`·`before`·`after`·`replaceWith`·`remove`

**언제 쓰나** — 끝이 아닌 자리에 넣거나 뺄 때. **기준이 부모냐 형제냐로 갈린다.**

```html
<!-- ex03d.html -->
<!doctype html>
<meta charset="utf-8">
<title>03d</title>
<div id="box"><b id="b1">B1</b><b id="b2">B2</b></div>
<script>
const O = [];
const box = document.getElementById('box');
const shape = () => [...box.childNodes].map(n =>
  n.nodeType === 1 ? '<' + n.nodeName.toLowerCase() + ' id=' + n.id + '>' : '"' + n.nodeValue + '"').join(' ');
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const step = label => O.push(label + '.'.repeat(Math.max(1, 26 - W(label))) + ' ' + shape());
const mk = id => Object.assign(document.createElement('i'), {id: id, textContent: id});
step('처음');
box.prepend(mk('p1'));
step('box.prepend(p1)');
document.getElementById('b1').before(mk('x1'));
step('b1.before(x1)');
document.getElementById('b1').after(mk('x2'));
step('b1.after(x2)');
document.getElementById('b2').replaceWith(mk('r1'));
step('b2.replaceWith(r1)');
document.getElementById('x1').remove();
step('x1.remove()');
box.prepend('텍스트도 된다');
step('box.prepend(문자열)');
O.push('');
const gone = document.getElementById('x1');
O.push('remove 한 x1 을 document 에서 다시 찾으면 = ' + gone);
O.push('removeChild 반환값 === 뗀 노드 = ' + (() => { const n = document.getElementById('r1'); return box.removeChild(n) === n; })());
step('removeChild(r1)');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03d.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
처음...................... <b id=b1> <b id=b2>
box.prepend(p1)........... <i id=p1> <b id=b1> <b id=b2>
b1.before(x1)............. <i id=p1> <i id=x1> <b id=b1> <b id=b2>
b1.after(x2).............. <i id=p1> <i id=x1> <b id=b1> <i id=x2> <b id=b2>
b2.replaceWith(r1)........ <i id=p1> <i id=x1> <b id=b1> <i id=x2> <i id=r1>
x1.remove()............... <i id=p1> <b id=b1> <i id=x2> <i id=r1>
box.prepend(문자열)....... "텍스트도 된다" <i id=p1> <b id=b1> <i id=x2> <i id=r1>

remove 한 x1 을 document 에서 다시 찾으면 = null
removeChild 반환값 === 뗀 노드 = true
removeChild(r1)........... "텍스트도 된다" <i id=p1> <b id=b1> <i id=x2>
(exit 0)
```

```text
   부모를 기준으로              형제를 기준으로
   +---------------------+     +----------------------------+
   | parent.append(x)    |     | node.before(x)   앞에       |
   | parent.prepend(x)   |     | node.after(x)    뒤에       |
   +---------------------+     | node.replaceWith(x) 자기 대신|
                               | node.remove()    자기를 뗀다 |
                               +----------------------------+
   ParentNode 의 것             ChildNode 의 것
```

그림 해설 (한 단계씩):

- **`prepend` 는 맨 앞**, `append` 는 맨 뒤. 둘 다 **부모에 대고** 부른다.
- **`before`·`after`·`replaceWith`·`remove` 는 자기 자신에 대고** 부른다. 부모를 몰라도 된다 — 이것이 옛 `parent.insertBefore(new, ref)` 보다 나은 점이다.
- **다섯 다 문자열을 받는다**(`remove` 제외). 출력의 마지막에서 `box.prepend('텍스트도 된다')` 가 텍스트 노드가 됐다.
- **`removeChild` 는 뗀 노드를 돌려주고 `remove()` 는 아무것도 안 돌려준다.** 뗀 노드를 다시 쓸 것이면 미리 변수에 담아 둔다.
- **`remove()` 한 노드는 `document.getElementById` 로 못 찾는다** — 출력의 `null` 이 그것이다. 그러나 **노드 자체는 살아 있다**(아래 (4)).

비용 — 같다. 형제 기준 메서드들은 **부모를 내부적으로 찾아** 쓴다.

### (4) `DocumentFragment` — 넣고 나면 자루가 빈다

**언제 쓰나** — 여러 노드를 한 번에 넣을 때. **그리고 「왜 두 번째 삽입이 아무 일도 안 하지」를 만날 때.**

```html
<!-- ex03c.html -->
<!doctype html>
<meta charset="utf-8">
<title>03c</title>
<ul id="list"></ul>
<script>
const O = [];
const list = document.getElementById('list');
const frag = document.createDocumentFragment();
for (const name of ['가', '나', '다']) {
  frag.appendChild(Object.assign(document.createElement('li'), {textContent: name}));
}
O.push('붙이기 전  frag.childNodes.length = ' + frag.childNodes.length +
       '   list.children.length = ' + list.children.length);
O.push('           frag.isConnected = ' + frag.isConnected);
const li0 = frag.firstElementChild;
list.appendChild(frag);
O.push('붙인 뒤    frag.childNodes.length = ' + frag.childNodes.length +
       '   list.children.length = ' + list.children.length);
O.push('           li0.isConnected = ' + li0.isConnected + '   li0.parentElement.id = ' + li0.parentElement.id);
O.push('');
O.push('list.innerHTML = ' + list.innerHTML);
O.push("문서에 frag 자신이 들어갔나: list.querySelector('ul') = " + list.querySelector('ul'));
O.push('');
frag.appendChild(document.createElement('li'));
list.appendChild(frag);
O.push('같은 frag 를 다시 채워 붙이면 list.children.length = ' + list.children.length);
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,5p'
붙이기 전  frag.childNodes.length = 3   list.children.length = 0
           frag.isConnected = false
붙인 뒤    frag.childNodes.length = 0   list.children.length = 3
           li0.isConnected = true   li0.parentElement.id = list

(exit 0)
```

```text
   붙이기 전                       list.appendChild(frag)        붙인 뒤
   frag                                                          frag
    +- <li>가                 ----- 자식들만 옮겨 간다 ----->       (비었다)
    +- <li>나                                                     list
    +- <li>다                                                      +- <li>가
   list  (비었다)                                                  +- <li>나
                                                                   +- <li>다
   ★ frag 자신은 트리에 안 들어간다.  list.querySelector('ul') 은 null
```

그림 해설 (한 단계씩):

- **조각을 넣으면 자식들만 옮겨 가고 조각은 빈 채로 남는다.** `frag.childNodes.length` 가 3 에서 **0** 이 된다.
- 이것도 **(2)의 「삽입은 이동」과 같은 규칙**이다 — 자식들이 조각에서 빠져 새 부모로 간다.
- **같은 조각을 두 번 붙이면 두 번째는 아무 일도 안 한다**(이미 비었으므로). 다시 채워 넣으면 그때부터 또 동작한다 — 출력의 마지막 줄이 그 확인이다.
- **조각 자신은 트리에 안 들어간다.** 그래서 「조각을 넣었는데 래퍼가 안 생기는」 것이 정상이다.
- **한 번에 넣는 것이 싼가**는 이 문서가 **주장하지 않는다.** 그 비교는 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에서 수치로 재고, 결과가 직관과 달랐다.

비용 — 조각을 만드는 것 자체는 싸다. **레이아웃이 몇 번 도느냐**가 본론이고 그것은 [목록의 **05번 주제**](../05-documentfragment-and-template/)와 **10번 주제**의 몫이다.

### (5) `cloneNode` — 무엇이 따라오고 무엇이 안 오나

**언제 쓰나** — 진짜로 복사가 필요할 때. **그리고 「복제본에서 클릭이 안 먹는다」를 만날 때.**

```html
<!-- ex03e.html -->
<!doctype html>
<meta charset="utf-8">
<title>03e</title>
<div id="orig" class="card" data-k="v"><b>깊은 것</b></div>
<button id="btn" onclick="window.속성이_불렸다 = true">속성 핸들러</button>
<script>
const O = [];
const orig = document.getElementById('orig');
const shallow = orig.cloneNode(false);
const deep = orig.cloneNode(true);
O.push('orig.childNodes.length    = ' + orig.childNodes.length);
O.push('cloneNode(false).childNodes.length = ' + shallow.childNodes.length);
O.push('cloneNode(true).childNodes.length  = ' + deep.childNodes.length);
O.push('cloneNode(false).outerHTML = ' + shallow.outerHTML);
O.push('cloneNode(true).outerHTML  = ' + deep.outerHTML);
O.push('복제본의 id = ' + JSON.stringify(deep.id) + '   (같은 id 가 둘이 된다)');
O.push('deep === orig = ' + (deep === orig) + '   deep.isConnected = ' + deep.isConnected);
O.push('');
const btn = document.getElementById('btn');
window.리스너가_불렸다 = 0;
btn.addEventListener('click', () => { window.리스너가_불렸다++; });
const btnClone = btn.cloneNode(true);
document.body.appendChild(btnClone);
window.속성이_불렸다 = false;
btn.click();
O.push('원본 클릭   addEventListener 호출 수 = ' + window.리스너가_불렸다 + '   onclick 속성 = ' + window.속성이_불렸다);
window.속성이_불렸다 = false;
btnClone.click();
O.push('복제본 클릭 addEventListener 호출 수 = ' + window.리스너가_불렸다 + '   onclick 속성 = ' + window.속성이_불렸다);
O.push('복제본의 onclick 속성 문자열 = ' + JSON.stringify(btnClone.getAttribute('onclick')));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03e.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
orig.childNodes.length    = 1
cloneNode(false).childNodes.length = 0
cloneNode(true).childNodes.length  = 1
cloneNode(false).outerHTML = <div id="orig" class="card" data-k="v"></div>
cloneNode(true).outerHTML  = <div id="orig" class="card" data-k="v"><b>깊은 것</b></div>
복제본의 id = "orig"   (같은 id 가 둘이 된다)
deep === orig = false   deep.isConnected = false

원본 클릭   addEventListener 호출 수 = 1   onclick 속성 = true
복제본 클릭 addEventListener 호출 수 = 1   onclick 속성 = true
복제본의 onclick 속성 문자열 = "window.속성이_불렸다 = true"
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03e.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,11p'
원본 클릭   addEventListener 호출 수 = 1   onclick 속성 = true
복제본 클릭 addEventListener 호출 수 = 1   onclick 속성 = true
복제본의 onclick 속성 문자열 = "window.속성이_불렸다 = true"
(exit 0)
```

```text
   cloneNode(false)   얕게 — 자기 자신만.  자식은 안 온다
   cloneNode(true)    깊게 — 하위 트리 전부

   따라오는 것                          안 따라오는 것
   +-------------------------------+   +-------------------------------+
   | 태그 이름                      |   | addEventListener 로 단 리스너  |
   | 속성 전부 (id 포함!)           |   | 자바스크립트로 넣은 프로퍼티    |
   | onclick 같은 '속성' 핸들러     |   | 폼 요소의 현재 입력값(사용자 상태)|
   | (true 면) 자식 노드 전부       |   | isConnected (복제본은 트리 밖) |
   +-------------------------------+   +-------------------------------+
```

그림 해설 (한 단계씩):

- **`id` 까지 복사된다.** 그대로 문서에 넣으면 **같은 `id` 가 둘**이 되고, `getElementById` 는 **첫 것만** 준다([02번 주제](../02-element-queries-and-live-collections/2-summary.md)).
- ★ **리스너는 안 따라오는데 `onclick` 속성은 따라온다.** 실측에서 복제본을 클릭했더니 `addEventListener` 카운터는 **1 그대로**였고 `onclick` 속성은 **켜졌다.**
- 그 이유는 한 줄이다 — **속성은 노드의 일부이고 리스너는 아니다.** 리스너는 노드와 따로 관리되는 목록이다([목록의 **15번 주제**](../15-listener-registration/)).
- **복제본은 트리 밖**이다(`isConnected = false`). 넣어야 보인다.

비용 — 깊은 복제는 **하위 트리 크기에 비례**한다. 이 문서는 그 비용을 재지 않았다.

### (6) 삽입이 검사하지 않는 것, 그리고 이동이 공짜가 아닌 한 자리

**언제 쓰나** — 「파서가 못 만드는 트리를 API 로 만들 수 있나」와 「이동이 정말 싼가」를 확인할 때.

```html
<!-- ex03f.html -->
<!doctype html>
<meta charset="utf-8">
<title>03f</title>
<div id="a"><iframe id="fr" srcdoc="<p>프레임 안</p>"></iframe></div>
<div id="b"></div>
<div id="c"></div>
<script>
const O = [];
const p = document.createElement('p');
p.appendChild(document.createElement('div'));
O.push('appendChild 로 <p> 안에 <div> 를 넣으면 = ' + p.outerHTML);
document.getElementById('c').innerHTML = '<p>가<div>나</div></p>';
O.push('같은 모양을 innerHTML 로 넣으면          = ' + document.getElementById('c').innerHTML);
O.push('');
window.addEventListener('load', () => {
  const fr = document.getElementById('fr');
  fr.contentWindow.표식 = 'A';
  O.push('iframe 을 옮기기 전  contentWindow.표식 = ' + fr.contentWindow.표식);
  O.push('프레임 안 글자 = ' + JSON.stringify(fr.contentDocument.body.textContent));
  document.getElementById('b').appendChild(fr);
  O.push('다른 부모로 옮긴 직후 표식 = ' + fr.contentWindow.표식);
  O.push('옮긴 직후 프레임 안 글자 = ' + JSON.stringify(fr.contentDocument.body.textContent));
  document.body.appendChild(Object.assign(document.createElement('script'),
    {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
});
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03f.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,2p'
appendChild 로 <p> 안에 <div> 를 넣으면 = <p><div></div></p>
같은 모양을 innerHTML 로 넣으면          = <p>가</p><div>나</div><p></p>
(exit 0)
```

```text
   같은 모양을 두 경로로 넣었다

   API 로     p.appendChild(div)          ->  <p><div></div></p>       그대로 들어간다
   파서로     innerHTML = '<p>가<div>나</div></p>'
                                          ->  <p>가</p><div>나</div><p></p>
                                              ^^^^^^^^^^^^^^^^^^^^^^ 파서가 쪼갰다

   ★ '트리가 될 수 있는 모양' 과 '파서가 만들 수 있는 모양' 이 다르다
```

- **삽입 알고리즘은 콘텐츠 모델을 검사하지 않는다.** 검사하는 것은 「부모가 될 수 있는 종류인가」·「조상을 자기 자손에 넣는가」 정도다.
- **파서 쪽 규칙이 정본인 곳은** HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **03번**이다. 여기서는 **두 경로의 결과가 다르다는 사실**만 보인다. 파싱 자체는 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)가 이어받는다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03f.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '4,7p'
iframe 을 옮기기 전  contentWindow.표식 = A
프레임 안 글자 = "프레임 안"
다른 부모로 옮긴 직후 표식 = undefined
옮긴 직후 프레임 안 글자 = ""
(exit 0)
```

```text
   이동은 '노드를 다시 만들지 않는다' 가 일반 규칙인데 — 여기에 예외가 있다

   <iframe> 을 다른 부모로 옮기면
     contentWindow 에 심어 둔 표식이 사라지고
     contentDocument 의 본문이 빈다                 <- 프레임 안이 통째로 버려졌다

   실측: 표식 'A' -> undefined,  본문 "프레임 안" -> ""
```

- **`<iframe>` 은 옮기면 안의 브라우징 문맥이 버려진다.** 노드 객체는 그대로인데 **그 안의 문서는 아니다.**
- 그래서 **「이동은 싸다」를 모든 요소에 일반화하면 안 된다.** 프레임을 품은 영역을 재배치하는 코드가 조용히 상태를 잃는 자리다.
- **이 문서는 그 뒤에 다시 로드되는지까지는 확인하지 못했다** — `--dump-dom` 이 한 턴 뒤에 끊기고, 재로드는 그 뒤에 일어나기 때문이다. 확인한 것은 「**옮긴 직후 안이 비었다**」까지다.

비용 — 이동 자체는 싸지만 **프레임 재로드는 네트워크까지 갈 수 있다.** 이 문서는 그 비용을 재지 않았다.

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
document.createElement('div')            // 요소
document.createTextNode('글자')           // 텍스트 노드
document.createDocumentFragment()        // 조각
document.createComment('메모')            // 주석 노드

parent.appendChild(node)                 // 노드 하나 · 넣은 노드를 돌려준다
parent.insertBefore(node, ref)           // ref 앞에 · 넣은 노드를 돌려준다
parent.removeChild(node)                 // 뗀 노드를 돌려준다
parent.replaceChild(newNode, oldNode)    // 뗀 노드를 돌려준다

parent.append(...노드와_문자열)            // undefined
parent.prepend(...노드와_문자열)           // undefined
parent.replaceChildren(...)              // 자식을 통째로 갈아 끼운다
node.before(...) / node.after(...)       // 형제 자리
node.replaceWith(...) / node.remove()    // 자기 자리

node.cloneNode(true)                     // 깊은 복제
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
preview.appendChild(item);               // 원본에서 사라진다
box.append(el).classList.add('x');       // undefined 에 접근 -> TypeError
box.appendChild('문자열');                // TypeError
list.appendChild(frag); list.appendChild(frag);   // 두 번째는 아무 일도 안 한다
document.body.appendChild(el.cloneNode(true));    // id 가 둘이 된다
const c = btn.cloneNode(true);           // 리스너는 안 온다
```

- **옛 3형제(`appendChild`·`insertBefore`·`removeChild`)는 전부 노드를 돌려주고**, 새 메서드들은 전부 `undefined` 다. 섞어 쓰면 체이닝에서 걸린다.
- **`replaceChildren()` 은 인자 없이 부르면 자식을 전부 지운다** — `innerHTML = ''` 의 안전한 대체다.

### 어디서 헷갈리나

- `append` 와 `appendChild` 의 **`Child`** 는 「자식으로」가 아니라 「**노드 하나만**」의 표시로 읽는 쪽이 낫다.
- **`before`/`after` 는 형제 자리**이지 부모 안의 앞뒤가 아니다. `prepend` 와 헷갈린다.
- **`remove()` 는 노드를 지우는 것이 아니라 떼는 것**이다. 변수가 붙들고 있으면 살아 있다.
- **텍스트를 넣을 때 `append('<b>x</b>')` 는 태그로 해석되지 않는다.** 마크업으로 넣으려면 `innerHTML` 인데, 그것이 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)의 위험이다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 중 넷이 **에러 없이 조용히 어긋난다.**

### 1. 「넣으면 복사되겠지」

실측에서 `right.appendChild(s1)` 한 줄에 **`left` 에서 `s1` 이 사라졌다.** 문서 안 `<span>` 수는 2 그대로다.\
증상은 「원본이 비었다」 하나뿐이고 **에러가 없다.**

### 2. `append` 의 반환값을 기대한다

`append` 는 **`undefined`** 다. `box.append(el).classList` 는 `TypeError` 로 죽는데, **죽는 줄과 원인이 멀어서** 헷갈린다.

### 3. 같은 조각을 두 번 붙인다

첫 번째에서 **조각이 비므로** 두 번째는 아무 일도 안 한다. 실측에서 `frag.childNodes.length` 가 3 에서 **0** 이 됐다.\
반복문 안에서 조각 하나를 돌려 쓰면 **첫 판만 동작**한다.

### 4. 복제본에 리스너가 있을 거라 기대한다

실측에서 복제본을 클릭해도 `addEventListener` 로 단 핸들러는 **안 불렸다.** 그런데 **`onclick` 속성은 불렸다** — 그래서 「어떤 것은 되고 어떤 것은 안 된다」로 보여 더 헷갈린다.

### 5. 복제본의 `id` 를 그대로 둔다

`cloneNode` 는 **속성을 전부 복사**하므로 `id` 도 온다. 문서에 넣으면 같은 `id` 가 둘이 되고, `getElementById` 는 **첫 것만** 준다.

### 6. `remove()` 한 노드를 버려진 것으로 여긴다

**떼어진 것**이지 지워진 것이 아니다. 배열이나 클로저가 붙들고 있으면 **그 하위 트리 전체**가 메모리에 남는다([목록의 **20번 주제**](../20-listener-lifetime/)).

## 구현 세부사항 대 언어 보장

여기서 「언어 보장」은 **명세(WHATWG DOM)가 정한 것**이고, 「구현」은 **Blink 가 하는 것**이다.

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 이미 부모가 있는 노드를 넣으면 **먼저 제거**되는 것 | **명세**(DOM §4.2.3 「insert」 — pre-insert 가 remove 를 부른다) |
| `DocumentFragment` 를 넣으면 **자식들만** 들어가고 조각이 비는 것 | **명세**(같은 절 — 조각이면 자식을 전부 옮긴다) |
| `appendChild` 가 **넣은 노드**를 돌려주는 것 | **명세**(DOM §4.4) |
| `append`·`prepend`·`before`·`after`·`replaceWith` 가 **`undefined`** 인 것 | **명세**(DOM §4.2.6·§4.2.7 — 반환 타입이 `undefined`) |
| 그 메서드들이 **문자열을 `Text` 노드로** 바꾸는 것 | **명세**(「converting nodes into a node」) |
| `appendChild` 에 문자열을 주면 **`TypeError`** 인 것 | **명세**(WebIDL 인자 타입) |
| `cloneNode` 가 **속성은 복사하고 리스너는 안 하는 것** | **명세**(DOM §4.4 「clone a node」 — 「event listeners… are not copied」) |
| `remove()` 한 노드가 **살아 있는 것** | **명세**(제거는 트리에서 떼는 것이고 파괴가 아니다) |
| `id` 가 복사되어 중복이 되는 것 | **명세**(속성 전부 복사) + **HTML 의 유일성 규칙은 별개** |
| **예외 메시지 문구**(`parameter 1 is not of type 'Node'.`) | **관찰**(Chrome 151). 명세는 문구를 정하지 않는다 |
| 트리 출력기가 그린 **들여쓰기 형태** | **이 문서의 코드**가 정한 것. 브라우저와 무관하다 |
| **삽입·복제의 비용** | 재지 않았다. 이 문서는 성능을 주장하지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 새 요소를 끝에 붙인다 | `append`(문자열도 섞을 때) · `appendChild`(반환값이 필요할 때) | 섞어 쓰며 체이닝 |
| 요소를 다른 자리로 **옮긴다** | 그냥 넣는다(이동이 기본) | `remove()` 뒤 다시 넣기(불필요) |
| 요소를 **하나 더** 만든다 | `cloneNode(true)` + `id` 를 지우거나 바꾼다 | 그냥 넣기 |
| 형제 자리에 넣는다 | `before`·`after` | `parent.insertBefore` (부모를 찾아야 한다) |
| 자식을 전부 간다 | `replaceChildren(...)` | `innerHTML = ''`([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)) |
| 여러 개를 한 번에 넣는다 | `append(a, b, c)` · `DocumentFragment` | 반복문 안에서 조각 하나 돌려 쓰기 |
| 글자를 넣는다 | `append('글자')` · `textContent` | `innerHTML` (파싱과 XSS) |

판단 규칙 두 줄.

- **「이 노드가 지금 트리에 있나」를 먼저 묻는다.** 있으면 넣는 순간 **옮겨진다.**
- **복사는 항상 명시**한다. DOM 에서 암묵적인 복사는 **한 군데도 없다.**

## 핵심 문장

- **삽입은 언제나 이동**이다. 명세의 삽입 알고리즘이 「부모가 있으면 먼저 제거」를 첫 단계로 갖는다 — 실측에서 `appendChild` 한 줄에 원래 자리에서 노드가 사라졌고 문서 안 개수는 **그대로 2** 였다.
- **`append` 와 `appendChild` 는 셋이 다르다** — 받는 것(문자열 가능/불가) · 개수(여럿/하나) · 반환값(`undefined`/넣은 노드).
- **`DocumentFragment` 는 넣고 나면 빈다.** 자식들만 옮겨 가고 조각 자신은 트리에 안 들어간다 — 그래서 **같은 조각을 두 번 붙이면 두 번째는 아무 일도 안 한다.**
- **형제 기준 메서드**(`before`·`after`·`replaceWith`·`remove`)는 **부모를 몰라도** 쓴다. 옛 API 보다 짧아진 것이 여기다.
- **`cloneNode` 는 속성을 복사하고 리스너를 복사하지 않는다.** 실측에서 `onclick` 속성은 따라왔고 `addEventListener` 리스너는 안 왔다 — **속성은 노드의 일부이고 리스너는 아니기 때문**이다.
- **복제본의 `id` 까지 따라온다.** 그대로 넣으면 중복 `id` 가 되고 `getElementById` 는 첫 것만 준다.
- **`remove()` 는 떼는 것이지 지우는 것이 아니다.** 뗀 노드는 변수가 붙들면 살아 있고 다시 넣을 수 있다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 03번)
- [01번 주제](../01-document-and-node-tree/2-summary.md) — **노드와 트리 구조의 정본.** 그쪽은 「무엇이 있나」까지, 여기는 「그것을 어떻게 바꾸나」부터
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md) — 여기서 바꾼 결과가 **잡아 둔 컬렉션에 어떻게 비치나**의 정본
- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) — **문자열로 트리를 만드는 쪽.** 여기는 노드를 하나씩 다루고, 그쪽은 마크업을 파싱해 통째로 만든다. **비용 비교도 그쪽**이다
- [목록의 **05번 주제**](../05-documentfragment-and-template/)(`DocumentFragment` 와 `<template>` 복제) — **일괄 삽입의 정본.** 여기는 조각의 **의미**(넣으면 빈다)까지, 그쪽은 **묶음 삽입 설계와 `<template>`** 부터
- [목록의 **15번 주제**](../15-listener-registration/)(리스너 등록과 해제) — `cloneNode` 가 리스너를 안 복사하는 이유가 되는 **리스너 관리 모델**의 정본
- [목록의 **10번 주제**](../10-layout-thrashing/)(레이아웃 스래싱) — 넣기가 비싸지는 **진짜 이유**. 여기는 삽입의 의미만 다루고 비용은 그쪽
- [목록의 **20번 주제**](../20-listener-lifetime/)(리스너 수명) — 뗀 노드가 메모리에 남는 경로
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **03번**(파서·오류 복구) — 「어떤 부모에 어떤 자식이 들어갈 수 있나」는 **파싱 때의 규칙**이다. `appendChild` 는 그 규칙을 **적용하지 않는다** — 04번 주제에 그 대비가 실려 있다
- JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **08번**(함수 정의 형태와 매개변수) — `append(...nodes)` 같은 **가변 인자**가 무엇인지는 그쪽. 여기는 **그 인자에 무엇을 줄 수 있나**만

## 용어 풀이

- **삽입(insert)** — 노드를 부모의 자식 목록에 넣는 명세상의 절차. **부모가 있으면 먼저 제거하는 단계**를 포함한다.
- **이동(move)** — 이 문서에서 「삽입이 곧 이동」이라고 부르는 것. 별도의 API 가 아니라 삽입의 성질이다.
- **`DocumentFragment`** — 부모 없는 임시 자루. 삽입하면 자식들만 옮겨 가고 자신은 빈다.
- **`ParentNode`** — `append`·`prepend`·`replaceChildren` 을 주는 믹스인. 부모에 대고 부른다.
- **`ChildNode`** — `before`·`after`·`replaceWith`·`remove` 를 주는 믹스인. 자기 자신에 대고 부른다.
- **얕은 복제(`cloneNode(false)`)** — 자기 자신만. 자식은 안 온다.
- **깊은 복제(`cloneNode(true)`)** — 하위 트리 전부.
- **속성 핸들러(`onclick` 속성)** — 마크업에 쓴 이벤트 핸들러. **속성이라서 복제에 따라온다.**
- **떼기(detach)** — `remove()` 가 하는 일. 트리에서 빠질 뿐 객체는 살아 있다.
- **`replaceChildren()`** — 자식을 통째로 갈아 끼우는 메서드. 인자 없이 부르면 전부 지운다.

## 더 들어가면

- **옛 3형제와 새 메서드가 공존하는 이유**는 역사다. `appendChild`·`insertBefore`·`removeChild` 는 DOM Level 1(1998) 것이고, `append`·`before`·`remove` 는 DOM4(2015 무렵) 에서 **jQuery 가 증명한 편의**를 표준이 받아들인 것이다. 그래서 반환값 규약이 서로 다르다.
- **`insertBefore(node, null)` 은 `appendChild` 와 같다.** 두 번째 인자가 `null` 이면 끝에 붙인다 — 옛 코드가 자주 쓰던 관용구다.
- **위 (6)의 두 실측은 이 주제의 경계를 그리는 자리**다. 하나는 「삽입은 파서의 규칙을 안 따른다」이고, 다른 하나는 「이동이 공짜라는 일반 규칙의 예외」다. 둘 다 **에러 없이** 일어난다.
- **`replaceChildren()` 은 2020 년 무렵 들어온 비교적 새 메서드**다. `innerHTML = ''` 의 대체로 권장되는 이유는 **파싱을 안 하기 때문**이고, 그 차이는 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)가 수치로 보여 준다.
