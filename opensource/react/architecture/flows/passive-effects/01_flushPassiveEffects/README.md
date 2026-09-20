# flushPassiveEffects

상위: [패시브 이펙트 흐름](../README.md)

가드하고, 우선순위를 낮춰 잡고, `Impl` 에 넘긴다. **캐시 풀 해제가 `finally` 에 있다.**

## 위치

`packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L4672-L4707 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L4672-L4707))

## 실제 코드

가드가 값을 돌려준다.

```js
// ReactFiberWorkLoop.js L4673-L4675
  if (pendingEffectsStatus !== PENDING_PASSIVE_PHASE) {
    return false;
  }
```

두 함수로 나뉜 이유를 TODO 가 밝힌다.

```js
// ReactFiberWorkLoop.js L4676-L4679
  // TODO: Merge flushPassiveEffectsImpl into this function. I believe they were only separate
  // in the first place because we used to wrap it with
  // `Scheduler.runWithPriority`, which accepts a function. But now we track the
  // priority within React itself, so we can mutate the variable directly.
```

> TODO: Merge `flushPassiveEffectsImpl` into this function. I believe they were **only** separate in the first place because we used to wrap it with `Scheduler.runWithPriority`, which accepts a function. But now we track the priority within React itself, so we can mutate the variable directly.

그리고 `finally` 에서 캐시 풀을 놓는다.

```js
// ReactFiberWorkLoop.js L4702-L4705
    // Once passive effects have run for the tree - giving components a
    // chance to retain cache instances they use - release the pooled
    // cache at the root (if there is one)
    releaseRootPooledCache(root, remainingLanes);
```

> Once passive effects have run for the tree - giving components a chance to retain cache instances they use - release the pooled cache at the root (**if there is one**)

## 동작 흐름

```text
 WL L4672  function flushPassiveEffects(): boolean

 L4673  pendingEffectsStatus !== PENDING_PASSIVE_PHASE 이면
 L4674    => return false

 L4682  root = pendingEffectsRoot
          주석 L4680-4681 - Impl 이 pendingEffectsRoot 를 지우므로
          미리 캐시해 둔다

 L4686  remainingLanes = pendingEffectsRemainingLanes
 L4687  pendingEffectsRemainingLanes = NoLanes
          주석 L4683-4685 - 리셋해야 한다. 이 메서드는 여러 곳에서 불릴 수 있고
          **언제나** completeRoot 에서 오는 것은 아니다
          (completeRoot 는 남은 lane 을 아는 자리다)

 L4689  renderPriority = lanesToEventPriority(pendingEffectsLanes)
 L4690  priority = lowerEventPriority(DefaultEventPriority, renderPriority)
 L4691  prevTransition = ReactSharedInternals.T
 L4692  previousPriority = getCurrentUpdatePriority()

 L4694  try {
 L4695    setCurrentUpdatePriority(priority)
 L4696    ReactSharedInternals.T = null
 L4697    => return [02] flushPassiveEffectsImpl()
 L4698  } finally {
 L4699    setCurrentUpdatePriority(previousPriority)
 L4700    ReactSharedInternals.T = prevTransition
 L4705    releaseRootPooledCache(root, remainingLanes)
 L4706  }
```

```text
 return 이 try 안에 있다

 L4697  return flushPassiveEffectsImpl();

 JS 는 반환식을 먼저 끝까지 평가하고,
 그 다음 finally 를 돌리고, 그 뒤에 값을 돌려준다

 => releaseRootPooledCache(L4705)는
    Impl 이 **끝난 뒤**, 호출자에게 값이 가기 **전**에 돈다

 Impl 이 던져도 finally 는 돈다.
 그때 root 는 L4682 에서 미리 캐시한 값이라
 Impl 이 L4717 에서 pendingEffectsRoot 를 null 로 지운 것과 무관하다
```

```text
 우선순위를 "낮춰" 잡는다

 L4689  renderPriority = lanesToEventPriority(pendingEffectsLanes)
 L4690  priority = lowerEventPriority(DefaultEventPriority, renderPriority)

 이번 커밋의 lane 에서 이벤트 우선순위를 뽑되,
 DefaultEventPriority 와 비교해 더 낮은 쪽을 쓴다

 => 패시브 이펙트 안에서 setState 를 하면
    그 갱신이 원래 렌더보다 급해지지 않는다
```

```text
 캐시 풀 해제가 남은 lane 을 본다

 releaseRootPooledCache(root, remainingLanes)

 root.pooledCacheLanes 는 그 캐시를 쓰며 렌더한 lane 들이다
 remainingLanes 와 교집합을 내서 남는 게 없으면 캐시를 놓는다

 => "아직 안 끝난 작업 중 이 캐시에 기대는 것이 있나" 를 묻는 것이다
 (이 설명은 검증 과정에서 확인된 것이고,
  나는 호출부와 주석까지만 직접 봤다)
```

```text
 다른 flush 들과 모양이 다르다

 [커밋]의 flush 넷은 이렇다
   가드 -> 즉시 상태 0 -> 일 -> 다음 단계 세움

 이 함수는
   가드가 **값을 돌려주고** (return false)
   상태를 0 으로 지우는 것은 [02] 안의 L4716 이고
   다음 단계를 세우지 않는다

 마지막 것은 "끝이라서" 가 아니다 -
 [02]가 L4799 에서 flushSyncWorkOnAllRoots 를 불러
 새 렌더가 그 자리에서 돌 수 있다
```

## 결과가 쓰이는 곳

```text
 반환 boolean
      --> flushPendingEffects 가 그대로 돌려준다
      --> "패시브를 실제로 비웠는가" 다
      --> 루트 스케줄러가 이것을 보고 우선순위를 다시 계산하기도 한다

 우선순위 / ReactSharedInternals.T
      --> 이펙트 안의 setState 가 이 값을 쓴다
      --> finally 가 되돌린다

 캐시 풀
      --> 남은 lane 이 없으면 여기서 놓인다
```

## 다루지 않는 것

`lanesToEventPriority` 와 `lowerEventPriority` 의 우선순위 대응, `releaseRootPooledCache`(WL L4621)의 본문과 `root.pooledCacheLanes` 가 세워지는 자리, `flushPendingEffects`(WL L4643)가 이 함수를 부르기 전에 하는 일, `ReactSharedInternals.T` 와 트랜지션은 같은 뼈대의 곁가지라 요약만 했다.
