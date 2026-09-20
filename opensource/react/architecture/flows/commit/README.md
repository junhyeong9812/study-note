# 커밋

[렌더 루프](../render-loop/README.md)가 만든 작업 중 트리를 **실제 DOM 에 반영한다.** [completeWork](../complete-work/README.md)가 세운 flags 를 읽어 무엇을 할지 정한다.

이 흐름의 핵심은 셋이다. **단계가 함수로 쪼개져 상태 기계로 이어지고**, **트리를 바꿔 다는 한 줄이 언마운트와 마운트 사이에 있으며**, **props diff 가 렌더가 아니라 여기서 일어난다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 파일을 밝힌다. `WL` = `ReactFiberWorkLoop.js`, `CW` = `ReactFiberCommitWork.js`.

## 전체 그림

```text
 completeRoot (WL L3492)
      +-- pendingEffects* 전역을 세운다            WL L3620-3631
      +-- commitRoot(...)                          WL L3693

 [01] commitRoot                                   WL L3706-3903
      +-- 패시브 이펙트 태스크를 **먼저** 예약      WL L3787
      +-- resetShouldStartViewTransition()          WL L3827
      +-- before-mutation 패스를 여기서 동기로 끝낸다  WL L3855
      +-- pendingEffectsStatus = PENDING_MUTATION_PHASE  WL L3875
      +-- 갈림길                                    WL L3876
      |     뷰 트랜지션이면 flush 다섯을 콜백으로 넘긴다  L3880-3895
      |     아니면 셋을 동기로 부른다                 L3898-3901

 [02] flushMutationEffects                         WL L3990-4034
      +-- commitMutationEffects                    WL L4012
      +-- root.current = finishedWork              WL L4032   ** 트리 교체 **

 [03] flushLayoutEffects                           WL L4036-4133
      +-- commitLayoutEffects                      WL L4106

 [04] flushSpawnedWork                             WL L4135-4418
      +-- requestPaint()                           WL L4170
      +-- 패시브 단계를 **열어 준다**                WL L4190
```

1. [commitRoot](01_commitRoot/README.md)가 준비하고 갈림길을 만든다.
2. [세 패스](02_threePasses/README.md)가 flags 를 읽어 DOM 을 바꾼다.
3. [flushSpawnedWork](03_flushSpawnedWork/README.md)가 뒷정리하고 다음을 연다.

```text
 ★ 단계가 함수로 쪼개져 있고 상태 기계가 순서를 잡는다

 pendingEffectsStatus (WL L730) 가 값 여덟을 오간다
   0 NO_PENDING_EFFECTS            5 PENDING_PASSIVE_PHASE
   1 PENDING_MUTATION_PHASE        6 PENDING_GESTURE_MUTATION_PHASE
   2 PENDING_LAYOUT_PHASE          7 PENDING_GESTURE_ANIMATION_PHASE
   3 PENDING_AFTER_MUTATION_PHASE
   4 PENDING_SPAWNED_WORK

 각 flush 가 기대값이 아니면 그냥 return 한다
 그래서 콜백이 두 번 불리거나 건너뛰어도 안전하다

 쪼갠 이유가 둘이다
   (가) 뷰 트랜지션이면 브라우저가 부르는 콜백이 되어야 한다
   (나) flushPendingEffects(WL L4643)가 밖에서 강제로 진행시킬 때
        여섯을 순서대로 다 불러 놓고 가드가 걸러내게 한다

 자세한 예외는 [spi](spi/README.md)에 있다
```

```text
 before-mutation 은 갈림길 밖이다

 WL L3855  commitBeforeMutationEffects(root, finishedWork, lanes)
 WL L3876  if (enableViewTransition && shouldStartViewTransition)

 순서가 이렇다. before-mutation 은 갈림길 **앞**에서
 commitRoot 안에서 동기로 끝난다

 그리고 그 패스가 shouldStartViewTransition 을 세운다
 (CVT L52 의 모듈 변수. WL L3827 이 먼저 리셋한다)
 => 갈림길은 "방금 끝난 before-mutation 이 대상을 찾았는가" 를 읽는 것이다
```

```text
 ★ 트리를 바꿔 다는 한 줄

 WL L4032  root.current = finishedWork;

 주석이 위치의 이유를 말한다 (WL L4028-4031)
   "The work-in-progress tree is now the current tree. This must come after
    the mutation phase, so that the previous tree is still current during
    componentWillUnmount, but before the layout phase, so that the finished
    work is current during componentDidMount/Update."

 실제로 그렇다
   componentWillUnmount  mutation 패스 안 (WL L4012 -> ... -> CW L1705)
   componentDidMount     layout 패스 안 (WL L4106 -> ... -> CE L404)
   그리고 layout 은 PENDING_LAYOUT_PHASE 여야 도는데
   그 값을 세우는 유일한 자리가 WL L4033 - 바로 다음 줄이다

 ★ 그리고 이 줄은 mutation 효과를 검사하는 if 블록 **밖**이다
   WL L4003  if (subtreeMutationHasEffects || rootMutationHasEffect) {
   WL L4026  }
   WL L4032  root.current = finishedWork;
   => 바꿀 것이 하나도 없어도 트리 교체는 반드시 일어난다
```

```text
 ★ props diff 는 여기서 일어난다

 [completeWork]는 참조 비교 하나로 flags |= Update 만 세웠다
 무엇이 달라졌는지는 이 단계가 계산한다

 CW L2244   if (flags & Update) {
 CW L2254     commitHostUpdate(finishedWork, newProps, oldProps)
 CommitHostEffects L133   commitUpdate(stateNode, type, oldProps, newProps, ...)
 ReactFiberConfigDOM L999   // Diff and update the properties.
 ReactFiberConfigDOM L1000  updateProperties(domElement, type, oldProps, newProps)
```

```text
 패시브는 예약과 허가가 나뉘어 있다

 예약  commitRoot WL L3787
       scheduleCallback(NormalSchedulerPriority, () => { ... flushPassiveEffects() })
       주석이 "가능한 한 일찍" 예약한다고 밝힌다 (WL L3752-3754)

 허가  flushSpawnedWork WL L4189-4190
       rootDidHavePassiveEffects 이면
         pendingEffectsStatus = PENDING_PASSIVE_PHASE

 => 예약된 콜백이 먼저 돌아도 flushPassiveEffects 의 가드(WL L4673)에 걸려
    아무 일도 하지 않는다. 허가가 떨어진 뒤에만 실제로 돈다
```

## 어디로 이어지는가

```text
 [렌더 루프]     completeRoot 가 commitRoot 를 부른다
                 그리고 flushSpawnedWork 가 ensureRootIsScheduled 로 되돌아간다

 [completeWork]  여기서 읽는 flags 를 저쪽이 세웠다

 [패시브 이펙트]  commitRoot 가 예약하고 flushSpawnedWork 가 연다
```

## 결과가 쓰이는 곳

```text
 DOM
      --> mutation 패스가 바꾼다

 root.current
      --> 다음 렌더의 current 트리가 된다
      --> 언마운트와 마운트가 보는 트리를 가른다

 pendingEffectsStatus
      --> 다음 flush 가 진행할지 정한다

 pendingEffects* 전역들
      --> 단계 사이에 정보를 넘긴다 ([spi](spi/README.md)에 목록이 있다)
```

## 다루지 않는 것

`commitMutationEffectsOnFiber`(CW L2042)의 tag 별 갈래 전부, `commitLayoutEffectOnFiber`(CW L591)의 본문, `commitDeletionEffectsOnFiber`(CW L1473)의 tag 별 언마운트, Offscreen 숨김·드러냄(`disappearLayoutEffects` CW L3010 / `reappearLayoutEffects`), ref 를 붙이고 떼는 세부, `commitAfterMutationEffects`(CW L2799)의 뷰 트랜지션 재측정, `startViewTransition` 과 `startGestureTransition` 의 브라우저 쪽 구현, 무한 업데이트 루프 감지(WL L4323-4366), transition tracing 은 같은 뼈대의 곁가지라 요약만 했다. 상태 기계의 예외와 에러 처리는 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 commitRoot](01_commitRoot/README.md)
- [02 세 패스](02_threePasses/README.md)
- [03 flushSpawnedWork](03_flushSpawnedWork/README.md)
- [spi](spi/README.md) — 상태 기계, 전역, 에러 처리, 제스처 경로
