# 03 잎 — 페이지와 레이아웃

상위: [트리를 조립하고 세그먼트로 자르기까지](../README.md)

자식을 다 만든 뒤에 이 세그먼트 자신을 만든다. 출구가 **넷**이다 — 컴포넌트가 없을 때, force-dynamic 을 PPR 로 미룰 때, 페이지일 때, 레이아웃일 때. 넷 다 `createSeedData` 로 같은 모양의 튜플을 돌려준다. 이 구획에서 [동적 API]의 팩토리가 불리고, [`'use cache'`]가 읽는 표지가 붙는다.

## 위치

`packages/next` / `src/server/app-render` / `create-component-tree.tsx` L737-L1135 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/create-component-tree.tsx#L737-L1135))

## 실제 코드

소스가 **스스로 고장을 인정하는** 갈래가 하나 있다 — 그리고 v16.3.6 에서는 **닿을 수 없는** 갈래다.

```tsx
// create-component-tree.tsx L759-L796
  // If force-dynamic is used and the current render supports postponing, we
  // replace it with a node that will postpone the render. This ensures that the
  // postpone is invoked during the react render phase and not during the next
  // render phase.
  // @TODO this does not actually do what it seems like it would or should do. The idea is that
  // if we are rendering in a force-dynamic mode and we can postpone we should only make the segments
  // that ask for force-dynamic to be dynamic, allowing other segments to still prerender. However
  // because this comes after the children traversal and the static generation store is mutated every segment
  // along the parent path of a force-dynamic segment will hit this condition effectively making the entire
  // render force-dynamic. We should refactor this function so that we can correctly track which segments
  // need to be dynamic
  if (
    workStore.isStaticGeneration &&
    workStore.forceDynamic &&
    experimental.isRoutePPREnabled
  ) {
    return createSeedData(
      ctx,
      createElement(
        Fragment,
        {
          key: cacheNodeKey,
        },
        createElement(Postpone, {
          reason: 'dynamic = "force-dynamic" was used',
          route: workStore.route,
        }),
        layerAssets
      ),
      parallelRouteCacheNodeSeedData,
      loadingData,
      true,

      // force-dynamic postpones without rendering the component, so no params
      // are accessed. The vary params are empty.
      emptyVaryParamsAccumulator
    )
  }
```

```text
 ★★★ `@TODO this does not actually do what it seems like it would or should do.` (L763)

 의도   force-dynamic 을 쓴 세그먼트**만** 동적으로 만들고 나머지는 prerender 한다
 실제   "because this comes after the children traversal and the static generation store
         is mutated every segment along the parent path of a force-dynamic segment will
         hit this condition effectively making the entire render force-dynamic" (L766-768)

 => 자식 순회([02]의 L510-710)가 **이 검사보다 먼저** 끝난다
 => 자식이 [01]의 L273 에서 `workStore.forceDynamic = true` 를 쓰면
    그 조상들이 차례로 이 L770 에 닿을 때 **전부** 조건을 만족한다
 => 결과적으로 **렌더 전체**가 force-dynamic 이 된다
 ★★ [01]에서 본 "플래그가 workStore 하나에 산다" 의 대가를 소스가 직접 적은 자리다.
   세그먼트별 설정을 요청 전역 플래그 하나에 쓰기 때문이다
 ★ 조건 — 정적 생성 중 · forceDynamic · PPR 켜짐. 셋 다면 L775 에서 `<Postpone>` 으로 갈아 끼운다

 ★★★ 그런데 이 조건은 **v16.3.6 사용자 설정으로 만들 수 없다**
   PPR 켜짐   ⇐ cacheComponents 켜짐 (server/config.ts L574-578 · L1603-1606)
   forceDynamic ⇐ 페이지 트리에서는 [01]의 L273 하나 (저장소 grep — 나머지 하나는 라우트 핸들러)
              ⇐ `export const dynamic = 'force-dynamic'`
   그런데 cacheComponents 에서는 `dynamic` export 가 **SWC 컴파일 오류**다
     (react_server_components.rs L956-967 수집 · L1010-1021 보고)
 => 둘을 동시에 켤 수 없다. @TODO 가 설명하는 기제는 **지금은 돌지 않는다**
 => PPR 이 꺼진 정적 생성에서 force-dynamic 이면 [01]의 L276-285 가 먼저
    DynamicServerError 를 던진다. "렌더 전체가 동적이 된다" 는 결과는 같지만 원인은 그 throw 다
```

## 동작 흐름

```text
 출구 넷 — 전부 createSeedData(ctx, 노드, parallelRouteCacheNodeSeedData, loadingData,
                               isPossiblyPartialResponse, varyParamsAccumulator)

 ① L737  컴포넌트가 없으면 (layout 도 page 도 default export 가 없음)
   L738    => <Fragment>{layerAssets}{parallelRouteProps.children}</Fragment>
           varyParams = emptyVaryParamsAccumulator
           주석 L752-753 - "No user-provided component, so no params will be accessed.
             Use the pre-resolved empty tracker."

 ② L770  정적 생성 + forceDynamic + PPR 이면 (위 실제 코드 — 지금은 닿지 않는다)
         isPossiblyPartialResponse 대신 리터럴 `true`, vary 누적기 대신 emptyVaryParamsAccumulator 를 넘긴다 (L790-794)
   L775    => <Fragment><Postpone reason='dynamic = "force-dynamic" was used'/>…</Fragment>

 ③ L817  페이지면
   L903    => createSeedData(...)

 ④ 레이아웃이면
   L1126   => createSeedData(...)
```

```text
 ★★ ② 의 `<Postpone>` 이 [동적 판별] [02]의 그 컴포넌트다 (L782-785) — `<Postpone>` 엘리먼트를
   만드는 곳은 저장소에서 **여기 하나뿐**이고, 위 이유로 지금은 닿지 않는다

   createElement(Postpone, {
     reason: 'dynamic = "force-dynamic" was used',
     route: workStore.route,
   })

 => [동적 판별] [02]는 "함수 호출이 아니라 **JSX 로 쓰는 중단**" 이라 적고
    "트리에 놓는 쪽은 범위 밖" 이라 했다. **여기가 그 자리다**
 ★ 주석 L759-762 가 컴포넌트로 만든 이유를 적는다 — "This ensures that the postpone
   is invoked during the react render phase and not during the next render phase."
```

```text
 ③ 페이지   CCTREE L817-903

 L798  isClientComponent = isClientReference(layoutOrPageMod)
 L800  varyParamsAccumulator =
         클라이언트 컴포넌트 && cacheComponents 이면 emptyVaryParamsAccumulator
         주석 L802-803 - "Client components with Cache Components enabled don't receive
           params from the server, so they have an empty vary params set."
         아니면 createVaryParamsAccumulator()

 클라이언트 페이지이면 <ClientPageRoot> 를 만든다 — 갈래 셋
   cacheComponents     L824  serverProvidedParams: null
                             주석 "Params are omitted when Cache Components is enabled"
   정적 생성 (L829)    L831  createPrerenderParamsForClientSegment(currentParams)
                       L832  createPrerenderSearchParamsForClientPage()
                             → promises: [searchParams 약속, params 약속]
   그 밖                     promises: null  (값만 넘긴다)

 서버 페이지이면
   L854  params       = createServerParamsForServerSegment(currentParams, …, varyParamsAccumulator)
   L863  searchParams = createServerSearchParamsForServerPage(query, varyParamsAccumulator)
         → [동적 API] [04]의 팩토리. 여기가 **사용자가 부르지 않는** 그 호출이다
   L868  isUseCacheFunction(PageComponent) 이면
   L875    { params, searchParams, **$$isPage: true** }
         아니면 { params, searchParams }
```

```text
 ★★★ `$$isPage` 를 심는 곳이 여기다 (L875)

 => [`'use cache'`] [02]가 "판별 표지 — 여기서 떼어낸다" 고 한 그 표지를
    **이 런타임 코드**가 붙인다. `isUseCacheFunction` 일 때만이다
 => 레이아웃은 L1051 에서 `$$isLayout: true` 를 붙인다
 => 이 두 곳과 [메타데이터]의 resolve-metadata.ts L560-561 이 전부다 (저장소 grep).
    컴파일러(crates/)에는 없다
 ★ 그래서 `'use cache'` 페이지는 params 를 **직렬화 안 된 바깥 객체**로 받을 수 있다 —
   [`'use cache'`] [02]가 표지를 보고 함수를 바꿔치기하기 때문이다
```

```text
 ④ 레이아웃   CCTREE L1033-1126

 L1034  params = createServerParamsForServerSegment(currentParams, …)
        ★ 레이아웃은 **searchParams 를 받지 않는다** — 팩토리를 부르지 않는다
 L1042  isUseCacheFunction(SegmentComponent) 이면
 L1046    createElement(UseCacheLayoutComponent,
            { ...parallelRouteProps, params, $$isLayout: true },
            parallelRouteProps.children)       ← children 을 **셋째 인자로 한 번 더**
          주석 L1053-1054 - "Force static children here so that they're validated.
            See https://github.com/facebook/react/pull/34846"
 L1058  아니면 createElement(SegmentComponent, { ...parallelRouteProps, params },
                               parallelRouteProps.children)   ← **여기도 똑같이** (주석 L1064-1065)
 ★ 두 갈래 모두 children 을 props 안에도, 셋째 인자로도 넘긴다

 => `...parallelRouteProps` — [02]에서 만든 **슬롯 이름 → <LayoutRouter>** 가 그대로
    레이아웃의 props 가 된다. `children` · `modal` 같은 prop 이 여기서 생긴다
```

```text
 createSeedData   CCTREE L1277-1307

 L1286  loading 이 있으면
          rsc = <LoadingBoundaryProvider loading={loading}>{rsc}</LoadingBoundaryProvider>
          주석 L1290-1291 - "NOTE: The reason this is a separate wrapper from LayoutRouter is
            because not all segments render a LayoutRouter component, e.g. the root segment."
 L1298  return [rsc, parallelRoutes, **null**, isPossiblyPartialResponse, varyParamsAccumulator]
        주석 - "The accumulator is itself the AsyncIterable<string> that Flight serializes
          into the segment's seed data."

 ★ 셋째 칸은 [README]의 "TODO: This field is no longer used" 그 칸이다.
   loading 이 칸에서 Provider 로 옮겨 간 흔적이 이 함수 하나에 다 있다
 ★ varyParamsAccumulator 가 **그 자체로 AsyncIterable** 이다 — 렌더가 끝나며
   읽힌 파라미터 이름을 흘려보내고, Flight 가 그것을 seed 에 직렬화한다
```

## 결과가 쓰이는 곳

```text
 CacheNodeSeedData (이 세그먼트의 것)
      --> 부모의 [02] L709 parallelRouteCacheNodeSeedData[key] 로 올라간다.
          루트까지 올라가면 [App Router]가 RSC 페이로드에 싣는다

 <ClientPageRoot serverProvidedParams=…>
      --> 클라이언트 페이지가 params 를 받는 길. cacheComponents 면 null 이라
          [클라이언트 트리]의 LayoutRouter 가 쌓은 params 를 쓴다

 $$isPage / $$isLayout
      --> [`'use cache'`] [02]의 isPageSegmentFunction · isLayoutSegmentFunction

 <Postpone>
      --> [동적 판별] [02]. PPR prerender 가 그 자리를 구멍으로 남긴다

 varyParamsAccumulator
      --> [README]의 튜플 다섯째 칸 → [프리페치]의 세그먼트 캐시 키
```

## 다루지 않는 것

`MaybeComponent` 를 개발·정적 생성에서 감싸는 부분(L413-450), `layerAssets` 와 CSS·JS 주입, 클라이언트 레이아웃(`ClientSegmentRoot`, L929-1032)의 갈래, `SegmentViewNode` 와 개발 전용 파일 경로 표시, `isPossiblyPartialResponse`(L403)의 판정, `ClientPageRoot` · `LoadingBoundaryProvider` 의 구현, `createVaryParamsAccumulator` 와 `vary-params` 모듈, 오류 경계용 `createErrorBoundaryClientSegmentRoot`(L1137)는 이 문서의 범위 밖이다.
