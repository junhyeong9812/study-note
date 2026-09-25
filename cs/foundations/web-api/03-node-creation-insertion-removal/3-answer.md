# web-api/03 — 노드 생성·삽입·이동·제거: `createElement`·`append` 계열·`remove` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「Mutation algorithms」로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **이 주제의 블록에는 흔들리는 칸이 없다** — 트리 문자열·자식 수·반환값은 다시 돌려도 한 글자도 같아야 한다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이미 트리에 있는 노드를 다른 곳에 넣으면 — 원래 자리에서 사라진다

**출력**

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

**전후의 자식**

- `left` — `s1`·`s2` → **`s2` 하나만** 남는다.
- `right` — `b1` → `b1`·**`s1`**.

**문서 안 `<span>` 개수**

- **2 그대로**다. 복사였다면 3 이 됐을 것이다 — **이 한 줄이 「이동」의 결정적 증거**다.

**`s1.parentElement.id`**

- 전에 **`left`**, 후에 **`right`**.

**명세의 어느 단계**

```text
   appendChild(node) 가 내부에서 하는 일

   1) pre-insert 검사      부모가 될 수 있는 종류인가 · 조상을 자손에 넣는가
   2) ★ node 에 부모가 있으면 remove 한다      <- 내가 안 시켰는데 일어난다
   3) insert 한다

   그래서 '넣기' 한 번에 '빼기' 가 끼어 있다
```

### 2. 두 메서드가 받는 것과 돌려주는 것

**출력**

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

**`r1` 과 `r2`**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '5,6p'
appendChild 반환값 === 넣은 노드 = true
append 반환값 = undefined
(exit 0)
```

- `r1` = **넣은 노드 자신**(`appendChild` 반환값 === `el` 이 `true`).
- `r2` = **`undefined`**.

**세 번째 줄 뒤의 두 수**

- `childNodes.length` = **5**, `children.length` = **3**.
- 문자열 둘이 **`Text` 노드 둘**이 되어 `childNodes` 에만 보인다([01번 주제](../01-document-and-node-tree/2-summary.md)).

**네 번째 줄**

- **`TypeError`** 를 던진다 — `Failed to execute 'appendChild' on 'Node': parameter 1 is not of type 'Node'.`
- 같은 문자열을 `append` 에 주면 **`Text` 노드**(`nodeType 3`)가 된다.

**체이닝이 죽는 이유**

- `append` 가 **`undefined`** 를 돌려주므로 그 뒤의 `.classList` 가 `undefined` 의 프로퍼티 접근이 된다. **죽는 줄과 원인이 붙어 있지 않아** 헷갈린다.

```text
   옛 3형제 (DOM Level 1)          새 메서드 (DOM4)
   appendChild  -> 넣은 노드        append       -> undefined
   insertBefore -> 넣은 노드        prepend      -> undefined
   removeChild  -> 뗀 노드          before/after -> undefined
   replaceChild -> 뗀 노드          replaceWith  -> undefined
                                    remove       -> undefined
   ★ 두 세대가 섞여 있고 규약이 반대다
```

### 3. 조각을 붙이고 나면 — 자루가 빈다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
붙이기 전  frag.childNodes.length = 3   list.children.length = 0
           frag.isConnected = false
붙인 뒤    frag.childNodes.length = 0   list.children.length = 3
           li0.isConnected = true   li0.parentElement.id = list

list.innerHTML = <li>가</li><li>나</li><li>다</li>
문서에 frag 자신이 들어갔나: list.querySelector('ul') = null

같은 frag 를 다시 채워 붙이면 list.children.length = 4
(exit 0)
```

**전후의 `frag.childNodes.length`**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,5p'
붙이기 전  frag.childNodes.length = 3   list.children.length = 0
           frag.isConnected = false
붙인 뒤    frag.childNodes.length = 0   list.children.length = 3
           li0.isConnected = true   li0.parentElement.id = list

(exit 0)
```

- 붙이기 전 **3**, 붙인 뒤 **0**.

**`list.children.length`**

- **3**. 조각의 자식들이 그대로 옮겨 갔다.

**조각 자신을 찾을 수 있나**

- **없다.** `list.querySelector('ul')` 이 **`null`** 이다. 조각은 **트리에 안 들어간다** — 자식만 옮겨 간다.

**네 번째 줄**

- **아무 일도 안 한다.** 조각이 이미 비었기 때문이다. 다시 채워 넣으면 그때부터 또 동작한다 — 출력의 마지막 줄에서 `list.children.length` 가 **4** 가 된 것이 그 확인이다.

```text
   반복문 안에서 조각 하나를 돌려 쓰면

   1회차   frag 에 담기 -> 넣기 -> frag 가 빈다        잘 동작
   2회차   (담는 것을 잊으면) 넣기 -> 아무 일 없음      ★ 조용히 통과
```

### 4. 다섯 메서드가 만드는 자리

**출력**

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

**한 줄씩**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03d.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
처음...................... <b id=b1> <b id=b2>
box.prepend(p1)........... <i id=p1> <b id=b1> <b id=b2>
b1.before(x1)............. <i id=p1> <i id=x1> <b id=b1> <b id=b2>
b1.after(x2).............. <i id=p1> <i id=x1> <b id=b1> <i id=x2> <b id=b2>
b2.replaceWith(r1)........ <i id=p1> <i id=x1> <b id=b1> <i id=x2> <i id=r1>
x1.remove()............... <i id=p1> <b id=b1> <i id=x2> <i id=r1>
box.prepend(문자열)....... "텍스트도 된다" <i id=p1> <b id=b1> <i id=x2> <i id=r1>
(exit 0)
```

- `prepend` 는 **맨 앞**, `before`/`after` 는 **그 형제의 앞뒤**, `replaceWith` 는 **자기 자리에 갈아 끼우기**, `remove` 는 **자기를 뺀다**.

**두 갈래**

```text
   부모에 대고 부른다 (ParentNode)      자기 자신에 대고 부른다 (ChildNode)
   append · prepend · replaceChildren   before · after · replaceWith · remove
   '어디에 넣을지' 를 부모가 정한다       '부모가 누구인지 몰라도' 된다
```

**반환값**

- `removeChild(node)` → **뗀 노드**. `node.remove()` → **`undefined`**.
- 뗀 노드를 다시 쓸 것이면 **미리 변수에 담아 둔다.**

**문자열을 받는 것**

- **`append`·`prepend`·`before`·`after`·`replaceWith`** 넷 + `replaceChildren`. `remove()` 는 인자를 안 받는다.
- 출력의 마지막에서 `box.prepend('텍스트도 된다')` 가 텍스트 노드가 됐다.

### 5. 복제본이 물려받는 것 — 속성은 오고 리스너는 안 온다

**출력**

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

**두 복제의 자식 수**

- `cloneNode(true)` = **1**, `cloneNode(false)` = **0**.

**`deep.id` 와 그 결과**

- **`"orig"`** — `id` 까지 복사된다.
- 그대로 문서에 넣으면 **같은 `id` 가 둘**이 되고, `getElementById` 는 **문서 순서로 첫 것만** 준다([02번 주제](../02-element-queries-and-live-collections/2-summary.md)).

**복제본을 클릭하면**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03e.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,11p'
원본 클릭   addEventListener 호출 수 = 1   onclick 속성 = true
복제본 클릭 addEventListener 호출 수 = 1   onclick 속성 = true
복제본의 onclick 속성 문자열 = "window.속성이_불렸다 = true"
(exit 0)
```

- **`addEventListener` 로 단 리스너는 안 불렸다**(카운터가 1 에서 안 움직였다).
- **`onclick` 속성은 불렸다**(플래그가 `true` 가 됐다). 복제본의 `onclick` 속성 문자열도 그대로 복사돼 있다.

**한 문장으로**

- **속성은 노드의 일부이고 리스너는 아니다.** `cloneNode` 는 **노드를 복사**하므로 속성은 따라오고, 노드 바깥에서 관리되는 리스너 목록은 안 따라온다.

```text
   노드 객체                         노드 바깥
   +---------------------------+    +---------------------------+
   | 태그 이름                  |    | addEventListener 목록     |
   | 속성 전부 (id · onclick)   |    | JS 가 심은 프로퍼티        |
   | 자식 (deep 일 때)          |    | 폼 요소의 사용자 입력 상태  |
   +---------------------------+    +---------------------------+
      cloneNode 가 복사한다             cloneNode 가 안 본다
```

### 6. 만들기와 넣기는 다른 단계다

**출력** — 위 `ex03a` 블록의 앞 세 줄이 근거다.

- `createElement` 직후 — `parentNode` = **`null`**, `isConnected` = **`false`**, `ownerDocument` = **`document`**(이미 매여 있다, [01번 주제](../01-document-and-node-tree/2-summary.md)).

**넣기 전까지 안 일어나는 것**

- **렌더·스타일 계산·레이아웃**이 없다. `getComputedStyle` 이나 기하 읽기가 의미를 갖지 않는다(목록의 **08번 주제**와 목록의 **09번 주제**).

**`createTextNode('<b>x</b>')`**

- 화면에 **`<b>x</b>` 라는 글자 그대로** 보인다. 텍스트 노드는 **마크업으로 해석되지 않는다** — 그것이 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에서 `textContent` 가 안전한 이유와 같은 성질이다.

**트리 밖 조립이 권장되는 이유**

- 트리 밖에서는 **스타일·레이아웃을 건드리지 않으므로** 조립 중간 상태가 화면 계산에 끼어들지 않는다. 다만 **그것이 실제로 얼마나 싼지는 이 문서가 재지 않았다** — 측정은 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)와 목록의 **05번 주제**·**10번 주제**의 몫이다.

### 7. 왜 복사가 아니라 이동인가

**어떤 성질이 강제하나**

- **DOM 은 그래프가 아니라 나무**이고, 노드의 **부모는 하나**다. 한 노드가 두 자리에 동시에 있을 수 없으므로 **넣으면 원래 자리에서 빠지는 것 말고 다른 답이 없다.**

**따라가는 것과 안 따라가는 것**

```text
   이동 (같은 노드가 자리만 바뀐다)      복제 (새 노드가 생긴다)
   리스너        따라간다               안 따라간다
   폼 입력값     따라간다               안 따라간다
   JS 프로퍼티   따라간다               안 따라간다
   속성          따라간다               따라간다
   id            따라간다               따라간다 -> 중복이 된다
```

**예외**

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03f.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '4,7p'
iframe 을 옮기기 전  contentWindow.표식 = A
프레임 안 글자 = "프레임 안"
다른 부모로 옮긴 직후 표식 = undefined
옮긴 직후 프레임 안 글자 = ""
(exit 0)
```

- **`<iframe>`** 이다. 다른 부모로 옮기자 `contentWindow` 에 심어 둔 표식이 **`undefined`** 가 되고, `contentDocument.body.textContent` 가 **빈 문자열**이 됐다 — **프레임 안의 문서가 통째로 버려졌다.**

**확인하지 못한 것**

- **그 뒤에 다시 로드되는지**까지는 못 봤다. `--dump-dom` 이 로드 완료 한 턴 뒤에 끊기고, 재로드는 그보다 뒤에 일어나기 때문이다. 확인한 것은 「**옮긴 직후 안이 비었다**」까지이고, 그 이상을 적지 않는다.

### 8. 뗀 노드는 어디로 가나

**`getElementById` 로 찾으면**

- **`null`** 이다 — 위 `ex03d` 출력의 `remove 한 x1 을 document 에서 다시 찾으면 = null` 이 근거다.

**노드 자체는**

- **살아 있다.** 확인하는 방법은 둘이다 — 변수로 프로퍼티를 읽어 보는 것, 그리고 `isConnected` 가 `false` 인지 보는 것([01번 주제](../01-document-and-node-tree/2-summary.md)).
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 실측이 같은 것을 보였다 — 지워진 노드를 정적 스냅샷이 여전히 들고 있었고 `isConnected` 가 `false` 였다.

**다시 넣을 수 있나**

- **있다.** 떼기는 파괴가 아니다. 그래서 「잠깐 빼 뒀다가 다시 넣기」가 성립한다.

```text
   remove()                       다시 appendChild()
   트리 --------> 노드 (변수가 붙듦) --------> 트리
                   ^
                   여기서 참조가 끊기면 그때 GC 대상이 된다
```

**메모리 경로**

- 오래 사는 배열·클로저·전역이 뗀 노드를 붙들면 **그 하위 트리 전체**가 안 치워진다. 리스너까지 붙어 있으면 더 크게 붙든다(목록의 **20번 주제**).

### 9. 삽입이 검사하지 않는 것

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03f.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,2p'
appendChild 로 <p> 안에 <div> 를 넣으면 = <p><div></div></p>
같은 모양을 innerHTML 로 넣으면          = <p>가</p><div>나</div><p></p>
(exit 0)
```

**API 로 넣으면**

- **`<p><div></div></p>`** — 그대로 들어간다.

**`innerHTML` 로 넣으면**

- **`<p>가</p><div>나</div><p></p>`** — 파서가 `<p>` 를 닫고 `<div>` 를 형제로 만든 뒤 빈 `<p>` 를 남겼다.

**왜 다르고 어디가 정본인가**

- **파싱 때만 콘텐츠 모델이 적용**된다. 파서 쪽 규칙의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **03번**(파서·오류 복구)이고, `innerHTML` 이 그 파서를 부르는 이야기는 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)다.
- **삽입 API 는 그 규칙을 안 본다.** 그래서 **「트리가 될 수 있는 모양」이 「파서가 만들 수 있는 모양」보다 넓다.**

**실제로 검사하는 것**

- 부모가 될 수 있는 종류인가(`Text` 에는 자식을 못 넣는다) · **조상을 자기 자손에 넣는가**(`HierarchyRequestError`) · `Document` 의 자식 제약(요소는 하나만) 정도다. **태그 궁합은 안 본다.**

### 10. 다른 주제와 잇기

**이동이 컬렉션에 비치는 모습**

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '26,27p'
옮기기 전  live=[left,left]  snap=[left,left]
옮긴 뒤    live=[left,right]  snap=[right,left]
(exit 0)
```

- **개수는 둘 다 2 그대로**다 — 이동은 멤버십을 안 바꾼다.
- **라이브는 문서 순서로 다시 줄을 선다**(`[left, right]` — 첫 칸이 이제 `s2`), **정적은 잡을 때의 순서를 지킨다**(`[right, left]` — 첫 칸이 여전히 `s1`).
- 그래서 **인덱스로 꺼내 쓰는 코드가 이동 뒤에 다른 것을 집는다.** 길이가 그대로라 **길이 검사로는 안 걸린다.**

**반환값 규약이 갈린 이유**

- **세대가 다르다.** `appendChild` 계열은 DOM Level 1(1998), `append` 계열은 DOM4(2015 무렵)에 들어왔다. 뒤엣것은 **jQuery 가 증명한 편의**를 표준이 받아들인 것이고, 그때는 체이닝보다 **여러 인자와 문자열 받기**를 골랐다.

**`replaceChildren()` 이 권장되는 이유**

- **파싱을 안 한다.** `innerHTML = ''` 는 문자열을 넣는 경로라 파서를 부르고, 신뢰할 수 없는 문자열이 섞일 여지가 생긴다([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)). **비용 비교는 그쪽에서 수치로 잰다.**

**「한 번에 넣는 것이 싸다」를 주장하지 않은 이유**

- **이 주제에서 재지 않았기 때문**이다. 그리고 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에서 실제로 재 보니 **`DocumentFragment` 가 항목마다 `appendChild` 하는 것보다 빠르지 않았다** — 널리 알려진 이야기와 다른 결과라, 수치 없이 옮겨 적지 않는다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

**하네스** — 01\~04 네 주제가 공유한다. 이 주제만 **트리 출력기**를 하나 더 쓴다.

```bash
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex03b.html \
  | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 이 주제의 창 4 — 같은 출력기로 조작 전후를 두 번 그린다.
// 한쪽만 그리면 '붙었다' 만 보이고 '빠졌다' 를 못 본다.
const tree = (n, d) => {
  let s = '';
  for (const c of n.childNodes) {
    if (c.nodeType === 1) s += '  '.repeat(d) + '<' + c.nodeName.toLowerCase() +
      (c.id ? ' id=' + c.id : '') + '>\n' + tree(c, d + 1);
    else if (c.nodeType === 3 && c.nodeValue.trim()) s += '  '.repeat(d) + '"' + c.nodeValue.trim() + '"\n';
  }
  return s;
};
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙). `ex03f` 의 `iframe` 실험이 **시간이 걸린 유일한 실험**이라 특히 그렇다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 만들기 셋의 `isConnected`·`parentNode`·`nodeType` | 2 | 동작 방식 (0) · A6 |
| `append` 대 `appendChild` 의 반환값·다중 인자·문자열·`TypeError` | 2 | 동작 방식 (1) · A2 |
| 이동 전후 트리 두 벌 + 문서 안 `span` 수 | 3 | 동작 방식 (2) · A1 |
| 같은 이동을 라이브·정적 컬렉션으로 본 순서 변화 | 2 | 동작 방식 (2) · A10 |
| 조각 삽입 전후 `childNodes.length` + 두 번째 삽입 | 2 | 동작 방식 (4) · A3 |
| 다섯 메서드를 한 줄씩 적용한 7단계 트리 | 2 | 동작 방식 (3) · A4 |
| `cloneNode` 깊이·`id`·리스너 대 `onclick` 속성 | 2 | 동작 방식 (5) · A5 |
| `p.appendChild(div)` 대 같은 모양의 `innerHTML` | 2 | 동작 방식 (6) · A9 |
| `iframe` 을 옮긴 직후 `contentWindow` 표식과 본문 | 3 | 동작 방식 (6) · A7 |
| `demo03` 을 래퍼에 띄워 버튼을 눌러 칩이 옮겨지는지 | 1 | 동작 방식 (2)의 demo |
| `demo03` 의 「바꿔 볼 것」(`cloneNode` 판 — 칩이 둘이 되는지) | 1 | 같은 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 예외 메시지 문구 | `parameter 1 is not of type 'Node'.` | 명세는 문구를 정하지 않는다 |
| `iframe` 을 옮겼을 때 **안이 즉시 비는 시점** | 옮긴 직후 동기적으로 | 명세는 문맥 폐기를 정하지만 시점의 세부는 이 판의 관찰 |
| 트리 출력기의 들여쓰기 형태 | 이 문서의 코드가 정한다 | 브라우저와 무관하다 |
| 삽입·복제의 **비용** | 재지 않음 | 이 주제는 성능을 주장하지 않는다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **옮긴 `iframe` 이 다시 로드되는지** — `--dump-dom` 이 그 전에 끊긴다. 「안이 비었다」까지만 적었다. ③ `<template>` 의 `content` 복제(목록의 **05번 주제**의 몫). ④ 삽입 비용 측정 — [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에서 잰다.

## 용어 풀이

- **삽입(insert)** — 노드를 부모의 자식 목록에 넣는 명세상의 절차. **부모가 있으면 먼저 제거**한다.
- **pre-insert** — 삽입 전에 도는 검사 단계. 계층 오류(`HierarchyRequestError`)가 여기서 난다.
- **`DocumentFragment`** — 부모 없는 임시 자루. 넣으면 자식만 옮겨 가고 자신은 빈다.
- **`ParentNode`** — `append`·`prepend`·`replaceChildren` 을 주는 믹스인.
- **`ChildNode`** — `before`·`after`·`replaceWith`·`remove` 를 주는 믹스인.
- **얕은/깊은 복제** — `cloneNode(false)` 는 자기만, `cloneNode(true)` 는 하위 트리 전부.
- **속성 핸들러** — 마크업에 쓴 `onclick` 같은 것. **속성이라 복제에 따라온다.**
- **떼기(detach)** — `remove()` 가 하는 일. 트리에서 빠질 뿐 객체는 살아 있다.
- **브라우징 문맥(browsing context)** — `<iframe>` 안의 문서를 담는 그릇. **프레임을 옮기면 버려진다.**
- **콘텐츠 모델(content model)** — 「어떤 요소 안에 어떤 요소를 쓸 수 있나」라는 HTML 규칙. **파싱 때만 적용되고 삽입 API 는 안 본다.**
