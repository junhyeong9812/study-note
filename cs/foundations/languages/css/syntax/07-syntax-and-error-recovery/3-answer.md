# css/syntax/07 — CSS 구문과 오류 복구: 선언·규칙·at-rule 단위로 버리는 규칙 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `document.styleSheets[…].cssRules`·`CSS.supports()`·`getComputedStyle`·`matchMedia` 로 읽은 것이다.\
> 규칙은 [CSS Syntax Level 3](https://drafts.csswg.org/css-syntax-3/) 「Error Handling」과 [CSS Cascading and Inheritance Level 5](https://drafts.csswg.org/css-cascade-5/) 로 접지했다.\
> **엔진은 Chrome 하나다** — 「콘솔에 아무것도 안 찍힌다」 같은 관찰은 이 엔진의 것이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 무엇이 사라지고 무엇이 남는가

**출력** (Chrome 151 headless — `cssRules[i].style` 의 속성 목록)

```text
규칙 .c1 = [background-color]
규칙 .c2 = [height]
규칙 .c3 = [margin-top, margin-right, margin-bottom, margin-left,
            padding-top, padding-right, padding-bottom, padding-left]

.c1 color / background-color = rgb(0, 0, 0) / rgb(253, 230, 138)
.c2 width / height           = 764px / 30px
.c3 margin-top / padding-top = 10px / 5px
```

**세 규칙의 속성 목록**

- `.c1` = **`[background-color]`** — `color: redd` 만 사라졌다.
- `.c2` = **`[height]`** — 단위 없는 `width: 10` 이 사라졌다.
- `.c3` = **전부 살았다** — `;;` 는 아무 해가 없다.

```text
  .c1 { color: redd ; background-color: #fde68a }
        ^^^^^^^^^^^   여기까지만 버리고
                      ↑ 다음 ';' 에서 회복한다
```

**브라우저가 출력하는 것**

- **아무것도 출력하지 않는다.** 실측으로 `--enable-logging=stderr` 를 붙여 stderr 를 전부 받았는데 **CSS 관련 줄이 0개**였다(같은 실행의 JS `console.log` 는 정상적으로 찍혔다).
- 예외도, 경고도, Console 탭의 한 줄도 없다.

**`;;` 일 때**

- **아무 일도 없다.** 빈 선언은 그냥 건너뛴다.

**값으로 확인하는 방법**

```js
document.styleSheets[0].cssRules[0].style        // [...] 속성 목록 — 담겼나
CSS.supports('color', 'redd')                    // false
getComputedStyle(el).color                       // rgb(0, 0, 0) — 결과
```

- **앞의 둘이** 「**파서가 담았나**」, 마지막이 「**값이 먹었나**」다. 두 질문은 다르다(A7 참고).

### 2. 선택자 하나가 목록 전체를 죽인다

**출력** (Chrome 151 headless)

```text
시트에 남은 규칙 수 = 2
  남은 규칙 = :is(.s3, .s4) { color: rgb(21, 128, 61); }
  남은 규칙 = .s5 { color: rgb(29, 78, 216); }

.s1 = rgb(0, 0, 0)        .s2 = rgb(0, 0, 0)
.s3 = rgb(21, 128, 61)    .s4 = rgb(21, 128, 61)
.s5 = rgb(29, 78, 216)
```

**남는 규칙 수와 다섯 색**

- **2개.** `.s1`·`.s2` **검정**, `.s3`·`.s4` **초록**, `.s5` **파랑**.
- 첫 규칙은 `cssRules` 에 **아예 없다** — 멀쩡한 `.s1`·`.s2` 까지 같이 잃었다.

**두 번째 규칙의 `cssText`**

- **`:is(.s3, .s4)`** 로 나온다. `::totally-bogus` 가 **지워진 채로** 직렬화됐다.
- 브라우저가 무엇을 버렸는지 **눈으로 볼 수 있는 드문 자리**다.

**한 낱말로**

- **너그러운 선택자 목록(forgiving selector list)** 이다. 무효한 인자만 빼고 나머지를 쓴다.

**안전하게 고치기**

```css
.card, .panel:has(> img) { padding: 16px; }        /* :has() 를 모르면 .card 도 잃는다 */
:is(.card, .panel:has(> img)) { padding: 16px; }   /* .card 는 산다 */
```

- 다만 `:is()` 는 명시도를 **가장 센 인자**로 올린다 — 공짜가 아니다([02번 주제](../02-specificity/2-summary.md), [목록의 **11번 주제**](../11-is-where-not/)).

### 3. 모르는 at-rule 은 어디까지 삼키나

**출력** (Chrome 151 headless)

```text
남은 규칙 수 = 4
  남은 = .a2 { color: rgb(185, 28, 28); }
  남은 = .a3 { color: rgb(21, 128, 61); }
  남은 = @media (totally-unknown-feature: 1) { … }
  남은 = .a4 { … }

.a1 = rgb(0, 0, 0)        .a2 = rgb(185, 28, 28)        .a3 = rgb(21, 128, 61)
```

**세 색**

- `.a1` **검정**(블록까지 같이 버려졌다) · `.a2` **빨강** · `.a3` **초록**.

**회복 지점**

```text
  @이름 prelude { ... }     회복 지점 = 짝 맞는 '}'   -> 블록 안의 규칙까지 버린다
  @이름 prelude ;           회복 지점 = ';'           -> 다음 줄은 산다
```

- `@another-unknown some stuff here;` 뒤의 `.a3` 가 살아난 것이 뒤쪽의 증거다.

**`@scope` 가 사라지는 이유**

- **같다.** 모르는 at-rule 이므로 블록 안의 스타일이 통째로 사라진다.
- [06번 주제](../06-scope/2-summary.md)의 Baseline **newly** 상태가 실무 문제가 되는 것이 바로 이 규칙 때문이다.

**기본 모양을 두는 자리**

- **at-rule 밖**이다. 안에는 「지원되면 더 나은 것」만 담는다.

```css
.card { border: 1px solid #ddd; }              /* 기본 — 밖 */
@scope (.card) to (.card) { … }                /* 향상 — 안. 통째로 사라져도 성립한다 */
```

### 4. 중괄호를 안 닫으면

**출력** (Chrome 151 headless)

```text
시트에 남은 규칙 수 = 1
  cssText = .b1 { color: rgb(185, 28, 28);
                  & .b2 { color: rgb(21, 128, 61); }
                  & .b3 { color: rgb(29, 78, 216); } }

.b1 안의 .b2  = rgb(21, 128, 61)
문서의 다른 .b2 = rgb(0, 0, 0)
```

**남는 규칙 수**

- **1개.** 다만 **버려진 게 아니라 그 안으로 들어갔다.**

**`&` 가 나타나는 뜻**

- 브라우저가 뒤 규칙들을 **`.b1` 의 중첩 규칙**으로 읽었다는 뜻이다.
- 선택자가 사실상 **`.b1 .b2`·`.b1 .b3`** 로 바뀌었다.

**두 `.b2` 의 색**

- `.b1` **안**의 `.b2` = **초록**(`rgb(21, 128, 61)`).
- `.b1` **밖**의 `.b2` = **검정**(안 먹는다).

**중첩 이전과의 대비**

```text
  중첩이 없던 시절                     오늘
  +---------------------------+       +---------------------------+
  | .b2·.b3 은 통째로 버려졌다 |       | .b1 의 자손에게만 먹는다   |
  |  -> 어디서도 안 먹는다     |       |  -> 어떤 곳에서는 먹는다   |
  +---------------------------+       +---------------------------+
```

- **어디서도 안 먹으면 금방 눈에 띈다.** 어떤 곳에서는 먹으면 **정상으로 보이는 화면이 생겨** 훨씬 늦게 들킨다.
- 중첩([목록의 **14번 주제**](../14-css-nesting/))이 표준이 되면서 **오류 복구의 결과 자체가 바뀐** 드문 사례다.

### 5. 괄호를 안 닫으면

**출력** (Chrome 151 headless)

```text
시트에 남은 규칙 수 = 1
  남은 = .v3
.v3 의 속성 목록 = []
.v3 = rgb(0, 0, 0)   .v4 = rgb(0, 0, 0)   .v5 = rgb(0, 0, 0)
```

**남는 규칙 수와 `.v3` 의 내용**

- **1개**(`.v3`)이고, 그 규칙은 **아무 속성도 담지 않았다**(`[]`).
- `.v4`·`.v5` 는 `cssRules` 에 **아예 없다.**

**`;`·`}` 가 회복 지점이 안 되는 이유**

```text
   rgb( 를 만나는 순간 '함수 토큰' 이 열린다
        함수 토큰은 짝 맞는 ')' 를 만날 때까지 모든 것을 '내용' 으로 삼킨다
        ';' 도 '}' 도 그냥 토큰일 뿐이다

   .v3 { color: rgb(1,2,3;  background-color: …; }  .v4 { … }  .v5 { … }
                    ^------------- 여기부터 시트 끝까지 한 덩어리 -------^
```

- 짝 맞는 `)` 가 없으면 **EOF 까지** 간다. 회복 지점이 **없다.**

**닫히지 않은 주석도 같은가**

- **같다.** 실측에서 `/*` 뒤에 쓴 규칙이 시트 끝까지 사라졌다(그 규칙이 `cssRules` 에 없었다).
- 곧 **버리는 단위는 셋(선언·규칙·at-rule)인데, 「아무 데서도 회복 못 함」이라는 네 번째 경우가 따로 있다.**

**무엇을 먼저 의심하나**

- **괄호와 주석.** 「맨 아래 규칙만 안 먹는다」가 아니라 「**어느 줄 아래로 전부 안 먹는다**」면 그 줄 위에서 열린 `(` 또는 `/*` 를 찾는다.
- `cssRules.length` 를 찍어 보면 **몇 개가 삼켜졌는지 숫자로** 나온다.

### 6. 최상위에 선언을 두면

**출력** (Chrome 151 headless)

```text
.y1 = rgb(0, 0, 0)        안 먹는다
```

**`.y1` 의 색**

- **검정.** 그 규칙도 같이 사라졌다.

**세미콜론이 못 지켜 주는 이유**

```text
  최상위에서 파서는 '규칙' 을 기대한다
     규칙의 prelude 는 '{' 를 만날 때까지다 — ';' 로는 안 끝난다

     prelude = "color: #b91c1c; .y1"     <- 다음 규칙의 선택자까지 빨려 들어갔다
     block   = "{ color: #15803d; }"

     prelude 가 선택자로 무효 -> 규칙 전체 폐기 -> .y1 의 블록도 같이 사라진다
```

- **`;` 가 선언 구분자 역할을 하는 것은 블록 안에서뿐**이다.

**파서가 기대하는 것과 프렐류드의 범위**

- 기대하는 것 = **규칙 또는 at-rule.**
- 프렐류드 = **`{` 를 만날 때까지** 전부.

**`@layer base, theme`(세미콜론 없음)과 같은 모양인가**

- **같은 모양이다.** 실측에서 그 시트의 `cssRules.length` 가 **0** 이었다 — at-rule 의 prelude 가 다음 줄의 `{` 까지 빨아들여 블록째 버려졌다([05번 주제](../05-cascade-layers/2-summary.md)).
- **구분자 하나를 빠뜨리면 그 다음 덩어리를 같이 잃는다**는 공통 성질이다.

### 7. 담겼는데 값이 안 먹는 경우

**출력** (Chrome 151 headless)

```text
규칙 .v2 의 속성 목록 = [--x, color, background-color]
.v2 color / background-color = rgb(0, 0, 0) / rgb(253, 230, 138)
.v2 --x 값 그대로            = redd

@media 규칙 = cssRules 에 남아 있다
matchMedia('(totally-unknown-feature: 1)').matches = false
.a4 = rgb(0, 0, 0)
```

**`.v2` 의 속성 목록과 `color`**

- 목록 = **`[--x, color, background-color]`** — **셋 다 담겼다.**
- `color` = **`rgb(0, 0, 0)`** — 담겼는데 안 먹었다.

```text
  .c1 { color: redd }                .v2 { --x: redd; color: var(--x) }
  속성 목록에 color 가 '없다'         속성 목록에 color 가 '있다'
  -> 파서가 안 담았다                 -> 담겼는데 계산 시점에 무효가 됐다
  getComputedStyle -> rgb(0,0,0)     getComputedStyle -> rgb(0,0,0)
        ★ 결과만 보면 구분이 안 된다
```

**`--x` 를 읽으면**

- **`"redd"`** 가 그대로 나온다. 커스텀 속성은 **거의 아무 토큰이나 담는다** — 뜻은 쓰는 쪽이 정하기 때문이다.
- 무효가 되는 것은 `var(--x)` 로 펼친 **그 속성**이고, 그때 선언은 버려지지 않고 **`unset` 처럼** 처리된다(**IACVT**). 정본은 [목록의 **36번 주제**](../36-custom-properties/).

**`@media` 는 남는가**

- **남는다.** 파서는 아무 문제도 못 느꼈다 — 문법이 맞기 때문이다.
- 안 먹는 이유는 오류가 아니라 **조건이 거짓**이어서다(`matches = false`).

**「미지원」을 한 낱말로 적으면 안 되는 이유**

| 경우 | 진단 도구 | 고칠 자리 |
|---|---|---|
| ① 파서가 아예 모른다 | `cssRules` 에 없다 · `CSS.supports` false | 문법·오타·지원 여부 |
| ② 파서는 아는데 조건이 거짓 | `cssRules` 에 있다 · `matchMedia(...).matches` false | 조건식 |
| ③ 담겼는데 계산 시점에 무효 | `cssRules` 에 있다 · 값만 안 먹는다 | 변수 값·`@property` 등록 |

- **셋이 전부 다르고 고칠 자리도 다르다.** 화면 결과는 셋 다 같다.

### 8. `!important` 는 어디까지 봐주나

**출력** (Chrome 151 headless)

```text
  .x1 담김: color: red !important;   -> rgb(255, 0, 0)   빨강
  .x2 담김: color: red !important;   -> rgb(255, 0, 0)   빨강
  .x3 담김: (빈 블록)                -> rgb(29, 78, 216) 파랑
  .x4 담김: color: red;              -> rgb(255, 0, 0)   빨강
```

**네 문단의 색**

- `.x1` **빨강** · `.x2` **빨강** · `.x3` **파랑** · `.x4` **빨강**.

**`!` 와 `important` 사이**

- **공백도 주석도 허용된다.** `red! important` 도, `red ! /*c*/ important` 도 유효하다(실측 셋 다 `!important` 로 담겼다).
- **대소문자도 안 가린다**(`!IMPORTANT`).
- 반면 `!` 가 없는 `red important` 는 **무효**라 그 선언이 버려진다 — `.x3` 의 블록이 비었다.

**선언 밖의 `!important`**

- **앞 선언은 산다.** `.x4` 는 `color: red` 를 담았고 빨강으로 나왔다.
- 떠 있는 `!important` 만 **잘못된 선언 하나**로 취급되어 버려진다.

**내가 쓴 형태와 `cssText` 가 다른 이유**

- CSSOM 이 **정규화해서 직렬화**하기 때문이다. 넷 다 `color: red !important;` 한 형태로 나온다.
- 그래서 `cssText` 는 **「파서가 이해한 것」을 보여 주지 「내가 쓴 것」을 보여 주지 않는다** — 진단할 때 유용한 성질이다.

### 9. 진단 도구가 거짓말하는 자리

**출력** (Chrome 151 headless)

```text
CSS.supports('selector(::totally-bogus)')            = false
CSS.supports('selector(:is(.a, ::totally-bogus))')   = false
CSS.supports('at-rule(@scope)')                      = true
```

**두 질의의 답**

- **둘 다 `false`** 다.

**두 번째가 실제 동작과 어긋나는 이유**

```text
  실제 규칙            :is(.s3, ::totally-bogus, .s4) { ... }   -> 동작한다
                       cssText = ":is(.s3, .s4) { ... }"          너그럽게 파싱했다

  supports 질의        selector(:is(.a, ::totally-bogus))       -> false
                       질의는 '너그럽지 않은 파싱' 을 쓴다
```

- **같은 문자열에 두 가지 파싱이 적용된다.** 질의 결과를 그대로 믿으면 「이건 안 되겠구나」라는 틀린 결론을 얻는다.
- 판단 근거로 쓸 것은 **실제 규칙의 `cssText` 와 값**이다.

**`cssRules` 가 예외를 던지는 때**

- **다른 출처의 시트**일 때다. `file://` 문서가 가져온 시트나 CDN 시트가 그렇다 — `"Cannot access rules"` 예외가 난다.
- 실측에서 `file://` 로 연 문서의 `@import` 시트가 정확히 그랬다([05번 주제](../05-cascade-layers/2-summary.md)).

**「줄 그어진 선언」은 버려진 것인가**

- **아니다.** 그것은 **캐스케이드에서 진 것**이다([01번 주제](../01-cascade-and-priority/2-summary.md)).
- **버려진 선언은 개발자 도구에 아예 안 보인다.** 「줄이 그어졌다」와 「안 보인다」는 서로 다른 진단이다.

### 10. 다른 주제와 잇기

**점진적 향상의 토대라는 말**

- 새 문법을 모르는 브라우저가 **그 한 줄만 버리고 나머지를 정상 처리**하기 때문에, 한 파일로 구형·신형을 동시에 지원할 수 있다.

```css
.btn {
  background: #2563eb;                                    /* 구형도 아는 것 */
  background: color-mix(in oklch, #2563eb 80%, white);    /* 모르면 이 줄만 버린다 */
}
```

- **에러를 던지는 언어였다면** 이 패턴이 성립하지 않는다 — 한 줄 때문에 시트가 안 실렸을 것이다.

**버려진 선언이 걸러지는 단계**

- **네 단계 어디도 아니다.** [04번 주제](../04-value-processing-stages/2-summary.md)의 ① 지정값조차 만들어지지 않는다.
- 파싱은 그 네 단계보다 **앞**이다. 캐스케이드의 후보 목록에 애초에 안 들어간다.

**두 줄 관용구에 필요한 단계**

- **6단계(등장 순서)** 다. 두 선언의 명시도가 같으므로 **나중에 쓴 쪽이 이긴다**([01번 주제](../01-cascade-and-priority/2-summary.md)).
- 그래서 **새 문법을 뒤에** 써야 한다. 순서를 뒤집으면 신형 브라우저에서도 구형 값이 이긴다.

**오류 복구 대 `@supports`**

| | 쓸 자리 |
|---|---|
| 오류 복구 | **선언 하나**가 무시돼도 화면이 성립할 때 (두 줄 관용구) |
| `@supports` | **여러 선언이 맞물려** 한 덩어리로 성립하거나 깨질 때 |

- 기준 한 줄 — **「이 한 줄만 무시돼도 페이지가 성립하는가」.** 성립하면 오류 복구에 맡기고, 아니면 통째로 가른다([목록의 **41번 주제**](../41-supports-feature-queries/)).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**하네스** — 03\~07 다섯 주제가 공유한 것이다. 이 주제만 프로브에서 `getComputedStyle` 뿐 아니라 `cssRules` 를 함께 읽는다.

```bash
# harness.sh body.html probes.js
{ echo '<!doctype html><meta charset="utf-8"><title>probe</title>'
  cat "$1"
  echo '<script>'
  echo 'const __o=[];function P(k,v){__o.push(k+" = "+v)}'
  echo 'function CS(s,p){return getComputedStyle(document.querySelector(s)).getPropertyValue(p)}'
  cat "$2"
  echo 'const __p=document.createElement("pre");'
  echo '__p.textContent="<<<BEGIN>>>\n"+__o.join("\n")+"\n<<<END>>>";'
  echo 'document.body.appendChild(__p);</script>'
} > /tmp/doc.html
google-chrome --headless --disable-gpu --no-sandbox --dump-dom /tmp/doc.html 2>/dev/null \
  | sed -n '/&lt;&lt;&lt;BEGIN&gt;&gt;&gt;/,/&lt;&lt;&lt;END&gt;&gt;&gt;/p' | sed '1d;$d'
```

```js
// 이 주제의 프로브가 쓰는 관용구 — '담겼나' 를 묻는다
const S = document.getElementById('S').sheet;
P('남은 규칙 수', S.cssRules.length);
for (const r of S.cssRules) P('규칙 ' + r.selectorText, '[' + [...r.style].join(', ') + ']');
```

```bash
# 콘솔 출력이 정말 없는지 — stderr 를 전부 받아 본다
google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr \
  --dump-dom cerr.html 2>&1 >/dev/null | grep -iE 'css|redd|parse|invalid'
#  -> 한 줄도 안 나온다 (같은 실행의 JS console.log 는 찍힌다)
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 선언 단위 3경우(`redd`·`width:10`·`;;`)의 속성 목록 | 1 | 동작 방식 (1) · A1 |
| 모르는 속성 이름(`-webkit-totally-fake`) | 1 | 동작 방식 (1) |
| `!important` 표기 7형태 | 2 | 동작 방식 (2) · A8 |
| 선택자 목록 오염 · `:is()` 의 `cssText` | 1 | 동작 방식 (3) · A2 |
| 모르는 at-rule(블록 있음/없음) + 뒤 규칙 생존 | 1 | 동작 방식 (4) · A3 |
| `}` 누락 — `cssText` 의 `&` 와 자손/비자손 색 | 2 | 동작 방식 (5) · A4 |
| `)` 누락 — 남은 규칙 수와 빈 속성 목록 | 2 | 동작 방식 (6) · A5 |
| `/*` 누락 — 뒤 규칙 소실 | 1 | 동작 방식 (6) · A5 |
| 최상위 선언이 다음 규칙을 죽이는 것 | 1 | 동작 방식 (7) · A6 |
| 세미콜론 없는 `@layer` 사전 선언(`cssRules.length = 0`) | 1 | A6 |
| `@media` 알 수 없는 특성 · `@supports` 거짓 조건 | 1 | 동작 방식 (8) · A7 |
| `--x: redd` + `var(--x)` 의 IACVT | 1 | 동작 방식 (8) · A7 |
| `CSS.supports` 4질의(속성/값/선택자/at-rule) | 2 | 문법 절 · A9 |
| **stderr 전체를 받아 CSS 로그가 0줄인지** | 1 | 어디서 틀리나 1 · A1 |
| 전역 키워드 오용 3경우(`10px inherit` 등) | 1 | 동작 방식 (9) 표 · 03번 A8 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| CSS 오류에 **아무 로그도 없는 것** | stderr 0줄 | 명세가 로그를 규정하지 않는다 — 다른 브라우저는 경고할 수 있다 |
| `cssText` 직렬화 형태 | `:is(.s3, .s4)` · `color: red !important;` | CSSOM 직렬화 규칙 + 구현 |
| `file://` 에서 `cssRules` 접근 거부 | `"Cannot access rules"` | 브라우저 보안 정책 |
| `}` 누락이 중첩으로 바뀌는 것 | `& .b2 { … }` | 중첩(css-nesting-1)이 들어온 뒤의 동작 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다) — 특히 **「콘솔에 아무것도 안 찍힌다」는 Chrome 관찰**이고 다른 브라우저는 다를 수 있다. ② 개발자 도구 Styles 패널의 실제 표시(headless 라 UI 가 없다) — 「버려진 선언은 안 보인다」는 명세·구조에서 나온 서술이고 화면으로 확인하지 않았다. 둘 다 본문 해당 자리에 표시했다.

## 용어 풀이

- **오류 복구(error recovery)** — 모르는 것을 만났을 때 어디까지 버리고 어디서 다시 읽기 시작하나.
- **선언(declaration)** — `속성: 값` 한 쌍. 버려지는 가장 작은 단위. 회복 지점은 다음 `;` 또는 `}`.
- **규칙(qualified rule)** — `선택자 { 선언들 }`. 선택자 목록 하나가 무효면 통째로 버려진다.
- **at-rule** — `@` 로 시작하는 문. 블록이 있으면 `}`, 없으면 `;` 까지가 한 문.
- **프렐류드(prelude)** — at-rule 이름 뒤 또는 규칙의 선택자 자리. **`{` 를 만날 때까지**라 다음 덩어리를 빨아들일 수 있다.
- **함수 토큰(function token)** — `rgb(` 처럼 `(` 로 시작하는 토큰. 짝 맞는 `)` 까지 `;`·`}` 를 삼킨다.
- **너그러운 선택자 목록(forgiving selector list)** — `:is()`·`:where()` 의 인자 목록. 무효한 인자만 빼고 쓴다.
- **IACVT(invalid at computed-value time)** — 파싱은 됐는데 계산 시점에 무효가 되는 값. `unset` 처럼 처리된다.
- **점진적 향상(progressive enhancement)** — 모르는 문법이 무시돼도 기본 화면이 성립하게 쌓는 방식.
- **`CSS.supports()`** — 파싱 가능 여부를 묻는 API. **너그럽지 않은 파싱**을 쓴다.
- **`cssRules`** — 시트가 실제로 담은 규칙 목록. 「파서가 담았나」의 정답지.
- **`cssText`** — 파서가 이해한 형태를 정규화해 직렬화한 문자열. 내가 쓴 형태와 다를 수 있다.
