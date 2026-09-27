# web-api/23 — 포인터 이벤트: `pointerdown` 계열·마우스/터치/펜 통합·`setPointerCapture` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 마우스·펜·터치는 **CDP 로 넣은 진짜 입력**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [W3C Pointer Events](https://w3c.github.io/pointerevents/) 의 implicit pointer capture · PREVENT MOUSE EVENT · Suppressing a pointer event stream · `click` 은 `PointerEvent` 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 순서 로그 세 판 · 캡처 9칸 · 막기 일곱 줄 · `touch-action` 10칸 | **안 실었다** — 스크롤 중 `touchmove` 개수(4 와 5 로 갈렸다) |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 펜의 압력·기울기 · 멀티터치 · Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 포인터 하나에 호환 마우스 하나 · `click` 은 `PointerEvent`

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-23-order.html | sed -n '1,17p'
① 마우스 — 상자 위로 옮기고 누르고 떼고 바깥으로 옮긴다
  #   이벤트              생성자        종류    isPrimary  button buttons
  1   pointerover         PointerEvent  mouse   true       -1     0
  2   pointerenter        PointerEvent  mouse   true       -1     0
  3   mouseover           MouseEvent    -       -          0      0
  4   mouseenter          MouseEvent    -       -          0      0
  5   pointermove         PointerEvent  mouse   true       -1     0
  6   mousemove           MouseEvent    -       -          0      0
  7   pointerdown         PointerEvent  mouse   true       0      1
  8   mousedown           MouseEvent    -       -          0      1
  9   pointerup           PointerEvent  mouse   true       0      0
  10  mouseup             MouseEvent    -       -          0      0
  11  click               PointerEvent  mouse   false      0      0
  12  pointerout          PointerEvent  mouse   true       -1     0
  13  pointerleave        PointerEvent  mouse   true       -1     0
  14  mouseout            MouseEvent    -       -          0      0
  15  mouseleave          MouseEvent    -       -          0      0
(exit 0)
```

```text
$ python3 wa20b-cdp.py page wa20b-23-order.html | sed -n '19,35p'
② 펜 — 같은 동작을 pointerType: pen 으로
  #   이벤트              생성자        종류    isPrimary  button buttons
  1   pointerover         PointerEvent  pen     true       -1     0
  2   pointerenter        PointerEvent  pen     true       -1     0
  3   mouseover           MouseEvent    -       -          0      0
  4   mouseenter          MouseEvent    -       -          0      0
  5   pointermove         PointerEvent  pen     true       -1     0
  6   mousemove           MouseEvent    -       -          0      0
  7   pointerdown         PointerEvent  pen     true       0      1
  8   mousedown           MouseEvent    -       -          0      1
  9   pointerup           PointerEvent  pen     true       0      0
  10  mouseup             MouseEvent    -       -          0      0
  11  click               PointerEvent  pen     false      0      0
  12  pointerout          PointerEvent  pen     true       -1     0
  13  pointerleave        PointerEvent  pen     true       -1     0
  14  mouseout            MouseEvent    -       -          0      0
  15  mouseleave          MouseEvent    -       -          0      0
(exit 0)
```

**왜 그런가**

- **포인터가 먼저, 호환 마우스가 바로 뒤** — over/enter 네 줄, move 두 줄, down 두 줄, up 두 줄, 그다음 `click`, 나갈 때 out/leave 네 줄.
- ★ **`click` 의 생성자는 `PointerEvent`** — Pointer Events 가 「`click`·`auxclick`·`contextmenu` 는 `PointerEvent` 다」로 정한다. ★ **`isPrimary` 는 `false`** 로 찍혔다 — 이 판의 관찰이고, 근거 문장은 찾지 못했다.
- **펜은 `pointerType` 만 `pen`** 이고 나머지는 한 글자도 같다(CDP 의 펜은 마우스 이벤트에 종류만 바꾼 것이다).

### 2. 부르지 않은 캡처가 오고, `mouse*` 는 `touchend` 뒤에 몰려 온다

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-23-order.html | sed -n '37,54p'
③ 터치 — 상자를 손가락으로 댔다 뗀다
  #   이벤트              생성자        종류    isPrimary  button buttons
  1   pointerover         PointerEvent  touch   true       0      1
  2   pointerenter        PointerEvent  touch   true       0      1
  3   pointerdown         PointerEvent  touch   true       0      1
  4   touchstart          TouchEvent    -       -          -      -
  5   gotpointercapture   PointerEvent  touch   true       0      0
  6   pointerup           PointerEvent  touch   true       0      0
  7   lostpointercapture  PointerEvent  touch   true       0      0
  8   pointerout          PointerEvent  touch   true       0      0
  9   pointerleave        PointerEvent  touch   true       0      0
  10  touchend            TouchEvent    -       -          -      -
  11  mouseover           MouseEvent    -       -          0      0
  12  mouseenter          MouseEvent    -       -          0      0
  13  mousemove           MouseEvent    -       -          0      0
  14  mousedown           MouseEvent    -       -          0      1
  15  mouseup             MouseEvent    -       -          0      0
  16  click               PointerEvent  touch   false      0      0
(exit 0)
```

**왜 그런가**

- ★★ **`gotpointercapture` 가 저절로** 온다 — **암묵 캡처**(직접 조작 장치는 `pointerdown` 때 타깃에 캡처를 건다). 뗄 때 `lostpointercapture`.
- ★★ **`mousedown` 은 14번째** — `touchend` **뒤에** `mouseover → mouseenter → mousemove → mousedown → mouseup` 이 몰려 오고 `click` 이 마지막이다. 명세는 「제스처 판정 때문에 호환 이벤트가 `pointerup` 뒤에 한꺼번에 올 **수 있다**」고 적는다.

### 3. 캡처가 걸린 칸만 받는다 — 4 / 9

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-23-capture.html
상자에서 누르고 → 상자 밖 세 점으로 옮기고 → 밖에서 뗀다 (pointerdown 리스너가 하는 일만 바꾼다)
장치 · pointerdown 에서                 밖 move  got  lost  cancel  pointerup 의 target
mouse · 아무것도 안 함                  0/3      0    0     0       HTML
mouse · setPointerCapture               3/3      1    1     0       상자
mouse · releasePointerCapture           0/3      0    0     0       HTML
pen · 아무것도 안 함                    0/3      0    0     0       HTML
pen · setPointerCapture                 3/3      1    1     0       상자
pen · releasePointerCapture             0/3      0    0     0       HTML
touch · 아무것도 안 함                  3/3      1    1     0       상자
touch · setPointerCapture               3/3      1    1     0       상자
touch · releasePointerCapture           0/3      0    0     0       HTML

상자가 밖의 pointermove 를 받은 칸 = 4 / 9
(exit 0)
```

**왜 그런가**

- **마우스·펜 「안 함」 0 / 3 · `set` 3 / 3 · `release` 0 / 3.** 캡처가 없으면 밖의 이벤트는 **그 아래 요소**로 간다(`pointerup` 이 `HTML`).
- ★★ **터치 「안 함」 3 / 3** — 암묵 캡처다. 그래서 **마우스와 터치의 「아무것도 안 함」 칸이 반대**다.
- **터치 `release` 0 / 3** — 암묵 캡처를 풀자 마우스처럼 됐다.

### 4. `mousedown`·`mouseup` 은 사라지고 `click` 은 남는다

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-23-prevent.html | sed -n '1,9p'
그 요소가 받은 이벤트 (mousemove 는 개수로 줄였다)
마우스 클릭 · pointerdown 그대로
  mouseover → mousemove×1 → pointerdown → mousedown → pointerup → mouseup → click
마우스 클릭 · pointerdown 에서 preventDefault
  mouseover → mousemove×1 → pointerdown → pointerup → click
터치 탭 · pointerdown 그대로
  pointerdown → pointerup → mouseover → mousemove×1 → mousedown → mouseup → click
터치 탭 · pointerdown 에서 preventDefault
  pointerdown → pointerup → click
(exit 0)
```

**왜 그런가**

- **마우스** — `mouseover → mousemove → pointerdown → pointerup → click`. **`mousedown`·`mouseup` 만** 사라졌다.
- **터치** — `pointerdown → pointerup → click`. 뒤에 몰려 오던 호환 이벤트가 **전부** 사라졌다.
- ★ **`click` 은 둘 다 남는다** — 호환 이벤트가 아니다. 명세: 「포인터 이벤트 안의 `preventDefault` 는 `click`·`auxclick`·`contextmenu` 가 나는지에 **영향을 주면 안 된다**」.

### 5. 드래그가 시작되면 `pointercancel`

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-23-prevent.html | sed -n '1p;10,15p'
그 요소가 받은 이벤트 (mousemove 는 개수로 줄였다)
마우스 끌기 · 글자를 미리 고름
  mouseover → mousemove×1 → pointerdown → mousedown → mousemove×1 → dragstart → pointercancel
마우스 끌기 · 글자를 미리 고름 · pointerdown 에서 preventDefault
  mouseover → mousemove×1 → pointerdown
마우스 끌기 · 글자를 미리 고름 · user-select:none
  mouseover → mousemove×1 → pointerdown → mousedown → mousemove×1
(exit 0)
```

**왜 그런가**

- **① 그대로** — `pointerdown → mousedown → mousemove → dragstart → pointercancel`. 브라우저가 **끌어 놓기**를 시작하며 포인터 스트림을 끊었다 — 명세의 「Suppressing a pointer event stream」이 **드래그 조작의 시작**을 그 경우로 든다.
- **② `pointerdown` 에서 막음** — `pointerdown` 뒤로 아무것도 없다. 드래그도 `mousedown` 도 안 났다.
- **③ `user-select: none`** — `dragstart` 가 없다. `mousedown`·`mousemove` 는 난다.
- ②·③ 모두 **`pointerup` 이 글상자에 안 왔다** — 밖에서 뗐고 캡처가 없었다.

### 6. 허락한 방향으로 끌면 끊긴다 — 6 / 10

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-23-cancel.html
터치로 상자를 끈다 (다섯 번 움직임) — 상자가 받은 것
touch-action · 끈 방향      pointermove  pointercancel  pointerup  문서가 움직였나
auto · 위로                 1            1              0          예
auto · 왼쪽으로             1            1              0          예
none · 위로                 5            0              1          아니오
none · 왼쪽으로             5            0              1          아니오
pan-y · 위로                1            1              0          예
pan-y · 왼쪽으로            5            0              1          아니오
pan-x · 위로                5            0              1          아니오
pan-x · 왼쪽으로            1            1              0          예
manipulation · 위로         1            1              0          예
manipulation · 왼쪽으로     1            1              0          예

pointercancel 이 난 칸 = 6 / 10
(exit 0)
```

**왜 그런가**

- **끊긴 칸은 전부 「`pointermove` 1 · `pointercancel` 1 · `pointerup` 0 · 움직였다」**, 안 끊긴 칸은 **「5 · 0 · 1 · 안 움직였다」** 다.
- ★★ **`pan-y` 는 위로 끌면 끊기고 왼쪽으로는 안 끊긴다. `pan-x` 는 반대.** 허락한 축으로 끌면 브라우저가 그 포인터를 **스크롤에 가져간다.**
- `auto`·`manipulation` 은 두 방향 다, `none` 은 어느 방향도 안 끊겼다.

### 7. 브라우저가 포인터를 가져갔다는 알림

- 명세는 **「웹 페이지가 그 포인터의 이벤트를 더 받지 못할 것 같을 때」** 스트림을 끊는다 — 뷰포트를 움직이는 데(팬·확대) 쓰일 때, **드래그 조작이 시작될 때**, 모달이 열릴 때 등. 이 편에서 본 두 경우는 **터치 스크롤**(문항 6)과 **글자 드래그**(문항 5)다.
- **`pointercancel` 뒤에는 `pointerup` 이 없다**(문항 6의 끊긴 칸이 전부 `pointerup` 0). 끝 처리는 **`pointerup` 과 `pointercancel` 둘 다**에 둔다.

### 8. 암묵 캡처의 유무

- **터치는 `pointerdown` 때 저절로 캡처**되고 **마우스·펜은 아니다**(문항 3). 그래서 캡처 없이 짠 끌기가 **폰에서는 되고 PC 에서는 밖에서 끊긴다.**
- **터치에서 `releasePointerCapture` 하면 마우스처럼** 밖의 이벤트를 못 받는다(0 / 3).

### 9. `mouseover` 류와 `click`

- 명세 문장 둘 — ① 「(`pointerdown` 을 막아도) **`mouseover`·`mouseenter`·`mouseout`·`mouseleave` 가 나는 것은 막지 않는다**」 ② 「`click`·`auxclick`·`contextmenu` 는 `PointerEvent` 라 **호환 마우스 이벤트가 아니다** — 포인터 이벤트에서의 `preventDefault` 가 그것들에 영향을 주면 안 된다」.
- 그래서 **`click` 은 `click` 리스너에서** 막는다.

### 10. 다른 주제와 잇기

- **19번 주제와 문항 6** — 같은 사실(「`touch-action` 이 브라우저가 가져갈 방향을 정한다」)의 두 면이다. 19편은 **화면 쪽**(`none` 이면 리스너 없이도 안 움직인다), 이 편은 **포인터 쪽**(허락된 방향으로 끌면 `pointercancel` 로 스트림을 잃는다).
- **18번 주제의 짝** — `pointerover`/`pointerout` 은 **버블하고** `pointerenter`/`pointerleave` 는 **버블하지 않는다**(Pointer Events 의 이벤트 표 — `pointerenter` 는 Bubbles No). 이 편은 버블 여부를 **던지지 않았다** — 명세 표로만 답한다. 순서 로그에서 over 가 enter 보다 먼저인 것까지가 이 판의 관찰이다.
- **도구가 못 보는 것** — ① **진짜 펜의 압력·기울기**(CDP 의 펜은 종류만 바꾼 마우스다) ② **멀티터치**. 그 밖에 입력 지연·프레임.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 크로스 브라우저 이식성은 이 문서의 주장 범위 밖이다.

★ **마우스·펜** — `Input.dispatchMouseEvent` 의 `mouseMoved`·`mousePressed`·`mouseReleased`(펜은 `pointerType: "pen"`). **터치** — `Input.dispatchTouchEvent` 의 `touchStart`·`touchMove`·`touchEnd`. 좌표는 매번 `getBoundingClientRect` 에서 계산했다.\
★ **`touch-action` 격자** — 판마다 **스크롤 위치가 animation frame 20장 연달아 그대로일 때까지** 기다린 뒤 0 으로 돌리고 다시 기다렸다. `scrollend` 만 기다리던 시험판에서는 **앞 칸의 관성이 다음 칸으로 새어** `none · 위로` 가 「움직였다」로 찍혔다. 그 칸을 포함한 **세 칸을 한 칸씩 따로 연 시험판**(`#조각` 으로 칸을 골라 Chrome 을 칸마다 새로 띄웠다)이 고친 판과 같은 답을 냈다.\
★ **하네스** — [20번 주제](../20-listener-lifetime/2-summary.md)의 (1)에 전문이 있다.

```sh
# wa20b-23-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
# 마우스·펜은 Input.dispatchMouseEvent(pointerType) · 터치는 Input.dispatchTouchEvent
python3 wa20b-cdp.py page wa20b-23-order.html
python3 wa20b-cdp.py page wa20b-23-capture.html
python3 wa20b-cdp.py page wa20b-23-prevent.html
python3 wa20b-cdp.py page wa20b-23-cancel.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 세 장치의 순서 로그 | 캡처 3판 | 동작 방식 (1) · A1 · A2 |
| 캡처 격자 9칸 | 캡처 3판 | 동작 방식 (2) · A3 · A8 |
| 막기 일곱 줄 | 캡처 3판 | 동작 방식 (3) · A4 · A5 |
| `touch-action` 10칸 | 캡처 3판 (+ 고치기 전 시험판) | 동작 방식 (4) · A6 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `click` 의 `isPrimary` | `false` | 근거 문장을 못 찾았다 |
| 터치의 호환 이벤트 자리 | `touchend` 뒤에 몰려서 | 명세는 「그럴 수 있다」만 말한다 |
| 골라 둔 글자를 끌면 `dragstart` | 남 | 드래그 시작 조건은 HTML 의 끌어 놓기 절 몫이다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② 멀티터치 · 핀치. ③ `getCoalescedEvents()` · `pointerrawupdate`. ④ `pointerover`/`pointerenter` 의 버블 여부(명세 표로만 답했다).
