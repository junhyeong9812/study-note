# spi

상위: [렌더 루프](../README.md)

이 흐름의 계약은 **두 상태값**이다 — 왜 멈췄는가(`SuspendedReason`)와 어떻게 끝났는가(`RootExitStatus`). 그리고 둘 다 죽은 값을 품고 있다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 `ReactFiberWorkLoop.js` 기준이다.

## SuspendedReason — 왜 멈췄나

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L443-L453 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L443-L453))

| 값 | 누가 세우나 | concurrent 가 하는 일 | sync 가 하는 일 |
|---|---|---|---|
| `NotSuspended` (0) | `prepareFreshStack` L2240, 각 switch 암 | switch 에 안 들어감 | 〃 |
| `SuspendedOnError` (1) | `handleThrow` L2342 (thenable 아님) | 되감기 | `default` 로 되감기 |
| **`SuspendedOnData`** (2) | **아무도 안 세움** | (도달 불가) | (도달 불가) |
| `SuspendedOnImmediate` (3) | `handleThrow` L2320 | `SuspendedAndReadyToContinue` 로 바꾸고 `break outer` | 되감기, prerendering 이면 `break outer` |
| `SuspendedOnInstance` (4) | `handleThrow` L2323 | `...AndReadyToContinue` 로 바꾸고 `break outer` | `default` 로 되감기 |
| `SuspendedOnInstanceAndReadyToContinue` (5) | concurrent 자신 L2866 | 리소스를 다시 확인해 이어가거나 되감기 | `default` 로 되감기 |
| `SuspendedOnDeprecatedThrowPromise` (6) | `handleThrow` L2342 (thenable) | 언제나 되감기 | Immediate 와 같은 암 |
| `SuspendedAndReadyToContinue` (7) | concurrent L2862 | thenable 이 풀렸으면 `replaySuspendedUnitOfWork` | `default` 로 되감기 |
| `SuspendedOnHydration` (8) | `handleThrow` L2334 | 스택 리셋 + `RootSuspendedAtTheShell` + `break outer` | 같음 (다만 **지역 변수**에 쓴다) |
| **`SuspendedOnAction`** (9) | **아무도 안 세움** | (도달 불가) | (도달 불가) |
| 그 밖 | — | **`throw new Error('Unexpected SuspendedReason. This is a bug in React.')`** | 조용히 되감기 |

```text
 ★ 죽은 값이 둘이다

 workInProgressSuspendedReason 에 대입하는 자리는 열여섯이고
 그중 SuspendedOnData / SuspendedOnAction 은 없다
 변수가 모듈 지역이라 밖에서 쓸 수도 없다

 TODO 주석이 이유를 적어 두었다 (L2314-2319)
   sibling prerendering 과 호환이 안 돼서 지금은
   무조건 SuspendedOnImmediate 로 접는다. 나중에 되돌릴 계획이다

 그 여파
   concurrent 의 OnData/OnAction 갈래 - 진짜로 thenable 을 기다리는
     유일한 자리였는데 도달 불가
   isWorkLoopSuspendedOnData() 가 언제나 false
   [스케줄링]의 "이 루트가 데이터 대기 중" 조건도 죽은 가지
   [마운트]의 scheduleUpdateOnFiber 첫 조건도 마찬가지
```

```text
 두 렌더 함수의 폭이 다르다

 sync        암이 셋이다 - Hydration / Immediate 묶음 / default
 concurrent  암이 여덟이다 + 던지는 default

 같은 "모르는 값"을
   concurrent 는 던지고 (L2980-2984)
   sync 는 조용히 되감는다 (default L2696-2703)

 그리고 SuspendedOnHydration 처리에도 차이가 있다
   concurrent  모듈 변수 workInProgressRootExitStatus 에 쓴다 (L2977)
   sync        지역 변수 exitStatus 에만 쓴다 (L2668)
   => sync 가 RootSuspendedAtTheShell 을 돌려줘도
      모듈 변수는 RootInProgress 로 남아 있을 수 있다
```

## RootExitStatus — 어떻게 끝났나

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L425-L432 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L425-L432))

| 값 | 어디서 세워지나 | `performWorkOnRoot` 의 do-while 이 하는 일 |
|---|---|---|
| `RootInProgress` (0) | `prepareFreshStack` L2245 / concurrent 가 `workInProgress !== null` 이면 L3017 에서 반환 | 양보하고 `break` (L1194) |
| `RootFatalErrored` (1) | **`handleThrow` L2356** | `prepareFreshStack` + `markRootSuspended` + `break` (L1289-1294) |
| `RootErrored` (2) | `renderDidError` | 재시도 lane 이 있으면 복구 시도 후 `continue` (L1269) |
| `RootSuspended` (3) | `renderDidSuspend` | 전용 분기 없음 → `finishConcurrentRender` |
| `RootSuspendedWithDelay` (4) | `renderDidSuspendDelayIfPossible` | 〃 |
| `RootCompleted` (5) | **`completeUnitOfWork` L3409-3411** | 〃 |
| `RootSuspendedAtTheShell` (6) | `unwindUnitOfWork` L3488 / concurrent L2977 | 〃 |

```text
 do-while 이 이름을 대고 처리하는 것은 셋뿐이다

 RootInProgress / RootErrored / RootFatalErrored

 나머지 넷은 전부 finishConcurrentRender 로 넘긴다
 즉 "커밋할지 미룰지" 의 판단은 이 흐름 밖이다
```

```text
 선언 순서가 뒤집혀 있다

 L425-432 에서 RootSuspendedAtTheShell 이 6, RootCompleted 가 5 인데
 선언은 6 이 먼저 나온다

 동작에는 영향이 없지만 읽을 때 헷갈리는 자리다
```

## 주석이 코드와 어긋나는 자리

```text
 renderRootSync 의 주석 (L2649-2651)

   "The work loop is suspended. During a synchronous render, we don't
    yield to the main thread. Immediately unwind the stack. This will
    trigger either a fallback or an error boundary."

 그런데 30줄 아래에서 양보한다 (L2682-2692)
   shouldYieldForPrerendering && workInProgressRootIsPrerendering 이면
   exitStatus = RootInProgress; break outer

 그 자리의 주석은 스스로 이렇게 적는다 (L2688-2690)
   "Yield to the main thread so we can switch to prerendering using
    the concurrent work loop."

 => 앞 주석의 "we don't yield" 는 한정어가 빠져 지금 코드에선 거짓이다
    (이 어긋남은 검증 과정에서 지적된 것이고, 나도 두 주석을 확인했다)
```

```text
 performWorkOnRoot 의 주석도 조건을 덜 적는다 (L1151-1153)

   "We disable time-slicing in some cases: if the work has been CPU-bound
    for too long ("expired" work, to prevent starvation), or we're in
    sync-updates-by-default mode."

 실제 조건은 셋의 AND 다 (L1155-1157)
   !forceSync && !includesBlockingLane && !includesExpiredLane

 주석에 forceSync 와 includesBlockingLane 이 없다
 그런데 performSyncWorkOnRoot 가 넘기는 forceSync = true 가
 가장 흔한 실제 경로다

 "in some cases" 라는 한정어를 떼고 읽으면 조건 나열이 어긋난다
```

## 죽은 플래그

```text
 enableThrottledScheduling   모든 빌드에서 false
   workLoopConcurrent(L3037)가 안 돈다. 호출처는 L2996 하나뿐

 enableSchedulingProfiler    언제나 false
   정의가 !enableComponentPerformanceTrack && __PROFILE__ 인데
   앞이 상수 true 라 결과가 늘 false
   이 흐름에서 L2637, L2730, L2797, L3014, L3020, L2371 이 전부 죽는다
   특히 handleThrow 의 다섯 갈래 switch(L2371-2410) 통째로

 disableLegacyMode           true
   L1234 의 (disableLegacyMode || root.tag !== LegacyRoot) 가 언제나 참
```

## 결과가 쓰이는 곳

```text
 SuspendedReason
      --> renderRoot 의 switch 가 읽는다
      --> 되감을지 다시 돌릴지가 여기서 갈린다

 RootExitStatus
      --> performWorkOnRoot 의 do-while 이 읽는다
      --> 커밋 여부는 finishConcurrentRender 가 정한다

 죽은 값·죽은 플래그
      --> 소스에는 있지만 이 커밋에서 재현할 수 없다
      --> 문서가 살아 있는 분기처럼 적으면 오해를 만든다
```

## 다루지 않는 것

`finishConcurrentRender` 가 상태별로 커밋 여부를 정하는 규칙, `renderDidSuspend` / `renderDidError` / `renderDidSuspendDelayIfPossible` 이 불리는 자리, `unwindUnitOfWork` 와 `throwAndUnwindWorkLoop` 의 되감기, `replaySuspendedUnitOfWork` 와 `replayBeginWork` 의 재생, `root.shellSuspendCounter` 의 무한 ping 방어, `ReactFeatureFlags` 의 나머지 플래그는 이 문서의 범위 밖이다.
