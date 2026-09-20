# attemptEarlyBailoutIfNoScheduledUpdate

상위: [beginWork 흐름](../README.md)

**같은 `tag` 를 두 번째로 `switch` 하는 자리**다. 컴포넌트를 평가하지 않고 **스택만 맞춰 둔다.** 다만 이름과 달리, 여기서 바이아웃을 포기하고 본 경로로 되돌아가는 `case` 가 있다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberBeginWork.js` L3921-L4187 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberBeginWork.js#L3921-L4187))

## 실제 코드

의도를 주석이 먼저 말한다.

`packages/react-reconciler` / `src` / `ReactFiberBeginWork.js` L3926-L3929 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberBeginWork.js#L3926-L3929))

```js
// ReactFiberBeginWork.js L3926-L3928
  // This fiber does not have any pending work. Bailout without entering
  // the begin phase. There's still some bookkeeping we that needs to be done
  // in this optimized path, mostly pushing stuff onto the stack.
```

> This fiber does not have any pending work. Bailout without entering the begin phase. There's still some bookkeeping we that needs to be done in this optimized path, **mostly** pushing stuff onto the stack.

평범한 `case` 는 push 하고 `break` 한다.

```js
// ReactFiberBeginWork.js L3944-L3954
    case HostSingleton:
    case HostComponent:
      pushHostContext(workInProgress);
      break;
    case ClassComponent: {
      const Component = workInProgress.type;
      if (isLegacyContextProvider(Component)) {
        pushLegacyContextProvider(workInProgress);
      }
      break;
    }
```

그런데 바이아웃을 포기하는 `case` 가 있다.

```js
// ReactFiberBeginWork.js L4039-L4041
          // The primary children have pending work. Use the normal path
          // to attempt to render the primary children again.
          return updateSuspenseComponent(current, workInProgress, renderLanes);
```

> The primary children have pending work. **Use the normal path** to attempt to render the primary children again.

마지막 줄.

```js
// ReactFiberBeginWork.js L4186-L4186
  return bailoutOnAlreadyFinishedWork(current, workInProgress, renderLanes);
```

## 동작 흐름

```text
 L3921  function attemptEarlyBailoutIfNoScheduledUpdate(current, workInProgress, renderLanes)

 L3929  switch (workInProgress.tag) {      case 레이블 14개 (본문 13개)

 --- (가) push 하고 break -> L4186 ---

 L3930    HostRoot
 L3931      pushHostRootContext(workInProgress)
 L3933      pushRootTransition(workInProgress, root, renderLanes)
 L3936      [enableTransitionTracing] pushRootMarkerInstance    안 돈다
 L3940      pushCacheProvider(workInProgress, cache)
 L3941      resetHydrationState()
 L3944    HostSingleton
 L3945    HostComponent                   <- 위와 본문을 공유한다
 L3946      pushHostContext(workInProgress)
 L3948    ClassComponent
 L3950      isLegacyContextProvider 면 pushLegacyContextProvider   조건부다
 L3955    HostPortal
 L3956      pushHostContainer(workInProgress, containerInfo)
 L3958    ContextProvider
 L3961      pushProvider(workInProgress, context, value)
 L3964    Profiler
 L3972      [enableProfilerTimer] 자식에 일 있으면 flags |= Update
 L3979      [enableProfilerCommitHooks] flags |= Passive
 L3983      effectDuration = -0 / passiveEffectDuration = -0    <- push 가 아니다
 L4159    CacheComponent
 L4161      pushCacheProvider(workInProgress, cache)

 --- (나) 자체 판단으로 따로 끝낸다 ---

 L3988    ActivityComponent
 L3996      탈수 상태면 flags |= DidCapture
 L3997      pushDehydratedActivitySuspenseHandler
 L3998      => return null

 L4002    SuspenseComponent                  아래 따로 적는다
 L4069    SuspenseListComponent              아래 따로 적는다

 L4142    OffscreenComponent
 L4151      workInProgress.lanes = NoLanes    <- L4281 을 손으로 재현한다
 L4152      => return updateOffscreenComponent(...)

 --- (다) 플래그가 꺼져 언제나 fallthrough ---

 L4164    TracingMarkerComponent  [enableTransitionTracing=false]
 L4172      // Fallthrough  ->  아래 LegacyHiddenComponent 본문으로 떨어진다
 L4174    LegacyHiddenComponent   [enableLegacyHidden=false]
 L4183      // Fallthrough  ->  switch 를 빠져나간다

 L4185  }
 L4186  => return [03] bailoutOnAlreadyFinishedWork(current, workInProgress, renderLanes)
```

```text
 case 레이블은 14인데 본문은 13이다

 L3944  case HostSingleton:
 L3945  case HostComponent:
 L3946    pushHostContext(workInProgress);
 L3947    break;

 둘이 한 본문을 공유한다. 무조건 fallthrough 라 갈래가 아니다
 (L4164 / L4174 의 // Fallthrough 는 조건부라 따로 센다)
```

```text
 ★ 출구가 L4186 하나가 아니다

 여섯 case 에서 아홉 개의 return 이 L4186 을 건너뛴다

   L3998  return null                       Activity 탈수
   L4015  return null                       Suspense 탈수
   L4041  return updateSuspenseComponent    **본 경로 복귀**
   L4056  return child.sibling              **형제로 점프**
   L4061  return null
   L4072  return updateSuspenseListComponent
   L4108  return updateSuspenseListComponent
   L4139  return null                       SuspenseList fast bail out
   L4152  return updateOffscreenComponent   **본 경로 복귀**

 그래서 주석의 "mostly" 가 한정어로 붙어 있다
 "스택 푸시만 한다" 고 읽으면 위 아홉 자리가 설명되지 않는다
```

```text
 SuspenseComponent 한 case 안에 출구가 넷이다   L4002-4067

 L4004  state !== null 인가 (타임아웃 상태인가)

   L4005  state.dehydrated !== null 이면 (탈수 경계)
   L4008    pushPrimaryTreeSuspenseHandler    push/pop 대칭만 맞춘다
   L4012    flags |= DidCapture
   L4015    => return null
            주석 L4013-4014 가 직접 말한다
              "We should never render the children of a dehydrated boundary
               until we upgrade it. We return null instead of
               bailoutOnAlreadyFinishedWork."

   L4028  아니면 lazilyPropagateParentContextChanges 를 먼저 부르고
          그 **반환값** 을 contextChanged 로 받는다
   L4035  contextChanged 이거나 주 자식에 이번 렌더 일이 있으면
   L4041    => return updateSuspenseComponent(...)      본 경로로 되돌아간다

   L4042  아니면
   L4045    pushPrimaryTreeSuspenseHandler
   L4048    child = bailoutOnAlreadyFinishedWork(...)    자기가 직접 부른다
   L4053    child 가 null 이 아니면
   L4056      => return child.sibling                    자식이 아니라 형제다
              주석 L4054-4055 "Skip over the primary children and
                               work on the fallback."
   L4057    아니면
   L4061      => return null

 L4064  state === null 이면 (평범한 경우)
 L4065    pushPrimaryTreeSuspenseHandler
 L4067    break                                          -> L4186
```

```text
 SuspenseListComponent 는 상태를 변형한다   L4069-4140

 L4070  flags & DidCapture 면 (2차 패스)
 L4072    => return updateSuspenseListComponent(...)

 L4078  didSuspendBefore = current.flags & DidCapture
 L4080  hasChildWork 계산
 L4093  없으면 lazilyPropagateParentContextChanges 후
 L4098    다시 계산

 L4108  didSuspendBefore 이고 hasChildWork 면
          => return updateSuspenseListComponent(...)
 L4117  didSuspendBefore 이고 hasChildWork 가 아니면
          flags |= DidCapture

 L4127  renderState.rendering = null          <- memoizedState 를 고친다
 L4128  renderState.tail = null
 L4129  renderState.lastEffect = null
 L4131  pushSuspenseListContext(...)

 L4137  hasChildWork 면 break
 L4139  아니면 => return null

 즉 push 도 하고 상태도 고치고 조기 return 도 한다
```

```text
 OffscreenComponent 는 주석이 스스로 인정한다   L4142-4158

 L4151  workInProgress.lanes = NoLanes
 L4152  return updateOffscreenComponent(current, workInProgress, renderLanes, pendingProps)

 주석 L4143-4150
   "almost identical to the logic used in the normal update path ...
    I'm tempted to do a labeled break here but I won't :)"

 L4151 이 [01] L4281 을 손으로 재현한 것이다
 빠른 바이아웃은 L4281 을 건너뛰고 왔기 때문이다
```

```text
 Profiler 는 push 를 하지 않는다   L3964-3987

 flags 를 세우고 stateNode 의 필드를 고친다
   L3983  stateNode.effectDuration = -0
   L3984  stateNode.passiveEffectDuration = -0

 그리고 enableProfilerTimer 가 __PROFILE__ 이라
 비프로파일 빌드에서는 본문 전체가 no-op 이다
```

```text
 [02] 에 없는 tag 는 빠진 것이 아니다

 HostHoistable 과 ViewTransitionComponent 는 [01] 에는 있고 여기 없다

 이유는 그 둘이 본 경로에서도 스택을 push 하지 않기 때문이다
   updateHostHoistable   L2008-2053, 언제나 return null (L2052)
   updateViewTransition  L3593-3653

 push 가 없으면 흉내 낼 것도 없다
 => 14개 레이블은 "push 가 있는 tag" 와 정확히 일치한다
```

## 결과가 쓰이는 곳

```text
 스택 (호스트 컨텍스트·컨텍스트 값·캐시·Suspense 핸들러)
      --> completeWork 가 올라오며 pop 한다
      --> 여기서 push 를 빠뜨리면 pop 이 짝을 잃는다

 => return [03]
      --> 평범한 case 가 가는 길이다

 자체 return null
      --> [01] 을 거쳐 performUnitOfWork 로 가고 서브트리를 건너뛴다

 자체 return update*Component
      --> 바이아웃을 포기하고 본 경로로 되돌아간다

 return child.sibling
      --> 주 자식을 건너뛰고 fallback 으로 간다
```

## 다루지 않는 것

`pushHostRootContext` / `pushHostContext` / `pushProvider` / `pushCacheProvider` / `pushSuspenseListContext` / `pushPrimaryTreeSuspenseHandler` 등 push 함수들의 구현과 대응하는 pop, `lazilyPropagateParentContextChanges`(`ReactFiberNewContext.js` L379)의 컨텍스트 전파, `updateSuspenseComponent` / `updateSuspenseListComponent` / `updateOffscreenComponent` 의 본문, 탈수(dehydrated) 경계의 수화 과정, `renderState` 의 tail 관리는 같은 뼈대의 곁가지라 요약만 했다.
