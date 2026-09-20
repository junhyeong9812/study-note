# placeChild

상위: [자식 조정 흐름](../README.md)

**무엇을 옮길지 정한다.** 열두 줄이고, 기준선 하나로 판정한다.

## 위치

`packages/react-reconciler` / `src` / `ReactChildFiber.js` L511-L539 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactChildFiber.js#L511-L539))

맵에 넣는 쪽 `packages/react-reconciler` / `src` / `ReactChildFiber.js` L467-L500 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactChildFiber.js#L467-L500))

## 실제 코드

판정 전부.

```js
// ReactChildFiber.js L523-L538
    const current = newFiber.alternate;
    if (current !== null) {
      const oldIndex = current.index;
      if (oldIndex < lastPlacedIndex) {
        // This is a move.
        newFiber.flags |= Placement | PlacementDEV;
        return lastPlacedIndex;
      } else {
        // This item can stay in place.
        return oldIndex;
      }
    } else {
      // This is an insertion.
      newFiber.flags |= Placement | PlacementDEV;
      return lastPlacedIndex;
    }
```

> This is a move. / This item can stay in place. / This is an insertion.

키가 없으면 인덱스로 넣는다.

```js
// ReactChildFiber.js L483-L498
    while (existingChild !== null) {
      if (existingChild.key === null) {
        existingChildren.set(existingChild.index, existingChild);
      } else if (
        enableOptimisticKey &&
        existingChild.key === REACT_OPTIMISTIC_KEY
      ) {
        // For optimistic keys, we store the negative index (minus one) to differentiate
        // them from the regular indices. We'll look this up regardless of what the new
        // key is, if there's no other match.
        existingChildren.set(-existingChild.index - 1, existingChild);
      } else {
        existingChildren.set(existingChild.key, existingChild);
      }
      existingChild = existingChild.sibling;
    }
```

> Add the remaining children to a temporary map so that we can find them by keys quickly. **Implicit (null) keys get added to this set with their index instead.**

## 동작 흐름

```text
 L511  function placeChild(newFiber, lastPlacedIndex, newIndex)

 L516  newFiber.index = newIndex

 L517  shouldTrackSideEffects 가 아니면 (마운트 경로)
 L520    newFiber.flags |= Forked
 L521    return lastPlacedIndex
          주석 L518-519 - 수화 중 useId 알고리즘이 어떤 fiber 가
          리스트(배열, 이터레이터)의 일부인지 알아야 한다

 L523  current = newFiber.alternate
 L524  current 가 있으면 (재사용한 fiber)
 L525    oldIndex = current.index
 L526    oldIndex < lastPlacedIndex 이면
 L528      flags |= Placement | PlacementDEV        ** 이동 **
 L529      return lastPlacedIndex                   기준선 그대로
 L530    아니면
 L532      return oldIndex                          ** 제자리. 기준선을 올린다 **
 L534  없으면 (새로 만든 fiber)
 L536    flags |= Placement | PlacementDEV          ** 삽입 **
 L537    return lastPlacedIndex                     기준선 그대로
```

```text
 반환값이 곧 새 기준선이다

 호출부 셋이 전부 이 모양이다
   lastPlacedIndex = placeChild(newFiber, lastPlacedIndex, newIdx)
   L1249 (1단계) / L1290 (3단계) / L1346 (4단계)

 경우가 셋인데 기준선을 올리는 것은 하나뿐이다
   이동   기준선 그대로
   제자리 **기준선을 oldIndex 로 올린다**
   삽입   기준선 그대로

 경계는 `<` 이므로 oldIndex === lastPlacedIndex 는 "제자리" 쪽이다
```

```text
 ★ [A,B,C,D] -> [D,A,B,C] 를 따라가 보면

 1단계: newIdx=0 에서 A(key a) 와 D(key d) 의 키가 달라 break
        newIdx 는 0 그대로다
 맵 경로로 넷 전부 들어간다

   newIdx  새 자식  oldIndex  oldIndex < 기준선?  결과       기준선
   ------  -------  --------  ------------------  ---------  ------
      0      D          3       3 < 0  아니오     제자리       0 -> 3
      1      A          0       0 < 3  예         **이동**       3
      2      B          1       1 < 3  예         **이동**       3
      3      C          2       2 < 3  예         **이동**       3

 => 사람 눈에는 "D 하나를 앞으로 옮겼다"(1회)인데
    React 는 **A·B·C 셋을 옮긴다**

 ★ 방향을 뒤집으면 정반대다
   [A,B,C,D] -> [B,C,D,A] 이면
   B(1) C(2) D(3) 은 기준선이 계속 올라 제자리이고
   A 만 oldIndex 0 < 3 으로 이동한다 -> **1회**

 => 맨 앞을 맨 뒤로 보내는 것은 싸고
    맨 뒤를 맨 앞으로 보내는 것은 비싸다

 주석 L1190-1191 이 말하는 "reversal 을 two ended search 만큼
 잘 다루지 못한다" 의 실체가 이것이다
 (그리고 같은 주석이 "그건 흔치 않다" 고 덧붙인다)
```

```text
 ★ 맵에 넣을 때 키가 없으면 인덱스를 쓴다

 L484  key 가 null 이면  set(existingChild.index, child)
 L494  아니면            set(existingChild.key, child)

 그래서 맵 경로에서 키 없는 새 자식을 찾을 때도 인덱스로 조회한다
   updateFromMap L1012  get(newChild.key === null ? newIdx : newChild.key)

 => 키가 없으면 **위치가 신원**이다

 다만 이 맵은 4단계에서만 쓰인다.
 1단계는 맵 없이 옛 fiber 의 키(null)와 새 자식의 키(null)를
 직접 비교해 통과한다 - 결과는 같은 원리다
```

```text
 지울 때도 같은 키를 써야 한다

 L1338 / L1340-1342 가 맵에서 지울 때 쓰는 키는
 **currentFiber.key**(옛 fiber 의 키)다. 새 자식의 키가 아니다

   existingChildren.delete(
     currentFiber.key === null ? newIdx : currentFiber.key)

 맵에 넣을 때 쓴 키(L484-495)와 짝을 맞춰야 하기 때문이다

 그리고 이 블록 전체가 shouldTrackSideEffects 안에 있다 -
 마운트 경로에서는 맵에서 지우지도 않는다
 (어차피 L1356 의 잔여 삭제도 안 돈다)
```

```text
 마운트 경로는 다른 플래그를 켠다

 L517-521 은 부수효과를 **끄는** 것이 아니라
 Forked 를 **켜고** 기준선을 그대로 돌려준다

 Forked 는 수화 중에만이 아니라
 shouldTrackSideEffects 가 거짓인 모든 경우에 붙는다
 (주석은 그 이유를 설명할 뿐이다)

 짝이 되는 코드는 세 return 앞의 pushTreeFork 다
   L1267-1270 / L1299-1302 / L1362-1365
```

```text
 단일 자식은 이 함수를 쓰지 않는다

 placeSingleChild (L541-548)
   shouldTrackSideEffects 이고 alternate === null 일 때만
   Placement 를 붙인다

 => 단일 자식은 재사용되면 절대 "이동" 으로 표시되지 않는다
    기준선도 없고 인덱스 비교도 없다
```

## 결과가 쓰이는 곳

```text
 newFiber.index
      --> 다음 렌더에서 이 fiber 의 oldIndex 가 된다

 flags |= Placement
      --> [커밋]의 mutation 패스가 DOM 을 옮기거나 넣는다

 flags |= PlacementDEV
      --> 커밋 후에도 리셋되지 않는다
      --> StrictMode 이중 실행이 "새로 삽입된 fiber" 를 찾는 데 쓴다

 flags |= Forked
      --> 수화 중 useId 가 리스트 안의 자리를 계산한다

 반환한 기준선
      --> 다음 자식의 판정 기준이 된다
```

## 다루지 않는 것

`mapRemainingChildren`(L467)의 낙관적 키 갈래(`enableOptimisticKey` 가 `__EXPERIMENTAL__` 다), `useFiber`(L502)와 `createWorkInProgress` 가 `index` / `sibling` 을 리셋하는 이유, `pushTreeFork` 와 수화 중 `useId` 알고리즘, `PlacementDEV` 를 소비하는 StrictMode 이중 실행, `Forked` 플래그의 커밋 쪽 쓰임은 같은 뼈대의 곁가지라 요약만 했다.
