# 페이지가 아닌 요청이 처리되기까지

상위: [Next.js 아키텍처 지도](../../README.md)

페이지 요청은 [요청 흐름](../request-to-render/README.md)이 따라간 길로 렌더러에 닿는다. 그 옆에 **페이지를 그리지 않는 길이 셋** 있다 — 미들웨어, 라우트 핸들러(`app/**/route.ts`), 웹소켓 업그레이드. 셋은 같은 자리에서 갈라지지 않는다. 미들웨어는 base-server **바깥**(router-server)에서 갈라져 들어왔다 나가고, 라우트 핸들러는 (Node 런타임이면) 페이지와 **끝까지 같은 길**을 가다가 마지막 `ComponentMod.handler` 에서 갈라지고, 업그레이드는 base-server 의 **업그레이드 처리를 거치지 않는다** — 다만 미들웨어에 맞으면 미들웨어 실행을 위해 render server 에 들어간다 ([03]).

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `RSRV` = `server/lib/router-server.ts`(1029줄), `RROUTES` = `server/lib/router-utils/resolve-routes.ts`(960줄), `BASE` = `server/base-server.ts`(3195줄), `NEXTSRV` = `server/next-server.ts`(2195줄), `WADAPT` = `server/web/adapter.ts`(548줄), `MWTPL` = `build/templates/middleware.ts`(152줄), `ARTPL` = `build/templates/app-route.ts`(602줄), `ARMOD` = `server/route-modules/app-route/module.ts`(1349줄), `AUTOIMPL` = `.../app-route/helpers/auto-implement-methods.ts`(82줄), `NEXTWRAP` = `server/next.ts`(697줄), `STARTSRV` = `server/lib/start-server.ts`(676줄).

## 위치

`packages/next` / `src/server/lib` / `router-server.ts` L247-L808 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/lib/router-server.ts#L247-L808))

`packages/next` / `src/server/lib/router-utils` / `resolve-routes.ts` L84-L116 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/lib/router-utils/resolve-routes.ts#L84-L116))

## 실제 코드

`next start` 에서 요청을 먼저 받는 것은 base-server 가 아니라 router-server 다. 그 안의 `resolveRoutes` 가 **라우팅 규칙을 한 줄로 세운 목록**을 앞에서부터 돈다.

```ts
// resolve-routes.ts L84-L116
  const calculateRoutes = () => {
    return [
      // _next/data with middleware handling
      { match: () => ({}), name: 'middleware_next_data' },

      ...(opts.minimalMode ? [] : fsChecker.headers),
      ...(opts.minimalMode ? [] : fsChecker.redirects),

      // check middleware (using matchers)
      { match: () => ({}), name: 'middleware' },

      ...(opts.minimalMode ? [] : fsChecker.rewrites.beforeFiles),

      // check middleware (using matchers)
      { match: () => ({}), name: 'before_files_end' },

      // we check exact matches on fs before continuing to
      // after files rewrites
      { match: () => ({}), name: 'check_fs' },

      ...(opts.minimalMode ? [] : fsChecker.rewrites.afterFiles),

      // we always do the check: true handling before continuing to
      // fallback rewrites
      {
        check: true,
        match: () => ({}),
        name: 'after files check: true',
      },

      ...(opts.minimalMode ? [] : fsChecker.rewrites.fallback),
    ]
  }
```

```text
 ★★ 미들웨어는 "라우트 목록의 한 칸" 이다 — 이름이 'middleware' 인 가짜 항목

   1  middleware_next_data         /_next/data 요청을 미들웨어용으로 고친다
   2  ...headers                   next.config 의 headers
   3  ...redirects                 next.config 의 redirects
   4  middleware                   ← **여기서 미들웨어가 돈다** (RROUTES L558)
   5  ...rewrites.beforeFiles
   6  before_files_end
   7  check_fs                     파일(정적 파일·페이지)과 정확히 맞는지
   8  ...rewrites.afterFiles
   9  after files check: true
  10  ...rewrites.fallback
   (이름 붙은 항목 다섯 + 펼쳐 넣는 설정 목록 다섯. 소스 L87-114 를 세었다)

 => 순서가 곧 우선순위다. **config 의 redirects 가 미들웨어보다 먼저**,
    beforeFiles rewrites 는 미들웨어 **다음**에 돈다
 ★ 이름 붙은 항목의 `match` 가 전부 `() => ({})` 다 — 언제나 맞는다.
   실제 판정은 handleRoute(L355-936) 안에서 `route.name` 으로 가른다
 ★ L97 의 주석 "check middleware (using matchers)" 는 L92 와 같은 문장인데
   바로 아래 항목은 'before_files_end' 다 (※ 복사해 온 주석으로 보인다 — 내 해석)
 ★ minimalMode 이면 설정 목록 다섯이 전부 빈 배열이다. 그리고 L558 이
   `!opts.minimalMode && route.name === 'middleware'` 라서 **미들웨어도 안 돈다**
```

## 동작 흐름

```text
 ★★★ 세 길이 갈라지는 자리가 셋 다 다르다

 node http 서버 (STARTSRV)
   |
   +-- 'request' 이벤트 ------------------------------------------------+
   |     RSRV requestHandlerImpl L247                                    |
   |       +-- handleRequest(0)  L786 -> L442                           |
   |           +-- resolveRoutes  L495  (RROUTES L118)                  |
   |               for (const route of routes)  RROUTES L938             |
   |                 |                                                  |
   |                 +-- route.name === 'middleware'  RROUTES L558      |
   |                 |     render server 의 requestHandler 를 **1번째로** 부른다  [01]
   |                 |       meta: invokePath='' · middlewareInvoke=true (L589-592)
   |                 |       BASE handleRequestImpl L1638  middlewareInvoke 갈래
   |                 |         +-- NEXTSRV handleCatchallMiddlewareRequest L1814
   |                 |               +-- runMiddleware L1629 -> adapter / sandbox
   |                 |               => throw BubbledError(true, result)  L1880
   |                 |     catch 로 받는다  RROUTES L607-610  ('result' in err)
   |                 |     응답 헤더를 읽어 rewrite / redirect / 본문 / 다음 칸 으로 가른다
   |                 v
   |               (목록의 나머지 칸)
   |           +-- invokeRender  RSRV L369
   |                 render server 의 requestHandler 를 **2번째로** 부른다
   |                   meta: invokePath=경로 · middlewareInvoke=false (L404-406)
   |                   BASE handleRequestImpl L1580  useInvokePath 갈래
   |                     +-- handleCatchallRenderRequest  BASE L1634 에서 곧장
   |                         ... [요청 흐름] [04]·[05] 와 [응답 나가기] 가 그린 길 ...
   |                         BASE renderToResponseWithComponentsImpl
   |                           L2603  await components.ComponentMod.handler(...)
   |                             |
   |                             +-- 페이지면  app-page.ts / pages.ts 템플릿의 handler
   |                             +-- route.ts 면  ARTPL handler L105                [02]
   |                                   +-- routeModule.handle  ARMOD L757
   |                                       +-- this.do  ARMOD L369  => GET/POST 본체
   |                                                                    |
   +-- 'upgrade' 이벤트  STARTSRV L286 --------------------------------+
         RSRV upgradeHandler L908                                          [03]
           dev + /_next/hmr 이면 hotReloader.onHMR  (L953)
           아니면 resolveRoutes({isUpgradeReq: true})  L986
             외부 rewrite 면 proxyRequest 로 웹소켓을 넘긴다 (L1001)
             그 밖엔 socket.end() 하거나 **아무것도 안 한다**
         ★★★ BASE handleUpgrade(L1765, abstract) 는 이 길에 **없다**.
             NEXTSRV L348 의 구현은 본문이 비어 있다
```

```text
 ★★★ 같은 base-server 입구를 **두 번** 지나간다 — 요청 메타 하나로 갈래를 바꾼다

 1번째 (미들웨어)   invokePath = ''     middlewareInvoke = true
                    => BASE L1578 useInvokePath = !useMatchedPathHeader && ''  → 거짓
                    => L1638 middlewareInvoke 갈래로
 2번째 (렌더)       invokePath = 경로   middlewareInvoke = false
 ★★ "두 번" 이 상한이 아니다 — 템플릿에서 NoFallbackError 가 나면(ARTPL L187) invokeRender 가
   받아 handleRequest(handleIndex+1) 로 resolveRoutes 를 **처음부터 다시** 돈다 (RSRV L423-426).
   그때 **미들웨어도 다시 돈다** (L558 에 막는 조건이 없다). 상한은 L443 `handleIndex > 5`,
   invokedOutputs 가 check_fs 만 건너뛰게 한다 (RROUTES L494). L799 의 오류 재렌더도 한 번 더다
                    => L1580 useInvokePath 갈래로. **run(L1673)을 거치지 않는다**

 ★★ 그래서 [요청 흐름] 이 그린 `run -> runImpl -> handleCatchallRenderRequest`
    는 router-server 를 거치는 `next start` 에서는 **타지 않는 길**이다.
    router-server 가 (일치한 출력에 대해서는) invokePath 를 심기 때문이다 —
    render server 의 requestHandler 를 부르는 자리는 grep 으로 둘뿐이고
    (RSRV L422 invokeRender 안 · RROUTES L606 미들웨어 칸), 둘 다 바로 앞에서 invokePath 를 쓴다
 ★ 예외 — invokeStatus 가 있는 호출(404 · `_not-found` · 405 · 400/412/416 정적 파일 오류 ·
   500/400 catch)은 handleCatchallRenderRequest 가 아니라 BASE L1581-1592 renderError 로 간다
   (RSRV L589-592 · L616 · L676-683 · L770-782 · L799)
 ★ run 갈래(L1673)는 router-server 를 **거치지 않을 때**의 길이다 — 확인됨.
   NEXTSRV L1088-1093 주석이 "router-server is not present" 환경을 명시하고,
   minimalMode + `x-matched-path` 면 useMatchedPathHeader 가 되어 L1673 으로 간다
   (BASE L1117-1118). router-server 는 x-matched-path 를 지운다 (RSRV L251-253)
 ★ 차이는 크지 않다 — run 도 runImpl(L1824-1830)에서 **같은** handleCatchallRenderRequest 에
   닿는다. 다른 것은 `run` 트레이스 span, basePath 제거(L1665-1670), statusCode 200,
   그리고 invokePath/invokeQuery 로 pathname·query 를 덮어쓰는지(L1595-1629)다
 ★ 미들웨어 호출에서 invokePath 를 **빈 문자열로 덮어쓰는** 것(L589)이 이 배타를 만든다.
   invokeOutput · invokeQuery 도 함께 비운다 (L590-591)
```

```ts
// base-server.ts L1638-L1659
      if (getRequestMeta(req, 'middlewareInvoke')) {
        finished = await this.normalizeAndAttachMetadata(req, res, parsedUrl)
        if (finished) return

        finished = await this.handleCatchallMiddlewareRequest(
          req,
          res,
          parsedUrl
        )
        if (finished) return

        const err = new Error()
        ;(err as any).result = {
          response: new Response(null, {
            headers: {
              'x-middleware-next': '1',
            },
          }),
        }
        ;(err as any).bubble = true
        throw err
      }
```

```text
 ★★★ 미들웨어의 답이 **반환값이 아니라 예외로** 거꾸로 올라간다

   handleCatchallMiddlewareRequest 가 응답을 얻으면  => throw new BubbledError(true, result)
   얻지 못하고 false 를 돌리면                       => 위 L1649 가 맨 Error 를 만들어 던진다
                                                        (응답 = `x-middleware-next: 1`)
   둘 다 router-server 쪽 RROUTES L607-610 의 catch 가
     `'result' in err && 'response' in err.result` 로 알아보고 꺼낸다

 ★★ 그런데 두 예외의 **종류가 다르다** — 이것이 BASE L1688 에서 갈린다
     L1688  if (this.minimalMode || this.dev || (isBubbledError(err) && err.bubble)) throw err
     isBubbledError 는 `instanceof BubbledError` 다 (server/lib/trace/tracer.ts L65-68)
   NEXTSRV 의 BubbledError  => 조건 셋째로 통과해 위로 던져진다
   L1649 의 맨 Error         => `bubble = true` 를 달았지만 BubbledError 가 아니다.
                               dev 도 minimal 도 아니면 L1691-1693 으로 떨어져
                               **500 'Internal Server Error'** 를 쓴다
 ※ 이 갈래가 실제로 도는 조건은 좁다 — [01]에서 본다. 실행해 확인하지는 않았다
 ※ [요청 흐름] 02_normalize 의 L1688 요약 "err.bubble 이면 => throw" 는
   `isBubbledError(err) &&` 를 빠뜨렸다 (그 문서에 대한 제보다)
```

1. [미들웨어](01_middleware/README.md) — router-server 가 render server 를 한 번 더 부르고, 답을 (대개) 예외로 받아 헤더로 해석한다. 미들웨어가 던지면 render server 가 500 을 직접 그린다.
2. [라우트 핸들러](02_route-handler/README.md) — 페이지와 같은 길을 가다 템플릿에서 갈라진다. 정적/동적 판정이 **요청 객체 Proxy** 로 이뤄진다.
3. [웹소켓 업그레이드](03_upgrade/README.md) — `handleUpgrade` 는 비어 있다. 실제 길은 router-server 에 있다.

## 결과가 쓰이는 곳

```text
 미들웨어의 FetchEventResult (BubbledError.result)
      --> RROUTES L607-610 이 받아 **응답 헤더를 요청 헤더로 옮겨 적는다**
          (x-middleware-override-headers · x-middleware-request-*)
      --> x-middleware-rewrite 이면 parsedUrl 을 바꿔 목록의 다음 칸으로 간다
          → 결국 invokeRender 의 invokePath 가 된다 → [요청 흐름] 으로
      --> 본문·리다이렉트면 RSRV L552-567 이 router-server 에서 바로 쓴다.
          render server 는 두 번째로 불리지 않는다

 라우트 핸들러의 Response
      --> ISR 이 아니면 ARTPL L375 sendResponse 로 곧장 나간다
      --> ISR 이면 캐시 항목(CachedRouteKind.APP_ROUTE)이 되어
          routeModule.handleResponse 의 응답 캐시로 간다 — [응답 나가기] 가 그린 캐시와 같은 층
      --> 핸들러 안의 revalidateTag 는 do() 끝의 executeRevalidates(ARMOD L397)로
          [재검증](../revalidation/README.md) 에 넘어간다

 업그레이드
      --> 외부 rewrite 목적지로 프록시되거나, 끊기거나,
          **사용자의 다른 'upgrade' 리스너 몫으로 남는다** (RSRV L1007-1008)
```

## 다루지 않는 것

router-server 의 나머지(i18n 로케일 리다이렉트 L297-346, 압축, `invokeRender` 뒤의 정적 파일 서빙 L581-687, dev 번들러 가상 파일), `resolveRoutes` 의 다른 칸(`middleware_next_data` L423 · headers · redirects · rewrites · `check_fs`)과 `fsChecker`(`filesystem.ts`)의 매칭, render server 의 초기화(`render-server.ts` 의 `initialize`)와 워커 프로세스 구조, `proxyRequest`(`proxy-request.ts`)의 http-proxy 사용, Edge 런타임 샌드박스(`server/web/sandbox/`)의 내부와 Edge 로 도는 라우트 핸들러(`build/templates/edge-app-route.ts` · `server/web/edge-route-module-wrapper.ts`), Pages Router 의 API 라우트(`pages/api`, NEXTSRV `handleApiRequest`), `RouteModule` 기반 클래스(`route-module.ts`)의 `prepare`(L594) · `handleResponse`(L1109)와 응답 캐시, 서버 액션이 라우트 핸들러와 공유하는 `actionAsyncStorage`, 그리고 dev 서버가 덮어쓰는 `runMiddleware`(`next-dev-server.ts` L445) · `getMiddleware`(L723) · `ensureMiddleware`(L742)의 세부는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 미들웨어](01_middleware/README.md)
- [02 라우트 핸들러](02_route-handler/README.md)
- [03 웹소켓 업그레이드](03_upgrade/README.md)
