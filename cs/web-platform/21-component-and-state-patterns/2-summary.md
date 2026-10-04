# web-platform/21-component-and-state-patterns — 컴포넌트 합성, 제어/비제어, 단방향 흐름, 상태 위치, 서버 상태 캐시 vs 클라이언트 상태 — 정리 (힌트)

## 해결하는 문제

UI가 커지면 두 질문이 계속 나온다. **상태를 어디에 두나**, 그리고 **컴포넌트를 어떻게 나누고 조합하나**.

```text
  상태를 잘못 둔 화면
  App ─ 전역 스토어 { 검색어, 주문목록(서버에서 복사), 모달열림 }
   ├─ SearchBox        검색어 입력 → 전역 갱신 → 주문 1000행 전부 다시 그림 (입력 지연)
   ├─ OrderList        서버 데이터를 한 번 복사해 둠 → 다른 화면에서 고쳐도 옛 값 (오래된 데이터)
   └─ PriceTag(price)  useState(price)로 복사 → 부모가 바꿔도 안 바뀜 (파생 상태 버그)
```

- 이 노트의 실험에서 위 세 증상을 각각 재현했다. 전역 Context의 검색어 10글자 입력 → 행 렌더 10,000회. 서버 데이터 전역 복사본 → 이름 변경 후에도 옛 이름. props를 state로 복사 → 가격 변경 미반영.

쉬운 예: 사무실의 공용 화이트보드다.
- 내 메모(로컬 상태)를 공용 보드(전역)에 쓰면, 글자 하나 쓸 때마다 전원이 고개를 든다.
- 본사 공지(서버 데이터)를 보드에 베껴 두면, 본사가 공지를 바꿔도 보드는 옛 내용이다. 원본을 다시 확인하는 규칙(캐시 무효화)이 필요하다.
- 동료가 불러 준 숫자를 내 수첩에 베끼면(props → state), 동료가 숫자를 고쳐도 내 수첩은 그대로다.

똑같은 구조다. 상태마다 **주인**(누가 진실을 갖나)과 **수명**을 정하지 않으면 복사본이 생기고, 복사본은 어긋난다.

실무 예:
- 주문 목록을 Redux 스토어에 넣고 수동 무효화를 빠뜨려, 결제 후에도 "미결제"로 보인다.
- 폼 입력값을 전역 스토어에 두어 큰 화면에서 타이핑이 끊긴다(INP 악화 — 재렌더 비용은 18번).
- 10단계 아래 컴포넌트가 쓰는 값을 중간 9개가 받아서 넘기기만 한다(prop drilling).

## 동작·원리

### 1. 단방향 데이터 흐름 — Flux·Redux·Elm

```text
  Flux                         Redux                           Elm Architecture
  Action ─> Dispatcher         action ─> reducer(state, action)   Msg ─> update(msg, model)
              │                            │                              │
              v                            v                              v
           Store(들) ─변경 이벤트─> View   store(하나) ─구독─> view       Model ─> view(model) ─> HTML
              ^                            ^                              ^
              └──── View가 Action 생성 ─────┴──── UI가 dispatch ───────────┴──── 사용자 입력이 Msg
```

- Flux 문서(보관된 프로젝트): 주요 부분은 Dispatcher·Store·View 셋이고, Action(생성 도우미 메서드)을 갱신 주기의 네 번째 부분으로 볼 수 있다고 한다. "데이터는 앱 안에서 한 방향으로 흐른다 — 양방향 바인딩이 없다." 양방향 바인딩의 연쇄 갱신을 막는 것이 목적이다.
- Redux "Three Principles"
  - *Single source of truth*: 전역 상태는 한 스토어의 객체 트리에 둔다.
  - *State is read-only*: 상태를 바꾸는 유일한 방법은 무슨 일이 있었는지 설명하는 객체(action)를 내보내는 것이다.
  - *Changes are made with pure functions*: 상태 변환은 순수 함수 reducer로 쓴다.
- Elm Architecture: *Model*(앱 상태), *View*(상태를 HTML로), *Update*(메시지로 상태를 갱신).
- 공통점: 상태 변경이 한 입구로만 들어온다. 그래서 "값이 왜 이렇게 됐나"를 action 기록으로 추적할 수 있다. 계보·양방향 바인딩과의 비교는 [software-design/42-ui-architecture-patterns](../../software-design/42-ui-architecture-patterns/2-summary.md).

### 2. 상태의 종류와 기본 위치

| 종류 | 예 | 진실의 주인 | 기본 위치 |
|---|---|---|---|
| 로컬 UI 상태 | 입력 중인 글자, 펼침 여부 | 그 컴포넌트 | `useState` (로컬) |
| 공유 UI 상태 | 선택된 탭을 형제 둘이 씀 | 가장 가까운 공통 부모 | 끌어올리기 |
| 앱 전역 클라이언트 상태 | 테마, 로그인 사용자 표시 | 앱 | Context·전역 스토어 |
| 서버 상태 | 주문 목록, 사용자 프로필 | **서버** | 키 기반 캐시(TanStack Query 등) |
| URL 상태 | 검색어·페이지 번호(공유·북마크 필요) | URL | 라우터 쿼리 |
| 파생 값 | 필터된 목록, 합계 | 원천 상태 | 상태로 두지 않고 렌더 중 계산 |

- 서버 상태는 클라이언트가 **소유하지 않는다**. 클라이언트에 있는 것은 어느 시점의 복사본(캐시)이다. 그래서 "언제 오래됐다고 보나, 언제 다시 가져오나"라는 캐시 문제가 된다.
- react.dev "Choosing the State Structure"의 원칙: 관련 상태 묶기, 모순 피하기, **중복(redundant) 상태 피하기**, 중복(duplication) 피하기, 깊은 중첩 피하기.
  - 중복 상태: props나 다른 상태에서 렌더 중 계산할 수 있으면 상태에 두지 않는다.

### 3. 상태 위치를 정하는 흐름

```text
  이 상태를 쓰는 컴포넌트는?
   ├─ 하나뿐 ──────────────────────────> 그 컴포넌트의 로컬 상태
   ├─ 몇 개(가까운 공통 부모가 있음) ───> 공통 부모로 끌어올리고 props로 내려줌
   ├─ 멀리 흩어진 여러 곳 ─────────────> Context(드물게 바뀌는 값) / 선택자 구독 스토어(자주 바뀌는 값)
   └─ 서버 데이터인가? ────────────────> 위와 별개로 서버 상태 캐시(키·무효화)
```

- *끌어올리기(lifting state up)*: 자식들의 상태를 지우고 가장 가까운 공통 부모로 옮겨 props로 내려 주는 것. 각 상태에 주인이 하나가 된다(react.dev "Sharing State Between Components").
- Context는 값이 바뀌면 그 값을 읽는 컴포넌트가 전부 다시 렌더된다. `memo`로 감싸도 막지 못한다(아래 실험 ①의 global).
- *선택자(selector) 구독*: 스토어 전체가 아니라 필요한 조각만 구독하고, 조각이 바뀔 때만 다시 그린다(`useSyncExternalStore(subscribe, () => 조각)`).

### 4. 제어 vs 비제어 컴포넌트

```text
  비제어(uncontrolled)                         제어(controlled)
  <Panel />  ── 자기 state로 열림 관리          <Panel isActive={i===0} onShow={() => setI(0)} />
  부모가 개입 못 함, 쓰기 쉬움                   부모가 완전히 결정, 유연하지만 배선이 많음
  폼: <input defaultValue="…">                  폼: <input value={v} onChange={…}>
```

- react.dev: 중요한 정보가 자기 로컬 상태로 결정되면 비제어, props로 결정되면 제어다.
- 폼 `<input>`이 수명 중에 둘 사이를 오가면(`value`가 `undefined` → 문자열) React가 경고한다(실험 ④). 직접 만든 컴포넌트의 제어·비제어는 설계상 구분이라, 오간다고 React가 경고하지는 않는다.

### 5. 합성 패턴 — 로직과 표시 나누기

| 패턴 | 생김새 | 지금의 위치 |
|---|---|---|
| Container/Presentational | 데이터 가져오는 컨테이너 + props만 그리는 표시 컴포넌트 | patterns.dev: Hooks가 대부분 대체 |
| 커스텀 훅 | `useOrders()`가 로직·상태를 담고, 어느 컴포넌트든 호출 | 현재 주된 방식 |
| Render props | `<DataSource render={data => <List data={data} />} />` | 훅 이전의 로직 공유 방식 |
| Compound | `<Tabs><Tabs.List/><Tabs.Panel/></Tabs>`가 내부 Context로 상태 공유 | 디자인 시스템 컴포넌트에 흔함 |

```tsx
// 커스텀 훅 = 컨테이너의 로직만 떼어 낸 것
function useOrders(userId: string) {
  return useQuery({ queryKey: ['orders', userId], queryFn: () => api.orders(userId) });
}
function OrderList({ userId }: { userId: string }) {          // 표시 + 훅 호출
  const { data, isPending, isError } = useOrders(userId);
  if (isPending) return <Spinner />;
  if (isError) return <p>불러오지 못했습니다</p>;   // 최종 실패면 data가 undefined일 수 있다
  return <ul>{data.map(o => <li key={o.id}>{o.title}</li>)}</ul>;
}

// Compound — 부모가 상태를 갖고 자식들이 Context로 읽는다
const TabsCtx = createContext<{ i: number; set: (i: number) => void } | null>(null);
function Tabs({ children }: { children: ReactNode }) { const [i, set] = useState(0); return <TabsCtx.Provider value={{ i, set }}>{children}</TabsCtx.Provider>; }
Tabs.Tab = ({ index, children }: { index: number; children: ReactNode }) => { const c = useContext(TabsCtx)!; return <button aria-selected={c.i === index} onClick={() => c.set(index)}>{children}</button>; };
```

### 6. 서버 상태 캐시 — 키, 중복 제거, 무효화

```text
  컴포넌트 A ─ useQuery(['user']) ─┐
  컴포넌트 B ─ useQuery(['user']) ─┼─> 캐시 Map: 'user' → { data, promise(진행 중), 갱신 시각 }
                                    │        ├─ 진행 중 promise가 있으면 같이 기다림 → 요청 1번
                                    │        ├─ 오래됨(stale) + 계기(마운트·포커스·재연결)면 옛 값 보여 주고 다시 가져옴
  변경 성공 ─ invalidate(['user']) ─┘        └─ 무효화되면 stale 표시(값은 남김), 화면에 쓰이는 쿼리는 다시 가져와 구독자에게 알림
```

- *stale-while-revalidate*: 캐시 값을 먼저 보여 주고 뒤에서 다시 가져와 바꾼다. HTTP `Cache-Control`의 같은 이름 지시어와 생각이 같다([network/34](../../network/34-http-caching/2-summary.md)).
- TanStack Query "Important Defaults"(문서 latest)
  - 캐시 데이터를 기본으로 stale로 본다(`staleTime` 0).
  - stale 쿼리는 새 인스턴스 마운트·창 포커스·네트워크 재연결 때 다시 가져온다.
  - 쓰이지 않는 쿼리는 5분 뒤 정리한다(`gcTime` 1000×60×5, 클라이언트 기본값 — 서버(SSR)에서는 `Infinity`, "Server Rendering" 가이드).
  - stale이 되는 순간 자체가 재요청을 시작하지는 않는다. 위 계기가 있어야 한다.
  - `invalidateQueries`는 캐시 값을 지우지 않고 stale로 표시한 뒤, 렌더 중인 쿼리를 뒤에서 다시 가져온다("Query Invalidation"). 지우는 것은 `removeQueries`다.
  - 실패하면 지수 백오프로 3번 조용히 재시도한다(클라이언트 기본값 — 서버에서는 0번, "Query Retries"; [reliability/06](../../reliability/06-retry-backoff-jitter/2-summary.md)).
  - 결과에 구조 공유를 적용해, 바뀌지 않은 부분의 참조를 유지한다.

### 실험: 상태 위치·파생 상태·서버 상태·제어 전환

환경: headless Chrome 151.0.7922.173, React·react-dom 19.2.8(①~③ 운영 빌드, ④ 개발 빌드), esbuild 0.28.2, Node 20.19.6 서버(127.0.0.1), Playwright(playwright-core 1.62.1).

```jsx
// ① 상태 위치 — 행 1000개, 행은 memo로 감쌌다
const Row = memo(function Row({ r }) { const { query } = useContext(Ctx) ?? {}; window.__renders++; return <li>{r.name}</li>; });
// global: 검색어를 최상위 Context에 → <Ctx.Provider value={{ query, setQuery }}>
// local : 검색어를 SearchBox 자신의 useState에 (행이 읽는 Context 값은 null로 고정)
// store : 외부 스토어 + 선택자 — 행은 useSyncExternalStore(store.sub, () => store.s.selected === r.id)
// ② 파생 상태
function CopyPrice({ price }) { const [p] = useState(price); return <span id="copy">{p}</span>; }
function DirectPrice({ price }) { return <span id="direct">{price}</span>; }
// ③ 서버 상태 — 각자 fetch 2개, 키 캐시(진행 중 promise 공유) 2개, 전역 스토어에 한 번 복사 1개
function fetchQuery(key, fn) { let e = qc.get(key); if (!e) { e = { data: undefined }; e.promise = fn().then(d => { e.data = d; notify(); }); qc.set(key, e); } return e; }
```

`(실험, headless Chrome 151, CPU 4×(①), 각 3회, 2026-10-04)` — ①은 입력창 클릭 뒤 `abcdefghij`를 30ms 간격으로 입력. 최장 이벤트 지속 = Event Timing(`durationThreshold: 16`, `interactionId` 있는 것) 최대값, 스크립트 시간 = CDP `Performance.getMetrics`의 `ScriptDuration` 증가분.

```text
① global 10글자 입력 → 행 렌더 10000/10000/10000 | 최장 이벤트 지속 120/120/120ms | 스크립트 시간 합 251/217/230ms | 입력값 abcdefghij
① local  10글자 입력 → 행 렌더 0/0/0 | 최장 이벤트 지속 80/88/96ms | 스크립트 시간 합 78/72/80ms | 입력값 abcdefghij
① store  10글자 입력 → 행 렌더 0/0/0 | 최장 이벤트 지속 104/96/104ms | 스크립트 시간 합 144/156/183ms | 입력값 abcdefghij
② 가격 +500 두 번 → state 복사: 1000 / props 직접: 2000
③ 첫 화면 /api/user 요청 수: 4 (각자 fetch 컴포넌트 2개 + 키 캐시 컴포넌트 2개 + 전역 복사 1개)
   표시: 김철수, 김철수, 김철수, 김철수, 김철수
   이름 변경 + invalidate("user") 뒤 요청 수: 1 → 캐시: 김영희 김영희 | 전역 복사본: 김철수
```

관찰과 해석:
- ① global: 글자마다 1000행이 다시 렌더됐다(10글자 × 1000 = 10,000). `memo`가 있어도 Context를 읽는 컴포넌트는 막지 못한다. 스크립트 시간도 local의 약 3배였다.
- ① local: 검색어를 입력창이 가지니 행은 한 번도 다시 그려지지 않았다.
- ① store: 행 렌더는 0이었지만 스크립트 시간은 local보다 컸다(144~183ms). 변경마다 구독자 1000개의 선택자(`getSnapshot`)를 실행해 비교하기 때문이다. 선택자 구독은 렌더를 막지만 공짜는 아니다.
- ① 이벤트 지속은 세 방식 모두 80~120ms였다(사실 점검 재실행: global 104~112, local 64~112, store 96~144ms — 범위가 겹쳐 방식 간 차이로 읽기 어렵다. 행 렌더 수·②·③·④ 출력은 재실행과 같았다). 이 페이지에서는 입력 뒤 프레임 처리 비용이 커서 차이가 작게 나타났다(Event Timing은 8ms 단위로 반올림된다). 입력 지연과의 관계는 18번에서 더 크게 다룬다.
- ② state로 복사한 쪽은 첫 값(1000)에 멈췄다. `useState`의 인자는 첫 렌더에만 쓰인다.
- ③ 요청 수 4 = 각자 fetch 2 + 키 캐시 1(두 컴포넌트가 진행 중 promise를 공유) + 전역 복사 1. 이름을 바꾸고 `invalidate`하자 키 캐시는 1번 다시 가져와 둘 다 새 이름을 보였다. 전역 복사본은 아무도 무효화하지 않아 옛 이름이 남았다.

④ 제어 전환 경고(개발 빌드). `value`가 `undefined`로 시작해 입력 뒤 문자열이 되는 입력창, 그리고 `onChange` 없이 `value`만 준 입력창:

```text
console.error: You provided a `value` prop to a form field without an `onChange` handler. This will render a read-only field. If the field should be mutable use `defaultValue`. Otherwise, set either `onChange` or `readOnly`.
console.error: A component is changing an uncontrolled input to be controlled. This is likely caused by the value changing from undefined to a defined value, which should not happen. Decide between using a controlled or uncontrolled input elemen
#j 값: 고정
```

## 쓰이는 자료구조·알고리즘

- **리듀서 = 폴드(fold)**: 현재 상태 = `actions.reduce(reducer, 초기상태)`. action 기록을 다시 적용하면 같은 상태가 나온다(시간 여행 디버깅의 근거). 이벤트 소싱과 같은 구조다 — [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md).
- **불변 상태 트리 + 구조 공유**: 갱신 때 바뀐 경로의 노드만 새로 만들고 나머지는 참조를 재사용한다. 그래서 "참조가 같으면 안 바뀜"으로 O(1) 비교가 된다(18번의 얕은 비교). [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)
- **키 기반 캐시 + 진행 중 promise 공유**: `Map<key, {data, promise, updatedAt}>`. 같은 키의 동시 요청은 진행 중 promise를 같이 기다린다(요청 합치기). 오래된 항목 정리는 LRU·시간 기반 — [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md).
- **옵서버(구독 집합)**: 스토어는 구독 함수 `Set`을 갖고 변경 때 순회 호출한다. 선택자 비교 비용은 구독자 수에 비례한다(실험 ①의 store).
- **트리 경로**: 끌어올리기의 "가장 가까운 공통 부모"는 트리의 최소 공통 조상(LCA)이다.

## 적용 — 풀어나가는 법

### 1. 순서

1. 화면의 상태를 나열하고 표(2절)로 분류한다. 특히 **서버 상태를 클라이언트 상태와 분리**한다.
2. 파생 값을 상태에서 지운다. 렌더 중 계산하고, 비싸면 `useMemo`(18번).
3. 로컬에서 시작한다. 형제가 필요해지면 끌어올린다. 멀리 흩어지면 Context(드물게 바뀜)나 선택자 스토어(자주 바뀜).
4. 서버 상태는 키 기반 캐시 라이브러리에 맡긴다. 키를 설계하고(`['orders', userId, filter]`), 변경 뒤 무효화할 키를 정한다.
5. 공유·북마크가 필요한 상태(검색어·페이지)는 URL에 둔다.
6. 재사용 컴포넌트는 제어·비제어 중 하나로 정한다. 둘 다 지원하면 `value`/`defaultValue` 규약을 따른다.
7. 측정: React Profiler나 렌더 카운터로 입력 한 번에 다시 그려지는 컴포넌트 수를 본다.

### 2. 코드 — 서버 상태와 클라이언트 상태 분리(TanStack Query 예)

```tsx
// 서버 상태: 캐시가 주인. 변경 뒤 무효화
function useRenameUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.renameUser(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['user'] }),   // ['user']로 시작하는 쿼리를 stale로 표시, 쓰이는 중인 것은 다시 가져옴
  });
}
// 클라이언트 상태: 모달 열림 같은 순수 UI 상태만 스토어/로컬에
const [open, setOpen] = useState(false);
```

- 서버 응답을 전역 스토어로 복사하는 코드(`dispatch(setUser(data))`)가 보이면 이유를 묻는다. 복사본이 생기면 무효화를 사람이 기억해야 한다.

### 3. 코드 — 파생 상태 대신 계산, 초기값만 필요하면 이름으로 밝히기

```tsx
function PriceTag({ price, qty }: { price: number; qty: number }) {
  const total = price * qty;                 // 상태로 두지 않는다
  return <span>{total.toLocaleString()}원</span>;
}
function Editor({ initialText }: { initialText: string }) {
  const [text, setText] = useState(initialText);  // 일부러 첫 값만 쓰는 경우 — initial/default 접두사(react.dev)
  // 다른 문서로 바뀔 때 초기화가 필요하면 부모에서 <Editor key={docId} …/>
}
```

### 4. 진단

- React DevTools Profiler: "Highlight updates when components render"로 입력 한 번에 번쩍이는 범위를 본다.
- 렌더 카운터(`window.__renders++`)와 CDP `ScriptDuration` 증가분(실험 ①의 방법).
- Network 패널에서 같은 API가 한 화면에 몇 번 불리는지(실험 ③의 4회).
- 개발 빌드 콘솔의 제어·비제어 경고(실험 ④).

## 장애 시나리오와 대처

### 1. 서버 데이터를 전역 스토어에 복사 → 오래된 값·수동 무효화 누락 (⚠ 커리큘럼)

- **현상**: 프로필 이름을 바꿨는데 헤더에는 옛 이름이 남는다. 새로고침하면 맞다.
- **보이는 형태**: 오류 없음. 화면끼리 값이 다르다. 실험 ③: 키 캐시는 `김영희`, 전역 복사본은 `김철수`.
- **원인**: 서버 상태의 복사본을 클라이언트가 주인처럼 들고 있다. 변경 경로마다 복사본 갱신을 손으로 넣어야 하는데 하나를 빠뜨렸다.
- **대처**: 서버 상태는 키 기반 캐시로 옮기고, 변경 성공 때 관련 키를 무효화한다. 복사본을 없앤다.

### 2. props를 state로 복사(파생 상태) → 부모 변경이 반영 안 됨 (⚠ 커리큘럼)

- **현상**: 목록에서 다른 상품을 골랐는데 편집 폼에는 이전 상품 값이 남는다.
- **보이는 형태**: 실험 ② — 부모 가격 2000, 복사한 자식 1000.
- **원인**: `useState(prop)`의 인자는 첫 렌더에만 쓰인다(react.dev "Don't mirror props in state").
- **대처**: prop을 직접 쓰거나 렌더 중 계산한다. 정말 초기값만 필요하면 `initialX`로 이름 짓고, 바뀔 때 초기화하려면 `key`를 바꿔 다시 마운트한다.

### 3. 전역 스토어 하나 변경에 전 트리 재렌더 → 입력 지연 (⚠ 커리큘럼)

- **현상**: 큰 목록 화면에서 검색창 타이핑이 끊긴다.
- **보이는 형태**: Profiler에서 키 입력마다 목록 전체가 번쩍인다. 실험 ① global: 10글자에 행 렌더 10,000회, 스크립트 시간 217~251ms(local 72~80ms).
- **원인**: 자주 바뀌는 값(입력 중 글자)을 많은 컴포넌트가 읽는 Context·스토어 조각에 두었다. `memo`도 Context 구독은 막지 못한다.
- **대처**: 입력 중 값은 로컬로 내린다. 공유가 필요하면 선택자 구독으로 필요한 조각만 읽게 한다(구독자 수에 비례하는 비교 비용은 남는다 — 실험 ① store). 재렌더 비용 자체는 18번.

### 4. prop drilling 10단계 (⚠ 커리큘럼)

- **현상**: 값 하나 추가하는데 중간 컴포넌트 9개의 props를 고친다.
- **보이는 형태**: 중간 컴포넌트가 쓰지 않는 props를 받아 넘기기만 한다. 리뷰 diff가 넓다.
- **원인**: 상태를 너무 위로 끌어올렸거나, 합성 대신 깊은 계층을 만들었다.
- **대처**: 먼저 합성으로 푼다 — 중간 컴포넌트가 `children`을 받게 하면 위에서 완성된 요소를 바로 꽂을 수 있다. 그래도 멀면 Context(드물게 바뀌는 값)를 쓴다.

### 5. 제어·비제어 전환 → 입력값이 갑자기 고정되거나 경고

- **현상**: 처음 몇 글자는 입력되다가 이후 동작이 이상해지거나, 입력이 안 된다.
- **보이는 형태**: 개발 콘솔 `A component is changing an uncontrolled input to be controlled.` 또는 `You provided a \`value\` prop to a form field without an \`onChange\` handler.` 실험 ④에서 `onChange` 없는 입력창은 `고정`에서 바뀌지 않았다.
- **원인**: `value`가 `undefined`로 시작했다가 값이 생겼다. 또는 `value`만 주고 `onChange`를 빠뜨렸다.
- **대처**: 제어 입력은 처음부터 문자열(`''`)로 초기화한다. 비제어로 쓸 거면 `defaultValue`를 쓴다.

## 핵심 문장

- 상태마다 진실의 주인을 하나로 정한다. 복사본이 생기면 언젠가 어긋난다.
- 서버 상태는 클라이언트가 소유하지 않는 캐시다. 키·신선도·무효화로 다루고, 전역 스토어에 복사하지 않는다.
- 렌더 중 계산할 수 있는 값은 상태에 두지 않는다. props를 `useState`로 복사하면 첫 값에 멈춘다.
- 자주 바뀌는 상태를 넓게 공유하면 재렌더 범위가 커진다. 실험에서 전역 Context 검색어 10글자는 행 렌더 10,000회를 만들었다.
- 단방향 흐름(Flux·Redux·Elm)은 상태 변경 입구를 하나로 만들어 변경 이유를 추적 가능하게 한다.
- 합성(커스텀 훅·Compound·children)은 로직과 표시를 나누고 prop drilling을 줄인다.

## 관련 주제·근거

- 선행
  - [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md) · [03-event-loop](../03-event-loop/2-summary.md)
  - [18-ui-rerender-and-memoization](../18-ui-rerender-and-memoization/2-summary.md) — 재렌더·재조정·참조 동일성
  - [software-design/42-ui-architecture-patterns](../../software-design/42-ui-architecture-patterns/2-summary.md) — MVC→MVVM→Flux 계보
- 후속·연결
  - [22-islands-and-micro-frontends](../22-islands-and-micro-frontends/2-summary.md) — 섬·마이크로 프론트엔드 사이의 상태 공유
  - [10-rendering-strategies](../10-rendering-strategies/2-summary.md) — 서버 렌더와 하이드레이션 입력 데이터
  - [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md) · [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md) · [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)
  - [network/34-http-caching](../../network/34-http-caching/2-summary.md) — stale-while-revalidate · [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)
  - [languages/web-api/22-input-event-order](../../../languages/web-api/22-input-event-order/2-summary.md) — 입력 이벤트 순서(제어 입력의 `onChange` 시점)
- 문서
  - Flux "In-Depth Overview"(보관된 프로젝트) <https://facebookarchive.github.io/flux/docs/in-depth-overview>
  - Redux "Three Principles" <https://redux.js.org/understanding/thinking-in-redux/three-principles>
  - The Elm Architecture <https://guide.elm-lang.org/architecture/>
  - react.dev "Choosing the State Structure"(원칙 5개, Don't mirror props in state, `initial`·`default` 예외) <https://react.dev/learn/choosing-the-state-structure>
  - react.dev "Sharing State Between Components"(끌어올리기, 제어·비제어, 단일 진실 원천) <https://react.dev/learn/sharing-state-between-components>
  - patterns.dev "Container/Presentational Pattern"(Hooks가 대부분 대체), Compound·Render Props 패턴 <https://www.patterns.dev/react/presentational-container-pattern/>
  - TanStack Query "Important Defaults" <https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults>
- 실험 목록(작업 scratchpad `wp/10/e21/`)
  - ① 상태 위치(global·local·store) 1000행, CPU 4×, 3회: 행 렌더 수·Event Timing·`ScriptDuration`.
  - ② props→state 복사 vs 직접 사용.
  - ③ 서버 상태: 각자 fetch·키 캐시·전역 복사의 요청 수와 무효화 후 표시.
  - ④ 제어·비제어 경고(React 19.2.8 개발 빌드).
  - 환경: headless Chrome 151.0.7922.173, React 19.2.8, Node 20.19.6, 127.0.0.1.
