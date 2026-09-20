# spi

상위: [스케줄링](../README.md)

이 흐름의 계약은 둘이다 — **언제 동기로 부를 수 있는가**와 **lane 이 스케줄러 우선순위로 어떻게 접히는가**.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 `ReactFiberRootScheduler.js` 기준이다.

## 호출 규약이 함수마다 다르다

같은 파일 안에서 정반대 주석이 공존한다.

| 함수 | 주석이 말하는 규약 |
|---|---|
| `processRootScheduleInMicrotask` L259 | "This function is always called inside a microtask. **It should never be called synchronously.**" (L260-261) |
| `scheduleTaskForRootDuringMicrotask` L384 | "always called inside a microtask, **or at the very end of a rendering task** right before we yield to the main thread. It should never be called synchronously." (L388-390) |
| `flushSyncWorkOnAllRoots` L171 | "**This is allowed to be called synchronously**, but the caller should check the execution context first." (L172-173) |
| `flushSyncWorkOnLegacyRootsOnly` L177 | 같은 문구 (L178-179) |

```text
 두 번째가 특히 눈에 띈다

 "or at the very end of a rendering task" 라는 예외가 주석에 미리 박혀 있다
 그것이 [04] L599 다

 즉 규약 위반처럼 보이는 호출을 계약 쪽에서 먼저 허용해 둔 것이다
```

```text
 그리고 하나 더 - 동기로 React 작업을 하지 않는다

 scheduleTaskForRootDuringMicrotask L392-393
   "This function also never performs React work synchronously; it should
    only schedule work to be performed later, in a separate task or microtask."

 이 약속 때문에 sync lane 도 그 자리에서 렌더하지 않고
 [03] 이 맡는다
```

## lane 이 우선순위로 접히는 표

`scheduleTaskForRootDuringMicrotask` L481-498.

| `lanesToEventPriority` 결과 | 스케줄러 우선순위 |
|---|---|
| `DiscreteEventPriority` | `UserBlockingSchedulerPriority` |
| `ContinuousEventPriority` | `UserBlockingSchedulerPriority` |
| `DefaultEventPriority` | `NormalSchedulerPriority` |
| `IdleEventPriority` | `IdleSchedulerPriority` |
| 그 외 | `NormalSchedulerPriority` |

```text
 이 표에 ImmediatePriority 가 없다 - 다만 범위가 한정돼 있다

 주석 (L482-484)
   "Scheduler does have an "ImmediatePriority", but now that we use
    microtasks for sync work we no longer use that. Any sync work that
    reaches this path is meant to be time sliced."

 **"this path"** 가 한정이다. 렌더 태스크를 거는 이 switch 에 한한 이야기다

 같은 파일의 다른 자리에서는 실제로 쓴다
   L682  Scheduler_scheduleCallback(ImmediateSchedulerPriority,
                                    processRootScheduleInImmediateTask)
   L692  같은 호출 (supportsMicrotasks 가 false 인 호스트)

 즉 "React 가 ImmediatePriority 를 안 쓴다" 가 아니라
 "렌더 태스크에는 안 쓴다" 다
```

```text
 sync lane 이 여기까지 오는 경우가 있다

 (나) 갈래(L442)의 조건이 둘이다
   includesSyncLane(nextLanes)
   && !checkIfRootIsPrerendering(root, nextLanes)

 prerendering 중이면 둘째가 거짓이라 (다)로 내려온다
 주석이 그 의도를 적는다 (L444-446)
   "If we're prerendering, then we should use the concurrent work loop
    even if the lanes are synchronous, so that prerendering never blocks
    the main thread."
```

## 루트 하나가 갖는 최종 상태

마이크로태스크가 한 번 돌고 났을 때.

| 상태 | 반환값 | `callbackNode` | `callbackPriority` | 리스트에 남나 | 렌더가 언제 |
|---|---|---|---|---|---|
| 할 일 없음 / 멈춤 | `NoLane` | `null` | `NoLane` | **아니오** | 안 돈다 |
| 동기 작업 | `SyncLane` | `null` | `SyncLane` | 예 | **이 마이크로태스크 끝에서** |
| 새 태스크 | 우선순위 lane | 새 태스크 객체 | 그 lane | 예 | 스케줄러 매크로태스크 |
| 태스크 재사용 | 우선순위 lane | 그대로 | 그대로 | 예 | 이미 걸린 태스크에서 |

```text
 "동기 작업" 줄이 특이하다

 callbackNode 가 null 인데 리스트에는 남는다
 태스크를 안 걸었기 때문이다 (L455)

 그래서 [03] 이 리스트를 훑을 때 이 루트를 찾아 돌린다
```

## 이 흐름의 빌드 플래그

```text
 호출부에 보이는 것

 __DEV__                          L263, L468, L630, L642, L651
 enableDefaultTransitionIndicator L277
 enableGestureTransition          L326, L234
 enableYieldingBeforePassive      L407
 enableProfilerTimer 조합          L520, L524, L617
 disableLegacyMode                L208
 disableSchedulerTimeoutInWorkLoop L589

 함수 안에 숨어 있는 것 (호출부에는 안 보인다)

 startDefaultTransitionIndicatorIfNeeded L351
   if (!enableDefaultTransitionIndicator) return;
   => 호출부 L346 에는 플래그가 없다

 flushSyncWorkOnLegacyRootsOnly L180
   if (!disableLegacyMode) { ... }
   => react-dom 에서 **함수 전체가 no-op**

 resetNestedUpdateFlag / syncNestedUpdateFlag
   ReactProfilerTimer 안에서 enableProfilerNestedUpdatePhase 로 한 번 더 가린다
   => 호출부와 함수 안에 같은 플래그가 이중으로 걸려 있다
```

```text
 __DEV__ 분기가 이 파일에 일곱이다 (L144, L157, L263, L468, L630, L642, L651)
 그중 스케줄 자체를 바꾸는 것은 넷이다

 L157  ensureScheduleIsScheduled 가 act 전용 dedupe 플래그를 쓴다
 L468  태스크 재사용 판정에 act 예외가 붙는다
 L630  scheduleCallback 이 act 큐에 push 한다
 L651  scheduleImmediateRootScheduleTask 가 act 큐에도 넣는다

 그리고 "act 안에서는 실제 스케줄러를 안 쓴다" 는 틀렸다

 L651 블록에 return 이 없어서 L666 의 진짜 scheduleMicrotask 도 걸린다
 L681-684 의 Safari 갈래는 act 큐를 안 거치고 Scheduler 를 직접 쓴다
 L691-694 도 마찬가지다

 정확히는 **렌더 태스크(L500)만** act 큐로 가고
 루트 스케줄 자체는 act 안에서도 실제 경로를 쓴다
```

## 결과가 쓰이는 곳

```text
 호출 규약
      --> 이 파일의 함수를 다른 곳에서 부를 때 지켜야 한다
      --> flushSync() 류는 실행 문맥을 먼저 확인할 책임이 있다

 우선순위 대응
      --> 스케줄러가 태스크 순서를 정하는 근거다
      --> 같은 우선순위면 태스크를 재사용한다

 플래그
      --> 어느 분기가 실제로 도는지를 정한다
      --> 호출부만 보면 절반을 놓친다
```

## 다루지 않는 것

`lanesToEventPriority` 와 `getHighestPriorityLane` 의 lane 매핑 규칙, `Scheduler` 패키지의 우선순위별 타임아웃, `act` 큐의 소비 방식(`flushActQueue`), `ReactFeatureFlags` 의 나머지 플래그와 포크별 값, `checkIfRootIsPrerendering` 의 prerendering 판정은 이 문서의 범위 밖이다.
