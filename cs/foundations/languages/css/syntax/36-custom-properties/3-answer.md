# css/syntax/36 — 사용자 정의 속성: 선언·`var()`·대체값·상속 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 실제로 렌더해 네 창으로 읽은 것**이다 —
> `cssRules[i].style`(담긴 선언 목록) · `cssRules[i].style.getPropertyValue('--x')`(담긴 변수 값) ·
> `getComputedStyle(el).getPropertyValue('--x')`(변수의 계산값) · `getComputedStyle(el).<속성>`(쓰는 쪽의 계산값).\
> **손으로 계산해 유도한 값은 없다.** 규칙은 [css-variables-1](https://drafts.csswg.org/css-variables-1/) 과 [css-cascade-5](https://drafts.csswg.org/css-cascade-5/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 오타가 난 변수는 어디서 죽는가

**실행 결과** (부모 `#p` 는 `color: green`)

```text
  ①   cssRules 속성 목록              = [--x, color, background-color]   ★ 셋 다 담겼다
  ①-b cssRules 의 --x                 = "redd"
  ③-b getComputedStyle 의 --x         = "redd"
  ③   getComputedStyle 의 color       = rgb(0, 128, 0)   <- 부모 green
  ③   getComputedStyle 의 background  = rgb(253, 230, 138)  <- 멀쩡하다

  대조군 (같은 부모 아래)
  color: unset    -> rgb(0, 128, 0)   ★ 일치한다
  color: initial  -> rgb(0, 0, 0)     ★ 다르다
```

**왜 그런가**

- **`cssRules` 목록에 셋 다 들어 있다.** 선언은 하나도 안 버려졌다.
- **`--x` 의 계산값은 `"redd"`** 다. 파서가 커스텀 속성의 값을 **검사하지 않기** 때문이다 — 뜻은 쓰는 쪽이 정한다.
- **`color` 는 `unset` 과 같다.** 대조군이 결정적이다 — `unset`(green)과 일치했고 `initial`(검정)과는 달랐다.\
  즉 **IACVT 는 `initial` 이 아니라 `unset`** 이다. `color` 는 상속 속성이라 **부모 값**이 나왔다.
- **`background-color` 는 살아 있다** — 규칙째 죽은 게 아니라 **`var()` 를 쓴 그 선언만** 무효가 됐다.
- **보통 속성과의 차이** — `color: redd` 는 [07번](../07-syntax-and-error-recovery/2-summary.md)의 규칙대로 **선언 하나가 버려진다**(`cssRules` 목록에서 사라진다).\
  커스텀 속성은 **선언이 살아남고 쓰는 쪽이 초기화된다.** 「무엇이 버려지느냐」가 반대편이다.

### 2. 앞선 선언으로 돌아가는가

**실행 결과** (부모 색 검정인 판)

```text
  #d { --x: redd; color: red; color: var(--x) }
     computed color = rgb(0, 0, 0)     <- 상속된 검정. red 가 아니다
```

**왜 그런가**

- **red 로 돌아가지 않는다.** 상속값(또는 초기값)이 된다.
- 순서가 이렇다 — ① 캐스케이드가 **뒤에 온 `color: var(--x)` 를 승자로 뽑는다** ② **그 뒤에** 계산 시점에 무효가 된다.\
  진 선언(`color: red`)은 **그 시점에 이미 버려진 뒤**라 돌아갈 곳이 없다.
- **시사점** — `color: red; color: var(--maybe)` 형태의 **점진적 향상이 커스텀 속성에서는 성립하지 않는다.**\
  보통 속성이라면 뒤 선언이 무효일 때 파서가 그것을 버려 앞 선언이 살아남는데, `var()` 는 파싱을 통과하므로 그 보호막이 없다.

### 3. ★ 대체값은 언제 쓰이나

**실행 결과** (부모 색을 purple 로 두어 「대체값」과 「상속」을 갈랐다)

```text
  선언                                  계산된 color       대체값이 쓰였나
  ------------------------------------  -----------------  --------------
  color: var(--none, green)             rgb(0,128,0)       ★ 쓰였다
  --x: redd;  color: var(--x, green)    rgb(128,0,128)     ★ 안 쓰였다 (부모 purple)
  --x: redd;  color: var(--x)           rgb(128,0,128)     (대체값 없음)

  부모 색이 검정인 별도 판
  color: red; color: var(--nope)        rgb(0,0,0)         (대체값 없음)
  color: red; color: var(--nope, green) rgb(0,128,0)       ★ 쓰였다
  --empty: ;  color: var(--empty, teal) rgb(0,0,0)         ★ 안 쓰였다
```

**왜 그런가**

- **대체값이 실제로 쓰인 것은 `#c`(`var(--nope, green)`)** 하나다.
- 판정 순서가 이렇다.

```text
    --x 가 아예 없나? (또는 '보장된 무효' 인가)
        ├─ 예  ──> 대체값을 그 자리에 펼친다
        └─ 아니오 ──> --x 의 토큰 뭉치를 펼친다
                          │
                          v
                     펼친 결과가 그 속성 문법에 안 맞나?
                          └─ 예 ──> ★ IACVT. 대체값은 쓰이지 않는다
```

- ★ **`#k`(`--empty: ;`)가 결정적인 근거다.** 빈 값도 **엄연히 존재하는 값**이라 「없나?」에서 통과하고, 펼친 결과 `color: ` 가 무효가 되어 IACVT 로 떨어졌다(teal 이 아니라 검정).\
  「무효하니까 대체값이 쓰이겠지」가 사실이라면 teal 이 나와야 했다.
- **그래서 「대체값을 넣어 두면 오타가 막힌다」는 틀리다.** 대체값은 **「이 변수를 안 준 사용자」를 위한 기본값**이지 오타 방어막이 아니다.

### 4. 대체값 안의 쉼표

**실행 결과**

```text
  border: var(--brd, 1px solid red)                 -> 1px solid rgb(255,0,0)
  --sp: 1px solid red;  border: var(--sp)           -> 1px solid rgb(255,0,0)
  font-family: var(--ff, "Courier New", monospace)  -> "Courier New", monospace
  color: var(--p, var(--q, teal))                   -> rgb(0,128,128)
```

**왜 그런가**

- **셋 다 동작한다.**
- 자르는 규칙 — **`var()` 의 인자는 「이름」과 「대체값」 둘뿐**이고, **첫 쉼표만 구분자**다.\
  그 뒤에 쉼표가 몇 개 더 있든 **전부 하나의 대체값**으로 읽는다.
- 그래서 `var(--ff, "Courier New", monospace)` 의 대체값은 **`"Courier New", monospace` 통째로**다.
- 공백을 품은 값도 같은 이유로 들어간다(`1px solid red`).
- **중첩도 된다** — `var(--p, var(--q, teal))` 로 「둘 다 없으면 teal」이 표현됐다.

### 5. ★ 순환 참조를 던져 본다

**실행 결과** (부모 `#p` 는 `color: green`)

```text
  선언                                                  --a(--s) 계산값   color
  ----------------------------------------------------  ---------------  --------------
  --a: var(--b); --b: var(--a); color: var(--a)         ""               rgb(0,128,0)
                                                                          = 부모 상속
  --a: var(--b); --b: var(--a); color: var(--a, purple) ""               rgb(128,0,128)
  --s: var(--s);                color: var(--s, navy)   ""               rgb(0,0,128)
```

**왜 그런가**

- **세 경우 모두 계산값이 빈 문자열**이다. 순환에 걸린 변수는 「**보장된 무효(guaranteed-invalid)**」가 된다.
- **대체값이 있는 쪽은 대체값이 쓰였다**(purple · navy). 보장된 무효는 **질문 3의 첫 갈래 — 「아예 없나?」에 해당**하기 때문이다.
- **대체값이 없으면** `var()` 자체가 무효가 되어 **IACVT → 부모 색 상속**(green)이 됐다.
- **자기 참조도 순환으로 처리된다** — `--s: var(--s)` 는 한 칸짜리 고리다.
- **에러는 나지 않는다.** 콘솔도 화면도 조용하고, **값이 빈 문자열인지 읽어 봐야** 안다.
- 그래서 순환이 생겨도 화면이 **「그럴듯하게」 보일 수 있다** — 대체값이 대신 들어가기 때문이다.

### 6. ★ 대소문자를 가리는가

**실행 결과**

```text
  #e { --X: blue; color: var(--x, orange) }
     computed --X   = "blue"
     computed --x   = ""                 <- 없다
     computed color = rgb(255,165,0)     = orange   ★ 대체값이 쓰였다

  공백 보존
  --ws:    hello   world   ;
     cssRules  = "hello   world"
     computed  = "hello   world"         ★ 앞뒤만 잘리고 가운데는 보존
```

**왜 그런가**

- **`color` 는 orange** 다. `--X` 를 선언했지만 `--x` 는 여전히 없으므로 대체값이 쓰였다.
- **커스텀 속성 이름은 대소문자를 가린다** — `--X` 와 `--x` 는 **서로 다른 속성**이다.
- **보통 속성 이름은 대소문자를 무시한다**(`COLOR: red` == `color: red`). CSS 안에서 이 둘만 규칙이 다르다.
- **`--ws` 의 계산값은 정확히 `"hello   world"`** 다 — 앞뒤 공백은 잘리고 **가운데 공백 세 칸은 그대로** 보존됐다.\
  값이 「해석된 결과」가 아니라 **토큰 뭉치 그대로**임을 보여 준다.
- 관행은 **전부 소문자 + 하이픈**(`--main-color`)이다 — 대소문자 사고를 원천 차단한다.

### 7. ★ 무엇이 상속되는가 — 토큰인가 값인가

**실행 결과**

```text
  #tp { font-size: 20px; text-indent: 2em; --len: 2em }
     └ #tc { font-size: 40px; width: var(--len) }

  보통 속성 text-indent                     커스텀 속성 --len
  --------------------------------------    --------------------------------------
  #tp 계산값 = 40px                         #tp 계산값 = "2em"   ★ px 이 안 됐다
  #tc 상속값 = 40px                         #tc 계산값 = "2em"   ★ 글자 그대로
                                            #tc 의 width: var(--len) = ★ 80px

  사슬 실측
  --a: 10px; --b: var(--a); --c: calc(var(--b) * 3);  width: var(--c)
     computed --c = "calc(10px * 3)"     ★ calc 가 계산되지 않은 채 남았다
     computed width = 30px               (쓰는 쪽에서 비로소 계산됐다)
```

**왜 그런가**

- **`text-indent` 는 부모에서 40px, 자식도 40px** 이다. 보통 속성은 **부모 자리에서 계산값이 확정되고 그 픽셀이 내려간다**([04번](../04-value-processing-stages/2-summary.md)).
- **`--len` 은 부모·자식 모두 `"2em"`** 이다. 커스텀 속성의 계산값은 **토큰 뭉치 그대로**다.
- **`#tc` 의 `width` 는 80px** 이다 — 자식이 `var(--len)` 으로 꺼낼 때 **자식의 글꼴 40px** 로 `2em` 을 풀었기 때문이다.\
  같은 판에서 `text-indent` 는 자식 글꼴이 두 배가 됐는데도 **40px 그대로**였다. **한 판에서 두 규칙이 갈린 것**이 근거다.
- **`--c` 의 계산값 문자열은 `"calc(10px * 3)"`** 이다. `var()` 는 펼쳐졌는데 **`calc()` 는 계산되지 않았다.**\
  쓰는 쪽(`width`)에서 비로소 30px 이 됐다.
- 이 성질이 **디자인 토큰 설계의 근거**다 — 한 번 선언해 두면 **각 자리에서 그 자리 맥락으로** 풀린다.

### 8. ★ 두 조상이 같은 변수를 선언하면

**실행 결과**

```text
  [거리 대조]
  .far { --tone: red } > #near { --tone: blue } > #leaf { color: var(--tone) }
     #leaf 의 --tone = "blue"   color = rgb(0,0,255)

  [명시도 대조]
  #hi { --tone2: red } > .lo { --tone2: blue } > #leaf2 { color: var(--tone2) }
     #leaf2 의 --tone2 = "blue"  color = rgb(0,0,255)   ★ ID 조상이 졌다
```

**왜 그런가**

- **두 경우 다 파랑**이다. **가까운 조상이 이겼다.**
- **`#hi` 가 지는 이유** — 두 선언이 **같은 요소에 걸려 있지 않다.**

```text
    #hi  { --tone2: red }    <- #hi 라는 '요소' 의 --tone2 를 정한다 (여기선 red 가 맞다)
      │  상속
    .lo  { --tone2: blue }   <- .lo 라는 '요소' 의 --tone2 를 정한다
      │                          ★ 상속받은 red 를 자기 선언 blue 가 덮는다
      v  상속
    #leaf2                   <- 부모 .lo 의 계산값 "blue" 를 물려받는다
```

- **명시도는 「한 요소에 걸린 여러 선언」 중에서 고르는 규칙**이다([02번](../02-specificity/2-summary.md)). 조상 둘이 각각 자기에게 선언한 것은 겨룰 자리가 없다.
- 커스텀 속성은 **전부 상속되므로**([03번](../03-inheritance-and-global-keywords/2-summary.md)) 규칙이 캐스케이드가 아니라 **상속**이다.
- **실무에서 가능하게 하는 것** — 「구역만 테마 바꾸기」다. 컴포넌트 규칙은 한 줄도 안 건드리고, **바꿀 구역의 조상에 변수를 다시 선언**하면 그 안쪽만 바뀐다(본문 (8) 의 demo).

### 9. `:root` 관행의 한계

**실행 결과**

```text
  @media (min-width: var(--bp, 100px)) { #mq  { outline: 2px solid red } }
  @media (min-width: 100px)            { #mq2 { outline: 2px solid red } }

     conditionText = "(min-width: var(--bp, 100px))"  · 안쪽 규칙 1개 담김
     conditionText = "(min-width: 100px)"             · 안쪽 규칙 1개 담김

     #mq  의 outline = 3px none      ★ 적용 안 됨
     #mq2 의 outline = 2px solid     적용됨

  #badname { --prop: color; var(--prop): red; width: 30px }
     cssRules 에 담긴 것 = "--prop: color; width: 30px;"
     ★ var(--prop): red 는 통째로 사라졌다 (computed color 는 부모 상속값)
```

**왜 그런가**

- **`:root` 가 전역이 되는 것은 특별한 기능이 아니다.** `:root` = `html` = 모든 요소의 조상이고, 커스텀 속성은 **전부 상속되므로** 한 번 선언하면 문서 전체가 읽는다. 질문 8 의 상속 규칙의 응용일 뿐이다.
- **`@media` 안에서는 동작하지 않는다.** 규칙은 담기고 조건 문자열도 보존되는데, **조건이 참이 되지 않았다**(outline none).\
  이유 — 미디어 쿼리는 **문서 트리 바깥**에서 평가되는데, 커스텀 속성은 **요소에 붙어 상속되는 것**이라 거기에 없다.
- **속성 이름 자리에서는 선언이 통째로 사라진다.** `var()` 는 **속성 「값」 자리에서만** 산다.
- 그래서 실무 관행은 **두 층**이다 — 전역 토큰은 `:root`, 구역 테마는 그 구역의 조상에 다시 선언.

### 10. 이름 규칙과 JS

**실행 결과**

```text
  한 규칙에 다섯 형태를 적고 cssRules 를 찍었다
     적은 것         담겼나   계산값
     --------------  -------  ----------
     --: 1px         ✗        —          이름이 비어 있다
     --1: red        ✓        "red"      ★ 숫자로 시작해도 된다
     --가나: blue    ✓        "blue"     ★ 비ASCII 도 된다
     --a-b_c: green  ✓        "green"
     -x: red         ✗        —          ★ 하이픈 하나는 벤더 자리다

     꺼내 써도 된다:  var(--가나) -> rgb(0,0,255)  ·  var(--1) -> rgb(255,0,0)

  JS  (#js { --j: 5px; width: var(--j) })
     getComputedStyle(el).getPropertyValue('--j') = "5px"
     el.style.getPropertyValue('--j')             = ""
     el.style.setProperty('--j','120px')  -> cssText "--j: 120px;"  width 120px  ★ 된다
     el.style['--j'] = '9px'              -> width 그대로 (auto)               ★ 안 된다
     el.style.setProperty('--j','oops')   -> --j "oops"  width auto (IACVT)
```

**왜 그런가**

- **인정되는 것은 `--1`·`--가나`** 다(그리고 `--a-b_c`). `--`(이름 없음)와 `-x`(하이픈 하나)는 커스텀 속성이 아니라 **선언이 버려졌다.**
- 이름 문법은 **`--` 두 개 + 한 글자 이상**이면 되고, 보통 식별자보다 훨씬 관대하다.
- **JS 로 쓸 때는 `setProperty` 만 통한다.** `el.style['--j'] = …` 는 **조용히 무시됐다** — 카멜케이스 프로퍼티 접근의 매핑 대상이 아니다.
- **두 읽기 창의 차이** — `getComputedStyle` 은 **상속까지 반영한 계산값**(`"5px"`), `el.style` 은 **그 요소의 인라인 선언만**(빈 문자열)이다.
- **JS 로 넣은 오타도 똑같이 IACVT** 다 — 값은 `"oops"` 로 담기고 `width` 만 `auto` 가 됐다.

### 11. ★ 애니메이션

**실행 결과** (10초 linear, 네 시점 샘플링)

```text
  시점       --w        width      (색 애니메이션) --c     color
  ---------  ---------  ---------  ----------------------  ----------------
  2s (20%)   "0px"      0px        "red"                   rgb(255,0,0)
  4s (40%)   "0px"      0px        "red"                   rgb(255,0,0)
  6s (60%)   "200px"    200px      "blue"                  rgb(0,0,255)
  9s (90%)   "200px"    200px      "blue"                  rgb(0,0,255)

  대조군 — 보통 속성 width 를 같은 조건으로
  5s 시점 width = 99.3281px       ★ 중간값이 나온다
```

**왜 그런가**

- **2·4초 0px, 6·9초 200px** 이다.
- ★ **「안 움직인다」는 정확하지 않다.** 정확한 서술은 「**이산(discrete) 보간이 되어 50% 지점에서 한 번 튄다**」다.
- 색도 같았다 — `--c` 가 red 에서 blue 로 **중간색 없이** 넘어갔다.
- **대조군이 결정적이다** — 같은 타이밍에 보통 `width` 는 **99.3281px** 이라는 중간값을 냈다.
- 이유 — 등록하지 않은 커스텀 속성의 **계산값 타입**이 「**토큰 뭉치**」다. 두 토큰 뭉치 사이의 「중간 문자열」은 정의되지 않으므로 보간할 방법이 없다.
- **푸는 기능은 `@property` 등록**이다. `syntax: '<length>'` 로 등록하면 계산값 타입이 길이가 되어 보간이 가능해진다.\
  정본은 [목록의 **37번 주제**](../37-at-property/)이고 **이 문서에서는 등록 쪽을 재지 않았다.**

### 12. 다른 주제로 잇기

- **보통 속성의 무효 값이 선언째 버려지는 규칙** — [07번](../07-syntax-and-error-recovery/2-summary.md)(CSS 구문과 오류 복구)이 정본이다. 이 편은 **커스텀 속성이 그 규칙을 따르지 않는다**는 차이를 푼다.
- **`unset` 이 무엇인가** — [03번](../03-inheritance-and-global-keywords/2-summary.md)(상속과 전역 키워드)이 정본이다. 커스텀 속성이 **전부 상속된다**는 예외도 거기서 선언된다.
- **명시도가 같은 요소의 선언끼리만 겨룬다** — [02번](../02-specificity/2-summary.md)(명시도).
- **CSS 에 변수가 들어온 경위** — [`history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) §2.7 이 정본이다. 이 편은 오늘의 규칙만 다룬다.

## 용어 풀이

- **커스텀 속성(custom property)** — `--` 로 시작하는 속성. 값이 파싱 시점에 해석되지 않고 토큰 뭉치로 보관된다.
- **토큰 뭉치(token stream)** — 뜻을 해석하지 않고 글자 단위로만 잘라 둔 값. 예: `--ws:  hello   world  ` 의 계산값이 `"hello   world"` 로 가운데 공백까지 보존됐다.
- **`var()`** — 커스텀 속성을 그 자리에 **펼치는** 함수. 값을 대입하는 게 아니라 토큰을 밀어 넣는다.
- **대체값(fallback)** — `var(--x, 여기)` 의 둘째 인자. **변수가 없거나 보장된 무효일 때만** 쓰인다. 예: `--empty: ;` 에서는 안 쓰였다.
- **IACVT(invalid at computed-value time)** — 파싱은 통과했는데 계산 시점에 무효가 되는 값. `unset` 처럼 처리된다. 예: 실측에서 부모의 green 을 상속했고 `initial`(검정)과 달랐다.
- **`unset`** — 상속되는 속성이면 `inherit`, 아니면 `initial` 로 되돌리는 전역 키워드. 정본은 [03번](../03-inheritance-and-global-keywords/2-summary.md).
- **보장된 무효(guaranteed-invalid)** — 커스텀 속성의 초기값이자 순환에 걸린 변수의 상태. 이 상태를 `var()` 로 꺼내면 **대체값이 쓰인다**.
- **순환 참조** — 변수 둘 이상이 서로를 가리키는 것. 예: `--a: var(--b); --b: var(--a)` 의 계산값이 둘 다 빈 문자열이었다.
- **이산 보간(discrete interpolation)** — 중간값 없이 50% 지점에서 한 번에 바뀌는 보간. 예: `--w` 가 40% 까지 `0px`, 60% 부터 `200px` 이었다.
- **진단 3창** — `cssRules` · `querySelectorAll` · `getComputedStyle`. 커스텀 속성에서는 **변수 값을 읽는 창 두 개**를 더 연다(A1).

## 실행 검증

| 무엇을 | 어떻게 | 결과 |
|---|---|---|
| IACVT 의 네 창 | Chrome 151 headless · `cssRules[i].style` + `getComputedStyle` | 목록 `[--x, color, background-color]` · `--x` `"redd"` · color 는 부모 green |
| IACVT = `unset` 인 것 | 같은 부모 아래 `unset`·`initial` 대조군 | unset 과 일치(green), initial 과 불일치(검정) |
| 비상속 속성의 IACVT | 부모 background green 아래 `background-color: var(--x)` 대 `unset` | 둘 다 `rgba(0,0,0,0)` |
| 앞선 선언으로 안 돌아가는 것 | `color: red; color: var(--x)`(`--x` 무효) | 검정(상속) — red 아님 |
| ★ 대체값이 「없을 때」만 쓰이는 것 | 부모 purple 판에서 `var(--x, green)` 대 `var(--none, green)` | purple 대 green |
| `--empty: ;` | `var(--empty, teal)` 의 계산값 + `--empty` 계산값 | 검정(teal 아님) · `""` |
| 대체값의 쉼표·공백·중첩 | `border`·`font-family`·`var(var())` 세 형태 | 셋 다 동작 |
| ★ 순환 참조 | 상호 참조 + 자기 참조, 대체값 있음/없음 4형태 | 계산값 `""` · 대체값 있으면 purple/navy, 없으면 상속 |
| ★ 대소문자 | `--X: blue` 선언 후 `--x`·`--X` 를 따로 읽기 | `--X` `"blue"` / `--x` `""` / color orange |
| 공백 보존 | `--ws:    hello   world   ;` 의 담긴 값·계산값 | 둘 다 `"hello   world"` |
| ★ 토큰 뭉치 상속 | 같은 판에서 `text-indent: 2em` 과 `--len: 2em` 대조 | 40/40px 대 `"2em"`/`"2em"`, 자식 width **80px** |
| `calc` 가 안 접히는 것 | `--c: calc(var(--b) * 3)` 의 계산값 문자열 | `"calc(10px * 3)"`, width 30px |
| ★ 가까운 조상이 이기는 것 | 거리 대조 + 명시도 대조(ID 조상 대 클래스 조상) | 둘 다 파랑 — ID 조상이 졌다 |
| `!important` | `--i: red` 를 `--i: blue !important` 로 덮기 | blue |
| `:root` 의 한계 ① | `@media (min-width: var(--bp,100px))` 의 `conditionText` + 적용 여부 | 담김 · **적용 안 됨** |
| `:root` 의 한계 ② | `var(--prop): red` 를 적고 `cssRules` 확인 | 선언 통째로 사라짐 |
| 이름 규칙 5형태 | `--` · `--1` · `--가나` · `--a-b_c` · `-x` | 가운데 셋만 담김 |
| JS 읽기/쓰기 | `setProperty` 대 `el.style['--j']`, 두 읽기 창 | setProperty 만 동작 |
| 테마 전환 | `documentElement.style.setProperty('--brand', …)` | `rgb(37,99,235)` → `rgb(220,38,38)` |
| ★ 애니메이션 | 10초 linear 를 2·4·6·9초에 샘플링 + 보통 `width` 대조군 | 50% 에서 튐 · 대조군은 5초에 99.3281px |
| 값 조립 | `--a: 10; --b: px; width: var(--a)var(--b)` | 무효 → auto |
| 인라인 스타일 | `style="--il: crimson; color: var(--il)"` | `rgb(220,20,60)` |
| `content` | `::before { --t: "hi"; content: var(--t) }` | `"hi"` |
| `--t: initial` 로 상속 끊기 | 부모 `--t: red`, 자식 `--t: initial; color: var(--t, navy)` | navy · `--t` `""` |
| demo 2개 | `extract-demo-blocks.py --render` 로 문서에서 재추출해 재실행 | 「보이는 것」 2건 모두 일치 |

**재지 않은 것** — `@property` 로 등록했을 때 달라지는 것 전부([목록의 **37번 주제**](../37-at-property/)).\
**구현 의존 항목** — ① `--empty` 의 계산값이 `""` 로 보이는 것 ② `--c` 가 `"calc(10px * 3)"` 으로 보이는 것(접기 범위는 구현 재량) ③ `el.style['--x']` 가 안 먹는 것. **Chrome 151 에서 관찰한 것**이고 브라우저가 바뀌면 다시 찍어야 한다.\
**엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 이 머신에 없다 — **「두 엔진에서 확인했다」고 적지 않았다.**
