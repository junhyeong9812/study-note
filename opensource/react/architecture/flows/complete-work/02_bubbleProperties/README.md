# bubbleProperties

상위: [completeWork 흐름](../README.md)

자식들을 훑어 **두 가지를 부모로 올린다** — `childLanes` 와 `subtreeFlags`. 거의 같은 루프가 넷인데, 그 차이에 이 함수의 내용이 다 들어 있다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberCompleteWork.js` L791-L912 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCompleteWork.js#L791-L912))

## 실제 코드

바이아웃 판정이 플래그가 아니다.

```js
// ReactFiberCompleteWork.js L792-L794
  const didBailout =
    completedWork.alternate !== null &&
    completedWork.alternate.child === completedWork.child;
```

바이아웃이 아니면 자식의 플래그를 그대로 올린다.

```js
// ReactFiberCompleteWork.js L842-L843
        subtreeFlags |= child.subtreeFlags;
        subtreeFlags |= child.flags;
```

바이아웃이면 걸러서 올린다.

```js
// ReactFiberCompleteWork.js L894-L895
        subtreeFlags |= child.subtreeFlags & StaticMask;
        subtreeFlags |= child.flags & StaticMask;
```

> "Static" flags share the lifetime of the fiber/hook they belong to, so we should bubble those up even during a bailout. All the other flags have a lifetime **only** of a single render + commit, so we should ignore them.

그리고 자기비판 주석이 붙은 한 줄.

```js
// ReactFiberCompleteWork.js L897-L900
        // Update the return pointer so the tree is consistent. This is a code
        // smell because it assumes the commit phase is never concurrent with
        // the render phase. Will address during refactor to alternate model.
        child.return = completedWork;
```

## 동작 흐름

```text
 L791  function bubbleProperties(completedWork)

 L792  didBailout = alternate !== null
                    && alternate.child === completedWork.child
 L796  newChildLanes = NoLanes
 L797  subtreeFlags = NoFlags

 L799  if (!didBailout)
 L801    [FLAG:enableProfilerTimer && ProfileMode]
           루프 (1)  L807-830
             newChildLanes |= child.lanes | child.childLanes
             subtreeFlags  |= child.subtreeFlags | child.flags
             actualDuration   += child.actualDuration      L825
             treeBaseDuration += child.treeBaseDuration     L828
 L832      completedWork.actualDuration = actualDuration
 L833      completedWork.treeBaseDuration = treeBaseDuration
 L834    아니면
           루프 (2)  L835-851
             newChildLanes |= ...
             subtreeFlags  |= child.subtreeFlags | child.flags
 L848        child.return = completedWork
 L854    completedWork.subtreeFlags |= subtreeFlags

 L855  아니면 (didBailout)
 L857    [FLAG:enableProfilerTimer && ProfileMode]
           루프 (3)  L862-879
             newChildLanes |= ...
             subtreeFlags  |= (child.subtreeFlags | child.flags) & StaticMask
             treeBaseDuration += child.treeBaseDuration     L877
             (actualDuration 은 건드리지 않는다)
 L881      completedWork.treeBaseDuration = treeBaseDuration
 L882    아니면
           루프 (4)  L883-903
             newChildLanes |= ...
             subtreeFlags  |= (...) & StaticMask
 L900        child.return = completedWork
 L906    completedWork.subtreeFlags |= subtreeFlags

 L909  completedWork.childLanes = newChildLanes
 L911  => return didBailout
```

```text
 루프 넷의 차이는 두 축이다

                    플래그 마스크      시간 측정        child.return
 (1) !bail 프로파일   없음             actual + base    없음
 (2) !bail 평상       없음             없음             L848
 (3)  bail 프로파일   StaticMask       base 만          없음
 (4)  bail 평상       StaticMask       없음             L900

 (1)과 (3)의 시간 측정이 다른 것이 앞뒤가 맞는다
 바이아웃이면 "이번에 실제로 쓴 시간"(actualDuration)은 없고
 "트리 기준 시간"(treeBaseDuration)만 올린다
```

```text
 바이아웃을 플래그가 아니라 포인터로 안다

 L792-794  alternate !== null && alternate.child === completedWork.child

 이전 트리와 지금 트리가 **같은 자식 객체를 가리키면**
 자식을 새로 만들지 않았다는 뜻이고, 그게 바이아웃이다

 [beginWork]의 bailoutOnAlreadyFinishedWork 가
 cloneChildFibers 를 부른 경우에는 자식이 새 클론이라
 이 비교가 거짓이 된다

 => 여기서 말하는 바이아웃은 "자식을 복제조차 안 한 얕은 바이아웃" 이다
```

```text
 StaticMask 가 걸리는 이유

 주석이 말한다 (L869-872, 같은 주석이 L890-893 에도 있다)
   Static 플래그는 그것이 속한 fiber/훅과 수명을 같이한다
   그래서 바이아웃 중에도 올려야 한다
   나머지 플래그는 렌더+커밋 한 번만 살기 때문에 무시해야 한다

 즉 플래그에 수명이 두 종류다
   한 번 쓰고 버리는 것   Update / Placement / Visibility ...
   fiber 와 함께 사는 것  Static 계열

 바이아웃은 "이번 렌더에서 아무 일도 안 했다" 는 뜻이므로
 한 번 쓰고 버리는 플래그를 올리면 거짓이 된다
```

```text
 ★ child.return 을 다시 세우는 줄은 운영 빌드에서만 돈다

 L848 / L900 이 그 줄이고 둘 다 비프로파일 갈래에 있다
 그런데 그 갈래에 언제 들어가는지를 따라가면 이렇게 된다

   가드          enableProfilerTimer && (mode & ProfileMode) !== NoMode
   플래그 정의   enableProfilerTimer = __PROFILE__   (ReactFeatureFlags L229)
   빌드 치환     __PROFILE__ = 운영이 아니면 true    (scripts/rollup/build.js L437)
   루트 모드     __DEV__ 이면 mode |= ProfileMode     (ReactFiber.js L550-554)
                 주석 L551 "dev: Enable profiling instrumentation by default."

 => DEV 빌드   가드가 참이라 프로파일러 갈래로 간다. L848/L900 안 돈다
    운영 빌드  enableProfilerTimer 가 false 라 평상 갈래로 간다. 언제나 돈다

 주석이 스스로 code smell 이라 부르는 그 줄이
 정작 개발 중에는 실행되지 않는다

 (그래도 문제가 되지 않는 것은 .return 을 세우는 주인이 따로 있기 때문이다 -
  자식을 만들거나 복제하는 쪽에서 이미 세운다.
  다만 그 전수 확인은 이 문서의 범위 밖이고, 검증 과정에서 짚어진 것이다)
```

```text
 반환값을 아무도 쓰지 않는다

 L911  return didBailout;

 이 파일에서 31곳이 부르는데 전부 맨문장이다
   bubbleProperties(workInProgress);

 값을 받는 형태(= / if / return)가 하나도 없고
 함수가 모듈 밖으로 나가지도 않는다

 => 계산해서 돌려주지만 죽은 값이다
```

## 결과가 쓰이는 곳

```text
 completedWork.subtreeFlags
      --> 커밋이 이것을 보고 서브트리로 내려갈지 정한다
      --> 자식에 할 일이 없으면 통째로 건너뛴다

 completedWork.childLanes
      --> 다음 렌더의 바이아웃 판정에 쓰인다
      --> [beginWork]의 bailoutOnAlreadyFinishedWork L3807 이 읽는다

 actualDuration / treeBaseDuration
      --> 프로파일러가 읽는다
      --> 바이아웃이면 actualDuration 은 올리지 않는다

 반환값 didBailout
      --> 쓰이지 않는다
```

## 다루지 않는 것

`StaticMask` 의 구성과 어떤 플래그가 Static 인지, `mergeLanes` 의 비트 연산, `actualDuration` / `treeBaseDuration` 이 커밋 후 어떻게 보고되는지, `ProfileMode` 가 자식 fiber 로 전파되는 경로, `.return` 포인터를 세우는 다른 자리들(자식 조정과 클론)은 같은 뼈대의 곁가지라 요약만 했다.
