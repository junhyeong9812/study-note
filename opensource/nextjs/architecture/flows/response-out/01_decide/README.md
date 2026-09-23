# 01 무엇을 할지 정하기

상위: [응답이 만들어져 나가기까지](../README.md)

`renderToResponseWithComponentsImpl` 의 앞 330줄이다. 렌더를 하지 않는다. **렌더가 어떤 성격이어야 하는지를 정한다.** L2122-2353 의 최상위 `const` / `let` 선언을 세면 스물셋이다(중첩된 것은 뺐다).

## 위치

`packages/next` / `src/server` / `base-server.ts` L2110-L2440 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L2110-L2440))

## 실제 코드

들머리에서 페이지의 정체를 묻는 질문들이 줄줄이 나온다.

```ts
// base-server.ts L2122-L2133
    const isErrorPathname = pathname === '/_error'
    const is404Page =
      pathname === '/404' || (isErrorPathname && res.statusCode === 404)
    const is500Page =
      pathname === '/500' || (isErrorPathname && res.statusCode === 500)
    const isAppPath = components.isAppPath === true

    const hasServerProps = !!components.getServerSideProps
    const isPossibleServerAction = getIsPossibleServerAction(req)
    let isSSG = !!components.getStaticProps
    // NOTE: Don't delete headers[RSC] yet, it still needs to be used in renderToHTML later
    const isRSCRequest = getRequestMeta(req, 'isRSCRequest') ?? false
```

## 동작 흐름

```text
 renderToResponseWithComponentsImpl  BASE L2110-2609 중 앞부분

 --- 정체 묻기 ---
 L2119  pathname === UNDERSCORE_NOT_FOUND_ROUTE 이면 pathname = '/404'
 L2122  isErrorPathname        = pathname === '/_error'
 L2123  is404Page  = '/404' 이거나 (_error 이고 상태가 404)
 L2125  is500Page  = '/500' 이거나 (_error 이고 상태가 500)
 L2127  isAppPath              = components.isAppPath === true
 L2129  hasServerProps         = !!components.getServerSideProps
 L2130  isPossibleServerAction = getIsPossibleServerAction(req)
 L2131  isSSG (let)            = !!components.getStaticProps
 L2133  isRSCRequest           = getRequestMeta(req, 'isRSCRequest') ?? false

 --- CDN 오염 방어 본문 ---
 L2141  네 조건이 **다** 참이면
 L2142    !this.minimalMode
 L2143    nextConfig.experimental.validateRSCRequestHeaders   (기본값 true)
 L2144    isRSCRequest
 L2148    !is404Page
        ★★ 첫 조건이 결정적이다 — **minimalMode 에서는 이 방어가 통째로 꺼진다.**
           CDN 이 실제로 앞에 있는 배포 형태가 minimalMode 인데 그렇다
        ※ 왜 끄는지 소스에 근거 주석이 없다. 플랫폼이 대신 한다고 보는 듯하다 (내 해석)
        주석 L2145-2147 - NoFallbackError 를 서빙하는 중이면 헤더가 이미 벗겨져
          비교가 **언제나 실패한다**. 그대로 두면 리다이렉트 고리가 된다
 L2152    prefetchHeaderValue = headers[NEXT_ROUTER_PREFETCH_HEADER]
 L2153    routerPrefetch
 L2156      헤더가 있으면 '1' '2' '3' 만 인정하고 나머지는 undefined 로 버린다
 L2164      헤더가 없으면 요청 메타 isPrefetchRSCRequest 가 참일 때만 '1'
            주석 L2161-2163 - 런타임 프리페치는 언제나 동적 요청이라
              중간 계층이 헤더를 벗길 일이 없다. 그래서 **정적 프리페치만** 여기서 다룬다
 L2168    segmentPrefetchRSCRequest = 헤더 또는 요청 메타
 L2172    expectedHash = await computeCacheBustingSearchParam(네 값)
 L2178    actualHash = 요청 메타 ?? URL 의 _rsc 검색 파라미터
 L2184    matchesHash = expectedHash === actualHash
 L2185    안 맞고 actualHash 가 null 이 아니면
 L2187      **구형 해시 형식**으로 한 번 더 비교한다
 L2196    그래도 안 맞으면
 L2206      url = new URL(초기 URL)
 L2210      setCacheBustingSearchParamWithHash(url, expectedHash)
 L2211      res.statusCode = 307
 L2212      res.setHeader('location', ...)
 L2213      res.body('').send()
 L2214                                       => return null   [이른 출구 1]

 --- 경로 두 벌 ---
 L2221  urlPathname         = parseUrl(req.url).pathname
 L2223  resolvedUrlPathname = 요청 메타 rewrittenPathname || urlPathname
          주석 L2218-2220 - iSSG 캐시 키는 **rewrite 된 경로**로 잡는다.
            fallback:false 페이지도 rewrite 대상이 될 수 있어서다
 L2226  this.setVaryHeader(req, res, isAppPath, resolvedUrlPathname)

 --- SSG 인가 ---
 L2233  (아래 별항 — 세 항 중 둘이 죽었다)
 L2241  아니고 dev 도 아니면
 L2242    isSSG ||= !!prerenderManifest.routes[toRoute(pathname)]

 L2246  isNextDataRequest = (isNextDataReq 메타 || x-nextjs-data + webServerConfig)
                            && (isSSG || hasServerProps)

 L2257  isSSG 가 아닌데 x-middleware-prefetch 이고 404/_error 도 아니면
 L2262    x-matched-path 와 x-middleware-skip: 1 을 박고
 L2265    cache-control: private, no-cache, no-store, max-age=0, must-revalidate
 L2268    res.body('{}').send()
 L2269                                       => return null   [이른 출구 2]
          주석 L2254-2256 - 미들웨어 프리페치가 정적 데이터 라우트로 풀리지 않으면
            **예기치 않은 SSR 호출**을 피하려고 일찍 빠진다

 L2274  isSSG && minimalMode && x-matched-path && /_next/data 로 시작하면
 L2280    req.url 에서 데이터 접두를 뗀다
          주석 L2272-2273 - getStaticProps 에 노출되지 않는 경로다.
            asPath 가 /_next/data 를 드러내면 안 된다

 L2285  x-nextjs-data 이고 상태가 없거나 200 이면
 L2289    x-nextjs-matched-path 헤더를 붙인다
 L2291    값은 `${locale ? '/'+locale : ''}${pathname}` — **로케일 접두가 붙는다**

 --- PPR 판정 ---
 L2295  routeModule = components.routeModule
 L2304  couldSupportPPR       = isAppPPREnabled && routeModule 이 app 페이지인가
 L2311  hasDebugStaticShellQuery = 환경변수 + ?__nextppronly + couldSupportPPR
 L2317  exposeTestingApi      = dev || experimental.exposeTestingApiInProductionBuild
 L2325  hasInstantTestCookie  = exposeTestingApi && RSC 헤더가 아니고
                                쿠키에 테스트 쿠키가 있고 couldSupportPPR
 L2334  isRoutePPREnabled     = couldSupportPPR &&
                                (매니페스트의 renderingMode === 'PARTIALLY_STATIC'
 L2344                            || (hasDebugStaticShellQuery || hasInstantTestCookie)
 L2345                               && (exposeTestingApi || this.experimentalTestProxy === true))
          주석 L2340-2343 - 원래는 appConfig 를 봐야 하지만 개발 중에 그것을
            서버까지 끌어오려면 배선이 필요하다. 그래서 **개발이나 테스트 API 가
            열려 있을 때만** 지원한다고 가정한다
 L2350  minimalPostponed  = isRoutePPREnabled ? 요청 메타 postponed : undefined
 L2353  hasPostponedState = typeof minimalPostponed === 'string'

 --- 상태 코드 ---
 L2356  is404Page 이고 데이터 요청도 RSC 도 아니면
 L2357    res.statusCode = 404
 L2361    GET/HEAD 이고 sec-fetch-dest 가 HTML 이 아니면
 L2365      Cache-Control: private, no-cache, ...
 L2369      Content-Type: text/plain; charset=utf-8
 L2370      res.body('Not Found').send()
 L2371                                     => return null   [이른 출구 3]
            주석 L2359-2360 - 이미지·폰트 같은 **하위 리소스 요청**에는
              not-found 라우트를 렌더하지 않고 평문 404 를 준다
 L2377  STATIC_STATUS_PAGES 에 들면 경로에서 숫자를 떼어 상태 코드로 쓴다

 L2381  서버 액션도 재개도 아니고 404/500/_error 도 아닌데
        메서드가 GET/HEAD 가 아니고 (정적 컴포넌트이거나 SSG)이면
 L2393    res.statusCode = 405
 L2394    res.setHeader('Allow', ['GET', 'HEAD'])
 L2395    res.body('Method Not Allowed').send()
 L2396                                     => return null   [이른 출구 4]

 --- 유일하게 payload 를 만드는 자리 ---
 L2400  components.Component 이 **문자열**이면
 L2401    => return {body: RenderResult.fromStatic(components.Component, ...)}
          ★ 빌드가 HTML 을 통째로 구워 둔 페이지다. 렌더할 것이 없다

 --- 동적 응답을 켤지 ---
 L2409  opts.supportsDynamicResponse === true 이면
 L2411    isBotRequest = isBot(ua)
 L2412    isSupportedDocument = Document 에 getInitialProps 가 없거나 내장 Document 이면
 L2422    opts.supportsDynamicResponse = !isSSG && !isBotRequest && isSupportedDocument
          주석 L2417-2418 - 생성되지 않을 것이 뻔한 경우에 동적 HTML 을 꺼
            **캐시 키를 계속 만들 수 있게** 한다
 L2427  데이터 요청이 아니고 app 경로이고 dev 이면
 L2428    opts.supportsDynamicResponse = true    (개발에서는 언제나 동적)

 --- 경로 다듬기 ---
 L2431  isSSG && minimalMode && x-matched-path 이면 resolvedUrlPathname = urlPathname
 L2436  둘 다 끝 슬래시를 뗀다
 L2438  localeNormalizer 가 있으면 resolvedUrlPathname 을 정규화
 L2444  isNextDataRequest 이면 둘 다 데이터 접두를 뗀다
```

```text
 ★★★ 세 항 중 **둘이 죽어 있다** (L2233-2243)
```

```ts
// base-server.ts L2228-L2243
    let staticPaths: string[] | undefined
    let hasFallback = false

    const prerenderManifest = this.getPrerenderManifest()

    if (
      hasFallback ||
      staticPaths?.includes(resolvedUrlPathname) ||
      // this signals revalidation in deploy environments
      // TODO: make this more generic
      req.headers['x-now-route-matches']
    ) {
      isSSG = true
    } else if (!this.dev) {
      isSSG ||= !!prerenderManifest.routes[toRoute(pathname)]
    }
```

```text
 L2228  let staticPaths: string[] | undefined     ← 이 함수에서 **대입이 없다**
 L2229  let hasFallback = false                   ← **재대입이 없다**

 전수로 grep 하면 이 둘은 L2228/2229 선언과 L2234/2235 사용이 전부다
 (L2476 의 `pathsResults.staticPaths` 는 다른 객체의 속성이다)

 => `hasFallback` 은 언제나 false, `staticPaths?.includes(...)` 는 언제나 undefined.
    실제로 살아 있는 항은 **`req.headers['x-now-route-matches']` 하나뿐**이다
 주석 L2236-2237 - "this signals revalidation in deploy environments
                    TODO: make this more generic"
 ※ 예전에 이 둘을 채우던 코드가 있었을 것이다. 그 이력은 확인하지 않았다
```

```text
 ★★ CDN 오염 방어는 해시 **두 벌**을 받아 준다 (L2184-2194)

 L2184  matchesHash = expectedHash === actualHash
 L2185  안 맞았는데 actualHash 가 null 도 아니면
 L2187    computeLegacyCacheBustingSearchParam(...) === actualHash 로 한 번 더

 주석 L2186 - "We'll fallback to checking the legacy hash format to support
               clients that do not have a secure context"
 => 보안 컨텍스트(HTTPS)가 아닌 브라우저는 SubtleCrypto 를 못 써서
    구형 5글자 `_rsc` 형식을 보낸다. 그것도 받아 준다
```

```ts
// base-server.ts L2196-L2215
      if (!matchesHash) {
        // The hash sent by the client does not match the expected value.
        // Redirect to the URL with the correct cache-busting search param.
        // This prevents cache poisoning attacks on CDNs that don't respect Vary headers.
        // We continue to accept the legacy short hash for clients that still
        // generate the 5-character `_rsc` form.
        // Note: When no headers are present, expectedHash is empty string and client
        // must send `_rsc` param, otherwise actualHash is null and hash check fails.
        // `req.url` may have had its basePath removed during normalization.
        // Build the redirect from the original URL so it remains public-facing.
        const url = new URL(
          getRequestMeta(req, 'initURL') || req.url || '',
          'http://localhost'
        )
        setCacheBustingSearchParamWithHash(url, expectedHash)
        res.statusCode = 307
        res.setHeader('location', `${url.pathname}${url.search}`)
        res.body('').send()
        return null
      }
```

```text
 => 안 맞으면 거절이 아니라 **307 로 옳은 URL 에 다시 보낸다**
 주석 L2202-2203 - 헤더가 하나도 없으면 expectedHash 는 빈 문자열이고
   클라이언트는 `_rsc` 파라미터를 반드시 보내야 한다. 안 보내면
   actualHash 가 null 이라 검사에 걸린다
 주석 L2204-2205 - req.url 은 정규화 중에 basePath 가 떨어졌을 수 있다.
   **초기 URL** 로 리다이렉트를 만들어야 바깥에서 통한다
```

## 결과가 쓰이는 곳

```text
 opts.supportsDynamicResponse
      --> [02]가 넘기는 renderOpts 에 실려 라우트 모듈이 읽는다.
          봇이거나 SSG 면 꺼진다

 isRoutePPREnabled / minimalPostponed / hasPostponedState
      --> PPR 재개 여부. [요청 흐름]의 x-matched-path 블록이 심은
          postponed 메타가 여기서 쓰인다

 urlPathname / resolvedUrlPathname
      --> [02]가 request.url 을 다시 쓸 때의 기준

 res.statusCode
      --> 이른 출구 넷이 307 · 404 · 405 를 직접 박고 나간다.
          payload 없이 소켓으로 간다
```

## 다루지 않는 것

`computeCacheBustingSearchParam` / `computeLegacyCacheBustingSearchParam` 의 해시 계산과 `setCacheBustingSearchParamWithHash`, `setVaryHeader`(L2226)의 헤더 규칙, `getPrerenderManifest`(L378, abstract)가 읽는 매니페스트의 형식, `isAppPageRouteModule` 등 라우트 모듈 판별 함수, PPR 의 `renderingMode` 값과 `PARTIALLY_STATIC` 의 의미, Instant Navigation Testing API 와 `NEXT_INSTANT_TEST_COOKIE`, `isNonHtmlSecFetchDest` 가 보는 `sec-fetch-dest` 값, `STATIC_STATUS_PAGES` 의 목록, `getIsPossibleServerAction` 의 판별, `stripNextDataPath`(L2611) · `localeNormalizer` 의 본문은 이 문서의 범위 밖이다.
