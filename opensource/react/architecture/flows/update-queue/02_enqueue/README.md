# 줄 세우기

상위: [업데이트 큐](../README.md)

`setState` 를 부른 그 순간 업데이트는 **큐에 들어가지 않는다.** 평평한 배열에 주차했다가 다음 렌더가 시작될 때 비로소 엮인다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberClassUpdateQueue.js` L223-L274 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassUpdateQueue.js#L223-L274))

주차장 `packages/react-reconciler` / `src` / `ReactFiberConcurrentUpdates.js` L40-L45 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberConcurrentUpdates.js#L40-L45))

## 실제 코드

갈래가 둘인데, 흔한 쪽은 아래 `else` 다.

```js
// ReactFiberClassUpdateQueue.js L253-L273
  if (isUnsafeClassRenderPhaseUpdate(fiber)) {
    // This is an unsafe render phase update. Add directly to the update
    // queue so we can process it immediately during the current render.
    const pending = sharedQueue.pending;
    if (pending === null) {
      // This is the first update. Create a circular list.
      update.next = update;
    } else {
      update.next = pending.next;
      pending.next = update;
    }
    sharedQueue.pending = update;

    // Update the childLanes even though we're most likely already rendering
    // this fiber. This is for backwards compatibility in the case where you
    // update a different component during render phase than the one that is
    // currently renderings (a pattern that is accompanied by a warning).
    return unsafe_markUpdateLaneFromFiberToRoot(fiber, lane);
  } else {
    return enqueueConcurrentClassUpdate(fiber, sharedQueue, update, lane);
  }
```

> This is an unsafe render phase update. Add directly to the update queue so we can process it immediately during the current render.

그 `else` 가 가는 곳이 이 배열이다.

```js
// ReactFiberConcurrentUpdates.js L40-L45

// If a render is in progress, and we receive an update from a concurrent event,
// we wait until the current render is over (either finished or interrupted)
// before adding it to the fiber/hook queue. Push to this array so we can
// access the queue, fiber, update, et al later.
const concurrentQueues: Array<any> = [];
```

> If a render is in progress, and we receive an update from a concurrent event, we wait until the current render is over (either finished or interrupted) before adding it to the fiber/hook queue.

그리고 주차할 때 하는 일.

```js
// ReactFiberConcurrentUpdates.js L90-L113
function enqueueUpdate(
  fiber: Fiber,
  queue: ConcurrentQueue | null,
  update: ConcurrentUpdate | null,
  lane: Lane,
) {
  // Don't update the `childLanes` on the return path yet. If we already in
  // the middle of rendering, wait until after it has completed.
  concurrentQueues[concurrentQueuesIndex++] = fiber;
  concurrentQueues[concurrentQueuesIndex++] = queue;
  concurrentQueues[concurrentQueuesIndex++] = update;
  concurrentQueues[concurrentQueuesIndex++] = lane;

  concurrentlyUpdatedLanes = mergeLanes(concurrentlyUpdatedLanes, lane);

  // The fiber's `lane` field is used in some places to check if any work is
  // scheduled, to perform an eager bailout, so we need to update it immediately.
  // TODO: We should probably move this to the "shared" queue instead.
  fiber.lanes = mergeLanes(fiber.lanes, lane);
  const alternate = fiber.alternate;
  if (alternate !== null) {
    alternate.lanes = mergeLanes(alternate.lanes, lane);
  }
}
```

> Don't update the `childLanes` on the return path yet. If we already in the middle of rendering, wait until after it has completed.

> The fiber's `lane` field is used in some places to check if any work is scheduled, to perform an eager bailout, so we need to update it immediately. **TODO: We should probably move this to the "shared" queue instead.**

## 동작 흐름

```text
 enqueueUpdate  L223-274

 L228  updateQueue = fiber.updateQueue
 L229  null 이면
 L231    => return null
          주석 L230 - "Only occurs if the fiber has been unmounted."
          ★ 부르는 쪽이 이 값을 스케줄할 root 로 쓴다.
            즉 여기로 빠지면 업데이트가 **말없이 버려진다**. 경고도 없다

 L234  sharedQueue = updateQueue.shared

 L236  [__DEV__]
 L237    currentlyProcessingQueue === sharedQueue
 L239    && !didWarnUpdateInsideUpdate 이면
 L242      console.error('An update (setState, replaceState, or forceUpdate)
                          was scheduled from inside an update function. ...')
 L249      didWarnUpdateInsideUpdate = true    ★ 한 번만 경고한다

 L253  isUnsafeClassRenderPhaseUpdate(fiber) 이면    --- 갈래 (가) 렌더 단계
 L256    pending = sharedQueue.pending
 L257    null 이면
 L259      update.next = update              ** 자기를 가리키는 원형 **
 L260    아니면
 L261      update.next = pending.next        ** 새것을 머리 앞에 끼운다 **
 L262      pending.next = update
 L264    sharedQueue.pending = update        ** pending 은 꼬리를 가리킨다 **
 L270    => return unsafe_markUpdateLaneFromFiberToRoot(fiber, lane)

 L271  아니면                                 --- 갈래 (나) 보통
 L272    => return enqueueConcurrentClassUpdate(fiber, sharedQueue, update, lane)
```

```text
 ★ pending 은 꼬리를 가리키는 원형 리스트다

 L264  sharedQueue.pending = update    마지막에 넣은 것

 그래서 첫 번째를 얻으려면 .next 를 한 번 따라간다.
 [03] 이 그렇게 읽는다
   L514  lastPendingUpdate = pendingQueue
   L515  firstPendingUpdate = lastPendingUpdate.next

 원형인 덕에 꼬리 포인터 하나로 머리와 꼬리를 둘 다 얻는다
 (이 설명은 내가 두 자리를 맞춰 보고 붙인 것이다)
```

```text
 ★ 갈래 (나) 가 곧장 큐로 안 간다 - 주차장을 거친다

 CCU enqueueUpdate  L90-113

 L98   concurrentQueues[i++] = fiber
 L99   concurrentQueues[i++] = queue
 L100  concurrentQueues[i++] = update
 L101  concurrentQueues[i++] = lane
        ** 연결 리스트가 아니라 평평한 배열에 네 칸씩 **

 L103  concurrentlyUpdatedLanes 에 merge
 L108  fiber.lanes 에 merge          ★ 이것만은 **즉시** 한다
 L110  alternate 가 있으면
 L111    alternate.lanes 에도 merge

 즉 이 시점에 sharedQueue.pending 은 **아직 null 이다**
```

```text
 ★ 즉시 하는 것과 미루는 것이 갈린다

 즉시   fiber.lanes / alternate.lanes      CCU L108-112
        주석 L105-107 이 이유를 적는다 - 어떤 자리들은 이 칸을 보고
        "할 일이 있나" 를 판정해 eager bailout 을 하므로 바로 올려야 한다
        그리고 그 자리에 TODO 가 붙어 있다 - shared 큐로 옮겨야 할 것 같다고

 미룸   조상의 childLanes                   주석 CCU L96-97
        렌더 중이면 끝난 뒤에 하자고

 => 그래서 setState 직후 fiber.lanes 는 올라가 있지만
    조상 경로는 아직 칠해지지 않은 짧은 구간이 존재한다
```

```text
 엮기 finishQueueingConcurrentUpdates  CCU L50-81

 L51   endIndex = concurrentQueuesIndex
 L52   concurrentQueuesIndex = 0
 L54   concurrentlyUpdatedLanes = NoLanes
 L56   while (i < endIndex)
 L57     fiber / L60 queue / L62 update / L64 lane 을 꺼내며
 L58     꺼낸 칸을 null 로 지운다
 L68     queue 와 update 가 둘 다 null 이 아니면
 L69       pending = queue.pending
 L70       null 이면 L72 update.next = update
 L73       아니면 L74 update.next = pending.next; L75 pending.next = update
 L77       queue.pending = update        ★ 여기서 비로소 pending 이 생긴다
 L80     lane !== NoLane 이면
 L81       markUpdateLaneFromFiberToRoot(fiber, update, lane)

 ★ L69-77 이 UPD L256-264 와 **같은 코드**다.
   원형 리스트를 만드는 자리가 둘인 것이다

 부르는 곳 넷
   WL L2265   prepareFreshStack
   WL L2745   renderRootSync
   WL L3029   renderRootConcurrent
   CCU L149   enqueueConcurrentHookUpdateAndEagerlyBailout 의 누수 방지
```

```text
 ★ 누수 방지 갈래가 재미있다  CCU L127-151

 enqueueConcurrentHookUpdateAndEagerlyBailout 은 재렌더가 필요 없는
 업데이트를 넣는다. 그런데 재렌더를 안 잡으므로 (2)를 불러 줄 사람이 없다

 주석 L140-143
   "Usually we can rely on the upcoming render phase to process the concurrent
    queue. However, since this is a bail out, we're not scheduling any work
    here. So the update we just queued will leak until something else happens
    to schedule work (if ever)."

 L147  isConcurrentlyRendering = getWorkInProgressRoot() !== null
 L148  아니면
 L149    finishQueueingConcurrentUpdates()   ** 자기가 직접 엮는다 **
```

```text
 CCU 의 진입점 넷

 L115  enqueueConcurrentHookUpdate                   훅
 L127  enqueueConcurrentHookUpdateAndEagerlyBailout  훅, 재렌더 불필요
 L153  enqueueConcurrentClassUpdate                  클래스  <- L272 가 부른다
 L165  enqueueConcurrentRenderForLane                큐 없이 lane 만

 ★ 넷째가 queue 와 update 를 null 로 넘긴다 (L169).
   CCU L68 의 `if (queue !== null && update !== null)` 가드가 그래서 있다
```

## 결과가 쓰이는 곳

```text
 반환 FiberRoot
      --> 부르는 쪽이 scheduleUpdateOnFiber(root, ...) 에 넘긴다
      --> null 이면 언마운트된 fiber 라 아무 것도 안 한다

 sharedQueue.pending
      --> [03] 이 base 리스트로 옮긴다
      --> current 와 WIP 가 같이 본다

 fiber.lanes
      --> [beginWork]의 바이아웃 판정이 본다
```

## 다루지 않는 것

`isUnsafeClassRenderPhaseUpdate`(`ReactFiberWorkLoop`)가 무엇을 "unsafe" 로 보는지, `unsafe_markUpdateLaneFromFiberToRoot`(CCU L173)가 backwards compatibility 로만 남아 있다는 주석과 그 본문, `markUpdateLaneFromFiberToRoot` / `getRootForUpdatedFiber`(CCU)의 조상 순회와 `markHiddenUpdate`, `getConcurrentlyUpdatedLanes`(CCU L86)를 읽는 곳, `entangleTransitions`(L276)의 트랜지션 엮기, `requestUpdateLane` 이 lane 을 고르는 규칙([lane 우선순위](../../lanes/README.md)에 있다), 훅 쪽 `enqueueConcurrentHookUpdate` 경로는 같은 뼈대의 곁가지라 요약만 했다.
