# 프리페치 작업 하나가 태어나서 끝나기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[프리페치]의 [02 프리페치 큐](../segment-cache/02_scheduler/README.md)가 "공개 표면과 한도 12 대 4" 까지만 보고 본문을 범위 밖으로 남겼다. 이 흐름은 그 본문이다 — **작업 객체 하나**가 `schedulePrefetchTask` 로 만들어져 큐에 들어가고, 여러 번 깨어나 요청을 내보내고, 끝나거나 취소되거나 무효화 뒤 다시 태어나는 과정. 캐시 항목 자체의 읽기·쓰기는 [캐시 항목](../cache-entries/README.md)이 본다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `SCHED` = `client/components/segment-cache/scheduler.ts`(2741줄), `SCPREF` = `.../segment-cache/prefetch.ts`(48줄), `SCFETCH` = `.../segment-cache/fetch.ts`(26줄), `LINKS` = `client/components/links.ts`(401줄), `LINKTSX` = `client/app-dir/link.tsx`, `SCCACHE` = `.../segment-cache/cache.ts`(4298줄), `SCNAV` = `.../segment-cache/navigation.ts`, `APPRINST` = `client/components/app-router-instance.ts`, `SCTYPES` = `.../segment-cache/types.ts`, `SARED` = `client/components/router-reducer/reducers/server-action-reducer.ts`, `APPROUTER` = `client/components/app-router.tsx`, `CFRS` = `server/app-render/create-flight-router-state-from-loader-tree.ts`.

## 위치

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L317-L377 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L317-L377))

`packages/next` / `src/client/components/segment-cache` / `prefetch.ts` L27-L48 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/prefetch.ts#L27-L48))

## 실제 코드

작업은 이 한 함수에서만 **새로** 만들어진다. 만들자마자 큐에 넣고, 처리는 마이크로태스크로 미룬다.

```ts
// scheduler.ts L317-L377
export function schedulePrefetchTask(
  key: RouteCacheKey,
  treeAtTimeOfPrefetch: FlightRouterState,
  fetchStrategy: PrefetchTaskFetchStrategy,
  priority: PrefetchPriority,
  onInvalidate: null | (() => void),
  navigationLockPrefetch: NavigationLockPrefetch | null
): PrefetchTask {
  // Bind the task to the segment cache map that is active right now: the
  // shared map, unless the Instant Navigation Testing lock is held, in which
  // case the task gets the lock scope's private map. This is the single
  // place work is bound to a map based on lock state — everything downstream
  // receives the map explicitly. See `segmentCacheMap` in cache.ts.
  let taskSegmentCacheMap = segmentCacheMap
  if (process.env.__NEXT_EXPOSE_TESTING_API) {
    const { getNavigationLockSegmentCacheMap } =
      require('./navigation-testing-lock') as typeof import('./navigation-testing-lock')
    const lockMap = getNavigationLockSegmentCacheMap()
    if (lockMap !== null) {
      taskSegmentCacheMap = lockMap
    }
  }

  // Spawn a new prefetch task
  const task: PrefetchTask = {
    key,
    treeAtTimeOfPrefetch,
    routeCacheVersion: getCurrentRouteCacheVersion(),
    segmentCacheVersion: getCurrentSegmentCacheVersion(),
    segmentCacheMap: taskSegmentCacheMap,
    priority,
    phase: PrefetchPhase.RouteTree,
    hasBackgroundWork: false,
    hasPendingResponses: false,
    spawnedRuntimePrefetches: null,
    fetchStrategy,
    sortId: sortIdCounter++,
    isCanceled: false,
    fallbackRetryStatus: EntryStatus.Empty,
    onInvalidate,
    _heapIndex: -1,
  }
  if (process.env.__NEXT_EXPOSE_TESTING_API) {
    task._navigationLockPrefetch = navigationLockPrefetch
  }

  trackMostRecentlyHoveredLink(task)

  heapPush(taskHeap, task)

  // Schedule an async task to process the queue.
  //
  // The main reason we process the queue in an async task is for batching.
  // It's common for a single JS task/event to trigger multiple prefetches.
  // By deferring to a microtask, we only process the queue once per JS task.
  // If they have different priorities, it also ensures they are processed in
  // the optimal order.
  pingPrefetchScheduler()

  return task
}
```

```text
 ★★ 인자가 여섯인데 우선순위를 뺀 다섯이 모두 "작업이 끝날 때까지 들고 다닐 것" 이다
   key                    RouteCacheKey (pathname · search · nextUrl)
   treeAtTimeOfPrefetch   **지금 화면의** FlightRouterState — 비교 기준
   fetchStrategy          PPR 또는 Full (아래 ★★★)
   onInvalidate           router.prefetch 의 콜백
   navigationLockPrefetch 테스트 API 전용

 L330-338  세그먼트 캐시 맵을 **여기서 한 번** 묶는다
   주석 L327-329 - "This is the single place work is bound to a map based on
     lock state — everything downstream receives the map explicitly."
   => 테스트 잠금이 걸려 있으면 사설 맵, 아니면 공유 `segmentCacheMap`
 L344-345  캐시 버전 둘을 태어날 때 찍어 둔다 → [04]의 dirty 판정
   ★ 다만 필드 주석(L77-82)의 "at the time the task was initiated" 와 달리
     **매 패스 시작 때 다시 찍는다** (L595-596) → [01]
 L348      phase: RouteTree — 모든 작업은 라우트 트리부터 시작한다 → [01]
 L353      sortId: sortIdCounter++ — 나중에 만든 것이 먼저다 → [03]
 L363      trackMostRecentlyHoveredLink — Intent 면 이전 Intent 를 끌어내린다 → [03]
 L374      pingPrefetchScheduler() — **여기서 요청을 보내지 않는다**
   주석 L369-373 - "It's common for a single JS task/event to trigger multiple
     prefetches. By deferring to a microtask, we only process the queue once per
     JS task. If they have different priorities, it also ensures they are
     processed in the optimal order."
```

## 동작 흐름

```text
 누가 작업을 만드는가 — schedulePrefetchTask 호출처 **넷** (grep 전수, 파일 셋)

 LINKS  L346   rescheduleLinkPrefetch  — 링크의 첫 작업
 LINKS  L392   pingVisibleLinks        — 무효화·트리 변경 뒤 새 작업 → [04]
 SCPREF L40    prefetch()              — router.prefetch 가 부른다 (APPRINST L431)
 SCNAV  L1236  ensurePrefetchThenNavigate — 테스트 API 잠금 아래 내비게이션

 그리고 **새로 만들지 않고 되살리는** 길이 하나 더 있다
 LINKS  L357   reschedulePrefetchTask(existingPrefetchTask, ...)   → [01]
   주석 LINKS L355-356 - "This is effectively the same as canceling the old
     task and creating a new one."
```

```text
 <Link> 한 개의 경로

 LINKTSX L383-391   prefetch prop -> prefetchIntent -> fetchStrategy
                    false => 'none' (그래도 FetchStrategy.PPR 을 넣는다 — TODO 주석 L390)
                    true  => 'full',  그 밖 => 'auto'
 LINKTSX L810-829   getFetchStrategyFromPrefetchIntent
                    'auto' => PPR,  'full' => Full   (cacheComponents 유무와 무관하게 결과가 같다)
 LINKTSX L629       ref 콜백 -> mountLinkInstance(LINKS L170)
 LINKS   L143-168   coercePrefetchableUrl -> createPrefetchURL
 LINKS   L121-126   IntersectionObserver(rootMargin '200px') 하나를 모든 링크가 공유
 LINKS   L270-290   onLinkVisibilityChanged -> rescheduleLinkPrefetch(instance, Default)
 LINKTSX L706-731   onMouseEnter -> onNavigationIntent -> rescheduleLinkPrefetch(instance, Intent)
 LINKS   L313-366   rescheduleLinkPrefetch
   L321    보이지 않으면 cancelPrefetchTask 하고 => return
   L342    작업이 없으면 schedulePrefetchTask,  있으면 L357 reschedulePrefetchTask

 router.prefetch(href, options)   APPRINST L395-438
   L406    kind 기본 AUTO -> PPR,  FULL -> Full
   주석 L408 - "We don't currently offer a way to issue a runtime prefetch via
     `router.prefetch()`."
   L431    prefetchWithSegmentCache = SCPREF prefetch() -> Default 우선순위로 schedule
```

```text
 ★★★ 개발 서버에서는 <Link> 와 router.prefetch 가 **작업을 만들지 않는다** — 공통 관문은 첫째(createPrefetchURL)이고
   나머지 둘은 그 위에 한 번 더 건 관문이다 (onTouchStart 는 개발 검사가 없지만 prefetchable 에 등록이 안 돼 끝난다, LINKS L296-300)

   app-router-utils.ts L32-35   createPrefetchURL 이 development 면 null
     주석 - "Don't prefetch during development (improves compilation performance)"
     => SCPREF L35-38 이 return, LINKS mountLinkInstance 는 Prefetchable 이 아닌 인스턴스를 만든다
   LINKS L271-276               onLinkVisibilityChanged 가 production 이 아니면 return
   LINKTSX L722-724             onMouseEnter 도 development 면 return
 => 개발에서 이 흐름에 들어오는 길은 SCNAV L1236(테스트 API) 하나다
 ★ 그리고 봇이면 production 에서도 null 이다 (app-router-utils.ts L17-19 `isBot`)
```

```text
 ★★★ 작업의 fetchStrategy 는 **실제로는 PPR 또는 Full 둘뿐**이다

   타입 PrefetchTaskFetchStrategy (SCTYPES L65-68) = PPR | PPRRuntime | Full
   그런데 위 호출처 넷과 reschedule 하나가 넘기는 값은
     link.tsx  L810-829 -> PPR | Full
     links.ts  L307     -> onNavigationIntent 가 __NEXT_DYNAMIC_ON_HOVER 이면 Full 로 바꾼다
     form.tsx  L108     -> PPR (mountFormInstance 의 넷째 인자)
     APPRINST  L411-428 -> PPR | Full
     SCNAV     L1224    -> link.fetchStrategy 또는 PPR
 => PPRRuntime 을 작업에 싣는 호출처가 **없다** (grep `FetchStrategy.PPRRuntime` 전수 — 나머지 참조는
    캐시·내비게이션 쪽이다)
 => 그래서 SCHED L1001 · L1617 의 `case FetchStrategy.PPRRuntime` 는 작업 경로로는 도달하지 않는다 → [02]
    PPRRuntime 은 작업의 전략이 아니라 **PPR 걷기가 격상할 때** 스케줄러가 스스로 고르는 값이다 (L955-958)
```

```text
 SCFETCH L13-24 — 프리페치 요청은 전역 fetch 를 직접 부르지 않는다

   fetchInternal(input, init)
     __NEXT_EXPOSE_TESTING_API 이고 getPreLockFetch() 가 있으면 그것으로
     아니면 fetch(input, init)
 => cache.ts 의 요청 함수들이 `import { fetch } from './fetch'`(SCCACHE L35)로 이것을 쓴다
 ★ 테스트 잠금이 window.fetch 를 막아도 라우터 내부 요청은 **잠금 전 fetch** 로 빠져나간다
```

1. [작업의 한살이](01_lifecycle/README.md) — 필드, 세 phase, 한 번의 큐 처리와 세 가지 종료 상태.
2. [한 번의 패스](02_one-pass/README.md) — 라우트 트리 먼저, 전략 고르기, 세그먼트 걷기와 요청 만들기.
3. [순서와 대역폭](03_concurrency/README.md) — 힙 비교 규칙, Intent 하나, 12 대 4, 쿨다운, 백그라운드.
4. [작업이 끝나는 자리](04_end/README.md) — Blocked 와 재깨움, 완료, 취소, 무효화 뒤 다시 태어나기.

## 결과가 쓰이는 곳

```text
 PrefetchTask (반환값)
      --> LINKS 의 instance.prefetchTask 에 붙어 산다. 다음 hover·가시성 변화 때
          **같은 객체**가 reschedule 된다
      --> SCNAV ensurePrefetchThenNavigate 는 버린다 — 대신 navigationLockPrefetch.promise 를 기다린다
      --> SCPREF prefetch() 도 버린다. router.prefetch 는 작업을 되돌려 주지 않는다

 캐시 항목 (작업이 만든 요청의 응답이 직접 쓴다)
      --> [캐시 항목]의 routeCacheMap · task.segmentCacheMap
      --> [프리페치] [03]의 navigate 가 읽는다. 맞으면 동기 내비게이션이다

 서버로 가는 요청 셋 (spawnPrefetchSubtask 호출 다섯 곳 → cache.ts 함수 셋)
      --> fetchRouteOnCacheMiss             '/_tree'   → [트리 조립] [04] · [중간부터 그리기]
      --> fetchSegmentsOnCacheMiss          세그먼트 키 → [트리 조립] [04]가 미리 잘라 둔 것
      --> fetchSegmentPrefetchesUsingDynamicRequest   → [중간부터 그리기]가 'refetch' 부터 그린다
```

## 다루지 않는 것

`cache.ts` 의 항목 읽기·생성·채우기(`readOrCreateRouteCacheEntry` · `readOrCreateSegmentCacheEntry` · `upgradeToPendingSegment` · `upsertSegmentEntry` 등)와 세 요청 함수의 응답 파싱은 [캐시 항목](../cache-entries/README.md)과 이 흐름의 범위 밖이다. `link.tsx` 의 나머지(클릭 처리 `linkClicked`, `legacyBehavior`, `useLinkStatus`), `form.tsx` 의 제출 처리, `offline.ts`(187줄)의 연결 감지, `navigation-testing-lock.ts`(553줄)의 잠금 범위와 `getPreLockFetch` · `resolveNavigationLockPrefetch` 의 본문, `optimistic-routes.ts`(1119줄)의 `matchKnownRoute`(L726) 중 L766-811 을 뺀 매칭 알고리즘, `cache-key.ts` 의 `createCacheKey` 는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 작업의 한살이](01_lifecycle/README.md)
- [02 한 번의 패스](02_one-pass/README.md)
- [03 순서와 대역폭](03_concurrency/README.md)
- [04 작업이 끝나는 자리](04_end/README.md)
