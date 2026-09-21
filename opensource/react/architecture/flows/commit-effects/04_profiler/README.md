# 프로파일러

상위: [커밋 이펙트](../README.md)

`<Profiler onRender>` 가 불리는 자리다. **이 무리는 프로파일링 빌드에서만 산다** — 죽은 코드가 아니라 빌드가 다르면 도는 코드다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberCommitEffects.js` L936-L1045 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitEffects.js#L936-L1045))

## 실제 코드

콜백 둘을 부른다.

```js
// ReactFiberCommitEffects.js L936-L970
function commitProfiler(
  finishedWork: Fiber,
  current: Fiber | null,
  commitStartTime: number,
  effectDuration: number,
) {
  const {id, onCommit, onRender} = finishedWork.memoizedProps as ProfilerProps;

  let phase: ProfilerPhase = current === null ? 'mount' : 'update';
  if (enableProfilerNestedUpdatePhase) {
    if (isCurrentUpdateNested()) {
      phase = 'nested-update';
    }
  }

  if (typeof onRender === 'function') {
    onRender(
      id,
      phase,
      // $FlowFixMe[incompatible-type]: This should be always a number in profiling mode
      finishedWork.actualDuration,
      // $FlowFixMe[incompatible-type]: This should be always a number in profiling mode
      finishedWork.treeBaseDuration,
      // $FlowFixMe[incompatible-type]: This should be always a number in profiling mode
      finishedWork.actualStartTime,
      commitStartTime,
    );
  }

  if (enableProfilerCommitHooks) {
    if (typeof onCommit === 'function') {
      onCommit(id, phase, effectDuration, commitStartTime);
    }
  }
}
```

바깥이 플래그로 감싼다.

```js
// ReactFiberCommitEffects.js L972-L996
export function commitProfilerUpdate(
  finishedWork: Fiber,
  current: Fiber | null,
  commitStartTime: number,
  effectDuration: number,
) {
  if (enableProfilerTimer) {
    try {
      if (__DEV__) {
        runWithFiberInDEV(
          finishedWork,
          commitProfiler,
          finishedWork,
          current,
          commitStartTime,
          effectDuration,
        );
      } else {
        commitProfiler(finishedWork, current, commitStartTime, effectDuration);
      }
    } catch (error) {
      captureCommitPhaseError(finishedWork, finishedWork.return, error);
    }
  }
}
```

그런데 post-commit 쪽은 감싸지 않는다.

```js
// ReactFiberCommitEffects.js L1018-L1045
export function commitProfilerPostCommit(
  finishedWork: Fiber,
  current: Fiber | null,
  commitStartTime: number,
  passiveEffectDuration: number,
) {
  try {
    if (__DEV__) {
      runWithFiberInDEV(
        finishedWork,
        commitProfilerPostCommitImpl,
        finishedWork,
        current,
        commitStartTime,
        passiveEffectDuration,
      );
    } else {
      commitProfilerPostCommitImpl(
        finishedWork,
        current,
        commitStartTime,
        passiveEffectDuration,
      );
    }
  } catch (error) {
    captureCommitPhaseError(finishedWork, finishedWork.return, error);
  }
}
```

## 동작 흐름

```text
 commitProfiler  L936-970

 L942  {id, onCommit, onRender} = finishedWork.memoizedProps
 L944  phase = current === null ? 'mount' : 'update'
 L945  [FLAG:enableProfilerNestedUpdatePhase]
 L946    isCurrentUpdateNested() 이면
 L947      phase = 'nested-update'

 L951  typeof onRender === 'function' 이면
 L952    onRender(id, phase,
                  finishedWork.actualDuration,
                  finishedWork.treeBaseDuration,
                  finishedWork.actualStartTime,
                  commitStartTime)

 L965  [FLAG:enableProfilerCommitHooks]
 L966    typeof onCommit === 'function' 이면
 L967      onCommit(id, phase, effectDuration, commitStartTime)
```

```text
 ★ onRender 는 플래그 가드가 없고 onCommit 은 있다

 L951  onRender  — 타입 검사만 한다
 L965  onCommit  — enableProfilerCommitHooks 안이다

 다만 바깥 commitProfilerUpdate 의 `if (enableProfilerTimer)`(L978)가
 둘 다를 덮는다. 그래서 실제 차이는 두 플래그가 갈리는 빌드에서만 보인다
 (둘 다 __PROFILE__ 이라 기본 포크에서는 같이 켜지고 같이 꺼진다)
```

```text
 ★★ 바깥 둘의 가드가 다르다

 commitProfilerUpdate      L972-996
   L978  if (enableProfilerTimer) {      ★ 감싼다
   L979    try { ... } catch { captureCommitPhaseError(...) }

 commitProfilerPostCommit  L1018-1045
   L1024  try { ... } catch { ... }      ★ **플래그 가드가 없다**

 부르는 쪽도 안 감싼다. 확인해 보면 이렇다
   CMW L3805  case Profiler: {
   CMW L3807    if (flags & Passive) {
   CMW L3820      if (enableProfilerTimer && enableProfilerCommitHooks) {
   CMW L3826      }                       ** 여기서 닫힌다 **
   CMW L3828      commitProfilerPostCommit(...)   <- 그 밖이다

 그러면 플래그가 꺼진 빌드에서 onPostCommit 이 불리는가? 아니다.
 **관문이 두 파일 위에 있다**

   BW L1364  if (enableProfilerTimer) {
   BW L1365    workInProgress.flags |= Update
   BW L1367    if (enableProfilerCommitHooks) {
   BW L1371      workInProgress.flags |= Passive    ★ 여기가 진짜 관문이다
   주석 BW L1368-1370 - "Schedule a passive effect for this Profiler to call
     onPostCommit hooks. This effect should be scheduled even if there is no
     onPostCommit callback for this Profiler, because the effect is also where
     times bubble to parent Profilers."

 플래그가 꺼지면 Profiler fiber 에 Passive 가 안 붙고,
 CMW L3807 의 `if (flags & Passive)` 가 거짓이라 L3828 에 닿지 않는다

 => 가드가 없는 것이 아니라 **세우는 자리에 있다**
 ★ 딸린 불변식 - Passive 가 붙었으면 stateNode 가 있다.
   BW L1374-1375 가 같은 if 안에서 그 객체를 초기화하고,
   CMW L3833 이 profilerInstance.passiveEffectDuration 을 가드 없이 읽는다
```

```text
 ★ phase 가 셋이다

 'mount'          current === null
 'update'         그 밖
 'nested-update'  isCurrentUpdateNested() 이고 플래그가 켜졌을 때

 commitProfilerPostCommitImpl(L998)도 같은 셋이다 (L1006, L1009).
 두 함수가 같은 세 줄을 따로 갖는다

 주석 shared/ReactFeatureFlags.js L250 -
   "Phase param passed to onRender callback differentiates between an
    "update" and a "cascading-update"."
 ★ 주석은 "cascading-update" 라 부르는데 코드는 'nested-update' 를 넣는다.
   이름이 어긋난다
```

```text
 ★★ 이 무리는 [DEAD] 가 아니라 빌드가 다르면 산다

 shared/ReactFeatureFlags.js
   L229  enableProfilerTimer = __PROFILE__
   L248  enableProfilerCommitHooks = __PROFILE__
   L251  enableProfilerNestedUpdatePhase = __PROFILE__
   L244  enableSchedulingProfiler = !enableComponentPerformanceTrack && __PROFILE__

 앞의 셋은 상수가 아니다. 프로파일링 빌드에서 켜진다

 ★★ 그런데 **넷째는 다르다**. 식을 끝까지 계산해야 한다
   L235  enableComponentPerformanceTrack: boolean = true
   L244  enableSchedulingProfiler = !enableComponentPerformanceTrack && __PROFILE__
   => !true && ... 이므로 **모든 react-dom 빌드에서 거짓**이다
   => [01]의 마커 블록 넷(L154-160 / L179-185 / L268-274 / L288-294)이
      프로파일링 빌드에서도 [DEAD] 다

 그리고 켜져도 fiber 단위 가드가 하나 더 있다 - L89 shouldProfile
   enableProfilerTimer && enableProfilerCommitHooks
   && (current.mode & ProfileMode) !== NoMode

 => <Profiler> 아래에 있는 fiber 만 타이머를 돈다
 ★ 그래서 [01]과 [02]의 `shouldProfile 이면 ... 아니면 ...` 갈래가
   프로덕션 빌드에서는 언제나 else 로 간다
```

```text
 ★ 타이머가 재는 것이 이 파일 곳곳에 있다

 startEffectTimer / recordEffectDuration 짝이
   [01] 훅 이펙트 래퍼 넷
   [02] componentDidMount / componentDidUpdate
   [03] ref 붙이기와 떼기
 에 각각 들어 있다

 그 합이 effectDuration 으로 onCommit 에 실린다 (L967)
 ※ 합산하는 자리는 이 파일 밖이라 확인하지 않았다
```

## 결과가 쓰이는 곳

```text
 onRender(id, phase, actualDuration, treeBaseDuration,
          actualStartTime, commitStartTime)
      --> 사용자 콜백. React DevTools Profiler 가 아니라
          <Profiler> 엘리먼트에 직접 넘긴 함수다

 onCommit(id, phase, effectDuration, commitStartTime)
      --> 커밋의 이펙트 시간

 onPostCommit(id, phase, passiveEffectDuration, commitStartTime)
      --> 패시브 이펙트까지 끝난 뒤

 captureCommitPhaseError
      --> 프로파일러 콜백이 던져도 커밋을 멈추지 않는다
```

## 다루지 않는 것

`actualDuration` / `treeBaseDuration` / `actualStartTime` 이 렌더 단계에서 쌓이는 방식(`ReactProfilerTimer`), `startEffectTimer` / `recordEffectDuration` 이 `effectDuration` 을 어디에 합산하는지, `isCurrentUpdateNested`(`ReactProfilerTimer`)가 중첩 업데이트를 판정하는 규칙, `ProfileMode` 가 트리에 붙는 자리, `enableComponentPerformanceTrack` 이 무엇을 켜는지, `ReactFiber.js` 가 `Profiler` fiber 의 `stateNode` 를 만드는 자리, `<Profiler>` fiber 가 `completeWork` 에서 하는 일([completeWork](../../complete-work/README.md)에 요약이 있다)은 이 문서의 범위 밖이다.
