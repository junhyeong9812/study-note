# 읽기와 비교

상위: [컨텍스트 흐름](../README.md)

소비자가 **읽으면서 값을 적어 두고**, 다음 렌더에 **그것과 비교해** 바뀌었는지 스스로 판정한다.

## 위치

읽기 `packages/react-reconciler` / `src` / `ReactFiberNewContext.js` L580-L627 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberNewContext.js#L580-L627))

비교 `packages/react-reconciler` / `src` / `ReactFiberNewContext.js` L515-L537 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberNewContext.js#L515-L537))

조상에 칠하기 `packages/react-reconciler` / `src` / `ReactFiberNewContext.js` L155-L195 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberNewContext.js#L155-L195))

## 실제 코드

읽으면서 값을 적어 둔다. 그리고 첫 의존이면 스스로 표시한다.

```js
// ReactFiberNewContext.js L589-L593
  const contextItem = {
    context: context as any as ReactContext<mixed>,
    memoizedValue: value,
    next: null,
  };
```

```js
// ReactFiberNewContext.js L605-L620
    // This is the first dependency for this component. Create a new list.
    // $FlowFixMe[incompatible-type]
    lastContextDependency = contextItem;
    consumer.dependencies = __DEV__
      ? // $FlowFixMe[incompatible-type]
        {
          lanes: NoLanes,
          firstContext: contextItem,
          _debugThenableState: null,
        }
      : // $FlowFixMe[incompatible-type]
        {
          lanes: NoLanes,
          firstContext: contextItem,
        };
    consumer.flags |= NeedsPropagation;
```

비교는 그 적어 둔 값과 한다.

```js
// ReactFiberNewContext.js L523-L536
  let dependency = currentDependencies.firstContext;
  while (dependency !== null) {
    const context = dependency.context;
    // $FlowFixMe[constant-condition]
    const newValue = isPrimaryRenderer
      ? context._currentValue
      : context._currentValue2;
    const oldValue = dependency.memoizedValue;
    if (!is(newValue, oldValue)) {
      return true;
    }
    dependency = dependency.next;
  }
  return false;
```

> This **only** gets called if props and state has already bailed out, so it's a **relatively uncommon** path, except at the root of a changed subtree. Alternatively, we could move these comparisons into `readContext`, but that's a much hotter path, so **I think** this is an appropriate trade off.

## 동작 흐름

```text
 [읽기] readContextForConsumer  L580-627

 L585  value = isPrimaryRenderer ? context._currentValue : context._currentValue2
 L589  contextItem = { context, memoizedValue: value, next: null }
        ★ **읽은 값을 그 자리에 적어 둔다**

 L595  lastContextDependency === null 이면  (이번 렌더의 첫 의존이다)
 L596    consumer === null 이면
 L597      => throw 'Context can only be read while React is rendering. ...'
 L607    lastContextDependency = contextItem
 L608    consumer.dependencies = { lanes: NoLanes, firstContext: contextItem }
 L620    consumer.flags |= NeedsPropagation
          ★ 저장소 전체에서 이 플래그를 세우는 **유일한 자리**다
 L621  아니면 (두 번째 이후)
 L624    lastContextDependency = lastContextDependency.next = contextItem
 L626  => return value
```

```text
 [비교] checkIfContextChanged  L515-537

 L523  dependency = currentDependencies.firstContext
 L524  while (dependency !== null)
 L527    newValue = isPrimaryRenderer ? context._currentValue : ._currentValue2
 L530    oldValue = dependency.memoizedValue        ** 적어 둔 값이다 **
 L531    !is(newValue, oldValue) 이면
 L532      => return true
 L534    dependency = dependency.next
 L536  => return false
```

```text
 [칠하기] scheduleContextWorkOnParentPath  L155-195

 L161  node = parent
 L162  while (node !== null)
 L164    node.childLanes 가 renderLanes 를 포함하지 않으면
 L165      node.childLanes 에 merge
 L166      alternate 가 있으면
 L167        alternate.childLanes 에도 merge
 L169    아니면 alternate 가 있고 그쪽만 모자라면
 L173      alternate 쪽에만 merge
 L174    아니면
          ** 빈 블록이다. 주석만 있다 (L175-180) **
 L182    node === propagationRoot 이면
 L183      break
 L185    node = node.return
 L187  [__DEV__]
 L188    node !== propagationRoot 이면
 L189      console.error('Expected to find the propagation root ...')
```

```text
 ★ 소비자가 스스로 표시한다

 L620  consumer.flags |= NeedsPropagation

 읽은 fiber 자신에게 붙는다. 그리고 그 표시를
 [01] L424 의 위로 가는 루프가 읽는다

 => 전파 알고리즘의 두 축(표시하기/읽기)이 한 파일 안에서 닫힌다
    읽는 쪽이 "나는 컨텍스트에 기대고 있다" 를 남기고
    전파하는 쪽이 그것을 보고 조상의 단축을 끈다
```

```text
 ★ 값을 memoize 하는 것이 비교의 전제다

 L589-593 이 읽은 값을 contextItem.memoizedValue 에 담고
 L530 이 그것을 oldValue 로 쓴다

 그런데 "옛 값" 이 남아 있으려면 리스트가 두 벌이어야 한다
   createWorkInProgress 가 dependencies 를 복제하되
   firstContext 포인터는 current 것을 그대로 복사하고
   prepareToReadContext L546-550 이 **WIP 쪽만** null 로 지운다

 => WIP 는 매 렌더 리스트를 새로 조립하고
    current 는 옛 리스트를 보존한다
    checkIfContextChanged(current.dependencies) 가 성립하는 근거다
```

```text
 ★ 왜 비교를 여기서 하는가

 주석 L518-522 가 트레이드오프를 적는다.
 readContext 로 옮길 수도 있지만 그쪽이 훨씬 뜨거운 경로라
 **"I think" 이쪽이 적절하다**고 적는다 (원문이 추정형이다)

 호출처를 세어 보면 구조가 그 말을 뒷받침한다
   checkIfContextChanged  네 곳. 전부 **바이아웃 판정** 경로다
     BW L3915 checkScheduledUpdateOrContext
     Hooks L722 renderWithHooks 말미
     ClassComponent L1077 / L1129
     넷 다 dependencies !== null 가드가 한 번 더 있다

   readContext  스무 곳 넘는다. 훅 디스패처 테이블만 열여섯이고
     클래스 contextType, 자식 조정 경유까지 더 있다

 => 읽기는 소비자마다 매 렌더 일어나고
    비교는 props·state 가 이미 바이아웃한 fiber 에서만 일어난다
```

```text
 ★ 조상에 칠할 때 양쪽 트리를 다 본다

 L164-173 이 두 갈래인데 결과적으로
 alternate 가 있는 한 **두 트리 모두** renderLanes 를 포함하게 된다

 셋째 갈래(L174-181)는 빈 블록이고 주석만 있다
   "Neither alternate was updated. Normally, this would mean that the rest
    of the ancestor path already has sufficient priority. However, this is
    not necessarily true inside offscreen or fallback trees because
    childLanes may be inconsistent with the surroundings.
    This is why we continue the loop."

 => 빈 else 가 곧 continue 다. 멈추지 않고 계속 올라간다
    유일한 break 는 propagationRoot 에 닿았을 때다 (L182-183)
```

```text
 렌더 밖에서 읽으면 여기서 던진다

 L596-602
   'Context can only be read while React is rendering.
    In classes, you can read it in the render method or
    getDerivedStateFromProps. In function components, you can read it
    directly in the function body, but not inside Hooks like
    useReducer() or useMemo().'

 조건은 lastContextDependency 와 consumer 가 **둘 다 null** 일 때다.
 그 둘을 함께 null 로 만드는 것이 resetContextDependencies (L60-68)이고,
 [렌더 루프]가 양보 직전에 부른다

 => [훅] 흐름에서 "ContextOnlyDispatcher 에서 readContext 가
    안 던지는데도 실패한다" 고 적은 것의 실제 던지는 자리다
```

## 결과가 쓰이는 곳

```text
 fiber.dependencies
      --> 이번 렌더에서 읽은 컨텍스트 목록
      --> 다음 렌더의 checkIfContextChanged 가 current 쪽을 본다

 NeedsPropagation
      --> [01]의 위로 가는 루프가 읽어 단축을 끈다

 조상의 childLanes
      --> 렌더가 소비자까지 내려오게 한다
      --> 양쪽 alternate 에 칠해야 어느 트리로 렌더하든 통한다

 반환값 (읽기)
      --> useContext 가 돌려주는 값 그 자체다
```

## 다루지 않는 것

`readContext`(L553) / `readContextDuringReconciliation`(L569)의 얇은 래퍼, `prepareToReadContext`(L539)를 부르는 여덟 자리, `isPrimaryRenderer` 가 두 슬롯을 가르는 다중 렌더러 시나리오, `enterDisallowedContextReadInDEV`(L70)와 DEV 경고 경로, `readContextForConsumer` 가 `dependencies` 객체를 갈아끼우며 이전 `lanes` 를 버리는 것, `ContextDependency` 타입의 나머지 칸은 같은 뼈대의 곁가지라 요약만 했다.
