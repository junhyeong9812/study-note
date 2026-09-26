# web-api/18 — 이벤트 위임: 조상 하나로 자손 전체 받기·`closest()` 로 되찾기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★ **이 편의 본체는 「되찾기 표」다** — 위임 리스너 안에서 **`e.target` · `closest()` · `contains` 가드**를 한 줄에 나란히 찍어, **조상 하나가 「누가 눌렸나」를 제대로 되찾았나**를 진짜 클릭마다 본다(창 ② 를 위임 리스너 안으로 옮긴 것).\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「`Element.closest()`」·「`Node.contains()`」·「`Event.composedPath()`」·「dispatch」 절. 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. **클릭·포커스·마우스 이동은 CDP 로 넣은 진짜 입력**이다. 하네스는 [16번 주제](../16-event-propagation-phases/2-summary.md)의 (1)에 있다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — [16번 주제](../16-event-propagation-phases/2-summary.md)(버블 단계) · CSS 갈래 [08번 주제](../../languages/css/syntax/08-basic-selectors-and-combinators/2-summary.md)(`closest()` 가 받는 선택자 문법). 위임이 **깨지는 자리** 셋은 [16번 주제](../16-event-propagation-phases/2-summary.md)(비버블) · [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md)(`stopPropagation`) · [12번 주제](../12-shadow-dom/2-summary.md)(그림자 경계)에서 인용하고 **여기서 진짜 클릭으로 다시 확인했다.**\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 편에는 흔들리는 칸이 없었다** — 세는 것이 호출 여부와 노드 이름뿐이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 되찾기 표 6줄 · 포커스 3줄 · 그림자 6줄 · `composedPath()` 길이 · `mouseover` 순서 · 스스로 지워지는 항목 · 네 메서드의 범위 | 같은 판이면 결정적이다. **캡처 네 판이 한 글자도 같았다** |
| **안 흔들린다** | 진짜 입력의 좌표 | 요소의 `getBoundingClientRect` 에서 계산한다. **안쪽 여백**은 왼쪽 위 모서리에서 `(4, 4)` 로 정했다 |
| **못 잰다** | 위임이 리스너 수를 줄여 얻는 **메모리·시간 이득** | 재지 않았다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | 위임은 트리에 자국을 안 남긴다 |
| **창 ② 노드 프로브 — 위임 리스너 안에서** | ★★ **본체(되찾기 표)** | `e.target` 이 무엇이고 · `closest('li')` 가 무엇을 찾았고 · 그것이 **위임 조상 안에 있나** |
| 창 ③ 같은 것을 두 번 읽기 | **부적용** | 한 번의 클릭에서 읽을 값이 한 번뿐이다 |
| **창 ④ 디스패치 계수기** | ★ **쓴다** | **직접 등록한 리스너 대 위임 리스너**가 각각 불렸나 |
| **진짜 입력(CDP)** | ★ **쓴다 — 입력 쪽** | 진짜 클릭 · 진짜 포커스 · 진짜 마우스 이동. 그림자 안의 × 는 **좌표를 그림자 안 요소에서 계산**해 눌렀다 |
| 창 ⑤ 콘솔 | **부적용** | 이 편에는 경고를 내는 자리가 없다 |

- ★★ **제5의 상태 — 그림자 경계에서는 「어느 항목을 눌렀나」를 `closest()` 가 아니라 `composedPath()` 로 물었다.** `closest()` 는 그림자 루트를 못 넘고 `e.target` 은 호스트로 바뀌어 오므로, **같은 질문을 다른 창(경로)으로** 물어야 답이 나온다((6)). ★ 바꾼 창이 못 보는 것 — **`closed` 그림자에서는 경로에서도 안쪽 칸이 빠진다.** 그 경우 바깥에서는 **어떤 창으로도** 못 되찾는다.

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| **위임의 이득**(리스너 수 · 메모리 · 등록 시간) | 재지 않았다. 이 편은 **「받나 못 받나」와 「되찾나 못 되찾나」** 만 적는다 |
| **`closed` 그림자 안에서 무엇이 눌렸나** | 바깥의 어떤 API 로도 안 보인다((6)) — 컴포넌트가 스스로 알려 줘야 한다 |
| **히트 테스트가 왜 그 요소를 골랐나** | 결과(`e.target`)만 보인다. `pointer-events: none` 이 **어디로 떨어뜨렸나**도 결과로만 본다((4)) |

## 한눈에 — 쉽게 말하면

**★ 위임은 「층마다 안내원을 두지 않고 1층 로비에 한 명만 두는 것」이다. 로비 안내원은 「누가 어느 방에서 내려왔나」를 명찰(`e.target`)로 되짚어 알아낸다.**

[16번 주제](../16-event-propagation-phases/2-summary.md)의 건물 비유를 잇는다.

| 비유 | 실체 |
|---|---|
| **로비의 안내원 한 명** | 조상(`ul`)에 단 **위임 리스너 하나** |
| 방마다 안내원을 두는 것 | 자손마다 **직접 등록** |
| **나중에 생긴 방** | 등록이 끝난 뒤 추가된 요소 |
| 손님의 **명찰** | `e.target` — 가장 깊은 요소(`<span>` 일 수 있다) |
| 명찰에서 **「어느 방 손님인가」를 되짚기** | `e.target.closest('li')` |
| **다른 건물의 방 번호**를 잘못 읽기 | `closest()` 가 위임 조상 **밖**의 `li` 를 찾는 것 |
| **「우리 건물 방이 맞나」 확인** | `목록.contains(찾음)` 가드 |
| **엘리베이터를 안 타는 손님** | 버블하지 않는 이벤트 — 로비로 안 내려온다 |
| **「로비에 알리지 마」라고 한 방** | `stopPropagation()` 한 자손 |
| **명찰을 가린 손님** | 그림자 안의 요소 — 로비에서는 **호스트 명찰**만 보인다 |

- ★ **로비 한 명이 나중에 생긴 방까지 받는다** — 올라오는 길(버블)은 방이 언제 생겼든 로비를 지나기 때문이다.
- ★ **되짚기가 로비 밖까지 나갈 수 있다** — 가드가 없으면 **다른 건물의 방**을 답한다.

```text
   위임 한 장 — 조상 하나가 받고, closest 로 되찾는다

   <ul id="목록">  ◀── 리스너 하나: e.target.closest('li')
     <li #항목1>
       <button .지움>
         <span .표>×</span>   ◀── 사람이 누른 곳 = e.target
     <li #항목3>  ◀── 등록이 끝난 뒤에 더한 항목 — 그래도 받는다

   누른 곳(span) ─ 버블 ─▶ button ─▶ li ─▶ ul(위임 리스너)
                                            │
                                            └─ e.target.closest('li') = #항목1
```

## 이 주제가 답하려는 질문

1. **나중에 추가된 요소에 리스너를 다시 안 달아도 되는 이유는** — 전파로 설명하면?
2. **`e.target` 이 자식의 자식일 때 무엇을 눌렀는지 어떻게 되찾나** — `closest()` 는 어디서 틀리나?
3. **위임이 깨지는 자리는 어디인가** — 비버블 이벤트 · `stopPropagation` · 그림자 경계 · `pointer-events`.

## 동작 방식

### (1) ★★★ 본체 — 되찾기 표: 직접 등록 대 위임

**언제 쓰나** — 목록을 그린 뒤 항목을 더하고 빼는 화면. 「새로 더한 항목의 버튼이 안 먹는다」일 때.

**던진 것** — 목록의 `.지움` 단추마다 **직접** 리스너를 달고, `#목록` 에는 **위임** 리스너 하나를 달았다. 등록이 **끝난 뒤에** `#항목3` 을 더했다. 여섯 자리를 진짜로 눌렀다. 아래 (2)\~(5)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa16b-18-deleg.html -->
<!doctype html>
<meta charset="utf-8">
<title>18-deleg</title>
<style>
  #목록 { padding: 16px; }
  #항목4 { pointer-events: none; }
  #항목5 .표 { pointer-events: none; }
</style>
<ul id="바깥목록">
  <li id="바깥항목">바깥 목록의 항목
    <ul id="목록">
      <li id="항목1"><button class="지움"><span class="표">×</span></button> 첫째</li>
      <li id="항목2"><button class="지움" id="멈추는단추"><span class="표">×</span></button> 둘째</li>
      <li id="항목4"><button class="지움"><span class="표">×</span></button> 넷째</li>
      <li id="항목5"><button class="지움"><span class="표">×</span></button> 다섯째</li>
      <li id="항목6"><input id="칸6" value="입력칸"> 여섯째</li>
    </ul>
  </li>
</ul>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null || n === undefined ? String(n) : n.id ? '#' + n.id
  : n.className ? n.nodeName.toLowerCase() + '.' + n.className : n.nodeName.toLowerCase();
const 목록 = $('목록');

// 직접 등록 — 지금 있는 단추마다 하나씩
let 직접 = 0;
for (const b of 목록.querySelectorAll('.지움')) b.addEventListener('click', () => { 직접++; });
$('멈추는단추').addEventListener('click', e => e.stopPropagation());

// 위임 — 목록 하나에만
let 판 = null;
목록.addEventListener('click', e => {
  const 찾음 = e.target.closest('li');
  판 = { target: 이름(e.target), closest: 이름(찾음),
         가드: 이름(찾음 && 목록.contains(찾음) ? 찾음 : null) };
});
const 포커스판 = {};
for (const [형, cap] of [['focus', false], ['focus', true], ['focusin', false]]) {
  목록.addEventListener(형, e => { 포커스판[형 + (cap ? '(capture)' : '')] = 이름(e.target.closest('li')); }, cap);
}

// 등록이 끝난 뒤에 항목 하나를 더한다
const 새 = document.createElement('li');
새.id = '항목3';
새.innerHTML = '<button class="지움"><span class="표">×</span></button> 셋째(나중에 더함)';
목록.insertBefore(새, $('항목4'));

const 줄 = [];
window.__한판 = () => { 직접 = 0; 판 = null; return 1; };
window.__적기 = 무엇 => { 줄.push([무엇, 직접, 판]); return 1; };
const 단계 = [];
for (const [무엇, 선택자, 오프셋] of [
  ['#항목1 의 × (span)', '#항목1 .표'],
  ['#항목3 의 × (나중에 더함)', '#항목3 .표'],
  ['#항목2 의 × (단추가 stopPropagation)', '#항목2 .표'],
  ['#목록 의 안쪽 여백', '#목록', [4, 4]],
  ['#항목5 의 × (span 이 pointer-events:none)', '#항목5 .표'],
  ['#항목4 의 × (li 가 pointer-events:none)', '#항목4 .표'],
]) {
  단계.push(['js', '__한판()']);
  단계.push(오프셋 ? ['clickat', 선택자, ...오프셋] : ['click', 선택자]);
  단계.push(['js', `__적기(${JSON.stringify(무엇)})`]);
}
단계.push(['click', '#칸6']);
window.__단계 = 단계;

window.__끝 = () => {
  const O = [];
  O.push('진짜 클릭 — 직접 등록한 리스너와 목록 하나에 단 위임 리스너');
  O.push(padw('누른 곳', 42) + padw('직접', 6) + padw('위임: e.target', 18) + padw("closest('li')", 16) + '+ 목록.contains 가드');
  for (const [무엇, 직, 판] of 줄) {
    O.push(padw(무엇, 42) + padw(String(직), 6) + (판 ? padw(판.target, 18) + padw(판.closest, 16) + 판.가드 : '(위임 리스너 안 불림)'));
  }
  O.push('');
  O.push('진짜 클릭으로 #칸6 에 포커스 — 목록에 단 리스너가 찾은 항목');
  for (const k of ['focus', 'focus(capture)', 'focusin']) O.push('  ' + padw(k, 16) + (포커스판[k] || '(안 불림)'));
  return O.join('\n');
};
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '1,8p'
진짜 클릭 — 직접 등록한 리스너와 목록 하나에 단 위임 리스너
누른 곳                                   직접  위임: e.target    closest('li')   + 목록.contains 가드
#항목1 의 × (span)                        1     span.표           #항목1          #항목1
#항목3 의 × (나중에 더함)                 0     span.표           #항목3          #항목3
#항목2 의 × (단추가 stopPropagation)      1     (위임 리스너 안 불림)
#목록 의 안쪽 여백                        0     #목록             #바깥항목       null
#항목5 의 × (span 이 pointer-events:none) 1     button.지움       #항목5          #항목5
#항목4 의 × (li 가 pointer-events:none)   0     #목록             #바깥항목       null
(exit 0)
```

- **첫 줄(`#항목1`)** — 직접 1 · 위임도 받았다. **`e.target` 은 `span.표`**(× 글자)이고 **`closest('li')` 가 `#항목1` 을 되찾았다.**
- ★★ **둘째 줄(`#항목3`, 나중에 더함)** — **직접 0**, 위임은 **받았다.** 직접 등록은 **등록할 때 있던 단추**에만 달렸고, 위임은 **버블이 조상을 지나기만 하면** 받는다.
- 나머지 네 줄은 **위임이 깨지거나 틀리는 자리**다 — (2)\~(4).

```text
   직접 등록 대 위임 — 나중에 더한 항목

                           직접 등록               위임(#목록 하나)
   등록할 때 있던 #항목1    O (단추에 달려 있다)    O
   나중에 더한   #항목3     X (아무도 안 달았다)    O (버블이 #목록 을 지난다)

   ★ 위임이 받는 조건은 「언제 생겼나」가 아니라 「버블이 조상을 지나나」다
```

- **왜 되찾아야 하나** — 위임 리스너의 `e.target` 은 **가장 깊은 요소**다([16번 주제](../16-event-propagation-phases/2-summary.md)의 (7)). 단추 안에 아이콘 `<span>` 이 있으면 `e.target` 은 `<span>` 이다. **`e.target === 단추` 로 견주면 아이콘을 누를 때 놓친다.** `closest()` 는 **자기부터 시작해 조상 쪽으로** 선택자에 맞는 첫 요소를 찾는다.

### (2) ★★★ `closest()` 가 위임 조상 **밖**을 잡는다 — 가드가 필요하다

**언제 쓰나** — 목록이 **다른 목록의 항목 안에** 들어 있을 때(중첩 메뉴·트리·댓글의 답글).

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '2p;6p'
누른 곳                                   직접  위임: e.target    closest('li')   + 목록.contains 가드
#목록 의 안쪽 여백                        0     #목록             #바깥항목       null
(exit 0)
```

- ★★★ **넷째 줄(`#목록` 의 안쪽 여백)** — `e.target` 은 **`#목록` 자신**이다. 그 자리에서 `closest('li')` 를 부르면 **`#목록` 을 넘어 올라가** **`#바깥항목`**(바깥 목록의 항목)을 찾았다.
- **`목록.contains(찾음)` 가드를 거치면 `null`** 이다 — 「내 목록 안의 항목이 아니다」.
- ★ **`closest()` 는 멈출 자리를 모른다** — 명세상 **「자기와 조상을 차례로 보며 선택자에 맞는 첫 요소」** 를 돌려줄 뿐, 위임 조상에서 멈추라는 인자가 없다. **위임 조상 밖의 요소를 돌려주는 것은 오작동이 아니라 정의대로다.**

```text
   closest 가 위임 조상을 넘어간다

   <ul id="바깥목록">
     <li id="바깥항목">          ◀── closest('li') 가 여기까지 올라와 찾았다
       <ul id="목록">            ◀── 위임 리스너 · 여기 여백을 눌렀다 = e.target
         <li id="항목1">…</li>

   e.target.closest('li')                         -> #바깥항목   ★ 틀린 답
   찾음 && 목록.contains(찾음) ? 찾음 : null       -> null        (가드)
```

```text
   가드 한 줄의 꼴

   목록.addEventListener('click', e => {
     const 항목 = e.target.closest('li');
     if (!항목 || !목록.contains(항목)) return;   // 내 목록 밖이면 버린다
     …
   });
```

- 비용 — 가드는 **한 줄**이다. 안 쓰면 **바깥 목록의 항목을 지우는** 식의 사고가 **예외 없이** 난다.

### (3) `stopPropagation()` 한 자손 — 위임이 조용히 끊긴다

**언제 쓰나** — 「어떤 항목만 위임 리스너가 안 받는다」일 때.

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '2p;5p'
누른 곳                                   직접  위임: e.target    closest('li')   + 목록.contains 가드
#항목2 의 × (단추가 stopPropagation)      1     (위임 리스너 안 불림)
(exit 0)
```

- **셋째 줄(`#항목2`)** — 그 단추에 **`stopPropagation()` 을 부르는 리스너**가 있다. **직접 등록은 1**(단추 자신의 리스너는 불렸다)인데 **위임 리스너는 안 불렸다.**
- [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md)의 격자 그대로다 — `stopPropagation` 은 **「조상 리스너가 불렸나」 칸만** 바꾼다. **위임 리스너가 곧 그 조상**이다.
- ★ **예외도 경고도 없다.** 자식 쪽 코드(대개 다른 사람이 짠 컴포넌트)가 부른 한 줄이 조상의 위임을 끊는다. 기본 동작을 막고 싶었던 것이면 **`preventDefault()` 만** 불러야 한다.

### (4) `pointer-events: none` — 두 자리가 반대로 갈린다

**언제 쓰나** — 아이콘을 누르면 `e.target` 이 아이콘이라 불편해서 CSS 로 흘려보낼 때. 또는 **비활성 항목**을 CSS 로 막을 때.

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '2p;7,8p'
누른 곳                                   직접  위임: e.target    closest('li')   + 목록.contains 가드
#항목5 의 × (span 이 pointer-events:none) 1     button.지움       #항목5          #항목5
#항목4 의 × (li 가 pointer-events:none)   0     #목록             #바깥항목       null
(exit 0)
```

- ★ **다섯째 줄(`#항목5`, × 글자에만 `pointer-events: none`)** — 클릭이 **글자를 통과해 단추에** 떨어졌다. **`e.target` 이 `button.지움`** 이고 `closest('li')` 가 **`#항목5`** 를 되찾았다. 직접 등록도 1 이다. **아이콘을 투명하게 만들어 `e.target` 을 단추로 맞추는 기법**이 이것이다.
- ★★ **여섯째 줄(`#항목4`, 항목 `li` 통째로 `pointer-events: none`)** — 그 값은 **상속**되므로 단추와 글자도 같이 투명해진다. 클릭이 **`#목록` 에** 떨어졌고, **`closest('li')` 가 또 `#바깥항목`** 을 잡았다(가드를 거치면 `null`). 직접 등록은 **0** 이다.
- ★ **「비활성 항목을 `pointer-events: none` 으로 막는다」는 이벤트를 없애지 않는다** — **아래에 있는 다른 요소**로 보낸다. 거기서 (2)의 함정이 다시 난다.

```text
   pointer-events: none — 클릭이 어디로 떨어지나

   #항목5 .표 { pointer-events: none }        #항목4 { pointer-events: none }
   li                                         li        (none · 상속)
   └ button   ◀── 여기로 떨어진다             └ button  (none)
     └ span   (통과)                            └ span  (none)
                                               ↓ 전부 통과
                                              ul#목록   ◀── 여기로 떨어진다

   closest('li') = #항목5                     closest('li') = #바깥항목 (가드 → null)
```

### (5) 버블하지 않는 이벤트 — `focus` 위임은 capture 나 `focusin` 으로

**언제 쓰나** — 목록 안의 입력칸 포커스를 조상 하나로 받고 싶을 때.

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '10,13p'
진짜 클릭으로 #칸6 에 포커스 — 목록에 단 리스너가 찾은 항목
  focus           (안 불림)
  focus(capture)  #항목6
  focusin         #항목6
(exit 0)
```

- **`focus` 를 bubble 로 단 위임 리스너는 안 불렸다.** [16번 주제](../16-event-propagation-phases/2-summary.md)의 비버블 격자 그대로다.
- **`focus` 를 capture 로 달면 받는다** — 내려가는 길에서 잡는다. `closest('li')` 가 `#항목6` 을 되찾았다.
- **`focusin` 은 버블하므로 bubble 로도 받는다.**
- ★ **위임의 전제는 「버블한다」** 다. 버블하지 않는 다섯 가지(`focus`·`blur`·`mouseenter`·`load`·`scroll`)는 **capture 로 달거나 버블하는 짝**을 쓴다.

### (6) ★★ 그림자 경계 — `closest()` 는 못 넘고 `composedPath()` 는 넘는다(`open` 일 때만)

**언제 쓰나** — 위임 조상 안에 **커스텀 요소**(그림자를 가진 컴포넌트)가 있을 때.

**던진 것** — `#목록` 안에 그림자 호스트 둘(`open`·`closed`)을 두고 그림자 안에 × 단추를 넣었다. 그림자 안의 × 를 **진짜로** 누르고(좌표를 그림자 안 요소에서 계산), 합성 `new MouseEvent('click', { bubbles: true })` 를 `composed` 없이 · 있게 던졌다.

```html
<!-- wa16b-18-shadow.html -->
<!doctype html>
<meta charset="utf-8">
<title>18-shadow</title>
<div id="목록">
  <div class="항목" id="열린"></div>
  <div class="항목" id="닫힌"></div>
</div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null || n === undefined ? String(n) : n === window ? 'Window'
  : n.nodeType === 11 ? '#shadow-root' : n.nodeType === 9 ? '#document'
  : n.id ? '#' + n.id : n.className ? n.nodeName.toLowerCase() + '.' + n.className : n.nodeName.toLowerCase();
const 뿌리 = {};
for (const [id, mode] of [['열린', 'open'], ['닫힌', 'closed']]) {
  뿌리[id] = $(id).attachShadow({ mode });
  뿌리[id].innerHTML = '<button class="지움"><span class="표">×</span></button>';
}
let 판 = null;
$('목록').addEventListener('click', e => {
  const 경로 = e.composedPath();
  판 = { target: 이름(e.target),
         closest: 이름(e.target.closest('.지움')),
         경로0: 이름(경로[0]),
         경로찾기: 이름(경로.find(n => n instanceof Element && n.matches('.지움')) || null),
         길이: 경로.length };
});
const 줄 = [];
window.__한판 = () => { 판 = null; return 1; };
window.__적기 = 무엇 => { 줄.push([무엇, 판]); return 1; };
window.__합성 = (id, composed) => { 뿌리[id].querySelector('.표').dispatchEvent(new MouseEvent('click', { bubbles: true, composed })); return 1; };
const 단계 = [];
for (const id of ['열린', '닫힌']) {
  단계.push(['js', '__한판()'], ['click', 'js:뿌리[' + JSON.stringify(id) + "].querySelector('.표')"], ['js', `__적기(${JSON.stringify(id + ' · 진짜 클릭')})`]);
  단계.push(['js', '__한판()'], ['js', `__합성(${JSON.stringify(id)}, false)`], ['js', `__적기(${JSON.stringify(id + ' · 합성 composed:false')})`]);
  단계.push(['js', '__한판()'], ['js', `__합성(${JSON.stringify(id)}, true)`], ['js', `__적기(${JSON.stringify(id + ' · 합성 composed:true')})`]);
}
window.__단계 = 단계;
window.__끝 = () => {
  const O = [];
  O.push('그림자 안의 × 를 눌렀을 때 — #목록 에 단 위임 리스너가 본 것');
  O.push(padw('어디를 어떻게', 28) + padw('e.target', 10) + padw("closest('.지움')", 18) + padw('composedPath()[0]', 19)
       + padw("composedPath 에서 찾기", 24) + '경로 길이');
  for (const [무엇, 판] of 줄) {
    O.push(padw(무엇, 28) + (판 ? padw(판.target, 10) + padw(판.closest, 18) + padw(판.경로0, 19) + padw(판.경로찾기, 24) + 판.길이
                                : '(위임 리스너 안 불림)'));
  }
  O.push('');
  O.push('그림자 안의 span.표 에서 위로 closest 를 부르면 (open)');
  const 안 = 뿌리['열린'].querySelector('.표');
  for (const 선택자 of ['.지움', '#열린', '#목록', ':host']) {
    let 답;
    try { 답 = 이름(안.closest(선택자)); } catch (e) { 답 = e.name + ' 「' + e.message + '」'; }
    O.push('  ' + padw("closest('" + 선택자 + "')", 20) + '= ' + 답);
  }
  return O.join('\n');
};
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-18-shadow.html | sed -n '1,8p'
그림자 안의 × 를 눌렀을 때 — #목록 에 단 위임 리스너가 본 것
어디를 어떻게               e.target  closest('.지움')  composedPath()[0]  composedPath 에서 찾기  경로 길이
열린 · 진짜 클릭            #열린     null              span.표            button.지움             9
열린 · 합성 composed:false  (위임 리스너 안 불림)
열린 · 합성 composed:true   #열린     null              span.표            button.지움             9
닫힌 · 진짜 클릭            #닫힌     null              #닫힌              null                    6
닫힌 · 합성 composed:false  (위임 리스너 안 불림)
닫힌 · 합성 composed:true   #닫힌     null              #닫힌              null                    6
(exit 0)
```

- ★★ **진짜 클릭 — 위임 리스너의 `e.target` 은 호스트**(`#열린`·`#닫힌`)다. [12번 주제](../12-shadow-dom/2-summary.md)의 재타기팅 그대로다.
- ★★ **그래서 `e.target.closest('.지움')` 은 `null`** 이다. 호스트는 단추가 아니고, `closest()` 는 **호스트의 조상 쪽(바깥)으로만** 올라간다 — **그림자 안으로는 안 들어간다.**
- ★ **`open` 이면 `composedPath()` 로 되찾는다** — `[0]` 이 `span.표`, 경로에서 `.지움` 을 찾으면 `button.지움`. 경로 길이 **9**.
- ★★★ **`closed` 면 경로에서도 안쪽 칸이 빠진다** — 길이 **6**, `[0]` 이 호스트다. **바깥의 위임 리스너는 어떤 창으로도 되찾지 못한다.** [12번 주제](../12-shadow-dom/2-summary.md)가 합성으로 잰 「7칸 → 5칸」과 같은 성질이 **진짜 클릭에서 9칸 → 6칸**으로 나왔다(이 페이지는 경로가 달라 칸 수가 다르다 — 빠진 것은 **`span`·`button`·`#shadow-root` 세 칸**이다).
- ★ **합성 `composed: false` 는 위임 리스너에 아예 안 왔다** — 경계에서 멈췄다. **`composed: true` 를 주면 진짜와 같은 줄**이 나왔다. 생성자의 `composed` 기본값이 `false` 인 것의 정본은 [12번 주제](../12-shadow-dom/2-summary.md)다.

```text
   그림자 경계 — 바깥의 위임 리스너가 되찾을 수 있나

   #목록 (위임)
     └ #열린 (host, open)                   └ #닫힌 (host, closed)
         #shadow-root                           #shadow-root
           └ button.지움                          └ button.지움
               └ span.표  ◀── 눌렀다                └ span.표  ◀── 눌렀다

   위임 리스너가 보는 것       open                   closed
   e.target                    #열린(호스트)          #닫힌(호스트)
   e.target.closest('.지움')   null                   null
   composedPath()[0]           span.표   ★ 되찾음     #닫힌      ★ 못 되찾음
   composedPath().length       9                      6
```

```text
$ python3 wa16b-cdp.py page wa16b-18-shadow.html | sed -n '10,14p'
그림자 안의 span.표 에서 위로 closest 를 부르면 (open)
  closest('.지움')    = button.지움
  closest('#열린')    = null
  closest('#목록')    = null
  closest(':host')    = null
(exit 0)
```

- ★★ **거꾸로 그림자 안에서 위로 부르면 그림자 루트에서 멈춘다** — 안쪽 `span.표` 에서 `closest('.지움')` 은 `button.지움` 을 찾지만, **호스트 `#열린` 도 위임 조상 `#목록` 도 `null`** 이다. `closest()` 는 부모를 따라가는데 **그림자 루트에는 요소 부모가 없다.**
- 그래서 `closest()` 는 **어느 방향으로도 경계를 못 넘는다** — 바깥에서 안으로도(호스트에서 시작), 안에서 바깥으로도(그림자 루트에서 멈춤). 경계를 넘는 것은 **이벤트 경로(`composedPath()`)** 뿐이다.
- `closest(':host')` 도 `null` 이었다 — `:host` 는 그림자 안 **스타일시트**에서 호스트를 가리키는 선택자이고, 여기서는 아무것도 안 잡았다(이 판의 관찰).

- **컴포넌트 쪽 처방** — 그림자 안에서 무엇이 눌렸는지 **바깥이 알아야 하면**, 컴포넌트가 **자기 이벤트를 `composed: true` 로 던지며 `detail` 에 담아** 알려 준다(목록의 **21번 주제**). `closed` 는 그것 말고 길이 없다.

### (7) `mouseenter` 는 위임이 안 되고 `mouseover` 는 되지만 여러 번 온다

**언제 쓰나** — 목록 항목에 마우스를 올릴 때 한 번만 처리하고 싶을 때.

**던진 것** — 진짜 마우스를 **목록 밖 → 항목1 글자 → 단추1 → 항목1 글자 → 항목2 글자 → 단추2** 로 옮겼다.

```html
<!-- wa16b-18-hover.html -->
<!doctype html>
<meta charset="utf-8">
<title>18-hover</title>
<p><button id="저쪽">저쪽</button></p>
<ul id="목록">
  <li id="항목1">첫째 항목 <button id="단추1">단추</button></li>
  <li id="항목2">둘째 항목 <button id="단추2">단추</button></li>
</ul>
<script>
const $ = id => document.getElementById(id);
const 이름 = n => n === null ? 'null' : n.id ? '#' + n.id : n.nodeName.toLowerCase();
const 목록 = $('목록');
const 로그 = { mouseenter: [], mouseover: [], '가드한 mouseover': [], 줄: [] };
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
목록.addEventListener('mouseenter', e => { 로그.mouseenter.push(이름(e.target)); });
목록.addEventListener('mouseover', e => {
  로그.mouseover.push(이름(e.target.closest('li')));
  const li = e.target.closest('li');
  // 같은 항목 안에서 옮겨 다닌 것은 버린다 — relatedTarget 이 이미 그 항목 안이면
  const 통과 = !!(li && 목록.contains(li) && !(e.relatedTarget && li.contains(e.relatedTarget)));
  if (통과) 로그['가드한 mouseover'].push(이름(li));
  로그.줄.push(padw(이름(e.target), 16) + padw(이름(e.relatedTarget), 16) + padw(이름(li), 16) + (통과 ? 'O' : 'X'));
});
window.__단계 = [
  ['move', '#저쪽'],
  ['moveat', '#항목1', 4, 4], ['move', '#단추1'], ['moveat', '#항목1', 4, 4],
  ['moveat', '#항목2', 4, 4], ['move', '#단추2'],
  ['js', 'new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => r(1))))'],
];
window.__끝 = () => [
  '진짜 마우스 이동: 저쪽 → 항목1 글자 → 단추1 → 항목1 글자 → 항목2 글자 → 단추2',
  '  목록의 mouseenter 가 본 target  : ' + (로그.mouseenter.join(' · ') || '(없음)'),
  "  목록의 mouseover 에서 closest('li'): " + 로그.mouseover.join(' · '),
  '  relatedTarget 으로 거른 mouseover : ' + 로그['가드한 mouseover'].join(' · '),
  '',
  '목록이 받은 mouseover 한 줄씩',
  '  ' + padw('e.target', 16) + padw('relatedTarget', 16) + padw("closest('li')", 16) + '가드 통과',
  ...로그.줄.map(x => '  ' + x),
].join('\n');
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-18-hover.html
진짜 마우스 이동: 저쪽 → 항목1 글자 → 단추1 → 항목1 글자 → 항목2 글자 → 단추2
  목록의 mouseenter 가 본 target  : #목록
  목록의 mouseover 에서 closest('li'): #항목1 · #항목1 · #항목1 · #항목2 · #항목2
  relatedTarget 으로 거른 mouseover : #항목1 · #항목2

목록이 받은 mouseover 한 줄씩
  e.target        relatedTarget   closest('li')   가드 통과
  #항목1          #저쪽           #항목1          O
  #단추1          #항목1          #항목1          X
  #항목1          #단추1          #항목1          X
  #항목2          #항목1          #항목2          O
  #단추2          #항목2          #항목2          X
(exit 0)
```

- **`mouseenter` 를 단 위임 리스너는 `#목록` 자신의 진입 한 번만** 봤다. 항목의 `mouseenter` 는 버블하지 않아 조상에 안 온다.
- ★ **`mouseover` 는 버블하므로 받는다 — 그런데 항목1 에서만 세 번** 왔다. **같은 항목 안에서 글자와 단추 사이를 오갈 때마다** 또 난다.
- ★ **`relatedTarget`(방금 떠난 요소)이 이미 그 항목 안이면 버리는 가드**를 거치면 **항목마다 한 번**(`#항목1 · #항목2`)으로 줄었다 — `mouseenter` 를 위임으로 흉내 낸 것이다.
- 블록 끝의 표가 한 줄씩이다 — **통과한 두 줄은 `relatedTarget` 이 그 항목 밖**(`#저쪽` · `#항목1`)이었고, 버린 세 줄은 **같은 항목 안**(`#항목1` · `#단추1` · `#항목2`)이었다.

```text
   mouseover 위임 — 같은 항목 안의 이동을 거른다

   const li = e.target.closest('li');
   if (!li || !목록.contains(li)) return;                    // 목록 밖
   if (e.relatedTarget && li.contains(e.relatedTarget)) return; // 같은 항목 안에서 옮긴 것

   relatedTarget = 방금 떠난 요소
     밖 -> 항목1         떠난 곳이 항목1 밖   -> 통과   (진입)
     항목1 안에서 이동   떠난 곳이 항목1 안   -> 버림
```

### (8) 위임 리스너의 `this` · 스스로 지워지는 항목 · 자기 자신도 넣나

**언제 쓰나** — 「지움」 단추가 **자기 항목을 지운 뒤** 위임 리스너가 무엇을 보나, 그리고 `closest()` 가 `e.target` 자신을 돌려주는지.

```html
<!-- wa16b-18-more.html -->
<!doctype html>
<meta charset="utf-8">
<title>18-more</title>
<ul id="목록">
  <li id="항목1">첫째 <button class="지움" id="지움1"><span class="표">×</span></button></li>
  <li id="항목2">둘째 <button class="지움" id="지움2"><span class="표">×</span></button></li>
</ul>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null ? 'null' : n.id ? '#' + n.id : n.className ? n.nodeName.toLowerCase() + '.' + n.className : n.nodeName.toLowerCase();
const 목록 = $('목록');
const O = [];
let 판 = null;
목록.addEventListener('click', function (e) {
  const 항목 = e.target.closest('li');
  판 = { this: 이름(this), currentTarget: 이름(e.currentTarget), target: 이름(e.target),
         항목: 이름(항목), 붙어있나: e.target.isConnected, 가드: 이름(항목 && 목록.contains(항목) ? 항목 : null) };
});
// 둘째 항목의 단추는 자기 click 리스너에서 항목을 지운다
$('지움2').addEventListener('click', () => { $('항목2').remove(); });
const 줄 = [];
window.__적기 = 무엇 => { 줄.push([무엇, 판]); 판 = null; return 1; };
window.__단계 = [
  ['click', '#항목1'], ['js', "__적기('#항목1 의 글자(li 자신)')"],
  ['click', '#지움1 .표'], ['js', "__적기('#항목1 의 ×')"],
  ['click', '#지움2 .표'], ['js', "__적기('#항목2 의 × (단추가 항목을 지움)')"],
];
window.__끝 = () => {
  O.push('진짜 클릭 — 목록 하나에 단 위임 리스너(보통 함수)가 본 것');
  O.push(padw('누른 곳', 36) + padw('this', 8) + padw('target', 10) + padw("closest('li')", 15) + padw('target.isConnected', 20) + '가드');
  for (const [무엇, p] of 줄) O.push(padw(무엇, 36) + padw(p.this, 8) + padw(p.target, 10) + padw(p.항목, 15) + padw(String(p.붙어있나), 20) + p.가드);
  O.push('');
  O.push("closest · matches · contains 가 자기 자신을 넣나 (li#항목1 에서)");
  const li = $('항목1');
  O.push("   li.closest('li') === li → " + (li.closest('li') === li) + " · li.matches('li') → " + li.matches('li')
       + ' · li.contains(li) → ' + li.contains(li) + " · li.querySelector('li') → " + 이름(li.querySelector('li')));
  return O.join('\n');
};
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-18-more.html | sed -n '1,5p'
진짜 클릭 — 목록 하나에 단 위임 리스너(보통 함수)가 본 것
누른 곳                             this    target    closest('li')  target.isConnected  가드
#항목1 의 글자(li 자신)             #목록   #항목1    #항목1         true                #항목1
#항목1 의 ×                         #목록   span.표   #항목1         true                #항목1
#항목2 의 × (단추가 항목을 지움)    #목록   span.표   #항목2         false               null
(exit 0)
```

- **위임 리스너의 `this` 는 세 줄 다 `#목록`** 이다 — 누른 항목이 아니다([16번 주제](../16-event-propagation-phases/2-summary.md)의 (9)).
- **`li` 자신(글자)을 누르면 `target` 이 `#항목1`** 이고 `closest('li')` 는 **그 `li` 자신**을 돌려준다.
- ★★ **셋째 줄 — 단추의 리스너가 `#항목2` 를 지웠는데도 위임 리스너는 불렸다.** [16번 주제](../16-event-propagation-phases/2-summary.md)의 (8) 그대로 — **경로는 디스패치 시작 때 굳었다.** 이때 `e.target` 은 **문서에서 떨어져 있고**(`isConnected = false`), `closest('li')` 는 **떨어진 `#항목2`** 를 찾는다.
- ★ **가드가 그것을 `null` 로 걸렀다** — `목록.contains(항목)` 가 `false` 다. **가드는 「바깥 목록의 항목」만이 아니라 「이미 지워진 항목」도 거른다.** 지워진 항목을 다시 고치거나 세는 사고를 막는다.

```text
   스스로 지워지는 항목 — 경로는 남고, 트리는 바뀌었다

   경로(시작 때 굳음):  span.표 → button#지움2 → li#항목2 → ul#목록 → …
                                    │ 리스너가 li#항목2.remove()
                                    ▼
   트리(지금):          ul#목록 ─ li#항목1                (li#항목2 는 떨어져 나감)

   위임 리스너(#목록):  e.target.closest('li') = #항목2   (떨어진 요소)
                        목록.contains(#항목2)   = false   → 가드가 null
```

```text
$ python3 wa16b-cdp.py page wa16b-18-more.html | sed -n '7,8p'
closest · matches · contains 가 자기 자신을 넣나 (li#항목1 에서)
   li.closest('li') === li → true · li.matches('li') → true · li.contains(li) → true · li.querySelector('li') → null
(exit 0)
```

- **`closest()`·`matches()`·`contains()` 는 자기 자신을 넣고, `querySelector()` 는 안 넣는다** — `li.querySelector('li')` 가 `null` 이다(자손만 본다).

```text
   네 메서드가 보는 범위 (li#항목1 에서)

   matches('li')         자기만              → true
   closest('li')         자기 + 조상         → 자기
   contains(li)          자기 + 자손         → true
   querySelector('li')   자손만(자기 빼고)   → null
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 위임의 한 꼴

```text
   조상.addEventListener(타입, e => {
     const 항목 = e.target.closest(선택자);         // ① 되찾기 — 자기부터 조상 쪽으로
     if (!항목 || !조상.contains(항목)) return;    // ② 가드 — 내 조상 밖이면 버린다
     …항목으로 일한다…
   });

   그림자 안까지 봐야 하면(open 만)
     const 항목 = e.composedPath().find(n => n instanceof Element && n.matches(선택자));

   버블하지 않는 타입이면
     조상.addEventListener('focus', f, true)   또는   조상.addEventListener('focusin', f)
```

### 어디서 헷갈리나

- **`closest()` 는 자기 자신부터 본다** — `e.target` 이 이미 `li` 면 그 `li` 를 돌려준다.
- **`closest()` 의 인자는 CSS 선택자**다 — 문법의 정본은 CSS 갈래 [08번 주제](../../languages/css/syntax/08-basic-selectors-and-combinators/2-summary.md).
- **`matches()` 는 자기만**, **`closest()` 는 자기와 조상**, **`querySelector()` 는 자손**을 본다.
- **`this`/`currentTarget` 은 위임 조상**이다 — 누른 항목이 아니다([16번 주제](../16-event-propagation-phases/2-summary.md)).

## 어디서 틀리나

### 1. 항목을 그린 뒤에 리스너를 달고, 새 항목에 다시 안 단다

**새 항목은 안 받는다**((1)의 `#항목3` 직접 0). 위임이면 **다시 달 일이 없다.**

### 2. `e.target === 단추` 로 견준다

**아이콘을 누르면 `e.target` 은 아이콘**이다((1)). `closest()` 로 되찾는다.

### 3. `closest()` 결과를 가드 없이 쓴다

**위임 조상 밖의 요소**를 받을 수 있다((2)·(4)). `contains` 가드를 한 줄 둔다.

### 4. 비활성 항목을 `pointer-events: none` 으로 막았으니 이벤트가 없다고 믿는다

**아래 요소로 떨어진다**((4)). 거기서 `closest()` 가 엉뚱한 것을 잡는다.

### 5. 자식 컴포넌트가 `stopPropagation()` 을 부르는지 모른 채 위임한다

**그 자식의 클릭만 조용히 빠진다**((3)).

### 6. 그림자를 가진 컴포넌트 안의 요소를 `e.target.closest()` 로 찾는다

**`null`** 이다((6)). `open` 이면 `composedPath()`, `closed` 면 **컴포넌트가 이벤트로 알려 줘야** 한다.

### 7. 지움 단추가 항목을 지운 뒤 위임 리스너에서 그 항목을 다시 만진다

**위임 리스너는 여전히 불리고 `closest()` 는 떨어진 항목을 준다**((8)). 가드가 `null` 로 거른다 — 가드를 빼면 **이미 지운 항목을 세거나 고친다.**

### 8. `focus`·`mouseenter` 를 bubble 로 위임한다

**안 온다**((5)·(7)). capture 로 달거나 `focusin`·`mouseover`(+ `relatedTarget` 가드)를 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 나중에 더한 요소도 위임 리스너가 받는 것 | **명세**(DOM — 경로는 디스패치할 때 부모를 따라 만든다) |
| `closest()` 가 **자기부터 조상 쪽으로** 첫 일치를 돌려주고 **멈출 자리를 모르는** 것 | **명세**(DOM — `closest()` 절차) |
| `closest()` 가 **그림자 루트에서 멈추고**(안에서 위로) **그림자 안으로 안 들어가는**(호스트에서) 것 | **명세**(DOM — `closest()` 는 요소 조상만 따라간다) · **이 판도 그랬다**((6)의 두 블록) |
| `closest(':host')` 가 그림자 안에서 `null` 인 것 | ★ **이 판의 관찰** |
| 재타기팅으로 바깥 리스너의 `e.target` 이 호스트인 것 | **명세**(DOM — dispatch 의 shadow-adjusted target) · [12번 주제](../12-shadow-dom/2-summary.md) |
| `closed` 에서 `composedPath()` 가 안쪽 칸을 빼는 것 | **명세**(DOM — `composedPath()` 절차) |
| `pointer-events: none` 이 **상속**되고 클릭을 아래 요소로 보내는 것 | ★ **CSS 명세의 몫**이고 이 문서는 **Chrome 151 의 관찰**로만 적는다((4)) |
| `mouseover` 가 같은 항목 안의 이동에서 또 나는 것 | ★ **이 판의 관찰**((7)) |
| 스스로 지워진 항목에서도 위임 리스너가 불리는 것 | **명세**(DOM — 경로는 시작 때 굳는다) · 이 판도 그랬다((8)) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 항목이 자주 더해지고 빠지는 목록 | 목록에 위임 하나 | 항목마다 직접 등록 |
| 항목 안에 아이콘·글자가 있다 | `e.target.closest(선택자)` | `e.target === 단추` |
| 목록이 다른 목록 안에 들어 있다 | `closest()` + `contains` 가드 | `closest()` 만 |
| 입력칸 포커스를 한 곳에서 | `focusin` · 또는 `focus` 를 capture 로 | `focus` 를 bubble 로 |
| 마우스 올림을 항목마다 한 번 | `mouseover` + `relatedTarget` 가드 | `mouseenter` 위임 |
| 위임 조상 안에 그림자 컴포넌트 | 컴포넌트가 `composed` 이벤트로 알림 · `open` 이면 `composedPath()` | `e.target.closest()` |
| 항목 하나뿐이고 안 바뀐다 | 직접 등록이 더 읽기 쉽다 | 억지로 위임 |

## 핵심 문장

1. **위임은 버블 단계에 기댄다** — 조상 하나가 **언제 생긴 자손이든** 받는다.
2. **`e.target` 은 가장 깊은 요소다** — `closest()` 로 「어느 항목인가」를 되찾는다.
3. **`closest()` 는 멈출 자리를 모른다** — 위임 조상 **밖**을 찾을 수 있으니 `contains` 가드를 둔다.
4. **위임이 깨지는 자리** — 버블하지 않는 이벤트 · `stopPropagation` 한 자손 · 그림자 경계 · `pointer-events: none` 이 보낸 엉뚱한 타깃.
5. **그림자 경계에서는 `composedPath()` 가 되찾는다 — `open` 일 때만.** `closed` 는 바깥에서 못 되찾는다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 18번)
- [16번 주제](../16-event-propagation-phases/2-summary.md) — 경로와 버블 단계. **그쪽은 비버블 격자를 쟀고, 여기는 그 격자를 위임의 「깨지는 자리」로 쓴다**
- [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md) — `stopPropagation` 이 조상 칸만 바꾸는 격자
- [12번 주제](../12-shadow-dom/2-summary.md) — 재타기팅과 `composedPath()`(합성 이벤트로 잰 정본). **여기는 그것을 진짜 클릭과 위임 리스너로 다시 확인했다**
- [15번 주제](../15-listener-registration/2-summary.md) — 위임 리스너 하나를 **떼는** 법(동일성 조건 · `signal`)
- CSS 갈래 [08번 주제](../../languages/css/syntax/08-basic-selectors-and-combinators/2-summary.md) — `closest()`·`matches()` 가 받는 선택자 문법의 정본
- 목록의 **20번 주제**(리스너 수명과 누수) — 위임이 **리스너 수를 줄이는 것**의 값어치(이 편은 재지 않았다)
- 목록의 **21번 주제**(커스텀 이벤트) — 그림자 컴포넌트가 `composed` 이벤트로 **바깥에 알리는** 형태

## 용어 풀이

- **이벤트 위임(event delegation)** — 자손마다 리스너를 달지 않고 **조상 하나**에 달아 버블로 받는 형태.
- **위임 조상** — 위임 리스너를 단 요소. 리스너 안의 `currentTarget`.
- **`closest(선택자)`** — 자기부터 조상 쪽으로 올라가며 선택자에 맞는 **첫 요소**. 없으면 `null`.
- **`contains(노드)`** — 그 노드가 자기 자신이거나 자손이면 `true`.
- **가드(guard)** — 되찾은 요소가 **위임 조상 안**인지 확인하는 한 줄.
- **`relatedTarget`** — `mouseover` 에서는 **방금 떠난** 요소.
- **`pointer-events: none`** — 그 요소를 히트 테스트에서 투명하게 만든다. **상속**된다.
- **재타기팅(retargeting)** — 그림자 경계 밖에서 보면 `e.target` 이 호스트로 바뀌는 것.
- **되찾기 표** — 위임 리스너 안에서 `e.target`·`closest()`·가드를 한 줄에 찍는 관측. 이 편의 본체.

## 더 들어가면

- **위임이 실제로 얼마나 가볍나**(리스너 수·메모리)는 **재지 않았다** — 목록의 **20번 주제**.
- **`slot` 에 배정된 라이트 DOM 자식**에서 난 이벤트는 재타기팅되지 않는다([12번 주제](../12-shadow-dom/2-summary.md)의 (15)) — 위임 리스너가 그 자식을 `closest()` 로 **그대로** 되찾을 수 있다. 이 편은 다시 던지지 않았다.
- **포인터 이벤트(`pointerover` 등)의 위임**은 목록의 **23번 주제** 몫이다.
- **`closest()` 에 복잡한 선택자(`:has()` 등)를 넣는 비용**은 재지 않았다.
