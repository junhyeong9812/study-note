# render 부르기

상위: [클래스 컴포넌트](../README.md)

`instance.render()` 가 불리는 자리다. 그리고 에러를 잡은 뒤라면 **자식을 통째로 버린다.**

## 위치

`packages/react-reconciler` / `src` / `ReactFiberBeginWork.js` L1695-L1787 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberBeginWork.js#L1695-L1787))

## 실제 코드

바이아웃 판정. ref 는 그 앞에 있다.

```js
// ReactFiberBeginWork.js L1703-L1715
  // Refs should update even if shouldComponentUpdate returns false
  markRef(current, workInProgress);

  const didCaptureError = (workInProgress.flags & DidCapture) !== NoFlags;

  if (!shouldUpdate && !didCaptureError) {
    // Context providers should defer to sCU for rendering
    if (hasContext) {
      invalidateContextProvider(workInProgress, Component, false);
    }

    return bailoutOnAlreadyFinishedWork(current, workInProgress, renderLanes);
  }
```

> Refs should update even if shouldComponentUpdate returns false

render 를 부르거나, 에러를 잡았으면 자식을 null 로 만든다.

```js
// ReactFiberBeginWork.js L1724-L1758
  if (
    didCaptureError &&
    typeof Component.getDerivedStateFromError !== 'function'
  ) {
    // If we captured an error, but getDerivedStateFromError is not defined,
    // unmount all the children. componentDidCatch will schedule an update to
    // re-render a fallback. This is temporary until we migrate everyone to
    // the new API.
    // TODO: Warn in a future release.
    nextChildren = null;

    if (enableProfilerTimer) {
      stopProfilerTimerIfRunning(workInProgress);
    }
  } else {
    if (enableSchedulingProfiler) {
      markComponentRenderStarted(workInProgress);
    }
    if (__DEV__) {
      nextChildren = callRenderInDEV(instance);
      if (workInProgress.mode & StrictLegacyMode) {
        setIsStrictModeForDevtools(true);
        try {
          callRenderInDEV(instance);
        } finally {
          setIsStrictModeForDevtools(false);
        }
      }
    } else {
      nextChildren = instance.render();
    }
    if (enableSchedulingProfiler) {
      markComponentRenderStopped();
    }
  }
```

> If we captured an error, but `getDerivedStateFromError` is not defined, unmount all the children. `componentDidCatch` will schedule an update to re-render a fallback. This is **temporary** until we migrate everyone to the new API.

에러에서 회복하는 중이면 자식을 재사용하지 않는다.

```js
// ReactFiberBeginWork.js L1760-L1786
  // React DevTools reads this flag.
  workInProgress.flags |= PerformedWork;
  if (current !== null && didCaptureError) {
    // If we're recovering from an error, reconcile without reusing any of
    // the existing children. Conceptually, the normal children and the children
    // that are shown on error are two different sets, so we shouldn't reuse
    // normal children even if their identities match.
    forceUnmountCurrentAndReconcile(
      current,
      workInProgress,
      nextChildren,
      renderLanes,
    );
  } else {
    reconcileChildren(current, workInProgress, nextChildren, renderLanes);
  }

  // Memoize state using the values we just used to render.
  // TODO: Restructure so we never read values from the instance.
  workInProgress.memoizedState = instance.state;

  // The context might have changed so we need to recalculate it.
  if (hasContext) {
    invalidateContextProvider(workInProgress, Component, true);
  }

  return workInProgress.child;
```

> If we're recovering from an error, reconcile without reusing any of the existing children. Conceptually, the normal children and the children that are shown on error are two different sets, so we shouldn't reuse normal children even if their identities match.

> TODO: Restructure so we never read values from the instance.

## 동작 흐름

```text
 finishClassComponent  BW L1695-1787

 L1704  markRef(current, workInProgress)     ★ 바이아웃보다 먼저다
 L1706  didCaptureError = (workInProgress.flags & DidCapture) !== NoFlags

 L1708  !shouldUpdate && !didCaptureError 이면
 L1710    hasContext 이면                     ** [DEAD] **
 L1711      invalidateContextProvider(workInProgress, Component, false)
 L1714    => return bailoutOnAlreadyFinishedWork(current, workInProgress, renderLanes)

 L1717  instance = workInProgress.stateNode

 L1724  didCaptureError 이고
 L1726  Component.getDerivedStateFromError 가 함수가 **아니면**
 L1733    nextChildren = null                ★ **자식을 전부 버린다**
 L1736    [FLAG:enableProfilerTimer] stopProfilerTimerIfRunning(workInProgress)
 L1738  아니면
 L1743    [__DEV__] nextChildren = callRenderInDEV(instance)
 L1744      StrictLegacyMode 이면
 L1747        callRenderInDEV(instance)       ★ **버린다**. 첫 번째를 쓴다
 L1753    nextChildren = instance.render()    ★ 여기가 render() 다

 L1761  workInProgress.flags |= PerformedWork
 L1762  current !== null 이고 didCaptureError 이면
 L1767    forceUnmountCurrentAndReconcile(current, workInProgress,
                                           nextChildren, renderLanes)
 L1773  아니면
 L1774    reconcileChildren(current, workInProgress, nextChildren, renderLanes)

 L1779  workInProgress.memoizedState = instance.state
 L1782  hasContext 이면                       ** [DEAD] **
 L1783    invalidateContextProvider(workInProgress, Component, true)
 L1786  => return workInProgress.child
```

```text
 ★ ref 는 바이아웃보다 먼저 처리한다

 L1704 가 L1708 의 바이아웃 판정보다 위에 있다.
 주석 L1703 이 그 의도를 적는다 -
   "Refs should update even if shouldComponentUpdate returns false"

 => shouldComponentUpdate 로 렌더를 막아도 ref 는 갱신된다
```

```text
 ★★ 에러 경계에 getDerivedStateFromError 가 없으면 자식이 null 이 된다

 L1724-1733

 주석 L1728-1731 이 이유를 적는다 -
   "If we captured an error, but getDerivedStateFromError is not defined,
    unmount all the children. componentDidCatch will schedule an update to
    re-render a fallback. This is temporary until we migrate everyone to
    the new API."
 그리고 L1732 에 별개의 TODO 가 붙어 있다 - "TODO: Warn in a future release."

 [업데이트 큐]에서 본 분업의 나머지 반쪽이다
   payload   = getDerivedStateFromError   -> 상태를 바꾼다
   callback  = componentDidCatch          -> 부수효과. setState 를 걸 수 있다

 payload 가 없으면 상태가 안 바뀌므로 그릴 것이 없다.
 그래서 일단 다 지우고 componentDidCatch 의 setState 를 기다린다

 => componentDidCatch 만 정의하고 setState 를 안 걸면 화면이 빈 채로 남는다
    (그 경우를 DEV 가 따로 경고한다 - Throw L185-192.
     조건이 `!includesSomeLane(fiber.lanes, SyncLane)` 이다 -
     즉 "상태 갱신이 예약되지 않았으면" 이다)
```

```text
 ★ 에러 회복에서는 자식을 재사용하지 않는다

 L1762-1772  forceUnmountCurrentAndReconcile

 주석 L1763-1766 -
   "If we're recovering from an error, reconcile without reusing any of the
    existing children. Conceptually, the normal children and the children
    that are shown on error are two different sets, so we shouldn't reuse
    normal children even if their identities match."

 => key 가 같아도 재사용하지 않는다.
    [자식 조정]의 재사용 규칙을 **의도적으로 끄는** 유일한 자리다

 그 함수는 BW L374 에 있는 로컬 함수다 (ReactChildFiber 의 것이 아니다).
 주석 BW L379 - "This function is fork of reconcileChildren. It's used in cases where we"
 안에서 reconcileChildFibers 를 두 번 부른다 (BW L382, L398)
 호출처는 L1767 하나뿐이다
```

```text
 ★ render 의 DEV 이중 호출은 첫 번째 것을 쓴다

 L1743  nextChildren = callRenderInDEV(instance)     <- 이것을 쓴다
 L1747  callRenderInDEV(instance)                    <- 맨 표현식. 버린다

 [02]에서 센 여섯 자리 중 이것이 "첫 번째를 쓰는" 셋 가운데 하나다.
 [02] L594 의 new ctor 는 반대로 두 번째를 쓴다

 ★ 대조로, 함수 컴포넌트는 **두 번째 렌더의 자식을 쓴다**
   Hooks L613  if (shouldDoubleRenderDEV) {
   Hooks L617    children = renderWithHooksAgain(...)
```

```text
 ★ 마지막에 instance 에서 state 를 되읽는다

 L1779  workInProgress.memoizedState = instance.state
 TODO L1778 - "Restructure so we never read values from the instance."

 보통 경로에서는 [04] L1181 이 이미 같은 값을 넣어 두었으므로 되풀이다.
 값이 달라질 수 있는 것은 render() 안에서 **this.state 를 직접 대입**했을 때다

 ★ render() 안의 this.setState 는 여기에 안 잡힌다.
   enqueueSetState 는 update 객체를 큐에 넣을 뿐 instance.state 를 안 바꾼다
   ([01] L171-180 에 대입이 없다)
```

```text
 [DEAD] invalidateContextProvider 두 자리

 L1711  didChange = false 로
 L1783  didChange = true 로

 둘 다 hasContext 가 참일 때만인데, hasContext 는
   BW L1637  isLegacyContextProvider(Component)
 이고 그것이 disableLegacyContext 때문에 늘 false 다
 => react-dom 에서 두 호출 모두 도달 불가다
```

## 결과가 쓰이는 곳

```text
 반환 workInProgress.child
      --> [렌더 루프]의 performUnitOfWork 가 다음 단위로 삼는다
      --> 바이아웃하면 bailoutOnAlreadyFinishedWork 의 반환값이다
          (자식이 없으면 null 이라 completeUnitOfWork 로 간다)

 nextChildren
      --> [자식 조정]이 옛 fiber 와 짝짓는다
      --> 에러 회복이면 짝짓지 않고 전부 새로 만든다

 PerformedWork
      --> 주석 L1760 - "React DevTools reads this flag."

 workInProgress.memoizedState
      --> 커밋 뒤 current 가 되어 다음 렌더의 oldState 가 된다
```

## 다루지 않는 것

`markRef`(BW)가 ref 를 비교해 `Ref` 플래그를 세우는 규칙, `bailoutOnAlreadyFinishedWork`(BW L3800 부근 — [beginWork](../../begin-work/README.md)에 있다), `callRenderInDEV`(`ReactFiberCallUserSpace`)가 render 를 감싸는 방식, `forceUnmountCurrentAndReconcile`(BW L374)이 `reconcileChildFibers` 를 두 번 부르는 본문([자식 조정](../../reconcile-children/README.md)의 규칙을 끄는 방식), `stopProfilerTimerIfRunning` 과 `markComponentRenderStarted` / `markComponentRenderStopped` 의 프로파일러 마커, `updateClassComponent` 앞머리의 DEV DevTools 에러 시뮬레이션(BW L1587-1631 — `shouldError` 로 경계를 강제로 터뜨리는 경로이고 `DidCapture` 를 세우는 세 번째 자리다), BW L1679-1691 의 "reassigning this.props" 경고, `invalidateContextProvider` 의 `processChildContext` 와 스택 운용은 같은 뼈대의 곁가지라 요약만 했다.
