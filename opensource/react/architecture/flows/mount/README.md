# 마운트

`createRoot(container)` 를 부르고 `root.render(<App/>)` 을 부르면 **무슨 일이 일어나는가**다.

결론부터 말하면 **렌더는 일어나지 않는다.** 이 흐름이 하는 일은 fiber 루트를 만들고, 갱신 객체 하나를 큐에 넣고, **마이크로태스크를 거는 것**까지다. 실제 렌더는 그 다음 턴에 시작한다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 각 절에 파일을 밝혔다.

## 전체 그림

```text
 [01] createRoot                          ReactDOMRoot L171
      +-- [02] createContainer             Reconciler L235
      |     +-- [03] createFiberRoot        ReactFiberRoot L157
      |     +-- registerDefaultIndicator    Reconciler L278
      +-- markContainerAsRoot               ReactDOMRoot L252
      +-- listenToAllSupportedEvents        ReactDOMRoot L258   등록만 한다
      +-- => new ReactDOMRoot(root)         ReactDOMRoot L261

      여기까지 화면에 아무것도 없다

 [04] root.render(children)               ReactDOMRoot L107
      +-- updateContainer                   Reconciler L353
            +-- requestUpdateLane            Reconciler L360
            +-- [05] updateContainerImpl     Reconciler L393
                  +-- createUpdate           Reconciler L433
                  +-- update.payload = {element}   Reconciler L436
                  +-- enqueueUpdate          Reconciler L452
                  +-- null 이면 => 아무것도 안 한다   Reconciler L453
                  +-- [06] scheduleUpdateOnFiber    Reconciler L455

 [06] scheduleUpdateOnFiber               WorkLoop L973
      +-- markRootUpdated                   WorkLoop L1013   언제나 돈다
      +-- 렌더 페이즈 중 갱신이면 => lane 만 기록하고 끝    WorkLoop L1015-1030
      +-- 보통은 ensureRootIsScheduled       WorkLoop L1079
            +-- root 를 스케줄 리스트에 넣는다   RootScheduler L125-134
            ~~> scheduleMicrotask(...)          RootScheduler L667

 여기서 이 흐름이 끝난다. 다음은 마이크로태스크 안이다
```

```text
 경계가 어디인지가 이 흐름의 핵심이다

 ensureRootIsScheduled 의 주석이 직접 말한다 (RootScheduler L117-122)

   "This function is called whenever a root receives an update. It does two
    things 1) it ensures the root is in the root schedule, and 2) it ensures
    there's a pending microtask to process the root schedule."

   "Most of the actual scheduling logic does not happen until
    `scheduleTaskForRootDuringMicrotask` runs."

 즉 root.render() 가 돌아온 시점에 결정된 것은
   "이 루트에 할 일이 생겼다" 와 "곧 처리하겠다" 뿐이다

 어느 우선순위로 어떤 태스크를 걸지도 마이크로태스크 안에서 정한다
```

```text
 두 단계가 나뉘어 있다

 createRoot   그릇을 만든다
              createContainer 가 initialChildren 을 null 로 하드코딩한다
              (Reconciler L262). 그래서 루트 fiber 의
              memoizedState.element 가 null 로 시작한다 (ReactFiberRoot L227)

 root.render  내용을 넣는다
              update.payload = {element} 로 children 을 실어 큐에 넣는다
              (Reconciler L436)

 그래서 createRoot 만 부르고 render 를 안 부르면 아무 일도 안 일어난다
```

```text
 fiber 루트와 fiber 가 서로를 가리킨다

 ReactFiberRoot L211  root.current = uninitializedFiber
 ReactFiberRoot L212  uninitializedFiber.stateNode = root

 주석이 그것을 이렇게 부른다 (L208-209)
   "Cyclic construction. This cheats the type system right now because
    stateNode is any."

 이 고리 때문에 어느 쪽을 잡아도 반대쪽으로 갈 수 있다
 DOM 노드에서 fiber 를 찾는 것도 markContainerAsRoot(ReactDOMRoot L252)가 건다
```

```text
 빌드 플래그가 분기를 만든다 - Java 에 없던 것

 이 흐름에만 플래그 분기가 여덟 종 나온다
 그중 둘은 **이 빌드에서 아예 안 도는 코드**를 만든다

 disableLegacyMode 가 기본 true 라서 (ReactFeatureFlags L192)
   WorkLoop L1080-1097 의 legacy sync flush 가 통째로 죽는다
   Reconciler L378 의 LegacyRoot 분기도 죽는다

 __DEV__ 블록은 프로덕션 빌드에서 빠진다
   그 안의 경고는 운영에서 안 나온다

 표는 spi 에 있다
```

## 어디로 이어지는가

```text
 [스케줄링]  마이크로태스크가 깨어나면 우선순위를 정하고 렌더 태스크를 건다
 [렌더 루프]  그 태스크가 fiber 트리를 훑는다
 [커밋]       DOM 에 반영한다
```

## 단계

1. [createRoot](01_createRoot/README.md)이 컨테이너를 검사하고 옵션을 읽는다.
2. [createFiberRoot](02_createFiberRoot/README.md)가 루트와 fiber 를 만들어 엮는다.
3. [root.render](03_ReactDOMRoot.render/README.md)가 children 을 넘긴다.
4. [updateContainerImpl](04_updateContainerImpl/README.md)이 갱신 객체를 만들어 큐에 넣는다.
5. [scheduleUpdateOnFiber](05_scheduleUpdateOnFiber/README.md)가 루트에 표시하고 스케줄을 건다.

## 결과가 쓰이는 곳

```text
 FiberRoot
      --> 이후 모든 렌더의 출발점이다
      --> current 가 커밋된 트리를, alternate 가 작업 중인 트리를 가리킨다

 update (payload = {element})
      --> 렌더 중 HostRoot 를 처리할 때 이것을 꺼내 children 으로 쓴다

 root.pendingLanes (markRootUpdated 가 세운다)
      --> 마이크로태스크가 이것을 보고 우선순위를 정한다

 걸린 마이크로태스크
      --> processRootScheduleInMicrotask 가 실제 스케줄링을 한다
```

## 다루지 않는 것

`hydrateRoot` 의 수화 경로, `FiberRootNode` 생성자가 세우는 필드 전부, `requestUpdateLane` 이 우선순위를 고르는 규칙, `enqueueConcurrentClassUpdate` 의 동시성 큐, `listenToAllSupportedEvents` 의 이벤트 위임 구조, 마이크로태스크가 깨어난 뒤의 `processRootScheduleInMicrotask` 와 렌더 태스크 스케줄링은 같은 뼈대의 곁가지라 요약만 했다. 빌드 플래그별 차이는 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 createRoot](01_createRoot/README.md)
- [02 createFiberRoot](02_createFiberRoot/README.md)
- [03 root.render](03_ReactDOMRoot.render/README.md)
- [04 updateContainerImpl](04_updateContainerImpl/README.md)
- [05 scheduleUpdateOnFiber](05_scheduleUpdateOnFiber/README.md)
- [spi](spi/README.md) — 빌드 플래그 표
