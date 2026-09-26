# 01 트리를 비교해 새로 짓기

상위: [내비게이션이 서버 응답을 트리에 합치기까지](../README.md)

`updateCacheNodeOnNavigation` 은 이전 라우트의 `FlightRouterState` 와 새 `RouteTree` 를 **위에서부터 같이 내려가며** 비교한다. 같은 세그먼트면 이전 CacheNode 를 복사해 쓰고, 처음 갈라지는 곳에서 `createCacheNodeOnNavigation` 으로 넘어가 그 아래를 전부 새로 만든다. 이 과정에서 "서버에 무엇을 다시 달라고 할지" 를 적은 요청 트리가 함께 만들어진다.

## 위치

`packages/next` / `src/client/components/router-reducer` / `ppr-navigations.ts` L270-L624 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/ppr-navigations.ts#L270-L624))

## 실제 코드

요청 트리를 만드는 규칙이 이 함수 하나에 있다.

```ts
// ppr-navigations.ts L848-L882
function createDynamicRequestTree(
  newRouterState: FlightRouterState,
  dynamicRequestTreeChildren: Record<string, FlightRouterState>,
  needsDynamicRequest: boolean,
  childNeedsDynamicRequest: boolean,
  parentNeedsDynamicRequest: boolean
): FlightRouterState | null {
  // Create a FlightRouterState that instructs the server how to render the
  // requested segment.
  //
  // Or, if neither this segment nor any of the children require a new data,
  // then we return `null` to skip the request.
  let dynamicRequestTree: FlightRouterState | null = null
  if (needsDynamicRequest) {
    dynamicRequestTree = patchRouterStateWithNewChildren(
      newRouterState,
      dynamicRequestTreeChildren
    )
    // The "refetch" marker is set on the top-most segment that requires new
    // data. We can omit it if a parent was already marked.
    if (!parentNeedsDynamicRequest) {
      dynamicRequestTree[3] = 'refetch'
    }
  } else if (childNeedsDynamicRequest) {
    // This segment does not request new data, but at least one of its
    // children does.
    dynamicRequestTree = patchRouterStateWithNewChildren(
      newRouterState,
      dynamicRequestTreeChildren
    )
  } else {
    dynamicRequestTree = null
  }
  return dynamicRequestTree
}
```

```text
 ★★★ `refetch` 표시는 **가지마다 맨 위**에만 붙는다

   needsDynamicRequest (이 세그먼트가 데이터를 받아야 한다)
     => 자식을 붙인 트리를 만들고, 부모가 이미 표시되지 않았으면 [3] = 'refetch'
   childNeedsDynamicRequest (아래 어딘가가 받아야 한다)
     => 자식을 붙인 트리만. 표시는 없다 — 서버에게 "여기까지는 길일 뿐" 이다
   둘 다 아니면
     => null. 그러나 부모는 이 자식을 빼지 않고 **표시 없는 route 로** 싣는다 (L587-593 · L763-768)
        서버는 일치하는 것을 보고 렌더를 건너뛴다. 정말 빠지면 오히려 walk-tree L108-109 의
        `!flightRouterState` 에 걸려 다시 그리게 된다

 => 서버(walk-tree-with-flight-router-state.tsx L107-113)는
    세그먼트가 어긋나거나 `flightRouterState[3] === 'refetch'` 인 곳에서 렌더를 시작한다
 => 그래서 표시 하나가 "그 아래 전부" 를 뜻한다. 아래에 또 붙일 필요가 없다 (주석 L866-867)
 ★ 억제는 **자손**에게만 간다 — 자식에게 넘기는 값이 `parentNeedsDynamicRequest || needsDynamicRequest`
   (L560)다. 재사용된 레이아웃 아래 형제 슬롯(`children` · `@modal`)이 각각 데이터를 원하면
   표시가 **슬롯마다 하나씩** 붙는다
 ★ 루트까지 전부 null 이면 task.dynamicRequestTree = null — [04]가 **요청을 아예 안 보낸다**
   (PPRNAV L1452-1457 "This navigation was fully cached.")
 ★ 요청으로 보낼 때는 클라이언트 전용 칸이 빠진다 — flight-data-helpers.ts L249-282 가
   [2] refreshState(URL) 를 버리고 [3] 표시와 [4] prefetchHints 만 남긴다
```

## 동작 흐름

```text
 updateCacheNodeOnNavigation  PPRNAV L270-624 (355줄)

 L295  oldSegment = oldRouterState[0]
 L296  newSegment = createSegmentFromRouteTree(newRouteTree)    (L799-826)
 L297  segmentMatchKind = compareSegments(newSegment, oldSegment)  (L1393-1409)

 L298  Change 면 — 여기서부터가 새 라우트다
 L324    루트 레이아웃이 바뀌었거나 (IsRootLayoutOrAbove 비트가 있을 때만 검사)
 L336    또는 newSegment === '/_not-found'(NOT_FOUND_SEGMENT_KEY, 전역 not-found)이면
 L338      => return null                       MPA 로 떨어진다
 L340    => return createCacheNodeOnNavigation(...)   아래 전부 새로

 --- 그 밖 (Match · SearchParamOnlyChange) ---
 L360  switch (freshness) → shouldRefreshDynamicData      RefreshAll · HMRRefresh 만 true
 L381  isLeafSegment = newSlots === null
 L389  이전 CacheNode 가 있고 && 새로고침이 아니고
         && !(잎 && 같은 페이지 내비게이션) && 검색 파라미터만 바뀐 것이 아니면
 L401    newCacheNode = reuseSharedCacheNode(false, oldCacheNode)   **복사해 재사용**
 L402    needsDynamicRequest = false
 L403  아니면
 L407    createCacheNodeForSegment(...)                               [02]
         bfcacheId 는 이전 노드 것을 **물려받는다** (L418-420)
 L428    잎이고 검색 파라미터만 바뀐 경우만 스크롤 표시를 새로 건다 (L434)
         그 밖은 이전 노드의 scrollRef 를 옮겨 온다 (L441-443)

 L452  refreshState = newRouteTree.refreshState ?? parentRefreshState
 L464  데이터를 받아야 하고 refreshState 가 있으면 => accumulateRefreshUrl  (별도 URL 요청 예약)

 L506  자식 슬롯마다
 L509    이전 트리에 그 슬롯이 없으면 => return null   (주석 "malformed server response")
 L521    새 쪽이 default 이고 이전 쪽은 아니며 HistoryTraversal 이 아니면
 L531      reuseActiveSegmentInDefaultSlot(...)   이전에 보이던 세그먼트를 그대로 쓴다
 L550    taskChild = updateCacheNodeOnNavigation(...)   재귀
 L570    null 이면 => return null   (아래에서 루트 레이아웃 변경을 만났다 — 즉시 풀린다)
 L579    newCacheNodeSlots[key] = taskChild.node
 L588    자식 요청 트리가 있으면 childNeedsDynamicRequest = true (L590)

 L598  newFlightRouterState = [segment, 자식들, refreshState 압축, null, prefetchHints]
 L608  => return { status: Pending | Fulfilled, route, node,
                  dynamicRequestTree: createDynamicRequestTree(...), refreshState, children }
```

```text
 ★★★ 세그먼트 비교가 **세 값**이다 (SegmentMatchKind L1379-1391)

   Match                   matchSegment 가 참 — 문자열이면 ===, 동적이면 [이름, 값] 둘 다 같음
                           (match-segments.ts L3-20)
   SearchParamOnlyChange   둘 다 `__PAGE__` 로 시작하는 문자열인데 다르다
   Change                  그 밖 전부

 주석 L1385-1389 - "Conceptually this is a refresh of the current page rather than a
   navigation to a new route — search params don't contribute to the LayoutRouter
   state key, and they shouldn't change the bfcacheId either. The CacheNode is
   rebuilt (so data refetches) but the bfcacheId carries forward."

 => `?page=2` 로만 바뀌면 CacheNode 는 **새로** 만들지만(데이터를 다시 받는다)
    bfcacheId 는 이어 간다. [클라이언트 트리] [03]이 본 "상태 키에서 검색 파라미터를 뺀다" 와
    짝이 맞는다 — React 상태도, bfcacheId 도 유지된다
 ★ 페이지 세그먼트 키에 검색 파라미터를 다시 붙이는 쪽이 createSegmentFromRouteTree 다 (L799-826).
   주석 L801-803 - 동적 응답은 서버가 키에 검색 파라미터를 넣고 정적 응답은 뺀다.
   클라이언트가 그 불일치를 "맨 끝에서 다시 붙이는" 것으로 맞춘다
```

```text
 ★★ 재사용 판정에서 **같은 페이지 내비게이션**은 잎만 다시 받는다 (L393)

 SCNAV L353  isSamePageNavigation = url.href === currentUrl.href
 L393        !(isLeafSegment && isSamePageNavigation)
 => 같은 링크를 다시 누르면 레이아웃은 재사용하고 **페이지 세그먼트만** 새로 채운다
    SCNAV 주석 L335-352 - "It's a common UI pattern for apps to refresh when you click a
      link to the current page." 그리고 "this only refreshes the dynamic data, not
      static/ cached data. If the page segment is fully static and prefetched, the
      request is skipped."
 ★ 해시나 검색 파라미터가 조금이라도 다르면 이 갈래가 아니다 (href 전체 비교)
```

```text
 ★★ default 슬롯은 서버가 **보내지 않는다** — 클라이언트가 이전 것을 채운다 (L521-543)

 주석 L528-530 - "These are never sent by the server during a soft navigation;
   instead, the client reuses whatever segment was already active in that slot
   on the previous route."

 reuseActiveSegmentInDefaultSlot (L907-948)
   이전 노드에 refreshState 가 있으면  그 URL 을 그대로 (더 오래된 라우트에서 온 것)
   없으면                                이전 라우트의 루트 URL (oldRootRefreshState)
   => 새 RouteTree 에 refreshState = { canonicalUrl, renderedSearch } 를 박는다

 => 이 슬롯을 나중에 새로고침하려면 **지금 URL 이 아니라 예전 URL** 로 물어야 한다.
    그래서 L464 가 그 URL 을 accumulation.separateRefreshUrls 에 모은다 → [04]
 ★ seedData · seedHead 를 null 로 끊는다 (L541-542) — 바깥 트리의 데이터라서다
 ★ HistoryTraversal 은 이 갈래를 **건너뛴다** (L522-524) — 기록에 저장된 트리를 그대로 복원한다
```

```text
 ★ createCacheNodeOnNavigation (L670-797)은 위의 **부분집합**이다

 주석 L690-693 - "For the most part, this is a subset of updateCacheNodeOnNavigation,
   so any change that happens in this function likely needs to be applied to that
   one, too. However there are some places where the behavior intentionally
   diverges, which is why we keep them separate."

 차이 셋
   비교가 없다        이전 트리가 없으니 언제나 createCacheNodeForSegment (L701)
   bfcacheId          언제나 새로 발급 generateBFCacheId(freshness) (L711)
   refreshState       언제나 null (L794 "This route is not part of the current tree")
 그리고 잎이면 언제나 accumulateScrollRef (L719-721)
 ★ 하이드레이션도 이 함수로 시작한다 — createInitialCacheNodeForHydration(L162-191)이
   이전 트리 없이 곧장 부른다 (L176). 그래서 첫 화면 전체가 "새 라우트" 로 지어진다
```

## 결과가 쓰이는 곳

```text
 NavigationTask (루트)
      --> startPPRNavigation 의 반환. SCNAV L354 가 받는다
      --> null 이면 SCNAV L401 completeHardNavigation — 루트 레이아웃 변경 · 전역 not-found ·
          이전 트리에 없는 슬롯, 이 셋이 MPA 로 가는 길이다

 task.dynamicRequestTree
      --> [04] spawnDynamicRequests 가 null 이면 즉시 return, 아니면 [03]으로 보낸다

 accumulation.separateRefreshUrls
      --> [04] 가 URL 마다 요청을 하나씩 더 만든다

 accumulation.scrollRef
      --> completeSoftNavigation(SCNAV L386)의 인자. 새 잎들이 **하나의** ScrollRef 를 공유하고
          처음 스크롤한 것이 소비한다 (주석 L627-631)

 newCacheNode.slots
      --> [클라이언트 트리] [03]의 `slots[parallelRouterKey]` 조회가 여기서 만들어진 것을 읽는다
```

## 다루지 않는 것

`isNavigatingToNewRootLayout`(`is-navigating-to-new-root-layout.ts`, 70줄)의 루트 레이아웃 비교 규칙, `convertReusedFlightRouterStateToRouteTree`(segment-cache/cache.ts)가 재사용 트리를 RouteTree 로 바꾸는 과정, `patchRouterStateWithNewChildren`(L828-846)이 칸을 복사하는 세부, `accumulateScrollRef`(L643-668)의 freshness 갈래([02]의 표에 한 줄로만 적었다)와 스크롤 핸들러, `getRenderedSearchFromVaryPath` · `urlSearchParamsToParsedUrlQuery` 의 직렬화, 서버가 `refetch` 표시와 어긋남을 보고 렌더 시작점을 고르는 쪽([중간부터 그리기](../../partial-tree/README.md))은 이 문서의 범위 밖이다.
