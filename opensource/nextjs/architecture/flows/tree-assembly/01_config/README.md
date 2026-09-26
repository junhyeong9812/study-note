# 01 세그먼트 설정 읽기

상위: [트리를 조립하고 세그먼트로 자르기까지](../README.md)

`export const dynamic = 'force-static'` 같은 한 줄이 어디서 읽히는가. 트리를 조립하는 함수가 **세그먼트마다** 그 모듈을 불러온 직후에 읽고, `workStore` 의 플래그를 세운다. [동적 API]의 cookies · headers · connection 이 switch 앞에서 확인하는 `forceStatic` · `dynamicShouldError` 가 **여기서 태어난다.**

★★ 단 "세그먼트마다" 는 **트리 전체를 조립할 때**(초기 HTML · prerender)의 이야기다. **동적** 내비게이션 RSC 요청은 walk-tree-with-flight-router-state.tsx 가 갈라지는 세그먼트부터만 createComponentTree 를 부른다(L239 · L264). (PPR 프리페치는 라우터 상태를 받지 않아 루트부터 그리고, 정적 라우트의 RSC 요청은 빌드 때 페이로드를 캐시에서 준다 → [중간부터 그리기]) 그 **위** 레이아웃의 `dynamic` · `revalidate` · `fetchCache` 는 그 요청에서 **읽히지 않는다.**

## 위치

`packages/next` / `src/server/app-render` / `create-component-tree.tsx` L253-L386 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/create-component-tree.tsx#L253-L386))

## 실제 코드

`dynamic` 문자열 하나가 갈래 셋으로 갈린다.

```tsx
// create-component-tree.tsx L266-L290
  if (typeof dynamic === 'string') {
    // the nested most config wins so we only force-static
    // if it's configured above any parent that configured
    // otherwise
    if (dynamic === 'error') {
      workStore.dynamicShouldError = true
    } else if (dynamic === 'force-dynamic') {
      workStore.forceDynamic = true

      // TODO: (PPR) remove this bailout once PPR is the default
      if (workStore.isStaticGeneration && !experimental.isRoutePPREnabled) {
        // If the postpone API isn't available, we can't postpone the render and
        // therefore we can't use the dynamic API.
        const err = new DynamicServerError(
          `Page with \`dynamic = "force-dynamic"\` won't be rendered statically.`
        )
        workStore.dynamicUsageDescription = err.message
        workStore.dynamicUsageStack = err.stack
        throw err
      }
    } else {
      workStore.dynamicShouldError = false
      workStore.forceStatic = dynamic === 'force-static'
    }
  }
```

```text
 ★★★ 세 갈래가 **서로 다른 플래그**를 건드린다

   'error'          dynamicShouldError = true                   (나머지 둘은 안 건드린다)
   'force-dynamic'  forceDynamic       = true                   (나머지 둘은 안 건드린다)
   그 밖 ('auto' · 'force-static')
                    dynamicShouldError = false
                    forceStatic        = (dynamic === 'force-static')
                                                                (forceDynamic 은 안 건드린다)

 주석 L267-269 - "the nested most config wins so we only force-static if it's configured
   above any parent that configured otherwise"

 => 이 함수는 부모 세그먼트에서 먼저 돌고, 자식은 부모 본문 안의 L585 에서 불린다
    ([02]). 그러니 같은 플래그는 **안쪽이 나중에 써서 이긴다**
 ★★ 그런데 "안쪽 설정 전체가 이긴다" 는 아니다. 갈래마다 건드리는 플래그가 달라서
   **플래그마다** 마지막 쓴 쪽이 이긴다
 ※ 코드에서 도출한 예 (실행해 보지 않았다)
     부모 'force-static' · 자식 'error'
       부모: forceStatic = true, dynamicShouldError = false
       자식: dynamicShouldError = true            ← forceStatic 은 **true 로 남는다**
     그리고 cookies() 는 forceStatic 을 dynamicShouldError **보다 먼저** 본다
       ([동적 API] [README] 관문표 — CKS L45 가 L52 보다 앞)
     => 이 조합에서 cookies() 는 빈 쿠키를 돌려주고, 자식의 'error' 는 드러나지 않는다
     부모 'force-dynamic' · 자식 'force-static'
       => (요청 시점 렌더에서) forceDynamic 과 forceStatic 이 **둘 다 true** 가 된다.
          정적 생성에서는 부모가 L276-285 에서 먼저 던지므로 자식까지 가지 않는다
     ★ 이 도출은 **트리 전체 조립**에서만 성립한다. 소프트 내비게이션 RSC 요청이면
       부모의 'force-static' 이 아예 안 읽혀 forceStatic 은 undefined 로 남는다 —
       그러면 자식 'error' 때문에 cookies() 가 StaticGenBailoutError 를 던진다
       (위 리드 참조. 코드에서 도출했고 실행하지 않았다)
 ★ forceStatic 은 **세 값**이다 — 초기값 undefined(work-async-storage.external.ts L42),
   'auto' 를 명시하면 false(L288). app-render L3223 은 `forceStatic === false` 를 따로 본다
```

## 동작 흐름

```text
 CCTREE L253-386

 L253  let dynamic = layoutOrPageMod?.dynamic

 L255  nextConfigOutput === 'export' 이면
 L256    dynamic 이 없거나 'auto' 면   => dynamic = 'error'      L257
 L258    'force-dynamic' 이면         => throw StaticGenBailoutError
           "`output: "export"` requires all pages be renderable statically because
            there is no runtime server to dynamically render routes in this output format. …"

 L266  typeof dynamic === 'string' 이면 — 위 실제 코드
 L276    'force-dynamic' + 정적 생성 중 + PPR 꺼짐 이면
           => throw DynamicServerError("won't be rendered statically")   L279-284
           주석 L275 - "TODO: (PPR) remove this bailout once PPR is the default"

 L292  fetchCache 가 문자열이면 => workStore.fetchCache = …            L293
 L296  revalidate 가 있으면     => validateRevalidate(...)
 L300  revalidate 가 숫자면
 L311    prerender 넷에서 workUnitStore.revalidate > 이 값 이면 덮어쓴다 — **최솟값**
 L331    forceStatic 아님(L332) + 정적 생성(L333) + revalidate === 0 + PPR 꺼짐(L337) 이면
 L342      => throw DynamicServerError(`revalidate: 0 configured ${segment}`)   (문구 L339)

 L349  페이지이고 unstable_dynamicStaleTime 이 숫자면
 L362    prerender 넷 · request 에서 stale > 이 값 이면 덮어쓴다 — **최솟값**
         주석 L346-348 - "Read unstable_dynamicStaleTime from page modules (not layouts)"
```

```text
 ★★ `output: 'export'` 는 기본값을 **'error' 로 바꾼다** (L255-257)

 => 정적 내보내기에서는 `dynamic` 을 안 적은 모든 페이지가 `dynamic = "error"` 처럼 동작한다
 => 그래서 export 빌드에서 cookies() 를 쓰면 StaticGenBailoutError 로 멈춘다 —
    단 경로 위 어느 세그먼트든 'force-static' 이면 forceStatic 이 true 로 남아
    cookies.ts L45 가 먼저 걸려 빈 쿠키를 돌려준다
 ★ 'error' 로 바뀌는 것은 "모든 페이지" 가 아니라 모듈이 없는 세그먼트까지 포함한 **모든 세그먼트**다
   (`!dynamic` 조건)
    ([동적 API] [01] — cookies.ts L52)
 ★ 'force-dynamic' 은 export 와 **양립할 수 없어서** 여기서 바로 던진다.
   런타임 서버가 없으니 동적으로 그릴 곳이 없다 (오류 문구가 그렇게 적는다)
 ★ 흐름 12 감사가 짚은 대로, cacheComponents 에서는 `dynamic` 설정 자체가
   컴파일 오류다 (react_server_components.rs L956-958). 이 구획은 cacheComponents 이전의
   모형을 떠받치고 있다
```

```text
 ★★ revalidate 와 stale 은 **세그먼트를 내려가며 최솟값으로 좁아진다**

   L311  if (workUnitStore.revalidate > defaultRevalidate) workUnitStore.revalidate = defaultRevalidate
   L362  if (workUnitStore.stale > pageStaleTime)         workUnitStore.stale = pageStaleTime

 => 레이아웃이 3600 이고 페이지가 60 이면 60 이다. 늘릴 수 없다
 => [`'use cache'`] [04]의 cacheLife 가 쓰는 **같은 규칙**이다 — 수명은 좁아지기만 한다
 ★ 'request' 에서는 revalidate 를 **안 쓴다** — 주석 "A request store doesn't have a
   revalidate property" (L316). stale 은 쓴다 (L367-372)
 ★ 두 switch 가 똑같이 적는다 — "createComponentTree is not called for these stores:"
   (L318 · L374). 캐시 스코프 · 클라이언트 · generateStaticParams 에서는 이 함수 자체가
   불리지 않는다
```

```text
 ★ `unstable_dynamicStaleTime` 은 **페이지에서만** 읽는다 (L349-351)

 => 레이아웃에 적어도 무시된다. `isPage &&` 가 조건이다
 => 이 값이 `workUnitStore.stale` 을 좁히고, 그것이 [응답 나가기]의
    Next-Router-Stale-Time 헤더와 [프리페치]의 StaleTimeIterable 로 간다
    (주석 L347-348 "This affects the segment cache stale time via the StaleTimeIterable")
```

## 결과가 쓰이는 곳

```text
 workStore.dynamicShouldError
      --> [동적 API] cookies · headers · connection 의 관문과
          [동적 판별] [01] markCurrentScopeAsDynamic L204

 workStore.forceStatic
      --> [동적 API] cookies · headers · connection 이 **빈 값**을 돌려주는 조건,
          [동적 API] [04] createStaticPrerenderSearchParams 의 `Promise.resolve({})`

 workStore.forceDynamic
      --> [동적 판별] [01] markCurrentScopeAsDynamic L202 의 조기 return

 workUnitStore.revalidate · stale
      --> [응답 나가기]의 Cache-Control · Next-Router-Stale-Time

 workStore.fetchCache
      --> fetch 패치(`lib/patch-fetch.ts`)가 fetch 마다 캐시 여부를 정할 때
```

## 다루지 않는 것

`validateRevalidate` 의 검사 규칙, `fetchCache` 값이 `patch-fetch.ts` 에서 해석되는 방식, `experimental.isRoutePPREnabled` 를 정하는 쪽, `nextConfigOutput === 'export'` 빌드 경로 전체, cacheComponents 에서 segment config 를 컴파일 오류로 만드는 SWC 변환(`react_server_components.rs`), 병렬 슬롯끼리 같은 플래그를 서로 다르게 쓸 때의 순서(형제 슬롯은 `Promise.all` 안에서 돈다 — [02])는 이 문서의 범위 밖이다.
