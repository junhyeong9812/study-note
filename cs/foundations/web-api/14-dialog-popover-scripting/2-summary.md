# web-api/14 — `dialog`·`popover` 의 스크립트 제어: `showModal()`·`togglePopover()`·최상위 레이어·포커스 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 여기서 다루는 것은 「`<dialog>` 를 어떻게 쓰나」가 아니라 「**스크립트가 그것을 어떻게 열고 닫고, 그때 포커스와 최상위 레이어가 어떻게 움직이나**」다. 마크업 표면(`open` 속성·`::backdrop` 선언·`popovertarget`)은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **47번** 과 **48번** 이 정본이고 여기서 다시 쓰지 않는다.\
> **기준 소스** — [HTML Living Standard — The `dialog` element](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element) · [같은 표준 — Popover API](https://html.spec.whatwg.org/multipage/popover.html) · [같은 표준 — The top layer](https://html.spec.whatwg.org/multipage/interaction.html#the-top-layer) · [같은 표준 — `inert`](https://html.spec.whatwg.org/multipage/interaction.html#inert-subtrees) · [WHATWG Close Watcher API](https://wicg.github.io/close-watcher/) · [CSS Position Layout — `::backdrop`](https://drafts.csswg.org/css-position-4/#backdrop). 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 블록마다 명령이 배너로 실려 있고, 그 배너에는 **`--window-size=1000,800`** 이 들어 있다 — **좌표 탐침이 창 크기에 달려 있어 창을 빼면 재현되지 않는다.**\
> ★★ **이 편에는 `--dump-dom` 말고 창이 하나 더 있다** — **CDP 로 진짜 키와 진짜 마우스를 넣었다**((12)). 가벼운 닫기와 `Esc` 는 **합성 이벤트로는 한 칸도 안 움직인다.**\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** `popover` 와 `dialog` 의 Baseline 상태는 갈래 [`../README.md`](../README.md) 의 지원 표를 따르고 **이 문서가 다시 재지 않았다**(미실행).\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `dialog` 는 오래된 표면이고 `popover`·`moveBefore` 쪽은 새 표면이다.\
> **선행** — [03번 주제](../03-node-creation-insertion-removal/2-summary.md)(노드를 붙이고 떼는 것)와 [08번 주제](../08-getcomputedstyle/2-summary.md)(계산값을 읽는다는 것), 그리고 CSS 갈래의 [22번 주제](../../languages/css/syntax/22-stacking-context-and-z-index/2-summary.md)(쌓임 맥락과 `z-index`).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 상태를 묻지 시간을 안 재기 때문이다. 다만 **부적용인 창**이 하나 있고, **못 보는 것**이 여럿 있다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | `open`·`:modal`·`:popover-open` · `returnValue` · 예외 이름과 문구 · 초기 포커스가 어디로 가나 · 가벼운 닫기 격자 · `beforetoggle`/`toggle` 순서 | 같은 판·같은 창 크기면 결정적이다. **캡처를 두 판 돌려 95블록이 한 글자도 같았다** |
| **흔들린다** | **창 크기를 바꾸면 좌표 탐침 전부** | `elementFromPoint(x, y)` 와 `getBoundingClientRect()` 가 뷰포트에 달렸다. 배너에 `--window-size=1000,800` 을 박은 이유다 |
| **흔들린다** | `창.getBoundingClientRect().width` 의 **234** | 글꼴·기본 여백에 달린 값이다. **대조할 것은 숫자가 아니라 「0 에서 0 이 아닌 값으로 바뀐다」는 성질**이다 |
| **부적용** | `getComputedStyle(dialog, '::backdrop')` | **열기 전과 연 뒤가 한 글자도 같다.** 「재 봤더니 같았다」가 아니라 「**잴 것이 없다**」다((5)) |
| **못 본다** | 스크린리더가 이 모달을 **뭐라고 읽는지** | 접근성 트리는 보조 기술의 **입력**이지 출력이 아니다 |
| **못 본다** | `::backdrop` 이 실제로 칠해진 **픽셀** · 모바일 가상 키보드 · 포커스 링의 생김새 | 스크린숏을 찍지 않았다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

## 한눈에 — 쉽게 말하면

**★ `showModal()` 과 `showPopover()` 가 하는 일은 「보이게 하는 것」이 아니라 「무대 위로 올리는 것」이다. 무대에 올라간 것은 객석의 `z-index` 를 전부 이긴다.**

연극 무대에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **객석** | 평범한 문서. 여기서는 `z-index` 로 앞뒤를 다툰다 |
| **무대** | **최상위 레이어(top layer)**. 객석 위에 통째로 얹힌 다른 판이다 |
| 무대에 올라가는 **문 두 개** | `showModal()` 과 `showPopover()` |
| 객석에서 일어서기만 한 것 | `show()` 와 `open` 속성 — **무대에는 안 올라간다** |
| **조명이 배우에게 간다** | 포커스가 안쪽 첫 요소로 옮겨 간다 |
| **객석 불이 꺼진다** | 배경이 막힌다 — 클릭도 포커스도 안 간다 |
| 객석과 무대 사이의 **막** | `::backdrop` |
| **무대에서 내려오는 길** | `close()` · `hidePopover()` · `Esc` · 바깥 클릭 |
| 배우가 **쪽지를 들고 내려온다** | `returnValue` |
| 무대에 **여럿이 겹쳐 선다** | 최상위 레이어는 **쌓기(stack)** 다 — 나중에 올라간 것이 위 |

- ★ **이 주제의 함정은 전부 「계산값에 자국이 없다」에 있다.** 무대에 올라간 것과 객석에 있는 것의 `getComputedStyle` 이 **한 글자도 같다.**
- ★ **두 번째 함정은 「합성 이벤트로는 안 보인다」다.** 가벼운 닫기와 `Esc` 는 **진짜 입력에만** 반응한다.

```text
   객석과 무대 — 이 편의 무대 장치

   +--------------------------------------------------+
   |  최상위 레이어 (무대)                            |   <- z-index 를 안 본다
   |    [ 모달 dialog ]  [ auto 팝오버 ]  ...         |      나중에 올라간 것이 위
   +--------------------------------------------------+
   |  ::backdrop (막)                                 |
   +--------------------------------------------------+
   |  평범한 문서 (객석)                              |
   |    #맨위  z-index: 2147483647                    |   <- 여기서 아무리 높여도
   |    #보통  z-index: 1                             |      무대를 못 이긴다
   +--------------------------------------------------+
```

## 이 주제가 답하려는 질문

1. **`show()` 와 `showModal()` 은 정확히 무엇이 다른가** — 그리고 **다른 칸이 몇 개인가.**
2. **「최상위 레이어에 올라갔다」를 스크립트로 어떻게 보나** — `::backdrop` 으로 되나.
3. **가벼운 닫기(light dismiss)는 언제 일어나나** — 그리고 **막을 수 있나.**

## 이 갈래의 관측 창 — ★★ 본체는 창 ⑤(진짜 입력 주입)다

★★ **이 편의 본체는 창 ⑤ 다** — 가벼운 닫기와 `Esc` 는 **합성 이벤트로 한 칸도 안 움직여서** 다른 창으로는 원리상 답이 안 나온다. 그 다음이 창 ④(좌표 탐침)이고, 최상위 레이어는 그 창으로만 보인다.

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋에 이 주제의 창을 둘 더 얹는다.

```text
  창 1  --dump-dom             스크립트가 다 돈 뒤의 트리를 글자로
                               ★ 반만 쓴다 — open 속성은 보이는데 최상위 레이어는 안 보인다
  창 2  노드 단위 프로브        :modal · :popover-open · open · returnValue · popover
  창 3  두 번 읽기              열기 전 / 연 뒤를 같은 표의 두 칸으로
  ★ 창 4 (이 주제 고유)  좌표 탐침 — elementFromPoint 와 getBoundingClientRect
        무엇을 답하나:  '지금 무대 위에 있나 · 누가 위인가'
        왜 필요한가:    계산값에 자국이 없다. z-index 도 ::backdrop 도 거짓말을 한다
  ★★ 창 5 (이 편의 본체)  진짜 입력 주입 — CDP 로 진짜 키와 진짜 마우스를 넣는다
        무엇을 답하나:  '가벼운 닫기가 언제 일어나나 · Esc 를 막을 수 있나'
        왜 필요한가:    dispatchEvent 로 만든 click 과 keydown 은 아무것도 안 닫는다
  ★ 부적용인 창  getComputedStyle(el, '::backdrop')
        열기 전과 연 뒤가 한 글자도 같다 — 재 봤더니 같은 것이 아니라 잴 것이 없다
  ★ 못 보는 창  스크린리더의 낭독 · 실제 픽셀 · 모바일 가상 키보드
```

**쓰는 창 / 부적용인 창**

| 창 | 이 편에서 | 무엇을 답하나 |
|---|---|---|
| ① `--dump-dom` 트리 | **반만 쓴다** | `open` 속성은 보인다. 최상위 레이어·포커스는 **안 보인다** |
| ② 노드 단위 프로브 | **쓴다** | `:modal`·`:popover-open`·`returnValue`·`popover` |
| ③ 두 번 읽기 | **쓴다** | 열기 전과 연 뒤를 나란히 — (5)의 표가 전부 이 꼴이다 |
| ④ 좌표 탐침 | **쓴다** | 최상위 레이어의 쌓임 순서와 히트 테스트 |
| ⑤ **진짜 입력 주입(CDP)** | ★★ **본체** | 가벼운 닫기 · `Esc` · 사용자 활성화 |
| `getComputedStyle(…, '::backdrop')` | ★ **부적용** | 열기 전후가 같다. **잴 것이 없다** |
| `el.inert` | ★ **같은 질문을 다른 창으로 물었다** | 「막혀 있나」를 못 답해서 **`focus()` 를 던져** 물었다((6)) |
| 접근성 트리(CDP) | ★ **안 열었다** | 역할·이름은 볼 수 있지만 **이 편의 결론이 전부 포커스와 좌표**라 열 이유가 없었다 |

- ★ **창 ⑤ 가 요구하는 것** — 원격 디버깅 포트를 연 Chrome 과 `Input.dispatchKeyEvent`·`Input.dispatchMouseEvent`. 그 스크립트는 (12)에 전문이 실려 있다.

## 동작 방식

### (1) `show()` 대 `showModal()` — 갈리는 칸이 몇 개인가

**언제 쓰나** — 대화 상자를 열 때. **「모달로 열까 아닐까」를 고르는 자리.**

**던진 것** — 두 `<dialog>` 를 **한 글자도 같은 속**으로 두고 **여는 방법만** 바꿨다. 아래 (2)·(3)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-14-dialog.html -->
<!doctype html>
<meta charset="utf-8">
<title>14-dialog</title>
<style>dialog::backdrop { background: rgba(1, 2, 3, 0.5) }</style>
<button id="뒤단추">배경 단추</button>
<input id="뒤입력">
<dialog id="비모달"><button id="비1">비모달 첫 단추</button><button id="비2">둘째</button></dialog>
<dialog id="모달"><button id="모1">모달 첫 단추</button><input id="모입력"><button id="모2">둘째</button></dialog>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null || n === undefined ? String(n) : (n.id ? '#' + n.id : n.nodeName);
const 행 = (...c) => O.push(c.map((v, i) => padw(String(v), [34, 26, 26][i])).join('').replace(/ +$/, ''));

// 두 dialog 를 한 글자도 같은 속으로 두고 여는 방법만 바꾼다.
const 재기 = (d, 열기) => {
  $('뒤단추').focus();
  열기();
  const 잰것 = {
    focus: d.contains(document.activeElement) ? '안쪽 첫 요소로 간다' : 이름(document.activeElement),
    open: String(d.open),
    modal: String(d.matches(':modal')),
    backdrop: getComputedStyle(d, '::backdrop').backgroundColor,
    배경inert: String($('뒤입력').inert),
    배경포커스: (() => { $('뒤입력').focus(); return document.activeElement === $('뒤입력') ? '옮겨간다' : '거절된다'; })(),
    배경히트: 이름(document.elementFromPoint(4, 4)),
    ESC로닫히나: '아래 14-dismiss 에서 실입력으로'
  };
  d.close();
  return 잰것;
};
const 비 = 재기($('비모달'), () => $('비모달').show());
const 모 = 재기($('모달'), () => $('모달').showModal());

O.push('show() 대 showModal() — 같은 dialog, 여는 방법만 다르다');
행('무엇을', 'show()', 'showModal()');
const 키 = ['focus', 'open', 'modal', 'backdrop', '배경inert', '배경포커스', '배경히트'];
const 라벨 = { focus: '열고 난 뒤 포커스', open: 'dialog.open', modal: 'matches(":modal")',
  backdrop: '::backdrop 의 background', 배경inert: '배경 input 의 .inert',
  배경포커스: '배경 input 에 focus() 하면', 배경히트: 'elementFromPoint(4,4)' };
let 갈림 = 0;
키.forEach(k => { 행(라벨[k], 비[k], 모[k]); if (비[k] !== 모[k]) 갈림++; });
O.push('');
O.push('갈린 칸 = ' + 갈림 + ' / ' + 키.length);
O.push('  ★ show() 도 포커스를 옮긴다 — 「모달만 포커스를 가져간다」가 아니다.');
O.push('  ★ ::backdrop 의 계산값은 두 쪽이 같다. 최상위 레이어 여부를 그것으로는 못 가른다.');
O.push('  ★ 배경의 .inert 는 두 쪽 다 false 인데 모달 쪽에서만 focus() 가 거절된다.');
O.push('');

O.push('returnValue 와 close(값)');
$('모달').showModal();
O.push('  연 직후 returnValue = ' + JSON.stringify($('모달').returnValue));
$('모달').close('확인');
O.push("  close('확인') 뒤    = " + JSON.stringify($('모달').returnValue) + ' · open = ' + $('모달').open
     + ' · 포커스는 ' + 이름(document.activeElement) + ' 로 돌아온다');
$('모달').showModal();
$('모달').close();
O.push('  인자 없이 close() 뒤 = ' + JSON.stringify($('모달').returnValue) + '  <- 지우지 않는다. 옛 값이 남는다');
$('모달').returnValue = '내가 직접';
O.push('  직접 대입할 수도 있다 = ' + JSON.stringify($('모달').returnValue));
O.push('');
O.push('이미 열린 것을 또 열면');
const 잡기 = fn => { try { fn(); return '예외 없음'; } catch (e) { return e.name + ' 「' + e.message + '」'; } };
$('모달').showModal();
O.push('  모달인데 showModal() 을 또 = ' + 잡기(() => $('모달').showModal()));
O.push('  모달인데 show() 를        = ' + 잡기(() => $('모달').show()));
$('모달').close();
$('모달').show();
O.push('  비모달인데 showModal() 을 = ' + 잡기(() => $('모달').showModal()));
$('모달').close();
O.push('  닫힌 것을 close() 하면    = ' + 잡기(() => $('모달').close()));
O.push('  open 속성을 직접 쓰면     = ' + (($('모달').open = true), 'open=' + $('모달').open + ' · matches(":modal")=' + $('모달').matches(':modal')));
O.push('  ★ open 속성으로 연 것은 최상위 레이어에 안 올라간다 — show() 와도 다르다.');
$('모달').open = false;
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

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

- ★ **갈린 칸은 7 중 3 이다.** `matches(':modal')` · **배경에 `focus()` 를 던졌을 때** · `elementFromPoint`.
- ★★ **`show()` 도 포커스를 옮긴다.** 둘 다 「안쪽 첫 요소로」 갔다 — 「모달만 포커스를 가져간다」는 틀렸다. 명세가 **두 경로 모두에 같은 포커스 절차**를 붙여 놓았다.
- ★★ **`::backdrop` 의 계산값이 두 쪽에서 같다.** 비모달에는 배경막이 안 칠해지는데도 계산값은 그대로다 — **이 창으로는 못 가른다.**
- ★★ **배경 `input` 의 `.inert` 는 두 쪽 다 `false`** 인데 **모달 쪽에서만 `focus()` 가 거절된다.** 「막혀 있다」는 성질이 **어느 프로퍼티에도 안 적혀 있다.**
- **`elementFromPoint(4, 4)`** 가 모달 쪽에서 `#모달` 을 돌려준다 — 좌표 `(4, 4)` 는 dialog 밖인데도 그렇다. **모달이 열리면 배경 전체가 히트 테스트에서 빠진다.**

```text
   show() 와 showModal() — 무엇이 같고 무엇이 다른가

   같은 칸 (4)                          다른 칸 (3)
   +----------------------------+       +----------------------------+
   | open = true                |       | :modal    false / true     |
   | 포커스가 안쪽 첫 요소로     |       | 배경 focus() 옮김 / 거절됨  |
   | ::backdrop 계산값 동일      |       | elementFromPoint HTML/#모달 |
   | 배경의 .inert = false      |       |                            |
   +----------------------------+       +----------------------------+
     -> 「모달만 포커스를 뺏는다」가        -> 갈리는 것은 전부 '무대에
        여기서 깨진다                         올라갔나' 한 가지의 그림자다
```

```text
   무대에 올라가는 문은 둘뿐이다

   dialog.showModal()   ──> 최상위 레이어에 올린다   :modal = true
   el.showPopover()     ──> 최상위 레이어에 올린다   :popover-open = true
   dialog.show()        ──> 올리지 않는다            open 만 true
   dialog.open = true   ──> 올리지 않는다            포커스도 안 움직인다
```

비용 — 모달을 여는 것은 **배경 전체의 히트 테스트를 끄는 일**이다. 「가벼운 팝업」이 필요하면 `showPopover()` 쪽이 맞다((9)).

### (2) `returnValue` — 쪽지를 들고 내려온다

**언제 쓰나** — 「확인을 눌렀나 취소를 눌렀나」를 여는 쪽에 돌려줄 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-dialog.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '16,20p'
returnValue 와 close(값)
  연 직후 returnValue = ""
  close('확인') 뒤    = "확인" · open = false · 포커스는 #뒤단추 로 돌아온다
  인자 없이 close() 뒤 = "확인"  <- 지우지 않는다. 옛 값이 남는다
  직접 대입할 수도 있다 = "내가 직접"
(exit 0)
```

- **`close(값)` 이 그 문자열을 `returnValue` 에 넣는다.** 열자마자는 빈 문자열이다.
- ★ **인자 없이 `close()` 를 부르면 옛 값이 그대로 남는다** — **지우지 않는다.** 한 dialog 를 여러 번 쓰면 **지난번 답이 남아 있다.**
- **직접 대입해도 된다** — `dialog.returnValue = '...'` 는 평범한 프로퍼티다.
- **닫으면 포커스가 열기 전 자리로 돌아온다**(`#뒤단추`). 그 규칙의 전수는 (8)에 있다.

```text
   returnValue 가 흐르는 길

   열기 전   returnValue = ""        (열자마자 비워진다)
      |
      | showModal()
      v
   열린 채   사용자가 무언가를 고른다
      |
      | close('확인')                 <- 여기서만 값이 들어간다
      v
   닫힌 뒤   returnValue = "확인"     close() 로 닫으면 '확인' 이 그대로 남는다
```

### (3) 이미 열린 것을 또 열면 — 여기만 예외를 던진다

**언제 쓰나** — 「열려 있으면 안 열기」를 코드로 막으려 할 때.

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

- **모드가 어긋날 때만 예외**다 — 모달인데 `show()`, 비모달인데 `showModal()` 이 `InvalidStateError` 로 막힌다.
- **같은 모드로 또 열면 예외가 없다.** 닫힌 것을 `close()` 해도 조용하다. **「열려 있나」를 먼저 물을 필요가 거의 없다.**
- ★★ **`open` 속성을 직접 쓰면 `open` 은 `true` 가 되는데 `:modal` 은 `false` 다.** 최상위 레이어에 **안 올라간다** — `show()` 와도 다르다. 포커스도 안 움직인다((7)).

```text
   dialog 의 세 가지 '열림'

   상태                    open    :modal   최상위 레이어   포커스 이동
   ------------------------------------------------------------------
   dialog.open = true      true    false    안 올라감       없음
   dialog.show()           true    false    안 올라감       있음
   dialog.showModal()      true    true     올라감          있음

   ★ open 하나만 보면 셋이 구분되지 않는다
```

```text
   dialog 의 상태 전이 — 어긋난 문만 막힌다

        닫힘 ──show()──> 비모달 ──showModal()──> InvalidStateError 로 막힌다
          │                 │
          │              close()
          │                 v
          └─showModal()─> 모달 ──show()──> InvalidStateError 로 막힌다
                            │
                         close()
                            v
                          닫힘
```

### (4) ★ 창 ④ — 최상위 레이어는 `z-index` 와 무관하다

**언제 쓰나** — 「`z-index` 를 최대로 줬는데도 모달 뒤로 간다」일 때.

**던진 것** — 배경에 **`z-index: 2147483647`**(32비트 정수의 최댓값)을 주고, 무대에 올라가는 쪽에는 **`z-index: 1`** 만 줬다. 아래 (5)·(6)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-14-layer.html -->
<!doctype html>
<meta charset="utf-8">
<title>14-layer</title>
<style>
  body { margin: 0; font: 14px monospace }
  #맨위 { position: fixed; inset: 0; background: rgb(0, 128, 0); z-index: 2147483647 }
  #팝 { position: fixed; top: 40px; left: 40px; width: 200px; height: 80px; margin: 0;
        background: rgb(255, 255, 0); z-index: 1; border: none }
  dialog { position: fixed; top: 160px; left: 40px; width: 200px; height: 80px; margin: 0; z-index: 1 }
  dialog::backdrop { background: rgba(1, 2, 3, 0.5) }
</style>
<div id="맨위">z-index 가 최댓값인 배경</div>
<div id="팝" popover="manual">z-index 1 인 팝오버</div>
<dialog id="창"><button id="창단추">모달 안 단추</button></dialog>
<button id="배경단추">배경 단추</button>
<input id="배경입력">
<div id="막힘" inert><button id="막힌단추">inert 안의 단추</button></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null || n === undefined ? String(n) : (n.id ? '#' + n.id : n.nodeName);
const cs = el => getComputedStyle(el);

O.push('최상위 레이어는 z-index 와 무관하다 — 좌표로 던져 본다');
O.push(padw('무엇을', 40) + padw('getComputedStyle().zIndex', 26) + 'elementFromPoint 가 주는 것');
const 점 = (x, y) => 이름(document.elementFromPoint(x, y));
O.push(padw('열기 전 — 팝오버 자리 (140, 80)', 40) + padw(cs($('팝')).zIndex, 26) + 점(140, 80));
$('팝').showPopover();
O.push(padw('팝오버를 연 뒤 — 같은 자리', 40) + padw(cs($('팝')).zIndex, 26) + 점(140, 80));
O.push(padw('  그때 #맨위 의 zIndex', 40) + padw(cs($('맨위')).zIndex, 26) + '같은 자리를 #맨위 가 덮고 있는데도');
$('창').showModal();
O.push(padw('모달을 연 뒤 — 모달 자리 (140, 200)', 40) + padw(cs($('창')).zIndex, 26) + 점(140, 200));
O.push(padw('모달을 연 뒤 — 팝오버 자리 (140, 80)', 40) + padw(cs($('팝')).zIndex, 26) + 점(140, 80));
O.push(padw('모달을 연 뒤 — 빈 자리 (600, 400)', 40) + padw('—', 26) + 점(600, 400));
O.push('');
O.push('★ z-index 가 2147483647 인 #맨위 가 z-index 1 짜리에게 전부 졌다.');
O.push('★ 계산값은 한 글자도 안 바뀐다 — 「최상위 레이어에 올라갔다」는 계산값에 자국을 안 남긴다.');
O.push('★ 모달이 열리면 팝오버 자리까지 모달이 먹는다 — 배경 전체가 히트 테스트에서 빠진다.');
O.push('');

O.push('그럼 「최상위 레이어에 있나」를 무엇으로 보나');
O.push(padw('창', 34) + padw('열기 전', 24) + '연 뒤');
const 보기 = (라벨, 재기) => O.push(padw(라벨, 34) + padw(String(전[라벨]), 24) + String(재기()));
const 항목 = {
  '창.matches(":modal")': () => $('창').matches(':modal'),
  '창.open': () => $('창').open,
  '::backdrop 의 background': () => getComputedStyle($('창'), '::backdrop').backgroundColor,
  '창.checkVisibility()': () => $('창').checkVisibility(),
  '창.getBoundingClientRect().width': () => $('창').getBoundingClientRect().width,
  '팝.matches(":popover-open")': () => $('팝').matches(':popover-open'),
  '팝의 zIndex 계산값': () => cs($('팝')).zIndex
};
$('창').close(); $('팝').hidePopover();
const 전 = {};
for (const k in 항목) 전[k] = 항목[k]();
$('창').showModal(); $('팝').showPopover();
for (const k in 항목) O.push(padw(k, 34) + padw(String(전[k]), 24) + String(항목[k]()));
O.push('');
O.push('★ ::backdrop 의 계산값은 열기 전에도 같다 — 이 창으로는 못 가른다(제5의 상태).');
O.push('★ 갈리는 것은 :modal·:popover-open 과 좌표(rect·elementFromPoint) 다.');
O.push('');

O.push('배경이 막힌 것을 무엇으로 보나 — 모달이 열린 상태');
O.push('  배경입력.inert (IDL)         = ' + $('배경입력').inert);
O.push('  배경입력.matches("[inert]")  = ' + $('배경입력').matches('[inert]'));
O.push('  배경입력.checkVisibility()   = ' + $('배경입력').checkVisibility());
$('배경입력').focus();
O.push('  배경입력.focus() 뒤 activeElement = ' + 이름(document.activeElement) + '  <- 거절됐다');
let 눌림 = '(안 불림)';
$('배경단추').addEventListener('click', () => 눌림 = '배경 단추가 눌렸다');
$('배경단추').click();
O.push('  배경단추.click() (스크립트) → ' + 눌림);
O.push('  ★ 막히는 것은 사용자 입력과 포커스다. 스크립트로 부른 click 은 그대로 통과한다.');
O.push('');
O.push('진짜 inert 속성과 견주면');
O.push('  막힘.inert = ' + $('막힘').inert + ' · 막힌단추.inert = ' + $('막힌단추').inert + '  <- 자손은 false 로 답한다');
$('막힌단추').focus();
O.push('  막힌단추.focus() 뒤 activeElement = ' + 이름(document.activeElement));
O.push('  ★ .inert 는 「그 요소에 속성이 붙었나」만 답한다 — 「지금 막혀 있나」를 묻는 창이 아니다.');
O.push('  ★ 「막혀 있나」를 묻는 방법은 focus() 를 던져 보는 것뿐이다(이 문서의 창 ④).');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

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

- ★★★ **`z-index: 2147483647` 인 `#맨위` 가 `z-index: 1` 짜리에게 전부 졌다.** 팝오버를 연 뒤 같은 좌표가 `#팝` 을 돌려준다.
- ★★ **계산값은 한 글자도 안 바뀐다.** `#팝` 의 `zIndex` 는 열기 전에도 뒤에도 `1` 이다 — **「최상위 레이어에 올라갔다」는 계산값에 자국을 안 남긴다.**
- **모달을 열면 팝오버 자리까지 `#창` 이 먹는다.** 배경 전체가 히트 테스트에서 빠지므로 **빈 자리 `(600, 400)` 도 `#창`** 이다.
- ★ **`z-index` 와 최상위 레이어는 서로 다른 축이다.** 같은 축에서 다투는 것이 아니라 **판이 하나 더 있는 것**이다. 쌓임 맥락 자체의 정본은 CSS 갈래의 [22번 주제](../../languages/css/syntax/22-stacking-context-and-z-index/2-summary.md)다.

```text
   두 축은 겹치지 않는다

   최상위 레이어  ┌──────────────────────────────┐   <- 이 판에 들어오면
   (무대)         │ 나중에 올라간 것이 위        │      z-index 를 안 본다
                  │   [모달]  [팝오버]  [팝오버] │
                  └──────────────────────────────┘
   ─────────────────────────────────────────────────
   쌓임 맥락      z-index: 2147483647   #맨위          <- 여기서 아무리 높여도
   (객석)         z-index: 1            #보통             위 판을 못 넘는다
                  z-index: auto         나머지
```

```text
   같은 좌표 (140, 80) 을 세 번 물었다

   열기 전              #맨위   (z-index 2147483647 이 이긴다)
      |  팝.showPopover()
      v
   팝오버를 연 뒤       #팝     (z-index 1 인데 이긴다)
      |  창.showModal()
      v
   모달까지 연 뒤       #창     (팝오버 자리까지 모달이 먹는다)
```

비용 — 최상위 레이어에 올리는 것은 **그 요소를 쌓임 맥락 밖으로 꺼내는 일**이다. 조상의 `transform`·`filter`·`overflow: hidden` 에 **안 잘린다** — 그것이 이 표면을 쓰는 가장 큰 이유다. (**이 문서는 잘리지 않는 것을 픽셀로 확인하지는 않았다** — 좌표 탐침까지만 던졌다.)

### (5) 「최상위 레이어에 있나」를 무엇으로 보나 — ★ 부적용인 창

**언제 쓰나** — 「지금 무대 위인가」를 코드로 판정할 때.

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

- ★★★ **`::backdrop` 의 계산값이 열기 전에도 `rgba(1, 2, 3, 0.5)` 다.** 닫혀 있어서 **배경막이 그려지지도 않는데** 계산값은 선언한 그대로다.
- ★ **이것은 「재 봤더니 같았다」가 아니라 「잴 것이 없다」다.** `::backdrop` 의 계산값은 **「무엇이 선언됐나」를 말하지 「지금 무대에 있나」를 말하지 않는다.** 그 구분 자체가 이 절의 결론이다.
- **갈리는 것은 셋이다** — `:modal`·`:popover-open` 같은 **의사 클래스**, `checkVisibility()`, 그리고 **좌표**(`rect`·`elementFromPoint`).
- **`getBoundingClientRect().width` 가 `0` 에서 `234` 로 바뀐다** — 닫힌 dialog 는 상자가 없다. **대조할 것은 `234` 라는 숫자가 아니라 「0 이 아니게 된다」는 성질**이다.

```text
   '무대에 있나' 를 묻는 다섯 창 — 셋만 답한다

   창                                열기 전      연 뒤       답하나
   ------------------------------------------------------------------
   matches(':modal')                 false        true        ○
   matches(':popover-open')          false        true        ○
   checkVisibility()                 false        true        ○
   getBoundingClientRect().width     0            234         ○ (성질로만)
   getComputedStyle(…, '::backdrop') 같다         같다        ✗ 부적용
   getComputedStyle(el).zIndex       1            1           ✗ 부적용
```

```text
   제5의 상태 — 세 창이 다 정상인데 기준이 다르다

   '::backdrop 이 rgba(1,2,3,0.5) 다' 는 참이다
        |
        +-- 규칙이 시트에 담겼나      -> 담겼다
        +-- 선택자가 잡았나           -> 잡았다
        +-- 계산값이 나오나           -> 나온다
        |
        v
   그런데 '그 막이 지금 칠해지고 있나' 는 한 창도 안 물었다
   -> 계산값은 '무엇이 선언됐나' 를 말하지 '무엇이 일어나나' 를 말하지 않는다
```

### (6) 배경이 막혔다는 것을 무엇으로 보나 — ★ 창을 바꿔 물었다

**언제 쓰나** — 「모달 뒤의 버튼이 왜 안 눌리지」일 때. 그리고 그 반대로 「**왜 눌리지**」일 때.

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

- ★★ **`.inert` 가 `false` 인 채로 `focus()` 가 거절된다.** `matches('[inert]')` 도 `false` 이고 `checkVisibility()` 도 `true` 다 — **「지금 막혀 있나」를 답하는 프로퍼티가 없다.**
- ★ **그래서 같은 질문을 다른 창으로 물었다** — **`focus()` 를 던져 보고 `document.activeElement` 를 읽는 것**이 이 문서가 찾은 유일한 판정법이다.
- ★★ **스크립트로 부른 `.click()` 은 그대로 통과한다.** 막히는 것은 **사용자 입력과 포커스**이지 **디스패치가 아니다.** 「모달을 띄웠으니 뒤는 안전하다」는 **스크립트에 대해서는 거짓**이다.
- ★ **진짜 `inert` 속성도 자손에게 `false` 로 답한다** — `막힘.inert` 는 `true` 인데 그 안의 `막힌단추.inert` 는 `false` 다. **`.inert` 는 「그 요소에 속성이 붙었나」만 반영한다.** `tabindex`·`inert` 의 마크업 쪽 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **45번** 이다.

```text
   '막혀 있나' 를 묻는 네 창 — 하나만 답한다

   배경입력.inert                 false   <- 속성이 안 붙었으니 false. 맞는 답이다
   배경입력.matches('[inert]')    false   <- 같은 것을 선택자로 물은 것뿐
   배경입력.checkVisibility()     true    <- 보이는 것은 사실이다
   배경입력.focus() -> activeElement       <- ★ 이것만 '거절됐다' 를 말한다
```

```text
   모달이 막는 것과 안 막는 것

   막는다                          안 막는다
   +------------------------+      +------------------------------+
   | 사용자의 클릭          |      | el.click()  (스크립트 호출)  |
   | 사용자의 탭 이동       |      | el.dispatchEvent(...)        |
   | el.focus()             |      | el.textContent = ...         |
   | 히트 테스트            |      | 읽기 전부                    |
   +------------------------+      +------------------------------+
     -> '보안 장치' 가 아니라 '입력 장치' 다
```

### (7) 초기 포커스가 어디로 가나 — ★ 이 편의 급소

**언제 쓰나** — 열자마자 커서가 엉뚱한 데 가 있을 때. **전수로 던졌다.**

**던진 것** — 속을 조금씩 바꾼 dialog 여덟과 팝오버 셋을 **같은 자리에서 같은 방법으로** 열었다. 아래 (8)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-14-focus.html -->
<!doctype html>
<meta charset="utf-8">
<title>14-focus</title>
<button id="연놈">열기를 부른 자리</button>
<dialog id="ㄱ"><p>글만 있다</p></dialog>
<dialog id="ㄴ"><button id="ㄴ1">첫 단추</button><button id="ㄴ2">둘째</button></dialog>
<dialog id="ㄷ"><button id="ㄷ1">첫 단추</button><input id="ㄷ2" autofocus><button id="ㄷ3">셋째</button></dialog>
<dialog id="ㄹ" autofocus><button id="ㄹ1">첫 단추</button></dialog>
<dialog id="ㅁ"><button id="ㅁ1" disabled>못 누르는 단추</button><button id="ㅁ2">누를 수 있는 단추</button></dialog>
<dialog id="ㅂ"><div id="ㅂ1" tabindex="-1">tabindex="-1" 인 div</div><button id="ㅂ2">단추</button></dialog>
<dialog id="ㅅ"><button id="ㅅ1" style="display:none">숨은 단추</button><button id="ㅅ2">보이는 단추</button></dialog>
<dialog id="ㅇ"><div id="ㅇ1" tabindex="0">tabindex="0" 인 div</div><button id="ㅇ2">단추</button></dialog>
<div id="팝ㄱ" popover="auto"><p>팝오버인데 글만 있다</p></div>
<div id="팝ㄴ" popover="auto"><button id="팝ㄴ1">팝오버 첫 단추</button></div>
<div id="팝ㄷ" popover="auto"><button id="팝ㄷ1">첫 단추</button><button id="팝ㄷ2" autofocus>autofocus 단추</button></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null || n === undefined ? String(n) : (n.id ? '#' + n.id : n.nodeName);
const 재기 = (id, 여는법, 설명) => {
  $('연놈').focus();
  const d = $(id);
  여는법(d);
  const a = document.activeElement;
  const 어디 = a === d ? '★ dialog·popover 자신' : (d.contains(a) ? 이름(a) : '★ 바깥 ' + 이름(a));
  if (d.close) d.close(); else d.hidePopover();
  O.push(padw(설명, 46) + 어디);
};
O.push('초기 포커스가 어디로 가나 — 전수');
O.push(padw('무엇을 어떻게 열었나', 46) + 'document.activeElement');
재기('ㄱ', d => d.showModal(), 'showModal · 포커스 받을 것이 하나도 없다');
재기('ㄴ', d => d.showModal(), 'showModal · 단추 둘, autofocus 없음');
재기('ㄴ', d => d.show(), 'show · 단추 둘, autofocus 없음');
재기('ㄷ', d => d.showModal(), 'showModal · 둘째 요소에 autofocus');
재기('ㄹ', d => d.showModal(), 'showModal · dialog 자신에 autofocus');
재기('ㅁ', d => d.showModal(), 'showModal · 첫 단추가 disabled');
재기('ㅂ', d => d.showModal(), 'showModal · 첫 요소가 tabindex="-1"');
재기('ㅅ', d => d.showModal(), 'showModal · 첫 단추가 display:none');
재기('ㅇ', d => d.showModal(), 'showModal · 첫 요소가 tabindex="0"');
재기('ㄱ', d => { d.open = true; }, 'open 속성만 true 로 (열기 메서드를 안 쓴다)');
재기('팝ㄱ', d => d.showPopover(), 'showPopover · 포커스 받을 것이 없다');
재기('팝ㄴ', d => d.showPopover(), 'showPopover · 단추 하나, autofocus 없음');
재기('팝ㄷ', d => d.showPopover(), 'showPopover · 둘째 단추에 autofocus');
O.push('');
O.push('★ dialog 는 autofocus 가 없어도 안쪽 첫 포커스 가능 요소로 간다 — show() 도 그렇다.');
O.push('★ popover 는 autofocus 가 없으면 포커스를 안 옮긴다 — 여기가 dialog 와 갈리는 급소다.');
O.push('★ disabled·display:none 은 「포커스 가능」에서 빠져 다음 것으로 넘어간다.');
O.push('★ 그런데 tabindex="-1" 은 안 빠진다 — 탭 순서에서만 빠질 뿐 포커스는 받는다(#ㅂ1 이 그 줄이다).');
O.push('★ dialog 자신의 autofocus 는 이 판에서 무시됐다 — 안쪽 첫 단추로 갔다(#ㄹ1). 구현 쪽 관찰이다.');
O.push('★ open 속성만 켜면 포커스가 안 움직인다. 최상위 레이어에도 안 올라간다.');
O.push('');
O.push('닫으면 포커스가 어디로 돌아오나');
$('연놈').focus();
$('ㄴ').showModal();
O.push('  열기 전 포커스 = #연놈 · 연 뒤 = ' + 이름(document.activeElement));
$('ㄴ').close();
O.push('  닫은 뒤        = ' + 이름(document.activeElement) + '  <- 열기 전 자리로 돌아온다');
$('연놈').focus();
$('ㄴ').showModal();
$('ㄴ2').focus();
$('ㄴ').close();
O.push('  안에서 포커스를 옮겨 두고 닫아도 = ' + 이름(document.activeElement));
const 사라질 = document.createElement('button');
document.body.appendChild(사라질); 사라질.id = '사라질'; 사라질.textContent = '곧 사라질 단추';
사라질.focus();
$('ㄴ').showModal();
사라질.remove();
$('ㄴ').close();
O.push('  돌아갈 자리가 사라졌으면       = ' + 이름(document.activeElement));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
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

- ★★ **`dialog` 는 `autofocus` 가 없어도 안쪽 첫 포커스 가능 요소로 간다.** `show()` 도 마찬가지다.
- ★★★ **`popover` 는 `autofocus` 가 없으면 포커스를 아예 안 옮긴다.** 바깥에 그대로 있다 — **여기가 둘이 갈리는 급소다.** 팝오버는 「떠 있는 레이어」일 뿐 「대화 상자」가 아니라서 그렇다.
- **`autofocus` 가 있으면 그것이 이긴다** — 첫 요소가 아니라 `autofocus` 가 붙은 것으로 간다.
- **`disabled`·`display: none` 은 「포커스 가능」에서 빠져** 다음 것으로 넘어간다.
- ★ **그런데 `tabindex="-1"` 은 안 빠진다.** 탭 순서에서만 빠질 뿐 **포커스는 받는다** — `#ㅂ1` 이 그 줄이다.
- ★ **`dialog` 자신에 붙인 `autofocus` 는 이 판에서 무시됐다**(안쪽 첫 단추로 갔다). **구현 쪽 관찰이지 명세 보장이 아니다.**
- **포커스 받을 것이 하나도 없으면 `dialog` 자신이 포커스를 받는다.**
- **`open` 속성만 켜면 아무 일도 안 난다** — 포커스도 최상위 레이어도 그대로다.

```text
   초기 포커스 결정 순서 — dialog 쪽

   dialog 를 열었다
        |
        +-- 안쪽에 autofocus 가 있나?  --예--> 그것으로 간다        (#ㄷ2)
        |
        +-- 포커스 가능한 자손이 있나? --예--> 첫 번째로 간다       (#ㄴ1 · #ㅁ2 · #ㅅ2)
        |                                      ★ tabindex="-1" 도 '가능' 이다 (#ㅂ1)
        |
        +-- 없다                       ------> dialog 자신이 받는다

   ★ show() 와 showModal() 이 이 흐름을 똑같이 탄다
```

```text
   dialog 와 popover 가 갈리는 한 칸

   autofocus 가 없을 때
   +-------------------------+      +-------------------------+
   | dialog.showModal()      |      | el.showPopover()        |
   |   -> 안쪽 첫 단추로     |      |   -> 아무 데도 안 간다  |
   |      (#ㄴ1)             |      |      (바깥 #연놈 그대로) |
   +-------------------------+      +-------------------------+
     -> 팝오버에 입력이 있으면 autofocus 를 직접 달아야 한다
```

```text
   '포커스 가능' 에서 빠지는 것과 안 빠지는 것

   빠진다                     안 빠진다
   disabled                   tabindex="-1"   <- 탭으로는 못 가는데 focus() 는 받는다
   display: none              tabindex="0"
                              보통 단추·입력
```

### (8) 닫으면 포커스가 어디로 돌아오나

**언제 쓰나** — 모달을 닫았는데 커서가 사라졌을 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-focus.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '24,28p'
닫으면 포커스가 어디로 돌아오나
  열기 전 포커스 = #연놈 · 연 뒤 = #ㄴ1
  닫은 뒤        = #연놈  <- 열기 전 자리로 돌아온다
  안에서 포커스를 옮겨 두고 닫아도 = #연놈
  돌아갈 자리가 사라졌으면       = #ㄴ1
(exit 0)
```

- **열기 전 자리로 돌아온다.** `#연놈` 에 포커스가 있었으면 닫은 뒤 `#연놈` 이다.
- ★ **안에서 포커스를 옮겨 둬도 돌아가는 자리는 그대로다** — 브라우저가 **열 때 기억해 둔 자리**로 되돌린다.
- ★★ **돌아갈 자리가 사라졌으면 안 돌아간다.** 그 단추를 `remove()` 한 뒤 닫았더니 **`#ㄴ1`**(닫힌 dialog 안의 단추)에 포커스가 남았다. **목록에서 항목을 지우는 모달**이 정확히 이 모양이라 실무에서 자주 만난다.

```text
   포커스 되돌리기 — 세 판

   ① 보통                    #연놈 -> (#ㄴ1) -> #연놈       돌아온다
   ② 안에서 옮겨 두고        #연놈 -> (#ㄴ2) -> #연놈       그래도 돌아온다
   ③ 돌아갈 자리를 지우면    #사라질 -> (#ㄴ1) -> #ㄴ1      ★ 안 돌아온다

   ★ ③ 이 실무의 모양이다 — '이 항목을 지울까요' 모달
```

### (9) `popover` 의 표면 — 속성 하나와 메서드 셋

**언제 쓰나** — 드롭다운·툴팁·메뉴를 만들 때.

**던진 것** — `auto`·`manual`·`hint` 셋과 DOM 으로 중첩한 한 쌍. 아래 (10)·(11)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-14-popover.html -->
<!doctype html>
<meta charset="utf-8">
<title>14-popover</title>
<style>[popover] { margin: 0; top: 10px; left: 10px; width: 180px; height: 50px; background: rgb(255, 255, 0) }</style>
<div id="오토" popover="auto">auto 팝오버</div>
<div id="매뉴얼" popover="manual">manual 팝오버</div>
<div id="힌트" popover="hint">hint 팝오버</div>
<div id="바깥" popover="auto">바깥<div id="안쪽" popover="auto">DOM 으로 중첩된 안쪽</div></div>
<div id="떨어진" popover="auto">떨어져 있는 auto</div>
<div id="막는것" popover="auto">beforetoggle 을 막는 것</div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 잡기 = fn => { try { return '예외 없음 · 돌려준 값 = ' + String(fn()); } catch (e) { return e.name + ' 「' + e.message + '」'; } };
const 열림 = id => $(id).matches(':popover-open');
const 상태 = (...ids) => ids.map(id => id + '=' + 열림(id)).join(' · ');
const 사건 = [];
for (const id of ['오토', '매뉴얼', '힌트', '바깥', '안쪽', '떨어진', '막는것']) {
  $(id).addEventListener('beforetoggle', e => 사건.push(id + ' beforetoggle ' + e.oldState + '->' + e.newState + ' (cancelable=' + e.cancelable + ')'));
  $(id).addEventListener('toggle', e => 사건.push(id + ' toggle ' + e.oldState + '->' + e.newState));
}
const 비우기 = () => { const v = 사건.slice(); 사건.length = 0; return v; };

O.push('표면 — 속성과 메서드');
O.push(padw('무엇을', 42) + '값');
O.push(padw('$("오토").popover', 42) + JSON.stringify($('오토').popover));
O.push(padw('$("힌트").popover', 42) + JSON.stringify($('힌트').popover));
const 모르는 = document.createElement('div');
모르는.setAttribute('popover', 'zzznope'); document.body.appendChild(모르는);
O.push(padw('popover="zzznope" 의 .popover', 42) + JSON.stringify(모르는.popover) + '   <- 모르는 값은 manual 로 떨어진다');
const 빈것 = document.createElement('div');
빈것.setAttribute('popover', ''); document.body.appendChild(빈것);
O.push(padw('popover="" 의 .popover', 42) + JSON.stringify(빈것.popover) + '   <- 빈 값은 auto 다');
O.push(padw('popover 속성이 없는 div 의 .popover', 42) + String(document.createElement('div').popover));
O.push('');

O.push('여닫기 — 돌려주는 값과 예외');
O.push('  showPopover()                  = ' + 잡기(() => $('오토').showPopover()) + ' · 열림=' + 열림('오토'));
O.push('  이미 열린 것에 또 showPopover() = ' + 잡기(() => $('오토').showPopover()) + ' · 열림=' + 열림('오토'));
O.push('  togglePopover()                = ' + 잡기(() => $('오토').togglePopover()) + ' · 열림=' + 열림('오토'));
O.push('  닫힌 것에 hidePopover()        = ' + 잡기(() => $('오토').hidePopover()) + ' · 열림=' + 열림('오토'));
O.push('  togglePopover(true)            = ' + 잡기(() => $('오토').togglePopover(true)) + ' · 열림=' + 열림('오토'));
O.push('  togglePopover(true) 를 또       = ' + 잡기(() => $('오토').togglePopover(true)) + ' · 열림=' + 열림('오토'));
O.push('  popover 속성이 없는 div 에 showPopover() = ' + 잡기(() => document.createElement('div').showPopover()));
$('오토').hidePopover(); 비우기();
O.push('  ★ 예외를 던지는 것은 「팝오버가 아닌 요소에 부른 것」 하나뿐이다. 나머지는 전부 조용하다.');
O.push('');

O.push('auto 끼리는 서로 밀어낸다 — manual 과 hint 는 어떤가');
$('오토').showPopover(); $('매뉴얼').showPopover(); $('힌트').showPopover();
O.push('  셋을 차례로 열면        ' + 상태('오토', '매뉴얼', '힌트'));
$('떨어진').showPopover();
O.push('  다른 auto 를 하나 더 열면 ' + 상태('오토', '매뉴얼', '힌트', '떨어진'));
O.push('  ★ 살아남은 것은 manual 하나다 — hint 는 auto 와 함께 밀려났다.');
$('떨어진').hidePopover(); $('매뉴얼').hidePopover(); $('힌트').hidePopover(); 비우기();
O.push('');

O.push('DOM 으로 중첩하면 안 밀린다');
$('바깥').showPopover(); $('안쪽').showPopover();
O.push('  바깥을 열고 안쪽을 열면   ' + 상태('바깥', '안쪽'));
$('떨어진').showPopover();
O.push('  떨어진 auto 를 열면       ' + 상태('바깥', '안쪽', '떨어진'));
O.push('  ★ 조상-자손 사이면 「이어진 것」으로 쳐서 같이 열려 있는다.');
$('떨어진').hidePopover(); 비우기();
O.push('');

O.push('beforetoggle 을 막으면');
const r = $('막는것').addEventListener('beforetoggle', e => { if (e.newState === 'open') e.preventDefault(); });
$('막는것').showPopover();
O.push('  showPopover() 뒤 열렸나 = ' + 열림('막는것'));
O.push('  이번 tick 의 사건       = ' + JSON.stringify(비우기()));
O.push('  ★ 여는 쪽 beforetoggle 만 cancelable 이다. 닫는 쪽은 못 막는다.');
O.push('');

O.push('beforetoggle 은 동기, toggle 은 나중이다');
const 새것 = document.createElement('div');
새것.setAttribute('popover', 'manual');
새것.textContent = '이 절만을 위한 새 팝오버';
document.body.appendChild(새것);
const 새사건 = [];
새것.addEventListener('beforetoggle', e => 새사건.push('beforetoggle ' + e.oldState + '->' + e.newState));
새것.addEventListener('toggle', e => 새사건.push('toggle ' + e.oldState + '->' + e.newState));
새것.showPopover();
O.push('  showPopover() 직후 (같은 tick) = ' + JSON.stringify(새사건));
새것.hidePopover();
새것.showPopover();
O.push('  닫았다 다시 연 직후            = ' + JSON.stringify(새사건));
setTimeout(() => {
  O.push('  한 tick 뒤                     = ' + JSON.stringify(새사건));
  O.push('  ★ beforetoggle 은 그 자리에서 세 번 다 왔는데 toggle 은 한 번만, 그것도 나중에 왔다.');
  O.push('  ★ toggle 은 「그 tick 이 끝났을 때의 상태」를 한 번 알린다 — 중간 상태를 놓친다.');
  document.body.appendChild(Object.assign(document.createElement('script'),
    {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
}, 0);
</script>
```

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

- **`popover` 속성이 IDL 프로퍼티로 그대로 반영된다** — [06번 주제](../06-attribute-vs-property/2-summary.md)의 반영 규칙 그대로다.
- ★ **모르는 값은 `manual` 로 떨어진다**(`popover="zzznope"` → `"manual"`). **빈 값은 `auto`** 다. 예외도 경고도 없다 — **열거값의 조용한 기본값**이고 [06번 주제](../06-attribute-vs-property/2-summary.md)의 그 모양이다.
- ★ **오타가 「안 열림」이 아니라 「가벼운 닫기가 안 되는 팝오버」로 나타난다.** 화면에는 뜨는데 **바깥을 눌러도 안 닫힌다** — 가장 알아채기 어려운 증상이다.

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

- **예외를 던지는 것은 「팝오버가 아닌 요소에 부른 것」 하나뿐**이다. 나머지는 전부 조용하다.
- **이미 열린 것에 또 `showPopover()` 를 불러도 조용하다.** 닫힌 것에 `hidePopover()` 도 조용하다.
- ★ **`togglePopover()` 는 「지금 열려 있나」를 불리언으로 돌려준다.** `showPopover()`·`hidePopover()` 는 `undefined` 다.
- ★ **`togglePopover(true)` 는 「열어 둬라」다** — 토글이 아니라 **강제**다. 두 번 불러도 열린 채다.

```text
   popover 네 메서드가 돌려주는 것

   showPopover()        -> undefined     항상 열어 둔다
   hidePopover()        -> undefined     항상 닫아 둔다
   togglePopover()      -> 열렸나(불리언)  뒤집는다
   togglePopover(true)  -> 열렸나(불리언)  '열어 둬라' (강제)
   togglePopover(false) -> 열렸나(불리언)  '닫아 둬라' (강제)
```

```text
   popover 속성 값 세 가지

   auto     서로 밀어낸다 · 바깥 클릭과 Esc 로 닫힌다      (드롭다운·메뉴)
   manual   아무것도 안 닫아 준다 · 스크립트로만          (토스트·붙박이 패널)
   hint     auto 가 열리면 밀려난다 · 바깥 클릭에 닫힌다  (툴팁)

   ★ 모르는 값 -> manual · 빈 값 -> auto
```

### (10) `auto` 끼리는 서로 밀어낸다 — 중첩은 예외다

**언제 쓰나** — 메뉴 안에 서브메뉴를 둘 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-popover.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '19,27p'
auto 끼리는 서로 밀어낸다 — manual 과 hint 는 어떤가
  셋을 차례로 열면        오토=true · 매뉴얼=true · 힌트=true
  다른 auto 를 하나 더 열면 오토=false · 매뉴얼=true · 힌트=false · 떨어진=true
  ★ 살아남은 것은 manual 하나다 — hint 는 auto 와 함께 밀려났다.

DOM 으로 중첩하면 안 밀린다
  바깥을 열고 안쪽을 열면   바깥=true · 안쪽=true
  떨어진 auto 를 열면       바깥=false · 안쪽=false · 떨어진=true
  ★ 조상-자손 사이면 「이어진 것」으로 쳐서 같이 열려 있는다.
(exit 0)
```

- **`auto` 를 새로 열면 다른 `auto` 가 닫힌다.** 한 번에 하나만 떠 있게 하는 것이 `auto` 의 뜻이다.
- ★ **살아남은 것은 `manual` 하나다** — **`hint` 는 `auto` 와 함께 밀려났다.** 「`hint` 는 독립이다」가 아니다.
- ★★ **DOM 으로 중첩하면 안 밀린다.** 바깥 팝오버 **안에** 들어 있는 팝오버는 「**이어진 것**」으로 쳐서 같이 열려 있는다. 서브메뉴가 이 규칙으로 산다.
- ★ **떨어져 있는 `auto` 를 열면 그 사슬이 통째로 닫힌다** — 바깥과 안쪽이 한꺼번에 사라진다.

```text
   auto 끼리 밀어내기 — 전/후

   전                                   후 (떨어진 auto 를 하나 더 열면)
   +----------------------------+       +----------------------------+
   | 오토    auto      열림     |       | 오토    auto      닫힘 ✗   |
   | 매뉴얼  manual    열림     |       | 매뉴얼  manual    열림     |
   | 힌트    hint      열림     |       | 힌트    hint      닫힘 ✗   |
   +----------------------------+       +----------------------------+
     -> 살아남는 것은 manual 하나다
```

```text
   중첩은 사슬로 이어진다

   DOM 이 이렇게 생겼으면                최상위 레이어는 이렇게 쌓인다
   <div id=바깥 popover=auto>              [바깥]        (아래)
     <div id=안쪽 popover=auto>            [안쪽]        (위)
   </div>
                                         둘 다 열려 있다 — 조상-자손이라서
   떨어져 있는 #떨어진 을 열면
                                         [떨어진]      바깥·안쪽은 함께 닫힌다
```

### (11) `beforetoggle` 은 동기, `toggle` 은 나중이다

**언제 쓰나** — 「열리기 직전에 데이터를 채우자」·「열린 뒤에 애니메이션을 걸자」일 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-14-popover.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '29,32p'
beforetoggle 을 막으면
  showPopover() 뒤 열렸나 = false
  이번 tick 의 사건       = ["막는것 beforetoggle closed->open (cancelable=true)"]
  ★ 여는 쪽 beforetoggle 만 cancelable 이다. 닫는 쪽은 못 막는다.
(exit 0)
```

- **여는 쪽 `beforetoggle` 은 `cancelable: true`** 라 `preventDefault()` 로 **열기를 막을 수 있다.**
- ★★ **닫는 쪽은 `cancelable: false` 라 못 막는다**((12)의 ⑨ 가 그 실측이다). **「닫지 마세요」는 원리상 안 된다.**

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

- **`beforetoggle` 은 그 자리에서** 세 번 다 왔다 — 동기다.
- ★★ **`toggle` 은 태스크로 미뤄지고, 게다가 한 번만 왔다.** 같은 tick 안에서 열고 닫고 다시 열었는데 **`closed->open` 하나**만 남았다.
- ★ **`toggle` 은 「그 tick 이 끝났을 때의 상태」를 알린다** — **중간 상태를 놓친다.** 여닫기를 `toggle` 로 세면 **수가 안 맞는다.**

```text
   같은 tick 안에서 열고·닫고·다시 열면

   시간 ────────────────────────────────────────────>
   showPopover()   hidePopover()   showPopover()      (tick 끝)
        |               |               |                 |
   before(c->o)   before(o->c)    before(c->o)            |
                                                     toggle(c->o)   <- 한 번뿐
   ★ before 는 3번, toggle 은 1번. toggle 로 여닫기를 세면 안 된다
```

### (12) ★★ 창 ⑤ — 가벼운 닫기는 진짜 입력에만 반응한다

**언제 쓰나** — 「바깥을 눌러도 안 닫힌다」·「`Esc` 를 막고 싶다」일 때.

**왜 창을 바꿨나** — 앞의 절들은 전부 `--dump-dom` 으로 봤다. 그런데 **가벼운 닫기와 `Esc` 는 `dispatchEvent` 로 만든 이벤트에 반응하지 않는다.** 그래서 **CDP 로 원격 디버깅에 붙어 진짜 키와 진짜 마우스를 넣었다.**

```python
# wa12b-cdp.py
#!/usr/bin/env python3
"""CDP 로 실제 키·마우스 입력을 넣는다 — 가벼운 닫기는 합성 이벤트로 안 난다.
페이지가 window.__단계 배열로 할 일을 적어 두면 순서대로 넣고 window.__결과() 를 읽는다.
  ['js',  '<식>']          페이지 안에서 식을 돌린다
  ['key', 키, 코드, 번호]  진짜 키 입력 (Input.dispatchKeyEvent)
  ['at',  '<선택자>']      그 요소의 한가운데를 진짜로 클릭한다
  ['xy',  x, y]            그 좌표를 진짜로 클릭한다
사용: wa12b-cdp.py <html파일>
"""
import json, subprocess, time, urllib.request, sys, websocket, os, shutil, random

PORT = 19800 + random.randint(10, 89)
PROF = "/tmp/wa12b-cdp-%d" % PORT
shutil.rmtree(PROF, ignore_errors=True)
p = subprocess.Popen(["google-chrome", "--headless", "--disable-gpu", "--no-sandbox",
    "--window-size=1000,800", "--remote-debugging-port=%d" % PORT,
    "--user-data-dir=" + PROF, "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    pages = []
    for _ in range(40):
        time.sleep(0.25)
        try:
            tabs = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json/list" % PORT))
            pages = [t for t in tabs if t["type"] == "page"]
            if pages:
                break
        except Exception:
            pass
    ws = websocket.create_connection(pages[0]["webSocketDebuggerUrl"], suppress_origin=True)
    mid = [0]
    def send(m, prm=None):
        mid[0] += 1
        ws.send(json.dumps({"id": mid[0], "method": m, "params": prm or {}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == mid[0]:
                return r
    def ev(expr):
        r = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        res = r.get("result", {})
        if "exceptionDetails" in res:
            return "«" + res["exceptionDetails"].get("text", "?") + "»"
        return res.get("result", {}).get("value")
    def click(x, y):
        for t in ("mousePressed", "mouseReleased"):
            send("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left",
                 "clickCount": 1, "buttons": 1 if t == "mousePressed" else 0})
    send("Page.enable"); send("Runtime.enable")
    send("Page.navigate", {"url": "file://" + os.path.abspath(sys.argv[1])})
    time.sleep(1.0)
    for st in json.loads(ev("JSON.stringify(window.__단계 || [])")):
        종 = st[0]
        if 종 == "js":
            ev(st[1])
        elif 종 == "key":
            for t in ("keyDown", "keyUp"):
                send("Input.dispatchKeyEvent", {"type": t, "key": st[1], "code": st[2],
                     "windowsVirtualKeyCode": st[3], "nativeVirtualKeyCode": st[3]})
        elif 종 == "at":
            xy = ev("(r => r ? [r.left + r.width / 2, r.top + r.height / 2] : null)"
                    "(document.querySelector(%s).getBoundingClientRect())" % json.dumps(st[1]))
            click(xy[0], xy[1])
        elif 종 == "xy":
            click(st[1], st[2])
        time.sleep(0.12)
    time.sleep(0.3)
    print(ev("window.__결과()"))
finally:
    p.terminate(); p.wait(); shutil.rmtree(PROF, ignore_errors=True)
```

**던진 것**

```html
<!-- wa12b-14-dismiss.html -->
<!doctype html>
<meta charset="utf-8">
<title>14-dismiss</title>
<style>
  body { margin: 0; font: 14px monospace }
  #빈터 { height: 700px; background: rgb(235, 235, 235) }
  [popover] { margin: 0; border: none; position: fixed }
  #오토 { top: 20px; left: 20px; width: 300px; height: 200px; background: rgb(255, 255, 0) }
  #안쪽 { top: 60px; left: 60px; width: 120px; height: 40px; background: rgb(0, 255, 255) }
  #매뉴얼 { top: 20px; left: 400px; width: 150px; height: 40px; background: rgb(200, 255, 200) }
  #힌트 { top: 80px; left: 400px; width: 150px; height: 40px; background: rgb(255, 200, 200) }
  #못막음 { top: 140px; left: 400px; width: 150px; height: 40px; background: rgb(220, 220, 255) }
  dialog { margin: 0; top: 300px; left: 20px; width: 200px; height: 60px }
</style>
<div id="빈터">빈 터 — (700, 600) 을 진짜로 클릭한다</div>
<div id="오토" popover="auto">바깥 auto<div id="안쪽" popover="auto">중첩된 auto</div></div>
<div id="매뉴얼" popover="manual">manual</div>
<div id="힌트" popover="hint">hint</div>
<div id="못막음" popover="auto">닫기를 막아 보는 auto</div>
<dialog id="모달"><button id="모달단추">모달 단추</button></dialog>
<dialog id="비모달"><button id="비모달단추">비모달 단추</button></dialog>
<dialog id="버팀"><button id="버팀단추">취소를 막는 모달</button></dialog>
<script>
const 줄 = [];
const $ = id => document.getElementById(id);
const 열림 = id => $(id).matches(':popover-open');
const 적기 = s => 줄.push(s);
const 팝 = () => '   ' + ['오토', '안쪽', '매뉴얼', '힌트'].map(id => id + '=' + 열림(id)).join(' ');
const 누구 = () => (document.activeElement.id || document.activeElement.tagName);
$('모달').addEventListener('cancel', e => 적기('     [모달 cancel · cancelable=' + e.cancelable + ']'));
$('모달').addEventListener('close', () => 적기('     [모달 close · returnValue=' + JSON.stringify($('모달').returnValue) + ']'));
$('비모달').addEventListener('cancel', e => 적기('     [비모달 cancel · cancelable=' + e.cancelable + ']'));
$('비모달').addEventListener('close', () => 적기('     [비모달 close]'));
$('버팀').addEventListener('cancel', e => { 적기('     [버팀 cancel · cancelable=' + e.cancelable + ' -> preventDefault 를 부른다]'); e.preventDefault(); });
$('버팀').addEventListener('close', () => 적기('     [버팀 close]'));
$('못막음').addEventListener('beforetoggle', e => {
  if (e.newState === 'closed') { 적기('     [못막음 닫기 beforetoggle · cancelable=' + e.cancelable + ' -> preventDefault 를 부른다]'); e.preventDefault(); }
});
window.__단계 = [
  ['js', '적기("① 네 가지 팝오버를 모두 연다"); $("오토").showPopover(); $("안쪽").showPopover(); $("매뉴얼").showPopover(); $("힌트").showPopover(); 적기(팝());'],
  ['xy', 120, 80],
  ['js', '적기("② 중첩된 안쪽 팝오버 위 (120, 80) 를 진짜로 클릭"); 적기(팝());'],
  ['xy', 280, 200],
  ['js', '적기("③ 바깥 auto 팝오버의 빈 자리 (280, 200) 를 진짜로 클릭"); 적기(팝());'],
  ['xy', 700, 600],
  ['js', '적기("④ 팝오버 바깥 빈 터 (700, 600) 를 진짜로 클릭"); 적기(팝());'],
  ['js', '적기("⑤ auto 둘을 다시 연다"); $("오토").showPopover(); $("안쪽").showPopover(); 적기(팝());'],
  ['key', 'Escape', 'Escape', 27],
  ['js', '적기("⑥ Esc 한 번"); 적기(팝());'],
  ['key', 'Escape', 'Escape', 27],
  ['js', '적기("⑦ Esc 한 번 더"); 적기(팝());'],
  ['key', 'Escape', 'Escape', 27],
  ['js', '적기("⑧ Esc 를 또 (manual 만 남아 있다)"); 적기(팝()); $("매뉴얼").hidePopover();'],
  ['js', '적기(""); 적기("⑨ 닫기를 beforetoggle 로 막아 본다"); $("못막음").showPopover(); 적기("   못막음 열림=" + 열림("못막음"));'],
  ['key', 'Escape', 'Escape', 27],
  ['js', '적기("   Esc 뒤 못막음 열림=" + 열림("못막음")); $("못막음").hidePopover();'],
  ['js', '적기(""); 적기("⑩ 모달 dialog 를 연다"); $("모달").showModal(); 적기("   open=" + $("모달").open + " · activeElement=" + 누구());'],
  ['xy', 700, 600],
  ['js', '적기("⑪ 배경 (700, 600) 을 진짜로 클릭"); 적기("   open=" + $("모달").open + " · activeElement=" + 누구());'],
  ['key', 'Escape', 'Escape', 27],
  ['js', '적기("⑫ Esc"); 적기("   open=" + $("모달").open + " · activeElement=" + 누구());'],
  ['js', '적기(""); 적기("⑬ show() 로 연 비모달에 Esc"); $("비모달").show(); 적기("   open=" + $("비모달").open);'],
  ['key', 'Escape', 'Escape', 27],
  ['js', '적기("   Esc 뒤 open=" + $("비모달").open); if ($("비모달").open) $("비모달").close();'],
  ['js', '적기(""); 적기("⑭ cancel 을 preventDefault 로 막는 모달 — 앞의 모달이 활성화를 이미 써 버린 뒤"); $("버팀").showModal(); 적기("   open=" + $("버팀").open + " · navigator.userActivation.isActive=" + navigator.userActivation.isActive);'],
  ['key', 'Escape', 'Escape', 27],
  ['js', '적기("   Esc 뒤 open=" + $("버팀").open);'],
  ['js', '적기(""); 적기("⑮ 같은 모달 — 새로 진짜 클릭을 하고 그 활성화 위에서 연다");'],
  ['xy', 700, 600],
  ['js', '적기("   클릭 뒤 isActive=" + navigator.userActivation.isActive); $("버팀").showModal(); 적기("   open=" + $("버팀").open);'],
  ['key', 'Escape', 'Escape', 27],
  ['js', '적기("   Esc 한 번 뒤 open=" + $("버팀").open);'],
  ['key', 'Escape', 'Escape', 27],
  ['js', '적기("   Esc 두 번째 뒤 open=" + $("버팀").open);']
];
window.__결과 = () => 줄.join('\n');
</script>
```

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

- **② 중첩된 안쪽을 클릭하면 둘 다 살아 있다.** 그런데 **`hint` 는 이때 닫혔다** — 팝오버 바깥이 아니라 **다른 팝오버 안**을 눌러도 `hint` 는 물러난다.
- ★★ **③ 바깥 팝오버의 빈 자리를 클릭하면 안쪽만 닫힌다.** 클릭 지점의 **조상 사슬에 없는** 팝오버가 닫힌다 — **한 겹씩** 벗겨진다.
- **④ 완전히 바깥을 클릭하면 `auto` 가 전부 닫힌다.** `manual` 은 남는다.
- ★★ **⑥⑦ `Esc` 도 한 겹씩** 벗긴다 — 안쪽부터 하나씩이다.
- **⑧ `manual` 은 `Esc` 에도 안 닫힌다.** 스크립트로만 닫힌다.
- ★★★ **⑨ 닫는 쪽 `beforetoggle` 은 `cancelable=false` 라 `preventDefault()` 가 아무 일도 안 한다.** 팝오버는 **「닫히지 않겠다」를 선언할 수 없다.**

```text
   가벼운 닫기 전수 — 무엇이 무엇을 닫나

   방아쇠                       auto   중첩 안쪽   manual   hint   모달 dialog   비모달
   ---------------------------------------------------------------------------------
   완전히 바깥을 클릭           닫힘   닫힘        남음     닫힘   남음          남음
   바깥 팝오버의 빈 자리 클릭   남음   닫힘        남음     닫힘   —             —
   그 팝오버 안을 클릭          남음   남음        남음     닫힘   —             —
   Esc 한 번                    한 겹  한 겹       남음     —      닫힘          남음
   다른 auto 를 연다            닫힘   닫힘        남음     닫힘   —             —
   스크립트 close/hidePopover   닫힘   닫힘        닫힘     닫힘   닫힘          닫힘
```

```text
   Esc 는 한 겹씩 벗긴다

   [바깥 auto]  [안쪽 auto]  [manual]        <- 셋이 떠 있다
        |
        | Esc
        v
   [바깥 auto]               [manual]        <- 안쪽만 내려갔다
        |
        | Esc
        v
                             [manual]        <- 바깥도 내려갔다
        |
        | Esc
        v
                             [manual]        <- 더는 안 내려간다
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

- ★★ **⑪ 모달의 배경을 진짜로 클릭해도 안 닫힌다.** `open` 이 그대로 `true` 다 — **「배경 클릭으로 닫기」는 직접 붙여야 하는 기능**이지 기본 동작이 아니다.
- ★ **그런데 포커스는 움직였다** — `#모달단추` 에서 **dialog 자신**으로 옮겨 갔다. 「아무 일도 안 일어난다」가 아니다.
- **⑫ `Esc` 는 `cancel` 을 먼저 내고 그 다음 `close`** 를 낸다. `returnValue` 는 빈 문자열이다 — **`Esc` 는 `close(값)` 을 안 부른다.**
- ★★ **⑬ `show()` 로 연 비모달은 `Esc` 로 안 닫힌다.** 닫기 감시자가 **모달에만** 붙는다.
- ★ **읽는 법 주의** — `[대괄호]` 줄은 **미뤄졌다가 나중에 도착한 이벤트 로그**다. ⑪ 아래의 `[모달 cancel]`·`[모달 close]` 는 **⑫ 의 `Esc` 가 낸 것**이고, ⑬ 아래의 `[비모달 close]` 는 **그 다음 단계에서 스크립트가 부른 `close()`** 가 낸 것이다. `Esc` 가 낸 것이 아니다.

```text
   dialog 를 닫는 네 가지 길

   길                         cancel 이 나나   close 가 나나   returnValue
   -------------------------------------------------------------------------
   close('확인')              안 난다          난다            '확인'
   close()                    안 난다          난다            옛 값 그대로
   Esc (모달)                 난다             난다            ''
   배경 클릭 (모달)           안 난다          안 난다         ★ 안 닫힌다
   Esc (비모달)               안 난다          안 난다         ★ 안 닫힌다
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

- ★★★ **`cancel` 을 `preventDefault()` 로 막을 수 있는지가 판마다 다르다.** ⑮ 에서는 **새로 진짜 클릭을 한 뒤** 연 모달의 `cancel` 이 **`cancelable=true`** 로 와서 **한 번 막혔고**, **그 다음 `Esc` 는 `cancelable=false`** 로 와서 **강제로 닫혔다.**
- ★ **⑭ 는 앞의 모달이 그 활성화를 이미 써 버린 뒤**라 처음부터 `cancelable=false` 였다.
- ★★ **그래서 「`Esc` 를 막는다」는 한 번만 되는 일이다.** 닫기 감시자가 **사용자 활성화 하나당 한 그룹**을 갖고, 그 그룹이 소진되면 **다음 `Esc` 는 못 막는다** — 「닫히지 않는 모달」로 사용자를 가두지 못하게 한 장치다.
- ★ **`navigator.userActivation.isActive` 는 이 판정을 대신 못 한다** — ⑭ 에서도 `true` 였는데 `cancelable` 은 `false` 였다. **읽어서 알 수 있는 값이 아니라 던져 봐야 아는 것**이다.

```text
   Esc 를 막을 수 있는가 — 사용자 활성화가 정한다

   진짜 클릭 (활성화를 얻는다)
        |
        | showModal()          닫기 감시자가 '제 그룹' 을 갖는다
        v
   Esc 첫 번째   cancel cancelable=true   -> preventDefault 가 먹힌다 (안 닫힘)
        |                                    ★ 여기서 활성화가 소진된다
        v
   Esc 두 번째   cancel cancelable=false  -> preventDefault 가 무시된다 (닫힘)

   ★ 활성화 없이 연 모달은 처음부터 cancelable=false 다 (⑭)
```

```text
   합성 이벤트와 진짜 입력은 같은 것이 아니다

   el.dispatchEvent(new MouseEvent('click'))   -> 리스너는 불린다
                                                  가벼운 닫기는 안 일어난다
   CDP Input.dispatchMouseEvent                -> 리스너도 불리고
                                                  가벼운 닫기도 일어난다

   ★ 그래서 이 절만 창 ⑤ 를 쓴다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
// wa12b-14-form.js
// dialog — 여는 문 셋
dialog.show();            // 비모달. 최상위 레이어에 안 올라간다. 포커스는 옮긴다
dialog.showModal();       // 모달. 최상위 레이어 · 배경 차단 · Esc 로 닫힌다
dialog.open = true;       // ★ 속성만 켠다. 포커스도 레이어도 안 움직인다

dialog.close('확인');      // returnValue 에 값을 넣고 닫는다
dialog.close();           // 옛 returnValue 가 남는다
dialog.returnValue;       // 평범한 문자열 프로퍼티. 직접 대입해도 된다
dialog.open;              // 열려 있나 (세 가지 '열림' 을 구분 못 한다)
dialog.matches(':modal'); // ★ 모달인가 — 이것이 구분한다

dialog.addEventListener('cancel', e => e.preventDefault()); // Esc 를 막는다 (한 번만)
dialog.addEventListener('close', e => { /* dialog.returnValue 를 읽는다 */ });

// popover — 속성 하나와 메서드 넷
el.popover;                  // 'auto' | 'manual' | 'hint' | null
el.showPopover();            // -> undefined
el.hidePopover();            // -> undefined
el.togglePopover();          // -> 열렸나 (불리언)
el.togglePopover(true);      // '열어 둬라' (강제)
el.matches(':popover-open'); // 열려 있나

el.addEventListener('beforetoggle', e => { /* 여는 쪽만 e.preventDefault() 가 먹는다 */ });
el.addEventListener('toggle', e => { /* 미뤄져서 온다. 중간 상태를 합친다 */ });

// '무대 위인가' 를 묻는 법
el.checkVisibility();                       // 닫혀 있으면 false
document.elementFromPoint(x, y);            // 모달이 열려 있으면 전부 모달을 준다
getComputedStyle(el, '::backdrop');         // ★ 아무것도 안 답한다
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
// wa12b-14-bad.js
// 1. open 속성으로 연다 — 모달이 아니고 포커스도 안 움직인다
dialog.open = true;                  // 최상위 레이어에 안 올라간다
dialog.showModal();                  // 이것이 모달이다

// 2. '열려 있나' 를 open 으로 판정한다 — 세 가지가 구분 안 된다
if (dialog.open) { }                 // show() 로 연 것도 true 다
if (dialog.matches(':modal')) { }    // 모달인지는 이것으로

// 3. ::backdrop 의 계산값으로 '무대 위인가' 를 본다 — 열기 전에도 같다
getComputedStyle(dialog, '::backdrop').backgroundColor;
dialog.matches(':modal');            // 이것으로 판정한다

// 4. .inert 로 '막혀 있나' 를 본다 — 모달 뒤에서도 false 다
if (!el.inert) el.focus();           // 막힌 줄 모르고 부른다
el.focus(); document.activeElement === el;   // 던져 보고 되읽는다

// 5. 팝오버에 입력을 넣고 autofocus 를 빼먹는다 — 커서가 안 간다
// <div popover><input></div>                 포커스가 바깥에 그대로 있다
// <div popover><input autofocus></div>       이렇게 해야 간다

// 6. toggle 이벤트로 여닫기 횟수를 센다 — 중간 상태가 합쳐진다
el.addEventListener('toggle', () => 횟수++);        // 셋을 열고 닫으면 1 이 된다
el.addEventListener('beforetoggle', () => 횟수++);  // 이쪽이 그 자리에서 온다

// 7. 닫기를 막으려 한다 — 원리상 안 된다
el.addEventListener('beforetoggle', e => {
  if (e.newState === 'closed') e.preventDefault();  // cancelable 이 false 다
});

// 8. 모달을 띄웠으니 뒤가 안전하다고 본다 — 스크립트는 통과한다
배경단추.click();                     // 모달이 열려 있어도 눌린다

// 9. dispatchEvent 로 가벼운 닫기를 시험한다 — 아무 일도 안 일어난다
document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
```

### 어디서 헷갈리나

- **`open` 과 `:modal`** — `open` 은 세 가지 열림을 **구분 못 한다.**
- **`show()` 와 `showModal()`** — **포커스는 둘 다 옮긴다.** 갈리는 것은 레이어·배경·`:modal` 셋뿐이다.
- **`auto` 와 `manual`** — 오타가 나면 `manual` 로 떨어지고 「**안 닫히는 팝오버**」가 된다.
- **`hint` 와 `manual`** — `hint` 는 **독립이 아니다.** `auto` 가 열리면 밀려난다.
- **`beforetoggle` 과 `toggle`** — 앞엣것은 **그 자리에서 · 막을 수 있고**, 뒤엣것은 **미뤄지고 · 합쳐진다.**
- **`cancel` 과 `close`** — 앞엣것은 **사용자가 물러날 때만** 나고 `close()` 로는 안 난다.
- **`.inert` 와 「막혀 있다」** — 앞엣것은 **속성을 반영할 뿐**이다.

## 어디서 틀리나

### 1. `z-index` 를 올려 모달 위로 올리려 한다

**최상위 레이어는 `z-index` 와 다른 축**이다. 실측에서 **`2147483647` 이 `1` 에게 졌다.** 무대 위로 가려면 **그 요소도 `showModal()`·`showPopover()` 로 올려야 한다.**

### 2. `::backdrop` 의 계산값으로 상태를 판정한다

**열기 전에도 연 뒤에도 같다.** 그 창은 **부적용**이다. `:modal`·`:popover-open` 을 쓴다.

### 3. 팝오버 안의 입력에 커서가 안 간다

**`popover` 는 `autofocus` 가 없으면 포커스를 안 옮긴다.** `dialog` 의 감각으로 짜면 여기서 틀린다.

### 4. 「배경을 클릭하면 닫히겠지」로 모달을 만든다

**모달 dialog 는 배경 클릭으로 안 닫힌다.** 실측에서 진짜 클릭을 넣어도 `open` 이 `true` 였다. 필요하면 **직접 붙여야 한다** — 그리고 그때 **`elementFromPoint` 가 늘 dialog 를 돌려준다**는 것까지 알아야 한다(클릭 좌표가 dialog 밖인지는 `getBoundingClientRect()` 로 따로 본다).

### 5. `toggle` 로 여닫기를 센다

**중간 상태가 합쳐진다.** 같은 tick 에서 세 번 뒤집었는데 `toggle` 은 **한 번**만 왔다. 그 자리에서 세려면 `beforetoggle` 이다.

### 6. 닫기를 막으려 한다

**팝오버의 닫는 쪽 `beforetoggle` 은 `cancelable: false`** 다. dialog 의 `cancel` 은 막을 수 있지만 **사용자 활성화 하나당 한 번**뿐이다.

### 7. `dispatchEvent` 로 가벼운 닫기를 시험한다

**아무 일도 안 일어난다.** 테스트가 「안 닫힌다」를 보고 **기능이 없다고 결론 낼 수 있다.** 진짜 입력이 필요하다.

### 8. 모달 뒤가 안전하다고 본다

**막히는 것은 사용자 입력과 포커스**다. **스크립트가 부른 `.click()` 은 통과한다.**

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `showModal()`·`showPopover()` 가 **최상위 레이어에 올린다**는 것 | **명세**(HTML — the top layer) |
| 최상위 레이어가 **`z-index` 를 안 본다**는 것 | **명세**(HTML + CSS Position — 최상위 레이어는 별도의 렌더링 판이다) |
| `show()` 와 `showModal()` **둘 다 포커스를 옮긴다**는 것 | **명세**(HTML — dialog focusing steps) |
| `autofocus` 가 있으면 그것이 이기는 것 | **명세**(HTML) |
| **팝오버가 `autofocus` 없이는 포커스를 안 옮긴다**는 것 | **명세**(HTML — popover 는 dialog 의 포커스 절차를 안 탄다) |
| 모달이 **배경을 inert 로 만든다**는 것 | **명세**(HTML — blocked by a modal dialog) |
| **`.inert` 가 속성만 반영한다**는 것 | **명세**(HTML — IDL 반영 규칙) |
| 모드가 어긋날 때 `InvalidStateError` 가 나는 것 | **명세**(HTML) |
| `popover` 의 모르는 값이 **`manual`**, 빈 값이 **`auto`** 인 것 | **명세**(HTML — enumerated attribute 의 invalid value default) |
| `auto` 끼리 밀어내고 **조상-자손은 안 밀리는** 것 | **명세**(HTML — popover ancestor 계산) |
| 닫는 쪽 `beforetoggle` 이 **`cancelable: false`** 인 것 | **명세**(HTML) |
| `toggle` 이 **미뤄지고 합쳐지는** 것 | **명세**(HTML — queue a popover toggle event task) |
| `Esc` 로 닫히는 것이 **모달뿐**인 것 | **명세**(HTML + Close Watcher) |
| **`cancel` 의 `cancelable` 이 사용자 활성화에 달린** 것 | **명세**(Close Watcher — 그룹 규칙). ★ **그런데 「몇 번까지」는 구현이 정한다** |
| **`dialog` 자신의 `autofocus` 가 무시된 것** | ★ **구현.** Chrome 151 의 관찰이다. 명세로는 dialog 가 받아야 한다 |
| **모달이 열렸을 때 `elementFromPoint` 가 늘 dialog 를 주는 것** | ★ **구현.** 명세는 「배경이 inert 다」까지만 정한다 |
| **`getBoundingClientRect().width` 의 234** | ★ **구현 + 글꼴·기본 여백.** 성질만 인용한다 |
| **모든 좌표 탐침** | **구현 + 창 크기.** 배너의 `--window-size` 가 전제다 |
| **합성 이벤트로 가벼운 닫기가 안 나는 것** | **명세**(신뢰된 이벤트만 사용자 상호작용으로 친다) |

- ★ **「알아서 해 주는」 표면일수록 구현 쪽**이다 — 초기 포커스가 정확히 어느 요소로 가느냐가 특히 그렇다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 확인 대화 상자 | `showModal()` + `close(값)` | `open` 속성 토글 |
| 비차단 알림 패널 | `show()` 또는 `popover="manual"` | `showModal()`(배경이 죽는다) |
| 드롭다운·메뉴 | `popover="auto"` | `showModal()`(무겁고 배경이 죽는다) |
| 서브메뉴 | 부모 팝오버 **안에** 중첩 | 형제로 두기(열면 부모가 닫힌다) |
| 툴팁 | `popover="hint"` | `popover="auto"`(메뉴를 닫아 버린다) |
| 토스트 | `popover="manual"` + 타이머 | `popover="auto"`(아무 클릭에나 사라진다) |
| 「무대 위인가」 판정 | `:modal` · `:popover-open` | `::backdrop` 계산값 · `z-index` |
| 「막혀 있나」 판정 | `focus()` 를 던지고 `activeElement` 되읽기 | `el.inert` |
| 팝오버 안의 첫 입력 | `autofocus` 를 직접 단다 | 브라우저가 해 줄 것으로 기대 |
| 여닫기 횟수 세기 | `beforetoggle` | `toggle`(합쳐진다) |
| 닫히기 직전 확인 | `dialog` 의 `cancel`(한 번) | 팝오버의 닫는 `beforetoggle`(못 막는다) |
| 가벼운 닫기 테스트 | 진짜 입력(CDP·WebDriver) | `dispatchEvent` |
| 모달 뒤를 진짜로 잠그기 | 상태 플래그로 스크립트 쪽도 막기 | 모달이 알아서 막아 줄 것으로 기대 |

## 핵심 문장

1. **`showModal()` 과 `showPopover()` 는 「최상위 레이어에 올리는」 두 문이다** — `show()` 와 `open` 속성은 안 올린다.
2. **최상위 레이어는 `z-index` 와 다른 축이다** — `2147483647` 이 `1` 에게 졌다.
3. **계산값에는 자국이 없다** — `::backdrop` 도 `zIndex` 도 열기 전후가 같다. **판정은 `:modal`·`:popover-open` 과 좌표로 한다.**
4. **`show()` 도 포커스를 옮긴다** — 갈리는 칸은 7 중 3 뿐이다.
5. **팝오버는 `autofocus` 가 없으면 포커스를 안 옮긴다** — 여기가 `dialog` 와 갈리는 급소다.
6. **「막혀 있나」를 답하는 프로퍼티는 없다** — `focus()` 를 던져 보는 것이 유일한 창이고, **스크립트의 `.click()` 은 막히지 않는다.**
7. **가벼운 닫기는 진짜 입력에만 반응한다** — `auto` 는 바깥 클릭과 `Esc` 에 **한 겹씩**, `manual` 은 아무것에도 안 닫힌다.
8. **모달은 배경 클릭으로 안 닫히고 비모달은 `Esc` 로 안 닫힌다** — 둘 다 「당연히 되겠지」가 틀리는 자리다.
9. **`Esc` 는 한 번만 막을 수 있다** — 사용자 활성화가 소진되면 `cancel` 이 `cancelable: false` 로 온다.
10. **`toggle` 은 중간 상태를 합친다** — 그 자리에서 세려면 `beforetoggle` 이다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 14번)
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **47번**(`dialog`) — ★ **그쪽은 마크업으로, 여기는 스크립트로.** `open` 속성·`::backdrop` 선언·`method="dialog"` 폼은 그쪽이 정본이다
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **48번**(`details`/`summary` 와 `popover` 속성) — ★ `popovertarget` 으로 **스크립트 없이** 여닫는 쪽이 그쪽이다
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **45번**(포커스·`tabindex`·`inert`) — ★ **「무엇이 포커스 가능인가」의 정본.** 여기는 「**그래서 열었을 때 어디로 가나**」만 쓴다
- [CSS 22번 주제](../../languages/css/syntax/22-stacking-context-and-z-index/2-summary.md) — ★ **이 주제의 정본 이웃.** 쌓임 맥락과 `z-index` 가 거기다. 여기는 「**그 축 밖에 판이 하나 더 있다**」만 쓴다
- [CSS 21번 주제](../../languages/css/syntax/21-position-and-containing-block/2-summary.md) — 최상위 레이어로 올라간 요소의 포함 블록이 무엇이 되나
- [03번 주제](../03-node-creation-insertion-removal/2-summary.md) — 열려 있는 dialog 를 `remove()` 하면 어떻게 되나((8)의 ③ 이 그 모양이다)
- [06번 주제](../06-attribute-vs-property/2-summary.md) — `popover` 의 모르는 값이 **조용히 `manual` 로 떨어지는** 것의 정본
- [08번 주제](../08-getcomputedstyle/2-summary.md) — 계산값이 「**무엇이 선언됐나**」를 말한다는 것. (5)가 그 위에 선다
- [12번 주제](../12-shadow-dom/2-summary.md) — 그림자 경계 안의 dialog·popover 도 같은 최상위 레이어를 쓴다(이 문서는 **그 조합을 던지지 않았다**)
- [목록의 **16번 주제**](../16-event-propagation-phases/)(전파 3단계) — `cancel`·`close`·`toggle` 이 버블하나
- [목록의 **17번 주제**](../17-stoppropagation-vs-preventdefault/)(`preventDefault`) — `cancelable` 이 `false` 일 때 `preventDefault()` 가 무엇을 하나의 정본
- [목록의 **24번 주제**](../24-document-lifecycle-events/)(문서 수명주기 이벤트) — 사용자 활성화가 어디서 또 나오나

## 용어 풀이

- **최상위 레이어(top layer)** — 문서 위에 통째로 얹히는 별도의 렌더링 판.\
  예: 무대. 객석에서 아무리 높은 의자에 올라가도 무대 위 배우보다 앞에 설 수 없다.
- **모달(modal)** — 열려 있는 동안 **배경을 못 쓰게 만드는** 대화 상자. `showModal()` 로만 된다.
- **비모달(modeless)** — 배경을 그대로 쓸 수 있는 대화 상자. `show()` 로 연 것.
- **`::backdrop`** — 최상위 레이어 요소 **뒤에 깔리는 막**을 가리키는 의사 요소.\
  예: 무대와 객석 사이의 반투명 커튼. **계산값은 커튼이 없을 때도 그대로 나온다.**
- **`inert`** — 그 부분 트리를 **사용자 입력과 포커스에서 빼는** 속성.\
  예: 불 꺼진 객석. 앉아 있기는 한데 아무도 말을 안 건다.
- **가벼운 닫기(light dismiss)** — 바깥을 누르거나 `Esc` 를 눌렀을 때 **저절로 닫히는** 동작.
- **닫기 감시자(close watcher)** — `Esc` 같은 「물러나기」 신호를 받아 무엇을 닫을지 정하는 브라우저 안의 장치.\
  예: 무대 감독. `Esc` 한 번에 **맨 위 하나만** 내려보낸다.
- **사용자 활성화(user activation)** — 「방금 사용자가 진짜로 눌렀다」는 표시.\
  예: 입장권. 한 장으로 한 번만 막을 수 있고, 쓰면 없어진다.
- **`returnValue`** — dialog 가 닫히면서 남기는 문자열. **`close()` 가 지우지 않는다.**
- **`beforetoggle` / `toggle`** — 팝오버가 열리고 닫힐 때 나는 두 이벤트. 앞엣것은 **그 자리에서**, 뒤엣것은 **미뤄져서** 온다.
- **신뢰된 이벤트(trusted event)** — 브라우저가 진짜 입력으로 만든 이벤트(`isTrusted === true`).\
  예: `dispatchEvent` 로 만든 클릭은 위조 지폐다 — 리스너는 속지만 브라우저는 안 속는다.
- **히트 테스트(hit test)** — 「이 좌표에 있는 요소가 누구인가」를 브라우저가 푸는 일. `elementFromPoint` 가 그 답을 준다.
- **부적용인 창** — 재 봤더니 같은 것이 아니라 **잴 것이 없는** 관측 수단. 이 편에서는 `::backdrop` 의 계산값이 그렇다.

## 더 들어가면

- **`<form method="dialog">`** 는 제출하면 dialog 를 닫고 **누른 버튼의 `value` 를 `returnValue` 로** 넣는다. **마크업 쪽 표면이라 HTML 갈래 47번의 몫**이고 **이 문서는 던지지 않았다.**
- **`popovertarget`·`popovertargetaction`** 은 스크립트 없이 팝오버를 여닫는 속성이다. **HTML 갈래 48번의 몫**이고, 이 문서는 **그 경로의 「이어짐」 계산을 확인하지 않았다**(DOM 중첩만 던졌다).
- **`::backdrop` 에 전환·애니메이션을 걸려면** `transition-behavior: allow-discrete` 와 `@starting-style` 이 필요하다. **CSS 갈래의 몫**이고 **여기서 던져 보지 않았다.**
- **`anchor` 위치 지정**(`anchor-name`·`position-anchor`)은 팝오버를 방아쇠 옆에 붙이는 CSS 표면이다. **던져 보지 않았다.**
- **`CloseWatcher` 를 직접 만드는 것**(`new CloseWatcher()`)도 가능하다 — 커스텀 UI 에 `Esc` 를 붙이는 길이다. **이 문서는 dialog 를 통해서만 관측했다.**
- **접근성** — 모달 dialog 는 암묵 역할이 `dialog` 이고 `aria-modal` 이 함께 붙는다. **스크린리더가 실제로 무엇을 읽는지는 이 문서가 못 본다**(접근성 트리는 보조 기술의 **입력**이지 출력이 아니다). 역할·이름 쪽은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **41번** 과 **46번** 의 몫이다.
- **모바일 가상 키보드** — 모달을 열면 키보드가 뜨고 뷰포트가 줄어든다. **headless 로는 관측하지 못했다.**
