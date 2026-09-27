# css/syntax/37 — `@property`: 타입 등록·초기값·상속 여부 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 질문의 코드를 그대로 돌려 읽은 것**이다.\
> 규칙은 [CSS Properties and Values API Level 1](https://drafts.csswg.org/css-properties-values-api-1/) 로 접지했다.\
> **엔진은 Chrome 하나다.** 전환 실험만 CDP 로 실제 마우스 입력을 넣어 잰다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 등록하면 애니메이션이 된다

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
.u  width = 200px      등록 안 함, 50%
.r  width = 100px      등록함,     50%
```

**두 막대의 `width`**

- 등록 안 한 `.u` 는 **`200px`** — 이미 끝값이다.
- 등록한 `.r` 은 **`100px`** — 0px 와 200px 의 한가운데다.

**25% 와 75%**

```text
진행률    .u (등록 안 함)    .r (등록함)
25%       0px                50px
50%       200px              100px
75%       200px              150px
```

- 등록한 쪽은 **선형**이다. 등록 안 한 쪽은 **0px 아니면 200px** 둘뿐이다.

**값이 바뀌는 지점**

```text
실측 — 같은 키프레임을 -4.9s 와 -5.1s 로 잘라 봤다
  49% (-4.9s)  ->  0px
  51% (-5.1s)  ->  200px
```

- **50% 에서 한 번 뒤집힌다.**

**명세 용어**

- **이산 보간**(discrete interpolation). 중간값을 만들 수 없는 값 타입의 기본 동작이다.\
  등록하지 않은 커스텀 속성은 브라우저에게 **토큰 뭉치**라서 중간값이 정의되지 않는다.

### 2. 전환은 애니메이션과 같은 방식으로 실패하는가

**출력** (Chrome 151 headless + CDP 실제 마우스 입력, `transition: … 1s linear`)

```text
시각          등록한 --w      등록 안 한 --uw
호버 전       40px            40px
+0.25s        114.656px       320px
+0.50s        184.656px       320px
+0.75s        254.656px       320px
+1.20s        320px           320px
뗀 뒤 1.5s    40px            40px
```

**중간에 보이는 것**

- **아무것도 안 보인다.** 0.25초 시점에 **이미 끝값**이다. 계단조차 없다.

**애니메이션과 다른 이유**

- 전환은 「**보간 가능한 값이 바뀌었을 때**」 생성된다 — 보간이 불가능하면 **전환 객체 자체가 안 만들어진다.**
- 애니메이션은 키프레임이 **시작값과 끝값을 명시적으로 준다.** 줄 게 있으니 이산 보간으로라도 성립한다.
- 곧 **애니메이션은 「질 나쁘게 성공」하고 전환은 「실패」한다.**

**진단 갈림길**

- 값이 **중간에 한 번 바뀐다** → 애니메이션(이산 보간). 등록만 하면 부드러워진다.
- 값이 **즉시 끝값** → 전환이 안 걸렸다. 역시 등록이 답이지만 증상이 다르다.

### 3. 칸 하나를 빼면

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
cssRules.length = 1
CSSPropertyRule = ["--b(init=null)"]
```

**실제로 등록되는 것**

- **`--b` 하나뿐**이다(`syntax: "*"`).
- `--a` 는 `initial-value` 가 없어서, `--c` 는 `<lengthzz>` 가 없는 타입 이름이라서 등록되지 않았다.

**어디로 갔는가**

- **규칙 전체가 버려졌다.** 시트에 남은 규칙이 **1개**다 — 선언 단위로 버려진 게 아니라 `@property` 블록이 통째로 사라졌다.
- [07번 주제](../07-syntax-and-error-recovery/2-summary.md)의 「at-rule 단위 — 블록까지 통째로」와 같은 규칙이다.

**무엇으로 확인하는가**

```js
[...document.styleSheets[0].cssRules]
  .filter(r => r.constructor.name === "CSSPropertyRule")
  .map(r => r.name)
```

- 화면으로는 **절대 안 잡힌다.** 증상은 「애니메이션이 안 된다」 하나뿐이다.

**`*` 만 면제받는 이유**

- `*` 는 「**타입이 없다**」는 신고다. 타입이 없으면 「그 타입의 기본값」이라는 것도 정의할 수 없다.\
  다른 타입은 초기값이 없으면 상속·초기값 계산이 성립하지 않으므로 필수다.

### 4. 무효한 값이 떨어지는 자리

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
p1 --plain = "redd"          p1 declared props = ["--plain","color"]
p2 --len   = "10px"          p2 declared props = ["--len","width"]
p1 color   = rgb(0, 0, 0)
p2 width   = 10px
```

**두 커스텀 속성의 값**

- `.p1` 의 `--plain` 은 **`"redd"` 그대로** 살아 있다.
- `.p2` 의 `--len` 은 **`"10px"`** — 내가 쓴 `redd` 가 아니라 **`initial-value` 로 갈아끼워졌다.**

**`color` 와 `width`**

- `.p1` 의 `color` 는 `rgb(0, 0, 0)` — **이 선언이 죽었다.**
- `.p2` 의 `width` 는 `10px` — **아무것도 안 죽었다.** 초기값이 흘러 들어갔을 뿐이다.

**어느 쪽이 IACVT 인가**

- **`.p1` 이 IACVT** 다. 선언은 담겼는데(`declared props` 에 `color` 가 있다) 계산 시점에 무효가 되어 `unset` 처럼 처리됐다.
- `.p2` 는 IACVT 가 **아니다.** 무효 판정이 `--len` 선언 자리에서 끝나고, 그 아래로 유효한 값만 흐른다.

**「디자인 토큰의 방화벽」**

```text
  등록 안 함                               등록함
  --brand: redd                            --brand: redd
     |                                        |  여기서 막힌다
     +-> color: var(--brand)      죽음        +-> --brand 은 initial-value 가 된다
     +-> border-color: var(--brand) 죽음      +-> 쓰는 쪽은 전부 유효한 색을 본다
     +-> fill: var(--brand)        죽음
     오타 하나가 사용처 수만큼 번진다          오타 하나가 한 자리에서 멈춘다
```

### 5. 상속 칸

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
.par --i = rgb(21, 128, 61)      .kid --i = rgb(21, 128, 61)
.par --n = rgb(21, 128, 61)      .kid --n = rgb(185, 28, 28)
```

**`.kid` 의 두 값**

- `--i`(`inherits: true`)는 **초록**(`rgb(21, 128, 61)`) — 부모에게서 내려왔다.
- `--n`(`inherits: false`)은 **빨강**(`rgb(185, 28, 28)`) — `initial-value` 다. 부모가 초록으로 정해 놨는데도 안 내려왔다.

**등록하지 않은 커스텀 속성**

- **항상 상속한다.** 끌 방법이 없다(명시적으로 `--x: initial` 을 다시 선언하는 우회뿐이다).

**「끄는 것」인가 「얻는 것」인가**

- **없던 기능을 얻는 것**이다. `inherits: false` 는 `@property` 등록이 주는 새 능력이다.\
  그래서 컴포넌트 안에서만 쓰는 토큰이 **자손 컴포넌트로 새는 것**을 처음으로 막을 수 있게 됐다.

### 6. 계산값의 모양이 바뀐다

**출력** (Chrome 151 headless)

```text
등록함       --c1 = "rgb(185, 28, 28)"
등록 안 함   --c2 = "#b91c1c"
```

**무엇이 나오는가**

- 등록하면 **`rgb(185, 28, 28)`** — `<color>` 타입의 계산값 정규형이다.
- 등록 안 하면 **`#b91c1c`** — 내가 쓴 글자 그대로다.

**판별 수단이 되는가**

- **된다.** 값이 정규형으로 바뀌어 있으면 등록된 것이다.\
  다만 **정규형이 원문과 같은 값**(`0px` 처럼)이면 구별이 안 되므로, 확실한 판별은 `CSSPropertyRule` 을 세는 쪽이다.

### 7. at-rule 과 JS API 의 실패 방식

**출력** (Chrome 151 headless — `CSS.registerProperty` 에 같은 실수를 던졌다)

```text
initial-value 없음 (syntax 가 * 아님)
  SyntaxError: An initial value must be provided if the syntax is not '*'
syntax: "*" + initialValue 없음
  ok
같은 이름을 두 번
  InvalidModificationError: The name provided has already been registered.
syntax: "<lengthzz>"
  SyntaxError: The syntax provided is not a valid custom property syntax.
initialValue: "redd"  (syntax 는 <length>)
  SyntaxError: The initial value provided does not parse for the given syntax.
name: "nodashes"
  SyntaxError: Custom property names must start with '--'.
```

**`initial-value` 를 뺐을 때**

- `@property` — **규칙이 조용히 사라진다.** 아무 신호도 없다.
- `CSS.registerProperty` — **`SyntaxError` 를 던지고 이유를 문장으로 말한다.**

**같은 이름을 두 번**

- JS 쪽은 **`InvalidModificationError`**. 등록은 **불가역**이라 덮어쓸 수 없다.
- CSS 쪽은 예외가 없고, **나중 선언의 기술자가 이긴다**(같은 이름에 대한 마지막 `@property` 가 유효하다).

**JS API 를 먼저 던져 보는 이유**

- **CSS 에는 에러가 없다.** 같은 규칙을 JS API 에 통과시켜 보면 **왜 버려졌는지**를 한 줄로 알려 준다.\
  이 언어에서 「진단 도구를 빌려 온다」의 가장 싼 형태다.

**그런데 실제 코드는 `@property`**

- 스타일시트와 **같은 곳**에 있어야 유지보수가 되고,
- JS 가 로드되기 전 첫 페인트부터 등록돼 있어야 **초기 렌더가 안 튄다.**

### 8. 등록은 언제부터 효력이 있는가

**출력** (Chrome 151 headless — 50% 에 멈춘 애니메이션이 있는 상태에서 등록)

```text
registerProperty 호출 전   .j1 width = 200px
registerProperty('--js-l', {syntax:'<length>', inherits:false, initialValue:'0px'})
registerProperty 호출 후   .j1 width = 100px
```

**진행 중 애니메이션**

- **그 자리에서 보간으로 바뀐다.** 이산이던 것이 선형이 된다 — 등록은 **소급 적용**된다.

**취소할 수 있는가**

- **없다.** 명세에 해제 API 가 없고, 실측에서 재등록은 `InvalidModificationError` 였다.

**이름이 부딪히면**

- JS 쪽은 두 번째 호출이 **예외**로 실패한다(먼저 등록한 쪽이 이긴다).
- CSS 쪽은 예외 없이 **나중 `@property` 의 기술자가 유효**해지므로, 라이브러리의 타입을 모르게 덮어쓸 수 있다.\
  그래서 **접두(`--acme-`)를 붙인다.**

### 9. `syntax` 문자열

**출력** (Chrome 151 headless)

```text
@property --mix { syntax: "<length> | auto"; inherits: false; initial-value: auto }
@keyframes m { from { --mix: auto } to { --mix: 200px } }
  50% 지점  --mix = "200px"   width = 200px      <- 이산이다
```

**`auto` ↔ `10px` 보간**

- **안 된다.** 등록은 됐지만 `auto` 와 길이는 **서로 다른 갈래**라 중간값이 없다.\
  실측에서 50% 에 `200px` 이 나왔다 — 이산 보간의 그 모양이다.
- 곧 **「등록했다」가 「보간된다」를 보장하지 않는다.** 두 끝값이 **같은 타입**이어야 한다.

**`"*"` 로 등록하면**

- **안 된다.** 타입이 없으므로 여전히 이산 보간이다.

**목록 타입의 구분자**

```text
  "<length>+"    공백으로 구분한 목록      10px 20px 30px
  "<color>#"     쉼표로 구분한 목록        red, blue, green
```

### 10. 다른 주제와 잇기

**07번의 어느 규칙인가**

- 「**모르는 at-rule 은 블록까지 통째로**」다. 정확히는 **프렐류드·본문이 무효인 at-rule 은 통째로 버려진다** — `@property` 는 필수 기술자가 빠지면 무효가 되도록 명세가 정해 놓았다.

**04번의 어느 단계인가**

- **지정값 → 계산값** 단계다. 등록 속성은 계산값을 만들 때 **`syntax` 로 타입 검사를 받고**, 통과 못 하면 `initial-value` 가 계산값이 된다.\
  등록 안 한 속성은 이 단계에서 **아무 검사도 안 받고 토큰 뭉치 그대로** 통과한다.

**52번의 어느 문장인가**

- 「**걸어갈 수 없는 짐이 있다 — 중간값을 만들 수 없는 값은 전환이 아예 시작되지 않는다**」이다.\
  `height: auto` 가 그 예였고, **등록 안 한 커스텀 속성이 같은 부류**다.

**스타일 쿼리에서 질의할 수 있는가**

- **된다.** 실측에서 `@container style(--ang: 45deg)` 가 등록한 `<angle>` 속성에 대해 정상 매치했다([40번 주제](../40-container-and-style-queries/2-summary.md)).\
  다만 스타일 쿼리는 **커스텀 속성만** 받는다 — 보통 속성(`style(color: red)`)은 Chrome 151 에서 조건이 항상 거짓이었다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**하네스** — 37\~41 다섯 주제가 공유한 것이다. 전환 실험만 CDP 판을 썼다.

```bash
# harness.sh body.html probes.js [W H]   —  file:// 로 연다
{ echo '<!doctype html><meta charset="utf-8"><title>probe</title>'
  cat "$1"
  echo '<script>'
  echo 'const __o=[];function P(k,v){__o.push(k+" = "+v)}'
  echo 'function CS(s,p){const e=document.querySelector(s);return e?getComputedStyle(e).getPropertyValue(p):"(no element)"}'
  cat "$2"
  echo 'const __p=document.createElement("pre");'
  echo '__p.textContent="<<<BEGIN>>>\n"+__o.join("\n")+"\n<<<END>>>";'
  echo 'document.body.appendChild(__p);</script>'
} > "$D/index.html"
google-chrome --headless --disable-gpu --no-sandbox --window-size="$W,$H" --dump-dom "$D/index.html"
```

**시각 고정 기법** — 애니메이션의 중간값은 `animation: <name> 10s linear -5s paused` 처럼
**음수 지연 + `paused`** 로 진행률을 고정해 읽었다. 이러면 `--dump-dom` 한 번으로 정확한 진행률의 계산값이 나온다.

**전환 하네스** — `--remote-debugging-port` + `--remote-allow-origins=*` 로 CDP 에 붙어
`Input.dispatchMouseEvent` 로 **실제 마우스를 대상 요소 중앙에 올리고**, 시각마다 `Runtime.evaluate` 로 `getComputedStyle` 을 샘플링했다.
`Runtime.evaluate` 로 클래스를 바꾸는 것은 사용자 조작이 아니므로 쓰지 않았다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 등록/미등록 색 애니메이션 50% | 1 | 동작 방식 (1) |
| 등록/미등록 길이 애니메이션 25·49·50·51·75% | 2 | 동작 방식 (1) · A1 |
| 등록/미등록 전환 (CDP, 6시점) | 2 | 동작 방식 (2) · demo · A2 |
| `@property` 7개 선언 후 `CSSPropertyRule` 세기 | 1 | 동작 방식 (5) · A3 |
| 질문 3의 코드 그대로(`--a`·`--b`·`--c`) | 1 | A3 |
| 등록/미등록 무효 값(`redd`) 대조 | 2 | 동작 방식 (4) · A4 |
| `inherits` true/false 부모-자식 | 2 | 동작 방식 (3) · A5 |
| 등록/미등록 계산값 표기 대조 | 1 | 동작 방식 (3) · A6 |
| `CSS.registerProperty` 실패 6종 던지기 | 1 | 동작 방식 (6) · A7 |
| 등록 전후 진행 중 애니메이션 값 | 1 | 동작 방식 (6) · A8 |
| `"<length> \| auto"` 의 50% 보간 | 1 | A9 |
| `syntax: "*"` 로 등록한 속성의 50% 보간 | 1 | A9 |
| 같은 이름 `@property` 두 번 — 어느 쪽이 유효한가 | 1 | A7 · A8 |
| `CSS.supports('at-rule(@property)')` | 1 | 동작 방식 (6) |
| demo 1개 — CDP 6시점 | 1 | 2-summary 의 demo |
| demo 의 「바꿔 볼 것」 — `@property` 블록 제거 (CDP) | 1 | demo |
| demo 의 「바꿔 볼 것」 — `syntax: "*"` 로 교체 (CDP) | 1 | demo |
| **제출 직전 demo 재추출·재실행 대조** | 1 | 어긋남 0건 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 50% 중간색 | `rgb(107, 53, 122)` | 색 보간 공간 선택은 구현 여지가 있다 |
| 전환 샘플값 `114.656px` 등 | ±10ms 오차 | 샘플 시각이 정확히 0.25s 가 아니다 |
| `registerProperty` 예외 **문구** | 위 6줄 | 명세는 예외 타입까지만 정한다 |
| 등록 커스텀 속성 지원 | Baseline **newly** 2024-07-09 | 2차 집계(`api.webstatus.dev` 의 `registered-custom-properties`) |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② `<image>`·`<transform-function>` 같은 드문 `syntax` 타입의 보간(명세 기술로만 적지 않고, 본문에서 아예 주장하지 않았다).

## 용어 풀이

- **`@property`** — 커스텀 속성의 타입·상속·초기값을 신고하는 at-rule. 칸 셋 중 둘은 필수.
- **등록 커스텀 속성** — 타입이 신고된 `--` 속성. 계산값이 정규형이 되고 보간이 가능해진다.
- **`syntax`** — 받을 수 있는 값의 타입 문자열. 모르는 이름을 쓰면 규칙째 버려진다.
- **`inherits`** — 자손에게 내려갈지. 등록해야만 끌 수 있다.
- **`initial-value`** — 아무도 안 정했을 때의 값. `syntax: "*"` 외에 필수.
- **보간(interpolation)** — 두 값 사이 중간값 만들기. 두 끝값이 같은 타입이어야 한다.
- **이산 보간(discrete interpolation)** — 50% 에서 한 번 뒤집히는 기본 동작.
- **IACVT** — 계산 시점 무효. 등록하면 이게 안 나고 `initial-value` 로 떨어진다. 정본은 [목록의 **36번 주제**](../36-custom-properties/).
- **`CSSPropertyRule`** — `@property` 의 CSSOM 타입. 등록 여부의 정답지.
- **`CSS.registerProperty()`** — 같은 등록의 JS API. **예외를 던져서** 이유를 말해 준다.
- **소급 적용** — 등록이 나중에 이뤄져도 이미 적용된 스타일·진행 중 애니메이션에 반영되는 것.
