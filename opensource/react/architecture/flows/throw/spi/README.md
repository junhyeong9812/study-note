# spi

상위: [에러와 Suspense 흐름](../README.md)

이 흐름의 계약은 **세 플래그**(`Incomplete` / `ShouldCapture` / `DidCapture`)와 **"셸"** 이라는 개념이다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). `TH` = `ReactFiberThrow.js`, `WL` = `ReactFiberWorkLoop.js`, `UNW` = `ReactFiberUnwindWork.js`, `BW` = `ReactFiberBeginWork.js`.

## 세 플래그의 비트

```js
// ReactFiberFlags.js L56-L62
// Union of all commit flags (flags with the lifetime of a particular commit)
export const HostEffectMask = /*               */ 0b0000000000000000111111111111111;

// These are not really side effects, but we still reuse this field.
export const Incomplete = /*                   */ 0b0000000000000001000000000000000;
export const ShouldCapture = /*                */ 0b0000000000000010000000000000000;
export const ForceUpdateForLegacySuspense = /* */ 0b0000000000000100000000000000000;
```

> Union of all commit flags (flags with the lifetime of a particular commit)

> These are not really side effects, but we still reuse this field.

```text
 DidCapture      8번째 비트   0b...010000000
 HostEffectMask  하위 15비트  0b...111111111111111
 Incomplete     16번째 비트   0b...1000000000000000
 ShouldCapture  17번째 비트   0b...10000000000000000

 ★ DidCapture 만 HostEffectMask 안에 있다
   그래서 WL L3435 의 next.flags &= HostEffectMask 가
   Incomplete 와 ShouldCapture 는 지우고 DidCapture 만 남긴다
```

## 플래그가 옮겨 가는 길

```text
 1  Incomplete 를 붙인다        TH L372
 2  경계에 ShouldCapture 를 붙인다
 3  Incomplete 를 읽어 되감기로 간다   WL L3257
 4  unwindWork 가 ShouldCapture -> DidCapture   UNW L84 등
 5  WL L3435 가 Incomplete / ShouldCapture 를 턴다
 6  beginWork 가 DidCapture 를 보고 fallback 을 고른다

 못 찾으면 3-4 사이에서
   WL L3466 returnFiber.flags |= Incomplete 로 부모에게 넘기고
   나중에 completeUnitOfWork(WL L3354)가 다시 읽는다
```

### ShouldCapture 를 세우는 자리 여덟

| 위치 | 맥락 |
|---|---|
| TH L276 | 레거시 Suspense, 경계와 returnFiber 가 같을 때 |
| TH L357 | `markSuspenseBoundaryShouldCapture` 의 concurrent 갈래 |
| TH L489 | 서스펜션인데 핸들러가 `OffscreenComponent` (직접 세운다) |
| TH L610 | 수화 에러인데 수화 경계가 없어 루트를 클라이언트 렌더할 때 |
| TH L650 | 경계 찾기 루프의 `HostRoot` |
| TH L672 | 경계 찾기 루프의 `ClassComponent` |
| TH L692 | 경계 찾기 루프의 숨은 `OffscreenComponent` |
| BW L1608 | `__DEV__` 전용, DevTools 가 경계를 강제로 에러낼 때 |

```text
 ★ markSuspenseBoundaryShouldCapture 를 거치지 않는 세터가 다섯이다
   (L489 / L610 / L650 / L672 / L692)

 즉 "서스펜스 경계 표시 함수" 는 여러 경로 중 하나일 뿐이다
```

### DidCapture 를 세우는 자리

```text
 되감기가 하는 것 (여섯)
   UNW L84 / L114 / L144 / L172 / L190 / L223

 되감기 밖에서 세우는 것
   TH L278                레거시 Suspense - ShouldCapture 를 건너뛴다
   ClassUpdateQueue       CaptureUpdate 업데이트를 처리할 때
                          (flags & ~ShouldCapture) | DidCapture
   BW L1110 / L3152       탈수 경계가 2차 패스에서 탈수 상태를 유지할 때
   BW L3099               탈수 Suspense 가 서버 데이터를 기다릴 때
   BW L3996 / L4012       조기 바이아웃 경로의 탈수 경계
   BW L3438               SuspenseList 가 ForceSuspenseFallback 을 받을 때
   BW L4117               SuspenseList 가 이전에 서스펜드했고 자식 일이 없을 때
   CompleteWork L1746 / L1797 / L1821 / L1854
                          SuspenseList 의 complete 단계
   BW L1607 / L2373       __DEV__ DevTools 강제 에러 / 강제 서스펜드

 지우는 자리
   BW L1133 / L2386       경계가 fallback 을 고르면서 소거
   WL L3435               HostEffectMask 로 터는 것과 별개로 DidCapture 는 남는다

 => ShouldCapture -> DidCapture 가 주 경로지만 유일하지 않다
 (이 목록은 검증 과정에서 전수 조사된 것이고,
  나는 UnwindWork 의 여섯 자리와 비트 위치를 직접 확인했다)
```

## "셸" 이 무엇인가

```text
 getShellBoundary() 는 모듈 변수 shellBoundary 를 돌려준다
 (ReactFiberSuspenseContext.js)

 주석이 정의를 적는다
   현재 트리에서 **보이지 않는 가장 바깥 경계**이고
   그 위쪽 전부가 "셸" 이다

   null  이면  셸을 렌더 중이다
   non-null 이면  이미 보이던 트리가 아닌 새 트리 안을 렌더 중이다

 왜 중요한가 - 셸에서 fallback 을 띄우면
 **이미 보이던 콘텐츠를 감추게** 된다.
 새 트리에서는 감출 것이 없으니 괜찮다

 그래서 [01] L414 의 분기가 있다
   셸이면    renderDidSuspendDelayIfPossible   커밋을 미룬다
   깊으면    (새 경계일 때만) renderDidSuspend  fallback 이 나타났다고 알린다

 shellBoundary 가 세워지는 자리
   경계를 push 할 때 shellBoundary 가 아직 null 이고
     (가) 새 마운트이거나 현재 트리가 숨겨져 있거나
     (나) 보이지만 지금 fallback 을 표시 중이면
   그 경계를 shellBoundary 로 삼는다

 popSuspenseHandler 가 같은 fiber 면 null 로 되돌린다

 (이 설명은 검증 과정에서 확인된 것이고,
  나는 getShellBoundary 가 쓰이는 자리까지만 직접 봤다)
```

## 에러 업데이트

```text
 createRootErrorUpdate (TH L93)
   tag = CaptureUpdate
   payload = { element: null }        루트를 null 로 렌더해 언마운트한다
   callback = logUncaughtError

 createClassErrorUpdate (TH L114)
   세 줄뿐이다. createUpdate + tag = CaptureUpdate

 initializeClassErrorUpdate (TH L120)
   내용물을 채운다
     getDerivedStateFromError 가 있으면
       payload = () => getDerivedStateFromError(error)
     componentDidCatch 가 있으면
       callback 을 덮어써서 그것을 부른다

 ★ 둘의 실행 시점이 다르다
   getDerivedStateFromError  payload  -> **렌더 단계** (processUpdateQueue)
   componentDidCatch         callback -> **커밋 단계**

 그리고 CaptureUpdate 태그를 처리할 때
 ClassUpdateQueue 가 (flags & ~ShouldCapture) | DidCapture 를 한다

 (세 함수의 본문은 검증 과정에서 확인된 것이다)
```

## 에러 경계의 범위

```text
 렌더 단계  TH L648 switch - HostRoot / ClassComponent / OffscreenComponent
 커밋 단계  captureCommitPhaseError - HostRoot / ClassComponent

 사용자가 정의하는 에러 경계는 **ClassComponent 뿐**이다
   HostRoot 는 루트를 null 로 언마운트하는 최후 수단이고
   OffscreenComponent 는 숨은 트리의 prerender 를 중단시키는 것이다

 함수 컴포넌트나 훅으로 만드는 에러 경계는 저장소에 없다
 (useErrorBoundary 는 존재하지 않는다)

 인정 조건 (TH L666-670)
   아직 DidCapture 가 없고
   getDerivedStateFromError 가 있거나
   (instance 가 있고 componentDidCatch 가 있고
    이미 실패한 레거시 경계가 아니면)
```

## 빌드 범위

```text
 disableLegacyMode
   packages/shared/ReactFeatureFlags.js  true
   forks 의 www / test-renderer          true
   forks 의 native-fb / native-oss / test-renderer.native-fb   **false**

 => 이 흐름의 레거시 갈래는
    "죽었다" 가 아니라 **"OSS 웹 빌드에서 안 돈다"** 다

    TH L250-315  레거시 Suspense 전체
    TH L284      Incomplete 를 지우는 자리
    TH L279      ForceUpdateForLegacySuspense 를 세우는 유일한 자리
    TH L537-547  서스펜션을 에러로 바꾸는 자리
```

## 결과가 쓰이는 곳

```text
 Incomplete
      --> WL L3257 / L3354 두 곳이 읽는다
      --> completeWork 를 건너뛰고 unwindWork 로 보낸다

 ShouldCapture
      --> unwindWork 가 되감기를 멈출 자리를 안다
      --> WL L3435 에서 털린다

 DidCapture
      --> beginWork 가 fallback 갈래를 고른다
      --> 되감기 뒤에도 남는 유일한 표시다

 에러 업데이트
      --> 경계가 다시 렌더될 때 상태를 바꾸고
      --> 커밋 때 componentDidCatch 를 부른다
```

## 다루지 않는 것

`ReactFiberSuspenseContext.js` 의 push/pop 전체와 `enableSuspenseAvoidThisFallback` 예외, `attachPingListener` 와 ping 스케줄링, `retryQueue` / `OffscreenQueue` 의 관리, `createCapturedValueAtFiber` 가 담는 컴포넌트 스택, `logUncaughtError` / `logCaughtError` 의 콘솔 출력, `isAlreadyFailedLegacyErrorBoundary` 와 레거시 경계 추적, `queueHydrationError` 의 행선지는 이 문서의 범위 밖이다.
