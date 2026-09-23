# css/syntax/05 — `@layer` 캐스케이드 레이어: 선언 순서와 레이어 밖의 위치 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 색은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려 `getComputedStyle` 로 읽은 것**이다.\
> 규칙은 [CSS Cascading and Inheritance Level 5](https://drafts.csswg.org/css-cascade-5/) 「Cascade Layers」로 접지했다.\
> **엔진은 Chrome 하나다.** `@import` 실험만 로컬 HTTP 서버로 띄웠다(A7 참고).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 레이어 밖 규칙은 어디에 서는가

**출력** (Chrome 151 headless)

```text
.u1  color = rgb(29, 78, 216)     = #1d4ed8  파랑 (레이어 밖)
```

**이 문단의 색**

- **파랑**(`#1d4ed8`). 레이어 밖 규칙이 이긴다.

**명세의 표현**

> Unlayered rules are sorted later than any layered rules within the same parent layer (if any).

- 「**같은 부모 레이어 안의 어떤 레이어 규칙보다도 나중에 정렬된다**」 — normal 에서는 나중이 센 쪽이다.

**레이어를 열 개 만들면**

```text
@layer a, b, c, d, e, f, g, h, i, j;
   ↓
  a b c d e f g h i j  [레이어 밖]
                        ↑ 언제나 마지막 칸이다 — 레이어 수와 무관
```

- **안 달라진다.** 레이어 밖은 늘 마지막 칸이다.

**도입 시 첫 점검 항목**

- 「**레이어에 안 들어간 시트가 한 장이라도 남아 있나**」다.
- 남아 있으면 그 시트의 모든 normal 선언이 **내가 만든 모든 레이어를 이긴다.** 「레이어를 썼는데 왜 예전 스타일이 이기지」의 답이 대개 이것이다.

### 2. `!important` 하나로 뒤집히는 것

**출력** (Chrome 151 headless)

```text
.u2  color = rgb(185, 28, 28)     = #b91c1c  빨강 (가장 먼저 레이어 base)
```

**이 문단의 색**

- **빨강**(`#b91c1c`). 1번에서 가장 약했던 `base` 가 이긴다.

**명세 문장**

> for normal rules the declaration whose cascade layer is latest in the layer order wins, and for important rules the declaration whose cascade layer is earliest wins.

```text
      normal (.u1)                    important (.u2)
+---------------------------+   +---------------------------+
| 레이어 밖  #1d4ed8  ← 이김 |   | base      #b91c1c  ← 이김 |
| theme      #15803d        |   | theme     #15803d        |
| base       #b91c1c        |   | 레이어 밖 #1d4ed8        |
+---------------------------+   +---------------------------+
     실측 파랑                        실측 빨강
```

**레이어 밖도 같이 뒤집히는가**

- **같이 뒤집힌다.** normal 에서 가장 셌던 레이어 밖이 important 에서 **가장 약해진다.**
- 실측에서 레이어 밖의 `#1d4ed8 !important` 가 세 후보 중 **꼴찌**였다.

**출처 사다리의 무엇과 같은 꼴인가**

- **normal 에서는 작성자가 사용자를 이기지만 important 에서는 사용자가 작성자를 이기는 것**과 같은 꼴이다([01번 주제](../01-cascade-and-priority/2-summary.md)의 1단계).
- `!important` 의 원래 뜻이 「**아래쪽이 위쪽을 이기게 하는 비상구**」라서, 레이어 안에서도 같은 모양을 반복한다.

### 3. 레이어 순서는 무엇이 정하는가

**출력** (Chrome 151 headless)

```text
.u1  color = rgb(21, 128, 61)     = #15803d  초록 (theme)
```

**이 문단의 색**

- **초록**(`#15803d`). 마지막 줄에 쓴 파랑이 아니다.

**자리가 안 바뀌는 이유**

```text
@layer base  { red }      <- 여기서 base 의 자리가 정해진다 (첫째 칸)
@layer theme { green }    <- theme 의 자리가 정해진다 (둘째 칸)
@layer base  { blue }     <- 이미 있는 base 를 '다시 연 것'
                             blue 는 base 칸 안에서 red 를 이겼을 뿐이다

  [base: blue]  [theme: green]   ->  나중 칸 theme 가 이긴다
```

- **레이어 순서는 이름이 처음 나타난 순간 고정된다.** 그 뒤로는 무엇을 해도 안 움직인다.

**맨 아래에 `@layer theme, base;` 를 덧붙이면**

- **안 달라진다.** 실측: `@layer gamma{} @layer delta{} @layer delta, gamma;` 의 승자는 여전히 `delta`(나중 칸)였다.
- 사전 선언은 **아직 안 나온 이름**의 순서를 정할 때만 효력이 있다.

**사전 선언을 맨 위에 두라는 관례**

- 위 답에서 곧바로 나온다 — **맨 위여야 모든 이름이** 「**아직 안 나온 이름**」이다.
- 그리고 순서를 **한 곳에서 읽을 수 있게** 된다. 그러지 않으면 순서가 번들러의 파일 결합 순서에 달리고, `@layer` 를 도입한 이유가 사라진다.

### 4. 익명 레이어 둘

**출력** (Chrome 151 headless)

```text
.an  color = rgb(21, 128, 61)     = #15803d  초록
```

**이 문단의 색**

- **초록**(`#15803d`).

**같은 레이어인가**

- **다른 레이어다.** `@layer { }` 는 쓸 때마다 **새 레이어를 하나 만든다** — 이름이 없으니 가리킬 수단이 없고, 따라서 「다시 연다」는 것이 성립하지 않는다.
- 판별 근거는 명세다. 결과만으로는 판별되지 않는다 — 다음 항목이 그 이야기다.

**`@layer solo { }` 두 개로 바꾸면**

- **결과는 같다**(실측 `rgb(21, 128, 61)` 초록). **그러나 이유가 다르다.**

```text
@layer { A } @layer { B }        두 레이어 -> '나중 레이어' 가 이긴다
@layer solo { A } @layer solo { B }   한 레이어 -> '같은 레이어 안의 나중 선언' 이 이긴다
```

- 결과가 같아서 **틀린 모델을 오래 유지하게 된다.** `@layer solo, other;` 같은 사전 선언을 끼우는 순간 두 모델의 예측이 갈린다.

**익명을 두 개 넘게 쓰면 안 되는 이유**

- **순서를 사람이 못 읽는다.** 이름이 없으니 사전 선언 줄에 적을 수도 없고, 개발자 도구에서도 구분이 어렵다.
- 서드파티 시트 하나를 `@import ... layer;` 로 아래에 까는 정도가 적당한 쓰임이다.

### 5. 레이어와 명시도가 맞붙으면

**출력** (Chrome 151 headless)

```text
.t1  color = rgb(21, 128, 61)     = #15803d  초록  (theme 의 p.t1)
```

**이 문단의 색**

- **초록**(`#15803d`). 명시도가 낮은 쪽이 이긴다.

**단계 번호로 설명**

```text
4단계  캐스케이드 레이어    base < theme   ->  theme 가 이긴다. 여기서 끝
5단계  명시도              (1,1,0) vs (0,1,1)  ->  부르지 않는다
```

- **4단계에서 갈리면 5단계는 계산조차 안 한다.** `(1,1,0)` 은 계산해 봐야 쓸 데가 없다.
- 두 단계표의 정본은 [01번 주제](../01-cascade-and-priority/2-summary.md)·[02번 주제](../02-specificity/2-summary.md)다.

**`@layer` 의 존재 이유와의 연결**

- **남의 시트를 덮으려고 선택자를 늘이는 일을 없애려고** 만든 기능이다.
- 선택자 길이는 5단계의 도구인데, 4단계에서 미리 갈라 두면 **5단계 싸움 자체가 안 일어난다.**

**명시도로 싸우고 있다는 신호**

- **4단계 설계가 없다**는 신호다. `#app #main .card .title` 같은 선택자가 늘고 있다면 레이어를 도입할 자리다.

### 6. 중첩 레이어의 안과 밖

**출력** (Chrome 151 headless)

```text
.ne  color = rgb(21, 128, 61)     = #15803d  초록
```

**이 문단의 색**

- **초록**(`#15803d`).

**`outer` 안에 쓴 `.ne` 는 레이어 밖인가**

- **문서 전체로 보면 레이어 안**(`outer` 소속)이지만, **`outer` 안에서 보면** 「**레이어 밖**」이다.
- 명세 문장의 「**within the same parent layer**」가 정확히 이 뜻이다.

```text
  outer 라는 서랍을 열면
  +---------------------------------+
  | outer.inner  #b91c1c            |   안쪽 칸막이
  | outer 직속   #15803d   ← 이김   |   칸막이에 안 넣고 서랍에 그냥 둔 것
  +---------------------------------+
```

**1번 규칙과의 관계**

- **같은 규칙이 재귀적으로 적용된 것**이다. 1번은 문서 최상위에서, 6번은 `outer` 안에서 같은 일이 일어난다.

**`@layer outer.inner { }` 와 같은 것인가**

- **같다.** 점 표기는 중첩 블록의 축약이다. 둘 다 `outer` 안의 `inner` 레이어를 가리킨다.

### 7. `@import` 로 서드파티를 아래에 깔기

**출력** (Chrome 151 headless, **로컬 HTTP 서버**)

```text
vendor.css : #app .btn { color: #b91c1c }     (1,1,0)
@layer app { .btn { color: #15803d } }        (0,1,0)

.btn  color = rgb(21, 128, 61)     = #15803d  초록.  app 이 이겼다
```

**어느 것이 이기는가**

- **`app` 의 `.btn`** 이 이긴다. `vendor` 가 더 센 선택자를 써도 **4단계에서 먼저 진다.**
- 이것이 `@layer` 의 가장 실용적인 쓰임이다 — **남의 시트를 한 줄도 안 고치고** 아래에 깐다.

**`@import` 줄을 규칙 뒤로 옮기면**

- **통째로 무시된다.** 실측에서 그 시트의 `cssRules` 에 `CSSImportRule` 이 **아예 없었고**(`CSSStyleRule` 하나만 남았다), 색도 안 바뀌었다.
- `@import` 는 `@charset`·`@layer` 사전 선언 다음, **다른 모든 규칙보다 앞**이어야 한다.

**`layer` 만 쓰면**

- **익명 레이어**에 들어간다. 이름이 없으니 사전 선언으로 순서를 조정할 수 없고, 그 자리(첫 등장 순서)로 고정된다.

**`file://` 에서 거짓 결론이 나오는 이유**

```text
file:// 로 연 문서                 http://127.0.0.1 로 연 같은 문서
+-----------------------------+   +-----------------------------+
| .i1 = rgb(0, 0, 0)          |   | .i1 = rgb(185, 28, 28)      |
| import 한 규칙이 안 먹는다   |   | import 한 규칙이 먹는다     |
| cssRules[0] 은 CSSImportRule|   | styleSheet.cssRules 도 읽힘 |
| .styleSheet.cssRules 는     |   |                             |
|   "Cannot access rules" 예외|   |                             |
+-----------------------------+   +-----------------------------+
```

- `file://` 문서는 **불투명 출처**라 가져온 시트가 적용되지 않는다. **에러도 경고도 없다.**
- ★ **이 문서를 쓰면서 실제로 당했다.** `@import` 없이 승부가 나는 판에서는 초록이 나와 「됐다」로 읽혔고, `@import` 만 남기고 다시 던져서야 검정이 나와 드러났다.
- **「한쪽만 보면 통과처럼 보이는」 실험은 반증 쪽을 한 번 더 던져야 한다.**

### 8. 이 at-rule 들은 살아남는가

**출력** (Chrome 151 headless)

```text
시트에 남은 규칙 수 = 0
```

**남는 규칙 수**

- **0개.** 아무것도 안 남는다.

**무엇이 잘못됐고 어디까지 삼키나**

```text
@layer base, theme          <- 세미콜론이 없다
@layer base { .z { red } }  <- 파서는 이 줄까지 '사전 선언의 prelude' 로 읽는다

at-rule 의 prelude 는 ';' 나 '{' 를 만날 때까지다.
여기서는 다음 줄의 '{' 를 먼저 만나므로
   prelude = "base, theme @layer base"
   block   = "{ .z { color: red } }"
가 되고, prelude 가 무효라 at-rule 이 통째로 버려진다 — 블록까지 같이.
```

- **다음 규칙을 같이 삼킨다.** 세미콜론 하나가 두 줄을 날린다.

**에러로 드러나는가**

- **안 난다.** 확인하려면 값을 읽어야 한다.

```js
document.styleSheets[0].cssRules.length   // 0  ← 파서가 아예 안 담았다
getComputedStyle(z).color                 // rgb(0, 0, 0)
```

- 정본은 [07번 주제](../07-syntax-and-error-recovery/2-summary.md)다.

**올바른 형태로 고치면**

- `@layer base, theme;` 로 세미콜론을 찍으면 **사전 선언 하나 + 레이어 블록 하나**, 둘 다 살아난다.

### 9. 레이어 안에서 예외 하나를 덮으려면

**어떤 수단을 쓰는가**

- **같은 레이어 안에서 명시도·순서로 푼다**(5·6단계). 레이어 설계가 있으면 그 안은 평범한 CSS 다.
- 또는 **그 예외를 위한 레이어를 더 나중에** 둔다(`@layer components, overrides;`).

**`!important` 가 두 번 실패하는 이유**

```text
①  레이어 순서가 뒤집혀 그 선언이 오히려 약해진다
      나중 레이어에 썼다면 important 에서는 가장 약한 칸이다
②  칸을 옮겨 버려서 되돌릴 수단이 사라진다
      다음 사람은 또 !important 를 붙이고, 그다음 사람은 붙일 게 없다
```

「**올리는 장치가 아니라 내리는 장치**」

- 레이어로 **이기게 만들 것을 고르는 게 아니라, 지게 만들 것을 서랍에 넣는다.**
- 레이어 밖이 가장 센 것(1번)이 그 설계를 드러낸다 — **아무것도 안 한 코드가 기본으로 가장 세다.**

**유틸리티 클래스를 항상 이기게 하려면**

- **가장 나중 레이어**에 둔다(`@layer reset, base, components, utilities;`).
- 레이어 밖에 둬도 이기지만, 그러면 **나중에 그 위에 무엇을 얹을 수단이 없어진다.**

### 10. 다른 주제와 잇기

**`revert-layer` 의** 「**앞 레이어**」

- 이 주제의 (1) 규칙 — **이름이 처음 나타난 순서**로 정해진 레이어 순서에서 한 칸 앞이다.
- 키워드 자체의 동작은 [03번 주제](../03-inheritance-and-global-keywords/2-summary.md)가 정본이다.
- 레이어 밖에서 쓰면 앞 레이어가 없으므로 `revert` 와 같아진다(실측 `rgb(0, 0, 0)`).

**`:where()` 대 `@layer`**

| | 건드리는 단계 | 하는 일 |
|---|---|---|
| `:where()` | **5단계(명시도)** | 그 선택자의 기여를 `(0,0,0)` 으로 만든다 |
| `@layer` | **4단계(레이어)** | 명시도를 보기 **전에** 승부를 낸다 |

- 그래서 `:where()` 로 누른 규칙끼리는 **6단계(순서)** 로 내려가지만, 레이어로 나눈 규칙끼리는 **5단계에 가지도 않는다.**
- 정본은 [02번 주제](../02-specificity/2-summary.md)와 [목록의 **11번 주제**](../11-is-where-not/).

**사용자 `!important` 를 레이어로 덮을 수 있는가**

- **없다.** 출처는 **1단계**이고 레이어는 4단계다. 1단계에서 갈리면 레이어는 불리지도 않는다.
- 사용자의 `!important` 는 작성자의 `!important` 보다 위 칸에 있다([01번 주제](../01-cascade-and-priority/2-summary.md)).
- *(이 항목은 실행 확인하지 않았다 — 이 환경에 사용자 스타일시트를 넣을 경로를 만들지 않았다. 명세 기술만 옮겼다.)*

**`@scope` 의 근접성은 어느 쪽 뒤인가**

- **명시도(5단계) 뒤, 등장 순서 앞**이다. 레이어(4단계)보다는 한참 뒤다.
- 그래서 넷이 다 걸리면 **레이어 → 명시도 → 근접성 → 순서** 차례로 읽는다. 정본은 [06번 주제](../06-scope/2-summary.md).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**하네스** — 03\~07 다섯 주제가 공유한 것이다. `@import` 가 걸린 실험만 두 번째 판(HTTP)을 썼다.

```bash
# harness.sh body.html probes.js   —  file:// 로 연다
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

# harness-http.sh — 같은 문서를 임시 디렉터리에 두고 python3 -m http.server 로 띄운 뒤
#                   같은 --dump-dom 을 http://127.0.0.1:<PORT>/index.html 에 건다.
#                   @import 는 이 판에서만 실제로 적용된다.
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 레이어 밖 대 레이어 안 (normal) | 1 | 동작 방식 (2) · A1 |
| 레이어 밖 대 레이어 안 (`!important`) | 1 | 동작 방식 (3) · A2 |
| 레이어 순서 뒤집기(`@layer theme, base;`)로 두 줄 재확인 | 1 | demo 의 「바꿔 볼 것」 · A2 |
| 재개방 · 첫 등장 순서 · 뒤에서 재나열 3경우 | 1 | 동작 방식 (1) · A3 |
| 익명 레이어 둘 · 이름 붙인 레이어 둘 | 2 | 동작 방식 (5) · A4 |
| 레이어 대 명시도 `(1,1,0)` vs `(0,1,1)` | 1 | 동작 방식 (4) · A5 |
| 중첩 레이어 `outer.inner` 대 `outer` 직속 | 1 | 동작 방식 (5) · A6 |
| `@import ... layer(vendor)` (HTTP) — app 이 이기는 판 | 1 | 동작 방식 (6) · A7 |
| `@import` 만 두고 실제 적용 확인 (HTTP / `file://` 대조) | 2 | 어디서 틀리나 7 · A7 |
| `@import` 를 규칙 뒤로 옮겼을 때 (HTTP) | 1 | A7 |
| 세미콜론 없는 사전 선언의 `cssRules.length` | 1 | A8 |
| `revert-layer` 3경우 | 1 | 동작 방식 (7) · A10 |
| demo 2개 — 값 + 「바꿔 볼 것」 단언 각 1회 | 4 | 2-summary 의 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `file://` 에서 `@import` 가 적용되지 않는 것 | `.i1 = rgb(0, 0, 0)` | 브라우저 보안 정책이지 CSS 규칙이 아니다 |
| `@layer` 지원 자체 | Baseline widely (2024-09-14) | 2차 집계(`webstatus.dev`) — 목록 README 의 표 |

**안 돌려 본 것** — ① 사용자(user) 출처 스타일시트와 레이어가 맞붙는 경우(환경 경로를 만들지 않았다). ② Firefox·Safari 에서의 재현(엔진이 없다). 둘 다 명세 기술로만 적었고 본문 해당 자리에 표시했다.

## 용어 풀이

- **캐스케이드 레이어(cascade layer)** — `@layer` 로 만든, 명시도보다 위에서 비교되는 서랍. 캐스케이드 4단계.
- **레이어 밖(unlayered)** — 어떤 레이어에도 안 들어간 규칙. normal 에서 가장 세고 important 에서 가장 약하다.
- **레이어 순서(layer order)** — 이름이 처음 나타난 순서. 한 번 정해지면 재개방·재나열로 안 바뀐다.
- **사전 선언** — `@layer a, b;` — 순서만 정하는 문. 세미콜론으로 끝내야 한다.
- **익명 레이어(anonymous layer)** — `@layer { }`. 쓸 때마다 새로 생기고 다시 열 수 없다.
- **중첩 레이어(nested layer)** — `@layer outer.inner`. 바깥 레이어 안에서 같은 규칙이 재귀적으로 성립한다.
- **prelude** — at-rule 의 이름 뒤, `;` 또는 `{` 앞까지의 부분. 여기가 무효면 at-rule 이 통째로 버려진다.
- **불투명 출처(opaque origin)** — `file://` 문서의 출처 상태. `@import` 가 조용히 실패하는 원인.
- **명시도(specificity)** — 5단계. 정본은 02번.
- **등장 순서(order of appearance)** — 6단계. 마지막 기준.
- **근접성(proximity)** — `@scope` 가 끼워 넣는 기준. 명시도 뒤·순서 앞. 정본은 06번.
