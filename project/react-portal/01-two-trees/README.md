# 01 — 두 트리: 논리 부모와 DOM 부모를 따로 들기

- 커밋: [`d76cf08`](https://github.com/junhyeong9812/react-portal-lab/commit/d76cf08) (노드·portal·레이어) · [PR #1](https://github.com/junhyeong9812/react-portal-lab/pull/1)
- 학습 노트: [archive/learning/pr1/01-my-understanding.md](../archive/learning/pr1/01-my-understanding.md)

---

## 1. 무엇이 문제였나

React의 `createPortal`이 "어떻게 동작하는지"를 직접 흉내 내 보고 싶었다.\
처음 질문은 "Portal은 z-index를 활용하는 기능 같은데?"였다.

알고 보니 순서가 반대였다.\
부모가 쌓임 맥락(stacking context)을 만들면 자식의 `z-index: 9999`는 **부모 층 안에서만** 비교된다.\
부모가 `overflow: hidden`이면 밖으로 나간 부분은 잘린다.\
그래서 숫자를 키우는 것으로는 못 이기고, **DOM을 부모 밖(body)으로 옮겨야** 한다.

그런데 DOM만 옮기면(`appendChild`) 원래 부모와의 관계도 끊긴다.\
모달은 여전히 카드의 상태·Context·클릭 처리를 이어받아야 한다.\
즉 풀어야 할 문제는 "**DOM 위치는 옮기되, 논리 관계는 원래 자리에 남긴다**"였다.

> **쌓임 맥락(stacking context)** — z-index가 비교되는 범위. 부모가 만들면 자식의 z-index는 그 안에서만 의미가 있다.\
> 예: `z-index: 1`인 카드 안의 `z-index: 9999` 모달은 `z-index: 2`인 헤더 아래에 깔린다.

---

## 2. 무엇을 고민했나

**안 1 — React 위에 바로 만들기.**\
`createPortal`을 쓰면 몇 줄이면 된다.\
하지만 핵심 원리(논리 관계 유지)를 React가 대신 해 버려서, 배우려던 것이 보이지 않는다.

**안 2 — 순수 JS로 DOM만 body에 붙이기.**\
stacking context 탈출은 재현된다.\
하지만 순수 JS에는 "DOM과 다른 논리 트리"라는 개념이 없어서, 옮기는 순간 관계가 끊긴다 — Portal의 절반만 만든 셈이다.

**안 3 — 순수 JS + 미니 논리 트리.**\
모든 컴포넌트가 논리 부모 참조를 들고, 이벤트·Context·정리를 그 참조로 처리한다.\
React가 내부(Fiber 트리)에서 하는 일을 직접 만드는 것이라 비용은 크지만, 원리가 코드로 드러난다.

→ **안 3을 골랐다.** 비교용으로 React 버전은 나중에 따로 만들었다([06](../06-react-compare/README.md)).

---

## 3. 그래서 이렇게

노드를 만들 때 **논리 부모(`parent`)와 DOM을 붙일 곳(`domParent`)을 따로** 받는다.\
일반 노드는 둘이 같고, portal만 둘이 갈라진다.

```text
논리 트리 (node.parent)              DOM 트리 (el.parentNode)
root                                 body
 └ card                               ├ #app
    └ portal  ←──── 같은 노드 ────→   │  └ .mini-root
       └ button                       │     └ .card
                                      └ .mini-portal   ← portal만 여기로
                                         └ button
```

| 만드는 함수 | domParent | 결과 |
|---|---|---|
| `createRoot(container)` | `container` | 시작점 |
| `createNode(parent, …)` | `parent.el` | 논리 부모 = DOM 부모 |
| `createPortal(parent, target)` | `target`(기본 body) | **둘이 갈라짐** |

| 따르는 트리 | 동작 |
|---|---|
| DOM | 화면 위치, CSS(쌓임 맥락·overflow), 브라우저의 네이티브 버블링 |
| 논리 | 컴포넌트 핸들러 실행 순서, Context(`inject`), 정리(`destroy`) |

---

## 4. 코드 — 실제 커밋에서

`src/node.js` (`d76cf08`) — 두 트리에 동시에 연결하는 생성자.

```js
export class Node {
  constructor({ el, parent = null, domParent = null, on = {} }) {
    this.el = el;
    this.parent = parent;
    this.children = new Set();
    this.handlers = { ...on };
    this.contexts = new Map();
    this.cleanups = [];
    this.destroyed = false;

    register(el, this);
    if (parent) parent.children.add(this);
    if (domParent) domParent.appendChild(el);
  }
```

`src/portal.js` (`d76cf08`) — 일반 노드와의 차이는 `domParent: target` 한 줄.

```js
export function createPortal(parent, target = document.body, { on } = {}) {
  const el = document.createElement('div');
  el.className = 'mini-portal';
  // z-index가 적용되려면 positioned 요소여야 한다.
  el.style.position = 'relative';

  const portal = new Node({ el, parent, domParent: target, on });
  portal.isPortal = true;

  pushLayer(el);
  portal.onCleanup(() => removeLayer(el));
  return portal;
}
```

- `register(el, this)`: DOM 요소 → 노드 역방향 연결(WeakMap). 이벤트 위임에서 "어느 노드가 클릭됐나"를 찾는 다리([02](../02-event-delegation/README.md)).
- `pushLayer` / `removeLayer`: portal 컨테이너는 모두 body 직속이라, 열린 순서대로 `1000 + i`를 매기면 같은 층에서 공정하게 비교된다.
- `onCleanup`: 획득한 쪽이 해제도 예약한다 — `destroy()` 때 역순(스택)으로 실행.

---

## 5. 구현 중 마주친 문제

**데모가 "갇힘"을 재현하지 못했다.**\
처음 데모 카드는 `overflow: hidden`만 있었는데, 모달 오버레이가 `position: fixed`라 **잘리지 않았다.**\
fixed 요소의 기준 상자는 보통 뷰포트라서, 조상의 overflow 클리핑을 받지 않는다.\
카드에 `transform: translateZ(0)`을 추가하자 fixed의 기준이 카드가 되어 잘렸다(커밋 [`e4ee6e5`](https://github.com/junhyeong9812/react-portal-lab/commit/e4ee6e5)).\
→ 실무에서 흔한 함정(애니메이션·GPU 가속용 transform)을 그대로 재현하는 데모가 됐다.

> **containing block** — 요소의 위치·% 크기를 계산하는 기준 상자. fixed는 보통 뷰포트지만, 조상에 transform 등이 있으면 그 조상이 된다.

**헷갈렸던 이해 (학습 Q&A에서).**
- "`createElement`로 만든 요소도 어딘가 등록되는 거 아니야?" → 아니다. 메모리에만 있다가 `appendChild` 순간에만 트리에 들어간다. 만드는 것과 붙이는 것이 별개라서 Portal이 가능하다.
- "`domParent`는 화면 전체를 그리는 큰 DOM?" → 노드마다 **바로 위에 붙을 요소 하나**다.
- "destroy는 역순으로 자식부터?" → 자식은 추가 순서대로, 하지만 **재귀**라서 결과적으로 맨 아래부터 끝난다. 클린업만 역순(스택).

---

## 6. 결론

- 노드 생성자 한 곳에서 `parent`와 `domParent`를 분리한 것이 Portal 전체다.
- 테스트 I1(DOM 이동)·I6(레이어 순서)로 고정. 이후 모든 기능(이벤트·Context·모달)이 이 분리 위에 섰다.
- 개념 노트: [cs/web-platform/26-portals-and-two-trees](../../../cs/web-platform/26-portals-and-two-trees/) · [cs/web-platform/25-stacking-context-and-containing-block](../../../cs/web-platform/25-stacking-context-and-containing-block/)
