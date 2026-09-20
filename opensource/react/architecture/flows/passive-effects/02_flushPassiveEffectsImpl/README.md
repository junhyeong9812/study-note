# flushPassiveEffectsImpl

상위: [패시브 이펙트 흐름](../README.md)

실제로 돌리는 쪽이다. 전역을 먼저 지우고, 정리하고, 실행하고, **마지막에 동기 작업을 한 번 더 돌린다.**

## 위치

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L4709-L4856 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L4709-L4856))

## 실제 코드

전역을 먼저 지운다. GC 를 의식한 주석이 붙어 있다.

```js
// ReactFiberWorkLoop.js L4714-L4722
  const root = pendingEffectsRoot;
  const lanes = pendingEffectsLanes;
  pendingEffectsStatus = NO_PENDING_EFFECTS;
  pendingEffectsRoot = null as any; // Clear for GC purposes.
  pendingFinishedWork = null as any; // Clear for GC purposes.
  // TODO: This is sometimes out of sync with pendingEffectsRoot.
  // Figure out why and fix it. It's not causing any known issues (probably
  // because it's only used for profiling), but it's a refactor hazard.
  pendingEffectsLanes = NoLanes;
```

> TODO: This is **sometimes** out of sync with `pendingEffectsRoot`. Figure out why and fix it. It's not causing any **known** issues (**probably** because it's **only** used for profiling), but it's a refactor hazard.

재진입 방어선.

```js
// ReactFiberWorkLoop.js L4730-L4732
  if ((executionContext & (RenderContext | CommitContext)) !== NoContext) {
    throw new Error('Cannot flush passive effects while already rendering.');
  }
```

정리와 실행.

```js
// ReactFiberWorkLoop.js L4769-L4776
  commitPassiveUnmountEffects(root.current);
  commitPassiveMountEffects(
    root,
    root.current,
    lanes,
    transitions,
    pendingEffectsRenderEndTime,
  );
```

그리고 끝이 아니다.

```js
// ReactFiberWorkLoop.js L4799-L4799
  flushSyncWorkOnAllRoots();
```

## 동작 흐름

```text
 WL L4709  function flushPassiveEffectsImpl()

 L4711  transitions = pendingPassiveTransitions
 L4712  pendingPassiveTransitions = null
 L4714  root = pendingEffectsRoot
 L4715  lanes = pendingEffectsLanes
 L4716  pendingEffectsStatus = NO_PENDING_EFFECTS
 L4717  pendingEffectsRoot = null       // Clear for GC purposes.
 L4718  pendingFinishedWork = null      // Clear for GC purposes.
 L4722  pendingEffectsLanes = NoLanes

 L4724  [FLAG:enableYieldingBeforePassive]
 L4726    root.callbackNode = null
 L4727    root.callbackPriority = NoLane

 L4730  (executionContext & (RenderContext | CommitContext)) !== NoContext 이면
 L4731    => throw new Error('Cannot flush passive effects while already rendering.')

 L4740  [FLAG:__DEV__]
 L4741    isFlushingPassiveEffects = true
 L4742    didScheduleUpdateDuringPassiveEffects = false

 L4766  prevExecutionContext = executionContext
 L4767  executionContext |= CommitContext

 L4769  commitPassiveUnmountEffects(root.current)      ** 정리 **
 L4770  commitPassiveMountEffects(root, root.current, lanes,
                                  transitions, pendingEffectsRenderEndTime)  ** 실행 **

 L4782  [FLAG:__DEV__]
 L4783    commitDoubleInvokeEffectsInDEV(root, true)
 L4786  executionContext = prevExecutionContext

 L4799  flushSyncWorkOnAllRoots()      ** 동기 작업을 그 자리에서 돌린다 **

 L4822  [FLAG:__DEV__] 중첩 패시브 갱신 카운트
 L4839  [FLAG:enableYieldingBeforePassive]
 L4844    ensureRootIsScheduled(root)
 L4848  onPostCommitRootDevTools(root)
 L4855  => return true
```

```text
 ★ L4799 가 이 흐름을 고리로 만든다

 패시브 이펙트 안에서 setState 를 하면 sync 작업이 쌓인다.
 이 줄이 그것을 **여기서** 돌린다

 그래서 completeRoot 가 이 함수를 루프로 부른다 (WL L3511-3519)
   do { flushPendingEffects(); }
   while (pendingEffectsStatus !== NO_PENDING_EFFECTS);

 한 번 비워도 그 과정에서 또 쌓일 수 있기 때문이다
 주석이 그 사정을 적는다 (WL L3512-3516 부근)
```

```text
 전역을 먼저 지우는 순서가 의미를 갖는다

 L4716 에서 pendingEffectsStatus 를 0 으로 만든다.
 그 다음에야 이펙트를 돌린다 (L4769-4770)

 => 이펙트 안에서 flushPassiveEffects 가 다시 불려도
    L4673 가드에 걸려 no-op 한다

 그리고 L4717-4718 은 GC 목적이라고 주석이 밝힌다
 큰 fiber 트리를 모듈 전역이 붙들고 있지 않게 한다
```

```text
 executionContext 복원에 try/finally 가 없다

 L4767  executionContext |= CommitContext
 ...    L4769 정리 / L4770 실행 / L4783 DEV 이중 호출
 L4786  executionContext = prevExecutionContext

 그 사이에 try 가 없다.
 => 이펙트가 위로 던지면 CommitContext 가 세워진 채로 남는다
    L4741 의 isFlushingPassiveEffects 도 마찬가지다

 바깥 [01]의 finally 는 우선순위와 캐시 풀만 되돌리고
 executionContext 는 건드리지 않는다

 (이펙트 안의 에러가 아래 단계에서 잡혀 여기까지 안 올라오는지는
  확인하지 못했다. [커밋]에서 커밋 에러가 captureCommitPhaseError 로
  잡히는 것은 확인했으니 같은 구조일 수 있다)
```

```text
 L4730 의 throw 는 세 겹 뒤의 방어선이다

 정상 경로로는 닿기 어렵다
   (가) CommitContext 는 커밋의 각 서브페이즈 안에서만 켜지고
        finally 로 되돌려진다
   (나) L4673 가드가 먼저 걸린다 -
        커밋 중에는 상태가 PENDING_PASSIVE_PHASE 가 아니다
        (그 값은 flushSpawnedWork L4190, 즉 layout 이 끝난 뒤에 세워진다)
   (다) flushSync 는 실행 컨텍스트를 스스로 검사해
        렌더/커밋 중이면 아무것도 비우지 않는다

 => 셋이 다 뚫렸을 때만 터지는 불변식이다
 (이 분석은 검증 과정에서 나온 것이고,
  나는 조건식과 위치만 직접 확인했다)
```

```text
 DEV 가 중첩 패시브 갱신을 센다

 L4825  이번 flush 중에 갱신이 스케줄됐고
 L4826    그 root 가 직전에 기록된 것과 같으면
 L4827      nestedPassiveUpdateCount++
 L4828  아니면
 L4829    0 으로 리셋하고
 L4830    rootWithPassiveNestedUpdates = root
 L4832  갱신이 없었으면
 L4833    0 으로 리셋

 한도는 50 이고, 넘으면 던지지 않고 DEV 에서 console.error 를 찍는다
   "Maximum update depth exceeded. This can happen when a component
    calls setState inside useEffect, but useEffect either doesn't
    have a dependency array, or one of the dependencies changes on
    every render."

 => 커밋 쪽의 같은 이름 카운터는 **던지는데** 이쪽은 경고만 한다
 (한도와 문구는 검증 과정에서 확인된 것이다)
```

## 결과가 쓰이는 곳

```text
 return true
      --> [01]이 그대로 돌려준다

 pendingEffects* 전역
      --> 전부 지워진다. 커밋 한 바퀴가 여기서 끝난다

 flushSyncWorkOnAllRoots (L4799)
      --> 패시브 중 쌓인 sync 작업이 그 자리에서 돈다
      --> 그래서 호출자가 루프를 돈다

 executionContext
      --> CommitContext 를 켜서 이펙트 중 재진입을 막는다
      --> 다만 복원이 finally 가 아니다
```

## 다루지 않는 것

`commitPassiveUnmountEffects` / `commitPassiveMountEffects` 의 본문([03 순회](../03_traversal/README.md)에 요약이 있다), `commitDoubleInvokeEffectsInDEV`(WL L5371)의 StrictMode 이중 실행, `flushSyncWorkOnAllRoots` 의 루트 스케줄러 쪽 구현, `throwIfInfiniteUpdateLoopDetected` 와 두 카운터의 차이, `enableYieldingBeforePassive` 가 켜진 빌드의 동작, 프로파일러 로거(L4745-4765, L4788-4820)와 transition tracing 은 같은 뼈대의 곁가지라 요약만 했다.
