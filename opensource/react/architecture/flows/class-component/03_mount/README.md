# 마운트

상위: [클래스 컴포넌트](../README.md)

첫 렌더가 세우는 것들. `instance.state` 를 `memoizedState` 로 다시 맞추는 줄이 **넷**인데, 그것이 이 함수의 리듬이다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberClassComponent.js` L761-L850 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassComponent.js#L761-L850))

파생 상태 `packages/react-reconciler` / `src` / `ReactFiberClassComponent.js` L129-L163 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassComponent.js#L129-L163))

## 실제 코드

앞머리가 인스턴스의 칸들을 채운다.

```js
// ReactFiberClassComponent.js L771-L786
  const instance = workInProgress.stateNode;
  instance.props = newProps;
  instance.state = workInProgress.memoizedState;
  instance.refs = {};

  initializeUpdateQueue(workInProgress);

  const contextType = ctor.contextType;
  if (typeof contextType === 'object' && contextType !== null) {
    instance.context = readContext(contextType);
  } else if (disableLegacyContext) {
    instance.context = emptyContextObject;
  } else {
    const unmaskedContext = getUnmaskedContext(workInProgress, ctor, true);
    instance.context = getMaskedContext(workInProgress, unmaskedContext);
  }
```

뒷머리가 파생 상태와 레거시 생명주기를 처리하고 플래그를 세운다.

```js
// ReactFiberClassComponent.js L815-L849
  instance.state = workInProgress.memoizedState;

  const getDerivedStateFromProps = ctor.getDerivedStateFromProps;
  if (typeof getDerivedStateFromProps === 'function') {
    applyDerivedStateFromProps(
      workInProgress,
      ctor,
      getDerivedStateFromProps,
      newProps,
    );
    instance.state = workInProgress.memoizedState;
  }

  // In order to support react-lifecycles-compat polyfilled components,
  // Unsafe lifecycles should not be invoked for components using the new APIs.
  if (
    typeof ctor.getDerivedStateFromProps !== 'function' &&
    typeof instance.getSnapshotBeforeUpdate !== 'function' &&
    (typeof instance.UNSAFE_componentWillMount === 'function' ||
      typeof instance.componentWillMount === 'function')
  ) {
    callComponentWillMount(workInProgress, instance);
    // If we had additional state updates during this life-cycle, let's
    // process them now.
    processUpdateQueue(workInProgress, newProps, instance, renderLanes);
    suspendIfUpdateReadFromEntangledAsyncAction();
    instance.state = workInProgress.memoizedState;
  }

  if (typeof instance.componentDidMount === 'function') {
    workInProgress.flags |= Update | LayoutStatic;
  }
  if (__DEV__ && (workInProgress.mode & StrictEffectsMode) !== NoMode) {
    workInProgress.flags |= MountLayoutDev;
  }
```

> In order to support react-lifecycles-compat polyfilled components, Unsafe lifecycles should not be invoked for components using the new APIs.

> If we had additional state updates during this life-cycle, let's process them now.

파생 상태는 업데이트 큐 밖에서 만들어진다.

```js
// ReactFiberClassComponent.js L149-L162
  // Merge the partial state and the previous state.
  const memoizedState =
    partialState === null || partialState === undefined
      ? prevState
      : assign({}, prevState, partialState);
  workInProgress.memoizedState = memoizedState;

  // Once the update queue is empty, persist the derived state onto the
  // base state.
  if (workInProgress.lanes === NoLanes) {
    // Queue is always non-null for classes
    const updateQueue: UpdateQueue<any> = workInProgress.updateQueue as any;
    updateQueue.baseState = memoizedState;
  }
```

> Once the update queue is empty, persist the derived state onto the base state.

## 동작 흐름

```text
 mountClassInstance  L761-850

 L767  [__DEV__]
 L768    checkClassInstance(workInProgress, ctor, newProps)   231줄의 경고

 L771  instance = workInProgress.stateNode
 L772  instance.props = newProps
 L773  instance.state = workInProgress.memoizedState     ** 첫 번째 **
 L774  instance.refs = {}                                ★ 문자열 ref 의 잔재
 L776  initializeUpdateQueue(workInProgress)             <- [업데이트 큐 01]

 L778  contextType = ctor.contextType
 L779  객체이고 null 이 아니면
 L780    instance.context = readContext(contextType)
 L781  아니면 disableLegacyContext 이면                    ★ **늘 여기다**
 L782    instance.context = emptyContextObject
 L783  아니면                                             ** [DEAD] **
 L785    instance.context = getMaskedContext(...)

 L788  [__DEV__] 세 가지를 본다
 L789    instance.state === newProps 이면 경고 (props 를 state 에 그대로 넣었다)
 L802    StrictLegacyMode 이면 recordLegacyContextWarning
 L809    recordUnsafeLifecycleWarnings                   (조건 없이)

 L815  instance.state = workInProgress.memoizedState     ** 두 번째 **

 L817  getDerivedStateFromProps = ctor.getDerivedStateFromProps
 L818  함수이면
 L819    applyDerivedStateFromProps(workInProgress, ctor, gDSFP, newProps)
 L825    instance.state = workInProgress.memoizedState   ** 세 번째 **

 L830  hasNewLifecycles 가 아니고 willMount 계열이 있으면
 L836    callComponentWillMount(workInProgress, instance)
 L839    processUpdateQueue(workInProgress, newProps, instance, renderLanes)
 L840    suspendIfUpdateReadFromEntangledAsyncAction()
 L841    instance.state = workInProgress.memoizedState   ** 네 번째 **

 L844  instance.componentDidMount 가 함수이면
 L845    workInProgress.flags |= Update | LayoutStatic
 L847  [__DEV__] StrictEffectsMode 이면
 L848    workInProgress.flags |= MountLayoutDev
```

```text
 ★★ 보통 마운트에서는 processUpdateQueue 가 안 불린다

 L839 는 L830-835 의 조건 안에만 있다
   getDerivedStateFromProps 도 없고
   getSnapshotBeforeUpdate 도 없고
   componentWillMount 계열이 있을 때

 => 요즘 쓰는 클래스(생성자 + render)는 이 가지에 안 들어간다.
    마운트 시점의 state 는 **생성자와 getDerivedStateFromProps** 가 만든다

 그러면 마운트 중에 큐에 들어온 업데이트는?
 L776 initializeUpdateQueue 가 baseState 를 memoizedState 로 잡아 두고,
 다음 렌더의 [04]가 처리한다
 (이 귀결은 내가 두 함수를 맞춰 보고 적은 것이고 주석에 없다)
```

```text
 ★ instance.state 를 다시 맞추는 줄이 넷이다

 L773  처음                       memoizedState 를 그대로
 L815  DEV 블록 뒤               ★ **중복이다**
 L825  파생 상태 뒤              바뀌었을 수 있다
 L841  큐 처리 뒤                바뀌었을 수 있다

 L815 가 중복인 근거 - L773 과 L815 사이에 memoizedState 를 바꾸는 것이 없다
   L774  instance.refs = {}                 관계없다
   L776  initializeUpdateQueue              fiber.memoizedState 를 **읽기만** 한다
                                            (UPD L178 baseState: fiber.memoizedState)
   L778-786  instance.context 만 건드린다
   L788-813  전부 DEV 경고다

 => 값은 같다. 쓰는 쪽이 방어적으로 다시 맞춘 것으로 보인다
    ※ 뒷문장은 내 판단이다
```

```text
 ★ instance.refs = {} 는 마운트에서만 쓴다

 L774 한 줄뿐이다. [04]의 resume/update 에는 없다.
 문자열 ref 시절의 잔재다
 (뒷문장은 내 판단이고 주석에 없다)
```

```text
 applyDerivedStateFromProps  L129-163

 L135  prevState = workInProgress.memoizedState
 L136  partialState = getDerivedStateFromProps(nextProps, prevState)
 L137  [__DEV__]
 L138    StrictLegacyMode 이면
 L142      partialState = getDerivedStateFromProps(...)   ★ 두 번째를 쓴다
 L147    warnOnUndefinedDerivedState(ctor, partialState)
 L150  memoizedState = partialState 가 null/undefined 이면 prevState
                       아니면 assign({}, prevState, partialState)
 L154  workInProgress.memoizedState = memoizedState
 L158  workInProgress.lanes === NoLanes 이면
 L161    updateQueue.baseState = memoizedState
```

```text
 ★ 병합 규칙이 UpdateState 와 글자까지 같다

 여기          L150-153  null/undefined 면 prevState, 아니면 assign 얕은 병합
 [업데이트 큐] UPD L448-453  똑같다

 => 파생 상태는 큐 밖에서 만들어지지만 합치는 방식은 setState 와 같다
```

```text
 ★★ lanes === NoLanes 가 뜻하는 것

 L158 의 조건은 "큐가 비었다" 가 아니다.
 processUpdateQueue 를 지난 뒤라면 **"우선순위가 모자라 건너뛴 업데이트가 없다"** 는 뜻이다
   UPD L593 이 건너뛴 갈래에서만 newLanes 에 merge 하고
   UPD L691 이 그것을 workInProgress.lanes 에 **덮어쓴다**

 왜 그때만 baseState 에 눌러 담는가 -
 건너뛴 것이 있으면 다음 렌더가 baseState 부터 다시 접어야 하는데,
 파생 상태를 베이스에 섞어 두면 그 재생이 틀어진다
 (이 설명은 내가 [업데이트 큐 03]과 맞춰 보고 적은 것이고 주석에 없다)

 ★ 다만 이 함수의 마운트 호출(L819)은 processUpdateQueue **앞**이다.
   거기서의 lanes 는 처리 잔여가 아니라 fiber 에 예약된 것 그대로다
```

## 결과가 쓰이는 곳

```text
 workInProgress.memoizedState / instance.state
      --> BW finishClassComponent 이 render 를 부를 때 this.state 다
      --> BW L1779 가 render 뒤에 instance 에서 되읽는다

 updateQueue
      --> [업데이트 큐]가 이어받는다
      --> baseState 가 파생 상태를 머금을 수 있다

 Update | LayoutStatic
      --> 커밋 레이아웃 패스가 componentDidMount 를 부른다
      --> LayoutStatic 은 StaticMask 에 있어 렌더를 넘어 산다
          (FFLAGS L137-138)

 MountLayoutDev
      --> StrictEffectsMode 의 이중 호출 표시다
```

## 다루지 않는 것

`checkClassInstance`(L296-526)의 검사 목록([02 인스턴스 만들기](../02_construct/README.md)에 대표 몇 개가 있다), `ReactStrictModeWarnings.recordLegacyContextWarning` / `recordUnsafeLifecycleWarnings`(L803, L809)가 경고를 모아 두었다가 커밋 때 쏟는 구조, `warnOnUndefinedDerivedState`(L113)의 검사 내용, `StrictEffectsMode` 와 `MountLayoutDev` 가 커밋에서 이펙트를 두 번 돌리는 경로([커밋](../../commit/README.md)에 있다), `instance.refs` 를 실제로 읽는 곳(문자열 ref 지원의 잔재), `emptyContextObject` 의 정체, 플래그를 끄지 않은 포크의 `getMaskedContext`(L785) 갈래는 같은 뼈대의 곁가지라 요약만 했다.
