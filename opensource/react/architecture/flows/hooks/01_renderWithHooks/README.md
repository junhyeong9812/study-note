# renderWithHooks

상위: [훅 흐름](../README.md)

사용자 함수를 부르기 직전에 **전역에 fiber 를 꽂고**, 끝나면 **뽑는다.** 그 사이에만 훅이 동작한다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberHooks.js` L502-L631 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHooks.js#L502-L631))

## 실제 코드

전역을 세우고 훅 리스트를 비운다.

```js
// ReactFiberHooks.js L510-L511
  renderLanes = nextRenderLanes;
  currentlyRenderingFiber = workInProgress;
```

```js
// ReactFiberHooks.js L526-L528
  workInProgress.memoizedState = null;
  workInProgress.updateQueue = null;
  workInProgress.lanes = NoLanes;
```

운영 빌드의 디스패처 선택은 두 갈래다.

```js
// ReactFiberHooks.js L560-L563
    ReactSharedInternals.H =
      current === null || current.memoizedState === null
        ? HooksDispatcherOnMount
        : HooksDispatcherOnUpdate;
```

그리고 사용자 함수를 부른다. 그 앞뒤로 플래그 하나가 켜졌다 꺼진다.

```js
// ReactFiberHooks.js L592-L599
  const shouldDoubleRenderDEV =
    __DEV__ && (workInProgress.mode & StrictLegacyMode) !== NoMode;

  shouldDoubleInvokeUserFnsInHooksDEV = shouldDoubleRenderDEV;
  let children = __DEV__
    ? callComponentInDEV(Component, props, secondArg)
    : Component(props, secondArg);
  shouldDoubleInvokeUserFnsInHooksDEV = false;
```

## 동작 흐름

```text
 L502  function renderWithHooks(current, workInProgress, Component,
                                props, secondArg, nextRenderLanes)

 L510  renderLanes = nextRenderLanes
 L511  currentlyRenderingFiber = workInProgress

 L513  [FLAG:__DEV__]
 L514    hookTypesDev = current?._debugHookTypes
 L518    hookTypesUpdateIndexDev = -1
 L520    ignorePreviousDependencies = current !== null && current.type !== wip.type
 L523    warnIfAsyncClientComponent(Component)

 L526  workInProgress.memoizedState = null       <- 훅 리스트를 비운다
 L527  workInProgress.updateQueue = null
 L528  workInProgress.lanes = NoLanes

 --- 디스패처 선택 ---
 L546  [FLAG:__DEV__] 세 갈래
 L548    OnUpdateInDEV                  current 있고 memoizedState 있음
 L555    OnMountWithHookTypesInDEV      갱신인데 stateful 훅이 없던 경우
 L557    OnMountInDEV                   그 밖
 L559  운영은 두 갈래
 L561    current === null || current.memoizedState === null
 L562      ? HooksDispatcherOnMount
 L563      : HooksDispatcherOnUpdate

 L592  shouldDoubleRenderDEV = __DEV__ && (mode & StrictLegacyMode) !== NoMode
 L595  shouldDoubleInvokeUserFnsInHooksDEV = shouldDoubleRenderDEV
 L598  children = Component(props, secondArg)     ** 사용자 함수 **
         [FLAG:__DEV__] L597 callComponentInDEV
 L599  shouldDoubleInvokeUserFnsInHooksDEV = false

 L602  렌더 중 setState 가 있었으면
 L605    children = [02] renderWithHooksAgain(...)

 L613  [FLAG:__DEV__] shouldDoubleRenderDEV 이면
 L615    setIsStrictModeForDevtools(true)
 L616    try {
 L617      children = [02] renderWithHooksAgain(...)
 L623    } finally {
 L624      setIsStrictModeForDevtools(false)

 L628  [03] finishRenderingHooks(current, workInProgress, Component)
 L630  => return children
```

```text
 L602 와 L613 은 배타적이 아니다

 두 if 가 else 로 이어져 있지 않고 나란히 있다
 그래서 둘 다 참이면 renderWithHooksAgain 이 **두 번** 불린다

 L605  렌더 중 setState 때문에 (안정될 때까지 루프)
 L617  StrictMode 이중 호출 때문에 (do-while 이라 최소 한 번)
```

```text
 마운트인가 갱신인가를 무엇으로 정하나

 L561  current === null || current.memoizedState === null

 두 번째 조건이 눈에 띈다 - current 가 있어도
 memoizedState 가 null 이면 마운트로 친다

 주석이 이유를 적는다 (L543-545)
   stateful 훅을 하나도 안 쓰면 memoizedState 가
   갱신에서도 마운트에서도 null 이라 구분이 안 된다

 그리고 그 바로 위 L539-542 에 TODO 가 있다
   훅을 전혀 안 쓰다가 쓰기 시작하면 경고해야 하는데
   지금은 그 갱신을 마운트로 인식한다
   React.lazy 같은 것에는 정당한 경우라 까다롭다고 덧붙인다

 => [훅 흐름] README 에 적은 "조용한 리셋" 이 여기서 일어난다
```

```text
 ★ 긴 주석이 설명하는 코드는 두 줄이다

 L566-591 에 스물여섯 줄짜리 주석이 있다.
 요지는 이렇다

   StrictMode 개발 빌드에서는 컴포넌트 함수를 두 번 부른다
   그런데 두 번째 호출은 첫 호출의 훅 상태를 재사용하므로
   useMemo 같은 것이 다시 돌지 않는다

   그래서 사용자 함수(useMemo 의 create 등)의 이중 호출은
   **첫** 호출 때만 하고 두 번째 호출 때는 하지 않는다

   이유는 use 가 서스펜드했을 때 첫 시도의 promise 를 재사용하기 때문이다
   그것 자체가 일종의 메모이제이션이라,
   use 의 입력과 출력이 같은 호출에서 나와야 한다

 그 구현이 두 줄이다
   L595  shouldDoubleInvokeUserFnsInHooksDEV = shouldDoubleRenderDEV;
   L599  shouldDoubleInvokeUserFnsInHooksDEV = false;

 첫 Component 호출(L598)만 이 플래그가 켜진 채로 돈다
 [02]로 들어가는 두 경로는 전부 꺼진 상태다

 그리고 try/finally 가 아니라서
 첫 호출이 던지면 L599 가 실행되지 않는다
 (다음 renderWithHooks 의 L595 가 덮어쓴다)
```

```text
 이 함수를 거치지 않는 진입점이 있다

 replaySuspendedComponentWithHooks (L751-785)
   서스펜드했던 컴포넌트를 재생할 때 쓴다
   L777  renderWithHooksAgain(...) 을 직접 부르고
   L783  finishRenderingHooks(...) 를 부른다

 ★ 그래서 L526 의 "훅 리스트 비우기" 를 하지 않는다
   서스펜드 전에 만들어 둔 훅들을 그대로 재사용한다
   L776 에서 updateQueue 만 비운다
```

## 결과가 쓰이는 곳

```text
 children
      --> [beginWork]의 updateFunctionComponent 가 받아
          reconcileChildren 으로 넘긴다

 ReactSharedInternals.H
      --> useState 등이 이것을 찾아 부른다
      --> [03]이 ContextOnlyDispatcher 로 되돌린다

 currentlyRenderingFiber / renderLanes
      --> 훅 구현들이 읽는다
      --> [03]이 지운다

 workInProgress.memoizedState
      --> 훅 리스트의 머리가 된다
      --> 다음 렌더의 L561 이 이것을 본다
```

## 다루지 않는 것

`callComponentInDEV` 와 DEV 스택 처리, `warnIfAsyncClientComponent`, `hookTypesDev` 를 쓰는 DEV 순서 검사, `setIsStrictModeForDevtools`, `replaySuspendedComponentWithHooks`(L751)의 나머지, `renderTransitionAwareHostComponentWithHooks`(L855)와 `TransitionAwareHostComponent`(L870)는 같은 뼈대의 곁가지라 요약만 했다. 디스패처 목록은 [spi](../spi/README.md)에 있다.
