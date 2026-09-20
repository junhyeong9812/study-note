# completeWork

[렌더 루프](../render-loop/README.md)의 `completeUnitOfWork` 가 부르는 **올라오는 쪽**이다. [beginWork](../begin-work/README.md)가 내려가며 밀어 둔 것을 꺼내고, 호스트 인스턴스를 만들고, 자식들의 정보를 부모로 올린다.

이 흐름의 핵심은 셋이다. **push 의 짝이 여기 있고**, **자식 정보를 부모로 올리며**, **올라오는 길인데 되돌려 보내는 자리가 다섯 있다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberCompleteWork.js` 기준이다.

## 전체 그림

```text
 [01] completeWork                                 L1080
      +-- popTreeContext(workInProgress)           L1090   모든 tag 공통
      +-- switch (workInProgress.tag)              L1091   case 레이블 29개
      |     거의 모두 이 모양이다
      |       pop 무언가 -> 일 하기 -> [02] bubbleProperties -> return null
      |     되돌려 보내는 다섯 자리는 아래에 따로 적는다
      +-- switch 를 빠져나오면 => **throw** Unknown unit of work tag   L2091

 [02] bubbleProperties                             L791
      +-- 자식을 훑어 childLanes 와 subtreeFlags 를 부모로 올린다
      +-- 바이아웃이면 StaticMask 로 거른 것만 올린다

 [03] HostComponent case                           L1372
      +-- popHostContext                           L1373
      +-- 갱신이면 updateHostComponent              L1376   참조 비교뿐이다
      +-- 최초면 createInstance                     L1424   실제 DOM 노드
      |     appendAllChildren                      L1434
      +-- preloadInstanceAndSuspendIfNeeded         L1463   **던질 수 있다**

 [04] SuspenseListComponent case                   L1707
      +-- row 를 하나씩 렌더하는 드라이버 루프다
      +-- => return workInProgress.child            L1787
      +-- => return next                            L1936
```

1. [completeWork](01_completeWork/README.md)가 tag 별로 갈리고 네 갈래가 throw 로 향한다.
2. [bubbleProperties](02_bubbleProperties/README.md)가 자식 정보를 부모로 올린다.
3. [HostComponent](03_HostComponent/README.md)가 실제 DOM 노드를 만든다.
4. [SuspenseListComponent](04_SuspenseListComponent/README.md)가 row 를 하나씩 몬다.

```text
 push 와 pop 이 짝을 이룬다

 [beginWork]가 내려가며 민다
   pushHostContext / pushProvider / pushCacheProvider
   pushHostContainer / pushSuspenseHandler / pushSuspenseListContext

 [completeWork]가 올라오며 꺼낸다
   popHostContext(L1373) / popProvider(L1691) / popCacheProvider(L1139, L2059)
   popHostContainer(L1146, L1680) / popSuspenseHandler / popSuspenseListContext(L1708)

 바이아웃해도 짝이 맞아야 해서
 [beginWork]의 attemptEarlyBailoutIfNoScheduledUpdate 가
 평가는 건너뛰면서 push 만 흉내 낸다

 그 반대쪽이 이 흐름이다
```

```text
 ★ 올라오는 길인데 되돌려 보내는 자리가 다섯이다

 completeWork 의 반환값이 null 이 아니면
 completeUnitOfWork 는 형제로도 부모로도 가지 않는다
   WorkLoop L3389  if (next !== null)
            L3390    // Completing this fiber spawned new work. Work on that next.
            L3391    workInProgress = next
            L3392    return

 그런 자리가 다섯이다

   L1522  ActivityComponent    return workInProgress
   L1571  SuspenseComponent    return workInProgress
   L1595  SuspenseComponent    return workInProgress
   L1787  SuspenseListComponent  return workInProgress.child
   L1936  SuspenseListComponent  return next

 앞의 셋은 "내 begin 단계를 다시 해라" 다
 이번에는 DidCapture 나 ForceClientRender 가 켜져 있어
 beginWork 가 다른 갈래를 고른다

 뒤의 둘은 [04] 가 row 를 하나씩 모는 것이다
```

```text
 throw 로 향하는 갈래가 넷인데 전부 닿지 않는다

 L1094  IncompleteFunctionComponent  break   [disableLegacyMode=true]
 L1696  IncompleteClassComponent     break   [disableLegacyMode=true]
 L1962  ScopeComponent               break   [enableScopeAPI=false]
 L2083  Throw                        흘러나감 [disableLegacyMode=true]

 앞의 셋은 그 tag 의 fiber 가 만들어지지 않아서,
 마지막 하나는 Throw fiber 가 이 함수에 오지 않아서 닿지 않는다
 자세한 것은 [spi](spi/README.md)에 있다
```

```text
 던지기가 이 단계에도 있다

 L1463  preloadInstanceAndSuspendIfNeeded
          -> L602 suspendCommit()
          -> ReactFiberThenable L313  throw SuspenseyCommitException

 [렌더 루프]의 handleThrow 가 그것을 받아 SuspendedOnInstance 로 바꾼다
 (L2321-2323)

 주석이 왜 이 호출을 맨 끝에 두는지 적는다 (L1459-1462)
   "This must come at the very end of the complete phase, because it might
    throw to suspend, and if the resource immediately loads, the work loop
    will resume rendering as if the work-in-progress completed.
    So it must fully complete."

 => 서스펜션은 컴포넌트를 그릴 때만 일어나는 것이 아니다
    리소스가 준비되지 않아도 일어난다
```

## 어디로 이어지는가

```text
 [렌더 루프]    completeUnitOfWork 가 이 흐름을 부르고
                반환값이 null 이면 형제나 부모로 올라간다

 [beginWork]    여기서 pop 하는 것을 저쪽이 push 했다
                반환값이 null 이 아니면 저쪽으로 되돌아간다

 [커밋]         여기서 세운 flags 와 만든 인스턴스를 저쪽이 쓴다
                props diff 도 이 단계가 아니라 저쪽에서 한다
```

[커밋](../commit/README.md)은 따로 지도가 있다.

## 결과가 쓰이는 곳

```text
 반환값 (Fiber 또는 null)
      --> completeUnitOfWork L3389 가 읽는다
      --> null 이 아니면 그 fiber 를 다시 begin 단계로 보낸다

 workInProgress.stateNode
      --> 호스트 인스턴스다. 커밋이 트리에 붙인다

 flags (Update / Snapshot / Passive / Visibility / Hydrate ...)
      --> 커밋의 각 패스가 무엇을 할지 정한다

 subtreeFlags / childLanes
      --> [02] 가 올린 것이다
      --> 커밋이 subtreeFlags 로 내려갈지 말지 정한다
      --> childLanes 는 다음 렌더의 바이아웃 판정에 쓰인다
```

## 다루지 않는 것

`updateHostText`(L672), 탈수(dehydrated) 경계를 끝내는 `completeDehydratedActivityBoundary`(L914)와 `completeDehydratedSuspenseBoundary`(L997), `HostRoot`(L1117) / `HostHoistable`(L1198) / `HostSingleton`(L1300) / `Offscreen`(L1964) case 의 본문, `scheduleRetryEffect`(L638)가 재시도를 거는 방식, `appendAllChildrenToContainer`(L353) 와 `doesRequireClone`(L217) 같은 persistence 전용 경로, 커밋 단계가 이 flags 를 소비하는 과정은 같은 뼈대의 곁가지라 요약만 했다. case 별 대조표와 죽은 갈래는 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 completeWork](01_completeWork/README.md)
- [02 bubbleProperties](02_bubbleProperties/README.md)
- [03 HostComponent](03_HostComponent/README.md)
- [04 SuspenseListComponent](04_SuspenseListComponent/README.md)
- [spi](spi/README.md) — case 대조표, 반환 계약, 죽은 갈래
