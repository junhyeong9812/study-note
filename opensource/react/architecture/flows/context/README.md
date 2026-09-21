# 컨텍스트 전파

상위: [React 아키텍처 지도](../../README.md)

`useContext` 가 값이 바뀐 것을 어떻게 아는가. 답이 뜻밖이다 — **provider 는 아무에게도 알리지 않는다.**

이 흐름의 핵심은 셋이다. **밀어내기가 아니라 당겨오기이고**, **lazy 전파는 위로 올라갔다가 아래로 내려오며**, **플래그 둘이 중복을 막는데 그 둘을 없앨 수 있다고 주석이 스스로 적는다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberNewContext.js` 기준이다. `BW` = `ReactFiberBeginWork.js`.

## 전체 그림

```text
 provider 가 하는 일은 이것뿐이다   BW L3682-3707
      pushProvider(workInProgress, context, newValue)   BW L3702
      reconcileChildren(...)                            BW L3705
      ★ 값이 바뀌었는지 비교하지도, 전파하지도 않는다

 소비자가 스스로 알아낸다 - 두 길
      (가) 바이아웃을 시도할 때 [03] checkIfContextChanged   L515-537
           자기 memoizedValue 와 지금 _currentValue 를 비교한다
      (나) 하위가 바이아웃할 때 [01] 이 **위로 올라가며** 찾는다  L431-453

 [01] propagateParentContextChanges           L411-513
      +-- 위로: 바뀐 provider 를 contexts 에 모은다    L422-479
      +-- 아래로: contexts 가 있을 때만 [02] 를 부른다  L481-490
      +-- flags |= DidPropagateContext                 L511

 [02] propagateContextChanges                 L214-377
      +-- nextFiber 커서로 서브트리를 훑는다
      +-- 소비자를 찾으면 lanes 를 올리고 조상 경로에 칠한다

 [04] scheduleContextWorkOnParentPath         L155-195
      조상의 **양쪽 alternate** 에 childLanes 를 칠한다
```

1. [lazy 전파](01_lazyPropagation/README.md)가 위로 모으고 아래로 뿌린다.
2. [내려가는 순회](02_propagateDown/README.md)가 소비자를 찾는다.
3. [읽기와 비교](03_readAndCheck/README.md)가 의존 목록을 만들고 값을 비교한다.

```text
 ★ 밀어내기가 아니라 당겨오기다

 updateContextProvider (BW L3682-3707) 전문이 이렇다
   L3702  pushProvider(workInProgress, context, newValue)
   L3705  reconcileChildren(current, workInProgress, newChildren, renderLanes)
   L3706  return workInProgress.child

 값 비교도 없고 전파 호출도 없다.
 그냥 새 값을 스택에 밀고 자식을 조정할 뿐이다

 => "provider 값이 바뀌면 소비자들에게 알린다" 는 단계가 **없다**
    소비자가 자기 렌더 차례에 스스로 확인한다

 이것이 lazy propagation 의 진짜 뜻이다
```

```text
 그럼 왜 전파 함수가 있는가

 소비자가 "자기 렌더 차례" 를 얻으려면 그 자리까지 내려와야 하는데,
 중간 조상이 바이아웃하면 내려오지 못한다

 그래서 전파가 하는 일은 **값을 알리는 것이 아니라**
 소비자와 그 조상 경로의 **lanes 를 올려 바이아웃을 뚫는 것**이다

   [02] L252  consumer.lanes 에 renderLanes 를 merge
        L257  scheduleContextWorkOnParentPath(consumer.return, ...)

 그리고 값이 실제로 바뀌었는지는 소비자가 렌더될 때
 [03] checkIfContextChanged 가 따로 본다

 주석 L245-251 이 그 분업을 적는다 -
 lazy 구현에서는 의존 항목에 dirty 플래그를 세우지 않는다.
 전부 전파되지 않으므로 전파 함수만으로는 판정할 수 없고
 소비자가 직접 검사한다
```

```text
 ★ 전파 전략이 둘인데 하나는 거의 안 쓴다

 즉시(eager)  propagateContextChange  L197-212
   TODO L202-204
     "This path is **only** used by Cache components. Update
      lazilyPropagateParentContextChanges to look for Cache components
      so they can take advantage of lazy propagation."
   호출처가 둘뿐이고 둘 다 CacheContext 를 넘긴다
   (BW L1271 updateCacheComponent, BW L1833 updateHostRoot 의 캐시 갱신)

 게으름(lazy)  lazilyPropagateParentContextChanges  L379-391
   본 경로다. 호출처가 다섯이고 전부 **바이아웃 판정 근처**다

 미뤄진 트리   propagateParentContextChangesToDeferredTree  L397-409
   Suspense / Offscreen 용이고 서브트리 전체에 전파한다
   주석 L393-396 - 현재 렌더가 끝날 때까지 다시 방문하지 않으니
   그때는 어느 provider 가 바뀌었는지 잊어버린다
```

## 어디로 이어지는가

```text
 [beginWork]    bailoutOnAlreadyFinishedWork 가 lazy 전파를 부른다
                checkScheduledUpdateOrContext 가 값 비교를 부른다
                updateContextProvider 는 push 만 한다

 [완료]         completeWork 가 popProvider 로 스택을 되돌린다

 [에러와 Suspense]  resetSuspendedComponent 가 미뤄진 트리에 전파한다

 [lane 우선순위]  전파가 하는 일이 결국 lanes 를 올리는 것이다
```

## 결과가 쓰이는 곳

```text
 fiber.dependencies
      --> 소비자가 읽은 컨텍스트의 연결 리스트
      --> 훅 리스트와 별개다
      --> checkIfContextChanged 가 memoizedValue 로 비교한다

 consumer.lanes / 조상의 childLanes
      --> 바이아웃을 뚫어 소비자까지 내려가게 한다

 context._currentValue
      --> pushProvider / popProvider 가 스택으로 관리한다

 NeedsPropagation / DidPropagateContext
      --> 중복 전파를 막는다. 렌더 1회 수명이다
```

## 다루지 않는 것

`pushProvider`(L82) / `popProvider`(L129)의 DEV 다중 렌더러 경고, `isPrimaryRenderer` 가 `_currentValue` 와 `_currentValue2` 를 가르는 이중화의 배경, `HostTransitionContext` 갈래(L454-477)와 host transition 상태, `DehydratedFragment`(L278) / Suspense fallback(L305) 갈래의 전체 본문([02 내려가는 순회](02_propagateDown/README.md)에 요약이 있다), `readContextDuringReconciliation`(L569)이 [자식 조정](../reconcile-children/README.md)에서 불리는 경로, `enterDisallowedContextReadInDEV`(L70)와 클래스 업데이트 큐의 DEV 가드는 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 lazy 전파](01_lazyPropagation/README.md)
- [02 내려가는 순회](02_propagateDown/README.md)
- [03 읽기와 비교](03_readAndCheck/README.md)
