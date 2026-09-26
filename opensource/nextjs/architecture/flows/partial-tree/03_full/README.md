# 03 전체 트리가 필요할 때

상위: [내비게이션 요청이 트리를 중간부터 그리기까지](../README.md)

중간부터 그리기는 빠르지만 **공유 레이아웃을 건너뛴다.** 개발 중에 "이 내비게이션이 즉시 되는가" 를 검증하려면 건너뛴 레이아웃까지 봐야 한다. 그래서 그때만 루트부터 전부 그리는 판본이 따로 있다.

## 위치

`packages/next` / `src/server/app-render` / `walk-tree-with-flight-router-state.tsx` L348-L423 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/walk-tree-with-flight-router-state.tsx#L348-L423))

## 실제 코드

부르는 쪽의 조건이 이 판본을 **개발 전용**으로 만든다.

```tsx
// app-render.tsx L694-L704
    // If we're performing instant validation, we need to render the whole tree,
    // without skipping shared layouts.
    const needsFullTree =
      process.env.__NEXT_DEV_SERVER &&
      ctx.renderOpts.cacheComponents &&
      !(
        requestStore?.type === 'request' &&
        isBypassingCachesInDev(requestStore, workStore)
      ) &&
      !options?.actionResult && // Only for navigations
      (await anySegmentNeedsInstantValidationInDev(loaderTree))
```

```text
 ★★★ 다섯 조건이 모두 참이어야 전체 트리로 간다

   process.env.__NEXT_DEV_SERVER                 개발 서버
   ctx.renderOpts.cacheComponents                cacheComponents 켜짐
   !(request 스토어 && isBypassingCachesInDev)   개발의 캐시 우회 요청이 아님
   !options?.actionResult                        서버 액션 결과가 아님 — 주석 "Only for navigations"
   await anySegmentNeedsInstantValidationInDev(loaderTree)   instant 검증이 필요한 세그먼트가 있음

 주석 L694-695 - "If we're performing instant validation, we need to render the whole tree,
   without skipping shared layouts."

 => **프로덕션에서는 언제나** walkTreeWithFlightRouterState 다 (첫 조건)
 => 개발이어도 cacheComponents 가 꺼져 있으면 여전히 중간부터다
 ★ 검증 기계 자체는 [instant 검증] 흐름이 다룬다
```

## 동작 흐름

```text
 createFullTreeFlightDataForNavigation   WALKTREE L353

 docstring L348-352
   "A simplified version of `walkTreeWithFlightRouterState` that doesn't skip any layouts
    but returns a result of the same shape.
    Intended to be used for instant validation, where we need the complete tree."

 L384  routerState = createFlightRouterStateFromLoaderTree(루트 로더 트리, ...)
 L395  rootSegment = routerState[0]
 L397  seedData = await createComponentTree({ loaderTree,        ← **루트** 로더 트리
                                              parentParams: {}, rootLayoutIncluded: false, ... })
 L412  return [[rootSegment, routerState, seedData, rscHead, ...]]   ← 경로 **하나**
         주석 L414-415 - "TODO: app-render slices this Segment off. why is that valid,
           and why are we including it in the first place?"

 => 받는 쪽이 같은 모양을 기대하므로 결과는 경로 배열이지만 항목은 **루트 하나**다
 => 그래서 [트리 조립]의 전체 조립과 사실상 같은 일을 하고, 모양만 내비게이션 응답에 맞춘다
 ★ 이 판본은 클라이언트가 보낸 FlightRouterState 를 **쓰지 않는다** — 파라미터 타입(L364)에는
   있지만 구조 분해(L353-361)에 없고, 부르는 쪽(APPR L736-745)도 넘기지 않는다
```

```text
 ★★ 두 판본의 차이가 곧 이 흐름의 요점이다

                      walkTreeWithFlightRouterState      createFullTreeFlightDataForNavigation
 시작점               클라이언트와 처음 어긋나는 자리    **루트**
 공유 레이아웃        건너뛴다                          다시 그린다
 그 레이아웃의 설정   **읽히지 않는다**                 읽힌다 ([트리 조립] [01])
 응답 경로 수         바뀐 슬롯마다 하나                루트 하나
 도는 곳              프로덕션 · 개발 대부분             개발 + cacheComponents + instant 검증

 ★★★ 검증이 전체 트리를 요구하는 이유가 여기 있다 — 건너뛴 레이아웃 안에서
   동적 접근이 일어나도 중간부터 그리면 **보이지 않는다**
   ※ 이 인과는 주석 L694-695("without skipping shared layouts")와 위 표에서 내가 끌어낸 것이다
```

## 결과가 쓰이는 곳

```text
 루트부터의 seedData 하나
      --> 내비게이션 응답으로 나간다 — 클라이언트는 평소처럼 경로에 끼운다
      --> 그리고 개발 서버의 instant 검증이 이 렌더를 관찰한다 ([instant 검증])
```

## 다루지 않는 것

`anySegmentNeedsInstantValidationInDev` 의 판정과 `export const instant` 설정, `isBypassingCachesInDev` 의 조건, 개발 서버가 이 렌더를 검증에 쓰는 방식 전체([instant 검증] 흐름), `rscHead` 를 만드는 [메타데이터] 쪽 `Viewport` · `Metadata` 조립(APPR L706-732)은 이 문서의 범위 밖이다.
