# 02 세그먼트 하나를 채우기

상위: [내비게이션이 서버 응답을 트리에 합치기까지](../README.md)

`createCacheNodeForSegment` 는 CacheNode **하나**를 만든다. 데이터를 가져올 곳이 넷이다 — BFCache, 세그먼트 캐시(프리페치), 이미 받은 서버 응답(seed), 그리고 "나중에 올 것" 의 약속. 어느 것을 먼저 보는지가 `FreshnessPolicy` 로 갈린다. [프리페치] [03](../../segment-cache/03_navigate/README.md)이 범위 밖으로 둔 여섯 값의 동작이 여기서 풀린다.

## 위치

`packages/next` / `src/client/components/router-reducer` / `ppr-navigations.ts` L969-L1344 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/ppr-navigations.ts#L969-L1344))

## 실제 코드

하이드레이션 갈래가 가장 단호하다.

```ts
// ppr-navigations.ts L1030-L1081
    case FreshnessPolicy.Hydration: {
      // This is not related to the BFCache but it is a special case.
      //
      // We should never spawn network requests during hydration. We must treat
      // the initial payload as authoritative, because the initial page load is
      // used as a last-ditch mechanism for recovering the app.
      //
      // This is also an important safety check because if this leaks into the
      // server rendering path (which theoretically it never should because the
      // server payload should be consistent), the server would hang because these
      // promises would never resolve.
      //
      // TODO: There is an existing case where the global "not found" boundary
      // triggers this path. But it does render correctly despite that. That's an
      // unusual render path so it's not surprising, but we should look into
      // modeling it in a more consistent way. See also the /_notFound special
      // case in updateCacheNodeOnNavigation.
      const rsc = seedRsc
      const prefetchRsc = null
      const head = isPage ? seedHead : null
      const prefetchHead = null
      writeToBFCache(
        now,
        tree.varyPath,
        rsc,
        prefetchRsc,
        head,
        prefetchHead,
        dynamicStaleAt,
        bfcacheId
      )
      if (isPage && metadataVaryPath !== null) {
        writeHeadToBFCache(
          now,
          metadataVaryPath,
          head,
          prefetchHead,
          dynamicStaleAt,
          bfcacheId
        )
      }
      return {
        cacheNode: createCacheNode(
          rsc,
          prefetchRsc,
          head,
          prefetchHead,
          bfcacheId
        ),
        needsDynamicRequest: false,
      }
    }
```

```text
 ★★★ 하이드레이션에서는 **네트워크 요청을 절대 만들지 않는다**

 주석 L1033-1035 - "We must treat the initial payload as authoritative, because the
   initial page load is used as a last-ditch mechanism for recovering the app."
 주석 L1037-1040 - 이 경로가 서버 렌더링으로 새면 "the server would hang because
   these promises would never resolve."

 => HTML 에 실려 온 seed 가 **정답**이다. 세그먼트 캐시도 BFCache 도 읽지 않는다
 => needsDynamicRequest 는 언제나 false (L1079)
 ★★ 복구 수단이 이 첫 로드다 — [04]의 재시도가 두 번 연속 실패하면 MPA 로 떨어지는데,
   그 MPA 가 다시 이 갈래로 온다. 여기서 요청을 또 만들면 복구가 순환한다
   (※ "순환" 은 주석의 "last-ditch" 를 내가 풀어 쓴 것이다)
 ★ 그래도 BFCache 에는 **쓴다** (L1051-1070). 첫 화면에서 뒤로 갔다 다시 오면 이것을 읽는다
 ★ 주석 L1042-1046 이 예외 하나를 자백한다 — 전역 "not found" 경계가 이 경로를 탄다.
   "it does render correctly despite that"
```

## 동작 흐름

```text
 createCacheNodeForSegment  PPRNAV L969-1344 (376줄)

 L1002  switch (freshness)                         ← 캐시보다 먼저 보는 곳
 L1003    Default          readFromBFCacheDuringRegularNavigation(now, varyPath)
 L1017                       있으면 => return { 캐시 값 + **호출자가 준** bfcacheId, needsDynamicRequest: false }
 L1030    Hydration        (위 실제 코드) => return  언제나
 L1082    HistoryTraversal readFromBFCache(varyPath)   ← now 대신 -1 로 신선도 검사를 끈다 (bfcache.ts L173-176)
 L1102                       있으면 => return { 캐시 값 + **항목에 저장된** bfcacheId, ... false }
 L1114    RefreshAll · HMRRefresh · Gesture    BFCache 를 안 본다

 L1127  segmentEntry = readSegmentCacheEntryForNavigation(now, map, varyPath, restrictToShell)
 L1135    Fulfilled   cachedRsc = entry.rsc,  isCachedRscPartial = entry.isPartial
 L1141    Pending     cachedRsc = waitForSegmentCacheEntry(...).then(e => e?.rsc)   약속을 그대로 쓴다
 L1162    Empty · Rejected    아무것도 없음 (isCachedRscPartial 초깃값 true, L1125)

 L1187  seed 있음 × 부분/완전,  seed 없음 × 부분/완전   → 네 갈래
        ([클라이언트 트리] [03]이 표로 정리했다. 여기서는 되풀이하지 않는다)
 L1212    seed 없음 + 부분이면  rsc = createDeferredRsc()   ← **나중에 [04]가 푼다**
 L1218    doesSegmentNeedDynamicRequest = isCachedRscPartial   (seed 가 있으면 false, L1202)

 L1231  페이지 세그먼트면 head 도 **똑같이** 한다 (메타데이터 varyPath 로 세그먼트 캐시를 한 번 더 읽는다)
 L1313  Gesture 가 아니면  writeToBFCache(...)  (+ 페이지면 writeHeadToBFCache)
 L1336  => return { cacheNode, needsDynamicRequest: 세그먼트 || head }
```

```text
 ★★★ FreshnessPolicy 여섯 값 × 판단하는 일곱 자리 (PPRNAV 전체)

                  L360     L524      L648     L1002          L1313    L1375   L1821
                  데이터    default   스크롤   BFCache 먼저?   BFCache  새       HMR
                  새로?    슬롯 재사용 표시                     쓰기     bfcacheId 헤더
 Default          -        O         O        정규 읽기       O        ++n     -
 Hydration        -        O         X        seed 가 정답    O        0       -
 HistoryTraversal -        **X**     X        신선도 무시 읽기 O        ++n     -
 RefreshAll       **O**    O         O        안 봄           O        ++n     -
 HMRRefresh       **O**    O         O        안 봄           O        ++n     O
 Gesture          -        O         O        안 봄           **X**    ++n     -

 (L524 는 01 의 default 슬롯 갈래, L648 은 accumulateScrollRef, L1375 는 generateBFCacheId,
  L1821 은 [04]의 fetchServerResponse 호출. 그리고 SCNAV L372 가 Gesture 면
  **요청 자체를 안 보낸다** — 여덟째 자리다)

 => Gesture 는 **알려진 라우트로 갈 때** "보여 주기만 하고 남기지 않는" 정책이다 —
    BFCache 에 안 쓰고(주석 L1311-1312 "they are transient and will be replaced by the
    canonical navigation") 동적 요청도 안 보낸다
 ★ 모르는 라우트로 가면 다르다 — navigateToUnknownRoute 가 현재 트리로 서버에 묻고(SCNAV L497-513)
   라우트 학습·세그먼트 캐시 쓰기도 남긴다(L557-635). app-router-instance.ts L359-365 의 TODO 가
   "this will still end up performing a dynamic request" 라고 인정한다
 => HistoryTraversal 은 "되돌리기" 다 — 신선도를 무시하고 BFCache 를 읽고,
    default 슬롯도 기록된 그대로 두고, 스크롤도 건드리지 않는다
 => RefreshAll · HMRRefresh 는 [01]의 재사용 갈래를 끈다 (L389-391).
    그래서 **겹치는 레이아웃까지** 이 함수로 와서 다시 채워진다
 ★ 새 bfcacheId 가 "++n" 인 자리도 [01]의 재사용 갈래에서는 **이전 값을 물려받는다** (L418-420)
```

```text
 ★★★ 기본 설정에서 Default 의 BFCache 읽기는 **거의 언제나 빗나간다**

 주석 L1004-1007 - "The entry's staleAt determines whether it's still fresh. This is
   used when staleTimes.dynamic is configured globally or when a page exports
   unstable_dynamicStaleTime for per-page control."

 staleAt 을 정하는 식 (bfcache.ts L15-22 computeDynamicStaleAt)
   서버가 `d` 를 보냈으면  now + d * 1000
   아니면                  now + DYNAMIC_STALETIME_MS
 DYNAMIC_STALETIME_MS 의 기본값은 **0초**다 (config-shared.ts L2229-2231 `staleTimes.dynamic: 0`
   → define-env.ts L234-238. [클라이언트 라우터] [02]가 같은 상수를 다뤘다)
 만료 판정은 `value.staleAt <= now` (cache-map.ts L260-266)

 => staleTimes.dynamic 도 unstable_dynamicStaleTime 도 없으면 staleAt = 쓴 시각이고,
    **다음 내비게이션의 now 는 그보다 늦다** — 만료로 지워지고(cache-map.ts L283-288) null 이다
 => 그래서 기본 설정의 현행 경로는 L1003 을 **통과해** 세그먼트 캐시(L1127)로 간다
 ★ HistoryTraversal 은 now = -1 로 읽어 이 검사를 피한다. 뒤로 가기는 신선도와 무관하게 BFCache 를 쓴다
   단 버전 검사는 남는다 — `router.refresh()`(refresh-reducer L51) · 재검증 액션(server-action-reducer
   L350)이 invalidateBfCache 로 버전을 올리면 뒤로 가기에서도 못 찾는다 (cache-map.ts L260-266). LRU 축출도 있다
 ※ "거의" — 같은 밀리초 안에 다시 내비게이션하는 경우는 따지지 않았다
```

```text
 ★★ BFCache 적중일 때 bfcacheId 를 **어디서 가져오는가**가 두 갈래로 다르다

 Default (L1013-1016) - "A regular navigation that happens to read cached data is still a
   fresh navigation, so we use the caller-supplied bfcacheId — the BFCacheEntry's id is
   only restored on history-traversal navigations."
 HistoryTraversal (L1099-1101) - "Restore the bfcacheId from the cached entry so that
   back/forward navigations preserve the original id, regardless of whether
   `cacheComponents` Activity preservation is enabled."

 => 같은 캐시 값을 읽어도 앞으로 가면 **새 정체성**, 뒤로 가면 **옛 정체성**이다
 => bfcacheId 는 `useRouter().bfcacheId` 로 사용자 코드에 보인다 (주석 L1365-1367)
 ★ generateBFCacheId (L1370-1377) — 서버(`typeof window === 'undefined'`)와 Hydration 은 **0** 이다.
   주석 L1371-1373 "so they reconcile cleanly across hydration"
```

```text
 ★★ 뒤로 가기에서 prefetchRsc 를 **버리는** 조건 (L1085-1098)

   oldRscDidResolve = !isDeferredRsc(oldRsc) || oldRsc.status !== 'pending'
   dropPrefetchRsc  = oldRscDidResolve

 주석 L1085-1087 - "Only show prefetched data if the dynamic data is still pending. This
   avoids a flash back to the prefetch state in a case where it's highly likely to have
   already streamed in."
 주석 L1089-1094 - 엄밀히는 "네트워크 응답을 받았는가" 만 본다. 스트리밍이라 전부 왔다는
   뜻은 아니지만 "we assume that the rest dynamic data will stream in quickly"

 => 동적 데이터가 이미 왔으면 프리페치 조각을 **건너뛰고** 최종 rsc 로 곧장 그린다.
    [클라이언트 트리] [03]의 useDeferredValue 가 "먼저 prefetchRsc" 를 하지 않게 하는 방법이다
```

```text
 ★★ DeferredRsc 는 Promise 에 **꼬리표**를 붙인 것이다 (L2240-2334)

 L2240  const DEFERRED = Symbol()
 L2281  createDeferredRsc() — new Promise 에 status · resolve · reject · tag · _debugInfo 를 붙인다
 L2306    resolve 는 status === 'pending' 일 때만 효과가 있다  → **두 번째 resolve 는 무시**
 L2277  isDeferredRsc(v) = v && typeof v === 'object' && v.tag === DEFERRED

 주석 L2273-2276 - Flight 약속과 구별하려는 것이다. "It's a compromise to avoid adding an
   extra field on every Cache Node, which would be awkward because the pre-PPR parts of
   codebase would need to account for it, too."
 => 세그먼트 캐시의 Pending 약속(L1146)은 DeferredRsc 가 **아니다** — 그냥 .then() 이다.
    그래서 [04]가 푸는 것은 L1212 · L1298 에서 만든 것뿐이다
 ★ status 를 직접 달아 두는 것은 React 의 use() 가 읽는 thenable 규약이다
   ※ React 쪽 규약은 이 저장소 밖이라 확인하지 않았다
```

```text
 ★ head 에 임시 우회가 하나 있다 (L1267-1284)

 `__NEXT_OPTIMISTIC_ROUTING` 이고 캐시된 head 가 부분이면  cachedHead = ''
 주석 - 뷰포트가 풀리기를 기다리며 막지 않으려는 **임시** 우회다. "will be fixed before stable".
   App Router 는 null 을 "그릴 head 없음" 으로, 빈 문자열을 "빈 head" 로 다룬다 (L1280-1282)
 ★ 이 플래그는 **기본 켜짐**이다 — config-shared.ts L2175 `optimisticRouting: true` → define-env.ts L391-392.
   그래서 이 우회는 기본 설정의 현행 경로다 ([프리페치] [03]의 L182 갈래와 같은 플래그)
```

## 결과가 쓰이는 곳

```text
 { cacheNode, needsDynamicRequest }
      --> [01]의 updateCacheNodeOnNavigation(L407) · createCacheNodeOnNavigation(L701)
          needsDynamicRequest 가 NavigationTask.status(Pending) 와 요청 트리의 refetch 표시가 된다

 cacheNode.rsc = DeferredRsc
      --> [04] finishPendingCacheNode 가 서버 데이터로 resolve,
          abortPendingCacheNode 가 null 로 resolve 한다
      --> [클라이언트 트리] [03] InnerLayoutRouter 가 isDeferredRsc 로 알아보고 use() 한다

 writeToBFCache · writeHeadToBFCache
      --> 다음 HistoryTraversal 이 L1083 에서 읽는다
      --> [04] 가 응답을 받으면 updateBFCacheEntryStaleAt 으로 staleAt 을 고친다
```

## 다루지 않는 것

`readSegmentCacheEntryForNavigation`(segment-cache/cache.ts)이 varyPath 로 항목을 고르는 규칙과 `waitForSegmentCacheEntry`, `bfcache.ts` 의 저장 구조(`bfcacheMap` · `currentBfCacheVersion` · `invalidateBfCache`)와 `writeToBFCache`(L70) · `writeHeadToBFCache`(L116) 본문, `getFromCacheMap` 의 폴백 탐색과 LRU, `restrictToShell` 과 Instant Navigation Testing API, `__NEXT_OPTIMISTIC_ROUTING` 이 켜진 경로 전체, seed × 부분/완전 네 갈래의 표([클라이언트 트리] [03](../../client-components/03_layout-router/README.md)), React `use()` 가 thenable 의 `status` 를 읽는 방식은 이 문서의 범위 밖이다.
