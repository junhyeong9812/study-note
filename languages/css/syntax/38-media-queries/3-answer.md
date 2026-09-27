# css/syntax/38 — 미디어 쿼리: 문법·범위 구문·논리 연산 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려 읽은 것**이다.\
> **뷰포트 폭은 `--window-size=W,H` 로 바꿔 가며 잰다** — 경계값은 599·600·601 을 **각각 따로 띄워** 찍었다.\
> 규칙은 [Media Queries Level 4](https://drafts.csswg.org/mediaqueries-4/) 로 접지했다.\
> **엔진은 Chrome 하나다.** `@import`·`<link>` 실험만 로컬 HTTP 서버로 띄웠다(A9 참고).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 경계는 어느 쪽에 포함되는가

**출력** (Chrome 151 headless — 같은 문서를 폭만 바꿔 세 번 띄웠다)

```text
  --window-size=599,400        --window-size=600,400        --window-size=601,400
  innerWidth = 599             innerWidth = 600             innerWidth = 601
  .a = rgb(254, 202, 202)      .a = rgb(254, 202, 202)      .a = rgb(226, 232, 240)
  .b = rgb(226, 232, 240)      .b = rgb(191, 219, 254)      .b = rgb(191, 219, 254)
  .c = rgb(254, 202, 202)      .c = rgb(191, 219, 254)      .c = rgb(191, 219, 254)
```

**599px 일 때**

- `.a` **분홍**(`#fecaca`) · `.b` **회색**(`#e2e8f0`) · `.c` **분홍**.
- `max-width: 600px` 만 참이다.

**600px 일 때**

- `.a` **분홍** · `.b` **파랑**(`#bfdbfe`) · `.c` **파랑**.
- ★ **둘 다 참**이다. `.c` 에는 두 규칙이 다 적용됐고 파랑이 이겼다.

**601px 일 때**

- `.a` **회색** · `.b` **파랑** · `.c` **파랑**.
- `min-width: 600px` 만 참이다.

**승자를 정한 단계**

- **6단계, 등장 순서**다. 두 규칙의 명시도는 `(0,1,0)` 로 같고 레이어도 같다.\
  `min-width` 쪽 `@media` 가 **뒤에 적혀 있어서** 이겼다 — 두 `@media` 의 순서를 바꾸면 분홍이 된다.

```text
   수직선
     598   599   600   601   602
   ---+-----+-----+-----+-----+--->
      |<---- max-width: 600px ---|
                    |---- min-width: 600px ---->
                    ^^^ 겹치는 1픽셀
```

### 2. 겹침을 없애는 방법

**`max-width: 599px` / `min-width: 600px`**

```text
실측 — 뷰포트 899px 에서 확인 (겹침 자체는 599/600 표로 확인)
  (max-width: 599px) = false     (min-width: 600px) = true
  두 조건이 동시에 참이 되는 정수 폭은 없다
```

- **겹침은 사라진다.** 정수 폭만 놓고 보면 599 이하 / 600 이상으로 깔끔히 나뉜다.

**남기는 틈 — 그리고 「못 잰 것」**

- 미디어 쿼리의 폭은 **정수가 아닐 수 있다.** 실측에서 `matchMedia("(width >= 599.5px)")` 가 **파싱되어 `true`** 를 돌려줬다 — **소수 비교가 실제로 평가된다.**
- 그러면 599.5px 같은 폭에서는 **두 규칙 다 거짓**이 되어 아무것도 안 걸린다.
- ★ 다만 **이 환경에서 소수 뷰포트 폭을 만들지 못했다.** `--force-device-scale-factor` 를 1.25·1.5 로 줘도 CSS 픽셀 폭은 `900`·`902` 처럼 정수로 나왔다.\
  **틈이 실제로 나는 것은 못 보였다** — 「안 돌려 봄」이 아니라 **측정 수단이 없어 못 잰 것**이다.

**오늘의 정공법**

- **범위 구문의 배타 연산자**다. `@media (width < 600px)` 와 `@media (width >= 600px)` 은 **겹치지도 비지도 않는다.**
- 옛 표기로 못 하는 이유 — `min-`/`max-` 에는 **「미만」·「초과」가 아예 없다.** 언제나 이상·이하뿐이다.

### 3. 모르는 기능을 만나면

**출력** (Chrome 151 headless, 뷰포트 800px)

```text
.a1 = rgb(0, 0, 0)
.a2 = rgb(0, 0, 0)
cssRules.length = 16            (같은 실험의 전체 시트 기준 — 하나도 안 사라졌다)
conditionText   = "(totally-unknown-zz: 1)"  /  "(min-width: bogus)"
matchMedia("(totally-unknown-zz: 1)").matches = false
matchMedia("(min-width: bogus)").matches      = false
matchMedia("(min-width: bogus)").media        = "(min-width: bogus)"
```

**두 문단의 색**

- **둘 다 검정**(`rgb(0, 0, 0)`). 규칙이 적용되지 않았다.

**`cssRules.length`**

- 실험 시트에 담은 열여섯 규칙이 **그대로 열여섯**이었다. **하나도 안 버려졌다.**

**`conditionText`**

- **내가 쓴 문자열이 그대로** 들어 있다 — `(min-width: bogus)` 처럼 뜻이 없는 것까지.\
  파서는 `(이름: 값)` 모양만 확인하고 통과시켰다는 뜻이다.

**07번과 같은 이야기인가**

- **다른 이야기다.**

```text
   07번 "모르는 at-rule"                   여기 "모르는 미디어 기능"
   @zzz { … }                              @media (zzz: 1) { … }
   -> cssRules 에 없다 (버려짐)             -> cssRules 에 있다 (조건이 거짓)
   고칠 곳: 문법·지원 여부                   고칠 곳: 조건·환경
```

- 07번 실측에도 같은 문장이 있다 — 「**안 버려졌다. 조건이 거짓일 뿐이다**」.

### 4. `not` 의 결합 범위

**출력** (Chrome 151 headless, 뷰포트 800px)

```text
.a3 = rgb(0, 0, 0)        안 먹었다
.c3 = rgb(21, 128, 61)    먹었다
matchMedia("not all and (min-width: 1px)").matches = false
```

**두 문단의 색**

- `.a3` **검정** — 조건이 거짓이다.
- `.c3` **초록** — 조건이 참이다.

**괄호로 풀어 쓰면**

```text
  not all and (min-width: 1px)
= not ( all and (min-width: 1px) )
       ^^^^^^^^^^^^^^^^^^^^^^^^^   뷰포트 800px 에서 참
  -> 전체는 거짓
```

- **`not` 은 바로 뒤 한 항이 아니라 이어지는 것 전체를 부정한다.**

**모르는 기능을 `not` 으로 감싸면**

- 모르는 기능은 **거짓**이므로 `not (모르는 기능)` 은 **항상 참**이 된다.
- 곧 「이 기능이 없는 브라우저에만 적용하겠다」고 쓴 것이 **그 기능을 지원하는 최신 브라우저에서도 켜진다.**\
  「미지원이면 무시되겠지」라는 직관이 **정확히 반대로** 나오는 자리다.

### 5. 쉼표와 `or`

**출력** (Chrome 151 headless, 뷰포트 800px)

```text
(min-width: 99999px), (min-width: 1px)        -> .a7  = rgb(21, 128, 61)   적용됨
((min-width: 99999px) or (min-width: 1px))    -> .a8  = rgb(21, 128, 61)   적용됨
zzunknown, (min-width: 1px)                   -> .c9  = rgb(21, 128, 61)   적용됨
```

**둘의 차이**

- **결과는 같다**(둘 다 OR). 문법 위치가 다르다 — 쉼표는 **최상위에서 여러 미디어 쿼리를 나열**하는 것이고, `or` 는 **하나의 조건 안에서 괄호로 묶어** 쓰는 것이다.

**최상위 `or`**

- **쓸 수 없다.** `@media (a) or (b)` 는 문법이 아니다. 최상위에서는 쉼표를 쓴다.

**`zzunknown, (min-width: 1px)`**

- **적용된다.** 왼쪽 항은 알 수 없는 미디어 타입이라 거짓이지만, 쉼표 목록은 **하나만 참이면 참**이다.

**닮은 것**

- 선택자의 **`:is()` 같은 「너그러운 목록」**([11번 주제](../11-is-where-not/2-summary.md))이다.\
  다만 방향이 조금 다르다 — 선택자의 쉼표 목록은 **한 몸이라 하나가 무효면 전부 죽는데**([07번](../07-syntax-and-error-recovery/2-summary.md)), **미디어 쿼리의 쉼표 목록은 항마다 독립**이다. **같은 기호가 반대로 동작한다.**

### 6. 미디어 타입

**출력** (Chrome 151 headless, 뷰포트 800px)

```text
@media tv and (min-width: 1px)      -> .a6  = rgb(0, 0, 0)        안 먹음
@media print                        -> .c10 = rgb(0, 0, 0)        안 먹음
@media { … }                        -> .a12 = rgb(185, 28, 28)    ★ 먹었다
   그 규칙의 conditionText = ""
@media only screen and (min-width: 1px) -> .a14 = rgb(21, 128, 61) 먹음
matchMedia("").matches    = true
matchMedia("all").matches = true
```

**`tv`**

- **적용 안 된다.** MQ4 가 `tv`·`handheld` 등을 폐기했다 — 문법상 쓸 수는 있지만 **아무것도 매치하지 않는다.**

**조건을 아예 비우면**

- **적용된다.** 빈 조건은 `all` 과 같다(실측: `matchMedia("").matches = true`).

**`only`**

- **영향이 없다.** `only screen and (min-width: 1px)` 이 정상 매치했다.\
  CSS2 시대 파서가 `screen and (…)` 을 잘못 읽는 것을 막으려던 접두이고 오늘 의미가 없다.

**타입을 안 쓰면**

- **`all` 로 취급**된다. `@media (min-width: 600px)` = `@media all and (min-width: 600px)`.

### 7. 미디어 쿼리는 무엇을 바꾸는가

**출력** (Chrome 151 headless, 뷰포트 800px)

```text
.a11 = rgb(29, 78, 216)      파랑.  #id-a11 이 이겼다
```

**이 문단의 색**

- **파랑**(`#1d4ed8`). `@media` 조건이 참인데도 `.a11` 규칙이 졌다.

**작용하는 단계**

```text
   1 출처·중요도  2 요소 안 스타일  3 레이어  4 명시도  5 근접성  6 등장 순서
                                                                   ^^^^^^^^^
                                            @media 는 여기서만 작용한다
```

- `@media` 는 **규칙을 켤지 말지**만 정한다. 켜진 규칙은 명시도 `(0,1,0)` 그대로 경쟁한다.

**명시도가 같을 때**

- **등장 순서**가 정한다. 실측 두 판이 이렇다.

```text
  @media (min-width: 1px) { .c1 { 빨강 } }     .c2 { 파랑 }
  .c1 { 파랑 }                                 @media (min-width: 1px) { .c2 { 빨강 } }
  -> .c1 = rgb(29, 78, 216)  파랑              -> .c2 = rgb(185, 28, 28)  빨강
     뒤에 쓴 쪽이 이긴다                          뒤에 쓴 쪽이 이긴다
```

**모바일 우선 관례**

- 순서가 곧 우선순위이므로, **작은 화면 스타일을 먼저 쓰고 `min-width` 를 오름차순으로 쌓으면** 큰 화면 규칙이 자동으로 뒤에 온다.\
  명시도를 건드릴 필요가 없어지고, `!important` 도 안 쓰게 된다.

### 8. 범위 구문의 대응

**출력** (Chrome 151 headless)

```text
(400px <= width <= 700px)         800px 에서 false · 599/600/601 에서 true
(600px <= width)                  599 false · 600 true · 601 true
(width >= 600px)                  599 false · 600 true · 601 true
mediaText 정규화
  "(min-width:400px) and (max-width:700px)" -> "(min-width: 400px) and (max-width: 700px)"
  "(width >= calc(100px + 100px))"          -> "(width >= calc(200px))"
```

**한 줄로 쓰면**

- **`(400px <= width <= 700px)`** 다.

**`(600px <= width)`**

- **같다.** 기능 이름을 오른쪽에 둬도 된다. 세 폭에서 `(width >= 600px)` 과 값이 전부 일치했다.

**범위 구문에만 있는 연산자**

- **`<` 와 `>`**(배타)다. 옛 `min-`/`max-` 에는 대응이 없다.

**`calc` 의 직렬화**

- **`(width >= calc(200px))`** 로 담긴다. 파서가 계산을 접어 넣고 `calc()` 껍데기는 남긴다.\
  ★ **내가 쓴 글자와 파서가 이해한 형태는 다르다** — 진단할 때 `mediaText` 를 읽는 이유다.

### 9. 중첩과 `@import`

**출력** (Chrome 151 headless + 로컬 HTTP 서버)

```text
@media (min-width: 1px) { @media (max-width: 99999px) { .a10 { … } } }
   .a10 = rgb(21, 128, 61)        적용됨

.z { color: #000; @media (min-width: 1px) { .z1 { color: #15803d } } }
   .z1 = rgb(21, 128, 61)
   cssText = .z { color: rgb(0, 0, 0); @media (min-width: 1px) { & .z1 { … } } }
                                                                ^^^

@media (min-width: 1px) { @import url("a.css"); }
   cssRules.length = 2   rules = [CSSMediaRule:(min-width: 1px), CSSStyleRule:.after]
   그 @media 의 안쪽 cssRules = []          ★ @import 가 사라졌다
   .imp = rgb(0, 0, 0)                      a.css 가 적용 안 됨
   서버 로그에 GET /a.css 가 아예 없다      ★ 요청조차 안 갔다
   .after = rgb(29, 78, 216)                뒤 규칙은 멀쩡하다

<link rel="stylesheet" media="print" href="print.css">
<link rel="stylesheet" media="(min-width: 99999px)" href="a.css">
   서버 로그
     GET /print.css HTTP/1.1  200
     GET /a.css HTTP/1.1      200          ★ 둘 다 내려받았다
   .pr = rgb(0, 0, 0)   .imp = rgb(0, 0, 0)   적용은 안 됨
```

**중첩된 조건**

- **AND 로 합쳐진다.** 둘 다 참이어야 적용된다.

**규칙 안에 넣으면**

- 파서가 **`&` 를 붙인다.** `.z` 안의 `.z1` 은 `& .z1`, 곧 `.z .z1` 이 된다([14번 주제](../14-css-nesting/2-summary.md)).

**`@media` 안의 `@import`**

- **조용히 사라진다.** `@media` 규칙은 남는데 안쪽이 **비어 있고**, 네트워크 요청도 **안 나갔다.**\
  `@import` 는 시트 맨 앞에만 올 수 있기 때문이다. 조건은 `@import url("a.css") screen and (…);` 처럼 **`@import` 쪽에** 단다.

**`<link media="print">`**

- **내려받는다.** 서버 로그에 `200` 이 찍혔다. 조건이 거짓이면 **적용만 안 될 뿐** 네트워크는 그대로 탄다.\
  「조건이 거짓이니 안 받겠지」는 틀린 최적화 기대다.

### 10. 다른 주제와 잇기

**무엇을 기준으로 재는가**

```text
   @media        뷰포트(창)          — 페이지 전체가 같은 답을 본다
   @container    가장 가까운 조상 컨테이너 상자 — 같은 페이지에서 답이 갈린다
   @supports     브라우저가 그 문법을 아는가 — 화면 크기와 무관
```

**「브라우저가 아는가」**

- **`@supports`** 다([41번 주제](../41-supports-feature-queries/2-summary.md)). `@media` 로는 지원 여부를 못 묻는다 — 모르는 기능은 그냥 거짓이 될 뿐 **아는지 모르는지를 구별해 주지 않는다.**

**진단 3창에 더할 것**

- **`matchMedia(조건).matches`** 다. 규칙이 담겼는지(`cssRules`)와 **조건이 참인지**는 별개의 질문이고, at-rule 에서는 뒤엣것이 원인인 경우가 훨씬 많다.
- 함께 **`conditionText` / `media.mediaText`** 를 읽어 **파서가 무엇으로 이해했는지**를 확인한다.

**헤드리스 값의 일반화**

```text
실측 (이 머신 · headless)
  (hover: hover)                      false      <- 사람의 데스크톱은 보통 true
  (pointer: fine)                     false
  (any-hover: hover)                  false
  (prefers-reduced-motion: reduce)    false
  (scripting: enabled)                true
  (update: fast)                      true
  (orientation: landscape)            true
  (color)                             true
  (monochrome)                        false
```

- **입력 장치가 없는 환경**이라 포인터·호버 계열이 전부 거짓이다.
- 이 값들은 **언어 규칙이 아니라 환경**이다. 「이 기능은 거짓이다」로 적으면 사람이 쓰는 브라우저에 대해 틀린 말이 된다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**하네스** — 37\~41 다섯 주제가 공유한 것이다. **이 주제는 `--window-size` 를 바꿔 가며 같은 문서를 여러 번 띄우는 것이 본체**다.

```bash
# harness.sh body.html probes.js W H
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
for w in 599 600 601; do
  google-chrome --headless --disable-gpu --no-sandbox --window-size=$w,400 --dump-dom "$D/index.html"
done

# @import / <link> 실험만 로컬 HTTP
(cd srv && python3 -m http.server 8755) &
google-chrome --headless --disable-gpu --no-sandbox --dump-dom http://127.0.0.1:8755/index.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 경계값 599 / 600 / 601 — 옛 표기 2종 + 범위 구문 3종 + `matchMedia` 5종 | 3 | 동작 방식 (2) · A1 |
| demo 3줄을 599 / 600 / 601 / 780 네 폭에서 | 4 | demo · A1 |
| demo 의 「바꿔 볼 것」 — `@media` 순서 뒤바꿈 (599/600/601) | 3 | demo |
| demo 의 「바꿔 볼 것」 — `(width < 600px)` 로 교체 (599/600/601) | 3 | demo |
| 모르는 기능·모르는 값 두 규칙 + `cssRules` 전수 | 1 | 동작 방식 (1)(5) · A3 |
| `not` 4종(`not all and`·`not (…)`·`not screen and`·`not screen`) | 2 | 동작 방식 (4) · A4 |
| 쉼표 · `or` · `and` · 알 수 없는 타입 섞은 쉼표 | 2 | 동작 방식 (4) · A5 |
| 미디어 타입 5종(`screen`·`tv`·`print`·빈 조건·`only screen`) | 2 | 동작 방식 (6) · A6 |
| 명시도 대 미디어 쿼리 1판 + 순서 2판 | 2 | 동작 방식 (7) · A7 |
| 범위 구문 ↔ 옛 표기 대응 + `calc` 직렬화 + `mediaText` 전수 | 2 | 동작 방식 (3) · A8 |
| 중첩 `@media` · 규칙 안 `@media` | 1 | 동작 방식 (8) · A9 |
| `@media` 안의 `@import` (HTTP, 서버 로그 포함) | 1 | A9 |
| `<link media>` 두 개의 다운로드 여부 (HTTP, 서버 로그) | 1 | A9 · 더 들어가면 |
| 환경 기능 12종(`hover`·`pointer`·`scripting`·`update` 등) | 1 | 어디서 틀리나 6 · A10 |
| 소수 폭 실험(`--force-device-scale-factor` 1 / 1.25 / 1.5) | 3 | A2 — **못 잰 것** |
| **제출 직전 demo 재추출·재실행 대조** | 1 | 어긋남 0건 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `conditionText` 가 원문을 유지하는 것 | `(min-width: bogus)` | CSSOM 직렬화 세부다 |
| `calc` 가 접히는 것 | `(width >= calc(200px))` | 〃 |
| `(hover: hover)` 등 환경 기능 | 전부 `false` | **환경**이다. 사람의 브라우저와 다르다 |
| 창 폭 하한 | `--window-size=400` 에서도 `innerWidth = 500` | 이 머신의 Chrome 창 최소 폭 |
| 스크롤바가 폭을 먹는 것 | 넘치는 문서에서 `innerWidth 800` · `clientWidth 785` (**15px**) | 스크롤바 폭은 OS·브라우저 설정에 달렸다. 넘치지 않는 문서에서는 0 이다 |
| 범위 구문 지원 | Baseline **widely** 2025-09-27 | 2차 집계(`api.webstatus.dev`) |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② 실제 인쇄 출력(`@media print` 의 적용은 화면 렌더에서 「거짓」인 것만 확인했다). ③ 500px 미만 뷰포트(창 폭 하한). 셋 다 본문에서 주장하지 않았다.

**못 잰 것** — 소수 뷰포트 폭에서 `max-width: 599px` / `min-width: 600px` 사이에 틈이 나는 것. `matchMedia("(width >= 599.5px)")` 가 **파싱되어 평가된다는 것까지는 쟀지만**, 이 환경에서 소수 CSS 픽셀 폭을 만들 수단이 없었다(DPR 을 1.25·1.5 로 줘도 폭이 정수였다). A2 에 그대로 적었다.

## 용어 풀이

- **미디어 쿼리(media query)** — 미디어 타입과 미디어 기능으로 만든 참/거짓 조건.
- **미디어 타입** — `all`·`screen`·`print` 셋. `tv` 등은 MQ4 가 폐기해 아무것도 매치하지 않는다.
- **미디어 기능** — 괄호 안에서 묻는 한 가지. 모르는 이름은 **거짓**이 된다(버려지는 게 아니다).
- **뷰포트** — 미디어 쿼리가 재는 대상. 창의 보이는 영역.
- **중단점(breakpoint)** — 레이아웃이 바뀌는 폭의 경계. 겹치면 등장 순서가 동작을 정한다.
- **범위 구문** — `(width <= 600px)` 표기. 배타 연산자 `<`·`>` 가 여기에만 있다.
- **`only`** — CSS2 파서 회피용 유물. 평가에 영향이 없다.
- **`matchMedia()`** — 조건만 따로 평가하는 JS API. at-rule 진단의 네 번째 창.
- **`conditionText` / `media.mediaText`** — 파서가 이해한 조건 문자열.
- **등장 순서** — 캐스케이드 6단계의 마지막. `@media` 가 작용하는 유일한 자리(정본은 01번).
- **너그러운 목록** — 한 항이 무효여도 나머지가 사는 목록. 미디어 쿼리의 쉼표가 그렇고, 선택자의 쉼표는 **반대**다.
