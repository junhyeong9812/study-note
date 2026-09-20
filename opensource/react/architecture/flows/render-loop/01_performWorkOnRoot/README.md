# performWorkOnRoot

상위: [렌더 루프](../README.md)

루프 모드를 정하고 **재시도를 관리한다.** 첫 줄이 `throw` 이고 마지막 줄이 `ensureRootIsScheduled` 다 — 들어올 때 막고 나갈 때 다시 건다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L1123-L1311 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L1123-L1311))

## 실제 코드

첫 줄은 플래그가 아니라 예외다.

```js
// ReactFiberWorkLoop.js L1128-L1130
  if ((executionContext & (RenderContext | CommitContext)) !== NoContext) {
    throw new Error('Should not already be working.');
  }
```

타임슬라이싱 여부를 정한다.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L1151-L1167 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L1151-L1167))

```js
// ReactFiberWorkLoop.js L1151-L1167
  // We disable time-slicing in some cases: if the work has been CPU-bound
  // for too long ("expired" work, to prevent starvation), or we're in
  // sync-updates-by-default mode.
  const shouldTimeSlice =
    (!forceSync &&
      !includesBlockingLane(lanes) &&
      !includesExpiredLane(root, lanes)) ||
    // If we're prerendering, then we should use the concurrent work loop
    // even if the lanes are synchronous, so that prerendering never blocks
    // the main thread.
    // TODO: We should consider doing this whenever a sync lane is suspended,
    // even for regular pings.
    checkIfRootIsPrerendering(root, lanes);

  let exitStatus: RootExitStatus = shouldTimeSlice
    ? renderRootConcurrent(root, lanes)
    : renderRootSync(root, lanes, true);
```

> We disable time-slicing in some cases: if the work has been CPU-bound for too long ("expired" work, to prevent starvation), or we're in sync-updates-by-default mode.

> If we're prerendering, then we should use the concurrent work loop even if the lanes are synchronous, so that prerendering never blocks the main thread.

그리고 재시도 루프를 돈다.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L1171-L1308 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L1171-L1308))

마지막 줄이 흐름 2 로 돌아간다.

```js
// ReactFiberWorkLoop.js L1310-L1310
  ensureRootIsScheduled(root);
```

## 동작 흐름

```text
 L1128  executionContext 에 Render 나 Commit 이 있으면
          throw new Error('Should not already be working.')

 L1132  [enableProfilerTimer && enableComponentPerformanceTrack]
          직전에 양보했던 시간을 yieldReason 별로 로깅한다 (3갈래)

 L1154  shouldTimeSlice =
          (!forceSync && !includesBlockingLane && !includesExpiredLane)
          || checkIfRootIsPrerendering(root, lanes)

 L1165  exitStatus = shouldTimeSlice
          ? renderRootConcurrent(root, lanes)
          : renderRootSync(root, lanes, true)

 L1171  do {
   L1172  RootInProgress 면
     L1174  prerendering 인데 타임슬라이싱이 아니면 markRootSuspended (L1186)
     L1188  [FLAG] startYieldTimer
     L1194  break                        <- 양보하고 나간다

   L1195  아니면 (렌더가 끝났다)
     L1208  finishedWork = root.current.alternate
     L1209  concurrent 였고 외부 스토어가 어긋났으면
       L1224  exitStatus = renderRootSync(root, lanes, false)
       L1227  renderWasConcurrent = false
       L1229  continue
     L1233  (disableLegacyMode || LegacyRoot 아님) 이고 RootErrored 면
       L1238  errorRetryLanes 를 구해
       L1254  recoverFromConcurrentError(...)
       L1261  에러가 아니게 됐으면 L1269 continue
     L1278  RootFatalErrored 면
       L1289  prepareFreshStack(root, NoLanes)
       L1293  markRootSuspended(didAttemptEntireTree = true)
       L1294  break
     L1299  finishConcurrentRender(...)
   L1307  break
 L1308  } while (true)

 L1310  ensureRootIsScheduled(root)
```

```text
 재진입이 조용한 실패가 아니다

 L1128-1130 이 던진다
   throw new Error('Should not already be working.')

 플래그도 assert 도 아니다. 운영에서도 던진다
 즉 렌더·커밋 중에 이 함수가 다시 불리면 예외로 드러난다
```

```text
 shouldTimeSlice 는 뒤 항이 앞 항을 뒤집는다

 앞  !forceSync && !includesBlockingLane && !includesExpiredLane
 뒤  checkIfRootIsPrerendering(root, lanes)

 OR 이므로 뒤가 참이면 앞이 거짓이어도 concurrent 루프를 쓴다
 주석이 그 의도를 말한다 (L1158-1160) - prerendering 이 메인 스레드를 막으면 안 된다

 그래서 sync lane 인데 concurrent 루프로 도는 경우가 있다
```

```text
 renderRootSync 의 셋째 인자에 이름이 있다

 shouldYieldForPrerendering (L2607)

 L1167  true 를 넘긴다   - prerendering 이면 양보해도 된다
 L1224  false 를 넘긴다  - 스토어 재렌더는 끝까지 간다

 그 인자가 쓰이는 곳은 L2682-2692 다
   shouldYieldForPrerendering && workInProgressRootIsPrerendering 이면
   exitStatus = RootInProgress 로 두고 break outer

 즉 "concurrent 루프에게 넘기려고 일부러 중단한다"
```

```text
 do-while 안의 출구가 다섯이다

 break    L1194  양보 (아직 안 끝남)
 continue L1229  스토어 불일치 -> 동기로 다시
 continue L1269  에러 복구 성공 -> 다시 판정
 break    L1294  치명적 에러
 break    L1307  정상 종료 (finishConcurrentRender 뒤)

 주석이 이 구조를 스스로 복잡하다고 적는다 (L1264-1268)
   "TODO: Refactor the exit algorithm to be less confusing. Maybe
    more branches + recursion instead of a loop."
```

```text
 L1233 의 조건에 가드가 둘이다

 (disableLegacyMode || root.tag !== LegacyRoot) && exitStatus === RootErrored

 disableLegacyMode 가 기본 true 라 앞 항은 언제나 참이다
 즉 실질적으로는 exitStatus === RootErrored 하나만 본다
```

```text
 마지막 줄이 고리를 닫는다

 L1310  ensureRootIsScheduled(root)

 양보했든 끝났든 이 줄이 돈다
 그래서 남은 일이 있으면 흐름 2 가 다음 태스크를 건다

 뒤에 다른 문장이 없다 (L1311 이 닫는 중괄호다)
```

## 결과가 쓰이는 곳

```text
 exitStatus
      --> 이 루프가 다음 행동을 정하는 근거다
      --> RootCompleted 는 completeUnitOfWork 가 세운다
      --> RootFatalErrored 는 handleThrow 가 세운다

 finishedWork (root.current.alternate)
      --> finishConcurrentRender 로 넘어가 커밋 여부가 정해진다

 ensureRootIsScheduled
      --> 흐름 2 로 돌아간다
      --> 양보한 경우 같은 태스크가 이어 돌 수도 있다
```

## 다루지 않는 것

`finishConcurrentRender`(L1401) 이후의 커밋 결정, `recoverFromConcurrentError`(L1313)의 에러 복구와 수화 폴백, `isRenderConsistentWithExternalStores` 의 스토어 검사, `getLanesToRetrySynchronouslyOnError` 의 lane 계산, `markRootSuspended` 와 `prepareFreshStack` 의 내용, `includesBlockingLane` / `includesExpiredLane` / `checkIfRootIsPrerendering` 의 판정은 같은 뼈대의 곁가지라 요약만 했다. 종료 상태는 [spi](../spi/README.md)에 있다.
