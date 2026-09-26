# 02 준비

상위: [App Router 가 페이지를 만드는 길](../README.md)

`renderToHTMLOrFlightImpl` 의 앞 225줄(L2562-2786)이다. 렌더 트리가 의지할 것들을 차례로 세운다. **전역을 건드리는 자리가 셋 있다.**

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L2562-L2786 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L2562-L2786))

## 실제 코드

가장 눈에 띄는 것이 이것이다.

```tsx
// app-render.tsx L2600-L2610
  // We need to expose the bundled `require` API globally for
  // react-server-dom-webpack. This is a hack until we find a better way.
  if (ComponentMod.__next_app__) {
    const isTracingEnabled =
      getTracer().getActiveScopeSpan()?.isRecording() ?? false
    installGlobalModuleLoadingHandlers(
      ComponentMod,
      cacheComponents,
      isTracingEnabled
    )
  }
```

```text
 주석 L2600-2601
   "We need to expose the bundled `require` API globally for
    react-server-dom-webpack. This is a hack until we find a better way."

 => RSC 직렬화 런타임이 모듈을 되찾으려면 번들러의 require 가 필요한데
    그것을 넘길 통로가 없어서 **전역에 심는다**. 소스가 스스로 hack 이라고 부른다
```

## 동작 흐름

```text
 renderToHTMLOrFlightImpl  APPR L2562-3088 의 앞부분

 L2577  isNotFoundPath = pagePath === '/404'
 L2579    맞으면 res.statusCode = 404
 L2586  requestTimestamp = Date.now()
          주석 L2582-2585 - 개발에서 한 요청 안에 **일관된** 타임스탬프를 쓴다.
            `<link href="a.css?v={Date.now()}"/>` 가 여러 번 렌더·프리로드될 때
            React Float 이 중복 제거를 못 하는 것을 막는다

 --- 전역 건드리기 1 ---
 L2602  ComponentMod.__next_app__ 이면
 L2605    installGlobalModuleLoadingHandlers(ComponentMod, cacheComponents, isTracingEnabled)

 --- 개발 ISR 표시 ---
 L2612  __NEXT_DEV_SERVER && setIsrStatus && !cacheComponents 이면
 L2615    setIsrStatus(pathname, Edge 면 false 아니면 undefined)
          주석 L2617 - Node 런타임만 ISR 을 쓴다. Edge 는 언제나 동적이다

 --- 응답이 닫힐 때 ---
 L2622  Edge 가 아니고 노드 요청이면
 L2628    res.onClose(() => { workStore.shouldTrackFetchMetrics = false })
            주석 L2629-2630 - 지표는 응답이 닫힐 때 보고하므로 그때 추적을 멈춘다
 L2634    req.originalRequest.on('end', () => {
 L2636      metrics = getClientComponentLoaderMetrics({reset: true})
 L2638      있으면 NextNodeServerSpan.clientComponentLoading 스팬을
              **시작 시각을 과거로 지정해** 만들고 끝낸다
            })

 L2656  metadata = {statusCode: isNotFoundPath ? 404 : undefined, hasPendingUi: false}
 L2661  appUsingSizeAdjustment = !!nextFontManifest?.appUsingSizeAdjust

 --- 전역 건드리기 2 ---
 L2663  ComponentMod.patchFetch()          ★ 전역 fetch 를 갈아끼운다

 --- 전역 건드리기 3 ---
 L2672  enableTainting 이면
 L2673    taintObjectReference(
            'Do not pass process.env to Client Components since it will leak sensitive data',
            process.env)
          ★ process.env 를 통째로 **오염 표시**한다.
            클라이언트 컴포넌트로 넘기면 React 가 막고 이 문장을 띄운다

 L2679  workStore.fetchMetrics = []
 L2680  metadata.fetchMetrics = workStore.fetchMetrics    ★ **같은 배열을 공유한다**
 L2683  query = {...query}                 (원본을 안 건드린다)
 L2684  stripInternalQueries(query)
 L2686  const { isStaticGeneration } = workStore     ★ [03]의 2분기를 가르는 값

 --- 요청 ID ---
 L2690  requestInsightsIdentity = __NEXT_REQUEST_INSIGHTS 이면 getRequestInsightsIdentity()
 L2704  헤더가 준 requestId 가 있으면 그것 (개발)
 L2707  아니고 Request Insights 정체가 있으면 그것
          주석 L2708-2709 - Request Insights 는 work store 가 생기기 **전에**
            기록을 시작한다. 바깥 스코프의 정체를 재사용해 스팬을 모은다
 L2711  아니면 세 갈래로 만든다 (L2713-2723)
          isStaticGeneration 이면  req.url 의 **SHA-1 해시** (결정론적 — 프리렌더 재현용)
          Edge 면                 crypto.randomUUID()
          그 밖이면                nanoid()
        ★ isStaticGeneration 의 **두 번째 사용처**다
 L2731  htmlRequestId 를 정하고
 L2735  workStore.requestId / htmlRequestId 에 기록한다

 --- 문맥 ---
 L2738  getDynamicParamFromSegment = makeGetDynamicParamFromSegment(...)
 L2744  isPossibleActionRequest = getIsPossibleServerAction(req)
 L2748  resolvedPathname = getRequestMeta(req, 'resolvedPathname')
 L2749    없으면 => throw
 L2753  implicitTags = await getImplicitTags(...)
 L2759  ctx: AppRenderContext = { ... }    ★ 아래 전부가 이것을 들고 다닌다
 L2785  getTracer().setRootSpanAttribute('next.route', pagePath)
        ★ [요청 흐름]의 handleRequest 가 `.finally` 에서 읽는 그 값이다.
          스팬 이름이 `GET /blog/[slug]` 로 바뀌는 근거가 여기서 심긴다
```

```text
 ★★ 전역을 셋 건드린다

 L2605  installGlobalModuleLoadingHandlers  번들 require 를 전역에 노출 (소스가 hack 이라 부른다)
 L2663  ComponentMod.patchFetch()           fetch 를 갈아끼운다
 L2673  taintObjectReference(process.env)   전역 객체 하나를 오염 표시

 ★ 그런데 **무조건 매 요청 도는 것은 patchFetch 하나뿐**이다
   L2602  installGlobalModuleLoadingHandlers 는 `if (ComponentMod.__next_app__)` 안
   L2672  taintObjectReference 는 `if (enableTainting)` 안이고
          enableTainting = nextConfig.experimental.taint 인데
          **config-shared.ts 의 defaultConfig 에 taint 항목이 없다** => 기본값 off
 ※ patchFetch 가 멱등인지는 구현을 열어야 안다. 여기서 확인하지 않았다
```

```text
 ★ metadata.fetchMetrics 는 복사가 아니라 **같은 배열**이다 (L2679-2680)

   workStore.fetchMetrics = []
   metadata.fetchMetrics = workStore.fetchMetrics

 => 렌더 도중 workStore 쪽에 push 하면 metadata 에도 보인다.
    렌더가 끝난 뒤 옮겨 담는 단계가 없는 이유다
```

```tsx
// app-render.tsx L2672-L2677
  if (enableTainting) {
    taintObjectReference(
      'Do not pass process.env to Client Components since it will leak sensitive data',
      process.env
    )
  }
```

```text
 => 오염 표시의 메시지가 곧 개발자가 볼 에러 문구다.
    "Do not pass process.env to Client Components since it will leak sensitive data"
 ★ enableTainting 이 꺼져 있으면 이 보호가 **없다**.
   그리고 `experimental.taint` 는 **기본값이 off** 다 (defaultConfig 에 항목이 없다).
   => 이 보호는 켜야 생긴다
```

## 결과가 쓰이는 곳

```text
 isStaticGeneration
      --> [03]의 2분기. 이 파일에서 가장 중요한 한 값이다

 ctx (AppRenderContext)
      --> [03]이 넘기는 모든 함수의 첫째나 둘째 인자다.
          getDynamicParamFromSegment · implicitTags · resolvedPathname 을 담는다

 metadata
      --> RenderResult 에 실려 나간다. statusCode 와 fetchMetrics 가 여기 있다

 workStore.shouldTrackFetchMetrics
      --> 응답이 닫히면 false 가 된다. 그 뒤의 fetch 는 세지 않는다

 patchFetch 로 갈아끼운 전역 fetch
      --> 서버 컴포넌트 안의 모든 fetch 가 캐시·태그·지표를 거치게 된다
```

## 다루지 않는 것

`installGlobalModuleLoadingHandlers`(L2496)의 본문과 `react-server-dom-webpack` 의 모듈 로딩 규약, `ComponentMod.patchFetch()` 가 갈아끼우는 fetch 의 캐시·태그 처리, `taintObjectReference` 의 React 쪽 구현, `makeGetDynamicParamFromSegment`(L596)가 세그먼트를 파라미터로 바꾸는 규칙, `getImplicitTags` 가 만드는 태그의 종류, `AppRenderContext`(L353)의 필드 전체, `createWorkStore` 와 `WorkStore` 의 필드, `stripInternalQueries` 가 지우는 키 목록, `setIsrStatus` 를 읽는 개발 도구, Request Insights 기능 자체는 이 문서의 범위 밖이다.
