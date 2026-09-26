# 04 standalone 디렉터리를 만든다

상위: [빌드가 번들러 설정과 배포 산출물을 만들기까지](../README.md)

**두 번들러 모두에서 돈다** — `output: 'standalone'` 일 때만이다(환경변수 `NEXT_PRIVATE_STANDALONE` 으로도 켜진다, `server/config-shared.ts` L2109). `writeStandaloneDirectory`(BUILD L796-902)가 `copyTracedFiles`(BUTILS L1223-1469, 247줄)를 부르고 나머지 파일을 덧붙인다. 하는 일은 셋이다 — `.nft.json` 목록대로 파일을 복사하고, 빌드 산출물 일부를 통째로 복사하고, 실행 입구 `server.js` 를 **템플릿 문자열로 써 넣는다.** 복사 목록의 근거는 [02]가(webpack·Rspack) 또는 Turbopack 이 쓴 `.nft.json` 이다.

## 위치

`packages/next` / `src/build` / `index.ts` L796-L902 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/index.ts#L796-L902))

`packages/next` / `src/build` / `utils.ts` L1223-L1469 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/utils.ts#L1223-L1469))

## 실제 코드

edge 함수 파일을 복사하는 도우미가 **자기가 띄운 복사를 기다리지 않는다.**

```ts
// utils.ts L1329-L1345
  async function handleEdgeFunction(page: EdgeFunctionDefinition) {
    async function handleFile(file: string) {
      const originalPath = path.join(distDir, file)
      const fileOutputPath = path.join(
        outputPath,
        path.relative(tracingRoot, distDir),
        file
      )
      await fs.mkdir(path.dirname(fileOutputPath), { recursive: true })
      await fs.copyFile(originalPath, fileOutputPath)
    }
    await Promise.all([
      page.files.map(handleFile),
      page.wasm?.map((file) => handleFile(file.filePath)),
      page.assets?.map((file) => handleFile(file.filePath)),
    ])
  }
```

```text
 ★★★ Promise.all 에 **배열의 배열**이 들어간다 (L1340-1344)

   page.files.map(handleFile)          → Promise[]   (배열 하나)
   page.wasm?.map(...)                 → Promise[] 또는 undefined
   page.assets?.map(...)               → Promise[] 또는 undefined
   await Promise.all([ 배열, 배열, 배열 ])

 => Promise.all 은 원소가 Promise 가 아니면 그 값을 그대로 결과로 쓴다.
    원소가 **배열**이므로 안쪽 copyFile 약속들은 기다려지지 않는다
 => 호출 쪽 L1359 `await Promise.all(edgeFunctionHandlers)` 도 곧바로 풀린다
    복사는 그 뒤에 백그라운드로 끝난다
 => 실패해도 거부가 버려지지는 않는다 — build/index.ts L12 가 불러오는 전역 리스너
    (lib/setup-exception-listeners.ts L6-9)가 unhandledRejection 에서 **exit 1** 로 빌드를 끝낸다.
    다만 에러가 standalone 단계와 끊긴 채, 그때 돌던 다른 작업 도중에 나타난다
 ※ 호출 쪽이 뒤에서 page·app handleTraceFiles 와 writeStandaloneDirectory 의 나머지(L827 · L869 · L885)를
   전부 await 하므로, 정상 경로에서 파일이 실제로 빠질 가능성은 낮아 보인다. 실행으로는 확인하지 않았다
 ★ edge 페이지의 엔트리 파일은 L885 의 `.next/server/app` 통째 복사와 **같은 목적지**에
   순서 없이 동시에 쓰일 수 있다 (내용은 같다)
 ★ 대조 — [03] 어댑터의 handleEdgeFunction 은 await 가 없어서 기다리지 않아도 안전했다.
   여기서는 await 가 **안쪽에** 있어서 문제가 된다
```

## 동작 흐름

```text
 writeStandaloneDirectory(...)   BUILD L796  ← BUILD L4469, 어댑터 **뒤**
 L811   span 'write-standalone-directory'
 L813   copyTracedFiles(requiredServerFiles.appDir, distDir, pageKeys.pages, denormalizedAppPages,
                        outputFileTracingRoot, requiredServerFiles.config, ...)      (아래)
 L827   requiredServerFiles.files + required-server-files.json + (.env · .env.production)
          각각 → standalone/<tracingRoot 기준 상대 경로>
 L853   node middleware 면 .next/server/middleware.js 복사
 L869   .next/server/pages 를 **통째로** recursiveCopy
 L885   app 디렉터리가 있으면 .next/server/app 을 **통째로** recursiveCopy
          (여기 prerender 가 쓴 .html · .rsc · .meta · .segments/ 가 들어 있다 — [빌드] 04)

 copyTracedFiles(...)   BUTILS L1223
 L1235  outputPath = .next/standalone
 L1238  fs.rm(outputPath, { recursive: true, force: true })     ← **먼저 지운다**
 L1241  nextConfig = { ...serverConfig, distDir: `./${relative(dir, distDir)}` }
 L1246  distDir/../package.json 을 읽어 type: module 인지 보고, standalone 에 **그대로** 쓴다
          실패하면 catch {} 로 **조용히** 넘어간다 (L1263)
 L1266  handleTraceFiles(traceFilePath)  — `.nft.json` 을 읽어 files 를 복사
 L1272    Sema(10) — 한 번에 10개씩
 L1289    심볼릭 링크면 링크로 다시 만든다 (Windows 에서 EPERM 이면 junction 으로)
 L1349  edge 함수 — middleware-manifest 의 middleware · functions  (위 실제 코드)
 L1361  pageKeys (Pages) — edge 면 건너뛰고, staticPages 면 건너뛰고
          `.next/server/pages/<page>.js.nft.json` 을 handleTraceFiles. 실패는 **경고만**
          (ENOENT 인 /404 · /500 은 경고도 안 한다, L1379)
 L1385  node middleware 면 middleware.js.nft.json          ← 실패하면 **던진다**
 L1391  appPageKeys — edge 면 건너뛰고 `.next/server/app/<page>.js.nft.json`. 실패는 경고만
 L1404  instrumentation 이 있으면 instrumentation.js.nft.json  ← 던진다
 L1410  next-server.js.nft.json                              ← **조건 없이**, 던진다
 L1418  standalone/<tracingRoot 기준 앱 경로>/server.js 를 writeFile        (아래 ★★★)
```

```text
 ★★★ server.js 는 **설정을 통째로 박아 넣은** 문자열이다 (BUTILS L1418-1467)

   L1441  const nextConfig = ${JSON.stringify(nextConfig)}
   L1443  process.env.__NEXT_PRIVATE_STANDALONE_CONFIG = JSON.stringify(nextConfig)
   L1445  require('next')
   L1446  const { startServer } = require('next/dist/server/lib/start-server')
   L1456  startServer({ dir, isDev: false, config: nextConfig, hostname, port: currentPort,
                       allowRetry: false, keepAliveTimeout })
   그 앞에서 NODE_ENV = 'production', process.chdir(__dirname),
     PORT(기본 3000) · HOSTNAME(기본 0.0.0.0) · KEEP_ALIVE_TIMEOUT 을 환경변수에서 읽는다
   package.json 이 type: module 이면 머리말만 ESM 판으로 바뀐다 (L1420-1428)

 받는 쪽 — server/config.ts L1895-1910
   if (process.env.__NEXT_PRIVATE_STANDALONE_CONFIG) {
     // we don't apply assignDefaults or modifyConfig here as it
     // has already been applied
     ... return [standaloneConfig, meta]
   }
 => 배포된 서버는 next.config 를 **읽지 않는다.** 빌드 때 확정한 값이 그대로 쓰인다
 => 그래서 [03] 어댑터의 modifyConfig 도 standalone 서버 시작 때는 다시 돌지 않는다
 ★ nextConfig 의 원천은 requiredServerFiles.config 다 — BUILD L1968-1996 이
   getNextConfigRuntime(config) 에서 configFile 을 지우고, Vercel(hasNextSupport)이면
   compress: false, cacheHandler 경로를 distDir 기준 상대 경로로 바꿔 만든 것이다
 ★ loadConfig 는 그 앞에서 loadWebpackHook(require 를 번들된 webpack 으로 돌리는 훅,
   server/config-utils.ts L3-)을 거는데, standalone 이면 그 실패를 **삼킨다** (server/config.ts L1883-1893)
   주석 L1887-1888 "this can fail in standalone mode as the files aren't traced/included"
 => startServer 부터는 [페이지 아닌 요청]·[요청 -> 렌더]가 다룬 서버 그대로다
```

```text
 ★★ 디렉터리 모양이 **추적 루트 기준**이다

   모든 대상 경로 = path.join(outputPath, path.relative(tracingRoot, 원본))
   tracingRoot = outputFileTracingRoot — 없으면 turbopack.root, 그것도 없으면 repoRoot
     (NEXT_PRIVATE_OUTPUT_TRACE_ROOT 환경변수, 없으면 lockfile 탐색 — server/config.ts L1161-1193 · L1176)
 => 모노레포에서 앱이 apps/web 에 있으면
      .next/standalone/apps/web/server.js
      .next/standalone/apps/web/.next/server/...
      .next/standalone/node_modules/...    (루트에서 hoist 된 패키지)
    처럼 **저장소 모양을 그대로** 재현한다 ※ (예시 경로는 코드의 relative 계산에서 내가 풀어 쓴 것이다)
 ★ L1246 의 package.json 경로는 `distDir/../package.json` 이다.
   distDir 가 앱 바로 아래 한 단계(.next)가 아니면 다른 파일을 읽거나 못 읽는다 — 못 읽으면 catch {} ※
```

```text
 ★★ 복사하지 **않는** 것

   writeStandaloneDirectory · copyTracedFiles 어디에도 .next/static 전체나 public/ 을 복사하는 코드가 없다
     (BUILD L796-902 · BUTILS L1223-1469 전체를 읽었다)
   예외 하나 — experimental.optimizeCss 면 .next/static/**/*.css 가 requiredServerFiles.files 에
     들어가서(BUILD L2085-2109) L827 루프로 복사된다
 => 브라우저가 받는 JS·CSS 청크와 public 파일은 standalone 밖에서 따로 옮겨야 한다 ※
    (그것을 안내하는 문구는 이 두 함수에 없다)

   .env 파일은 **`.env` 와 `.env.production` 둘만** 복사한다 (BUILD L833-838)
 => `.env.local` · `.env.production.local` 은 standalone 에 들어가지 않는다
```

```text
 ★★ standalone 이면 [02]의 추적 대상 자체가 달라진다 (CBT)

   L198-204  serverEntries 에 start-server · next · require-hook 을 **추가**
   L225      jest-worker 를 무시하지 **않는다** (standalone 이 아니면 무시)
   L246      TRACE_IGNORES(next/dist/server/next.js · next/dist/bin/next)도 적용하지 **않는다**
   L292-303  jest-worker 의 processChild · threadChild 를 직접 목록에 넣는다
 => server.js 가 require('next') 와 start-server 를 부르므로 그 파일들이 next-server.js.nft.json 에
    들어가야 한다 ※ (CBT L137-138 주석은 "the extra IPC server and worker files" 라고만 적는다)
 ★ Turbopack 쪽도 같은 사정을 적는다 — next_server_nft.rs L86-89
   "`copyTracedFiles` reads `next-server.js.nft.json` unconditionally whenever standalone
    output is requested (adapter or not), so suppressing the pair crashes the build"
```

## 결과가 쓰이는 곳

```text
 .next/standalone/<앱 경로>/server.js
      --> `node server.js` → startServer (server/lib/start-server.ts) → [요청 -> 렌더]

 .next/standalone/**/node_modules/**  ·  .next/standalone/<앱 경로>/.next/server/**
      --> 서버 프로세스가 require 하는 번들·외부 패키지·매니페스트

 .next/standalone/<앱 경로>/.next/required-server-files.json
      --> 런타임이 읽는 설정·파일 목록 ※ (읽는 쪽은 이 흐름에서 확인하지 않았다)
```

## 다루지 않는 것

`#region required-server-files`(BUILD L1950-2143)가 `files` 목록을 고르는 기준(번들러별 매니페스트 차이 포함), `getNextConfigRuntime` 이 거르는 설정 키, `recursiveCopy`(`lib/recursive-copy.ts`)의 동시성, `startServer` 이후의 서버 동작, `loadedEnvFiles` 를 만드는 `loadEnvConfig`, `experimental.outputStandalone` 을 `output: 'standalone'` 으로 옮기는 설정 이관(`server/config.ts` L941-948), Docker 등 배포 환경에서의 사용법, 그리고 standalone 과 어댑터가 함께 켜졌을 때 Turbopack 이 `.nft.json` 을 고르는 Rust 쪽 세부는 이 문서의 범위 밖이다.
