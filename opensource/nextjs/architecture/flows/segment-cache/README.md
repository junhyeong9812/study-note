# 프리페치가 쌓이고 내비게이션이 그것을 쓰기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[클라이언트가 화면을 바꾸기까지](../client-router/README.md)의 `navigate-reducer` 가 56줄짜리 접착 코드였던 이유가 여기다. 내비게이션의 본체가 이 11,522줄로 옮겨졌다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `SCTYPES` = `client/components/segment-cache/types.ts`(68줄), `SCCACHE` = `.../cache.ts`(4298줄), `SCNAV` = `.../navigation.ts`(1278줄).

## 위치

`packages/next` / `src/client/components/segment-cache` / `types.ts` L1-L68 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/types.ts#L1-L68))

## 실제 코드

68줄짜리 `types.ts` 가 이 디렉터리 전체의 설계를 담고 있다.

```ts
// types.ts L34-L68
export const enum FetchStrategy {
  // Deliberately ordered so we can easily compare two segments
  // and determine if one segment is "more specific" than another
  // (i.e. if it's likely that it contains more data). See
  // canNewFetchStrategyProvideMoreContent in cache.ts for what each tier can
  // contain relative to the others.
  //
  // These numeric values are client-internal and never cross the wire — the
  // `next-router-prefetch` request header values are mapped explicitly in
  // fetchSegmentPrefetchesUsingDynamicRequest (cache.ts) — so the members can
  // be renumbered freely as long as the relative order is preserved.
  LoadingBoundary = 0,
  // The App Shell variant extracted from a static per-segment prefetch
  // response: every segment's param-dependent content is reduced to pending
  // references that render as the param fallback. Less complete than
  // RuntimeShell — a static response can't include content that depends on
  // session data (cookies, headers) — and less complete than PPR at concrete
  // paths, which includes prerendered param-dependent content.
  StaticShell = 1,
  RuntimeShell = 2,
  PPR = 3,
  PPRRuntime = 4,
  Full = 5,
}

/**
 * A subset of fetch strategies used for prefetch tasks.
 * A prefetch task can't know if it should use `PPR` or `LoadingBoundary`
 * until we complete the initial tree prefetch request, so we use `PPR` to signal both cases
 * and adjust it based on the route when actually fetching.
 * */
export type PrefetchTaskFetchStrategy =
  | FetchStrategy.PPR
  | FetchStrategy.PPRRuntime
  | FetchStrategy.Full
```

```text
 ★★ 완성도 티어가 여섯이고 숫자 순서가 "더 많은 데이터를 담을 **가능성**" 을 나타낸다

   LoadingBoundary = 0   loading.tsx 만
   StaticShell     = 1   정적 프리페치에서 뽑은 앱 셸. 파라미터 의존 내용은 폴백으로
   RuntimeShell    = 2   런타임 셸 (세션 데이터를 쓸 수 있다)
   PPR             = 3   구체적 경로의 PPR — 프리렌더된 파라미터 의존 내용까지
   PPRRuntime      = 4
   Full            = 5   전부

 주석 L35-39 - "Deliberately ordered so we can easily compare two segments
   and determine if one segment is "more specific" than another
   (i.e. **if it's likely that** it contains more data)"
 ★ "likely" 가 원문에 있다. 정의적 순서가 아니다
 ★★ 그리고 이 값은 **두 축을 겹친 것**이다 (SCCACHE L257-263)
     "'Effectively' spans both of the tier axes, static-vs-runtime included"
   SCCACHE L2723-2738 - 런타임 요청이 필요 없던 정적 응답은
     **요청한 티어가 아니라 그 variant 의 런타임 티어**로 기록된다
     (StaticShell -> RuntimeShell, 그 밖 -> PPRRuntime)
   => 항목에 적힌 숫자는 "무엇으로 요청했나" 가 아니다

 => 그래서 함수 본문이 한 줄이다 (SCCACHE L4058-4063)
      export function canNewFetchStrategyProvideMoreContent(
        currentStrategy, newStrategy
      ): boolean {
        return currentStrategy < newStrategy
      }

 ★★★ 그런데 **`<` 하나로 끝나지 않는다.** 그 위 docstring 이 부인한다 (L4046-4053)
     "However, it's possible that a more specific fetch strategy *won't* give us
      more content if: a segment is fully static ... Because of this, when comparing
      two segments, we should **also check if the existing segment is partial**.
      If it's not partial, then there's no need to prefetch it again,
      even using a 'more specific' strategy."
   => 호출처가 그대로 한다 — SCCACHE L1002 는 `canNew…` **또는**
      `!existingEntry.isPartial && candidateEntry.isPartial`,
      SCHED L1891 은 `segment.isPartial && canNew…`
   => 순수 티어 비교만 하는 곳은 SCHED L1214 하나이고, 거기엔 별도 해명 주석이 붙어 있다

 ★ 주석 L4055-4056 - 실제로는 `LoadingBoundary` 와 `PPR`/`PPRRuntime` 을
   비교하는 일이 없다고 본다. **전순서로 쓰이지 않는다**
```

## 동작 흐름

```text
 segment-cache/ 11,522줄

   cache.ts             4298   캐시 둘과 항목 상태 기계          [01]
   scheduler.ts         2741   프리페치 작업 큐                  [02]
   navigation.ts        1278   navigate — 동기냐 비동기냐를 가른다 [03]
   optimistic-routes.ts 1119
   navigation-testing-lock.ts 553 · cache-map.ts 497 · vary-path.ts 437
   bfcache.ts 201 · lru.ts 127 · types.ts 68
   navigation-testing-lock.disabled.ts 68 · cache-key.ts 61 · prefetch.ts 48 · fetch.ts 26
   (열거 합계 = 11,522)
```

1. [캐시 둘과 항목 상태](01_entries/README.md) — 라우트 캐시와 세그먼트 캐시.
2. [프리페치 큐](02_scheduler/README.md) — 우선순위 셋과 대역폭 예약.
3. [내비게이션](03_navigate/README.md) — 캐시에 있으면 동기, 없으면 Promise.

```text
 ★★ 프리페치 헤더를 붙이는 자리가 **셋**이다

 SCCACHE L1944-1948  fetchRouteOnCacheMiss — 라우트 트리 프리페치
                      NEXT_ROUTER_PREFETCH_HEADER: '1'
                      + NEXT_ROUTER_SEGMENT_PREFETCH_HEADER: '/_tree'
 SCCACHE L2397-2401  정적 per-segment 프리페치 — '1' + 세그먼트 requestKey
 SCCACHE L3063-3078  동적 요청 — FetchStrategy 를 헤더 값으로 바꾼다 (아래)

 ★★ 모든 프리페치는 **라우트 트리 요청으로 시작**하므로 앞의 둘이 주 경로다.
   그리고 서버가 세그먼트 캐시 프로토콜을 알아보는 것은
   `NEXT_ROUTER_SEGMENT_PREFETCH_HEADER` 다 —
   app-render.tsx L474-475  isRouteTreePrefetchRequest =
     isRSCRequest && headers[NEXT_ROUTER_SEGMENT_PREFETCH_HEADER] === '/_tree'

 SCCACHE L3063-3078 의 매핑
   FetchStrategy.Full         => 헤더를 **생략한다**
                                 주석 L3064-3065 - "because it's essentially
                                   just a navigation request that happens ahead of time"
   FetchStrategy.PPRRuntime   => NEXT_ROUTER_PREFETCH_HEADER = '2'
   FetchStrategy.RuntimeShell => '3'
   FetchStrategy.LoadingBoundary => '1'
   default                    => `fetchStrategy satisfies never` (L3081)
 ★ 분기가 **넷뿐**이고 fallthrough 기본값이 없다.
   함수 시그니처(L3030-3034)가 타입으로 `StaticShell`·`PPR` 을 배제한다 —
   그 둘은 **이 switch 에 도달하지 않는다**

 => [App Router] [01]이 서버에서 읽은 그 값들이다
      '1' -> isPrefetchRequest
      '2' -> isRuntimePrefetchRequest
      '3' -> isAppShellPrefetchRequest (runtime 에 포함)
 => 그리고 [응답 나가기] [01]의 CDN 방어가 "'1' '2' '3' 만 인정한다" 고 한 그 값들이다
 ★ 서버 주석(app-render.tsx L450-451)이 덧붙인다 —
   "runtime prefetch requests are *not* treated as prefetch requests".
   '2'/'3' 이면 isPrefetchRequest 는 거짓이다

 ★ 그 이유를 **types.ts L41-44** 가 적어 놓았다 (cache.ts 가 아니다)
     // These numeric values are client-internal and never cross the wire — the
     // `next-router-prefetch` request header values are mapped explicitly in
     // fetchSegmentPrefetchesUsingDynamicRequest (cache.ts) — so the members can
     // be renumbered freely as long as the relative order is preserved.
   => 숫자는 **절대 와이어를 넘지 않는다.** 헤더 값은 위에서 명시적으로 매핑하므로
      상대 순서만 지키면 번호는 자유롭게 바꿔도 된다
```

```text
 ★★★ `NavigationResultTag`(SCTYPES L5-10)는 **죽은 열거형이다**

   MPA · Success · NoOp · Async 네 값이 선언돼 있는데
   저장소 전체에서 참조가 **선언 한 줄뿐**이다 (grep 전수)

 => 쓰이지 않는다. 내비게이션 결과의 실제 모양은 이것이 아니라
    `navigate` 의 반환형 `AppRouterState | Promise<AppRouterState>`(SCNAV L79)다
 ★ types.ts 가 이 디렉터리의 설계를 담고 있긴 하지만,
   그중 한 열거형은 **남겨진 것**이다
```

```text
 ★★ 프리페치 우선순위가 셋이고 **대역폭을 따로 예약한다** (SCTYPES L15-32)

   Intent     = 2   가장 최근에 hover/touch 한 링크
                    주석 - "Special network bandwidth is reserved for this task only.
                      There's only ever one Intent-priority task at a time; when a new
                      Intent task is scheduled, the previous one is bumped down to Default."
   Default    = 1
   Background = 0   부분만 캐시된 항목을 재검증해 더 받을 게 있는지 보는 일 등

 => Intent 는 **언제나 하나**다. 새 것이 오면 이전 것이 Default 로 내려간다
 => 사용자가 마우스를 올린 링크에 네트워크를 몰아 주는 설계다
```

## 결과가 쓰이는 곳

```text
 routeCacheMap (SCCACHE L357) / segmentCacheMap (L382)
      --> [03]의 navigate 가 읽는다. 맞는 것이 있으면 **동기로** 화면을 바꾼다
      ★ 다만 동기로 끝나는 것이 "서버에 안 묻는다" 는 아니다 —
        라우트 트리가 맞아도 `spawnDynamicRequests`(SCNAV L373)가 돈다 — 다만 기다리지 않는다

 FetchStrategy
      --> 헤더 값이 되어 서버로 간다. 그리고 받은 항목의 완성도를 기록해
          나중에 "더 받을 게 있나" 를 `<` 비교 **와 `isPartial`** 로 판단한다

 navigate 의 반환형 `AppRouterState | Promise<AppRouterState>`
      --> [클라이언트 라우터]의 navigate-reducer 가 그대로 돌려준다.
          `ReducerState` 가 Promise 유니온인 근원이다
      ★ `NavigationResultTag` 는 여기에 관여하지 않는다 (죽은 열거형)

 STATIC_STALETIME_MS
      --> SCCACHE L107 이 import 한다. 프리페치 항목의 수명 —
          단 **서버가 `Next-Router-Stale-Time` 헤더를 주면 그 값이 이긴다.**
          이 상수는 헤더가 없을 때의 대체값이다 (L4074-4076)
          ([클라이언트 라우터] [02]에서 본 대로 DYNAMIC 은 여기 안 쓴다)
```

## 다루지 않는 것

`cache.ts`(4298줄)의 항목 읽기·쓰기 함수 전체와 `CacheMap`(`cache-map.ts` 497줄) · `lru.ts`(127줄)의 자료구조, `scheduler.ts`(2741줄)의 작업 스케줄링 세부, `navigation.ts`(1278줄)의 트리 병합, `optimistic-routes.ts`(1119줄)의 낙관적 라우트 예측, `PrefetchTaskFetchStrategy`(SCTYPES L64-68)가 세 값만 갖는 이유와 `PPR` 이 `LoadingBoundary` 자리를 겸하는 처리, `vary-path.ts`(437줄) · `bfcache.ts`(201줄) · `cache-key.ts` · `fetch.ts` · `prefetch.ts`, `navigation-testing-lock.ts`(553줄)와 Instant Navigation Testing API, `ppr-navigations.ts`(2383줄)의 PPR 병합, `FlightRouterState` 의 구조, 서버가 세그먼트별 응답을 만드는 쪽(`collect-segment-data.tsx` 1528줄)은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 캐시 둘과 항목 상태](01_entries/README.md)
- [02 프리페치 큐](02_scheduler/README.md)
- [03 내비게이션](03_navigate/README.md)
