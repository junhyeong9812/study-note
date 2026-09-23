# 짝 만들기

상위: [Fiber 라는 자료구조](../README.md)

트리를 두 벌 쓰는 장치가 이 함수 하나다. 그리고 이 지도의 흐름 둘이 각각 참조하던 자리가 **여기 한 함수 안에** 있다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiber.js` L327-L444 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiber.js#L327-L444))

## 실제 코드

짝이 없으면 만들고, 있으면 돌려쓴다. 어느 쪽이든 마지막은 같다.

```js
// ReactFiber.js L327-L444
export function createWorkInProgress(current: Fiber, pendingProps: any): Fiber {
  let workInProgress = current.alternate;
  if (workInProgress === null) {
    // We use a double buffering pooling technique because we know that we'll
    // only ever need at most two versions of a tree. We pool the "other" unused
    // node that we're free to reuse. This is lazily created to avoid allocating
    // extra objects for things that are never updated. It also allow us to
    // reclaim the extra memory if needed.
    workInProgress = createFiber(
      current.tag,
      pendingProps,
      current.key,
      current.mode,
    );
    workInProgress.elementType = current.elementType;
    workInProgress.type = current.type;
    workInProgress.stateNode = current.stateNode;

    if (__DEV__) {
      // DEV-only fields

      workInProgress._debugOwner = current._debugOwner;
      workInProgress._debugStack = current._debugStack;
      workInProgress._debugTask = current._debugTask;
      workInProgress._debugHookTypes = current._debugHookTypes;
    }

    workInProgress.alternate = current;
    current.alternate = workInProgress;
  } else {
    workInProgress.pendingProps = pendingProps;
    // Needed because Blocks store data on type.
    workInProgress.type = current.type;

    // We already have an alternate.
    // Reset the effect tag.
    workInProgress.flags = NoFlags;

    // The effects are no longer valid.
    workInProgress.subtreeFlags = NoFlags;
    workInProgress.deletions = null;

    if (enableOptimisticKey) {
      // For optimistic keys, the Fibers can have different keys if one is optimistic
      // and the other one is filled in.
      workInProgress.key = current.key;
    }

    if (enableProfilerTimer) {
      // We intentionally reset, rather than copy, actualDuration & actualStartTime.
      // This prevents time from endlessly accumulating in new commits.
      // This has the downside of resetting values for different priority renders,
      // But works for yielding (the common case) and should support resuming.
      workInProgress.actualDuration = -0;
      workInProgress.actualStartTime = -1.1;
    }
  }

  // Reset all effects except static ones.
  // Static effects are not specific to a render.
  workInProgress.flags = current.flags & StaticMask;
  workInProgress.childLanes = current.childLanes;
  workInProgress.lanes = current.lanes;

  workInProgress.child = current.child;
  workInProgress.memoizedProps = current.memoizedProps;
  workInProgress.memoizedState = current.memoizedState;
  workInProgress.updateQueue = current.updateQueue;

  // Clone the dependencies object. This is mutated during the render phase, so
  // it cannot be shared with the current fiber.
  const currentDependencies = current.dependencies;
  workInProgress.dependencies =
    currentDependencies === null
      ? null
      : __DEV__
        ? {
            lanes: currentDependencies.lanes,
            firstContext: currentDependencies.firstContext,
            _debugThenableState: currentDependencies._debugThenableState,
          }
        : {
            lanes: currentDependencies.lanes,
            firstContext: currentDependencies.firstContext,
          };

  // These will be overridden during the parent's reconciliation
  workInProgress.sibling = current.sibling;
  workInProgress.index = current.index;
  workInProgress.ref = current.ref;
  workInProgress.refCleanup = current.refCleanup;

  if (enableProfilerTimer) {
    workInProgress.selfBaseDuration = current.selfBaseDuration;
    workInProgress.treeBaseDuration = current.treeBaseDuration;
  }

  if (__DEV__) {
    workInProgress._debugInfo = current._debugInfo;
    workInProgress._debugNeedsRemount = current._debugNeedsRemount;
    switch (workInProgress.tag) {
      case FunctionComponent:
      case SimpleMemoComponent:
        workInProgress.type = resolveFunctionForHotReloading(current.type);
        break;
      case ClassComponent:
        workInProgress.type = resolveClassForHotReloading(current.type);
        break;
      case ForwardRef:
        workInProgress.type = resolveForwardRefForHotReloading(current.type);
        break;
      default:
        break;
    }
  }

  return workInProgress;
}
```

> We use a **double buffering pooling** technique because we know that we'll only ever need at most two versions of a tree. We pool the "other" unused node that we're free to reuse. This is **lazily created** to avoid allocating extra objects for things that are never updated.

그리고 이 세 줄이 흐름 둘의 전제다.

```js
// ReactFiber.js L385-L394
  // Reset all effects except static ones.
  // Static effects are not specific to a render.
  workInProgress.flags = current.flags & StaticMask;
  workInProgress.childLanes = current.childLanes;
  workInProgress.lanes = current.lanes;

  workInProgress.child = current.child;
  workInProgress.memoizedProps = current.memoizedProps;
  workInProgress.memoizedState = current.memoizedState;
  workInProgress.updateQueue = current.updateQueue;
```

> Reset all effects except static ones. Static effects are not specific to a render.

```js
// ReactFiber.js L396-L411
  // Clone the dependencies object. This is mutated during the render phase, so
  // it cannot be shared with the current fiber.
  const currentDependencies = current.dependencies;
  workInProgress.dependencies =
    currentDependencies === null
      ? null
      : __DEV__
        ? {
            lanes: currentDependencies.lanes,
            firstContext: currentDependencies.firstContext,
            _debugThenableState: currentDependencies._debugThenableState,
          }
        : {
            lanes: currentDependencies.lanes,
            firstContext: currentDependencies.firstContext,
          };
```

> Clone the dependencies object. This is mutated during the render phase, so it cannot be shared with the current fiber.

## 동작 흐름

```text
 createWorkInProgress(current, pendingProps)   FIBER L327-444

 L328  workInProgress = current.alternate

 --- 짝이 없으면 ---
 L329  null 이면
 L335    workInProgress = createFiber(...)      (인자는 L336-339)
 L341    elementType / L342 type / L343 stateNode 복사
 L345    [__DEV__]
 L348      _debugOwner / L349 _debugStack / L350 _debugTask / L351 _debugHookTypes
 L354    workInProgress.alternate = current
 L355    current.alternate = workInProgress     ★ **서로 건다**

 --- 있으면 ---
 L356  아니면
 L357    pendingProps 를 새것으로
 L359    type = current.type
          주석 L358 - "Needed because Blocks store data on type."
 L363    flags = NoFlags                        ★ 아래에서 덮어써진다
 L366    subtreeFlags = NoFlags
 L367    deletions = null
 L369    [FLAG:enableOptimisticKey]
 L372      key = current.key
 L375    [FLAG:enableProfilerTimer]
 L380      actualDuration = -0
 L381      actualStartTime = -1.1

 --- 여기부터 공통 ---
 L387  flags = current.flags & StaticMask       ★★ 이 한 줄이 핵심이다
 L388  childLanes / L389 lanes 복사
 L391  child 복사
 L392  memoizedProps / L393 memoizedState / L394 updateQueue 복사
 L399  dependencies 를 **복제** (L399-411)
 L414  sibling / L415 index / L416 ref / L417 refCleanup 복사
        주석 L413 - "These will be overridden during the parent's reconciliation"
 L419  [FLAG:enableProfilerTimer]
 L420    selfBaseDuration / L421 treeBaseDuration 복사
 L424  [__DEV__]
 L425    _debugInfo / L426 _debugNeedsRemount 복사
 L427    핫 리로딩용 type 해소 switch (L427-440)
 L443  => return workInProgress
```

```text
 ★★★ L387 이 이 지도의 흐름 둘이 각각 가리키던 줄이다

 workInProgress.flags = current.flags & StaticMask
 주석 L385-386 - "Reset all effects except static ones.
                 Static effects are not specific to a render."

 [컨텍스트 전파]가 말한 것
   DidPropagateContext / NeedsPropagation 은 StaticMask 에 **없다**
   => 렌더 한 번만 살고 여기서 자동으로 사라진다
   => 그래서 명시적으로 지우는 코드가 없다

 [클래스 컴포넌트]가 말한 것
   LayoutStatic 은 StaticMask 에 **있다**
   => componentDidMount 가 있다는 사실이 렌더를 넘어 산다

 => 같은 한 줄을 두 문서가 반대편에서 인용하고 있었다
```

```text
 ★★ L399-411 이 [컨텍스트 전파]의 전제다

 주석 L396-397 - "Clone the dependencies object. This is mutated during the
 render phase, so it cannot be shared with the current fiber."

 복제하기 때문에 current 쪽에 **옛 의존 목록이 남는다**.
 그래서 checkIfContextChanged(current.dependencies) 가 성립한다

 ★ 복제하는 칸이 둘뿐이다 - lanes 와 firstContext
   (DEV 는 _debugThenableState 하나 더)
   => firstContext 포인터는 같은 노드를 가리키고,
      prepareToReadContext 가 WIP 쪽만 null 로 지운다
   (마지막 줄은 [컨텍스트 전파]에서 확인한 것이다)
```

```text
 ★ 이중 버퍼링을 왜 이렇게 하는지 주석이 적는다  L330-334

 "We use a double buffering pooling technique because we know that we'll only
  ever need at most two versions of a tree. We pool the "other" unused node
  that we're free to reuse. This is lazily created to avoid allocating extra
  objects for things that are never updated. It also allow us to reclaim the
  extra memory if needed."

 ★ 세 가지를 말한다
   (가) 트리는 **최대 두 벌**이면 충분하다
   (나) 짝은 **게을리** 만든다 - 갱신된 적 없는 fiber 는 짝이 없다
   (다) 필요하면 짝을 버려 메모리를 되찾을 수 있다
```

```text
 ★★ L363 은 쓸모없다

 재사용 갈래에서 flags = NoFlags 로 두는데,
 L387 이 곧바로 `= current.flags & StaticMask` 로 **덮어쓴다** (|= 가 아니다).
 그 사이에 flags 를 읽거나 쓰는 줄이 하나도 없다

 => 재사용 갈래도 반드시 L387 을 지나므로 L363 의 효과가 남지 않는다
 ※ 내가 두 줄 사이를 전수로 훑어 확인한 것이다. 주석은 없다
```

```text
 ★ 프로파일러 시간만 복사가 아니라 리셋이다

 L380-381  actualDuration = -0 / actualStartTime = -1.1
 주석 L376-379 -
   "We intentionally reset, rather than copy, actualDuration & actualStartTime.
    This prevents time from endlessly accumulating in new commits.
    This has the downside of resetting values for different priority renders,
    But works for yielding (the common case) and should support resuming."

 ★ 반면 selfBaseDuration / treeBaseDuration 은 **복사한다** (L420-421).
   전자는 "이번 렌더에 쓴 시간", 후자는 "기준 시간" 이라 성격이 다르다
   (마지막 줄은 [01]의 주석을 보고 내가 붙인 것이다)

 ★ -0 과 -1.1 이라는 값이 특이하다. 이유는 주석에 없다
```

```text
 ★ child 는 복사하고 sibling 은 "덮어써질 것" 이라 적는다

 L391  child = current.child
 L414  sibling = current.sibling
 L415  index / L416 ref / L417 refCleanup
 주석 L413 - "These will be overridden during the parent's reconciliation"

 sibling·index·ref 에는 그 단서가 붙어 있고 child 에는 없다.
 child 는 조정이 시작되기 전까지 옛 자식을 가리켜야 하기 때문으로 보인다
 ※ 뒷문장은 내 추측이다
```

```text
 ★ 어느 fiber 구현을 쓰는지도 플래그다

 FIBER L303-305
   const createFiber = enableObjectFiber
     ? createFiberImplObject
     : createFiberImplClass;

 [FLAG:enableObjectFiber=false] 라 **클래스 구현**을 쓴다.
 createFiberImplObject(L236)는 이 빌드에서 [DEAD] 다
 ※ 두 구현의 차이는 안 읽었다
```

## 결과가 쓰이는 곳

```text
 반환 workInProgress
      --> [렌더 루프]가 이것을 새 트리의 노드로 삼는다
      --> [자식 조정]의 useFiber 가 재사용할 때 부른다

 alternate 양방향 링크
      --> 커밋이 root.current 를 바꾸면 역할이 뒤집힌다
      --> 두 트리가 서로를 가리킨 채 번갈아 산다

 flags & StaticMask
      --> 렌더 1회짜리 플래그가 여기서 사라진다

 복제된 dependencies
      --> [컨텍스트 전파]의 값 비교가 성립한다
```

## 다루지 않는 것

`StaticMask`(`ReactFiberFlags.js` L137)에 들어 있는 플래그 전체 목록, `createFiberImplClass`(FIBER L226) / `createFiberImplObject`(L236) 두 구현의 차이와 `enableObjectFiber` 실험의 배경, `resetWorkInProgress`(FIBER L447)가 "두 번째 패스" 를 위해 하는 일과 그 호출처, `createHostRootFiber`(FIBER L536)가 `mode` 를 정하는 규칙, `resolveFunctionForHotReloading` / `resolveClassForHotReloading` / `resolveForwardRefForHotReloading`(`ReactFiberHotReloading.js`)의 본문, `enableOptimisticKey` 가 무엇을 위한 것인지, `actualDuration` 의 `-0` 과 `actualStartTime` 의 `-1.1` 이라는 초기값의 사정은 이 문서의 범위 밖이다.
