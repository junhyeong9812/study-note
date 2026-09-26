# web-api/02 — 요소 조회: `querySelector` 계열과 `getElementsBy*`·라이브 대 정적 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **이 주제의 블록에는 흔들리는 칸이 없다** — 컬렉션의 `length`·예외 이름·트리 문자열은 다시 돌려도 한 글자도 같아야 한다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 넷을 잡아 두고 DOM 을 바꾸면 — 셋만 따라간다

**출력**

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

**전후의 네 수**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '5,7p'
처음            byTag=2  byClass=2  children=2  querySelectorAll=2
li 하나 추가    byTag=3  byClass=3  children=3  querySelectorAll=2
li 하나 제거    byTag=2  byClass=2  children=2  querySelectorAll=2
(exit 0)
```

- 붙이기 전 **2·2·2·2** → 붙인 뒤 **3·3·3·2** → 하나 지운 뒤 **2·2·2·2**.
- **`querySelectorAll` 만 혼자 2 에서 안 움직인다.**

**마지막 시점의 `snap[0]`**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,10p'
snap[0] 은 지운 A 를 아직 들고 있다: snap[0].textContent = "A"
snap[0].isConnected = false
(exit 0)
```

- **지워진 `A` 를 아직 들고 있다.** `isConnected` 가 **`false`** 다 — 「문서에 없는 노드」를 가리키는 참조가 살아 있는 것이다.

**시점이 셋 필요한 이유**

```text
   t0 잡기만 하면      네 수가 전부 같다        -> 차이가 안 보인다
   t1 바꾸기           여기서 라이브가 움직인다
   t2 다시 읽기        ★ 비로소 갈린다

   시점 둘(잡기·읽기)로는 '아무 일도 안 일어난 것' 과 구분되지 않는다
```

### 2. 같은 타입에서 갈리는 것 — 만든 API 가 정한다

**출력**

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

**두·세 번째 줄**

- `Object.prototype.toString.call(cn)` = **`[object NodeList]`**, `qs` 도 **같다**.
- `cn.constructor === qs.constructor` = **`true`**. 같은 생성자의 같은 타입이다.

**붙인 뒤**

- `cn.length` = **3**, `qs.length` = **2**.

**요약이 틀린 곳**

- 「`NodeList` 는 정적」이 틀렸다. **`childNodes` 는 라이브 `NodeList`** 다.
- 맞는 절반은 「`HTMLCollection` 은 언제나 라이브」쪽이다 — 여기엔 예외가 없다.

**판정 기준**

```text
   타입으로 판정  ->  HTMLCollection 이면 라이브 (이것만 참)
                      NodeList 면 ???       (모른다)

   API 로 판정    ->  querySelectorAll  = 정적
                      childNodes        = 라이브
                      getElementsBy*    = 라이브
                      children          = 라이브
   ★ 명세가 '반환하는 자리' 에서 정적인지 라이브인지 못 박는다
```

### 3. 지우는 반복문 — 절반만 지워진다

**출력**

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

**남는 것**

- **2개**가 남고, 남은 것은 **`2` 와 `4`** 다.

**한 판씩**

```text
   i=0   live = [1,2,3,4]  length 4   live[0] = 1 을 지움
   i=1   live = [2,3,4]    length 3   live[1] = 3 을 지움
   i=2   live = [2,4]      length 2   2 < 2 가 거짓 -> 끝
```

- **지울 때마다 뒤가 당겨 오고 끝나는 조건도 같이 줄어든다.** 그래서 반복이 절반에서 멎는다.

**정적으로 바꾸면**

- `snap.length` 는 끝까지 **4** 이고 **넷 다 지워진다** — 출력의 아래쪽 `B 나중 = []` 이 그것이다.

**라이브를 그대로 쓰면서 고치는 법**

```js
for (let i = live.length - 1; i >= 0; i--) live[i].remove();   // 뒤에서부터
while (live.length) live[0].remove();                          // 늘 첫 것을
```

### 4. 기준 요소에 대고 물으면 — 자기 자신이 조상으로 쓰인다

**출력**

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

**세 줄**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '4,7p'
outer.querySelectorAll('div p')       = [a, b]
outer.querySelectorAll(':scope > p')  = [a]
outer.querySelectorAll('p')           = [a, b]
document.querySelector('p').id        = a
(exit 0)
```

- `outer.querySelectorAll('div p')` = **`[a, b]`** — **바깥 문단까지 잡힌다.**
- `outer.querySelectorAll(':scope > p')` = **`[a]`**.
- `outer.getElementById('a')` = **`TypeError`** — 그 메서드가 요소에 없다(`typeof` 가 `undefined`).

**매치와 걸러내기**

```text
   1) 매치      선택자를 '문서 전체' 를 기준으로 푼다
                'div p' 를 만족하는 요소를 다 찾는다  ->  a, b
                (a 의 조상에 <div id=outer> 가 있다)

   2) 걸러내기  그중 기준 요소의 '자손' 만 남긴다
                a 도 b 도 outer 의 자손이다           ->  a, b

   ★ 1) 이 문서 전체를 보기 때문에 기준 요소 자신이 조상 자격으로 쓰인다
```

**`getElementById` 가 요소에 없는 이유**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,2p;9,10p'
typeof document.getElementById = function
typeof outer.getElementById    = undefined
떼어낸 트리 안의 id=c 를 document.getElementById 로 = null
같은 것을 detached.querySelector('#c') 로 = 문서 밖
(exit 0)
```

- `NonElementParentNode` 라는 믹스인이 주는 메서드이고, 그것을 갖는 것은 **`Document` 와 `DocumentFragment`** 뿐이다. `Element` 는 안 갖는다.

**떼어낸 트리의 `id`**

- `document.getElementById('c')` = **`null`**. 문서에 이어져 있지 않으면 문서의 id 색인에 없다.
- 같은 것을 그 트리의 루트에 대고 `querySelector('#c')` 로 물으면 **찾는다.**

### 5. 잘못된 선택자를 주면 — 던진다

**출력**

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

**네 줄**

- `querySelectorAll('div:has(')` → **던진다.**
- `getElementsByTagName('div:has(')` → **0개.** 안 던진다.
- `getElementsByClassName('.ok')` → **0개.** `.ok` 라는 **이름의 클래스**를 찾은 것이다.
- `querySelectorAll(':is(.ok, ::bogus)')` → **1개.** 너그러운 목록이라 그 인자만 버린다.

**예외의 정체**

- `e.name` = **`'SyntaxError'`** · 타입은 **`DOMException`** · `e.code` = **`12`**.

**`instanceof SyntaxError` 로 잡히나**

- **안 잡힌다.** 실측에서 `false` 였다. `e.name === 'SyntaxError'` 나 `e instanceof DOMException` 을 봐야 한다.

```text
   이름만 같고 족보가 다르다

   JS 의 SyntaxError      Error -> SyntaxError          (언어가 던진다)
   여기서 잡힌 것          Error -> DOMException         (플랫폼이 던진다)
                                    name = 'SyntaxError'
```

**스타일시트에 쓰면**

- **조용히 버려진다.** 규칙 전체가 `cssRules` 에 안 담기고 에러도 경고도 없다 — 정본은 [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)다.
- **같은 문자열에 대해 한쪽은 침묵하고 한쪽은 던진다.** 무효한 선택자를 쓴 코드가 스타일에서는 안 들키고 스크립트에서만 들키는 이유다.

### 6. 다섯 API 의 반환 타입

**출력** — 타입 이름은 위 `ex02a` 블록의 앞 세 줄이 근거다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,3p'
byTag  = HTMLCollection
kids   = HTMLCollection
snap   = NodeList
(exit 0)
```

**반환 타입**

```text
   getElementById            Element | null
   getElementsByTagName      HTMLCollection   라이브
   getElementsByClassName    HTMLCollection   라이브
   querySelector             Element | null
   querySelectorAll          NodeList         ★ 정적
   children                  HTMLCollection   라이브
   childNodes                NodeList         ★ 라이브
```

**언제나 라이브인 타입**

- **`HTMLCollection`.** 명세가 「collection」을 라이브로 정의한다.

**두 타입의 표면 차이**

- `NodeList` 에 있고 `HTMLCollection` 에 없는 것 — **`forEach`**·`entries`·`keys`·`values`.
- `HTMLCollection` 에 있고 `NodeList` 에 없는 것 — **`namedItem`**(이름·`id` 로 꺼내기).

**`map`·`filter` 를 걸려면**

- **배열로 펼친다** — `[...live]` 또는 `Array.from(live)`. 그 순간 **정적 배열**이 된다.

### 7. `getElementById` 에 탐색 범위가 없는 이유

**믹스인**

- **`NonElementParentNode`** 가 준다. `Document` 와 `DocumentFragment` 만 이것을 포함한다.

**유일성과의 연결**

- `id` 는 **문서 전체에서 유일**해야 하는 식별자다. 유일하다면 「어디서부터 찾느냐」가 **답을 바꾸지 않는다** — 그래서 범위라는 개념 자체가 필요 없다.

**같은 `id` 가 둘이면**

**출력**

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

- `getElementById` 는 **문서 순서로 첫 것**(`"첫째"`)을 준다. 던지지도 경고하지도 않는다.
- `querySelectorAll('#dup')` 은 **둘 다**(`2`) 준다. 「`id` 는 유일」은 **HTML 의 규칙**이지 선택자 엔진의 전제가 아니다. `id` 유일성의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **07번**이다.

**둘의 차이**

- `getElementById` 는 **문서가 들고 있는 id 색인**을 본다. `querySelector('#x')` 는 **선택자 엔진**을 돈다. 결과는 같지만 경로가 다르고, `querySelector` 쪽은 **무효한 선택자면 던진다.**

### 8. 정적 스냅샷이 들고 있는 것

**「낡았다」인가 「고정됐다」인가**

- **고정됐다.** 실측에서 같은 자리를 다시 잡으니 **최신 값**이 나왔다(`ex02b` 의 마지막 줄 `3`). 정적 목록은 **그 시점의 답을 계약으로 보관**한 것이지 망가진 것이 아니다.

**노드를 지우면**

- 스냅샷은 **그 노드를 계속 가리킨다.** 실측에서 `snap[0].textContent` 가 `"A"` 이고 `isConnected` 가 `false` 였다.

```text
   문서 트리                  스냅샷(NodeList)
   +-----------+              +-----------+
   |  <ul>     |              | [0] -> A  |   A 는 트리에서 떨어졌는데
   |   <li>B   |              | [1] -> B  |   스냅샷이 아직 붙들고 있다
   +-----------+              +-----------+
                                 ^ 이 참조가 살아 있는 한 GC 대상이 아니다
```

**메모리 문제가 되는 경로**

- 떨어진 노드를 가리키는 참조를 **오래 사는 배열·클로저**가 붙들면, 그 노드와 **그 하위 트리 전체**가 안 치워진다. 리스너까지 붙어 있으면 더 크게 붙든다([목록의 **20번 주제**](../20-listener-lifetime/)).

**최신이 필요하면**

- **다시 잡는다.** 그것이 정적 목록의 사용법이다.

### 9. 어느 쪽이 이득인가

**계속 묻는 화면**

- **라이브**가 낫다. 「지금 몇 개」를 물을 때마다 다시 조회하는 코드를 안 써도 된다.

**순회하며 바꾸는 코드**

- **정적**이 낫다. 순회 중에 목록이 움직이지 않는 것이 유일한 안전장치다.

**`live.length` 를 반복 조건에 두면**

- 명세상 보장되는 것은 「**읽을 때마다 현재 상태를 답한다**」는 것뿐이다. 그래서 **조건이 매 판 바뀔 수 있다**는 사실 자체가 중요하고, 위 A3 의 사고가 정확히 그것이다.
- **그 비용은 이 문서가 재지 않았다.** 구현이 캐시를 두는지, 무효화가 얼마나 자주 일어나는지는 Blink 의 사정이고 이 문서의 실행 검증 범위 밖이다. 「라이브가 느리다」를 **수치 없이 주장하지 않는다.**

**`[...live]` 한 줄**

- **라이브 목록을 그 자리에서 정적 배열로 얼린다.** 그 뒤의 DOM 변경과 무관해지고 배열 메서드도 같이 얻는다.

### 10. 다른 주제와 잇기

**명세의 계약이라는 말**

- 라이브·정적은 **각 인터페이스와 각 메서드의 반환 자리에 명세가 적어 둔 것**이다. `HTMLCollection` 은 정의가 라이브이고, `querySelectorAll` 은 반환 문장에 「static」이 박혀 있다. 그래서 「Chrome 이 그렇더라」가 아니라 「**그래야 한다**」로 읽고, 다른 엔진에서도 같아야 한다고 **명세를 근거로** 말할 수 있다 — 이 문서가 단일 엔진인데도 이 항목만은 이식성을 말할 수 있는 이유다.

**던지는 쪽과 버리는 쪽**

- **누가 읽느냐**가 갈랐다. 스타일시트는 **브라우저가 알아서 읽는 선언**이라 모르는 것을 만나면 페이지를 안 깨뜨리는 쪽이 옳고(점진적 향상), API 호출은 **프로그래머가 방금 쓴 문장**이라 틀렸다고 알려 주는 쪽이 옳다.

**경계**

- **선택자가 무엇을 고르나**는 CSS 갈래([CSS 08번 주제](../../languages/css/syntax/08-basic-selectors-and-combinators/2-summary.md)), **그 선택자를 API 로 던진 계약**(정적·예외·`:scope`)은 이 갈래다.

**`innerHTML` 로 통째로 갈면**

- 실측이 위 A7 의 출력이다 — **라이브는 새 노드 셋을 가리키고**(`A,B,C`), **정적은 사라진 둘을 그대로 들고 있다**(`하나,둘`, `isConnected = false`).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다.** 따라서 **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이고, 이식성을 말한 자리는 **명세 문장을 근거로 든 A10 하나**다.

**하네스** — 01\~04 네 주제가 공유한다. 결과를 문자열로 모아 `<script type="text/plain">` 에 넣고 `--dump-dom` 으로 받은 뒤 마커 사이만 잘라낸다.

```bash
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex02a.html \
  | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 창 3 의 관용구 — 잡기 · 바꾸기 · 다시 읽기를 한 파일 안에서
const live = document.getElementsByTagName('li');     // t0 잡는다
const snap = document.querySelectorAll('li');
row('처음');                                          //    둘 다 같은 답
list.appendChild(document.createElement('li'));       // t1 바꾼다
row('li 하나 추가');                                   // t2 다시 읽는다 -> 갈린다
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 네 컬렉션을 잡아 두고 추가·삭제 전후 `length` 3회 읽기 | 3 | 동작 방식 (0) · A1 |
| 네 컬렉션의 `constructor.name` | 3 | 동작 방식 (1) · A6 |
| 스냅샷이 떨어진 노드를 들고 있는 것(`isConnected`) | 3 | 동작 방식 (0) · A8 |
| 같은 `NodeList` 두 개의 `toString`·`constructor` 비교 + 변경 전후 | 2 | 동작 방식 (2) · A2 |
| 라이브 순회 삭제 대 정적 순회 삭제(4항목) | 2 | 동작 방식 (3) · A3 |
| `outer.querySelectorAll('div p')` 대 `:scope > p` | 2 | 동작 방식 (4) · A4 |
| `typeof outer.getElementById` · 떼어낸 트리의 `id` | 2 | 동작 방식 (4) · A4 |
| 무효 선택자 10질의(던지는 것·안 던지는 것·`:is()`·예외 정체) | 2 | 동작 방식 (5) · A5 |
| 같은 `id` 둘 + `innerHTML` 통째 교체 뒤 라이브·정적 | 2 | 동작 방식 (6) · A7 · A10 |
| `demo02` 를 래퍼에 띄워 버튼을 눌러 「3 대 2」 확인 | 1 | 동작 방식 (5)의 demo |
| `demo02` 의 「바꿔 볼 것」 두 갈래 | 1 | 같은 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 예외 메시지 문구 | `'div:has(' is not a valid selector.` | 명세는 문구를 정하지 않는다 |
| `getElementsByTagName` 이 요소 순서를 주는 방식 | 문서 순서 | 명세가 정하지만 세부 직렬화는 이 판의 관찰 |
| 라이브 컬렉션의 **캐시 여부** | 재지 않음 | 명세는 「살아 있다」만 정한다. **비용은 측정하지 않았다** |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **라이브 대 정적의 성능 차이** — 이 주제에서 수치를 재지 않기로 정했고, 그래서 본문에도 성능 주장을 넣지 않았다. 비용을 재는 것은 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)의 몫이다. ③ Shadow DOM 경계를 넘는 조회([목록의 **12번 주제**](../12-shadow-dom/)).

## 용어 풀이

- **라이브 컬렉션(live collection)** — DOM 이 바뀌면 따라 바뀌는 목록. `HTMLCollection` 전부와 `childNodes`.
- **정적 컬렉션(static collection)** — 돌려받는 순간의 스냅샷. `querySelectorAll` 의 결과.
- **`HTMLCollection`** — 요소만 담는 라이브 목록. `forEach` 가 없고 `namedItem` 이 있다.
- **`NodeList`** — 노드를 담는 목록. **만든 API 가 라이브인지 정적인지 정한다.**
- **`NonElementParentNode`** — `getElementById` 를 주는 믹스인. `Document`·`DocumentFragment` 만 포함한다.
- **`:scope`** — 조회의 기준 요소를 가리키는 의사 클래스.
- **scope-matching** — 요소에 대고 부른 선택자를 **문서 기준으로 매치하고 자손만 거르는** 명세상의 절차.
- **`DOMException`** — 플랫폼이 던지는 예외 타입. `name` 이 `'SyntaxError'` 여도 JS 의 `SyntaxError` 가 아니다.
- **너그러운 선택자 목록(forgiving selector list)** — `:is()`·`:where()` 의 인자 목록. 무효한 인자만 빼고 쓴다.
- **id 색인** — 문서가 `id` 별로 들고 있는 조회표. `getElementById` 가 이것을 본다.
