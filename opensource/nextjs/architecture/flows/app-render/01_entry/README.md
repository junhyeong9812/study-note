# 01 진입과 헤더 읽기

상위: [App Router 가 페이지를 만드는 길](../README.md)

`renderToHTMLOrFlight` 는 99줄이다. 렌더를 하지 않는다. **헤더를 플래그로 바꾸고, 저장소를 만들고, 그 안에서 진짜 함수를 부른다.**

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L3101-L3199 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L3101-L3199))

`packages/next` / `src/server/app-render` / `app-render.tsx` L444-L522 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L444-L522))

## 실제 코드

마지막 스무 줄이 이 함수의 요점이다.

```tsx
// app-render.tsx L3180-L3198
  return workAsyncStorage.run(
    workStore,
    // The function to run
    renderToHTMLOrFlightImpl,
    // all of it's args
    req,
    res,
    url,
    pagePath,
    query,
    renderOpts,
    workStore,
    parsedRequestHeaders,
    postponedState,
    serverComponentsHmrCache,
    sharedContext,
    interpolatedParams,
    fallbackRouteParams
  )
```

```text
 workAsyncStorage.run(workStore, renderToHTMLOrFlightImpl, ...인자 13개)

 => AsyncLocalStorage 다. 이 호출 안에서 **동기적으로 이어지는** 코드가
    workAsyncStorage.getStore() 로 workStore 에 닿는다.
 ★ 다만 I/O 이벤트로 나중에 불리는 콜백은 이 문맥 밖이다 —
   [02]의 res.onClose(L2628) · req.on('end')(L2634 · L2926)가 그렇다.
   셋 다 getStore() 대신 **클로저로 잡은 변수**를 쓴다 (L2631 · L2928)
   (※ 런타임으로 실증하지는 않았다. 코드 정황이 근거다)
 => 서버 컴포넌트가 revalidate 를 기록하거나 fetch 를 세는 통로다
 => 인자를 13개나 명시적으로 넘기면서도 저장소를 따로 두는 것은,
    렌더 트리 **안쪽**에서는 인자를 받을 길이 없기 때문이다
```

## 동작 흐름

```text
 renderToHTMLOrFlight  APPR L3101-3199

 L3111  req.url 이 없으면         => throw new Error('Invalid URL')
 L3115  url = parseRelativeUrl(req.url, undefined, false)
 L3119  parsedRequestHeaders = parseRequestHeaders(req.headers, {
          isRoutePPREnabled: renderOpts.experimental.isRoutePPREnabled === true,
          previewModeId: renderOpts.previewProps?.previewModeId,
        })

 L3132  renderOpts.postponed 이 **문자열**이면      (PPR 재개 요청)
        ★ 이 값이 있으면 app-page-runtime.ts L874-875 가
          supportsDynamicResponse 를 강제로 켠다 => [03]의 **아래쪽 갈래**로 간다
 L3133    fallbackRouteParams 도 있으면
 L3134      => throw new InvariantError('postponed state should not be provided
                                         when fallback params are provided')
 L3139    interpolatedParams = interpolateParallelRouteParams(loaderTree, params, pagePath, ...)
 L3146    postponedState = parsePostponedState(renderOpts.postponed,
                                                interpolatedParams,
                                                maxPostponedStateSizeBytes)
 L3151  아니면
 L3152    interpolatedParams 만 만든다

 L3160  postponedState.renderResumeDataCache 와 renderOpts.renderResumeDataCache 가
        **둘 다** 있으면
 L3164    => throw new InvariantError('postponed state and dev warmup immutable
                                       resume data cache should not be provided together')

 L3169  workStore = createWorkStore({page, renderOpts, isPrefetchRequest,
                                     buildId, deploymentId,
                                     previouslyRevalidatedTags, nonce})
 L3180  => return workAsyncStorage.run(workStore, renderToHTMLOrFlightImpl, ...)
```

```text
 ★ 이 함수의 출구는 넷인데 셋이 throw 다
   L3112  'Invalid URL'
   L3134  InvariantError — postponed 와 fallback 파라미터가 같이 왔다
   L3164  InvariantError — postponed 와 dev warmup 캐시가 같이 왔다
   L3180  정상

 => 셋 다 **있으면 안 되는 조합**을 막는다. 값을 고치지 않고 즉시 죽는다
```

## 헤더를 플래그로 바꾼다

```tsx
// app-render.tsx L448-L462
  const isRSCRequest = isRSCRequestHeader(headers[RSC_HEADER])

  // runtime prefetch requests are *not* treated as prefetch requests
  // (TODO: this is confusing, we should refactor this to express this better)
  const isPrefetchRequest =
    isRSCRequest && headers[NEXT_ROUTER_PREFETCH_HEADER] === '1'

  const isAppShellPrefetchRequest =
    isRSCRequest && headers[NEXT_ROUTER_PREFETCH_HEADER] === '3'

  // App Shell prefetches are a subtype of runtime prefetch — same code path,
  // but with less resolved content (omitting link data)
  const isRuntimePrefetchRequest =
    isRSCRequest &&
    (headers[NEXT_ROUTER_PREFETCH_HEADER] === '2' || isAppShellPrefetchRequest)
```

```text
 ★★★ 프리페치 헤더 하나가 값에 따라 **세 가지**를 뜻한다

   NEXT_ROUTER_PREFETCH_HEADER === '1'  ->  isPrefetchRequest
   NEXT_ROUTER_PREFETCH_HEADER === '2'  ->  isRuntimePrefetchRequest
   NEXT_ROUTER_PREFETCH_HEADER === '3'  ->  isAppShellPrefetchRequest
                                            (그리고 이것도 runtime 으로 친다)

 [응답 흐름]의 CDN 방어(L2153)가 "'1' '2' '3' 만 인정한다" 고 한 그 값들이다

 ★ 소스가 스스로 이 이름을 문제 삼는다 — 주석 L450-451
   "runtime prefetch requests are *not* treated as prefetch requests
    (TODO: this is confusing, we should refactor this to express this better)"
 => isRuntimePrefetchRequest 가 참이어도 isPrefetchRequest 는 거짓이다.
    둘은 배타다. 이름만 보면 포함 관계로 읽힌다
 ★ 반면 App Shell(3)은 runtime(2)에 **포함된다** (L460-462)
   주석 L458-459 - "App Shell prefetches are a subtype of runtime prefetch —
     same code path, but with less resolved content (omitting link data)"
```

```tsx
// app-render.tsx L466-L475
  const shouldProvideFlightRouterState =
    isRSCRequest && (!isPrefetchRequest || !options.isRoutePPREnabled)

  const flightRouterState = shouldProvideFlightRouterState
    ? parseAndValidateFlightRouterState(headers[NEXT_ROUTER_STATE_TREE_HEADER])
    : undefined

  // Checks if this is a prefetch of the Route Tree by the Segment Cache
  const isRouteTreePrefetchRequest =
    isRSCRequest && headers[NEXT_ROUTER_SEGMENT_PREFETCH_HEADER] === '/_tree'
```

```text
 L466  shouldProvideFlightRouterState = isRSCRequest && (!isPrefetchRequest || !isRoutePPREnabled)
 => 프리페치이면서 PPR 이 켜진 라우트면 라우터 상태를 **넘기지 않는다**.
    PPR 은 어느 세그먼트에 있는지와 무관하게 같은 껍데기를 주기 때문이다
    (※ 뒷문장은 내 해석이다)

 L474  isRouteTreePrefetchRequest = isRSCRequest && 세그먼트 프리페치 헤더 === '/_tree'
 => 세그먼트 캐시가 **라우트 트리만** 미리 받아 가는 요청이다
```

```text
 그 밖에 뽑는 것

 L464  isHmrRefresh = NEXT_HMR_REFRESH_HEADER 가 있는가
 L477  csp = 'content-security-policy' || 'content-security-policy-report-only'
 L481  nonce = csp 가 문자열이면 getScriptNonceFromHeader(csp)
       => **CSP 헤더에서 nonce 를 뽑아** 렌더가 심을 스크립트에 붙인다
 L484  previouslyRevalidatedTags = getPreviouslyRevalidatedTags(headers, previewModeId)
 L492  __NEXT_DEV_SERVER 이면 requestId / htmlRequestId 를 헤더에서 읽는다
       주석 L493-496 - 개발 서버가 **디버그 정보를 맞는 클라이언트에 보내려고** 쓴다.
         htmlRequestId 는 HTML 문서와 함께 보낸 것, requestId 는 클라이언트가 정한 것
 L509  => return 열한 칸짜리 객체
```

## 결과가 쓰이는 곳

```text
 parsedRequestHeaders
      --> [03]의 갈림길이 전부 이 플래그를 본다.
          isRSCRequest / isRuntimePrefetchRequest / isAppShellPrefetchRequest 가
          RSC 네 갈래를 가른다

 workStore
      --> AsyncLocalStorage 로 렌더 트리 전체가 공유한다.
          [02]가 fetchMetrics 와 isStaticGeneration 을 여기서 꺼낸다

 postponedState
      --> PPR 재개. [응답 흐름]의 x-matched-path 블록이 본문에서 읽어
          요청 메타에 심은 그 값이 여기까지 왔다

 interpolatedParams
      --> 동적 세그먼트의 실제 값. [02]의 getDynamicParamFromSegment 가 쓴다

 nonce
      --> 렌더가 만드는 <script> 에 붙는다. CSP 를 통과시키려는 것이다
```

## 다루지 않는 것

`createWorkStore` 가 만드는 `WorkStore` 의 필드 전체와 `workAsyncStorage` 의 구현, `interpolateParallelRouteParams` 가 병렬 라우트 파라미터를 채우는 규칙, `parsePostponedState`(`postponed-state.ts` 327줄)의 형식과 `maxPostponedStateSizeBytes` 검사, `parseAndValidateFlightRouterState` 의 검증 규칙과 `FlightRouterState` 의 구조, `getPreviouslyRevalidatedTags` 와 프리뷰 모드, `getScriptNonceFromHeader` 의 CSP 파싱, `parseRelativeUrl` 의 동작은 이 문서의 범위 밖이다.
