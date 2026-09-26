# html/syntax/28 — 검증 속성: `required`/`pattern`/`min`/`max`/`step`/`minlength`/`maxlength` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [25번 주제](../25-label-association/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「The input element」(상태별 적용 목록 · `pattern` · `min`/`max` · `step`)와 「Limiting user input length」 절로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 `validity` 깃발이다** — 「무시된다」는 마흔두 칸을 미리 선언하고 **깃발도 값도 안 움직인 곳**을 센 것이다(A1).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 편집 없음 26 / 42 · 편집 뒤 22 / 42 — 명세의 적용 목록과 갈린 칸 0 · `range` 는 값으로만 먹는다

**출력**

명세 열 파일 —

```javascript
// html25b-28-spec.js
// 명세 열 — 타입마다 「적용되는」 속성 목록. 명세의 상태별 「must not be specified and do not apply」 목록에서 이 표의 일곱 속성을 뺀 나머지다.
const 명세 = {
  text: ["required", "pattern", "minlength", "maxlength"], email: ["required", "pattern", "minlength", "maxlength"],
  number: ["required", "min", "max", "step"], date: ["required", "min", "max", "step"],
  checkbox: ["required"], range: ["min", "max", "step"],
};
```

```text
$ python3 html25b-form.py --lang=ko-KR 시도 html25b-28-grid.html | sed -n '/^── /,$p'
── 편집 없음 (스크립트 값만)
속성 \ 타입 text       email      number     date       checkbox   range
required    깃발       깃발       깃발       깃발       깃발       ·
pattern     깃발       깃발       ·          ·          ·          ·
min         ·          ·          깃발       깃발       ·          값 5
max         ·          ·          깃발       깃발       ·          값 5
step        ·          ·          깃발       깃발       ·          값 4
minlength   ·          ·          ·          ·          ·          ·
maxlength   ·          ·          ·          ·          ·          ·
무시된 칸 = 26 / 42  (「깃발」= 그 속성의 validity 깃발이 켜짐 · 「값 N」= 깃발 없이 값이 N 으로 고쳐짐(속성 없는 짝과 다름) · 「·」= 아무 일 없음)

── minlength·maxlength 줄을 진짜 키로 편집한 뒤
속성 \ 타입 text       email      number     date       checkbox   range
required    깃발       깃발       깃발       깃발       깃발       ·
pattern     깃발       깃발       ·          ·          ·          ·
min         ·          ·          깃발       깃발       ·          값 5
max         ·          ·          깃발       깃발       ·          값 5
step        ·          ·          깃발       깃발       ·          값 4
minlength   깃발       깃발       ·          ·          ·          ·
maxlength   깃발       깃발       ·          ·          ·          ·
무시된 칸 = 22 / 42  (「깃발」= 그 속성의 validity 깃발이 켜짐 · 「값 N」= 깃발 없이 값이 N 으로 고쳐짐(속성 없는 짝과 다름) · 「·」= 아무 일 없음)

편집 뒤의 값 — minlength: text="ab" email="a@b.cd" number="12" date="2027-01-01" checkbox="on"(checked=true) range="51"
              maxlength: text="ab" email="a@b.c" number="12" date="2027-01-01" checkbox="on"(checked=true) range="51"
명세의 적용 목록과 갈린 칸(편집 뒤) = 0 / 42
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- **먹은 칸(편집 뒤)** — `text`·`email`: `required`·`pattern`·`minlength`·`maxlength` · `number`·`date`: `required`·`min`·`max`·`step` · `checkbox`: `required` · `range`: `min`→`5` · `max`→`5` · `step`→`4`(값).
- ★★ **편집 없음 판** — `minlength`·`maxlength` 가 **`text`·`email` 에서도** 「·」 → 네 칸이 더 무시되어 **26**.
- **갈린 칸 0 / 42** — 명세 목록(`html25b-28-spec.js`)과 **한 칸도 안 갈렸다.**

### 2. `min=1 step=2` 면 `4` 는 `true` · `5` 는 `false` — 경로(스크립트·속성·키)는 무관 · `min` 이 없으면 `value` 속성이 출발점

**출력**

```text
$ python3 html25b-form.py --lang=ko-KR 시도 html25b-28-step.html | sed -n '/^id /,$p'
id  속성                                                      값을 넣은 길     .value        stepMismatch
n1  type="number" min="1" step="2"                            스크립트 "4"     "4"           true
n2  type="number" min="1" step="2"                            스크립트 "5"     "5"           false
n3  type="number" min="1" step="2" value="4"                  속성만           "4"           true
n4  type="number" step="2" value="3"                          속성만           "3"           false
n5  type="number" step="2" value="3"                          스크립트 "4"     "4"           true
n6  type="number" step="2" value="3"                          스크립트 "5"     "5"           false
n7  type="number" step="2"                                    스크립트 "3"     "3"           true
n8  type="number" min="1" step="2"                            진짜 키 "4"      "4"           true
a2  type="number" step="0.5" value="1.3"                      속성만           "1.3"         false
a2s type="number" step="0.5"                                  스크립트 "1.3"   "1.3"         true
t1  type="time" step="900" value="13:07"                      속성만           "13:07"       false
t2  type="time" step="900"                                    스크립트 "13:07" "13:07"       true
t3  type="time" step="900" min="13:00" value="13:07"          속성만           "13:07"       true
d1  type="date" step="7" min="2026-09-07" value="2026-09-10"  속성만           "2026-09-10"  true
d2  type="date" step="7" value="2026-09-10"                   속성만           "2026-09-10"  false
r1  type="range" min="1" step="2" value="4"                   속성만           "5"           false
r2  type="range" min="1" step="2"                             스크립트 "4"     "5"           false
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`n1`·`n3`·`n8` 셋 다 `true`** — 스크립트·속성·진짜 키 **어느 경로든 같다.** 눈금은 **`min` = 1** 에서 출발해 1·3·5.
- ★★★ **`n4` `false` · `n5` `true` · `n6` `false`** — `min` 이 없으니 **`value="3"`** 이 출발점(3·5·7). `n7`(둘 다 없음)은 출발점 0 이라 `3` 이 `true`.
- **`a2` `false` · `a2s` `true` · `t1` `false` · `t2` `true` · `t3` `true` · `d1` `true` · `d2` `false`** — 전부 같은 순서(A6).
- **`r1`·`r2`** — `range` 는 **`5`** 로 고쳐 깃발이 없다(A9).

### 3. `a|bc` 는 `abc` 거절 · `[a-z-]+` 는 `v` 에서 무효라 검사 없음(콘솔 한 줄) · 집합 빼기가 먹는다 · 대소문자를 가린다 · 빈 값은 안 본다

**출력**

```text
$ python3 html25b-form.py page html25b-28-pattern.html
id   pattern             .value    patternMismatch
p1   a|bc                "a"       false
p2   a|bc                "bc"      false
p3   a|bc                "abc"     true
p4   [a-z-]+             "1"       false
p5   [a-z\-]+            "1"       true
p6   [\p{L}--[a-z]]+     "ABC가"   false
p7   [\p{L}--[a-z]]+     "abc"     true
p8   \p{L}+              "가나"    false
p9   abc                 "ABC"     true
p10  x+                  ""        false

같은 글자를 JS 로 — 감싸지 않으면
  /a|bc/v.test("abc")        = true
  /^a|bc$/v.test("abc")      = true
  /^(?:a|bc)$/v.test("abc")  = false

[a-z-] 를 플래그별로 컴파일하면
  new RegExp("[a-z-]", "")  → /[a-z-]/
  new RegExp("[a-z-]", "u")  → /[a-z-]/u
  new RegExp("[a-z-]", "v")  → SyntaxError 「Invalid regular expression: /[a-z-]/v: Invalid character class」

콘솔 기록(Log.entryAdded) 1줄
  Pattern attribute value [a-z-]+ is not a valid regular expression: Uncaught SyntaxError: Invalid regular expression: /[a-z-]+/v: Invalid character class
(exit 0)
```

**왜 그런가**

- **`p1`·`p2` `false` · `p3` `true`** — `^(?:a|bc)$`. JS 로 감싸지 않은 `/a|bc/v` 와 `^`·`$` 만 붙인 `/^a|bc$/v` 는 `abc` 에 **`true`**, 명세 모양 `/^(?:a|bc)$/v` 만 **`false`**.
- ★★★ **`p4` `false`** — `new RegExp("[a-z-]", "v")` 가 **`SyntaxError 「… Invalid character class」`**(플래그 없음·`u` 는 성공). 컴파일된 패턴이 없어 **검사 자체를 안 한다.** **`p5`**(이스케이프)는 `true`.
- **`p6` `false` · `p7` `true`** — `[\p{L}--[a-z]]+` 는 `v` 의 집합 빼기. **`p8` `false`** — `\p{L}+`.
- **`p9` `true`**(대소문자) · **`p10` `false`**(빈 값).
- **콘솔 1 줄** — `p4` 의 패턴이 **유효한 정규식이 아니다**는 경고. 화면·깃발·예외로는 안 보인다.

### 4. 스크립트로 넣은 값은 둘 다 조용하다 · 진짜 편집 뒤에만 `tooLong`·`tooShort` · 치는 글자는 `abc` 에서 막힌다 · 마지막이 스크립트면 다시 꺼진다

**출력**

```text
$ python3 html25b-form.py 시도 html25b-28-length.html | sed -n '/^── /,$p'
── 편집 없음
id  속성          .value    tooLong  tooShort 무엇을 했나
m1  maxlength=3   "abcdef"  false    false    스크립트 "abcdef" → (둘째 시도) End + Backspace
m2  maxlength=3   ""        false    false    (둘째 시도) 진짜로 "abcdef" 를 친다
m3  minlength=5   ""        false    false    (둘째 시도) 진짜로 "ab" 를 친다
m4  minlength=5   "ab"      false    false    스크립트 "ab"
m5  maxlength=3   "abcdef"  false    false    스크립트 "abcdef" → (둘째 시도) End + Backspace → 스크립트 "abcdef"
m6  maxlength=3   "abcdef"  false    false    자식 텍스트 "abcdef"

── 진짜 키로 편집
id  속성          .value    tooLong  tooShort 무엇을 했나
m1  maxlength=3   "abcde"   true     false    스크립트 "abcdef" → (둘째 시도) End + Backspace
m2  maxlength=3   "abc"     false    false    (둘째 시도) 진짜로 "abcdef" 를 친다
m3  minlength=5   "ab"      false    true     (둘째 시도) 진짜로 "ab" 를 친다
m4  minlength=5   "ab"      false    false    스크립트 "ab"
m5  maxlength=3   "abcdef"  false    false    스크립트 "abcdef" → (둘째 시도) End + Backspace → 스크립트 "abcdef"
m6  maxlength=3   "abcdef"  false    false    자식 텍스트 "abcdef"
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- **편집 없음** — 여섯 칸 전부 `false`·`false`(`m1`·`m5` 는 `"abcdef"` 인데도).
- ★★★ **편집 뒤** — `m1` **`"abcde"` · `tooLong true`** · `m2` **`"abc"`**(막힘) · `false` · `m3` **`"ab"` · `tooShort true`** · `m4` `false`(스크립트) · **`m5` `false`**(편집 뒤 스크립트가 다시 넣었다) · `m6` `false`(자식 텍스트).

### 5. 상태별 「지정하지 말아야 하고 적용되지 않는」 목록 · `range` 는 빈 값이 없어서 · `checkbox` 는 `required` 하나

- 명세는 `input` 의 **상태마다** 「다음 콘텐츠 속성은 **지정하지 말아야 하고 적용되지 않는다**」 목록을 둔다. Number 상태의 목록에 **`pattern`·`minlength`·`maxlength`** 가, Text 상태의 목록에 **`min`·`max`·`step`** 이 있다. **적용되지 않는 속성은 제약도 만들지 않는다** — 그래서 깃발이 없다(A1).
- **`range`** — 목록에 **`required`** 가 있다(값이 언제나 있는 컨트롤이라 「빠짐」이 성립하지 않는다 — 해석이다). **`checkbox`** — 일곱 중 **`required` 만** 남는다(`max`·`maxlength`·`min`·`minlength`·`pattern`·`step` 이 목록에 있다).

### 6. `min` → `value` 속성 → 타입의 기본 기준 → 0 · 23편의 `a2`·`a6` 은 `value` 속성이 출발점이라 눈금 위에 있었다

- 명세의 step base — ① **`min` 속성**이 있고 수로 바뀌면 그 값 · ② **`value` 속성**이 있고 수로 바뀌면 그 값 · ③ 타입에 **기본 기준**이 있으면 그것(`week`) · ④ **0**.
- ★★★ **23편의 `a2`(`step=0.5 value="1.3"`)** — ② 에 걸려 출발점이 **1.3** → `1.3 − 1.3 = 0` 은 눈금 위 → `false`. **`a2s`**(스크립트 `1.3`, 속성 없음) — ④ 로 출발점 0 → `1.3` 은 0.5 의 정수배가 아니다 → `true`. `a6`(`time step=900 value="13:07"`)도 ② 다. **23편의 `a5`(`date`)가 속성으로도 켜진 것은 `min` 이 있어서**(①)다 — A2 의 `d2`(`min` 없음)는 `false`. 명세의 step mismatch 줄이 **경로를 묻지 않는다**는 것은 맞고, **Chrome 도 묻지 않았다**(A2 의 `n1`·`n3`·`n8`). ★ **그래서 23편의 「구현(Chrome) — 명세와 갈림」 줄은 「명세대로 — step base 가 `value` 속성」으로 옮겨야 한다.**

### 7. 앞뒤를 문자열 끝에 붙들기 · 감싼 뒤에야 유효해지는 패턴을 막기 — 실패하면 패턴 없음 + (UA 권장) 콘솔

- 명세의 두 이유 — ① 「정규식의 **시작을 문자열의 시작에, 끝을 끝에** 붙들기 위해」 ② 「`^(?:`·`)$` 로 **감싼 뒤에야 유효해지는** 것이 아니라 **혼자서도 유효**하도록」(그래서 감싸기 전에 한 번 `RegExpCreate(pattern, "v")` 를 돌려 본다).
- **실패하면** — 「컴파일된 패턴이 **없다**」 → `patternMismatch` 가 **언제나 거짓**(A3 의 `p4`). 명세 — 「UA 는 이 오류를 **개발자 콘솔에 남기기를 권한다**」 — 이 판은 **남겼다**(A3 의 콘솔 1 줄).

### 8. 「막아도 된다(may)」와 「사용자 편집이면 too long」 — 손대기 전에는 안 막힌다

- **막기** — 「UA 는 사용자가 API 값을 최대보다 길게 **만들지 못하게 해도 된다**」(A4 의 `m2` → `abc`). **깃발** — 「더러움 표시가 참이고, **값이 마지막으로 사용자 편집으로 바뀌었고**, 길이가 최대보다 크면 too long」(A4 의 `m1`).
- **서버가 채운 긴 값** — 스크립트·속성으로 들어온 값은 **사용자 편집이 아니므로** `tooLong` 이 거짓 → **제출이 안 막힌다**(A4 첫 판).

### 9. `range` 는 「해야 한다(must)」 · `number` 는 「해도 된다(may)」 — 이 판은 `number` 를 안 고쳤다 · 3 과 5 중 양의 무한대 쪽

- 명세 — Range 상태: 「step mismatch 를 겪으면 가장 가까운 허용 값으로 **반올림해야 한다**(범위 안에서) · 둘이면 **양의 무한대에 가까운 쪽**」 · Number 상태: 「**반올림해도 된다** · 둘이면 양의 무한대 쪽을 **권한다**」.
- **이 판** — `range` 는 고쳤고(A2 의 `r1`·`r2` `5`), `number` 는 **안 고쳤다**(A2 의 `n1` `"4"` + `true`).
- **`4` → `5`** — 출발점 1 · 눈금 2 → 허용 값 **3 과 5 가 똑같이 1 만큼** 떨어져 있다 → 양의 무한대 쪽 **5**.

### 10. 서버는 그 검증을 모른다(21편의 `novalidate`·`curl`) · 이 속성들은 조용히 무시되거나 스크립트 값을 안 센다(이 편)

- **[21번](../21-form-submission-model/2-summary.md)의 측정** — 검증 폼은 `invalid` 로 멈췄지만, **`novalidate` 폼과 `curl` 이 보낸 본문이 한 글자도 같았다**((5)). 서버 쪽에서는 브라우저가 검증했는지 **가를 칸이 없다.** `form.submit()` 은 **검증을 건너뛴다**((2)).
- **이 주제의 측정** — 타입과 안 맞는 속성은 **깃발 없이 무시된다**(A1) · `v` 에서 무효한 패턴은 **버려진다**(A3) · `maxlength` 는 **스크립트 값을 안 센다**(A4). **클라이언트 검증은 사용자 편의**이고 서버 검증을 대신하지 못한다.

### 11. 갈린 칸은 없다 · 23편의 줄은 「명세대로」로 · 막기와 콘솔은 구현(명세가 허용·권장) · 반올림 안 함도 구현(may)

- **이 주제에서 명세와 갈린 칸은 없다** — 적용 목록 0 / 42 · step base 가 네 타입 모두 명세대로.
- **23편의 「명세와 갈림」** — **명세 층**으로 옮긴다(step base 의 둘째 줄).
- **「초과 입력을 막는다」** — 명세가 **허용(may)** 한 것을 구현했다 · **「콘솔에 남긴다」** — 명세가 **권장**한 것을 구현했다 · **「`number` 를 반올림하지 않는다」** — 명세가 **허용**한 것을 **안 한** 구현. 셋 다 **구현** 층이다.

### 12. 정본 경계

- **검증이 언제 도나 · `curl` 우회** — [21번](../21-form-submission-model/2-summary.md)의 (2)·(5) · **`:user-invalid`** — [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md) · 목록의 **29번 주제** · **`setCustomValidity`** — web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **60번** · **`u`/`v`** — [JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md)의 (3)·(4).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800` · 격자·눈금 블록은 **`LANGUAGE=ko_KR`**(하네스의 `--lang=ko-KR`). **엔진은 이것 하나다.** 하네스는 [25번](../25-label-association/3-answer.md)의 `html25b-form.py`·`html25b-cdp.py` 그대로다.\
★ **쌍둥이** — 격자의 칸마다 **속성만 없는 짝**을 두고 같은 값·같은 편집을 준 뒤, `.value` 가 갈리면 「값을 고쳤다」로 센다(제5의 상태 — `range`).\
★ **사용자 편집** — 글자 칸은 `type`(`Input.insertText`) 또는 `End` + `Backspace`(`Input.dispatchKeyEvent`), 날짜는 `ArrowUp`, 체크박스는 `Space`, 슬라이더는 `ArrowRight`.\
★ **콘솔** — `Log.enable` 뒤 페이지 세션의 `Log.entryAdded` 글자를 모아 페이지에 넘겼다.

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌렸다(재대조는 25번 `## 실행 검증`). ★ **콘솔 기록 줄**은 이벤트가 **로드가 끝나기 전에** 오는 것에 기대지만, 세 판 모두 **1 줄**이었다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **속성 × 타입 격자 두 판** | 3 | 동작 방식 (1) · A1 |
| **step base 열일곱 칸** | 3 | 동작 방식 (2) · A2 |
| **`pattern` 열 개 · JS · 콘솔** | 3 | 동작 방식 (3) · A3 |
| **길이 제한 여섯 칸 두 판** | 3 | 동작 방식 (4) · A4 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `number` 의 step 반올림 | 안 한다 | 명세는 허용(may) |
| 사용자의 초과 입력 | 막는다 | 명세는 허용(may) |
| 무효한 `pattern` 의 콘솔 기록 | 남긴다(문구는 구현) | 명세는 권장 |

**안 돌려 본 것** — ① **IME 조합 중의 `maxlength`.** ② **`step="any"`.** ③ **`multiple` 인 `email` 의 `pattern`**(값마다 따로 본다 — 명세 문장만). ④ **`textarea` 의 `maxlength` 가 CRLF 가 아니라 LF 로 세는 것**(명세 문장 — [26번](../26-select-datalist-textarea/2-summary.md)이 `textLength` 로 LF 세기를 보였다).

**못 잰 것** — ① **검증 풍선.** ② **보조 기술의 무효 상태 알림.**

**부적용인 창** — **창 ① · ③ · ④ · ⑥**, **창 ⑤ 는 21번 인용** · **창 ⑦ 은 안 쟀다**(검증 속성이 트리에 남기는 상태).

## 용어 풀이

- **적용되지 않는다(do not apply)** — 상태별 「의미 없는 속성」 목록.
- **step base** — 눈금의 출발점. `min` → `value` 속성 → 기본 기준 → 0.
- **컴파일된 패턴** — `^(?:…)$` 를 `v` 로 만든 정규식. 못 만들면 없음.
- **사용자 편집** — 사용자가 직접 바꾼 값. `tooLong`·`tooShort` 의 조건.
