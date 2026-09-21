# 업데이트 큐

상위: [React 아키텍처 지도](../../README.md)

`setState` 가 상태로 바뀌는 자리다. 이 파일에는 **76줄짜리 머리 주석**이 있고, 그것이 알고리즘 전체를 설명한다. 요지는 하나다 — **업데이트는 우선순위 순이 아니라 삽입 순으로 처리되고, 부족한 것은 건너뛰되 그 뒤의 것도 전부 남긴다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberClassUpdateQueue.js` 기준이다. `CCU` = `ReactFiberConcurrentUpdates.js`, `BW` = `ReactFiberBeginWork.js`, `CC` = `ReactFiberClassComponent.js`, `CMW` = `ReactFiberCommitWork.js`, `CE` = `ReactFiberCommitEffects.js`.

## 머리 주석이 알고리즘을 설명한다

```js
// ReactFiberClassUpdateQueue.js L45-L60
// Prioritization
// --------------
//
// Updates are not sorted by priority, but by insertion; new updates are always
// appended to the end of the list.
//
// The priority is still important, though. When processing the update queue
// during the render phase, only the updates with sufficient priority are
// included in the result. If we skip an update because it has insufficient
// priority, it remains in the queue to be processed later, during a lower
// priority render. Crucially, all updates subsequent to a skipped update also
// remain in the queue *regardless of their priority*. That means high priority
// updates are sometimes processed twice, at two separate priorities. We also
// keep track of a base state, that represents the state before the first
// update in the queue is applied.
//
```

우선순위 정렬을 안 한다는 말이 먼저 나오고, 그 다음 문장이 진짜 규칙이다. 건너뛴 업데이트 **뒤의 것도 우선순위와 무관하게 남는다**. 그래서 높은 우선순위 업데이트가 두 번 처리되는 일이 생긴다.

그 다음이 이 지도 전체에서 가장 중요한 예시다.

```js
// ReactFiberClassUpdateQueue.js L61-L85
// For example:
//
//   Given a base state of '', and the following queue of updates
//
//     A1 - B2 - C1 - D2
//
//   where the number indicates the priority, and the update is applied to the
//   previous state by appending a letter, React will process these updates as
//   two separate renders, one per distinct priority level:
//
//   First render, at priority 1:
//     Base state: ''
//     Updates: [A1, C1]
//     Result state: 'AC'
//
//   Second render, at priority 2:
//     Base state: 'A'            <-  The base state does not include C1,
//                                    because B2 was skipped.
//     Updates: [B2, C1, D2]      <-  C1 was rebased on top of B2
//     Result state: 'ABCD'
//
// Because we process updates in insertion order, and rebase high priority
// updates when preceding updates are skipped, the final result is deterministic
// regardless of priority. Intermediate state may vary according to system
// resources, but the final state is always the same.
```

읽는 법은 이렇다.

```text
 baseState ''  에 A1 - B2 - C1 - D2 가 쌓여 있다 (숫자가 우선순위)

 1차 렌더, 우선순위 1
      베이스 ''
      처리   [A1, C1]        B2 는 우선순위가 모자라 건너뛴다
      결과   'AC'            <- 화면에 이것이 보인다

 2차 렌더, 우선순위 2
      베이스 'A'             ★ 'AC' 가 아니다
      처리   [B2, C1, D2]    ★ C1 이 두 번째로 처리된다
      결과   'ABCD'

 베이스가 'A' 인 이유를 주석이 직접 적는다 L77-78
   "The base state does not include C1, because B2 was skipped."

 => 건너뛴 자리에서 베이스가 얼어붙고,
    그 뒤의 것은 전부 다시 처리 대상이 된다.
    이것을 **리베이스**라고 부른다
```

```text
 ★ 최종 상태는 결정적이다

 주석 L82-85
   "Because we process updates in insertion order, and rebase high priority
    updates when preceding updates are skipped, the final result is
    deterministic regardless of priority. Intermediate state may vary
    according to system resources, but the final state is always the same."

 중간 상태는 기계 사정에 따라 달라지지만 최종 상태는 같다.
 이 문장이 인터럽트 가능한 렌더링이 성립하는 근거다
```

## 전체 그림

```text
 setState 한 번이 상태가 되기까지 — 자리가 넷이다

 (1) 주차          CCU L98-101   concurrentQueues 배열에 네 칸씩 넣는다
      ★ 이 시점에는 아직 shared.pending 에 안 들어간다
      다만 fiber.lanes 는 즉시 올린다 (CCU L108-113)

 (2) 엮기          CCU L50-81    finishQueueingConcurrentUpdates
      렌더가 시작될 때 원형 연결 리스트로 잇고 shared.pending 에 건다

 (3) 옮기기        L504-544      processUpdateQueue 앞머리
      pending 원형을 끊어 base 리스트 꼬리에 붙인다
      ★ current 큐에도 **같은 노드**를 단다 (구조 공유)

 (4) 접기          L547-693      do-while 로 훑으며 건너뛰거나 처리한다
      처리는 [04] getStateFromUpdate 가 한다
```

1. [큐의 모양](01_queueShape/README.md) — Update 다섯 칸, 큐 셋 + shared, tag 넷.
2. [줄 세우기](02_enqueue/README.md) — 주차와 엮기. 렌더 단계 업데이트만 다른 길로 간다.
3. [접기](03_processUpdateQueue/README.md) — 건너뛰기와 리베이스, baseState 가 정해지는 두 자리.
4. [하나를 상태로](04_getStateFromUpdate/README.md) — switch 넷과 의도적 fallthrough.
5. [에러 업데이트와 콜백](05_capturedAndCallbacks/README.md) — WIP 큐에만 넣는 이유, 콜백 저장소 둘.

```text
 ★ 이 큐를 쓰는 것이 클래스만이 아니다 - 셋이다

 processUpdateQueue 호출처 다섯의 내역이 이렇다
   ClassComponent   CC L839   mountClassInstance
                      ★ 마운트 일반이 아니다. CC L830-835 의 레거시 생명주기
                        가지 안이다 - getDerivedStateFromProps 도
                        getSnapshotBeforeUpdate 도 없고
                        componentWillMount 가 있을 때만 여기로 온다
                    CC L915   resumeMountClassInstance
                    CC L1063  updateClassInstance
   HostRoot         BW L1819  updateHostRoot          <- root.render
   CacheComponent   BW L1239  updateCacheComponent    <- 캐시 경계

 그리고 useCacheRefresh 도 같은 큐를 쓴다.
 훅 쪽에서 **별칭 셋**으로 이 파일을 부른다 (Hooks L131-133)
   Hooks L3521  createLegacyQueueUpdate      = createUpdate
   Hooks L3522  enqueueLegacyQueueUpdate     = enqueueUpdate
   Hooks L3526  entangleLegacyQueueTransitions = entangleTransitions
 올라가며 찾는 대상이 `case CacheComponent: case HostRoot:` 다 (Hooks L3517-3518)

 => 별칭에 "Legacy" 가 붙어 있다. 훅 쪽에서 보면 이것이 옛 큐다
```

```text
 ★ 큐도 fiber 처럼 쌍으로 온다

 주석 L12-16
   "Like fibers, update queues come in pairs: a current queue, which
    represents the visible state of the screen, and a work-in-progress queue,
    which can be mutated and processed asynchronously before it is committed
    — a form of double buffering."

 그런데 **shared 만은 공유한다** — cloneUpdateQueue L203 이
   shared: currentQueue.shared
 로 그대로 넘긴다. baseState/firstBaseUpdate/lastBaseUpdate 는 복제하고
 shared 는 공유한다

 => 들어오는 업데이트(pending)는 양쪽이 같이 보고,
    처리 진행도(base 포인터)는 각자 갖는다
```

```text
 ★ 왜 양쪽 큐에 다 다는가

 주석 L34-43 이 이유를 양방향으로 적는다
   WIP 큐에만 달면  - current 에서 복제해 다시 시작할 때 사라진다
   current 에만 달면 - WIP 가 커밋되며 교체될 때 사라진다
   둘 다 달면       - 다음 WIP 에 반드시 들어간다

 그리고 마지막 괄호가 중복 적용 걱정을 미리 막는다 L41-43
   "(And because the work-in-progress queue becomes the current queue once
    it commits, there's no danger of applying the same update twice.)"
```

```text
 ★ 다만 머리 주석 한 줄이 코드와 어긋난다

 L18-19
   "Both queues share a persistent, singly-linked list structure.
    To schedule an update, we append it to the end of both queues."

 그런데 지금 **예약 시점**에는 양쪽 큐에 붙이지 않는다
   L264  sharedQueue.pending 에 넣거나
   L272  concurrent 큐로 보낸다

 양쪽 base 리스트에 같은 노드를 다는 일은
 **처리 시점**에 일어난다 - [03] L530-543

 => 일 자체는 지금도 하는데 시점이 다르다.
    주석대로 예약 시점의 양쪽 append 를 찾으면 없다

 나머지 대목(각 큐가 미처리 첫 포인터를 갖는다는 것,
 current 포인터는 커밋 때만 갱신된다는 것)은 지금도 맞다
```

## 어디로 이어지는가

```text
 [beginWork]    updateHostRoot 가 BW L1818-1819 에서 clone + process 한다
                updateCacheComponent 이 BW L1238-1239 에서 같은 짝을 부른다

 [훅]           같은 리베이스 규칙을 **따로 구현**한다
                ReactFiberHooks.js L1320-1563 이 짝이다
                다른 점 둘 - 훅 큐는 원형을 유지하고, revertLane 칸이 더 있다

 [에러와 Suspense]  경계를 찾은 뒤 CaptureUpdate 를 여기에 넣는다
                그리고 [04] L420 이 ShouldCapture 를 끄고 DidCapture 를 켠다

 [lane 우선순위]  isSubsetOfLanes 가 건너뛸지를 정하고
                markSkippedUpdateLanes 가 남은 것을 알린다

 [커밋]         콜백(setState 의 두 번째 인자)이 여기서 불린다
```

## 결과가 쓰이는 곳

```text
 workInProgress.memoizedState
      --> 렌더가 쓸 실제 state (L692)

 queue.baseState / firstBaseUpdate / lastBaseUpdate
      --> 다음 렌더가 이어받을 자리 (L672-674)

 workInProgress.lanes
      --> 건너뛴 것이 남긴 lanes (L691)
      --> 렌더 루프가 "아직 남았다" 를 안다

 Callback 플래그
      --> 커밋 단계가 queue.callbacks 를 부른다

 hasForceUpdate (모듈 전역)
      --> CC 가 shouldComponentUpdate 를 건너뛸지 판단한다
```

## 다루지 않는 것

`entangleTransitions`(L276)가 트랜지션 lane 을 엮는 규칙과 `markRootEntangled`, `ReactFiberConcurrentUpdates.js` 의 `markUpdateLaneFromFiberToRoot` / `getRootForUpdatedFiber` 본문, `unsafe_markUpdateLaneFromFiberToRoot` 가 "backwards compatibility" 로 남아 있는 사정, `peekEntangledActionLane` / `peekEntangledActionThenable`(`ReactFiberAsyncAction`)의 비동기 액션 엮기, 클래스 쪽 `enqueueSetState` / `enqueueReplaceState` / `enqueueForceUpdate`(CC L165-240)의 본문([클래스 컴포넌트] 흐름의 자리다), 훅 큐의 `revertLane` 과 낙관적 업데이트, `OffscreenLane` 이 숨은 트리 업데이트에 덧붙는 경위는 이 문서의 범위 밖이다.

## 하위 메서드

- [01 큐의 모양](01_queueShape/README.md)
- [02 줄 세우기](02_enqueue/README.md)
- [03 접기](03_processUpdateQueue/README.md)
- [04 하나를 상태로](04_getStateFromUpdate/README.md)
- [05 에러 업데이트와 콜백](05_capturedAndCallbacks/README.md)
