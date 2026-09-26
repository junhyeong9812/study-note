# 03 예측이 틀렸을 때

상위: [가져온 적 없는 라우트 트리를 예측하기까지](../README.md)

[02]의 합성 항목은 "리라이트도 redirect 도 없다" 는 가정 위에 서 있다. 가정이 틀렸다는 것은 **서버 응답이 온 뒤에야** 드러난다. 드러나는 자리는 내비게이션 하나, 프리페치 하나다. 두 곳 모두 같은 두 줄로 끝난다 — 쓴 항목에 `hasDynamicRewrite` 를 세우고, **라우트 캐시 전체를 무효화**한다. 트리를 다시 짓는 재시도 자체는 [PPR 내비게이션] [04](../../ppr-navigation/04_write-back/README.md)가 다룬 경로다.

## 위치

`packages/next` / `src/client/components/router-reducer` / `ppr-navigations.ts` L1711-L1800 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/ppr-navigations.ts#L1711-L1800))

## 실제 코드

내비게이션 쪽 재시도 함수의 앞머리다. 표시하고, 무효화한다.

```ts
// ppr-navigations.ts L1731-L1762
  // If the navigation used a route prediction, mark it as having a dynamic
  // rewrite since it resulted in a mismatch.
  if (routeCacheEntry !== null) {
    markRouteEntryAsDynamicRewrite(routeCacheEntry)
  } else if (seed !== null) {
    // Even without a direct reference to the route cache entry, we can still
    // mark the route as having a dynamic rewrite by traversing the known route
    // tree. This handles cases where the navigation didn't originate from a
    // route prediction, but still needs to mark the pattern.
    const metadataVaryPath = seed.metadataVaryPath
    if (metadataVaryPath !== null) {
      const now = Date.now()
      discoverKnownRoute(
        now,
        retryUrl.pathname,
        retryUrl.search as NormalizedSearch,
        retryNextUrl,
        null,
        seed.routeTree,
        metadataVaryPath,
        false, // couldBeIntercepted - doesn't matter, we're just marking hasDynamicRewrite
        createHrefFromUrl(retryUrl),
        false, // supportsPerSegmentPrefetching - doesn't matter, we're just marking hasDynamicRewrite
        true // hasDynamicRewrite
      )
    }
  }

  // Invalidate all route cache entries. Other entries may have been derived
  // from the template before we knew it had a dynamic rewrite. This also
  // triggers re-prefetching of visible links.
  invalidateRouteCacheEntries(retryNextUrl, baseTree)
```

```text
 ★★★ 표시를 세운 **바로 다음 줄**이 그 표시를 읽을 수 없게 만든다

 L1734  markRouteEntryAsDynamicRewrite(routeCacheEntry)     entry.hasDynamicRewrite = true (SCCACHE L1464)
 L1743  (또는) discoverKnownRoute(..., hasDynamicRewrite = true)   잎의 패턴에 표시
 L1762  invalidateRouteCacheEntries(...)                    currentRouteCacheVersion++ (SCCACHE L435)

 그런데 [02]가 패턴을 읽는 네 자리는 **모두 readPattern 을 먼저 거친다** (OPTR L854 · L905 · L934 · L977)
   readPattern  OPTR L180  isValueExpired(now, 현재 버전, pattern)
                cache-map.ts L265  `value.staleAt <= now || value.version < currentCacheVersion`
 => 방금 표시한 패턴은 version 이 **옛 버전**이므로 다음 읽기에서 만료로 지워진다 (L182 `part.pattern = null`).
    hasDynamicRewrite 검사(L855 · L912 · L924 · L935 · L978)에 닿기 전이다

 표시를 세우는 곳 전수 (packages/next/src grep "hasDynamicRewrite = true" · markRouteEntryAsDynamicRewrite 호출 · discoverKnownRoute 의 마지막 인자 true)
   PPRNAV L1734 · L1743   → L1762 에서 무효화
   SCCACHE L3316          → L3317 에서 무효화
 => 셋 다 표시 직후 버전을 올린다. 표시가 선 채로 **현재 버전**인 패턴이 생기는 길이 없다
    (fulfillRouteCacheEntry 는 다시 채울 때 false 로 되돌린다 — SCCACHE L1415)
 ★ OPTR L249 의 표시는 **닿지 않는다** — 마지막 인자에 true 를 넘기는 유일한 호출(PPRNAV L1754)은
   pendingEntry 로 null 을 넘기고(L1748), pendingEntry 를 넘기는 두 호출(SCCACHE L2130 · L3456)은 false 다
 ★ 캐시 맵 직접 조회(readRouteCacheEntry · getFromCacheMap)는 hasDynamicRewrite 를 아예 보지 않는다 —
   이 표시의 소비자는 트라이 하나다. "모든 라우트 캐시 항목이 사라진다" 는 것도 표시가 아니라
   **버전이 올라간 결과**다
 ※ 그래서 주석이 약속하는 "Future predictions for this route will see the flag and bail out"
   (OPTR L788-792 · SCCACHE L3309-3311)은 **표시가 아니라 무효화로** 이루어진다고 읽힌다 —
   잘못 예측한 패턴 하나가 아니라 **모든 패턴과 모든 라우트 캐시 항목**이 사라진다.
   코드를 따라 내린 결론이고, 실행해 확인하지는 않았다
```

## 동작 흐름

```text
 틀린 예측이 드러나는 자리

 A. 배울 때 걸러진다 (예측이 아니다)                                         [01]
    서버 트리와 URL 이 안 맞으면 패턴으로 저장하지 않는다 — 리라이트 여덟 자리
    => "정적으로" 리라이트되는 URL 은 애초에 템플릿이 되지 않는다
    => 남는 것은 **같은 모양의 URL 인데 값에 따라** 리라이트·redirect 가 갈리는 경우다
       (cache.ts L192-196 "Since rewrite behavior can vary by param value, we can't safely
        predict the route structure for other URLs matching this pattern.")

 B. 내비게이션 — finishNavigationTask  PPRNAV L1554-1660
    fetchMissingDynamicData 가 돌려준 exitStatus 로 가른다 ([PPR 내비게이션] [04])
      SoftRetry      모르는 병렬 슬롯을 받았다(L1957), 또는 다 쓰고도 Pending 이 남았다(L1577)
      RedirectRetry  routeCacheEntry 의 canonicalUrl 과 응답 URL 의 pathname·search 가 다르다 (L1947-1955)
                     ★ 합성 항목의 canonicalUrl 은 **요청한 URL 그대로**다 ([02] L794) —
                       예측으로 간 내비게이션이 redirect 를 만나면 대개 여기로 온다 — 모르는 병렬 라우트면
                       SoftRetry 가 먼저고(L1957-1961), 외부 · MPA redirect 는 문자열이라 HardRetry,
                       pathname · search 가 같으면 재시도가 없다
      HardRetry      fetchServerResponse 가 URL 문자열을 돌려줬다(L1824-1833), 또는 예외(L1983)
    L1602 · L1621 · L1644  **세 갈래 모두** 같은 routeCacheEntry 를 넘겨 dispatchRetryDueToTreeMismatch
    ★★ HardRetry 도 항목을 표시하고 라우트 캐시를 무효화한다 —
       dispatchRetryDueToTreeMismatch 앞머리(L1733-1762)는 isHardRetry 를 보지 않는다
       HardRetry 의 원인은 네트워크 오류만이 아니다 — flight 가 아니거나 2xx 가 아닌 응답(FSR L238) ·
       빌드 ID 불일치(L279) · 문자열 flightData(L284). useOffline 이면 네트워크 오류는 연결을 기다려
       재시도한다(L336-345)
       => 그러나 결과는 사실상 없다 — HardRetry 는 `mpa: true`(L1766 · L1789)로 문서를 통째로 바꾸므로
          트라이 · 캐시 같은 모듈 상태가 사라진다

 C. 프리페치 — fetchSegmentPrefetchesUsingDynamicRequest  SCCACHE L3027-
    L3287  응답을 convertServerPatchToFullTree 로 요청 트리에 붙인다
    L3296  treeDivergedFromBase 이고 요청이 head 만 받는 것이 아니면
    L3316    markRouteEntryAsDynamicRewrite(route)
    L3317    invalidateRouteCacheEntries(key.nextUrl, task.treeAtTimeOfPrefetch)
    L3324    rejectSegmentEntriesIfStillPending(spawnedEntries, -1)   백오프 없이 즉시 만료
    주석 L3313-3315 - "It can't loop: the refetched route entry is built from the server's
      response, so it only mismatches again if the rewrite's behavior changes again."
    ★ 이 검사는 **동적 요청으로 받는 프리페치**(LoadingBoundary · RuntimeShell · PPRRuntime · Full 전략 — 시그니처 L3030-3034) 쪽에만 있다
    ※ 정적 per-segment 프리페치(SCCACHE L2397 부근)가 합성 트리로 요청했다가 어긋나는 경우의 처리는
      읽지 않았다 — [프리페치 작업](../../prefetch-tasks/README.md) · [캐시 항목](../../cache-entries/README.md)
```

```text
 무엇을 표시하는가 — routeCacheEntry 가 있느냐로 갈린다

 routeCacheEntry !== null   (navigateUsingPrefetchedRouteTree 로 온 내비게이션 — SCNAV L450)
   그 항목 자체. 셋 중 하나다
     프리페치로 받은 항목            캐시 맵 안의 항목 = 잎의 패턴일 수 있다 ([01] L716)
     첫 로드·이전 내비게이션으로 배운 항목   〃
     합성 항목                        잎의 패턴 ([02] L809)
   주석 SCNAV L255-258 - "if it came from route prediction"
   ★ 이름과 달리 **예측이 아닌 적중**도 여기로 온다 — 인자 주석(L260-262)은 null 을
     "the route was already fully cached" 라고 하지만, SCNAV L450 은 적중한 항목도 그대로 넘긴다

 routeCacheEntry === null 이고 seed !== null   (캐시 미스 · 새로고침 · 액션 · 재시도 경로)
   L1743  discoverKnownRoute(retryUrl, seed.routeTree, ..., hasDynamicRewrite = true)
     retryUrl = primaryRequestResult.url — **redirect 뒤의** 응답 URL 이다 (L1604 · L1623 · L1646)
     couldBeIntercepted · supportsPerSegmentPrefetching 는 false 로 넘긴다
       주석 L1751 · L1753 "doesn't matter, we're just marking hasDynamicRewrite"
     ※ 잎에 패턴이 없으면 이 호출이 writeRouteIntoCache 로 **새 항목을 캐시에 넣는다**([01] L698).
       그 항목은 L1762 에서 곧바로 옛 버전이 되므로 해가 없어 보인다
     ★ 표시가 실제로 닿는 것은 retryUrl 의 모양이 seed.routeTree 와 맞을 때뿐이다. 전형적인 리라이트는
       [01]의 리라이트 자리 여덟 중 하나를 거쳐 handleMismatchDueToRewrite(OPTR L301-327)로 가고,
       그 함수는 hasDynamicRewrite 를 받지도 쓰지도 않는다 — 표시 없이 캐시에만 넣는다
     ★ redirect 가 원인이면 retryUrl 이 목적지라, 예측한 원래 모양이 아니라 **목적지 모양**의 패턴에 표시가 간다

 seed === null   (HardRetry 의 URL 문자열 · 예외)
   아무것도 표시하지 않는다. 무효화(L1762)는 한다
```

```text
 그다음 — 재시도와 복구 (본문은 [PPR 내비게이션] [04])

 L1766  isHardRetry = isHardRetry || previousNavigationDidMismatch
 L1767  previousNavigationDidMismatch = true
 L1789  retryAction = { type: ACTION_SERVER_PATCH, ..., seed, mpa: isHardRetry, ... }
 L1799  dispatchAppRouterAction(retryAction)
          --> serverPatchReducer → navigateToKnownRoute(..., seed, freshnessPolicy)
              서버가 준 트리를 seed 로 **다시 짓는다** — 예측은 다시 쓰지 않는다
 ★★ 두 번 연속 어긋나면 MPA 로 떨어진다 (PPRNAV 주석 L1411-1413) — 예측이 되풀이돼도
    무한 재시도는 없다
 ★ serverPatchReducer 는 discoverKnownRoute 를 부르지 않는다 (grep 0건) —
   재시도로 받은 트리는 **배우지 않는다**

 ※ 되풀이 비용 — 무효화 뒤 pingVisibleLinks 가 보이는 링크를 다시 프리페치하고, 그 `/_tree` 응답이
   [01]로 패턴을 다시 채운다. 리라이트된 URL 이 보이는 링크였다면 [01]의 리라이트 검사로 **그 URL 만의
   캐시 항목**이 생겨 다음에는 예측을 거치지 않는다. 아니라면 다른 링크로 다시 배운 패턴이
   같은 URL 을 또 예측할 수 있다. 호출 사슬로 추론한 것이다
```

## 결과가 쓰이는 곳

```text
 currentRouteCacheVersion++ (invalidateRouteCacheEntries)
      --> [02]의 readPattern 이 **모든** 잎의 패턴을 만료로 지운다
      --> readRouteCacheEntry 의 캐시 조회(SCCACHE L522)도 옛 항목을 버린다
      --> pingVisibleLinks · pingInvalidationListeners — [프리페치 작업]이 다시 돈다
      ★ 세그먼트 캐시 버전은 올리지 않는다 — 받아 둔 세그먼트 데이터는 남는다
        (invalidateSegmentCacheEntries L448 는 따로다)

 hasDynamicRewrite = true
      --> [02]의 다섯 검사. 위 ★★★ 대로 무효화 뒤에는 읽힐 기회가 없어 보인다
      --> SCCACHE L796 옛 경로가 템플릿의 값을 합성 항목에 옮겨 적는다 (읽지는 않는다)

 ACTION_SERVER_PATCH
      --> [PPR 내비게이션] [04]의 serverPatchReducer
```

## 다루지 않는 것

`finishNavigationTask` · `fetchMissingDynamicData` · `abortRemainingPendingTasks` 의 본문과 `ExitStatus` 우선순위, `serverPatchReducer` 가 `previousTree` 를 비교하는 규칙, `getLastCommittedTree` 와 push/replace 상속([PPR 내비게이션] [04]), `convertServerPatchToFullTree` 가 `treeDivergedFromBase` 를 세우는 조건(SCNAV L907-992), `fetchSegmentPrefetchesUsingDynamicRequest`(SCCACHE L3027-)의 나머지 본문과 `rejectSegmentEntriesIfStillPending`, `pingVisibleLinks` 가 어떤 링크를 다시 프리페치하는지는 이 문서의 범위 밖이다.
