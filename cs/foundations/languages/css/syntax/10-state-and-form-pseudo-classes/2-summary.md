# css/syntax/10 — 상태·폼 의사 클래스: `:hover`·`:focus-visible`·`:checked`·`:disabled` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Selectors Level 4](https://drafts.csswg.org/selectors-4/) 의 [§사용자 동작](https://drafts.csswg.org/selectors-4/#useraction-pseudos) · [`:focus-visible`](https://drafts.csswg.org/selectors-4/#the-focus-visible-pseudo) · [§입력 의사 클래스](https://drafts.csswg.org/selectors-4/#input-pseudos) · [`:user-valid`/`:user-invalid`](https://drafts.csswg.org/selectors-4/#user-pseudos) · [§링크 의사 클래스](https://drafts.csswg.org/selectors-4/#location). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 주제는 **스크린샷만으로는 안 된다.** `:hover`·`:active`·`:focus-visible` 은 입력이 있어야 켜진다. 그래서 **Google Chrome 151.0.7922.173** 을 `--remote-debugging-port` 로 띄우고 **CDP 로 실제 마우스 이동·버튼 누름·Tab 키·문자 입력을 넣은 뒤** `element.matches(':hover')` 와 `getComputedStyle` 을 읽었다. 넣은 입력의 정확한 명령은 [3-answer.md](3-answer.md) 의 「실행 검증」 절에 그대로 적어 두었다.\
> `demo` 블록 **2개 전부**와 그 「바꿔 볼 것」도 같은 방식으로 확인했다. **WebKit(Safari)은 이 머신에 없다** — Safari 관련 서술은 하지 않았다. **엔진은 Chrome 하나**다.
> **버전** — CSS 에 언어 버전은 없다. Baseline(2026-09-23 에 `api.webstatus.dev` 조회): `:checked`/`:disabled` 등 입력 의사 클래스 **widely**(2015-07-29 → 2018-01-29) · `:focus-within` **widely**(2020-01-15 → 2022-07-15) · `:placeholder-shown` **widely**(2020-01-15 → 2022-07-15) · `:focus-visible` **widely**(2022-03-14 → 2024-09-14) · **`:user-valid`/`:user-invalid` widely**(newly 2023-11-02 → widely 2026-05-02, Chrome 119 · Firefox 88 · Safari 16.5).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**여기 선택자들은 「켜졌다 꺼지는 그물」이다. 그리고 켜는 스위치가 저마다 다르다.**

08\~11 의 비유(그물 모양 / 그물의 힘)를 이어받아, 여기서는 **모양이 시간에 따라 바뀐다.**

| 비유 | 실체 | 스위치를 누르는 것 |
|---|---|---|
| 손을 얹으면 켜지는 등 | `:hover` | 포인터의 **위치** |
| 누르고 있는 동안만 | `:active` | 버튼을 **누른 채** |
| 여기에 입력이 간다 | `:focus` | 포커스가 **어떻게 왔든** |
| 여기에 입력이 가는 걸 **보여 줘야 한다** | `:focus-visible` | 브라우저가 **어떻게 왔는지 보고 판단** |
| 폼이 처음부터 틀렸다 | `:invalid` | **아무도 아무것도 안 해도** 켜져 있다 |
| 사용자가 **틀리게 만들었다** | `:user-invalid` | 사람이 **건드리고 떠난 뒤에만** |

- ★ **`:focus` 와 `:focus-visible` 이 갈리는 자리가 이 주제의 과녁이다.** 같은 요소·같은 포커스인데 **입력 방식**에 따라 하나는 켜지고 하나는 안 켜진다.
- ★ **`:invalid` 와 `:user-invalid` 는 시점이 다르다.** 앞엣것은 페이지가 뜬 순간 이미 켜져 있고, 뒤엣것은 사람이 손대고 나간 다음이다.
- 그리고 **순서 문제**가 하나 있다 — `:link`·`:visited`·`:hover`·`:active` 는 **명시도가 전부 같아서** 쓰는 순서가 승부를 정한다((6) 절).

```text
   시간축으로 본 한 입력칸 (type=email required, 비어 있음)

   t0 페이지 로드     :invalid                     <- 이미 빨갛게 할 수 있다
        |            (:user-invalid 아님)
   t1 클릭/Tab        :focus  (+:focus-visible?)
        |
   t2 "ab" 입력       :invalid                     <- 아직 :user-invalid 아님
        |
   t3 칸 밖으로 나감   :invalid :user-invalid       <- 여기서 켜진다
```

실무에서 이게 터지는 자리는 「**아직 입력도 안 했는데 칸이 벌겋게 물든 폼**」과 「**마우스로 누를 때마다 파란 테두리가 튀어나오는 버튼**」이다. 둘 다 `:invalid`·`:focus` 만 알고 뒤의 짝을 모를 때 나온다.

> **의사 클래스(pseudo-class)** — 요소의 상태나 위치를 가리키는 `:` 로 시작하는 선택자.

> **포커스(focus)** — 지금 키보드 입력이 들어갈 요소. 문서에 하나뿐이고 `document.activeElement` 로 읽는다.\
> 예: 입력칸을 클릭하면 그 칸이 포커스를 갖는다.

> **제약 검증(constraint validation)** — `required`·`type=email`·`pattern`·`min`/`max` 같은 HTML 속성으로 값이 규칙에 맞는지 브라우저가 판정하는 것.\
> 예: `type="email"` 인 칸에 `ab` 가 들어 있으면 그 칸은 「맞지 않음」이다.

## 이 주제가 답하려는 질문

1. `:focus` 와 `:focus-visible` 이 **어떤 입력에서 갈리는가** — 그리고 요소 종류에 따라 또 갈리는가.
2. `:invalid` 가 **언제부터 켜져 있는가**, `:user-invalid` 는 정확히 **무엇을 기다리는가**.
3. `:link`·`:visited`·`:hover`·`:active` 를 **왜 그 순서로 써야 하는가** — 명시도가 아니라 무엇이 정하는가.

## 예시 데이터 — 이 편이 쓰는 폼

`10-form.html`. 여기에 CDP 로 실제 입력을 넣어 가며 `matches()` 를 찍었다.

```text
form#f
 ├─ button#btn                                버튼
 ├─ input#txt  type=text  required  placeholder="이메일"
 ├─ label#lab  > input#chk  type=checkbox     체크박스
 ├─ input#dis  type=text  disabled  value="x"
 ├─ input#opt  type=text  value="ok"          (required 없음)
 ├─ input#mail type=email required           (비어 있음)
 └─ a#lnk      href="https://example.invalid/never-visited"
div#wrap
 └─ input#inner type=text
```

## 동작 방식

### (1) `:hover` 와 `:active` — 포인터가 만드는 상태

**언제 쓰나** — 마우스 상호작용의 되먹임을 줄 때.

```text
   CDP 로 넣은 입력                          그때 버튼이 맞는 선택자
   ─────────────────────────────────────────────────────────────
   (아무것도 안 함)                          (없음)
   Input.dispatchMouseEvent mouseMoved       :hover
      -> 버튼 중심 좌표로
   Input.dispatchMouseEvent mousePressed     :hover :active :focus
      -> 뗴지 않은 상태
   Input.dispatchMouseEvent mouseReleased    :hover :focus
      -> 뗀 직후                                    ^^^^^^ :active 가 꺼졌다
```

그림 해설 (한 단계씩):

- **`:hover` 는 포인터가 위에 있기만 하면** 켜진다. 누를 필요가 없다.
- **`:active` 는 누르고 있는 동안만**이다. 떼는 순간 꺼진다 — 실측에서 `mouseReleased` 직후 목록에서 빠졌다.
- **누르는 순간 `:focus` 도 같이 켜졌다.** 포커스는 `mousePressed` 시점에 옮겨간다.
- ★ **이 셋은 스크린샷으로는 확인할 수 없다.** 입력을 안 넣으면 화면은 평소 상태 그대로다. 그래서 이 주제는 CDP 가 필수다.

비용 — 없다. 다만 **터치 기기에는 `:hover` 가 사실상 없다** — 손가락은 올려놓고 있을 수가 없다. 호버에만 정보를 담으면 터치에서 사라진다.

### (2) `:focus` 대 `:focus-visible` — 같은 포커스, 다른 판정 ★ 이 주제의 과녁

**언제 쓰나** — 포커스 링(테두리)을 그릴 때. **거의 항상 `:focus-visible` 쪽이다.**

```text
   같은 <button> 에 포커스를 주는 두 경로

   마우스로 클릭                          Tab 키로 이동
   +-------------------------+            +-------------------------+
   | :focus          O       |            | :focus          O       |
   | :focus-visible  X       |            | :focus-visible  O       |
   +-------------------------+            +-------------------------+
     "어디를 눌렀는지 사용자가              "지금 어디 있는지 안 보이면
      이미 안다" -> 링을 안 그린다            길을 잃는다" -> 링을 그린다
```

```text
   실측 (Chrome 151 headless + CDP, 버튼 / 텍스트 입력칸)

   로드 직후                  btn: -                        txt: -
   Tab 1회                    btn: :focus :focus-visible    txt: -
   Tab 2회                    btn: -                        txt: :focus :focus-visible
   마우스 클릭 (버튼)          btn: :focus :hover            txt: -
   마우스 클릭 (텍스트칸)      btn: -                        txt: :focus :focus-visible :hover
                                                                   ^^^^^^^^^^^^^^ 클릭인데도 켜진다
```

★ **요소 종류가 세 번째 변수다.**

- **버튼을 마우스로 클릭** → `:focus` 만. `:focus-visible` 은 **안 켜진다.**
- **텍스트 입력칸을 마우스로 클릭** → **둘 다 켜진다.**
- 체크박스를 마우스로 클릭 → `:focus` 만(실측: `:checked :hover :focus :enabled`).

브라우저의 판단 기준은 **이 요소가 키보드 입력을 받는가** 하나다. 텍스트칸은 클릭해서 왔어도 **곧 키보드를 쓸 것**이므로 커서 위치를 보여 줘야 한다.

```html demo
<button class="b">클릭해 보고, Tab 으로도 와 보세요</button>
<style>
  .b { padding: 8px 14px; font: 16px system-ui; border: 1px solid #94a3b8; }
  .b:focus         { background: #fde68a; outline: none; }
  .b:focus-visible { outline: 3px solid #b91c1c; }
</style>
```

> **보이는 것** — **마우스로 클릭하면 배경만 노랗게** 바뀌고 외곽선은 안 생긴다. **Tab 키로 오면 노란 배경에 더해 빨간 3px 외곽선**이 같이 생긴다. 같은 버튼, 같은 포커스인데 들어온 길이 달라서 결과가 다르다.\
> **바꿔 볼 것** — `.b:focus-visible` 을 `.b:focus` 로 바꾸면 **마우스 클릭에도 빨간 외곽선이 생긴다**(이것이 흔히 「포커스 링이 거슬린다」고 지워 버리게 되는 원인이다)

*(Chrome 151 headless + CDP 실측 — 마우스 클릭 후: `background-color: rgb(253, 230, 138)`, `outline-style: none`. Tab 후: 같은 배경에 `outline: solid 3px rgb(185, 28, 28)`. `:focus-visible` 을 `:focus` 로 바꾼 판은 마우스 클릭만으로 `outline: solid rgb(185, 28, 28)` 이 나왔다.)*

- `:focus-within` 은 「**나 또는 내 자손이 포커스를 가졌다**」다. 실측에서 `#wrap` 안쪽 입력칸에 포커스를 주니 `#wrap` 이 `:focus-within` 에 맞았다.

비용 — 없다. **`outline: none` 을 `:focus` 에 거는 것이 접근성 사고의 단골**이다. 지우려면 `:focus-visible` 로 되살릴 것을 같이 써라.

### (3) `:checked`·`:disabled` — 켜짐·꺼짐 두 갈래

**언제 쓰나** — 체크박스·라디오·`select` 와 비활성 컨트롤을 칠할 때.

```text
   폼을 띄우자마자 (사용자 입력 0) 실측

   fieldset#fs [disabled]   :disabled :read-only :valid
    ├─ input#fi             :disabled :optional :read-only     <- 조상에서 내려왔다
    └─ button#fb            :disabled :default  :optional :read-only
   input#r1 [radio checked] :enabled :checked :default :optional :read-only :valid
   input#r2 [radio]         :enabled :optional :read-only :valid
   option#o1 [selected]     :enabled :checked :default :read-only
   input#ro [readonly required] :enabled :required :read-only
   input#pat [pattern 불일치]   :enabled :optional :read-write :invalid
   input#num [min=1 max=5 value=9] :enabled :optional :read-write :invalid :out-of-range
```

그림 해설 (한 단계씩):

- **`:disabled` 는 조상에서 내려온다.** `fieldset[disabled]` 안의 `input`·`button` 이 전부 `:disabled` 였다.
- **`:checked` 는 체크박스·라디오뿐 아니라 `option` 에도 걸린다**(실측: `option#o1`).
- `:default` 는 「**문서에 적힌 초기 선택**」이다 — 처음부터 `checked` 인 라디오, `selected` 인 `option`, 그리고 폼의 **첫 제출 버튼**(실측에서 `button#fb` 가 그랬다).
- **`:read-only` 가 입력칸이 아닌 것에도 붙는다.** `fieldset`·라디오·`option` 이 전부 `:read-only` 였다 — "편집 가능한 것이 아니면 read-only" 라는 뜻이다. **`:read-only` 를 "readonly 속성이 있다"로 읽으면 틀린다.**
- ★ **`[checked]` 속성과 `:checked` 상태는 다른 것이다.**

```text
   <input id="c1" type="checkbox" checked>   <input id="c2" type="checkbox">

   초기                      c1: 속성 O  :checked O      c2: 속성 X  :checked X
   사용자가 c1 을 끄고
   c2 를 켠 뒤               c1: 속성 O  :checked X      c2: 속성 X  :checked O
                                  ^^^^^ 속성은 그대로 남는다
```

`[checked]` 는 **초기값**을 적어 둔 HTML 속성이고 `:checked` 는 **지금 상태**다. 속성 선택자([08번](../08-basic-selectors-and-combinators/2-summary.md))로 폼 상태를 고르면 사용자 조작 뒤에 조용히 어긋난다.

비용 — 없다. 다만 `:disabled` 인 컨트롤은 **제약 검증에서 아예 빠진다** — 다음 절.

### (4) `:valid`/`:invalid` — 아무도 안 건드려도 이미 켜져 있다

**언제 쓰나** — 폼 오류 표시를 만들 때. **여기가 「빨간 폼」 사고의 진원지다.**

```text
   실측 — 페이지가 뜬 직후, 사용자 입력 0

   input#txt  [text required, 비어 있음]     :required :invalid :placeholder-shown
   input#mail [email required, 비어 있음]    :required :invalid
   input#opt  [text value="ok"]              :optional :valid
   input#dis  [text disabled]                :disabled            <- valid 도 invalid 도 아니다
   input#ro   [readonly required 값 있음]    :enabled :required :read-only
                                                      ^^ valid/invalid 둘 다 없다
```

그림 해설 (한 단계씩):

- **비어 있는 `required` 칸은 로드 직후부터 `:invalid`** 다. 사용자는 아직 아무것도 안 했다.
- **`:disabled` 와 `readonly` 는 제약 검증에서 제외된다** — `:valid` 에도 `:invalid` 에도 안 맞는다.\
  "둘 중 하나겠지"가 틀리는 자리다.
- `:out-of-range` 는 `min`/`max` 를 벗어난 수치 입력에 따로 붙는다(실측: `value=9`, `max=5`).

### (5) `:user-valid`/`:user-invalid` — 사람이 건드린 뒤에만

**언제 쓰나** — (4) 의 「처음부터 빨간 폼」을 고칠 때. 이것이 처방이다.

```text
   실측 (Chrome 151 + CDP) — input#mail [type=email required placeholder="이메일"]

   ① 로드 직후                 :required :invalid :placeholder-shown
   ② 클릭 + "ab" 입력, 포커스 중 :required :invalid
   ③ blur (칸 밖으로)          :required :invalid :user-invalid      <- 여기서 켜진다
   ④ 값을 a@b.co 로 고치고 blur :required :valid   :user-valid
   ⑤ (새로 로드) JS 로만 값 주입 :required :invalid                   <- user-* 안 켜진다
      element.value = 'zzz'
```

- `:user-invalid` 는 「**사용자가 건드렸고, 그 칸을 떠났고, 그런데도 틀렸다**」일 때만 켜진다.
- ★ **②에서 아직 안 켜진 것**이 핵심이다 — 타이핑하는 도중에 빨갛게 되지 않는다. "쓰는 중인데 혼내는" UI 를 막아 준다.
- ★ **⑤가 경계다.** 스크립트로 값만 넣은 것은 **사용자 조작이 아니다.** 자동 채움·복원 로직을 짠 뒤 `:user-invalid` 가 안 켜져 당황하는 자리다.

```html demo
<input class="e" type="email" required placeholder="이메일">
<style>
  .e { padding: 6px; font: 16px system-ui; border: 2px solid #94a3b8; }
  .e:invalid      { background: #fee2e2; }
  .e:user-invalid { border-color: #b91c1c; }
</style>
```

> **보이는 것** — 페이지가 뜨자마자 **칸 배경이 이미 연분홍**이다(`:invalid`). 아직 아무것도 안 했는데 그렇다. 테두리는 아직 회색이다. 칸을 클릭해 아무 글자나 치고 **칸 밖을 눌러 빠져나오면 그제야 테두리가 빨갛게** 바뀐다(`:user-invalid`). 타이핑하는 동안에는 테두리가 안 바뀐다.\
> **바꿔 볼 것** — `.e:invalid` 를 `.e:user-invalid` 로 바꾸면 **로드 직후 분홍 배경이 사라진다**(흰 바탕으로 뜬다)

*(Chrome 151 headless + CDP 실측 — 로드 직후: `background-color: rgb(254, 226, 226)`, `border-top-color: rgb(148, 163, 184)`. `ab` 입력 후 포커스 중: 그대로. blur 후: 배경 그대로에 `border-top-color: rgb(185, 28, 28)`. `:invalid` 를 `:user-invalid` 로 바꾼 판은 로드 직후 `background-color: rgb(255, 255, 255)`.)*

- **`:placeholder-shown`** 은 placeholder 가 실제로 **보이고 있을 때**(값이 비었을 때)만 맞는다. 실측에서 `ab` 를 치자 목록에서 빠졌다.

비용 — 없다. **오늘 폼 오류 표시의 기본형은 `:user-invalid`** 다(Baseline widely, 2026-05-02).

### (6) 순서 문제 — LVHA

**언제 쓰나** — 링크에 호버 스타일을 줄 때. 안 먹으면 거의 항상 이것이다.

```text
   a:link      (0, 1, 1)
   a:visited   (0, 1, 1)
   a:hover     (0, 1, 1)      <- 넷의 명시도가 전부 같다
   a:active    (0, 1, 1)

   실측으로 고정: a:hover 뒤에 a.zz (0,1,1) 를 쓰면 a.zz 가 이기고 (동점 -> 순서),
                 a:hover 뒤에 .zz  (0,1,0) 를 쓰면 a:hover 가 이긴다 (한 칸 높다).

   명시도가 같으면 승부는 캐스케이드 6단계 = 등장 순서로 간다 (01번)
   => 뒤에 쓴 것이 이긴다
   => 좁은 조건(hover, active)을 뒤에 써야 한다
```

```text
   실측 (Chrome 151 + CDP, 방문한 적 없는 링크)

   a:link{color:blue} a:hover{color:red}     평소 rgb(0, 0, 255)  호버 rgb(255, 0, 0)   먹는다
   a:hover{color:red} a:link{color:blue}     평소 rgb(0, 0, 255)  호버 rgb(0, 0, 255)   안 먹는다
                                                                       ^^^^^^^^^^^^^ 색이 안 변한다
```

- **`:link` 를 `:hover` 뒤에 쓰면 호버가 통째로 가려진다.** 두 규칙 다 살아 있고 둘 다 매치되는데, 나중에 쓴 `:link` 가 이긴다.
- 그래서 외우는 순서가 **L → V → H → A**(`:link`·`:visited`·`:hover`·`:active`)다. 흔히 "LoVe HAte" 로 외운다.
- ★ **이것은 명시도 문제가 아니다.** 명시도를 아무리 올려도 순서를 안 고치면 똑같다 — 진단 순서는 [01번](../01-cascade-and-priority/2-summary.md)이 정본이다.
- `:any-link` 는 `:link` 와 `:visited` 를 합친 것이다(실측: 방문 안 한 링크가 `:link :any-link` 둘 다 맞았다).

비용 — 없다. **`:visited` 는 이 머신에서 실행 확인하지 못했다**(headless 프로파일에 방문 기록이 없다). 켜졌을 때 무엇이 보이는지는 「미실행」이다.

## 문법 — 어디서 헷갈리나

### 형태

```css
.btn:hover              { }   /* 상태는 대상 뒤에 붙인다 */
.btn:focus-visible      { }
.field:has(:focus)      { }   /* 자손의 상태를 부모에 — 12번 주제 */
.group:focus-within     { }   /* :has(:focus) 의 전용 축약형 */
input:checked + .label  { }   /* 상태를 조합자로 이어 옆 요소를 칠한다 */
```

### 헷갈리는 자리

- **`:disabled` 는 `[disabled]` 와 다르다** — 조상 `fieldset` 에서 내려온 것도 `:disabled` 이지만 속성은 없다.
- **`:checked` 는 `[checked]` 와 다르다** — 위 (3) 의 실측.
- **`:read-only` 는 "readonly 속성"이 아니다** — 편집 가능하지 않은 모든 요소다(`fieldset`·라디오·`option` 포함).
- **`:required` 는 `input`·`select`·`textarea` 에만 붙는다.**\
  *(Chrome 151 headless 실측: `<div required>` 를 놓고 `div:required` 를 던지면 0개, 같은 문서의 `input[required]` 는 1개.)*
- **`:focus-within` 은 부모에 건다.** 자식에 걸면 `:focus` 와 다를 바 없다.
- **`:hover` 는 조상에도 걸린다** — 자식 위에 포인터가 있으면 부모도 `:hover` 다.\
  *(Chrome 151 + CDP 실측: 링크 위로 마우스를 옮기니 그 링크·부모 `div`·`body` 가 전부 `:hover` 였다.)*

## 어디서 틀리나

### 1. 포커스 링을 `:focus` 로 지운다

```css
button:focus { outline: none; }   /* 키보드 사용자가 길을 잃는다 */
```

마우스 클릭의 링이 거슬려 지우면 **Tab 사용자의 링까지 사라진다.**\
처방은 `:focus-visible` 로 되살리는 것이다 — 실측에서 마우스 클릭은 `:focus-visible` 에 **안** 걸렸다((2) 절).

### 2. `:invalid` 로 오류를 칠한다

```css
input:invalid { border-color: red; }   /* 로드 직후 빈 required 칸이 전부 빨갛다 */
```

실측에서 비어 있는 `required` 칸은 **페이지가 뜨자마자** `:invalid` 였다.\
사용자가 손대기 전에 혼내지 않으려면 **`:user-invalid`** 다((5) 절).

### 3. `:user-invalid` 가 타이핑 중에 켜진다고 생각한다

실측 ②에서 `ab` 를 친 상태·포커스 유지 중에는 **안 켜졌다.** **칸을 떠나야** 켜진다.\
그리고 ⑤ — **스크립트로 값만 넣으면 영영 안 켜진다.**

### 4. `:hover` 를 `:link`·`:visited` 앞에 쓴다

```css
a:hover   { color: red; }    /* 이 순서면 아래에 가려진다 */
a:link    { color: blue; }
```

명시도가 `(0,1,1)` 로 **같아서** 순서가 승부를 낸다. 실측에서 호버해도 색이 `rgb(0, 0, 255)` 그대로였다.

### 5. `:disabled` 인 칸이 `:valid` 나 `:invalid` 중 하나일 거라고 생각한다

실측에서 `input#dis` 는 **둘 다 아니었다.** `readonly` 도 마찬가지다.\
`form:invalid` 로 제출 버튼을 잠그는 패턴에서 **비활성 칸이 검증에서 빠진다**는 것을 모르면 진단이 안 된다.

### 6. 스크린샷으로 이 주제를 검증하려 한다

`:hover`·`:active`·`:focus-visible` 은 **입력이 없으면 화면에 아무 흔적도 없다.**\
★ 첫 확인에서 스크린샷만 찍으면 **「스타일이 안 먹네」로 오진**한다. CDP 로 입력을 넣거나, 못 하면 **「미실행」으로 적어야** 한다.

## 구현 세부사항 대 언어 보장

| 것 | 성격 | 근거 |
|---|---|---|
| `:hover`·`:active`·`:focus` 의 의미 | **명세 보장** | Selectors 4 §useraction-pseudos |
| **`:focus-visible` 이 언제 켜지나** | ★ **UA 휴리스틱** — 명세가 "UA 가 판단한다"고 정했다 | Selectors 4 §the-focus-visible-pseudo |
| 마우스 클릭한 버튼에 안 켜지는 것 | **Chrome 151 의 관찰** | 이 문서 (2) 의 실측. 다른 엔진은 미확인 |
| 마우스 클릭한 **텍스트칸**에는 켜지는 것 | **Chrome 151 의 관찰** | 같은 실측 |
| `:user-invalid` 가 blur 에서 켜지는 것 | ★ **UA 가 정하는 시점** — 명세는 "사용자가 값과 상호작용한 뒤"라고만 한다 | Selectors 4 §user-pseudos · 이 문서 (5) 의 실측 |
| `:disabled`/`readonly` 가 검증에서 빠지는 것 | **HTML 명세 보장**(barred from constraint validation) | 이 문서 (4) 의 실측과 일치 |
| `:visited` 에 쓸 수 있는 속성이 제한되는 것 | **프라이버시 제약** — 이 머신에서 **미실행** | 방문 기록이 없는 headless 프로파일이라 확인 못 했다 |
| LVHA 순서가 필요한 이유 | **명세 보장** — 넷의 명시도가 같다 | [02번](../02-specificity/2-summary.md) · 이 문서 (6) 의 실측 |

★ **위 두 줄이 이 주제에서 가장 조심할 자리다.** `:focus-visible` 과 `:user-invalid` 의 **정확한 발동 시점은 명세가 UA 에 맡긴 것**이고, 내가 잰 것은 **Chrome 151 한 엔진의 행동**이다. 「모든 브라우저가 이렇다」고 적지 않는다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 포커스 링 | `:focus-visible` | `:focus` 에 `outline: none` |
| 폼 오류 표시 | `:user-invalid` | `:invalid` 단독 |
| 폼 성공 표시 | `:user-valid` | `:valid` 단독 |
| "이 묶음 안에 포커스가 있다" | `:focus-within` | JS 이벤트 |
| 체크 상태로 옆 라벨 칠하기 | `input:checked + label` | `[checked]` |
| 비활성 스타일 | `:disabled` | `[disabled]` |
| 링크 상태 | LVHA **순서대로** | 순서 무시 + `!important` |
| 터치 기기에서도 보여야 할 정보 | 항상 보이게 | `:hover` 에만 담기 |
| `:hover` 를 "가리키는 중"으로 쓰기 | 보조 정보에만 | 유일한 조작 경로로 |

판단 규칙 두 줄.

- **"사용자가 아직 아무것도 안 했을 때 무엇이 켜져 있나"를 먼저 물어라.** `:invalid` 사고는 전부 거기서 난다.
- **포커스 관련 스타일은 반드시 Tab 으로도 한 번 와 보라.** 마우스로만 확인하면 절반만 본 것이다.

## 핵심 문장

- 여기 선택자들은 **입력에 따라 켜졌다 꺼진다** — 스크린샷만으로는 검증되지 않는다.
- **`:focus` 는 어떻게 왔든 켜지고, `:focus-visible` 은 브라우저가 「보여 줄 필요가 있나」를 판단해 켠다.**\
  실측: 버튼을 마우스로 클릭 → `:focus` 만. Tab → 둘 다. **텍스트칸은 마우스 클릭에도 둘 다.**
- **`:invalid` 는 페이지가 뜬 순간 이미 켜져 있다.** 비어 있는 `required` 칸이 그렇다.
- **`:user-invalid` 는 사람이 건드리고 그 칸을 떠난 뒤에만** 켜진다. 타이핑 중에는 안 켜지고, **스크립트로 값만 넣으면 영영 안 켜진다.**
- **`:disabled`·`readonly` 는 `:valid` 도 `:invalid` 도 아니다** — 제약 검증에서 제외된다.
- **`[checked]` 는 초기값, `:checked` 는 지금 상태다.** 사용자가 끄면 속성은 남고 `:checked` 만 꺼진다.
- **LVHA 는 명시도 문제가 아니라 순서 문제다.** 넷 다 `(0,1,1)` 이라 뒤에 쓴 것이 이긴다.
- **`:focus-visible` 과 `:user-invalid` 의 발동 시점은 명세가 UA 에 맡겼다** — 내가 잰 것은 Chrome 151 의 행동이다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 10번) · Baseline 표
- [`../08-basic-selectors-and-combinators/2-summary.md`](../08-basic-selectors-and-combinators/2-summary.md) — **선행.** `[checked]` 같은 속성 선택자와 조합자. **거기는 트리 모양으로 고르는 정적인 그물, 여기는 입력으로 켜지는 그물**
- [`../09-structural-pseudo-classes/2-summary.md`](../09-structural-pseudo-classes/2-summary.md) — 같은 「의사 클래스」이지만 **트리 위치**로 판정하는 쪽. 입력과 무관하다
- [`../01-cascade-and-priority/2-summary.md`](../01-cascade-and-priority/2-summary.md) — **LVHA 가 왜 순서로 갈리는지의 정본**(명시도 동점 → 6단계 등장 순서)
- [`../02-specificity/2-summary.md`](../02-specificity/2-summary.md) — 의사 클래스가 `(A, B, C)` 의 **B 자리**라는 것의 정본
- [`../11-is-where-not/2-summary.md`](../11-is-where-not/2-summary.md) — 상태 선택자 여럿을 `:is()` 로 묶을 때 명시도가 어떻게 되나
- [목록의 **12번 주제**](../12-has-relational-selector/)(`:has()`) — `.field:has(:focus)` 처럼 **자손의 상태를 부모로** 끌어올리는 것
- [목록의 **13번 주제**](../13-pseudo-elements-and-generated-content/)(의사 요소) — `::placeholder` 는 의사 **요소**이고 `:placeholder-shown` 은 의사 **클래스**다
- [목록의 **60번 주제**](../60-prefers-reduced-motion/)(`prefers-reduced-motion`) — 상태 전환에 움직임을 붙일 때의 접근성
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **상태 의사 클래스** — 사용자 입력·폼 상태에 따라 켜졌다 꺼지는 `:` 선택자. 트리 모양과 무관하다.
- **`:hover`** — 포인터가 그 요소(또는 그 자손) 위에 있을 때. 조상에도 같이 걸린다.
- **`:active`** — 버튼을 **누르고 있는 동안**. 떼면 꺼진다.
- **포커스(focus)** — 지금 키보드 입력이 들어갈 요소. `document.activeElement` 하나뿐.
- **`:focus-visible`** — 포커스 표시를 **보여 줘야 한다고 UA 가 판단**했을 때. 판단 기준은 명세가 UA 에 맡겼다.
- **`:focus-within`** — 나 또는 내 자손이 포커스를 가졌을 때. 부모에 건다.
- **제약 검증** — `required`·`type`·`pattern`·`min`/`max` 로 값을 판정하는 HTML 기능.
- **`:valid` / `:invalid`** — 제약 검증 결과. **사용자 조작과 무관하게** 로드 직후부터 켜져 있다.
- **`:user-valid` / `:user-invalid`** — 사용자가 값과 상호작용한 **뒤에만** 켜지는 짝. Chrome 151 에서는 blur 시점.
- **검증에서 제외(barred from constraint validation)** — `:disabled`·`readonly` 인 컨트롤은 `:valid` 도 `:invalid` 도 아니다.
- **`:default`** — 문서에 적힌 초기 선택. 처음부터 `checked` 인 라디오, `selected` 인 `option`, 폼의 첫 제출 버튼.
- **`:read-only`** — 편집 가능하지 않은 모든 요소. `readonly` 속성이 있다는 뜻이 아니다.
- **`:placeholder-shown`** — placeholder 가 실제로 보이고 있을 때(값이 비었을 때).
- **LVHA** — `:link` → `:visited` → `:hover` → `:active` 의 작성 순서. 넷의 명시도가 같아서 순서가 승부를 낸다.

## 더 들어가면

- **`:focus-visible` 의 휴리스틱을 직접 흉내 내지 마라.** 예전에는 `:focus:not(.js-mouse-focus)` 같은 JS 우회가 표준이었다. 지금은 브라우저가 입력 방식·요소 종류·이전 상호작용을 종합해 판단한다 — 내가 재현할 수 있는 규칙이 아니다.
- **`:user-invalid` 이전에 쓰던 패턴**은 `.touched` 클래스를 blur 때 JS 로 붙이는 것이었다. `:user-invalid` 는 그 클래스를 언어 기능으로 흡수한 것이다.
- **`:has(:focus-visible)`** 로 포커스 링을 **부모 카드**에 그리는 형태가 오늘 흔하다. `:focus-within` 은 `:focus` 기준이라 마우스 클릭에도 켜진다 — 둘은 다르다. *(이 문서에서 `:has(:focus-visible)` 은 미실행 — [목록의 **12번 주제**](../12-has-relational-selector/).)*
- **`:indeterminate`** 는 HTML 속성으로는 못 만든다. 실측에서 `element.indeterminate = true` 를 **JS 로 준 뒤에야** 켜졌다. 「부분 선택」 체크박스의 스타일이 이것이다.
- **`:target`** (URL 프래그먼트가 가리키는 요소)도 상태 의사 클래스이지만 사용자 입력이 아니라 **주소**가 스위치다. *(이 문서에서 미실행.)*
