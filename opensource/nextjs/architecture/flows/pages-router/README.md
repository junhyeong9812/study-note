# Pages Router 가 페이지를 그리기까지

상위: [Next.js 아키텍처 지도](../../README.md)

`pages/` 디렉터리의 페이지는 App Router 와 **같은 문으로 들어와 같은 응답 캐시를 거친 뒤**, 전혀 다른 렌더러로 갈라진다. 서버는 데이터 함수를 부르고 HTML 을 **문자열 하나로** 만든다. 브라우저는 그 안의 `__NEXT_DATA__` 를 읽어 하이드레이트하고, 그 뒤의 이동은 **클래스 하나(`Router`)** 가 맡는다. [클라이언트 라우터]의 리듀서 + 액션 큐와 나란히 놓고 읽으면 값어치가 있다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `PTPL` = `build/templates/pages.ts`(74줄), `PHAND` = `server/route-modules/pages/pages-handler.ts`(832줄), `PMOD` = `server/route-modules/pages/module.ts`(164줄), `RMOD` = `server/route-modules/route-module.ts`(1179줄), `PRENDER` = `server/render.tsx`(1643줄), `CINDEX` = `client/index.tsx`(1003줄), `PROUTER` = `shared/lib/router/router.ts`(2666줄), `CROUTER` = `client/router.ts`(195줄), `PLOADER` = `client/page-loader.ts`(214줄), `ADAPT` = `shared/lib/router/adapters.tsx`(131줄), `PATPL` = `build/templates/pages-api.ts`(212줄), `PAPIMOD` = `server/route-modules/pages-api/module.ts`(164줄), `APIRES` = `server/api-utils/node/api-resolver.ts`(489줄), `BASE` = `server/base-server.ts`(3195줄), `NEXTSRV` = `server/next-server.ts`(2195줄).

## 위치

`packages/next` / `src/server/route-modules/pages` / `pages-handler.ts` L52-L832 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/route-modules/pages/pages-handler.ts#L52-L832))

## 실제 코드

페이지 하나가 번들이 되면 이 템플릿이 된다. 사용자 모듈을 끌어올려(`hoist`) 다시 내보내고, 끝에 `handler` 를 붙인다.

```ts
// pages.ts L46-L74
// Create and export the route module that will be consumed.
export const routeModule = new PagesRouteModule({
  definition: {
    kind: RouteKind.PAGES,
    page: 'VAR_DEFINITION_PAGE',
    pathname: 'VAR_DEFINITION_PATHNAME',
    // The following aren't used in production.
    bundlePath: '',
    filename: '',
  },
  distDir: process.env.__NEXT_RELATIVE_DIST_DIR || '',
  relativeProjectDir: process.env.__NEXT_RELATIVE_PROJECT_DIR || '',
  components: {
    // default export might not exist when optimized for data only
    App: app.default,
    Document: document.default,
  },
  userland,
})

export const handler = getHandler({
  srcPage: 'VAR_DEFINITION_PAGE',
  config,
  userland,
  routeModule,
  getStaticPaths,
  getStaticProps,
  getServerSideProps,
})
```

```text
 ★★ 라우트 모듈에 `_app` 과 `_document` 가 **같이 들어간다** (PTPL L6-8, L58-62)
   import * as document from 'VAR_MODULE_DOCUMENT'
   import * as app from 'VAR_MODULE_APP'
 => 페이지마다 자기 번들 안에 App 과 Document 를 쥐고 있다.
    PMOD render(L136-154)가 그 둘을 renderToHTMLImpl 의 `extra` 로 넘긴다
 ★ 주석 L59 - "default export might not exist when optimized for data only"

 ★★ `handler` 는 getHandler 가 만든 **클로저**다 (PHAND L52-832, 781줄)
   바깥 함수는 인자 여덟을 받아 두고 `return async function handler(req, res, ctx)`
   (L71-831, 761줄) 하나를 돌려준다. 요청마다 도는 것은 안쪽이다
 ★ 템플릿은 getHandler 에 인자 일곱만 넘긴다 — `isFallbackError` 는 빠진다 (L66-74)
   그것을 `true` 로 넘기는 곳은 내장 에러 페이지 하나다
     server/route-modules/pages/builtin/_error.tsx L28-34 (`packages/next/src` 비테스트 grep `getHandler(` 두 건)
```

## 동작 흐름

```text
 ★★★ App 과 Pages 가 **처음** 갈리는 자리는 컴포넌트를 찾을 때다
   ★ 한 번으로 끝나지 않는다 — 그 뒤에도 renderToResponseWithComponentsImpl 이 isAppPath 로
     여러 번 더 갈린다 (BASE L2127 · L2226 setVaryHeader · L2427 · L2461 · L2484).
     [응답 나가기] 02_delegate 가 적은 L2484 의 app 갈래가 그중 하나다

 [요청 -> 렌더] 가 BASE renderPageComponent 까지 온다
 BASE L2646  appPaths  = this.getOriginalAppPaths(pathname)
 BASE L2647  isAppPath = Array.isArray(appPaths)
 BASE L2655  this.findPageComponents({ ..., isAppPath, ... })
               NEXTSRV findPageComponentsImpl L854 -> loadComponents(...)
               => app 이면 app-page 템플릿, 아니면 이 흐름의 pages 템플릿을 싣는다
 BASE L2669  this.renderToResponseWithComponents(ctx, result)
   +-- [응답 나가기] 의 renderToResponseWithComponentsImpl
         BASE L2400  Component 가 **문자열**이면 => RenderResult.fromStatic   (아래 ★)
         BASE L2603  await components.ComponentMod.handler(handlerReq, handlerRes, {...})
                       ↑ 여기서부터 이 흐름이다. 두 라우터가 **같은 한 줄**로 들어온다
                         (노드 런타임 한정 — Edge 페이지는 [응답 나가기] 가 적은 대로
                          NEXTSRV renderPageComponent L781 에서 먼저 가로채인다)

 ★ `pages/api` 는 이 길로 안 온다 — NEXTSRV L1179 에서 먼저 빠진다   [04]
```

```text
 handler (PHAND L71-831)

 L102  routeModule.prepare(req, res, {srcPage, multiZoneDraftMode})
         RMOD L713-717  pathname 이 /_next/data 로 시작하면 isNextDataRequest = true
 L107  prepareResult 가 없으면 => 400 'Bad Request'
 L170  hasServerProps / hasStaticProps / hasStaticPaths / hasGetInitialProps
 L185  cacheKey 는 **!isDev && !isDraftMode && hasStaticProps 일 때만** 만든다
 L200  getStaticPaths 가 있으면 prerenderManifest.dynamicRoutes[srcPage] 를 본다
 L213    fallback === false 이고 미리 안 만든 경로면 => throw NoFallbackError
 L220    fallback 이 문자열이고 미리 안 만든 경로이고 data 요청이 아니면  isIsrFallback = true   (L220-224)
 L233  봇이거나 minimalMode 면 isIsrFallback = false  (주석 L230-232)
 L257  handleResponse = async (span) => {
 L258    responseGenerator = async ({previousCacheEntry}) => {
 L261      doRender = () => routeModule.render(req, res, {...})         [01]
 L372        .then(renderResult => ResponseCacheEntry)   PAGES / REDIRECT / null
 L456      isIsrFallback 이면 fallback 셸을 **srcPage 키로** 캐시에서 꺼낸다
 L528      => return doRender()
 L532    result = await routeModule.handleResponse({cacheKey, responseGenerator, ...})
 L557    SSG 면 x-nextjs-cache: REVALIDATED / MISS / STALE / HIT
 L572    Cache-Control 을 고른다 (SSG 가 아니거나 fallback 이면 revalidate 0)
 L617    value 가 null 이면 404       (data 요청이면 '{"notFound":true}')
 L640    REDIRECT 면 data 요청은 JSON, 아니면 Location 헤더
 L719    await sendRenderResult({ result: data 요청이면 pageData JSON, 아니면 html })
       }
```

```text
 ★★★ 응답 캐시는 두 라우터가 **같은 메서드**로 쓴다

 RMOD handleResponse L1109-1178 을 부르는 곳 (저장소 전체 grep `\.handleResponse(`)
   PHAND L532                        Pages Router
   build/templates/app-page-runtime.ts L1252 · L1609   App Router 페이지
   build/templates/app-route.ts L408                    라우트 핸들러
 => 넷이 전부 RouteModule 의 한 메서드로 ResponseCache.get 에 닿는다 — 그 밖에 **직접** 부르는
    자리도 있다. Pages 는 ISR fallback 셸을 가져올 때 `routeModule.getResponseCache(req).get(...)`
    (PHAND L457), App 은 app-page-runtime.ts L1306 · L1416
 ★ 인스턴스는 공유하지 않는다 — RMOD L1101-1107 getResponseCache 가
   `this.responseCache` 에 **라우트 모듈마다** 하나씩 만든다
 ★ IncrementalCache 는 호출마다 새로 만든다. 주석 L504-506 -
   "incremental-cache is request specific although can have shared caches in
    module scope per-cache handler"

 ★★ 그런데 Pages 는 cacheKey 를 **SSG 에서만** 만든다 (PHAND L185)
   getServerSideProps · getInitialProps 페이지는 cacheKey = null
   response-cache/index.ts L221-226  key 가 없으면 캐시를 안 보고 responseGenerator 를 그대로 부른다
 => [응답 나가기] 의 캐시 판정은 Pages 에서 **`getStaticProps` 페이지 전용**이다
```

```text
 ★★★ 같은 캐시 항목이 **HTML 과 JSON 을 둘 다** 들고 있다 (PHAND L414-423)

   value: { kind: PAGES, html: renderResult, pageData: metadata.pageData, headers, status }

 L725  isNextDataRequest && !isErrorPage && !is500Page
         ? new RenderResult(JSON.stringify(result.value.pageData), ...)
         : result.value.html
 => `/blog/a` 와 `/_next/data/<buildId>/blog/a.json` 이 **같은 cacheKey 로 한 항목을 본다**
    cacheKey 의 재료 resolvedPathname 은 요청 URL 이 아니라 srcPage 에 params 를 채워 만든다
    (RMOD L1028-1058). 그래서 URL 모양이 달라도 키가 같다
 => SSG 는 data 요청이어도 HTML 까지 렌더한다 (PRENDER L1226 의 조기 return 이 `!isSSG` 일 때만이다)
    ※ "한 항목에 둘 다 담아야 해서" 라는 이유는 내 추론이다. 소스는 이유를 적지 않는다
    반대로 getServerSideProps 의 data 요청은 HTML 렌더를 **건너뛴다**   [01]
```

```text
 ★★ 자동 정적 최적화 페이지는 (프로덕션에서) handler 에 **닿지도 않는다**

 require.ts L121   pagePath 가 .html 로 끝나면 파일을 **문자열로** 읽어 돌려준다
 BASE L2400        if (typeof components.Component === 'string')
 BASE L2402          => RenderResult.fromStatic(components.Component, HTML_CONTENT_TYPE_HEADER)
 => 데이터 함수가 없는 페이지는 빌드 때 HTML 파일이 되고, 요청 때는 base-server 가
    그 파일을 그대로 보낸다. [응답 나가기] 가 센 "payload 를 만드는 자리 넷" 중 하나다
 ★ .html 이 되는 조건 (build/index.ts L2641-2647 · build/utils.ts L975-978) — getStaticProps ·
   getInitialProps · getServerSideProps 가 모두 없고, **사용자 `_app` 에 getInitialProps 가 없고**,
   서버 컴포넌트가 아닐 때다. `_app` 하나에 gIP 가 있으면 모든 페이지가 .html 이 되지 않는다
 ★ 개발에서는 .html 파일이 없어 handler 까지 온다 — render.tsx L639 · L852 가 그 갈래를 처리한다
```

1. [서버에서 HTML 을 만든다](01_render/README.md) — 데이터 함수의 순서와, 문자열 두 개를 이어 붙이는 문서 렌더.
2. [브라우저가 하이드레이트한다](02_hydrate/README.md) — `__NEXT_DATA__` 에서 시작해 `hydrateRoot` 한 번.
3. [클라이언트가 이동한다](03_navigate/README.md) — 719줄짜리 `change` 와 하드 내비게이션 열네 자리.
4. [API 라우트](04_api/README.md) — 응답 캐시도 렌더도 없는 곁길.

```text
 ★★★ 두 라우터의 클라이언트 모양 (대비)

                    App Router ([클라이언트 라우터])        Pages Router (이 흐름)
 상태가 사는 곳     모듈 전역 액션 큐                     Router 인스턴스의 `private state` 와
                                                         그 밖의 인스턴스 필드(isReady · isSsr · components ·
                                                         sdc/sbc — router.ts L723 · L1240)
 바꾸는 방법        액션 6종 -> 리듀서 switch             push/replace -> change() 한 메서드
 React 에 알림      useActionQueue 가 구독                this.sub(...) 콜백이 root.render 를 직접 부른다
 서버에서 받는 것   RSC 페이로드(트리 조각)               /_next/data/<buildId>/<path>.json (props 만)
 페이지 코드        (이 흐름에서 확인하지 않았다)          page-loader 가 페이지 청크를 따로 싣는다

 => Pages 의 이동은 "데이터 JSON + 페이지 청크" 를 받아 **App 컴포넌트를 통째로 다시 그린다**
 ★ 두 라우터는 서로의 기록(history.state)을 모른다 — PROUTER L927-930
     if (state.__NA) { window.location.reload(); return }
   `__NA` 는 App Router 가 심는다 (client/components/app-router.tsx L84)
```

## 결과가 쓰이는 곳

```text
 sendRenderResult 로 나간 HTML
      --> 브라우저가 받아 `<script id="__NEXT_DATA__">` 를 읽는다          [02]

 sendRenderResult 로 나간 pageData JSON (/_next/data 요청)
      --> 클라이언트 Router 의 fetchNextData 가 받는다                        [03]

 ResponseCacheEntry (kind PAGES · REDIRECT · null)
      --> RouteModule.handleResponse 를 거쳐 IncrementalCache 에 저장된다.
          [응답 나가기] 가 다루는 캐시 계층이다

 x-nextjs-cache 헤더
      --> SSG 페이지에서만 붙는다 (L557). res.revalidate 가 내부 경로 없이
          HEAD 요청으로 재검증할 때(trustHostHeader) 이 값을 읽어 성공을 판정한다   [04]

 NoFallbackError
      --> handler 밖으로 던져진다(L736 은 이것만 onRequestError 에서 뺀다).
          BASE renderPageComponent L2670-2678 이 받아, bubbleNoFallback 이 아니면
          삼키고 false("내 것이 아니다, 다음 매치로")를 돌려준다
```

## 다루지 않는 것

`RouteModule.prepare`(RMOD L594)의 URL 정규화·i18n·파라미터 추출 본문, `ResponseCache.get` 과 `IncrementalCache` 의 저장 규칙(응답 캐시 계층 자체), PHAND 의 트레이싱(L757-803 · L806-830)과 `render404` 가 App Router not-found 로 넘기는 경로(L116-138, 주석 L119-126), Edge 런타임 페이지(`next-edge-ssr-loader`)와 `export/routes/pages.ts` 의 빌드 시점 prerender(`lazyRenderPagesPage` 를 부른다), `getStaticPaths` 를 빌드 때 부르는 쪽(`build/utils.ts`)과 `prerender-manifest.json` 의 구조, `loadComponents` 와 `requirePage` 가 매니페스트에서 파일을 고르는 방식, next.config 의 `i18n` · `basePath` · `trailingSlash` 가 URL 을 바꾸는 세부, 개발 서버의 on-demand 컴파일과 HMR, `next/link` · `next/head` · `next/script` · `next/dynamic` 컴포넌트 자체는 이 흐름의 범위 밖이다. minimal mode(`x-nextjs-cache` · isIsrFallback · 응답 캐시 동작이 달라진다)와 adapter(`nextConfig.adapterPath` — next-server 없이 handler 를 직접 부르는 진입)도 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 서버에서 HTML 을 만든다](01_render/README.md)
- [02 브라우저가 하이드레이트한다](02_hydrate/README.md)
- [03 클라이언트가 이동한다](03_navigate/README.md)
- [04 API 라우트](04_api/README.md)
