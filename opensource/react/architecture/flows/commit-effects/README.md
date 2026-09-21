# 커밋 이펙트

상위: [React 아키텍처 지도](../../README.md)

`useEffect` 의 콜백과 `componentDidMount` 가 **실제로 불리는 자리**다. 이 파일의 자리가 선명하다 — [커밋]의 `ReactFiberCommitWork.js` 가 트리를 순회하고, 이 파일이 **사용자 코드를 부른다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberCommitEffects.js` 기준이다. `CMW` = `ReactFiberCommitWork.js`, `CUS` = `ReactFiberCallUserSpace.js`, `WL` = `ReactFiberWorkLoop.js`.

## 전체 그림

```text
 함수 스물셋 - export 열일곱, 내부 여섯. 네 무리로 갈린다

 [0] 공용      L89   shouldProfile

 [1] 훅 이펙트  L97-338
       래퍼 넷    commitHookLayoutEffects        L97
                  commitHookLayoutUnmountEffects L114
                  commitHookPassiveMountEffects  L305
                  commitHookPassiveUnmountEffects L318
       본체 둘    commitHookEffectListMount      L141
                  commitHookEffectListUnmount    L249

 [2] 클래스 생명주기  L340-755
       commitClassLayoutLifecycles  L340   componentDidMount / DidUpdate
       commitClassDidMount          L497
       commitClassCallbacks         L518   setState 의 콜백
       commitClassHiddenCallbacks   L568
       commitRootCallbacks          L592   root.render 의 콜백
       commitClassSnapshot          L635   getSnapshotBeforeUpdate
       safelyCallComponentWillUnmount L710

 [3] ref  L757-934
       commitAttachRef   L757 / safelyAttachRef L827
       safelyDetachRef   L842 / safelyCallDestroy L910

 [4] 프로파일러  L936-1045   [FLAG:__PROFILE__ — 프로파일링 빌드만]
       commitProfiler L936 / commitProfilerUpdate L972
       commitProfilerPostCommitImpl L998 / commitProfilerPostCommit L1018
```

1. [훅 이펙트](01_hookEffects/README.md) — 래퍼 넷에 본체 둘. 마운트와 언마운트가 예외를 다르게 다룬다.
2. [클래스 생명주기](02_classLifecycles/README.md) — 패스 둘을 잇는 것이 인스턴스의 칸 하나다.
3. [ref](03_refs/README.md) — 붙이기와 떼기, 그리고 cleanup.
4. [프로파일러](04_profiler/README.md) — 프로파일링 빌드에서만 사는 무리.

```text
 ★★ 순회와 호출이 파일로 갈려 있다

 이 파일의 export 열일곱을 부르는 곳이 딱 둘이다
   ReactFiberCommitWork.js     열일곱을 전부 아우른다
   ReactFiberApplyGesture.js   둘만 (L435, L1096 - 둘 다 insertion 이펙트다)

 반대로 이 파일은 트리를 순회하지 않는다.
 fiber 하나를 받아 그 fiber 의 사용자 코드를 부를 뿐이다

 => [커밋]이 "언제 무엇을" 을 정하고, 여기가 "어떻게 안전하게" 를 맡는다
```

```text
 ★★ 파일 전체를 관통하는 모양 - 사용자 코드를 부르는 두 갈래

 모양이 둘인데, 어느 쪽이든 끝은 captureCommitPhaseError 다

 (가) 바깥 try 하나가 **두 갈래를 다** 감싼다 — 이쪽이 다수다
        try {
          [__DEV__] runWithFiberInDEV(...) 아니면 직접 호출
        } catch { captureCommitPhaseError(...) }
      commitClassCallbacks L556 / commitClassHiddenCallbacks L575
      commitRootCallbacks L610 / commitClassSnapshot L670
      safelyAttachRef L831 / commitProfilerUpdate L979
      commitProfilerPostCommit L1024

 (나) CUS 로 위임하고 **거기서 잡는다**
        [__DEV__] runWithFiberInDEV(fiber, callXInDEV, ...)
        아니면    try { 사용자코드() } catch { captureCommitPhaseError(...) }
      클래스 생명주기 셋과 이펙트 cleanup 이 이쪽이다

 그 callXInDEV 들이 CUS 에 모여 있고 **일부만** 자기 안에 try/catch 를 갖는다
   CUS L78   callComponentDidMount      try L83
   CUS L101  callComponentDidUpdate     try L109
   CUS L153  callComponentWillUnmount   try L159
   CUS L195  callDestroy                try L201
   CUS L178  callCreate                 ★ **try 가 없다**

 마지막 하나가 [01]의 비대칭에 얽힌다
 (다만 그 비대칭의 직접 원인은 safelyCallDestroy 가 루프 **안**에서
  잡는다는 것이다 — [01]에 있다)

 ★ 그리고 commitAttachRef 는 예외다. 사용자 코드(L798 / L803 의 ref 호출)를
   try 없이 부르고, 감싸는 것은 한 단계 위 safelyAttachRef 다

 그리고 CUS 의 함수들이 전부 이 모양이다
   const callX = { react_stack_bottom_frame: function (...) { ... } }
   export const callXInDEV = __DEV__ ? callX.react_stack_bottom_frame.bind(callX) : null
 주석 - "We use this technique to trick minifiers to preserve the function name."
 (스택 트레이스에 이름을 남기려는 장치로 보인다 - 내 판단이다)
```

```text
 ★ captureCommitPhaseError 가 이 파일에서 열아홉 번 불린다

 렌더 단계의 에러는 **되감아** 경계를 찾지만([에러와 Suspense]),
 커밋 단계의 에러는 되감을 수 없다. 이미 DOM 을 바꿨기 때문이다

 그래서 세 가지가 다르다
   (가) 되감는 대신 경계에 SyncLane 업데이트를 **새로 걸고 렌더를 다시 스케줄**한다
   (나) Suspense 경계를 **보지 않는다**. getDerivedStateFromError 와
        componentDidCatch 만 본다 => 커밋 에러는 fallback 을 띄울 수 없다
   (다) 찾기 시작하는 곳이 **부모**다. 이 파일이 finishedWork.return 을 넘긴다
        => 컴포넌트가 자기 커밋 에러를 스스로 잡을 수 없다

 ★ 인자 모양도 둘이다
   마운트·갱신 쪽 열셋  (finishedWork, finishedWork.return, error)
   언마운트·떼기 쪽 여섯 (current, nearestMountedAncestor, error)
   삭제 경로는 부모 사슬이 이미 끊겨 .return 을 못 쓴다

 (셋 다 WL 의 captureCommitPhaseError 본문을 읽어 확인한 것이다)
 그래서 이 파일의 함수 이름에 safely- 가 붙은 것이 넷이다
   safelyAttachRef / safelyDetachRef
   safelyCallDestroy / safelyCallComponentWillUnmount
 앞의 둘에 주석이 있다
   L826  "Capture errors so they don't interrupt mounting."
   L709  "Capture errors so they don't interrupt unmounting."
```

## 어디로 이어지는가

```text
 [커밋]         CMW 가 순회하며 이 파일을 부른다
                before-mutation -> commitClassSnapshot
                mutation        -> cleanup 들, componentWillUnmount, detachRef
                layout          -> 콜백 들, componentDidMount/DidUpdate, attachRef

 [패시브 이펙트] commitHookPassiveMountEffects / UnmountEffects 를 부른다

 [훅]           Effect 리스트와 HookFlags 가 거기서 만들어진다

 [업데이트 큐]   commitCallbacks / commitHiddenCallbacks 가 그 파일 함수다
                이 파일은 그것을 감싸 try/catch 를 붙인다

 [클래스 컴포넌트]  렌더 단계가 세운 Update / Snapshot 플래그를 보고
                CMW 가 여기를 부른다
```

## 결과가 쓰이는 곳

```text
 inst.destroy
      --> 다음 커밋의 cleanup 이 꺼내 쓴다
      --> Effect 객체는 렌더마다 새로 만들어지지만 inst 는 이어진다

 instance.__reactInternalSnapshotBeforeUpdate
      --> before-mutation 패스가 담고 layout 패스가 읽는다

 finishedWork.refCleanup
      --> 함수 ref 의 반환값. 다음에 뗄 때 쓴다

 captureCommitPhaseError
      --> 에러를 가장 가까운 경계로 올려 보낸다
```

## 다루지 않는 것

`ReactFiberCommitWork.js` 의 순회 자체(어떤 플래그를 보고 어느 함수를 부르는지 — [커밋](../commit/README.md)에 있다), `runWithFiberInDEV`(`ReactCurrentFiber`)가 DEV 스택을 세우는 방식, `captureCommitPhaseError`(`ReactFiberWorkLoop` L4894)가 경계를 찾아 올라가는 본문([에러와 Suspense](../throw/README.md)에 있다), `ReactFiberApplyGesture.js` 의 제스처 시스템이 왜 insertion 이펙트만 돌리는지, `startEffectTimer` / `recordEffectDuration`(`ReactProfilerTimer`)의 측정 방식, `getPublicInstance` / `createFragmentInstance` / `createViewTransitionInstance` 같은 호스트 설정 함수는 이 문서의 범위 밖이다.

## 하위 메서드

- [01 훅 이펙트](01_hookEffects/README.md)
- [02 클래스 생명주기](02_classLifecycles/README.md)
- [03 ref](03_refs/README.md)
- [04 프로파일러](04_profiler/README.md)
