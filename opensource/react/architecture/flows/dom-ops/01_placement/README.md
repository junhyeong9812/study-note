# 붙일 자리 찾기

상위: [DOM 조작](../README.md)

새 노드를 **어디에** 넣을지 정한다. 그 답을 찾는 함수가 이 지도 전체에서 가장 솔직한 주석을 달고 있다 — 스스로 지수 탐색이라고 적는다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberCommitHostEffects.js` L328-L385 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitHostEffects.js#L328-L385))

`packages/react-reconciler` / `src` / `ReactFiberCommitHostEffects.js` L499-L594 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitHostEffects.js#L499-L594))

## 실제 코드

찾는 함수 전문. 주석이 먼저 한계를 밝힌다.

```js
// ReactFiberCommitHostEffects.js L328-L385
function getHostSibling(fiber: Fiber): ?Instance {
  // We're going to search forward into the tree until we find a sibling host
  // node. Unfortunately, if multiple insertions are done in a row we have to
  // search past them. This leads to exponential search for the next sibling.
  // TODO: Find a more efficient way to do this.
  let node: Fiber = fiber;
  siblings: while (true) {
    // If we didn't find anything, let's try the next sibling.
    while (node.sibling === null) {
      if (node.return === null || isHostParent(node.return)) {
        // If we pop out of the root or hit the parent the fiber we are the
        // last sibling.
        return null;
      }
      // $FlowFixMe[incompatible-type] found when upgrading Flow
      node = node.return;
    }
    node.sibling.return = node.return;
    node = node.sibling;
    while (
      node.tag !== HostComponent &&
      node.tag !== HostText &&
      node.tag !== DehydratedFragment
    ) {
      // If this is a host singleton we go deeper if it's not a special
      // singleton scope. If it is a singleton scope we skip over it because
      // you only insert against this scope when you are already inside of it
      if (
        // $FlowFixMe[constant-condition]
        supportsSingletons &&
        node.tag === HostSingleton &&
        isSingletonScope(node.type)
      ) {
        continue siblings;
      }

      // If it is not host node and, we might have a host node inside it.
      // Try to search down until we find one.
      if (node.flags & Placement) {
        // If we don't have a child, try the siblings instead.
        continue siblings;
      }
      // If we don't have a child, try the siblings instead.
      // We also skip portals because they are not part of this host tree.
      if (node.child === null || node.tag === HostPortal) {
        continue siblings;
      } else {
        node.child.return = node;
        node = node.child;
      }
    }
    // Check if this host node is stable or about to be placed.
    if (!(node.flags & Placement)) {
      // Found it!
      return node.stateNode;
    }
  }
}
```

> We're going to search forward into the tree until we find a sibling host node. Unfortunately, if multiple insertions are done in a row we have to search past them. This leads to **exponential search** for the next sibling. **TODO: Find a more efficient way to do this.**

누구를 호스트 부모로 치는가.

```js
// ReactFiberCommitHostEffects.js L310-L322
function isHostParent(fiber: Fiber): boolean {
  return (
    fiber.tag === HostComponent ||
    fiber.tag === HostRoot ||
    // $FlowFixMe[constant-condition]
    (supportsResources ? fiber.tag === HostHoistable : false) ||
    // $FlowFixMe[constant-condition]
    (supportsSingletons
      ? fiber.tag === HostSingleton && isSingletonScope(fiber.type)
      : false) ||
    fiber.tag === HostPortal
  );
}
```

그리고 부모를 찾아 넣는 쪽.

```js
// ReactFiberCommitHostEffects.js L538-L593
  switch (hostParentFiber.tag) {
    case HostSingleton: {
      // $FlowFixMe[constant-condition]
      if (supportsSingletons) {
        const parent: Instance = hostParentFiber.stateNode;
        const before = getHostSibling(finishedWork);
        // We only have the top Fiber that was inserted but we need to recurse down its
        // children to find all the terminal nodes.
        insertOrAppendPlacementNode(
          finishedWork,
          before,
          parent,
          parentFragmentInstances,
        );
        break;
      }
      // Fall through
    }
    case HostComponent: {
      const parent: Instance = hostParentFiber.stateNode;
      if (hostParentFiber.flags & ContentReset) {
        // Reset the text content of the parent before doing any insertions
        resetTextContent(parent);
        // Clear ContentReset from the effect tag
        hostParentFiber.flags &= ~ContentReset;
      }

      const before = getHostSibling(finishedWork);
      // We only have the top Fiber that was inserted but we need to recurse down its
      // children to find all the terminal nodes.
      insertOrAppendPlacementNode(
        finishedWork,
        before,
        parent,
        parentFragmentInstances,
      );
      break;
    }
    case HostRoot:
    case HostPortal: {
      const parent: Container = hostParentFiber.stateNode.containerInfo;
      const before = getHostSibling(finishedWork);
      insertOrAppendPlacementNodeIntoContainer(
        finishedWork,
        before,
        parent,
        parentFragmentInstances,
      );
      break;
    }
    default:
      throw new Error(
        'Invalid host parent fiber. This error is likely caused by a bug ' +
          'in React. Please file an issue.',
      );
  }
```

## 동작 흐름

```text
 getHostSibling  CHE L328-385

 L333  node = fiber
 L334  siblings: while (true)                 ★ 레이블 붙은 루프다

       --- (가) 형제가 없으면 위로 ---
 L336    while (node.sibling === null)
 L337      node.return === null 이거나 isHostParent(node.return) 이면
 L340        => return null                   ** 마지막 형제다. append 하라는 뜻 **
 L343      node = node.return

       --- (나) 형제로 간다 ---
 L345    node.sibling.return = node.return
 L346    node = node.sibling

       --- (다) 호스트 노드가 나올 때까지 내려간다 ---
 L347    while (node.tag 가 HostComponent 도 HostText 도
                DehydratedFragment 도 아닌 동안)
 L355      다음 셋이 모두 참이면 (L357-359)
             supportsSingletons / node.tag === HostSingleton
             / isSingletonScope(node.type)
 L361        continue siblings
 L366      node.flags & Placement 이면
 L368        continue siblings
 L372      node.child === null 이거나 node.tag === HostPortal 이면
 L373        continue siblings
 L375      node.child.return = node
 L376      node = node.child

       --- (라) 찾았나 ---
 L380    !(node.flags & Placement) 이면
 L382      => return node.stateNode           ** 이 앞에 넣어라 **
          아니면 L334 로 되돌아간다
```

```text
 ★★ continue siblings 가 셋인데 이유가 다 다르다

 L361  싱글톤 스코프다
       주석 L352-354 - "If this is a host singleton we go deeper if it's not a
       special singleton scope. If it is a singleton scope we skip over it
       because you only insert against this scope when you are already
       inside of it"

 L368  그 노드도 Placement 가 붙어 있다
       아직 DOM 에 없으니 "이 앞에" 의 기준이 될 수 없다

 L373  포털이거나 자식이 없다
       주석 L370-371 - "We also skip portals because they are not part of
       this host tree."
```

```text
 ★★★ 왜 비싸지는가

 L366 이 핵심이다. 연속으로 여러 개를 삽입하면 그것들이 전부 Placement 를 갖는다.
 그런데 이 함수는 **앞으로만** 훑는다 (L345-346).
 그리고 Placement 는 놓은 **뒤에** 꺼진다
   CMW L2768  flags & Placement 이면
   CMW L2769    commitHostPlacement(finishedWork)
   CMW L2774    finishedWork.flags &= ~Placement
   주석 CMW L2770-2771 - "Clear the "placement" from effect tag so that we
     know that this is inserted, before any life-cycles like
     componentDidMount gets called."

 => 이미 놓인 **앞** 형제는 커서 뒤에 있어 다시 안 지난다.
    비싼 쪽은 i 번째 삽입이 아직 안 놓인 **뒤쪽** 형제들을 지나는 것이다
```

```text
 ★★ 주석의 단어가 코드와 다르다

 주석 L331 은 "exponential search" 라고 쓴다.
 그런데 한 번의 호출은 같은 fiber 를 다시 보지 않는다 -
 L366-369 가 Placement 서브트리를 **내려가지 않고 통째로 건너뛴다**

 호출 하나가 훑는 fiber 수를 k 라 하면 O(k) 이고,
 연속 삽입 n 개의 합이 n + (n-1) + ... 이라
 **제곱(O(n^2))이다. 지수가 아니다**

 => 코드를 따르고 어긋남을 적어 둔다.
    TODO 가 붙어 있는 것("Find a more efficient way to do this")은 그대로 유효하다
```

```text
 ★ 소스에 잘못 놓인 주석이 하나 있다

 L367  // If we don't have a child, try the siblings instead.

 이 문장이 Placement 갈래 안에 있어 말이 안 맞는다.
 같은 문장이 L370 에 제자리로 한 번 더 있다 (자식이 없을 때의 갈래)
```

```text
 ★ 반환값 null 은 "못 찾았다" 가 아니다

 L340 의 null 은 **마지막 형제라는 뜻**이다.
 부르는 쪽이 before 가 null 이면 insertBefore 대신 appendChild 를 쓴다.
 같은 모양이 두 함수에 있다

   컨테이너용  insertOrAppendPlacementNodeIntoContainer  L387
     L397  before 이면
     L398    insertInContainerBefore(parent, stateNode, before)
     L399  아니면
     L400    appendChildToContainer(parent, stateNode)

   보통       insertOrAppendPlacementNode               L446
     L456  before 이면
     L457    insertBefore(parent, stateNode, before)
     L458  아니면
     L459    appendChild(parent, stateNode)

 ★ 둘 다 L394 / L453 에서 `tag === HostComponent || tag === HostText` 로
   호스트 노드인지 먼저 본다. 아니면 자식으로 내려간다
```

```text
 isHostParent  CHE L310-322 — 다섯을 호스트 부모로 친다

 L312  HostComponent
 L313  HostRoot
 L315  [FLAG:supportsResources=true]  HostHoistable
 L317  [FLAG:supportsSingletons=true] HostSingleton 이면서 isSingletonScope 인 것
 L320  HostPortal

 ★ isSingletonScope 는 딱 한 가지다 - CFG L1170-1172
     export function isSingletonScope(type: string): boolean {
       return type === 'head';
     }
   => `<html>` 과 `<body>` 는 HostSingleton 이지만 **호스트 부모가 아니다**.
      `<head>` 만 그렇다

 ★ HostText 가 없다. 텍스트 노드는 부모가 될 수 없다
 ★ 플래그 둘이 이 빌드에서 true 라 다섯 다 산다
 (마지막 두 문장은 내 관찰이다)
```

```text
 commitPlacement  CHE L499-594

 --- 호스트 부모를 찾는다 ---
 L503  parentFiber = finishedWork.return
 L504  while (parentFiber !== null)
 L505    [FLAG:enableFragmentRefs=true] isFragmentInstanceParent 이면 모아 둔다
 L513    isHostParent(parentFiber) 이면
 L514      hostParentFiber = parentFiber
 L515      break
 L517    parentFiber = parentFiber.return

 L521  !supportsMutation 이면                  ** [DEAD] — 늘 true 다 **
 L528    => return
 L531  hostParentFiber == null 이면
 L532    => throw
 L533      'Expected to find a host parent. This error is likely caused by a
 L534       bug in React. Please file an issue.'

 --- 넣는다 ---
 L538  switch (hostParentFiber.tag)
 L539    case HostSingleton
 L541      supportsSingletons 이면                (이 빌드에서 늘 참)
 L543        before = getHostSibling(finishedWork)
 L546        insertOrAppendPlacementNode(...)
 L552        break
 L554      // Fall through                       ** [DEAD] **
 L556    case HostComponent
 L557      parent = hostParentFiber.stateNode
 L558      hostParentFiber.flags & ContentReset 이면
 L560        resetTextContent(parent)
 L562        hostParentFiber.flags &= ~ContentReset   ★ 커밋 중에 플래그를 끈다
 L565      before = getHostSibling(finishedWork)
 L568      insertOrAppendPlacementNode(...)

 L576    case HostRoot
 L577    case HostPortal
 L578      parent = hostParentFiber.stateNode.containerInfo   ★ stateNode 가 아니다
 L579      before = getHostSibling(finishedWork)
 L580      insertOrAppendPlacementNodeIntoContainer(...)
            ★ 이 함수의 **유일한 호출처**다

 L588    default
 L589      => throw 'Invalid host parent fiber. This error is likely caused by
                     a bug in React. Please file an issue.'
```

```text
 ★ fallthrough 가 이 빌드에서 죽어 있다

 L554 의 `// Fall through` 는 L541 의 `if (supportsSingletons)` 가
 거짓일 때만 닿는다. 이 빌드에서 그 값이 true 라 L552 에서 break 한다

 [커밋 이펙트]의 Fragment fallthrough 와 **같은 종류**다 —
 플래그가 꺼진 빌드(react-art, react-native, test-renderer)를 위한 대비책이다

 ※ 의도적 fallthrough 자체는 이 파일들에서 흔하다. 세어 보면 스무 곳이 넘는다.
   드문 것은 "언제나 흘러가는" 것이고, 그런 예가 [업데이트 큐]의 CaptureUpdate 다
```

```text
 ★ 삽입 전에 부모의 텍스트를 지운다

 L558-563  부모에 ContentReset 이 붙어 있으면
   L560  resetTextContent(parent)         -> setTextContent(el, '')
   L562  hostParentFiber.flags &= ~ContentReset

 주석 L559 - "Reset the text content of the parent before doing any insertions"
 주석 L561 - "Clear ContentReset from the effect tag"

 ★★ 플래그를 끄는 이유가 다른 파일의 TODO 에 적혀 있다. 이 이음매에서 가장 강한 주석이다

 부모 자신의 ContentReset 처리가 **자식을 놓은 뒤**에 돈다
   CMW L2240  finishedWork.flags & ContentReset 이면
   CMW L2241    commitHostResetTextContent(finishedWork)

 그래서 CHE L562 가 플래그를 끄지 않으면 **방금 넣은 자식이 지워진다**

 CMW L2234-2239 가 그것을 위험이라고 적는다 -
   "TODO: ContentReset gets cleared by the children during the commit
    phase. This is a refactor hazard because it means we must read
    flags the flags after `commitReconciliationEffects` has already run;
    the order matters. We should refactor so that ContentReset does not
    rely on mutating the flag during commit. Like by setting a flag
    during the render phase instead."

 ★ 원문에 "read flags the flags" 오타가 있다
```

```text
 ★ 서브트리 하나에 대해 재귀한다

 주석 L544-545 / L566-567 이 같은 말을 두 번 한다 -
   "We only have the top Fiber that was inserted but we need to recurse down
    its children to find all the terminal nodes."

 Placement 는 서브트리의 꼭대기에만 붙는다.
 그래서 insertOrAppendPlacementNode 가 아래로 내려가며
 **호스트 노드가 나올 때까지** 찾아 전부 넣는다
```

## 결과가 쓰이는 곳

```text
 getHostSibling 의 반환값
      --> before 인자가 된다
      --> null 이면 append, 아니면 insertBefore

 insertOrAppendPlacementNode
      --> 실제로 [02]가 만든 DOM 노드를 부모에 넣는다

 ContentReset 플래그
      --> 지우고 나면 꺼진다
```

## 다루지 않는 것

`insertOrAppendPlacementNode`(CHE L446) / `insertOrAppendPlacementNodeIntoContainer`(CHE L387)가 서브트리를 내려가며 재귀하는 본문, `commitImmutablePlacementNodeToFragmentInstances`(CHE L596)와 `enableFragmentRefs` 계열이 Fragment 인스턴스에 자식을 알리는 경로, `isSingletonScope` / `HostSingleton` 이 `<html>` `<head>` `<body>` 를 다루는 방식, `ContentReset` 플래그를 세우는 렌더 단계 자리, `DehydratedFragment` 를 형제로 인정하는 수화 쪽 사정, `getHostSibling` 의 비용을 실제로 재 본 벤치마크는 같은 뼈대의 곁가지라 요약만 했다.
