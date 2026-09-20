# 훅

[beginWork](../begin-work/README.md)가 함수 컴포넌트를 평가할 때 지나는 길이다. **`useState` 가 어느 fiber 의 것인지 아는 방법**과 **훅이 순서로 짝지어지는 이유**가 여기 있다.

이 흐름의 핵심은 셋이다. **전역 변수 몇 개가 "지금 누구를 렌더 중인가" 를 들고 있고**, **`ReactSharedInternals.H` 를 갈아끼워 같은 `useState` 가 다른 함수가 되며**, **훅 개수가 어긋나는 것을 양쪽에서 잡는데 한 구멍이 있다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberHooks.js` 기준이다.

## 전체 그림

```text
 [01] renderWithHooks                              L502-631
      +-- renderLanes / currentlyRenderingFiber 를 세운다   L510-511
      +-- workInProgress.memoizedState = null              L526  훅 리스트를 비운다
      +-- ReactSharedInternals.H 를 갈아끼운다              L560-563
      |     current 가 없거나 memoizedState 가 없으면 OnMount
      |     아니면 OnUpdate
      +-- Component(props, secondArg)                      L598  ** 사용자 함수 **
      +-- 렌더 중 setState 가 있었으면 [02]                 L602-611
      +-- [FLAG:__DEV__] StrictMode 이중 호출도 [02]        L613-626
      +-- [03] finishRenderingHooks                        L628
      +-- => return children                               L630

 [02] renderWithHooksAgain                         L787-853
      +-- do { ... } while (렌더 중 setState 가 또 있으면)
      +-- 25회를 넘으면 => throw 'Too many re-renders.'     L818
      +-- ReactSharedInternals.H = OnRerender              L844-846

 [03] finishRenderingHooks                         L633-749
      +-- ReactSharedInternals.H = ContextOnlyDispatcher   L656  되돌린다
      +-- 훅이 모자라면 => throw                            L704
      +-- 컨텍스트가 바뀌었으면 markWorkInProgressReceivedUpdate  L724

 [04] 훅 리스트                                     L979 / L1000
      +-- 연결 리스트이고 머리가 fiber.memoizedState 다
      +-- 훅이 이전보다 많으면 => throw                     L1044
```

1. [renderWithHooks](01_renderWithHooks/README.md)가 전역을 세우고 디스패처를 고른다.
2. [renderWithHooksAgain](02_renderWithHooksAgain/README.md)이 세 가지 이유로 다시 돌린다.
3. [훅 리스트](03_hookList/README.md)가 순서로 훅을 짝짓는다.
4. [dispatchSetState](04_dispatchSetState/README.md)가 갱신을 큐에 넣거나 넣지 않는다.

```text
 훅이 "지금 누구의 것인지" 아는 방법

 모듈 전역 둘이 그것을 들고 있다
   L258  renderLanes
   L261  currentlyRenderingFiber

 그리고 리스트 위치를 둘이 더 잡는다
   L267  currentHook          이전 트리에서 읽고 있는 자리
   L268  workInProgressHook   지금 트리에서 쓰고 있는 자리

 renderWithHooks L510-511 이 앞의 둘을 세우고
 finishRenderingHooks L663-664 가 지운다

 => useState 가 인자로 fiber 를 받지 않아도 되는 이유다
    사용자 함수를 부르기 직전에 전역에 꽂아 두고
    끝나면 뽑는다
```

```text
 디스패처를 갈아끼운다

 ReactSharedInternals.H 가 훅 구현체 묶음을 가리킨다
 useState 는 그것을 찾아 부르는 얇은 함수일 뿐이다

 운영 빌드에 넷이 있고 각 24항목이다
   ContextOnlyDispatcher      L3874   렌더 밖 / 컴포넌트 본문 밖
   HooksDispatcherOnMount     L3902   최초
   HooksDispatcherOnUpdate    L3930   갱신
   HooksDispatcherOnRerender  L3958   렌더 중 setState 재실행

 => 같은 useState 호출이 mountState 가 되기도 updateState 가 되기도 한다
    "최초인가 갱신인가" 를 훅마다 따지지 않고 묶음째 바꾼다

 자세한 대조표는 [spi](spi/README.md)에 있다
```

```text
 ★ 훅 개수 검사가 비대칭이다

 더 많으면   updateWorkInProgressHook L1044 에서 **그 자리에서** 던진다
             'Rendered more hooks than during the previous render.'

 더 적으면   finishRenderingHooks 가 L660-661 에서 세어 두었다가
             L704 에서 던진다
             'Rendered fewer hooks than expected.'

 조건이 이렇다
   currentHook !== null && currentHook.next !== null

 ★ 그래서 훅을 **하나도** 부르지 않고 일찍 반환하면 걸리지 않는다
   currentHook 이 null 로 남아 첫 항이 거짓이기 때문이다

   그러면 memoizedState 가 L526 에서 null 이 된 채로 커밋되고,
   다음 렌더에서 L561 의 current.memoizedState === null 이 참이 되어
   **마운트 디스패처가 골라지고 훅 상태가 조용히 초기화된다**

   에러가 아니라 조용한 리셋이다
```

```text
 진입점이 셋이다

 renderWithHooks (L502)
   BeginWork L443    updateForwardRef
   BeginWork L1498 / L1508  updateFunctionComponent

 replaySuspendedComponentWithHooks (L751)
   renderWithHooks 를 **건너뛰고** renderWithHooksAgain(L777)을 직접 부른 뒤
   finishRenderingHooks(L783)를 부른다
   ★ 훅 리스트를 비우지 않는다 - 서스펜드 전 상태를 살려서 재사용한다

 renderTransitionAwareHostComponentWithHooks (L855)
   BeginWork L1977, updateHostComponent 안
   함수 컴포넌트가 아닌 **호스트 fiber 가 훅을 쓰는 유일한 자리**다
   form action 때문에 stateful 로 승격된 경우다
```

## 어디로 이어지는가

```text
 [beginWork]    updateFunctionComponent / updateForwardRef 가 이 흐름을 부른다
                didReceiveUpdate 를 올리는 유일한 외부 경로가 여기다
                (markWorkInProgressReceivedUpdate 호출 여섯 자리)

 [스케줄링]     dispatchSetState 가 scheduleUpdateOnFiber 를 부른다
                다만 부르지 않는 갈래가 셋 있다

 [커밋]         useEffect / useLayoutEffect 가 만든 효과 목록을 저쪽이 쓴다
```

## 결과가 쓰이는 곳

```text
 fiber.memoizedState
      --> 훅 연결 리스트의 머리다
      --> 다음 렌더가 이것을 보고 마운트인지 갱신인지 정한다

 fiber.updateQueue
      --> 효과 목록이 여기 붙는다. 커밋이 읽는다

 didReceiveUpdate
      --> [beginWork]가 읽어 바이아웃할지 정한다

 queue.pending / baseQueue / baseState
      --> 다음 렌더의 updateReducerImpl 이 처리한다
      --> lane 이 모자라 건너뛴 갱신이 baseQueue 에 남는다
```

## 다루지 않는 것

`useEffect` / `useLayoutEffect` / `useInsertionEffect` 가 효과 목록을 만드는 과정, `useMemo` / `useCallback` / `useRef` 의 본문, `useTransition` / `useOptimistic` / `useActionState` / `useSyncExternalStore` / `useDeferredValue` 의 구현, `useMemoCache`, DEV 전용 디스패처 일곱 개의 검사, `resetHooksAfterThrow`(L925) 와 `resetHooksOnUnwind`(L939), `bailoutHooks`(L904), 커밋 단계가 효과를 실행하는 규칙은 같은 뼈대의 곁가지라 요약만 했다. 디스패처 대조표와 모듈 전역 목록은 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 renderWithHooks](01_renderWithHooks/README.md)
- [02 renderWithHooksAgain](02_renderWithHooksAgain/README.md)
- [03 훅 리스트](03_hookList/README.md)
- [04 dispatchSetState](04_dispatchSetState/README.md)
- [spi](spi/README.md) — 디스패처 대조표와 모듈 전역
