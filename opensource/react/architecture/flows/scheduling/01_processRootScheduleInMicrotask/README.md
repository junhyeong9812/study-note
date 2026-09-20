# processRootScheduleInMicrotask

상위: [스케줄링](../README.md)

마이크로태스크의 본체다. **루트 리스트를 두 번 훑고**, 그 사이에 동기 작업을 그 자리에서 돌린다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L259-L348 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L259-L348))

## 실제 코드

문을 다시 여는 것부터 한다.

```js
// ReactFiberRootScheduler.js L262-L268
  didScheduleMicrotask = false;
  if (__DEV__) {
    didScheduleMicrotask_act = false;
  }

  // We'll recompute this as we iterate through all the roots and schedule them.
  mightHavePendingSyncWork = false;
```

> This function is always called inside a microtask. It should never be called synchronously.

리스트를 훑으며 빈 루트를 뺀다.

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L289-L332 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L289-L332))

```js
// ReactFiberRootScheduler.js L300-L311
      // Null this out so we know it's been removed from the schedule.
      root.next = null;
      if (prev === null) {
        // This is the new head of the list
        firstScheduledRoot = next;
      } else {
        prev.next = next;
      }
      if (next === null) {
        // This is the new tail of the list
        lastScheduledRoot = prev;
      }
```

> To guard against subtle reentrancy bugs, this microtask is the only place we do this — you can add roots to the schedule whenever, but you can only remove them here.

그리고 맨 끝에서 동기 작업을 돌린다.

```js
// ReactFiberRootScheduler.js L334-L341
  // At the end of the microtask, flush any pending synchronous work. This has
  // to come at the end, because it does actual rendering work that might throw.
  // If we're in the middle of a View Transition async sequence, we don't want to
  // interrupt that sequence. Instead, we'll flush any remaining work when it
  // completes.
  if (!hasPendingCommitEffects()) {
    flushSyncWorkAcrossRoots_impl(syncTransitionLanes, false);
  }
```

## 동작 흐름

```text
 L262  didScheduleMicrotask = false       다음 예약을 받을 수 있게 연다
 L263  [__DEV__] didScheduleMicrotask_act 도 연다 (L264)
 L268  mightHavePendingSyncWork = false   아래에서 다시 계산한다

 L271  currentEventTransitionLane 이 있으면 syncTransitionLanes 를 정한다
         L272  shouldAttemptEagerTransition() 이면 그 lane 을 쓴다
               주석 L273-275: popstate 에서 이전 페이지 스크롤 위치를 지키려고
                              transition 을 동기로 렌더한다
         L277  [enableDefaultTransitionIndicator] 면 DefaultLane 을 쓴다

 L290  root = firstScheduledRoot
 L291  리스트를 훑는다
         L293  nextLanes = scheduleTaskForRootDuringMicrotask(root, currentTime)
         L294  NoLane 이면 리스트에서 뺀다 (L301-311)
         L312  아니면 남기고
         L320    sync 관련이면 mightHavePendingSyncWork = true (L328)

 L339  hasPendingCommitEffects() 가 아니면
 L340    flushSyncWorkAcrossRoots_impl(syncTransitionLanes, false)

 L343  currentEventTransitionLane 을 되돌리고
 L346    startDefaultTransitionIndicatorIfNeeded()
```

```text
 L262 가 먼저 오는 이유

 didScheduleMicrotask 는 "마이크로태스크가 예약돼 있다" 는 표시다
 여기서 false 로 되돌려야 이 마이크로태스크가 도는 동안 들어온 갱신이
 다음 마이크로태스크를 예약할 수 있다

 만약 맨 끝에서 되돌리면
 L340 의 렌더 중에 생긴 갱신이 예약을 못 한다

 (주석은 없다. 두 자리의 순서와 ensureScheduleIsScheduled 의 조건을 보고
  내가 판단한 것이다)
```

```text
 리스트를 두 번 훑는다

 L291  스케줄 결정 + 빈 루트 제거
 L358  인디케이터를 켤 루트 찾기 (startDefaultTransitionIndicatorIfNeeded 안)

 두 번째 루프는 플래그가 꺼져 있으면 함수 첫 줄에서 돌아온다 (L351-353)
   if (!enableDefaultTransitionIndicator) { return; }

 그 플래그는 호출부 L346 에 없다. 함수 안에 있다
 호출만 보고는 분기를 알 수 없는 자리다
```

```text
 제거를 여기서만 하는 이유

 주석이 "subtle reentrancy bugs" 를 막으려는 것이라고 적는다 (L295-298)

 넣는 쪽은 ensureRootIsScheduled 가 언제든 한다 (L125-134)
 그쪽은 링크만 걸므로 순회 중에 끼어들어도 안전하다

 빼는 것은 prev/next 를 다시 이어야 해서
 순회 중에 여러 곳에서 하면 리스트가 깨진다
 (뒷문장은 주석에 없다. 제거 코드의 모양을 보고 내가 붙인 것이다)
```

```text
 L339 의 가드와 L334-338 의 주석

   "At the end of the microtask, flush any pending synchronous work. This has
    to come at the end, because it does actual rendering work that might throw.
    If we're in the middle of a View Transition async sequence, we don't want to
    interrupt that sequence. Instead, we'll flush any remaining work when it
    completes."

 두 가지를 말한다
   맨 끝이어야 하는 이유 - 렌더는 던질 수 있다
   건너뛰는 조건 - View Transition 중이면 끊지 않는다

 L339 의 hasPendingCommitEffects() 가 그 둘째 조건이다
```

```text
 L340 이 L343 보다 먼저여야 하는 이유가 하나 더 있다

 주석 L334-338 은 "렌더가 던질 수 있어서" 만 말한다
 그런데 순서 의존성이 하나 더 있고 그건 주석에 없다

 L340 의 렌더가 커밋까지 가면
   커밋 쪽이 markIndicatorHandled(root) 를 부를 수 있고 (L730)
   그 안에서 root.indicatorLanes &= ~currentEventTransitionLane 을 한다 (L735)

 그런데 L345 가 currentEventTransitionLane 을 NoLane 으로 되돌린다

 만약 L345 가 먼저 돌면 ~NoLane 이라 아무것도 안 지워지고
 L346 의 루프가 이미 처리된 인디케이터를 다시 켠다

 (주석은 없다. 세 자리를 이어 보고 내가 판단한 것이다.
  검증 과정에서 확인된 것이고 나도 L730-736 을 읽었다)


 이 함수로 들어오는 길이 셋이다

 L687  실제 마이크로태스크 안
 L658  act 큐에 넣은 콜백 안
 L256  processRootScheduleInImmediateTask 안 (매크로태스크 폴백)

 주석 L260-261 의 "never be called synchronously" 는
 "동기로 부르지 마라" 는 뜻이지 "호출처가 하나다" 는 뜻이 아니다
 (grep 범위: packages 전체 *.js, __tests__ 제외)
```

## 결과가 쓰이는 곳

```text
 정리된 스케줄 리스트
      --> 할 일 있는 루트만 남는다
      --> 다음 마이크로태스크가 그것을 다시 훑는다

 mightHavePendingSyncWork
      --> [03] 의 빠른 탈출 조건이다
      --> 이 루프에서 다시 계산한 값이다

 didScheduleMicrotask = false
      --> 다음 갱신이 새 마이크로태스크를 예약할 수 있게 한다

 걸린 스케줄러 태스크들
      --> [02] 가 루트마다 걸어 둔 것이다
      --> 이 함수가 돌아간 뒤 브라우저가 부른다
```

## 다루지 않는 것

`shouldAttemptEagerTransition` 의 판정, `hasPendingCommitEffects` 가 보는 상태, `startIsomorphicDefaultIndicatorIfNeeded` 와 `retainIsomorphicIndicator` 의 인디케이터 공유, `currentEventTransitionLane` 이 세워지는 자리(`requestTransitionLane`), `processRootScheduleInImmediateTask` 의 매크로태스크 폴백은 같은 뼈대의 곁가지라 요약만 했다.
