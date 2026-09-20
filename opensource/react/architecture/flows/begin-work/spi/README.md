# spi

상위: [beginWork 흐름](../README.md)

이 흐름의 계약은 **`tag`** 하나다. 그런데 그 `tag` 를 두 곳에서 `switch` 하고, 둘의 `case` 수가 다르며, 꺼진 플래그를 처리하는 방식이 세 곳에서 다르다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberBeginWork.js` 기준이다.

## tag 목록

`packages/react-reconciler` / `src` / `ReactWorkTags.js` L10-L40 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactWorkTags.js#L10-L40))

## 두 switch 대조표

`beginWork` 의 `switch`(L4283)는 `case` 레이블이 **29개**, `attemptEarlyBailoutIfNoScheduledUpdate` 의 `switch`(L3929)는 **14개**다. 14개는 전부 29개의 부분집합이다 — 바이아웃 쪽에만 있는 `tag` 는 없다.

| tag | [01] case | [01] 이 하는 일 | [02] case | [02] 가 하는 일 | 이 빌드에서 |
|---|---|---|---|---|---|
| LazyComponent | L4284 | `mountLazyComponent` | — | — | 산다 |
| FunctionComponent | L4293 | `updateFunctionComponent` | — | — | 산다 |
| ClassComponent | L4303 | `updateClassComponent` | L3948 | 레거시 컨텍스트 제공자면 `pushLegacyContextProvider` (조건부) | 산다 |
| HostRoot | L4318 | `updateHostRoot` | L3930 | `pushHostRootContext` + `pushRootTransition` + `pushCacheProvider` + `resetHydrationState` | 산다 |
| HostHoistable | L4320 | `supportsResources` 면 `updateHostHoistable`, 아니면 `// Fall through` (L4325) | — | — | react-dom 은 `true`. push 가 없어 [02] 에도 없다 |
| HostSingleton | L4326 | `supportsSingletons` 면 `updateHostSingleton`, 아니면 `// Fall through` (L4331) | L3944 | `pushHostContext` (아래와 본문 공유) | react-dom 은 `true` |
| HostComponent | L4332 | `updateHostComponent` | L3945 | 〃 | 산다 |
| HostText | L4334 | `updateHostText` — 언제나 `return null` | — | — | 산다 |
| SuspenseComponent | L4336 | `updateSuspenseComponent` | L4002 | **단순 push 아님** — 출구 넷 | 산다 |
| HostPortal | L4338 | `updatePortalComponent` | L3955 | `pushHostContainer` | 산다 |
| ForwardRef | L4340 | `updateForwardRef` | — | — | 산다 |
| Fragment | L4349 | `updateFragment` | — | — | 산다 |
| Mode | L4351 | `updateMode` | — | — | 산다 |
| Profiler | L4353 | `updateProfiler` | L3964 | push 아님 — flags 세팅 + `stateNode` 필드 변형 | 비프로파일 빌드에선 [02] 본문이 no-op |
| ContextProvider | L4355 | `updateContextProvider` | L3958 | `pushProvider` | 산다 |
| ContextConsumer | L4357 | `updateContextConsumer` | — | — | 산다 |
| MemoComponent | L4359 | `updateMemoComponent` | — | — | 산다 |
| SimpleMemoComponent | L4368 | `updateSimpleMemoComponent` | — | — | 산다 |
| IncompleteClassComponent | L4377 | `disableLegacyMode` 면 **`break`** (L4379) | — | — | **죽었다** |
| IncompleteFunctionComponent | L4395 | `disableLegacyMode` 면 **`break`** (L4397) | — | — | **죽었다** |
| SuspenseListComponent | L4413 | `updateSuspenseListComponent` | L4069 | **단순 push 아님** — `memoizedState` 변형 + 출구 넷 | 산다 |
| ScopeComponent | L4416 | `enableScopeAPI` 면 `updateScopeComponent`, 아니면 **`break`** (L4420) | — | — | **죽었다** |
| ActivityComponent | L4422 | `updateActivityComponent` | L3988 | 탈수 상태면 `return null` (L3998) | 산다 |
| OffscreenComponent | L4425 | `updateOffscreenComponent` | L4142 | push 없음 — `return updateOffscreenComponent` (L4152) | 산다 |
| LegacyHiddenComponent | L4433 | `enableLegacyHidden` 면 `updateLegacyHiddenComponent`, 아니면 **`break`** (L4441) | L4174 | 꺼지면 `// Fallthrough` (L4183) | **죽었다** |
| CacheComponent | L4443 | `updateCacheComponent` | L4159 | `pushCacheProvider` | 산다 |
| TracingMarkerComponent | L4446 | `enableTransitionTracing` 면 `updateTracingMarkerComponent`, 아니면 **`break`** (L4454) | L4164 | 꺼지면 `// Fallthrough` (L4172) | **죽었다** |
| ViewTransitionComponent | L4456 | `enableViewTransition` 이라 `updateViewTransition`; `break`(L4460)은 안 돈다 | — | — | 산다. push 가 없어 [02] 에도 없다 |
| Throw | L4462 | update 함수를 부르지 않는다 — **`throw pendingProps`** (L4465) | — | — | 산다 |

```text
 레이블 14, 본문 13

 L3944  case HostSingleton:
 L3945  case HostComponent:
 L3946    pushHostContext(workInProgress);
 L3947    break;

 무조건 fallthrough 로 본문을 공유한다
 [01] 쪽에는 이런 묶음이 하나도 없어 레이블 29 = 본문 29 다
```

```text
 [02] 에 없는 tag 15개가 다 같은 이유는 아니다

 (가) 아예 push 를 안 한다
      HostHoistable  updateHostHoistable L2008-2053, 언제나 return null (L2052)
      ViewTransition updateViewTransition L3593-3653
      HostText, Fragment, Mode 등
      => 흉내 낼 push 가 없다. 일관된 설계다

 (나) 죽어 있다
      ScopeComponent / IncompleteClassComponent / IncompleteFunctionComponent

 (다) 훅이나 래퍼라 바이아웃 판정이 [01] 안에서 끝난다
      SimpleMemoComponent (L558 / L600 에서 didReceiveUpdate 를 직접 세운다)
      MemoComponent / LazyComponent / ForwardRef
```

## 꺼진 플래그를 처리하는 방식이 세 곳에서 다르다

같은 무늬 — `if (플래그) { ... }` 와 그 다음 — 가 세 곳에 있는데 결말이 셋 다 다르다.

### (가) fiber 를 만들 때 — 사슬로 떨어진다

`packages/react-reconciler` / `src` / `ReactFiber.js` L631-L650 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiber.js#L631-L650))

```js
// ReactFiber.js L631-L650
      case REACT_LEGACY_HIDDEN_TYPE:
        if (enableLegacyHidden) {
          return createFiberFromLegacyHidden(pendingProps, mode, lanes, key);
        }
      // $FlowFixMe[invalid-compare] -- falls through
      case REACT_VIEW_TRANSITION_TYPE:
        if (enableViewTransition) {
          return createFiberFromViewTransition(pendingProps, mode, lanes, key);
        }
      // $FlowFixMe[invalid-compare] -- falls through
      case REACT_SCOPE_TYPE:
        if (enableScopeAPI) {
          return createFiberFromScope(type, pendingProps, mode, lanes, key);
        }
      // $FlowFixMe[invalid-compare] -- falls through
      case REACT_TRACING_MARKER_TYPE:
        if (enableTransitionTracing) {
          return createFiberFromTracingMarker(pendingProps, mode, lanes, key);
        }
      // Fall through
```

```text
 다음 case 로 떨어지는 사슬이다

 LEGACY_HIDDEN -> VIEW_TRANSITION -> SCOPE -> TRACING_MARKER -> default

 네 플래그 중 하나만 켜져 있다
   enableLegacyHidden      false   (ReactFeatureFlags L109)
   enableViewTransition    **true**  (L81)
   enableScopeAPI          false   (L53)
   enableTransitionTracing false   (L106)

 ★ 그래서 사슬이 중간에 끊긴다
   <LegacyHidden> 은 default 까지 못 가고
   켜져 있는 ViewTransition 가지에 걸려
   **ViewTransitionComponent fiber 가 된다** (L638)

   Scope 와 TracingMarker 는 ViewTransition 뒤에 있어 default 로 간다

 (코드가 그렇게 쓰여 있다는 사실만 적는다. 의도인지는 확인하지 못했다)
```

`default` 가 하는 일.

```js
// ReactFiber.js L725-L736
        // The type is invalid but it's conceptually a child that errored and not the
        // current component itself so we create a virtual child that throws in its
        // begin phase. This is the same thing we do in ReactChildFiber if we throw
        // but we do it here so that we can assign the debug owner and stack from the
        // element itself. That way the error stack will point to the JSX callsite.
        fiberTag = Throw;
        pendingProps = new Error(
          'Element type is invalid: expected a string (for built-in ' +
            'components) or a class/function (for composite components) ' +
            `but got: ${typeString}.${info}`,
        );
        resolvedType = null;
```

> The type is invalid but it's conceptually a child that errored and not the current component itself so we create a virtual child that throws in its begin phase ... That way the error stack will point to the JSX callsite.

### (나) 바이아웃 switch — fallthrough 해서 bailout 으로

```js
// ReactFiberBeginWork.js L4164-L4184
    case TracingMarkerComponent: {
      if (enableTransitionTracing) {
        const instance: TracingMarkerInstance | null = workInProgress.stateNode;
        if (instance !== null) {
          pushMarkerInstance(workInProgress, instance);
        }
        break;
      }
      // Fallthrough
    }
    case LegacyHiddenComponent: {
      if (enableLegacyHidden) {
        workInProgress.lanes = NoLanes;
        return updateLegacyHiddenComponent(
          current,
          workInProgress,
          renderLanes,
        );
      }
      // Fallthrough
    }
```

```text
 break 가 if **안** 에 있다 (L4170)

 그래서 플래그가 켜지면 break 하고,
 꺼지면 L4172 의 // Fallthrough 로 다음 case 본문에 떨어진다

 TracingMarker -> LegacyHidden -> (거기도 꺼져 있어) switch 밖 -> L4186

 결과는 bailoutOnAlreadyFinishedWork 다. 무해하다
```

### (다) 본 경로 switch — break 해서 throw 로

```js
// ReactFiberBeginWork.js L4416-L4421
    case ScopeComponent: {
      if (enableScopeAPI) {
        return updateScopeComponent(current, workInProgress, renderLanes);
      }
      break;
    }
```

```text
 여기는 break 가 if **밖** 에 있다

 그래서 꺼지면 switch 를 빠져나가고,
 [01] 에는 default 가 없어 L4469 의 throw 에 닿는다

   throw new Error(`Unknown unit of work tag (${tag}). ...`)
```

## 그런데 그 throw 는 도달하지 않는다

```text
 (다) 의 break 다섯은 실제로 실행되지 않는다
 그 tag 의 fiber 가 애초에 만들어지지 않기 때문이다

 ScopeComponent
   만드는 곳이 createFiberFromScope 하나뿐이고
   그 호출처가 ReactFiber.js L643 하나다
   enableScopeAPI 가 false 라 그 줄이 안 돈다
   -> 사슬을 타고 default 로 가 fiberTag = Throw 가 된다

 TracingMarkerComponent
   같은 구조. 호출처 ReactFiber.js L648 하나
   -> default -> Throw

 LegacyHiddenComponent
   호출처 ReactFiber.js L633 하나
   -> 사슬이 ViewTransition 에서 끊겨 ViewTransitionComponent 가 된다

 IncompleteClassComponent / IncompleteFunctionComponent
   이 둘은 생성이 아니라 **tag 재기입** 으로 붙는다
   ReactFiberThrow.js L292 / L306
   그 블록의 조건이 !disableLegacyMode && ... (L250-253) 인데
   disableLegacyMode 가 true 라 블록 전체가 도달 불가

 => L4469 는 "플래그가 꺼졌을 때" 가 아니라
    **"tag 가 손상됐을 때" 를 위한 방어선**이다

    메시지가 'Unknown unit of work tag' 인 것도 그래서 맞다
    (확인한 범위는 createFiberFrom* 계열과 ReactFiberThrow 의 재기입이다.
     fiber.tag 를 직접 쓰는 다른 자리를 전수 조사하지는 않았다)
```

## Throw tag — 에러를 가상의 자식으로 옮긴다

```text
 만드는 곳이 둘이다

 1  ReactFiber.js L730
    유효하지 않은 element type 일 때
    pendingProps 에 Error('Element type is invalid: ...') 를 담는다

 2  ReactChildFiber.js L2075
    조정(reconciliation) 중에 무언가 던졌을 때
    createFiberFromThrow(x, returnFiber.mode, lanes)

    단 SuspenseException / SuspenseActionException 은
    그 전에 그냥 다시 던진다 (L2055-2070)

 주석 L2071-2074 가 이유를 적는다
   "conceptually a child that errored and not the current component itself
    so we create a virtual child that throws in its begin phase.
    That way the current component can handle the error or suspending if needed."

 => 목적은 **에러의 발생 지점을 부모가 아니라 가상의 자식으로 옮기는 것**이다
    그래야 에러 바운더리와 Suspense 가
    정상적인 begin/complete 사이클 안에서 잡는다

 그리고 [01] L4465 가 begin 단계에서 그것을 다시 던지면
 [렌더 루프]의 work loop catch 가 받아 handleThrow 로 간다
 담긴 값이 Error 일 수도 thenable 일 수도 있어서
 (L4464 "This might be a Thenable.")
 거기서 다시 갈린다
```

## didReceiveUpdate — 모듈 전역 하나

```text
 L319  let didReceiveUpdate: boolean = false;

 대입 자리 여덟 (전부 이 파일 안)
   L558, L600   updateSimpleMemoComponent
   L3764        markWorkInProgressReceivedUpdate
   L4223, L4238, L4248, L4254, L4258   beginWork

 읽는 자리 일곱 - L457, L1004, L1014, L1522, L1565, L3020, L3030

 ★ 밖에서 올리는 주체는 훅 시스템 하나다

   markWorkInProgressReceivedUpdate (L3763) 의 호출처
     ReactFiberHooks.js  L724, L1542, L1618, L1765, L3053, L3080
   게터 checkIfWorkInProgressReceivedUpdate (L3767) 의 호출처
     ReactFiberHooks.js  L711

 다른 프로덕션 파일에서는 이 이름이 나오지 않는다

 => "props 는 같은데 다시 그려야 한다" 를 판정하는 곳이
    beginWork 의 다섯 자리와 훅 여섯 자리, 둘뿐이다
```

## 죽은 플래그와 죽은 가지

```text
 disableLegacyMode = true        ReactFeatureFlags L192
   [01] L4379 / L4397 의 break 가 언제나 돈다
   그리고 ForceUpdateForLegacySuspense 가지(L4245-4248)도 죽는다
     그 플래그를 세우는 유일한 자리가 ReactFiberThrow.js L279 인데
     !disableLegacyMode 블록(L250-253) 안이다
   같은 이유로 L597 의 SimpleMemo 쪽 체크도 죽는다

 enableScopeAPI = false          L53
 enableLegacyHidden = false      L109
 enableTransitionTracing = false L106
   위 세 tag 의 fiber 가 만들어지지 않는다
   [02] L3936 의 pushRootMarkerInstance 도 안 돈다

 enableViewTransition = true     L81
   유일하게 켜져 있어 (가) 의 사슬을 끊는다

 enableProfilerTimer = __PROFILE__   L229
   비프로파일 빌드에서 [02] 의 Profiler case(L3964-3987) 본문이 통째로 no-op
   [03] L3799 의 stopProfilerTimerIfRunning 도 안 돈다

 DehydratedFragment (tag 18)
   두 switch 어디에도 case 가 없다
   beginWork 에 들어오지 않는다 - 부모 Suspense 가 처리한다
```

## 결과가 쓰이는 곳

```text
 tag
      --> 두 switch 가 각각 읽는다
      --> 같은 값에 대해 "평가한다" 와 "스택만 맞춘다" 로 갈린다

 죽은 case
      --> 소스에는 있지만 이 빌드에서 재현할 수 없다
      --> 문서가 살아 있는 분기처럼 적으면 오해를 만든다

 Throw tag
      --> [01] L4465 가 던지고 [렌더 루프]의 catch 가 받는다
      --> 에러와 서스펜션이 같은 통로를 쓴다

 didReceiveUpdate
      --> update*Component 들과 훅이 공유하는 단 하나의 신호다
```

## 다루지 않는 것

`update*Component` 29종의 본문, `ReactWorkTags.js` 의 숫자 배정 규칙, `createFiberFromTypeAndProps` 의 나머지 갈래와 `$$typeof` 분기, `ReactChildFiber.js` 의 조정 과정, `ReactFiberThrow.js` 의 `throwException` 과 경계 찾기, 훅 여섯 자리가 각각 언제 `markWorkInProgressReceivedUpdate` 를 부르는지, `__PROFILE__` 의 빌드별 실제 값은 이 문서의 범위 밖이다.
