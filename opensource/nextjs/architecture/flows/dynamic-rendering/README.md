# 무엇이 동적인지 가려내기

상위: [Next.js 아키텍처 지도](../../README.md)

[App Router]·[동적 응답]·[정적 응답]·[`'use cache'`] 네 흐름이 전부 "여기서 다루지 않는다" 며 가리킨 곳이다. 동적 API 를 하나 썼을 때 렌더 전체가 동적이 되는지, 일부만 구멍이 되는지, 빌드가 실패하는지를 이 1592줄이 정한다.

★ 이 파일은 **장치**를 모아 둔 곳이지 `cookies()` 의 구현이 아니다. `cookies()` 같은 ② 계열 API 는 `server/request/` 에서 자기 switch 를 돌며 여기 함수들을 **골라 쓴다**.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `DYNR` = `server/app-render/dynamic-rendering.ts`(1592줄).

## 위치

`packages/next` / `src/server/app-render` / `dynamic-rendering.ts` L1-L21 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/dynamic-rendering.ts#L1-L21))

## 실제 코드

파일 맨 위 21줄이 이 모듈 전체의 설계를 말한다.

```ts
// dynamic-rendering.ts L1-L21
/**
 * The functions provided by this module are used to communicate certain properties
 * about the currently running code so that Next.js can make decisions on how to handle
 * the current execution in different rendering modes such as pre-rendering, resuming, and SSR.
 *
 * Today Next.js treats all code as potentially static. Certain APIs may only make sense when dynamically rendering.
 * Traditionally this meant deopting the entire render to dynamic however with PPR we can now deopt parts
 * of a React tree as dynamic while still keeping other parts static. There are really two different kinds of
 * Dynamic indications.
 *
 * The first is simply an intention to be dynamic. unstable_noStore is an example of this where
 * the currently executing code simply declares that the current scope is dynamic but if you use it
 * inside unstable_cache it can still be cached. This type of indication can be removed if we ever
 * make the default dynamic to begin with because the only way you would ever be static is inside
 * a cache scope which this indication does not affect.
 *
 * The second is an indication that a dynamic data source was read. This is a stronger form of dynamic
 * because it means that it is inappropriate to cache this at all. using a dynamic data source inside
 * unstable_cache should error. If you want to use some dynamic data inside unstable_cache you should
 * read that data outside the cache and pass it in as an argument to the cached function.
 */
```

```text
 ★★★ 동적 표시가 **두 종류**다

 ① "동적이고 싶다" 는 의사 표시 (intention to be dynamic)
      예: unstable_noStore
      현재 스코프가 동적이라고 선언할 뿐이라
      **unstable_cache 안에 있으면 여전히 캐시된다**

 ② "동적 데이터 원천을 읽었다" (a dynamic data source was read)
      더 강한 형태다. 아예 캐시하면 안 된다는 뜻이다
      캐시 스코프 안에서 쓰면 **오류가 나야 한다**

 원문 - "using a dynamic data source inside unstable_cache should error.
   If you want to use some dynamic data inside unstable_cache you should
   read that data outside the cache and pass it in as an argument to the
   cached function."

 => ①은 캐시 경계가 삼켜 버리고, ②는 캐시 경계를 뚫는다
 ★ 그리고 ①에 대해 "기본을 동적으로 바꾸면 이 표시는 없애도 된다" 고 적는다 —
   캐시 스코프 안에서만 정적일 수 있고, 이 표시는 거기에 영향을 못 주기 때문이다
 ★★ PPR 이 이 모듈의 존재 이유다 — 원문이 "전통적으로는 렌더 전체를 동적으로
   떨어뜨렸지만 PPR 로 트리의 **일부만** 동적으로 떨어뜨릴 수 있게 됐다" 고 적는다
```

## 동작 흐름

```text
 dynamic-rendering.ts 1592줄

 L87-164    상태 세 벌
              DynamicAccess          expression + (디버그면) stack
              DynamicTrackingState   RSC 렌더 중 쌓는 것
              DynamicValidationState SSR 렌더 중 쌓는 것
 L165-394   **표시하고 끊는다**                                  [01]
 L396-554   postpone 과 오류로 흐름을 끊는다                      [02]
 L556-765   신호와 훅 (createHangingInputAbortSignal ·
              useDynamicRouteParams · useDynamicSearchParams)
 L767-918   **컴포넌트 스택을 정규식으로 읽는다**                  [03]
 L920-1313  구멍이 어디서 났는지 기록한다 (Navigation · RuntimeShell · StaticShell)
 L1315-1592 **정적 셸을 못 만들었으면 빌드를 세운다**              [04]
```

1. [표시하고 끊는다](01_mark/README.md) — 같은 호출이 렌더 모드마다 다르게 끝난다.
2. [흐름을 끊는 두 오류](02_interrupt/README.md) — 문자열로 알아보는 것과 digest 로 알아보는 것.
3. [컴포넌트 스택을 정규식으로 읽는다](03_stack/README.md) — 마커 컴포넌트를 심어 두고 스택에서 찾는다.
4. [정적 셸을 못 만들었을 때](04_verdict/README.md) — 언제 빌드가 멈추고 언제 봐주는가.

```text
 ★★★ 뒤 두 구획이 **추적 하나에 판정 하나씩, 세 짝**이다

   trackAllowedDynamicAccess(L865)        --> throwIfDisallowedDynamic(L1342)
     app-render.tsx L9155 · L9934              app-render.tsx L9201 · L9981
   trackDynamicHoleInRuntimeShell(L1158)  --> getStaticShellDisallowedDynamicReasons(L1411)
   trackDynamicHoleInStaticShell(L1223)        app-render.tsx L7028 · L7037
   trackDynamicHoleInNavigation(L960)     --> getNavigationDisallowedDynamicReasons(L1479)
     app-render.tsx L7271

 => 판정 함수 셋이 **중복이 아니라 각자의 짝**이다.
    쌓는 쪽과 읽는 쪽이 같은 상태 객체를 공유하므로 둘이 함께 움직인다
 ★★ 그리고 쌓는 필드가 갈린다 — trackAllowedDynamicAccess 만
   `hasDynamicMetadata`(boolean)를 세우고(L878), 나머지 둘은
   `dynamicMetadata`(Error 객체)를 세운다(L1176 · L1241).
   그래서 판정 쪽 조건도 서로 다르다 ([04] 참조)
```

```text
 ★ 구멍의 종류가 셋이다 (DYNR L920-927) — **즉시 검증 경로 전용**이다

   DynamicHoleKind.Link    = 1   링크 데이터 때문이다
   DynamicHoleKind.Runtime = 2   런타임 데이터 때문이다
   DynamicHoleKind.Dynamic = 3   동적 데이터 때문이다

 ★★★ 이 값은 **구멍을 보고 정하는 것이 아니다.** 인과가 반대다 —
   app-render.tsx L7232-7246 이 `ValidationPrefetchKind` 와
   `payloadResult.hasAmbiguousErrors` 로 미리 정해 넘긴다
     Shell            + 모호한 오류 => Link,    아니면 Dynamic
     LegacySpeculative + 모호한 오류 => Runtime, 아니면 Dynamic
 => 즉 "**어떤 프리페치를 검증하는 중인가**" 가 hole kind 를 정한다
 ★ 이 파일 안에서 이 값이 하는 일은 `trackDynamicHoleInNavigation` 이
   **오류 문구를 고르는 것**뿐이다 (L985-989 · L998-1002 · L1094-1098)
 ★ 그리고 이 열거는 `trackDynamicHoleInNavigation` 한 곳에서만 쓰인다.
   흐름 전체의 구멍 분류가 아니다
```

## 결과가 쓰이는 곳

```text
 postpone (React.unstable_postpone)
      --> [정적 응답]의 PPR 이 그 자리를 구멍으로 남기고 셸을 완성한다

 AbortController.abort(오류)
      --> [정적 응답]의 cacheComponents prerender 가 통째로 중단된다.
          그 신호가 [`'use cache'`]의 `renderSignal` 이다

 DynamicServerError / StaticGenBailoutError
      --> 옛 경로(prerender-legacy)와 `dynamic = "error"` 설정.
          던져서 정적 생성을 포기시킨다

 workStore.dynamicUsageDescription / dynamicUsageStack
      --> 빌드 로그의 "이 라우트가 왜 동적인가" 문구

 DynamicValidationState.dynamicErrors
      --> [04]가 빌드를 세울지 정할 때 읽는다

 createHangingInputAbortSignal 이 만든 AbortSignal
      --> [`'use cache'`]가 인자를 인코딩하다 **중단**할 때 쓰는 신호다 (docstring L566-570).
          약속 자체를 만드는 것은 `dynamic-rendering-utils.ts` 의 `make*HangingPromise` 계열
```

## 다루지 않는 것

`useDynamicRouteParams`(L647) · `useDynamicSearchParams`(L711)의 클라이언트 훅 경로와 `makeClientHookHangingPromise`, `createHangingInputAbortSignal`(L571-628)의 세 오버로드와 신호 수명, `createRenderInBrowserAbortSignal`(L560) · `annotateDynamicAccess`(L632) · `consumeDynamicAccess`(L499) · `formatDynamicAPIAccesses`(L510), `trackDynamicHoleInNavigation`(L960) · `trackThrownErrorInNavigation`(L1106) · `trackDynamicHoleInRuntimeShell`(L1158) · `trackDynamicHoleInStaticShell`(L1223) 각각의 본문, `instant-validation/` 의 경계 추적(`boundary-tracking.tsx` · `instant-samples.ts`)과 슬롯 마커 체계, `blocking-route-messages.ts` 의 오류 문구 열네 종과 `logBuildDebugHint`, `getNavigationDisallowedDynamicReasons`(L1479)와 내비게이션 검증, `dynamic-rendering-utils.ts` 의 `trackRuntimeDataAccessed` · `isClientHookDynamicError` · `ClientHookDynamicError`(digest `'CLIENT_HOOK_DYNAMIC'`)와 `BailoutToCSRError`(세 번째 중단 수단 — `createRenderInBrowserAbortSignal` L562 · `useDynamicSearchParams` L743), `DynamicValidationState.dynamicMetadata`(L123)와 `hasDynamicMetadata` 의 분업이 판정 쪽에서 쓰이는 세부, `hasAllowedClientDynamicAboveBoundary`(L932), `createDynamicTrackingState`(L129) · `createDynamicValidationState`(L140) · `createInstantValidationState`(L944) 팩토리, `work-unit-async-storage` 의 스토어 열한 종 정의, `cookies()`/`headers()`/`draftMode()` 가 실제로 이 함수들을 부르는 자리(`server/request/`)는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 표시하고 끊는다](01_mark/README.md)
- [02 흐름을 끊는 두 오류](02_interrupt/README.md)
- [03 컴포넌트 스택을 정규식으로 읽는다](03_stack/README.md)
- [04 정적 셸을 못 만들었을 때](04_verdict/README.md)
