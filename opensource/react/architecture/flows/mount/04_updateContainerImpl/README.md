# updateContainerImpl

상위: [마운트](../README.md)

children 을 **갱신 객체 하나로 포장해 큐에 넣는다.** 그리고 큐에 넣은 결과가 `null` 이면 아무것도 스케줄하지 않는다.

## 위치

`ReactFiberReconciler.js` `packages/react-reconciler` / `src` / `ReactFiberReconciler.js` L393-L458 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberReconciler.js#L393-L458))

## 실제 코드

들어오는 길이 둘이다. lane 을 요청하는 쪽과 고정하는 쪽.

`packages/react-reconciler` / `src` / `ReactFiberReconciler.js` L353-L391 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberReconciler.js#L353-L391))

```js
// ReactFiberReconciler.js L359-L369
  const current = container.current;
  const lane = requestUpdateLane(current);
  updateContainerImpl(
    current,
    lane,
    element,
    container,
    parentComponent,
    callback,
  );
  return lane;
```

핵심은 세 줄이다.

`packages/react-reconciler` / `src` / `ReactFiberReconciler.js` L433-L436 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberReconciler.js#L433-L436))

```js
// ReactFiberReconciler.js L433-L436
  const update = createUpdate(lane);
  // Caution: React DevTools currently depends on this property
  // being called "element".
  update.payload = {element};
```

> Caution: React DevTools currently depends on this property being called "element".

그리고 큐에 넣고 스케줄한다.

```js
// ReactFiberReconciler.js L452-L457
  const root = enqueueUpdate(rootFiber, update, lane);
  if (root !== null) {
    startUpdateTimerByLane(lane, 'root.render()', null);
    scheduleUpdateOnFiber(root, rootFiber, lane);
    entangleTransitions(root, rootFiber, lane);
  }
```

## 동작 흐름

```text
 [updateContainer]  L353
 L359  current = container.current
 L360  lane = requestUpdateLane(current)
 L361  updateContainerImpl(current, lane, element, container, null, null)
 L369  => return lane

 [updateContainerSync]  L372   unmount 가 쓴다
 L378  [!disableLegacyMode && LegacyRoot] flushPendingEffects()
 L382  updateContainerImpl(current, SyncLane, ...)   <- lane 고정
 L390  => return SyncLane

 [updateContainerImpl]  L393
 L401  [__DEV__] onScheduleRoot(container, element)
 L405  [enableSchedulingProfiler] markRenderScheduled(lane)
 L409  context = getContextForSubtree(parentComponent)
 L410  container.context 가 null 이면 context, 아니면 pendingContext 에
 L416  [__DEV__] 렌더 중 중첩 갱신이면 경고
 L433  update = createUpdate(lane)
 L436  update.payload = {element}
 L438  callback 을 정규화한다. 있으면 update.callback 에 단다
 L452  root = enqueueUpdate(rootFiber, update, lane)
 L453  root !== null 이면
 L454    startUpdateTimerByLane(lane, 'root.render()', null)
 L455    scheduleUpdateOnFiber(root, rootFiber, lane)
 L456    entangleTransitions(root, rootFiber, lane)
```

```text
 enqueueUpdate 가 null 을 주는 조건은 둘이다

 (1) ReactFiberClassUpdateQueue L229
     if (updateQueue === null) { return null; }
     주석 L230: "Only occurs if the fiber has been unmounted."

 (2) 큐는 있는데 루트까지 못 올라간 경우
     enqueueConcurrentClassUpdate -> getRootForUpdatedFiber 가
     return 체인을 끝까지 올라갔을 때 최상단이 HostRoot 가 아니면 null 이다
     (ReactFiberConcurrentUpdates)

 주석은 (1)만 설명한다. (2)도 null 을 내는데 계약 주석이 그것을 말하지 않는다
 => 주석만 읽으면 원인이 하나인 줄 안다

 그리고 L453 이 막는 것은 스케줄 하나가 아니라 셋이다
   L454 startUpdateTimerByLane / L455 scheduleUpdateOnFiber / L456 entangleTransitions
```

```text
 update 는 평범한 객체다

 createUpdate (ReactFiberClassUpdateQueue L210-221)
   { lane, tag: UpdateState, payload: null, callback: null, next: null }

 payload 를 채우는 것은 이 함수다 (L436)
 그리고 그 키 이름이 "element" 여야 한다고 주석이 경고한다 (L434-435)
 DevTools 가 그 이름에 의존하기 때문이다
```

```text
 큐는 원형 리스트다

 enqueueUpdate 가 두 갈래로 간다 (ReactFiberClassUpdateQueue L253, L272)

 렌더 페이즈 중 안전하지 않은 갱신이면 직접 끼운다 (L253-270)
   주석 L254-255: "This is an unsafe render phase update. Add directly to the
                   update queue so we can process it immediately during the
                   current render."
   처음이면 자기 자신을 next 로 가리켜 고리를 만든다 (L258-259)

 보통은 enqueueConcurrentClassUpdate 로 간다 (L272)
 root.render 는 이쪽이다
 (그 함수 내부는 읽지 않았다)
```

```text
 컨텍스트를 두 자리에 나눠 담는다

 L410  container.context 가 null 이면 context 에
 L412  아니면 pendingContext 에

 즉 처음 한 번만 context 이고 그 뒤로는 pendingContext 다
 (둘을 어떻게 쓰는지는 렌더 흐름의 일이라 확인하지 않았다)
```

```text
 updateContainerSync 의 첫 줄은 이 빌드에서 안 돈다

 L378  if (!disableLegacyMode && container.tag === LegacyRoot)

 react-dom 은 disableLegacyMode 가 true 라 (ReactFeatureFlags L192)
 앞 항이 언제나 거짓이다

 즉 unmount 경로에서 flushPendingEffects 는 호출되지 않는다
 (주석은 없다. 플래그 값을 확인하고 내가 판단한 것이다)
```

## 결과가 쓰이는 곳

```text
 update (payload = {element})
      --> 루트 fiber 의 updateQueue.shared.pending 에 쌓인다
      --> 렌더 중 HostRoot 를 처리할 때 꺼내 children 으로 쓴다

 enqueueUpdate 가 돌려준 root
      --> 그대로 scheduleUpdateOnFiber 의 첫 인자가 된다
      --> null 이면 흐름이 여기서 끝난다

 lane
      --> markRootUpdated 가 root.pendingLanes 에 합친다
      --> 마이크로태스크가 그것을 보고 우선순위를 정한다
```

## 다루지 않는 것

`requestUpdateLane` 이 실행 문맥과 transition 을 보고 lane 을 고르는 규칙, `enqueueConcurrentClassUpdate` 의 동시성 큐 구조, `getContextForSubtree` 와 legacy 컨텍스트, `entangleTransitions` 의 lane 얽힘 계산, `startUpdateTimerByLane` 의 계측, `onScheduleRoot` 의 DevTools 연동은 같은 뼈대의 곁가지라 요약만 했다.
