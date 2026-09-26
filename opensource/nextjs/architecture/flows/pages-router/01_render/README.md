# 01 서버에서 HTML 을 만든다

상위: [Pages Router 가 페이지를 그리기까지](../README.md)

[README]의 `doRender` 가 부르는 `renderToHTMLImpl` 이 혼자 **1154줄**(L459-1612)이다. 데이터 함수를 부르고, 페이지를 그리고, `_document` 를 그린다. 순서는 이렇다 — `_app` 의 `getInitialProps` → `getStaticProps` 또는 `getServerSideProps` → 페이지 → 문서. 끝은 **스트림이 아니라 문자열**이다.

## 위치

`packages/next` / `src/server` / `render.tsx` L459-L1612 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/render.tsx#L459-L1612))

## 실제 코드

끝의 return 문(L1593-1611)이 이 함수의 모양을 말한다. 페이지와 문서를 **따로 문자열로 만든 뒤 이어 붙인다.**

```tsx
// render.tsx L1593-L1611
  const [renderTargetPrefix, renderTargetSuffix] = documentHTML.split(
    '<next-js-internal-body-render-target></next-js-internal-body-render-target>',
    2
  )

  let prefix = ''
  if (!documentHTML.startsWith(DOCTYPE)) {
    prefix += DOCTYPE
  }
  prefix += renderTargetPrefix

  const content = prefix + documentResult.contentHTML + renderTargetSuffix

  const optimizedHtml = await postProcessHTML(content, renderOpts)

  return new RenderResult(optimizedHtml, {
    metadata,
    contentType: HTML_CONTENT_TYPE_HEADER,
  })
```

```text
 ★★★ 문서 안에 **자리표시 태그**가 있고, 그 자리를 문자열로 잘라 끼운다

 pages/_document.tsx L996-1001
   export function Main() {
     const { docComponentsRendered } = useHtmlContext()
     docComponentsRendered.Main = true
     // @ts-ignore
     return <next-js-internal-body-render-target />
   }

 => `<Main />` 은 페이지를 그리지 않는다. 빈 태그 하나만 남긴다
 => documentHTML 을 그 태그로 **최대 두 조각**으로 자르고(L1593-1596)
    그 사이에 이미 만든 contentHTML 을 넣는다(L1604)
 ★ packages · crates 전체 grep 에서 이 태그 이름은 두 파일뿐이다 — 만드는 _document.tsx L1000,
   자르는 render.tsx L1594
 ★ DOCTYPE 이 없으면 앞에 붙인다(L1599-1601). 사용자 Document 가 안 써도 된다
 ★ postProcessHTML(L1606)은 Edge 에서는 `async (html) => html` 이다 (L127-130)
```

## 동작 흐름

```text
 renderToHTMLImpl(req, res, pathname, query, renderOpts, extra, sharedContext, renderContext)

 L470  req.cookies 를 **게으른 속성**으로 단다 (setLazyProp)
 L532  isSSG = !!getStaticProps
 L534  defaultAppGetInitialProps = App.getInitialProps === App.origGetInitialProps
        ★ 기본 _app 인지를 **함수 동일성**으로 가린다. 기본 App 은 같은 함수를
          두 이름에 달아 둔다 (pages/_app.tsx L38-39)
 L560  isAutoExport = 페이지 gIP 없음 && 기본 _app && !isSSG && !getServerSideProps
 L578-614  충돌 검사 일곱 개 (아래 ★)
 L680  await Loadable.preloadAll()          next/dynamic 을 전부 미리 싣는다
 L685  SSG · SSR 이고 fallback 이 아니면 previewData 를 읽는다
 L710  router = new ServerRouter(...)        push · replace 등은 전부 noRouter() 로 던진다 (L189-209)
 L750  AppContainer — 감싸는 층 아홉 겹 (L751-786, Provider 일곱 + PathnameContextProviderAdapter + StyleRegistry)
 L814  ctx = { req, res, pathname, query, asPath, AppTree, ... }
         isAutoExport 면 req · res 를 **undefined** 로 준다 (L816-817)
 L860  props = await loadGetInitialProps(App, {AppTree, Component, router, ctx})   ← **먼저**
 L871  isSSG 면 props.__N_SSG = true
 L875  isSSG && !isFallback 이면  getStaticProps(...)            L888
 L1064 getServerSideProps 면 props.__N_SSP = true
 L1068 getServerSideProps && !isFallback 이면  getServerSideProps(...)   L1108
 L1226 (data 요청 && !isSSG) 이거나 redirect 면
 L1227   => return new RenderResult(JSON.stringify(props), ...)   ← HTML 을 안 만든다
 L1235 isFallback 이면 props.pageProps = {}
 L1240 getInitialProps 가 이미 응답을 보냈고 SSG 가 아니면  => return RenderResult.EMPTY
 L1450 documentResult = renderDocument()     L1273-1447
 L1491 htmlProps.__NEXT_DATA__ = { props, page, query, buildId, gsp, gssp, gip, ... }
 L1565 documentHTML = renderToString(<HtmlContext.Provider>{Document}</...>)
 L1593 자르고 이어 붙인다 (위 실제 코드)
 L1608 => return new RenderResult(optimizedHtml, {metadata, contentType: HTML})
```

```text
 ★★★ 스트림 렌더러를 쓰고도 **스트리밍하지 않는다**

 L138-142  async function renderToString(element) {
             const renderStream = await ReactDOMServerPages.renderToReadableStream(element)
             await renderStream.allReady
             return streamToString(renderStream)
           }
 L1329-1331  (renderPage 안)  stream = await renderShell(...); await stream.allReady; streamToString
 L1405-1407  (Document.getInitialProps 가 없을 때)  같은 세 줄

 => 페이지도 문서도 `allReady` 까지 기다린 뒤 **문자열**이 된다
 => 반환 RenderResult 의 몸통은 문자열 optimizedHtml 이다 (L1608)
 ★ 주석 L1373 - "Always using react concurrent rendering mode with required react version 18.x"
   — 동시성 모드이지 스트리밍이 아니다
 ※ Suspense 경계가 나눠 보내지지 않는다는 결론은 위 세 자리를 읽고 내가 붙인 것이다
```

```text
 ★★★ `_app` 의 getInitialProps 가 **데이터 함수보다 먼저** 돈다 (L860 < L875 < L1068)

 그리고 결과는 **덮어쓰며 합쳐진다**
```

```tsx
// render.tsx L1045-L1053
    props.pageProps = Object.assign(
      {},
      props.pageProps,
      'props' in data ? data.props : undefined
    )

    // pass up cache control and props for export
    metadata.cacheControl = { revalidate, expire: undefined }
    metadata.pageData = props
```

```text
 L1208 (getServerSideProps 쪽)  props.pageProps = Object.assign({}, props.pageProps, data.props)

 => `_app` 이 pageProps 에 넣은 키와 getStaticProps 의 props 가 겹치면 **데이터 함수 쪽이 이긴다**
 => 그리고 `_app` 의 getInitialProps 는 SSG 페이지에서도 불린다 (조건 없이 L860)

 ★★ 기본 _app 은 결국 **페이지의** getInitialProps 를 부른다
   pages/_app.tsx L26-32  appGetInitialProps → loadGetInitialProps(Component, ctx)
   shared/lib/utils.ts L390-397  App 에 getInitialProps 가 없어도
     ctx.ctx && ctx.Component 이면 **페이지의 것을 대신 부른다**
 => 사용자 _app 에 getInitialProps 가 없어도 페이지 gIP 는 돈다
```

```text
 ★★ 충돌 검사가 **세 곳**에 있다 (규칙: 컴파일·빌드가 먼저 막는가)

 런타임  PRENDER L578-588   gIP+SSG / gIP+SSR / SSR+SSG  => throw
 빌드    build/utils.ts L934-944   isPageStatic 안의 같은 세 검사, 같은 상수
 컴파일  번들러마다 다르다
         Turbopack(v16 의 **기본** — lib/bundler.ts L99-102)
           crates/next-custom-transforms/src/transforms/strip_page_exports.rs L178-205 가 같은 문구를 낸다
         webpack + SWC
           next_ssg.rs L63-85 — 단 **클라이언트 컴파일에서만** 돈다.
           서버 컴파일은 `disableNextSsg: true` (build/swc/options.ts L528)
         webpack + Babel
           build/babel/plugins/next-ssg-transform.ts L83 · L88 — 같은 상수로 던진다
           "You can not use getStaticProps or getStaticPaths with getServerSideProps..."

 => SSR+SSG 는 **컴파일에서 먼저** 걸린다. 런타임 L586 에 닿는 일은 드물다
 ※ 어느 설정에서 빌드 검사를 거치지 않고 런타임까지 오는지는 확인하지 않았다

 나머지 넷은 런타임에 있다 (L590-614) — 그중 셋은 **다른 곳에도** 있다
   빌드 build/utils.ts L948-953   동적 경로가 아닌데 getStaticPaths
   빌드 build/utils.ts L955-959   동적 SSG 인데 getStaticPaths 없음
   내보내기 export/routes/pages.ts L48-50   getServerSideProps + output: export
   런타임에만 있는 것은 "getStaticPaths 만 있고 getStaticProps 가 없음" 하나다
   getServerSideProps + output: 'export'       => throw
   getStaticPaths 인데 동적 경로가 아님         => throw
   getStaticPaths 만 있고 getStaticProps 없음   => throw
   동적 SSG 인데 getStaticPaths 없음            => throw
```

```text
 ★★ revalidate 를 정규화한다 (L990-1043)

   정수가 아닌 수        => throw  ("Try changing the value to 'Math.ceil(...)'")
   0 이하                => throw  ("revalidate 0 은 매 요청 재검증이라 stale 을 못 참는다는 뜻")
   31536000(1년) 초과    => console.warn 만
   true                  => 1       주석 L1023-1025 "optimal for the most up-to-date page
                                     possible, but without a 1-to-1 request-refresh ratio"
   false · undefined     => false   주석 L1031 "By default, we never revalidate."
   'revalidate' 키 없음   => false
   그 밖(문자열 등)       => throw
 L1052  metadata.cacheControl = { revalidate, expire: undefined }
 L1128  getServerSideProps 는 언제나 { revalidate: 0, expire: undefined }

 => expire 는 여기서 비워 두고 [README]의 PHAND L387-394 가 nextConfig.expireTime 으로 채운다
```

```text
 ★★ getServerSideProps 의 `res` 는 개발에서만 **감시 프록시**다 (L1071-1096)

 L1074  if (process.env.NODE_ENV !== 'production') { resOrProxy = new Proxy(res, { get ... }) }
 L1127  getServerSideProps 가 끝나면 canAccessRes = false
        그 뒤 res 를 만지면  deferredContent 면 throw, 아니면 warn
 L1145  data.props 가 Promise 면 deferredContent = true
 L1195    그리고 여기서 await 한다

 => props 를 Promise 로 돌려줄 수 있다. 그 경우 res 를 늦게 만지면 개발에서 **던진다**
 ★ 프로덕션에서는 프록시가 없다 — 감시도 없다
```

```text
 ★ 오류 문구가 복사돼 있다 (L1168-1173)

   getServerSideProps 갈래인데
     "The /404 page can not return notFound in \"getStaticProps\", please remove it to continue!"
 => getStaticProps 갈래 L946-949 와 **같은 문장**이다. SSR 갈래에서도 "getStaticProps" 라고 말한다
```

```text
 ★★ redirect 는 **props 로 변장**한다 (L969-976 · L1184-1191)

   data.props = { __N_REDIRECT: destination, __N_REDIRECT_STATUS: status }
   basePath 가 있으면 __N_REDIRECT_BASE_PATH 도
   metadata.isRedirect = true

 => [README]의 PHAND L649-679 가 HTML 요청이면 이 값으로 Location 헤더를 세우고,
    data 요청이면 JSON 그대로 보낸다 → [03] 의 클라이언트가 pageProps.__N_REDIRECT 를 본다
 ★ 빌드 시점의 getStaticProps 는 redirect 를 돌려주면 던진다 (L962-967)
```

```text
 ★★ 문서 렌더가 **두 갈래**다 (L1385-1408)

 hasDocumentGetInitialProps = NEXT_RUNTIME !== 'edge' && !!Document.getInitialProps
   참   => loadDocumentInitialProps(renderShell)
           Document.getInitialProps 가 ctx.renderPage() 를 부를 때 **비로소** 페이지를 그린다
           주석 L1388-1389 - "If it has getInitialProps, we will render the shell in
             `renderPage`. Otherwise we do it right now."
   거짓 => 바로 renderShell(App, Component)

 ★★ 기본 Document 에도 getInitialProps 가 **있다** (pages/_document.tsx L1014-1016)
     static getInitialProps(ctx) { return ctx.defaultGetInitialProps(ctx) }
   그 defaultGetInitialProps 가 PRENDER L831-845 이고, 안에서 docCtx.renderPage({enhanceApp}) 를 부른다
 => Node 에서 기본 Document(또는 그것을 상속한 클래스)면 **언제나 첫 갈래**다.
    둘째 갈래는 Edge 이거나, getInitialProps 가 없는 함수형 Document 일 때다
 ★ Edge 에서의 Document 처리 (L1282-1292) — 판별 키 NEXT_BUILTIN_DOCUMENT 는 **정적 속성**이다
   (constants.ts L124, _document.tsx L1045). 그래서 `next/document` 의 Document 를 **상속한**
   사용자 클래스도 그 속성을 물려받아, 던지지 않고 내장 함수형 Document 로 **조용히 바뀐다**
   (사용자의 render 도 버려진다). 던지는 것은 상속하지 않았으면서 getInitialProps 가 있을 때뿐이다
```

```text
 ★★ 서버와 클라이언트의 파이버 모양을 **빈 컴포넌트로** 맞춘다 (L789-812)

   <>
     <Noop />                 {/* <Head/> */}
     <AppContainer>
       <> {children} <Noop /> </>   {/* <RouteAnnouncer/> */}
     </AppContainer>
   </>

 주석 L789-791 - "The `useId` API uses the path indexes to generate an ID for each node.
   To guarantee the match of hydration, we need to ensure that the structure
   of wrapper nodes is isomorphic in server and client."
 => 클라이언트([02])에만 있는 `<Head>` 와 `<RouteAnnouncer>` 자리를 서버는 Noop 으로 채운다
 ★ 주석 L792-793 이 스스로 한계를 적는다 - "With `enhanceApp` and `enhanceComponents`
   options, this approach may not be useful."
```

## 결과가 쓰이는 곳

```text
 RenderResult (문자열 HTML)
      --> [README]의 PHAND L372 가 ResponseCacheEntry{kind: PAGES, html} 로 감싼다

 metadata.pageData (= props 전체)
      --> 같은 캐시 항목의 pageData. `/_next/data/...json` 응답의 몸통이 된다

 metadata.cacheControl
      --> PHAND L375-394 가 expire 를 채우고, L572-614 가 cacheControl 을 고른 뒤
          L612-613 이 Cache-Control 헤더로 쓴다

 metadata.isNotFound / isRedirect
      --> PHAND L396-412 가 캐시 항목의 value 를 null / REDIRECT 로 바꾼다

 __NEXT_DATA__ (htmlProps 에 실린 것)
      --> _document.tsx 의 NextScript 가 `<script id="__NEXT_DATA__" type="application/json">` 로 싣는다
          (L944-954, 직렬화는 getInlineScriptSource L858-902)
      --> [02]의 initialize 가 JSON.parse 로 되읽는다
      ★ largePageDataBytes 를 넘으면 **경고만** 한다. 자르지 않는다 (L875-891)
```

## 다루지 않는 것

`pages/_document.tsx`(1045줄)의 `Head` · `NextScript` 가 스크립트·스타일 태그를 고르는 방식(`getScripts` · `getPolyfillScripts` · `getDynamicChunks`)과 `server/render.tsx` 쪽의 `docComponentsRendered` 경고(L1570-1591), `postProcessHTML`(`server/post-process.ts`)과 `optimizeCss`, styled-jsx 레지스트리와 `Loadable`(next/dynamic), `tryGetPreviewData` 의 쿠키 해석과 draft mode, `isSerializableProps` 의 검사 규칙, `ErrorDebug` 개발 오버레이 갈래(L1303-1315 · L1357-1360), `isExperimentalCompile` 갈래(L566-576), 개발 서버에서만 하는 검사(L618-666)와 `setIsrStatus`, `STATIC_STATUS_PAGES` 제약, `filteredBuildManifest` 의 `_buildManifest` 선적재(L1244-1267), `renderToHTML`(L1624) 을 부르는 빌드 시점 prerender 는 이 문서의 범위 밖이다.
