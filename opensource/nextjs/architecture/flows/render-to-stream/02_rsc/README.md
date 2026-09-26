# 02 RSC 페이로드

상위: [동적 응답을 스트림으로 내보내기](../README.md)

첫 번째 렌더다. 서버 컴포넌트 트리를 돌려 **Flight 스트림**을 만든다. HTML 은 아직 없다. 갈래가 셋인데 **평범한 프로덕션 요청이 타는 것은 마지막 하나**다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L3452-L3798 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L3452-L3798))

## 실제 코드

세 갈래의 조건이 이렇다 (조건 줄만 옮겼다 — 몸통은 아래 행 범위).

```text
 L3452        if (
 L3453          process.env.__NEXT_DEV_SERVER &&
 L3454          // Edge routes never prerender so we don't have a Prerender environment for anything in edge runtime
 L3455          process.env.NEXT_RUNTIME !== 'edge' &&
 L3456          // We only have a Prerender environment for projects opted into cacheComponents
 L3457          cacheComponents
 L3458        ) {                                                    … 몸통 L3459-3567
 L3568        } else if (cacheComponents && cachedNavigations) {    … 몸통 L3569-3711
 L3712        } else {                                              … 몸통 L3713-3797
```

```text
 L3452  개발 + Node + cacheComponents            (L3452-3567, 116줄)
 L3568  } else if (cacheComponents && cachedNavigations)   (L3568-3711, 144줄)
 L3712  } else {                                 (L3712-3798, 87줄)  ← **평범한 요청**

 => 앞의 둘은 `cacheComponents` 를 요구한다. 기본값이 꺼져 있다
    (config-shared.ts 의 defaultConfig 기준 — [App Router] 흐름에서 확인했다)
 => 그러므로 기본 설정의 프로덕션 요청은 **셋째 갈래만** 탄다
```

## 동작 흐름

```text
 --- 갈래 1: 개발 + cacheComponents  L3452-3567 ---
 L3453  __NEXT_DEV_SERVER && NEXT_RUNTIME !== 'edge' && cacheComponents
          주석 L3454 - Edge 라우트는 프리렌더를 하지 않아 Prerender 환경이 없다
          주석 L3456 - cacheComponents 를 켠 프로젝트에만 Prerender 환경이 있다
 L3459  debugChannelClientStream (let)
 L3462  getPayload = async (requestStore) => { ... }
 L3490  ★ createRequestStore 가 있으면 (L3493)
 L3506    stagedRenderWithCachesInDev(...)      **다시 시작할 수 있는** 렌더
 L3514    fallbackRouteParams: fallbackParams   ← 시그니처의 fallbackParams 가 쓰이는 유일한 곳
 L3532  없으면
 L3540    stagedRenderWithoutCachesInDevNode(...)
        ★★ 시그니처 파라미터 `createRequestStore` 가 여기서만 쓰인다.
           호출처가 이 값을 **일부러 죽인다**
             [App Router] L3001  undefined  // Prevent restartable-render behavior
             [App Router] L3043  didExecuteServerAction ? undefined : createRequestStore
           => 서버 액션을 실행한 뒤에는 렌더를 다시 시작하지 않는다
 L3559  debugChannelClientStream 과 setReactDebugChannel 이 있으면 연결한다

 --- 갈래 2: cacheComponents && cachedNavigations  L3568-3711 ---
 L3574  selectStaleTime = createSelectStaleTime(experimental)
 L3575  staleTimeIterable = new StaleTimeIterable()
 L3577  stageController = new StagedRenderingController({...})
 L3604  shellByteLengthDeferred = createPromiseWithResolvers<...>()
 L3607  staticStageByteLengthDeferred = ...
 L3610  runtimePrefetchStream (let)
 L3646  RSCPayload = await workUnitAsyncStorage.run(...)
 L3660  flightStream = await runInSequentialTasks(...)
        ★ **단계를 나눠 렌더한다** — 셸 / 정적 / 동적의 바이트 수를 따로 센다

 --- 갈래 3: 그 밖 (평범한 요청)  L3712-3798 ---
 L3714  if (__NEXT_USE_NODE_STREAMS) {              ← 빌드에서 한쪽이 사라진다
          주석 L3715 - "This is a dynamic render. We don't do dynamic tracking
                        because we're not prerendering"
 L3716    RSCPayload = await workUnitAsyncStorage.run(
             requestStore, getRSCPayload, tree, ctx, {is404: res.statusCode === 404})
 L3725    debugChannel = setReactDebugChannel && createNodeDebugChannel()
 L3727    debugChannel 이 있으면
 L3728      [readableSsr, readableBrowser] = teeStream(debugChannel.clientSide.readable)
 L3732      reactDebugStream = readableSsr
 L3734      setReactDebugChannel({readable: readableBrowser}, htmlRequestId, requestId)
 L3741    reactServerResult = new ReactServerResult(
             workUnitAsyncStorage.run(
               requestStore, renderToNodeFlightStream,
               ctx.componentMod, RSCPayload, clientModules,
               {filterStackFrame, onError: serverComponentsErrorHandler,
                debugChannel: debugChannel?.serverSide}))
 L3755  } else {                                     Edge 빌드
 L3756    // MARK: webStreams RSC — 같은 일을 web 스트림으로
```

```text
 ★★★ 셋째 갈래가 이 흐름의 본선이다. 하는 일은 셋뿐이다

 1  getRSCPayload(tree, ctx, {is404})  로 **직렬화할 객체**를 만든다
 2  개발이면 디버그 채널을 tee 로 갈라 하나는 SSR 에, 하나는 브라우저에 준다
 3  renderToNodeFlightStream 으로 그 객체를 **Flight 스트림**으로 만든다

 ★ 1 과 3 은 workUnitAsyncStorage.run(requestStore, ...) 안에서 돈다.
   2(디버그 채널 tee, L3725-3739)는 그 밖이다
   [App Router] 흐름에서 본 workAsyncStorage 와 **다른 저장소**다.
   workAsyncStorage 는 요청 하나, workUnitAsyncStorage 는 렌더 단위를 나른다
```

```tsx
// app-render.tsx L3741-L3754
          reactServerResult = new ReactServerResult(
            workUnitAsyncStorage.run(
              requestStore,
              renderToNodeFlightStream,
              ctx.componentMod,
              RSCPayload,
              clientModules,
              {
                filterStackFrame,
                onError: serverComponentsErrorHandler,
                debugChannel: debugChannel?.serverSide,
              }
            )
          )
```

```text
 ★ ReactServerResult 로 감싸 두는 것이 중요하다

 renderToNodeFlightStream 은 **스트림을 동기로 돌려준다** (Promise 가 아니다).
   stream-ops.node.ts L542  export function renderToNodeFlightStream(...): AnyStream
   ReactServerResult 의 생성자도 `constructor(stream: AnyStream)` 이다
 => 그러므로 여기서 기다릴 것 자체가 없다. 스트림 손잡이만 받아 둔다.
    내용이 채워지는 것은 그 뒤다
 => [03]이 `reactServerResult.tee()` 로 필요할 때 갈라 쓴다
 ★ [README]가 말한 L3803 의 "한 틱 쉬기" 는 이것과 별개다 —
   주석 L3800 이 말하듯 **React 가 렌더를 동기로 시작하지 않아서**다
```

```text
 ★★ 디버그 채널은 개발 전용이고 **스트림을 둘로 가른다** (L3727-3739)

   [readableSsr, readableBrowser] = teeStream(debugChannel.clientSide.readable)
   reactDebugStream = readableSsr                     → [03]의 App 에 넘어간다
   setReactDebugChannel({readable: readableBrowser}, htmlRequestId, requestId)
                                                      → 브라우저 쪽으로

 => [01]에서 본 htmlRequestId / requestId 짝이 여기서 쓰인다.
    개발 서버가 **어느 클라이언트에** 디버그 정보를 보낼지 가리는 열쇠다
```

## 결과가 쓰이는 곳

```text
 reactServerResult  (L3444 에 선언, 여기서 대입)
      --> [03]이 reactServerResult.tee() 로 갈라
          하나는 <App> 의 reactServerStream 으로, 하나는 인라인 데이터 스트림으로 쓴다
      --> 같은 Flight 스트림이 **HTML 안에 심기고** 동시에 SSR 의 입력이 된다

 reactDebugStream  (L3445 에 선언)
      --> [03]의 <App> 에 넘어간다. 개발에서만 값이 있다

 serverComponentsErrorHandler 가 잡은 에러
      --> workStore.reactServerErrorsByDigest 에 쌓인다.
          [03]의 HTML 핸들러가 digest 로 알아보고 중복 보고를 피한다
```

## 다루지 않는 것

`getRSCPayload`(L2047)가 로더 트리를 RSC 페이로드로 바꾸는 과정과 `create-component-tree.tsx`(1307줄), `renderToNodeFlightStream` / `renderToWebFlightStream`(`stream-ops.node.ts` · `stream-ops.web.ts`)의 구현, `ReactServerResult` 와 `tee()` 의 동작, 갈래 1 의 `getPayload` 와 개발 프리렌더 환경, 갈래 2 의 `StagedRenderingController` · `StaleTimeIterable` · `runInSequentialTasks` 와 단계별 바이트 계수, `createNodeDebugChannel` / `createWebDebugChannel` 과 `setReactDebugChannel` 의 전달 경로, `clientModules`(클라이언트 참조 매니페스트)의 형식, `filterStackFrame` 의 규칙, `workUnitAsyncStorage` 가 나르는 저장소의 종류는 이 문서의 범위 밖이다.
