# 02 — 이벤트 위임: 브라우저는 DOM으로 잡고, 핸들러는 논리 트리로 돈다

- 커밋: [`3a7d496`](https://github.com/junhyeong9812/react-portal/commit/3a7d496) (위임·논리 버블링·Context) · [`dcbb229`](https://github.com/junhyeong9812/react-portal/commit/dcbb229) (미지원 타입 경고) · [PR #1](https://github.com/junhyeong9812/react-portal/pull/1)
- 학습 노트: [archive/learning/pr1/03-internals-qa.md](../archive/learning/pr1/03-internals-qa.md) Q12~Q21 · [04-remaining-code.md](../archive/learning/pr1/04-remaining-code.md)

---

## 1. 무엇이 문제였나

DOM을 body로 옮긴 portal 안에서 버튼을 누르면, 그 클릭이 **원래 부모(카드)의 클릭 처리**까지 올라가야 한다.\
React에서 portal 안 클릭이 React 부모의 `onClick`까지 올라가는 것과 같은 동작이다.

그런데 브라우저의 버블링은 **DOM 경로**를 따른다.\
portal 안 버튼의 경로는 `button → … → .mini-portal → body → document`이고, 카드와 `#app`은 그 길에 없다.\
즉 브라우저에게 맡기면 카드는 그 클릭을 영원히 모른다.

---

## 2. 무엇을 고민했나

**안 1 — 버튼마다 `addEventListener`.**\
브라우저 버블링에 그대로 실린다 → DOM 경로를 따르니 논리 부모에 못 닿는다. 기각.

**안 2 — 받은 이벤트를 논리 부모 요소에 `dispatchEvent`로 재전파.**\
구현은 쉽지만, 재전파된 이벤트가 그 요소의 DOM 경로로 또 버블되어 순서가 꼬이고, "논리 트리를 따라 돈다"는 원리가 드러나지 않는다.

**안 3 — 루트 이벤트 위임 (React 방식).**\
버튼에는 아무것도 안 달고, **컨테이너(루트·portal)에만** 브라우저 리스너 `dispatch`를 단다.\
`dispatch`가 클릭된 DOM에서 노드를 찾고, 그 노드부터 `n.parent`로 올라가며 핸들러를 실행한다.

→ **안 3.** React 17+도 루트 컨테이너(+ portal 컨테이너)에 리스너를 단다.

---

## 3. 그래서 이렇게

```text
[등록]  createNode(…, { on: { click: fn } })  → node.handlers에 "저장만"   (브라우저 등록 아님)
        createRoot / createPortal             → listen(el): 컨테이너에 dispatch 등록

[클릭]  ─ 단계 1: 브라우저 (DOM 경로) ─────────────────────────────
        button → … → .mini-portal  ← 여기 dispatch가 있음 → 브라우저가 dispatch(native) 호출
        ─ 단계 2: dispatch (논리 트리) ───────────────────────────
        nodeOf(native.target)            클릭된 DOM → 시작 노드
        for (n = start; n; n = n.parent) n.handlers[native.type]?.(event)
        → button → portal → card → root
```

| 등록 종류 | 무엇을 | 어디에 | 언제 |
|---|---|---|---|
| 브라우저 리스너 | `dispatch` | `.mini-root`, `.mini-portal` **요소** | root 생성 1번, portal **열 때마다** |
| 우리 핸들러 | `on`의 함수 | 노드 **객체**의 `handlers` | 모든 노드 생성 시 |

portal 컨테이너는 루트 DOM 밖이라, **portal에도 `listen`을 따로** 달아야 단계 1에서 잡을 수 있다.

---

## 4. 코드 — 실제 커밋에서

`src/events.js` (`3a7d496`)

```js
// 같은 네이티브 이벤트가 중첩된 컨테이너(예: portal target이 루트 안)에서
// 두 번 디스패치되지 않도록 표시한다.
const handled = new WeakSet();

function dispatch(native) {
  if (handled.has(native)) return;
  handled.add(native);

  const start = nodeOf(native.target);
  if (!start) return;

  let stopped = false;
  const event = {
    type: native.type,
    nativeEvent: native,
    target: start,
    currentTarget: null,
    stopPropagation() {
      stopped = true;
      native.stopPropagation();
    },
    preventDefault() {
      native.preventDefault();
    },
  };

  // 핵심: DOM 부모가 아니라 논리 부모(n.parent)를 따라 올라간다.
  for (let n = start; n && !stopped; n = n.parent) {
    const handler = n.handlers[native.type];
    if (handler) {
      event.currentTarget = n;
      handler(event);
    }
  }
}

// container에 위임 리스너를 달고, 해제 함수를 돌려준다.
export function listen(container) {
  for (const type of EVENT_TYPES) container.addEventListener(type, dispatch);
  return () => {
    for (const type of EVENT_TYPES) container.removeEventListener(type, dispatch);
  };
}
```

- **합성 이벤트**: `target`이 DOM 요소가 아니라 노드. `stopPropagation()`이 클로저로 `stopped`를 바꿔 **우리 루프도** 멈춘다(브라우저의 stopPropagation만으로는 우리 루프가 안 멈춘다).
- **`handled`(WeakSet)**: portal target이 루트 안이면 같은 이벤트 객체가 dispatch 두 곳에 도착한다 → 한 번만 처리. 사용자가 두 번 클릭하면 이벤트 객체가 둘이라 둘 다 처리된다(연타 방지가 아님).
- **`'click'` 한 문자열**이 `EVENT_TYPES`(등록) ↔ `on`의 key ↔ `native.type`(꺼낼 때)을 잇는다.

---

## 5. 구현 중 마주친 문제

**미지원 이벤트 타입이 조용히 무시됐다.**\
`on: { mouseover }`처럼 `EVENT_TYPES`에 없는 타입을 넣으면 dispatch가 불리지 않아 에러 없이 영영 실행되지 않았다(머지 전 반증 질문에서 발견).\
노드 생성자에서 경고하도록 고쳤다(`dcbb229`).

**테스트가 진짜 결함을 잡는지 변이로 확인했다.**
- 루프를 `n = nodeOf(n.el.parentNode)`(DOM 기준)로 바꾸면 → 논리 버블링 테스트 4개 실패.
- `handled` 가드를 지우면 → 2개 실패("1번이어야 하는데 2번").

**헷갈렸던 이해.**
- "브라우저가 DOM을 따라 **처리 방법을 찾는다**?" → 브라우저는 경로의 리스너를 **부를 뿐**, 핸들러를 찾아 실행하는 건 단계 2.
- "app 밖이라 portal 이벤트를 app이 못 받는다?" → 단계 1(브라우저 리스너)에서만 맞다. 단계 2에서 card·root 핸들러는 정상 실행.
- "미니루트에서 처리됐으면 버블링이 멈춰야지?" → 네이티브 버블링은 처리 여부와 무관하게 끝까지 간다(이 성질이 [03](../03-outside-click/README.md)의 N2를 만든다).

---

## 6. 결론

- 테스트 I2(논리 버블링, "형제의 DOM 안에 portal을 넣어 DOM 조상 ≠ 논리 조상" 케이스 포함)·I3(stopPropagation)·I5(Context)로 고정.
- 개념 노트: [cs/web-platform/04-dom-and-event-model](../../../cs/web-platform/04-dom-and-event-model/) · [cs/web-platform/26-portals-and-two-trees](../../../cs/web-platform/26-portals-and-two-trees/)
- 한계: 위임하는 이벤트는 `click`·`input`·`keydown` 세 가지뿐.
