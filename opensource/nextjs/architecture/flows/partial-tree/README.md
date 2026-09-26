# 내비게이션 요청이 트리를 중간부터 그리기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[트리 조립]은 **루트부터 끝까지** 조립하는 경로(초기 HTML · prerender)를 봤다. **동적** 내비게이션 RSC 요청은 그렇게 하지 않는다. 클라이언트가 트리 하나를 보내고, 서버는 로더 트리를 그것과 나란히 내려가다가 **'refetch' 표시가 붙었거나 어긋나는 자리부터** 그린다. 그 위의 레이아웃 **컴포넌트**는 다시 그리지 않는다 — 그리고 그 레이아웃의 세그먼트 설정도 그 요청의 workStore 에 반영되지 않는다.

★★ 이 흐름이 **안 도는** 요청이 셋 있다 — ① 프로덕션의 **정적** 라우트는 빌드 때 만든 페이로드를 캐시에서 준다(app-page-runtime.ts L545-601 · L1906-1952, generateDynamicRSCPayload docstring APPR L646-648 "only called on 'dynamic' requests"). ② PPR 이 켜진 프리페치는 라우터 상태를 받지 않아(APPR L466-471 `shouldProvideFlightRouterState`) 루트부터 그린다. ③ 개발 + cacheComponents + instant 검증은 전체 트리다([03]).

★ 그리고 "다시 안 그린다" 는 **컴포넌트**에만 맞다. 메타데이터는 루트 트리 전체를 돈다 — createMetadataComponents 가 루트 loaderTree 를 받는다(APPR L706-713). 건너뛴 레이아웃의 generateMetadata · generateViewport 는 이 요청에서도 실행된다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `WALKTREE` = `server/app-render/walk-tree-with-flight-router-state.tsx`(438줄), `CFRS` = `.../create-flight-router-state-from-loader-tree.ts`(225줄), `ARTYPES` = `shared/lib/app-router-types.ts`, `APPR` = `server/app-render/app-render.tsx`.

## 위치

`packages/next` / `src/server/app-render` / `walk-tree-with-flight-router-state.tsx` L28-L346 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/walk-tree-with-flight-router-state.tsx#L28-L346))

## 실제 코드

클라이언트가 보내는 트리의 넷째 칸이 서버에게 무엇을 할지 알려 준다.

```ts
// app-router-types.ts L136-L169
export type FlightRouterState = [
  segment: Segment,
  parallelRoutes: { [parallelRouterKey: string]: FlightRouterState },
  refreshState?: CompressedRefreshState | null,
  /**
   * - "refetch" is used during a request to inform the server where rendering
   *   should start from.
   *
   * - "inside-shared-layout" is used during a prefetch request to inform the
   *   server that even if the segment matches, it should be treated as if it's
   *   within the "new" part of a navigation — inside the shared layout. If
   *   the segment doesn't match, then it has no effect, since it would be
   *   treated as new regardless. If it does match, though, the server does not
   *   need to render it, because the client already has it.
   *
   * - "metadata-only" instructs the server to skip rendering the segments and
   *   only send the head data.
   *
   *   A bit confusing, but that's because it has only one extremely narrow use
   *   case — during a non-PPR prefetch, the server uses it to find the first
   *   loading boundary beneath a shared layout.
   *
   *   TODO: We should rethink the protocol for dynamic requests. It might not
   *   make sense for the client to send a FlightRouterState, since this type is
   *   overloaded with concerns.
   */
  refresh?: 'refetch' | 'inside-shared-layout' | 'metadata-only' | null,
  /**
   * Bitmask of PrefetchHint flags. Encodes route structure metadata:
   * root layout, loading boundaries, instant configs, and prefetch strategy
   * hints. Only set when non-zero.
   */
  prefetchHints?: number,
]
```

```text
 ★★★ 요청이 **트리 하나**를 싣고 온다 — FlightRouterState

   [0] segment          이 자리의 세그먼트
   [1] parallelRoutes   슬롯 이름 → 아래 FlightRouterState
   [3] refresh          'refetch' · 'inside-shared-layout' · 'metadata-only' · null

 => 클라이언트가 **자기 캐시가 무엇을 가졌는지**를 서버에 알린다.
    서버는 그 모양을 보고 어디서부터 그릴지 정한다
 ★★ 주석 L154-156 이 "A bit confusing" · "it has only one extremely narrow use case" 라고 적는다
   ※ 'metadata-only' 바로 아래 있지만 내용("during a non-PPR prefetch, the server uses it to find
     the first loading boundary beneath a shared layout")은 'inside-shared-layout' 의 용도와 같다.
     어느 표지를 가리키는지 소스만으로는 모호하다
 ★★★ 그리고 **거의 같은 TODO 가 두 파일에** 있다
   ARTYPES L158-160  "We should rethink the protocol for dynamic requests. It might not make
                      sense for the client to send a FlightRouterState, since this type is
                      overloaded with concerns."
   WALKTREE L127-129 "... since **that** type is overloaded with **other** concerns."
   => 이 프로토콜 자체를 다시 생각해야 한다고 소스가 두 번 적는다
```

## 동작 흐름

```text
 누가 부르는가 — generateDynamicRSCPayload   APPR L651

 L696  needsFullTree = __NEXT_DEV_SERVER && cacheComponents && (캐시 우회 아님)
                       && 내비게이션(액션 결과 아님) && instant 검증이 필요한 세그먼트가 있음
 L734  flightData =
 L736    needsFullTree ? createFullTreeFlightDataForNavigation(...)   ← [03] 루트부터 전부
 L746                  : walkTreeWithFlightRouterState({             ← [01][02] 중간부터
                           loaderTreeToFilter: loaderTree,
                           flightRouterState,                          ← 클라이언트가 보낸 것
                           parentParams: {}, rootLayoutIncluded: false, ... })
 L760    .map((path) => path.slice(1))   // remove the '' (root) segment
```

```text
 ★ generateDynamicRSCPayload 를 부르는 쪽도 하나가 아니다 (APPR, 저장소 grep)
   generateDynamicFlightRenderResult          L849  (L910 · L946) — 보통 RSC 요청.
                                                   서버 액션도 handleAction 에 이것을 generateFlight 로 넘긴다 (L2979)
   generateStagedDynamicFlightRenderResultNode L979  (L1083)
   spawnRuntimePrefetchWithFilledCaches       L1148 (L1172)
   generateDynamicFlightRenderResultWithStagesInDev L1294 (L1354)
   generateRuntimePrefetchResult              L1495 (L1545 · L1574) — 런타임 프리페치
 => 이 흐름은 그 모두의 **공통 아래층**이다. 어느 쪽이 부르든 flightRouterState 가 있으면
    중간부터 그린다
```

1. [어디서부터 그리는가](01_where/README.md) — 클라이언트의 트리와 서버의 트리가 처음 어긋나는 자리.
2. [출구 넷](02_exits/README.md) — 트리만 보내기 · 머리만 보내기 · 여기서 그리기 · 한 단 더 내려가기.
3. [전체 트리가 필요할 때](03_full/README.md) — 개발 중 instant 검증은 중간부터 그릴 수 없다.

```text
 ★★ [트리 조립]과 **같은 함수를 부르지만 시작점이 다르다**

 [트리 조립]   createComponentTree(루트 로더 트리)            초기 HTML · prerender
 이 흐름       walkTreeWithFlightRouterState 가 내려가다가
               WALKTREE L264  createComponentTree(**그 자리의** 로더 트리)

 => 어긋난 자리 **아래**만 조립한다. 그 위 레이아웃은 createComponentTree 가 안 돈다
 ★★★ 그래서 그 위 레이아웃의 `export const dynamic` · `revalidate` · `fetchCache` 는
   **이 요청에서 읽히지 않는다** ([트리 조립] [01]이 적은 한계의 근원이 여기다)
```

## 결과가 쓰이는 곳

```text
 FlightDataPath[] (경로 배열)
      --> [App Router]가 RSC 페이로드의 flightData 로 싣는다.
          [PPR 내비게이션]이 받아 기존 CacheNode 트리의 **그 경로에** 끼운다

 createRouteTreePrefetch 의 결과 (route tree 프리페치)
      --> **PPR 이 꺼진 동적 라우트**의 `/_tree` 요청에 대한 요청 시점 응답.
          [트리 조립] [04]의 prerender 버퍼와는 **배타적**이다 — 정적 생성된 라우트(PPR 이든
          평범한 SSG 든)는 그 버퍼를 캐시에서 주거나 404 이고 여기로 오지 않는다 ([프리페치]의 isRouteTreePrefetchRequest)
```

## 다루지 않는 것

`createFlightRouterStateFromLoaderTree`(CFRS L168) · `createRouteTreePrefetch`(CFRS L197)의 본문과 prefetch hint 비트마스크, `matchSegment` · `addSearchParamsIfPageSegment` 의 규칙, 클라이언트가 FlightRouterState 를 만들어 헤더(`Next-Router-State-Tree`)에 싣는 쪽, `refresh` 표지를 붙이는 클라이언트 코드(segment-cache/scheduler.ts L1699-1731 · L1995, navigation.ts L465, cache.ts L354, ppr-navigations.ts L869)의 판단 규칙, `getLinkAndScriptTags` · `getPreloadableFonts` 의 CSS·폰트 수집, 서버 액션 응답의 flightData 는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 어디서부터 그리는가](01_where/README.md)
- [02 출구 넷](02_exits/README.md)
- [03 전체 트리가 필요할 때](03_full/README.md)
