# Event Capture (캡처 단계)

> **한 줄**: 클릭하면 브라우저는 먼저 **위(window·document)에서 실제로 클릭된 요소까지 내려가며** 캡처 리스너를 실행하고(탑다운), 그다음 **클릭된 요소에서 다시 위로 올라가며** 버블 리스너를 실행한다(바텀업). 캡처 리스너는 같은 이벤트를 **가장 먼저** 받는다.

## 이해의 흐름 — 내가 정리한 정의를 다듬기

> 대화에서 직접 정리한 정의와 보정한 두 군데.

**내가 정리한 것**: "클릭하면 DOM부터 해당 모달까지 이벤트를 쭉 훑고, 그 후 아래부터 역으로 올라오면서 버블을 한다."

```text
보정 ①  끝점은 "모달"이 아니라 실제로 클릭된 요소(e.target)
보정 ②  길은 논리 트리가 아니라 DOM 경로(parentNode 체인) — 이벤트 시작 때 한 번 정해짐

window → document → body → .mini-portal → … → button     ① 캡처: 탑다운으로 훑음
                                              button     ② 타깃
window ← document ← body ← .mini-portal ← … ← button     ③ 버블: 바텀업으로 훑음

각 요소에 들를 때: 그 단계용 리스너가 있으면 실행, 없으면 지나감
```

**캡처를 쓰는 이유 한 줄**: 내려가는 길에서 **가장 먼저** 받으므로, 아래 요소의 `stopPropagation`에 막히지 않는다. (pointerdown을 쓰는 이유와는 **다른** 이유 — 아래 표)

## 이벤트 한 번이 지나가는 길

```
window → document → body → #outer → #inner → button     ① 캡처: 탑다운으로 훑음
                                             button     ② 타깃 (e.target)
window ← document ← body ← #outer ← #inner ← button     ③ 버블: 바텀업으로 훑음
```

- 끝점은 **실제로 클릭된 요소**(`e.target`)다. "모달"이나 "컴포넌트"가 아니다.
- 길은 **DOM 경로**(`parentNode` 체인)이고, 이벤트가 시작될 때 한 번 정해진다. 그래서 portal 안 버튼의 길에는 `#app`이 없다. → [event-flow](event-flow.md)
- 각 요소에 들를 때마다 **그 단계용으로 등록된 리스너가 있으면 실행, 없으면 지나간다.** 같은 요소라도 캡처 리스너는 ①에서, 버블 리스너는 ③에서 따로 불린다.

## 등록 방법

```js
el.addEventListener('click', fn);                     // 버블 (기본값)
el.addEventListener('click', fn, true);               // 캡처
el.addEventListener('click', fn, { capture: true });  // 캡처 (같은 뜻)

el.removeEventListener('click', fn, true);            // 해제도 같은 capture 값으로 — 다르면 해제 안 됨
```

## 실험 1: 실행 순서

모든 요소에 캡처·버블 리스너를 하나씩 달고 버튼을 클릭했다 (jsdom에서 실제 실행한 출력).

```js
const add = (el, name) => {
  el.addEventListener('click', () => out.push('캡처  ' + name), true);
  el.addEventListener('click', () => out.push('버블  ' + name));
};
// document, body, #outer, #inner, button에 add → button 클릭
```

```
캡처  document     ┐
캡처  body         │ ① 위에서 아래로
캡처  #outer       │
캡처  #inner       │
캡처  button       ┘
버블  button       ┐
버블  #inner       │ ③ 아래에서 위로
버블  #outer       │
버블  body         │
버블  document     ┘
```

**같은 document인데 캡처는 맨 처음, 버블은 맨 마지막.** 어느 단계에 등록했느냐에 따라 순서가 정반대다.

## 실험 2: 중간에서 stopPropagation

`#inner`의 **버블** 리스너가 `e.stopPropagation()`을 부르게 하고 다시 클릭.

```
캡처  document     ← 그래도 실행됨 (이미 지나간 뒤)
캡처  body
캡처  #outer
캡처  #inner
캡처  button
버블  button
버블  #inner       ← 여기서 stopPropagation
                    #outer · body · document 버블은 실행 안 됨
```

- 버블 쪽 상위 리스너는 막혔다 — 이벤트가 거기까지 못 올라갔다.
- 캡처 쪽 리스너는 **내려가는 길에서 이미 실행된 뒤**였다.

→ **캡처 리스너는 하위 요소의 stopPropagation에 막히지 않는다.** (반대로 캡처 리스너가 stopPropagation을 부르면, 그 아래 요소들과 버블 전체가 막힌다.)

## 언제 캡처를 쓰나

| 용도 | 이유 | 예 |
|---|---|---|
| 무조건 먼저·무조건 봐야 할 때 | 앱 코드의 stopPropagation과 무관 | 모달 바깥 클릭 감지, 전역 단축키, 클릭 로깅 |
| 하위 요소보다 먼저 가로챌 때 | 캡처에서 stopPropagation하면 아래로 안 감 | 로딩 중 모든 클릭 막기 |
| 버블링하지 않는 이벤트를 상위에서 받을 때 | `focus`·`blur`는 버블 안 하지만 캡처 단계는 지난다 | 폼 전체 focus 추적 |

일반 핸들러는 버블(기본값)로 충분하다. React의 `onClick`은 버블, 캡처는 `onClickCapture`로 따로 있다.

## 이 프로젝트에서

```js
// src/modal.js — attachDocument
document.addEventListener('pointerdown', onPointerDown, true);   // 바깥 클릭 감지
document.addEventListener('keydown', onKeyDown, true);           // ESC · Tab
```

- 데모의 모달 안 버튼들은 `stopPropagation()`을 부른다(닫기, 메뉴 열기, 또 열기). 버블로 달았다면 그 버튼들을 누를 때 document 리스너가 이벤트를 못 받는다. 캡처라서 항상 먼저 받는다.
- **pointerdown(click 대신)과 캡처(버블 대신)는 서로 다른 문제를 막는다.**

| 선택 | 막는 문제 |
|---|---|
| pointerdown | 여는 click이 닫기 리스너에 걸려 열자마자 닫힘 → [N2](../learning/modal/n2-open-close-same-click.md) |
| 캡처 | 앱 코드의 stopPropagation에 바깥 클릭·ESC 감지가 막힘 |

## 흔한 함정

- **해제 시 capture 값 누락**: `addEventListener(t, fn, true)` 후 `removeEventListener(t, fn)` → 해제 안 됨(다른 리스너로 취급).
- **캡처에서 stopPropagation**: 아래의 모든 핸들러가 먹통이 된다. 의도한 게 아니면 쓰지 않는다.
- **리스너를 이벤트 진행 중에 추가**: 이미 지나간 단계·요소의 리스너는 이번 이벤트에 실행되지 않고, 아직 안 지나간 요소의 리스너는 실행된다. N2가 이 성질 때문에 생긴다.
