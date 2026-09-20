# flushSpawnedWork

상위: [커밋 흐름](../README.md)

커밋의 **마지막 단계**다. 페인트를 요청하고, 패시브 단계를 열어 주고, 다음 렌더를 다시 스케줄한다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L4135-L4418 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L4135-L4418))

## 실제 코드

가드가 기대값 둘을 받는다.

```js
// ReactFiberWorkLoop.js L4136-L4143
  if (
    pendingEffectsStatus !== PENDING_SPAWNED_WORK &&
    // If a startViewTransition times out, we might flush this earlier than
    // after mutation phase. In that case, we just skip the after mutation phase.
    pendingEffectsStatus !== PENDING_AFTER_MUTATION_PHASE
  ) {
    return;
  }
```

> If a `startViewTransition` times out, we might flush this earlier than after mutation phase. In that case, we just skip the after mutation phase.

그리고 패시브 단계를 여는 한 줄.

```js
// ReactFiberWorkLoop.js L4190-L4190
    pendingEffectsStatus = PENDING_PASSIVE_PHASE;
```

## 동작 흐름

```text
 WL L4135  function flushSpawnedWork(): void

 L4136  가드 - PENDING_SPAWNED_WORK 도 PENDING_AFTER_MUTATION_PHASE 도 아니면
 L4142    return

 L4144  [FLAG:enableProfilerTimer] 애니메이션 시작 여부 판정과 로깅
 L4163  pendingEffectsStatus = NO_PENDING_EFFECTS
 L4165  committedViewTransition = pendingViewTransition
 L4166  pendingViewTransition = null

 L4170  requestPaint()                         ** 여기서 페인트를 요청한다 **

 L4172  전역들을 지역으로 스냅샷
 L4178  패시브 마스크 판정 (PassiveMask 또는 PassiveTransitionMask)
 L4189  rootDidHavePassiveEffects 이면
 L4190    pendingEffectsStatus = PENDING_PASSIVE_PHASE     ** 허가 **
 L4191  아니면
 L4192    pendingEffectsStatus = NO_PENDING_EFFECTS
 L4193    pendingEffectsRoot = null / L4194 pendingFinishedWork = null
 L4201    releaseRootPooledCache(...)

 L4205  남은 lane 정리
 L4223  [FLAG:__DEV__] StrictMode 이중 호출
 L4229  onCommitRootDevTools
 L4242  onRecoverableError 보고
 L4271  뷰 트랜지션 이벤트 발사
 L4305  sync lane 이면 패시브를 **즉시** flush
 L4314  ensureRootIsScheduled(root)            <- [스케줄링]으로 돌아간다
 L4323  중첩 업데이트 횟수 검사
 L4378  flushHydrationEvents
 L4382  flushSyncWorkOnAllRoots
 L4388  [FLAG:enableTransitionTracing] transition tracing
 L4418  }
```

```text
 ★ 가드가 기대값을 둘 받는다

 다른 flush 는 하나만 받는데 이것만 둘이다

 L4137  pendingEffectsStatus !== PENDING_SPAWNED_WORK &&
 L4140  pendingEffectsStatus !== PENDING_AFTER_MUTATION_PHASE

 주석이 이유를 적는다 (L4138-4139)
   뷰 트랜지션이 타임아웃하면 after-mutation 보다 일찍 불릴 수 있고,
   그러면 after-mutation 단계를 그냥 건너뛴다

 => "순서가 어긋나면 return" 이 아니라
    "한 단계 건너뛰고 진행" 하는 정식 경로가 하나 있다
```

```text
 0 으로 지우는 것이 즉시가 아니다

 다른 flush 들은 가드 바로 다음 줄에서 0 으로 지우는데
 이 함수는 L4144-4161 프로파일러 블록이 먼저 돌고
 L4163 에서 지운다

 그리고 그 블록이 pendingEffectsStatus 를 읽어 분기한다 (L4146)
   const startedAnimation = pendingEffectsStatus === PENDING_SPAWNED_WORK;
 => 지우기 전에 읽어야 해서 순서가 이렇다
```

```text
 패시브는 여기서 "열린다"

 예약은 이미 commitRoot L3787 에서 끝나 있다.
 이 줄이 하는 일은 그 콜백이 실제로 뭔가 하도록 상태를 여는 것이다

 L4190  pendingEffectsStatus = PENDING_PASSIVE_PHASE

 패시브 효과가 없으면 반대로 정리한다 (L4192-4201)
   상태 0, pendingEffectsRoot / pendingFinishedWork 를 null 로 (GC)
   releaseRootPooledCache

 그리고 sync lane 이면 기다리지 않는다
   L4305  같은 태스크 안에서 flushPendingEffects() 로 당겨 실행한다
```

```text
 이 흐름이 스스로 다시 스케줄한다

 L4314  ensureRootIsScheduled(root)

 커밋이 끝났어도 남은 lane 이 있으면 다음 태스크가 걸린다
 [렌더 루프]의 L1310 과 같은 자리다

 => 마운트 -> 스케줄링 -> 렌더 루프 -> 커밋 -> 스케줄링 으로
    고리가 닫힌다
```

```text
 감싸지 않는 사용자 코드가 여기 있다

 커밋 중 사용자 코드는 대개 try/catch 로 감싸
 captureCommitPhaseError 로 보내는데, 이 함수에는 예외가 둘 있다

 L4247-4268  onRecoverableError 호출
             try 와 finally 는 있는데 **catch 가 없다**
             => 사용자가 준 콜백이 던지면 그대로 새어 나간다

 L4286-4292  뷰 트랜지션 이벤트 콜백
             아예 감싸지 않는다

 (이 둘은 검증 과정에서 지적된 것이고,
  나는 L4247-4268 의 try/finally 구조만 직접 확인했다)
```

## 결과가 쓰이는 곳

```text
 requestPaint()
      --> 브라우저에 페인트를 요청한다

 pendingEffectsStatus = PENDING_PASSIVE_PHASE
      --> [패시브 이펙트]의 가드를 연다

 ensureRootIsScheduled
      --> [스케줄링]으로 돌아간다. 고리가 닫힌다

 onRecoverableError
      --> 렌더 중 복구된 에러를 사용자에게 알린다
```

## 다루지 않는 것

`requestPaint` 의 스케줄러 쪽 구현, `onCommitRootDevTools` 와 DevTools 연동, 무한 업데이트 루프 감지(L4323-4366)의 한도와 판정, `flushHydrationEvents` 와 수화 이벤트, `flushSyncWorkOnAllRoots`, transition tracing(L4388-4417), `releaseRootPooledCache` 와 캐시 수명, StrictMode 이중 호출(L4223-4227)은 같은 뼈대의 곁가지라 요약만 했다. 에러 처리 규칙은 [spi](../spi/README.md)에 있다.
