# 02 병렬 라우트를 따라 재귀하기

상위: [트리를 조립하고 세그먼트로 자르기까지](../README.md)

한 세그먼트를 다 준비하면 이 함수는 **자기 자신을 다시 부른다** — 병렬 라우트(`children` · `@modal` 같은 슬롯)마다 한 번씩. 그런데 돌려받은 자식을 레이아웃에 그대로 끼우지 않는다. 레이아웃은 **`<LayoutRouter>` 엘리먼트**를 받고, 자식의 실제 내용은 별도 칸으로 나간다.

## 위치

`packages/next` / `src/server/app-render` / `create-component-tree.tsx` L510-L710 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/create-component-tree.tsx#L510-L710))

## 실제 코드

"PPR 이전" 의 프리페치 규칙이다 — 그런데 v16.3.6 의 **기본 설정에서 지금 도는 규칙**이기도 하다.

```tsx
// create-component-tree.tsx L535-L608
        if (
          // Before PPR, the way instant navigations work in Next.js is we
          // prefetch everything up to the first route segment that defines a
          // loading.tsx boundary. (We do the same if there's no loading
          // boundary in the entire tree, because we don't want to prefetch too
          // much) The rest of the tree is deferred until the actual navigation.
          // It does not take into account whether the data is dynamic — even if
          // the tree is completely static, it will still defer everything
          // inside the loading boundary.
          //
          // This behavior predates PPR and is only relevant if the
          // PPR flag is not enabled.
          isPrefetch &&
          (Loading || !hasLoadingComponentInTree(parallelRoute)) &&
          // The approach with PPR is different — loading.tsx behaves like a
          // regular Suspense boundary and has no special behavior.
          //
          // With PPR, we prefetch as deeply as possible, and only defer when
          // dynamic data is accessed. If so, we only defer the nearest parent
          // Suspense boundary of the dynamic data access, regardless of whether
          // the boundary is defined by loading.tsx or a normal <Suspense>
          // component in userspace.
          //
          // NOTE: In practice this usually means we'll end up prefetching more
          // than we were before PPR, which may or may not be considered a
          // performance regression by some apps. The plan is to address this
          // before General Availability of PPR by introducing granular
          // per-segment fetching, so we can reuse as much of the tree as
          // possible during both prefetches and dynamic navigations. But during
          // the beta period, we should be clear about this trade off in our
          // communications.
          !experimental.isRoutePPREnabled
        ) {
          // Don't prefetch this child. This will trigger a lazy fetch by the
          // client router.
        } else {
          // Create the child component

          if (process.env.NODE_ENV === 'development' && missingSlots) {
            // When we detect the default fallback (which triggers a 404), we collect the missing slots
            // to provide more helpful debug information during development mode.
            const parsedTree = parseLoaderTree(parallelRoute)
            if (
              parsedTree.conventionPath?.endsWith(PARALLEL_ROUTE_DEFAULT_PATH)
            ) {
              missingSlots.add(parallelRouteKey)
            }
          }

          if (childCacheNodeSeedData === null) {
            const seedData = await createComponentTreeInternal(
              {
                loaderTree: parallelRoute,
                parentParams: currentParams,
                parentOptionalCatchAllParamName: optionalCatchAllParamName,
                rootLayoutIncluded: rootLayoutIncludedAtThisLevelOrAbove,
                injectedCSS: injectedCSSWithCurrentLayout,
                injectedJS: injectedJSWithCurrentLayout,
                injectedFontPreloadTags:
                  injectedFontPreloadTagsWithCurrentLayout,
                ctx,
                missingSlots,
                preloadCallbacks,
                authInterrupts,
                // `StreamingMetadataOutlet` is used to conditionally throw. In the case of parallel routes we will have more than one page
                // but we only want to throw on the first one.
                MetadataOutlet: isChildrenRouteKey ? MetadataOutlet : null,
              },
              false
            )

            childCacheNodeSeedData = seedData
          }
        }
```

```text
 ★★★ [프리페치]의 `FetchStrategy.LoadingBoundary = 0` 이 서버에서 무엇을 하는지가 여기 있다

 주석 L536-543
   "Before PPR, the way instant navigations work in Next.js is we prefetch everything
    up to the first route segment that defines a loading.tsx boundary. (We do the same
    if there's no loading boundary in the entire tree, because we don't want to prefetch
    too much) The rest of the tree is deferred until the actual navigation.
    It does not take into account whether the data is dynamic — even if the tree is
    completely static, it will still defer everything inside the loading boundary."

 => PPR 이 꺼져 있으면 **첫 loading.tsx 까지만** 프리페치한다. 데이터가 정적이어도 그 안은 미룬다
 ★★★ 주석은 "Before PPR" 이라 과거형이지만 **현행 경로**다 — v16.3.6 에서 PPR 은
   cacheComponents 로만 켜진다(server/config.ts L574-578 은 `experimental.ppr` 을 아예 오류로,
   L1603-1606 은 cacheComponents 이면 ppr = true). cacheComponents 는 기본이 꺼져 있으므로
   **대부분의 앱이 지금 이 조건을 탄다.** 클라이언트도 PPR 을 못 쓰는 라우트에는
   LoadingBoundary 를 고른다 (segment-cache/scheduler.ts L866-888 · L1680-1724)
 ★ 같은 규칙이 **한 번 더** 있다 — 내비게이션·프리페치 요청은 walk-tree-with-flight-router-state.tsx
   L135-145 가 먼저 처리하고, 거기에 `isPrefetch && !modules.loading && !hasLoadingComponentInTree`
   가 똑같이 들어 있다
 => 조건 — isPrefetch && (Loading || !hasLoadingComponentInTree(parallelRoute)) && !PPR
    이면 자식을 **아예 만들지 않는다**. childCacheNodeSeedData 는 null 로 남는다
    주석 L568-569 - "Don't prefetch this child. This will trigger a lazy fetch by the
      client router."

 주석 L549-556 — PPR 에서는 다르다
   "With PPR, we prefetch as deeply as possible, and only defer when dynamic data is
    accessed. If so, we only defer the nearest parent Suspense boundary of the dynamic
    data access, regardless of whether the boundary is defined by loading.tsx or a
    normal <Suspense> component in userspace."

 ★★ 그리고 대가를 스스로 적는다 (L558-565)
   "NOTE: In practice this usually means we'll end up prefetching more than we were before PPR,
    which may or may not be considered a performance regression by some apps. The plan is
    to address this before General Availability of PPR by introducing granular per-segment
    fetching"
 => 그 "granular per-segment fetching" 이 [프리페치] 흐름의 세그먼트 캐시다.
    그리고 그 응답을 만드는 것이 [04]다
```

## 동작 흐름

```text
 CCTREE L510-711

 L510  parallelRouteMap = await Promise.all(
 L511    Object.keys(parallelRoutes).map(async parallelRouteKey => {
 L515      isChildrenRouteKey = parallelRouteKey === 'children'
 L518-528  notFound · forbidden · unauthorized 는 **'children' 에만** 넘긴다
 L535      PPR 이전 프리페치 규칙이면 자식을 만들지 않는다 (위 실제 코드)
           그 밖이면
 L585        seedData = await createComponentTreeInternal({   ← **재귀**
               loaderTree: parallelRoute,
               parentParams: currentParams,                  ← 쌓인 파라미터를 넘긴다
               rootLayoutIncluded: rootLayoutIncludedAtThisLevelOrAbove,
               MetadataOutlet: isChildrenRouteKey ? MetadataOutlet : null,   L601
               ... }, false)
 L610      templateNode = <Template><RenderFromTemplateContext/></Template>
 L668      return [
             parallelRouteKey,
 L670        createElement(LayoutRouter, { parallelRouterKey, error…, template…, … }),
             childCacheNodeSeedData,
           ]
         }))

 L706  for (const parallelRoute of parallelRouteMap)
 L708    parallelRouteProps[key]             = <LayoutRouter …/>
 L709    parallelRouteCacheNodeSeedData[key] = 자식의 seed
```

```text
 ★★★ 레이아웃의 `children` 은 **자식 페이지가 아니다**

   parallelRouteProps.children = createElement(LayoutRouter, {...경계들...})
   parallelRouteCacheNodeSeedData.children = 자식을 재귀로 만든 CacheNodeSeedData

 => 레이아웃 컴포넌트가 받는 `children` prop 은 **<LayoutRouter> 엘리먼트**다.
    그 props 에는 자식의 내용이 없다 — 경계(error · template · notFound …)만 있다
 => 자식의 실제 트리는 [README]의 튜플 **둘째 칸**(parallelRoutes)으로 따로 나간다
 => 클라이언트에서 그 <LayoutRouter> 가 부모 CacheNode 의 slots 에서 자식을 꺼내 그린다
    → [클라이언트 트리] [03]
 ★★ 이 분리 덕에 내비게이션 때 **레이아웃을 다시 그리지 않고** 자식만 바꿀 수 있다 —
   레이아웃이 들고 있는 것은 "여기에 자식이 온다" 는 자리표뿐이다
   ※ 뒷문장은 이 구조에서 내가 읽은 효과다
```

```text
 ★★ 형제 슬롯은 **병렬**, 부모→자식은 **순차**다

 L510  Promise.all(Object.keys(parallelRoutes).map(async …))
   => 'children' 과 '@modal' 은 동시에 만들어진다
 L585  await createComponentTreeInternal(...)   ← 그 안에서 자기 자식을 기다린다
   => 한 갈래 안에서는 깊이 우선으로 내려간다

 ★ [01]의 세그먼트 설정(L253-386)은 각 호출의 **앞부분**에 있으므로
   부모의 설정은 언제나 자식보다 먼저 쓰인다. 형제끼리는 순서가 정해지지 않는다
   ※ 형제가 같은 workStore 플래그를 다르게 쓸 때 어느 쪽이 이기는지는 확인하지 않았다
```

```text
 ★ MetadataOutlet 은 'children' 에만 내려간다 (L599-601)

   주석 - "`StreamingMetadataOutlet` is used to conditionally throw. In the case of
     parallel routes we will have more than one page but we only want to throw on
     the first one."
 => 병렬 슬롯마다 page 가 있을 수 있지만 메타데이터 오류는 **한 번만** 던져야 한다
 => [메타데이터] [01]의 outlet 이 여기서 한 갈래로만 흐른다
```

## 결과가 쓰이는 곳

```text
 parallelRouteProps (슬롯 이름 → <LayoutRouter>)
      --> [03]에서 레이아웃 컴포넌트의 props 로 펼쳐진다 (`...parallelRouteProps`)

 parallelRouteCacheNodeSeedData (슬롯 이름 → 자식 seed | null)
      --> [03]의 createSeedData 가 튜플 둘째 칸에 넣는다.
          null 이면 [클라이언트 라우터]가 나중에 그 슬롯을 따로 받아 온다

 currentParams (쌓인 파라미터)
      --> 재귀 호출의 parentParams. 잎에서 [동적 API] [04]의 팩토리로 간다
```

## 다루지 않는 것

`hasLoadingComponentInTree` 의 판정, `isPrefetch` 가 세워지는 조건, 개발 전용 `missingSlots` 수집(L573-582)과 `SegmentViewNode`/`segmentViewBoundaries`(L623-666), notFound · forbidden · unauthorized 경계 요소를 만드는 `createBoundaryConventionElement`(L1226), `Template` 과 `RenderFromTemplateContext` 의 동작, `injectedCSS` · `injectedJS` 집합이 재귀로 전달되며 중복 주입을 막는 방식, `rootLayoutIncluded` 의 쓰임은 이 문서의 범위 밖이다.
