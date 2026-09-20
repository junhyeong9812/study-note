# 되감기

상위: [에러와 Suspense 흐름](../README.md)

표시를 **확정하고** 스택을 되돌린다. 그리고 begin 단계로 돌아가기 직전에 **플래그를 털어 낸다.**

## 위치

`packages/react-reconciler` / `src` / `ReactFiberUnwindWork.js` L66-L249 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberUnwindWork.js#L66-L249))

## 실제 코드

표시를 확정하는 자리. 같은 꼴이 여섯 번 나온다.

```js
// ReactFiberUnwindWork.js L83-L92
      if (flags & ShouldCapture) {
        workInProgress.flags = (flags & ~ShouldCapture) | DidCapture;
        if (
          enableProfilerTimer &&
          (workInProgress.mode & ProfileMode) !== NoMode
        ) {
          transferActualDuration(workInProgress);
        }
        return workInProgress;
      }
```

그리고 begin 단계로 돌아가기 전에 플래그를 턴다.

```js
// ReactFiberWorkLoop.js L3430-L3437
      // Found a boundary that can handle this exception. Re-renter the
      // begin phase. This branch will return us to the normal work loop.
      //
      // Since we're restarting, remove anything that is not a host effect
      // from the effect tag.
      next.flags &= HostEffectMask;
      workInProgress = next;
      return;
```

> Found a boundary that can handle this exception. Re-renter the begin phase. This branch will return us to the normal work loop. Since we're restarting, remove anything that is not a host effect from the effect tag.

## 동작 흐름

```text
 [렌더 루프] throwAndUnwindWorkLoop (WL L3215)
 WL L3232  didFatal = throwException(...)        -> [01]
 WL L3240  치명적이면 panicOnRootError 후 return
 WL L3257  unitOfWork.flags & Incomplete 이면
 WL L3308    unwindUnitOfWork(unitOfWork, skipSiblings)
 WL L3319  아니면 completeUnitOfWork(unitOfWork)

 unwindUnitOfWork 안에서
   UNW L66  unwindWork(current, workInProgress, renderLanes)
              ShouldCapture 가 있으면 DidCapture 로 바꾸고
              그 fiber 를 돌려준다
              없으면 스택만 pop 하고 null 을 돌려준다

   WL L3435  경계를 찾았으면 next.flags &= HostEffectMask
   WL L3436  workInProgress = next
   WL L3437  return                              -> begin 단계로 되돌아간다

   WL L3466  못 찾았으면 returnFiber.flags |= Incomplete
              -> 부모로 계속 올라간다
```

```text
 ★ 플래그를 털어 내는 한 줄

 WL L3435  next.flags &= HostEffectMask;

 HostEffectMask 는 하위 15비트다 (ReactFiberFlags L57)
   DidCapture     8번째 비트   -> **남는다**
   Incomplete    16번째 비트   -> 지워진다
   ShouldCapture 17번째 비트   -> 지워진다

 => 이 한 줄이 "다시 그리기 시작" 을 만든다
    되감기 표시는 지우고, "잡았다" 는 사실만 남긴다

 "ShouldCapture 는 왜 한 번 쓰고 사라지나" 의 답이다
```

```text
 전이가 일어나는 tag 여섯

 UNW L83-84    ClassComponent
 UNW L108-114  HostRoot          ★ 조건이 하나 더 있다
                 ShouldCapture 가 있고 **동시에 DidCapture 가 없을 때만**
 UNW L143-144  ActivityComponent
 UNW L171-172  SuspenseComponent
 UNW L189-190  SuspenseListComponent
 UNW L222-223  OffscreenComponent / LegacyHiddenComponent (case 공유)

 전이한 tag 는 workInProgress 를 돌려주고
 아니면 null 을 돌려준다. default 도 null 이다 (L246-247)

 SuspenseListComponent 만 부수효과가 더 있다
   renderState.rendering = null / tail = null  (L196-202)
   flags |= Update                              (L204)
```

```text
 unwindWork 는 pop 도 한다

 모든 tag 공통    popTreeContext (L75)

 HostRoot         popCacheProvider / popRootTransition /
                  popHostContainer / popTopLevelLegacyContextObject
 HostComponent 계열  popHostContext
 SuspenseComponent   popSuspenseHandler (무조건)
 ActivityComponent   popSuspenseHandler (탈수 상태일 때만)
 SuspenseList        popSuspenseListContext
 Offscreen/LegacyHidden  popSuspenseHandler / popHiddenContext / popTransition
 HostPortal          popHostContainer
 ContextProvider     popProvider
 CacheComponent      popCacheProvider

 => [completeWork]가 정상적으로 올라오며 하는 pop 을
    되감기도 똑같이 해야 스택이 어긋나지 않는다

 쌍둥이 함수가 하나 더 있다 - unwindInterruptedWork (UNW L251)
 같은 pop 만 하고 플래그 전이는 하지 않는다
 (렌더가 중단되어 스택만 풀 때 쓴다)
```

```text
 못 찾으면 부모로 전파한다

 WL L3466  returnFiber.flags |= Incomplete

 그래서 형제를 마저 렌더한 뒤 그 부모가 완료될 차례가 오면
 completeUnitOfWork (WL L3354) 가 같은 플래그를 보고
 다시 되감기로 보낸다

 => Incomplete 를 읽는 자리가 둘인 이유다
    WL L3257  던진 직후
    WL L3354  올라오다 만났을 때
```

```text
 전이가 되감기에서만 일어나는 것은 아니다

 클래스 경계는 에러 업데이트를 처리할 때도 같은 전이를 한다
   ReactFiberClassUpdateQueue 의 CaptureUpdate 처리
   (flags & ~ShouldCapture) | DidCapture

 그리고 DidCapture 를 되감기 밖에서 세우는 자리가 여럿 있다 -
 탈수 경계, SuspenseList, DEV 의 DevTools 강제 에러 등

 (전수 목록은 [spi](../spi/README.md)에 있다.
  이것은 검증 과정에서 확인된 것이고,
  나는 UnwindWork 의 여섯 자리를 직접 확인했다)
```

## 결과가 쓰이는 곳

```text
 DidCapture
      --> [beginWork]가 읽어 fallback 갈래를 고른다
      --> 되감기가 끝난 뒤에도 남는 유일한 표시다

 pop 한 스택
      --> 정상 경로가 밀어 둔 것을 짝 맞춰 꺼낸다
      --> 어긋나면 다음 렌더가 잘못된 컨텍스트를 본다

 workInProgress = next
      --> 경계 fiber 로 돌아가 begin 단계를 다시 한다

 returnFiber.flags |= Incomplete
      --> 못 찾았을 때 부모가 이어받는다
```

## 다루지 않는 것

`unwindUnitOfWork`(WL L3414)의 전체 본문과 `skipSiblings` 계산, `unwindInterruptedWork`(UNW L251), 각 `pop*` 함수의 구현, `panicOnRootError`(WL L3333) 이후, `HostEffectMask` 를 포함한 플래그 비트 배치의 나머지, `transferActualDuration` 의 프로파일러 계측은 같은 뼈대의 곁가지라 요약만 했다. 플래그 전이 전수는 [spi](../spi/README.md)에 있다.
