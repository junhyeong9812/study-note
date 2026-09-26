# `next build` 가 산출물을 만들기까지

상위: [Next.js 아키텍처 지도](../../README.md)

지금까지의 흐름은 전부 **요청이 들어온 뒤**의 이야기였다. 이 흐름은 그 전에 한 번 도는 것 — `next build` 가 소스를 읽어 `.next/` 를 채우는 길이다. 진입 함수 `build()` 는 혼자 **3558줄**(L1042-4599)이고, 이 지도에서 다룬 함수 중 가장 길다(`createAppPageEntrypoint` 2082줄, [정적 응답]의 `prerenderToStream` 1996줄보다 길다). **요약 흐름**이다 — 단계의 순서와 각 단계가 다음 단계에 넘기는 것, 그리고 다른 흐름과 만나는 자리만 따라간다.

만나는 흐름 — [정적 응답](../prerender-to-stream/README.md) · [App Router](../app-render/README.md) · [트리 조립](../tree-assembly/README.md) · [페이지 아닌 요청](../non-page/README.md) · [동적 판별](../dynamic-rendering/README.md) · [`'use cache'`](../use-cache/README.md) · [메타데이터](../metadata/README.md). 어디서 만나는지는 각 하위 문서의 첫머리에 적었다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `BUILD` = `build/index.ts`(4636줄), `NBCLI` = `cli/next-build.ts`(164줄), `WPIMPL` = `build/webpack-build/impl.ts`(460줄), `TPIMPL` = `build/turbopack-build/impl.ts`(389줄), `SPAPP` = `build/static-paths/app.ts`(1180줄), `EXPORT` = `export/index.ts`(1121줄), `EXWORKER` = `export/worker.ts`(654줄), `EXAPPPAGE` = `export/routes/app-page.ts`(300줄), `EXAPPROUTE` = `export/routes/app-route.ts`(176줄), `WPBUILD` = `build/webpack-build/index.ts`(163줄), `TPBUILD` = `build/turbopack-build/index.ts`(95줄), `APPR` = `server/app-render/app-render.tsx`(10598줄).

## 위치

`packages/next` / `src/build` / `index.ts` L1042-L4599 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/index.ts#L1042-L4599))

CLI 는 인자를 풀어 이 함수를 부르기만 한다 — `packages/next` / `src/cli` / `next-build.ts` L123-L136 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/cli/next-build.ts#L123-L136))

## 실제 코드

시그니처가 이미 두 가지를 말한다.

```ts
// index.ts L1042-L1055
export default async function build(
  dir: string,
  experimentalAnalyze = false,
  reactProductionProfiling = false,
  debugOutput = false,
  debugPrerender = false,
  noMangling = false,
  appDirOnly = false,
  bundler = Bundler.Turbopack,
  experimentalBuildMode: 'default' | 'compile' | 'generate' | 'generate-env',
  traceUploadUrl: string | undefined,
  debugBuildPathsPatterns: string[] | undefined,
  enabledFeatures: Record<string, unknown> = {}
): Promise<void> {
```

```text
 ★★ `bundler = Bundler.Turbopack` — **기본값이 Turbopack** 이다
   CLI 쪽도 같다. lib/bundler.ts L99-102
     // The default is turbopack when nothing is configured.
     if (bundlerFlags.size === 0) { process.env.TURBOPACK = 'auto'; return Bundler.Turbopack }
   webpack 은 `--webpack` 플래그(L68-70)나 `IS_WEBPACK_TEST` 환경변수(L72-77)가 있어야 탄다
 ★ 그리고 번들러는 **설정을 읽은 뒤 한 번 더 바뀔 수 있다** (BUILD L1160-1161)
     // Reading the config can modify environment variables that influence the bundler selection.
     bundler = finalizeBundlerFromConfig(bundler)
   바뀌는 방향은 하나다 — 설정이 `NEXT_RSPACK` 을 세우면 Rspack (lib/bundler.ts L121-132)
 ★ 컴파일 갈림(L1779)은 `bundler === Bundler.Turbopack` 이냐 아니냐 **둘**이다.
   Rspack 은 webpack 쪽 else 로 가고, 워커가 `NEXT_RSPACK` 을 보고 고른다 (WPIMPL L429)

 ★ `experimentalBuildMode` 가 넷이다 — 'default' | 'compile' | 'generate' | 'generate-env'
   compile  = 번들 뒤 **워커 질의를 건너뛰고** build() 끝까지 간다 (멈추지 않는다)
              Collect data 는 돌되 워커 질의만 건너뛰고(L2214-2220), NFT·BUILD_ID(L2899)·
              prerender-manifest(L4312) 쓰기도 일어난다. 끝의 L4398-4404 가
              "generate 를 이어 돌려라" 고 안내한다
   generate = 번들을 건너뛰고 뒤만 돈다  (L1778 `if (!isGenerateMode)` 가 컴파일 전체를 감싼다)
   => 한 빌드를 **두 번의 프로세스로 쪼갤 수 있게** 만든 자리다
```

## 동작 흐름

```text
 ★★★ 단계를 나누는 뼈대가 **소스 안에 이미 있다** — `// #region` 주석 다섯 개

   grep -n "#region\|#endregion" build/index.ts  (전부 build() 안이다)

   L1094-1764   (region 없음)            설정·라우트 발견        [01]
   L1765-1939   #region Compile          번들러                  [02]
   L1950-2143   #region required-server-files
   L2144-2815   #region Collect data     페이지마다 정적인가      [03]
   L2816-2998   #region NFT              파일 추적
   L2999-4321   #region SSG              prerender + 매니페스트   [04]
   L4323-4554   (region 없음)            output 모드·어댑터·트리 출력
   L4555-4598   catch / finally          워커 정리·트레이스 flush
```

```text
 ★★ 트레이스 span 은 **뼈대로 반쯤만 쓸 수 있다**

   build() 안의 traceChild( 호출 32개 (awk 'NR>=1042 && NR<=4599' | grep -c "traceChild(")
   루트는 L1081 trace('next-build'). 이름을 소스 순서대로 뽑으면

   [01] load-dotenv · load-next-config · (generate-env 모드면 inline-static-env)
        load-custom-routes · create-dist-dir · clean · discover-routes
        create-root-mapping · generate-route-types · public-dir-conflict-check
        generate-routes-manifest
   [02] ── **build() 안에는 span 이 없다** ──
        run-webpack (webpack-build/index.ts L139) · run-turbopack (turbopack-build/index.ts L85)
        두 도우미가 자기 안에서 연다. 병렬 모드면 여기서 collect-build-traces (L1845)
   (required-server-files) generate-required-server-files
   [03] static-check > check-static-error-page · check-page > is-page-static
        collect-build-traces (L2824, NFT)  ·  write-routes-manifest (L2877)
        (generate 모드 + webpack 이면 inline-static-env L2940)
   [04] static-generation > move-exported-app-not-found- · move-exported-app-global-error-
        write-routes-manifest (L4161, **두 번째**)
   끝   verify-partytown-setup · output-export-full-static-export
        adapter-handle-build-complete · output-standalone
        print-custom-routes · print-tree-view · write-route-bundle-stats · telemetry-flush

 => 가장 무거운 단계(번들)가 build() 의 span 목록에서 **비어 있다.** region 주석이 그 구멍을 메운다
 ★ `routes-manifest.json` 은 두 번 쓰인다 — L2875 주석 "We need to write the manifest
   with rewrites before build", L4147-4148 주석 "As we may have modified the dynamicRoutes,
   we need to sort the dynamic routes by page." 뒤에 L4161 에서 다시 쓴다
```

```text
 단계 사이에 넘어가는 것 — **대부분 디스크 위의 파일이다**

 [01] NextBuildContext (모듈 전역 객체) 에 mappedPages · mappedAppPages · buildId ·
      encryptionKey · previewProps · rewrites 를 채운다
        │  워커로 갈 때는 직렬화된다 — Turbopack 은 nextBuildSpan · config 를 빼고,
        │  webpack 은 nextBuildSpan 만 뺀다 (WPBUILD L38 — 워커가 config.distDir 를 읽는다, WPIMPL L410)
        │  (webpack-build/index.ts L38 · turbopack-build/index.ts L33-38)
        │  ★ config 는 직렬화가 안 돼서 **워커가 다시 읽는다** (WPIMPL L423 · TPIMPL L334 — 둘 다 loadConfig 호출 행)
        v
 [02] 번들러가 .next/server/** 와 매니페스트 파일들을 쓴다
        │  pages-manifest · build-manifest · app-paths-manifest ·
        │  middleware-manifest · server-reference-manifest ...
        v
 [03] 그 매니페스트를 **파일에서 다시 읽는다** (BUILD L2171-2179 · L2291-2303)
      그리고 컴파일된 모듈을 **require 해서** 정적 여부를 묻는다 (utils.ts L817 loadComponents)
        │  pageInfos · staticPaths · ssgPages · appDefaultConfigs (메모리)
        v
 [04] exportPathMap 으로 번역해 export 워커에 넘긴다
      워커가 .next/server/app/*.html · .rsc · .meta · .segments/ 를 **직접 쓴다**
      돌아온 결과로 prerender-manifest · routes-manifest 를 완성한다
```

1. [설정을 읽고 라우트를 찾는다](01_discover/README.md) — 번들러보다 **먼저** 라우트 목록을 만든다. Turbopack 은 그것을 거의 안 쓴다.
2. [번들러를 돌린다](02_compile/README.md) — webpack 은 server → edge → client 순서가 **강제**이고, Turbopack 은 호출 하나다.
3. [페이지마다 정적인지 묻는다](03_collect/README.md) — 컴파일된 모듈을 워커에서 불러 `generateStaticParams` 까지 돌린다.
4. [prerender 하고 매니페스트를 쓴다](04_generate/README.md) — 가짜 요청으로 [App Router] 를 부르고, 실패는 `revalidate: 0` 이 되거나 빌드를 세운다.

```text
 ★★ 두 번들러가 갈리는 자리는 [02] 하나가 아니다

   grep -n "Bundler\." build/index.ts  → build() 안에 14번. 기본값(L1050)과
   텔레메트리(L1327 · L4594)를 빼면 **분기 열한 자리**다

   L1203  generate-env 모드 — Turbopack 이면 "not needed" 경고 후 exit(0)
   L1581  app/pages 충돌 검사 — webpack 만. 주석 "Turbopack already handles conflicting
          app and page routes."
   L1779  **컴파일 자체**                                          [02]
   L2010 · L2046 · L2078  required-server-files 목록 — react-loadable · dynamic-css ·
          edge instrumentation 파일을 webpack 일 때만 넣는다
   L2792  client middleware manifest JS — Turbopack 만 여기서 쓴다
   L2819  NFT(collect-build-traces) — `bundler !== Turbopack` (webpack · Rspack)
   L2936  generate 모드의 inline-static-env — webpack 만
   L4361  proxy.js → middleware.js 이름 바꾸기 — webpack 만
   L4517  route bundle stats — Turbopack 만

 => #region SSG(L2999-4321, [04])에는 번들러 분기가 **하나도 없다.**
    [03]의 Collect data region 에는 L2792 한 자리 — middleware 매처 JS 파일을 쓰는 곳 — 뿐이고,
    정적 판별(isPageStatic) 호출 자체는 두 번들러 공통이다
 => [03][04]에는 번들러 분기가 거의 없다 — 그러나 **산출물이 같은 모양은 아니다.**
    build() 스스로 번들러별 차이를 적는다 — react-loadable 매니페스트는 webpack 만(L2010-2018),
    L2066-2078 주석 "Turbopack generates this chunk with a hashed name".
    prerender 런타임도 `process.env.TURBOPACK` 으로 갈린다 (route-modules/app-page/module.compiled.js)
```

## 결과가 쓰이는 곳

```text
 .next/server/app/**  (.html · .rsc · .meta · .body · .segments/*.segment.rsc)
      --> [응답 나가기]의 응답 캐시가 정적 응답으로 읽는다 ※ (읽는 쪽은 이 흐름에서 확인하지 않았다)

 prerender-manifest.json  (routes · dynamicRoutes · notFoundRoutes · preview)
      --> 런타임 서버가 "이 경로는 미리 만들어졌는가 / fallback 은 무엇인가" 를 묻는다 ※

 routes-manifest.json  (rewrites · dynamicRoutes · prefetchSegmentDataRoutes)
      --> [요청 -> 렌더]의 라우트 해석 ※

 required-server-files.json · standalone 디렉터리 · 어댑터 onBuildComplete
      --> 배포 플랫폼
```

## 다루지 않는 것

`#region required-server-files`(L1950-2143)의 파일 목록 조립, `#region NFT`(L2816-2998)의 `collectBuildTraces`(`build/collect-build-traces.ts`)와 `.nft.json`, 타입 검사 `startTypeChecking`(L1692 · L1946)과 `generate-route-types`(L1537-1578)가 쓰는 `.next/types/`, `generateRoutesManifest`(`build/generate-routes-manifest.ts`)의 본문, `createClientRouterFilter`(L1699-1711), `output: 'export'` 의 두 번째 `exportApp` 호출(`writeFullyStaticExport` L989-1019 · L4406-4426), `output: 'standalone'`(`writeStandaloneDirectory` L4465-4484), 어댑터(`handleBuildComplete` L4431-4463, `build/adapter/`), `printTreeView`(L4505)의 기호 규칙, `experimental.lockDistDir`(L1264-1271), 텔레메트리 이벤트 전부, `generate` / `compile` / `generate-env` 모드의 세부, Rspack 경로(`finalizeBundlerFromConfig` 이후), Pages Router 의 `getStaticProps` / `getStaticPaths` 쪽 갈래(`build/static-paths/pages.ts` 230줄 · `export/routes/pages.ts`), `next.config` 를 읽는 `loadConfig` 자체, 그리고 **Turbopack 내부(Rust, `crates/`)** 는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 설정을 읽고 라우트를 찾는다](01_discover/README.md)
- [02 번들러를 돌린다](02_compile/README.md)
- [03 페이지마다 정적인지 묻는다](03_collect/README.md)
- [04 prerender 하고 매니페스트를 쓴다](04_generate/README.md)
