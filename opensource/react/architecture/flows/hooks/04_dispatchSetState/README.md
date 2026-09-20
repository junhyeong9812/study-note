# dispatchSetState

상위: [훅 흐름](../README.md)

`setState` 를 부른다고 렌더가 도는 것은 아니다. **스케줄하지 않고 끝나는 갈래가 셋**이다.

## 위치

래퍼 `packages/react-reconciler` / `src` / `ReactFiberHooks.js` L3602-L3630 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHooks.js#L3602-L3630))

본체 `packages/react-reconciler` / `src` / `ReactFiberHooks.js` L3632-L3702 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHooks.js#L3632-L3702))

## 실제 코드

래퍼는 lane 을 정하고 넘긴 뒤, 반환된 boolean 을 읽는다.

```js
// ReactFiberHooks.js L3619-L3629
  const lane = requestUpdateLane(fiber);
  const didScheduleUpdate = dispatchSetStateInternal(
    fiber,
    queue,
    action,
    lane,
  );
  if (didScheduleUpdate) {
    startUpdateTimerByLane(lane, 'setState()', fiber);
  }
  markUpdateInDevTools(fiber, lane, action);
```

본체의 조기 바이아웃.

```js
// ReactFiberHooks.js L3675-L3683
          if (is(eagerState, currentState)) {
            // Fast path. We can bail out without scheduling React to re-render.
            // It's still possible that we'll need to rebase this update later,
            // if the component re-renders for a different reason and by that
            // time the reducer has changed.
            // TODO: Do we still need to entangle transitions in this case?
            enqueueConcurrentHookUpdateAndEagerlyBailout(fiber, queue, update);
            return false;
          }
```

> The queue is currently empty, which means we can eagerly compute the next state before entering the render phase. If the new state is the same as the current state, we **may be able to** bail out entirely.

> Fast path. We can bail out without scheduling React to re-render. It's **still possible** that we'll need to rebase this update later, if the component re-renders for a different reason and by that time the reducer has changed.

그리고 계산 중 에러는 삼킨다.

```js
// ReactFiberHooks.js L3684-L3689
        } catch (error) {
          // Suppress the error. It will throw again in the render phase.
        } finally {
          if (__DEV__) {
            ReactSharedInternals.H = prevDispatcher;
          }
```

## 동작 흐름

```text
 [래퍼] dispatchSetState  L3602
 L3607  [FLAG:__DEV__] 두 번째 인자 오용 경고
 L3619  lane = requestUpdateLane(fiber)
 L3620  didScheduleUpdate = dispatchSetStateInternal(fiber, queue, action, lane)
 L3626  didScheduleUpdate 이면
 L3627    startUpdateTimerByLane(lane, 'setState()', fiber)
 L3629  markUpdateInDevTools(fiber, lane, action)

 [본체] dispatchSetStateInternal  L3632
 L3638  update = { lane, revertLane, gesture, action,
                   hasEagerState: false, eagerState: null, next: null }

 L3648  렌더 단계 갱신이면 (isRenderPhaseUpdate)
 L3649    enqueueRenderPhaseUpdate(queue, update)
           => 아래로 흘러 L3701 return false

 L3650  아니면
 L3652    fiber.lanes 도 NoLanes 이고
 L3654    alternate 가 null 이거나 그 lanes 도 NoLanes 이면 (큐가 비었다)
 L3660      lastRenderedReducer 가 있으면
 L3662        [FLAG:__DEV__] 디스패처를 InvalidNested... 로 바꾼다
 L3666        try {
 L3667          currentState = queue.lastRenderedState
 L3668          eagerState = lastRenderedReducer(currentState, action)
 L3673          update.hasEagerState = true
 L3674          update.eagerState = eagerState
 L3675          is(eagerState, currentState) 이면
 L3681            enqueueConcurrentHookUpdateAndEagerlyBailout(fiber, queue, update)
 L3682            => return false        ** 렌더를 스케줄하지 않는다 **
 L3684        } catch (error) {
 L3685          // Suppress the error. It will throw again in the render phase.
 L3686        } finally {
 L3688          [FLAG:__DEV__] 디스패처를 되돌린다

 L3694    root = enqueueConcurrentHookUpdate(fiber, queue, update, lane)
 L3695    root 가 null 이 아니면
 L3696      scheduleUpdateOnFiber(root, fiber, lane)      -> [스케줄링]
 L3697      entangleTransitionUpdate(root, queue, lane)
 L3698      => return true

 L3701  => return false
```

```text
 ★ false 로 끝나는 길이 셋이다

 1  조기 바이아웃            L3682
    큐가 비었고 미리 계산한 다음 상태가 지금과 같다

 2  렌더 단계 갱신           L3648-3649 -> L3701
    렌더 중에 부른 setState 다. 스케줄이 아니라
    didScheduleRenderPhaseUpdateDuringThisPass 를 세워
    [02] renderWithHooksAgain 이 처리한다

 3  root 가 null             L3694-3695 -> L3701
    이미 떨어져 나간 fiber 다

 true 는 L3698 한 곳뿐이다 - 실제로 scheduleUpdateOnFiber 를 친 경우
```

```text
 그 boolean 을 누가 읽나

 읽는 곳은 L3626 하나다.
 쓰임은 startUpdateTimerByLane - 성능 트랙 타이머다

 => "바이아웃된 setState 가 성능 트랙에 가짜 업데이트로 찍히지 않게" 가
    이 반환값의 전부다

 본체를 부르는 다른 네 자리(L3172, L3179, L3195, L3393)는
 반환값을 버린다
```

```text
 조기 바이아웃이 "업데이트를 버리는" 것은 아니다

 L3681  enqueueConcurrentHookUpdateAndEagerlyBailout(fiber, queue, update)

 함수 이름이 말하듯 큐에 **넣고** 바이아웃한다
 주석이 이유를 적는다 (L3676-3679)
   나중에 이 갱신을 재베이스해야 할 수도 있다
   컴포넌트가 다른 이유로 다시 렌더되고
   그때 reducer 가 바뀌어 있을 수 있기 때문이다

 => "렌더를 스케줄하지 않는다" 와 "업데이트를 버린다" 는 다르다
```

```text
 미리 계산한 값을 재사용한다

 L3673  update.hasEagerState = true
 L3674  update.eagerState = eagerState

 주석 L3669-3672
   미리 계산한 상태와 그 계산에 쓴 reducer 를 update 에 얹어 둔다
   렌더 단계에 들어갈 때까지 reducer 가 바뀌지 않았다면
   reducer 를 다시 부르지 않고 그 값을 쓸 수 있다

 (주석은 "and the reducer used to compute it" 이라 적지만
  update 객체에 reducer 칸은 없다 - L3638-3646.
  소스 주석과 구조가 어긋나는 자리다)

 그리고 계산이 던지면 L3673-3674 에 닿지 못해
 hasEagerState 가 false 로 남고, 에러는 삼켜진 뒤
 정상 스케줄 경로로 간다
```

```text
 조기 바이아웃의 전제

 L3652-3655  fiber.lanes === NoLanes
             && (alternate === null || alternate.lanes === NoLanes)

 "이 fiber 에 아직 처리 안 된 갱신이 하나도 없다" 는 뜻이다
 큐에 뭔가 있으면 미리 계산한 값이 틀릴 수 있어 이 길로 안 간다

 그래서 연달아 setState 를 부르면
 첫 번째만 이 판정을 받는다
```

## 결과가 쓰이는 곳

```text
 scheduleUpdateOnFiber (L3696)
      --> [스케줄링] 흐름으로 간다
      --> 렌더가 도는 유일한 길이다

 queue.pending
      --> 다음 렌더의 updateReducerImpl 이 baseQueue 에 접합해 처리한다

 update.hasEagerState / eagerState
      --> 렌더 단계에서 reducer 재호출을 건너뛰는 데 쓴다

 반환 boolean
      --> L3626 에서 성능 트랙 타이머를 칠지 정한다
```

## 다루지 않는 것

`requestUpdateLane` 의 lane 계산, `enqueueConcurrentHookUpdate` / `enqueueConcurrentHookUpdateAndEagerlyBailout` 의 큐 조작, `isRenderPhaseUpdate`(L3814)와 `enqueueRenderPhaseUpdate`(L3824), `entangleTransitionUpdate`, `updateReducerImpl`(L1303)이 이 update 들을 처리하는 규칙(재베이스·optimistic·gesture 갈래), `dispatchReducerAction`(L3559)과 `dispatchOptimisticSetState`, `startUpdateTimerByLane` 의 성능 트랙은 같은 뼈대의 곁가지라 요약만 했다.
