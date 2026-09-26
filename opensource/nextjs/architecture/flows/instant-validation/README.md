# 즉시 내비게이션을 개발 중에 검증하기까지

상위: [Next.js 아키텍처 지도](../../README.md)

cacheComponents 를 켠 앱에서 페이지를 열면, 응답이 다 나간 **뒤에** 서버가 한 번 더 일한다. 방금 만든 RSC 청크를 세그먼트별로 잘라 "이 URL 깊이에서 내비게이션이 시작됐다면 프리페치만으로 화면이 바로 나오는가" 를 깊이마다 다시 렌더해 본다. 그 기계가 `server/app-render/instant-validation/` 과 `app-render.tsx` 의 L4418-8228 사이에 흩어져 있다. 입구는 사용자가 쓰는 한 줄 `export const instant` 이다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `ICONF` = `server/app-render/instant-validation/instant-config.tsx`(311줄), `IVAL` = `.../instant-validation.tsx`(1511줄), `ISAMP` = `.../instant-samples.ts`(496줄), `IBOUND` = `.../boundary-impl.tsx`(138줄), `APPR` = `server/app-render/app-render.tsx`.

## 위치

`packages/next` / `src/server/app-render/instant-validation` / `instant-config.tsx` L132-L230 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/instant-validation/instant-config.tsx#L132-L230))

## 실제 코드

검증할지 말지는 **설정 한 줄과 세그먼트 파일 한 줄**이 함께 정한다. 먼저 설정 쪽이다.

```tsx
// instant-config.tsx L146-L169
  switch (validationLevel) {
    case 'manual-warning':
      manualValidation = true
    // intentional fallthrough
    case 'warning':
      baseValidationLevel = VALIDATION_LEVEL.WARNING
      break
    case 'experimental-manual-error':
      manualValidation = true
    // intentional fallthrough
    case 'experimental-error':
      baseValidationLevel = VALIDATION_LEVEL.ERROR
      break
    default:
      validationLevel satisfies never
  }

  const applyDefaultValidation =
    // We need to be validating the right level
    level <= baseValidationLevel &&
    // We need to not be in manual validation mode
    !manualValidation &&
    // We don't validate framework internal routes by default
    !isFrameworkErrorRoute(workStore.route)
```

```text
 validationLevel 은 next.config 의 experimental.instantInsights.validationLevel 이다
   config.ts L1671-1672 - 값이 없으면 **'warning'** 으로 채운다
   config-shared.ts L1521-1525 - 네 값 'warning' · 'manual-warning' ·
                                   'experimental-error' · 'experimental-manual-error'

 ★★★ 기본값 'warning' 에서는 `instant` 를 **안 써도 검증한다**
   applyDefaultValidation = level <= base && !manual && 프레임워크 오류 라우트 아님
   이것이 참이면 설정이 없는 **page · default 세그먼트**를 instant = true 로 본다
     (L212-216, 판별은 isImplicitValidationSegment L28-35 — docstring L24-27
      "Only page and default segments qualify — layouts do not validate on their own.")
   config-shared.ts L1208 문서 주석도 그렇게 적는다
     "'warning' (default): Validates all navigations for Instant UI in development"

 ★★ 개발과 빌드가 **같은 함수를 수준만 바꿔** 부른다
   anySegmentNeedsInstantValidationInDev    L232  level = WARNING (0)
   anySegmentNeedsInstantValidationInBuild  L237  level = ERROR   (1)
   => 'warning' 계열이면 base = 0 이라 빌드(1 <= 0 거짓)에서는 기본 검증이 꺼진다.
      빌드 검증은 'experimental-*' 설정이나 세그먼트의 `level: 'experimental-error'` 로만 켜진다
 ★★ 그런데 `level` 은 **라우트를 넣을지만** 정한다 — 켜진 뒤의 깊이 루프(IVAL L1410-1420)는
   수준을 읽지 않고 `instant` 가 true · 객체인 세그먼트를 전부 검증한다. 설정 없는 page/default 도
   승격된다(L1291-1299 — 수준 비교가 없다). 세그먼트 하나가 'experimental-error' 로 빌드 관문을 켜면
   base 가 'warning' 이어도 그 라우트 전체가 빌드 오류 대상이 된다 → [03]
 ★ 둘 다 cacheScopedToWorkStore(L284-311)로 감싸 **WorkStore 하나당 한 번만** 트리를 훑는다
   다만 Turbopack 기본값은 검증을 **워커**에서 새 WorkStore 로 돌리므로(APPR L6417 buildDevValidationWorkStore · [02])
   요청 하나에 메인과 워커가 각각 한 번씩 훑는다
```

## 동작 흐름

```text
 `export const instant` 을 읽는 자리 — 저장소 전체 grep (`\.instant\b` · `.instant ??`)

   ICONF L90    isPageAllowedToBlock                  instant = false 면 빈 정적 셸 허용
   ICONF L179   anySegmentNeedsInstantValidation      검증을 켤지         [01]
   ICONF L248   resolveInstantConfigSamplesForPage    빌드 샘플을 고른다   [04]
   IVAL  L1285  createCombinedPayloadAtDepth 안        깊이별로 요구를 모은다 [03]
   create-flight-router-state-from-loader-tree.ts L38  instant = false 면 프리페치 힌트 비트

 그리고 컴파일러가 하나를 더 심는다
   crates/next-custom-transforms/src/transforms/debug_instant_stack.rs
     page · layout · default 파일에 `instant` export 가 있으면
     export const __debugCreateInstantConfigStack =
       process.env.NODE_ENV !== 'production' ? function instant() {...} : null
     그 함수의 `new Error(' ')` 에 **`instant` 값의 소스 위치**를 붙인다
   => 검증 오류의 스택이 사용자의 `export const instant = ...` 줄을 가리킨다
   ★ **명시한** `instant` 만이다. 기본 수준에서 암묵 승격된 page 에는 이 export 가 없어
     localCreateInstantStack 이 null 이다(IVAL L1301-1307). 그 오류에는 설정 위치가 없을 수 있다
   ★ 프로덕션 빌드에서는 null 이다. 빌드 검증 오류에는 이 위치가 없다
     (IVAL L1305-1308 이 함수가 아니면 null 로 둔다)
```

```text
 ★★★ 이 기계는 **두 곳에서** 돈다 — 개발 전용이 아니다

 개발  (process.env.__NEXT_DEV_SERVER && NEXT_RUNTIME !== 'edge' && cacheComponents)
   초기 HTML   APPR L3452-3458 → L3506 stagedRenderWithCachesInDev(shouldValidate: true)
   RSC 요청    APPR L2944-2950 → generateDynamicFlightRenderResultWithStagesInDev
                 → L1445 stagedRenderWithCachesInDev(shouldValidate)
     +-- 렌더가 끝나면 L5812 runDevValidationInBackground               [02]
         +-- 응답이 다 나간 뒤 runValidationInDev L6476
             1) 정적 셸 검증 validateStaticShell   — **오류가 나면 여기서 끝난다**
             2) 즉시 검증     validateInstantConfigs L7063               [03][04]

 빌드  (workStore.cacheComponentsEnabled && isBuildTimePrerendering
        && renderOpts.runInstantValidation && ...InBuild)
   APPR L2873-2885  prerender 결과를 **다 만든 뒤** validateInstantConfigsInBuild
     +-- 샘플마다 동적 렌더를 새로 하고 같은 validateInstantConfigs 를 부른다  [04]
     +-- 실패하면 StaticGenBailoutError 로 빌드를 세운다 (L7748-7751)

 프로덕션 런타임에서 도는 것
   isPageAllowedToBlock          prerenderToStream L8279-8281 (정적 셸 판정)
   SubtreeHasInstantFalse 비트    create-flight-router-state-from-loader-tree.ts L102-107
   검증 경계 컴포넌트 자리        layout-router.tsx L779-781 · L912-922 (서버 쪽에서만,
                                  컨텍스트 값이 없으면 아무것도 안 감싼다)
 ※ 검증 렌더 자체는 요청 시각 프로덕션 서버에서 돌지 않는다 — 위 두 진입의
   조건(__NEXT_DEV_SERVER / isBuildTimePrerendering)을 읽고 내린 결론이다
```

1. [검증을 켤지 정한다](01_gate/README.md) — `instant` 네 값과 수준 네 값이 만나는 자리.
2. [응답이 나간 뒤 입력을 모은다](02_inputs/README.md) — 방금 스트림한 청크를 다시 쓸 수 있는가.
3. [깊이마다 새 트리를 조립한다](03_depth/README.md) — 공유 레이아웃은 Dynamic, 새 서브트리는 프리페치 단계.
4. [렌더하고 판정한다](04_verdict/README.md) — 모호하면 한 번 더, 얕은 깊이까지 내려가며.

```text
 ★★ 이 흐름이 [동적 판별]의 **즉시 검증 전용** 함수가 넷, 부르는 자리는 다섯이다 (validateInstantConfigs 안)

   L7201  createInstantValidationState(payloadResult.slotStacks)   DYNR L944
   L7271  trackDynamicHoleInNavigation(... dynamicHoleKind, boundaryState)   DYNR L960
   L7304  trackThrownErrorInNavigation(...)                         DYNR L1106
   L7343  getNavigationDisallowedDynamicReasons(...)                DYNR L1479
   L7352    〃 (catch 쪽 — PreludeState.Errored 로 한 번 더)
   (공용 도구 createDynamicTrackingState L129 · isPrerenderInterruptedError L480 ·
    PreludeState L1315 도 같은 함수 안에서 쓴다)

 => 스택을 읽어 "구멍이 Suspense 아래인가, 검증 경계 아래인가" 를 가리는 일은
    [동적 판별] 03 이 다룬다. 이 흐름은 **그 렌더에 무엇을 넣는가**를 다룬다
```

## 결과가 쓰이는 곳

```text
 runValidationInDev 의 반환 (오류 배열)
      --> logMessagesAndSendErrorsToBrowser (APPR L4643) 가 개발 오버레이로 보낸다
      --> 워커가 있으면 워커가 만든 Flight 바이트를 sendErrorsToBrowser 로 (L4612)

 validateInstantConfigsInBuild 의 실패
      --> StaticGenBailoutError. export/worker.ts L586-607 이 잡아 `{ error: true }` 를 돌려준다
          ★ `new StaticGenBailoutError()` 는 메시지가 비어 있어 L598-601 이 덧붙여 찍는 문구가 없다.
            원인은 그 전에 console.error 로 찍힌 검증 오류들이다 (APPR L7834-7841)
          [빌드] 04 가 실패 경로를 모아 ExportError 로 끝낸다

 isPageAllowedToBlock 의 참
      --> allowEmptyStaticShell. [동적 판별] 04 의 정적 셸 판정이 봐준다

 needsFullTree (APPR L696-704)
      --> 개발 + cacheComponents 에서 검증이 필요하면 RSC 페이로드가
          공유 레이아웃을 건너뛰지 않고 **트리 전체**를 그린다. [03]이 자를 재료다
```

## 다루지 않는 것

정적 셸 검증(`validateStaticShell` L6637-6709 · `validateStagedShell` L6889-7053)의 본문, 클라이언트 모듈 예열(`warmupClientModulesForStagedValidation` L6711-6887), 개발 서버의 스테이지 렌더 자체(`streamStagedRenderInDev` L5204-5432 의 reveal 규칙과 `_revealAfter`), 캐시를 데운 재렌더 두 종(`renderWithWarmCachesForValidationInDev` L5446 · `prerenderWithWarmCachesForStaticValidationInDev` L5546)의 본문, 빌드용 두 번 렌더(`renderWithRestartOnCacheMissInValidation` L7487-7724)의 본문, 검증 워커(`server/dev/dev-validation-worker-pool.ts` · `dev-validation-worker-globals.ts` · `dev-validation-worker-snapshot.ts`)와 스냅숏 직렬화, 개발 오버레이가 오류를 보여 주는 쪽(`next-devtools/`), 요청 API 가 `validation-client` 스토어에서 고르는 갈래(`params.ts` · `search-params.ts` · `root-params.ts` · `client/components/instant-samples.ts`), 스택 정규식과 판정 규칙(`dynamic-rendering.ts` L767-1592), Instant Navigation Testing API(`isInstantNavigationTest` · `NEXT_INSTANT_TEST_COOKIE`), SWC 변환의 등록 절차(`chain_transforms.rs` L353 · `next_server/transforms.rs` L154)는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 검증을 켤지 정한다](01_gate/README.md)
- [02 응답이 나간 뒤 입력을 모은다](02_inputs/README.md)
- [03 깊이마다 새 트리를 조립한다](03_depth/README.md)
- [04 렌더하고 판정한다](04_verdict/README.md)
