# 큐의 모양

상위: [업데이트 큐](../README.md)

칸이 몇 개 없다. **Update 다섯 칸, 큐 네 칸 + shared.** 그런데 그 `shared` 한 칸이 current 와 WIP 사이에 공유되는 것이 이 자료구조의 전부다.

## 위치

타입 `packages/react-reconciler` / `src` / `ReactFiberClassUpdateQueue.js` L131-L153 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassUpdateQueue.js#L131-L153))

tag `packages/react-reconciler` / `src` / `ReactFiberClassUpdateQueue.js` L155-L158 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassUpdateQueue.js#L155-L158))

초기화 `packages/react-reconciler` / `src` / `ReactFiberClassUpdateQueue.js` L176-L208 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassUpdateQueue.js#L176-L208))

## 실제 코드

세 타입이 나란히 있다.

```js
// ReactFiberClassUpdateQueue.js L131-L153
export type Update<State> = {
  lane: Lane,

  tag: 0 | 1 | 2 | 3,
  payload: any,
  callback: (() => mixed) | null,

  next: Update<State> | null,
};

export type SharedQueue<State> = {
  pending: Update<State> | null,
  lanes: Lanes,
  hiddenCallbacks: Array<() => mixed> | null,
};

export type UpdateQueue<State> = {
  baseState: State,
  firstBaseUpdate: Update<State> | null,
  lastBaseUpdate: Update<State> | null,
  shared: SharedQueue<State>,
  callbacks: Array<() => mixed> | null,
};
```

tag 는 넷이고 전부 상수다.

```js
// ReactFiberClassUpdateQueue.js L155-L163
export const UpdateState = 0;
export const ReplaceState = 1;
export const ForceUpdate = 2;
export const CaptureUpdate = 3;

// Global state that is reset at the beginning of calling `processUpdateQueue`.
// It should only be read right after calling `processUpdateQueue`, via
// `checkHasForceUpdateAfterProcessing`.
let hasForceUpdate = false;
```

> Global state that is reset at the beginning of calling `processUpdateQueue`. It should **only** be read right after calling `processUpdateQueue`, via `checkHasForceUpdateAfterProcessing`.

복제할 때 무엇을 남기고 무엇을 버리는지가 여기서 갈린다.

```js
// ReactFiberClassUpdateQueue.js L191-L208
export function cloneUpdateQueue<State>(
  current: Fiber,
  workInProgress: Fiber,
): void {
  // Clone the update queue from current. Unless it's already a clone.
  const queue: UpdateQueue<State> = workInProgress.updateQueue as any;
  const currentQueue: UpdateQueue<State> = current.updateQueue as any;
  if (queue === currentQueue) {
    const clone: UpdateQueue<State> = {
      baseState: currentQueue.baseState,
      firstBaseUpdate: currentQueue.firstBaseUpdate,
      lastBaseUpdate: currentQueue.lastBaseUpdate,
      shared: currentQueue.shared,
      callbacks: null,
    };
    workInProgress.updateQueue = clone;
  }
}
```

## 동작 흐름

```text
 [모양] L131-153

 Update            다섯 칸
   lane            이 업데이트의 우선순위
   tag             0|1|2|3
   payload         새 상태 또는 상태를 만드는 함수
   callback        setState 의 두 번째 인자
   next            다음 업데이트

 SharedQueue       세 칸      ★ current 와 WIP 가 **같은 객체**를 본다
   pending         아직 base 로 안 옮긴 원형 리스트
   lanes           트랜지션 엮기용
   hiddenCallbacks 숨은 동안 미뤄 둔 콜백

 UpdateQueue       네 칸 + shared
   baseState       첫 업데이트를 적용하기 전의 상태
   firstBaseUpdate 아직 처리 안 한 첫 업데이트
   lastBaseUpdate  그 꼬리
   callbacks       이번 렌더에서 모은 콜백
   shared          ↑ 위의 것
```

```text
 [tag] L155-158

 L155  UpdateState   = 0    기본값. createUpdate 가 이것으로 만든다 (L214)
 L156  ReplaceState  = 1    payload 로 통째로 갈아끼운다
 L157  ForceUpdate   = 2    상태를 안 바꾸고 전역 플래그만 세운다
 L158  CaptureUpdate = 3    UpdateState 에 플래그 전이를 얹은 것
```

```text
 [초기화] initializeUpdateQueue  L176-189

 L178  baseState: fiber.memoizedState     ★ 지금 상태를 베이스로 삼는다
 L179  firstBaseUpdate: null
 L180  lastBaseUpdate: null
 L181  shared: { pending: null, lanes: NoLanes, hiddenCallbacks: null }
 L186  callbacks: null
 L188  fiber.updateQueue = queue

 부르는 곳 셋
   ReactFiberRoot L233  루트를 만들 때
   CC L776              mountClassInstance
   BW L1233             updateCacheComponent 의 마운트 갈래
```

```text
 [복제] cloneUpdateQueue  L191-208

 L196  queue = workInProgress.updateQueue
 L197  currentQueue = current.updateQueue
 L198  queue === currentQueue 이면        ** 아직 복제 안 했으면 **
 L200    baseState: currentQueue.baseState
 L201    firstBaseUpdate: currentQueue.firstBaseUpdate
 L202    lastBaseUpdate: currentQueue.lastBaseUpdate
 L203    shared: currentQueue.shared          ★ **공유한다**
 L204    callbacks: null                      ★ **버린다**
 L206    workInProgress.updateQueue = clone

 주석 L195 - "Clone the update queue from current. Unless it's already a clone."
 => 이미 복제본이면 아무 것도 안 한다. 멱등이다
```

```text
 ★ 복제가 하는 일이 네 칸에서 다 다르다

 baseState / firstBaseUpdate / lastBaseUpdate
      값을 복사한다. 포인터가 같은 노드를 가리키므로
      **리스트 자체는 공유**하고 "어디까지 봤나" 만 따로 갖는다

 shared
      객체를 공유한다. 그래서 새로 들어온 업데이트(pending)를
      양쪽이 같이 본다

 callbacks
      null 로 버린다. 콜백은 커밋될 렌더의 것만 유효하다

 => 이 네 칸의 처리가 다른 것이 "큐도 이중 버퍼링" 의 실제 내용이다
```

```text
 ★ 같은 복제인데 반대로 하는 자리가 있다

 cloneUpdateQueue        L204  callbacks: null
 enqueueCapturedUpdate   L369  callbacks: currentQueue.callbacks

 [05] 의 에러 업데이트 경로는 콜백을 **보존한다**.
 이미 이번 렌더에서 모아 둔 콜백을 버리면 안 되기 때문이다
 (다만 이것은 내가 두 자리를 나란히 놓고 판단한 것이고
  주석에 그 대비가 적혀 있지 않다)
```

```text
 ★ hasForceUpdate 는 모듈 전역이다  L163

 그래서 쓰는 규약이 주석에 붙어 있다 (L160-162)
   processUpdateQueue 를 부른 **직후에만** 읽으라고

 리셋하는 자리가 둘
   L498  processUpdateQueue 진입부 (스스로)
   L712  resetHasForceUpdateBeforeProcessing  (CC L911, CC L1059)

 세우는 자리는 하나
   L456  getStateFromUpdate 의 case ForceUpdate

 읽는 자리는 넷, 전부 CC 다
   CC L922, L946     resumeMountClassInstance
   CC L1071, L1112   updateClassInstance

 => forceUpdate() 가 shouldComponentUpdate 를 건너뛰는 것이
    이 전역 변수 하나로 구현되어 있다
```

## 결과가 쓰이는 곳

```text
 fiber.updateQueue
      --> [03] processUpdateQueue 가 읽는다
      --> 커밋 단계가 callbacks 를 읽는다

 queue.shared
      --> [02] 가 여기에 업데이트를 건다
      --> current 와 WIP 가 같이 본다

 tag
      --> [04] getStateFromUpdate 의 switch 가 가른다

 hasForceUpdate
      --> CC 가 바이아웃 판정에 쓴다
```

## 다루지 않는 것

`Update` 의 `lane` 이 `requestUpdateLane` 으로 정해지는 경위([lane 우선순위](../../lanes/README.md)에 있다), `SharedQueue.lanes` 가 `entangleTransitions`(L276)에서 쓰이는 규칙과 `markRootEntangled`, `didWarnUpdateInsideUpdate` / `currentlyProcessingQueue`(L165-174) DEV 변수의 나머지 쓰임, `resetCurrentlyProcessingQueue`(L167)를 부르는 곳, `initializeUpdateQueue` 가 `ReactFiberRoot.js` L233 에서 불릴 때의 `uninitializedFiber`, 훅 큐(`ReactFiberHooks.js` L196-197)의 `baseState` / `baseQueue` 칸 구성은 같은 뼈대의 곁가지라 요약만 했다.
