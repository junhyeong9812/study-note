# web-api/19 — `passive` 와 스크롤 성능: 기본값이 바뀐 이유 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 휠과 터치는 **CDP 로 넣은 진짜 입력**, 기본값 격자는 합성 이벤트다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 default passive value · flatten more options · set the canceled flag · 2.8 절로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> ★★ **시간·프레임은 재지 않았다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 기본값 42칸 · 인자 꼴 9줄 · body 바꿔 끼우기 · 진짜 입력의 네 칸 · 콘솔 줄 수 | **안 실었다** — 스크롤한 거리(관성으로 흔들린다) |
| 캡처를 여러 판 돌려 **한 글자도 같았다** | ★ **못 잰 것** — 스크롤 지연 · 프레임 · 입력 지연 |
| — | Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 16 / 42 — 문서 수준 네 대상 × 스크롤 네 이벤트의 사각형

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa16b-19-default.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,11p'
가. 옵션을 생략하고 달았을 때 — P = preventDefault 가 무시됨 · O = 먹힘
                touchstart  touchmove   touchend    wheel       mousewheel  click       
window          P           P           O           P           P           O           
document        P           P           O           P           P           O           
html            P           P           O           P           P           O           
body            P           P           O           P           P           O           
body 안의 div   O           O           O           O           O           O           
떼어 둔 div     O           O           O           O           O           O           
head            O           O           O           O           O           O           

preventDefault 가 무시된 칸 = 16 / 42
(exit 0)
```

**왜 그런가**

- **`window`·`document`·`html`·`body` × `touchstart`·`touchmove`·`wheel`·`mousewheel`** — **16칸**, 사각형 하나다.
- `touchend`·`click` 은 네 대상에서도 먹힌다. **`head`·떼어 둔 `div`·`body` 안의 `div`** 는 전부 먹힌다.
- DOM 표준의 **default passive value** 가 이 사각형을 정의한다 — 타입이 넷 중 하나이고 대상이 `Window`·`Document`·그 문서의 document element·body element 일 때만 `true`.

### 2. `window` 에서 되돌리는 꼴은 `{ passive: false }` 하나

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa16b-19-default.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '13,25p'
나. 세 번째 인자를 여러 꼴로 — wheel 이벤트
세 번째 인자              window    body 안의 div
생략                      P         O
false                     P         O
true                      P         O
{}                        P         O
{ capture: true }         P         O
{ passive: undefined }    P         O
{ once: true }            P         O
{ passive: false }        O         O
{ passive: true }         P         P

window 와 div 가 갈린 줄 = 7 / 9
(exit 0)
```

**왜 그런가**

- **`window`** — `{ passive: false }` 만 먹히고 나머지 여덟은 무시(P).
- **`div`** — `{ passive: true }` 만 무시되고 나머지 여덟은 먹힌다.
- **같은 답을 내는 줄은 `{ passive: false }`(둘 다 O)와 `{ passive: true }`(둘 다 P)** 둘이다. 나머지 **7 / 9** 가 갈렸다.
- **`false` 는 `capture`** 로 읽힌다. 명세의 flatten more options 는 불리언이면 **`passive` 를 null 로** 남기고, add an event listener 가 그 null 을 기본값으로 채운다.

### 3. 등록할 때 굳는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa16b-19-default.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '27,29p'
다. 달 때의 대상이 정하나 던질 때의 대상이 정하나 — body 를 바꿔 끼운다
  ① 문서의 body 일 때 달고 → 떼어 낸 뒤 던지면     defaultPrevented = false  (던질 때 document.body === 그 요소 ? false)
  ② 떼어 둔 채 달고 → 문서의 body 로 끼운 뒤 던지면 defaultPrevented = true  (던질 때 document.body === 그 요소 ? true)
(exit 0)
```

**왜 그런가**

- **① `false`**(떼어 낸 뒤에도 passive), **② `true`**(끼운 뒤에도 passive 아님).
- **passive 는 add an event listener 때 한 번 정해진다.** 던질 때 다시 계산하지 않는다.

### 4. 기본 passive 는 `cancelable: false` 로 받고, 화면은 움직인다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-19-real.html | sed -n '1,10p'
진짜 입력 한 번 — 리스너는 preventDefault 를 부른다 (cancelable · defaultPrevented 는 첫 호출의 값)
입력 · 리스너를 단 곳 · 옵션                      불림    cancelable  defaultPrevented  문서가 움직였나 상자가 움직였나
휠 · 리스너 없음                                  아니오  -           -                 예              아니오
휠 · document · 생략                              예      false       false             예              아니오
휠 · document · { passive: false }                예      true        true              아니오          아니오
휠 · window · 생략                                예      false       false             예              아니오
휠 · 상자 위 · 리스너 없음                        아니오  -           -                 아니오          예
휠 · #상자 · 생략                                 예      true        true              아니오          아니오
휠 · #상자 · { passive: true }                    예      false       false             아니오          예
휠 · document 의 scroll 리스너 · 생략             예      false       false             예              아니오
(exit 0)
```

**왜 그런가**

- **① `document` · 생략 — `false`·`false`·문서 움직임.** **③ `window` · 생략 — 같다.**
- **② `{ passive: false }` — `true`·`true`·안 움직임.**
- **④ `#상자` · 생략 — `true`·`true`·안 움직임**(상자는 문서 수준이 아니다). **⑤ `#상자` · `{ passive: true }` — `false`·`false`·상자 움직임.**
- **⑥ `scroll` 리스너 — `false`·`false`·문서 움직임.** `scroll` 은 **이미 일어난 스크롤의 알림**이라 막을 것이 없다.
- ★ **①·③ 의 `cancelable` 은 합성과 다르다** — 15번 주제의 합성 이벤트는 내가 `cancelable: true` 로 만들었으므로 `true` 였다. **진짜 휠은 `false` 로 왔다.**

### 5. `touchmove` 도 같은 모양이고, `touch-action` 은 리스너 없이 막는다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-19-real.html | sed -n '11,17p'
터치 · 리스너 없음                                아니오  -           -                 예              아니오
터치 · document touchmove · 생략                  예      false       false             예              아니오
터치 · document touchmove · { passive: false }    예      true        true              아니오          아니오
터치 · document touchstart · { passive: false }   예      true        true              아니오          아니오
터치 · touch-action: none 위 · 리스너 없음        아니오  -           -                 아니오          아니오

리스너가 불린 줄 가운데 문서나 상자가 움직인 줄 = 5 / 9
(exit 0)
```

**왜 그런가**

- **① `touchmove` · 생략 — `false`·`false`·움직임.**
- **② `touchmove` · `{ passive: false }` — `true`·`true`·안 움직임.**
- **③ `touchstart` · `{ passive: false }` — `true`·`true`·안 움직임** — 시작에서 막아도 된다.
- **④ `touch-action: none` — 리스너 0개 · 안 움직임.**
- 자바스크립트 없이 할 수 있는 일 — 그 상자에 **`touch-action: none`**. 리스너는 passive 로 두어도 된다.

### 6. 12 줄 — 기본 passive + 합성 칸만 0 줄

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-19-console.html
passive 리스너 안에서 preventDefault 를 부른 횟수 (부른 순서대로)
  ① document · 생략            · 진짜 휠   4
  ② #상자   · { passive: true } · 진짜 휠   4
  ③ document · 생략            · 합성 휠   4
  ④ #상자   · { passive: true } · 합성 휠   4
(exit 0)
```

```text
$ python3 wa16b-cdp.py log wa16b-19-console.html#1
intervention · error · Unable to preventDefault inside passive event listener due to target being treated as passive. See https://www.chromestatus.com/feature/6662647093133312
intervention · error · Unable to preventDefault inside passive event listener due to target being treated as passive. See https://www.chromestatus.com/feature/6662647093133312
intervention · error · Unable to preventDefault inside passive event listener due to target being treated as passive. See https://www.chromestatus.com/feature/6662647093133312
intervention · error · Unable to preventDefault inside passive event listener due to target being treated as passive. See https://www.chromestatus.com/feature/6662647093133312
(Log 도메인 항목 4 줄)
(exit 0)
```

```text
$ python3 wa16b-cdp.py log wa16b-19-console.html#2
javascript · error · Unable to preventDefault inside passive event listener invocation.
javascript · error · Unable to preventDefault inside passive event listener invocation.
javascript · error · Unable to preventDefault inside passive event listener invocation.
javascript · error · Unable to preventDefault inside passive event listener invocation.
(Log 도메인 항목 4 줄)
(exit 0)
```

```text
$ python3 wa16b-cdp.py log wa16b-19-console.html#3
(Log 도메인 항목 0 줄)
(exit 0)
```

```text
$ python3 wa16b-cdp.py log wa16b-19-console.html#4
javascript · error · Unable to preventDefault inside passive event listener invocation.
javascript · error · Unable to preventDefault inside passive event listener invocation.
javascript · error · Unable to preventDefault inside passive event listener invocation.
javascript · error · Unable to preventDefault inside passive event listener invocation.
(Log 도메인 항목 4 줄)
(exit 0)
```

**왜 그런가**

- **① 4줄**(`intervention`) · **② 4줄**(`javascript`) · **③ 0줄** · **④ 4줄**(`javascript`) — **16번 무시에 12줄**.
- **③ 기본 passive + 합성은 무시되는데 한 줄도 안 남는다.**
- ★ **콘솔로 「무시가 없었다」를 말할 수 없다** — 특히 합성 이벤트로 짠 테스트에서는 기본 passive 의 무시가 안 보인다.

### 7. 합성은 내가 준 값, 진짜는 브라우저가 정한 값

- **합성 — `true`**(내가 만든 값), **진짜 — `false`**.
- DOM 표준 **2.8 Observing event listeners** — 리스너가 전부 passive 면 스크롤을 먼저 시작하고 **이벤트를 uncancelable 로 만들어** 보낼 **수 있다**는 설명이다. **「할 수 있다」** 이지 「해야 한다」가 아니다.
- 그래서 **진짜 입력에서는 `cancelable` 이 「막을 수 있나」를 맞게 말하고**, 합성에서는 **내가 준 값이라 틀린다**([15번 주제](../15-listener-registration/3-answer.md)의 A8).

### 8. 문서 전체의 스크롤을 결재 대기에 묶기 때문이다

- 문서 수준의 비passive `wheel`·`touchmove` 리스너 하나가 있으면 **모든 스크롤**이 「이 리스너가 막을지」를 **메인 스레드에 물어야** 한다(명세 2.8 절의 모형).
- 그런 리스너 대부분은 **읽기만** 한다(분석·지연 로딩 등) — 막지 않는데도 기다리게 한다.
- 그래서 **문서 수준 네 대상 × 스크롤 네 이벤트만** 기본을 passive 로 바꿨다. 되돌리려면 **`{ passive: false }` 를 명시**한다(A2).
- ★ 그 「기다림」의 표지는 이 판에서도 보였다 — 아무것도 안 하는 비passive 리스너 하나를 더 달자 진짜 휠의 **`cancelable` 이 `false` 에서 `true` 로** 바뀌었다.

```text
$ python3 wa16b-cdp.py page wa16b-19-more.html | sed -n '1,3p'
가. document 에 wheel 리스너 A(생략 — 기본 passive, preventDefault 부름) · B({ passive: false }, 아무것도 안 함) — 진짜 휠
  A 만                                    A 안 cancelable=false · A 뒤 defaultPrevented=false · 문서가 움직였나=예
  A + B                                   A 안 cancelable=true · A 뒤 defaultPrevented=false · B 안 cancelable=true · 문서가 움직였나=예
(exit 0)
```

### 9. 잰 것은 「passive 인가」와 「움직였나」뿐이다

- **잰 것** — ① 리스너가 passive 인가(행동으로 묻는 판정 · 42칸·9줄·body) · ② 진짜 휠·터치에서 문서나 상자가 **움직였나**(그리고 `cancelable`·`defaultPrevented`·콘솔 줄 수).
- **못 잰 것** — **스크롤 지연·프레임·입력에서 화면까지의 시간.** 이 하네스는 합성 스레드의 시간을 못 본다.
- **「5%」는 Chromium 쪽 실험**이다(chromestatus 의 휠 개입 기록). 이 문서에는 **「Chromium 의 기록은 이렇게 적는다 — 이 편은 재지 않았다」** 로만 적는다.

### 10. 지금은 명세 본문, 출발은 Chrome 의 개입

- **있다** — DOM 표준의 **「default passive value」** 절.
- **출발은 Chrome 의 개입** — 터치 쪽 Chrome 56, 휠 쪽 Chrome 73(chromestatus). 이 판의 콘솔은 출처를 **`intervention`** 으로 찍는다(A6 의 ①).
- 진짜 입력에서 `cancelable` 을 `false` 로 보내는 것은 — **명세는 「할 수 있다」는 설명**, **하는 것은 Chrome 의 구현**, 이 편은 그것을 **관찰**했다.

### 11. 다른 주제와 잇기

- **15번 주제의 「두 줄」** — 같은 페이지를 이 하네스로 다시 열었다.

```text
$ python3 wa16b-cdp.py log wa12b-15-passive.html
javascript · error · Unable to preventDefault inside passive event listener invocation.
javascript · error · Unable to preventDefault inside passive event listener invocation.
(Log 도메인 항목 2 줄)
(exit 0)
```

  두 줄은 그 페이지에서 **명시 `{ passive: true }` 리스너가 두 번** 불린 것과 맞고, 나머지 호출은 전부 **기본 passive + 합성**(문항 6의 ③ 칸)이라 **한 줄도 안 남았다.** 이 판에서는 **합친 것이 아니라 ③ 칸의 침묵**이었다.
- **17번 주제의 두 속성** — 진짜 입력에서는 **`cancelable` 이 `false` 로 와서** 「막을 수 있나」가 제대로 드러났고, **`defaultPrevented`** 가 「막혔나」를 확인했다(A4·A5).
- **`passive` 가 동일성 키가 아니라는 것**은 [15번 주제](../15-listener-registration/3-answer.md)의 격자에서 쟀다. 문항 2의 **불리언 `false`** 가 `capture` 로만 읽히는 것도 그 격자의 「세 번째 인자가 불리언이면 `capture`」와 같은 규칙(flatten)이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 크로스 브라우저 이식성은 이 문서의 주장 범위 밖이다.

★★ **시간·프레임은 재지 않았다.** 스크롤은 「움직였나」만 찍었다.\
★ **진짜 휠**은 `Input.dispatchMouseEvent` 의 `mouseWheel`(아래로 100), **진짜 터치**는 `Input.dispatchTouchEvent`(대고 → 위로 100 을 다섯 번에 나눠 끌고 → 뗀다). 휠 앞에 **그 자리로 마우스를 옮긴다**(안 옮기면 첫 휠이 `body` 에 떨어졌다 — 하네스를 고친 자리다).\
★ **판마다 스크롤을 0 으로 돌리고 `scrollend`(또는 frame 30장)를 기다린 뒤** 입력을 넣었다. 휠을 **연달아** 넣으면 두 번째부터 타깃이 `body` 로 바뀌는 판이 있었다 — 그래서 판 사이에 반드시 가라앉혔다.\
★ **하네스** — [16번 주제](../16-event-propagation-phases/2-summary.md)의 (1)에 전문이 있다. 콘솔은 CDP `Log` 도메인의 `entryAdded` 를 셌다.

```sh
# wa16b-19-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
# 진짜 입력(CDP) 페이지 — 하네스가 자기 프로필로 Chrome 을 띄우고 끝나면 치운다
python3 wa16b-cdp.py page wa16b-19-real.html
python3 wa16b-cdp.py page wa16b-19-console.html
python3 wa16b-cdp.py page wa16b-19-more.html
python3 wa16b-cdp.py log wa16b-19-console.html#1   # #1 ~ #4 로 칸마다
# 합성 이벤트만 쓰는 페이지 — --dump-dom
google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 \
  --dump-dom wa16b-19-default.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 기본값 42칸 · 인자 꼴 9줄 · body 바꿔 끼우기 | 캡처 4판 | 동작 방식 (1)\~(3) · A1\~A3 |
| 진짜 휠 8줄 · 진짜 터치 5줄 | 캡처 4판 | 동작 방식 (4)·(5) · A4 · A5 |
| 콘솔 네 칸 + 15편 페이지 | 캡처 4판 | 동작 방식 (6) · A6 · A11 |
| 섞인 리스너의 `cancelable` · `touchstart` 를 막은 탭 | 캡처 4판 | 동작 방식 (7) · A8 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 진짜 입력의 `cancelable` | passive 면 `false` | 명세는 「할 수 있다」만 말한다 |
| 콘솔의 출처·문구·줄 수 | 네 칸 12줄 | Chrome 의 것이다 |
| `touch-action: none` 의 효과 | 리스너 없이 안 움직임 | 이 문서는 CSS·Pointer Events 명세를 열어 확인하지 않았다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② **성능**(지연·프레임). ③ `iframe` 안의 문서 수준 대상. ④ 핀치·관성 같은 **여러 손가락·빠른 끌기.** ⑤ **스크롤이 실제로 얼마나 기다렸나** — 비passive 가 끼면 `cancelable` 이 `true` 가 되는 것까지만 봤다(요약의 (7)).
