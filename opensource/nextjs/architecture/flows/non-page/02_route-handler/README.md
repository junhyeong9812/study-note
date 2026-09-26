# 02 라우트 핸들러

상위: [페이지가 아닌 요청이 처리되기까지](../README.md)

`app/**/route.ts` 의 `GET` · `POST` 는 페이지와 **같은 길**로 base-server 를 지나 `ComponentMod.handler` 에 닿는다. 갈라지는 것은 그 `handler` 가 어느 템플릿에서 왔느냐다. 그리고 "이 라우트가 정적인가" 를 페이지와 다르게 판정한다 — **기본이 동적**이고, 정적 생성을 켰을 때만 **요청 객체를 Proxy 로 감싸** 무엇을 읽는지 지켜본다.

★★★ 빌드의 1차 관문 — 설정이 없는 평범한 `GET` 은 **정적 생성을 시도조차 하지 않는다**. export 워커(`export/routes/app-route.ts` L106-116)가 `isStaticGenEnabled(userland)` 가 거짓이고 cacheComponents 도 꺼져 있으면 `handle` 을 **부르지 않고** `revalidate: 0` 을 돌려준다. 켜지는 조건은 `dynamic` 이 'force-static' · 'error' 이거나, `revalidate` 가 false 또는 0 보다 크거나, `generateStaticParams` 가 있을 때다 (helpers/is-static-gen-enabled.ts L13-19). 주석 L109-112 가 이유를 적는다 — "the cache surprises that led to us removing static gen unless specifically opted into".

## 위치

`packages/next` / `src/build/templates` / `app-route.ts` L105-L602 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/templates/app-route.ts#L105-L602))

`packages/next` / `src/server/route-modules/app-route` / `module.ts` L757-L943 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/route-modules/app-route/module.ts#L757-L943))

`packages/next` / `src/server/route-modules/app-route` / `module.ts` L369-L755 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/route-modules/app-route/module.ts#L369-L755))

`packages/next` / `src/server/route-modules/app-route` / `module.ts` L1277-L1349 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/route-modules/app-route/module.ts#L1277-L1349))

## 실제 코드

`handle()` 이 핸들러를 부르기 전에 먼저 보는 것이다.

```ts
// module.ts L831-L843
            const hasNonStatic = liveUserland
              ? hasNonStaticMethods(liveUserland)
              : this._hasNonStaticMethods
            if (hasNonStatic) {
              if (workStore.isStaticGeneration) {
                const err = new DynamicServerError(
                  'Route is configured with methods that cannot be statically generated.'
                )
                workStore.dynamicUsageDescription = err.message
                workStore.dynamicUsageStack = err.stack
                throw err
              }
            }
```

```text
 ★★★ POST 하나만 export 해도 **GET 까지 정적 생성에서 빠진다**

 hasNonStaticMethods  ARMOD L955-967
   handlers.POST || handlers.PUT || handlers.DELETE || handlers.PATCH || handlers.OPTIONS
   => 다섯 중 하나라도 있으면 true
 => 판정 단위가 **메서드가 아니라 파일**이다. 정적 생성 중(isStaticGeneration)에
    GET 을 부르려 해도, 같은 파일에 POST 가 있으면 L836 에서 DynamicServerError 를 던진다
 ★ 이 검사는 사용자 모듈(userland)을 본다. 자동으로 만들어지는 OPTIONS(아래 AUTOIMPL)는 세지 않는다.
   사용자가 OPTIONS 를 **직접** export 해야 정적에서 빠진다
 ★ docstring L948-954 는 "Gets all the method names ... @returns the method names that
   are not considered static or false if all methods are static" 라고 적지만
   반환형은 `boolean` 이고 이름 목록을 돌려주지 않는다
```

## 동작 흐름

```text
 ① 템플릿 handler — 캐시할지 정한다  ARTPL L105-602

 L119   srcPage = 'VAR_DEFINITION_PAGE'   (Turbopack 은 /index 를 떼고, webpack 은 /index 만 '/' 로)
 L133   prepareResult = await routeModule.prepare(req, res, {srcPage, multiZoneDraftMode})
 L138   없으면 400 'Bad Request'                               => return null
 L163   isIsr = prerenderManifest.dynamicRoutes[normalizedSrcPage]
                || prerenderManifest.routes[resolvedPathname]
          ★ 런타임 템플릿 안에서는 "빌드 때 prerender 매니페스트에 들어갔는가" 가 정적 여부의
            **유일한 입력**이다. 빌드에서 그것을 정하는 1차 관문은 위 리드의 isStaticGenEnabled 다
 L178   isIsr && !isDraftMode 이고 fallback: false 인데 미리 만든 경로가 아니면
 L184     adapterPath 가 있으면 render404                       => return
 L187     아니면                                                  => throw NoFallbackError
 L194   cacheKey — isIsr && !dev && !draftMode 일 때만 경로 (그 밖엔 null = 캐시 안 함)
 L200   supportsDynamicResponse = routeModule.isDev === true || !isIsr
 L211   isStaticGeneration      = isIsr && !supportsDynamicResponse
 L244   context.renderOpts 를 조립한다
 L291   responseGenerator = async ({previousCacheEntry}) => {
 L295     on-demand revalidate · revalidateOnlyGenerated 인데 이전 항목이 없으면 404 => return null
 L308     response = await routeModule.handle(nextReq, context)        ← ②
 L325     isIsr 이면 본문을 blob 으로 읽어 **캐시 항목**을 만든다     => return cacheEntry
            revalidate / expire 는 handle 이 채운 collectedRevalidate / collectedExpire
 L373     아니면 sendResponse 로 **곧장 보낸다**                     => return null
 L403   handleResponse
 L408     cacheEntry = await routeModule.handleResponse({..., responseGenerator,
                                                         isRoutePPREnabled: false})
 L424     !isIsr 이면                                                  => return
 L434     x-nextjs-cache: REVALIDATED / MISS / STALE / HIT
 L448     draft mode 면 Cache-Control: private, no-cache, no-store ...
 L463     응답에 Cache-Control 이 없을 때만 cacheControl 로 만들어 붙인다
 L474     sendResponse(...)
 L484   catch — onRequestError 를 부르고, isIsr 이면 => throw, 아니면 500 을 보낸다
```

```ts
// app-route.ts L200-L211
  const supportsDynamicResponse: boolean =
    // If we're in development, we always support dynamic HTML
    routeModule.isDev === true ||
    // If this is not SSG or does not have static paths, then it supports
    // dynamic HTML.
    !isIsr

  // This is a revalidation request if the request is for a static
  // page and it is not being resumed from a postponed render and
  // it is not a dynamic RSC request then it is a revalidation
  // request.
  const isStaticGeneration = isIsr && !supportsDynamicResponse
```

```text
 ★★ 페이지와 **같은 공식**이지만 입력이 하나 적다

 work-store.ts L116-119
   isStaticGeneration = !renderOpts.supportsDynamicResponse
                        && !renderOpts.isDraftMode
                        && !renderOpts.isPossibleServerAction

 라우트 핸들러의 renderOpts(ARTPL L247-277)에는 isDraftMode · isPossibleServerAction 이 **없다**
 => workStore.isStaticGeneration 은 supportsDynamicResponse 하나로 정해진다
    = 프로덕션에서 isIsr 이면 참
 ★ 위 인용의 주석 L207-210 은 "not being resumed from a postponed render and it is not
   a dynamic RSC request" 를 조건으로 말하지만, 바로 아래 식(L211)에는 **그 조건이 없다.**
   라우트 핸들러에는 postpone 도 RSC 요청도 없다 (L415 `isRoutePPREnabled: false`)
   ※ 페이지 쪽 템플릿의 주석을 옮겨 온 것으로 보인다 (내 해석이다)
 ★ draft mode 는 템플릿에서 따로 막는다 — cacheKey(L194) · fallback 검사(L178) · Cache-Control(L448)
 ※ 그래서 ISR 라우트에 draft mode 요청이 오면 캐시는 안 쓰지만 workStore 는 "정적 생성 중" 으로
   서는 것으로 보인다. 그 결과가 어떻게 드러나는지는 실행해 보지 않았다 (내 추론이다)
```

```text
 ② handle — 어떤 함수를 어떤 스토어 안에서 부를지  ARMOD L757-943

 L763   await this.ensureUserland()          (top-level await 모듈 대비)
 L771   Turbopack dev 면 요청마다 살아 있는 userland 를 다시 require 한다 (HMR)
 L777   handler = resolveHandler(req.method)
          L351  HTTP 메서드가 아니면 400 을 돌려주는 함수   주석 L350 "Prevent RCE"
          L353  _methods[method]  — autoImplementMethods 가 만든 표 (아래)
 L797   actionStore = {isAppRoute: true, isAction: getIsPossibleServerAction(req)}
 L802   implicitTags = await getImplicitTags(page, pathname, null)
          주석 L805 "App Routes don't support unknown route params."
 L809   requestStore = createRequestStoreForAPI(...)
 L818   workStore    = createWorkStore(staticGenerationContext)
 L823   actionAsyncStorage.run -> workUnitAsyncStorage.run(requestStore)
                                -> workAsyncStorage.run(workStore, async () => {
 L831     hasNonStatic 이고 정적 생성 중이면                => throw DynamicServerError   (위 실제 코드)
 L854     switch (dynamic)                                   ← `export const dynamic`
 L855       'force-dynamic'  workStore.forceDynamic = true
                             정적 생성 중이면                   => throw DynamicServerError
 L868       'force-static'   workStore.forceStatic = true
                             request = new Proxy(req, forceStaticRequestHandlers)
 L876       'error'          workStore.dynamicShouldError = true
                             정적 생성 중일 때만 request = new Proxy(req, requireStaticRequestHandlers)
 L883       undefined·'auto' request = proxyNextRequest(req, workStore)
 L899     tracer.trace(runHandler, () => this.do(handler, ..., request, context))   ← ③
 L924   Response 가 아니면                                   => return 500
 L929   x-middleware-rewrite 헤더가 있으면                   => throw 'NextResponse.rewrite() was used in a app route handler ...'
 L935   x-middleware-next === '1' 이면                        => throw 'NextResponse.next() was used in a app route handler ...'
 L942                                                         => return response
```

```text
 ★ 'force-dynamic' 의 오류 문구가 **다른 갈래의 것**이다 (L859-861)

   case 'force-dynamic':
     ...
     'Route is configured with dynamic = error which cannot be statically generated.'

 => 설정은 force-dynamic 인데 문구는 `dynamic = error` 라고 말한다
 ※ 복사해 온 문구로 보인다 (내 해석이다). 'error' 갈래(L876)는 이 문구를 쓰지 않는다
```

```text
 ★★★ 정적/동적 판정 — 페이지는 `cookies()` 가 스스로 판정하고, 라우트 핸들러는 **요청 객체가** 판정한다
     (정적 생성이 켜졌을 때의 이야기다 — 리드의 1차 관문 참조)

 dynamic 이 undefined·'auto' 일 때 request 는 proxyNextRequest(ARMOD L1103-1189)다
   request.headers · cookies · url · body · blob · json · text · arrayBuffer · formData   (아홉)
   nextUrl.search · searchParams · url · href · toJSON · toString · origin               (일곱)
   (L1145-1153 과 L1111-1117 의 case 를 세었다)
   => 이 중 하나를 **읽는 순간** trackDynamic(workStore, workUnitStore, 'request.headers' 등)

 'force-static' 이면 **일부**가 빈 값을 돌려준다 (L999-1101) — headers · cookies · nextUrl · url ·
   geo · ip · clone 만 case 가 있다. body · blob · json · text · arrayBuffer · formData 는
   그대로 통과한다 (ARMOD L995-1060)
   headers → 빈 Headers(sealed) · cookies → 빈 RequestCookies · search → '' · ip / geo → undefined
   => 읽어도 동적이 되지 않는다. 대신 거짓 값을 받는다
 'error' + 정적 생성 중이면 같은 이름들이 **던진다** (L1191-1269)
   StaticGenBailoutError `Route ... with \`dynamic = "error"\` couldn't be rendered statically ...`

 ★★ 이 Proxy 는 **NextRequest 인자**만 지킨다. 핸들러가 `headers()` · `cookies()` 를
   next/headers 에서 불러 쓰면 그쪽은 server/request/ 의 자기 switch 로 간다
   ([동적 판별](../../dynamic-rendering/01_mark/README.md) 01 이 본 cookies.ts 의 갈래)
```

```ts
// module.ts L1301-L1310
      case 'prerender':
        const error = new Error(
          `Route ${store.route} used ${expression} without first calling \`await connection()\`. See more info here: https://nextjs.org/docs/messages/next-prerender-sync-request`
        )
        return abortAndThrowOnSynchronousRequestDataAccess(
          store.route,
          expression,
          error,
          workUnitStore
        )
```

```text
 ★★★ trackDynamic(ARMOD L1277-1349)은 [동적 판별]의 switch 를 **세 번째로 다시 쓴 것**이다

 같은 스토어 종류에 대한 세 구현을 나란히 놓는다
                      markCurrentScopeAsDynamic   cookies()            trackDynamic (여기)
                      (DYNR L172)                 (cookies.ts)         (ARMOD L1277)
   'cache'            return (조용히)              throw                throw
   'private-cache'    return (조용히)              값 그대로             **throw**
   'unstable-cache'   return (조용히)              throw                throw
   'prerender'        (타입이 막아 못 옴)          hanging promise      **abortAndThrow…**  L1305
   'prerender-runtime'(타입이 막아 못 옴)          delayUntilStage      InvariantError
   'prerender-ppr'    postponeWithTracking         postponeWithTracking postponeWithTracking
   'prerender-legacy' revalidate=0 + throw         throwToInterrupt…    revalidate=0 + throw
   'request'          dev 면 usedDynamic           track… 뒤 값         dev 면 usedDynamic
   (앞 두 열은 [동적 판별] 01_mark 의 기록을 옮겼다)

 => 'prerender' 에서 cookies() 는 **기다리게**(hanging) 하지만,
    라우트 핸들러의 request.headers 는 **그 자리에서 prerender 를 끊고 던진다**
 ★ 주석 L1338-1339 — 'request' 갈래의 usedDynamic 은 "This is currently not really needed
   for route handlers, as it only controls the ISR status that's shown for pages."
 ★ 'prerender-runtime' 이 InvariantError 인 이유 — 라우트 핸들러는 런타임 prerender 를
   하지 않는다. 아래 ③의 prerender 스토어는 전부 type 'prerender' 또는 'prerender-legacy' 다
```

```text
 ③ do — 실제로 부른다  ARMOD L369-755

 L385   patchFetch(...)
 L396   resolvePendingRevalidations = () => executeRevalidates(workStore) 를 pendingWaitUntil 로
 L417   workStore.isStaticGeneration 이면
 L418     defaultRevalidate = userland.revalidate (false·undefined 면 INFINITE_CACHE)
 L427     cacheComponents 이면 — **두 번 돈다**
 L459       1차(prospective) 스토어 {type: 'prerender', phase: 'action', cacheSignal, ...}
 L489       handler 를 부른다. 동기 throw 에 신호가 abort 됐으면 prospectiveRenderIsDynamic
 L518       Promise 를 돌려받으면 reject 도 같은 방식으로 본다
 L537       await cacheSignal.cacheReady()        캐시가 다 찰 때까지
 L539       동적이었으면 getFirstDynamicReason 으로 이유를 꺼내    => throw DynamicServerError
 L563       2차(final) 스토어 — cacheSignal: null
 L587       scheduleImmediate 한 번 안에 Response 가 오고, 또 한 번 안에 본문이 풀려야 한다
 L621-638   못 풀리면 abort + createCacheComponentsError      ("used IO that was not cached")
 L649     아니면 {type: 'prerender-legacy', phase: 'action', ...} 스토어로 한 번
 L668   아니면 requestStore 로 한 번                           ← 평범한 요청
 L676   catch — redirect() 면 Location 응답 (서버 액션이면 303), notFound() 류면 그 상태 코드
 L714   Response 가 아니면 => throw 'No response is returned from route handler ...'
 L733   resolvePendingRevalidations()
 L735   prerender 스토어였으면 tags · revalidate · expire · stale 을 renderOpts 에 옮긴다   → ① L325
 L746   cookies().set() 으로 바뀐 쿠키를 응답 헤더에 합친다
```

```text
 ★★★ 1차에서 request.headers 를 읽으면 이 사슬이 돈다 (각 고리 소스 확인)

 request.headers 읽기
   +-- proxyNextRequest get 트랩        ARMOD L1145-1155
       +-- trackDynamic 'prerender'     ARMOD L1301-1305
           +-- abortAndThrowOnSynchronousRequestDataAccess     DYNR L359
               +-- abortOnSynchronousDynamicDataAccess          DYNR L381 -> L304
                     L313  prerenderStore.controller.abort(error)   ← prospectiveController
                     L317  dynamicTracking.dynamicAccesses.push({expression: 'request.headers'})
               => throw createPrerenderInterruptedError(...)     DYNR L391
   <= ARMOD L495 catch  — prospectiveController.signal.aborted 가 참
      L499 prospectiveRenderIsDynamic = true
   L542 getFirstDynamicReason(dynamicTracking)  = 'request.headers'   (DYNR L159-163)
   L544 => throw DynamicServerError "Route ... couldn't be rendered statically because it used `request.headers`"

 ★★ DYNR L349-352 의 docstring 은 "If we are doing a prospective prerender we don't
   actually abort because we want to discover all caches for the shell." 라고 적는다.
   그런데 본문(L375-381)은 prospective 인지 보지 않고 **signal 이 안 끊겼으면 끊는다**.
   그리고 여기 1차 스토어의 controller 는 prospectiveController 다 —
   **1차에서도 끊긴다.** 이 모듈은 오히려 그 abort 를 동적 판정의 신호로 쓴다 (L496 · L521)
 ※ docstring 이 지금 본문과 어긋난 것으로 보인다 (내 해석이다)
```

```text
 ★★ 라우트 핸들러의 스토어는 phase 가 **'action'** 이다 — 그래서 revalidateTag 가 된다

 request-store.ts L231-232   createRequestStoreForAPI  phase: 'action'
                             주석 "API routes start in action phase by default"
   (페이지용은 L200-201   phase: 'render'  "Pages start in render phase by default")
 ARMOD L462 · L565 · L652     prerender 스토어 셋도 전부 phase: 'action'

 revalidate.ts L142  workUnitStore.phase === 'render' 이면 throw
   => 페이지 렌더 중에는 막히고, 라우트 핸들러에서는 통과한다
 revalidate.ts L162-168  그다음 'prerender' · 'prerender-runtime' 이면 abortAndThrowOnSynchronousRequestDataAccess
   => cacheComponents 로 **GET 을 prerender 하는 중** revalidateTag 를 부르면
      위 사슬과 똑같이 끊기고 동적이 된다
 ★ updateTag 는 따로 막는다 — revalidate.ts L57 `workStore.page.endsWith('/route')` 이면 throw.
   주석 L55-56 "TODO: change this after investigating why phase: 'action' is set for route handlers"
   ([재검증](../../revalidation/README.md) 이 짚은 그 TODO 다)
```

```ts
// auto-implement-methods.ts L56-L60
      // If the list of methods doesn't include HEAD, but it includes GET, then
      // add HEAD as it's automatically implemented.
      if (!implemented.has('HEAD') && implemented.has('GET')) {
        allow.push('HEAD')
      }
```

```text
 ★★ 메서드 표는 일곱 칸이고, 빈 칸은 405 다 (AUTOIMPL L16-24)

 HTTP_METHODS = GET HEAD OPTIONS POST PUT DELETE PATCH   (web/http.ts L5-13, 일곱)
 없는 메서드            => 405 (L7-9 handleMethodNotAllowedResponse)
 HEAD 가 없고 GET 이 있으면 => HEAD = GET 그대로 (L38-45)
 OPTIONS 가 없으면       => 204 + Allow 헤더 (L50-74)
 목록 밖의 메서드        => 400 (ARMOD L351 — 표를 보기 전에 막는다)

 ★ 위 L58 의 `!implemented.has('HEAD') && implemented.has('GET')` 은 **참이 될 수 없다**.
   AUTOMATIC_ROUTE_METHODS 가 ['HEAD', 'OPTIONS'] 순서라(L5) HEAD 를 먼저 처리하고,
   GET 이 있으면 L44 에서 이미 implemented 에 HEAD 를 넣었다.
   HEAD 는 L54 의 `...implemented` 로 Allow 에 들어간다 — 결과는 같다
```

## 결과가 쓰이는 곳

```text
 Response (handle 의 반환)
      --> ISR 이 아니면 ARTPL L375 sendResponse 로 곧장 나간다.
          base-server 로는 L2608 `return null` ("response is handled fully in handler")만 돌아간다
          ([응답 나가기](../../response-out/02_delegate/README.md) 가 본 그 null)
      --> ISR 이면 {kind: APP_ROUTE, status, body, headers} 캐시 항목이 되어
          routeModule.handleResponse 가 응답 캐시에 넣고 꺼낸다

 context.renderOpts.collectedTags / Revalidate / Expire / Stale  (ARMOD L736-739)
      --> ARTPL L331-369 가 캐시 항목의 NEXT_CACHE_TAGS_HEADER 와 cacheControl 로 쓴다

 context.renderOpts.pendingWaitUntil  (executeRevalidates 의 Promise)
      --> ARTPL L315-320 이 ctx.waitUntil 이 있으면 거기로 넘긴다. 없으면 비 ISR 갈래의
          sendResponse(L375)에 넘어간다 — 주석 L313-314 "if it's not we fallback to sendResponse's handling"
          [재검증] 02_execute 가 그리는 실행이 여기서 붙는다

 DynamicServerError (정적 생성 중)
      --> 빌드가 이 라우트를 정적으로 만들지 않는 신호다.
          받는 쪽 — export 워커가 isDynamicUsageError 이면 `revalidate: 0` 으로 기록한다
          (export/routes/app-route.ts L169-174)
```

## 다루지 않는 것

`RouteModule.prepare`(route-module.ts L594)가 파라미터·draft mode·on-demand revalidate 를 푸는 과정과 `handleResponse`(L1109)의 응답 캐시, `sendResponse` 의 구현, `getIsPossibleServerAction` 과 라우트 핸들러의 서버 액션, `createServerParamsForRoute` 로 만드는 `params` Promise, `createRequestStoreForAPI` · `createWorkStore` 의 나머지 필드, `appendMutableCookies` 와 `MutableRequestCookiesAdapter`, `patchFetch` 가 라우트 핸들러의 `fetch` 를 캐시에 넣는 방식, `CacheSignal` · `trackPendingModules` · `createPrerenderResumeDataCache` 의 구현(주석 L451-456 이 RDC 를 쓰는 이유만 적는다), `printDebugThrownValueForProspectiveRender`, `isStaticGenEnabled` 와 `output: 'export'` 검사(L279-308), `isRedirectError` · `isHTTPAccessFallbackError` 의 판별, 빌드가 라우트 핸들러의 GET 을 prerender 하는 export 워커, 그리고 Edge 런타임 라우트 핸들러(`build/templates/edge-app-route.ts` · `server/web/edge-route-module-wrapper.ts` — base-server 의 `runEdgeFunction` 으로 샌드박스를 거친다)는 이 문서의 범위 밖이다.
