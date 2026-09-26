# 03 갈림길

상위: [App Router 가 페이지를 만드는 길](../README.md)

`renderToHTMLOrFlightImpl` 의 뒤 302줄(L2787-3088)이다. **`isStaticGeneration` 한 값이 파일을 반으로 가른다.** 그리고 요청 쪽은 다시 네 갈래로 갈린다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L2787-L3088 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L2787-L3088))

## 실제 코드

RSC 갈래는 소스가 스스로 이름을 붙여 놓았다.

```tsx
// app-render.tsx L2933-L2969
    // MARK: RSC request
    if (isRSCRequest) {
      if (isRuntimePrefetchRequest) {
        // MARK: RSC runtimePrefetch
        return generateRuntimePrefetchResult(
          req,
          ctx,
          requestStore,
          isAppShellPrefetchRequest
        )
      } else {
        if (
          process.env.__NEXT_DEV_SERVER &&
          process.env.NEXT_RUNTIME !== 'edge' &&
          cacheComponents
        ) {
          // MARK: RSC devCacheComponents
          return generateDynamicFlightRenderResultWithStagesInDev(
            req,
            ctx,
            requestStore,
            createRequestStore,
            fallbackParams
          )
        } else if (cacheComponents && cachedNavigations) {
          // MARK: RSC cacheComponents
          return generateStagedDynamicFlightRenderResultNode(
            req,
            ctx,
            requestStore
          )
        } else {
          // MARK: RSC dynamic
          return generateDynamicFlightRenderResult(req, ctx, requestStore)
        }
      }
    }
```

```text
 // MARK: RSC request
 // MARK: RSC runtimePrefetch
 // MARK: RSC devCacheComponents
 // MARK: RSC cacheComponents
 // MARK: RSC dynamic

 => 주석이 각 갈래의 이름이다. 네 갈래가 **서로 다른 함수**로 간다
```

## 동작 흐름

```text
 APPR L2787-3088

 L2787  if (isStaticGeneration) {                --- 정적 응답을 만드는 갈래 ---
          주석 L2788-2789 - "We're either building or revalidating. In either
            case we need to prerender our page rather than render it."
          ★ **빌드 또는 재검증**이다. 빌드 전용이 아니다
 L2790    prerenderToStreamWithTracing = getTracer().wrap(...)
 L2801    response = await prerenderToStreamWithTracing(...)      -> L8229-10224 (1996줄)
 L2813    response.dynamicAccess 이고 동적 데이터에 닿았고 isDebugDynamicAccesses 면
 L2818      warn('The following dynamic usage was detected:')  — 진단 출력
 L2826    workStore.invalidDynamicUsageError 이면 ...
 L2830    response.digestErrorsMap.size 이면 ...
 L2835    response.ssrErrors.length 이면 ...
 L2842    options: RenderResultOptions = {...}
 L2848    maybeRevalidatesPromise = executeRevalidates(workStore)
 L2849    false 가 아니면 ... (L2849-2860)
 L2862    applyMetadataFromPrerenderResult(response, metadata, workStore)
          ★ metadata 를 채우는 자리는 여기다
 L2864    response.renderResumeDataCache 이면 ...
 L2868    streamString = await streamToString(response.stream)
          ★★ **스트림을 문자열로 다 받는다.** 빌드는 결과를 저장해야 한다
 L2869    result = new RenderResult(streamString, options)
 L2873    cacheComponentsEnabled && isBuildTimePrerendering && runInstantValidation
          && await anySegmentNeedsInstantValidationInBuild(loaderTree) 이면
 L2880      await validateInstantConfigsInBuild(ctx, response.renderResumeDataCache ?? null)
            ★★ 주석 L2879 - "Throws StaticGenBailoutError if validation failed."
               **결과를 다 만든 뒤에도 던져서 죽을 수 있다**
            주석 L2872 - "TODO(instant-validation-build): This is not a great
                          place to wire this in."
 L2886    => return result

 L2887  } else {                                 --- 동적 응답을 흘리는 갈래 ---
 L2889    renderResumeDataCache = ...
 L2894    rootParams = getRootParams(loaderTree, ctx.getDynamicParamFromSegment)
 L2895    fallbackParams = getRequestMeta(req, 'fallbackParams') || null
 L2896    hmrRefreshHash = getRequestMeta(req, 'hmrRefreshHash')
 L2898    createRequestStore = createRequestStoreForRender.bind(...)
 L2913    requestStore = createRequestStore()

 L2915    개발 + setIsrStatus + !cacheComponents + Node + 노드 요청이면
 L2926      req.originalRequest.on('end', () => {
 L2928        isStatic = !requestStore.usedDynamic && !workStore.forceDynamic
 L2929        setIsrStatus(pathname, isStatic)
            })
            ★ **렌더가 끝난 뒤에야** 정적인지 알 수 있다.
              동적 API 를 실제로 썼는지를 requestStore 가 기록해 둔다

 --- ★ RSC 요청이면 네 갈래 ---
 L2934    if (isRSCRequest) {
 L2935      isRuntimePrefetchRequest 이면
 L2937        => return generateRuntimePrefetchResult(req, ctx, requestStore,
                                                      isAppShellPrefetchRequest)
 L2943      아니면
 L2944        개발 + Node + cacheComponents 이면
 L2950          => return generateDynamicFlightRenderResultWithStagesInDev(...)
 L2957        아니고 cacheComponents && cachedNavigations 이면
 L2959          => return generateStagedDynamicFlightRenderResultNode(req, ctx, requestStore)
 L2964        아니면
 L2966          => return generateDynamicFlightRenderResult(req, ctx, requestStore)
            }
            ★★ 넷 다 여기서 **끝난다.** 아래 renderToStream 에 닿지 않는다

 --- ★ 서버 액션이면 ---
 L2971    didExecuteServerAction = false
 L2972    formState = null
 L2973    if (isPossibleActionRequest) {
 L2975      actionRequestResult = await handleAction({req, res, ComponentMod,
                                                      generateFlight: generateDynamicFlightRenderResult,
                                                      workStore, requestStore, serverActions, ctx, metadata})
 L2987      결과가 있으면
 L2988        type === 'not-found' 이면
 L2989          notFoundLoaderTree = createNotFoundLoaderTree(loaderTree)
 L2990          res.statusCode = 404 / metadata.statusCode = 404
 L2992          stream = await renderToStream(..., notFoundLoaderTree, ...)
 L3005          => return new RenderResult(stream, {metadata, contentType: HTML})
 L3009        type === 'done' 이면
 L3010          result 가 있으면
 L3011            result.assignMetadata(metadata)
 L3012            => return actionRequestResult.result
 L3013          아니고 formState 가 있으면 formState = 그것    (계속 내려간다)
 L3019      didExecuteServerAction = true
          }
          ★ 이 값의 용처는 L3043 이다
              didExecuteServerAction ? undefined : createRequestStore
            주석 L3038-3042 - 액션을 실행한 뒤에는 **다시 시작하는 렌더를 막는다**.
              requestStore 가 draftMode 같은 것으로 이미 변형됐을 수 있기 때문이다
          ★ not-found 렌더(L2992)의 아홉째 인자도 같은 뜻으로 undefined 다
            주석 L3001 - "Prevent restartable-render behavior in dev + Cache Components mode"

 --- 그 밖 전부: HTML 렌더 ---
 L3022    options = {metadata, contentType: HTML_CONTENT_TYPE_HEADER}
 L3027    stream = await renderToStream(...)                      -> L3258-4369 (1112줄)
 L3058    개발이고 !cacheComponents 이고 workStore.invalidDynamicUsageError 에
          digest 가 없으면 그 오류를 **브라우저 오버레이로 보낸다** (L3058-3068)
 L3071    maybeRevalidatesPromise = executeRevalidates(workStore)
 L3086    => return new RenderResult(stream, options)
        }
```

```text
 ★★★ 2분기의 뜻 — 스트림을 받는 방식이 다르다

 정적 갈래  L2868  streamString = await streamToString(response.stream)
                   => 끝까지 기다려 **문자열**로 만든다.
                      캐시에 넣거나 디스크에 써야 하기 때문이다

 동적 갈래  L3086  return new RenderResult(stream, options)
                   => 스트림을 **그대로** 넘긴다. 브라우저로 흘려보낸다

 => 같은 컴포넌트 트리를 같은 React 로 렌더하는데
    결과를 붙잡느냐 흘리느냐가 갈린다
 ★ 이름을 "빌드 / 요청" 으로 붙이면 틀린다 — 프로덕션 ISR 의 재검증은
   **요청 시각에 위쪽 갈래**를 탄다 ([README] 참고)
```

```text
 ★★ 동적 갈래의 출구는 일곱이다

   L2937  generateRuntimePrefetchResult                  RSC · 런타임 프리페치
   L2950  generateDynamicFlightRenderResultWithStagesInDev  RSC · 개발 + 캐시 컴포넌트
   L2959  generateStagedDynamicFlightRenderResultNode    RSC · 캐시 컴포넌트
   L2966  generateDynamicFlightRenderResult              RSC · 그 밖
   L3005  renderToStream(notFoundLoaderTree)             액션이 not-found 를 냈다
   L3012  actionRequestResult.result                     액션이 결과를 만들었다
   L3086  renderToStream(loaderTree)                     보통의 HTML

 => RSC 요청은 HTML 을 만들지 않는다. 넷 다 Flight 페이로드로 끝난다
```

```text
 ★ 서버 액션이 결과를 내지 않을 수도 있다 (L3013)

   } else if (actionRequestResult.formState) {
     formState = actionRequestResult.formState
   }

 => 이 경우 return 하지 않고 **아래로 계속 내려가** HTML 을 렌더한다.
    폼 액션 뒤에 같은 페이지를 다시 그려 주는 길이다.
    그때 formState 가 렌더에 실린다 (L3027 의 인자)
```

```tsx
// app-render.tsx L2926-L2930
      req.originalRequest.on('end', () => {
        const { pathname } = new URL(req.url || '/', 'http://n')
        const isStatic = !requestStore.usedDynamic && !workStore.forceDynamic
        setIsrStatus(pathname, isStatic)
      })
```

```text
 ★ 개발 ISR 표시는 **렌더가 끝난 뒤에** 정해진다

 L2928  isStatic = !requestStore.usedDynamic && !workStore.forceDynamic

 => "동적 API 를 실제로 썼는가" 는 렌더를 해 봐야 안다.
    그래서 요청이 끝나는 이벤트('end')에 붙여 놓았다
 => [02]가 요청 들머리에서 setIsrStatus(pathname, undefined) 로 초기화한 것과 짝이다
```

## 결과가 쓰이는 곳

```text
 RenderResult
      --> 라우트 모듈이 받아 res 에 직접 쓴다.
          [응답 흐름]의 base-server 는 null 만 돌려받는다

 executeRevalidates(workStore)  L2848 / L3071  — 이 파일의 호출은 이 둘뿐이다
      ★★ "두 갈래 모두 마지막에" 가 **아니다**
        위쪽 갈래  L2848 은 마지막이 아니다. 뒤에 streamToString(L2868)과
                   validateInstantConfigsInBuild(L2880)가 더 있다
        아래쪽 갈래 출구 일곱 중 **L3086 하나만** L3071 을 지난다.
                   RSC 네 갈래(L2937·2950·2959·2966)와 액션 둘(L3005·3012)은 건너뛴다
      ※ 액션 경로는 action-handler.ts L1246 · L1433 이 스스로 부른다

 metadata
      --> statusCode · fetchMetrics · hasPendingUi.
          서버 액션이 결과를 냈을 때는 L3011 이 그쪽에 옮겨 붙인다

 requestStore.usedDynamic
      --> 개발 ISR 표시(L2928). 동적 API 사용 여부의 기록이다
```

## 다루지 않는 것

`prerenderToStream`(L8229-10224, 1996줄)과 `renderToStream`(L3258-4369, 1112줄)의 본문, `generateRuntimePrefetchResult`(L1495) · `generateDynamicFlightRenderResultWithStagesInDev`(L1294) · `generateStagedDynamicFlightRenderResultNode`(L979) · `generateDynamicFlightRenderResult`(L849) 각각의 구현, `handleAction`(`action-handler.ts` 1580줄)의 서버 액션 검증·실행·재검증, `createRequestStoreForRender` 와 `RequestStore` 의 필드, `executeRevalidates` 의 실행 순서와 실패 처리, `createNotFoundLoaderTree`(L566)가 트리를 바꾸는 방식, `getRootParams` · `streamToString` · `RenderResult` 의 구현, `digestErrorsMap` / `ssrErrors` / `invalidDynamicUsageError` 가 채워지는 자리는 이 문서의 범위 밖이다.
