# renderWithHooksAgain

상위: [훅 흐름](../README.md)

**세 가지 다른 이유가 같은 함수를 쓴다** — 렌더 중 `setState`, StrictMode 이중 호출, 서스펜스 재생.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberHooks.js` L787-L853 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHooks.js#L787-L853))

## 실제 코드

머리 주석이 용도를 밝힌다.

`packages/react-reconciler` / `src` / `ReactFiberHooks.js` L793-L802 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHooks.js#L793-L802))

무한 루프를 막는 한도.

```js
// ReactFiberHooks.js L817-L824
    if (numberOfReRenders >= RE_RENDER_LIMIT) {
      throw new Error(
        'Too many re-renders. React limits the number of renders to prevent ' +
          'an infinite loop.',
      );
    }

    numberOfReRenders += 1;
```

그리고 리스트를 처음부터 다시 훑는다.

```js
// ReactFiberHooks.js L831-L846
    // Start over from the beginning of the list
    currentHook = null;
    workInProgressHook = null;

    if (workInProgress.updateQueue != null) {
      resetFunctionComponentUpdateQueue(workInProgress.updateQueue as any);
    }

    if (__DEV__) {
      // Also validate hook order for cascading updates.
      hookTypesUpdateIndexDev = -1;
    }

    ReactSharedInternals.H = __DEV__
      ? HooksDispatcherOnRerenderInDEV
      : HooksDispatcherOnRerender;
```

## 동작 흐름

```text
 L787  function renderWithHooksAgain(workInProgress, Component, props, secondArg)

 L804  currentlyRenderingFiber = workInProgress
 L806  numberOfReRenders = 0            <- 지역 변수다

 L808  do {
 L809    렌더 중 setState 가 있었으면
 L812      thenableState = null
 L814    thenableIndexCounter = 0
 L815    didScheduleRenderPhaseUpdateDuringThisPass = false

 L817    numberOfReRenders >= RE_RENDER_LIMIT(25) 이면
 L818      => throw 'Too many re-renders. React limits the number of
                     renders to prevent an infinite loop.'

 L824    numberOfReRenders += 1
 L825    [FLAG:__DEV__] ignorePreviousDependencies = false

 L832    currentHook = null
 L833    workInProgressHook = null       <- 리스트를 처음부터 다시 훑는다
           주석 L831 "Start over from the beginning of the list."

 L835    updateQueue 가 있으면 resetFunctionComponentUpdateQueue(...)
 L839    [FLAG:__DEV__] hookTypesUpdateIndexDev = -1

 L844    ReactSharedInternals.H = __DEV__
 L845      ? HooksDispatcherOnRerenderInDEV
 L846      : HooksDispatcherOnRerender

 L850    children = Component(props, secondArg)
           [FLAG:__DEV__] L849 callComponentInDEV

 L851  } while (didScheduleRenderPhaseUpdateDuringThisPass)
 L852  => return children
```

```text
 부르는 곳이 셋이다

 L605  renderWithHooks   렌더 중 setState 가 있었다
 L617  renderWithHooks   StrictMode 이중 호출
 L777  replaySuspendedComponentWithHooks   서스펜드 후 재생

 셋이 목적은 다른데 하는 일이 같다 -
 "훅 리스트를 처음부터 다시 훑으며 컴포넌트를 한 번 더 돌린다"

 다만 들어올 때 상태가 다르다
   L605 경유  didScheduleRenderPhaseUpdateDuringThisPass 가 true 다
              그래서 L809 가 참이 되어 thenableState 를 지운다
   L617 경유  이미 false 라 thenableState 가 보존된다
```

```text
 한도가 지역 변수다

 L806  let numberOfReRenders: number = 0;

 모듈 전역이 아니라 이 함수의 지역 변수다
 그래서 L617 의 StrictMode 이중 호출이 새로 부르면
 카운터가 0부터 다시 센다

 RE_RENDER_LIMIT 은 25 다 (L292)

 검사가 do-while **몸통 머리**에 있어서
 이 함수 안에서 컴포넌트 함수는 최대 25번 불리고
 26번째 진입에서 던진다
 (renderWithHooks L598 의 최초 한 번은 별도다)
```

```text
 검사 순서가 의미를 갖는다

 L815  didScheduleRenderPhaseUpdateDuringThisPass = false
 L817  한도 검사

 리셋이 검사보다 **먼저**다
 그래서 L818 에서 던질 때 그 플래그는 이미 false 다

 그리고 L809 의 조건 읽기는 L815 의 리셋보다 앞이다
 한 바퀴 안에서 읽고 지우는 순서가 정해져 있다
```

```text
 네 번째 디스패처가 여기서만 쓰인다

 HooksDispatcherOnRerender (L3958)

 OnUpdate 와 비교하면 일곱 칸만 다르다
   useReducer / useState / useDeferredValue / useTransition
   / useFormState / useActionState / useOptimistic
 나머지 열일곱 칸은 OnUpdate 와 같은 함수다

 rerender* 계열이 하는 일은 "이미 큐에 넣은 갱신을
 다시 렌더하며 반영" 이다. 자세한 것은 [spi](../spi/README.md)에 있다
```

## 결과가 쓰이는 곳

```text
 children
      --> 부른 쪽이 그대로 돌려준다

 훅 리스트
      --> 매 바퀴 처음부터 다시 훑으므로
          같은 훅 객체가 재사용된다 (updateWorkInProgressHook L1024 갈래)

 didScheduleRenderPhaseUpdateDuringThisPass
      --> 루프를 한 바퀴 더 돌지 정한다
      --> dispatchSetStateInternal 이 렌더 중 갱신에서 세운다
```

## 다루지 않는 것

`resetFunctionComponentUpdateQueue`(L1080), `rerenderReducer` / `rerenderState` 등 rerender 계열 훅의 본문, `thenableState` 와 `trackUsedThenable` 의 promise 재사용, `replaySuspendedComponentWithHooks`(L751)가 이 함수를 부르기 전에 하는 일, `callComponentInDEV` 는 같은 뼈대의 곁가지라 요약만 했다.
