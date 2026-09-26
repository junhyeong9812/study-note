# web-api/10 — 레이아웃 스래싱: 읽기·쓰기 교차로 나는 강제 동기 레이아웃 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 주제는 이 갈래에서 유일하게 「API」가 아니라 「실패 모드」를 주제로 세운 자리다.** 그리고 **명세가 보장하지 않는 것이 본체**다 — 「언제 레이아웃이 도는가」를 정한 명세는 **없다.** 명세가 정한 것은 「**이 값은 최신이어야 한다**」이고, 그 요구를 지키느라 구현이 그 자리에서 레이아웃을 돌린다. **그 사실 자체가 이 주제의 축이다.**\
> **기준 소스** — [CSSOM View Module](https://drafts.csswg.org/cssom-view/) 의 「**Web developers should be aware …**」 노트와 각 속성의 「run the update the rendering steps / flush layout」 요구, [HTML Living Standard — Event loop: 렌더링 단계](https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model). 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 블록마다 명령이 배너로 실려 있고, 그 배너에는 **`--window-size=1000,800`** 이 들어 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. **이식성을 주장하지 않는다.** 그리고 이 주제는 **원래부터 구현 이야기**라 다른 엔진에서 수치가 다른 것이 당연하다.\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. 여기서 다루는 속성은 전부 **Baseline 추적 대상이 아닐 만큼 오래된** 표면이다.\
> **선행** — [08번 주제](../08-getcomputedstyle/2-summary.md)(계산값 읽기)와 [09번 주제](../09-element-geometry/2-summary.md)(기하 읽기). **둘이 이 주제의 방아쇠 목록이다.**\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제는 수치를 재는 주제**다. 그래서 흔들리는 칸이 많고, **무엇을 결론으로 쓸지 먼저 못 박는다.**

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | **최신성 프로브의 답**(바뀌었나 / 안 바뀌었나) · 관측된 값 목록 `[10,20,30]` | 시간을 안 재는 결정적 관측이다 |
| **안 흔들린다** | 시간 표의 **자릿수와 순위** · 「쓰기만 한 것과 갈리는 반복 수」 칸 | 세 판 모두 같았다 |
| **흔들린다** | `performance.now()` 의 **모든 개별 수치**(중앙값·최소·최대·비) | 판마다 달라진다 |
| **흔들린다** | **rAF 블록의 실행 횟수·시각·경과** — 다섯 판이 서로 달랐다((7)의 블록) | **프레임은 이 도구로 통제되지 않는다.** 그 흔들림 자체가 결론이다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- **수치를 인용할 때는 「몇 판을 어떻게 쟀나」를 같이 적는다** — 본 실험은 **400행 · 9판 중앙값**(최소·최대 동반), 읽기 목록은 **반복 30/300/3000 · 3판 중앙값**이다.
- ★ **`performance.now()` 는 Chrome 에서 100마이크로초 단위로 뭉개진다**([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) 실측 · 이 문서 (1)에서 다시 확인). **`0.10` 은 「공짜」가 아니라 「이 자로는 못 잰다」다**.
- 재대조에서 정규화하는 칸은 **시간 수치와 rAF 블록**뿐이다. 위 표에 없는 것은 정규화하지 않는다.

## 한눈에 — 쉽게 말하면

**★ 브라우저는 게으른 회계원이다. 고칠 것을 장부에 쌓아 두었다가 한꺼번에 계산하는데, 「지금 잔액이 얼마죠?」라고 물으면 그 자리에서 전부 계산해 버린다.**

회계원에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 전표를 **쌓아 두는 것** | 스타일을 쓰는 것 — 쌓이기만 하고 계산은 안 된다 |
| **「잔액이 얼마죠?」** | 기하·계산값을 읽는 것 |
| 물으면 **그 자리에서 다 계산한다** | 강제 동기 레이아웃 |
| 전표 하나 쌓고 물어보기를 **번갈아** 하면 | 읽기·쓰기 교차 — 계산을 N번 한다 |
| 전표를 **다 쌓고 한 번만** 물어보면 | 읽기를 묶는 것 — 계산을 한 번 한다 |
| 아무도 안 물어보면 **퇴근 전에 한 번** 계산한다 | 다음 렌더 단계에서 한 번 |
| ★ 회계원에게 **「언제 계산하라」는 규정이 없다** | 명세는 타이밍을 안 정한다 — 「답이 최신이어야 한다」만 정한다 |

- **비싼 것은 읽기도 쓰기도 아니라 「섞는 것」이다.** 실측에서 **같은 횟수인데 순서만 바꿔 한 자릿수 넘게** 갈렸다.
- ★ **이름이 무섭게 붙어 있지만**(스래싱·강제 동기 레이아웃) **동작은 조용하다.** 예외도 경고도 없고 결과도 옳다. **느려질 뿐이다.**
- ★ **그래서 진단이 어렵다.** 코드를 읽어서는 「읽기」인지 「쓰기」인지 이름만으로 안 보인다 — (8)의 목록을 **실측으로** 만든 이유가 그것이다.

```text
   한 tick 안에서 무슨 일이 나나

   ① 교차                                ② 묶음
   쓰기 → 읽기 → 쓰기 → 읽기 → …          쓰기 → 쓰기 → 쓰기 → … → 읽기 → 읽기 → …
      ↓      ↓      ↓      ↓                  (쌓이기만 한다)        ↓  (한 번만)
   레이아웃 레이아웃 레이아웃 …                                    레이아웃
   N 번                                                            1 번

   쓰기 횟수도 읽기 횟수도 똑같다. 다른 것은 순서뿐이다.
```

## 이 주제가 답하려는 질문

1. **무엇이 「읽기」인가** — 레이아웃을 강제하는 것과 안 하는 것을 **실측으로** 가를 수 있나.
2. **왜 섞으면 느려지나.** 그리고 **묶으면 정말 달라지나** — 같은 횟수인데.
3. **명세는 무엇을 보장하고 무엇을 안 보장하나** — 「언제 레이아웃이 도는가」를 정한 문장이 있나.

## 이 갈래의 관측 창 — ★ 창 4 는 「최신성 프로브」

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋에 이 주제의 창을 하나 더 얹는다.

```text
  창 1  --dump-dom             스크립트가 다 돈 뒤의 트리를 글자로
                               ★ 부적용 — 레이아웃은 트리에 자국을 안 남긴다 (09번 (1) 과 같은 이유)
  창 2  노드 단위 프로브        같은 루프를 조건만 바꿔 여러 벌 돌린다
  창 3  두 번 읽기              쓰기 전 / 쓴 뒤를 같은 tick 안에서
  ★ 창 4 (이 주제 고유)  최신성 프로브 — 시간을 안 재고 '값이 최신인가' 만 본다
        무엇을 답하나:  쓰기 직후 같은 tick 에서 읽으면 새 값이 오나
        왜 필요한가:    시간은 흔들린다. '느려졌다' 는 판마다 다른 수지만
                        '최신 값이 왔다' 는 결정적이다.
                        ★ 그리고 이쪽이 원인에 더 가깝다 — 최신 값을 줘야 하니까
                          레이아웃을 도는 것이지, 느리려고 도는 것이 아니다.
  ★ 창 5 (04번에서 빌린다)  performance.now() 중앙값 — 비용
        ★ 분해능 100마이크로초. 0.10 은 '공짜' 가 아니라 '못 잰다' 이다
  ★ 부적용인 창  requestAnimationFrame 으로 프레임을 갈라 재는 것
        이 도구로는 프레임이 통제되지 않는다 — (7) 에서 수치로 보인다. '못 잰 것' 이다
```

- ★ **두 창이 짝이다.** 창 ④ 는 **무엇이 레이아웃을 강제하는지**를 결정적으로 답하고, 창 ⑤ 는 **그것이 얼마인지**를 흔들리는 수로 답한다. **둘을 같이 봐야 (8)의 목록이 선다.**

## 동작 방식

### (1) 먼저 자를 잰다 — 이 도구의 눈금

**언제 쓰나** — 시간을 재기 전에. **자의 눈금을 모르면 「0.00」을 「공짜」로 읽는다.**

```html
<!-- wa09b-10-res.html -->
<!doctype html>
<meta charset="utf-8">
<title>10-res</title>
<style>body { margin: 0 } .r { width: 50%; padding: 1px; border: 1px solid rgb(204, 204, 204) } #host { width: 600px }</style>
<div id="host"></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [10, 14, 12, 14, 12, 12][i])).join('').replace(/ +$/, ''));
const med = a => a.slice().sort((x, y) => x - y)[(a.length - 1) >> 1];

O.push('먼저 자를 재 본다 — performance.now() 가 구분하는 최소 간격');
{
  const 증분 = new Set();
  let prev = performance.now();
  for (let i = 0; i < 200000; i++) { const n = performance.now(); if (n !== prev) { 증분.add(+(n - prev).toFixed(6)); prev = n; } }
  const arr = [...증분].sort((a, b) => a - b);
  O.push('  20만 번 잇달아 부르며 모은 서로 다른 증분(작은 것 다섯) = ' + arr.slice(0, 5).join(' · ') + ' ms');
  O.push('  ★ 관측된 최소 양수 증분 = ' + arr[0] + ' ms — 이 자에는 ' + arr[0] + ' ms 보다 가는 눈금이 없다.');
  O.push('  그래서 표의 0.10 은 「공짜」가 아니라 「이 자로는 못 잰다」다.');
}
O.push('');

const host = document.getElementById('host');
const rows = [];
for (let i = 0; i < 400; i++) { const d = document.createElement('div'); d.className = 'r'; d.textContent = '행 ' + i; host.appendChild(d); rows.push(d); }
let sink = 0;
const N = 9;
const bench = fn => { const t = []; for (let r = 0; r < N; r++) { const s = performance.now(); fn(r); t.push(performance.now() - s); } return med(t); };

O.push('반복을 몇 번 해야 분해능 위로 올라오나 — 교차와 분리를 같은 n 으로 견준다');
row('n', '교차 ms', '눈금 칸', '분리 ms', '눈금 칸', '비');
for (const n of [1, 5, 10, 50, 100, 200, 400]) {
  const sub = rows.slice(0, n);
  const a = bench(r => { for (const d of sub) { d.style.paddingLeft = (r % 2) + 'px'; sink += d.offsetWidth; } });
  const b = bench(r => { for (const d of sub) d.style.paddingLeft = (r % 2) + 'px'; for (const d of sub) sink += d.offsetWidth; });
  row(n, a.toFixed(2), Math.round(a / 0.1), b.toFixed(2), Math.round(b / 0.1), (a / b).toFixed(1) + '배');
}
O.push('');
O.push('★ 분자만 분해능을 넘어서는 모자란다 — 분모가 한두 칸이면 그 비는 자가 만든 허수다.');
O.push('  분모까지 열 칸을 넘는 n = 400 을 본문 수치로 쓴다.');
O.push('sink = ' + (sink > 0));

document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-res.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,4p'
먼저 자를 재 본다 — performance.now() 가 구분하는 최소 간격
  20만 번 잇달아 부르며 모은 서로 다른 증분(작은 것 다섯) = 0.1 · 0.3 · 0.4 · 0.5 ms
  ★ 관측된 최소 양수 증분 = 0.1 ms — 이 자에는 0.1 ms 보다 가는 눈금이 없다.
  그래서 표의 0.10 은 「공짜」가 아니라 「이 자로는 못 잰다」다.
(exit 0)
```

- **20만 번 잇달아 불러도 증분이 `0.1` 과 `0.2` 뿐**이다. 이 자에는 **0.1ms 보다 가는 눈금이 없다.**
- ★ **그래서 표의 `0.10` 은 「1/10 밀리초가 걸렸다」가 아니라 「한 칸도 못 채웠다」다.** 「공짜」로 읽으면 안 된다.
- **이것은 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)가 먼저 실측한 한계**를 이 주제가 물려받은 것이다. 스펙터 계열 공격 때문에 브라우저가 일부러 뭉갠 값이고, **명세가 정한 수가 아니다.**

비용 — 이 절 자체가 비용 이야기의 전제다.

### (2) ★ 창 ④ — 시간을 안 재고 「최신인가」만 본다

**언제 쓰나** — 「무엇이 레이아웃을 강제하나」를 묻기 전에. **원인 쪽을 먼저 본다.**

**던진 것** — 아래 (3)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa09b-10-fresh.html -->
<!doctype html>
<meta charset="utf-8">
<title>10-fresh</title>
<style>
  body { margin: 0; font: 14px monospace }
  #host { width: 400px }
  #t { width: 100px; height: 30px; background: rgb(204, 255, 204) }
</style>
<div id="host"><div id="t">T</div></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [34, 14, 14, 16][i])).join('').replace(/ +$/, ''));
const host = document.getElementById('host'), t = document.getElementById('t');

O.push('창 ④ — 시간을 안 재고 「값이 최신인가」만 본다');
O.push('한 tick 안에서: 읽고 → 쓰고 → 같은 tick 에서 다시 읽는다');
row('무엇을 읽었나', '쓰기 전', '쓴 뒤', '최신인가');
const probes = [
  ['t.offsetLeft', () => t.offsetLeft],
  ['t.getBoundingClientRect().left', () => t.getBoundingClientRect().left],
  ['t.clientWidth', () => t.clientWidth],
  ['host.scrollWidth', () => host.scrollWidth],
  ['getComputedStyle(t).width', () => getComputedStyle(t).width],
  ['t.textContent', () => t.textContent],
  ['t.style.width', () => t.style.width],
];
for (const [label, f] of probes) {
  host.style.paddingLeft = '0px'; t.style.width = '100px';
  const 전 = f();
  host.style.paddingLeft = '50px'; t.style.width = '120px';
  const 후 = f();
  row(label, String(전), String(후), 전 === 후 ? '안 바뀜' : '바뀌었다');
}
host.style.paddingLeft = '0px'; t.style.width = '100px';
O.push('');

O.push('쓰기는 모이고, 읽기가 그 자리에서 터뜨린다 — 중간 값은 아무도 못 본다');
host.style.paddingLeft = '10px';
host.style.paddingLeft = '20px';
host.style.paddingLeft = '30px';
O.push('  10 → 20 → 30 을 잇달아 쓰고 한 번 읽으면  t.offsetLeft = ' + t.offsetLeft);
host.style.paddingLeft = '0px';
O.push('  그 사이 10 이나 20 을 관측할 방법은 스크립트에 없다 — 읽지 않으면 레이아웃도 안 돈다.');
O.push('');

O.push('그런데 읽으면 매번 터진다 — 쓰기 사이에 읽기를 끼우면 세 값이 전부 관측된다');
const 본값 = [];
for (const px of [10, 20, 30]) { host.style.paddingLeft = px + 'px'; 본값.push(t.offsetLeft); }
O.push('  쓰기·읽기를 번갈아 하면 = ' + JSON.stringify(본값) + '   ← 관측 가능하다는 것이 곧 비용이다');
host.style.paddingLeft = '0px';
O.push('');
O.push('★ 명세가 정한 것은 「이 값은 최신이어야 한다」이지 「언제 레이아웃을 돌려라」가 아니다.');
O.push('  최신성을 지키는 방법은 구현이 고른다 — Blink 는 읽는 그 자리에서 레이아웃을 돌린다.');

document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-fresh.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,10p'
창 ④ — 시간을 안 재고 「값이 최신인가」만 본다
한 tick 안에서: 읽고 → 쓰고 → 같은 tick 에서 다시 읽는다
무엇을 읽었나                     쓰기 전       쓴 뒤         최신인가
t.offsetLeft                      0             50            바뀌었다
t.getBoundingClientRect().left    0             50            바뀌었다
t.clientWidth                     100           120           바뀌었다
host.scrollWidth                  400           450           바뀌었다
getComputedStyle(t).width         100px         120px         바뀌었다
t.textContent                     T             T             안 바뀜
t.style.width                     100px         120px         바뀌었다
(exit 0)
```

- **한 tick 안에서 쓰고 바로 읽었는데 전부 새 값이 온다.** `offsetLeft` 도, `rect.left` 도, `clientWidth` 도, `scrollWidth` 도, 계산값도.
- ★ **이것이 원인이다.** 명세가 이 속성들에 「**최신 값을 돌려주라**」고 요구하므로, 구현은 **쌓아 둔 변경을 그 자리에서 반영**할 수밖에 없다. **느리려고 도는 것이 아니라 답을 맞히려고 도는 것**이다.
- **`t.textContent` 만 안 바뀌었다** — 레이아웃과 아무 상관없는 값이라 그렇다.
- ★ **`t.style.width` 가 바뀐 것은 다른 이유다** — 그것은 **내가 방금 써 넣은 인라인 문자열을 도로 읽은 것**이지 레이아웃 결과가 아니다. **「바뀌었다」가 전부 같은 뜻이 아니라는 것**을 이 줄이 보여 준다. 그래서 창 ④ 만으로는 목록이 안 서고 **창 ⑤ 가 필요하다**((8)).

### (3) 쓰기는 모이고, 읽기가 그 자리에서 터뜨린다

**언제 쓰나** — 「쓰기가 왜 안 비싼가」가 이상할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-fresh.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,20p'
쓰기는 모이고, 읽기가 그 자리에서 터뜨린다 — 중간 값은 아무도 못 본다
  10 → 20 → 30 을 잇달아 쓰고 한 번 읽으면  t.offsetLeft = 30
  그 사이 10 이나 20 을 관측할 방법은 스크립트에 없다 — 읽지 않으면 레이아웃도 안 돈다.

그런데 읽으면 매번 터진다 — 쓰기 사이에 읽기를 끼우면 세 값이 전부 관측된다
  쓰기·읽기를 번갈아 하면 = [10,20,30]   ← 관측 가능하다는 것이 곧 비용이다

★ 명세가 정한 것은 「이 값은 최신이어야 한다」이지 「언제 레이아웃을 돌려라」가 아니다.
  최신성을 지키는 방법은 구현이 고른다 — Blink 는 읽는 그 자리에서 레이아웃을 돌린다.
(exit 0)
```

- **10 → 20 → 30 을 잇달아 쓰고 한 번만 읽으면 30 이다.** 중간의 10 과 20 은 **아무도 못 본다** — 레이아웃을 안 돌렸으니 존재한 적이 없다.
- **쓰기 사이에 읽기를 끼우면 `[10, 20, 30]` 세 값이 전부 관측된다.** ★ **관측 가능하다는 것이 곧 비용이다.** 세 번 보이려면 세 번 계산해야 한다.
- ★ **이 두 줄이 「왜 쓰기는 싸고 읽기는 비싼가」의 답 전부**다. 쓰기는 **장부에 적는 것**이고, 읽기는 **결산을 요구하는 것**이다.

```text
   같은 세 번의 쓰기, 다른 결과

   쓰기 쓰기 쓰기 → 읽기              쓰기 → 읽기 → 쓰기 → 읽기 → 쓰기 → 읽기
     10  20  30      30                 10     10    20     20    30     30
                     ↑                        ↑           ↑           ↑
              레이아웃 1 번               레이아웃 3 번 (관측된 값마다 한 번)
```

비용 — 이것이 (5)에서 잴 것의 정체다.

### (4) 반복이 몇 번 필요한가 — 자 위로 올라오는 지점

**언제 쓰나** — 비를 주장하기 전에. **분자만 자 위에 올라와도 모자란다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-res.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '6,17p'
반복을 몇 번 해야 분해능 위로 올라오나 — 교차와 분리를 같은 n 으로 견준다
n         교차 ms       눈금 칸     분리 ms       눈금 칸     비
1         0.30          3           0.20          2           1.5배
5         1.30          13          0.30          3           4.3배
10        2.50          25          0.30          3           8.3배
50        8.90          89          0.60          6           14.8배
100       16.80         168         1.50          15          11.2배
200       35.80         358         1.70          17          21.1배
400       55.30         553         2.30          23          24.0배

★ 분자만 분해능을 넘어서는 모자란다 — 분모가 한두 칸이면 그 비는 자가 만든 허수다.
  분모까지 열 칸을 넘는 n = 400 을 본문 수치로 쓴다.
(exit 0)
```

- **교차 쪽은 `n = 5`\~`10` 이면 이미 자 위**로 올라온다(눈금 여러 칸). 그런데 **그때 분모(분리)는 아직 한두 칸**이다.
- ★ **분모가 한 칸일 때의 「비」는 자가 만든 허수**다. 0.10 은 「0.10 이 걸렸다」가 아니라 「못 쟀다」이므로, 그 수로 나눈 값에는 뜻이 없다.
- **분자와 분모가 둘 다 열 칸을 넘는 `n = 400` 을 본문 수치로 쓴다**((5)). 그래서 본 실험의 행 수가 400 이다.
- ★ **이 절이 이 주제에서 가장 자주 건너뛰는 자리**다. 「30배 차이가 난다」를 **분해능 한 칸으로 나눠 만든 배수**로 적는 글이 많다.

### (5) ★ 본 실험 — 같은 횟수인데 순서만 바꾼다

**언제 쓰나** — 루프에서 기하를 읽을 때.

**던진 것** — 아래 (6)·(7)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa09b-10-mix.html -->
<!doctype html>
<meta charset="utf-8">
<title>10-mix</title>
<style>body { margin: 0 } .r { width: 50%; padding: 1px; border: 1px solid rgb(204, 204, 204) } #host { width: 600px }</style>
<div id="host"></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const med = a => a.slice().sort((x, y) => x - y)[(a.length - 1) >> 1];
const N = 9, ROWS = 400;
const host = document.getElementById('host');
const rows = [];
for (let i = 0; i < ROWS; i++) { const d = document.createElement('div'); d.className = 'r'; d.textContent = '행 ' + i; host.appendChild(d); rows.push(d); }
let sink = 0;
const bench = (label, fn) => {
  const t = [];
  for (let r = 0; r < N; r++) { const s = performance.now(); fn(r); t.push(performance.now() - s); }
  O.push(padw(label, 40) + '중앙값 ' + med(t).toFixed(2).padStart(8) + ' ms' +
         '   최소 ' + Math.min(...t).toFixed(2).padStart(8) + '   최대 ' + Math.max(...t).toFixed(2).padStart(8));
  return med(t);
};

O.push('읽기와 쓰기를 섞으면 — ' + ROWS + '행 · ' + N + '판의 중앙값');
O.push('');
const 교차 = bench('① 쓰기·읽기 교차 (한 행마다 번갈아)', r => {
  for (const d of rows) { d.style.paddingLeft = (r % 2) + 'px'; sink += d.offsetWidth; } });
const 분리 = bench('② 쓰기 다 하고 읽기 다 하기', r => {
  for (const d of rows) d.style.paddingLeft = (r % 2) + 'px';
  for (const d of rows) sink += d.offsetWidth; });
const 읽기만 = bench('③ 읽기만 (쓰기 없음)', () => {
  for (const d of rows) sink += d.offsetWidth; });
const 쓰기만 = bench('④ 쓰기만 (읽기 없음)', r => {
  for (const d of rows) d.style.paddingLeft = (r % 2) + 'px'; });
O.push('');
O.push('①/② = ' + (교차 / 분리).toFixed(1) + '배   ·   ②는 ③+④(' + (읽기만 + 쓰기만).toFixed(2) + ')와 같은 자릿수다');
O.push('★ 쓰기 횟수도 읽기 횟수도 ①과 ②가 똑같다. 다른 것은 순서뿐이다.');
O.push('');

O.push('읽기를 거꾸로 묶어 봐도 같다 — 순서가 아니라 「사이에 쓰기가 끼었나」가 가른다');
bench('⑤ 읽기 다 하고 쓰기 다 하기', r => {
  for (const d of rows) sink += d.offsetWidth;
  for (const d of rows) d.style.paddingLeft = (r % 2) + 'px'; });
bench('⑥ 앞쪽 절반만 교차, 뒤쪽 절반은 묶음', r => {
  const 반 = ROWS / 2;
  for (let i = 0; i < 반; i++) { rows[i].style.paddingLeft = (r % 2) + 'px'; sink += rows[i].offsetWidth; }
  for (let i = 반; i < ROWS; i++) rows[i].style.paddingLeft = (r % 2) + 'px';
  for (let i = 반; i < ROWS; i++) sink += rows[i].offsetWidth; });
O.push('');

setTimeout(() => {
  O.push('태스크를 갈라 보면 — 쓰기는 이 tick, 읽기는 다음 tick');
  const t0 = performance.now();
  for (const d of rows) d.style.paddingLeft = '3px';
  const 쓰기끝 = performance.now();
  setTimeout(() => {
    const t1 = performance.now();
    for (const d of rows) sink += d.offsetWidth;
    const t2 = performance.now();
    O.push('  이 tick 의 쓰기 ' + ROWS + '번 = ' + (쓰기끝 - t0).toFixed(2) + ' ms');
    O.push('  다음 tick 의 읽기 ' + ROWS + '번 = ' + (t2 - t1).toFixed(2) + ' ms  (첫 읽기 하나가 레이아웃을 한 번 돌린다)');
    O.push('  합 = ' + ((쓰기끝 - t0) + (t2 - t1)).toFixed(2) + ' ms — ②와 같은 자릿수다. 태스크를 갈라도 ①로 돌아가지 않는다.');
    O.push('sink = ' + (sink > 0));
    document.body.appendChild(Object.assign(document.createElement('script'),
      {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
  }, 0);
}, 0);
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-mix.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,9p'
읽기와 쓰기를 섞으면 — 400행 · 9판의 중앙값

① 쓰기·읽기 교차 (한 행마다 번갈아)    중앙값    55.60 ms   최소    51.30   최대    83.80
② 쓰기 다 하고 읽기 다 하기            중앙값     2.80 ms   최소     0.70   최대     4.00
③ 읽기만 (쓰기 없음)                   중앙값     0.30 ms   최소     0.20   최대     0.80
④ 쓰기만 (읽기 없음)                   중앙값     0.10 ms   최소     0.10   최대     0.60

①/② = 19.9배   ·   ②는 ③+④(0.40)와 같은 자릿수다
★ 쓰기 횟수도 읽기 횟수도 ①과 ②가 똑같다. 다른 것은 순서뿐이다.
(exit 0)
```

- **교차와 묶음은 쓰기 횟수도 읽기 횟수도 똑같다.** 다른 것은 **순서뿐**인데 **자릿수가 바뀐다.**
- **③ 읽기만 · ④ 쓰기만은 둘 다 분해능 언저리**다 — 각각을 따로 하면 **이 자로는 잴 수 없을 만큼 싸다.**
- **② 는 ③ + ④ 와 같은 자릿수**다. 즉 **묶으면 「읽기 비용 + 쓰기 비용」으로 떨어진다.** ① 의 초과분이 전부 **강제 레이아웃 N번**이다.
- ★ **신호 대 잡음** — ①과 ② 는 **한 자릿수 이상** 차이라 신호가 압도적이다. **이 비교만 결론으로 쓴다.**

### (6) 순서가 아니라 「사이에 쓰기가 끼었나」가 가른다

**언제 쓰나** — 「읽기를 먼저 하면 되나?」가 궁금할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-mix.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '11,13p'
읽기를 거꾸로 묶어 봐도 같다 — 순서가 아니라 「사이에 쓰기가 끼었나」가 가른다
⑤ 읽기 다 하고 쓰기 다 하기            중앙값     2.50 ms   최소     0.30   최대     3.40
⑥ 앞쪽 절반만 교차, 뒤쪽 절반은 묶음   중앙값    33.00 ms   최소     2.50   최대    35.40
(exit 0)
```

- **⑤ 읽기를 먼저 다 하고 쓰기를 다 해도 ② 와 같다.** 「읽기가 먼저냐 쓰기가 먼저냐」는 상관없다.
- **⑥ 앞쪽 절반만 교차했더니 ① 과 ② 의 중간**이다. **섞인 만큼만 비싸진다** — 임계점이 있는 게 아니라 **비례한다.**
- ★ 그래서 고치는 법이 「순서를 바꿔라」가 아니라 「**읽기 구간과 쓰기 구간을 나눠라**」인 것이다.

### (7) 태스크를 갈라도 — 그리고 프레임은 못 갈랐다

**언제 쓰나** — 「그럼 나중에 읽으면 되나?」가 궁금할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-mix.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '15,19p'
태스크를 갈라 보면 — 쓰기는 이 tick, 읽기는 다음 tick
  이 tick 의 쓰기 400번 = 0.20 ms
  다음 tick 의 읽기 400번 = 0.50 ms  (첫 읽기 하나가 레이아웃을 한 번 돌린다)
  합 = 0.70 ms — ②와 같은 자릿수다. 태스크를 갈라도 ①로 돌아가지 않는다.
sink = true
(exit 0)
```

- **쓰기를 이 tick 에, 읽기를 다음 tick 에 두면 ② 와 같은 자릿수**다. **태스크를 갈라도 ① 로 돌아가지 않는다** — 다음 tick 의 **첫 읽기 하나가 레이아웃을 한 번** 돌리고 나머지는 그 결과를 쓴다.
- ★ **얻는 것은 「레이아웃을 안 돌린다」가 아니라 「한 번만 돌린다」다.** 그건 ② 가 이미 하고 있다.

**`requestAnimationFrame` 으로 나누면? — 이 도구로는 못 잰다.**

```html
<!-- wa09b-10-raf.html -->
<!doctype html>
<meta charset="utf-8">
<title>10-raf</title>
<div id="host"></div>
<script>
const O = [];
const host = document.getElementById('host');
for (let i = 0; i < 400; i++) { const d = document.createElement('div'); d.textContent = '행 ' + i; host.appendChild(d); }
let 실행 = 0;
const 시각 = [];
const t0 = performance.now();
const 다음 = () => { 실행++; 시각.push((performance.now() - t0).toFixed(0)); requestAnimationFrame(다음); };
requestAnimationFrame(다음);
while (performance.now() - t0 < 100) { /* 동기 루프로 100ms 를 태운다 */ }
setTimeout(() => {
  setTimeout(() => {
    O.push('rAF 콜백을 끝없이 이어 걸고 --dump-dom 이 기다리는 끝까지 세었다');
    O.push('  실행 횟수 = ' + 실행 + '   실행 시각(ms) = ' + (시각.join(',') || '(없음)')
         + '   경과 = ' + (performance.now() - t0).toFixed(0) + 'ms');
    document.body.appendChild(Object.assign(document.createElement('script'),
      {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
  }, 0);
}, 0);
</script>
```

```text
$ for i in $(seq 5); do google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-raf.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'; done
rAF 콜백을 끝없이 이어 걸고 --dump-dom 이 기다리는 끝까지 세었다
  실행 횟수 = 2   실행 시각(ms) = 100,138   경과 = 139ms
rAF 콜백을 끝없이 이어 걸고 --dump-dom 이 기다리는 끝까지 세었다
  실행 횟수 = 1   실행 시각(ms) = 138   경과 = 144ms
rAF 콜백을 끝없이 이어 걸고 --dump-dom 이 기다리는 끝까지 세었다
  실행 횟수 = 0   실행 시각(ms) = (없음)   경과 = 132ms
rAF 콜백을 끝없이 이어 걸고 --dump-dom 이 기다리는 끝까지 세었다
  실행 횟수 = 1   실행 시각(ms) = 125   경과 = 128ms
rAF 콜백을 끝없이 이어 걸고 --dump-dom 이 기다리는 끝까지 세었다
  실행 횟수 = 0   실행 시각(ms) = (없음)   경과 = 135ms
(exit 0)
```

- **같은 파일을 다섯 판 던졌더니 rAF 콜백 실행 횟수가 판마다 달랐다** — 위 블록에서 한 판은 아예 0 이고 다른 판은 둘이다. **프레임이 오는지 자체가 판마다 다르다.**
- ★ **`--dump-dom` 은 `load` 뒤의 `setTimeout(…, 0)` 을 두 겹까지만 기다린다** — 세 겹을 걸면 **출력이 통째로 사라진다**(직접 확인했다). 그래서 「쓰기는 프레임 N, 읽기는 프레임 N+1」이라는 **두 프레임짜리 실험이 성립하지 않는다.**
- ★ **이것은 「안 돌려 본 것」이 아니라 「못 잰 것」이다.** 「rAF 로 미루면 싸진다」는 이 문서가 **주장하지 않는다.** 재려면 CDP 로 프레임을 몰아야 한다.
- **그래도 (7)의 앞부분이 방향은 보여 준다** — 읽기를 **뒤로 미루면** 레이아웃이 **한 번으로 줄어든다.** rAF 가 하는 일도 그것이다.

비용 — 이 절은 **도구의 한계를 비용으로 치른 자리**다.

### (8) ★ 무엇이 「읽기」인가 — 목록을 실측으로 만든다

**언제 쓰나** — 코드를 읽으며 「이 줄이 방아쇠인가」를 판정할 때.

**던진 것** — 반복을 30 / 300 / 3000 세 단으로 두어 **어느 줄이 어디서 자 위로 올라오는지**를 같이 본다.

```html
<!-- wa09b-10-reads.html -->
<!doctype html>
<meta charset="utf-8">
<title>10-reads</title>
<style>body { margin: 0 } .r { width: 50%; padding: 1px; border: 1px solid rgb(204, 204, 204) } #host { width: 600px }</style>
<div id="host"></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const med = a => a.slice().sort((x, y) => x - y)[(a.length - 1) >> 1];
const host = document.getElementById('host');
const rows = [];
for (let i = 0; i < 300; i++) { const d = document.createElement('div'); d.className = 'r'; d.textContent = '행 ' + i; host.appendChild(d); rows.push(d); }
const one = rows[150];
let sink = 0;
const N = 3, TIERS = [30, 300, 3000];
const bench = (fn, it) => { const t = []; for (let r = 0; r < N; r++) { const s = performance.now(); fn(it); t.push(performance.now() - s); } return med(t); };

const probes = [
  ['el.offsetTop', () => one.offsetTop],
  ['el.offsetWidth', () => one.offsetWidth],
  ['el.offsetParent', () => one.offsetParent ? 1 : 0],
  ['el.clientWidth', () => one.clientWidth],
  ['el.scrollTop', () => one.scrollTop],
  ['el.scrollHeight', () => one.scrollHeight],
  ['el.getBoundingClientRect()', () => one.getBoundingClientRect().top],
  ['el.getClientRects().length', () => one.getClientRects().length],
  ['el.innerText.length', () => one.innerText.length],
  ['window.scrollY', () => scrollY],
  ['document.elementFromPoint(5, 5)', () => document.elementFromPoint(5, 5) ? 1 : 0],
  ['getComputedStyle(el).width', () => getComputedStyle(one).width.length],
  ['getComputedStyle(el).color', () => getComputedStyle(one).color.length],
  ['getComputedStyle(el) 부르기만', () => getComputedStyle(one) ? 1 : 0],
  ['el.checkVisibility()', () => one.checkVisibility() ? 1 : 0],
  ['el.textContent.length', () => one.textContent.length],
  ['el.style.paddingLeft', () => one.style.paddingLeft.length],
  ['el.className.length', () => one.className.length],
  ['el.getAttribute("class")', () => one.getAttribute('class').length],
  ['el.children.length', () => one.children.length],
  ['el.matches(".r")', () => one.matches('.r') ? 1 : 0],
  ['el.closest("#host")', () => one.closest('#host') ? 1 : 0],
  ['document.querySelector(".r")', () => document.querySelector('.r') ? 1 : 0],
];

O.push('무엇이 「읽기」인가 — 쓰기 한 번 + 읽기 한 번을 한 묶음으로 반복했다');
O.push('한 반복 = host.style.paddingLeft 를 바꾸고(쓰기) 아래 것을 한 번 읽는다');
O.push('');
O.push(padw('읽은 것', 34) + TIERS.map(t => padw(t + '회', 11)).join('') + padw('회당 µs', 11) + '쓰기만 한 것과 갈리는 반복 수');
const 기준 = [];
for (const it of TIERS) 기준.push(bench(n => { for (let i = 0; i < n; i++) { host.style.paddingLeft = (i % 2) + 'px'; sink += 1; } }, it));
O.push(padw('(쓰기만 — 읽기 없음)', 34) + 기준.map(v => padw(v.toFixed(2), 11)).join(''));
O.push('');
for (const [label, f] of probes) {
  const ms = TIERS.map(it => bench(n => { for (let i = 0; i < n; i++) { host.style.paddingLeft = (i % 2) + 'px'; sink += Number(f()) || 0; } }, it));
  const 회당 = (ms[2] * 1000 / TIERS[2]).toFixed(2);
  const i = ms.findIndex((v, k) => v - 기준[k] >= 1);
  const 지점 = i < 0 ? '3000회로도 안 갈린다' : TIERS[i] + '회';
  O.push(padw(label, 34) + ms.map(v => padw(v.toFixed(2), 11)).join('') + padw(회당, 11) + 지점);
}
O.push('');
O.push('sink = ' + (sink > 0));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-reads.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
무엇이 「읽기」인가 — 쓰기 한 번 + 읽기 한 번을 한 묶음으로 반복했다
한 반복 = host.style.paddingLeft 를 바꾸고(쓰기) 아래 것을 한 번 읽는다

읽은 것                           30회       300회      3000회     회당 µs    쓰기만 한 것과 갈리는 반복 수
(쓰기만 — 읽기 없음)             0.00       0.10       0.80       

el.offsetTop                      3.60       32.10      346.10     115.37     30회
el.offsetWidth                    3.00       30.20      318.50     106.17     30회
el.offsetParent                   3.40       34.40      353.30     117.77     30회
el.clientWidth                    2.70       28.20      263.70     87.90      30회
el.scrollTop                      2.80       34.50      376.30     125.43     30회
el.scrollHeight                   3.60       30.50      339.40     113.13     30회
el.getBoundingClientRect()        2.40       34.80      347.50     115.83     30회
el.getClientRects().length        4.20       35.90      321.50     107.17     30회
el.innerText.length               3.00       31.00      354.20     118.07     30회
window.scrollY                    3.10       39.50      371.40     123.80     30회
document.elementFromPoint(5, 5)   9.50       93.40      1013.50    337.83     30회
getComputedStyle(el).width        3.50       28.20      379.80     126.60     30회
getComputedStyle(el).color        0.30       1.70       14.60      4.87       300회
getComputedStyle(el) 부르기만     0.10       0.00       1.20       0.40       3000회로도 안 갈린다
el.checkVisibility()              0.20       1.40       12.90      4.30       300회
el.textContent.length             0.00       0.10       0.90       0.30       3000회로도 안 갈린다
el.style.paddingLeft              0.00       0.10       0.80       0.27       3000회로도 안 갈린다
el.className.length               0.00       0.10       0.70       0.23       3000회로도 안 갈린다
el.getAttribute("class")          0.00       0.10       0.70       0.23       3000회로도 안 갈린다
el.children.length                0.00       0.10       0.80       0.27       3000회로도 안 갈린다
el.matches(".r")                  0.00       0.10       0.80       0.27       3000회로도 안 갈린다
el.closest("#host")               0.00       0.10       0.90       0.30       3000회로도 안 갈린다
document.querySelector(".r")      0.00       0.10       0.90       0.30       3000회로도 안 갈린다

sink = true
(exit 0)
```

- **위 열두 줄은 반복 30번이면 이미 갈린다** — **한 번 읽는 데 100마이크로초 대**다. 아래 여덟 줄은 **3000번을 반복해도 「쓰기만 한 것」과 안 갈린다.**
- ★ **이름으로는 안 보이는 경계**가 셋 있다.
  - **`window.scrollY` 가 방아쇠다.** 요소를 안 건드리는데도 레이아웃이 필요하다.
  - **`innerText` 는 방아쇠이고 `textContent` 는 아니다.** 앞엣것은 **「보이는 대로의 텍스트」라** 레이아웃을 거친다([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)가 그 차이의 정본이다).
  - **`getComputedStyle(el)` 은 부르기만 하면 안 갈리고**, 거기서 **`width` 를 읽으면 방아쇠, `color` 를 읽으면 중간**이다. **속성마다 다르다**([08번 주제](../08-getcomputedstyle/2-summary.md)의 실측과 같은 결론).
- ★ **중간 단이 따로 있다** — `getComputedStyle(el).color` 와 `checkVisibility()` 는 **300번에서 갈린다.** 레이아웃까지는 안 가고 **스타일 재계산**까지만 간다. **두 단계가 다른 일**이라는 것이 여기서 수치로 드러난다.
- **`elementFromPoint` 가 가장 비싸다** — 레이아웃 위에 **히트 테스트**가 얹힌다([09번 주제](../09-element-geometry/2-summary.md)의 창 ④ 가 그것이다).
- **선택자 조회(`matches`·`closest`·`querySelector`)는 방아쇠가 아니다.** 트리만 보면 되기 때문이다.

```text
   실측이 만든 세 칸

   레이아웃까지 간다 (반복 30 이면 갈린다)
     offsetTop/Left/Width/Height · offsetParent · client* · scrollTop/Height
     getBoundingClientRect() · getClientRects() · innerText
     window.scrollX/Y · elementFromPoint(가장 비싸다)
     getComputedStyle(el).width  ← 속성에 달렸다

   스타일 재계산까지만 간다 (반복 300 이면 갈린다)
     getComputedStyle(el).color · el.checkVisibility()

   아무것도 안 돌린다 (반복 3000 으로도 안 갈린다)
     textContent · style.<속성>(인라인 되읽기) · className · getAttribute
     children.length · matches() · closest() · querySelector()
     getComputedStyle(el) 을 부르기만 하는 것
```

비용 — 이 절 자체가 비용표다. **자릿수와 「갈리는 반복 수」 칸만 결론으로 쓴다.**

### (9) 무엇을 쓰느냐도 가른다 — 여기서 직관이 뒤집힌다

**언제 쓰나** — 「색만 바꾸는데 왜 느리지?」일 때.

```html
<!-- wa09b-10-writes.html -->
<!doctype html>
<meta charset="utf-8">
<title>10-writes</title>
<style>body { margin: 0 } .r { width: 50%; padding: 1px; border: 1px solid rgb(204, 204, 204) } #host { width: 600px }</style>
<div id="host"></div>
<div id="far" style="width: 123px">다른 가지에 있는 요소</div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const med = a => a.slice().sort((x, y) => x - y)[(a.length - 1) >> 1];
const host = document.getElementById('host'), far = document.getElementById('far');
const rows = [];
for (let i = 0; i < 300; i++) { const d = document.createElement('div'); d.className = 'r'; d.textContent = '행 ' + i; host.appendChild(d); rows.push(d); }
const one = rows[150];
let sink = 0;
const N = 9, IT = 300;
const bench = (label, fn) => {
  const t = []; for (let r = 0; r < N; r++) { const s = performance.now(); for (let i = 0; i < IT; i++) fn(i); t.push(performance.now() - s); }
  O.push(padw(label, 48) + med(t).toFixed(2).padStart(9) + ' ms'); return med(t);
};

O.push('무엇을 쓰느냐도 가른다 — 읽는 것은 전부 one.offsetTop 하나로 고정, ' + IT + '회 · ' + N + '판 중앙값');
O.push('');
bench('조상 #host 에 padding 을 쓰고 읽기', i => { host.style.paddingLeft = (i % 2) + 'px'; sink += one.offsetTop; });
bench('조상 #host 에 color 를 쓰고 읽기', i => { host.style.color = (i % 2) ? 'rgb(255,0,0)' : 'rgb(0,0,255)'; sink += one.offsetTop; });
bench('잎 #one 에 color 를 쓰고 읽기', i => { one.style.color = (i % 2) ? 'rgb(255,0,0)' : 'rgb(0,0,255)'; sink += one.offsetTop; });
bench('조상 #host 에 transform 을 쓰고 읽기', i => { host.style.transform = 'translateX(' + (i % 2) + 'px)'; sink += one.offsetTop; });
bench('조상 #host 에 opacity 를 쓰고 읽기', i => { host.style.opacity = (i % 2) ? '0.9' : '1'; sink += one.offsetTop; });
host.style.transform = ''; host.style.opacity = ''; host.style.color = '';
O.push('');
O.push('쓴 자리와 읽는 자리가 달라도 마찬가지다 — 레이아웃은 문서 하나에 하나다');
bench('#host 에 쓰고 같은 가지의 one.offsetTop 읽기', i => { host.style.paddingLeft = (i % 2) + 'px'; sink += one.offsetTop; });
bench('#host 에 쓰고 다른 가지의 far.offsetTop 읽기', i => { host.style.paddingLeft = (i % 2) + 'px'; sink += far.offsetTop; });
bench('#host 에 쓰고 document.body.offsetHeight 읽기', i => { host.style.paddingLeft = (i % 2) + 'px'; sink += document.body.offsetHeight; });
O.push('');
O.push('sink = ' + (sink > 0));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-writes.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
무엇을 쓰느냐도 가른다 — 읽는 것은 전부 one.offsetTop 하나로 고정, 300회 · 9판 중앙값

조상 #host 에 padding 을 쓰고 읽기                  34.80 ms
조상 #host 에 color 를 쓰고 읽기                   144.40 ms
잎 #one 에 color 를 쓰고 읽기                        1.80 ms
조상 #host 에 transform 을 쓰고 읽기                 2.10 ms
조상 #host 에 opacity 를 쓰고 읽기                   2.10 ms
(exit 0)
```

- ★ **직관과 반대다.** `color` 는 레이아웃과 무관한 속성인데 **조상에 쓰면 가장 비싸다.**
- **잎에 `color` 를 쓰면 싸다.** 갈라 보면 원인이 나온다 — **`color` 는 상속되는 속성**이라 조상에 쓰면 **자손 300개의 스타일 재계산**이 번진다. 그 비용이 레이아웃보다 컸다.
- **`transform`·`opacity` 를 조상에 써도 싸다** — 둘은 **레이아웃을 더럽히지 않는다**(정본: [CSS 56번 주제](../../languages/css/syntax/56-rendering-pipeline-and-will-change/2-summary.md)). 그래서 그 뒤의 `offsetTop` 읽기가 **되돌릴 것이 없다.**
- ★ **그래서 「읽기·쓰기를 섞지 마라」는 반쪽짜리 처방**이다. 정확히는 **「무효화한 뒤에 읽지 마라」이고,** 무엇이 무효화되는지는 **쓴 속성과 쓴 자리**가 정한다.

### (10) 레이아웃은 문서에 하나다

**언제 쓰나** — 「내가 건드린 건 저쪽인데」일 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-10-writes.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,12p'
쓴 자리와 읽는 자리가 달라도 마찬가지다 — 레이아웃은 문서 하나에 하나다
#host 에 쓰고 같은 가지의 one.offsetTop 읽기        33.60 ms
#host 에 쓰고 다른 가지의 far.offsetTop 읽기        38.30 ms
#host 에 쓰고 document.body.offsetHeight 읽기       34.30 ms
(exit 0)
```

- **다른 가지의 요소를 읽어도 값이 같다.** 레이아웃은 **문서 단위**로 도므로 **어디를 읽든 같은 대가**다.
- ★ **그래서 「컴포넌트를 나눴으니 괜찮다」가 안 통한다.** 남이 쓴 코드가 쓰기를 하고 내 코드가 읽으면, **둘 다 자기 몫만 했는데 합쳐서 느려진다.**
- 이 성질 때문에 **큰 앱에서 진단이 특히 어렵다** — 원인과 증상이 **다른 파일**에 있다.

### (11) 고치는 형태

**언제 쓰나** — 이미 섞여 있는 코드를 고칠 때.

```html demo
<button id="d10a">교차로 200번</button>
<button id="d10b">묶어서 200번</button>
<div id="d10out">버튼을 눌러 보세요</div>
<div id="d10rows"></div>
<style>
  #d10out { font-family: monospace; white-space: pre; background: #0f172a; color: #e2e8f0; padding: 8px; margin-top: 6px; }
  #d10rows > div { width: 50%; padding: 1px; border: 1px solid #ccc; font: 11px monospace; }
</style>
<script>
  const 칸 = document.getElementById('d10rows');
  const 행 = [];
  for (let i = 0; i < 200; i++) { const d = document.createElement('div'); d.textContent = '행 ' + i; 칸.appendChild(d); 행.push(d); }
  let sink = 0, 교차 = null, 묶음 = null;
  const 보이기 = () => document.getElementById('d10out').textContent =
    '교차 (쓰고 읽고 쓰고 읽고) = ' + (교차 === null ? '아직' : 교차.toFixed(2) + ' ms') +
    '\n묶음 (다 쓰고 다 읽기)    = ' + (묶음 === null ? '아직' : 묶음.toFixed(2) + ' ms');
  document.getElementById('d10a').onclick = () => {
    const s = performance.now();
    for (const d of 행) { d.style.paddingLeft = (sink % 2) + 'px'; sink += d.offsetWidth; }
    교차 = performance.now() - s; 보이기();
  };
  document.getElementById('d10b').onclick = () => {
    const s = performance.now();
    for (const d of 행) d.style.paddingLeft = (sink % 2) + 'px';
    for (const d of 행) sink += d.offsetWidth;
    묶음 = performance.now() - s; 보이기();
  };
</script>
```

> **보이는 것** — 화면에는 200개의 가는 줄만 있고 **버튼을 눌러도 눈에 보이는 변화는 없다**(패딩이 0과 1 사이를 오갈 뿐이다). 달라지는 것은 검은 칸의 숫자뿐이다.\
> 「교차」 버튼의 수가 「묶음」 버튼의 수보다 **한 자릿수 이상 크다.** 같은 200번의 쓰기와 200번의 읽기인데 순서만 다르다.\
> **바꿔 볼 것** — `d.offsetWidth` 를 `d.textContent.length` 로 바꾸면 **두 수가 둘 다 분해능 언저리로 내려간다**(레이아웃을 안 읽으니 방아쇠가 없다) · 행 수를 200 에서 20 으로 줄여 보라 — **자로 잡히는 차이가 남는지** (4)에서 본 눈금을 떠올리며 보면 된다\
> ★ **수를 외우지 마라.** 이 demo 가 보여 주는 것은 **두 수의 자릿수 차이**이고, 절댓값은 기계마다 다르다.

*(Chrome 151 headless 실측 — `--window-size=1000,800`, 행 200 · 두 버튼을 차례로 눌렀다: 교차 79.80ms · 묶음 1.80ms. 같은 래퍼를 세 판 돌려 교차 79.80 / 93.20 / 72.60 · 묶음 1.80 / 1.30 / 1.50 이었다 — **자릿수만 재현된다.** 같은 판에서 `offsetWidth` 를 `textContent.length` 로 바꾼 루프는 교차 0.50 / 0.30 / 0.20 · 묶음 0.10 / 0.10 / 0.10 으로 **둘 다 분해능 한두 칸**이었다.)*

- **고치는 형태는 한 줄이다** — **읽기를 위로 몰고 쓰기를 아래로 몬다.**

```js
// 고치기 전 — 한 행마다 번갈아
for (const el of 목록) { el.style.height = el.offsetWidth + 'px'; }

// 고친 뒤 — 읽기를 다 하고 쓰기를 다 한다
const 폭 = 목록.map(el => el.offsetWidth);     // 읽기 구간
목록.forEach((el, i) => el.style.height = 폭[i] + 'px');   // 쓰기 구간
```

비용 — 배열 하나가 는다. **자릿수를 사는 값으로는 싸다.**

## 문법 — 형태와 규칙

이 주제에는 「이 주제만의 API」가 없다. 그래서 이 절은 **「무엇이 방아쇠인가」의 목록**으로 읽는다.

### 형태 — 방아쇠가 되는 표면

```js
// 레이아웃까지 간다 (실측: 반복 30 이면 갈린다)
el.offsetTop  el.offsetLeft  el.offsetWidth  el.offsetHeight  el.offsetParent
el.clientTop  el.clientLeft  el.clientWidth  el.clientHeight
el.scrollTop  el.scrollLeft  el.scrollWidth  el.scrollHeight
el.getBoundingClientRect()   el.getClientRects()
el.innerText
window.scrollX  window.scrollY
document.elementFromPoint(x, y)
getComputedStyle(el).width      // 레이아웃이 필요한 속성일 때

// 스타일 재계산까지만 간다 (실측: 반복 300 이면 갈린다)
getComputedStyle(el).color      // 레이아웃이 필요 없는 속성
el.checkVisibility()

// 아무것도 안 돌린다 (실측: 반복 3000 으로도 안 갈린다)
el.textContent   el.className   el.getAttribute(…)   el.children.length
el.style.paddingLeft            // 인라인에 쓴 것을 도로 읽는 것
el.matches(…)  el.closest(…)  document.querySelector(…)
getComputedStyle(el)            // 부르기만 하는 것
```

### 금지 사례 — 형태는 맞는데 조용히 느려지는 자리

```js
// 1. 한 행마다 번갈아 — 이 주제의 원형
for (const el of 목록) el.style.height = el.offsetWidth + 'px';

// 2. 읽기가 함수 안에 숨어 있다 — 호출부만 봐서는 안 보인다
for (const el of 목록) { el.classList.add('on'); 높이맞추기(el); }  // 안에서 rect 를 읽는다

// 3. 「저쪽 요소니까 괜찮겠지」 — 레이아웃은 문서에 하나다
for (const el of 목록) { el.style.width = '10px'; sum += 다른요소.offsetTop; }

// 4. 상속되는 속성을 조상에 쓴다 — 자손 전부의 스타일이 다시 계산된다
for (const … ) { 조상.style.color = c; sum += el.offsetTop; }

// 5. 분해능 한 칸을 근거로 배수를 말한다
'0.10ms 대 3.00ms 니까 30배'      // 0.10 은 '못 잰 것' 이다

// 6. rAF 안이면 공짜라고 믿는다 — 프레임 안에서도 읽으면 강제된다
requestAnimationFrame(() => { for (const el of 목록) { el.style.top = …; sum += el.offsetTop; } });
```

### 어디서 헷갈리나

- **「읽기가 비싸다」가 아니다** — 읽기만 하면 싸다. **더럽힌 뒤에 읽는 것**이 비싸다.
- **「쓰기가 싸다」도 아니다** — 쓰기는 **미뤄진 것**이지 공짜가 아니다. 언젠가는 계산된다.
- **`textContent` 와 `innerText`** — 이름이 닮았는데 **한쪽만 방아쇠**다.
- **`getComputedStyle` 은 한 가지 일이 아니다** — 어느 속성을 읽느냐로 단이 갈린다.

## 어디서 틀리나

### 1. 루프 안에서 번갈아 한다

실측에서 **400행에 교차 쪽이 묶음 쪽보다 한 자릿수 넘게 컸다**((5)의 블록). **같은 횟수인데 순서만 다르다.**

### 2. 읽기가 헬퍼 함수 안에 숨는다

호출부에는 `el.classList.add('on')` 만 보이는데 헬퍼가 `getBoundingClientRect()` 를 읽는다. **(8)의 목록을 외워 두면 함수 이름이 아니라 그 안을 보게 된다.**

### 3. 분해능 한 칸을 분모로 쓴다

(4)의 표에서 **n 이 작을 때 분모가 눈금 한두 칸**이었다. 그 수로 나눈 배수에는 뜻이 없다.

### 4. 색만 바꾸니 괜찮다고 생각한다

실측에서 **조상에 `color` 를 쓰는 쪽이 `padding` 보다 비쌌다**((9)의 블록 — 네 배 남짓). **상속이 번진다.**

### 5. 다른 컴포넌트니까 상관없다고 생각한다

레이아웃은 **문서에 하나**다. 실측에서 **다른 가지를 읽어도 같은 값**이었다.

### 6. rAF 로 옮기면 해결됐다고 믿는다

**프레임 안에서도 더럽힌 뒤에 읽으면 강제된다.** rAF 가 주는 것은 「한 프레임에 한 번으로 모을 기회」이지 면제가 아니다. ★ 그리고 **이 문서는 그 효과를 재지 못했다**((7)).

### 7. 「테스트가 통과하니 괜찮다」

**결과는 언제나 옳다.** 스래싱은 **값이 틀리는 버그가 아니라 느려지는 버그**다. 단위 테스트로는 영영 안 잡힌다.

## 구현 세부사항 대 언어 보장

★★★ **이 절이 이 주제의 본체다.** 다른 주제에서는 「명세가 정한 것」이 대부분인데, 여기서는 **핵심이 전부 구현 쪽**이다.

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `offsetTop`·`rect` 등이 **최신 값을 돌려주는 것** | **명세**(CSSOM View — 읽기 전에 레이아웃을 최신화하도록 요구한다) |
| 쓰기가 **미뤄질 수 있다는 것**(중간 값이 관측되지 않는 것) | **명세**(렌더링은 이벤트 루프의 렌더링 단계에서 일어난다 — HTML) |
| **「언제 레이아웃이 도는가」** | ★ **아무도 안 정한다.** 명세는 「읽을 때 최신이어야 한다」만 요구하고, **그 사이에 몇 번 도는지·어디까지 다시 도는지는 구현의 자유**다 |
| **「읽기·쓰기를 섞으면 느려진다」** | ★ **구현.** 명세에는 이런 문장이 없다. 다만 CSSOM View 가 노트로 **「이 속성들을 읽으면 레이아웃이 강제될 수 있다」고** 경고한다 |
| (8)의 **세 칸 목록** | **구현 + 이 판의 관찰.** 어느 속성이 레이아웃을 필요로 하는지는 **엔진의 무효화 설계**에 달렸다 |
| `getComputedStyle(el).color` 가 **중간 단**인 것 | **구현.** 스타일 재계산과 레이아웃이 별개 단계라는 것은 파이프라인 설계다([CSS 56번 주제](../../languages/css/syntax/56-rendering-pipeline-and-will-change/2-summary.md)) |
| `transform`·`opacity` 가 **레이아웃을 안 더럽히는 것** | **구현**(합성 단계로 보내는 최적화). 명세가 「이 속성은 레이아웃을 안 건드린다」고 못 박지는 않는다 |
| **상속 속성이 자손으로 번지는 것** | **명세**(상속은 CSS 가 정한다) **+ 구현**(그 재계산을 얼마나 좁힐 수 있나) |
| **모든 시간 수치** | **구현 + 머신 + 그 판의 부하.** 자릿수와 순위만 결론으로 쓴다 |
| `performance.now()` 의 분해능 **100마이크로초** | **구현**(Blink 의 정책) |
| **rAF 가 이 도구에서 0\~1회 실행되는 것** | **도구**(`--dump-dom` 의 대기 규칙) |

- ★ **그래서 이 주제는 「표준을 읽으면 안다」가 성립하지 않는다.** 명세를 끝까지 읽어도 **「교차하면 N번 돈다」는 문장이 없다.** 알려면 **재는 수밖에 없다** — 이 문서가 목록을 실측으로 만든 이유다.
- ★ **바꿔 말하면 이 주제의 결론은 엔진이 바뀌면 바뀔 수 있다.** 실제로 **`transform`·`opacity` 가 싼 것**은 십수 년 전에는 사실이 아니었다. **「지금 이 판에서 그렇다」로 읽어라.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 목록의 치수를 재서 반영한다 | 읽기 구간 → 쓰기 구간 | 한 행마다 번갈아 |
| 여러 요소의 위치를 읽는다 | 한 번에 모아 배열로 | 필요할 때마다 그때그때 |
| 애니메이션 | `transform`·`opacity` | `top`·`left`·`width` |
| 「보이나」를 자주 묻는다 | 목록의 **35번 주제**(IntersectionObserver) | 스크롤마다 `rect` 읽기 |
| 크기 변화를 따라간다 | 목록의 **36번 주제**(ResizeObserver) | 폴링으로 `offsetWidth` 읽기 |
| 쓰기를 프레임에 맞춘다 | 목록의 **38번 주제**(`requestAnimationFrame`) | `setTimeout` 으로 어림잡기 |
| 비용을 주장한다 | 분자·분모가 **둘 다** 자 위에 올라오는 반복 수 | 분해능 한 칸을 분모로 |
| 진단한다 | 개발자 도구의 Performance 패널 | 코드만 읽고 짐작하기 |
| 쓰기만 하고 안 읽어도 되나 | 그대로 둔다 — 미뤄진다 | 「확인차」 한 번 읽기 |

## 핵심 문장

1. **명세가 정한 것은 「값이 최신이어야 한다」이지 「언제 레이아웃을 돌려라」가 아니다.** 이 주제의 본체는 명세 밖에 있다.
2. **쓰기는 쌓이고 읽기가 터뜨린다.** 관측되지 않은 중간 값은 계산된 적도 없다.
3. **비싼 것은 읽기도 쓰기도 아니라 섞는 것이다** — 실측에서 같은 횟수인데 **자릿수가 하나 넘게 갈렸다**.
4. **섞인 만큼만 비싸진다** — 절반만 교차하면 절반쯤 비싸다. 임계점이 아니라 비례다.
5. **무엇이 「읽기」인지는 이름으로 안 보인다** — `innerText` 는 방아쇠이고 `textContent` 는 아니다.
6. **무엇을 쓰느냐도 가른다** — 조상에 쓴 `color` 가 `padding` 보다 비쌌다(상속이 번진다).
7. **레이아웃은 문서에 하나다** — 남의 컴포넌트가 더럽히면 내 읽기가 비싸진다.
8. **자를 먼저 재라.** `0.10` 은 공짜가 아니라 「못 쟀다」이고, 그것을 분모로 쓴 배수는 허수다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 10번). **이 갈래에서 유일하게 실패 모드를 주제로 세운 자리**라는 설명이 거기 있다
- [08번 주제](../08-getcomputedstyle/2-summary.md) — `getComputedStyle`. 그 주제의 마지막 절이 **이 주제의 씨앗**이다(`color` 대 `width` 의 비용 차이)
- [09번 주제](../09-element-geometry/2-summary.md) — ★ **방아쇠 목록의 절반이 그 주제의 표면**이다. 좌표계·`offsetParent` 는 그쪽이 정본
- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) — `performance.now()` 의 **분해능 100마이크로초** 실측과 **`innerText` 대 `textContent`** 의 정본
- [11번 주제](../11-scroll-control/2-summary.md) — `scrollTop` 에 **쓰는 것**도 같은 이야기 안에 있다
- 목록의 **35번 주제**(IntersectionObserver) — 「보이나」를 **레이아웃을 강제하지 않고** 묻는 법
- 목록의 **36번 주제**(ResizeObserver) — 치수 변화를 **폴링 없이** 받는 법
- 목록의 **38번 주제**(`requestAnimationFrame` 과 프레임 예산) — **읽기·쓰기를 언제 묶나**. 이 문서가 못 잰 자리가 그쪽의 몫이다
- 목록의 **40번 주제**(마이크로태스크 대 태스크) — **렌더 단계가 그 사이 어디에 끼는가**
- [CSS 56번 주제](../../languages/css/syntax/56-rendering-pipeline-and-will-change/2-summary.md) — ★ **이 주제의 정본 이웃.** 스타일 → 레이아웃 → 페인트 → 합성의 단계와 **어느 속성이 어느 단계를 돌리나**가 거기다. **여기서 다시 쓰지 않는다**
- [CSS 54번 주제](../../languages/css/syntax/54-transform-2d-and-origin/2-summary.md) — `transform` 이 **레이아웃을 안 바꾼다**는 것
- [`../../../../history/web/04-브라우저-엔진.md`](../../../../history/web/04-브라우저-엔진.md) — 레이아웃 엔진의 계보. **「왜 이런 설계가 됐나」는 그쪽**이고 여기는 **「그래서 오늘 무엇을 조심하나」다**

## 용어 풀이

- **강제 동기 레이아웃(forced synchronous layout)** — 쌓아 둔 변경을 **읽기가 그 자리에서** 반영하게 만드는 것. 이 주제의 주인공.
- **레이아웃 스래싱(layout thrashing)** — 그 강제가 **한 tick 안에서 여러 번** 되풀이되는 것. 「스래싱」은 「같은 일을 헛되이 되풀이한다」는 뜻.
- **무효화(invalidation)** — 쓰기가 「여기부터 다시 계산해야 한다」고 표시하는 것. 무엇을 쓰느냐로 번지는 범위가 다르다.
- **스타일 재계산(style recalculation)** — 어떤 규칙이 어느 요소에 적용되는지 다시 정하는 단계. **레이아웃보다 앞이다.**
- **렌더링 단계(rendering steps)** — 이벤트 루프가 한 바퀴 돌 때 **프레임을 그리려고** 지나가는 단계들. 여기서 레이아웃이 **자연스럽게** 돈다.
- **분해능(resolution)** — 측정 도구가 구분할 수 있는 최소 간격. 여기서는 100마이크로초.
- **중앙값(median)** — 여러 판을 크기순으로 늘어놓았을 때 가운데 값.
- **신호 대 잡음** — 재려는 차이가 측정 오차보다 얼마나 큰가. 한 자릿수 차이면 압도적이다.
- **합성(compositing)** — 이미 그린 조각들을 화면에 겹쳐 놓는 마지막 단계. `transform`·`opacity` 가 여기서 처리되면 레이아웃이 안 돈다.

## 더 들어가면

- **`FastDOM` 같은 라이브러리**는 읽기와 쓰기를 각각 큐에 모아 **rAF 콜백에서 읽기 전부 → 쓰기 전부**로 실행한다. 이 문서의 (11)을 라이브러리로 만든 것이다. **던져 보지 않았다** — 형태만 적는다.
- **`content-visibility: auto`** 는 화면 밖 자손의 레이아웃을 통째로 건너뛰게 한다. 스래싱이 나도 **비용이 훨씬 작아진다.** 정본은 CSS 갈래이고 **여기서 던져 보지 않았다.**
- **`Element.computedStyleMap()`**(Typed OM)도 결국 같은 파이프라인을 거친다 — **문자열 파싱만 줄지 레이아웃은 그대로**일 것으로 보이지만 **이 문서는 재지 않았다.**
- **개발자 도구의 Performance 패널**은 강제 레이아웃을 **`Recalculate Style` / `Layout` 막대와 경고 삼각형**으로 표시하고, **어느 줄이 방아쇠인지**까지 짚어 준다. 실무 진단은 이쪽이 정답이다. **헤드리스에서는 쓸 수 없어 이 문서에 싣지 못했다.**
- **`LongAnimationFrame` API** 는 「이 프레임이 왜 길었나」를 스크립트로 물을 수 있게 한다. Baseline limited 라 이 목록에서는 뺐다(갈래 [`../README.md`](../README.md)).
- **왜 브라우저가 미루나** — 미루면 **여러 변경을 한 번에** 계산할 수 있기 때문이다. 즉 **게으름이 최적화**다. 읽기는 그 최적화를 포기시키는 요청이다.
