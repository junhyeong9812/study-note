# 03 부모를 약속으로 넘기며 합친다

상위: [메타데이터가 `<head>` 가 되기까지](../README.md)

`generateMetadata(props, parent)` 의 `parent` 는 **약속**이다. 이유가 여기 있다 — `generateMetadata` 를 루프 전에 **대부분 먼저 부르고**, 루프가 앞에서부터 합쳐 가며 그 약속을 하나씩 풀어 준다. 예외는 parent 를 쓰는 `'use cache'` 함수 — 그것만 미뤄져 부모가 풀린 뒤에 불린다. 합치는 규칙은 대체로 **최상위 키 단위 덮어쓰기**다.

## 위치

`packages/next` / `src/lib/metadata` / `resolve-metadata.ts` L1025-L1276 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/lib/metadata/resolve-metadata.ts#L1025-L1276))

## 실제 코드

항목 하나를 "resolver + 결과" 또는 "결과" 로 바꾸는 함수다. 갈래가 넷이다.

```ts
// resolve-metadata.ts L1057-L1116
function getResult<TData extends object>(
  resolversAndResults: Array<
    ((value: Resolved<TData>) => void) | Result<TData>
  >,
  exportForResult: null | TData | InstrumentedResolver<TData>
) {
  if (typeof exportForResult === 'function') {
    // If the function is a 'use cache' function that uses the parent data as
    // the second argument, we don't want to eagerly execute it during
    // metadata/viewport pre-rendering, as the parent data might also be
    // computed from another 'use cache' function. To ensure that the hanging
    // input abort signal handling works in this case (i.e. the depending
    // function waits for the cached input to resolve while encoding its args),
    // they must be called sequentially. This can be accomplished by wrapping
    // the call in a lazy promise, so that the original function is only called
    // when the result is actually awaited.
    const useCacheFunctionInfo = getUseCacheFunctionInfo(
      exportForResult.$$original
    )
    if (useCacheFunctionInfo && useCacheFunctionInfo.usedArgs[1]) {
      const promise = new Promise<Resolved<TData>>((resolve) =>
        resolversAndResults.push(resolve)
      )
      resolversAndResults.push(
        createLazyResult(async () => exportForResult(promise))
      )
    } else {
      let result: TData | Promise<TData>
      if (useCacheFunctionInfo) {
        resolversAndResults.push(noop)
        // @ts-expect-error We intentionally omit the parent argument, because
        // we know from the check above that the 'use cache' function does not
        // use it.
        result = exportForResult()
      } else {
        result = exportForResult(
          new Promise<Resolved<TData>>((resolve) =>
            resolversAndResults.push(resolve)
          )
        )
      }
      resolversAndResults.push(result)
      if (result instanceof Promise) {
        // since we eager execute generateMetadata and
        // they can reject at anytime we need to ensure
        // we attach the catch handler right away to
        // prevent unhandled rejections crashing the process
        result.catch((err) => {
          return {
            __nextError: err,
          }
        })
      }
    }
  } else if (typeof exportForResult === 'object') {
    resolversAndResults.push(exportForResult)
  } else {
    resolversAndResults.push(null)
  }
}
```

```text
 resolversAndResults — 한 배열에 **resolver 와 결과가 번갈아** 들어간다
   함수 칸 다음 칸은 반드시 그 결과다 (주석 L1028-1030)

 갈래 ① 보통 generateMetadata (L1091-1096)
   result = exportForResult(new Promise(resolve => resolversAndResults.push(resolve)))
   => **지금 바로 부른다.** parent 는 아직 안 풀린 약속이다
 갈래 ② 'use cache' 이고 parent 를 **쓰는** 함수 (L1076-1082)
   resolver 를 먼저 넣고, 결과 칸에는 createLazyResult(...) — **await 될 때까지 안 부른다**
 갈래 ③ 'use cache' 이고 parent 를 **안 쓰는** 함수 (L1085-1090)
   resolver 칸에 noop, 결과 = exportForResult() — parent 없이 바로 부른다
 갈래 ④ 객체(정적 metadata) => 그대로 / null => null (L1111-1115)

 ★★★ ②가 따로 있는 이유 (주석 L1064-1072)
   "If the function is a 'use cache' function that uses the parent data as the
    second argument, we don't want to eagerly execute it during metadata/viewport
    pre-rendering, as the parent data might also be computed from another
    'use cache' function. To ensure that the hanging input abort signal handling
    works in this case (i.e. the depending function waits for the cached input to
    resolve while encoding its args), they must be called sequentially. ..."
 => 'use cache' 는 인자를 **직렬화해 캐시 키**를 만든다([`'use cache'`] 02).
    parent 가 인자면 parent 가 풀릴 때까지 키를 못 만든다 — 그래서 순차로 부른다
 ★ "parent 를 쓰는가" 는 **컴파일러가 서버 참조 ID 첫 바이트에 심은 비트**로 안다
   usedArgs[1] (server-reference-info.ts L33-60 — argMask 6비트 중 둘째)
 ★ ③은 parent 인자를 아예 생략한다. 주석 L1087-1089 - "We intentionally omit the parent
   argument, because we know from the check above that the 'use cache' function does
   not use it." ※ 감싼 함수(02 의 L532)가 undefined 를 parent 로 넘기게 된다
```

## 동작 흐름

```text
 accumulateMetadata(route, metadataItems, pathname, metadataContext)   RMD L1128

 L1134  resolvedMetadata = createDefaultMetadata()     (default-metadata.tsx — 전부 null/빈 값)
 L1136  titleTemplates = { title: null, twitter: null, openGraph: null }
 L1142  buildState = { warnings: new Set() }
 L1150  leafSegmentStaticIcons = { icon: [], apple: [] }

 L1155  resolversAndResults = prerenderMetadata(metadataItems)
          L1034  for 항목마다 getResult(...)            ← **여기서 사용자 함수가 불린다 — 대부분**
                 ★ `'use cache'` 이면서 `usedArgs[1]` — parent 인자 — 이 켜진 함수는 createLazyResult 로
                   **미뤄진다** (L1076-1082, server/lib/lazy-result.ts L9-35).
                   루프 안 L1182-1183 의 await 에서 **부모가 풀린 뒤에야** 불린다

 L1158  for (i = 0; i < metadataItems.length; i++)
 L1162    i <= 1 이고 파일 icon 첫 칸이 favicon 이면 shift — i === 0 일 때만 favicon 으로 쥔다
 L1167    pendingMetadata = resolversAndResults[resultIndex++]
 L1168    함수(resolver)면
 L1175      pendingMetadata = 다음 칸 (그 결과)
 L1177      resolveParentMetadata(freezeInDev(resolvedMetadata))  ← **여기서 parent 가 풀린다**
 L1182    약속 같으면 await, 아니면 그대로
 L1188    resolvedMetadata = await mergeMetadata(route, pathname, {...})
 L1200    i < length - 2 이면 titleTemplates 를 지금 값의 template 으로 갱신
 L1209  파일 icon/apple 이 남아 있고 **resolvedMetadata.icons 가 없을 때만** 채운다
 L1228  warnings 를 한 번에 Log.warn
 L1234  return postProcessMetadata(resolvedMetadata, favicon, titleTemplates, metadataContext)
```

```text
 ★★★ 부모 값이 **합친 결과**다 — 부모 export 그대로가 아니다

 L1177 이 넘기는 것은 i 번째 항목 **직전까지 합친** resolvedMetadata 다
 => 자식의 `await parent` 는 루트부터 바로 위까지 **누적된 ResolvedMetadata** 를 받는다
 => 그리고 자식 함수는 이미 L1155 에서 돌기 시작했다.
    parent 를 await 하지 않는 generateMetadata 는 **부모와 동시에** 돈다
 ★ 개발에서는 그 값을 deepFreeze 해서 넘긴다 (freezeInDev, L1118-1126)
   ※ 자식이 parent 를 고쳐 쓰면 개발에서만 막힌다. mergeMetadata 가 structuredClone(L234) 으로
     새 객체를 만들므로 얼린 객체를 합치는 쪽은 문제가 없다
```

```text
 ★★ 먼저 부른 약속이 reject 되면? (L1099-1109)

   result.catch((err) => { return { __nextError: err } })
   주석 L1100-1103 - "since we eager execute generateMetadata and they can reject at
     anytime we need to ensure we attach the catch handler right away to prevent
     unhandled rejections crashing the process"

 => 목적은 **unhandled rejection 으로 프로세스가 죽는 것**을 막는 것뿐이다
 ★ `.catch` 가 만든 새 약속은 버려진다. `__nextError` 는 저장소 전체에서 이 한 줄뿐이다 (grep)
 => 배열에는 **원래 result** 가 들어 있으므로(L1098) 오류는 L1183 의 await 에서 그대로 던져진다
   ※ 뒤 문장은 JS 약속 의미론에서 온 추론이다. 소스가 적지는 않는다
 => 그 오류가 [01]의 Metadata catch(null 을 그림)와 MetadataOutlet(던짐)으로 간다
```

```text
 ★★★ 합치기는 **최상위 키 하나씩 통째로 바꾼다** (mergeMetadata, L213-446)

 L234  newResolvedMetadata = structuredClone(resolvedMetadata)
 L236  metadataBase = 자식의 metadataBase 가 undefined 가 아니면 그것, 아니면 부모 것 (normalize)
 L242  for (const key_ in metadata)   ← **자식 export 에 있는 키만** 돈다
 L245    switch (key) — case 36개 + default `key satisfies never`

   title       L246  resolveTitle(metadata.title, titleTemplates.title)
   openGraph   L264  resolveOpenGraph(...) 결과로 **통째로 교체**
   twitter     L276  resolveTwitter(...) — 교체
   icons · alternates · robots · verification · appLinks ... — 전부 교체
   description 등 10개  L347-377  `metadata[key] ?? null`
   other       L384  Object.assign({}, 부모 other, 자식 other)   ← switch 안의 **유일한 병합**
   themeColor · colorScheme · viewport  L421-429  경고만 — viewport export 로 옮기라고

 => 자식이 `openGraph: { title }` 만 주면 부모의 openGraph.images 는 **사라진다**
 => 키가 **있기만 하면** 값이 undefined 여도 덮는다 — `description: undefined` 는
    `?? null` 로 부모 설명을 지운다 (L354-356)
 ★ 병합이 깊지 않다. switch 안에서는 `other` 만 한 단계 얕게 합친다
 ★ title.template 은 **끊긴다** — 어떤 층이 `title` 을 문자열로 주면 resolveTitle 이
   `template: null` 을 돌려주고(resolve-title.ts L16-19 · L38), 그 아래로는 조상 template 이
   더 전달되지 않는다
 ★ `await parent` 로 받는 값은 **후처리 전** 값이다 — 잎의 파일 아이콘(L1209-1225),
   og→twitter 자동 채우기, favicon 이 빠진 상태다. 파일 og·twitter 이미지는 이미 들어 있다
 ★ 단 switch 밖에 병합이 더 있다 — mergeMetadata 끝의 mergeStaticMetadata(L434-443)가
   파일 이미지를 `{ ...target.openGraph, images }` · `{ ...target.twitter, images }` 로
   **펼쳐 합친다** (L181-202). title template 과 metadataBase 대체도 계승 경로다
```

```ts
// resolve-metadata.ts L384-L402
      case 'other':
        newResolvedMetadata.other = Object.assign(
          {},
          newResolvedMetadata.other,
          metadata.other
        )
        if (metadata.other) {
          if ('apple-touch-fullscreen' in metadata.other) {
            buildState.warnings.add(
              `Use appleWebApp instead\nRead more: https://nextjs.org/docs/app/api-reference/functions/generate-metadata`
            )
          }
          if ('apple-touch-icon-precomposed' in metadata.other) {
            buildState.warnings.add(
              `Use icons.apple instead\nRead more: https://nextjs.org/docs/app/api-reference/functions/generate-metadata`
            )
          }
        }
        break
```

```text
 ★ `other` 로 'apple-touch-fullscreen' · 'apple-touch-icon-precomposed' 를 넣어도
   경고를 남긴다 (L391-400). 최상위 키로 넣어도 같은 경고다 (L409-420)
   => 옛 이름을 두 경로에서 다 잡는다
```

```text
 ★★ title.template 은 **다음 항목부터** 먹는다 (L1198-1206)

   if (i < metadataItems.length - 2) {
     titleTemplates = { title: resolvedMetadata.title?.template || null, ... }
   }
   주석 L1198-1199 - "If the layout is the same layer with page, skip the leaf layout
     and leaf page" / "The leaf layout and page are the last two items"   (두 줄, 마침표 없음)

 => 템플릿은 합친 **뒤에** 갱신되므로, 그 항목 자신의 title 에는 안 먹는다
 => 마지막 두 항목(잎 layout, page)에서는 아예 갱신하지 않는다
 ※ [02]에서 본 것처럼 page 는 `__PAGE__` 자식 노드라서, 끝에서 둘째는
   **page 와 같은 폴더의 layout** 이다. 그 layout 의 template 은 page 에 안 먹는다는 뜻이 된다.
   테스트 resolve-metadata.test.ts L78-96 의 `[null, null], // same level layout` 이 그 가정을 적는다
 ★ resolveTitle(resolvers/resolve-title.ts L11-40) — template 의 `%s` 를 **전부** 바꾼다
   (`/%s/g`, L8). `absolute` 가 있으면 template 을 무시한다 (L27-28)
```

```text
 ★★ 파일 icon 과 export icons 는 **둘 중 하나**다 (L1209-1225)

 mergeStaticMetadata L174-179 — 파일 icon/apple 이 있으면 leafSegmentStaticIcons 를 **덮어쓴다**
   주석 L172 - "Keep updating the static icons in the most leaf node"
 => 가장 깊은 세그먼트의 파일 아이콘만 남는다
 L1213  if (!resolvedMetadata.icons) { ... unshift ... }
 => 어느 층이든 export 의 `icons` 가 null 이 아니게 만들었으면 **파일 아이콘은 버려진다**

 favicon 은 예외다 (L1160-1165 · L1011-1020)
   isFavicon (L118-129) — url 이 '/favicon.ico' 이거나 '/favicon.ico?' 로 시작하고 type 이 image/x-icon
     주석 L123 - "turbopack appends a hash to all images"
   i <= 1 에서 shift 로 빼고, i === 0 일 때만 쥔다
   주석 L1161 - "i <= 1 represents root layout, and if current page is also at root"
   postProcessMetadata 가 **icons.icon 맨 앞**에 끼운다 (L1019) — icons 가 있든 없든
 ※ i === 1 에서 빼기만 하고 버리는 이유 — 루트 page 노드에도 같은 폴더의 파일 메타데이터가
   실린다(next-app-loader L280 · L536 이 같은 `metadata` 를 두 번 쓴다). 두 번 나오는 것을 막는다
```

```text
 ★★ 파일 opengraph-image 는 **그 층이 images 를 안 줬을 때만** 쓴다 (L192-202 — twitter 는 L181-190)

   if (openGraph && !source?.openGraph?.hasOwnProperty('images'))
 => export 가 openGraph.images 를 명시하면 파일 이미지는 무시된다
 ★ 그때 `isStaticMetadataRouteFile: true` 로 풀어서 metadataBase 대체값을 쓰게 한다
   (resolve-opengraph.ts L74 — **상대 URL 이고** (metadataBase 가 없거나 정적 라우트 파일이면) 대체 base.
    조건은 `isRelativeUrl && (!metadataBase || isStaticMetadataRouteFile)` 다)
```

```text
 postProcessMetadata  L952-1023 — 다 합친 뒤 한 번

 L960  openGraph 가 있으면 twitter 의 빈 칸을 채운다
         title       twitter 에 없으면 og.title, 그것도 없으면 metadata.title
         description twitter 에 없으면 og.description || metadata.description
         images      twitter 에 images 키가 없거나 값이 비었으면 og.images (L970-972)
 L1008 inheritFromMetadata(openGraph, metadata) · (twitter, metadata)
         og/twitter 에 title · description 이 없으면 최상위 것을 가져온다
 L1011 favicon 을 icons.icon 맨 앞에

 ★ 채우는 방향이 한쪽이다 — og → twitter 는 있지만 twitter → og 는 없다
 ★ `commonOgKeys` 선언 위에 `no-unused-vars` 억제 주석이 붙어 있다(L950-951).
   값으로는 안 쓰고 **타입 계산**(L964)에만 쓴다
```

```text
 accumulateViewport  L1242-1276 — 같은 구조, 더 단순

 L1245  resolvedViewport = createDefaultViewport()
          width 'device-width' · initialScale 1 · themeColor null · colorScheme null
 L1247  resolversAndResults = prerenderViewport(viewportItems)   ← 같은 getResult
 L1250  while — resolver 면 parent 를 풀고, 결과를 await, mergeViewport
 mergeViewport L451-493 — case 10개, 역시 키 단위 교체
   width · height · initialScale 등 여덟은 주석 L482 "always override the target with the source"
 ★ titleTemplates · 파일 메타데이터 · 경고 · postProcess 가 **전부 없다**
 ★ 기본 viewport 가 이미 width/initialScale 을 갖고 있어서, 아무도 안 바꾸면
   [04]에서 `width=device-width, initial-scale=1` 태그가 나온다
```

## 결과가 쓰이는 곳

```text
 ResolvedMetadata (postProcessMetadata 의 반환)
      --> renderMetadata(MDT L257-265) 가 받아 createMetadataElements 로 [04]

 ResolvedViewport (accumulateViewport 의 반환)
      --> renderViewport(MDT L274-280) 가 받아 createViewportElements 로 [04]

 generateMetadata 의 reject
      --> L1183 await 에서 던져져 [01]의 두 catch 로

 buildState.warnings
      --> Log.warn — accumulateMetadata 한 번에 중복 없이 (Set)

 parent 약속에 넘긴 값
      --> 사용자 generateMetadata 가 `await parent` 로 받는다 (개발에서는 얼려서)
```

## 다루지 않는 것

`resolveOpenGraph` · `resolveTwitter` 의 og type 별 필드 표(`resolve-opengraph.ts` L27-159)와 이미지 URL 경고 문구 · Vercel 환경 변수 판정(L53-94), `resolveAlternates` · `resolveItunes` · `resolvePagination` 이 `pathname` 을 기다려 상대 URL 을 푸는 방식, `resolveRobots` · `resolveVerification` · `resolveAppleWebApp` · `resolveAppLinks` · `resolveFacebook` · `resolveThemeColor` 의 정규화(`resolve-basics.ts` 323줄), `resolveIcons`, `convertUrlsToStrings`(L131)가 URL 을 문자열로 바꾸는 이유, `normalizeMetadataBase`(L148)의 오류 문구, `createLazyResult`(`server/lib/lazy-result.ts`)의 `value` 캐싱, `deepFreeze` 구현, 병렬 라우트가 여럿일 때 "마지막 두 항목" 가정이 어떻게 되는지는 이 문서의 범위 밖이다.
