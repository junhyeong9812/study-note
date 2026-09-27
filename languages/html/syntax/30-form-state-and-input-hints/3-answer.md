# html/syntax/30 — 폼 상태·입력 보조 속성: `disabled`/`readonly`/`autofocus`/`autocomplete`/`inputmode` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [29번 주제](../29-constraint-validation/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 disabled·readonly·required·entry list·`requestSubmit`·autofocus·autofill 처리 모델·inputmode 절로 접지했다(앞 배치가 받아 둔 사본).\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 세 지점 격자다** — 45 칸을 미리 선언하고 「「없음」과 갈린 칸」·「명세 열과 갈린 칸」을 스크립트가 센다(A1).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 갈린 칸 18 / 30 — `disabled` 15 칸 전부 · `readonly` 는 `text`·`checkbox`·`textarea` 의 검증 셋 · 비활성 단추의 `requestSubmit` 은 빈 본문으로 제출 · 명세 열과 갈린 칸 1 / 45

**출력**

명세 열 파일 —

```javascript
// html29b-30-spec.js
// 명세 열 — [제출에 실리나, 순차 포커스를 받나, willValidate]
// disabled: 항목 목록에서 건너뛴다 · 포커스 가능 영역이 아니다 · 제약 검증에서 빠진다(barred)
// readonly: input 의 텍스트·날짜·number 칸과 textarea 에만 적용된다 — 적용되면 barred · checkbox 에는 적용되지 않는다 · select·button 에는 그 속성이 없다
// button: 누른(제출자) 단추만 실린다 — 이 표의 제출은 그 폼의 button 을 제출자로 준 requestSubmit 이다
const 명세 = {
  없음:     { text: [true, true, true],   checkbox: [true, true, true],   select: [true, true, true],   textarea: [true, true, true],   button: [true, true, true] },
  disabled: { text: [false, false, false], checkbox: [false, false, false], select: [false, false, false], textarea: [false, false, false], button: [false, false, false] },
  readonly: { text: [true, true, false],  checkbox: [true, true, true],   select: [true, true, true],   textarea: [true, true, false],  button: [true, true, true] },
};
```

```text
$ python3 html29b-form.py 시도 html29b-30-grid.html | sed -n '/^속성 · 대상/,$p'
속성 · 대상           제출    포커스  검증
없음 · text           예      예      예
없음 · checkbox       예      예      예
없음 · select         예      예      예
없음 · textarea       예      예      예
없음 · button         예      예      예
disabled · text       —      —      —
disabled · checkbox   —      —      —
disabled · select     —      —      —
disabled · textarea   —      —      —
disabled · button     —      —      —
readonly · text       예      예      —
readonly · checkbox   예      예      —
readonly · select     예      예      예
readonly · textarea   예      예      —
readonly · button     예      예      예
(제출 = 서버가 받은 필드에 그 이름이 있나 · 포커스 = 진짜 Tab 열여덟 번 안에 닿았나 · 검증 = willValidate)
Tab 이 닿은 곳 = 없음-text → 없음-checkbox → 없음-select → 없음-textarea → 없음-button → readonly-text → readonly-checkbox → readonly-select → readonly-textarea → readonly-button → BODY → 시작 → 없음-text → 없음-checkbox → 없음-select → 없음-textarea → 없음-button → readonly-text
폼0 의 기록 = submit(submitter=없음-button) · 서버 필드 = text,checkbox,select,textarea,button
폼1 의 기록 = submit(submitter=disabled-button) · 서버 필드 = (빈 본문)
폼2 의 기록 = submit(submitter=readonly-button) · 서버 필드 = text,checkbox,select,textarea,button
「없음」과 갈린 칸 = 18 / 30
명세 열과 갈린 칸 = 1 / 45
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- **`disabled`** — 대상 다섯의 세 지점이 **전부 「—」**(15 칸).
- **`readonly`** — 제출·포커스는 다섯 다 「예」, 검증은 **`text`·`checkbox`·`textarea` 가 「—」**(3 칸) · `select`·`button` 은 「예」.
- ★★ **폼1** — `submit(submitter=disabled-button)` 이 났고 서버 필드는 **(빈 본문)**.
- **Tab** — `없음-*` 다섯 → `readonly-*` 다섯 → `BODY` → `시작` → 다시 `없음-*` … **`disabled-*` 에는 한 번도 안 닿았다.**
- ★★★ **명세 열과 갈린 칸 1 / 45** — `readonly · checkbox` 의 검증(명세 목록으로는 「예」, Chrome 은 「—」 — A6).

### 2. 편집을 막은 칸 4 / 8(`text`·`number`·`date`·`textarea`) · `willValidate` 는 `readonly` 칸 중 `select` 만 참 · 세 폼 — 가: 제출 · 나: 제출(체크박스 없이) · 다: `invalid(t)`

**출력**

```text
$ python3 html29b-form.py 시도 html29b-30-readonly.html | sed -n '/^type /,$p'
type      readonly 칸: 전 → 뒤         짝(속성 없음): 전 → 뒤       willValidate  :read-only
text      "가" → "가"                  "가" → "가x"                 false / true  true / false
number    "1" → "1"                    "1" → "2"                    false / true  true / false
date      "2026-01-01" → "2026-01-01"  "2026-01-01" → "2027-01-01"  false / true  true / false
range     "50" → "51"                  "50" → "51"                  false / true  true / true
checkbox  "false" → "true"             "false" → "true"             false / true  true / true
radio     "false" → "true"             "false" → "true"             false / true  true / true
select    "가" → "나"                  "가" → "나"                  true / true   true / true
textarea  "가" → "가"                  "가" → "가x"                 false / true  true / false
(willValidate · :read-only 는 「readonly 칸 / 짝」)
readonly 가 사용자 편집을 막은 칸 = 4 / 8

가(text readonly required 빈 칸) · 보냄
  페이지  valueMissing=false · willValidate=false · :invalid=false → click(가보냄 · detail=1) → submit(submitter=가보냄)
  서버    필드  t=「」
나(checkbox readonly required 안 켬) · 보냄
  페이지  valueMissing=true · willValidate=false · :invalid=false → click(나보냄 · detail=1) → submit(submitter=나보냄)
  서버    필드  (없음)
다(text required 빈 칸 · readonly 없음) · 보냄
  페이지  valueMissing=true · willValidate=true · :invalid=true → click(다보냄 · detail=1) → invalid(t)
  서버    (받은 요청 없음)
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`range`·`checkbox`·`radio`·`select`** — `readonly` 칸이 짝과 **똑같이** 바뀌었다(`50 → 51` · `false → true` · `가 → 나`).
- ★★★ **`willValidate`** — `readonly` 칸은 **`select` 만 `true`**, 나머지 일곱이 `false`. 짝은 전부 `true`.
- **`:read-only`** — `readonly` 칸은 전부 `true` · 짝은 `range`·`checkbox`·`radio`·`select` 도 `true`(글자 편집 칸이 아니라서).
- **가** — `valueMissing=false · willValidate=false · :invalid=false` → 제출 · `t=「」`.
- ★★★ **나** — `valueMissing=true · willValidate=false · :invalid=false` → 제출 · 필드 `(없음)`(안 켠 체크박스는 안 실린다).
- **다** — `valueMissing=true · willValidate=true · :invalid=true` → `invalid(t)` · 서버 0.

### 3. 그냥 — `a1` · `d1` · `d1` · `e0` / `#p1` — `BODY` · `d1` · `d1` · `e0`

**출력**

```text
$ python3 html29b-form.py page html29b-30-autofocus.html
주소의 조각 = "" · document.hasFocus() = true
로드 뒤 포커스 = a1
창1.showModal() 뒤 = d1
창1.show() 뒤 = d1
창2.showModal() 뒤 (autofocus 없음) = e0
(exit 0)
```

```text
$ python3 html29b-form.py page 'html29b-30-autofocus.html#p1'
주소의 조각 = "#p1" · document.hasFocus() = true
로드 뒤 포커스 = BODY
창1.showModal() 뒤 = d1
창1.show() 뒤 = d1
창2.showModal() 뒤 (autofocus 없음) = e0
(exit 0)
```

**왜 그런가**

- ★★★ **로드 뒤 `a1`** — 후보 목록의 앞에서부터 **포커스 가능한 첫 칸**. 닫힌 `dialog` 의 `d1` 은 트리 순서로 앞이지만 포커스 가능 영역이 아니라 건너뛰고, `a2` 는 둘째라 안 쓰인다.
- **`showModal()`·`show()` → `d1`** — 대화상자가 **보일 때** 그 안의 `autofocus` 를 고른다. autofocus 가 없는 `창2` 는 **첫 포커스 가능 칸 `e0`**.
- ★★★ **`#p1` → `BODY`** — 「최상위 문서에 **조각 대상**이 있으면 후보를 비운다」. 대화상자 쪽은 같다.

### 4. 규칙대로면 그대로 · 어긋나면 `""` · `EMAIL` 만 `"email"`(명세는 `"EMAIL"`) · 트리에 흔적 없음(0 / 24)

**출력**

명세 열 파일 —

```javascript
// html29b-30-hints-spec.js
// 명세 열 — autocomplete 는 「IDL-exposed autofill value」(Autofill 처리 모델), inputMode 는 「알려진 값으로만 제한된 반영」
// 처리 모델: 마지막 토큰이 필드 이름 → IDL 값은 그 토큰 그대로 · 앞의 home/work 등은 Contact 필드 앞에서만 · shipping/billing 은 목록의 글자(소문자)
//            · section-* 는 소문자로 · 규칙에 안 맞으면 default = 빈 문자열 · off/on 은 토큰이 하나일 때만
const 명세값 = {
  c1: "email", c2: "EMAIL", c3: "shipping email", c4: "shipping email", c5: "section-a billing tel",
  c6: "home email", c7: "", c8: "", c9: "", c10: "off", c11: "", c12: "current-password webauthn",
  c13: "", c14: "", c15: "street-address", c16: "country", c17: "",
  m1: "numeric", m2: "numeric", m3: "decimal", m4: "none", m5: "", m6: "", m7: "",
};
```

```text
$ python3 html29b-form.py page html29b-30-hints.html
id   속성 글자                         IDL 값                        명세 열                       접근성 노드의 속성
c1   "email"                           "email"                       "email"                       invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c2   "EMAIL"                           "email"                       "EMAIL"                       invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c3   "shipping email"                  "shipping email"              "shipping email"              invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c4   "Shipping email"                  "shipping email"              "shipping email"              invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c5   "section-A billing tel"           "section-a billing tel"       "section-a billing tel"       invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c6   "home email"                      "home email"                  "home email"                  invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c7   "home name"                       ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c8   "email shipping"                  ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c9   "e-mail"                          ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c10  "off"                             "off"                         "off"                         invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c11  "shipping off"                    ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c12  "current-password webauthn"       "current-password webauthn"   "current-password webauthn"   invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c13  ""                                ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c14  (속성 없음)                       ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c15  "street-address"                  "street-address"              "street-address"              invalid=false focusable=true editable=plaintext settable=true multiline=true readonly=false required=false
c16  "country"                         "country"                     "country"                     invalid=false focusable=true hasPopup=menu expanded=false
c17  (속성 없음) · form off            ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m1   inputmode="numeric"               "numeric"                     "numeric"                     invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m2   inputmode="NUMERIC"               "numeric"                     "numeric"                     invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m3   inputmode="decimal"               "decimal"                     "decimal"                     invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m4   inputmode="none"                  "none"                        "none"                        invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m5   inputmode="zzz"                   ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m6   (속성 없음)                       ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m7   (속성 없음) · type=number         ""                            ""                            invalid=false focusable=true editable=plaintext settable=true required=false valuemin=0 valuemax=0 valuetext=
명세 열과 갈린 칸 = 1 / 24
접근성 노드에 나온 속성 이름 = editable · expanded · focusable · hasPopup · invalid · multiline · readonly · required · settable · valuemax · valuemin · valuetext
(exit 0)
```

**왜 그런가**

- **맞는 것** — `email` · `shipping email` · `home email` · `off` · `current-password webauthn` · `street-address`(`textarea`) · `country`(`select`).
- **소문자로** — `Shipping email` → `"shipping email"` · `section-A billing tel` → `"section-a billing tel"`.
- ★★★ **`""`** — `home name`(`home` 은 연락처 필드 앞에만) · `email shipping`(필드가 끝이 아님) · `e-mail`(없는 필드) · `shipping off`(`off` 는 토큰 하나) · 빈 속성 · 속성 없음 · **폼이 off 인 칸**.
- ★★★ **`EMAIL`** — Chrome **`"email"`** · 명세 열 `"EMAIL"` → **갈린 칸 1 / 24**(A10).
- **`inputMode`** — `numeric`·`NUMERIC`(→ `numeric`)·`decimal`·`none` 은 그대로, `zzz`·속성 없음·`type=number` 는 `""`.
- ★★★ **접근성 노드** — 나온 속성 이름 12 개 중 **`autocomplete`·`inputmode` 에 해당하는 것이 없다.** 같은 타입의 칸은 토큰이 달라도 **같은 줄**이다.

### 5. 「체크박스·단추 같은 컨트롤에는 읽기 전용과 비활성 사이에 쓸모 있는 구별이 없다」 · `select`·`button` 에는 그 속성이 아예 없다

- 명세의 `readonly` 절 — 「**텍스트 컨트롤만** 읽기 전용이 될 수 있다. 다른 컨트롤(체크박스·단추 등)에는 읽기 전용과 비활성 사이에 **쓸모 있는 구별이 없어서** `readonly` 가 **적용되지 않는다**」. 그리고 상태마다의 「지정하지 말아야 하고 적용되지 않는」 목록에 Checkbox·Radio·Range 등이 `readonly` 를 올린다.
- `select`·`button` 은 **콘텐츠 속성 목록에 `readonly` 가 없다**(`select` 는 `autocomplete`·`disabled`·`form`·`multiple`·`name`·`required`·`size`). 달아도 전역 속성이 아닌 **모르는 속성**일 뿐이다 — A1·A2 의 `select` 가 「없음」과 같았다.

### 6. 목록으로 읽으면 참(검증에 남음) · `readonly` 절을 글자대로 읽으면 거짓 · Chrome 은 거짓 — 이탈로 세지 않고 「판별」

- **목록 쪽** — Checkbox 상태의 목록에 `readonly` 가 「**적용되지 않는다**」. [28번](../28-validation-attributes/2-summary.md)은 이 목록을 「적용되지 않는 속성은 **아무 효과도 없다**」로 읽었고 42 칸이 그대로 맞았다. 그 읽기라면 `readonly` 체크박스는 **검증 후보에 남는다.**
- **`readonly` 절 쪽** — 「`readonly` 속성이 **`input` 요소에 지정되면** 그 요소는 제약 검증에서 빠진다」 — **타입 조건이 없다.**
- **Chrome** — A2 에서 `checkbox`·`radio`·`range` 의 `readonly` 칸이 **전부 `willValidate=false`**. 뒤 문장을 글자대로 읽은 쪽이다. 두 문장이 **서로 다른 결론**을 내는 자리라 「명세와 갈렸다」고 단정하지 않는다 — 결과로 **`readonly required` 체크박스가 필수 검사를 잃는다**(A7)는 것이 실무의 요점이다.

### 7. 글자 칸 — 「mutable 이고 값이 빈 문자열이면」 · 체크박스 — 「required 이고 체크가 거짓이면」 · 둘 다 `willValidate` 가 거짓이라 검증이 안 돈다

- **글자 칸** — `required` 의 제약에 **「요소가 mutable 이고」** 가 있다. `readonly` 텍스트 컨트롤은 mutable 이 아니다 → **`valueMissing=false`**.
- **체크박스** — Checkbox 상태의 제약은 「required 이고 **checkedness 가 거짓**이면 missing」 — mutable 조건이 없다 → **`valueMissing=true`**.
- ★★★ **그래도 둘 다 제출됐다** — 검증은 **후보(`willValidate=true`)인 칸만** 본다(정적 검증 — 「후보가 아니면 다음 칸으로」). 둘 다 후보가 아니다. **깃발이 서 있어도(나) 검증은 모른다.**

### 8. 「제출 단추가 아니면 `TypeError`」 · 「소유자가 이 폼이 아니면 `NotFoundError`」 — 비활성은 묻지 않는다 · 항목 목록이 비활성 필드를 건너뛴다

- 명세의 `requestSubmit(submitter)` — ① 제출 단추가 아니면 `TypeError` ② 폼 소유자가 이 폼이 아니면 `NotFoundError` → 아니면 **그 단추에서 제출**. 비활성 검사가 **없다**(A1 의 폼1 이 제출됐다).
- 항목 목록 만들기 — 「필드가 **disabled** 면 건너뛴다」가 **「단추인데 제출자가 아니면」보다 앞**에 있다. 제출자여도 비활성이면 안 실린다 → **빈 본문**.

### 9. 확인하지 않았다(못 잰다) — 잰 것은 IDL 값과 트리의 침묵 · 못 잰 것은 가상 키보드

- ★★★ **못 잰 것** — 데스크톱 headless Chrome 에는 **가상 키보드가 없다.** 「숫자 자판이 뜬다」는 명세의 **「UA 는 숫자 입력이 가능한 가상 키보드를 보여야 한다(should)」** 까지이고, 이 판은 **관찰하지 못했다.**
- **잰 것** — `inputMode` 가 **알려진 값으로만** 반영된다(`NUMERIC` → `numeric` · `zzz` → `""`) · `type=number` 는 `inputMode` 를 채우지 않는다 · **접근성 트리에 흔적이 없다**(A4 — 18-A).

### 10. `EMAIL` → `email` — 구현(명세와 갈림 · 이탈 1) · `readonly` 체크박스 — 구현(명세 판별) · 조각이면 `autofocus` 없음 — 명세대로

- **`autocomplete="EMAIL"`** — 처리 모델은 필드 토큰을 **대소문자 무시로 비교**하고 IDL 값을 「**field 와 같은 값**」으로 둔다. 소문자 변환은 `section-*` 에만 있다 → Chrome 의 `"email"` 은 **알고리즘의 「IDL value 를 field 로」 단계와 갈린다.**
- **`readonly` 체크박스** — 두 문장이 부딪히는 자리를 Chrome 이 한쪽으로 읽은 것(A6).
- **`#조각` 이면 `autofocus` 없음** — 「autofocus 후보 비우기」의 **「조각 대상이 있으면 비운다」** 그대로.

### 11. 정본 경계

- **`disabled`/`readonly` 의 제출** — [24번](../24-input-types-choice-special/2-summary.md)(첫 측정) · 여기(세 지점).
- **`fieldset[disabled]`** — [27번](../27-fieldset-and-legend/2-summary.md).
- **포커스 순서와 `tabindex`·`inert`** — 목록의 **45번 주제**.
- **`dialog` 의 포커스 트랩** — 목록의 **47번 주제**.
- **`:read-only`·`:disabled` 로 칠하기** — [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800` · `--force-renderer-accessibility`. **엔진은 이것 하나다.** 하네스는 [29번](../29-constraint-validation/3-answer.md)의 `html29b-form.py`·`html29b-cdp.py`·`html29b-rec.js` 다.\
★ **Tab** — `Input.dispatchKeyEvent` 의 `Tab`(가상 키코드 9)을 열여덟 번. 매번 `document.activeElement` 의 `id` 를 모았다.\
★ **`autofocus`** — 페이지를 연 뒤 **`requestAnimationFrame` 두 번**을 기다리고 물었다(후보 비우기는 렌더 갱신 단계에서 돈다). 같은 판에서 `document.hasFocus()` 가 `true` 였다.

**흔들림 확인** — 캡처 세 판의 재대조는 [29번](../29-constraint-validation/3-answer.md)의 `## 실행 검증` 에 있다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **세 지점 격자 45 칸** | 3 | 동작 방식 (1) · A1 |
| **`readonly` 여덟 타입 · 세 폼** | 3 | 동작 방식 (2) · A2 |
| **`autofocus` 두 판** | 3 | 동작 방식 (3) · A3 |
| **`autocomplete`·`inputmode` 24 칸** | 3 | 동작 방식 (4) · A4 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `readonly` 가 적용되지 않는 `input` 의 `willValidate` | `false` | 명세 두 문장이 부딪힌다 |
| 필드 토큰의 대소문자 | 소문자로 돌려준다 | 명세는 그대로 |

**안 돌려 본 것** — ① **`contenteditable` 의 `inputmode`.** ② **`autocomplete` 의 `webauthn` 이 실제로 무엇을 띄우나**(IDL 값만). ③ **`popover` 안의 `autofocus`**(명세 문장만).

**못 잰 것** — ① **가상 키보드.** ② **자동 완성 제안 UI.** ③ **보조 기술이 `autocomplete` 를 쓰나.**

**부적용인 창** — **창 ① · ③ · ④ · ⑥**.

## 용어 풀이

- **세 지점** — 제출(서버) · 순차 포커스(Tab) · 검증(`willValidate`).
- **mutable** — 사용자가 값을 바꿀 수 있는 상태.
- **autofocus 후보 목록** — 앞에서부터 한 번 쓰고 끝나는 목록.
- **IDL-exposed autofill value** — `element.autocomplete` 의 값.
