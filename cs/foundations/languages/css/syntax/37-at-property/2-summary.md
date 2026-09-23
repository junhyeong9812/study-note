# css/syntax/37 — `@property`: 타입 등록·초기값·상속 여부 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Properties and Values API Level 1](https://drafts.csswg.org/css-properties-values-api-1/) 의 「The `@property` Rule」·「`registerProperty()`」·「Syntax Strings」 절. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 값은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `document.styleSheets[…].cssRules`·`getComputedStyle`·`CSS.registerProperty` 로 읽은 것이다. 애니메이션 중간값은 **음수 지연 + `paused`** 로 시각을 고정해 읽었고, 전환은 **CDP 로 실제 마우스를 움직여** `:hover` 를 발생시킨 뒤 샘플링했다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — CSS 에 언어 버전은 없다. 등록 커스텀 속성(registered custom properties)은 Baseline **newly**(2024-07-09, 아직 widely 아님) — `api.webstatus.dev` 의 `registered-custom-properties` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`@property` 는 커스텀 속성을 「토큰 뭉치」에서 「타입 있는 값」으로 바꾸는 신고서다.**

세관 신고에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 신고 안 한 짐 | 등록하지 않은 커스텀 속성 — 안에 뭐가 들었는지 아무도 안 본다 |
| 「이 상자에는 길이가 들었습니다」 신고서 | `syntax: "<length>"` |
| 신고 내용과 다른 물건이 들었을 때 | 값이 `syntax` 에 안 맞음 → **초기값으로 되돌린다** |
| 신고서에 반드시 적어야 하는 기본 품목 | `initial-value` — `syntax: "*"` 말고는 **필수** |
| 아래층으로 상자를 내려보낼지 | `inherits: true` / `false` |
| 신고했으니 중간 상태를 만들 수 있다 | **애니메이션·전환이 된다** |

- 등록하지 않은 커스텀 속성은 **값이 아니라 글자 뭉치**다.\
  `--w: 40px` 는 브라우저에게 「`40px` 라는 **일곱 글자**」이지 길이가 아니다.\
  길이인지는 `var(--w)` 로 펼쳐져 **쓰이는 자리에서** 비로소 판정된다([목록의 **36번 주제**](../36-custom-properties/)가 정본).
- `@property` 로 등록하면 그 판정이 **선언 시점으로 앞당겨진다.** 그러면 두 가지가 따라온다.\
  ① **중간값을 만들 수 있다** → 애니메이션·전환이 된다.\
  ② **무효 값의 처리가 달라진다** → 버리는 게 아니라 `initial-value` 로 되돌린다.

```text
  등록 안 함                              @property 로 등록함
  +----------------------------+          +----------------------------+
  | --w: 40px                  |          | --w: 40px                  |
  |   브라우저가 보는 것        |          |   브라우저가 보는 것        |
  |   = "40px" 라는 토큰 뭉치   |          |   = <length> 타입의 40px   |
  +----------------------------+          +----------------------------+
    40px 과 320px 사이의                     40px 과 320px 사이의
    중간값을 만들 수 없다                    중간값 = 180px 을 만든다
    -> 전환이 아예 안 걸린다                 -> 1초에 걸쳐 걸어간다
```

실무에서 이게 터지는 자리는 **그라데이션 각도·색을 부드럽게 돌리려 할 때**다.\
`--angle` 에 `transition` 을 걸어 놓고 「왜 뚝 끊기지」 하는데, 에러도 경고도 없다.\
등록 한 줄이 빠진 것이고, 그 한 줄이 **값의 타입을 만들어 준다.**

> **등록 커스텀 속성(registered custom property)** — `@property` 나 `CSS.registerProperty()` 로 타입을 신고한 `--` 속성.\
> 예: `@property --w { syntax: "<length>"; inherits: false; initial-value: 0px; }` 뒤의 `--w`.

> **보간(interpolation)** — 시작값과 끝값 사이의 중간값을 만드는 것.\
> 예: `0px` 와 `200px` 의 50% 는 `100px`. 토큰 뭉치 `"0px"` 와 `"200px"` 의 50% 는 **만들 수 없다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **등록하면 무엇이 달라지는가.** 등록 전후를 나란히 놓았을 때 눈에 보이는 차이가 무엇인가.
2. **세 칸(`syntax`·`inherits`·`initial-value`)은 각각 무엇을 정하는가.** 한 칸을 빼면 어떻게 되는가.
3. **무효한 값이 들어오면 어디로 떨어지는가.** 등록 전의 IACVT 와 어떻게 다른가.

## 동작 방식

### (1) ★ 등록하면 애니메이션이 된다 — 이 주제의 과녁

**언제 쓰나** — 커스텀 속성으로 색·길이·각도를 움직이려 할 때. **등록 여부가 갈리는 유일한 자리는 여기다.**

같은 키프레임을 **등록한 속성**과 **등록 안 한 속성**에 걸고 **50% 지점에서 멈춰** 읽었다.

```text
실측 — animation: … 10s linear -5s paused   (곧 진행률 50%)

  등록 안 함  @keyframes { from { --unreg-c: #b91c1c } to { --unreg-c: #1d4ed8 } }
     --unreg-c        = "#1d4ed8"            <- 끝값. 중간이 없다
     background-color = rgb(29, 78, 216)

  등록함      @property --reg-c { syntax: "<color>"; inherits: false; initial-value: #b91c1c }
     --reg-c          = "rgb(107, 53, 122)"  <- 빨강과 파랑의 중간색
     background-color = rgb(107, 53, 122)
```

```text
  진행률                 등록 안 한 --uw            등록한 --reg-l
  ------------------     ----------------------     ----------------------
  25%   (-2.5s)          0px                        50px
  49%   (-4.9s)          0px                        (측정 안 함)
  51%   (-5.1s)          200px   <- 여기서 점프      (측정 안 함)
  50%   (-5s)            200px                      100px
  75%   (-7.5s)          200px                      150px
```

그림 해설 (한 단계씩):

- 등록 안 한 쪽은 **0% ↔ 100% 두 값만** 가진다 — 49%까지 `0px`, 51%부터 `200px` 다.\
  이것이 명세가 말하는 **이산 보간**(discrete interpolation)이다. 애니메이션이 「되긴 되는데」 **계단 하나**다.
- 등록한 쪽은 25%/50%/75% 가 각각 `50px`/`100px`/`150px` 로 **선형으로 나온다.** 타입을 알기 때문이다.
- 색도 같다 — `#b91c1c` 와 `#1d4ed8` 의 절반이 `rgb(107, 53, 122)` 라는 **실제 중간색**으로 계산됐다.

> **이산 보간(discrete interpolation)** — 중간값을 못 만드는 타입의 기본 동작. 50% 지점에서 시작값→끝값으로 **한 번 뒤집힌다.**\
> 예: `visibility` 나 등록 안 한 커스텀 속성이 이렇다.

비용 — 등록 한 줄. 대신 그 속성은 그 문서 전체에서 **타입 검사를 받게 된다**(아래 (4)).

### (2) ★ 전환은 「계단」조차 아니다 — 아예 안 걸린다

**언제 쓰나** — `transition` 으로 커스텀 속성을 움직이려 할 때.

(1)과 **결과가 다르다.** 애니메이션은 계단이라도 있는데 전환은 그냥 없다.

```text
실측 — CDP 로 실제 마우스를 올려 :hover 를 발생시키고 시각마다 width 를 읽었다
       transition: --w 1s linear  /  transition: --uw 1s linear

  시각          등록한 --w      등록 안 한 --uw
  ----------    ------------    ----------------
  호버 전       40px            40px
  +0.25s        114.656px       320px      <- 이미 끝
  +0.50s        184.656px       320px
  +0.75s        254.656px       320px
  +1.20s        320px           320px
  뗀 뒤 1.5s    40px            40px
```

그림 해설 (한 단계씩):

- 등록 안 한 쪽은 **0.25초 시점에 이미 끝값**이다. 이산 보간의 계단조차 안 보인다.
- 이유는 전환의 시작 조건에 있다 — 전환은 **보간 가능한 값이 바뀌었을 때** 걸린다.\
  등록 안 한 커스텀 속성은 보간 가능하지 않으므로 **전환 자체가 생성되지 않는다**([52번 주제](../52-transition/2-summary.md)의 「걸어갈 수 없는 짐」과 같은 자리다).
- 애니메이션은 키프레임이 **명시적으로 두 값을 주므로** 이산 보간이라도 성립하고, 전환은 줄 게 없어서 안 걸린다.

비용 — 없음. 다만 **애니메이션과 전환이 다르게 실패한다**는 것을 모르면 진단이 엉킨다.

### (3) 세 칸이 각각 정하는 것

**언제 쓰나** — `@property` 를 쓸 때마다. 칸이 셋뿐이라 전부 외운다.

```text
  @property --box-w {
    syntax: "<length>";      <- 무엇이 들어올 수 있나  (타입)
    inherits: false;         <- 자손에게 내려가나      (상속)
    initial-value: 0px;      <- 아무도 안 정했을 때    (초기값)
  }
```

```text
실측 — cssRules 에서 CSSPropertyRule 을 읽은 것

  --ok-len   | syntax=<length>        | inherits=false | initialValue=10px
  --star     | syntax=*               | inherits=false | initialValue=null
  --noinh    | syntax=<color>         | inherits=false | initialValue=#b91c1c
  --inh      | syntax=<color>         | inherits=true  | initialValue=#b91c1c
  --numlist  | syntax=<length> | auto  | inherits=false | initialValue=auto
```

상속 칸을 실제로 갈라 재 본 것이다.

```text
  <div class="p4">  --inh: #15803d   --noinh: #15803d
    +-- <div class="g5">   아무것도 안 정함

  실측
    .g5 의 --inh    = rgb(21, 128, 61)   <- 초록. 부모에게서 내려왔다
    .g5 의 --noinh  = rgb(185, 28, 28)   <- 빨강. initial-value 로 떨어졌다
```

그림 해설 (한 단계씩):

- `inherits: true` 면 **보통 커스텀 속성처럼** 상속을 탄다([03번 주제](../03-inheritance-and-global-keywords/2-summary.md)).
- `inherits: false` 면 부모가 무엇을 정했든 **자손은 `initial-value`** 를 본다.\
  등록 안 한 커스텀 속성은 **항상 상속하므로**, 이 칸은 「상속을 **끌 수 있게** 됐다」는 뜻이다.
- ★ 읽어 온 값이 `rgb(21, 128, 61)` 다 — **등록하면 계산값이 타입의 정규형으로 바뀐다.**\
  등록 안 한 속성은 `"#15803d"` 라는 글자 그대로 나온다. `getComputedStyle` 출력만 봐도 등록 여부를 안다.

비용 — 없음.

### (4) ★ 무효 값이 IACVT 가 아니라 초기값으로 떨어진다

**언제 쓰나** — 커스텀 속성에 잘못된 값이 들어올 수 있는 모든 자리. **36번과 갈리는 지점이다.**

```text
실측 — 같은 오타 redd 를 두 자리에 넣었다

  등록 안 함     .g2 { --plain: redd; color: var(--plain) }
     속성 목록에 --plain 과 color 가 둘 다 담겨 있다
     --plain = "redd"          <- 글자 그대로 살아 있다
     color   = rgb(0, 0, 0)    <- 이 선언만 unset 처럼 처리됐다  (IACVT)

  등록함         @property --ok-len { syntax:"<length>"; inherits:false; initial-value:10px }
                 .g3 { --ok-len: redd; width: var(--ok-len) }
     --ok-len = "10px"         <- ★ 값 자체가 초기값으로 갈아끼워졌다
     width    = 10px
```

```text
   등록 안 함                          등록함
   +-------------------------+         +-------------------------+
   | --plain 은 "redd" 그대로 |         | --ok-len 은 "10px" 로   |
   |   쓰는 쪽(color)만 죽는다|         |   되돌아간다             |
   |   -> IACVT              |         |   -> 쓰는 쪽은 멀쩡히 산다|
   +-------------------------+         +-------------------------+
     var() 를 쓴 속성마다 하나씩 죽는다   한 군데서 막히고 아래로 안 번진다
```

그림 해설 (한 단계씩):

- 등록 전에는 **무효 판정이 사용처로 미뤄진다.** `var(--plain)` 을 쓴 속성이 열 개면 열 개가 각각 죽는다.
- 등록 후에는 **선언 시점에 막힌다.** 타입에 안 맞는 값은 그 자리에서 `initial-value` 로 대체되고, 그 뒤로는 **항상 유효한 값**만 흐른다.
- ★ 그래서 등록은 **디자인 토큰의 방화벽**이다. 한 군데 오타가 페이지 절반을 지우는 일이 안 생긴다.
- IACVT 의 정본은 [목록의 **36번 주제**](../36-custom-properties/)와 [07번 주제](../07-syntax-and-error-recovery/2-summary.md)다. 여기서는 **등록이 그 동작을 바꾼다**는 것만 쓴다.

비용 — 무효 값이 **조용히 다른 값으로 바뀐다.** 콘솔에 아무것도 안 찍히는 것은 똑같다.

### (5) ★ `initial-value` 는 `syntax: "*"` 말고는 필수다 — 어기면 규칙째 사라진다

**언제 쓰나** — `@property` 를 처음 쓸 때 가장 흔한 사고.

```text
실측 — @property 를 일곱 개 선언했는데 cssRules 에 담긴 CSSPropertyRule 은 다섯 개였다

  선언한 것                                               담겼나
  ----------------------------------------------------   ------
  --ok-len   syntax:"<length>"  initial-value:10px         O
  --no-init  syntax:"<length>"  (initial-value 없음)       X  <- 통째로 사라졌다
  --star     syntax:"*"         (initial-value 없음)       O  <- * 는 면제
  --noinh    syntax:"<color>"   initial-value:#b91c1c      O
  --inh      syntax:"<color>"   initial-value:#b91c1c      O
  --badsyn   syntax:"<lengthzz>" initial-value:1px         X  <- 타입 이름이 없다
  --numlist  syntax:"<length> | auto"  initial-value:auto  O

  그 결과
    --no-init 을 읽으면 ""     등록도 안 됐고 값도 없다
    --badsyn  을 읽으면 ""
```

그림 해설 (한 단계씩):

- 칸 하나가 모자라면 **그 선언만 버려지는 게 아니라 `@property` 규칙 전체가 버려진다.**\
  at-rule 의 프렐류드·본문이 무효면 통째로 간다는 [07번 주제](../07-syntax-and-error-recovery/2-summary.md)의 규칙 그대로다.
- **에러도 경고도 없다.** 「등록했는데 왜 애니메이션이 안 되지」의 첫 번째 원인이다.
- `syntax: "*"` 만 면제되는 이유 — `*` 는 「아무 토큰 뭉치나」라서 **정할 초기값이 없다.**\
  대신 `*` 로 등록하면 애니메이션도 안 된다(타입이 없으니 중간값도 없다).
- 진단은 언제나 **`cssRules` 에서 `CSSPropertyRule` 을 세어 보는 것**이다.

비용 — 없음.

### (6) at-rule 과 JS API — 같은 일을 하는데 실패 방식이 정반대다

**언제 쓰나** — 등록이 왜 안 됐는지 알아내야 할 때. **여기가 이 주제의 진단 창이다.**

```text
실측 — CSS.registerProperty 에 같은 실수를 던졌더니 전부 예외를 던졌다

  initial-value 없음 (syntax 가 * 아님)
    SyntaxError: An initial value must be provided if the syntax is not '*'
  syntax: "*" + initialValue 없음
    ok                                       <- at-rule 과 같은 규칙
  같은 이름을 두 번
    InvalidModificationError: The name provided has already been registered.
  syntax: "<lengthzz>"
    SyntaxError: The syntax provided is not a valid custom property syntax.
  initialValue: "redd"  (syntax 는 <length>)
    SyntaxError: The initial value provided does not parse for the given syntax.
  name: "nodashes"
    SyntaxError: Custom property names must start with '--'.
```

```text
   @property (CSS)                       CSS.registerProperty (JS)
   +-----------------------------+       +-----------------------------+
   | 틀리면 규칙이 조용히 사라짐  |       | 틀리면 예외를 던진다         |
   |   cssRules 를 세어야 안다    |       |   메시지가 이유까지 말해 준다 |
   +-----------------------------+       +-----------------------------+
     CSS 의 기본 — 에러가 없다              JS API 라서 에러가 있다
```

등록 시점이 늦어도 **소급해서 적용된다**는 것도 실측으로 보였다.

```text
  같은 문서, 같은 애니메이션 (50% 지점에 멈춰 있음)

    registerProperty 호출 전   .j1 의 width = 200px      <- 이산 보간
    registerProperty('--js-l', {syntax:'<length>', …}) 실행
    registerProperty 호출 후   .j1 의 width = 100px      <- 그 자리에서 보간으로 바뀐다
```

그림 해설 (한 단계씩):

- **등록은 문서 전역이고 되돌릴 수 없다.** 같은 이름을 두 번 등록하면 JS 쪽은 예외를 던진다.
- ★ **진단할 때는 `CSS.registerProperty` 로 같은 값을 한 번 던져 보는 것이 가장 빠르다.**\
  `@property` 는 왜 버려졌는지 말해 주지 않지만, JS API 는 **문장으로 말해 준다.**
- 반대로 **실제 코드는 `@property` 를 쓴다** — 스타일시트와 같은 곳에 있어야 하고, JS 로드 전에 이미 적용돼야 하기 때문이다.

비용 — 없음.

### (7) `syntax` 문법 — 쓸 수 있는 것과 조합

**언제 쓰나** — 색·길이 말고 다른 것을 등록할 때.

```text
  한 타입          "<length>"  "<color>"  "<number>"  "<percentage>"
                   "<angle>"   "<time>"   "<integer>" "<length-percentage>"
                   "<image>"   "<url>"    "<resolution>"  "<transform-function>"

  선택지 묶기      "<length> | auto"            둘 중 하나
  고정 낱말        "auto | cover | contain"     이 세 낱말만
  목록             "<length>+"   공백으로 구분   "<color>#"  쉼표로 구분
  아무거나         "*"           타입 없음 -> 애니메이션 안 됨 · initial-value 면제

  실측  "<length> | auto"  로 등록하고 initial-value: auto  -> 정상 등록, 값 "auto"
        "<lengthzz>"                                        -> 규칙째 버려짐
```

그림 해설 (한 단계씩):

- **`<length>` 같은 산꺾쇠 이름은 명세가 정한 목록에서만** 고른다. 모르는 이름을 쓰면 규칙이 통째로 사라진다.
- `|` 로 묶으면 **어느 쪽이든 받되**, 서로 다른 갈래 사이에서는 보간이 안 된다(`auto` ↔ `10px` 는 중간이 없다).
- 고정 낱말(`auto` 같은 것)은 산꺾쇠 없이 그대로 적는다.

비용 — 없음.

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
@property --card-pad {
  syntax: "<length>";
  inherits: false;
  initial-value: 8px;
}

.card { --card-pad: 16px; padding: var(--card-pad); transition: --card-pad .3s; }
```

```js
CSS.registerProperty({
  name: "--card-pad", syntax: "<length>", inherits: false, initialValue: "8px"
});
```

### 금지 사례 — 던져서 확인한 것

```css
@property --a { syntax: "<length>"; inherits: false; }          /* initial-value 없음 -> 규칙째 사라짐 */
@property --b { syntax: "<lengthzz>"; inherits: false; initial-value: 1px; }  /* 타입 이름 없음 -> 사라짐 */
@property a   { syntax: "*"; inherits: false; }                 /* -- 로 시작해야 한다 */
```

### 어디서 헷갈리나

- **`@property` 는 값을 정하지 않는다.** 타입과 기본값만 신고한다. 값은 여전히 보통 선언(`--x: 1px`)으로 준다.
- **`inherits` 는 생략할 수 없다.** 세 칸 중 `initial-value` 만 `syntax: "*"` 에서 면제된다.
- **등록해도 `var()` 는 그대로 쓴다.** 문법이 바뀌는 게 아니라 **값의 성질**이 바뀐다.
- **`@property` 는 캐스케이드를 안 탄다.** 같은 이름을 여러 번 선언하면 **나중 것이 이긴다**(규칙 자체는 문서 전역 등록표에 들어간다).

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `initial-value` 를 빼놓고 「등록했다」고 믿는다

실측에서 일곱 개를 선언했는데 **다섯 개만 등록됐다.** 빠진 둘은 `cssRules` 에 **아예 없다.**\
화면상 증상은 「애니메이션이 안 된다」 하나뿐이라 문법을 아무리 들여다봐도 안 보인다.\
**`[...sheet.cssRules].filter(r => r.constructor.name === "CSSPropertyRule")` 를 세어라.**

### 2. 전환이 안 되는 것과 애니메이션이 계단인 것을 같은 증상으로 본다

실측에서 **다르다.** 등록 안 한 속성은 **전환이 아예 안 걸리고**(0.25초에 이미 끝값),\
**애니메이션은 50% 에서 한 번 뒤집힌다**(49% 는 `0px`, 51% 는 `200px`).\
「계단이라도 움직인다」면 애니메이션이고, 「순간이동한다」면 전환이다 — **진단 갈림길이 여기다.**

### 3. 등록한 속성에 오타를 내고 IACVT 를 찾는다

등록하면 **IACVT 가 안 난다.** 실측에서 `--ok-len: redd` 는 `"10px"`(초기값)로 읽혔고 `width` 는 **멀쩡히 `10px`** 였다.\
「값이 왜 예상과 다르지」인데 **아무것도 안 죽어 있어서** 더 안 잡힌다. 36번의 진단 경로가 여기서는 안 통한다.

### 4. `syntax: "*"` 로 등록해 놓고 애니메이션을 기대한다

`*` 는 **타입이 없다는 신고**다. 등록은 되지만(실측: `initialValue=null` 로 담김) 중간값은 여전히 못 만든다.\
`*` 의 쓸모는 **상속을 끄는 것**(`inherits: false`)과 초기값 지정뿐이다.

### 5. `inherits` 의 기본값이 있을 거라 생각한다

없다. 세 칸 중 둘(`syntax`·`inherits`)은 항상 적어야 한다.\
또 하나 — 등록 안 한 커스텀 속성은 **언제나 상속하므로**, `inherits: false` 는 **등록해야만 얻는 기능**이다.

### 6. 계산값 출력이 달라진 것을 오류로 읽는다

실측에서 등록한 `<color>` 는 `getComputedStyle` 이 `rgb(185, 28, 28)` 로 돌려줬다. 내가 쓴 것은 `#b91c1c` 다.\
**등록하면 타입의 정규형으로 계산된다** — 오류가 아니라 등록이 됐다는 증거다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 등록하면 애니메이션·전환이 된다 | **명세**(css-properties-values-api-1 「Animation Behavior of Custom Properties」) |
| 등록 안 한 커스텀 속성이 이산 보간인 것 | **명세**(같은 절) |
| `initial-value` 가 `syntax: "*"` 외에 필수인 것 | **명세**(「The `initial-value` Descriptor」) |
| 칸이 모자라면 규칙 전체가 무효인 것 | **명세**(같은 절 + css-syntax-3 오류 복구) |
| 무효 값이 `initial-value` 로 떨어지는 것 | **명세**(「Computed Value」 — 등록 속성은 계산 시점에 타입 검사를 받는다) |
| `CSS.registerProperty` 의 예외 **종류와 메시지 문구** | **관찰**(Chrome 151). 명세는 예외 타입까지만 정하고 문구는 안 정한다 |
| 등록이 소급 적용되어 진행 중 애니메이션이 보간으로 바뀌는 것 | **관찰**(Chrome 151) |
| 계산값이 `rgb(…)` 정규형으로 나오는 것 | **명세**(계산값 정의) + 직렬화는 CSSOM |
| `rgb(107, 53, 122)` 이라는 **구체적 중간색** | **관찰** — 색 보간 공간은 구현이 고를 여지가 있다 |
| Baseline **newly**(2024-07-09) | **2차 집계**(`webstatus.dev`). 명세가 아니라 지원 현황이다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 커스텀 속성을 움직이고 싶다 | `@property` 등록 | `transition` 만 걸어 두기(안 걸린다) |
| 디자인 토큰에 타입 안전망을 두고 싶다 | `syntax` + `initial-value` | 사용처마다 `var(--x, 기본값)` 반복 |
| 부모의 토큰이 자손에 새는 것을 막고 싶다 | `inherits: false` | 자손마다 다시 덮어쓰기 |
| 그냥 색 변수 하나 | 등록 없이 보통 커스텀 속성 | 쓰지도 않을 등록 규칙 |
| 값의 모양이 매번 다르다(단축 뭉치 등) | `syntax: "*"` 또는 등록 안 함 | 억지 타입 지정 |
| 왜 등록이 안 됐는지 알아내야 한다 | `CSS.registerProperty` 로 한 번 던져 보기 | `@property` 를 눈으로 다시 읽기 |

판단 규칙 두 줄.

- **「이 값이 움직여야 하나」를 먼저 묻는다.** 움직여야 하면 등록이 **필수**이고, 아니면 대개 불필요하다.
- **등록은 문서 전역·불가역이다.** 라이브러리에서 등록한 이름과 부딪히지 않게 접두를 붙인다.

## demo — 등록 한 줄이 만드는 차이

```html demo
<div class="stage">
  <div class="bar reg">등록한 --w</div>
  <div class="bar unreg">등록 안 한 --uw</div>
</div>
<style>
  @property --w { syntax: "<length>"; inherits: false; initial-value: 40px; }
  .stage { width: 340px; padding: 8px; border: 1px solid #94a3b8; }
  .bar { height: 28px; background: #1d4ed8; color: #fff; font: 13px/28px system-ui; margin: 4px 0; overflow: hidden; }
  .reg   { --w: 40px;  width: var(--w);  transition: --w  1s linear; }
  .unreg { --uw: 40px; width: var(--uw); transition: --uw 1s linear; }
  .stage:hover .reg   { --w: 320px; }
  .stage:hover .unreg { --uw: 320px; }
</style>
```

> **보이는 것** — 테두리 상자에 마우스를 올리면 **위 막대는 1초에 걸쳐 40px 에서 320px 까지 늘어나고, 아래 막대는 그 즉시 320px 로 튄다.** 두 막대의 CSS 는 `@property` 한 줄 말고는 완전히 같다. 마우스를 떼면 둘 다 40px 로 돌아가는데, 이때도 위는 걸어서 아래는 순간이동으로 돌아간다.\
> **바꿔 볼 것** — `@property` 블록을 지우면 → **위 막대도 아래처럼 순간이동한다** · `syntax: "<length>"` → `syntax: "*"` 로 바꾸면 → **역시 순간이동한다**(타입이 없으면 중간값이 없다)

*(Chrome 151 headless 실측, CDP 로 실제 마우스 입력: 호버 전 `["40px","40px"]` → +0.25s `["114.656px","320px"]` → +0.5s `["184.656px","320px"]` → +0.75s `["254.656px","320px"]` → +1.2s `["320px","320px"]` → 뗀 뒤 1.5s `["40px","40px"]`.)*

## 핵심 문장

- **`@property` 는 커스텀 속성에 타입을 붙이는 신고서**다. 칸은 `syntax`·`inherits`·`initial-value` 셋뿐이다.
- **등록하면 애니메이션이 된다.** 실측에서 등록한 색은 50% 에 `rgb(107, 53, 122)` 라는 중간색이 나왔고, 등록 안 한 색은 **49%까지 시작값, 51%부터 끝값**이었다.
- **전환은 계단조차 없다.** 등록 안 한 속성에 `transition` 을 걸면 **전환이 아예 생성되지 않는다**(실측: 0.25초에 이미 끝값).
- **`initial-value` 는 `syntax: "*"` 말고는 필수**다. 빼면 **규칙 전체가 조용히 사라진다**(실측: 7개 중 5개만 등록됨).
- **등록하면 무효 값이 IACVT 가 아니라 `initial-value` 로 떨어진다.** 쓰는 쪽은 안 죽는다 — 36번의 진단 경로가 안 통한다.
- **`CSS.registerProperty` 는 예외를 던진다.** CSS 에는 에러가 없지만 **JS API 에는 있다** — 진단은 이쪽으로 한다.
- **등록은 문서 전역이고 소급 적용된다.** 실측에서 등록 직후 진행 중이던 애니메이션이 `200px` → `100px` 로 바뀌었다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 37번)
- [목록의 **36번 주제**](../36-custom-properties/)(사용자 정의 속성) — **커스텀 속성 자체와 IACVT 의 정본.**\
  「`var()`·대체값·상속은 어떻게 도나」는 거기, 여기는 **「등록하면 무엇이 달라지나」만**.
- [`../07-syntax-and-error-recovery/2-summary.md`](../07-syntax-and-error-recovery/2-summary.md) — **오류 복구의 정본.**\
  `@property` 규칙이 칸 하나 때문에 **통째로** 사라지는 것은 거기의 「모르는 at-rule 은 블록까지」와 같은 규칙이다.
- [`../04-value-processing-stages/2-summary.md`](../04-value-processing-stages/2-summary.md) — 지정값 → 계산값 네 단계.\
  등록은 **계산값 단계에 타입 검사를 끼워 넣는 것**이다.
- [`../03-inheritance-and-global-keywords/2-summary.md`](../03-inheritance-and-global-keywords/2-summary.md) — 상속의 정본.\
  `inherits: false` 가 **등록해야만 얻는 기능**인 이유가 거기 있다.
- [`../52-transition/2-summary.md`](../52-transition/2-summary.md) — 전환의 정본. 「보간할 수 없는 값은 전환이 시작조차 안 한다」가 거기.
- [`../41-supports-feature-queries/2-summary.md`](../41-supports-feature-queries/2-summary.md) — `CSS.supports('at-rule(@property)')` 로 지원을 묻는 방법.
- [목록의 **53번 주제**](../53-keyframes-and-animation/)(애니메이션) — 키프레임·이산 보간의 정본. 여기는 **등록 여부가 만드는 차이**만.

## 용어 풀이

- **`@property`** — 커스텀 속성의 타입·상속·초기값을 신고하는 at-rule.
- **등록 커스텀 속성(registered custom property)** — 타입이 신고된 `--` 속성. 계산값이 타입의 정규형이 된다.
- **`syntax`** — 받을 수 있는 값의 타입 문자열. `"<length>"`·`"<color>"`·`"auto | <length>"`·`"*"` 등.
- **`inherits`** — 자손에게 내려갈지. 생략 불가.
- **`initial-value`** — 아무도 안 정했을 때의 값. `syntax: "*"` 외에는 필수.
- **보간(interpolation)** — 두 값 사이의 중간값을 만드는 것. 타입을 알아야 가능하다.
- **이산 보간(discrete interpolation)** — 중간값이 없는 타입의 기본 동작. 50% 에서 한 번 뒤집힌다.
- **IACVT(invalid at computed-value time)** — 파싱은 됐는데 계산 시점에 무효가 되는 값. 등록하면 **이게 안 난다.**
- **`CSS.registerProperty()`** — 같은 등록을 하는 JS API. 틀리면 **예외를 던진다.**
- **`CSSPropertyRule`** — `@property` 규칙의 CSSOM 타입. `name`·`syntax`·`inherits`·`initialValue` 를 읽을 수 있다.
- **Baseline newly** — 주요 브라우저 최신판에 다 들어왔지만 아직 널리(30개월) 퍼지지는 않은 상태.

## 더 들어가면

- **그라데이션 각도 애니메이션이 대표 용례**다. `@property --angle { syntax: "<angle>"; … }` 를 등록하고 `conic-gradient(from var(--angle), …)` 을 돌리면 **회전하는 테두리**가 CSS 만으로 된다. 등록 없이는 각도가 이산 보간이라 안 돈다.
- **`@property` 는 컨테이너 스타일 쿼리와 맞물린다.** 실측에서 `@container style(--ang: 45deg)` 가 등록한 `<angle>` 속성에 대해 정상 동작했다([40번 주제](../40-container-and-style-queries/2-summary.md)).
- **왜 커스텀 속성이 처음부터 타입을 안 가졌나** — 설계 의도가 「**뜻은 쓰는 쪽이 정한다**」였기 때문이다. 토큰 뭉치로 두면 단축 속성 조각·조건부 값 같은 것도 담을 수 있다. `@property` 는 그 자유를 **버리는 대신** 타입을 얻는 선택지다.
- **Houdini 의 일부로 시작했다.** Properties and Values API 는 Paint/Layout Worklet 과 같은 묶음에서 나왔고, 그중 **가장 먼저 널리 구현된 조각**이다.
