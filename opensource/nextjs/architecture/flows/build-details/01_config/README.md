# 01 webpack 설정을 조립한다

상위: [빌드가 번들러 설정과 배포 산출물을 만들기까지](../README.md)

**webpack·Rspack 전용이다. 기본 번들러(Turbopack)에서는 이 함수가 한 번도 불리지 않는다.** `getBaseWebpackConfig` 는 혼자 2577줄(L327-2903)이고, 컴파일러 하나(client · server · edge-server)의 `webpack.Configuration` 을 돌려준다. [빌드 02](../../build/02_compile/README.md)가 적은 대로 워커마다 이것을 **세 번** 부르고 그중 하나만 돌린다. 이 문서는 그 2577줄이 무엇을 어떤 순서로 쌓는지, 그중 **레이어별 로더 체인**을 따라간다.

## 위치

`packages/next` / `src/build` / `webpack-config.ts` L327-L2903 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/webpack-config.ts#L327-L2903))

호출처는 둘뿐이다 — 빌드 `WPIMPL` L171 · L180 · L189 와 개발 서버 `server/dev/hot-reloader-webpack.ts` L771 · L777 · L783 · L802 (`grep -rn "getBaseWebpackConfig("`).

## 실제 코드

SWC 로더 네 벌이 **`bundleLayer`** 로 갈린다(기본 로더 하나만 `esm: false` 도 다르다).

```ts
// webpack-config.ts L596-L620
  // RSC loaders, prefer ESM, set `esm` to true
  const swcServerLayerLoader = getSwcLoader({
    serverComponents: true,
    bundleLayer: WEBPACK_LAYERS.reactServerComponents,
    esm: true,
  })
  const swcSSRLayerLoader = getSwcLoader({
    serverComponents: true,
    bundleLayer: WEBPACK_LAYERS.serverSideRendering,
    esm: true,
  })
  const swcBrowserLayerLoader = getSwcLoader({
    serverComponents: true,
    bundleLayer: WEBPACK_LAYERS.appPagesBrowser,
    esm: true,
  })
  // Default swc loaders for pages doesn't prefer ESM.
  const swcDefaultLoader = getSwcLoader({
    serverComponents: true,
    esm: false,
  })

  const defaultLoaders = {
    babel: useSWCLoader ? swcDefaultLoader : babelLoader!,
  }
```

```text
 ★★★ 같은 next-swc-loader 인데 레이어가 옵션으로 들어간다
   rsc · ssr · app-pages-browser 는 esm: true, Pages 쪽 기본은 esm: false (주석 L612)
   이 bundleLayer 가 SWC 옵션을 가른다 — build/swc/options.ts
     L105  isReactServerLayer   = shouldUseReactServerCondition(bundleLayer)
     L106  isAppRouterPagesLayer = isWebpackAppPagesLayer(bundleLayer)
     L223  serverComponents: { isReactServerLayer, cacheComponentsEnabled, useCacheEnabled, ... }
     L233  serverActions: isAppRouterPagesLayer && !jest ? { ..., cacheKinds } : undefined

 => [`'use cache'`]를 cache() 호출로 바꾸는 serverActions 변환은
    **appPages 레이어 묶음**(rsc · ssr · app-pages-browser · action-browser, lib/constants.ts L206-212)
    에서만 켜진다. Pages 기본 로더(bundleLayer 없음)와 middleware 로더(L650-653)에는 없다
 ★ 그리고 instrumentation 레이어는 **자기 bundleLayer 가 없다** —
   instrumentLayerLoaders(L634-642)가 swcServerLayerLoader(bundleLayer: rsc)를 그대로 쓴다
 ★★ `defaultLoaders.babel` 은 이름과 달리 **SWC 로더일 수 있다** (L619)
   babel 설정 파일이 없거나 forceSwcTransforms 면 swcDefaultLoader 다 (L427).
   이 객체가 사용자 `config.webpack(config, { defaultLoaders, ... })` 에 그대로 넘어간다 (L2597)
   ※ 이름을 안 바꾼 것은 사용자 설정 호환 때문으로 보인다
```

## 동작 흐름

```text
 getBaseWebpackConfig(dir, {...})   WPCFG L327  (시그니처 L327-387)

 L388   bundler = getWebpackBundler()      NEXT_RSPACK 이면 Rspack 코어, 아니면 webpack
 L389   isClient · isEdgeServer · isNodeServer = compilerType 비교
 L393   isRspack = Boolean(process.env.NEXT_RSPACK)
 L422   !dev && output: 'export' 이면 config.distDir = '.next'   ← BUILD L1165 와 **같은 일을 또 한다**
          ※ 워커 모드면 워커가 config 를 다시 읽기 때문이다 (WPIMPL L423 loadConfig). 부모에서 고친 값이 안 넘어온다
            사용자 `webpack` 훅이 있으면 기본이 in-process(BUILD L1739-1742)라 이 줄은 no-op 이다.
            조건도 정확히는 `hasCustomExportOutput(config)` 다
 L427   useSWCLoader = !babelConfigFile || experimental.forceSwcTransforms
 L486   codeCondition — .tsx|ts|js|cjs|mjs|jsx 와 __barrel_optimize__, node_modules 는 exclude()
 L520   getSwcLoader(extra)  Rspack + BUILTIN_SWC_LOADER 면 'builtin:next-swc-loader'(L540)
 L597   SWC 로더 네 벌  (위 실제 코드)
 L622   레이어별 로더 배열 — app 서버 · instrument · middleware · client(ssr/browser) · api
 L699     API 라우트만 serverComponents: false   주석 L696-698 "shouldn't have RSC transpiler enabled"
 L731   clientEntries — client 컴파일러만. main · main-app · (dev) react-refresh
 L784   resolveConfig — alias = createWebpackAliases(...)  L793
          ★ [`'use cache'`]의 private-next-rsc-cache-wrapper alias 가 여기서 들어간다
            (create-compiler-aliases.ts L217-218, createWebpackAliases L40-229 안)
 L836   framework 청크 후보 경로를 package.json 의존성을 따라 모은다
 L892   serverExternalPackages ∩ transpilePackages 가 있으면 => throw
 L906   optOutBundlingPackages = EXTERNAL_PACKAGES(79개) + serverExternalPackages − transpile
 L922   handleExternals = makeExternalHandler(...)                       (아래 ★★★)

 L994   let webpackConfig = {                   ← **객체 리터럴 하나가 L994-2258**
 L998     externals        client/edge = ['next', ...], node server = builtin + bun + handleExternals
                           Rspack 이면 false (`!isRspack &&`, L999)
 L1074    optimization     splitChunks · runtimeChunk · minimize · minimizer
 L1327    output           server 는 path = .next/server/chunks, filename = '../[name].js'
 L1378    resolveLoader    Next 로더 28개를 이름으로 alias (L1381-1408)
 L1424    module.rules     (아래 ★★★)
 L2009    plugins          [...].filter(Boolean)  — 조건부 플러그인 목록
 L2258  }

 L2262  tsconfig baseUrl · JsConfigPathsPlugin
 L2277  edge-server 면 wasm · asset 규칙을 **맨 앞에** unshift
 L2296  experiments = { layers: true, cacheUnaffected: true, buildHttp }
 L2380  configVars = JSON.stringify({...})  → 캐시 version 에 들어간다
 L2415  cache = { type: 'filesystem', version, cacheDirectory: .next/cache/webpack }
 L2461  Rspack 이면 cache 를 persistent 로 **통째로 갈아 끼운다**
 L2547  webpackConfig = await buildConfiguration(...)     CSS·이미지 블록
 L2588  config.webpack 이 함수면  **사용자 훅**                       (아래 ★★)
 L2666  사용자가 svg 규칙을 넣었으면 레이어별 React alias 를 덧붙이고 next-image-loader 에서 svg 를 뺀다
 L2717  experimental.craCompat 이면 규칙을 top/inner 로 재배열
 L2807  사용자 규칙이 CSS 를 잡을 수 있으면 **내장 CSS 를 걷어낸다**
 L2859  entry 를 함수로 감싸 finalizeEntrypoint 를 적용
 L2897  !dev 면 그 함수를 바로 await 해 객체로 만든다
 L2902  return webpackConfig
```

```text
 ★★★ 규칙이 파일이 아니라 **import 한 쪽의 레이어(issuerLayer)** 로 고른다

 레이어는 lib/constants.ts WEBPACK_LAYERS_NAMES(L116-170)에 13개다
   shared · rsc · ssr · action-browser · api-node · api-edge · middleware · instrument ·
   edge-asset · app-pages-browser · pages-dir-browser · pages-dir-edge · pages-dir-node
 레이어를 **처음 정하는 것은 엔트리**다
   getAppEntry        build/entries.ts L291-294   next-app-loader, layer: rsc
   middleware         build/entries.ts L209-213  next-middleware-loader, layer: middleware
   finalizeEntrypoint build/entries.ts L671       server 컴파일러면 api-node · instrument · rsc · pages-dir-node
                                                  (`...entry` 가 뒤에 와서 엔트리가 정한 layer 가 이긴다)
 그다음부터는 import 를 따라 issuerLayer 로 전파된다

 코드 파일을 고르는 oneOf (L1707-1801) — 위에서부터 첫 번째만 맞는다
   issuerLayer api-node               → apiRoutesLayerLoaders   (parser.url: true)
   issuerLayer api-edge               → apiRoutesLayerLoaders
   issuerLayer middleware             → middlewareLayerLoaders  (next-flight-loader + SWC(middleware))
   issuerLayer instrument             → instrumentLayerLoaders  (next-flight-loader + SWC(rsc))
   (app 디렉터리가 있을 때만 넷)
   issuerLayer ∈ serverOnly 묶음       → appServerLayerLoaders   (asyncStorages 제외)
   resourceQuery __next_edge_ssr_entry__ → appServerLayerLoaders
   issuerLayer app-pages-browser      → appBrowserLayerLoaders
   issuerLayer ssr                    → appSSRLayerLoaders
   그 밖                               → defaultLoaders.babel (+ react-refresh · react compiler)
 => app 디렉터리가 있으면 9갈래, 없으면 5갈래다

 oneOf 밖에서 레이어를 **바꾸는** 규칙 (L1515-1535)
   app-render 의 async storage 넷      → layer: shared
     주석 L1518-1519 "Make sure that AsyncLocalStorage module instance is shared between
     server and client layers."
   resourceQuery __next_metadata_route__ → layer: rsc                  [메타데이터]
     ★ 주석 L1523 은 "Convert metadata routes to **separate** layer" 인데
       코드가 넣는 레이어는 따로 만든 것이 아니라 **rsc** 다
   route-modules/app-page/module       → layer: ssr
     주석 L1531-1532 "Ensure that the app page module is in the client layers"

 ★ 레이어에 따라 `import 'react'` 가 **다른 파일**로 간다 —
   createVendoredReactAliases(bundledReactChannel, { layer, ... }) 를 레이어마다 따로 건다
   (L1587 · L1652 · L1664 · L1678 · L1733 · L1748, 그리고 사용자 svg 보정 L2692). rsc 쪽은 conditionNames 에 'react-server' 를 앞세운다 (L717-721)
 ★ cacheComponents 면 middleware · instrument 를 **뺀** 모든 레이어의 resolve 에
   conditionName 'next-js' 가 붙는다 (L1426-1436)
```

```text
 ★★★ node_modules 를 번들할지 밖에 둘지 — 레이어로 갈린다 (build/handle-externals.ts)

 handleExternals 는 **node server 컴파일러에만** 걸린다 (WPCFG L1017-1071)
   client 는 ['next'] 하나, edge 는 'next' + partytown·etag 빈 모듈 + edge polyfill 모듈 +
   handleWebpackExternalForEdgeRuntime 이다 (L1004-1016)

 handle-externals.ts L293-298
   const isOptOutBundling = optOutBundlingPackageRegex.test(res)
   // Apply bundling rules to all app layers.
   // ... (L295 한 줄 생략)
   if (!isOptOutBundling && isAppLayer) { return }   (소스는 여러 줄)          ← **번들한다**
 L385-399  resolveBundlingOptOutPackages
   node_modules 이고, (Pages 레이어 + bundlePagesRouterDependencies) 도 아니고
   transpilePackages 도 아니면  => `${externalType} ${request}`   ← **밖에 둔다**

   isAppLayer = isWebpackBundledLayer(layer)
     = rsc · action-browser · ssr · app-pages-browser · shared · instrument · middleware (lib/constants.ts L197-205)

 => App Router 쪽은 기본이 **번들**, Pages Router 쪽은 기본이 **external** 이다
 => 밖에 둔 패키지는 청크에 없다. 그래서 [02]의 NFT 가 그 파일을 찾아
    배포 산출물에 넣어 줘야 한다 ※ (두 코드를 잇는 주석은 없다. 인과는 내 추론이다)
 ★ 기본 opt-out 목록 EXTERNAL_PACKAGES 는 lib/server-external-packages.jsonc 의 **79개**다
   (주석을 걷고 JSON 으로 읽어 셌다). DEFAULT_TRANSPILED_PACKAGES 는 ['geist'] 하나다
```

```text
 ★★ 서버 번들의 파일 배치가 여기서 정해진다 (L1337-1345 · L1133-1139)

   output.path     !dev && node server  => .next/server/chunks
   output.filename node server(prod)    => '../[name].js'
   splitChunks     node · edge server   => { filename: [edge-chunks/][name].js, chunks: 'all', minChunks: 2 }

 => 엔트리(app/blog/page.js)는 한 단계 올라가 .next/server/app/blog/page.js 가 되고,
    공유 청크는 .next/server/chunks/ 에 남는다
 => [02]의 TraceEntryPointsPlugin 이 `.nft.json` 을 쓸 때 '../' 를 앞에 붙이는 이유다
    (NFTPLUG L224-226 주석 "server compiler outputs to `server/chunks` so we traverse up one")
```

```text
 ★★ 사용자 `config.webpack` 훅은 **중간**에 끼고, Next 가 그 뒤를 다시 고친다 (L2587-2647)

 L2591  webpackConfig = config.webpack(webpackConfig, {
          dir, dev, isServer, buildId, config, defaultLoaders,
          totalPages: Object.keys(entrypoints).length,   ← 이 컴파일러의 엔트리 수
          webpack: bundler,                               ← **Rspack 이면 Rspack 코어**
          nextRuntime: 'edge' | 'nodejs' (서버 컴파일러만) })
 L2615  반환이 falsy 면 => throw  "Webpack config is undefined. You may have forgot to return ..."
 L2622  dev 에서 devtool 을 바꿨으면 **되돌리고** 경고한다
 L2631  experiments.lazyCompilation 의 entries 를 **false 로 강제**
          주석 L2630 "disable lazy compilation of entries as next.js has it's own method here"
 L2642  반환이 Promise 면 경고만 한다 — await 하지 않는다

 => 훅은 buildConfiguration(CSS·이미지, L2547) **뒤**, svg 보정·CSS 감지·엔트리 확정 **앞**이다
 => 그래서 사용자가 CSS 규칙을 넣으면 L2812-2847 이 Next 의 CSS 로더·추출 플러그인·CSS 최소화기를
    표식(Symbol.for('__next_css_remove') · __next_css_remove)으로 찾아 **걷어낸다**
    (서버 컴파일러에서 한 번 경고: "Built-in CSS support is being disabled ...")
```

```text
 ★★ 캐시 무효화 키가 **문자열 하나**다 (L2415-2459)

   version: `${__dirname}|${process.env.__NEXT_VERSION}|${configVars}`
     주석 L2419-2422 — Next.js 의 디스크 위치 · 버전 · 컴파일에 영향을 주는 next.config 키
   buildDependencies: config.webpack 과 config.configFile 이 둘 다 있을 때만 next.config 파일을 넣는다 (L2432-2443)
   L2445  done 훅에서 buildDependencies 중 **next 패키지 안의 파일을 지운다**
     주석 L2449-2450 "they are already covered by the cacheVersion and next.js also imports
       the output files which leads to broken caching."

 => configVars(L2380-2413)에 없는 설정 키를 바꾸면 캐시가 그대로 쓰인다 ※
    (어떤 키가 빠졌는지는 대조하지 않았다)
 ★ Rspack 은 이 cache 를 버리고 .next/cache/rspack/<compilerType>[-fallback] 의 (L2473) persistent 캐시로 바꾼다.
   buildDependencies 에 next.config · babel 설정 · tsconfig 를 넣는다 (L2461-2483)
```

```text
 ★ 만들어 놓고 안 쓰는 값이 있다

   L836  const nextFrameworkPaths: string[] = []
   L886  addPackagePath('next', dir, nextFrameworkPaths)
   => 이 파일에서 nextFrameworkPaths 를 읽는 곳이 **없다** (grep 결과 L836 · L886 두 줄뿐, 지역 상수)
      짝인 topLevelFrameworkPaths 는 framework 청크 test(L1149 · L1224)에서 쓰인다
```

```text
 설정이 컴파일러가 되는 곳 — build/compiler.ts (93줄)

 L39   runCompiler(config, { runWebpackSpan, inputFileSystem })
 L55     compiler = getWebpackBundler()(config)
 L58     이전 컴파일러의 inputFileSystem 을 **이어 받는다** — 한 프로세스에서 server → edge → client 를
         잇달아 돌릴 때다 (WPIMPL L243 · L254 · L287). 컴파일러마다 워커를 따로 띄우면 이을 것이 없다
 L62     compiler.run((err, stats) => {
 L67       closeCompiler(compiler)  주석 L30 "Webpack 5 requires the compiler to be closed (to save caches)"
 L69       err 가 있고 stack/문자열이 비어 있지 않으면 errors 한 칸짜리 결과로 **resolve** 한다 (L71-81 — 비어 있을 때만 reject)
 L82       stats 가 없으면 throw — 그런데 이것은 `.then` 콜백 안이라
           바깥 Promise 의 resolve/reject 어느 쪽도 불리지 않는다 — 대신 unhandledRejection 이 되어
           부모 빌드 프로세스면 전역 리스너가 exit 1 로 끝낸다 (lib/setup-exception-listeners.ts L6-9)
           ※ webpack 이 err 와 stats 를 둘 다 없이 부르는 경우가 있는지는 확인하지 않았다
 L87       generateStats — errors-warnings 프리셋으로 모은다
```

## 결과가 쓰이는 곳

```text
 webpack.Configuration (컴파일러마다)
      --> WPIMPL 이 runCompiler 에 넘긴다. [빌드] 02 의 server → edge → client 순서

 serverConfig.plugins 안의 TraceEntryPointsPlugin 인스턴스
      --> WPIMPL L326-328 이 **plugins 배열에서 찾아** buildTraceContext 를 꺼낸다 → [02]

 DefinePlugin(getDefineEnv(...)) (L2064-2080)
      --> process.env.* 치환. getDefineEnv 는 Turbopack 도 쓴다 (build/swc/index.ts L463)

 cache.cacheDirectory (.next/cache/webpack)
      --> getCacheDirectories(L297)가 모은다. 그 호출처는 개발 서버(hot-reloader-webpack.ts L1239 · L1669)뿐이다

 defaultLoaders · webpack(=bundler)
      --> 사용자 next.config 의 webpack 훅
```

## 다루지 않는 것

`buildConfiguration`(`build/webpack/config/index.ts`)의 CSS·Sass·이미지 블록, `splitChunks` 의 client 쪽 캐시 그룹(framework · lib, L1141-1244) 세부와 `minimizer`(L1255-1313)의 SWC·CSS 최소화기, `createWebpackAliases` · `createVendoredReactAliases` · `createServerOnlyClientOnlyAliases` 가 만드는 alias 표의 내용, `resolveExternal`(`handle-externals.ts` L45)의 ESM/CJS 해석과 `resolveNextExternal` 의 `.external` 규칙, `plugins` 배열 각 항목의 본문(`FlightClientEntryPlugin` · `ClientReferenceManifestPlugin` · `MiddlewarePlugin` · `NextTypesPlugin` · `DeferredEntriesPlugin` 등), `getNextRootParamsRules`(L2905-2967), `next-swc-loader` 와 `next-flight-loader` 의 본문, 여러 규칙이 같은 모듈에 맞을 때 로더가 실행되는 순서, `NEXT_WEBPACK_LOGGING`(L2485-2545), `dev` 전용 갈래(React Refresh · MemoryWithGcCachePlugin · unsafeCache), `webpackDevMiddleware` 호환(L2759-2766), 그리고 Rspack 전용 플러그인(`NextExternalsPlugin` · `RspackFlightClientEntryPlugin`)의 구현은 이 문서의 범위 밖이다.
