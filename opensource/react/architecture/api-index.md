# API 역인덱스

상위: [React 아키텍처 지도](README.md)

공개 API 에서 흐름으로 거꾸로 찾는 표다. "이 함수를 부르면 어디로 가는가" 를 묻는다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 대상은 **react-dom 클라이언트 빌드**다.

## 시작점

| API | 하는 일 | 흐름 |
|---|---|---|
| `createRoot(container)` | `FiberRoot` 와 `HostRoot` fiber 를 만든다 | [마운트](flows/mount/README.md) |
| `root.render(<App/>)` | 루트에 갱신을 걸고 스케줄한다 | [마운트](flows/mount/README.md) |
| `hydrateRoot` | 같은 길인데 수화 플래그가 붙는다 | [마운트](flows/mount/README.md) |
| `root.unmount()` | `null` 을 렌더해 트리를 걷어낸다 | [마운트](flows/mount/README.md) |
| `flushSync(fn)` | 실행 컨텍스트를 확인하고 동기로 밀어붙인다 | [스케줄링](flows/scheduling/README.md) |

## 상태를 바꾸는 것

| API | 어디로 가는가 | 흐름 |
|---|---|---|
| `useState` | `mountState` → `dispatchSetState` → `scheduleUpdateOnFiber` | [훅](flows/hooks/README.md) → [스케줄링](flows/scheduling/README.md) |
| `useReducer` | `useState` 와 같은 길. `useState` 가 reducer 고정판이다 | [훅](flows/hooks/README.md) |
| `setState` (클래스) | `enqueueUpdate` → `scheduleUpdateOnFiber`. 상태가 되는 것은 렌더 때 `processUpdateQueue` 에서다 | [업데이트 큐](flows/update-queue/README.md) → [스케줄링](flows/scheduling/README.md) |
| `setState(x, cb)` 의 `cb` | `queue.callbacks` 에 쌓이고 `Callback` 플래그가 선다. 커밋 레이아웃 패스에서 불린다 | [업데이트 큐](flows/update-queue/05_capturedAndCallbacks/README.md) |
| `replaceState` | tag 가 `ReplaceState`. 병합하지 않고 payload 로 통째로 갈아끼운다 | [업데이트 큐](flows/update-queue/04_getStateFromUpdate/README.md) |
| `forceUpdate` | tag 가 `ForceUpdate`. 상태를 안 바꾸고 모듈 전역 `hasForceUpdate` 만 세운다 | [업데이트 큐](flows/update-queue/04_getStateFromUpdate/README.md) |
| `root.render(el, cb)` 의 `cb` | 같은 큐를 쓴다. `commitRootCallbacks` 가 부르고 `this` 는 첫 호스트 자식이다 | [업데이트 큐](flows/update-queue/05_capturedAndCallbacks/README.md) |
| `useCacheRefresh` | `CacheComponent` 나 `HostRoot` 조상을 찾아 **클래스 큐**에 업데이트를 건다 | [업데이트 큐](flows/update-queue/README.md) |
| `useOptimistic` | 언제나 동기다. 트랜지션과 얽히지 않는다 | [훅](flows/hooks/README.md) |
| `useSyncExternalStore` | 스냅샷이 달라지면 `markWorkInProgressReceivedUpdate` | [훅](flows/hooks/README.md) |

```text
 setState 가 렌더를 스케줄하지 않는 갈래가 셋이다

 조기 바이아웃   큐가 비었고 다음 상태가 지금과 같을 때
 렌더 단계 갱신   렌더 중에 부른 setState — 루프가 처리한다
 fiber 가 분리됨  이미 언마운트된 경우

 [훅]의 dispatchSetState 문서에 있다
```

## 우선순위를 정하는 것

| API | 하는 일 | 흐름 |
|---|---|---|
| `startTransition` | 트랜지션 lane 을 뽑고 그 안의 갱신을 얽는다 | [lane 우선순위](flows/lanes/README.md) |
| `useTransition` | 위 + `isPending` 상태 | [훅](flows/hooks/README.md) |
| `useDeferredValue` | Deferred lane 을 낳고 기존 lane 과 얽는다 | [lane 우선순위](flows/lanes/README.md) |

```text
 "왜 이것이 먼저 도는가" 의 답은 전부 lane 에 있다

 낮은 비트 = 높은 우선순위
 Default 는 Transition 을 끊지 않는다
 오래 기다리면 만료돼 동기로 밀린다

 [lane 우선순위] 흐름에 있다
```

## 효과를 거는 것

| API | 언제 도는가 | 흐름 |
|---|---|---|
| `useInsertionEffect` | 커밋의 **mutation** 패스. DOM 을 건드리기 전. 이 안에서 setState 하면 DEV 가 경고한다 | [커밋](flows/commit/README.md) → [커밋 이펙트](flows/commit-effects/README.md) |
| `useLayoutEffect` | cleanup 은 mutation, 콜백은 **layout** 패스 — tag 가 말하는 단계는 **콜백 쪽**이다 | [커밋](flows/commit/README.md) → [커밋 이펙트](flows/commit-effects/README.md) |
| `useEffect` | 커밋 **뒤** 별도 태스크. sync lane 이면 같은 태스크 안 | [패시브 이펙트](flows/passive-effects/README.md) → [커밋 이펙트](flows/commit-effects/README.md) |
| 이펙트가 돌려주는 cleanup | `Effect` 가 아니라 한 칸짜리 `EffectInstance` 에 담긴다. 그래서 렌더를 넘어 산다 | [커밋 이펙트](flows/commit-effects/README.md) |
| 이펙트 안에서 던지면 | 그 fiber 의 **남은 이펙트가 건너뛰어진다**. cleanup 쪽은 이펙트마다 잡아 계속 돈다 | [커밋 이펙트](flows/commit-effects/README.md) |
| Offscreen 으로 숨겼다 보이면 | deps 가 그대로여도 이펙트가 다시 돈다 (`HookHasEffect` 를 빼고 부른다) | [커밋 이펙트](flows/commit-effects/README.md) |
| 함수 `ref` 의 반환값 | cleanup 으로 저장된다. 그러면 뗄 때 `ref(null)` 을 안 부른다 | [커밋 이펙트](flows/commit-effects/README.md) |
| `<Profiler onRender>` | 프로파일링 빌드에서만 돈다. `onPostCommit` 은 `Passive` 플래그가 붙어야 온다 | [커밋 이펙트](flows/commit-effects/README.md) |
| `componentDidMount` | layout 패스. `root.current` 교체 **뒤**. `Update \| LayoutStatic` 이 렌더 때 선다 | [커밋](flows/commit/README.md) → [클래스 컴포넌트](flows/class-component/README.md) |
| `componentWillUnmount` | mutation 패스. `root.current` 교체 **앞**. 부르기 직전 `instance.props`/`state` 를 current 것으로 덮어쓴다 | [커밋](flows/commit/README.md) |
| `getSnapshotBeforeUpdate` | before-mutation 패스. 있으면 `Snapshot` 플래그가 선다 — 다만 **이어서 마운트하는 길에서는 예약되지 않는다** | [커밋](flows/commit/README.md) → [클래스 컴포넌트](flows/class-component/README.md) |
| `componentDidUpdate` | layout 패스. `prevProps` 는 커밋이 `current.memoizedProps` 로 따로 만들어 넘긴다 | [커밋](flows/commit/README.md) → [클래스 컴포넌트](flows/class-component/README.md) |
| `getDerivedStateFromProps` | 렌더 단계. ★ **바이아웃한 렌더에서는 안 불린다** | [클래스 컴포넌트](flows/class-component/README.md) |
| `shouldComponentUpdate` | 렌더 단계. `forceUpdate()` 면 아예 건너뛴다. `PureComponent` 보다 우선한다 | [클래스 컴포넌트](flows/class-component/README.md) |
| `componentWillMount` / `UNSAFE_` | 새 API(`getDerivedStateFromProps`·`getSnapshotBeforeUpdate`)가 하나라도 있으면 **안 불린다** | [클래스 컴포넌트](flows/class-component/README.md) |
| `componentWillReceiveProps` / `UNSAFE_` | 같은 조건으로 꺼진다. props 나 컨텍스트가 바뀐 때만 | [클래스 컴포넌트](flows/class-component/README.md) |
| `componentWillUpdate` / `UNSAFE_` | 같은 조건으로 꺼진다. 업데이트 경로에만 있다 | [클래스 컴포넌트](flows/class-component/README.md) |
| `constructor` | `new ctor(props, context)`. StrictMode DEV 는 두 번 만들고 **두 번째를 쓴다** | [클래스 컴포넌트](flows/class-component/README.md) |
| `render` | `instance.render()`. StrictMode DEV 는 두 번 부르고 **첫 번째를 쓴다** | [클래스 컴포넌트](flows/class-component/README.md) |
| `this.refs` | 마운트에서만 `{}` 로 초기화된다. 문자열 ref 의 잔재 | [클래스 컴포넌트](flows/class-component/README.md) |
| `this.replaceState` | 공개 API 가 아니다 — deprecated getter 라 경고하고 `undefined` 를 준다 | [클래스 컴포넌트](flows/class-component/README.md) |

```text
 ★ 세 이펙트가 도는 순서

 mutation   useInsertionEffect (cleanup + 콜백)
            useLayoutEffect 의 cleanup
            componentWillUnmount
   -------- root.current = finishedWork --------
 layout     useLayoutEffect 의 콜백
            componentDidMount / componentDidUpdate
            ref 붙이기
   -------- 페인트 --------
 passive    useEffect 의 cleanup 그리고 콜백

 교체 줄이 가운데 있는 이유를 주석이 적는다 -
 언마운트는 옛 트리를, 마운트는 새 트리를 봐야 한다
```

## 값을 기억하는 것

| API | 어디서 처리되는가 | 흐름 |
|---|---|---|
| `useMemo` / `useCallback` | 훅 리스트에 deps 와 값을 담는다 | [훅](flows/hooks/README.md) |
| `useRef` | 훅 리스트에 객체 하나를 담는다 | [훅](flows/hooks/README.md) |
| `memo(Component)` | `MemoComponent` / `SimpleMemoComponent` tag | [beginWork](flows/begin-work/README.md) |

## 트리 모양을 바꾸는 것

| API | tag | 흐름 |
|---|---|---|
| `<Suspense>` | `SuspenseComponent` | [에러와 Suspense](flows/throw/README.md) |
| `<SuspenseList>` | `SuspenseListComponent` — completeWork 안에 드라이버 루프가 있다 | [completeWork](flows/complete-work/README.md) |
| `lazy(fn)` | `LazyComponent` → 해결되면 원래 tag 로 | [beginWork](flows/begin-work/README.md) |
| `forwardRef` | `ForwardRef` tag, `renderWithHooks` 로 들어간다 | [훅](flows/hooks/README.md) |
| `createContext` / `useContext` | `ContextProvider` / `readContext` | [beginWork](flows/begin-work/README.md) |
| `<Profiler>` | `Profiler` tag. 비프로파일 빌드에선 대부분 no-op | [completeWork](flows/complete-work/README.md) |
| `createPortal` | `HostPortal` tag, `pushHostContainer` | [completeWork](flows/complete-work/README.md) |

## 끊길 때

| 상황 | 어디로 가는가 | 흐름 |
|---|---|---|
| `use(promise)` 가 대기 중 | `SuspenseException` 을 던진다 | [에러와 Suspense](flows/throw/README.md) |
| 컴포넌트가 에러를 던짐 | 경계를 찾아 올라간다 | [에러와 Suspense](flows/throw/README.md) |
| `getDerivedStateFromError` | 에러 업데이트의 **payload** — 렌더 단계. `getStateFromUpdate` 가 부른다 | [에러와 Suspense](flows/throw/README.md) → [업데이트 큐](flows/update-queue/04_getStateFromUpdate/README.md) |
| `componentDidCatch` | 에러 업데이트의 **callback** — 커밋 단계. 로깅도 이 콜백이 한다 | [에러와 Suspense](flows/throw/README.md) → [업데이트 큐](flows/update-queue/05_capturedAndCallbacks/README.md) |
| 리소스가 준비 안 됨 | `completeWork` 가 `SuspenseyCommitException` 을 던진다 | [completeWork](flows/complete-work/README.md) |
| `onRecoverableError` | 커밋 끝에서 불린다. `catch` 로 감싸지 않는다 | [커밋](flows/commit/README.md) |

```text
 ★ 에러 경계는 클래스 컴포넌트뿐이다

 경계를 찾는 switch 에 HostRoot / ClassComponent / OffscreenComponent 셋인데
 사용자가 정의하는 것은 ClassComponent 뿐이다
   HostRoot 는 루트를 null 로 언마운트하는 최후 수단
   OffscreenComponent 는 숨은 트리의 prerender 중단

 useErrorBoundary 같은 훅은 저장소에 없다
```

## 훅이 아닌데 훅처럼 보이는 것

```text
 use(usable)
   훅 리스트를 쓰지 않는다. 별도 위치 카운터를 쓴다
   => if 안에서 불러도 된다

 useContext
   훅 리스트가 아니라 fiber.dependencies 에 붙는다
   네 디스패처에서 같은 함수(readContext)다

 useDebugValue
   mount 와 update 가 같은 함수다 (이름만 둘)

 useHostTransitionStatus / useMemoCache
   렌더용 세 디스패처에서 같은 함수다

 자세한 것은 [훅]의 spi 에 대조표가 있다
```

## 자주 만나는 에러 메시지

| 메시지 | 어디서 나는가 | 흐름 |
|---|---|---|
| `Invalid hook call.` | `ContextOnlyDispatcher` 의 22개 항목 | [훅](flows/hooks/README.md) |
| `Rendered more hooks than during the previous render.` | `updateWorkInProgressHook` — 그 자리에서 즉시 | [훅](flows/hooks/README.md) |
| `Rendered fewer hooks than expected.` | `finishRenderingHooks` — 렌더가 끝난 뒤 | [훅](flows/hooks/README.md) |
| `Too many re-renders.` | 렌더 단계 갱신 루프가 25회를 넘겼을 때 | [훅](flows/hooks/README.md) |
| `Maximum update depth exceeded.` | 커밋 쪽은 throw, `useEffect` 쪽은 DEV 경고 | [패시브 이펙트](flows/passive-effects/README.md) |
| `Unknown unit of work tag` | `beginWork` / `completeWork` 의 switch 밖 — 둘 다 닿지 않는다 | [beginWork](flows/begin-work/README.md) |
| `Should not already be working.` | 렌더·커밋 재진입 방어선 | [렌더 루프](flows/render-loop/README.md) |
| `Cannot flush passive effects while already rendering.` | 패시브 재진입 방어선 | [패시브 이펙트](flows/passive-effects/README.md) |
| `Context can only be read while React is rendering.` | 렌더 밖에서 `readContext` | [훅](flows/hooks/README.md) |

```text
 ★ 훅 개수 검사에 구멍이 하나 있다

 "더 많다" 는 그 자리에서 던지고
 "더 적다" 는 렌더 끝에 잡는데,
 훅을 **하나도** 부르지 않고 일찍 반환하면 어느 쪽에도 안 걸린다

 그러면 다음 렌더에서 마운트 디스패처가 골라져
 훅 상태가 조용히 초기화된다. 에러가 아니라 무음 리셋이다

 [훅]의 훅 리스트 문서에 있다
```

## 이 표에 없는 것

서버 전용 API(`renderToString`, `renderToPipeableStream`, 서버 컴포넌트), `react-dom` 의 이벤트 시스템과 합성 이벤트, `createPortal` 이후의 DOM 조작, `unstable_*` 실험 API 대부분, DevTools 전용 표면, `act()` 의 테스트 유틸리티 동작은 이 지도의 범위 밖이다.
