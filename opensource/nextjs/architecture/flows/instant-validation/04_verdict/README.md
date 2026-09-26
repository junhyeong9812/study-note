# 04 렌더하고 판정한다

상위: [즉시 내비게이션을 개발 중에 검증하기까지](../README.md)

[03]이 만든 합성 페이로드를 **클라이언트 prerender** 로 한 번 그려 본다. 서버 쪽 데이터는 이미 청크로 굳어 있고, 프리페치 단계에서 안 풀린 구멍은 매달린 채 중단된다. 그 중단이 어느 Suspense · 어느 경계 아래에서 났는지로 오류를 쌓고, 가장 깊은 내비게이션부터 얕은 쪽으로 내려가며 **처음 실패한 깊이에서 멈춘다.** 빌드는 같은 함수를 샘플마다 부른다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L7063-L7474 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L7063-L7474))

## 실제 코드

깊이 하나의 결과를 돌려주기 직전이다. 오류가 있고 첫 시도였으면 **한 번 더** 그린다.

```tsx
// app-render.tsx L7362-L7394
    // If the prerender produced no real errors at this depth — either an
    // empty array (clean) or a deferred-only result (Error/AggregateError
    // representing a missing-boundary fallback) — there's nothing to
    // discriminate. Pass it up so the outer loop can hold any deferred
    // fallback back until every depth has been tried.
    if (!Array.isArray(result) || result.length === 0) {
      return result
    }

    if (previousBoundaryState === null && payloadResult.hasAmbiguousErrors) {
      // This is the first validation attempt. we prepared a payload where dynamic holes might be runtime data dependencies
      // or dynamic data dependencies. We do a followup validation using a payload with only Runtime segments to discriminate
      if (
        validationAbortSignal !== undefined &&
        !(await yieldToForegroundRequest(validationAbortSignal))
      ) {
        return []
      }

      const dynamicOnlyResult = await validateAtDepthImpl(
        depth,
        groupDepthForValidation,
        boundaryState
      )

      if (Array.isArray(dynamicOnlyResult) && dynamicOnlyResult.length > 0) {
        // The dynamic errors only validation found errors to report so we favor those
        return dynamicOnlyResult
      }
    }

    // If we didn't return some other errors at this point the only thing to return is this validation's result
    return result
```

```text
 첫 시도   useRuntimeStageForPartialSegments = false → [03]의 hasAmbiguousErrors 가 참
 재시도   previousBoundaryState 를 넘긴다 (L7381-7385)
          → L7151-7158 이 useRuntimeStage… = true 로 바꾸고 requiredIds 를 **이어받는다**
          → 새 서브트리를 전부 Runtime 단계로 다시 조립한다

 ★★★ 재시도에서 오류가 나오면 **그것을 고르고**, 안 나오면 **첫 시도의 오류를 낸다**
   주석 L7372-7373 - "we prepared a payload where dynamic holes might be runtime data
     dependencies or dynamic data dependencies. We do a followup validation using a payload
     with only Runtime segments to discriminate"
 => Runtime 단계로도 막히면 진짜 동적 데이터(연결·캐시 안 된 IO)가 원인이다
 => Runtime 단계에서는 풀리면 원인은 링크/런타임 데이터다 — 첫 시도의 오류가 그 종류로
    이미 적혀 있다(아래 DynamicHoleKind)
 ★ 주석은 "runtime data" 라고만 적지만 Shell 종류의 첫 시도에서 모호한 것은 "링크 데이터 대 동적"
   이다 (IVAL L1479-1482) — 주석이 Legacy 쪽 말투로 남아 있다 ※
```

## 동작 흐름

```text
 validateInstantConfigs   APPR L7063-7474  (412줄)

 L7080  const {...} = ctx.componentMod.InstantValidation()!  (L7080-7086) 로 IVAL 을 불러온다
          entry-base.ts L73-82 - NEXT_RUNTIME !== 'edge' && __NEXT_CACHE_COMPONENTS 일 때만
          require, 아니면 undefined. `!` 로 단정하고 쓴다
 L7093  prefetchKind = Partial ? ValidationPrefetchKind.Shell : LegacySpeculative
          ★ 열거의 셋째 값 `Speculative = 2` 는 **주석 처리돼 있다** (IVAL L1016-1017
            "TODO(app-shells): validate speculative prefetches"). 도달하는 값은 이 둘뿐이다
 L7102  __NEXT_USE_NODE_STREAMS 로 노드/웹 Flight 렌더러를 고른다
 L7109  collectStagedSegmentData(...)                            [03] ①
 L7400  groupDepthsByUrlDepth = discoverValidationDepths(loaderTree)   [03] ②
 L7405  for depth = maxDepth - 1 .. 0            **깊은 곳부터**
 L7408    for group = 그 깊이의 최대 그룹 깊이 .. 0
 L7421      양보 — 새 요청이 들어왔으면 => return []
 L7428      result = validateAtDepth(depth, group)
 L7430      배열이고 비어 있지 않으면 => return errors        ★ **처음 실패에서 끝**
 L7445      null 이면 건너뛴다                                  (그 깊이에 새 `instant` 없음)
 L7448      배열이 아니면(Error/AggregateError) impairedValidation = result
              주석 L7449-7453 - **덮어쓴다** — 가장 얕은 것이 원인에 가깝다
 L7459  모든 깊이가 통과했는데 impaired 가 있으면 그것을 낸다
 L7473  => return []
```

```text
 validateAtDepthImpl(depth, group, previousBoundaryState)   L7135-7395

 L7150  boundaryState = createValidationBoundaryTracking()
 L7160  payloadResult = createCombinedPayloadAtDepth(...)        [03] ③
 L7175  null 이면 => return null
 L7189  createCombinedPayloadStream(...)                         [03] ④
 L7201  instantValidationState = createInstantValidationState(slotStacks)
 L7210  prerenderStore = { type: 'validation-client', ...
          revalidate · expire · stale = INFINITE_CACHE, cacheSignal: null,
          boundaryState, fallbackRouteParams, validationSamples, validationSampleTracking }
 L7232  dynamicHoleKind 를 **미리** 정한다
          Shell             모호 ? Link    : Dynamic
          LegacySpeculative 모호 ? Runtime : Dynamic
 L7250  runInSequentialTasks(
          () => workUnitAsyncStorage.run(prerenderStore, getClientPrerender, <App .../>, { onError }),
          () => reactController.abort()
        )
          ★ 두 번째 태스크(L7333-7338)가 **무조건 중단한다**
          ※ 그래서 첫 태스크 안에 못 끝난 것은 전부 중단 오류로 onError 에 온다고 본다
 L7267  onError — 중단 오류이거나 신호가 끊겼으면
 L7271    trackDynamicHoleInNavigation(err, workStore, componentStack,
            instantValidationState, clientDynamicTracking, dynamicHoleKind, boundaryState)
 L7282  아니면(진짜로 던진 오류)
 L7286    NODE_ENV === 'production'(= 빌드 검증)이면 digest 로 **원래 서버 오류를 되찾는다**
            (workStore.reactServerErrorsByDigest, L7290-7301)
 L7304    trackThrownErrorInNavigation(...)
 L7341  processPreludeOp → preludeIsEmpty
 L7343  result = getNavigationDisallowedDynamicReasons(workStore, Empty|Full, ...)
 L7351  catch → 같은 함수에 PreludeState.Errored
 L7362  재시도 판단 (위 실제 코드)

 ★ 여기 넷이 [동적 판별]의 함수다 — DYNR L944 · L960 · L1106 · L1479
   스택 정규식으로 Suspense · 경계 · 슬롯 표시를 읽는 법은 [동적 판별] 03,
   무엇을 먼저 돌려주는지는 DYNR L1479-1592 가 정한다
```

```text
 ★★ 판정 함수가 돌려주는 모양이 셋이다 (DYNR L1472-1477)

   Array<Error>              막는 오류들 — 비어 있으면 통과
   Error | AggregateError    "검증을 끝까지 못 했다" — 루프가 **보류**한다

 보류가 되는 대표가 "경계가 안 그려졌다" 다 (DYNR L1540-1588)
   주석 L1540-1545 - "Missing boundaries on their own aren't a strong signal — a parent
     layout may legitimately omit a slot. Defer this so the caller can try shallower
     validation depths first; ..."
 => [03]의 requiredIds 중 renderedIds 에 없는 것이 있으면,
    그 원인이 될 오류가 경계 밖에서 났는지에 따라 Error 또는 AggregateError 가 된다
 => 위 루프가 그것을 바로 내지 않고 **다른 깊이가 진짜 오류를 낼 기회**를 준다
 ★ 개발에서 본 렌더가 이미 오류를 냈으면(devRenderDidError) 몇 갈래가 [] 로 접힌다
   (DYNR L1497-1502 · L1564-1568, 둘 다 __NEXT_DEV_SERVER 조건)
```

```text
 ★★ 검증 렌더는 어떤 스토어로 도는가 — 'validation-client'

 work-unit-async-storage.external.ts L142 에 정의된 전용 타입이다.
 만드는 곳은 APPR 두 곳뿐이다 (grep "type: 'validation-client'")
   L6766  warmupClientModulesForStagedValidation   예열
   L7211  validateAtDepthImpl                     판정
 읽는 쪽 몇
   IBOUND L22-24        이 스토어일 때만 boundaryState 를 돌려준다. 아니면 경계 컴포넌트가 던진다
   ISAMP  L34-40        'request' 와 이 스토어에서만 validationSampleTracking 을 찾는다
   request/params.ts L91-98 · search-params.ts L81-89
                        validationSamples 가 있으면 샘플 프록시를 씌운다 → [동적 API]
                        ('request' 갈래도 validationSamples 가 있으면 같다 — params.ts L101-106)
   request/root-params.ts L85-89   이 스토어에서는 **던진다** — "must not be used within a client component"
                        (샘플 확인 assertRootParamInSamples 는 'request' 갈래 L91-102 의 것이다)
```

```text
 빌드 — 같은 판정을 샘플마다   APPR L7726-8135

 validateInstantConfigsInBuild  L7726-7774
 L7736  workAsyncStorage.**exit**(...)  — 바깥 prerender 의 WorkStore 를 **벗어나서** 돈다
          주석 L7733-7735 - 검증 렌더는 별도 WorkStore 를 쓰지만 방어적으로 빠져나온다
 L7748  실패면 console.error('Stopping prerender due to instant validation errors.')
 L7750    => throw new StaticGenBailoutError()

 validateInstantConfigsInBuildImpl  L7783-7847
 L7794  samples = resolveInstantConfigSamplesForPage(loaderTree)
          ICONF L242-277 — **children 슬롯만** 따라 내려가고 안쪽 것이 바깥 것을 **덮어쓴다**
          주석 L260-262 - "The samples from inner segments override samples from outer
            segments, i.e. a page overrides the samples from a layout. We do not perform
            any merging logic."
 L7795  없으면 samples = [{}]    ★ 샘플이 없어도 **빈 샘플 하나로** 돈다
        ★★ 빈 샘플도 validationSamples 는 null 이 아니다(L7982-7985). 선언된 쿠키·헤더가 없으므로
          cookies().get/has · headers().get/has(ISAMP L81-224) · searchParams · 동적 params 를
          **한 번이라도 읽으면** missing-sample 오류가 되고, 그것이 가장 먼저 돌아온다(L8077-8081)
          => `unstable_samples` 없이 빌드 검증이 켜진 라우트는 요청 API 를 읽는 순간 빌드가 실패한다
 L7806  샘플마다 — 하나라도 실패하면 오류를 찍고 => return false (나머지 샘플은 안 본다)

 validateInstantConfigInBuildWithSample  L7849-8135  (287줄)
 L7880  createRelativeURLFromSamples(route, params, searchParams)
          ISAMP L414-478 이 라우트 패턴에 샘플 파라미터를 끼워 경로를 만든다
          docstring L411-412 - "this logic is somewhat hacky and likely incomplete"
          가로채기 라우트면 InvariantError('Not implemented: ...') (L456-468)
          → InstantValidationError 가 아니므로 validateInstantConfigsInBuild(L7739-7746)가
            "An unexpected error occurred during instant validation" 을 찍고 실패로 돌린다
            => 빌드 관문이 켜진 동적 가로채기 라우트는 **빌드가 멈춘다**
 L7887  샘플에 없는 파라미터만 fallbackRouteParams 로 남긴다
 L7914  새 WorkStore — isStaticGeneration: false, isDraftMode: false, after() 는 무시
 L7989  createRequestStore — **샘플로 만든** 쿠키 · 헤더 · draftMode
          createCookiesFromSample (ISAMP L81-146)   선언 안 한 이름을 get/has 하면 오류
          createHeadersFromSample (ISAMP L164-224)  〃. 'cookie' 헤더로 쿠키를 주면 거부 (L173-177)
          createDraftModeForValidation (ISAMP L229-249)  언제나 isEnabled = false
 L8044  renderWithRestartOnCacheMissInValidation — 캐시를 데우고 필요하면 한 번 더
 L8077  **샘플 누락 오류가 먼저다** — 있으면 그것만 돌려준다
          주석 L8075-8076 - "because they prevent us from rendering everything we need to validate."
 L8086  Abandoned 이고 syncInterruptReason 이 있으면 그것을 돌려준다
 L8107  클라이언트 모듈 예열 — 여기서도 샘플 누락이면 그것을 돌려준다 (L8117-8119)
 L8121  => validateInstantConfigs(prefetchMode, accumulatedChunks, null(디버그), ...,
                                 validationSamples, false)
          ★ 마지막 인자 devRenderDidError 가 **false 로 고정** — 주석 L8132
            "build has no shared dev render that would surface errors"
          ★ 정적 셸 검증은 여기서 안 한다 — 주석 L8095-8096 "that happens implicitly
            as part of the static prerender."
```

```text
 ★★ 샘플 프록시는 **읽기**만 가로챈다 — 선언이 곧 허용 목록이다

 쿠키   get · has 를 감싼다. getAll 은 그대로 둔다
          주석 L140-141 - "TODO(instant-validation-build): what should getAll do?"
        `{ name, value: null }` 은 "선언했지만 없음" (docstring L78-79)
 헤더   get · has 를 감싼다. 쿠키 샘플이 있으면 'cookie' 헤더를 자동으로 선언한다 (L169-186)
 params 선언 안 한 **라우트 파라미터**를 읽을 때만 — 라우트에 없는 키는 통과 (L262-268)
        주석 L279-281 - has/ownKeys 는 안 감싼다. 모양은 라우팅이 정한다
 searchParams  get 과 **has(`in`)** 둘 다 감싼다 (L290-321)
 루트 파라미터  assertRootParamInSamples (ISAMP L480-496) — [동적 API] 03 이 "범위 밖" 으로
               남겨 둔 그 함수다. 샘플 params 에 이름이 없으면 오류

 전부 trackMissingSampleErrorAndThrow(L68-74)로 **기록하고 던진다**
   주석 L71 - "TODO(instant-validation-build): this should abort the render"
 => 던진 오류를 사용자 코드가 잡아도 기록은 남는다. 그래서 L8077 과
    DYNR L1488-1493 이 **기록을 먼저** 본다 ※(잡힌 경우를 대비한 순서라는 해석은 내 것이다)
```

## 결과가 쓰이는 곳

```text
 validateInstantConfigs 의 반환 (Array<unknown>)
      --> 개발: runValidationInDev 가 그대로 돌려주고 [02]의 호출자가 오버레이로 보낸다
      --> 빌드: validateInstantConfigsInBuildImpl 이 console.error 로 찍고 false

 DynamicHoleKind (Link · Runtime · Dynamic)
      --> trackDynamicHoleInNavigation 이 **오류 문구**를 고른다 (DYNR L985-989 · L998-1002 · L1094-1098)
          "링크 프리페치면 풀린다" / "런타임 프리페치면 풀린다" / "진짜 동적이다" ※(문구 요지는 내 요약)

 StaticGenBailoutError
      --> [빌드]의 export 워커가 그 경로를 실패로 돌려준다 (README 참조)

 impairedValidation
      --> 모든 깊이가 통과했을 때만 나가는 "검증을 끝까지 못 했다" 보고
```

## 다루지 않는 것

`trackDynamicHoleInNavigation`(DYNR L960-1104) · `trackThrownErrorInNavigation`(L1106) · `getNavigationDisallowedDynamicReasons`(L1479-1592)의 판정 세부와 오류 문구(`blocking-route-messages.ts`, `shared/lib/instant-messages.ts`), `createUnrenderedSegmentError`, `getClientPrerender` 와 `<App>` 의 클라이언트 렌더, `processPreludeOp`, `renderWithRestartOnCacheMissInValidation`(L7487-7724)의 두 번 렌더 세부, `warmupClientModulesForStagedValidation`(L6711-6887), `getFallbackRouteParams` · `makeGetDynamicParamFromSegment`, `logBuildDebugHint`, 테스트 모드 표식(`formatValidationEvent`, L7754-7770), 클라이언트 훅 쪽 샘플 검사(`client/components/instant-samples.ts` — [클라이언트 트리] 04), `createExhaustiveURLSearchParamsProxy`(L328-355)의 쓰임새는 이 문서의 범위 밖이다.
