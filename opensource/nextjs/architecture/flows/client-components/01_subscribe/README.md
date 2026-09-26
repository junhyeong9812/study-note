# 01 상태를 구독한다

상위: [클라이언트 트리가 라우터 상태를 읽기까지](../README.md)

`<AppRouter>` 가 라우터 상태를 받는 통로는 `useActionQueue` 하나다(호출처는 `app-router.tsx` L165 하나 — 저장소 전체 grep). 141줄짜리 파일인데, **React 의 `useState` 에 Promise 를 넣고 `use()` 로 푸는** 방식으로 바깥 상태를 React 에 잇는다.

## 위치

`packages/next` / `src/client/components` / `use-action-queue.ts` L61-L141 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/use-action-queue.ts#L61-L141))

## 실제 코드

dispatch 함수를 **렌더 중에 모듈 변수로 내보낸다.**

```ts
// use-action-queue.ts L77-L104
  // Because of a known issue that requires to decode Flight streams inside the
  // render phase, we have to be a bit clever and assign the dispatch method to
  // a module-level variable upon initialization. The useState hook in this
  // module only exists to synchronize state that lives outside of React.
  // Ideally, what we'd do instead is pass the state as a prop to root.render;
  // this is conceptually how we're modeling the app router state, despite the
  // weird implementation details.
  let nextDispatch: Dispatch<ReducerActions>

  if (process.env.NODE_ENV !== 'production') {
    const { useAppDevRenderingIndicator } =
      require('../../next-devtools/userspace/use-app-dev-rendering-indicator') as typeof import('../../next-devtools/userspace/use-app-dev-rendering-indicator')
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const appDevRenderingIndicator = useAppDevRenderingIndicator()

    nextDispatch = (action: ReducerActions) => {
      appDevRenderingIndicator(() => {
        actionQueue.dispatch(action, setState)
      })
    }
  } else {
    nextDispatch = (action: ReducerActions) =>
      actionQueue.dispatch(action, setState)
  }

  if (typeof window !== 'undefined') {
    dispatch = nextDispatch
  }
```

```text
 ★★★ 이유를 주석이 스스로 "영리하게 굴어야 한다" 고 적는다 (L77-83)

   "Because of a known issue that requires to decode Flight streams inside the
    render phase, we have to be a bit clever and assign the dispatch method to
    a module-level variable upon initialization. The useState hook in this
    module only exists to synchronize state that lives outside of React.
    Ideally, what we'd do instead is pass the state as a prop to root.render;
    this is conceptually how we're modeling the app router state, despite the
    weird implementation details."

 => 상태의 정본은 React 밖(액션 큐)에 있고, useState 는 **동기화용**이다
 => 이상형은 "root.render 에 상태를 prop 으로 넘기는 것" 이라고 적는다
 ★ 대입은 **브라우저에서만** 한다 (L102 `typeof window !== 'undefined'`).
   서버(SSR)에서는 모듈 변수 `dispatch` 가 null 로 남는다 (L15) —
   그때 `dispatchAppRouterAction` 을 부르면 L34-37 이 던진다
     'Internal Next.js error: Router action dispatched before initialization.'
 ★ 개발 빌드에서는 디스패치를 `useAppDevRenderingIndicator` 로 한 겹 감싼다 (L86-96)
```

## 동작 흐름

```text
 useActionQueue(actionQueue)                       USEAQ L61

 L64   [canonicalState, setState] = React.useState<ReducerState>(actionQueue.state)
         ★ 타입이 AppRouterState 가 아니라 **ReducerState** 다 — Promise 를 담을 수 있다
 L72   [state, setGesture] = useOptimistic(canonicalState)
         주석 L68-71 - experimental_gesturePush 용. 제스처 전환 중에는
           "a fork of the router state that represents the eventual target" 를 돌려준다
 L73   브라우저면 setGestureRouterState = setGesture   (읽는 쪽 = dispatchGestureState L46,
         부르는 곳 = APPRINST L379 하나)
 L92   nextDispatch = (action) => …   개발은 appDevRenderingIndicator 로 감싸고(L92-96),
                                     프로덕션은 actionQueue.dispatch(action, setState) (L98-99)
 L102  브라우저면 dispatch = nextDispatch      (위 실제 코드)
 L111  개발이면 Promise 상태에 `_debugInfo` 를 옮겨 붙인다 (L116-133)
         주석 L117-118 - useMemo 는 suspend 하면 버려지므로 **WeakMap** 으로 캐시한다
 L138  return isThenable(stateWithDebugInfo)
 L139    ? use(stateWithDebugInfo)    ← 상태가 Promise 면 **여기서 suspend**
 L140    : stateWithDebugInfo
```

`setState` 에 무엇이 들어가는지는 큐 쪽이 정한다.

```ts
// app-router-instance.ts L153-L173
  let resolvers: {
    resolve: (value: ReducerState) => void
    reject: (reason: any) => void
  } = { resolve: setState, reject: () => {} }

  // most of the action types are async with the exception of restore
  // it's important that restore is handled quickly since it's fired on the popstate event
  // and we don't want to add any delay on a back/forward nav
  // this only creates a promise for the async actions
  if (payload.type !== ACTION_RESTORE) {
    // Create the promise and assign the resolvers to the object.
    const deferredPromise = new Promise<AppRouterState>((resolve, reject) => {
      resolvers = { resolve, reject }
    })

    startTransition(() => {
      // we immediately notify React of the pending promise -- the resolver is attached to the action node
      // and will be called when the associated action promise resolves
      setState(deferredPromise)
    })
  }
```

```text
 ★★★ 디스패치하는 **그 순간** setState 에 **아직 안 풀린 Promise** 를 넣는다

 APPRINST L164  deferredPromise = new Promise(...)  resolve/reject 를 꺼내 둔다
 APPRINST L168  startTransition(() => setState(deferredPromise))
 ...
 APPRINST L131  (리듀서가 끝나면) actionQueue.state = nextState
 APPRINST L134  action.resolve(nextState)   ← 그 Promise 가 여기서 풀린다

 => React 입장에서 라우터 상태는 "Promise 였다가 값이 되는 것" 이다.
    USEAQ L139 의 use() 가 그 사이 suspend 한다
 ※ startTransition 안에서 set 하므로 React 가 이전 화면을 유지한 채 기다린다고 읽힌다.
   그것은 React 의 transition 의미론이고 이 저장소 코드가 적은 것은 아니다

 ★★ ACTION_RESTORE 만 이 Promise 를 **만들지 않는다** (L158-162)
   "most of the action types are async with the exception of restore
    it's important that restore is handled quickly since it's fired on the popstate event
    and we don't want to add any delay on a back/forward nav
    this only creates a promise for the async actions"
   => 그때 resolve 는 setState 그 자체다 (L156 `{ resolve: setState, reject: () => {} }`)
 ★★ 그런데 큐의 `action` 은 **async 함수**다 (APPRINST L233-236)
     action: async (state, action) => { const result = reducer(state, action); return result }
   async 함수의 반환은 언제나 Promise 라, runAction 의 `isThenable(actionResult)`(L138)는
   이 큐에서 언제나 참이고 동기 갈래 `handleResult(actionResult)`(L143-145)는 타지 않는다.
   (`AppRouterActionQueue` 를 만드는 곳은 `createMutableActionQueue` 하나 — 저장소 전체 grep)
 => restore 도 setState 는 **마이크로태스크 뒤**에 불린다. 피한 것은 transition Promise 이지
    비동기 자체가 아니다
   ※ "restore 를 빨리 처리하려는" 주석의 의도가 async 래퍼로 일부 무뎌졌다는 것은 내 해석이다
```

```text
 ★★ 리듀서가 **돌려준 Promise** 는 React 에 가지 않는다

 [클라이언트 라우터]가 본 대로 리듀서는 `Promise<AppRouterState> | AppRouterState` 를 돌려준다.
 그 Promise 는 async 래퍼(APPRINST L233)가 삼키고, runAction 이 `.then(handleResult)`(L139)로
 **풀린 값**만 actionQueue.state 에 넣는다 (L131).
 React 가 받는 Promise 는 리듀서의 것이 아니라 dispatchAction 이 새로 만든 `deferredPromise` 다

 => 그래서 USEAQ L111-136 이 개발 빌드에서 `_debugInfo` 를 **따로 옮겨 붙여야** 했다 —
    주석 L106-110 "We need to transfer the `_debugInfo` from the underlying Flight response
    onto the top-level promise that is passed to React (via `use`)"
 ★ 단 옮겨 붙이는 대상은 받은 state Promise 가 **아니다** — `Promise.resolve(state).then(...)`
   으로 **새 약속**을 만들어 거기에 `_debugInfo` 를 붙이고, 그 새 약속을 state 를 키로 한
   WeakMap 에 캐시한다 (L119-130). 옮기는 값은 풀린 상태의 `asyncState.debugInfo` 다
```

## 결과가 쓰이는 곳

```text
 useActionQueue 의 반환 (풀린 AppRouterState)
      --> APPROUTER L165 `const state = useActionQueue(actionQueue)`.
          [02]가 canonicalUrl · tree · cache · pushRef 를 여기서 꺼낸다

 모듈 변수 dispatch (USEAQ L15)
      --> dispatchAppRouterAction(L33)을 거쳐 쓰인다.
          부르는 곳 — APPROUTER L228(pageshow 복원) · L318(history 가로채기) ·
          app-call-server.ts L8(서버 액션) · ppr-navigations.ts L1799(트리 불일치 재시도) ·
          APPRINST 의 dispatchNavigateAction(L300) · dispatchTraverseAction(L320) ·
          publicAppRouterInstance.refresh(L479) · hmrRefresh(L503)   — 모두 여덟 곳

 setGestureRouterState
      --> dispatchGestureState(L46) — APPRINST L379 의 제스처 내비게이션만 쓴다

 suspend (use(state))
      --> `<AppRouter>` 전체가 멈춘다. 새 상태가 풀릴 때까지 트리가 바뀌지 않는다
```

## 다루지 않는 것

`runAction` · `runRemainingActions`(APPRINST L68-146)의 큐 진행 규칙과 폐기(`discarded`)·`needsRefresh` 처리, `dispatchAction` 의 나머지(L175-221 — 내비게이션이 대기 중인 액션을 폐기하고 앞지르는 규칙), `useAppDevRenderingIndicator`(`next-devtools/userspace`)의 본문, `refreshOnInstantNavigationUnlock`(USEAQ L23-31)과 테스트 API, 제스처 내비게이션(`gesturePush`, APPRINST L379 부근)의 상태 포크, React 의 `useOptimistic` · `use` · `startTransition` 내부 동작은 이 문서의 범위 밖이다.
