# 내비게이션이 서버 응답을 트리에 합치기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[프리페치] [03](../segment-cache/03_navigate/README.md)이 "본문은 범위 밖" 이라 하고 멈춘 자리 — `navigateUsingPrefetchedRouteTree` · `navigateToUnknownRoute` · `spawnDynamicRequests` — 가 **모두 이 두 파일로 이어진다.** 한쪽(`ppr-navigations.ts`)이 이전 CacheNode 트리와 새 라우트 트리를 비교해 **새 트리를 동기로 짓고**, 비어 있는 자리를 약속(Promise)으로 남긴다. 다른 쪽(`fetch-server-response.ts`)이 서버에 RSC 를 요청하고, 그 응답이 돌아오면 앞의 약속을 **제자리에서** 풀어 준다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `PPRNAV` = `client/components/router-reducer/ppr-navigations.ts`(2383줄), `FSR` = `client/components/router-reducer/fetch-server-response.ts`(875줄), `SCNAV` = `client/components/segment-cache/navigation.ts`(1278줄).

이어지는 흐름: [프리페치] [03 내비게이션](../segment-cache/03_navigate/README.md) · [클라이언트 라우터] [02 내비게이션](../client-router/02_navigate/README.md) · [클라이언트 트리] [03 `<LayoutRouter>`](../client-components/03_layout-router/README.md) · [트리 조립](../tree-assembly/README.md) · [중간부터 그리기](../partial-tree/README.md) (이 흐름이 받는 응답을 서버가 만드는 쪽).

## 위치

`packages/next` / `src/client/components/router-reducer` / `ppr-navigations.ts` L222-L268 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/ppr-navigations.ts#L222-L268))

## 실제 코드

이 파일은 트리를 **셋째** 종류로 하나 더 만든다. 주석이 스스로 "yet another" 라고 적는다.

```ts
// ppr-navigations.ts L64-L86
// This is yet another tree type that is used to track pending promises that
// need to be fulfilled once the dynamic data is received. The terminal nodes of
// this tree represent the new Cache Node trees that were created during this
// request. We can't use the Cache Node tree or Route State tree directly
// because those include reused nodes, too. This tree is discarded as soon as
// the navigation response is received.
export type NavigationTask = {
  status: NavigationTaskStatus
  // The router state that corresponds to the tree that this Task represents.
  route: FlightRouterState
  // The CacheNode that corresponds to the tree that this Task represents.
  node: CacheNode
  // The tree sent to the server during the dynamic request. If all the segments
  // are static, then this will be null, and no server request is required.
  // Otherwise, this is the same as `route`, except with the `refetch` marker
  // set on the top-most segment that needs to be fetched.
  dynamicRequestTree: FlightRouterState | null
  // The URL that should be used to fetch the dynamic data. This is only set
  // when the segment cannot be refetched from the current route, because it's
  // part of a "default" parallel slot that was reused during a navigation.
  refreshState: RefreshState | null
  children: Map<string, NavigationTask> | null
}
```

```text
 ★★★ 한 번의 내비게이션에 트리가 **셋** 나란히 선다

   FlightRouterState   route   라우트 모양 (서버와 주고받는 전송 형식)
   CacheNode           node    화면에 그릴 데이터 ([클라이언트 트리]의 LayoutRouter 가 읽는다)
   NavigationTask      이것    "아직 안 풀린 약속이 어디 있는가" 의 지도

 주석 L64-69 - "The terminal nodes of this tree represent the new Cache Node
   trees that were created during this request. We can't use the Cache Node
   tree or Route State tree directly because those include reused nodes, too.
   This tree is discarded as soon as the navigation response is received."

 => 앞의 두 트리에는 **재사용된 노드**가 섞여 있다. 그래서 "이번 요청이 새로 만든 곳" 만
    가리키는 트리가 따로 필요하다
 => 응답을 받으면 버린다. 수명이 요청 하나다
 ★★ `dynamicRequestTree` 가 null 이면 **서버 요청이 없다** (L76-79).
    그 밖이면 route 와 같되 "맨 위에서 다시 받아야 할 세그먼트" 에 `refetch` 표시가 붙는다 → [01]
 ★ `refreshState` 는 "default 병렬 슬롯이 **예전 URL** 에서 재사용됐을 때" 만 채워진다 (L81-84)
```

## 동작 흐름

```text
 들어오는 길 — 호출처 전수 (packages/next/src 전체 grep, 테스트 제외)

 startPPRNavigation                  SCNAV L354 (navigateToKnownRoute 안) · restore-reducer.ts L63
 spawnDynamicRequests                SCNAV L373 (navigateToKnownRoute 안) · restore-reducer.ts L86
 createInitialCacheNodeForHydration  create-initial-router-state.ts L93
 fetchServerResponse                 PPRNAV L1818 · SCNAV L513 (navigateToUnknownRoute) · FSR L343 (자기 재귀)

 navigateToKnownRoute(SCNAV L236-402)를 부르는 곳이 **다섯**이다
   SCNAV L433           navigateUsingPrefetchedRouteTree   라우트 캐시 적중
   SCNAV L653           navigateToUnknownRoute             응답을 먼저 받은 뒤
   refresh-reducer L91  refreshDynamicData                 router.refresh() · HMR
   server-patch-reducer L54                                 이 흐름의 재시도 [04]
   server-action-reducer L504                               액션의 redirect · 재검증
 => 내비게이션 · 새로고침 · 액션 · 재시도가 **전부 한 함수**로 모인다.
    뒤로/앞으로(restore-reducer)만 navigateToKnownRoute 를 거치지 않고 두 함수를 직접 부른다
```

```text
 navigateToKnownRoute   SCNAV L236-402

 L353  isSamePageNavigation = url.href === currentUrl.href
 L354  task = startPPRNavigation(...)                         [01] 트리를 **동기로** 짓는다
         +-- updateCacheNodeOnNavigation  PPRNAV L270-624      이전 트리와 비교
               +-- createCacheNodeOnNavigation  L670-797       갈라진 곳부터 아래는 새로
               +-- createCacheNodeForSegment    L969-1344      [02] 세그먼트 하나를 채운다
 L371  task !== null 이면
 L372    freshnessPolicy !== Gesture 이면
 L373      spawnDynamicRequests(task, url, ...)                [04] **기다리지 않는다**
             +-- fetchMissingDynamicData  PPRNAV L1802
                   +-- fetchServerResponse  FSR L149           [03] 서버에 RSC 요청
             ~~> finishNavigationTask  PPRNAV L1554            결과를 트리에 쓰고, 어긋나면 재시도
 L386    => return completeSoftNavigation(..., task.route, task.node, ...)
 L401  => return completeHardNavigation(state, url, navigateType)    task 가 null (MPA)

 ★★★ 순서가 "짓고 → 반환하고 → 나중에 채운다" 다
   startPPRNavigation 주석 L213-215 - "The tree can be rendered immediately after it is
     created (that's why this is a synchronous function). Any new trees that do not have
     prefetch data will suspend during rendering, until the dynamic data streams in."
 => 리듀서는 서버 응답을 기다리지 않고 새 상태를 돌려준다.
    응답은 이미 반환된 CacheNode 안의 약속을 **제자리에서** 푼다 (L1429-1430
    "This does _not_ create a new tree; it modifies the existing one in place.")
```

```text
 ★★★ 캐시 미스(navigateToUnknownRoute)는 순서가 **뒤집힌다**

 SCNAV L513  fetchServerResponse(url, ...) 를 **먼저 await** 한다
 SCNAV L540  convertServerPatchToFullTree(...)  응답으로 NavigationSeed 를 만든다
 SCNAV L653  navigateToKnownRoute(..., navigationSeed, ...)
               seed.data 에 서버 데이터가 이미 들어 있다 → [02] 의 "seedRsc 있음" 갈래

 => 라우트 캐시 적중  트리 먼저, 요청은 나중 (seed.data = null, SCNAV L427)
    라우트 캐시 미스  요청 먼저, 트리는 응답으로
 ★ 미스 경로가 서버에 보내는 트리는 task.dynamicRequestTree 가 아니다 (SCNAV L496-510) —
   Default · HistoryTraversal · Gesture 는 **현재 트리**를 표시 없이 보내 서버가 어긋나는 곳부터 그리고,
   RefreshAll · HMRRefresh 는 `['', {}, null, 'refetch']` 로 루트부터 받는다
 ※ 그래서 미스 경로에서는 spawnDynamicRequests 가 대개 L1453 의 검사에 걸려 L1456 에서 곧장 return 할 것이다 —
   새 세그먼트는 seedRsc 가 있어 요청이 필요 없고, 겹치는 세그먼트는 재사용되기 때문이다.
   [02]의 판정식에서 끌어낸 추론이고, 실행해 확인하지는 않았다
```

```text
 ★★★ 파일 이름에 "ppr" 이 있지만 **PPR 을 끈 앱도 이 파일을 탄다** (규칙 16 확인)

 ppr-navigations.ts 안에 PPR · cacheComponents 플래그를 읽는 줄이 **0개**다
   grep -n "__NEXT_PPR\|__NEXT_CACHE_COMPONENTS" ppr-navigations.ts  → 없음
 SCNAV L354 의 startPPRNavigation 호출도 플래그로 감싸여 있지 않다
 => 모든 App Router 내비게이션이 이 경로다. 기본 설정(cacheComponents: false,
    config-shared.ts L2114)도 마찬가지다
 ※ 이름은 PPR 과 함께 들어온 구현이라서 붙은 흔적으로 보인다. 소스가 그렇게 적지는 않는다

 플래그로 갈리는 곳은 FSR 에 **둘** 있다 → [03]
   FSR L195-197  isLegacyPPR = __NEXT_PPR && !__NEXT_CACHE_COMPONENTS
   FSR L403      processFetch 의 `if (process.env.__NEXT_CACHE_COMPONENTS)`

 v16.3.6 에서 두 플래그의 관계 (define-env.ts L125-126 · L180-181)
   __NEXT_PPR              = checkIsAppPPREnabled(config.experimental.ppr)
   __NEXT_CACHE_COMPONENTS = !!config.cacheComponents
   server/config.ts L574-578   사용자가 experimental.ppr 을 켜면 HardDeprecatedConfigError
   server/config.ts L1603-1606 cacheComponents 면 experimental.ppr = true 로 채운다
   (둘 다 assignDefaultsAndValidate L316-1657 안이고 L574 가 먼저다.
    experimental.ppr 에 값을 쓰는 곳은 packages/next/src 에서 L1605 **하나**다)
 => 가능한 조합은 (PPR 꺼짐, CC 꺼짐) · (PPR 켜짐, CC 켜짐) **둘뿐**이다
 ※ define-env 가 받는 config 가 이 검증을 거친 완성본이라는 것은 webpack-config.ts L2065 의
   getDefineEnv 호출까지만 따라갔다. 다른 호출처(build/swc/index.ts · setup-dev-bundler.ts)는 읽지 않았다
 => isLegacyPPR 은 v16.3.6 에서 **언제나 false** 다. 그 갈래(FSR L254-267)는 닿지 않는다
 => 기본 설정의 현행 경로는 "CC 꺼짐" 이다 — processFetch 가 cacheData 를 null 로 돌려주고,
    그래서 staticStageData 도 null 이다 ([04]의 캐시 쓰기 둘 중 하나가 꺼진다)
 ★ CC 를 켜면 cachedNavigations 도 **자동으로** 켜진다 (server/config.ts L2370-2384 — 명시적 false 가
   아니면). 그래서 CC 켜짐 설정에서는 그 캐시 쓰기가 기본으로 살아 있다
```

1. [트리를 비교해 새로 짓기](01_build-tree/README.md) — 같으면 복사, 갈라지면 새로, `refetch` 표시는 가지마다 맨 위에만.
2. [세그먼트 하나를 채우기](02_fill-segment/README.md) — `FreshnessPolicy` 여섯 값이 여기서 갈린다.
3. [서버에 RSC 요청하기](03_fetch/README.md) — 실패는 전부 **URL 문자열**로 돌아온다.
4. [응답을 쓰고, 어긋나면 다시 하기](04_write-back/README.md) — 약속을 푸는 규칙과 재시도 넷.

```text
 ★★ FreshnessPolicy 여섯 값을 **누가 넘기는가** (client/ 전체 grep)

   Default           navigate-reducer.ts L52 · server-action-reducer.ts L460 (재검증 없는 액션)
   Hydration         PPRNAV L180 createInitialCacheNodeForHydration **하나**
   HistoryTraversal  restore-reducer.ts L71 · L90 · PPRNAV L1629 (redirect 재시도)
   RefreshAll        refresh-reducer.ts L42 · server-action-reducer.ts L461 · PPRNAV L1610 · L1652
   HMRRefresh        hmr-refresh-reducer.ts L20
   Gesture           app-router-instance.ts L366 (experimental_gesturePush —
                     `__NEXT_GESTURE_TRANSITION` 일 때만, L336 · L516)

 => 여섯 값이 이 파일 안 **일곱 자리**에서 판단을 바꾼다. 표는 [02]에 있다
```

## 결과가 쓰이는 곳

```text
 task.node (CacheNode 트리)
      --> completeSoftNavigation 이 새 AppRouterState.cache 로 싣는다 (SCNAV L386)
      --> [클라이언트 트리]의 LayoutRouter 가 slots 를 따라 내려가며 rsc · prefetchRsc 를 그린다
      --> 아직 안 풀린 rsc 는 DeferredRsc — LayoutRouter 가 use() 로 기다린다

 task.route (FlightRouterState)
      --> 같은 자리에서 state.tree 가 된다. **다음** 내비게이션의 "이전 트리" 다

 task.dynamicRequestTree
      --> FSR 이 `next-router-state-tree` 헤더로 서버에 보낸다 (FSR L159)
      --> 서버는 `refetch` 표시가 붙은 곳부터 그린다 — [중간부터 그리기] 흐름의 입력이다
          (walk-tree-with-flight-router-state.tsx L113 `flightRouterState[3] === 'refetch'`)

 BFCache 항목 (writeToBFCache)
      --> 다음 뒤로/앞으로가 [02]의 HistoryTraversal 갈래에서 읽는다

 ACTION_SERVER_PATCH (재시도)
      --> [클라이언트 라우터]의 액션 큐로 다시 들어간다 → server-patch-reducer → navigateToKnownRoute
```

## 다루지 않는 것

`completeSoftNavigation`(SCNAV L715) · `completeHardNavigation`(L680) · `completeTraverseNavigation`(L853)이 상태를 조립하는 과정, `convertServerPatchToFullTree`(SCNAV L907-992)의 패치 적용과 `convertRootFlightRouterStateToRouteTree` · `RouteTree` 타입의 모양, `navigateToKnownRoute` 앞머리의 개발 경고(`prefetch={true}` 링크, SCNAV L271-315), Instant Navigation Testing API(`navigation-testing-lock.ts`, `restrictToShell` · `NavigationLock` · `getCurrentNavigationLock` 류 PPRNAV L147-158 · L2336-2383), `segmentCacheMap` 과 `CacheMap` 의 구조, `readSegmentCacheEntryForNavigation` · `waitForSegmentCacheEntry` 의 본문(세그먼트 캐시는 [프리페치]), `bfcache.ts`(201줄)의 저장 구조, `discoverKnownRoute`(`optimistic-routes.ts`)의 라우트 학습, 서버가 `next-router-state-tree` 헤더를 읽어 트리 중간부터 그리는 쪽([중간부터 그리기](../partial-tree/README.md)), 스크롤 처리(`ScrollRef` 가 LayoutRouter 에서 소비되는 과정)는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 트리를 비교해 새로 짓기](01_build-tree/README.md)
- [02 세그먼트 하나를 채우기](02_fill-segment/README.md)
- [03 서버에 RSC 요청하기](03_fetch/README.md)
- [04 응답을 쓰고, 어긋나면 다시 하기](04_write-back/README.md)
