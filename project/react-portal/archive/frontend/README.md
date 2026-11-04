# Frontend 기초 — 추상화 뒤에서 브라우저가 실제로 하는 일

> React 같은 프레임워크가 가려 주던 동작을 주제별로 정리. 이 저장소(mini-portal)에서 직접 부딪힌 원리 위주.
> 각 문서: 한 줄 요약 → **이해의 흐름**(코드를 읽으며 실제로 헷갈렸던 질문 → 처음 그린 그림 vs 실제 그림) → 브라우저가 실제로 하는 일 → 코드 → 이 프로젝트에서 → 흔한 함정.
> "이해의 흐름" 절은 [학습 Q&A](../learning/pr1/03-internals-qa.md)와 [모달 노트](../learning/modal/README.md)에서 한 질문들을 주제별로 옮긴 것이다. 복습할 때는 그 절의 질문에 먼저 답해 보고 그림을 확인한다.

| 주제 | 한 줄 | 이 프로젝트에서 |
|------|------|----------------|
| [dom-tree.md](dom-tree.md) | DOM은 JS 객체의 트리다. 만드는 것과 붙이는 것은 별개 | `node.js` createElement / appendChild |
| [event-flow.md](event-flow.md) | 브라우저는 이벤트를 DOM 경로로 캡처 → 타깃 → 버블 순서로 흘린다 | 단계 1 (브라우저) |
| [event-capture.md](event-capture.md) | 캡처는 탑다운으로 먼저, 버블은 바텀업으로 나중에. 캡처는 하위 stopPropagation에 안 막힘 | 모달 document 리스너 `true` |
| [event-object.md](event-object.md) | 리스너에는 브라우저가 만든 Event 객체가 들어온다 | `dispatch(native)` |
| [event-delegation.md](event-delegation.md) | 상위 하나가 받아서 나눠 준다. React의 이벤트 시스템 | `listen` + `dispatch` (단계 2) |
| [component-tree-vs-dom.md](component-tree-vs-dom.md) | 프레임워크는 DOM과 별개의 논리 트리를 갖는다. Portal은 둘을 가른다 | `node.parent` vs `el.parentNode` |
| [stacking-context.md](stacking-context.md) | z-index는 같은 stacking context 안에서만 비교된다 | 카드 함정, 레이어 스택 |
| [overflow.md](overflow.md) | 넘치는 내용 처리. body hidden → 뷰포트 스크롤 막기 | 카드 클리핑, 모달 스크롤 잠금 |
| [containing-block.md](containing-block.md) | 위치의 기준 상자와 overflow 클리핑. fixed + transform 함정 | 데모 카드 `transform` |
| [memory-and-cleanup.md](memory-and-cleanup.md) | GC는 도달 가능성으로 회수한다. 정리는 명시적으로 | WeakMap, `destroy`, 클린업 |
| [weak-collections.md](weak-collections.md) | WeakSet·WeakMap — 담되 붙잡지 않는 컬렉션 | `handled`, `elToNode` |
| [closures.md](closures.md) | 함수는 만들어진 곳의 변수를 기억한다 | `stopped`, `listen` 해제 함수, 클린업 |
| [reference-vs-copy.md](reference-vs-copy.md) | 객체는 참조로 전달된다. 복사는 명시적으로, `...`은 얕은 복사 | `{ ...on }`, `[...children]`, 클로저의 `portal` |

## 읽는 순서 추천

```
dom-tree → event-flow → event-capture → event-object → event-delegation → component-tree-vs-dom
                                                                ↓
                         reference-vs-copy ← closures ← weak-collections ← memory-and-cleanup ← containing-block ← overflow ← stacking-context
```
