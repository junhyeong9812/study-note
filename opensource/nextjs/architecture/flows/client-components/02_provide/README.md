# 02 Context 를 만든다

상위: [클라이언트 트리가 라우터 상태를 읽기까지](../README.md)

`Router`(APPROUTER L154-577, 424줄)는 [01]에서 받은 상태 하나로 Context 일곱 개의 값을 만든다. **URL 에서 둘**(pathname · searchParams), **트리에서 둘**(pathParams · layoutRouterContext)이 나온다. 그리고 그 사이에 브라우저 history 를 가로채는 effect 가 끼어 있다 — 훅이 돌려주는 URL 이 사용자 코드의 `pushState` 까지 따라가게 하는 장치다.

## 위치

`packages/next` / `src/client/components` / `app-router.tsx` L154-L577 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/app-router.tsx#L154-L577))

## 실제 코드

`usePathname()` 과 `useSearchParams()` 가 읽는 값이 **둘 다 `canonicalUrl` 한 문자열**에서 나온다.

```tsx
// app-router.tsx L165-L181
  const state = useActionQueue(actionQueue)
  const { canonicalUrl } = state
  // Add memoized pathname/query for useSearchParams and usePathname.
  const { searchParams, pathname } = useMemo(() => {
    const url = new URL(
      canonicalUrl,
      typeof window === 'undefined' ? 'http://n' : window.location.href
    )

    return {
      // This is turned into a readonly class in `useSearchParams`
      searchParams: url.searchParams,
      pathname: hasBasePath(url.pathname)
        ? removeBasePath(url.pathname)
        : url.pathname,
    }
  }, [canonicalUrl])
```

```text
 ★★ 서버에서는 기준 URL 이 **가짜 오리진** 'http://n' 이다 (L171)
   canonicalUrl 은 경로+쿼리 문자열이라 new URL 에 base 가 필요하다.
   서버에는 window.location 이 없으니 아무 오리진이나 붙이고 pathname 만 쓴다
 ★ basePath 는 여기서 떼어 낸다 (L177-179) — usePathname() 은 basePath 를 모른다
 ★ searchParams 는 **날것의 URLSearchParams** 다. 읽기 전용으로 감싸는 것은 훅이다
   주석 L175 "This is turned into a readonly class in `useSearchParams`"
   => [04]의 NAVHOOKS L70 `new ReadonlyURLSearchParams(searchParams)`
 => useMemo 의존성이 [canonicalUrl] 하나다. tree 가 바뀌어도 URL 이 같으면
    두 Context 값의 **참조가 그대로**다
```

## 동작 흐름

```text
 Router({ actionQueue, globalError, webSocket, staticIndicatorState })   L154

 L165  state = useActionQueue(actionQueue)                              [01]
 L168  { searchParams, pathname } = useMemo(... canonicalUrl)            (위 실제 코드)
 L183  개발이면 window.nd = { router, cache, tree }  (디버깅용)
 L200  effect — window.next.__internal_src_page = extractSourcePageFromFlightRouterState(tree)
 L210  effect — 'pageshow'(bfcache 복원)면 ACTION_RESTORE 디스패치 (L228)
 L242  effect — 'error' · 'unhandledrejection' 에서 redirect 오류를 잡아
                publicAppRouterInstance.push / replace 로 바꾼다 (L255-259)
 L282  if (pushRef.mpaNavigation) — **렌더 중에** location.assign/replace 후 throw   (아래)
 L303  effect — history.pushState / replaceState 를 **덮어쓴다**                  (아래)
 L412  matchingHead = findHeadInCache(cache, tree[1])
 L417  pathParams   = getSelectedParams(tree)            → PathParamsContext
 L425  개발이면(L429) createRootNavigationPromises(tree, pathname, searchParams, pathParams)
 L437  layoutRouterContext = { parentTree: tree, parentCacheNode: cache, ... }   (아래 인용)
 L455  globalLayoutRouterContext = { tree, focusAndScrollRef, nextUrl, previousNextUrl }
 L487  content = <RedirectBoundary>{head}<RootLayoutBoundary>{cache.rsc}</...><AppRouterAnnouncer/></...>
 L498  개발 서버면 HotReloader 로, 아니면 RootErrorBoundary(globalError) 로 감싼다
 L547  return <HistoryUpdater/> + 일곱 Provider      ([README] 실제 코드)
```

```tsx
// app-router.tsx L281-L301
  const { pushRef } = state
  if (pushRef.mpaNavigation) {
    // if there's a re-render, we don't want to trigger another redirect if one is already in flight to the same URL
    if (globalMutable.pendingMpaPath !== canonicalUrl) {
      const location = window.location
      if (pushRef.pendingPush) {
        location.assign(canonicalUrl)
      } else {
        location.replace(canonicalUrl)
      }

      globalMutable.pendingMpaPath = canonicalUrl
    }
    // TODO-APP: Should we listen to navigateerror here to catch failed
    // navigations somehow? And should we call window.stop() if a SPA navigation
    // should interrupt an MPA one?
    // NOTE: This is intentionally using `throw` instead of `use` because we're
    // inside an externally mutable condition (pushRef.mpaNavigation), which
    // violates the rules of hooks.
    throw unresolvedThenable
  }
```

```text
 ★★★ 하드 내비게이션을 **렌더 함수 안에서** 한다

 주석 L271-280
   "When mpaNavigation flag is set do a hard navigation to the new url.
    Infinitely suspend because we don't actually want to rerender any child
    components with the new URL and any entangled state updates shouldn't
    commit either (eg: useTransition isPending should stay true until the page
    unloads).
    This is a side effect in render. Don't try this at home, kids. It's
    probably safe because we know this is a singleton component and it's never
    in <Offscreen>. At least I hope so. (It will run twice in dev strict mode,
    but that's... fine?)"

 => [클라이언트 라우터]의 02 문서가 "completeHardNavigation 은 새 상태만 돌려주고
    실제 재요청은 AppRouter 가 한다" 고 적은 그 자리가 여기다 — **확인했다**
 => 그리고 `throw unresolvedThenable` 로 **영원히 suspend** 한다.
    페이지가 내려갈 때까지 새 URL 로 자식을 다시 그리지 않는다
 ★ 같은 URL 로 두 번 이동하지 않게 모듈 전역 `globalMutable.pendingMpaPath`(L55-57)로 막는다.
   bfcache 로 돌아오면 L226 이 그것을 지운다 — 안 지우면 같은 URL 로 다시 못 간다
 ★ `use()` 가 아니라 `throw` 인 이유도 적었다 (L297-299) —
   "we're inside an externally mutable condition (pushRef.mpaNavigation),
    which violates the rules of hooks."
```

```text
 ★★★ 사용자가 부른 history.pushState 도 **라우터 상태가 된다** (L303-408)

 L304  originalPushState / originalReplaceState 를 bind 해 둔다
 L331  window.history.pushState = function pushState(data, _unused, url) {
 L338    data?.__NA || data?._N 이면 => 원래 함수로 그냥 넘긴다   ← Next.js 자신의 호출
 L342    data = copyNextJsInternalHistoryState(data)   __NA 와 내부 트리를 옮겨 싣는다
 L344    url 이 있으면 applyUrlFromHistoryPushReplace(url)
 L317      startTransition(() => dispatchAppRouterAction({ type: ACTION_RESTORE, url, historyState }))
 L348    return originalPushState(...)
 L356  replaceState 도 같다
 L379  onPopState
 L380    event.state 가 없으면 => return            (TODO-APP 주석: 밖에서 부른 경우다)
 L386    !event.state.__NA 이면 => location.reload()  (pages 라우터가 넣은 항목)
 L394    아니면 dispatchTraverseAction(location.href, 내부 트리)   (L393 startTransition 안)
 L403  cleanup 에서 원래 함수로 되돌린다

 주석 L309 "Ensure the canonical URL in the Next.js Router is updated when the URL is
   changed so that `usePathname` and `useSearchParams` hold the pushed values."
 => 이 effect 의 **존재 이유가 훅 두 개**다
 ★ 표지가 둘이다 — `__NA` 는 App Router, `_N` 은 옛 라우터 (코드 L338 · L363).
   주석 L83 은 밑줄 **둘**인 `__N` 으로 적어 코드와 어긋난다.
   Next.js 가 넣은 항목은 HistoryUpdater(L79-86)가 `__NA: true` 를 달아 준다.
   그래서 **자기 호출은 가로채지 않고** 순환을 피한다 (주석 L337)
 ★ 가로챈 URL 은 ACTION_NAVIGATE 가 아니라 **ACTION_RESTORE** 로 간다 —
   서버에 새로 묻는 이동이 아니라 "이 URL 과 이 트리로 상태를 맞춰라" 다
```

```tsx
// app-router.tsx L437-L453
  const layoutRouterContext = useMemo(() => {
    return {
      parentTree: tree,
      parentCacheNode: cache,
      parentSegmentPath: null,
      parentParams: {},
      parentLoadingData: null,
      // This is the <Activity> "name" that shows up in the Suspense DevTools.
      // It represents the root of the app.
      debugNameContext: '/',
      // Root node always has `url`
      // Provided in AppTreeContext to ensure it can be overwritten in layout-router
      url: canonicalUrl,
      // Root segment is always active
      isActive: true,
    }
  }, [tree, cache, canonicalUrl])
```

```text
 ★★ 뿌리의 LayoutRouterContext 는 **빈 경로**에서 시작한다

   parentTree         tree        (전체 라우터 트리)
   parentCacheNode    cache       (전체 CacheNode 트리의 뿌리)
   parentSegmentPath  null        ← [03]이 이 null 을 "뿌리" 로 알아본다 (LAYOUTR L751)
   parentParams       {}          ← 파라미터는 [03]이 내려가며 **쌓는다**
   parentLoadingData  null
   url                canonicalUrl
   isActive           true        주석 L450 "Root segment is always active"

 ★★★ 그런데 useParams() 는 이 parentParams 를 **읽지 않는다**
   PathParamsContext 는 L417 `getSelectedParams(tree)` 로 **트리 전체**에서 한 번에 모은다
   (compute-changed-path.ts L225-251 — `Object.values(parallelRoutes)` 로 모든 병렬 라우트를
    재귀하며 `params[segment[0]]` 에 넣는다)
 => 파라미터를 만드는 길이 **둘**이다
      useParams()                  맨 위 한 번, 트리 전체         (APPROUTER L417)
      클라이언트 page 의 params prop  세그먼트마다 쌓은 것          (LAYOUTR L834-849 → client-page.tsx L41-43)
 ★ 둘이 한 가지는 맞춰 둔다 — catch-all 값을 '/' 로 쪼개 배열로 만드는 규칙이다.
   route-params.ts L231-232 주석 "Catch-all param keys are a concatenation of the path
   segments. See equivalent logic in `getSelectedParams`."
 ★★ 그 밖에서는 **범위가 다르다** — 같은 결과가 아니다
   getSelectedParams (compute-changed-path.ts L231-248)  트리 **전체** — 모든 병렬 슬롯과
                                                           **아래** 세그먼트까지 돈다
   LayoutRouter 가 쌓는 것 (LAYOUTR L834-849)              **조상**만 쌓는다 — 주석 L836-838
     "params that the layout/page components are permitted to access below this point"
 => 레이아웃에서 부른 `useParams()` 에는 **자식** 세그먼트의 파라미터가 들어가지만,
    그 레이아웃의 클라이언트 params prop(client-segment.tsx L34-36)에는 없다
 ★ getSelectedParams 는 빈 값 세그먼트를 만나면 그 아래를 통째로 건너뛰고(L235 `continue`),
   슬롯끼리 이름이 겹치면 나중 것이 덮어쓴다
```

## 결과가 쓰이는 곳

```text
 pathname · searchParams · pathParams
      --> PathnameContext · SearchParamsContext · PathParamsContext (L554-556)
          --> [04]의 usePathname · useSearchParams · useParams

 layoutRouterContext
      --> LayoutRouterContext (L566) --> [03]의 첫 <LayoutRouter> 가 읽는다
          --> [04]의 useSelectedLayoutSegments 를 **뿌리 레이아웃에서** 부르면 이 값이다

 globalLayoutRouterContext
      --> [03]의 ScrollAndMaybeFocusHandler 가 L480 에서 focusAndScrollRef 를 읽는다
          (InnerLayoutRouter L508-513 은 Context 가 null 인지만 본다).
          `nextUrl` · `previousNextUrl` 필드는 src 안에 읽는 곳이 없다. 개발 도구(segment-explorer-node.tsx L77)와
          hot-reloader 의 web-socket.ts L211 이 tree 를 읽는다

 publicAppRouterInstance (APPRINST L392, 모듈 상수)
      --> AppRouterContext (L565). 값이 **렌더마다 같은 객체**다

 HistoryUpdater (L59-112)
      --> useInsertionEffect 에서 pushState / replaceState 로 주소창을 맞추고
          setLastCommittedTree(tree)(L100)를 부른다.
          nextUrl · tree 가 바뀌면 pingVisibleLinks(L108) — [프리페치]가 보이는 링크를 다시 잰다
```

## 다루지 않는 것

`findHeadInCache` 와 `Head`(L130-149)의 머리 교체, `copyNextJsInternalHistoryState`(L114-128)의 세부, `extractSourcePageFromFlightRouterState`(compute-changed-path.ts L160), `HistoryUpdater` 의 `__NEXT_APP_NAV_FAIL_HANDLING` 갈래와 `setLastCommittedTree`(`committed-state`)의 쓰임, `pingVisibleLinks`(`links.ts`)의 재프리페치, `RootLayoutBoundary` 가 [동적 판별]의 스택 정규식과 맺는 관계(주석 L490-492 가 언급만 한다 — [동적 판별]의 [03 컴포넌트 스택](../../dynamic-rendering/03_stack/README.md) 참고), 개발 서버의 `HotReloader` · `DevRootHTTPAccessFallbackBoundary`(L498-529), `OfflineProvider`(L541-545), `RuntimeStylesForWebpack`(L610-657), `createRootNavigationPromises`(navigation-devtools.ts L84-129)의 캐시 키는 이 문서의 범위 밖이다.
