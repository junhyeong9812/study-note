# 03 컴포넌트 스택을 정규식으로 읽는다

상위: [무엇이 동적인지 가려내기](../README.md)

동적 접근이 **어디서** 일어났는지 알아야 봐줄지 말지가 갈린다. 그런데 Next.js 는 그것을 트리 상태나 컨텍스트로 알아내지 않는다. **React 가 만든 컴포넌트 스택 문자열을 정규식으로 뒤진다.**

## 위치

`packages/next` / `src/server/app-render` / `dynamic-rendering.ts` L767-L802 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/dynamic-rendering.ts#L767-L802))

## 실제 코드

가장 복잡한 정규식 하나가 이 수법을 다 보여 준다.

```ts
// dynamic-rendering.ts L773-L787
// Detects when RootLayoutBoundary (our framework marker component) appears
// after Suspense in the component stack, indicating the root layout is wrapped
// within a Suspense boundary. Ensures no body/html/implicit-body components are in between.
//
// Example matches:
//   at Suspense (<anonymous>)
//   at __next_root_layout_boundary__ (<anonymous>)
//
// Or with other components in between (but not body/html/implicit-body):
//   at Suspense (<anonymous>)
//   at SomeComponent (<anonymous>)
//   at __next_root_layout_boundary__ (<anonymous>)
const hasSuspenseBeforeRootLayoutWithoutBodyOrImplicitBodyRegex = new RegExp(
  `\\n\\s+at Suspense \\(<anonymous>\\)(?:(?!\\n\\s+at (?:${bodyAndImplicitTags}) \\(<anonymous>\\))[\\s\\S])*?\\n\\s+at ${ROOT_LAYOUT_BOUNDARY_NAME} \\([^\\n]*\\)`
)
```

```text
 ★★★ 스택에서 **Suspense 와 루트 레이아웃 사이에 body 가 없는지** 본다

   \n  at Suspense (<anonymous>)
   (그 사이에 body|div|main|section|... 가 나오면 안 된다)
   \n  at __next_root_layout_boundary__ (...)

 => `(?:(?!\n\s+at (?:body|div|...) \(<anonymous>\))[\s\S])*?` 가
    **부정 전방탐색을 문자마다 반복**해 "그 사이에 없음" 을 표현한다
 ★ 암묵적 body 로 취급되는 태그 목록을 직접 들고 있다 (L770-771)
   body · div · main · section · article · aside · header · footer ·
   nav · form · p · span · h1~h6
   주석 L769 - "Common implicit body tags that React will treat as body
     when placed directly in html"
 => 즉 `<html><div>` 라고 써도 React 가 body 로 본다는 사실을 정규식이 알아야 한다
```

## 동작 흐름

```text
 정규식 일곱 (L767-802)

 hasSuspenseRegex                     \n␣at Suspense (<anonymous>)          L767
 hasSuspenseBeforeRootLayout…Regex    위 실제 코드                          L785
 hasMetadataRegex                     \n␣at ${METADATA_BOUNDARY_NAME}       L789
 hasViewportRegex                     \n␣at ${VIEWPORT_BOUNDARY_NAME}       L792
 hasOutletRegex                       \n␣at ${OUTLET_BOUNDARY_NAME}         L795
 hasInstantValidationBoundaryRegex    \n␣at ${INSTANT_VALIDATION_BOUNDARY_NAME}  L797
 slotMarkerRegex                      \n␣at __next_instant_slot_(\d+)__     L800

 ★★★ 일곱 중 **여섯이 마커 컴포넌트**를 찾는다
   lib/framework/boundary-constants.tsx 의 넷 —
     METADATA_BOUNDARY_NAME · VIEWPORT_BOUNDARY_NAME ·
     OUTLET_BOUNDARY_NAME · ROOT_LAYOUT_BOUNDARY_NAME
   instant-validation/boundary-constants.ts 의 둘 —
     INSTANT_VALIDATION_BOUNDARY_NAME · 슬롯 마커 `__next_instant_slot_N__`
   React 자체를 찾는 것은 `hasSuspenseRegex` **하나**뿐이다
 => 아무 일도 안 하는 컴포넌트를 트리에 심어 두고,
    **스택 문자열에 이름이 찍히게** 만들어 위치를 표시한다
 ★ slotMarkerRegex 만 캡처 그룹이 있다 — 번호를 꺼내 쓴다 (아래)
```

```text
 ★★★ trackAllowedDynamicAccess 가 **여섯 갈래 사다리**다 (L865-918)

 들어오는 길 — app-render.tsx L9145-9165 의 React `onError` 다.
   `isPrerenderInterruptedError(err) || signal.aborted` 이면
   `errorInfo.componentStack` 과 함께 여기로 넘긴다
 => `dynamicReason` 은 [01]이 만든 그 중단 오류이고,
    `componentStack` 은 React 가 준 문자열이다

 L874  hasOutletRegex             => trackOutletSuspenseAboveBody(...) 하고 return
        ★★★ 그 docstring(L829-851)이 이 칸의 존재 이유를 적는다 —
          outlet 자체는 의미 있는 동적 원천이 아니지만 **그 스택만이
          사용자 루트 레이아웃을 지나가므로**, body 위 Suspense 를 발견할
          유일한 기회다. 그래서 `hasSuspenseAboveBody` 만 세우고
          `hasAllowedDynamic` 은 **일부러 세우지 않는다** —
          dynamic metadata 는 본문에 진짜 구멍이 있을 때만 봐줘야 하는데
          outlet 기반 탐지가 그 경우를 가려 버리면 안 되기 때문이다
        => [04]의 metadata 조건에 `hasAllowedDynamic === false` 가 들어간
           이유가 여기 있다
 L877  hasMetadataRegex           => hasDynamicMetadata = true
 L880  hasViewportRegex           => hasDynamicViewport = true
 L884  hasSuspenseBeforeRootLayout…  => hasAllowedDynamic = true
                                      + hasSuspenseAboveBody = true
 L894  hasSuspenseRegex           => hasAllowedDynamic = true
 L899  syncDynamicError 가 있으면 => dynamicErrors 에 밀어 넣는다

 그 아래로 내려오면 (전부 아니면)
 L904  isClientHookDynamicError(dynamicReason) 이면   ← `useDynamicRouteParams`(L659-664) ·
          `useDynamicSearchParams`(L730-735)가 만든 `ClientHookDynamicError` 다.
          그 문구가 `<Suspense>` 와 `export const instant = false` 두 처방을
          직접 제시한다 (dynamic-rendering-utils.ts L39-52)
        => [04]의 `allowEmptyStaticShell`(= instant = false)로 이어지는 고리다
 L905    => addErrorContext(그 오류, componentStack, null) 을 dynamicErrors 에
 L911  그 밖 => createDynamicOrRuntimeBodyError(route)(L912)를 만들어 dynamicErrors 에

 ★★ **순서가 곧 우선순위**다. 위에서 걸리면 아래는 안 본다
 ★★★ 그리고 **같은 사다리가 세 번** 있다 —
   trackAllowedDynamicAccess(L874) · trackDynamicHoleInRuntimeShell(L1167) ·
   trackDynamicHoleInStaticShell(L1232). 정규식 순서까지 같다
 ★★ 다만 "문구만 다르다" 가 아니다 — **쓰는 필드가 다르다.**
   앞엣것은 `hasDynamicMetadata = true`(boolean, L878),
   뒤 둘은 `dynamicMetadata = error`(Error 객체, L1176 · L1241).
   그래서 [04]의 판정 쪽 조건도 서로 다르다

 ★★★ `trackDynamicHoleInNavigation`(L960-1104)은 **네 번째가 아니라 다른 사다리**다
   - outlet 칸이 `trackOutletSuspenseAboveBody` 를 안 부르고 그냥 return 한다 (L971-974)
     => 이 경로는 `hasSuspenseAboveBody` 를 **절대 세우지 않는다**
   - `hasSuspenseBeforeRootLayout…` 칸이 **아예 없다**
   - 대신 `hasInstantValidationBoundaryRegex` 칸(L1010-)이 있고,
     `test()` 가 아니라 **`exec()` 의 index 를 비교한다** (L1060-1068)
       suspenseLocation.index < boundaryLocation.index 이면 봐준다
     => 정규식을 "있나" 가 아니라 **"어느 쪽이 위인가"** 로 쓴다
   - `allRequiredBoundariesRendered` · `hasAllowedClientDynamicAboveBoundary` ·
     `validationPreventingErrors` 칸이 더 있다 (L1021-1038)
   - `resolveInstantStack` 은 **이 함수에서만** 불린다 (L978)
 => Outlet · metadata · viewport 안에서 난 것은 "본문" 문제가 아니므로 따로 표시만 하고,
    Suspense 아래면 **봐준다**(hasAllowedDynamic), 아무것도 아니면 **오류로 쌓는다**
```

```text
 ★★★ Suspense 가 body 위에 있으면 봐주는 이유 (주석 L888-890)

   "For Suspense within body, the prelude wouldn't be empty so it wouldn't
    violate the empty static shells rule. But if you have Suspense above body,
    the prelude is empty but we allow that because having Suspense is an
    **explicit signal from the user that they acknowledge the empty shell**
    and want dynamic rendering."

 => Suspense 가 body 안에 있으면 셸이 비지 않는다 — 문제가 안 된다
 => Suspense 가 body **위**에 있으면 셸이 빈다. 그런데도 봐준다.
    사용자가 "빈 셸이어도 좋다" 고 명시한 것으로 읽기 때문이다
 ★ 그래서 앞의 그 복잡한 정규식이 필요하다 — "Suspense 와 루트 레이아웃 사이에
   body 가 없다" 가 정확히 "Suspense 가 body 위에 있다" 를 뜻한다
 ★★ 설정 항목이 아니라 **트리의 모양**이 옵트인이다.
   `allowEmptyStaticShell` 플래그와 나란히 쓰이는 것이 [04]에서 보인다
 ★ 그냥 Suspense(L894)만 있어도 봐주지만 그때는 hasSuspenseAboveBody 를 안 켠다.
   [04]가 그 둘을 다르게 쓴다
```

```text
 ★★ 슬롯 번호로 오류의 주인을 찾는다 (L804-850)

 resolveInstantStack(componentStack, dynamicValidation)   L808
 docstring L804-807
   "Look up the config factory for the slot this error belongs to.
    Checks the component stack for a slot marker (__next_instant_slot_N__)
    and returns the config at that index. Falls back to index 0 (root config)
    when no slot marker is found or the slot has no config."

 => `slotStacks: Array<(() => Error) | null>` (L941)에서 꺼낸다
 ★★ 그런데 docstring 이 "that index" 라고만 해서 오해하기 쉽다 —
   코드는 **N + 1** 번째를 본다 (L818 `parseInt(match[1], 10) + 1`)
   주석 L816-817 - "Slot markers are 0-indexed in the component name but
     slotStacks is 1-indexed (index 0 is the root config)."
 => 없으면 0 번(루트)으로 떨어진다
 ★ 스택 문자열에서 **정수를 캡처해 배열 인덱스로** 쓴다.
   마커 컴포넌트의 이름이 곧 색인이다
```

```text
 ★ 이 수법의 대가

 => 컴포넌트 이름이 바뀌면 판정이 조용히 틀어진다.
    그래서 이름들이 `boundary-constants` 에 상수로 모여 있고
    정규식이 그 상수를 **문자열 보간**으로 쓴다 (L785-802)
 => 프로덕션 빌드의 함수 이름 압축(minify)에 걸리면 안 되므로
    마커 이름이 `__next_...__` 같은 예약어 꼴이다
 ★ [`'use cache'`] [02]에서 본 `{ [name]: async ... }[name]` 수법과 같은 계열이다 —
   **함수 이름이 관측 대상**이라 이름을 지키는 코드가 따로 있다
 ※ 압축 관련 문장은 내 추론이다. 소스가 그렇게 적지는 않았다
```

## 결과가 쓰이는 곳

```text
 DynamicValidationState.hasAllowedDynamic
      --> [04]가 "봐줄 수 있는 동적" 이 있었는지 볼 때. metadata 판정의 전제

 DynamicValidationState.hasSuspenseAboveBody
      --> [04]가 `allowEmptyStaticShell` 과 **같은 뜻으로** 취급한다.
          빈 셸 오류를 통째로 건너뛰는 두 길 중 하나

 DynamicValidationState.hasDynamicMetadata / hasDynamicViewport
      --> [04]가 각각 다른 오류 문구로 빌드를 세운다

 DynamicValidationState.dynamicErrors
      --> [04]가 하나씩 console.error 로 찍고 빌드를 세운다

 InstantValidationState.slotStacks
      --> resolveInstantStack 이 꺼내 쓰는 배열. 오류에 붙일 스택을 고른다
```

## 다루지 않는 것

`boundary-constants` 의 마커 이름 넷과 그 컴포넌트를 트리에 심는 쪽, `instant-validation/boundary-constants` 의 `INSTANT_VALIDATION_BOUNDARY_NAME` · 슬롯 마커 접두/접미사와 `boundary-tracking.tsx` 의 `allRequiredBoundariesRendered`, `trackOutletSuspenseAboveBody`(L852)의 본문 세 줄, `addErrorContext`(L1295)가 오류에 스택을 붙이는 방식, `resolveInstantStack`(L808)을 유일하게 부르는 `trackDynamicHoleInNavigation`(L978)과 그 계열 네 함수의 본문, `createDynamicOrRuntimeBodyError` 등 `blocking-route-messages.ts` 의 문구 생성, `isClientHookDynamicError` · `ClientHookDynamicError`(`dynamic-rendering-utils.ts`), React 가 컴포넌트 스택 문자열을 만드는 형식 자체는 이 문서의 범위 밖이다.
