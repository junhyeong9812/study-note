# App Router 가 페이지를 만드는 길

상위: [Next.js 아키텍처 지도](../../README.md)

[응답이 만들어져 나가기까지](../response-out/README.md)의 끝에서 `ComponentMod.handler` 로 넘어간 뒤를 따라간다. 그 handler 가 **여러 층을 지나** 부르는 것이 이 파일이다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `APPR` = `server/app-render/app-render.tsx`(10598줄).

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L3090-L3099 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L3090-L3099))

## 실제 코드

진입점은 타입 하나로 선언돼 있다.

```tsx
// app-render.tsx L3090-L3099
export type AppPageRender = (
  req: BaseNextRequest,
  res: BaseNextResponse,
  pagePath: string,
  query: NextParsedUrlQuery,
  fallbackRouteParams: OpaqueFallbackRouteParams | null,
  renderOpts: RenderOpts,
  serverComponentsHmrCache: ServerComponentsHmrCache | undefined,
  sharedContext: AppSharedContext
) => Promise<RenderResult<AppPageRenderResultMetadata>>
```

## 동작 흐름

```text
 ★★ handler 와 이 파일 사이에 층이 여럿이다

 base-server L2603  components.ComponentMod.handler(req, res, {waitUntil})
   +-- build/templates/app-page.ts L33   handler = entrypoint.handler
       +-- app-page-runtime.ts L197  async function handler
           L226  routeModule.prepare(...)          실패하면 400 으로 끝. **렌더 없음**
           L684  stripFlightHeaders(req.headers)   ★ 렌더 입력을 변형한다
           L1609 routeModule.handleResponse({cacheKey, responseGenerator, ...})
                 +-- 응답 캐시 (route-modules/route-module.ts)
                     ★★ **캐시에 맞으면 아래가 한 번도 안 돈다**
                     ★★ 백그라운드 재검증이면 **여러 번** 돈다
                     +-- doRender  app-page-runtime.ts L817
                         L903  enableTainting = nextConfig.experimental.taint
                         L996  forceStaticRender 면 supportsDynamicResponse = false
                               ★★★ isStaticGeneration 을 켜는 **실제 스위치**가 여기다
                         +-- invokeRouteModule  L740   (NodeNextRequest/Response 로 감싼다)
                             +-- route-modules/app-page/module.ts L152-166
                                 +-- renderToHTMLOrFlight      ← 이 파일

 ★ 두 번째 진입로도 있다
   route-modules/app-page/module.render.ts L3  lazyRenderAppPage
     <- next-server.ts L646 renderHTMLImpl
     <- export/routes/app-page.ts L78 (정적 내보내기)

 => "이 파일이 응답을 만든다" 는 절반만 맞다.
    렌더를 할지 말지는 **응답 캐시**가 정하고,
    renderOpts 는 doRender 가 마지막에 덮어쓴다
```

```text
 ★★ 이 파일의 지형 — 큰 함수 넷이 8할이다

   L8229-10224  prerenderToStream         1996줄   빌드·PPR 갈래
   L3258-4369   renderToStream            1112줄   요청 시각 갈래
   L2562-3088   renderToHTMLOrFlightImpl   527줄   오케스트레이터
   L7063-7474   validateInstantConfigs     412줄   검증
   (시작 줄부터 **닫는 중괄호까지** 센 값이다.
    다음 선언까지의 간격으로 재면 사이의 주석·타입이 섞여 각각 1999·1181·639·424 가 된다)

 L4418-8228 은 검증 기계다. 그 구간의 최상위 함수 54개 중
 **함수 이름**에 Dev 나 Valid 가 든 것이 22개다
 ※ "개발 전용" 이라고 쓰면 틀린다 — validateInstantConfigsInBuild(L7726)처럼
   빌드에서 도는 것도 섞여 있다 (내 관찰이다)
```

```text
 ★★★ 뼈대는 한 줄로 갈린다

 renderToHTMLOrFlight  L3101   헤더를 읽고 workStore 를 만든다
   +-- workAsyncStorage.run(workStore, renderToHTMLOrFlightImpl, ...)
       |                            ← AsyncLocalStorage
       renderToHTMLOrFlightImpl  L2562-3088
         L2577-2786  준비                                        [02]
         L2686       const { isStaticGeneration } = workStore
         L2787       ★ if (isStaticGeneration)                   [03]
                       +-- prerenderToStream  L8229   (1996줄)   프리렌더
                           L2868  streamToString(response.stream)
                                  ★ 스트림을 **문자열로 다 받는다**
                       else
                       +-- requestStore 를 만들고 (L2913)
                           isRSCRequest 면        네 갈래로            [03]
                           서버 액션이면          handleAction         [03]
                           그 밖이면              renderToStream L3258 (1112줄)
                           L3086  return new RenderResult(stream, options)
                                  ★ 스트림을 **그대로 넘긴다**
```

```text
 ★★★ 그런데 `isStaticGeneration` 은 **"빌드인가" 가 아니다**

 값의 정의는 이 파일이 아니라 async-storage/work-store.ts L116-119 에 있다
   const isStaticGeneration =
     !renderOpts.supportsDynamicResponse &&
     !renderOpts.isDraftMode &&
     !renderOpts.isPossibleServerAction

 => 빌드인지 요청인지를 **전혀 보지 않는다.**
    "동적 응답을 지원하지 않는가" 하나로 정해진다

 갈래 안쪽 주석이 그것을 말한다 (L2788-2789)
   "We're either building or revalidating. In either case we need to
    prerender our page rather than render it."
 => **또는 재검증(revalidate)** 이다. 프로덕션 ISR 은 요청 시각에 이 갈래를 탄다

 ★ 개발 서버는 이 갈래에 **절대 오지 않는다**
   build/templates/app-page-runtime.ts L558-560
     // If we're in development, we always support dynamic HTML, unless it's
     // a data request, in which case we only produce static HTML.
     routeModule.isDev === true ||
   => supportsDynamicResponse 가 참이므로 isStaticGeneration 은 거짓이다

 => 그러므로 이 2분기는 "빌드 / 요청" 이 아니라
    **"정적 응답을 만드는가 / 동적 응답을 흘리는가"** 다
```

```text
 ★★ PPR 재개는 **오히려 아래쪽(동적) 갈래**로 간다

 prerenderToStream 의 시그니처(L8229-8235)에 postponedState 가 **없다**.
 postponedState 를 받는 것은 renderToStream(L3258-3268)이고 호출은 L3027 뿐이다

 build/templates/app-page-runtime.ts L874-875
   supportsDynamicResponse: typeof postponed === 'string' || supportsDynamicResponse
 => postponed 가 있으면 supportsDynamicResponse 를 **강제로 켠다**
    따라서 PPR 재개 요청은 언제나 isStaticGeneration === false 다

 => [01]이 파싱한 postponedState 의 행선지는 위가 아니라 아래다.
    PPR 이 위쪽 갈래와 닿는 것은 "재개" 가 아니라 **셸을 미리 만드는 쪽**이다
```

1. [진입과 헤더 읽기](01_entry/README.md) — `workAsyncStorage.run` 과 프리페치 세 종류.
2. [준비](02_prepare/README.md) — `patchFetch` · 오염 표시 · `ctx` 만들기.
3. [갈림길](03_split/README.md) — 2분기와 RSC 네 갈래, 서버 액션.

```text
 ★★ 앞 흐름들과 이어지는 자리

 [응답 흐름]이 원본 노드 req 에 메타를 옮겨 심었다.
 여기서 그것을 다시 꺼낸다
   L2748  resolvedPathname = getRequestMeta(req, 'resolvedPathname')
   L2895  fallbackParams   = getRequestMeta(req, 'fallbackParams') || null
   L2896  hmrRefreshHash   = getRequestMeta(req, 'hmrRefreshHash')

 그리고 헤더도 읽는다. 그 이유를 주석이 말한다 (L3117-3118)
   "We read these values from the request object as, in certain cases,
    base-server will strip them to opt into different rendering behavior."

 ★★★ 이 문장은 "원본을 지킨다" 가 아니라 **그 반대**다
   벗겨진 **실물 req 객체**에서 읽는다는 뜻이다.
   base-server 가 렌더 동작을 바꾸려고 **일부러** 벗기기 때문에,
   그 벗겨진 상태가 반영되어야 한다

   app-render/strip-flight-headers.ts L10-13
     export function stripFlightHeaders(headers: IncomingHttpHeaders) {
       for (const header of FLIGHT_HEADERS) {
         delete headers[header]
       }
     }
   => `delete` 다. 요청 헤더를 **파괴적으로** 지운다

 => 이것이 위쪽 갈래로 들어가는 장치다.
    SSG + RSC 요청의 flight 헤더를 렌더 직전에 벗기면
    isRSCRequest 가 거짓이 되어 정적 응답이 만들어진다
```

## 결과가 쓰이는 곳

```text
 RenderResult
      --> [응답 흐름]으로 돌아가지 않는다. 다만 곧장 res 에 쓰이지도 않는다.
          doRender 가 {kind: APP_PAGE, html, rscData, postponed, ...} 로 감싸
          **응답 캐시에 넣고**(app-page-runtime.ts L1069-1080),
          그 뒤 엔트리포인트의 handler 가 sendRenderResult 로 쓴다.
          base-server 는 null 만 받았다

 workStore (AsyncLocalStorage)
      --> 렌더 트리의 서버 컴포넌트가 revalidate 와 fetch 지표를 기록한다
      ★ 동적 사용 여부(usedDynamic)는 workStore 가 아니라 **RequestStore** 에 있다
        (work-unit-async-storage.external.ts). 그리고 렌더 단위 상태는
        workAsyncStorage 가 아니라 **workUnitAsyncStorage** 가 나른다 —
        이 파일에서 workAsyncStorage.run 은 L3180 한 곳뿐이지만
        workUnitAsyncStorage.run 은 마흔 곳이 넘는다

 metadata (AppPageRenderResultMetadata)
      --> statusCode · fetchMetrics · hasPendingUi.
          RenderResult 에 실려 나간다
```

## 다루지 않는 것

`renderToStream`(L3258-4369, 1112줄)과 `prerenderToStream`(L8229-10224, 1996줄)의 본문, L4418-8228 의 검증 기계 전체(`runValidationInDev` · `validateStaticShell` · `validateStagedShell` · `validateInstantConfigs`), `handleAction`(`action-handler.ts` 1580줄)의 서버 액션 실행, `create-component-tree.tsx`(1307줄)가 로더 트리를 컴포넌트로 바꾸는 과정, `dynamic-rendering.ts`(1592줄)의 정적·동적 경계 판정, `collect-segment-data.tsx`(1528줄)와 세그먼트 캐시, `createWorkStore` / `createRequestStoreForRender` 의 필드 전체, React Server Components 직렬화(`react-server-dom-webpack`) 자체, PPR 의 postponed 상태 형식은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 진입과 헤더 읽기](01_entry/README.md)
- [02 준비](02_prepare/README.md)
- [03 갈림길](03_split/README.md)
