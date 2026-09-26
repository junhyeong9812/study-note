# 빌드가 번들러 설정과 배포 산출물을 만들기까지

상위: [Next.js 아키텍처 지도](../../README.md)

**먼저 밝혀 둔다 — 이 흐름의 절반은 기본 설정에서 돌지 않는다.** v16.3.6 의 기본 번들러는 Turbopack 이다(`lib/bundler.ts` L99-102, 아무 플래그도 없으면 `Bundler.Turbopack`). 아래 [01] webpack 설정 조립과 [02] NFT 추적은 `bundler !== Bundler.Turbopack` 일 때만 돈다 — 즉 `--webpack` 을 주거나 설정이 `NEXT_RSPACK` 을 세워 **webpack 또는 Rspack** 이 골라졌을 때다. 반대로 [03] 어댑터와 [04] standalone 은 번들러와 상관없이 돈다. [빌드](../build/README.md) 흐름이 "다루지 않는 것" 으로 넘긴 깊이 — 설정 조립, 파일 추적, 배포 산출물 — 를 여기서 따라간다.

만나는 흐름 — [빌드](../build/README.md)(부모) · [`'use cache'`](../use-cache/README.md)(캐시 래퍼 alias 와 SWC 변환이 어느 로더에서 켜지는가) · [메타데이터](../metadata/README.md)(메타데이터 라우트가 어느 레이어로 가는가) · [페이지 아닌 요청](../non-page/README.md)(미들웨어 템플릿이 번들 엔트리가 되는 자리와 standalone 의 `server.js` 가 부르는 `startServer`).

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `WPCFG` = `build/webpack-config.ts`(2967줄), `NFTPLUG` = `build/webpack/plugins/next-trace-entrypoints-plugin.ts`(813줄), `CBT` = `build/collect-build-traces.ts`(686줄), `ADBC` = `build/adapter/build-complete.ts`(2619줄), `BUTILS` = `build/utils.ts`(1677줄), `BUILD` = `build/index.ts`(4636줄), `WPIMPL` = `build/webpack-build/impl.ts`(460줄). NFT = `@vercel/nft` 의 `nodeFileTrace`(Node File Trace) — 실행에 필요한 파일을 정적으로 찾아 `*.nft.json` 에 적는다.

## 위치

설정 조립 — `packages/next` / `src/build` / `webpack-config.ts` L327-L2903 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/webpack-config.ts#L327-L2903))

파일 추적 — `packages/next` / `src/build` / `collect-build-traces.ts` L94-L686 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/collect-build-traces.ts#L94-L686))

어댑터 — `packages/next` / `src/build/adapter` / `build-complete.ts` L557-L2322 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/adapter/build-complete.ts#L557-L2322))

standalone — `packages/next` / `src/build` / `utils.ts` L1223-L1469 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/utils.ts#L1223-L1469))

## 실제 코드

`build()` 의 끝, 배포 산출물을 만드는 두 호출이 나란히 있다.

```ts
// index.ts L4428-L4484
      // This should come after output: export handling but before
      // output: standalone, in the future output: standalone might
      // not be allowed if an adapter with onBuildComplete is configured
      const adapterPath = config.adapterPath
      if (adapterPath) {
        await nextBuildSpan
          .traceChild('adapter-handle-build-complete')
          .traceAsyncFn(async () => {
            await handleBuildComplete({
              dir,
              distDir,
              config,
              appType,
              buildId,
              bundler,
              configOutDir: path.join(dir, configOutDir),
              staticPages,
              serverPropsPages,
              nextVersion: process.env.__NEXT_VERSION as string,
              repoRoot: config.repoRoot,
              outputFileTracingRoot,
              hasNodeMiddleware,
              hasInstrumentationHook,
              adapterPath,
              pageKeys: pageKeys.pages,
              appPageKeys: denormalizedAppPages,
              routesManifest,
              prerenderManifest,
              middlewareManifest,
              functionsConfigManifest,
              hasStatic404: useStaticPages404,
              hasStatic500: useDefaultStatic500,
              requiredServerFiles: requiredServerFilesManifest.files,
            })
          })
      }

      if (config.output === 'standalone') {
        await nextBuildSpan
          .traceChild('output-standalone')
          .traceAsyncFn(async () => {
            await writeStandaloneDirectory(
              nextBuildSpan,
              distDir,
              pageKeys,
              denormalizedAppPages,
              outputFileTracingRoot,
              requiredServerFilesManifest,
              middlewareManifest,
              hasNodeMiddleware,
              hasInstrumentationHook,
              staticPages,
              loadedEnvFiles,
              appDir
            )
          })
      }
```

```text
 ★★ 순서가 주석으로 못박혀 있다 (L4428-4430)
   "This should come after output: export handling but before
    output: standalone, in the future output: standalone might
    not be allowed if an adapter with onBuildComplete is configured"
 => output: export → 어댑터 → standalone 순이다. 어댑터는 export 와도 standalone 과도 함께 켜질 수 있다.
    export 와 standalone 은 `config.output` 한 키의 두 값이라 **서로 배타**다 (BUILD L4406 · L4465)
 => 그리고 standalone 이 "어댑터가 있으면 금지될 수 있다" 고 미래형으로 적는다.
    v16.3.6 에는 그런 금지가 없다 — 두 if 사이에 조건이 없다

 ★★★ 두 호출 모두 bundler 로 갈리지 않는다. 그런데 둘 다 `*.nft.json` 을 **읽는다**
   어댑터    ADBC L689-716 handleTraceFiles → L2572 loadNFT  (`${entryFilePath}.nft.json`)
   standalone BUTILS L1266 handleTraceFiles (`${pageFile}.nft.json` · next-server.js.nft.json)
 => 그 파일을 누가 쓰는가가 번들러로 갈린다
      webpack·Rspack  [02] — 컴파일 중 플러그인 + 컴파일 뒤 collectBuildTraces
      Turbopack       Rust 가 직접 쓴다 (crates/next-api/src/nft_json.rs · next_server_nft.rs)
 => `.nft.json` 이 **번들러와 배포 산출물 사이의 계약**이다
```

## 동작 흐름

```text
 build()  BUILD — 이 흐름의 조각이 끼는 자리 (시간순)

 L1676  generateRoutesManifest(...)          두 번들러 공통. routes-manifest 의 뼈대   [03]
 L1779  if (bundler === Bundler.Turbopack)   ← 여기서 갈린다
          Turbopack  turbopackBuild → Rust 가 번들과 **`.nft.json` 까지** 쓴다 ※
          else       webpackBuild → 워커 WPIMPL L171-199
                       getBaseWebpackConfig ×3 (client · server · edge-server)      [01]
                       runCompiler (compiler.ts L39)
                         server 컴파일 안에서 TraceEntryPointsPlugin 이
                         페이지마다 `.nft.json` 1차본을 emit 한다                     [02]
 L1824  (parallelServerBuildTraces 면) server 컴파일 직후 NFT 워커를 띄운다          [02]
 L1950  #region required-server-files        standalone · 어댑터가 쓰는 파일 목록
 L2816  #region NFT — webpack·Rspack 이고 generate 모드가 아니고 아직 안 띄웠으면
          buildTracesPromise = collectBuildTraces(...)   **기다리지 않는다**         [02]
 L2999  #region SSG                          prerender 가 NFT 와 **동시에** 돈다 (webpack·Rspack 만 —
                                             Turbopack 은 buildTracesPromise 가 없다, L2819)
 L4348  await buildTracesPromise             여기서 비로소 기다린다
 L4361  proxy.js → middleware.js 이름 바꾸기 (webpack·Rspack 만, `.nft.json` 안까지 고친다)
 L4406  output: 'export'
 L4431  config.adapterPath 면  handleBuildComplete(...)                             [03]
 L4465  output: 'standalone' 면  writeStandaloneDirectory(...)                      [04]
```

1. [webpack 설정을 조립한다](01_config/README.md) — 2577줄 함수가 컴파일러 셋에 **레이어별 로더 체인**을 깐다. webpack·Rspack 전용.
2. [실행에 필요한 파일을 추적한다](02_trace/README.md) — NFT 가 **두 번** 돈다. 컴파일 중엔 소스를, 컴파일 뒤엔 번들 청크를. webpack·Rspack 전용.
3. [어댑터에 산출물을 넘긴다](03_adapter/README.md) — 1766줄이 `.next/` 를 **출력 목록과 라우팅 표**로 번역해 `onBuildComplete` 에 준다. 두 번들러 공통.
4. [standalone 디렉터리를 만든다](04_standalone/README.md) — `.nft.json` 목록대로 파일을 복사하고 `server.js` 를 **문자열로 써 넣는다**. 두 번들러 공통.

```text
 ★★ 어디까지가 Turbopack 에서도 도는가 — 번들러 분기를 grep 한 결과

                                   webpack·Rspack   Turbopack   근거
 getBaseWebpackConfig              돈다             안 돈다     호출처가 WPIMPL L171·L180·L189
                                                                 (개발 서버 hot-reloader-webpack 제외)
 TraceEntryPointsPlugin            돈다             안 돈다     생성처가 WPCFG L2089-2105 하나
 collectBuildTraces                돈다             안 돈다     BUILD L1848 · L2828, 둘 다 webpack 갈래
 NFT region 의 나머지              돈다             돈다        BUILD L2844-2998 (dataRoutes ·
                                                                 routes-manifest 첫 쓰기 · BUILD_ID)
 generateRoutesManifest            돈다             돈다        BUILD L1676 은 컴파일 전
 getDefineEnv                      돈다             돈다        WPCFG L2065 와 build/swc/index.ts L463
 handleBuildComplete (어댑터)      돈다             돈다        번들러 분기 셋만 (ADBC L649·L2413·L2565)
 writeStandaloneDirectory          돈다             돈다        BUTILS L1223-1469 에 번들러 분기 0

 ★ "webpack 만" 이 아니다 — `bundler !== Bundler.Turbopack` 은 Rspack 도 포함한다.
   getBaseWebpackConfig 안에서도 `isRspack`(WPCFG L393) 으로 갈리는 자리가 여럿이다
   (externals 를 끄고 NextExternalsPlugin 으로 대신 L999 · L2248, 캐시 방식 L2461, 레이어 실험 L2314)
```

## 결과가 쓰이는 곳

```text
 webpack.Configuration ×3  ([01])
      --> runCompiler 가 compiler 를 만든다. 결과는 [빌드] 02 가 말한 .next/server/** 와 매니페스트

 .next/server/**/<entry>.js.nft.json · next-server.js.nft.json · next-minimal-server.js.nft.json  ([02])
      --> [03] 어댑터의 assets, [04] standalone 의 복사 목록.
          그리고 배포 플랫폼이 직접 읽는다 ※ (BUILD L4378-4382 주석이 "providers like Vercel that uses NFT" 라고 적는다)

 onBuildComplete({ routing, outputs, ... })  ([03])
      --> 어댑터 모듈(사용자 또는 플랫폼 코드). routes-manifest 의 prefetchSegmentDataRoutes 를 읽는 곳은 저장소에서 여기 하나다

 .next/standalone/**  (server.js 포함)  ([04])
      --> `node server.js` → startServer → [요청 -> 렌더]
```

## 다루지 않는 것

Turbopack 의 설정·번들·NFT 를 만드는 Rust 쪽(`crates/`, 이 흐름은 `next_server_nft.rs` · `nft_json.rs` 의 인용한 줄만 읽었다), `buildConfiguration`(`build/webpack/config/`)이 붙이는 CSS·이미지 블록, 개별 webpack 플러그인(`FlightClientEntryPlugin` · `ClientReferenceManifestPlugin` · `MiddlewarePlugin` · `BuildManifestPlugin` · `PagesManifestPlugin` 등)과 개별 로더(`next-app-loader` · `next-flight-loader` · `next-swc-loader` 등)의 본문, 개발 서버의 webpack 경로(`server/dev/hot-reloader-webpack.ts`)와 `dev` 갈래 전부, `#region required-server-files`(BUILD L1950-2143)의 파일 목록 조립 세부, `output: 'export'` 의 `writeFullyStaticExport`, `next.config` 의 `adapterPath` 를 불러 `modifyConfig` 를 적용하는 `applyModifyConfig`(`server/config.ts` L1721-1747)의 호출 시점, `createEntrypoints`(`build/entries.ts`)의 엔트리 구성, `@vercel/nft` 자체의 추적 알고리즘은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 webpack 설정을 조립한다](01_config/README.md)
- [02 실행에 필요한 파일을 추적한다](02_trace/README.md)
- [03 어댑터에 산출물을 넘긴다](03_adapter/README.md)
- [04 standalone 디렉터리를 만든다](04_standalone/README.md)
