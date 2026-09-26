# 01 준비와 에러 핸들러

상위: [동적 응답을 스트림으로 내보내기](../README.md)

`renderToStream` 의 앞 180줄(L3270-3449)이다. 브라우저에 실릴 스크립트를 고르고, **스팬을 직접 열고**, 에러를 담을 그릇 둘을 만든다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L3270-L3449 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L3270-L3449))

## 실제 코드

스팬을 `getTracer().wrap` 이 아니라 손으로 연다. 이유가 주석에 있다.

```tsx
// app-render.tsx L3368-L3381
  // Create the "render route (app)" span manually so we can keep it open during streaming.
  // This is necessary because errors inside Suspense boundaries are reported asynchronously
  // during stream consumption, after a typical wrapped function would have ended the span.
  // Note: We pass the full span name as the first argument since startSpan uses it directly.
  const renderSpan = getTracer().startSpan(
    `render route (app) ${pagePath}` as any,
    {
      attributes: {
        'next.span_name': `render route (app) ${pagePath}`,
        'next.span_type': AppRenderSpan.getBodyResult,
        'next.route': pagePath,
      },
    }
  )
```

```text
 주석 L3368-3370
   "Create the "render route (app)" span manually so we can keep it open during
    streaming. This is necessary because errors inside Suspense boundaries are
    reported asynchronously during stream consumption, after a typical wrapped
    function would have ended the span."

 => Suspense 경계 안의 에러는 **스트림이 소비되는 동안 비동기로** 보고된다.
    함수를 감싸는 방식(wrap)은 함수가 반환되면 스팬을 닫아 버려서
    그 에러들을 놓친다. 그래서 직접 열고 나중에 닫는다
 => 이 흐름의 스팬은 [03]과 [04] 곳곳에서 `renderSpan.end()` 로 닫힌다
```

## 동작 흐름

```text
 준비  APPR L3270-3397

 L3272  ctx 에서 뽑는다 — assetPrefix · htmlRequestId · nonce · pagePath
                          renderOpts · requestId · workStore
 L3282  renderOpts 에서 뽑는다 — basePath · buildManifest · createElement
                                crossOrigin · experimental · isBuildTimePrerendering
                                onInstrumentationRequestError · page ...
 L3300  {ServerInsertedHTMLProvider, renderServerInsertedHTML} = createServerInsertedHTML()
 L3302  getServerInsertedMetadata = createServerInsertedMetadata(nonce)
 L3304  tracingMetadata = getTracedMetadata(전파 데이터, experimental.clientTraceMetadata)

 --- 폴리필 ---
 L3309  buildManifest.polyfillFiles 중
 L3311    `.js` 로 끝나고 `.module.js` 가 **아닌** 것만 고른다
 L3315    각각 <script src noModule integrity crossOrigin nonce> 로 만든다
         => `noModule` 이다. 모듈을 아는 브라우저는 건너뛴다

 L3326  [preinitScripts, bootstrapScript] = getRequiredScripts(buildManifest, ...)

 --- 부트스트랩 스크립트 본문 ---
 L3343  __NEXT_DEV_SERVER 이면
 L3344    `self.__next_r=${JSON.stringify(requestId ?? crypto.randomUUID())}`
           주석 L3338-3341 - 부트스트랩 스크립트가 **수화할 때 이 값에 의존한다**.
             그래서 그것보다 먼저 전역에 심는다. MPA 내비게이션(새로고침·직접 입력)에는
             요청 ID 헤더가 없어서 그때는 무작위로 만든다
 L3347  아니고 pagesChunkGroupBootstrapParams 와 chunkLoadingGlobal 이 있으면
 L3351    getTurbopackChunkGroupBootstrap(...)      ★ Turbopack 판이다
 L3362  exposeTestingApi 이면
 L3363    앞의 것에 `;` 를 붙이고 getInstantTestBootstrapScriptContent() 를 이어 붙인다

 --- 스팬 ---
 L3372  renderSpan = getTracer().startSpan(`render route (app) ${pagePath}`, {...})
 L3384  endSpanWithError = (err) => { 예외를 기록하고 ERROR 로 닫는다 }
 L3399  => return getTracer().withSpan(renderSpan, async () => { ... })
          주석 L3397-3398 - 나머지를 스팬 문맥 안에서 돌려야
            자식 스팬("build component tree", "generateMetadata")이 제대로 매달린다
```

```text
 에러 핸들러  APPR L3400-3449

 L3401  {reactServerErrorsByDigest} = workStore    ★ 저장소에서 온다. 여기서 만들지 않는다
 L3404  didErrorObservably = false
         주석 L3403 - "We use this to determine if we should suppress
                       other derivative errors"

 L3405  onHTMLRenderRSCError(err, silenceLog)
 L3406    didErrorObservably = true
 L3407    onInstrumentationRequestError?.(err, req, createErrorContext(ctx, 'react-server-components'), silenceLog)
 L3414  serverComponentsErrorHandler = createReactServerErrorHandler(
           NODE_ENV === 'development', isBuildTimePrerendering,
           reactServerErrorsByDigest, onHTMLRenderRSCError, renderSpan)

 L3422  onHTMLRenderSSRError(err)
 L3425    silenceLog = false
           주석 L3423-3424 - 여기서는 로그를 죽일 필요가 없다.
             RSC 에러 핸들러에서 이미 찍혔다면 이 함수는 **아예 안 불린다**
 L3426    onInstrumentationRequestError?.(err, req, createErrorContext(ctx, 'server-rendering'), false)
 L3434  allCapturedErrors: Array<unknown> = []
 L3435  htmlRendererErrorHandler = createHTMLErrorHandler(
           ..., allCapturedErrors, onHTMLRenderSSRError, renderSpan)

 L3444  reactServerResult = null        (let — [02]가 채운다)
 L3445  reactDebugStream = undefined    (let)
 L3447  setHeader    = res.setHeader.bind(res)
 L3448  appendHeader = res.appendHeader.bind(res)
 L3449  {clientModules} = getClientReferenceManifest()
```

```text
 ★★ 에러 핸들러가 **두 벌**이다. 렌더가 둘이기 때문이다

   serverComponentsErrorHandler  RSC 렌더용    컨텍스트 'react-server-components'
   htmlRendererErrorHandler      HTML 렌더용   컨텍스트 'server-rendering'

 ★ 둘이 `reactServerErrorsByDigest` 를 **공유한다** (L3417 · L3438)
   => RSC 렌더에서 난 에러를 HTML 렌더가 digest 로 알아본다.
      같은 원인을 두 번 보고하지 않으려는 것이다 (주석 L3423-3424 가 그 이야기다)

 ★ 반면 `allCapturedErrors`(L3434)는 HTML 쪽에만 있다
   => [03]의 makeGetServerInsertedHTML 이 이 배열을 받아
      개발 화면에 에러를 심는다
```

```tsx
// app-render.tsx L3447-L3449
    const setHeader = res.setHeader.bind(res)
    const appendHeader = res.appendHeader.bind(res)
    const { clientModules } = getClientReferenceManifest()
```

```text
 => setHeader / appendHeader 를 **미리 묶어 둔다**.
    렌더 도중 preload 헤더 같은 것을 붙일 때 res 를 들고 다니지 않아도 된다
```

## 결과가 쓰이는 곳

```text
 renderSpan
      --> [03]과 [04]가 end() 한다 (L3821 · 3862 · 3932 · 3964 · 4005 · 4069 / L4232 · 4329).
          **[02] 구간에는 end() 가 없다**
          스트림이 끝나야 닫히므로 함수 반환보다 오래 산다

 polyfills · preinitScripts · bootstrapScript · bootstrapScriptContent
      --> [03]의 fizzOptions 와 makeGetServerInsertedHTML 로 간다.
          최종 HTML 의 <script> 들이다

 serverComponentsErrorHandler / htmlRendererErrorHandler
      --> [02]와 [03]이 각각 React 에 onError 로 넘긴다

 allCapturedErrors
      --> [03]의 서버 삽입 HTML 에만 쓰인다 (L3846 · L3884 · L3989 · L4027).
          [04]의 에러 화면은 빈 배열을 넘긴다

 clientModules
      --> [02]가 RSC 페이로드를 직렬화할 때 쓴다. [04]도 쓴다 (L4192 · L4290)
```

## 다루지 않는 것

`createReactServerErrorHandler` / `createHTMLErrorHandler` 의 분류·digest 규칙, `createServerInsertedHTML` / `createServerInsertedMetadata` 의 구현, `getRequiredScripts` 가 매니페스트에서 스크립트를 고르는 규칙과 `preinitScripts` 의 역할, `getTurbopackChunkGroupBootstrap` 과 Turbopack 청크 로딩, `getInstantTestBootstrapScriptContent` 와 Instant Navigation Testing API, `getClientReferenceManifest` 와 `clientModules` 의 형식, `getTracedMetadata` / `clientTraceMetadata`, `onInstrumentationRequestError` 를 심는 쪽(`instrumentation.ts`), `buildManifest` 의 필드 전체는 이 문서의 범위 밖이다.
