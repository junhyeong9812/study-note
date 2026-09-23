# 05 렌더로 들어가기

상위: [요청이 들어와서 렌더로 가기까지](../README.md)

[04]가 되돌려 준 `this.render(...)` 부터를 따라간다. 이 흐름의 마지막 구간이다. 여기에 **위로 되돌아가는 고리**가 하나 있다.

## 위치

`packages/next` / `src/server` / `base-server.ts` L1936-L2031 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L1936-L2031))

`packages/next` / `src/server` / `base-server.ts` L2704-L2863 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L2704-L2863))

## 실제 코드

`render` 도 추적 껍데기다.

```ts
// base-server.ts L1944-L1946
    return getTracer().trace(BaseServerSpan.render, async () =>
      this.renderImpl(req, res, pathname, query, parsedUrl, internalRender)
    )
```

## 동작 흐름

```text
 renderImpl  BASE L1980-2031

 L1988  pathname 이 '/' 로 시작하지 않으면
 L1989    console.warn('Cannot render page with path ... did you mean ...')
          ★ 경고만 한다. 막지 않는다
 L1994  customServer 이고 pathname === '/index' 이고 /index 페이지가 없으면
 L2001    pathname = '/'
            주석 L1999-2000 - 커스텀 서버 하위 호환
 L2004  ua = req.headers['user-agent'] || ''
 L2005  this.renderOpts.botType = getBotType(ua)

 L2011  ★★ !internalRender && !minimalMode && !isNextDataReq 이고
        L2015   req.url 이 /_next/ 로 시작하거나
        L2016   (hasStaticDir && req.url 이 /static/ 으로 시작)하면
 L2018    => return this.handleRequest(req, res, parsedUrl)
          ★★★ **[01]의 맨 위로 되돌아간다**

 L2021  isBlockedPage(pathname) 이면
 L2022    => return this.render404(req, res, parsedUrl)

 L2025  => return this.pipe((ctx) => this.renderToResponse(ctx), {req, res, pathname, query})
```

```text
 ★★★ 흐름이 고리다 — renderImpl 이 handleRequest 를 다시 부른다

 주석 L2009-2010
   "we don't modify the URL for _next/data request but still
    call render so we special case this to prevent an infinite loop"

 => 무한 고리가 **실제 위험**이었다. 가드 넷이 그것을 막는다
      internalRender    [04]가 부를 때 true 를 넘긴다 (NEXTSRV L1124 / L1189)
      minimalMode       서버리스에서는 정적 파일을 플랫폼이 처리한다
      isNextDataReq     데이터 요청은 URL 을 안 고쳐서 다시 오면 또 걸린다
      URL 패턴          /_next/ 나 /static/ 일 때만

 => 커스텀 서버가 아무 URL 로나 render() 를 부를 수 있어서 생긴 길이다
    주석 L2007-2008 - "we allow custom servers to call render for all URLs
      so check if we need to serve a static _next file or not."
```

```ts
// base-server.ts L2009-L2019
    // we don't modify the URL for _next/data request but still
    // call render so we special case this to prevent an infinite loop
    if (
      !internalRender &&
      !this.minimalMode &&
      !getRequestMeta(req, 'isNextDataReq') &&
      (req.url?.match(/^\/_next\//) ||
        (this.hasStaticDir && req.url!.match(/^\/static\//)))
    ) {
      return this.handleRequest(req, res, parsedUrl)
    }
```

```text
 renderToResponseImpl  BASE L2704-2863

 L2709  bubbleNoFallback = getRequestMeta(ctx.req, 'bubbleNoFallback') ?? false
        ([04] L1090 이 심은 값이다)
 L2712  !minimalMode && validateRSCRequestHeaders 이면
 L2716    addRequestMeta(ctx.req, 'cacheBustingSearchParam', query[NEXT_RSC_UNION_QUERY])
 L2722  delete query[NEXT_RSC_UNION_QUERY]

 L2724  options = {i18n: this.i18nProvider?.fromRequest(req, pathname)}
 L2728  existingMatch = getRequestMeta(ctx.req, 'match')     ([04] L1131 이 심었다)
 L2730  fastPath = true
 L2733  invokeOutput = getRequestMeta(ctx.req, 'invokeOutput')
 L2735  아래 둘 중 하나면 fastPath = false
          (가) !minimalMode && invokeOutput 이 동적 라우트인데 기존 매치와 다르다
          (나) existingMatch 의 page 가 '/@' 를 담고 있다 (병렬 라우트)
              주석 L2740-2742 - 병렬 라우트는 매치가 여럿일 수 있어
                기존 매치가 맞는 것이라는 보장이 없다

 L2748  try {
 L2749    ★ for await (const match of fastPath && existingMatch
 L2750                                 ? [existingMatch]
 L2751                                 : this.matchers.matchAll(pathname, options)) {
 L2752      !minimalMode && invokeOutput 이 동적인데 이 매치와 다르면
 L2758        continue
 L2761      result = await this.renderPageComponent({...ctx, pathname, renderOpts},
                                                    bubbleNoFallback)
            ★★ 이것도 NEXTSRV L781 이 덮어쓴 것이다 (아래 별항)
 L2772      result !== false 이면                    => return result
 L2773    }
 L2780    webServerConfig 가 있으면
 L2782      ctx.pathname = webServerConfig.page
 L2783      result = await this.renderPageComponent(ctx, bubbleNoFallback)
 L2784      result !== false 이면                    => return result
              주석 L2775-2778 - Edge 함수는 x-matched-path 헤더를 못 받아서
                동적 라우트로 못 맞췄을 때 현재 페이지로 되돌아가야 한다
            ★ 이 갈래는 **잔재로 보인다** — 아래 별항

 L2786  } catch (error) {
 L2789    MissingStaticPage 이면 진단 정보를 찍고   => throw
 L2808    NoFallbackError 이고 bubbleNoFallback 이면 => throw   (위로 올린다)
 L2811    DecodeError / NormalizeError 이면
 L2812      res.statusCode = 400                     => return renderErrorToResponse
 L2816    res.statusCode = 500
 L2820    pages/500 이 있으면 customErrorRender 표시를 켜고 한 번 렌더한 뒤 끈다
              주석 L2818-2819 - /_error 의 getInitialProps 를 태워 에러 보고를 돌게 한다
 L2828    WrappedBuildError 가 아니면
 L2829      minimalMode 이거나 dev 이면 err.page = page 를 붙여 => throw
 L2833      아니면 this.logError(...)
 L2835    => return await this.renderErrorToResponse(ctx, 감싼 것이면 innerError)
 L2840  }

        (루프를 다 돌아도 아무도 안 받았을 때)
 L2842  middleware = await this.getMiddleware()
 L2843  middleware 가 있고 x-nextjs-data 헤더가 있고 상태가 없거나 200/404 이면
 L2850    x-nextjs-matched-path 헤더에 로케일 붙인 경로를 담고
 L2854    200 + Content-Type: JSON + 본문 '{}' 로 보낸다
 L2858    => return null
 L2861  res.statusCode = 404
 L2862  => return this.renderErrorToResponse(ctx, null)
```

```text
 ★★ 라우트 선택은 표 조회가 아니다. **순차 시도 + 첫 성공 반환**이다

 renderPageComponent 의 `false` 는 "내가 응답을 끝냈다" 의 부정이 아니라
 **"내 것이 아니다. 다음 매치로 가라"** 는 감시값이다 (L2772 / L2784)

 => [04]의 `true` 일곱, handleRSCRequest 의 `false` 다섯,
    그리고 이 `false`(BASE L2678)가 전부 다른 계약이다
 ★ 여기에 `null` 이 하나 더 있다 — NEXTSRV L806. 세 번째 값이다
```

```text
 ★★★ 렌더가 base 에서 끝나지 않을 수 있다 — NEXTSRV L781 이 가로챈다

 L2761 의 this.renderPageComponent 는 BASE L2640 이 아니라 NEXTSRV L781 로 간다

   NEXTSRV L785  edgeFunctionsPages = this.getEdgeFunctionsPages() || []
           L796  그중 이 페이지와 같은 것이 있으면
           L798    await this.runEdgeFunction({...})
           L806    => return null
           L811  아니면 => return super.renderPageComponent(ctx, bubbleNoFallback)

 ★ `null` 은 `false` 가 아니다. 그래서 L2772 의 `result !== false` 를 **통과한다**
 => Edge 함수로 서빙되는 페이지는 응답을 하위 클래스가 만들고
    base 의 렌더 파이프라인은 그 결과를 그대로 흘려보낸다
```

```text
 ★ webServerConfig 갈래(L2780)는 지금 주인이 없다

 L2779 · L2781  // @ts-expect-error extended in child class web-server
 => `web-server` 라는 하위 클래스를 가리키는데
    v16.3.6 트리에 `web-server.ts` 도 `NextWebServer` 클래스도 **없다**
    BASE L1966 의 "NOTE: for edge functions, `NextWebServer` always runs in
    minimal mode" 주석도 같은 잔재다
 ※ "지워졌다" 는 내 관찰이다. 언제 왜 없어졌는지는 확인하지 않았다
```

```text
 ★★ CDN 캐시 오염 방어가 여기 있다
```

```ts
// base-server.ts L2135-L2140
    // Not all CDNs respect the Vary header when caching. We must assume that
    // only the URL is used to vary the responses. The Next client computes a
    // hash of the header values and sends it as a search param. Before
    // responding to a request, we must verify that the hash matches the
    // expected value. Neglecting to do this properly can lead to cache
    // poisoning attacks on certain CDNs.
```

```text
 => 헤더에 따라 응답이 갈리는데 CDN 이 URL 만 보고 캐시하면
    A 사용자의 응답이 B 에게 간다.
    그래서 **클라이언트가 헤더 값의 해시를 검색 파라미터로 보내** URL 에 섞고
    서버가 그 해시를 검증한다

 ★ 규칙대로 플래그 식을 끝까지 읽었다
   조건 L2141-2149  !this.minimalMode && experimental.validateRSCRequestHeaders
                    && isRSCRequest(L2144) && !is404Page(L2148)
                    주석 L2145-2147 - NoFallbackError 를 서빙하는 중이면 헤더가 이미
                      벗겨져 있어 비교가 **언제나 실패한다**. 그대로 두면 리다이렉트 고리가 된다
   config-shared.ts L2228  validateRSCRequestHeaders: true
   => **기본값이 true 다. 살아 있는 코드다** (experimental 이라는 이름에 속으면 안 된다)
   => minimalMode 에서 끄는 것은 그 환경의 플랫폼이 이미 처리하기 때문으로 보인다
      (※ 뒷문장은 내 해석이다. 소스에 근거 주석이 없다)

 L2712-2721 이 짝이다 — 검증에 쓸 파라미터를 요청 메타에 먼저 심는다
```

```text
 ★ getWaitUntil 이 minimalMode 의 뜻을 가장 분명히 말한다 (L1949-1974)

 L1950  getBuiltinRequestContext() 가 있으면 => return 그 waitUntil
 L1960  this.minimalMode 이면               => return undefined
 L1973                                      => return this.getInternalWaitUntil()
```

```ts
// base-server.ts L1960-L1971
    if (this.minimalMode) {
      // we're built for a serverless environment, and `waitUntil` is not available,
      // but using a noop would likely lead to incorrect behavior,
      // because we have no way of keeping the invocation alive.
      // return nothing, and `after` will error if used.
      //
      // NOTE: for edge functions, `NextWebServer` always runs in minimal mode.
      //
      // NOTE: if we're in an edge runtime sandbox, waitUntil will be passed in using "@next/request-context",
      // so we won't get here.
      return undefined
    }
```

```text
 => minimalMode = **서버리스**. 응답을 보내면 실행이 끝난다.
    "응답 뒤에 뭘 더 한다"(after)를 지원할 방법이 없다.
    조용히 넘기는 noop 대신 **에러를 고른다**

 L1976 getInternalWaitUntil 은 `return undefined` 한 줄이다.
   NEXTSRV L2176 이 덮어쓴다 — [README]의 확장점 (다) 셋 중 하나다
```

## 결과가 쓰이는 곳

```text
 renderToResponse 의 반환 (ResponsePayload | null)
      --> pipe / pipeImpl(L1832 / L1846)이 받아 응답으로 흘려보낸다

 요청 메타 'cacheBustingSearchParam'
      --> renderToResponseWithComponentsImpl(L2110)의 CDN 방어가 검증한다

 renderPageComponent 로 넘어간 ctx
      --> renderOpts.params 에 라우트 파라미터가 담겨 있다.
          여기서부터 App Router(app-render.tsx) 또는
          Pages Router(render.tsx) 로 갈린다 — 다른 흐름의 시작이다
```

## 다루지 않는 것

`renderPageComponent` 와 `findPageComponents`(L365, abstract)가 컴포넌트를 찾는 방식, `renderToResponseWithComponents` / `Impl`(L2058 / L2110)의 본문 전체와 ISR·캐시 판정, `pipe` / `pipeImpl`(L1832 / L1846)의 응답 전송, `renderError` / `renderErrorToResponse` / `render404` 의 에러 페이지 경로, `getStaticPaths`(L2033) · `getStaticHTML`(L1913), `matchers.matchAll` 의 순서와 병렬 라우트(`/@`) 매칭, `NoFallbackError` / `WrappedBuildError` / `MissingStaticPage` 가 던져지는 자리, `renderOpts` 의 필드 전체, 그리고 렌더러 안쪽(`app-render.tsx` · `render.tsx`)은 이 문서의 범위 밖이다.
