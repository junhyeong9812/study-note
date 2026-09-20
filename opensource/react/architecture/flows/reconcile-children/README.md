# 자식 조정

상위: [React 아키텍처 지도](../../README.md)

[beginWork](../begin-work/README.md)가 컴포넌트를 평가해 얻은 엘리먼트를 **옛 fiber 와 짝지어** 재사용할지 새로 만들지 정한다. **`key` 가 왜 필요한가**의 답이 여기 있다.

이 흐름의 핵심은 셋이다. **키 비교와 타입 비교가 서로 다른 층에서 일어나고**, **알고리즘이 앞으로만 가며**, **키가 없으면 신원이 슬롯 위치가 된다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactChildFiber.js` 기준이다. `BW` = `ReactFiberBeginWork.js`.

## 전체 그림

```text
 [beginWork]의 reconcileChildren    BW L341-372
      +-- 부모의 current === null 이면  mountChildFibers   BW L352
      +-- 아니면                        reconcileChildFibers BW L365

 [01] 팩토리가 둘을 만든다            L431 / L2108-2110
      같은 본문, shouldTrackSideEffects 하나만 다르다

 [02] reconcileChildFibersImpl        L1852-2030
      +-- 엘리먼트 하나면  reconcileSingleElement
      +-- 배열이면        [03] reconcileChildrenArray
      +-- 이터러블이면    reconcileChildrenIterator (같은 알고리즘)
      +-- 그 밖은 전부    deleteRemainingChildren     L2029

 [03] reconcileChildrenArray          L1175-1367
      1단계  나란히 걷기        L1209-1262
      2단계  새 것이 끝남       L1264-1272
      3단계  옛 것만 남음       L1274-1304
      4단계  키 맵              L1306-1366

 [04] placeChild - 이동 판정          L511-539
      옛 인덱스가 기준선보다 작으면 이동, 아니면 기준선을 올린다
```

1. [reconcileChildrenArray](01_reconcileChildrenArray/README.md)가 네 단계로 짝짓는다.
2. [재사용 판정](02_reuseDecision/README.md)이 키와 타입을 각각 본다.
3. [placeChild](03_placeChild/README.md)가 무엇을 옮길지 정한다.

```text
 ★ 키 비교와 타입 비교가 다른 층이다

 키를 보는 층   updateSlot (L857 / L877 / L898 / L925)
                updateFromMap (맵 조회가 키 비교를 대신한다)

 타입을 보는 층  updateTextNode  L556   tag !== HostText
                updateElement   L601   current.elementType === elementType
                updatePortal    L642   tag + containerInfo + implementation
                updateFragment  L677   tag !== Fragment

 ★ updateSlot 이 null 을 돌려주는 것은 **키가 안 맞을 때**다.
   타입이 달라도 null 이 아니다 - 새 fiber 를 만들어 돌려준다

 그래서 1단계 루프는 타입이 달라도 멈추지 않고
 그 자리에서 교체한다 (L1243-1246 deleteChild)
```

```text
 ★ 키가 없으면 신원이 슬롯 위치가 된다

 updateSlot L847  const key = oldFiber !== null ? oldFiber.key : null;
            L877  newChild.key === key

 둘 다 키가 없으면 null === null 이라 **언제나 통과한다**

 그 다음 updateElement L601 이 elementType 을 비교한다
   같으면  L616 useFiber(current, element.props)   ** 재사용 **
   다르면  L627 새로 만들고, 호출부가 옛것을 지운다

 => 키 없는 리스트에서 순서를 바꾸면
    타입이 같으면 **전부 재사용되고 props 만 뒤바뀐다**
    타입이 다르면 전부 새로 만들어진다

 ★ 즉 문제는 "재사용이 안 되는 것" 이 아니라
   **상태가 위치에 붙는 것**이다.
   useState 가 0번 슬롯에 남고 그 자리에 다른 항목의 props 가 온다
```

```text
 ★ 앞으로만 가는 이유를 주석이 적는다

 L1181-1184
   "This algorithm can't optimize by searching from both ends since we
    don't have backpointers on fibers. I'm trying to see how far we can
    get with that model. If it ends up not being worth the tradeoffs,
    we can add it later."

 실제로 Fiber 에는 형제를 거슬러 갈 포인터가 없다.
 구조 주석이 "Singly Linked List Tree Structure" 라고 적고
 child / sibling / index 와 위 방향 return 뿐이다
 (alternate 는 세대 간 짝이지 형제 방향이 아니다)

 L1186-1192 가 이유를 더 댄다
   양끝 최적화가 있어도, 변화가 적을 때는 맵 대신 무차별 비교를
   하고 싶다. 이 방식이 뒤집기(reversal)를 two ended search 만큼
   잘 다루지 못하지만 **그건 흔치 않다**.
   게다가 이터러블에 양끝 최적화를 하려면 집합 전체를 복사해야 한다
```

## 어디로 이어지는가

```text
 [beginWork]    update*Component 들이 reconcileChildren 을 부른다
                결과가 workInProgress.child 가 된다

 [커밋]         여기서 붙인 Placement 플래그를 저쪽이 소비한다
                여기서 부모에 쌓은 deletions 배열도 저쪽이 읽는다

 [패시브 이펙트] 그 deletions 배열로 삭제된 트리의 cleanup 을 돈다

 [에러와 Suspense] 조정 중 던져진 에러는 여기서 Throw fiber 가 된다
                   (L2032-2103 의 try/catch)
```

## 결과가 쓰이는 곳

```text
 workInProgress.child
      --> 반환한 첫 자식. sibling 사슬로 이어진다

 flags |= Placement | PlacementDEV
      --> 커밋의 mutation 패스가 DOM 을 옮기거나 넣는다
      --> PlacementDEV 는 커밋 후에도 리셋되지 않는다

 returnFiber.deletions / flags |= ChildDeletion
      --> 삭제는 **부모에** 기록된다
      --> 지워지는 fiber 자신에는 아무 표시도 안 붙는다

 재사용한 fiber
      --> alternate 가 채워져 있다
      --> 훅 상태가 그대로 딸려 온다 (이것이 key 의 요점이다)
```

## 다루지 않는 것

`reconcileSingleElement`(L1701)와 `reconcileSinglePortal`(L1806)의 단일 자식 경로([02 재사용 판정](02_reuseDecision/README.md)에 요약이 있다), `reconcileChildrenIterator`(L1491)의 본문(배열과 같은 알고리즘이다), 비동기 이터러블(L1435)과 `unwrapThenable`, `createChild`(L708)의 갈래 전부, `coerceRef`(L291)와 ref 처리, `warnOnInvalidKey`(L1120)의 DEV 검증, `getIsHydrating` → `pushTreeFork` 의 수화용 `useId` 장치, `validateSuspenseListChildren`(L2187), `forceUnmountCurrentAndReconcile`(BW L374)의 강제 재마운트는 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 reconcileChildrenArray](01_reconcileChildrenArray/README.md)
- [02 재사용 판정](02_reuseDecision/README.md)
- [03 placeChild](03_placeChild/README.md)
