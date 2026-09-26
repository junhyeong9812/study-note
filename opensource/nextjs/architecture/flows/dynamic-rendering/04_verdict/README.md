# 04 정적 셸을 못 만들었을 때

상위: [무엇이 동적인지 가려내기](../README.md)

렌더가 끝났고 셸이 비었다. 이제 빌드를 세울지 봐줄지를 정해야 한다. 그 판정이 `throwIfDisallowedDynamic` 한 함수에 순서대로 들어 있고, **순서가 규칙의 전부**다.

## 위치

`packages/next` / `src/server/app-render` / `dynamic-rendering.ts` L1315-L1409 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/dynamic-rendering.ts#L1315-L1409))

## 실제 코드

셸의 상태가 세 가지다.

```ts
// dynamic-rendering.ts L1315-L1319
export enum PreludeState {
  Full = 0,
  Empty = 1,
  Errored = 2,
}
```

```text
 PreludeState.Full    = 0   셸이 다 만들어졌다
 PreludeState.Empty   = 1   비었다
 PreludeState.Errored = 2   만들다 오류가 났다

 ★ 판정에서 `Full` 인지 아닌지만 두 번 본다 (L1356 · L1375).
   Empty 와 Errored 를 구분하는 자리는 **맨 끝 한 곳**뿐이다 (L1399)
 ★★ 그리고 `Errored` 는 이 함수에 **오지 않는다** — 호출처가 넘기는 것은
   Empty 나 Full 뿐이고(app-render.tsx L9203 · L9983),
   `Errored` 는 던지지 않는 두 함수만 받는다(L7039 · L7354).
   그래서 L1399 를 빠져나가는 조용한 통과 경로는 실제로는 안 밟힌다
```

## 동작 흐름

```text
 throwIfDisallowedDynamic(workStore, prelude, dynamicValidation,
                          serverDynamic, allowEmptyStaticShell)   DYNR L1342

 ── ① 동기 IO 는 무조건 ──
 L1349  throwIfSyncIOUsed(workStore, serverDynamic)
          L1333  serverDynamic.syncDynamicErrorWithStack 이 있으면
          L1334    logDisallowedDynamicError(...)  =>  L1338 throw StaticGenBailoutError()

 ── ② metadata 만 동적이면 실수로 본다 ──
 L1356  prelude === Full && hasAllowedDynamic === false && hasDynamicMetadata 이면
 L1361    console.error(createDynamicOrRuntimeMetadataError(route).message)
 L1362    throw StaticGenBailoutError()

 ── ③ 옵트인 둘 중 하나면 여기서 끝 ──
 L1371  allowEmptyStaticShell || dynamicValidation.hasSuspenseAboveBody 이면 => return

 ── ④ 셸이 Full 이 아니면 ──
 L1375  prelude !== Full 이면
 L1380    dynamicErrors 가 있으면 => 전부 찍고(L1381-1383) L1385 throw
 L1392    hasDynamicViewport 이면 => viewport 오류 찍고(L1393) L1396 throw
 L1399    prelude === Empty 이면 => **"이건 Next.js 버그다"**(L1404) 찍고 L1406 throw
```

```text
 ★★★ ②가 ③보다 앞에 있는 것이 의도다 (주석 L1351-1355)

   "The dynamic metadata error is a mistake-detection signal. It fires when the
    rest of the shell is otherwise fully static apart from metadata, suggesting
    the dynamic data access in `generateMetadata` was probably unintentional.
    That condition is independent of whether the user or build phase accepted
    an empty shell, so **we surface it before any opt-in bypass**."

 => 셸이 **다 만들어졌는데**(Full) metadata 만 동적이면 실수일 가능성이 크다
 => 그 판정은 "빈 셸을 받아들였는가" 와 무관하므로 **옵트인보다 먼저** 본다
 ★ 조건에 `hasAllowedDynamic === false` 가 들어간다 —
   [03]에서 Suspense 를 봐준 적이 있으면 실수로 보지 않는다
 ★★ 즉 옵트인으로 못 끄는 것이 **둘**이다 — ①의 sync IO 와 ②의 metadata.
   둘 다 옵트인 우회(L1371)보다 **앞**에 있다
```

```text
 ★★★ 옵트인 둘을 **같은 뜻으로** 취급한다 (주석 L1365-1370)

   "Either flag expresses "this shell is allowed to be empty/blocking":
      - `allowEmptyStaticShell` covers `instant = false` (user opt-in)
        and the build-phase fallback-shell case.
      - `hasSuspenseAboveBody` is the structural opt-in inside the user's root
        layout.
    Treat them as synonyms for the purpose of bypassing shell-failure errors."

 => 설정으로 하는 옵트인(`instant = false`)과
    **트리 모양으로 하는 옵트인**(body 위의 Suspense)이 같은 값어치다
 => [03]의 그 복잡한 정규식이 존재하는 이유가 이 한 줄이다 —
    정규식이 판정한 것이 설정 플래그와 동등하게 쓰인다
 ★ `allowEmptyStaticShell` 은 빌드의 fallback 셸 경우도 덮는다.
   사용자가 켠 것과 빌드 단계가 켠 것을 한 플래그로 합쳤다
```

```text
 ★★ ④가 사다리이고 **마지막 칸이 자기 버그 신고**다 (L1375-1404)

 L1376-1378  주석 - "We didn't have any sync bailouts but there may be user code
   which blocked the root. We would have captured these during the prerender
   and can log them here and then terminate the build/validating render"
   => [03]이 쌓아 둔 dynamicErrors 를 하나씩 찍는다 (L1381-1383)

 L1388-1391  주석 - "the only other thing that could be blocking the root is
   dynamic Viewport. If this is dynamic then you need to opt into that by adding
   a Suspense boundary above the body to indicate your are ok with fully dynamic
   rendering."
   => viewport 는 Suspense 옵트인을 요구한다

 L1400-1402  주석 - "If we ever get this far then **we messed up the tracking of
   invalid dynamic.** We still adhere to the constraint that you must produce a
   shell but invite the user to report this as a bug in Next.js."
   문구 - `Route "${route}" did not produce a static shell and Next.js was
     unable to determine a reason. **This is a bug in Next.js.**`

 => 셸이 비었는데 이유를 못 찾으면 **추적 코드가 잘못된 것**이다
 => 그래도 빌드는 세운다 — "셸을 만들어야 한다" 는 제약은 지키고,
    다만 사용자에게 버그 신고를 부탁한다
 ★★ [02]의 모듈 로드 자기 검사와 같은 태도다.
   문자열·스택에 기댄 판정이 틀렸을 때를 **코드가 미리 인정해 둔다**
```

```text
 ★ 오류를 찍는 방법이 두 가지 섞여 있다

 logDisallowedDynamicError(workStore, error)   L1321
   L1325  console.error(error)           ← 오류 객체 그대로 (스택이 나온다)
   L1326  logBuildDebugHint(workStore.route)

 그런데 metadata·viewport 는
   console.error(create…Error(route).**message**)   L1361 · L1393
                                        ← 문자열만 (스택이 안 나온다)

 => 사용자 코드에서 온 오류(dynamicErrors · syncDynamicError)는 **스택째** 찍고,
    프레임워크가 만든 진단 문구는 **문구만** 찍는다
 ★ 그래서 앞의 것만 logBuildDebugHint 를 붙인다
```

```text
 ★ 던지는 것은 언제나 같은 오류다

 => 다섯 갈래 모두 `throw new StaticGenBailoutError()` 다.
    ①만 인수가 없고 나머지도 전부 인수 없이 던진다
 => 문구는 이미 console.error 로 찍었으므로 오류 객체는 **흐름을 끊는 역할만** 한다
 ★ [01]의 `markCurrentScopeAsDynamic` 이 `dynamic = "error"` 에서 던지는 것과
   같은 클래스다. 그쪽은 문구를 인수로 넣는다

 ★★★ `getStaticShellDisallowedDynamicReasons`(L1411)가 **비슷하지만 중복이 아니다**

   같은 주석이 L1417 · L1431 · L1437 · L1441 · L1446 · L1450 에 있는데
   칸이 넷 대 **셋**이고 네 군데가 다르다

   ① sync IO 칸이 **없다.** `serverDynamic` 을 인자로 받지도 않는다 (L1411-1416)
   ② metadata 조건이 다르다 — `dynamicErrors.length === 0` 이 더 붙고
      `hasDynamicMetadata`(boolean) 대신 `dynamicMetadata`(Error)를 본다 (L1422-1426).
      반환도 **저장된 Error 그대로**(L1428)이고, 이쪽은 문구를 새로 만든다 (L1361)
   ③ `hasDynamicViewport` 칸(L1392-1397)이 **없다**
   ④ 마지막 칸이 `new InvariantError(...)` 반환이고
      문구에서 "This is a bug in Next.js." 가 빠졌다 (L1456)

 => 둘은 같은 판정의 두 판본이 아니라 **다른 추적 함수의 짝**이다.
    [README]의 세 짝 표를 보라 — 이쪽은
    `trackDynamicHoleInRuntimeShell` · `InStaticShell` 이 채운 상태를 읽는다.
    그 둘이 `dynamicMetadata`(Error)를 세우므로 조건도 그렇게 생겼다
```

## 결과가 쓰이는 곳

```text
 StaticGenBailoutError (인수 없이)
      --> [정적 응답]은 받자마자 **다시 던진다** (app-render.tsx L9665-9677 — isStaticGenBailoutError 면 throw).
          실제로 받아 처리하는 곳은 빌드의 export 워커다 (export/worker.ts L598) → [빌드] [04].
          문구는 이미 터미널에 찍혀 있다

 console.error 로 찍힌 것들
      --> `next build` 출력. logBuildDebugHint 가 라우트 이름과 함께 힌트를 붙인다

 return (옵트인 통과)
      --> 빈 셸을 그대로 인정하고 렌더를 통과시킨다.
          [정적 응답]이 그 셸로 프리렌더 결과를 만든다

 getStaticShellDisallowedDynamicReasons(L1411) / getNavigationDisallowedDynamicReasons(L1479)
      --> 던지지 않고 **이유 목록만** 돌려주는 짝. 즉시 검증 경로가 쓴다
```

## 다루지 않는 것

`getStaticShellDisallowedDynamicReasons`(L1411) · `getNavigationDisallowedDynamicReasons`(L1479)와 `NavigationValidationResult`(L1472)의 판정 규칙, `blocking-route-messages.ts` 의 오류 문구 생성 함수 열네 종과 `logBuildDebugHint` 의 내용, `PreludeState` 를 정하는 쪽([정적 응답]이 셸의 상태를 판정하는 자리)과 `allowEmptyStaticShell` 을 세우는 쪽(`instant = false` 설정과 빌드 fallback 경로), `StaticGenBailoutError` 를 받아 처리하는 쪽, `trackDynamicHoleInStaticShell`(L1223) 등 네 추적 함수가 `dynamicErrors` 를 채우는 세부, `InstantValidationState.validationPreventingErrors` · `thrownErrorsOutsideBoundary` 를 쓰는 즉시 검증 경로는 이 문서의 범위 밖이다.
