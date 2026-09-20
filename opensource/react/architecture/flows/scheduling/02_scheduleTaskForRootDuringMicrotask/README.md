# scheduleTaskForRootDuringMicrotask

상위: [스케줄링](../README.md)

루트 하나의 운명을 정한다. **갈래가 셋이고 `return` 문이 넷이다.** 그리고 호출자는 돌려받은 값이 `NoLane` 인지만 본다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L384-L509 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L384-L509))

## 실제 코드

주석이 계약을 두 문단으로 적는다.

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L388-L393 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L388-L393))

> This function is always called inside a microtask, or at the very end of a rendering task right before we yield to the main thread. It should never be called synchronously.

> This function also never performs React work synchronously; it should only schedule work to be performed later, in a separate task or microtask.

할 일이 없거나 멈춰 있으면 콜백을 지운다.

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L420-L439 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L420-L439))

```js
// ReactFiberRootScheduler.js L432-L438
    // Fast path: There's nothing to work on.
    if (existingCallbackNode !== null) {
      cancelCallback(existingCallbackNode);
    }
    root.callbackNode = null;
    root.callbackPriority = NoLane;
    return NoLane;
```

동기 작업이면 태스크를 안 건다.

```js
// ReactFiberRootScheduler.js L449-L456
    // Synchronous work is always flushed at the end of the microtask, so we
    // don't need to schedule an additional task.
    if (existingCallbackNode !== null) {
      cancelCallback(existingCallbackNode);
    }
    root.callbackPriority = SyncLane;
    root.callbackNode = null;
    return SyncLane;
```

> Synchronous work is always flushed at the end of the microtask, so we don't need to schedule an additional task.

그 외에는 우선순위를 골라 태스크를 건다.

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L480-L507 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L480-L507))

```js
// ReactFiberRootScheduler.js L500-L507
    const newCallbackNode = scheduleCallback(
      schedulerPriorityLevel,
      performWorkOnRootViaSchedulerTask.bind(null, root),
    );

    root.callbackPriority = newCallbackPriority;
    root.callbackNode = newCallbackNode;
    return newCallbackPriority;
```

## 동작 흐름

```text
 L397  markStarvedLanesAsExpired(root, currentTime)
 L400  진행 중인 렌더·패시브 상태를 읽는다                L400-405
 L406  nextLanes 를 정한다
         [enableYieldingBeforePassive] 이고 이 루트가 패시브 대기면
           pendingPassiveEffectsLanes 를 쓴다
         아니면 getNextLanes(...)

 갈래 (가)  할 일이 없거나 멈춰 있다                      L420-439
   nextLanes === NoLanes
   또는 이 루트가 데이터 대기 중
   또는 root.cancelPendingCommit !== null
   => 기존 콜백 취소 / callbackNode = null / callbackPriority = NoLane
   => return NoLane

 갈래 (나)  sync lane 이고 prerendering 이 아니다         L442-456
   => 기존 콜백 취소 / callbackPriority = SyncLane / callbackNode = null
   => return SyncLane
   **태스크를 안 건다**

 갈래 (다)  그 외                                          L457-508
   L460  newCallbackPriority = getHighestPriorityLane(nextLanes)
   L462  기존 우선순위와 같으면 => return (태스크 재사용)   L474
           단 [__DEV__] act 스코프면 예외로 다시 건다      L467-471
   L477  다르면 기존을 취소
   L481  lanesToEventPriority 로 스케줄러 우선순위를 고른다
   L500  scheduleCallback(level, performWorkOnRootViaSchedulerTask.bind(null, root))
   L505  callbackPriority / callbackNode 를 기록
   => return newCallbackPriority
```

```text
 return 문은 넷이고 값 종류는 셋이다

 L438  NoLane
 L456  SyncLane
 L474  newCallbackPriority   (태스크 재사용)
 L507  newCallbackPriority   (새 태스크)

 그런데 (다) 갈래가 sync lane 을 돌려줄 수도 있다
 L447 의 !checkIfRootIsPrerendering 이 거짓이면
 sync lane 이어도 (나)를 건너뛰고 (다)로 오기 때문이다

 즉 "SyncLane 을 돌려주면 태스크를 안 걸었다" 가 아니다
 주석이 그 사정을 적는다 (L444-446)
   prerendering 중에는 lane 이 sync 여도 concurrent 루프를 써서
   메인 스레드를 막지 않는다
```

```text
 갈래 셋 모델이 깨지는 경우가 있다

 "태스크를 건다" 와 "이 마이크로태스크에서 동기로 렌더한다" 는
 배타적이지 않다

 (1) gesture 렌더 [enableGestureTransition]
     GestureLane 은 sync lane 이 아니라 (다) 갈래로 가 **태스크를 건다**
     그런데 [01] L326 이 mightHavePendingSyncWork 를 켜고
     [03] L234 의 isGestureRender 가 그 자리에서 performSyncWorkOnRoot 를 부른다
     => 태스크를 걸어 놓고 같은 마이크로태스크에서 렌더한다

 (2) syncTransitionLanes 가 세워진 경우 ([01] L276 또는 L283)
     [01] L322 가 **루트와 무관하게** mightHavePendingSyncWork 를 켜고
     [03] L211-217 이 getNextLanesToFlushSync 로 구해 동기로 돌린다

 두 경우 모두 걸어 둔 태스크는 나중에 떠서
 [04] L580 의 getNextLanes 가 NoLanes 를 주면 그냥 돌아간다

 (주석은 없다. 세 자리를 이어 보고 내가 판단한 것이다)


 호출자는 NoLane 인지만 본다

 [01] L294  if (nextLanes === NoLane) { 리스트에서 뺀다 }

 그 밖의 값은 전부 "남겨 둔다" 로 같게 취급한다
 다만 L320 에서 sync 인지 다시 보고
 mightHavePendingSyncWork 를 세운다

 즉 "태스크를 걸었나" 를 호출자가 알 필요가 없는 구조다
```

```text
 태스크 재사용 조건에 act 예외가 붙어 있다

 L462  newCallbackPriority === existingCallbackPriority
 L467  && !( __DEV__ && actQueue !== null && existingCallbackNode !== fakeActCallbackNode )

 즉 우선순위가 같아도
 act 스코프 안인데 기존 태스크가 스케줄러 것이면 취소하고 다시 건다

 주석이 그 이유를 적는다 (L464-466)
   "Special case related to `act`. If the currently scheduled task is a
    Scheduler task, rather than an `act` task, cancel it and re-schedule
    on the `act` queue."
```

```text
 우선순위는 넷으로 접힌다

 L481  switch (lanesToEventPriority(nextLanes))
         DiscreteEventPriority   -> UserBlockingSchedulerPriority
         ContinuousEventPriority -> UserBlockingSchedulerPriority
         DefaultEventPriority    -> NormalSchedulerPriority
         IdleEventPriority       -> IdleSchedulerPriority
         default                 -> NormalSchedulerPriority

 이 switch 에는 ImmediatePriority 가 없다 - 다만 범위 한정이다
 주석의 "this path" 가 그 한정이고, 같은 파일 L682·L692 에서는 실제로 쓴다
 (L482-484)
   "Scheduler does have an "ImmediatePriority", but now that we use
    microtasks for sync work we no longer use that. Any sync work that
    reaches this path is meant to be time sliced."
```

```text
 이 함수는 [04] 에서도 불린다

 [04] L599 가 렌더를 마친 뒤 부른다
 마이크로태스크 밖인데도 부르는 이유를 주석이 적는다 (L594-598)
   "Usually `scheduleTaskForRootDuringMicrotask` only runs inside a microtask;
    however, since most of the logic for determining if we need a continuation
    versus a new task is the same, we cheat a bit and call it here. This is
    only safe to do because we know we're at the end of the browser task.
    So although it's not an actual microtask, it might as well be."

 계약 주석(L388-390)도 그 경우를 미리 허용해 두었다 -
 "or at the very end of a rendering task right before we yield to the main thread"
```

## 결과가 쓰이는 곳

```text
 반환값
      --> [01] 이 NoLane 인지 보고 리스트 유지를 정한다
      --> sync 계열이면 mightHavePendingSyncWork 를 세운다
      --> [04] 는 반환값을 안 쓰고 root.callbackNode 를 직접 본다

 root.callbackNode
      --> 스케줄러가 돌려준 태스크 객체다
      --> [04] 가 continuation 판별에 쓴다
      --> act 모드에서는 가짜 노드가 들어간다

 root.callbackPriority
      --> 다음 호출에서 재사용 판단의 기준이다
```

## 다루지 않는 것

`getNextLanes` 와 `markStarvedLanesAsExpired` 의 lane 계산, `checkIfRootIsPrerendering` 의 판정, `lanesToEventPriority` 와 `getHighestPriorityLane` 의 lane 매핑, `isWorkLoopSuspendedOnData` 가 보는 상태, `enableYieldingBeforePassive` 갈래의 패시브 이펙트 사정은 같은 뼈대의 곁가지라 요약만 했다. 우선순위 대응표는 [spi](../spi/README.md)에 있다.
