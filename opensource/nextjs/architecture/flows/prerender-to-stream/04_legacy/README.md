# 04 평범한 정적 생성

상위: [정적 응답을 미리 만들기](../README.md)

100줄(L9565-9664)이다. **기본 설정(`cacheComponents: false`, `ppr: false`)의 빌드와 ISR 재검증이 타는 길**이다. 앞의 두 갈래가 1139줄인 것과 대비된다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L9565-L9664 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L9565-L9664))

## 실제 코드

이 갈래의 성격을 주석이 한 문장으로 말한다.

```tsx
// app-render.tsx L9576-L9584
      // This is a regular static generation. We don't do dynamic tracking because we rely on
      // the old-school dynamic error handling to bail out of static generation
      const RSCPayload = await workUnitAsyncStorage.run(
        prerenderLegacyStore,
        getRSCPayload,
        tree,
        ctx,
        { is404: res.statusCode === 404 }
      )
```

```text
 "This is a regular static generation. We don't do dynamic tracking because we rely on
  the old-school dynamic error handling to bail out of static generation"

 => **동적 추적을 하지 않는다.**
    `cookies()` 같은 동적 API 를 쓰면 그것이 **예외를 던지고**,
    그 예외를 [05]의 catch 가 받아 **다시 던진다**(L9683).
    정적 생성을 포기할지는 부르는 쪽이 정한다
 => 앞의 두 갈래([02] cacheComponents · [03] PPR)가 쓰는 "추적" 이
    이 예전 방식의 대체물이다. 그래서 그쪽이 그렇게 큰 것이다
```

## 동작 흐름

```text
 APPR L9565-9664

 L9566  prerenderStore = prerenderLegacyStore = {
          type: 'prerender-legacy',
          phase: 'render',
          rootParams, implicitTags,
 L9571     revalidate: INFINITE_CACHE,
 L9572     expire:     INFINITE_CACHE,
 L9573     stale:      INFINITE_CACHE,
          tags: [...implicitTags.tags],
        }
        ★ 세 값이 전부 INFINITE_CACHE 로 시작한다.
          렌더 도중 fetch 나 `revalidate` 설정이 이 값을 **낮춘다**

 --- 첫 번째 렌더: RSC ---
 L9578  RSCPayload = await workUnitAsyncStorage.run(
           prerenderLegacyStore, getRSCPayload, tree, ctx,
           {is404: res.statusCode === 404})
 L9587  reactServerResult = reactServerPrerenderResult =
 L9588    await createReactServerPrerenderResultFromRender(
           workUnitAsyncStorage.run(
             prerenderLegacyStore, renderFlightStream,
             ComponentMod, RSCPayload, clientModules,
             {filterStackFrame, onError: serverComponentsErrorHandler}))
        ★ [동적 응답]과 달리 **await 한다.** 끝까지 기다려 결과를 붙잡는다

 --- 두 번째 렌더: HTML ---
 L9602  {stream: htmlStream} = await workUnitAsyncStorage.run(
           prerenderLegacyStore, renderFizzStream,
 L9607     <App reactServerStream={reactServerResult.asUnclosingStream()}
                reactDebugStream={undefined}
                preinitScripts={preinitScripts}
                ServerInsertedHTMLProvider={...} nonce={nonce}
                images={ctx.renderOpts.images} />,
           {onError: htmlRendererErrorHandler, nonce,
            bootstrapScriptContent, bootstrapScripts: [bootstrapScript]},
 L9621     {waitForAllReady: true})
        ★★ **언제나 true 다.** [동적 응답]은 generateStaticHTML 로 갈렸지만
           여기는 고를 것이 없다 — 저장할 것이므로 끝까지 기다린다

 --- 세그먼트 데이터 ---
 L9624  shouldGenerateStaticFlightData(workStore) 이면
 L9625    flightData = await streamToBuffer(reactServerResult.asStream())
 L9626    metadata.flightData = flightData
 L9627    await collectSegmentData(...)

 L9637  getServerInsertedHTML = makeGetServerInsertedHTML({...})
 L9644  => return {
 L9647       stream: await continueFizzStream(htmlStream, {...}),
             ...
           }
```

```text
 ★★ 스트림을 쓰는 방식이 [동적 응답]과 다르다

 [동적 응답]  reactServerResult.tee()        HTML 렌더용
              reactServerResult.consume()    인라인 데이터용

 여기         reactServerResult.asUnclosingStream()   HTML 렌더용 (L9607)
              reactServerResult.asStream()            세그먼트 데이터용 (L9625)
              reactServerResult.consumeAsStream()     인라인 데이터용 (L9649)

 => `createReactServerPrerenderResultFromRender` 로 **다 받아 둔 뒤**라
    갈라 쓸 필요가 없다. 같은 버퍼를 여러 번 읽는다
 ※ asUnclosingStream 과 asStream 의 차이는 구현을 봐야 안다.
   여기서 확인하지 않았다
```

```text
 ★ 이 갈래에는 `if` 가 하나뿐이고, **그 하나도 언제나 참이다** (L9624)

   shouldGenerateStaticFlightData(L8154-8159)는 workStore.isStaticGeneration 을
   그대로 돌려준다. 그런데 prerenderToStream 은 [App Router] L2787 의
   `if (isStaticGeneration)` 안에서만 불린다
   => 소스도 알고 있다 — L8152-8153 에 "이제 정적 생성만 검사하므로 제거 가능" 이라는 TODO 가 있다
   => 실질 분기가 **0개**다

 [02]가 AbortController 열둘과 단계 컨트롤러로 렌더를 **여러 번** 돌리는 동안,
 여기는 RSC 한 번 · HTML 한 번으로 끝난다
 => 흐름도로 그리면 직선이다. 실패는 전부 [05]의 catch 가 받는다
```

## 결과가 쓰이는 곳

```text
 PrerenderToStreamResult
      --> [App Router]의 L2801 이 받아 L2868 에서 문자열로 만든다

 metadata.flightData
      --> 응답 캐시의 rscData 로 저장된다.
          클라이언트 내비게이션이 이 페이지로 올 때 HTML 대신 이것을 받는다

 prerenderLegacyStore 의 revalidate / expire / stale
      --> INFINITE_CACHE 에서 시작해 렌더 도중 낮아진다.
          최종값이 캐시 수명이 된다

 collectSegmentData 의 산출
      --> 세그먼트 캐시. 부분만 받아 가는 길
```

## 다루지 않는 것

`createReactServerPrerenderResultFromRender` 와 `ReactServerPrerenderResult` 의 `asStream` / `asUnclosingStream` 차이, `collectSegmentData`(`collect-segment-data.tsx` 1528줄)가 RSC 페이로드를 세그먼트로 쪼개는 방식, `shouldGenerateStaticFlightData`(L8154)의 판정, `INFINITE_CACHE` 가 렌더 도중 낮아지는 경로(`patchFetch` 와 `revalidate` 설정), `PrerenderStore` 의 `type: 'prerender-legacy'` 가 다른 종류와 다르게 취급되는 자리, "old-school dynamic error handling" 이 실제로 던지는 예외(`DynamicServerError` 등)의 발생 지점, `streamToBuffer` / `continueFizzStream` 의 구현은 이 문서의 범위 밖이다.
