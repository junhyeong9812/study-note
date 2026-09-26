# 01 어디서부터 그리는가

상위: [내비게이션 요청이 트리를 중간부터 그리기까지](../README.md)

서버는 로더 트리(`[segment, parallelRoutes, modules]`)와 클라이언트가 보낸 FlightRouterState 를 **나란히** 한 단씩 내려간다. 둘이 어긋나거나 클라이언트가 "여기서부터 다시" 라고 표시한 자리에서 멈추고, 거기서부터 그린다.

## 위치

`packages/next` / `src/server/app-render` / `walk-tree-with-flight-router-state.tsx` L89-L133 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/walk-tree-with-flight-router-state.tsx#L89-L133))

## 실제 코드

멈출 자리를 정하는 조건이 셋이다.

```tsx
// walk-tree-with-flight-router-state.tsx L104-L113
  /**
   * Decide if the current segment is where rendering has to start.
   */
  const renderComponentsOnThisLevel =
    // No further router state available
    !flightRouterState ||
    // Segment in router state does not match current segment
    !matchSegment(actualSegment, flightRouterState[0]) ||
    // Explicit refresh
    flightRouterState[3] === 'refetch'
```

```text
 ★★★ 셋 중 하나면 **이 단에서 그린다**

   !flightRouterState                         클라이언트가 이 자리 아래를 **모른다**
   !matchSegment(actualSegment, 클라이언트 [0])   세그먼트가 **다르다** — 새 경로다
   flightRouterState[3] === 'refetch'          클라이언트가 **다시 달라고** 표시했다

 ★★★ 주 경로에서 시작점을 정하는 것은 **셋째 조건('refetch')** 이다
   프리페치된 라우트로 가는 내비게이션 — 클라이언트는 **목적지** 트리를 보내고,
     새 데이터가 필요한 가장 위 세그먼트에 'refetch' 를 붙인다
     (ppr-navigations.ts L866-869 "The "refetch" marker is set on the top-most segment that
      requires new data"). 세그먼트는 모두 일치하므로 둘째 조건은 걸리지 않는다
   프리페치가 없는 내비게이션(navigateToUnknownRoute) — 클라이언트는 **현재** 트리를 보낸다
     (navigation.ts L497-501). 이때만 둘째 조건(어긋남)이 시작점을 정한다 —
     `/blog/a` → `/blog/b` 면 `[slug]` 에서 'a' ≠ 'b' 라 거기서 그린다
   전체 새로고침·HMR — `['', {}, null, 'refetch']` 를 보내 **루트부터** (navigation.ts L459-464)
 => 'refetch' 는 refresh 전용이 아니라 **동적 내비게이션의 기본 장치**다
```

## 동작 흐름

```text
 walkTreeWithFlightRouterState   WALKTREE L28

 L72   [segment, parallelRoutes, modules] = loaderTreeToFilter
 L82   rootLayoutAtThisLevel = layout 이 있고 아직 루트 레이아웃을 안 지났으면
 L90   segmentParam = getDynamicParamFromSegment(...)
 L91   currentParams = 부모 파라미터 + 이 세그먼트 파라미터
         주석 L89 - "Because this function walks to a deeper point in the tree to start
           rendering we have to track the dynamic parameters up to the point where
           rendering starts"
 L99   actualSegment = addSearchParamsIfPageSegment(...)   ← 페이지면 쿼리까지 붙인다
 L107  renderComponentsOnThisLevel = (위 실제 코드)
 L130  isInsideSharedLayout = renderComponentsOnThisLevel
                             || parentIsInsideSharedLayout
                             || flightRouterState[3] === 'inside-shared-layout'
```

```text
 ★★ 그리지 않고 지나가도 **파라미터와 CSS 는 쌓는다**

 파라미터  L91 — 그리는 자리에서 createComponentTree 에 parentParams 로 넘긴다 (L269)
           => [트리 조립]이 루트부터 쌓던 것을 여기서는 **내려가며** 쌓는다
 CSS       L294-315 — 이 단을 그리지 않아도 layout 이 있으면 그 CSS·JS·폰트를
           injected 집합에 **넣어 둔다**
           주석 L294-296 - "If we are not rendering on this level we need to check if the
             current segment has a layout. If so, we need to track all the used CSS to make
             the result consistent."
 => 클라이언트가 이미 가진 레이아웃의 스타일을 **다시 주입하지 않으려는** 장부다
```

```text
 ★★ 'inside-shared-layout' — 같아도 "새 쪽" 으로 치라는 표시 (L120-133)

 주석 L120-125
   "Check if we're inside the "new" part of the navigation — inside the shared layout.
    In the case of a prefetch, this can be true even if the segment matches, because the
    client might send a matching segment to indicate that it already has the data in its
    cache. But in order to find the correct loading boundary, we still need to track where
    the shared layout begins."

 => 프리페치에서 클라이언트는 **이미 가진 데이터**를 세그먼트가 같은 것으로 표시한다.
    그래도 서버는 "공유 레이아웃이 어디서 시작하는가" 를 알아야 loading 경계를 찾는다
 => 그래서 그리지는 않되 "안쪽이다" 라는 사실만 아래로 물려준다 (L329 parentIsInsideSharedLayout)
 ★ 이 값이 [02]의 첫 출구(트리만 보내기)의 조건이 된다
 ★ 이 표지를 붙이는 클라이언트 자리는 scheduler.ts L1699-1700 하나다 (grep)
```

## 결과가 쓰이는 곳

```text
 renderComponentsOnThisLevel
      --> [02]의 셋째 출구. 여기서 createComponentTree 가 돈다

 isInsideSharedLayout
      --> [02]의 첫 출구 조건. 그리고 재귀로 아래 단에 넘어간다

 currentParams
      --> 그리는 자리의 parentParams. [동적 API] [04]의 팩토리까지 간다

 injected CSS · JS · 폰트 집합
      --> 그리는 자리의 createComponentTree 에 넘어가 중복 주입을 막는다
```

## 다루지 않는 것

`matchSegment` 의 비교 규칙(동적 세그먼트 튜플 비교 포함), `addSearchParamsIfPageSegment` 가 쿼리를 붙이는 형식, `getDynamicParamFromSegment` 의 파라미터 해석, 루트 레이아웃 판정(`rootLayoutIncluded`)이 쓰이는 곳, 클라이언트가 'refetch' · 'inside-shared-layout' 을 붙이는 판단 규칙은 이 문서의 범위 밖이다.
