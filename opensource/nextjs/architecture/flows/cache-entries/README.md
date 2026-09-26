# 세그먼트 캐시 항목이 만들어지고 채워지고 버려지기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[프리페치가 쌓이고 내비게이션이 그것을 쓰기까지](../segment-cache/README.md)의 [01 캐시 둘과 항목 상태](../segment-cache/01_entries/README.md)는 항목의 **모양**(네 상태 · 캐시 둘 · 버전 번호)만 보고 본문을 모두 범위 밖으로 넘겼다. 이 흐름이 그 본문이다 — 항목 하나가 **어느 키에 생기고, 누가 채우고, 어느 키로 옮겨지고, 언제 사라지는가**.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `SCCACHE` = `client/components/segment-cache/cache.ts`(4298줄), `CMAP` = `.../cache-map.ts`(497줄), `LRU` = `.../lru.ts`(127줄), `VARY` = `.../vary-path.ts`(437줄), `CKEY` = `.../cache-key.ts`(61줄), `SCHED` = `.../scheduler.ts`, `PPRNAV` = `client/components/router-reducer/ppr-navigations.ts`.

## 위치

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L868-L907 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L868-L907))

## 실제 코드

세그먼트 항목을 "읽거나 만든다" 는 함수 둘이다. 이 흐름 전체의 요점이 여기 들어 있다 — **읽는 키와 쓰는 키가 다르다.**

```ts
// cache.ts L868-L907
export function readOrCreateSegmentCacheEntry(
  now: number,
  // The map the calling task operates in (`PrefetchTask.segmentCacheMap`,
  // captured when the task was scheduled).
  map: CacheMap<SegmentCacheEntry>,
  fetchStrategy: FetchStrategy,
  tree: RouteTree
): SegmentCacheEntry {
  const existingEntry = getFromCacheMap(
    now,
    getCurrentSegmentCacheVersion(),
    map,
    tree.varyPath,
    false,
    false
  )
  if (existingEntry !== null) {
    return existingEntry
  }
  return insertEmptySegmentCacheEntry(now, map, fetchStrategy, tree)
}

/**
 * Creates an empty segment cache entry and inserts it into the cache, keyed
 * at the vary path a request made with the given fetch strategy is stored
 * under. The stale time is set to a default value; the actual stale time will
 * be set when the entry is fulfilled with data from the server response.
 */
function insertEmptySegmentCacheEntry(
  now: number,
  map: CacheMap<SegmentCacheEntry>,
  fetchStrategy: FetchStrategy,
  tree: RouteTree
): EmptySegmentCacheEntry {
  const varyPathForRequest = getSegmentVaryPathForRequest(fetchStrategy, tree)
  const emptyEntry = createDetachedSegmentCacheEntry(now)
  const isRevalidation = false
  setInCacheMap(map, varyPathForRequest, emptyEntry, isRevalidation)
  return emptyEntry
}
```

```text
 ★★★ 읽을 때는 `tree.varyPath`, 만들 때는 `getSegmentVaryPathForRequest(fetchStrategy, tree)` 다

   tree.varyPath                 모든 파라미터가 **구체값**인 키 (가장 구체적)
   getSegmentVaryPathForRequest  전략에 따라 일부를 `Fallback` 으로 바꾼 키 (더 일반적)
                                 (VARY L275-353 — [03])

 => 빈 항목은 **처음부터 일반적인 자리**에 둔다.
    그래도 다음 읽기가 찾는다 — CacheMap 의 조회는 정확히 맞는 키가 없으면
    같은 자리의 `Fallback` 키로 내려가 본다 (CMAP L356-369)
 => 그래서 "없으면 만든다" 가 같은 키에 대한 get/set 이 아니다.
    키가 넓어지는 것은 두 경우뿐이다 (VARY L275-353) — Shell 전략(StaticShell · RuntimeShell)이면
    비루트 파라미터가, **페이지**(Full · PPRRuntime 가 아닐 때)면 검색 문자열이 달라도 한 빈 항목에 모인다.
    레이아웃이면서 Shell 이 아니면(기본 설정의 LoadingBoundary · Full 대부분) 읽기 키와 같다

 ★ docstring(L890-895)이 적는 대로 stale 시간은 **임시값**이다 —
   "The stale time is set to a default value; the actual stale time will
    be set when the entry is fulfilled with data from the server response."
   (그 기본값은 `createDetachedSegmentCacheEntry` L1199 의 30초 — [04])
```

```text
 ★★★ 기본 설정(cacheComponents 꺼짐)에서 실제로 도는 길

   라우트 응답   정적 생성된 페이지는 `x-nextjs-postponed: 2` 로 segmentData 를 받아 PPR 가지로,
                 동적 라우트는 L2063 routeIsPPREnabled 가 거짓이라 비-PPR 가지(L2132
                 writeDynamicTreeResponseIntoCache)로 간다
   세그먼트      동적 라우트는 LoadingBoundary(자동) 또는 Full(`prefetch={true}`) 전략으로
                 fetchSegmentPrefetchesUsingDynamicRequest → writeDynamicRenderResponseIntoCache
   cacheComponents 에서만 도는 것
                 StaticShell · RuntimeShell 전략, 셸/분리 사본 쓰기와 ISR 재시도([02]),
                 varyParams 재키잉 — 서버가 varyParams 누산기를 만드는 렌더가 cacheComponents
                 경로뿐이라(app-render.tsx L1021 · L1808 · L3596, vary-params.ts L140-152)
                 기본 설정에서는 varyParams 가 null 이다
                 내비게이션 · 첫 로드의 static-stage · runtime 스트림 쓰기(cachedNavigations)
```

## 동작 흐름

```text
 항목 하나의 일생 (세그먼트)

 [01] 만든다     readOrCreateSegmentCacheEntry        L868   Empty
                 readOrCreateRevalidatingSegmentEntry  L909   Empty (Revalidation 칸에)
                 createDetachedSegmentCacheEntry       L1194  Empty, 맵 밖 (ref: null)
      ~~> 스케줄러가 요청을 띄우기 직전
      올린다     upgradeToPendingSegment               L1220  Pending   version 을 여기서 찍는다
 [02] 채운다     fulfillSegmentCacheEntry              L1470  Fulfilled  promise 를 풀고 blockedTasks 를 깨운다
      거절한다   rejectSegmentCacheEntry               L1519  Rejected   promise 를 null 로 풀고 깨운다
      옮긴다     upsertSegmentEntry / setInCacheMap           응답이 알려 준 **더 일반적인 키**로
 [03] 찾는다     getFromCacheMap                       CMAP L229   정확 -> Fallback 순
 [04] 버린다     isValueExpired                        CMAP L260   staleAt 지남 · version 낡음
                 cleanup                               LRU L109    50MB 넘으면 90% 까지

 라우트 항목은 짧다
   readOrCreateRouteCacheEntry L661 -> Empty
   ~~> SCHED L833  route.status = EntryStatus.Pending  (그리고 staleAt = now + 60초, L830)
   fetchRouteOnCacheMiss L1928 -> fulfillRouteCacheEntry L1380 / rejectRouteCacheEntry L1509
   couldBeIntercepted 가 거짓이면 Next-Url 칸을 Fallback 으로 **다시 건다** (L2185-2205)
```

```text
 ★★ 상태 전이는 **새 객체를 만들지 않는다.** 같은 객체의 필드를 덮어쓴다

   L1224  const pendingEntry: PendingSegmentCacheEntry = emptyEntry as any
   L1392  const fulfilledEntry: FulfilledRouteCacheEntry = entry as any
   L1492  const fulfilledEntry: FulfilledSegmentCacheEntry = segmentCacheEntry as any
   L1513  const rejectedEntry: RejectedRouteCacheEntry = entry as any
   L1523  const rejectedEntry: RejectedSegmentCacheEntry = entry as any
   (grep "status = EntryStatus" — cache.ts 다섯 곳 + scheduler.ts 두 곳 L762 · L833)

 => 이 항목을 들고 있는 쪽(내비게이션의 `waitForSegmentCacheEntry`, 스케줄러의 작업)이
    **같은 참조로 상태 변화를 본다.** 타입은 `as any` 로 갈아 끼운다
 ★ 그래서 `upsertSegmentEntry` 주석(L1059-1067)이 "후보를 **변형하지 말라**" 고 한다 —
   이미 누가 그 객체를 받아 `rsc` 를 읽으려 하고 있을 수 있다 ([03])
```

```text
 모듈 경계 (주석 CMAP L56-65)

   "Anything to do with retrival, lifetimes, or eviction needs to go in this
    module because it affects the fallback algorithm. For example, when
    performing a lookup, if an entry is stale, it needs to be treated as
    semantically equivalent to if the entry was not present at all."

 => 수명 판정(staleAt · version)이 cache.ts 가 아니라 **cache-map.ts 에** 있다.
    낡은 항목은 "없는 것" 과 같아야 Fallback 탐색이 그 아래로 내려갈 수 있기 때문이다
 ★ 원문의 "retrival" 은 원문 철자 그대로다
```

1. [읽거나 만들기](01_read-or-create/README.md) — 읽는 함수 넷, 만드는 함수 일곱(+ optimistic 쓰기 writeRouteIntoCache), Pending 으로 올리는 함수 하나.
2. [채우기와 다시 걸기](02_fill/README.md) — 응답이 항목을 채우고 더 일반적인 키로 옮긴다.
3. [맵과 키](03_map/README.md) — `CacheMap` 의 Fallback 탐색, vary path, 가림 항목 축출.
4. [수명과 축출](04_stale-evict/README.md) — staleAt 의 출처들, 버전 무효화, LRU.

## 결과가 쓰이는 곳

```text
 Fulfilled 세그먼트 항목 (rsc · isPartial · fetchStrategy)
      --> [PPR 내비게이션] [02](../ppr-navigation/02_fill-segment/README.md)의 createCacheNodeForSegment 가
          PPRNAV L1127 에서 readSegmentCacheEntryForNavigation 으로 꺼내 CacheNode 에 넣는다
      --> [프리페치] [02](../segment-cache/02_scheduler/README.md)의 스케줄러가
          "더 받을 게 있나" 를 fetchStrategy 와 isPartial 로 판단한다

 Pending 항목의 promise
      --> 내비게이션이 기다린다 (PPRNAV L1145 waitForSegmentCacheEntry)

 blockedTasks
      --> 채우거나 거절할 때 pingBlockedTasks(L1345)가 그 작업들을 다시 큐에 넣는다

 Fulfilled 라우트 항목 (tree · metadata · canonicalUrl)
      --> [프리페치] [03](../segment-cache/03_navigate/README.md)의 navigate 가 SCNAV L150 에서 읽는다
```

## 다루지 않는 것

요청을 만들어 보내는 쪽 — `fetchRouteOnCacheMiss`(L1928)의 요청 헤더·`output: export` 분기(L1957-2022), `fetchSegmentsOnCacheMissImpl`(L2363)의 셸 오프셋 디코딩, `fetchSegmentPrefetchesUsingDynamicRequest`(L3027-3377)의 헤더 매핑·단계 분리, `createNonTaskyPrefetchResponseStream`(L3899) · `createIncrementalPrefetchResponseStream`(L3981), 그리고 라우트 트리 변환(`convertRootTreePrefetchToRouteTree` L1542 · `convertFlightRouterStateToRouteTree` L1770 · `convertRouteTreeToFlightRouterState` L1905)은 이 흐름의 범위 밖이다. 스케줄러가 어느 항목에 어떤 전략으로 요청을 띄울지 정하는 규칙([프리페치] [02](../segment-cache/02_scheduler/README.md)), `optimistic-routes.ts`(1119줄)의 `matchKnownRoute` · `discoverKnownRoutePart` 내부와 `deprecated_requestOptimisticRouteCacheEntry`(L689-862), `bfcache.ts`(201줄)의 저장 구조, 내비게이션이 응답을 CacheNode 에 쓰는 쪽([PPR 내비게이션] [04](../ppr-navigation/04_write-back/README.md)), 서버가 세그먼트 응답과 varyParams 를 만드는 쪽([트리 조립] [04](../tree-assembly/04_slice/README.md)), `vary-params-decoding.ts` 의 `drainVaryParams` 본문도 다루지 않는다.

## 하위 메서드

- [01 읽거나 만들기](01_read-or-create/README.md)
- [02 채우기와 다시 걸기](02_fill/README.md)
- [03 맵과 키](03_map/README.md)
- [04 수명과 축출](04_stale-evict/README.md)
