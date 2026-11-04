# 06 — React와 대조: 진짜 portal vs 별도 루트로 렌더한 가짜 portal

- 커밋: [`a0780a4`](https://github.com/junhyeong9812/react-portal-lab/commit/a0780a4) (React 의존성·멀티 페이지) · [`7f601d5`](https://github.com/junhyeong9812/react-portal-lab/commit/7f601d5) (비교 페이지·테스트) · [PR #3](https://github.com/junhyeong9812/react-portal-lab/pull/3)
- 학습 노트: [archive/learning/react-compare/README.md](../archive/learning/react-compare/README.md)

---

## 1. 무엇이 문제였나

미니 구현으로 만든 원리(DOM은 옮기고 논리 관계는 유지)가 실제 React에서도 똑같이 성립하는지 확인하고 싶었다.\
그리고 Portal 대신 흔히 저지르는 실수 — **별도 `createRoot`로 body에 렌더하기** — 가 정확히 무엇을 깨뜨리는지 보이고 싶었다.

---

## 2. 무엇을 고민했나

| 후보 | 요지 | 대가 |
|---|---|---|
| A. 같은 저장소에 비교 페이지(Vite 멀티 페이지) | `react.html` 하나, JSX 없이 `createElement` | 의존성 추가(devDependency) |
| B. 별도 저장소 | 깔끔한 분리 | 비교·테스트를 한 번에 못 돌림 |
| C. 문서로만 비교 | 의존성 없음 | 실제 동작을 확인 못 함 |

→ **A.** JSX를 쓰지 않아 빌드 플러그인을 늘리지 않았다. 사용자 판단으로 "가볍게" 진행하고, 코드 리딩은 생략했다.

---

## 3. 그래서 이렇게

같은 카드(`ThemeContext="dark"` 제공 + `onClick`)를 두 방식으로 렌더한다.

```text
진짜                                   가짜
React 트리 (하나)                       React 트리 A          React 트리 B (새 루트)
Provider(dark)                          Provider(dark)        PortalContent  ← 부모가 없음
 └ Card(onClick)                         └ Card(onClick)
    └ Portal                                └ FakePortal (null 렌더)
       └ PortalContent ← 부모 체인 유지
```

| | 진짜 `createPortal` | 가짜 `createRoot` |
|---|---|---|
| 콘텐츠 DOM 위치 | 카드 밖 | 카드 밖 — **같음** |
| `useContext` | `"dark"` | `"light"`(기본값) |
| 안쪽 클릭 → 카드 `onClick` | 호출됨 | 호출 안 됨 |
| 버튼 자기 `onClick` | 호출됨 | 호출됨(prop으로 넘긴 함수 참조는 살아 있음) |

**DOM 위치는 같고, 차이는 전부 React 트리(Fiber)에서 생긴다.** 값을 직접 넘긴 것(props·함수 참조)은 동작하고, **트리를 따라 찾는 것**(Context·버블링·언마운트 연쇄)만 끊긴다.

| 개념 | 미니 Portal | React |
|---|---|---|
| 논리 트리 | `node.parent` | Fiber 트리 |
| DOM과 논리 분리 | `new Node({ parent, domParent: target })` | `createPortal(children, container)` |
| Context 조회 | `inject` — `n.parent`로 올라감 | `useContext` — Fiber 조상의 Provider |
| 이벤트 위임 | 루트·portal 컨테이너의 `dispatch` | 루트(+ portal) 컨테이너의 React 리스너 |

---

## 4. 코드 — 실제 커밋에서

`demo/react/compare.js` (`7f601d5`)

```js
// 진짜 portal: DOM은 container로, React 트리(Fiber)는 원래 부모 아래 그대로
export function RealPortal({ children, container }) {
  return createPortal(children, container);
}

// 가짜 portal: container에 "새 React 루트"를 만들어 렌더.
// DOM 위치는 진짜와 똑같이 옮겨지지만, React 트리가 새로 시작돼 부모와 끊긴다.
export function FakePortal({ children, container }) {
  const [root, setRoot] = useState(null);

  useEffect(() => {
    const el = document.createElement('div');
    container.appendChild(el);
    const r = createRoot(el);
    setRoot(r);
    return () => {
      // 렌더 도중 다른 루트를 동기 unmount하면 React가 경고한다 → 다음 틱으로 미룸
      setTimeout(() => {
        r.unmount();
        el.remove();
      });
    };
  }, [container]);

  useEffect(() => {
    root?.render(children);
  }, [root, children]);

  return null; // 이 컴포넌트 자리에는 아무것도 그리지 않는다
}
```

`vite.config.js` (`a0780a4`)

```js
export default defineConfig({
  build: {
    rolldownOptions: {
      input: {
        main: resolve(import.meta.dirname, 'index.html'),
        react: resolve(import.meta.dirname, 'react.html'),
      },
    },
  },
});
```

---

## 5. 구현 중 마주친 문제

**Vite 8의 설정 키가 바뀌어 있었다.** 설치된 타입 정의를 확인하니 `rollupOptions`는 deprecated이고 `rolldownOptions`가 정식이었다 → 임시 `react.html`로 두 페이지가 빌드되는지 먼저 스모크한 뒤 진행.

**가짜 portal 정리.** effect cleanup은 부모 루트 커밋 중에 실행되므로, 거기서 다른 루트를 동기 unmount하면 React가 경고한다 → `setTimeout`으로 미뤘다. 진짜 portal은 같은 트리라서 이런 비용이 없다.

**변이 점검.** 가짜를 `RealPortal`로 바꾸면 "가짜는 light", "가짜는 카드 onClick 미도달" 두 테스트가 실패 → 테스트가 두 방식을 실제로 구분한다.

**머지 순서 충돌.** PR #2와 #3이 같은 기준에서 갈라져 README·NEXT·측정로그를 함께 고쳤다 → #2 머지 후 #3 브랜치에 main을 병합하고 양쪽 내용을 보존해 해소.

---

## 6. 결론

- 테스트 R1(Context)·R2(이벤트)·R3(DOM 위치는 둘 다 카드 밖) 6개. 전체 38개 통과로 프로젝트 마무리.
- 개념 노트: [cs/web-platform/26-portals-and-two-trees](../../../cs/web-platform/26-portals-and-two-trees/) · 이슈 카드: [issue/typescript/react/tree-position-semantics](../../../issue/typescript/react/tree-position-semantics/)
