# JSX 가 tag 이 되기까지

상위: [Fiber 라는 자료구조](../README.md)

`<div>` 와 `<Foo/>` 와 `<Suspense>` 가 서로 다른 tag 을 받는 자리. [beginWork] 와 [completeWork] 의 29갈래 switch 가 **전제하는** 것이 여기서 정해진다.

그리고 `Element type is invalid` 라는 그 에러가 만들어지는 곳이기도 하다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiber.js` L561-L751 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiber.js#L561-L751))

## 실제 코드

기본값은 함수 컴포넌트다. 거기서부터 좁혀 간다.

```js
// ReactFiber.js L569-L571
  let fiberTag: WorkTag = FunctionComponent;
  // The resolved type is set if we know what the final type will be. I.e. it's not lazy.
  let resolvedType = type;
```

문자열이면 호스트인데, 플래그에 따라 셋으로 갈린다.

```js
// ReactFiber.js L583-L604
  } else if (typeof type === 'string') {
    // $FlowFixMe[constant-condition]
    if (supportsResources && supportsSingletons) {
      const hostContext = getHostContext();
      fiberTag = isHostHoistableType(type, pendingProps, hostContext)
        ? HostHoistable
        : isHostSingletonType(type)
          ? HostSingleton
          : HostComponent;
      // $FlowFixMe[constant-condition]
    } else if (supportsResources) {
      const hostContext = getHostContext();
      fiberTag = isHostHoistableType(type, pendingProps, hostContext)
        ? HostHoistable
        : HostComponent;
      // $FlowFixMe[constant-condition]
    } else if (supportsSingletons) {
      fiberTag = isHostSingletonType(type) ? HostSingleton : HostComponent;
    } else {
      fiberTag = HostComponent;
    }
  } else {
```

클래스와 함수를 가르는 것은 한 줄이다.

```js
// ReactFiber.js L303-L310
const createFiber = enableObjectFiber
  ? createFiberImplObject
  : createFiberImplClass;

function shouldConstruct(Component: Function) {
  const prototype = Component.prototype;
  return !!(prototype && prototype.isReactComponent);
}
```

마지막에 fiber 를 만든다.

```js
// ReactFiber.js L741-L750
  const fiber = createFiber(fiberTag, pendingProps, key, mode);
  fiber.elementType = type;
  fiber.type = resolvedType;
  fiber.lanes = lanes;

  if (__DEV__) {
    fiber._debugOwner = owner;
  }

  return fiber;
```

## 동작 흐름

```text
 createFiberFromTypeAndProps  FIBER L561-751

 L569  fiberTag = FunctionComponent            ★ **기본값이 함수 컴포넌트다**
 L570  주석 - "The resolved type is set if we know what the final type will be.
               I.e. it's not lazy."
 L571  resolvedType = type

 --- 함수인가 ---
 L572  typeof type === 'function' 이면
 L573    shouldConstruct(type) 이면
 L574      fiberTag = ClassComponent
 L578    아니면 (FunctionComponent 그대로 둔다)

 --- 문자열인가 ---
 L583  typeof type === 'string' 이면
 L585    [FLAG] supportsResources && supportsSingletons 이면   (react-dom 이 여기다)
 L586      hostContext = getHostContext()
 L587      fiberTag = isHostHoistableType(type, pendingProps, hostContext)
 L588        ? HostHoistable
 L589        : isHostSingletonType(type)
 L590          ? HostSingleton
 L591          : HostComponent
 L593    (플래그가 하나만 켜진 갈래 둘, 둘 다 꺼진 갈래 하나가 더 있다)

 --- 그 밖 ---
 L605  getTag: switch (type)                   ★ **레이블 붙은 switch**
 L607    REACT_ACTIVITY_TYPE
 L610    REACT_FRAGMENT_TYPE
 L613    REACT_STRICT_MODE_TYPE
 L614      fiberTag = Mode
 L615      mode |= StrictLegacyMode
 L616      disableLegacyMode 이거나 이미 ConcurrentMode 이면
 L618        mode |= StrictEffectsMode      ★ 아래로 떨어지는 case 중 유일하게
                                             mode 를 건드린다
 L622    REACT_PROFILER_TYPE
 L625    REACT_SUSPENSE_TYPE
 L628    REACT_SUSPENSE_LIST_TYPE
 L631    REACT_LEGACY_HIDDEN_TYPE      [FLAG:enableLegacyHidden=false]
 L636    REACT_VIEW_TRANSITION_TYPE    [FLAG:enableViewTransition=true]
 L641    REACT_SCOPE_TYPE              [FLAG:enableScopeAPI=false]
 L646    REACT_TRACING_MARKER_TYPE     [FLAG:enableTransitionTracing=false]
          ★ 이 넷은 **fall-through 사슬**이다. 아래에 따로 적는다
 L651    default
 L653      typeof type === 'object' 이고 null 이 아니면   (default 레이블은 L651)
 L654        switch (type.$$typeof)
 L656          REACT_CONTEXT_TYPE     -> L657 ContextProvider ; L658 break getTag
 L660          REACT_CONSUMER_TYPE    -> L661 ContextConsumer ; L662 break getTag
 L665          REACT_FORWARD_REF_TYPE -> L666 ForwardRef      ; L670 break getTag
 L672          REACT_MEMO_TYPE        -> L673 MemoComponent   ; L674 break getTag
 L676          REACT_LAZY_TYPE        -> L677 LazyComponent
 L678                                    resolvedType = null  ★ 여기만 null 로
 L679                                    break getTag

 --- 못 알아보면 ---
 L730      fiberTag = Throw
 L731      pendingProps = new Error(...)
 L736      resolvedType = null

 --- 만든다 ---
 L741  fiber = createFiber(fiberTag, pendingProps, key, mode)
 L742  fiber.elementType = type                ★ 원본을 담는다
 L743  fiber.type = resolvedType               ★ 해소된 것을 담는다
 L744  fiber.lanes = lanes
 L750  => return fiber
```

```text
 ★★ 기본값이 FunctionComponent 다

 L569 에서 그렇게 두고, 함수이면서 shouldConstruct 가 아니면 **그대로 둔다**.
 => 함수 컴포넌트는 "따로 판정하지 않는" 것이다
```

```text
 ★★ 클래스와 함수를 가르는 것이 세 줄이다

 FIBER L307-310
   function shouldConstruct(Component: Function) {
     const prototype = Component.prototype;
     return !!(prototype && prototype.isReactComponent);
   }

 => React.Component 를 상속했는지만 본다.
    `isReactComponent` 라는 표식이 프로토타입에 있는지가 전부다

 ★ 다만 판정이 하나 더 있다 - isSimpleFunctionComponent(L312-318)는
   `!shouldConstruct(type) && type.defaultProps === undefined` 까지 본다
   (SimpleMemoComponent 를 고를 때 쓴다)
 => 화살표 함수는 prototype 이 없어 자동으로 함수 컴포넌트가 된다
    (마지막 줄은 내 귀결이고 주석에 없다)
```

```text
 ★ 문자열 태그가 셋으로 갈린다  L585-591

 HostHoistable   isHostHoistableType  <link> <meta> <title> 처럼 <head> 로 올릴 것
 HostSingleton   isHostSingletonType  <html> <head> <body>
 HostComponent   그 밖

 [FLAG:supportsResources=true] [FLAG:supportsSingletons=true] 라
 react-dom 은 셋을 다 쓴다.
 나머지 갈래 셋(L593 이하)은 다른 렌더러용이다
 ※ isHostHoistableType / isHostSingletonType 의 본문은 안 읽었다
```

```text
 ★★ 레이블 붙은 switch 다

 L605  getTag: switch (type) {
 L658 / L662 / L670 / L674 / L679  break getTag;

 안쪽 `switch (type.$$typeof)`(L654)에서 **바깥 switch 를** 빠져나가려고 쓴다.
 `break` 만 쓰면 안쪽 switch 만 끊긴다

 ★ 이 지도가 지금까지 만난 레이블 구문의 세 번째다
     [DOM 조작]  getHostSibling 의 `siblings:`
     [컨텍스트 전파]  `findChangedDep:`
     여기  `getTag:`
   다만 저장소 전체로는 열셋이다 (work loop 의 `outer:` / `resumeOrUnwind:`,
   커밋의 `findParent:`, 이벤트의 `mainLoop:` 등)
   ※ 열셋은 내가 전수 grep 으로 센 것이다
```

```text
 ★★★ Element type is invalid 가 여기서 만들어진다

 L730  fiberTag = Throw
 L731  pendingProps = new Error(
         'Element type is invalid: expected a string (for built-in components)
          or a class/function (for composite components) but got:
          ${typeString}.${info}')
 L736  resolvedType = null

 => 에러를 **던지지 않고 Throw fiber 의 pendingProps 에 담는다**

 그리고 [beginWork]가 그것을 되던진다
   BW L4462  case Throw: {
   BW L4463-4464  주석 - "This represents a Component that threw in the
     reconciliation phase. So we'll rethrow here. This might be a Thenable."
   BW L4465  throw workInProgress.pendingProps;

 => 최상위 인덱스가 "case Throw 가 되던짐" 이라고만 적었던 것의 한 갈래다.
    센티널이 아니라 **담아 둔 진짜 에러**다

 ★ 다만 Throw fiber 를 만드는 곳이 여기뿐은 아니다.
   createFiberFromThrow(FIBER L971)가 따로 있고
   [자식 조정](../../reconcile-children/README.md)의 ReactChildFiber L2075 가 그것을 쓴다
 => 렌더 단계까지 미루는 이유는 그 위치에서 컴포넌트 스택을 붙이려는 것으로 보인다
    ※ 마지막 줄은 내 추측이다. 주석에 없다
```

```text
 ★★★ 이 switch 는 나란한 목록이 아니라 **fall-through 사슬**이다

 L631  case REACT_LEGACY_HIDDEN_TYPE:
 L632    if (enableLegacyHidden) { return createFiberFromLegacyHidden(...) }
 L635  // $FlowFixMe[invalid-compare] -- falls through
 L636  case REACT_VIEW_TRANSITION_TYPE:
 L637    if (enableViewTransition) { return createFiberFromViewTransition(...) }
 L640  // falls through
 L641  case REACT_SCOPE_TYPE:
 L642    if (enableScopeAPI) { ... }
 L645  // falls through
 L646  case REACT_TRACING_MARKER_TYPE:
 L647    if (enableTransitionTracing) { ... }
 L650  // Fall through
 L651  default: { ... }

 플래그 실제 값을 넣어 보면 결과가 뜻밖이다
   enableLegacyHidden      = false   (FLAGS L109)
   enableViewTransition    = true    (FLAGS L81)
   enableScopeAPI          = false   (FLAGS L53)
   enableTransitionTracing = false   (FLAGS L106)

 => `<LegacyHidden>` 은 자기 case 를 통과해 **ViewTransition fiber 가 된다**
 => `<Scope>` 와 `<TracingMarker>` 는 default 까지 떨어져 **Throw fiber 가 된다**
    ("Element type is invalid" 를 받는다)

 ★ 플래그가 꺼진 기능을 "없는 것" 으로 만드는 방식인데,
   떨어지는 곳이 하필 다음 case 라 LegacyHidden 만 엉뚱한 곳에 닿는다
   ※ 마지막 문장은 내 관찰이다. 주석은 falls through 만 적는다
```

```text
 ★ 이 switch 의 case 아홉은 아래까지 안 내려온다

 L608 / L611 / L623 / L626 / L629 / L633 / L638 / L643 / L648 이
 각각 createFiberFromX 를 **return** 한다

 => L741-750 의 공통 마무리(elementType / type / lanes 대입)를 안 거친다
 => 그래서 fiber.elementType 이 언제나 채워지는 것은 아니다
    createFiberFromFragment(L781-790)와 createFiberFromOffscreen(L859-868)은
    본문이 세 줄인데 createFiber / lanes / return 뿐이다.
    elementType 을 **아예 안 세운다** (null 로 남는다)
```

```text
 ★ DEV 가 가장 흔한 원인을 짚어 준다

 L685-691  type 이 undefined 이거나 **빈 객체**이면
 L693-694    info += ' You likely forgot to export your component from the file
              it's defined in, or you might have mixed up default and named
              imports.'

 => import 실수가 이 에러의 대표 원인이라고 코드가 인정하는 셈이다
    (마지막 줄은 내 해석이다)
```

```text
 ★ elementType 과 type 이 갈리는 자리

 L742  fiber.elementType = type          원본 (memo/lazy 로 감싼 것 그대로)
 L743  fiber.type = resolvedType         해소된 것

 lazy 만 resolvedType 을 null 로 둔다 (L678).
 아직 무엇인지 모르기 때문이다
 주석 L570 - "The resolved type is set if we know what the final type will be.
              I.e. it's not lazy."

 => [자식 조정]이 재사용을 판정할 때 **elementType** 을 보는 이유가 이것이다.
    감싼 것이 같아야 같은 컴포넌트다
    (마지막 줄은 내가 흐름 11 과 맞춰 본 것이다)
```

## 결과가 쓰이는 곳

```text
 fiber.tag
      --> [beginWork] L4283 의 29갈래
      --> [completeWork] L1091 의 29갈래
      --> [에러와 Suspense]의 UnwindWork switch

 fiber.elementType
      --> [자식 조정]의 재사용 판정

 fiber.type
      --> 실제로 부를 함수/클래스. lazy 면 나중에 채워진다

 Throw fiber 의 pendingProps
      --> [beginWork] L4465 가 되던진다
```

## 다루지 않는 것

`isHostHoistableType` / `isHostSingletonType`(호스트 설정)이 어떤 태그를 골라내는지, `REACT_*_TYPE` 심볼들(`shared/ReactSymbols`)과 각 tag 의 의미([beginWork](../../begin-work/spi/README.md)의 표에 있다), `createFiberFromX` 열다섯(FIBER L753-979) 각각이 `pendingProps` 와 `mode` 를 다루는 방식, DEV 가 `typeString` 을 만드는 분기(L697-729)와 `_debugOwner` 를 붙이는 자리, `createFiberFromElement`(L753)가 `element.key` 와 `_debugInfo` 를 옮기는 경로, lazy 가 해소된 뒤 tag 이 바뀌는 자리([beginWork]의 `mountLazyComponent`), `enableObjectFiber` 가 꺼져 있어 죽은 `createFiberImplObject`(L236)는 이 문서의 범위 밖이다.
