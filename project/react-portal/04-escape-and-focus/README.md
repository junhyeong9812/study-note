# 04 — ESC는 맨 위만, Tab은 모달 안에서만

- 커밋: [`8623f68`](https://github.com/junhyeong9812/react-portal/commit/8623f68) (createModal) · [`f6386cb`](https://github.com/junhyeong9812/react-portal/commit/f6386cb) (재현 토글 N3) · [PR #2](https://github.com/junhyeong9812/react-portal/pull/2)
- 학습 노트: [archive/learning/modal/n3-escape-top-only.md](../archive/learning/modal/n3-escape-top-only.md) · [n3-tab-trap.md](../archive/learning/modal/n3-tab-trap.md)

---

## 1. 무엇이 문제였나

모달이 겹쳐 있을 때 키보드 동작에 두 가지 계약이 필요했다.

- **ESC**: 맨 위 모달 하나만 닫는다. 한 번에 전부 닫히면 안 된다.
- **Tab**: 포커스가 모달 밖(브라우저 UI, 어두운 배경 뒤의 페이지 버튼)으로 빠지면 안 된다. 빠지면 Enter로 **보이지 않는 뒤쪽 버튼**이 눌린다.

둘 다 "**지금 맨 위 모달이 누구인지**"를 아는 곳이 있어야 풀린다.

---

## 2. 무엇을 고민했나

**ESC — 리스너를 어디에 몇 개 둘까.**

| 후보 | 구조 | ESC 결과 |
|---|---|---|
| A. 모달마다 자기 리스너 | `createModal`이 불릴 때마다 document에 keydown 리스너 추가, 각자 클로저로 "자기 모달"을 기억 | 각 리스너가 자기 모달만 안다 → 전부 반응 → 전부 닫힘 ✗ |
| B. 공유 리스너 1개 + 모달 스택 | 모듈에 `stack` 하나, 리스너는 첫 모달 때만 붙임 | 리스너가 `top()`을 보고 맨 위 하나만 닫음 ✓ |

"다른 모달에 도달하지 못하게"를 stopPropagation으로 막는 게 아니라, **리스너를 하나만 두고 그 리스너가 맨 위를 고르는** 구조로 풀었다.\
레이어 스택(z-index용, 메뉴 같은 비모달 portal도 포함)과 모달 스택은 따로 둔다.

**Tab — 어디까지 직접 구현할까.**

| 후보 | 방법 | 대가 |
|---|---|---|
| A. 모든 Tab 이동을 직접 계산 | 포커스 가능 요소 목록에서 다음 요소를 직접 focus | 브라우저 규칙(tabindex 순서·숨김 요소)을 다시 구현해야 함 |
| B. 가장자리에서만 개입 | 마지막에서 Tab·처음에서 Shift+Tab일 때만 `preventDefault` + 반대쪽 끝으로 | 가운데는 브라우저에 맡김 → 단순 |

→ **B.** 그리고 여기서는 "안쪽" 판정을 **DOM**(`contains`·`querySelectorAll`)으로 한다. Tab 순서는 브라우저가 **DOM 순서**로 정하므로 위치 질문이기 때문이다([03](../03-outside-click/README.md)의 관계 질문과 대비).

---

## 3. 그래서 이렇게

```text
stack: [#1, #2]   ESC → top() = #2 → #2만 닫음 → stack: [#1]
                  ESC → top() = #1 → #1 닫음   → stack: []  → document 리스너 해제

Tab:        [안쪽 버튼] → [메뉴 열기] → [또 열기] → [닫기] ─┐
               ↑   (가운데는 브라우저 기본 이동)              │ preventDefault + first.focus()
               └─────────────────────────────────────────────┘
열 때: previousFocus 기억 → microtask에서 첫 포커스 요소로 / 닫을 때: previousFocus로 복귀
```

---

## 4. 코드 — 실제 커밋에서

`src/modal.js` (`8623f68`)

```js
function onKeyDown(e) {
  const modal = top();
  if (!modal) return;
  if (e.key === 'Escape') {
    e.preventDefault();
    modal.close('escape');
  } else if (e.key === 'Tab') {
    trapTab(e, modal);
  }
}

function attachDocument() {
  document.addEventListener('pointerdown', onPointerDown, true);
  document.addEventListener('keydown', onKeyDown, true);
}
```

```js
  const first = items[0];
  const last = items[items.length - 1];
  const active = document.activeElement;
  const inside = dialogEl.contains(active);
  // 가장자리에서만 개입한다. 중간 이동은 브라우저 기본 Tab 동작에 맡긴다.
  if (e.shiftKey) {
    if (!inside || active === first || active === dialogEl) {
      e.preventDefault();
      last.focus();
    }
  } else if (!inside || active === last) {
    e.preventDefault();
    first.focus();
  }
```

`demo/naive-modal.js` (`f6386cb`) — N3 버그: 맨 위 확인 없음, Tab 가두기 없음.

```js
  // N3 버그: 모달마다 자기 리스너가 ESC에 반응(맨 위 확인 없음) → ESC 한 번에 전부 닫힘. Tab 가두기도 없음.
  const onKey = (e) => {
    if (e.key === 'Escape') {
      if (bugs.escAllNoTrap || isTop()) modal.close('escape');
    } else if (e.key === 'Tab' && !bugs.escAllNoTrap && isTop()) {
      trapTab(e, dialog.el);
    }
  };
  document.addEventListener('keydown', onKey, true);
```

---

## 5. 구현 중 마주친 문제

**"ESC가 전부 닫는" 경로가 둘이었다 (jsdom으로 닫힘 사유 기록).**

| 구조 | 로그 | 해석 |
|---|---|---|
| #2가 #1의 논리 자식(데모) | `#2 destroy` → `#1 escape` | 먼저 등록된 #1 리스너가 #1을 닫고, #2는 **연쇄**로 사라짐(#2 리스너는 이미 해제돼 호출 안 됨) |
| #1·#2가 형제 | `#1 escape`, `#2 escape` | 연쇄 없이 **두 리스너가 각자** 닫음 |

원인은 하나 — "맨 위인가" 확인 없음. 리스너들은 동시에가 아니라 **등록 순서대로** 실행된다(캡처·버블과 무관).

**`preventDefault`가 없으면 한 칸 더 간다.** `first.focus()` 직후 브라우저가 원래 하던 "다음 요소로 이동"을 마저 해서 두 번째 버튼으로 간다.

**알려진 한계였던 것(`ponytail:` 주석 — 아래에서 해소).** 모달 안에서 연 메뉴(portal)의 버튼은 DOM상 dialog 밖이라 Tab 순환에 포함되지 않는다.

**해소 — 메뉴 키보드 (2026-11-04, 커밋 [`c77eca7`](https://github.com/junhyeong9812/react-portal/commit/c77eca7)).**\
Tab 순환에 메뉴를 끼워 넣는 안(A — 논리 자손 portal의 요소까지 모아 순서를 직접 정함)은 "메뉴를 어느 버튼 다음에 끼울지" 규칙을 새로 만들어야 해서 고르지 않았다.\
대신 실무 방식(B)으로, **메뉴가 열리면 포커스를 메뉴 안으로** 옮기고 메뉴가 ↑↓·ESC·Tab을 직접 처리한다.\
충돌(모달의 document 캡처 리스너가 메뉴보다 먼저 키를 받음)은 **모달 스택을 오버레이 스택으로 일반화**해서 풀었다 — 모달·메뉴가 같은 스택에 쌓이고, 리스너 하나가 맨 위에게만 넘긴다. ESC "맨 위만"과 같은 원리의 확장이다.

```text
오버레이 스택 [모달, 메뉴]  →  ESC: 메뉴만 닫힘(모달 유지)
                           Tab: 메뉴 닫고 포커스 메뉴 버튼 → 같은 Tab을 모달에 넘김(onKey가 true 반환) → trapTab
                           바깥: 메뉴만 닫힘
```

테스트 `test/menu.test.js` 11개(K1~K7), 키 디스패치를 "맨 위 모달"로 되돌리면 3개 실패(변이 확인). 전체 49개 통과.

**jsdom은 Tab의 기본 이동을 흉내 내지 않는다.** 테스트는 "가장자리에서 개입했는가"만 검증하고, 가운데 이동은 실브라우저로 확인했다.

---

## 6. 결론

- 테스트 M2(ESC 맨 위부터)·M3(첫 포커스, 순환, 밖에서 복귀, 닫으면 복귀)로 고정.
- 클로저 관점: naive는 각 리스너가 **자기 모달**을 기억, 라이브러리는 리스너가 **공유 스택**을 본다.
- 개념 노트: [cs/web-platform/27-modal-dialog-behavior](../../../cs/web-platform/27-modal-dialog-behavior/) · [cs/language/07-scope-closures-first-class-functions](../../../cs/language/07-scope-closures-first-class-functions/)
