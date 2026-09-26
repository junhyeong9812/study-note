# 03 매달리지 않는 둘

상위: [동적 API 가 값을 내주기까지](../README.md)

`draftMode()` 와 루트 파라미터는 [README] 표에서 **매달리는 칸이 거의 없다.** 모르면 빈 값을 주거나(draftMode), 대부분 이미 알고 있다(루트 파라미터). 대신 둘 다 **다른 곳에 선을 긋는다** — draftMode 는 읽기와 쓰기 사이에, 루트 파라미터는 라우트와 라우트 아닌 것 사이에.

## 위치

`packages/next` / `src/server/request` / `draft-mode.ts` L28-L91 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/request/draft-mode.ts#L28-L91))

`packages/next` / `src/server/request` / `root-params.ts` L26-L202 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/request/root-params.ts#L26-L202))

## 실제 코드

루트 파라미터가 prerender 에서 매달리는 경우는 **하나뿐**이다.

```ts
// root-params.ts L158-L173
    case 'prerender': {
      // We are in a cacheComponents prerender.
      // The param is a fallback, so it should be treated as dynamic.
      if (
        prerenderStore.fallbackRouteParams &&
        prerenderStore.fallbackRouteParams.has(paramName)
      ) {
        return makeFallbackParamsHangingPromise<ParamValue>(
          prerenderStore.renderSignal,
          workStore.route,
          apiName,
          prerenderStore
        )
      }
      break
    }
```

```text
 ★★★ fallback 파라미터일 때**만** 매달린다

   prerenderStore.fallbackRouteParams.has(paramName) 이면
     => makeFallbackParamsHangingPromise(...)
   아니면 break(L172) → L200-201
     accumulateRootVaryParam(paramName)
     return Promise.resolve(underlyingParams[paramName])   ← **값을 그대로 준다**

 => 정적 prerender 에서 cookies() 는 무조건 매달리는데,
    루트 파라미터는 빌드 때 이미 아는 값이라 **그냥 준다**
 ★ 매달리는 경우 — fallback 셸(`/[lang]` 을 아직 모르는 채로 미리 만드는 셸)에서
   그 파라미터를 읽을 때다. 그때만 "구체적 prerender 가 채울 것" 을 기록한다
 ★ makeFallbackParamsHangingPromise 는 [README]의 여섯 변형 중 하나다 —
   docstring 이 "on a fallback-upgradeable route the access is **transient** (a concrete
   prerender resolves it), so it leaves the hint intact" 라고 적는다 (DRU L157-159)
```

## 동작 흐름

```text
 draftMode()   DRAFT L28

 L33   스토어가 없으면 => throwForMissingRequestStore (L34)
       ★ cookies · headers · connection · io 는 `if (workStore) { … }` 로 감싸고,
         draftMode 와 getRootParam(L30 · L35) 은 스토어부터 **먼저** 확인해 던진다
 L37   switch (workUnitStore.type)
 L38     'prerender-runtime'   => stagedRendering.delayUntilStage(sessionData, ...)
 L51     'request'             => createOrGetCachedDraftMode(workUnitStore.draftMode, ...)
 L54     'cache' · 'private-cache' · 'unstable-cache'
 L60       getDraftModeProviderForCacheScope(workStore, workUnitStore) 가 있으면 그것
           주석 L57-59 - "draft mode is available if the outmost work unit store is a
             request store (or a runtime prerender), and if draft mode is enabled"
           없으면 **아래로 떨어진다** (eslint-disable no-fallthrough)
 L71     'prerender' · 'prerender-ppr' · 'prerender-legacy'
           => createOrGetCachedDraftMode(null, ...)   ← **빈 draft mode**
 L76     'prerender-client' · 'validation-client' => InvariantError
 L83     'generate-static-params'                  => throw

 ★ forceStatic · dynamicShouldError 관문이 **없다.** 그리고 어느 갈래도 매달리지 않는다
 => draftMode() 를 **읽는** 것은 prerender 를 막지 않는다. 빈 값이면 "꺼져 있음" 이다
```

```text
 ★★★ 읽기는 공짜, **쓰기**는 추적한다

 DraftMode 의 enable() · disable()
   L164  trackDynamicDraftMode('draftMode().enable()', this.enable)
   L170  trackDynamicDraftMode('draftMode().disable()', this.disable)

 trackDynamicDraftMode(expression, constructorOpt)   L192
   주석 L197-198 - "We have a store we want to track dynamic data access to ensure
     we don't statically generate routes that manipulate draft mode."
   after() phase 이면                  => throw  (읽기는 되지만 켜고 끌 수 없다)
                                         ★ 판정이 `workUnitStore?.phase === 'after'` **직접 비교**다 (L199).
                                           나머지 API 는 isRequestApiAllowedInCurrentPhase(utils.ts L30-68)를
                                           써서 Route Handler·Server Action 의 after 는 허용하는데,
                                           draftMode enable/disable 만 그 예외를 못 받는다
   dynamicShouldError 이면             => StaticGenBailoutError   L205
   'cache' · 'private-cache'           => throw
       "The enabled status of `draftMode()` can be read in caches but you must not
        enable or disable `draftMode()` inside a cache."
   'unstable-cache'                    => throw (같은 취지)
   'prerender' · 'prerender-runtime'   => **abortAndThrowOnSynchronousRequestDataAccess** (L233)
   'prerender-client' · 'validation-client' => InvariantError (L240-245)
   'prerender-ppr'                     => postponeWithTracking (L246-251)
   'prerender-legacy'                  => revalidate = 0 뒤 DynamicServerError 를 **인라인으로** 만들어 throw
                                          (L252-261) — [동적 판별] [01]의 throwToInterruptStaticGeneration
                                          본문을 그대로 복제한 것이다
   'request'                           => trackDynamicDataInDynamicRender (L262-264)

 => 관문이 draftMode() 가 아니라 **enable/disable 에 붙어 있다**
 => 켜고 끄는 것은 응답(쿠키)을 바꾸는 일이므로 정적으로 만들 수 없다
 ★ prerender 에서는 [동적 판별] [01]의 중단 함수 셋 중 **런타임을 기록하는 쪽**으로 간다.
   흐름 11 감사가 찾은 그 호출처(draft-mode.ts:233)가 여기다
 ★★ 그런데 그 함수의 전제가 draftMode 에는 **맞지 않는다.** 전제는 "런타임 prerender 였으면
   이 지점을 지나 렌더했을 것"(dynamic-rendering.ts L365-371)인데, enable/disable 은
   **prerender-runtime 에서도** 같은 함수로 중단된다 (L228-229)
   그리고 trackRuntimeDataAccessed 는 'prerender' 에서만 기록하고 prerender-runtime 에서는
   아무것도 안 한다 (DRU L275-285)
   ※ 그래서 정적 prerender 에서는 런타임 프리페치가 채우러 올 것이라 기록되지만
     실제로는 런타임 prerender 도 이 자리에서 멈춘다 — 헛 기록이 될 수 있다.
     DRU L119-121 이 과잉 기록의 대가를 "중복 런타임 프리페치 한 번" 으로 적는다
 ★ 오류 문구가 "without first calling `await connection()`" 이다 (L231) —
   draft mode 를 바꾸려면 먼저 실제 요청임을 선언하라는 처방이다
```

```text
 ★★★ 그 "캐시" 는 **한 번도 채워지지 않는다**

   const CachedDraftModes = new WeakMap<CacheLifetime, Promise<DraftMode>>()   L114
   createOrGetCachedDraftMode   L93
     L98   const cachedDraftMode = CachedDraftModes.get(cacheKey)
           있으면 돌려주고, 없으면 새로 만들어 돌려준다 — **set 하지 않는다**

 => 저장소 전체에 `CachedDraftModes.set` 이 **없다** (grep)
 => cookies · headers 는 같은 WeakMap 수법으로 같은 약속을 재사용하는데 ([01]),
    draftMode 는 이름만 get·set 짝을 흉내 내고 **부를 때마다 새 약속**을 만든다
 ※ 의도인지 빠뜨린 것인지 소스에 흔적이 없다

 ★★ 동기 접근 덫이 cookies 와 **다른 방식**이다

 cookies()     Object.defineProperties(promise, { get, getAll, … })   ([01])
 draftMode()   new Proxy(promise, { get(target, prop, receiver) { switch (prop) … } })  L123

 => 같은 목적(await 없이 쓰는 옛 사용법 경고)에 **두 기법**이 쓰인다
 ★ draftMode 는 속성이 셋(isEnabled · enable · disable)뿐이라 Proxy 의 switch 로 충분하다
 ★ 이 덫은 `isPrefetchRequest` 이면 붙지 않는다 (L104)
 ※ 뒷문장은 내 추론이다. 두 기법을 고른 이유는 소스에 없다
```

```text
 getRootParam(paramName)   RPARAMS L26

 docstring L22-25 - "Used for the compiler-generated `next/root-params` module."
   => 사용자는 이 함수를 부르지 않는다. `import { lang } from 'next/root-params'` 를
      컴파일러가 이 함수 호출로 바꾼다

 L30   workStore 없음        => InvariantError
 L35   workUnitStore 없음    => Error "outside of a Server Component"
 L42   actionStore 가 있으면
 L43     isAppRoute          => throw  Route Handler 는 아직 지원하지 않는다 (TODO)
 L49     isAction && phase === 'action' => throw
         주석 L50-51 - "Actions are not fundamentally tied to a route (even if they're
           always submitted from some page), so root params would be inconsistent if an
           action is called from multiple roots."
 L60   switch (workUnitStore.type)
 L66     'cache'   rootParams 가 없으면 throw (unstable_cache 안에 중첩된 경우)
 L72               **workUnitStore.readRootParamNames.add(paramName)**
 L73               => Promise.resolve(rootParams[paramName])
 L75     prerender 셋 => createPrerenderRootParamPromise (위 실제 코드)
 L91     'request'  instant 검증 샘플이 있으면 assertRootParamInSamples (L100)
 L111    'private-cache'  개발이면 readRootParamNames.add (L115)
 L122    'generate-static-params'  부모 generateStaticParams 가 준 것이 아니면 throw
 L135  accumulateRootVaryParam(paramName)
 L136  => Promise.resolve(workUnitStore.rootParams[paramName])
```

```text
 ★★★ L72 가 [`'use cache'`]의 리다이렉트 항목이 **시작되는 곳**이다

   case 'cache':
     workUnitStore.readRootParamNames.add(paramName)

 => `'use cache'` 함수 안에서 `lang()` 을 부르면 그 이름이 캐시 스토어에 남는다
 => [`'use cache'`] [04]의 collectResult 가 이것을 `readRootParamNames` 로 모으고,
    [03]이 `_N_RP_lang` 태그로 리다이렉트 항목에 실어 보낸다
 => 그래서 같은 함수를 `/en` 과 `/ko` 에서 부르면 **다른 캐시 항목**이 된다
 ★ 캐시 키에 파라미터를 넣으라고 사용자가 적을 필요가 없다 — **읽은 것이 곧 키**다
 ★ 그리고 'cache' 갈래는 L73 에서 **먼저 return** 한다 — 아래 L135 의
   accumulateRootVaryParam 을 **부르지 않는다.** 캐시 안에서는 vary 대신
   readRootParamNames 로 기록이 간다
 ★ readRootParamNames 에 쓰는 곳은 셋이다 — L72(사용자 접근), L115(private 캐시,
   개발 서버에서 필드가 있을 때만 — use-cache-wrapper.ts L772), 그리고 중첩 캐시가
   바깥으로 전파하는 use-cache-wrapper.ts L985 ([`'use cache'`] [04])
 ★ [`'use cache'`] [02]의 TODO 가 "쿠키·헤더도 root params 처럼 읽은 것만 기록하자" 고
   적은 **그 방식**이 이것이다
```

```text
 ★★ 여섯 API 중 generateStaticParams 안에서 **값을 내주는 유일한 것**이다

   cookies · headers · connection · draftMode  => 'generate-static-params' 에서 throw
   io                                          => 즉시 풀림 (값이 없으니 해가 없다)
   getRootParam                                => 부모가 준 파라미터면 **값**

 L125  (오류 문구) "In `generateStaticParams`, root params are only available for segments
   nested below the segment that provides them."
 => L123 이 검사하는 것은 `paramName in workUnitStore.rootParams` 뿐이다
 ※ `/[lang]/[slug]` 에서 `[lang]` 의 generateStaticParams 가 먼저 돌아 rootParams 를
   채운다는 인과는 이 파일에서 확인하지 않았다. 오류 문구가 그렇게 말할 뿐이다
```

```text
 ★ createPrerenderRootParamPromise 첫머리의 **빈 switch** (L148-153)

   switch (prerenderStore.type) {
     case 'prerender':
     case 'prerender-legacy':
     case 'prerender-ppr':
     default:
   }

 => 본문이 없다. 아무 일도 안 한다
 ※ 타입 좁히기나 남은 코드로 보인다. 소스에 이유가 없다 — 바로 아래 L157 에
   같은 값으로 **실제** switch 가 다시 있다
```

## 결과가 쓰이는 곳

```text
 빈 draft mode (createOrGetCachedDraftMode(null))
      --> prerender 결과에 "draft mode 꺼짐" 으로 박힌다

 abortAndThrowOnSynchronousRequestDataAccess (enable/disable)
      --> [동적 판별] [01]. prerender 를 중단하고 **런타임 기록을 남긴다**

 readRootParamNames
      --> [`'use cache'`] [02]·[03]·[04]. 리다이렉트 항목과 구체적 캐시 키

 accumulateRootVaryParam(paramName)
      --> 응답이 이 루트 파라미터로 **갈린다**는 표시. vary-params 로 간다

 makeFallbackParamsHangingPromise
      --> fallback 셸의 구멍. 구체적 prerender 가 채운다
```

## 다루지 않는 것

`DraftMode` 클래스와 `DraftModeProvider` 가 쿠키로 draft mode 를 켜고 끄는 구현, `getDraftModeProviderForCacheScope` 의 판정, `NullDraftMode` 의 쓰임, draftMode 의 덫 Proxy 세부(L116-144), `makeErroringRootParamPromise`(L205)가 옛 PPR 에서 오류를 내는 방식, `accumulateRootVaryParam` 과 `app-render/vary-params`, `assertRootParamInSamples`(`instant-validation/instant-samples`), 컴파일러가 `next/root-params` 모듈을 생성하는 과정(`build/webpack-config.ts` · `server/config.ts` · `server/lib/router-utils/root-params-type-utils.ts`)은 이 문서의 범위 밖이다.
