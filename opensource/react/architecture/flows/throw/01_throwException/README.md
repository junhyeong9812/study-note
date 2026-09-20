# throwException

상위: [에러와 Suspense 흐름](../README.md)

**첫 줄이 되감기를 시작시키고**, 그 다음 `thenable` 인지 하나만 보고 서스펜션과 에러로 갈린다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberThrow.js` L364-L705 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberThrow.js#L364-L705))

## 실제 코드

되감기를 시작시키는 줄.

```js
// ReactFiberThrow.js L371-L372
  // The source fiber did not complete.
  sourceFiber.flags |= Incomplete;
```

> The source fiber did not complete.

그리고 갈림길.

```js
// ReactFiberThrow.js L383-L385
      // This is a wakeable. The component suspended.
      const wakeable: Wakeable = value as any;
      resetSuspendedComponent(sourceFiber, rootRenderLanes);
```

에러 경로의 끝 — 경계를 못 찾았을 때.

```js
// ReactFiberThrow.js L635-L643
  // We didn't find a boundary that could handle this type of exception. Start
  // over and traverse parent path again, this time treating the exception
  // as an error.

  if (returnFiber === null) {
    // There's no return fiber, which means the root errored. This should never
    // happen. Return `true` to trigger a fatal error (panic).
    return true;
  }
```

> There's no return fiber, which means the root errored. This **should never** happen. Return `true` to trigger a fatal error (panic).

## 동작 흐름

```text
 TH L364  function throwException(root, returnFiber, sourceFiber, value, rootRenderLanes)

 L372  sourceFiber.flags |= Incomplete
 L374  [FLAG:enableUpdaterTracking]
 L375    DevTools 가 있으면
 L377      restorePendingUpdaters(root, rootRenderLanes)

 --- 서스펜션 경로 ---
 L381  value 가 객체이고
 L382    value.then 이 함수이면
 L385      resetSuspendedComponent(sourceFiber, rootRenderLanes)
 L397      suspenseBoundary = getSuspenseHandler()

 L398      경계가 있으면 tag 로 갈린다 (switch L399)
 L400-402    Activity / Suspense / SuspenseList
 L413          concurrent 면
 L414            getShellBoundary() === null 이면 (셸에서)
 L417              renderDidSuspendDelayIfPossible()
 L418            아니면 (셸보다 깊은 곳)
 L432              alternate === null 이면 (새 경계면)
 L433                renderDidSuspend()
 L438          flags &= ~ForceClientRender
 L439          markSuspenseBoundaryShouldCapture(...)      -> [02]
 L465          suspensey 리소스면 flags |= ScheduleRetry
 L469          아니면 retryQueue 에 wakeable 을 넣는다
 L481          concurrent 면 attachPingListener(...)
 L485          => return false

 L487        OffscreenComponent
 L489          flags |= ShouldCapture     ([02]를 거치지 않고 직접 세운다)
 L513          attachPingListener(...)
 L515          => return false

 L519        그 밖의 tag 이면
              => throw new Error('Unexpected Suspense handler tag ...')

 L523      경계가 없으면
 L527        concurrent 루트면
 L534          attachPingListener(...)
 L535          renderDidSuspendDelayIfPossible()
 L536          => return false
 L537        레거시 루트면
 L545          value = uncaughtSuspenseError        ** 에러로 바꾼다 **
              (return 없이 아래로 흘러내린다)

 --- 에러 경로 ---
 L551  // This is a regular error, not a Suspense wakeable.
 L575  수화 중이면 markSuspenseBoundaryShouldCapture(...) -> [02]
 L595  => return false
 L614  루트 에러면 createRootErrorUpdate(...) ; L621 => return false

 L632  queueConcurrentError(...)
 L633  renderDidError()
 L639  returnFiber === null 이면
 L642    => return true            ** panic **

 --- 경계 찾기 루프 ---
 L646  workInProgress = returnFiber
 L647  do {
 L648    switch (workInProgress.tag)
 L649      HostRoot           -> ShouldCapture, 에러 업데이트, L659 return false
 L661      ClassComponent     -> 조건 맞으면 ShouldCapture, 업데이트, L679 return false
 L681                            아니면 break
 L682      OffscreenComponent -> 숨겨진 상태면 L692 ShouldCapture, L693 return false
 L695                            아니면 break
 L697      default: L698 break
 L701    workInProgress = workInProgress.return      ** 부모로 올라간다 **
 L702  } while (workInProgress !== null)
 L704  => return false
```

```text
 ★ 갈림길이 thenable 검사 하나다

 L381  value !== null && typeof value === 'object'
 L382    typeof value.then === 'function'

 중첩 if 둘이고 else 가 없다.
 서스펜션 갈래가 return 없이 끝나면 아래 에러 경로로 흘러내린다

 그래서 "경계가 없는 레거시 루트" (L537-547)에서
 서스펜션이 에러로 바뀐다 - 두 갈래가 합류하는 유일한 자리다
 (레거시 갈래라 OSS 웹 빌드에서는 도달하지 않는다)
```

```text
 경계 찾기 루프의 모양

 L647  do { ... } while (workInProgress !== null)

 case 가 셋이고 default 가 하나다
 잡을 수 있으면 return false 로 끝내고,
 아니면 break 로 switch 를 빠져나와
 L701 이 부모로 올려 보낸다

 루프가 끝나면 (루트까지 올라가 return 이 null 이 되면)
 L704 가 return false 다 - 아무도 못 잡았다는 뜻이다

 ★ 그런데 HostRoot 가 항상 잡으므로 (L649-659)
   실제로는 루트에 닿기 전에 끝난다
```

```text
 클래스 경계로 인정받는 조건

 L666  (flags & DidCapture) === NoFlags      이미 잡은 적이 없고
 L667  getDerivedStateFromError 가 함수이거나
 L668  instance !== null 이고
 L669    componentDidCatch 가 함수이고
 L670    isAlreadyFailedLegacyErrorBoundary 가 아니면

 조건이 안 맞으면 L681 break 로 부모에게 넘긴다
 => 같은 에러가 위로 올라가며 다음 경계를 찾는다
```

```text
 OffscreenComponent 는 잡는 것이 아니다

 L682-696  숨겨진 Offscreen 안에서 에러가 났을 때다

 주석 L686-691
   "An error was thrown inside a hidden Offscreen boundary. This should
    not be allowed to escape into the visible part of the UI. Mark the
    boundary with ShouldCapture to abort the ongoing prerendering
    attempt. This is the same flag would be set if something were to
    suspend. It will be cleared the next time the boundary is attempted."

 => 에러를 처리하는 것이 아니라
    **보이는 UI 로 새어 나가지 않게 prerender 를 중단** 시키는 것이다
    서스펜드했을 때와 같은 플래그를 쓴다
```

```text
 반환값은 "치명적인가" 다

 return true 는 L642 하나뿐이다.
 returnFiber 가 null - 즉 루트가 에러났을 때다

 [렌더 루프]의 throwAndUnwindWorkLoop 가 그것을 받아
 panicOnRootError 를 부르고, 그 안에서
 RootFatalErrored 를 세우고 workInProgress 를 null 로 만든다
 => unwindWork 를 거치지 않으므로 스택 pop 도 건너뛴다

 return false 는 아홉 자리다
 (L485 / L515 / L536 / L595 / L621 / L659 / L679 / L693 / L704)
 그리고 갈래를 끝내는 throw 도 하나 있다 (L519)
```

## 결과가 쓰이는 곳

```text
 sourceFiber.flags |= Incomplete
      --> [렌더 루프] WL L3257 이 읽어 되감기로 보낸다

 경계의 ShouldCapture
      --> [03] unwindWork 가 DidCapture 로 바꾼다

 에러 업데이트
      --> 경계가 다시 렌더될 때 처리된다
      --> getDerivedStateFromError 는 렌더 단계, componentDidCatch 는 커밋 단계

 retryQueue / ping 리스너
      --> promise 가 풀리면 그 lane 을 다시 스케줄한다

 반환 boolean
      --> true 면 panic, false 면 되감기를 이어간다
```

## 다루지 않는 것

`resetSuspendedComponent`(L203)가 컨텍스트를 다시 전파하는 이유, `attachPingListener` 와 ping 의 스케줄링, `createRootErrorUpdate`(L93) / `createClassErrorUpdate`(L114) / `initializeClassErrorUpdate`(L120)의 본문([spi](../spi/README.md)에 요약이 있다), 수화 에러 경로(L552-621)와 `ForceClientRender`, `queueConcurrentError` / `queueHydrationError` 의 행선지, `OffscreenQueue` 의 retryQueue 관리는 같은 뼈대의 곁가지라 요약만 했다.
