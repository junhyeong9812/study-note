# 03 내비게이션

상위: [프리페치가 쌓이고 내비게이션이 그것을 쓰기까지](../README.md)

`navigate` 는 1278줄 파일의 진입이다. **캐시에 맞는 프리페치가 있으면 동기로 끝낸다.** 없으면 Promise 를 돌려주는데, 그때 하는 일이 예전 구현과 다르다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `navigation.ts` L60-L79 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/navigation.ts#L60-L79))

## 실제 코드

docstring 이 계약을 명시한다.

```ts
// navigation.ts L60-L67
/**
 * Navigate to a new URL, using the Segment Cache to construct a response.
 *
 * To allow for synchronous navigations whenever possible, this is not an async
 * function. It returns a promise only if there's no matching prefetch in
 * the cache. Otherwise it returns an immediate result and uses Suspense/RSC to
 * stream in any missing data.
 */
```

시그니처는 이렇다 (L68-79).

```text
 export function navigate(
   state, url, currentUrl, currentRenderedSearch,
   currentCacheNode, currentFlightRouterState, nextUrl,
   freshnessPolicy, scrollBehavior, navigateType
 ): AppRouterState | Promise<AppRouterState> {      ← L79
```

```text
 "To allow for synchronous navigations whenever possible, this is not an async
  function. It returns a promise only if there's no matching prefetch in
  the cache. Otherwise it returns an immediate result and uses Suspense/RSC to
  stream in any missing data."

 => 반환형이 `AppRouterState | Promise<AppRouterState>` 다
 => [클라이언트 라우터]에서 본 `ReducerState` 가 Promise 유니온인 근원이 여기다.
    **async 함수로 만들지 않은 것이 의도**다 — async 면 언제나 Promise 가 된다
 ★ 캐시에 있으면 "즉시 결과" 를 주고, 빠진 데이터는 Suspense/RSC 로 흘려 넣는다
```

## 동작 흐름

```text
 navigate  SCNAV L68-

 L80   navigationLock = null
 L88   __NEXT_EXPOSE_TESTING_API 이면
 L89     const { isNavigationLocked } =
 L90       require('./navigation-testing-lock') as typeof import(...) 로 확인한다
 L97     => return ensurePrefetchThenNavigate(...)
          주석 L82-87 - 잠금이 켜져 있으면 내비게이션 전에 프리페치 작업이
            시작됐음을 보장한다. 그래야 셸이 불완전해지지 않는다
 L113  => return navigateImpl(...)

 navigateImpl (L130-234) 의 출구가 **셋**이다

 L150  route = readRouteCacheEntry(...) 가 Fulfilled 면
 L153    => return navigateUsingPrefetchedRouteTree(..., route, ...)

 L182  `!__NEXT_OPTIMISTIC_ROUTING` 이고 route 가 Rejected 가 아니면
 L184    optimisticRoute = deprecated_requestOptimisticRouteCacheEntry(now, url, nextUrl)
 L191    비어 있지 않으면 => return navigateUsingPrefetchedRouteTree(..., optimisticRoute, ...)
        주석 L171-181 - 검색 파라미터 기반의 낡은 매칭이다. 새 optimisticRouting
          플래그가 꺼져 있을 때만 쓴다. **Rejected 는 제외** — 검색 파라미터에
          걸린 rewrite/redirect 때문에 거절됐을 수 있어서다
   ★★ 캐시에 아무것도 없어도 여기서 **동기로** 끝날 수 있다

 L216  그 밖 => return navigateToUnknownRoute(...).catch(() => state)   L230-233
   ★ 실패하면 **현재 상태를 그대로 돌려준다.** 예외가 리듀서로 새지 않는다
```

```text
 ★★★ 캐시 미스 때 하는 일이 **예전 구현과 반대**다
     — 위 셋째 출구 `navigateToUnknownRoute` 의 docstring 이다 (L483-493)

 주석 원문
   "Runs when a navigation happens but there's no cached prefetch we can use.
    Don't bother to wait for a prefetch response; go straight to a full
    navigation that contains both static and dynamic data in a single stream.
    (This is unlike the old navigation implementation, which instead blocks
    the dynamic request until a prefetch request is received.)

    To avoid duplication of logic, we're going to pretend that the tree
    returned by the dynamic request is, in fact, a prefetch tree. Then we can
    use the same server response to write the actual data into the CacheNode
    tree. So it's the same flow as the 'happy path' (prefetch, then
    navigation), except we use a single server response for both stages."
   (원문의 "happy path" 는 큰따옴표다)

 => 예전 구현  프리페치 응답을 받을 때까지 **동적 요청을 막았다**
    지금        프리페치를 기다리지 않고 **정적+동적을 한 스트림으로** 곧장 받는다
 => 그리고 로직 중복을 피하려고 **동적 요청의 트리를 프리페치 트리인 척** 다룬다.
    그래서 캐시 히트와 미스가 **같은 흐름**을 탄다 — 응답이 하나냐 둘이냐만 다르다
```

```text
 ★★ 테스트 API 가 켜져 있으면 갈래가 하나 더 생긴다 (L88-97)

   if (process.env.__NEXT_EXPOSE_TESTING_API) {          L88
     const { isNavigationLocked } =                     L89
       require('./navigation-testing-lock') as typeof import('./navigation-testing-lock')   L90
     ...
     return ensurePrefetchThenNavigate(...)             L97
   }

 주석 L82-87 - 잠금이 켜져 있으면 **프리페치 작업이 시작됐음을 보장한다.**
   그래야 세그먼트 데이터 요청이 최소한 pending 상태가 된다.
   이것이 없으면 이미 라우트 트리가 캐시된 경로에서
   일부 세그먼트가 아예 요청되지 않아 셸이 불완전할 수 있다

 ★ 빌드타임 플래그라 프로덕션 번들에서는 이 갈래와 require 가 함께 사라진다
   ([클라이언트 라우터] [01]의 HMR 리듀서와 같은 수법이다)
 ★ 여기서도 `navigation-testing-lock.disabled.ts`(68줄)라는 짝이 있다 —
   비활성 판을 따로 둔 것으로 보인다
   (※ 뒷문장은 내 관찰이다. 어느 쪽이 언제 쓰이는지는 확인하지 않았다)
```

```text
 ★ FreshnessPolicy 가 갈림을 하나 더 만든다 (L502 부근)

 L502  case FreshnessPolicy.Hydration:   // <- shouldn't happen during client nav
 => 주석이 "클라이언트 내비게이션 중에는 일어나면 안 된다" 고 적는다.
    그런데 case 는 있다
 ★ [클라이언트 라우터] [02]의 navigate-reducer 는 언제나
   `FreshnessPolicy.Default` 를 넘긴다. Hydration 은 다른 경로가 쓴다
```

## 결과가 쓰이는 곳

```text
 AppRouterState (동기 반환)
      --> [클라이언트 라우터] [02]의 navigate-reducer 가 그대로 돌려준다.
          리듀서가 동기로 끝나는 경우다. 출구 둘(L153 · L191)이 여기다
      ★ 동기로 끝나도 **서버 요청이 없는 것은 아니다** —
        두 출구가 거쳐 가는 navigateToKnownRoute(L236) 안의 L371-384 가 `freshnessPolicy !== Gesture` 이면
        `spawnDynamicRequests(...)` 를 부르고 **기다리지 않는다**

 Promise<AppRouterState> (캐시 미스)
      --> 같은 자리지만 Promise 다. 액션 큐가 await 해야 한다
      --> [클라이언트 라우터]가 "상태 기계로 다시 쓰겠다" 고 한 이유의 절반

 CacheNode 트리
      --> 응답 데이터가 여기 써진다. 캐시 히트든 미스든 같은 경로다
          (미스는 동적 응답의 트리를 프리페치 트리처럼 다룬다)

 navigationLock
      --> 테스트 API 전용. 프리페치가 시작됐음을 보장하는 장치
```

## 다루지 않는 것

`navigateUsingPrefetchedRouteTree`(L153 · L191 이 부르는 것) · `completeHardNavigation`(L680 부근) · `navigateToUnknownRoute` · `spawnDynamicRequests`(L373) · `completeSoftNavigation`(L386) 의 본문, `deprecated_requestOptimisticRouteCacheEntry`(cache.ts L689)의 검색 파라미터 매칭과 `__NEXT_OPTIMISTIC_ROUTING` 이 켜진 쪽의 경로, L483 이후의 캐시 미스 처리 전체와 `CacheNode` 트리에 데이터를 쓰는 과정, `FreshnessPolicy` 여섯 값(`Default` · `Hydration` · `HistoryTraversal` · `RefreshAll` · `HMRRefresh` · `Gesture`)의 각 동작과 `ppr-navigations.ts`(2383줄), `navigation-testing-lock.ts`(553줄) / `.disabled.ts`(68줄)와 Instant Navigation Testing API, `optimistic-routes.ts`(1119줄)의 라우트 예측, 스크롤 처리(`scrollBehavior`)와 `pushRef.mpaNavigation`, `bfcache.ts`(201줄)의 뒤로/앞으로 복원은 이 문서의 범위 밖이다.
