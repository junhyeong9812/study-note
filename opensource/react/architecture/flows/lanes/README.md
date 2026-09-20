# lane 우선순위

상위: [React 아키텍처 지도](../../README.md)

React 가 "무엇을 먼저 할지" 정하는 방식이다. 앞의 모든 흐름이 이 비트들을 쓴다 — [스케줄링](../scheduling/README.md)이 태스크를 걸 때, [렌더 루프](../render-loop/README.md)가 양보할지 정할 때, [beginWork](../begin-work/README.md)가 바이아웃할지 볼 때.

이 흐름의 핵심은 셋이다. **낮은 비트가 높은 우선순위라 비교가 한 줄로 끝나고**, **다음에 할 일을 고르는 규칙이 2×3 이며**, **만료 시각이 기아를 막는 안전장치**다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberLane.js` 기준이다.

## 전체 그림

```text
 [01] 비트 배치                              L41-123
      bit 0 SyncHydrationLane  ...  bit 30 DeferredLane
      31개를 연속으로 쓴다

 [02] getNextLanes                           L249-361
      +-- idle 이 아닌 일을 먼저 고른다
      |     (1) 서스펜드 안 된 새 일
      |     (2) ping 된 일
      |     (3) 예열할 일
      +-- 그것이 없을 때만 idle 을 같은 순서로 본다
      +-- 이미 렌더 중이면 끼어들지 판정한다        L337-358

 [03] 만료                                    L477-588
      computeExpirationTime 이 등급별 시각을 정하고
      markStarvedLanesAsExpired 가 2패스로 expiredLanes 를 세운다
```

1. [비트 배치](01_laneLayout/README.md)가 우선순위 순서를 만든다.
2. [getNextLanes](02_getNextLanes/README.md)가 다음에 할 일을 고른다.
3. [만료](03_expiration/README.md)가 기아를 막는다.

```text
 ★ 낮은 비트가 높은 우선순위다

 주석이 그것을 명시한다 (L347-348)
   "Tests whether the next lane is equal or lower priority than the wip
    one. This works because the bits decrease in priority as you go left."

 그래서 "가장 급한 lane 고르기" 가 한 줄이다
   L757  return lanes & -lanes;

 2의 보수 트릭으로 가장 낮은 켜진 비트만 남긴다.
 lanes 가 0 이면 0 이 나오는데, 부르는 쪽이 전부
 !== NoLanes 로 감싸고 있다
```

```text
 ★ 이름이 닮은 두 함수가 서로 다르다

 getHighestPriorityLane (L756, 단수)
   lanes & -lanes 한 줄. **비트 하나**를 준다

 getHighestPriorityLanes (L180, 복수)
   같은 등급을 **배치로 묶어** 준다
   L181-183  SyncUpdateLanes 비트가 있으면
             그 부분집합을 통째로 돌려주고 switch 를 건너뛴다
   L215      트랜지션이면 lanes & TransitionUpdateLanes
   L225      retry 면 lanes & RetryLanes

 [02]는 복수형으로 묶음을 고른 뒤
 단수형으로 대표 비트를 뽑아 비교한다 (L344-345)

 (복수형이 언제나 최고 우선순위 비트를 포함하지는 않는다 -
  SyncHydrationLane 은 SyncUpdateLanes 에 없어서
  SyncHydrationLane | DefaultLane 이 들어오면 DefaultLane 만 나온다.
  이것은 검증 과정에서 지적된 것이고, 나는 L181-183 의 구조만 확인했다)
```

```text
 앞 흐름들이 쓰는 술어

 includesSyncLane              [스케줄링]이 동기로 돌릴지 정할 때
 includesBlockingLane          [렌더 루프] L1156 shouldTimeSlice
 includesExpiredLane           〃 (만료됐으면 양보를 끈다)
 includesOnlySuspenseyCommitEligibleLanes
                               [completeWork] L591 리소스 프리로드 판정
 includesOnlyViewTransitionEligibleLanes
                               [커밋]의 뷰 트랜지션 판정
 isGestureRender               [커밋]의 제스처 경로

 => lane 은 이 흐름 안에만 있는 것이 아니라
    다른 흐름들이 묻는 질문의 답이다
```

## 어디로 이어지는가

```text
 [스케줄링]    getNextLanes 로 다음 태스크의 lane 을 정한다
               markStarvedLanesAsExpired 를 매 마이크로태스크마다 부른다

 [렌더 루프]   shouldTimeSlice 가 includesBlockingLane / includesExpiredLane 를 본다

 [beginWork]   바이아웃 판정이 renderLanes 와 childLanes 를 비교한다

 [훅]          setState 가 requestUpdateLane 으로 lane 을 정한다
               트랜지션 갱신은 서로 얽힌다(entangle)
```

## 결과가 쓰이는 곳

```text
 root.pendingLanes
      --> 아직 안 한 일 전부

 root.suspendedLanes / pingedLanes / warmLanes
      --> [02]의 (1)(2)(3) 이 이 셋을 본다

 root.expiredLanes
      --> [03]이 세운다. shouldTimeSlice 가 읽어 양보를 끈다

 root.entanglements
      --> 같이 렌더돼야 하는 lane 묶음
      --> 트랜지션 갱신이 흩어지지 않게 한다

 entangledRenderLanes
      --> beginWork / completeWork 가 받는 것은 이쪽이다
```

## 다루지 않는 것

`markRootUpdated`(L825) / `markRootSuspended`(L851) / `markRootPinged`(L887) / `markRootFinished`(L894)의 상태 전이 세부, `getNextLanesToFlushSync`(L363), `getEntangledLanes`(L427)와 `markRootEntangled`(L1028)의 얽힘 전개, `claimNext*Lane`(L726/738/747)의 순환 커서, 수화 lane 승급(`getBumpedLaneForHydration` L1092), transition tracing(L1210 이하), DevTools 용 `getLabelForLane`(L127)과 updater 추적은 같은 뼈대의 곁가지라 요약만 했다. 술어 목록과 루트 필드는 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 비트 배치](01_laneLayout/README.md)
- [02 getNextLanes](02_getNextLanes/README.md)
- [03 만료](03_expiration/README.md)
- [spi](spi/README.md) — 술어, 루트 필드, 얽힘
