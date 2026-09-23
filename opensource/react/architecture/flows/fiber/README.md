# Fiber 라는 자료구조

상위: [React 아키텍처 지도](../../README.md)

이 지도의 문서 스물넷이 `alternate` · `memoizedState` · `flags` 같은 칸을 **전제하고** 쓴다. 그 칸들이 어디서 정의되고 어떻게 채워지는지를 한자리에 모은다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 약어: `TYPES` = `ReactInternalTypes.js`(464줄), `FIBER` = `ReactFiber.js`(979줄), `BW` = `ReactFiberBeginWork.js`.

## 전체 그림

```text
 파일 둘이 짝이다

 TYPES   무엇이 있는가      Fiber 타입 L89-210, FiberRoot L386-392,
                           Dispatcher L397-457
 FIBER   어떻게 만드는가    createFiber / createWorkInProgress /
                           createFiberFromTypeAndProps / createFiberFromX 열다섯
```

1. [칸 서른셋](01_shape/README.md) — Fiber 타입의 필드와 그 주석.
2. [짝 만들기](02_workInProgress/README.md) — `alternate` 와 이중 버퍼링, `StaticMask`.
3. [JSX 가 tag 이 되기까지](03_tagFromType/README.md) — `<div>` 와 `<Foo/>` 가 갈리는 자리.

```text
 ★★ 필드가 서른셋이다 — 필수 23, 선택 10

 필수 23
   tag key elementType type stateNode          인스턴스에 속하는 것
   return child sibling index                  트리
   ref refCleanup                              ref
   pendingProps memoizedProps
   updateQueue memoizedState dependencies      들어오는 것과 나가는 것
   mode                                        모드
   flags subtreeFlags deletions                이펙트
   lanes childLanes                            우선순위
   alternate                                   짝

 선택 10
   actualDuration actualStartTime
   selfBaseDuration treeBaseDuration           [FLAG:enableProfilerTimer]
   _debugInfo _debugOwner _debugStack
   _debugTask _debugNeedsRemount
   _debugHookTypes                             [__DEV__]
```

```text
 ★★★ return 은 "부모" 가 아니다. 주석이 다르게 부른다

 TYPES L123-125
   "This is effectively the parent, but there can be multiple parents (two)
    so this is only the parent of the thing we're currently processing.
    It is conceptually the same as the return address of a stack frame."

 => 부모가 둘일 수 있다 (current 트리의 것과 work-in-progress 트리의 것).
    그래서 "지금 처리 중인 것의 부모" 이고, 이름이 parent 가 아니라 return 이다

 TYPES L128 - "Singly Linked List Tree Structure."
 => child 하나와 sibling 사슬로 트리를 만든다. 자식 배열이 없다
```

```text
 ★ Flow 의 한계가 타입 모양을 두 번 바꿨다

 Fiber      TYPES L90-93
   "These first fields are conceptually members of an Instance. This used to
    be split into a separate type and intersected with the other Fiber fields,
    but until Flow fixes its intersection bugs, we've merged them into a
    single type."
   => 교집합을 포기하고 **한 타입에 합쳤다**

 FiberRoot  TYPES L386-392
   조각 다섯을 **스프레드**로 합친다 (`...BaseFiberRootProperties,` 등)
   주석 L383-384 - "Exported FiberRoot type includes all properties, / To avoid
     requiring potentially error-prone :any casts throughout the project."
   ★ 스프레드는 속성의 **합집합**이다. 교집합이 아니다
     (조각 다섯은 키가 서로 겹치지 않아 교집합이면 빈 타입이 된다)

 (두 방식을 나란히 놓은 것은 내 관찰이다)
```

## 어디로 이어지는가

```text
 [마운트]        createHostRootFiber 로 첫 fiber 를 만든다

 [beginWork]     tag 로 29갈래 switch 를 돈다. 그 tag 를 [03]이 정한다
                 case Throw 가 되던지는 값이 [03]에서 담긴다

 [자식 조정]     createFiberFromElement / createWorkInProgress 로
                 재사용할지 새로 만들지 가른다

 [렌더 루프]     createWorkInProgress 로 트리 한 벌을 더 만든다

 [컨텍스트 전파]  dependencies 를 복제하는 자리가 [02]에 있다

 [클래스 컴포넌트] StaticMask 가 LayoutStatic 을 살리는 자리가 [02]에 있다
```

## 결과가 쓰이는 곳

```text
 fiber.tag
      --> [beginWork] / [completeWork] / [에러와 Suspense]의 switch 셋이 본다

 fiber.alternate
      --> 두 트리를 오간다. 커밋이 root.current 를 바꾸면 역할이 뒤집힌다

 fiber.flags & StaticMask
      --> 렌더를 넘어 사는 플래그와 한 번 쓰고 사라지는 플래그를 가른다

 fiber.stateNode
      --> 호스트면 DOM 노드, 클래스면 인스턴스, HostRoot 면 FiberRoot
```

## 다루지 않는 것

`FiberRoot` 의 조각 다섯(`BaseFiberRootProperties` L212 외)이 담는 필드 전체와 `ReactFiberRoot.js` 의 생성, `Dispatcher`(TYPES L397-457) / `AsyncDispatcher`(L459) 타입이 훅 디스패처 테이블과 대응하는 방식([훅](../hooks/README.md)에 그 테이블이 있다), `WorkTag`(`ReactWorkTags.js`)의 전체 목록([beginWork](../begin-work/README.md)의 표에 있다), `TypeOfMode`(`ReactTypeOfMode.js`)의 비트와 `mode` 가 상속되는 경로, `Flags`(`ReactFiberFlags.js`)의 비트 배치([커밋](../commit/README.md)에 있다), `HookType` / `ContextDependency` / `MemoCache` 타입, `createHostRootFiber`(FIBER L536)가 mode 를 정하는 규칙, `resetWorkInProgress`(FIBER L447)의 본문과 호출처, `createFiberFromX` 열다섯 각각의 세부는 이 문서의 범위 밖이다.

## 하위 메서드

- [01 칸 서른셋](01_shape/README.md)
- [02 짝 만들기](02_workInProgress/README.md)
- [03 JSX 가 tag 이 되기까지](03_tagFromType/README.md)
