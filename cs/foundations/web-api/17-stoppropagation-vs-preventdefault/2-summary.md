# web-api/17 — `stopPropagation` 대 `preventDefault`: 전파를 멈추는 것과 기본 동작을 막는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★ **이 편의 본체는 「멈춤 × 막음」 2×2 격자**다 — 창 ④(조상 리스너가 불렸나)와 창 ②(기본 동작이 일어났나)를 **한 표의 두 칸**으로 세우고, 그 표를 **진짜 입력**으로 채운다.\
> **기준 소스** — [WHATWG DOM Standard — Events](https://dom.spec.whatwg.org/#events) 의 「`stopPropagation()`」·「`stopImmediatePropagation()`」·「set the canceled flag」·「dispatch」(activation behavior 부분) 절, [HTML Standard — `input` 요소](https://html.spec.whatwg.org/multipage/input.html) 의 「legacy-pre-activation behavior」·「legacy-canceled-activation behavior」, [HTML Standard — Links](https://html.spec.whatwg.org/multipage/links.html) 의 「`a` 요소의 activation behavior」. 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. **링크 이동·체크박스 토글·폼 제출은 CDP 로 넣은 진짜 클릭과 진짜 키**로 일으켰고, 같은 격자를 **합성 세 가지**로도 던져 견줬다. 하네스는 [16번 주제](../16-event-propagation-phases/2-summary.md)의 (1)에 있다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — [16번 주제](../16-event-propagation-phases/2-summary.md)(경로와 세 단계). 여기는 그 경로를 **어디서 끊나**와, 경로와 **상관없이 따로 도는** 기본 동작이다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 편에는 흔들리는 칸이 없었다** — 세는 것이 호출 여부·`checked`·`location.hash`·`submit` 이벤트 여부뿐이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 2×2 격자 24칸 · 합성 세 가지와 진짜의 견줌 · `checked` 두 번 읽기 · 리스너 셋의 호출 순서 · `defaultPrevented`·`dispatchEvent` 반환값 · 라디오 · 링크 가로채기 · Enter 제출 | 같은 판이면 결정적이다. **캡처 네 판이 한 글자도 같았다** |
| **안 흔들린다** | 링크 이동의 판정 | **같은 문서 안의 조각(`#도착`)** 으로만 이동시켰다. 다른 문서로 떠나면 페이지가 사라져 셀 수 없다 |
| **부적용** | 시간 | 재지 않았다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | 기본 동작의 결과는 **속성이 아니라 상태**로 남는다(`checked` 성질·`location`). 트리의 `checked` 속성은 안 바뀐다 |
| **창 ② 노드 프로브** | ★ **본체의 한 축** | **기본 동작이 일어났나** — 링크는 `location.hash`, 체크박스는 `checked`, 제출 단추는 `submit` 이벤트 |
| **창 ③ 같은 것을 두 번 읽기** | ★ **쓴다** | 체크박스의 `checked` 를 **리스너 안에서 한 번, 디스패치가 끝난 뒤 한 번** 읽는다((4)) — 이 편의 함정이 이 두 값의 차이다 |
| **창 ④ 디스패치 계수기** | ★ **본체의 다른 축** | **조상 리스너가 불렸나** · 같은 요소의 리스너 셋이 어디까지 불렸나 |
| **진짜 입력(CDP)** | ★ **쓴다 — 입력 쪽** | 진짜 클릭 · 진짜 Space · 진짜 Enter |
| 창 ⑤ 콘솔 | **부적용** | 이 편에는 경고를 내는 자리가 없다 — **`passive` 의 경고는 [19번 주제](../19-passive-and-scroll/2-summary.md)** |

- ★★ **제5의 상태 — 「기본 동작이 일어났나」를 대상마다 다른 창으로 물었다.** 링크는 **`location.hash`**, 체크박스는 **`checked`**, 제출 단추는 **`submit` 이벤트가 났나**다. **셋 다 「기본 동작」이라는 한 질문**인데 드러나는 자리가 다르다. ★ 바꾼 창이 못 보는 것 — `submit` 이벤트는 「제출이 **시작됐나**」까지만 말한다. 실제 네트워크 요청은 `submit` 리스너가 막았으므로 **보내지 않았다.**

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| **다른 문서로 떠나는 링크 이동** | 떠나면 페이지와 로그가 사라진다. 그래서 **같은 문서 안의 조각**으로만 쟀다 |
| **실제 폼 전송(네트워크 요청)** | `submit` 리스너가 막았다. 이 편이 잰 것은 **`submit` 이벤트가 났나**까지다 |
| **「기본 동작」의 전체 목록** | 요소마다 명세가 따로 정한다. 이 편은 **링크·체크박스·제출 단추 셋**만 던졌다 |
| **브라우저가 막은 이유를 말해 주는 것** | `preventDefault()` 는 예외도 경고도 없다. **결과 상태를 다시 읽어야** 안다 |

## 한눈에 — 쉽게 말하면

**★ 둘은 다른 스위치다. `stopPropagation` 은 「소문이 위층으로 퍼지는 것」을 끊고, `preventDefault` 는 「건물이 원래 하려던 일」을 취소한다.**

택배 비유로 고정한다.

| 비유 | 실체 |
|---|---|
| **택배 도착 소식**이 층층이 전달된다 | 이벤트가 경로를 따라 퍼진다 |
| 「**위층에는 알리지 마**」 | `stopPropagation()` — 경로의 다음 자리로 안 간다 |
| 「**이 층의 다른 사람에게도 알리지 마**」 | `stopImmediatePropagation()` — 같은 자리의 남은 리스너도 안 부른다 |
| **택배 회사가 원래 하는 일**(문 앞에 두기) | **기본 동작** — 링크 이동 · 체크 토글 · 폼 제출 |
| 「**문 앞에 두지 마**」라는 쪽지 | `preventDefault()` — 기본 동작을 취소한다 |
| 쪽지를 **누가** 붙여도 된다 | 경로 위의 **어느 리스너**가 불러도 기본 동작은 취소된다 |
| **쪽지를 받지 않는 택배** | `cancelable: false` 인 이벤트 — `preventDefault()` 가 아무 일도 안 한다 |
| **「취소됐나」 확인란** | `e.defaultPrevented` |

- ★ **소식을 끊어도 택배는 온다** — `stopPropagation()` 은 기본 동작을 **안 막는다.**
- ★ **쪽지를 붙여도 소식은 퍼진다** — `preventDefault()` 는 전파를 **안 멈춘다.**

```text
   ★ 이 편의 본체 — 2×2 (진짜 클릭 · 대상 셋 모두 같은 모양)

                        조상 리스너가 불렸나      기본 동작이 일어났나
   없음                 예                        예
   stopPropagation      아니오                    예
   preventDefault       예                        아니오
   둘 다                아니오                    아니오

   stopPropagation 은 왼쪽 칸만,  preventDefault 는 오른쪽 칸만 바꾼다
```

## 이 주제가 답하려는 질문

1. **`stopPropagation` 과 `preventDefault` 는 각각 무엇을 바꾸나** — 서로의 칸을 건드리나.
2. **기본 동작은 언제 일어나나** — 그래서 **조상이 막을 수 있나**, 리스너 안에서 보이는 `checked` 는 무엇인가.
3. **`stopImmediatePropagation`·`cancelable`·`defaultPrevented` 는 무엇을 판정하나.**

## 동작 방식

### (1) ★★★ 본체 — 「멈춤 × 막음」 격자를 진짜 클릭으로

**언제 쓰나** — 「`stopPropagation` 했는데 링크가 이동한다」·「`preventDefault` 했는데 조상이 받는다」일 때.

**던진 것** — `#조상` 안에 **링크(`href="#도착"`) · 체크박스 · 폼 안의 제출 단추**를 두고, 대상 요소의 click 리스너가 **없음 / `stopPropagation` / `preventDefault` / 둘 다** 를 부르게 했다. `#조상` 의 bubble 리스너가 불렸나와 기본 동작이 일어났나를 적는다. 폼의 `submit` 리스너는 「제출 이벤트가 났다」를 적고 **실제 전송은 막는다.** 아래 (2)·(4)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa16b-17-grid.html -->
<!doctype html>
<meta charset="utf-8">
<title>17-grid</title>
<div id="조상">
  <p><a id="링크" href="#도착">링크</a></p>
  <p><input type="checkbox" id="상자"></p>
  <form id="양식"><button id="제출">제출</button></form>
</div>
<p id="도착">도착</p>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 대상 = [['링크', $('링크')], ['체크박스', $('상자')], ['제출 단추', $('제출')]];
const 방법 = ['없음', 'stopPropagation', 'preventDefault', '둘 다'];
const 던지기 = ['진짜', 'new MouseEvent', 'el.click()', 'new Event'];

let 모드 = '없음';
let 판 = null;
for (const [, el] of 대상) {
  el.addEventListener('click', e => {
    판.안쪽checked = $('상자').checked;
    if (모드 === 'stopPropagation' || 모드 === '둘 다') e.stopPropagation();
    if (모드 === 'preventDefault' || 모드 === '둘 다') e.preventDefault();
    판.cancelable = e.cancelable;
    판.defaultPrevented = e.defaultPrevented;
  });
}
$('조상').addEventListener('click', () => { 판.조상 = true; });
$('양식').addEventListener('submit', e => { 판.제출 = true; e.preventDefault(); });

window.__준비 = (m) => {
  history.replaceState(null, '', location.pathname);
  $('상자').checked = false;
  모드 = m;
  판 = { 조상: false, 제출: false };
  return 1;
};
window.__기본동작 = (이름) => 이름 === '링크' ? decodeURIComponent(location.hash) === '#도착'
  : 이름 === '체크박스' ? $('상자').checked : 판.제출;

const 결과 = {};
window.__기록 = (던짐, 이름, m) => {
  결과[[던짐, 이름, m]] = { 조상: 판.조상, 기본: __기본동작(이름), 안쪽: 판.안쪽checked,
                           cancelable: 판.cancelable, defaultPrevented: 판.defaultPrevented };
  return 1;
};
const 합성 = {
  'new MouseEvent': el => el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })),
  'el.click()': el => el.click(),
  'new Event': el => el.dispatchEvent(new Event('click', { bubbles: true, cancelable: true })),
};

const 단계 = [];
for (const 던짐 of 던지기) {
  for (const [이름] of 대상) {
    for (const m of 방법) {
      const 선택자 = '#' + (이름 === '링크' ? '링크' : 이름 === '체크박스' ? '상자' : '제출');
      단계.push(['js', `__준비(${JSON.stringify(m)})`]);
      if (던짐 === '진짜') 단계.push(['click', 선택자]);
      else 단계.push(['js', `합성[${JSON.stringify(던짐)}](document.querySelector(${JSON.stringify(선택자)})); 1`]);
      단계.push(['js', `__기록(${JSON.stringify(던짐)}, ${JSON.stringify(이름)}, ${JSON.stringify(m)})`]);
    }
  }
}
window.__단계 = 단계;

const 예 = b => b ? '예' : '아니오';
window.__끝 = () => {
  const O = [];
  O.push('진짜 클릭 — 대상 요소의 click 리스너가 하는 일 × 두 가지 관찰');
  O.push(padw('대상', 11) + padw('리스너가 부른 것', 18) + padw('조상 리스너가 불렸나', 22) + '기본 동작이 일어났나');
  for (const [이름] of 대상) {
    for (const m of 방법) {
      const r = 결과[['진짜', 이름, m]];
      O.push(padw(이름, 11) + padw(m, 18) + padw(예(r.조상), 22) + 예(r.기본));
    }
  }
  O.push('');
  O.push('같은 격자를 다른 던지기로 — 진짜와 갈린 칸');
  for (const 던짐 of 던지기.slice(1)) {
    let 갈림 = 0, 전체 = 0;
    const 어디 = [];
    for (const [이름] of 대상) for (const m of 방법) {
      const a = 결과[['진짜', 이름, m]], b = 결과[[던짐, 이름, m]];
      for (const 칸 of ['조상', '기본']) {
        전체++;
        if (a[칸] !== b[칸]) { 갈림++; 어디.push(이름 + '/' + m + '/' + 칸); }
      }
    }
    O.push('  ' + padw(던짐, 16) + '갈린 칸 = ' + 갈림 + ' / ' + 전체 + (어디.length ? '  (' + 어디.join(', ') + ')' : ''));
  }
  O.push('');
  O.push('체크박스 — 리스너 안에서 읽은 checked 와 디스패치가 끝난 뒤의 checked (진짜 클릭, 처음 값 false)');
  O.push(padw('리스너가 부른 것', 18) + padw('리스너 안', 11) + padw('끝난 뒤', 9) + padw('cancelable', 12) + 'defaultPrevented');
  for (const m of 방법) {
    const r = 결과[['진짜', '체크박스', m]];
    O.push(padw(m, 18) + padw(String(r.안쪽), 11) + padw(String(r.기본), 9) + padw(String(r.cancelable), 12) + r.defaultPrevented);
  }
  return O.join('\n');
};
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-17-grid.html | sed -n '1,14p'
진짜 클릭 — 대상 요소의 click 리스너가 하는 일 × 두 가지 관찰
대상       리스너가 부른 것  조상 리스너가 불렸나  기본 동작이 일어났나
링크       없음              예                    예
링크       stopPropagation   아니오                예
링크       preventDefault    예                    아니오
링크       둘 다             아니오                아니오
체크박스   없음              예                    예
체크박스   stopPropagation   아니오                예
체크박스   preventDefault    예                    아니오
체크박스   둘 다             아니오                아니오
제출 단추  없음              예                    예
제출 단추  stopPropagation   아니오                예
제출 단추  preventDefault    예                    아니오
제출 단추  둘 다             아니오                아니오
(exit 0)
```

- ★★ **대상 셋이 한 줄도 안 다르다** — 링크·체크박스·제출 단추가 **같은 네 줄 모양**이다.
- **`stopPropagation` 은 「조상 리스너가 불렸나」만 「아니오」로 바꾼다.** 기본 동작은 **그대로 일어났다** — 링크는 이동했고, 체크박스는 체크됐고, 폼은 제출 이벤트를 냈다.
- **`preventDefault` 는 「기본 동작」만 「아니오」로 바꾼다.** 조상 리스너는 **그대로 불렸다.**
- **둘 다 부르면 두 칸 다 「아니오」** 다.
- ★ **두 스위치가 서로의 칸을 한 번도 안 건드렸다** — 12줄 × 2칸 = 24칸 중 **엇갈린 칸이 없다.**

```text
   두 스위치가 끊는 자리 — 경로 그림 위에

   window ─ document ─ html ─ body ─ #조상 ─ … ─ 대상
                                        ▲            │
                                        │            │ click 리스너
             stopPropagation() ─────────┘ 여기로     │
                                         못 올라간다 │
                                                      ▼
                                              디스패치가 끝난 뒤
                                              기본 동작(이동·토글·제출)
                                                      ▲
             preventDefault() ────────────────────────┘ 이것만 취소한다
```

비용 — **`stopPropagation()` 은 남의 리스너를 조용히 죽인다.** 조상에 단 분석 코드·위임 리스너([18번 주제](../18-event-delegation/2-summary.md))·「바깥을 누르면 닫기」가 **예외 없이 안 불린다.** 기본 동작을 막고 싶으면 **`preventDefault()` 만** 부른다.

### (2) ★★ 같은 격자를 합성으로 던지면 — 진짜와 갈린 칸

**언제 쓰나** — 「기본 동작은 진짜 입력이라야 나겠지」 또는 「합성 테스트로 충분하겠지」일 때. **둘 다 틀릴 수 있다.**

```text
$ python3 wa16b-cdp.py page wa16b-17-grid.html | sed -n '16,19p'
같은 격자를 다른 던지기로 — 진짜와 갈린 칸
  new MouseEvent  갈린 칸 = 0 / 24
  el.click()      갈린 칸 = 0 / 24
  new Event       갈린 칸 = 6 / 24  (링크/없음/기본, 링크/stopPropagation/기본, 체크박스/없음/기본, 체크박스/stopPropagation/기본, 제출 단추/없음/기본, 제출 단추/stopPropagation/기본)
(exit 0)
```

- ★★ **`new MouseEvent('click')` 은 진짜와 갈린 칸이 0 / 24** 다. **합성 이벤트인데도 링크가 이동했고, 체크박스가 토글됐고, 폼이 제출 이벤트를 냈다.**
- **`el.click()` 도 0 / 24** 다.
- ★★ **`new Event('click')` 만 6 / 24** 다. 갈린 여섯 칸이 전부 **「기본」 칸**이고, 전부 **진짜에서는 기본 동작이 난 줄**(없음·`stopPropagation`)이다 — **`new Event` 로는 기본 동작이 아예 안 난다.**
- ★ **가르는 것은 「진짜냐 합성이냐」가 아니라 「`MouseEvent` 인가」다.** DOM 표준의 dispatch 는 **「이벤트가 `MouseEvent` 이고 타입이 `click` 이면」** 활성화 대상(activation target)을 잡는다. `isTrusted` 는 안 본다.

```text
   기본 동작이 나는가 — 무엇이 가르나

                               isTrusted   MouseEvent 인가   기본 동작
   사람의 진짜 클릭             true        예                난다
   new MouseEvent('click')      false       예                난다   <- 합성인데도
   el.click()                   false       예                난다
   new Event('click')           false       아니오            안 난다 <- 같은 이름인데도

   ★ DOM dispatch: 「MouseEvent 이고 type 이 click 이면」 activation target 을 잡는다
```

- ★ **그래서 「합성으로는 기본 동작이 안 드러날 것」이라는 예상은 이 판에서 틀렸다.** [14번 주제](../14-dialog-popover-scripting/2-summary.md)의 가벼운 닫기는 합성으로 한 칸도 안 움직였지만, **클릭의 활성화 동작은 다르다** — 이 둘을 같은 규칙으로 외우지 마라.

### (3) ★ 기본 동작은 디스패치가 **끝난 뒤** 돈다 — 그래서 조상이 막을 수 있다

**언제 쓰나** — 「`preventDefault` 는 타깃 리스너에서만 불러야 하나?」일 때.

**던진 것** — 같은 요소에 리스너 셋, 그리고 조상. 둘째 리스너가 무엇을 부르느냐에 따라 **어디까지 불리나**를 본다. 체크박스 쪽은 **조상이 막는 경우**와 **조상이 capture 에서 멈추는 경우**를 본다. 아래 (5)·(6)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa16b-17-imm.html -->
<!doctype html>
<meta charset="utf-8">
<title>17-imm</title>
<div id="조상"><button id="단추">단추</button></div>
<div id="상자조상"><input type="checkbox" id="상자"></div>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 로그 = [];
let 모드 = null;

// 가: 같은 요소에 리스너 셋, 둘째가 무엇을 부르나
for (const 표 of ['첫째', '둘째', '셋째']) {
  $('단추').addEventListener('click', e => {
    if (!모드) return;
    로그.push(표);
    if (표 === '둘째' && 모드 === 'stopPropagation') e.stopPropagation();
    if (표 === '둘째' && 모드 === 'stopImmediatePropagation') e.stopImmediatePropagation();
    if (표 === '둘째' && 모드 === 'cancelBubble = true') e.cancelBubble = true;
  });
}
$('조상').addEventListener('click', () => { if (모드) 로그.push('조상'); });
// 나: 조상의 capture 리스너가 멈추면
$('조상').addEventListener('click', e => { if (모드 === '조상 capture 에서 stopPropagation') { 로그.push('조상(capture)'); e.stopPropagation(); } }, true);

// 다: 조상의 bubble 리스너가 막으면 — 체크박스
let 조상막기 = false, 조상멈춤 = false, 상자리스너 = 0;
$('상자조상').addEventListener('click', e => { if (조상막기) e.preventDefault(); });
$('상자조상').addEventListener('click', e => { if (조상멈춤) e.stopPropagation(); }, true);
$('상자').addEventListener('click', () => { 상자리스너++; });
let 바뀜 = 0;
$('상자').addEventListener('change', () => { 바뀜++; });

const 줄 = [];
window.__한판 = m => { 모드 = m; 로그.length = 0; return 1; };
window.__적기 = m => { 줄.push('  ' + padw(m, 36) + ' → ' + 로그.join(' · ')); 모드 = null; return 1; };

const 단계 = [];
for (const m of ['없음', 'stopPropagation', 'stopImmediatePropagation', 'cancelBubble = true', '조상 capture 에서 stopPropagation']) {
  단계.push(['js', `__한판(${JSON.stringify(m)})`], ['click', '#단추'], ['js', `__적기(${JSON.stringify(m)})`]);
}
단계.push(['js', "조상막기 = true; 바뀜 = 0; $('상자').checked = false; 1"], ['click', '#상자'], ['js', "window.__조상후 = [$('상자').checked, 바뀜]; 조상막기 = false; 1"]);
단계.push(['js', "조상멈춤 = true; 상자리스너 = 0; 바뀜 = 0; $('상자').checked = false; 1"], ['click', '#상자'], ['js', "window.__멈춤후 = [$('상자').checked, 상자리스너, 바뀜]; 조상멈춤 = false; 1"]);
window.__단계 = 단계;

window.__끝 = () => {
  const O = [];
  O.push('가·나. 단추에 리스너 셋(첫째·둘째·셋째) + 조상 — 진짜 클릭, 둘째가 부른 것에 따라');
  O.push(...줄);
  O.push('');
  O.push('다. 조상의 bubble 리스너가 preventDefault — 진짜 클릭 뒤 체크박스 checked = ' + window.__조상후[0]
       + ' · change 이벤트 = ' + window.__조상후[1] + '번');
  O.push('   조상의 capture 리스너가 stopPropagation — 진짜 클릭 뒤 체크박스 checked = ' + window.__멈춤후[0]
       + ' · 체크박스 자신의 click 리스너 = ' + window.__멈춤후[1] + '번 · change 이벤트 = ' + window.__멈춤후[2] + '번');
  O.push('');
  O.push('라. cancelable 이 false 인 이벤트에서 preventDefault');
  let 안 = null;
  const 한 = e => { e.preventDefault(); 안 = e.defaultPrevented; };
  $('단추').addEventListener('x', 한);
  const r1 = $('단추').dispatchEvent(new Event('x', { cancelable: false }));
  O.push('  cancelable:false → defaultPrevented = ' + 안 + ' · dispatchEvent 의 반환값 = ' + r1);
  const r2 = $('단추').dispatchEvent(new Event('x', { cancelable: true }));
  O.push('  cancelable:true  → defaultPrevented = ' + 안 + ' · dispatchEvent 의 반환값 = ' + r2);
  $('단추').removeEventListener('x', 한);
  const 옛 = e => { e.returnValue = false; 안 = e.defaultPrevented; };
  $('단추').addEventListener('x', 옛);
  $('단추').dispatchEvent(new Event('x', { cancelable: true }));
  O.push('  returnValue = false 를 대입하면 → defaultPrevented = ' + 안);
  $('단추').removeEventListener('x', 옛);
  const 거짓 = () => false;
  $('단추').addEventListener('x', 거짓);
  const r3 = $('단추').dispatchEvent(new Event('x', { cancelable: true }));
  O.push('  addEventListener 리스너가 false 를 돌려주면 → dispatchEvent 의 반환값 = ' + r3);
  $('단추').removeEventListener('x', 거짓);
  $('단추').onclick = () => false;
  const 클릭 = new MouseEvent('click', { cancelable: true });
  $('단추').dispatchEvent(클릭);
  O.push('  onclick 속성 핸들러가 false 를 돌려주면 → defaultPrevented = ' + 클릭.defaultPrevented);
  $('단추').onclick = null;
  return O.join('\n');
};
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-17-imm.html | sed -n '8,9p'
다. 조상의 bubble 리스너가 preventDefault — 진짜 클릭 뒤 체크박스 checked = false · change 이벤트 = 0번
   조상의 capture 리스너가 stopPropagation — 진짜 클릭 뒤 체크박스 checked = true · 체크박스 자신의 click 리스너 = 0번 · change 이벤트 = 1번
(exit 0)
```

- ★★ **조상의 bubble 리스너가 `preventDefault()` 를 불러도 체크박스가 안 바뀐다**(`checked = false` · **`change` 이벤트 0번**). 기본 동작은 **경로를 다 돈 뒤에** 돌기 때문에, 그 전에 **누가 불렀든** 취소 표시(canceled flag)가 서 있으면 안 돈다.
- ★★ **조상의 capture 리스너가 `stopPropagation()` 을 부르면 체크박스 자신의 click 리스너는 0 번 불리는데, 체크는 되고 `change` 도 1번 난다**(`checked = true`). **전파를 끊어도 기본 동작은 돈다** — 대상에 리스너가 한 번도 안 불려도 그렇다.

```text
   DOM 「dispatch」 — 기본 동작은 맨 끝

   ① activation target 을 잡는다 (MouseEvent 의 click 이면)
   ② (체크박스) legacy-pre-activation: checked 를 먼저 뒤집는다
   ③ 경로를 훑는다 — capture 한 번, bubble 한 번    <- 여기서 누가 preventDefault 해도 된다
   ④ 취소 표시가 없으면   activation behavior      (이동 · change 이벤트 · 제출)
      취소 표시가 있으면   legacy-canceled-activation (체크박스: checked 를 되돌린다)

   stopPropagation 은 ③ 의 「다음 자리」만 끊는다 — ④ 는 그대로 온다
```

### (4) ★★ 체크박스의 함정 — 리스너 안에서는 이미 바뀌어 있다

**언제 쓰나** — 「`preventDefault()` 했는데 리스너 안에서 `checked` 가 `true` 로 보인다」일 때.

```text
$ python3 wa16b-cdp.py page wa16b-17-grid.html | sed -n '21,26p'
체크박스 — 리스너 안에서 읽은 checked 와 디스패치가 끝난 뒤의 checked (진짜 클릭, 처음 값 false)
리스너가 부른 것  리스너 안  끝난 뒤  cancelable  defaultPrevented
없음              true       true     true        false
stopPropagation   true       true     true        false
preventDefault    true       false    true        true
둘 다             true       false    true        true
(exit 0)
```

- ★★ **리스너 안에서 읽은 `checked` 는 네 줄 모두 `true`** 다 — **막든 안 막든.** 처음 값은 `false` 였다.
- **디스패치가 끝난 뒤에는 막은 두 줄만 `false` 로 돌아가 있다.**
- 명세가 그렇게 정한다 — HTML 표준의 **legacy-pre-activation behavior** 가 **리스너를 부르기 전에** 체크박스의 checkedness 를 뒤집고, 취소됐으면 **legacy-canceled-activation behavior** 가 **리스너가 다 끝난 뒤에** 되돌린다.
- ★ **그래서 「리스너 안에서 `checked` 를 보고 막을지 정한다」는 코드는 이미 뒤집힌 값을 본다.** 「막으면 체크가 안 된다」를 리스너 안에서 확인하려 하면 **거꾸로 보인다.**
- **`cancelable` 은 네 줄 모두 `true`**, **`defaultPrevented` 는 막은 두 줄만 `true`** 다.

```text
   체크박스 한 번의 클릭 — checked 가 두 번 바뀐다 (preventDefault 한 경우)

   클릭 전           checked = false
     │ legacy-pre-activation   (리스너보다 먼저)
     ▼
   리스너 안          checked = true    <- ★ 막았는데도 true 로 보인다
     │ e.preventDefault()
     ▼
   디스패치 끝        legacy-canceled-activation   (리스너가 다 끝난 뒤)
     ▼
   끝난 뒤            checked = false   <- 되돌려졌다 · change 이벤트 0번((3))
```

```text
   창 ③ — 같은 것을 두 번 읽기가 이 함정을 잡는다

                       리스너 안    끝난 뒤
   막지 않음           true         true
   막음                true         false     <- 두 번 읽어야 차이가 보인다
```

### (5) `stopImmediatePropagation` — 같은 자리의 남은 리스너까지

**언제 쓰나** — 「같은 요소에 단 다른 리스너도 막고 싶다」일 때.

```text
$ python3 wa16b-cdp.py page wa16b-17-imm.html | sed -n '1,6p'
가·나. 단추에 리스너 셋(첫째·둘째·셋째) + 조상 — 진짜 클릭, 둘째가 부른 것에 따라
  없음                                 → 첫째 · 둘째 · 셋째 · 조상
  stopPropagation                      → 첫째 · 둘째 · 셋째
  stopImmediatePropagation             → 첫째 · 둘째
  cancelBubble = true                  → 첫째 · 둘째 · 셋째
  조상 capture 에서 stopPropagation    → 조상(capture)
(exit 0)
```

- **`stopPropagation`** — 둘째가 불렀는데 **셋째는 불렸다.** 조상만 안 불렸다. **같은 자리의 남은 리스너는 계속 부른다.**
- ★ **`stopImmediatePropagation`** — **셋째도 안 불렸다.** 같은 자리의 남은 리스너까지 멈춘다.
- **`cancelBubble = true`** — `stopPropagation` 과 **같은 결과**다. 명세상 `cancelBubble` 은 stop propagation 플래그의 **옛 이름**이다.
- ★ **조상의 capture 리스너에서 `stopPropagation`** — **대상의 리스너 셋이 하나도 안 불렸다.** 경로를 **내려가는 길에서** 끊었기 때문이다([16번 주제](../16-event-propagation-phases/2-summary.md)의 경로 그림).

```text
   같은 요소에 리스너 셋 — 둘째가 부르면

                               첫째  둘째  셋째  조상
   없음                         O     O     O     O
   stopPropagation              O     O     O     X    <- 자리를 떠나는 것만 막는다
   stopImmediatePropagation     O     O     X     X    <- 이 자리의 남은 것도
   cancelBubble = true          O     O     O     X    <- stopPropagation 의 옛 이름

   명세: stopImmediatePropagation = stop propagation 플래그 + stop immediate propagation 플래그
         inner invoke 는 리스너 하나를 부른 뒤 「immediate 플래그가 서 있으면 break」
```

- **순서에 기대는 방어**다 — `stopImmediatePropagation` 은 **먼저 등록된 리스너**만 막을 수 있다. 첫째가 이미 불린 뒤다([15번 주제](../15-listener-registration/2-summary.md)의 (8)에서 목록 변경과 견줬다).

### (6) `cancelable` · `defaultPrevented` · `dispatchEvent` 의 반환값

**언제 쓰나** — 「`preventDefault` 가 먹혔나」를 코드로 확인할 때.

```text
$ python3 wa16b-cdp.py page wa16b-17-imm.html | sed -n '11,16p'
라. cancelable 이 false 인 이벤트에서 preventDefault
  cancelable:false → defaultPrevented = false · dispatchEvent 의 반환값 = true
  cancelable:true  → defaultPrevented = true · dispatchEvent 의 반환값 = false
  returnValue = false 를 대입하면 → defaultPrevented = true
  addEventListener 리스너가 false 를 돌려주면 → dispatchEvent 의 반환값 = true
  onclick 속성 핸들러가 false 를 돌려주면 → defaultPrevented = true
(exit 0)
```

- **`cancelable: false` 인 이벤트에서는 `preventDefault()` 가 아무 일도 안 한다** — `defaultPrevented` 가 `false` 다. **예외도 경고도 없다.**
- **`dispatchEvent` 의 반환값은 「취소 안 됐나」** — 취소되면 `false`, 아니면 `true` 다. 합성 이벤트를 던진 쪽이 **「누가 막았나」를 이 값으로** 안다.
- **`returnValue = false` 대입은 `preventDefault()` 와 같다** — 명세의 옛 표면이다.
- ★ **`addEventListener` 로 단 리스너가 `false` 를 돌려주는 것은 아무것도 안 한다** — `dispatchEvent` 가 `true`(취소 안 됨)를 돌려줬다.
- ★ **`onclick` 속성 핸들러가 `false` 를 돌려주면 취소된다** — `defaultPrevented = true`. **표면이 다르면 규칙이 다르다.**
- ★ **「막을 수 있나」와 「막혔나」는 다른 질문**이다 — 앞엣것은 `cancelable`, 뒤엣것은 `defaultPrevented` 다. **`passive` 리스너에서는 `cancelable` 이 `true` 인데도 막을 수 없다** — [15번 주제](../15-listener-registration/2-summary.md)의 (9)가 합성으로 쟀고, **진짜 휠·터치에서 무엇이 달라지는지는 [19번 주제](../19-passive-and-scroll/2-summary.md)** 가 정본이다.

```text
   「막았나」를 묻는 세 자리

   이벤트의 성질   e.cancelable        막을 수 있는 이벤트인가
   결과            e.defaultPrevented  실제로 막혔나
   던진 쪽         dispatchEvent(e)    false 면 누군가 막았다

   명세: set the canceled flag 는 「cancelable 이고 passive 리스너 안이 아닐 때만」 표시를 세운다
```

### (7) 키보드로 눌러도 click 이 오고, 같은 방법으로 막힌다

**언제 쓰나** — 「키보드 사용자도 막히나」를 확인할 때.

**던진 것** — 체크박스에 포커스를 주고 **진짜 Space**, 링크에 포커스를 주고 **진짜 Enter**. click 리스너가 막는 판과 안 막는 판.

```html
<!-- wa16b-17-key.html -->
<!doctype html>
<meta charset="utf-8">
<title>17-key</title>
<p><a id="링크" href="#도착">링크</a></p>
<p><input type="checkbox" id="상자"></p>
<p id="도착">도착</p>
<script>
const $ = id => document.getElementById(id);
const 로그 = [];
let 막기 = false;
for (const el of [$('링크'), $('상자')]) {
  el.addEventListener('click', e => {
    로그.push('#' + el.id + ' click · isTrusted=' + e.isTrusted + ' · detail=' + e.detail + ' · 막기=' + 막기);
    if (막기) e.preventDefault();
  });
}
window.__준비 = m => { 막기 = m; history.replaceState(null, '', location.pathname); $('상자').checked = false; return 1; };
window.__적기 = 무엇 => {
  로그.push('  → ' + 무엇 + ' 뒤: 링크 이동 = ' + (decodeURIComponent(location.hash) === '#도착') + ' · 체크박스 checked = ' + $('상자').checked);
  return 1;
};
const 단계 = [];
for (const 막 of [false, true]) {
  단계.push(['js', `__준비(${막})`], ['js', "$('상자').focus(); 1"], ['key', ' ', 'Space', 32, ' '], ['js', `__적기('체크박스에서 Space')`]);
  단계.push(['js', `__준비(${막})`], ['js', "$('링크').focus(); 1"], ['key', 'Enter', 'Enter', 13, '\r'], ['js', `__적기('링크에서 Enter')`]);
}
window.__단계 = 단계;
window.__끝 = () => 로그.join('\n');
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-17-key.html
#상자 click · isTrusted=true · detail=0 · 막기=false
  → 체크박스에서 Space 뒤: 링크 이동 = false · 체크박스 checked = true
#링크 click · isTrusted=true · detail=0 · 막기=false
  → 링크에서 Enter 뒤: 링크 이동 = true · 체크박스 checked = false
#상자 click · isTrusted=true · detail=0 · 막기=true
  → 체크박스에서 Space 뒤: 링크 이동 = false · 체크박스 checked = false
#링크 click · isTrusted=true · detail=0 · 막기=true
  → 링크에서 Enter 뒤: 링크 이동 = false · 체크박스 checked = false
(exit 0)
```

- ★ **키보드로 눌러도 `click` 이벤트가 온다** — `isTrusted=true` 이고 **`detail=0`** 이다(마우스 클릭 수가 없다).
- **click 리스너의 `preventDefault()` 가 키보드 활성화도 막는다** — Space 로 체크가 안 되고, Enter 로 이동이 안 된다.
- ★ **그래서 「클릭을 막는다」는 코드는 키보드 사용자도 막는다.** 마우스만 막으려고 `click` 에서 막으면 키보드 접근이 같이 죽는다. 키보드 동작의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **41번**이다.

```text
   진짜 키 → 합성된 click → 같은 기본 동작

   Space (체크박스에 포커스)    ─┐
                                 ├─> click 이벤트 (isTrusted=true · detail=0)
   Enter (링크에 포커스)        ─┘        │
                                          ├─ preventDefault 없음 -> 토글 / 이동
                                          └─ preventDefault      -> 둘 다 안 난다
```

### (8) 라디오 · 링크를 한 곳에서 가로채기 · Enter 의 암묵 제출

**언제 쓰나** — 체크박스 말고도 **먼저 바뀌는** 요소가 있는지, **SPA 라우터**가 링크를 어떻게 막는지, **Enter 로 제출되는 폼**을 어떻게 막는지.

```html
<!-- wa16b-17-more.html -->
<!doctype html>
<meta charset="utf-8">
<title>17-more</title>
<p><input type="radio" name="고름" id="첫" checked> <input type="radio" name="고름" id="둘"></p>
<nav><a id="길" href="#다른화면">다른 화면</a></nav>
<form id="양식"><input id="칸" value="글"><button id="보냄">보냄</button></form>
<p id="다른화면">다른 화면</p>
<script>
const $ = id => document.getElementById(id);
const O = [];
let 판 = {};

// 가: 라디오 — 둘째를 누르고 막는다
$('둘').addEventListener('click', e => {
  판.안 = '첫=' + $('첫').checked + ' 둘=' + $('둘').checked;
  e.preventDefault();
});
window.__라디오후 = () => { O.push('가. 라디오 둘째를 진짜로 누르고 click 리스너가 preventDefault (처음: 첫=true 둘=false)');
  O.push('   리스너 안  ' + 판.안);
  O.push('   끝난 뒤    첫=' + $('첫').checked + ' 둘=' + $('둘').checked); return 1; };

// 나: document 의 capture 리스너 하나가 모든 링크를 가로챈다(라우터 꼴)
let 가로챔 = [];
document.addEventListener('click', e => {
  const a = e.target.closest('a');
  if (!a) return;
  e.preventDefault();
  가로챔.push(a.getAttribute('href'));
}, true);
window.__링크후 = () => { O.push('나. document 의 capture 리스너가 링크 click 을 preventDefault — 진짜 클릭 뒤');
  O.push('   가로챈 href = ' + 가로챔.join(',') + ' · location.hash = "' + decodeURIComponent(location.hash) + '"'); return 1; };

// 다: 입력칸에서 Enter — 암묵 제출이 제출 단추에 click 을 낸다
const 다로그 = [];
let 막기 = false;
$('보냄').addEventListener('click', e => { 다로그.push('보냄 click · isTrusted=' + e.isTrusted + ' · detail=' + e.detail); if (막기) e.preventDefault(); });
$('양식').addEventListener('submit', e => { 다로그.push('submit'); e.preventDefault(); });
window.__다 = (m, 끝) => { if (끝) { O.push('   ' + m + ' → ' + (다로그.join(' → ') || '(아무것도 안 남)')); 다로그.length = 0; } else { 막기 = m; } return 1; };

window.__단계 = [
  ['click', '#둘'], ['js', '__라디오후()'],
  ['click', '#길'], ['js', '__링크후()'],
  ['js', "O.push('다. 입력칸에 포커스를 두고 진짜 Enter'); __다(false)"], ['js', "$('칸').focus(); 1"],
  ['key', 'Enter', 'Enter', 13, '\r'], ['js', "__다('보냄 click 을 안 막으면', true)"],
  ['js', '__다(true)'], ['js', "$('칸').focus(); 1"],
  ['key', 'Enter', 'Enter', 13, '\r'], ['js', "__다('보냄 click 을 preventDefault 하면', true)"],
];
window.__끝 = () => O.join('\n');
</script>
```

```text
$ python3 wa16b-cdp.py page wa16b-17-more.html | sed -n '1,3p'
가. 라디오 둘째를 진짜로 누르고 click 리스너가 preventDefault (처음: 첫=true 둘=false)
   리스너 안  첫=false 둘=true
   끝난 뒤    첫=true 둘=false
(exit 0)
```

- ★ **라디오도 체크박스와 같은 모양**이다 — 리스너 안에서는 **이미 `둘` 이 선택되고 `첫` 이 풀려 있고**, 막으면 **끝난 뒤에 `첫` 으로 돌아간다.** HTML 표준의 legacy-pre-activation 이 라디오에서는 「그룹에서 선택된 것을 기억해 두고 자기를 선택」, canceled-activation 이 「기억해 둔 것을 되살리기」다.

```text
$ python3 wa16b-cdp.py page wa16b-17-more.html | sed -n '4,5p'
나. document 의 capture 리스너가 링크 click 을 preventDefault — 진짜 클릭 뒤
   가로챈 href = #다른화면 · location.hash = ""
(exit 0)
```

- ★ **`document` 의 capture 리스너 하나가 모든 링크를 가로챘다** — `href` 를 읽고 `preventDefault()` 했더니 **이동이 없었다**(`location.hash` 가 빈 문자열). **SPA 라우터가 링크를 가로채는 꼴**이 이것이다 — (3)의 「기본 동작은 끝에 돈다 · 경로 위 누구든 막을 수 있다」를 그대로 쓴다.
- capture 로 단 이유 — 가장 먼저 받으려고다. 다만 **막기만 할 것이면 bubble 로 달아도 된다** — 기본 동작은 어차피 경로가 다 끝난 뒤에 돌고, (3)에서 **조상의 bubble 리스너가 체크박스를 막았다.** (링크를 bubble 로 가로채는 판은 따로 던지지 않았다.)

```text
$ python3 wa16b-cdp.py page wa16b-17-more.html | sed -n '6,8p'
다. 입력칸에 포커스를 두고 진짜 Enter
   보냄 click 을 안 막으면 → 보냄 click · isTrusted=true · detail=0 → submit
   보냄 click 을 preventDefault 하면 → 보냄 click · isTrusted=true · detail=0
(exit 0)
```

- ★★ **입력칸에서 Enter 를 누르면 제출 단추에 `click` 이 난다** — `isTrusted=true` · `detail=0`. 그 뒤에 `submit` 이 났다. 폼의 **암묵 제출(implicit submission)** 이 「기본 단추에 click 을 낸다」로 돌기 때문이다.
- ★ **그 `click` 을 막으면 `submit` 도 안 난다.** 그래서 「단추의 click 에서 막는다」는 코드는 **Enter 제출까지** 막는다 — (7)의 「키보드도 같은 방법으로 막힌다」의 폼 쪽 판이다. 제출 모델의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **21번**이다.

```text
   Enter 한 번이 지나는 길

   입력칸에서 Enter
       │ 암묵 제출
       ▼
   기본 단추에 click (isTrusted=true · detail=0)
       ├─ preventDefault 없음 ──▶ submit 이벤트 ──▶ (제출)
       └─ preventDefault      ──▶ 아무것도 안 난다

   ★ 「제출을 막는다」는 submit 이벤트에서 막는 것이 정석이다 — 단추·Enter 를 다 받는다
```

```text
   「먼저 바뀌는」 요소 — 이 편에서 확인한 둘

                  리스너 안           막은 뒤(끝난 뒤)
   체크박스       이미 뒤집힘          되돌아감           (4)
   라디오         이미 새 것이 선택    옛 것이 되살아남   (8)
   링크           (바뀌는 것 없음)     이동 안 함          — 이동은 맨 끝에만
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   멈추는 쪽(전파)                           막는 쪽(기본 동작)
   ------------------------------------      ------------------------------------
   e.stopPropagation()                       e.preventDefault()
   e.stopImmediatePropagation()              e.returnValue = false   (옛 표면)
   e.cancelBubble = true   (옛 표면)                onclick = () => false   (속성 핸들러만)
                                             e.cancelable            막을 수 있나
                                             e.defaultPrevented      막혔나
                                             dispatchEvent(e) 의 반환값   false = 막혔다
```

### 어디서 헷갈리나

- **`return false`** — `addEventListener` 로 단 리스너에서는 **아무것도 안 한다.** `onclick` 속성 핸들러에서는 **취소가 된다**((6)). 같은 한 줄이 표면에 따라 갈린다.
- **`preventDefault` 는 경로 위 어디서 불러도 된다** — 조상도 막을 수 있다((3)).
- **`stopPropagation` 은 기본 동작을 안 막는다** — 이것을 기대하고 쓰는 코드가 가장 흔하다((1)).

## 어디서 틀리나

### 1. 링크 이동을 막으려고 `stopPropagation()` 을 부른다

**이동한다**((1)). 전파만 끊긴다. **`preventDefault()`** 를 불러야 한다.

### 2. 부모에 알리지 않으려고 `preventDefault()` 를 부른다

**부모는 받는다**((1)). 기본 동작만 취소된다.

### 3. 기본 동작을 막으려고 `stopPropagation` 과 `preventDefault` 를 습관처럼 둘 다 부른다

**기본 동작은 막히지만 조상의 리스너도 다 죽는다** — 위임 리스너·분석 코드·「바깥 클릭 닫기」가 **조용히** 안 불린다. 필요한 것만 부른다.

### 4. 체크박스 click 리스너 안에서 `checked` 를 보고 판단한다

**이미 뒤집힌 값**이다((4)). 원래 값이 필요하면 `!checked` 로 읽거나 **`change` 이벤트**를 쓴다 — 취소된 클릭에서는 **0번** 났다((3)).

### 5. 합성 이벤트로는 기본 동작이 안 난다고 믿는다

**`new MouseEvent('click')` 과 `el.click()` 은 기본 동작을 낸다**((2)). 안 나는 것은 **`new Event('click')`** 이다 — 이름이 같아도 **`MouseEvent` 가 아니면** 활성화가 없다.

### 6. `cancelable` 을 보고 「막을 수 있다」고 판정한다

**`passive` 리스너에서는 `cancelable` 이 `true` 여도 못 막는다**((6) · [19번 주제](../19-passive-and-scroll/2-summary.md)). 결과는 `defaultPrevented` 로 확인한다.

### 7. 마우스 클릭만 막으려고 `click` 에서 막는다

**키보드 활성화도 같이 막힌다**((7)). 폼이면 **입력칸의 Enter 제출까지** 막힌다((8)).

### 8. 폼 제출을 단추의 click 에서 막는다

**이 판에서는 동작했다** — Enter 도 단추의 click 을 거쳐 같이 막혔다((8)). 다만 그 코드는 **「제출은 반드시 단추의 click 을 거친다」에 기댄다.** 제출을 막는 자리는 **`submit` 이벤트**가 정석이다 — 이 판에서 단추 클릭과 Enter 가 **둘 다 `submit` 을 거쳤다.**

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `stopPropagation` 이 **경로의 다음 자리**만 끊고 기본 동작은 안 건드리는 것 | **명세**(DOM — stop propagation 플래그는 invoke 만 본다) |
| `preventDefault` 가 **취소 표시**만 세우고 전파는 안 건드리는 것 | **명세**(DOM — set the canceled flag) |
| 기본 동작이 **경로를 다 돈 뒤에** 도는 것 | **명세**(DOM — dispatch 의 activation behavior 가 마지막) |
| **`MouseEvent` 의 `click` 이면** 합성이어도 활성화가 도는 것 | **명세**(DOM — isActivationEvent 는 `isTrusted` 를 안 본다) · **이 판도 그랬다**((2)) |
| 체크박스가 **리스너보다 먼저** 뒤집히고 취소되면 **뒤에** 되돌아가는 것 | **명세**(HTML — legacy-pre-activation · legacy-canceled-activation) |
| `stopImmediatePropagation` 이 같은 자리의 남은 리스너를 막는 것 | **명세**(DOM — inner invoke 의 break) |
| `cancelBubble`·`returnValue` 가 옛 이름인 것 | **명세**(DOM — legacy 표면으로 남아 있다) |
| `addEventListener` 리스너의 `return false` 가 **아무것도 안 하고**, `onclick` 의 `return false` 는 **취소가 되는** 것 | ★ **이 판의 관찰**((6)). 속성 핸들러의 반환값 처리는 HTML 의 이벤트 핸들러 절이 정하는데 **이 문서는 그 절을 열어 확인하지 않았다** |
| 키보드 Space·Enter 가 **`click` 을 만들어** 같은 기본 동작을 내는 것 | ★ **이 판의 관찰**이다. 요소마다 무엇이 click 을 만드는지는 이 문서가 명세로 전수 확인하지 않았다 |
| 라디오가 리스너보다 먼저 선택되고 취소되면 되살아나는 것 | **명세**(HTML — legacy-pre-activation · legacy-canceled-activation 의 라디오 칸) · 이 판도 그랬다((8)) |
| 입력칸의 Enter 가 **기본 단추에 `click` 을 내고** 그것을 막으면 제출이 안 되는 것 | ★ **이 판의 관찰**((8)). 암묵 제출 절은 이 문서가 열어 확인하지 않았다 |
| `detail=0`(키보드로 만든 click) | ★ **이 판의 관찰** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 링크 이동·폼 제출·체크를 막는다 | `preventDefault()` | `stopPropagation()` |
| 조상에게 안 알린다 | `stopPropagation()` — **정말 필요할 때만** | `preventDefault()` |
| 같은 요소의 다른 리스너도 막는다 | `stopImmediatePropagation()` — **먼저 등록돼야** 한다 | 등록 순서를 모른 채 쓰기 |
| 여러 곳을 한 곳에서 막는다 | **조상에서** `preventDefault()`((3)) | 자식마다 리스너 |
| 체크 상태를 보고 판단한다 | `change` 이벤트 · 또는 `!checked` | click 리스너 안의 `checked` 를 그대로 |
| 합성 테스트로 기본 동작을 확인한다 | `el.click()` · `new MouseEvent('click', …)` | `new Event('click')` |
| 「막혔나」를 확인한다 | `defaultPrevented` · `dispatchEvent` 반환값 | `cancelable` |

## 핵심 문장

1. **`stopPropagation` 은 전파만, `preventDefault` 는 기본 동작만 바꾼다** — 진짜 클릭 24칸에서 서로의 칸을 한 번도 안 건드렸다.
2. **기본 동작은 경로를 다 돈 뒤에 돈다** — 그래서 **조상도 막을 수 있고**, 전파를 끊어도 **기본 동작은 온다.**
3. **체크박스는 리스너보다 먼저 뒤집힌다** — 리스너 안의 `checked` 는 막든 안 막든 새 값이고, 막으면 **끝난 뒤에** 되돌아간다.
4. **합성이어도 `MouseEvent` 의 `click` 이면 기본 동작이 난다** — 갈리는 것은 `new Event('click')` 이다.
5. **`stopImmediatePropagation` 은 같은 자리의 남은 리스너까지 멈춘다.**
6. **「막을 수 있나」는 `cancelable`, 「막혔나」는 `defaultPrevented`** 다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 17번)
- [16번 주제](../16-event-propagation-phases/2-summary.md) — 경로와 세 단계. **그쪽은 경로가 어떻게 생기나까지, 여기는 그 경로를 어디서 끊나부터.** 진짜 입력 하네스도 거기 있다
- [15번 주제](../15-listener-registration/2-summary.md) — `passive` 가 `preventDefault` 를 무효로 만드는 규칙(합성) · 목록 변경과 `stopImmediatePropagation` 의 견줌
- [14번 주제](../14-dialog-popover-scripting/2-summary.md) — `cancel` 이벤트의 `cancelable` 이 **사용자 활성화에 달린** 자리. 「막을 수 있나」가 이벤트마다 다르다는 사례
- [18번 주제](../18-event-delegation/2-summary.md) — `stopPropagation` 한 자식이 **위임을 깨는** 자리
- [19번 주제](../19-passive-and-scroll/2-summary.md) — **`passive` 에서 `preventDefault` 가 무시되는 것의 정본.** 여기는 경계만 긋는다
- HTML 갈래 [16번 주제](../../languages/html/syntax/16-links/2-summary.md) — 링크의 `rel`·`target` 이 기본 동작에 무엇을 더하나. **그쪽은 링크가 무엇을 하나, 여기는 그것을 어떻게 취소하나**
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **21번**(폼 제출 모델) · **24번**(체크박스 등 선택 타입) — `preventDefault` 로 막을 **기본 동작 자체의 정본**
- 목록의 **21번 주제**(커스텀 이벤트) — 내가 만든 이벤트를 `cancelable` 로 던지고 **`dispatchEvent` 반환값으로 「누가 막았나」를 받는** 형태

## 용어 풀이

- **기본 동작(default action)** — 요소가 이벤트를 받고 **원래 하는 일**. 명세 용어로는 activation behavior 등.
- **activation behavior** — `click` 으로 요소가 「활성화」될 때 하는 일(링크 이동 · 체크 토글 · 폼 제출).
- **activation target** — dispatch 가 처음에 잡아 두는 「활성화될 요소」. `MouseEvent` 의 `click` 일 때만 잡는다.
- **legacy-pre-activation behavior** — 리스너보다 **먼저** 하는 일. 체크박스는 여기서 뒤집힌다.
- **legacy-canceled-activation behavior** — 취소됐을 때 **나중에** 하는 일. 체크박스는 여기서 되돌아간다.
- **취소 표시(canceled flag)** — `preventDefault()` 가 세우는 표시. `defaultPrevented` 가 이것을 읽는다.
- **stop propagation 플래그** — `stopPropagation()` 이 세우는 표시. 경로의 다음 자리로 안 간다.
- **stop immediate propagation 플래그** — 같은 자리의 남은 리스너도 안 부르게 하는 표시.
- **`cancelable`** — 이벤트가 취소될 수 있는 성질. 이벤트를 만들 때 정해진다.
- **`defaultPrevented`** — 실제로 취소됐나.
- **`cancelBubble`·`returnValue`** — 두 플래그의 옛 이름.

## 더 들어가면

- **`mousedown` 에서 `preventDefault()`** 는 포커스 이동과 글자 선택을 막는다 — 그 뒤의 `click` 과는 **다른 이벤트의 다른 기본 동작**이다. 이 편은 던지지 않았다.
- **`label` 을 누르면 연결된 입력에 click 이 한 번 더 난다** — 라벨 연결의 정본은 HTML 갈래 목록의 **25번**이다. 이 편은 던지지 않았다.
- **`form.submit()` 은 `submit` 이벤트를 안 내고, `form.requestSubmit()` 은 낸다** — 폼 제출 모델의 몫이라 던지지 않았다.
- **`on*` 속성 핸들러의 `return false` 가 취소가 되는 것**은 (6)에서 `onclick` 하나만 던졌다. 다른 이벤트 타입의 예외 규칙(반환값을 거꾸로 읽는 타입이 있다는 설명)은 **확인하지 않았다.**
- **`passive` 리스너에서 `preventDefault()` 가 조용히 무시되는 것**과 **진짜 휠·터치에서 `cancelable` 자체가 `false` 가 되는 것**은 [19번 주제](../19-passive-and-scroll/2-summary.md)에서 진짜 입력으로 쟀다.
