# 02 한 번의 패스

상위: [프리페치 작업 하나가 태어나서 끝나기까지](../README.md)

`pingRoute` 한 번이 패스 하나다. **라우트 트리가 없으면 그것만 요청하고 멈춘다.** 트리가 있으면 전략을 하나 골라 트리를 걸으며 캐시 항목을 살피고, 빈 자리를 모아 요청을 **묶어서** 내보낸다. 요청을 보내는 자리는 다섯 곳이고 모두 `spawnPrefetchSubtask` 를 거친다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L729-L1054 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L729-L1054))

## 실제 코드

라우트 트리를 받은 뒤 **어떤 전략으로 걸을지** 가 여기서 정해진다. 작업이 들고 온 전략을 그대로 쓰지 않는다.

```ts
// scheduler.ts L865-L891
      // A task's fetch strategy gets set to `PPR` for any "auto" prefetch.
      // If it turned out that the route isn't PPR-enabled, we need to use `LoadingBoundary` instead.
      // We don't need to do this for runtime prefetches, because those are only available in
      // `cacheComponents`, where every route is PPR.
      let fetchStrategy: FetchStrategy
      if (tree.prefetchHints & PrefetchHint.SubtreeHasPartialPrefetching) {
        // If Partial Prefetching is enabled anywhere on the target route,
        // ignore the fetch strategy and switch to unified strategy used by
        // Cache Components (called `PPR` for now, will likely be renamed).
        //
        // In practice, this just means that a "full" prefetch (<Link
        // prefetch={true}>) has no effect. You're meant to use Runtime
        // Prefetching instead — that's the new pattern that replaces
        // prefetch={true}.
        //
        // The reason we check for the Partial Prefetching opt-in rather than
        // the `cacheComponents` flag is to support incremental adoption.
        // `prefetch={true}` will continue to work until you opt into
        // Partial Prefetching.
        fetchStrategy = FetchStrategy.PPR
      } else if (task.fetchStrategy === FetchStrategy.PPR) {
        fetchStrategy = route.supportsPerSegmentPrefetching
          ? FetchStrategy.PPR
          : FetchStrategy.LoadingBoundary
      } else {
        fetchStrategy = task.fetchStrategy
      }
```

```text
 갈래 셋
   ① 라우트 어딘가에 Partial Prefetching 이 있으면     => PPR  (작업이 Full 이어도 무시한다)
   ② 작업이 PPR 이면  route.supportsPerSegmentPrefetching ? PPR : LoadingBoundary
   ③ 그 밖(= 작업이 Full)                              => Full

 ★★ ① 의 주석 L875-878 - "In practice, this just means that a "full" prefetch (<Link
   prefetch={true}>) has no effect. You're meant to use Runtime Prefetching instead"
   그리고 L880-883 - cacheComponents 플래그가 아니라 opt-in 을 보는 이유는 점진 도입이다.
   "`prefetch={true}` will continue to work until you opt into Partial Prefetching."

 ★★★ ② 의 supportsPerSegmentPrefetching 이 기본 설정의 갈림길이다
   이 값은 /_tree 응답의 `x-nextjs-postponed: 2` 헤더(SCCACHE L2063-2068, output: export 면 늘 참),
   또는 초기 로드 · 내비게이션 RSC 의 `S` 필드(FSR L304 → discoverKnownRoute)에서 온다.
   예측된 합성 항목은 패턴에서 복사한다(optimistic-routes.ts L800). `S` = isStaticGeneration ||
   cacheComponents (app-render.tsx L2204) 이므로 두 출처 모두 기본 설정에서 "정적 생성된 페이지만 참" 이다
     routeIsPPREnabled = response.headers.get(NEXT_DID_POSTPONE_HEADER) === '2' || isOutputExportMode
     주석 L2060-2062 - "This checks whether the response was served from the per-segment cache,
       rather than the old prefetching flow. If it fails, it implies that PPR is disabled on this route."
   그 '2' 를 붙이는 곳은 app-page-runtime.ts L1778 — 캐시에 segmentData 가 있을 때만이다 (L1763-1767)
   서버 쪽 주석(app-render.tsx L2200-2203, RSC 페이로드의 `S` 필드)이 조건을 적는다
     "With Cache Components, all routes support it. Without it, only fully static pages do,
      because their per-segment prefetch responses are generated during static generation"
   => 기본 설정(cacheComponents 끔)에서 **정적 페이지는 PPR 걷기**, 동적 페이지는 **LoadingBoundary**
   ★ 이름은 "PPR" 이지만 PPR 을 켜지 않은 정적 페이지도 이 갈래를 탄다.
     비-cacheComponents prerender 갈래(app-render.tsx L9565 `} else {`)도 L9624-9634 에서
     collectSegmentData 를 부른다
```

## 동작 흐름

```text
 pingRoute(now, task)   L729-794

 L737  route = readOrCreateRouteCacheEntry(now, task, key)          → [캐시 항목]
         ★ 이 호출이 task 를 무효화 리스너로 등록한다 (SCCACHE L666) → [04]
         ★★ optimisticRouting(기본 true) 에서는 캐시 미스여도 **요청 없이 Fulfilled** 가 올 수 있다
           SCCACHE L536-538  readRouteCacheEntry 가 matchKnownRoute 로 알려진 패턴을 복제한다
           optimistic-routes.ts L786-811 - 합성 항목은 routeCacheMap 이 아니라 **패턴 자리**에 저장된다
           ※ 같은 모양의 라우트를 한 번 받아 두면(SCCACHE L2119 discoverKnownRoute), 다른 파라미터의
             링크는 /_tree 요청을 건너뛸 수 있다고 읽었다. 매칭 조건(optimistic-routes.ts L760 가로채기 제외 등)의 세부는 읽지 않았다
 L738  exitStatus = pingRootRouteTree(now, task, route)
 L740  exitStatus 가 InProgress 가 아니고 key.search 가 비어 있지 않으면
 L752-758  검색 문자열을 뗀 URL 로 라우트 항목을 하나 더 읽는다
 L761      Empty 이고 background(task) 이면 fetchRouteOnCacheMiss 를 하나 더 보낸다   → [03]
           주석 L741-743 - "We use the searchless route tree as a base for optimistic routing;
             see requestOptimisticRouteCacheEntry for details."
           ※ 그 소비자 deprecated_requestOptimisticRouteCacheEntry 는 SCNAV L182 에서
             `!__NEXT_OPTIMISTIC_ROUTING` 일 때만 불린다. optimisticRouting 기본값이 true 이므로
             기본 설정에서는 이 요청의 **명시된 쓰임이 꺼져 있다**.
           ★ 그래도 요청은 나간다 — L754 가 만든 Empty 항목이 맵에 남아 readRouteCacheEntry 가 그것을
             먼저 돌려주므로(SCCACHE L528-532) matchKnownRoute 예측이 가려지고, 결과는 검색 없는 URL 의
             일반 라우트 항목으로 쓰인다
 L786  exitStatus 가 Done 인데 task.hasPendingResponses 이면
 L790    => return Blocked       "the current phase isn't actually complete"
 L793  => return exitStatus
```

```text
 pingRootRouteTree(now, task, route)   L796-1054 — route.status 로 가른다

 Empty      L805
   L820      spawnPrefetchSubtask(fetchRouteOnCacheMiss(route, task.key, task.segmentCacheMap))
   L830      route.staleAt = now + 60 * 1000
             주석 L824-827 - 1분 넘게 걸리면 다음 요청이 기다리지 말고 다시 시도하라는 뜻
   L833      route.status = Pending
             주석 L835 "Intentional fallthrough to the Pending branch"
 Pending    L837
   L841-846  route.blockedTasks 에 task 를 넣는다
   L847      => return Blocked
 Rejected   L849  => return Done        주석 "Route tree failed to load. Treat as a 404."
 Fulfilled  L853
   L854      phase 가 RouteTree 면 => return Done   "Do not prefetch segment data during the route tree phase."
   L859      대역폭이 없으면 => return InProgress
   L865-891  전략 고르기 (위 실제 코드)
   L893      switch (fetchStrategy)
     PPR                               L894-999   아래 ①
     Full · PPRRuntime · LoadingBoundary L1000-1043 아래 ②

 ★★ "라우트 트리 먼저" 는 두 겹이다
   phase 가 RouteTree 면 트리가 있어도 L854 에서 멈춘다 — 트리 요청들이 큐에서 **먼저** 다 돌게 한다
   (phase 가 큐 비교의 둘째 기준이라서다 → [03])
   트리가 아직 Pending 이면 phase 와 무관하게 L847 에서 Blocked
```

```text
 ① PPR 갈래 — 세그먼트마다 정적 요청   L894-999

 L909-912  staticWalkStrategy = phase 가 Shell 이면 StaticShell, 아니면 PPR
           주석 L907-908 - "This is the only place the phase is consulted"
 L914-925  PPR 걷기이고 subtreeHasSpeculativePrefetch(...) 가 거짓이면 => Done
 L927      pingStaticHead — 메타데이터(head)도 세그먼트처럼 캐시 항목 하나로 다룬다 (L1070-1137)
 L929      pingSharedPartOfCacheComponentsTree(..., task.treeAtTimeOfPrefetch, tree, null, staticWalkStrategy)

   pingSharedPart…  L1263-1378   지금 화면과 **겹치는** 부분
     L1291-1299  accumulateSegmentBundle(..., FetchStrategy.PPR, true) — 겹치는 부분은 **언제나 PPR**
     L1305-1374  자식마다 — 대역폭 확인(L1306) 후
                 doesCurrentSegmentMatchCachedSegment 이면 계속 shared, 아니면 pingNewPart… 로 갈아탄다
   pingNewPart…     L1380-1528   지금 화면에 **없는** 부분
     L1416-1426  PPR 걷기이고 speculative 할 것이 없으면 => Done
     L1447-1466  runtime 완전성이 필요한데 정적 시도 힌트가 없으면
                   addSpawnedRuntimePrefetch 하고 => Done (정적 시도 없이 곧장 runtime 으로)
     L1470-1478  accumulateSegmentBundle(..., fetchStrategy, true)
     L1481-1491  정적 시도가 부족했다는 신호면 addSpawnedRuntimePrefetch 하고 => Done
     L1493-1521  자식마다 재귀 (대역폭 확인 L1494)

   accumulateSegmentBundle  L2316-2416
     L2338  prefetch 가 강제로 꺼진 세그먼트는 tree/entry 가 null 인 자리만 차지한다
     L2352  __NEXT_PREFETCH_INLINING 이고 InlinedIntoChild 면 **요청하지 않고** 묶음에 얹어 자식에게 넘긴다
     L2405  그 밖이면 pingSegmentBundle 로 묶음을 닫는다
   pingSegmentBundle  L2077-2306 — 묶음의 노드마다 status 로 가른다
     Empty      upgradeToPendingSegment + needsFetch + blockTaskOnPendingResponse
     Pending    (PPR 걷기이고 더 줄 수 있으면) 재검증 항목을 하나 더 만들고, 어쨌든 기다린다
     Rejected   (같은 조건이면) 재시도 재검증, 아니면 건너뛴다 — **Rejected 에는 등록하지 않는다**
     Fulfilled  isPartial 이고 더 줄 수 있거나, ISR fallback 을 올릴 수 있으면 재검증
     L2292-2304  needsFetch 면 spawnPrefetchSubtask(fetchSegmentsOnCacheMiss(...))
                 ★ 묶음 하나 = 요청 **하나**다

 L954  walkRequiresRuntimeCompleteness(staticWalkStrategy, route) 이면     runtime 관문
 L955-958  runtimeStrategy = Shell 이면 RuntimeShell, 아니면 PPRRuntime
 L968-995  spawnedRuntimePrefetches 가 있으면 pingRuntimeHead + pingRuntimePrefetches 로
           요청 트리를 만들고, 모인 항목이 있으면 fetchSegmentPrefetchesUsingDynamicRequest 한 번
 L998  => Done
```

```text
 ② 동적 요청 하나로 — Full · LoadingBoundary   L1000-1043

 L1003-1008  Shell phase 면 => Done   (이 전략들은 Shell 에서 할 일이 없다 — 방어 코드다. Shell phase 는
             SubtreeHasPartialPrefetching 이 있어야 들어가고, 그 비트면 L870-884 가 전략을 PPR 로 강제한다)
 L1020       pingRuntimeHead — head 는 LoadingBoundary 여도 **Full 로** 본다 (L1253-1257)
 L1021-1029  dynamicRequestTree = diffRouteTreeAgainstCurrent(...)
 L1030-1041  spawnedEntries 가 하나라도 있으면 fetchSegmentPrefetchesUsingDynamicRequest 한 번
 L1042       => Done

 diffRouteTreeAgainstCurrent  L1530-1678
   주석 L1542-1550 - 한 번의 재귀가 셋을 한다: 지금 화면과 diff, 요청 트리(FlightRouterState) 조립,
     요청할 세그먼트의 Pending 항목 만들기 ("so that a subsequent prefetch task does not
     request the same segments again")
   겹치는 부분은 그대로 내려가고, 갈라지는 자리에서 전략별로
     LoadingBoundary  L1585-1616  서브트리에 loading 이 **없으면** 요청 트리만 복제하고 끝
                                  주석 L1595-1597 - "If there's no loading boundary anywhere in the tree,
                                    the server will never return any data, so we can skip the request."
                      있으면 pingPPRDisabledRouteTreeUpToLoadingBoundary (L1680-1799)
     PPRRuntime       L1617-1631  ★ 작업 경로로는 도달하지 않는다 ([README] — PPRRuntime 을 싣는 호출처 없음)
     Full             L1632-1661  pingRouteTreeAndIncludeDynamicData (L1834-2007)

 요청 트리의 표시 (FlightRouterState 넷째 칸)
   'inside-shared-layout'  L1699-1700   LoadingBoundary 걷기의 맨 위 — 서버가 loading 을 어디서부터 찾을지
   'refetch'               L1731 · L1994-1995   이 자리부터 그려라. 부모에 이미 있으면 다시 붙이지 않는다
   => [중간부터 그리기]의 서버가 이 표시를 보고 그 자리부터 렌더한다

 ★★ LoadingBoundary 와 Full 은 캐시된 부분 항목을 **반대로** 다룬다 (주석 L1688-1695)
   "a LoadingBoundary prefetch ... will omit from the request tree any segment that is already
    cached, regardles of whether it's partial or full. By contrast, a Full prefetch will refetch
    partial segments."
   코드도 그렇다 — L1738-1755(LoadingBoundary 의 Fulfilled 는 건너뜀) 대 L1887-1922
   (Full 은 isPartial 이고 더 줄 수 있으면 재검증 항목을 만든다)
 ★ Full 은 요청 전에 bfcache 를 먼저 본다 (L1871-1882 · L1906-1915)
```

```text
 ★★★ 기본 설정(cacheComponents 끔, production)에서 닿는 갈래 (규칙 16)

 갈래                                   조건                                   기본 설정
 /_tree 요청 (L820)                     라우트 항목 Empty                      닿음 (단 위 optimistic 합성이면 건너뜀)
 ① PPR 걷기                             supportsPerSegmentPrefetching          정적 페이지에서 닿음
 ② LoadingBoundary                      작업 PPR + 위 값 거짓                  동적 페이지에서 닿음
 ② Full                                 <Link prefetch={true}> · kind FULL     닿음
 Shell phase · StaticShell 걷기          SubtreeHasPartialPrefetching           안 닿음 → [01]
 runtime 관문 (L954)                    StaticShell 이거나 위 비트             안 닿음
 L914 · L1416 speculative 생략          SubtreeHasEagerPrefetch 가 없음         안 닿음 — prefetchConfig 가
                                                                                'partial' 이 아니면 모든 세그먼트에
                                                                                eager 비트 (CFRS L126-128)
 L1001 · L1617 의 PPRRuntime            task.fetchStrategy === PPRRuntime      **어떤 설정에서도** 작업 경로로 안 닿음
 __NEXT_PREFETCH_INLINING 묶음           experimental.prefetchInlining          플래그 기본값 true (config-shared.ts L2177)
                                                                                ※ 실제 묶음은 서버가 준 Inlined* 힌트에
                                                                                  달려 있고, 그 힌트 계산은 추적하지 않았다
```

## 결과가 쓰이는 곳

```text
 Pending 캐시 항목 (upgradeToPendingSegment · 라우트 항목 status = Pending)
      --> 같은 URL 의 **다른 작업**이 같은 세그먼트를 다시 요청하지 않는다 (diff 주석 L1548-1550)
      --> 응답이 오면 [캐시 항목]이 Fulfilled/Rejected 로 바꾸고 기다리던 작업을 깨운다 → [04]

 요청 트리 (diffRouteTreeAgainstCurrent · pingRuntimePrefetches 의 반환값)
      --> fetchSegmentPrefetchesUsingDynamicRequest 가 서버에 보낸다
      --> [중간부터 그리기]가 'refetch' 자리부터 그린다

 spawnPrefetchSubtask 호출 다섯 곳 (grep 전수)
      L763  fetchRouteOnCacheMiss (검색 없는 트리, background)
      L820  fetchRouteOnCacheMiss
      L985  fetchSegmentPrefetchesUsingDynamicRequest (runtime 관문)
      L1032 fetchSegmentPrefetchesUsingDynamicRequest (Full · LoadingBoundary)
      L2293 fetchSegmentsOnCacheMiss (정적 묶음)
      --> [03]의 inProgressRequests 를 하나씩 올린다

 task.spawnedRuntimePrefetches · hasPendingResponses · hasBackgroundWork
      --> 패스가 끝나면 [01]의 큐 루프가 읽고 지운다
```

## 다루지 않는 것

`pingStaticHead`(L1070-1137)의 head 인라인 조건, `finishStaticBundleOnRuntimeBailout`(L2418-2459)의 묶음 마무리, `pingRuntimePrefetches`(L2009-2063)의 트리 복제, `pingFullSegmentRevalidation`(L2461-2532)의 재검증 항목 교체 규칙, `doesCurrentSegmentMatchCachedSegment`(L2534-2562)의 페이지 세그먼트 검색 파라미터 비교는 줄 번호만 따라갔고 세부는 이 문서의 범위 밖이다. `readOrCreateSegmentCacheEntry` · `readOrCreateRevalidatingSegmentEntry` · `upgradeToPendingSegment` · `attemptToFulfillDynamicSegmentFromBFCache` 와 세 요청 함수의 응답 쓰기(`writeDynamicTreeResponseIntoCache` 등)는 [캐시 항목](../../cache-entries/README.md), 서버가 세그먼트 응답을 미리 자르는 쪽은 [트리 조립](../../tree-assembly/04_slice/README.md), 'refetch' 표시를 읽는 쪽은 [중간부터 그리기](../../partial-tree/README.md), `optimistic-routes.ts` 의 `matchKnownRoute` 매칭 알고리즘과 `hasDynamicRewrite` 는 이 문서의 범위 밖이다.
