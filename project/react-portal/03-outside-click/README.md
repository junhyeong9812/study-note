# 03 — 바깥 클릭으로 닫기: 어느 트리에 묻고, 어느 이벤트로 듣나

- 커밋: [`8623f68`](https://github.com/junhyeong9812/react-portal/commit/8623f68) (createModal) · [`f6386cb`](https://github.com/junhyeong9812/react-portal/commit/f6386cb) (문제 재현 토글 N1·N2) · [PR #2](https://github.com/junhyeong9812/react-portal/pull/2)
- 학습 노트: [archive/learning/modal/n1-outside-click.md](../archive/learning/modal/n1-outside-click.md) · [n2-open-close-same-click.md](../archive/learning/modal/n2-open-close-same-click.md)

---

## 1. 무엇이 문제였나

"모달 바깥을 누르면 닫기"는 두 가지 결정을 품고 있다.

1. **"바깥"을 어떻게 판정하나.** 모달 안에서 연 드롭다운 메뉴도 Portal이라 DOM은 body로 나간다. 그 메뉴를 누르는 건 "안쪽"이어야 한다.
2. **어떤 이벤트로 듣나.** 모달은 여는 버튼의 **click** 핸들러에서 만들어진다. 같은 click이 이어서 document까지 올라간다(버블링은 처리됐다고 멈추지 않는다).

둘 중 하나라도 틀리면 증상이 바로 보인다.
- N1: 메뉴 항목을 누르면 모달이 닫힌다.
- N2: 열자마자 닫힌다(모달이 아예 안 보인다).

---

## 2. 무엇을 고민했나

**판정 — DOM에 물을까, 논리 트리에 물을까.**

| 후보 | 방법 | 메뉴 항목 클릭 결과 |
|---|---|---|
| A. DOM `contains` | `dialog.el.contains(e.target)` — dialog 요소 아래 DOM 자식인가 | 메뉴는 body 쪽 다른 portal → **바깥** ✗ |
| B. 논리 트리 | 클릭된 노드에서 `n.parent`를 따라 올라가며 dialog를 만나나 | 메뉴 항목 → box → menu → 메뉴 열기 버튼 → … → dialog → **안쪽** ✓ |

"안쪽인가"는 **관계**에 대한 질문이다. 엘리먼트는 DOM 관계만 알고, 노드가 논리 관계를 안다 → B.

**이벤트 — click을 들을까, pointerdown을 들을까.**

| 후보 | 등록 | 여는 click이 document에 도착하면 |
|---|---|---|
| A. `click` 버블 | 여는 핸들러 안에서 `document.addEventListener('click', …)` | 방금 단 닫기 리스너가 같은 click을 받음 → target(여는 버튼)은 바깥 → **닫힘** ✗ |
| B. `pointerdown` 캡처 | `document.addEventListener('pointerdown', …, true)` | 이번 클릭의 pointerdown은 모달 생성 **전에** 이미 끝남 → 반응 없음 ✓ |
| C. `click` 캡처 | — | document 캡처 단계는 여는 핸들러보다 먼저 지나가서 이번 click은 안 받음. 다만 "안에서 누르고 바깥에서 뗀 드래그"에서 click이 공통 조상에서 발생해 판정이 애매해진다 |

→ **pointerdown + 캡처.** 여는 이벤트(click)와 닫는 이벤트(pointerdown)를 **서로 다른 이벤트**로 만든다.\
캡처는 별개의 이유다 — 앱 코드가 버블 단계에서 `stopPropagation()`을 불러도 바깥 감지가 막히지 않게.

---

## 3. 그래서 이렇게

```text
사용자가 "모달 열기"를 누름
├─ pointerdown ─ … → document   모달 없음, 닫기 리스너 없음 → 아무 일 없음 (여기서 끝)
└─ click ─ … → .mini-root(dispatch) → 여는 핸들러 → createModal
                                         └ document.addEventListener('pointerdown', onPointerDown, true)
           … → document          닫기 리스너는 pointerdown용 → 이 click엔 반응 없음 ✓

(나중에) 바깥을 누름
└─ pointerdown ─ document 캡처 → onPointerDown
                  nodeOf(target) → n.parent를 따라 dialog를 만나나?
                     만남   → 안쪽 → return
                     못 만남 → modal.close('outside')
```

---

## 4. 코드 — 실제 커밋에서

`src/modal.js` (`8623f68`) — 논리 트리 판정.

```js
// ── 논리 트리 판정 ──
function isLogicalDescendant(node, ancestor) {
  for (let n = node; n; n = n.parent) if (n === ancestor) return true;
  return false;
}

const top = () => stack[stack.length - 1];

// ── document 리스너 (모달이 1개 이상일 때만 붙어 있음) ──
// 캡처 단계로 단다: 앱 코드가 stopPropagation해도 먼저 받는다.
// pointerdown을 쓰는 이유: 모달을 "여는" 클릭의 pointerdown은 모달이 생기기 전에 이미 지나갔으므로
// 여는 클릭이 곧바로 "바깥 클릭"으로 오인되지 않는다(click을 쓰면 오인된다).
function onPointerDown(e) {
  const modal = top();
  if (!modal) return;
  const node = nodeOf(e.target);
  // DOM의 contains가 아니라 논리 트리로 판정 → dialog 안에서 연 portal(DOM은 body)도 "안쪽"
  if (node && isLogicalDescendant(node, modal.dialog)) return;
  modal.close('outside');
}
```

`demo/naive-modal.js` (`f6386cb`) — 일부러 틀린 버전(토글로 켜고 끔). before(버그)와 after(정답)가 한 줄씩 대비된다.

```js
  const outsideType = bugs.clickOutside ? 'click' : 'pointerdown';
  const outsideCapture = !bugs.clickOutside;
  const onOutside = (e) => {
    if (!isTop()) return;
    // N1 버그: DOM contains → dialog 안에서 연 메뉴(portal, DOM은 body)가 "바깥"이 됨
    const inside = bugs.domContains
      ? dialog.el.contains(e.target)
      : isLogicalDescendant(nodeOf(e.target), dialog);
    if (!inside) modal.close('outside');
  };
  document.addEventListener(outsideType, onOutside, outsideCapture);
```

---

## 5. 구현 중 마주친 문제

**데모의 여는 버튼이 N2를 가리고 있었다.**\
여는 버튼이 `e.stopPropagation()`을 부르고 있어서 click이 document까지 못 가, click 기반 naive 코드도 "우연히" 정상으로 보였다.\
실제 앱에서는 "어떤 버튼으로 열면 되고 어떤 버튼으로 열면 안 되는" 이상한 버그가 되는 형태다.\
재현 토글을 만들며 여는 버튼의 `stopPropagation`을 뺐고, 라이브러리(pointerdown)는 그 상태에서도 정상임을 확인했다.

**load-bearing 가정을 먼저 실증했다.**\
"click 핸들러 안에서 document에 단 **버블** click 리스너가 같은 click에 실행된다"를 jsdom 스모크로 확인한 뒤에 토글을 구현했다.

**click-through 의심 — 정정됨.**\
pointerdown에서 오버레이를 치우면 같은 클릭의 click이 뒤 요소로 관통할 수 있다는 위험을 PR에 "실브라우저 미검증"으로 남겼다.\
사용자가 실브라우저에서 "뒤 버튼이 눌린다"고 보고했다가, 다시 보니 바깥 클릭으로 맨 위 모달이 하나씩 닫힌 정상 동작이었다고 정정했다 → 여전히 **미검증**으로 NEXT에 남김.

**헷갈렸던 이해.**
- "N1은 DOM이 이벤트를 돌 때 mini-portal에 물어서?" → 이벤트를 받는 곳은 두 버전이 같다. 다른 건 받은 **다음의 판정 한 줄**(물리 트리에 묻기 vs 논리 트리에 묻기).
- "document에 도착했다고 왜 닫혀? 닫는 동작이 등록돼 있어야지?" → 여는 도중에 등록된 그 리스너가 바로 **닫는 리스너**다. 여는 click 하나가 여는 데도, 닫는 판정에도 쓰였다.

---

## 6. 결론

- 테스트: "dialog 안에서 연 portal은 DOM상 dialog 밖이지만 논리 자손이라 안쪽이다"(`dialog.el.contains`로 바꾸면 실패 — 변이 확인).
- 원칙: **위치 질문은 DOM, 관계 질문은 논리 트리.** **여는 이벤트와 닫는 이벤트를 다른 이벤트로.**
- 개념 노트: [cs/web-platform/27-modal-dialog-behavior](../../../cs/web-platform/27-modal-dialog-behavior/)
