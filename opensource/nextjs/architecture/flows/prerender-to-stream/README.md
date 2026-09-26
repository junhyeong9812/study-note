# 정적 응답을 미리 만들기

상위: [Next.js 아키텍처 지도](../../README.md)

[App Router 가 페이지를 만드는 길](../app-render/README.md)의 갈림길에서 **위쪽(정적) 갈래**가 부르는 것이 `prerenderToStream` 이다. [동적 응답](../render-to-stream/README.md)과 짝이지만 1996줄로 두 배 가깝다. **응답이 살아 있지 않고 저장될 것**이라는 차이가 구조를 바꾼다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `APPR` = `server/app-render/app-render.tsx`(10598줄).

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L8229-L10224 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L8229-L10224))

## 실제 코드

시그니처에 없는 것이 말해 준다.

```tsx
// app-render.tsx L8229-L8236
async function prerenderToStream(
  req: BaseNextRequest,
  res: BaseNextResponse,
  ctx: AppRenderContext,
  metadata: AppPageRenderResultMetadata,
  tree: LoaderTree,
  fallbackRouteParams: OpaqueFallbackRouteParams | null
): Promise<PrerenderToStreamResult> {
```

```text
 ★★ postponedState 가 **없다**

 [동적 응답]의 renderToStream 은 그것을 받는다 (L3265).
 여기는 안 받는다
 => PPR **재개**는 이 함수가 하는 일이 아니다.
    이쪽은 재개할 대상(정적 셸)을 **만드는** 쪽이다
 ★ 대신 fallbackRouteParams 를 받는다 — 아직 값이 정해지지 않은 동적 세그먼트다
```

## 동작 흐름

```text
 prerenderToStream  APPR L8229-10224 (1996줄)

 L8237-8424  준비 (188줄)                                     [01]
 L8425       try {
 L8426-9319    ★ if (cacheComponents)                894줄    [02]
 L9320-9564    ★ else if (isRoutePPREnabled)         245줄    [03]
 L9565-9664    ★ else  — 평범한 정적 생성             100줄    [04]
              (앞 둘은 닫는 중괄호를 `} else if` · `} else` 줄과 나눠 쓴다)
 L9665-10223 } catch (err) {  (559줄)                          [05]
```

```text
 ★★★ 세 갈래의 크기가 894 / 245 / 100 이다

 기본 설정(cacheComponents: false, ppr: false)이 타는 것은 **마지막 100줄**이다.
 나머지 1139줄은 실험 기능을 켰을 때만 돈다

 주석 L9576-9577 이 그 100줄의 성격을 말한다
   "This is a regular static generation. We don't do dynamic tracking because we rely on
    the old-school dynamic error handling to bail out of static generation"
 => 동적 추적을 하지 않는다. 동적 API 를 쓰면 **예외가 나서** 정적 생성을 포기하는
    예전 방식에 기댄다. 위의 두 갈래가 하는 "추적" 이 그 대체물이다
```

1. [준비](01_setup/README.md) — 헤더를 두 곳에 쓰는 이유.
2. [cacheComponents](02_cache-components/README.md) — 894줄. 가장 큰 갈래.
3. [PPR](03_ppr/README.md) — 245줄. 정적 셸을 만든다.
4. [평범한 정적 생성](04_legacy/README.md) — 100줄. 기본 설정이 타는 길.
5. [실패 처리](05_error/README.md) — catch 559줄.

```text
 ★★★ [동적 응답]과 나란히 놓으면 구조 차이가 보인다

                      renderToStream        prerenderToStream
 전체                  1112줄                1996줄
 준비                  180줄                 188줄
 try                   636줄                 1240줄
 catch                 280줄                 559줄
 node/web 스위치       if/else **셋**        **변수 셋으로 올린다** (L8269-8277)
 헤더                  res.setHeader.bind    **직접 만든 함수 셋** (L8400-8418)
 postponedState        받는다                 안 받는다
 formState             인자로 받는다          **언제나 null** (L8240)
```

```tsx
// app-render.tsx L8269-L8277
  const renderFlightStream = process.env.__NEXT_USE_NODE_STREAMS
    ? renderToNodeFlightStream
    : renderToWebFlightStream
  const renderFizzStream = process.env.__NEXT_USE_NODE_STREAMS
    ? renderToNodeFizzStream
    : renderToWebFizzStream
  const createInlinedDataStream = process.env.__NEXT_USE_NODE_STREAMS
    ? createNodeInlinedDataStream
    : createWebInlinedDataStream
```

```text
 => [동적 응답]은 같은 갈림을 `if/else` 로 세 번 쓴다.
    여기서는 **함수를 변수에 담아** 한 번만 고른다
 => 빌드타임 상수라 결과는 같지만, 본문이 두 벌로 늘어나지 않는다
 ※ 어느 쪽이 먼저 쓰인 방식인지는 확인하지 않았다
```

```text
 ★★ 에러를 보고하지 않는 갈래가 있다 (L8356)

   const reportErrors = !experimental.isRoutePPREnabled

 => PPR 이 켜져 있으면 onInstrumentationRequestError 를 **부르지 않는다**
    (L8358 의 가드)
 ※ PPR 은 정적 셸을 만들다 동적 경계에서 일부러 중단하므로
   그때 나는 에러를 사고로 보고하면 안 되기 때문으로 보인다 (내 해석이다)
```

## 결과가 쓰이는 곳

```text
 PrerenderToStreamResult
      --> [App Router]의 L2801 이 받는다. 그리고 L2868 이
          streamToString 으로 **문자열로 만들어** 캐시에 넣는다

 metadata.headers
      --> [01]의 setHeader 가 res 와 여기에 **둘 다** 쓴다.
          응답이 나중에 재생되어야 하므로 헤더도 저장해야 한다

 collectSegmentData 의 산출
      --> 세그먼트 캐시. 클라이언트가 부분만 받아 갈 수 있게 쪼갠 것이다

 renderResumeDataCache
      --> PPR 재개 때 [동적 응답]으로 넘어간다
```

## 다루지 않는 것

`cacheComponents` 갈래(L8426-9319, 894줄)의 세부와 `'use cache'` 의 캐시 채우기, PPR 갈래(L9320-9564)의 postpone 수집과 `postponed-state.ts`(327줄)의 직렬화, `collect-segment-data.tsx`(1528줄)가 RSC 페이로드를 세그먼트로 쪼개는 방식, `dynamic-rendering.ts`(1592줄)의 동적 접근 추적과 `abortOnSynchronousPlatformIOAccess` 류, `createReactServerPrerenderResultFromRender` / `ReactServerPrerenderResult` 의 구현, `PrerenderStore` 의 종류와 필드, `isPageAllowedToBlock` / `allowEmptyStaticShell` 의 판정, `stream-ops.node.ts` / `.web.ts` 의 스트림 함수들, React 의 `prerender` API 자체는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 준비](01_setup/README.md)
- [02 cacheComponents](02_cache-components/README.md)
- [03 PPR](03_ppr/README.md)
- [04 평범한 정적 생성](04_legacy/README.md)
- [05 실패 처리](05_error/README.md)
