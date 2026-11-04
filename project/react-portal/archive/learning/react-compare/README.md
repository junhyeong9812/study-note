# React createPortal 비교 — 학습 노트

> 대상: `react.html`, `demo/react/compare.js`, `test/react-compare.test.js` · 작성: 2026-11-04
> 미니 Portal로 흉내 낸 원리가 실제 React에서도 똑같이 성립하는지, 그리고 Portal 대신 "별도 루트로 렌더"하면 무엇이 깨지는지.

## 비교 상황

두 카드는 똑같다: `ThemeContext.Provider value="dark"` + 카드 `onClick`. 콘텐츠를 내보내는 방식만 다르다.

```js
// 진짜 portal — demo/react/compare.js RealPortal
return createPortal(children, container);

// 가짜 portal — demo/react/compare.js FakePortal
const r = createRoot(el);   // container 안에 "새 React 루트"
r.render(children);
```

## 결과 (테스트 R1~R3, 페이지 스모크로 확인)

| | 진짜 (`createPortal`) | 가짜 (`createRoot`) |
|---|---|---|
| R3 콘텐츠 DOM 위치 | 카드 밖 (`#real-target`) | 카드 밖 (`#fake-target`) — **같음** |
| R1 `useContext(ThemeContext)` | `"dark"` (카드가 제공한 값) | `"light"` (**기본값** — Provider를 못 찾음) |
| R2 안쪽 버튼 클릭 → 카드 `onClick` | 호출됨 | **호출 안 됨** |
| 안쪽 버튼 자기 `onClick` | 호출됨 | 호출됨 |

**DOM 위치는 똑같다.** 차이는 전부 **React 트리(Fiber 트리)** 에서 생긴다.

```
진짜                                   가짜
React 트리 (하나)                       React 트리 A          React 트리 B (새 루트)
Provider(dark)                          Provider(dark)        PortalContent  ← 부모가 없음
 └ Card(onClick)                         └ Card(onClick)
    └ Portal                                └ FakePortal (null 렌더)
       └ PortalContent ← 부모 체인 유지
```

## 미니 Portal과의 대응

| 개념 | 미니 Portal (`src/`) | React |
|---|---|---|
| 논리 트리 | `node.parent` | Fiber 트리 (`return` 포인터) |
| DOM과 논리 분리 | `new Node({ parent, domParent: target })` | `createPortal(children, container)` |
| Context 조회 | `inject` — `n.parent`로 올라감 | `useContext` — Fiber 조상의 Provider |
| 이벤트 위임 | 루트·portal 컨테이너에 `dispatch` | 루트 컨테이너(+ portal 컨테이너)에 React 리스너 |
| 논리 버블링 | `dispatch` 루프 `n = n.parent` | 합성 이벤트를 Fiber 트리 따라 전파 |
| 합성 이벤트 | `{ target: 노드, stopPropagation… }` | `SyntheticEvent` (`e.nativeEvent`) |
| "가짜 portal" 실수 | DOM만 `appendChild` | 별도 `createRoot` |

1·2단계에서 손으로 만든 장치가 React 안에 각각 대응한다. 그래서 React에서도 같은 결과가 나온다.

## 관찰: 가짜인데 버튼 onClick은 왜 동작하나

`onLog`는 **prop으로 넘긴 함수**다. 함수는 참조로 전달되고, 그 함수가 기억하는 변수(클로저)는 어느 트리에서 실행되든 살아 있다. → [closures](../../frontend/closures.md), [reference-vs-copy](../../frontend/reference-vs-copy.md)

정리하면:
- **값을 직접 넘긴 것**(props, 함수 참조)은 트리가 끊겨도 동작한다.
- **트리를 따라 찾는 것**(Context, 이벤트 버블링, 언마운트 연쇄)만 끊긴다.

가짜 portal을 써도 겉보기엔 "대충 동작"한다. 그래서 이 실수는 Context를 쓰거나 부모가 클릭을 받아야 할 때가 돼서야 드러난다.

## 가짜 portal 구현에서 만난 것

```js
return () => {
  setTimeout(() => { r.unmount(); el.remove(); });   // 다음 틱으로 미룸
};
```
- React는 **렌더(또는 커밋) 도중에 다른 루트를 동기적으로 unmount**하면 경고한다. effect cleanup은 부모 루트의 커밋 중에 실행되므로 지연시킨다.
- 이것도 가짜 portal의 비용이다. 진짜 portal은 같은 트리라서 부모와 함께 자연스럽게 정리된다.

## 테스트 읽는 법 (React 쪽 추가분)

```js
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
await act(async () => root.render(...));
```
- `act()`: React가 예약해 둔 렌더·effect를 **모두 끝낸 뒤** 다음 줄로 넘어가게 한다. 가짜 portal은 effect 안에서 두 번째 루트를 렌더하므로, `act` 없이 검사하면 아직 아무것도 안 그려져 있다.
- `IS_REACT_ACT_ENVIRONMENT`: "여기는 테스트 환경"이라고 알려서 act 관련 경고를 정확히 낸다.

### 변이 점검
가짜를 `RealPortal`로 바꾸면 "가짜는 light", "가짜는 카드 onClick에 안 닿음" 테스트 2개가 실패한다. 테스트가 두 방식의 차이를 실제로 구분한다.

## 페이지에서 확인

`npm run dev` → `http://localhost:5173/react.html`
1. 아래 두 점선 영역(카드 밖)에 각 portal의 콘텐츠가 그려진다.
2. 진짜 쪽은 `"dark"`, 가짜 쪽은 `"light"`.
3. 각 "안쪽 버튼" 클릭 → 진짜는 로그 2줄(버튼 + Card), 가짜는 1줄(버튼만).
