# css/syntax/41 — `@supports` 기능 질의 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 질문의 코드를 그대로 돌려 읽은 것**이다.\
> **질의 결과와 실제 규칙의 동작을 매번 둘 다 재서** 대조했다.\
> 규칙은 [CSS Conditional Rules 4](https://drafts.csswg.org/css-conditional-4/)·[5](https://drafts.csswg.org/css-conditional-5/) 로 접지했다.\
> **엔진은 Chrome 하나다.** 웹폰트 실험만 로컬 HTTP 서버로 띄웠다(A9 참고).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 진단 도구가 거짓말하는 자리

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
CSS.supports('selector(:is(.a, ::zzbogus))')  = false
.f14 span color = rgb(29, 78, 216)            ★ 파랑. 규칙이 동작한다
.f7 color       = rgb(0, 0, 0)                @supports 블록은 적용 안 됨
시트의 selectorText 목록
  ["p, span", ":is(.f14) span", ".g1", ".g2", ".g2", ".g3"]
                ^^^^^^^^^^^^^^  ★ ::zzbogus 만 지워졌다
```

**`CSS.supports`**

- **`false`** 다.

**두 요소의 색**

- `.f14 span` **파랑**(`rgb(29, 78, 216)`) — **규칙이 멀쩡히 동작한다.**
- `.f7` **검정** — `@supports` 블록은 적용되지 않았다.

**`selectorText`**

- **`:is(.f14) span`** 이다. 브라우저가 무효한 인자 `::zzbogus` 를 **지워 버린 것이 눈에 보인다.**

**왜 갈리는가**

```text
   경로 A — 스타일시트 파싱                경로 B — selector() 질의
   :is() 는 "너그러운 선택자 목록"          "관대하지 않은 파싱" 을 쓴다
   무효한 인자만 지우고 나머지를 쓴다        인자 하나가 무효면 전체 false

   명세가 이렇게 정한 이유
     관대하게 파싱하면 selector(:is(:완전히-모르는-것)) 도 true 가 되어
     질의가 "이 브라우저가 이 문법을 아는가" 에 아무 정보도 못 준다
   => 도구가 고장난 게 아니라 묻는 질문이 다르다
```

### 2. `:where()`·`:not()` 도 같은가

**출력** (Chrome 151 headless)

```text
CSS.supports('selector(:is(.a))')                = true
CSS.supports('selector(:is(.a, ::zzbogus))')     = false
CSS.supports('selector(:where(.a, ::zzbogus))')  = false
CSS.supports('selector(:not(.a, ::zzbogus))')    = false
CSS.supports('selector(::zzbogus)')              = false
```

**`:where()`**

- **`false`** 다. `:is()` 와 같다.

**`:not()`**

- **`false`** 다.

**두 관대함의 짝이 같은가**

```text
   매칭에서 관대한 것          :is()  :where()          <- :not()·:has() 는 아니다 (07번)
   질의에서 관대한 것          없다   — 셋 다 false

   => 짝이 다른 게 아니라, 질의 쪽에는 관대함이 아예 없다.
      그래서 "매칭 규칙으로 질의 결과를 예측하면 틀린다"
```

- 07번은 **명시도가 묶는 짝**(`:is`/`:not`)과 **관대함이 묶는 짝**(`:is`/`:where`)이 서로 다르다고 적었다.\
  여기에 **세 번째 축**이 붙는다 — **질의에서는 셋 다 `false`** 다.

**진단 수단**

```text
   1) cssRules 의 selectorText      인자가 지워졌으면 그 인자만 무효다
   2) querySelectorAll().length     실제로 잡히나
   3) getComputedStyle()            캐스케이드에서 이겼나
   ★ CSS.supports('selector(...)') 는 위 셋의 대체가 아니다
```

### 3. 언제 `@supports` 가 필요한가

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
.g1 color                  = rgb(21, 128, 61)    초록

.g2 display                = flex
.g2 grid-template-columns  = 1fr 1fr      ★ 쓸모없는 grid 선언이 남았다
.g2 gap                    = 8px

.g3 display                = flex
.g3 grid-template-columns  = none         ★ 깨끗하다
```

**`.g1`**

- **초록**(`rgb(21, 128, 61)`). 뒤 선언 `color: zzbogus(1)` 만 버려지고 앞 선언이 살아남았다.
- **`@supports` 가 필요 없다.** 오류 복구가 이미 폴백을 해 준다([07번 주제](../07-syntax-and-error-recovery/2-summary.md)).

**`.g2`**

- `display` **`flex`** · `grid-template-columns` **`1fr 1fr`**.
- `display: zzgrid` 만 버려지고 **`grid-template-columns: 1fr 1fr` 은 「유효한 선언」이라 살아남았다.**

**`.g3`**

- `display` **`flex`** · `grid-template-columns` **`none`**.
- `@supports` 조건이 거짓이라 **블록 전체가 적용되지 않았다.**

**차이를 만든 것**

```text
   캐스케이드 폴백은 "선언 단위" 로만 되돌린다
     -> 버려지지 않는 선언은 그대로 남는다 (반쪽 폴백)

   @supports 는 "블록 단위" 로 켜고 끈다
     -> 맞물린 선언들이 함께 켜지거나 함께 꺼진다

   판단 한 줄
     "이 한 줄이 무시돼도 나머지가 성립하는가?"
        성립 -> 오류 복구      안 함 -> @supports
```

### 4. 폴백을 어디에 두는가

**깨지는 브라우저**

- **`@supports` 자체를 모르는 아주 오래된 브라우저**다.

**왜 깨지는가**

```text
   07번 — "모르는 at-rule 은 블록까지 통째로 버린다"

   @supports not (display: grid) { .x { display: flex } }
   ^^^^^^^^^ 모르면 이 블록이 cssRules 에 아예 안 담긴다
   => 폴백이 통째로 사라진다.  grid 도 모르고 폴백도 없는 최악의 상태
```

**안전한 배치**

```text
   .grid { display: flex; gap: 8px }                      <- 폴백은 at-rule '밖'
   @supports (display: grid) {
     .grid { display: grid; grid-template-columns: … }    <- 향상만 '안'
   }

   @supports 를 모르는 브라우저 -> 블록이 버려지고 flex 폴백이 남는다
   @supports 를 아는 브라우저   -> 조건을 평가해 판단한다
```

- 「기본은 밖에, 향상만 안에」는 07번의 **at-rule 단위 폐기**에서 곧바로 나오는 배치다.

### 5. 항상 참인 조건

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
.qa  (--x: anything)     = rgb(21, 128, 61)    적용됨
.qb  (color: var(--x))   = rgb(21, 128, 61)    적용됨
.qc  (foo)               = rgb(0, 0, 0)        적용 안 됨
.qd  (zz-prop: 1)        = rgb(0, 0, 0)        적용 안 됨
```

**적용되는 것**

- **`.qa` 와 `.qb`** 다.

**참이 되는 이유**

```text
   --x 의 값은 "뜻은 쓰는 쪽이 정한다" 는 설계라 파서가 아무 토큰이나 받는다
      -> (--x: anything) 은 '파싱 가능' 하다

   var() 는 펼쳐지기 전에 유효한지 알 수 없으므로 파싱을 통과시킨다
      -> (color: var(--x)) 도 '파싱 가능' 하다

   @supports 가 묻는 것은 '파싱 가능한가' 이지 '동작하는가' 가 아니다
```

- 이것이 **07번의 IACVT 와 같은 뿌리**다 — 커스텀 속성은 선언 시점에 아무 검사도 안 받는다.

**커스텀 속성 지원을 물을 수 있는가**

- **없다.** 질의가 언제나 참이므로 **게이트가 영영 안 닫힌다.**

**타입을 고정하는 수단**

- **`@property`** 다([37번 주제](../37-at-property/2-summary.md)). 검사를 선언 시점으로 앞당기고, 무효 값은 `initial-value` 로 떨어진다.\
  지원 여부 자체는 `CSS.supports('at-rule(@property)')` 로 묻는다(실측: `true`).

### 6. 프렐류드가 무효하면

**출력** (Chrome 151 headless)

```text
.g4 = rgb(0, 0, 0)         안 먹음
.g5 = rgb(21, 128, 61)     살아남음
cssRules 에 그 @supports 가 '없다'
```

**두 문단의 색**

- `.g4` **검정** · `.g5` **초록**.

**`cssRules` 에 있는가**

- **없다.** 조건이 거짓인 것과 **완전히 다른 상태**다.

```text
   조건이 거짓                          프렐류드가 무효
   @supports (display: zzgrid) { … }    @supports zzz nonsense { … }
   -> cssRules 에 있다                   -> cssRules 에 없다
   -> 문법은 맞다                        -> at-rule 단위로 폐기됐다
```

**회복 지점**

- **짝 맞는 `}`** 다. 그래서 `.g5` 가 살아남았다([07번 주제](../07-syntax-and-error-recovery/2-summary.md)의 「블록이 있는 at-rule」).

### 7. 명시도와 순서

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
.h1 = rgb(29, 78, 216)     파랑.  #hid1 이 이겼다
.h2 = rgb(29, 78, 216)     파랑.  뒤에 쓴 쪽이 이김
.h3 = rgb(185, 28, 28)     빨강.  뒤에 쓴 쪽이 이김
```

**세 문단의 색**

- `.h1` **파랑** · `.h2` **파랑** · `.h3` **빨강**.

**무엇을 바꾸는가**

```text
   1 출처·중요도  2 요소 안 스타일  3 레이어  4 명시도  5 근접성  6 등장 순서
                                                                   ^^^^^^^^^
                                          @supports 는 여기서만 작용한다
                                          (@media 와 완전히 같다 — 38번)
```

- **규칙을 켤지 말지**만 정한다. 켜진 뒤에는 보통 규칙과 똑같이 경쟁하므로 `#hid1` 에게 진다.

**어느 쪽을 먼저**

- **폴백을 먼저, 향상을 나중에.** 명시도가 같으면 **뒤에 쓴 쪽이 이기므로** 향상이 자연스럽게 덮는다.\
  이것이 4번의 「기본은 밖에, 향상만 안에」와 같은 배치다.

### 8. 다섯 형태

**출력** (Chrome 151 headless)

```text
CSS.supports('(display: grid)')            = true
CSS.supports('selector(:has(a))')          = true
CSS.supports('font-format(woff2)')         = true
CSS.supports('font-tech(color-COLRv1)')    = true
CSS.supports('at-rule(@container)')        = true
CSS.supports('at-rule(@zzbogus)')          = false
CSS.supports('display', 'grid')            = true
CSS.supports('display', '')                = false
CSS.supports('bogus)(')                    = false      예외 없음
```

**다섯 형태**

```text
  (속성: 값)           그 선언을 파싱할 수 있나
  selector(선택자)      그 선택자를 파싱할 수 있나  ★ 관대하지 않다
  font-format(포맷)     그 폰트 파일 포맷을 읽을 수 있나
  font-tech(기술)       그 폰트 기술을 쓸 수 있나
  at-rule(@이름)        그 at-rule 을 아나         ★ Baseline limited
```

**두 호출 형태**

- **두 인자 형태** `CSS.supports('display', 'grid')` — 속성과 값을 따로 준다. **괄호를 안 쓴다.** 논리도 못 쓴다.
- **한 인자 형태** `CSS.supports('(display: grid) or (…)')` — 조건 문자열 하나. **`and`·`or`·`not`·`selector()` 를 전부 쓸 수 있다.**

**예외를 던지는가**

- **안 던진다.** `CSS.supports('bogus)(')` 가 **`false`** 를 돌려줬다. 파싱 실패는 곧 `false` 다.

**`at-rule(@container)`**

- 이 브라우저에서는 **`true`** 다. 모르는 것(`at-rule(@zzbogus)`)은 `false` 였다.
- 다만 **Baseline 은 `limited`** 다(`api.webstatus.dev` 의 `supports-at-rule`). 널리 쓰기에는 이르다.

### 9. 웹폰트

**출력** (Chrome 151 headless + 로컬 HTTP 서버 로그)

```text
CSS.supports('font-format(woff2)')       = true
CSS.supports('font-format(zzbogus)')     = false
CSS.supports('font-tech(color-COLRv1)')  = true
CSS.supports('font-tech(zzbogus)')       = false

@font-face { font-family: TestF;
             src: url("f.zzfmt") format("zzbogus"), url("f.woff2") format("woff2") }
  서버 로그
    GET /font.html HTTP/1.1   200
    GET /f.woff2 HTTP/1.1     200
    ★ f.zzfmt 요청이 아예 없다
```

**두 질의가 묻는 것**

- `font-format(…)` — **파일 포맷**을 읽을 수 있나(`woff2`·`woff`·`opentype`·`truetype` 등).
- `font-tech(…)` — **폰트 기술**을 쓸 수 있나(`color-COLRv1`·`variations`·`palettes` 등).

**`src` 목록의 자체 폴백**

- **된다.** `@supports` 가 전혀 필요 없다.

**네트워크 요청**

- **안 나간다.** 모르는 `format()` 이 붙은 항목은 **건너뛴다** — 실측에서 `f.zzfmt` 요청이 로그에 없었다.

**Baseline 과 같은 이야기인가**

- **아니다.** `font-tech(color-COLRv1)` 이 참인 것은 **이 브라우저 하나**의 답이고, webstatus.dev 의 `colrv1` 은 **limited** 다.\
  크로스 브라우저 판단은 **Baseline 데이터로만** 한다.

### 10. 다른 주제와 잇기

**각각의 단위**

```text
   오류 복구 (07번)        선언 단위 · 규칙 단위 · at-rule 단위로 '버린다'
   @supports  (41번)       블록 단위로 '켜고 끈다'

   겹치는 도구다. 선언 하나면 앞엣것으로 충분하고,
   여러 선언이 한 덩어리로 성립하거나 깨질 때만 뒤엣것이 필요하다
```

**`cssRules` 에 남는가**

- **남는다.** 실측에서 조건이 거짓인 `@supports` 열세 개가 전부 `CSSSupportsRule` 로 담겨 있었다.
- **[38번 주제](../38-media-queries/2-summary.md)의 「조건이 거짓인 `@media`」와 똑같다** — 「안 담겼다」와 「담겼는데 조건이 거짓」을 가르는 그 이야기다.

**세 조건부 at-rule 이 재는 것**

```text
   @media       뷰포트·장치·사용자 선호       (38 · 39번)
   @container   가장 가까운 조상 컨테이너      (40번)
   @supports    브라우저가 그 문법을 아는가    (41번)

   셋 다 "언제 적용하나" 라는 한 축이고, 기준이 다르다
```

**중첩하면**

- 파서가 **`&` 를 덧붙인다.** 실측에서 `.h4 { @supports (display: grid) { .h5 { … } } }` 의 `cssText` 가\
  `.h4 { @supports (display: grid) { & .h5 { color: rgb(21, 128, 61); } } }` 로 읽혔다([14번 주제](../14-css-nesting/2-summary.md)).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**하네스** — 37\~41 다섯 주제가 공유한 것이다. 이 주제는 **질의 결과와 실제 동작을 한 문서에서 같이 재는 것**이 핵심이다.

```bash
# harness.sh body.html probes.js W H  (37~41 공유)
google-chrome --headless --disable-gpu --no-sandbox --window-size=900,600 --dump-dom "$D/index.html"

# 웹폰트 실험만 로컬 HTTP — 어느 파일을 실제로 요청했는지는 서버 로그로만 보인다
(cd srv && python3 -m http.server 8781) &
google-chrome --headless --disable-gpu --no-sandbox --dump-dom http://127.0.0.1:8781/font.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `@supports` 조건 13종의 블록 적용 여부 + `CSSSupportsRule` 전수 | 1 | 동작 방식 (1) · A10 |
| `CSS.supports` 질의 15종 | 1 | 동작 방식 (1)(3)(6) · A2 · A8 |
| `selector(:is(…))` 질의 대 실제 규칙 동작 + `selectorText` | 2 | 동작 방식 (3) · A1 · A2 |
| 질문 1의 코드 그대로 | 1 | A1 |
| 캐스케이드 폴백 대 `@supports` 게이트(`.g1`·`.g2`·`.g3`) | 2 | 동작 방식 (4) · A3 |
| 프렐류드 무효 `@supports` + 뒤 규칙 생존 | 2 | 문법 절 · A6 |
| 명시도 1판 + 순서 2판 | 1 | 동작 방식 (2) · A7 |
| 항상 참인 조건 4종(`--x`·`var()`·`(foo)`·모르는 속성) | 2 | 동작 방식 (5) · A5 |
| 규칙 안 `@supports` 중첩 + `cssText` | 1 | 동작 방식 (2) · A10 |
| `@media` 안 `@supports` | 1 | 동작 방식 (2) |
| `font-format`·`font-tech` 질의 4종 + 블록 적용 | 1 | 동작 방식 (6) · A9 |
| `@font-face src` 폴백 (HTTP, 서버 로그) | 1 | A9 · 더 들어가면 |
| `CSS.supports('bogus)(')` 예외 여부 | 1 | A8 |
| Baseline 조회(`supports`·`css-supports`·`supports-at-rule`·`colrv1`) | 1 | 머리말 · A8 · A9 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `selectorText` 가 `:is(.f14) span` 으로 직렬화되는 것 | 위 | CSSOM 직렬화 세부 |
| `font-tech(color-COLRv1)` 이 참인 것 | `true` | **이 브라우저 하나**의 답이다. Baseline 은 `limited` |
| `at-rule()` 질의가 되는 것 | `true` | Baseline **limited** — 다른 브라우저는 다르다 |
| Baseline | `@supports` widely 2018-03-30 · `CSS.supports()` widely 2020-01-15 · `at-rule()` limited | 2차 집계(`api.webstatus.dev`) |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다 — `selector()` 질의의 비관대함이 다른 엔진에서도 같은지는 **명세로만** 접지했다). ② `@supports` 를 모르는 구형 브라우저에서 블록이 버려지는 것(그런 브라우저가 없다 — 07번의 **모르는 at-rule 실측**(`@totally-unknown`)으로 대신 접지했고 본문에 그렇게 적었다).

**렌더 검증** — 이 주제의 리스트업 `렌더` 칸은 **불필요**다. 계산값과 `cssRules` 로 전부 판정되므로 `demo` 블록을 두지 않았다.
제출 전 `extract-demo-blocks.py` 를 이 주제 문서에 돌려 **demo 블록 0개**임을 확인했다.

## 용어 풀이

- **`@supports`** — 브라우저의 문법 지원 여부로 규칙을 켜는 조건부 at-rule.
- **기능 질의(feature query)** — `@supports` 의 조건. 다섯 형태가 있다.
- **관대하지 않은 파싱** — 무효한 항이 하나라도 있으면 전체를 무효로 보는 파싱. `selector()` 질의가 쓴다.
- **너그러운 선택자 목록** — `:is()`·`:where()` 의 인자 목록. **매칭에서만** 관대하다.
- **general enclosed** — `(foo)` 처럼 뜻을 모르는 괄호 조건. 파싱은 되고 평가는 항상 거짓.
- **프렐류드(prelude)** — at-rule 이름 뒤 `{` 앞까지. 여기가 무효면 at-rule 이 통째로 버려진다.
- **`CSSSupportsRule`** — `@supports` 의 CSSOM 타입. `conditionText` 를 읽는다.
- **`font-format()` / `font-tech()`** — 폰트 파일 포맷 / 폰트 기술을 묻는 질의.
- **`at-rule()`** — at-rule 지원을 묻는 질의. Baseline **limited**.
- **Baseline** — 여러 브라우저의 지원 집계. 질의 결과와 다른 이야기다.
