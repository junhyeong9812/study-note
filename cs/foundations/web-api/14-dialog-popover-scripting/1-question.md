# web-api/14 — `dialog`·`popover` 의 스크립트 제어: `showModal()`·`togglePopover()`·최상위 레이어·포커스 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **마크업 갈래와의 경계** — HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **47번** 과 **48번** 은 `dialog`·`popover` 를 **마크업으로** 다루고, 여기는 **그것을 스크립트로 열고 닫는 쪽**이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★★ **가벼운 닫기와 `Esc` 문항은 진짜 입력으로 던진 것**이다 — `dispatchEvent` 로는 한 칸도 안 움직인다.
> ★ 선행은 [03번 주제](../03-node-creation-insertion-removal/2-summary.md)(노드를 붙이고 떼는 것)와 [CSS 22번 주제](../../languages/css/syntax/22-stacking-context-and-z-index/2-summary.md)(쌓임 맥락과 `z-index`)다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여는 문이 셋인데 (예측)

```js
// wa12b-14-q1.js
dialog.open = true;        // ①
dialog.show();             // ②
dialog.showModal();        // ③

dialog.open            dialog.matches(':modal')
document.activeElement                 // 열기 전에는 바깥 단추에 있었다
getComputedStyle(dialog).zIndex        // 셋 다 z-index: 1 을 줬다
```

- 세 문 각각에 대해 네 줄을 적어라.
- **`open` 하나만 보면 셋이 구분되는가**?
- 「최상위 레이어에 올라갔다」를 무엇으로 아는가?

### 2. 같은 dialog, 여는 방법만 바꾸면 (예측)

```js
// wa12b-14-q2.js
// 속이 한 글자도 같은 dialog 둘을 각각 show() 와 showModal() 로 연다
dialog.open                        dialog.matches(':modal')
document.activeElement             getComputedStyle(dialog, '::backdrop').backgroundColor
배경입력.inert                     배경입력.focus() 뒤의 document.activeElement
document.elementFromPoint(4, 4)
```

- 일곱 칸을 두 모드에 대해 적어라.
- **갈리는 칸이 몇 개인가**?
- 「모달만 포커스를 가져간다」는 맞는 말인가?

### 3. 닫고 나서 무엇이 남나 (예측)

```js
// wa12b-14-q3.js
dialog.showModal();
dialog.returnValue                 //  ?
dialog.close('확인');
dialog.returnValue                 //  ?  · dialog.open 은?
dialog.showModal();  dialog.close();
dialog.returnValue                 //  ?
```

- 네 줄을 적어라.
- 인자 없는 `close()` 가 **`returnValue` 를 지우는가**?
- 닫은 뒤 포커스는 어디로 가는가?

### 4. `z-index` 를 최댓값으로 주면 (예측)

```css
/* wa12b-14-q4.css */
#맨위 { position: fixed; inset: 0; z-index: 2147483647 }
#팝   { z-index: 1 }        /* popover="manual" */
dialog { z-index: 1 }
```

```js
// wa12b-14-q4.js
document.elementFromPoint(140, 80)       // 팝오버를 열기 전 / 연 뒤
getComputedStyle(팝).zIndex              // 열기 전 / 연 뒤
document.elementFromPoint(600, 400)      // 모달을 연 뒤 — 아무것도 없는 빈 자리다
```

- 다섯 값을 적어라.
- **`z-index` 와 최상위 레이어는 같은 축인가**?
- 계산값에서 무엇이 바뀌는가?

### 5. 「무대 위인가」를 무엇으로 묻나 (경계)

```js
// wa12b-14-q5.js
창.matches(':modal')          창.open          창.checkVisibility()
창.getBoundingClientRect().width
getComputedStyle(창, '::backdrop').backgroundColor
getComputedStyle(팝).zIndex
```

- 여섯 칸을 **열기 전 / 연 뒤** 두 값으로 적어라.
- **답을 못 하는 창이 몇 개인가**? 그것은 「재 봤더니 같았다」인가?
- 대조할 것이 **숫자가 아니라 성질**인 칸은 어느 것인가?

### 6. 배경이 막혔다는 것을 무엇으로 아나 (경계)

```js
// wa12b-14-q6.js
// 모달이 열려 있는 상태에서
배경입력.inert            배경입력.matches('[inert]')       배경입력.checkVisibility()
배경입력.focus();  document.activeElement
배경단추.click();  // 리스너가 불리는가?
막힘.inert                막힌단추.inert                    // <div inert><button id=막힌단추>
```

- 일곱 줄을 적어라.
- **「지금 막혀 있나」를 답하는 프로퍼티가 있는가**?
- 모달이 막는 것과 **안 막는 것**을 갈라라.

### 7. 열자마자 커서가 어디에 있나 (예측)

```html
<!-- wa12b-14-q7.html -->
<dialog id="ㄱ"><p>글만 있다</p></dialog>
<dialog id="ㄴ"><button>첫 단추</button><button>둘째</button></dialog>
<dialog id="ㄷ"><button>첫 단추</button><input autofocus><button>셋째</button></dialog>
<dialog id="ㅁ"><button disabled>못 누름</button><button>누를 수 있음</button></dialog>
<dialog id="ㅂ"><div tabindex="-1">div</div><button>단추</button></dialog>
<div id="팝ㄴ" popover="auto"><button>팝오버 첫 단추</button></div>
```

- 각각을 `showModal()`(팝오버는 `showPopover()`)로 열었을 때 `document.activeElement` 를 적어라.
- **`dialog` 와 `popover` 가 갈리는 칸**은 어디인가?
- `tabindex="-1"` 은 「포커스 가능」에서 빠지는가?

### 8. 닫으면 포커스가 어디로 돌아오나 (경계)

```js
// wa12b-14-q8.js
연놈.focus();  dialog.showModal();  dialog.close();     // ①
연놈.focus();  dialog.showModal();  안쪽둘째.focus();  dialog.close();   // ②
사라질.focus();  dialog.showModal();  사라질.remove();  dialog.close();  // ③
```

- 세 판의 `document.activeElement` 를 적어라.
- ③ 이 실무에서 **어떤 화면의 모양**인가?

### 9. `popover` 의 표면을 던지면 (예측)

```js
// wa12b-14-q9.js
$('오토').popover                            // popover="auto"
모르는것.popover                             // popover="zzznope"
빈것.popover                                 // popover=""
평범한div.popover
el.showPopover()  ·  el.hidePopover()  ·  el.togglePopover()  ·  el.togglePopover(true)
평범한div.showPopover()
```

- 아홉 줄을 적어라(메서드는 **돌려주는 값**까지).
- **예외를 던지는 자리가 몇 개인가**?
- `popover` 속성에 오타를 내면 **화면에서 어떤 증상**으로 드러나는가?

### 10. 가벼운 닫기가 언제 일어나나 (경계)

```text
auto 하나 · 그 안에 중첩된 auto 하나 · manual 하나 · hint 하나를 전부 열어 두고
  ① 중첩된 안쪽 팝오버 안을 클릭
  ② 바깥 팝오버의 빈 자리를 클릭
  ③ 완전히 바깥을 클릭
  ④ Esc 를 한 번 · 두 번 · 세 번
모달 dialog 를 열어 두고
  ⑤ 배경을 클릭        ⑥ Esc
show() 로 연 비모달에
  ⑦ Esc
```

- 일곱 경우에 무엇이 닫히는지 전수로 적어라.
- **`dispatchEvent` 로 만든 클릭·키로 같은 것을 던지면** 어떻게 되는가?
- 닫히는 쪽 `beforetoggle` 을 `preventDefault()` 로 막을 수 있는가?
- **`Esc` 로 닫히는 것을 `cancel` 로 막을 수 있는가**? 몇 번까지?

### 11. `beforetoggle` 과 `toggle` 은 왜 둘인가 (왜)

- 같은 tick 안에서 **열고·닫고·다시 열면** 두 이벤트가 각각 몇 번 오는가?
- **여닫기 횟수를 세려면** 어느 것을 써야 하는가?
- `toggle` 이 알려 주는 것은 「무슨 일이 있었나」인가 「지금 어떤가」인가?

### 12. 다른 주제와 잇기 (연결)

- HTML 갈래의 **47번**·**48번** 과 이 주제의 경계선을 한 문장으로 그어라.
- [CSS 22번 주제](../../languages/css/syntax/22-stacking-context-and-z-index/2-summary.md)의 `z-index` 와 최상위 레이어의 관계를 한 문장으로 적어라.
- [08번 주제](../08-getcomputedstyle/2-summary.md)의 「계산값이 무엇을 말하나」가 이 주제의 어느 자리에서 되풀이되는가?
- [06번 주제](../06-attribute-vs-property/2-summary.md)의 「조용히 버려짐」이 이 주제의 어디에 나오는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
