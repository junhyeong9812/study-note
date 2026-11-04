# react-portal — React Portal을 순수 JS로 흉내 내며 배운 것

React `createPortal`이 **어떻게 동작하는지** 이해하려고, 의존성 없이 순수 JavaScript로 그 원리를 다시 만든 학습 프로젝트의 기록이다.\
코드는 저장소에 있으니 여기서는 **결정의 이유와 안 고른 후보**, 그리고 공부하며 정리한 문서를 남긴다.

- 저장소: https://github.com/junhyeong9812/react-portal · 기간 2026-11-03 ~ 2026-11-04 · 상태: 완료(main `27d95e9`)
- 스택: 순수 JavaScript(ES 모듈) · Vite 8 · Vitest 4 + jsdom · (비교용) React 19.3.1
- PR: [#1 미니 Portal](https://github.com/junhyeong9812/react-portal/pull/1) · [#2 모달 실무 기능 + 문제 재현 토글](https://github.com/junhyeong9812/react-portal/pull/2) · [#3 React 비교](https://github.com/junhyeong9812/react-portal/pull/3)
- 최종: 테스트 38개(Portal 17 · 모달 15 · React 6), 데모 페이지 2개(`/` 미니 Portal·모달, `/react.html` React 비교)

## 전체 구조 한눈에

```text
논리 트리 (node.parent)              DOM 트리 (el.parentNode)
root                                 body
 └ card                               ├ #app
    └ portal  ←──── 같은 노드 ────→   │  └ .mini-root      ← dispatch (이벤트 위임)
       └ overlay → dialog → 버튼       │     └ .card
                                      └ .mini-portal       ← dispatch (portal도 따로)
                                         └ .overlay → .dialog → 버튼

[클릭]  단계 1  브라우저: DOM 경로를 따라 컨테이너의 dispatch까지
        단계 2  dispatch: 클릭된 노드에서 n.parent를 따라 핸들러 실행 (button → portal → card → root)

[원칙]  위치(화면·CSS·Tab 순서) → DOM에 묻는다 · 관계(누구의 자식·이벤트·Context·안쪽인가) → 논리 트리에 묻는다
```

## 이슈 목록 — 왜 이렇게 풀었나

골격은 [reference/study-note-guide §2-B](../../reference/study-note-guide.md).

| # | 이슈 | 한 줄 | PR |
|---|---|---|---|
| [01](01-two-trees/README.md) | 두 트리 | 노드가 논리 부모(`parent`)와 DOM 부모(`domParent`)를 따로 든다 — Portal 전체가 이 한 줄 차이 | #1 |
| [02](02-event-delegation/README.md) | 이벤트 위임 | 브라우저는 DOM으로 잡고, 핸들러는 논리 트리로 돈다 · 등록이 두 종류 · 중복 방지 | #1 |
| [03](03-outside-click/README.md) | 바깥 클릭 | "안쪽인가"는 관계 질문 → 논리 트리 · 여는 click과 닫는 pointerdown을 다른 이벤트로 | #2 |
| [04](04-escape-and-focus/README.md) | ESC·Tab | 리스너 하나 + 모달 스택으로 맨 위만 · Tab은 가장자리에서만 되돌림 | #2 |
| [05](05-scroll-lock/README.md) | 스크롤 잠금 | 스위치가 아니라 참조 카운트 · 원래 값 복원 · 해제는 클린업 한 곳 | #2 |
| [06](06-react-compare/README.md) | React 대조 | 진짜 `createPortal` vs 별도 `createRoot` — DOM은 같고 Fiber 트리만 다르다 | #3 |
| [07](07-problem-replay-demo/README.md) | 문제 재현 토글 | 해결된 코드에서 문제를 다시 겪게 만드는 데모 전용 naive 모달 | #2 |

## 공부하며 만든 문서 (아카이브)

원 저장소 `docs/`의 문서를 그대로 옮겼다 → [archive/](archive/README.md).

| 묶음 | 무엇 | 입구 |
|---|---|---|
| 학습 노트 — PR #1 | 코드 읽는 순서, 내가 정리한 구조, 몰랐던 개념, 질문 23개(처음 생각 → 정답) | [archive/learning/pr1/](archive/learning/pr1/README.md) |
| 학습 노트 — 모달 | N1~N4 문제를 직접 겪고 정리 (바깥 클릭·여는 click·ESC·Tab·스크롤 잠금) | [archive/learning/modal/](archive/learning/modal/README.md) |
| 학습 노트 — React 비교 | 미니 구현 ↔ React 대응표, 가짜 portal이 깨지는 이유 | [archive/learning/react-compare/](archive/learning/react-compare/README.md) |
| 주제 문서 | DOM·이벤트(흐름·캡처·객체·위임)·두 트리·쌓임 맥락·containing block·overflow·메모리·WeakSet·클로저·참조와 복사 — 각 문서 첫 절 "이해의 흐름"에 실제 질문과 처음 그림 vs 실제 그림 | [archive/frontend/](archive/frontend/README.md) |

## 이 프로젝트에서 나온 지식

| 갈래 | 어디 |
|---|---|
| 개념 (cs 훈련) | [web-platform/25 쌓임 맥락·containing block](../../cs/web-platform/25-stacking-context-and-containing-block/) · [26 Portal과 두 트리](../../cs/web-platform/26-portals-and-two-trees/) · [27 모달 상호작용 계약](../../cs/web-platform/27-modal-dialog-behavior/) · 기존 [04 DOM과 이벤트 모델](../../cs/web-platform/04-dom-and-event-model/) |
| 실전 이슈 카드 (방안 비교 추가) | [tree-position-semantics](../../issue/typescript/react/tree-position-semantics/) (바깥 클릭 판정) · [input-event-model](../../issue/typescript/browser/input-event-model/) (진행 중 이벤트에 단 리스너) · [instance-scope-of-global-state](../../issue/typescript/react/instance-scope-of-global-state/) (ESC 전체 닫힘·스크롤 잠금 카운트) · 기존 [css-containing-context](../../issue/typescript/react/css-containing-context/) (fixed + transform — 무변경) |

## 남은 것

- 모달 click-through(바깥 `pointerdown`으로 오버레이가 사라진 뒤 같은 클릭의 click이 뒤 요소로 가는지) — 실브라우저 미검증.
- 모달 Tab 순환에 모달 안에서 연 portal(메뉴)의 버튼이 포함되지 않음 — 알려진 한계.
