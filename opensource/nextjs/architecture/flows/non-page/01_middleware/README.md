# 01 미들웨어

상위: [페이지가 아닌 요청이 처리되기까지](../README.md)

미들웨어(`middleware.ts` / `proxy.ts`)는 **두 프로세스 역할에 걸쳐** 돈다. 언제 돌릴지는 router-server 의 `resolveRoutes` 가 정하고, 실제 실행은 render server(base-server 를 상속한 `NextNodeServer`)가 한다. 그리고 결과는 반환값이 아니라 **예외에 실려** 돌아온다.

## 위치

`packages/next` / `src/server/lib/router-utils` / `resolve-routes.ts` L558-L803 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/lib/router-utils/resolve-routes.ts#L558-L803))

`packages/next` / `src/server` / `next-server.ts` L1814-L1924 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/next-server.ts#L1814-L1924))

`packages/next` / `src/server` / `next-server.ts` L1629-L1812 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/next-server.ts#L1629-L1812))

`packages/next` / `src/server/web` / `adapter.ts` L127-L548 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/web/adapter.ts#L127-L548))

## 실제 코드

render server 쪽 입구 `handleCatchallMiddlewareRequest` 에서 응답을 얻은 뒤의 갈래다.

```ts
// next-server.ts L1877-L1899
      if ('response' in result) {
        if (isMiddlewareInvoke) {
          bubblingResult = true
          throw new BubbledError(true, result)
        }

        for (const [key, value] of Object.entries(
          toNodeOutgoingHttpHeaders(result.response.headers)
        )) {
          if (key !== 'content-encoding' && value !== undefined) {
            res.setHeader(key, value as string | string[])
          }
        }
        res.statusCode = result.response.status

        const { originalResponse } = res
        if (result.response.body) {
          await pipeToNodeResponse(result.response.body, originalResponse)
        } else {
          originalResponse.end()
        }
        return true
      }
```

```text
 ★★★ L1883-1898 은 **돌 수 없는 줄**이다

 L1819  const isMiddlewareInvoke = getRequestMeta(req, 'middlewareInvoke')
 L1821  if (!isMiddlewareInvoke) {
 L1822    return false
 L1823  }
   ...
 L1878  if (isMiddlewareInvoke) {        ← `const` 라서 여기서는 언제나 참
 L1880    throw new BubbledError(true, result)

 => 헤더를 복사하고 본문을 pipeToNodeResponse 로 흘리는 16줄(L1883-1898)은
    미들웨어 응답을 **render server 가 직접 쓰던 시절**의 길이다
 ※ "시절" 은 내 추측이다
 ★★ 지금도 render server 가 응답을 **직접 쓰는** 갈래가 넷 있다 — 그때는 예외가 안 올라간다
   handleFinished `res.body('').send()` (NEXTSRV L1825-1829) — 미들웨어가 없거나(L1832)
     render 쪽 matcher 가 안 맞을 때(L1853)
   ENOENT → render404 (L1905-1906) · DecodeError → 400 (L1910-1912)
   **미들웨어가 throw 하면 → 500 renderError** (L1918-1919)
   => router-server 는 예외를 받지 못하고 `res.finished` 로 그냥 끝난다 (RROUTES L647 → RSRV L503-505)
   => 미들웨어가 던지는 오류는 **render server 가 500 에러 페이지를 직접 그린다**
 ★ 그 대신 결과를 BubbledError 에 실어 던진다. `bubblingResult = true`(L1879)가
   바로 아래 catch(L1900-1903)에서 이 예외만 **다시 던지게** 한다 — 다른 예외는 삼켜 에러 페이지로 간다
```

## 동작 흐름

```text
 ① router-server — 언제 부를지  RROUTES L558-803

 L558  !opts.minimalMode && route.name === 'middleware' 일 때만
 L559    match = fsChecker.getMiddlewareMatchers()
 L568    원래 pathname 또는 decodeURIComponent 한 것 중 하나라도 맞으면
 L578      dev 면 ensureMiddleware(req.url)       (컴파일을 기다린다)
 L582      serverResult = await renderServer?.initialize(renderServerOpts)
 L589-592  invokePath='' · invokeOutput='' · invokeQuery={} · middlewareInvoke=true
 L606      await serverResult.requestHandler(req, res, parsedUrl)   ← render server 1번째 호출
 L607      catch (err)
 L608        'result' in err && 'response' in err.result 가 아니면  => throw err
 L611        middlewareRes = err.result.response
 L614-623    본문이 있으면 그 스트림, 없는데 status 가 있으면 **빈 스트림**을 만든다
 L637      클라이언트가 끊었으면                             => return {finished: true}
 L647      res 가 이미 끝났거나 middlewareRes 가 없으면       => return {finished: true}
```

```text
 ② render server — 한 번 더 거른다  NEXTSRV L1814-1924

 L1821  middlewareInvoke 가 없으면                    => return false
 L1831  middleware = await this.getMiddleware()
 L1832  없으면 handleFinished()                        => return true   (빈 본문을 보낸다)
 L1853  matcher 에 안 맞으면 handleFinished()          => return true
          ★ router-server 가 L568 에서 **같은 판정을 이미 했다.** 두 번 거른다 —
            router 쪽은 맞고 render 쪽이 안 맞으면 걸러지는 데서 끝나지 않고
            **빈 본문 200 으로 요청이 끝난다** (L1859 → handleFinished → RROUTES L647)
 L1868  await this.ensureMiddleware(req.url)
 L1870  result = await this.runMiddleware({...})
 L1877  'response' in result 이면
 L1880    => throw new BubbledError(true, result)       ← 정상 경로
 L1900  catch
 L1901    bubblingResult 면                             => throw err
 L1905    ENOENT 면 render404                           => return true
 L1910    DecodeError 면 400 + renderError              => return true
 L1918    그 밖은 500 + renderError                     => return true
 L1923  => return result.finished
```

```text
 ③ runMiddleware — 무엇으로 돌릴지  NEXTSRV L1629-1812

 L1636  NEXT_MINIMAL 이면 => throw 'invariant: runMiddleware should not be called in minimal mode'
 L1643  on-demand revalidate 요청이면
 L1649    => return { response: new Response(null, {headers: {'x-middleware-next': '1'}}) }
          주석 L1642 - "Middleware is skipped for on-demand revalidate requests"
          ★ 건너뛰는 방법이 "미들웨어가 next() 를 돌려준 척" 이다. router-server 는 차이를 모른다
 L1656  URL 을 만든다 — 주석 L1659 "For middleware to "fetch" we must always provide an absolute URL"
 L1670  http 로 시작하지 않으면 => throw 'To use middleware you must provide a `hostname` and `port` ...'
 L1681  getMiddleware() 가 없으면           => return { finished: false }
 L1685  hasMiddleware(page) 가 거짓이면      => return { finished: false }
 L1690  middlewareInfo = this.getEdgeFunctionInfo({page, middleware: true})

 L1724  ★★ middlewareInfo 가 없으면 — **Node.js 미들웨어**
 L1726    middlewareModule = await this.loadNodeMiddleware()   (dist/server/middleware.js 를 require)
 L1743    result = await getTracer().runWithDetachedContext(() => adapterFn({...}))
            **같은 프로세스에서** 부른다. 샌드박스를 거치지 않는다
 L1763  아니면 — **Edge 미들웨어**
 L1764    require('./web/sandbox') 의 run(...)            ← 여기만 샌드박스를 거친다
 L1780  dev 가 아니면 result.waitUntil.catch(...)
 L1786  if (!result) render404 (await 없음)              => return { finished: true }
 L1792  set-cookie 를 쪼개 하나씩 다시 붙이고 요청 메타 'middlewareCookie' 에도 남긴다
 L1811  => return result
```

```text
 ★★ `server/web/sandbox/` 를 거치는지는 **런타임이 가른다** (grep 으로 확인)

   next-server.ts 에서 sandbox 를 require 하는 자리는 둘이다
     L1764  runMiddleware 의 Edge 갈래
     L2063  runEdgeFunction  (Edge 로 도는 페이지·라우트 핸들러)
   => middleware-manifest 에 항목이 있으면(Edge) 샌드박스, 없으면(Node.js) 프로세스 안

   주석 L1719-1723
     "if no middleware info check for Node.js middleware
      this is not in the middleware-manifest as that historically
      has only included edge-functions, we need to do a breaking
      version bump for that manifest to write this info there if
      we decide we want to"
 => "manifest 에 없음 = Node.js" 라는 판정은 **매니페스트 형식을 못 바꿔서 생긴 관례**다
 ★ 주석 L1739-1742 — Node.js 미들웨어는 handleRequest 스팬 **안**에서 돌지만
   스팬을 떼어 내(detach) Edge 미들웨어처럼 **형제 루트**가 되게 한다
```

```text
 ★★★ NEXTSRV 가 넘긴 handler 와 page 는 **덮어써진다**

 NEXTSRV L1731  adapterFn: typeof import('./web/adapter').adapter = middlewareModule.default || ...
 NEXTSRV L1745  handler: middlewareModule.proxy || middlewareModule.middleware || middlewareModule
 NEXTSRV L1755  page: 'middleware'

 그런데 middleware.js 의 default export 는 `adapter` 가 아니라 템플릿의 internalHandler 다
   MWTPL L152  export default internalHandler
   (webpack 은 next-middleware-loader 가, Turbopack 은 crates/next-core/src/middleware.rs L112 이
    같은 템플릿 `middleware` 를 불러 번들을 만든다)
```

```ts
// middleware.ts L98-L104
  return adapter({
    ...opts,
    IncrementalCache,
    incrementalCacheHandler,
    page,
    handler: errorHandledHandler(handlerUserland),
  })
```

```text
 => `...opts` 가 **먼저** 펼쳐지고 page · handler 가 **뒤에서** 덮는다.
    NEXTSRV 가 고른 handler 와 'middleware' 라는 page 는 adapter 에 닿지 않는다
 => 실제 handler 는 MWTPL L21 이 고른 것 — `proxy.ts` 면 mod.proxy, 아니면 mod.middleware,
    둘 다 없으면 mod.default — 을 errorHandledHandler(L41)로 감싼 것이다
 ★ 타입 표기(L1731 `typeof ...adapter`)가 실제 값과 다르다
 ★ 그 전에 L78-96 이 Node.js 일 때 instrumentation 을 등록한다 —
   주석 L79 "This mirrors what `RouteModule#prepare` does for routes"
```

```text
 ④ adapter — 미들웨어 함수를 실제로 부른다  WADAPT L127-548

 L137  URL 을 RSC 정규화하고 NextURL 로 감싼다
 L148  내부 쿼리 키를 일반 키로 바꾼다 (normalizeNextQueryParam)
 L163  buildId 를 URL 에서 **떼어 낸다** — 주석 L162 "Ensure users only see page requests, never data requests."
 L181  Edge 렌더링이 아니면 FLIGHT_HEADERS 를 요청에서 **뺀다** (아래 별항)
 L197  NextRequestHint 를 만든다 — request / respondWith / waitUntil 을 부르면 PageSignatureError (L71-81)
 L228  공유 IncrementalCache 가 없으면 새로 만든다
 L271  propagator 로 추적 문맥을 잇고
 L273    page 가 '/middleware' · '/src/middleware' · '/proxy' · '/src/proxy' 이면
 L311      requestStore = createRequestStoreForAPI(...)
 L322      workStore = createWorkStore({page: '/', ...})    주석 L302 "Fake Work"
 L358      workAsyncStorage.run(workStore, () => workUnitAsyncStorage.run(requestStore, handler, ...))
 L366      finally — setTimeout 0 뒤 closeController.dispatchClose()
            주석 L367 "middleware cannot stream, so we can consider the response closed
                       as soon as the handler returns."
 L378    아니면 그냥 params.handler(request, event)
 L382  Response 가 아니면 => throw TypeError('Expected an instance of Response to be returned')
 L396  x-middleware-rewrite 가 있으면 목적지를 다시 쓰고 RSC 요청이면 rewritten path/query 헤더를 붙인다
 L484  Location 이 있으면 (Edge 렌더링이 아닐 때) 상대 경로로 바꾸고,
         데이터 요청이면 Location 대신 x-nextjs-redirect 로 옮긴다 (주석 L508-512: CORS)
 L522  응답이 없으면 NextResponse.next()
 L525  x-middleware-override-headers 가 있으면 떼어 둔 flight 헤더를 되돌려 넣는다
 L543  => return { response, waitUntil, fetchMetrics }
```

```ts
// adapter.ts L178-L189
  const flightHeaders = new Map()

  // Headers should only be stripped for middleware
  if (!isEdgeRendering && !process.env.__NEXT_NO_MIDDLEWARE_URL_NORMALIZE) {
    for (const header of FLIGHT_HEADERS) {
      const value = requestHeaders.get(header)
      if (value !== null) {
        flightHeaders.set(header, value)
        requestHeaders.delete(header)
      }
    }
  }
```

```text
 ★★★ 미들웨어는 RSC 요청의 flight 헤더를 **볼 수 없다**

 L181-188  FLIGHT_HEADERS 를 요청 헤더에서 지우고 flightHeaders 맵에 따로 둔다
 L524-541  미들웨어가 요청 헤더를 덮어쓰면(x-middleware-override-headers)
           그 목록 끝에 flight 헤더를 **강제로 다시 붙인다**
   주석 L524 - "Flight headers are not overridable / removable so they are applied at the end."

 => 미들웨어가 요청 헤더를 통째로 갈아도 RSC 요청이 RSC 요청으로 남는다
 ★ `__NEXT_NO_MIDDLEWARE_URL_NORMALIZE` 가 켜지면 떼지 않는다 (L181)
```

```text
 ★★ 미들웨어 안에서도 `cookies()` · `headers()` 가 되는 이유 (L279-377)

 page 가 미들웨어 네 이름 중 하나이면 **요청 스토어와 작업 스토어를 만들어 감싼다**
   주석 L272 "we only care to make async storage available for middleware"
 작업 스토어의 renderOpts 는 대부분 **던지는 감시값**이다
   cacheLifeProfiles   proxyCacheLifeProfiles — `default` 를 읽으면 InvariantError (L50-56)
   staticPageGenerationTimeout: 0 · useCacheTimeout: 0
     주석 L326-329 "0 is a sentinel: if something ever reads it,
                    it'll surface loudly instead of silently using a misleading default."
   cacheComponents: false · isRoutePPREnabled: false · supportsDynamicResponse: true
 => 미들웨어는 [`'use cache'`](../../use-cache/README.md) 도 prerender 도 하지 않는다.
    그 값들을 누가 읽으면 조용히 틀리지 말고 **시끄럽게 깨지라**는 설계다
```

```text
 ⑤ router-server — 답을 해석한다  RROUTES L655-803

 L661  x-middleware-override-headers 가 있으면
 L676    목록에 **없는** 요청 헤더를 전부 지운다
 L683    목록의 헤더를 x-middleware-request-<이름> 값으로 바꾼다
         => NextResponse.next({request: {headers}}) 가 이렇게 전달된다
 L695  rewrite · next · location 이 **셋 다 없으면** x-middleware-refresh = '1'
         => "미들웨어가 제 손으로 응답을 만들었다" 는 뜻으로 바꿔 적는다
 L702  x-middleware-next 는 지운다
 L704  나머지 헤더를 resHeaders **와 req.headers 양쪽에** 복사한다
         (content-length · rewrite · redirect · refresh 는 뺀다.
          x-middleware-set-cookie 는 요청에만 넣는다 — 주석 L718-719)
 L731  rewrite 면 parsedUrl 을 목적지로 바꾸고
 L738    외부 URL(protocol 있음)이면                => return {finished: true}
         내부면 **return 없이 아래로** — 목록의 다음 칸으로 간다
 L758  location 이 있으면
 L767    리다이렉트 상태 코드이면                   => return {finished, statusCode}
 L783    아니면 본문과 함께                          => return {finished, bodyStream, statusCode}
 L793  refresh 면                                    => return {finished, bodyStream, statusCode}
       (셋 다 아니면 — next() 이거나 내부 rewrite — 다음 칸으로 넘어간다. 미들웨어 route 객체에는
        destination · statusCode · headers · check 가 없어서 L805-934 는 아무것도 안 한다)
```

```text
 ★★ `x-middleware-next` 를 돌려주는 곳이 **셋**이다 — 그리고 셋째만 결이 다르다

   ⓐ 미들웨어 함수가 NextResponse.next() 를 돌려줌 → adapter 가 그대로 BubbledError 로
   ⓑ on-demand revalidate 요청 → runMiddleware L1649 가 가짜 결과를 만듦 → BubbledError 로
   ⓒ handleCatchallMiddlewareRequest 가 false 를 돌림 → BASE L1649 가 **맨 Error** 로

 ⓒ 가 되려면 runMiddleware 가 {finished: false} 를 돌려야 한다 (L1683 / L1686).
   그런데 NEXTSRV L1831-1834 가 getMiddleware() 가 없을 때를 먼저 걸러내므로
   남는 것은 L1685 `hasMiddleware(page)` 가 거짓인 경우뿐이다 — **프로덕션 NextNodeServer 에서는.**
   dev 는 runMiddleware 를 덮어써서 내부 URL 오류면 `{finished:false}` 를 돌려주고
   (next-dev-server.ts L491-498), hasMiddleware 도 hasPage 다 (L738-740). dev 는 BASE L1688 의
   `this.dev` 로 다시 던지므로 500 이 되지는 않는다
 ※ getMiddleware 가 있다고 했는데 hasMiddleware 가 거짓인 경우는 매니페스트 항목의
   files 가 비어 있을 때(L1608 `info.paths.length > 0`)로 보인다. 드물다 (내 추론이다)
 ※ 그때 BASE L1688 이 BubbledError 가 아닌 이 예외를 프로덕션에서 **500 으로 바꾼다** —
   [README] 의 ★★ 참조. 실행해 확인하지는 않았다
```

```text
 ★ 순서가 어긋난 방어 코드 (L1780-1789)

 L1780  if (!this.dev) {
 L1781    result.waitUntil.catch(...)       ← result 가 undefined 면 **여기서 먼저 TypeError**
 L1786  if (!result) {
 L1787    this.render404(...)               ← await 도 없다
 L1788    return { finished: true }

 ※ 두 갈래 모두 result 를 언제나 채운다 — adapter 는 L543 에서 객체를 돌려주고,
   sandbox 의 run 은 결과가 없으면 던진다 (sandbox.ts L158 'Edge function did not return a response').
   그래서 L1786 은 실제로는 안 타는 줄로 보인다 (내 추론이다)
 ★ [요청 흐름] 04_handoff 가 센 "L1787 만 await 이 없다" 가 이 줄이다
```

## 결과가 쓰이는 곳

```text
 BubbledError(true, FetchEventResult)
      --> BASE L1688 의 `isBubbledError(err) && err.bubble` 을 지나 위로 올라가
          router-server 의 RROUTES L607-610 이 받는다

 요청 헤더 (L676-693 · L704-729 에서 고쳐 쓴 것)
      --> 두 번째 render server 호출(invokeRender)에 **그대로 실려 간다.**
          페이지의 headers() / cookies() 가 읽는 것이 이 값이다

 resHeaders
      --> RSRV L546-550 이 최종 응답에 붙인다

 parsedUrl (rewrite 목적지)
      --> 목록의 다음 칸들을 거쳐 invokeRender 의 invokePath 가 된다

 요청 메타 'middlewareCookie' (NEXTSRV L1808)
      --> 읽는 곳은 저장소 전체에 하나다 — server/lib/patch-set-header.ts L43.
          BASE L1037 이 그 패치를 응답에 설치한다 ([요청 흐름] 02_normalize 가 본
          L1035-1036 주석 "ensure cookies set in middleware are merged ...")
      ※ 이 메타는 **첫 번째**(미들웨어) 호출의 요청 객체에 붙는다. 두 번째(렌더) 호출까지
        살아남는지는 요청 메타의 저장 방식을 읽어야 한다 — 확인하지 않았다

 result.waitUntil
      --> 프로덕션에서는 catch 만 걸고 흘려보낸다. dev 서버는 next-dev-server.ts L464 에서 다시 건다
```

## 다루지 않는 것

`fsChecker.getMiddlewareMatchers` 와 `getMiddlewareRouteMatcher` 의 매칭 규칙(`config.matcher` 의 has/missing 조건), `middleware_next_data` 칸(RROUTES L423)이 `/_next/data` 요청을 고치는 방식, `NextURL` · `NextRequest` · `NextResponse` · `NextFetchEvent` 의 구현(`server/web/spec-extension/`), `server/web/sandbox/` 의 VM 컨텍스트 구성과 모듈 캐시, `getEdgeFunctionInfo`(NEXTSRV L1499) · `loadNodeMiddleware`(L1561)가 매니페스트를 읽는 세부, `createRequestStoreForAPI` 와 `createWorkStore` 의 필드, `CloseController` 와 `after()` 의 연결, `getImplicitTags`, dev 서버의 `ensureMiddleware` 컴파일 대기와 `runMiddleware` 오버라이드(next-dev-server.ts L445-505), `MiddlewareSpan` 추적 속성, `edgeInstrumentationOnRequestError` 로 가는 오류 보고, 그리고 RROUTES L746-756 의 i18n 로케일 재판별은 이 문서의 범위 밖이다.
