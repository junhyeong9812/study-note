# beginWork

상위: [beginWork 흐름](../README.md)

절반이 **바이아웃 판정**이고 나머지 절반이 **29갈래 `switch`** 다. 그리고 `default:` 가 없다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberBeginWork.js` L4189-L4473 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberBeginWork.js#L4189-L4473))

## 실제 코드

갱신인지 최초인지부터 가른다.

`packages/react-reconciler` / `src` / `ReactFiberBeginWork.js` L4211-L4274 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberBeginWork.js#L4211-L4274))

빠른 바이아웃으로 빠지는 자리.

```js
// ReactFiberBeginWork.js L4231-L4244
      if (
        !hasScheduledUpdateOrContext &&
        // If this is the second pass of an error or suspense boundary, there
        // may not be work scheduled on `current`, so we check for this flag.
        (workInProgress.flags & DidCapture) === NoFlags
      ) {
        // No pending updates or context. Bail out now.
        didReceiveUpdate = false;
        return attemptEarlyBailoutIfNoScheduledUpdate(
          current,
          workInProgress,
          renderLanes,
        );
      }
```

switch 앞에서 lanes 를 지운다. 그 위 주석이 예외를 적어 둔다.

```js
// ReactFiberBeginWork.js L4276-L4281
  // Before entering the begin phase, clear pending update priority.
  // TODO: This assumes that we're about to evaluate the component and process
  // the update queue. However, there's an exception: SimpleMemoComponent
  // sometimes bails out later in the begin phase. This indicates that we should
  // move this assignment out of the common path and into each branch.
  workInProgress.lanes = NoLanes;
```

> TODO: This assumes that we're about to evaluate the component and process the update queue. However, there's an exception: SimpleMemoComponent **sometimes** bails out later in the begin phase. This indicates that we should move this assignment out of the common path and into each branch.

switch 의 마지막 case.

```js
// ReactFiberBeginWork.js L4462-L4466
    case Throw: {
      // This represents a Component that threw in the reconciliation phase.
      // So we'll rethrow here. This might be a Thenable.
      throw workInProgress.pendingProps;
    }
```

> This represents a Component that threw in the reconciliation phase. So we'll rethrow here. **This might be a Thenable.**

그리고 switch 를 빠져나오면 닿는 곳.

```js
// ReactFiberBeginWork.js L4469-L4472
  throw new Error(
    `Unknown unit of work tag (${workInProgress.tag}). This error is likely caused by a bug in ` +
      'React. Please file an issue.',
  );
```

## 동작 흐름

```text
 L4189  function beginWork(current, workInProgress, renderLanes)

 L4194  [__DEV__]
 L4195    _debugNeedsRemount 이고 current !== null 이면
 L4197      createFiberFromTypeAndProps 로 새 fiber 를 만들고
 L4207      => return remountFiber(...)          핫 리로드 전용

 --- 바이아웃 판정 ---

 L4211  if (current !== null)                    갱신인가

   L4215    props 가 바뀌었거나
   L4217    hasLegacyContextChanged() 이거나
   L4219    [__DEV__] type !== current.type 이면 (핫 리로드)
   L4223      didReceiveUpdate = true

   L4224    아니면
   L4227      hasScheduledUpdateOrContext = checkScheduledUpdateOrContext(current, renderLanes)
   L4231      그것이 거짓이고
   L4235      DidCapture 플래그도 없으면
   L4238        didReceiveUpdate = false
   L4239        => return [02] attemptEarlyBailoutIfNoScheduledUpdate(...)
                  **switch 에 들어가지 않는다**

   L4245    ForceUpdateForLegacySuspense 플래그가 있으면
   L4248      didReceiveUpdate = true                    [DEAD]
   L4249    아니면
   L4254      didReceiveUpdate = false

 L4257  else                                      최초 마운트
 L4258    didReceiveUpdate = false
 L4260    수화 중이고 forked child 면
 L4272      pushTreeId(workInProgress, numberOfForks, slotIndex)

 L4281  workInProgress.lanes = NoLanes

 L4283  switch (workInProgress.tag) {             case 29개
          대부분 => return update<타입>Component(...)
 L4465    case Throw => **throw** workInProgress.pendingProps
 L4467  }

 L4469  => **throw** new Error('Unknown unit of work tag (...)')
```

```text
 빠른 바이아웃의 조건은 여섯이다

 1  current !== null                        L4211  최초 마운트는 이 길이 없다
 2  oldProps === newProps                    L4216
 3  !hasLegacyContextChanged()               L4217
 4  [__DEV__] type === current.type          L4219  핫 리로드로 안 바뀌었나
 5  !checkScheduledUpdateOrContext(...)      L4227
 6  (flags & DidCapture) === NoFlags         L4235

 여섯을 다 통과해야 L4239 로 빠진다
 4 는 운영 빌드에서 언제나 참이라 실질 조건은 다섯이다
```

```text
 checkScheduledUpdateOrContext 는 두 가지만 본다   L3902-3919

 L3908  includesSomeLane(current.lanes, renderLanes)      -> 참이면 즉시 true
 L3914  current.dependencies !== null
        && checkIfContextChanged(current.dependencies)    -> 참이면 true
 그 밖에는 false

 ★ workInProgress 가 아니라 **current** 의 lanes 를 본다

 컨텍스트를 따로 보는 이유를 주석이 적는다 (L3912-3913)
   컨텍스트는 lazy 전파라 lanes 에 안 잡힌다

 호출처는 둘뿐이다 - 여기 L4227 과 updateSimpleMemoComponent L577
```

```text
 L4281 의 lanes 지우기와 그 보상이 짝을 이룬다

 L4281  workInProgress.lanes = NoLanes
        "이 렌더에서 처리했다" 는 뜻인데, switch 앞에 있어
        아직 평가하지도 않은 시점에 미리 지운다

 주석 L4277-4280 이 예외를 적는다
   SimpleMemoComponent 가 **sometimes** begin phase 뒤쪽에서 바이아웃한다
   그러면 지운 lanes 를 되살려야 한다

 실제로 그 보상 코드가 반대쪽에 있다
   L591  workInProgress.lanes = current.lanes;
   그 위 L589-590
     "TODO: Move the reset at in beginWork out of the common path
      so that this is no longer necessary."

 => TODO 가 둘이고 서로를 가리킨다
      L4277-4280  "각 갈래로 옮겨야 한다"
      L589-590    "beginWork 의 리셋을 빼면 이게 필요 없어진다"

    버그가 아니라 짝지어진 보상이다
```

```text
 switch 의 29 case 가 다 같은 모양은 아니다

 (가) => return update<타입>Component(...)          20개

 (나) 언제나 break 한다 - 플래그가 꺼져 있어서        5개
      L4379  IncompleteClassComponent     [disableLegacyMode=true]
      L4397  IncompleteFunctionComponent  [disableLegacyMode=true]
      L4420  ScopeComponent               [enableScopeAPI=false]
      L4441  LegacyHiddenComponent        [enableLegacyHidden=false]
      L4454  TracingMarkerComponent       [enableTransitionTracing=false]

 (다) 조건부 fallthrough                             2개
      L4320  HostHoistable   supportsResources 면 return, 아니면 // Fall through (L4325)
      L4326  HostSingleton   supportsSingletons 면 return, 아니면 // Fall through (L4331)
      react-dom 은 둘 다 true 라 fallthrough 쪽이 안 돈다

 (라) throw                                          1개
      L4465  case Throw

 (마) 플래그가 켜져 있어 break 가 안 도는 것          1개
      L4460  ViewTransitionComponent      [enableViewTransition=true]

 => (나) 의 break 다섯은 L4469 의 throw 로 향하도록 쓰여 있지만
    그 tag 의 fiber 가 애초에 만들어지지 않아 실제로는 도달하지 않는다
    [spi](../spi/README.md)에 정리했다
```

```text
 case Throw 는 update 함수를 부르지 않는다

 L4465  throw workInProgress.pendingProps;

 주석 L4463-4464
   "This represents a Component that threw in the reconciliation phase.
    So we'll rethrow here. This might be a Thenable."

 마지막 문장이 중요하다 - 되던지는 것이 에러만이 아니다
 서스펜드한 thenable 일 수도 있다

 이 throw 는 [렌더 루프]의 work loop 를 감싼 catch 가 받아
 handleThrow 로 간다. 거기서 thenable 인지 에러인지 다시 갈린다

 즉 조정 중에 던져진 것을 fiber 에 담아 두었다가
 begin 단계에서 **제자리에 다시 던지는** 구조다
```

```text
 default 가 없다

 L4467 에서 switch 가 닫히고 L4469 가 곧장 throw 다
 그래서 break 로 나온 case 는 전부 이 throw 에 닿는다

 메시지는 'Unknown unit of work tag (${tag}).' 인데
 (나) 의 다섯은 tag 를 아는데 기능이 꺼진 것이라
 이 메시지가 사실과 다르다 - 다만 도달하지 않는다
```

## 결과가 쓰이는 곳

```text
 반환값
      --> performUnitOfWork L3098 이 읽는다
      --> null 이면 completeUnitOfWork, 아니면 그 fiber 로 내려간다

 didReceiveUpdate
      --> update*Component 들이 읽는다
      --> 밖에서 올리는 것은 훅 시스템뿐이다 (L3763 의 호출처)

 workInProgress.lanes = NoLanes
      --> SimpleMemoComponent 는 L591 에서 되살린다

 [02] 로 넘어간 경우
      --> 컴포넌트를 평가하지 않고 스택만 맞춘다
```

## 다루지 않는 것

`update*Component` 29종의 본문, `remountFiber`(L3830)와 핫 리로드, `pushTreeId` 와 수화 중 id 생성, `hasLegacyContextChanged`, `checkIfContextChanged` 의 구현, `resolveClassComponentProps`, `ForceUpdateForLegacySuspense` 가 세워지는 자리(`ReactFiberThrow.js` L279 — 이 빌드에서는 도달 불가)는 같은 뼈대의 곁가지라 요약만 했다. `tag` 별 대조표는 [spi](../spi/README.md)에 있다.
