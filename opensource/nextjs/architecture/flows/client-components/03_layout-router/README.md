# 03 `<LayoutRouter>` 가 세그먼트마다 그리는 것

상위: [클라이언트 트리가 라우터 상태를 읽기까지](../README.md)

`<LayoutRouter>` 는 서버가 레이아웃의 병렬 라우트 자리마다 하나씩 심는 클라이언트 컴포넌트다. 그런데 서버는 그것에 **자식 내용을 넘기지 않는다.** 내용은 [02]가 내려 준 `LayoutRouterContext` 에서 CacheNode 를 찾아 꺼내고, 다 그린 뒤에는 그 Context 를 **자기 세그먼트로 좁혀 다시 공급**한다. 이 재공급이 [04]의 `useSelectedLayoutSegments()` 가 부른 자리마다 다른 답을 내는 이유다.

## 위치

`packages/next` / `src/client/components` / `layout-router.tsx` L706-L963 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/layout-router.tsx#L706-L963))

## 실제 코드

서버 쪽에서 `<LayoutRouter>` 를 만드는 자리다. props 를 보라.

```tsx
// create-component-tree.tsx L668-L696
        return [
          parallelRouteKey,
          createElement(LayoutRouter, {
            parallelRouterKey: parallelRouteKey,
            error: ErrorComponent,
            errorStyles: wrappedErrorStyles,
            errorScripts: errorScripts,
            template:
              isSegmentViewEnabled && templateFilePath
                ? createElement(
                    SegmentViewNode,
                    {
                      type: 'template',
                      pagePath: templateFilePath,
                    },
                    templateNode
                  )
                : templateNode,
            templateStyles: templateStyles,
            templateScripts: templateScripts,
            notFound: notFoundComponent,
            forbidden: forbiddenComponent,
            unauthorized: unauthorizedComponent,
            ...(isSegmentViewEnabled && {
              segmentViewBoundaries,
            }),
          }),
          childCacheNodeSeedData,
        ]
```

```text
 ★★★ props 가 **경계 컴포넌트뿐**이다

   parallelRouterKey   어느 슬롯인가 ('children' · '@modal' 의 이름 등)
   error · errorStyles · errorScripts · notFound · forbidden · unauthorized
   template · templateStyles · templateScripts
   (개발에서만) segmentViewBoundaries   CCTREE L691-693 · LAYOUTR L729 · L940

 => 자식 세그먼트의 내용(`children`)이 **없다**. 그것은 튜플의 셋째 칸
    `childCacheNodeSeedData`(L695)로 따로 실려 가고, 클라이언트에서 CacheNode 의
    `slots[parallelRouterKey]` 로 다시 만난다 (LAYOUTR L784)
 => 그래서 같은 `<LayoutRouter>` 엘리먼트가 내비게이션 뒤에도 그대로이고,
    바뀌는 것은 Context 로 들어오는 트리와 CacheNode 뿐이다
    ※ "그래서 엘리먼트가 그대로다" 는 props 구성에서 내가 끌어낸 것이다

 ★★ template 도 내용을 **Context 로** 받는다
   서버  L610-614  template = <Template><RenderFromTemplateContext/></Template>
                   Template 은 template.tsx 가 없으면 Fragment 다 (CCTREE L175)
   클라  LAYOUTR L926  <TemplateContext.Provider key={stateKey} value={templateValue}>
   render-from-template-context.tsx L7  children = useContext(TemplateContext)
 => 사용자의 template.tsx 가 받는 children 은 LayoutRouter 가 만든 경계 묶음
    (templateValue, L868-911)이다. `key={stateKey}` 라 세그먼트가 바뀌면 다시 마운트된다
```

## 동작 흐름

```text
 OuterLayoutRouter({ parallelRouterKey, error, ..., template })     LAYOUTR L706

 L731  context = useContext(LayoutRouterContext)
 L733    없으면 => throw 'invariant expected layout router to be mounted'
 L750  segmentPath = parentSegmentPath === null
                     ? [parallelRouterKey]                    ← 뿌리 ([02]의 null)
                     : parentSegmentPath.concat([parentTreeSegment, parallelRouterKey])
 L768  activeTree       = parentTree[1][parallelRouterKey]
 L769  maybeParentSlots = parentCacheNode.slots
 L770  둘 중 하나라도 없으면 => use(unresolvedThenable)   **영원히 suspend**
 L779  서버 + cacheComponents 면 InstantValidationBoundaryContext 를 읽는다
 L784  activeCacheNode = maybeParentSlots[parallelRouterKey] ?? null
 L785  activeStateKey  = createRouterCacheKey(activeSegment, true)   ← 검색 파라미터 제외
 L793  bfcacheEntry = useRouterBFCache(activeTree, activeCacheNode, activeStateKey)
 L799  do {                                    ← 활성 1개 + 최근 비활성 N-1개
 L834    params = parentParams (+ 이 세그먼트가 동적이면 [이름]: 값)
 L868    templateValue =
           ScrollAndMaybeFocusHandler
             ErrorBoundary(error)
               LoadingBoundary(loading = parentLoadingData)
                 HTTPAccessFallbackBoundary(notFound · forbidden · unauthorized)
                   RedirectBoundary
                     InnerLayoutRouter(tree, cacheNode, params, segmentPath,
                                       isActive = isActive && stateKey === activeStateKey)
 L913    서버 + cacheComponents 면 RenderValidationBoundaryAtThisLevel 로 한 겹 더
 L925    child = <TemplateContext.Provider key={stateKey}> template </...>
 L933    개발이면 SegmentStateProvider 로 감싼다
 L945    cacheComponents 면 <Activity mode={활성이면 'visible' 아니면 'hidden'}>
 L957    children.push(child)
 L960  } while (bfcacheEntry !== null)
 L962  => return children          ← **배열**이다
```

```tsx
// layout-router.tsx L758-L797
  // The "state" key of a segment is the one passed to React — it represents the
  // identity of the UI tree. Whenever the state key changes, the tree is
  // recreated and the state is reset. In the App Router model, search params do
  // not cause state to be lost, so two segments with the same segment path but
  // different search params should have the same state key.
  //
  // The "cache" key of a segment, however, *does* include the search params, if
  // it's possible that the segment accessed the search params on the server.
  // (This only applies to page segments; layout segments cannot access search
  // params on the server.)
  const activeTree = parentTree[1][parallelRouterKey]
  const maybeParentSlots = parentCacheNode.slots
  if (activeTree === undefined || maybeParentSlots === null) {
    // Could not find a matching segment. The client tree is inconsistent with
    // the server tree. Suspend indefinitely; the router will have already
    // detected the inconsistency when handling the server response, and
    // triggered a refresh of the page to recover.
    use(unresolvedThenable) as never
  }

  let maybeValidationBoundaryId: string | null = null
  if (typeof window === 'undefined' && process.env.__NEXT_CACHE_COMPONENTS) {
    maybeValidationBoundaryId = use(InstantValidationBoundaryContext)
  }

  const activeSegment = activeTree[0]
  const activeCacheNode = maybeParentSlots![parallelRouterKey] ?? null
  const activeStateKey = createRouterCacheKey(activeSegment, true) // no search params

  // At each level of the route tree, not only do we render the currently
  // active segment — we also render the last N segments that were active at
  // this level inside a hidden <Activity> boundary, to preserve their state
  // if or when the user navigates to them again.
  //
  // bfcacheEntry is a linked list of FlightRouterStates.
  let bfcacheEntry: RouterBFCacheEntry | null = useRouterBFCache(
    activeTree,
    activeCacheNode,
    activeStateKey
  )
```

```text
 ★★★ 키가 **둘**이다 — "상태 키" 와 "캐시 키" (주석 L758-767)

   "The "state" key of a segment is the one passed to React — it represents the
    identity of the UI tree. ... In the App Router model, search params do
    not cause state to be lost, so two segments with the same segment path but
    different search params should have the same state key.
    The "cache" key of a segment, however, *does* include the search params, if
    it's possible that the segment accessed the search params on the server.
    (This only applies to page segments; layout segments cannot access search
    params on the server.)"

 => createRouterCacheKey(segment, true)(create-router-cache-key.ts L16-18)는
    `__PAGE__?foo=bar` 를 `__PAGE__` 로 자른다.
    그래서 `?page=2` 로만 바뀐 이동은 React 키가 같아 **상태가 남는다**
 ★ 동적 세그먼트는 `이름|값|타입` 문자열이 키다 (L10-12). 값이 바뀌면 키가 바뀐다

 ★★ 비활성 트리를 **몇 개** 들고 있는가가 플래그로 갈린다 (bfcache-state-manager.ts L8)
     const MAX_BF_CACHE_ENTRIES = process.env.__NEXT_CACHE_COMPONENTS ? 3 : 1
   주석 L7 "When the flag is disabled, only track the currently active tree"
 => cacheComponents 가 꺼져 있으면 do-while 은 **한 번**만 돈다.
    켜져 있으면 최근 셋까지 <Activity hidden> 으로 **상태를 보존한 채** 같이 그린다
 ★ 그 목록은 React state 로 산다 (주석 L26-31)
 ★★★ 주석 L33-36 은 "데이터는 부모 CacheNode 에 있고 이 훅은 상태만 정한다" 고 적지만
   **코드와 다르다.** `CacheNode.slots` 는 키당 CacheNode **하나**다
   (`Record<string, CacheNode>`, app-router-types.ts L51). 비활성 항목의 CacheNode 는
   **이 훅의 state 가 직접 들고 있다** (bfcache-state-manager.ts L81 · L108), 그리고
   LayoutRouter 는 그 값을 그대로 그린다 (LAYOUTR L801 `const cacheNode = bfcacheEntry.cacheNode`)
 => "내용은 부모 `CacheNode.slots` 에서 꺼낸다" 는 **활성 세그먼트만** 해당한다.
    숨겨진 `<Activity>` 항목은 slots 를 거치지 않는다
```

`InnerLayoutRouter` 가 CacheNode 에서 무엇을 그릴지 고른다.

```tsx
// layout-router.tsx L528-L564
  // `rsc` represents the renderable node for this segment.

  // If this segment has a `prefetchRsc`, it's the statically prefetched data.
  // We should use that on initial render instead of `rsc`. Then we'll switch
  // to `rsc` when the dynamic response streams in.
  //
  // If no prefetch data is available, then we go straight to rendering `rsc`.
  const resolvedPrefetchRsc =
    cacheNode.prefetchRsc !== null ? cacheNode.prefetchRsc : cacheNode.rsc

  // We use `useDeferredValue` to handle switching between the prefetched and
  // final values. The second argument is returned on initial render, then it
  // re-renders with the first argument.
  const rsc: any = useDeferredValue(cacheNode.rsc, resolvedPrefetchRsc)

  // `rsc` is either a React node or a promise for a React node, except we
  // special case `null` to represent that this segment's data is missing. If
  // it's a promise, we need to unwrap it so we can determine whether or not the
  // data is missing.
  let resolvedRsc: React.ReactNode
  if (isDeferredRsc(rsc)) {
    const unwrappedRsc = use(rsc)
    if (unwrappedRsc === null) {
      // If the promise was resolved to `null`, it means the data for this
      // segment was not returned by the server. Suspend indefinitely. When this
      // happens, the router is responsible for triggering a new state update to
      // un-suspend this segment.
      use(unresolvedThenable) as never
    }
    resolvedRsc = unwrappedRsc
  } else {
    // This is not a deferred RSC promise. Don't need to unwrap it.
    if (rsc === null) {
      use(unresolvedThenable) as never
    }
    resolvedRsc = rsc
  }
```

```text
 ★★★ 세그먼트 하나에 **그릴 거리가 둘**이다 — prefetchRsc 와 rsc

   L535  resolvedPrefetchRsc = prefetchRsc !== null ? prefetchRsc : rsc
   L541  rsc = useDeferredValue(cacheNode.rsc, resolvedPrefetchRsc)
   주석 L538-540 - "The second argument is returned on initial render, then it
     re-renders with the first argument."
 => 처음에는 프리페치된 정적 조각을 그리고, 곧바로 최종 rsc 로 다시 그린다
 ★ 이 둘을 채우는 곳이 [프리페치]와의 이음매다 —
   ppr-navigations.ts `createCacheNodeForSegment`(L969-1344)가
   L1002-1122 먼저 freshness 로 가른다. 여기서 **세그먼트 캐시를 안 보고** 반환하는 길이 셋이다 —
              일반 내비게이션의 BFCache 적중(L1017) · Hydration(L1071, 언제나) ·
              뒤로/앞으로의 BFCache 적중(L1102)
   L1127 그렇지 않으면 readSegmentCacheEntryForNavigation(...) 로 세그먼트 캐시(cache.ts L557)를 읽고
   L1187-1219 에서 네 갈래로 나눈다 ("부분" 에는 캐시가 아예 없는 경우도 든다 — 주석 L1205-1207,
              isCachedRscPartial 의 초깃값이 true 다 L1125)
     서버 응답 있음 + 캐시가 부분   prefetchRsc = 캐시,  rsc = 서버 응답
     서버 응답 있음 + 캐시가 완전   prefetchRsc = null,  rsc = 캐시
     서버 응답 없음 + 캐시가 부분   prefetchRsc = 캐시,  rsc = createDeferredRsc()  ← 나중에 채울 약속
     서버 응답 없음 + 캐시가 완전   prefetchRsc = null,  rsc = 캐시

 ★★ null 은 "빈 화면" 이 아니라 "**데이터 없음**" 이다
   L550 · L560  rsc 가 null(또는 null 로 풀린 약속)이면 use(unresolvedThenable) — 영원히 suspend
   주석 L551-554 - "the router is responsible for triggering a new state update to
     un-suspend this segment."
   CacheNode 타입 주석(app-router-types.ts L28-30)이 근거를 적는다 —
     "`null` is a valid React Node but because segment data is always a
      <LayoutRouter> component, we can use `null` to represent empty."
 ★ suspend 가 **세 군데**다 — CacheNode 가 없을 때(L526), rsc 가 null 일 때(L555 · L561),
   OuterLayoutRouter 에서 트리·slots 가 없을 때(L775). 셋 다 "빈 것을 그리느니 멈춘다" 는 같은 태도다
   (L518-524 주석 "we must suspend rather than render nothing, to prevent showing an
    inconsistent route")
```

```text
 ★★★ 다 그리고 나서 LayoutRouterContext 를 **자기로 바꿔** 내려 준다 (L590-611)

   <LayoutRouterContext.Provider value={
     parentTree:        tree            ← 이 세그먼트의 트리
     parentCacheNode:   cacheNode       ← 이 세그먼트의 CacheNode
     parentSegmentPath: segmentPath
     parentParams:      params          ← L834-849 에서 쌓은 것
     parentLoadingData: null            ← 언제나 null 로 되돌린다
     debugNameContext · url · isActive }>
     {rsc}                              ← 이 세그먼트의 레이아웃/페이지
   </...>

 => rsc 안의 레이아웃이 다시 <LayoutRouter> 를 품고 있으면, 그것은 **이 값**을 부모로 본다.
    이렇게 한 단씩 좁혀 내려간다. 주석 L591 "The layout router context narrows down
    tree and childNodes at each level."
 => [04]의 useSelectedLayoutSegments 가 가장 가까운 이 Provider 의 parentTree 에서
    **아래쪽** 세그먼트를 읽는다. 레이아웃 컴포넌트는 이 Provider 의 **안**에 있으므로
    "자기 아래" 가 된다

 ★★ loading.tsx 는 **한 단 건너서** 적용된다
   서버(CCTREE L1286-1297)가 loading 이 있는 세그먼트의 rsc 를 LoadingBoundaryProvider 로 감싼다
   그 Provider(LAYOUTR L616-659)는 parentLoadingData 만 바꿔 LayoutRouterContext 를 다시 공급한다
   => 그 아래의 <LayoutRouter> 가 L887 `loading={parentLoadingData}` 로 Suspense 를 친다
   주석 CCTREE L1290-1291 - "not all segments render a LayoutRouter component, e.g. the root segment."
   주석 LAYOUTR L877-886 은 이 배치가 병렬 라우트에서 맞는지 스스로 의심한다 —
     "this sort of smells like an implementation accident to me."
```

## 결과가 쓰이는 곳

```text
 children 배열 (활성 1 + 비활성 최대 2)
      --> 부모 레이아웃의 `children` 또는 `@슬롯` prop 자리. 화면이다

 다시 공급한 LayoutRouterContext
      --> 아래의 <LayoutRouter> (L731)
      --> [04] useSelectedLayoutSegments · useSelectedLayoutSegment · useRouter(bfcacheId)
      --> client-page.tsx L41-43 · client-segment.tsx L34-36 — cacheComponents 에서
          서버가 params 를 props 로 안 줄 때 parentParams 를 읽는다

 NavigationPromisesContext (개발만, L582-588)
      --> [04]의 훅들이 개발 빌드에서 Suspense DevTools 용 약속을 여기서 꺼낸다

 영원한 suspend (unresolvedThenable)
      --> 라우터가 새 상태를 내보낼 때까지 그 세그먼트가 멈춘다.
          새 상태는 [01]의 경로로 들어온다
```

## 다루지 않는 것

스크롤·포커스 처리 전체(`InnerScrollAndFocusHandlerOld` L192-324 · `InnerScrollHandlerNew` L330-460 · `ScrollAndMaybeFocusHandler` L466-486 과 그 보조 함수 L60-186), `ErrorBoundary` · `HTTPAccessFallbackBoundary` · `RedirectBoundary` 의 내부, `LoadingBoundary`(L665-700)의 Suspense 이름 붙이기, `getBoundaryDebugNameFromSegment` · `isVirtualLayout`(L965-988)과 Suspense DevTools 이름, 개발 도구 `SegmentViewStateNode` · `SegmentBoundaryTriggerNode` · `SegmentStateProvider`(`segment-explorer-node`), cacheComponents 의 즉시 검증 경계(`instant-validation/boundary` 의 `InstantValidationBoundaryContext` · `RenderValidationBoundaryAtThisLevel`), `useRouterBFCache`(bfcache-state-manager.ts L38-120)의 연결 리스트 복제 세부, `createCacheNodeForSegment`(ppr-navigations.ts L969-1344)의 freshness 갈래 본문(L1002-1122 — BFCache 쓰기 `writeToBFCache` · `writeHeadToBFCache`, 뒤로 가기에서 prefetchRsc 를 버리는 조건 L1095-1098)과 head 처리(L1221 이후), `createDeferredRsc` 가 채워지는 과정, `readSegmentCacheEntryForNavigation` 의 본문([프리페치]의 [01 항목](../../segment-cache/01_entries/README.md)이 이름만 다룬다)은 이 문서의 범위 밖이다.
