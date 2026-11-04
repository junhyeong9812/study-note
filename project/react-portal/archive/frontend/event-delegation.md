# Event Delegation

> **한 줄**: 요소마다 리스너를 달지 않고 **상위 컨테이너 하나**에 리스너를 달아, 버블링으로 올라온 이벤트를 받아서 해당 요소의 처리로 나눠 주는 방식. React의 이벤트 시스템이 이렇게 동작한다.

## 이해의 흐름 — 헷갈렸던 지점에서 시작하기

> 전체 Q&A: [03-internals-qa Q15·Q17~Q20](../learning/pr1/03-internals-qa.md)

### ① "`createNode(… on: { click })`에서 클릭 이벤트가 등록되는 거지?"

**등록이 두 종류다.** 이 구분이 이벤트 위임 전체를 푸는 열쇠였다.

```text
                     무엇을          어디에                    언제
브라우저 리스너        dispatch        .mini-root / .mini-portal   root 생성 1번, portal 열 때마다
  (addEventListener)                  "요소"에                    (listen → events.js:45)

우리 핸들러           on의 함수        노드 "객체"의 handlers      모든 createNode
  (메모만 해 둠)                       필드에                     (node.js:12)

버튼 <button> 자체에는 브라우저 리스너가 하나도 없다.
```

### ② "그럼 dispatch는 뭐야?"

```text
브라우저 ──호출──▶ dispatch(native)    ← 브라우저 입장: 평범한 리스너 하나
                      │
                      ├ nodeOf(native.target)       어느 노드에서 일어났나
                      └ for (n = start; n; n = n.parent)
                          n.handlers[native.type]?.(event)   메모해 둔 함수를 꺼내 실행

= 브라우저와 논리 트리 사이의 "교환원"
```

### ③ "`'click'` 하나로 어떻게 이어지는 거야?"

```text
EVENT_TYPES = ['click', …]        ① 브라우저에 "이 타입 오면 알려줘" (listen이 등록)
on: { click: fn }                 ② key로 동작 매핑 → node.handlers
n.handlers[native.type]           ③ 받은 이벤트의 type('click')으로 꺼내 실행

①과 ②의 이름이 안 맞으면(예: mouseover) ③까지 못 감 → 생성자 경고가 잡는다
```

### ④ "portal 리스너 등록 코드는 main.js 어디 있어?"

**main.js에는 안 보인다.** `createPortal` 안(`portal.js` `portal.onCleanup(listen(el))`)에 숨어 있다 — 쓰는 쪽은 `createPortal`만 부르면 된다(React의 `createPortal`과 같은 감춤).

## 왜 쓰나

| 요소마다 리스너 | 위임 |
|---|---|
| 요소 1000개 → 리스너 1000개 | 리스너 1개 |
| 나중에 추가된 요소는 따로 등록해야 함 | 나중에 추가돼도 자동으로 처리 |
| 요소 제거 시 리스너 정리 필요 | 컨테이너 하나만 관리 |

## 순수 DOM에서의 기본형

```js
list.addEventListener('click', (e) => {
  const item = e.target.closest('li');     // ① 어디서 일어났나 (target에서 위로)
  if (!item || !list.contains(item)) return;
  handle(item);                             // ② 해당 항목 처리로 배분
});
```

## 프레임워크가 하는 일 (React)

React의 `onClick`은 실제 `<button>`에 `addEventListener`되지 **않는다.**

```
[등록 시]
<button onClick={fn}>   →  fn은 React 내부의 컴포넌트(Fiber) 정보에 저장만 됨
                           브라우저 리스너는 루트 컨테이너에 이벤트 타입별로 미리 달아 둠

[클릭 시]
브라우저 → 루트 컨테이너의 React 리스너 호출
         → React가 target에서 해당 Fiber를 찾고
         → Fiber 트리를 따라 올라가며 onClick들을 실행 (합성 이벤트를 넘겨서)
```

- **합성 이벤트(SyntheticEvent)**: React가 네이티브 이벤트를 감싸서 만든 객체. 원본은 `e.nativeEvent`.
- **리스너 위치의 변화**: React 16까지는 `document`, **17부터는 루트 컨테이너**(`createRoot`에 넘긴 요소). 한 페이지에 React 앱이 여러 개이거나 다른 라이브러리와 섞일 때 간섭을 줄이기 위해 바뀌었다.
- **Portal**: portal 컨테이너는 루트 밖에 있을 수 있으므로 React는 거기에도 리스너를 단다. 그리고 버블링은 DOM이 아니라 **Fiber 트리**를 따른다 → portal 안 클릭이 React 부모의 `onClick`까지 올라간다.

## 이 프로젝트에서 (React 흉내)

```
[등록]  createNode(..., { on: { click: fn } })   → node.handlers에 저장만   (node.js:12)
        createRoot / createPortal                 → listen(el): 컨테이너에 dispatch 등록 (events.js:45)

[클릭]  브라우저 → 컨테이너의 dispatch(native)
        dispatch → nodeOf(native.target)          시작 노드 찾기   (events.js:15)
                 → n = n.parent 로 올라가며        논리 트리 버블링 (events.js:34)
                   n.handlers[native.type] 실행
```

- `'click'` 문자열이 세 곳을 잇는다: `EVENT_TYPES`(등록 목록) ↔ `on`의 key ↔ `native.type`.
- 목록에 없는 타입은 dispatch가 불리지 않는다 → 생성자에서 경고 (`node.js:19-23`).
- 컨테이너가 겹치면(portal target이 루트 안) 같은 이벤트를 두 번 받는다 → `handled` WeakSet으로 1회만 (`events.js:9-13`).

## 흔한 함정

- **버블링하지 않는 이벤트는 위임 불가**: `focus`, `mouseenter` 등. `focusin`, `mouseover`로 대체. → [event-flow.md](event-flow.md)
- **중간에서 stopPropagation**: 컨테이너까지 못 올라와서 위임 핸들러 전체가 먹통이 된다.
- **React + 네이티브 리스너 혼용**: `document`에 단 네이티브 리스너와 React 핸들러의 실행 순서가 React 버전마다 다르다(17에서 변경). 섞을 땐 순서를 테스트로 확인.
- **e.target을 그대로 비교**: 안쪽 요소일 수 있다. `closest` 또는 등록 요소 탐색.
