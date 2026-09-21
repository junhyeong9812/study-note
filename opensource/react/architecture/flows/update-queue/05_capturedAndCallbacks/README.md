# 에러 업데이트와 콜백

상위: [업데이트 큐](../README.md)

에러 업데이트는 보통 업데이트와 **반대로** 다룬다. 양쪽 큐가 아니라 **WIP 큐에만** 넣는다. 그리고 그 업데이트의 `callback` 이 실제로 에러를 찍고 `componentDidCatch` 를 부른다.

## 위치

에러 업데이트 `packages/react-reconciler` / `src` / `ReactFiberClassUpdateQueue.js` L304-L384 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassUpdateQueue.js#L304-L384))

콜백 `packages/react-reconciler` / `src` / `ReactFiberClassUpdateQueue.js` L700-L765 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassUpdateQueue.js#L700-L765))

## 실제 코드

WIP 큐에만 넣는 이유.

```js
// ReactFiberClassUpdateQueue.js L308-L311
  // Captured updates are updates that are thrown by a child during the render
  // phase. They should be discarded if the render is aborted. Therefore,
  // we should only put them on the work-in-progress queue, not the current one.
  let queue: UpdateQueue<State> = workInProgress.updateQueue as any;
```

> Captured updates are updates that are thrown by a child during the render phase. They should be discarded if the render is aborted. Therefore, we should **only** put them on the work-in-progress queue, not the current one.

복제를 여기서 직접 하는 이유.

```js
// ReactFiberClassUpdateQueue.js L318-L323
      // The work-in-progress queue is the same as current. This happens when
      // we bail out on a parent fiber that then captures an error thrown by
      // a child. Since we want to append the update only to the work-in
      // -progress queue, we need to clone the updates. We usually clone during
      // processUpdateQueue, but that didn't happen in this case because we
      // skipped over the parent when we bailed out.
```

그리고 흔한 쪽 — base 리스트 꼬리에 그냥 붙인다.

```js
// ReactFiberClassUpdateQueue.js L376-L383
  // Append the update to the end of the list.
  const lastBaseUpdate = queue.lastBaseUpdate;
  if (lastBaseUpdate === null) {
    queue.firstBaseUpdate = capturedUpdate;
  } else {
    lastBaseUpdate.next = capturedUpdate;
  }
  queue.lastBaseUpdate = capturedUpdate;
```

콜백 저장소가 둘로 갈리는 자리.

```js
// ReactFiberClassUpdateQueue.js L719-L735
export function deferHiddenCallbacks<State>(
  updateQueue: UpdateQueue<State>,
): void {
  // When an update finishes on a hidden component, its callback should not
  // be fired until/unless the component is made visible again. Stash the
  // callback on the shared queue object so it can be fired later.
  const newHiddenCallbacks = updateQueue.callbacks;
  if (newHiddenCallbacks !== null) {
    const existingHiddenCallbacks = updateQueue.shared.hiddenCallbacks;
    if (existingHiddenCallbacks === null) {
      updateQueue.shared.hiddenCallbacks = newHiddenCallbacks;
    } else {
      updateQueue.shared.hiddenCallbacks =
        existingHiddenCallbacks.concat(newHiddenCallbacks);
    }
  }
}
```

> When an update finishes on a hidden component, its callback should not be fired until/unless the component is made visible again. Stash the callback on the shared queue object so it can be fired later.

## 동작 흐름

```text
 enqueueCapturedUpdate  L304-384

 L311  queue = workInProgress.updateQueue
 L314  current = workInProgress.alternate
 L315  current !== null 이면
 L316    currentQueue = current.updateQueue
 L317    queue === currentQueue 이면      ** WIP 큐가 아직 복제본이 아니다 **

 L326      firstBaseUpdate = queue.firstBaseUpdate
 L327      null 이 아니면
 L329        update = firstBaseUpdate
 L330        do {
 L331          clone = { lane, tag, payload, callback: null, next: null }
                                          ↑ 리베이스와 같은 이유로 버린다
 L342          newLast === null 이면
 L343            newFirst = newLast = clone
 L344          아니면
 L345            newLast.next = clone
 L346            newLast = clone
 L349          update = update.next
 L350        } while (update !== null)

 L353        [$FlowFixMe invalid-compare]
 L354        newLast === null 이면
 L355          newFirst = newLast = capturedUpdate   ** 도달 불가 **
 L356        아니면
 L357          newLast.next = capturedUpdate
 L358          newLast = capturedUpdate
 L360      아니면                            (base 가 비어 있다)
 L362        newFirst = newLast = capturedUpdate

 L364      queue = { baseState: currentQueue.baseState,
                     firstBaseUpdate: newFirst,
                     lastBaseUpdate: newLast,
                     shared: currentQueue.shared,
                     callbacks: currentQueue.callbacks }   ★ **지킨다**
 L371      workInProgress.updateQueue = queue
 L372      => return

 --- 흔한 쪽 ---
 L377  lastBaseUpdate = queue.lastBaseUpdate
 L378  null 이면
 L379    queue.firstBaseUpdate = capturedUpdate
 L380  아니면
 L381    lastBaseUpdate.next = capturedUpdate
 L383  queue.lastBaseUpdate = capturedUpdate
```

```text
 ★ shared.pending 이 아니라 base 리스트 꼬리다

 L377-383 이 base 에 직접 붙인다. [02]의 enqueueUpdate 와 다르다

 => 이 WIP 의 **바로 다음** processUpdateQueue 가 반드시 본다
    (앞머리의 pending 흡수를 기다릴 필요가 없다)
 => 렌더가 버려지면 WIP 와 함께 사라진다. 주석 L308-310 의 의도 그대로다

 그리고 lane 도 지금 렌더 중인 것에서 뽑는다
   Throw L611  const lane = pickArbitraryLane(rootRenderLanes)
 => [03] L571 의 부분집합 검사에서 건너뛰어질 일이 사실상 없다
    (이 귀결은 내가 두 자리를 맞춰 보고 적은 것이고 주석에 없다)
```

```text
 ★★ 죽은 가지가 여기에도 있다

 L354  if (newLast === null)

 이 자리는 L327 `firstBaseUpdate !== null` 가지 안이다.
 그 안의 do-while(L330-350)은 최소 한 번 돌고,
 L343 이 newLast 를 반드시 대입한다

 => L355 는 실행되지 않는다
 => 지문이 같다. L353 의 `$FlowFixMe[invalid-compare]` 가
    [03] L676 의 것과 같은 억제 주석이다.
    이 주석을 알아보면 죽은 가지를 찾을 수 있다
```

```text
 ★ 복제 둘이 callbacks 한 칸에서 갈린다

 cloneUpdateQueue       L204  callbacks: null                   버린다
 enqueueCapturedUpdate  L369  callbacks: currentQueue.callbacks  지킨다

 둘 다 current 에서 WIP 큐를 만드는데 이 칸만 반대다.
 뒤엣것은 렌더 도중에 불리므로 이미 이번 렌더에서 모아 둔 콜백이 있다
 (이 설명은 내가 두 자리를 나란히 놓고 판단한 것이고 주석에 없다)
```

```text
 ★★ 에러 업데이트의 callback 이 진짜 일을 한다

 Throw initializeClassErrorUpdate  L120-
 L126  getDerivedStateFromError 가 함수이면
 L129    update.payload = () => getDerivedStateFromError(error)
            ★ 이것이 [04] L432 에서 불려 상태가 된다
 L132    update.callback = () => ... 
 L145      logCaughtError(root, fiber, errorInfo)

 L150  inst = fiber.stateNode
 L151  componentDidCatch 가 함수이면
 L153    update.callback = function callback() { ... }    ** 덮어쓴다 **
 L166      logCaughtError(root, fiber, errorInfo)
 L168      getDerivedStateFromError 가 함수가 아니면
 L174        markLegacyErrorBoundaryAsFailed(this)
 L181      this.componentDidCatch(error, { componentStack })

 => payload 와 callback 이 분업한다
      payload   상태   getDerivedStateFromError
      callback  부수효과  로깅 + componentDidCatch

 그 callback 이 [03] L632-643 에서 queue.callbacks 에 담기고
 L634 가 Callback 플래그를 세운다. 커밋 단계가 그것을 보고 부른다

 => 에러 바운더리에서 Callback 플래그가 중요한 이유가 이것이다
```

```text
 콜백 세 함수  L700-765

 callCallback  L700
 L701  함수가 아니면
 L702    => throw 'Invalid argument passed as callback. Expected a function. ...'
 L708  callback.call(context)

 deferHiddenCallbacks  L719
 L725  newHiddenCallbacks = updateQueue.callbacks
 L726  null 이 아니면
 L727    existingHiddenCallbacks = updateQueue.shared.hiddenCallbacks
 L728    null 이면
 L729      shared.hiddenCallbacks = newHiddenCallbacks
 L730    아니면
 L732      existingHiddenCallbacks.concat(newHiddenCallbacks) 로 대입
 ★ updateQueue.callbacks 를 **비우지 않는다**

 commitHiddenCallbacks  L737
 L743  hiddenCallbacks = updateQueue.shared.hiddenCallbacks
 L744  null 이 아니면
 L745    shared.hiddenCallbacks = null       ** 먼저 비운다 **
 L746    for 문으로 callCallback

 commitCallbacks  L753
 L757  callbacks = updateQueue.callbacks
 L758  null 이 아니면
 L759    updateQueue.callbacks = null        ** 먼저 비운다 **
 L760    for 문으로 callCallback
```

```text
 ★ 콜백 저장소가 둘이다

 queue.callbacks                이번 렌더에서 모은 것  ([03] L638-643)
 queue.shared.hiddenCallbacks   숨은 동안 미뤄 둔 것

 deferHiddenCallbacks 가 앞엣것을 뒤엣것으로 **옮긴다**.
 그런데 옮기고 나서 앞엣것을 비우지 않는다

 그래도 두 번 불리지 않는 이유 -
   미루기는 변이 단계에서 offscreenSubtreeIsHidden 일 때 일어나고,
   숨은 서브트리에는 레이아웃 이펙트가 커밋되지 않는다.
   즉 같은 커밋에서 commitCallbacks 가 안 불린다
 그리고 다음 렌더의 cloneUpdateQueue L204 가 callbacks 를 null 로 만든다
 (이 추적은 내가 세 파일을 맞춰 보고 적은 것이고 주석에 없다)

 ★ shared 에 두는 것이 핵심이다. shared 는 current 와 WIP 가
   같이 보는 객체라 숨은 동안 렌더가 몇 번 일어나도 안 사라진다
```

```text
 커밋 단계의 자리 넷 (실제 분기는 CMW 에 있고 CE 는 얇은 포장이다)

 보이는 서브트리가 숨겨져 있을 때
   CMW L2109  if (flags & Callback && offscreenSubtreeIsHidden)
   CMW L2113    deferHiddenCallbacks        (commitMutationEffectsOnFiber 의
                                             ClassComponent case L2099)
   ★ "전환하는 순간" 이 아니라 숨은 서브트리에서 Callback 을 만날 때마다다

 다시 보이게 될 때 (reappearLayoutEffects CMW L3136)
   CMW L3173  commitClassHiddenCallbacks    -> CE L568
   CMW L3177  commitClassCallbacks          -> CE L518
              조건 `includeWorkInProgressEffects && flags & Callback`

 보통 (commitLayoutEffectOnFiber CMW L591)
   CMW L629   commitClassCallbacks          -> CE L518   setState 의 콜백
   CMW L645   commitRootCallbacks           -> CE L592   root.render 의 콜백

 ★ CE L518 은 클래스 일반이다. componentDidMount 는 다른 함수다 (CE L497)
 ★ CE L592 는 HostRoot 전용이고 componentDidUpdate 와 무관하다
   instance 를 자식에서 찾아 넘긴다 (CE L598-607) -
   root.render(el, cb) 의 cb 가 받는 this 가 그것이다

 셋 다 try/catch 로 감싸 captureCommitPhaseError 로 보낸다
 => 콜백이 던져도 커밋이 멈추지 않고 에러 경계로 간다
```

## 결과가 쓰이는 곳

```text
 workInProgress.updateQueue (에러 경로)
      --> 되감기가 끝나고 다시 beginWork 할 때 [03]이 읽는다
      --> [04] L420 이 ShouldCapture 를 끄고 DidCapture 를 켠다

 queue.callbacks
      --> 커밋 단계 commitClassCallbacks / commitRootCallbacks

 queue.shared.hiddenCallbacks
      --> 다시 보이게 될 때 commitHiddenCallbacks

 Callback 플래그
      --> 커밋이 이 fiber 를 들여다볼 이유가 된다
      --> 에러 경계에서는 componentDidCatch 가 불릴 이유다
```

## 다루지 않는 것

`createRootErrorUpdate`(Throw L92) / `createClassErrorUpdate`(Throw L114) / `initializeClassErrorUpdate`(Throw L120)를 부르는 네 자리의 문맥([에러와 Suspense](../../throw/README.md)에 있다), `logCaughtError` / `logUncaughtError`(`ReactFiberErrorLogger`)와 `reportGlobalError`, `markLegacyErrorBoundaryAsFailed` / `isAlreadyFailedLegacyErrorBoundary` 의 배치별 재시도 정책, `callComponentDidCatchInDEV`(`ReactFiberCallUserSpace`), `captureCommitPhaseError` 가 콜백의 예외를 다시 경계로 보내는 경로, `offscreenSubtreeIsHidden` / `includeWorkInProgressEffects` 가 커밋 순회에서 켜지는 자리([커밋](../../commit/README.md)에 있다), `runWithFiberInDEV` 가 각 호출을 한 겹 더 감싸는 DEV 쌍둥이는 같은 뼈대의 곁가지라 요약만 했다.
