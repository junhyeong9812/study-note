# 동적 API 가 값을 내주기까지

상위: [Next.js 아키텍처 지도](../../README.md)

`cookies()` · `headers()` · `connection()` · `io()` · `draftMode()` · 루트 파라미터. 여섯 API 가 **똑같은 모양**을 하고 있다 — 스토어 두 개를 꺼내고, 관문 몇 개를 지나고, `workUnitStore.type` 열한 값으로 switch 를 돈다. 그런데 같은 칸에 든 결말이 API 마다 다르고, 그 차이가 곧 각 API 가 **무엇을 약속하는가**다.

[동적 판별]이 장치(postpone · 중단 · hanging promise)를 모아 둔 곳이라면, 여기는 그 장치를 **골라 쓰는** 곳이다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `CKS` = `server/request/cookies.ts`(318줄), `HDRS` = `.../headers.ts`(320줄), `CONN` = `.../connection.ts`(144줄), `IOAPI` = `.../io.ts`(108줄), `DRAFT` = `.../draft-mode.ts`(274줄), `RPARAMS` = `.../root-params.ts`(235줄), `PARAMS` = `.../params.ts`(917줄), `SPARAMS` = `.../search-params.ts`(793줄), `DRU` = `server/dynamic-rendering-utils.ts`.

## 위치

`packages/next` / `src/server` / `dynamic-rendering-utils.ts` L83-L150 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/dynamic-rendering-utils.ts#L83-L150))

## 실제 코드

매달리는 약속을 만드는 함수가 여럿인데, **본문이 거의 같다.**

```ts
// dynamic-rendering-utils.ts L83-L92
export function makeDynamicHangingPromise<T>(
  signal: AbortSignal,
  route: string,
  expression: string
): Promise<T> {
  return makeHangingPromiseWithError(
    signal,
    new HangingPromiseRejectionError(route, expression)
  )
}
```

```ts
// dynamic-rendering-utils.ts L137-L150
export function makeRuntimeHangingPromise<T>(
  signal: AbortSignal,
  route: string,
  expression: string,
  workUnitStore: WorkUnitStore | null
): Promise<T> {
  if (workUnitStore !== null) {
    trackRuntimeDataAccessed(workUnitStore)
  }
  return makeHangingPromiseWithError(
    signal,
    new HangingPromiseRejectionError(route, expression)
  )
}
```

```text
 ★★★ 차이가 **한 줄**이다 — trackRuntimeDataAccessed(workUnitStore)

   makeDynamicHangingPromise   아무것도 기록하지 않는다
   makeRuntimeHangingPromise   "런타임 요청이었으면 풀렸을 것" 을 기록한다

 => 둘 다 영원히 안 풀리는 약속이고, 렌더가 중단되면 같은 오류로 거절된다
 => 다른 것은 **나중에 누가 이것을 채울 수 있는가** 에 대한 기록뿐이다
 ★ [동적 판별] [01]의 중단 함수 셋 중 하나만 trackRuntimeDataAccessed 를 부른
   것과 **같은 축**이다. 동기 경로와 비동기 경로가 같은 질문에 따로 답한다

 같은 계열이 더 있다 (DRU)
   L83   makeDynamicHangingPromise        기록 없음
   L94   makeUntrackedHangingPromise      기록 없음 — prerender 가 이미 끝난 뒤
   L137  makeRuntimeHangingPromise        trackRuntimeDataAccessed
   L169  makeFallbackParamsHangingPromise trackFallbackParamsAccessed
   L198  makeStageHangingPromise          뒤 단계에서 풀릴 것 (정적 스토어면 runtime 기록)
   L294  makeClientHookHangingPromise     클라이언트 훅 전용 ([동적 판별] [03])
 => 대부분 **무엇을 기록하느냐**로 갈린다 — 예외 둘
    makeDynamicHangingPromise 와 makeUntrackedHangingPromise 는 **본문이 똑같다** (L83-103).
      다른 것은 이름(부르는 자리의 뜻)뿐이다
    makeClientHookHangingPromise 는 거절 오류 자체가 ClientHookDynamicError 로 다르다 (L294-299)
 ★ makeRuntimeHangingPromise 는 `workUnitStore` 에 **null** 을 받을 수 있다 (docstring L123-129).
   그때는 만드는 시점이 아니라 **관측하는 시점**에 호출처가 따로 기록한다 —
   searchParams(SPARAMS L387-403)와 fallback params(PARAMS L737-746)가 그렇게 부른다
 ★ trackRuntimeDataAccessed 가 하는 일은 둘이다 — runtimeDataAccessed 를 풀고(L257)
   정적 프리페치 힌트를 끈다(L267-273). 그리고 **'prerender' 에서만** 한다.
   prerender-runtime 을 포함한 나머지 열 갈래에서는 아무것도 안 한다 (L275-285)
```

## 동작 흐름

```text
 ★★★ 여섯 API × 스토어 열한 종 — 같은 칸, 다른 결말
     (각 파일의 switch 를 스크립트로 뽑아 대조했다)

                     cookies/headers  connection    io          draftMode    rootParam
 request             값               값            값          값           값
 prerender           R 매달림         D 매달림      D 매달림    빈 값        prerender 약속
 prerender-runtime   세션 단계까지    D 매달림      D 매달림    세션 단계까지 값
 prerender-ppr       postpone         postpone      PPR제거오류 빈 값        prerender 약속
 prerender-legacy    중단 throw       중단 throw    값          빈 값        prerender 약속
 prerender-client    Invariant        D 매달림      D 매달림    Invariant    Invariant
 validation-client   Invariant        Invariant     값          Invariant    Invariant
 cache               throw            throw         값          바깥이면 값  값 + 기록
 private-cache       값               **throw**     값          바깥이면 값  값 (+개발 기록)
 unstable-cache      throw            throw         값          바깥이면 값  throw
 generate-static-params throw         throw         값          throw        부모가 주면 값

   R = makeRuntimeHangingPromise   D = makeDynamicHangingPromise
   중단 throw = throwToInterruptStaticGeneration   ([동적 판별] [01])

 ★★ 열이 곧 API 의 성격이다
   cookies/headers  **요청 데이터** — 런타임 요청이면 채울 수 있다 (R)
   connection       **실제 요청이 있어야만** — 런타임 prerender 도 안 된다 (D)
   io               **IO 일 뿐** — 캐시 안이면 채운 시점 값으로 충분하다
   draftMode        **절대 매달리지 않는다** — 모르면 빈 값
   rootParam        **라우트에 묶인 값** — 캐시 키에 들어간다
```

1. [요청 데이터를 읽는 두 API](01_cookies-headers/README.md) — 같은 결말, 다른 관문 순서.
2. [요청이 있다는 것 자체를 묻는 두 API](02_connection-io/README.md) — 캐시 스코프에서 정반대다.
3. [매달리지 않는 둘](03_draft-root/README.md) — draftMode 와 루트 파라미터.
4. [사용자가 부르지 않는 둘](04_params/README.md) — params · searchParams 는 프레임워크가 만들어 넘긴다.

```text
 ★★ switch 앞의 관문도 API 마다 다르다

                  after() 안   forceStatic      dynamicShouldError
 cookies          throw  L39   빈 값  L45       StaticGenBailout L52   → switch L59
 headers          throw  L46   빈 값  L52       (switch① L60 뒤) L92  → switch② L99
 connection       throw  L32   resolve L38      StaticGenBailout L44   → switch L51
 io               throw  L33   -                -                      → switch L38
 draftMode        -            -                -                      → switch L37
 rootParam        (Route Handler · Server Action 에서 throw — L42-58)  → switch L60
                  ★ dynamicShouldError 를 **일부러 무시한다** — 주석 L212-215
                    "even with `dynamic = "error"` we still support generating dynamic fallback shells"

 => `forceStatic` 은 **값을 비워서 돌려준다** — 던지지 않는다.
    "정적으로 만들어라" 는 요청을 "요청 데이터가 없는 척하라" 로 받는다
 ★ headers 만 switch 가 **둘**이다. 그래서 캐시 스코프 + `dynamic = "error"` 에서
   cookies 는 StaticGenBailoutError, headers 는 "used headers() inside use cache"
   로 **서로 다른 오류**를 낸다 ([01])
 ★ io · draftMode · rootParam 에는 두 관문이 **없다** (rootParam 은 위 주석대로 의도적이다)
 ★ io 는 스토어가 **없어도 던지지 않는다** — 브라우저·스크립트에서 즉시 풀린다 (IOAPI L104-107).
   나머지 다섯은 스토어가 없으면 던진다
 ★ 이 시나리오(`dynamic = "error"` + 캐시 스코프)는 cacheComponents 를 켜면 생기지 않는다 —
   cacheComponents 에서는 segment config `dynamic` 자체가 컴파일 오류다
   (crates/next-custom-transforms/src/transforms/react_server_components.rs L956-958)
```

## 결과가 쓰이는 곳

```text
 매달린 약속 (R / D / fallback)
      --> [정적 응답]의 prerender 가 그 자리에서 멈추고 셸을 만든다.
          R 이면 "런타임 프리페치가 더 줄 수 있다" 가 기록돼
          [프리페치]가 PPRRuntime 으로 다시 물을 근거가 된다

 postponeWithTracking · throwToInterruptStaticGeneration
      --> [동적 판별] [01]·[02]. 옛 PPR 과 옛 정적 생성의 경로

 캐시 스코프에서 던진 오류
      --> `workStore.invalidDynamicUsageError ??= error` 로 남긴다 —
          cookies · headers · connection 의 'cache', connection 의 'private-cache'(CONN L70),
          draftMode enable/disable 의 'cache'·'private-cache'(DRAFT L220),
          'use cache' 안의 searchParams(utils.ts L25). 'unstable-cache' 갈래는 남기지 않는다.
          [`'use cache'`] [04]의 버퍼 스트림이 이것을 읽는다

 readRootParamNames (rootParam 의 'cache' 갈래)
      --> [`'use cache'`] [02]·[03]의 `_N_RP_` 리다이렉트 항목. **여기서 처음 쓰인다**

 workUnitStore.asyncApiPromises
      --> 요청 스토어가 미리 만들어 둔 약속. 같은 렌더 안에서 같은 약속 객체를 돌려준다
```

## 다루지 않는 것

`pathname.ts`(174줄)의 `createServerPathnameForMetadata`, `fallback-params.ts`(156줄)의 fallback 파라미터 계산, `utils.ts` 의 `isRequestApiAllowedInCurrentPhase` 판정 규칙, `after()` 의 phase 체계, `RequestCookiesAdapter` · `HeadersAdapter` 와 `areCookiesMutableInCurrentPhase`(서버 액션에서 쿠키 쓰기), `makeHangingPromiseWithError` · `HangingPromiseRejectionError` 의 본문, `trackRuntimeDataAccessed` · `trackFallbackParamsAccessed` 가 기록한 값을 읽는 쪽, `stagedRendering.delayUntilStage` 와 `RENDER_STAGES_BY_DATA_KIND` 의 단계 정의, `asyncApiPromises` 를 만드는 쪽(요청 스토어 생성), `next/root-params` 를 컴파일러가 만드는 과정(`build/webpack-config.ts` · `server/config.ts`), `accumulateRootVaryParam` 과 `vary-params`, `fallback-params.test.ts` 는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 요청 데이터를 읽는 두 API](01_cookies-headers/README.md)
- [02 요청이 있다는 것 자체를 묻는 두 API](02_connection-io/README.md)
- [03 매달리지 않는 둘](03_draft-root/README.md)
- [04 사용자가 부르지 않는 둘](04_params/README.md)
