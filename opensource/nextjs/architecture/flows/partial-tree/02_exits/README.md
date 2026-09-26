# 02 출구 넷

상위: [내비게이션 요청이 트리를 중간부터 그리기까지](../README.md)

한 단에서 할 수 있는 일이 넷이다 — 트리 모양만 돌려주기, 머리(head)만 돌려주기, 여기서부터 그리기, 한 단 더 내려가기. 앞의 셋은 **여기서 끝난다.** 넷째만 재귀한다.

## 위치

`packages/next` / `src/server/app-render` / `walk-tree-with-flight-router-state.tsx` L135-L346 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/walk-tree-with-flight-router-state.tsx#L135-L346))

## 실제 코드

첫 출구 — PPR 이 꺼져 있으면 **컴포넌트를 하나도 그리지 않고** 돌려주는 갈래다 (블록 전체).

```tsx
// walk-tree-with-flight-router-state.tsx L135-L195
  if (
    isInsideSharedLayout &&
    !experimental.isRoutePPREnabled &&
    // If PPR is disabled, and this is a request for the route tree, then we
    // never render any components. Only send the router state.
    (parsedRequestHeaders.isRouteTreePrefetchRequest ||
      // Otherwise, check for the presence of a `loading` component.
      (isPrefetch &&
        !Boolean(modules.loading) &&
        !hasLoadingComponentInTree(loaderTreeToFilter)))
  ) {
    // Send only the router state.
    // TODO: Even for a dynamic route, we should cache these responses,
    // because they do not contain any render data (neither segment data nor
    // the head). They can be made even more cacheable once we move the route
    // params into a separate data structure.
    const overriddenSegment =
      flightRouterState &&
      // TODO: Why does canSegmentBeOverridden exist? Why don't we always just
      // use `actualSegment`? Is it to avoid overwriting some state that's
      // tracked by the client? Dig deeper to see if we can simplify this.
      canSegmentBeOverridden(actualSegment, flightRouterState[0])
        ? flightRouterState[0]
        : actualSegment

    const routerState = parsedRequestHeaders.isRouteTreePrefetchRequest
      ? // Route tree prefetch requests contain some extra information
        await createRouteTreePrefetch(
          loaderTreeToFilter,
          hintTree,
          prefetchInliningEnabled,
          cacheComponents,
          partialPrefetching,
          isStaticGeneration,
          isBuildTimePrerendering,
          getDynamicParamFromSegment,
          rootLayoutIncluded
        )
      : await createFlightRouterStateFromLoaderTree(
          loaderTreeToFilter,
          hintTree,
          prefetchInliningEnabled,
          cacheComponents,
          partialPrefetching,
          isStaticGeneration,
          isBuildTimePrerendering,
          getDynamicParamFromSegment,
          query,
          rootLayoutIncluded
        )

    return [
      [
        overriddenSegment,
        routerState,
        null,
        [null, null],
        true,
      ] satisfies FlightDataSegment,
    ]
  }
```

```text
 ★★★ 이 갈래는 v16.3.6 기본 설정에서 **도달한다** — 단 **동적 라우트와 개발 서버**에서다

   isInsideSharedLayout && !experimental.isRoutePPREnabled && (
     route tree 프리페치 요청이거나
     || (프리페치이고 이 단에도 아래에도 loading 이 없다)
   )

 => PPR 은 cacheComponents 로만 켜진다 (server/config.ts L574-578 · L1603-1606).
    cacheComponents 는 기본이 꺼져 있으므로 PPR 조건은 대부분 참이다.
    그러나 프로덕션의 **정적** 라우트는 RSC · `/_tree` 요청 모두 캐시의 페이로드로 끝나
    이 함수까지 오지 않는다 (app-page-runtime.ts L557-601 · L1906-1952)
 ★ PPR 이 cacheComponents 없이 켜지는 예외도 있다 — Instant Navigation Testing
   (app-page-runtime.ts L457-473 `couldSupportPPR || isInstantNavigationTest`)
 => 주석 L115-118 - "Pre-PPR, the `loading` component signals to the router how deep to
    render the component tree to ensure prefetches are quick and inexpensive."
 ★ [트리 조립] [02]의 CCTREE L535-567 과 **같은 규칙이 여기 한 번 더** 있다.
   그쪽은 전체 조립 경로, 이쪽은 내비게이션 요청 경로다
 ★ 주석 L147-150 TODO - 이 응답은 렌더 데이터가 없으니 동적 라우트라도 캐시해야 한다
```

## 동작 흐름

```text
 ① 트리만 보낸다   L135-195   (위 실제 코드)
 L160    route tree 프리페치면 createRouteTreePrefetch(...)   (호출은 L162)       ← **PPR 꺼진 동적 라우트의 `/_tree`**
           `/_tree` 요청은 라우터 상태 헤더를 싣지 않으므로(cache.ts L1944-1948) flightRouterState 가
           undefined 이고 **루트에서 곧바로** 여기로 나간다 — "중간부터" 가 아니다
 L173    아니면 createFlightRouterStateFromLoaderTree(...)
 L186    return [[overriddenSegment, routerState, null, [null, null], true]]
           셋째(seed) 자리에 **null** — 그린 것이 없다. 넷째 [null, null] 은 head 다

 ② 머리만 보낸다   L199-237
 L199    flightRouterState[3] === 'metadata-only' 이면
           주석 L197-198 - "This flag is sent by the client to request only the metadata
             for a page. No segment data."
 L228    return [[..., routerState, ...]]   ← 세그먼트 데이터 없이 head 만

 ③ 여기서 그린다   L239-292
 L239    renderComponentsOnThisLevel 이면 ([01])
 L249      routerState = createFlightRouterStateFromLoaderTree(이 자리의 로더 트리, ...)
 L264      seedData = await createComponentTree({ loaderTree: loaderTreeToFilter,
                                                   parentParams: currentParams, ... })
           ← [트리 조립]의 그 함수. **이 자리부터** 조립한다
 L283      return [[overriddenSegment, routerState, seedData, rscHead, ...]]

 ④ 한 단 더 내려간다   L317-345
 L320    for (const parallelRouteKey of parallelRoutesKeys) {
 L323      subPaths = await walkTreeWithFlightRouterState({
             flightRouterState: flightRouterState && flightRouterState[1][parallelRouteKey],
             parentIsInsideSharedLayout: isInsideSharedLayout, ... })
 L340      각 subPath 앞에 [actualSegment, parallelRouteKey] 를 붙인다
 L345    return paths
```

```text
 ★★ ④ 는 슬롯을 **순차로** 돈다 (L320-343)

   for (const parallelRouteKey of parallelRoutesKeys) {
     const subPaths = await walkTreeWithFlightRouterState({...})

 => [트리 조립] [02]는 `Promise.all` 로 형제 슬롯을 **병렬**로 만들었다 (CCTREE L510).
    여기는 `for … await` 라 한 슬롯이 끝나야 다음 슬롯으로 간다
 ※ 이유는 소스에 없다
 ★ 그러나 ④ 는 **그리지 않는** 단을 지나가는 것이다. 실제로 그리는 ③ 안의
   createComponentTree 는 그 아래를 여전히 Promise.all 로 만든다
```

```text
 ★ ④ 는 **빈 배열**을 돌려줄 수 있다 (L317 `paths = []` 에서 시작)
   슬롯이 없는 잎(페이지)까지 ①~③ 어디에도 걸리지 않고 내려오면 for 가 한 번도 돌지 않는다
 => 클라이언트 트리가 끝까지 같고 'refetch' 도 없으면 flightData 가 `[]` 다 —
    그릴 세그먼트가 하나도 없는 응답이다
 ※ 클라이언트가 이런 요청을 보내는 경로가 있는지는 확인하지 않았다
```

```text
 ★★ 결과의 모양 — **경로의 배열**

 ① ② ③ 이 돌려주는 것   [[segment, routerState, seed, head, ...]]   (경로 하나)
 ④ 가 돌려주는 것       그 경로들 앞에 [segment, 슬롯이름] 을 계속 붙인 배열

 => 최종 결과는 "루트 → … → 그리기 시작한 자리" 까지의 **경로마다 한 항목**이다
 => 병렬 슬롯 둘이 모두 새로 그려져야 하면 항목도 둘이다
 => [App Router]의 L760 이 맨 앞의 '' (루트) 세그먼트를 잘라 낸다
 ★ 같은 파일의 createFullTreeFlightDataForNavigation 안 TODO L414-415 가 그 자르기를 의심한다 —
   "app-render slices this Segment off. why is that valid, and why are we including it
    in the first place?" ([03])
```

```text
 ★ 같은 TODO 가 **두 번** 있다 — canSegmentBeOverridden

   L153-155 · L242-244 (삼항 자체는 ② 의 L202 까지 **세 번** 쓰인다 — L156 · L202 · L245)
     "TODO: Why does canSegmentBeOverridden exist? Why don't we always just use
      `actualSegment`? Is it to avoid overwriting some state that's tracked by the
      client? Dig deeper to see if we can simplify this."

 => 클라이언트가 보낸 세그먼트를 그대로 쓸지 서버의 것으로 바꿀지 고르는 함수(L429)가
    **왜 있는지 모른다**고 소스가 적는다
```

## 결과가 쓰이는 곳

```text
 ① 의 routerState (seed 없음)
      --> 클라이언트가 **트리 모양만** 받는다. [프리페치]의 LoadingBoundary 전략이
          받는 응답은 이것 **또는 ③** 이다 — 트리에 loading 이 있으면 ③ 으로 떨어지고
          createComponentTree 가 loading 아래를 잘라 낸다 (CCTREE L533-567)

 ① 의 createRouteTreePrefetch 결과
      --> PPR 꺼진 동적 라우트의 `/_tree` 응답 ([트리 조립] [04]의 빌드 버퍼와 배타적이다)

 ③ 의 seedData
      --> [트리 조립]의 CacheNodeSeedData 튜플. [PPR 내비게이션]이 그 경로에 끼운다

 ④ 의 경로 배열
      --> 여러 슬롯이 따로 바뀌는 내비게이션을 한 응답에 담는다
```

## 다루지 않는 것

`createRouteTreePrefetch`(CFRS L197) · `createFlightRouterStateFromLoaderTree`(CFRS L168)가 prefetch hint 와 inlining 을 넣는 방식, `canSegmentBeOverridden`(L429-438)의 판정, `hasLoadingComponentInTree` 의 판정, `FlightDataSegment` 튜플의 나머지 칸, ② 를 요청하는 클라이언트 쪽(cache.ts L354)의 조건, 서버 액션 응답에서 이 함수가 쓰이는 방식은 이 문서의 범위 밖이다.
