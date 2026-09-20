# spi

상위: [커밋 흐름](../README.md)

이 흐름의 계약은 **`pendingEffectsStatus`** 다. 값 여덟짜리 상태 기계가 단계 순서를 잡고, 나머지 `pending*` 전역들이 단계 사이로 정보를 나른다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). `WL` = `ReactFiberWorkLoop.js`, `CW` = `ReactFiberCommitWork.js`, `FF` = `packages/shared/ReactFeatureFlags.js`.

## 상태 기계

```js
// ReactFiberWorkLoop.js L722-L730
const NO_PENDING_EFFECTS = 0;
const PENDING_MUTATION_PHASE = 1;
const PENDING_LAYOUT_PHASE = 2;
const PENDING_AFTER_MUTATION_PHASE = 3;
const PENDING_SPAWNED_WORK = 4;
const PENDING_PASSIVE_PHASE = 5;
const PENDING_GESTURE_MUTATION_PHASE = 6;
const PENDING_GESTURE_ANIMATION_PHASE = 7;
let pendingEffectsStatus: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 = 0;
```

| 함수 | 정의 | 가드 | 0 으로 | 다음 |
|---|---|---|---|---|
| `flushAfterMutationEffects` | WL L3978 | L3979 (AFTER_MUTATION) | L3982 즉시 | L3987 SPAWNED_WORK |
| `flushMutationEffects` | WL L3990 | L3991 (MUTATION) | L3994 즉시 | L4033 LAYOUT |
| `flushLayoutEffects` | WL L4036 | L4037 (LAYOUT) | L4040 즉시 | L4132 AFTER_MUTATION |
| `flushSpawnedWork` | WL L4135 | L4136 **기대값 둘** | L4163 **즉시 아님** | L4190 PASSIVE 또는 L4192 0 |
| `flushPassiveEffects` | WL L4672 | L4673 (PASSIVE, `return false`) | **L4716 — 다른 함수 안** | **없음 — 종착역** |

```text
 네 단계 패턴을 그대로 지키는 것은 셋뿐이다

 지키는 것   flushAfterMutation / flushMutation / flushLayout
             (+ 제스처의 flushGestureMutations)

 어긋나는 것
   flushSpawnedWork
     가드가 기대값을 둘 받는다 (SPAWNED_WORK 또는 AFTER_MUTATION)
       주석 WL L4138-4139 - 뷰 트랜지션이 타임아웃하면
       after-mutation 을 건너뛰고 여기로 온다
     0 으로 지우기 전에 프로파일러 블록이 먼저 돈다 (L4144-4161)
       그 블록이 지우기 전의 값을 읽어 분기하기 때문이다 (L4146)

   flushPassiveEffects
     가드 return 이 값을 돌려준다 (return false)
     0 으로 지우는 것은 flushPassiveEffectsImpl (L4709) 안의 L4716 이다
     다음 단계를 세우지 않는다 - 체인의 끝이다
```

```text
 "순서가 어긋나도 안전하다" 의 진짜 근거

 flushPendingEffects (WL L4643-4670) 가
 밖에서 강제로 진행시킬 때 여섯을 **무조건 전부** 부른다
   flushGestureMutations -> flushGestureAnimations
   -> flushMutationEffects -> flushLayoutEffects
   -> flushSpawnedWork -> flushPassiveEffects

 각 가드가 해당 없는 것을 걸러 내므로
 지금 어느 단계든 거기서부터 끝까지 진행된다

 주석이 after-mutation 을 뺀 이유를 적는다 (WL L4667 부근)
   "Skip flushAfterMutation if we're forcing this early."

 => 상태 기계는 "잘못된 호출을 막는 것" 이기도 하지만
    "어디서든 재개할 수 있게 하는 것" 이기도 하다
```

## pending* 전역

| 전역 | 선언 | 담는 것 |
|---|---|---|
| `pendingEffectsStatus` | WL L730 | 상태 기계 값 |
| `pendingEffectsRoot` | L731 | 커밋 중인 FiberRoot |
| `pendingFinishedWork` | L732 | 커밋할 작업 중 트리 |
| `pendingEffectsLanes` | L733 | 이번 커밋의 lane |
| `pendingEffectsRemainingLanes` | L734 | 커밋 후에도 남는 lane — 캐시 풀 해제 판단용 |
| `pendingEffectsRenderEndTime` | L735 | 프로파일링 전용 |
| `pendingPassiveTransitions` | L736 | 패시브 단계로 넘길 Transition |
| `pendingRecoverableErrors` | L737 | 렌더 중 복구된 에러들 |
| `pendingViewTransition` | L738 | 진행 중인 뷰 트랜지션 핸들 |
| `pendingViewTransitionEvents` | L739 | 발사 대기 중인 이벤트 콜백 |
| `pendingTransitionTypes` | L742 | 이번 트랜지션 타입 목록 |
| `pendingDidIncludeRenderPhaseUpdate` | L743 | 렌더 단계 갱신 포함 여부 |
| `pendingSuspendedCommitReason` | L744 | 프로파일링 전용 |
| `pendingDelayedCommitReason` | L745 | 프로파일링 전용 |
| `pendingSuspendedViewTransitionReason` | L746 | 프로파일링 전용 |

```text
 세우는 곳이 commitRoot 가 아니다

 대부분을 completeRoot (WL L3492) 가 L3620-3631 에서 세운다
 commitRoot 는 그것을 받아 쓴다

 pendingEffectsRemainingLanes 만 commitRoot L3721 이 세우고
 flushPassiveEffects L4686-4687 이 소비한 뒤
 L4705 releaseRootPooledCache 로 넘긴다
```

## 에러 처리

```text
 사용자 코드는 개별 try/catch 로 감싸 captureCommitPhaseError (WL L4894) 로 보낸다

 ★ 그런데 이 함수는 에러를 삼키지 않는다
   가장 가까운 에러 바운더리를 찾아 **SyncLane 업데이트를 큐잉한다**
   못 찾고 루트에 닿으면 루트에 큐잉한다
   어느 쪽도 안 되면 DEV 에서 console.error 만 하고 사라진다

   => 커밋 에러는 "잡혀서 다음 동기 렌더로 이연" 된다

 던져지는 자리는 React 내부 불변식 위반뿐이다
   CW L563   before-mutation 의 default case (Snapshot 이 붙으면 안 되는 tag)
   CW L1426  'Expected to find a host parent'
   CW L1940  getRetryCache 의 default case
   CW L2295  HostText 의 stateNode 가 null
   WL L3597  'Cannot commit the same tree as before'
   WL L4731  'Cannot flush passive effects while already rendering'

 ★ 감싸지 않는 사용자 코드가 둘 있다
   WL L4247-4268  onRecoverableError - try/finally 는 있는데 catch 가 없다
   WL L4286-4292  뷰 트랜지션 이벤트 콜백 - 아예 감싸지 않는다

   그리고 규칙이 다른 자리가 하나 더 있다
   WL L4076-4078  transition indicator 의 cleanup 은
                  captureCommitPhaseError 가 아니라 reportGlobalError 로 간다

 (이 목록은 검증 과정에서 나온 것이고,
  나는 captureCommitPhaseError 의 자리와 L4247-4268 의 구조만 직접 확인했다)
```

## 커밋 경로가 셋이다

```text
 (가) 동기          commitRoot L3898-3901
 (나) 뷰 트랜지션    commitRoot L3880-3895, 콜백 다섯을 넘긴다
 (다) 제스처        completeRoot L3633 에서 갈라진다

 ★ (다)는 commitRoot 를 아예 부르지 않는다
   completeRoot L3688 에서 return 해 버린다

   applyGestureOnRoot       WL L4420-4474
     예전 트리의 클론을 심고 (L4449)
     pendingEffectsStatus = PENDING_GESTURE_MUTATION_PHASE (L4457)
     startGestureTransition 에 콜백 **둘**을 넘긴다 (L4466-4467)
   flushGestureMutations    WL L4476-4512
   flushGestureAnimations   WL L4514-4601

   root.current 교체도, layout 패스도, 패시브 패스도 없다

 ★ flushGestureAnimations 만 가드보다 먼저 일을 한다
   L4520 에서 flushGestureMutations() 를 부른 뒤
   L4521 에서 자기 가드를 검사한다
   주석이 이유를 적는다 - 시작 전에 취소되면
   mutation 이 아직 안 붙어 있을 수 있다

 시작점은 React.unstable_startGestureTransition 이다
```

## 플래그

```text
 enableViewTransition        FF L81   **true**
 enableGestureTransition     FF L85   __EXPERIMENTAL__
                             => 죽은 경로가 아니다.
                                stable 에서는 꺼지고 experimental/canary 에서는 켜진다
 enableCreateEventHandleAPI  FF L56   false (www 포크만 true)
 enableYieldingBeforePassive FF L70   false
 enableProfilerTimer         FF L229  __PROFILE__ (빌드마다 다르다)
```

```text
 주석이 코드보다 넓게 말하는 자리

 CW L373-374
   "This phase is only used for beforeActiveInstanceBlur.
    Let's skip the whole loop if it's off."

 그런데 그 플래그 if (CW L375)가 감싸는 것은
 deletions 순회(CW L376-386) **하나뿐**이다

 자식 하강(CW L439-442), commitNestedViewTransitions(L449),
 _complete 호출(L451)은 전부 플래그 밖에 있어 언제나 돈다
 그리고 getSnapshotBeforeUpdate 도 그 "건너뛴다는" 루프 안에서 처리된다

 => 패스 전체가 생략되는 것은 두 층 위다 -
    commitRoot L3838 의 subtreeFlags 검사
    루프 안에서 가지를 치는 것은 CW L440 의 subtreeMask 검사다

 (주석이 옛 구현의 흔적으로 보이지만 그 판단은 내 추측이다.
  확인한 것은 플래그 if 의 범위다)
```

## 결과가 쓰이는 곳

```text
 pendingEffectsStatus
      --> 각 flush 가 진행할지 정한다
      --> flushPendingEffects 가 밖에서 강제 진행시킬 때도 이것이 기준이다

 pending* 전역들
      --> completeRoot 가 세우고 각 단계가 소비한다
      --> 패시브 단계가 마지막으로 정리한다

 captureCommitPhaseError 가 큐잉한 SyncLane 업데이트
      --> 다음 동기 렌더에서 에러 바운더리가 처리한다

 죽은 갈래
      --> enableCreateEventHandleAPI 가 꺼져 deletions 순회가 안 돈다
      --> enableGestureTransition 은 빌드에 따라 다르다. 죽은 것이 아니다
```

## 다루지 않는 것

`captureCommitPhaseError`(WL L4894)가 에러 바운더리를 찾는 규칙과 `createClassErrorUpdate`, `flushPendingEffects`(WL L4643)의 나머지, 제스처 경로의 `insertDestinationClones` 와 `startGestureTransition`, `ReactFiberGestureScheduler.js` 의 큐 관리, `releaseRootPooledCache` 와 캐시 수명, `commitAfterMutationEffects`(CW L2799)의 뷰 트랜지션 재측정, `ReactFiberFlags.js` 의 마스크 상수 구성은 이 문서의 범위 밖이다.
