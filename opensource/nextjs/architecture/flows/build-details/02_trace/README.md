# 02 실행에 필요한 파일을 추적한다

상위: [빌드가 번들러 설정과 배포 산출물을 만들기까지](../README.md)

**webpack·Rspack 전용이다.** Turbopack 은 같은 이름의 `.nft.json` 을 Rust 에서 스스로 쓴다(`crates/next-api/src/nft_json.rs` · `next_server_nft.rs`) — 이 문서의 코드는 그때 돌지 않는다. webpack 쪽에서는 NFT(`nodeFileTrace`)가 **두 번** 돈다. 한 번은 server 컴파일 **안에서** 플러그인이 소스 모듈을 추적하고, 한 번은 컴파일 **뒤에** `collectBuildTraces` 가 만들어진 청크를 추적해 앞의 결과에 덧붙인다. 결과 파일은 [03] 어댑터와 [04] standalone 이 복사 목록으로 읽는다.

## 위치

`packages/next` / `src/build/webpack/plugins` / `next-trace-entrypoints-plugin.ts` L129-L813 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/webpack/plugins/next-trace-entrypoints-plugin.ts#L129-L813))

`packages/next` / `src/build` / `collect-build-traces.ts` L94-L686 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/collect-build-traces.ts#L94-L686))

## 실제 코드

첫 번째 추적(플러그인)은 **`node_modules` 를 아예 보지 않는다.**

```ts
// next-trace-entrypoints-plugin.ts L474-L480
            let fileList: Set<string>
            let reasons: NodeFileTraceReasons
            const ignores = [
              ...TRACE_IGNORES,
              ...this.traceIgnores,
              '**/node_modules/**',
            ]
```

```text
 ★★★ 두 추적이 보는 것이 다르다

 1차  TraceEntryPointsPlugin (컴파일 중, finishModules 훅)
        입력  엔트리 모듈과 그 의존 모듈의 **소스**(readFile 이 webpack 모듈의 변환된 소스를 준다, L418-427)
        무시  TRACE_IGNORES + '**/node_modules/**'           (위 코드)
        남김  로더가 처리한 파일(= 번들에 들어간 것)은 bundled 로 표시해 뺀다 (L520-539)
      => 1차 `.nft.json` 에 들어가는 것은 셋이다
         엔트리가 참조하는 **webpack 청크 전부**(chunk.files · auxiliaryFiles, L187-205)
         app 이면 client-reference-manifest (L239-262)
         node_modules 밖에서 번들되지 않은 소스 추적 파일 (L266-285 에서 합친다)
      ★ 2차는 라우트별로 `'**/.next/server/chunks/**'` 를 무시하므로(CBT L272-279)
        **페이지별 청크 목록은 1차 파일에만** 있다. 2차는 청크가 require 하는 node_modules 를 더한다

 2차  collectBuildTraces (컴파일 뒤, 별도 region 또는 워커)
        입력  **emit 된 청크 파일**(.next/server/chunks/*.js 등)과 next-server 엔트리
        무시  node_modules 는 무시하지 않는다
      => 청크가 require 하는 **external 패키지**(node_modules)가 여기서 잡힌다
         [01]의 handleExternals 가 밖에 둔 것들이다 ※

 ★ 그래서 1차가 쓴 `.nft.json` 은 **2차가 끝나기 전에는 node_modules 가 빠진 반쪽**이다.
   2차는 1차 파일을 읽어 합친다 (CBT L453 · L487-489)
```

## 동작 흐름

```text
 1차 — TraceEntryPointsPlugin   NFTPLUG (813줄)

 생성처  WPCFG L2089-2105  `isNodeServer && !dev && new TraceEntryPointsPlugin({...})`  ← **유일**
 L593   apply(compiler)
 L594     compiler.hooks.compilation.tap
 L803       tapfinishModules(...)  → compilation.hooks.finishModules (L313)
 L333         compilation.entries 중 app/ · pages/ · middleware(proxy) 엔트리만
                주석 L339-343 - middleware 는 프로젝트 루트에 있어 따로 문을 열었다.
                "Without this, source-level NFT analysis is skipped for the middleware/proxy entry"
 L353         로더가 만든 엔트리면(resource === '') buildInfo.route.absolutePagePath 로 원본 파일을 찾는다
 L431         collectDependencies — 모듈 그래프를 재귀로 따라 depModMap 을 채운다
 L458         buildTraceContext.entriesTrace = {...}
 L496         nodeFileTrace(entriesToTrace, { readFile, resolve: doResolve, ignore, ... })
 L520         getFilesMapFromReasons — reasons 트리를 부모 쪽으로 전파해 **엔트리별 파일 목록**
 L581         this.entryTraces.set(entryName, finalDeps)
 L642     compilation.hooks.processAssets (stage SUMMARIZE)
 L174       createTraceAssets
 L187         엔트리마다 getAllReferencedChunks 의 files · auxiliaryFiles (.wasm · 이미지 확장자 제외)
 L213         buildTraceContext.chunksTrace = { action.input: 모든 청크, entryNameFilesMap }
 L229         `${outputPrefix}${entry}.js.nft.json`
                outputPrefix = compilerType === 'server' ? '../' : ''  (L224-226)
                ★ 주석은 edge-server 를 위한 '' 갈래를 적지만 **닿지 않는다** — 생성처가
                  `isNodeServer && !dev` 하나라서 compilerType 은 언제나 'server' 다
 L239-262     app 엔트리면 `<entry>_client-reference-manifest.js` 를 목록에 **직접 넣는다**
                (정적 메타데이터 라우트는 빼고. 주석 L249-250)
 L288         compilation.emitAsset(...)  { version, files }        ← **1차 `.nft.json` 이 여기서 생긴다**

 WPIMPL L326-328  serverConfig.plugins 에서 이 플러그인을 **찾아** buildTraceContext 를 꺼낸다
 WPIMPL L386      결과 객체에 실어 부모 프로세스로 돌려준다
```

```text
 2차 — collectBuildTraces   CBT L94-686 (593줄)

 누가 부르나 (grep "collectBuildTraces" — 두 곳)
   BUILD L1824-1865  parallelServerBuildTraces 면 server 컴파일 직후 **별도 워커**
                      staticPages: [] · edgeRuntimeRoutes: 빈 Map 으로 넘긴다
   BUILD L2818-2842  #region NFT — webpack·Rspack 이고 generate 모드가 아니고 위에서 안 띄웠으면
                      staticPages · edgeRuntimeRoutes 를 제대로 채워 넘긴다
   둘 다 promise 만 buildTracesPromise 에 넣고 **기다리지 않는다.** BUILD L4348 에서 await
   기본값: parallelServerBuildTraces 는 설정이 없고 compile 모드일 때만 true (BUILD L1745-1748)

 L122   span 'node-file-trace-build'  (isTurbotrace: 'false' — 주석 "TODO(arlyon): remove this")
 L139   isStandalone = config.output === 'standalone'
 L140   sharedEntriesSet = require-hook 의 defaultOverrides 가 가리키는 모듈들
 L150   cacheHandler · cacheHandlers 가 있으면 그 파일도 엔트리에 넣는다
 L196   serverEntries        = shared + (standalone 이면 start-server · next · require-hook) + next-server
 L208   minimalServerEntries = shared + compiled/next-server/server.runtime.prod
 L223   sharedIgnores  — standalone 이 아니면 jest-worker 와 TRACE_IGNORES 도 무시
 L252   serverIgnores  — + react 의 *.development.js · *.d.ts · *.map · next/dist/pages
 L264   minimalServerIgnores — + edge-runtime · web/sandbox · post-process
 L272   routesIgnores  — + '**/.next/server/chunks/**'  (아래 ★★)
 L292   standalone 이면 jest-worker 의 processChild · threadChild 를 직접 넣는다
 L311   nodeFileTrace([...청크, ...serverEntries, ...minimalServerEntries], {...})   ← **한 번에**
 L385     serverEntries → serverTracedFiles, minimalServerEntries → minimalServerTracedFiles
 L424     엔트리마다 (Promise.all)
 L444       staticPages 에 있으면 건너뛴다 — 주석 L440-443 "automatically statically optimized
              pages ... don't have server bundles"
 L453       1차 `.nft.json` 을 읽고 (JSON.parse)
 L463       그 엔트리의 청크 + 엔트리 파일에서 reasons 로 딸린 파일을 모아
 L487       1차 목록을 합친 뒤
 L491       **같은 파일에 덮어쓴다**   (아래 실제 코드 주변)
 L502   route-modules/app-page · pages 의 module.compiled 와 vendored/contexts 를 **손으로** 추가
 L534   next-server.js.nft.json · next-minimal-server.js.nft.json 을 쓴다
 L559   span 'apply-include-excludes' — outputFileTracingIncludes/Excludes 를 라우트 glob 으로 적용
 ★ exclude 는 한 번 더 쓰인다 — 키가 'next-server' 에 맞으면(L214-221) 그 패턴을 서버 NFT 자체의
   ignore 에 넣는다 (additionalIgnores → sharedIgnores, L246-247)
 ★ 이 적용은 webpack·Rspack 전용이다. 기본 Turbopack 은 Rust 가 따로 한다 —
   crates/next-api/src/nft.rs L79-80 · L143(includes) · L228(tracing_exclude_glob)
```

```text
 ★★ 청크를 추적할 때 **webpack 이 정한 경계를 넘지 않는다** (CBT L362-371)

   // if a chunk is attempting to be traced that isn't
   // in our initial list we need to ignore it to prevent
   // over tracing as webpack needs to be the source of
   // truth for which chunks should be included for each entry
   if (p.includes('.next/server/chunks') && !chunksToTrace.includes(...)) return true

 그리고 라우트별 목록에서는 청크 디렉터리를 통째로 무시한다 (L272-279)
   주석 L274-276 "server chunks are provided via next-trace-entrypoints-plugin plugin
     as otherwise all chunks are traced here and included for all pages
     whether they are needed or not"
 => 어느 청크가 어느 페이지에 필요한지는 **1차(플러그인)가 webpack 청크 그래프로** 정한다.
    2차는 그 청크들 **안의 require** 만 따라간다
```

```text
 ★★ NFT 가 SSG 와 동시에 돌아서 **파일이 사라지는 것을 견딘다** (CBT L316-328)

   async readFile(p) { ... if (ENOENT || EISDIR) return '' ... }
   주석 L321-323 "since tracing runs in parallel with static generation server
     files might be removed from that step so tolerate ENOENT errors gracefully"

 실제로 지우는 쪽 — BUILD L3269-3278 (SSG region, exportApp 뒤)
   // remove server bundles that were exported
   for (const page of staticPages) { ... await fs.unlink(serverBundle) }   ('/404' 만 남긴다)
 => Pages Router 의 정적 페이지 서버 번들을 SSG 가 지우는 동안 NFT 가 그것을 읽고 있을 수 있다 ※
    (주석이 가리키는 "that step" 이 이 unlink 라는 것은 내 대조다)
 ★ 반면 L453 의 1차 `.nft.json` 읽기는 **견디지 않는다** — 없으면 그대로 throw 한다
```

```text
 ★★ 병렬 워커판은 정적 페이지도 추적한다

   BUILD L1854-1856  edgeRuntimeRoutes: collectRoutesUsingEdgeRuntime(new Map()),  staticPages: []
 => L444 의 건너뛰기가 **아무것도 걸러내지 않는다.** server 컴파일 직후라 아직
    Collect data 가 돌기 전이어서 정적 여부를 모르기 때문이다 ※
 => 대가는 추적량이다. 결과 파일이 틀리는 것은 아니다 ※
```

```text
 ★ 같은 이름을 두 곳이 **다르게** 정규화한다

   L433-435  (추적 쓰기)          route = normalizeAppPath(route.substring('app'.length))
   L587-589  (include/exclude)    route = normalizeAppPath(entryName)       ← 'app' 을 안 뗀다
   Pages 쪽도 같다 — L437 은 substring('pages'.length), L591 은 entryName 그대로

   normalizeAppPath('app/blog/page') = '/app/blog'  (shared/lib/router/utils/app-paths.ts L23-51 —
   'app' 은 그룹·병렬 세그먼트가 아니라서 그대로 남는다)
 => include/exclude 쪽의 route 는 '/app/blog' 모양이다.
    그 값으로 staticPages.includes · edgeRuntimeRoutes.hasOwnProperty ·
    outputFileTracingIncludes 의 glob(picomatch, contains: true)을 맞춘다
 => CBT L18 의 picomatch 는 `contains: true` 면 앞뒤 앵커 없이 **부분 일치**다
    그래서 라우트 기준 glob(`/api/*` · `/blog`)은 '/pages/api/x' · '/app/blog' 에도 맞는다 — **놓침은 없다**.
    대신 '/app' · '/pages' 접두에 걸리는 과다 일치가 생길 수 있다
 ★ L594 `staticPages.includes(route)` 는 모양이 달라 **참이 될 수 없다** (정적 Pages 엔트리의 nft 에도
   include/exclude 가 적용되지만, standalone L1367 · 어댑터가 정적 페이지를 건너뛰어 실해는 없다)
```

```text
 ★★ 1차가 만든 것 중 **절반은 아무도 안 읽는다**

   BuildTraceContext (NFTPLUG L113-127)
     entriesTrace { action, appDir, outputPath, depModArray, entryNameMap, absolutePathByEntryName }
     chunksTrace  { action, outputPath, entryNameFilesMap }

   collectBuildTraces 가 읽는 것  chunksTrace.action.input (L307) · chunksTrace.entryNameFilesMap (L420 · L578)
   entriesTrace 를 읽는 곳        플러그인 자신의 L241 (absolutePathByEntryName) 하나
     (grep "entriesTrace\|depModArray\|entryNameMap" — 나머지는 워커 경계를 넘길 때
      제 값을 제 자리에 다시 대입하는 코드뿐이다: WPIMPL L438-447 · webpack-build/index.ts L99-107)
 ★ `action: 'print' | 'annotate'` 와 타입 이름 `TurbotraceAction`(L104) 은 Turbotrace 시절의 모양이다 ※
   지금 `action` 에서 쓰이는 필드는 input 하나다
```

```text
 ★★★ Turbopack 이 쓰는 `.nft.json` 은 **모양이 다르다**

   webpack·Rspack   { version, files }                       (NFTPLUG L291-294, CBT L493-496)
   Turbopack        { version, files, fileHashes, entryHash } (crates/next-api/src/nft_json.rs L281-286)
     주석 nft_json.rs L271-276 — entryHash 를 files 에 넣지 않고 따로 둔 것은
       정적 페이지의 .js 가 지워질 수 있어서이고, "a separate field that only build-complete reads"

 그리고 next-server 쪽 두 파일
   webpack·Rspack   CBT L534-555 가 **언제나 둘 다** 쓴다
   Turbopack        next_server_nft.rs L76-115 —
                      어댑터가 있고 standalone 이 아니면 **둘 다 안 쓴다**
                      Vercel(hasNextSupport)이고 standalone 이 아니면 minimal 만
                      그 밖엔 둘 다
 => [03] 어댑터의 assetsHashes 가 Turbopack 에서만 채워지는 이유가 이 필드다
```

## 결과가 쓰이는 곳

```text
 .next/server/app/**/<entry>.js.nft.json · .next/server/pages/**/<entry>.js.nft.json
 .next/server/middleware.js.nft.json (node middleware · proxy)
      --> [03] ADBC L689-716 handleTraceFiles → L2572 loadNFT
      --> [04] BUTILS L1266 handleTraceFiles (페이지 · middleware · instrumentation)
      --> BUILD L4361-4398 이 proxy.js.nft.json 을 middleware.js.nft.json 으로 **이름과 내용**을 바꾼다
          (webpack·Rspack 만. await buildTracesPromise(L4348) 뒤라 2차가 끝난 파일을 고친다)

 .next/next-server.js.nft.json
      --> [04] BUTILS L1410 — standalone 이면 **조건 없이** 읽는다

 .next/next-minimal-server.js.nft.json
      --> 이 저장소 안에서 읽는 곳을 찾지 못했다 (grep "next-minimal-server.js.nft.json" —
          쓰는 곳 CBT L133 · next_server_nft.rs L139 뿐) ※ 배포 플랫폼이 읽는 것으로 보인다

 buildTraceContext.chunksTrace
      --> 2차의 입력. 1차 → WPIMPL → (워커 경계) → BUILD → collectBuildTraces
```

## 다루지 않는 것

`@vercel/nft` 의 `nodeFileTrace` 알고리즘과 `reasons` 구조, 플러그인의 `doResolve` · `getResolve`(NFTPLUG L663-801)가 webpack 리졸버로 경로를 풀고 상위 `package.json` 을 함께 넣는 규칙, `resolveExternal` 의 ESM/CJS 판단, `shouldIgnore`(CBT L45-92)의 "부모가 모두 무시되면 자식도 무시" 재귀, `makeIgnoreFn` 의 tracingRoot 밖 경로 처리, `apply-include-excludes`(CBT L559-683)의 glob 해석 세부, `ciEnvironment.hasNextSupport` 가 켜질 때의 차이, Turbopack 이 `.nft.json` 을 만드는 Rust 쪽 전체(인용한 줄 밖), 그리고 edge 런타임 라우트(추적 파일이 없다 — CBT L598)의 번들 파일 목록은 이 문서의 범위 밖이다.
