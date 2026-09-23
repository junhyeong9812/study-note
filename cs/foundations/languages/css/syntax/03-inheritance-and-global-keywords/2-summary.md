# css/syntax/03 — 상속: 상속되는 속성과 `inherit`/`initial`/`unset`/`revert`/`revert-layer` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Cascading and Inheritance Level 5](https://drafts.csswg.org/css-cascade-5/) 의 「Inheritance」·「Defaulting」(`initial`/`inherit`/`unset`/`revert`/`revert-layer`) 절. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 값은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getComputedStyle` 로 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 그대로 적어 두었다.\
> **엔진은 Chrome 하나다.** 이 머신의 Firefox 155.0.1 은 headless 스크린샷이 산출되지 않고, WebKit 은 아예 없다 — 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — CSS 에는 언어 버전이 없다. `inherit` 은 CSS1, `initial` 은 CSS3, `unset`·`revert` 는 css-cascade-4, `revert-layer` 는 css-cascade-5 에서 들어왔다. 실행 확인은 Chrome 151 한 판이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**상속 = 아무도 지원하지 않은 자리에만 부모 것이 내려오는 것이다.**

가업 승계에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 가업 | 부모 요소의 **계산값** 하나 (`color: #b91c1c`) |
| 자식이 자기 일을 정했다 | 그 속성에 선언이 하나라도 걸렸다 → 캐스케이드가 이겼다 |
| 자식이 아무것도 안 정했다 | 그 속성 바구니가 비었다 → **그때만** 가업이 내려온다 |
| 가업이 원래 없는 집 | 상속되지 않는 속성(`border`·`padding`·`background`) |
| 「아버지 것 그대로 주세요」 | `inherit` — 상속 안 되는 속성에도 강제로 내려받는다 |

- 상속은 **싸워서 이기는 게 아니다.** 자식에게 선언이 하나라도 있으면 그 선언이 아무리 약해도 상속은 **일어나지 않는다**. 비교 자체가 없다.
- 그래서 「상속보다 센 선언」이라는 말은 성립하지 않는다.
- 그리고 **모든 속성이 가업을 가진 것은 아니다.** `color` 는 내려오고 `border` 는 안 내려온다. 이 갈림이 이 주제의 절반이다.

```text
자식 요소의 color 바구니를 들여다본다

  후보가 하나라도 있다        후보가 하나도 없다
  +--------------------+      +--------------------+
  | p { color: green } |      |      (비어 있음)   |
  +--------------------+      +--------------------+
          ↓                            ↓
   캐스케이드가 승자를 뽑는다     상속되는 속성인가?
          ↓                       ├─ 예  → 부모의 계산값
     color = green                └─ 아니오 → 그 속성의 초기값
```

실무에서 이게 터지는 자리는 **컴포넌트를 「초기화」할 때**다.\
`all: initial` 로 깨끗이 지웠더니 글꼴까지 사라지고, `all: unset` 으로 지웠더니 버튼이 버튼처럼 안 보인다.\
둘 중 무엇을 써야 하는지는 「**무엇으로 되돌리려는가**」가 정한다 — 초기값인가, 브라우저 기본 스타일인가, 부모 값인가.

> **상속(inheritance)** — 자식 요소의 어떤 속성에 선언이 하나도 없을 때, 부모 요소의 그 속성 **계산값**을 그대로 쓰는 것.\
> 예: `body { color: red }` 만 써도 안쪽 모든 글자가 빨개지는 것.

> **초기값(initial value)** — 명세가 속성마다 정해 둔 값. 스타일시트가 하나도 없어도 그 속성이 갖는 값.\
> 예: `display` 의 초기값은 `inline`, `color` 의 초기값은 `canvastext`(Chrome 151 에서 `rgb(0, 0, 0)` 으로 나온다).

> **사용자 에이전트 스타일시트(UA stylesheet)** — 브라우저가 내장한 기본 시트. `div { display: block }`·`strong { font-weight: bolder }` 같은 것이 여기 있다.\
> 예: `<a>` 가 파랗고 밑줄이 있는 것은 내가 안 썼는데도 있는 것 — 이 시트가 준 값이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 속성이 내려오고 어떤 속성이 안 내려오는가.** 그리고 「내려온 것처럼 보이는데 아닌 것」은 무엇인가.
2. 다섯 전역 키워드가 각각 **어디로 되돌리는가.** 특히 `initial` 과 `revert` 는 언제 같고 언제 갈리는가.
3. `all: unset` 과 `all: revert` 는 **결과가 어떻게 다른가.** 컴포넌트 초기화에 무엇을 써야 하는가.

## 동작 방식

### (1) 상속이 일어나는 자리 — 캐스케이드가 끝난 다음

**언제 쓰나** — 모든 요소의 모든 속성마다. 캐스케이드([01번 주제](../01-cascade-and-priority/2-summary.md))가 승자를 뽑은 **뒤**에 돈다.

```text
① 캐스케이드   이 속성에 걸린 선언 중 하나를 뽑는다     ← 01번이 정본
                    ↓
② 채워 넣기    뽑힌 게 없으면 여기서 값을 만든다        ← 이 주제
                    상속되는 속성  → 부모의 계산값
                    아닌 속성      → 초기값
                    ↓
③ 키워드 해소  뽑힌 값이 inherit/initial/unset/revert 면
                    그것을 ②와 같은 방식으로 실제 값으로 바꾼다
                    ↓
④ 계산값 확정  이 값이 계산값이 되고, 자식의 ②가 이것을 읽는다   ← 04번이 정본
```

그림 해설 (한 단계씩):

- ②는 **비어 있을 때만** 돈다. 자식에게 `color: inherit` 조차 아닌 아무 약한 선언이 있으면 ②는 건너뛴다.
- ③이 이 주제의 본체다. 다섯 키워드는 **②의 동작을 명시적으로 불러 쓰는 장치**다.\
  `unset` 이 「상속되면 inherit, 아니면 initial」인 것은 ②를 글자 그대로 옮긴 것이다.
- ④가 중요하다 — 자식이 물려받는 것은 부모의 **계산값**이지 부모가 쓴 글자가 아니다([04번 주제](../04-value-processing-stages/2-summary.md)가 정본).

비용 — 없음(판정 순서다). 대신 상속은 **트리를 타고 내려가므로** 부모에 한 줄 쓰면 그 아래 전부가 영향을 받는다. 그것이 장점이자 사고의 원인이다.

### (2) 무엇이 상속되나 — 글자에 관한 것, 상자에 관한 것

**언제 쓰나** — 「부모에 썼는데 왜 안 내려오지」를 진단할 때.

경계선은 대체로 **글자냐 상자냐**로 갈린다. 실측으로 확인한 표다.

```text
부모(#par)에 한 번에 다 선언하고 자식(#kid)에서 읽어 봤다

  내려온 것                            안 내려온 것
  +------------------------------+     +------------------------------+
  | color         #b91c1c        |     | border-top-width   0px       |
  | font-family   Georgia, serif |     | border-top-style   none      |
  | line-height   (아래 참고)    |     | padding-top        0px       |
  | text-align    right          |     | background-color   투명      |
  | visibility    visible        |     | text-decoration-line none    |
  | cursor        help           |     | opacity            1         |
  | letter-spacing 3px           |     | display            block(UA) |
  | list-style-type disc         |     |                              |
  | white-space   normal         |     |                              |
  | word-spacing / text-transform |    |                              |
  +------------------------------+     +------------------------------+
   글자·문단·목록 표시에 관한 것        상자·배경·테두리에 관한 것
```

그림 해설 (한 단계씩):

- 외울 것은 목록이 아니라 **기준**이다 — *「이 값이 트리 전체에 퍼지는 게 자연스러운가」*.\
  글꼴·색·줄높이는 퍼지는 게 자연스럽고, 테두리·여백·배경은 요소마다 따로 정하는 게 자연스럽다.
- `visibility` 와 `cursor` 는 상자 쪽처럼 보이는데 **상속된다.** 둘 다 「이 가지 전체에 걸린다」는 뜻이라서다.
- `opacity` 는 상속되지 **않는다.** 부모가 0.5 면 자식도 흐려 보이지만 그건 상속이 아니라 **부모 그룹을 통째로 합성**한 결과다 — 자식의 `opacity` 계산값은 `1`이다.

**★ 상속처럼 보이는데 아닌 것 셋** — 이 주제에서 가장 자주 틀리는 자리다.

```text
①  border-color 가 부모 색을 따라간다                실측: kid border-top-color = rgb(185, 28, 28)
    -> 상속이 아니다. 초기값이 currentColor 이고
       currentColor 가 그 요소의 color 로 해소된 것뿐이다

②  자식 p 의 width 가 부모와 같다                    실측: kid width = 300px (부모 content 폭)
    -> 상속이 아니다. width 초기값 auto 가 블록에서
       「부모 content 폭을 채운다」로 사용된 것이다

③  text-decoration 밑줄이 자식 글자에도 그어진다      실측: kid text-decoration-line = none
    -> 상속이 아니다. 조상이 그은 선이 자손 글자 위를
       지나갈 뿐이라, 자식의 계산값은 none 이다
```

비용 — 없음. 다만 ①·②·③은 **개발자 도구에서도 「상속됨」으로 안 보이므로** 값을 직접 읽어야 구분된다.

> **`currentColor`** — 「그 요소의 `color` 계산값」을 가리키는 키워드. `border-color`·`outline-color`·`box-shadow` 색의 초기값이다.\
> 예: `border: 1px solid` 라고 색을 안 적으면 글자색과 같은 색 테두리가 나온다.

### (3) 네 키워드 — 같은 속성에 넷을 나란히 걸어 본다

**언제 쓰나** — 물려받은 값을 끊거나, 되돌리고 싶을 때.

| 키워드 | 무엇으로 되돌리나 | 상속되는 속성에서 | 상속 안 되는 속성에서 |
|---|---|---|---|
| `inherit` | **부모의 계산값** | 부모 값 | 부모 값 *(강제로 내려받는다)* |
| `initial` | **명세의 초기값** | 초기값 | 초기값 |
| `unset` | 상속되면 `inherit`, 아니면 `initial` | 부모 값 | 초기값 |
| `revert` | **이 출처의 선언을 없앤 셈 치고 아래 출처의 값** | 아래 출처 값 · 없으면 상속 | 아래 출처 값 · 없으면 초기값 |
| `revert-layer` | 이 **레이어**의 선언을 없앤 셈 치고 앞 레이어의 값 | 〃 (레이어 단위) | 〃 (레이어 단위) |

`.box`(부모)가 빨강, `.t`(자식들)가 초록으로 깔려 있는 판에 넷을 걸고 읽은 값이다.

```text
  .box { color:#b91c1c; border:4px solid #1d4ed8 }     부모
  .t   { color:#15803d; border:4px solid #15803d }     자식 공통

  키워드      color 결과          border-color 결과
  ---------   -----------------   ------------------------------
  inherit     rgb(185,28,28) 빨    rgb(29,78,216) 파  <- 부모의 파란 테두리를 강제로 받았다
  initial     rgb(0,0,0)     검    rgb(0,0,0)     검  <- currentColor 가 검정 color 를 가리킨다
  unset       rgb(185,28,28) 빨    rgb(185,28,28) 빨  <- border-color 는 initial=currentColor=빨강
  revert      rgb(185,28,28) 빨    rgb(185,28,28) 빨  <- UA 시트에 p 의 color/border-color 가 없다
```

그림 해설 (한 단계씩):

- **`inherit` 은 상속 안 되는 속성에도 통한다.** 테두리 색이 부모의 파랑을 받아 갔다 — 상속 여부와 무관하게 「부모 계산값」을 가져온다.
- `initial` 의 두 칸이 둘 다 검정인 이유는 **`border-color` 의 초기값이 `currentColor`** 라서다. `color` 가 먼저 검정이 되니 테두리도 검정이 된다.
- 이 표에서 **`unset` 과 `revert` 가 같은 값을 냈다.** 우연이 아니라 조건이다 — *UA 시트가 `p` 의 `color`·`border-color` 를 건드리지 않기 때문*이다. 그 조건이 깨지는 자리가 다음 절이다.

```html demo
<p class="row">
  <strong class="w1">기본</strong>
  <strong class="w2">revert</strong>
  <strong class="w3">initial</strong>
  <strong class="w4">unset</strong>
</p>
<style>
  .row { font: 20px/1.8 system-ui, sans-serif; }
  .w2 { font-weight: revert; }
  .w3 { font-weight: initial; }
  .w4 { font-weight: unset; }
</style>
```

> **보이는 것** — 「기본 revert」 두 낱말만 **굵게** 나오고 「initial unset」 두 낱말은 **보통 굵기**로 나온다. `<strong>` 의 굵기는 UA 시트가 준 것이라 `revert` 는 그대로 굵고, `initial` 은 명세 초기값 `normal` 로, `unset` 은 `font-weight` 가 상속 속성이므로 부모(`p`)의 `normal` 로 간다.\
> **바꿔 볼 것** — `.row` 에 `font-weight: 700` 을 추가하면 → **`unset` 이 부모의 `700` 을 받아 굵어지고 `initial` 만 `400` 으로 남는다.** 덤으로 `기본`·`revert` 는 `900` 이 된다 — UA 시트의 `bolder` 가 부모 `700` 기준으로 다시 풀리기 때문이다

*(Chrome 151 headless 실측: `.w1` `700` · `.w2` `700` · `.w3` `400` · `.w4` `400`. 스크린샷으로도 굵기 두 낱말/두 낱말을 확인했다.\
부모에 `font-weight: 700` 을 준 판도 따로 던졌다 — `900` · `900` · `400` · `700`.)*

### (4) ★ `revert` 와 `initial` 이 갈리는 자리 — UA 시트가 값을 가진 속성

**언제 쓰나** — 브라우저 기본 모양을 되살리고 싶을 때. 이 주제에서 **가장 값어치 있는 절**이다.

`initial` 은 **명세**로 돌아가고 `revert` 는 **브라우저 기본 시트**로 돌아간다.\
UA 시트가 그 속성을 건드리지 않는 속성에서는 둘이 같고, 건드리는 속성에서는 **완전히 다른 값**이 나온다.

```text
같은 선언을 revert / initial 로만 바꿔 읽은 값 (Chrome 151)

  요소·속성                      revert          initial      갈리나
  -----------------------------  --------------  -----------  ------
  div   display                  block           inline       ★ 갈린다
  li    display                  list-item       inline       ★ 갈린다
  strong font-weight             700             400          ★ 갈린다
  p     margin-top               16px            0px          ★ 갈린다
  a     text-decoration-line     underline       none         ★ 갈린다
  a     color                    rgb(0,0,238)    rgb(0,0,0)   ★ 갈린다
  p     color                    (상속값)        rgb(0,0,0)   같을 수도
  p     border-top-color         (상속 color)    (상속 color) 같다
```

그림 해설 (한 단계씩):

- **`display: initial` 은 `block` 이 아니라 `inline` 이다.** 이것 하나만 외워도 절반은 산다 —\
  `display` 의 명세 초기값은 `inline` 이고, `div` 가 블록인 것은 **UA 시트가 그렇게 써 뒀기 때문**이다.
- `li { display: initial }` 은 `list-item` 을 잃어 **목록 마커가 사라진다.** `revert` 면 남는다.
- `a { color: initial }` 은 링크색을 잃고, `revert` 는 브라우저의 링크색 `rgb(0, 0, 238)` 로 돌아온다.\
  이 값은 **Chrome 151 의 UA 시트 값이며 브라우저마다 다를 수 있다** — 관찰이지 보장이 아니다.
- 그래서 판단 규칙은 한 줄이다 — **「내 시트를 안 쓴 것처럼」은 `revert`, 「명세 기본값」은 `initial`.**

> **`revert`** — 그 선언이 속한 **출처**(작성자 시트)의 선언이 없었던 셈 치고 캐스케이드를 다시 판정하게 하는 키워드.\
> 예: 작성자 시트에서 `display: revert` 라고 쓰면 UA 시트의 값(`div` 면 `block`)이 남는다.

비용 — 없음. 다만 `revert` 의 결과는 **브라우저의 UA 시트에 달려 있으므로** 브라우저마다 다를 수 있다. 값을 단정하고 싶으면 `initial` 이나 구체 값을 쓴다.

### (5) `all` — 한 번에 전부 되돌리기

**언제 쓰나** — 서드파티 위젯이나 버튼을 **스타일이 없는 상태로 만들 때.**

`all` 은 전역 키워드 **다섯만** 받는 특수 단축이다(`direction`·`unicode-bidi` 는 제외). 같은 버튼 셋에 걸어 읽은 값이다.

```text
  .bar { color:#b91c1c; font-family:Georgia,serif; font-size:18px }   부모

  속성              기본 button      all: unset        all: revert
  ----------------  ---------------  ----------------  ---------------
  display           inline-block     inline            inline-block
  color             rgb(0,0,0)       rgb(185,28,28)    rgb(0,0,0)
  font-family       Arial            Georgia, serif    Arial
  font-size         13.3333px        18px              13.3333px
  border-top-style  outset           none              outset
  background-color  rgb(239,239,239) rgba(0,0,0,0)     rgb(239,239,239)
  padding-top       1px              0px               1px
```

```html demo
<div class="bar">
  <button class="p">기본</button>
  <button class="u">all: unset</button>
  <button class="r">all: revert</button>
</div>
<style>
  .bar { color: #b91c1c; font-family: Georgia, serif; font-size: 18px; }
  .u { all: unset; }
  .r { all: revert; }
</style>
```

> **보이는 것** — 첫째와 셋째는 **똑같은 회색 테두리 버튼**으로 보이고, 가운데만 **버튼 껍데기가 사라져 부모의 빨간 Georgia 글자**로 보인다. `all: revert` 는 UA 시트로 돌아가므로 기본 버튼과 픽셀 단위로 같은 값이 되고, `all: unset` 은 상속되는 속성만 부모에서 받아 와 「글자만 남는다」.\
> **바꿔 볼 것** — `all: unset` → `all: initial` 로 바꾸면 → **글자색이 검정, 글꼴도 부모의 Georgia 가 아니라 브라우저 기본 글꼴**이 된다(상속마저 끊기므로)

*(Chrome 151 headless 실측: 위 표가 그 출력이다. `all: revert` 행과 기본 버튼 행이 일곱 속성 전부 같은 값이었다. 스크린샷으로 버튼 모양도 확인했다.)*

그림 해설 (한 단계씩):

- **`all: unset` 은 「지우개」가 아니다.** 상속되는 속성은 부모 값으로 *채워진다* — 글꼴과 색은 남는다.
- **`all: initial` 은 지나치게 세다.** `font-family` 까지 브라우저 기본으로 바꿔 버려서 컴포넌트가 문서와 따로 논다.
- **`all: revert` 는 「내 시트를 안 썼더라면」이다.** 버튼은 다시 버튼이 된다 — 폼 컨트롤을 되살릴 때 쓸 유일한 것이다.

비용 — `all` 은 **모든 속성을 건드린다.** `transition`·`animation`·커스텀 속성 계열까지 되돌아가므로, 범위를 좁힐 수 있으면 개별 속성을 쓰는 쪽이 안전하다.

### (6) `revert-layer` — 출처가 아니라 레이어 한 칸을 되돌린다

**언제 쓰나** — `@layer` 를 쓰는 문서에서 **앞 레이어의 값**으로 돌아가고 싶을 때. 레이어 자체는 [05번 주제](../05-cascade-layers/2-summary.md)가 정본이다.

```text
@layer base, theme;
@layer base  { .r1 { color:#b91c1c } }
@layer theme { .r1 { color: revert-layer } }     -> 실측 rgb(185,28,28)  base 의 빨강

@layer base  { .r2 { color:#b91c1c } }
@layer base  { .r2 { color: revert-layer } }     -> 실측 rgb(0,0,0)
                                                     같은 레이어의 선언까지 같이 지워진다
.r3 { color:#15803d }
.r3 { color: revert-layer }                      -> 실측 rgb(0,0,0)
                                                     레이어 밖에서는 revert 와 같아진다
```

그림 해설 (한 단계씩):

- `revert-layer` 가 지우는 것은 **그 선언 하나가 아니라 그 레이어의 그 속성 선언 전부**다. `.r2` 가 검정이 된 이유가 이것이다.
- **레이어 밖에서 쓰면 `revert` 와 같다** — 앞 레이어가 없으므로 출처를 통째로 되돌린다(`.r3`).
- 앞 레이어가 없고 UA 시트도 없으면 결국 상속·초기값으로 떨어진다.

비용 — 없음. 다만 「어느 레이어에서 쓴 `revert-layer` 인가」에 결과가 통째로 달려 있어서, 레이어 순서를 모르면 읽을 수 없는 코드가 된다.

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
.a { color: inherit; }            /* 부모의 계산값 */
.b { color: initial; }            /* 명세 초기값 */
.c { color: unset; }              /* 상속되면 inherit, 아니면 initial */
.d { color: revert; }             /* 아래 출처의 값 */
.e { color: revert-layer; }       /* 앞 레이어의 값 */
.f { all: revert; }               /* 모든 속성에 한 번에 */
```

- 다섯 키워드는 **모든 CSS 속성에 쓸 수 있다**(커스텀 속성 포함).
- **값의 일부로는 못 쓴다.** `margin: 10px inherit` 은 무효이고, 그 선언 하나가 통째로 버려진다([07번 주제](../07-syntax-and-error-recovery/2-summary.md)).
- 대소문자를 가리지 않는다(`INHERIT` 도 같다).

### 금지 사례 — 무효라 조용히 버려지는 것

```css
.x { margin: 10px inherit; }      /* 무효 — 전역 키워드는 값 전체여야 한다 */
.y { color: initial red; }        /* 무효 — 같은 이유 */
.z { all: red; }                  /* 무효 — all 은 전역 키워드만 받는다 */
```

**에러는 안 난다.** 선언 하나가 사라지고 그 자리는 이전 값 그대로 남는다 — 07번이 정본이다.

### 어디서 헷갈리나 — 이름이 비슷한 넷

- `initial` 은 「초기값」이지 **「브라우저 기본」이 아니다.** 브라우저 기본은 `revert` 다.
- `unset` 은 독립된 값이 아니라 **`inherit` 과 `initial` 중 하나로 가는 갈림길**이다.
- `revert` 는 「한 칸 아래 출처」이지 **「전부 지움」이 아니다.**
- `revert-layer` 는 레이어 단위, `revert` 는 출처 단위 — **단위가 다르다.**

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `display: initial` 이 `block` 일 거라 생각한다

```text
의도                                실제 (Chrome 151 실측)
+--------------------------+       +--------------------------+
| div { display: initial } |       | display = inline         |
| "원래대로 블록"          |       | 명세 초기값이 inline 이다 |
+--------------------------+       +--------------------------+
                                     원래대로 = revert  -> block
```

`li` 에서는 더 아프다 — `initial` 이면 `list-item` 을 잃어 **마커가 사라진다**(실측 `inline`).

### 2. `all: initial` 로 컴포넌트를 초기화한다

글꼴까지 브라우저 기본으로 바뀐다. 문서 전체가 한 글꼴인데 그 컴포넌트만 다른 글꼴이 되고,\
**「글꼴이 왜 이러지」를 `font-family` 부터 찾게 된다.** 원인은 `all` 이다.

### 3. 상속 안 되는 속성에 `inherit` 을 쓰면 무효일 거라 생각한다

유효하다. `border-color: inherit` 은 **부모의 테두리색을 강제로 가져온다**(실측 `rgb(29, 78, 216)`).\
「상속되는 속성만 `inherit` 을 쓴다」는 규칙은 없다.

### 4. `border-color` 가 상속된다고 생각한다

```text
부모 color #b91c1c · 자식은 테두리 색을 안 적었다
  자식 border-top-color = rgb(185, 28, 28)     빨강이 내려왔다?

  아니다. border-color 의 초기값이 currentColor 이고
  자식의 color 가 상속으로 빨강이 되었을 뿐이다.
  부모의 border-color(#1d4ed8 파랑)는 내려오지 않았다.  <- 이게 증거다
```

실측에서 부모 테두리는 **파랑**인데 자식 테두리는 **빨강**이었다. 상속이면 파랑이 나와야 한다.

### 5. `revert-layer` 를 같은 레이어 안에서 쓰고 앞 선언이 남을 줄 안다

`@layer base { .r2 { color: red } .r2 { color: revert-layer } }` 는 **빨강이 남지 않는다**(실측 검정).\
지워지는 것은 「앞 선언」이 아니라 **그 레이어의 그 속성 선언 전부**다.

### 6. 「상속을 이겼다」고 설명한다

자식에게 선언이 있으면 상속은 **애초에 일어나지 않는다.** 이긴 게 아니라 비교가 없었던 것이다.\
그래서 **상속되는 속성을 `*` 로 선언하면 그 속성의 상속이 통째로 끊긴다** — 모든 요소가 자기 후보를 하나씩 갖게 되어, 나중에 부모에 쓴 값이 아무 데도 안 내려온다.

```text
* { font-family: "DejaVu Sans", sans-serif; }     모든 요소에 후보가 하나씩 생겼다
.card { font-family: Georgia, serif; }            .card 에만 걸린다

실측:  .card  font-family = Georgia, serif
      .inner font-family = "DejaVu Sans", sans-serif    <- 안 내려왔다
```

`* { box-sizing: border-box }` 가 같은 문제를 안 일으키는 이유는 간단하다 — **`box-sizing` 은 원래 상속되지 않는다.** 끊을 상속이 없다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 「상속되는 속성 / 아닌 속성」의 구분 | **명세** — 속성마다 「Inherited: yes/no」가 정해져 있다 |
| 다섯 키워드가 무엇으로 되돌리는지 | **명세**(css-cascade-5 「Defaulting」) |
| `display` 초기값 `inline` · `font-weight` 초기값 `normal` | **명세** |
| `div` 가 `block`, `strong` 이 굵음, `p` 마진 `16px` | **UA 시트** — 브라우저 구현이다. 다른 브라우저는 다를 수 있다 |
| 링크색 `rgb(0, 0, 238)` | **Chrome 151 의 UA 시트 값.** 관찰이지 보장이 아니다 |
| `color: initial` 이 `rgb(0, 0, 0)` | **관찰.** 명세 초기값은 `canvastext` 이고 그 해소는 환경에 달려 있다 |
| `all: revert` 한 버튼이 기본 버튼과 같아 보이는 것 | **관찰**(일곱 속성 대조). 「모든 속성이 같다」고는 확인하지 않았다 |

**★ `revert` 를 쓰는 코드는 브라우저 기본 시트에 의존한다.** 이 주제에서 명세와 구현이 갈리는 유일한 자리이고, 크로스 브라우저 확인이 필요한 것도 여기뿐이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 폼 컨트롤을 브라우저 기본으로 되살린다 | `all: revert` | `all: initial`(버튼이 인라인 글자가 된다) |
| 서드파티 위젯의 내 스타일을 걷어낸다 | `all: revert` 또는 레이어 + `revert-layer` | `!important` 로 덮기 |
| 아이콘 색을 글자색에 맞춘다 | `currentColor` | `color: inherit` 을 SVG 마다 반복 |
| 상속된 값만 끊고 싶다 | 그 속성에 구체 값 또는 `initial` | `all: unset`(상속이 그대로 남는다) |
| 다크 모드에서 테마 레이어만 무르고 싶다 | `revert-layer` | `initial`(테마 이전 값까지 날아간다) |
| 표에서 부모 글꼴을 물려받고 싶다 | `font: inherit` | 부모 `font-family` 를 복사해 적기 |

판단 규칙 두 줄.

- **「무엇으로 되돌리려는가」를 먼저 말로 정한다** — 부모(`inherit`) · 명세(`initial`) · 브라우저(`revert`) · 앞 레이어(`revert-layer`).
- **`all` 은 마지막 수단이다.** 되돌릴 속성을 셀 수 있으면 세어서 적는다.

## 핵심 문장

- 상속은 **바구니가 비었을 때만** 일어난다 — 자식에게 선언이 있으면 아무리 약해도 상속은 일어나지 않고, 「이겼다」는 표현 자체가 성립하지 않는다.
- 자식이 물려받는 것은 부모가 **쓴 글자가 아니라 부모의 계산값**이다(`em` 은 부모 자리에서 이미 픽셀이 되어 내려온다 — 04번).
- `unset` 은 **②단계를 글자 그대로 부른 것**이다 — 상속되면 `inherit`, 아니면 `initial`.
- **`initial` 은 명세로, `revert` 는 브라우저 기본 시트로 돌아간다.** `display`·`font-weight`·`margin`·링크색처럼 UA 시트가 값을 가진 속성에서 둘은 완전히 다른 값을 낸다.
- **`all: unset` 은 글자만 남기고, `all: revert` 는 버튼을 다시 버튼으로 만든다.** 컴포넌트 초기화의 정답은 대개 뒤쪽이다.
- `border-color` 가 부모 색을 따라가는 것은 상속이 아니라 **`currentColor` 초기값**이다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 03번) · 「버전·지원 기준」의 Baseline 표
- [`../01-cascade-and-priority/2-summary.md`](../01-cascade-and-priority/2-summary.md) — **캐스케이드 6단계와 출처·`!important` 사다리의 정본.**\
  그쪽은 「선언 여럿 중 누가 이기나」까지, 여기는 **「아무도 없을 때 무엇이 채워지나」부터**다.
- [`../02-specificity/2-summary.md`](../02-specificity/2-summary.md) — **명시도 계산의 정본.** 이 문서는 명시도를 계산하지 않는다.
- [`../04-value-processing-stages/2-summary.md`](../04-value-processing-stages/2-summary.md) — 상속되는 것이 **왜 계산값인가**. `em`·`%` 가 언제 픽셀이 되는지는 거기가 정본이다.
- [`../05-cascade-layers/2-summary.md`](../05-cascade-layers/2-summary.md) — `revert-layer` 가 돌아가는 「앞 레이어」의 정의와 레이어 순서 규칙
- [`../07-syntax-and-error-recovery/2-summary.md`](../07-syntax-and-error-recovery/2-summary.md) — `margin: 10px inherit` 처럼 무효한 전역 키워드가 **조용히 버려지는** 규칙
- [목록의 **33번 주제**](../33-length-units/)(길이 단위) — `em` 이 무엇을 기준으로 삼는지
- [목록의 **36번 주제**](../36-custom-properties/)(사용자 정의 속성) — 커스텀 속성은 **항상 상속되고** 무효 시 동작이 따로 있다(IACVT)
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙
- [`history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) — **언제 이렇게 됐나는 거기.** 여기는 오늘의 규칙만

## 용어 풀이

- **상속(inheritance)** — 자식의 어떤 속성에 선언이 하나도 없을 때 부모의 그 속성 계산값을 쓰는 것.
- **상속되는 속성(inherited property)** — 명세가 「Inherited: yes」로 정한 속성. 대체로 글자·문단에 관한 것.
- **초기값(initial value)** — 명세가 속성마다 정해 둔 값. 스타일시트가 없어도 갖는 값.
- **사용자 에이전트 스타일시트(UA stylesheet)** — 브라우저 내장 기본 시트. `div{display:block}` 같은 것이 여기 있다.
- **`inherit`** — 부모의 계산값을 쓴다. 상속 안 되는 속성에도 쓸 수 있다.
- **`initial`** — 명세 초기값으로 되돌린다.
- **`unset`** — 상속되면 `inherit`, 아니면 `initial`.
- **`revert`** — 이 출처의 선언이 없었던 셈 치고 아래 출처(대개 UA 시트)의 값으로.
- **`revert-layer`** — 이 레이어의 선언이 없었던 셈 치고 앞 레이어의 값으로. 레이어 밖에서는 `revert` 와 같다.
- **`all`** — 전역 키워드 다섯만 받는 단축. `direction`·`unicode-bidi` 를 뺀 모든 속성에 한꺼번에 건다.
- **`currentColor`** — 그 요소의 `color` 계산값을 가리키는 키워드. `border-color` 등의 초기값.
- **계산값(computed value)** — 상속되는 값의 단위. 자세한 것은 04번.
- **전역 키워드(CSS-wide keyword)** — 모든 속성이 받는 다섯 키워드의 총칭.

## 더 들어가면

- **커스텀 속성은 예외적으로 전부 상속된다.** `--brand` 를 `:root` 에 한 줄 쓰면 문서 전체가 읽을 수 있는 것이 그 때문이다.\
  `@property` 로 등록하면 `inherits: false` 로 끌 수 있다([목록의 **36번 주제**](../36-custom-properties/)·**37번 주제**).
- **상속은 DOM 트리를 타지 플랫 트리를 탄다.** `display: contents` 로 상자를 없앤 요소도 **상속은 그대로 통과시킨다** — 상자가 없어졌다고 상속이 끊기지 않는다([목록의 **16번 주제**](../16-display-inner-outer/)).
- **`:root` 대 `html` 대 `*`** — 상속의 출발점을 잡을 때 `*` 를 쓰면 상속이 아니라 **모든 요소에 선언을 하나씩 넣는 것**이라 그 아래로 아무것도 안 내려간다. 출발점은 `:root` 나 `body` 에 건다.
- 전역 키워드가 다섯인데 **`all` 은 여섯 번째가 아니다** — `all` 은 키워드가 아니라 그 다섯만 받는 **속성**이다.
