# web-api/19 — `passive` 와 스크롤 성능: 기본값이 바뀐 이유 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★ **이 편의 본체는 「행동으로 묻는 passive 판정」이다** — 리스너의 `passive` 값을 **읽는 API 가 없으므로**, 리스너 안에서 `preventDefault()` 를 불러 **`defaultPrevented` 가 바뀌나**로 묻는다(제5의 상태). 여기에 **진짜 휠·진짜 터치에서 화면이 움직였나**를 한 칸 더 얹는다.\
> ★★★ **제목에 「성능」이 있지만 이 편은 시간도 프레임도 재지 않았다.** 「합성 스레드가 리스너를 기다려야 하나」는 **DOM 표준의 설명 절과 Chromium 쪽 기록을 인용**할 뿐이고, **이 머신에서 잰 것은 「passive 인가」와 「움직였나」뿐**이다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「2.8 Observing event listeners」·「default passive value」·「flatten more options」·「add an event listener」·「set the canceled flag」 절. Chromium 의 기록은 [chromestatus — Treat Document Level Touch Event Listeners as Passive](https://chromestatus.com/feature/5093566007214080) · [chromestatus — Treat Document Level Wheel/Mousewheel Event Listeners as Passive](https://chromestatus.com/feature/6662647093133312). 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. **휠과 터치는 CDP 로 넣은 진짜 입력**(`Input.dispatchMouseEvent` 의 `mouseWheel` · `Input.dispatchTouchEvent`)이고, 기본값 격자는 합성 이벤트로 물었다. 하네스는 [16번 주제](../16-event-propagation-phases/2-summary.md)의 (1)에 있다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md)(`preventDefault`·`cancelable`·`defaultPrevented`). **[15번 주제](../15-listener-registration/2-summary.md)의 (9)·(10)이 직접 선행**이다 — 그쪽이 합성 이벤트로 「`passive` 면 무시된다」와 기본값 10칸을 쟀고, 여기는 **나머지 칸 · 인자 꼴 · 진짜 입력 · 콘솔**을 잰다.\
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
| **안 흔들린다** | 기본값 격자 42칸 · 인자 꼴 9줄 · body 바꿔 끼우기 · 진짜 입력의 「불렸나 · `cancelable` · `defaultPrevented` · 움직였나」 · 콘솔 줄 수 · 섞인 리스너의 `cancelable` · 탭의 `click` 횟수 | 캡처 네 판이 **한 글자도 같았다** |
| **흔들릴 수 있어 안 실었다** | 스크롤한 **거리**(`scrollY` 의 숫자) | 터치는 끄는 속도에 따라 관성이 붙는다. 그래서 **「움직였나(예/아니오)」로만** 찍었다 |
| ★ **못 잰다** | **스크롤 지연 · 프레임 · 입력에서 화면까지의 시간** | 이 하네스는 **합성 스레드의 시간**을 보지 못한다. **안 돌려 본 것이 아니라 못 잰 것**이다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.
- ★ **스크롤이 끝났나**는 시간 상수로 기다리지 않았다 — **`scrollend` 이벤트**가 오면 끝, 안 오면(막힌 경우) **animation frame 30장**을 넘긴 뒤 끝이다. 이 편이 읽는 것은 **거리가 아니라 「0 인가 아닌가」** 라서 30장 안에 끝나지 않은 스크롤도 판정이 같다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | 리스너의 성질은 트리에 안 남는다 |
| 창 ② 노드 프로브 | ★ **쓴다** | `scrollY`·`scrollTop` 이 **0 에서 움직였나**((4)·(5)) |
| 창 ③ 같은 것을 두 번 읽기 | **부적용** | — |
| **창 ④ 디스패치 계수기 → 행동으로 묻는 passive 판정** | ★★ **본체** | `preventDefault()` 뒤 **`defaultPrevented` 가 `true` 로 바뀌나** — 바뀌면 passive 가 아니다 |
| **진짜 입력(CDP)** | ★ **쓴다 — 입력 쪽** | 진짜 휠 · 진짜 터치 끌기 |
| **창 ⑤ 콘솔(CDP `Log` 도메인)** | ★ **쓴다** | 막으려다 무시된 호출마다 **몇 줄이 남나**((6)) |

- ★★ **제5의 상태 — 「이 리스너가 passive 인가」를 옵션값이 아니라 행동으로 물었다.** 표준에 등록된 리스너의 옵션을 **읽는 표면이 없다**([15번 주제](../15-listener-registration/2-summary.md) — `EventTarget` 의 표면은 세 메서드뿐). 그래서 **리스너 안에서 `preventDefault()` 를 불러 보고 `defaultPrevented` 로 판정**했다. ★ 바꾼 창이 못 보는 것 — **`cancelable: false` 인 이벤트**에서는 passive 든 아니든 `defaultPrevented` 가 `false` 다. 그래서 격자는 **`cancelable: true` 로 만든 합성 이벤트**로만 던졌다.

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★ **스크롤 지연 · 프레임 드롭 · 입력 지연** | 합성 스레드(compositor)의 시간을 이 하네스가 못 본다. **이 편은 성능을 주장하지 않는다** |
| **리스너의 `passive` 값 자체** | 읽는 API 가 없다. 행동으로만 판정한다 |
| **콘솔에 안 남은 무시** | 기본 passive + 합성 이벤트는 **무시되는데 한 줄도 안 남았다**((6)) — 콘솔을 근거로 「무시가 없었다」를 말할 수 없다 |
| **진짜 손가락의 관성·핀치** | CDP 터치는 다섯 번에 나눠 끈 한 손가락뿐이다 |

## 한눈에 — 쉽게 말하면

**★ 스크롤은 「사람이 휠을 굴리자마자 화면을 미는 일꾼(합성 스레드)」과 「리스너를 돌리는 사무실(메인 스레드)」 둘이 한다. 리스너가 「막을 수도 있다」고 하면 일꾼은 사무실의 답을 기다려야 한다. `passive: true` 는 「안 막을 테니 기다리지 마」라는 약속이다.**

| 비유 | 실체 |
|---|---|
| **화면을 미는 일꾼** | 합성 스레드 — 스크롤을 그린다 |
| **사무실** | 메인 스레드 — 자바스크립트 리스너가 돈다 |
| 「막을 수도 있다」는 **결재 대기** | `passive: false` 인 `touchstart`/`touchmove`/`wheel` 리스너 |
| 「**안 막겠다**」는 약속 | `passive: true` |
| 약속을 어기고 「막아」라고 하면 | `preventDefault()` 가 **조용히 무시**된다 |
| **회사가 정한 기본 규칙** | `window`·`document`·`html`·`body` 의 네 종류는 **옵션을 안 적으면 약속한 것으로 친다** |
| 결재가 필요 없다고 **미리 알리는 표지판** | CSS `touch-action` — 자바스크립트 없이 「이 상자에서는 끌어도 스크롤하지 마」 |

- ★ **기본값이 바뀐 이유** — 페이지 **전체**에 단 리스너(`document` 등)는 **모든 스크롤**을 결재 대기에 묶는다. 그런데 그런 리스너 대부분이 **실제로는 안 막는다**(분석 코드 등). 그래서 **그 네 자리만** 기본을 「약속한 것」으로 바꿨다.
- ★ **이 비유의 「기다린다」는 이 편이 잰 것이 아니다** — 명세 설명 절과 Chromium 기록의 서술이다.

```text
   진짜 휠 한 번 — 누가 무엇을 기다리나 (명세 설명 절의 모형 · 이 편은 시간을 안 쟀다)

   사람의 휠 ──▶ 합성 스레드
                   │
                   ├─ 막을 수 있는 리스너가 있다(passive 아님)
                   │     └─▶ 메인 스레드에 wheel 을 보내고 답을 기다린다
                   │           └─ preventDefault 면 스크롤 안 함 / 아니면 스크롤
                   │
                   └─ 리스너가 전부 passive 다
                         └─▶ 곧바로 스크롤하고, wheel 은 cancelable: false 로 보낸다
```

## 이 주제가 답하려는 질문

1. **`touchstart`/`wheel` 리스너가 스크롤을 왜 지연시킬 수 있나** — 무엇이 무엇을 기다리나.
2. **옵션을 안 적었을 때 어디서 `passive` 가 되나** — 그리고 그것은 명세인가 구현인가.
3. **`passive` 에서 `preventDefault()` 를 부르면 무엇이 일어나고, 그것이 어디에 드러나나** — 반환값·`cancelable`·화면·콘솔.

## 동작 방식

### (1) ★★★ 본체 — 옵션을 생략했을 때의 기본값 격자 42칸

**언제 쓰나** — 「나는 `passive` 를 쓴 적이 없는데 `preventDefault()` 가 안 먹는다」일 때.

**던진 것** — 대상 일곱 × 이벤트 여섯에 **옵션 없이** 리스너를 달고, `cancelable: true` 인 합성 이벤트를 던져 `preventDefault()` 뒤의 `defaultPrevented` 를 읽었다. [15번 주제](../15-listener-registration/2-summary.md)의 (10)이 **10칸**을 쟀고 **「?」로 남긴 칸**을 여기서 채운다. 아래 (2)·(3)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa16b-19-default.html -->
<!doctype html>
<meta charset="utf-8">
<title>19-default</title>
<div id="보통">보통 요소</div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const O = [];
// passive 인지 아닌지는 옵션값을 읽을 창구가 없다 — preventDefault 를 불러 defaultPrevented 가 바뀌는지로 묻는다
const 묻기 = (대상, 형, 옵션) => {
  let 답 = null;
  const h = e => { e.preventDefault(); 답 = e.defaultPrevented; };
  if (옵션 === '생략') 대상.addEventListener(형, h); else 대상.addEventListener(형, h, 옵션);
  대상.dispatchEvent(new Event(형, { cancelable: true }));
  대상.removeEventListener(형, h, typeof 옵션 === 'object' || typeof 옵션 === 'boolean' ? 옵션 : undefined);
  return 답 === null ? '안 불림' : 답 ? 'O' : 'P';
};

const 대상 = [['window', window], ['document', document], ['html', document.documentElement],
              ['body', document.body], ['body 안의 div', document.getElementById('보통')],
              ['떼어 둔 div', document.createElement('div')], ['head', document.head]];
const 형들 = ['touchstart', 'touchmove', 'touchend', 'wheel', 'mousewheel', 'click'];
O.push('가. 옵션을 생략하고 달았을 때 — P = preventDefault 가 무시됨 · O = 먹힘');
O.push(padw('', 16) + 형들.map(t => padw(t, 12)).join(''));
let 무시 = 0, 전체 = 0;
for (const [라벨, t] of 대상) {
  const 칸 = 형들.map(형 => 묻기(t, 형, '생략'));
  칸.forEach(c => { 전체++; if (c === 'P') 무시++; });
  O.push(padw(라벨, 16) + 칸.map(c => padw(c, 12)).join(''));
}
O.push('');
O.push('preventDefault 가 무시된 칸 = ' + 무시 + ' / ' + 전체);
O.push('');

O.push('나. 세 번째 인자를 여러 꼴로 — wheel 이벤트');
const 꼴들 = [['생략', '생략'], ['false', false], ['true', true], ['{}', {}], ['{ capture: true }', { capture: true }],
              ['{ passive: undefined }', { passive: undefined }], ['{ once: true }', { once: true }],
              ['{ passive: false }', { passive: false }], ['{ passive: true }', { passive: true }]];
O.push(padw('세 번째 인자', 26) + padw('window', 10) + 'body 안의 div');
let 갈림 = 0;
for (const [라벨, 옵션] of 꼴들) {
  const a = 묻기(window, 'wheel', 옵션), b = 묻기(document.getElementById('보통'), 'wheel', 옵션);
  if (a !== b) 갈림++;
  O.push(padw(라벨, 26) + padw(a, 10) + b);
}
O.push('');
O.push('window 와 div 가 갈린 줄 = ' + 갈림 + ' / ' + 꼴들.length);
O.push('');

O.push('다. 달 때의 대상이 정하나 던질 때의 대상이 정하나 — body 를 바꿔 끼운다');
const 원래몸 = document.body;
let 답1 = null;
원래몸.addEventListener('wheel', e => { e.preventDefault(); 답1 = e.defaultPrevented; });
const 새몸 = document.createElement('body');
document.documentElement.replaceChild(새몸, 원래몸);
원래몸.dispatchEvent(new Event('wheel', { cancelable: true }));
O.push('  ① 문서의 body 일 때 달고 → 떼어 낸 뒤 던지면     defaultPrevented = ' + 답1
     + '  (던질 때 document.body === 그 요소 ? ' + (document.body === 원래몸) + ')');
const 또새몸 = document.createElement('body');
let 답2 = null;
또새몸.addEventListener('wheel', e => { e.preventDefault(); 답2 = e.defaultPrevented; });
document.documentElement.replaceChild(또새몸, 새몸);
또새몸.dispatchEvent(new Event('wheel', { cancelable: true }));
O.push('  ② 떼어 둔 채 달고 → 문서의 body 로 끼운 뒤 던지면 defaultPrevented = ' + 답2
     + '  (던질 때 document.body === 그 요소 ? ' + (document.body === 또새몸) + ')');
document.documentElement.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

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

- ★★ **무시된 칸은 16 / 42** — **`window`·`document`·`html`·`body` 네 대상 × `touchstart`·`touchmove`·`wheel`·`mousewheel` 네 이벤트**다. 사각형 하나로 딱 떨어진다.
- **같은 네 대상이라도 `touchend`·`click` 은 먹힌다** — 스크롤을 시작·진행하는 이벤트가 아니다.
- **`body` 안의 `div` · 떼어 둔 `div` · `head` 는 전부 먹힌다** — **「문서 수준」이 아니면** 기본이 passive 가 아니다.
- ★ [15번 주제](../15-listener-registration/2-summary.md)의 표에서 **「?」였던 칸**(`document`·`body`·`html` 의 `touchmove`·`wheel`·`mousewheel`, 평범한 요소의 `touchmove`·`mousewheel`)이 **전부 사각형의 규칙대로** 나왔다.

```text
   ★ 기본값이 passive 인 칸 — 이 판 42칸 전수

                   touchstart  touchmove  touchend  wheel  mousewheel  click
   window             P           P          -        P        P         -
   document           P           P          -        P        P         -
   html               P           P          -        P        P         -
   body               P           P          -        P        P         -
   body 안의 div      -           -          -        -        -         -
   떼어 둔 div        -           -          -        -        -         -
   head               -           -          -        -        -         -

   P = preventDefault 가 무시됨(기본이 passive)    - = 먹힘
```

**명세가 정한 절차** — 이 사각형은 **DOM 표준 본문에 있다.**

```text
   DOM 「default passive value」(type, eventTarget)

   다음이 전부 참이면 true
     · type 이 "touchstart" · "touchmove" · "wheel" · "mousewheel" 중 하나
     · eventTarget 이 Window 이거나
       node document 가 eventTarget 인 노드가 있는(= Document) 것이거나
       node document 의 document element 이거나(= html)
       node document 의 body element 이거나(= body)
   아니면 false

   DOM 「add an event listener」
     listener 의 passive 가 null 이면 default passive value 로 채운다
```

### (2) ★★ 세 번째 인자의 꼴 — `false` 를 적어도 passive 다

**언제 쓰나** — 「옛날 코드에 `addEventListener('wheel', f, false)` 라고 명시했으니 괜찮겠지」일 때.

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

- ★★ **`window` 에서는 `{ passive: false }` 한 줄만 먹힌다.** **`false`·`true`·`{}`·`{ capture: true }`·`{ passive: undefined }`·`{ once: true }`** 는 전부 **기본이 passive** 다.
- ★ **`false` 는 `capture` 다** — 세 번째 인자가 불리언이면 **`capture` 로만** 읽힌다([15번 주제](../15-listener-registration/2-summary.md)의 동일성 격자). `passive` 는 **안 적은 것**이 된다.
- ★ **`{ passive: undefined }` 도 안 적은 것처럼** 굴었다 — 명세의 flatten more options 는 「`passive` **가 있으면**」 그 값을 쓴다. `undefined` 를 준 멤버가 「없는 것」으로 읽힌 것은 **이 판의 결과**이고, 그 규칙을 정하는 WebIDL 의 사전 변환 절은 **열어 확인하지 않았다.**
- **`div` 에서는 `{ passive: true }` 만 무시**된다 — 7 / 9 줄이 `window` 와 갈렸다.

```text
   passive 가 정해지는 길 — DOM 「flatten more options」 + 「add an event listener」

   세 번째 인자              passive 칸      문서 수준 대상이면
   생략                      null      ─┐
   false / true              null       │
   {}                        null       ├─▶  default passive value  ─▶  true
   { capture: true }         null       │
   { once: true }            null       │
   { passive: undefined }    null      ─┘
   { passive: false }        false     ───────────────────────────▶  false
   { passive: true }         true      ───────────────────────────▶  true

   ★ 되돌리는 유일한 꼴은 { passive: false } 를 「적는 것」이다
```

### (3) 달 때 정해진다 — body 를 바꿔 끼우면

**언제 쓰나** — 「`body` 를 갈아 끼우는 SPA 에서 리스너가 이상하다」일 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa16b-19-default.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '27,29p'
다. 달 때의 대상이 정하나 던질 때의 대상이 정하나 — body 를 바꿔 끼운다
  ① 문서의 body 일 때 달고 → 떼어 낸 뒤 던지면     defaultPrevented = false  (던질 때 document.body === 그 요소 ? false)
  ② 떼어 둔 채 달고 → 문서의 body 로 끼운 뒤 던지면 defaultPrevented = true  (던질 때 document.body === 그 요소 ? true)
(exit 0)
```

- ★ **① 문서의 `body` 일 때 달면 passive** 이고, **떼어 낸 뒤에도 passive 로 남는다**(`defaultPrevented = false`).
- ★ **② 떼어 둔 채 달면 passive 가 아니고**, **문서의 `body` 로 끼운 뒤에도 그대로다**(`true`).
- 명세 그대로다 — `passive` 는 **add an event listener 때 한 번** 채워지고, 던질 때 다시 계산하지 않는다.

```text
   passive 는 등록 순간에 굳는다

   ① body(문서의 것) 에 addEventListener  ──▶ passive = true 로 굳음
      replaceChild 로 떼어 냄              ──▶ 여전히 true

   ② 떼어 둔 <body> 에 addEventListener    ──▶ passive = false 로 굳음
      문서의 body 로 끼움                  ──▶ 여전히 false
```

### (4) ★★★ 진짜 휠 — 화면이 움직였나, 그리고 `cancelable` 이 바뀐다

**언제 쓰나** — 「합성 이벤트로는 `cancelable: true` 인데 실제 휠에서는?」일 때.

**던진 것** — 높이 3000px 문서와 안쪽 스크롤 상자. 리스너는 **`preventDefault()` 를 부른다.** 진짜 휠을 **아래로 100** 한 번 굴리고, 문서(`scrollY`)와 상자(`scrollTop`)가 0 에서 움직였나를 본다. 매 판 스크롤을 0 으로 돌리고 리스너를 뗀다. 아래 (5)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa16b-19-real.html -->
<!doctype html>
<meta charset="utf-8">
<title>19-real</title>
<style>
  body { margin: 0; height: 3000px; }
  #상자 { position: absolute; left: 500px; top: 100px; width: 300px; height: 200px; overflow: auto; }
  #상자 > div { height: 2000px; }
  #빈곳 { position: absolute; left: 100px; top: 100px; width: 200px; height: 200px; }
  #잠금 { position: absolute; left: 100px; top: 400px; width: 200px; height: 200px; touch-action: none; }
</style>
<div id="빈곳">문서 위의 한 점</div>
<div id="상자"><div>안쪽 스크롤 상자</div></div>
<div id="잠금">touch-action: none 인 상자</div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 줄 = [];
let 판 = null, 뗄것 = null;
const 리스너 = e => {
  판.불림++;
  e.preventDefault();
  if (판.cancelable === '-') { 판.cancelable = e.cancelable; 판.defaultPrevented = e.defaultPrevented; }
};

// 스크롤이 끝났나를 이벤트로 기다린다 — scrollend 가 오면 끝, 안 오면 animation frame 30장을 넘긴 뒤 끝
const 가라앉기 = () => new Promise(r => {
  let 끝 = false, n = 0;
  const 끝내기 = () => { if (!끝) { 끝 = true; r(1); } };
  addEventListener('scrollend', 끝내기, { once: true });
  $('상자').addEventListener('scrollend', 끝내기, { once: true });
  const 한장 = () => { if (끝) return; if (++n >= 30) 끝내기(); else requestAnimationFrame(한장); };
  requestAnimationFrame(한장);
});

window.__준비 = (어디, 형, 옵션) => {
  scrollTo(0, 0); $('상자').scrollTop = 0;
  판 = { 불림: 0, cancelable: '-', defaultPrevented: '-' };
  const t = 어디 === 'document' ? document : 어디 === 'window' ? window : 어디 === '#상자' ? $('상자') : null;
  if (t) { 옵션 === '생략' ? t.addEventListener(형, 리스너) : t.addEventListener(형, 리스너, 옵션); 뗄것 = [t, 형]; }
  return 가라앉기();
};
window.__적기 = 라벨 => {
  줄.push([라벨, 판.불림 > 0 ? '예' : '아니오', 판.cancelable, 판.defaultPrevented,
           scrollY > 0 ? '예' : '아니오', $('상자').scrollTop > 0 ? '예' : '아니오']);
  if (뗄것) { 뗄것[0].removeEventListener(뗄것[1], 리스너); 뗄것 = null; }
  return 1;
};
// [라벨, 입력, 리스너를 단 곳, 이벤트, 옵션, 입력을 넣을 곳]
const 판들 = [
  ['휠 · 리스너 없음', 'wheel', '없음', 'wheel', '생략', '#빈곳'],
  ['휠 · document · 생략', 'wheel', 'document', 'wheel', '생략', '#빈곳'],
  ['휠 · document · { passive: false }', 'wheel', 'document', 'wheel', { passive: false }, '#빈곳'],
  ['휠 · window · 생략', 'wheel', 'window', 'wheel', '생략', '#빈곳'],
  ['휠 · 상자 위 · 리스너 없음', 'wheel', '없음', 'wheel', '생략', '#상자'],
  ['휠 · #상자 · 생략', 'wheel', '#상자', 'wheel', '생략', '#상자'],
  ['휠 · #상자 · { passive: true }', 'wheel', '#상자', 'wheel', { passive: true }, '#상자'],
  ['휠 · document 의 scroll 리스너 · 생략', 'wheel', 'document', 'scroll', '생략', '#빈곳'],
  ['터치 · 리스너 없음', 'touch', '없음', 'touchmove', '생략', '#빈곳'],
  ['터치 · document touchmove · 생략', 'touch', 'document', 'touchmove', '생략', '#빈곳'],
  ['터치 · document touchmove · { passive: false }', 'touch', 'document', 'touchmove', { passive: false }, '#빈곳'],
  ['터치 · document touchstart · { passive: false }', 'touch', 'document', 'touchstart', { passive: false }, '#빈곳'],
  ['터치 · touch-action: none 위 · 리스너 없음', 'touch', '없음', 'touchmove', '생략', '#잠금'],
];
const 단계 = [];
for (const [라벨, 입력, 어디, 형, 옵션, 선택자] of 판들) {
  단계.push(['js', `__준비(${JSON.stringify(어디)}, ${JSON.stringify(형)}, ${JSON.stringify(옵션)})`]);
  단계.push([입력, 선택자, 100]);
  단계.push(['js', '가라앉기()']);
  단계.push(['js', `__적기(${JSON.stringify(라벨)})`]);
}
window.__단계 = 단계;
window.__끝 = () => {
  const O = [];
  O.push('진짜 입력 한 번 — 리스너는 preventDefault 를 부른다 (cancelable · defaultPrevented 는 첫 호출의 값)');
  O.push(padw('입력 · 리스너를 단 곳 · 옵션', 50) + padw('불림', 8) + padw('cancelable', 12) + padw('defaultPrevented', 18)
       + padw('문서가 움직였나', 16) + '상자가 움직였나');
  for (const r of 줄) O.push(padw(r[0], 50) + padw(r[1], 8) + padw(String(r[2]), 12) + padw(String(r[3]), 18) + padw(r[4], 16) + r[5]);
  const 불린 = 줄.filter(r => r[1] === '예');
  O.push('');
  O.push('리스너가 불린 줄 가운데 문서나 상자가 움직인 줄 = ' + 불린.filter(r => r[4] === '예' || r[5] === '예').length + ' / ' + 불린.length);
  return O.join('\n');
};
</script>
```

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

- **리스너 없음** — 문서 위에서 굴리면 **문서가**, 상자 위에서 굴리면 **상자가** 움직였다(대조군).
- ★★ **`document` · 생략 / `window` · 생략 — 리스너가 불렸고 `preventDefault()` 를 불렀는데 문서가 움직였다.** 리스너 안의 **`cancelable` 이 `false`** 였다.
- ★ **`document` · `{ passive: false }` — 안 움직였다.** `cancelable` 이 **`true`**, `defaultPrevented` 가 **`true`**.
- **`#상자` · 생략 — 안 움직였다**(상자는 문서 수준이 아니므로 기본이 passive 가 아니다). **`#상자` · `{ passive: true }` — 움직였다.**
- ★ **`scroll` 리스너의 `preventDefault()` 는 아무것도 못 막는다** — `cancelable` 이 `false` 이고 문서는 움직였다. **`scroll` 은 이미 일어난 스크롤을 알리는 이벤트**다.

```text
   ★ 합성과 진짜가 갈리는 칸 — passive 리스너 안의 e.cancelable

                                   합성 (15번 주제)          진짜 휠 (이 편)
   passive 리스너 안 cancelable    true  (내가 true 로 만듦)  false
   defaultPrevented                false                     false
   화면                            (이 편은 안 던졌다)        움직였다

   DOM 2.8 의 설명: 리스너가 전부 passive 면 스크롤을 먼저 시작하고
                    「이벤트를 uncancelable 로 만들 수 있다」
```

- ★ **그래서 진짜 입력에서는 「`cancelable` 을 보고 막을 수 있나 판정」이 맞게 된다** — 합성 이벤트([15번 주제](../15-listener-registration/2-summary.md))에서는 그것이 틀렸다. **같은 코드의 답이 입력 종류에 따라 갈린다.** [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md)의 「막을 수 있나(`cancelable`)와 막혔나(`defaultPrevented`)는 다르다」가 합성 쪽의 이야기다.

### (5) ★★ 진짜 터치 — `touchmove` 기본 passive 와 `touch-action`

**언제 쓰나** — 모바일에서 「끌기로 그림을 옮기는데 페이지가 같이 스크롤된다」일 때.

**던진 것** — 문서 위의 한 점에 손가락을 대고 **위로 100 을 다섯 번에 나눠** 끈 뒤 뗐다. 마지막 줄은 리스너 없이 **`touch-action: none` 인 상자** 위에서 끌었다.

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

- **리스너 없음** — 문서가 움직였다.
- ★★ **`document` 의 `touchmove` · 생략 — 불렸고 막으려 했는데 문서가 움직였다**(`cancelable: false`). 휠과 같은 모양이다.
- **`touchmove` · `{ passive: false }` — 안 움직였다**(`cancelable: true` · `defaultPrevented: true`).
- ★ **`touchstart` · `{ passive: false }` 에서 막아도 안 움직였다** — 스크롤은 **시작 단계에서** 막을 수 있다.
- ★★ **`touch-action: none` 인 상자 위에서는 리스너가 하나도 없는데 안 움직였다.** 자바스크립트 없이 **CSS 한 줄로** 「여기서는 끌어도 스크롤하지 마」를 **미리** 알린 것이다 — **메인 스레드에 묻지 않아도 되는 표지판**이다.
- 마지막 줄 **「리스너가 불린 줄 가운데 움직인 줄 = 5 / 9」** — `preventDefault()` 를 불렀는데도 움직인 줄이 **다섯**이다(passive 로 무시된 넷 + `scroll`).

```text
   끌어도 스크롤하지 않게 하는 두 길

   ① 자바스크립트: touchmove 리스너 { passive: false } + preventDefault()
        └─ 합성 스레드가 매번 메인 스레드의 답을 기다려야 한다(명세 설명 절의 모형)

   ② CSS: touch-action: none   (그 상자에만)
        └─ 리스너 없이 미리 선언 — 이 판에서 리스너 0개로 안 움직였다

   ★ 가능하면 ② — 막을 자리를 CSS 로 좁히고, 리스너는 passive 로 둔다
```

- CSS 갈래에는 **`touch-action` 을 다룬 편이 없다.** 스크롤 컨테이너 자체의 정본은 CSS 갈래 [23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)(`overflow`·`overscroll-behavior`)다.

### (6) ★★ 콘솔 — 무시될 때마다 한 줄인가

**언제 쓰나** — 「콘솔에 경고가 없으니 passive 문제는 없다」고 읽으려 할 때.

**던진 것** — passive 리스너 안에서 `preventDefault()` 를 부르는 네 칸, **칸마다 네 번**. 주소의 `#1`\~`#4` 로 **한 칸씩 따로** 열어 CDP `Log` 도메인에 남은 줄을 셌다.

```html
<!-- wa16b-19-console.html -->
<!doctype html>
<meta charset="utf-8">
<title>19-console</title>
<style>
  body { margin: 0; height: 3000px; }
  #상자 { position: absolute; left: 500px; top: 100px; width: 300px; height: 200px; overflow: auto; }
  #상자 > div { height: 2000px; }
  #빈곳 { position: absolute; left: 100px; top: 100px; width: 200px; height: 200px; }
</style>
<div id="빈곳">문서 위의 한 점</div>
<div id="상자"><div>안쪽 스크롤 상자</div></div>
<script>
const $ = id => document.getElementById(id);
const 센것 = { 문서진짜: 0, 문서합성: 0, 상자진짜: 0, 상자합성: 0 };
document.addEventListener('wheel', e => { if (!$('상자').contains(e.target)) { 센것[e.isTrusted ? '문서진짜' : '문서합성']++; e.preventDefault(); } });
$('상자').addEventListener('wheel', e => { 센것[e.isTrusted ? '상자진짜' : '상자합성']++; e.preventDefault(); }, { passive: true });

// 스크롤이 끝났나를 이벤트로 기다린다 — scrollend 가 오면 끝, 안 오면 animation frame 30장을 넘긴 뒤 끝
const 가라앉기 = () => new Promise(r => {
  let 끝 = false, n = 0;
  const 끝내기 = () => { if (!끝) { 끝 = true; r(1); } };
  addEventListener('scrollend', 끝내기, { once: true });
  $('상자').addEventListener('scrollend', 끝내기, { once: true });
  const 한장 = () => { if (끝) return; if (++n >= 30) 끝내기(); else requestAnimationFrame(한장); };
  requestAnimationFrame(한장);
});
window.__처음으로 = () => { scrollTo(0, 0); $('상자').scrollTop = 0; return 가라앉기(); };
// 주소의 #1 ~ #4 로 한 칸만 돌린다(콘솔 줄을 칸마다 따로 세려고). 없으면 넷 다.
const 칸 = location.hash.slice(1);
const 할것 = k => 칸 === '' || 칸 === k;
const 단계 = [];
if (할것('1')) for (let i = 0; i < 4; i++) 단계.push(['js', '__처음으로()'], ['wheel', '#빈곳', 100], ['js', '가라앉기()']);
if (할것('2')) for (let i = 0; i < 4; i++) 단계.push(['js', '__처음으로()'], ['wheel', '#상자', 100], ['js', '가라앉기()']);
if (할것('3')) 단계.push(['js', "for (let i = 0; i < 4; i++) $('빈곳').dispatchEvent(new WheelEvent('wheel', { cancelable: true, bubbles: true })); 1"]);
if (할것('4')) 단계.push(['js', "for (let i = 0; i < 4; i++) $('상자').dispatchEvent(new WheelEvent('wheel', { cancelable: true })); 1"]);
window.__단계 = 단계;
window.__끝 = () => ['passive 리스너 안에서 preventDefault 를 부른 횟수 (부른 순서대로)',
  '  ① document · 생략            · 진짜 휠   ' + 센것.문서진짜,
  '  ② #상자   · { passive: true } · 진짜 휠   ' + 센것.상자진짜,
  '  ③ document · 생략            · 합성 휠   ' + 센것.문서합성,
  '  ④ #상자   · { passive: true } · 합성 휠   ' + 센것.상자합성].join('\n');
</script>
```

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

- **① 기본 passive + 진짜 휠 — 네 번에 네 줄**, 출처가 **`intervention`**(개입)이고 문구가 「**target being treated as passive**」다. Chrome 이 **스스로 이것을 개입이라고 부른다.**
- **② 명시 `{ passive: true }` + 진짜 휠 — 네 번에 네 줄**, 출처 `javascript`.
- ★★★ **③ 기본 passive + 합성 휠 — 네 번 무시됐는데 0 줄이다.** 경고가 **아예 안 남는다.**
- **④ 명시 `{ passive: true }` + 합성 휠 — 네 번에 네 줄.**
- ★ **「발생마다 한 줄이 아니다」의 정체** — [15번 주제](../15-listener-registration/2-summary.md)의 (9)는 「여덟 번 부른 `preventDefault` 가 **두 줄**로만 남았다 — Chrome 이 **합친다**」로 적었다. **같은 페이지를 이 하네스로 다시 열었다.**

```text
$ python3 wa16b-cdp.py log wa12b-15-passive.html
javascript · error · Unable to preventDefault inside passive event listener invocation.
javascript · error · Unable to preventDefault inside passive event listener invocation.
(Log 도메인 항목 2 줄)
(exit 0)
```

- **두 줄은 그 페이지의 14행 리스너(명시 `{ passive: true }`)가 두 번 불린 것**과 맞는다 — 한 번은 첫 디스패치, 한 번은 같은 `#상자` 에 `wheel` 을 던진 격자 줄에서다. **나머지 호출은 전부 ③ 칸(기본 passive + 합성)** 이라 **한 줄도 안 남았다.** 이 판에서는 **합치는 것이 아니라 ③ 칸이 침묵하는 것**이었다.
- ★ **그래서 콘솔은 「무시가 있었다」의 근거는 되지만 「없었다」의 근거는 못 된다.** 합성 이벤트로 짠 테스트에서는 **기본 passive 의 무시가 콘솔에 안 보인다.**

```text
   무시될 때 콘솔에 남나 — 네 칸(칸마다 4번)

                         진짜 휠                     합성 휠
   기본 passive(생략)    4줄  intervention           ★ 0줄
   명시 { passive:true } 4줄  javascript             4줄  javascript
```

### (7) passive 와 비passive 가 섞이면 · `touchstart` 를 막으면 탭이 사라진다

**언제 쓰나** — 「`passive` 를 붙였는데 왜 여전히 `cancelable` 이 `true` 로 오지?」·「터치 스크롤을 막았더니 단추가 안 눌린다」일 때.

```html
<!-- wa16b-19-more.html -->
<!doctype html>
<meta charset="utf-8">
<title>19-more</title>
<style>
  body { margin: 0; height: 3000px; }
  #빈곳 { position: absolute; left: 100px; top: 100px; width: 200px; height: 200px; }
  #단추 { position: absolute; left: 500px; top: 100px; width: 200px; height: 100px; }
</style>
<div id="빈곳">문서 위의 한 점</div>
<button id="단추">단추</button>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const O = [];
const 가라앉기 = () => new Promise(r => {
  let 끝 = false, n = 0;
  const 끝내기 = () => { if (!끝) { 끝 = true; r(1); } };
  addEventListener('scrollend', 끝내기, { once: true });
  const 한장 = () => { if (끝) return; if (++n >= 30) 끝내기(); else requestAnimationFrame(한장); };
  requestAnimationFrame(한장);
});
window.__처음으로 = () => { scrollTo(0, 0); return 가라앉기(); };

// 가: 한 대상에 passive(생략) 리스너와 비passive 리스너를 같이 달면
let 가판 = null;
const A = e => { 가판.A = e.cancelable; e.preventDefault(); 가판.A2 = e.defaultPrevented; };
const B = e => { 가판.B = e.cancelable; };
window.__가준비 = 둘 => { 가판 = {}; document.addEventListener('wheel', A); if (둘) document.addEventListener('wheel', B, { passive: false }); return __처음으로(); };
window.__가적기 = 라벨 => {
  O.push('  ' + padw(라벨, 40) + 'A 안 cancelable=' + 가판.A + ' · A 뒤 defaultPrevented=' + 가판.A2
       + (가판.B !== undefined ? ' · B 안 cancelable=' + 가판.B : '') + ' · 문서가 움직였나=' + (scrollY > 0 ? '예' : '아니오'));
  document.removeEventListener('wheel', A); document.removeEventListener('wheel', B); return 1;
};

// 나: touchstart 를 막으면 탭의 click 이 오나
let 나판 = null;
const 막기 = e => { e.preventDefault(); 나판.막음 = e.defaultPrevented; };
$('단추').addEventListener('click', () => { if (나판) 나판.click++; });
window.__나준비 = 막 => { 나판 = { click: 0, 막음: '-' }; if (막) document.addEventListener('touchstart', 막기, { passive: false }); return 1; };
window.__나적기 = 라벨 => { O.push('  ' + padw(라벨, 40) + 'touchstart 의 defaultPrevented=' + 나판.막음 + ' · 단추 click=' + 나판.click + '번');
  document.removeEventListener('touchstart', 막기, { passive: false }); 나판 = null; return 1; };

window.__단계 = [
  ['js', "O.push('가. document 에 wheel 리스너 A(생략 — 기본 passive, preventDefault 부름) · B({ passive: false }, 아무것도 안 함) — 진짜 휠'); 1"],
  ['js', '__가준비(false)'], ['wheel', '#빈곳', 100], ['js', '가라앉기()'], ['js', "__가적기('A 만')"],
  ['js', '__가준비(true)'], ['wheel', '#빈곳', 100], ['js', '가라앉기()'], ['js', "__가적기('A + B')"],
  ['js', "O.push('나. 단추를 손가락으로 탭(대고 뗌) — document 의 touchstart 리스너가 막으면'); 1"],
  ['js', '__나준비(false)'], ['tap', '#단추'], ['js', 'new Promise(r => { let n = 0; const f = () => { if (++n >= 10) r(1); else requestAnimationFrame(f); }; requestAnimationFrame(f); })'], ['js', "__나적기('touchstart 리스너 없음')"],
  ['js', '__나준비(true)'], ['tap', '#단추'], ['js', 'new Promise(r => { let n = 0; const f = () => { if (++n >= 10) r(1); else requestAnimationFrame(f); }; requestAnimationFrame(f); })'], ['js', "__나적기('touchstart { passive: false } 에서 막음')"],
];
window.__끝 = () => O.join('\n');
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-19-more.html | sed -n '1,3p'
가. document 에 wheel 리스너 A(생략 — 기본 passive, preventDefault 부름) · B({ passive: false }, 아무것도 안 함) — 진짜 휠
  A 만                                    A 안 cancelable=false · A 뒤 defaultPrevented=false · 문서가 움직였나=예
  A + B                                   A 안 cancelable=true · A 뒤 defaultPrevented=false · B 안 cancelable=true · 문서가 움직였나=예
(exit 0)
```

- ★★ **A 만 있을 때 — A 안의 `cancelable` 이 `false`**((4)와 같다).
- ★★ **아무것도 안 하는 비passive 리스너 B 를 하나 더 달자 — A 안의 `cancelable` 도 `true` 로 바뀌었다.** 진짜 휠이 **「막힐 수도 있는 이벤트」로** 보내진 것이다. A 는 여전히 passive 라 `preventDefault()` 가 무시됐고(`defaultPrevented=false`), B 는 막지 않았으므로 문서는 움직였다.
- ★ **이것이 DOM 2.8 절의 모형이 말하는 자리다** — 「**비passive 리스너가 하나도 없을 때만** uncancelable 로 보낼 수 있다」. 모형대로 읽으면 B 하나 때문에 **브라우저가 리스너의 답을 기다리는 쪽으로** 돌아갔다는 뜻이다. ★ **기다린 시간은 재지 않았다** — 이 편이 본 것은 **`cancelable` 이라는 표지**뿐이다.

```text
   리스너 하나가 모두의 이벤트를 바꾼다 — 진짜 휠의 cancelable

   document 의 wheel 리스너들          A 가 받은 cancelable
   A(생략 = passive)                   false   ← 전부 passive: 기다리지 않아도 된다
   A(생략) + B({ passive: false })     true    ← 하나라도 비passive: 기다려야 한다(모형)

   ★ 「passive: true 를 붙였다」는 그 리스너의 약속일 뿐이다 — 같은 이벤트의 다른 리스너가 깨면 소용없다
```

```text
$ python3 wa16b-cdp.py page wa16b-19-more.html | sed -n '4,6p'
나. 단추를 손가락으로 탭(대고 뗌) — document 의 touchstart 리스너가 막으면
  touchstart 리스너 없음                  touchstart 의 defaultPrevented=- · 단추 click=1번
  touchstart { passive: false } 에서 막음 touchstart 의 defaultPrevented=true · 단추 click=0번
(exit 0)
```

- ★ **`touchstart` 를 `{ passive: false }` 로 막자 탭의 `click` 이 0번**이 됐다. 막지 않으면 1번이었다.
- ★ **그래서 「스크롤을 막으려고 `touchstart` 에서 `preventDefault()`」는 그 영역의 탭(클릭)까지 죽인다.** 스크롤만 막고 싶으면 **`touchmove`** 에서 막거나 **`touch-action`** 을 쓴다((5)).

### (8) ★ 층을 가른다 — 명세 · Chrome 의 개입 · 이 판의 관찰

**언제 쓰나** — 「문서 수준 기본 passive 는 브라우저의 꼼수다」 또는 「표준이다」 중 무엇으로 적어야 하나.

- ★★ **지금은 DOM 표준 본문에 있다** — 「default passive value」 절이 (1)의 사각형을 그대로 정의한다(기준일에 열어 확인).
- ★ **출발은 Chrome 의 개입(intervention)이었다** — chromestatus 에 **터치 쪽이 Chrome 56**, **휠 쪽이 Chrome 73** 에 기본으로 켜졌다고 적혀 있다. 이 판의 콘솔도 출처를 **`intervention`** 으로 찍고 그 기록의 주소를 건다((6)).
- ★ **두 기록의 「표준화 상태」 칸은 아직 「인큐베이션」** 으로 남아 있다 — **표준 본문보다 늦게 갱신된 메타데이터**로 읽는다. 이 문서의 층 판정은 **표준 본문**을 따른다.
- **진짜 입력에서 `cancelable` 이 `false` 로 오는 것** — 명세는 2.8 절에서 「그렇게 **할 수 있다**」는 **설명**으로만 적는다. **그렇게 하는 것은 Chrome 의 구현**이고 이 편은 그것을 **관찰**했다((4)·(5)).
- ★★★ **「성능」은 이 편이 잰 것이 아니다.** chromestatus 의 휠 쪽 기록은 「**개입이 휠 스크롤의 입력부터 화면 반영까지의 지연을 5% 줄였다**」는 **Chromium 쪽 실험 결과**를 적는다 — **그들의 측정**이지 이 편의 측정이 아니다. 이 편은 그 수치를 **재현하지 않았다.**

```text
   세 층 — 이 편의 서술이 어디에 서 있나

   명세(DOM)        default passive value 의 사각형 · flatten more options · set the canceled flag
                    2.8 절의 설명(전부 passive 면 uncancelable 로 「할 수 있다」)
   ──────────────────────────────────────────────────────────────────
   Chrome 구현      개입으로 출발(터치 56 · 휠 73 — chromestatus)
                    진짜 입력에서 cancelable = false 로 보낸다
                    콘솔: intervention 출처 · ③ 칸은 침묵
                    「지연 5% 감소」— Chromium 의 실험(이 편이 재지 않음)
   ──────────────────────────────────────────────────────────────────
   이 판의 관찰     42칸 중 16칸 · 인자 꼴 7 / 9 · 등록 순간에 굳음
                    진짜 휠·터치에서 움직였나 · 콘솔 네 칸
                    비passive 하나가 끼면 cancelable 이 true · touchstart 막으면 탭 click 0
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   passive 를 정하는 꼴
     el.addEventListener('wheel', f, { passive: true })    막지 않겠다(무시되면 콘솔에 한 줄)
     el.addEventListener('wheel', f, { passive: false })   막을 수도 있다 — 문서 수준에서 되돌리는 유일한 꼴
     el.addEventListener('wheel', f)                        문서 수준이면 true · 아니면 false

   CSS 로 미리 알리는 꼴
     .끌기상자 { touch-action: none; }                     이 상자에서는 끌어도 스크롤하지 않는다

   막혔나 확인
     e.cancelable        진짜 입력에서는 「막을 수 있나」가 여기 드러난다
     e.defaultPrevented  실제로 막혔나
```

### 어디서 헷갈리나

- **`false` 를 세 번째 인자로 주면 `passive: false` 가 아니다** — `capture: false` 다((2)).
- **`passive` 는 동일성 키가 아니다** — 지울 때 안 적어도 된다([15번 주제](../15-listener-registration/2-summary.md)의 (3)).
- **`scroll` 리스너는 막는 자리가 아니다** — 이미 일어난 스크롤의 알림이다((4)).

## 어디서 틀리나

### 1. `document` 에 `wheel`·`touchmove` 리스너를 옵션 없이 달고 `preventDefault()` 로 스크롤을 막으려 한다

**안 막힌다**((1)·(4)·(5)). **`{ passive: false }` 를 명시**하거나, 막을 자리를 **그 요소**로 좁히거나, **`touch-action`** 을 쓴다.

### 2. `addEventListener('touchmove', f, false)` 로 「명시했다」고 믿는다

**`false` 는 `capture`** 다((2)). 문서 수준이면 여전히 passive 다.

### 3. `scroll` 리스너에서 `preventDefault()` 로 스크롤을 막으려 한다

**아무것도 못 막는다**((4)). `cancelable` 이 `false` 다.

### 4. 콘솔에 경고가 없으니 무시된 곳이 없다고 읽는다

**③ 칸(기본 passive + 합성)은 0 줄**이다((6)). 테스트에서는 특히 안 보인다.

### 5. 합성 이벤트로 짠 테스트의 `cancelable` 을 진짜 입력에서도 믿는다

**진짜 입력에서는 `cancelable` 이 `false` 로 온다**((4)). 합성은 **내가 준 값**일 뿐이다.

### 6. 「`passive: true` 를 붙였으니 빨라졌다」고 적는다

**이 편은 재지 않았다.** 빨라지는지는 **그 페이지에서 재야** 한다. 명세 설명 절의 모형에서 따라 나오는 것은 **「같은 이벤트에 비passive 리스너가 하나라도 남아 있으면 기다림이 남는다」** 까지다 — 그 크기는 이 편의 추론 밖이다.

### 7. `body` 를 갈아 끼우면 기본 passive 도 따라간다고 믿는다

**등록 순간에 굳는다**((3)).

### 8. 「내 리스너는 `passive: true` 니까 이 이벤트는 안 기다린다」고 믿는다

**같은 이벤트에 비passive 리스너가 하나라도 있으면** 진짜 휠이 `cancelable: true` 로 왔다((7)). 약속은 **리스너 하나의 것**이다.

### 9. 스크롤을 막으려고 `touchstart` 에서 `preventDefault()` 한다

**탭의 `click` 이 0번**이 됐다((7)). 스크롤만 막으려면 `touchmove` 나 `touch-action`.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `window`·`document`·`html`·`body` × 네 이벤트가 **옵션을 생략하면 passive** 인 것 | **명세**(DOM — default passive value) · 출발은 Chrome 의 개입(chromestatus) · **이 판도 42칸이 그대로였다**((1)) |
| 불리언 인자·`{}`·`{ passive: undefined }` 가 **passive 를 안 정한 것**으로 읽히는 것 | **명세**(DOM — flatten more options) |
| passive 가 **등록 순간에** 정해지는 것 | **명세**(DOM — add an event listener) · 이 판도 그랬다((3)) |
| passive 리스너 안의 `preventDefault()` 가 **아무것도 안 하는** 것 | **명세**(DOM — set the canceled flag) |
| 리스너가 전부 passive 면 **이벤트를 uncancelable 로 보내는** 것 | ★ **명세는 「할 수 있다」는 설명(2.8 절)** · **하는 것은 Chrome 의 구현** · 이 판에서 관찰((4)·(5)) — 비passive 가 하나 끼면 `cancelable` 이 `true` 로 돌아왔다((7)) |
| `touchstart` 를 막으면 **탭의 `click` 이 안 나는** 것 | ★ **이 판의 관찰**((7)) — 어느 명세 절이 그렇게 정하는지 이 문서는 확인하지 않았다 |
| 콘솔 경고의 **출처·문구·줄 수** · ③ 칸의 침묵 | ★ **구현.** Chrome 의 것이다((6)) |
| `touch-action: none` 이 리스너 없이 터치 스크롤을 막는 것 | ★ **CSS(Pointer Events 쪽) 명세의 몫**이고 이 문서는 **Chrome 151 의 관찰**로만 적는다((5)) |
| **스크롤 지연·성능 이득** | ★★ **재지 않았다.** 「5% 감소」는 **Chromium 의 실험**을 인용한 것이다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 스크롤을 읽기만 한다(분석·지연 로딩) | `{ passive: true }` · 또는 `scroll` 이벤트 | 옵션 없이 요소에 `wheel`·`touchmove` |
| 특정 상자에서 끌기를 스크롤 대신 쓴다 | 그 상자에 **`touch-action: none`** | `document` 에 비passive `touchmove` |
| 정말로 스크롤을 막아야 한다 | 그 요소에 `{ passive: false }` **명시** | 불리언 `false` · 옵션 생략 |
| 스크롤 위치에 반응한다 | `scroll`·`scrollend` · 관측 API | `wheel` 로 흉내 |
| 「막혔나」를 테스트한다 | **진짜 입력** · 또는 결과(`defaultPrevented`) | 합성의 `cancelable` · 콘솔 경고 유무 |

## 핵심 문장

1. **문서 수준 네 자리 × 스크롤 네 이벤트는 옵션을 생략하면 passive** 다 — 이 판 42칸 중 16칸, 사각형 하나.
2. **되돌리는 꼴은 `{ passive: false }` 를 적는 것뿐**이다 — 불리언 `false` 는 `capture` 다.
3. **passive 는 등록 순간에 굳는다.**
4. **진짜 휠·터치에서 passive 리스너는 `cancelable: false` 인 이벤트를 받고, 화면은 이미 움직인다.**
5. **`touch-action` 은 리스너 없이 미리 알리는 표지판**이다.
6. **콘솔은 「없었다」의 근거가 못 된다** — 기본 passive + 합성은 한 줄도 안 남았다.
7. **이 편은 성능을 재지 않았다** — 기다림의 모형은 명세 설명 절, 수치는 Chromium 의 실험이다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 19번)
- [15번 주제](../15-listener-registration/2-summary.md) — **「`passive` 면 `preventDefault` 가 무시된다」는 규칙과 기본값 10칸의 첫 측정.** 여기는 그 나머지 칸과 진짜 입력 · 콘솔의 정체
- [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md) — `preventDefault`·`cancelable`·`defaultPrevented` 의 정본
- [16번 주제](../16-event-propagation-phases/2-summary.md) — 진짜 입력 하네스 전문
- [11번 주제](../11-scroll-control/2-summary.md) — 스크립트로 스크롤을 **일으키는** 쪽(`scrollTo` 등)
- CSS 갈래 [23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md) — 스크롤 컨테이너와 `overscroll-behavior`. **`touch-action` 은 CSS 갈래에 편이 없다**
- [목록의 **23번 주제**](../23-pointer-events/)(포인터 이벤트) — 터치를 포인터로 받을 때의 `touch-action` 과 `pointercancel`
- [chromestatus 5093566007214080](https://chromestatus.com/feature/5093566007214080) · [chromestatus 6662647093133312](https://chromestatus.com/feature/6662647093133312) — 개입의 출발점과 Chromium 의 측정 서술

## 용어 풀이

- **`passive`** — 「이 리스너는 `preventDefault()` 를 안 부르겠다」는 약속. 어기면 조용히 무시된다.
- **default passive value** — 옵션에 `passive` 가 없을 때 DOM 이 채우는 값. 문서 수준 네 자리 × 네 이벤트면 `true`.
- **문서 수준 대상** — `window` · `document` · `document.documentElement`(html) · `document.body`.
- **합성 스레드(compositor thread)** — 스크롤과 일부 애니메이션을 메인 스레드와 따로 그리는 스레드. 이 편은 그 시간을 재지 않았다.
- **uncancelable** — `cancelable: false` 로 보내진 이벤트. 누가 `preventDefault()` 를 불러도 소용없다.
- **개입(intervention)** — 브라우저가 호환성을 조금 깨면서 기본 동작을 바꾸는 것. Chrome 의 콘솔이 출처를 이 이름으로 찍는다.
- **`touch-action`** — 요소 위의 터치가 **브라우저 기본 동작**(스크롤·확대)을 할지 CSS 로 미리 정하는 속성.
- **`scrollend`** — 스크롤이 끝났을 때 오는 이벤트. 이 편은 「스크롤이 끝났나」를 이것으로 기다렸다.
- **행동으로 묻는 passive 판정** — 옵션값을 못 읽으므로 `preventDefault()` 뒤 `defaultPrevented` 로 판정하는 관측. 이 편의 본체.

## 더 들어가면

- **성능 이득의 실제 크기**는 **재지 않았다.** 재려면 합성 스레드의 프레임 시간과 입력 지연을 보는 도구(성능 추적)가 필요하다 — 이 하네스 밖이다.
- **`pointer` 이벤트와 `touch-action` 의 관계**(`pointercancel`)는 [목록의 **23번 주제**](../23-pointer-events/) 몫이다.
- **`overscroll-behavior`**(당겨서 새로고침·스크롤 체이닝 막기)는 리스너 없이 스크롤의 **끝**을 다루는 CSS 다 — CSS 갈래 [23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md).
- **`iframe` 안의 문서 수준 대상**이 같은 규칙인지는 던지지 않았다.
