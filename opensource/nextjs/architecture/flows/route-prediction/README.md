# 가져온 적 없는 라우트 트리를 예측하기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[프리페치] [03](../segment-cache/03_navigate/README.md)은 `navigateImpl` 의 첫 출구를 "라우트 캐시에 Fulfilled 항목이 있으면" 이라고 적었다. 그런데 그 항목이 **서버에서 받은 적 없는 것**일 수 있다. `readRouteCacheEntry` 는 캐시가 비어 있으면 `/blog/post-1` 에서 배운 모양으로 `/blog/post-2` 의 라우트 트리를 **지어서** 돌려준다. 이 흐름은 그 예측을 배우고(01), 맞추고(02), 틀렸을 때 되돌리는(03) 코드와, 같은 디렉터리에 붙은 테스트 전용 잠금(04)을 다룬다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `OPTR` = `client/components/segment-cache/optimistic-routes.ts`(1119줄), `NTLOCK` = `.../navigation-testing-lock.ts`(553줄), `NTLOCKOFF` = `.../navigation-testing-lock.disabled.ts`(68줄), `SCCACHE` = `.../cache.ts`, `SCNAV` = `.../navigation.ts`, `PPRNAV` = `client/components/router-reducer/ppr-navigations.ts`, `APPRT` = `build/templates/app-page-runtime.ts`(2245줄).

이어지는 흐름: [프리페치](../segment-cache/README.md) · [PPR 내비게이션](../ppr-navigation/README.md) · [캐시 항목](../cache-entries/README.md) · [프리페치 작업](../prefetch-tasks/README.md).

## 위치

`packages/next` / `src/client/components/segment-cache` / `optimistic-routes.ts` L1-L44 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/optimistic-routes.ts#L1-L44))

## 실제 코드

파일 머리 주석이 설계 전체를 적는다. 진입점이 둘이다.

```ts
// optimistic-routes.ts L18-L35
 * Main entry points:
 *
 * 1. discoverKnownRoute: Called after receiving a route tree from the server.
 *    Traverses the route tree, compares URL parts to segments, and populates
 *    the known route tree if they match. Routes are always inserted into the
 *    cache.
 *
 * 2. matchKnownRoute: Called when looking up a route with no cache entry.
 *    Matches the candidate URL against learned patterns. Returns a synthetic
 *    cache entry if successful, or null to fall back to server resolution.
 *
 * Rewrite detection happens during traversal: if a URL path part doesn't match
 * the corresponding route segment, we stop populating the known route tree
 * (since the mapping is incorrect) but still insert the route into the cache.
 *
 * The known route tree is append-only with no eviction. Route patterns are
 * derived from the filesystem, so they don't become stale within a session.
 * Cache invalidation on deploy clears everything anyway.
```

```text
 ★★ 라우트 캐시에 "배우는 쪽" 과 "지어내는 쪽" 이 따로 있다

   discoverKnownRoute   서버가 준 라우트 트리를 받을 때마다 부른다. 캐시에 넣고,
                        URL 과 트리 모양이 맞으면 **패턴**으로도 저장한다        [01]
   matchKnownRoute      캐시에 없을 때 부른다. 패턴에 맞으면 합성 항목을,
                        아니면 null (서버에 물어라)                                [02]

 주석 L29-31 - 리라이트 탐지는 순회 중에 한다. URL 조각이 세그먼트와 안 맞으면
   "we stop populating the known route tree ... but still insert the route into the cache"

 ★★ 주석 L33-35 - "The known route tree is append-only with no eviction.
   Route patterns are derived from the filesystem, so they don't become stale
   within a session. Cache invalidation on deploy clears everything anyway."
 => **노드**는 그렇다. 그러나 노드에 매달린 **패턴은 사라진다** —
    readPattern(L172-186)이 읽을 때마다 `isValueExpired` 로 검사해
    만료면 `part.pattern = null` 로 지운다 (L180-183)
      staleAt <= now                    정적 수명(STATIC_STALETIME_MS)이 지나면
      version < 현재 라우트 캐시 버전   invalidateRouteCacheEntries · invalidateEntirePrefetchCache 가
                                        버전을 올리면 (SCCACHE L417 · L435) **전부 한꺼번에**
 => 그래서 "빠지지 않는 것" 은 트리 모양(어떤 정적 이름·동적 자식이 있나)이고,
    예측에 쓰는 템플릿은 라우트 캐시 항목과 수명을 같이한다 → [03]에서 이것이 문제가 된다
```

## 동작 흐름

```text
 들어오는 길 — 호출처 전수 (packages/next/src 전체 grep, 테스트 제외)

 discoverKnownRoute (OPTR L220) — **여섯 곳**
   create-initial-router-state.ts L108   첫 로드 (브라우저에서만, L106 `location !== null`)
   SCNAV L555                            캐시 미스 내비게이션 응답 (navigateToUnknownRoute)
   server-action-reducer.ts L488         액션이 redirect 로 돌려준 트리
   SCCACHE L2119                         라우트 트리 프리페치 응답 (/_tree, PPR 켜진 라우트)
   SCCACHE L3445                         같은 프리페치의 PPR 아닌 응답 (writeDynamicTreeResponseIntoCache)
   PPRNAV L1743                          어긋남 재시도 — retryUrl 이 seed 트리와 맞으면 hasDynamicRewrite 표시,
                                         리라이트 자리에 걸리면 표시 없이 캐시 삽입만 한다  [03]
   => 주석 L205-206 "(initial load, navigation, or prefetch)" 셋에 **액션 redirect 와 재시도**가 더 있다

 matchKnownRoute (OPTR L726) — **한 곳**
   SCCACHE L537  readRouteCacheEntry 안, 캐시 맵에서 못 찾았을 때
     readRouteCacheEntry 를 부르는 곳
       SCNAV L150              navigateImpl — 내비게이션
       SCCACHE L668            readOrCreateRouteCacheEntry ← scheduler.ts L737 · L754 (프리페치)
       scheduler.ts L633       RouteTree 단계가 끝난 뒤 prefetchHints 를 읽을 때
       SCCACHE L725            deprecated_requestOptimisticRouteCacheEntry (아래 표) — 플래그가 꺼졌을 때만
                               불리므로(SCNAV L182) 여기서 matchKnownRoute 까지 가는 일은 없다
   => 예측은 내비게이션만의 것이 아니다. **프리페치 작업도 같은 함수로 캐시를 읽으므로**
      패턴이 맞으면 `/_tree` 요청 없이 곧장 세그먼트 단계로 간다 (머리 주석 L6-7
      "this allows skipping the route tree prefetch request entirely")

 resetKnownRoutes (OPTR L1117) — app-router-instance.ts L492 hmrRefresh 하나 (개발 전용)
```

```text
 ★★★ 플래그 셋이 이 흐름을 가른다 (규칙 14·16 — 세우는 곳까지 grep)

 __NEXT_OPTIMISTIC_ROUTING = config.experimental.optimisticRouting ?? false   (define-env.ts L391-392)
   기본값 true (config-shared.ts L2175)  => **기본 설정의 현행 경로가 예측이다**
   읽는 곳 (client/ 전체 grep)
     SCCACHE L536   켜져 있으면 matchKnownRoute                          [02]
     SCNAV L182     꺼져 있으면 옛 경로 deprecated_requestOptimisticRouteCacheEntry
     PPRNAV L1267   켜져 있고 캐시된 head 가 partial 이면 viewport 를 기다리지 않는다 (TODO 임시책)
   서버도 같은 설정을 읽는다
     app-render.tsx L610  `optimisticRouting ? staticSiblings : null`
       => 꺼져 있으면 서버가 **정적 형제 목록을 보내지 않는다** — 예측의 안전장치가 [01] 이 목록이다
   ★ discoverKnownRoute 여섯 곳은 **플래그로 감싸여 있지 않다** — 꺼져 있어도 트리는 쌓인다.
     다만 읽는 쪽(L536)이 없으므로 쓰이지 않는다

 옛 경로와 새 경로
   꺼짐  같은 pathname 에 **빈 검색 문자열** 항목이 있을 때만, 그 트리에 검색 문자열을 바꿔 끼운다
         (SCCACHE L689-811. 주석 L684-688 "will be removed once optimisticRouting is stable")
   켜짐  pathname 을 패턴에 맞춘다. 검색 문자열은 무엇이든 그대로 끼운다          [02]
   ★ scheduler.ts L740-784 의 "검색 문자열 뺀 라우트 트리도 프리페치" 는 **플래그와 무관하게** 돈다.
     주석 L741-743 은 이것을 옛 경로의 밑천이라 적는다 (함수 이름도 옛 이름 `requestOptimisticRouteCacheEntry`)

 __NEXT_EXPOSE_TESTING_API = dev || experimental.exposeTestingApiInProductionBuild === true
   (define-env.ts L396-397)                                                 [04]
   => **개발 서버에서는 언제나 켜져 있다.** 잠금 쿠키가 없으면 아무 일도 안 한다

 cacheComponents / PPR
   OPTR 에는 `process.env` 를 읽는 줄이 **0개**다 (grep -n "process.env" optimistic-routes.ts → 없음)
     => PPR·cacheComponents 로 갈리는 갈래가 파일 안에 없다
   => 예측은 CC 를 끈 기본 앱에서도 돈다 ([PPR 내비게이션] README 의 "ppr 인데 PPR 무관" 과 같은 모양)
```

1. [패턴을 배우기](01_learn/README.md) — 서버 트리와 URL 을 나란히 걸으며, 어긋나면 캐시에만 넣는다.
2. [패턴에 맞추기](02_match/README.md) — 정적 이름이 이기고, 모르는 것이 하나라도 있으면 거절한다.
3. [예측이 틀렸을 때](03_mispredict/README.md) — 표시하고, 라우트 캐시 전체를 버리고, 다시 한다.
4. [테스트 잠금](04_testing-lock/README.md) — 쿠키 하나로 동적 데이터 쓰기를 붙잡는다. 프로덕션에서는 모듈째 바뀐다.

```text
 ★★ 한 번의 예측이 지나는 길 (기본 설정)

 사용자가 /blog/b 링크를 누른다. 전에 /blog/a 를 방문했다 (첫 로드 → discoverKnownRoute)
 SCNAV L150  readRouteCacheEntry(/blog/b)
               SCCACHE L522 캐시 맵 → 없음
               SCCACHE L537 matchKnownRoute → 합성 항목 (tree 의 [slug] 캐시 키 = "b")      [02]
 SCNAV L153  navigateUsingPrefetchedRouteTree(..., route = 합성 항목)
 SCNAV L433    navigateToKnownRoute(..., routeCacheEntry = 합성 항목)
                 트리를 **동기로** 짓고, 빈 곳은 spawnDynamicRequests 로 채운다   [PPR 내비게이션]
 PPRNAV L1947    응답의 URL 이 합성 항목의 canonicalUrl(= 요청한 pathname+search)과 다르면 RedirectRetry
 PPRNAV L1576    풀리지 않은 자리가 남으면 SoftRetry
                 => dispatchRetryDueToTreeMismatch                                    [03]
 => 맞으면 이 내비게이션은 **캐시 미스인데도 동기로** 끝난다 —
    [프리페치] [03]이 적은 "Promise 를 돌려주는 셋째 출구" 로 가지 않는다
```

## 결과가 쓰이는 곳

```text
 knownRouteTreeRoot (OPTR L200, 모듈 전역 트라이)
      --> [02] matchKnownRoute 가 URL 조각을 따라 내려간다
      ★ 탭 하나의 세션 동안 유지된다. 비우는 곳은 개발 HMR(resetKnownRoutes) 하나다

 합성 FulfilledRouteCacheEntry
      --> SCNAV 의 navigateUsingPrefetchedRouteTree → [PPR 내비게이션]의 navigateToKnownRoute
      --> 프리페치 작업의 pingRootRouteTree → [프리페치 작업]의 세그먼트 단계
      ★ routeCacheMap 에는 **넣지 않는다** (ref: null, L803) — 읽을 때마다 다시 짓는다 [02]

 hasDynamicRewrite
      --> [03]. 틀린 예측을 표시해 다음 매칭이 거절하게 하려는 값

 NEXT_INSTANT_TEST_COOKIE · NavigationLock
      --> [04]. 서버는 쿠키로 셸만 그리고, 클라이언트는 잠금으로 동적 데이터 쓰기를 미룬다
```

## 다루지 않는 것

`routeCacheMap` · `CacheMap` 의 키 구조와 `getRouteVaryPath` · `getFulfilledRouteVaryPath`, `fulfillRouteCacheEntry` · `writeRouteIntoCache` 가 항목을 만드는 과정([캐시 항목](../cache-entries/README.md)), `vary-path.ts` 의 `appendLayoutVaryPath` · `finalizePageVaryPath` 가 키를 조립하는 규칙, `convertRootTreePrefetchToRouteTree` · `convertRootFlightRouterStateToRouteTree` 가 서버 응답을 `RouteTree` 로 바꾸는 과정, 프리페치 작업이 합성 항목을 받은 뒤의 세그먼트 단계([프리페치 작업](../prefetch-tasks/README.md)), `deprecated_requestOptimisticRouteCacheEntry`(SCCACHE L689-811)의 본문 세부, 서버가 `staticSiblings` 를 로더 트리에 싣는 쪽(next-app-loader · Turbopack `app_structure.rs`)의 계산 규칙, Instant Navigation 개발 도구 패널(`next-devtools/.../instant-navs/`)과 `@next/playwright` 의 `instant()` 본문은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 패턴을 배우기](01_learn/README.md)
- [02 패턴에 맞추기](02_match/README.md)
- [03 예측이 틀렸을 때](03_mispredict/README.md)
- [04 테스트 잠금](04_testing-lock/README.md)
