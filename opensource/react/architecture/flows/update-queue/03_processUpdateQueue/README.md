# 접기

상위: [업데이트 큐](../README.md)

리스트 하나를 훑어 상태 하나로 접는다. 그런데 **부족한 것은 건너뛰고, 건너뛴 뒤의 것은 전부 복제해 다시 남긴다.** 그 복제가 리베이스다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberClassUpdateQueue.js` L487-L698 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassUpdateQueue.js#L487-L698))

## 실제 코드

앞머리가 pending 을 base 로 옮긴다. 양쪽 큐에 같은 노드를 다는 자리다.

```js
// ReactFiberClassUpdateQueue.js L525-L543
    // If there's a current queue, and it's different from the base queue, then
    // we need to transfer the updates to that queue, too. Because the base
    // queue is a singly-linked list with no cycles, we can append to both
    // lists and take advantage of structural sharing.
    // TODO: Pass `current` as argument
    const current = workInProgress.alternate;
    if (current !== null) {
      // This is always non-null on a ClassComponent or HostRoot
      const currentQueue: UpdateQueue<State> = current.updateQueue as any;
      const currentLastBaseUpdate = currentQueue.lastBaseUpdate;
      if (currentLastBaseUpdate !== lastBaseUpdate) {
        if (currentLastBaseUpdate === null) {
          currentQueue.firstBaseUpdate = firstPendingUpdate;
        } else {
          currentLastBaseUpdate.next = firstPendingUpdate;
        }
        currentQueue.lastBaseUpdate = lastPendingUpdate;
      }
    }
```

> Because the base queue is a singly-linked list with no cycles, we can append to both lists and take advantage of structural sharing.

건너뛰는 갈래. 첫 스킵에서 베이스가 얼어붙는다.

```js
// ReactFiberClassUpdateQueue.js L574-L593
        // Priority is insufficient. Skip this update. If this is the first
        // skipped update, the previous update/state is the new base
        // update/state.
        const clone: Update<State> = {
          lane: updateLane,

          tag: update.tag,
          payload: update.payload,
          callback: update.callback,

          next: null,
        };
        if (newLastBaseUpdate === null) {
          newFirstBaseUpdate = newLastBaseUpdate = clone;
          newBaseState = newState;
        } else {
          newLastBaseUpdate = newLastBaseUpdate.next = clone;
        }
        // Update the remaining priority in the queue.
        newLanes = mergeLanes(newLanes, updateLane);
```

처리하는 갈래. 앞에 스킵이 있었으면 복제해서 남긴다.

```js
// ReactFiberClassUpdateQueue.js L604-L621
        if (newLastBaseUpdate !== null) {
          const clone: Update<State> = {
            // This update is going to be committed so we never want uncommit
            // it. Using NoLane works because 0 is a subset of all bitmasks, so
            // this will never be skipped by the check above.
            lane: NoLane,

            tag: update.tag,
            payload: update.payload,

            // When this update is rebased, we should not fire its
            // callback again.
            callback: null,

            next: null,
          };
          newLastBaseUpdate = newLastBaseUpdate.next = clone;
        }
```

> This update is going to be committed so we never want uncommit it. Using `NoLane` works because 0 is a subset of all bitmasks, so this will never be skipped **by the check above**.

> When this update is rebased, we should not fire its callback again.

## 동작 흐름

```text
 processUpdateQueue  L487-698

 L493  didReadFromEntangledAsyncAction = false
 L496  queue = workInProgress.updateQueue
        주석 L495 - "This is always non-null on a ClassComponent or HostRoot"
 L498  hasForceUpdate = false
 L501  [__DEV__] currentlyProcessingQueue = queue.shared

 --- (1) pending 을 base 로  L504-544 ---
 L504  firstBaseUpdate = queue.firstBaseUpdate
 L505  lastBaseUpdate = queue.lastBaseUpdate
 L508  pendingQueue = queue.shared.pending
 L509  pendingQueue !== null 이면
 L510    queue.shared.pending = null
 L514    lastPendingUpdate = pendingQueue           ** pending 은 꼬리다 **
 L515    firstPendingUpdate = lastPendingUpdate.next
 L516    lastPendingUpdate.next = null              ** 원형을 끊는다 **
 L518    lastBaseUpdate === null 이면
 L519      firstBaseUpdate = firstPendingUpdate
 L520    아니면
 L521      lastBaseUpdate.next = firstPendingUpdate
 L523    lastBaseUpdate = lastPendingUpdate

 L530    current = workInProgress.alternate
 L531    current !== null 이면
 L533      currentQueue = current.updateQueue
 L534      currentLastBaseUpdate = currentQueue.lastBaseUpdate
 L535      currentLastBaseUpdate !== lastBaseUpdate 이면
 L536        null 이면
 L537          currentQueue.firstBaseUpdate = firstPendingUpdate
 L538        아니면
 L539          currentLastBaseUpdate.next = firstPendingUpdate
 L541        currentQueue.lastBaseUpdate = lastPendingUpdate
              ★ **같은 노드를 양쪽에 단다**
```

```text
 --- (2) 순회  L547-693 ---
 L547  firstBaseUpdate !== null 이면
 L549    newState = queue.baseState
 L552    newLanes = NoLanes
 L554    newBaseState = null
 L555    newFirstBaseUpdate = null
 L556    newLastBaseUpdate = null
 L558    update = firstBaseUpdate

 L559    do {
 L563      updateLane = removeLanes(update.lane, OffscreenLane)
 L564      isHiddenUpdate = updateLane !== update.lane
 L569      shouldSkipUpdate =
 L570        isHiddenUpdate 이면
                !isSubsetOfLanes(getWorkInProgressRootRenderLanes(), updateLane)
 L571        아니면
                !isSubsetOfLanes(renderLanes, updateLane)

 L573      shouldSkipUpdate 이면              === 건너뛴다 ===
 L577        clone = { lane: updateLane, tag, payload, callback, next: null }
                                 ↑ OffscreenLane 비트가 벗겨진 채 저장된다
                                              ↑ callback 을 **지킨다**
 L586        newLastBaseUpdate === null 이면   (첫 스킵이다)
 L587          newFirstBaseUpdate = newLastBaseUpdate = clone
 L588          newBaseState = newState        ★ **여기서 베이스가 얼어붙는다**
 L589        아니면
 L590          newLastBaseUpdate = newLastBaseUpdate.next = clone
 L593        newLanes = mergeLanes(newLanes, updateLane)

 L594      아니면                              === 처리한다 ===
 L600        updateLane !== NoLane
              && updateLane === peekEntangledActionLane() 이면
 L601          didReadFromEntangledAsyncAction = true
 L604        newLastBaseUpdate !== null 이면   (앞에 스킵이 있었다)
 L605          clone = { lane: NoLane, tag, payload, callback: null, next: null }
                                 ↑ 다시는 안 건너뛰게   ↑ callback 을 **버린다**
 L620          newLastBaseUpdate = newLastBaseUpdate.next = clone
 L624        newState = getStateFromUpdate(workInProgress, queue, update,
                                            newState, props, instance)
 L632        callback = update.callback
 L633        null 이 아니면
 L634          workInProgress.flags |= Callback
 L635          isHiddenUpdate 이면
 L636            workInProgress.flags |= Visibility
 L638          callbacks = queue.callbacks
 L639          null 이면
 L640            queue.callbacks = [callback]
 L641          아니면
 L642            callbacks.push(callback)

 --- 커서 전진 ---
 L647      update = update.next
 L648      null 이면
 L649        pendingQueue = queue.shared.pending
 L650        null 이면
 L651          break                       ** 유일한 정상 종료 **
 L652        아니면
 L655          lastPendingUpdate = pendingQueue
 L658          firstPendingUpdate = lastPendingUpdate.next
 L660          lastPendingUpdate.next = null
 L661          update = firstPendingUpdate
 L662          queue.lastBaseUpdate = lastPendingUpdate
 L663          queue.shared.pending = null
 L666    } while (true)
```

```text
 --- (3) 되쓰기  L668-692 ---
 L668    newLastBaseUpdate === null 이면    (스킵이 하나도 없었다)
 L669      newBaseState = newState
 L672    queue.baseState = newBaseState
 L673    queue.firstBaseUpdate = newFirstBaseUpdate
 L674    queue.lastBaseUpdate = newLastBaseUpdate
 L676    [$FlowFixMe invalid-compare]
 L677    firstBaseUpdate === null 이면
 L680      queue.shared.lanes = NoLanes      ** 도달 불가. 아래에 따로 적는다 **
 L690    markSkippedUpdateLanes(newLanes)
 L691    workInProgress.lanes = newLanes     ** merge 가 아니라 덮어쓰기다 **
 L692    workInProgress.memoizedState = newState
 L696  [__DEV__] currentlyProcessingQueue = null
```

```text
 ★ baseState 와 memoizedState 가 다른 것이다

 L692  workInProgress.memoizedState = newState
       다 적용한 상태. 화면이 이것을 본다

 L672  queue.baseState = newBaseState
       **첫 스킵 직전**의 상태. 다음 렌더가 여기서 다시 시작한다

 정해지는 자리가 둘이고 조건이 반대다
   L588  첫 스킵에서 얼린다        (스킵이 있었다)
   L669  루프가 끝난 뒤에 넣는다   (스킵이 없었다)

 => 스킵이 없으면 둘이 같고, 있으면 갈라진다.
    머리 주석의 "베이스 상태가 'A'" 가 L588 에서 나온다
```

```text
 ★ 복제가 둘인데 callback 처리가 반대다

 L582  건너뛴 복제    callback: update.callback     지킨다
 L616  리베이스 복제  callback: null                버린다

 건너뛴 것은 아직 안 불렸으니 나중에 불려야 하고,
 리베이스된 것은 이번 렌더에서 이미 불린다.
 주석 L614-615 가 뒤엣것만 적는다 - "When this update is rebased,
 we should not fire its callback again."

 그리고 lane 도 반대다
   L578  건너뛴 복제    lane: updateLane   ** OffscreenLane 이 벗겨진 채다 **
   L609  리베이스 복제  lane: NoLane       ** 0 은 모든 비트마스크의 부분집합 **

 => 건너뛴 것은 다음 렌더에서 isHiddenUpdate(L564)가 거짓이 된다
    (이 귀결은 내가 두 자리를 맞춰 보고 적은 것이고 주석에 없다)
```

```text
 ★ 숨은 트리 업데이트는 다른 renderLanes 로 판정한다

 L570  isHiddenUpdate 이면 getWorkInProgressRootRenderLanes()
 L571  아니면              인자로 받은 renderLanes

 주석 L566-568 이 이유를 적는다 - Offscreen 트리에 들어갈 때
 renderLanes 에 덧붙은 base lanes 를 무시해야 하기 때문이다.
 그래야 "트리가 숨겨지기 전부터 있던 업데이트" 와
 "숨겨진 뒤에 들어온 업데이트" 를 구분할 수 있다 (주석 L560-562)
```

```text
 ★ 리듀서 안에서 setState 를 하면 같은 루프가 이어 처리한다

 L649-664 가 루프를 끝내지 않고 새 pending 을 이어 붙인다.
 주석 L653-654 - "An update was scheduled from inside a reducer. Add the
 new pending updates to the end of the list and keep processing."

 DEV 는 이것을 경고한다 ([02] L237-242). 다만 **세션당 한 번뿐이다**
 (L239 !didWarnUpdateInsideUpdate / L249 에서 래치를 건다)
 => 경고하면서도 처리는 한다. 그리고 두 번째부터는 조용하다

 그런데 렌더 중에 shared.pending 이 차는 길이 하나뿐이다 -
 [02]의 렌더 단계 갈래(L253)다. 보통 업데이트는 주차장에 있어
 도는 루프에게 보이지 않는다
```

```text
 ★★ 앞머리와 중간이 대칭이 아니다

 앞머리 L530-543   current 큐에도 같은 노드를 단다 (구조 공유)
 중간   L655-663   queue.lastBaseUpdate 와 queue.shared.pending 만 건드린다
                   current.updateQueue 를 **안 건드린다**
                   지역 변수 firstBaseUpdate / lastBaseUpdate 도 갱신 안 한다

 이 함수에서 가장 뜻밖인 자리다.
 (주석이 이 비대칭을 설명하지 않는다 - 내가 두 블록을 나란히 놓고 본 것이다)
```

```text
 ★★ L677-681 은 도달할 수 없다

 L547 이 `firstBaseUpdate !== null` 로 감싸고 있는데
 L677 이 다시 `firstBaseUpdate === null` 을 묻는다

 이 지역 변수에 대입하는 자리가 파일 전체에 둘뿐이고 둘 다 L547 **위**다
   L504  let firstBaseUpdate = queue.firstBaseUpdate
   L519  firstBaseUpdate = firstPendingUpdate      (원형의 .next 라 null 이 아니다)

 L547-693 안에는 대입이 없다. 루프 커서는 다른 변수(L558 update)이고
 L673 은 지역 변수가 아니라 프로퍼티다

 => L680 `queue.shared.lanes = NoLanes` 는 **실행되지 않는다**
 => L676 의 `// $FlowFixMe[invalid-compare]` 가 그 자국이다.
    Flow 가 "항상 거짓인 비교" 를 잡은 것을 억눌러 둔 것이다

 파급 - shared.lanes 는 한 번도 지워지지 않는다.
 저장소 전체에서 그 칸을 건드리는 곳이 셋뿐이다
   L285  읽기   entangleTransitions
   L296  쓰기   sharedQueue.lanes = newQueueLanes   <- 유일한 산 쓰기
   L680  쓰기   죽은 코드

 그래서 트랜지션 엮기가 계속 과대 근사된다.
 보정은 L292 intersectLanes(queueLanes, root.pendingLanes) 이고,
 주석 L287-291 이 그 태도를 적는다 -
   "In some cases we may entangle more than we need to, but that's OK.
    In fact it's worse if we *don't* entangle when we should."

 => 의도한 조건은 newFirstBaseUpdate 쪽이었을 것 같다.
    ※ 이 추측은 주석에 적혀 있지 않다
```

```text
 L547 가드 밖으로 나가면 아무 것도 안 쓴다

 firstBaseUpdate 가 null 이면 (처리할 것이 없으면)
 L690-692 가 **실행되지 않는다**
   markSkippedUpdateLanes 도
   workInProgress.lanes 도
   workInProgress.memoizedState 도

 memoizedState 는 createWorkInProgress 가 복사해 둔 값 그대로 남는다
```

## 결과가 쓰이는 곳

```text
 workInProgress.memoizedState
      --> 클래스는 CC 가 instance.state 에 넣는다
      --> HostRoot 는 nextState.element 가 자식이 된다

 queue.baseState / firstBaseUpdate / lastBaseUpdate
      --> 다음 렌더가 이어받는다

 workInProgress.lanes
      --> 남은 것이 여기 담긴다 (덮어쓰기)
      --> markSkippedUpdateLanes 가 렌더 루트에도 알린다

 Callback / Visibility 플래그
      --> [커밋]이 queue.callbacks 를 부른다
      --> Visibility 는 숨은 트리에서 온 콜백 표시다

 didReadFromEntangledAsyncAction
      --> suspendIfUpdateReadFromEntangledAsyncAction 이 읽고 던진다
```

## 다루지 않는 것

`peekEntangledActionLane` / `peekEntangledActionThenable`(`ReactFiberAsyncAction`)과 비동기 액션 엮기의 전체 그림, `suspendIfUpdateReadFromEntangledAsyncAction`(L469-485)이 thenable 을 던진 뒤 어디로 가는지([에러와 Suspense](../../throw/README.md)에 있다), `getWorkInProgressRootRenderLanes` 와 Offscreen 트리에 들어갈 때 base lanes 가 덧붙는 경위, `markSkippedUpdateLanes`(`ReactFiberWorkLoop`)의 본문, `isSubsetOfLanes` / `removeLanes` / `mergeLanes`([lane 우선순위](../../lanes/README.md)에 있다), `currentlyProcessingQueue` 에 `try/finally` 가 없어 updater 가 던지면 남는 것과 그래서 있는 듯한 `resetCurrentlyProcessingQueue`(L167 — 저장소에 import 하는 곳이 없다)는 같은 뼈대의 곁가지라 요약만 했다.
