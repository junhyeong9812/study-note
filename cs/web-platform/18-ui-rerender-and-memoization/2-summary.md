# web-platform/18-ui-rerender-and-memoization — 선언형 UI의 재렌더 모델과 메모이제이션 — 정리 (힌트)

## 해결하는 문제

선언형 UI는 "상태 → 화면"을 함수로 적는다. 상태가 바뀌면 그 함수를 다시 부르고(재렌더), 이전 결과와 비교해(재조정) 바뀐 DOM만 고친다.
편하지만, **다시 부르는 범위**가 넓으면 바뀌지 않은 부분까지 계산한다.

```text
  <App>  ← 입력창 상태 q가 여기 있음. 키 한 번 → App 재렌더
   ├─ <input value={q}>
   └─ <List>
        ├─ <Row 0>    ┐
        ├─ ...        ├ q와 무관한데 3000개 전부 다시 렌더 (기본 동작)
        └─ <Row 2999> ┘
```

- *재렌더(re-render)*: 컴포넌트 함수를 다시 호출해 새 요소 트리를 만드는 것. DOM을 바꾸는 것과 다르다.
- *재조정(reconciliation)*: 새 요소 트리와 이전 트리를 비교해 실제 DOM 변경을 최소로 정하는 과정.

쉬운 예: 반 전체 성적표다.
- 한 학생 점수만 바뀌었는데 담임이 30명 성적표를 모두 다시 쓰고, 옛 것과 한 줄씩 대조해 바뀐 칸만 고친다.
- 결과(바뀐 칸)는 맞다. 하지만 다시 쓰고 대조하는 시간이 학생 수에 비례한다.

똑같은 구조다.\
실무 예: 검색창 타이핑마다 아래 큰 표·목록 전체가 재렌더되어 글자가 늦게 찍힌다(INP 악화). 전역 스토어 하나가 바뀌면 화면 전체가 다시 렌더된다.

이 노트는 React를 예로 든다. "부모가 재렌더되면 자식도 기본으로 재렌더"는 React의 규칙이고, 가상 DOM을 쓰는 프레임워크 모두의 규칙은 아니다. Vue도 가상 DOM을 쓰지만 렌더 중에 반응형 의존성을 추적한다. 그래서 부모가 갱신돼도 자식은 받은 props 중 하나라도 바뀔 때만 갱신한다(자식이 직접 쓰는 반응형 상태가 바뀌면 그것으로도 갱신된다 — vuejs.org "Rendering Mechanism"·"Performance"). Solid·Svelte의 갱신 범위는 각 문서로 확인하지 않았다 [?].

## 동작·원리

### 1. 재렌더의 전파 — 상태가 있는 곳부터 아래로

```text
  setQ('h')  →  App 재렌더  →  App이 반환한 모든 자식 요소도 재렌더
                                 ├ 같은 props라도 재렌더 (기본)
                                 └ memo로 감싼 자식: props가 얕은 비교로 같으면 건너뜀
```

- React는 상태를 가진 컴포넌트를 다시 렌더하고, 그 컴포넌트가 반환한 자식들도 다시 렌더한다.
- 예외: `memo`로 감싼 컴포넌트는 props가 이전과 같으면(각 prop을 `Object.is`로 비교) 보통 건너뛴다. "보통" — React 문서는 memo를 **성능 최적화이지 보장이 아니라**고 적는다(react.dev "memo").
- 같은 요소 객체(예: 부모에서 `children`으로 받아 그대로 반환한 JSX)는 다시 만들어지지 않으므로 그 아래도 건너뛴다. react.dev가 "JSX를 children으로 받기"를 권하는 이유다.

### 2. 재조정 — O(n) 휴리스틱

```text
  이전            다음
  <ul>           <ul>
   <li key=a>     <li key=b>   ← key로 같은 항목끼리 짝지음 (이동만)
   <li key=b>     <li key=a>
  <div> → <span> : 타입이 다르면 하위 트리를 버리고 새로 만듦 (상태도 사라짐)
```

- 일반적인 트리 diff(트리 편집 거리)는 고전 알고리즘이 O(n³)이다(legacy.reactjs.org "Reconciliation"이 든 값). 그 뒤 가중치 없는 편집 거리는 약 O(n^2.69)까지 내려갔지만 여전히 n의 제곱보다 크다(ESA 2025 논문 서론의 정리). React는 두 가정으로 O(n) 휴리스틱을 쓴다(같은 React 문서).
  1. 타입이 다른 두 요소는 다른 트리를 만든다 → 비교하지 않고 교체.
  2. 개발자가 `key`로 어떤 자식이 같은지 알려 준다.
- `Math.random()` 같은 불안정한 key는 컴포넌트·DOM을 매번 다시 만들고 자식 상태를 잃게 한다(같은 문서).

### 3. 참조 동일성 — memo가 무력화되는 이유

```text
  렌더 1:  <Row style={{padding: 2}} onSelect={id => ...} />   style = 객체 #1, onSelect = 함수 #1
  렌더 2:  <Row style={{padding: 2}} onSelect={id => ...} />   style = 객체 #2, onSelect = 함수 #2
           Object.is(#1, #2) = false  → "props가 바뀌었다" → 재렌더
```

- *참조 동일성*: 두 값이 **같은 객체**인가. 내용이 같아도 새로 만든 객체는 다르다 — [language/06 값·참조·전달](../../language/06-values-references-passing/2-summary.md)(원고: [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md)).
- 렌더 중에 만든 객체·배열·함수는 매번 새것이다. react.dev는 이런 prop을 받는 컴포넌트에 memo가 "완전히 쓸모없다"고 적는다.
- 그래서 짝으로 쓰는 도구가 있다.
  - `useCallback(fn, deps)`: deps가 같으면 같은 함수 객체를 돌려준다.
  - `useMemo(calc, deps)`: deps가 같으면 지난 계산 결과를 돌려준다. deps는 `Object.is`로 비교한다(react.dev "useMemo").
  - 렌더 밖(모듈 최상위)의 상수 객체는 원래 같은 참조다.

### 4. 상태를 어디에 두나 — 가장 싼 최적화

```text
  끌어올린 상태 (나쁨)                  내려 둔 상태 (좋음)
  <App q>                               <App>
   ├─ <input>                            ├─ <SearchBox q>  ← 키 입력은 여기만 재렌더
   └─ <List> 3000행 ← 키마다 재렌더       │    └─ <input>
                                          └─ <List> 3000행 ← 영향 없음
```

- 상태를 쓰는 곳 가까이 둘수록 재렌더 범위가 좁아진다(react.dev "memo"의 "Prefer local state"). memo 없이 같은 효과를 낸다.

### 실험: 3000행 + 입력창 — 키 5번에 Row가 몇 번 렌더되나

React 19.2.8 프로덕션 빌드(esbuild 0.28.2, `NODE_ENV=production`). Row 함수 본문에서 전역 카운터를 올린다. 입력창에 `hello`를 150ms 간격으로 친다.

```jsx
// app18.jsx 핵심 (scratchpad/wp/16/app18.jsx)
function RowImpl({ item, onSelect, style }) { window.__renders++; return <li style={style} onClick={() => onSelect(item.id)}>…</li>; }
const MemoRow = memo(RowImpl);
const rowStyle = { padding: 2 };                                    // 모듈 상수 = 같은 참조
function List({ setSelected }) {
  const onSelect = useCallback(id => setSelected(id), [setSelected]);
  return <ul>{items.map(it => <MemoRow key={it.id} item={it} onSelect={onSelect} style={rowStyle} />)}</ul>;
}
// plain       : App(q) 아래 <RowImpl … onSelect={id=>…} style={{padding:2}} /> × 3000
// memo-broken : App(q) 아래 <MemoRow  … onSelect={id=>…} style={{padding:2}} /> × 3000
// memo-ok     : App(q) 아래 <List> (memo + useCallback + 상수 style)
// colocate    : q를 <SearchBox>로 내림, 목록은 plain 그대로
// baseline    : 입력창만 (목록 없음)
```

측정: Row 렌더 수, Event Timing의 키 상호작용 `duration`(interactionId별 최대), CDP `Performance.getMetrics`의 `ScriptDuration`·`RecalcStyleDuration`·`LayoutDuration` 증가분(5번 입력 전체).

(실험, headless Chrome 151.0.7922.173, **CPU 4× 스로틀**, 기본 뷰포트, 2026-10-04, 3회 — 상호작용이 6개인 판은 입력창 클릭이 늦게 기록된 것으로 해석. 아래 표는 사실 점검 재실행 3회 × 2묶음을 합친 범위)

```text
plain 0 initialRowRenders 3000 {"rowRendersFor5Keys":15000,"keyInteractions":[304,224,200,208,168],"value":"hello","scriptMs":578,"styleMs":0,"layoutMs":5}
plain 1 initialRowRenders 3000 {"rowRendersFor5Keys":15000,"keyInteractions":[344,240,216,240,264],"value":"hello","scriptMs":668,"styleMs":1,"layoutMs":5}
plain 2 initialRowRenders 3000 {"rowRendersFor5Keys":15000,"keyInteractions":[208,328,280,224,192,192],"value":"hello","scriptMs":626,"styleMs":0,"layoutMs":6}
memo-broken 0 initialRowRenders 3000 {"rowRendersFor5Keys":15000,"keyInteractions":[384,240,192,232,272],"value":"hello","scriptMs":728,"styleMs":2,"layoutMs":9}
memo-broken 1 initialRowRenders 3000 {"rowRendersFor5Keys":15000,"keyInteractions":[168,360,240,208,224,208],"value":"hello","scriptMs":674,"styleMs":1,"layoutMs":5}
memo-broken 2 initialRowRenders 3000 {"rowRendersFor5Keys":15000,"keyInteractions":[304,200,248,224,232],"value":"hello","scriptMs":672,"styleMs":1,"layoutMs":7}
memo-ok 0 initialRowRenders 3000 {"rowRendersFor5Keys":0,"keyInteractions":[160,240,152,144,120,136],"value":"hello","scriptMs":206,"styleMs":1,"layoutMs":6}
memo-ok 1 initialRowRenders 3000 {"rowRendersFor5Keys":0,"keyInteractions":[144,184,160,200,192,208],"value":"hello","scriptMs":188,"styleMs":1,"layoutMs":6}
memo-ok 2 initialRowRenders 3000 {"rowRendersFor5Keys":0,"keyInteractions":[192,200,160,128,192,144],"value":"hello","scriptMs":176,"styleMs":1,"layoutMs":5}
colocate 0 initialRowRenders 3000 {"rowRendersFor5Keys":0,"keyInteractions":[152,120,128,128,160],"value":"hello","scriptMs":49,"styleMs":0,"layoutMs":6}
colocate 1 initialRowRenders 3000 {"rowRendersFor5Keys":0,"keyInteractions":[176,152,120,144,168,112],"value":"hello","scriptMs":50,"styleMs":1,"layoutMs":6}
colocate 2 initialRowRenders 3000 {"rowRendersFor5Keys":0,"keyInteractions":[152,144,120,104,104,112],"value":"hello","scriptMs":47,"styleMs":0,"layoutMs":5}
baseline 0 initialRowRenders 0 {"rowRendersFor5Keys":0,"keyInteractions":[48,64,16,16,16],"value":"hello","scriptMs":60,"styleMs":0,"layoutMs":7}
baseline 1 initialRowRenders 0 {"rowRendersFor5Keys":0,"keyInteractions":[56,40,16,16,16,16],"value":"hello","scriptMs":45,"styleMs":1,"layoutMs":6}
baseline 2 initialRowRenders 0 {"rowRendersFor5Keys":0,"keyInteractions":[40,24,24,16,24],"value":"hello","scriptMs":52,"styleMs":0,"layoutMs":8}
```

| 변형 | 키 5번 Row 렌더 | 스크립트 시간(5번 합) | 키 상호작용 |
|---|---|---|---|
| plain | 15,000 (= 3000 × 5) | 578~770ms | 160~424ms |
| memo-broken | 15,000 | 672~850ms | 152~464ms |
| memo-ok | 0 | 164~213ms | 120~240ms |
| colocate | 0 | 47~87ms(대부분 47~55) | 104~264ms |
| baseline(목록 없음) | — | 39~60ms | 16~64ms |

- **plain**: 키 한 번에 Row 3000개가 다시 렌더된다. 키 상호작용 다수가 200ms를 넘는다.
- **memo-broken**: memo를 씌웠지만 인라인 객체·함수 때문에 렌더 수는 그대로 15,000. 스크립트 시간은 plain과 같거나 조금 많다 — 범위는 겹치지만(672~850 vs 578~770ms) 세 묶음 모두 중앙값이 plain보다 컸다(674·830·728 vs 626·738·699ms). 해석: props 비교 비용만 더해졌다.
- **memo-ok**: Row 렌더 0. 그래도 스크립트 164~213ms(재실행 포함)가 남는다 — 해석: List가 재렌더되며 3000개 요소를 만들고 3000번 props를 비교하기 때문이다.
- **colocate**: 상태를 입력창 컴포넌트로 내리자 스크립트가 목록 없는 baseline 수준(대부분 47~55ms, 한 번씩 76·87ms)이 됐다. memo 없이 가장 쌌다.
- 남은 차이: colocate의 상호작용(104~264ms)이 baseline(16~64ms)보다 큰데 스크립트·스타일·레이아웃은 비슷하다. 사실 점검에서 `keydown` 항목을 세 조각으로 나눠 보니 차이는 presentation delay에 있었다(colocate 103~187ms vs baseline 12~35ms, input delay·processing은 둘 다 0~3ms). 해석: 3000행 문서의 페인트·합성 등 렌더링 비용이다. 어느 렌더링 단계인지는 나누지 않았다 [?]. 재렌더를 줄여도 큰 DOM 비용은 남는다 → 17 가상화.

## 쓰이는 자료구조·알고리즘

- **트리 diff 휴리스틱 O(n)**: 같은 레벨끼리, 타입이 같으면 갱신·다르면 교체, 자식은 key로 짝짓기(해시 맵). 일반 트리 편집 거리(고전 O(n³), 최신 결과도 n²보다 큼)를 포기하고 실용 가정을 둔 것이다(legacy.reactjs.org "Reconciliation").
- **얕은 비교(shallow equality)**: props 객체의 각 키를 `Object.is`로 한 단계만 비교. O(prop 수). 깊은 비교는 하지 않는다.
- **메모이제이션**: 같은 입력이면 저장해 둔 결과를 재사용 — [algorithm/21 DP 기초](../../algorithm/21-dp-basics/2-summary.md)(커리큘럼 25)의 메모이제이션과 같은 생각이다. 차이: React의 `useMemo`는 **직전 한 번**의 deps만 기억한다(캐시 크기 1). 입력이 번갈아 바뀌면 적중하지 않는다.
- **불변 데이터 + 참조 비교**: 상태를 제자리에서 바꾸지 않고 새 객체를 만들면 "바뀌었나?"를 O(1) 참조 비교로 안다. 제자리 변경(mutation)은 참조가 같아 변경을 놓친다.

## 적용 — 풀어나가는 법

1. **측정** — React DevTools 일반 설정의 "Highlight updates when components render", Profiler의 커밋별 렌더 시간, 또는 Event Timing으로 느린 상호작용을 찾는다(16 긴 태스크). 렌더 수만 보지 말고 시간을 본다.
2. **상태 위치부터** — 자주 바뀌는 상태(입력값·호버·스크롤 위치)를 쓰는 컴포넌트로 내린다. 무거운 트리는 `children`으로 받아 상태 변경 범위 밖에 둔다.

```jsx
// children 패턴: Layout의 상태가 바뀌어도 <HeavyTree/> 요소는 부모가 만든 같은 객체 → 재렌더 안 됨
function Layout({ children }) { const [open, setOpen] = useState(false); return <div>{/* … */}{children}</div>; }
<Layout><HeavyTree /></Layout>
```

3. **그다음 memo** — 자주, 같은 props로 재렌더되고, 렌더가 비싼 컴포넌트에만(react.dev "memo"가 든 조건). 넘기는 객체·함수는 상수·`useMemo`·`useCallback`으로 참조를 고정한다.
4. **비싼 계산은 `useMemo`** — react.dev는 `console.time`으로 재서 1ms 이상이면 고려하라고 한다. 코드가 `useMemo` 없이도 맞게 동작해야 한다(성능 최적화로만 의존).
5. **목록 자체가 크면** 메모이제이션이 아니라 가상화(17), 계산이 크면 양보·워커(16).
6. **자동화** — React Compiler는 memo에 해당하는 최적화를 자동으로 적용한다(react.dev "memo"). 수동 memo·useCallback이 줄지만, 상태 위치 설계는 여전히 사람 몫이다.

## 장애 시나리오와 대처

### 1. 타이핑 지연 — 최상위 상태 하나에 수천 개가 재렌더

- 현상: 검색창에 글자를 치면 한 박자 늦게 찍힌다.
- 보이는 형태: 키 입력 INP 200ms 초과, Profiler에서 키마다 목록 전체가 커밋에 포함. 위 실험 plain: 키 5번에 Row 15,000회, 상호작용 160~424ms(4× 스로틀, 재실행 포함).
- 원인: 입력 상태가 큰 목록의 공통 조상에 있다.
- 대처: 상태를 입력 컴포넌트로 내림(colocate: 스크립트 대부분 47~55ms). 필터 결과가 목록에 필요하면 목록 쪽만 memo하거나 `useDeferredValue`로 목록 갱신을 미룬다(React 18+ API — 동작 세부는 react.dev "useDeferredValue").

### 2. memo를 씌웠는데 효과가 없다

- 현상: `React.memo`를 붙였는데 Profiler에서 여전히 매번 렌더된다.
- 보이는 형태: Profiler 설정 "Record why each component rendered while profiling"을 켜면 props 변경이 이유로 표시된다. 위 실험 memo-broken: 15,000회 그대로, 스크립트는 plain과 같거나 조금 더.
- 원인: 렌더할 때마다 새 객체·배열·화살표 함수를 prop으로 넘긴다 → `Object.is` 비교가 항상 false.
- 대처: 상수는 모듈 밖으로, 계산 객체는 `useMemo`, 콜백은 `useCallback`. 또는 React Compiler.

### 3. memo 남발 — 비교 비용과 메모리만 늘어난다

- 현상: 모든 컴포넌트에 memo·useMemo·useCallback을 붙였는데 빨라지지 않고 코드만 복잡해졌다.
- 보이는 형태: props가 매번 바뀌는 컴포넌트에서 비교 비용이 더해짐(위 실험 memo-broken이 그 극단). 의존성 배열 누락으로 오래된 값(stale closure) 버그.
- 원인: 재렌더가 싸거나, props가 어차피 매번 바뀌는 곳에 memo를 썼다.
- 대처: 측정해서 비싼 곳에만. 상태 위치·children 패턴이 먼저다.

### 4. 상태를 제자리에서 바꿔 화면이 안 바뀐다

- 현상: `items.push(x); setItems(items)` 뒤 화면이 그대로다.
- 원인: 같은 참조를 넘겨 React가 "같다"로 판단(`Object.is`)한다. memo된 자식도 같은 이유로 건너뛴다.
- 대처: 새 배열·객체로 갱신(`setItems([...items, x])`). 불변 갱신이 참조 비교 최적화의 전제다.

### 5. 불안정한 key — 상태 소실과 DOM 재생성

- 현상: 목록 정렬 후 입력 중이던 값이 다른 행으로 옮겨 가거나 사라진다. 매 렌더 DOM이 다시 만들어진다.
- 원인: 인덱스 key(재정렬 시 짝이 틀어짐) 또는 `Math.random()` key(매번 새 컴포넌트).
- 대처: 데이터의 안정적 ID를 key로.

## 핵심 문장

- React에서 상태가 바뀌면 그 컴포넌트와 하위 트리가 (memo, 같은 요소 객체 재사용(children 패턴), React Compiler의 자동 최적화로 건너뛰지 않는 한) 다시 렌더되고, 재조정이 바뀐 DOM만 고친다 — 비용은 다시 렌더한 범위를 따라 커진다.
- `memo`는 props를 `Object.is`로 얕게 비교하므로, 렌더 중에 만든 객체·함수를 넘기면 무력화된다.
- 가장 싼 최적화는 상태를 쓰는 곳 가까이 두는 것이다 — 실험에서 상태 내리기가 memo보다 스크립트 시간이 적었다.
- 메모이제이션은 비교 비용과 메모리를 내고 재계산을 아끼는 거래이며, 적중하지 않으면 손해다.
- 재렌더를 0으로 만들어도 큰 DOM의 렌더링 비용은 남는다 — 그때는 가상화다.

## 관련 주제·근거

- 선행: [04 DOM과 이벤트 모델](../04-dom-and-event-model/2-summary.md), [16 긴 태스크와 웹 워커](../16-long-tasks-and-web-workers/2-summary.md)
- 후속: [17 목록 가상화](../17-list-virtualization/2-summary.md), [19 하이드레이션 비용](../19-hydration-cost-and-partial-hydration/2-summary.md), [21 컴포넌트와 상태 패턴](../21-component-and-state-patterns/2-summary.md), [23 증상 색인](../23-web-symptom-index/2-summary.md)
- 다른 영역: [language/06 값·참조·전달](../../language/06-values-references-passing/2-summary.md)(원고: [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md)), [algorithm/21 DP 기초](../../algorithm/21-dp-basics/2-summary.md), [software-design/42 UI 아키텍처 패턴](../../software-design/42-ui-architecture-patterns/2-summary.md)
- 근거
  - react.dev "memo" https://react.dev/reference/react/memo — `Object.is` 얕은 비교, "not a guarantee", 매번 다른 props면 무용, 상태 지역화·children 권고, React Compiler
  - react.dev "useMemo" https://react.dev/reference/react/useMemo — deps `Object.is`, 성능 최적화로만 의존, 1ms 기준
  - react.dev "useCallback" https://react.dev/reference/react/useCallback
  - legacy.reactjs.org "Reconciliation" https://legacy.reactjs.org/docs/reconciliation.html — O(n³) vs O(n) 휴리스틱, 두 가정, key
  - LIPIcs ESA 2025 논문 94 서론 https://drops.dagstuhl.de/storage/00lipics/lipics-vol351-esa2025/LIPIcs.ESA.2025.94/LIPIcs.ESA.2025.94.pdf — 트리 편집 거리 O(n³)(Demaine 외), 가중치 없는 경우 Mao O(n^2.9546) → O(n^2.6857)
  - vuejs.org "Rendering Mechanism" https://vuejs.org/guide/extras/rendering-mechanism.html · "Performance" https://vuejs.org/guide/best-practices/performance.html — Vue의 가상 DOM, 렌더 중 의존성 추적, "a child component only updates when at least one of its received props has changed"
  - React DevTools 설정 문구: facebook/react `packages/react-devtools-shared/src/devtools/views/Settings/GeneralSettings.js`·`ProfilerSettings.js`
- 실험 목록 (headless Chrome 151.0.7922.173 CPU 4×, React 19.2.8 프로덕션 빌드, esbuild 0.28.2, Node 20.19.6 + playwright-core 1.62.1, 127.0.0.1 로컬 서버, 2026-10-04)
  - 18-A 다섯 변형의 렌더 수·스크립트 시간·키 상호작용: `scratchpad/wp/16/app18.jsx` → `www/app18.js`, `www/r18.html`, `scratchpad/wp/16/exp18.js`(인자: 변형 목록, 스로틀 배율) — 3회씩
  - 사실 점검 재실행(같은 코드·같은 환경, 2026-10-04): 18-A 3회 × 2묶음(`scratchpad/wp/fc-16/out18.txt`·`out18-run2.txt`) — 렌더 수는 일치, 시간은 위 표 범위로 넓어졌다. 18-B colocate vs baseline `keydown` 세 조각 분해(`fc-16/fc18-split.js`, 2회씩, `out18-split.txt`)
