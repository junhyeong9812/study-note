# html/syntax/32 — `button` 의 `type` 과 폼 소유권: `form` 속성·`formaction`/`formmethod` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [29번 주제](../29-constraint-validation/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 `button` 요소·Implicit submission·폼 소유자·제출 알고리즘·`requestSubmit`/`submit` 절로 접지했다(앞 배치가 받아 둔 사본).\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 서버 요청 로그다** — Enter 격자는 14 칸을 미리 선언하고 「제출된 칸」·「명세 열과 갈린 칸」을 스크립트가 센다(A2).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `type` 없는 「+」 — 제출(`qty=2`) · `type=button` 「+」 — 안 감(`qty=2`) · `type` 없는 `commandfor` — 아무것도(`창.open=false`) · `type=button` `commandfor` — 창이 열림

**출력**

```text
$ python3 html29b-form.py 시도 html29b-32-accident.html | sed -n '1,/^$/p'
[type 없는 + 클릭]
  페이지  click(더하기1 · detail=1) → 손잡이가 올림 qty=2 → submit(submitter=더하기1)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「qty=2」
          필드  qty=「2」
[type=button 인 + 클릭]
  페이지  click(더하기2 · detail=1) → 손잡이가 올림 qty=2
  뒤      {"qty":"2","창":false}
  서버    (받은 요청 없음)
[type 없는 commandfor 단추 클릭]
  페이지  click(열기 · detail=1)
  뒤      {"qty":"1","창":false}
  서버    (받은 요청 없음)
[type=button 인 commandfor 단추 클릭]
  페이지  click(열기2 · detail=1)
  뒤      {"qty":"1","창":true}
  서버    (받은 요청 없음)
[폼 밖 표본 b8 클릭]
  페이지  click(b8 · detail=1)
  뒤      {"qty":"1","창":true}
  서버    (받은 요청 없음)

(exit 0)
```

```text
$ python3 html29b-form.py 시도 html29b-32-accident.html | sed -n '/^type 없는 + 클릭 /,$p'
type 없는 + 클릭                    서버 1번 필드  qty=「2」 · 뒤 (이동해서 없음)
type=button 인 + 클릭               서버 0번 · 뒤 qty=2 창.open=false
type 없는 commandfor 단추 클릭      서버 0번 · 뒤 qty=1 창.open=false
type=button 인 commandfor 단추 클릭 서버 0번 · 뒤 qty=1 창.open=true
폼 밖 표본 b8 클릭                  서버 0번 · 뒤 qty=1 창.open=true

id  속성                                                    .type     willValidate
b1  (없음)                                                  "submit"  true
b2  type="submit"                                           "submit"  true
b3  type="reset"                                            "reset"   false
b4  type="button"                                           "button"  false
b5  type="BUTTON"                                           "button"  false
b6  type="zzz"                                              "submit"  true
b7  type=""                                                 "submit"  true
b8  commandfor="창" command="show-modal"                    "button"  false
b9  type="submit" commandfor="창" command="show-modal"      "submit"  true
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **「+」 둘** — 둘 다 손잡이가 `qty=2` 로 올렸고, **`type` 없는 쪽만** `submit(submitter=더하기1)` 과 **서버 `qty=「2」`**.
- ★★★ **폼 안의 `commandfor` 둘** — `type` 이 없으면 **서버 0 · `창.open=false`**, `type=button` 이면 **`창.open=true`**. **폼 밖**의 `b8`(`type` 없음)은 **`창.open=true`**.
- **표본** — `(없음)`·`submit`·`zzz`·`""` → `"submit"` · `true` · `reset` → `"reset"` · `false` · `button`·`BUTTON` → `"button"` · `false` · **`commandfor` 만 → `"button"` · `false`** · `submit` + `commandfor` → `"submit"` · `true`.

### 2. 제출된 칸 10 / 14 · 명세 열과 갈린 칸 0 / 14 — 안 간 넷은 `f2A`·`f2C`·`f1F`·`f2F`

**출력**

명세 열 파일 —

```javascript
// html29b-32-spec.js
// 명세 열 — 「Implicit submission」: 기본 단추 = 그 폼이 소유한 첫 제출 단추(트리 순서)
// 기본 단추가 있고 비활성이 아니면 그 단추에 click · 비활성이면 아무것도 안 한다 · 제출 단추가 없으면 막는 칸이 둘 이상일 때 돌아가고 아니면 폼 자체로 제출
// type=button·type=reset 은 제출 단추가 아니다 · 폼 밖이라도 form= 으로 소유된 단추는 트리 순서에 든다
const 명세제출 = {
  "1A": true,  "1B": true, "1C": true,  "1D": true, "1E": true, "1F": false, "1G": true,
  "2A": false, "2B": true, "2C": false, "2D": true, "2E": true, "2F": false, "2G": true,
};
```

```text
$ python3 html29b-form.py 시도 html29b-32-implicit.html | sed -n '/^폼 /,$p'
폼   칸 수 단추 구성                                   제출  submitter  서버가 받은 필드
f1A  1     단추 없음                                   예    null       a=「1」
f1B  1     제출 단추                                   예    go         a=「1」 · act=「go」
f1C  1     type=button 만                              예    null       a=「1」
f1D  1     type=button 다음 제출 단추                  예    go         a=「1」 · act=「go」
f1E  1     type=reset 다음 제출 단추                   예    go         a=「1」 · act=「go」
f1F  1     disabled 제출 단추 다음 제출 단추           —    —         (요청 없음)
f1G  1     폼 앞의 form= 제출 단추 다음 안의 제출 단추 예    out        act=「out」 · a=「1」
f2A  2     단추 없음                                   —    —         (요청 없음)
f2B  2     제출 단추                                   예    go         a=「1」 · b=「2」 · act=「go」
f2C  2     type=button 만                              —    —         (요청 없음)
f2D  2     type=button 다음 제출 단추                  예    go         a=「1」 · b=「2」 · act=「go」
f2E  2     type=reset 다음 제출 단추                   예    go         a=「1」 · b=「2」 · act=「go」
f2F  2     disabled 제출 단추 다음 제출 단추           —    —         (요청 없음)
f2G  2     폼 앞의 form= 제출 단추 다음 안의 제출 단추 예    out        act=「out」 · a=「1」 · b=「2」
제출된 칸 = 10 / 14
명세 열과 갈린 칸 = 0 / 14
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- **`A`·`C`(제출 단추 없음)** — 칸 하나면 `submitter=null` 로 제출 · 칸 둘이면 **안 감**.
- **`B`·`D`·`E`** — 칸 수와 무관하게 **`act=go`**(앞의 `type=button`·`type=reset` 을 건너뜀).
- ★★★ **`F`** — 첫 제출 단추가 `disabled` → 둘째가 있어도 **안 감**.
- ★★★ **`G`** — 폼 앞의 `form=` 단추가 눌려 **`act=out`**, 필드의 **맨 앞**.

### 3. `안단추`·`밖단추`·`을안갑` — 갑을 제출(`act=in`·`out`·`inB`) · `없는폼단추`·`속가리킴` — `null` · 요청 없음 · `속단추` — 겉(`/r4`) · 폼 3 개 · `속` 은 트리에 없다

**출력**

```text
$ python3 html29b-form.py 시도 html29b-32-owner.html | sed -n '/^단추 /,$p'
단추        부모      form 속성 button.form  요청      서버가 받은 필드
안단추      form#갑   (없음)    form#갑      GET /r    a=「1」 · act=「in」
밖단추      body      갑        form#갑      GET /r    a=「1」 · act=「out」
없는폼단추  body      없음      null         없음      —
을안갑      form#을   갑        form#갑      GET /r    a=「1」 · act=「inB」
속단추      form#겉   (없음)    form#겉      GET /r4   c=「3」 · act=「nest」
속가리킴    body      속        null         없음      —
form 개수 = 3 · id = 갑 · 을 · 겉
뒤늦게 온 요청 = 0
(exit 0)
```

```text
$ python3 html29b-form.py dom html29b-32-owner.html | sed -n '/<form id="겉"/,/속가리킴/p'
<form id="겉" action="/r4"><input name="c" value="3"><button id="속단추" name="act" value="nest">속</button></form>
<button id="속가리킴" form="속" name="act" value="toNest">속을 가리킴</button>
(exit 0)
```

**왜 그런가**

- ★★★ **`form` 속성이 트리 위치를 이긴다** — `밖단추`(body)·`을안갑`(을 안) 모두 **`form#갑`** · `GET /r` · 을의 `b` 는 없다.
- ★★ **없는 id** — `없는폼단추` 는 `null` · 요청 없음.
- ★★★ **중첩** — 덤프에 `<form id="속">` 이 **없다.** `속단추` 는 겉 안 → `GET /r4 · c=3 · act=nest`. `속가리킴` 의 `form="속"` 은 **가리킬 것이 없어** `null`.

### 4. Enter = 첫 단추 클릭(`POST /r2 · act=a` · 검증 건넘) · 둘째 클릭·`requestSubmit()`·`requestSubmit(둘째)` = `invalid` · `submit()` = `GET /r` · 이벤트 없음 · 예외 `TypeError`·`NotFoundError`

**출력**

```text
$ python3 html29b-form.py 시도 html29b-32-submitter.html | sed -n '/^시도 /,$p'
시도                              submit  invalid  요청       서버가 받은 필드              호출
첫 단추 클릭                      났다    —       POST /r2   q=「1」 · 빈=「」 · act=「a」 —
둘째 단추 클릭                    —      났다     없음       —                            —
q 에서 Enter                      났다    —       POST /r2   q=「1」 · 빈=「」 · act=「a」 —
requestSubmit()                   —      났다     없음       —                            반환됨
requestSubmit(둘째)               —      났다     없음       —                            반환됨
requestSubmit(첫)                 났다    —       POST /r2   q=「1」 · 빈=「」 · act=「a」 반환됨
submit()                          —      —       GET /r     q=「1」 · 빈=「」             반환됨
type=button 단추 클릭             —      —       없음       —                            —
requestSubmit(type=button 단추)   —      —       없음       —                            예외 TypeError
requestSubmit(남의 폼 단추)       —      —       없음       —                            예외 NotFoundError
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **첫 단추 클릭 · q 에서 Enter · `requestSubmit(첫)`** — 셋 다 **`POST /r2`** · `q=「1」 · 빈=「」 · act=「a」` · `invalid` 없음.
- ★★★ **둘째 클릭 · `requestSubmit()` · `requestSubmit(둘째)`** — **`invalid` 로 멈춤** · 요청 없음(`formnovalidate` 가 없는 제출자).
- ★★★ **`submit()`** — `submit` 이벤트 **없음** · `invalid` 없음 · **`GET /r`** · `q=「1」 · 빈=「」` · `act` **없음**.
- **`type=button` 클릭** — 아무것도. **`requestSubmit(type=button)`** — `TypeError` · **`requestSubmit(남의 폼 단추)`** — `NotFoundError`.

### 5. Auto 상태 — ① `type` 이 Auto 상태 ② `command`·`commandfor` 가 둘 다 없음 ③ 부모가 `select` 가 아님

- 명세 — `type` 은 열거 속성이고 「**누락 기본값과 무효 기본값이 둘 다 Auto 상태**」. `button` 이 **제출 단추**인 경우 — 「`type` 이 Auto 상태이고 **`command`·`commandfor` 가 둘 다 없고** 부모 노드가 **`select` 가 아니면**」 **또는** 「`type` 이 Submit Button 상태」.
- 그래서 `type` 없음·`zzz`·빈 글자는 (`commandfor` 가 없으면) **제출 단추**다 — A1 의 표본 `b1`·`b6`·`b7` 이 `willValidate=true`, 폼 안의 「+」가 제출했다.

### 6. 「폼 소유자가 있으면」 갈래의 **뒤** — 그 갈래가 「Auto 상태면 돌아간다」로 먼저 끝난다

- 명세의 `button` 활성화 동작 — ① 비활성이면 끝 ② 문서가 완전히 활성이 아니면 끝 ③ **폼 소유자가 있으면** — 제출 단추면 제출하고 끝 · Reset 상태면 초기화하고 끝 · **Auto 상태면 끝** ④ 그다음에야 **`commandfor` 대상**을 구해 명령을 실행한다.
- `type` 없는 `commandfor` 단추는 **Auto 상태**이고 `commandfor` 때문에 **제출 단추는 아니다** → ③ 의 첫 줄은 지나가지만 **셋째 줄에서 끝난다.** **폼 밖**이면 ③ 을 건너뛰어 ④ 에 닿는다 — 폼 밖 표본 `b8`(`type` 없음 · `commandfor`)을 누르니 **`창.open=true`**(A1). **`type="button"` 이면 Button 상태**라 ③ 의 어느 줄에도 안 걸려 ④ 로 간다(A1 — `창.open=true`).

### 7. 「그 폼이 소유한 트리 순서로 첫 제출 단추」 — `button`·`reset` 은 제출 단추가 아니라 건너뜀 · `disabled` 는 기본 단추가 되고 끝 · 폼 앞의 `form=` 단추는 기본 단추

- 명세 — 「폼의 **기본 단추**는 폼 소유자가 그 폼인 **트리 순서로 첫 제출 단추**」 · 「기본 단추가 활성화 동작이 있고 **비활성이 아니면** click 을 쏜다」.
- **`type=button`·`type=reset`** — 제출 단추가 아니다 → **후보가 아니다**(A2 의 `D`·`E` — 뒤의 `go`).
- **`disabled`** — 제출 단추이므로 **기본 단추가 된다** → 비활성이라 **아무것도 안 한다**(A2 의 `F`). 「제출 단추가 없으면」 갈래도 아니다.
- **폼 앞의 `form=` 단추** — **폼 소유자가 그 폼**이고 **트리 순서로 앞** → 기본 단추(A2 의 `G` — `act=out`).

### 8. 기본 단추(= Enter 가 click 을 쏜 단추)의 것 — 그 단추가 제출자이기 때문이다

- 암묵 제출은 **기본 단추에 click 을 쏘는 것**이다 → 그 단추의 활성화 동작이 **「그 단추에서」 제출**한다 → 제출자 = 그 단추.
- 제출 알고리즘은 **제출자 요소의** method·action·enctype·no-validate 를 읽는다(`formmethod` 가 있으면 그 상태, 없으면 폼 소유자의 것). 항목 목록은 「단추인데 **제출자가 아니면** 건너뛴다」 → 제출자의 `name`/`value` 만 실린다. A4 — Enter 가 **첫 단추 클릭과 한 글자도 같다.**

### 9. `requestSubmit()` — 검증 · 이벤트 · 단추 설정 없음 · `requestSubmit(단추)` — 셋 다 그 단추대로 · `submit()` — 셋 다 없음 / 예외 — 제출 단추가 아님(`TypeError`) · 소유자가 다름(`NotFoundError`)

- **`requestSubmit()`** — 「submitter 가 null 이면 **submitter 를 이 폼으로**」 → 폼의 설정 · 검증이 돈다 · `submit` 이벤트가 난다 · 단추 값 없음(A4 — `invalid` 로 멈춤).
- **`requestSubmit(첫)`** — 그 단추에서 제출 → `formaction`·`formmethod`·`formnovalidate`·`name`/`value` **전부**.
- **`submit()`** — 「**submitted from submit() method** 를 참으로」 → 검증·`submit` 이벤트·도장 단계를 **건너뛴다** · 제출자는 폼 자신([21번](../21-form-submission-model/2-summary.md)의 「어디서 틀리나」 3).
- 예외 — 명세의 두 줄 그대로(A4).

### 10. `commandfor` 단추의 `.type` — 구현(관찰) · `disabled` 기본 단추 — 명세대로 · `form="없는id"` — 명세대로

- **`.type` 의 `"button"`** — 명세상 Auto 상태다. IDL 이 무엇을 돌려줘야 하는지는 **받아 둔 사본에서 문장을 찾지 못했다** → **이 판의 관찰**로만.
- **`disabled` 기본 단추** — 「기본 단추가 … **비활성이 아니면** click」 → 명세대로(A2 — 명세 열 0 갈림).
- **`form="없는id"`** — 폼 소유자가 **없다** → 활성화 동작의 「폼 소유자가 있으면」을 못 타고 `commandfor` 도 없다 → 명세대로.

### 11. 정본 경계

- **제출을 일으키는 것 열여섯 시도** — [21번](../21-form-submission-model/2-summary.md)의 (2).
- **`input` 의 `form` 속성 · 표 안의 `form`** — [21번](../21-form-submission-model/2-summary.md)의 (4).
- **누른 단추만 실린다(클릭·그림 단추)** — [24번](../24-input-types-choice-special/2-summary.md)의 (1).
- **중첩 `form`** — [05번](../05-content-categories-and-models/2-summary.md).
- **`dialog` 를 여는 것** — 목록의 **47번 주제**.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 하네스는 [29번](../29-constraint-validation/3-answer.md)의 `html29b-form.py` 다.\
★ **Enter** — 칸에 포커스를 두고 `Input.dispatchKeyEvent` 로 `Enter`(가상 키코드 13 · `text="\r"`)를 눌렀다([21번](../21-form-submission-model/3-answer.md)과 같다).\
★ **`requestSubmit`·`submit()`** — 페이지 안에서 `try … catch` 로 불러 **예외 이름**을 기록했다.

**흔들림 확인** — 캡처 세 판의 재대조는 [29번](../29-constraint-validation/3-answer.md)의 `## 실행 검증` 에 있다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **폼 안의 단추 넷 · 표본 아홉** | 3 | 동작 방식 (1) · A1 |
| **Enter 격자 14 폼** | 3 | 동작 방식 (2) · A2 |
| **단추 여섯의 소유자 · 덤프** | 3 | 동작 방식 (3) · A3 |
| **제출을 일으키는 열 가지** | 3 | 동작 방식 (4) · A4 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| Auto 상태의 `.type` | `"submit"`·`"button"` 두 이름 | IDL 문장을 확인하지 못했다 |

**안 돌려 본 것** — ① **`formtarget`.** ② **`select` 안의 `button`**(명세 — 부모가 `select` 면 제출 단추가 아니다). ③ **`input type=submit`/`image` 의 `form` 속성.**

**못 잰 것** — ① **모바일 가상 키보드의 「이동」 키.**

**부적용인 창** — **창 ③ · ④ · ⑥ · ⑦**.

## 용어 풀이

- **Auto 상태** — `type` 이 없거나 무효한 `button` 의 상태.
- **기본 단추** — 소유한 트리 순서의 첫 제출 단추.
- **제출자** — 제출을 일으킨 단추 또는 폼.
