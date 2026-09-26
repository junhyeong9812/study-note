# web-api/06 — 속성(attribute) 대 성질(property): `getAttribute`/`setAttribute` 와 IDL 프로퍼티의 반영 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 와 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/common-dom-interfaces.html#reflecting-content-attributes-in-idl-attributes) 의 「Reflecting content attributes in IDL attributes」 절로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** 다만 이 주제의 결론은 **계약**이라 명세 문장이 근거의 중심이다.

**★ 이 주제에는 흔들리는 칸이 없다.** 시간도 크기도 재지 않는다.

| 안 흔들리는 칸 | 흔들리는 칸 |
|---|---|
| `getAttribute` 반환값 · 프로퍼티 값 · `null` 대 `""` · 직렬화 문자열 · 예외 이름 · 속성 개수·순서 | Chrome 판 번호뿐 |

그래서 제출 전 재대조에서 **정규화할 칸이 하나도 없다** — 블록이 한 글자라도 달라지면 전부 「고칠 것」이다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 칸을 양쪽에서 써 보면 — 네 줄 중 마지막만 갈린다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
① 반영된다 — 이름도 같고 양쪽이 서로 따라간다 (id)
                            getAttribute('id')      el.id
처음                        "a1"                    "a1"
setAttribute('id','b2')     "b2"                    "b2"
el.id = 'c3'                "c3"                    "c3"
removeAttribute('id')       null                    ""
(exit 0)
```

**왜 그런가**

- `id` 는 **꼴 ①**(그대로 반영)이다. 명세가 `HTMLElement` 의 `id` 를 「`id` 콘텐츠 속성을 반영한다」고 못 박았고, 그 반영은 **양방향**이다. `setAttribute` 로 써도 프로퍼티가 따라오고 프로퍼티로 써도 속성이 따라온다.
- **마지막 줄만 갈린다** — 속성을 지우면 `getAttribute` 는 **`null`**(「그 줄이 없다」)이고 `el.id` 는 **`""`**(「빈 칸」)이다. 글자열 반영의 기본값이 빈 문자열이기 때문이다.
- 같은 꼴에 드는 것 — `title`·`lang`·`dir`·`hidden`·`slot`·`accessKey`(속성은 `accesskey`). **이름이 같고 뜻이 같은 것 대부분**이 여기다.
- 이 꼴에서는 **어느 쪽을 써도 된다.** 다만 프로퍼티 쪽이 오타에 조용하므로(A8 참조) 짧은 이름은 프로퍼티, 임의 이름은 `setAttribute` 로 갈라 쓰는 편이 안전하다.

### 2. 이름이 다른 둘 — 예외가 아니라 그냥 없는 프로퍼티다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,14p'
② 이름이 다르다 — class ↔ className · for ↔ htmlFor
                            getAttribute            프로퍼티
el.class 라는 프로퍼티      (없다)                  undefined
class / className           "card big"              "card big"
className = 'x y' 뒤        "x y"                   "x y"
label.for 라는 프로퍼티     (없다)                  undefined
for / htmlFor               "f1"                    "f1"
(exit 0)
```

**왜 그런가**

- **`el.class` 와 `label.for` 는 `undefined`** 다. 예외가 아니라 **정의된 적이 없는 프로퍼티**를 읽은 것이라 자바스크립트가 조용히 `undefined` 를 준다.
- 이름이 갈린 이유는 **역사**다. `class` 와 `for` 는 초기 자바스크립트의 **예약어**였고, 그래서 IDL 쪽 이름을 `className`·`htmlFor` 로 정했다. 오늘의 자바스크립트는 프로퍼티 이름에 예약어를 허용하지만 **이름은 되돌릴 수 없다.**
- **이 꼴은 둘뿐이다** — HTML 요소에서 콘텐츠 속성과 IDL 이름이 갈리는 것은 `class`→`className`, `for`→`htmlFor` 두 쌍이다. (`accesskey`→`accessKey` 처럼 **대소문자만 다른 것**은 다른 이야기다 — 여러 낱말 속성은 전부 카멜로 바뀐다.)
- `className` 은 **문자열 한 덩어리**라 토큰을 더하고 빼려면 직접 자르게 된다. 그 일을 대신하는 것이 [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)의 `classList` 다.

### 3. 세 칸을 나란히 두면 — 세 번째 줄에서 갈린다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '16,22p'
③ 한쪽만 바뀐다 — input.value 는 「초기값」만 반영한다
                            getAttr('value')        .value                  .defaultValue
처음                        "초기"                  "초기"                  "초기"
setAttribute('value','A')   "A"                     "A"                     "A"
inp.value = 'B'             "A"                     "B"                     "A"
setAttribute('value','C')   "C"                     "B"                     "C"
form.reset()                "C"                     "C"                     "C"
(exit 0)
```

**왜 그런가**

- `value` **속성을 반영하는 성질은 `defaultValue`** 다. `el.value` 는 반영이 아니라 명세가 따로 정의한 **「값 모드」 상태**다.
- **갈리는 줄은 `inp.value = 'B'`** 다. 그 순간 명세의 **dirty value flag** 가 서고, 그 뒤로는 `value` 속성을 아무리 고쳐도 `.value` 에 안 온다(네 번째 줄: 속성 `"C"`, `.value` `"B"`).
- **다시 잇는 방법은 `form.reset()`** 이다. 리셋 알고리즘이 `.value` 를 `defaultValue` 로 되돌리고 플래그를 지운다 — 마지막 줄에서 세 칸이 다시 `"C"` 로 모였다.
- 두 번째 줄이 중요하다 — **아직 플래그가 안 섰을 때는 `setAttribute('value', …)` 가 화면까지 바꾼다.** 그래서 「가끔 되는 것처럼 보이는」 코드가 생긴다.

```text
   dirty value flag
   ┌ false ─────────────────────┬ true ────────────────────────┐
   │ 속성 -> .value 가 따라온다 │ 속성 -> .value 안 온다        │
   │ (초기 렌더 · 리셋 직후)     │ (사용자 입력 · .value 대입 뒤)│
   └────────────────────────────┴───────────────────────────────┘
                  .value = 'B'  가 플래그를 세운다
                  form.reset()  이 플래그를 지운다
```

### 4. 체크박스를 속성으로 켜면 — 아무 일도 안 난다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '24,29p'
③ 같은 꼴의 불리언판 — checkbox 의 checked 와 defaultChecked
                            getAttr('checked')      .checked                .defaultChecked
처음 (마크업에 checked)     ""                      true                    true
ck.click() 사용자 조작      ""                      false                   true
setAttribute('checked')     "checked"               false                   true
checked=true · 속성 제거    null                    true                    false
(exit 0)
```

**왜 그런가**

- 같은 구조의 불리언판이다. **`checked` 속성 → `defaultChecked`** 이고 `el.checked` 는 **dirty checkedness flag** 가 붙은 별도 상태다.
- **`ck.click()` 은 속성을 안 바꾼다** — 속성은 `""` 그대로이고 `.checked` 만 `false` 가 된다. 사용자가 마우스로 눌렀을 때도 같다.
- **두 번째 줄로 체크는 안 켜진다.** `setAttribute('checked','checked')` 뒤에도 `.checked` 는 `false` 다. 플래그가 이미 섰기 때문이다.
- **`checked="false"` 라고 쓰면 켜진다.** 불리언 속성은 **있느냐 없느냐만** 보고 값은 무시한다(정본 실측: HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **02번** — `disabled="false"` 인 버튼이 `.disabled === true` 였다).
- 마지막 줄이 반대 방향이다 — `checked = true` 로 켠 뒤 속성을 지우면 **`.checked` 는 `true`, `defaultChecked` 는 `false`** 로 완전히 갈린다.

### 5. 같은 `href` 를 두 창구로 — 읽기는 갈리고 쓰기는 안 갈린다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '31,37p'
④ URL 이 정규화된다 — getAttribute 는 원문, 프로퍼티는 절대 URL
문서의 base = "https://example.org/a/b/"
getAttribute('href')        "sub/page.html?q=1#n"
lk.href                     "https://example.org/a/b/sub/page.html?q=1#n"
lk.protocol/host/pathname   "https:" "example.org" "/a/b/sub/page.html"
lk.search / lk.hash         "?q=1" "#n"
lk.href = '../up.html' 뒤   속성 "../up.html"  프로퍼티 "https://example.org/a/up.html"
(exit 0)
```

**왜 그런가**

- `a.href` 는 「**URL 로 푸는 반영**」이다. 읽을 때 문서의 base(`document.baseURI`)로 **절대 URL 을 만들어** 돌려준다. `getAttribute` 는 그런 절차가 없으므로 **마크업 원문 그대로**다.
- **왕복이 안 맞는다.** `lk.href = '../up.html'` 로 쓰면 **속성에는 쓴 글자가 그대로** 담기고(`"../up.html"`) 프로퍼티만 절대 URL 을 답한다. **네 꼴 중 유일하게 「쓴 것을 그대로 되읽을 수 없는」 꼴**이다.
- 덤으로 오는 조각 프로퍼티는 **같은 절대 URL 을 쪼갠 것**이다 — `protocol` `"https:"`, `host` `"example.org"`, `pathname` `"/a/b/sub/page.html"`, `search` `"?q=1"`, `hash` `"#n"`.
- **원문이 필요한 경우** — 마크업에 무엇이 적혔는지 검사·치환할 때(빌드 도구·링크 검사기). **절대 URL 이 필요한 경우** — 실제로 어디로 가는지 판정할 때(외부 링크 표시·출처 비교).

### 6. 없는 것을 물으면 — 속성은 한 가지, 성질은 네 가지

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '39,45p'
없는 속성을 물으면 — 「빈 값」이 프로퍼티 타입마다 다르다
getAttribute('id')          null                    el.id = ""
getAttribute('class')       null                    el.className = ""
getAttribute('title')       null                    el.title = ""
getAttribute('tabindex')    null                    el.tabIndex = -1
getAttribute('hidden')      null                    el.hidden = false
getAttribute('data-x')      null                    el.dataset.x = undefined
(exit 0)
```

**왜 그런가**

- **속성 쪽 대답은 `null` 한 가지**다. DOM 명세가 「없으면 `null`」로 못 박았다.
- **성질 쪽은 타입마다 다르다** — 글자열 반영은 `""`, 불리언 반영은 `false`, `tabIndex` 는 **`-1`**(그 속성의 기본값), `dataset.x` 는 반영이 아니라 **`undefined`** 다. **네 가지**다.
- `if (el.getAttribute('title') === '')` 는 **속성이 있는데 값이 빈 문자열일 때만** 참이다(`<div title="">`). 없을 때는 `null` 이라 거짓이다.
- 「있는지 없는지」를 묻는 것은 **`el.hasAttribute('title')`** 다. 불리언 속성이면 반영 성질(`el.hidden`)을 읽어도 같은 답이 온다.

### 7. `value` 가 반영이 아닌 이유 — 사용자가 친 것을 마크업이 덮으면 안 되기 때문

**출력** — A3 와 같은 실행에서 **갈리는 두 줄만** 잘라 냈다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '20,21p'
inp.value = 'B'             "A"                     "B"                     "A"
setAttribute('value','C')   "C"                     "B"                     "C"
(exit 0)
```

**왜 그런가**

- 한 문장으로: **사용자가 이미 친 것을 「초기값을 다시 쓴다」가 덮어써서는 안 된다.** 서버가 폼을 다시 그리거나 스크립트가 기본값을 갱신해도 **타이핑 중인 글자는 지켜져야** 한다.
- 명세가 그 상태에 붙인 이름이 **dirty value flag**(`checked` 쪽은 **dirty checkedness flag**)다. **이름이 있다는 것 자체가 구현 사정이 아니라 계약**이라는 뜻이다.
- 만약 양방향 반영이었다면 — 서버 렌더가 `value` 를 다시 내려보낼 때마다, 또는 스크립트가 기본값을 고칠 때마다 **입력칸이 리셋**된다. 그리고 반대로 **타이핑할 때마다 DOM 속성이 계속 바뀌어** `MutationObserver`·직렬화가 매 키 입력에 반응한다.
- 같은 설계가 걸린 것 하나 더 — **`<select>` 의 `selected`** 다. `option.selected` 는 별도 상태이고 `option.defaultSelected` 가 `selected` 속성의 반영이다. (**이 문서는 `select` 를 돌려 보지 않았다** — 명세 구조가 같다는 것만 적는다.)

### 8. 배선이 없거나 이상한 이름 — 세 갈래로 갈린다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-edge.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
반영은 명세가 속성마다 못 박은 것이다 — 없는 자리도 있고 제한된 자리도 있다
                                  getAttribute            프로퍼티
data-user-id (반영 없음)          "7"                     d.dataUserId = undefined
  같은 것을 dataset 으로          "7"                     d.dataset.userId = "7"
d.foo = 1 (그냥 프로퍼티)         null                    d.foo = 1
setAttribute('bar','2')           "2"                     d.bar = undefined
  이때 d.outerHTML                "<div id=\"d\" data-user-id=\"7\" bar=\"2\"></div>"
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-edge.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,15p'
제한된 반영 — 알려진 값만 받고 나머지는 기본값으로 떨어진다 (input.type)
                                  getAttribute('type')    .type
처음                              "text"                  "text"
setAttribute('type','checkbox')   "checkbox"              "checkbox"
setAttribute('type','bogus')      "bogus"                 "text"
setAttribute('type','TEXT')       "TEXT"                  "text"
setAttribute('maxlength','-3')    "-3"                    .maxLength = -1
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-edge.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '17,24p'
값의 모양이 바뀐다 — 속성은 언제나 문자열, 프로퍼티는 IDL 타입
                                  getAttribute            프로퍼티
d.hidden = true                   ""                      d.hidden = true
d.tabIndex = 3                    "3"                     d.tabIndex = 3 (number)
setAttribute('tabindex',' 07 ')   " 07 "                  d.tabIndex = 7
setAttribute('CLASS','q')         "q"                     d.className = "q"
  대문자로 되물으면               "q"                     d.attributes.length = 6
  최종 d.outerHTML                "<div id=\"d\" data-user-id=\"7\" bar=\"2\" hidden=\"\" tabindex=\" 07 \" class=\"q\"></div>"
(exit 0)
```

**왜 그런가**

- **`d.dataUserId` 는 `undefined`** 다. `data-*` 에는 반영이 **없다.** 같은 값을 `d.dataset.userId` 로는 읽을 수 있고 그것이 [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)다.
- **`d.foo = 1` 은 속성을 만들지 않고**(`getAttribute('foo')` 가 `null`), **`setAttribute('bar','2')` 는 프로퍼티를 만들지 않는다**(`d.bar` 가 `undefined`). **배선이 없는 이름은 양쪽 다 조용하다.**
- **넷째·다섯째 줄**(`type`·`maxlength`)이 영영 어긋나는 이유는 **반영의 종류**다. `input.type` 은 「**알려진 값만 받는(limited to only known values)**」 반영이라 모르는 값이면 **기본값 `"text"`** 를 답하고, `maxLength` 는 「**음이 아닌 정수**」 반영이라 `-3` 에 대해 **기본값 `-1`** 을 답한다. 속성 쪽은 쓴 글자를 그대로 보관한다.
- **에러가 없는 것이 위험한 이유** — `el.classname = 'card'` 처럼 오타를 내면 **예외도 경고도 없이 프로퍼티 하나가 생기고 끝난다.** 진단은 창 ④ 하나뿐이다: `el.outerHTML` 을 찍어 **속성이 안 생겼다**를 눈으로 확인하는 것.
- **여섯째 줄의 대문자는 사라졌다.** HTML 문서에서 `setAttribute` 는 이름을 **ASCII 소문자로 맞춘다**(DOM 명세). 그래서 `getAttribute('CLASS')` 도 같은 것을 답하고 `outerHTML` 에는 `class="q"` 로 나온다. 마크업 쪽 같은 규칙의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **02번**이다.
- 마지막 줄의 `d.outerHTML` 이 **이 절의 요약**이다 — 프로퍼티로 쓴 `hidden`·`tabIndex`·`className` 은 속성으로 남았고, `d.foo` 는 흔적이 없다.

### 9. 성질에만 있는 것은 어디까지 따라오나 — 직렬화를 거치는 경로만 잃는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-serialize.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
창 ④ — 바꾼 뒤 문서 자신에게 「속성에 남았나」를 다시 묻는다
처음                fm.innerHTML = "<input id=\"in\" name=\"n\" value=\"초기\"><input id=\"ck\" type=\"checkbox\" checked=\"\">"
                    속성 개수 = 3   .value = "초기"
inp.value 대입 · ck.click() 뒤
                    fm.innerHTML = "<input id=\"in\" name=\"n\" value=\"초기\"><input id=\"ck\" type=\"checkbox\" checked=\"\">"
                    속성 개수 = 3   .value = "사용자가 친 것"   ck.checked = false
                    ★ 직렬화가 한 글자도 안 바뀌었다
inp.id = 'z9' 뒤     fm.innerHTML = "<input id=\"z9\" name=\"n\" value=\"초기\"><input id=\"ck\" type=\"checkbox\" checked=\"\">"
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-serialize.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,16p'
그래서 「복사」 세 경로의 결과가 갈린다 — 던져 보기 전에는 모른다
innerHTML 왕복      복사본 input.value = "초기"   checkbox.checked = true
cloneNode(true)     복사본 input.value = "사용자가 친 것"   checkbox.checked = false
importNode(fm,true) 복사본 input.value = "사용자가 친 것"   checkbox.checked = false
원본                원본   input.value = "사용자가 친 것"   checkbox.checked = false
원본의 defaultValue / defaultChecked = "초기" / true
★ 직렬화를 거친 경로만 사용자 상태를 잃는다. 노드 복제는 HTML 명세가 값을 함께 옮기라고 정한다
(exit 0)
```

**왜 그런가**

- **`innerHTML` 왕복만 잃는다** — 복사본의 `input.value` 가 `"초기"`, `checkbox.checked` 가 `true`(= 마크업의 `checked` 속성대로)다. **글자에는 속성만 있기 때문**이다.
- **`cloneNode(true)` 와 `importNode(…, true)` 는 지킨다** — 둘 다 `"사용자가 친 것"` / `false` 다.
- **이것은 구현의 친절이 아니라 명세의 계약**이다. HTML 명세의 `input` 요소 정의에 **cloning steps** 가 따로 있어서 「값과 체크 상태, 그리고 dirty 플래그를 복제본에 옮긴다」고 정해 두었다.
- **`--dump-dom` 으로 찍으면 원래 마크업이 보인다** — 앞의 블록 세 줄 중 첫 둘이 한 글자도 같다. 창 ① 만으로는 **사용자가 무엇을 쳤는지 영영 알 수 없다.**

```text
   원본 (성질 "사용자가 친 것" / 속성 value="초기")
        │
        ├─ innerHTML ──> "…value=\"초기\"…" ──파싱──> 복사본 .value "초기"      ★ 잃는다
        ├─ cloneNode(true) ─────────────────────────> 복사본 .value "사용자가…"
        └─ importNode(…,true) ──────────────────────> 복사본 .value "사용자가…"
```

### 10. 다른 주제와 잇기

**출력** — 창 ① 로 찍은 트리가 네 답을 한꺼번에 받쳐 준다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-tree.html | sed -n '4,5p'
</head><body><form id="fm"><input id="in" value="초기"><input id="ck" type="checkbox"></form>
<div id="d" class="성질로 바꾼 class" title="성질로 준 title"></div>
(exit 0)
```

**왜 그런가**

- **[04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)와 만나는 자리** — 04 는 `innerHTML` 이 **무엇을 글자로 뽑나**를 다뤘고, 여기는 **그 글자에 무엇이 안 실리나**를 다룬다. 한 문장으로: **`innerHTML` 은 속성만 뽑는다.** 그래서 04 의 「읽기·쓰기 비용」 위에 「**상태 손실**」이라는 항목이 하나 더 붙는다.
- **[05번 주제](../05-documentfragment-and-template/2-summary.md)에 덧붙인 것** — 05 는 `cloneNode` 와 `importNode` 가 **무엇을 만들고 어디에 두나**를 봤다. 여기서 덧붙인 것은 「**폼 상태까지 가져온다**」이고, 그 근거는 `input` 의 cloning steps 라는 **명세의 별도 조항**이다.
- **[02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 라이브 컬렉션이 걸리는 표면** — **`el.attributes`**(`NamedNodeMap`)다. 라이브이므로 앞에서부터 순회하며 `removeAttribute` 하면 **한 칸씩 건너뛴다.** 안전한 형태는 `el.getAttributeNames()` 로 **이름 배열을 먼저 떠 놓고** 지우는 것이다.
- **[07번 주제](../07-dataset-classlist-inline-style/2-summary.md)가 넘겨받는 것** — 이 주제가 「반영이 아니다」까지만 말한 셋이다: **`data-*`**(→ `dataset`), **`class` 문자열**(→ `classList`), **`style` 속성**(→ `el.style`). 07 은 그 셋이 각각 **어떤 규칙으로 속성 칸에 담기나**를 본다.
- 위 트리가 그 전부를 한 화면에 보여 준다 — `className`·`title` 은 남았고, `value` 는 `"초기"` 그대로이며, `checked` 는 **아예 없고**, `zzzNotReflected` 는 흔적도 없다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다. 다만 이 주제의 결론은 **명세가 속성마다 못 박은 계약**이므로, 다른 엔진에서 달라진다면 그쪽이 명세 위반이다 — **그래도 「같을 것이다」라고 적지는 않는다.**

**측정 조건** — **없다.** 이 주제는 시간도 크기도 재지 않는다. 모든 출력이 **한 글자까지 결정적**이고, 그래서 **재대조에서 정규화할 칸이 하나도 없다.**

**하네스** — 01\~05 와 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다.

```bash
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html \
  | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 이 주제의 창 ④ — 성질에 쓴 것이 '속성 칸' 에 남았는가
el.outerHTML                          // 직렬화에 남았나
[...el.attributes].map(a => a.name)    // 속성 칸 전수
copy.innerHTML = fm.innerHTML;         // 왕복 — 글자를 거치면 무엇이 사라지나
// 한글 칸 정렬은 JS 안에서 2폭 padw 로 한다. padEnd 는 UTF-16 단위라 어긋난다.
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).\
★ **`--dump-dom` 은 `load` + `setTimeout(…, 0)` 까지만 기다린다.** 이 주제의 실험은 전부 **파싱 직후 동기**로 끝나므로 그 한계에 안 걸린다.\
★ **출력은 `<pre>` 가 아니라 `<script type="text/plain">` 에 담아 마커로 잘랐다.** `<pre>` 는 이 주제가 싣는 `outerHTML` 문자열을 **이스케이프해 망친다.**

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 꼴 ① `id` 의 양방향 반영 + 속성 제거 | 2 | 동작 방식 (2) · A1 |
| 꼴 ② `class`↔`className` · `for`↔`htmlFor` | 2 | 동작 방식 (3) · A2 |
| 꼴 ③ `value`/`defaultValue` 4단계 + `form.reset()` | 3 | 동작 방식 (4) · A3 · A7 |
| 꼴 ③ 불리언판 `checked`/`defaultChecked` 4단계 | 3 | 동작 방식 (4) · A4 |
| 꼴 ④ `href` 읽기·쓰기 + 조각 프로퍼티 | 2 | 동작 방식 (5) · A5 |
| 없는 속성 6종 × 두 창구 | 2 | 어디서 틀리나 5 · A6 |
| 반영 없음 · 제한된 반영 · 타입 변환 | 3 | 동작 방식 (6) · A8 |
| 창 ④ 직렬화 3회 + 복사 3경로 | 3 | 동작 방식 (7) · A9 |
| 창 ① 성질로만 바꾼 문서의 트리 | 2 | 동작 방식 (7) · A10 |
| `demo` 블록을 래퍼에 띄워 초기 상태 + 버튼 2종 확인 | 1 | 동작 방식 (7)의 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 직렬화 형태(속성 순서·따옴표·`checked=""`·줄바꿈 위치) | 위 출력 | 명세 + 구현. **속성 순서는 「설정된 순서」라 의미로 읽지 않는다** |
| `.maxLength` 가 `-3` 에서 `-1` 인 것 | `-1` | 명세가 정한 기본값이지만 **다른 제한 정수 속성은 기본값이 다르다** |
| `d.attributes.length = 6` | 6 | 이 실험이 만든 개수다. 실험을 고치면 바뀐다 |
| `document.baseURI` 가 `https://example.org/a/b/` 인 것 | 위 출력 | 이 실험이 `<base>` 로 심은 값이다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **`<select>`/`<option>` 의 `selected`** — 명세 구조가 `checked` 와 같다는 것만 적었고 **던져 보지 않았다.** ③ `getAttributeNS`·`setAttributeNode` 계열(SVG 가 섞인 문서를 만들지 않았다). ④ **커스텀 요소가 직접 구현한 반영**([목록의 **13번 주제**](../13-custom-element-lifecycle/)의 몫). ⑤ `el.attributes` 를 순회하며 지웠을 때의 건너뜀 — [02번 주제](../02-element-queries-and-live-collections/2-summary.md)에서 `HTMLCollection` 으로 실측한 것을 **같은 성질이라고 적었을 뿐 `NamedNodeMap` 으로 다시 던지지는 않았다.** ⑥ **이미지·폼의 URL 속성**(`img.src`·`form.action`) — `a.href` 하나만 쟀다. **「URL 속성 전부가 그렇다」로 일반화하지 않는다.**

## 용어 풀이

- **콘텐츠 속성(content attribute)** — 마크업에 쓰인 속성. `getAttribute` 가 다루고 **값은 언제나 글자열**이다.
- **IDL 속성 · 성질(IDL attribute)** — DOM 객체에 달린 프로퍼티. **타입이 있다.**
- **반영(reflect)** — 명세가 두 칸을 잇는다고 못 박은 것. 종류가 여럿이다.
- **dirty value flag** — `.value` 가 한 번이라도 바뀌었음을 표시하는 명세의 플래그. 서면 속성 변경이 `.value` 에 안 온다.
- **dirty checkedness flag** — 위의 체크 상태판.
- **`defaultValue`·`defaultChecked`** — `value`·`checked` **속성을 반영하는** 성질.
- **알려진 값만 받는 반영** — 모르는 값이면 기본값을 답하는 반영(`input.type`).
- **URL 로 푸는 반영** — 읽을 때 base 로 절대 URL 을 만드는 반영(`a.href`).
- **expando** — 표준에 없는데 스크립트가 붙인 프로퍼티. 속성도 안 만들고 직렬화에도 안 남는다.
- **`NamedNodeMap`** — `el.attributes` 의 타입. **라이브**다.
- **cloning steps** — 요소를 복제할 때 추가로 밟으라고 명세가 요소별로 정해 둔 절차. `input` 의 값 복사가 여기 있다.
- **직렬화(serialize)** — 노드 트리를 HTML 글자열로 뽑는 것.
- **base URL** — 상대 URL 을 절대 URL 로 풀 때의 기준. `document.baseURI` 로 읽는다.
