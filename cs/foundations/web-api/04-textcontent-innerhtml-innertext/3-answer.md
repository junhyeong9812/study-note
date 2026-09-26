# web-api/04 — `textContent` 대 `innerHTML` 대 `innerText`: 파싱·비용·XSS — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 와 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** `innerText` 는 특히 엔진 차이가 남아 있을 수 있는 자리다.

**★ 이 주제에는 흔들리는 칸이 있다.** 네 주제 중 여기만 그렇다.

| 안 흔들리는 칸 | 흔들리는 칸 |
|---|---|
| 읽은 문자열 · 파싱 결과 트리 · 자식 수 · **실행 횟수** · 문자열 길이 | `performance.now()` 의 **모든 수치** |
| **자릿수와 순위** — 세 판 모두 같았다 | 같은 자릿수 안의 대소 |

측정 조건 — **한 파일 안에서 9판**을 돌려 **중앙값**을 쓰고 최소·최대를 함께 실었다. 항목 수는 **2000**, 판마다 대상 컨테이너를 비우고 다시 만든다. 읽기 실험은 **읽기 전마다 `paddingLeft` 를 바꿔** 레이아웃을 더럽힌다. **결론으로 쓰는 것은 자릿수뿐**이다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 셋을 나란히 읽으면 — 셋이 다 다르다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,5p'
textContent = "\n  보이는 문단\n  숨은 문단\n  hidden 속성\n  .z { color: red }\n  {\"설정\": 1}\n  줄바꿈abc\n"

innerText   = "보이는 문단\n\n줄\n바꿈ABC"

innerHTML   = "\n  <p>보이는 문단</p>\n  <p style=\"display: none\">숨은 문단</p>\n  <span hidden=\"\">hidden 속성</span>\n  <style>.z { color: red }</style>\n  <script type=\"application/json\">{\"설정\": 1}</script>\n  <p>줄<br>바꿈<span style=\"text-transform: uppercase\">abc</span></p>\n"
(exit 0)
```

**셋이 주는 것**

- **`textContent`** — 트리의 **모든 글자**. 보이는 문단 · 숨은 문단 · `hidden` 속성이 걸린 글자 · `<style>` 내용 · `<script>` 내용 · **소스의 들여쓰기 공백까지**.
- **`innerText`** — **보이는 글자만**. `"보이는 문단\n\n줄\n바꿈ABC"`.
- **`innerHTML`** — **트리에서 되뽑은 마크업**. `hidden` 이 `hidden=""` 로 정규화돼 있다.

**`<style>` 안의 글자**

- **`textContent` 와 `innerHTML` 에만** 나온다. `innerText` 에는 없다 — `<style>` 은 렌더되지 않는다.

**`<br>` 과 `text-transform`**

- `<br>` — `innerText` 에서 **`"\n"`**, `textContent` 에서는 **아무것도 아니다**(요소이므로 글자가 없다), `innerHTML` 에서는 **`<br>`** 그대로.
- `text-transform: uppercase` — `innerText` 에서 **`ABC`**(적용된 결과), 나머지 둘은 **`abc`**(소스 그대로).

**들여쓰기 공백**

- **`textContent` 와 `innerHTML`** 에 보인다. `innerText` 는 렌더 결과라 축약돼 사라진다.

```text
   한 트리를 세 각도에서 본다

   트리 ──> textContent   "여기 있는 글자 전부"       화면을 안 본다
        ──> innerHTML     "이 트리를 마크업으로"       화면을 안 본다
        ──> innerText     "화면에 이렇게 적혀 있다"    ★ 화면을 본다
```

### 2. 안 보이는 요소에서 읽으면 — 자기 자신으로 읽으면 나온다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '7,11p'
display:none 인 p 의 textContent = "숨은 문단"
display:none 인 p 의 innerText   = "숨은 문단"
display:none 인 p 의 innerHTML   = "숨은 문단"

innerText 를 문서에서 떼어낸 복제본에서 읽으면 = "\n  보이는 문단\n  숨은 문단\n  hidden 속성\n  .z { color: red }\n  {\"설정\": 1}\n  줄바꿈abc\n"
(exit 0)
```

**세 줄**

- `p2.textContent` = **`"숨은 문단"`**.
- `p2.innerText` = **`"숨은 문단"`** — ★ 빠지지 않는다.
- `box.cloneNode(true).innerText` = **`textContent` 와 같은 문자열**(들여쓰기 공백까지 전부).

**갈리는 이유**

- 명세가 「**요소가 렌더되고 있지 않으면 `innerText` 는 `textContent` 와 같은 값**」으로 정해 뒀기 때문이다.
- 부모를 통해 읽으면 **부모는 렌더되고 있으므로** 렌더 경로를 타고, 그 안에서 `display: none` 인 부분이 빠진다.
- 그 요소 자신으로 읽으면 **읽을 렌더 결과가 없으므로** `textContent` 로 물러선다.

```text
   box.innerText            box 는 렌더된다 -> 렌더 경로 -> 숨은 문단이 '빠진다'
     +- <p>보이는 문단
     +- <p style=display:none>숨은 문단

   p2.innerText             p2 는 렌더 안 된다 -> textContent 로 물러섬 -> '나온다'

   ★ 같은 노드인데 '누구에게 물었느냐' 로 답이 갈린다
```

**떼어낸 복제본**

- 문서 밖이라 **아무것도 렌더되지 않는다.** 그래서 **언제나 `textContent` 와 같다.**

**테스트의 함정**

- 트리 밖에서 만든 DOM 으로 단위 테스트를 짜면 `innerText` 와 `textContent` 가 **늘 같은 값**이라 둘을 바꿔 써도 통과한다. **화면에 붙는 순간 갈린다.**

### 3. 잘못된 마크업을 넣으면 — 파서가 고친다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
넣은 것   <p>가<div>나</div>
읽은 것   <p>가</p><div>나</div>
자식 수   2   p 는 div 를 품지 못한다

넣은 것   <b><i>가</b>나</i>
읽은 것   <b><i>가</i></b><i>나</i>
자식 수   2   겹친 태그를 파서가 다시 연다

넣은 것   <td>셀</td>
읽은 것   셀
자식 수   0   div 안에서는 td 가 버려진다

넣은 것   <tr><td>셀
읽은 것   <tbody><tr><td>셀</td></tr></tbody>
자식 수   1   table 안에서는 tbody 가 끼워진다

넣은 것   <ul><li>하나<li>둘
읽은 것   <ul><li>하나</li><li>둘</li></ul>
자식 수   1   닫지 않아도 닫아 준다

넣은 것   &amp;lt; &lt; &#65;
읽은 것   &amp;lt; &lt; A
자식 수   0   문자 참조는 풀린다

한 번 더 넣었다 뺀 것이 같은가 = true
(exit 0)
```

**네 줄의 결과**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,3p'
넣은 것   <p>가<div>나</div>
읽은 것   <p>가</p><div>나</div>
자식 수   2   p 는 div 를 품지 못한다
(exit 0)
```

- `<p>가<div>나</div>` → **`<p>가</p><div>나</div>`** (자식 2개)
- `<b><i>가</b>나</i>` → **`<b><i>가</i></b><i>나</i>`** (자식 2개)
- `<td>셀</td>` (div 안) → **`셀`** (자식 0개 — `<td>` 가 버려졌다)
- `<tr><td>셀` (table 안) → **`<tbody><tr><td>셀</td></tr></tbody>`** (자식 1개)

**세 번째와 네 번째가 갈리는 이유**

- **문맥 요소가 다르다.** fragment parsing 은 「이 문자열을 **어떤 요소의 자식으로** 파싱하나」를 먼저 정하고 시작한다. `<div>` 안에서는 `<td>` 가 갈 자리가 없어 버려지고, `<table>` 안에서는 `<tbody>` 를 만들어 넣는다.

**정본과 경계**

- 「어떤 마크업이 어떤 트리가 되나」의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **03번**(파서와 오류 복구)이다.
- **이 주제가 다루는 것은 「`innerHTML` 이 그 파서를 부른다」는 사실**과, 그 결과가 **API 삽입과 다르다**는 것까지다.

**`appendChild` 로 만들면**

- [03번 주제](../03-node-creation-insertion-removal/2-summary.md)의 실측대로 **`<p><div></div></p>`** 가 그대로 만들어진다. 삽입 API 는 **콘텐츠 모델을 안 본다.**

### 4. 위험한 문자열을 넣으면 — script 는 안 돌고 나머지는 돈다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '3,5p'
innerHTML 로 넣었을 때 실행 횟수  script=0  img(onerror)=1  svg(onload)=1
textContent 로 넣었을 때 실행 횟수 = 0  (아무 핸들러도 등록되지 않는다)

(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '6,10p'
viaHTML.children.length = 3   태그 = SCRIPT,IMG,svg
viaText.children.length = 0
viaText.innerHTML = &lt;script&gt;window.run.script++;&lt;/script&gt;&lt;img src="data:image/gif;base64,zzz" onerror="window.run.img++"&gt;&lt;svg onload="window.run.svg++"&gt;&lt;/svg&gt;

innerHTML 이 만든 script 노드는 트리에 있는가 = true   내용 = "window.run.script++;"
(exit 0)
```

**세 함수**

- `A`(`<script>`) = **0회** · `B`(`onerror`) = **1회** · `C`(`onload`) = **1회**.
- `textContent` 로 넣은 쪽은 **전부 0회**다.

**자식 요소**

- `viaHTML.children.length` = **3**, 태그는 **`SCRIPT,IMG,svg`**.
- `viaText.children.length` = **0** — 같은 문자열이 **글자로만** 들어갔고, 읽어 보면 `&lt;script&gt;` 로 이스케이프돼 있다.
- ★ `svg` 만 소문자인 것은 **SVG 요소라서**다([01번 주제](../01-document-and-node-tree/2-summary.md)).

**안 불린 것이 트리에 있나**

- **있다.** `innerHTML 이 만든 script 노드는 트리에 있는가 = true` 이고 내용도 그대로다.
- **「들어갔나」와 「돌았나」는 다른 질문**이고, 트리만 봐서는 못 가른다. 그래서 **전역 카운터라는 창**이 필요했다.

**옮기면 도나**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,13p'
그 script 노드를 다른 부모로 옮겨 붙인 뒤 script 실행 횟수 = 0
createElement 로 만든 script 를 붙이면        script 실행 횟수 = 10
(exit 0)
```

- **안 돈다.** 다른 부모로 옮겨 붙여도 실행 횟수가 **0** 그대로다 — 「안 돈다」는 **그 노드에 찍힌 플래그**이지 자리의 문제가 아니다.
- **`createElement('script')` 로 만든 것은 돈다**(카운터가 10 늘었다). 막힌 것은 **「파싱으로 만들어졌다」는 출처 하나**뿐이다.

### 5. 셋으로 같은 문자열을 쓰면

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04e.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
넣는 문자열 = "한 줄\n다음 줄 <b>굵게</b>"

textContent 로 쓰면 innerHTML = "한 줄\n다음 줄 &lt;b&gt;굵게&lt;/b&gt;"
innerText 로 쓰면   innerHTML = "한 줄<br>다음 줄 &lt;b&gt;굵게&lt;/b&gt;"
innerHTML 로 쓰면   innerHTML = "한 줄\n다음 줄 <b>굵게</b>"

각각의 children.length = 0 / 1 / 1
각각의 childNodes.length = 1 / 3 / 2

textContent = '' 뒤 c.childNodes.length = 0
떼어진 노드는 살아 있다: kept.nodeValue = "한 줄\n다음 줄 "  isConnected = false
(exit 0)
```

**셋의 `innerHTML`**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04e.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '3,5p'
textContent 로 쓰면 innerHTML = "한 줄\n다음 줄 &lt;b&gt;굵게&lt;/b&gt;"
innerText 로 쓰면   innerHTML = "한 줄<br>다음 줄 &lt;b&gt;굵게&lt;/b&gt;"
innerHTML 로 쓰면   innerHTML = "한 줄\n다음 줄 <b>굵게</b>"
(exit 0)
```

- `textContent` 로 쓰면 — `"한 줄\n다음 줄 &lt;b&gt;굵게&lt;/b&gt;"` (태그가 **글자로** 이스케이프됐다)
- `innerText` 로 쓰면 — `"한 줄<br>다음 줄 &lt;b&gt;굵게&lt;/b&gt;"` (★ **줄바꿈이 `<br>` 이 됐다**)
- `innerHTML` 로 쓰면 — `"한 줄\n다음 줄 <b>굵게</b>"` (태그가 **요소가** 됐다)

**두 수**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04e.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '7,8p'
각각의 children.length = 0 / 1 / 1
각각의 childNodes.length = 1 / 3 / 2
(exit 0)
```

- `children` = **0 / 1 / 1**, `childNodes` = **1 / 3 / 2**.

**요소를 안 만드는 것**

- **`textContent`** 뿐이다. 자식이 **텍스트 노드 하나**다.
- 그래서 **「`textContent` 는 절대 실행되지 않는다」가 구조적으로 보장**된다 — 실행될 요소가 아예 안 생긴다.

**`c.textContent = ''` 뒤**

- 자식이 전부 **떼어진다**(`childNodes.length = 0`). 그런데 **떼어진 노드는 살아 있다** — 변수에 담아 둔 것의 `nodeValue` 가 그대로이고 `isConnected` 가 `false` 다([03번 주제](../03-node-creation-insertion-removal/2-summary.md)).

### 6. 비용 — 재서 말한다

**출력** (2000항목 · 9판 중앙값 · **수치는 흔들린다**)

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04d.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
쓰기 — 2000개 항목 만들기 · 9판의 중앙값

innerHTML += 를 항목마다          중앙값  1558.70 ms   최소  1065.30   최대  2777.40
문자열을 모아 innerHTML 한 번     중앙값     1.20 ms   최소     1.00   최대     2.00
appendChild 를 항목마다           중앙값     2.20 ms   최소     1.70   최대     3.40
DocumentFragment 에 모아 한 번    중앙값     2.50 ms   최소     1.60   최대     5.90
textContent 한 번(태그 없음)      중앙값     0.10 ms   최소     0.00   최대     0.30
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04d.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,13p'
읽기 — 위와 같은 2000개 트리에서 · 읽기 전마다 스타일을 건드려 레이아웃을 더럽힌다

textContent 읽기                  중앙값     0.00 ms   최소     0.00   최대     0.30   길이 6890
innerHTML 읽기                    중앙값     0.20 ms   최소     0.10   최대     0.30   길이 32890
innerText 읽기                    중앙값     4.10 ms   최소     3.30   최대    70.10   길이 6890
(exit 0)
```

**쓰기의 자릿수 순위**

```text
   innerHTML += 를 항목마다       ~1,000 ms 대     ★ 혼자 세 자릿수 크다
   ------------------------------------------------ 자릿수 경계
   문자열을 모아 innerHTML 한 번   ~1 ms 대
   appendChild 를 항목마다         ~1 ms 대        셋은 같은 자릿수이고
   DocumentFragment 에 모아        ~1 ms 대        순위가 판마다 뒤집힌다
   textContent 한 번(태그 없음)    분해능 아래
```

- **`+=` 가 혼자 다른 이유** — `+=` 는 **읽기 + 문자열 합치기 + 쓰기**다. 항목마다 **트리 전체를 직렬화하고 전체를 다시 파싱**하므로 항목 수의 제곱으로 자란다.
- ★ **`DocumentFragment` 가 안 빨랐다.** 세 판 모두 `appendChild` 반복과 같은 자릿수였고 순위가 뒤집혔다 — **「조각에 모으면 빠르다」는 이 조건에서 재현되지 않았다.**

**읽기의 순위**

```text
   textContent   분해능 아래
   innerHTML     ~0.2 ms
   innerText     ~3\~5 ms        ★ 한두 자릿수 크다
```

**`innerText` 만 큰 이유**

- **레이아웃을 돌려야 답할 수 있기 때문**이다. 읽기 전마다 스타일을 건드려 레이아웃을 더럽혔고, 그때마다 다시 계산됐다.
- 이것이 **「보이는 것을 답한다」는 계약의 값**이고, [목록의 **10번 주제**](../10-layout-thrashing/)(레이아웃 스래싱)의 씨앗이다.

**`0.00 ms` 의 뜻**

- 「공짜」가 아니라 「**이 도구로는 못 잰다**」다. Chrome 의 `performance.now()` 는 **100마이크로초 단위로 뭉개진다** — 표에 `0.00` 과 `0.10` 만 나오는 것이 그 증거다.

### 7. 「렌더에 의존한다」는 말의 뜻

**먼저 끝나야 하는 단계**

- **스타일 계산과 레이아웃**이다. 「무엇이 보이나」·「어디서 줄이 바뀌나」를 알아야 답할 수 있다.

**CSS 로 답이 바뀌는 예**

```text
   같은 트리 <p>숨은 문단</p>

   style 없음                   -> innerText 에 "숨은 문단" 이 들어간다
   style="display: none"        -> 부모를 통해 읽으면 빠진다
   style="text-transform:upper" -> "abc" 가 "ABC" 로 나온다

   ★ 트리는 한 글자도 안 바뀌었는데 답이 바뀐다
```

- 실측에서 `text-transform: uppercase` 가 걸린 `abc` 가 `innerText` 에서 **`ABC`** 로 나왔다.

**명세의 규정**

- 「요소가 **렌더되고 있지 않으면**(being rendered 가 아니면) `innerText` 는 `textContent` 와 같은 값을 반환한다.」

**비교·검색에서 피하는 이유**

- **화면 상태가 답을 바꾸므로** 같은 데이터에 대해 다른 결과가 나온다. 게다가 **읽기가 비싸다**(위 A6).

### 8. `<script>` 를 막으면 안전한가 — 아니다

**어떤 규정 때문인가**

- **fragment parsing 으로 만들어진 `script` 요소는 실행이 막혀 있다**(명세가 그 노드를 「이미 시작된 것」으로 표시한다). `innerHTML` 이 그 경로를 쓴다.

**실제로 돈 것**

- **`<img onerror>` 와 `<svg onload>`** 다. 각각 **1회** 돌았다.

**면적**

```text
   막힌 것                     안 막힌 것
   +---------------------+    +-------------------------------------------+
   | <script> 실행       |    | on* 이벤트 핸들러 속성 전부                |
   |   (파싱 경로 한정)   |    | javascript: URL                           |
   +---------------------+    | <iframe srcdoc> · <object> · <embed>      |
                              | <style> 를 통한 공격                       |
                              | createElement('script') 경로 (실측: 돈다)  |
                              +-------------------------------------------+
   ★ 막힌 것은 점 하나이고 안 막힌 것은 면이다.
     그래서 '태그 하나 걸러내기' 는 방어가 아니다
```

**`insertAdjacentHTML`**

- **같은 파서를 쓴다.** 안전하지 않다 — **XSS 면적이 `innerHTML` 과 같다.**

### 9. 안전하게 쓰는 법

**면적을 0 으로 만드는 한 줄**

- **`el.textContent = 문자열`** 이다. 요소를 하나도 안 만들므로 실행될 것이 없다.

**권하지 않는 방법**

- **직접 만든 태그·속성 필터**다. 위 A8 의 면적을 사람이 전부 덮을 수 없고, 실측이 보여 주듯 **`<script>` 를 막았다는 감각이 오히려 방심을 만든다.**

**`Trusted Types`·Sanitizer 를 확정하지 않은 이유**

- **저변에 도달하지 않았다.** `Trusted Types` 는 Baseline **newly**(2026-02-24), Sanitizer API 는 **limited** 다([`../README.md`](../README.md)의 지원 표). 방향은 맞지만 **「오늘 이것을 쓰면 된다」로 적을 수 없다.**
- 위협 모델과 방어 설계의 정본은 [`../../security/`](../../security/)이고, 브라우저가 실행 자체를 차단하는 층은 목록의 **58번 주제**(CSP)다.

**자식을 비울 때**

- **`replaceChildren()`** 을 쓴다. `innerHTML = ''` 는 **파서를 부르는 경로**이고, 의도가 「비우기」라면 그 경로를 탈 이유가 없다([03번 주제](../03-node-creation-insertion-removal/2-summary.md)).

### 10. 다른 주제와 잇기

**통째로 갈았을 때의 두 컬렉션**

- [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 실측이 답이다 — **라이브는 새로 생긴 노드들을 가리키고**, **정적 스냅샷은 사라진 옛 노드를 그대로 들고 있다**(`isConnected = false`).

**무엇을 검사하느냐**

```text
   appendChild        부모 종류 · 순환(조상을 자손에) · Document 자식 제약
                      -> 콘텐츠 모델은 안 본다.  <p><div></div></p> 가 만들어진다

   innerHTML          HTML 파싱 알고리즘 전부
                      -> 콘텐츠 모델이 적용된다.  <p>가</p><div>나</div> 로 쪼개진다
```

- 그래서 **「트리가 될 수 있는 모양」이 「파서가 만들 수 있는 모양」보다 넓다.**

**레이아웃 스래싱의 씨앗**

- `innerText` 읽기가 **레이아웃을 강제**하므로, 루프 안에서 읽기와 스타일 쓰기를 교차시키면 **프레임마다 레이아웃이 다시 돈다.** 실측에서 읽기 전 스타일을 건드렸더니 한두 자릿수 비용이 났다.

**`DocumentFragment` 를 주장하지 않은 이유**

- **이 조건에서 재현되지 않았기 때문**이다. 세 판 모두 `appendChild` 반복과 같은 자릿수였고 순위가 뒤집혔다. **널리 알려진 이야기도 실측 대상**이고, 재지 않은 성능 주장은 이 저장소가 금지한다. 조건을 넓혀 다루는 것은 [목록의 **05번 주제**](../05-documentfragment-and-template/)의 몫이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이고, 특히 `innerText` 는 엔진 차이가 남아 있을 수 있는 자리다.

**측정 조건** — 도구는 **`performance.now()`** 하나(JMH 같은 벤치마크 하네스가 아니다) · 머신은 이 Linux 한 대 · **판 수 9** · **중앙값**을 쓰고 최소·최대를 함께 실었다 · 항목 수 **2000** · 판마다 컨테이너를 비우고 다시 만든다 · 읽기 실험은 읽기 전마다 `paddingLeft` 를 토글해 레이아웃을 더럽힌다.\
**재현되는 것은 자릿수와 순위**다. 절댓값은 재현되지 않는다 — 세 판을 비교해 확인했다.\
**신호 대 잡음** — 쓰기의 1등과 2등은 **세 자릿수 차이**라 신호가 압도적이고, **2\~4등은 같은 자릿수 안에서 순위가 뒤집혔다.** 그래서 앞엣것만 결론으로 쓴다.

**하네스** — 01\~04 네 주제가 공유한다.

```bash
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04c.html \
  | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 이 주제의 창 4 — '트리에 있나' 가 아니라 '돌았나' 를 전역 카운터로 남긴다.
// 그리고 창 5 — 9판을 재고 중앙값을 쓴다.
window.run = {script: 0, img: 0, svg: 0};
const med = a => a.slice().sort((x, y) => x - y)[(a.length - 1) >> 1];
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙). XSS 실험은 `load` 이벤트 뒤 `setTimeout(…, 0)` 에서 결과를 찍는다 — 가상 시간을 쓰면 **「아무 일도 안 일어남」이 찍힐** 자리다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 셋을 나란히 읽기(`display:none`·`hidden`·`<style>`·`<br>`·`text-transform`) | 3 | 동작 방식 (0) · A1 |
| 렌더되지 않는 요소와 떼어낸 복제본에서의 `innerText` | 3 | 동작 방식 (1) · A2 · A7 |
| `innerHTML` 파싱 복구 6경우 + 재삽입 안정성 | 2 | 동작 방식 (2) · A3 |
| XSS 3벡터의 **실행 횟수** + 트리에 남은 노드 | 3 | 동작 방식 (3) · A4 · A8 |
| `script` 노드를 옮겨 붙이기 · `createElement('script')` 붙이기 | 2 | 동작 방식 (3) · A4 |
| 셋으로 쓰기 + `textContent = ''` 뒤 뗀 노드 | 2 | 동작 방식 (4) · A5 |
| **쓰기 5방식 × 9판** 중앙값·최소·최대 | 3 | 동작 방식 (5) · A6 |
| **읽기 3방식 × 9판** 중앙값·최소·최대 | 3 | 동작 방식 (5) · A6 |
| `demo04` 를 래퍼에 띄워 두 칸의 계산값·`textContent` 확인 | 1 | 동작 방식 (3)의 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| **모든 시간 수치** | 위 표 | 판마다 흔들린다. **자릿수만 결론으로 쓴다** |
| `performance.now()` 의 분해능 | 100마이크로초 | Blink 의 정책이고 명세가 정한 값이 아니다 |
| `DocumentFragment` 가 안 빨랐던 것 | 같은 자릿수·순위 뒤집힘 | **이 조건에서의 관찰**이다. 일반 규칙으로 읽지 않는다 |
| 직렬화 형태(`hidden=""`·속성 순서) | 위 출력 | 명세 + 구현 |
| `innerText` 의 세부(빈 줄 개수·축약) | 위 출력 | 명세가 렌더 결과를 말하므로 **엔진 차이가 남을 수 있는 자리** |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). **`innerText` 는 원래 IE 확장이라 이 항목의 이식성 위험이 가장 크다.** ② `Trusted Types`·Sanitizer API 의 실제 동작(Baseline 이 각각 newly·limited 라 이 문서의 기준선 밖이다). ③ CSP 로 실행을 차단했을 때의 결과(목록의 **58번 주제**의 몫). ④ `DocumentFragment` 가 이기는 조건(부모가 트리 밖일 때·레이아웃이 중간에 도는 조건) — **조건을 못 찾았다고 적지, 「효과가 없다」로 일반화하지 않는다.**

## 용어 풀이

- **`textContent`** — 하위 트리의 모든 `Text` 를 이어 붙인 문자열. 쓰면 텍스트 노드 하나가 된다.
- **`innerText`** — 렌더된 텍스트. 렌더되지 않는 요소에서는 `textContent` 와 같다.
- **`innerHTML`** — 자식들의 마크업. 쓰면 **fragment parsing** 을 한다.
- **fragment parsing** — 문자열을 **문맥 요소의 자식으로** 파싱하는 절차. 문맥에 따라 결과가 달라진다.
- **XSS(교차 사이트 스크립팅)** — 남이 준 문자열이 내 페이지의 코드로 실행되는 것.
- **이벤트 핸들러 속성** — `onerror`·`onload` 같은 마크업 속성. `innerHTML` 로 들어가면 **그대로 동작한다.**
- **「이미 시작된」 표시** — 파싱으로 만들어진 `script` 노드에 찍히는 플래그. **자리를 옮겨도 안 지워진다.**
- **레이아웃 강제(forced layout)** — 최신 결과가 필요해 그 자리에서 레이아웃을 돌리는 것. `innerText` 읽기가 유발한다.
- **분해능(resolution)** — 측정 도구가 구분할 수 있는 최소 간격. 여기서는 100마이크로초.
- **중앙값(median)** — 여러 판을 크기순으로 늘어놓았을 때 가운데 값.
- **Baseline** — 웹 플랫폼 기능의 지원 상태 기준. `newly`·`widely`·`limited` 로 나뉜다.
