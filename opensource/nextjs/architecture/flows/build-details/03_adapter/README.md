# 03 어댑터에 산출물을 넘긴다

상위: [빌드가 번들러 설정과 배포 산출물을 만들기까지](../README.md)

**두 번들러 모두에서 돈다** — 다만 `config.adapterPath`(또는 환경변수 `NEXT_ADAPTER_PATH`, `server/config-shared.ts` L2157)가 있을 때만이다. `handleBuildComplete` 는 혼자 1766줄(L557-2322)이고, 하는 일은 번역이다. `.next/` 에 흩어진 매니페스트와 파일을 **출력 목록(`outputs`)과 라우팅 표(`routing`)** 로 바꿔 어댑터 모듈의 `onBuildComplete` 에 한 번 넘긴다. [빌드](../../build/README.md) 흐름이 짚은 대로, routes-manifest 의 `prefetchSegmentDataRoutes` 를 읽는 곳은 저장소에서 이 파일 하나다.

## 위치

`packages/next` / `src/build/adapter` / `build-complete.ts` L557-L2322 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/adapter/build-complete.ts#L557-L2322))

## 실제 코드

[빌드 04](../../build/04_generate/README.md)가 routes-manifest 에 실어 둔 세그먼트 rewrite 가 **여기서 라우팅 항목이 된다.**

```ts
// build-complete.ts L2113-L2129
      for (const segmentRoute of route.prefetchSegmentDataRoutes || []) {
        dynamicSegmentRoutes.push({
          source: route.page,
          sourceRegex: segmentRoute.source.replace(
            '^',
            `^${config.basePath && config.basePath !== '/' ? path.posix.join('/', config.basePath || '') : ''}[/]?`
          ),
          destination: path.posix.join(
            '/',
            config.basePath,
            segmentRoute.destination +
              getDestinationQuery(segmentRoute.routeKeys)
          ),
          has: undefined,
          missing: undefined,
        })
      }
```

```text
 ★★ 세그먼트 요청 하나가 **두 규칙**에 걸릴 수 있다

   dynamicSegmentRoutes    위 코드. prefetchSegmentDataRoutes 한 항목 = 규칙 하나
   dynamicRoutes 의 .rsc   L2088-2102 — app 페이지가 하나라도 있으면 동적 라우트마다
                           sourceRegex 끝을 `(?<rscSuffix>\.rsc|\.segments/.+\.segment\.rsc)` 로 바꾼 규칙
 합치는 순서 (L2231-2235)
   combinedDynamicRoutes = [...dynamicDataRoutes, ...dynamicSegmentRoutes, ...dynamicRoutes]
 => 세그먼트 전용 규칙이 **먼저** 온다 ※ (어댑터가 배열 순서대로 맞춘다고 가정하면)

 ★ basePath 가 있으면 source 앞에 붙이고(L2117-2119) destination 에도 붙인다(L2121-2125).
   routeKeys 는 `?값=$키` 꼴 쿼리로 destination 에 달린다 (getDestinationQuery L2047-2052)
 ★ `has` · `missing` 이 **언제나 undefined** 다 — 페이지 규칙(L2109)은 fallback: false 면
   프리뷰 쿠키 조건을 거는데, 세그먼트 규칙은 그러지 않는다
```

## 동작 흐름

```text
 handleBuildComplete({...})   ADBC L557  ← BUILD L4436, output: export 처리 **뒤**, standalone **앞**

 L612   adapterMod = interopDefault(await import(pathToFileURL(require.resolve(adapterPath)).href))
 L616   if (typeof adapterMod.onBuildComplete === 'function') {      ← **없으면 아무것도 안 한다**
 L617     outputs = { pages, pagesApi, appPages, appRoutes, prerenders, staticFiles }  (+ middleware)
 L626     output: 'export' 면
 L628       out 디렉터리를 전부 읽어 **staticFiles 로만** 넣는다  (.html 은 확장자를 뗀 pathname)
 L645     아니면
 L646       .next/static/** → staticFiles  (pathname = /_next/static/...)
 L648         Turbopack && supportsImmutableAssets 면 immutable-static-hashes.json 에서 해시
 L671       getSharedNodeAssets(...)                                      (아래 ★★★)
 L852-862   edge 함수(middleware-manifest 의 middleware · functions) → handleEdgeFunction
 L877       pageKeys (Pages Router)
              _app · _document 는 건너뛴다. edge 함수로 이미 처리한 것도
              staticPages 면 → STATIC_FILE (.html) 만. '/404' 는 PAGES 로도 남긴다 (주석 L944-946)
              아니면 → handleTraceFiles(pageFile, 'pages') 로 assets 를 채워 PAGES / PAGES_API
              getServerSideProps 면 /_next/data/<buildId>/<page>.json 출력을 하나 더
 L1049      node middleware 면 → MIDDLEWARE (handleTraceFiles(..., 'neutral'))
 L1094      appPageKeys (App Router)
              정적 메타데이터 라우트이면서 prerender 된 것은 건너뛴다 (L1101-1120)
              같은 pathname 이 이미 있으면(병렬 라우트) assets 만 **합친다** (L1130-1145)
              APP_PAGE 는 `<path>.rsc` 출력과 짝으로, APP_ROUTE 도 `.rsc` 짝을 만든다
 L1366      prerenderManifest.routes      → PRERENDER (+ 데이터 · 세그먼트 출력)
 L1658      prerenderManifest.dynamicRoutes → PRERENDER (fallback 셸)
 L1998      정적 404 · 500 이 prerender 에 없으면 STATIC_FILE 로 보탠다
 L2041    normalizePathnames — basePath 를 pathname 앞에 붙인다
 L2066    routesManifest.dynamicRoutes → dynamicRoutes · dynamicSegmentRoutes    (위 실제 코드)
 L2148    데이터 라우트 → dynamicDataRoutes
 L2228    try {
 L2265      await adapterMod.onBuildComplete({ routing, outputs, projectDir, repoRoot,
                                               distDir, config, nextVersion, buildId })
 L2317    } catch => Log.error(...) 후 **다시 던진다** — 빌드가 실패한다
```

```text
 ★★ 어댑터 모듈을 **두 번** import 한다 (평가는 ESM 캐시로 프로세스당 한 번, 워커 프로세스는 따로)

   server/config.ts L1721-1747  applyModifyConfig — loadConfig 마다(L1930 · L2169 · L2242)
                                 adapterPath 가 있으면 import 해서 modifyConfig(config, { phase, ... })
                                 주석 L1727-1728 "we always call modify config  and phase can be used to
                                 only modify for specific times"
   ADBC L612-614                 빌드 끝에서 다시 import 해 onBuildComplete
 => 설정을 바꾸는 입구와 산출물을 받는 입구가 **같은 모듈의 두 함수**다 (NextAdapter, ADBC L461-534)
 ★ [01]의 webpack **워커 모드**면 워커가 loadConfig 를 다시 부르므로(WPIMPL L423) 그때도 modifyConfig 가 돈다 ※
   사용자 `webpack` 훅이 있으면 기본은 in-process 라(BUILD L1739-1742) 다시 부르지 않는다
```

```text
 ★★★ webpack 이면 어댑터가 **세 번째 NFT** 를 돌린다 (ADBC L2412-2504)

   // Turbopack traces these itself, they are listed in the nft.json files.
   if (bundler !== Bundler.Turbopack) {
     necessaryNodeDependencies = node-environment · require-hook · node-polyfill-crypto
                                 + defaultOverrides 중 확장자 있는 것 (주석 L2445
                                   "Nothing references these, the require hook resolves them at runtime.")
                                 + cacheHandler · cacheHandlers
     nodeFileTrace(necessaryNodeDependencies, { base: outputFileTracingRoot, ignore, ... })
   }
 => [02]의 두 추적은 페이지·서버 엔트리를 기준으로 하고, 이것은 **함수 하나를 부팅하는 데**
    드는 파일이다. 결과는 sharedNodeAssets 로 모든 Node 출력의 assets 에 합쳐진다 (L701-712)
 ★ 그리고 번들러와 상관없이 `next/setup-node-env.js` 자리에
   build/adapter/setup-node-env.external.ts(12줄)를 넣는다 (L2397-2410)
     주석(그 파일 L1-4) "a minimal import that initializes the node environment ...
       without require `next-server`"
     본문은 edge 가 아니면 node-environment · require-hook · node-polyfill-crypto 를 require 할 뿐이다
```

```text
 ★★★ 해시는 **Turbopack 에서만** 채워진다 — 분기가 세 겹이다

   pushAsset  L2554-2570   `if (bundler === Bundler.Turbopack)` 일 때만 hashFile(salt, path)
   loadNFT    L2572-2598   `.nft.json` 에 fileHashes · entryHash 가 있을 때만 옮긴다
                            — [02]에서 본 대로 webpack 의 `.nft.json` 에는 그 필드가 없다
   immutableHash L648-656  Turbopack && config.supportsImmutableAssets 일 때만
                            — 게다가 server/config.ts L1696-1700 이 webpack·Rspack 이면
                              supportsImmutableAssets 를 **false 로 덮는다**
                              주석 "the server code assumes that all files in `static/chunks`
                              are always immutable without checking the manifest"
 => webpack·Rspack 빌드의 어댑터 출력은 assetsHashes 가 비어 있다
 ★ Turbopack 이어도 **edge 출력은 언제나 `{}`** 다 — L775-776 "Computing assetsHash for edge
   functions isn't implemented for now"
 ★ immutableHash 는 Turbopack 이어도 output 이 'standalone' · 'export' 면 꺼진다 — server/config.ts
   L1702-1710 이 supportsImmutableAssets 를 false 로 (주석 "designed to work with adapters")
    (grep "assetsHashes\[" — 값을 넣는 곳은 L714(entryHash, loadNFT 가 준 것) · L2566(pushAsset) ·
     L2594(loadNFT) 셋이고, 셋 다 위 조건 안이다)
 ★ hashFile(L2600-2619) 은 심볼릭 링크면 대상 경로를, 아니면 내용을 해시한다.
   salt 는 config.outputHashSalt
```

```text
 ★★ edge 함수 처리를 기다리지 않는다 — 그래도 괜찮은 이유가 코드에 있다

   L852  const edgeFunctionHandlers: Promise<any>[] = []
   L856  edgeFunctionHandlers.push(handleEdgeFunction(middleware, true))
   L861  edgeFunctionHandlers.push(handleEdgeFunction(page))
   => 이 배열을 await 하는 곳이 **없다** (grep "edgeFunctionHandlers" — L852 · L856 · L861 셋뿐)
   그런데 handleEdgeFunction(L719-850) 본문에 await 가 **하나도 없다** (awk 로 확인)
   => async 함수라도 첫 await 전까지는 동기로 돈다. 그래서 push 하는 순간 outputs 에 다 들어간다
 ★ 대조 — [04] standalone 의 같은 이름 함수는 await 가 있고, 거기서는 다른 문제가 생긴다
```

```text
 ★★ 하이브리드 앱이면 Pages 라우트에 **가짜 `.rsc`** 를 붙인다 (L869-875 · L911-919 · L933-941)

   app 페이지와 pages 페이지가 **둘 다** 있으면
     await fs.writeFile(.next/server/rsc-fallback.json, '{}')
   Pages 정적 페이지 · gSSP 페이지 · Pages prerender 마다
     { pathname: `${route}.rsc`, filePath: rscFallbackPath }   STATIC_FILE
 => App Router 클라이언트가 Pages 라우트의 RSC 를 달라고 해도 빈 객체 `{}` 가 나간다 ※
    (왜 필요한지 적은 주석은 없다. 클라이언트 라우터 쪽 소비는 확인하지 않았다)
```

```text
 ★ 미들웨어 매처에 **조건 하나를 언제나 덧붙인다** (L804-820 · L1068-1084)

   missing: [ ...item.missing,
     // always skip middleware for on-demand revalidate
     { type: 'header', key: 'x-prerender-revalidate', value: previewModeId } ]
 => on-demand revalidate 요청(프리뷰 ID 를 헤더에 실은 것)은 미들웨어를 건너뛴다.
    edge 미들웨어와 node 미들웨어 두 갈래에 **같은 코드가 두 번** 있다
```

```text
 ★★ routing.rsc 를 **다시 만든다** (L2293-2306)

   rsc: generateRoutesManifest({ appType, pageKeys, config, redirects: [], headers: [],
          onMatchHeaders: [], rewrites, restrictedRedirectPaths: [],
          isAppPPREnabled: config.cacheComponents }).routesManifest.rsc
 => 손에 있는 routesManifest.rsc(L1211-1217 에서 이미 구조 분해해 쓴다)를 두고
    routes-manifest 전체를 새로 만들어 `.rsc` 만 꺼낸다
 ★ BUILD L1676 은 같은 함수에 isAppPPREnabled = checkIsAppPPREnabled(config.experimental.ppr) 를 넘긴다.
   rsc 안에서 그 값을 쓰는 것은 dynamicRSCPrerender(generate-routes-manifest.ts L135) 하나이고
   `isAppPPREnabled && config.cacheComponents === true` 라서, experimental.ppr 이 cacheComponents 일 때만
   true 인 v16.3.6 에서는 두 호출의 결과가 같다 ※ ([빌드] 04 가 확인한 server/config.ts 규칙에 기댄 것이다)

 generateRoutesManifest  build/generate-routes-manifest.ts L53-159 — 두 번들러 공통
   L69   pages + app 키를 sortPages 로 정렬
   L80   동적이면 dynamicRoutes, 예약 페이지가 아니거나 /api 면 staticRoutes
   L97   routesManifest { version: 3, pages404: true, basePath, redirects, headers, rewrites,
                          dynamicRoutes, staticRoutes, dataRoutes: [], rsc, ppr, ... }
   L121  rsc — 헤더 이름 · 접미사(.rsc · .segment.rsc · .segments) · clientParamParsing = cacheComponents
   L143  ppr — isAppPPREnabled 면 { chain: { headers: { next-resume: '1' } } }
   L154  return { routesManifest, dynamicRoutes, sourcePages }
         sourcePages 는 **빈 Map** 으로 나간다 — 채우는 것은 BUILD L3624 (SSG region)
```

## 결과가 쓰이는 곳

```text
 onBuildComplete 의 ctx
   outputs.pages · pagesApi · appPages · appRoutes · middleware
        --> 함수로 배포할 단위. filePath + assets(추적된 파일) + config(maxDuration · preferredRegion)
   outputs.prerenders
        --> ISR 캐시에 미리 넣을 항목. fallback.filePath · initialRevalidate(없으면 1, L1544-1547) ·
            bypassToken(= previewModeId) · groupId(같이 재검증할 묶음)
   outputs.staticFiles
        --> CDN 에 올릴 파일
   routing.beforeMiddleware · beforeFiles · afterFiles · dynamicRoutes · onMatch · fallback
        --> 플랫폼의 라우터. onMatch 첫 항목은 /_next/static 의 해시 파일에
            `public,max-age=31536000,immutable` 을 건다 (L2279-2288)
   routing.shouldNormalizeNextData
        --> 미들웨어가 있고 Pages 출력이 있을 때 true (L2132-2133)

 예외
        --> onBuildComplete 가 던지면 빌드가 실패한다 (L2317-2320)
```

## 다루지 않는 것

`prerenderManifest.dynamicRoutes` 갈래(L1658-1996)의 partial fallback · allowQuery 계산과 `fallbackRootParams` 처리, `getPrerenderClassification`(L397-429)이 routeType · response · compute 를 검사하는 규칙, `handleAppMeta`(L1219-1305)가 세그먼트 출력의 `allowQuery` 를 고르는 조건(`clientParamParsing`), i18n 로케일마다 출력을 복제하는 갈래, 데이터 라우트(L2135-2200)의 정규식 조립, `convertRedirects` · `convertRewrites` · `convertHeaders`(`@vercel/routing-utils`)의 변환, `modifyRouteRegex`, 어댑터 인터페이스 타입(L60-534)의 필드 설명 전부, `output: 'export'` 일 때 out 디렉터리를 채우는 `writeFullyStaticExport`, 그리고 실제 어댑터 구현(이 저장소 밖)은 이 문서의 범위 밖이다.
