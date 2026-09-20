# commitRoot

상위: [커밋 흐름](../README.md)

**before-mutation 패스를 끝내고 갈림길을 만든다.** 나머지 단계는 직접 부르지 않고 함수로 넘기거나 동기로 부른다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L3706-L3903 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L3706-L3903))

## 실제 코드

패시브 이펙트를 가장 먼저 예약한다.

```js
// ReactFiberWorkLoop.js L3787-L3801
      scheduleCallback(NormalSchedulerPriority, () => {
        if (enableProfilerTimer && enableComponentPerformanceTrack) {
          // Track the currently executing event if there is one so we can ignore this
          // event when logging events.
          trackSchedulerEvent();
        }
        if (pendingDelayedCommitReason === IMMEDIATE_COMMIT) {
          pendingDelayedCommitReason = DELAYED_PASSIVE_COMMIT;
        }
        flushPassiveEffects();
        // This render triggered passive effects: release the root cache pool
        // *after* passive effects fire to avoid freeing a cache pool that may
        // be referenced by a node in the tree (HostRoot, Cache boundary etc)
        return null;
      });
```

before-mutation 은 갈림길 앞에서 끝난다.

```js
// ReactFiberWorkLoop.js L3855-L3855
      commitBeforeMutationEffects(root, finishedWork, lanes);
```

그리고 갈림길.

```js
// ReactFiberWorkLoop.js L3876-L3902
  if (enableViewTransition && shouldStartViewTransition) {
    if (enableProfilerTimer && enableComponentPerformanceTrack) {
      startAnimating(lanes);
    }
    pendingViewTransition = startViewTransition(
      suspendedState,
      root.containerInfo,
      pendingTransitionTypes,
      flushMutationEffects,
      flushLayoutEffects,
      flushAfterMutationEffects,
      flushSpawnedWork,
      flushPassiveEffects,
      reportViewTransitionError,
      enableProfilerTimer ? suspendedViewTransition : (null as any),
      enableProfilerTimer
        ? // This callback fires after "pendingEffects" so we need to snapshot the arguments.
          finishedViewTransition.bind(null, lanes)
        : (null as any),
    );
  } else {
    // Flush synchronously.
    flushMutationEffects();
    flushLayoutEffects();
    // Skip flushAfterMutationEffects
    flushSpawnedWork();
  }
```

> Flush synchronously.

> Skip flushAfterMutationEffects

## 동작 흐름

```text
 WL L3706  function commitRoot(...)

 L3719  remainingLanes = mergeLanes(finishedWork.lanes, finishedWork.childLanes)
 L3721  pendingEffectsRemainingLanes = remainingLanes
 L3725  렌더 중 들어온 갱신 lane 을 합친다
 L3728  제스처가 없으면 GestureLane 을 뺀다
 L3740  markRootFinished(...)
 L3750  didIncludeCommitPhaseUpdate = false

 L3757  ★ 패시브 이펙트 태스크를 예약한다
 L3787    scheduleCallback(NormalSchedulerPriority, () => {
 L3796      flushPassiveEffects();
 L3801    });
 L3806  해당 없으면 root.callbackNode / callbackPriority 를 지운다

 L3810  [FLAG:enableProfilerTimer] 커밋 시각 기록
 L3827  resetShouldStartViewTransition()

 L3838  subtreeFlags 에 BeforeMutationMask | MutationMask 가 있으면
 L3851    try {
 L3855      commitBeforeMutationEffects(root, finishedWork, lanes)
 L3856    } finally { ... }

 L3864  제스처 렌더였으면 stopCommittedGesture(root)
 L3875  pendingEffectsStatus = PENDING_MUTATION_PHASE

 L3876  if (enableViewTransition && shouldStartViewTransition) {
 L3877    [FLAG:enableProfilerTimer && enableComponentPerformanceTrack]
 L3878      startAnimating(lanes)
 L3880    pendingViewTransition = startViewTransition(
             suspendedState, root.containerInfo, pendingTransitionTypes,
             flushMutationEffects,        <- 콜백
             flushLayoutEffects,          <- 콜백
             flushAfterMutationEffects,   <- 콜백
             flushSpawnedWork,            <- 콜백
             flushPassiveEffects,         <- 콜백
             reportViewTransitionError, ... )
 L3896  } else {
 L3897    // Flush synchronously.
 L3898    flushMutationEffects();
 L3899    flushLayoutEffects();
 L3900    // Skip flushAfterMutationEffects
 L3901    flushSpawnedWork();
 L3902  }
```

```text
 넘기는 콜백이 다섯이다

 동기 경로는 셋을 부르는데 (mutation / layout / spawned)
 콜백 경로는 다섯을 넘긴다 - 거기에 after-mutation 과 passive 가 더 있다

 동기 경로가 after-mutation 을 건너뛰는 것은 주석이 밝힌다 (L3900)
 그리고 commitAfterMutationEffects 자체도
 enableViewTransition 이 꺼져 있으면 곧장 return 한다 (CW L2804-2807)
 => 이중 방어다

 패시브는 양쪽 다 별도 태스크(L3787)로 이미 예약돼 있다.
 콜백으로 넘기는 것은 브라우저가 시점을 정하게 하기 위함이다
```

```text
 before-mutation 이 갈림길을 결정한다

 shouldStartViewTransition 은 WorkLoop 의 변수가 아니다
 ReactFiberCommitViewTransitions 의 모듈 변수를 import 한 것이다

 L3827  resetShouldStartViewTransition()      먼저 false 로 만들고
 L3855  commitBeforeMutationEffects(...)      이 패스가 true 로 세울 수 있고
 L3876  if (... && shouldStartViewTransition) 그 결과를 읽는다

 => 갈림길은 "방금 훑은 트리에 뷰 트랜지션 대상이 있었는가" 다
    (세우는 자리는 세 곳이고 전부 before-mutation 패스 안이다.
     이것은 검증 과정에서 확인된 것이고 나는 리셋과 읽기만 직접 봤다)
```

```text
 패시브를 가장 먼저 예약하는 이유

 주석이 적는다 (L3752-3754)
   커밋 단계에서 할 수 있는 한 일찍 예약한다

 그런데 예약만으로는 아무 일도 일어나지 않는다.
 flushPassiveEffects 의 가드(WL L4673)가
 pendingEffectsStatus === PENDING_PASSIVE_PHASE 를 요구하는데
 그 값은 [03] flushSpawnedWork 가 L4190 에서 세운다

 => 예약과 실행 허가가 나뉘어 있다
    콜백이 먼저 돌아도 조용히 돌아간다
```

```text
 before-mutation 패스에도 게이트가 있다

 L3838  finishedWork.subtreeFlags 나 flags 에
        BeforeMutationMask | MutationMask 가 있을 때만 돈다

 그 안에서 다시 CW L440 의 subtreeMask 검사가 하강을 막는다

 => 패스를 통째로 건너뛰는 판단은 여기(L3838)이고,
    루프 안에서 가지를 치는 것은 CW L440 이다
```

## 결과가 쓰이는 곳

```text
 pendingEffectsStatus = PENDING_MUTATION_PHASE
      --> [02] flushMutationEffects 의 가드를 연다

 pendingEffects* 전역들
      --> completeRoot 가 세운 것을 각 단계가 읽는다

 예약된 스케줄러 태스크
      --> [패시브 이펙트] 흐름으로 간다
      --> 다만 [03]이 허가할 때까지 아무 일도 안 한다

 shouldStartViewTransition
      --> 갈림길을 정한다
```

## 다루지 않는 것

`completeRoot`(WL L3492)가 `pendingEffects*` 를 세우는 과정, `commitBeforeMutationEffects`(CW L343)와 `getSnapshotBeforeUpdate` 호출, `markRootFinished` 의 lane 정리, 제스처 렌더 분기(WL L3728-3738, L3864-3873), `startViewTransition` 의 브라우저 쪽 구현, `reportViewTransitionError`(WL L3905), 프로파일러 계측은 같은 뼈대의 곁가지라 요약만 했다. 상태 기계와 전역 목록은 [spi](../spi/README.md)에 있다.
