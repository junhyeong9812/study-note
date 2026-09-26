# 02 cacheComponents

상위: [정적 응답을 미리 만들기](../README.md)

894줄로 이 파일에서 가장 큰 단일 갈래다. `cacheComponents` 를 켰을 때만 돈다(**기본값은 꺼짐**). 렌더를 여러 번 돌려 **무엇이 캐시에서 오고 무엇이 요청 때 와야 하는지**를 가려낸다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L8426-L9319 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L8426-L9319))

## 실제 코드

이 갈래의 성격은 맨 앞에서 만드는 것들이 말해 준다.

```tsx
// app-render.tsx L8446-L8467
      const initialServerPrerenderController = new AbortController()

      // This controller is used to abort the React prerender.
      const initialServerReactController = new AbortController()

      // This controller represents the lifetime of the React prerender. Its
      // signal can be used for any I/O operation to abort the I/O and/or to
      // reject, when prerendering aborts. This includes our own hanging
      // promises for accessing request data, and for fetch calls. It might be
      // replaced in the future by React.cacheSignal(). It's aborted after the
      // React controller, so that no pending I/O can register abort listeners
      // that are called before React's abort listener is called. This ensures
      // that pending I/O is not rejected too early when aborting the prerender.
      // Notably, during the prospective prerender, it is different from the
      // prerender controller because we don't want to end the React prerender
      // until all caches are filled.
      const initialServerRenderController = new AbortController()

      // The cacheSignal helps us track whether caches are still filling or we are ready
      // to cut the render off.
      const cacheSignal = new CacheSignal()

```

```text
 AbortController 가 셋, CacheSignal 이 하나 — 다만 **이 갈래 전체에는 열둘**이다
   L8446 · 8449 · 8462   초기 서버
   L8642 · 8643 · 8644   초기 클라이언트
   L8757 · 8758          최종 서버
   L9090 · 9091          최종 클라이언트
   L8490 · 8801          이름 없이 인라인으로

 => 렌더를 **중간에 끊는 것**이 이 갈래의 기본 도구다.
    [04]가 "예외가 나면 포기" 하는 것과 달리,
    여기는 **일부러 끊어서** 어디까지가 캐시로 되는지를 잰다
```

## 동작 흐름

```text
 APPR L8426-9319 — 크게 두 단계다

 --- 1단계: 초기 프리렌더 (캐시를 채운다) ---
 L8446  initialServerPrerenderController = new AbortController()
 L8449  initialServerReactController     = new AbortController()
 L8462  initialServerRenderController    = new AbortController()
 L8466  cacheSignal = new CacheSignal()
 L8472  resumeDataCache: ResumeDataCache = ...
 L8478  initialServerPayloadPrerenderStore: PrerenderStore = {...}
 L8512  initialServerPayload = await workUnitAsyncStorage.run(...)
 L8520  prerenderStore = initialServerPrerenderStore = {...}
 L8547  initialPrerenderOptions = {...}
 L8583  pendingInitialServerResult = workUnitAsyncStorage.run(...)   ★ await 하지 않는다
 L8605  await cacheSignal.cacheReady()
        ★★ **캐시가 다 채워질 때까지** 기다린다. 렌더가 끝나기를 기다리는 것이 아니다
 L8611  workStore.invalidDynamicUsageError 가 있으면 ...
 L8616  initialServerResult (let)
 L8617  try {  ...  } catch (err) { ... }      (L8617-8639)
 L8641  initialServerResult 가 있으면 ... (L8641-8755)

 --- 2단계: 최종 프리렌더 (실제 결과를 만든다) ---
 L8757  finalServerReactController  = new AbortController()
 L8758  finalServerRenderController = new AbortController()
 L8760  varyParamsAccumulator = createResponseVaryParamsAccumulator()
 L8762  finalStageController = new StagedRenderingController({...})
 L8777  runtimeDataAccessed = createPromiseWithResolvers<boolean>()
 L8787  shouldAttemptStaticPrefetch = { current: true }
 L8789  finalServerPayloadPrerenderStore: PrerenderStoreModernServer = {...}
 L8820  shellByteLengthDeferred = createPromiseWithResolvers<...>()
 ... (L8820-9319)
```

```text
 ★★★ 렌더를 두 번 돌린다 — 목적이 다르다

 1단계  **캐시를 채우려고** 돌린다
        `cacheSignal.cacheReady()`(L8605)가 그것을 말한다.
        렌더 완료가 아니라 **캐시 완료**를 기다린다
        그 사이에 `'use cache'` 로 감싼 것들이 전부 계산되어 자리를 잡는다

 2단계  **결과를 만들려고** 돌린다
        이번에는 캐시가 이미 차 있으므로 캐시에서 오는 것과
        요청 때 와야 하는 것이 갈린다

 => [04]는 렌더를 한 번(RSC) + 한 번(HTML) 한다.
    여기는 그 짝을 **두 벌** 돌린다. 그래서 894줄이다
 ※ 두 단계가 정확히 무엇을 주고받는지는 본문을 더 읽어야 안다.
   이 문서는 골격까지만 적는다
```

```text
 ★★ `shouldAttemptStaticPrefetch = { current: true }` (L8787)

 원시값이 아니라 **객체**다. 여러 콜백이 같은 값을 보고 고칠 수 있게 한 것이다
 => 렌더 도중 어딘가에서 이것을 false 로 내리면 정적 프리페치를 포기한다
 ※ 내리는 자리는 확인하지 않았다

 ★ runtimeDataAccessed 는 `createPromiseWithResolvers<boolean>()` 다 (L8777)
 => 렌더가 끝나기 전에 **다른 쪽에서** 이 약속을 풀어 준다.
    "런타임 데이터에 닿았는가" 를 렌더 밖에서 알아야 하기 때문이다
```

## 결과가 쓰이는 곳

```text
 resumeDataCache
      --> [App Router]의 L2864 가 response.renderResumeDataCache 를 본다.
          PPR 재개 때 [동적 응답]으로 넘어간다

 varyParamsAccumulator
      --> 응답이 어떤 파라미터에 따라 갈리는지를 모은다.
          Vary 헤더와 캐시 키에 쓰인다

 shellByteLengthDeferred (L8820)
      --> 이 갈래에 있는 것은 이것 하나다.
          짝인 staticStageByteLengthDeferred 는 **여기 없다** (L1036 · L3607 의 다른 함수들에 있다)
      --> 서버가 읽는 것이 아니라 getRSCPayload 에 shellByteLengthPromise 로 들어가(L8831)
          **RSC 페이로드의 필드가 되어 나간다** (L803-804)
```

## 다루지 않는 것

1단계와 2단계 본문의 세부(L8478-8754 · L8789-9319), `CacheSignal` 과 `cacheReady()` 의 구현, `'use cache'`(`server/use-cache/`)가 캐시를 채우는 과정, `ResumeDataCache` 의 형식과 `createPrerenderResumeDataCache`, `StagedRenderingController` 의 단계 전이, `createResponseVaryParamsAccumulator` 와 `vary-params.ts`(308줄), AbortController 열둘이 각각 **언제** abort 되는지와 `abortOnSynchronousPlatformIOAccess` 류, `PrerenderStoreModernServer` 와 다른 스토어 종류의 차이, `shouldAttemptStaticPrefetch` 를 내리는 자리, `runtimeDataAccessed` 를 푸는 자리는 이 문서의 범위 밖이다.
