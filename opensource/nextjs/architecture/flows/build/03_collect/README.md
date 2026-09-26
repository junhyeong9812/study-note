# 03 페이지마다 정적인지 묻는다

상위: [`next build` 가 산출물을 만들기까지](../README.md)

`#region Collect data`(L2144-2815)는 빌드 로그의 "Collecting page data" 다. 페이지 하나마다 **[02]가 만든 모듈을 워커에서 require** 해 세그먼트 설정을 읽고, 동적 라우트면 `generateStaticParams` 를 실제로 호출한다. 여기서 정해진 `staticPaths` 가 [04]가 prerender 할 경로 목록이 된다. 렌더는 아직 하지 않는다.

만나는 흐름 — `generateStaticParams` 가 도는 `'generate-static-params'` 스토어를 [동적 판별 01](../../dynamic-rendering/01_mark/README.md)과 [동적 API](../../request-apis/README.md)가 각자 다르게 받는다.

## 위치

`packages/next` / `src/build` / `index.ts` L2144-L2815 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/build/index.ts#L2144-L2815))

## 실제 코드

동적 라우트의 fallback 모드는 이 몇 줄로 정해진다.

```ts
// app.ts L1007-L1020
  const dynamicParams = segments.every(
    (segment) => segment.config?.dynamicParams !== false
  )

  const supportsRoutePreGeneration =
    hadAllParamsGenerated || !process.env.__NEXT_DEV_SERVER

  const fallbackMode = dynamicParams
    ? supportsRoutePreGeneration
      ? isRoutePPREnabled
        ? FallbackMode.PRERENDER
        : FallbackMode.BLOCKING_STATIC_RENDER
      : undefined
    : FallbackMode.NOT_FOUND
```

```text
 dynamicParams (모든 세그먼트가 false 가 아닐 때만 true)
   true  + 파라미터가 다 채워졌다(또는 개발 서버가 아니다)
           + PPR 이면  PRERENDER                ← 셸을 미리 만들어 둔다
           + 아니면    BLOCKING_STATIC_RENDER    ← 요청 때 만들고 기다리게 한다
   true  + 다 못 채웠고 개발 서버면  undefined
   false                              NOT_FOUND  ← 목록 밖이면 404

 ★★ `supportsRoutePreGeneration = hadAllParamsGenerated || !process.env.__NEXT_DEV_SERVER`
   => **빌드에서는 언제나 true** 다. 앞 항은 개발 서버에서만 의미가 있다
   (※ 이 파일이 개발 서버에서도 불린다는 뜻이다. 그 호출처는 확인하지 않았다)
 ★ 주석 L1004-1006 - 세그먼트마다 dynamicParams 를 달리 주고 싶지만
   "we need additional information stored/leveraged in the prerender manifest" — 그래서 **하나로 뭉갠다**
```

## 동작 흐름

```text
 BUILD L2147  numberOfWorkers = getNumberOfWorkers(config, totalPageCount)
 L2171  pagesManifest = readManifest(.next/server/pages-manifest.json)    ← [02]의 출력을
 L2172  buildManifest = readManifest(.next/build-manifest.json)             **파일로** 읽는다
 L2177  app-paths-manifest.json 을 읽어 app-path-routes-manifest.json 으로 다시 쓴다
 L2193  staticWorker = createStaticWorker(config, { numberOfWorkers, ... })
 L2201  staticCheckSpan = traceChild('static-check')
 L2214    compile 모드면 **아무것도 안 묻고** 기본값을 돌려준다 (L2215-2220)
 L2226    check-static-error-page — /_error 의 getInitialProps 와 정적 여부
 L2271    /_app 의 getInitialProps · named exports (사용자 pages 가 있을 때만)
 L2291    middleware-manifest.json · server-reference-manifest.json 을 require
 L2324    pageKeys 의 pages + app 을 한 배열로 펴서 Promise.all(...)
 L2343      check-page (페이지마다)
 L2394        staticInfo = getStaticInfoIncludingLayouts(...)   소스 정적 분석
 L2409        hadUnsupportedValue 면 errorFromUnsupportedSegmentConfig() => process.exit(1)
 L2432        middleware-manifest 에 이름이 있으면 pageRuntime = 'edge'
 L2464        workerResult = staticWorker.isPageStatic({...})         ~~> 워커 (아래)
 L2502        app 이면
 L2505          edge 런타임  => isStatic = isSSG = false + 경고 "disables static generation"
 L2524          isRoutePPREnabled  => isSSG = isStatic = true, staticPaths.set(path, [])
 L2531          prerenderedRoutes 가 있으면 staticPaths.set(path, prerenderedRoutes)
 L2543          appConfig.revalidate !== 0 이면
 L2549            output: export + 동적 + generateStaticParams 없음  => throw
 L2562            동적이 아니면  staticPaths = [ {pathname: page, ...} ]  isStatic = true
 L2576            동적인데 gSP 없고 dynamic 이 'error' | 'force-static' 이면  []  isStatic = true
 L2596        pages 면 hasStaticProps → ssgPages / hasServerProps → serverPropsPages / ...
 L2684        catch — 'INVALID_DEFAULT_EXPORT' 만 삼켜 invalidPages 에 넣는다
 L2703      pageInfos.set(page, { isStatic, isSSG, isRoutePPREnabled, ssgPageRoutes, ... })
 L2780  proxy 이거나 nodejs middleware 면 functionsConfigManifest['/_middleware']
 L2813  writeFunctionsConfigManifest(distDir, ...)
```

```text
 ★★★ 같은 워커 풀이 [03]과 [04]를 **둘 다** 한다

 BUILD L936-941
   const staticWorkerExposedMethods = [
     'hasCustomGetInitialProps', 'isPageStatic', 'getDefinedNamedExports', 'exportPages',
   ] as const
 build/worker.ts (27줄) — isPageStatic 은 utils.ts 것을 감싸고(L21-25), exportPages 는
   export/worker.ts 에서 다시 내보낸다 (L27)
 BUILD L3197  exportApp(..., staticWorker)  ← [04]가 **이 풀을 넘겨받는다**
 export/index.ts L783-787  staticWorker 가 오면 새로 만들지 않고 그것을 쓴다

 => 정적 판별 때 require 한 모듈이 워커 프로세스에 **남아 있는 채로** prerender 가 돈다 ※
    (※ 모듈 캐시가 재사용된다는 것은 풀 재사용에서 내가 끌어낸 것이다. 측정하지 않았다)
 ★ 워커는 `isolatedMemory: true` 로 뜬다 (L967). 주석 L966 "remove --max-old-space-size flag"
```

```text
 isPageStatic  build/utils.ts L685  — 워커 안에서 돈다

 L743   '/_global-error' 는 **묻지도 않고** isStatic: true
 L757   createIncrementalCache(...)
 L780   edge 런타임이면  getRuntimeContext(...) 샌드박스에서 `_ENTRIES["middleware_" + name]` 을 꺼낸다
 L817   아니면           loadComponents({ distDir, page, isAppPath, ... })    ← [02]의 출력
 L833   app 이면
 L840     segments = collectSegments(routeModule)       레이아웃~페이지의 설정·gSP 를 모은다
 L851     appConfig = reduceAppConfig(segments)           세그먼트 설정을 하나로 합친다
 L867     isRoutePPREnabled = APP_PAGE && checkIsRoutePPREnabled(pprConfig)
 L874     force-dynamic 이고 PPR 이 아니면  appConfig.revalidate = 0
 L883     동적 세그먼트가 있고 edge 가 아니면
 L889       정적 메타데이터 파일 라우트면  buildStaticMetadataStaticPaths(page)
 L897       아니면                          buildAppStaticPaths({...})     (아래)
 L922   pages 면 기본 export 가 React 컴포넌트가 아니면 => throw 'INVALID_DEFAULT_EXPORT'
 L934   gIP+gSP · gIP+gSSP · gSP+gSSP 조합은 => throw
 L962   gSP + getStaticPaths 면  buildPagesStaticPaths(...)
 L975   gSP · gIP · gSSP 가 다 없으면 isStatic = true.  L982 PPR 이면 무조건 isStatic = true
```

```text
 buildAppStaticPaths  SPAPP L817-1180 — generateStaticParams 를 **실제로 부른다**

 L864   output: export 에 dynamicParams: true 세그먼트가 있으면 => throw
 L873   ComponentMod.patchFetch()                    ← fetch 가 캐시를 타게 한다
 L898   store = createWorkStore({ page, renderOpts: { supportsDynamicResponse: true, ... } })
 L923   workAsyncStorage.run(store, generateRouteStaticParams, segments, ...)
          L676-775  세그먼트를 앞에서부터 돌며 부모 params 마다 자식 gSP 를 부른다
          L612-661  callGenerateStaticParams
            L627      workUnitStore = { type: **'generate-static-params'**, phase: 'render', implicitTags, rootParams }
            L634      workUnitAsyncStorage.run(workUnitStore, generateStaticParams, { params: parentParams })
            L640      배열이 아니면 => throw.  L652 원소가 plain object 가 아니면 => throw
          L746 · L763  PPR 인데 gSP 가 빈 배열이면 => throwEmptyGenerateStaticParamsError
 L948   dynamicParams: false 인 세그먼트의 param 이 결과에 빠져 있으면 => throw
 L990   hadAllParamsGenerated
 L1014  fallbackMode                                  (위 실제 코드)
 L1027  다 채웠거나 PPR 이면 prerenderedRoutesByPathname 을 채운다
 L1050    PPR 이면 **placeholder 그대로인 기본 경로**(`/blog/[slug]`)도 하나 넣는다 — fallback 셸용
 L1086    PPR 인데 값이 빠진 param 부터는 fallbackRouteParams 로 돌린다
 L1175  cacheComponents 면 assignStaticShellMetadata(...)
 L1179  return { fallbackMode, prerenderedRoutes }
```

```text
 ★★★ `generateStaticParams` 가 도는 스토어 — [동적 판별]과 [동적 API]가 말한 그 'generate-static-params' 다

   'generate-static-params' 를 **만드는** 곳은 저장소 전체에서 SPAPP L628 하나다
     (grep "'generate-static-params'" — 나머지는 타입 정의 work-unit-async-storage.external.ts L432 와 case 절)
   => [동적 판별] 01 의 markCurrentScopeAsDynamic 은 이 스토어에서 `break`(아무것도 안 함)
   => [동적 API] 의 cookies() 는 이 스토어에서 "runs at build time without an HTTP request" 로 throw

 ★★ 바깥의 WorkStore 는 `supportsDynamicResponse: true` 로 만든다 (L904)
   work-store.ts L116-119  isStaticGeneration = !supportsDynamicResponse && !isDraftMode && !isPossibleServerAction
   => generateStaticParams 가 도는 동안 workStore.isStaticGeneration 은 **false** 다 ※
      (※ 이 값이 gSP 안의 fetch 캐시 동작을 어떻게 바꾸는지는 확인하지 않았다)
```

```text
 ★★ "work queue" 인데 큐에 **한 번에 하나만** 있다 (SPAPP L701-772)

   L701  const queue: WorkItem[] = [{ segmentIndex: 0, params: [] }]
   L717  gSP 가 없으면  queue.push({ segmentIndex + 1, params }); continue
   L771  있으면         queue.push({ segmentIndex + 1, params: nextParams })
   L708  끝까지 갔으면  break

 => 모든 갈래가 **정확히 하나를** 넣거나 끝낸다. 실제로는 세그먼트를 앞에서 뒤로 도는 for 문이다
    주석 L695 "Use iterative processing with a work queue to avoid recursion overhead"
 ★★ 그리고 buildAppStaticPaths 의 docstring(L807-816)은 이 함수의 docstring(L663-675)을
   **거의 그대로 옮긴 것**이다 — "@returns Promise that resolves to an array of all parameter
   combinations" 라고 적지만 실제 반환은 `{ fallbackMode, prerenderedRoutes }` 다
```

## 결과가 쓰이는 곳

```text
 staticPaths : Map<originalAppPath, PrerenderedRoute[]>
      --> [04]가 알파벳순으로 정렬해(L3030-3032) exportPathMap 의 app 항목으로 바꾼다

 appDefaultConfigs : Map<originalAppPath, AppSegmentConfig>
      --> [04]에서 dynamic === 'error' 를 _isDynamicError 로, revalidate 를 기본 수명으로 쓴다

 ssgPages · staticPages · additionalPaths · ssgStaticFallbackPages · ssgBlockingFallbackPages
      --> [04]의 Pages Router 쪽 경로와 prerender-manifest 의 fallback

 pageInfos : Map<page, PageInfo>
      --> [04]가 export 결과로 덮어쓰고, 마지막 printTreeView(L4505)가 빌드 로그의 표로 찍는다

 invalidPages
      --> NFT region L2885-2897 이 BUILD_OPTIMIZATION_FAILED 로 던진다 — CLI 가 그 코드를 알아본다 (NBCLI L146)

 functions-config-manifest.json (L2813)
      --> maxDuration · regions · nodejs middleware 매처
```

## 다루지 않는 것

`getNumberOfWorkers`(L904)의 계산, `hasCustomGetInitialProps` · `getDefinedNamedExports` 의 구현, `getStaticInfoIncludingLayouts`(`build/get-static-info-including-layouts.ts`)의 AST 분석, `collectSegments` · `reduceAppConfig` · `collectRootParamKeys`(`build/segment-config/`)의 규칙, `checkIsRoutePPREnabled` 가 `experimental.ppr` 만 보는 이유와 `cacheComponents` 와의 관계, `getRuntimeContext` 의 edge 샌드박스, `buildStaticMetadataStaticPaths`, `buildPagesStaticPaths`(`build/static-paths/pages.ts` 230줄), `extractPathnameRouteParamSegments` · `generateAllParamCombinations` · `validateParams` · `filterUniqueParams` · `resolveRouteParamsFromTree` · `calculateFallbackMode` · `assignStaticShellMetadata` 의 본문, `createIncrementalCache` 와 ISR 캐시, `AfterRunner`, `getImplicitTags`, 그리고 middleware 매처 JS(L2792-2809)의 소비처는 이 문서의 범위 밖이다.
