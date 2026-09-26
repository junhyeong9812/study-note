# 04 prerender 하고 매니페스트를 쓴다

상위: [`next build` 가 산출물을 만들기까지](../README.md)

`#region SSG`(L2999-4321, 1323줄)는 둘로 나뉜다. 앞의 약 200줄은 [03]의 결과를 **`exportPathMap` 으로 번역해 `exportApp` 에 넘기는 일**이고, 뒤의 약 1100줄은 돌아온 결과로 `prerender-manifest` 와 `routes-manifest` 를 **조립하는 일**이다. 그 사이에서 export 워커가 가짜 요청으로 [App Router]를 불러 [정적 응답]의 `prerenderToStream` 까지 내려가고, 결과 파일을 `.next/server/` 에 직접 쓴다.

만나는 흐름 — [정적 응답](../../prerender-to-stream/README.md)(`prerenderToStream` 까지의 경로) · [트리 조립 04](../../tree-assembly/04_slice/README.md)(세그먼트 Map 이 파일이 되는 자리) · [페이지 아닌 요청 02](../../non-page/02_route-handler/README.md)(`isStaticGenEnabled` 1차 관문) · [동적 판별 04](../../dynamic-rendering/04_verdict/README.md)(`StaticGenBailoutError` 를 받는 쪽) · [`'use cache'` 03](../../use-cache/03_lookup/README.md)(두 단계 export 의 RDC 씨앗).

## 위치

`packages/next` / `src/build` / `index.ts` L2999-L4321 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/index.ts#L2999-L4321))

## 실제 코드

[트리 조립]의 `collectSegmentData` 가 만든 세그먼트 Map 이 **파일이 되는 자리**다.

```ts
// app-page.ts L165-L182
    let segmentPaths
    if (segmentData) {
      // Emit the per-segment prefetch data. We emit them as separate files
      // so that the cache handler has the option to treat each as a
      // separate entry.
      segmentPaths = []
      const segmentsDir = htmlFilepath.replace(
        /\.html$/,
        RSC_SEGMENTS_DIR_SUFFIX
      )

      for (const [segmentPath, buffer] of segmentData) {
        segmentPaths.push(segmentPath)
        const segmentDataFilePath =
          segmentsDir + segmentPath + RSC_SEGMENT_SUFFIX
        fileWriter.append(segmentDataFilePath, buffer)
      }
    }
```

```text
 ★★★ 세그먼트 하나 = 파일 하나

   htmlFilepath      .next/server/app/<경로>.html        (EXWORKER L137 — app 이면 outDir 가 여기로 고정)
   segmentsDir       .next/server/app/<경로>.segments     (RSC_SEGMENTS_DIR_SUFFIX = '.segments')
   파일              <segmentsDir><segmentPath>.segment.rsc  (RSC_SEGMENT_SUFFIX = '.segment.rsc')
                     lib/constants.ts L14-15

 주석 L167-169 - "Emit the per-segment prefetch data. We emit them as separate files
   so that the cache handler has the option to treat each as a separate entry."
 => 세그먼트를 한 파일로 묶지 않는 이유가 **캐시 핸들러**다. 항목 단위로 따로 다룰 수 있게 한다
 => 경로 목록 segmentPaths 는 `.meta` 파일(L226-229)에 실리고, 워커가 돌려주는 메모리의
    `metadata` 에도 실린다(EXAPPPAGE L231-238). routes-manifest 의 `prefetchSegmentDataRoutes` 는
    **후자**로 만든다 (BUILD L3654-3683)
 ★ 쓰기는 append 에서 **곧바로 시작한다** — mkdir → writeFile 약속을 그 자리에서 띄우고
   (lib/multi-file-writer.ts L81-90), `await fileWriter.wait()`(EXWORKER L577)는 **기다리기만** 한다
   (L96-98)
```

## 동작 흐름

```text
 BUILD L3005  !compile 이고 (정적/SSG 페이지가 있거나 · 정적 404/500 · **appDir 가 있으면**)
 L3013    staticGenerationSpan = traceChild('static-generation')
 L3015    detectConflictingPaths(...)
 L3030    sortedStaticPaths = staticPaths 를 경로 이름순 정렬
 L3037    exportConfig = { ...config, exportPathMap: (defaultMap) => {...} }     (아래 ★★★)
 L3180    exportResult = await exportApp(dir, {
            nextConfig: exportConfig, buildExport: true, pages: combinedPages,
            outdir: .next/export, numWorkers, ... }, nextBuildSpan, **staticWorker**)
                                                                          ~~> export/ (아래)
 L3201    결과가 없으면 return
 L3265    prerenderManifest.notFoundRoutes = exportResult.ssgNotFoundPaths
 L3270    **Pages Router 정적 페이지(staticPages)의 서버 번들을 지운다** — fs.unlink(getPagePath(page, distDir))
            /404 만 남긴다. 주석 L3272-3273 "we might need it if we do want to runtime-render the 404"
 L3280    sortedStaticPaths.forEach — app 라우트마다
 L3289      revalidate 가 0 이면(설정 또는 export 결과) isStatic · isSSG 를 **false 로 되돌린다**
              주석 L3294-3295 "if the page was marked as being static, but it contains dynamic data
              (ie, in the case of a static generation bailout), then it should be marked dynamic"
 L3321      bypassFor — ACTION_HEADER('next-action') · multipart/form-data · (PPR 이면) htmlLimitedBots UA
              주석 L3319-3320 "to enable server actions on static routes"
 L3356      fallbackRouteParams 가 있으면 unknown, 없으면 known 으로 나눠 따로 정렬
 L3424      known  → prerenderManifest.routes[pathname] = { initialRevalidateSeconds, srcRoute, dataRoute, ... }
 L3534        revalidate 0 이면 routes 에 안 넣고 ssgPageRoutes 에서 뺀다
 L3571      unknown(+ PPR 아닌 동적 라우트의 기본 경로) → prerenderManifest.dynamicRoutes[pathname]
 L3654        metadata.segmentPaths 가 있으면 routes-manifest 의 prefetchSegmentDataRoutes 를 만든다
 L3828    updatePagesManifestForExportedPage
            주석 L3826-3827 "The export worker writes pages directly to .next/server/pages/,
            so no file moving is needed — only the manifest must be updated."
 L3964    정적 app /_not-found 가 있으면 server/pages/404.html 로 **복사** (L3881-3920)
 L3988    정적 app /_global-error 가 있으면 server/pages/500.html 로 복사 (L3922-3959)
 L4144    pages-manifest.json 을 다시 쓴다
 L4149    routesManifest.dynamicRoutes 를 다시 정렬하고 L4161 routes-manifest.json 을 **두 번째로** 쓴다
 (region 끝)
 L4236    Pages 의 동적 SSG(tbdPrerenderRoutes)를 dynamicRoutes 에 넣는다
 L4295    정적 메타데이터 파일이 dynamicRoutes 에 남았으면 지운다 (주석 L4287-4294 "Defensive sweep")
 L4301    writePrerenderManifest(distDir, prerenderManifest)
 L4302    server/prefetch-hints.json
 L4306    writeClientSsgManifest(...)
```

```text
 ★★★ build 와 export 사이의 규약이 **`exportPathMap`** 이다

   L1358-1364  사용자가 app/ 와 함께 exportPathMap 을 설정하면 => throw
                 "The "exportPathMap" configuration cannot be used with the "app" directory.
                  Please use generateStaticParams() instead."
   L3043       그런데 build 자신은 **exportPathMap 함수를 지어 붙여** exportApp 에 넘긴다
   EXPORT L536-547  exportApp 은 그 함수를 `nextConfig.exportPathMap(defaultPathMap, {...})` 로 부른다

 => 사용자에게 막은 설정 키가 내부에서는 **build → export 의 통로**다
 => app 경로는 `_` 로 시작하는 숨은 필드를 달고 간다 (L3127-3143)
      _ssgPath · _fallbackRouteParams · _isDynamicError · _isAppDir · _isRoutePPREnabled ·
      _allowEmptyStaticShell (= !route.throwOnEmptyStaticShell) · _isFallbackUpgradeable
 ★ L3115-3125 는 "fallbackRootParams 가 있는데 cacheComponents 가 아니면 뺀다" 고 적는다 —
   그런데 이 조합은 v16.3.6 에서 **닿지 않는다.** fallbackRootParams 는 isRoutePPREnabled 일 때만
   생기고(SPAPP L1027-1060), isRoutePPREnabled 는 checkIsRoutePPREnabled(config.experimental.ppr)
   (BUILD L3099)인데 experimental.ppr 은 cacheComponents 일 때만 true 다 (server/config.ts L574-578 ·
   L1603-1606)
   주석 L3111-3112 "we don't support revalidating the shells without the parameters present"
```

```text
 exportApp  EXPORT L1110 → exportAppImpl L192

 L205   nextConfig = options.nextConfig (build 가 넘긴 exportConfig) — 없을 때만 loadConfig
 L239   .next/BUILD_ID 가 없으면 => throw ExportError   (build 는 L2899 에서 먼저 써 둔다)
 L443   output: 'export' 면 routes-manifest.json 을 require 해 가로채기 rewrite 를 찾는다
          ※ BUILD L2875 주석 "We need to write the manifest with rewrites before build" 가
            routes-manifest 를 SSG **전에** 한 번 쓰는 이유 중 하나로 보인다
 L537   run-export-path-map
 L573   allExportPaths — 중복 경로 제거 (L574 seenExportPaths)
 L694   numWorkers = min(options.numWorkers, ceil(경로 수 / 25))
          주석 L685-688 - 최소 25개씩 묶는 것은 "even setups with only a few static pages can
          leverage a shared incremental cache" 를 위해서다 (staticGenerationMinPagesPerWorker)
 L746   cacheComponents 면 두 단계로 나눈다
 L751     _allowEmptyStaticShell 인 경로(fallback 셸) → final 단계, 나머지 → initial 단계
 L762     instant validation 은 **라우트마다 한 번만** 표시한다
 L798   results = exportPagesInBatches(worker, initial)
 L801   final 이 있으면 buildRDCCacheByPage(results, final) 로 **앞 단계의 RDC 를 모아**
 L806     뒤 단계에 넘긴다                                  → [`'use cache'`] 03 의 "읽기 전용 씨앗" ※
 L825   결과를 byPath · byPage · ssgNotFoundPaths 로 모은다
 L1040  실패한 경로가 하나라도 있으면 => throw ExportError("Export encountered errors on N paths")
```

```text
 export 워커  EXWORKER — [03]과 같은 staticWorker 프로세스들이다

 exportPages  L349
 L385   createIncrementalCache(...)   워커마다 하나
 L399   maxConcurrency = staticGenerationMaxConcurrency ?? 8   ← 한 워커 안에서 **8개씩** 동시에
 L425     Promise.race([ exportPage(...), staticPageGenerationTimeout 초 타이머 ])
 L474     TimeoutError 면 maxAttempts = 3
            ★ 주석 L475 은 "we will restart the worker up to 3 times" 라고 적지만 이 루프는
              워커를 건드리지 않고 exportPage 를 **같은 프로세스에서 다시 부른다** (L423-519)
              ※ lib/worker 쪽에 따로 재시작 장치가 있는지는 확인하지 않았다
 L489     마지막 시도도 실패 + prerenderEarlyExit 면  => process.exit(1)
 L531   재시도 기본값 staticGenerationRetryCount ?? 1  (= 한 번만 시도)

 exportPage  L542 → exportPageImpl  L71
 L137   outDir = app 이면 .next/server/app, 아니면 넘겨받은 것(build 이면 .next/server/pages, EXPORT L728-730)
 L171   { req, res } = createRequestResponseMocks({ url: updatedPath })   ← **가짜 요청**
 L238   components = loadComponents({ distDir, page, isAppPath, ... })     ← [02]의 출력
 L248   app 라우트 핸들러면  => exportAppRoute(...)          [페이지 아닌 요청]
 L274   renderOpts.supportsDynamicResponse = false           ← 이것이 isStaticGeneration 을 켠다
 L279   serveStreamingMetadata = true
          주석 L275-278 "we always enable the streaming metadata since if there's any dynamic
          access in metadata we can determine it in the build phase."
 L291   app 페이지면       => exportAppPage(...)
 L327   pages 면          => exportPagesPage(...)
```

```text
 exportAppPage → [정적 응답] 까지

 EXAPPPAGE L78   lazyRenderAppPage(new NodeNextRequest(req), new NodeNextResponse(res), ...)
   server/route-modules/app-page/module.render.ts L7-11
     require('./module.compiled').renderToHTMLOrFlight
   module.compiled.js 는 NODE_ENV · __NEXT_EXPERIMENTAL_REACT · **process.env.TURBOPACK** 로
     미리 번들된 런타임(app-page[-turbo][-experimental].runtime.{dev,prod}.js) 하나를 고른다
     ★ 번들러 선택이 prerender 시점의 런타임 파일까지 따라온다 ※
       (※ 정적 워커 프로세스에 TURBOPACK 환경변수가 전달되는지는 확인하지 않았다)
   app-page/module.ts L9 · L230 이 app-render 의 renderToHTMLOrFlight 를 다시 내보낸다
 APPR L3101  renderToHTMLOrFlight                                     [App Router]
 APPR L2787    if (isStaticGeneration) {
                 주석 "We're either building or revalidating. In either case we need to
                   prerender our page rather than render it."
 APPR L2801      prerenderToStreamWithTracing(...)  =  prerenderToStream L8229    [정적 응답]
               work-store.ts L116-119 — isStaticGeneration = !supportsDynamicResponse && !isDraftMode
                 && !isPossibleServerAction. 위 L274 의 false 가 여기서 true 로 뒤집힌다

 결과가 돌아오면 (EXAPPPAGE)
 L113   cacheControl.revalidate === 0 이면
 L114     _isDynamicError 면  => throw `Page with dynamic = "error" encountered dynamic data method on ${path}.`
 L129     아니면  => return { cacheControl, fetchMetrics }     ← **파일을 하나도 안 쓴다**
 L148   shouldWriteRsc = PPR 이 아니거나 (postponed 없고 fallback param 도 없을 때)
 L158     <경로>.rsc
 L165   <경로>.segments/...                                  (위 실제 코드)
 L194   <경로>.html
 L226   <경로>.meta   { status, headers, postponed, segmentPaths, prefetchHints }
 L239   hasEmptyStaticShell = Boolean(postponed) && html === ''
 L246   renderResumeDataCache 를 문자열로 → [EXPORT L801]의 다음 단계 씨앗
```

```text
 ★★★ 동적으로 판명된 페이지가 끝나는 길이 **둘**이다

 ① DynamicServerError 류 (isDynamicUsageError — export/helpers/is-dynamic-usage-error.ts)
      = isDynamicServerError · isBailoutToCSRError · isNextRouterError · isDynamicPostpone
    EXAPPPAGE L253  catch — isDynamicUsageError 가 아니면 다시 던진다
    L260            BailoutToCSR 는 **조건 없이** 다시 던진다 ("페이지 수준" 은 주석의 말이다)
    L278            나머지 => return { cacheControl: { revalidate: 0 } }
    => 빌드는 계속된다. BUILD L3289-3300 이 그 페이지를 **동적으로 되돌린다**

 ② StaticGenBailoutError  (isDynamicUsageError 에 **없다**)                   [동적 판별] 04
    APPR L9665-9678   prerender 의 catch 가 isStaticGenBailoutError 면 그대로 다시 던진다
    APPR L2826-2829   invalidDynamicUsageError 가 있으면 renderToHTMLOrFlightImpl 도 던진다
    EXAPPPAGE L254    ① 이 아니므로 다시 던진다
    EXWORKER L586     exportPage 의 catch
      L598              isStaticGenBailoutError 면 메시지만 찍는다 (스택은 안 찍는다, 주석 L594-597)
      L607              => return { error: true }
    EXWORKER L461     'error' in result 면 ExportPageError → 재시도 (기본 1회라 곧 포기)
    EXPORT L1040      실패 경로를 모아 => throw ExportError   code = 'NEXT_EXPORT_ERROR' (EXPORT L78-80)
    NBCLI L147        CLI 가 그 코드를 알아보고 `> ${err.message}` 만 찍고 종료한다
    => **빌드가 선다** — 그리고 **기본은 첫 실패에서 즉시** 선다.
       `experimental.prerenderEarlyExit` 의 기본값이 **true** 다 (server/config-shared.ts L2166).
       그래서 워커 안 L489-493 이 `process.exit(1)` 로 끝내고 부모 lib/worker.ts L173-181 이
       그 종료 코드로 프로세스를 끝낸다
       위의 ExportError → NBCLI 길은 **비기본**이다 — `--debug-prerender` 일 때만 prerenderEarlyExit 이
       false 가 되어 모든 경로를 돌린 뒤 한꺼번에 선다 (server/config.ts L2302-2306)
 ★ NBCLI L148 은 'NEXT_STATIC_GEN_BAILOUT' 코드도 알아본다 — 그 오류가 export 워커를 거치지 않고
   CLI 까지 오는 경로는 이 문서에서 확인하지 않았다
```

```text
 exportAppRoute  EXAPPROUTE — 라우트 핸들러의 GET                   [페이지 아닌 요청] 02

 L55    req.url = `http://localhost:3000${req.url}`   ← 절대 URL 로 만든다
 L81    isBuildTimePrerendering: true · L82 supportsDynamicResponse: false
 L106   !isStaticGenEnabled(userland) && !메타데이터 라우트 && cacheComponents !== true
 L115     => return { revalidate: 0 }        **handle 을 부르지도 않는다**
 L118   response = module.handle(request, context)
 L120   status >= 400 이면서 404 가 아니면 => revalidate: 0
 L156   <경로>.body  (응답 본문)
 L160   <경로>.meta  { status, headers }
 L170   catch — isDynamicUsageError 면 revalidate: 0, 아니면 다시 던진다
```

## 결과가 쓰이는 곳

```text
 .next/server/app/<경로>.{html,rsc,meta,body} · <경로>.segments/*.segment.rsc
      --> 런타임의 응답 캐시가 정적 응답으로 읽는다 ※
          세그먼트 파일은 [프리페치]의 세그먼트 요청 응답이다 ([트리 조립] 04 의 '/_tree' · 세그먼트 키)

 prerender-manifest.json
      routes[경로]        initialRevalidateSeconds · initialExpireSeconds · srcRoute · dataRoute ·
                          experimentalBypassFor
      dynamicRoutes[패턴] fallback · fallbackRouteParams · fallbackRootParams · routeRegex
      notFoundRoutes · preview
      --> 런타임 서버와 어댑터(handleBuildComplete, BUILD L4455)

 routes-manifest.json (두 번째 쓰기, L4161)
      dynamicRoutes[].prefetchSegmentDataRoutes
      --> 세그먼트 요청을 파일 경로로 바꾸는 rewrite ※

 pageInfos (initialCacheControl · hasPostponed · hasEmptyStaticShell)
      --> printTreeView (L4505). 빌드 로그의 라우트 표

 ExportError / NEXT_EXPORT_ERROR
      --> CLI (NBCLI L137-155)
```

## 다루지 않는 것

`detectConflictingPaths`, Pages Router 의 `exportPagesPage`(`export/routes/pages.ts`)와 `_pagesFallback` · i18n 갈래(L3050-3073 · L3147-3173 · L4030-4140), `getPprAppPageClassification` · `getStaticAppPageClassification` · `collectMeta` 의 분류 규칙, `buildPrefetchSegmentDataRoute` 가 만드는 정규식, `pageToRoute` 와 `skipInternalRouting`, `fallbackModeToFallbackField`, `buildRDCCacheByPage` · `createRenderResumeDataCache` · `stringifyResumeDataCache` 의 구현, instant validation(`_runInstantValidation`) 의 판정, `createRequestResponseMocks` · `MultiFileWriter` 의 구현, `createIncrementalCache` 와 fetch 캐시, `recordFetchMetrics` · `writeTurborepoAccessTraceResult`, `buildExport: false` 일 때만 도는 exportApp 의 복사 경로(`public/` 복사 L664-678 · prerender 라우트를 outDir 로 옮기는 L897-1037), `writeClientSsgManifest` 와 `writeImagesManifest`, `lazyRenderAppPage` 가 고르는 미리 번들된 런타임의 내용, 그리고 [정적 응답] 안의 세 갈래(cacheComponents · PPR · legacy)는 이 문서의 범위 밖이다.
