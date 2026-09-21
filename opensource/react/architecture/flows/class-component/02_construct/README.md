# 인스턴스 만들기

상위: [클래스 컴포넌트](../README.md)

`new ctor(props, context)` 를 부르고 fiber 와 이어 붙인다. 176줄 중 **133줄이 DEV 경고**다. 실제로 하는 일은 서른 줄이 안 된다.

## 위치

만들기 `packages/react-reconciler` / `src` / `ReactFiberClassComponent.js` L528-L703 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassComponent.js#L528-L703))

props 해소 `packages/react-reconciler` / `src` / `ReactFiberClassComponent.js` L1187-L1220 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassComponent.js#L1187-L1220))

## 실제 코드

하는 일 전부.

```js
// ReactFiberClassComponent.js L576-L608
  if (typeof contextType === 'object' && contextType !== null) {
    context = readContext(contextType as any);
  } else if (!disableLegacyContext) {
    unmaskedContext = getUnmaskedContext(workInProgress, ctor, true);
    const contextTypes = ctor.contextTypes;
    isLegacyContextConsumer =
      contextTypes !== null && contextTypes !== undefined;
    context = isLegacyContextConsumer
      ? getMaskedContext(workInProgress, unmaskedContext)
      : emptyContextObject;
  }

  let instance = new ctor(props, context);
  // Instantiate twice to help detect side-effects.
  if (__DEV__) {
    if (workInProgress.mode & StrictLegacyMode) {
      setIsStrictModeForDevtools(true);
      try {
        instance = new ctor(props, context);
      } finally {
        setIsStrictModeForDevtools(false);
      }
    }
  }

  const state = (workInProgress.memoizedState =
    instance.state !== null && instance.state !== undefined
      ? instance.state
      : null);
  instance.updater = classComponentUpdater;
  workInProgress.stateNode = instance;
  // The instance needs access to the fiber so that it can schedule updates
  setInstance(instance, workInProgress);
```

DEV 가 한 번 더 만들고 **두 번째 것을 채택한다**.

```js
// ReactFiberClassComponent.js L588-L599
  let instance = new ctor(props, context);
  // Instantiate twice to help detect side-effects.
  if (__DEV__) {
    if (workInProgress.mode & StrictLegacyMode) {
      setIsStrictModeForDevtools(true);
      try {
        instance = new ctor(props, context);
      } finally {
        setIsStrictModeForDevtools(false);
      }
    }
  }
```

> Instantiate twice to help detect side-effects.

props 해소는 두 가지를 한다.

```js
// ReactFiberClassComponent.js L1187-L1220
export function resolveClassComponentProps(
  Component: any,
  baseProps: Object,
): Object {
  let newProps = baseProps;

  // Remove ref from the props object, if it exists.
  if ('ref' in baseProps) {
    newProps = {} as any;
    for (const propName in baseProps) {
      if (propName !== 'ref') {
        newProps[propName] = baseProps[propName];
      }
    }
  }

  // Resolve default props.
  const defaultProps = Component.defaultProps;
  if (defaultProps) {
    // We may have already copied the props object above to remove ref. If so,
    // we can modify that. Otherwise, copy the props object with Object.assign.
    if (newProps === baseProps) {
      newProps = assign({}, newProps);
    }
    // Taken from old JSX runtime, where this used to live.
    for (const propName in defaultProps) {
      if (newProps[propName] === undefined) {
        newProps[propName] = defaultProps[propName];
      }
    }
  }

  return newProps;
}
```

> Taken from old JSX runtime, where this used to live.

## 동작 흐름

```text
 constructClassInstance  L528-703

 --- 컨텍스트를 구한다 ---
 L576  contextType 이 객체이고 null 이 아니면
 L577    context = readContext(contextType)        <- [컨텍스트 전파]
 L578  아니면 !disableLegacyContext 이면            ** [DEAD] **
 L579    unmaskedContext = getUnmaskedContext(...)
 L581    isLegacyContextConsumer = contextTypes 가 있나
 L583    context = isLegacyContextConsumer ? getMaskedContext(...) : emptyContextObject

 --- 만든다 ---
 L588  instance = new ctor(props, context)         ★ 사용자 생성자
 L590  [__DEV__]
 L591    workInProgress.mode & StrictLegacyMode 이면
 L594      instance = new ctor(props, context)     ★ **재대입**. 두 번째를 쓴다

 --- 잇는다 ---
 L601  state = workInProgress.memoizedState =
          instance.state 가 null/undefined 가 아니면 instance.state
          아니면 null
 L605  instance.updater = classComponentUpdater    ★ this.setState 의 통로
 L606  workInProgress.stateNode = instance
 L608  setInstance(instance, workInProgress)       ★ 되돌아오는 길
 L610  [__DEV__] instance._reactInternalInstance = fakeInternalInstance

 L698  isLegacyContextConsumer 이면                 ** [DEAD] **
 L699    cacheContext(workInProgress, unmaskedContext, context)
 L702  => return instance
```

```text
 ★ DEV 이중 생성은 두 번째 것을 채택한다

 L588  let instance = new ctor(...)
 L594      instance = new ctor(...)     <- 재대입이다

 첫 번째 인스턴스는 버려진다. 생성자가 부수효과를 일으켰다면
 그 효과는 두 번 일어나고 객체는 하나만 남는다

 ★ 이 "두 번 부르고 어느 것을 쓰나" 가 자리마다 다르다. 여섯을 모아 보면

   두 번째를 쓴다 (재대입)
     L594   new ctor                          <- 여기
     L142   getDerivedStateFromProps          [03]
     L266   shouldComponentUpdate             [04]

   첫 번째를 쓴다 (두 번째는 맨 표현식)
     BW L1743 / L1747  render                 [05]
     UPD L402 / L407   ReplaceState 의 함수 payload
     UPD L432 / L437   UpdateState 의 함수 payload

 세 대 셋이다. 주석은 어느 쪽에도 이유를 적지 않는다
```

```text
 ★ instance 와 fiber 를 잇는 두 줄

 L605  instance.updater = classComponentUpdater
       => this.setState 가 갈 곳. [01]이 그 객체다

 L608  setInstance(instance, workInProgress)
       => [01] L168 의 getInstance(inst) 가 돌아올 길

 그리고 L606 이 fiber -> instance 방향이다
 (커밋 단계가 workInProgress.stateNode 로 생명주기를 부른다)
```

```text
 ★ 레거시 컨텍스트 갈래가 죽어 있어서 생기는 것

 L578 이 늘 거짓이므로
   context 는 emptyContextObject 로 남고 (L535 초기값)
   isLegacyContextConsumer 도 false 로 남는다 (L533 초기값)
 => L698-700 의 cacheContext 도 안 불린다

 그 cacheContext 가 왜 여기 있는지는 주석 L696-697 이 적는다
   "Cache unmasked context so we can avoid recreating masked context unless
    necessary. ReactFiberLegacyContext usually updates this cache but can't
    for newly-created instances."
 getMaskedContext 가 보통 스스로 캐시하는데, L584 시점에는
 workInProgress.stateNode 가 아직 null 이라 못 한다는 뜻이다
 (그 사정은 플래그를 끄지 않은 포크에서만 의미가 있다)
```

```text
 resolveClassComponentProps  L1187-1220 — 두 가지를 한다

 L1194  'ref' in baseProps 이면
 L1195    newProps = {}
 L1196    ref 를 뺀 나머지를 얕게 복사한다

 L1204  defaultProps = Component.defaultProps
 L1205  있으면
 L1208    아직 복사 안 했으면 L1209 assign({}, newProps)
 L1212    defaultProps 의 키를 돈다
 L1213      newProps[propName] === undefined 이면
 L1214        defaultProps[propName] 로 채운다
 L1219  => return newProps

 ★ undefined 일 때만 채운다. null 은 안 채운다
 ★ 복사가 일어나면 **새 객체**가 나온다. 이것이 [04]에서
   "비교는 resolve 안 한 props 로 한다" 의 이유다
```

```text
 defaultProps 를 쓰는 자리가 여기뿐인가

 호출처 아홉을 세어 보면 클래스만은 아니다
   CC   L861 / L1016        [04]의 oldProps
   BW   L2102               mountLazyComponent 의 ClassComponent 갈래
   BW   L4306               beginWork 의 ClassComponent case
   BW   L4383               IncompleteClassComponent case      ** [DEAD] **
   BW   L4401               IncompleteFunctionComponent case   ** [DEAD] **
   CE   L411                componentDidUpdate 의 prevProps
   CE   L671                getSnapshotBeforeUpdate 의 prevProps
   CE   L715                componentWillUnmount 직전 instance.props 덮어쓰기

 죽은 둘을 빼면 함수 컴포넌트에는 안 쓰인다
 ★ 커밋 쪽 셋이 [05]에서 다시 나온다 - "생명주기가 보는 props" 이야기다
```

## 결과가 쓰이는 곳

```text
 반환 instance
      --> BW L1651 이 받고 바로 L1652 mountClassInstance 로 넘어간다
      --> workInProgress.stateNode 에 이미 꽂혀 있다

 workInProgress.memoizedState
      --> 생성자가 정한 초기 state
      --> [03]이 instance.state 와 맞춘다

 instance.updater
      --> this.setState 가 [01]로 간다

 resolveClassComponentProps 의 결과
      --> instance.props 에 들어간다
      --> 비교에는 **쓰지 않는다** ([04])
```

## 다루지 않는 것

`checkClassInstance`(L296-526)가 검사하는 열아홉 가지 중 대표 몇 개만 적었다 — `render` 누락, `getInitialState` / `getDefaultProps` 같은 createClass 잔재, `contextType` 을 인스턴스 속성으로 둔 경우, `componentShouldUpdate` / `componentDidUnmount` / `componentWillRecieveProps` 같은 오타 계열, `isPureReactComponent` 와 `shouldComponentUpdate` 를 함께 정의한 경우(L416-427 — [04]의 우선순위 규칙과 짝이다), `super(props)` 를 안 넘긴 경우, `state` 가 객체가 아닌 경우 — 그 전체 목록과 각 경고문, 어느 것이 `Set` 으로 중복 제거되는지, `fakeInternalInstance`(L65)가 `Object.freeze`(L92) 되어 pre-Fiber 내부 접근을 잡는 방식, `ReactStrictModeWarnings` 가 경고를 모아 두었다가 커밋 때 쏟는 구조, `getInstance` / `setInstance`(`ReactFiberTreeReflection`)의 저장 위치, `emptyContextObject` 의 정체, 플래그를 끄지 않은 포크에서 `getMaskedContext` / `cacheContext` 가 실제로 하는 일은 같은 뼈대의 곁가지라 요약만 했다.
