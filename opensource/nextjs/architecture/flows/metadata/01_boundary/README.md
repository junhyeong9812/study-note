# 01 경계와 스트리밍

상위: [메타데이터가 `<head>` 가 되기까지](../README.md)

`createMetadataComponents` 는 값을 돌려주지 않는다. **컴포넌트 셋**을 돌려준다. 셋이 같은 메타데이터 계산을 나눠 쥐는데, 태그를 그리는 쪽은 오류를 삼키고 **오류를 던지는 일은 페이지 옆의 outlet 이 맡는다.** 그리고 봇이냐 아니냐에 따라 `Suspense` 로 감쌀지가 갈린다.

## 위치

`packages/next` / `src/lib/metadata` / `metadata.tsx` L36-L182 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/lib/metadata/metadata.tsx#L36-L182))

## 실제 코드

같은 `Metadata` 를 두 가지로 감싼다.

```tsx
// metadata.tsx L128-L175
  function MetadataWrapper() {
    // TODO: We shouldn't change what we render based on whether we are streaming or not.
    // If we aren't streaming we should just block the response until we have resolved the
    // metadata.
    if (!serveStreamingMetadata) {
      return (
        <MetadataBoundary>
          <Metadata />
        </MetadataBoundary>
      )
    }
    return (
      <div hidden>
        <MetadataBoundary>
          <Suspense name="Next.Metadata">
            <Metadata />
          </Suspense>
        </MetadataBoundary>
      </div>
    )
  }

  function MetadataOutlet() {
    const pendingOutlet = Promise.all([
      getResolvedMetadata(
        tree,
        pathnameForMetadata,
        searchParams,
        interpolatedParams,
        metadataContext,
        errorType
      ),
      getResolvedViewport(tree, searchParams, interpolatedParams, errorType),
    ]).then(() => null)

    // TODO: We shouldn't change what we render based on whether we are streaming or not.
    // If we aren't streaming we should just block the response until we have resolved the
    // metadata.
    if (!serveStreamingMetadata) {
      return <OutletBoundary>{pendingOutlet}</OutletBoundary>
    }
    return (
      <OutletBoundary>
        <Suspense name="Next.MetadataOutlet">{pendingOutlet}</Suspense>
      </OutletBoundary>
    )
  }
  MetadataOutlet.displayName = 'Next.MetadataOutlet'
```

```text
 ★★★ serveStreamingMetadata 하나로 **트리 모양이 바뀐다**

   false  <MetadataBoundary><Metadata/></MetadataBoundary>
   true   <div hidden>
            <MetadataBoundary><Suspense name="Next.Metadata"><Metadata/></Suspense></MetadataBoundary>
          </div>

 => 스트리밍이면 metadata 가 **Suspense 경계 안**에 있다.
    generateMetadata 가 늦어도 셸은 먼저 나간다
 => 아니면 경계가 없다. metadata 가 풀릴 때까지 **응답이 기다린다**
 ★ 두 갈래 모두 TODO 가 같은 말을 한다 (L129-131 · L163-165)
   "We shouldn't change what we render based on whether we are streaming or not.
    If we aren't streaming we should just block the response until we have
    resolved the metadata."
 ★★ MetadataOutlet 도 같은 조건으로 Suspense 를 씌우거나 뺀다 (L166-173)
 ★★ 그리고 Viewport 에는 이 갈림이 **없다** — ViewportWrapper(L88-94)는 언제나
   <ViewportBoundary><Viewport/></ViewportBoundary> 뿐이다
   즉 viewport 는 스트리밍 여부와 무관하게 Suspense 밖에서 기다린다
   ★ 이유는 [동적 판별] 쪽 주석이 적는다 — DYNR L1388-1391 "dynamic Viewport … blocking
     the root … you need to opt into that by adding a Suspense boundary above the body",
     DYNR L841-845 "the viewport's stack lives in the head". viewport 는 head 안에 있어
     본문의 Suspense 로는 가릴 수 없다
```

## 동작 흐름

```text
 createMetadataComponents({tree, pathname, parsedQuery, metadataContext,
                           interpolatedParams, errorType, serveStreamingMetadata})   MDT L36

 L57   searchParams        = createServerSearchParamsForMetadata(parsedQuery)
 L58   pathnameForMetadata = createServerPathnameForMetadata(pathname)
        ★ 이 두 객체를 **클로저에 한 번만** 만든다 — 아래 셋이 같은 인자를 쓰게 된다

 L60   async function Viewport()
 L61     getResolvedViewport(tree, searchParams, interpolatedParams, errorType)
 L66     .catch(viewportErr =>
 L70        isPostpone 이면                          => throw (L71)
 L73        errorType 없고 HTTP 접근 대체 오류면       => getNotFoundViewport(...).catch(() => null)
 L81        그 밖                                    => return null
 L96   async function Metadata()                  — 같은 모양, getResolvedMetadata / getNotFoundMetadata
 L150  function MetadataOutlet()
 L151    pendingOutlet = Promise.all([getResolvedMetadata(...), getResolvedViewport(...)])
                           .then(() => null)
 L167    <OutletBoundary>{pendingOutlet}</OutletBoundary>   ← **약속 자체를 자식으로** 둔다
 L177  return { Viewport: ViewportWrapper, Metadata: MetadataWrapper, MetadataOutlet }
```

```text
 ★★★ 오류를 삼키는 쪽과 던지는 쪽이 **나뉘어 있다** (주석 L30-35)

   "Use a promise to share the status of the metadata resolving,
    returning two components `MetadataTree` and `MetadataOutlet`
    `MetadataTree` is the one that will be rendered at first in the content
    sequence for metadata tags.
    `MetadataOutlet` is the one that will be rendered under error boundaries
    for metadata resolving errors.
    In this way we can let the metadata tags always render successfully,
    and the error will be caught by the error boundary and trigger fallbacks."

 Metadata 의 catch    => null 을 그린다. 주석 L120 -
                        "We're going to throw the error from the metadata outlet
                         so we just render null here instead"
 MetadataOutlet       => Promise.all 이 reject 되면 그 약속을 자식으로 쥔 자리에서 터진다
 => head 자리는 **언제나 성공**하고, 오류는 페이지 옆의 에러 경계가 받는다
 ★ 주석은 `MetadataTree` 라 부르지만 반환 객체의 이름은 `Metadata` 다 (L179). 이름만 남은 흔적이다
 ※ "약속을 자식으로 두면 reject 시 그 자리에서 throw 된다" 는 React 의 규약이다.
   소스는 결과("error will be caught by the error boundary")만 적는다
```

```text
 ★★★ 같은 계산을 두 번 하지 않는 장치가 React `cache()` 다 (L184 · L204 · L223 · L234)

 const getResolvedMetadata = cache(getResolvedMetadataImpl)
 const getNotFoundMetadata = cache(getNotFoundMetadataImpl)
 const getResolvedViewport = cache(getResolvedViewportImpl)
 const getNotFoundViewport = cache(getNotFoundViewportImpl)

 Metadata(L97) 와 MetadataOutlet(L152) 은 getResolvedMetadata 를
   **같은 여섯 인자**로 부른다 — tree · pathnameForMetadata · searchParams ·
   interpolatedParams · metadataContext · errorType
 => 앞의 두 객체를 L57-58 에서 한 번만 만든 이유다.
    ※ React cache 는 인자 동일성으로 적중하므로, 매번 새로 만들었다면 두 번 계산됐을 것이다
 ★ 그 안의 resolveMetadataItems · resolveViewportItems 도 cache() 다 (RMD L707 · L812) [02]
```

```text
 ★★ errorType 이 'redirect' 면 **없는 것으로** 친다 (L193 · L230)

   const errorConvention = errorType === 'redirect' ? undefined : errorType

 => MetadataErrorType 은 'not-found' | 'forbidden' | 'unauthorized' 셋이다 (RMD L88)
    redirect 는 경계 파일(not-found.js 같은 것)이 없으니 평소 트리로 푼다
 ★ getNotFound* 는 errorConvention 을 **'not-found' 로 고정**한다 (L212 · L240).
   Metadata 가 notFound() 를 맞으면(L111) 여기로 한 번 더 푼다
   ★★ isHTTPAccessFallbackError 는 404 · 403 · 401 **셋 다** 참이다
     (http-access-fallback.ts L1-7 ALLOWED_CODES · L33-38 digest 의 상태 코드 검사)
   => digest 가 403 · 401 인 오류가 와도 head 에는 **not-found 쪽 메타데이터**가 그려진다
   ※ forbidden() · unauthorized() 가 그 digest 로 던진다는 것은 이름에서 온 추정이다 (본문 안 읽음)
```

```text
 ★★ Legacy PPR 의 postpone 만 **삼키지 않고 다시 던진다** (L67-72 · L105-110)

   "When Legacy PPR is enabled metadata can reject with a Postpone type
    This will go away once Legacy PPR is removed and dynamic metadata will
    stay pending until after the prerender is complete when it is dynamic"

 => postpone 은 오류가 아니라 **구멍 신호**라서 null 로 바꾸면 안 된다
 => 주석은 Legacy PPR 이 사라지면 동적 metadata 가 **걸린 채(pending)로 남을 것**이라고 적는다
 ※ cacheComponents 의 prerender 에서는 이미 그렇다고 본다 — `cookies()` 의 'prerender' 갈래가
   makeHangingCookies 로 걸린 약속을 돌려주고([동적 판별] 01), 중단될 때
   [동적 판별] 03 이 그 컴포넌트 스택에서 `__next_metadata_boundary__` 를 찾는다
```

```text
 serveStreamingMetadata 는 어디서 정해지는가

 build/templates/app-page-runtime.ts L535-537
   const serveStreamingMetadata = !userAgent ? true
     : shouldServeStreamingMetadata(userAgent, nextConfig.htmlLimitedBots)

 server/lib/streaming-metadata.ts L6-20
   htmlLimitedBots(설정) 또는 HTML_LIMITED_BOT_UA_RE_STRING 정규식에
   user-agent 가 걸리면 => false. 주석 L15 - "Only block metadata for HTML-limited bots"
 => **사람 브라우저는 스트리밍, HTML 만 읽는 봇은 블로킹**이다

 ★★ 그 결정이 PPR 셸 사용도 바꾼다 (app-page-runtime.ts L539-543)
   "PPR shells are generated for streaming metadata. Requests that require
    blocking metadata must bypass the shell so the prerender and dynamic
    render use the same metadata tree."
   shouldForceDynamicPPRRender = isRoutePPREnabled && !serveStreamingMetadata
 => 봇 요청은 **미리 만든 PPR 셸을 안 쓴다.** 셸은 Suspense 가 있는 트리로 만들어졌기 때문이다
 ★ 같은 이유로 fallback 도 블로킹 렌더로 바뀐다 (L1128-1136)
 ★ 옆의 TODO(L531-534)가 **알려진 버그**를 적는다 — revalidate 때 이 값이 늘 true 가
   된다는 것, 그리고 export 중에 true 로 세워 두어 고치면 hydration 문제가 난다는 것
 ★ export/worker.ts L279 · edge-ssr-app.ts L133 는 `serveStreamingMetadata: true` 로 고정한다
```

## 결과가 쓰이는 곳

```text
 ViewportWrapper · MetadataWrapper
      --> [App Router]의 initialHead(app-render.tsx L2157-2158) / rscHead(L726-731)

 MetadataOutlet
      --> create-component-tree.tsx L912 — 페이지 엘리먼트 · layerAssets 다음
          `children` 슬롯 경로에만 넘긴다(L599-601) — 주석 "we only want to throw on the first one"

 <div hidden> + Suspense (스트리밍일 때)
      --> 태그가 body 쪽 스트림에 늦게 나올 수 있다. 아이콘은 [04]의 스크립트가 head 로 옮긴다

 MetadataBoundary / ViewportBoundary / OutletBoundary 프레임
      --> [동적 판별] 03 — hasMetadataRegex · hasViewportRegex · hasOutletRegex
          outlet 칸이 hasSuspenseAboveBody 만 세우는 이유도 거기 있다
```

## 다루지 않는 것

`notFound()` · `forbidden()` · `unauthorized()` 가 digest 를 만들어 던지는 쪽, `isPostpone` 과 Legacy PPR 의 postpone 체계, `createServerSearchParamsForMetadata` · `createServerPathnameForMetadata` 가 만드는 약속의 동적 추적, `HTML_LIMITED_BOT_UA_RE_STRING`(`shared/lib/router/utils/is-bot`)의 봇 목록과 `htmlLimitedBots` 설정, `app-page-runtime.ts` 의 fallback 모드 전체, 에러 경계가 outlet 의 오류를 받아 `not-found.js` 등을 그리는 쪽, React `cache()` 의 수명(요청 단위인지)은 이 문서의 범위 밖이다.
