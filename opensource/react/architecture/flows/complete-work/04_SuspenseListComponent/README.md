# SuspenseListComponent case

상위: [completeWork 흐름](../README.md)

**"올라오는 길" 의 반례다.** 이 case 안에 row 를 하나씩 렌더하는 **드라이버 루프**가 있어서, 같은 fiber 를 다시 begin 단계로 되돌려 보낸다. 그래서 234줄로 이 파일에서 가장 길다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberCompleteWork.js` L1707-L1940 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCompleteWork.js#L1707-L1940))

## 실제 코드

입구에서 대부분이 걸러진다.

```js
// ReactFiberCompleteWork.js L1708-L1718
      popSuspenseListContext(workInProgress);

      const renderState: null | SuspenseListRenderState =
        workInProgress.memoizedState;

      if (renderState === null) {
        // We're running in the default, "independent" mode.
        // We don't do anything in this mode.
        bubbleProperties(workInProgress);
        return null;
      }
```

> We're running in the default, "independent" mode. We don't do anything in this mode.

1차 패스에서 서스펜드한 row 를 찾으면 결과를 버리고 다시 그린다.

```js
// ReactFiberCompleteWork.js L1766-L1787
                // Rerender the whole list, but this time, we'll force fallbacks
                // to stay in place.
                // Reset the effect flags before doing the second pass since that's now invalid.
                // Reset the child fibers to their original state.
                workInProgress.subtreeFlags = NoFlags;
                resetChildFibers(workInProgress, renderLanes);

                // Set up the Suspense List Context to force suspense and
                // immediately rerender the children.
                pushSuspenseListContext(
                  workInProgress,
                  setShallowSuspenseListContext(
                    suspenseStackCursor.current,
                    ForceSuspenseFallback,
                  ),
                );
                if (getIsHydrating()) {
                  // Re-apply tree fork since we popped the tree fork context in the beginning of this function.
                  pushTreeFork(workInProgress, renderState.treeForkCount);
                }
                // Don't bubble properties in this case.
                return workInProgress.child;
```

tail 에 row 가 남아 있으면 하나를 꺼내 begin 으로 보낸다.

```js
// ReactFiberCompleteWork.js L1890-L1896
        const next = renderState.tail;
        const onlyNewMounts = isOnlyNewMounts(next);
        renderState.rendering = next;
        renderState.tail = next.sibling;
        renderState.renderingStartTime = now();
        next.sibling = null;

```

## 동작 흐름

```text
 L1707  case SuspenseListComponent: {
 L1708    popSuspenseListContext(workInProgress)

 L1710    renderState = workInProgress.memoizedState
 L1713    renderState 가 null 이면 (revealOrder 를 안 준 경우)
 L1716      bubbleProperties(workInProgress)
 L1717      => return null            <- 가장 흔한 길. 여기서 끝난다

 L1720    didSuspendAlready = (flags & DidCapture) !== NoFlags
 L1722    renderedTail = renderState.rendering

 [A] L1723  renderedTail === null - 방금 head 를 렌더했다
     L1725    didSuspendAlready 가 아니면 (1차 패스)
                row 들을 훑으며 서스펜드한 것을 찾는다
                찾으면
     L1770        workInProgress.subtreeFlags = NoFlags
     L1771        resetChildFibers(workInProgress, renderLanes)   <- 1차 결과를 버린다
     L1775        pushSuspenseListContext(... ForceSuspenseFallback)
     L1787        => return workInProgress.child    ** head 를 다시 그린다 **
     L1793    tail 이 남았는데 CPU 데드라인을 넘겼으면
                DidCapture 를 세우고 재시도 lane 을 건다
     L1812    이미 서스펜드 상태였으면 cutOffTailIfNeeded

 [B] L1816  renderedTail !== null - 방금 tail row 하나를 렌더했다
     L1818    서스펜드했는지 보고, 했으면 DidCapture 와 재시도 처리
     L1870    렌더한 row 를 자식 목록에 이어 붙인다
                isBackwards 면 앞에, 아니면 last 뒤에

 L1885    renderState.tail !== null - 아직 렌더할 row 가 남았다
 L1890      next = renderState.tail
 L1892      renderState.rendering = next
 L1893      renderState.tail = next.sibling
 L1895      next.sibling = null
 L1900      suspenseContext 를 다시 세운다
 L1920      pushSuspenseListContext 또는
 L1928      pushSuspenseListCatch
 L1936      => return next            ** 다음 row 로 간다 **

 L1938    bubbleProperties(workInProgress)
 L1939    => return null              <- 리스트가 완전히 끝났다
 L1940  }
```

```text
 ★ completeWork 안의 루프다

 보통 completeWork 는 fiber 하나를 끝내고 올라간다
 그런데 이 case 는 두 자리에서 fiber 를 돌려준다

   L1787  return workInProgress.child
   L1936  return next

 [렌더 루프]의 completeUnitOfWork 는 그것을 이렇게 받는다
   L3389  if (next !== null)
   L3390    // Completing this fiber spawned new work. Work on that next.
   L3391    workInProgress = next
   L3392    return

 => 올라가지 않고 그 fiber 를 begin 단계로 보낸다

 그러면 그 row 가 렌더되고 다시 이 case 로 돌아온다
 이번에는 renderState.rendering 이 채워져 있으니 [B] 로 간다
 그리고 tail 에서 다음 row 를 꺼내 또 보낸다

 즉 리스트의 row 개수만큼 이 case 가 반복해서 불린다
```

```text
 상태가 memoizedState 에 산다

 SuspenseListRenderState 의 칸들 (그래서 재진입이 가능하다)
   rendering            지금 렌더 중인 row
   renderingStartTime   그 row 를 시작한 시각
   tail                 아직 안 한 row 들의 연결 리스트
   last                 이미 붙인 마지막 자식
   isBackwards          뒤에서부터 그리는가
   tailMode             visible / collapsed / hidden
   treeForkCount        수화용

 L1892-1895 가 한 스텝을 진행시킨다
   rendering = next
   tail = next.sibling
   next.sibling = null      <- 꺼낸 row 를 리스트에서 떼어 낸다
```

```text
 두 return 자리에 같은 주석이 있다

 L1786  // Don't bubble properties in this case.
 L1935  // Don't bubble properties in this case.

 아직 이 fiber 가 끝난 게 아니기 때문이다
 bubbleProperties 는 마지막에 한 번만 부른다 (L1938)

 반대로 L1716 의 독립 모드와 L1938 의 완전 종료에서는
 bubbleProperties 를 부르고 null 을 돌려준다
```

```text
 1차 결과를 버리는 자리

 L1770  workInProgress.subtreeFlags = NoFlags
 L1771  resetChildFibers(workInProgress, renderLanes)

 주석이 이유를 적는다 (L1766-1769)
   "Rerender the whole list, but this time, we'll force fallbacks to stay
    in place. Reset the effect flags before doing the second pass since
    that's now invalid. Reset the child fibers to their original state."

 새 내용이 준비됐어도 아직 준비 안 된 것이 있으면,
 준비된 것만 먼저 보여 주면 순서가 깨진다
 그래서 전부 fallback 을 유지하도록 강제하고 처음부터 다시 그린다

 그것이 ForceSuspenseFallback 컨텍스트다 (L1775-1781)
```

```text
 tail 의 마지막 push 가 둘로 갈린다

 L1910  tailMode 가 visible 이거나 collapsed 이거나
        새 마운트만 있는 게 아니거나 수화 중이면
 L1920    pushSuspenseListContext     서스펜드가 부모로 올라간다
 L1921  아니면
 L1928    pushSuspenseListCatch       리스트 자신이 받는다

 주석이 차이를 적는다 (L1922-1927)
   hidden(기본) 모드에서 tail 자체가 서스펜드하면
   부모를 서스펜드시키는 대신 그 row 를 지울 수 있다. 그래서 catch 로 행동한다
   collapsed 는 적어도 하나는 서스펜드 상태로 그려야 하고,
   그 뒤로는 잘라내서 다시 시도하지 않으므로 이 경우에 오지 않는다
   갱신된 노드는 tail 에서 지울 수 없어 사실상 visible 이고,
   다시 서스펜드하면 다른 길로 가 부모를 서스펜드시킨다
```

## 결과가 쓰이는 곳

```text
 return workInProgress.child (L1787)
      --> head 전체를 ForceSuspenseFallback 으로 다시 그린다

 return next (L1936)
      --> 그 row 하나를 begin 단계로 보낸다
      --> 끝나면 이 case 로 돌아와 다음 row 를 꺼낸다

 return null (L1717 / L1939)
      --> 독립 모드이거나 리스트가 끝났다
      --> completeUnitOfWork 가 형제나 부모로 올라간다

 renderState
      --> 다음 재진입이 이어받는 상태다

 DidCapture
      --> 2차 패스에 들어섰다는 표시다
      --> 다시 들어올 때 didSuspendAlready 로 읽힌다
```

## 다루지 않는 것

`cutOffTailIfNeeded`(L703)가 `tailMode` 별로 tail 을 잘라 내는 규칙, `isOnlyNewMounts`(L780), `findFirstSuspended` 가 서스펜드한 경계를 찾는 방식, `resetChildFibers` 의 되돌리기, `scheduleRetryEffect`(L638)와 재시도 lane, `pushSuspenseListContext` / `pushSuspenseListCatch` / `setShallowSuspenseListContext` 의 컨텍스트 조작, `getRenderTargetTime` 의 CPU 예산, [B] 갈래가 row 를 자식 목록에 잇는 세부(L1870-1882), 수화 중 `pushTreeFork` 는 같은 뼈대의 곁가지라 요약만 했다.
