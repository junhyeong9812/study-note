# 스케줄링

[마운트](../mount/README.md)가 건 마이크로태스크가 깨어나 **렌더 태스크를 걸기까지**다.

이 흐름의 핵심은 **결정을 미뤘다가 한꺼번에 한다**는 것이다. 갱신이 들어올 때는 "이 루트에 할 일이 있다"만 기록하고, 마이크로태스크가 깨어나서야 어느 루트를 어떤 우선순위로 처리할지 정한다. 그리고 동기 작업은 **태스크를 걸지 않고 이 마이크로태스크 안에서 그대로 렌더한다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberRootScheduler.js` 기준이다.

## 전체 그림

```text
 ~~> 마이크로태스크가 깨어난다                      L667 이 건 것

 [01] processRootScheduleInMicrotask              L259
      +-- didScheduleMicrotask = false             L262   문을 다시 연다
      +-- 루트 리스트를 훑는다                      L291
      |     +-- [02] scheduleTaskForRootDuringMicrotask
      |     +-- NoLane 이면 리스트에서 뺀다          L294
      +-- [03] flushSyncWorkAcrossRoots_impl        L340
      |     +-- performSyncWorkOnRoot -> performWorkOnRoot
      |         **이 스택에서 렌더까지 돈다**
      +-- 리스트를 한 번 더 훑는다                   L358
            인디케이터를 켤 루트를 찾는다

 [02] scheduleTaskForRootDuringMicrotask          L384
      갈래 셋
        할 일 없음/멈춤  => 콜백 취소, NoLane 반환         L420
        sync            => 태스크를 안 걸고 SyncLane 반환  L442
        그 외            => ~~> scheduleCallback(...)      L500

 ~~> 스케줄러가 매크로태스크로 부른다

 [04] performWorkOnRootViaSchedulerTask           L513
      +-- performWorkOnRoot(root, lanes, forceSync)   L590  <- 흐름 3
      +-- [02] 를 다시 불러 다음 태스크를 정한다       L599
      +-- 같은 태스크면 continuation 을 돌려준다       L603
```

```text
 동기와 비동기가 갈리는 자리

 [02] 가 sync lane 을 보면 태스크를 안 건다 (L442-456)
 주석이 이유를 말한다 (L449-450)

   "Synchronous work is always flushed at the end of the microtask, so we
    don't need to schedule an additional task."

 그리고 그 "end of the microtask" 가 [03] 이다 (L340)
 거기서 performSyncWorkOnRoot -> performWorkOnRoot 로 **같은 스택에서** 렌더한다

 다만 주석의 "always" 는 코드보다 강하다
 L339 의 hasPendingCommitEffects() 가 참이면 flush 자체를 건너뛴다
 그러면 sync lane 인데도 이 마이크로태스크에서 안 돈다

 즉 sync 작업은 대체로 마이크로태스크 안에서 끝나고
 concurrent 작업만 스케줄러 태스크로 넘어간다
```

```text
 리스트에서 빼는 자리는 하나다

 주석이 규약으로 못박는다 (L295-298)

   "To guard against subtle reentrancy bugs, this microtask is the only place
    we do this — you can add roots to the schedule whenever, but you can
    only remove them here."

 넣는 것은 아무 데서나 할 수 있다 (ensureRootIsScheduled L125-134)
 빼는 것은 여기뿐이다
```

```text
 마이크로태스크가 리스트를 두 번 훑는다

 L291  스케줄을 정하고 빈 루트를 빼는 루프
 L358  인디케이터를 켤 루트를 찾는 루프

 두 번째는 enableDefaultTransitionIndicator 가 꺼져 있으면
 함수 첫 줄에서 바로 돌아온다 (L351-353)
 그 플래그는 호출부(L346)에 없고 함수 안에 있다
```

```text
 같은 파일에 정반대 규약이 있다

 processRootScheduleInMicrotask  L260-261
   "This function is always called inside a microtask.
    It should never be called synchronously."

 flushSyncWorkOnAllRoots         L172-173
   "This is allowed to be called synchronously, but the caller should check
    the execution context first."

 즉 함수마다 호출 규약이 다르다
 앞엣것은 마이크로태스크 전용이고, 뒤엣것은 flushSync() 류가 동기로 부른다
```

## 어디로 이어지는가

```text
 [렌더 루프]  performWorkOnRoot 가 fiber 트리를 훑는다
              동기 경로는 [03] 에서, 비동기 경로는 [04] 에서 들어간다
```

## 단계

1. [processRootScheduleInMicrotask](01_processRootScheduleInMicrotask/README.md)이 리스트를 훑고 정리한다.
2. [scheduleTaskForRootDuringMicrotask](02_scheduleTaskForRootDuringMicrotask/README.md)가 루트 하나의 운명을 정한다.
3. [flushSyncWorkAcrossRoots](03_flushSyncWorkAcrossRoots/README.md)가 동기 작업을 그 자리에서 돌린다.
4. [performWorkOnRootViaSchedulerTask](04_performWorkOnRootViaSchedulerTask/README.md)가 비동기 태스크의 진입점이다.

## 결과가 쓰이는 곳

```text
 root.callbackNode / root.callbackPriority
      --> 다음 마이크로태스크가 태스크를 재사용할지 판단한다
      --> 스케줄러가 돌려준 태스크 객체가 그대로 들어간다

 스케줄 연결 리스트
      --> 할 일이 없는 루트는 여기서 빠진다
      --> 빠진 루트는 다음 갱신 때 다시 들어온다

 performWorkOnRoot 호출
      --> 렌더 루프가 시작된다
      --> 동기든 비동기든 결국 같은 함수로 들어간다

 continuation
      --> [04] 가 자기 자신을 돌려주면 스케줄러가 같은 태스크로 이어 돌린다
```

## 다루지 않는 것

`Scheduler` 패키지의 태스크 큐와 타임 슬라이싱, `getNextLanes` / `markStarvedLanesAsExpired` / `checkIfRootIsPrerendering` 의 lane 계산, `performWorkOnRoot` 이후의 렌더 루프, `flushPendingEffects` 의 패시브 이펙트 처리, `startIsomorphicDefaultIndicatorIfNeeded` 의 인디케이터 관리, `requestTransitionLane` 의 transition lane 할당은 같은 뼈대의 곁가지라 요약만 했다. 빌드 플래그와 우선순위 대응은 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 processRootScheduleInMicrotask](01_processRootScheduleInMicrotask/README.md)
- [02 scheduleTaskForRootDuringMicrotask](02_scheduleTaskForRootDuringMicrotask/README.md)
- [03 flushSyncWorkAcrossRoots](03_flushSyncWorkAcrossRoots/README.md)
- [04 performWorkOnRootViaSchedulerTask](04_performWorkOnRootViaSchedulerTask/README.md)
- [spi](spi/README.md) — 우선순위 대응과 플래그
