# 하나를 상태로

상위: [업데이트 큐](../README.md)

업데이트 하나와 이전 상태를 받아 새 상태를 돌려준다. `switch` 가 넷인데 **그중 하나가 `break` 없이 다음으로 흘러 들어간다.** 그 자리가 에러 경계의 플래그 전이다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberClassUpdateQueue.js` L386-L461 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassUpdateQueue.js#L386-L461))

## 실제 코드

`CaptureUpdate` 가 `UpdateState` 로 흘러 들어가는 자리.

```js
// ReactFiberClassUpdateQueue.js L419-L423
    case CaptureUpdate: {
      workInProgress.flags =
        (workInProgress.flags & ~ShouldCapture) | DidCapture;
    }
    // Intentional fallthrough
```

> Intentional fallthrough

흘러 들어간 곳이 여기다. updater 함수를 DEV 가 두 번 부르고, 끝에서 얕게 병합한다.

```js
// ReactFiberClassUpdateQueue.js L424-L454
    case UpdateState: {
      const payload = update.payload;
      let partialState;
      if (typeof payload === 'function') {
        // Updater function
        if (__DEV__) {
          enterDisallowedContextReadInDEV();
        }
        partialState = payload.call(instance, prevState, nextProps);
        if (__DEV__) {
          if (workInProgress.mode & StrictLegacyMode) {
            setIsStrictModeForDevtools(true);
            try {
              payload.call(instance, prevState, nextProps);
            } finally {
              setIsStrictModeForDevtools(false);
            }
          }
          exitDisallowedContextReadInDEV();
        }
      } else {
        // Partial state object
        partialState = payload;
      }
      if (partialState === null || partialState === undefined) {
        // Null and undefined are treated as no-ops.
        return prevState;
      }
      // Merge the partial state and the previous state.
      return assign({}, prevState, partialState);
    }
```

> Null and undefined are treated as no-ops.

그리고 상태를 안 바꾸는 갈래 하나.

```js
// ReactFiberClassUpdateQueue.js L455-L458
    case ForceUpdate: {
      hasForceUpdate = true;
      return prevState;
    }
```

## 동작 흐름

```text
 getStateFromUpdate  L386-461

 L386  (workInProgress, queue, update, prevState, nextProps, instance)
        ★ queue 인자(L388)는 본문에서 한 번도 안 쓰인다.
          호출부는 L626 에서 넘긴다

 L394  switch (update.tag)

 === case ReplaceState  L395 ===
 L396    payload = update.payload
 L397    typeof payload === 'function' 이면
 L400      [__DEV__] enterDisallowedContextReadInDEV()
 L402      nextState = payload.call(instance, prevState, nextProps)
 L404      [__DEV__] workInProgress.mode & StrictLegacyMode 이면
 L405        setIsStrictModeForDevtools(true)
 L407        payload.call(instance, prevState, nextProps)   ** 반환값을 버린다 **
 L409        setIsStrictModeForDevtools(false)   (finally)
 L412      [__DEV__] exitDisallowedContextReadInDEV()
 L414      => return nextState
 L417    => return payload                ** 객체면 통째로 갈아끼운다 **

 === case CaptureUpdate  L419 ===
 L420    workInProgress.flags =
 L421      (workInProgress.flags & ~ShouldCapture) | DidCapture
 L423    // Intentional fallthrough        ** break 가 없다 **

 === case UpdateState  L424 ===
 L425    payload = update.payload
 L427    함수이면
 L430      [__DEV__] enterDisallowedContextReadInDEV()
 L432      partialState = payload.call(instance, prevState, nextProps)
 L434      [__DEV__] StrictLegacyMode 이면
 L437        payload.call(...)                      ** 또 버린다 **
 L442      [__DEV__] exitDisallowedContextReadInDEV()
 L444    아니면
 L446      partialState = payload
 L448    partialState 가 null 이거나 undefined 이면
 L450      => return prevState
 L453    => return assign({}, prevState, partialState)   ** 얕은 병합 **

 === case ForceUpdate  L455 ===
 L456    hasForceUpdate = true
 L457    => return prevState              ** 상태를 안 바꾼다 **

 L460  => return prevState                (switch 를 벗어난 기본값)
```

```text
 ★ CaptureUpdate 는 UpdateState 에 플래그 전이를 얹은 것이다

 L419-422 가 하는 일이 플래그 한 줄이고, break 가 없어 L424 로 흘러간다

 => 에러 업데이트도 **payload 를 상태로 병합한다**
    그 payload 가 getDerivedStateFromError 의 결과다
    ([05]에 그 자리가 있다)

 흐름 [에러와 Suspense]가 세운 ShouldCapture 가 여기서 꺼지고
 DidCapture 가 켜진다. 그 다음 [beginWork]가 DidCapture 를 보고
 fallback 을 그린다
```

```text
 ★ 이 전이를 하는 자리가 저장소에 일곱이다

 UQ  L421                                     <- 여기
 UnwindWork  L84, L114, L144, L172, L190, L223

 여섯은 **되감는 중**에 하고 이것만 **다시 렌더하는 중**에 한다.
 => 되감기 밖에서 이 전이를 하는 유일한 자리다
```

```text
 ★ ForceUpdate 는 상태를 안 바꾼다

 L456  hasForceUpdate = true
 L457  return prevState

 하는 일이 모듈 전역 하나다. 그 전역을 CC 가 읽어
 shouldComponentUpdate 를 **건너뛸지** 정한다
   CC L922, L946     resumeMountClassInstance
   CC L1071, L1112   updateClassInstance

 => forceUpdate() 의 "강제" 가 이 불리언 하나로 구현되어 있다
```

```text
 ★ ReplaceState 와 UpdateState 가 갈리는 한 줄

 ReplaceState  L417  return payload
 UpdateState   L453  return assign({}, prevState, partialState)

 앞엣것은 통째로 갈아끼우고 뒤엣것은 얕게 병합한다.
 setState 가 UpdateState 이고 replaceState 가 ReplaceState 다
 (createUpdate L214 의 기본값이 UpdateState 다)

 그리고 UpdateState 만 null/undefined 를 no-op 으로 본다 (L448-451).
 ReplaceState 는 payload 가 null 이면 상태를 null 로 만든다
 (이 대비는 내가 두 갈래를 나란히 놓고 본 것이고 주석에 없다)
```

```text
 ★ DEV 가 updater 를 두 번 부른다

 L402 / L407     ReplaceState
 L432 / L437     UpdateState

 조건은 `workInProgress.mode & StrictLegacyMode` 이고
 setIsStrictModeForDevtools(true/false) 로 감싼 try/finally 다

 둘째 호출의 반환값은 어디에도 안 담긴다.
 => 값을 얻으려는 것이 아니라 **불순한 updater 를 드러내려는 것**이다.
    setIsStrictModeForDevtools 는 그 둘째 호출 동안
    로그 중복과 스케줄러 양보를 억누르는 장치다
    (ReactFiberDevToolsHook L187-206)
```

```text
 ★ enter/exitDisallowedContextReadInDEV 가 감싸는 것

 L400  enter          <- __DEV__ 블록
 L402  payload.call   <- 블록 밖. 프로덕션에서도 불려야 한다
 L412  exit           <- __DEV__ 블록

 payload 가 함수일 때만 둘 다 불린다. 아니면 둘 다 안 불린다

 ★ 이 파일이 그 플래그를 **세우는 유일한 곳**이다 (L400, L430)
   읽는 곳은 NewContext L557 하나 - readContext 안이다
   거기서 console.error 로 같은 문구를 찍는다
     'Context can only be read while React is rendering. ...'
   주석 NewContext L555-556 -
     "This warning would fire if you read context inside a Hook like useMemo.
      Unlike the class check below, it's not enforced in production for perf."

 => 이 DEV 가드가 있는 이유가 **클래스 updater 안에서 컨텍스트를 읽는 것**
    하나다. [컨텍스트 전파] 흐름과 여기서 닫힌다

 ★ try/finally 가 없다. L402 가 던지면 exit 가 안 불린다.
   되돌리는 것은 resetContextDependencies (NewContext L60-68)이고
   렌더가 양보하기 직전에 불린다
   (이 귀결은 내가 두 파일을 맞춰 보고 적은 것이다)
```

## 결과가 쓰이는 곳

```text
 반환값
      --> [03] L624 가 newState 에 담아 다음 업데이트의 prevState 로 쓴다
      --> 루프가 끝나면 workInProgress.memoizedState 가 된다

 workInProgress.flags (CaptureUpdate 갈래)
      --> ShouldCapture 가 꺼지고 DidCapture 가 켜진다
      --> [beginWork]가 DidCapture 를 보고 fallback 을 그린다

 hasForceUpdate
      --> CC 가 shouldComponentUpdate 를 건너뛸지 정한다
```

## 다루지 않는 것

`assign`(`shared/assign`)이 `Object.assign` 의 얇은 포장이라는 것 외의 세부, `StrictLegacyMode`(`ReactTypeOfMode`)가 어떤 트리에 붙는지, `setIsStrictModeForDevtools`(`ReactFiberDevToolsHook` L187)의 본문과 `unstable_setDisableYieldValue`, `instance` 가 `null` 로 넘어오는 HostRoot / CacheComponent 호출(BW L1239, L1819)에서 `payload.call(null, ...)` 이 되는 경우, `getDerivedStateFromError` 가 `update.payload` 로 들어오는 경로([05 에러 업데이트와 콜백](../05_capturedAndCallbacks/README.md)에 있다), `ShouldCapture` / `DidCapture` 의 나머지 수명([에러와 Suspense](../../throw/README.md)에 있다)은 같은 뼈대의 곁가지라 요약만 했다.
