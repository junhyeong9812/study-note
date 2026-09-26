# web-api/02 — 요소 조회: `querySelector` 계열과 `getElementsBy*`·라이브 대 정적 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 언어 문법은 [`../../languages/`](../../languages/) 에 있고, 여기는 **브라우저가 건네주는 객체와 그 계약**이다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「Interface `NodeList`」·「Interface `HTMLCollection`」·「Interface `ParentNode`」·「`getElementsByTagName`」 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 그래서 이 문서는 **「이식성」을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. 기준은 **Baseline** 하나이고, 이 주제의 표면은 전부 Baseline 추적 대상 자체가 아닐 만큼 오래된 것이다. 예외는 `:scope` 로, 오늘 모든 현행 엔진에 있다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

**근거로 쓸 칸을 미리 가른다.**

| 안 흔들리는 칸 (근거로 쓴다) | 흔들리는 칸 (근거로 쓰지 않는다) |
|---|---|
| 컬렉션의 `length` · 순회가 돈 횟수 · `constructor.name` · 예외 이름과 메시지 · `--dump-dom` 트리 | Chrome 판 번호 · `performance.now()` 수치 |

이 주제의 블록에도 **흔들리는 칸이 없다.** 수치를 재는 자리가 없다.

## 한눈에 — 쉽게 말하면

**★ 어떤 조회는 「사진」을 주고 어떤 조회는 「생중계」를 준다. 문제는 받은 자리에서는 둘이 똑같아 보인다는 것이다.**

방범 카메라에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 지금 화면을 찍은 **사진 한 장** | `querySelectorAll()` 이 주는 **정적 `NodeList`** |
| 벽에 걸린 **생중계 모니터** | `getElementsBy*`·`children` 이 주는 **라이브 `HTMLCollection`** |
| 사진과 모니터를 나란히 걸어 두고 **가게 안을 바꿔 본다** | 창 3 — DOM 을 바꾼 뒤 둘을 다시 읽는다 |
| 사진 속 사람이 이미 가게를 나갔다 | 스냅샷이 **문서에서 떨어진 노드**를 들고 있다 |
| 모니터를 보며 손님을 한 명씩 내보낸다 | 라이브 컬렉션을 순회하며 삭제 — **한 칸씩 밀린다** |

- **받은 순간에는 둘이 같은 답을 준다.** 그래서 **한 번만 읽으면 영원히 구분이 안 된다.**
- 둘을 가르는 것은 「**언제 읽었나**」다. 이 주제는 **시간 축이 본체**인 유일한 주제다.
- **타입 이름으로 외우면 틀린다** — 같은 `NodeList` 인데 한쪽은 라이브고 한쪽은 정적이다.

```text
   t0  둘 다 잡는다              t1  li 를 하나 붙인다        t2  다시 읽는다
   +---------------------+       +--------------------+      +---------------------+
   | 라이브  length = 2  |       |  <li>C</li> 추가   |      | 라이브  length = 3  |
   | 정적    length = 2  |       |                    |      | 정적    length = 2  |
   +---------------------+       +--------------------+      +---------------------+
        같은 답                                                   ★ 여기서 갈린다
```

실무에서 이게 터지는 자리는 **목록을 지우는 반복문**이다.\
`for (let i = 0; i < live.length; i++) live[i].remove()` 는 **절반만 지운다** — 지울 때마다 뒤가 앞으로 당겨 오는데 `i` 는 늘기만 하기 때문이다.\
**에러도 경고도 없다.** 남은 항목을 보고 「왜 두 개가 남지」에서 출발해야 한다.

> **라이브 컬렉션(live collection)** — 돌려받은 목록이 **DOM 을 바꾸면 따라 바뀌는** 것.\
> 예: `getElementsByTagName('li')` 를 잡아 두고 `<li>` 를 하나 붙이면 잡아 둔 목록의 `length` 가 늘어난다.

> **정적 컬렉션(static collection)** — 돌려받는 순간의 **스냅샷**. 그 뒤 DOM 이 바뀌어도 변하지 않는다.\
> 예: `querySelectorAll('li')` 결과는 `<li>` 를 붙여도 `length` 가 그대로다.

## 이 주제가 답하려는 질문

1. **같은 조건으로 잡은 두 목록이 언제 갈리나.** 그리고 **한 번만 읽으면 왜 못 가르나.**
2. **무엇이 라이브인가를 어떻게 아나.** 타입 이름인가, 그 타입을 만든 API 인가.
3. **어디서부터 찾나.** `document` 에서 찾는 것과 요소에서 찾는 것이 어떻게 다르고, 어디서 직관과 어긋나나.

## 이 갈래의 관측 창 — 창 3 이 이 주제의 본체다

[01번 주제](../01-document-and-node-tree/2-summary.md)에서 세운 창 셋 중 **세 번째가 여기서 주인공**이 된다.

```text
  창 1  --dump-dom            결과 트리를 글자로            (바꾼 결과를 확인할 때)
  창 2  length · constructor.name   무엇이 몇 개인가         (한 시점의 상태)
  창 3  ★ 같은 것을 두 번 읽기      DOM 을 바꾸기 전 / 바꾼 뒤
        -> 이 창이 없으면 라이브와 정적이 '완전히 같은 객체' 로 보인다

  창 4 (이 주제 고유)  Object.prototype.toString + constructor 비교
        -> '타입이 같은데 동작이 다르다' 를 보이는 자리.  타입만 봐서는 못 가른다
```

- **창 3 은 반드시 세 시점**이 필요하다 — 잡기 · 바꾸기 · 다시 읽기. 두 시점만 쓰면 아무 일도 안 일어난 것처럼 보인다.
- **창 4 가 없으면 「`NodeList` 는 정적」이라는 틀린 요약을 못 깬다.** 뒤에서 그 요약이 **절반만 맞다**는 것을 출력으로 본다.

## 동작 방식

### (0) ★ 창 3 — 같은 조건으로 넷을 잡고 DOM 을 바꾼다

**언제 쓰나** — 조회 결과를 **변수에 담아 두고 나중에 쓰는** 모든 자리. **이 주제의 본체다.**

```html
<!-- ex02a.html -->
<!doctype html>
<meta charset="utf-8">
<title>02a</title>
<ul id="list">
  <li class="item">A</li>
  <li class="item">B</li>
</ul>
<script>
const O = [];
const list = document.getElementById('list');
const byTag = document.getElementsByTagName('li');
const byClass = document.getElementsByClassName('item');
const kids = list.children;
const snap = document.querySelectorAll('li');
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = when => O.push(padw(when, 16) +
  'byTag=' + byTag.length + '  byClass=' + byClass.length +
  '  children=' + kids.length + '  querySelectorAll=' + snap.length);
O.push('byTag  = ' + byTag.constructor.name);
O.push('kids   = ' + kids.constructor.name);
O.push('snap   = ' + snap.constructor.name);
O.push('');
row('처음');
list.appendChild(Object.assign(document.createElement('li'), {className: 'item', textContent: 'C'}));
row('li 하나 추가');
list.firstElementChild.remove();
row('li 하나 제거');
O.push('');
O.push('snap[0] 은 지운 A 를 아직 들고 있다: snap[0].textContent = ' + JSON.stringify(snap[0].textContent));
O.push('snap[0].isConnected = ' + snap[0].isConnected);
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
byTag  = HTMLCollection
kids   = HTMLCollection
snap   = NodeList

처음            byTag=2  byClass=2  children=2  querySelectorAll=2
li 하나 추가    byTag=3  byClass=3  children=3  querySelectorAll=2
li 하나 제거    byTag=2  byClass=2  children=2  querySelectorAll=2

snap[0] 은 지운 A 를 아직 들고 있다: snap[0].textContent = "A"
snap[0].isConnected = false
(exit 0)
```

```text
   같은 <li> 를 네 방식으로 잡아 둔다

   byTag   = document.getElementsByTagName('li')     HTMLCollection
   byClass = document.getElementsByClassName('item') HTMLCollection
   kids    = list.children                            HTMLCollection
   snap    = document.querySelectorAll('li')          NodeList

           t0 잡는다      t1 <li>C</li> 추가     t2 <li>A</li> 제거
   byTag      2       ->        3          ->        2
   byClass    2       ->        3          ->        2
   kids       2       ->        3          ->        2
   snap       2       ->        2          ->        2      ★ 혼자 안 움직인다
```

그림 해설 (한 단계씩):

- **네 개가 t0 에서 전부 같은 답**을 준다. 여기서 멈추면 차이를 영원히 못 본다.
- **t1 에서 셋만 따라 늘었다.** 라이브 컬렉션은 「그때 찾은 결과」를 담아 둔 것이 아니라 **조건 자체를 들고 있다.**
- **t2 에서 셋은 다시 줄었는데 정적은 여전히 2** 다 — 그런데 그 2 가 **처음의 2 와 다른 뜻**이다. 스냅샷은 **이미 지운 `A` 를 아직 들고 있다.**
- 그래서 **정적 컬렉션은 「문서에 없는 노드」를 들고 있을 수 있다.** 이것이 메모리를 붙드는 경로가 되기도 한다(목록의 **20번 주제**).

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,10p'
snap[0] 은 지운 A 를 아직 들고 있다: snap[0].textContent = "A"
snap[0].isConnected = false
(exit 0)
```

비용 — 라이브 컬렉션은 **읽을 때 다시 계산될 수 있다.** 반복문 조건에 `live.length` 를 두는 것이 느려지는 근거가 여기다(아래 (2)).

### (1) 조회 API 다섯과 그 반환 타입

**언제 쓰나** — 어떤 조회를 쓸지 고를 때. **타입을 먼저 보고 그 다음에 성질을 본다.**

```text
  API                                 반환                       라이브?     어디에 있나
  ---------------------------------  -------------------------  ---------  --------------------
  document.getElementById(id)         Element | null             -          document 에만
  getElementsByTagName(name)          HTMLCollection             라이브      Document · Element
  getElementsByClassName(cls)         HTMLCollection             라이브      Document · Element
  el.children                         HTMLCollection             라이브      ParentNode
  querySelector(sel)                  Element | null             -          ParentNode
  querySelectorAll(sel)               NodeList                   ★ 정적      ParentNode
  node.childNodes                     NodeList                   ★ 라이브    Node
  el.closest(sel)                     Element | null             -          Element   (위로 올라간다)
  el.matches(sel)                     boolean                    -          Element
```

- **`HTMLCollection` 은 언제나 라이브**다. 예외가 없다.
- **`NodeList` 는 만든 쪽이 정한다** — `querySelectorAll` 은 정적, `childNodes` 는 라이브.
- **`getElementById` 만 `document` 에 있다.** 요소에는 없다 — 아래 (4).
- `closest()` 는 이 목록에서 **유일하게 위로 올라가는** 조회다. 자기 자신부터 본다.

### (2) ★ 같은 `NodeList` 인데 한쪽만 따라 변한다

**언제 쓰나** — 「`NodeList` 는 정적이다」를 외우고 있을 때. **그 요약이 절반만 맞다.**

```html
<!-- ex02b.html -->
<!doctype html>
<meta charset="utf-8">
<title>02b</title>
<div id="box"><span>A</span><span>B</span></div>
<script>
const O = [];
const box = document.getElementById('box');
const cn = box.childNodes;
const qs = box.querySelectorAll('span');
O.push('cn = box.childNodes            ' + Object.prototype.toString.call(cn));
O.push('qs = box.querySelectorAll(...)  ' + Object.prototype.toString.call(qs));
O.push('cn.constructor === qs.constructor = ' + (cn.constructor === qs.constructor));
O.push('둘 다 NodeList 인가 = ' + [cn instanceof NodeList, qs instanceof NodeList].join('/'));
O.push('');
O.push('붙이기 전  cn.length = ' + cn.length + '   qs.length = ' + qs.length);
box.appendChild(Object.assign(document.createElement('span'), {textContent: 'C'}));
O.push('붙인 뒤    cn.length = ' + cn.length + '   qs.length = ' + qs.length);
O.push('');
O.push('qs 를 다시 잡으면 = ' + box.querySelectorAll('span').length);
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
cn = box.childNodes            [object NodeList]
qs = box.querySelectorAll(...)  [object NodeList]
cn.constructor === qs.constructor = true
둘 다 NodeList 인가 = true/true

붙이기 전  cn.length = 2   qs.length = 2
붙인 뒤    cn.length = 3   qs.length = 2

qs 를 다시 잡으면 = 3
(exit 0)
```

```text
   cn = box.childNodes            qs = box.querySelectorAll('span')
        [object NodeList]              [object NodeList]
        constructor 가 같다  ==========  constructor 가 같다

   <span>C</span> 를 붙인다
        cn.length  2 -> 3              qs.length  2 -> 2
        ^^^^^^^^^^^^^^^^^              ^^^^^^^^^^^^^^^^^
        라이브                          정적
```

그림 해설 (한 단계씩):

- **타입이 한 글자도 다르지 않다.** `Object.prototype.toString` 도 같고 `constructor` 도 같은 객체다.
- **갈리는 것은 그 목록을 만든 API** 다. 명세가 「`querySelectorAll` 은 정적 `NodeList` 를 반환한다」고 **그 자리에서** 못 박았다.
- 그래서 외울 것은 타입 이름이 아니라 「**누가 만들었나**」다.
- **다시 잡으면 정적도 최신이 된다** — 출력의 마지막 줄이 그것이다. 정적이 「낡았다」가 아니라 「**그 시점을 고정했다**」는 뜻이다.

비용 — 정적 `NodeList` 는 만들 때 **한 번에 다 훑는다.** 라이브는 **읽을 때마다** 유효성을 확인한다(캐시가 있지만 DOM 이 바뀌면 무효가 된다).

### (3) ★ 라이브 컬렉션을 순회하며 지우면 절반만 지워진다

**언제 쓰나** — 목록을 비우는 반복문. **이 주제에서 실제로 사고가 나는 자리다.**

```html
<!-- ex02e.html -->
<!doctype html>
<meta charset="utf-8">
<title>02e</title>
<div id="wrapA"><p class="x">1</p><p class="x">2</p><p class="x">3</p><p class="x">4</p></div>
<div id="wrapB"><p class="x">1</p><p class="x">2</p><p class="x">3</p><p class="x">4</p></div>
<script>
const O = [];
const left = el => '[' + [...el.children].map(c => c.textContent).join(', ') + ']';
const A = document.getElementById('wrapA'), B = document.getElementById('wrapB');
const live = A.getElementsByClassName('x');
O.push('A 처음 = ' + left(A) + '   live.length = ' + live.length);
for (let i = 0; i < live.length; i++) { O.push('  i=' + i + ' 에서 지운다: ' + live[i].textContent); live[i].remove(); }
O.push('A 나중 = ' + left(A) + '   live.length = ' + live.length);
O.push('');
const snap = B.querySelectorAll('.x');
O.push('B 처음 = ' + left(B) + '   snap.length = ' + snap.length);
for (let i = 0; i < snap.length; i++) { snap[i].remove(); }
O.push('B 나중 = ' + left(B) + '   snap.length = ' + snap.length);
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02e.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
A 처음 = [1, 2, 3, 4]   live.length = 4
  i=0 에서 지운다: 1
  i=1 에서 지운다: 3
A 나중 = [2, 4]   live.length = 2

B 처음 = [1, 2, 3, 4]   snap.length = 4
B 나중 = []   snap.length = 4
(exit 0)
```

```text
   i=0 에서 live[0] 을 지운다
      [1] [2] [3] [4]        live.length = 4
       ^ 지움
      [2] [3] [4]            live.length = 3   ★ 전부 한 칸씩 당겨졌다

   i=1 에서 live[1] 을 지운다     -> [2] 가 아니라 [3] 이 지워진다
      [2] [3] [4]
           ^ 지움
      [2] [4]                live.length = 2

   i=2 이고 live.length 도 2  -> 반복문이 끝난다.   [2] [4] 가 남는다
```

그림 해설 (한 단계씩):

- **지울 때마다 뒤가 앞으로 당겨 온다.** `i` 는 늘기만 해서 **한 칸씩 건너뛴다.**
- **끝나는 조건도 같이 줄어든다** — `i < live.length` 의 오른쪽이 매 판 작아지므로 반복이 **절반에서 멈춘다.**
- **정적 스냅샷으로 하면 전부 지워진다.** 출력의 아래쪽이 그것이다 — `snap.length` 는 끝까지 4 이고 `B` 는 비었다.
- 고치는 법은 셋이다 — **정적으로 잡기**(`querySelectorAll`) · **뒤에서부터 돌기**(`for (let i = n - 1; i >= 0; i--)`) · **`while (live.length) live[0].remove()`**.

비용 — 없음. 다만 **`live.length` 를 반복 조건에 두면 매 판 다시 확인**한다.

### (4) 어디서부터 찾나 — 그리고 어디서 직관과 어긋나나

**언제 쓰나** — 요소에 대고 조회할 때. **선택자가 「어디를 기준으로」 해석되는지가 직관과 다르다.**

```html
<!-- ex02c.html -->
<!doctype html>
<meta charset="utf-8">
<title>02c</title>
<div id="outer">
  <p id="a">바깥 문단</p>
  <div id="inner"><p id="b">안쪽 문단</p></div>
</div>
<script>
const O = [];
const outer = document.getElementById('outer');
const ids = ns => '[' + [...ns].map(n => n.id).join(', ') + ']';
O.push('typeof document.getElementById = ' + typeof document.getElementById);
O.push('typeof outer.getElementById    = ' + typeof outer.getElementById);
O.push('');
O.push("outer.querySelectorAll('div p')       = " + ids(outer.querySelectorAll('div p')));
O.push("outer.querySelectorAll(':scope > p')  = " + ids(outer.querySelectorAll(':scope > p')));
O.push("outer.querySelectorAll('p')           = " + ids(outer.querySelectorAll('p')));
O.push("document.querySelector('p').id        = " + document.querySelector('p').id);
O.push('');
const detached = document.createElement('div');
detached.innerHTML = '<p id="c">문서 밖</p>';
O.push("떼어낸 트리 안의 id=c 를 document.getElementById 로 = " + document.getElementById('c'));
O.push("같은 것을 detached.querySelector('#c') 로 = " + detached.querySelector('#c').textContent);
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
typeof document.getElementById = function
typeof outer.getElementById    = undefined

outer.querySelectorAll('div p')       = [a, b]
outer.querySelectorAll(':scope > p')  = [a]
outer.querySelectorAll('p')           = [a, b]
document.querySelector('p').id        = a

떼어낸 트리 안의 id=c 를 document.getElementById 로 = null
같은 것을 detached.querySelector('#c') 로 = 문서 밖
(exit 0)
```

```text
   <div id=outer>                outer.querySelectorAll('div p')  ->  [a, b]
     <p id=a>                                                          ^^^ ★ a 도 잡힌다
     <div id=inner>
       <p id=b>

   왜인가 — 선택자는 'outer 안에서' 해석되는 것이 아니라
            '문서 전체를 기준으로' 매치되고, 결과만 outer 의 자손으로 거른다.
            a 의 조상에 <div id=outer> 가 있으므로 'div p' 를 만족한다.

   outer.querySelectorAll(':scope > p')  ->  [a]
                          ^^^^^^ :scope 가 '기준 요소' 를 가리킨다
```

그림 해설 (한 단계씩):

- **요소에 대고 부른 `querySelectorAll` 은 「그 요소 안에서만 매치」하지 않는다.** 매치는 문서 전체를 보고, **걸러내기만** 그 요소의 자손으로 한다.
- 그래서 `outer.querySelectorAll('div p')` 가 **`outer` 자신을 조상으로 써서** `a` 를 잡는다. 「outer 안에 있는 `div` 의 `p`」를 의도했다면 틀린 것이다.
- **`:scope` 가 그 기준 요소를 가리킨다.** `:scope > p` 라야 직계 자식만 잡는다.
- **`getElementById` 는 `document` 에만 있다.** 출력의 첫 두 줄이 근거다 — 요소에서 부르면 `undefined` 라 **`TypeError` 가 난다.** `id` 는 문서 전체에서 유일해야 하는 것이라 **탐색 범위라는 개념이 없다.**
- **문서에서 떼어낸 트리 안의 `id` 는 `document.getElementById` 로 못 찾는다.** 그 트리의 루트에 대고 `querySelector('#c')` 를 쓰면 찾는다 — 출력의 마지막 두 줄이다.

비용 — `getElementById` 는 **문서가 들고 있는 id 색인**을 본다. 선택자 엔진을 도는 `querySelector('#x')` 보다 직접적이다.

### (5) 잘못된 선택자는 조용히 실패하지 않는다

**언제 쓰나** — 선택자를 문자열로 조립할 때(사용자 입력·변수 결합).

```html
<!-- ex02d.html -->
<!doctype html>
<meta charset="utf-8">
<title>02d</title>
<p class="ok">문단</p>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const tryIt = (label, fn) => {
  try { O.push(padw(label, 38) + '-> ' + fn()); }
  catch (e) { O.push(padw(label, 38) + '-> ' + e.constructor.name + ': ' + e.message); }
};
tryIt("querySelectorAll('.ok')", () => document.querySelectorAll('.ok').length + '개');
tryIt("querySelectorAll('')", () => document.querySelectorAll('').length + '개');
tryIt("querySelectorAll('.5cls')", () => document.querySelectorAll('.5cls').length + '개');
tryIt("querySelectorAll('div:has(')", () => document.querySelectorAll('div:has(').length + '개');
tryIt("querySelectorAll('p::totally-bogus')", () => document.querySelectorAll('p::totally-bogus').length + '개');
tryIt("querySelectorAll(':is(.ok, ::bogus)')", () => document.querySelectorAll(':is(.ok, ::bogus)').length + '개');
tryIt("getElementsByTagName('div:has(')", () => document.getElementsByTagName('div:has(').length + '개');
tryIt("getElementsByClassName('.ok')", () => document.getElementsByClassName('.ok').length + '개');
tryIt("matches('div:has(')", () => document.querySelector('p').matches('div:has('));
tryIt("잡은 것의 정체", () => {
  try { document.querySelectorAll('div:has('); } catch (e) {
    return 'e.name=' + e.name + '  DOMException=' + (e instanceof DOMException) +
           '  JS SyntaxError=' + (e instanceof SyntaxError) + '  e.code=' + e.code;
  }
});
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02d.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
querySelectorAll('.ok')               -> 1개
querySelectorAll('')                  -> DOMException: Failed to execute 'querySelectorAll' on 'Document': The provided selector is empty.
querySelectorAll('.5cls')             -> DOMException: Failed to execute 'querySelectorAll' on 'Document': '.5cls' is not a valid selector.
querySelectorAll('div:has(')          -> DOMException: Failed to execute 'querySelectorAll' on 'Document': 'div:has(' is not a valid selector.
querySelectorAll('p::totally-bogus')  -> DOMException: Failed to execute 'querySelectorAll' on 'Document': 'p::totally-bogus' is not a valid selector.
querySelectorAll(':is(.ok, ::bogus)') -> 1개
getElementsByTagName('div:has(')      -> 0개
getElementsByClassName('.ok')         -> 0개
matches('div:has(')                   -> DOMException: Failed to execute 'matches' on 'Element': 'div:has(' is not a valid selector.
잡은 것의 정체                        -> e.name=SyntaxError  DOMException=true  JS SyntaxError=false  e.code=12
(exit 0)
```

그림 해설 (한 단계씩):

- **`querySelector` 계열은 던진다.** CSS 와 정반대다 — 스타일시트에서 무효한 선택자는 **조용히 버려지는데**([CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)), API 로 물으면 **예외**가 온다.
- **`getElementsBy*` 는 안 던진다.** 선택자가 아니라 **이름·클래스 문자열**을 받기 때문이다 — `getElementsByClassName('.ok')` 가 `.ok` 라는 **이름의 클래스**를 찾아 0개를 돌려준다. 점을 붙인 채 넘기는 실수가 여기서 조용히 통과한다.
- **`:is()` 안의 무효한 선택자는 던지지 않는다.** 너그러운 선택자 목록이라 그 인자만 버린다([CSS 11번 주제](../../languages/css/syntax/11-is-where-not/2-summary.md)) — 출력에서 `1개` 가 나온 줄이다.
- ★ **잡힌 것의 정체는 `SyntaxError` 라는 이름의 `DOMException`** 이다. **JS 의 `SyntaxError` 가 아니다**(`instanceof SyntaxError` 가 `false`). `catch (e) { if (e instanceof SyntaxError) }` 로 거르면 **안 걸린다.**

### (6) 트리를 통째로 갈면 — 라이브는 따라가고 정적은 남는다

**언제 쓰나** — `innerHTML` 로 영역을 다시 그리는 모든 자리. **04번 주제와 이어지는 지점이다.**

```html
<!-- ex02f.html -->
<!doctype html>
<meta charset="utf-8">
<title>02f</title>
<div id="dup">첫째</div>
<div id="dup">둘째</div>
<div id="host"><p class="q">하나</p><p class="q">둘</p></div>
<script>
const O = [];
O.push('같은 id 가 둘일 때 getElementById 가 준 것 = ' + JSON.stringify(document.getElementById('dup').textContent));
O.push('querySelectorAll("#dup").length = ' + document.querySelectorAll('#dup').length);
O.push('');
const host = document.getElementById('host');
const live = host.getElementsByClassName('q');
const snap = host.querySelectorAll('.q');
O.push('갈아치우기 전  live=' + live.length + '  snap=' + snap.length);
host.innerHTML = '<p class="q">A</p><p class="q">B</p><p class="q">C</p>';
O.push('innerHTML 로 통째 교체 뒤  live=' + live.length + '  snap=' + snap.length);
O.push('live 가 가리키는 글자 = ' + [...live].map(e => e.textContent).join(','));
O.push('snap 이 가리키는 글자 = ' + [...snap].map(e => e.textContent).join(','));
O.push('snap[0].isConnected = ' + snap[0].isConnected);
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02f.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
같은 id 가 둘일 때 getElementById 가 준 것 = "첫째"
querySelectorAll("#dup").length = 2

갈아치우기 전  live=2  snap=2
innerHTML 로 통째 교체 뒤  live=3  snap=2
live 가 가리키는 글자 = A,B,C
snap 이 가리키는 글자 = 하나,둘
snap[0].isConnected = false
(exit 0)
```

그림 해설 (한 단계씩):

- **같은 `id` 가 둘이면 `getElementById` 는 문서 순서로 첫 것**을 준다. 던지지도 경고하지도 않는다 — `querySelectorAll('#dup')` 은 **둘 다** 준다.
- **`innerHTML` 한 줄이 그 안을 통째로 갈아엎는다.** 라이브 컬렉션은 **새로 생긴 `A`·`B`·`C` 를 가리키고**, 정적 스냅샷은 **사라진 `하나`·`둘` 을 그대로 들고 있다.**
- 그래서 **정적 스냅샷은 「지운 화면의 잔해」를 붙들 수 있다.** `isConnected` 가 `false` 인 노드를 배열에 담아 두는 것이 누수 경로가 된다(목록의 **20번 주제**).
- **이 실험이 창 3 의 가장 센 형태**다 — 바꾼 것이 한 노드가 아니라 하위 트리 전체인데도 두 목록이 각자의 계약대로 움직인다.

비용 — `innerHTML` 쓰기는 **파싱 + 기존 트리 폐기**다. 값은 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에서 실제로 잰다.

```html demo
<ul id="list"><li class="item">A</li><li class="item">B</li></ul>
<button id="add">li 하나 더</button>
<p id="report"></p>
<script>
  const list = document.getElementById('list');
  const live = list.getElementsByClassName('item');
  const snap = list.querySelectorAll('.item');
  const report = () => document.getElementById('report').textContent =
    '라이브(getElementsByClassName) ' + live.length + '개 · 정적(querySelectorAll) ' + snap.length + '개';
  document.getElementById('add').onclick = () => {
    list.append(Object.assign(document.createElement('li'), {className: 'item', textContent: '새 항목'}));
    report();
  };
  report();
</script>
```

> **보이는 것** — 처음에는 「라이브 2개 · 정적 2개」가 찍혀 있다. 버튼을 한 번 누르면 목록에 `새 항목` 이 붙으면서 문구가 「라이브 3개 · 정적 2개」로 바뀐다. 정적 쪽 숫자는 몇 번을 눌러도 2 에서 안 움직인다.\
> **바꿔 볼 것** — `list.querySelectorAll('.item')` 을 `report()` 안으로 옮겨 **읽을 때마다 새로 잡으면** 두 숫자가 같이 올라간다 · `getElementsByClassName` 을 `querySelectorAll` 로 바꾸면 두 줄이 다 멈춘다.

비용 — 없음.

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
document.getElementById('x')            // Element | null — document 에만 있다
root.querySelector('.a > b')            // 첫 하나 | null
root.querySelectorAll('.a')             // 정적 NodeList
root.getElementsByTagName('li')         // 라이브 HTMLCollection
root.getElementsByClassName('item')     // 라이브 HTMLCollection
el.closest('.card')                     // 자기 자신부터 위로
el.matches('.card > li')                // boolean
root.querySelectorAll(':scope > p')     // 기준 요소의 직계만

[...root.querySelectorAll('.a')]        // 배열로 — map·filter 가 필요하면
Array.from(root.children)               // 라이브를 그 자리에서 얼린다
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
for (let i = 0; i < live.length; i++) live[i].remove();   // 절반만 지워진다
document.getElementsByClassName('.item')                  // 점을 붙이면 0개
outer.getElementById('a')                                 // TypeError
outer.querySelectorAll('div p')                           // outer 자신이 조상으로 쓰인다
catch (e) { if (e instanceof SyntaxError) }               // DOMException 이라 안 걸린다
snap.forEach(...)                                         // 되지만 live.forEach 는 없다
```

- **`HTMLCollection` 에는 `forEach` 가 없다.** `NodeList` 에는 있다 — 같은 「목록」인데 표면이 다르다. `[...live]` 로 펼치거나 `Array.from` 을 쓴다.
- **`[...live]` 는 그 자리에서 정적 배열을 만든다.** 라이브를 얼리는 가장 짧은 방법이다.

### 어디서 헷갈리나

- **「`NodeList` 는 정적, `HTMLCollection` 은 라이브」는 절반만 맞다.** `childNodes` 가 라이브 `NodeList` 다.
- **`querySelector` 는 「첫 번째」를 문서 순서로 준다** — 내가 쓴 선택자의 순서가 아니다.
- **`:scope` 를 빼먹으면 조상이 새어 들어온다.** 요소에 대고 자손 조합자를 쓸 때만 나는 일이다.
- **`getElementsBy*` 에 선택자 문법을 쓰면 조용히 0개**다. 던지지 않는다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 중 다섯이 **에러 없이 조용히 어긋난다.**

### 1. 라이브 컬렉션을 앞에서부터 순회하며 지운다

실측에서 항목 **4개 중 2개만** 지워졌다. 예외도 경고도 없다.\
증상은 「왜 두 개가 남지」 하나뿐이고, 항목이 홀수면 「하나만 남네」가 된다.

### 2. 조회 결과를 잡아 두고 나중에 쓴다

`querySelectorAll` 로 잡아 둔 목록은 **그 뒤에 추가된 요소를 모른다.** 목록을 그려 놓고 항목을 추가하는 화면에서, 새 항목에만 리스너가 안 붙는 사고가 여기서 난다.\
반대로 `getElementsBy*` 로 잡아 두면 **내가 모르는 사이에 늘어나** 있다.

### 3. 타입 이름으로 라이브 여부를 판정한다

`box.childNodes` 는 **라이브 `NodeList`** 다. 실측에서 `constructor` 까지 같은데 동작이 갈렸다.

### 4. 요소에 대고 `getElementById` 를 부른다

`typeof outer.getElementById` 가 **`undefined`** 다. 호출하면 `TypeError` 가 난다 — 이것만은 **시끄럽게 실패**한다.

### 5. `outer.querySelectorAll('div p')` 를 「outer 안의 div 의 p」로 읽는다

**`outer` 자신이 조상으로 쓰인다.** 실측에서 바깥 문단까지 잡혔다.\
`:scope` 를 넣거나 선택자를 자손 조합자 없이 쓴다.

### 6. `SyntaxError` 를 JS 예외로 잡으려 한다

`e.name` 은 `'SyntaxError'` 인데 **`e instanceof SyntaxError` 는 `false`** 다. 실제 정체는 `DOMException`(`code = 12`)이다.\
거르려면 `e.name === 'SyntaxError'` 나 `e instanceof DOMException` 을 본다.

## 구현 세부사항 대 언어 보장

여기서 「언어 보장」은 **명세(WHATWG DOM)가 정한 것**이고, 「구현」은 **Blink 가 하는 것**이다.

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `HTMLCollection` 이 **언제나 라이브**인 것 | **명세**(DOM §4.2.10 — 「collection」은 라이브로 정의된다) |
| `querySelectorAll` 이 **정적** `NodeList` 를 주는 것 | **명세**(DOM §4.2.6 — 「static」이라고 명시) |
| `childNodes` 가 **라이브** `NodeList` 인 것 | **명세**(DOM §4.4) |
| ★ 「라이브냐 정적이냐」가 **타입이 아니라 만든 API** 에 달린 것 | **명세.** 구현 최적화가 아니다 |
| `getElementById` 가 `Document` 에만 있는 것 | **명세**(`NonElementParentNode` 믹스인 — `Document`·`DocumentFragment` 만) |
| 무효한 선택자에 `SyntaxError` `DOMException` 을 던지는 것 | **명세**(DOM §4.2.6 — 「throw a "SyntaxError" DOMException」) |
| `:scope` 가 기준 요소를 가리키는 것 | **명세**(Selectors 4 + DOM 의 scoping root) |
| 요소에 대고 부른 선택자가 **문서 전체를 보고 매치**하는 것 | **명세**(DOM 의 「scope-matching a selectors string」) |
| `getElementsByClassName('.ok')` 가 0개인 것 | **명세**(인자는 클래스 이름 목록이지 선택자가 아니다) |
| `DOMException.code` 가 `12` 인 것 | **명세**(레거시 코드 표 — `SYNTAX_ERR`) |
| **예외 메시지 문구**(`'div:has(' is not a valid selector.`) | **관찰**(Chrome 151). 명세는 문구를 정하지 않는다 |
| 라이브 컬렉션을 **읽을 때 다시 계산하는지, 캐시하는지** | **구현**(Blink). 명세는 「살아 있다」만 정하고 방법은 안 정한다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 한 번 찾아 바로 쓴다 | `querySelector`·`querySelectorAll` | — |
| 목록을 잡아 두고 뒤에 순회하며 **지운다** | `querySelectorAll` 스냅샷 · 뒤에서부터 돌기 | 라이브 컬렉션 앞에서부터 |
| 「지금 몇 개인가」를 계속 묻는다 | 라이브 컬렉션(`children`·`getElementsBy*`) | 매번 `querySelectorAll` |
| `id` 하나로 찾는다 | `document.getElementById` | `querySelector('#x')`(굳이) |
| 요소 안에서만 찾는다 | `:scope` 를 붙인다 | 자손 조합자만 쓴다 |
| `map`·`filter` 를 건다 | `[...컬렉션]` · `Array.from` | 라이브에 직접(메서드가 없다) |
| 조상을 찾는다 | `closest()` | `parentElement` 루프 |

판단 규칙 두 줄.

- **「이 목록을 지금 쓰고 버리나, 들고 있나」를 먼저 묻는다.** 들고 있을 것이면 라이브냐 정적이냐가 **반드시** 결론을 바꾼다.
- **지우는 반복문은 정적으로 잡거나 뒤에서부터 돈다.** 이 두 줄이 이 주제의 실무 전부다.

## 핵심 문장

- **같은 조건으로 잡은 두 목록이 받은 순간에는 같은 답을 준다.** 갈리는 것은 **DOM 을 바꾼 뒤 다시 읽을 때**다 — 실측에서 `li` 하나를 붙이자 라이브 셋은 3, 정적은 2 였다.
- **「`NodeList` 는 정적」은 절반만 맞다.** `childNodes` 는 **라이브 `NodeList`** 이고, 실측에서 `constructor` 까지 같은데 동작이 갈렸다. 외울 것은 타입이 아니라 「**누가 만들었나**」다.
- **`HTMLCollection` 은 예외 없이 라이브**다. 이것만 타입으로 외워도 된다.
- **라이브 컬렉션을 앞에서부터 지우면 절반만 지워진다.** 실측에서 4개 중 2개가 남았고, **에러가 없다.**
- **정적 스냅샷은 이미 문서에서 떨어진 노드를 들고 있을 수 있다** — 실측에서 `snap[0].isConnected` 가 `false` 였다.
- **`getElementById` 는 `document` 에만 있다.** 요소에서 부르면 `TypeError` — 이 주제에서 **유일하게 시끄러운 실패**다.
- **요소에 대고 부른 선택자도 문서 전체를 보고 매치한다.** `:scope` 가 없으면 **기준 요소 자신이 조상으로 쓰인다.**
- **무효한 선택자는 `SyntaxError` 라는 이름의 `DOMException`** 이다 — CSS 가 조용히 버리는 것과 정반대이고, JS 의 `SyntaxError` 로는 못 잡는다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 02번)
- [01번 주제](../01-document-and-node-tree/2-summary.md) — **노드와 컬렉션 타입의 정본.** 그쪽은 「나무에 무엇이 있나」까지, 여기는 「그것을 찾은 결과가 살아 있나」부터
- [03번 주제](../03-node-creation-insertion-removal/2-summary.md) — 이 주제의 실험이 DOM 을 바꾸는 데 쓰는 API 들의 정본
- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) — `innerHTML` 로 트리를 통째로 갈면 **잡아 둔 라이브 컬렉션이 어떻게 되는지**가 이어진다
- [CSS 08번 주제](../../languages/css/syntax/08-basic-selectors-and-combinators/2-summary.md) — **선택자 문법의 정본.**\
  그쪽은 **선택자가 무엇을 고르나**까지, 여기는 **그 선택자를 API 로 던졌을 때의 계약**(정적·예외·`:scope`)부터다
- [CSS 11번 주제](../../languages/css/syntax/11-is-where-not/2-summary.md) — `:is()` 가 너그러운 목록이라 **무효한 인자에 안 던지는** 근거
- [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md) — 같은 무효 선택자를 **스타일시트에서는 조용히 버린다**는 정반대 쪽
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **07번**(`id` 와 조각 식별자) — `id` 가 문서에서 유일해야 한다는 규칙의 정본. 여기는 **그래서 `getElementById` 에 탐색 범위가 없다**는 결과만
- 목록의 **20번 주제**(리스너 수명) — 정적 스냅샷이 떨어진 노드를 붙드는 것이 누수가 되는 경로

## 용어 풀이

- **라이브 컬렉션(live collection)** — DOM 이 바뀌면 따라 바뀌는 목록. `HTMLCollection` 과 `childNodes`.
- **정적 컬렉션(static collection)** — 돌려받는 순간의 스냅샷. `querySelectorAll` 의 결과.
- **`HTMLCollection`** — 요소만 담는 라이브 목록. `forEach` 가 없고 `namedItem` 이 있다.
- **`NodeList`** — 노드를 담는 목록. **만든 API 가 라이브인지 정적인지 정한다.** `forEach` 가 있다.
- **`:scope`** — 조회의 **기준 요소**를 가리키는 의사 클래스. 요소에 대고 부른 조회에서만 뜻이 있다.
- **`DOMException`** — 플랫폼이 던지는 예외 타입. `name` 이 `'SyntaxError'` 여도 **JS 의 `SyntaxError` 가 아니다.**
- **`closest()`** — 자기 자신부터 조상으로 올라가며 선택자에 맞는 첫 요소를 찾는다.
- **스냅샷(snapshot)** — 그 시점의 결과를 고정한 것. 낡은 것이 아니라 **고정된 것**이다.
- **id 색인** — 문서가 `id` 별로 들고 있는 조회표. `getElementById` 가 이것을 본다.

## 더 들어가면

- **`getElementsByTagName` 이 라이브인 것은 DOM Level 1(1998) 의 설계**다. 그때는 「문서를 계속 보고 있는 목록」이 자연스러웠고, `querySelectorAll`(2008, Selectors API)이 나오면서 **정적이 기본**이 됐다. 오늘 새로 쓰는 코드가 정적을 쓰는 이유는 성능이 아니라 **예측 가능성**이다.
- **`getElementsByTagName('*')` 은 문서 전체 요소를 라이브로 들고 있는 것**이라 옛 코드에서 성능 함정이었다. 오늘도 `document.all` 과 함께 남아 있지만 쓸 일이 없다.
- **`querySelectorAll` 의 정적 `NodeList` 는 「배열 같은 것」이지 배열이 아니다.** `map` 이 없다. `forEach` 만 있는 이유는 DOM 명세가 그 하나만 넣었기 때문이다.
- **선택자 매치를 문서 기준으로 하는 설계는 Selectors API 초안부터 논쟁**이었다. 「요소 안에서만 매치」가 직관적인데 **명시도·조합자 계산이 달라져** 그렇게 못 했고, 대신 `:scope` 가 들어왔다.
- **Shadow DOM 경계를 넘는 조회는 없다.** `document.querySelector` 는 그림자 트리 안을 못 본다 — 그 규칙은 [목록의 **12번 주제**](../12-shadow-dom/)가 정본이다.
