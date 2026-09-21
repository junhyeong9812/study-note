# 쌍둥이 둘

상위: [클래스 컴포넌트](../README.md)

`resumeMountClassInstance` 와 `updateClassInstance` 는 뼈대가 같고 꼬리는 글자까지 같다. 그런데 **차이가 열셋**이고, 그중 몇은 동작이 갈린다.

## 위치

이어서 마운트 `packages/react-reconciler` / `src` / `ReactFiberClassComponent.js` L852-L1001 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassComponent.js#L852-L1001))

업데이트 `packages/react-reconciler` / `src` / `ReactFiberClassComponent.js` L1004-L1185 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassComponent.js#L1004-L1185))

## 실제 코드

비교에 쓰는 props 와 인스턴스에 넣는 props 가 다르다. 그 이유를 주석이 적는다.

```js
// ReactFiberClassComponent.js L883-L892
  // When comparing whether props changed, we should compare using the
  // unresolved props object that is stored on the fiber, rather than the
  // one that gets assigned to the instance, because that object may have been
  // cloned to resolve default props and/or remove `ref`.
  const unresolvedNewProps = workInProgress.pendingProps;
  const didReceiveNewProps = unresolvedNewProps !== unresolvedOldProps;

  // Note: During these life-cycles, instance.props/instance.state are what
  // ever the previously attempted to render - not the "current". However,
  // during componentDidUpdate we pass the "current" props.
```

> When comparing whether props changed, we should compare using the unresolved props object that is stored on the fiber, rather than the one that gets assigned to the instance, because that object may have been cloned to resolve default props and/or remove `ref`.

> Note: During these life-cycles, instance.props/instance.state are what ever the previously attempted to render - not the "current". However, during componentDidUpdate we pass the "current" props.

조기 바이아웃. 두 함수가 여기서 가장 크게 갈린다.

```js
// ReactFiberClassComponent.js L918-L933
  if (
    !didReceiveNewProps &&
    oldState === newState &&
    !hasContextChanged() &&
    !checkHasForceUpdateAfterProcessing()
  ) {
    // If an update was already in progress, we should schedule an Update
    // effect even though we're bailing out, so that cWU/cDU are called.
    if (typeof instance.componentDidMount === 'function') {
      workInProgress.flags |= Update | LayoutStatic;
    }
    if (__DEV__ && (workInProgress.mode & StrictEffectsMode) !== NoMode) {
      workInProgress.flags |= MountLayoutDev;
    }
    return false;
  }
```

```js
// ReactFiberClassComponent.js L1067-L1099
  if (
    unresolvedOldProps === unresolvedNewProps &&
    oldState === newState &&
    !hasContextChanged() &&
    !checkHasForceUpdateAfterProcessing() &&
    !(
      // prettier-ignore
      // $FlowFixMe[invalid-compare]
      (current !== null &&
        current.dependencies !== null &&
        checkIfContextChanged(current.dependencies))
    )
  ) {
    // If an update was already in progress, we should schedule an Update
    // effect even though we're bailing out, so that cWU/cDU are called.
    if (typeof instance.componentDidUpdate === 'function') {
      if (
        unresolvedOldProps !== current.memoizedProps ||
        oldState !== current.memoizedState
      ) {
        workInProgress.flags |= Update;
      }
    }
    if (typeof instance.getSnapshotBeforeUpdate === 'function') {
      if (
        unresolvedOldProps !== current.memoizedProps ||
        oldState !== current.memoizedState
      ) {
        workInProgress.flags |= Snapshot;
      }
    }
    return false;
  }
```

> TODO: In some cases, we'll end up checking if context has changed twice, both before and after `shouldComponentUpdate` has been called. Not ideal, but I'm loath to refactor this function. **This only happens for memoized components so it's not that common.**

꼬리는 글자까지 같다.

```js
// ReactFiberClassComponent.js L994-L998
  // Update the existing instance's state, props, and context pointers even
  // if shouldComponentUpdate returns false.
  instance.props = newProps;
  instance.state = newState;
  instance.context = nextContext;
```

> Update the existing instance's state, props, and context pointers even if shouldComponentUpdate returns false.

## 동작 흐름

```text
 뼈대가 같다 (왼쪽 resume / 오른쪽 update)

  1  옛 props 를 resolve 해 instance.props 에      L861-862   / L1016-1017
  2  nextContext 를 구한다                         L865-876   / L1021-1028
  3  hasNewLifecycles 판정                          L879-881   / L1031-1033
  4  willReceiveProps 를 조건부로 부른다            L896-909   / L1041-1057
  5  resetHasForceUpdateBeforeProcessing            L911       / L1059
     instance.state = oldState                      L914       / L1062
     processUpdateQueue                             L915       / L1063
  6  ★ 조기 바이아웃 판정                           L918-933   / L1067-1099
  7  getDerivedStateFromProps 적용                   L935-943   / L1101-1109
  8  shouldUpdate 판정                               L945-955   / L1111-1129
  9  생명주기 + 플래그 / 아니면 memoized 갱신        L957-992   / L1131-1176
 10  instance 세 칸 갱신하고 반환                    L994-1000  / L1178-1184
```

```text
 ★ 차이 열셋

 D1  update 만 cloneUpdateQueue 를 부른다            L1013
     resume 은 current 가 없으니 복제할 것이 없다

 D2  update 의 `current: Fiber` 가 **non-nullable** 타입이다  L1005
     그래서 L1075 / L1127 의 `current !== null` 가드가 죽었다
     L1073-1074 에 `// prettier-ignore` 와 `// $FlowFixMe[invalid-compare]` 가 붙어 있다
     ★ [업데이트 큐]에서 죽은 가지 둘을 찾을 때 본 그 지문이다

 D3  props 비교 방식
       resume  L888  didReceiveNewProps 를 변수로 한 번 계산
       update  L1047 / L1068  두 번 인라인. 게다가 부등호 방향이 반대다

 D4  조기 바이아웃 조건
       둘 다 hasContextChanged() 를 갖는다 (L921 / L1070)
         ★ 그런데 그것은 [DEAD] 라 **상수 거짓 항**이다
       update 만 **두 번째** 컨텍스트 항을 갖는다 (L1072-1078)
         checkIfContextChanged(current.dependencies)

 D5  shouldUpdate 계산에도 update 만 컨텍스트 항을 또 OR 한다   L1127-1129
     TODO L1122-1125 가 "두 번 검사한다" 를 인정한다

 D6  생명주기 계열
       resume  componentWillMount    L965-970
       update  componentWillUpdate   L1139-1144

 D7  ★ 인자가 다르다
       resume  L966  instance.componentWillMount()          인자 없음
       update  L1140 instance.componentWillUpdate(newProps, newState, nextContext)

 D8  ★★ resume 의 cWM 은 **인라인**이다. callComponentWillMount 헬퍼를 안 거친다
       => this.state 직접 대입을 못 잡는다 ([01]에 있다)

 D9  ★ resume 은 cWM 뒤에 processUpdateQueue 를 **안 부른다**
       [03] mountClassInstance L839 는 부른다. 같은 생명주기인데 다르다

 D10 ★★ 플래그 어휘가 서로 겹치지 않는다
       resume  Update | LayoutStatic / MountLayoutDev       Snapshot 은 없다
       update  Update / Snapshot                            LayoutStatic 은 없다
     => 이어서 마운트하는 길에서는 getSnapshotBeforeUpdate 가 **예약되지 않는다**

 D11 바이아웃 갈래의 플래그 구조
       resume  componentDidMount 면 Update|LayoutStatic          L926-928
       update  componentDidUpdate 면 Update                      L1082-1089
               **그리고** getSnapshotBeforeUpdate 면 Snapshot    L1090-1097
               둘 다 current 와 비교하는 가드가 한 겹 더 있다     L1084-1085

 D12 지역 변수 이름만 다른 것 하나
       L870 nextLegacyUnmaskedContext / L1026 nextUnmaskedContext

 D13 꼬리 L994-1000 과 L1178-1184 는 **글자까지 같다**
```

```text
 ★★ 조기 바이아웃이 getDerivedStateFromProps 앞에 있다

 L932  return false      <- L935 의 gDSFP 보다 먼저다
 L1098 return false      <- L1101 의 gDSFP 보다 먼저다

 => 바이아웃한 렌더에서는 getDerivedStateFromProps 가 **안 불린다**
    "매 렌더 불린다" 는 통념이 여기서 깨진다
```

```text
 ★ 바이아웃하면서도 플래그는 세운다

 같은 주석이 네 번 나온다
   L924-925   resume 조기 바이아웃
   L979-980   resume shouldUpdate 거짓
   L1080-1081 update 조기 바이아웃
   L1153-1154 update shouldUpdate 거짓

   "If an update was already in progress, we should schedule an Update effect
    even though we're bailing out, so that cWU/cDU are called."

 즉 "이 렌더는 건너뛰지만 앞선 렌더가 걸어 둔 생명주기는 불러야 한다"
```

```text
 ★ shouldUpdate 가 거짓이어도 두 가지를 갱신한다

 fiber 쪽    L990-991  /  L1174-1175
 instance 쪽 L996-998  /  L1180-1182

 ★ 그런데 같은 뜻의 주석이 **한 단어 다르다**
   L988-989   (resume)  "... we should still update the
                         **memoized state** to indicate that this work can be reused."
   L1172-1173 (update)  "... we should still update the
                         **memoized props/state** to indicate that this work can be reused."

 코드는 둘 다 props 와 state 를 대입한다.
 resume 쪽 주석이 자기 코드보다 좁게 말한다
```

```text
 ★ instance.state 를 쓰는 자리가 둘이다

 L914 / L1062  let newState = (instance.state = oldState)
                 -> processUpdateQueue 보다 **먼저** 맞춘다
 L997 / L1181  instance.state = newState
                 -> 마지막에 결과로 맞춘다

 앞엣것이 왜 필요한지는 주석에 없다
```

```text
 checkShouldComponentUpdate  L245-294 — 세 갈래

 L255  instance.shouldComponentUpdate 가 함수이면
 L256    shouldUpdate = instance.shouldComponentUpdate(newProps, newState, nextContext)
 L262    [__DEV__] StrictLegacyMode 이면
 L266      shouldUpdate = instance.shouldComponentUpdate(...)   ★ 두 번째를 쓴다
 L275    [__DEV__] shouldUpdate === undefined 이면
 L276      console.error('%s.shouldComponentUpdate(): Returned undefined
                          instead of a boolean value. ...')
 L284    => return shouldUpdate

 L287  ctor.prototype && ctor.prototype.isPureReactComponent 이면
 L289    => return !shallowEqual(oldProps, newProps)
              || !shallowEqual(oldState, newState)

 L293  => return true

 ★ PureComponent 는 props 와 state 를 **둘 다** 얕게 비교한다
 ★ shouldComponentUpdate 가 있으면 PureComponent 여도 그쪽이 이긴다 (L255 가 먼저다)
   DEV 가 그 조합을 경고한다 (checkClassInstance L416-427)
 ★ 그리고 shouldUpdate 앞에 checkHasForceUpdateAfterProcessing() 이 OR 로 붙어 있어
   (L946 / L1112) forceUpdate() 는 이 함수를 아예 건너뛴다
```

```text
 ★ 비교에 쓰는 props 가 instance 의 것과 다르다

 L861  oldProps = resolveClassComponentProps(ctor, unresolvedOldProps)
 L862  instance.props = oldProps                  <- resolve 한 것
 L888  didReceiveNewProps = unresolvedNewProps !== unresolvedOldProps
                                                  <- resolve 안 한 것

 resolve 는 ref 를 빼거나 defaultProps 를 채울 때 **새 객체**를 만든다 ([02]).
 그러면 === 비교가 늘 거짓이 되어 바이아웃이 영영 안 일어난다.
 주석 L883-886 이 그것을 적는다

 ★ 그리고 이 주석의 짝이 커밋 쪽에 있다 (주석 L890-892)
   생명주기가 보는 instance.props 는 "직전에 렌더하려던 것" 이고,
   componentDidUpdate 에는 "current" props 를 따로 만들어 넘긴다 -> [05]
```

## 결과가 쓰이는 곳

```text
 반환 shouldUpdate
      --> [05] finishClassComponent 이 바이아웃할지 정한다

 Update / Snapshot / LayoutStatic
      --> 커밋이 어떤 생명주기를 부를지 정한다
      --> 바이아웃해도 세워질 수 있다

 instance.props / state / context
      --> render() 안에서 보는 this 의 세 칸
      --> shouldUpdate 와 무관하게 늘 갱신된다

 workInProgress.memoizedProps / memoizedState
      --> 바이아웃 갈래에서도 갱신해야 다음 렌더가 재사용할 수 있다
```

## 다루지 않는 것

`hasContextChanged`(`ReactFiberLegacyContext.js` L113 — `disableLegacyContext` 때문에 늘 `false` 다)가 플래그를 끄지 않은 포크에서 하는 일, `checkIfContextChanged`(`ReactFiberNewContext.js` L515 — [컨텍스트 전파 03](../../context/03_readAndCheck/README.md)에 있다)의 본문, `shallowEqual`(`shared/shallowEqual`)의 비교 규칙, `resetHasForceUpdateBeforeProcessing` / `checkHasForceUpdateAfterProcessing`([업데이트 큐 01](../../update-queue/01_queueShape/README.md)에 있다), `suspendIfUpdateReadFromEntangledAsyncAction`(L916 / L1064)이 던지는 thenable 의 행선지, `StrictEffectsMode` 와 `MountLayoutDev`, `callComponentWillReceiveProps`(L728)의 본문([01 업데이터](../01_updater/README.md)에 있다)은 같은 뼈대의 곁가지라 요약만 했다.
