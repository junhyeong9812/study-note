# handleThrow

상위: [렌더 루프](../README.md)

던져진 값을 **상태로 바꾼다.** 다시 던지지 않는다. 그래서 work loop 의 `do-while` 이 `try` 로 되돌아가 그 상태를 보고 다음을 정한다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L2283-L2411 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L2283-L2411))

## 실제 코드

의도를 주석이 먼저 말한다.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L2284-L2295 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L2284-L2295))

> Until we decide whether we're going to unwind or replay, we should preserve the current state of the work loop without resetting anything.

서스펜션은 센티널로 온다.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L2304-L2320 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L2304-L2320))

> This is a special type of exception used for Suspense. For historical reasons, the rest of the Suspense implementation expects the thrown value to be a thenable, because before `use` existed that was the (unstable) API for suspending.

그리고 셋을 세운다.

```js
// ReactFiberWorkLoop.js L2342-L2348
    workInProgressSuspendedReason = isWakeable
      ? // A wakeable object was thrown by a legacy Suspense implementation.
        // This has slightly different behavior than suspending with `use`.
        SuspendedOnDeprecatedThrowPromise
      : // This is a regular error. If something earlier in the component already
        // suspended, we must clear the thenable state to unblock the work loop.
        SuspendedOnError;
```

```js
// ReactFiberWorkLoop.js L2351-L2362
  workInProgressThrownValue = thrownValue;

  const erroredWork = workInProgress;
  if (erroredWork === null) {
    // This is a fatal error
    workInProgressRootExitStatus = RootFatalErrored;
    logUncaughtError(
      root,
      createCapturedValueAtFiber(thrownValue, root.current),
    );
    return;
  }
```

## 동작 흐름

```text
 L2299  resetHooksAfterThrow()
 L2300  [__DEV__] resetCurrentFiber()
        주석 L2297-2298: 이 둘은 즉시 리셋해야 한다.
                        사용자 코드를 돌릴 때만 세워지는 것이라서다

 던져진 값 분류
 L2304  SuspenseException 또는 SuspenseActionException
          L2313  thrownValue = getSuspendedThenable()
          L2320  SuspendedOnImmediate
 L2321  SuspenseyCommitException
          L2322  thrownValue = getSuspendedThenable()
          L2323  SuspendedOnInstance
 L2324  SelectiveHydrationException
          L2334  SuspendedOnHydration
 L2335  그 외 = 진짜 에러
          isWakeable 이면 SuspendedOnDeprecatedThrowPromise
          아니면 SuspendedOnError                          L2342-2348

 L2351  workInProgressThrownValue = thrownValue

 L2353  erroredWork = workInProgress
 L2354  null 이면
 L2356    workInProgressRootExitStatus = RootFatalErrored
 L2357    logUncaughtError(...)
 L2361    return                                <- 여기서 끝난다

 L2364  [enableProfilerTimer && ProfileMode] 렌더 시간 기록
 L2371  [enableSchedulingProfiler] 프로파일러 마킹 (이 빌드에서는 안 돈다)
```

```text
 세 가지를 세운다

 workInProgressSuspendedReason   어떤 종류의 중단인가
 workInProgressThrownValue       무엇이 던져졌나
 workInProgressRootExitStatus    치명적일 때만 (L2356)

 앞의 둘은 renderRoot 의 switch 가 읽는다 (L2658, L2810)
 셋째는 performWorkOnRoot 의 L1278 이 읽는다

 즉 [01] 의 RootFatalErrored 갈래가 여기서 출발한다
```

```text
 throw 가 제어 흐름인 이유

 SuspenseException 은 진짜 예외가 아니라 센티널 값이다
 실제 thenable 은 getSuspendedThenable() 로 따로 꺼낸다 (L2313)

 주석이 역사적 사정을 적는다 (L2308-2312)
   use 가 생기기 전에는 thenable 을 직접 던지는 것이 서스펜션 API 였고
   나머지 구현이 아직 그 전제 위에 있다

 그래서 던지는 쪽은 상수를 던지고
 받는 쪽이 모듈 전역에서 실제 값을 꺼낸다
```

```text
 다시 던지지 않는다 - 다만 그 다음 단계는 던질 수 있다

 이 함수 본문에 throw 가 없다

 그런데 되감기로 넘어간 뒤 throwAndUnwindWorkLoop 안에서
 에러 처리 중 또 에러가 나면 다시 던진다 (L3250 부근)
 그러면 work loop 의 catch 가 다시 이 함수로 데려온다

 (그쪽 본문은 읽지 않았다. 검증 과정에서 확인된 것이다)
```

```text
 ★ 죽은 상태값이 둘 있다

 SuspendedOnData 와 SuspendedOnAction 은
 **이 커밋에서 아무도 대입하지 않는다**

 workInProgressSuspendedReason 에 대입하는 자리를 전부 세면 16곳인데
 (L2240, L2320, L2323, L2334, L2342, L2679, L2699, L2814, L2829,
  L2848, L2862, L2874, L2879, L2916, L2947, L2962)
 그중 그 둘은 없다. 변수는 모듈 지역이라 밖에서 쓸 수도 없다

 TODO 주석이 이유를 적어 두었다 (L2314-2319)
   "Suspending the work loop during the render phase is currently not
    compatible with sibling prerendering. We will add this optimization
    back in a later step. Don't suspend work loop, except to check if the
    data has immediately resolved (i.e. in a microtask). Otherwise,
    trigger the nearest Suspense fallback."

 즉 예전에 SuspendedOnData 를 세우던 자리가 지금은
 무조건 SuspendedOnImmediate 로 접혔다 (L2320)

 그 여파가 넓다
   renderRootConcurrent 의 OnData/OnAction 갈래가 도달 불가
   isWorkLoopSuspendedOnData() 가 언제나 false
   그것을 쓰는 [스케줄링]의 조건과 [마운트]의 조건도 죽은 가지다
```

## 결과가 쓰이는 곳

```text
 workInProgressSuspendedReason
      --> renderRoot 의 switch 가 읽어 되감을지 다시 돌릴지 정한다
      --> [spi](../spi/README.md)에 값별 처리가 표로 있다

 workInProgressThrownValue
      --> 같은 switch 가 읽는다
      --> 되감기에서 throwException 의 인자가 된다

 RootFatalErrored
      --> [01] L1278 이 받아 prepareFreshStack 후 끝낸다
```

## 다루지 않는 것

`resetHooksAfterThrow` 와 훅 상태 정리, `getSuspendedThenable` 이 값을 꺼내는 방식, `throwException` 과 `throwAndUnwindWorkLoop` 의 되감기, `logUncaughtError` 와 `createCapturedValueAtFiber`, `enableSchedulingProfiler` 블록의 마킹 함수들은 같은 뼈대의 곁가지라 요약만 했다. 상태값 전체는 [spi](../spi/README.md)에 있다.
