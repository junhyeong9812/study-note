# 01 읽거나 만들기

상위: [세그먼트 캐시 항목이 만들어지고 채워지고 버려지기까지](../README.md)

읽는 함수가 넷(L512 · L557 · L600 · L616 — 단 L616 waitForSegmentCacheEntry 는 조회가 아니라 promise 를 붙인다)이고, 항목을 만드는 함수가 일곱(L631 · L661 · L868 · L896 · L909 · L961 · L1194)이다. 이 밖에 optimistic 쪽 writeRouteIntoCache(L1420)도 항목을 만들어(L1431) 맵에 넣고(L1448), deprecated_requestOptimisticRouteCacheEntry(L689)는 맵에 넣지 않는 항목을 만든다. 읽기는 **두 번 조회**할 때가 있고, 만들기는 **맵 밖에서** 먼저 만들 때가 있다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L512-L682 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L512-L682))

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L868-L978 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L868-L978))

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L1194-L1243 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L1194-L1243))

## 실제 코드

내비게이션용 읽기다. 같은 키로 **두 번** 찾는다.

```ts
// cache.ts L557-L598
export function readSegmentCacheEntryForNavigation(
  now: number,
  // The map the navigation is bound to: a locked navigation's driving-task
  // map, or the shared map otherwise.
  map: CacheMap<SegmentCacheEntry>,
  varyPath: SegmentVaryPath,
  restrictToShell: boolean = false
): SegmentCacheEntry | null {
  const isRevalidation = false

  let lookupVaryPath = varyPath
  if (process.env.__NEXT_EXPOSE_TESTING_API && restrictToShell) {
    // Instant Navigation Testing API: we're navigating to a link that 1) has
    // Partial Prefetching enabled, and 2) does not have a prefetch prop set.
    // Only the shell may render, not anything that varies on concrete route
    // params.
    lookupVaryPath = getShellSegmentVaryPath(varyPath)
  }

  // Prefer a Fulfilled entry (e.g. a cached shell) over a more-specific
  // Pending/Rejected one so it renders immediately instead of blocking on an
  // in-flight entry.
  const fulfilled = getFromCacheMap(
    now,
    getCurrentSegmentCacheVersion(),
    map,
    lookupVaryPath,
    isRevalidation,
    true
  )
  if (fulfilled !== null) {
    return fulfilled
  }
  return getFromCacheMap(
    now,
    getCurrentSegmentCacheVersion(),
    map,
    lookupVaryPath,
    isRevalidation,
    false
  )
}
```

```text
 ★★★ 첫 조회는 `onlyMatchFulfilled = true`, 둘째는 `false` 다 (L585 · L596)

 docstring(L543-556)이 이유를 적는다
   "Unlike a plain lookup, prefers a Fulfilled entry over a more-specific
    Pending or Rejected entry: during a navigation, a less-specific shell entry
    (e.g. params -> Fallback) should be rendered immediately rather than
    blocking on a more-specific Pending entry that may still be in-flight."

 => 구체적 키에 **요청 중인** 항목이 있고, 더 일반적인 키(Fallback)에 **완료된 셸**이 있으면
    내비게이션은 셸을 고른다. 기다리지 않고 바로 그린다
 => 그 플래그가 CacheMap 안에서 하는 일은 한 줄이다 (CMAP L290-294)
      if (onlyMatchFulfilled && value.status !== EntryStatus.Fulfilled) return null
    null 이면 재귀가 **그 자리의 Fallback 으로 내려간다** ([03])
 ★ 첫 조회가 못 찾으면 둘째가 **상태를 가리지 않고** 가장 구체적인 것을 준다 —
   Pending 이면 [PPR 내비게이션] [02](../../ppr-navigation/02_fill-segment/README.md)가
   waitForSegmentCacheEntry 로 약속을 받는다 (PPRNAV L1145)

 ★ `restrictToShell` 은 `__NEXT_EXPOSE_TESTING_API` 일 때만 본다 (L568).
   그때는 키를 `getShellSegmentVaryPath` 로 바꿔 **셸만** 찾는다 ([03])
   ※ 이 플래그는 개발 서버이거나 `exposeTestingApiInProductionBuild` 일 때만 켜진다
     (build/define-env.ts L396-397). 프로덕션 기본 번들에서는 이 갈래가 사라진다
```

## 동작 흐름

```text
 readRouteCacheEntry(now, key)                                          L512-541

 L516  varyPath = getRouteVaryPath(pathname, search, nextUrl)           세 칸 ([03])
 L522  getFromCacheMap(now, 라우트 버전, routeCacheMap, varyPath, false, false)
 L530  있으면 => return
 L536  `__NEXT_OPTIMISTIC_ROUTING` 이면
 L537    => return matchKnownRoute(now, pathname, search)
 L540  => return null

 ★★ 캐시 미스에서 **예측한 항목**을 돌려줄 수 있다.
   optimistic-routes.ts L793-807 이 만드는 것은 `ref: null` 인 합성 Fulfilled 항목이다 —
   **맵에 넣지 않는다.** 그리고 그 합성 항목을 패턴 자리에 둔다 (L809)
 => optimisticRouting 은 기본으로 켜져 있다 (config-shared.ts L2175 → define-env.ts L391-392)
 ★ 이 합성 항목이 readOrCreateRouteCacheEntry 로도 흘러간다 (아래 L668-670).
   그러면 Empty 항목을 **만들지 않고**, 라우트 트리 요청도 없이 Fulfilled 로 진행한다
   ※ 예측이 틀렸을 때의 복구(`markRouteEntryAsDynamicRewrite` L1461)는 [02]에서 짧게 본다
```

```text
 readOrCreateRouteCacheEntry(now, task, key)                             L661-682

 L666  attachInvalidationListener(task)          ← router.prefetch(onInvalidate) 의 콜백 등록
 L668  existingEntry = readRouteCacheEntry(now, key)
 L669    있으면 => return
 L673  pendingEntry = createDetachedRouteCacheEntry()                     L631-655
 L680  setInCacheMap(routeCacheMap, getRouteVaryPath(...), pendingEntry, false)
 L681  => return pendingEntry                     (상태는 아직 Empty)

 createDetachedRouteCacheEntry 의 초기값
   status: Empty · couldBeIntercepted: **true** (L641) · supportsPerSegmentPrefetching: false
   staleAt: **Infinity** (L652) · version: getCurrentRouteCacheVersion() (L653)
   주석 L650-651 - "Since this is an empty entry, there's no reason to ever evict it.
     It will be updated when the data is populated."
 ★ couldBeIntercepted 를 true 로 시작하는 이유 (주석 L638-640) —
   가로채기 여부는 응답을 받아야 안다. 그래서 처음 키는 Next-Url 을 **구체값**으로 넣는다

 ~~> Empty -> Pending 은 이 파일이 아니라 스케줄러가 한다
   SCHED L830  route.staleAt = now + 60 * 1000
   SCHED L833  route.status = EntryStatus.Pending
   주석 SCHED L824-827 - "If the request takes longer than a minute, a subsequent
     request should retry instead of waiting for this one."
 ★★ 그런데 같은 파일의 **다른 자리**(SCHED L762, 검색 문자열을 뗀 라우트)는
   status 만 Pending 으로 바꾸고 staleAt 을 **건드리지 않는다** (L760-770).
   => 그 항목의 staleAt 은 L652 의 Infinity 그대로다
   (적용 조건 — key.search !== '' · exitStatus !== InProgress · background(task))
   다만 버전 판정은 받는다(L653) — 라우트 무효화가 일어나면 풀린다
   ※ 그 요청이 응답도 예외도 없이 멈추면 1분 재시도 안전망이 이 항목에는 없다.
     fetchRouteOnCacheMiss 는 try/catch 로 모든 결말에서 fulfill/reject 하므로(L2024-2228)
     실제로 문제가 되는 것은 fetch 자체가 끝나지 않는 경우뿐이다 — 내 추론이다
```

```text
 attachInvalidationListener (L458-471) 가 불리는 곳은 **L666 하나**다
   (grep "attachInvalidationListener" — 선언 L458 과 호출 L666 뿐)

 주석 L459-463
   "This function is called whenever a prefetch task reads a cache entry. ...
    then we attach that listener to the every cache entry that the task reads."
 ★★ 코드와 어긋난다 — 호출은 **라우트 read-or-create 한 자리**이고,
   붙이는 곳도 항목이 아니라 **모듈 전역 Set 하나**(`invalidationListeners` L390)다.
   L384-389 주석이 "태그·경로 무효화가 없으니 더 잘게 추적할 이유가 없다" 고 적는 쪽이
   실제 구현과 맞다
```

```text
 readOrCreateSegmentCacheEntry(now, map, fetchStrategy, tree)           L868-888

 L876  getFromCacheMap(now, 세그먼트 버전, map, **tree.varyPath**, false, false)
 L884    있으면 => return  (Empty · Pending · Fulfilled · Rejected 무엇이든)
 L887  => return insertEmptySegmentCacheEntry(now, map, fetchStrategy, tree)   L896-907
          varyPathForRequest = getSegmentVaryPathForRequest(fetchStrategy, tree)
          setInCacheMap(map, varyPathForRequest, createDetachedSegmentCacheEntry(now), false)

 ★ `map` 을 인자로 받는다. [프리페치] [01](../../segment-cache/01_entries/README.md)에서 본 대로
   작업이 스케줄될 때 잡아 둔 맵(`PrefetchTask.segmentCacheMap`)이다
 호출처 (grep — SCHED 다섯 곳 L1112 · L1702 · L1854 · L2345 · L2389, cache.ts 없음)
   => 세그먼트 항목을 새로 **만드는** 것은 스케줄러다.
      응답 쓰기 쪽은 insertEmptySegmentCacheEntry 를 직접 부르는 자리가 하나 있다 (L3805, [02])
```

```text
 createDetachedSegmentCacheEntry(now)                                    L1194-1218

   status: Empty · fetchStrategy: **PPR** (L1205, "Default to assuming ... PPR")
   isPartial: true · staleAt: now + 30초 (L1199) · version: **0** (L1215) · ref: null

 ★★ 라우트 쪽은 만들 때 현재 버전을 찍는데(L653), 세그먼트 쪽은 **0** 을 찍는다
 => 버전은 Pending 으로 올릴 때 찍는다 (L1240, 아래)
 => 세그먼트 버전이 한 번이라도 1 이상이 되면, 그 **뒤에 새로 만든** Empty 항목도
    만든 순간부터 `isValueExpired` 가 **이미 만료**로 본다 (0 < current)
      CMAP L265  value.staleAt <= now || value.version < currentCacheVersion
    다음 조회가 그 항목을 지우고 null 을 돌려준다 (CMAP L283-288)
 => 세그먼트 항목의 version 을 찍는 곳은 L1240 하나이고, 모든 fulfill 경로가 upgradeToPendingSegment
    를 거친다(L1275 · L1310 · L2787 · L3816 · L3838 · SCHED). 그래서 드러나는 것은 Empty 로 **남겨 둔**
    항목뿐이다 — 예: SCHED L2345-2365 의 inlining 갈래(InlinedIntoChild)는 readOrCreate 만 하고
    그 자리에서 Pending 으로 올리지 않는다. 다음 읽기가 지우고 새 Empty 를 만든다 — 해 없는 되풀이다. 의도인지는 소스가 적지 않았다
```

```text
 upgradeToPendingSegment(emptyEntry, fetchStrategy)                      L1220-1243

 L1225  status = Pending
 L1226  fetchStrategy = 인자
 L1228  Full 이면 isPartial = false
          주석 L1229-1231 - 응답이 전부를 담을 것이므로, 아직 pending 이어도
            내비게이션 요청에서 이 세그먼트를 **빼도 된다**
 L1240  version = getCurrentSegmentCacheVersion()
          주석 L1235-1239 - "This happens before initiating the request, rather than
            when receiving the response, because it's guaranteed to happen before
            the data is read on the server."

 => 요청 **전에** 버전을 찍는다. 요청이 날아간 사이에 무효화가 일어나면
    응답이 와도 그 항목은 이미 낡은 버전이다
 ★ 이 판단이 응답 쪽에서 실제로 쓰이는 자리 — upsertSegmentEntry L1038 이
   후보가 만료면 **넣지 않는다** ([03])
   다만 주석 L1034-1036 의 TODO 가 한계를 적는다 — "요청 이후 **그 키가** 무효화됐는지"
   는 아직 확인하지 않는다
```

```text
 재검증 칸 — 같은 키 아래 숨은 둘째 자리

 readOrCreateRevalidatingSegmentEntry                                    L909-959
 L943   readRevalidatingSegmentCacheEntry(now, map, tree.varyPath)       L600-614  isRevalidation = true
 L948     있으면 => return
 L954   varyPathForRequest = getSegmentVaryPathForRequest(...)
 L957   setInCacheMap(map, varyPathForRequest, createDetached…, **true**)

 overwriteRevalidatingSegmentCacheEntry                                  L961-978
          읽지 않고 같은 자리에 **덮어쓴다** (L976)

 주석 L923-934 - 재검증을 캐시에 넣는 이유는 **중복 요청을 막기** 위해서다.
   그리고 같은 키의 "정상" 항목을 덮으면 안 되므로 각 자리마다 별도의 재검증 칸이 있다.
   "You can think of it as if all the revalidation entries were stored in a
    separate cache map from the canonical entries, and then transfered to the
    canonical cache map once the request is complete"
 => 실제로는 키 경로 끝에 내부 키 `Revalidation`(CMAP L144)을 하나 더 붙인다 ([03])
 ★ 정상 칸이 비어 있으면 재검증 칸이 아니라 **정상 칸에 바로 넣는다** (CMAP L184-189)

 ★★ 주석 L936-942 의 TODO 는 **낡았다**
   "For now, though, this isn't a concern because the keypath is based solely on
    the prefetch strategy, not on data contained in the response."
   그런데 지금은 응답의 varyParams 로 키를 다시 건다 —
   writeSegmentBundleResponse L2748-2751 · fulfillEntrySpawnedByRuntimePrefetch L3736-3747 ([02]).
   varyParams 플래그는 기본으로 켜져 있다 (config-shared.ts L2174 → define-env.ts L395).
   다만 서버가 varyParams 를 싣는 것은 cacheComponents 렌더뿐이라 TODO 의 전제는 **cacheComponents 에서만** 낡았다
```

```text
 waitForSegmentCacheEntry(pendingEntry)                                  L616-629

 L621  promise 가 없으면 createPromiseWithResolvers 로 **그때 만든다** (L623-624)
 L628  => return promise

 ★ 기다리는 쪽이 있을 때만 약속을 만든다. 없으면 promise 는 null 로 남는다
 => 채우는 쪽(L1500-1504)과 거절하는 쪽(L1526-1531)이 **있을 때만** resolve 하고 null 로 되돌린다
 ★ 거절은 reject 가 아니라 **`resolve(null)`** 이다 (L1529).
   주석 L1527-1528 - 취소 사유는 아직 전달하지 않는다
   => 기다리는 쪽(PPRNAV L1146-1148)은 `entry !== null ? entry.rsc : null` 로 받는다
```

## 결과가 쓰이는 곳

```text
 readSegmentCacheEntryForNavigation 의 반환
      --> PPRNAV L1127 createCacheNodeForSegment. Fulfilled 면 rsc 를 바로,
          Pending 이면 약속을, Empty · Rejected 면 아무것도 쓰지 않는다 (PPRNAV L1133-1169)

 readOrCreate* 의 반환 (Empty 항목)
      --> 스케줄러가 upgradeToPendingSegment 로 올리고 요청을 띄운다.
          [프리페치] [02](../../segment-cache/02_scheduler/README.md)

 Pending 항목의 version
      --> [04]의 isValueExpired 와 [03]의 upsertSegmentEntry L1038 이 본다

 invalidationListeners (전역 Set)
      --> 무효화 함수 셋이 pingInvalidationListeners(L493)로 비운다 ([04])
```

## 다루지 않는 것

`deprecated_requestOptimisticRouteCacheEntry`(L689-811)와 `deprecated_createOptimisticRouteTree`(L813-862), `matchKnownRoute`(optimistic-routes.ts L726)의 패턴 매칭 본문과 `reifyRouteTree`, `attemptToFulfillDynamicSegmentFromBFCache`(L1245) · `attemptToUpgradeSegmentFromBFCache`(L1296)가 BFCache 에서 항목을 채우는 조건, 스케줄러의 호출 다섯 곳(SCHED L1112 · L1702 · L1854 · L2345 · L2389)이 각각 어느 전략으로 부르는지, `blockTaskOnPendingResponse` 와 `blockedTasks` 에 작업을 넣는 쪽, `notifyInvalidationListener`(L473)의 콜백 호출 세부는 이 문서의 범위 밖이다.
