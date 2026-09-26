# 04 훅이 Context 에서 값을 꺼낸다

상위: [클라이언트 트리가 라우터 상태를 읽기까지](../README.md)

`next/navigation` 의 훅은 `navigation.ts`(369줄)에 있다. 브라우저에서는 거의 **`useContext` 한 줄**이다. 그런데 같은 파일이 SSR 에도 들어가고, 거기서는 훅이 부른 순간이 **prerender 중인지**를 따져 멈추거나 던진다. 그 판단은 이 파일에 없고 [동적 판별]의 `dynamic-rendering.ts` 에 있다.

## 위치

`packages/next` / `src/client/components` / `navigation.ts` L55-L351 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/navigation.ts#L55-L351))

## 실제 코드

`usePathname()` 이 훅들의 공통 골격을 가장 짧게 보여 준다.

```ts
// navigation.ts L112-L139
export function usePathname(): string {
  useDynamicRouteParams?.('usePathname()')

  // In the case where this is `null`, the compat types added in `next-env.d.ts`
  // will add a new overload that changes the return type to include `null`.
  const pathname = useContext(PathnameContext) as string

  // During build-time instant validation, error if fallback params exist
  // because usePathname() can't return a sensible value without all params.
  if (
    typeof window === 'undefined' &&
    process.env.__NEXT_CACHE_COMPONENTS &&
    pathname
  ) {
    expectCompleteParamsInClientValidation!('usePathname()')
    return pathname
  }

  // Instrument with Suspense DevTools (dev-only)
  if (process.env.NODE_ENV !== 'production' && 'use' in React) {
    const navigationPromises = use(NavigationPromisesContext)
    if (navigationPromises) {
      return use(navigationPromises.pathname)
    }
  }

  return pathname
}
```

```text
 ★★ 네 겹이다 — 그리고 **셋은 브라우저 프로덕션에서 사라진다**

 ① L113  useDynamicRouteParams?.('usePathname()')        서버에서만 실체가 있다   (아래)
 ② L117  useContext(PathnameContext)                     ← 본체는 이 한 줄
 ③ L121  typeof window === 'undefined' && __NEXT_CACHE_COMPONENTS
           => expectCompleteParamsInClientValidation(...)  빌드 때 즉시 검증 (instant-samples.ts L50)
 ④ L131  NODE_ENV !== 'production' && 'use' in React
           => use(navigationPromises.pathname)             Suspense DevTools 용 (개발만)

 ★ ①이 **선택적 호출** `?.()` 인 이유 — 브라우저 번들에서는 그 함수가 `undefined` 다
   navigation-dynamic-rendering.browser.ts L4-5
     export const useDynamicRouteParams = undefined
     export const useDynamicSearchParams = undefined
   build/browser-variant-modules.ts L12 가 이 모듈을 `.browser` 판으로 바꿔 끼우는 목록에 올린다
 => 서버 전용 모듈(`dynamic-rendering.ts`)이 클라이언트 번들에 **안 끌려 들어가게** 한 장치다
 ★ ④는 조건 안에서 `use()` 를 부른다. `process.env.NODE_ENV` 는 빌드 때 고정되므로
   렌더마다 호출 순서가 바뀌지 않는다 ※ (훅 규칙과의 관계는 내 해석이다. 소스는 이유를 안 적는다)
```

```ts
// navigation-dynamic-rendering.ts L1-L11
// Client-safe access to the server-only dynamic-rendering hooks used by the
// navigation hooks. On the server these re-export the real implementations; in
// the browser bundle this module is aliased to
// `./navigation-dynamic-rendering.browser` (see
// scripts/generate-browser-variant-aliases.mjs), which exports `undefined` so
// the server module is not bundled into the client. Callers use optional calls
// (`useDynamicRouteParams?.(...)`), so the browser stub is a no-op.
export {
  useDynamicRouteParams,
  useDynamicSearchParams,
} from '../../server/app-render/dynamic-rendering'
```

## 동작 흐름

```text
 공개 훅 여섯 — 무엇을 읽는가              NAVHOOKS

 L55   useSearchParams()        SearchParamsContext    ① useDynamicSearchParams
                                → useMemo 로 new ReadonlyURLSearchParams(...)  (L63-71)
 L112  usePathname()            PathnameContext        ① useDynamicRouteParams
 L166  useRouter()              AppRouterContext       ① 없음
                                + LayoutRouterContext 의 parentCacheNode.bfcacheId (L179-180)
 L215  useParams()              PathParamsContext      ① useDynamicRouteParams
 L267  useSelectedLayoutSegments(key='children')
                                LayoutRouterContext    ① useDynamicRouteParams
                                → getSelectedLayoutSegmentPath(context.parentTree, key)  (L300)
 L322  useSelectedLayoutSegment(key='children')
                                위 훅을 **부른다**(L327) → computeSelectedLayoutSegment (L350)

 ★ `useDynamicSearchParams` 의 호출처는 useSearchParams **하나**,
   `useDynamicRouteParams` 는 넷이다 (L113 · L216 · L270 · L325 — 저장소 전체 grep)
 ★ useSelectedLayoutSegment 는 L325 에서 한 번, L327 → L270 에서 또 한 번,
   **useDynamicRouteParams 를 두 번** 부른다. expectCompleteParamsInClientValidation 도
   L283 · L332 로 두 번이다
 ★ 서버 컴포넌트가 `next/navigation` 을 import 하면 **이 파일이 아닌 것**을 받는다 —
   webpack 은 create-compiler-aliases.ts L290-293, Turbopack 은 next_import_map.rs L989 · L1020 이
   서버 전용 레이어에서 그것을 `navigation.react-server` 로 바꾼다.
   그 파일(19줄)은 redirect · notFound 류만 내보내고 훅이 **없다**
```

```text
 ★★ null 을 돌려주는 자리가 **Pages Router 용**이다

 L64-67  searchParams 가 없으면 `return null!`
         주석 "When the router is not ready in pages, we won't have the search params available."
 L274    LayoutRouterContext 가 없으면 `return null`
         주석 "This only happens in `pages`. Type is overwritten in navigation.d.ts"

 => 같은 Context 를 Pages Router 도 채운다 — client/index.tsx L311-317 · server/render.tsx L751-757
    (AppRouterContext · SearchParamsContext · PathnameContext · PathParamsContext)
    LayoutRouterContext 는 채우지 않는다 → useSelectedLayoutSegments 가 null
 ★★ 그런데 Pages 의 공급자 `adaptForSearchParams`(shared/lib/router/adapters.tsx L47-55)는
   준비 전이면 **빈** URLSearchParams 를 준다 — null 이 아니다
     if (!router.isReady || !router.query) { return new URLSearchParams() }
 => L64 의 null 갈래는 "준비 전" 이 아니라 **공급자가 아예 없을 때**(Context 기본값 null,
    HOOKCTX L7) 걸린다. 주석과 공급자가 어긋난다
   ★ 이 주석은 **처음부터 사실과 달랐다** — cdf1d52d9ae(#45919, 2023-02-14)에서 들어왔는데,
     그 시점에도 `adaptForSearchParams` 는 준비 전이면 `new URLSearchParams()` 를 줬다
     (efcec4c1e3, 2023-01 부터). 지금 공급자 셋(client/index.tsx L312 · server/render.tsx L752 ·
     app-router.tsx L556)도 null 을 주지 않는다
 ★ Pages Router 에서 `useParams()` 도 null 을 준다 (adapters.tsx L57-60 adaptForPathParams)
 ★ usePathname 쪽은 어댑터(adapters.tsx L92-108)가 fallback 페이지 · 준비 전 자동 정적 최적화에서
   **실제로 null 을 준다**. 그래서 반환형이 호환 타입에서 `string | null` 로 덮인다 (L115-116 주석)
```

`useSearchParams()` 가 서버에서 부르는 판정 함수 전체다.

```ts
// dynamic-rendering.ts L711-L765
export function useDynamicSearchParams(expression: string) {
  const workStore = workAsyncStorage.getStore()
  const workUnitStore = workUnitAsyncStorage.getStore()

  if (!workStore) {
    // We assume pages router context and just return
    return
  }

  if (!workUnitStore) {
    throwForMissingRequestStore(expression)
  }

  switch (workUnitStore.type) {
    case 'validation-client':
      // During instant validation we try to behave as close to client as possible,
      // so this shouldn't hang during SSR.
      return
    case 'prerender-client': {
      React.use(
        makeClientHookHangingPromise(
          workUnitStore.renderSignal,
          new ClientHookDynamicError(workStore.route, expression)
        )
      )
      break
    }
    case 'prerender-legacy':
    case 'prerender-ppr': {
      if (workStore.forceStatic) {
        return
      }
      throw new BailoutToCSRError(expression)
    }
    case 'prerender':
    case 'prerender-runtime':
      throw new InvariantError(
        `\`${expression}\` was called from a Server Component. Next.js should be preventing ${expression} from being included in server components statically, but did not in this case.`
      )
    case 'cache':
    case 'unstable-cache':
    case 'private-cache':
      throw new InvariantError(
        `\`${expression}\` was called inside a cache scope. Next.js should be preventing ${expression} from being included in server components statically, but did not in this case.`
      )
    case 'generate-static-params':
      throw new InvariantError(
        `\`${expression}\` was called in \`generateStaticParams\`. Next.js should be preventing ${expression} from being included in server component files statically, but did not in this case.`
      )
    case 'request':
      return
    default:
      workUnitStore satisfies never
  }
}
```

```text
 ★★★ 같은 "prerender" 라도 **store 종류마다 결말이 다르다**

   (workStore 없음)          => return           주석 L716 "We assume pages router context"
   (workUnitStore 없음)      => throwForMissingRequestStore — "`useSearchParams()` was called
                                outside a request scope." (work-unit-async-storage.external.ts L446-450)
   'validation-client'       => return           주석 L726-727 SSR 중에 멈추지 않게
   'prerender-client'        => React.use(makeClientHookHangingPromise(renderSignal,
                                  new ClientHookDynamicError(route, expression)))
                                **영원히 멈춘다** — 그 컴포넌트가 동적 구멍이 된다
   'prerender-legacy'        \
   'prerender-ppr'           /  forceStatic 이면 return, 아니면
                                => throw new BailoutToCSRError(expression)
   'prerender' · 'prerender-runtime'            => InvariantError  "called from a Server Component"
   'cache' · 'unstable-cache' · 'private-cache' => InvariantError  "called inside a cache scope"
   'generate-static-params'                     => InvariantError
   'request'                 => return           실제 요청이면 아무것도 안 한다

 => 이 둘이 [동적 판별]로 이어진다
    ClientHookDynamicError   → [동적 판별] 03 의 L904 `isClientHookDynamicError` 가 알아보고
                               `<Suspense>` 로 감싸라는 오류로 바꾼다
    BailoutToCSRError        → [정적 응답] 05 · [동적 응답] 04 의 `isBailoutToCSRError` 갈래.
                               `new BailoutToCSRError` 를 만드는 곳은 저장소 전체에 셋이다 —
                               이 L743(throw), 같은 파일 L562(`controller.abort(...)` 의
                               **중단 사유로** 넘긴다 — throw 가 아니다),
                               `next/dynamic` 의 dynamic-bailout-to-csr.tsx L17
 ★ InvariantError 를 던지는 자리 셋(L747 · L753 · L757)은 "Next.js 가 막았어야 했다(should be preventing)" 는 문구다 —
   정상 경로에서는 닿지 않는다는 뜻이다. 서버 컴포넌트는 위 별칭 때문에 훅을 받지 못하고,
   'use cache' 안에서도 렌더되는 것은 서버 컴포넌트다
   ※ 뒷문장(cache 스코프 안에서 클라이언트 훅이 불리지 않는 이유)은 내 해석이다
```

```text
 ★★★ usePathname · useParams 쪽(`useDynamicRouteParams`, DYNR L647-709)은 **훨씬 너그럽다**

                      useDynamicSearchParams       useDynamicRouteParams
   'prerender-client'  언제나 멈춘다 (L729-737)      fallbackRouteParams 가 있을 때만 멈춘다 (L652-666)
   'prerender-ppr'     BailoutToCSRError (L739-743)  fallback 이 있을 때만 postponeWithTracking (L672-681)
   'prerender-legacy'  BailoutToCSRError             break (L701)
   'unstable-cache'    InvariantError (L751)         break (L703)
   workUnitStore 없음  던진다 (L720-722)              아무것도 안 한다 (L650 `workStore && workUnitStore`)

 => 경로 파라미터는 prerender 시점에 **값이 정해져 있을 수 있다**. 모르는 것(fallback)이
    있을 때만 동적으로 떨어진다. 검색 파라미터는 prerender 에 들어올 방법이 없으니
    **거의** 언제나 동적이다 — 예외 하나, `prerender-legacy` · `prerender-ppr` 에서
    `workStore.forceStatic` 이면 그냥 return 한다 (DYNR L740-741)
   ※ 두 함수의 차이를 "검색 파라미터는 빌드 때 알 수 없다" 로 설명한 것은 내 추론이다.
     소스는 차이의 이유를 적지 않는다
 ★ 'prerender-ppr' 에서 두 훅의 수단이 다르다 — 검색 파라미터는 **던지고**(CSR 로 포기),
   경로 파라미터는 **postpone** 한다(그 자리만 구멍). postpone 은 [동적 판별]의 02 가 다룬다
```

`useSelectedLayoutSegments()` 의 실제 계산은 `shared/lib/segment.ts` 에 있다.

```ts
// segment.ts L52-L85
export function getSelectedLayoutSegmentPath(
  tree: FlightRouterState,
  parallelRouteKey: string,
  first = true,
  segmentPath: string[] = []
): string[] {
  let node: FlightRouterState
  if (first) {
    // Use the provided parallel route key on the first parallel route
    node = tree[1][parallelRouteKey]
  } else {
    // After first parallel route prefer children, if there's no children pick the first parallel route.
    const parallelRoutes = tree[1]
    node = parallelRoutes.children ?? Object.values(parallelRoutes)[0]
  }

  if (!node) return segmentPath
  const segment = node[0]

  let segmentValue = getSegmentValue(segment)

  if (!segmentValue || segmentValue.startsWith(PAGE_SEGMENT_KEY)) {
    return segmentPath
  }

  segmentPath.push(segmentValue)

  return getSelectedLayoutSegmentPath(
    node,
    parallelRouteKey,
    false,
    segmentPath
  )
}
```

```text
 ★★ [03]이 좁혀 내려 준 parentTree 에서 **아래로만** 걷는다

 L61   첫 단은 인자로 받은 병렬 라우트 키(기본 'children')로 내려간다
 L65   그 뒤로는 children 을 우선하고, 없으면 **첫 번째 병렬 라우트**를 고른다
         주석 L63 "After first parallel route prefer children, if there's no children
                   pick the first parallel route."
 L71   동적 세그먼트면 값(segment[1])을 쓴다 (getSegmentValue L3-5)
 L73   값이 비었거나 '__PAGE__' 로 시작하면 멈춘다  => 페이지 세그먼트는 **안 들어간다**

 ★ 같은 파일에 `isGroupSegment`(L7-10)가 있지만 여기서 부르지 않는다.
   그래서 `(group)` 같은 라우트 그룹도 결과 배열에 **그대로 들어간다**
 ★★ 단수 훅은 배열에서 **하나를 고르는 규칙이 키마다 다르다** (computeSelectedLayoutSegment L32-49)
     const rawSegment = parallelRouteKey === 'children'
       ? segments[0]
       : segments[segments.length - 1]
   주석 L40 "For 'children', use first segment; for other parallel routes, use last segment"
   그리고 '__DEFAULT__' 면 null 로 바꾼다 (L46-48 — "it's not technically "selected"")
 => 복수 훅은 '__DEFAULT__' 를 거르지 않는다. 이 치환은 **단수 훅에만** 있다
   ※ 복수 훅 결과에 '__DEFAULT__' 가 실제로 나타나는 라우트 모양은 확인하지 않았다
```

```text
 ★★ useRouter() 는 맨 위 객체를 **세그먼트마다 새로 포장한다** (L166-195)

 L167  router = useContext(AppRouterContext)       [02]의 publicAppRouterInstance
 L168  null 이면 => throw 'invariant expected app router to be mounted'
 L179  layout = useContext(LayoutRouterContext)
 L180  bfcacheIdNumber = layout?.parentCacheNode.bfcacheId ?? 0
 L181  return useMemo(() => ({ back, forward, refresh, hmrRefresh, push, replace, prefetch,
                               experimental_gesturePush, bfcacheId: '_b_' + n + '_' }),
                        [router, bfcacheIdNumber])

 주석 L172-178 - "This is contextual: callers in a shared layout get the layout's id;
   callers in a leaf segment get the leaf's. ... The format mirrors React's `useId()`
   (e.g. `_r_0_`) with a `b` prefix"
 ★ 원본 객체의 bfcacheId 는 '0' 으로 박혀 있다 (APPRINST L510-512 "Default value.
   Each route segment provides its own value at runtime. Refer to `useRouter()`.")
 => useRouter() 가 돌려주는 객체는 AppRouterContext 의 값 그 자체가 **아니다**.
    메서드만 옮겨 담은 새 객체다
 ★★ bfcacheId 가 **언제 바뀌는가**는 타입 docstring 이 적는다 (ARCTX L71-88)
   "Changes when the surrounding segment is freshly created by a push or replace
    navigation. Stays the same for back/forward navigations, `router.refresh()`, and
    search-param/hash-only changes."
   용도 — `<form key={useRouter().bfcacheId}>` 로 **새로 이동했을 때만** 상태를 버린다
 => 뒤로/앞으로 가면 같은 id 라 [03]의 bfcache 가 보존한 폼 상태가 그대로 산다
 ★ 값을 **이어받는** 곳이 셋이다 — ppr-navigations.ts L964(공유 레이아웃 reuseSharedCacheNode),
   L1385-1390(검색 파라미터만 바뀜), L1108(히스토리 이동)
 ★ bfcacheId 를 매기는 곳은 ppr-navigations.ts L1370 `generateBFCacheId` —
   서버와 hydration 은 언제나 0 이다 (L1374-1375)
```

## 결과가 쓰이는 곳

```text
 훅의 반환값
      --> 사용자의 클라이언트 컴포넌트

 ReadonlyURLSearchParams (readonly-url-search-params.ts L20-37)
      --> append · delete · set · sort 가 전부 던진다. 읽기만 된다
      ★ 개발 빌드에서는 L87 `use(navigationPromises.searchParams)` 가 돌려주는 것이
        L70 의 객체가 아니라 navigation-devtools.ts L112 에서 **따로 만든** 인스턴스다

 ClientHookDynamicError 로 멈춘 렌더
      --> [동적 판별]의 [03 컴포넌트 스택](../../dynamic-rendering/03_stack/README.md) —
          정적 셸 검증이 이것을 알아보고 `<Suspense>` 처방을 붙인다

 BailoutToCSRError
      --> [정적 응답]의 [05 오류](../../prerender-to-stream/05_error/README.md) ·
          [동적 응답]의 [04 오류 복구](../../render-to-stream/04_error-recovery/README.md)
          가 `isBailoutToCSRError` 로 가른다

 postponeWithTracking (useDynamicRouteParams 의 'prerender-ppr' 갈래)
      --> [동적 판별]의 [02 흐름을 끊는 두 오류](../../dynamic-rendering/02_interrupt/README.md)
```

## 다루지 않는 것

`instant-samples.ts`(125줄)의 즉시 검증 프록시(`createExhaustiveParamsProxy` · `createExhaustiveURLSearchParamsProxy` · `trackMissingSampleErrorAndThrow` 는 `server/app-render/instant-validation/` 에 있다), `makeClientHookHangingPromise` · `ClientHookDynamicError`(`dynamic-rendering-utils.ts`)의 본문, `postponeWithTracking` 의 본문, `navigation-devtools.ts`(179줄)의 약속 캐시(WeakMap 세 개 — L22 · L76 · L131)와 Suspense DevTools 표시, `useServerInsertedHTML`(L142-145 재수출), `unstable_isUnrecognizedActionError`, `navigation.react-server` 가 내보내는 `redirect` · `notFound` 류(API 역인덱스의 서버 쪽 행), `useUntrackedPathname`(navigation-untracked.ts — 오류 경계 전용 내부 훅), Pages Router 의 `useRouter`(`next/router`)와 `PathnameContextProviderAdapter` 의 asPath 처리(adapters.tsx L111-124), `navigation.d.ts` 의 호환 타입 덮어쓰기는 이 문서의 범위 밖이다.
