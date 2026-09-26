# 트리를 조립하고 세그먼트로 자르기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[App Router]가 "여기서 트리를 만든다" 고만 하고 넘어간 자리, [동적 판별] [01]이 "`export const dynamic` 에서 플래그를 세우는 쪽은 범위 밖" 이라 한 자리, [프리페치]가 "서버가 세그먼트별 응답을 만드는 쪽은 범위 밖" 이라 한 자리가 **모두 여기**다. 파일 둘이 앞뒤로 붙어 있다 — 하나가 라우트 트리를 따라 React 트리를 **조립**하고, 다른 하나가 다 만든 결과를 세그먼트 단위로 **자른다**.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `CCTREE` = `server/app-render/create-component-tree.tsx`(1307줄), `CSEG` = `server/app-render/collect-segment-data.tsx`(1528줄), `ARTYPES` = `shared/lib/app-router-types.ts`.

## 위치

`packages/next` / `src/server/app-render` / `create-component-tree.tsx` L84-L1135 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/create-component-tree.tsx#L84-L1135))

## 실제 코드

조립이 돌려주고 자르기가 받는 것이 **다섯 칸 튜플** 하나다.

```ts
// app-router-types.ts L379-L405
export type CacheNodeSeedData = [
  node: React.ReactNode | null,
  parallelRoutes: {
    [parallelRouterKey: string]: CacheNodeSeedData | null
  },
  // TODO: This field is no longer used. Remove it.
  loading: null,
  isPartial: boolean,
  /**
   * An AsyncIterable that yields the route params this segment accessed during
   * server rendering (one name per yield, deduped). Used by the client router
   * to determine cache key specificity - segments that only access certain
   * params can be reused across navigations where unaccessed params change.
   *
   * Does NOT include root params; those are emitted once at the top level of
   * the response (see `r` on the payload) and unioned in by the consumer.
   *
   * - null: tracking was not enabled for this render (e.g., not a prerender).
   *   Treat conservatively - assume all params vary.
   * - Drains to empty Set: segment accesses no params (e.g., client components,
   *   or server components that don't read params). Can be shared across all
   *   param values.
   * - Drains to non-empty Set: segment depends on those params. Can only reuse
   *   when those specific params match.
   */
  varyParams: VaryParamsIterable | null,
]
```

```text
 ★★★ 셋째 칸이 **죽은 칸**이다

   // TODO: This field is no longer used. Remove it.
   loading: null,

 => 트리를 만드는 쪽(CCTREE L1277-1307 createSeedData)은 이 칸에 **언제나 null** 을 넣는다
 => loading 은 칸이 아니라 **감싸는 Provider** 로 옮겨 갔다 — createSeedData 주석
    "wrap the component data in an additional context provider to pass the loading data
     to the next set of children"
 ★ 튜플이라 칸을 지우면 뒤 칸의 번호가 다 바뀐다. 그래서 null 로 자리만 남아 있다
   ※ 뒷문장은 내 추론이다

 ★★★ 다섯째 칸 varyParams 의 docstring 이 세 흐름을 잇는다
   "segments that only access certain params can be reused across navigations where
    unaccessed params change."
   null           추적 안 함 — 모든 파라미터가 바뀐다고 보수적으로 가정
   빈 Set 으로 끝남 파라미터를 안 읽었다 — **모든 값에 공유 가능**
   비어 있지 않음   그 파라미터가 같을 때만 재사용
 => 값을 채우는 것은 [동적 API] [04]의 팩토리가 받는 varyParamsAccumulator 이고,
    쓰는 것은 [프리페치]의 세그먼트 캐시 키다
 ★ 루트 파라미터는 여기 **안 들어간다** — 응답 최상위 `r` 로 한 번만 나간다 (docstring)
```

## 동작 흐름

```text
 조립   createComponentTreeInternal   CCTREE L84-1135   (1052줄, 함수 하나)

 L114-251   준비 — 모듈 · CSS/JS · template · error · loading, layout 이나 page 모듈을
            불러오고(L199), notFound · forbidden · unauthorized 컴포넌트를 준비한다(L221-251)
 L253-386   **라우트 세그먼트 설정을 읽는다**                         [01]
            dynamic · fetchCache · revalidate · unstable_dynamicStaleTime
 L452-474   파라미터를 쌓는다 — 부모 것에 이 세그먼트 것을 더한다 (optional catch-all 이름 포함)
 L510-710   **병렬 라우트마다 자기 자신을 다시 부른다**              [02]
 L798-1135  페이지 또는 레이아웃을 만들고 createSeedData 로 돌려준다  [03]

 자르기  collectSegmentData   CSEG L279-469
            다 만든 RSC 버퍼를 **디코드하고 세그먼트마다 다시 인코드**한다   [04]
            결과는 Map<SegmentRequestKey, Buffer> — '/_tree' · '/_full' · 세그먼트마다 하나
```

1. [세그먼트 설정 읽기](01_config/README.md) — `export const dynamic` 이 플래그 셋을 세운다.
2. [병렬 라우트를 따라 재귀하기](02_recurse/README.md) — PPR 이전의 `loading.tsx` 규칙이 여기 남아 있다.
3. [잎 — 페이지와 레이아웃](03_leaf/README.md) — 팩토리를 부르고 표지를 붙인다.
4. [세그먼트로 자르기](04_slice/README.md) — 끝난 prerender 를 다시 디코드한다.

```text
 ★★ 이 흐름이 다른 흐름의 미룬 자리를 **넷** 닫는다

 [동적 API]·[동적 판별]  "forceStatic · dynamicShouldError 를 세우는 쪽은 범위 밖"
      --> [01] CCTREE L270-288
 [`'use cache'`] [02]   "`$$isPage` / `$$isLayout` 을 누가 심는가"
      --> [03] CCTREE L875 · L1051 (그리고 [메타데이터]의 resolve-metadata.ts L560-561)
 [동적 API] [README]    "trackRuntimeDataAccessed 가 남긴 기록을 읽는 쪽은 범위 밖"
      --> [04] CSEG L997-998  `u` 약속을 세그먼트 응답마다 needsRuntimeRequest 로 넘긴다
          (그리고 최종 판단은 클라이언트가 한다)
 [프리페치] [README]    "서버가 알아보는 것은 NEXT_ROUTER_SEGMENT_PREFETCH_HEADER === '/_tree'"
      --> 응답을 만드는 길이 **둘**이다
          ⓐ 정적 생성된 라우트 — [04] CSEG L437 이 prerender 때 미리 만든 버퍼를 캐시에서 준다
          ⓑ 정적 생성되지 않은 동적 라우트(PPR 꺼짐) — 요청 시점에 [중간부터 그리기] 가
             createRouteTreePrefetch 로 만든다
 ★★★ 두 길은 **대체 관계가 아니다** — 캐시 항목에 segmentData 가 있느냐로 **서로 배타적**이다
         있음   세그먼트 캐시 요청은 캐시에서 주거나(HIT) **404** 다 (app-page-runtime.ts L1763-1810 —
                조건은 `cachedData?.kind === APP_PAGE && cachedData.segmentData`, PPR 이 아니다)
                주석 L1768-1770 "These should never reach the application layer (lambda).
                  We should either respond from the cache (HIT) or respond with 404 (MISS)."
                segmentData 는 PPR 갈래만이 아니라 **평범한 정적 생성**(prerender-legacy) 갈래에서도
                만든다 (app-render L9624-9634). PPR(= cacheComponents)이면 모든 라우트가 적어도 fallback
                항목을 갖는다. RSC 페이로드 `S` 주석 L2200-2203 "With Cache Components, all routes support
                it. Without it, only fully static pages do"
         없음   PPR 이 꺼진 동적 라우트다. 요청 시점에 walk-tree 의 첫 출구(`!isRoutePPREnabled`)가
                createRouteTreePrefetch 로 만든다
         => 응답 형식도 다르다 — 빌드 버퍼는 RootTreePrefetch, 요청 시점 응답은 NavigationFlightResponse
            안의 FlightRouterState 다. 클라이언트가 따로 파싱한다 (segment-cache/cache.ts L2066-2068 · L2127-2141)
          [프리페치]가 든 isRouteTreePrefetchRequest(app-render L474-475)는 ⓑ 의 입력이다
```

## 결과가 쓰이는 곳

```text
 CacheNodeSeedData (루트의 것)
      --> [App Router]가 RSC 페이로드로 직렬화한다.
          클라이언트에서는 [클라이언트 트리]의 LayoutRouter 가 CacheNode 로 풀어 쓴다

 workStore 의 forceStatic · forceDynamic · dynamicShouldError · fetchCache
      --> [동적 API]의 여섯 API 관문, [동적 판별] [01]의 markCurrentScopeAsDynamic

 workUnitStore.revalidate · stale (최솟값)
      --> [응답 나가기]의 Cache-Control 과 Next-Router-Stale-Time

 세그먼트별 버퍼 Map
      --> 빌드 결과물로 저장되고, [프리페치]의 세그먼트 요청이 키로 꺼낸다
```

## 다루지 않는 것

`createComponentTree`(L48)의 추적 껍데기, CSS·JS·폰트 preload 수집(`getLayerAssets` 와 injected 집합), `template` · `error` · `not-found` · `forbidden` · `unauthorized` 경계 요소를 만드는 `createBoundaryConventionElement`(L1226)와 `createErrorBoundaryClientSegmentRoot`(L1137), 개발 전용 `SegmentViewNode` 와 `missingSlots` 수집, `getRootParams`(L1175)의 루트 파라미터 계산, `LoaderTree` 의 모양과 `parseLoaderTree`, `collectPrefetchHints`(CSEG L493-889)와 prefetch inlining 힌트, `PrefetchTreeData`(L931)의 트리 순회 본문과 `renderSegmentPrefetch`(L1273)의 세그먼트 렌더 본문, `collectSegmentDataImpl`(L1071), gzip 크기 측정, 이 Map 을 빌드가 파일로 쓰는 쪽은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 세그먼트 설정 읽기](01_config/README.md)
- [02 병렬 라우트를 따라 재귀하기](02_recurse/README.md)
- [03 잎 — 페이지와 레이아웃](03_leaf/README.md)
- [04 세그먼트로 자르기](04_slice/README.md)
