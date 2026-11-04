# N3-② Tab이 빠져나간다 — 포커스를 모달 안에 가두기

> 데모: "문제 재현" → **N3 ESC 전체 닫힘 · Tab 탈출** 켜기 → Portal 모달 열기 → Tab 연타
> 증상: 포커스 테두리가 모달 버튼 4개를 지난 뒤 브라우저 UI(주소창 등)로 빠지고, 다음 Tab에서 **배경 뒤의 페이지 버튼**으로 들어간다. 그 상태에서 Enter → 보이지 않는 뒤쪽 버튼이 눌린다.
> ESC 부분(N3-①)은 [n3-escape-top-only.md](n3-escape-top-only.md)

## 한 문장

**Tab은 DOM 순서로 움직이고 모달이 화면 위에 있다는 걸 모른다.** 그래서 모달 끝에서 Tab(처음에서 Shift+Tab)을 누르면 포커스가 브라우저 UI나 뒤쪽 페이지로 빠져나간다. `trapTab`은 **끝에서만** 기본 이동을 취소(`preventDefault`)하고 **반대쪽 끝으로 돌려보내** 포커스를 모달 안에 가둔다.

## 왜 빠져나가나 — 브라우저는 화면이 아니라 DOM 순서를 본다

```
DOM 순서 (body 위 → 아래)
  [일반 자식 모달 열기] [Portal 모달 열기]     ← #app 안 (어두운 배경 뒤)
  [체크박스 ×4] [지우기]                       ← 배경 뒤
  [안쪽 버튼] [메뉴 열기] [또 열기] [닫기]      ← body 끝의 모달
                                    │ Tab
                                    ▼
             다음 요소 없음 → 브라우저 UI(주소창 등) → 다시 문서 처음 [일반 자식 모달 열기] …
```

- 어두운 배경(오버레이)은 **마우스만 막는다.** 키보드 포커스는 막지 못한다.
- 마우스 사용자는 못 누르는 뒤쪽 버튼을 키보드·스크린 리더 사용자는 누를 수 있게 된다 → 접근성 결함이자 오작동 원인.

## 라이브러리: 끝에서만 반대쪽으로 넘겨 주기

```js
// src/modal.js:54-76
function trapTab(e, modal) {
  const dialogEl = modal.dialog.el;
  const items = focusables(modal);       // dialog 안의 포커스 가능 요소 (DOM 순서)
  if (items.length === 0) {              // 하나도 없으면 dialog 자체에 머무름
    e.preventDefault();
    dialogEl.focus();
    return;
  }
  const first = items[0];
  const last = items[items.length - 1];
  const active = document.activeElement; // 지금 포커스가 있는 요소
  const inside = dialogEl.contains(active);
  // 가장자리에서만 개입한다. 중간 이동은 브라우저 기본 Tab 동작에 맡긴다.
  if (e.shiftKey) {
    if (!inside || active === first || active === dialogEl) {
      e.preventDefault();                // 브라우저의 기본 이동 취소
      last.focus();                      // 처음에서 Shift+Tab → 마지막으로
    }
  } else if (!inside || active === last) {
    e.preventDefault();
    first.focus();                       // 마지막에서 Tab → 처음으로
  }
}
```

```
Tab 키 → document 캡처 keydown → onKeyDown → (맨 위 모달) trapTab
   지금 포커스가 마지막인가? (또는 모달 밖인가?)
     예     → preventDefault() + first.focus()
     아니오 → 아무것도 안 함 → 브라우저가 평소처럼 다음 요소로

Tab:        [안쪽 버튼] → [메뉴 열기] → [또 열기] → [닫기] ─┐
               ↑   (가운데는 브라우저 기본 이동)              │
               └─────────────────────────────────────────────┘
Shift+Tab:  [안쪽 버튼] ─→ last.focus() = [닫기]   (반대 방향 같은 원리)
```

| 요소 | 역할 |
|---|---|
| `preventDefault()` | 없으면 `first.focus()` **직후에** 브라우저가 원래 하던 "다음 요소로 이동"을 마저 해서 두 번째 버튼으로 가 버린다 |
| 가운데는 안 건드림 | 가운데까지 직접 구현하면 `tabindex` 순서·숨김 요소 등 브라우저 규칙을 다시 만들어야 한다. 끝에서만 넘기면 충분 |
| `!inside` | 마우스로 뒤쪽을 클릭하는 등 포커스가 모달 밖에 있으면 다음 Tab에서 안으로 되돌린다 |
| `active === dialogEl` | 포커스할 버튼이 없어 dialog 자체에 포커스가 있을 때의 Shift+Tab |
| 캡처 + 맨 위만 | `onKeyDown`은 document **캡처**(앱의 stopPropagation과 무관) + `top()` 모달에만 적용 → [event-capture](../../frontend/event-capture.md) |

## naive: 아예 부르지 않는다

```js
// demo/naive-modal.js:82-84
    } else if (e.key === 'Tab' && !bugs.escAllNoTrap && isTop()) {   // N3 켜짐 → false
      trapTab(e, dialog.el);                                          // → 안 불림
    }
```

`trapTab`이 없으니 매번 브라우저 기본 이동 → 끝에서 밖으로 나간다.

## 질문: N1에선 "안쪽인가"를 DOM에 물으면 틀렸는데, 여기선 왜 DOM(`contains`, `querySelectorAll`)인가?

**지금 다루는 대상이 Tab 순서이고, Tab 순서는 DOM(물리) 트리가 정하기 때문이다.**

- 브라우저가 Tab으로 다음 요소를 고를 때 보는 건 **DOM 순서**다. 우리의 논리 트리(`node.parent`)는 모른다.
- 그러니 "Tab으로 갈 수 있는 요소가 어디 있고, 처음·마지막이 무엇인가"는 **위치(DOM)에 대한 질문**이다. → DOM에 묻는 게 맞다.
- N1의 "이 클릭이 모달 안쪽인가"는 **관계**에 대한 질문이라 논리 트리에 물어야 했다.

| 질문 | 성격 | 묻는 트리 |
|---|---|---|
| 이 클릭이 모달에 속하나 (N1) | 관계 | 논리 |
| Tab이 다음에 어디로 가나 (N3-②) | 위치·순서 | DOM |

### 그 대가 — 알려진 한계였던 것 (당시 `src/modal.js:44-45` `ponytail:` 주석 · 2026-11-04 PR #4에서 해소 → 아래)

```js
// ponytail: 포커스 순환 범위는 dialog의 DOM 서브트리뿐. dialog 안에서 연 비모달 portal(드롭다운 등)의
// 포커스 요소는 Tab 순환에 포함되지 않는다. 필요하면 논리 자손 portal의 el까지 모아 정렬하도록 확장.
```

- 모달 안에서 연 **메뉴의 "메뉴 항목"** 은 논리적으로는 모달의 자손이지만, DOM상 body 쪽 다른 portal에 있다.
- 그래서 `querySelectorAll`(DOM)로 모은 `items`에 **들어가지 않는다** → Tab 순환에 포함되지 않는다.
- 메뉴 항목에 포커스가 있는 상태에서 Tab을 누르면 `!inside`가 되어 모달의 첫 버튼으로 돌아간다.
- 확장하려면 "dialog DOM + 논리 자손 portal들의 el"을 모아 순서를 정해야 한다. 순서 규칙(메뉴를 어느 버튼 다음에 끼울지)을 직접 정해야 해서 이번 범위에서는 단순화했다. 실무 라이브러리들은 메뉴가 열리면 포커스를 메뉴 안으로 옮기고 메뉴 자체에서 키보드를 처리하는 식으로 푼다.

### 해소 — 메뉴가 포커스를 받고 자기 키를 처리한다 (PR #4)

Tab 순환에 메뉴를 끼워 넣는 대신, 실무 라이브러리처럼 **메뉴가 열리면 포커스를 메뉴 안으로** 옮기고 메뉴가 키를 직접 처리하게 했다(`src/menu.js` `createMenu`).

```text
모달 위에 메뉴가 열림 → 오버레이 스택: [모달, 메뉴]   (src/overlay-stack.js — 모달 스택을 일반화)
document 리스너 하나 → 맨 위(메뉴)에게만 키·바깥 클릭을 넘김

  ↑ / ↓   메뉴 항목 사이 이동 (끝에서 반대쪽)
  ESC     메뉴만 닫고 메뉴 버튼으로 포커스 복귀 — 모달은 그대로
  Tab     메뉴를 닫고 포커스를 메뉴 버튼으로 → 같은 Tab을 다음 맨 위(모달)에 넘김
          → 모달의 trapTab이 이어서 처리 (버튼이 마지막이면 처음으로 순환)
  바깥    메뉴만 닫힘 (모달 안을 눌러도, 모달 배경을 눌러도)
```

- 핵심은 N3-①과 같은 원리의 확장이다: **맨 위 하나만 반응**한다. 맨 위가 모달이면 모달이, 메뉴면 메뉴가.
- `onKey(e)`가 `true`를 돌려주면 "나는 닫혔으니 같은 키를 아래로 넘겨라" — Tab처럼 두 오버레이가 한 키를 이어서 처리할 때 쓴다.
- 테스트: `test/menu.test.js` K1~K7. 키 디스패치를 "맨 위 모달"로 되돌리면 K2·K3·K5가 실패(변이 확인).
- 실브라우저 확인 필요: 메뉴에서 Tab을 눌렀을 때 브라우저 기본 이동이 메뉴 버튼 **다음** 요소로 가는지(jsdom은 Tab 기본 이동을 흉내 내지 않음).

## 함께 하는 일: 열 때·닫을 때 포커스

| 시점 | 동작 | 코드 |
|---|---|---|
| 열 때 | 열기 전 포커스(`document.activeElement`) 기억 | `previousFocus` |
| 연 직후 | dialog의 첫 포커스 요소로 이동(없으면 dialog 자체 — `tabIndex = -1`) | `queueMicrotask(...)` |
| 닫을 때 | 기억해 둔 요소로 복귀(문서에 남아 있으면) | 클린업의 `previousFocus.focus()` |

열자마자 포커스를 안으로 옮기지 않으면, 첫 Tab이 "여는 버튼 다음 요소"(뒤쪽 페이지)부터 시작한다. 닫을 때 복귀하지 않으면 포커스가 body로 떨어져 키보드 사용자가 위치를 잃는다.

## 테스트

`test/modal.test.js` — M3:
- "열면 dialog의 첫 포커스 요소로 이동한다"
- "Tab은 마지막 → 처음, Shift+Tab은 처음 → 마지막으로 순환한다"
- "포커스가 dialog 밖에 있으면 Tab이 dialog 안으로 되돌린다"
- "닫으면 열기 전 포커스 요소로 돌아간다"

jsdom은 Tab 키의 **기본 이동**을 흉내 내지 않는다. 그래서 테스트는 "가장자리에서 우리가 개입했는가"만 검증하고, 가운데 이동은 실브라우저에서 확인한다.
