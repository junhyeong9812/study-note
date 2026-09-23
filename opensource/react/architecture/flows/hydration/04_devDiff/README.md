# DEV 어긋남 트리

상위: [하이드레이션](../README.md)

에러 메시지 끝에 붙는 그 트리 모양 diff 를 만드는 자리다. **같은 트리가 던지는 에러에 붙거나 경고로 찍히거나 하는데, 둘 중 하나뿐**이다.

## 위치

트리 만들기 `packages/react-reconciler` / `src` / `ReactFiberHydrationContext.js` L97-L144 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHydrationContext.js#L97-L144))

성공 경로의 경고 `packages/react-reconciler` / `src` / `ReactFiberHydrationContext.js` L933-L969 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHydrationContext.js#L933-L969))

## 실제 코드

fiber 하나에 대해 루트까지 거슬러 올라가며 경로를 만든다.

```js
// ReactFiberHydrationContext.js L97-L144
function buildHydrationDiffNode(
  fiber: Fiber,
  distanceFromLeaf: number,
): HydrationDiffNode {
  if (fiber.return === null) {
    // We're at the root.
    if (hydrationDiffRootDEV === null) {
      hydrationDiffRootDEV = {
        fiber: fiber,
        children: [],
        serverProps: undefined,
        serverTail: [],
        distanceFromLeaf: distanceFromLeaf,
      };
    } else if (hydrationDiffRootDEV.fiber !== fiber) {
      throw new Error(
        'Saw multiple hydration diff roots in a pass. This is a bug in React.',
      );
    } else if (hydrationDiffRootDEV.distanceFromLeaf > distanceFromLeaf) {
      hydrationDiffRootDEV.distanceFromLeaf = distanceFromLeaf;
    }
    return hydrationDiffRootDEV;
  }
  const siblings = buildHydrationDiffNode(
    fiber.return,
    distanceFromLeaf + 1,
  ).children;
  // The same node may already exist in the parent. Since we currently always render depth first
  // and rerender if we suspend or terminate early, if a shared ancestor was added we should still
  // be inside of that shared ancestor which means it was the last one to be added. If this changes
  // we may have to scan the whole set.
  if (siblings.length > 0 && siblings[siblings.length - 1].fiber === fiber) {
    const existing = siblings[siblings.length - 1];
    if (existing.distanceFromLeaf > distanceFromLeaf) {
      existing.distanceFromLeaf = distanceFromLeaf;
    }
    return existing;
  }
  const newNode: HydrationDiffNode = {
    fiber: fiber,
    children: [],
    serverProps: undefined,
    serverTail: [],
    distanceFromLeaf: distanceFromLeaf,
  };
  siblings.push(newNode);
  return newNode;
}
```

> The same node may already exist in the parent. Since we currently always render depth first and rerender if we suspend or terminate early, if a shared ancestor was added we should still be inside of that shared ancestor which means it was the last one to be added. **If this changes we may have to scan the whole set.**

## 동작 흐름

```text
 buildHydrationDiffNode  HYD L97-144

 L101  fiber.return === null 이면          (루트다)
 L103    hydrationDiffRootDEV 가 null 이면
 L104      새 노드를 만들어 담는다
 L111    아니면 그 노드의 fiber 가 다르면
 L112      throw new Error(
 L113        'Saw multiple hydration diff roots in a pass. This is a bug in React.')
 L115    아니면 distanceFromLeaf 가 더 작으면
 L116      hydrationDiffRootDEV.distanceFromLeaf = distanceFromLeaf
 L118    => return hydrationDiffRootDEV

 L120  siblings = buildHydrationDiffNode(fiber.return, distanceFromLeaf + 1).children
        ★ **재귀로 루트까지 올라가며 경로를 만든다**

 L128  마지막 형제가 같은 fiber 이면
 L129    existing 을 재사용하고 distanceFromLeaf 만 줄인다 (L130-132)
 L133    => return existing

 L135  아니면 새 노드를 만들어 (L135-141)
 L142    siblings.push(newNode)
 L143    => return newNode
```

```text
 ★ 마지막 형제만 보면 되는 근거가 주석에 있다  L124-127

 "The same node may already exist in the parent. Since we currently always
  render depth first and rerender if we suspend or terminate early, if a
  shared ancestor was added we should still be inside of that shared ancestor
  which means it was the last one to be added. If this changes we may have to
  scan the whole set."

 => 지금은 깊이 우선이라 마지막 것만 보면 된다.
    그 전제가 바뀌면 전부 훑어야 한다고 미리 적어 두었다
```

```text
 ★ 이 함수는 __DEV__ 가드가 함수 **밖**에 있다

 부르는 쪽이 전부 `if (__DEV__)` 안이지만 (L240 / L271 / L445 / L595 등),
 함수 본문에는 가드가 없다

 => L112-114 의 throw 가 프로덕션 번들에도 들어간다.
    닿을 일이 없어도 살아 있는 던지기다
```

```text
 ★ 트리를 채우는 세 가지

 serverProps   속성이 다르다        L446 (싱글톤) 등에서 담는다
 serverTail    남은 꼬리 노드들      warnIfUnhydratedTailNodes L844
 children      경로                  L142 에서 쌓인다

 warnIfUnhydratedTailNodes(L837)는 **남은 형제를 전부** 훑는다
   L840  while (nextInstance)
   L844    diffNode.serverTail.push(description)
   L846    description.type === 'Suspense' 이면
   L849      getNextHydratableInstanceAfterSuspenseInstance 로 건너뛴다
   L851    아니면 getNextHydratableSibling

 => [03]의 "서버가 더 많이 보냈다" 에러가 **무엇이 남았는지** 를 나열할 수 있는 이유다
```

```text
 ★★ 같은 트리가 두 길 중 하나로만 간다

 던지는 길   [02] throwOnHydrationMismatch
               L393  diffRoot = hydrationDiffRootDEV
               L395  hydrationDiffRootDEV = null      ★ 소비
               L396  diff = describeDiff(diffRoot)
               L412  에러 문구 끝에 붙인다

 경고하는 길 emitPendingHydrationWarnings  L933
               L934  [__DEV__]
               수화가 **끝까지 성공했는데** 차이만 있었을 때
               L944-947  가장 깊은 첫 자식까지 내려가 diffOwner 를 잡고
               L949-951  runWithFiberInDEV 로 경고를 찍는다
                 "A tree hydrated but some attributes of the server rendered
                  HTML didn't match the client properties. This won't be
                  patched up."
               주석 L935-936 - "If we haven't yet thrown any hydration errors
                 by the time we reach the end we've successfully hydrated,
                 however, we might still have DEV-only mismatches that we
                 log now."
               ★ 그 뒤로 이어지는 원인 다섯(L954-958)이 [02]의 던지는 문구와
                 **글자까지 같다**. 링크도 같다 (L963)

 => 먼저 소비하는 쪽이 null 로 만들므로 **둘 다 나오지는 않는다**
 ★ 그리고 이 경고가 말한다 - "This won't be patched up."
    속성 차이는 고쳐 주지 않는다. 알려만 준다
```

```text
 ★★ 서스펜드 뒤에는 트리가 아예 안 만들어진다

 didSuspendOrErrorDEV 를 세우는 곳이 둘뿐이다 - THROW L392 / L556
 (markDidThrowWhileHydratingDEV, HYD L156-160)

 그 뒤로 warnNonHydratedInstance 는 곧장 나간다
   L232  didSuspendOrErrorDEV 이면
   L236    return
   주석 L233-235 - "Inside a boundary that already suspended. We're currently
     rendering the siblings of a suspended node. The mismatch may be due to
     the missing data, so it's probably a false positive."

 같은 플래그가 L269 / L435 / L594 도 가른다

 => 서스펜드한 경계 안에서는 어긋남이 **데이터가 없어서** 생긴 가짜일 수 있다.
    그래서 diff 를 안 모은다.
    던지기는 여전히 던지지만 메시지의 diff 가 빈 채로 나간다
```

## 결과가 쓰이는 곳

```text
 describeDiff(diffRoot)
      --> [02]의 에러 문구 끝에 붙는다

 emitPendingHydrationWarnings
      --> 수화가 성공했을 때의 console.error
      --> [completeWork]가 부른다

 hydrationDiffRootDEV
      --> 둘 중 먼저 쓰는 쪽이 소비한다. 한 번만 나온다
```

## 다루지 않는 것

`describeDiff` / `HydrationDiffNode` 타입(`ReactFiberHydrationDiffs`)이 트리를 사람이 읽는 문자열로 바꾸는 방식과 `distanceFromLeaf` 를 실제로 쓰는 자리, `diffHydratedPropsForDevWarnings` / `diffHydratedTextForDevWarnings`(호스트 설정)가 무엇을 비교하는지와 `suppressHydrationWarning` 이 그것을 끄는 경로, `describeHydratableInstanceForDevWarnings` 가 후보 노드를 묘사하는 형식, `emitPendingHydrationWarnings`(L933) 본문의 나머지와 그것을 부르는 CW 세 자리, `upgradeHydrationErrorsToRecoverable`(L907)이 에러를 복구 가능으로 올려 `onRecoverableError` 로 보내는 길([커밋](../../commit/README.md)에 있다)은 같은 뼈대의 곁가지라 요약만 했다.
