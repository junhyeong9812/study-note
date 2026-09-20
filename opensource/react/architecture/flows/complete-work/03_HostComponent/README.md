# HostComponent case

상위: [completeWork 흐름](../README.md)

**실제 DOM 노드가 여기서 만들어진다.** 그리고 갱신 경로는 `props` 를 비교하지 않는다 — 참조 비교 한 번과 비트 하나가 전부다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberCompleteWork.js` L1372-L1471 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCompleteWork.js#L1372-L1471))

## 실제 코드

최초 마운트에서 인스턴스를 만들고 자식을 붙인다.

```js
// ReactFiberCompleteWork.js L1423-L1449
          const rootContainerInstance = getRootHostContainer();
          const instance = createInstance(
            type,
            newProps,
            rootContainerInstance,
            currentHostContext,
            workInProgress,
          );
          // TODO: For persistent renderers, we should pass children as part
          // of the initial instance creation
          markCloned(workInProgress);
          appendAllChildren(instance, workInProgress, false, false);
          workInProgress.stateNode = instance;

          // Certain renderers require commit-time effects for initial mount.
          // (eg DOM renderer supports auto-focus for certain elements).
          // Make sure such renderers get scheduled for later work.
          if (
            finalizeInitialChildren(
              instance,
              type,
              newProps,
              currentHostContext,
            )
          ) {
            markUpdate(workInProgress);
          }
```

갱신 경로는 이것이 전부다.

`packages/react-reconciler` / `src` / `ReactFiberCompleteWork.js` L461-L480 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCompleteWork.js#L461-L480))

```js
// ReactFiberCompleteWork.js L472-L479
    const oldProps = current.memoizedProps;
    if (oldProps === newProps) {
      // In mutation mode, this is sufficient for a bailout because
      // we won't touch this node even if children changed.
      return;
    }

    markUpdate(workInProgress);
```

> In mutation mode, this is sufficient for a bailout because we won't touch this node even if children changed.

그리고 맨 끝에 던질 수 있는 호출이 온다.

```js
// ReactFiberCompleteWork.js L1459-L1470
      // This must come at the very end of the complete phase, because it might
      // throw to suspend, and if the resource immediately loads, the work loop
      // will resume rendering as if the work-in-progress completed. So it must
      // fully complete.
      preloadInstanceAndSuspendIfNeeded(
        workInProgress,
        workInProgress.type,
        current === null ? null : current.memoizedProps,
        workInProgress.pendingProps,
        renderLanes,
      );
      return null;
```

> This must come at the very end of the complete phase, because it **might** throw to suspend, and if the resource **immediately** loads, the work loop will resume rendering as if the work-in-progress completed. So it must fully complete.

## 동작 흐름

```text
 L1372  case HostComponent: {
 L1373    popHostContext(workInProgress)      <- [beginWork]의 push 와 짝

 L1375    current !== null 이고 stateNode 가 있으면 (갱신)
 L1376      updateHostComponent(current, workInProgress, type, newProps, renderLanes)

 L1383    아니면 (최초)
 L1384      newProps 가 없으면
 L1385        stateNode 도 null 이면
 L1386          => **throw** 'We must have new props for new mounts. ...'
 L1393        bubbleProperties(workInProgress)
 L1394        [FLAG:enableViewTransition]
 L1397          subtreeFlags &= ~ViewTransitionStatic
 L1399        => return null
                주석 L1392 "This can happen when we abort work."

 L1407      wasHydrated = popHydrationState(workInProgress)
 L1408      수화된 것이면
 L1411        prepareToHydrateHostInstance(workInProgress, currentHostContext)
 L1412        finalizeHydratedChildren(...) 이 참이면
 L1420          flags |= Hydrate
 L1422      아니면 (새로 만든다)
 L1424        instance = createInstance(type, newProps, ...)   <- DOM 노드
 L1433        markCloned(workInProgress)        no-op (L209 가드)
 L1434        appendAllChildren(instance, workInProgress, false, false)
 L1435        workInProgress.stateNode = instance
 L1440        finalizeInitialChildren(...) 이 참이면
 L1448          markUpdate(workInProgress)

 L1452    bubbleProperties(workInProgress)
 L1453    [FLAG:enableViewTransition]
 L1456      subtreeFlags &= ~ViewTransitionStatic

 L1463    preloadInstanceAndSuspendIfNeeded(...)   ** 던질 수 있다 **
 L1470    => return null
```

```text
 ★ 갱신 경로는 diff 를 하지 않는다

 updateHostComponent(L461)의 mutation 갈래 본문 전체가 이것뿐이다

   L472  const oldProps = current.memoizedProps;
   L473  if (oldProps === newProps) {
   L476    return;                            <- 참조 비교 하나로 끝
   L477  }
   L479  markUpdate(workInProgress);          <- flags |= Update 한 줄

 markUpdate(L199)도 한 줄이다
   workInProgress.flags |= Update;

 즉 렌더 단계는 "props 객체가 같은 참조인가" 만 본다
 무엇이 어떻게 달라졌는지는 보지 않는다

 실제 diff 는 커밋 mutation 단계에서 일어난다
 (그 경로는 [커밋] 흐름에서 다룬다.
  여기서 확인한 것은 이 함수가 diff 를 하지 않는다는 사실까지다)

 주석이 그래도 되는 이유를 적는다 (L474-475)
   "In mutation mode, this is sufficient for a bailout because
    we won't touch this node even if children changed."

 그리고 renderLanes 와 type 인자는 이 갈래에서 쓰이지 않는다
```

```text
 자식을 붙이는 쪽은 내려가며 찾는다

 L1434  appendAllChildren(instance, workInProgress, false, false)

 자식 fiber 가 곧 호스트 노드인 것은 아니다
 함수 컴포넌트가 끼어 있으면 그 아래로 더 내려가야 DOM 노드가 나온다

 주석이 그것을 말한다 (L251-252)
   "We only have the top Fiber that was created but we need recurse down
    its children to find all the terminal nodes."

 그래서 이 함수는 자식 fiber 를 훑으며
 HostComponent / HostText 를 만나면 붙이고
 아니면 더 내려간다

 => 트리는 아래에서 위로 지어진다
    자식이 먼저 완료되어 자기 인스턴스를 갖고 있어야
    부모가 그것을 붙일 수 있다
```

```text
 던지는 호출이 맨 끝에 있는 이유

 L1463  preloadInstanceAndSuspendIfNeeded(...)

 그 안에서
   L588  flags |= MaySuspendCommit
   L597  isReady = preloadInstance(stateNode, type, newProps)
   L598  준비 안 됐고
   L599    이전 화면에 머물러야 하면 flags |= ShouldSuspendCommit
   L602    아니면 suspendCommit()      -> throw SuspenseyCommitException
   L604  준비됐어도
   L608    flags |= ShouldSuspendCommit
           주석 L605-607 - 디코딩이 늦거나 캐시에서 빠질 수 있어
                           pre-commit 에서 다시 확인한다

 주석이 위치의 이유를 적는다 (L1459-1462)
   던질 수 있는데, 만약 리소스가 곧바로 로드되면
   work loop 가 이 fiber 를 완료된 것처럼 여기고 이어서 렌더한다
   그러니 그 전에 완전히 끝나 있어야 한다

 => bubbleProperties 도 ViewTransition 처리도 먼저 끝낸 뒤에 던진다
```

## 결과가 쓰이는 곳

```text
 workInProgress.stateNode
      --> 실제 DOM 노드다
      --> 부모가 appendAllChildren 으로 가져다 붙인다
      --> 커밋이 문서 트리에 넣는다

 flags |= Update
      --> 커밋 mutation 단계가 이것을 보고 props 를 갱신한다
      --> 무엇을 바꿀지는 그때 계산한다

 flags |= Hydrate
      --> 수화된 인스턴스라는 표시다

 flags |= MaySuspendCommit / ShouldSuspendCommit
      --> 커밋 전에 리소스를 다시 확인해야 한다는 표시다

 throw SuspenseyCommitException
      --> [렌더 루프]의 handleThrow 가 SuspendedOnInstance 로 바꾼다
```

## 다루지 않는 것

`createInstance` 가 DOM 노드를 만드는 방식과 `finalizeInitialChildren`, `appendAllChildren`(L243)의 재귀와 포털·Offscreen 처리, `popHydrationState` 와 `prepareToHydrateHostInstance` 의 수화 과정, `updateHostComponent` 의 persistence 갈래(L481 이하 — react-dom 에서는 죽어 있다), `maySuspendCommit` 과 `preloadInstance` 의 리소스 판정, 커밋 mutation 단계가 `Update` 를 소비해 실제 diff 를 하는 경로는 같은 뼈대의 곁가지라 요약만 했다.
