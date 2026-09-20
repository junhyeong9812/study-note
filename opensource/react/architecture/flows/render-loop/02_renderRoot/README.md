# renderRootSync / renderRootConcurrent

상위: [렌더 루프](../README.md)

work loop 를 **`try` 로 감싸고 돌린다.** 두 함수의 모양이 거의 같고, 다른 것은 어느 루프를 부르느냐와 서스펜션 처리의 폭이다.

## 위치

동기 판 `packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L2604-L2749 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L2604-L2749))

동시 판 `packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L2760-L3034 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L2760-L3034))

## 실제 코드

동기 판의 뼈대.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L2643-L2712 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L2643-L2712))

```js
// ReactFiberWorkLoop.js L2706-L2710
      workLoopSync();
      exitStatus = workInProgressRootExitStatus;
      break;
    } catch (thrownValue) {
      handleThrow(root, thrownValue);
```

동시 판은 루프를 셋 중에서 고른다.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L2988-L3004 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L2988-L3004))

```js
// ReactFiberWorkLoop.js L2988-L3000
      if (__DEV__ && ReactSharedInternals.actQueue !== null) {
        // `act` special case: If we're inside an `act` scope, don't consult
        // `shouldYield`. Always keep working until the render is complete.
        // This is not just an optimization: in a unit test environment, we
        // can't trust the result of `shouldYield`, because the host I/O is
        // likely mocked.
        workLoopSync();
      } else if (enableThrottledScheduling) {
        workLoopConcurrent(includesNonIdleWork(lanes));
      } else {
        workLoopConcurrentByScheduler();
      }
      break;
```

> `act` special case: If we're inside an `act` scope, don't consult `shouldYield`. Always keep working until the render is complete. This is not just an optimization: in a unit test environment, we can't trust the result of `shouldYield`, because the host I/O is likely mocked.

스택을 버릴지 이어갈지는 입구에서 정한다.

```js
// ReactFiberWorkLoop.js L2766-L2767
  // If the root or lanes have changed, throw out the existing stack
  // and prepare a fresh one. Otherwise we'll continue where we left off.
```

> If the root or lanes have changed, throw out the existing stack and prepare a fresh one. Otherwise we'll continue where we left off.

## 동작 흐름

```text
 [renderRootSync]  L2604
 L2607  셋째 인자 이름이 shouldYieldForPrerendering 이다
 L2614  root 나 lanes 가 바뀌었으면 prepareFreshStack
 L2643  outer: do {
 L2644    try {
            서스펜션 상태에 따라 처리
   L2669    SuspendedOnHydration 이면 break outer
   L2682    shouldYieldForPrerendering && prerendering 이면
   L2692      exitStatus = RootInProgress; break outer
   L2706    workLoopSync()
   L2707    exitStatus = workInProgressRootExitStatus
   L2708    break
 L2709    } catch (thrownValue) {
 L2710      handleThrow(root, thrownValue)
 L2712  } while (true)
 L2726  executionContext = prevExecutionContext     <- finally 가 아니다
 L2727  popDispatcher / L2728 popAsyncDispatcher

 [renderRootConcurrent]  L2760
 L2762  executionContext |= RenderContext
 L2763  pushDispatcher / L2764 pushAsyncDispatcher
 L2768  root 나 lanes 가 바뀌었으면 prepareFreshStack
 L2801  outer: do {
 L2802    try {
   L2811    resumeOrUnwind: switch (workInProgressSuspendedReason) {
   L2856      break outer
   L2863      break outer
   L2868      break outer
   L2930      break resumeOrUnwind          <- switch 만 빠져나간다
   L2978      break outer
   L2980      default: throw new Error('Unexpected SuspendedReason. ...')
            }
   L2988    [__DEV__] act 스코프면 workLoopSync()
   L2995    [enableThrottledScheduling] workLoopConcurrent(...)      안 돈다
   L2998    아니면 workLoopConcurrentByScheduler()
   L3000    break
 L3001    } catch (thrownValue) {
 L3002      handleThrow(root, thrownValue)
 L3004  } while (true)
 L3009  executionContext = prevExecutionContext
 L3032  return workInProgressRootExitStatus
```

```text
 catch 가 다시 던지지 않는다

 catch 본문은 handleThrow 한 줄뿐이다 (L2710, L3002)
 그리고 do-while(true) 이라 try 로 되돌아간다

 되돌아간 try 의 앞부분이 서스펜션 switch 다
 handleThrow 가 세워 둔 workInProgressSuspendedReason 을 보고
 다시 시도할지 되감을지 정한다

 즉 throw -> 상태 세움 -> 루프 재진입 이 한 바퀴다
```

```text
 자기 버그도 같은 경로로 흡수된다

 L2980-2984  default: throw new Error('Unexpected SuspendedReason. This is a bug in React.')

 이 throw 가 try 안에 있다
 그래서 같은 catch 가 잡고 handleThrow 로 간다
 거기서 thenable 이 아니므로 "일반 에러" 로 분류된다

 (주석은 없다. throw 의 위치와 catch 범위를 보고 내가 판단한 것이다)
```

```text
 finally 가 없다

 executionContext 복원이 루프 **뒤 평문**이다 (L2726, L3009)

 catch 가 예외를 삼키므로 보통은 거기 도달한다
 다만 handleThrow 자체가 던지면 복원이 건너뛰어진다
 (그럴 수 있는지는 확인하지 못했다)
```

```text
 레이블이 둘이다 (동시 판)

 outer:          L2801   do-while 전체
 resumeOrUnwind: L2811   switch 하나

 break outer          루프를 빠져나간다 (L2856, L2863, L2868, L2978)
 break resumeOrUnwind switch 만 빠져나가 아래 work loop 로 간다 (L2930)

 즉 "되감기" 와 "이어서 렌더" 가 같은 switch 에서 갈린다
```

```text
 work loop 를 고르는 세 갈래

 L2988  [__DEV__] act 스코프면 workLoopSync
        주석이 이유를 적는다 - 테스트 환경에서 shouldYield 를 못 믿는다
        "the host I/O is likely mocked"

 L2995  [enableThrottledScheduling] workLoopConcurrent
        그 플래그가 모든 빌드에서 false 라 안 돈다

 L2998  그 밖에는 workLoopConcurrentByScheduler
        이것이 실제로 도는 concurrent 루프다
```

```text
 입구에서 스택을 이어갈지 정한다

 L2768  workInProgressRoot !== root || workInProgressRootRenderLanes !== lanes

 다르면 prepareFreshStack 으로 버리고 새로 시작한다
 같으면 workInProgress 가 남아 있는 자리에서 이어간다

 그래서 양보 후 재개가 가능하다
 동기 판에도 같은 주석과 같은 조건이 있다 (L2614-2615)
```

## 결과가 쓰이는 곳

```text
 workInProgressRootExitStatus
      --> 동시 판은 L3032 에서 그대로 돌려준다
      --> 동기 판은 L2707 에서 지역 변수로 옮겨 돌려준다

 workInProgress
      --> 양보하면 남아 있다. 다음 호출이 이어받는다
      --> prepareFreshStack 이 불리면 버려진다

 executionContext
      --> RenderContext 가 켜져 있는 동안 재진입이 막힌다
      --> [01] L1128 의 throw 가 그것을 본다
```

## 다루지 않는 것

서스펜션 switch 의 각 갈래가 하는 일(`replaySuspendedUnitOfWork`, `throwAndUnwindWorkLoop`, 데이터 대기), `prepareFreshStack`(L2004)의 스택 초기화, `pushDispatcher` 와 `pushAsyncDispatcher` 의 디스패처 교체, `resetContextDependencies` 와 뒷정리, `shouldYield` 의 구현은 같은 뼈대의 곁가지라 요약만 했다. 서스펜션 상태 목록은 [spi](../spi/README.md)에 있다.
