# performWorkOnRootViaSchedulerTask

상위: [스케줄링](../README.md)

**스케줄러가 부르는 진입점이다.** 렌더를 돌리고, 끝나면 [scheduleTaskForRootDuringMicrotask](../02_scheduleTaskForRootDuringMicrotask/README.md)를 다시 불러 다음 태스크를 정한다. 그리고 자기 자신을 돌려주면 스케줄러가 이어서 돌린다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L513-L606 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L513-L606))

## 실제 코드

진입 선언이 주석에 있다.

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L517-L518 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L517-L518))

> This is the entry point for concurrent tasks scheduled via Scheduler (and postTask, in the future).

비동기 커밋 중이면 미룬다.

```js
// ReactFiberRootScheduler.js L530-L541
  if (hasPendingCommitEffects()) {
    // We are currently in the middle of an async committing (such as a View Transition).
    // We could force these to flush eagerly but it's better to defer any work until
    // it finishes. This may not be the same root as we're waiting on.
    // TODO: This relies on the commit eventually calling ensureRootIsScheduled which
    // always calls processRootScheduleInMicrotask which in turn always loops through
    // all the roots to figure out. This is all a bit inefficient and if optimized
    // it'll need to consider rescheduling a task for any skipped roots.
    root.callbackNode = null;
    root.callbackPriority = NoLane;
    return null;
  }
```

렌더를 돌린다.

```js
// ReactFiberRootScheduler.js L585-L590
  // Enter the work loop.
  // TODO: We only check `didTimeout` defensively, to account for a Scheduler
  // bug we're still investigating. Once the bug in Scheduler is fixed,
  // we can remove this, since we track expiration ourselves.
  const forceSync = !disableSchedulerTimeoutInWorkLoop && didTimeout;
  performWorkOnRoot(root, lanes, forceSync);
```

그리고 다음을 정한다.

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L592-L605 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L592-L605))

```js
// ReactFiberRootScheduler.js L599-L605
  scheduleTaskForRootDuringMicrotask(root, now());
  if (root.callbackNode != null && root.callbackNode === originalCallbackNode) {
    // The task node scheduled for this root is the same one that's
    // currently executed. Need to return a continuation.
    return performWorkOnRootViaSchedulerTask.bind(null, root);
  }
  return null;
```

> Usually `scheduleTaskForRootDuringMicrotask` only runs inside a microtask; however, since most of the logic for determining if we need a continuation versus a new task is the same, we cheat a bit and call it here. This is only safe to do because we know we're at the end of the browser task. So although it's not an actual microtask, it might as well be.

## 동작 흐름

```text
 ~~> 스케줄러가 매크로태스크로 부른다. didTimeout 을 인자로 준다

 L520  [enableProfilerTimer && enableProfilerNestedUpdatePhase] resetNestedUpdateFlag()
 L524  [enableProfilerTimer && enableComponentPerformanceTrack] trackSchedulerEvent()

 L530  hasPendingCommitEffects() 면
 L538    callbackNode = null / callbackPriority = NoLane
 L540    => return null

 L545  originalCallbackNode = root.callbackNode
 L546  didFlushPassiveEffects = flushPendingEffectsDelayed()
 L547  돌았으면
 L550    callbackNode 가 바뀌었으면 => return null   (취소된 것)
 L555    아니면 계속

 L575  lanes = getNextLanes(...)
 L580  NoLanes 면 => return null

 L589  forceSync = !disableSchedulerTimeoutInWorkLoop && didTimeout
 L590  performWorkOnRoot(root, lanes, forceSync)     <- 흐름 3

 L599  scheduleTaskForRootDuringMicrotask(root, now())
 L600  callbackNode 가 그대로면
 L603    => return performWorkOnRootViaSchedulerTask.bind(null, root)
 L605  아니면 => return null
```

```text
 continuation 이 어떻게 성립하나

 스케줄러는 콜백을 부르기 전에 태스크의 callback 을 비우고
 반환값이 있으면 **같은 태스크 객체에 다시 꽂는다**
 null 이면 큐에서 뺀다

 그래서 태스크 객체가 유지되고 root.callbackNode 도 안 바뀐다
 L600 의 비교가 그것을 본다

   root.callbackNode != null && root.callbackNode === originalCallbackNode

 즉 "L599 가 새 태스크를 걸지 않았다" = "같은 태스크로 계속하면 된다"
 (스케줄러 쪽 동작은 검증 과정에서 확인한 것이고, 내가 직접 읽지는 않았다)
```

```text
 flush 함수가 동기 경로와 다르다

 여기          L546  flushPendingEffectsDelayed()
 동기 경로      L611  flushPendingEffects()

 앞엣것은 pendingDelayedCommitReason 이 IMMEDIATE_COMMIT 일 때만
 DELAYED_PASSIVE_COMMIT 으로 바꾼 뒤 뒤엣것을 부른다
 (WorkLoop L4636-4641)

 즉 조건부로 한 겹 더 씌운다
```

```text
 flush 뒤에 취소를 확인한다

 L546  패시브 이펙트를 먼저 돌린다
 L547  돌았으면 root.callbackNode 가 바뀌었는지 본다

 패시브 이펙트 안에서 새 갱신이 생기면
 그것이 ensureRootIsScheduled 를 거쳐 이 태스크를 취소하고
 새 태스크를 걸 수 있기 때문이다

 주석이 그 사정을 적는다 (L548-549)
   "Something in the passive effect phase may have canceled the current task.
    Check if the task node for this root was changed."
```

```text
 L530 갈래가 TODO 를 달고 있다

 주석 L531-537 이 현재 구조의 비효율을 인정한다
   비동기 커밋(View Transition) 중이면 이 루트의 태스크를 버리고
   커밋이 끝나면서 ensureRootIsScheduled 가 불리기를 기대한다

   "TODO: This relies on the commit eventually calling ensureRootIsScheduled
    which always calls processRootScheduleInMicrotask which in turn always
    loops through all the roots to figure out. This is all a bit inefficient
    and if optimized it'll need to consider rescheduling a task for any
    skipped roots."

 즉 "다른 루트도 같이 건너뛴다" 는 것을 알고 둔 것이다
```

```text
 didTimeout 을 방어적으로만 쓴다

 L589  forceSync = !disableSchedulerTimeoutInWorkLoop && didTimeout

 주석이 이유를 적는다 (L586-588)
   "TODO: We only check `didTimeout` defensively, to account for a Scheduler
    bug we're still investigating. Once the bug in Scheduler is fixed,
    we can remove this, since we track expiration ourselves."

 만료는 React 가 직접 추적하므로 원래는 필요 없다는 뜻이다
```

## 결과가 쓰이는 곳

```text
 performWorkOnRoot 호출
      --> 렌더 루프가 시작된다
      --> forceSync 가 false 면 중간에 양보할 수 있다

 반환한 continuation
      --> 스케줄러가 같은 태스크로 이어 돌린다
      --> null 이면 태스크가 큐에서 빠진다

 L599 가 갱신한 root.callbackNode
      --> 우선순위가 바뀌었으면 새 태스크가 들어가 있다
      --> 그러면 이 함수는 null 을 돌려주고 끝난다
```

## 다루지 않는 것

`Scheduler` 패키지의 태스크 큐·타임 슬라이싱·continuation 처리, `performWorkOnRoot` 이후의 렌더 루프, `flushPendingEffectsDelayed` 와 `flushPendingEffects` 의 패시브 이펙트 처리, `hasPendingCommitEffects` 가 보는 커밋 상태, `trackSchedulerEvent` 와 `resetNestedUpdateFlag` 의 계측은 같은 뼈대의 곁가지라 요약만 했다.
