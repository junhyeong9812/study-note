# scheduleUpdateOnFiber

상위: [마운트](../README.md)

루트에 **할 일이 생겼다고 표시하고** 스케줄을 건다. 그런데 갈래가 둘이고, **한쪽은 스케줄을 안 한다.** 그리고 이 흐름이 끝나는 자리가 여기 안에 있다.

## 위치

`ReactFiberWorkLoop.js` `packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L973-L1099 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L973-L1099))

## 실제 코드

멈춰 있던 렌더를 깨우는 자리.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L990-L1010 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L990-L1010))

```js
// ReactFiberWorkLoop.js L992-L1010
  if (
    // Suspended render phase
    (root === workInProgressRoot &&
      (workInProgressSuspendedReason === SuspendedOnData ||
        workInProgressSuspendedReason === SuspendedOnAction)) ||
    // Suspended commit phase
    root.cancelPendingCommit !== null
  ) {
    // The incoming update might unblock the current render. Interrupt the
    // current attempt and restart from the top.
    prepareFreshStack(root, NoLanes);
    const didAttemptEntireTree = false;
    markRootSuspended(
      root,
      workInProgressRootRenderLanes,
      workInProgressDeferredLane,
      didAttemptEntireTree,
    );
  }
```

> The incoming update might unblock the current render. Interrupt the current attempt and restart from the top.

표시는 갈래보다 앞이다.

```js
// ReactFiberWorkLoop.js L1012-L1013
  // Mark that the root has a pending update.
  markRootUpdated(root, lane);
```

렌더 페이즈 중 갱신이면 lane 만 적고 끝난다.

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L1019-L1030 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L1019-L1030))

> This update was dispatched during the render phase. This is a mistake if the update originates from user space (with the exception of local hook updates, which are handled differently and don't reach this function), but there are some internal React features that use this as an implementation detail, like selective hydration.

보통은 여기로 간다.

```js
// ReactFiberWorkLoop.js L1079-L1084
    ensureRootIsScheduled(root);
    if (
      lane === SyncLane &&
      executionContext === NoContext &&
      !disableLegacyMode &&
      (fiber.mode & ConcurrentMode) === NoMode
```

## 동작 흐름

```text
 L978  [__DEV__] insertion effect 안이면 경고
 L984  [__DEV__] passive effect flush 중이면 플래그를 세운다

 L992  멈춰 있는 렌더가 있는가
         workInProgressRoot 가 같고 SuspendedOnData/SuspendedOnAction 이거나
         root.cancelPendingCommit !== null

         ★ 앞 절은 이 커밋에서 죽은 가지다
           SuspendedOnData 와 SuspendedOnAction 을 세우는 코드가 없다
           (ReactFiberWorkLoop 의 대입 자리 열여섯 곳에 그 둘이 없다)
           그래서 실질 조건은 root.cancelPendingCommit !== null 하나다
           자세한 것은 [렌더 루프]의 spi 에 있다
       예 => prepareFreshStack(L1002) + markRootSuspended(L1004)
            **early return 이 없다. 아래로 그대로 흐른다**

 L1013 markRootUpdated(root, lane)          언제나 돈다

 L1015 렌더 페이즈 중에 온 갱신인가
       예 (L1016-1030)
         L1024  warnAboutRenderPhaseUpdatesInDEV(fiber)
         L1027  renderPhaseUpdatedLanes 에 합친다
         **ensureRootIsScheduled 를 안 부른다** => 끝

       아니오 (L1031-1098)
         L1034  [enableUpdaterTracking] devtools 에 기록
         L1040  warnIfUpdatesNotWrappedWithActDEV(fiber)
         L1042  [enableTransitionTracing] transition 기록
         L1053  root 가 workInProgressRoot 면 독립 if 가 둘
                  L1056  렌더 중이 아니면 interleaved lanes 에 합친다
                  L1062  RootSuspendedWithDelay 면 markRootSuspended
                  **둘 다 돌 수 있다**
         L1079  ensureRootIsScheduled(root)
         L1080  네 조건이 전부 맞으면 legacy sync flush
                  이 빌드에서는 안 돈다 (아래 참고)
```

```text
 이 흐름이 끝나는 자리는 ensureRootIsScheduled 안이다

 ReactFiberRootScheduler.js L116 의 주석이 직접 말한다 (L117-122)

   "This function is called whenever a root receives an update. It does two
    things 1) it ensures the root is in the root schedule, and 2) it ensures
    there's a pending microtask to process the root schedule."

   "Most of the actual scheduling logic does not happen until
    `scheduleTaskForRootDuringMicrotask` runs."

 실제 경계
   L125-134  root 를 스케줄 연결 리스트에 넣는다
   L139      mightHavePendingSyncWork = true
   L141      ensureScheduleIsScheduled()
   L164      didScheduleMicrotask 가 false 일 때만 아래로
   L667      scheduleMicrotask(() => { ... processRootScheduleInMicrotask() })

 즉 root.render() 가 돌아온 시점에 정해진 것은
 "할 일이 있다" 와 "곧 처리한다" 뿐이다
 우선순위도 태스크도 마이크로태스크 안에서 정한다
```

```text
 L1015 의 if 쪽은 스케줄을 안 한다

 하는 일이 둘뿐이다 - 경고와 lane 기록
 ensureRootIsScheduled 는 else 블록 안 L1079 에만 있다

 주석이 그 사정을 말한다 (L1019-1023)
 렌더 중 갱신은 원칙적으로 실수지만
 selective hydration 같은 내부 기능이 일부러 쓴다고 적혀 있다
```

```text
 legacy sync flush 는 이 빌드에서 죽어 있다

 조건이 넷이다 (L1080-1084)
   lane === SyncLane
   executionContext === NoContext        <- & 가 아니라 === 다. 어떤 문맥에도 없어야 한다
   !disableLegacyMode
   (fiber.mode & ConcurrentMode) === NoMode

 셋째가 react-dom 에서 언제나 거짓이다 (기본값 true)
 넷째도 독립적으로 거짓이다 - 루트 fiber 가 언제나 ConcurrentMode 라서

 즉 이중으로 막혀 있다. 자세한 것은 spi 에 있다
```

```text
 markRootUpdated 는 그냥 표시가 아니다

 L1013 이 부르는 것은 ReactFiberLane 의 함수가 아니라
 이 파일의 지역 래퍼다 (L1749-1762)

 그 안에서 원본을 부른 뒤
 [enableInfiniteRenderLoopDetection] 이면 무한 루프를 감지해 던질 수 있다

 기본값이 false 라 이 빌드에서는 표시만 한다
 (그 플래그가 켜진 빌드는 확인하지 못했다)
```

```text
 L992 블록에 early return 이 없다

 그래서 "멈춰 있던 렌더를 버리고" 나서도
 L1013 과 그 아래 갈래를 그대로 탄다

 R7("markRootUpdated 는 언제나 돈다")이 성립하는 이유가 이것이다
```

## 결과가 쓰이는 곳

```text
 root.pendingLanes (markRootUpdated 가 세운다)
      --> 마이크로태스크가 이것을 보고 우선순위를 정한다
      --> 비어 있으면 할 일이 없다고 판단한다

 스케줄 연결 리스트 (firstScheduledRoot / lastScheduledRoot)
      --> 마이크로태스크가 이 리스트를 훑는다
      --> 루트가 여럿이면 여기 줄줄이 달린다

 걸린 마이크로태스크
      --> processRootScheduleInMicrotask 가 실제 스케줄링을 한다
      --> 그것이 흐름 2다

 renderPhaseUpdatedLanes
      --> 렌더 중 갱신은 현재 렌더가 끝난 뒤 처리된다
```

## 다루지 않는 것

`ensureRootIsScheduled` 이후의 `processRootScheduleInMicrotask` 와 `scheduleTaskForRootDuringMicrotask`(흐름 2), `prepareFreshStack` 과 `markRootSuspended` 의 내용, `requestUpdateLane` 이 lane 을 고르는 네 단계, `throwIfInfiniteUpdateLoopDetected` 의 판정, `warnAboutRenderPhaseUpdatesInDEV` 와 `warnIfUpdatesNotWrappedWithActDEV` 의 본문, `SuspendedOnData` / `SuspendedOnAction` 이 왜 세워지지 않는지(그쪽은 [렌더 루프](../../render-loop/spi/README.md)의 spi 에 있다)는 같은 뼈대의 곁가지라 요약만 했다. 빌드 플래그는 [spi](../spi/README.md)에 모았다.
