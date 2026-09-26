# 04 사용자가 부르지 않는 둘

상위: [동적 API 가 값을 내주기까지](../README.md)

`params` 와 `searchParams` 는 사용자가 **부르지 않는다.** 페이지와 레이아웃이 props 로 받는다. 만드는 것은 프레임워크다 — `create…Params` · `create…SearchParams` 팩토리 아홉 개가 스토어 종류에 따라 다른 약속을 만들어 넘긴다. 그래서 캐시 스코프에서 던지는 오류가 사용자 오류가 아니라 **InvariantError** 다.

## 위치

`packages/next` / `src/server/request` / `params.ts` L207-L266 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/request/params.ts#L207-L266))

`packages/next` / `src/server/request` / `search-params.ts` L114-L162 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/request/search-params.ts#L114-L162))

## 실제 코드

옛 정적 생성에서 `searchParams` 는 **`then` 을 읽는 순간**을 잡는다.

```ts
// search-params.ts L464-L518
function makeErroringSearchParams(
  workStore: WorkStore,
  prerenderStore: PrerenderStoreLegacy | PrerenderStorePPR
): Promise<SearchParams> {
  const cachedSearchParams = CachedSearchParams.get(workStore)
  if (cachedSearchParams) {
    return cachedSearchParams
  }

  const underlyingSearchParams = {}
  // For search params we don't construct a ReactPromise because we want to interrupt
  // rendering on any property access that was not set from outside and so we only want
  // to have properties like value and status if React sets them.
  const promise = Promise.resolve(underlyingSearchParams)

  const proxiedPromise = new Proxy(promise, {
    get(target, prop, receiver) {
      if (Object.hasOwn(promise, prop)) {
        // The promise has this property directly. we must return it.
        // We know it isn't a dynamic access because it can only be something
        // that was previously written to the promise and thus not an underlying searchParam value
        return ReflectAdapter.get(target, prop, receiver)
      }

      if (typeof prop === 'string' && prop === 'then') {
        const expression =
          '`await searchParams`, `searchParams.then`, or similar'
        if (workStore.dynamicShouldError) {
          throwWithStaticGenerationBailoutErrorWithDynamicError(
            workStore.route,
            expression
          )
        } else if (prerenderStore.type === 'prerender-ppr') {
          // PPR Prerender (no cacheComponents)
          postponeWithTracking(
            workStore.route,
            expression,
            prerenderStore.dynamicTracking
          )
        } else {
          // Legacy Prerender
          throwToInterruptStaticGeneration(
            expression,
            workStore,
            prerenderStore
          )
        }
      }
      return ReflectAdapter.get(target, prop, receiver)
    },
  })

  CachedSearchParams.set(workStore, proxiedPromise)
  return proxiedPromise
}
```

```text
 ★★★ `await searchParams` 를 **Proxy 의 get 덫**으로 감지한다

   await x  는 내부적으로  x.then  을 읽는다
   => prop === 'then' 이면 그것이 곧 "searchParams 를 기다렸다" 는 뜻이다
     dynamicShouldError     => StaticGenBailoutError
     'prerender-ppr'        => postponeWithTracking
     그 밖(legacy)          => throwToInterruptStaticGeneration
   expression 문구 - '`await searchParams`, `searchParams.then`, or similar'

 => 속성 하나하나를 감싸지 않는다. **기다리는 행위 자체**를 동적 접근으로 본다
 ★ 알맹이는 빈 객체 `{}` 다 (L473). 정적 생성에는 쿼리 문자열이 없다
 ★ 그런데 주석(L474-476)은 "interrupt rendering on **any property access**" 라고 하는데
   코드가 검사하는 것은 `then` 하나다 (L488). 주석과 코드가 어긋난다
 ★ L481 `Object.hasOwn(promise, prop)` 이면 그대로 돌려준다 —
   주석 L482-484 - 약속에 **직접 쓰인** 속성이면 밖에서 넣은 것이지 사용자의
   searchParams 접근이 아니다
```

```text
 ★★★ 그 이유가 [02]의 io() 와 **정반대 선택**이다 (주석 L474-476)

   "For search params we don't construct a ReactPromise because we want to interrupt
    rendering on any property access that was not set from outside and so we only
    want to have properties like value and status if **React sets them**."

 io()           약속에 status='fulfilled' · value 를 **미리 박는다** — React 가 안 매달리게
 searchParams   **일부러 안 박는다** — React 가 박으면 그건 React 가 한 것,
                그 밖의 접근은 사용자가 한 것으로 가를 수 있게

 => 같은 React thenable 규약을 한쪽은 **이용**하고 한쪽은 **구분자로** 쓴다
 ※ 두 파일을 나란히 놓은 비교는 내 것이다. 각 주석은 자기 쪽 이유만 적는다

 ★★★ 모던 경로(cacheComponents)의 searchParams 는 **`status` 를 덫으로 잡는다**
   makeHangingSearchParams (SPARAMS L378-462) 의 Proxy
     'then' · 'catch' · 'finally'  => await 류 감지
     'status'                      => L443-449
         expression = '`use(searchParams)`, `searchParams.status`, or similar'
         trackSearchParamsAccessed() + annotateDynamicAccess(...)
   => `use(x)` 는 React 가 x.status 를 읽는다. 그 읽기 자체가 **동적 접근의 증거**다
   => io() 가 `use()` 를 위해 **심어 두는** 그 필드를, searchParams 는 **덫으로 건다**
   ★ 덫에 걸리면 dynamicAccessAsyncStorage 의 abort 도 한다 (L433-438)
```

## 동작 흐름

```text
 팩토리 아홉 (+ use cache 전용 하나)

 params.ts
   L52   createParamsFromClient                  클라이언트 경계
   L132  createServerParamsForMetadata           → L137 createServerParamsForServerSegment 로 위임
   L145  createServerParamsForRoute              라우트 핸들러
   L207  createServerParamsForServerSegment      레이아웃·페이지 (위 위치)
   L268  createPrerenderParamsForClientSegment   클라이언트 세그먼트 prerender
 search-params.ts
   L51   createSearchParamsFromClient            클라이언트 경계
   L104  createServerSearchParamsForMetadata     → L108 createServerSearchParamsForServerPage 로 위임
   L114  createServerSearchParamsForServerPage   페이지 (위 위치)
   L164  createPrerenderSearchParamsForClientPage
   L525  makeErroringSearchParamsForUseCache     [`'use cache'`] [02]가 부르는 것

 ★ …ForMetadata 둘은 **위임만** 한다 — 다른 점은 `getMetadataVaryParamsAccumulator()`
   로 메타데이터 전용 vary 누적기를 넘기는 것뿐이다 (params L136 · search-params L107)
```

```text
 ★★ 호출처가 전부 프레임워크다 (저장소 grep, server/request 밖·테스트 제외)

   server/app-render/create-component-tree.tsx  L831-832 · L854 · L863 · L940 · L1034
   server/app-render/entry-base.ts              L52-57 (재export)
   lib/metadata/resolve-metadata.ts             L769 · L876   (ForMetadata)
   lib/metadata/metadata.tsx                    L57           (ForMetadata)
   server/route-modules/app-route/module.ts     L392          (ForRoute)
   client/components/client-boundary-params.ts  L8-9          (FromClient 를 createClient… 로 재export)

 => 사용자 코드에는 하나도 없다
 ★★ 그래서 **팩토리가** 캐시 스코프에서 불리면 던지는 것이 **InvariantError** 다
   createServerParamsForServerSegment L238  "should not be called in cache contexts."
   cookies() 의 'cache' 갈래                "used `cookies()` inside "use cache"…"  ([01])
 => cookies() 가 캐시 안에서 불리면 **사용자가** 잘못한 것이고,
    params 팩토리가 캐시 안에서 불리면 **프레임워크가** 잘못한 것이다
 ★ 단 `'use cache'` 페이지 안에서 **사용자가** searchParams 를 읽으면 그것은 일반 Error 다 —
   makeErroringSearchParamsForUseCache(L525)가 만든 약속이 던지고 invalidDynamicUsageError 에도
   남긴다 (utils.ts L16-28, search-params.ts L547-551)
 ★ 클라이언트 쪽(client-boundary-params.ts)도 **같은 server/request 파일**을 쓴다
```

```text
 createServerParamsForServerSegment   PARAMS L207

 L218  switch (workUnitStore.type)
 L219    prerender 넷           => createStaticPrerenderParams(...)     L331
 L230    'validation-client'    => InvariantError
 L234    캐시 셋                 => InvariantError
 L240    'generate-static-params' => InvariantError
 L244    'prerender-runtime'    => createRuntimePrerenderParams(...)    L434
 L252    'request'              => createRenderParamsForPage(...)       L487

 createStaticPrerenderParams 의 'prerender' 갈래 (L339-)
   파라미터가 없으면             => 추적 없이 그대로 (L349-352)
   fallback 파라미터가 있으면    => makeHangingParams(...)             (L354-359)
   전부 정적이면 — 아래
```

```text
 ★★★ 파라미터가 **전부 정적이어도 셸에서는 뺀다** (L363-378)

   if (stagedRendering) {
     // Even if all params are static, we need to exclude them from the app shell
     // by delaying them to the static stage. However, root params are allowed in shells,
     // so if all the params are root params, they can be included as well.
     if (!allParamsAreRootParams(underlyingParams, prerenderStore.rootParams)) {
       return stagedRendering.delayUntilStage(
         RENDER_STAGES_BY_DATA_KIND.staticLinkData, 'params', userspaceParams)
     }
   }

 => 값을 **아는데도** 앱 셸 단계에서는 주지 않는다. staticLinkData 단계까지 미룬다
 ★ 판정 단위가 파라미터 하나가 아니라 **객체 전체**다 (params-utils.ts L30-40) —
   비루트 파라미터가 하나라도 섞이면 루트 파라미터까지 **통째로** 미룬다
 ★ `stagedRendering` 이 없으면 이 판정 자체를 안 하고 그냥 값을 준다 (L363 · L380)
 => 앱 셸은 같은 레이아웃을 쓰는 모든 경로가 **공유**하는 것이다.
    `/blog/a` 의 slug 가 박히면 `/blog/b` 가 그 셸을 못 쓴다
    ※ 뒷문장은 내 해석이다. 소스는 "exclude them from the app shell" 까지만 적는다
 ★ 루트 파라미터는 예외다 — [03]에서 본 대로 루트 파라미터는 셸에 들어가도 된다
   ※ "`/[lang]` 은 셸 자체가 언어별로 갈리기 때문" 은 내 해석이다
 ★ `RENDER_STAGES_BY_DATA_KIND` 의 단계 이름(staticLinkData · sessionData · runtimeLinkData)은
   [`'use cache'`] [01]·[03]과 [동적 API] [01]이 쓰는 그 단계 체계다
```

```text
 ★★ 정적 prerender 의 searchParams 에는 **실제 값을 넘기지 않는다** (SPARAMS L125-129)

   case 'prerender' · 'prerender-client' · 'prerender-ppr' · 'prerender-legacy':
     return createStaticPrerenderSearchParams(workStore, workUnitStore)
                                              ↑ underlyingSearchParams 가 **없다**

 createStaticPrerenderSearchParams   L217
   forceStatic 이면                   => Promise.resolve({})
   'prerender' · 'prerender-client'  => makeHangingSearchParams (L378)
   'prerender-ppr' · 'prerender-legacy' => makeErroringSearchParams (위 실제 코드)

 => 정적 결과에는 쿼리 문자열이 **있을 수 없다.** 인자에서부터 받지 않는다
 ★ params 는 빌드 때 아는 값이 있어서 넘기지만, searchParams 는 모르는 게 정상이다
```

## 결과가 쓰이는 곳

```text
 params / searchParams 약속
      --> 페이지·레이아웃의 props. create-component-tree.tsx 가 넘긴다
          (그 흐름은 아직 이 지도에 없다 — 흐름 14 예정)

 staticLinkData 까지 미룬 params
      --> [정적 응답]의 단계별 렌더. 앱 셸에는 안 들어가고 링크 데이터 단계에 들어간다

 makeErroringSearchParams 의 then 덫
      --> 옛 정적 생성(legacy·PPR)에서 `await searchParams` 한 줄이 라우트를 동적으로 만든다

 makeErroringSearchParamsForUseCache (L525)
      --> [`'use cache'`] [02]. public 캐시가 page 의 searchParams 를 대신 넘기는 것

 vary 누적기 (varyParamsAccumulator)
      --> 어떤 파라미터를 읽었는지 기록. 메타데이터는 전용 누적기를 쓴다
```

## 다루지 않는 것

`createRuntimePrerenderParams`(L434) · `createRenderParamsForPage`(L487) · `createRuntimePrerenderSearchParams` · `createRenderSearchParams` 의 본문, `makeHangingParams` 의 약속 구현, `makeHangingSearchParams`(L378) 의 `status` 이외 덫 세부, `createVaryingParams` · `createVaryingSearchParams` 와 `vary-params` 체계, `optionalCatchAllParamName` 처리, `fallback-params.ts`(156줄)의 fallback 파라미터 계산과 `hasFallbackRouteParams`, `instrumentSearchParamsPromiseWithDevWarnings`(L689)의 개발 모드 덫(그 안에도 `then` 검사가 L708 에 있다), `createParamsFromClient`(L52) · `createPrerenderParamsForClientSegment`(L268) 등 클라이언트 쪽 팩토리의 갈래, `pathname.ts` 의 `createServerPathnameForMetadata`, `create-component-tree.tsx` 가 팩토리를 고르는 조건은 이 문서의 범위 밖이다.
