# web-api/23 — 포인터 이벤트: `pointerdown` 계열·마우스/터치/펜 통합·`setPointerCapture` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 를 늘린 「포인터 순서 로그」와 「받은 칸 격자」다** — 진짜 마우스·펜·터치 한 동작이 부르는 이벤트를 **생성자·`pointerType`·`isPrimary`·`button`·`buttons`** 와 함께 한 줄씩 적고, 드래그가 요소 밖으로 나갔을 때 **그 요소가 `pointermove` 를 받았나**를 장치 × 캡처 방식으로 센다.\
> **기준 소스** — [W3C Pointer Events](https://w3c.github.io/pointerevents/) 의 「implicit pointer capture」(직접 조작 장치는 `pointerdown` 때 **스스로** 캡처) · 「PREVENT MOUSE EVENT flag」(`pointerdown` 을 막으면 호환 마우스 이벤트가 안 난다 — **단 `mouseover`/`out`/`enter`/`leave` 는 막지 않는다**) · 「`click`·`auxclick`·`contextmenu` 는 `PointerEvent` 이고 호환 마우스 이벤트가 아니다」 · 「Suppressing a pointer event stream」(뷰포트를 움직이는 데 쓰이거나 **드래그 조작이 시작되면** 스트림을 끊는다 → `pointercancel`) 절. 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. **마우스·펜은 CDP `Input.dispatchMouseEvent`**(펜은 `pointerType: "pen"`), **터치는 `Input.dispatchTouchEvent`** 로 넣은 진짜 입력이다. 하네스는 [20번 주제](../20-listener-lifetime/2-summary.md)의 (1)에 있다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md)(`preventDefault` 가 막는 것). ★★ **[19번 주제](../19-passive-and-scroll/2-summary.md)의 (5)** 가 **`touch-action: none` 이면 리스너 없이 터치 스크롤이 안 된다**를 쟀다 — 여기는 **그때 포인터 쪽에서 무엇이 나나(`pointercancel`)** 로 확장한다. [18번 주제](../18-event-delegation/2-summary.md)의 (7)이 `mouseenter` 와 `mouseover` 의 차이를 쟀다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 세 장치의 순서 로그 · 캡처 격자 9칸 · 막기 일곱 줄 · `touch-action` 격자 10칸의 `pointermove`·`pointercancel`·`pointerup`·「문서가 움직였나」 | 캡처 세 판이 **한 글자도 같았다** |
| ★ **흔들려서 안 실었다** | 스크롤 중의 **`touchmove` 개수** | 시험판에서 같은 칸이 **4 와 5** 로 갈렸다. 그래서 그 열을 뺐다 |
| ★ **흔들렸다가 고쳤다** | `touch-action` 격자에서 **앞 칸의 관성 스크롤이 다음 칸으로 샌 것** | `scrollend` 하나만 기다리면 `none · 위로` 가 「움직였다」로 찍혔다. **스크롤 위치가 20프레임 연달아 그대로일 때까지** 기다리게 고쳤다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `scrollX`·`scrollY` 가 0 에서 움직였나((5)) · `e.constructor.name` |
| 창 ③ 같은 것을 두 번 읽기 | **부적용** | — |
| **창 ④ 디스패치 계수기 → 포인터 순서 로그 · 받은 칸 격자** | ★★★ **본체** | 어느 이벤트가 어느 순서로 · 요소 밖에서 받은 `pointermove` 수 |
| **진짜 입력(CDP)** | ★ **쓴다 — 입력 쪽** | 마우스 · 펜 · 터치 |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| **진짜 펜의 압력·기울기·지우개** | CDP 의 펜은 `pointerType` 만 바꾼 마우스 이벤트다. `pressure`·`tiltX` 는 안 넣었다 |
| **여러 손가락(멀티터치)·핀치** | 한 손가락만 넣었다 |
| **입력 지연·프레임** | 순서와 개수만 봤다. **재지 않았다** |
| **`pointerrawupdate`** | 보안 문맥 전용이고 던지지 않았다 |
| **호버가 없는 장치에서의 `pointerover` 시점** | CDP 터치는 대는 순간 `pointerover` 를 낸다 — 실제 기기와 같은지는 모른다 |

## 한눈에 — 쉽게 말하면

**★ 포인터 이벤트는 「마우스·손가락·펜을 한 창구에서 받는 번역기」다. 누가 눌렀든 `pointerdown` 으로 오고, 옛 코드를 위해 `mousedown` 같은 「호환 번역본」을 한 번 더 보낸다. `setPointerCapture` 는 「이 사람이 손을 뗄 때까지 내가 전부 받겠다」는 예약이다.**

| 비유 | 실체 |
|---|---|
| 한 창구 | `pointer*` 이벤트 — `pointerType` 이 `mouse`·`pen`·`touch` |
| 옛 코드를 위한 번역본 | 호환 마우스 이벤트(`mousedown`·`mousemove`·`mouseup` …) |
| 「번역본은 보내지 마」 | `pointerdown` 에서 `preventDefault()` |
| 「손 뗄 때까지 나한테」 예약 | `setPointerCapture(pointerId)` |
| 손가락은 처음부터 예약돼 있다 | 터치의 **암묵 캡처** — `gotpointercapture` 가 저절로 |
| 「이 사람은 이제 스크롤하러 갔다」 | `pointercancel` — 브라우저가 화면을 움직이는 데 가져갔다 |
| 「여기서는 스크롤하지 마」 표지판 | CSS `touch-action` |

```text
   ★ 마우스 클릭 한 번 — 포인터와 호환 마우스가 번갈아 온다 (이 판)

   옮김        pointerover → pointerenter → mouseover → mouseenter → pointermove → mousemove
   누름        pointerdown → mousedown
   뗌          pointerup   → mouseup
   (결과)      click  ← 생성자가 PointerEvent 다
   벗어남      pointerout → pointerleave → mouseout → mouseleave
```

## 이 주제가 답하려는 질문

1. **마우스 이벤트와 포인터 이벤트가 겹쳐 나는 순서** — 마우스 · 펜 · 터치에서 각각 어떻게 다른가.
2. **드래그가 요소 밖으로 나가도 끊기지 않게** 하려면 무엇을 하나 — 장치마다 기본값이 다른가.
3. **무엇이 포인터 스트림을 끊나** — `pointercancel` 은 언제 나고, `preventDefault`·`touch-action`·`user-select` 가 어떻게 얽히나.

## 동작 방식

### (1) ★★★ 본체 — 세 장치의 한 동작 순서

**언제 쓰나** — 「`mousedown` 과 `pointerdown` 을 둘 다 달았더니 두 번 돈다」·「터치에서 `mousedown` 이 늦게 온다」일 때.

**던진 것** — 상자에 포인터·마우스·터치·캡처·`click` 리스너를 달고, 진짜 입력으로 **① 마우스 · ② 펜 · ③ 터치** 한 동작씩. 마우스·펜은 **상자 위로 옮기고 → 누르고 → 떼고 → 바깥으로 옮긴다**, 터치는 **댔다 뗀다.**

```html
<!-- wa20b-23-order.html -->
<!doctype html>
<meta charset="utf-8">
<title>23-order</title>
<style>
  body { margin: 0; }
  #상자 { position: absolute; left: 100px; top: 100px; width: 200px; height: 200px; }
  #바깥 { position: absolute; left: 500px; top: 100px; width: 200px; height: 200px; }
</style>
<div id="상자">상자</div>
<div id="바깥">바깥</div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const O = [];
let n = 0;
const 형들 = ['pointerover', 'pointerenter', 'pointerdown', 'pointermove', 'pointerup', 'pointercancel',
             'pointerout', 'pointerleave', 'gotpointercapture', 'lostpointercapture',
             'mouseover', 'mouseenter', 'mousedown', 'mousemove', 'mouseup', 'mouseout', 'mouseleave',
             'touchstart', 'touchmove', 'touchend', 'click'];
const 값 = v => v === undefined ? '-' : String(v);
for (const 형 of 형들) document.getElementById('상자').addEventListener(형, e => {
  O.push('  ' + padw(String(++n), 4) + padw(e.type, 20) + padw(e.constructor.name, 14) + padw(값(e.pointerType), 8)
       + padw(값(e.isPrimary), 11) + padw(값(e.button), 7) + 값(e.buttons));
});
window.__판 = 제목 => {
  n = 0; O.push(''); O.push(제목);
  O.push('  ' + padw('#', 4) + padw('이벤트', 20) + padw('생성자', 14) + padw('종류', 8) + padw('isPrimary', 11) + padw('button', 7) + 'buttons');
  return 1;
};
window.__단계 = [
  ['js', '__판("① 마우스 — 상자 위로 옮기고 누르고 떼고 바깥으로 옮긴다")'],
  ['mouse', 'mouseMoved', '#상자', null, null, {}],
  ['mouse', 'mousePressed', '#상자', null, null, { button: 'left', buttons: 1, clickCount: 1 }],
  ['mouse', 'mouseReleased', '#상자', null, null, { button: 'left', buttons: 0, clickCount: 1 }],
  ['mouse', 'mouseMoved', '#바깥', null, null, {}],
  ['js', '__판("② 펜 — 같은 동작을 pointerType: pen 으로")'],
  ['mouse', 'mouseMoved', '#상자', null, null, { pointerType: 'pen' }],
  ['mouse', 'mousePressed', '#상자', null, null, { pointerType: 'pen', button: 'left', buttons: 1, clickCount: 1 }],
  ['mouse', 'mouseReleased', '#상자', null, null, { pointerType: 'pen', button: 'left', buttons: 0, clickCount: 1 }],
  ['mouse', 'mouseMoved', '#바깥', null, null, { pointerType: 'pen' }],
  ['js', '__판("③ 터치 — 상자를 손가락으로 댔다 뗀다")'],
  ['touchpt', 'touchStart', '#상자', null, null], ['touchpt', 'touchEnd', '#상자', null, null],
];
window.__끝 = () => O.slice(1).join('\n');
</script>
```

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

- ★★ **포인터가 먼저, 호환 마우스가 바로 뒤** — `pointerover → pointerenter → mouseover → mouseenter`, `pointerdown → mousedown`, `pointerup → mouseup`.
- ★ **`click` 의 생성자가 `PointerEvent`** 다 — Pointer Events 가 「`click` 은 `PointerEvent` 이고 호환 마우스 이벤트가 아니다」로 정한다. `pointerType` 도 `mouse` 로 실려 온다.
- ★ **`click` 의 `isPrimary` 가 `false`** 로 찍혔다 — 다른 포인터 이벤트는 `true` 인데 여기만 다르다. **이 판의 관찰**이고, 이 문서는 그 값을 정한 명세 문장을 찾지 못했다 — `click` 에서 `isPrimary` 로 판정하지 마라.
- **`button`** — 누르고 뗄 때 `0`(왼쪽), **움직임·들어옴·나감은 `-1`**(버튼 상태가 안 바뀜). 호환 `mouse*` 는 옛 모형대로 `0`.

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

- **펜은 마우스와 순서가 한 글자도 같다** — `pointerType` 만 `pen` 이다. ★ CDP 의 펜은 **마우스 이벤트에 종류만 바꿔 단 것**이라, 진짜 펜의 호버·압력은 이 판이 모른다.

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

- ★★ **터치는 순서가 다르다** — `pointerdown → touchstart` 다음에 **`gotpointercapture` 가 저절로** 온다(**암묵 캡처** — Pointer Events 가 「직접 조작 장치는 `pointerdown` 때 타깃에 캡처를 건다」로 정한다). 뗄 때 **`lostpointercapture`**.
- ★★ **호환 마우스 이벤트가 `touchend` 뒤에 한꺼번에** 온다 — `mouseover → mouseenter → mousemove → mousedown → mouseup` → **`click`**. Pointer Events 도 「제스처 판정 때문에 호환 마우스 이벤트가 **`pointerup` 뒤에 몰려** 나올 수 있다」고 적는다.
- **터치의 `pointerover` 는 `buttons: 1`** 이다 — 대는 순간에 들어오기 때문이다(마우스는 `0`).

```text
   세 장치 — 한 동작의 모양

   마우스 · 펜     over/enter → move → down → mousedown → up → mouseup → click → out/leave
                   (포인터와 호환 mouse* 가 한 쌍씩 번갈아)

   터치            over/enter → down → touchstart → ★gotpointercapture → up → ★lostpointercapture
                   → out/leave → touchend → (여기서 한꺼번에) mouseover … mousedown → mouseup → click

   ★ 터치에서 mouse* 에 기대면 「늦게, 몰아서」 온다
```

### (2) ★★★ `setPointerCapture` — 받은 칸 격자

**언제 쓰나** — 슬라이더·그림판에서 **끌다가 요소 밖으로 나가면 끊기는** 문제.

**던진 것** — 상자(`touch-action: none`)에서 누르고, **상자 밖 오른쪽 세 점**으로 옮기고, 밖에서 뗀다. `pointerdown` 리스너가 하는 일만 바꾼다 — **아무것도 안 함 · `setPointerCapture` · `releasePointerCapture`**. 상자의 `pointermove` 가운데 **좌표가 상자 밖인 것**을 센다.

```html
<!-- wa20b-23-capture.html -->
<!doctype html>
<meta charset="utf-8">
<title>23-capture</title>
<style>
  body { margin: 0; user-select: none; }
  #상자 { position: absolute; left: 100px; top: 100px; width: 200px; height: 200px; touch-action: none; }
  #쉼 { position: absolute; left: 100px; top: 500px; width: 200px; height: 100px; }
</style>
<div id="상자">상자</div>
<div id="쉼">쉼</div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const 상자 = document.getElementById('상자');
let 판 = null;
const 밖인가 = e => { const r = 상자.getBoundingClientRect(); return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom; };
상자.addEventListener('pointerdown', e => {
  if (!판) return;
  if (판.방식 === 'setPointerCapture') 상자.setPointerCapture(e.pointerId);
  if (판.방식 === 'releasePointerCapture') 상자.releasePointerCapture(e.pointerId);
});
상자.addEventListener('pointermove', e => { if (판 && 밖인가(e)) 판.밖move++; });
상자.addEventListener('gotpointercapture', () => { if (판) 판.got++; });
상자.addEventListener('lostpointercapture', () => { if (판) 판.lost++; });
상자.addEventListener('pointercancel', () => { if (판) 판.cancel++; });
document.addEventListener('pointerup', e => { if (판) 판.up = e.target.id || e.target.nodeName; });
const 줄 = [];
window.__판 = (장치, 방식) => { 판 = { 장치, 방식, 밖move: 0, got: 0, lost: 0, cancel: 0, up: '-' }; return 1; };
window.__적기 = () => { 줄.push(판); 판 = null; return 1; };
// 상자 한가운데에서 누르고, 상자 밖 오른쪽 세 점으로 옮긴 뒤, 밖에서 뗀다
const 밖 = [[400, 100], [450, 120], [500, 140]];
const 끌기 = 장치 => {
  if (장치 === 'touch') return [['touchpt', 'touchStart', '#상자', null, null],
    ...밖.map(([x, y]) => ['touchpt', 'touchMove', '#상자', x, y]), ['touchpt', 'touchEnd', '#상자', null, null]];
  const 덧 = { pointerType: 장치 };
  return [['mouse', 'mouseMoved', '#상자', null, null, 덧],
    ['mouse', 'mousePressed', '#상자', null, null, { ...덧, button: 'left', buttons: 1, clickCount: 1 }],
    ...밖.map(([x, y]) => ['mouse', 'mouseMoved', '#상자', x, y, { ...덧, button: 'left', buttons: 1 }]),
    ['mouse', 'mouseReleased', '#상자', 밖[2][0], 밖[2][1], { ...덧, button: 'left', buttons: 0, clickCount: 1 }],
    ['mouse', 'mouseMoved', '#쉼', null, null, 덧]];
};
const 단계 = [];
for (const 장치 of ['mouse', 'pen', 'touch'])
  for (const 방식 of ['아무것도 안 함', 'setPointerCapture', 'releasePointerCapture'])
    단계.push(['js', `__판(${JSON.stringify(장치)}, ${JSON.stringify(방식)})`], ...끌기(장치), ['js', '__적기()']);
window.__단계 = 단계;
window.__끝 = () => {
  const O = [];
  O.push('상자에서 누르고 → 상자 밖 세 점으로 옮기고 → 밖에서 뗀다 (pointerdown 리스너가 하는 일만 바꾼다)');
  O.push(padw('장치 · pointerdown 에서', 40) + padw('밖 move', 9) + padw('got', 5) + padw('lost', 6) + padw('cancel', 8) + 'pointerup 의 target');
  for (const r of 줄) O.push(padw(r.장치 + ' · ' + r.방식, 40) + padw(r.밖move + '/3', 9) + padw(String(r.got), 5)
                         + padw(String(r.lost), 6) + padw(String(r.cancel), 8) + r.up);
  O.push('');
  O.push('상자가 밖의 pointermove 를 받은 칸 = ' + 줄.filter(r => r.밖move > 0).length + ' / ' + 줄.length);
  return O.join('\n');
};
</script>
```

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

- ★★★ **마우스·펜은 캡처하지 않으면 밖의 `pointermove` 를 0 / 3 받는다** — 포인터가 나가면 이벤트는 **그 아래 요소**로 간다. `pointerup` 도 `HTML` 에서 났다.
- ★★★ **`setPointerCapture` 하면 3 / 3** — 밖에서도 상자가 받고, **`pointerup` 도 상자에서** 난다. `gotpointercapture`/`lostpointercapture` 가 한 번씩.
- ★★ **터치는 아무것도 안 해도 3 / 3** — **암묵 캡처**다((1)).
- ★★ **터치에서 `releasePointerCapture` 하면 0 / 3** — 암묵 캡처를 **풀면** 마우스처럼 된다. `got`/`lost` 도 0.
- **받은 칸 4 / 9** — 캡처가 걸린 네 칸(마우스·펜의 `set` · 터치의 「안 함」·`set`)이 정확히 받은 칸이다.

```text
   캡처가 있을 때와 없을 때 — 포인터가 상자 밖으로 나간 뒤

   캡처 없음      pointermove ─▶ 그 점 아래의 요소(HTML)       상자는 모른다
                  pointerup   ─▶ HTML

   캡처 있음      pointermove ─▶ ★ 상자                        좌표는 상자 밖이어도
                  pointerup   ─▶ ★ 상자 ─▶ lostpointercapture   떼는 순간 캡처가 풀린다
```

```text
   ★ 밖으로 끈 pointermove 를 누가 받나 (이 판 9칸)

                 아무것도 안 함      setPointerCapture     releasePointerCapture
   mouse         0/3  (아래 요소)    3/3  (상자)            0/3
   pen           0/3                 3/3                    0/3
   touch         3/3  ★암묵 캡처     3/3                    0/3  ★풀림

   ★ 「터치에서는 되는데 마우스에서는 끊긴다」 = 암묵 캡처의 유무
```

- ★ **이 격자를 처음 돌렸을 때 마우스 `set` 칸이 1 / 3 에 `pointercancel` 1** 이 나왔다. 앞 칸의 끌기가 **글자를 골라 놓아** 다음 끌기가 **드래그(끌어 놓기)** 로 바뀐 것으로 보인다 — 상자에 `user-select: none` 을 주자 사라졌다(위 블록이 그 판이다). **같은 모양(골라 둔 글자를 끌면 `dragstart` → `pointercancel`)은 (3)에서 따로 쟀다.**

### (3) ★★ `pointerdown` 에서 막으면 · 드래그가 스트림을 끊는다

**언제 쓰나** — 「터치에서 가짜 `mousedown` 이 와서 두 번 돈다」·「끄는 도중 `pointercancel` 이 온다」일 때.

```html
<!-- wa20b-23-prevent.html -->
<!doctype html>
<meta charset="utf-8">
<title>23-prevent</title>
<style>
  body { margin: 0; }
  #상자 { position: absolute; left: 100px; top: 100px; width: 200px; height: 200px; user-select: none; }
  #글상자 { position: absolute; left: 100px; top: 400px; width: 200px; height: 100px; }
  #글상자.막음 { user-select: none; }
  #쉼 { position: absolute; left: 500px; top: 600px; width: 100px; height: 100px; }
</style>
<div id="상자">상자</div>
<div id="글상자">끌어 볼 글자가 여기 있다</div>
<div id="쉼">쉼</div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
let 판 = null;
const 형들 = ['pointerdown', 'pointerup', 'pointercancel', 'mouseover', 'mousedown', 'mousemove', 'mouseup', 'click', 'dragstart'];
for (const id of ['상자', '글상자']) for (const 형 of 형들) $(id).addEventListener(형, e => {
  if (!판 || 판.id !== id) return;
  if (형 === 'pointerdown' && 판.막기) e.preventDefault();
  판.본것.push(형);
});
const 줄 = [];
window.__판 = (라벨, id, 막기, 준비) => {
  getSelection().removeAllRanges();
  $('글상자').classList.toggle('막음', 준비 === 'user-select:none');
  if (준비 === '글자를 미리 고름' || 준비 === 'user-select:none') { const r = document.createRange(); r.selectNodeContents($('글상자')); getSelection().addRange(r); }
  판 = { 라벨, id, 막기, 본것: [] };
  return 1;
};
window.__적기 = () => { 줄.push(판); 판 = null; return 1; };
const 마우스클릭 = 선택자 => [['mouse', 'mouseMoved', 선택자, null, null, {}],
  ['mouse', 'mousePressed', 선택자, null, null, { button: 'left', buttons: 1, clickCount: 1 }],
  ['mouse', 'mouseReleased', 선택자, null, null, { button: 'left', buttons: 0, clickCount: 1 }],
  ['mouse', 'mouseMoved', '#쉼', null, null, {}]];
const 탭 = 선택자 => [['touchpt', 'touchStart', 선택자, null, null], ['touchpt', 'touchEnd', 선택자, null, null]];
const 마우스끌기 = 선택자 => [['mouse', 'mouseMoved', 선택자, 20, 20, {}],
  ['mouse', 'mousePressed', 선택자, 20, 20, { button: 'left', buttons: 1, clickCount: 1 }],
  ['mouse', 'mouseMoved', 선택자, 120, 30, { button: 'left', buttons: 1 }],
  ['mouse', 'mouseMoved', 선택자, 300, 60, { button: 'left', buttons: 1 }],
  ['mouse', 'mouseReleased', 선택자, 300, 60, { button: 'left', buttons: 0, clickCount: 1 }],
  ['mouse', 'mouseMoved', '#쉼', null, null, {}]];
const 판들 = [
  ['마우스 클릭 · pointerdown 그대로', '상자', false, '', 마우스클릭('#상자')],
  ['마우스 클릭 · pointerdown 에서 preventDefault', '상자', true, '', 마우스클릭('#상자')],
  ['터치 탭 · pointerdown 그대로', '상자', false, '', 탭('#상자')],
  ['터치 탭 · pointerdown 에서 preventDefault', '상자', true, '', 탭('#상자')],
  ['마우스 끌기 · 글자를 미리 고름', '글상자', false, '글자를 미리 고름', 마우스끌기('#글상자')],
  ['마우스 끌기 · 글자를 미리 고름 · pointerdown 에서 preventDefault', '글상자', true, '글자를 미리 고름', 마우스끌기('#글상자')],
  ['마우스 끌기 · 글자를 미리 고름 · user-select:none', '글상자', false, 'user-select:none', 마우스끌기('#글상자')],
];
const 단계 = [];
for (const [라벨, id, 막기, 준비, 동작] of 판들)
  단계.push(['js', `__판(${JSON.stringify(라벨)}, ${JSON.stringify(id)}, ${막기}, ${JSON.stringify(준비)})`], ...동작, ['js', '__적기()']);
window.__단계 = 단계;
window.__끝 = () => {
  const O = [];
  O.push('그 요소가 받은 이벤트 (mousemove 는 개수로 줄였다)');
  for (const r of 줄) {
    const 줄인것 = []; let mm = 0;
    for (const t of r.본것) { if (t === 'mousemove') { mm++; continue; } if (mm) { 줄인것.push('mousemove×' + mm); mm = 0; } 줄인것.push(t); }
    if (mm) 줄인것.push('mousemove×' + mm);
    O.push(r.라벨);
    O.push('  ' + 줄인것.join(' → '));
  }
  return O.join('\n');
};
</script>
```

```text
$ python3 wa20b-cdp.py page wa20b-23-prevent.html | sed -n '1,5p'
그 요소가 받은 이벤트 (mousemove 는 개수로 줄였다)
마우스 클릭 · pointerdown 그대로
  mouseover → mousemove×1 → pointerdown → mousedown → pointerup → mouseup → click
마우스 클릭 · pointerdown 에서 preventDefault
  mouseover → mousemove×1 → pointerdown → pointerup → click
(exit 0)
```

- ★★ **마우스 — `pointerdown` 에서 막으면 `mousedown`·`mouseup` 이 사라진다.** 그런데 **`mouseover`·`mousemove`(누르기 전)는 이미 났고**, **`click` 은 그대로** 온다.

```text
$ python3 wa20b-cdp.py page wa20b-23-prevent.html | sed -n '1p;6,9p'
그 요소가 받은 이벤트 (mousemove 는 개수로 줄였다)
터치 탭 · pointerdown 그대로
  pointerdown → pointerup → mouseover → mousemove×1 → mousedown → mouseup → click
터치 탭 · pointerdown 에서 preventDefault
  pointerdown → pointerup → click
(exit 0)
```

- ★★ **터치 — 막으면 뒤에 몰려 오던 호환 이벤트(`mouseover`·`mousemove`·`mousedown`·`mouseup`)가 전부 사라지고 `click` 만** 남는다.
- **명세 그대로다** — `pointerdown` 을 막으면 **PREVENT MOUSE EVENT 플래그**가 서서 `mousedown`·`mousemove`·`mouseup` 을 안 보낸다. **`mouseover`/`out`/`enter`/`leave` 는 막지 않고**, **`click` 은 호환 이벤트가 아니라** 막히지 않는다.

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

- ★★ **글자를 골라 둔 상자를 마우스로 끌면 `dragstart` → `pointercancel`** — 브라우저가 **끌어 놓기(드래그)** 를 시작하며 포인터 스트림을 끊었다. Pointer Events 의 「Suppressing a pointer event stream」이 **드래그 조작의 시작**을 그 경우로 든다.
- **`pointerdown` 에서 막으면 `dragstart` 도 `mousedown` 도 없다** — 드래그의 시작이 막혔다.
- **`user-select: none` 이면 `dragstart` 가 없다** — 골라 둔 글자가 없는 것처럼 끌렸다.
- ★ **두 경우 다 `pointerup` 이 글상자에 안 왔다** — 밖에서 뗐고 캡처가 없었다((2)).

```text
   pointerdown 에서 preventDefault 가 막는 것 (Pointer Events — PREVENT MOUSE EVENT)

   막는다       mousedown · mousemove · mouseup     (호환 마우스 이벤트)
                드래그의 시작(dragstart)             (이 판의 관찰)
   안 막는다    mouseover · mouseout · mouseenter · mouseleave
                click · auxclick · contextmenu      (PointerEvent 라 호환 이벤트가 아니다)
```

### (4) ★★ `touch-action` 과 `pointercancel` — 19편의 확장

**언제 쓰나** — 「터치로 끄는데 `pointermove` 가 한 번 오고 끊긴다」일 때.

**던진 것** — 가로·세로로 다 스크롤되는 문서 위의 상자에 `touch-action` 다섯 값을 주고, **위로 · 왼쪽으로** 각각 100 을 다섯 번에 나눠 끈다. 판마다 **스크롤 위치가 20프레임 연달아 그대로일 때까지** 가라앉힌 뒤 0 으로 돌린다.

```html
<!-- wa20b-23-cancel.html -->
<!doctype html>
<meta charset="utf-8">
<title>23-cancel</title>
<style>
  body { margin: 0; height: 3000px; width: 3000px; }
  #상자 { position: absolute; left: 300px; top: 300px; width: 200px; height: 200px; }
</style>
<div id="상자">상자</div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const 상자 = document.getElementById('상자');
let 판 = null;
for (const 형 of ['pointermove', 'pointercancel', 'pointerup'])
  상자.addEventListener(형, () => { if (판) 판[형]++; });
// 스크롤이 가라앉았나를 프레임으로 기다린다 — 스크롤 위치가 animation frame 20장 연달아 그대로면 끝(최대 600장)
// ★ scrollend 하나만 기다리면 앞 칸의 관성 스크롤이 다음 칸으로 샜다(시험판에서 확인)
const 가라앉기 = () => new Promise(r => {
  let 같음 = 0, n = 0, 전 = scrollX + ',' + scrollY;
  const 한장 = () => {
    const 지금 = scrollX + ',' + scrollY;
    같음 = 지금 === 전 ? 같음 + 1 : 0; 전 = 지금;
    if (같음 >= 20 || ++n >= 600) r(1); else requestAnimationFrame(한장);
  };
  requestAnimationFrame(한장);
});
const 줄 = [];
window.__판 = (ta, 방향) => {
  상자.style.touchAction = ta;
  return 가라앉기().then(() => { scrollTo(0, 0); return 가라앉기(); }).then(() => {
    판 = { ta, 방향, pointermove: 0, pointercancel: 0, pointerup: 0 };
    return 1;
  });
};
window.__적기 = () => { 판.움직임 = scrollX > 0 || scrollY > 0 ? '예' : '아니오'; 줄.push(판); 판 = null; return 1; };
// 상자 가운데에 대고 한 방향으로 100 을 다섯 번에 나눠 끈 뒤 뗀다
const 끌기 = 방향 => {
  const s = [['touchpt', 'touchStart', '#상자', 100, 100]];
  for (let k = 1; k <= 5; k++) s.push(['touchpt', 'touchMove', '#상자', 방향 === '위로' ? 100 : 100 - 20 * k, 방향 === '위로' ? 100 - 20 * k : 100]);
  s.push(['touchpt', 'touchEnd', '#상자', null, null]);
  return s;
};
const 단계 = [];
for (const ta of ['auto', 'none', 'pan-y', 'pan-x', 'manipulation'])
  for (const 방향 of ['위로', '왼쪽으로'])
    단계.push(['js', `__판(${JSON.stringify(ta)}, ${JSON.stringify(방향)})`], ...끌기(방향), ['js', '가라앉기()'], ['js', '__적기()']);
window.__단계 = 단계;
window.__끝 = () => {
  const O = [];
  O.push('터치로 상자를 끈다 (다섯 번 움직임) — 상자가 받은 것');
  O.push(padw('touch-action · 끈 방향', 28) + padw('pointermove', 13) + padw('pointercancel', 15) + padw('pointerup', 11) + '문서가 움직였나');
  for (const r of 줄) O.push(padw(r.ta + ' · ' + r.방향, 28) + padw(String(r.pointermove), 13) + padw(String(r.pointercancel), 15)
                         + padw(String(r.pointerup), 11) + r.움직임);
  O.push('');
  O.push('pointercancel 이 난 칸 = ' + 줄.filter(r => r.pointercancel > 0).length + ' / ' + 줄.length);
  return O.join('\n');
};
</script>
```

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

- ★★★ **브라우저가 스크롤하기로 한 칸은 전부 「`pointermove` 1 · `pointercancel` 1 · `pointerup` 0 · 문서가 움직였다」** — 첫 움직임 뒤 스트림이 **끊겼다.** 「뷰포트를 움직이는 데 쓰인 포인터」라 명세가 스트림을 끊는다.
- **`none` — 두 방향 다 `pointermove` 5 · `pointerup` 1 · 문서 안 움직임.**
- ★★ **`pan-y` 는 위로 끌면 끊기고 왼쪽으로 끌면 안 끊긴다**, **`pan-x` 는 그 반대**다 — 허락한 방향만 브라우저가 가져간다.
- **`manipulation`(팬·확대 허락) 은 `auto` 와 같다** — 두 방향 다 끊겼다.
- **`pointercancel` 이 난 칸 6 / 10.**
```text
   끄는 중 상태를 닫는 두 문 — pointercancel 을 빠뜨리면

   pointerdown ─▶ 끄는 중 = true
        │
        ├─ pointerup      ─▶ 끄는 중 = false   ✔
        └─ pointercancel  ─▶ (처리 없음)       ✕ 끄는 중이 영영 true — 다음 hover 가 「끌기」로 읽힌다
```

- [19번 주제](../19-passive-and-scroll/2-summary.md)의 (5)는 **`touchmove` 리스너 쪽**에서 「`none` 이면 리스너 없이도 안 움직인다」를 봤다. **포인터 쪽에서는 그 반대편 — 허락된 방향으로 끌면 `pointercancel` 로 스트림을 잃는다 — 가 보인다.**

```text
   ★ touch-action × 끈 방향 → 포인터 스트림 (이 판 10칸)

                  위로 끔                    왼쪽으로 끔
   auto           ✕ cancel · 스크롤          ✕ cancel · 스크롤
   none           ○ move 5 · up             ○ move 5 · up
   pan-y          ✕ cancel · 스크롤          ○ move 5 · up
   pan-x          ○ move 5 · up             ✕ cancel · 스크롤
   manipulation   ✕ cancel · 스크롤          ✕ cancel · 스크롤

   ✕ = 첫 pointermove 뒤 pointercancel(브라우저가 가져감)   ○ = 끝까지 받음
   ★ 끌기로 무엇을 옮기는 요소는 「그 방향을 브라우저에게 주지 않는」 touch-action 을 단다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   이벤트      pointerover · pointerenter · pointerdown · pointermove · pointerup · pointercancel
               pointerout · pointerleave · gotpointercapture · lostpointercapture
   속성        e.pointerId · e.pointerType('mouse'|'pen'|'touch') · e.isPrimary · e.button · e.buttons
   캡처        el.setPointerCapture(e.pointerId) · el.releasePointerCapture(e.pointerId) · el.hasPointerCapture(id)
   CSS         touch-action: auto | none | pan-x | pan-y | manipulation …

   끌기 관용구
     el.addEventListener('pointerdown', e => { el.setPointerCapture(e.pointerId); 시작(e); });
     el.addEventListener('pointermove', e => { if (el.hasPointerCapture(e.pointerId)) 옮김(e); });
     el.addEventListener('pointerup',     끝);
     el.addEventListener('pointercancel', 끝);     ← 빠뜨리면 「끄는 중」 상태가 남는다
     .끌기 { touch-action: none; user-select: none; }
```

### 어디서 헷갈리나

- **`click` 도 포인터 이벤트다** — 생성자가 `PointerEvent` 다((1)).
- **터치는 캡처가 기본이다** — 마우스와 반대다((2)).
- **`pointercancel` 뒤에는 `pointerup` 이 없다** — 끝 처리를 `pointerup` 에만 두면 새다((4)).

## 어디서 틀리나

### 1. `mousedown` 과 `pointerdown` 을 둘 다 달아 같은 일을 한다

**두 번 돈다**((1)) — 포인터 하나에 호환 마우스 이벤트가 따라온다. 포인터 쪽만 쓰거나, `pointerdown` 에서 `preventDefault()` 로 호환 이벤트를 끈다((3)).

### 2. 끄는 요소에 캡처를 안 건다 — 마우스에서만 끊긴다

**마우스·펜은 밖에서 0 / 3**, 터치는 암묵 캡처라 3 / 3 이었다((2)). 「폰에서는 되는데」가 이것이다.

### 3. 끝 처리를 `pointerup` 에만 둔다

**`pointercancel` 로 끝나면 `pointerup` 이 안 온다**((4)). 둘 다 같은 끝 처리로 받는다.

### 4. 터치 끌기 요소에 `touch-action` 을 안 준다

**첫 움직임 뒤 `pointercancel`** 이고 문서가 스크롤된다((4)). 끄는 방향을 브라우저에게 주지 않는 값(`none` · 반대축 `pan-*`)을 준다.

### 5. `pointerdown` 에서 막으면 `click` 도 안 온다고 믿는다

**`click` 은 온다**((3)) — 호환 이벤트가 아니다. `click` 을 막으려면 `click` 에서 막는다.

### 6. 글자가 있는 요소를 끌기로 쓴다

**골라 둔 글자가 있으면 드래그가 시작되어 `pointercancel`**((3)). `user-select: none` 을 주거나 `pointerdown` 에서 막는다.

### 7. `click` 의 `isPrimary` 로 판정한다

**이 판에서 `false`** 였다((1)). 판정은 `pointerdown` 에서 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 포인터 이벤트 뒤에 호환 마우스 이벤트가 오는 것 | **명세**(Pointer Events — 호환 마우스 이벤트 절 · **선택적** 절이다) · 이 판도 그랬다((1)) |
| 터치의 **암묵 캡처** | **명세**(Pointer Events — implicit pointer capture) · 이 판도 그랬다((2)) |
| `pointerdown` 을 막으면 `mousedown`·`mousemove`·`mouseup` 이 안 나고 `mouseover` 류·`click` 은 나는 것 | **명세**(Pointer Events — PREVENT MOUSE EVENT · click 은 PointerEvent) · 이 판도 그랬다((3)) |
| 스크롤·드래그가 시작되면 `pointercancel` | **명세**(Pointer Events — Suppressing a pointer event stream) · 이 판도 그랬다((3)·(4)) |
| 터치의 호환 이벤트가 **`touchend` 뒤에 몰려** 오는 것 | ★ 명세는 「**그럴 수 있다**」 · **이 판의 관찰**((1)) |
| `click` 의 `isPrimary` 가 `false` | ★ **이 판의 관찰** — 이 문서는 근거 문장을 찾지 못했다 |
| `touch-action` 값마다 어느 방향을 브라우저가 가져가나 | ★ `touch-action` 의 정의는 Pointer Events 에 있지만 **이 문서는 그 절을 옮기지 않았다** — **이 판의 10칸 관찰**로 적는다((4)) |
| CDP 의 펜이 **마우스에 종류만 바꾼 것**인 것 | ★ **도구의 성질** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 마우스·터치·펜을 한 코드로 | `pointer*` | `mouse*` + `touch*` 두 벌 |
| 끌기(슬라이더·그림판·정렬) | `setPointerCapture` + `pointercancel` 처리 + `touch-action` | 문서에 `mousemove` 를 달아 흉내 |
| 옛 `mouse*` 코드와 공존 | `pointerdown` 에서 `preventDefault()`(호환 끄기) | 두 쪽에서 같은 일 |
| 장치에 따라 다르게 | `e.pointerType` (in `pointerdown`) | `click` 의 속성으로 판정 |
| 스크롤은 살리고 가로 끌기만 | `touch-action: pan-y` | `touch-action: none` 으로 전부 막기 |

## 핵심 문장

1. **포인터 이벤트가 먼저, 호환 마우스 이벤트가 뒤따른다** — 터치에서는 `touchend` 뒤에 몰려 온다.
2. **`click` 은 `PointerEvent` 다** — 호환 이벤트가 아니라 `pointerdown` 을 막아도 온다.
3. **터치는 암묵 캡처, 마우스·펜은 `setPointerCapture` 를 불러야** 밖에서도 받는다(받은 칸 4 / 9).
4. **`pointerdown` 을 막으면 `mousedown`·`mouseup` 이 사라진다** — `mouseover` 류는 남는다.
5. **브라우저가 화면을 움직이거나 드래그를 시작하면 `pointercancel`** 이고 `pointerup` 은 없다.
6. **`touch-action` 은 「어느 방향을 브라우저에 줄지」** 다 — 준 방향으로 끌면 스트림을 잃는다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 23번)
- [19번 주제](../19-passive-and-scroll/2-summary.md) — **`touch-action` 과 터치 스크롤의 첫 측정**(`touchmove` 쪽). 여기는 **포인터 쪽의 `pointercancel`**
- [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md) — `preventDefault` 가 막는 것의 정본
- [18번 주제](../18-event-delegation/2-summary.md) — `mouseenter` 와 `mouseover`(위임)
- [16번 주제](../16-event-propagation-phases/2-summary.md) — 진짜 클릭 한 번의 전파 순서
- [22번 주제](../22-input-event-order/2-summary.md) — 같은 「입력」 묶음의 키보드 쪽
- [20번 주제](../20-listener-lifetime/2-summary.md) — 하네스 전문(마우스·터치 한 동작 단계)

## 용어 풀이

- **포인터 이벤트** — 마우스·펜·터치를 한 모형으로 받는 이벤트(`pointer*`).
- **`pointerType`** — 무엇이 눌렀나(`mouse`·`pen`·`touch`).
- **호환 마우스 이벤트** — 옛 `mouse*` 코드를 위해 포인터 입력에서 **만들어 보내는** 마우스 이벤트.
- **포인터 캡처** — 그 포인터의 이벤트를 **한 요소가 전부** 받게 하는 것. `setPointerCapture`.
- **암묵 캡처** — 터치처럼 직접 조작 장치는 `pointerdown` 때 **저절로** 캡처가 걸리는 것.
- **`pointercancel`** — 브라우저가 그 포인터를 **가져갔다**(스크롤·드래그 등)는 알림. 그 뒤 `pointerup` 은 없다.
- **PREVENT MOUSE EVENT 플래그** — `pointerdown` 을 막으면 서는 표시. 호환 `mousedown`·`mousemove`·`mouseup` 을 끈다.
- **`touch-action`** — 터치로 브라우저가 할 수 있는 일(팬·확대)을 CSS 로 미리 정하는 속성.
- **받은 칸 격자** — 장치 × 캡처 방식마다 요소가 밖의 `pointermove` 를 받았나 센 것. 이 편의 본체.

## 더 들어가면

- **멀티터치**(`isPrimary: false` 인 둘째 손가락)는 던지지 않았다.
- **`getCoalescedEvents()`·`getPredictedEvents()`**(끌기의 부드러움)는 던지지 않았다.
- **`pointerrawupdate`** 는 보안 문맥 전용이라 던지지 않았다.
- **펜의 호버·지우개 버튼**은 CDP 의 펜으로는 재현되지 않는다.
