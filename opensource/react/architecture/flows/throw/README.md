# 에러와 Suspense

상위: [React 아키텍처 지도](../../README.md)

[렌더 루프](../render-loop/README.md)가 되감기로 갈아탄 뒤, **어디까지 되감을지 정하는 자리**다. 서스펜션과 에러가 같은 함수에서 갈린다.

이 흐름의 핵심은 셋이다. **한 줄이 되감기를 시작시키고**, **플래그가 세 단계로 옮겨 가며**, **경계를 못 찾으면 서스펜션이 에러로 바뀐다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). `TH` = `ReactFiberThrow.js`, `WL` = `ReactFiberWorkLoop.js`, `UNW` = `ReactFiberUnwindWork.js`.

## 전체 그림

```text
 [렌더 루프]의 handleThrow 가 값을 상태로 바꾼 뒤
 throwAndUnwindWorkLoop (WL L3215) 가 이 흐름을 부른다

 [01] throwException                          TH L364-705
      +-- sourceFiber.flags |= Incomplete      TH L372   ** 되감기의 시작 **
      +-- thenable 인가                        TH L381-382
      |     예 -> 서스펜션 경로  (경계를 찾아 ShouldCapture)
      |     아니오 -> 에러 경로  (경계를 찾아 ShouldCapture + 에러 업데이트)
      +-- 치명적이면 => return true             TH L642

 WL L3232  didFatal = throwException(...)
 WL L3240    didFatal 이면 panicOnRootError -> RootFatalErrored
 WL L3257  unitOfWork.flags & Incomplete 이면
 WL L3308    unwindUnitOfWork(...)             ** 여기서 되감는다 **
 WL L3319  아니면 completeUnitOfWork(...)

 [02] unwindWork                              UNW L66-249
      +-- ShouldCapture 를 DidCapture 로 바꾼다  여섯 tag
      +-- 스택을 pop 한다
      +-- 경계를 찾으면 그 fiber 를 돌려준다

 WL L3435  next.flags &= HostEffectMask        ** 플래그를 털어 낸다 **
 WL L3436  workInProgress = next               -> begin 단계로 되돌아간다
```

1. [throwException](01_throwException/README.md)이 경계를 찾아 표시한다.
2. [markSuspenseBoundaryShouldCapture](02_markSuspenseBoundary/README.md)가 서스펜스 경계를 표시한다.
3. [되감기](03_unwind/README.md)가 표시를 확정하고 스택을 되돌린다.

```text
 ★ 한 줄이 되감기를 시작시킨다

 TH L372  sourceFiber.flags |= Incomplete;

 이 플래그를 **곧바로** 읽는 곳은 WL L3257 이다
   L3257  if (unitOfWork.flags & Incomplete)
   L3308    unwindUnitOfWork(...)
   L3319  아니면 completeUnitOfWork(...)

 그리고 unwindUnitOfWork 가 부모에게도 같은 플래그를 칠한다 (WL L3466)
 => 형제를 마저 렌더한 뒤 그 부모가 완료될 차례가 오면
    completeUnitOfWork(WL L3354)가 다시 같은 플래그를 보고 되감기로 간다

 [completeWork] 흐름에서 "case Throw 가 도달 불가" 라고 본 근거가 이것이다
```

```text
 ★ 플래그가 세 단계로 옮겨 간다

 1  표시   throwException 이 경계에 ShouldCapture 를 붙인다
 2  확정   unwindWork 가 그것을 DidCapture 로 바꾼다 (UNW L84 등)
 3  사용   beginWork 가 DidCapture 를 보고 fallback 갈래를 고른다

 그리고 네 번째가 있다 - **털어 내기**

 WL L3435  next.flags &= HostEffectMask;
   주석 L3433-3434 "Since we're restarting, remove anything that is not
   a host effect from the effect tag."

 HostEffectMask 는 하위 15비트인데
   Incomplete    는 16번째 비트
   ShouldCapture 는 17번째 비트
   DidCapture    는 8번째 비트
 => 이 한 줄이 Incomplete 와 ShouldCapture 를 **함께 지우고**
    DidCapture 만 남긴다

 "ShouldCapture 는 왜 한 번 쓰고 사라지나" 의 답이다
```

```text
 ★ 경계를 못 찾으면 서스펜션이 에러가 된다

 서스펜스 핸들러가 없을 때 (TH L523 else)
   concurrent 루트면  ping 리스너를 달고 지연 서스펜드로 끝낸다 (L536 return false)
   레거시 루트면      uncaughtSuspenseError 를 만들어
                      value 를 그 에러로 **교체하고** (L545)
                      return 없이 에러 경로로 흘러내린다

 => 서스펜션 갈래와 에러 갈래가 완전히 배타적이지 않다.
    한 호출 안에서 앞의 것이 뒤의 것으로 바뀔 수 있다
    (레거시 갈래이므로 OSS 웹 빌드에서는 도달하지 않는다)
```

```text
 에러 경계는 클래스 컴포넌트뿐이다

 경계를 찾아 올라가는 루프(TH L647-702)의 switch 에 case 가 셋이다
   L649  HostRoot            루트를 null 로 렌더해 언마운트한다
   L661  ClassComponent      **사용자가 정의하는 유일한 에러 경계**
   L682  OffscreenComponent  숨은 트리의 prerender 를 중단시킨다
   L697  default: break

 앞의 둘만 에러를 "처리" 하고, 셋째는 전파를 멈추는 것이다.
 함수 컴포넌트나 훅으로 만드는 에러 경계는 저장소에 없다

 (커밋 단계의 captureCommitPhaseError 도 같은 둘만 본다.
  이것은 검증 과정에서 확인된 것이다)
```

## 어디로 이어지는가

```text
 [렌더 루프]    throwAndUnwindWorkLoop 가 이 흐름을 부르고
                되감기가 끝나면 work loop 로 돌아간다

 [beginWork]    DidCapture 를 보고 fallback 갈래를 고른다

 [completeWork] Incomplete 가 completeWork 를 건너뛰게 한다

 [커밋]         에러 업데이트가 커밋 단계에서 componentDidCatch 를 부른다
```

## 결과가 쓰이는 곳

```text
 Incomplete
      --> WL L3257 이 읽어 되감기로 보낸다
      --> unwindUnitOfWork 가 부모로 전파한다

 ShouldCapture -> DidCapture
      --> 어느 경계가 잡을지 정한다
      --> beginWork 가 fallback 을 고르는 근거다

 에러 업데이트 (CaptureUpdate)
      --> getDerivedStateFromError 는 payload 로 렌더 단계에서
      --> componentDidCatch 는 callback 으로 커밋 단계에서

 retryQueue / ping 리스너
      --> promise 가 풀리면 다시 렌더를 건다
```

## 다루지 않는 것

서스펜션 경로의 `OffscreenComponent` 갈래(TH L487)와 retryQueue 적재, `attachPingListener` 가 promise 에 리스너를 다는 방식, `resetSuspendedComponent`(TH L203)의 컨텍스트 재전파, `createCapturedValueAtFiber` 가 담는 스택, `queueConcurrentError` / `queueHydrationError` 의 행선지, `unwindInterruptedWork`(UNW L251), 수화 에러와 `ForceClientRender` 의 전체 경로, `panicOnRootError`(WL L3333) 이후는 같은 뼈대의 곁가지라 요약만 했다. 플래그 전이 전수와 경계 개념은 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 throwException](01_throwException/README.md)
- [02 markSuspenseBoundaryShouldCapture](02_markSuspenseBoundary/README.md)
- [03 되감기](03_unwind/README.md)
- [spi](spi/README.md) — 플래그 전이, 셸, 에러 업데이트
