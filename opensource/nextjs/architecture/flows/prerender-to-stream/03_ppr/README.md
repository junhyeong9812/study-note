# 03 PPR

상위: [정적 응답을 미리 만들기](../README.md)

245줄이다. `else if` 이므로 **`!cacheComponents && isRoutePPREnabled`** 일 때 돈다. 렌더를 끝까지 하지 않고 **동적 경계에서 멈춰** 정적 셸과 "나중에 이어 붙일 자리"를 함께 만든다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L9320-L9564 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L9320-L9564))

```text
 ★★ 이 갈래에 닿는 조건이 얽혀 있다

 `experimental.ppr` 을 직접 설정하면 **에러가 난다**
   config.ts L574-578  HardDeprecatedConfigError
     "`experimental.ppr` has been merged into `cacheComponents`."
 `cacheComponents: true` 가 그것을 대신 켠다
   config.ts L1603-1605  result.experimental.ppr = true

 그런데 이 갈래는 `else if` 라 cacheComponents 가 **꺼져** 있어야 온다.
 => 설정만 보면 모순이다. 그래도 죽은 코드가 아니다 —
    app-page-runtime.ts L457-462 가 길을 하나 더 연다
      isRoutePPREnabled = (couldSupportPPR || **isInstantNavigationTest**) && ...
    주석 L458-461 - "When the instant navigation testing API is active, enable the
      PPR prerender path even without Cache Components. In dev mode without CC,
      static pages need this path to produce buffered segment data
      (the legacy prerender path hangs in dev mode)."
 => 즉 이 갈래는 **테스트 API 가 켜진 개발 모드**의 길이다
```

## 실제 코드

이 갈래가 낼 수 있는 결과를 소스가 주석으로 정의해 놓았다.

```tsx
// app-render.tsx L9427-L9441
      /**
       * When prerendering there are three outcomes to consider
       *
       *   Dynamic HTML:      The prerender has dynamic holes (caused by using Next.js Dynamic Rendering APIs)
       *                      We will need to resume this result when requests are handled and we don't include
       *                      any server inserted HTML or inlined flight data in the static HTML
       *
       *   Dynamic Data:      The prerender has no dynamic holes but dynamic APIs were used. We will not
       *                      resume this render when requests are handled but we will generate new inlined
       *                      flight data since it is dynamic and differences may end up reconciling on the client
       *
       *   Static:            The prerender has no dynamic holes and no dynamic APIs were used. We statically encode
       *                      all server inserted HTML and flight data
       */
      // First we check if we have any dynamic holes in our HTML prerender
```

```text
 ★★★ 결과가 셋이다. 이름과 뜻이 소스에 있다

 Dynamic HTML   프리렌더에 **동적 구멍**이 있다 (동적 렌더링 API 를 써서).
                요청이 올 때 이 결과를 **재개해야** 한다.
                그래서 정적 HTML 에는 서버 삽입 HTML 도 인라인 flight 데이터도 안 넣는다

 Dynamic Data   구멍은 없는데 동적 API 는 썼다.
                재개하지는 않는다. 다만 데이터가 동적이라
                **새 인라인 flight 데이터를 만든다**.
                차이는 클라이언트에서 맞춰질 수 있다

 Static         구멍도 없고 동적 API 도 안 썼다.
                서버 삽입 HTML 과 flight 데이터를 **전부 정적으로 박는다**

 => [App Router] 흐름에서 본 postponedState 의 DynamicState.DATA 가
    여기 "Dynamic Data" 다. 그 값을 만드는 곳은 **둘**이다 — L9456 과 L9484
```

## 동작 흐름

```text
 APPR L9320-9564

 L9322  dynamicTracking = createDynamicTrackingState(isDebugDynamicAccesses)
        ★ [04]와 갈리는 지점이다. 여기는 **추적한다**
 L9324  resumeDataCache = createPrerenderResumeDataCache()
 L9325  prerenderStore = pprReactServerPrerenderStore = {...}

 --- RSC ---
 L9338  RSCPayload = await workUnitAsyncStorage.run(...)
 L9345  reactServerResult: ReactServerPrerenderResult

 --- HTML (여기서 멈춘다) ---
 L9361  ssrPrerenderStore: PrerenderStore = {...}
 L9374  pprOnHeaders = createOnHeadersCallback(appendHeader)
 L9375  {prelude: unprocessedPrelude, postponed} = await ...
        ★★ 반환이 **둘**이다 — 여기까지 그린 것(prelude)과
           멈춘 자리(postponed)
 L9398  metadata.hasPendingUi = ...
        ★ 세 갈래가 다 쓴다 ([02] L9196 · [03] L9398 · [05] L9971).
          build/index.ts L438-450 이 이 값으로 프리렌더 매니페스트의
          response 를 'initial' / 'complete' 로 가른다.
          그 분류가 renderingMode === 'PARTIALLY_STATIC' 이 되어
          base-server L2334-2339 의 isRoutePPREnabled 로 **돌아온다**
 L9399  getServerInsertedHTML = makeGetServerInsertedHTML({...})
 L9410  flightData = await streamToBuffer(reactServerResult.asStream())
 L9412  shouldGenerateStaticFlightData(workStore) 이면 ... (L9412-9422)
 L9424  {prelude, preludeIsEmpty} = await processPreludeOp(unprocessedPrelude)

 --- 갈래 넷으로 가른다 (L9442-9564) ---
 L9442  accessedDynamicData(dynamicTracking.dynamicAccesses) 이면
 L9443    postponed != null 이면              ★ **Dynamic HTML**
 L9444      // Dynamic HTML case.
 L9445      metadata.postponed = await getDynamicHTMLPostponedState(
              postponed,
              preludeIsEmpty ? DynamicHTMLPreludeState.Empty : DynamicHTMLPreludeState.Full,
              fallbackRouteParams, resumeDataCache, cacheComponents)
 L9454    아니면                              ★ **Dynamic Data**
 L9455      // Dynamic Data case.
 L9456      metadata.postponed = await getDynamicDataPostponedState(
              resumeDataCache, cacheComponents)
 L9461    주석 - 둘 중 어느 경우든 서버 삽입 HTML 은 정적 응답에 넣어야 한다.
            프리렌더의 HTML 이 그것에 기댈 수 있기 때문이다
 L9482  아니고 fallbackRouteParams 가 비어 있지 않으면
 L9483    // Rendering the fallback case.     ★ **폴백 렌더** (위 셋과 별개다)
 L9484    metadata.postponed = await getDynamicDataPostponedState(...)
 L9508  아니면                                ★ **Static**
 L9509    // Static case
 L9511    workStore.forceDynamic 이면 ...
```

```text
 ★★ 주석이 정의한 결과는 셋인데 **코드의 갈래는 넷**이다

 1  accessedDynamicData 인가?
      예 + postponed 있음   -> Dynamic HTML   (L9443)
      예 + postponed 없음   -> Dynamic Data   (L9454)   ← 안쪽 else 다
 2  아니고 fallbackRouteParams.size > 0 인가?
      예                    -> 폴백 렌더      (L9482)   ← 주석이 따로 이름 붙였다
 3  둘 다 아니면            -> Static         (L9508)

 ★ 넷째(폴백)는 L9427-9441 의 세 결과 정의에 **없는 이름**이다.
   다만 getDynamicDataPostponedState 를 쓰는 것은 Dynamic Data 와 같다 (L9456 · L9484)
 => `fallbackRouteParams` 는 이 함수의 인자다. 아직 값이 정해지지 않은
    동적 세그먼트가 있다는 뜻이고, 그때는 구멍이 없어도 **재개 상태를 남긴다**
```

```text
 ★ 헤더를 모으는 방식이 다르다 (L9374)

   const pprOnHeaders = createOnHeadersCallback(appendHeader)

 [동적 응답]은 fizzOptions 안에 인라인으로 onHeaders 를 적었다 (L3907).
 여기는 [01]이 만든 appendHeader 를 감싼 콜백을 따로 만든다
 => 그 appendHeader 가 res 와 metadata.headers 둘 다에 쓰므로,
    렌더 도중 붙은 헤더가 캐시에 남는다
```

## 결과가 쓰이는 곳

```text
 metadata.postponed
      --> 캐시에 저장된다. 나중에 요청이 오면 [응답 나가기]의 x-matched-path 블록이
          본문에서 읽어 요청 메타에 심고, [App Router]가 파싱해
          [동적 응답]의 재개 갈래로 보낸다
      => 이 값이 세 흐름을 건너 돌아온다

 prelude
      --> 정적 셸. 캐시에 저장되어 먼저 브라우저로 나간다

 dynamicTracking.dynamicAccesses
      --> 어떤 동적 API 를 어디서 썼는지. 판정과 개발 진단에 쓰인다

 resumeDataCache
      --> 재개할 때 다시 계산하지 않아도 되는 것들
```

## 다루지 않는 것

`createDynamicTrackingState` / `accessedDynamicData` 와 `dynamic-rendering.ts`(1592줄)의 추적 구현, React 의 `prerender` API 가 `prelude` 와 `postponed` 를 나눠 주는 방식, `getDynamicHTMLPostponedState` / `getDynamicDataPostponedState` 와 `postponed-state.ts`(327줄)의 직렬화·크기 제한, `processPreludeOp` 와 `preludeIsEmpty` 의 쓰임, `createPrerenderResumeDataCache` 와 `ResumeDataCache` 의 형식, `createOnHeadersCallback` 의 구현, L9442-9564 각 갈래 본문의 세부와 `workStore.forceDynamic` 처리, 폴백 렌더(`pprFallbackDynamicOpts`)의 동작은 이 문서의 범위 밖이다.
