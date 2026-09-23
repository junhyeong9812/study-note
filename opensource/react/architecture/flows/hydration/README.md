# 하이드레이션

상위: [React 아키텍처 지도](../../README.md)

서버가 보낸 HTML 을 버리지 않고 **그 위에 fiber 트리를 얹는다**. 커서 하나가 DOM 을 걸으며 fiber 마다 노드를 하나씩 집는다.

이 흐름에서 이 지도의 오래된 오류 하나가 드러났다 — **throw 를 제어 흐름으로 쓰는 센티널이 셋이 아니라 다섯**이고, 그중 둘이 여기 있다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberHydrationContext.js`(989줄) 기준이다. `BW` = `ReactFiberBeginWork.js`, `CW` = `ReactFiberCompleteWork.js`, `THROW` = `ReactFiberThrow.js`, `WL` = `ReactFiberWorkLoop.js`, `UW` = `ReactFiberUnwindWork.js`.

## 전체 그림

```text
 모듈 전역 일곱이 상태의 전부다  L80-94

 hydrationParentFiber    지금 어느 fiber 아래인가
 nextHydratableInstance  ★ 커서. 다음에 집을 DOM 노드
 isHydrating             지금 수화 중인가
 rootOrSingletonContext  루트·싱글톤 바로 아래인가
 hydrationErrors         모아 둔 에러
 didSuspendOrErrorDEV    [DEV] 이미 서스펜드/에러가 났나
 hydrationDiffRootDEV    [DEV] 어긋남 트리
```

```text
 ★★ 단계 둘에 걸쳐 있다. "집는 것" 과 "수화하는 것" 이 다르다

 begin 단계
   BW --> tryToClaimNextHydratableInstance   노드를 **맞춰만** 본다
          fiber.stateNode 에 붙인다

 complete 단계
   CW --> popHydrationState                  빠져나오며 커서를 옮긴다
   CW --> prepareToHydrateHostInstance       속성과 텍스트를 **실제로 맞춘다**

 CW L1407  const wasHydrated = popHydrationState(workInProgress)
 CW L1408  wasHydrated 이면
 CW L1411    prepareToHydrateHostInstance(...)
 CW L1409-1410 의 TODO - "Move this and createInstance step into the beginPhase
                          to consolidate."

 => 호스트 fiber 하나가 **두 단계에서 각각 어긋남을 던질 수 있다**
 => popHydrationState 의 반환값이 "수화할까 새로 만들까" 스위치다
```

1. [커서](01_cursor/README.md) — 들어가기와 집기. 경계를 만나면 fiber 를 하나 더 만든다.
2. [어긋남](02_mismatch/README.md) — 그 긴 에러 메시지가 만들어지는 자리와 센티널 다섯.
3. [빠져나오기](03_pop/README.md) — 남은 노드 검사와 커서 전진, 되감기용 포크.
4. [DEV 어긋남 트리](04_devDiff/README.md) — 메시지 끝에 붙는 diff.

```text
 ★★★ 센티널이 다섯이다 (이 지도가 "셋" 이라 적었던 것을 고친다)

 SuspenseException            Thenable L51   use / 렌더 중
 SuspenseyCommitException     Thenable L61   completeWork 의 리소스 대기
 SuspenseActionException      Thenable L66   useActionState
 HydrationMismatchException   HYD L383       ★ 어긋남
 SelectiveHydrationException  BW L313        ★ 선택적 수화

 그런데 동급이 아니다. work loop 가 알아보는 것은 **넷**이다
   WL L2305 / L2306 / L2321 / L2324 가 넷을 이름으로 가르고,
   HydrationMismatchException 은 WL L2335 의 else 로 떨어져
   L2336 "This is a regular error." 취급을 받는다

 그것을 알아보는 곳은 THROW L585 / L597 하나뿐이고,
 하는 일도 "두 번 감싸지 마라" 다

 ★ 그리고 "case Throw 가 되던짐"(BW L4465)은 센티널이 아니다.
   사용자의 진짜 에러를 다시 던지는 것이라 종류가 다르다
```

```text
 ★★★ 왜 예외를 제어 흐름으로 쓰는가 — 근거가 적혀 있다

 BW L1034-1041 (SelectiveHydrationException 을 던지기 직전)

   "Throw a special object that signals to the work loop that it should
    interrupt the current render.

    Because we're inside a React-only execution stack, we don't strictly
    need to throw here — we could instead modify some internal work loop
    state. But using an exception means we don't need to check for this
    case on every iteration of the work loop. So doing it this way moves
    the check out of the fast path."

 => work loop 의 **매 반복마다 검사하지 않으려고** 예외를 쓴다
    (이 이유를 다른 센티널에도 그대로 적용하는 것은 내 판단이다.
     주석은 이 자리만 말한다)
```

```text
 ★ 이 빌드에서 죽은 갈래

 supportsHydration = true (CFG L3779)
 => 이 파일의 `if (!supportsHydration)` 가드 **열한 개**가 전부 죽었다
    L164 / L187 / L210 / L563 / L585 / L656 / L678 / L720 / L761 / L859 / L880
    그중 다섯(L563 / L585 / L656 / L678 / L720)은 "Expected ... to never be
    called" 불변식이라 죽은 것을 넘어 **설계상 도달 불가**다

 supportsSingletons = true (CFG L4643)
 => popHydrationState 의 else 갈래(L799-816)가 죽었다
    다만 조건이 산 쪽과 **논리적으로 같다** ([03]에 있다)
```

## 어디로 이어지는가

```text
 [beginWork]    enterHydrationState / reenter* 로 들어가고
                claim* 로 노드를 집는다
                SelectiveHydrationException 도 여기서 던진다

 [completeWork] popHydrationState 로 나오고
                prepareToHydrate* 로 실제 수화를 한다
                emitPendingHydrationWarnings / upgradeHydrationErrorsToRecoverable

 [에러와 Suspense]  어긋남을 받아 경계를 찾고 ForceClientRender 를 세운다

 [렌더 루프]     되감기 중 popHydrationStateOnInterruptedWork 를 부른다

 [훅]           useId 와 useActionState 가 getIsHydrating 을 본다

 [자식 조정]     여섯 자리에서 getIsHydrating 을 본다
```

```text
 ★ getIsHydrating(L921)이 이 파일에서 가장 많이 불리는 export 다

 이 파일은 수화를 **수행**하기도 하지만
 "지금 수화 중인가" 를 온 리콘실러에 알려 주는 자리이기도 하다
```

## 결과가 쓰이는 곳

```text
 fiber.stateNode
      --> 서버가 만든 DOM 노드가 그대로 붙는다. 새로 만들지 않는다

 popHydrationState 의 반환값
      --> [completeWork]가 "수화할까 새로 만들까" 를 가른다

 hydrationErrors
      --> upgradeHydrationErrorsToRecoverable 이 복구 가능 에러로 올린다
      --> onRecoverableError 로 사용자에게 간다

 ForceClientRender 플래그
      --> 어긋난 경계를 클라이언트 렌더로 다시 그린다
```

## 다루지 않는 것

서버 쪽(`react-server`, `ReactFizzServer`)이 그 HTML 과 주석 마커를 만드는 전체 경로, `hydrateInstance` / `hydrateProperties` / `hydrateText` / `diffHydratedProperties`(`ReactDOMComponent`, `ReactFiberConfigDOM`)가 속성을 실제로 비교하고 맞추는 규칙과 `suppressHydrationWarning`, `canHydrateInstance` 계열이 주석 노드와 공백을 건너뛰며 후보를 고르는 방식, 선택적 수화(`SelectiveHydrationException`, BW L1042 / L3058)가 우선순위를 올려 사용자가 만진 경계를 먼저 수화하는 규칙, `useId` 의 id 생성과 `ReactFiberTreeContext` 의 스택, 수화 실패 뒤 `retrySuspenseComponentWithoutHydrating`(BW L2860) / `mountHostRootWithoutHydrating`(BW L1924)이 트리를 다시 그리는 본문([beginWork](../begin-work/README.md)에 있다), `ReactFiberConfigDOM` 의 `hydrateHoistable` / 리소스 수화는 이 문서의 범위 밖이다.

## 하위 메서드

- [01 커서](01_cursor/README.md)
- [02 어긋남](02_mismatch/README.md)
- [03 빠져나오기](03_pop/README.md)
- [04 DEV 어긋남 트리](04_devDiff/README.md)
