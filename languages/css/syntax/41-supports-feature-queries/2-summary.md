# css/syntax/41 — `@supports` 기능 질의 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Conditional Rules Module Level 4](https://drafts.csswg.org/css-conditional-4/) 의 「`@supports`」·「Supports Queries」·「`CSS.supports()`」 절과 [CSS Conditional Rules 5](https://drafts.csswg.org/css-conditional-5/) 의 `font-format()`/`font-tech()`. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 값은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getComputedStyle`·`cssRules`·`CSS.supports()` 로 읽은 것이다. **질의 결과와 실제 규칙의 동작을 매번 둘 다 재서** 대조했다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — CSS 에 언어 버전은 없다. `@supports` 는 Baseline **widely**(2015-09-30 → 2018-03-30) · `CSS.supports()` 는 **widely**(2020-01-15) · **`at-rule()` 질의는 Baseline limited** 인데 **Chrome 151 은 지원한다**(실측) — `api.webstatus.dev` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`@supports` 는 「이 브라우저가 이 문법을 아느냐」를 묻는 자다. 그런데 이 자가 때때로 거짓말을 한다.**

통역사에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 「이 낱말 아세요?」 하고 묻는다 | `@supports (display: grid)` · `CSS.supports(…)` |
| 통역사가 「모릅니다」 하면 다른 말로 바꾼다 | `@supports not (…) { 폴백 }` |
| 그런데 **묻는 말투가 너무 딱딱해서** 아는 것도 「모른다」고 한다 | ★ **질의는 관대하지 않은 파싱을 쓴다** |
| 실제로 문장을 던져 보면 잘 알아듣는다 | 같은 선택자를 쓴 **규칙은 정상 동작한다** |
| 한 낱말만 모르면 그 낱말만 버리고 문장은 산다 | **오류 복구**([07번](../07-syntax-and-error-recovery/2-summary.md)) — 대개 이걸로 충분하다 |

- **CSS 에는 이미 오류 복구가 있다.** 모르는 선언은 그 줄만 버려지고 앞줄이 살아남는다.\
  그래서 **`@supports` 가 필요한 경우는 생각보다 적다** — 아래 (4)가 그 경계다.
- **`@supports` 가 진짜로 필요한 것은 「여러 선언이 한 덩어리로 맞물릴 때」** 다.\
  실측에서 캐스케이드 폴백은 **반쪽만** 되돌아왔다.

```text
   ★ 진단 도구가 거짓말하는 자리 (실측)

   CSS.supports('selector(:is(.a, ::zzbogus))')   ->  false
   @supports selector(:is(.a, ::zzbogus)) { … }   ->  블록이 적용 안 됨

   그런데 같은 선택자를 쓴 규칙은
     :is(.f14, ::zzbogus) span { color: #1d4ed8 }
     .f14 span 의 실제 색 = rgb(29, 78, 216)      ★ 정상 동작한다
     시트에 담긴 selectorText = ":is(.f14) span"  ★ 이상한 인자만 지워졌다

   => 「질의가 false 니까 안 되겠구나」로 읽으면 틀린다
```

실무에서 이게 터지는 자리는 **`@supports selector(...)` 로 새 선택자를 게이트할 때**다.\
질의가 `false` 라서 폴백이 켜지는데, **폴백이 없어도 원래 규칙이 잘 동작한다.** 멀쩡한 기능을 스스로 끄는 것이다.

> **기능 질의(feature query)** — `@supports` 로 브라우저의 지원 여부를 묻고 그 결과로 규칙을 켜는 것.\
> 예: `@supports (display: grid) { … }` 는 grid 를 아는 브라우저에서만 안쪽을 적용한다.

> **관대하지 않은 파싱(non-forgiving parsing)** — 목록 안에 무효한 항이 하나라도 있으면 전체를 무효로 보는 파싱.\
> 예: `:is()` 는 실제 매칭에서는 관대한데, `selector()` 질의는 관대하지 않게 파싱해 `false` 를 돌려준다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **언제 `@supports` 가 필요하고 언제 오류 복구로 충분한가.**
2. **질의가 거짓말하는 자리는 어디이고 왜 그런가.**
3. **무엇을 물을 수 있고 무엇은 못 묻는가.**

## 동작 방식

### (1) 무엇을 물을 수 있나 — 다섯 형태

**언제 쓰나** — `@supports` 를 쓸 때마다.

```text
  (속성: 값)              @supports (display: grid)
  selector(선택자)         @supports selector(:has(a))
  font-format(포맷)        @supports font-format(woff2)
  font-tech(기술)          @supports font-tech(color-COLRv1)
  at-rule(@이름)           CSS.supports('at-rule(@container)')     ★ Baseline limited

  논리                     and · or · not · 괄호
```

```text
실측 — 열세 개 조건을 한 시트에 담고 각 블록의 적용 여부를 봤다

  조건                                        블록이 적용됐나
  ----------------------------------------    ---------------
  (display: grid)                              O
  (display: zzgrid)                            X
  (zz-prop: 1)                                 X
  not (display: zzgrid)                        O
  selector(:has(a))                            O
  selector(::zzbogus)                          X
  selector(:is(.a, ::zzbogus))                 X      ★ 아래 (3)
  ((display:grid) and (display:flex)) or (display: zzgrid)   O
  font-format(woff2)                           O
  font-tech(color-COLRv1)                      O
  (foo)                                        X      괄호만 친 것은 거짓
  (--x: anything)                              O      ★ 아래 (5)
  (display: grid) and (zz: 1)                  X      한 항이 거짓이면 전체 거짓

  CSSSupportsRule 은 열세 개 전부 cssRules 에 담겨 있었다
```

그림 해설 (한 단계씩):

- **조건이 거짓이어도 규칙은 버려지지 않는다.** `@media` 와 똑같다([38번 주제](../38-media-queries/2-summary.md)) — 「담겼는데 조건이 거짓」이다.
- `CSS.supports` 는 두 가지 호출 형태가 있다.

```text
  CSS.supports('display', 'grid')          속성·값을 따로 — 괄호를 안 쓴다
  CSS.supports('(display: grid)')          조건 문자열 하나로 — 논리도 쓸 수 있다

  실측  CSS.supports('display','')      -> false      빈 값은 거짓
        CSS.supports('bogus)(')         -> false      망가진 문자열도 예외 없이 false
```

비용 — 없음.

### (2) `@supports` 는 명시도를 안 바꾼다 — `@media` 와 같다

**언제 쓰나** — 「`@supports` 안에 넣었는데 안 먹는다」를 진단할 때.

```text
실측

  #hid1 { color: #1d4ed8 }                          명시도 (1,0,0)
  @supports (display: grid) { .h1 { color: #b91c1c } }  명시도 (0,1,0)
     .h1 = rgb(29, 78, 216)     파랑.  조건이 참인데도 졌다

  @supports (display: grid) { .h2 { 빨강 } }        .h3 { 파랑 }
  .h2 { 파랑 }                                      @supports (display: grid) { .h3 { 빨강 } }
     .h2 = rgb(29, 78, 216) 파랑                       .h3 = rgb(185, 28, 28) 빨강
     뒤에 쓴 쪽이 이긴다                                뒤에 쓴 쪽이 이긴다
```

그림 해설 (한 단계씩):

- 조건부 규칙은 **규칙을 켤지 말지**만 정한다. 켜진 뒤에는 **보통 규칙과 똑같이** 경쟁한다.
- 그래서 **폴백을 먼저, 향상을 나중에** 쓰는 것이 관례다 — 순서만으로 이기게 하려는 것이다.
- 중첩도 된다. 실측에서 `.h4 { @supports (display: grid) { .h5 { … } } }` 가 `& .h5` 로 펼쳐졌다([14번 주제](../14-css-nesting/2-summary.md)).

비용 — 없음.

### (3) ★★ 진단 도구가 거짓말하는 자리 — `selector()` 는 관대하지 않다

**언제 쓰나** — `selector()` 질의를 쓸 때. **이 주제의 과녁이다.**

```text
실측 — 질의 결과와 실제 동작을 둘 다 쟀다

  질의                                              결과
  ---------------------------------------------    ------
  CSS.supports('selector(:is(.a))')                 true
  CSS.supports('selector(::zzbogus)')               false      당연하다
  CSS.supports('selector(:is(.a, ::zzbogus))')      false      ★
  CSS.supports('selector(:where(.a, ::zzbogus))')   false      ★
  CSS.supports('selector(:not(.a, ::zzbogus))')     false

  같은 선택자를 쓴 실제 규칙
    :is(.f14, ::zzbogus) span { color: #1d4ed8 }
      .f14 span 의 색      = rgb(29, 78, 216)       ★ 동작한다
      시트의 selectorText = ":is(.f14) span"        ★ 이상한 인자만 지워졌다

  @supports selector(:is(.a, ::zzbogus)) { .f7 { … } }
      .f7 = rgb(0, 0, 0)                            블록이 적용 안 됨
```

```text
   같은 선택자, 두 경로, 다른 답

   경로 A — 스타일시트 파싱                경로 B — selector() 질의
   +-----------------------------+        +-----------------------------+
   | :is() 는 "너그러운 목록"     |        | 질의는 관대하지 않게 파싱한다|
   |   무효한 인자만 지운다       |        |   인자 하나가 무효 -> false |
   |   -> :is(.f14) 로 살아남는다 |        |                             |
   +-----------------------------+        +-----------------------------+
     결과: 규칙이 동작한다                   결과: "지원 안 함" 이라 답한다
```

```text
   왜 이렇게 설계했나

   질의의 목적은 "이 브라우저가 이 문법을 온전히 아는가" 다.
   관대하게 파싱하면 :is(:완전히-모르는-것) 도 true 가 되어
   질의가 아무 정보도 못 준다.
   그래서 명세가 selector() 에 "관대하지 않은 파싱" 을 못 박았다.
   -> 도구가 고장난 게 아니라, 묻는 질문이 다른 것이다
```

그림 해설 (한 단계씩):

- **`:is()`·`:where()` 의 관대함은 「매칭」에만 있다.** 「질의」에는 없다.
- 07번 실측에서도 같은 것이 나왔다 — **이 문서는 그 자리를 정본으로 맡는다.**
- 그래서 판정은 **질의가 아니라 실제 규칙의 `selectorText` 와 계산값**으로 한다.

```text
   올바른 진단 순서 (07번의 진단 3창 + 이 주제)

   1) cssRules 에서 그 규칙의 selectorText 를 읽는다
        ":is(.f14) span" 처럼 인자가 지워졌으면 -> 그 인자만 무효다
   2) querySelectorAll 로 잡히는지 본다
   3) getComputedStyle 로 이겼는지 본다
   ★ CSS.supports('selector(...)') 는 위 셋의 대체가 아니다
```

비용 — 없음. 대신 **질의 결과를 그대로 믿으면 멀쩡한 기능을 스스로 끈다.**

### (4) ★ 언제 `@supports` 가 필요한가 — 캐스케이드 폴백과의 경계

**언제 쓰나** — 폴백을 쓸 때마다. **대개는 안 필요하다는 것이 결론이다.**

```text
실측 A — 선언 하나면 오류 복구로 충분하다

  .g1 { color: #15803d; color: zzbogus(1); }
     .g1 = rgb(21, 128, 61)      초록.  뒤 선언이 버려지고 앞 선언이 남았다
     @supports 가 없어도 폴백이 된다
```

```text
실측 B — 여러 선언이 맞물리면 캐스케이드 폴백은 "반쪽" 만 된다

  캐스케이드 폴백 (.g2)                      @supports 게이트 (.g3)
  .g2 { display: flex; gap: 8px }            @supports (display: zzgrid) {
  .g2 { display: zzgrid;                       .g3 { display: zzgrid;
        grid-template-columns: 1fr 1fr }              grid-template-columns: 1fr 1fr }
                                             }
                                             .g3 { display: flex; gap: 8px }

  실측                                       실측
    display               = flex               display               = flex
    grid-template-columns = 1fr 1fr  ★         grid-template-columns = none  ★
    gap                   = 8px                (블록이 통째로 안 담겼다)

  ★ 왼쪽에는 쓸모없는 grid 선언이 살아남는다.
    display: zzgrid 만 버려지고, grid-template-columns: 1fr 1fr 은 '유효한 선언' 이라 남는다
```

```text
   판단 한 줄

   "이 한 줄이 무시돼도 나머지가 성립하는가?"
        성립한다  ->  오류 복구에 맡긴다 (같은 속성 두 줄)
        안 한다   ->  @supports 로 덩어리째 가른다
```

그림 해설 (한 단계씩):

- **모르는 값은 선언 하나만 버린다**([07번 주제](../07-syntax-and-error-recovery/2-summary.md)). 그래서 `color` 를 두 줄 쓰는 관용구로 충분하다.
- **문제는 「남는 선언」이다.** `display` 만 버려지고 `grid-template-columns` 가 남으면, flex 레이아웃에 쓸모없는 grid 속성이 붙어 있게 된다.\
  대부분은 무해하지만 **`gap`·`place-items` 처럼 두 레이아웃 모두에서 뜻이 있는 속성**이 섞이면 실제로 어긋난다.
- **`@supports not (…)` 로 폴백을 쓰는 패턴**은 이 문제를 반대쪽에서 푼다.

```text
   두 패턴

   (a) 향상 게이트  — 폴백을 기본으로, 향상만 안에
       .grid { display: flex }
       @supports (display: grid) { .grid { display: grid; grid-template-columns: … } }
       ★ 모르는 브라우저에서 블록째 안 담긴다 -> 안전하다

   (b) 폴백 게이트  — @supports not (…) 안에 폴백
       .grid { display: grid; grid-template-columns: … }
       @supports not (display: grid) { .grid { display: flex } }
       ★ 위험하다 — 아주 오래된 브라우저는 @supports 자체를 모른다.
         그러면 이 블록이 통째로 버려져 폴백이 안 걸린다
```

비용 — (a)는 없음. (b)는 `@supports` 를 모르는 브라우저에서 폴백이 사라진다.

### (5) ★ 항상 참이 되는 조건들 — 물어도 소용없는 것

**언제 쓰나** — 커스텀 속성이나 `var()` 를 게이트하려 할 때.

```text
실측

  CSS.supports('(--x: anything)')        -> true       ★ 커스텀 속성은 뭐든 파싱된다
  CSS.supports('(color: var(--x))')      -> true       ★ var() 도 언제나 파싱된다
  @supports (--x: anything) { .f12 { … } }  -> 블록이 적용됨
  @supports (color: var(--x)) { .h7 { … } } -> 블록이 적용됨

  반면
  CSS.supports('(foo)')                  -> false      괄호만 친 것(general enclosed)
  CSS.supports('(zz-prop: 1)')           -> false      모르는 속성 이름
  CSS.supports('(display: zzgrid)')      -> false      모르는 값
```

```text
   왜 항상 참인가

   --x 의 값은 "뜻을 쓰는 쪽이 정한다" 는 설계라 파서가 아무 토큰이나 받는다.
   var() 도 마찬가지 — 펼쳐지기 전에는 유효한지 알 수 없으므로 파싱은 통과시킨다.
   => "커스텀 속성을 지원하나" 를 @supports 로 물을 수 없다.
      (--x: anything) 이 참인 것은 '지원한다' 가 아니라 '파싱은 된다' 는 뜻이다
```

그림 해설 (한 단계씩):

- 이것이 **07번의 IACVT 이야기와 같은 뿌리**다 — 커스텀 속성은 **선언 시점에 아무 검사도 안 받는다.**
- 타입 검사를 앞당기고 싶으면 `@property` 로 등록한다([37번 주제](../37-at-property/2-summary.md)).
- **`at-rule(@property)` 질의는 참이었다**(실측). at-rule 지원 여부는 이쪽으로 묻는다.

비용 — 없음. 다만 **참인데 아무 정보도 없는 질의**를 게이트로 쓰면 폴백이 영영 안 켜진다.

### (6) `font-format()` 과 `font-tech()`

**언제 쓰나** — 웹폰트 폴백을 쓸 때.

```text
실측

  CSS.supports('font-format(woff2)')        -> true
  CSS.supports('font-format(zzbogus)')      -> false
  CSS.supports('font-tech(color-COLRv1)')   -> true
  CSS.supports('font-tech(zzbogus)')        -> false

  @supports font-format(woff2)     { … }  -> 블록 적용됨
  @supports font-tech(color-COLRv1){ … }  -> 블록 적용됨
```

```text
   두 질의가 묻는 것이 다르다

   font-format(woff2)         이 '파일 포맷' 을 읽을 수 있나
                              woff2 · woff · opentype · truetype · collection …

   font-tech(color-COLRv1)    이 '폰트 기술' 을 쓸 수 있나
                              color-COLRv1 · variations · palettes · features-opentype …
```

- ★ **`font-tech(color-COLRv1)` 이 참인 것과 「COLRv1 이 Baseline widely 이다」는 다른 이야기**다.\
  webstatus.dev 에서 `colrv1` 은 **limited** 로 나온다. 질의는 **이 브라우저가** 아는지만 말한다.

비용 — 없음.

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
.grid { display: flex; gap: 8px; }
@supports (display: grid) {
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
}

@supports selector(:has(a)) and (not (display: zzgrid)) { … }
@supports font-format(woff2) { @font-face { src: url(f.woff2) format("woff2") } }
```

```js
CSS.supports("display", "grid")            // 속성·값 두 인자 — 괄호 없음
CSS.supports("(display: grid) or (display: zzgrid)")   // 조건 문자열 하나
CSS.supports("at-rule(@container)")        // Baseline limited 인데 Chrome 151 은 true
```

### 금지 사례 — 던져서 확인한 것

```css
@supports (--x: anything) { … }              /* 항상 참 — 게이트로 못 쓴다 */
@supports (color: var(--x)) { … }            /* 항상 참 */
@supports (foo) { … }                        /* 괄호만 — 항상 거짓 */
@supports selector(:is(.a, ::zzbogus)) { … } /* 거짓인데 그 선택자 규칙은 동작한다 */
@supports zzz nonsense { .g4 { … } }         /* 프렐류드가 무효 -> at-rule 이 통째로 버려진다 */
```

```text
실측 — 프렐류드가 무효한 @supports

  @supports zzz nonsense { .g4 { color: #b91c1c } }
  .g5 { color: #15803d }

    cssRules 에 그 @supports 가 '없다'        at-rule 단위 폐기 (07번)
    .g4 = rgb(0, 0, 0)     안 먹음
    .g5 = rgb(21, 128, 61) 살아남음           회복 지점은 짝 맞는 '}'
```

### 어디서 헷갈리나

- **괄호를 빼먹지 않는다.** `@supports display: grid` 는 무효다. `CSS.supports` 의 두 인자 형태에서만 괄호가 없다.
- **`@supports` 는 조건이지 우선순위가 아니다.** 명시도는 그대로다.
- **`selector()` 질의는 관대하지 않다.** 결과를 그대로 믿지 않는다.
- **커스텀 속성·`var()` 질의는 항상 참**이다. 게이트로 쓸 수 없다.
- **조건이 거짓인 `@supports` 는 버려지지 않는다.** `cssRules` 에 남는다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `CSS.supports('selector(...)')` 의 `false` 를 그대로 믿는다

실측에서 `selector(:is(.a, ::zzbogus))` 가 **`false`** 인데 같은 선택자를 쓴 규칙은 **정상 동작**했고,\
시트의 `selectorText` 는 **`:is(.f14) span`** 으로 **이상한 인자만 지워져** 있었다.\
질의는 **관대하지 않은 파싱**을 쓴다. **멀쩡한 기능을 스스로 끄는 자리**다.

### 2. 안 써도 되는 곳에 `@supports` 를 쓴다

선언 하나짜리 폴백은 **오류 복구로 충분하다.** 실측에서 `color: #15803d; color: zzbogus(1)` 가\
`rgb(21, 128, 61)` 로 남았다. `@supports` 로 감싸면 **코드만 늘고 얻는 게 없다.**

### 3. 여러 선언이 맞물리는데 캐스케이드 폴백에 맡긴다

반대 사고다. 실측에서 `display: zzgrid` 만 버려지고 **`grid-template-columns: 1fr 1fr` 은 살아남았다**\
(계산값이 `1fr 1fr` 이었다). `@supports` 로 가른 쪽은 `none` 으로 깨끗했다.\
**「한 줄이 무시돼도 나머지가 성립하는가」** 로 갈린다.

### 4. `@supports not (…)` 로 폴백을 쓴다

아주 오래된 브라우저는 **`@supports` 자체를 모른다.** 그러면 그 블록이 **통째로 버려져**([07번 주제](../07-syntax-and-error-recovery/2-summary.md))\
폴백이 안 걸린다. **폴백은 at-rule 밖에, 향상만 안에** 두는 배치가 안전하다.

### 5. 커스텀 속성을 `@supports` 로 게이트한다

실측에서 `(--x: anything)` 과 `(color: var(--x))` 가 **둘 다 참**이었다.\
「파싱은 된다」와 「지원한다」가 다른데 질의는 앞엣것만 말한다. **게이트가 영영 안 닫힌다.**

### 6. 질의 결과를 Baseline 으로 읽는다

실측에서 `font-tech(color-COLRv1)` 이 **참**인데 webstatus.dev 의 `colrv1` 은 **limited** 다.\
질의는 **이 브라우저 하나**에 대한 답이고, Baseline 은 **여러 브라우저의 집계**다.\
크로스 브라우저 판단은 **Baseline 데이터로만** 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `@supports` 조건이 거짓이어도 규칙이 `cssRules` 에 남는 것 | **명세**(css-conditional) + 관찰 |
| `selector()` 가 관대하지 않은 파싱을 쓰는 것 | **명세**(css-conditional-4 「`selector()`」) |
| `:is()` 가 매칭에서는 관대한 것 | **명세**(selectors-4) |
| 커스텀 속성·`var()` 질의가 항상 참인 것 | **명세**(커스텀 속성은 임의 토큰을 받는다) |
| `@supports` 가 명시도에 영향이 없는 것 | **명세**(css-cascade — 조건부 규칙) |
| 프렐류드가 무효한 `@supports` 가 통째로 버려지는 것 | **명세**(css-syntax-3 오류 복구) |
| `(foo)` 가 거짓인 것(general enclosed) | **명세**(css-conditional) |
| **`selectorText` 가 `:is(.f14) span` 으로 직렬화되는 것** | **명세**(CSSOM 직렬화) + **관찰** |
| **`font-tech(color-COLRv1)` 이 참인 것** | **관찰**(Chrome 151). 다른 브라우저의 답이 아니다 |
| **`at-rule(@container)` 질의가 되는 것** | **관찰**(Chrome 151). Baseline 은 **limited** 다 |
| `CSS.supports('bogus)(')` 가 예외 없이 `false` 인 것 | **명세**(파싱 실패는 false) + 관찰 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 새 값 하나를 점진적으로 쓴다 | 같은 속성 두 줄(구형 먼저) | `@supports`(코드만 는다) |
| 여러 선언이 한 덩어리로 맞물린다 | `@supports` 로 통째로 가르기 | 캐스케이드 폴백(반쪽만 된다) |
| 새 at-rule 을 쓴다 | 기본은 밖에, 향상만 안에 | `@supports not (…)` 에 폴백 담기 |
| 새 선택자를 쓴다 | `:is()` 로 감싸기([11번](../11-is-where-not/2-summary.md)) | `@supports selector(…)` 로 게이트 |
| 커스텀 속성 지원을 묻고 싶다 | (물을 수 없다) `@property` 로 타입을 고정 | `@supports (--x: …)` |
| 웹폰트 포맷 폴백 | `@supports font-format(…)` 또는 `src` 의 `format()` 목록 | 추측 |
| 크로스 브라우저 판단 | **Baseline 데이터** | `CSS.supports` 결과 |
| 「왜 안 먹지」 진단 | `cssRules` → `selectorText` → `getComputedStyle` | `CSS.supports` 한 줄 |

판단 규칙 두 줄.

- **「이 한 줄이 무시돼도 나머지가 성립하는가」** 를 먼저 묻는다. 성립하면 오류 복구에 맡긴다.
- **질의는 진단 도구가 아니라 게이트 도구**다. 진단은 언제나 `cssRules` 부터.

## 핵심 문장

- **`@supports` 는 「이 브라우저가 이 문법을 아느냐」를 묻는다.** 조건이 거짓이어도 규칙은 `cssRules` 에 남는다.
- ★ **`selector()` 질의는 관대하지 않다.** 실측에서 `selector(:is(.a, ::zzbogus))` 가 `false` 인데 **같은 선택자 규칙은 정상 동작**했고 `selectorText` 는 `:is(.f14) span` 으로 인자만 지워져 있었다.
- **CSS 에는 이미 오류 복구가 있어 `@supports` 가 필요한 경우가 적다.** 선언 하나면 같은 속성을 두 줄 쓰면 된다.
- **필요한 것은 「여러 선언이 맞물릴 때」** 다. 실측에서 캐스케이드 폴백은 `grid-template-columns: 1fr 1fr` 를 **남겨 놓았다.**
- **`@supports not (…)` 에 폴백을 담으면 위험하다.** `@supports` 자체를 모르는 브라우저에서 폴백째 사라진다.
- **커스텀 속성·`var()` 질의는 항상 참**이다. 게이트로 쓸 수 없다.
- **`@supports` 는 명시도를 안 바꾼다.** 순서만 바꾼다 — `@media` 와 같다.
- **질의 결과는 이 브라우저 하나의 답**이다. 크로스 브라우저는 Baseline 으로 판단한다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 41번)
- [`../07-syntax-and-error-recovery/2-summary.md`](../07-syntax-and-error-recovery/2-summary.md) — **오류 복구의 정본.**\
  「무엇이 어느 단위로 버려지나」는 거기, 여기는 **「오류 복구로 부족할 때 통째로 가르는 수단」** 만.\
  `CSS.supports('selector(...)')` 가 거짓말하는 것도 거기서 처음 나왔고, **정본은 여기가 맡는다.**
- [`../38-media-queries/2-summary.md`](../38-media-queries/2-summary.md) — 조건부 at-rule 의 문법·논리·명시도 무관성이 거기와 같다.\
  다른 것은 **무엇을 재는가**뿐이다 — 뷰포트 대 **브라우저의 지식**.
- [`../11-is-where-not/2-summary.md`](../11-is-where-not/2-summary.md) — `:is()`·`:where()` 의 명시도와 너그러운 목록.\
  **매칭의 관대함**이 거기, **질의의 비관대함**이 여기.
- [`../01-cascade-and-priority/2-summary.md`](../01-cascade-and-priority/2-summary.md) — 캐스케이드 6단계.\
  `@supports` 가 **등장 순서**에만 작용하는 근거.
- [`../14-css-nesting/2-summary.md`](../14-css-nesting/2-summary.md) — 규칙 안에 `@supports` 를 넣을 수 있게 된 근거(실측: `& .h5` 로 펼쳐진다).
- [`../37-at-property/2-summary.md`](../37-at-property/2-summary.md) — 커스텀 속성에 타입을 붙이는 쪽. `@supports` 로 못 묻는 것을 거기서 고정한다.
- [`../40-container-and-style-queries/2-summary.md`](../40-container-and-style-queries/2-summary.md) — `CSS.supports('at-rule(@container)')` 가 참인 실측.
- [목록의 **36번 주제**](../36-custom-properties/)(사용자 정의 속성) — `(--x: anything)` 이 항상 참인 이유의 뿌리.

## 용어 풀이

- **`@supports`** — 브라우저의 문법 지원 여부로 규칙을 켜는 조건부 at-rule. 기능 질의라고도 한다.
- **기능 질의(feature query)** — `@supports` 의 조건. 다섯 형태(`(속성:값)`·`selector()`·`font-format()`·`font-tech()`·`at-rule()`)가 있다.
- **관대하지 않은 파싱(non-forgiving parsing)** — 목록 안에 무효한 항이 하나라도 있으면 전체를 무효로 보는 파싱. `selector()` 질의가 이것을 쓴다.
- **너그러운 선택자 목록(forgiving selector list)** — `:is()`·`:where()` 의 인자 목록. **매칭에서만** 관대하다.
- **general enclosed** — `(foo)` 처럼 뜻을 모르는 괄호 조건. 파싱은 되고 평가는 **항상 거짓**이다.
- **점진적 향상(progressive enhancement)** — 기본은 at-rule 밖에, 향상만 안에 두는 배치.
- **`CSS.supports()`** — 같은 질의를 JS 에서 하는 API. 두 인자 형태와 조건 문자열 형태가 있다.
- **`CSSSupportsRule`** — `@supports` 의 CSSOM 타입. `conditionText` 를 읽을 수 있다.
- **Baseline** — 여러 브라우저의 지원을 집계한 것. **질의 결과와 다른 이야기**다.

## 더 들어가면

- **`@supports` 가 늦게 나온 이유**는 CSS 에 이미 오류 복구가 있었기 때문이다. 대부분의 폴백이 「같은 속성을 두 줄」로 해결되니 급하지 않았고, **여러 선언이 맞물리는 레이아웃**(flex → grid)이 등장하고서야 필요가 커졌다.
- **`@supports` 로 브라우저를 식별하려는 시도**가 있다(`@supports (-webkit-touch-callout: none)` 으로 Safari 고르기 같은 것). 지원하는 것을 묻는 게 아니라 **지원 조합으로 신원을 추정**하는 것이라, 브라우저가 그 속성을 정리하는 순간 깨진다.
- **`@font-face` 의 `src` 목록은 `@supports` 없이도 자체 폴백이 된다.**
  실측(로컬 HTTP 서버 로그): `src: url("f.zzfmt") format("zzbogus"), url("f.woff2") format("woff2")` 를 주자
  브라우저가 **`f.zzfmt` 는 요청조차 안 하고 `f.woff2` 만 `200` 으로 받아 갔다.**
  모르는 `format()` 을 만나면 그 항목을 건너뛴다 — **네트워크도 안 쓴다.**
  `font-format()` 질의는 **그보다 큰 덩어리**(폰트 종류를 통째로 갈아 끼우는 것)를 가를 때 쓴다.
- **`at-rule()` 질의는 Baseline limited 인데 Chrome 151 은 지원한다**(실측: `at-rule(@container)` 가 `true`, `at-rule(@zzbogus)` 가 `false`). **「지원 여부를 묻는 기능 자체의 지원 여부」** 를 먼저 물어야 하는 순환이 있고, 그래서 널리 쓰기에는 아직 이르다.
