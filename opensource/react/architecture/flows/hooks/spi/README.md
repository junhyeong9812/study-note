# spi

상위: [훅 흐름](../README.md)

이 흐름의 계약은 **`ReactSharedInternals.H`** 하나다. 훅 스물넷을 담은 묶음이고, 렌더 상태에 따라 갈아끼워진다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberHooks.js` 기준이다.

## 디스패처 대조표

운영 빌드에 넷이 있고 **각 24항목**이다. `TIHE` = `throwInvalidHookError`(L442).

| # | 훅 | ContextOnly L3874 | OnMount L3902 | OnUpdate L3930 | OnRerender L3958 |
|---|---|---|---|---|---|
| 1 | readContext | `readContext` | `readContext` | `readContext` | `readContext` |
| 2 | use | `use` | `use` | `use` | `use` |
| 3 | useCallback | TIHE | `mountCallback` | `updateCallback` | `updateCallback` |
| 4 | useContext | TIHE | `readContext` | `readContext` | `readContext` |
| 5 | useEffect | TIHE | `mountEffect` | `updateEffect` | `updateEffect` |
| 6 | useImperativeHandle | TIHE | `mountImperativeHandle` | `updateImperativeHandle` | `updateImperativeHandle` |
| 7 | useLayoutEffect | TIHE | `mountLayoutEffect` | `updateLayoutEffect` | `updateLayoutEffect` |
| 8 | useInsertionEffect | TIHE | `mountInsertionEffect` | `updateInsertionEffect` | `updateInsertionEffect` |
| 9 | useMemo | TIHE | `mountMemo` | `updateMemo` | `updateMemo` |
| 10 | useReducer | TIHE | `mountReducer` | `updateReducer` | **`rerenderReducer`** |
| 11 | useRef | TIHE | `mountRef` | `updateRef` | `updateRef` |
| 12 | useState | TIHE | `mountState` | `updateState` | **`rerenderState`** |
| 13 | useDebugValue | TIHE | `mountDebugValue` | `updateDebugValue` | `updateDebugValue` |
| 14 | useDeferredValue | TIHE | `mountDeferredValue` | `updateDeferredValue` | **`rerenderDeferredValue`** |
| 15 | useTransition | TIHE | `mountTransition` | `updateTransition` | **`rerenderTransition`** |
| 16 | useSyncExternalStore | TIHE | `mountSyncExternalStore` | `updateSyncExternalStore` | `updateSyncExternalStore` |
| 17 | useId | TIHE | `mountId` | `updateId` | `updateId` |
| 18 | useHostTransitionStatus | TIHE | `useHostTransitionStatus` | `useHostTransitionStatus` | `useHostTransitionStatus` |
| 19 | useFormState | TIHE | `mountActionState` | `updateActionState` | **`rerenderActionState`** |
| 20 | useActionState | TIHE | `mountActionState` | `updateActionState` | **`rerenderActionState`** |
| 21 | useOptimistic | TIHE | `mountOptimistic` | `updateOptimistic` | **`rerenderOptimistic`** |
| 22 | useMemoCache | TIHE | `useMemoCache` | `useMemoCache` | `useMemoCache` |
| 23 | useCacheRefresh | TIHE | `mountRefresh` | `updateRefresh` | `updateRefresh` |
| 24 | useEffectEvent | TIHE | `mountEvent` | `updateEvent` | `updateEvent` |

```text
 OnRerender 는 OnUpdate 에서 일곱 칸만 갈아끼운 것이다

 다른 칸  useReducer / useState / useDeferredValue / useTransition
          / useFormState / useActionState / useOptimistic
 같은 칸  나머지 열일곱

 그 일곱은 전부 "큐에 갱신을 넣는" 훅이다
 렌더 중 setState 를 다시 돌릴 때 다르게 처리해야 하는 것들이다
```

```text
 네 디스패처에서 같은 함수인 항목이 둘이다

 L3875 / 3903 / 3931 / 3959   readContext
 L3877 / 3905 / 3933 / 3961   use

 렌더용 셋만 보면 넷이 더 같다
   useContext (= readContext), useHostTransitionStatus,
   useMemoCache, useDebugValue
   (L2897 const updateDebugValue = mountDebugValue 라 이름만 둘이다)

 그리고 키 순서에 함정이 있다
   OnMount 는 useLayoutEffect(3910) -> useInsertionEffect(3911)
   OnUpdate / OnRerender 는 useInsertionEffect -> useLayoutEffect
   순서만 다르고 집합은 같다
```

## ContextOnlyDispatcher — 둘만 던지지 않는다

```js
// ReactFiberHooks.js L3875-L3879
  readContext,

  use,
  useCallback: throwInvalidHookError,
  useContext: throwInvalidHookError,
```

```text
 스물둘이 throwInvalidHookError 다 (L3878-3899)
 던지지 않는 둘은 L3875 readContext 와 L3877 use

 ★ 그렇다고 렌더 밖에서 쓸 수 있다는 뜻은 아니다

 readContext 는 ReactFiberNewContext 의 별도 전역을 보는데
 그것을 resetContextDependencies 가 지운다
 그 함수의 주석이 목적을 밝힌다
   "This is called right before React yields execution, to ensure
    `readContext` cannot be called outside the render phase."
 => 렌더 밖에서 부르면 'Context can only be read while React is
    rendering.' 이 난다. 'Invalid hook call' 이 아니다

 use 는 thenable 상태에 따라 갈린다
   대기 중이면 SuspenseException 이 잡아 줄 루프 없이 새어 나가고
   거부됐으면 그 이유가 던져지고
   이미 풀렸으면 currentlyRenderingFiber 가 null 이라 TypeError 가 난다

 => 방어선은 디스패처가 아니라 한 겹 아래에 있다
    디스패처에서 이 둘을 뺀 이유는 렌더 단계이지만
    컴포넌트 본문 밖인 구간이 있기 때문이다
    (렌더 시작 전에 pushDispatcher 가 ContextOnly 를 깔아 둔다)

 (이 결론은 검증 과정에서 확인된 것이고,
  나는 resetContextDependencies 의 주석까지만 직접 확인했다)
```

## use 가 조건부로 불려도 되는 이유

```text
 use 는 훅 리스트를 쓰지 않는다

 mountWorkInProgressHook 도 updateWorkInProgressHook 도 부르지 않는다
 그래서 workInProgressHook / currentHook 커서를 전진시키지 않는다

 => "더 많다"(L1044) 검사도 "더 적다"(L660) 검사도 건드리지 않는다
    그래서 if 안에서 불러도 된다

 대신 별도의 위치 카운터를 쓴다
   L1097  thenableIndexCounter += 1
   그 index 로 thenableState 에 promise 를 저장·재사용한다

 카운터는 세 곳에서 0 으로 돌아간다
   finishRenderingHooks L700
   renderWithHooksAgain 루프 머리 L814
   resetHooksOnUnwind L975

 그래서 재시도해도 "같은 자리 = 같은 promise" 가 유지된다
 다만 조건부라 index 가 어긋나면 DEV 경고가 나고
 이전 promise 를 재사용한다
```

## 모듈 전역 — 렌더 사이에 남는 것

| 전역 | 선언 | 세우는 곳 | 지우는 곳 |
|---|---|---|---|
| `renderLanes` | L258 | L510 | L663, L960 — **`resetHooksAfterThrow` 는 안 지운다** |
| `currentlyRenderingFiber` | L261 | L511, L804 | L664, L932, L961 |
| `currentHook` | L267 | L1029, L1048 | L666, L832, L963 |
| `workInProgressHook` | L268 | L995, L1026, L1065 | L667, L833, L964 |
| `didScheduleRenderPhaseUpdate` | L274 | L3830 | L696, L957 |
| `didScheduleRenderPhaseUpdateDuringThisPass` | L279 | L3829 | L815, L973 |
| `shouldDoubleInvokeUserFnsInHooksDEV` | L280 | L595 | L599 |
| `localIdCounter` | L282 | L3474 | **L900 (`checkDidRenderIdHook`)**, L974 |
| `thenableIndexCounter` | L284 | L1097 | L700, L814, L975 |
| `thenableState` | L285 | L1099 | L701, L812, L976 |
| `globalClientIdCounter` | L290 | L3482 | **지우지 않는다** |

```text
 ★ 지우지 않는 것이 의도인 자리들

 globalClientIdCounter (L290)
   주석 L287-289 가 밝힌다
     "이 카운터는 전역이므로 클라이언트 id 는
      렌더 시도 사이에 안정적이지 않다"

 renderLanes 를 resetHooksAfterThrow 가 남기는 것
   주석 L926-931 이 이유를 적는다
     throw 직후에 불리는데, 작업 루프가 되감기 없이
     컴포넌트를 재생할 수 있으므로 모듈 상태를 전부
     리셋하면 안 된다

 localIdCounter 를 finishRenderingHooks 가 안 지우는 것
   L697-698 에 주석 처리돼 있고
   호출자가 checkDidRenderIdHook() 을 불러야 0 이 된다
   ([beginWork] L451 / L1506 / L1516 / L1560 이 그렇게 한다)
```

## 훅 개수 검사의 비대칭

```text
 더 많으면   updateWorkInProgressHook L1044
             그 훅을 부르는 **즉시** 던진다
             초기 렌더 변종은 L1039 (도달하면 안 되는 방어선)

 더 적으면   finishRenderingHooks L660-661 에서 세어 두고
             전역을 전부 리셋한 **뒤** L704 에서 던진다
             (그래야 던진 뒤에도 모듈 전역이 깨끗하다)

 ★ 훅을 하나도 안 부른 조기 반환은 어느 쪽에도 안 걸린다
   currentHook 이 null 이라 L660 의 첫 항이 거짓이다
   결과는 에러가 아니라 다음 렌더의 조용한 상태 초기화다
```

## didReceiveUpdate 를 올리는 여섯 자리

```text
 markWorkInProgressReceivedUpdate ([beginWork] L3763) 를
 import 하는 파일은 이 파일 하나뿐이다 (L114)

 L724   finishRenderingHooks    props·state 는 그대로인데 컨텍스트가 바뀜
                                (훅이 아니라 렌더 마무리 단계다)
 L1542  updateReducerImpl       useState/useReducer 갱신의 본줄기
 L1618  rerenderReducer         렌더 중 setState 재실행
 L1765  updateSyncExternalStore 외부 스토어 스냅샷이 달라짐
 L3053  updateDeferredValueImpl 숨겨진 트리에서 값이 바뀜
 L3080  updateDeferredValueImpl 긴급하지 않은 렌더에서 새 값을 씀

 => [beginWork]의 바이아웃 판정을 훅이 뒤집는 유일한 통로다
```

## DEV 전용 디스패처 일곱

```text
 HooksDispatcherOnMountInDEV                 L4013
 HooksDispatcherOnMountWithHookTypesInDEV    L4183
 HooksDispatcherOnUpdateInDEV                L4347
 HooksDispatcherOnRerenderInDEV              L4511
 InvalidNestedHooksDispatcherOnMountInDEV    L4675
 InvalidNestedHooksDispatcherOnUpdateInDEV   L4864
 InvalidNestedHooksDispatcherOnRerenderInDEV L5053

 InvalidNested* 셋은 "훅 안에서 훅을 부르는 것" 을 잡는다
 경고만 찍고 원래 구현을 그대로 실행한다. 던지지 않는다

 갈아끼우는 훅은 언제나 셋뿐이다 -
 useMemo / useReducer / useState
 사용자 함수(create, init, initialState)를 부르는 훅들이다

 OnMountWithHookTypesInDEV 는 운영에 대응물이 없다
 "갱신인데 stateful 훅이 하나도 없던" 엣지 케이스 전용이다
 (운영은 그냥 OnMount 를 쓴다)

 (이 목록은 검증 과정에서 확인된 것이고
  나는 선언 줄과 용도까지만 확인했다)
```

## 결과가 쓰이는 곳

```text
 ReactSharedInternals.H
      --> react 패키지의 useState 등이 이것을 찾아 부른다
      --> 렌더 밖에서는 ContextOnlyDispatcher 가 깔려 있다

 훅 리스트 (fiber.memoizedState)
      --> 다음 렌더가 마운트/갱신을 이것으로 판정한다

 모듈 전역
      --> 훅 구현들이 "지금 누구를 렌더 중인가" 를 여기서 읽는다
      --> throw 후 재생을 위해 일부러 남기는 것이 있다

 didReceiveUpdate
      --> [beginWork]가 바이아웃할지 정한다
```

## 다루지 않는 것

각 훅 구현의 본문, `updateReducerImpl` 의 재베이스·optimistic·gesture 갈래, `trackUsedThenable` 과 `ReactFiberThenable.js` 의 promise 관리, `readContext` 와 `fiber.dependencies` 의 컨텍스트 의존 목록, DEV 디스패처 일곱 개의 개별 검사와 `hookTypesDev` 순서 검증, `pushDispatcher` / `popDispatcher`(`ReactFiberWorkLoop.js`), `resetHooksAfterThrow` / `resetHooksOnUnwind` 의 나머지, `StaticMask` 무결성 검사(L678-693)는 이 문서의 범위 밖이다.
