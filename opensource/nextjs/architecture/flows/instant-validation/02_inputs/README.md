# 02 응답이 나간 뒤 입력을 모은다

상위: [즉시 내비게이션을 개발 중에 검증하기까지](../README.md)

검증의 재료는 **단계별로 나눠 받은 RSC 청크**다. 가장 싼 길은 사용자에게 방금 보낸 그 렌더의 청크를 그대로 쓰는 것이고, 못 쓰면 캐시가 데워진 상태로 한 번 더 렌더한다. 이 구획은 그 선택과, 그 모든 일을 **응답이 끝난 뒤로** 미루는 장치다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L4487-L4670 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L4487-L4670))

## 실제 코드

방금 스트림한 렌더를 다시 쓸 수 있는 조건이 두 줄이다.

```tsx
// app-render.tsx L4794-L4808
  // Check if we can re-use the main render for validation.
  let inputsFromNavigation: ResolvedValidationInputs | null
  if (!result.hadCacheMiss && !('syncInterruptReason' in result.outcome)) {
    inputsFromNavigation = {
      accumulatedChunks: result.outcome.accumulatedChunks,
      startTime: result.outcome.startTime,
      stageEndTimes: result.outcome.stageEndTimes,
      requestStore,
      debugChannelClient: validationDebugChannel,
    }
  } else {
    // Cache miss or sync IO. We can't re-use the main render.
    dropValidationDebugChannel(validationDebugChannel)
    inputsFromNavigation = null
  }
```

```text
 hadCacheMiss       스테이지 경계에서 아직 끝나지 않은 캐시 읽기가 있었다
                    (streamStagedRenderInDev L5284-5308 checkForCacheMiss)
 syncInterruptReason 동기 IO 로 렌더가 중단됐다

 ★★ 캐시 미스가 있었던 렌더는 **프로덕션을 대표하지 않는다**
   stagedRenderWithCachesInDev docstring L5714-5716 -
     "(against the streamed render directly when it's prod-representative,
       otherwise against a separate warm-cache render)"
   => 첫 방문(캐시가 차가운 상태)은 Suspense 폴백을 흘렸을 수 있다.
      프로덕션이라면 캐시에 있었을 내용이다. 그 청크로 검증하면 없는 구멍을 잡는다 ※
 ★ 못 쓰는 경우 디버그 채널을 **읽지 않고 버린다** (dropValidationDebugChannel L4439-4445)
```

## 동작 흐름

```text
 stagedRenderWithCachesInDev   APPR L5719-5839

 L5735  shouldValidate 면 validationGeneration = beginDevValidation(ctx.htmlRequestId)
 L5750  디버그 채널이 있고 검증하면 ReplayableNodeStream 으로 **한 벌 더** 떠 둔다 (L5751-5757)
 L5763  streamStagedRenderInDev(...)  → { stream, resultPromise }
 L5834  => return { stream, debugChannel }        ← 응답은 여기서 이미 흐른다

 L5789  void resultPromise.then(async (result) => {
 L5791    hadCacheMiss 면 await cacheSignal.cacheReady()
 L5795    hadInvalidDynamicUsage = forwardInvalidDynamicUsageError(...)
 L5800    검증 안 하면 => return
 L5804    invalid dynamic usage 가 있었거나 세대가 이미 중단됐으면 => finish, return
 L5812    runDevValidationInBackground(...)
        })
 ★ `void` — 렌더 함수는 검증을 **기다리지 않는다**
```

```text
 ★★★ 같은 문서의 새 렌더가 옛 검증을 **끊는다** (dev-validation-scheduler.ts)

 beginDevValidation(htmlRequestId)   L72 → DevValidationScheduler.begin L29-63
   같은 htmlRequestId 로 진행 중인 것이 있으면 L32-35 **abort** 하고 지운다
   전체가 MAX_ACTIVE_DEV_VALIDATIONS(= 100, L4) 이상이면 가장 오래된 것을 abort
   finish() 는 **자기가 여전히 현재 세대일 때만** 지운다 (L53-61)
     주석 L54-55 - "A superseded generation may settle after its replacement."

 yieldToForegroundRequest(signal)   L86-95
   **패치되지 않은** setImmediate 로 한 번 양보한다
   주석 L82-84 - "The regular global `setImmediate` is patched by staged rendering and
     can run inside the current timer task. The original immediate is required here so
     we actually pass through the event-loop poll phase where HTTP requests arrive."
 => 렌더 사이마다 양보해 **새 요청이 들어와 이 검증을 대체할 틈**을 준다.
    검증 기계 곳곳의 `if (!(await yieldToForegroundRequest(...))) return` 이 그것이다
```

```text
 runDevValidationInBackground   APPR L4487-4670  (184줄)

 L4504  consoleAsyncStorage.run({ dim: true }, ...)   ★ 검증 중 로그를 흐리게 표시하는 표지로 보인다 ※
 L4510  노드 응답이면 waitForResponseToFinish(...) 가 거짓일 때 => logValidationAborted, return
          주석 L4506-4509 - "... Wait until the response has finished so that work cannot
            delay Flight delivery or the client navigation."
 L4518  yieldToForegroundRequest 가 거짓이면 => return
 L4523  runInstantInsightsWithTracing(ctx, async (runSpan) => {
 L4526    devRenderDidError = getDevRenderDidError()   (렌더가 다 끝난 **지금** 읽는다)
 L4532    lazyInputs = await prepareValidationInputs(...)           아래
 L4553    Promise.all([ instantInputs 풀기 · staticInputs 풀기 ])
            주석 L4546-4552 - 렌더가 둘 필요하면 **병렬로** 돌린다
 L4561    둘 중 하나라도 VALIDATION_BAILOUT 이면 => return
 L4570    세대가 중단됐으면 => return
 L4585    devValidationWorker = getDevValidationWorker()
 L4587    있으면 스냅숏을 만들어 **워커 스레드**에 넘긴다 → Flight 바이트를 받아
 L4612      sendErrorsToBrowser(createNodeStreamFromChunks(chunks), ctx.htmlRequestId)
 L4617    없으면 runWithDevValidationLogging 안에서
 L4629      runValidationInDev(...)   → L4643 logMessagesAndSendErrorsToBrowser
        })
 L4657  .catch — 세대가 중단된 뒤의 오류는 삼킨다. 아니면 InvariantError 로 감싸 찍는다
 L4669  .finally(() => validationGeneration.finish())

 ★ 워커가 설치되는 조건 — next-dev-server.ts L247-257
   process.env.TURBOPACK && nextConfig.experimental.devValidationWorker !== false
   config-shared.ts L1225-1227 - "Has no effect with Webpack, where validation always runs
     in process. The worker's thread cannot reach Webpack's dev source maps, ..."
 => Turbopack 기본값이면 **워커**, Webpack 이면 **메인 스레드**다
 ★ 워커 쪽 진입은 runValidationInDevFromSnapshot(APPR L6385) —
   route-modules/app-page/module.ts L189 에서 불리고, 결국 같은 runValidationInDev 를 부른다 (L6457-6467)
```

```text
 prepareValidationInputs   APPR L4781-4833 — 모드가 둘로 가른다

 PrefetchingMode (L5053-5056)   LegacySpeculative = 1 · Partial = 2
 getPrefetchingModeForPage  L5058-5077
   renderOpts.partialPrefetching                          => Partial
   anySegmentHasPartialPrefetchingEnabled(loaderTree)      => Partial
     (세그먼트 `export const prefetch` 이 'partial' · 'unstable_eager', ICONF L59-83)
   그 밖                                                  => LegacySpeculative
 ★ 두 값 다 도달한다 — partialPrefetching 은 next.config 최상위 옵션(config-shared.ts L1947,
   `boolean | 'unstable_eager'` — 둘 다 참값이라 Partial)이고
   config.ts L568-570 이 cacheComponents 없이 켜면 오류를 낸다

 ── Partial  (L4835-4929) ──────────────────────────────────────────
 needsInstantValidation = anySegmentNeedsInstantValidationInDev(loaderTree)
 areStagesCompatible   = !hasNonRootStaticParams(...)
   주석 L4850-4851 - 루트가 아닌 정적 파라미터가 있으면 정적 셸과 App Shell 의
     정적 단계가 달라 **한 렌더를 둘에 못 쓴다**

   재사용 가능 + 호환            instant = 본 렌더(필요시) · static = 본 렌더
   재사용 가능 + 비호환 + App Shell 내비게이션
                                 instant = 본 렌더(필요시) · static = LAZY_RUNTIME_PRERENDER
   재사용 가능 + 비호환 + 그 밖   instant = LAZY_FULL_RENDER(필요시) · static = 본 렌더
   재사용 불가                   instant = LAZY_FULL_RENDER(필요시)
                                 static  = 호환이고 instant 가 있으면 **그것을 같이**, 아니면 PRERENDER

 ── LegacySpeculative  (L4931-4998) ─────────────────────────────────
   재사용 가능                   instant = 본 렌더(필요시) · static = 본 렌더
   재사용 불가 + 즉시 검증 필요   instant = static = LAZY_FULL_RENDER   (한 번 렌더로 둘 다)
   재사용 불가 + 불필요           instant = null · static = LAZY_RUNTIME_PRERENDER

 ★ "필요시" = needsInstantValidation 이 거짓이면 instantInputs 는 null
 ★ "App Shell 내비게이션" = navigationHasAppShell(L5174-5181) —
   'prefetched-client' 이고 prefetchStage === ShellRuntime 일 때만 참이다.
   그 값은 RSC 요청 + Partial + HMR 새로고침 아님에서만 정해진다 (L1403-1415).
   초기 HTML('initial-load')은 언제나 거짓이다
 ★ LAZY_* 는 createMemoizedThunk(L4770-4779)다 — 같은 thunk 를 둘이 가리켜도 **한 번만** 돈다
```

```text
 ★★ 주석과 코드가 어긋난다 — prerenderWithWarmCachesForStaticValidationInDev

 L5554  // This function is currently only used in partialPrefetching.
 L5555  const prefetchMode = PrefetchingMode.Partial
 그런데 Legacy 쪽 L4972-4985 도 이 함수로 LAZY_RUNTIME_PRERENDER 를 만들고
 L4995 에서 쓴다 (재사용 불가 + 즉시 검증 불필요)
 => 그 경로의 정적 셸 prerender 는 syncIO 가 getSyncIOMode(Partial) =
    SyncIOMode.AllowedInDynamic 이 된다 (L5571). Legacy 의 본 렌더는
    AllowedInRuntimeOrDynamic 이다 (L5079-5086)
    staged-rendering.ts L50-53
      AllowedInRuntimeOrDynamic - "Before `partialPrefetching`: Sync IO errors in static stages, and is allowed otherwise."
      AllowedInDynamic          - "After `partialPrefetching`: Sync IO errors in all stages other than dynamic."
 ※ 그래서 Legacy 라우트에서 Runtime 단계의 동기 IO 가 이 경로에서만 중단으로 잡힐 수
   있다고 본다 — 실제로 결과가 달라지는지는 돌려 보지 않았다
```

```text
 청크를 쌓는 규칙 — 단계가 **포함 관계**다 (APPR L5934-5963 collectStageChunk)

   ShellStatic 에서 온 청크   → shellStatic · static · shellRuntime · runtime · dynamic
   Static                   →               static · shellRuntime · runtime · dynamic
   ShellRuntime             →                        shellRuntime · runtime · dynamic
   Runtime                  →                                       runtime · dynamic
   Dynamic                  →                                                 dynamic
   (switch 의 fall through 로 한 청크를 뒤 배열 전부에 넣는다)

 => 각 배열이 "그 단계까지 나온 전부" 다. dynamicChunks 가 전체 스트림이다
 ★ 이 규칙 덕에 [03]의 createStagedStreamFromChunks 가 dynamic 배열 하나에서
   **길이만 보고** 단계를 끊을 수 있다 (IVAL L492-495 주석)
 ★ shellStaticChunks 는 즉시 검증이 쓰지 않는다 — APPR L7113-7118 이 넘기는 것은 넷뿐이고,
   그 배열을 읽는 곳은 prerenderToStream(L9007 · L9025)뿐이다
   (grep — 그 밖에는 워커 타입 선언 dev-validation-worker-globals.ts L26 하나)
```

```text
 runValidationInDev   APPR L6476-6627 — 순서가 정해져 있다

 L6489  needsInstantValidation = anySegmentNeedsInstantValidationInDev(loaderTree)
 L6492  "`samples` from instant config are only used during build"
          validationSamples = null · validationSampleTracking = null
 L6499  클라이언트 모듈 예열 — 즉시 검증이면 'validation-client' + dynamicChunks,
          아니면 'prerender-client' + runtimeChunks (L6512-6513)
 L6527  양보
 L6550  ① 정적 셸 검증  validateStaticShell(staticInputs, ...)
 L6577    오류가 있으면 => return result        ★★ **즉시 검증까지 가지 않는다**
 L6588  ② if (needsInstantValidation && instantInputs)
 L6600    validateInstantConfigs(prefetchMode, inputs.accumulatedChunks, ...)   [03][04]
 L6620    오류가 있으면 => return result

 ★ instantInputs 와 staticInputs 가 **같은 객체**일 수 있어서 디버그 채널을
   WeakMap 으로 한 번만 읽는다 (L6531-6545)
 ★ docstring L6470-6475 - "This function is a fork of prerenderToStream cacheComponents
   branch. ... should update it in conjunction with any changes to that function."
```

## 결과가 쓰이는 곳

```text
 ResolvedValidationInputs (accumulatedChunks · startTime · stageEndTimes · requestStore · 디버그 채널)
      --> runValidationInDev 가 정적 셸 검증과 즉시 검증에 나눠 쓴다
      --> 워커 경로면 스냅숏으로 직렬화돼 스레드를 건넌다

 accumulatedChunks.{static,shellRuntime,runtime,dynamic}Chunks
      --> [03]의 collectStagedSegmentData 가 세그먼트별로 자른다

 stageEndTimes
      --> [03]이 단계마다 `endTime` 으로 넘겨 그 뒤에 끝난 IO 의 디버그 정보를 뺀다

 VALIDATION_BAILOUT
      --> 동기 IO · invalid dynamic usage 가 있었다는 뜻. 그 오류만 오버레이로 보내고 검증은 안 한다
```

## 다루지 않는 것

`streamStagedRenderInDev`(L5204-5432)의 reveal 규칙·`_revealAfter`·콜드 캐시 표시, `renderWithWarmCachesForValidationInDev`(L5446-5536) · `prerenderWithWarmCachesForStaticValidationInDev`(L5546-5668)의 본문, `accumulateStreamChunksInto`(L5869-5932)와 스테이지 바이트 계산(L5965-6047), `createAsyncApiPromises`(L6049-6089), `logMessagesAndSendErrorsToBrowser`(L6099-6165)와 `runWithDevValidationLogging`(L6200-6261)의 로그 표식, `buildDevValidationSnapshot` 과 워커 쪽 재구성(`buildDevValidationWorkStore` L6316 · `toDevValidationInputs` L6359), `runInstantInsightsWithTracing`(L4704-4734)의 트레이싱, `hasNonRootStaticParams` 의 판정, `waitForResponseToFinish`(`wait-for-response.ts`), `validateStaticShell` 본문은 이 문서의 범위 밖이다.
