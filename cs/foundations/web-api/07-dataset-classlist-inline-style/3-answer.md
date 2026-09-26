# web-api/07 — `dataset`·`classList`·인라인 `style`: 스크립트가 만지는 세 표면 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/dom.html#dom-dataset)(`dataset`)·[WHATWG DOM Standard](https://dom.spec.whatwg.org/#interface-domtokenlist)(`DOMTokenList`)·[CSSOM](https://drafts.csswg.org/cssom/#the-elementcssinlinestyle-interface)(`CSSStyleDeclaration`)으로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

**★ 이 주제에는 흔들리는 칸이 없다.** 시간도 크기도 재지 않는다.

| 안 흔들리는 칸 | 흔들리는 칸 |
|---|---|
| 속성 이름·값 · `dataset` 키 목록과 순서 · `classList` 반환값과 `length` · `style.length` 와 `item(i)` 목록 · 예외 이름 · 직렬화 문자열 | Chrome 판 번호뿐 |

단축 속성이 풀리는 **낱개 개수**는 명세가 정한 목록이라 흔들리지 않지만, **명세에 낱개가 더해지면 바뀐다** — 그래서 판을 적어 둔다(A8).

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 마크업에서 `dataset` 으로 — 소스의 대문자는 이미 없다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-dataset.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,12p'
마크업 -> 속성 -> dataset  (읽는 쪽)
소스에 쓴 것              트리의 속성 이름              dataset 키
                          "data-foo-bar"                "케밥"
                          "data-foobar"                 "소스에 대문자"
                          "data-x"                      "짧은 것"
                          "data-"                       "이름이 빈 것"
                          "data-1-2"                    "숫자"
                          Object.keys(dataset)          ["fooBar","foobar","x","","1-2"]
                          dataset.fooBar                "케밥"
                          dataset.foobar                "소스에 대문자"
                          dataset['1-2'] · ['12']       "숫자" / undefined
                          dataset 객체 동일성           true
(exit 0)
```

**왜 그런가**

- **키는 다섯 개**다 — `fooBar`·`foobar`·`x`·`''`·`'1-2'`. 속성이 다섯이므로 키도 다섯이다.
- ★ **`data-fooBar` 라고 쓴 것은 `foobar` 가 된다.** HTML 파서가 **속성 이름을 ASCII 소문자로 맞추기 때문**이다 — 트리에 담긴 이름이 이미 `data-foobar` 라 `dataset` 은 대문자를 본 적이 없다. 그 규칙의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **02번**이다.
- **`data-1-2` 가 `'12'` 가 아닌 이유** — 변환 규칙이 「`-` **다음이 ASCII 소문자**일 때만 그 글자를 대문자로 바꾸고 `-` 를 지운다」이기 때문이다. `-1`·`-2` 는 숫자라 **그대로 남는다.** 그래서 점 표기로는 못 읽고 `dataset['1-2']` 로만 읽힌다.
- **`m.dataset === m.dataset` 은 `true`** 다. 부를 때마다 같은 객체를 준다. 그러면서 **값은 라이브**라 속성을 나중에 바꿔도 따라온다(A2 의 마지막 줄).

### 2. `dataset` 에 쓰면 무엇이 생기나 — 대문자마다 `-` 가 하나씩 붙는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-dataset.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,22p'
dataset -> 속성  (쓰는 쪽) — 창 ④ 「담겼나」 왕복
dataset 에 쓴 이름        생긴 속성 이름 · 또는 예외    되읽기
dataset["foo"]            "data-foo"                    "a"
dataset["fooBar"]         "data-foo-bar"                "b"
dataset["fooBAR"]         "data-foo-b-a-r"              "c"
dataset["a1B2"]           "data-a1-b2"                  "d"
dataset["foo-bar"]        예외 SyntaxError              속성이 안 생긴다
dataset["foo-Bar"]        "data-foo--bar"               "f"
dataset[""]               "data-"                       "g"
(exit 0)
```

**왜 그런가**

```text
   foo        ──> data-foo
   fooBar     ──> data-foo-bar
   fooBAR     ──> data-foo-b-a-r     ★ B·A·R 마다 각각 '-소문자'
   a1B2       ──> data-a1-b2
   foo-bar    ──> ✗ SyntaxError
   foo-Bar    ──> data-foo--bar      ★ '-' 는 남고 B 가 '-b' 를 더한다
   ''         ──> data-
```

- **예외는 `foo-bar` 한 줄**이다(`SyntaxError`). 명세가 「키에 `-` 다음이 ASCII 소문자면 던져라」라고 못 박았다. **왕복이 깨지는 것을 막으려는 것**이다 — 그대로 두면 `data-foo-bar` 가 되어 **읽을 때는 `fooBar` 로 돌아오고** 방금 쓴 `foo-bar` 키는 영영 못 읽는다.
- **셋째 줄이 둘째 줄과 갈리는 규칙 한 문장** — **쓰기 변환은 「대문자를 `-소문자` 로 바꾼다」뿐이고, 연속 대문자를 한 덩어리로 묶지 않는다.** 그래서 읽기 규칙의 역이 아니다.
- **여섯째 줄이 안 던지는 것이 더 나쁜 이유** — `-` 다음이 **대문자**라 금지 규칙에 안 걸리고, 결과로 **`-` 가 둘인 `data-foo--bar`** 라는 아무도 기대하지 않는 이름이 조용히 생긴다. 예외라면 즉시 알 텐데 **성공한 것처럼 보인다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-dataset.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '24,29p'
지우기와 최종 상태
w.outerHTML               "<div id=\"w\" data-foo=\"a\" data-foo-bar=\"b\" data-foo-b-a-r=\"c\" data-a1-b2=\"d\" data-foo--bar=\"f\" data-=\"g\"></div>"
delete w.dataset.foo 뒤   null                          w.outerHTML 길이 = 97
setAttr('data-Late-Add')  ["data-late-add"]             dataset.lateAdd = "h"
                          dataset.LateAdd / lateadd     undefined / undefined
최종 Object.keys(dataset) ["fooBar","fooBAR","a1B2","foo-Bar","","lateAdd"]
(exit 0)
```

- `delete el.dataset.foo` 가 **속성을 지운다**(되읽으면 `null`).
- **나중에 `setAttribute('data-Late-Add', …)` 로 대문자를 써도** DOM 이 이름을 소문자로 맞춰 `data-late-add` 가 되고 키는 **`lateAdd`** 다. `dataset.LateAdd`·`dataset.lateadd` 는 **둘 다 `undefined`** — 키는 **정확히 한 가지 표기**로만 열린다.

### 3. `classList` 다섯 메서드 — 셋만 값을 돌려준다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-classlist.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,16p'
연산마다 class 속성이 어떻게 되나 — 왼쪽을 부르고 오른쪽을 되읽었다
연산                          getAttribute('class')       반환값 · length
처음                          "a b"                       length = 2
add('c')                      "a b c"                     (undefined)   length = 3
add('a') 이미 있는 것         "a b c"                     (undefined)   length = 3
add('d','e') 여러 개          "a b c d e"                 (undefined)   length = 5
remove('zz') 없는 것          "a b c d e"                 (undefined)   length = 5
remove('d','e')               "a b c"                     (undefined)   length = 3
toggle('a')                   "b c"                       false   length = 2
toggle('a') 다시              "b c a"                     true   length = 3
toggle('a', true)             "b c a"                     true   length = 3
toggle('a', true) 다시        "b c a"                     true   length = 3
toggle('a', false)            "b c"                       false   length = 2
replace('b','q')              "q c"                       true   length = 2
replace('nope','r')           "q c"                       false   length = 2
contains('q')                 "q c"                       true   length = 2
(exit 0)
```

**왜 그런가**

- **`add`·`remove` 는 `undefined`** 다. 여러 개를 한 번에 받고, **이미 있는 것을 더하거나 없는 것을 빼도 조용하다**(에러가 아니라 「할 일 없음」).
- **`toggle`·`replace`·`contains` 는 값을 돌려준다** — 각각 「그 뒤에 있나」·「바꿨나」·「있나」.
- ★ **두 번째 인자는 「뒤집기」를 「강제」로 바꾼다.**

```text
   toggle('a')          있으면 빼고 없으면 넣는다   -> 반환 = 그 뒤에 있나
   toggle('a', true)    언제나 넣는다 (= add)       -> 반환 언제나 true
   toggle('a', false)   언제나 뺀다   (= remove)    -> 반환 언제나 false
```

- **`toggle('a', true)` 를 두 번 불러도 아무 일도 안 난다** — 실측에서 속성이 `"b c a"` 그대로였고 반환도 `true` 그대로였다. **멱등**이다.
- **`replace('nope','r')` 는 `false` 를 돌려주고 아무것도 안 넣는다.** 속성이 `"q c"` 그대로다. 「없으면 새로 넣는다」가 아니다.
- **왜 두 번째 인자가 있나** — `if (조건) add(); else remove();` 를 `toggle(name, 조건)` 한 줄로 줄이기 위해서다.

### 4. 클래스 이름이 이상하면 — 메서드만 검사한다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-classlist.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '18,24p'
예외와 경계 — 창 ④ 「담겼나」 세 갈래로 가른다
연산                          결과                        되읽은 getAttribute('class')
add('두 칸')                  예외 InvalidCharacterError  "q c"  (안 바뀜)
add('')                       예외 SyntaxError            "q c"  (안 바뀜)
cl.value = 'x  y'             담김   반환 2               "x  y"
className = '가 나 가'        담김   반환 2               "가 나 가"
cl.supports('가')             예외 TypeError              "가 나 가"  (안 바뀜)
(exit 0)
```

**왜 그런가**

| 줄 | 판정 | 이름 |
|---|---|---|
| `add('두 칸')` | **예외** | `InvalidCharacterError` |
| `add('')` | **예외** | `SyntaxError` |
| `cl.value = 'x  y'` | **담김** | — |
| `className = '가 나 가'` | **담김** | — |
| `cl.supports('가')` | **예외** | `TypeError` |

- **두 예외 모두 속성을 안 바꾼다** — 되읽은 값이 `"q c"` 그대로다(「안 바뀜」). **던지기 전에 검사하고, 검사에 걸리면 아무것도 안 한다.**
- **셋째·넷째 줄이 갈리는 이유** — **메서드만 토큰을 검사하고 문자열 대입은 검사하지 않는다.** `classList.value` 와 `className` 은 **속성 원문을 그대로 넣는 창구**라 공백 둘도, 중복 토큰(`'가 나 가'`)도 그대로 담긴다. 실측에서 `length` 는 **2**(중복이 하나로 셈된다)인데 속성 문자열에는 `가` 가 둘 있다.
- **`supports` 가 `TypeError` 인 이유** — 그 메서드는 **「지원 토큰 목록」이 정의된 속성**에서만 쓸 수 있다. `class` 에는 그런 목록이 없으므로 명세가 던지라고 정했다. `link.relList` 처럼 목록이 있는 곳에서는 동작한다(**이 문서는 `relList` 를 던져 보지 않았다**).

### 5. `class` 속성의 공백 — 원문은 남아 있다가 한 번에 정리된다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-classlist.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '26,32p'
잡아 둔 classList 는 라이브인가 · 공백은 어떻게 되나
c.classList === c.classList   true
setAttribute 로 갈아 끼운 뒤  잡아 둔 cl.length = 3       ["z1","z2","z3"]
소스의 class 속성             "  두   칸   띄움  "
classList 로 보면             length = 3                  ["두","칸","띄움"]
classList.value               "  두   칸   띄움  "        (속성 원문 그대로다)
add('끝') 뒤 속성             "두 칸 띄움 끝"             (그때 정규화된다)
(exit 0)
```

**왜 그런가**

- **속성 원문은 `"  두   칸   띄움  "` 그대로 남아 있다.** `classList.value` 도 같은 글자다 — **`value` 는 속성 원문을 그대로 돌려준다.**
- 그런데 **`classList` 로 보면 토큰은 셋**이고 `length` 가 3 이다. 토큰 분해는 읽을 때마다 하는 것이고 속성을 고치지 않는다.
- ★ **`add('끝')` 한 번에 속성이 `"두 칸 띄움 끝"` 으로 정리된다.** 토큰을 하나 더한 뒤 **목록 전체를 다시 직렬화**하기 때문이다.
- **「아무 일도 안 시켰는데 문자열이 바뀐다」가 성립한다** — 내가 시킨 것은 「`끝` 을 더해라」뿐인데 **앞의 여분 공백까지 전부 사라졌다.**
- **위험해지는 경우** — 서버나 테스트가 `class` 속성 **문자열을 원문으로 대조**하고 있을 때, 그리고 CSS 선택자가 `[class="  두   칸   띄움  "]` 처럼 **정확 일치**를 쓰고 있을 때다.

### 6. 인라인 `style` 은 무엇과 같은 것인가 — 세미콜론 하나 차이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-style.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,11p'
인라인 style 은 style 속성 문자열과 같은 것이다
getAttribute("style")                   "color: red; padding-left: 4px"
s.style.cssText                         "color: red; padding-left: 4px;"
둘이 한 글자도 같은가                   false                             (끝의 세미콜론 하나 차이다)
s.style.color · paddingLeft             "red"  "4px"
getPropertyValue('padding-left')        "4px"
s.style.length · item(0)                2  "color"
s.style === s.style                     true
style 속성이 없는 요소                  null                              n.style.cssText = ""
거기에 한 줄 쓰면                       "color: teal;"                    속성 === cssText 가 true
s.style.color = 'navy' 뒤               "color: navy; padding-left: 4px;" 속성 === cssText 가 true
(exit 0)
```

**왜 그런가**

- **처음 두 줄이 한 글자 다르다** — `getAttribute('style')` 은 `"color: red; padding-left: 4px"`(원문), `cssText` 는 **끝에 `;` 가 붙은** `"color: red; padding-left: 4px;"` 다. CSSOM 직렬화가 선언마다 `;` 를 붙이기 때문이다.
- **`style` 속성이 없는 요소의 `el.style` 도 있다** — `null` 이 아니라 **`cssText` 가 `""` 인 빈 선언 목록**이다. 그래서 `n.style.color = 'teal'` 을 바로 쓸 수 있다.
- **한 줄을 쓰고 나면 둘이 같아진다** — 속성이 CSSOM 이 만든 문자열로 통째로 다시 쓰이기 때문이다(마지막 두 줄에서 `속성 === cssText` 가 `true`).
- **`s.style === s.style` 은 `true`** 다. 부를 때마다 같은 객체다. **[08번 주제](../08-getcomputedstyle/2-summary.md)의 `getComputedStyle` 은 여기서 갈린다** — 그쪽은 부를 때마다 새 객체다.

### 7. 쓴 것이 어디로 갔나 — 예외는 한 줄도 없다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-style.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '13,25p'
창 ④ — 쓴 자리에서 되읽어 담김 · 조용히 버려짐 · 예외로 가른다
쓴 것                                   되읽기                            판정
style.color = 'blue'                    "blue"                            담겼다
style.color = 'bogus'                   "blue"                            안 바뀜 — 조용히 버려졌다
style.color = ''                        ""                                지워졌다
style.width = '10'                      ""                                안 바뀜 — 조용히 버려졌다
style.width = '10px'                    "10px"                            담겼다
style.colour = 'red' (오타)             ""                                안 바뀜 — 조용히 버려졌다
setProperty('color','lime','important') "lime !important"                 담겼다
setProperty('--x','7')                  "7"                               담겼다
style['--x'] = '9' (대괄호)             "7"                               안 바뀜 — 조용히 버려졌다
cssText = 'color:green;bogus:1;width:z' "color: green;"                   담겼다
그 뒤 t.getAttribute("style")           "color: green;"
(exit 0)
```

**왜 그런가**

| 줄 | 판정 | 왜 |
|---|---|---|
| `color = 'blue'` | **담김** | 유효한 값 |
| `color = 'bogus'` | **조용히 버려짐** | 색으로 파싱 안 된다 |
| `color = ''` | 지워짐 | 빈 문자열 대입은 「제거」다 |
| `width = '10'` | **조용히 버려짐** | 0 이 아닌 길이에 단위가 없다 |
| `colour = 'red'` | **조용히 버려짐** | 그런 프로퍼티가 없다 — expando 가 생긴다 |
| `style['--x'] = '9'` | **조용히 버려짐** | 커스텀 속성은 카멜 매핑이 없다 |
| `cssText = 'color:green;bogus:1;width:z'` | **일부만 담김** | 유효한 `color` 만 |

- ★ **예외는 한 줄도 없다.** `dataset` 과 `classList` 에는 던지는 자리가 있는데 **`el.style` 은 거의 전부 조용하다.**
- **이유는 CSS 의 설계**다. CSS 는 모르는 선언을 **에러가 아니라 무시**로 처리한다(전방 호환). `el.style` 은 그 문법을 쓰는 표면이라 성질을 그대로 물려받았다. 정본은 [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)다.
- **마지막 줄 뒤 `getAttribute('style')` 은 `"color: green;"`** 이다. 셋을 던졌는데 **둘이 사라졌고 아무 말도 없었다.**
- **커스텀 속성은 `setProperty('--x', …)` / `getPropertyValue('--x')`** 로만 다룬다. 실측에서 `setProperty` 로 넣은 `"7"` 이 대괄호 대입 뒤에도 그대로였다.

### 8. 한 줄 쓰면 목록은 몇 줄이 되나 — 담기는 것은 낱개다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-style.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '27,34p'
한 줄 썼는데 목록에는 몇 줄이 담기나 — 단축 속성은 낱개로 풀린다
style.color = 'red'                     length = 1        "color"
style.margin = '1px 2px'                length = 5        "color margin-top margin-right margin-bottom margin-left"
style.marginTop = '9px' (한 낱개만)     length = 5        "color margin-top margin-right margin-bottom margin-left"
style.margin = '' (단축으로 지우기)     length = 1        "color"
style.background = 'blue'               length = 10       "color background-image background-position-x background-position-y background-size background-repeat background-attachment background-origin background-clip background-color"
그 뒤 getAttribute("style")             "color: red; background: blue;"
u.style.background 되읽기               "blue"                            u.style.margin = ""
(exit 0)
```

**왜 그런가**

```text
   style.color = 'red'         length 1    color
   style.margin = '1px 2px'    length 5    color + margin-top/right/bottom/left
   style.marginTop = '9px'     length 5    이미 있는 낱개를 고친다 (개수 그대로)
   style.margin = ''           length 1    단축으로 지우면 낱개가 전부 빠진다
   style.background = 'blue'   length 10   color + background-* 아홉 낱개
```

- **담기는 것은 낱개이고 직렬화는 단축**이다 — 같은 모양이 아니다. `getAttribute('style')` 이 `"color: red; background: blue;"` 로 **다시 단축으로 되접혔다.** 낱개가 전부 갖춰지고 서로 모순되지 않을 때 CSSOM 이 그렇게 직렬화한다.
- **낱개 하나만 고치려고 단축을 쓰면 나머지 낱개가 전부 초기값으로 리셋된다.** 실측에서 `background = 'blue'` 가 `background-image` 이하 아홉 낱개를 한꺼번에 다시 썼다 — 앞서 심어 둔 `backgroundImage` 는 그때 사라진다.
- **개수는 흔들리는 칸이 아니다** — 명세가 낱개 목록을 정한다. 다만 **명세에 낱개가 더해지면 바뀌므로 판을 적어 둔다**(Chrome 151 · CSS 명세의 오늘 판 기준).

### 9. `el.style` 이 못 보는 것 — 시트도 상속도 안 보인다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-style.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '36,41p'
el.style 은 스타일시트 규칙을 못 본다 — 그 창은 08번 주제다
sheet 의 style 속성                     null
sh.style.color · fontSize               ""  ""
sh.style.length                         0                                 (스타일시트가 칠했는데 0 이다)
getComputedStyle 로 물으면              "rgb(0, 128, 0)"  "21px"
인라인이 있는 s 는                      style.color = "navy"              computed = "rgb(0, 0, 128)"
(exit 0)
```

**왜 그런가**

- **`getAttribute('style')` 이 `null` 이고 `el.style.length` 가 `0`** 이다. 화면은 초록인데 그렇다.
- **`el.style` 이 답하는 것은 「내가 이 요소에 직접 쓴 것」뿐**이기 때문이다. 스타일시트도, 부모에게서 상속된 것도, UA 기본값도 안 본다. 이름이 `style` 인 것은 **`style` 속성**을 가리키는 것이지 「스타일」 일반이 아니다.
- **인라인이 있는 요소에서도 값의 모양이 다르다** — `s.style.color` 는 쓴 글자 그대로 `"navy"` 인데 `getComputedStyle(s).color` 는 **절대화된 `"rgb(0, 0, 128)"`** 다.
- 「지금 무슨 값인가」를 묻는 창구는 **[08번 주제](../08-getcomputedstyle/2-summary.md)** 다.

### 10. 세 표면의 실패 방식 — 하나만 조용하다

**출력** — 앞의 세 블록이 이 답의 근거다. 판정만 모은다.

| 표면 | 예외를 던지는 자리 | 조용히 버리는 자리 |
|---|---|---|
| `dataset` | **있다** — `SyntaxError`(키에 `-소문자`) | 있다 — `foo-Bar` 가 `data-foo--bar` 를 만든다(성공처럼 보인다) |
| `classList` | **있다** — `InvalidCharacterError`·`SyntaxError`·`TypeError` | 있다 — `value`·`className` 대입은 검사를 건너뛴다 |
| `el.style` | **없다**(이 실험에서 0줄) | **거의 전부** |

**왜 그런가**

- **`el.style` 이 조용한 것은 CSS 의 설계**다. CSS 는 모르는 속성·무효한 값을 **에러로 보지 않고 무시**한다. 그래야 새 기능을 쓴 시트가 옛 브라우저에서도 **나머지 선언은 살아서** 동작한다. `el.style` 은 그 파서를 그대로 쓰는 창구다.
- **그래서 창 ④ 는 「쓴 자리에서 곧바로 되읽어 대조하는」 창**이다. 세 갈래로 가른다 — 되읽은 값이 바뀌었으면 **담김**, 그대로인데 예외도 없으면 **조용히 버려짐**, 예외가 나면 **예외**.
- **창 1\~3 으로 안 잡히는 이유** — 창 ①(`--dump-dom`)과 창 ②(프로브)는 **지금 값이 무엇인지**만 보여 준다. 「안 바뀐 것」과 「원래 그 값이던 것」이 **같은 글자**라서 구분이 안 된다. 창 ③(두 번 읽기)에 가장 가깝지만, **쓰기 직전의 값을 잡아 두고 쓰기 직후와 대조한다**는 조작이 있어야 비로소 갈린다.
- ★ 이것이 CSS 갈래의 **진단 3창** 중 **`cssRules`(담겼나)** 와 같은 일을 한다 — 정본은 [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)다.

### 11. 다른 주제와 잇기

**출력** — 창 ① 로 찍은 트리가 네 답을 한꺼번에 받쳐 준다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-tree.html | sed -n '4p'
</head><body><div id="t" class="b c" data-keep="지킨다" style="color: red; font-weight: bold; background: blue;" data-new-key="새로 쓴 것"></div>
(exit 0)
```

**왜 그런가**

- **[06번 주제](../06-attribute-vs-property/2-summary.md)가 넘긴 셋** — ① **`data-*`**(반영이 없다 → `dataset`) ② **`class` 문자열**(`className` 은 반영이지만 문자열 한 덩어리다 → `classList`) ③ **`style` 속성**(→ `el.style`). 06 은 「반영이 아니다」·「문자열이다」까지만 말하고 규칙은 여기로 넘겼다.
- **「라이브」가 걸리는 객체는 `classList`** 다. `setAttribute` 로 속성을 갈아 끼워도 잡아 둔 `classList` 가 따라왔고, `c.classList === c.classList` 가 `true` 였다. `dataset` 도 같은 객체를 주고 값이 라이브다.
- **진단 3창 중 같은 일을 하는 창은 `cssRules`(담겼나)** 다. 저쪽은 **시트의 규칙이 담겼나**를 묻고 이쪽은 **인라인 선언이 담겼나**를 묻는다 — **묻는 자리만 다르고 질문이 같다.**
- **08 이 넘겨받는 질문 한 문장** — **「`el.style` 에 없는 값은 지금 무엇이고, 그것을 어떻게 읽나.」**
- 위 트리가 셋을 한 화면에 보여 준다 — `data-new-key` 가 **속성 목록 맨 뒤에** 붙었고, `class` 는 `"b c"` 로 정리됐고, `style` 문자열에 `font-weight`·`background` 가 이어 붙었는데 **`color` 는 `red` 그대로**(`'bogus'` 가 버려졌다)다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

**측정 조건** — **없다.** 이 주제는 시간도 크기도 재지 않는다. 모든 출력이 **한 글자까지 결정적**이고, **재대조에서 정규화할 칸이 하나도 없다.**

**하네스** — 01\~06 과 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다.

```bash
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-style.html \
  | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 이 주제의 창 ④ — 쓴 자리에서 곧바로 되읽어 세 갈래로 가른다
const 써보기 = (label, fn, read) => {
  const 전 = read();
  try { fn(); const 후 = read();
    row(label, J(후), 후 === 전 ? '안 바뀜 — 조용히 버려졌다' : (후 === '' ? '지워졌다' : '담겼다')); }
  catch (e) { row(label, '예외 ' + e.name, e.message.slice(0, 40)); }
};
// 한글 칸 정렬은 JS 안에서 2폭 padw 로 한다. padEnd 는 UTF-16 단위라 어긋난다.
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).\
★ **`--dump-dom` 은 `load` + `setTimeout(…, 0)` 까지만 기다린다.** 이 주제의 실험은 전부 **파싱 직후 동기**로 끝나므로 그 한계에 안 걸린다.\
★ **출력은 `<pre>` 가 아니라 `<script type="text/plain">` 에 담아 마커로 잘랐다.** `<pre>` 는 이 주제가 싣는 `outerHTML`·`cssText` 문자열을 **이스케이프해 망친다.**

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `dataset` 읽기 — 속성 5종 × 키 변환 | 3 | 동작 방식 (2) · A1 |
| `dataset` 쓰기 — 키 7종의 속성 이름과 예외 | 3 | 동작 방식 (3) · A2 |
| `dataset` 삭제 · 나중 `setAttribute` 의 대소문자 | 2 | 동작 방식 (3) · A2 |
| `classList` 13연산의 속성·반환값·`length` | 3 | 동작 방식 (4) · A3 |
| `classList` 예외 5종과 되읽기 | 3 | 동작 방식 (5) · A4 |
| `classList` 라이브·공백 원문·정규화 | 2 | 동작 방식 (5) · A5 |
| `el.style` ↔ `style` 속성 왕복 9줄 | 2 | 동작 방식 (6) · A6 |
| 창 ④ 「담겼나」 10연산 | 3 | 동작 방식 (7) · A7 · A10 |
| 단축 속성 5단계의 `length` 와 낱개 목록 | 2 | 동작 방식 (8) · A8 |
| `el.style` 대 `getComputedStyle` 5줄 | 2 | 동작 방식 (9) · A9 |
| 창 ① 세 표면으로 바꾼 문서의 트리 | 2 | 동작 방식 (1) · A11 |
| `demo` 블록을 래퍼에 띄워 초기 상태 + 버튼 3종 × 5회 확인 | 1 | 동작 방식 (9)의 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| **단축 속성이 풀리는 낱개 개수** | `margin` 4 · `background` 9 | **명세가 정하지만 낱개가 추가되면 바뀐다.** 판을 적고 다시 찍는다 |
| 직렬화가 단축으로 되접히는 것 | `"color: red; background: blue;"` | 명세가 직렬화를 정하지만 **되접는 조건의 세부**는 구현에 달렸다 |
| `cssText` 끝의 세미콜론 | 위 출력 | CSSOM 직렬화 형식 |
| 속성 목록의 순서(`data-new-key` 가 맨 뒤) | 위 트리 | 「설정된 순서」다. **의미로 읽지 않는다** |
| `--dump-dom` 의 줄바꿈 위치 | 위 트리 | 구현 |
| 예외의 `message` 문구 | 이 문서는 **싣지 않았다**(이름만 실었다) | 문구는 구현이 바꾼다. **이름은 명세가 정한다** |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **`link.relList`·`iframe.sandbox` 의 `supports()`** — `classList` 에서 `TypeError` 라는 것만 쟀고 **동작하는 쪽은 안 던졌다.** 「지원 토큰 목록이 있는 곳에서는 된다」는 **명세를 읽은 것**이다. ③ **`classList` 를 인덱스로 순회하며 `remove`** — 라이브라는 것은 쟀지만 **순회 사고 자체는 안 던졌다**([02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 `HTMLCollection` 실측과 같은 모양일 것이라고만 적는다). ④ **CSP 와 `el.style`** — 명세가 검사 대상을 마크업 쪽으로 두었다는 것만 읽었고 **CSP 를 건 문서를 던져 보지 않았다**(목록의 **58번 주제**의 몫). ⑤ **Typed OM**(`attributeStyleMap`) — 표면만 언급했다. ⑥ **`dataset` 값에 큰 JSON 을 넣었을 때의 비용** — 재지 않았다. 「는다」가 아니라 「**안 쟀다**」로 적는다.

## 용어 풀이

- **`DOMStringMap`** — `el.dataset` 의 타입. 값이 **글자열만** 담기는 맵처럼 생긴 객체.
- **`DOMTokenList`** — `el.classList` 의 타입. 공백으로 갈린 **토큰 목록**을 다루는 **라이브** 객체.
- **`CSSStyleDeclaration`** — `el.style` 의 타입. **선언 목록**이다.
- **케밥 표기** — `data-foo-bar`. **카멜 표기** — `fooBar`.
- **토큰** — 공백으로 갈린 한 낱말. 클래스 이름 하나.
- **정규화** — 토큰 목록을 다시 직렬화하면서 여분 공백이 정리되는 것.
- **단축 속성(shorthand)** — `margin`·`background`. **낱개 속성(longhand)** — `margin-top`·`background-color`. **담기는 것은 낱개**다.
- **커스텀 속성** — `--x`. `setProperty`/`getPropertyValue` 로만 다룬다.
- **조용히 버려짐** — 값이 무효해서 안 담겼는데 예외도 경고도 없는 것.
- **멱등(idempotent)** — 여러 번 해도 한 번 한 것과 같은 것. `toggle(name, true)` 가 그렇다.
- **전방 호환(forward compatible)** — 모르는 것을 에러로 보지 않고 무시해서, 새 기능을 쓴 코드가 옛 구현에서도 나머지는 동작하게 하는 설계.
- **expando** — 표준에 없는데 스크립트가 붙인 프로퍼티(정본: [06번 주제](../06-attribute-vs-property/2-summary.md)).
