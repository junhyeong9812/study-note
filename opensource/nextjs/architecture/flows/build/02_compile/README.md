# 02 번들러를 돌린다

상위: [`next build` 가 산출물을 만들기까지](../README.md)

`#region Compile`(L1765-1939)은 175줄인데 **두 번들러로 갈리는 자리**가 여기다. Turbopack 쪽은 호출 하나로 끝나고, webpack 쪽은 컴파일러 셋을 **정해진 순서로** 돌린다. 어느 쪽이든 결과는 `.next/` 아래의 파일과 매니페스트이고, 다음 단계는 그 파일을 읽는다. Turbopack 내부(Rust)는 이 흐름의 범위 밖이다.

만나는 흐름 — [`'use cache'`](../../use-cache/README.md)의 캐시 래퍼 치환과 [메타데이터](../../metadata/README.md)의 export 검사가 이 단계의 SWC 변환에서 일어난다. [메타데이터]는 그 검사 문구(`react_server_components.rs` L361-364)까지 확인했다 — 여기서는 그 변환이 **어느 단계에서 도는가**만 잇는다.

## 위치

`packages/next` / `src/build` / `index.ts` L1765-L1939 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/index.ts#L1765-L1939))

## 실제 코드

webpack 에서 client 컴파일러가 **마지막**인 이유가 이 블록이다.

```ts
// impl.ts L259-L293
    // Only continue if there were no errors
    if (!serverResult?.errors.length && !edgeServerResult?.errors.length) {
      const pluginState = getPluginState()
      for (const key in pluginState.injectedClientEntries) {
        const value = pluginState.injectedClientEntries[key]
        const clientEntry = clientConfig.entry as webpack.EntryObject
        if (key === APP_CLIENT_INTERNALS) {
          clientEntry[CLIENT_STATIC_FILES_RUNTIME_MAIN_APP] = {
            import: [
              // TODO-APP: cast clientEntry[CLIENT_STATIC_FILES_RUNTIME_MAIN_APP] to type EntryDescription once it's available from webpack
              // @ts-expect-error clientEntry['main-app'] is type EntryDescription { import: ... }
              ...clientEntry[CLIENT_STATIC_FILES_RUNTIME_MAIN_APP].import,
              value,
            ],
            layer: WEBPACK_LAYERS.appPagesBrowser,
          }
        } else {
          clientEntry[key] = {
            dependOn: [CLIENT_STATIC_FILES_RUNTIME_MAIN_APP],
            import: value,
            layer: WEBPACK_LAYERS.appPagesBrowser,
          }
        }
      }

      if (!compilerName || compilerName === 'client') {
        debug('starting client compiler')
        const start = Date.now()
        ;[clientResult, inputFileSystem] = await runCompiler(clientConfig, {
          runWebpackSpan,
          inputFileSystem,
        })
        debug(`client compiler finished ${Date.now() - start}ms`)
      }
    }
```

```text
 ★★★ client 엔트리의 일부를 **server 컴파일러가 만든다**

 주석 WPIMPL L226-227 - "Run the server compilers first and then the client
   compiler to track the boundary of server/client components."
 주석 L230-231 - "During the server compilations, entries of client components will be
   injected to this set and then will be consumed by the client compiler."

 => server 컴파일러가 RSC 트리를 훑다가 'use client' 경계를 만나면
    pluginState.injectedClientEntries 에 넣는다. client 컴파일러는 그것을 엔트리로 받는다
 => 그래서 app/ 페이지의 client 엔트리는 createEntrypoints 에서 **일부러 비워 둔다**
      entries.ts L503-505
        if (isServerComponent || isInsideAppDir) {
          // We skip the initial entries for server component pages and let the
          // server compiler inject them instead.
 ★ server 나 edge 에 오류가 있으면 client 컴파일은 **아예 안 돈다** (L260, 주석 L259)
 ★ APP_CLIENT_INTERNALS 는 새 엔트리가 아니라 `main-app` 엔트리의 import 목록에 **덧붙인다** (L265-274)
```

## 동작 흐름

```text
 BUILD L1778  if (!isGenerateMode) {             ← generate 모드는 컴파일을 통째로 건너뛴다
 L1779    if (bundler === Bundler.Turbopack) {
 L1785      turbopackBuild(useWorker, telemetry)
              useWorker = NEXT_TURBOPACK_USE_WORKER 가 없거나 '0' 이 아니면 (L1786-1787)
 L1790      shutdownPromise = p                  ← **기다리지 않는다.** L4529 에서 맨 끝에 await
 L1791      deferredTurbopackWarnings = warnings ← 경고를 **나중에** 찍는다
 L1794      buildTraceContext = rest.buildTraceContext   (Turbopack 은 언제나 undefined)
 L1806    } else {                               ← webpack · Rspack
 L1807      parallelServerCompiles || parallelServerBuildTraces 면
 L1817        webpackBuild(useBuildWorker, ['server'])      .then 안에서 NFT 워커를 띄울 수 있다
 L1874        webpackBuild(useBuildWorker, ['edge-server'])
                parallelServerCompiles 면 server 와 edge 가 **동시에** 돈다 (L1867 · L1883)
 L1895        webpackBuild(useBuildWorker, ['client'])      언제나 마지막
 L1910      아니면
 L1911        webpackBuild(useBuildWorker, null)            null = 셋 다
 L1928    runAfterProductionCompile(...)
```

```text
 Turbopack 갈래 — TPBUILD(turbopack-build/index.ts 95줄) → TPIMPL

 TPBUILD L85   traceChild('run-turbopack')
 TPBUILD L13   new Worker(impl.js, { enableWorkerThreads: true, numWorkers: 1, maxRetries: 0 })
 TPBUILD L33   NextBuildContext 에서 nextBuildSpan · config 를 빼고 넘긴다
                 주석 L35 "Config is not serializable and is loaded in the worker."
 TPIMPL L323   workerMain → L334 loadConfig 를 **워커에서 다시** 부른다
 TPIMPL L39    turbopackBuild(telemetry)
 L64             bindings.isWasm 이면 => throw  "Turbopack is not supported on this platform ...
                                                  use Webpack instead: next build --webpack"
 L139            project = bindings.turbo.createProject(...)       ← 여기서 Rust 로 넘어간다
 L172            .next/turbopack 에 **빈 파일**을 쓴다  주석 "signal this was built with Turbopack"
 L185            entrypoints = project.writeAllEntrypointsToDisk(appDirOnly)
 L188            printBuildErrors(entrypoints, dev, { deferWarnings: true })
 L220            pages 엔트리가 없으면 appDirOnly = true
 L238-260        라우트마다 handleRouteType(...) — pages(appDirOnly 가 아닐 때) 와 app
 L288            manifestLoader.writeManifests(...)   ← 매니페스트는 **JS 쪽이 쓴다**
 L302            shutdownPromise = project.shutdown().then(...)
 L308            return { duration, buildTraceContext: undefined, shutdownPromise, warnings }
```

```text
 webpack 갈래 — WPBUILD(webpack-build/index.ts 163줄) → WPIMPL

 WPBUILD L139  traceChild('run-webpack')
 WPBUILD L140  withWorker 이면 webpackBuildWithWorker(compilerNames)
 L37             compilerNames 가 null 이면 ORDERED_COMPILER_NAMES = ['server', 'edge-server', 'client']
 L47             for (const compilerName of compilerNames) {        ← **순차**
 L48               new Worker(impl.js, { numWorkers: 1, maxRetries: 0 })
 L68               await worker.workerMain({ buildContext, compilerName, ... })
 L81               await worker.end()    주석 "destroy worker so it's not sticking around using memory"
 L84               pluginState = deepMerge(pluginState, curResult.pluginState)
 L85               prunedBuildContext.pluginState = pluginState   ← **다음 워커에 넘긴다**
               }
 WPIMPL L420   workerMain 이 resumePluginState(NextBuildContext.pluginState) 로 이어 받는다

 => `useBuildWorker` 이면 컴파일러마다 **프로세스가 따로**다. 커스텀 webpack 설정이 있으면 기본값이
    false 가 되고(BUILD L1739-1742) 셋 다 같은 프로세스에서 돈다(WPBUILD L143-147
    "building all compilers in same process"). 그래서 위 "server 가 client 엔트리를 만든다" 가
    프로세스를 건너려면 pluginState 를 직렬화해 들고 다녀야 한다
 ★★ 그리고 워커마다 **엔트리 생성과 설정 셋을 전부** 다시 한다 —
   WPIMPL L99-118 createEntrypoints · L162-199 getBaseWebpackConfig ×3 은 조건 없이 돌고,
   compilerName 은 runCompiler 만 가른다 (L240 · L250 · L284)

 useBuildWorker (BUILD L1739-1742)
   = experimental.webpackBuildWorker, 또는 그 값이 없고 **커스텀 webpack 설정이 없을 때**
 병렬 옵션은 워커 없이는 금지 (L1756-1763 => throw)
```

```text
 createEntrypoints  entries.ts L382-669 — **webpack 만 부른다**

 호출처 grep "createEntrypoints(" 전수
   build/webpack-build/impl.ts L102 · L125       (L125 는 deferredEntries 용 두 번째 호출)
   server/dev/hot-reloader-webpack.ts L733 · L825  (개발 서버)
 => turbopack-build/ 에는 없다

 L638-653  appPaths → rootPaths → pages 순으로 getEntryHandler 를 걸어 Promise.all
 L475      페이지마다 getStaticInfoIncludingLayouts(...)   ← **소스를 정적 분석**해 runtime 등을 읽는다
 L498      runDependingOnPageType(...) 이 client · server · edgeServer 중 어디에 넣을지 고른다
             (L316-380. API 라우트는 server 또는 edge 하나, _document 는 server 만,
              _app · _error · 404 · 500 은 client + server)
 L516      app 페이지의 server 엔트리 = getAppEntry(...)   ← [App Router]의 페이지 모듈이 여기서 생긴다 ※
 L663      return { client, server, edgeServer, middlewareMatchers }

 ★ 반환 타입이 `middlewareMatchers: undefined` 로 적혀 있다 (L388) —
   그런데 본문은 L490 에서 ProxyMatcher[] 를 넣고 L667 에서 돌려준다
   ※ 대입이 async 콜백 안이라 TS 가 L667 시점의 타입을 `undefined` 로 좁혀 통과시킨 것으로 보인다.
     WPIMPL L173 이 이 값을 getBaseWebpackConfig 에 그대로 넘긴다
```

```text
 ★★ SWC 변환은 **이 단계 안에서** 돈다 — 번들러마다 등록 지점이 다르다

   webpack   build/swc/options.ts L233-243  serverActions: { useCacheEnabled, cacheKinds, ... }
   Turbopack crates/next-core/src/next_shared/transforms/server_actions.rs
             (next_custom_transforms::transforms::server_actions 를 가져다 쓴다, L4-5)

 [`'use cache'`]   'use cache' 지시어도 같은 변환이 다룬다
                   (crates/next-custom-transforms/src/transforms/server_actions.rs L326 · L1074 주석)
                   => 캐시 래퍼 호출로 바뀌는 것은 **번들 시점**이다
 [메타데이터]      react_server_components.rs L362
                   "\"metadata\" and \"generateMetadata\" cannot be exported at the same time ..."
                   => 둘을 함께 export 하면 **[03]까지 가지 못한다** ※
                   (※ 변환 오류가 빌드 실패로 이어지는 경로는 확인하지 않았다)
```

## 결과가 쓰이는 곳

```text
 .next/server/** 의 컴파일된 모듈
      --> [03]의 isPageStatic 과 [04]의 export 워커가 loadComponents 로 require 한다

 pages-manifest · build-manifest · app-paths-manifest · middleware-manifest ·
 server-reference-manifest.json
      --> [03]이 BUILD L2171-2179 · L2291-2303 에서 **파일로 다시 읽는다**

 buildTraceContext (webpack 만)
      --> NFT region 의 collectBuildTraces (L2818-2842). Turbopack 이면 **이 if 블록만** 빠진다.
          region 의 나머지(dataRoutes · routes-manifest 첫 쓰기 L2877 · invalidPages throw ·
          writeBuildId L2899 · prerender-manifest 초기화)는 Turbopack 에서도 돈다

 deferredTurbopackWarnings
      --> [04]가 끝난 뒤 L4165 flushTurbopackWarnings() 가 찍는다.
          주석 TPIMPL L186-187 "keeping SSG errors more prominent than compile warnings"

 shutdownPromise (Turbopack)
      --> build() 의 거의 마지막 L4529 에서 await. 주석 TPBUILD L50
          "We need to wait for shutdown to make sure filesystem cache is flushed"
```

## 다루지 않는 것

`getBaseWebpackConfig`(`build/webpack-config.ts`)와 그 안의 로더·플러그인 전부, `runCompiler`(`build/compiler.ts`)와 webpack 오류 포맷, `FlightClientEntryPlugin` 등 `injectedClientEntries` 를 채우는 쪽, `getAppEntry` · `getEdgeServerEntry` · `getRouteLoaderEntry` 가 만드는 로더 문자열, `getStaticInfoIncludingLayouts` 의 정적 분석, `deferredEntries` 와 `onBeforeDeferredEntries`, `webpackMemoryOptimizations`(L221-224), `collectBuildTraces` 워커(L1824-1865), `createProject` · `writeAllEntrypointsToDisk` · `handleRouteType` · `TurbopackManifestLoader` 의 구현, `backgroundLogCompilationEvents`, `seedTurbopackCacheIfNeeded`(L122-127)와 파일 시스템 캐시, `runAfterProductionCompile`(`build/after-production-compile.ts`), Rspack 고유 처리, 그리고 SWC 변환(`crates/next-custom-transforms/`)과 Turbopack(`crates/`)의 Rust 본문은 이 문서의 범위 밖이다.
