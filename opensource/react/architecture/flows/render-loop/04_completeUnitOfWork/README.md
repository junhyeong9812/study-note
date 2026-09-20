# completeUnitOfWork

상위: [렌더 루프](../README.md)

**올라가는 쪽이다.** 그리고 **`RootCompleted` 를 세우는 자리**이자 work loop 를 끝내는 자리다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L3349-L3412 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L3349-L3412))

## 실제 코드

되감기로 갈아타는 자리.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L3354-L3364 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L3354-L3364))

```js
// ReactFiberWorkLoop.js L3354-L3364
    if ((completedWork.flags & Incomplete) !== NoFlags) {
      // This fiber did not complete, because one of its children did not
      // complete. Switch to unwinding the stack instead of completing it.
      //
      // The reason "unwind" and "complete" is interleaved is because when
      // something suspends, we continue rendering the siblings even though
      // they will be replaced by a fallback.
      const skipSiblings = workInProgressRootDidSkipSuspendedSiblings;
      unwindUnitOfWork(completedWork, skipSiblings);
      return;
    }
```

> The reason "unwind" and "complete" is interleaved is because when something suspends, we continue rendering the siblings even though they will be replaced by a fallback.

올라가는 세 갈래.

```js
// ReactFiberWorkLoop.js L3389-L3405
    if (next !== null) {
      // Completing this fiber spawned new work. Work on that next.
      workInProgress = next;
      return;
    }

    const siblingFiber = completedWork.sibling;
    if (siblingFiber !== null) {
      // If there is more work to do in this returnFiber, do that next.
      workInProgress = siblingFiber;
      return;
    }
    // Otherwise, return to the parent
    // $FlowFixMe[incompatible-type] we bail out when we get a null
    completedWork = returnFiber;
    // Update the next thing we're working on in case something throws.
    workInProgress = completedWork;
```

그리고 루트에 닿으면 상태를 세운다.

```js
// ReactFiberWorkLoop.js L3409-L3411
  if (workInProgressRootExitStatus === RootInProgress) {
    workInProgressRootExitStatus = RootCompleted;
  }
```

## 동작 흐름

```text
 L3352  completedWork = unitOfWork
 L3353  do {

 L3354    Incomplete 플래그가 있으면
 L3362      unwindUnitOfWork(completedWork, skipSiblings)
 L3363      return                       <- 되감기로 갈아탄다

 L3369    current = completedWork.alternate
 L3370    returnFiber = completedWork.return
 L3373    startProfilerTimer(completedWork)
 L3374    [__DEV__] runWithFiberInDEV(completeWork...) 아니면 completeWork(...)
 L3385    [enableProfilerTimer && ProfileMode]
           stopProfilerTimerIfRunningAndRecordIncompleteDuration

 L3389    next !== null 이면 workInProgress = next / return    새 일이 생겼다
 L3395    sibling 이 있으면 workInProgress = sibling / return
 L3403    아니면 completedWork = returnFiber
 L3405    workInProgress = completedWork
           주석 L3404: "Update the next thing we're working on in case
                        something throws."

 L3406  } while (completedWork !== null)

 L3409  workInProgressRootExitStatus 가 RootInProgress 면
 L3410    RootCompleted 로 바꾼다
```

```text
 루프가 끝나는 방식

 returnFiber 가 null 이 되면
 L3403 이 completedWork 를 null 로 만들고
 L3405 가 workInProgress 도 null 로 만든다

 그러면 while (completedWork !== null) 이 끝나고
 바깥 work loop 의 while (workInProgress !== null) 도 끝난다

 즉 이 한 줄이 두 루프를 동시에 끝낸다
```

```text
 RootCompleted 가 여기서 세워진다

 L3409  if (workInProgressRootExitStatus === RootInProgress)
 L3410    workInProgressRootExitStatus = RootCompleted

 조건이 붙어 있다 - 이미 다른 상태면 덮지 않는다
 서스펜드나 에러로 상태가 이미 바뀌었을 수 있기 때문이다

 (주석은 없다. 조건의 모양을 보고 내가 판단한 것이다)
```

```text
 되감기와 완료가 섞이는 이유

 주석이 적어 두었다 (L3358-3360)
   "The reason "unwind" and "complete" is interleaved is because when
    something suspends, we continue rendering the siblings even though
    they will be replaced by a fallback."

 즉 서스펜드해도 형제는 계속 렌더한다
 그 형제들이 올라오면서 Incomplete 를 만나면 그때 되감기로 갈아탄다

 skipSiblings 는 workInProgressRootDidSkipSuspendedSiblings 에서 온다 (L3361)
```

```text
 completeWork 호출 자리는 둘이다

 L3377  [__DEV__] runWithFiberInDEV 의 인자로
 L3383  운영에서 직접 호출

 performUnitOfWork 의 beginWork 넷과 다르다
 여기는 ProfileMode 분기를 안 하기 때문이다
```

```text
 startProfilerTimer 호출부가 비대칭이다

 performUnitOfWork L3069-3070
   if (enableProfilerTimer && (unitOfWork.mode & ProfileMode) !== NoMode) {
     startProfilerTimer(unitOfWork);

 completeUnitOfWork L3373
   startProfilerTimer(completedWork);        가드가 없다

 그 함수 자체에 가드가 있다 (ReactProfilerTimer L587-589)
   if (!enableProfilerTimer) { return; }

 그래서 앞쪽은 이중 가드이고 뒤쪽은 함수 안 가드에만 기댄다
 게다가 뒤쪽은 ProfileMode 도 안 본다

 (주석은 없다. 두 호출부와 함수 첫 줄을 비교해 내가 판단한 것이다)
```

## 결과가 쓰이는 곳

```text
 workInProgress
      --> 형제나 부모로 옮겨진다
      --> null 이 되면 work loop 가 끝난다

 workInProgressRootExitStatus = RootCompleted
      --> [01] 의 do-while 이 이것을 보고 finishConcurrentRender 로 간다

 completeWork 가 만든 것
      --> 호스트 인스턴스와 효과 목록이다
      --> 커밋 단계가 그것을 쓴다

 unwindUnitOfWork 로 넘어간 경우
      --> 경계를 찾아 되감는다. 이 함수는 return 으로 끝난다
```

## 다루지 않는 것

`completeWork` 가 호스트 인스턴스를 만들고 효과를 모으는 과정([completeWork 흐름](../../complete-work/README.md)에 따로 있다), `unwindUnitOfWork`(L3414)와 `unwindWork` 의 되감기, `workInProgressRootDidSkipSuspendedSiblings` 가 세워지는 자리, `Incomplete` 플래그를 붙이는 쪽, 프로파일러 계측 함수들의 내용은 같은 뼈대의 곁가지라 요약만 했다.
