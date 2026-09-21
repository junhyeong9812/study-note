# 클래스 컴포넌트

상위: [React 아키텍처 지도](../../README.md)

생명주기가 실제로 불리는 자리다. 들어오는 길이 **셋**인데, 그 갈림이 `current` 가 아니라 **`instance` 가 있느냐**로 먼저 난다.

그리고 이 파일의 **40% 남짓이 DEV 전용**이다. `if (__DEV__)` 블록만 중괄호로 추적해 세면 496줄이고, 통째로 DEV 인 헬퍼 둘(L95-111, L113-127)과 `__DEV__ &&` 인라인 조건까지 더하면 515줄이다. 1227줄 중 42% — 과반은 아니지만 큰 소수다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberClassComponent.js` 기준이다. `BW` = `ReactFiberBeginWork.js`, `UPD` = `ReactFiberClassUpdateQueue.js`, `CE` = `ReactFiberCommitEffects.js`.

## 들어오는 길이 셋이다

```js
// ReactFiberBeginWork.js L1645-L1670
  const instance = workInProgress.stateNode;
  let shouldUpdate;
  if (instance === null) {
    resetSuspendedCurrentOnMountInLegacyMode(current, workInProgress);

    // In the initial pass we might need to construct the instance.
    constructClassInstance(workInProgress, Component, nextProps);
    mountClassInstance(workInProgress, Component, nextProps, renderLanes);
    shouldUpdate = true;
  } else if (current === null) {
    // In a resume, we'll already have an instance we can reuse.
    shouldUpdate = resumeMountClassInstance(
      workInProgress,
      Component,
      nextProps,
      renderLanes,
    );
  } else {
    shouldUpdate = updateClassInstance(
      current,
      workInProgress,
      Component,
      nextProps,
      renderLanes,
    );
  }
```

```text
 BW updateClassComponent 의 삼분기

 BW L1645  instance = workInProgress.stateNode

 BW L1647  instance === null 이면          --- (가) 처음 만든다
 BW L1651    constructClassInstance(...)
 BW L1652    mountClassInstance(...)
 BW L1653    shouldUpdate = true           ★ 묻지도 않는다

 BW L1654  아니면 current === null 이면     --- (나) 이어서 마운트
 BW L1656    shouldUpdate = resumeMountClassInstance(...)

 BW L1662  아니면                           --- (다) 업데이트
 BW L1663    shouldUpdate = updateClassInstance(...)

 ★ 순서가 instance 먼저, current 나중이다

 그래서 (나)는 **인스턴스는 있는데 current 가 없는** 상태다 -
 마운트 도중에 서스펜드했다가 다시 시도하는 길이다.
 이 갈래가 따로 있는 것이 이 파일의 구조를 가른다
```

1. [업데이터](01_updater/README.md) — `this.setState` 가 fiber 를 찾아가는 길.
2. [인스턴스 만들기](02_construct/README.md) — `new ctor()` 와 props 해소.
3. [마운트](03_mount/README.md) — 첫 렌더가 세우는 것.
4. [쌍둥이 둘](04_resumeAndUpdate/README.md) — 이어서 마운트 대 업데이트, 그 다섯 차이.
5. [render 부르기](05_finish/README.md) — 바이아웃 판정과 에러 회복.

```text
 ★ 네 번째 진입점이 있는데 [DEAD] 다

 BW L2189  mountIncompleteClassComponent
 BW L2201  주석 - "The rest of this function is a fork of `updateClassComponent`"
 BW L2198    // Promote the fiber to a class and try rendering again.
 BW L2199    workInProgress.tag = ClassComponent      ★ **승격**이 요점이다
 BW L2215    constructClassInstance(...)
 BW L2216    mountClassInstance(...)
 BW L2222    shouldUpdate 자리에 true 를 직접 넘긴다

 그런데 이 함수는 react-dom 에서 **불릴 수 없다**
   BW L4377  case IncompleteClassComponent: {
   BW L4378    if (disableLegacyMode) {
   BW L4379      break;                     ** 늘 여기로 빠진다 **
   [FLAG:disableLegacyMode=true]

 만드는 쪽도 같은 플래그로 꺼져 있다
   Throw L250-253  markSuspenseBoundaryShouldCapture 의 레거시 갈래 조건이
     !disableLegacyMode && (suspenseBoundary.mode & ConcurrentMode) === NoMode
   그 안에서만 Throw L292 sourceFiber.tag = IncompleteClassComponent 가 일어난다

 => 생산자도 소비자도 같은 플래그로 죽어 있다. 앞뒤가 맞는다
    ([beginWork]와 [completeWork]의 tag 표에도 죽은 것으로 적혀 있다)
```

## 생명주기가 불리는 자리

```text
 렌더 단계 (이 파일)

 constructor           02  L588  new ctor(props, context)
 getDerivedStateFromProps
                       03  L819  마운트
                       04  L936  이어서 마운트 / L1102 업데이트
 componentWillMount    03  L836  callComponentWillMount  (헬퍼를 거친다)
                       04  L965-970  ★ **인라인이다**. 헬퍼를 안 거친다
                           그래서 this.state 직접 대입을 못 잡는다 ([01]에 있다)
 componentWillReceiveProps
                       04  L902 / L1050  callComponentWillReceiveProps
 shouldComponentUpdate 04  L947 / L1113  checkShouldComponentUpdate
 componentWillUpdate   04  L1139-1144  업데이트만
 render                05  BW L1753  instance.render()

 커밋 단계 (CE - [커밋] 흐름)

 getSnapshotBeforeUpdate   CE L635  commitClassSnapshot
 componentDidMount         CE L404
 componentDidUpdate        CE L411 이 prevProps 를 만들어 넘긴다
 componentWillUnmount      CE L710  safelyCallComponentWillUnmount
 componentDidCatch         에러 업데이트의 callback 이다 ([업데이트 큐] 05)
```

```text
 ★★ 레거시 컨텍스트 갈래도 전부 [DEAD] 다

 shared/ReactFeatureFlags.js L174
   export const disableLegacyContext: boolean = true;
 (native-fb / www 포크만 false 다. 이 지도의 대상은 기본 포크다)

 그래서 ReactFiberLegacyContext.js 의 헬퍼가 전부 상수를 조기 반환한다
   L45-46    getUnmaskedContext   -> emptyContextObject
   L64-65    cacheContext         -> 그냥 return
   L77-78    getMaskedContext     -> emptyContextObject
   L113-114  hasContextChanged    -> **false**
   L121-122  isContextProvider    -> **false**

 이 파일에서 죽는 자리
   L578   `else if (!disableLegacyContext)` 가 늘 거짓
          -> L579-586 이 안 돈다. isLegacyContextConsumer 가 false 로 고정
   L698   그래서 L699 cacheContext 도 안 불린다
   L781   mountClassInstance 은 `else if (disableLegacyContext)` 를 타
          L782 instance.context = emptyContextObject
   L921 / L1070  두 바이아웃 조건의 hasContextChanged() 가 **상수 거짓 항**이다

 BW 에서 죽는 자리
   isLegacyContextProvider 가 늘 false -> hasContext 가 늘 false
   -> invalidateContextProvider 두 호출(BW L1711, BW L1783)이 도달 불가

 => 클래스가 읽는 컨텍스트는 static contextType 하나뿐이다 (L576-577 / L779-780).
    그리고 그것은 [컨텍스트 전파] 흐름의 readContext 다
```

```text
 ★ hasNewLifecycles 가 옛 생명주기를 전부 끈다

 getDerivedStateFromProps 나 getSnapshotBeforeUpdate 가 **하나라도** 있으면
 UNSAFE_ 계열이 아예 안 불린다

 판정하는 자리  L879-881 (resume) / L1031-1033 (update)
 가드하는 자리  L830-834 (mount) / L896-899 / L960-963 / L1041-1044 / L1134-1137

 주석이 이유를 적는다 (L828-829 등)
   "In order to support react-lifecycles-compat polyfilled components,
    Unsafe lifecycles should not be invoked for components using the new APIs."

 => 옛 API 와 새 API 를 섞으면 옛 것이 조용히 죽는다.
    DEV 가 그것을 경고한다 (L666-692)
```

```text
 ★ componentWillMount 와 UNSAFE_componentWillMount 가 둘 다 있으면
   **둘 다 불린다**

 L708-713   if 가 둘이고 else 가 아니다
 L735-740   componentWillReceiveProps 쪽도 같다
 L965-970 / L1139-1144  도 같은 모양이다

 => 하나를 고르는 것이 아니라 있는 것을 다 부른다
```

## 어디로 이어지는가

```text
 [업데이트 큐]  이 파일이 그 큐의 주 고객이다
                initializeUpdateQueue  L776
                cloneUpdateQueue       L1013
                processUpdateQueue     L839 / L915 / L1063
                hasForceUpdate 를 읽는 넷도 전부 여기다

 [beginWork]    updateClassComponent 가 이 파일을 부르고
                finishClassComponent 이 render 를 부른다

 [자식 조정]    에러 회복에서만 forceUnmountCurrentAndReconcile 로 간다
                (BW L374 에 있고 호출처가 BW L1767 하나뿐이다)

 [커밋]         Update / Snapshot / LayoutStatic 플래그를 여기서 세운다
                실제 호출은 CE 가 한다

 [에러와 Suspense]  DidCapture 를 보고 자식을 null 로 만드는 자리가
                BW L1733 이다
```

## 결과가 쓰이는 곳

```text
 shouldUpdate (boolean)
      --> finishClassComponent 이 받아 바이아웃할지 정한다
      --> 거짓이어도 memoizedProps/State 는 갱신한다

 workInProgress.stateNode
      --> 인스턴스 그 자체. 커밋 단계가 여기서 생명주기를 부른다

 workInProgress.memoizedState
      --> instance.state 와 같은 값을 유지한다
      --> BW L1779 가 render 뒤에 instance 에서 되읽는다

 Update / Snapshot / LayoutStatic 플래그
      --> 커밋이 어떤 생명주기를 부를지 정한다
      --> LayoutStatic 은 StaticMask 에 있어 렌더를 넘어 산다
```

## 다루지 않는 것

레거시 컨텍스트 헬퍼(`ReactFiberLegacyContext.js`)가 플래그를 끄지 **않은** 포크(native-fb, www)에서 실제로 하는 일과 `processChildContext` / `contextStackCursor` 의 스택 운용, `checkClassInstance`(L296-526)가 검사하는 항목 열아홉 가지 전체(231줄의 DEV 경고다 — [02 인스턴스 만들기](02_construct/README.md)에 대표 몇 개만 있다), `ReactStrictModeWarnings` 의 경고 수집, `getInstance` / `setInstance`(`ReactFiberTreeReflection`)의 저장 방식, `startUpdateTimerByLane` 과 `enableSchedulingProfiler` 의 마커, 커밋 단계에서 생명주기가 실제로 불리는 본문([커밋](../commit/README.md)과 `ReactFiberCommitEffects.js` 에 있다), `callComponentWillUnmountInDEV` / `callRenderInDEV`(`ReactFiberCallUserSpace`)의 감싸기는 이 문서의 범위 밖이다.

## 하위 메서드

- [01 업데이터](01_updater/README.md)
- [02 인스턴스 만들기](02_construct/README.md)
- [03 마운트](03_mount/README.md)
- [04 쌍둥이 둘](04_resumeAndUpdate/README.md)
- [05 render 부르기](05_finish/README.md)
