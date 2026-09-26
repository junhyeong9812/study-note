# html/syntax/29 — 제약 검증: 유효성 상태·`novalidate`·`:valid`/`:user-invalid` 의 관계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 아래 `## 실행 검증` 절에 전문이 있다(30\~32번이 같은 하네스를 쓴다).\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「Constraints」·「Form submission algorithm」·user validity·focus update steps 와 [Selectors Level 4 §12.3.4](https://drafts.csswg.org/selectors-4/#user-pseudos) 로 접지했다(앞 배치가 받아 둔 사본).\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 `matches()` 격자다** — 72 칸을 미리 선언하고 「로드와 갈린 칸」·「명세 열과 갈린 칸」을 스크립트가 센다(A1).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 갈린 칸 6 / 60 — 전부 `T4`·`T5` 의 `:user-*` · `change` 는 `r=0 e=1 ok=1` · 명세 열과 갈린 칸 1 / 72(`r :user-invalid` 의 `T4`)

**출력**

명세 열 파일 —

```javascript
// html29b-29-spec.js
// 명세 열 — HTML 의 user validity 가 참이 되는 자리 × Selectors 4 의 「:user-invalid 는 :invalid 인 것만 · :user-valid 는 :valid 인 것만」
// user validity 가 참이 되는 자리: ① 포커스를 떠날 때 값이 포커스 받을 때와 달라졌으면(focus update steps) ② 제출 시도(submit() 가 아닌 길)
// 거짓이 되는 자리: reset. 스크립트 대입과 포커스 중의 입력은 어느 쪽도 아니다.
const 명세유효 = { r: false, e: false, ok: true };
const 명세사용자 = (id, t) => t === "T5" || (t === "T4" && id !== "r");   // r 은 x 를 쳤다 지워 포커스 받을 때와 값이 같다
const 명세맞음 = (id, t, p) => {
  const v = 명세유효[id], u = 명세사용자(id, t);
  return { ":valid": v, ":invalid": !v, ":user-valid": u && v, ":user-invalid": u && !v }[p];
};
```

```text
$ python3 html29b-form.py 시도 html29b-29-grid.html | sed -n '/^칸 /,$p'
칸 · 의사 클래스              T1   T2   T3   T4   T5   T6
r :valid                      ·    ·    ·    ·    ·    ·
r :invalid                    예   예   예   예   예   예
r :user-valid                 ·    ·    ·    ·    ·    ·
r :user-invalid               ·    ·    ·    예   예   ·
e :valid                      ·    ·    ·    ·    ·    ·
e :invalid                    예   예   예   예   예   예
e :user-valid                 ·    ·    ·    ·    ·    ·
e :user-invalid               ·    ·    ·    예   예   ·
ok :valid                     예   예   예   예   예   예
ok :invalid                   ·    ·    ·    ·    ·    ·
ok :user-valid                ·    ·    ·    예   예   ·
ok :user-invalid              ·    ·    ·    ·    ·    ·

T1 = 로드 직후 · 값 r="" e="ab" ok="가" · change 이벤트 r=0 e=0 ok=0
T2 = 스크립트 대입 뒤 · 값 r="" e="cd" ok="나" · change 이벤트 r=0 e=0 ok=0
T3 = 진짜 키 입력 뒤(포커스 중) · 값 r="" e="abd" ok="가다" · change 이벤트 r=0 e=0 ok=0
T4 = 진짜 키 입력 → Tab · 값 r="" e="abd" ok="가다" · change 이벤트 r=0 e=1 ok=1
T5 = 제출 단추 클릭 뒤 · 값 r="" e="ab" ok="가" · change 이벤트 r=0 e=0 ok=0
T6 = 제출 단추 클릭 → reset() · 값 r="" e="ab" ok="가" · change 이벤트 r=0 e=0 ok=0
로드 직후(T1)와 갈린 칸 = 6 / 60
명세 열과 갈린 칸 = 1 / 72
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- **`:valid`/`:invalid`** — 여섯 시점 내내 같다. `r`·`e` 는 `:invalid`, `ok` 는 `:valid`. 깃발은 **값**이 정한다.
- ★★★ **`:user-*`** — `T4`(키 입력 → Tab)와 `T5`(제출 단추 클릭)에서만 켜졌다. `r`·`e` 는 `:user-invalid`, `ok` 는 `:user-valid`. `T2`(스크립트)·`T3`(포커스 중)·`T6`(제출 뒤 `reset()`)은 꺼져 있다.
- ★★★ **`change` 는 `r=0`** — `r` 은 `x` 를 쳤다 지워 값이 **처음 포커스 받을 때와 같다.** focus update steps 의 「(처음과 달라졌으면)」이 거짓이라 명세 문장대로면 **도장이 없다** — 그런데 Chrome 은 `:user-invalid` 를 켰다. 그 한 칸이 **1 / 72** 다(A7).

### 2. 서버가 무효한 값을 받은 시도 4 / 5 — 막힌 것은 검증 폼의 클릭 하나 · `novalidate`·`formnovalidate` 에서도 깃발은 `true`

**출력**

```text
$ python3 html29b-form.py 시도 html29b-29-submit.html | sed -n '1,/^$/p'
[가 · 보냄 클릭]
  페이지  깃발 addr.typeMismatch=true · age.rangeUnderflow=true · form:invalid=true → click(가보냄 · detail=1) → invalid(addr) → invalid(age)
  서버    (받은 요청 없음)
[가 · formnovalidate 단추 클릭]
  페이지  깃발 addr.typeMismatch=true · age.rangeUnderflow=true · form:invalid=true → click(가건넘 · detail=1) → submit(submitter=가건넘)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
[나(novalidate) · 보냄 클릭]
  페이지  깃발 addr.typeMismatch=true · age.rangeUnderflow=true · form:invalid=true → click(나보냄 · detail=1) → submit(submitter=나보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
[가 · 속성을 지운 뒤 보냄 클릭]
  페이지  깃발 addr.typeMismatch=false · age.rangeUnderflow=false · form:invalid=false → click(가보냄 · detail=1) → submit(submitter=가보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
[가 · fetch(URLSearchParams(FormData(가)))]
  페이지  깃발 addr.typeMismatch=true · age.rangeUnderflow=true · form:invalid=true → fetch 응답 200
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded;charset=UTF-8
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」

(exit 0)
```

```text
$ python3 html29b-form.py 시도 html29b-29-submit.html | sed -n '/^시도 /,$p'
시도                                      submit  invalid  서버 요청 서버가 받은 addr · age
가 · 보냄 클릭                            —      2번      0번       (없음)
가 · formnovalidate 단추 클릭             났다    0번      1번       addr=「아무 글자」 · age=「-5」
나(novalidate) · 보냄 클릭                났다    0번      1번       addr=「아무 글자」 · age=「-5」
가 · 속성을 지운 뒤 보냄 클릭             났다    0번      1번       addr=「아무 글자」 · age=「-5」
가 · fetch(URLSearchParams(FormData(가))) —      0번      1번       addr=「아무 글자」 · age=「-5」
서버가 무효한 값을 받은 시도 = 4 / 5
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- **`가 · 보냄 클릭`** — `invalid(addr) → invalid(age)` · 서버 **0**.
- ★★★ **나머지 넷** — 서버 **1 번씩**, 받은 값이 **전부 `addr=「아무 글자」 · age=「-5」`**. 본문 줄도 한 글자도 같다(`fetch` 는 `Content-Type` 에 `;charset=UTF-8` 만 더 붙었다).
- ★★★ **깃발** — `formnovalidate`·`novalidate`·`fetch` 셋은 제출 직전이 **`typeMismatch=true · rangeUnderflow=true · form:invalid=true`**, **속성을 지운 판만 셋 다 `false`**.

### 3. 둘 다 `invalid` 둘 · `false` — `reportValidity` 만 포커스를 옮기고 둘 다 도장은 없다 · `novalidate` 제출 시도는 도장 · `setCustomValidity` 는 `''` 로만 풀린다

**출력**

```text
$ python3 html29b-form.py 시도 html29b-29-api.html | sed -n '/^다.checkValidity/,$p'
다.checkValidity()
  페이지  invalid(c2) → invalid(c3) → 반환 false → user-invalid=(없음) · 포커스=BODY
  서버    (받은 요청 없음)
다.reportValidity()
  페이지  invalid(c2) → invalid(c3) → 반환 false → user-invalid=(없음) · 포커스=c2
  서버    (받은 요청 없음)
라(novalidate · submit 을 막음) · 보냄 클릭
  페이지  click(라보냄 · detail=1) → submit(submitter=라보냄) → user-invalid=d1 · 포커스=라보냄
  서버    (받은 요청 없음)
c2 에 포커스만 주고 Tab
  페이지  user-invalid=(없음) · 포커스=c3
  서버    (받은 요청 없음)
c2·c3 을 채우고 c1.setCustomValidity('이유') · 보냄
  페이지  c1.customError=true · c1:invalid=true → click(다보냄 · detail=1) → invalid(c1)
  서버    (받은 요청 없음)
같은 뒤 c1 을 진짜 키로 고치고 보냄
  페이지  c1.value=다가 · c1.customError=true → click(다보냄 · detail=1) → invalid(c1)
  서버    (받은 요청 없음)
같은 뒤 setCustomValidity('') · 보냄
  페이지  c1.customError=false → click(다보냄 · detail=1) → submit(submitter=다보냄)
  서버    POST /r · 필드  c1=「가」 · c2=「나」 · c3=「a@b.c」
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- **`checkValidity()`** — `invalid(c2) → invalid(c3)` · `false` · `:user-invalid` 없음 · 포커스 `BODY`.
- **`reportValidity()`** — 같은 둘 · `false` · `:user-invalid` **없음** · 포커스 **`c2`**.
- ★★★ **`novalidate` 폼 제출 시도** — `submit` 이 났고(막았으니 이동 없음) **`d1` 이 `:user-invalid`**.
- **포커스만 → Tab** — 도장 없음(값을 안 바꿨다) · 포커스는 `c3`.
- ★★★ **`setCustomValidity('이유')`** — `customError=true` · `invalid(c1)` 로 막힘 · **진짜 키로 `다가` 로 고쳐도 `true`** · **`''` 를 부른 뒤에야** `POST /r` 로 `c1=「가」 · c2=「나」 · c3=「a@b.c」` 가 갔다.

### 4. `:invalid` 는 유효성 상태(값) · `:user-invalid` 는 거기에 user validity(사용자)를 하나 더

- `:valid`/`:invalid` 는 **제약을 만족하나**만 읽는다 — 값이 정하므로 **로드 직후·스크립트 대입 뒤에도** 맞는다(A1 의 `T1`·`T2`).
- `:user-invalid` 는 Selectors 4 가 「**`:invalid` 인 것만**」으로 묶고, 거기에 HTML 의 **user validity** 가 참이어야 한다(A1 의 `T4`·`T5` 에서만 켜졌다). 도장이 「손님이 써 보고 돌아섰다」다.

### 5. 끄는 것은 「no-validate 가 거짓이면 대화형으로 검증한다」 한 단계 — 깃발은 값이 정하므로 그대로

- 명세의 제출 알고리즘 — 「**제출자 요소의 no-validate 상태**가 거짓이면 **대화형으로 검증**하고 결과가 부정이면 돌아간다」. `novalidate`(폼)·`formnovalidate`(단추)는 이 **조건 하나**를 참으로 만든다.
- 유효성 상태는 **값과 속성**이 정하고 제출 알고리즘과 무관하다 — 그래서 A2 의 두 시도가 `typeMismatch=true` 를 그대로 들고 보냈다. **`form:invalid=true` 인 채로 제출이 갔다.**

### 6. 참 — focus update steps(값이 달라졌으면) · 제출 시도(`submit()` 제외) / 거짓 — `reset` · 도장이 검증보다 앞이다

- **참으로** — ① **focus update steps**: 포커스를 잃는 칸이 「포커스 중에 사용자가 값을 바꿨고 **처음 포커스 받을 때와 달라졌으면**」 user validity 를 참으로 두고 `change` 를 쏜다. ② **제출 알고리즘**: 「`submit()` 에서 온 것이 아니면 … **폼이 소유한 제출 가능 요소마다** user validity 를 참으로」. (그 밖에 `select` 의 선택 변경 알림에도 같은 문장이 있다 — 이 판은 안 던졌다.)
- **거짓으로** — `input` 의 **초기화(reset) 알고리즘**: 「user validity · 더러움 표시 · 체크 더러움 표시를 **거짓으로** 되돌린다」(A1 의 `T6`).
- ★★★ **순서** — ② 의 도장 찍기가 **no-validate 검사보다 먼저** 적혀 있다. 그래서 **`novalidate` 폼도 제출 시도만으로 손대지 않은 칸에 `:user-invalid` 가 켜진다**(A3 의 `d1`). 검증이 멈추는 판에서는 **멈춘 화면에 빨간 줄**이 선다(Selectors 4 의 「제출 시도 뒤에는 **반드시** 맞아야 한다」).

### 7. 문장대로면 안 찍힌다 · 이 판은 찍었다(`change` 0 번) — HTML 의 의사 클래스 정의 절을 못 읽어서 이탈로 세지 않았다

- focus update steps 의 조건은 「**처음 포커스 받을 때와 달라졌으면**」이다. `x` → Backspace 로 `""` 에 돌아왔으니 **거짓** → 도장 없음 · `change` 없음. 이 판은 **`change` 는 0 번**(명세대로)인데 **`:user-invalid` 는 켜졌다**(A1).
- ★★ **이탈로 세지 않은 이유** — Selectors 4 가 「그 밖의 시점에도 **맞아도 된다(may)**」·「**호스트 언어가 더 정확한 규칙을 정해도 된다**」고 넘기고, HTML 은 그 규칙을 **「Pseudo-classes」 절**에 둔다. **이 배치의 사본에 그 절이 없다.** 그래서 적을 수 있는 것은 「**Chrome 의 도장은 `change` 에 묶여 있지 않다**」까지다.

### 8. 같다 — `invalid` 를 무효 칸마다 · `false` / 갈린다 — `reportValidity` 만 포커스 · 둘 다 `:user-invalid` 를 켜지 않는다

- A3 — 둘 다 **`invalid(c2) → invalid(c3)`**, 반환 **`false`**. `reportValidity()` 만 포커스를 **`c2`** 로 옮겼다. 명세 — `reportValidity` 는 「문제를 사용자에게 **알리고** … 포커스를 옮겨도 된다(may)」.
- ★★★ **둘 다 `user-invalid=(없음)`** — 도장을 찍는 문장(A6)에 이 호출들이 없다. 「스크립트로 검증 결과를 보여 줘도 **CSS 의 빨간 줄은 따로**」.

### 9. `formnovalidate` · `novalidate` · 속성 지우기 · `fetch` + `curl` — 가를 칸이 없다 · 「서버는 클라이언트 쪽 검증에 기대면 안 된다」

- A2 의 넷이 **같은 본문**을 보냈고, [21번](../21-form-submission-model/2-summary.md)의 (5) 가 `curl` 로 **같은 본문**을 보냈다. 서버가 보는 것은 메서드·경로·본문뿐이다 — `fetch` 의 `charset` 꼬리표 말고는 **다섯이 같다.**
- 명세의 「Security」 — 「**서버는 클라이언트 쪽 검증에 기대면 안 된다.** 적대적인 사용자가 일부러 건너뛸 수 있고, 오래된 UA 나 자동화 도구가 의도치 않게 건너뛴다. 제약 검증 기능은 **사용자 경험**을 높이려는 것이지 **어떤 보안 장치도 아니다**」.

### 10. 포커스 이동 — 구현(명세는 may) · `novalidate` 제출의 도장 — 명세대로 · 원래대로 돌아온 편집의 도장 — 이 판의 관찰(명세층 미확인)

- **`reportValidity()` 의 포커스** — 명세가 **허용(may)** 한 것을 Chrome 이 **했다** → 구현.
- **`novalidate` 폼의 제출 시도가 `:user-invalid` 를 켠다** — 제출 알고리즘의 **순서** 그대로다 → 명세(HTML) + Selectors 4.
- **값이 원래대로 돌아온 편집에 도장** — focus update steps 문장과는 맞지 않지만, 판정할 절을 못 읽었다 → **이 판의 관찰**(A7).

### 11. 정본 경계

- **속성이 어느 깃발을 켜나** — [28번](../28-validation-attributes/2-summary.md).
- **검증이 언제 도나**(`submit()` 은 건너뛴다) · **`curl`** — [21번](../21-form-submission-model/2-summary.md)의 (2)·(5).
- **`:user-invalid` 의 CSS 쪽**(명시도 · 다른 상태 의사 클래스) — [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md).
- **`setCustomValidity`·`checkValidity`·`reportValidity` 자체** — web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **60번**.
- **`fetch` 로 만드는 본문** — [web-api 30번](../../../../web-api/30-request-body-and-content-type/2-summary.md).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800` · `--force-renderer-accessibility`. **엔진은 이것 하나다.**\
★ **하네스** — [25번](../25-label-association/3-answer.md)의 `html25b-form.py`·`html25b-cdp.py`·`html25b-rec.js` 를 복사해 `html29b-` 로 이름을 바꾸고 넷을 더했다 —
① **`files` 단계**(CDP `DOM.setFileInputFiles` — 31번) ·
② **`drop` 단계**(CDP `Input.dispatchDragEvent` 의 `dragEnter`·`dragOver`·`drop` — 파일을 끌어다 놓는 사용자 길을 흉내 낸다) ·
③ **`chooser` 단계**(`Page.setInterceptFileChooserDialog` 로 파일 고르기 창을 가로챈 채 **진짜 마우스로 누르고**, 열린 창 `Page.fileChooserOpened` 에 파일을 넣는다 — 창의 `mode` 를 페이지 기록에 남긴다) ·
④ **표 종류 「종합」에 서버 로그 줄과 요청 목록을 넘긴다**(페이지가 격자를 짤 때 `filename`·경로를 읽는다) · multipart 의 파일 부분이 UTF-8 이 아니면 「(바이트 N개)」로 적는다.\
★ **제출 감지는 21번과 같다** — 동작 뒤 `details` 의 `toggle` 작업을 하나 더 넣고 그것이 돌 때 `beforeunload` 가 났나를 본다. 거짓 「안 갔다」는 **「뒤늦게 온 요청 = N」** 줄이 센다 — 이 배치의 모든 시도 블록이 **0** 이다.\
★ **올리는 파일** — 하네스 옆 `files/` 에 셋을 두었다(`p1.png` 는 1×1 PNG, 나머지 둘은 글자 네 바이트).

```text
$ stat -c '%s %n' files/p1.png files/t1.txt files/t2.png
67 files/p1.png
4 files/t1.txt
4 files/t2.png
(exit 0)
```

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌려(`capture.sh blocks` · `blocks-r1` · `blocks-r2`) `normalize-shaky.py` 로 첫 판과 견줬다 — 결과는 이 절 끝의 「재대조」 줄이다. 29\~32번의 블록이 전부 그 안에 있다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **의사 클래스 격자 72 칸** | 3 | 동작 방식 (1) · A1 |
| **검증을 건너는 다섯 시도** | 3 | 동작 방식 (2) · A2 |
| **스크립트 API 일곱 시도** | 3 | 동작 방식 (3) · A3 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `reportValidity()` 의 포커스 | 첫 무효 칸으로 옮긴다 | 명세는 허용(may) |
| 원래대로 돌아온 편집의 도장 | 찍는다(`change` 0 번) | HTML 의 의사 클래스 절을 확인하지 못했다 |

**안 돌려 본 것** — ① **`select`·`textarea` 의 도장**(명세 문장만). ② **`form.submit()` 이 도장을 안 찍는 것**(명세 문장만 — `submit()` 은 페이지를 떠나 확인할 판이 없었다). ③ **라디오 그룹의 `:user-invalid`**.

**못 잰 것** — ① **검증 풍선.** ② **보조 기술의 알림.**

**부적용인 창** — **창 ① · ③ · ④ · ⑥** · **창 ⑦ 은 안 쟀다.**

**재대조** — `capture.sh blocks-r1`·`blocks-r2` 를 첫 판(`blocks`)과 `normalize-shaky.py` 로 견준 결과가 **두 번 다 「블록 43개 · 동일 43 · 흔들린 칸 0 · ★고칠 것 0 · 한쪽에만 0」** 이다 — 정규화 규칙은 기본 넷만 썼다(`--rule` 없음 — 경계·포트는 하네스가 애초에 안 찍는다).

**하네스 전문** — 30\~32번이 같은 파일을 쓴다.

```python
# html29b-form.py
#!/usr/bin/env python3
"""29~32 폼 — 창 ⑤(서버 요청 로그)·창 ⑦(접근성 트리)·창 ②(노드 프로브)를 한 실행기로 묻는다(25편 하네스를 이었다).

사용: html29b-form.py [--lang=xx-YY] 시도 <페이지> | page <페이지> | ax <페이지> | dom <페이지> | curl
     html29b-form.py 로케일 <페이지> <로케일1> <로케일2>
  · 서버 하나(A)를 이 프로세스 안에 띄운다. 포트는 0 — 운영체제가 고른다(출력에는 서버 이름 A 만 적는다).
  · 서버 로그는 「서버 · 메서드 · 경로 · Content-Type · 질의 · 본문 · 필드」만 적는다. 시각·포트는 안 적는다.
    ★ multipart 의 경계(boundary) 문자열은 실행마다 바뀐다 — 싣지 않고 경계로 본문을 갈라 **필드 목록만** 적는다.
    ★ 필드 값은 디코딩해서 「」 안에 적는다. 퍼센트 인코딩된 원문은 「본문」·「질의」 줄에 그대로 둔다.
  · 시도 — 페이지의 window.__시도 = [{이름, 단계: [...]}, ...] 를 하나씩 돈다.
    시도마다 페이지를 새로 열고 → sessionStorage 를 비우고 → 단계를 실행한 뒤
    (시도에 「뒤」 식이 있고 이동이 없었으면 그 식을 평가해 「뒤」 줄로 찍는다)
    ★ 「제출이 일어났나」는 울타리로 가른다(시간 상수 없음) — 폼 제출의 이동은 DOM 조작 작업 원천의 작업으로
      미뤄지므로, 같은 작업 원천에 details 의 toggle 작업을 하나 더 넣고 그것이 돌 때 beforeunload 가 이미 났나를 본다.
      일어났으면 새 문서의 loadEventFired 를 기다린다. 거짓 「안 갔다」는 「뒤늦게 온 요청 = N」 줄이 센다.
    페이지 쪽 기록(click·submit·invalid)은 html29b-rec.js 가 sessionStorage 에 적어 둔다 —
    같은 출처로 이동해도 같은 탭이면 남는다.
  단계 꼴:
    ["js", 식]                     페이지 안에서 평가한다
    ["click", 선택자]              그 요소 한가운데를 진짜 마우스로 누른다
    ["clickat", 선택자, dx, dy]    그 요소 왼쪽 위에서 (dx, dy) 떨어진 점을 누른다
    ["enter", 선택자]              그 요소에 포커스를 두고 진짜 Enter 를 누른다
    ["type", 선택자, 글자]         그 요소에 포커스를 두고 글자를 입력한다(Input.insertText)
    ["key", 선택자, key, code, 가상키코드[, 글자]]  그 요소에 포커스를 두고 키를 누르고 뗀다(글자를 주면 keyDown 에 싣는다)
    ["keyhere", key, code, 가상키코드[, 글자]]      포커스를 옮기지 않고 지금 포커스에 키를 누르고 뗀다
    ["files", 선택자, [파일…]]     그 파일 칸에 CDP DOM.setFileInputFiles 로 파일을 넣는다(파일은 이 디렉토리의 files/ 아래)
    ["drop", 선택자, [파일…]]      그 요소 한가운데에 파일을 끌어다 놓는다(Input.dispatchDragEvent — dragEnter·dragOver·drop)
    ["chooser", 선택자, [파일…]]   파일 고르기 창을 가로채 둔 채 그 요소를 진짜 마우스로 누르고, 열린 창(Page.fileChooserOpened)에
                                   파일을 넣는다 — 창의 mode 를 페이지 기록에 「chooser(mode)」로 적는다
  · multipart 의 파일 부분은 내용을 UTF-8 로 읽을 수 있으면 「」 안에, 못 읽으면 「(바이트 N개)」로 적는다.
  · 표 종류 「종합」 — 시도를 다 돈 뒤 페이지를 새로 열고 window.__종합(결과) 가 돌려준 글자를 찍는다.
    결과 = [{이름, 기록, 뒤, 필드: [서버가 받은 필드 이름…] | null, 요청: [{메서드, 경로, 형식}…], 서버: [로그 줄…]}]
    — 표 짜기·칸 세기는 페이지가 한다.
    window.__뒤숨김 = true 면 시도마다의 「뒤」 줄은 찍지 않는다(종합표가 그 값을 쓴다).
  · page 모드(와 「종합」) — window.__대상 = [[열쇠, 선택자], …] 면 접근성 노드를 window.__AX 로,
    window.__내부 = true 면 내부 덤프(htmlId 열쇠)를 window.__INT 로,
    window.__콘솔 = true 면 그때까지 받은 콘솔 기록(Log.entryAdded 의 글자)을 window.__LOG 로 넣어 준다.
  · --lang=xx-YY — Chrome 을 그 로케일로 띄운다(23편 — 환경 변수 LANGUAGE). 이때 로그에 Accept-Language 를 함께 적는다.
"""
import http.server, importlib.util, json, os, shutil, subprocess, sys, threading, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp", os.path.join(HERE, "html29b-cdp.py"))
cdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdp)

LOG = []
INFO = []          # 요청마다 격자용 요약 — (메서드, 질의 있나, 본문 종류, Content-Type)
LOCK = threading.Lock()
LANG = None
RESULT = '<!DOCTYPE html><meta charset="utf-8"><link rel="icon" href="data:,"><title>받음</title><p>받음</p>'.encode()


def 값(s):
    return "「" + s.replace("\r", "\\r").replace("\n", "\\n") + "」"


def 필드_urlencoded(raw):
    return [(k, v) for k, v in urllib.parse.parse_qsl(raw, keep_blank_values=True)]


def 적기(label, method, path, headers, body):
    out = []
    ct = headers.get("Content-Type")
    u = urllib.parse.urlsplit(path)
    head = f"{label} {method} {u.path}"
    if ct:
        if ct.startswith("multipart/form-data"):
            head += "  Content-Type=multipart/form-data; boundary=(경계)"
        else:
            head += f"  Content-Type={ct}"
    out.append(head)
    if LANG:
        out.append(f"  Accept-Language  {headers.get('Accept-Language', '(없음)')}")
    out.append(f"  질의  {u.query if u.query else '(없음)'}")
    fields = 필드_urlencoded(u.query) if u.query else []
    if method == "POST":
        if ct and ct.startswith("multipart/form-data"):
            b = ct.split("boundary=", 1)[1].encode()
            parts = body.split(b"--" + b)[1:-1]
            out.append(f"  본문  (multipart — 부분 {len(parts)}개 · 경계로 갈라 필드만 적는다)")
            fields = []
            for p in parts:
                h, _, v = p[2:].partition(b"\r\n\r\n")
                v = v[:-2] if v.endswith(b"\r\n") else v
                hs = h.decode().split("\r\n")
                disp = next(x for x in hs if x.lower().startswith("content-disposition"))
                name = disp.split('name="', 1)[1].split('"', 1)[0]
                extra = []
                if 'filename="' in disp:
                    extra.append("filename=" + 값(disp.split('filename="', 1)[1].split('"', 1)[0]))
                for x in hs:
                    if x.lower().startswith("content-type"):
                        extra.append("부분 " + x)
                try:
                    shown = v.decode()
                except UnicodeDecodeError:
                    shown = f"(바이트 {len(v)}개)"
                fields.append((name, shown + ("" if not extra else "\0" + " · ".join(extra))))
        else:
            text = body.decode()
            out.append(f"  본문  {값(text) if text else '(빈 본문)'}")
            if ct == "text/plain":
                fields = [tuple(line.split("=", 1)) for line in text.split("\r\n") if line]
            else:
                fields = 필드_urlencoded(text)
    else:
        out.append("  본문  (없음)")
    shown = []
    for k, v in fields:
        v, _, extra = v.partition("\0")
        shown.append(f"{k}={값(v)}" + (f" ({extra})" if extra else ""))
    out.append("  필드  " + (" · ".join(shown) if shown else "(없음)"))
    kind = "없음" if method != "POST" else ("multipart" if ct and ct.startswith("multipart")
                                             else "글자 그대로" if ct == "text/plain" else "퍼센트 인코딩")
    info = (method, "있음" if u.query else "없음", kind,
            "multipart/form-data" if ct and ct.startswith("multipart") else (ct or "(없음)"),
            [k for k, _ in fields], u.path)
    return out, info


def server(label):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=HERE, **k)

        def 기록(self, method, body=b""):
            if not self.path.endswith(".js"):
                lines, info = 적기(label, method, self.path, self.headers, body)
                with LOCK:
                    LOG.extend(lines)
                    INFO.append(info)

        def 받음(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(RESULT)))
            self.end_headers()
            self.wfile.write(RESULT)

        def do_GET(self):
            self.기록("GET")
            if self.path.startswith("/r"):
                return self.받음()
            return super().do_GET()

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            self.기록("POST", self.rfile.read(n))
            return self.받음()

        def log_message(self, *a):
            pass

    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def take_log():
    with LOCK:
        out = LOG[:]
        LOG.clear()
        INFO.clear()
    return out


def take_info():
    with LOCK:
        return INFO[:]


def center(c, sid, sel, off=None):
    at = "[r.x + r.width / 2, r.y + r.height / 2]" if off is None else \
         "[r.x + %s, r.y + %s]" % (json.dumps(off[0]), json.dumps(off[1]))
    xy = cdp.evaluate(c, sid, "(() => { const r = document.querySelector(" + json.dumps(sel)
                      + ").getBoundingClientRect(); return " + at + "; })()")
    if not isinstance(xy, list):
        raise RuntimeError("좌표를 못 얻었다: " + sel + " " + str(xy))
    return xy


def focus(c, sid, sel):
    r = cdp.evaluate(c, sid, "(() => { const e = document.querySelector(" + json.dumps(sel)
                     + "); e.focus(); return document.activeElement === e; })()")
    if r is not True:
        raise RuntimeError("포커스를 못 줬다: " + sel)


def 단계(c, sid, st):
    kind = st[0]
    if kind == "js":
        v = cdp.evaluate(c, sid, st[1])
        if isinstance(v, str) and v.startswith("«예외"):
            raise RuntimeError(st[1] + " -> " + v)
    elif kind in ("click", "clickat"):
        x, y = center(c, sid, st[1], st[2:4] if kind == "clickat" else None)
        c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y}, sid)
        for t in ("mousePressed", "mouseReleased"):
            c.send("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left",
                   "clickCount": 1, "buttons": 1 if t == "mousePressed" else 0}, sid)
    elif kind == "enter":
        focus(c, sid, st[1])
        for t in ("keyDown", "keyUp"):
            prm = {"type": t, "key": "Enter", "code": "Enter",
                   "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13}
            if t == "keyDown":
                prm["text"] = "\r"
            c.send("Input.dispatchKeyEvent", prm, sid)
    elif kind in ("key", "keyhere"):
        if kind == "key":
            focus(c, sid, st[1])
            st = st[1:]
        key, code, vk = st[1:4]
        text = st[4] if len(st) > 4 else None
        for t in ("keyDown", "keyUp"):
            prm = {"type": t, "key": key, "code": code,
                   "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
            if text and t == "keyDown":
                prm["text"] = text
            c.send("Input.dispatchKeyEvent", prm, sid)
    elif kind in ("files", "drop", "chooser"):
        paths = [os.path.join(HERE, "files", f) for f in st[2]]
        if kind == "files":
            root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
            nid = c.send("DOM.querySelector", {"nodeId": root, "selector": st[1]}, sid)["nodeId"]
            c.send("DOM.setFileInputFiles", {"files": paths, "nodeId": nid}, sid)
        elif kind == "drop":
            x, y = center(c, sid, st[1])
            data = {"items": [], "files": paths, "dragOperationsMask": 1}
            for t in ("dragEnter", "dragOver", "drop"):
                c.send("Input.dispatchDragEvent", {"type": t, "x": x, "y": y, "data": data}, sid)
        else:
            c.send("Page.setInterceptFileChooserDialog", {"enabled": True}, sid)
            x, y = center(c, sid, st[1])
            c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y}, sid)
            for t in ("mousePressed", "mouseReleased"):
                c.send("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left",
                       "clickCount": 1, "buttons": 1 if t == "mousePressed" else 0}, sid)
            ev = c.wait("Page.fileChooserOpened", sid)
            cdp.evaluate(c, sid, "(() => { const a = JSON.parse(sessionStorage.getItem('기록') || '[]'); a.push("
                         + json.dumps("chooser(" + ev.get("mode", "?") + ")") + "); sessionStorage.setItem('기록', JSON.stringify(a)); 1 })()")
            c.send("DOM.setFileInputFiles", {"files": paths, "backendNodeId": ev["backendNodeId"]}, sid)
            c.send("Page.setInterceptFileChooserDialog", {"enabled": False}, sid)
    elif kind == "type":
        focus(c, sid, st[1])
        c.send("Input.insertText", {"text": st[2]}, sid)
    else:
        raise RuntimeError("모르는 단계: " + kind)


FENCE = """new Promise(r => { const d = document.createElement('details');
  d.addEventListener('toggle', () => r(sessionStorage.getItem('떠남') || '안 떠남'), { once: true });
  document.body.append(d); d.open = true; })"""


def 울타리(c, sid):
    """제출이 계획됐나 — 폼 제출의 이동은 DOM 조작 작업 원천의 작업으로 뒤로 미뤄진다.
    같은 작업 원천에 details 의 toggle 작업을 하나 더 넣고, 그것이 돌 때 beforeunload 가 이미 났나를 본다."""
    r = c.send("Runtime.evaluate", {"expression": FENCE, "awaitPromise": True, "returnByValue": True}, sid)
    v = r.get("result", {}).get("value")
    return v == "1" or "exceptionDetails" in r


def goto(c, sid, url):
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)


def 너비(s):
    return sum(2 if ord(ch) > 0x1100 else 1 for ch in s)


def 칸(s, w):
    return s + " " * max(w - 너비(s), 1)


def 시도(c, sid, base, page):
    goto(c, sid, base + page)
    trials = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__시도)"))
    kind = cdp.evaluate(c, sid, "window.__표 || ''")
    names = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__칸목록 || [])"))
    hide = cdp.evaluate(c, sid, "window.__뒤숨김 === true")   # 「뒤」 값을 종합표만 쓰면 시도 줄에는 안 찍는다
    rows = []
    late = 0
    for t in trials:
        goto(c, sid, base + page)
        cdp.evaluate(c, sid, "sessionStorage.clear(); 1")
        # ★ 앞 시도가 「안 갔다」로 적혔는데 요청이 뒤늦게 왔다면 여기서 잡힌다(이 페이지를 연 요청은 뺀다)
        late += sum(1 for i in take_info() if not (i[0] == "GET" and i[5] == "/" + page and i[1] == "없음"))
        take_log()
        for st in t["단계"]:
            단계(c, sid, st)
        went = 울타리(c, sid)
        if went:
            c.wait("Page.loadEventFired", sid)
        rec = json.loads(cdp.evaluate(c, sid, "sessionStorage.getItem('기록') || '[]'"))
        after = cdp.evaluate(c, sid, t["뒤"]) if t.get("뒤") and not went else None
        info = take_info()
        log = take_log()
        print(f"[{t['이름']}]")
        print("  페이지  " + (" → ".join(rec) if rec else "(기록 없음)"))
        if after is not None and not hide:
            print("  뒤      " + str(after))
        for line in log:
            print(("  서버    " if line.startswith("A ") else "        ") + line)
        if not log:
            print("  서버    (받은 요청 없음)")
        rows.append((t["이름"], "났다" if any(r.startswith("submit") for r in rec) else "—",
                     "났다" if any(r.startswith("invalid") for r in rec) else "—",
                     str(len(info)) + "번", info, rec, after, log))
    if kind == "제출":
        print()
        print(칸("시도", 40) + 칸("submit", 8) + 칸("invalid", 9) + "서버가 받은 요청  「" + rows[0][0] + "」과 갈린 칸")
        hit = total = 0
        for r in rows:
            d = sum(1 for i in (1, 2, 3) if r[i] != rows[0][i])
            if r is not rows[0]:
                hit += d
                total += 3
            print(칸(r[0], 40) + 칸(r[1], 8) + 칸(r[2], 9) + 칸(r[3], 18) + ("(기준)" if r is rows[0] else f"{d} / 3"))
        print(f"서버가 받은 시도 = {sum(1 for r in rows if r[4])} / {len(rows)}")
        print(f"갈린 칸 = {hit} / {total}")
    elif kind == "싣기":
        print()
        print(칸("시도", 30) + 칸("메서드", 8) + 칸("질의", 6) + 칸("본문", 14) + 칸("Content-Type", 36) + "「" + rows[0][0] + "」과 갈린 칸")
        base_i = rows[0][4][0]
        hit = total = 0
        for r in rows:
            m, q, b, ct = r[4][0][:4]
            d = sum(1 for x, y in zip((m, q, b, ct), base_i[:4]) if x != y)
            if r is not rows[0]:
                hit += d
                total += 4
            print(칸(r[0], 30) + 칸(m, 8) + 칸(q, 6) + 칸(b, 14) + 칸(ct, 36) + ("(기준)" if r is rows[0] else f"{d} / 4"))
        print(f"본문에 실린 시도 = {sum(1 for r in rows if r[4][0][2] != '없음')} / {len(rows)}")
        print(f"갈린 칸 = {hit} / {total}")
    elif kind == "실린":
        print()
        print((칸("칸", 34) + "".join(칸(f"({k + 1})", 6) for k in range(len(rows)))).rstrip())
        for label, field in names:
            print((칸(label, 34) + "".join(칸("실림" if r[4] and field in r[4][0][4] else "—", 6) for r in rows)).rstrip())
        for k, r in enumerate(rows):
            n = sum(1 for _, field in names if r[4] and field in r[4][0][4])
            print(f"({k + 1}) {r[0]} — 실린 칸 = {n} / {len(names)}")
    elif kind == "종합":
        print()
        goto(c, sid, base + page)
        넣기(c, sid)
        res = [{"이름": r[0], "기록": r[5], "뒤": r[6], "필드": (r[4][0][4] if r[4] else None),
                "요청": [{"메서드": i[0], "경로": i[5], "형식": i[3]} for i in r[4]], "서버": r[7]} for r in rows]
        print(cdp.evaluate(c, sid, "window.__종합(" + json.dumps(res, ensure_ascii=False) + ")"))
    goto(c, sid, base + page)
    late += sum(1 for i in take_info() if not (i[0] == "GET" and i[5] == "/" + page and i[1] == "없음"))
    take_log()
    print(f"뒤늦게 온 요청 = {late}")
    return rows


def 넣기(c, sid):
    """page·종합 공용 — 페이지가 선언한 것(__대상·__내부·__콘솔)을 묻고 결과를 페이지에 넣는다."""
    targets = cdp.evaluate(c, sid, "JSON.stringify(window.__대상 || [])")
    ax = {k: cdp.ax_of(c, sid, sel) for k, sel in json.loads(targets)}
    cdp.evaluate(c, sid, "window.__AX = " + json.dumps(ax, ensure_ascii=False))
    if cdp.evaluate(c, sid, "window.__내부 === true"):
        by = {}
        for n in cdp.internal(c, sid):      # 같은 htmlId 가 둘이면 무시되지 않은 노드를 고른다
            hid = n["속성"].get("htmlId")
            if hid and (hid not in by or "ignored" in by[hid]["속성"]):
                by[hid] = n
        cdp.evaluate(c, sid, "window.__INT = " + json.dumps(by, ensure_ascii=False))
    if cdp.evaluate(c, sid, "window.__콘솔 === true"):
        cdp.evaluate(c, sid, "1")           # 앞서 온 이벤트를 다 받아 둔다
        logs = [e["params"]["entry"]["text"] for e in c.events
                if e.get("method") == "Log.entryAdded" and e.get("sessionId") == sid]
        cdp.evaluate(c, sid, "window.__LOG = " + json.dumps(logs, ensure_ascii=False))


def 화면글자(c, sid, sel):
    """창 ⑦ — 그 입력 칸 아래 StaticText 를 트리 순서로 이어 붙인다(선택도구 단추는 뺀다). 화면에 그려진 글자다."""
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    nid = c.send("DOM.querySelector", {"nodeId": root, "selector": sel}, sid)["nodeId"]
    be = cdp.backend(c, sid, nid)
    nodes = c.send("Accessibility.getFullAXTree", {}, sid)["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    top = next(n for n in nodes if n.get("backendDOMNodeId") == be)
    out = []

    def walk(n):
        role = cdp.val(n, "role")
        if role == "button":
            return
        if role == "StaticText":
            out.append(cdp.val(n, "name"))
        for ch in n.get("childIds", []):
            if ch in by:
                walk(by[ch])
    walk(top)
    return "".join(out)


def 로케일(page, langs):
    """같은 페이지를 로케일마다 새 브라우저로 열어 — 준비 단계(입력) → 화면 글자 → 제출 → 서버 필드."""
    global LANG
    got = {}
    for lang in langs:
        LANG = lang
        env = {**os.environ, "LANGUAGE": lang.replace("-", "_")}
        a = server("A")
        base = f"http://127.0.0.1:{a.server_address[1]}/"
        proc, c = cdp.start((), env)
        try:
            tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
            sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
            for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable", "Log.enable"):
                c.send(m, sid=sid)
            goto(c, sid, base + page)
            nav = cdp.evaluate(c, sid, "navigator.language")
            for st in json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__준비 || [])")):
                단계(c, sid, st)
            ids = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__칸)"))
            screen = {i: 화면글자(c, sid, "#" + i) for i in ids}
            take_log()
            단계(c, sid, ["click", cdp.evaluate(c, sid, "window.__보냄")])
            if 울타리(c, sid):
                c.wait("Page.loadEventFired", sid)
            info = take_info()
            log = take_log()
        finally:
            proc.terminate()
            proc.wait()
            shutil.rmtree(cdp.PROF, ignore_errors=True)
            a.shutdown()
        body = next(l for l in log if l.strip().startswith("본문"))
        fields = dict(urllib.parse.parse_qsl(body.split("「", 1)[1].rsplit("」", 1)[0], keep_blank_values=True))
        al = next(l for l in log if "Accept-Language" in l).split()[-1]
        got[lang] = (nav, al, screen, fields, body.strip(), len(info))
    L1, L2 = langs
    for lang in langs:
        nav, al, _, _, body, n = got[lang]
        print(f"[{lang}]  navigator.language = {nav} · 요청 {n}번")
        print(f"  Accept-Language  {al}")
        print(f"  {body}")
    print()
    ids = list(got[L1][2])
    print(칸("칸", 5) + 칸(f"화면({L1})", 26) + 칸(f"화면({L2})", 26) + 칸(f"서버({L1})", 20) + f"서버({L2})")
    ds = dv = 0
    for i in ids:
        s1, s2 = got[L1][2][i], got[L2][2][i]
        v1, v2 = got[L1][3].get(i, "(없음)"), got[L2][3].get(i, "(없음)")
        ds += s1 != s2
        dv += v1 != v2
        print(칸(i, 5) + 칸(json.dumps(s1, ensure_ascii=False), 26) + 칸(json.dumps(s2, ensure_ascii=False), 26)
              + 칸(json.dumps(v1, ensure_ascii=False), 20) + json.dumps(v2, ensure_ascii=False))
    print(f"화면 글자가 갈린 칸 = {ds} / {len(ids)}")
    print(f"서버 값이 갈린 칸 = {dv} / {len(ids)}")


def main():
    global LANG
    args = sys.argv[1:]
    extra = []
    env = None
    if args and args[0].startswith("--lang="):
        # ★ 리눅스의 Chrome 은 --lang 플래그를 안 듣는다(실측) — 환경 변수 LANGUAGE 로 로케일을 준다
        LANG = args.pop(0).split("=", 1)[1]
        env = {**os.environ, "LANGUAGE": LANG.replace("-", "_")}
    mode = args[0]
    if mode == "로케일":
        로케일(args[1], args[2:4])
        return
    a = server("A")
    base = f"http://127.0.0.1:{a.server_address[1]}/"
    if mode == "dom":
        # 창 ① — 같은 로컬 서버에서 연 페이지의 --dump-dom (file:// 의 muted errors 를 피한다 — 규칙 34)
        prof = cdp.PROF + "-dom"
        r = subprocess.run(["google-chrome", "--headless", "--disable-gpu", "--no-sandbox", "--window-size=1000,800",
                            f"--user-data-dir={prof}", "--dump-dom", base + args[1]],
                           capture_output=True, text=True, env=env)
        shutil.rmtree(prof, ignore_errors=True)
        sys.stdout.write(r.stdout)
        a.shutdown()
        sys.exit(r.returncode)
    if mode == "curl":
        # 폼을 거치지 않고 같은 본문을 직접 보낸다 — 브라우저도, 검증도 없다
        body = "addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5"
        cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--data", body, base + "r"]
        print("보낸 명령  curl -s -o /dev/null -w '%{http_code}' --data '" + body + "' http://127.0.0.1:<A>/r")
        r = subprocess.run(cmd, capture_output=True, text=True)
        print("  응답 코드 " + r.stdout + " · curl exit " + str(r.returncode))
        for line in take_log():
            print(("  서버    " if line.startswith("A ") else "        ") + line)
        a.shutdown()
        return
    proc, c = cdp.start(extra, env)
    try:
        tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
        for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable", "Log.enable"):
            c.send(m, sid=sid)
        if mode == "시도":
            시도(c, sid, base, args[1])
        elif mode == "page":
            goto(c, sid, base + args[1])
            넣기(c, sid)
            take_log()
            print(cdp.evaluate(c, sid, "window.__끝()"))
        elif mode == "ax":
            goto(c, sid, base + args[1])
            cdp.dump_tree(c, sid)
        else:
            sys.exit("모드는 시도 | page | ax | dom | curl")
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(cdp.PROF, ignore_errors=True)
        a.shutdown()


if __name__ == "__main__":
    main()
```

```python
# html29b-cdp.py
#!/usr/bin/env python3
"""CDP 로 헤드리스 Chrome 에 붙는 공용 부품 — html29b-form.py 가 불러 쓴다(25편 판을 그대로 이었다).

사용(단독):
  html29b-cdp.py ax   <url|파일>   접근성 트리 전체를 트리 순서로 찍는다
  html29b-cdp.py page <url|파일>   페이지의 window.__대상 = [[열쇠, 선택자], ...] 마다
                              접근성 노드(역할·이름·설명·무시 여부)를 받아 window.__AX 로 넣고
                              window.__끝() 이 돌려준 문자열을 찍는다(표 짜기·칸 세기는 페이지가 한다)

★ 기다림은 시간 상수가 아니라 이벤트다 — Page.loadEventFired 를 받은 뒤에 묻는다.
★ CDP 포트와 프로필 경로는 실행마다 다르다 — 출력에는 안 들어간다.
★ start(extra, env) — 추가 플래그·환경 변수를 주면 그것으로 띄운다(23편의 로케일은 환경 변수 LANGUAGE).
★ internal(c, sid) — chrome://accessibility 의 「blink」 내부 트리 덤프(17편) — CDP 에 없는 nameFrom(이름의 출처)이 거기 있다.
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
PROF = os.path.join(HERE, f".prof-html29b-{os.getpid()}")
# ★ 포트는 0 — Chrome 이 빈 포트를 고르고 프로필의 DevToolsActivePort 에 적는다.
#   고정 범위에서 무작위로 고르면 같은 기계의 다른 작업과 겹칠 수 있다(뒤 브라우저가 앞에 붙는다).
FLAGS = ["--headless", "--disable-gpu", "--no-sandbox", "--window-size=1000,800",
         "--force-renderer-accessibility", "--remote-debugging-port=0",
         f"--user-data-dir={PROF}", "about:blank"]


class Cdp:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, suppress_origin=True)
        self.n = 0
        self.events = []

    def send(self, method, params=None, sid=None):
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(method + " " + json.dumps(r["error"], ensure_ascii=False))
                return r.get("result", {})
            self.events.append(r)

    def post(self, method, params=None, sid=None):
        """응답을 안 기다리고 보낸다 — 디버거 대기 중인 새 창은 run 전까지 답을 안 한다."""
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))

    def wait(self, method, sid=None, pred=lambda p: True):
        """이미 받아 둔 이벤트부터 뒤지고, 없으면 올 때까지 막고 기다린다."""
        while True:
            for i, e in enumerate(self.events):
                if e.get("method") == method and (sid is None or e.get("sessionId") == sid) \
                        and pred(e.get("params", {})):
                    return self.events.pop(i).get("params", {})
            self.events.append(json.loads(self.ws.recv()))


def start(extra=(), env=None):
    shutil.rmtree(PROF, ignore_errors=True)
    proc = subprocess.Popen(["google-chrome"] + FLAGS[:-1] + list(extra) + FLAGS[-1:],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    port_file = os.path.join(PROF, "DevToolsActivePort")
    for _ in range(400):          # 브라우저가 CDP 를 열 때까지 — 순서만 기다린다(값에는 안 들어간다)
        try:
            port = open(port_file).read().split()[0]
            v = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"))
            return proc, Cdp(v["webSocketDebuggerUrl"])
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("CDP 가 안 열렸다")


def open_page(c, url):
    tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable", "Log.enable"):
        c.send(m, sid=sid)
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)
    return sid


def evaluate(c, sid, expr):
    r = c.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True,
                                    "returnByValue": True}, sid)
    if "exceptionDetails" in r:
        d = r["exceptionDetails"]
        return "«예외 " + (d.get("exception", {}).get("description") or d.get("text", "?")) + "»"
    return r.get("result", {}).get("value")


def val(node, key):
    return (node.get(key) or {}).get("value", "")


def ax_of(c, sid, selector):
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    nid = c.send("DOM.querySelector", {"nodeId": root, "selector": selector}, sid)["nodeId"]
    if not nid:
        return {"없음": True}
    nodes = c.send("Accessibility.getPartialAXTree",
                   {"nodeId": nid, "fetchRelatives": True}, sid)["nodes"]
    n = next(x for x in nodes if x.get("backendDOMNodeId") and
             x["backendDOMNodeId"] == backend(c, sid, nid))
    kids = [x for x in nodes if x.get("parentId") == n["nodeId"]]
    props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])}
    src = ""
    for x in (n.get("name") or {}).get("sources", []):   # 이름을 실제로 준 출처 — 값이 있고 밀려나지 않은 첫 줄
        if (x.get("value") or {}).get("value") and not x.get("superseded"):
            src = x.get("type", "") + ":" + (x.get("attribute") or x.get("nativeSource") or "")
            break
    return {"역할": val(n, "role"), "이름": val(n, "name"), "설명": val(n, "description"), "이름출처": src,
            "무시": bool(n.get("ignored")), "속성": props,
            "표지": [val(x, "name") for x in kids if val(x, "role") == "ListMarker"]}


def backend(c, sid, nid):
    return c.send("DOM.describeNode", {"nodeId": nid}, sid)["node"]["backendNodeId"]


def dump_tree(c, sid):
    nodes = c.send("Accessibility.getFullAXTree", {}, sid)["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    SKIP = {"InlineTextBox"}

    def walk(n, d):
        role = val(n, "role")
        ignored = n.get("ignored")
        if role not in SKIP and not ignored:
            name = val(n, "name")
            props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])
                     if p["name"] in ("level", "selected", "disabled", "multiselectable", "multiline", "checked")
                     or (p["name"] == "url" and role == "link")}
            extra = " ".join(f"{k}={v}" for k, v in props.items())
            print(f"{'  ' * d}{role:14} 이름={name!r} {extra}".rstrip())
            d += 1
        for ch in n.get("childIds", []):
            if ch in by:
                walk(by[ch], d)

    for n in nodes:
        if not n.get("parentId"):
            walk(n, 0)


INTERNAL_JS = r"""(async (title) => {
  const until = async (f, what, n = 500) => { for (let i = 0; i < n; i++) { const v = f(); if (v) return v;
    await new Promise(r => setTimeout(r, 20)); }
    throw new Error("내부 덤프 — " + what + " 을 못 기다렸다: pre=" + JSON.stringify([...document.querySelectorAll('#pages pre')].map(q => q.textContent.slice(0, 80)))); };
  const b = await until(() => [...document.querySelectorAll('#pages button')].find(x =>
    x.id.endsWith('showOrRefreshTree') && x.getAttribute('aria-label') === 'Show accessibility tree for ' + title), '단추');
  // ★ 줄이 처음 그려질 때는 모드가 전부 disabled 다 — 「Web: true」로 바뀐 뒤에 눌러야 덤프가 온다
  await until(() => document.querySelector('[aria-label="Web for ' + title + '"][aria-pressed="true"]'), '모드');
  const a = document.getElementById('filter-allow'); a.value = '*'; a.dispatchEvent(new Event('change'));
  // ★ 첫 요청이 빈 트리(「-」)로 돌아오는 판이 있다 — 덤프가 찰 때까지 새로고침 단추를 다시 누른다
  const api = document.getElementById('apiType').value;
  if (api !== 'blink') throw new Error('apiType = ' + api);
  let p = null;
  for (let k = 0; k < 40 && !p; k++) {
    const r = [...document.querySelectorAll('#pages button')].find(x => x.id === b.id) || b;
    r.click();
    try { p = await until(() => { const q = document.querySelector('#pages pre');
      return q && q.textContent.includes('id#=') ? q : null; }, '덤프', 25); } catch (e) { p = null; }
  }
  if (!p) throw new Error('내부 덤프 — 40 번 눌러도 빈 트리다');
  return p.textContent;
})"""


def internal(c, sid):
    """창 ⑦ 의 내부 덤프 — 같은 브라우저의 chrome://accessibility 에 두 번째 창을 열어 받는다."""
    title = evaluate(c, sid, "document.title")
    href = evaluate(c, sid, "location.href")
    sid2 = open_page(c, "chrome://accessibility")
    # ★ 새 창이 앞으로 오면 원래 페이지가 뒤로 밀려 빈 트리(「-」)가 돌아온다 — 원래 페이지를 다시 앞으로
    for t in c.send("Target.getTargets")["targetInfos"]:
        if t["type"] == "page" and t["url"] == href:
            c.send("Target.activateTarget", {"targetId": t["targetId"]})
    text = evaluate(c, sid2, INTERNAL_JS + "(" + json.dumps(title) + ")")
    out = []
    heads = list(re.finditer(r"(\+*)id#=(-?\d+) (\S+)", text or ""))
    if not heads:
        raise RuntimeError("내부 덤프를 못 받았다: " + str(text)[:300])
    for i, m in enumerate(heads):
        body = text[m.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        attrs = {}
        for k, v in re.findall(r"(\w[\w-]*)(?:=('[^']*'|\S+))?", body):
            attrs[k] = v.strip("'") if v else True
        out.append({"깊이": len(m.group(1)) // 2, "역할": m.group(3), "속성": attrs})
    return out


def main():
    mode, url = sys.argv[1], sys.argv[2]
    if "://" not in url:
        url = "file://" + os.path.abspath(url)
    proc, c = start()
    try:
        sid = open_page(c, url)
        if mode == "ax":
            dump_tree(c, sid)
        elif mode == "page":
            targets = evaluate(c, sid, "JSON.stringify(window.__대상 || [])")
            ax = {k: ax_of(c, sid, s) for k, s in json.loads(targets)}
            evaluate(c, sid, "window.__AX = " + json.dumps(ax, ensure_ascii=False))
            print(evaluate(c, sid, "window.__끝()"))
        else:
            sys.exit("모드는 ax | page")
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(PROF, ignore_errors=True)


if __name__ == "__main__":
    main()
```

```javascript
// html29b-rec.js
// 페이지 쪽 기록 — 같은 탭의 sessionStorage 에 적는다(같은 출처로 이동해도 남는다)
const 적기 = s => {
  const a = JSON.parse(sessionStorage.getItem("기록") || "[]");
  a.push(s);
  sessionStorage.setItem("기록", JSON.stringify(a));
};
addEventListener("click", e => {
  const t = e.target.closest("button, input");
  if (t) 적기("click(" + (t.id || t.name) + " · detail=" + e.detail + ")");
}, true);
addEventListener("invalid", e => 적기("invalid(" + e.target.name + ")"), true);
addEventListener("beforeunload", () => sessionStorage.setItem("떠남", "1"));
addEventListener("submit", e => 적기("submit(submitter=" + (e.submitter ? e.submitter.id || e.submitter.name : "null") + ")"), true);
```

```bash
# capture.sh
#!/usr/bin/env bash
# html29b 묶음(HTML 29~32 폼) — 문서에 실을 블록을 전부 파일로 받는다.
#   사용: ./capture.sh [출력디렉토리]    (기본 blocks)
# ★ 출력 디렉토리를 첫머리에서 절대경로로 정규화한다(규칙 25).
# ★ set -o pipefail — 없으면 파이프 뒤 명령의 종료 코드가 기록된다.
# ★ 자르는 명령은 배너에 적되 실행에는 파이프를 물리지 않는다 — 전부 받아 둔 뒤 필터를 건다.
# ★ grep -c 를 블록의 마지막 명령으로 두지 않는다(0건이면 exit 1).
# ★ 표준 출력만 싣는다 — 표준 오류는 버린다(규칙 18).
# ★ 서버 포트는 운영체제가 고른다 — 출력에는 서버 이름 A 만 나온다. multipart 경계는 하네스가 지운다.
# ★ 페이지는 전부 하네스 안의 로컬 서버로 연다(file:// 의 muted errors — 규칙 34). --dump-dom 도 dom 모드로 같은 서버에서.
set -o pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${1:-blocks}"
case $OUT_DIR in /*) ;; *) OUT_DIR="$HERE/$OUT_DIR" ;; esac
SRC="$HERE/src"
RAW="$OUT_DIR/.raw"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR" "$RAW"
cd "$SRC" || exit 1

run() {  # run <열쇠> <명령문자열> — 한 번만 돌려 표준 출력과 종료 코드를 받아 둔다
  local key="$1" cmd="$2"
  if [ ! -f "$RAW/$key.rc" ]; then
    eval "$cmd" > "$RAW/$key.out" 2>/dev/null
    printf '%s' "$?" > "$RAW/$key.rc"
  fi
}

# 출력 블록 — 코드펜스째 뱉는다. 배너 = 실제로 던진 명령 + (있으면) 자르는 필터.
out_block() {  # out_block <블록이름> <열쇠> <명령> [필터]
  local name="$1" key="$2" cmd="$3" pipe="$4" rc
  run "$key" "$cmd"
  rc="$(cat "$RAW/$key.rc")"
  {
    printf '```text\n'
    if [ -n "$pipe" ]; then
      printf '$ %s | %s\n' "$cmd" "$pipe"
      eval "cat '$RAW/$key.out' | $pipe"
    else
      printf '$ %s\n' "$cmd"
      cat "$RAW/$key.out"
    fi
    printf '(exit %s)\n' "$rc"
    printf '```\n'
  } > "$OUT_DIR/$name.txt"
}

form() {  # form <블록이름> <인자…> [-- 필터]
  local name="$1"; shift
  local args="" pipe=""
  while [ $# -gt 0 ]; do
    if [ "$1" = "--" ]; then pipe="$2"; break; fi
    args="$args $1"; shift
  done
  args="${args# }"
  out_block "$name" "form-${args//[ \/#\']/_}" "python3 html29b-form.py $args" "$pipe"
}

# 소스 삽입용 블록 — 원고의 펜스 안에 들어가므로 펜스로 감싸지 않는다.
# 배너는 여기서만 찍는다(basename — 규칙 28). 원고에 손으로 쓰면 이중 배너가 된다.
src_html() { { printf '<!-- %s -->\n' "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_js()   { { printf '// %s\n'        "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_py()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_sh()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }

out_block ver ver "google-chrome --version"
out_block files files "stat -c '%s %n' files/p1.png files/t1.txt files/t2.png"

# ------------------------------------------------------------ 29 제약 검증
src_html 29-grid-src      html29b-29-grid.html
src_js   29-spec-src      html29b-29-spec.js
form     29-grid-out      시도 html29b-29-grid.html -- "sed -n '/^칸 /,\$p'"
src_html 29-submit-src    html29b-29-submit.html
form     29-submit-trials 시도 html29b-29-submit.html -- "sed -n '1,/^\$/p'"
form     29-submit-table  시도 html29b-29-submit.html -- "sed -n '/^시도 /,\$p'"
src_html 29-api-src       html29b-29-api.html
form     29-api-out       시도 html29b-29-api.html -- "sed -n '/^다.checkValidity/,\$p'"

# ------------------------------------------------------------ 30 폼 상태·입력 보조
src_html 30-grid-src      html29b-30-grid.html
src_js   30-spec-src      html29b-30-spec.js
form     30-grid-out      시도 html29b-30-grid.html -- "sed -n '/^속성 · 대상/,\$p'"
src_html 30-ro-src        html29b-30-readonly.html
form     30-ro-out        시도 html29b-30-readonly.html -- "sed -n '/^type /,\$p'"
src_html 30-af-src        html29b-30-autofocus.html
form     30-af-out        page html29b-30-autofocus.html
form     30-af-frag       page "'html29b-30-autofocus.html#p1'"
src_html 30-hints-src     html29b-30-hints.html
src_js   30-hints-spec    html29b-30-hints-spec.js
form     30-hints-out     page html29b-30-hints.html

# ------------------------------------------------------------ 31 파일 업로드
src_html 31-accept-src    html29b-31-accept.html
form     31-accept-one    시도 html29b-31-accept.html -- "sed -n '1,7p'"
form     31-accept-grid   시도 html29b-31-accept.html -- "sed -n '/^길 · 파일/,\$p'"
src_html 31-enc-src       html29b-31-enctype.html
form     31-enc-out       시도 html29b-31-enctype.html
src_html 31-multi-src     html29b-31-multiple.html
form     31-multi-out     시도 html29b-31-multiple.html

# ------------------------------------------------------------ 32 button 의 type 과 폼 소유권
src_html 32-acc-src       html29b-32-accident.html
form     32-acc-trials    시도 html29b-32-accident.html -- "sed -n '1,/^\$/p'"
form     32-acc-table     시도 html29b-32-accident.html -- "sed -n '/^type 없는 + 클릭 /,\$p'"
src_html 32-imp-src       html29b-32-implicit.html
src_js   32-spec-src      html29b-32-spec.js
form     32-imp-out       시도 html29b-32-implicit.html -- "sed -n '/^폼 /,\$p'"
src_html 32-own-src       html29b-32-owner.html
form     32-own-out       시도 html29b-32-owner.html -- "sed -n '/^단추 /,\$p'"
form     32-own-dom       dom html29b-32-owner.html -- "sed -n '/<form id=\"겉\"/,/속가리킴/p'"
src_html 32-sub-src       html29b-32-submitter.html
form     32-sub-out       시도 html29b-32-submitter.html -- "sed -n '/^시도 /,\$p'"

# ------------------------------------------------------------ 하네스 (29-answer 실행 검증)
src_py   form-py          html29b-form.py
src_py   cdp-py           html29b-cdp.py
src_js   rec-js           html29b-rec.js
src_sh   capture-sh       ../capture.sh
```

## 용어 풀이

- **user validity** — 「사용자가 손댔다」 불리언. `:user-*` 의 조건.
- **focus update steps** — 포커스 이동 때 도는 알고리즘. 떠나는 칸의 `change` 와 도장.
- **no-validate 상태** — `formnovalidate`(제출자) 또는 `novalidate`(폼).
- **custom error** — `setCustomValidity` 의 메시지가 빈 문자열이 아닌 상태.
