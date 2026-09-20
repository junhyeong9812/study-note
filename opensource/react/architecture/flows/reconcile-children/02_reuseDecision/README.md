# 재사용 판정

상위: [자식 조정 흐름](../README.md)

**키를 보는 층과 타입을 보는 층이 다르다.** 이 분리가 `key` 의 동작을 결정한다.

## 위치

슬롯 판정 `packages/react-reconciler` / `src` / `ReactChildFiber.js` L840-L981 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactChildFiber.js#L840-L981))

타입 판정 `packages/react-reconciler` / `src` / `ReactChildFiber.js` L578-L634 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactChildFiber.js#L578-L634))

## 실제 코드

키는 **옛 fiber 의 것**을 기준으로 잡는다.

```js
// ReactChildFiber.js L846-L847
    // Update the fiber if the keys match, otherwise return null.
    const key = oldFiber !== null ? oldFiber.key : null;
```

> Update the fiber if the keys match, otherwise return null.

그리고 타입 비교는 한 층 아래에 있다.

```js
// ReactChildFiber.js L599-L625
    if (current !== null) {
      if (
        current.elementType === elementType ||
        // Keep this check inline so it only runs on the false path:
        (__DEV__
          ? isCompatibleFamilyForHotReloading(current, element)
          : false) ||
        // Lazy types should reconcile their resolved type.
        // We need to do this after the Hot Reloading check above,
        // because hot reloading has different semantics than prod because
        // it doesn't resuspend. So we can't let the call below suspend.
        (typeof elementType === 'object' &&
          elementType !== null &&
          elementType.$$typeof === REACT_LAZY_TYPE &&
          resolveLazy(elementType) === current.type)
      ) {
        // Move based on index
        const existing = useFiber(current, element.props);
        coerceRef(existing, element);
        existing.return = returnFiber;
        if (__DEV__) {
          existing._debugOwner = element._owner;
          existing._debugInfo = currentDebugInfo;
        }
        return existing;
      }
    }
```

## 두 층

```text
 키를 보는 층
   updateSlot   L857  텍스트인데 옛 fiber 에 키가 있으면 null
                L877  엘리먼트의 키가 옛 fiber 키와 다르면 null
                L898  포털도 같다
                L925  배열/이터러블인데 옛 fiber 에 키가 있으면 null
                L980  렌더 불가 값이면 null

   updateFromMap  키 비교가 없다. **맵 조회**가 그 일을 한다
                  L1012  get(newChild.key === null ? newIdx : newChild.key)
                  L997   텍스트는 get(newIdx) - 인덱스로만
                  L1060  배열/이터러블도 get(newIdx)

 타입을 보는 층 (네 함수뿐)
   updateTextNode  L556  current.tag !== HostText 이면 생성
   updateElement   L601  current.elementType === elementType 이면 재사용
   updatePortal    L642  tag + containerInfo + implementation 을 다 본다
   updateFragment  L677  current.tag !== Fragment 이면 생성
```

```text
 ★ updateSlot 이 null 을 돌려주는 것은 키 때문이다

 타입이 달라도 null 이 아니다.
 키가 맞으면 updateElement 로 내려가고,
 거기서 타입이 다르면 **새 fiber 를 만들어 돌려준다** (L627)

 => 1단계 루프는 타입이 달라도 멈추지 않는다
    호출부가 newFiber.alternate === null 로 사후 판별해
    옛 fiber 를 지운다 (L1243-1246)

 ★ update* 넷은 절대 null 을 돌려주지 않는다
   "재사용 못 했다" 를 표현하는 방법이 반환값이 아니라
   **alternate 가 비어 있다**는 사실이다
```

```text
 ★ updateElement 의 재사용 조건이 셋이다

 먼저 Fragment 선분기가 있다 (L584-598)
   element.type === REACT_FRAGMENT_TYPE 이면 updateFragment 로 위임한다
   즉 <React.Fragment key="x"> 는 본체를 타지 않는다

 본체 (L599-614) - current 가 있고 셋 중 하나면 재사용
   1  current.elementType === elementType            L601
      ★ type 이 아니라 **elementType** 이다
        elementType 은 element.type 그대로이고
        type 은 풀린 함수/클래스다
   2  [__DEV__] isCompatibleFamilyForHotReloading    L603-605
      운영에서는 false 리터럴이다
   3  elementType 이 REACT_LAZY_TYPE 이고
      resolveLazy(elementType) === current.type      L610-613

 ★ 3번이 비대칭이다 - 1번은 current.elementType 과 비교하는데
   3번은 current.type(풀린 타입)과 비교한다

 그리고 주석 L606-609 이 순서의 이유를 적는다 -
 핫 리로딩 검사 뒤에 둬야 한다.
 핫 리로딩은 resuspend 하지 않으므로 resolveLazy 가 서스펜드하면 안 된다

 => resolveLazy 는 미해결이면 던진다.
    즉 **이 비교가 렌더를 서스펜드시킬 수 있다**
```

```text
 ★ updateFromMap 은 거의 null 을 안 돌려준다

 updateSlot     키가 안 맞으면 null -> 1단계가 break 한다
 updateFromMap  못 찾아도 null 이 아니다.
                matchedFiber = null 로 updateElement 에 넘겨
                **새 fiber 를 만들어** 돌려준다
                null 은 렌더 불가 값일 때만이다 (L1114)

 => 두 함수의 성격이 다르다.
    슬롯 경로는 "안 맞으면 포기", 맵 경로는 "못 찾으면 만든다"
```

```text
 Lazy 는 키를 버린다

 updateSlot L905-916 / updateFromMap L1039-1051

 resolveLazy 로 풀고 **같은 자리에서 재귀**한다.
 즉 lazy 래퍼의 키가 아니라 **풀린 자식의 키**가 비교 대상이 된다

 thenable(L944) 과 Context 객체(L958)도 같은 모양이다 -
 풀어서 재귀한다
```

```text
 단일 자식 경로는 네 가지가 다르다

 reconcileSingleElement (L1701)

 1  인덱스 대응이 아니라 **키로 옛 sibling 사슬을 탐색**한다
    옛 자식이 여럿이어도 키만 맞으면 그것을 재사용한다
 2  훑으면서 지나친 자식을 **즉시 삭제**한다 (L1771)
    키는 맞는데 타입이 틀리면 자기 자신부터 뒤 전부 삭제하고 break
    (같은 키가 둘일 수 없으므로 더 찾지 않는다)
 3  lastPlacedIndex / placeChild 가 **없다**
    호출부가 placeSingleChild 로 감싸고,
    그것은 alternate === null 일 때만 Placement 를 붙인다 (L544-546)
    => 단일 자식은 재사용되면 **절대 "이동" 으로 표시되지 않는다**
 4  useFiber 가 index=0, sibling=null 로 리셋해 사슬에서 떼어 낸다

 (이 대조는 검증 과정에서 확인된 것이고,
  나는 reconcileSingleElement 의 위치와 placeSingleChild 까지 직접 봤다)
```

```text
 createChild 는 아무것도 재사용하지 않는다

 L708-838. 키를 전혀 보지 않는다.
 결과 fiber 는 언제나 alternate === null 이라
 placeChild 에서 무조건 Placement 가 붙는다

 마지막 줄 L837 이 return null 이다 -
 빈 문자열·null·undefined·boolean·함수·심볼이 여기로 온다
```

## 결과가 쓰이는 곳

```text
 재사용한 fiber (alternate 가 있다)
      --> 훅 상태와 stateNode 가 딸려 온다
      --> placeChild 가 이동인지 제자리인지 판정한다

 새로 만든 fiber (alternate 가 null)
      --> placeChild 가 삽입으로 보고 Placement 를 붙인다
      --> 호출부가 옛 fiber 를 deleteChild 한다

 null 반환 (updateSlot 만)
      --> 1단계가 break 하고 맵 경로로 간다
```

## 다루지 않는 것

`updateTextNode`(L550) / `updatePortal`(L636) / `updateFragment`(L670)의 본문, `createChild`(L708)의 갈래별 생성 함수, `reconcileSingleElement`(L1701) / `reconcileSinglePortal`(L1806) / `reconcileSingleTextNode`(L1671)의 전체 본문, `useFiber`(L502)와 `createWorkInProgress`, `coerceRef`(L291), `resolveLazy` 의 thenable 처리, `readContextDuringReconciliation`, `enableOptimisticKey` 의 낙관적 키 부여는 같은 뼈대의 곁가지라 요약만 했다.
