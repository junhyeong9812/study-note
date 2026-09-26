# 01 검증을 켤지 정한다

상위: [즉시 내비게이션을 개발 중에 검증하기까지](../README.md)

`export const instant` 은 값이 넷이다 — 없음 · `true` · `false` · 객체. 여기에 next.config 의 수준 넷이 곱해진다. 그 조합을 로더 트리 전체에 대해 한 번에 판정하는 것이 `anySegmentNeedsInstantValidation` 이고, 개발의 두 진입과 빌드의 한 진입이 그 판정 **앞에** 각자 관문을 더 둔다.

## 위치

`packages/next` / `src/server/app-render/instant-validation` / `instant-config.tsx` L132-L230 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/instant-validation/instant-config.tsx#L132-L230))

## 실제 코드

세그먼트 하나를 보는 갈래다. `visit` 이 로더 트리를 깊이 우선으로 돌며 이것을 되풀이한다.

```tsx
// instant-config.tsx L182-L216
    if (instantConfig === false) {
      // Explicit opt-out. Doesn't itself trigger validation.
    } else if (instantConfig === true) {
      // Explicit opt-in using the default level.
      if (level <= baseValidationLevel) {
        needsValidation = true
      }
    } else if (typeof instantConfig === 'object' && instantConfig !== null) {
      if (
        instantConfig.unstable_disableValidation === true ||
        (level === VALIDATION_LEVEL.WARNING &&
          instantConfig.unstable_disableDevValidation === true) ||
        (level === VALIDATION_LEVEL.ERROR &&
          instantConfig.unstable_disableBuildValidation === true)
      ) {
        disabled = true
        return
      }

      if (instantConfig.level !== undefined) {
        const configuredLevel =
          instantConfig.level === 'experimental-error'
            ? VALIDATION_LEVEL.ERROR
            : VALIDATION_LEVEL.WARNING
        if (level <= configuredLevel) {
          needsValidation = true
        }
      } else if (level <= baseValidationLevel) {
        needsValidation = true
      }
    } else if (applyDefaultValidation && isImplicitValidationSegment(tree[0])) {
      // No explicit config. Implicit validation applies to page/default
      // segments when the default level is active for this mode.
      needsValidation = true
    }
```

```text
 instant = false     아무것도 안 한다. 주석 L183 "Doesn't itself trigger validation."
                     ★ 그리고 **자식 방문을 막지도 않는다** — L218-222 가 그대로 내려간다
                     => 레이아웃에 false 를 달아도 그 아래 page 의 암묵 검증이 이 판정을 켠다
                        (그 false 가 실제로 무엇을 끄는지는 [03]의 "지역 설정 우선" 이다)
 instant = true      level <= base 일 때만 켠다
 객체                unstable_disable* 중 하나가 맞으면 **트리 전체**의 즉시 검증을 끈다 (disabled = true)
                     (정적 셸 검증은 별개다 — 초기 HTML 은 shouldValidate: true 그대로, APPR L3513)
                     level 필드가 있으면 base 대신 그 값과 비교한다
 없음                applyDefaultValidation && page/default 세그먼트면 켠다

 ★★★ disable 은 "이 세그먼트만" 이 아니다
   docstring L129-130 - "`unstable_disableValidation` on any segment kills validation
                         for the whole tree."
   L225-229 - disabled 면 needsValidation 이 참이어도 **false 를 돌려준다**
   => 깊은 page 하나가 끄면 위 레이아웃이 켠 요구도 사라진다
 ★ 세 disable 중 Dev 는 level === WARNING 일 때, Build 는 ERROR 일 때만 본다 (L192-195)
```

```text
 ★★ 런타임에 오기 **전에** 걸러지는 조합 — build/analysis/get-page-static-info.ts
   L703-707  'use client' 파일의 `instant` export             => 오류
   L709-713  cacheComponents 없이 `instant` export             => 오류
             "cannot use `export const instant = ...` without enabling `cacheComponents`"
   L739-743  `unstable_dynamicStaleTime` 과 `instant` 를 함께    => 오류
   스키마(build/segment-config/app/app-segment-config.ts L22-37) — `level` 은 'warning' |
     'experimental-error' 뿐이고 disable 플래그는 `true` 만, `.strict()` 다
 => 위 "값 넷 × 수준 넷" 중 일부는 여기서 끝난다. cacheComponents 가 꺼져 있으면 `instant` 자체가 빌드 오류다
```

## 동작 흐름

```text
 anySegmentNeedsInstantValidation(rootTree, level)   ICONF L132-230

 L137  workStore 가 없으면 => throw InvariantError
 L142  validationLevel = workStore.validationLevel
         work-store.ts L158 이 renderOpts.validationLevel 에서 옮긴다
         renderOpts 에 넣는 쪽 — app-page-runtime.ts L940-941(개발·런타임) · export/index.ts L486(빌드)
           · edge-ssr-app.ts L166(Edge 페이지). base-server.ts L595-596 도 넣는다
         그 뒤 워커 스냅숏(APPR L6351)과 빌드 샘플 WorkStore(L7948)가 이 값을 옮겨 싣는다
 L146  switch — manual-* 이면 manualValidation = true, 수준은 WARNING/ERROR 둘로 접힌다
 L163  applyDefaultValidation (README 의 실제 코드)
 L174  visit(tree)
 L177    getLayoutOrPageModule(tree) 로 모듈을 **실제로 불러온다**
 L182    네 갈래 (위 실제 코드)
 L218    parallelRoutes 전부로 재귀 — disabled 면 즉시 멈춘다
 L225  => disabled ? false : needsValidation

 ★ 설정을 안 읽고 'warning' 을 **박아 넣는** 자리가 다섯 있다 (grep `validationLevel: 'warning'`)
   web/adapter.ts L335 · web/edge-route-module-wrapper.ts L130      Proxy · Edge Route Handler (둘 다 TODO 주석.
                                                                  주석 L332 "Proxy doesn't run…" · L127 "Edge runtime doesn't run…")
   build/static-paths/app.ts L909 · export/routes/app-route.ts L79   generateStaticParams · Route Handler (〃)
   server/dev/use-cache-probe-worker.ts L224                          'use cache' 멈춤 탐지 워커
     (주석 L222-223 - "the validation level is irrelevant because we do not perform validation")
 ※ 다섯 다 이 문서의 검증 진입(개발은 Edge 제외, 빌드는 app-page prerender)에
   닿지 않는 경로로 보여, 이 고정값이 검증 결과를 바꾸는 길은 찾지 못했다
```

```text
 개발 관문 둘 — 판정 함수를 부르기 **전에** 거르는 것

 ① 초기 HTML   renderToStream 안  APPR L3452-3498
      __NEXT_DEV_SERVER && NEXT_RUNTIME !== 'edge' && cacheComponents
      && createRequestStore && !isBypassingCachesInDev(requestStore, workStore)
   => stagedRenderWithCachesInDev({ shouldValidate: **true**, navigationKind: 'initial-load' })
   ★ 여기는 판정 함수를 **안 본다.** 정적 셸 검증이 늘 필요하기 때문이다
     (즉시 검증 여부는 [02]의 prepareValidationInputs 가 다시 묻는다)
   아니면 L3533 logValidationSkipped(ctx) 후 캐시 없는 스테이지 렌더

 ② RSC 요청     generateDynamicFlightRenderResultWithStagesInDev  APPR L1294
      (진입 조건은 L2944-2950 — 위 ①의 앞 세 조건과 같다)
   L1343  shouldValidate =
            !ctx.isPrefetch
            && !isBypassingCachesInDev(initialRequestStore, workStore)
            && (isHmrRefresh === true || await anySegmentNeedsInstantValidationInDev(loaderTree))
   L1377  createRequestStore && !isBypassing… 이면 stagedRenderWithCachesInDev
   ★★ 클라이언트 내비게이션은 **판정이 참이거나 HMR 새로고침일 때만** 검증한다
     주석 L1340-1342 - "We validate RSC requests for HMR refreshes and client navigations
       when instant configs exist, since we render all the layouts necessary to perform
       the validation in those cases."
   ★ 프리페치 요청(ctx.isPrefetch)은 검증하지 않는다
   ★ 런타임 프리페치 요청은 이 함수까지 오지도 않는다 — L2934 의 isRuntimePrefetchRequest 갈래가 먼저다

 isBypassingCachesInDev 의 뜻 — 주석 L1381-1383
   "disable cache" in devtools, a hard refresh (cache-control: "no-cache"), or draft mode
```

```text
 ★★★ 판정이 참이면 **RSC 페이로드의 모양이 바뀐다** (APPR L694-704)

   needsFullTree =
     process.env.__NEXT_DEV_SERVER && ctx.renderOpts.cacheComponents
     && !(request 스토어 && isBypassingCachesInDev(...))
     && !options?.actionResult           // Only for navigations
     && await anySegmentNeedsInstantValidationInDev(loaderTree)

   주석 L694-695 - "If we're performing instant validation, we need to render the whole
     tree, without skipping shared layouts."
 => 보통의 클라이언트 내비게이션은 이미 가진 레이아웃을 건너뛴 페이로드를 받는다.
    검증은 **공유 레이아웃까지 있어야** [03]에서 "여기까지 공유, 여기부터 새것" 을 자를 수 있다
 => 그래서 ②의 판정과 이 판정이 같은 함수다.
 ★ 그런데 needsFullTree 에는 `isPrefetch` 조건이 **없다** — 관문이 참이면 (PPR 꺼진) 프리페치
   RSC 응답도 공유 레이아웃까지 전부 그린다. 검증(②의 shouldValidate)만 프리페치를 뺀다
    cacheScopedToWorkStore 가 같은 요청 안의 두 번째 호출을 캐시에서 돌려준다
```

```text
 빌드 관문 — 라우트당 한 번

 export/index.ts L746-766
   cacheComponents 면 모든 exportPath 를 돌며 **라우트(page)마다 처음 것에만**
   exportPath._runInstantValidation = true
   주석 L747 - "Only run instant validation once per route, even if multiple param sets
               from generateStaticParams exist."
 export/worker.ts L121 → L281 renderOpts.runInstantValidation

 APPR L2873-2885  (prerenderToStream 이 끝나고 RenderResult 까지 만든 뒤)
   workStore.cacheComponentsEnabled && workStore.isBuildTimePrerendering
   && renderOpts.runInstantValidation
   && await anySegmentNeedsInstantValidationInBuild(loaderTree)
   => validateInstantConfigsInBuild(ctx, response.renderResumeDataCache ?? null)   [04]
 ★ ISR 재검증의 prerender 는 isBuildTimePrerendering 이 거짓이라 여기 오지 않는다
   (그 필드의 뜻은 [`'use cache'`] 03 참조)
```

```text
 ★★ `instant = false` 의 다른 효과 — 검증 여부와 **별개로** 정적 셸을 봐준다

 isPageAllowedToBlock(tree)   ICONF L85-115
   위에서 아래로 내려가며 **처음 만난 설정이 이긴다**
     false  => true  (막아도 된다)
     그 밖   => false (막으면 안 된다)
   주석 L93-96 - "If we encounter a non-false instant config before a instant=false,
     the page isn't allowed to block. The config expresses a requirement for instant UI,
     so we should make sure that a static shell exists."
   설정이 없으면 parallelRoutes 중 **하나라도** 참이면 참 (L105-113)

 부르는 곳 둘 (grep isPageAllowedToBlock)
   APPR L6658-6660  validateStaticShell       개발의 정적 셸 검증
   APPR L8279-8281  prerenderToStream         빌드·ISR 의 정적 셸 판정
   둘 다 `(renderOpts.allowEmptyStaticShell ?? false) || isPageAllowedToBlock(...)`
 => [동적 판별] 04 의 `allowEmptyStaticShell` 이 설정으로 켜지는 길이 이것이다
```

## 결과가 쓰이는 곳

```text
 anySegmentNeedsInstantValidationInDev 의 참/거짓 — 부르는 곳 다섯 (grep)
      --> APPR L704   needsFullTree            RSC 페이로드에 공유 레이아웃까지
      --> APPR L1347  shouldValidate           RSC 요청을 검증할지
      --> APPR L4848 · L4942  prepareValidationInputs*   즉시 검증 입력을 만들지 [02]
      --> APPR L6490  runValidationInDev       즉시 검증을 돌지 [02]

 anySegmentNeedsInstantValidationInBuild
      --> APPR L2877  빌드 검증을 돌지 [04]

 isPageAllowedToBlock
      --> allowEmptyStaticShell (정적 셸 판정)
```

## 다루지 않는 것

`getLayoutOrPageModule` 이 모듈을 불러오는 방식과 `parseLoaderTree`, `isFrameworkErrorRoute`(L46-51)가 가리키는 `_global-error` · `_not-found` 라우트의 합성, `anySegmentHasPartialPrefetchingEnabled`(L59-83)와 `export const prefetch` 설정([02]에서 결과만 쓴다), `resolveInstantConfigSamplesForPage`(L242-277 — [04]), `isBypassingCachesInDev` 의 구현, `stagedRenderWithoutCachesInDevNode` 의 캐시 없는 렌더, `InstantConfig` 의 `unstable_from` 필드(스키마 `app-segment-config.ts` L26 외에 읽는 곳을 찾지 못했다), `create-flight-router-state-from-loader-tree.ts` 의 프리페치 힌트 비트 전체는 이 문서의 범위 밖이다.
