# 03 깊이마다 새 트리를 조립한다

상위: [즉시 내비게이션을 개발 중에 검증하기까지](../README.md)

한 페이지의 RSC 스트림을 **세그먼트마다, 단계마다** 따로 떼어 캐시에 담아 둔다. 그리고 "URL 의 이 깊이까지는 이미 화면에 있고, 그 아래가 새로 들어온다" 는 가상의 내비게이션마다, 위쪽은 Dynamic 단계(다 그려진 것) · 아래쪽은 프리페치 단계(프리페치로 받았을 것)로 이어 붙인 **합성 페이로드**를 만든다. 경계 자리에는 이름 붙은 컴포넌트를 하나 심는다.

## 위치

`packages/next` / `src/server/app-render/instant-validation` / `instant-validation.tsx` L1022-L1511 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/instant-validation/instant-validation.tsx#L1022-L1511))

## 실제 코드

새 서브트리의 세그먼트 하나가 "즉시 UI 를 요구하는가" 를 정하는 규칙이다.

```tsx
// instant-validation.tsx L1406-L1425
    // Local config takes precedence over children.
    let requiresInstantUI: boolean
    let createInstantStack: (() => Error) | null
    let configDepth: number
    if (instantConfig === false) {
      requiresInstantUI = false
      createInstantStack = null
      configDepth = -1
    } else if (
      instantConfig === true ||
      (typeof instantConfig === 'object' && instantConfig !== null)
    ) {
      requiresInstantUI = true
      createInstantStack = localCreateInstantStack
      configDepth = segmentDepth
    } else {
      requiresInstantUI = childrenRequireInstantUI
      createInstantStack = childCreateInstantStack
      configDepth = bestChildConfigDepth
    }
```

```text
 ★★★ **자기 설정이 자식을 이긴다** — 주석 L1406 "Local config takes precedence over children."
   instant = false       자식이 요구해도 requiresInstantUI = false
   instant = true/객체   자식과 무관하게 true, configDepth = 이 세그먼트의 깊이
   설정 없음             자식에게서 올라온 것을 그대로

 => [01]의 판정 함수는 false 를 "아무것도 안 한다" 로 넘기고 자식을 계속 봤다.
    여기서는 false 가 **그 아래 요구를 지운다**
 ※ 그래서 레이아웃의 `instant = false` 는 "이 레이아웃이 **새로 들어오는** 내비게이션은
   막혀도 된다" 로 읽힌다. 그 레이아웃이 경계 위(공유)에 있는 깊이에서는 buildNewTreeSeedData 가
   그것을 보지 않으므로 아래 page 의 요구가 살아남는다 (L1094-1263 이 공유 쪽을 따로 걷는다)

 ★ 설정 없는 page/default 는 L1291-1299 에서 **true 로 승격된다**
   (validationLevel 이 manual-* 가 아니고, 프레임워크 오류 라우트가 아니고, page/default 세그먼트)
 ★★ [01]의 암묵 검증(ICONF L163-169 applyDefaultValidation)과 **같지 않다** — 거기 있는
   `level <= baseValidationLevel` 이 여기엔 없다. 개발(level 0)에서는 결과가 같지만,
   빌드에서는 관문이 한 번 켜지면 base 가 'warning' 이어도 설정 없는 page/default 가 검증된다
 ★ 그리고 이 루프는 세그먼트의 `level` 도 읽지 않는다 (L1410-1420) — 수준은 [01]의 관문에서만 쓰인다
```

## 동작 흐름

```text
 validateInstantConfigs 가 부르는 순서 (APPR L7109 · L7400 · L7160 · L7189)

 ① collectStagedSegmentData(prefetchKind, ...)   IVAL L218-270   페이지당 한 번
 ② discoverValidationDepths(loaderTree)          IVAL L938-984   페이지당 한 번
 ③ createCombinedPayloadAtDepth(...)             IVAL L1022-1511 깊이 × 그룹 깊이마다
 ④ createCombinedPayloadStream(...)              IVAL L563-665   ③이 null 이 아닐 때만
```

```text
 ① 스트림을 세그먼트 × 단계로 자른다   collectStagedSegmentData  IVAL L218-270

 L231  partialStages 를 종류마다 **둘만** 고른다
         Shell              [ShellRuntime, Runtime]
         LegacySpeculative  [Static, Runtime]
 L264  그 둘을 차례로 doStage, 그리고 L267 Dynamic 을 마지막에 → payload 를 돌려받는다
 ★ Shell 은 Static 을, Legacy 는 ShellRuntime 을 **담지 않는다.**
   ③의 getStageEntry(L837-849)가 없는 단계를 찾으면 InvariantError 를 던지므로,
   ③이 고르는 단계(L1317-1339)가 정확히 이 둘과 Runtime 안에 있어야 한다 — 실제로 그렇다

 collectSegmentDataForStage   IVAL L272-454  (단계 하나)
 L293  createStagedStreamFromChunks(fullPageChunks)   — 청크 배열을 **단계를 올려 가며** 흘리는 스트림
 L327  createFromNodeStream(stream, ..., { startTime, endTime })
         주석 L334-341 - 단계마다 그 단계가 **끝난 시각**을 endTime 으로 준다.
           이 첫 역직렬화에서 해야 한다. 다시 직렬화하면 React 가 IO 시각을 지금으로
           잘라 버려 "이 단계 뒤에 끝난 IO" 를 가려낼 수 없다
 L349  controller.advanceStage(firstStage)
         주석 L345-348 - 바깥 구조는 어느 단계에서나 읽혀야 한다.
           await **전에** 해야 한다. 아니면 교착이다
 L360  traverseRootSeedDataSegments — 세그먼트 경로(SegmentPath)마다 SegmentData 를 뽑는다
 L411  runInSequentialTasks(
         () => 목표 단계로 올리고 head 와 세그먼트마다 renderFlightStream 으로 **다시 인코딩**,
         () => Dynamic 으로 올린다   (늦게 온 디버그 정보용, 주석 L407-410)
       )
 L542  writeChunk — currentStage <= targetStage 인 청크만 chunks 에, 전부는 allChunks 에
         ★ RenderStage 값이 13 < 21 < 23 < 30 이라 `<=` 하나로 단계를 비교한다
           (staged-rendering.ts L4-16)

 결과 SegmentCache = { head, segments: Map<SegmentPath, 단계별 {chunks, allChunks, debugChunks}> }
```

```text
 ② 깊이의 범위를 잰다   discoverValidationDepths  IVAL L938-984

 segmentConsumesURLDepth (L890-904)
   동적 세그먼트(튜플) · 일반 이름 · 루트 ''      => URL 깊이를 하나 쓴다
   __PAGE__ · (그룹) · __DEFAULT__ · /_not-found  => 안 쓴다
 L966-975  진짜 라우트 그룹이면 그룹 깊이를 센다 — 합성 세그먼트 '(__SLOT__)' 는 뺀다
   주석 L970-972 - "The synthetic group can't be a real navigation boundary."
 => 반환: 배열[URL 깊이] = 그 깊이와 다음 URL 세그먼트 사이 그룹 수의 **최댓값**
   docstring 예 (L932-936)
     '' / (outer) / (inner) / dashboard / page   =>  [2, 0]

 ★★ 왜 그룹을 세는가 — docstring L909-919
   "When a user navigates between sibling routes that share a route group layout,
    that layout is already mounted — its Suspense boundaries are revealed and don't
    cover new content below. ... This is conservative: some boundaries may not
    correspond to real navigations (e.g. a route group with no siblings), but it
    ensures we don't miss real violations."
 => 이미 떠 있는 레이아웃의 Suspense 는 **이미 드러나 있어서** 새 내용을 가려 주지 못한다.
    그래서 그룹 레이아웃마다 "여기가 공유 경계였다면" 을 따로 해 본다
 ★ 병렬 슬롯이 여럿이면 가장 깊은 슬롯이 범위를 정한다 (L920-925)
```

```text
 ③ 합성 페이로드   createCombinedPayloadAtDepth  IVAL L1022-1511 (490줄, 파일 끝까지)

 buildSharedTreeSeedData  L1094-1263     ← 루트부터 여기로 시작 (L1440-1447)
 L1115    Dynamic 단계 청크로 역직렬화한다 (이미 떠 있는 레이아웃)
 L1137    URL 세그먼트면 URL 깊이 +1 · 그룹 깊이 0, 그룹이면 그룹 깊이 +1
 L1146    pastUrlBoundary = nextUrlDepth > depth
 L1147    isBoundary = pastUrlBoundary && currentGroupDepth >= groupDepth
 L1149    경계면
 L1155      이 세그먼트의 노드를 <PlaceValidationBoundaryBelowThisLevel id={path}> 로 감싼다
 L1176      자식 슬롯 전부를 buildNewTreeSeedData 로 — 여기부터 **새 트리**
 L1206      자식 중 하나라도 requiresInstantUI 면
 L1207        boundaryState.requiredIds.set(path, slotModFilePaths)   "이 경계는 그려져야 한다"
              주석 L1203-1205 - 설정 없는 슬롯은 안 그려져도 된다 (레이아웃이 뺄 수 있다)
 L1221    경계가 아니면 공유로 계속 내려간다

 buildNewTreeSeedData  L1265-1438
 L1272    모듈을 불러 instant 를 읽는다 (L1285)  + 승격(L1291-1299)
 L1305    true/객체면 모듈의 __debugCreateInstantConfigStack 을 오류 팩토리로 든다
 L1317    단계를 고른다
            Shell              → useRuntimeStage… ? Runtime : ShellRuntime
            LegacySpeculative  → useRuntimeStage… ? Runtime : Static
 L1341    Static 이면 hasStaticSegments, Runtime 이면 hasRuntimeSegments
            ★ Shell 의 ShellRuntime 은 둘 다 안 세운다 (주석 L1326-1327)
 L1358    그 단계의 chunks 로 역직렬화 — 모자란 부분은 allChunks 로 **나중에** 푼다
 L1376    자식 슬롯 재귀 → L1406 지역 설정 우선 (위 실제 코드)

 L1449  루트가 requiresInstantUI 가 아니면 => return null   ("이 깊이는 검증할 것이 없다")
 L1455  slotStacks[0] = 루트의 오류 팩토리
 L1459  head 단계 — Shell 은 위와 같고, Legacy 는 **Runtime 세그먼트가 하나라도 있으면** Runtime
 L1501  payload = { ...initialRSCPayload, f: [[flightRouterState, seedData, head]] }
 L1506  => return { payload, hasAmbiguousErrors, slotStacks }
```

```text
 ★★★ 경계 표시는 **서버 컴포넌트 → 클라이언트 컨텍스트 → 레이아웃 라우터** 세 손을 거친다

 IVAL L1157   <PlaceValidationBoundaryBelowThisLevel id={path}>   (서버 레이어에서는 클라이언트 참조)
 IBOUND L70-83   컨텍스트에 id 를 넣기만 한다
                 주석 L78 "OuterLayoutRouter will see this and render a
                           `RenderValidationBoundaryAtThisLevel`."
 layout-router.tsx L779-781   서버 + __NEXT_CACHE_COMPONENTS 면 use(InstantValidationBoundaryContext)
 layout-router.tsx L912-922   id 가 문자열이면 templateValue 를 RenderValidationBoundaryAtThisLevel 로 감싼다
 IBOUND L85-100   그 안에서 이름 붙은 컴포넌트를 그리고 **컨텍스트를 null 로 되돌린다**
                  주석 L92 - 자식이 경계를 또 그리지 않게
 IBOUND L44-61    그 컴포넌트의 이름이 `__next_instant_validation_boundary__` 이고,
                  그려지면 boundaryState.renderedIds.add(id)

 => 경계 컴포넌트는 경계 세그먼트 **바로 아래 슬롯의 레이아웃 라우터** 안에 들어간다.
    그 이름이 컴포넌트 스택에 찍히고, [동적 판별] 03 의 정규식이 그 위치를 읽는다
 => requiredIds(L1207) − renderedIds 가 비어 있지 않으면 "경계가 안 그려졌다" 가 된다 [04]
 ★ IBOUND L13-17 - 브라우저 번들에 들어오면 InvariantError. 브라우저용 shim 은 전부 null 이다
   (client/components/instant-validation/impl.browser.tsx)
```

```text
 ★★ 병렬 슬롯 표시 — 오류를 **어느 `instant` 설정에** 돌릴지 (wrapSlotsWithMarkers L1056-1083)

 슬롯이 둘 이상인 갈림에서만(L1061) 슬롯마다 노드를 SlotMarker 로 감싼다
   markerName = `__next_instant_slot_${markerIndex - 1}__`   (L1069)
   slotStacks.push(그 슬롯의 오류 팩토리)
 IBOUND L115-138  SlotMarker 는 **그 이름의 함수 컴포넌트를 즉석에서 만들어** 캐시한다
   주석 L113-114 - "Renders a dynamically-named inner component so the slot index
     appears in the SSR component stack (__next_instant_slot_N__)."
 => 이름이 0 부터, slotStacks 는 1 부터다. DYNR L816-818 이 +1 로 맞춘다
 ★ 함수 이름을 지키려고 네임스페이스 객체 · slice(0) 를 쓴다 (IBOUND L42-43 · L103-104) —
   프로덕션 번들링의 이름 축소를 피하기 위해서다
```

```text
 ★★★ "모호하다" 는 사실상 **첫 번째 시도인가** 와 같다 (IVAL L1476-1492)

 Shell              hasAmbiguousErrors = !useRuntimeStageForPartialSegments
 LegacySpeculative  hasAmbiguousErrors = hasStaticSegments

   주석 L1479-1482 - 셸 프리페치의 구멍은 링크 데이터일 수도 동적 데이터일 수도 있다
   주석 L1487-1488 - 옛 프리페치에서 static 세그먼트의 구멍은 런타임 데이터일 수도 동적 데이터일 수도

 ※ 내 도출 — 첫 시도(useRuntime… = false)에서 Legacy 는 새 세그먼트가 **전부 Static** 이다 (L1335).
   그리고 null 이 아니려면 새 트리에 적어도 한 세그먼트가 있어야 한다(requiresInstantUI 는
   buildNewTreeSeedData 에서만 생긴다). 그러니 hasStaticSegments 는 첫 시도에서 늘 참이고,
   두 번째 시도(전부 Runtime)에서는 늘 거짓이다. Shell 은 식 그대로다
 => 두 종류 모두 "첫 시도 = 모호, 재시도 = 확정" 이다. [04]의 재시도가 이 값으로 갈린다
```

```text
 ④ 합성 페이로드를 스트림으로   createCombinedPayloadStream  IVAL L563-665

 L585  runInSequentialTasks(
         () => renderFlightStream(payload) 를 돌려 청크를 쌓는다 —
               isRenderable 인 동안 온 것만 renderableChunks 에,
         () => isRenderable = false; extraChunksAbortController.abort()
       )
 L656  createNodeStreamWithLateRelease(renderableChunks, allChunks, renderSignal)
 ★ 첫 태스크에서 나온 청크만 "렌더할 내용" 이다. 그 뒤 것은 renderSignal 이 끊길 때
   **디버그 정보로만** 풀어 준다 (stream-utils.ts L4-7 주석 —
   "This will not cause more contents to be rendered.")
 ※ 합성 페이로드 안에서 아직 안 풀린 구멍은 첫 태스크 안에 끝나지 못하므로 클라이언트
   prerender 에서 **매달린 채로** 중단된다. 그것이 [04]가 잡는 "동적 구멍" 이다
```

## 결과가 쓰이는 곳

```text
 ValidationPayloadResult.payload
      --> [04]가 createCombinedPayloadStream 을 거쳐 클라이언트 prerender(getClientPrerender)에 넣는다

 hasAmbiguousErrors
      --> [04]가 DynamicHoleKind 를 고르고, 오류가 나면 재시도할지 정한다

 slotStacks
      --> createInstantValidationState(slotStacks) → DYNR resolveInstantStack 이 오류의 스택으로 쓴다

 boundaryState.requiredIds
      --> [04]의 판정이 renderedIds 와 비교한다 (allRequiredBoundariesRendered)

 null
      --> "이 깊이에는 새로 들어오는 `instant` 가 없다". [04]의 루프가 건너뛴다
```

## 다루지 않는 것

`traverseCacheNodeSegments`(L129-168)와 `SegmentPath` 문자열 규칙(`stringifySegment` L182-188 · `createChildSegmentPath` L170-180), `createStagedStreamFromChunks`(L491-540)의 스트림 구현, `deserializeFromChunks`(L726-765)와 늦은 방출 스트림(`stream-utils.ts` 93줄), `onFlightRenderError`(L456-482)의 digest 규칙, `createValidationHead`(L690-711)와 head 의 `// TODO: handle head`(L684), `getDynamicParamFromSegment` · `addSearchParamsIfPageSegment` 가 세그먼트 키를 만드는 방식, `RouteTree` 타입(L95-107 — 이 파일 밖에서 import 하는 곳을 찾지 못했다), `renderToNodeFlightStream` / `renderToWebFlightStream` 과 디버그 채널, `layout-router.tsx` 의 나머지(스크롤·Activity·템플릿)는 이 문서의 범위 밖이다.
