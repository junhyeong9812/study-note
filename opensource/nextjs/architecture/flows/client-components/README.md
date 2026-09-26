# 클라이언트 트리가 라우터 상태를 읽기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[클라이언트가 화면을 바꾸기까지](../client-router/README.md)는 리듀서가 상태를 **만드는** 쪽이었다. 여기는 그 상태를 **읽는** 쪽이다 — `<AppRouter>` 가 상태를 받아 Context 일곱 개로 풀어 내리고, `<LayoutRouter>` 가 세그먼트마다 그것을 좁히고, `usePathname()` 같은 훅이 가장 가까운 Context 에서 값을 꺼낸다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `APPROUTER` = `client/components/app-router.tsx`(657줄), `LAYOUTR` = `.../layout-router.tsx`(988줄), `NAVHOOKS` = `.../navigation.ts`(369줄), `USEAQ` = `.../use-action-queue.ts`(141줄), `APPRINST` = `.../app-router-instance.ts`(523줄), `HOOKCTX` = `shared/lib/hooks-client-context.shared-runtime.ts`(55줄), `ARCTX` = `shared/lib/app-router-context.shared-runtime.ts`(122줄).

## 위치

`packages/next` / `src/client/components` / `app-router.tsx` L579-L608 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/app-router.tsx#L579-L608))

## 실제 코드

`<AppRouter>` 의 안쪽 컴포넌트 `Router` 가 마지막에 돌려주는 것이 이 흐름 전체의 배선도다.

```tsx
// app-router.tsx L547-L576
  return (
    <>
      <HistoryUpdater appRouterState={state} />
      {process.env.TURBOPACK ? null : <RuntimeStylesForWebpack />}
      <NavigationPromisesContext.Provider
        value={instrumentedNavigationPromises}
      >
        <PathParamsContext.Provider value={pathParams}>
          <PathnameContext.Provider value={pathname}>
            <SearchParamsContext.Provider value={searchParams}>
              <GlobalLayoutRouterContext.Provider
                value={globalLayoutRouterContext}
              >
                {/* TODO: We should be able to remove this context. useRouter
                    should import from app-router-instance instead. It's only
                    necessary because useRouter is shared between Pages and
                    App Router. We should fork that module, then remove this
                    context provider. */}
                <AppRouterContext.Provider value={publicAppRouterInstance}>
                  <LayoutRouterContext.Provider value={layoutRouterContext}>
                    {content}
                  </LayoutRouterContext.Provider>
                </AppRouterContext.Provider>
              </GlobalLayoutRouterContext.Provider>
            </SearchParamsContext.Provider>
          </PathnameContext.Provider>
        </PathParamsContext.Provider>
      </NavigationPromisesContext.Provider>
    </>
  )
```

```text
 ★★★ Provider 가 **일곱 겹**이다 (`grep -c '\.Provider\( value\|$\)' app-router.tsx` = 7,
     여는 태그만 센 것. L542-544 의 OfflineProvider 는 Context 가 아니라 컴포넌트라 빠진다)

   NavigationPromisesContext   개발 전용 약속 묶음     (HOOKCTX L31)
   PathParamsContext           useParams()             (HOOKCTX L9)
   PathnameContext             usePathname()           (HOOKCTX L8)
   SearchParamsContext         useSearchParams()       (HOOKCTX L7)
   GlobalLayoutRouterContext   tree · focusAndScrollRef · nextUrl   (ARCTX L106)
   AppRouterContext            useRouter()             (ARCTX L92)
   LayoutRouterContext         useSelectedLayoutSegments() · <LayoutRouter>  (ARCTX L95)

 => 공개 훅 여섯 중 셋(useSearchParams · usePathname · useParams)은
    **맨 위 한 자리**의 값만 읽는다. 어느 세그먼트에서 불러도 같다
 => 세그먼트마다 다시 공급되는 것은 둘이다 — LayoutRouterContext
    (LAYOUTR L592 InnerLayoutRouter · L644 LoadingBoundaryProvider)와,
    개발 빌드에서만 NavigationPromisesContext(L584)
 => 그래서 useSelectedLayoutSegments 는 **부른 자리마다 답이 다르고**,
    useRouter 는 맨 위 객체에 가장 가까운 세그먼트의 bfcacheId 를 섞는다 [04]
 ★ 네 Context 는 `hooks-client-context` 에, 세 Context 는 `app-router-context` 에 있다.
   두 파일 다 첫 줄이 `'use client'` 다
 ★★ 소스 주석(L560-564)이 AppRouterContext 를 **없애고 싶다**고 적는다 —
   "useRouter should import from app-router-instance instead. It's only
    necessary because useRouter is shared between Pages and App Router."
```

## 동작 흐름

```text
 app-render.tsx L2408 · L2469 / app-index.tsx L379   createMutableActionQueue(initialState)
      |  서버(SSR)와 브라우저가 각자 한 번 만든다
      v
 <AppRouter actionQueue>        APPROUTER L579   (app-render L2422 · L2474, app-index L292)
      +-- useNavFailureHandler()                  L590
      +-- <RootErrorBoundary errorComponent={DefaultGlobalError}>   L604
            <Router>                               L154
      +-- useActionQueue(actionQueue)             L165   [01] 상태를 구독한다
      +-- canonicalUrl -> pathname · searchParams L168   [02]
      +-- tree -> pathParams (getSelectedParams)  L417   [02]
      +-- tree · cache -> layoutRouterContext     L437   [02]
      +-- 일곱 Provider 로 감싸 {cache.rsc} 를 그린다   L493 · L547
                |
                v
            cache.rsc   = 뿌리 세그먼트의 RSC. 그 안에 서버가 심은 <LayoutRouter> 가 있다
                |
 <LayoutRouter parallelRouterKey>   LAYOUTR L706    [03] 세그먼트마다 한 번
      +-- useContext(LayoutRouterContext)          L731  부모가 준 tree · cacheNode
      +-- parentTree[1][key] · parentCacheNode.slots[key]   L768 · L784
      +-- <InnerLayoutRouter>                      L491
            +-- cacheNode.rsc 를 그리고
            +-- LayoutRouterContext 를 **자기 세그먼트로 다시 공급**   L592
                |
                v
 usePathname() · useSearchParams() · useSelectedLayoutSegments() ...   [04]
      +-- useContext(가장 가까운 Provider)
```

1. [상태를 구독한다](01_subscribe/README.md) — `useReducer` 가 아니라 `useState` + `use()` 다.
2. [Context 를 만든다](02_provide/README.md) — URL 에서 둘, 트리에서 둘, 그리고 브라우저 history 를 가로챈다.
3. [`<LayoutRouter>` 가 세그먼트마다 그리는 것](03_layout-router/README.md) — 서버는 껍데기만 보내고 내용은 캐시에서 꺼낸다.
4. [훅이 Context 에서 값을 꺼낸다](04_hooks/README.md) — 브라우저에서는 한 줄, 서버에서는 렌더 모드마다 다르다.

```text
 ★★★ [클라이언트 라우터]가 확인한 사실과 맞는가 — 맞다. 단 한 겹이 더 있다

 [클라이언트 라우터] "reducer 는 useReducer 가 아니라 app-router-instance.ts 에서
                      직접 불리고, 상태는 모듈 전역 globalActionQueue 에 산다"

 이 흐름에서 본 것
   APPROUTER 는 **리듀서 본체(router-reducer.ts)를** import 하지 않는다 (L1-53 import 목록).
   같은 디렉터리의 보조 모듈 다섯(router-reducer-types · create-href-from-url · committed-state ·
   find-head-in-cache · compute-changed-path, L14 · L19 · L28 · L31 · L38)은 가져온다
   L165  const state = useActionQueue(actionQueue)
   USEAQ L64  React.useState<ReducerState>(actionQueue.state)
   USEAQ L94  actionQueue.dispatch(action, setState)   ← reducer 호출은 큐 안이다

 => 일치한다. 그리고 한 겹이 더 있다 —
   `<AppRouter>` 는 전역 `globalActionQueue` 를 읽지 않고 **prop 으로 받은** 큐를 쓴다.
   전역 변수에 넣는 일은 `createMutableActionQueue` 가 브라우저에서만 한다
     APPRINST L241  if (typeof window !== 'undefined') { ... globalActionQueue = actionQueue }
 => 서버(SSR)에서는 globalActionQueue 가 비어 있고, 큐는 렌더 한 번짜리 지역값이다
 ★ 전역을 읽는 쪽은 **React 밖에서 디스패치하는 함수**다 —
   `dispatchNavigateAction`(APPRINST L270, `<Link>` 가 link.tsx L310 에서 부른다) ·
   `dispatchTraverseAction`(APPRINST L310, popstate 핸들러가 부른다) 이
   `getAppRouterActionQueue().state.tree` 로 현재 트리를 읽는다.
   그 밖에 `publicAppRouterInstance.prefetch`(APPRINST L405 `getAppRouterActionQueue()`) ·
   `gesturePush`(L345 `getCurrentAppRouterState()`) · links.ts L339 도 전역을 읽는다
   그 둘이 부르는 dispatch 함수 자체는 USEAQ L15 의 모듈 변수 `dispatch` 에 산다 ([01])
```

## 결과가 쓰이는 곳

```text
 일곱 Context 의 값
      --> `next/navigation` 의 훅 여섯(useSearchParams · usePathname · useRouter ·
          useParams · useSelectedLayoutSegments · useSelectedLayoutSegment)  [04]
      --> `<Link>`(link.tsx L381) · `<Form>`(form.tsx L33) · ErrorBoundary(error-boundary.tsx L46)
          가 AppRouterContext 를 읽는다
      --> client-page.tsx L41-50 · client-segment.tsx L34 가 LayoutRouterContext 의
          `parentParams` 와 SearchParamsContext 를 읽어 클라이언트 페이지의 props 를 만든다

 cacheNode.rsc 가 그려진 React 트리
      --> 화면이다. 세그먼트 캐시가 채운 `rsc` / `prefetchRsc` 가 여기서 소비된다 [03]
          ([프리페치]가 채운 것을 `ppr-navigations.ts` 가 CacheNode 로 옮긴다)

 history.pushState / replaceState 의 가로채기
      --> 사용자 코드가 직접 부른 pushState 도 — `url` 인자가 있고(APPROUTER L344)
          `data.__NA` · `data._N` 이 없을 때(L338) — ACTION_RESTORE 로 바뀌어
          [클라이언트 라우터]의 리듀서로 간다 [02]
```

## 다루지 않는 것

리듀서와 액션 큐의 정렬·폐기 규칙(`APPRINST` L68-222 의 `runRemainingActions` · `runAction` · `dispatchAction` 중 [01]이 인용한 L153-173 밖)은 [클라이언트 라우터]의 범위다. `createInitialRouterState`(`create-initial-router-state.ts` 280줄), `publicAppRouterInstance`(APPRINST L392-513)의 메서드 본문과 `<Link>` 의 프리페치, `HotReloader`(`hot-reloader-app`)와 개발 오버레이, `RootErrorBoundary` · `RedirectBoundary` · `HTTPAccessFallbackBoundary` · `ErrorBoundary` 의 내부, `AppRouterAnnouncer`, `RuntimeStylesForWebpack`(APPROUTER L610-657), `useNavFailureHandler`(`nav-failure-handler.ts`), `findHeadInCache` 의 머리(head) 탐색, 스크롤·포커스 처리(LAYOUTR L60-486), `useOffline`, Pages Router 가 같은 Context 를 채우는 어댑터(`shared/lib/router/adapters.tsx` 중 [04]가 인용한 L47-55 · L92-108 · L111-124 밖)는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 상태를 구독한다](01_subscribe/README.md)
- [02 Context 를 만든다](02_provide/README.md)
- [03 `<LayoutRouter>` 가 세그먼트마다 그리는 것](03_layout-router/README.md)
- [04 훅이 Context 에서 값을 꺼낸다](04_hooks/README.md)
