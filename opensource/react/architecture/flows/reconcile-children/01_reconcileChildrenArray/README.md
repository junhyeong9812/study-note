# reconcileChildrenArray

상위: [자식 조정 흐름](../README.md)

리스트를 짝짓는 본체다. **네 단계**로 되어 있고, 1단계가 끝까지 가면 맵을 만들지 않는다.

## 위치

`packages/react-reconciler` / `src` / `ReactChildFiber.js` L1175-L1367 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactChildFiber.js#L1175-L1367))

## 실제 코드

머리 주석이 설계를 밝힌다.

```js
// ReactChildFiber.js L1181-L1198
    // This algorithm can't optimize by searching from both ends since we
    // don't have backpointers on fibers. I'm trying to see how far we can get
    // with that model. If it ends up not being worth the tradeoffs, we can
    // add it later.

    // Even with a two ended optimization, we'd want to optimize for the case
    // where there are few changes and brute force the comparison instead of
    // going for the Map. It'd like to explore hitting that path first in
    // forward-only mode and only go for the Map once we notice that we need
    // lots of look ahead. This doesn't handle reversal as well as two ended
    // search but that's unusual. Besides, for the two ended optimization to
    // work on Iterables, we'd need to copy the whole set.

    // In this first iteration, we'll just live with hitting the bad case
    // (adding everything to a Map) in for every insert/move.

    // If you change this code, also update reconcileChildrenIterator() which
    // uses the same algorithm.
```

> This algorithm **can't** optimize by searching from both ends since we don't have backpointers on fibers. **I'm trying to see how far we can get** with that model. **If it ends up not being worth the tradeoffs, we can add it later.**

> This doesn't handle reversal as well as two ended search but that's **unusual**.

> **In this first iteration**, we'll just live with hitting the bad case (adding everything to a Map) in for every insert/move.

> If you change this code, also update `reconcileChildrenIterator()` which uses the same algorithm.

1단계가 멈추는 자리. 그 위 TODO 가 함정을 적는다.

```js
// ReactChildFiber.js L1222-L1231
      if (newFiber === null) {
        // TODO: This breaks on empty slots like null children. That's
        // unfortunate because it triggers the slow path all the time. We need
        // a better way to communicate whether this was a miss or null,
        // boolean, undefined, etc.
        if (oldFiber === null) {
          oldFiber = nextOldFiber;
        }
        break;
      }
```

> TODO: This breaks on empty slots like null children. That's unfortunate because it **triggers the slow path all the time**. We need a better way to communicate whether this was a miss or null, boolean, undefined, etc.

## 동작 흐름

```text
 L1175  function reconcileChildrenArray(returnFiber, currentFirstChild,
                                        newChildren, lanes)

 지역 상태 일곱
   L1200  knownKeys          [__DEV__] 중복 키 경고용
   L1202  resultingFirstChild  돌려줄 첫 자식
   L1203  previousNewFiber     sibling 사슬을 잇는 커서
   L1205  oldFiber             옛 리스트의 현재 위치
   L1206  lastPlacedIndex      이동 판정의 기준선
   L1207  newIdx               새 리스트의 현재 위치
   L1208  nextOldFiber         구멍 처리용 보류 자리

 --- 1단계: 나란히 걷기  L1209-1262 ---
 L1209  for (; oldFiber !== null && newIdx < newChildren.length; newIdx++)
 L1210    oldFiber.index > newIdx 이면 (구멍이다)
 L1211      nextOldFiber = oldFiber
 L1212      oldFiber = null            <- 이 슬롯은 대응이 없다고 친다
 L1213    아니면
 L1214      nextOldFiber = oldFiber.sibling

 L1216    newFiber = updateSlot(returnFiber, oldFiber, newChildren[newIdx], lanes)
 L1222    null 이면 (키가 안 맞거나 렌더 불가 값이다)
 L1227      oldFiber === null 이면 oldFiber = nextOldFiber   <- 보류분 복원
 L1230      break

 L1233    [__DEV__] warnOnInvalidKey(...)
 L1242    shouldTrackSideEffects 이고
 L1243      oldFiber 가 있는데 newFiber.alternate === null 이면
 L1246        deleteChild(returnFiber, oldFiber)   <- 타입이 달라 교체했다
 L1249    lastPlacedIndex = placeChild(newFiber, lastPlacedIndex, newIdx)
 L1250    previousNewFiber === null 이면
 L1252      resultingFirstChild = newFiber
 L1253    아니면
 L1258      previousNewFiber.sibling = newFiber
 L1260    previousNewFiber = newFiber
 L1261    oldFiber = nextOldFiber

 --- 2단계: 새 것이 끝남  L1264-1272 ---
 L1264  newIdx === newChildren.length 이면
 L1266    deleteRemainingChildren(returnFiber, oldFiber)
 L1267    [수화 중] pushTreeFork(returnFiber, newIdx)
 L1271    => return resultingFirstChild

 --- 3단계: 옛 것만 끝남  L1274-1304 ---
 L1274  oldFiber === null 이면
 L1277    for (; newIdx < newChildren.length; newIdx++)
 L1278      newFiber = createChild(returnFiber, newChildren[newIdx], lanes)
 L1279      null 이면 continue
 L1290      lastPlacedIndex = placeChild(newFiber, lastPlacedIndex, newIdx)
 L1291      사슬을 잇는다
 L1299    [수화 중] pushTreeFork
 L1303    => return resultingFirstChild

 --- 4단계: 키 맵  L1306-1366 ---
 L1307  existingChildren = mapRemainingChildren(oldFiber)
 L1310  for (; newIdx < newChildren.length; newIdx++)
 L1311    newFiber = updateFromMap(existingChildren, returnFiber, newIdx, ...)
 L1318    null 이 아니면
 L1327      shouldTrackSideEffects 이고
 L1329        newFiber.alternate 가 있으면 (재사용했으면)
 L1338          existingChildren.delete(-newIdx - 1)          (낙관적 키)
 L1340          또는 delete(currentFiber.key === null ? newIdx : currentFiber.key)
 L1346      lastPlacedIndex = placeChild(newFiber, lastPlacedIndex, newIdx)
 L1347      사슬을 잇는다
 L1356  shouldTrackSideEffects 이면
 L1359    existingChildren.forEach(child => deleteChild(returnFiber, child))
 L1362  [수화 중] pushTreeFork
 L1366  => return resultingFirstChild
```

```text
 2단계와 3단계는 조건이 배타적이지 않다

 길이가 같고 전부 슬롯이 맞으면 1단계가
 oldFiber === null 과 newIdx === length 를 **동시에** 만족하며 끝난다

 그때 L1264 를 먼저 검사해 L1271 에서 돌려주므로 3단계는 안 돈다
 (deleteRemainingChildren(returnFiber, null) 은 무해하다)

 => 이름을 정확히 하면
    2단계 = "새 것이 끝남(동시 포함)"
    3단계 = "새 것은 남았고 옛 것만 끝남"
```

```text
 ★ 맵을 만드는 조건은 좁다

 맵(4단계)은 **1단계가 break 로 끝났고 그때 oldFiber 가 남아 있을 때만** 만든다

 끝에 덧붙이는 삽입   1단계가 oldFiber === null 로 정상 종료 -> 3단계 fast path
 끝에서 지우는 삭제   1단계가 newIdx === length 로 종료 -> 2단계
 둘 다 맵 없이 끝난다

 그런데 반대 방향의 함정이 있다 - TODO L1223-1226 이 적는다
   {cond && <X/>} 가 슬롯에 있으면 cond 가 거짓일 때 값이 false 다
   false 는 updateSlot 바닥의 return null 로 떨어져 즉시 break 한다
   빈 문자열('')도 같다 (L850 의 newChild !== '' 때문)

 => 조건부 렌더가 섞인 흔한 리스트에서는 맵이 매번 만들어진다
    주석이 "triggers the slow path all the time" 이라고 적는 그것이다
```

```text
 ★ 인덱스 구멍을 다루는 한 쌍

 L1210-1215 와 L1227-1229 는 한 쌍으로 읽어야 한다

 옛 자식 중 null/boolean 은 fiber 를 만들지 않아
 옛 fiber 의 index 가 연속이 아니다
   [<A/>, null, <B/>]  ->  A.index=0, B.index=2

 newIdx=1 인데 oldFiber 가 B(index 2)면
 이 슬롯에 대응하는 옛 fiber 가 없다는 뜻이다. 그래서
   L1211  nextOldFiber = oldFiber    B 를 보류하고
   L1212  oldFiber = null            updateSlot 이 "삽입" 으로 흐르게 한다

 그런데 새 자식도 null 이라 updateSlot 이 null 을 돌려주면
   L1227  oldFiber = nextOldFiber    보류했던 B 를 되돌린다
 안 그러면 L1274 가 "옛 자식이 없다" 고 오판해
 B 가 맵에도 삭제 목록에도 못 들어가고 사라진다
```

```text
 세 단계 모두 placeChild 를 부른다

 L1249 (1단계) / L1290 (3단계) / L1346 (4단계)

 3단계는 전부 새로 만든 fiber 라 언제나 Placement 가 붙고,
 4단계는 재사용 여부에 따라 갈린다
```

```text
 이터레이터 판은 정말 같은 알고리즘이다

 reconcileChildrenIterator (L1491) 와 비교하면
 다른 것은 순회 구동부뿐이다

   루프 헤더   newChildren[newIdx]  vs  step.value
   종료 판정   newIdx === length    vs  step.done
   추가 가드   없음                 vs  newChildren == null 이면 throw

 구멍 보정, break 복원, deleteChild 조건, placeChild,
 맵 삭제, 잔여 삭제, pushTreeFork 전부 같다

 (이 대조는 검증 과정에서 기계적으로 확인된 것이다)

 실제 차이는 알고리즘 밖에 있다 - 이터레이터는 한 번만 소비된다.
 그래서 제너레이터 경고가 붙고, 비동기 이터러블은
 next() 를 unwrapThenable 로 감싸 서스펜드 시 처음부터 다시 돌린다
```

## 결과가 쓰이는 곳

```text
 resultingFirstChild
      --> [beginWork]가 workInProgress.child 로 받는다

 각 fiber 의 sibling 사슬
      --> 다음 렌더의 옛 리스트가 된다

 Placement 플래그
      --> [커밋]의 mutation 패스가 DOM 을 옮긴다

 returnFiber.deletions
      --> [커밋]이 언마운트하고 [패시브 이펙트]가 cleanup 한다
```

## 다루지 않는 것

`updateSlot`(L840) / `updateFromMap`(L983) / `createChild`(L708)의 갈래별 판정([02 재사용 판정](../02_reuseDecision/README.md)에 있다), `mapRemainingChildren`(L467)이 키를 고르는 규칙([03 placeChild](../03_placeChild/README.md)에 있다), `deleteChild`(L434)의 기록 방식, `warnOnInvalidKey`(L1120)의 DEV 검증, `pushTreeFork` 와 수화 중 `useId` 장치, `reconcileChildrenIterator`(L1491)의 본문은 같은 뼈대의 곁가지라 요약만 했다.
