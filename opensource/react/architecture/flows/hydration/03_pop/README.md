# 빠져나오기

상위: [하이드레이션](../README.md)

fiber 하나를 다 수화하고 나올 때. **남은 DOM 노드가 있으면 그것도 어긋남**이고, 되감기용 포크가 따로 있다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberHydrationContext.js` L759-L834 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHydrationContext.js#L759-L834))

부모 찾기 `packages/react-reconciler` / `src` / `ReactFiberHydrationContext.js` L740-L757 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHydrationContext.js#L740-L757))

## 실제 코드

나올 때 커서를 어디로 보내는가.

```js
// ReactFiberHydrationContext.js L759-L834
function popHydrationState(fiber: Fiber): boolean {
  // $FlowFixMe[constant-condition]
  if (!supportsHydration) {
    return false;
  }
  if (fiber !== hydrationParentFiber) {
    // We're deeper than the current hydration context, inside an inserted
    // tree.
    return false;
  }
  if (!isHydrating) {
    // If we're not currently hydrating but we're in a hydration context, then
    // we were an insertion and now need to pop up reenter hydration of our
    // siblings.
    popToNextHostParent(fiber);
    isHydrating = true;
    return false;
  }

  const tag = fiber.tag;

  // $FlowFixMe[constant-condition]
  if (supportsSingletons) {
    // With float we never clear the Root, or Singleton instances. We also do not clear Instances
    // that have singleton text content
    if (
      tag !== HostRoot &&
      tag !== HostSingleton &&
      !(
        tag === HostComponent &&
        (!shouldDeleteUnhydratedTailInstances(fiber.type) ||
          shouldSetTextContent(fiber.type, fiber.memoizedProps))
      )
    ) {
      const nextInstance = nextHydratableInstance;
      if (nextInstance) {
        warnIfUnhydratedTailNodes(fiber);
        throwOnHydrationMismatch(fiber);
      }
    }
  } else {
    // If we have any remaining hydratable nodes, we need to delete them now.
    // We only do this deeper than head and body since they tend to have random
    // other nodes in them. We also ignore components with pure text content in
    // side of them. We also don't delete anything inside the root container.
    if (
      tag !== HostRoot &&
      (tag !== HostComponent ||
        (shouldDeleteUnhydratedTailInstances(fiber.type) &&
          !shouldSetTextContent(fiber.type, fiber.memoizedProps)))
    ) {
      const nextInstance = nextHydratableInstance;
      if (nextInstance) {
        warnIfUnhydratedTailNodes(fiber);
        throwOnHydrationMismatch(fiber);
      }
    }
  }
  popToNextHostParent(fiber);
  if (tag === SuspenseComponent) {
    nextHydratableInstance = skipPastDehydratedSuspenseInstance(fiber);
  } else if (tag === ActivityComponent) {
    nextHydratableInstance = skipPastDehydratedActivityInstance(fiber);
    // $FlowFixMe[constant-condition]
  } else if (supportsSingletons && tag === HostSingleton) {
    nextHydratableInstance = getNextHydratableSiblingAfterSingleton(
      fiber.type,
      nextHydratableInstance,
    );
  } else {
    nextHydratableInstance = hydrationParentFiber
      ? getNextHydratableSibling(fiber.stateNode)
      : null;
  }
  return true;
}
```

올라가며 호스트 부모를 찾는다.

```js
// ReactFiberHydrationContext.js L740-L757
function popToNextHostParent(fiber: Fiber): void {
  hydrationParentFiber = fiber.return;
  while (hydrationParentFiber) {
    switch (hydrationParentFiber.tag) {
      case HostComponent:
      case ActivityComponent:
      case SuspenseComponent:
        rootOrSingletonContext = false;
        return;
      case HostSingleton:
      case HostRoot:
        rootOrSingletonContext = true;
        return;
      default:
        hydrationParentFiber = hydrationParentFiber.return;
    }
  }
}
```

그리고 되돌릴 때는 다른 함수를 쓴다.

```js
// ReactFiberHydrationContext.js L857-L867
function resetHydrationState(): void {
  // $FlowFixMe[constant-condition]
  if (!supportsHydration) {
    return;
  }

  hydrationParentFiber = null;
  nextHydratableInstance = null;
  isHydrating = false;
  didSuspendOrErrorDEV = false;
}
```

## 동작 흐름

```text
 popHydrationState  HYD L759-834

 L761  !supportsHydration 이면
 L762    => return false                         ** [DEAD] — 늘 true 다 **

 L764  fiber !== hydrationParentFiber 이면
 L767    => return false
          주석 L765-766 - "We're deeper than the current hydration context,
                          inside an inserted tree."

 L769  !isHydrating 이면
 L773    popToNextHostParent(fiber)
 L774    isHydrating = true                      ★ **다시 켠다**
 L775    => return false
          주석 L770-772 - "If we're not currently hydrating but we're in a
            hydration context, then we were an insertion and now need to pop
            up reenter hydration of our siblings."

 L778  tag = fiber.tag          ★ 아래 갈래가 전부 이 값을 읽는다

 --- 남은 노드 검사 ---
 L781  [FLAG:supportsSingletons=true]
 L784    tag 가 HostRoot 도 HostSingleton 도 아니고
 L788    (HostComponent 이면서 꼬리를 안 지우거나 텍스트 내용인) 것도 아니면
 L793      nextInstance = nextHydratableInstance
 L794      있으면
 L795        warnIfUnhydratedTailNodes(fiber)
 L796        throwOnHydrationMismatch(fiber)     ★ **남은 것이 어긋남이다**
 L799  아니면                                     ** [DEAD] **
 L804-815  **논리적으로 같은** 블록 (아래에 따로 적는다)

 --- 커서 전진 ---
 L817  popToNextHostParent(fiber)
 L818  tag === SuspenseComponent 이면
 L819    nextHydratableInstance = skipPastDehydratedSuspenseInstance(fiber)
 L820  아니면 ActivityComponent 이면
 L821    nextHydratableInstance = skipPastDehydratedActivityInstance(fiber)
 L823  아니면 supportsSingletons 이고 HostSingleton 이면
 L824    nextHydratableInstance = getNextHydratableSiblingAfterSingleton(...)
 L828  아니면
 L829    nextHydratableInstance = hydrationParentFiber
              ? getNextHydratableSibling(fiber.stateNode)
              : null
 L833  => return true
```

```text
 ★★ 서버가 더 많이 보내도 어긋남이다

 L793-797  fiber 를 다 썼는데 커서에 노드가 남아 있으면 던진다

 => "클라이언트가 덜 그리는 것" 도 mismatch 다.
    서버 HTML 에만 있는 노드를 조용히 지우지 않는다

 ★★ 다만 **봐 주는 자리가 꽤 있다** (L784-791 의 조건)
     HostRoot 와 HostSingleton 은 아예 검사하지 않는다
     HostComponent 중에도
       shouldDeleteUnhydratedTailInstances 가 거짓이거나
       shouldSetTextContent 가 참이면 빼 준다

   그 첫째가 무엇인지 보면 구체적이다 - DOM L4466-4469
     shouldDeleteUnhydratedTailInstances(parentType) {
       return parentType !== 'form' && parentType !== 'button';
     }

   => 컨테이너 바로 안, `<html>`/`<head>`/`<body>` 안,
      `<form>` 안, `<button>` 안, 그리고 텍스트 내용을 가진 엘리먼트 안의
      남은 노드는 **조용히 봐 준다**
   주석(죽은 갈래 쪽 L800-803)이 이유를 적는다 -
     "We only do this deeper than head and body since they tend to have
      random other nodes in them. We also ignore components with pure text
      content inside of them. We also don't delete anything inside the
      root container."
   ★ 원문은 L802-803 에서 "content in / side of them" 으로 줄이 갈린다.
     한 단어가 줄바꿈으로 쪼개진 것이라 읽을 때 "inside" 로 붙여 읽는다
```

```text
 ★★ 수화 중에 "삽입" 이 섞여도 이어진다

 L769-776 이 그 자리다.

 수화하다 못 맞춘 서브트리는 클라이언트가 새로 만든다(삽입).
 그 동안 isHydrating 이 꺼져 있다가,
 그 fiber 를 **빠져나올 때 다시 켜져** 형제부터 이어서 수화한다

 => 페이지 하나가 통째로 수화되거나 통째로 버려지는 것이 아니라,
    서브트리 단위로 섞일 수 있다
    (마지막 문장은 내 귀결이다)
```

```text
 popToNextHostParent  HYD L740-757

 L741  hydrationParentFiber = fiber.return
 L742  while (hydrationParentFiber)
 L743    switch (tag)
 L744      case HostComponent
 L745      case ActivityComponent
 L746      case SuspenseComponent
 L747        rootOrSingletonContext = false
 L748        return
 L749      case HostSingleton
 L750      case HostRoot
 L751        rootOrSingletonContext = true
 L752        return
 L753      default
 L754        hydrationParentFiber = hydrationParentFiber.return

 ★ 호스트가 아닌 fiber(함수 컴포넌트 등)는 그냥 지나친다.
   DOM 에는 그것에 대응하는 노드가 없기 때문이다
   (마지막 문장은 내 판단이다)
```

```text
 ★ 커서를 전진시키는 방법이 넷이다  L818-832

 Suspense       skipPastDehydratedSuspenseInstance   경계 전체를 건너뛴다
 Activity       skipPastDehydratedActivityInstance   같다
 HostSingleton  getNextHydratableSiblingAfterSingleton
 그 밖          getNextHydratableSibling(fiber.stateNode)

 => 경계마다 "다음 형제" 의 뜻이 다르다.
    탈수 경계는 그 안이 통째로 서버 것이라 안으로 안 들어간다
    (마지막 문장은 내 판단이다)

 ★ 마지막 갈래는 전진이 아닐 수도 있다.
   hydrationParentFiber 가 없으면 **null 을 넣는다** (L829-831).
   L742-756 의 pop 이 꼭대기를 벗어났다는 뜻이다
   => 셋은 전진이고 하나는 끝낼 수도 있다
```

```text
 ★ 죽은 갈래와 산 갈래의 조건이 **논리적으로 같다**

 싱글톤 쪽   L785-792
   tag !== HostRoot && tag !== HostSingleton
   && !(tag === HostComponent && (!D || S))
 아닌 쪽     L805-808
   tag !== HostRoot && (tag !== HostComponent || (D && !S))

 드모르간으로 `!(HC && (!D || S)) === !HC || (D && !S)` 이므로
 뒤엣것의 둘째 항과 앞엣것의 셋째 항이 같다

 => 차이는 싱글톤 쪽에 `tag !== HostSingleton` 한 항이 더 있는 것뿐이다.
    미묘한 논리 차이가 있는 것이 아니다
```

```text
 resetHydrationState  HYD L857-867

 L863  hydrationParentFiber = null
 L864  nextHydratableInstance = null
 L865  isHydrating = false
 L866  didSuspendOrErrorDEV = false

 ★★ 전역 **일곱 중 넷만** 지운다.
   hydrationErrors / hydrationDiffRootDEV / rootOrSingletonContext 는 남는다

 남겨도 되는 이유는 **진입점 셋이 매번 다시 초기화하기 때문**이다
   L173-176 / L194-197 / L217-220
     hydrationErrors = null
     didSuspendOrErrorDEV = false
     hydrationDiffRootDEV = null
     rootOrSingletonContext = ...

 그리고 rootOrSingletonContext 는 pop 마다도 다시 쓴다 (L747 / L751).
 => 셋 다 다음 사용 전에 반드시 덮어써진다. 남겨도 낡을 일이 없다
```

```text
 ★★ 되감기용 포크가 따로 있다

 popHydrationStateOnInterruptedWork  HYD L878

 주석 L869-877 이 존재 이유를 통째로 적는다 -
   "Restore the hydration cursor when unwinding a HostComponent that already
    claimed a DOM node. This is a fork of popHydrationState that does all the
    same validity checks but restores the cursor to this fiber's DOM node
    instead of advancing past it. It also does NOT clear unhydrated tail nodes
    or throw on mismatches since we're unwinding, not completing.

    This is needed when replaySuspendedUnitOfWork calls unwindInterruptedWork
    before re-running beginWork on the same fiber, or when
    throwAndUnwindWorkLoop calls unwindWork on ancestor fibers."

 => 같은 검사를 하되 셋이 다르다
      커서를 **앞으로 안 보내고** 이 fiber 의 노드로 되돌린다
      남은 꼬리를 지우지 않는다
      어긋나도 던지지 않는다
 => 끝낸 것이 아니라 **되감는 중**이기 때문이다

 ★ 다만 커서를 되돌리는 것은 **HostComponent 일 때만**이다
     L902  fiber.tag === HostComponent && fiber.stateNode != null 이면
     L903    nextHydratableInstance = fiber.stateNode
   다른 tag 는 부모만 pop 하고 커서를 안 건드린다

 ★ 그리고 이 포크도 isHydrating 을 다시 켠다 (L888-895).
   위의 "삽입이 섞여도 이어진다" 와 같은 장치가 여기에도 있다

 ★★ 주석이 코드보다 넓게 말한다.
   L876-877 의 "or when throwAndUnwindWorkLoop calls unwindWork on ancestor
   fibers" 는 실제 호출처가 없다. 이 함수를 부르는 곳은
   WL L3187 (replaySuspendedUnitOfWork 의 case HostComponent) 하나뿐이고,
   UW 의 HostComponent 갈래에는 `// TODO: popHydrationState` 만 있다
   => 코드를 따르고 어긋남을 적어 둔다
```

## 결과가 쓰이는 곳

```text
 반환 boolean
      --> [completeWork]가 이 fiber 를 수화로 처리했는지 안다
      --> false 면 삽입으로 다룬다

 nextHydratableInstance
      --> 다음 fiber 가 집을 노드

 hydrationParentFiber / rootOrSingletonContext
      --> 다음 claim 이 어느 문맥인지 안다

 throwOnHydrationMismatch
      --> 남은 노드가 있으면 [02]로 간다
```

## 다루지 않는 것

`skipPastDehydratedSuspenseInstance`(L716) / `skipPastDehydratedActivityInstance`(L699)의 본문, `getNextHydratableSibling` / `getNextHydratableSiblingAfterSingleton` / `getFirstHydratableChildWithinSingleton`(호스트 설정)이 주석 노드와 공백을 어떻게 건너뛰는지, `shouldDeleteUnhydratedTailInstances` / `shouldSetTextContent` 가 태그별로 무엇을 돌려주는지, `warnIfUnhydratedTailNodes`(L837)가 DEV 트리에 꼬리를 쌓는 방식([04 DEV 어긋남 트리](../04_devDiff/README.md)에 있다), `popHydrationStateOnInterruptedWork`(L878)의 본문 전체와 `replaySuspendedUnitOfWork` / `unwindInterruptedWork`([렌더 루프](../../render-loop/README.md)에 있다), `supportsSingletons` 가 꺼진 빌드의 갈래(L799-816)는 같은 뼈대의 곁가지라 요약만 했다.
