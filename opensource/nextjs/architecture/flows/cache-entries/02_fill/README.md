# 02 채우기와 다시 걸기

상위: [세그먼트 캐시 항목이 만들어지고 채워지고 버려지기까지](../README.md)

응답을 항목에 쓰는 길은 크게 셋이다 — 라우트 트리 응답, 정적 세그먼트 묶음 응답, 동적·런타임 응답. 셋 다 마지막에 같은 두 함수(`fulfillSegmentCacheEntry` · `rejectSegmentCacheEntry`, 라우트는 `fulfillRouteCacheEntry` · `rejectRouteCacheEntry`)로 끝난다. 그리고 채운 뒤 **키를 다시 건다** — 요청할 때 짐작한 키보다 응답이 알려 준 키가 더 정확하기 때문이다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L1380-L1533 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L1380-L1533))

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L2524-L2812 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L2524-L2812))

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L3503-L3860 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L3503-L3860))

## 실제 코드

동적·런타임 응답이 세그먼트를 채울 때 **어느 키로 옮길지** 정하는 부분이다.

```ts
// cache.ts L3719-L3748
  // Decide whether to re-key the entry under a more generic vary path based on
  // which params the segment actually depends on.
  //
  // Skip re-keying for Full prefetches: as of today, `varyParams` tracking only
  // works within the static stage portion of a response. A Full prefetch
  // response covers all stages, and we can't track params during the dynamic
  // stage without dead-locking the Flight stream, so the server-reported set is
  // incomplete and can't be trusted for the full response. Re-keying with an
  // untrustworthy set could replace concrete params with Fallback and let
  // unrelated URLs read each other's content from the cache.
  //
  // For RuntimeShell prefetches, always re-key to the precomputed shell vary
  // path. A shell entry is spawned at a concrete param path but is reusable
  // across all of them; tree.shellVaryPath (root-param values kept, every other
  // param replaced with Fallback) is exactly the path that shell reads look it
  // up under.
  let fulfilledVaryPath: SegmentVaryPath | null = null
  if (process.env.__NEXT_VARY_PARAMS) {
    if (fetchStrategy === FetchStrategy.RuntimeShell) {
      fulfilledVaryPath = tree.shellVaryPath
    } else if (
      fetchStrategy !== FetchStrategy.Full &&
      segmentVaryParams !== null
    ) {
      fulfilledVaryPath = getFulfilledSegmentVaryPath(
        tree.varyPath,
        segmentVaryParams
      )
    }
  }
```

```text
 ★★★ 키를 다시 거는 규칙이 전략마다 다르다

   RuntimeShell                 => tree.shellVaryPath  (루트 파라미터만 남기고 나머지 Fallback)
   Full                         => **다시 걸지 않는다**
   그 밖 + varyParams 가 있으면 => getFulfilledSegmentVaryPath(tree.varyPath, varyParams)
                                   서버가 "이 세그먼트가 읽은 파라미터" 라고 알려 준 것만 남긴다
   varyParams 가 null           => null  (아래에서 요청 때의 키를 쓴다)

 ★★ Full 을 빼는 이유가 주석에 있다 (L3722-3728)
   "varyParams tracking only works within the static stage portion of a response.
    A Full prefetch response covers all stages, and we can't track params during
    the dynamic stage without dead-locking the Flight stream, so the server-reported
    set is incomplete and can't be trusted for the full response. Re-keying with an
    untrustworthy set could replace concrete params with Fallback and let unrelated
    URLs read each other's content from the cache."
 => 불완전한 목록으로 키를 넓히면 **다른 URL 이 이 내용을 읽는다.** 그래서 안 넓힌다

 ★ 전체가 `process.env.__NEXT_VARY_PARAMS` 아래에 있다 (L3736).
   플래그 기본값은 켜짐 — config-shared.ts L2174 `varyParams: true` → define-env.ts L395
   그러나 서버가 varyParams 를 싣는 것은 cacheComponents 렌더뿐이라 **실효는 cacheComponents 에서만**이다
   (cache.ts L3657-3660 주석 "A null iterable means tracking was not enabled")
 ★ varyParams 가 null 인 경우는 vary-params-decoding.ts L91-100 docstring 이 적는다 —
   세그먼트 자신의 목록이나 루트 파라미터 목록 **둘 중 하나라도** 없으면 null("unknown,
   key on all params")이다. 둘 다 있으면 **빈 집합도 권위가 있다**
```

## 동작 흐름

```text
 공통 끝 — 항목의 상태를 바꾸는 네 함수

 fulfillSegmentCacheEntry(entry, rsc, staleAt, isPartial,              L1470-1507
                          isUpgradeableISRFallback, fetchStrategy)
   L1493-1498  status · rsc · staleAt · isPartial · isUpgradeableISRFallback · fetchStrategy 를 덮어쓴다
   L1500       promise 가 있으면 resolve(fulfilledEntry) 하고 null 로
   L1505       pingBlockedTasks
   ★ fetchStrategy 를 **언제나** 덮어쓴다 — 주석 L1480-1489 "The strategy tier describing
     the CONTENT this entry is fulfilled with — which comes from the response, not the tier
     the entry was requested at." 요청 때 전략은 키 결정에만 쓰였다

 rejectSegmentCacheEntry(entry, staleAt)                                L1519-1533
   L1524  status = Rejected, staleAt 만 바꾼다. promise 는 resolve(null)

 fulfillRouteCacheEntry(now, entry, tree, metadataVaryPath, …)          L1380-1418
   L1395  metadata = createMetadataRouteTree(metadataVaryPath)     head 를 가짜 세그먼트로
   L1406  prefetchHints 에 InliningHintsStale 이 있으면 staleAt = **-1** (즉시 만료)
   L1409  그 밖 staleAt = now + STATIC_STALETIME_MS
          주석 L1396-1399 - 라우트 구조는 배포 때만 바뀐다. 예외는 미들웨어의 rewrite/redirect
 rejectRouteCacheEntry(entry, staleAt)                                  L1509-1517

 거절의 staleAt 은 둘이다 (grep "rejectRouteCacheEntry(\|rejectSegmentCacheEntry(\|rejectRemaining\|rejectSegmentEntriesIfStillPending(")
   now + 10초   대부분 — 서버 오류·빈 응답·배포 ID 불일치·형식 이상
   -1           오프라인(`__NEXT_USE_OFFLINE` + checkOfflineError, L2222 · L2288 · L3370)
                동적 rewrite 발견(L3324)
   그리고 SCHED 가 Pending 으로 올리며 넣은 60초는 거절이 아니라 **대기 한도**다 ([01])
```

```text
 1) 라우트 트리 응답 — fetchRouteOnCacheMiss                            L1928-2229

 L2024  응답이 없거나 !ok 이거나 body 가 없으면 => reject(+10초)
 L2063  routeIsPPREnabled = 헤더 `x-nextjs-postponed` === '2' || output: export
 L2070  PPR 이면
 L2074    setSizeInCacheMap(entry, responseSize)                 LRU 크기 ([04])
 L2081    배포 ID 불일치 => reject(+10초)
 L2114    metadataVaryPath 가 없으면 => reject(+10초)
 L2119    discoverKnownRoute(..., entry, ...)
            → optimistic-routes.ts L239 fulfillRouteCacheEntry     **여기서 Fulfilled**
 L2132  PPR 이 아니면
 L2141    setSizeInCacheMap
 L2149    배포 ID 불일치 => reject(+10초)
 L2165    writeDynamicTreeResponseIntoCache(LoadingBoundary, …)      L3379-3486
            안에서 reject 셋(L3408 · L3414 · L3441) 또는 discoverKnownRoute(L3445)
            그리고 트리 응답에 실린 세그먼트 데이터를 writeDynamicRenderResponseIntoCache 로 쓴다
            주석 L3461-3463 - "Tree prefetches should never include segment data. We
              can delete it." — 남은 가지다
 L2185  !couldBeIntercepted 이면
 L2197    getFulfilledRouteVaryPath(..., couldBeIntercepted)          Next-Url 칸 = Fallback
 L2204    setInCacheMap(routeCacheMap, fulfilledVaryPath, entry, false)   ← 다시 걸기
 L2209  catch => 오프라인이면 reject(-1), 아니면 reject(+10초)

 ★★ 다시 걸기가 **upsert 가 아니다.** 주석 L2194-2196 이 스스로 적는다 —
   "TODO: Treat this as an upsert — should check if an entry already exists at the
    new keypath, and if so, whether we should keep that one instead."
 ★ L2185 조건은 couldBeIntercepted 만 본다. 비-PPR 갈래에서 writeDynamicTreeResponseIntoCache 가
   L3408 · L3414 · L3441 로 **거절한 항목도** 그대로 Fallback 키로 옮겨진다.
   (배포 ID 불일치 · metadataVaryPath 없음은 그 전에 return 하므로 옮겨지지 않는다)
   ※ couldBeIntercepted 가 거짓이면 Next-Url 과 무관한 응답이었으므로
     거절도 모든 Next-Url 에 대해 공유되는 것이 맞다고 볼 수 있다 — 내 해석이다
```

```text
 2) 정적 세그먼트 묶음 — writeSegmentBundleResponseVariants              L2524-2600

 응답 하나에 **내용물이 둘** 있을 수 있다 — 전체(serverResponse)와 셸(shellResponse).
 셸은 같은 바이트를 셸 경계에서 잘라 **한 번 더 디코딩**한 것이다 (L2464-2502)
   shellOffset null => 셸 = 전체 (같은 참조)   0 => 셸 없음   양수 => 잘라서 디코딩

 묶음(SegmentBundle)의 항목을 채우는 것은 **그 항목을 띄운 쪽의 내용물**이다

   StaticShell 로 띄웠다  전체 ≠ 셸이면 전체를 **분리 사본**(detachEntriesFromSegmentBundle)에 쓰고
                          셸이 없으면 => rejectRemainingSegmentsInBundle(+10초)
                          셸이 있으면 셸을 원래 묶음에 쓴다
                            기록 전략 = 셸이 곧 전체면 PPR, 아니면 StaticShell (L2571-2573)
   PPR 로 띄웠다          전체를 원래 묶음에 쓰고, 셸이 따로 있으면 셸을 분리 사본에 쓴다

 docstring L2613-2618 - "fulfilling a spawned StaticShell entry with the concrete payload
   would leak param-dependent content into shell positions: during a navigation, a pending
   entry can be rendered as a promise that resolves to its eventual value."
 => 셸 자리의 Pending 항목에 전체 내용을 넣으면, 그것을 약속으로 쥔 내비게이션이
    **다른 파라미터 값의 내용**을 그리게 된다. 그래서 짝을 맞춘다
 ★ 두 번 쓸 때는 **전체를 먼저** 쓴다 (docstring L2516-2517) —
   셸 쓰기의 가림 축출([03])이 방금 쓴 구체 항목을 보게 하려는 것이다
```

```text
 writeSegmentBundleResponse(map, response, size, segments, count, now,  L2623-2812
                            fetchStrategy, payloadFetchStrategy)

 L2642  averageSize = responseSize / segmentCount   묶음의 항목마다 크기를 나눠 준다
 L2680  while (node !== null && dataIndex < data.length)       묶음과 data 배열을 **나란히** 걷는다
 L2687    data 가 null 이거나 node.tree 가 null  (prefetch 가 꺼진 세그먼트)
 L2693      Pending 이면 reject(+10초)   주석 - 서버와 클라이언트 힌트가 어긋나면 작업이 영원히 막히므로
 L2707    entryStaleAt = readFulfilledStaleAt(now, data.staleTime)          ([04])
 L2711    varyParams = readVaryParams(data.varyParams, serverResponse.rootVaryParams)
 L2715    isPartial = readFulfilledIsPartial(data.isPartial)
 L2721    needsRuntimeRequest = 응답이 런타임 데이터를 읽었다 && isPartial
 L2734    recordedFetchStrategy = needsRuntimeRequest 가 거짓이면
            셸이면 RuntimeShell, 아니면 PPRRuntime   ← **요청보다 높은 티어로 기록**
          참이면 fetchStrategy 그대로
 L2748    payloadVaryPath = (__NEXT_VARY_PARAMS && varyParams) ?
                             getFulfilledSegmentVaryPath(...) : getSegmentVaryPathForRequest(payload…)
 L2754    내 Pending 항목이면  fulfill → upsertSegmentEntry(map, payloadVaryPath, 항목, tree.varyPath)
 L2782    아니면              새 분리 항목을 만들어 fulfill → upsertSegmentEntry
 L2809  data 가 모자라면 남은 Pending 을 reject(+10초)

 ★★ isPartial 은 **값이 아니라 "풀렸는가"** 로 읽는다 (L2846-2863)
   서버는 완전 정적 세그먼트에만 그 약속을 풀고 부분 세그먼트는 pending 으로 둔다.
   응답이 전부 버퍼링된 뒤 디코딩되므로 thenable 의 status 를 **동기로** 볼 수 있다
   => 셸 경계에서 자른 디코딩에서는 경계 뒤의 풀림이 안 보인다 → 부분으로 읽힌다
 ★ upsert 로 쓰는 이유 (주석 L2772-2774) — "The upsert (rather than a bare set) applies
   the usual precedence rules, so a concurrent task's more complete response already in
   this slot isn't downgraded."
```

```text
 ★★ 크기 주석과 코드가 어긋난다 (L2638-2641 ↔ L2643-2649 · L2785)

 주석 "(When a response produces two payload writes, each write distributes the
   full response size — intentionally double-charging the LRU for one wire response,
   since it produced two live entries per segment.)"

 코드
   L2645  if (sizeNode.entry !== null) setSizeInCacheMap(sizeNode.entry, averageSize)
   두 쓰기 중 원래 묶음과 짝이 안 맞는 쪽이 **분리 사본**이다 — StaticShell 이면 전체(첫째, L2537-2547),
   PPR 이면 셸(둘째). detachEntriesFromSegmentBundle(L2819-2840)이 entry 를 전부 null 로 만든다
     => 크기 분배 루프가 아무 항목에도 크기를 주지 않는다
   분리 사본의 항목은 L2785 createDetachedSegmentCacheEntry 로 새로 만든다 — size: 0 (L1213)
     그리고 fulfill · upsert 어디에서도 크기를 바꾸지 않는다
     (setSizeInCacheMap 호출은 cache.ts 다섯 곳 L2074 · L2141 · L2646 · L3135 · L3354 뿐)
 => 분리 사본 쪽 항목은 LRU 에 **0 바이트로** 들어간다. "이중 청구" 는 일어나지 않는다
 ★ ISR 재시도에서는 크기를 먼저 원래 묶음 항목에 준 뒤(L2645) 분리 upsert 가 그 항목을 밀어낸다
   (setMapEntryValue → updateLruSize(entry, 0)) — 업그레이드된 항목이 전부 0 바이트가 된다
 ★ 같은 모양이 동적 경로에도 있다 — fetchSegmentPrefetchesUsingDynamicRequest 의 두 번째 쓰기
   (L3215 · L3242)는 spawnedEntries 가 null 이고, 크기 배분(L3135 · L3354)은 띄운 항목에만 한다
 => 크기를 받는 것은 **프리페치 작업이 띄운 항목**뿐이다
 ※ 그 결과 LRU 합계가 실제 메모리보다 작게 잡힌다 — 크기는 내 추론이 아니라 코드이고,
   "메모리보다 작다" 는 rsc 가 실제로 메모리를 차지한다는 전제의 추론이다
```

```text
 ISR 폴백 셸이면 — 재시도 루프                                          L2951-3020

 L2323  응답이 isUpgradeableISRFallback 이고 작업의 fallbackRetryStatus 가 Empty 이면
 L2328    Pending 으로 바꾸고 retryUpgradeableFallbackPrefetch 를 **기다리지 않고** 띄운다
 L2963  최대 MAX_FALLBACK_RETRIES = 3 번 (L2252), FALLBACK_RETRY_DELAY_MS = 2000 간격 (L2248)
 L2987    여전히 폴백이면 continue
 L3002    구체 버전이면 writeSegmentBundleResponseVariants 로 다시 쓰고 Fulfilled, pingPrefetchTask
 L3019  실패하면 Rejected — 이 작업에서는 **다시 돌지 않는다** (docstring L2943-2945)
 ★ 이때 원래 묶음의 항목은 이미 settled 라서 쓰기가 전부 분리 upsert 가 된다 (docstring L2519-2522)
```

```text
 3) 동적·런타임 응답 — writeDynamicRenderResponseIntoCache              L3503-3632

 호출처 (grep 전수 — 여섯 곳)
   cache.ts L3331    fetchSegmentPrefetchesUsingDynamicRequest — **spawnedEntries 를 넘기는 유일한 곳**
   cache.ts L3473    트리 응답의 남은 가지 (위 1)
   cache.ts L4166    writePrerenderResponseIntoCache 가 감싼다 (spawnedEntries = null)
   ppr-navigations.ts L1894 · navigation.ts L616 · create-initial-router-state.ts L216
                     내비게이션·첫 로드의 런타임 프리페치 스트림 (null)
   writePrerenderResponseIntoCache 호출은 ppr-navigations.ts L1865 · navigation.ts L587 ·
     create-initial-router-state.ts L148 · L176 · cache.ts L3215 · L3242
   => [PPR 내비게이션] [04](../../ppr-navigation/04_write-back/README.md)가 호출 쪽을 본 그 경로들이다

 L3526  배포 ID 불일치 => 띄운 항목을 reject(+10초) 하고 null
 L3541  flightData 마다
 L3551    segmentPath 를 따라 routeTree 의 slots 를 내려간다
 L3558      못 찾으면 => reject(+10초) 하고 null
 L3566    writeSeedDataIntoCache(…)                                     L3634-3698
            isPartial = rsc === null || isResponsePartial              (L3656)
            varyParams = readVaryParams(seedData[4], root)             (L3661)
            fulfillEntrySpawnedByRuntimePrefetch(…) 후 slots 를 재귀
 L3581    head 가 있으면 fulfillEntrySpawnedByRuntimePrefetch(…, metadataTree)
            ★ cacheComponents 면 서버의 isHeadPartial 을 **무시**하고 isResponsePartial 을 쓴다
              주석 L3583-3593 - 서버 값이 직렬화 전에 계산돼 정적 PPR 페이지에는 늘 true,
                런타임 응답에는 틀리게 false 가 된다
 L3624  띄운 항목 중 아직 Pending 인 것은 reject(+10초)
          주석 L3616-3618 - "intentionally not rendered by the server, because it was
            inside the loading boundary"
        => return 채워진 항목 목록 (L3354 이 그 목록에 크기를 나눠 준다)
```

```text
 fulfillEntrySpawnedByRuntimePrefetch — 내 것이냐 아니냐                  L3700-3860

 L3753  ownedEntry = spawnedEntries?.get(tree.requestKey)
 L3757  내 것이면
 L3758    fulfillSegmentCacheEntry(ownedEntry, …)
 L3776    canonicalVaryPath = fulfilledVaryPath ?? (Full 이 아니면 요청 때의 키 : null)
 L3784    setInCacheMap(map, canonicalVaryPath, 항목, false)         ← **bare set**
 L3792    evictShadowingSegmentEntries(now, map, tree.varyPath, 항목)   ([03])
          주석 L3769-3772 - 재검증으로 띄운 항목은 이 다시 걸기가 없으면
            "they'd stay in their Revalidation slot forever, invisible to canonical reads"
 L3794  아니면
 L3796    getFromCacheMap(…, tree.varyPath)   구체 키로 읽는다
 L3804    없으면 insertEmptySegmentCacheEntry 로 만든다
 L3812    Empty 면 **그 빈 항목을 차지해** 채운다. fulfilledVaryPath 가 있으면 set + 가림 축출
 L3834    그 밖이면 새 분리 항목을 만들어 upsertSegmentEntry(…, tree.varyPath)

 주석 L3750-3752 - "We must never write over an entry that was created by a different
   task, because that causes data races."
 ★★ 그런데 내 항목을 옮기는 L3784 는 upsert 가 아니라 **bare set** 이다.
   옮겨 갈 자리(canonicalVaryPath)에 다른 작업의 항목이 있으면 우선순위 비교 없이 **덮는다**
   (setMapEntryValue CMAP L392-398 이 기존 값의 ref 를 끊는다)
 => 정적 묶음 쪽(L2775)은 같은 상황에서 upsert 를 쓰고 그 이유를 주석으로 남겼다 (위 2)
 ※ 두 경로의 차이가 의도인지는 소스가 적지 않았다. 덮인 쪽이 Pending 이어도
   그 항목을 띄운 요청이 끝나면 자기 blockedTasks 를 깨우므로 작업이 멈추지는 않는다 —
   덮어쓰기의 손해는 "더 완전한 항목이 덜 완전한 항목에 밀릴 수 있다" 쪽이다. 내 추론이다
```

```text
 ★★ writePrerenderResponseIntoCache 의 docstring 이 본문과 어긋난다 (L4127-4132)

   "Writes a prerender response into the segment cache at the vary path
    determined by `fetchStrategy`. Default segments are skipped (by
    `writeSeedDataIntoCache`) to avoid caching fallback content that would
    block refreshes from overwriting with dynamic data."

 writeSeedDataIntoCache(L3634-3698) 본문에는 default 세그먼트를 거르는 코드가 **없다**.
   rsc 를 읽고(L3655), varyParams 를 읽고(L3661), 채우고(L3662), slots 를 재귀할(L3677-3697) 뿐이다
 cache.ts 전체에서 default 를 언급하는 곳은 이 docstring 한 줄이다
   (grep "DEFAULT_SEGMENT\|__DEFAULT__\|isDefault\|default segment\|Default segment" — L4129 하나)
 ※ 거르는 일이 다른 곳(서버 응답이 default 를 안 싣는 등)에서 일어날 수는 있다.
   navigation.ts 의 DEFAULT_SEGMENT_KEY 사용 셋(L1019 · L1047 · L1077)은 트리 어긋남 판정이지
   쓰기 거르기가 아니다. 서버 쪽은 확인하지 않았다
```

```text
 예측이 틀렸을 때 (L3296-3326)

 navigationSeed.treeDivergedFromBase 이면
 L3316  markRouteEntryAsDynamicRewrite(route)      hasDynamicRewrite = true (L1461-1468)
 L3317  invalidateRouteCacheEntries(…)            라우트 버전을 올린다 ([04])
 L3324  띄운 항목을 reject(**-1**)                 즉시 만료 — 다음 패스가 다시 요청한다
 => 예측 템플릿에 표시를 남겨, 같은 패턴으로 다시 예측하지 않게 한다
    (optimistic-routes.ts 가 이 플래그를 보고 서버에 묻는다 — 그 본문은 범위 밖)
```

## 결과가 쓰이는 곳

```text
 Fulfilled 항목의 fetchStrategy (기록 티어)
      --> 스케줄러의 wouldRuntimeRequestProvideMore(SCHED L1210-1218)가
          canNewFetchStrategyProvideMoreContent 로 "런타임 요청이 더 줄까" 를 묻는다
          [프리페치] [01](../../segment-cache/01_entries/README.md)

 다시 건 키 (Fallback 이 섞인 vary path)
      --> 다른 파라미터 값의 읽기가 이 항목을 찾는다 ([03]의 Fallback 탐색)

 promise 의 resolve / resolve(null)
      --> 기다리던 내비게이션(PPRNAV L1145)이 rsc 를 받거나 null 을 받는다

 pingBlockedTasks
      --> 막혀 있던 프리페치 작업이 다시 돈다 (pingPrefetchTask)

 setSizeInCacheMap 이 준 크기
      --> [04]의 LRU 합계
```

## 다루지 않는 것

`fetchSegmentsOnCacheMissImpl`(L2363-2510)의 요청 헤더·셸 오프셋 디코딩(`decodeBufferedStage`), `fetchSegmentPrefetchesUsingDynamicRequest`(L3027-3377)의 단계 분리(`resolveShellStageData`)와 RuntimeShell/PPRRuntime 에 따른 두 번 쓰기 갈래(L3163-3257), `processRuntimePrefetchStream`(L4187) · `stripIsPartialByte`(L4251), `convertServerPatchToFullTree`(SCNAV L907)가 navigationSeed 를 만드는 과정, `discoverKnownRoute`(optimistic-routes.ts L220)의 패턴 학습과 `handleMismatchDueToRewrite`, `drainVaryParams` 의 디코딩, 서버가 `varyParams` · `isPartial` · `needsRuntimeRequest` · 셸 오프셋 `a` 를 싣는 쪽(`collect-segment-data.tsx`), `attemptToFulfillDynamicSegmentFromBFCache`(L1245) · `attemptToUpgradeSegmentFromBFCache`(L1296)의 BFCache 채우기는 이 문서의 범위 밖이다.
