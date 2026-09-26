# web-api/14 — `dialog`·`popover` 의 스크립트 제어: `showModal()`·`togglePopover()`·최상위 레이어·포커스 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> ★ **배너의 `--window-size=1000,800` 이 이 문서의 전제다.** 좌표 탐침이 뷰포트에 달려 있어 창이 다르면 값이 달라진다.\
> ★★ **A10 의 블록만 창이 다르다** — `--dump-dom` 이 아니라 **CDP 로 진짜 키와 진짜 마우스를 넣었다.** 가벼운 닫기는 합성 이벤트로 안 난다.\
> 규칙은 [HTML Living Standard](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element) 의 `dialog`·[Popover API](https://html.spec.whatwg.org/multipage/popover.html)·[the top layer](https://html.spec.whatwg.org/multipage/interaction.html#the-top-layer) 절과 [Close Watcher API](https://wicg.github.io/close-watcher/) 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 상태를 묻지 시간을 안 재기 때문이다. 다만 **부적용인 창**이 하나 있다.

| 안 흔들리는 칸 | 흔들리는 칸 · 부적용인 칸 |
|---|---|
| `open`·`:modal`·`:popover-open` · `returnValue` · 예외 이름과 문구 · 초기 포커스 · 가벼운 닫기 격자 · 이벤트 순서 | **창 크기를 바꾸면 좌표 탐침 전부** |
| 캡처를 두 판 돌려 **95블록이 한 글자도 같았다** | `rect.width` 의 **234**(성질만 인용한다) |
| — | ★ **부적용** — `getComputedStyle(…, '::backdrop')`(A5) |
| — | **못 본다** — 스크린리더의 낭독 · 실제 픽셀 · 모바일 가상 키보드 |
| — | Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 여는 문 셋 — `open` 하나로는 구분이 안 된다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-dialog.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '22,28p'
이미 열린 것을 또 열면
  모달인데 showModal() 을 또 = 예외 없음
  모달인데 show() 를        = InvalidStateError 「Failed to execute 'show' on 'HTMLDialogElement': The dialog is already open as a modal dialog, and therefore cannot be opened as a non-modal dialog.」
  비모달인데 showModal() 을 = InvalidStateError 「Failed to execute 'showModal' on 'HTMLDialogElement': The dialog is already open as a non-modal dialog, and therefore cannot be opened as a modal dialog.」
  닫힌 것을 close() 하면    = 예외 없음
  open 속성을 직접 쓰면     = open=true · matches(":modal")=false
  ★ open 속성으로 연 것은 최상위 레이어에 안 올라간다 — show() 와도 다르다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-focus.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,22p'
초기 포커스가 어디로 가나 — 전수
무엇을 어떻게 열었나                          document.activeElement
showModal · 포커스 받을 것이 하나도 없다      ★ dialog·popover 자신
showModal · 단추 둘, autofocus 없음           #ㄴ1
show · 단추 둘, autofocus 없음                #ㄴ1
showModal · 둘째 요소에 autofocus             #ㄷ2
showModal · dialog 자신에 autofocus           #ㄹ1
showModal · 첫 단추가 disabled                #ㅁ2
showModal · 첫 요소가 tabindex="-1"           #ㅂ1
showModal · 첫 단추가 display:none            #ㅅ2
showModal · 첫 요소가 tabindex="0"            #ㅇ1
open 속성만 true 로 (열기 메서드를 안 쓴다)   ★ 바깥 #연놈
showPopover · 포커스 받을 것이 없다           ★ 바깥 #연놈
showPopover · 단추 하나, autofocus 없음       ★ 바깥 #연놈
showPopover · 둘째 단추에 autofocus           #팝ㄷ2

★ dialog 는 autofocus 가 없어도 안쪽 첫 포커스 가능 요소로 간다 — show() 도 그렇다.
★ popover 는 autofocus 가 없으면 포커스를 안 옮긴다 — 여기가 dialog 와 갈리는 급소다.
★ disabled·display:none 은 「포커스 가능」에서 빠져 다음 것으로 넘어간다.
★ 그런데 tabindex="-1" 은 안 빠진다 — 탭 순서에서만 빠질 뿐 포커스는 받는다(#ㅂ1 이 그 줄이다).
★ dialog 자신의 autofocus 는 이 판에서 무시됐다 — 안쪽 첫 단추로 갔다(#ㄹ1). 구현 쪽 관찰이다.
★ open 속성만 켜면 포커스가 안 움직인다. 최상위 레이어에도 안 올라간다.
(exit 0)
```

**왜 그런가**

- **세 문의 결과를 한 줄씩 적으면 이렇다.**

  | 문 | `open` | `:modal` | 최상위 레이어 | 포커스 |
  |---|---|---|---|---|
  | `dialog.open = true` | `true` | `false` | 안 올라간다 | **안 움직인다**(위 블록의 `★ 바깥 #연놈`) |
  | `dialog.show()` | `true` | `false` | 안 올라간다 | 안쪽 첫 요소로 |
  | `dialog.showModal()` | `true` | `true` | 올라간다 | 안쪽 첫 요소로 |

- ★★ **`open` 하나만 보면 셋이 구분되지 않는다.** 셋 다 `true` 다. `open` 은 「**열림 표시**」일 뿐이고 **「어떻게 열렸나」를 말하지 않는다.**
- ★★★ **`open` 속성을 직접 쓰면 최상위 레이어에 안 올라간다.** `matches(':modal')` 이 `false` 이고, 포커스도 **바깥에 그대로** 있다. `show()` 와도 다르다 — **속성 토글은 메서드의 축약이 아니다.**
- **「최상위 레이어에 올라갔다」를 아는 법은 `matches(':modal')`·`matches(':popover-open')` 과 좌표 탐침**이다. `getComputedStyle(dialog).zIndex` 는 **셋 다 `1`** 이라 아무것도 안 답한다(A4·A5).
- **명세가 그렇게 정했다** — `open` 속성은 상태를 **반영**만 하고, 최상위 레이어에 올리는 것은 `showModal()`·`showPopover()` 의 **절차**다.

### 2. `show()` 대 `showModal()` — 갈린 칸은 7 중 3

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-dialog.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,14p'
show() 대 showModal() — 같은 dialog, 여는 방법만 다르다
무엇을                            show()                    showModal()
열고 난 뒤 포커스                 안쪽 첫 요소로 간다       안쪽 첫 요소로 간다
dialog.open                       true                      true
matches(":modal")                 false                     true
::backdrop 의 background          rgba(1, 2, 3, 0.5)        rgba(1, 2, 3, 0.5)
배경 input 의 .inert              false                     false
배경 input 에 focus() 하면        옮겨간다                  거절된다
elementFromPoint(4,4)             HTML                      #모달

갈린 칸 = 3 / 7
  ★ show() 도 포커스를 옮긴다 — 「모달만 포커스를 가져간다」가 아니다.
  ★ ::backdrop 의 계산값은 두 쪽이 같다. 최상위 레이어 여부를 그것으로는 못 가른다.
  ★ 배경의 .inert 는 두 쪽 다 false 인데 모달 쪽에서만 focus() 가 거절된다.
(exit 0)
```

**왜 그런가**

- **같은 칸 넷** — `open`·**포커스가 안쪽 첫 요소로 가는 것**·`::backdrop` 계산값·배경의 `.inert`.
- **갈린 칸 셋** — `matches(':modal')` · **배경에 `focus()` 를 던졌을 때** · `elementFromPoint`.
- ★★★ **「모달만 포커스를 가져간다」는 틀렸다.** 두 쪽 다 안쪽 첫 요소로 갔다. 명세가 **`show()` 와 `showModal()` 둘 다에 같은 포커스 절차**를 붙여 놓았기 때문이다. **「비모달이니까 커서는 그대로겠지」가 여기서 깨진다.**
- ★★ **`::backdrop` 의 계산값이 두 쪽에서 같다.** 비모달에는 배경막이 안 그려지는데도 `rgba(1, 2, 3, 0.5)` 가 나온다 — **계산값은 「무엇이 선언됐나」를 말하지 「무엇이 일어나나」를 말하지 않는다**([08번 주제](../08-getcomputedstyle/2-summary.md)의 그 문장 그대로다).
- ★★ **배경 `input` 의 `.inert` 가 두 쪽 다 `false`** 인데 **모달 쪽에서만 `focus()` 가 거절된다.** 「막혀 있다」는 성질이 **어느 프로퍼티에도 안 적혀 있다**(A6).
- **`elementFromPoint(4, 4)` 가 모달 쪽에서 `#모달` 을 준다** — 그 좌표는 dialog 밖인데도 그렇다. **모달이 열리면 배경 전체가 히트 테스트에서 빠진다**(A4 가 같은 것을 다른 좌표로 보인다).

### 3. `returnValue` — `close()` 는 지우지 않는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-dialog.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '16,20p'
returnValue 와 close(값)
  연 직후 returnValue = ""
  close('확인') 뒤    = "확인" · open = false · 포커스는 #뒤단추 로 돌아온다
  인자 없이 close() 뒤 = "확인"  <- 지우지 않는다. 옛 값이 남는다
  직접 대입할 수도 있다 = "내가 직접"
(exit 0)
```

**왜 그런가**

- **열자마자 `returnValue` 는 빈 문자열**이다.
- **`close('확인')` 이 그 문자열을 `returnValue` 에 넣고 `open` 을 `false` 로 만든다.**
- ★★ **인자 없이 `close()` 를 부르면 옛 값(`"확인"`)이 그대로 남는다.** **지우지 않는다** — 명세가 「인자가 있으면 그것으로 설정한다」까지만 정했기 때문이다.
- ★ **그래서 한 dialog 를 여러 번 쓰면 지난번 답이 남아 있다.** `close()` 로 닫힌 것을 「취소」로 읽는 코드는 **두 번째부터 틀린다.** 열 때 `dialog.returnValue = ''` 로 **직접 비워 두는 것**이 처방이다(그 프로퍼티는 평범한 문자열이라 대입이 된다).
- **닫으면 포커스가 열기 전 자리(`#뒤단추`)로 돌아온다** — 그 규칙의 전수는 A8 이다.

### 4. `z-index` 를 최댓값으로 줘도 진다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-layer.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,12p'
최상위 레이어는 z-index 와 무관하다 — 좌표로 던져 본다
무엇을                                  getComputedStyle().zIndex elementFromPoint 가 주는 것
열기 전 — 팝오버 자리 (140, 80)        1                         #맨위
팝오버를 연 뒤 — 같은 자리             1                         #팝
  그때 #맨위 의 zIndex                  2147483647                같은 자리를 #맨위 가 덮고 있는데도
모달을 연 뒤 — 모달 자리 (140, 200)    1                         #창단추
모달을 연 뒤 — 팝오버 자리 (140, 80)   1                         #창
모달을 연 뒤 — 빈 자리 (600, 400)      —                        #창

★ z-index 가 2147483647 인 #맨위 가 z-index 1 짜리에게 전부 졌다.
★ 계산값은 한 글자도 안 바뀐다 — 「최상위 레이어에 올라갔다」는 계산값에 자국을 안 남긴다.
★ 모달이 열리면 팝오버 자리까지 모달이 먹는다 — 배경 전체가 히트 테스트에서 빠진다.
(exit 0)
```

**왜 그런가**

- ★★★ **`z-index: 2147483647` 인 `#맨위` 가 `z-index: 1` 짜리에게 전부 졌다.** 팝오버를 열자 같은 좌표 `(140, 80)` 이 `#팝` 을 돌려준다.
- ★★ **`z-index` 와 최상위 레이어는 같은 축이 아니다.** 같은 판에서 앞뒤를 다투는 것이 아니라 **판이 하나 더 있는 것**이다. 쌓임 맥락 안에서 아무리 값을 올려도 **그 판을 넘지 못한다**(쌓임 맥락 자체의 정본은 [CSS 22번 주제](../../languages/css/syntax/22-stacking-context-and-z-index/2-summary.md)다).
- ★★ **계산값에서는 아무것도 안 바뀐다.** `#팝` 의 `zIndex` 는 열기 전에도 뒤에도 `1` 이다 — **「최상위 레이어에 올라갔다」는 계산값에 자국을 안 남긴다.**
- **모달을 연 뒤에는 빈 자리 `(600, 400)` 도 `#창`** 이다. 배경 전체가 히트 테스트에서 빠지므로 **어느 좌표를 물어도 모달이 나온다** — 「배경의 어디를 눌렀나」를 `elementFromPoint` 로는 못 푼다(A10 의 ⑪ 이 그 실무 결과다).
- **그래서 이 표면을 쓰는 것이 이득이다** — 조상의 `transform`·`overflow: hidden` 에 안 잘린다. (**이 문서는 잘리지 않는 것을 픽셀로 확인하지 않았다** — 좌표 탐침까지만 던졌다.)

### 5. 「무대 위인가」를 묻는 여섯 창 — 둘은 부적용이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-layer.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,25p'
그럼 「최상위 레이어에 있나」를 무엇으로 보나
창                                열기 전                 연 뒤
창.matches(":modal")              false                   true
창.open                           false                   true
::backdrop 의 background          rgba(1, 2, 3, 0.5)      rgba(1, 2, 3, 0.5)
창.checkVisibility()              false                   true
창.getBoundingClientRect().width  0                       234
팝.matches(":popover-open")       false                   true
팝의 zIndex 계산값                1                       1

★ ::backdrop 의 계산값은 열기 전에도 같다 — 이 창으로는 못 가른다(제5의 상태).
★ 갈리는 것은 :modal·:popover-open 과 좌표(rect·elementFromPoint) 다.
(exit 0)
```

**왜 그런가**

- **답하는 창 넷** — `matches(':modal')`·`matches(':popover-open')`·`checkVisibility()`·`getBoundingClientRect()`.
- **답 못 하는 창 둘** — `getComputedStyle(…, '::backdrop')` 과 `getComputedStyle(el).zIndex`. **열기 전과 연 뒤가 한 글자도 같다.**
- ★★★ **이것은 「재 봤더니 같았다」가 아니라 「잴 것이 없다」다.** `::backdrop` 의 계산값은 **선언한 값을 그대로 돌려줄 뿐**이고, 그 막이 **지금 그려지고 있는지는 한 번도 묻지 않는다.** 세 창(규칙이 담겼나·선택자가 잡았나·계산값이 나오나)이 전부 정상인데 **기준이 다른** 자리다.
- ★ **그 구분 자체가 결론이다** — 「`::backdrop` 으로 모달 여부를 알 수 있다」는 그럴듯한데 **원리상 거짓**이고, 값이 그럴듯해서 안 걸린다.
- ★ **`rect.width` 는 「성질로만」 근거가 된다.** `0` 에서 `234` 로 바뀌는데, **대조할 것은 `234` 라는 숫자가 아니라 「0 이 아니게 된다」는 성질**이다(글꼴·기본 여백에 달린 값이다).
- **`checkVisibility()` 가 쓸 만한 이유** — 닫힌 dialog 는 `display: none` 이라 `false` 이고 열면 `true` 다. 다만 **모달인지 비모달인지는 구분 못 한다.**

### 6. 배경이 막혔다는 것 — 답하는 프로퍼티가 없다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-layer.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '27,39p'
배경이 막힌 것을 무엇으로 보나 — 모달이 열린 상태
  배경입력.inert (IDL)         = false
  배경입력.matches("[inert]")  = false
  배경입력.checkVisibility()   = true
  배경입력.focus() 뒤 activeElement = #창단추  <- 거절됐다
  배경단추.click() (스크립트) → 배경 단추가 눌렸다
  ★ 막히는 것은 사용자 입력과 포커스다. 스크립트로 부른 click 은 그대로 통과한다.

진짜 inert 속성과 견주면
  막힘.inert = true · 막힌단추.inert = false  <- 자손은 false 로 답한다
  막힌단추.focus() 뒤 activeElement = #창단추
  ★ .inert 는 「그 요소에 속성이 붙었나」만 답한다 — 「지금 막혀 있나」를 묻는 창이 아니다.
  ★ 「막혀 있나」를 묻는 방법은 focus() 를 던져 보는 것뿐이다(이 문서의 창 ④).
(exit 0)
```

**왜 그런가**

- ★★★ **「지금 막혀 있나」를 답하는 프로퍼티가 없다.** `inert` 도 `matches('[inert]')` 도 `false` 이고 `checkVisibility()` 는 `true` 다.
- ★★ **그래서 같은 질문을 다른 창으로 물었다** — **`focus()` 를 던져 보고 `document.activeElement` 를 되읽는 것.** 그것만이 「거절됐다」를 말한다. 이것이 이 주제의 창 ④ 가 하는 일이다.
- ★★ **막는 것과 안 막는 것이 갈린다.**

  | 막는다 | 안 막는다 |
  |---|---|
  | 사용자의 클릭·탭 이동 | **`el.click()`**(스크립트 호출) |
  | `el.focus()` | `el.dispatchEvent(...)` |
  | 히트 테스트 | 프로퍼티 읽기·쓰기 전부 |

- ★ **「모달을 띄웠으니 뒤는 안전하다」는 스크립트에 대해서는 거짓**이다. 실측에서 `배경단추.click()` 의 리스너가 **그대로 불렸다.** 진짜로 잠그려면 **상태 플래그로 스크립트 쪽도 막아야 한다.**
- ★ **진짜 `inert` 속성도 자손에게 `false` 로 답한다** — `막힘.inert` 가 `true` 인데 그 안의 `막힌단추.inert` 는 `false` 다. **`.inert` 는 「그 요소에 속성이 붙었나」를 반영하는 IDL 프로퍼티**이지 **「이 요소가 지금 비활성인가」를 계산해 주는 값이 아니다**([06번 주제](../06-attribute-vs-property/2-summary.md)의 반영 규칙 그대로다).

### 7. 초기 포커스 전수 — `popover` 만 안 옮긴다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-focus.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,22p'
초기 포커스가 어디로 가나 — 전수
무엇을 어떻게 열었나                          document.activeElement
showModal · 포커스 받을 것이 하나도 없다      ★ dialog·popover 자신
showModal · 단추 둘, autofocus 없음           #ㄴ1
show · 단추 둘, autofocus 없음                #ㄴ1
showModal · 둘째 요소에 autofocus             #ㄷ2
showModal · dialog 자신에 autofocus           #ㄹ1
showModal · 첫 단추가 disabled                #ㅁ2
showModal · 첫 요소가 tabindex="-1"           #ㅂ1
showModal · 첫 단추가 display:none            #ㅅ2
showModal · 첫 요소가 tabindex="0"            #ㅇ1
open 속성만 true 로 (열기 메서드를 안 쓴다)   ★ 바깥 #연놈
showPopover · 포커스 받을 것이 없다           ★ 바깥 #연놈
showPopover · 단추 하나, autofocus 없음       ★ 바깥 #연놈
showPopover · 둘째 단추에 autofocus           #팝ㄷ2

★ dialog 는 autofocus 가 없어도 안쪽 첫 포커스 가능 요소로 간다 — show() 도 그렇다.
★ popover 는 autofocus 가 없으면 포커스를 안 옮긴다 — 여기가 dialog 와 갈리는 급소다.
★ disabled·display:none 은 「포커스 가능」에서 빠져 다음 것으로 넘어간다.
★ 그런데 tabindex="-1" 은 안 빠진다 — 탭 순서에서만 빠질 뿐 포커스는 받는다(#ㅂ1 이 그 줄이다).
★ dialog 자신의 autofocus 는 이 판에서 무시됐다 — 안쪽 첫 단추로 갔다(#ㄹ1). 구현 쪽 관찰이다.
★ open 속성만 켜면 포커스가 안 움직인다. 최상위 레이어에도 안 올라간다.
(exit 0)
```

**왜 그런가**

- **물어본 대로 적으면 이렇다.**

  | 무엇을 열었나 | `document.activeElement` |
  |---|---|
  | `ㄱ` — 포커스 받을 것이 없다 | **dialog 자신** |
  | `ㄴ` — 단추 둘, `autofocus` 없음 | 첫 단추 |
  | `ㄷ` — 둘째에 `autofocus` | **둘째**(`autofocus` 가 이긴다) |
  | `ㅁ` — 첫 단추가 `disabled` | **둘째**(`disabled` 는 빠진다) |
  | `ㅂ` — 첫 요소가 `tabindex="-1"` | **그 요소**(★ 안 빠진다) |
  | `팝ㄴ` — 팝오버, `autofocus` 없음 | ★★ **바깥 그대로** |

- ★★★ **`dialog` 와 `popover` 가 갈리는 칸이 여기다.** `dialog` 는 `autofocus` 가 없어도 **안쪽 첫 포커스 가능 요소로** 가고, **`popover` 는 `autofocus` 가 없으면 아예 안 옮긴다.** 팝오버는 「떠 있는 레이어」이지 「대화 상자」가 아니라서 명세가 포커스 절차를 안 붙였다.
- ★ **`tabindex="-1"` 은 「포커스 가능」에서 안 빠진다.** 탭 **순서**에서만 빠질 뿐 `focus()` 는 받는다 — `#ㅂ1` 이 그 줄이다. `disabled`·`display: none` 은 빠진다.
- ★ **`dialog` 자신에 붙인 `autofocus` 는 이 판에서 무시됐다**(안쪽 첫 단추로 갔다). **Chrome 151 의 관찰이지 명세 보장이 아니다** — 명세로는 dialog 자신이 받아야 한다.
- **`show()` 도 같은 흐름을 탄다** — A2 의 결론과 같은 줄이다.
- **실무 결론** — **팝오버 안에 입력이 있으면 `autofocus` 를 직접 달아라.** 안 달면 커서가 방아쇠 단추에 그대로 있어서 **키보드 사용자가 팝오버 안으로 못 들어간다.**

### 8. 닫으면 포커스가 돌아오나 — 자리가 사라지면 안 돌아온다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-focus.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '24,28p'
닫으면 포커스가 어디로 돌아오나
  열기 전 포커스 = #연놈 · 연 뒤 = #ㄴ1
  닫은 뒤        = #연놈  <- 열기 전 자리로 돌아온다
  안에서 포커스를 옮겨 두고 닫아도 = #연놈
  돌아갈 자리가 사라졌으면       = #ㄴ1
(exit 0)
```

**왜 그런가**

- **① 보통은 열기 전 자리로 돌아온다**(`#연놈`).
- **② 안에서 포커스를 옮겨 둬도 그대로 돌아온다** — 브라우저가 **열 때 기억해 둔 자리**로 되돌리기 때문이다. 「마지막으로 포커스가 있던 데」가 아니다.
- ★★ **③ 돌아갈 자리를 지우면 안 돌아온다.** 그 단추를 `remove()` 한 뒤 닫았더니 **`#ㄴ1`**(이미 닫힌 dialog 안의 단추)에 포커스가 남았다.
- ★ **③ 이 실무의 모양이다** — **「이 항목을 지울까요」 모달**이 정확히 이 꼴이다. 확인을 누르면 목록에서 그 행이 사라지고, **그 행 안에 있던 방아쇠 버튼도 같이 사라진다.** 닫은 뒤 포커스가 **허공에 남아** 스크린리더 사용자가 길을 잃는다.
- **처방** — 지우는 모달은 **닫기 전에 돌아갈 자리를 정해 두고** 닫은 뒤 `focus()` 를 직접 부른다. (**이 문서는 그 처방을 던져 보지 않았다** — 증상까지만 관측했다.)

### 9. `popover` 의 표면 — 예외를 던지는 자리는 하나뿐이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-popover.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
표면 — 속성과 메서드
무엇을                                    값
$("오토").popover                         "auto"
$("힌트").popover                         "hint"
popover="zzznope" 의 .popover             "manual"   <- 모르는 값은 manual 로 떨어진다
popover="" 의 .popover                    "auto"   <- 빈 값은 auto 다
popover 속성이 없는 div 의 .popover       null
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-popover.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,17p'
여닫기 — 돌려주는 값과 예외
  showPopover()                  = 예외 없음 · 돌려준 값 = undefined · 열림=true
  이미 열린 것에 또 showPopover() = 예외 없음 · 돌려준 값 = undefined · 열림=true
  togglePopover()                = 예외 없음 · 돌려준 값 = false · 열림=false
  닫힌 것에 hidePopover()        = 예외 없음 · 돌려준 값 = undefined · 열림=false
  togglePopover(true)            = 예외 없음 · 돌려준 값 = true · 열림=true
  togglePopover(true) 를 또       = 예외 없음 · 돌려준 값 = true · 열림=true
  popover 속성이 없는 div 에 showPopover() = NotSupportedError 「Failed to execute 'showPopover' on 'HTMLElement': Not supported on elements that are not popovers.」
  ★ 예외를 던지는 것은 「팝오버가 아닌 요소에 부른 것」 하나뿐이다. 나머지는 전부 조용하다.
(exit 0)
```

**왜 그런가**

- **속성 값** — `popover="auto"` → `"auto"`, **모르는 값 → `"manual"`**, **빈 값 → `"auto"`**, 속성이 없으면 `null`.
- **메서드가 돌려주는 값** — `showPopover()`·`hidePopover()` 는 `undefined`, **`togglePopover()` 계열은 「지금 열려 있나」를 불리언으로** 돌려준다.
- ★ **`togglePopover(true)` 는 토글이 아니라 강제**다 — 「열어 둬라」이고, 두 번 불러도 열린 채다.
- ★★ **예외를 던지는 자리는 하나뿐**이다 — **팝오버가 아닌 요소에 부른 것**(`NotSupportedError`). 이미 열린 것에 또 `showPopover()`, 닫힌 것에 `hidePopover()` 는 **전부 조용하다.** 그래서 **「열려 있나」를 미리 물을 필요가 거의 없다.**
- ★★★ **오타의 증상이 고약하다.** `popover="atuo"` 라고 쓰면 **`manual` 로 떨어진다** — 화면에는 정상으로 뜨는데 **바깥을 눌러도 `Esc` 를 눌러도 안 닫힌다.** 「안 열린다」면 금방 알아채는데 **「안 닫힌다」는 한참 뒤에 발견된다.** 열거값이 조용히 기본값으로 떨어지는 이 모양의 정본은 [06번 주제](../06-attribute-vs-property/2-summary.md)다.
- **진단은 `el.popover` 를 되읽는 것** 한 줄이다.

### 10. 가벼운 닫기 전수 — 진짜 입력으로만 난다

**출력** — ★ 이 셋만 **CDP 로 진짜 키와 진짜 마우스를 넣은** 것이다.

```text
$ python3 wa12b-cdp.py wa12b-14-dismiss.html | sed -n '1,21p'
① 네 가지 팝오버를 모두 연다
   오토=true 안쪽=true 매뉴얼=true 힌트=true
② 중첩된 안쪽 팝오버 위 (120, 80) 를 진짜로 클릭
   오토=true 안쪽=true 매뉴얼=true 힌트=false
③ 바깥 auto 팝오버의 빈 자리 (280, 200) 를 진짜로 클릭
   오토=true 안쪽=false 매뉴얼=true 힌트=false
④ 팝오버 바깥 빈 터 (700, 600) 를 진짜로 클릭
   오토=false 안쪽=false 매뉴얼=true 힌트=false
⑤ auto 둘을 다시 연다
   오토=true 안쪽=true 매뉴얼=true 힌트=false
⑥ Esc 한 번
   오토=true 안쪽=false 매뉴얼=true 힌트=false
⑦ Esc 한 번 더
   오토=false 안쪽=false 매뉴얼=true 힌트=false
⑧ Esc 를 또 (manual 만 남아 있다)
   오토=false 안쪽=false 매뉴얼=true 힌트=false

⑨ 닫기를 beforetoggle 로 막아 본다
   못막음 열림=true
     [못막음 닫기 beforetoggle · cancelable=false -> preventDefault 를 부른다]
   Esc 뒤 못막음 열림=false
(exit 0)
```

```text
$ python3 wa12b-cdp.py wa12b-14-dismiss.html | sed -n '23,35p'
⑩ 모달 dialog 를 연다
   open=true · activeElement=모달단추
⑪ 배경 (700, 600) 을 진짜로 클릭
   open=true · activeElement=모달
     [모달 cancel · cancelable=true]
     [모달 close · returnValue=""]
⑫ Esc
   open=false · activeElement=BODY

⑬ show() 로 연 비모달에 Esc
   open=true
   Esc 뒤 open=true
     [비모달 close]
(exit 0)
```

```text
$ python3 wa12b-cdp.py wa12b-14-dismiss.html | sed -n '37,50p'
⑭ cancel 을 preventDefault 로 막는 모달 — 앞의 모달이 활성화를 이미 써 버린 뒤
   open=true · navigator.userActivation.isActive=true
     [버팀 cancel · cancelable=false -> preventDefault 를 부른다]
     [버팀 close]
   Esc 뒤 open=false

⑮ 같은 모달 — 새로 진짜 클릭을 하고 그 활성화 위에서 연다
   클릭 뒤 isActive=true
   open=true
     [버팀 cancel · cancelable=true -> preventDefault 를 부른다]
   Esc 한 번 뒤 open=true
     [버팀 cancel · cancelable=false -> preventDefault 를 부른다]
     [버팀 close]
   Esc 두 번째 뒤 open=false
(exit 0)
```

**왜 그런가**

- **일곱 경우를 표로 적으면 이렇다.**

  | 무엇을 했나 | 무엇이 닫히나 |
  |---|---|
  | ① 중첩된 안쪽 팝오버 **안**을 클릭 | `hint` 만. `auto` 둘은 남는다 |
  | ② 바깥 팝오버의 **빈 자리**를 클릭 | **안쪽 `auto` 만**(한 겹) |
  | ③ 완전히 바깥을 클릭 | `auto` 전부. `manual` 은 남는다 |
  | ④ `Esc` 한 번 · 두 번 · 세 번 | **안쪽부터 한 겹씩.** `manual` 은 끝까지 남는다 |
  | ⑤ 모달의 배경을 클릭 | ★ **아무것도 안 닫힌다** |
  | ⑥ 모달에 `Esc` | `cancel` 다음 `close`. `returnValue` 는 빈 문자열 |
  | ⑦ `show()` 로 연 비모달에 `Esc` | ★ **안 닫힌다** |

- ★★★ **`dispatchEvent` 로 만든 클릭·키로는 한 칸도 안 움직인다.** 명세가 **신뢰된 이벤트**(trusted event)만 사용자 상호작용으로 치기 때문이다. **그래서 이 절만 창을 바꿔 CDP 로 던졌다** — 안 그랬으면 「가벼운 닫기가 안 된다」로 잘못 결론 낼 뻔했다.
- ★★ **클릭은 「조상 사슬」로 판정한다.** 클릭 지점의 조상에 그 팝오버가 있으면 살고, 없으면 닫힌다. 그래서 **바깥 팝오버의 빈 자리를 누르면 안쪽만** 닫힌다.
- ★ **`hint` 는 독립이 아니다** — 다른 팝오버 **안**을 눌러도 물러난다. 툴팁이라 그렇다.
- ★★ **모달 dialog 는 배경 클릭으로 안 닫힌다.** 다만 **포커스는 dialog 자신으로 옮겨 간다** — 「아무 일도 안 일어난다」가 아니다. 「바깥을 누르면 닫히는 모달」은 **직접 붙여야 하는 기능**이다.
- ★★ **`show()` 로 연 비모달은 `Esc` 로 안 닫힌다.** 닫기 감시자가 **모달에만** 붙는다. (블록의 `[비모달 close]` 줄은 **그 다음 단계에서 스크립트가 부른 `close()`** 가 낸 것이다. `Esc` 가 낸 것이 아니다 — 미뤄진 이벤트 로그가 다음 단계 줄보다 먼저 도착해서 그렇게 보인다.)
- ★★★ **닫는 쪽 `beforetoggle` 은 `cancelable=false` 라 못 막는다**(⑨). 팝오버는 **「닫히지 않겠다」를 선언할 수 없다.**
- ★★★ **`cancel` 로 `Esc` 를 막는 것은 한 번만 된다**(⑮). **새로 진짜 클릭을 한 뒤** 연 모달의 `cancel` 은 `cancelable=true` 로 와서 **막혔고**, **그 다음 `Esc` 는 `cancelable=false`** 로 와서 **강제로 닫혔다.** 닫기 감시자가 **사용자 활성화 하나당 한 그룹**을 갖고 그 그룹이 소진되면 못 막는다 — **「닫히지 않는 모달」로 사용자를 가두지 못하게 한 장치**다.
- ★ **`navigator.userActivation.isActive` 로는 이 판정을 대신 못 한다** — ⑭ 에서도 `true` 였는데 `cancelable` 은 `false` 였다. **읽어서 알 수 있는 값이 아니라 던져 봐야 아는 것**이다.

### 11. `beforetoggle` 과 `toggle` — 하나는 그 자리, 하나는 나중

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-popover.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '29,32p'
beforetoggle 을 막으면
  showPopover() 뒤 열렸나 = false
  이번 tick 의 사건       = ["막는것 beforetoggle closed->open (cancelable=true)"]
  ★ 여는 쪽 beforetoggle 만 cancelable 이다. 닫는 쪽은 못 막는다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-popover.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '34,39p'
beforetoggle 은 동기, toggle 은 나중이다
  showPopover() 직후 (같은 tick) = ["beforetoggle closed->open"]
  닫았다 다시 연 직후            = ["beforetoggle closed->open","beforetoggle open->closed","beforetoggle closed->open"]
  한 tick 뒤                     = ["beforetoggle closed->open","beforetoggle open->closed","beforetoggle closed->open","toggle closed->open"]
  ★ beforetoggle 은 그 자리에서 세 번 다 왔는데 toggle 은 한 번만, 그것도 나중에 왔다.
  ★ toggle 은 「그 tick 이 끝났을 때의 상태」를 한 번 알린다 — 중간 상태를 놓친다.
(exit 0)
```

**왜 그런가**

- **같은 tick 안에서 열고·닫고·다시 열면 `beforetoggle` 은 세 번, `toggle` 은 한 번** 온다. 그것도 **`closed->open`** 하나뿐이다.
- ★★ **`toggle` 은 「그 tick 이 끝났을 때의 상태」를 알린다** — 명세가 「**토글 이벤트 태스크를 큐에 넣는다**」로 정했고, 이미 큐에 있으면 **새로 넣지 않고 최종 상태만 바꾼다.** 그래서 **중간 상태가 합쳐진다.**
- ★ **여닫기 횟수를 세려면 `beforetoggle`** 이다. `toggle` 로 세면 **수가 안 맞는다.**
- **`toggle` 이 알려 주는 것은 「지금 어떤가」** 이지 「무슨 일이 있었나」가 아니다. 애니메이션을 거는 자리에는 이쪽이 맞고, 로그를 남기는 자리에는 앞엣것이 맞다.
- ★★ **여는 쪽 `beforetoggle` 만 `cancelable: true` 다.** `preventDefault()` 로 **열기는 막을 수 있고 닫기는 못 막는다**(A10 의 ⑨). 막으면 **`toggle` 도 안 온다** — 상태가 안 바뀌었으니 알릴 것이 없다.

### 12. 다른 주제와 잇기

**출력** — 이 답의 근거는 앞의 블록들과 선행 주제들이다. 새 출력은 없다.

**왜 그런가**

- **HTML 갈래 47번·48번 과의 경계선** — 그쪽은 「**마크업으로 무엇을 선언하나**」(`open` 속성·`::backdrop` 선언·`popovertarget`·`method="dialog"`)이고, 여기는 「**스크립트가 그것을 어떻게 열고 닫고, 그때 포커스와 최상위 레이어가 어떻게 움직이나**」다. 같은 요소를 다루지만 **묻는 것이 다르다** — 그쪽은 「무엇을 쓰나」, 여기는 「무엇이 일어나나」.
- **[CSS 22번 주제](../../languages/css/syntax/22-stacking-context-and-z-index/2-summary.md)와의 관계** — **`z-index` 와 최상위 레이어는 겹치는 축이 아니다.** 쌓임 맥락 안에서 아무리 값을 올려도 **최상위 레이어를 못 넘는다**(A4 가 `2147483647` 대 `1` 로 그것을 보인다). 그쪽은 「**객석 안의 앞뒤**」, 여기는 「**객석 밖에 판이 하나 더 있다**」.
- **[08번 주제](../08-getcomputedstyle/2-summary.md)의 되풀이** — 「**계산값은 무엇이 선언됐나를 말하지 무엇이 일어나나를 말하지 않는다**」가 이 주제에서 **두 번** 나온다. `::backdrop` 의 배경색(A5)과 `zIndex`(A4)다. 둘 다 **값이 그럴듯해서 안 걸린다.**
- **[06번 주제](../06-attribute-vs-property/2-summary.md)의 되풀이** — **`popover` 의 모르는 값이 조용히 `manual` 로 떨어지는 것**(A9)이 그 주제의 「열거값은 조용히 버려진다」와 같은 모양이다. 그리고 **`.inert` 가 자손에게 `false` 로 답하는 것**(A6)은 그 주제의 **IDL 반영 규칙** 그대로다.
- ★ **이 주제의 조용한 실패를 모으면 넷이다** — `open` 속성 토글이 아무 일도 안 하는 것 · `::backdrop` 계산값이 거짓말하는 것 · `popover` 오타가 `manual` 로 떨어지는 것 · 닫는 `beforetoggle` 의 `preventDefault()` 가 무시되는 것. **전부 예외도 경고도 없다.**

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · **`--window-size=1000,800`**. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

★ **창 크기를 배너에 박은 이유** — `elementFromPoint(x, y)` 와 `getBoundingClientRect()` 가 뷰포트에 달렸다. 배너대로 던져야 같은 글자가 나온다.\
★ **시간은 재지 않았다.** 이 주제에 성능 주장은 하나도 없다.\
★ **못 본 것** — 스크린리더가 이 모달을 **뭐라고 읽는지**(접근성 트리는 보조 기술의 **입력**이지 출력이 아니다) · `::backdrop` 이 실제로 칠해진 **픽셀** · 모바일 **가상 키보드** · 포커스 링의 생김새.

**하네스** — 01\~13 과 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다. **다만 A10 만 다른 하네스**다.

```bash
# wa12b-14-rerun.sh
# --dump-dom 블록을 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 \
  --dump-dom wa12b-14-layer.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'

# A10 블록을 다시 던지는 법 (진짜 입력 — CDP)
python3 wa12b-cdp.py wa12b-14-dismiss.html
```

★ **A10 의 하네스가 하는 일** — 원격 디버깅 포트를 연 headless Chrome 에 websocket 으로 붙어, 페이지가 `window.__단계` 에 적어 둔 대로 **`Input.dispatchKeyEvent`(진짜 `Esc`)** 와 **`Input.dispatchMouseEvent`(진짜 클릭)** 를 넣고 `window.__결과()` 를 읽는다. 전문은 [2-summary.md](2-summary.md)의 (12)에 실려 있다.

```js
// wa12b-14-probe.js
// 이 주제의 창 ④ — 좌표로 '무대 위인가' 를 묻는다
document.elementFromPoint(x, y);         // 모달이 열리면 어느 좌표든 모달을 준다
el.getBoundingClientRect().width;        // 닫혀 있으면 0

// 이 주제의 창 ⑤ 가 없으면 못 보는 것 — 합성 이벤트로는 아무것도 안 닫힌다
document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));  // 아무 일 없음

// '막혀 있나' 를 묻는 유일한 법 — 던져 보고 되읽는다
el.focus();  document.activeElement === el;

// 한글 칸 정렬은 JS 안에서 2폭 padw 로 한다. padEnd 는 UTF-16 단위라 어긋난다.
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).\
★ **`--dump-dom` 은 `load` 뒤의 `setTimeout(…, 0)` 을 한 겹까지만 기다린다**(직접 확인했다). 그래서 **미뤄지는 이벤트를 보는 절은 한 겹 안에서 끝내도록** 짰고, **dialog 의 `close`/`cancel` 은 그 한 겹 안에 안 들어와** A10 의 CDP 쪽으로 옮겼다.\
★ **출력은 `<pre>` 가 아니라 `<script type="text/plain">` 에 담아 마커로 잘랐다.**

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `show()` 대 `showModal()` 7칸 격자 | 2 | 동작 방식 (1) · A2 |
| `returnValue` 4단계 | 2 | 동작 방식 (2) · A3 |
| 모드가 어긋난 재호출 5종 + `open` 속성 | 2 | 동작 방식 (3) · A1·A3 |
| **창 ④** — 좌표 탐침 6지점 | 2 | 동작 방식 (4) · A4 |
| 「무대 위인가」 6창 × 열기 전·뒤 | 2 | 동작 방식 (5) · A5 |
| 「막혀 있나」 7줄 + 진짜 `inert` 대조 | 2 | 동작 방식 (6) · A6 |
| **초기 포커스 전수** 13판 | 2 | 동작 방식 (7) · A1·A7 |
| 닫은 뒤 포커스 3판 | 2 | 동작 방식 (8) · A8 |
| `popover` 속성 5종 + 메서드 7호출 | 2 | 동작 방식 (9) · A9 |
| `auto`/`manual`/`hint` 밀어내기 + DOM 중첩 | 2 | 동작 방식 (10) |
| `beforetoggle` 막기 + `toggle` 타이밍 | 2 | 동작 방식 (11) · A11 |
| **창 ⑤** — 진짜 입력 15단계(CDP) | 2 | 동작 방식 (12) · A10 |

- **두 판 사이에 한 글자도 안 달라졌다**(재대조: 블록 95개 · 동일 95 · 흔들린 칸 0 · 고칠 것 0).

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| **모든 좌표 탐침** | 위 출력 | **창 크기**에 달렸다. 배너의 `--window-size` 가 전제다 |
| `창.getBoundingClientRect().width` | **234** | 글꼴·기본 여백에 달렸다. **성질만 인용한다** |
| **`dialog` 자신의 `autofocus` 가 무시된 것** | `#ㄹ1` | ★ **명세로는 dialog 가 받아야 한다.** 판이 오르면 바뀔 자리다 |
| **모달이 열렸을 때 `elementFromPoint` 가 늘 dialog 를 주는 것** | `#창` | ★ 명세는 「배경이 inert 다」까지만 정한다 |
| **`cancel` 을 몇 번까지 막을 수 있나** | **한 번** | ★ 닫기 감시자의 그룹 규칙은 명세에 있지만 **횟수는 구현이 정한다** |
| `popover` 의 모르는 값이 `manual` 인 것 | 위 출력 | **명세**(enumerated attribute)가 정한 절차다 |
| 최상위 레이어가 `z-index` 를 안 보는 것 | 위 출력 | **명세**가 정한 절차다. 값이 아니라 절차를 외운다 |
| 합성 이벤트로 가벼운 닫기가 안 나는 것 | A10 | **명세**(신뢰된 이벤트) |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **`<form method="dialog">`** 로 닫는 경로 — **던지지 않았다.** ③ **`popovertarget`·`popovertargetaction`** 으로 여닫는 경로와 그때의 「이어짐」 계산 — **DOM 중첩만 던졌다.** ④ **`::backdrop` 의 전환·애니메이션**(`allow-discrete`·`@starting-style`) — 던지지 않았다. ⑤ **`anchor` 위치 지정** — 던지지 않았다. ⑥ **`new CloseWatcher()`** 를 직접 만드는 경로 — dialog 를 통해서만 관측했다. ⑦ **그림자 트리 안의 dialog·popover** — [12번 주제](../12-shadow-dom/2-summary.md)와의 조합을 **던지지 않았다.** ⑧ **`::backdrop` 이 실제로 칠해진 픽셀** — 스크린숏을 찍지 않았다. ⑨ **모바일 가상 키보드와 뷰포트 축소** — headless 로 관측하지 못했다. ⑩ **A8 의 ③ 에 대한 처방**(닫기 전에 돌아갈 자리를 정해 두는 것) — 증상까지만 관측했다. ⑪ **최상위 레이어가 조상의 `transform`·`overflow: hidden` 에 안 잘리는 것** — 좌표 탐침까지만 던졌고 **픽셀로 확인하지 않았다.**

## 용어 풀이

- **최상위 레이어(top layer)** — 문서 위에 통째로 얹히는 별도의 렌더링 판. `z-index` 를 보지 않는다.
- **모달(modal)** — 열려 있는 동안 배경을 못 쓰게 만드는 대화 상자. `showModal()` 로만 된다.
- **비모달(modeless)** — 배경을 그대로 쓸 수 있는 대화 상자. `show()` 로 연 것.
- **`::backdrop`** — 최상위 레이어 요소 뒤에 깔리는 막. **계산값은 막이 없을 때도 그대로 나온다.**
- **`inert`** — 그 부분 트리를 사용자 입력과 포커스에서 빼는 속성. **`.inert` 는 속성이 붙었는지만 반영한다.**
- **가벼운 닫기(light dismiss)** — 바깥을 누르거나 `Esc` 를 눌렀을 때 저절로 닫히는 동작. **진짜 입력에만 난다.**
- **닫기 감시자(close watcher)** — `Esc` 같은 「물러나기」 신호를 받아 무엇을 닫을지 정하는 브라우저 안의 장치.
- **사용자 활성화(user activation)** — 「방금 사용자가 진짜로 눌렀다」는 표시. **`cancel` 을 막을 수 있는지를 이것이 정한다.**
- **신뢰된 이벤트(trusted event)** — 브라우저가 진짜 입력으로 만든 이벤트(`isTrusted === true`). `dispatchEvent` 로 만든 것은 아니다.
- **`returnValue`** — dialog 가 닫히면서 남기는 문자열. **`close()` 가 지우지 않는다.**
- **히트 테스트(hit test)** — 「이 좌표에 있는 요소가 누구인가」를 푸는 일. `elementFromPoint` 가 그 답을 준다.
- **부적용인 창** — 재 봤더니 같은 것이 아니라 **잴 것이 없는** 관측 수단. 이 편에서는 `::backdrop` 의 계산값이 그렇다.
