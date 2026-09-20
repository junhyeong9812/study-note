# bailoutOnAlreadyFinishedWork

상위: [beginWork 흐름](../README.md)

**서브트리를 통째로 건너뛸지 정한다.** `null` 을 돌려주면 건너뛰고, 자식을 돌려주면 자식만 복제해 계속 내려간다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberBeginWork.js` L3789-L3828 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberBeginWork.js#L3789-L3828))

## 실제 코드

전부 40줄이다.

```js
// ReactFiberBeginWork.js L3789-L3828
function bailoutOnAlreadyFinishedWork(
  current: Fiber | null,
  workInProgress: Fiber,
  renderLanes: Lanes,
): Fiber | null {
  if (current !== null) {
    // Reuse previous dependencies
    workInProgress.dependencies = current.dependencies;
  }

  if (enableProfilerTimer) {
    // Don't update "base" render times for bailouts.
    stopProfilerTimerIfRunning(workInProgress);
  }

  markSkippedUpdateLanes(workInProgress.lanes);

  // Check if the children have any pending work.
  if (!includesSomeLane(renderLanes, workInProgress.childLanes)) {
    // The children don't have any work either. We can skip them.
    // TODO: Once we add back resuming, we should check if the children are
    // a work-in-progress set. If so, we need to transfer their effects.

    if (current !== null) {
      // Before bailing out, check if there are any context changes in
      // the children.
      lazilyPropagateParentContextChanges(current, workInProgress, renderLanes);
      if (!includesSomeLane(renderLanes, workInProgress.childLanes)) {
        return null;
      }
    } else {
      return null;
    }
  }

  // This fiber doesn't have work, but its subtree does. Clone the child
  // fibers and continue.
  cloneChildFibers(current, workInProgress);
  return workInProgress.child;
}
```

## 동작 흐름

```text
 L3789  function bailoutOnAlreadyFinishedWork(current, workInProgress, renderLanes)

 L3794  current !== null 이면
 L3796    workInProgress.dependencies = current.dependencies
           주석 L3795: "Reuse previous dependencies"

 L3799  [enableProfilerTimer]
 L3801    stopProfilerTimerIfRunning(workInProgress)
           주석 L3800: "Don't update "base" render times for bailouts."

 L3804  markSkippedUpdateLanes(workInProgress.lanes)

 L3807  if (!includesSomeLane(renderLanes, workInProgress.childLanes))
          주석 L3806: "Check if the children have any pending work."
          주석 L3808: "The children don't have any work either. We can skip them."

 L3812    if (current !== null)
 L3815      lazilyPropagateParentContextChanges(current, workInProgress, renderLanes)
             주석 L3813-3814: 바이아웃 전에 자식의 컨텍스트 변화를 확인한다
 L3816      if (!includesSomeLane(renderLanes, workInProgress.childLanes))
 L3817        => return null
 L3818      }
              (거짓이면 아래로 흘러내려간다)
 L3819    else
 L3820      => return null
 L3822  }

 L3826  cloneChildFibers(current, workInProgress)
 L3827  => return workInProgress.child
```

```text
 return 이 셋인데 도달 경로는 넷이다

 return null #1   L3817
   자식에 이번 렌더 일이 없다 AND current !== null
   AND 컨텍스트 전파 후에도 여전히 없다

 return null #2   L3820
   자식에 이번 렌더 일이 없다 AND current === null
   최초 마운트라 전파할 부모 컨텍스트 변화가 없다

 return child     L3827  -- 여기 오는 길이 둘이다
   (가) L3807 이 거짓    처음부터 자식에 일이 있었다
   (나) L3816 이 거짓    일이 없었는데 L3815 전파로 **생겼다**

 (나) 가 이 함수의 요점이다
 "일이 없어 보여도 컨텍스트 때문에 생길 수 있다"
```

```text
 "자식에 일이 없다" 는 이번 렌더 기준이다

 L3807  !includesSomeLane(renderLanes, workInProgress.childLanes)

 renderLanes 와 childLanes 의 교집합이 비었다는 뜻이다
 다른 lane 의 일은 남아 있을 수 있다

 그것을 바로 윗줄이 기록한다
   L3804  markSkippedUpdateLanes(workInProgress.lanes)

 즉 "지금은 건너뛰지만 나중에 할 일이 있다" 를 루트에 남긴다
 그래야 [렌더 루프]가 끝난 뒤 다시 스케줄된다
```

```text
 ★ markSkippedUpdateLanes 가 보는 lanes 가 진입 경로마다 다르다

 (가) 빠른 바이아웃으로 왔다
      [01] L4239 에서 return 했으므로
      L4281 의 lanes = NoLanes 를 **지나지 않았다**
      -> workInProgress.lanes 가 살아 있다

 (나) switch 를 거쳐 update 함수 안에서 왔다
      L4281 을 지나왔으므로 이미 NoLanes 다
      -> 기록할 것이 없다

 그래서 updateSimpleMemoComponent 는 이 함수를 부르기 전에
 L591 에서 workInProgress.lanes = current.lanes 로 되돌린다
 그 주석(L578-590)이 이유를 적는다
   "we're bailing out early *without* evaluating the component,
    we need to account for it here, too"

 [01] L4277-4280 의 TODO 와 L589-590 의 TODO 가
 서로를 가리키는 것이 이 지점이다
```

```text
 dependencies 를 재사용한다

 L3796  workInProgress.dependencies = current.dependencies

 컴포넌트를 평가하지 않으므로 컨텍스트 의존 목록을 새로 만들 수 없다
 그래서 이전 것을 그대로 가져온다

 그리고 L3815 가 그 목록을 근거로 전파를 확인한다
```

```text
 cloneChildFibers 는 자식만 복제한다

 L3826  cloneChildFibers(current, workInProgress)

 자식 fiber 들을 work-in-progress 쪽으로 복제하되
 그 아래는 건드리지 않는다

 다음 beginWork 가 그 자식을 받아 같은 판정을 다시 한다
 즉 건너뛰기는 한 단계씩 내려가며 결정된다
```

## 결과가 쓰이는 곳

```text
 return null
      --> [01] 이 그대로 돌려준다
      --> performUnitOfWork L3098 이 completeUnitOfWork 로 넘긴다
      --> 서브트리 전체를 건너뛴다

 return workInProgress.child
      --> 그 자식으로 내려간다
      --> 자식이 같은 판정을 다시 받는다

 markSkippedUpdateLanes
      --> 루트에 남은 lane 을 모은다
      --> [렌더 루프]가 끝난 뒤 ensureRootIsScheduled 가 이것을 본다

 workInProgress.dependencies
      --> 컨텍스트 전파가 이것을 근거로 판정한다
```

## 다루지 않는 것

`cloneChildFibers` 의 복제 규칙, `lazilyPropagateParentContextChanges`(`ReactFiberNewContext.js` L379)가 자식을 훑는 방식과 `checkIfContextChanged`, `markSkippedUpdateLanes` 가 루트에 lane 을 모으는 과정, `includesSomeLane` 의 비트 연산, `stopProfilerTimerIfRunning` 의 계측은 같은 뼈대의 곁가지라 요약만 했다.
