# 01 준비

상위: [정적 응답을 미리 만들기](../README.md)

앞 188줄이다. [동적 응답]의 준비와 겹치는 것이 많지만 **두 군데가 다르다** — node/web 갈림을 변수로 올리고, 헤더를 두 곳에 쓴다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L8237-L8424 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L8237-L8424))

## 실제 코드

헤더 함수가 이 흐름의 성격을 그대로 드러낸다.

```tsx
// app-render.tsx L8400-L8418
  const setMetadataHeader = (name: string) => {
    metadata.headers ??= {}
    metadata.headers[name] = res.getHeader(name)
  }
  const setHeader = (name: string, value: string | string[]) => {
    res.setHeader(name, value)
    setMetadataHeader(name)
    return res
  }
  const appendHeader = (name: string, value: string | string[]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        res.appendHeader(name, item)
      })
    } else {
      res.appendHeader(name, value)
    }
    setMetadataHeader(name)
  }
```

```text
 ★★★ 헤더를 **두 곳에** 쓴다

   setHeader(name, value)
     res.setHeader(name, value)      ← 지금의 응답에
     setMetadataHeader(name)          ← metadata.headers 에도

   setMetadataHeader(name)
     metadata.headers ??= {}
     metadata.headers[name] = res.getHeader(name)

 => [동적 응답]은 `res.setHeader.bind(res)` 한 줄이었다 (L3447).
    거기서는 응답이 **살아 있어** 소켓으로 바로 나가기 때문이다
 => 여기서는 결과가 캐시에 저장됐다가 **나중에 재생된다.**
    그때 헤더도 같이 붙어야 하므로 metadata 에 사본을 남긴다
 ★ appendHeader(L8409)는 배열이면 하나씩 append 한다.
   res 의 appendHeader 가 배열을 안 받기 때문이다
```

## 동작 흐름

```text
 APPR L8237-8424

 L8240  formState = null
          주석 L8237-8239 - 프리렌더에서 formState 는 언제나 null 이다.
            그래도 넣어 두는 것은 공유 API 들이 그 값을 기대해서이고,
            선택 인자로 만드는 것보다 이 편이 명시적이기 때문이다

 L8242  ctx 에서 — assetPrefix · getDynamicParamFromSegment · implicitTags
                  nonce · pagePath · renderOpts · workStore
 L8252  renderOpts 에서 — (열두 칸쯤. cacheComponents 도 여기서 온다)
 L8267  {cachedNavigations} = renderOpts.experimental
        => [02]가 StaleTimeIterable 을 붙일지 정할 때 쓴다 (L8836-8839)

 --- ★ node/web 갈림을 변수로 올린다 ---
 L8269  renderFlightStream      = __NEXT_USE_NODE_STREAMS ? renderToNodeFlightStream : renderToWebFlightStream
 L8272  renderFizzStream        = 〃 ? renderToNodeFizzStream : renderToWebFizzStream
 L8275  createInlinedDataStream = 〃 ? createNodeInlinedDataStream : createWebInlinedDataStream

 L8279  allowEmptyStaticShell = (renderOpts.allowEmptyStaticShell ?? false)
                                 || (await isPageAllowedToBlock(tree))
 L8283  rootParams = getRootParams(tree, getDynamicParamFromSegment)
 L8285  {ServerInsertedHTMLProvider, renderServerInsertedHTML} = createServerInsertedHTML()
 L8287  getServerInsertedMetadata = createServerInsertedMetadata(nonce)
 L8289  tracingMetadata = getTracedMetadata(...)
 L8294  polyfills — `.js` 이고 `.module.js` 가 아닌 것만, noModule 로
 L8311  [preinitScripts, bootstrapScript] = getRequiredScripts(...)
 L8323  bootstrapScriptContent = ...
 L8337  exposeTestingApi 이면 테스트 부트스트랩을 이어 붙인다
 L8348  __NEXT_DEV_SERVER 이고 bootstrapScriptContent 가 있으면 ...

 --- 에러 핸들러 ---
 L8354  {reactServerErrorsByDigest} = workStore
 L8356  reportErrors = !experimental.isRoutePPREnabled        ★ 아래 별항
 L8357  onHTMLRenderRSCError(err, silenceLog)
 L8358    reportErrors 일 때만 onInstrumentationRequestError?.(...)
 L8367  serverComponentsErrorHandler = createReactServerErrorHandler(...)
 L8374  onHTMLRenderSSRError(err)
 L8375    **여기도 reportErrors 가드가 있다**
 L8387  allCapturedErrors = []
 L8388  htmlRendererErrorHandler = createHTMLErrorHandler(...)

 --- 상태 변수 넷 ---
 L8396  reactServerPrerenderResult = null
 L8397  reactServerPrerenderResultIsDynamic = null
 L8398  reactServerResumeDataCache = null
 L8399  reactServerPrerenderStore = null

 --- 헤더 함수 셋 ---
 L8400  setMetadataHeader   L8404  setHeader   L8409  appendHeader

 L8420  selectStaleTime = createSelectStaleTime(experimental)
 L8421  {clientModules} = getClientReferenceManifest()
 L8423  prerenderStore = null       (let — 세 갈래가 각자 채운다)
 L8425  try {
```

```tsx
// app-render.tsx L8269-L8277
  const renderFlightStream = process.env.__NEXT_USE_NODE_STREAMS
    ? renderToNodeFlightStream
    : renderToWebFlightStream
  const renderFizzStream = process.env.__NEXT_USE_NODE_STREAMS
    ? renderToNodeFizzStream
    : renderToWebFizzStream
  const createInlinedDataStream = process.env.__NEXT_USE_NODE_STREAMS
    ? createNodeInlinedDataStream
    : createWebInlinedDataStream
```

```text
 ★★ [동적 응답]은 같은 갈림을 `if (__NEXT_USE_NODE_STREAMS) { ... } else { ... }`
    로 **세 번** 썼다 (L3714 · L3806 · L4170).
    여기서는 함수를 변수에 담아 **한 번만** 고른다

 => 결과는 같다. 빌드타임 상수라 번들러가 한쪽을 지운다
 => 다만 본문이 두 벌로 늘어나지 않는다.
    그래서 1996줄인데도 세 갈래가 각각 한 벌씩만 있다
```

```tsx
// app-render.tsx L8355-L8366
  // We don't report errors during prerendering through our instrumentation hooks
  const reportErrors = !experimental.isRoutePPREnabled
  function onHTMLRenderRSCError(err: DigestedError, silenceLog: boolean) {
    if (reportErrors) {
      return onInstrumentationRequestError?.(
        err,
        req,
        createErrorContext(ctx, 'react-server-components'),
        silenceLog
      )
    }
  }
```

```text
 ★★ PPR 이면 에러를 **계측에 보고하지 않는다**

   const reportErrors = !experimental.isRoutePPREnabled

 => RSC 핸들러(L8358)와 SSR 핸들러(L8375) **둘 다** 이 가드를 단다.
    PPR 일 때는 양쪽이 침묵한다
 ★ 바로 위 L8355 에 근거 주석이 있다
     // We don't report errors during prerendering through our instrumentation hooks
 ★ 그런데 주석은 "프리렌더 중" 이라고 말하는데 코드는 `isRoutePPREnabled` 로 건다.
   주석과 조건이 어긋난다 — PPR 이 아닌 프리렌더([04])에서는 보고한다
 ★ [동적 응답]에는 이 가드가 없다 (L3405-3413). 거기서는 언제나 보고한다
```

## 결과가 쓰이는 곳

```text
 renderFlightStream    --> L9300 · L9350 · L9591  (세 갈래 전부)
 createInlinedDataStream --> L9293 · L9548 · L9648
 renderFizzStream      --> **L9604 와 L10152 뿐**
      ★ [02]와 [03]의 HTML 패스는 이것을 안 쓴다.
        `getClientPrerender`(L8670 · L9133 · L9378)를 쓴다 —
        그쪽도 stream-ops.ts 가 node/web 을 골라 준다

 setHeader / appendHeader
      --> 렌더 도중 붙는 헤더가 res 와 metadata.headers **둘 다**에 남는다.
          캐시에서 재생될 때 헤더가 살아 있는 이유다

 prerenderStore (let)
      --> 세 갈래가 각자 자기 종류의 PrerenderStore 를 만들어 여기 대입한다.
          [05]의 catch 가 그것을 읽는다

 allowEmptyStaticShell
      --> 셸이 비어도 되는지. 이 함수 안에서 읽는 곳은 **L9206 하나**,
          즉 [02] 전용이다 (throwIfDisallowedDynamic). [03]·[04]는 안 본다
```

## 다루지 않는 것

`isPageAllowedToBlock` 의 판정과 `allowEmptyStaticShell` 의 쓰임새, `createSelectStaleTime` / `getRootParams` / `getTracedMetadata` 의 구현, `createReactServerErrorHandler` / `createHTMLErrorHandler` 의 분류 규칙([동적 응답] 01 과 같다), `PrerenderStore` 의 종류(`PrerenderStoreModernServer` 등)와 필드, `getRequiredScripts` 와 부트스트랩 스크립트 선택, `metadata.headers` 를 나중에 읽어 재생하는 쪽(응답 캐시), `res.appendHeader` 가 배열을 못 받는 이유는 이 문서의 범위 밖이다.
