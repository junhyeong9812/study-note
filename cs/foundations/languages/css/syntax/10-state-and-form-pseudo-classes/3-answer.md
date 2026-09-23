# css/syntax/10 — 상태·폼 의사 클래스: `:hover`·`:focus-visible`·`:checked`·`:disabled` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 상태 목록과 모든 색은 Google Chrome 151.0.7922.173 에서 실제로 입력을 넣어 받은 것**이다.\
> ★ 이 주제는 **스크린샷만으로는 검증되지 않는다.** `:hover`·`:active`·`:focus-visible` 은 입력이 있어야 켜진다.\
> 그래서 Chrome 을 `--remote-debugging-port` 로 띄우고 **CDP 로 실제 마우스 이동·버튼 누름·Tab 키·문자 입력을 넣은 뒤** `element.matches(...)` 와 `getComputedStyle` 을 읽었다. 넣은 명령은 아래 **「실행 검증」** 절에 그대로 적었다.\
> 규칙은 [Selectors Level 4](https://drafts.csswg.org/selectors-4/) 로, 지원 상태는 `api.webstatus.dev` 조회(2026-09-23)로 접지했다. **엔진은 Chrome 하나다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 포인터가 만드는 세 상태

**실행 결과** (Chrome 151 + CDP, `<button id="btn">`)

```text
  입력                                        btn 이 맞는 선택자
  ─────────────────────────────────────────  ──────────────────────────
  (아무것도 안 함)                            (없음)
  mouseMoved  (버튼 중심 좌표로)              :hover
  mousePressed (아직 안 뗌)                   :hover :active :focus
  mouseReleased                               :hover :focus
```

**마우스를 위로 옮기기만 했을 때**

- **`:hover`** 하나다. 누를 필요가 없다.

**누른 채 있을 때**

- **`:hover` · `:active` · `:focus`** 셋이다. 포커스는 `mousePressed` 시점에 옮겨간다.

**뗀 직후 목록에서 빠지는 것**

- **`:active`** 다. 누르고 있는 동안만 켜져 있다.

**스크린샷만으로 확인할 수 있는가**

- **없다.** 입력을 안 넣으면 화면은 평소 상태 그대로이고, 「스타일이 안 먹네」로 오진하게 된다.
- **CDP** 로 `Input.dispatchMouseEvent` 를 보내거나, 못 하면 **「미실행」으로 정직하게 적어야** 한다.

### 2. `:focus` 와 `:focus-visible` 이 갈리는 자리 ★

**실행 결과** (Chrome 151 + CDP)

```text
  입력                       btn                              txt
  ────────────────────────  ───────────────────────────────  ───────────────────────────────
  로드 직후                  -                                -
  Tab 1회                    :focus :focus-visible            -
  Tab 2회                    -                                :focus :focus-visible
  마우스 클릭 (버튼)          :focus :hover                    -
  마우스 클릭 (텍스트칸)      -                                :focus :focus-visible :hover
  마우스 클릭 (체크박스)      -                                -    (chk: :checked :hover :focus :enabled)
```

**Tab 키로 버튼에 포커스했을 때**

- **`:focus` 와 `:focus-visible` 둘 다** 맞는다.

**마우스 클릭으로 버튼에 포커스했을 때**

- **`:focus` 는 맞고 `:focus-visible` 은 안 맞는다.** (`:hover` 도 같이 맞는다 — 포인터가 버튼 위에 있으니까.)

**마우스 클릭으로 텍스트 입력칸에 포커스했을 때**

- **둘 다 맞는다.** 버튼과 **답이 다르다.**
- 체크박스는 버튼과 같다 — 마우스 클릭에서 `:focus-visible` 이 안 켜졌다.

**갈리는 기준**

- **이 요소가 곧 키보드 입력을 받는가** 하나다. 텍스트칸은 클릭해서 왔어도 커서 위치를 보여 줘야 하므로 링을 그린다.
- ★ 이 판단은 **명세가 UA 에 맡긴 것**이다. 위 표는 **Chrome 151 한 엔진의 행동**이지 모든 브라우저의 보장이 아니다.

### 3. 포커스 링을 지우는 코드

**무엇을 망가뜨리는가**

- **키보드 사용자의 현재 위치 표시**를 통째로 없앤다. Tab 으로 이동하면 어디에 있는지 화면에 아무 표시가 없다.
- 마우스 클릭의 링이 거슬려서 지우면 **Tab 의 링까지 같이 사라진다** — 둘은 같은 `:focus` 이기 때문이다.

**마우스 클릭의 링만 없애려면**

```css
button:focus         { outline: none; }
button:focus-visible { outline: 3px solid …; }
```

- 실측에서 마우스 클릭은 `:focus-visible` 에 **안 걸렸으므로** 이 두 줄이면 마우스에서는 링이 없고 Tab 에서는 살아난다.
- 이 문서의 첫 `demo` 블록이 정확히 이 형태다.

**`:focus-visible` 이 언제 켜지는지를 누가 정하는가**

- **UA(브라우저)가 정한다.** 명세는 "표시가 필요하다고 UA 가 판단했을 때"라고만 쓴다.

**그러면 이 문서의 실측은 무엇에 대한 근거인가**

- **Chrome 151 이 그 판단을 어떻게 내리는가**에 대한 근거다.
- 「모든 브라우저가 이렇다」는 결론은 이 실측에서 나올 수 없다. **관찰은 관찰로 적는다.**

### 4. `:focus-within` 은 누구에게 거는가

**실행 결과** (Chrome 151 + CDP, `#inner` 를 마우스로 클릭한 상태)

```text
  #wrap:focus-within          ->  1개
  #wrap:has(:focus)           ->  1개
  #wrap:has(:focus-visible)   ->  1개    (#inner 가 텍스트칸이라 클릭에도 focus-visible 이 켜진다)
```

**`#wrap` 은 `:focus-within` 에 맞는가**

- **맞는다.** 자손이 포커스를 가지면 조상도 맞는다.

**`#wrap` 을 `:focus` 로 걸면 같은 효과인가**

- **아니다.** `:focus` 는 **그 요소 자신**이 포커스를 가져야 한다. `#wrap` 은 `div` 라 포커스를 못 받는다(실측에서 `:focus` 목록에 없었다).

**`:focus-within` 과 `:has(:focus)` 의 관계**

- **같은 것을 잡는다** — 실측에서 둘 다 1개였다.
- `:focus-within` 은 `:has()` 가 없던 시절에 이 한 가지 용도로 먼저 들어온 **전용 축약형**이다.

**`:focus-within` 과 `:has(:focus-visible)` 의 차이**

- **기준이 다르다.** 앞엣것은 `:focus` 기준이라 **마우스 클릭에도 켜지고**, 뒤엣것은 `:focus-visible` 기준이다.
- 이 실험에서 둘의 답이 같았던 것은 자손이 **텍스트칸**이라 마우스 클릭에도 `:focus-visible` 이 켜졌기 때문이다. **버튼이었다면 갈린다.**

### 5. 폼이 뜨자마자 무엇이 켜져 있는가

**실행 결과** (Chrome 151, 로드 직후 · 입력 0)

```text
  #txt [text required, 비어 있음]      :required :invalid :placeholder-shown
  #opt [text value="ok"]               :optional :valid
  #dis [text disabled]                 :disabled
  #ro  [text readonly required 값 있음] :enabled :required :read-only
```

**넷은 각각 어떤 의사 클래스에 맞는가**

- 위 출력 그대로다.

**`#dis` 는 `:valid` 인가 `:invalid` 인가**

- **둘 다 아니다.** `:disabled` 인 컨트롤은 **제약 검증에서 제외된다**(barred from constraint validation).
- 그래서 `form:invalid` 도 안 켜진다 — 8번 참고.

**`#ro` 는 어떤가, 그 이유는**

- **역시 둘 다 아니다.** `readonly` 인 컨트롤도 제약 검증에서 제외된다.
- `required` 가 붙어 있는데도 그렇다 — **`:required` 는 맞고 `:invalid` 는 아니다.**

**`:placeholder-shown` 은 어디에 맞는가**

- **`#txt` 하나**다. placeholder 가 있고 값이 비어서 **실제로 보이고 있기** 때문이다.
- `ab` 를 치자 목록에서 빠졌다(6번 참고).

### 6. `:invalid` 와 `:user-invalid` 의 시점 ★

**실행 결과** (Chrome 151 + CDP, `#mail`)

```text
  ① 로드 직후                   :required :invalid :placeholder-shown
  ② 클릭 + "ab" 입력, 포커스 중   :required :invalid
  ③ blur (칸 밖으로)            :required :invalid :user-invalid
  ④ 값을 a@b.co 로 고치고 blur   :required :valid   :user-valid
  ⑤ (새로 로드) element.value='zzz' 만   :required :invalid
```

**로드 직후는 `:invalid` 인가 `:user-invalid` 인가**

- **`:invalid` 다.** `:user-invalid` 는 아니다.
- 사용자는 아직 아무것도 안 했는데 이미 「맞지 않음」 판정이 내려져 있다.

**`ab` 를 치고 아직 그 칸에 있을 때**

- **여전히 `:invalid` 만**이다. `:user-invalid` 는 **아직 안 켜진다.**
- ★ 이것이 중요한 이유 — **타이핑하는 도중에 빨갛게 되지 않는다.**

**칸 밖으로 나온 뒤**

- **`:invalid` 와 `:user-invalid` 둘 다** 맞는다. blur 가 스위치였다.

**스크립트로 값만 넣으면**

- **`:user-invalid` 가 안 켜진다**(⑤). `:invalid` 만 켜진다.
- **사용자 조작이 아니기 때문**이다. 자동 채움·복원 로직을 짠 뒤 당황하는 자리다.
- ★ 「blur 시점」이라는 것도 **명세가 아니라 Chrome 151 의 행동**이다. 명세는 "사용자가 값과 상호작용한 뒤"라고만 쓴다.

### 7. `[checked]` 와 `:checked`

**실행 결과** (Chrome 151 + CDP 로 실제 클릭)

```text
  초기        c1: [checked] O  :checked O      c2: [checked] X  :checked X
  c1 을 끄고
  c2 를 켠 뒤  c1: [checked] O  :checked X      c2: [checked] X  :checked O
```

**넷은 각각 어떻게 되는가**

- 위 출력 그대로다. **속성은 그대로이고 상태만 뒤집혔다.**

**왜 `[checked]` 는 그대로 남는가**

- 속성은 「**문서에 적힌 초기값**」이라 사용자 조작으로 안 바뀐다. 조작은 프로퍼티(상태)를 바꾼다.

**`option[selected]` 와 `option:checked` 도 같은 관계인가**

- **같다.**
- *(Chrome 151 실측: `<option selected>A</option><option>B</option>` 에서 선택을 B 로 옮기니 A 는 `[selected]` 가 여전히 맞고 `:checked` 는 꺼졌으며, B 는 `[selected]` 가 안 맞고 `:checked` 만 켜졌다.)*

**`:default` 는 무엇을 가리키는가**

- **문서에 적힌 초기 선택**이다.
- 실측에서 처음부터 `checked` 인 라디오(`r1`), `selected` 인 `option`(`o1`), 그리고 **폼의 첫 제출 버튼**(`fb`)이 `:default` 였다.

### 8. `:disabled` 는 어디서 오는가

**실행 결과**

```text
  fieldset#fs [disabled]   :disabled :read-only :valid
   ├─ input#fi             :disabled :optional :read-only
   └─ button#fb            :disabled :default :optional :read-only

  form#f1 (required 빈 칸)             -> :invalid  = true
  form#f2 (required 빈 칸 + disabled)  -> :invalid  = false
```

**`#fi` 와 `#fb` 는 `:disabled` 인가**

- **맞다.** 둘 다 `:disabled` 목록에 있다.

**그 둘에 `disabled` 속성이 있는가**

- **없다.** 속성은 `fieldset` 에만 있다. **`:disabled` 는 조상에서 내려온 것**이다.

**`[disabled]` 와 `:disabled` 중 어느 쪽인가**

- **`:disabled`** 다. `[disabled]` 를 쓰면 `fieldset` 으로 한꺼번에 끈 자식들이 **스타일에서 새어 나간다.**

**`:disabled` 인 칸이 `form:invalid` 에 영향을 주는가**

- **안 준다.** 실측에서 같은 빈 `required` 칸이라도 **`disabled` 를 붙인 쪽 폼은 `:invalid` 가 아니었다.**
- 제출 버튼을 `form:invalid` 로 잠그는 패턴에서 **비활성 칸이 검증에서 빠진다**는 것을 모르면 진단이 안 된다.

### 9. `:read-only` 는 무엇을 잡는가

**실행 결과** (로드 직후, 입력 0)

```text
  fieldset#fs   :read-only        라디오 r1/r2   :read-only
  option o1/o2  :read-only        input#pat (편집 가능)  :read-write
```

**`<fieldset>`·라디오·`<option>` 은 `:read-only` 인가**

- **전부 `:read-only` 다.**

**"readonly 속성이 있다"로 읽으면 어디서 틀리는가**

- 바로 위에서 틀린다 — 셋 다 `readonly` 속성이 없는데 맞는다.
- `:read-only` 의 뜻은 「**사용자가 편집할 수 있는 것이 아니다**」이고, 편집 가능한 텍스트 입력이 아닌 것은 전부 여기 들어간다.

**`:read-write` 는 무엇에 맞는가**

- **사용자가 값을 편집할 수 있는 것**이다. 실측에서 일반 텍스트 입력(`#pat`·`#num`)만 맞았다.

**`:required` 는 `<div required>` 에 맞는가**

- **안 맞는다.**
- *(Chrome 151 실측: `<div required>` 를 놓고 `div:required` 를 던지면 0개, 같은 문서의 `input[required]` 는 1개.)*
- `:required` 는 `input`·`select`·`textarea` 에만 붙는다.

### 10. 링크 스타일이 안 먹는다 ★

**실행 결과** (Chrome 151 + CDP, 방문한 적 없는 링크)

```text
  a:link{color:blue}  a:hover{color:red}   평소 rgb(0, 0, 255)   호버 rgb(255, 0, 0)
  a:hover{color:red}  a:link{color:blue}   평소 rgb(0, 0, 255)   호버 rgb(0, 0, 255)
                                                                       ^^^^^^^^^^^^ 안 바뀐다
```

**마우스를 올리면 무슨 색인가**

- 질문의 순서(`a:hover` 가 먼저)에서는 **파랑 그대로**다. 호버 스타일이 통째로 가려진다.

**두 선택자의 명시도**

- **둘 다 `(0, 1, 1)`** 이다 — 타입 1(C) + 의사 클래스 1(B).
- *(Chrome 151 실측으로 고정: `a:hover` 뒤에 `a.zz`(0,1,1) 를 쓰면 `a.zz` 가 이기고(동점 → 순서), 뒤에 `.zz`(0,1,0) 를 쓰면 `a:hover` 가 이긴다.)*

**승부를 정한 것은 몇 단계인가**

- **6단계(등장 순서)** 다. 명시도(5단계)가 동점이라 거기까지 내려갔다.
- 정본은 [01번 주제](../01-cascade-and-priority/2-summary.md).

**고치려면, 그 순서의 이름은**

- **`:hover` 를 `:link` 뒤로 옮긴다.** 표준 순서는 **`:link` → `:visited` → `:hover` → `:active`**, 곧 **LVHA**("LoVe HAte")다.
- ★ 명시도를 올려도 소용없다 — 이것은 **순서 문제**다.

### 11. `:hover` 의 범위

**실행 결과** (Chrome 151 + CDP, `#a1` 중심으로 `mouseMoved`)

```text
  #par:hover   ->  true
  #a1:hover    ->  true
  body:hover   ->  true
```

**`#par` 은 `:hover` 인가**

- **맞다.** 자손 위에 포인터가 있으면 조상도 `:hover` 다.

**`body` 는**

- **역시 맞다.** 뿌리까지 전부 올라간다.

**터치 기기에서 `:hover` 는**

- **사실상 없다.** 손가락은 화면 위에 올려놓고 있을 수가 없다(탭하면 잠깐 켜졌다 꺼지는 정도의 흉내만 낸다). *(터치 기기는 이 머신에 없어 **미실행**이다 — 결론으로 쓰지 않는다.)*

**그래서 `:hover` 에만 담으면 안 되는 것**

- **유일한 조작 경로**(메뉴 열기·삭제 버튼 노출)와 **꼭 읽어야 할 정보**다.
- 호버는 **보조 되먹임**으로만 쓰고, 같은 것을 `:focus-visible` 이나 항상 보이는 형태로도 제공한다.

### 12. 다른 주제와 잇기

**상태 의사 클래스의 명시도 자리와 정본**

- **B 자리**다 — 클래스·속성 선택자와 같은 급이다.
- 정본은 [02번 주제](../02-specificity/2-summary.md). `a:hover` = `(0,1,1)` 도 거기 규칙으로 유도되고, 이 문서 10번에서 실측으로 고정했다.

**`:hover` 와 `:nth-child` 는 무엇이 다른가**

- 둘 다 의사 클래스이지만 **스위치가 다르다.**
  - `:nth-child` — **문서 트리의 모양.** 사용자 입력과 무관하고, 로드 시점에 이미 정해져 있다([09번](../09-structural-pseudo-classes/2-summary.md)).
  - `:hover` — **사용자 입력.** 시간에 따라 켜졌다 꺼진다.
- 그래서 검증 방법도 다르다 — 앞엣것은 스크린샷으로 되고 뒤엣것은 **CDP 입력이 필요하다.**

**`:placeholder-shown` 과 `::placeholder` 의 차이**

- **`:placeholder-shown`** 은 의사 **클래스** — "지금 placeholder 가 보이고 있는 **입력칸**"을 고른다(B 자리).
- **`::placeholder`** 는 의사 **요소** — 그 **placeholder 글자 자체**라는 가상 상자를 고른다(C 자리). 정본은 [목록의 **13번 주제**](../13-pseudo-elements-and-generated-content/)다.

**「사용자가 아직 아무것도 안 했을 때 무엇이 켜져 있나」를 먼저 묻는 이유**

- **이 주제의 사고가 전부 거기서 난다.** `:invalid` 는 로드 직후 이미 켜져 있고, `:focus-visible` 은 아직 안 켜져 있다.
- 「입력이 있어야 켜지는 것」과 「입력 없이 이미 켜져 있는 것」을 갈라 놓지 않으면, 폼은 처음부터 빨갛고 버튼은 클릭할 때마다 테두리가 튄다.

## 용어 풀이

- **상태 의사 클래스** — 사용자 입력·폼 상태로 켜졌다 꺼지는 `:` 선택자. 명시도는 **B 자리**.
- **`:hover` / `:active`** — 포인터가 위에 있을 때 / 버튼을 **누르고 있는 동안**. 둘 다 조상에도 걸린다.
- **포커스** — 지금 키보드 입력이 들어갈 요소. `document.activeElement` 하나뿐.
- **`:focus-visible`** — 포커스 표시를 보여 줘야 한다고 **UA 가 판단**했을 때. 판단 기준은 명세가 UA 에 맡겼다.
- **`:focus-within`** — 나 또는 내 자손이 포커스를 가졌을 때. `:has(:focus)` 의 전용 축약형.
- **제약 검증** — `required`·`type`·`pattern`·`min`/`max` 로 값을 판정하는 HTML 기능.
- **`:valid` / `:invalid`** — 제약 검증 결과. **사용자 조작과 무관하게** 로드 직후부터 켜져 있다.
- **`:user-valid` / `:user-invalid`** — 사용자가 값과 상호작용한 **뒤에만**. Chrome 151 에서는 blur 시점.
- **검증에서 제외(barred from constraint validation)** — `:disabled`·`readonly` 컨트롤은 `:valid` 도 `:invalid` 도 아니고 `form:invalid` 에도 영향을 안 준다.
- **`:default`** — 문서에 적힌 초기 선택(처음부터 `checked` 인 라디오, `selected` 인 `option`, 폼의 첫 제출 버튼).
- **`:read-only`** — 사용자가 편집할 수 있는 것이 **아닌** 모든 요소. `readonly` 속성이 있다는 뜻이 아니다.
- **`:placeholder-shown`** — placeholder 가 실제로 보이고 있을 때. 의사 **클래스**다(`::placeholder` 는 의사 요소).
- **LVHA** — `:link` → `:visited` → `:hover` → `:active` 의 작성 순서. 넷의 명시도가 같아 순서가 승부를 낸다.

## 실행 검증

**환경** — Google Chrome **151.0.7922.173**. 정적 확인은 `--headless --no-sandbox --disable-gpu`, 입력이 필요한 것은 **같은 프로세스에 `--remote-debugging-port` 를 붙여 CDP 로 조작**했다. Firefox 155.0.1 은 이 환경에서 **headless 스크린샷이 산출되지 않아 쓰지 않았다.** WebKit(Safari)은 없다. **이 문서의 모든 값은 Blink 단일 엔진의 관찰이다.**

### CDP 로 입력을 넣은 방법 (다음 배치가 그대로 재사용할 수 있게)

```text
1) 띄우기
   google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
     --force-device-scale-factor=1 --remote-allow-origins=* \
     --remote-debugging-port=9333 --window-size=900,500 about:blank
   http://127.0.0.1:9333/json 에서 type=="page" 인 탭의 webSocketDebuggerUrl 로 붙는다.
   Page.enable / Runtime.enable / DOM.enable 을 먼저 보낸다.

2) 호버 — 요소 중심 좌표를 먼저 구하고 거기로 포인터를 옮긴다
   r = el.getBoundingClientRect(); x = r.left + r.width/2; y = r.top + r.height/2
   Input.dispatchMouseEvent { type:"mouseMoved", x, y, button:"none", buttons:0 }
   호버를 풀 때는 같은 이벤트를 x:1, y:1 로 보낸다.

3) 누른 채 / 클릭
   Input.dispatchMouseEvent { type:"mousePressed",  x, y, button:"left", buttons:1, clickCount:1 }
   (여기서 matches(':active') 를 읽는다)
   Input.dispatchMouseEvent { type:"mouseReleased", x, y, button:"left", buttons:0, clickCount:1 }

4) Tab 으로 포커스 — 한 번의 Tab 은 rawKeyDown + keyUp 두 이벤트다
   Input.dispatchKeyEvent { type:"rawKeyDown", key:"Tab", code:"Tab",
                            windowsVirtualKeyCode:9, nativeVirtualKeyCode:9, modifiers:0 }
   Input.dispatchKeyEvent { type:"keyUp",      key:"Tab", code:"Tab",
                            windowsVirtualKeyCode:9, nativeVirtualKeyCode:9, modifiers:0 }
   ★ 앞선 실험이 포커스를 남겨 두면 Tab 이 예상과 다른 요소로 간다 —
     Page.navigate 로 다시 띄우고 시작하는 편이 안전하다(실제로 한 번 어긋났다).

5) 문자 입력 — 글자마다 rawKeyDown + char + keyUp 셋
   Input.dispatchKeyEvent { type:"rawKeyDown", key:"a", code:"KeyA",
                            windowsVirtualKeyCode:65, nativeVirtualKeyCode:65 }
   Input.dispatchKeyEvent { type:"char", text:"a", ...같은 필드 }
   Input.dispatchKeyEvent { type:"keyUp", ...같은 필드 }
   ★ Runtime.evaluate 로 el.value='...' 를 넣는 것은 "사용자 조작"이 아니다 —
     :user-invalid 가 안 켜진다(정답 6 의 ⑤ 가 그 실측이다).

6) 읽기
   Runtime.evaluate { expression: "el.matches(':focus-visible')", returnByValue: true }
   Runtime.evaluate { expression: "getComputedStyle(el).outlineStyle", returnByValue: true }
   blur 는 Runtime.evaluate 로 el.blur() — 이건 상태를 끄는 것이라 조작 종류를 안 따진다.
```

### 무엇을 몇 번 돌렸나

| 무엇을 | 어떻게 | 몇 번 | 결과가 실린 곳 |
|---|---|---|---|
| `:hover`·`:active`·`:focus` 전이 | CDP 마우스 4단계 + `matches()` 12선택자 | 폼 전체 1회 통과(12장면) | 정답 1 · 2-summary (1) |
| `:focus` ↔ `:focus-visible` | Tab 2회 판 1 + 마우스 클릭 판 2(버튼·텍스트칸, 각각 새 로드) | 3회 | 정답 2 · 2-summary (2) |
| `:focus-within` · `:has(:focus)` | 클릭 후 `querySelectorAll` 3종 | 1회 | 정답 4 |
| 로드 직후 폼 상태 11요소 × 13선택자 | `matches()` 전수 | 1회 | 정답 5 · 8 · 9 · 2-summary (3)(4) |
| `:invalid` → `:user-invalid` 5단계 | CDP 클릭 + 문자 입력 + blur, JS 주입판 별도 | 5장면 | 정답 6 · 2-summary (5) |
| `[checked]` ↔ `:checked` | CDP 클릭 2회 후 속성·프로퍼티·`matches()` | 초기 + 조작 후 | 정답 7 |
| `option[selected]` ↔ `option:checked` | `selectedIndex` 변경 후 대조 | 1회 | 정답 7 |
| `form:invalid` 과 `disabled` | 두 폼 `matches()` | 1회 | 정답 8 |
| `div:required` | `querySelectorAll` | 1회 | 정답 9 |
| LVHA 순서 | 두 판(순서만 바꿔) × 평소·호버 | 4측정 | 정답 10 · 2-summary (6) |
| `a:hover` 명시도 `(0,1,1)` | 동점 경쟁자 / 한 칸 낮은 경쟁자 두 판 | 2회 | 정답 10 |
| `:hover` 조상 전파 | 링크에 호버 후 3요소 `matches()` | 1회 | 정답 11 |
| `demo` 블록 2개 | 래퍼를 씌운 사본에 같은 입력 + `getComputedStyle` + 스크린샷 | 원본 2 + 변형 2 | 2-summary (2)(5) |

### 구현 의존 항목

| 항목 | 왜 | 다시 찍을 것 |
|---|---|---|
| ★ `:focus-visible` 이 언제 켜지나 | **명세가 UA 에 맡긴 휴리스틱.** 크롬 버전이 오르면 바뀔 수 있고, 다른 엔진은 지금도 다를 수 있다 | 정답 2 의 표 전부 |
| ★ `:user-invalid` 가 blur 에서 켜지는 것 | 같은 이유 — 명세는 "상호작용한 뒤"라고만 한다 | 정답 6 의 ②③ |
| `:default` 가 폼의 첫 제출 버튼에 붙는 것 | HTML 명세 보장이지만 "첫 제출 버튼"의 판정은 폼 구조에 달렸다 | 정답 7 |
| `:read-only` 가 `fieldset`·라디오·`option` 에 붙는 것 | HTML 명세 보장 | 다시 찍을 필요 없음 |
| `:disabled`/`readonly` 가 검증에서 제외되는 것 | HTML 명세 보장 | 다시 찍을 필요 없음 |
| LVHA 가 순서로 갈리는 것 | 명시도가 같다는 **명세 보장**에서 나온다 | 다시 찍을 필요 없음 |

**안 돌려 본 것** — **`:visited`**(headless 프로파일에 방문 기록이 없어 켜 볼 수 없었다. 프라이버시 제약으로 쓸 수 있는 속성이 제한된다는 것도 **미실행**이다) · **터치 기기의 `:hover`**(기기 없음) · **`:target`**(주소 프래그먼트가 스위치인 것) · **`:has(:focus-visible)` 과 `:focus-within` 이 버튼에서 갈리는지**(이 문서의 실험은 텍스트칸으로만 했다). 넷 다 이 문서에서 **결론으로 쓰지 않았고 「미실행」으로 표기했다.**
