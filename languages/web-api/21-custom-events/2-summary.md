# web-api/21 — 커스텀 이벤트: `CustomEvent`·`dispatchEvent`·`detail`·`bubbles`/`composed` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 를 늘린 「닿은 자리 격자」다** — 그림자 안에서 던진 `CustomEvent` 가 **어느 자리에서 불렸나**와 그 자리에서 본 **`target` · `composedPath().length`** 를 `bubbles` × `composed` × `open`/`closed` 로 센다. 여기에 **「디스패치가 동기」를 호출 순서 로그로** 얹는다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 `CustomEvent`(「`detail` 은 초기화된 값을 돌려준다」) · `dispatchEvent()`(「dispatch flag 가 서 있거나 initialized flag 가 없으면 `InvalidStateError`」 · `isTrusted` 를 `false` 로) · 「dispatch」·「inner invoke」(리스너가 던지면 **report exception**) 절. 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 대부분 스크립트가 던진 합성 이벤트이고, (5)의 견줌 한 줄만 **CDP 로 넣은 진짜 클릭**이다. 하네스는 [20번 주제](../20-listener-lifetime/2-summary.md)의 (1)에 있다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★★ **[12번 주제](../12-shadow-dom/2-summary.md)의 (14)·(15)** 가 재타기팅과 **`bubbles`×`composed` 두 스위치**(`Event` 로 받은 자리만)를 이미 쟀고, `closed` 에서 `composedPath` 가 **7칸 → 5칸**이 되는 것도 거기서 봤다. **[18번 주제](../18-event-delegation/2-summary.md)의 (6)** 이 `composed:false` 합성 이벤트가 **위임 리스너에 안 닿는 것**을 쟀다. **[16번 주제](../16-event-propagation-phases/2-summary.md)의 (7)** 이 생성자의 `bubbles` 기본값이 `false` 인 것을, **[17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md)의 (6)** 이 `dispatchEvent` 의 반환값을 쟀다. 여기는 **그것을 인용하고**, `CustomEvent` 로 **격자를 채우고**, **동기성 · 예외 · `detail`** 을 잰다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 편에는 흔들리는 칸이 없었다** — 세는 것이 전부 **닿은 자리 · 순서 · 값**이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 닿은 자리 격자 8줄 · 호출 순서 · 예외 이름과 문구 · 반환값 · `detail` 의 동일성 · 진짜 클릭과 `el.click()` 의 순서 | 캡처 세 판이 **한 글자도 같았다** |
| **흔들린다** | Chrome 판 번호 · 예외 **문구** | 문구는 Chrome 의 것이다. 외울 것은 **이름**이다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | 이벤트는 트리에 자국을 안 남긴다 |
| 창 ② 노드 프로브 | **부적용** | — |
| 창 ③ 같은 것을 두 번 읽기 | ★ **쓴다** | 디스패치 **뒤에** 보낸 쪽이 `detail` 을 다시 읽는다((4)) |
| **창 ④ 디스패치 계수기 → 닿은 자리 격자 + 호출 순서 로그** | ★★★ **본체** | 어느 자리에서 불렸나 · 그 자리의 `target`·경로 길이((1)) · 누가 먼저 찍혔나((2)·(5)) |
| 창 ⑤ 콘솔 → `window` 의 `error` 이벤트 | ★ **쓴다 — 제5의 상태** | 리스너가 던진 예외는 **콘솔로 간다.** 콘솔 대신 **`error` 이벤트로 물었다**((3)) |

- ★★ **제5의 상태 — 「예외가 어디로 갔나」를 콘솔이 아니라 `window` 의 `error` 이벤트로 물었다.** DOM 이 리스너 예외를 **report exception** 으로 넘기고, 그것이 `error` 이벤트로 온다. ★ 바꾼 창이 못 보는 것 — **콘솔에 찍힌 스택 트레이스**는 이 창에 없다(`message` 만 온다).

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| **`closed` 그림자의 안쪽 경로** | 바깥 리스너의 `composedPath()` 가 **안쪽을 잘라 준다** — 잘렸다는 사실(길이 5)만 보인다 |
| **리스너 예외의 스택** | `error` 이벤트의 `message` 만 읽었다 |
| **디스패치에 걸리는 시간** | 순서만 봤다. **재지 않았다** |

## 한눈에 — 쉽게 말하면

**★ `dispatchEvent` 는 「우편」이 아니라 「전화」다. 거는 순간 받는 사람이 전부 말을 끝내야 수화기가 돌아온다. 그리고 `bubbles`·`composed` 는 「이 건물 안에서만 방송할지, 담장 밖까지 방송할지」를 정하는 두 스위치다.**

| 비유 | 실체 |
|---|---|
| 전화를 건다 | `el.dispatchEvent(ev)` — 리스너가 **다 끝나야** 다음 줄로 간다 |
| 통화 중에 누가 또 전화를 건다 | 리스너 안의 `dispatchEvent` — **그 자리에서 끼어들어** 끝난 뒤 돌아온다 |
| 「나중에 전해 줘」 메모 | 리스너가 건 마이크로태스크 — 스크립트가 건 전화가 **다 끝난 뒤** 돈다 |
| 받는 사람이 쓰러져도 전화는 계속 돈다 | 리스너 예외 — **거는 쪽 `try` 로 안 오고** 다음 리스너가 불린다 |
| 소포 상자 | `detail` — **복사가 아니라 같은 상자**가 건너간다 |
| 위층으로 방송 | `bubbles: true` |
| 담장(그림자 경계) 밖까지 방송 | `composed: true` |

```text
   dispatchEvent 는 동기다

   순.push('앞')
   el.dispatchEvent(ev) ─────▶ 리스너 1
                               리스너 2 ──▶ (안에서 또 dispatch) ──▶ 그 리스너 ──┐
                               리스너 2 의 나머지  ◀─────────────────────────────┘
                               리스너 3 …
                        ◀───── 전부 끝나고 돌아온다
   순.push('뒤')
   (스크립트가 끝난 뒤) 마이크로태스크
```

## 이 주제가 답하려는 질문

1. **내 이벤트가 그림자 경계를 넘을지**를 무엇이 정하나 — `bubbles` 와 `composed` 가 각각 무엇을 막나, 넘은 뒤 `target` 은 무엇이 되나.
2. **디스패치가 동기**라는 것이 만드는 흐름 — 리스너와 호출자의 다음 줄, 중첩 디스패치, 마이크로태스크는 어떤 순서인가.
3. **보낸 쪽이 받는 것** — 반환값, 리스너 예외, `detail` 은 무엇이 건너오나.

## 동작 방식

### (1) ★★★ 본체 — `bubbles` × `composed` × `open`/`closed` 격자

**언제 쓰나** — 웹 컴포넌트가 **자기 이벤트를 바깥에 알릴 때.**

**던진 것** — 호스트 둘(`open` · `closed`) 안에 각각 `#안쪽` 하나. 리스너는 **`#안쪽` · 호스트 · `document`** 세 자리. `#안쪽` 에서 `dispatchEvent(new CustomEvent('알림', { bubbles, composed }))` 를 네 조합으로 던지고, 불린 자리마다 **그 자리에서 본 `e.target` 과 `e.composedPath().length`** 를 적는다.

```html
<!-- wa20b-21-grid.html -->
<!doctype html>
<meta charset="utf-8">
<title>21-grid</title>
<div id="열린호스트"></div>
<div id="닫힌호스트"></div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const 이름 = n => n === window ? 'window' : n === document ? 'document' : n instanceof ShadowRoot ? '#shadow-root'
  : n.id ? '#' + n.id : n.nodeName;

// 호스트 둘 — 하나는 open, 하나는 closed. 그림자 안에 #안쪽 하나.
const 안쪽들 = {};
for (const [id, mode] of [['열린호스트', 'open'], ['닫힌호스트', 'closed']]) {
  const r = document.getElementById(id).attachShadow({ mode });
  const 안 = document.createElement('span'); 안.id = '안쪽'; r.appendChild(안);
  안쪽들[mode] = 안;
}

let 판 = null;
const 받기 = 자리 => e => { if (판 && e.type === 판.형) 판[자리] = { target: 이름(e.target), 길이: e.composedPath().length }; };
for (const id of ['열린호스트', '닫힌호스트']) document.getElementById(id).addEventListener('알림', 받기('호스트'));
document.addEventListener('알림', 받기('문서'));
for (const 안 of Object.values(안쪽들)) 안.addEventListener('알림', 받기('안쪽'));

const 줄 = [];
for (const mode of ['open', 'closed'])
  for (const bubbles of [true, false])
    for (const composed of [true, false]) {
      판 = { 형: '알림', 안쪽: null, 호스트: null, 문서: null };
      안쪽들[mode].dispatchEvent(new CustomEvent('알림', { bubbles, composed, detail: 1 }));
      줄.push({ mode, bubbles, composed, ...판 });
    }
판 = null;

const 칸 = r => r ? r.target + ' · ' + r.길이 : '-';
window.__끝 = () => {
  const O = [];
  O.push('그림자 안 #안쪽 에서 dispatchEvent(new CustomEvent(\'알림\', { bubbles, composed }))');
  O.push('칸 = 그 자리에서 본 e.target · e.composedPath().length   (- = 안 불림)');
  O.push(padw('mode · bubbles · composed', 28) + padw('#안쪽', 14) + padw('호스트', 20) + '문서');
  for (const r of 줄) O.push(padw(r.mode + ' · ' + r.bubbles + ' · ' + r.composed, 28)
                         + padw(칸(r.안쪽), 14) + padw(칸(r.호스트), 20) + 칸(r.문서));
  O.push('');
  for (const mode of ['open', 'closed']) {
    const rs = 줄.filter(r => r.mode === mode);
    O.push(mode + ' — 호스트가 받은 칸 = ' + rs.filter(r => r.호스트).length + ' / ' + rs.length
         + ' · 문서가 받은 칸 = ' + rs.filter(r => r.문서).length + ' / ' + rs.length);
  }
  let 갈림 = 0, 모두 = 0;
  for (let i = 0; i < 4; i++) for (const k of ['안쪽', '호스트', '문서']) { 모두++; if (칸(줄[i][k]) !== 칸(줄[i + 4][k])) 갈림++; }
  O.push('open 과 closed 가 갈린 칸 = ' + 갈림 + ' / ' + 모두);
  return O.join('\n');
};
</script>
```

```text
$ python3 wa20b-cdp.py page wa20b-21-grid.html
그림자 안 #안쪽 에서 dispatchEvent(new CustomEvent('알림', { bubbles, composed }))
칸 = 그 자리에서 본 e.target · e.composedPath().length   (- = 안 불림)
mode · bubbles · composed   #안쪽         호스트              문서
open · true · true          #안쪽 · 7     #열린호스트 · 7     #열린호스트 · 7
open · true · false         #안쪽 · 2     -                   -
open · false · true         #안쪽 · 7     #열린호스트 · 7     -
open · false · false        #안쪽 · 2     -                   -
closed · true · true        #안쪽 · 7     #닫힌호스트 · 5     #닫힌호스트 · 5
closed · true · false       #안쪽 · 2     -                   -
closed · false · true       #안쪽 · 7     #닫힌호스트 · 5     -
closed · false · false      #안쪽 · 2     -                   -

open — 호스트가 받은 칸 = 2 / 4 · 문서가 받은 칸 = 1 / 4
closed — 호스트가 받은 칸 = 2 / 4 · 문서가 받은 칸 = 1 / 4
open 과 closed 가 갈린 칸 = 3 / 12
(exit 0)
```

- ★★ **문서까지 닿는 것은 `bubbles: true, composed: true` 한 줄뿐**이다(두 모드 다 1 / 4). 컴포넌트가 바깥에 알릴 이벤트는 **둘 다 켜야** 한다 — [12번 주제](../12-shadow-dom/2-summary.md)의 (15)가 `Event` 로 본 결론을 `CustomEvent` 로 다시 받았다.
- ★ **`composed: true, bubbles: false` 는 호스트까지는 온다** — 호스트에서 이벤트의 타깃이 **호스트로 바뀌어** 그 자리가 **다시 「타깃 단계」** 가 되기 때문이다. 문서는 못 받는다.
- **`composed: false` 는 호스트도 못 받는다** — 경로가 **그림자 루트에서 끝난다**(길이 2 = `#안쪽`·`#shadow-root`).
- ★★★ **바깥에서 본 `target` 은 호스트다** — `#안쪽` 이 아니다(재타기팅).
- ★★ **`open` 과 `closed` 가 갈린 칸은 3 / 12** 이고 **전부 「경로 길이」** 다 — `closed` 에서는 바깥 자리가 **7 이 아니라 5** 를 본다(그림자 안 두 칸이 잘린다). **닿느냐 안 닿느냐는 두 모드가 같다.** `closed` 는 **보이는 것**을 줄일 뿐 **가는 길**을 막지 않는다.

```text
   ★ 두 스위치 × 두 모드 — 어디까지 닿나 (이 판 8줄)

                          #안쪽     호스트                 문서
   bubbles  · composed    ○ 7       ○ (target=호스트)      ○ (target=호스트)
   bubbles  · ─           ○ 2       ─                      ─
   ─        · composed    ○ 7       ○ (target=호스트)      ─
   ─        · ─           ○ 2       ─                      ─

   closed 일 때 달라지는 것은 바깥 두 자리의 경로 길이뿐: 7 → 5
```

```text
   경로가 바깥에서 어떻게 보이나 (bubbles · composed · 문서 리스너에서)

   open    #안쪽 → #shadow-root → #열린호스트 → BODY → HTML → #document → Window   (7)
   closed           (잘림)         #닫힌호스트 → BODY → HTML → #document → Window   (5)
```

### (2) ★★ 디스패치는 동기다 — 호출 순서 로그

**언제 쓰나** — 「이벤트를 보냈으니 리스너는 나중에 돌겠지」라고 기대할 때.

```html
<!-- wa20b-21-sync.html -->
<!doctype html>
<meta charset="utf-8">
<title>21-sync</title>
<button id="단추">단추</button>
<script>
const O = [];
const $ = id => document.getElementById(id);
const 잡기 = fn => { try { return '예외 없음 · ' + fn(); } catch (e) { return e.name + ' 「' + e.message + '」'; } };

O.push('가. dispatchEvent 앞뒤 줄과 리스너 줄의 순서');
const 순 = [];
$('단추').addEventListener('가', () => 순.push('리스너 1'));
$('단추').addEventListener('가', () => { 순.push('리스너 2 — 안에서 나 를 던짐'); $('단추').dispatchEvent(new CustomEvent('나')); 순.push('리스너 2 — 나 를 던진 뒤'); });
$('단추').addEventListener('가', () => 순.push('리스너 3'));
$('단추').addEventListener('나', () => 순.push('  나 의 리스너'));
$('단추').addEventListener('가', () => Promise.resolve().then(() => 순.push('리스너 4 가 건 마이크로태스크')));
$('단추').addEventListener('가', () => 순.push('리스너 5'));
순.push('dispatchEvent 앞');
$('단추').dispatchEvent(new CustomEvent('가'));
순.push('dispatchEvent 뒤');
window.__가 = () => Promise.resolve().then(() => { O.push(...순.map((s, i) => '  ' + (i + 1) + '. ' + s)); O.push(''); return 1; });

// 나.는 __나 에서 찍는다(오류 이벤트가 오고 난 뒤)
const 오류 = [];
window.addEventListener('error', e => 오류.push(e.message));
window.__나 = () => {
  O.push('나. 리스너가 던진 예외 — dispatchEvent 를 try 로 감싸면');
  const 순2 = [];
  $('단추').addEventListener('다', () => { 순2.push('리스너 1 — 던지기 직전'); throw new Error('리스너가 터진다'); });
  $('단추').addEventListener('다', () => 순2.push('리스너 2'));
  let 반환 = '-', 잡힘 = '없음';
  try { 반환 = $('단추').dispatchEvent(new CustomEvent('다', { cancelable: true })); }
  catch (e) { 잡힘 = e.name + ' 「' + e.message + '」'; }
  O.push('  리스너 순서 = ' + 순2.join(' → '));
  O.push('  호출한 쪽 catch 가 잡은 것 = ' + 잡힘 + ' · dispatchEvent 의 반환값 = ' + 반환);
  O.push('  window 의 error 이벤트가 받은 message = ' + JSON.stringify(오류));
  O.push('');
  return 1;
};

window.__다 = () => {
  O.push('다. dispatchEvent 의 반환값과 cancelable');
  for (const cancelable of [true, false]) {
    const f = e => e.preventDefault();
    $('단추').addEventListener('라', f);
    const e = new CustomEvent('라', { cancelable });
    const 반환 = $('단추').dispatchEvent(e);
    $('단추').removeEventListener('라', f);
    O.push('  cancelable:' + cancelable + ' · 리스너가 preventDefault → 반환값 = ' + 반환 + ' · defaultPrevented = ' + e.defaultPrevented);
  }
  O.push('');

  O.push('라. detail 은 무엇이 건너가나');
  const 보낸것 = { 수: 1, 목록: ['가'] };
  let 받은것 = null;
  $('단추').addEventListener('마', e => { 받은것 = e.detail; e.detail.수 = 2; e.detail.목록.push('나'); });
  const ev = new CustomEvent('마', { detail: 보낸것 });
  $('단추').dispatchEvent(ev);
  O.push('  리스너가 받은 detail === 보낸 객체 → ' + (받은것 === 보낸것));
  O.push('  디스패치 뒤 보낸 쪽이 읽은 값 = ' + JSON.stringify(보낸것));
  O.push('  detail 을 안 주면 = ' + JSON.stringify(new CustomEvent('x').detail) + ' · detail 에 대입하면 = ' + 잡기(() => { 'use strict'; const e2 = new CustomEvent('x'); e2.detail = 5; return JSON.stringify(e2.detail); }));
  O.push('  isTrusted = ' + ev.isTrusted + ' · bubbles 기본 = ' + ev.bubbles + ' · composed 기본 = ' + ev.composed + ' · cancelable 기본 = ' + ev.cancelable);
  O.push('');

  O.push('마. 같은 이벤트 객체를 다시 던지면');
  let 안에서 = '-';
  const e3 = new CustomEvent('바');
  $('단추').addEventListener('바', () => { if (안에서 === '-') 안에서 = 잡기(() => $('단추').dispatchEvent(e3)); });
  $('단추').dispatchEvent(e3);
  O.push('  리스너 안에서 같은 객체를 dispatchEvent = ' + 안에서);
  O.push('  디스패치가 끝난 뒤 같은 객체를 한 번 더 = ' + 잡기(() => $('단추').dispatchEvent(e3)));
  O.push('  Event 가 아닌 객체(CustomEvent.prototype 만 물려받음) 를 던지면 = ' + 잡기(() => $('단추').dispatchEvent(Object.create(CustomEvent.prototype))));
  O.push('');
  return 1;
};

// 바. 같은 두 리스너 — 진짜 클릭 한 번 대 스크립트의 el.click()
const 순3 = [];
$('단추').addEventListener('click', () => { 순3.push('리스너 1'); Promise.resolve().then(() => 순3.push('리스너 1 이 건 마이크로태스크')); });
$('단추').addEventListener('click', () => 순3.push('리스너 2'));
window.__바앞 = 무엇 => { 순3.length = 0; 순3.push(무엇 + ' 시작'); return 1; };
window.__바뒤 = 무엇 => Promise.resolve().then(() => { O.push('바. ' + 무엇 + ' — ' + 순3.join(' → ')); return 1; });
window.__스크립트클릭 = () => { __바앞('el.click()'); $('단추').click(); 순3.push('el.click() 다음 줄'); return 1; };

window.__단계 = [['js', '__가()'], ['js', '__나()'], ['js', 'new Promise(r => setTimeout(r, 0))'], ['js', '__다()'],
  ['js', '__바앞("진짜 클릭")'], ['click', '#단추'], ['js', '__바뒤("진짜 클릭")'],
  ['js', '__스크립트클릭()'], ['js', '__바뒤("el.click()")']];
window.__끝 = () => O.join('\n');
</script>
```

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '1,10p'
가. dispatchEvent 앞뒤 줄과 리스너 줄의 순서
  1. dispatchEvent 앞
  2. 리스너 1
  3. 리스너 2 — 안에서 나 를 던짐
  4.   나 의 리스너
  5. 리스너 2 — 나 를 던진 뒤
  6. 리스너 3
  7. 리스너 5
  8. dispatchEvent 뒤
  9. 리스너 4 가 건 마이크로태스크
(exit 0)
```

- ★★★ **「dispatchEvent 뒤」가 리스너 다섯 줄보다 늦다** — `dispatchEvent` 는 **리스너를 전부 부른 뒤에야** 돌아온다.
- ★ **리스너 2 안의 디스패치가 그 자리에서 끼어들었다** — `나 의 리스너` 가 리스너 2 의 **앞뒤 두 줄 사이**에 있다. 중첩도 동기다.
```text
   중첩 디스패치 — 호출 스택으로 보면

   스크립트
    └─ dispatchEvent('가')
        ├─ 리스너 1
        ├─ 리스너 2
        │   └─ dispatchEvent('나')          ← 여기서 스택이 한 칸 더 깊어진다
        │       └─ 나 의 리스너
        │   (돌아와서) 리스너 2 의 나머지
        ├─ 리스너 3
        ├─ 리스너 4 ── Promise.then 을 큐에 넣기만 한다
        └─ 리스너 5
    'dispatchEvent 뒤'
   (스크립트 끝 · 스택이 빔) ─▶ 마이크로태스크
```

- ★★ **리스너 4 가 건 마이크로태스크는 맨 끝**이다 — 「`dispatchEvent` 뒤」보다도 늦다. **스크립트가 던진 디스패치**에서는 리스너 사이에 마이크로태스크가 **안 끼어든다**(스크립트가 아직 안 끝났다). 진짜 클릭에서는 다르다 — (5).

### (3) ★★ 리스너가 던진 예외는 호출자에게 안 온다

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '12,15p'
나. 리스너가 던진 예외 — dispatchEvent 를 try 로 감싸면
  리스너 순서 = 리스너 1 — 던지기 직전 → 리스너 2
  호출한 쪽 catch 가 잡은 것 = 없음 · dispatchEvent 의 반환값 = true
  window 의 error 이벤트가 받은 message = ["Uncaught Error: 리스너가 터진다"]
(exit 0)
```

- ★★★ **호출한 쪽 `try` 의 `catch` 가 아무것도 못 잡았다**(「없음」). `dispatchEvent` 는 **정상으로 돌아왔고** 반환값은 `true` 다.
- **리스너 2 는 여전히 불렸다** — 한 리스너의 예외가 **나머지를 막지 않는다.**
- ★ **예외는 `window` 의 `error` 이벤트로 갔다**(`Uncaught Error: 리스너가 터진다`). DOM 의 inner invoke 가 리스너 예외를 **report exception** 으로 넘기기 때문이다.
- ★ **[13번 주제](../13-custom-element-lifecycle/2-summary.md)의 (6)과 같은 모양**이다 — 커스텀 요소 생성자 예외도 `createElement` 호출자에게 **안 오고** 콘솔로 샜다. 둘 다 명세가 **report exception** 을 쓰는 자리다.

```text
   예외가 가는 길

   try {                                    리스너 1 ── throw ──▶ report exception ──▶ window 'error' 이벤트
     el.dispatchEvent(ev);   ── 정상 반환 ◀── 리스너 2 (계속 불린다)                        + 콘솔
   } catch (e) { … }         ← 오지 않는다
```

### (4) 반환값 · `detail` · 생성자 기본값

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '17,19p'
다. dispatchEvent 의 반환값과 cancelable
  cancelable:true · 리스너가 preventDefault → 반환값 = false · defaultPrevented = true
  cancelable:false · 리스너가 preventDefault → 반환값 = true · defaultPrevented = false
(exit 0)
```

- **반환값 = 「취소 안 됐나」** — `cancelable: true` 에서 `preventDefault()` 하면 `false`, **`cancelable: false` 면 `preventDefault()` 가 무시되어 `true`** 다. [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md)의 (6)이 `Event` 로 잰 것과 같다.

```text
   보낸 쪽이 반환값으로 받는 것 — 「받는 쪽 거부권」

   const 진행 = el.dispatchEvent(new CustomEvent('닫기전', { cancelable: true }));
   if (!진행) return;          ← 누군가 preventDefault 했다
   닫기();

   ★ cancelable 을 안 켜면 거부권이 없다 — preventDefault 가 무시되고 반환값은 늘 true
```

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '21,25p'
라. detail 은 무엇이 건너가나
  리스너가 받은 detail === 보낸 객체 → true
  디스패치 뒤 보낸 쪽이 읽은 값 = {"수":2,"목록":["가","나"]}
  detail 을 안 주면 = null · detail 에 대입하면 = TypeError 「Cannot set property detail of #<CustomEvent> which has only a getter」
  isTrusted = false · bubbles 기본 = false · composed 기본 = false · cancelable 기본 = false
(exit 0)
```
- ★★ **`detail` 은 참조 그대로 건너간다** — 리스너가 받은 것이 **보낸 객체와 같고**(`===` 가 `true`), 리스너가 고친 것이 **보낸 쪽에서 보인다**(`수:2` · `목록` 에 `"나"`). **복사가 아니다.**
- ★ **`detail` 을 안 주면 `null`**, **대입은 `TypeError`**(읽기 전용 접근자) — 엄격 모드에서만 던진다. 느슨한 모드면 **조용히 무시**된다.
- **생성자 기본값** — `bubbles`·`composed`·`cancelable` 이 **전부 `false`**, `isTrusted` 도 `false`. [16번 주제](../16-event-propagation-phases/2-summary.md)의 (7)이 `bubbles` 를, [12번 주제](../12-shadow-dom/2-summary.md)의 (15)가 `composed` 를 쟀다.

```text
   detail 은 같은 상자다

   보낸것 = { 수: 1, 목록: ['가'] }
   new CustomEvent('마', { detail: 보낸것 }) ──▶ 리스너: e.detail.수 = 2; e.detail.목록.push('나')
   디스패치 뒤  보낸것 = { 수: 2, 목록: ['가','나'] }   ← 보낸 쪽도 바뀌었다

   ★ 받는 쪽이 못 고치게 하려면 보낼 때 얼리거나(Object.freeze) 복사해서 보낸다 — 이 편은 그 둘을 던지지 않았다
```

### (5) 같은 객체를 다시 던지면 · 진짜 클릭과 `el.click()`

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '27,30p'
마. 같은 이벤트 객체를 다시 던지면
  리스너 안에서 같은 객체를 dispatchEvent = InvalidStateError 「Failed to execute 'dispatchEvent' on 'EventTarget': The event is already being dispatched.」
  디스패치가 끝난 뒤 같은 객체를 한 번 더 = 예외 없음 · true
  Event 가 아닌 객체(CustomEvent.prototype 만 물려받음) 를 던지면 = TypeError 「Failed to execute 'dispatchEvent' on 'EventTarget': parameter 1 is not of type 'Event'.」
(exit 0)
```

- ★ **리스너 안에서 같은 이벤트 객체를 다시 던지면 `InvalidStateError`** — DOM 의 `dispatchEvent()` 첫 단계가 「**dispatch flag 가 서 있으면**」 던진다.
- **끝난 뒤에는 다시 던질 수 있다** — 플래그가 내려갔다.
- **`Event` 가 아닌 것은 `TypeError`** — 프로토타입만 물려받은 객체는 **진짜 이벤트가 아니다**(IDL 이 먼저 거른다).

```text
   이벤트 객체의 dispatch flag

   new CustomEvent('바')      flag 내림
   dispatchEvent(e3) 시작     flag 올림  ── 리스너 안에서 dispatchEvent(e3) ─▶ InvalidStateError
   dispatchEvent(e3) 끝       flag 내림
   dispatchEvent(e3) 또       ✔ 된다 — 같은 객체를 두 번 보낼 수 있다
```

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '32,33p'
바. 진짜 클릭 — 진짜 클릭 시작 → 리스너 1 → 리스너 1 이 건 마이크로태스크 → 리스너 2
바. el.click() — el.click() 시작 → 리스너 1 → 리스너 2 → el.click() 다음 줄 → 리스너 1 이 건 마이크로태스크
(exit 0)
```

- ★★ **같은 두 리스너인데 순서가 갈린다.** **진짜 클릭**에서는 리스너 1 이 건 마이크로태스크가 **리스너 2 보다 먼저** 돈다. **`el.click()`** 에서는 **스크립트의 다음 줄보다도 늦다.**
- 이유 — 진짜 입력은 브라우저가 리스너를 부르고, **리스너 하나가 끝날 때마다 스크립트 스택이 비어** 마이크로태스크 체크포인트가 돈다. `el.click()`·`dispatchEvent` 는 **스크립트 안에서 부르므로** 스택이 끝까지 안 빈다. ★ **이 설명의 명세 절(「clean up after running script」의 체크포인트)은 이 문서가 열어 확인하지 않았다** — 순서만 이 판의 관찰이다. 정본은 목록의 **40번 주제**다.

```text
   같은 리스너 둘 · 리스너 1 이 Promise.then 을 건다

   진짜 클릭      리스너 1 → (마이크로태스크) → 리스너 2
   el.click()     리스너 1 → 리스너 2 → el.click() 다음 줄 → (마이크로태스크)
   dispatchEvent  (2)의 가. 와 같다 — 마이크로태스크는 맨 끝

   ★ 「합성으로 짠 테스트가 실제 클릭과 순서가 다르다」는 자리가 여기다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   만들기
     new CustomEvent(type, { detail, bubbles, cancelable, composed })   기본은 전부 false · detail 은 null
   던지기
     const 안막힘 = el.dispatchEvent(ev)   리스너가 다 끝난 뒤 돌아온다 · false 면 누가 preventDefault
   받기
     el.addEventListener(type, e => e.detail)
   컴포넌트가 바깥에 알리기
     this.dispatchEvent(new CustomEvent('바뀜', { detail, bubbles: true, composed: true }))
```

### 어디서 헷갈리나

- **`composed` 만 켜면 문서까지 간다** — 아니다. **호스트까지**다((1)).
- **`closed` 면 바깥으로 안 나간다** — 아니다. **나간다.** 경로가 잘려 보일 뿐이다((1)).
- **`detail` 은 복사된다** — 아니다. **같은 객체**다((4)).

## 어디서 틀리나

### 1. 컴포넌트 이벤트를 `new CustomEvent('x', { detail })` 로만 던진다

**호스트 밖 누구도 못 받는다**((1)) — `bubbles`·`composed` 가 둘 다 `false` 다. 문서 수준 위임([18번 주제](../18-event-delegation/2-summary.md))도 안 닿는다.

### 2. `composed: true` 만 켜고 `document` 에서 기다린다

**호스트까지만 온다**((1)). `bubbles: true` 도 켜야 한다.

### 3. `dispatchEvent` 를 `try` 로 감싸 리스너 실패를 잡으려 한다

**안 잡힌다**((3)). 반환값도 `true` 다. 리스너 쪽에서 잡거나 `error` 이벤트를 본다.

### 4. `dispatchEvent` 뒤 줄이 리스너보다 먼저 돈다고 믿는다

**리스너가 먼저다**((2)). 「알리고 나서 상태를 바꾸는」 코드는 **리스너가 옛 상태를 본다.** 상태를 먼저 바꾸고 알린다.

### 5. 받은 `detail` 을 고쳐도 보낸 쪽은 모른다고 믿는다

**같은 객체라 보낸 쪽도 바뀐다**((4)).

### 6. 리스너 안에서 받은 이벤트를 그대로 다시 던진다

**`InvalidStateError`**((5)). 새 이벤트를 만들어 던진다.

### 7. `el.click()` 으로 짠 테스트의 순서를 실제 클릭에서도 믿는다

**마이크로태스크가 끼는 자리가 다르다**((5)).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `composed` 가 경계를, `bubbles` 가 위로 가는 것을 정하는 것 · 재타기팅 | **명세**(DOM — dispatch 의 경로 만들기 · retarget) · 이 판도 그랬다((1)) |
| `closed` 에서 바깥 리스너의 `composedPath()` 가 **안쪽을 뺀** 것 | **명세**(DOM — `composedPath()` 가 closed 트리 안을 숨긴다) · 이 판에서 7 → 5 |
| `dispatchEvent` 가 리스너를 **다 부른 뒤 돌아오는** 것 | **명세**(DOM — `dispatchEvent()` 가 dispatch 의 결과를 돌려준다) |
| 리스너 예외가 **호출자에게 안 가고** 나머지 리스너가 불리는 것 | **명세**(DOM — inner invoke 의 report exception) |
| 예외 **문구**(`Uncaught Error: …` · `The event is already being dispatched.`) | ★ **구현.** 외울 것은 이름(`InvalidStateError`·`TypeError`)이다 |
| 이미 디스패치 중인 이벤트를 다시 던지면 `InvalidStateError` | **명세**(DOM — `dispatchEvent()`) |
| `detail` 이 **참조 그대로**인 것 · 기본 `null` | **명세**(DOM — 「초기화된 값을 돌려준다」) |
| 진짜 클릭에서 리스너 사이에 마이크로태스크가 도는 것 | ★ **이 판의 관찰.** 이 문서는 해당 명세 절을 열어 확인하지 않았다 — 목록의 **40번 주제** 몫 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 컴포넌트가 바깥에 알린다 | `{ bubbles: true, composed: true }` | 기본값 그대로 |
| 컴포넌트 **안에서만** 쓰는 신호 | `composed: false` | 바깥까지 새는 이벤트 |
| 받는 쪽이 「취소」할 수 있게 | `cancelable: true` + 반환값 확인 | 반환값 무시 |
| 받는 쪽이 데이터를 못 고치게 | 얼리거나 복사한 `detail` | 내부 상태 객체를 그대로 |
| 알림 뒤 비동기로 처리하고 싶다 | 리스너 안에서 `queueMicrotask`·`setTimeout` | 「`dispatchEvent` 가 알아서 나중에」 기대 |

## 핵심 문장

1. **문서까지 닿는 것은 `bubbles: true, composed: true` 한 조합뿐**이다 — `composed` 만이면 호스트까지.
2. **바깥에서 본 `target` 은 호스트**이고, `closed` 는 **경로를 잘라 보여 줄 뿐 가는 길을 막지 않는다**(갈린 칸 3 / 12 가 전부 경로 길이).
3. **`dispatchEvent` 는 동기다** — 리스너가 다 끝나야 돌아오고, 중첩 디스패치도 그 자리에서 끼어든다.
4. **리스너 예외는 호출자의 `try` 로 안 온다** — `error` 이벤트와 콘솔로 가고, 나머지 리스너는 불린다.
5. **`detail` 은 같은 객체**다 — 받는 쪽이 고치면 보낸 쪽도 바뀐다.
6. **진짜 클릭과 `el.click()` 은 마이크로태스크가 끼는 자리가 다르다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 21번)
- [12번 주제](../12-shadow-dom/2-summary.md) — **재타기팅 · 두 스위치 · closed 의 7→5 칸의 정본.** 여기는 그것을 `CustomEvent` 격자로 다시 받는다
- [18번 주제](../18-event-delegation/2-summary.md) — `composed:false` 합성 이벤트가 위임에 안 닿는 것 · 그림자 경계의 `closest`
- [16번 주제](../16-event-propagation-phases/2-summary.md) — 전파 3단계와 생성자의 `bubbles` 기본값
- [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md) — `cancelable`·`defaultPrevented`·반환값의 정본
- [13번 주제](../13-custom-element-lifecycle/2-summary.md) — 생성자 예외가 호출자에게 안 오는 같은 모양
- [20번 주제](../20-listener-lifetime/2-summary.md) — 하네스 전문
- 목록의 **40번 주제** — 마이크로태스크와 렌더의 순서(진짜 클릭 쪽 설명의 정본)

## 용어 풀이

- **`CustomEvent`** — `detail` 하나를 더 실을 수 있는 `Event`. 나머지는 `Event` 와 같다.
- **`detail`** — 이벤트에 실어 보내는 값. 복사하지 않고 그대로 건넨다.
- **`composed`** — 이벤트가 그림자 경계를 넘어 바깥 트리로 가나.
- **재타기팅** — 경계 밖 리스너에게 `target` 을 **호스트로** 바꿔 보여 주는 것.
- **동기 디스패치** — 리스너를 전부 부른 뒤에야 `dispatchEvent` 가 돌아오는 것.
- **report exception** — 리스너·콜백의 예외를 호출자 대신 전역의 `error` 이벤트와 콘솔로 넘기는 명세 절차.
- **닿은 자리 격자** — 어느 리스너 자리가 불렸나를 스위치 조합마다 센 것. 이 편의 본체.

## 더 들어가면

- **`Event` 를 상속한 클래스**(`class 내이벤트 extends Event`)로 `detail` 대신 필드를 싣는 형태는 던지지 않았다.
- **슬롯에 배정된 자식에서 던진 커스텀 이벤트**의 경로는 [12번 주제](../12-shadow-dom/2-summary.md)의 (15)가 `Event` 로 봤다(재타기팅 없음 · 경로에 `<slot>`).
- **`cancelable` 커스텀 이벤트로 「받는 쪽 거부권」을 설계하는 패턴**은 반환값까지만 봤다.
