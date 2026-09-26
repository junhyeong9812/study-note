# 04 응답을 쓰고, 어긋나면 다시 하기

상위: [내비게이션이 서버 응답을 트리에 합치기까지](../README.md)

`spawnDynamicRequests` 는 [01]이 남긴 요청 트리로 요청을 **띄우기만** 하고 돌아간다. 응답이 오면 `NavigationTask` 트리를 따라 내려가며 [02]가 만든 `DeferredRsc` 를 서버 데이터로 푼다. 다 쓰고 나서도 풀리지 않은 약속이 남아 있으면, 서버가 클라이언트의 예상과 **다른 트리**를 보냈다는 뜻이다 — 그때 재시도를 액션 큐에 다시 넣는다.

## 위치

`packages/next` / `src/client/components/router-reducer` / `ppr-navigations.ts` L1431-L2238 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/ppr-navigations.ts#L1431-L2238))

## 실제 코드

응답을 CacheNode 에 쓰는 규칙이다. **덮어쓰기가 금지**돼 있다.

```ts
// ppr-navigations.ts L2106-L2142
  const rsc = cacheNode.rsc
  const dynamicSegmentData = dynamicData[0]

  if (dynamicSegmentData === null) {
    // This is an empty CacheNode; this particular server request did not
    // render this segment. There may be a separate pending request that will,
    // though, so we won't abort the task until all pending requests finish.
    return
  }

  if (rsc === null) {
    // This is a lazy cache node. We can overwrite it. This is only safe
    // because we know that the LayoutRouter suspends if `rsc` is `null`.
    cacheNode.rsc = dynamicSegmentData
  } else if (isDeferredRsc(rsc)) {
    // This is a deferred RSC promise. We can fulfill it with the data we just
    // received from the server. If it was already resolved by a different
    // navigation, then this does nothing because we can't overwrite data.
    //
    // In the streaming dev render, defer the fill until `revealAfter` settles,
    // so React doesn't render the boundary's children before their row has been
    // decoded (otherwise it suspends on the still-pending children and commits
    // a premature fallback). Outside that render `revealAfter` is null and we
    // resolve immediately.
    if (revealAfter !== null) {
      const resolveRsc = () => rsc.resolve(dynamicSegmentData, debugInfo)
      // Use the same callback for both outcomes: we don't expect `revealAfter`
      // to reject, but if it ever did (e.g. a connection drop mid-stream) we'd
      // still want to resolve the RSC.
      revealAfter.then(resolveRsc, resolveRsc)
    } else {
      rsc.resolve(dynamicSegmentData, debugInfo)
    }
  } else {
    // This is not a deferred RSC promise, nor is it empty, so it must have
    // been populated by a different navigation. We must not overwrite it.
  }
```

```text
 ★★★ 쓰는 규칙이 "Suspense 캐시 안전성" 이다 (주석 L2093-2098)

   "it can resolve pending promises, but it cannot overwrite existing data.
    It can add segments to the tree (because a missing segment will cause the
    layout router to suspend). but it cannot delete them."

   서버가 이 세그먼트를 안 그렸다 (dynamicData[0] === null)
     => return. 다른 요청(separateRefreshUrls)이 그릴 수 있으니 **아직 포기하지 않는다**
   rsc === null       빈 노드 — 덮어쓴다. LayoutRouter 가 null 이면 suspend 하므로 안전하다
   DeferredRsc        resolve 한다. 이미 다른 내비게이션이 풀었으면 **아무 일도 없다** ([02]의 pending 검사)
   그 밖              다른 내비게이션이 채운 값이다. 건드리지 않는다

 => 새 트리를 만들지 않고 **이미 반환된 트리를 제자리에서** 채운다.
    React 가 그 트리를 이미 그리고 있을 수 있으므로, 보이는 값을 바꿔치기하면 안 된다
 ★ 개발의 스트리밍 렌더에서는 `revealAfter` 가 풀릴 때까지 resolve 를 **미룬다** (L2125-2135) —
   행이 디코드되기 전에 React 가 자식을 그려 Suspense 폴백을 먼저 커밋하는 것을 막는다.
   `revealAfter` 가 거부돼도 같은 콜백으로 resolve 한다 (주석 L2132-2134)
 ★ head 는 따로 푼다 (L2147-2150). 페이지 세그먼트만 head 가 DeferredRsc 다
```

## 동작 흐름

```text
 spawnDynamicRequests(task, primaryUrl, nextUrl, freshness, accumulation,
                      routeCacheEntry, navigateType, lock, map, signal): void    PPRNAV L1431-1552

 L1453  task.dynamicRequestTree === null 이면
 L1455    previousNavigationDidMismatch = false
 L1456    => return                          전부 캐시에 있었다 — 요청 없음
 L1468  primaryRequestPromise = fetchMissingDynamicData(task, tree, primaryUrl, ...)   await 안 함
 L1484  separateRefreshUrls 가 있으면   ([01]의 default 슬롯)
 L1501    URL 마다 (지금 URL 과 같은 것은 건너뛴다 L1502)
 L1515      scopedDynamicRequestTree = dynamicRequestTree       ← **전체 트리를 그대로**
 L1518      fetchMissingDynamicData(task, ..., new URL(refreshUrl), nextUrl, ...)
 L1541  voidPromise = finishNavigationTask(...)
 L1551  voidPromise.then(noop, noop)       ~~> 여기서부터 이 함수와 끊긴다

 주석 L1459-1462 - "This is intentionally not an async function to discourage the caller
   from awaiting the result. Any subsequent async operations spawned by this function
   should result in a separate navigation task, rather than block the original one."
 ★ 요청을 **먼저 전부 띄우고** 그다음에 기다린다 — 워터폴을 막기 위해서다 (주석 L1464-1467)
 ★ 추가 URL 요청도 전체 요청 트리를 보낸다. `splitTaskByURL` 은 주석 속에만 있다 (L1514).
   주석 L1509-1513 "the server may sometimes render more data than necessary; this is not a
   regression compared to the pre-Segment Cache implementation"
 ★ L1516 `if (scopedDynamicRequestTree !== null)` 은 언제나 참이다 — L1453 에서 null 을 걸렀다
```

```text
 fetchMissingDynamicData  PPRNAV L1802-1989 (188줄)

 L1818  result = await fetchServerResponse(url, {                         [03]
          flightRouterState: dynamicRequestTree, nextUrl,
          isHmrRefresh: freshnessPolicy === HMRRefresh, signal })
 L1824  문자열이면 => return { HardRetry, url: 그 URL, seed: null }
 L1837  seed = convertServerPatchToFullTree(now, **task.route**, result.flightData, ...)
          서버가 보낸 패치(segmentPath 로 트리 중간을 가리킨다)를 **낙관적으로 지은 트리**에 붙인다
          → 서버가 "중간부터" 그린 응답을 받는 자리다 ([중간부터 그리기])
 L1848  테스트 API 의 잠금이 있으면 풀릴 때까지 await
 L1855  routeCacheEntry && staticStageData      → writePrerenderResponseIntoCache (PPR 전략)   ~~> then
 L1885  routeCacheEntry && runtimePrefetchStream → processRuntimePrefetchStream → writeDynamicRender…  ~~> then
        둘 다 실패는 삼킨다 ("Not fatal", L1880-1881 · L1910-1911)
 L1917  dynamicStaleAt = computeDynamicStaleAt(now, result.dynamicStaleTime)
 L1919  didReceiveUnknownParallelRoute = writeDynamicDataIntoNavigationTask(task, seed.routeTree,
                                          seed.data, seed.head, dynamicStaleAt, debugInfo, revealAfter)
 L1947  routeCacheEntry 가 있으면 그 canonicalUrl 과 응답의 URL 을 pathname · search 로 비교
 L1957  => return { exitStatus: 모르는 슬롯 ? SoftRetry : URL 이 틀림 ? RedirectRetry : Done,
                   url: resolvedUrl, seed }
 L1968  catch — signal.aborted 면 Canceled, 아니면 HardRetry
```

```text
 ★★★ routeCacheEntry 가 null 이 아닌 경우가 **하나**다 — navigateUsingPrefetchedRouteTree 경로
   그 엔트리는 프리페치 결과만이 아니다 — 첫 로드·이전 내비게이션에서 학습한 라우트나
   패턴 예측(cache.ts L534-538 matchKnownRoute, 기본 켜짐)일 수도 있다 (optimistic-routes.ts L203-208)
   => 프리페치한 적 없는 링크도 두 번째 방문부터는 이 경로를 탄다

 navigateToKnownRoute 의 routeCacheEntry 인자 (호출처 다섯 전수)
   SCNAV L433-453  navigateUsingPrefetchedRouteTree   `route` (L450)
   SCNAV L653      navigateToUnknownRoute             null
   refresh-reducer L91 · server-patch-reducer L54 · server-action-reducer L504   null
   restore-reducer L86 은 spawnDynamicRequests 에 **직접** null
 => 캐시 쓰기 둘(L1855 · L1885)과 RedirectRetry 판정(L1947)이 **라우트 캐시 적중 내비게이션에서만** 돈다
 => 거기에 [03]의 조건이 겹친다
      staticStageData       cacheComponents + experimental.cachedNavigations 일 때만 null 이 아니다
                            (CC 를 켜면 cachedNavigations 는 기본으로 따라 켜진다 — [03])
      runtimePrefetchStream 서버가 응답에 `p` 를 실었을 때만 — app-render.tsx L1047-1050 ·
                            L3619-3622 가 `renderOpts.partialPrefetching` 이거나 어떤 세그먼트가
                            partial prefetching 을 켰을 때 싣는다. `partialPrefetching` 설정은
                            cacheComponents 를 요구한다 (server/config.ts L568-572)
 => **기본 설정에서는 두 캐시 쓰기 모두 일어나지 않는다**
 ※ 세그먼트 단위 `prefetch` export 가 cacheComponents 없이 허용되는지는 확인하지 않았다
```

```text
 ★★★ varyParams(튜플 다섯째 칸)는 **CacheNode 에 쓰이지 않는다**

 [트리 조립]이 만든 CacheNodeSeedData = [rsc, 자식, loading(null), isPartial, varyParams]
 PPRNAV 가 읽는 칸 (grep "seedData\[" — L357 · L406 · L698 · L700)
   seedData[0]   rsc   → [02]의 seedRsc
   seedData[1]   자식  → 재귀
   [2] · [3] · [4] 는 **한 번도 읽지 않는다**
 클라이언트에서 [4] 를 읽는 곳은 segment-cache/cache.ts L3661 **하나**다 (client/ 전체 grep)
   writeSeedDataIntoCache (cache.ts L3634-3698)
     varyParams = readVaryParams(seedData[4], rootVaryParamsIterable)
       (shared/lib/segment-cache/vary-params-decoding.ts L103)
     → fulfillEntrySpawnedByRuntimePrefetch 가 "이 세그먼트가 실제로 읽은 파라미터" 로
       세그먼트 캐시 항목을 **더 일반적인 varyPath 로 다시 걸지** 정한다 (주석 cache.ts L3719-3720)

 이 흐름에서 그곳에 닿는 길은 넷이다
   L1865 writePrerenderResponseIntoCache → cache.ts L4166 writeDynamicRenderResponseIntoCache
   L1894 writeDynamicRenderResponseIntoCache                        (라우트 캐시 적중)
   SCNAV L587 · L616 — 같은 두 함수                                   (캐시 미스, metadataVaryPath !== null)
     → cache.ts L3566 writeSeedDataIntoCache   (배포 ID 가 맞고 flightData 의 seedData 가 있고, segmentPath 를 따라 route tree 에서 자리를 찾았을 때 — L3526 · L3543 · 못 찾으면 L3553-3563 이 null 로 빠진다)
 => 내비게이션 응답의 varyParams 는 **지금 화면**에는 영향이 없고,
    **다음** 내비게이션이 세그먼트 캐시를 얼마나 넓게 재사용할지만 바꾼다
 ★ 서버 패치의 조상 칸은 클라이언트가 `[null, 자식, null, true, null]` 로 채운다
   (SCNAV L1188-1194). 다섯째 칸이 null — [트리 조립] 문서가 적은 "null = 추적 안 함" 이다
```

```text
 writeDynamicDataIntoNavigationTask  PPRNAV L1991-2084

 L2000  task 가 Pending 이고 dynamicData 가 있으면
 L2001    status = Fulfilled
 L2002    finishPendingCacheNode(task.node, ...)          (위 실제 코드)
 L2015    updateBFCacheEntryStaleAt(varyPath, dynamicStaleAt)   받은 세그먼트만 staleAt 을 고친다
 L2026  task 에 자식이 있으면
 L2027    서버 트리에 자식이 있으면 서버 슬롯마다
 L2035      task 에 없는 슬롯이면  didReceiveUnknownParallelRoute = true
 L2053      세그먼트가 같고 데이터가 있으면 재귀
            ★ 세그먼트가 **다르면 조용히 건너뛴다** — 그 task 는 Pending 으로 남는다
 L2075    (else 쪽) `serverChildren !== null` 검사 — 바깥 if 가 이미 null 인 경우라 **언제나 거짓**이다
 L2083  => return didReceiveUnknownParallelRoute

 주석 L2038-2048 - 슬롯 **집합**이 다른 것은 세그먼트가 다른 것과 다르다.
   "a given layout should never have a mismatching set of child slots."
   "Theoretically, this should only happen in development during an HMR refresh, ...
    But as an extra precaution, we validate in prod, too."
```

```text
 finishNavigationTask  PPRNAV L1554-1660

 L1565  exitStatus = await waitForRequestsToFinish(primary, refreshes)
          모두 Done 이면 Done,  **하나라도 Done 이 아니면 즉시** 그 값 (L1685-1693)
 L1576  Done 이면  exitStatus = abortRemainingPendingTasks(task, null, null)   (호출은 L1577)
          아직 Pending 인 task 마다 rsc 를 **null 로 resolve** 하고 (abortPendingCacheNode L2214-2238)
            refreshState === null  이면 SoftRetry     (보이는 트리에서 어긋남)
            그 밖                   이면 HardRetry     (비활성 병렬 라우트에서 어긋남, L2181-2187)
 L1580  switch (exitStatus)
          Canceled       => return                         새 HMR 이 넘겨받았다
          Done           => previousNavigationDidMismatch = false; return
          SoftRetry      => dispatchRetryDueToTreeMismatch(false, ..., RefreshAll)
          RedirectRetry  => dispatchRetryDueToTreeMismatch(false, ..., **HistoryTraversal**)
          HardRetry      => dispatchRetryDueToTreeMismatch(true,  ..., RefreshAll)
 ★ 정리는 **Done 일 때만** 돈다 — SoftRetry · HardRetry · RedirectRetry · Canceled 로 곧장 가면
   남은 Pending 약속은 null 로도 풀리지 않고 그대로 남는다 (Canceled 는 주석 L1582-1586 이 적는다)
 ★ 외부 호출이 L1577 하나이고 error 를 늘 null 로 넘기므로, abortPendingCacheNode 의
   `rsc.reject(error, …)` 갈래(L2224-2227)는 닿지 않는다 (재귀 L2198 도 같은 인자를 넘긴다)
```

```text
 ★★★ 재시도는 **액션 큐로 다시 들어간다** — dispatchRetryDueToTreeMismatch  L1711-1800

 L1733  routeCacheEntry 가 있으면 markRouteEntryAsDynamicRewrite
 L1735  없고 seed 가 있으면 discoverKnownRoute(..., hasDynamicRewrite = true) 로 패턴에 표시
 L1762  invalidateRouteCacheEntries(retryNextUrl, baseTree)   라우트 캐시 **전부** 무효 + 보이는 링크 재프리페치
 L1766  isHardRetry = isHardRetry || previousNavigationDidMismatch
 L1767  previousNavigationDidMismatch = true
 L1783  아직 커밋 안 됐으면 원래의 push/replace, 커밋됐으면 'replace'
 L1789  dispatchAppRouterAction({ type: ACTION_SERVER_PATCH, previousTree, url, nextUrl,
                                 seed, mpa: isHardRetry, navigateType, freshnessPolicy })

   --> router-reducer.ts L31 → serverPatchReducer (server-patch-reducer.ts L17-79)
         mpa 거나 seed 가 null 이면           => completeHardNavigation
         previousTree !== state.tree 이면     => refreshReducer   (그사이 다른 내비게이션이 있었다)
         그 밖                                => navigateToKnownRoute(..., seed, freshnessPolicy)
                                                 **받은 트리를 seed 로** 다시 짓는다 — [README]의 출발점

 ★★ 두 번 연속이면 MPA 다 (주석 L1411-1413, 모듈 전역 L1414)
   "If there are two successive mismatches, we will fall back to an MPA navigation,
    to prevent a retry loop."
   되돌리는 곳은 L1455(요청 없음) · L1591(Done) 둘이다
 ★★ RedirectRetry 는 데이터를 **다시 받지 않는다** — 재시도는 이미 채워진 CacheNode 재사용,
   BFCache(신선도 무시), seed 에 실린 서버 데이터(L1837) 순으로 데이터를 얻는다.
   HistoryTraversal 이 하는 일은 새로고침 갈래(L360)를 끄는 것이다. 주석 L1614-1618 "reuse the data we already
   received (HistoryTraversal) instead of re-fetching it. See issue #95195."
 ★ 재시도 액션도 이름은 "server patch" 지만, 서버 요청이 아니라 **클라이언트가 만든** 액션이다
```

```text
 ★★★ 주석 셋이 "null 이면 렌더 중에 **지연 fetch**" 라고 적지만, **코드에는 그런 fetch 가 없다** (규칙 13)

 주석 L1421-1423 - "A `null` value will trigger a lazy fetch during render, which will then
   patch up the tree using the same mechanism as the non-PPR implementation
   (serverPatchReducer)."
 주석 L2101-2102 - "... we will resolve its data promise to `null` to trigger a lazy fetch
   during render."
 주석 L2222      - "This will trigger a lazy fetch during render."

 받는 쪽 layout-router.tsx L547-555
   unwrappedRsc === null 이면 use(unresolvedThenable) — **영원히 suspend**
   주석 L551-554 "the router is responsible for triggering a new state update to un-suspend
     this segment."
   layout-router.tsx 에 fetchServerResponse · ACTION_SERVER_PATCH 가 **없다** (grep 0건)

 => 실제로 트리를 복구하는 것은 렌더가 아니라 **finishNavigationTask 의 재시도**다
    (abortRemainingPendingTasks → SoftRetry → ACTION_SERVER_PATCH)
 => serverPatchReducer 는 "non-PPR 구현" 이 아니라 **이 파일의 재시도 경로**다 (L1789)
 ※ 세 주석은 렌더 중 fetch 가 있던 예전 구현의 흔적으로 보인다. 그 구현은 확인하지 않았다
```

```text
 ★ 작은 것 둘

 NavigationTaskStatus.Rejected (L2161) 는 **쓰기만 하고 읽지 않는다** —
   status 를 비교하는 줄은 L2000 · L2159 둘이고 둘 다 `=== Pending` 이다 (grep "task.status")
 ExitStatus 를 `childExitStatus > exitStatus` 로 모은다 (L2205, 주석 "ordered by their precedence").
   숫자 순서는 Canceled -1 < Done 0 < SoftRetry 1 < HardRetry 2 < RedirectRetry 3 (L107-135) —
   이 함수가 내는 값은 Done · SoftRetry · HardRetry 셋뿐이라 RedirectRetry 가 HardRetry 를
   누르는 경우는 여기서 생기지 않는다
```

## 결과가 쓰이는 곳

```text
 풀린 DeferredRsc (rsc · head)
      --> [클라이언트 트리] [03]의 InnerLayoutRouter 가 use() 에서 깨어나 최종 rsc 를 그린다
      --> null 로 풀린 것은 영원히 suspend — 재시도 액션이 새 상태를 낼 때까지

 updateBFCacheEntryStaleAt
      --> 다음 Default 내비게이션이 [02] L1008 에서 이 staleAt 으로 BFCache 를 읽는다
          (unstable_dynamicStaleTime 의 `d` 가 여기서 실린다)

 ACTION_SERVER_PATCH
      --> [클라이언트 라우터]의 액션 큐 → serverPatchReducer → navigateToKnownRoute

 세그먼트 캐시 쓰기 (라우트 캐시 적중 + CC 켜짐일 때 — 미스 경로는 SCNAV 쪽이 쓴다)
      --> [프리페치]의 다음 readSegmentCacheEntryForNavigation 이 읽는다.
          varyParams 로 다시 걸린 키가 여기서 만들어진다

 markRouteEntryAsDynamicRewrite · invalidateRouteCacheEntries
      --> [프리페치]의 라우트 캐시. 다음 예측이 이 라우트를 믿지 않게 된다
```

## 다루지 않는 것

`writePrerenderResponseIntoCache`(cache.ts L4133) · `writeDynamicRenderResponseIntoCache`(L3503) · `processRuntimePrefetchStream`(L4187) · `fulfillEntrySpawnedByRuntimePrefetch`(L3700)의 본문과 varyPath 재키잉 규칙, `readVaryParams` 의 디코딩, `resolveStaleAt`, `markRouteEntryAsDynamicRewrite` · `invalidateRouteCacheEntries` · `discoverKnownRoute` 의 라우트 캐시 조작, `getLastCommittedTree`(`committed-state.ts`)와 push/replace 상속이 React 전환에 얽히는 방식(주석 L1774-1776), `revealAfter` 를 서버가 만드는 쪽, 서버가 `segmentPath` 패치를 만드는 쪽([중간부터 그리기](../../partial-tree/README.md)), Instant Navigation Testing API 의 `navigationLock`, `convertServerPatchToFullTree` 의 패치 적용 본문(SCNAV L907-992)과 `didServerPatchDivergeFromBase` 는 이 문서의 범위 밖이다.
