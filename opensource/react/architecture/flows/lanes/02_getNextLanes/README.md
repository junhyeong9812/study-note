# getNextLanes

상위: [lane 흐름](../README.md)

**다음에 무엇을 할지 고른다.** 고르고 나서, 이미 렌더 중이면 끼어들지도 정한다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberLane.js` L249-L361 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberLane.js#L249-L361))

## 실제 코드

idle 은 뒤로 민다.

```js
// ReactFiberLane.js L279-L281
  // Do not work on any idle work until all the non-idle work has finished,
  // even if the work is suspended.
  const nonIdlePendingLanes = pendingLanes & NonIdleLanes;
```

> Do not work on any idle work until all the non-idle work has finished, **even if the work is suspended**.

그리고 끼어들기 판정.

```js
// ReactFiberLane.js L344-L357
    const nextLane = getHighestPriorityLane(nextLanes);
    const wipLane = getHighestPriorityLane(wipLanes);
    if (
      // Tests whether the next lane is equal or lower priority than the wip
      // one. This works because the bits decrease in priority as you go left.
      nextLane >= wipLane ||
      // Default priority updates should not interrupt transition updates. The
      // only difference between default updates and transition updates is that
      // default updates do not support refresh transitions.
      (nextLane === DefaultLane && (wipLane & TransitionLanes) !== NoLanes)
    ) {
      // Keep working on the existing in-progress tree. Do not interrupt.
      return wipLanes;
    }
```

> Tests whether the next lane is equal or lower priority than the wip one. This works because the bits decrease in priority as you go left.

> Default priority updates **should not** interrupt transition updates. The **only** difference between default updates and transition updates is that default updates do not support refresh transitions.

## 동작 흐름

```text
 L249  function getNextLanes(root, wipLanes, rootHasPendingCommit)

 L256  pendingLanes === NoLanes 이면
 L257    => return NoLanes

 L281  nonIdlePendingLanes = pendingLanes & NonIdleLanes
 L282  그것이 있으면 (idle 이 아닌 일이 남았다)
 L285    (1) nonIdlePendingLanes & ~suspendedLanes 가 있으면
 L286        nextLanes = getHighestPriorityLanes(그것)
 L290    (2) 아니면 nonIdlePendingLanes & pingedLanes 가 있으면
 L291        nextLanes = getHighestPriorityLanes(그것)
 L294    (3) 아니면 rootHasPendingCommit 이 아니고
 L296        nonIdlePendingLanes & ~warmLanes 가 있으면
 L297        nextLanes = getHighestPriorityLanes(그것)

 L302  아니면 (idle 만 남았다)
 L310    (1) pendingLanes & ~suspendedLanes 가 있으면  -> L311
 L314    (2) 아니면 pingedLanes 가 있으면              -> L315
 L318    (3) 아니면 rootHasPendingCommit 이 아니고
 L320        pendingLanes & ~warmLanes 가 있으면       -> L321

 L328  nextLanes 가 여전히 NoLanes 이면
 L331    => return NoLanes
          주석 L329 "This should only be reachable if we're suspended"

 --- 끼어들기 판정 ---
 L338  wipLanes !== NoLanes 이고
 L339  wipLanes !== nextLanes 이고
 L342  (wipLanes & suspendedLanes) === NoLanes 이면      (셋 다 AND)
 L344    nextLane = getHighestPriorityLane(nextLanes)
 L345    wipLane = getHighestPriorityLane(wipLanes)
 L349    nextLane >= wipLane 이거나
 L353    (nextLane === DefaultLane && (wipLane & TransitionLanes) !== NoLanes) 이면  (OR)
 L356      => return wipLanes          끼어들지 않는다

 L360  => return nextLanes
```

```text
 2 x 3 구조다

 바깥 둘   idle 이 아닌 일 먼저, 없을 때만 idle
 안쪽 셋   (1) 서스펜드 안 된 새 일
           (2) ping 된 일 (서스펜드했다가 promise 가 풀린 것)
           (3) 예열할 일 (아직 시도 안 해 본 것)

 (3)에는 전제가 하나 더 있다 - rootHasPendingCommit 이 아니어야 한다
 커밋할 트리가 이미 있으면 추측 렌더로 그것을 버릴 이유가 없다
```

```text
 ★ 안쪽 (2)가 두 갈래에서 다르다

 비idle  L289  nonIdlePendingLanes & pingedLanes     교집합을 취한다
 idle    L314  pingedLanes                           그대로 쓴다

 (1)과 (3)은 양쪽 다 pendingLanes 와 교집합을 취하는데
 (2)만 idle 쪽에서 마스킹이 빠져 있다

 markRootPinged 는 pingedLanes 가 suspendedLanes 의 부분집합임은
 보장하지만 pendingLanes 의 부분집합임은 보장하지 않는다
 => 구조적으로는 이미 pending 이 아닌 lane 이 나올 여지가 열려 있다

 의도인지 누락인지는 주석이 없어 알 수 없다.
 다만 바로 위 L303-306 에 Idle 자체를 지우자는 TODO 가 붙어 있다
 (이 비대칭은 검증 과정에서 지적된 것이고,
  나는 두 줄의 식 차이를 직접 확인했다)
```

```text
 ★ idle 은 서스펜드돼 있어도 뒤로 민다

 주석 L279-280 이 "even if the work is suspended" 라고 덧붙인다

 즉 "비idle 이 데이터를 기다리느라 못 나아가는 중" 이라도
 idle 을 먼저 하지 않는다.
 우선순위가 대기 상태보다 앞선다
```

```text
 Idle 에 TODO 가 붙어 있다

 L304-306
   "TODO: Idle isn't really used anywhere, and the thinking around
    speculative rendering has evolved since this was implemented.
    Consider removing until we've thought about this again."

 => 바깥 갈래의 절반이 사실상 쓰이지 않는다고 스스로 적는다
```

```text
 끼어들기 판정이 비트 크기 비교다

 L349  nextLane >= wipLane

 크거나 **같으면** 끼어들지 않는다.
 비트가 왼쪽으로 갈수록 우선순위가 낮으므로
 "숫자가 크다 = 덜 급하다" 다

 주석이 그 전제를 명시한다 (L347-348)

 그리고 예외가 하나 있다 (L353)
   Default 는 Transition 을 끊지 않는다
   주석이 이유를 적는다 - 둘의 유일한 차이는
   Default 가 refresh transition 을 지원하지 않는 것뿐이다
```

```text
 이미 지연 서스펜드한 렌더는 보호하지 않는다

 L342  (wipLanes & suspendedLanes) === NoLanes

 이 조건이 참일 때만 보호 블록에 들어간다.
 wip 가 서스펜드돼 있으면 판정 자체를 건너뛰고 L360 으로 간다

 주석 L340-341
   "If we already suspended with a delay, then interrupting is fine.
    Don't bother waiting until the root is complete."
```

```text
 고를 때와 비교할 때 쓰는 함수가 다르다

 고르기  getHighestPriorityLanes (복수, L180)  -> 등급 **배치**
 비교    getHighestPriorityLane  (단수, L756)  -> 비트 **하나**

 복수형은 같은 등급을 묶어 한 배치로 준다
   L181-183  SyncUpdateLanes 비트가 있으면 그 부분집합을 통째로
             (switch 를 건너뛴다)
   L215      트랜지션이면 lanes & TransitionUpdateLanes
   L225      retry 면 lanes & RetryLanes

 그래서 TransitionLane1 갱신이 TransitionLane5 렌더 중에 들어와도
 새 배치가 둘 다 포함한다
```

## 결과가 쓰이는 곳

```text
 반환한 lanes
      --> [스케줄링]이 그것으로 태스크 우선순위를 정한다
      --> [렌더 루프]가 renderLanes 로 받는다
      --> 다만 beginWork 가 받는 것은 entangledRenderLanes 다
          (getEntangledLanes 가 한 번 더 확장한다)

 return wipLanes (끼어들지 않음)
      --> 진행 중인 트리를 계속 그린다

 return NoLanes
      --> 할 일이 없거나 전부 막혀 있다
```

## 다루지 않는 것

`getHighestPriorityLanes`(L180)의 tag 별 case 전부와 `enableParallelTransitions` 분기, `getNextLanesToFlushSync`(L363), `checkIfRootIsPrerendering`(L412), `getEntangledLanes`(L427)의 얽힘 전개, `root.warmLanes` / `pingedLanes` 가 세워지는 자리(`markRoot*` 계열), `rootHasPendingCommit` 을 넘기는 쪽은 같은 뼈대의 곁가지라 요약만 했다. 루트 필드 표는 [spi](../spi/README.md)에 있다.
