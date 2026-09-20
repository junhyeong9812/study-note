# performUnitOfWork

상위: [렌더 루프](../README.md)

**내려가는 쪽이다.** 마흔 줄인데 실제 분기는 둘뿐이고, 나머지는 프로파일러와 개발 모드 조합이다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L3062-L3104 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L3062-L3104))

## 실제 코드

전부 인용해도 짧다.

```js
// ReactFiberWorkLoop.js L3062-L3104
function performUnitOfWork(unitOfWork: Fiber): void {
  // The current, flushed, state of this fiber is the alternate. Ideally
  // nothing should rely on this, but relying on it here means that we don't
  // need an additional field on the work in progress.
  const current = unitOfWork.alternate;

  let next;
  if (enableProfilerTimer && (unitOfWork.mode & ProfileMode) !== NoMode) {
    startProfilerTimer(unitOfWork);
    if (__DEV__) {
      next = runWithFiberInDEV(
        unitOfWork,
        beginWork,
        current,
        unitOfWork,
        entangledRenderLanes,
      );
    } else {
      next = beginWork(current, unitOfWork, entangledRenderLanes);
    }
    stopProfilerTimerIfRunningAndRecordDuration(unitOfWork);
  } else {
    if (__DEV__) {
      next = runWithFiberInDEV(
        unitOfWork,
        beginWork,
        current,
        unitOfWork,
        entangledRenderLanes,
      );
    } else {
      next = beginWork(current, unitOfWork, entangledRenderLanes);
    }
  }

  unitOfWork.memoizedProps = unitOfWork.pendingProps;
  if (next === null) {
    // If this doesn't spawn new work, complete the current work.
    completeUnitOfWork(unitOfWork);
  } else {
    workInProgress = next;
  }
}
```

돌리는 루프는 셋이다.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L2753-L2758 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L2753-L2758))

```js
// ReactFiberWorkLoop.js L2753-L2758
function workLoopSync() {
  // Perform work without checking if we need to yield between fiber.
  while (workInProgress !== null) {
    performUnitOfWork(workInProgress);
  }
}
```

시간 기반 루프는 의도가 특이하다.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L3037-L3051 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L3037-L3051))

> We yield every other "frame" when rendering Transition or Retries. Those are blocking revealing new content. The purpose of this yield is not to avoid the overhead of yielding, which is very low, but rather to intentionally block any frequently occurring other main thread work like animations from starving our work. In other words, the purpose of this is to reduce the framerate of animations to 30 frames per second.

> For Idle work we yield every 5ms to keep animations going smooth.

## 동작 흐름

```text
 L3066  current = unitOfWork.alternate
        주석 L3063-3065: alternate 에 의존하면 별도 필드가 필요 없다

 L3069  [enableProfilerTimer] 이고 fiber 가 ProfileMode 면
          L3070  startProfilerTimer(unitOfWork)
          L3071  [__DEV__] runWithFiberInDEV(unitOfWork, beginWork, ...)
          L3079  아니면 beginWork(current, unitOfWork, entangledRenderLanes)
          L3082  stopProfilerTimerIfRunningAndRecordDuration(unitOfWork)
        아니면
          L3084  [__DEV__] runWithFiberInDEV(...)
          L3092  아니면 beginWork(...)

 L3097  unitOfWork.memoizedProps = unitOfWork.pendingProps
 L3098  next === null 이면 completeUnitOfWork(unitOfWork)
 L3102  아니면 workInProgress = next
```

```text
 beginWork 가 네 자리에 있다

 L3074  ProfileMode + __DEV__     runWithFiberInDEV 의 인자로
 L3080  ProfileMode + 운영        직접 호출
 L3087  일반 + __DEV__            runWithFiberInDEV 의 인자로
 L3093  일반 + 운영               직접 호출

 두 조건의 조합이라 네 갈래다
 파일 전체에서 beginWork 를 **직접** 부르는 곳은 L3080, L3093 과
 replaySuspendedUnitOfWork 의 L3204 뿐이다
```

```text
 L3097 이 분기보다 앞이다

 unitOfWork.memoizedProps = unitOfWork.pendingProps

 beginWork 가 끝난 뒤, 자식으로 갈지 완료할지 정하기 전에 돈다
 즉 어느 갈래로 가든 props 는 확정된다
```

```text
 work loop 가 셋인데 실제로 도는 것은 둘이다

 workLoopSync L2753
   while (workInProgress !== null) performUnitOfWork(workInProgress)
   양보 검사가 아예 없다
   동기 렌더와 act 스코프가 쓴다

 workLoopConcurrent L3037
   yieldAfter = now() + (nonIdle ? 25 : 5)
   do { performUnitOfWork } while (workInProgress && now() < yieldAfter)
   enableThrottledScheduling 이 필요한데 모든 빌드에서 false 다

 workLoopConcurrentByScheduler L3054
   while (workInProgress !== null && !shouldYield()) performUnitOfWork(...)
   이것이 실제 concurrent 루프다
```

```text
 죽은 루프의 주석이 의도를 잘 적어 두었다

 25ms 와 5ms 가 목적이 다르다

 nonIdle (Transition / Retry)  25ms
   양보 비용을 줄이려는 게 아니다
   애니메이션 같은 잦은 메인 스레드 작업이 렌더를 굶기는 것을 막으려고
   **일부러** 막는 것이고, 결과적으로 애니메이션을 30fps 로 떨어뜨린다

 Idle                          5ms
   반대다. "keep animations going smooth"

 플래그 선언에도 그 말이 있다 (ReactFeatureFlags L72)
   "Experiment to intentionally yield less to block high framerate animations."
```

## 결과가 쓰이는 곳

```text
 workInProgress
      --> next 가 있으면 그 자식으로 옮긴다
      --> work loop 의 while 조건이 이것을 본다

 completeUnitOfWork 호출
      --> 자식이 없으면 올라가는 쪽으로 넘긴다
      --> 거기서 형제나 부모로 이어진다

 memoizedProps
      --> 다음 렌더에서 props 가 바뀌었는지 비교하는 기준이 된다
```

## 다루지 않는 것

`beginWork` 가 컴포넌트 타입별로 하는 일([beginWork 흐름](../../begin-work/README.md)에 따로 있다), `runWithFiberInDEV` 가 감싸는 방식, `startProfilerTimer` 와 `stopProfilerTimerIfRunningAndRecordDuration` 의 계측, `replaySuspendedUnitOfWork`(L3106)가 서스펜드된 fiber 를 다시 돌리는 방식, `shouldYield` 의 구현은 같은 뼈대의 곁가지라 요약만 했다.
