# 01 캐시 둘과 항목 상태

상위: [프리페치가 쌓이고 내비게이션이 그것을 쓰기까지](../README.md)

캐시가 **둘**이다. 라우트 트리를 담는 것과 세그먼트 데이터를 담는 것. 항목은 각각 **네 상태**를 가진다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L184-L336 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L184-L336))

## 실제 코드

상태는 `cache-map.ts` 가 정의하고 두 캐시가 공유한다.

```text
 cache-map.ts L76-81
   export const enum EntryStatus {
     Empty = 0,
     Pending = 1,
     Fulfilled = 2,
     Rejected = 3,
   }
 주석 L83-86 - 이 모듈이 실제로 다루는 타입은 RouteCacheEntry ·
   SegmentCacheEntry · BFCacheEntry 셋뿐이다. 프로토콜을 둔 것은
   모듈 사이로 관심사가 새지 않게 결합을 추적하려는 것이다
```

```ts
// cache.ts L285-L326
export type EmptySegmentCacheEntry = SegmentCacheEntryShared & {
  status: EntryStatus.Empty
  blockedTasks: Set<PrefetchTask> | null
  rsc: null
  isPartial: true
  promise: null
}

export type PendingSegmentCacheEntry = SegmentCacheEntryShared & {
  status: EntryStatus.Pending
  blockedTasks: Set<PrefetchTask> | null
  rsc: null
  isPartial: boolean
  promise: null | PromiseWithResolvers<FulfilledSegmentCacheEntry | null>
}

type RejectedSegmentCacheEntry = SegmentCacheEntryShared & {
  status: EntryStatus.Rejected
  blockedTasks: Set<PrefetchTask> | null
  rsc: null
  isPartial: true
  promise: null
}

export type FulfilledSegmentCacheEntry = SegmentCacheEntryShared & {
  status: EntryStatus.Fulfilled
  blockedTasks: null
  rsc: React.ReactNode | null
  isPartial: boolean
  promise: null
}

export type SegmentCacheEntry =
  | EmptySegmentCacheEntry
  | PendingSegmentCacheEntry
  | RejectedSegmentCacheEntry
  | FulfilledSegmentCacheEntry

export type NonEmptySegmentCacheEntry = Exclude<
  SegmentCacheEntry,
  EmptySegmentCacheEntry
>
```

## 동작 흐름

```text
 ★★ 캐시가 둘이다 (SCCACHE L357 · L382)

   const routeCacheMap:  CacheMap<RouteCacheEntry>   = createCacheMap()   L357
   export const segmentCacheMap: CacheMap<SegmentCacheEntry> = createCacheMap()   L382

 ★ routeCacheMap 은 **export 하지 않는다.** segmentCacheMap 만 내보낸다
 ★★ 그런데 export 하는 이유가 "모듈 밖에서 쓰라" 가 아니다 —
   L359-381 에 24줄 docstring 이 붙어 있다
     "Segment cache functions do not access this ambiently — every unit of
      work is **bound to a map when it is created**, and reads and writes
      receive that map explicitly"
   프리페치 작업은 스케줄될 때 자기 맵을 포착하고(`PrefetchTask.segmentCacheMap`),
   Instant Navigation Testing 잠금 아래 스케줄된 작업은 **잠금 범위의 사설 맵**을 받는다.
   그 밖 전부(잠금 없는 내비게이션·하이드레이션·refresh·history 복원·
   서버 액션 리다이렉트·서버 패치)가 이 공유 맵을 쓴다
 => export 는 "**명시적으로 넘길 기본 맵**" 을 내주는 것이다.
    생성 시점에 묶어 두면 잠금 전에 큐에 든 작업이 범위 맵을 오염시키지 않고,
    범위 작업의 늦은 응답이 공유 맵으로 새지 않는다
```

```text
 라우트 캐시 항목의 상태 (SCCACHE L211-241)

 L211  PendingRouteCacheEntry     status: Empty | Pending   ★ 두 값을 함께 받는다
 L221  RejectedRouteCacheEntry    status: Rejected
 L231  FulfilledRouteCacheEntry   status: Fulfilled
 L241  RouteCacheEntry = 그 셋의 유니온

 세그먼트 캐시 항목의 상태 (SCCACHE L285-323)

 L285  EmptySegmentCacheEntry      Empty
 L293  PendingSegmentCacheEntry    Pending
 L301  RejectedSegmentCacheEntry   Rejected
 L309  FulfilledSegmentCacheEntry  Fulfilled
 L317  SegmentCacheEntry = 넷의 유니온
 L323  NonEmptySegmentCacheEntry = Exclude<SegmentCacheEntry, Empty 인 것>
```

```text
 ★★★ 라우트 쪽은 Empty 와 Pending 을 **한 타입으로 묶는다** (L211-212)

   export type PendingRouteCacheEntry = RouteCacheEntryShared & {
     status: EntryStatus.Empty | EntryStatus.Pending
     ...
   }

 세그먼트 쪽은 넷을 각각 다른 타입으로 나눈다 (L285 · L293 · L301 · L309)

 => 세그먼트는 "비어 있다" 와 "요청 중이다" 를 구분해야 하고,
    라우트는 둘 다 "아직 없다" 로 충분하다는 뜻으로 보인다
 ※ 내 해석이다. 소스가 이유를 적어 놓지는 않았다
 ★ `NonEmptySegmentCacheEntry`(L323)가 따로 있는 것이 그 구분의 값어치다 —
   Empty 를 배제한 타입을 요구하는 자리가 있다
```

```text
 ★★ 완성도를 항목에 기록해 두고 `<` **와 `isPartial`** 로 비교한다

 SCCACHE L4058-4063
   export function canNewFetchStrategyProvideMoreContent(
     currentStrategy: FetchStrategy,
     newStrategy: FetchStrategy
   ): boolean {
     return currentStrategy < newStrategy
   }

 => [README]에서 본 FetchStrategy 여섯 단계가 이 한 줄을 위해 순서대로 매겨졌다
 ★★★ 그런데 이 한 줄만으로 답하지 않는다. docstring(L4046-4053)이 그렇게 시킨다 —
   완전 정적인 세그먼트처럼 "더 구체적인 전략이 더 주지 못하는" 경우가 있으니
   **기존 항목이 partial 인지도 함께 보라**고 한다.
   호출처 일곱 중 여섯이 `isPartial` 과 짝지어 쓴다 (L1002 · SCHED L1891 등)

 ★ 그리고 항목에 적힌 티어는 "무엇으로 요청했나" 가 아니다 —
   필드 docstring L250-263 이, 정적 응답이 런타임 데이터를 안 건드렸으면
   같은 variant 의 **런타임 티어로 기록한다**고 적는다.
   그 덕에 "런타임 요청이 더 줄까" 를 별도 신호 없이 티어 비교로 답한다
```

```text
 ★ 무효화 함수가 **셋**이다 (SCCACHE L413-448)

 L413  invalidateEntirePrefetchCache(...)
 L431  invalidateRouteCacheEntries(...)
 L448  invalidateSegmentCacheEntries(...)

 L493  pingInvalidationListeners(...)  ← 무효화가 아니라 **통지**다
         주석 L497-500 - Next-Url 이나 base tree 가 바뀔 때,
           그리고 무효화 **뒤에** 부른다. `router.prefetch(onInvalidate)` 로
           등록된 콜백을 깨우는 통로다 (L458 attach · L473 notify 가 짝)

 => [클라이언트 라우터] [03]에서 본 대로,
    재검증 헤더가 1 이면 invalidateEntirePrefetchCache,
    1·2 면 invalidateBfCache 를 부른다
 ★★ 버전 번호를 따로 들고 있고 (L399 getCurrentRouteCacheVersion ·
   L403 getCurrentSegmentCacheVersion) **그 방식이 주석에 적혀 있다** (L392-395)
     "Route and segment caches have separate versions so they can be
      invalidated independently. Invalidation does not eagerly evict anything
      from the cache; entries are **lazily evicted when read**."
 => 무효화가 아무것도 지우지 않는다. 읽을 때 버전이 낡았으면 그때 버린다
```

## 결과가 쓰이는 곳

```text
 routeCacheMap
      --> [03]의 navigate 가 라우트 트리를 여기서 찾는다.
          있으면 **동기로** 화면을 바꾼다
      ★ "서버에 안 묻는다" 는 아니다 — 트리가 맞아도
        `spawnDynamicRequests`(SCNAV L373)가 돈다. 다만 그것을 기다리지 않는다

 segmentCacheMap (export)
      --> 세그먼트 단위 데이터. 부분만 받아 놓은 상태도 여기 들어간다
      --> 모듈 밖에서도 쓸 수 있게 내보낸다

 EntryStatus
      --> 읽는 함수들(L512 readRouteCacheEntry · L557 readSegmentCacheEntryForNavigation ·
          L616 waitForSegmentCacheEntry)이 이 값으로 갈린다
      --> Pending 이면 기다리고, Fulfilled 면 바로 쓰고, Rejected 면 포기한다

 캐시 버전 번호
      --> 무효화. 항목을 지우는 대신 버전을 올린다
```

## 다루지 않는 것

`CacheMap`(`cache-map.ts` 497줄)의 자료구조와 `lru.ts`(127줄)의 축출 정책, `readRouteCacheEntry`(L512) / `readSegmentCacheEntryForNavigation`(L557) / `waitForSegmentCacheEntry`(L616) / `readOrCreateRouteCacheEntry`(L661) / `readOrCreateSegmentCacheEntry`(L868) / `readOrCreateRevalidatingSegmentEntry`(L909) / `overwriteRevalidatingSegmentCacheEntry`(L961)의 본문, `RouteCacheEntryShared` / `SegmentCacheEntryShared` / `SegmentBundle`(L336)의 필드, `RefreshState`(L169) · `RouteTree`(L184) · `MetadataOnlyRequestTree`(L350), `deprecated_requestOptimisticRouteCacheEntry`(L689)와 낙관적 라우트, 무효화 함수 셋의 본문과 버전 비교가 읽기 함수 안에서 실제로 일어나는 자리, `attachInvalidationListener`(L458) · `notifyInvalidationListener`(L473)와 `router.prefetch(onInvalidate)` 계약, `getStaleAtFromHeader`(L4065)의 헤더 파싱은 이 문서의 범위 밖이다.
