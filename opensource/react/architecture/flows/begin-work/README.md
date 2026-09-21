# beginWork

상위: [React 아키텍처 지도](../../README.md)

[렌더 루프](../render-loop/README.md)의 `performUnitOfWork` 가 부르는 **내려가는 쪽**이다. fiber 하나를 받아 **자식을 돌려주거나, `null` 을 돌려준다.**

이 흐름의 핵심은 셋이다. **같은 `tag` 에 대한 `switch` 가 둘이고**, **`null` 의 뜻이 둘이며**, **플래그가 꺼진 `case` 가 세 곳에서 서로 다르게 끝난다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberBeginWork.js` 기준이다.

## 전체 그림

```text
 [01] beginWork                                    L4189
      +-- [__DEV__] 핫 리로드 리마운트 => return       L4194-4209
      +-- 바이아웃 판정                               L4211-4274
      |     조건 여섯을 전부 통과하면
      |     => return [02] attemptEarlyBailoutIfNoScheduledUpdate   L4239
      +-- workInProgress.lanes = NoLanes            L4281
      +-- switch (workInProgress.tag)               L4283   case 29개
      |     대부분 => return update<타입>Component(...)
      |     case Throw => **throw** pendingProps      L4465
      +-- switch 를 빠져나오면 => **throw** Unknown unit of work tag   L4469

 [02] attemptEarlyBailoutIfNoScheduledUpdate       L3921
      +-- switch (workInProgress.tag)               L3929   case 29개 중 14개만
      |     대부분 스택에 push 하고 break
      |     여섯 case 는 자체 판단으로 따로 끝낸다
      +-- => return [03] bailoutOnAlreadyFinishedWork   L4186

 [03] bailoutOnAlreadyFinishedWork                 L3789
      +-- markSkippedUpdateLanes(workInProgress.lanes)   L3804
      +-- 이번 렌더 lanes 에 자식 일이 없으면 => return null   L3817 / L3820
      +-- 아니면 cloneChildFibers 후 => return child        L3827
```

1. [beginWork](01_beginWork/README.md)가 바이아웃할지 정하고 타입별로 갈린다.
2. [attemptEarlyBailoutIfNoScheduledUpdate](02_attemptEarlyBailoutIfNoScheduledUpdate/README.md)가 스택만 맞춰 두고 건너뛴다.
3. [bailoutOnAlreadyFinishedWork](03_bailoutOnAlreadyFinishedWork/README.md)가 서브트리를 건너뛸지 정한다.

```text
 tag 에 대한 switch 가 둘이다

 [01] L4283  case 29개   실제로 컴포넌트를 평가한다
 [02] L3929  case 14개   평가하지 않고 스택만 맞춘다

 왜 둘인가
   본 경로가 update*Component 안에서 pushHostContext, pushProvider 같은
   스택 푸시를 한다. 그리고 completeWork 가 올라오며 pop 한다

   바이아웃은 그 사이를 통째로 건너뛰는데,
   push 를 안 하면 pop 이 짝을 잃는다

 그래서 [02] 는 **본 경로의 push 만 골라 흉내 낸다**
 주석이 그렇게 적는다 (L3926-3928)
   "There's still some bookkeeping we that needs to be done in this
    optimized path, mostly pushing stuff onto the stack."
   (원문의 "we that" 은 오타 그대로다)

 14개인 이유도 여기 있다 - push 하는 tag 가 그만큼이다
 HostHoistable 과 ViewTransition 이 [02] 에 없는 것은 빠진 게 아니라
 그 둘이 본 경로에서도 push 를 안 하기 때문이다
```

```text
 null 의 뜻이 둘이다

 [01] 이 null 을 돌려주면 performUnitOfWork 는
 L3098 에서 completeUnitOfWork 로 넘긴다. 한 가지 동작뿐이다

 그런데 그 null 이 온 이유는 둘이다

   (가) 자식이 없다      updateHostText L2083 - 주석이 "This is terminal"
                         updateHostHoistable L2052
   (나) 건너뛴다         [03] L3817 / L3820
                         [02] 자체 return null L3998 / L4015 / L4061 / L4139

 (가) 는 "다 했다", (나) 는 "안 했다" 인데 반환값이 같다
 구분은 fiber 에 남은 lanes 로만 남는다 (L3804 markSkippedUpdateLanes)
```

```text
 ★ 플래그가 꺼진 case 를 처리하는 방식이 세 곳에서 다르다

 같은 무늬 - if (플래그) { ... } 그리고 그 다음 - 가 세 파일에 있는데
 결말이 셋 다 다르다

 (가) fiber 생성    ReactFiber.js getTag L605-738
      fallthrough 사슬이다. 다음 case 로 떨어진다
        LEGACY_HIDDEN -> VIEW_TRANSITION -> SCOPE -> TRACING_MARKER -> default
      default 는 fiberTag = Throw (L730)

 (나) [02] bailout  L4164-4184
      fallthrough 해서 L4186 의 bailout 으로 떨어진다. 무해하다

 (다) [01] 본 경로  L4416-4461
      break 로 switch 를 빠져나가 L4469 의 throw 에 닿는다

 그런데 (다) 는 실제로 도달하지 않는다 - (가) 가 먼저 막기 때문이다
 자세한 것은 [spi](spi/README.md)에 있다
```

```text
 ★ (가) 의 사슬이 중간에 끊긴다

 네 플래그 중 enableViewTransition 만 true 다

   enableLegacyHidden      false
   enableViewTransition    **true**
   enableScopeAPI          false
   enableTransitionTracing false

 사슬 순서가 LegacyHidden -> ViewTransition 이므로
 <LegacyHidden> 엘리먼트는 default 까지 가지 못하고
 켜져 있는 ViewTransition 가지에 걸린다 (ReactFiber.js L636-639)

 => 기본 빌드에서 <LegacyHidden> 은 조용히
    ViewTransitionComponent fiber 가 된다

 Scope 와 TracingMarker 는 ViewTransition 뒤에 있어 default 로 간다
 (코드가 그렇게 쓰여 있다는 사실만 적는다. 의도인지는 확인하지 못했다)
```

```text
 didReceiveUpdate - 모듈 전역 하나가 축이다

 L319  let didReceiveUpdate: boolean = false;

 [01] 이 이것을 세우고, update*Component 들이 읽는다
 대입 자리 여덟 중 다섯이 [01] 안에 있다

 밖에서 올리는 주체는 **훅 시스템 하나**다
   markWorkInProgressReceivedUpdate (L3763) 의 호출처가
   ReactFiberHooks.js 여섯 곳뿐이다

 즉 "props 는 같은데 다시 그려야 한다" 를 판정하는 곳이
 beginWork 와 훅 둘뿐이다
```

## 어디로 이어지는가

```text
 [렌더 루프]    performUnitOfWork 가 이 흐름을 부르고
                반환값이 null 이면 completeUnitOfWork 로 넘긴다

 [completeWork] 올라오며 이 흐름이 push 한 것을 pop 한다

 [훅]           update*Component 안에서 renderWithHooks 가 불린다
                didReceiveUpdate 를 올리는 유일한 외부 주체다
```

[훅](../hooks/README.md)은 따로 지도가 있다.

## 결과가 쓰이는 곳

```text
 반환값 (Fiber 또는 null)
      --> performUnitOfWork L3098 이 읽는다
      --> null 이면 completeUnitOfWork 로, 아니면 그 fiber 로 내려간다

 didReceiveUpdate
      --> update*Component 들이 읽어 다시 그릴지 정한다

 workInProgress.lanes = NoLanes (L4281)
      --> 이 렌더에서 처리했다는 표시다
      --> 건너뛴 lane 은 markSkippedUpdateLanes 가 따로 모은다

 스택 (컨텍스트·호스트·캐시)
      --> completeWork 가 pop 한다
      --> 바이아웃해도 짝이 맞아야 해서 [02] 가 있다
```

## 다루지 않는 것

`update*Component` 29종의 본문(`updateFunctionComponent`, `updateClassComponent`, `updateHostComponent`, `updateSuspenseComponent` 등)이 실제로 자식을 만드는 과정, `renderWithHooks` 와 훅 디스패처([훅 흐름](../hooks/README.md)에 따로 있다), `reconcileChildren` 의 자식 조정과 키 매칭([자식 조정 흐름](../reconcile-children/README.md)에 따로 있다), `pushHostContext` / `pushProvider` / `pushCacheProvider` 등 스택 푸시 함수의 구현, `cloneChildFibers`, `lazilyPropagateParentContextChanges` 와 컨텍스트 전파([컨텍스트 흐름](../context/README.md)에 따로 있다), `remountFiber`(L3830)의 핫 리로드는 같은 뼈대의 곁가지라 요약만 했다. `tag` 별 두 switch 대조표와 죽은 case 는 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 beginWork](01_beginWork/README.md)
- [02 attemptEarlyBailoutIfNoScheduledUpdate](02_attemptEarlyBailoutIfNoScheduledUpdate/README.md)
- [03 bailoutOnAlreadyFinishedWork](03_bailoutOnAlreadyFinishedWork/README.md)
- [spi](spi/README.md) — tag 대조표와 죽은 case
