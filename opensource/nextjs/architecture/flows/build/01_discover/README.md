# 01 설정을 읽고 라우트를 찾는다

상위: [`next build` 가 산출물을 만들기까지](../README.md)

`build()` 의 앞 671줄(L1094-1764)은 **번들러를 부르기 전**의 일이다. 설정을 읽고, 빌드 ID 와 암호화 키를 만들고, `app/` · `pages/` 를 훑어 라우트 목록을 만든다. 이 목록이 webpack 에게는 엔트리의 원천이고, 두 번들러 모두에게는 [03]이 페이지를 하나씩 도는 목록이다.

## 위치

`packages/next` / `src/build` / `index.ts` L1094-L1764 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/index.ts#L1094-L1764))

## 실제 코드

라우트 발견은 도우미 하나에 맡긴다. 그런데 **결과가 입력을 고친다.**

```ts
// index.ts L1447-L1464
      const discovery = await nextBuildSpan
        .traceChild('discover-routes')
        .traceAsyncFn(() =>
          discoverRoutes({
            appDir,
            pagesDir,
            pageExtensions: config.pageExtensions,
            isDev: false,
            baseDir: dir,
            isSrcDir,
            appDirOnly,
            debugBuildPaths,
          })
        )

      // Update appDirOnly from discovery (may have changed if no pages found)
      appDirOnly = discovery.appDirOnly
      NextBuildContext.appDirOnly = appDirOnly
```

```text
 ★★ `appDirOnly` 가 발견 **뒤에** 바뀐다
   route-discovery.ts L466-470 — pages 를 매핑해 보니 사용자 페이지가 0개면
     // Update appDirOnly if no user page routes were found, so the
     // subsequent app mapping can emit the global error entry.
     appDirOnly = true
 => "pages/ 디렉터리가 있다" 와 "pages 라우트가 있다" 는 다르다. 빈 pages/ 는 없는 것으로 친다
 ★ 그 전에 BUILD L1295-1297 도 같은 일을 한 번 한다 — `pagesDir` 가 없으면 appDirOnly = true

 discoverRoutes (route-discovery.ts L405-546) 가 돌려주는 것
   appRoutes · appRouteHandlers · layoutRoutes · slots      라우트 타입 생성용
   pageRoutes · pageApiRoutes
   mappedAppPages · mappedAppLayouts · mappedPages          **이후 단계가 쓰는 것**
   pagesPaths · appDirOnly
 ★ 테스트용 탈출구가 둘 있다 — `NEXT_PRIVATE_PAGE_PATHS`(L454) · `NEXT_PRIVATE_APP_PATHS`(L491)
   환경변수가 있으면 파일 시스템을 안 훑고 그 JSON 을 쓴다
```

## 동작 흐름

```text
 build()  BUILD L1094  nextBuildSpan.traceAsyncFn(async () => {

 L1097  load-dotenv          loadEnvConfig(dir)            ← next.config 보다 **먼저**
          주석 L1095 - "attempt to load global env values so they are available in next.config.js"
 L1112  load-next-config     loadConfig(PHASE_PRODUCTION_BUILD, dir, {...})
 L1161  bundler = finalizeBundlerFromConfig(bundler)
 L1165  hasCustomExportOutput(config) 이면  configOutDir = config.distDir;  config.distDir = '.next'
          조건 = output: 'export' 이고 distDir 가 '.next' 가 아닐 때 (export/utils.ts L3-14)
          ★ 그 경우 사용자가 적은 distDir 는 **최종 export 폴더**로 옮겨 가고 빌드 자체는 .next 에서 한다
            주석 export/utils.ts L6-8 "when "output: export" is configured, "next build" does both
            steps. So the user-configured distDir is actually the outDir."
 L1184  installBindings(...)   SWC 네이티브 바인딩. 주석 L1183 "so we can have synchronous access later"
 L1194  buildId = getBuildId(...)                         (L1021-1040)
 L1202  'generate-env' 모드면 inline-static-env 후 **여기서 exit(0)**
 L1229  load-custom-routes   headers · rewrites · redirects
 L1244  create-dist-dir      EPERM 이면 false → L1258 "Build directory is not writeable"
 L1273  clean                cleanDistDir && !generate 이면 .next 를 지운다
                             **cache · dev · lock · trace 로 시작하는 것은 남긴다** (L1279)
 L1285  findPagesDir(dir)    → appType = 'hybrid' | 'pages' | 'app'
 L1309  encryptionKey = generateEncryptionKeyBase64({ isBuild: true, distDir })
          주석 L1307-1308 - "used to encrypt cross boundary values"
 L1358  appDir && 'exportPathMap' in config  => throw   ← [04]에서 다시 만난다
 L1387  루트의 middleware · proxy · instrumentation 파일을 찾는다
 L1417    middleware 와 proxy 가 **둘 다** 있으면 => throw
 L1427    middleware 만 있으면 deprecated 경고 (`Please use "${PROXY_FILENAME}" instead`)
 L1441  previewProps = generatePreviewKeys(...)
 L1447  discover-routes      (위 실제 코드)
 L1470  create-root-mapping  루트 파일(middleware 등)을 PAGE_TYPES.ROOT 로 매핑
 L1498  같은 경로가 app 과 pages 에 **둘 다** 있으면 conflictingAppPagePaths 에 모은다
 L1523  validateAppPaths(appPaths)
 L1526  rewrites.beforeFiles.push(...generateInterceptionRoutesRewrites(appPaths, basePath))
          ★ 가로채기 라우트(`(.)` 등)는 **beforeFiles rewrite 로 모델링된다** (주석 L1525)
 L1537  generate-route-types  .next/types/routes.d.ts · validator.ts · cache-life.d.ts · root-params.d.ts
 L1581  webpack 이면 conflictingAppPagePaths 가 있을 때 => throw
 L1618  public-dir-conflict-check  public/ 파일과 페이지 경로가 겹치면 => throw
 L1673  generate-routes-manifest   routesManifest · dynamicRoutes · sourcePages  (**메모리에만**)
 L1691  !appDir && !compile 이면 여기서 타입 검사  ← pages 전용 프로젝트만
 L1715  .next/package.json 에 {"type": "commonjs"}
```

```text
 ★★ 빌드 ID 는 deploymentId 가 있으면 **상수**다 (BUILD L1030-1034)

   if (config.deploymentId) {
     // Skew protection is enabled and NEXT_NAV_DEPLOYMENT_ID_HEADER will be used instead. Set a
     // constant but "random" string because various tools perform `.replace(escapedBuildId, ....)`
     // which would fail if this were something like "build-id" instead.
     return 'build-TfctsWXpff2fKS'
   }

 => 배포 간 구분을 deploymentId 가 맡으면 buildId 는 역할을 내려놓는다
 => 그래도 "random" 처럼 보이는 문자열이어야 한다 — 외부 도구가 buildId 를 **문자열 치환**하기 때문이다
 ★ generate 모드면 새로 만들지 않고 이전 빌드의 BUILD_ID 파일을 읽는다 (L1027-1029)
```

```text
 ★★ 라우트 목록을 만들지만 **Turbopack 은 그 매핑으로 엔트리를 만들지 않는다**

   NextBuildContext.mappedPages · mappedAppPages · mappedRootPaths  (L1468-1482)
     --> webpack  : WPIMPL L102-117 createEntrypoints({ pages: mappedPages, appPaths: mappedAppPages, ... })
     --> Turbopack: turbopack-build/ 에서 mappedPages · mappedAppPages 를 grep 하면 **0건**
                    TPIMPL L185 project.writeAllEntrypointsToDisk(appDirOnly) 가 스스로 찾는다 ※
                    (※ Rust 쪽이 라우트를 다시 훑는다는 것은 추론이다. crates/ 는 읽지 않았다)
   L1580 주석 - "Turbopack already handles conflicting app and page routes."

 => 그래도 발견 결과는 버려지지 않는다. [03]이 `pageKeys` 와 `mappedAppPages` 로
    페이지를 하나씩 돈다 (BUILD L2324-2342 · L2368-2384) — 두 번들러 공통이다
 ★ 타입 검사 위치가 프로젝트 모양으로 갈린다 — pages 전용이면 컴파일 **전**(L1691),
   app 이 있으면 컴파일 **뒤**(L1942). 주석 L1941 "For app directory, we run type checking after build."
```

## 결과가 쓰이는 곳

```text
 NextBuildContext (build-context.ts 의 모듈 전역)
      --> [02]의 워커로 직렬화돼 넘어간다. webpack 이 엔트리를 만든다

 pageKeys { pages, app }
      --> [03]이 페이지마다 check-page span 을 연다

 routesManifest (메모리)
      --> NFT region 의 L2877 에서 처음 파일이 되고, [04] 뒤 L4161 에서 한 번 더 쓰인다

 rewrites.beforeFiles (가로채기 라우트 포함)
      --> routes-manifest 에 실린다 → [요청 -> 렌더]의 라우트 해석 ※

 encryptionKey · previewProps · buildId
      --> webpack 에서는 define 값, Turbopack 에서는 createProject 의 ProjectOptions 필드(TPIMPL L109-111)와
          prerender-manifest 의 preview 로 간다 (BUILD L2958)
```

## 다루지 않는 것

`loadConfig` 와 `next.config` 검증, `resolveBuildPaths`(L1136)와 `--debug-build-paths` 필터, `generateBuildId`(`build/generate-build-id.ts`) 의 기본 규칙, `generateEncryptionKeyBase64` · `generatePreviewKeys` 의 키 생성과 저장, `createPagesMapping` · `collectAppFiles` · `processAppRoutes` · `extractSlotsFromRoutes` 의 세부, `validateAppPaths`(`build/validate-app-paths.ts`)의 규칙, `generateInterceptionRoutesRewrites` 가 만드는 rewrite 의 모양, `createRouteTypesManifest` 와 `.next/types/` 파일 넷의 내용, `generateRoutesManifest`(`build/generate-routes-manifest.ts`)의 본문, 텔레메트리(`eventCliSession` · `eventNextPlugins` · `eventSwcPlugins`), `Lockfile` 과 `recursiveDeleteSyncWithAsyncRetries` 는 이 문서의 범위 밖이다.
