# css/syntax/03 — 상속: 상속되는 속성과 `inherit`/`initial`/`unset`/`revert`/`revert-layer` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려 `getComputedStyle` 로 읽은 것**이다.\
> 규칙은 [CSS Cascading and Inheritance Level 5](https://drafts.csswg.org/css-cascade-5/) 의 「Inheritance」·「Defaulting」 절로 접지했다.\
> **엔진은 Chrome 하나다** — 다른 엔진에서 확인했다고 적지 않았다. UA 시트에 달린 값은 그 자리에 표시해 두었다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 자식은 무슨 색인가

**출력** (Chrome 151 headless)

```text
.child  color = rgb(21, 128, 61)      = #15803d  초록
```

**이 문단의 `color` 는 무엇이 되는가**

- **초록**(`#15803d`). `p` 선언이 그대로 적용된다.

**`p` 선언의 명시도가 가장 약한데도 이기는 이유**

```text
.child 의 color 바구니
  +------------------------+
  | p { color: #15803d }   |   <- 후보가 하나 있다
  +------------------------+
        ↓
  캐스케이드가 이 하나를 뽑는다 → 끝
        ↓
  상속 단계는 아예 돌지 않는다
```

- 부모의 `#b91c1c` 는 **후보가 아니다.** 상속은 바구니가 비었을 때 채워 넣는 단계이고, 여기서는 바구니가 안 비었다.
- 이긴 게 아니라 **비교가 일어나지 않았다.**

**「상속이 선언보다 약하다」가 틀린 표현인 이유**

- 약하다·세다는 **같은 줄에 세웠을 때** 쓰는 말이다. 상속값은 애초에 후보로 줄을 서지 않는다.
- 정확한 표현은 「**선언이 하나라도 있으면 상속은 일어나지 않는다**」이다.

**`p` 선언을 지우면**

- **`rgb(185, 28, 28)`**(`#b91c1c` 빨강) — 바구니가 비었으므로 부모의 계산값이 내려온다. *(실측)*

> **바구니** *(이 문서의 설명 장치 — [01번 주제](../01-cascade-and-priority/2-summary.md)에서 이어 쓴다)* — 한 요소의 한 속성에 걸린 후보 선언들의 집합.\
> 예: `color` 바구니가 비면 그때 상속이 값을 채운다.

### 2. 상속처럼 보이는데 상속이 아닌 것

**출력** (Chrome 151 headless)

```text
kid border-top-color      = rgb(185, 28, 28)     부모 테두리는 파랑(#1d4ed8)인데 빨강이 나왔다
kid width                 = 300px
kid text-decoration-line  = none
kid opacity               = 1                     부모에 0.5 를 줘도
```

**`#kid` 의 `border-top-color` 와 그것이 상속의 증거가 아닌 이유**

- **`rgb(185, 28, 28)`**(빨강)이다.
- 상속이라면 **부모의 테두리색 파랑**(`#1d4ed8`)이 나와야 한다. 빨강이 나왔다는 것 자체가 반증이다.

```text
상속이라면                          실제로 일어난 일
+--------------------------+       +---------------------------------+
| 부모 border-color 파랑   |       | border-color 초기값 = currentColor|
|      ↓ 내려온다          |       |      ↓                          |
| 자식 border-color 파랑   |       | 자식 color = (상속) 빨강        |
+--------------------------+       |      ↓                          |
                                   | 자식 border-color = 빨강        |
                                   +---------------------------------+
```

- **`color` 는 상속되고, 그 상속된 색을 `currentColor` 가 가리킨 것**이다. `border-color` 자체는 내려오지 않았다.

**`width: 300px` 는 상속인가**

- **아니다.** `width` 의 초기값은 `auto` 이고, 블록 요소에서 `auto` 는 「부모 content 폭을 채운다」로 **사용**된다.
- 부모의 content 폭이 300px 이라 자식이 300px 로 **계산된 것**이지, 값이 내려온 게 아니다. 자세한 것은 [04번 주제](../04-value-processing-stages/2-summary.md).

**`text-decoration-line` 이 `none` 인데 밑줄이 보이는 이유**

- `text-decoration` 은 **상속되지 않는다.** 조상이 그린 선이 자손 글자 위를 **지나가는 것**이지 자손이 자기 선을 그린 게 아니다.
- 그래서 자손에서 `text-decoration: none` 을 줘도 **조상이 그은 선은 안 지워진다** — 자주 걸리는 자리다.

**부모 `opacity: 0.5` 일 때 자식의 `opacity`**

- **`1`** 이다. `opacity` 는 상속되지 않는다.
- 자식이 흐려 보이는 것은 **부모 그룹을 통째로 하나의 이미지로 합성해 반투명하게 칠한 결과**다.
- 그래서 자식에 `opacity: 1` 을 줘도 다시 진해지지 않는다.

### 3. 네 키워드를 한 줄씩 말하라

**각각 무엇으로 되돌리는가**

| 키워드 | 되돌리는 곳 |
|---|---|
| `inherit` | 부모의 **계산값** |
| `initial` | 명세가 정한 **초기값** |
| `unset` | 상속되면 `inherit`, 아니면 `initial` |
| `revert` | 이 **출처**의 선언이 없었던 셈 치고 아래 출처(대개 UA 시트)의 값 |

**`unset` 이 각각 무엇이 되는가**

```text
color (상속됨)          -> inherit 와 같다  -> 부모 값
border-color (상속 안 됨) -> initial 과 같다 -> currentColor
```

실측: 부모 빨강 판에서 `.c { color: unset; border-color: unset }` 은 **둘 다 `rgb(185, 28, 28)`** 이었다.\
앞은 상속으로, 뒤는 `currentColor` 로 같은 값이 된 것이라 **이유가 서로 다르다.**

**브라우저 기본 스타일로 돌아가는 것**

- **`revert`** 하나뿐이다. `initial` 은 브라우저가 아니라 **명세**로 간다.

**`revert` 와 `revert-layer` 의 단위**

- `revert` = **출처**(작성자 시트 전체) 단위.
- `revert-layer` = **레이어** 하나 단위. 레이어 밖에서 쓰면 `revert` 와 같아진다.

### 4. `revert` 와 `initial` 이 갈리는 자리

**출력** (Chrome 151 headless)

```text
#d1 display (revert)      = block
#d2 display (initial)     = inline
#g1 font-weight (revert)  = 700
#g2 font-weight (initial) = 400
```

**네 값의 예측**

- `revert` 쪽은 **UA 시트의 값**(`div{display:block}` · `strong{font-weight:bolder}`).
- `initial` 쪽은 **명세 초기값**(`display: inline` · `font-weight: normal`).

**`div { display: initial }` 이 `block` 이 아닌 이유**

```text
명세                       UA 시트                  내 시트
+--------------------+    +--------------------+   +---------------------+
| display 초기값     |    | div { display:     |   | div { display:      |
|        inline      |    |        block }     |   |        initial }    |
+--------------------+    +--------------------+   +---------------------+
       ↑                          ↑
   initial 이 가는 곳        revert 가 가는 곳
```

- `div` 가 블록인 것은 **CSS 의 성질이 아니라 브라우저가 써 둔 한 줄**이다.
- `display` 의 명세 초기값은 `inline` 이다. 그래서 `initial` 은 `inline` 을 준다.

**`li { display: initial }` 이 잃는 것**

- **`list-item`** 을 잃는다(실측 `inline`). 곧 **목록 마커(불릿·번호)가 사라지고 줄바꿈도 안 된다.**
- `revert` 면 `list-item` 이 남는다(실측).

**둘이 같은 값을 내는 속성의 조건**

- **UA 시트가 그 요소의 그 속성을 건드리지 않는 속성**이다.\
  그때 `revert` 는 「작성자 선언이 없는 상태」로 떨어지고, 그것은 상속되지 않는 속성이면 곧 초기값이다.
- 실측에서 `p` 의 `border-top-color` 가 그랬다 — `revert` 와 `initial` 이 둘 다 `rgb(185, 28, 28)`.
- 상속되는 속성이면 `revert` 는 **초기값이 아니라 상속값**으로 떨어지므로 `initial` 과 갈릴 수 있다.

### 5. 버튼 셋 중 어느 것이 버튼처럼 보이나

**출력** (Chrome 151 headless — 일곱 속성)

```text
속성              기본 button      all: unset        all: revert
----------------  ---------------  ----------------  ---------------
display           inline-block     inline            inline-block
color             rgb(0, 0, 0)     rgb(185, 28, 28)  rgb(0, 0, 0)
font-family       Arial            Georgia, serif    Arial
font-size         13.3333px        18px              13.3333px
border-top-style  outset           none              outset
background-color  rgb(239,239,239) rgba(0, 0, 0, 0)  rgb(239,239,239)
padding-top       1px              0px               1px
```

**회색 테두리 버튼으로 보이는 것**

- **「기본」과 「all: revert」 둘**이다. 일곱 속성이 전부 같은 값으로 나왔고, 스크린샷에서도 같은 모양이었다.
- *(「모든 속성이 같다」고는 확인하지 않았다 — 위 일곱만 대조했다.)*

**`all: unset` 버튼의 `color` 와 `font-family`**

- `color` = **`rgb(185, 28, 28)`**, `font-family` = **`Georgia, serif`** — 둘 다 **부모 `.bar` 의 값**이다.
- 이 둘이 상속되는 속성이라 `unset` 이 `inherit` 으로 갈렸기 때문이다.

**`all: initial` 로 바꾸면 더 달라지는 것**

- **상속마저 끊긴다.** `color` 는 검정, `font-family` 는 브라우저 기본 글꼴이 된다.\
  실측에서 `all: initial` 버튼의 `font-family` 는 `"Noto Sans CJK KR"`(이 머신의 브라우저 기본 글꼴)이었다 — **환경에 달린 값이다.**

**서드파티 위젯의 내 스타일만 걷어낼 때**

- **`all: revert`** 다. 「내 시트를 안 썼더라면」이 정확히 그 뜻이다.
- `all: unset`·`all: initial` 은 UA 시트의 값까지 지워서 **위젯의 폼 컨트롤이 컨트롤처럼 안 보이게** 된다.

### 6. 상속되지 않는 속성에 `inherit` 을 쓰면

**출력** (Chrome 151 headless)

```text
.t  border-color: inherit  = rgb(29, 78, 216)     부모의 파랑을 받아 왔다
.t2 border-color: unset    = rgb(185, 28, 28)
.t3 border-color: initial  = rgb(185, 28, 28)
```

**`.t` 의 `border-top-color`**

- **`rgb(29, 78, 216)`**(`#1d4ed8` 파랑) — 부모 `.box` 의 테두리색을 그대로 가져왔다.

**상속 안 되는 속성에 `inherit` 이 유효한 이유**

- `inherit` 은 「이 속성이 상속되는 속성인가」를 **묻지 않는다.** 언제나 「부모의 계산값을 쓴다」다.
- 상속 여부는 **선언이 없을 때 무엇을 채우나**를 정할 뿐이고, `inherit` 은 선언이 **있는** 경우다.

**`unset` 과 `initial` 이면**

- 둘 다 **`rgb(185, 28, 28)`**(빨강)이다.
- `unset` → `border-color` 는 상속 안 되니 `initial` → `currentColor`.
- `initial` → 곧바로 `currentColor`.
- `.t` 의 `color` 는 `.box` 에서 상속된 빨강이므로 `currentColor` 가 빨강이 된다.

**`currentColor` 로 설명하면**

```text
inherit  -> 부모의 border-color 값 자체를 가져온다        파랑
unset    -> border-color 초기값 = currentColor
initial  -> border-color 초기값 = currentColor
              ↓ currentColor = 이 요소의 color
              ↓ 이 요소의 color = (상속) 빨강
                                                          빨강
```

셋 중 **`inherit` 만 「부모의 그 속성」을 보고**, 나머지 둘은 **자기 자신의 `color`** 를 본다.

### 7. `revert-layer` 는 무엇을 지우는가

**출력** (Chrome 151 headless)

```text
.r1 = rgb(185, 28, 28)     base 의 빨강이 남았다
.r2 = rgb(0, 0, 0)         빨강도 같이 지워졌다
```

**두 문단의 색**

- `.r1` = **빨강**, `.r2` = **검정**.

**`.r2` 가 다른 결과를 내는 이유**

```text
.r1                                  .r2
@layer base  { color: red }          @layer base { color: red }
@layer theme { revert-layer }        @layer base { revert-layer }
       ↓                                    ↓
theme 레이어의 선언만 없앤다          base 레이어의 선언을 전부 없앤다
       ↓                                    ↓
base 의 red 가 남는다                 red 도 같이 사라진다 -> 검정
```

- `revert-layer` 가 없애는 것은 **그 선언 하나가 아니라 그 레이어의 그 속성 선언 전부**다.
- `.r2` 는 되돌릴 값과 되돌리라는 명령이 **같은 레이어 안에** 있어서 둘 다 지워졌다.

**레이어 밖에서 쓰면**

- **`revert` 와 같아진다.** 앞 레이어가 없으므로 출처 전체를 되돌린다.
- 실측: 레이어 밖 `.r3 { color:#15803d } .r3 { color: revert-layer }` → **`rgb(0, 0, 0)`**.

**다크 테마 레이어만 무를 때 `initial` 대신 쓰는 이유**

- `initial` 은 **모든 앞 레이어의 값까지 날린다.** 기본 테마 레이어가 정해 둔 색도 같이 사라진다.
- `revert-layer` 는 **한 칸만 되돌린다** — 「테마를 안 얹었을 때의 값」이 정확히 그것이다.

### 8. 이 선언들은 살아남는가

**출력** (Chrome 151 headless — `document.styleSheets[0].cssRules` 의 각 규칙이 담고 있는 속성 목록)

```text
규칙 .x = [padding-top, padding-right, padding-bottom, padding-left]
규칙 .y = [background-color]
규칙 .z = []
```

**실제로 적용되는 선언**

- `.x` — **`padding: 4px` 만.** `margin: 10px inherit` 은 파서가 **아예 담지 않았다.**
- `.y` — **`background-color: gold` 만.** `color: initial red` 는 담기지 않았다.
- `.z` — **아무것도 없다.** `all` 은 전역 키워드만 받는데 `red` 를 줬다.

**에러가 나는가**

- **안 난다.** 예외도, 콘솔 경고도, 화면의 표시도 없다. CSS 는 **모르는 선언을 조용히 버린다.**
- 버려진 자리는 이전 값 그대로 남으므로 **화면상으로는 「내 CSS 가 무시됐다」로만 보인다.**

**「버려졌다」를 값으로 확인하려면**

```js
document.styleSheets[0].cssRules[0].style   // 규칙이 담고 있는 속성 목록
CSS.supports('margin', '10px inherit')      // false
getComputedStyle(el).marginTop              // 실제 계산 결과
```

- 앞의 둘은 **파서가 담았는지**를 묻고, 마지막은 **값이 먹었는지**를 묻는다. 둘은 다른 질문이다 — [07번 주제](../07-syntax-and-error-recovery/2-summary.md)가 정본이다.

**전역 키워드를 값의 일부로 못 쓰는 규칙**

- **전역 키워드는 선언 값 전체여야 한다.** 다른 토큰과 섞이면 그 선언 하나가 통째로 버려진다.
- 단축에는 쓸 수 있다 — `margin: inherit` 은 유효하고, 네 방향 전부에 걸린다.

### 9. 전역 선택자가 상속에 하는 일

**출력** (Chrome 151 headless)

```text
.card  font-family = Georgia, serif
.inner font-family = "DejaVu Sans", sans-serif      <- 안 내려왔다
```

**`.card` 안 `<p>` 의 `font-family`**

- **`"DejaVu Sans", sans-serif`** — `*` 가 준 값이다. Georgia 는 안 내려온다.

**상속되는 속성을 `*` 로 선언하면**

```text
*  { font-family: A }           모든 요소의 바구니에 후보가 하나씩 들어간다
      ↓
.card { font-family: B }        .card 의 바구니에만 B 가 추가된다
      ↓
.card 안의 p  -> 바구니에 A 가 이미 있다 -> 상속 단계가 안 돈다 -> A
```

- **그 속성의 상속이 문서 전체에서 끊긴다.** 부모에 뭘 써도 한 칸 아래로 안 내려간다.

**`* { box-sizing: border-box }` 가 괜찮은 이유**

- **`box-sizing` 은 원래 상속되지 않는다.** 끊을 상속이 없으니 잃는 것이 없다.
- 상속 여부를 모르면 「`*` 를 써도 되나」를 판단할 수 없다 — 그래서 §「무엇이 상속되나」가 실용 지식이 된다.

**출발점을 `:root`·`body` 에 거는 이유**

- 요소 **하나**에만 선언을 넣고 나머지는 상속으로 내려보내면, 중간에서 부모를 바꾸는 것이 그대로 통한다.
- `*` 는 상속 사슬을 **모든 마디에서 끊는다.**

### 10. 다른 주제와 잇기

**출력** (Chrome 151 headless)

```text
#parent font-size / text-indent / line-height / letter-spacing = 20px / 40px / 30px / 2px
#child  font-size / text-indent / line-height / letter-spacing = 10px / 40px / 15px / 2px
```

**자식의 `letter-spacing`**

- **`2px`** 다. `1px` 이 아니다.

**「물려받는 것은 부모의 계산값」과 이어지는 지점**

```text
부모에서 일어난 일                         자식에서 일어난 일
+-------------------------------+         +-------------------------------+
| letter-spacing: 0.1em         |         | 바구니가 비었다               |
|   font-size 20px 기준으로     |         |   ↓                           |
|   계산값이 이미 2px 이 되었다  |  ───→   | 부모의 계산값 2px 을 받는다    |
+-------------------------------+         | em 을 다시 계산하지 않는다     |
                                          +-------------------------------+
```

- **`em` 은 부모 자리에서 이미 픽셀이 된다.** 자식은 「0.1em」이라는 글자를 받는 게 아니다.
- 같은 판의 `text-indent: 2em` 도 부모·자식 둘 다 **`40px`** 이었다 — 자식 글꼴이 10px 인데도 20px 이 아니다.
- **예외가 `line-height` 의 무단위 값**이다 — 부모 30px / 자식 15px 로 **자식에서 다시 계산됐다.** 그 값의 계산값이 「숫자 그 자체」라서다. 정본은 [04번 주제](../04-value-processing-stages/2-summary.md).

**`display: contents` 가 상속을 끊는가**

- **안 끊는다.** 실측에서 `display: contents` 인 부모의 `color`·`font-family` 가 자식에 그대로 내려왔다\
  (`rgb(185, 28, 28)` / `Georgia, serif`).
- 상속은 **상자 트리가 아니라 요소 트리**를 탄다. 상자가 없어져도 상속은 통과한다.

**커스텀 속성이 예외인 점**

- **커스텀 속성은 전부 상속된다.** `--brand` 를 부모에 한 줄 쓰면 자손 어디서나 읽힌다(실측 `#15803d`).
- 그래서 `:root` 에 쓰는 관례가 성립한다. `@property` 로 등록하면 `inherits: false` 로 끌 수 있다(목록의 **36번 주제**·**37번 주제**).
- 무효한 값일 때의 동작도 다르다 — 보통 속성은 선언이 버려지지만 커스텀 속성은 **값을 담은 채** 쓰는 쪽에서 무효가 된다([07번 주제](../07-syntax-and-error-recovery/2-summary.md)).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**하네스** — 문서 조각과 프로브 스크립트를 합쳐 한 문서로 만들고, 결과를 DOM 에 써 넣은 뒤 `--dump-dom` 을 읽는다. 다섯 주제(03\~07)가 같은 것을 썼다.

```bash
# harness.sh body.html probes.js   —  probes.js 안에서 P(라벨, 값) / CS(선택자, 속성) 을 쓴다
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

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 22개 속성을 부모에 걸고 자식에서 읽기(상속 여부) | 1 | 동작 방식 (2) · A2 |
| 네 키워드 × (`color`·`border-color`) | 1 | 동작 방식 (3) · A3 · A6 |
| `revert` 대 `initial` × (`div`·`li`·`strong`·`p`·`a`) 10개 값 | 1 | 동작 방식 (4) · A4 |
| `all` × (기본·`unset`·`revert`·`initial`) × 7속성 | 1 | 동작 방식 (5) · A5 |
| `revert-layer` 3경우 + 루트 `inherit` | 1 | 동작 방식 (6) · A7 |
| 무효 선언 3개의 `cssRules[].style` | 1 | A8 |
| `*` 가 `font-family` 상속을 끊는가 | 1 | 어디서 틀리나 6 · A9 |
| `em` 계산값 상속 4속성 × 부모·자식 | 1 | A10 |
| `display: contents` 통과 · 커스텀 속성 상속 | 1 | A10 |
| demo 2개(`font-weight` 셋 · `all` 버튼 셋) — 값 + 스크린샷 | 각 1 | 2-summary 의 demo |
| demo 의 「바꿔 볼 것」 단언 2개(부모 `font-weight: 700` · `all: initial`) | 각 1 | 2-summary 의 demo |

**구현에 달린 항목** — 버전이 오르면 다시 찍을 자리다.

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `a { color: revert }` | `rgb(0, 0, 238)` | Chrome UA 시트의 링크색 |
| `p { margin-top: revert }` | `16px` | UA 시트의 `1em` 해소값 |
| `button` 기본 `font-size` | `13.3333px` | UA 시트 |
| `all: initial` 의 `font-family` | `"Noto Sans CJK KR"` | 이 머신의 브라우저 기본 글꼴 설정 |
| `color: initial` | `rgb(0, 0, 0)` | 명세는 `canvastext` — 해소는 환경에 달렸다 |

**안 돌려 본 것** — 사용자(user) 출처의 스타일시트가 있을 때 `revert` 가 거기서 멈추는지는 확인하지 않았다. 이 환경에 사용자 시트를 넣을 경로를 만들지 않았고, 명세 기술만 옮겼다.

## 용어 풀이

- **상속(inheritance)** — 자식의 어떤 속성 바구니가 비었을 때 부모의 그 속성 **계산값**을 쓰는 것.
- **바구니** *(설명 장치)* — 한 요소의 한 속성에 걸린 후보 선언들의 집합. 01번에서 이어 쓴다.
- **초기값(initial value)** — 명세가 속성마다 정한 값. `display` 는 `inline`, `font-weight` 는 `normal`.
- **사용자 에이전트 스타일시트(UA stylesheet)** — 브라우저 내장 기본 시트. `revert` 가 돌아가는 곳.
- **`inherit`** — 상속 여부와 무관하게 부모의 계산값을 쓴다.
- **`initial`** — 명세 초기값으로.
- **`unset`** — 상속되면 `inherit`, 아니면 `initial`.
- **`revert`** — 이 출처의 선언이 없었던 셈 치고 아래 출처의 값으로.
- **`revert-layer`** — 이 레이어의 그 속성 선언 전부를 없앤 셈 치고 앞 레이어의 값으로.
- **`all`** — 전역 키워드 다섯만 받는 단축. `direction`·`unicode-bidi` 는 제외.
- **`currentColor`** — 그 요소의 `color` 계산값. `border-color`·`outline-color` 의 초기값.
- **계산값(computed value)** — 상속되는 단위. `em` 은 여기서 이미 픽셀이 된다. 정본은 04번.
- **해석값(resolved value)** — `getComputedStyle` 이 실제로 돌려주는 값. 계산값일 때도 사용값일 때도 있다. 정본은 04번.
