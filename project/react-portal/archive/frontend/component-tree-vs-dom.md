# Component Tree vs DOM

> **한 줄**: 프레임워크는 DOM과 **별개로** 컴포넌트의 논리 트리를 들고 있다. 평소엔 둘이 같은 모양이지만, **Portal은 둘을 의도적으로 가른다.** 어떤 동작이 어느 트리를 따르는지 구분하는 것이 핵심.

## 이해의 흐름 — 헷갈렸던 지점에서 시작하기

> 전체 노트: [N1 바깥 클릭](../learning/modal/n1-outside-click.md), [N3-② Tab](../learning/modal/n3-tab-trap.md)

### ① "N1은 DOM이 클릭 이벤트를 돌 때 mini-portal에 물어서 생긴 문제?"

이벤트가 **어디로 가느냐**는 두 버전이 같았다(둘 다 document 리스너가 같은 `e.target`을 받음). 다른 건 받은 **다음의 판정**이었다.

```text
질문: "이 버튼(메뉴 항목)이 모달 안쪽인가?"   ← 관계에 대한 질문

물리(DOM)에 물음 — dialog.el.contains(target)       논리에 물음 — n = n.parent 루프
  .mini-modal 아래 DOM 자식을 뒤짐                    메뉴 항목 → box → menu → 메뉴 열기 버튼
  메뉴는 body 쪽 다른 portal에 있음                     → row → dialog ✓ 만남
  → 없음 → "바깥" ✗                                 → "안쪽" ✓
```

**내가 정리한 한 줄**: "엘리먼트에게 직접 물어보니까 그냥 물리 노드를 타고 간 거구나."

| 누구에게 묻나 | 아는 것 | 묻는 방법 |
|---|---|---|
| 엘리먼트 (`dialog.el`) | DOM 관계만 | `el.contains(x)` |
| 노드 (`dialog`) | 논리 관계 | `n = n.parent` |

### ② 원칙 — 질문의 성격이 트리를 고른다

```text
           질문이 "위치"에 관한 것인가, "관계"에 관한 것인가?
                 │                                 │
               위치                               관계
   화면 어디 · CSS · 잘림 · Tab 순서        누구의 자식 · 이벤트를 누가 받나 · Context · 안쪽인가
                 │                                 │
             DOM 트리                           논리 트리
```

- N1 "이 클릭이 모달에 속하나" → 관계 → 논리
- N3-② "Tab이 다음에 어디로 가나" → 위치·순서(브라우저가 DOM 순서로 정함) → DOM

같은 "안쪽인가"라도 **무엇의 안쪽인지**에 따라 묻는 트리가 다르다.

## 두 트리

```
논리 트리 (컴포넌트)                  DOM 트리 (브라우저)
App                                  body
 └ Card                               ├ div#app
    └ Modal (portal)                  │  └ div.card
       └ Button                       └ div.modal-container   ← portal로 이동
                                         └ button
```

- **DOM 트리**: 브라우저가 화면을 그리는 실제 구조. `el.parentNode`.
- **논리 트리**: 프레임워크가 상태·이벤트·생명주기를 관리하는 구조. React에서는 **Fiber 트리**.

## 어떤 동작이 어느 트리를 따르나

| 동작 | 따르는 트리 | 이유 |
|---|---|---|
| 화면 위치, CSS 상속·선택자 | DOM | 브라우저가 그림 |
| stacking context, overflow 클리핑 | DOM | CSS 규칙 |
| **네이티브** 이벤트 버블링 | DOM | 브라우저가 흘림 |
| **프레임워크** 이벤트 버블링 (`onClick`) | 논리 | 프레임워크가 다시 흘림 |
| Context (`useContext`, provide/inject) | 논리 | 프레임워크가 조상을 찾음 |
| 생명주기 (언마운트, 정리) | 논리 | 부모가 사라지면 자식도 |

## Portal이 푸는 문제

모달이 논리적으로는 Card의 자식이어야 한다(Card의 상태·Context·이벤트를 써야 함). 그런데 DOM상 Card 안에 있으면 Card의 CSS에 갇힌다. → [stacking-context.md](stacking-context.md), [containing-block.md](containing-block.md)

- **DOM만 body로 옮기면**(`appendChild`): CSS 문제는 풀리지만 논리 관계도 끊긴다.
- **Portal**: DOM은 옮기고 논리 관계는 유지한다.

```jsx
// React
function Card() {
  return createPortal(<Modal />, document.body);   // DOM은 body, React 부모는 Card
}
```

## 흔한 착각: "다른 루트로 렌더링하면 되지 않나?"

```js
// Portal 대신 별도 루트를 만들어 렌더링
const container = document.createElement('div');
document.body.appendChild(container);
createRoot(container).render(<Modal />);   // 논리 트리도 새로 시작됨
```
- DOM은 옮겨지지만 **논리 트리가 별개**라서 Card의 Context를 못 읽고, `onClick`이 Card까지 안 올라가고, Card가 언마운트돼도 Modal은 남는다.
- Portal이 별도 API로 존재하는 이유가 이것이다.

## 이 프로젝트에서

- `src/node.js:8` — `parent`(논리)와 `domParent`(DOM)를 따로 받는다.
- 일반 노드: `domParent: parent.el` → 두 트리 일치 (`node.js:65`).
- portal: `domParent: target` → 두 트리 분리 (`src/portal.js`).
- 논리 트리를 타는 세 곳: `dispatch` 루프(`events.js:34`), `inject`(`node.js:38`), `destroy` 재귀(`node.js:52`) — 모두 `n.parent`/`children`을 쓴다.
- DOM 트리를 타는 곳: `nodeOf`(`registry.js`) — 시작 노드를 찾을 때만.

## 흔한 함정

- **portal 안 클릭이 부모 onClick까지 올라와서 놀람**: 의도된 동작(논리 버블링). 막으려면 portal 경계에서 `stopPropagation`.
- **CSS가 부모를 따라올 거라 기대**: portal 안 요소에는 DOM 부모의 CSS(상속 font, 하위 선택자 `.card .btn`)가 적용되지 않는다.
- **"바깥 클릭 시 닫기" 구현에서 portal 무시**: DOM의 `contains`로 판정하면 portal 안 클릭을 "바깥"으로 오인한다.
