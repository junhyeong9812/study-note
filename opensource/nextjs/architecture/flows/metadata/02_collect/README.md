# 02 트리를 따라 모은다

상위: [메타데이터가 `<head>` 가 되기까지](../README.md)

로더 트리를 깊이 우선으로 내려가며 세그먼트마다 `[export, 파일 메타데이터]` 한 쌍을 배열에 쌓는다. 여기서는 **`generateMetadata` 를 부르지 않는다.** 부를 수 있게 감싸 둘 뿐이다. 부르는 것은 [03]이다.

## 위치

`packages/next` / `src/lib/metadata` / `resolve-metadata.ts` L607-L809 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/lib/metadata/resolve-metadata.ts#L607-L809))

## 실제 코드

export 를 꺼내는 자리다. 함수면 감싸고, 아니면 객체를 그대로 준다.

```ts
// resolve-metadata.ts L522-L563
function getDefinedMetadata(
  mod: any,
  props: SegmentProps,
  tracingProps: { route: string }
): Metadata | MetadataResolver | null {
  if (typeof mod.generateMetadata === 'function') {
    const { route } = tracingProps
    const segmentProps = createSegmentProps(mod.generateMetadata, props)

    return Object.assign(
      (parent: ResolvingMetadata) =>
        getTracer().trace(
          ResolveMetadataSpan.generateMetadata,
          {
            spanName: `generateMetadata ${route}`,
            attributes: {
              'next.page': route,
            },
          },
          () => mod.generateMetadata(segmentProps, parent)
        ),
      { $$original: mod.generateMetadata }
    )
  }
  return mod.metadata || null
}

/**
 * If `fn` is a `'use cache'` function, we add special markers to the props,
 * that the cache wrapper reads and removes, before passing the props to the
 * user function.
 */
function createSegmentProps(
  fn: Function,
  props: SegmentProps
): SegmentProps | UseCacheSegmentProps {
  return isUseCacheFunction(fn)
    ? 'searchParams' in props
      ? { ...props, $$isPage: true }
      : { ...props, $$isLayout: true }
    : props
}
```

```text
 ★★★ generateMetadata 를 **바로 부르지 않고 한 겹 감싼다** (L531-544)

   (parent) => getTracer().trace(ResolveMetadataSpan.generateMetadata,
                 { spanName: `generateMetadata ${route}` ... },
                 () => mod.generateMetadata(segmentProps, parent))
   + { $$original: mod.generateMetadata }

 => 감싼 함수는 **parent 하나만** 받는다. props 는 이미 클로저에 들어 있다
 => `$$original` 로 원래 함수를 붙여 둔다 — [03]이 그것을 보고
    'use cache' 함수인지, 둘째 인자(parent)를 쓰는지 읽는다
 ★ 정적 `metadata` 는 `mod.metadata || null` 로 끝이다 (L546)

 ★★ createSegmentProps(L554-563) — 'use cache' 함수면 표시를 붙인다
   'searchParams' in props  => { ...props, $$isPage: true }
   아니면                   => { ...props, $$isLayout: true }
   docstring L549-553 - "If `fn` is a `'use cache'` function, we add special markers
     to the props, that the cache wrapper reads and removes, before passing the
     props to the user function."
 => page 인지 layout 인지를 **searchParams 유무로** 가른다.
    그 props 는 아래 L773 이 isPage 일 때만 searchParams 를 넣어 만든다
```

## 동작 흐름

```text
 resolveMetadata(tree, pathname, searchParams, errorConvention,
                 interpolatedParams, metadataContext)            RMD L1279

 L1287  metadataItems = await resolveMetadataItems(tree, searchParams,
                                                   errorConvention, interpolatedParams)
          L707  cache(async function (...) {
          L713-715 parentParams = {} · metadataItems = [] · errorMetadataItem = [null, null]
          L717    return resolveMetadataItemsImpl(...)
 L1293  workStore = workAsyncStorage.getStore()
 L1294    없으면 => throw InvariantError('Expected workStore to be initialized')
 L1297  return accumulateMetadata(workStore.route, metadataItems, pathname, metadataContext)  [03]

 resolveMetadataItemsImpl(metadataItems, tree, treePrefix, parentParams, ...)   L730
 L742  [segment, parallelRoutes, { page }] = tree
 L749  segmentParam = getSegmentParam(segment)
 L750    동적 세그먼트면 interpolatedParams 에서 값을 꺼내 currentParams 에 더한다
 L762  optionalCatchAllParamName — 값이 없는 [[...slug]] 를 기억한다
 L769  params = createServerParamsForMetadata(currentParams, optionalCatchAllParamName)
 L773  props = isPage ? { params, searchParams } : { params }
 L775  await collectMetadata({ tree, metadataItems, errorMetadataItem, errorConvention,
                               props, route: 세그먼트를 '/' 로 이은 것 (__PAGE__ 제외) })
 L787  for (key in parallelRoutes)
 L789    await resolveMetadataItemsImpl(... childTree ...)   ← **재귀, 순차**
 L802  자식이 없고 errorConvention 이면
 L805    metadataItems.push(errorMetadataItem)   ← 병렬 라우트가 빈 **모든** 잎에서 같은 배열 참조를 넣는다
                                                 (슬롯이 여럿이면 여러 번, 맨 뒤가 아닐 수도 있다)
 L808  return metadataItems
```

```text
 collectMetadata  L608 — 세그먼트 하나에서 쌍 하나

 L625  hasErrorConventionComponent = errorConvention && tree[2][errorConvention]
 L628  errorConvention 이 있으면
 L629    mod = getComponentTypeModule(tree, 'layout')    ← **page 는 안 본다**
 L630    modType = errorConvention
 L631  없으면
 L632    { mod, modType } = await getLayoutOrPageModule(tree)   (L632-633)
            app-dir-module.ts L42-54 — layout 이 있으면 layout, 없으면 page, 없으면 defaultPage
 L639  route += `/${modType}`
 L642  staticFilesMetadata = await resolveStaticMetadata(tree[2], props)
 L643  metadataExport = mod ? getDefinedMetadata(mod, props, { route }) : null
 L645  metadataItems.push([metadataExport, staticFilesMetadata])
 L647  이 세그먼트에 에러 경계 파일이 있으면
 L648    errorMod = getComponentTypeModule(tree, errorConvention)
 L653    errorMetadataItem[0] = 그 export,  [1] = 이 세그먼트의 파일 메타데이터
          ★ 배열을 **바꿔 끼운다.** 더 깊은 세그먼트에 경계가 있으면 그것이 덮어쓴다
```

```text
 ★★★ 세그먼트 하나에 **모듈은 하나만** 읽는다

   getLayoutOrPageModule 이 layout 을 먼저 고르고 page 는 그 다음이다 (app-dir-module.ts L42-49)
 => 한 노드에 layout 과 page 가 같이 있으면 page 의 metadata 는 이 노드에서 안 읽힌다
 => 그런데 webpack 로더는 page 를 **따로 `__PAGE__` 자식 노드**로 만든다
    (next-app-loader/index.ts L276-280 — ['__PAGE__', {}, { page: [...], 메타데이터 }])
    그래서 page 의 metadata 는 그 자식 노드에서 읽힌다
 ★ route 문자열에서 `__PAGE__` 는 뺀다 (L782-784) — 트레이스 스팬 이름에 안 보이게
 ※ Turbopack 이 만드는 로더 트리도 같은 모양인지는 확인하지 않았다

 => 배열의 순서가 곧 **상속 순서**다. 주석 L607 이 그 모양을 적는다
      "[layout.metadata, static files metadata] -> ... -> [page.metadata, static files metadata]"
```

```text
 ★★ 병렬 라우트도 **전부** 한 줄로 이어 붙인다 (L787-800)

   for (const key in parallelRoutes) { await resolveMetadataItemsImpl(...) }

 => `children` 만이 아니라 @슬롯 트리도 같은 배열에 들어간다.
    순서는 parallelRoutes 객체의 키 순서다
 ※ 그래서 슬롯의 page 가 export 한 metadata 도 합쳐지고,
   [03]의 "나중 것이 이긴다" 규칙에 따라 키 순서상 뒤의 슬롯이 이길 수 있다.
   이것을 의도했다는 주석은 없다
 ★ 재귀가 `await` 로 **순차**다. 모듈 import 가 세그먼트마다 차례로 일어난다.
   generateMetadata 호출은 여기서 일어나지 않는다. **그러나 사용자 코드는 돈다** —
   ① getLayoutOrPageModule 이 `await layout[0]()`/`page[0]()` 로 모듈을 import 하면서
     최상위 코드가 평가되고 (server/lib/app-dir-module.ts L42-53)
   ② resolveStaticMetadata 가 부르는 동적 이미지 모듈이 사용자의
     `generateImageMetadata({params})` 를 실행한다 (next-metadata-image-loader.ts L114-120)
```

```text
 ★★ 파일 메타데이터(icon.png · opengraph-image 등)는 **모듈과 따로** 모은다 (L565-605)

 resolveStaticMetadata(modules, props)   L582
   metadata 가 없으면 => return null (L587)
   L589  [icon, apple, openGraph, twitter] = Promise.all(collectStaticImagesFiles × 4)
   L601  manifest: metadata.manifest   (이미지 아님 — 그대로)

 collectStaticImagesFiles(metadata, props, type)   L565
   L572  metadata[type].map(async imageModule => await imageModule(props))
   L578  (await Promise.all(...)).flat()
 => 이미지 모듈이 **props(params)를 받는 함수**다. 동적 세그먼트의 이미지 URL 이
    params 에 따라 달라질 수 있어서다 ※ (함수 형태에서 추론 — 주석 없음)
 ★ 이 쪽은 Promise.all 로 **병렬**이다 — 단 세그먼트 **안에서만**이다.
   세그먼트 사이는 `await resolveStaticMetadata`(L642)라 순차다
```

```text
 viewport 도 같은 길을 한 벌 더 간다 (L811-927)

 resolveViewportItems   L812  cache() — 인자 넷 (pathname · metadataContext 없음)
 resolveViewportItemsImpl  L837  — 본문이 metadata 판과 **줄 단위로 거의 같다**
 collectViewport        L659  — 차이는 둘
   ① 파일 메타데이터를 안 모은다. 항목이 쌍이 아니라 **export 하나**다 (ViewportItems, L94)
   ② 에러 항목을 배열 대신 `{ current }` ref 로 쥔다 (ErrorViewportItemRef, L811)
 ★ 트리 순회를 metadata 와 viewport 가 **따로 두 번** 한다.
   두 cache() 가 각자의 결과를 들고 있다
```

## 결과가 쓰이는 곳

```text
 metadataItems : Array<[Metadata | MetadataResolver | null, StaticMetadata]>
      --> accumulateMetadata 가 [03]에서 앞에서부터 합친다
          index 0 = 루트 layout. [03]의 favicon 규칙이 `i <= 1` 로 이 순서를 가정한다

 errorMetadataItem (errorConvention 일 때 맨 뒤)
      --> not-found.js 등의 metadata 가 page 자리를 대신한다

 viewportItems : Array<Viewport | ViewportResolver | null>
      --> accumulateViewport 가 [03]에서 합친다

 $$original · $$isPage · $$isLayout
      --> [03]의 getResult 가 $$original 을 읽고,
          [`'use cache'`] 02 의 isPageSegmentFunction(UCW L3575) 이 $$isPage 를 읽는다
```

## 다루지 않는 것

`getSegmentParam` 의 세그먼트 파싱과 `interpolatedParams` 를 채우는 쪽, `createServerParamsForMetadata`(`server/request/params`)가 만드는 약속과 optional catch-all 처리(주석이 `create-component-tree.tsx` 를 가리킨다), `next-app-loader` 의 `createStaticMetadataFromRoute` · `createMetadataExportsCode` 가 이미지 모듈을 만드는 방식과 Turbopack 쪽 로더 트리, `defaultPage`(`default.js`) 세그먼트의 의미, `getTracer().trace` 와 `ResolveMetadataSpan` 스팬, `isUseCacheFunction` 이 서버 참조 ID 첫 바이트를 읽는 방식(`server-reference-info.ts`)은 이 문서의 범위 밖이다.
