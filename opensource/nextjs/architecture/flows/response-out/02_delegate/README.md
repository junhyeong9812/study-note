# 02 라우트 모듈로 넘기기

상위: [응답이 만들어져 나가기까지](../README.md)

[01]이 플래그를 다 세운 뒤의 170줄이다. 여기서 base-server 는 **렌더를 포기하고 넘긴다.** 그리고 넘기기 전에 지금까지 쌓아 온 상태를 원본 노드 객체로 옮긴다.

## 위치

`packages/next` / `src/server` / `base-server.ts` L2440-L2609 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L2440-L2609))

## 실제 코드

이 메서드의 마지막 여섯 줄이 전부다.

```ts
// base-server.ts L2603-L2608
    await components.ComponentMod.handler(handlerReq, handlerRes, {
      waitUntil: this.getWaitUntil(),
    })

    // response is handled fully in handler
    return null
```

```text
 // response is handled fully in handler
 return null

 => 응답을 라우트 모듈이 **처음부터 끝까지** 쓴다.
    base-server 는 null 을 돌려주고 [03]이 그것을 보고 돌아선다
```

## 동작 흐름

```text
 BASE L2440-2609

 --- 캐시 인스턴스 ---
 L2450  incrementalCache = await this.getIncrementalCache({
 L2452    requestHeaders: Object.assign({}, req.headers),
        })
 L2456  incrementalCache.resetRequestCache()
          주석 L2455 - "TODO: investigate, this is not safe across
                        multiple concurrent requests"
          ★ 소스가 스스로 **동시 요청에 안전하지 않다**고 적어 놓았다
        ※ L2449 주석은 "use existing incrementalCache instance if available" 이라고
          말하지만, NEXTSRV L445 의 구현은 호출마다 `new IncrementalCache(...)` 를 만든다.
          주석과 구현이 어긋난다 (내 관찰이다 — 왜인지는 확인하지 않았다)

 --- 개발 전용: 정적 경로를 그때그때 만든다 ---
 L2458  routeModule?.isDev && 동적 라우트이고 (getStaticPaths 나 app 경로)이면
 L2464    dev 이면
 L2465      getStaticPathsStart = process.hrtime.bigint()
 L2468    pathsResults = await this.getStaticPaths({pathname, urlPathname, ...})
          ★★ BASE 의 getStaticPaths(L2033-2056)는 **아무것도 계산하지 않는다**
               L2051-2053  // `staticPaths` is intentionally set to `undefined`
                           //  as it should've been caught when checking disk data.
                           staticPaths: undefined,
             실제로 경로를 만드는 것은 DEV L815 의 오버라이드뿐이다
          => 이 블록 전체(L2458-2528)는 **개발 서버에서만** 값이 들어온다.
             L2458 의 `routeModule?.isDev` 가 그것을 가리킨다
          ★ [01]이 찾은 "staticPaths 는 대입이 없다" 의 가장 강한 근거가 이 주석이다
 L2476    dev 이고 결과가 있으면 devGenerateStaticParamsDuration 메타에 소요 시간을 심는다
 L2484    app 경로이고 cacheComponents 이면
 L2504      prerenderedRoutes 를 돌며 이 URL 에 맞는 것 중
 L2509        **fallbackRouteParams 가 가장 적은 것**을 고른다
 L2516      고른 것이 있고 비어 있지 않으면
 L2520        addRequestMeta(req, 'fallbackParams', createOpaqueFallbackRouteParams(...))
              주석 L2486-2500 - 프로덕션 빌드가 프리렌더 매니페스트에 써 두는
                URL 별 폴백 집합을 **개발에서 그때그때 복제**한다.
                완전히 구체적인 라우트(/blog/a)는 폴백 파라미터가 0개라
                자기 URL 에 대해 가장 구체적인 매치이므로 함께 견줘야 한다

 --- OPTIONS 거절 ---
 L2531  메서드가 OPTIONS 이고 404 페이지도 아니고
        (라우트 모듈이 없거나 app route 모듈이 아니면)
 L2536    await sendResponse(req, res, new Response(null, {status: 400}))
 L2537                                          => return null   [이른 출구 5]
          주석 L2530 - "An OPTIONS request to a page handler is invalid."

 --- ★★ 원본 꺼내기 ---
 L2540  request  = isNodeNextRequest(req) ? req.originalRequest : req
 L2541  response = isNodeNextResponse(res) ? res.originalResponse : res

 --- URL 되돌리기 ---
 L2543  parsedInitUrl = parseUrl(요청 메타 initURL || req.url)
 L2544  initPathname = parsedInitUrl.pathname || '/'
 L2546  segmentPrefetchRSC / rsc 노멀라이저를 차례로 대 보고 맞으면 정규화한다
 L2558  !(minimalMode && isErrorPathname) 이면
 L2559    request.url = `${initPathname}${parsedInitUrl.search || ''}`
          주석 L2555-2557 - minimal 모드에서는 동적 라우트의 요청 URL 이
            실제 URL 이 아니라 **문자 그대로의 '/[slug]'** 일 수 있다.
            initPathname 으로 덮어써 되돌린다

 --- ★★★ 메타를 원본으로 옮긴다 ---
 L2563  setRequestMeta(request, getRequestMeta(req))
 L2564  addRequestMeta(request, 'distDir', this.distDir)
 L2565  addRequestMeta(request, 'query', query)
 L2566  addRequestMeta(request, 'params', opts.params)
 L2567  addRequestMeta(request, 'minimalMode', this.minimalMode)
 L2569  opts.err 가 있으면 addRequestMeta(request, 'invokeError', opts.err)

 --- 개발 전용 프록시 ---
 L2573  maybeDevRequest = (선언 시작)
 L2578    process.env.NODE_ENV === 'development' 이면 request 를 Proxy 로 감싼다
 L2580    get 트랩 — 함수면 bind 해서 돌려준다
 L2586    set 트랩 — 'fetchMetrics' 면 **원래 req 에도** 써 준다
          주석 L2574-2577 - fetch 지표는 응답 close 시점에 기록되는데
            그때는 handler 가 아직 resolve 되지 않았다. 기다릴 수 없어서 가로챈다

 --- 넘긴다 ---
 L2598  handlerReq = maybeDevRequest      (@ts-expect-error)
 L2601  handlerRes = response             (@ts-expect-error)
 L2603  await components.ComponentMod.handler(handlerReq, handlerRes, {
           waitUntil: this.getWaitUntil(),
         })
 L2608                                          => return null
```

```text
 ★★★ 여기가 프레임워크 경계다

 [요청 흐름]이 다듬어 온 것은 Next 의 래퍼(BaseNextRequest / BaseNextResponse)였다.
 L2540-2541 이 그 **껍질을 벗겨** 원본 노드 객체를 꺼낸다.
 L2563 이 그동안 쌓은 요청 메타를 **원본 쪽으로 통째로 복사**한다.

 => 라우트 모듈은 Next 의 래퍼를 모른다. 노드의 req/res 와
    거기 심긴 메타만 본다
 => [요청 흐름]이 `addRequestMeta` 로 심어 온 것들
    (locale · isRSCRequest · postponed · match · fallbackParams · incrementalCache ...)이
    전부 이 한 줄로 건너간다
```

```ts
// base-server.ts L2540-L2541
    const request = isNodeNextRequest(req) ? req.originalRequest : req
    const response = isNodeNextResponse(res) ? res.originalResponse : res
```

```ts
// base-server.ts L2562-L2567
    // propagate the request context for dev
    setRequestMeta(request, getRequestMeta(req))
    addRequestMeta(request, 'distDir', this.distDir)
    addRequestMeta(request, 'query', query)
    addRequestMeta(request, 'params', opts.params)
    addRequestMeta(request, 'minimalMode', this.minimalMode)
```

```text
 ★ waitUntil 이 여기서 쓰인다 (L2604)

   waitUntil: this.getWaitUntil()

 getWaitUntil(BASE L1949-1974)은 순서가 있다
   L1950  getBuiltinRequestContext() 가 있으면 => 그쪽 waitUntil 을 쓴다  (먼저다)
   L1960  그게 없고 minimalMode 이면        => undefined
   L1973  둘 다 아니면                      => getInternalWaitUntil()

 => 그러므로 "minimalMode 면 undefined" 는 **플랫폼 컨텍스트가 없을 때만** 참이다.
    주석 L1966-1969 가 못박는다 — Edge 런타임 샌드박스에서는 waitUntil 이
    "@next/request-context" 로 전달되므로 **여기까지 오지 않는다**
 => 플랫폼도 안 주고 minimalMode 이면 그때 라우트 모듈의 `after()` 가 에러를 낸다.
    base-server 는 noop 을 주는 대신 없는 것을 없다고 넘긴다
```

## 결과가 쓰이는 곳

```text
 원본 노드 request 에 심긴 메타
      --> 라우트 모듈의 handler 가 읽는다. 이 흐름의 실제 산출물이다

 request.url (L2559 에서 다시 쓴 것)
      --> 라우트 모듈이 보는 URL. minimal 모드에서 '/[slug]' 로 오던 것이
          여기서 실제 경로로 되돌아간다

 요청 메타 'fallbackParams'
      --> 개발 중 PPR 폴백 셸 렌더. 프로덕션에서는 매니페스트가 대신한다

 return null
      --> [03]의 pipeImpl L1871 이 받는다. 그대로 돌아선다
```

## 다루지 않는 것

`components.ComponentMod.handler` 안쪽(라우트 모듈의 실제 실행), `getIncrementalCache`(L414, abstract)와 `IncrementalCache` 의 구현, `getStaticPaths`(L2033)와 `generateStaticParams` 의 관계, `createOpaqueFallbackRouteParams` 와 PPR 폴백 파라미터의 형식, `prerenderedRoutes` / `fallbackRouteParams` 가 빌드에서 만들어지는 과정, `nextConfig.cacheComponents` 의 의미, `sendResponse` 의 구현, `setRequestMeta` / `getRequestMeta` 의 저장 방식(심볼 키), `NodeNextRequest.originalRequest` 래퍼의 구조는 이 문서의 범위 밖이다.
