# 내려가는 순회

상위: [컨텍스트 흐름](../README.md)

서브트리를 훑어 소비자를 찾는다. **값을 알리는 것이 아니라 lanes 를 올려 바이아웃을 뚫는다.**

## 위치

`packages/react-reconciler` / `src` / `ReactFiberNewContext.js` L214-L377 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberNewContext.js#L214-L377))

## 실제 코드

소비자를 찾았을 때 하는 일.

```js
// ReactFiberNewContext.js L252-L261
            consumer.lanes = mergeLanes(consumer.lanes, renderLanes);
            const alternate = consumer.alternate;
            if (alternate !== null) {
              alternate.lanes = mergeLanes(alternate.lanes, renderLanes);
            }
            scheduleContextWorkOnParentPath(
              consumer.return,
              renderLanes,
              workInProgress,
            );
```

> Since propagation is lazy, we don't set the dirty flag on the dependency itself. ... the consumer checks for itself.

그리고 커서를 전진시키는 자리.

```js
// ReactFiberNewContext.js L352-L374
    if (nextFiber !== null) {
      // Set the return pointer of the child to the work-in-progress fiber.
      nextFiber.return = fiber;
    } else {
      // No child. Traverse to next sibling.
      nextFiber = fiber;
      while (nextFiber !== null) {
        if (nextFiber === workInProgress) {
          // We're back to the root of this subtree. Exit.
          nextFiber = null;
          break;
        }
        const sibling = nextFiber.sibling;
        if (sibling !== null) {
          // Set the return pointer of the sibling to the work-in-progress fiber.
          sibling.return = nextFiber.return;
          nextFiber = sibling;
          break;
        }
        // No more siblings. Traverse up.
        nextFiber = nextFiber.return;
      }
    }
```

## 동작 흐름

```text
 L214  function propagateContextChanges(workInProgress, contexts,
                                        renderLanes, forcePropagateEntireTree)

 L220  fiber = workInProgress.child
 L221  fiber 가 있으면
 L223    fiber.return = workInProgress
          주석 L222 - 자식의 return 포인터를 WIP 로 다시 건다

 L225  while (fiber !== null)
 L226    nextFiber

        --- 갈래 넷 (switch 가 아니라 if/else-if 체인) ---

 L230    fiber.dependencies 가 있으면          (소비자 후보)
 L231      nextFiber = fiber.child             기본은 내려간다
 L234      의존 리스트를 훑으며 contexts 와 대조한다
 L242        dependency.context === context     ★ 동일성 비교다
 L252        consumer.lanes 에 renderLanes merge
 L253        alternate.lanes 에도 merge
 L257        scheduleContextWorkOnParentPath(consumer.return, renderLanes,
                                             workInProgress)
 L263        forcePropagateEntireTree 가 아니면
 L268          nextFiber = null                ** 자식은 안 내려간다 **
 L273        break findChangedDep

 L278    아니면 DehydratedFragment 이면
 L282      parentSuspense = fiber.return
 L290      parentSuspense 와 그 alternate 의 lanes 에 merge
 L299      scheduleContextWorkOnParentPath(parentSuspense, ...)
            ★ 주석 L295-298 - 일부러 .return 이 아니라 이 fiber 자신을
              parent 로 넘긴다. 자기 childLanes 로 표시하려고
 L304      nextFiber = null                    탈수 경계 안으로는 안 간다

 L305    아니면 Suspense 가 fallback 을 보여주는 중이면
 L319      fiber 와 alternate 의 lanes 에 merge
 L324      scheduleContextWorkOnParentPath(fiber.return, ...)
 L341      primaryChildFragment = fiber.child
 L343      nextFiber = primaryChildFragment.sibling
            ** 숨은 primary 를 건너뛰고 fallback 형제로 점프한다 **

 L347    아니면
 L348      nextFiber = fiber.child

        --- 커서 전진 ---
 L352    nextFiber 가 있으면
 L354      nextFiber.return = fiber
 L356    없으면
 L357      nextFiber = fiber
 L358      위로 올라가며 형제를 찾는다
 L359        nextFiber === workInProgress 이면
 L361          nextFiber = null; break     ** 서브트리 루트에 닿았다 **
 L364        sibling 이 있으면
 L367          sibling.return = nextFiber.return
 L369          nextFiber = sibling; break
 L372        nextFiber = nextFiber.return
 L375    fiber = nextFiber
```

```text
 재귀가 아니라 커서 루프다

 while 하나에 nextFiber 커서로 오르내린다.
 그리고 내려가거나 옆으로 갈 때마다 return 포인터를 다시 건다
   L354  nextFiber.return = fiber
   L367  sibling.return = nextFiber.return

 옛 트리의 fiber 를 만날 수 있어서다.
 [자식 조정]의 bubbleProperties 가 같은 일을 하는 것과 같은 사정이다

 종료는 L359-363 이다 - workInProgress 에 돌아오면 끝낸다
 => 순회가 **workInProgress 서브트리로 엄격히 제한된다**
```

```text
 ★ 소비자를 찾아도 값을 안 건드린다

 L252  consumer.lanes = mergeLanes(consumer.lanes, renderLanes)
 L253  alternate.lanes 에도 같은 일을
 L257  scheduleContextWorkOnParentPath(consumer.return, renderLanes,
                                       workInProgress)

 하는 일이 이것뿐이다. memoizedValue 를 갱신하지도,
 dirty 플래그를 세우지도 않는다

 주석 L245-251 이 이유를 적는다 -
 lazy 구현에서는 전부 전파되지 않으므로
 전파 함수만으로는 "바뀌었다" 를 판정할 수 없다.
 소비자가 렌더될 때 [03] checkIfContextChanged 로 직접 검사한다

 => 전파의 역할은 **소비자를 렌더 대상으로 만드는 것**까지다
```

```text
 ★ forcePropagateEntireTree 를 쓰는 자리는 하나뿐이다

 L263  이 플래그가 거짓이면 L268 nextFiber = null

 즉 lazy 전파는 **매치한 소비자의 자식으로 내려가지 않는다**.
 어차피 그 소비자가 렌더될 때 자식도 방문하기 때문이다
 (형제는 계속 훑는다 - 커서는 위로 올라가 형제를 찾는다)

 그리고 2번·3번 갈래의 nextFiber = null 은
 이 플래그와 **무관**하다. 언제나 그 자리에서 멈춘다
```

```text
 ★ Suspense fallback 갈래가 비자명하다

 L341-346  숨은 primary(Offscreen)를 건너뛰고 fallback 형제로 점프한다

 주석 L310-340 이 길게 이유를 적는다.
 요지는 이렇다 -
   초기 마운트 중 primary 가 서스펜드하면 그 안의 소비자 fiber 들이
   버려져 트리에 없다. 그래서 경계 자체를 보수적으로 재시도 표시하고,
   커밋되어 **사용자에게 보이는** fallback 서브트리에는 계속 전파해야 한다

 => 안 보이는 쪽은 건너뛰고 보이는 쪽만 훑는다
```

```text
 같은 context 를 다시 제공하는 provider 를 만나면

 **멈추지 않는다.**
 이 함수 안에 ContextProvider 검사가 아예 없다
 (파일에서 그 토큰이 쓰이는 곳은 [01]의 위로 가는 루프 L431 하나다)

 그래도 맞는 이유는 그 아래 소비자가 lanes 만 올라간 뒤
 렌더될 때 [03]이 값이 안 바뀐 것을 보고 바이아웃하기 때문이다
 (다만 이것은 내가 구조를 보고 판단한 것이고 주석에 적혀 있지 않다)
```

## 결과가 쓰이는 곳

```text
 consumer.lanes / alternate.lanes
      --> 그 fiber 가 다음 렌더에서 바이아웃하지 않는다

 조상의 childLanes
      --> [04] scheduleContextWorkOnParentPath 가 칠한다
      --> 그래야 렌더가 소비자까지 내려온다

 nextFiber 커서
      --> 서브트리를 벗어나지 않는다
```

## 다루지 않는 것

`DehydratedFragment` 갈래(L278-304)의 탈수 경계 처리와 `parentSuspense` 를 자기 자신으로 넘기는 이유, Suspense fallback 갈래(L305-346)의 긴 주석 전체, `findChangedDep` / `findContext` 레이블(뒤엣것은 선언만 되고 쓰이지 않는다), 의존 리스트와 `contexts` 배열을 이중 루프로 대조하는 비용, `scheduleContextWorkOnParentPath`(L155)의 세 갈래([03 읽기와 비교](../03_readAndCheck/README.md)에 있다)는 같은 뼈대의 곁가지라 요약만 했다.
