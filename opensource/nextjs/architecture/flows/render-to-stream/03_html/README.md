# 03 HTML

상위: [동적 응답을 스트림으로 내보내기](../README.md)

두 번째 렌더다. [02]가 만든 Flight 스트림을 입력으로 받아 React 를 **한 번 더** 돌려 HTML 을 만든다. 그리고 그 Flight 스트림을 HTML 안에 심는다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L3805-L4085 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L3805-L4085))

## 실제 코드

평범한 요청이 끝나는 자리다.

```tsx
// app-render.tsx L3935-L3947
        return await continueFizzStream(htmlStream, {
          inlinedDataStream: createNodeInlinedDataStream(
            reactServerResult.consume(),
            nonce,
            formState
          ),
          isStaticGeneration: generateStaticHTML,
          allReady,
          deploymentId: ctx.sharedContext.deploymentId,
          getServerInsertedHTML,
          getServerInsertedMetadata,
          validateRootLayout: !!process.env.__NEXT_DEV_SERVER,
        })
```

```text
 ★★★ 같은 Flight 스트림을 **두 번** 쓴다

 L3893  reactServerStream={reactServerResult.tee()}     -> <App> 이 읽어 HTML 을 만든다
 L3937  createNodeInlinedDataStream(reactServerResult.consume(), ...)
                                                        -> 그 HTML **안에 심는다**

 => 서버가 HTML 을 그리는 데 쓴 것과 똑같은 데이터를
    브라우저가 수화할 때 쓰도록 문서에 붙여 보낸다.
    `tee()` 와 `consume()` 이 그 둘을 가른다
```

## 동작 흐름

```text
 APPR L3805-4085 — 겉껍질은 빌드에서 사라지는 if 다

 L3806  if (process.env.__NEXT_USE_NODE_STREAMS) {        Node 빌드
 L3948  } else {                                          Edge 빌드 — **같은 일이 아니다**
          L4060  renderToWebFizzStream 에는 셋째 인자를 **안 넘긴다**
                 stream-ops.web.ts L265  `_options?: { waitForAllReady?: boolean }`
                 => 언더스코어다. 쓰지 않는다
          L4078  isStaticGeneration 만 쓴다
          ★ node 만 getTracer().trace(AppRenderSpan.renderToNodeFizzStream) 으로 감싼다

 --- Node 쪽 본문 L3807-3947 ---

 L3809  renderOpts.postponed 이 문자열이면            ★ PPR 재개
 L3810    postponedState?.type === DynamicState.DATA 이면
          ★ postponed 가 문자열인데 postponedState 가 null 이면
            두 PPR 갈래를 **모두 빠져나가** 아래의 평범한 동적 렌더로 떨어진다
 L3814      inlinedDataStream = createNodeInlinedDataStream(reactServerResult.tee(), nonce, formState)
 L3821      renderSpan.end()   (비동기 렌더가 없는 길이라 여기서 닫는다)
 L3822      => return chainStreams(inlinedDataStream, createDocumentClosingStream())
              주석 L3811-3813 - 프리렌더에 **완전한 HTML 문서**가 이미 있다.
                다만 새 서버 컴포넌트 렌더는 그 정적 서두에 없었으므로 그것만 이어 붙인다
              ★ HTML 을 아예 안 만든다. 데이터와 닫는 태그만 보낸다

 L3826    아니고 postponedState 가 있으면
 L3828      {postponed, preludeState} = getPostponedFromState(postponedState)
 L3831      resumeAppElement = <App reactServerStream={reactServerResult.tee()} ... />
 L3843      getServerInsertedHTML = makeGetServerInsertedHTML({...})
 L3851      {stream: htmlStream, allReady} = await workUnitAsyncStorage.run(
               requestStore, resumeToFizzStream, resumeAppElement, postponed,
               {onError: htmlRendererErrorHandler, nonce})
 L3861      allReady.finally(() => renderSpan.end())
 L3865      => return await continueDynamicHTMLResumeNode(htmlStream, {
 L3866           delayDataUntilFirstHtmlChunk: preludeState === DynamicHTMLPreludeState.Empty, ...})

 --- 평범한 동적 렌더 L3880-3947 ---
        주석 L3880 - "This is a regular dynamic render"
 L3881  getServerInsertedHTML = makeGetServerInsertedHTML({
           polyfills, renderServerInsertedHTML,
           serverCapturedErrors: allCapturedErrors, basePath, tracingMetadata})
 L3889  generateStaticHTML = supportsDynamicResponse !== true     ★ 아래 별항
 L3891  appElement = <App reactServerStream={reactServerResult.tee()}
                          reactDebugStream={reactDebugStream}
                          preinitScripts={preinitScripts}
                          ServerInsertedHTMLProvider={...} nonce={nonce}
                          images={ctx.renderOpts.images} />
 L3904  fizzOptions = {
           onError: htmlRendererErrorHandler,
           nonce,
 L3907     onHeaders: (headers) => { 전부 appendHeader 로 붙인다 },
           maxHeadersLength: reactMaxHeadersLength,
           bootstrapScriptContent, bootstrapScripts: [bootstrapScript], formState}
 L3918  {stream: htmlStream, allReady} = await getTracer().trace(
           AppRenderSpan.renderToNodeFizzStream, () =>
             workUnitAsyncStorage.run(requestStore, renderToNodeFizzStream,
                                       appElement, fizzOptions,
 L3926                                  {waitForAllReady: generateStaticHTML}))
 L3931  allReady.finally(() => { renderSpan.end() })
          주석 L3930 - React 가 **Suspense 경계 안까지** 다 끝낸 뒤에 닫는다
 L3935  => return await continueFizzStream(htmlStream, {
 L3936       inlinedDataStream: createNodeInlinedDataStream(reactServerResult.consume(), nonce, formState),
 L3941       isStaticGeneration: generateStaticHTML,
             allReady, deploymentId,
             getServerInsertedHTML, getServerInsertedMetadata,
 L3946       validateRootLayout: !!process.env.__NEXT_DEV_SERVER})
```

```text
 ★★★ `supportsDynamicResponse` 가 여기까지 왔다 (L3889)

   const generateStaticHTML = supportsDynamicResponse !== true

 이 값은 세 군데서 좁혀졌다
   [응답 나가기] pipeImpl L1862   supportsDynamicResponse: !this.renderOpts.botType
   [응답 나가기] 01_decide L2422  = !isSSG && !isBotRequest && isSupportedDocument
   [응답 나가기] 01_decide L2428  개발 + app 경로면 다시 true
   (그리고 app-page-runtime.ts L996 의 forceStaticRender 가 마지막에 끈다)

 여기서 그것이 뒤집혀 **`waitForAllReady`** 가 된다 (L3926)
 => 동적 응답을 지원하지 않으면 React 가 **전부 끝날 때까지 기다린다**.
    스트리밍이 아니라 완성된 HTML 을 만든다
 => 봇에게 완성된 문서를 주는 길이 이 한 줄로 이어진다
 ★★ 다만 이것은 **Node 빌드 한정**이다.
   Edge 쪽(L4060)은 그 인자를 넘기지 않고 web 판 시그니처도 `_options` 로 무시한다.
   Edge 에서 generateStaticHTML 이 쓰이는 자리는 isStaticGeneration(L4078) 하나뿐이다
```

```tsx
// app-render.tsx L3904-L3916
        const fizzOptions = {
          onError: htmlRendererErrorHandler,
          nonce,
          onHeaders: (headers: { [header: string]: string }) => {
            for (const key in headers) {
              appendHeader(key, headers[key])
            }
          },
          maxHeadersLength: reactMaxHeadersLength,
          bootstrapScriptContent,
          bootstrapScripts: [bootstrapScript],
          formState,
        }
```

```text
 ★★ 렌더 도중에 응답 헤더가 붙는다 (L3907-3911)

   onHeaders: (headers) => { for (const key in headers) appendHeader(key, headers[key]) }

 => React 가 렌더하면서 preload 힌트 같은 것을 헤더로 알려 준다.
    [01]이 미리 bind 해 둔 appendHeader 가 여기서 쓰인다
 ※ [README]가 인용한 L3800-3802 주석("preload 헤더를 잡으려고 한 틱 쉰다")이
   가리키는 것이 이 통로로 보인다. 소스에 둘을 잇는 근거는 없다 (내 추측이다)
 ★ maxHeadersLength 로 상한이 걸려 있다
```

```text
 ★ 스팬은 스트림이 끝나야 닫힌다 (L3931)

   allReady.finally(() => { if (renderSpan.isRecording()) renderSpan.end() })

 => [01]이 스팬을 손으로 연 이유가 이것이다. 함수는 L3935 에서 반환하지만
    스팬은 React 가 Suspense 안까지 다 끝낸 뒤에 닫힌다
```

```text
 ★ PPR 재개에는 HTML 을 아예 안 만드는 길이 있다 (L3810-3825)

 postponedState.type === DynamicState.DATA 면
 => 정적 서두에 **완전한 HTML 문서**가 이미 있다.
    새로 만든 RSC 데이터와 `</body></html>` 만 이어 붙여 보낸다
 => 이 갈래만 renderSpan 을 동기적으로 닫는다 (L3821).
    비동기 렌더가 없기 때문이다
```

## 결과가 쓰이는 곳

```text
 반환한 스트림
      --> [App Router]의 L3027 이 받아 L3086 에서 RenderResult 로 감싼다

 appendHeader 로 붙인 헤더
      --> 응답 헤더. 라우트 모듈이 sendRenderResult 할 때 이미 붙어 있다

 inlinedDataStream
      --> HTML 문서 안의 self.__next_f 푸시들. 브라우저가 수화할 때 읽는다

 generateStaticHTML
      --> Node 빌드에서는 waitForAllReady(L3926)와 isStaticGeneration(L3941) 두 자리.
          Edge 빌드에서는 isStaticGeneration(L4078) 한 자리뿐이다
```

## 다루지 않는 것

`renderToNodeFizzStream` / `resumeToFizzStream` / `continueFizzStream` / `continueDynamicHTMLResumeNode` / `createNodeInlinedDataStream` / `chainStreams` / `createDocumentClosingStream`(`stream-ops.node.ts` 1104줄)의 구현, `<App>`(L2368) 컴포넌트가 Flight 스트림을 React 엘리먼트로 되살리는 과정, `makeGetServerInsertedHTML` 과 `ServerInsertedHTMLProvider` 의 삽입 지점, `getServerInsertedMetadata` 와 스트리밍 메타데이터, PPR 의 `postponedState` 형식 · `DynamicState` · `DynamicHTMLPreludeState` 열거와 `getPostponedFromState`, React Fizz 의 `onHeaders` 규약과 `reactMaxHeadersLength`, `validateRootLayout` 의 검사 내용, Edge 갈래(L3948-4085)의 web 스트림 판은 이 문서의 범위 밖이다.
