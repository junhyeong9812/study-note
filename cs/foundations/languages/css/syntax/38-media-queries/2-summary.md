# css/syntax/38 — 미디어 쿼리: 문법·범위 구문·논리 연산 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Media Queries Level 4](https://drafts.csswg.org/mediaqueries-4/) 의 「Media Query Syntax」·「Range Context」·「Evaluating Media Queries」 절과 [Media Queries Level 5](https://drafts.csswg.org/mediaqueries-5/) 의 사용자 선호 기능 목록. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 값은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 읽은 것이다. **뷰포트 폭은 `--window-size=W,H` 를 바꿔 가며 잰다** — 경계값은 **599 · 600 · 601 을 각각 따로 띄워** 찍었다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — CSS 에 언어 버전은 없다. 미디어 쿼리 자체는 Baseline **widely**(2015-07-29 → 2018-01-29), **범위 구문**(`(400px <= width <= 700px)`)은 Baseline **widely**(newly 2023-03-27 → widely 2025-09-27) — `api.webstatus.dev` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**미디어 쿼리는 「이 스타일을 **언제** 켤 것인가」를 뷰포트에 대고 재는 자다.**

옷장에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 창밖 날씨를 본다 | **뷰포트**(브라우저 창의 보이는 영역)를 잰다 |
| 「영하면 패딩」 | `@media (max-width: 600px) { … }` |
| 온도계가 가리키는 눈금 | `width`·`height`·`orientation` 같은 **미디어 기능** |
| 창밖을 봤는데 못 알아보는 계기판 | **모르는 기능** — 읽지 않고 **거짓**으로 친다 |
| 패딩을 옷장에서 꺼낸 것뿐, 서열이 오른 건 아니다 | **명시도가 안 오른다.** 순서만 바뀐다 |
| 창문이 아니라 **방 크기**를 재는 자 | **컨테이너 쿼리** — 이 주제가 아니라 [40번](../40-container-and-style-queries/2-summary.md) |

- **미디어 쿼리가 재는 것은 언제나 뷰포트(또는 출력 장치)다.** 부모 상자가 아무리 좁아도 안 본다.\
  이 하나가 **38 ↔ 40 의 전부**다.

```text
   미디어 쿼리 (38)                        컨테이너 쿼리 (40)
   +-------------------------------+       +-------------------------------+
   |  +-------------------------+  |       |  +-------------------------+  |
   |  |  조상 상자 300px        |  |       |  |  조상 상자 300px  <--- 이|  |
   |  |   +------------------+  |  |       |  |   +------------------+  |  |
   |  |   | .card            |  |  |       |  |   | .card            |  |  |
   |  |   +------------------+  |  |       |  |   +------------------+  |  |
   |  +-------------------------+  |       |  +-------------------------+  |
   +-------------------------------+       +-------------------------------+
     ^ 뷰포트 1200px  <--- 이걸 잰다         뷰포트는 안 본다
     .card 는 "넓은 화면" 으로 판정된다       .card 는 "좁은 상자" 로 판정된다
```

- ★ **at-rule 은 버려지지 않는다.** 조건이 거짓인 `@media` 도 시트에 **멀쩡히 담겨 있다**([07번 주제](../07-syntax-and-error-recovery/2-summary.md) 실측).\
  그래서 이 묶음에는 진단 창이 하나 더 있다 — **`matchMedia(…)` 로 조건만 따로 평가**하는 것.

```text
  진단 3창 (07번 정본)                       at-rule 의 4번째 창
  ------------------------------------      -------------------------------
  cssRules           규칙이 담겼나           matchMedia("(…)").matches
  querySelectorAll   선택자가 잡았나              조건이 참인가
  getComputedStyle   캐스케이드에서 이겼나    CSSMediaRule.media.mediaText
                                                 파서가 이해한 조건 문자열
```

실무에서 이게 터지는 자리는 **중단점을 `max-width: 600px` 과 `min-width: 600px` 으로 잡았을 때**다.\
**정확히 600px 에서 둘 다 참**이 되어 겹치는데, 화면을 대충 늘였다 줄였다 해서는 **그 1픽셀을 못 본다.**

> **뷰포트(viewport)** — 문서가 그려지는 창의 보이는 영역. 스크롤바를 뺀 폭이다.\
> 예: 실측에서 창 폭 `800` 짜리 문서가 세로로 넘치자 `documentElement.clientWidth` 가 `785` 가 됐다 — 스크롤바 15px 만큼 줄어든다.

> **미디어 기능(media feature)** — 괄호 안에서 묻는 한 가지. `width`·`orientation`·`hover` 등.\
> 예: `(min-width: 600px)` 의 기능은 `width` 이고, `min-` 은 「이상」이라는 접두다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **경계는 어느 쪽에 포함되는가.** `max-width: 600px` 과 `min-width: 600px` 은 600 에서 어떻게 되는가.
2. **모르는 것을 만나면 어떻게 되는가.** 버려지는가, 거짓이 되는가 — 그 둘을 어떻게 가르는가.
3. **미디어 쿼리는 캐스케이드에서 무엇을 바꾸는가.** 명시도인가 순서인가.

## 동작 방식

### (1) ★ 조건이 거짓인 `@media` 는 버려진 게 아니다

**언제 쓰나** — 「미디어 쿼리를 썼는데 안 먹는다」를 진단하는 모든 자리. **이 절을 먼저 세워야 나머지가 읽힌다.**

```text
실측 — 오타·미지원을 섞은 @media 열여섯 규칙을 담고 cssRules 를 세었다

  cssRules.length = 16          <- 하나도 안 사라졌다

  담긴 CSSMediaRule 의 conditionText (파서가 이해한 그대로)
    (totally-unknown-zz: 1)
    (min-width: bogus)
    not all and (min-width: 1px)
    screen and (min-width: 1px)
    tv and (min-width: 1px)
    (min-width: 99999px), (min-width: 1px)
    ((min-width: 99999px) or (min-width: 1px))
    (min-width: 1px) and (max-width: 99999px)
    …
```

```text
   "안 담겼다"                              "담겼는데 조건이 거짓"
   +-----------------------------+          +-----------------------------+
   | cssRules 에 규칙이 없다     |          | cssRules 에 규칙이 있다      |
   |   -> 문법이 틀렸다           |          |   -> 문법은 맞다            |
   |   고칠 곳: 문법             |          |   고칠 곳: 조건 또는 환경    |
   +-----------------------------+          +-----------------------------+
     모르는 at-rule(@zzz)이 이쪽              모르는 미디어 기능이 이쪽
```

그림 해설 (한 단계씩):

- **`@media` 는 브라우저가 아는 at-rule** 이므로 조건이 무엇이든 블록째 담는다.
- **안에 모르는 기능이 있어도 안 버린다** — 「**조건이 거짓**」이 될 뿐이다.
- 그래서 진단은 `cssRules` 다음에 **`matchMedia(조건).matches` 를 한 번 더** 본다.
- ★ `conditionText` 는 **내가 쓴 글자가 아니라 파서가 이해한 형태**다. `(min-width: bogus)` 처럼 뜻 없는 것도 **원형 그대로** 남는다 — 파서가 「기능 이름 + 값」 모양만 보고 통과시켰다는 뜻이다.

비용 — 없음. 다만 「버려졌다」와 「거짓이다」를 섞어 말하면 **`@supports` 로 고칠 문제를 문법 문제로 오진**한다.

### (2) ★★ 경계값 — `max-width: 600px` 과 `min-width: 600px` 은 600 에서 둘 다 참이다

**언제 쓰나** — 중단점을 설계할 때마다. **가장 많이 당하는 자리다.**

같은 문서를 **창 크기만 바꿔** 세 번 띄웠다.

```text
실측 — --window-size=W,400 을 599 / 600 / 601 로 바꿔 각각 띄웠다
       (이 문서는 넘치지 않아 스크롤바가 없었다 — innerWidth = documentElement.clientWidth)

  뷰포트                                599      600      601
  ------------------------------------  -------  -------  -------
  (max-width: 600px)                    참       참       거짓
  (min-width: 600px)                    거짓     참       참
  (width <= 600px)                      참       참       거짓
  (width >= 600px)                      거짓     참       참
  (width: 600px)                        거짓     참       거짓
  (400px <= width <= 700px)             참       참       참
```

```text
   수직선으로 보면

     598   599   600   601   602
   ---+-----+-----+-----+-----+--->
      |<---- max-width: 600px ---|
                    |---- min-width: 600px ---->
                    ^^^
                    여기서 겹친다 — 둘 다 참인 1픽셀
```

그림 해설 (한 단계씩):

- `min-`/`max-` 는 「**이상**」·「**이하**」다. 「초과」·「미만」이 아니다.\
  그래서 **같은 숫자를 쓰면 반드시 겹친다.**
- 겹치는 구간에서는 **캐스케이드의 마지막 단계(등장 순서)** 가 승자를 정한다 — 나중에 쓴 쪽이 이긴다.
- 겹치지 않게 하려면 **한쪽을 1 줄인다**(`max-width: 599px`) 또는 **범위 구문의 배타 연산자를 쓴다**(`(width < 600px)`).
- ★ **`599px` 트릭에는 「못 잰 것」이 하나 붙는다.** 미디어 쿼리의 폭은 정수가 아닐 수 있고
  (실측: `matchMedia("(width >= 599.5px)")` 가 **파싱되어 `true` 를 돌려줬다** — 소수 비교가 실제로 평가된다),
  그러면 599 와 600 사이에 **아무 규칙도 안 걸리는 틈**이 생긴다.
  다만 **이 환경에서는 소수 뷰포트 폭을 만들지 못했다** — `--force-device-scale-factor` 를 1.25·1.5 로 줘도
  CSS 픽셀 폭은 `900`·`902` 처럼 정수로만 나왔다. **틈이 나는 것을 직접 보이지는 못했다.**
  어느 쪽이든 오늘 권장은 **범위 구문의 `<`/`>`** 다 — 겹침도 틈도 원천적으로 안 생긴다.

비용 — 없음. 대신 **겹치는 1픽셀을 실제로 띄워 보지 않으면 절대 안 보인다.**

### (3) 범위 구문 — 옛 표기와의 대응

**언제 쓰나** — 새로 중단점을 쓸 때. 옛 표기는 **읽을 줄만** 알면 된다.

```text
  옛 표기                                   범위 구문 (Media Queries 4)
  --------------------------------------    --------------------------------
  (min-width: 600px)                        (width >= 600px)
  (max-width: 600px)                        (width <= 600px)
  (min-width: 400px) and (max-width: 700px) (400px <= width <= 700px)
  (없음)                                     (width < 600px)      <- 배타
  (없음)                                     (width > 600px)      <- 배타
  (width: 600px)                            (width = 600px)

  실측 — 위 표의 좌우가 599/600/601 세 폭에서 전부 같은 값을 냈다
```

```text
   한쪽만 쓰기                  양쪽을 한 줄에
   (width >= 600px)            (400px <= width <= 700px)
        기능이 왼쪽                  기능이 가운데
   (600px <= width)            (700px >= width >= 400px)
        기능이 오른쪽 — 같은 뜻       방향을 맞춰야 한다

   실측 — (600px <= width) 는 600 과 601 에서 참, 599 에서 거짓.  (width >= 600px) 와 같다
```

그림 해설 (한 단계씩):

- 범위 구문은 **비교 연산자를 직접 쓴다.** `<`·`<=`·`>`·`>=`·`=` 다섯이다.
- **두 개를 한 줄에 쓸 때는 부등호 방향이 같아야 한다.** `400px <= width >= 700px` 같은 건 없다.
- ★ **범위 구문에만 있는 것이 `<`·`>`**(배타)다. 옛 `min-`/`max-` 에는 대응이 없다 — 경계 겹침 문제가 여기서 풀린다.
- `calc()` 도 받는다. 실측에서 `(width >= calc(100px + 100px))` 이 `mediaText` 에 `(width >= calc(200px))` 로 정규화돼 담겼다.

비용 — Baseline **widely** 지만 widely 가 된 것이 2025-09-27 로 비교적 최근이다. 아주 오래된 기기를 받아야 하면 옛 표기를 쓴다.

### (4) 논리 연산 — `and`·`or`·`not`·쉼표

**언제 쓰나** — 조건이 둘 이상일 때.

```text
실측 — 뷰포트 800px

  (min-width: 99999px), (min-width: 1px)          -> 참   쉼표 = OR (둘 중 하나)
  ((min-width: 99999px) or (min-width: 1px))      -> 참   or 는 괄호가 필요하다
  (min-width: 1px) and (max-width: 99999px)       -> 참   and
  not (min-width: 99999px)                        -> 참   not (거짓의 부정)
  not (min-width: 1px)                            -> 거짓
  screen and (min-width: 1px)                     -> 참   미디어 타입 + 기능
```

```text
   쉼표 목록은 특별하다 — "여러 개의 미디어 쿼리" 다

   @media (a), (b) { … }
          ^^^^^^^^
          하나가 무효여도 나머지가 산다.  :is() 와 닮은 성질

   실측  @media zzunknown, (min-width: 1px)  ->  참
         왼쪽은 알 수 없는 미디어 타입이라 거짓이지만 오른쪽이 참이라 통과했다
```

```text
   not 의 결합 범위 — 뒤 전체를 부정한다

   not all and (min-width: 1px)
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^   = not ( all and (min-width: 1px) )
                                  뷰포트 800px 에서 안쪽이 참 -> 전체 거짓

   실측  .a3 = rgb(0, 0, 0)           안 먹었다
         matchMedia("not all and (min-width: 1px)").matches = false

   not screen and (min-width: 1px)     -> 거짓 (우리는 screen 이다)
   not screen                          -> 거짓
```

그림 해설 (한 단계씩):

- **`not` 은 한 조건만 집어 부정하지 않는다.** 그 뒤에 이어지는 것을 **통째로** 부정한다.
- 일부만 부정하려면 **괄호를 명시적으로 친다**(`(min-width: 1px) and (not (hover: hover))`).
- **`or` 는 괄호 안에서만** 쓴다. 최상위에서 두 조건을 OR 하려면 **쉼표**를 쓴다(옛 문법과의 호환).
- ★ **쉼표 목록은 관대하다.** 실측에서 `zzunknown, (min-width: 1px)` 이 통과했다 — 한 항이 못 알아보는 것이어도 **다른 항이 살아난다.**

비용 — 없음.

### (5) 모르는 기능·모르는 값은 「거짓」이다 — 버려지는 게 아니다

**언제 쓰나** — 새 미디어 기능을 시험할 때.

```text
실측 — 뷰포트 800px

  @media (totally-unknown-zz: 1) { .a1 { color: red } }
     cssRules 에 있다.  matchMedia("(totally-unknown-zz: 1)").matches = false
     .a1 = rgb(0, 0, 0)                              안 먹었다

  @media (min-width: bogus) { .a2 { … } }
     cssRules 에 있다.  conditionText = "(min-width: bogus)"
     matchMedia("(min-width: bogus)").matches = false
     .a2 = rgb(0, 0, 0)

  @media (min-width: 1px) and (totally-unknown-zz: 1) { .a13 { … } }
     .a13 = rgb(0, 0, 0)     한 항이 거짓이면 and 전체가 거짓

  @media tv and (min-width: 1px) { .a6 { … } }
     .a6 = rgb(0, 0, 0)      tv 는 MQ4 에서 사라진 미디어 타입 -> 거짓
```

```text
   ★ 이 성질이 바로 "안전한 점진적 향상" 의 근거다

   @media (min-width: 600px) and (새-기능: x) { 향상된 스타일 }
                                  ^^^^^^^^^^
                                  모르는 브라우저 -> 조건이 거짓 -> 향상만 안 됨
                                  기본 스타일은 at-rule 밖에 있으므로 무사하다
```

그림 해설 (한 단계씩):

- **파서는 `(이름: 값)` 모양만 확인하고 통과시킨다.** 이름을 아는지는 **평가 시점**의 문제다.
- 그래서 「미지원」이 **문법 오류가 아니라 항상 거짓**이 된다. 07번의 「모르는 at-rule」과 결과가 다르다.
- 단 하나 예외적으로 위험한 것 — **`not` 과 섞였을 때**다. 모르는 기능이 거짓이면 `not (모르는 기능)` 은 **참**이 되어, 의도하지 않은 스타일이 켜진다.

비용 — 없음. 다만 「거짓이 될 뿐」이므로 **오타를 끝까지 못 찾는다.** `matchMedia` 로 한 번 물어보는 것이 유일한 확인이다.

### (6) 미디어 타입 — 오늘 쓸 것은 셋뿐이다

**언제 쓰나** — 인쇄용 스타일을 쓸 때. 그 밖에는 거의 안 쓴다.

```text
  오늘 유효한 미디어 타입   all · screen · print
  MQ4 가 폐기한 것          tv · handheld · tty · projection · braille · …
                            문법상 허용은 되지만 "아무것도 매치하지 않는다"

  실측  @media tv and (min-width: 1px)  -> 안 먹음
        @media print { … }              -> 안 먹음 (화면 렌더이므로)
        @media { … }                    -> ★ 먹는다.  conditionText = ""
        matchMedia("").matches    = true
        matchMedia("all").matches = true

  only screen and (…)    only 는 CSS2 시대 파서를 속이기 위한 접두다.
                         오늘 의미는 없고 평가에도 영향이 없다 (실측: 정상 매치)
```

그림 해설 (한 단계씩):

- **타입을 안 쓰면 `all` 이다.** `@media (min-width: 600px)` 은 `@media all and (min-width: 600px)` 과 같다.
- ★ 실측에서 **조건이 아예 빈 `@media { … }` 도 적용됐다** — 빈 조건은 `all` 이다.
- `only` 는 **오래된 파서 회피용 유물**이다. 오늘 새로 쓸 이유가 없다.

비용 — 없음.

### (7) ★ 미디어 쿼리는 명시도를 안 바꾼다 — 순서만 바꾼다

**언제 쓰나** — 「미디어 쿼리 안에 썼는데 안 먹는다」를 진단할 때. **[01번 주제](../01-cascade-and-priority/2-summary.md)와 이어지는 자리다.**

```text
실측 A — 명시도가 다르면 미디어 쿼리 안이어도 진다 (뷰포트 800px, 조건은 참)

  #id-a11 { color: #1d4ed8 }                       명시도 (1,0,0)
  @media (min-width: 1px) { .a11 { color: #b91c1c } }  명시도 (0,1,0)

  .a11 = rgb(29, 78, 216)     파랑.  조건이 참인데도 졌다
```

```text
실측 B — 명시도가 같으면 "등장 순서" 만으로 갈린다

  @media (min-width: 1px) { .c1 { color: #b91c1c } }
  .c1 { color: #1d4ed8 }
     .c1 = rgb(29, 78, 216)     파랑 — 뒤에 쓴 쪽이 이김

  .c2 { color: #1d4ed8 }
  @media (min-width: 1px) { .c2 { color: #b91c1c } }
     .c2 = rgb(185, 28, 28)     빨강 — 역시 뒤에 쓴 쪽이 이김
```

```text
   캐스케이드 6단계에서 @media 가 끼는 자리 (01번 정본)

   1 출처·중요도  2 요소 안 스타일  3 레이어  4 명시도  5 근접성  6 등장 순서
                                                                   ^^^^^^^^^
                                            @media 는 여기서만 작용한다
                                            (규칙이 시트에서 어디에 적혀 있느냐)
```

그림 해설 (한 단계씩):

- `@media` 안에 넣는다고 **선택자가 세지지 않는다.** 규칙을 **켤지 말지**만 정한다.
- 그래서 「미디어 쿼리로 덮어쓰기」가 되려면 **덮을 규칙보다 뒤에** 있어야 한다.
- 모바일 우선(`min-width` 를 위에서 아래로 키워 가며 쓰기)이 관례가 된 이유가 이것이다 — **순서가 곧 우선순위**라서 오름차순으로 쓰면 자연스럽게 맞는다.

비용 — 없음.

### (8) 중첩 — `@media` 안의 `@media`, 규칙 안의 `@media`

**언제 쓰나** — 컴포넌트 단위로 스타일을 모아 둘 때.

```text
실측 — 두 방향 다 동작한다 (뷰포트 800px)

  @media (min-width: 1px) { @media (max-width: 99999px) { .a10 { color: #15803d } } }
     .a10 = rgb(21, 128, 61)         중첩된 조건은 AND 로 합쳐진다

  .z { color: #000; @media (min-width: 1px) { .z1 { color: #15803d } } }
     .z1 = rgb(21, 128, 61)
     cssText 를 읽으면
       .z { color: rgb(0, 0, 0); @media (min-width: 1px) { & .z1 { … } } }
                                                          ^^^ 파서가 & 를 붙였다
```

그림 해설 (한 단계씩):

- `@media` 를 겹치면 조건이 **AND** 로 합쳐진다.
- 2023 년에 들어온 **중첩**([14번 주제](../14-css-nesting/2-summary.md)) 덕분에 **규칙 안에 `@media` 를 넣을 수 있다.**\
  그러면 그 규칙의 선택자가 **암묵적으로 앞에 붙는다**(`& .z1`).
- 컴포넌트마다 중단점을 모아 둘 수 있게 된 것이 실무상 가장 큰 변화다.

비용 — 없음. 다만 **규칙이 시트의 어디에 있느냐가 여전히 순서를 정한다**(위 (7)).

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
@media screen and (400px <= width <= 700px) { .card { padding: 8px } }
@media (min-width: 600px), print            { .card { padding: 16px } }
@media not all and (hover: hover)           { .card { padding: 20px } }
```

```js
matchMedia("(width <= 600px)").matches      // 조건만 따로 평가
document.styleSheets[0].cssRules[3].media.mediaText   // 파서가 이해한 조건
document.styleSheets[0].cssRules[3].conditionText     // 같은 문자열
```

### 금지 사례 — 던져서 확인한 것

```css
@media (min-width: 600px) or (print) { … }   /* 최상위 or 는 없다 — 쉼표를 쓴다 */
@media (400px <= width >= 700px) { … }       /* 부등호 방향이 섞였다 */
@media (min-width: bogus) { … }              /* 담기지만 항상 거짓 */
@media not (min-width: 1px) and (print) { … }/* not 의 범위가 의도와 다르다 */
```

### 어디서 헷갈리나

- **`min-`/`max-` 는 이상/이하**다. 초과·미만이 필요하면 범위 구문의 `<`·`>` 를 쓴다.
- **쉼표는 OR 이고, 최상위에 `or` 키워드는 없다.** `or` 는 괄호 안에서만 쓴다.
- **`not` 은 뒤 전체를 부정한다.** 한 항만 부정하려면 괄호를 친다.
- **미디어 쿼리는 조건이지 우선순위가 아니다.** 명시도는 그대로다.
- **`@media` 안에 `@import` 를 넣으면 조용히 사라진다.** 실측(로컬 HTTP): `@media (min-width: 1px) { @import url("a.css"); }` 는
  `@media` 규칙은 담기는데 **안쪽 `cssRules` 가 비어 있고 `a.css` 요청이 서버 로그에 아예 안 찍혔다.**
  조건은 `@import url(…) screen and (…)` 처럼 `@import` 쪽에 단다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. 중단점을 같은 숫자로 잡고 겹친 걸 모른다

실측에서 **600px 에서 `max-width: 600px` 과 `min-width: 600px` 이 둘 다 참**이었다.\
599 와 601 만 확인하면 절대 안 보이고, **정확히 600 을 띄워야** 보인다.\
그 1픽셀에서는 **나중에 쓴 규칙이 이긴다** — 곧 시트를 재배치하는 순간 동작이 바뀐다.

### 2. 「미지원 기능이니 규칙이 버려지겠지」라고 설명한다

**안 버려진다.** 실측에서 `(totally-unknown-zz: 1)` 이 든 `@media` 가 `cssRules` 에 멀쩡히 있었고,\
`conditionText` 도 **원문 그대로** 남아 있었다. 버려진 게 아니라 **평가가 거짓**이다.\
이걸 섞어 말하면 「`@supports` 로 감싸면 되겠네」 같은 엉뚱한 처방이 나온다.

### 3. `not` 이 바로 뒤 한 항만 부정한다고 생각한다

실측에서 `not all and (min-width: 1px)` 이 뷰포트 800px 에서 **거짓**이었다.\
`not all` 과 `(min-width: 1px)` 을 AND 한 게 아니라 **`all and (min-width: 1px)` 전체를 부정**한 것이다.\
더 위험한 경우 — **모르는 기능을 `not` 으로 감싸면 항상 참**이 되어 의도하지 않은 스타일이 켜진다.

### 4. 미디어 쿼리로 「덮어쓰기」를 하려는데 명시도를 안 본다

실측에서 `#id-a11` 이 `@media` 안의 `.a11` 을 이겼다. 조건은 참이었는데도 졌다.\
`@media` 는 **6단계 중 마지막(등장 순서)** 에만 작용한다. 명시도가 지면 조건이 참이어도 못 이긴다.

### 5. 창 크기를 안 바꿔 보고 「좁히면 이렇게 된다」고 쓴다

**헤드리스에서도 `--window-size` 를 바꾸면 곧바로 확인된다.** 안 바꾸고 쓴 문장은 전부 추측이다.\
★ 이 환경에서 **창 폭 하한이 있다** — `--window-size=400,400` 으로 띄워도 `innerWidth` 는 **500** 이었다.\
400px 이하를 주장하려면 **다른 수단**(에뮬레이션·iframe)이 필요하다. 이 문서는 500px 이상만 실측했다.

### 6. 헤드리스에서 잰 기능값을 사람의 브라우저 값으로 읽는다

실측에서 **`(hover: hover)` 와 `(pointer: fine)` 이 둘 다 거짓**이었다(입력 장치가 없다).\
`(prefers-reduced-motion: no-preference)`·`(scripting: enabled)`·`(update: fast)` 는 참이었다.\
**환경에 달린 값**이므로 「이 기능은 거짓이다」로 일반화하면 안 된다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `min-`/`max-` 가 이상/이하인 것 | **명세**(mediaqueries-4 「Media Features」) |
| 600 에서 두 조건이 겹치는 것 | **명세**의 논리적 귀결 + **관찰**(실측 세 폭) |
| 범위 구문과 옛 표기의 대응 | **명세**(「Range Context」) |
| 쉼표가 OR 이고 최상위에 `or` 가 없는 것 | **명세**(「Media Query Syntax」) |
| `not` 이 뒤 전체를 부정하는 것 | **명세**(같은 절) |
| 모르는 기능·타입이 **거짓**이 되는 것 | **명세**(「Evaluating Media Queries」 — unknown 은 false) |
| 조건이 거짓인 `@media` 가 `cssRules` 에 남는 것 | **명세**(CSSOM) + **관찰** |
| `conditionText` 가 `(min-width: bogus)` 로 **원형 유지**되는 것 | **관찰**(Chrome 151). 직렬화 세부다 |
| `calc(100px + 100px)` 이 `calc(200px)` 로 정규화되는 것 | **관찰**(Chrome 151 직렬화) |
| 미디어 쿼리가 명시도에 영향이 없는 것 | **명세**(css-cascade — 조건부 규칙은 명시도에 기여하지 않는다) |
| **`(hover: hover)` 가 거짓인 것** | **환경**(headless 에 포인팅 장치 없음). 언어 규칙이 아니다 |
| **창 폭 하한 500px** | **환경**(이 머신의 Chrome 창 최소 폭). 명세와 무관 |
| 범위 구문 Baseline **widely**(2025-09-27) | **2차 집계**(`webstatus.dev`) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 페이지 전체 레이아웃을 화면 크기로 가른다 | `@media` | 컨테이너 쿼리(뷰포트를 못 본다) |
| 컴포넌트가 놓인 **자리**에 맞춰 바뀌어야 한다 | `@container`([40번](../40-container-and-style-queries/2-summary.md)) | `@media`(부모 상자를 못 본다) |
| 새로 중단점을 쓴다 | 범위 구문 `(width < 600px)` | 같은 숫자의 `min-`/`max-` 짝 |
| 아주 오래된 기기를 받아야 한다 | `min-`/`max-` 표기 | 범위 구문 |
| 인쇄용 스타일 | `@media print` | 화면 스타일에 `!important` 로 덧칠 |
| 모르는 기능을 시험한다 | `matchMedia` 로 먼저 물어보기 | 화면만 보고 추측 |
| 조건이 아니라 **지원 여부**를 묻고 싶다 | `@supports`([41번](../41-supports-feature-queries/2-summary.md)) | `@media` |

판단 규칙 두 줄.

- **「무엇을 기준으로 재는가」를 먼저 묻는다.** 뷰포트면 `@media`, 조상 상자면 `@container`, 브라우저가 아는지면 `@supports`.
- **중단점은 겹치지 않게 짠다.** 겹치면 시트의 순서가 동작을 정하게 된다 — 리팩터링 한 번에 깨진다.

## demo — 경계의 1픽셀

```html demo
<p class="a">max-width: 600px 만 걸린 줄</p>
<p class="b">min-width: 600px 만 걸린 줄</p>
<p class="c">둘 다 걸린 줄</p>
<style>
  p { margin: 4px 0; padding: 6px 10px; font: 14px system-ui; background: #e2e8f0; }
  @media (max-width: 600px) { .a, .c { background: #fecaca } }
  @media (min-width: 600px) { .b, .c { background: #bfdbfe } }
</style>
```

> **보이는 것** — 창 폭에 따라 세 줄의 배경이 갈린다. **뷰포트가 601px 이상이면** 첫 줄은 회색, 둘째·셋째 줄은 파랑이다. **599px 이하로 좁히면** 첫 줄과 셋째 줄이 분홍, 둘째 줄이 회색이 된다. **정확히 600px 에서는** 첫 줄이 분홍, 둘째 줄이 파랑, **셋째 줄은 파랑**이다 — 셋째 줄에는 두 조건이 **둘 다 참**이라 나중에 쓴 `min-width` 쪽이 이긴 것이다.\
> **바꿔 볼 것** — 두 `@media` 의 **순서를 뒤바꾸면** → **600px 에서 셋째 줄이 분홍으로 바뀐다**(명시도가 같아 순서가 승자를 정한다) · `(max-width: 600px)` → `(width < 600px)` 로 바꾸면 → **600px 에서 첫 줄이 회색이 되고 겹침이 사라진다**

*(Chrome 151 headless 실측, `--window-size` 를 바꿔 가며: 599px 에서 `.a`=`rgb(254, 202, 202)` `.b`=`rgb(226, 232, 240)` `.c`=`rgb(254, 202, 202)` · 600px 에서 `.a`=`rgb(254, 202, 202)` `.b`=`rgb(191, 219, 254)` `.c`=`rgb(191, 219, 254)` · 601px 과 780px 에서 `.a`=`rgb(226, 232, 240)` `.b`=`rgb(191, 219, 254)` `.c`=`rgb(191, 219, 254)`.)*

## 핵심 문장

- **미디어 쿼리가 재는 것은 뷰포트**다. 조상 상자를 재는 것은 컨테이너 쿼리이고, 그 하나가 38 ↔ 40 의 전부다.
- **`max-width: N` 과 `min-width: N` 은 N 에서 둘 다 참**이다. 실측에서 600px 에 겹쳤고, 그 구간은 **등장 순서**가 정한다.
- **범위 구문에만 배타 연산자(`<`·`>`)가 있다.** 겹침을 없애는 유일한 정공법이다.
- **모르는 기능·타입은 버려지지 않고 「거짓」이 된다.** 조건이 거짓인 `@media` 도 `cssRules` 에 남는다.
- **`not` 은 뒤 전체를 부정한다.** 모르는 기능을 `not` 으로 감싸면 **항상 참**이 되는 함정이 있다.
- **쉼표는 OR 이고 관대하다.** 실측에서 `zzunknown, (min-width: 1px)` 이 통과했다.
- **미디어 쿼리는 명시도를 안 바꾼다.** 캐스케이드 6단계 중 **등장 순서**에만 작용한다.
- **at-rule 의 진단 창은 `matchMedia`** 다. 「담겼나」 다음에 「참인가」를 따로 물어야 한다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 38번)
- [`../../../../../../history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) — **반응형 웹이 왜 필요해졌나의 정본.**\
  도입 맥락은 거기, 여기는 **범위 구문·경계값·논리 결합이라는 문법 규칙**만.
- [`../07-syntax-and-error-recovery/2-summary.md`](../07-syntax-and-error-recovery/2-summary.md) — **오류 복구와 at-rule 폐기의 정본.**\
  「모르는 at-rule 은 블록째」는 거기, 여기는 **「아는 at-rule 안의 모르는 기능은 거짓이 된다」** 는 반대편.
- [`../01-cascade-and-priority/2-summary.md`](../01-cascade-and-priority/2-summary.md) — 캐스케이드 6단계의 정본.\
  미디어 쿼리가 **어느 단계에도 안 끼어들고 순서만 쓴다**는 결론이 거기서 나온다.
- [`../05-cascade-layers/2-summary.md`](../05-cascade-layers/2-summary.md) — `@layer` 와 `@media` 를 겹쳐 쓸 때의 순서.
- [`../14-css-nesting/2-summary.md`](../14-css-nesting/2-summary.md) — 규칙 안에 `@media` 를 넣을 수 있게 된 근거.
- [`../39-color-scheme-and-preferences/2-summary.md`](../39-color-scheme-and-preferences/2-summary.md) — **사용자 선호 기능**(`prefers-*`)의 정본. 여기는 **문법과 논리**만.
- [`../40-container-and-style-queries/2-summary.md`](../40-container-and-style-queries/2-summary.md) — **조상 상자를 재는 쪽.** 이 주제와 대비해 읽는다.
- [`../41-supports-feature-queries/2-summary.md`](../41-supports-feature-queries/2-summary.md) — **브라우저가 아는지**를 묻는 쪽.
- [목록의 **33번 주제**](../33-length-units/)(길이 단위) — `px`·`em`·`vw` 가 무엇을 재는가. 중단점 숫자의 단위 선택은 거기.

## 용어 풀이

- **미디어 쿼리(media query)** — 미디어 타입과 미디어 기능으로 만든 참/거짓 조건.
- **미디어 타입(media type)** — `all`·`screen`·`print`. 그 밖은 MQ4 가 폐기해 아무것도 매치하지 않는다.
- **미디어 기능(media feature)** — 괄호 안에서 묻는 한 가지. `width`·`orientation`·`hover` 등.
- **뷰포트(viewport)** — 문서가 그려지는 창의 보이는 영역. 미디어 쿼리가 재는 대상.
- **중단점(breakpoint)** — 레이아웃을 바꾸는 폭의 경계.
- **범위 구문(range syntax)** — `(width <= 600px)` 처럼 비교 연산자를 직접 쓰는 MQ4 표기.
- **`only`** — CSS2 시대 파서를 속이려던 접두. 오늘 의미가 없다.
- **`matchMedia()`** — 조건만 따로 평가하는 JS API. at-rule 진단의 네 번째 창.
- **`conditionText` / `media.mediaText`** — 파서가 이해한 조건 문자열. 내가 쓴 글자와 다를 수 있다.
- **등장 순서(order of appearance)** — 캐스케이드 6단계의 마지막. `@media` 가 작용하는 유일한 자리.
- **점진적 향상(progressive enhancement)** — 모르는 조건이 거짓이 되어 기본 화면이 살아남는 방식.

## 더 들어가면

- **미디어 쿼리는 `<link>` 에도 붙는다 — 그래도 파일은 내려받는다.** 실측(로컬 HTTP 서버 로그):
  `media="print"` 와 `media="(min-width: 99999px)"` 를 단 두 시트가 **둘 다 `200` 으로 요청됐다.**
  조건이 거짓이면 적용이 안 될 뿐 **네트워크는 그대로 탄다** — 「안 받겠지」가 아니다.
- **`matchMedia` 는 이벤트를 준다.** `mq.addEventListener("change", …)` 로 조건이 뒤집히는 순간을 잡을 수 있다 — JS 쪽 로직을 CSS 중단점과 **한 숫자로 묶는** 표준 방법이다.
- **컨테이너 쿼리가 나온 뒤에도 미디어 쿼리는 안 없어진다.** 페이지 단위의 결정(사이드바를 접을지, 인쇄 레이아웃)은 여전히 뷰포트 문제다. 둘은 대체가 아니라 **축이 다르다.**
- **MQ5 는 「사용자」 쪽 기능을 잔뜩 들여왔다** — `prefers-color-scheme`·`prefers-reduced-motion`·`prefers-contrast`·`forced-colors`. 「기기를 재던 자」가 「사람을 재는 자」로 넓어진 것이고, 그 이야기는 [39번 주제](../39-color-scheme-and-preferences/2-summary.md)다.
