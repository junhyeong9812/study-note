# lazy 전파

상위: [컨텍스트 흐름](../README.md)

한 함수 안에서 **위로 올라갔다가 아래로 내려온다.** 위로 가며 바뀐 provider 를 모으고, 모인 게 있을 때만 아래로 뿌린다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberNewContext.js` L411-L513 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberNewContext.js#L411-L513))

## 실제 코드

위로 올라가며 모으는 자리.

```js
// ReactFiberNewContext.js L417-L421
  // Collect all the parent providers that changed. Since this is usually small
  // number, we use an Array instead of Set.
  let contexts = null;
  let parent: null | Fiber = workInProgress;
  let isInsidePropagationBailout = false;
```

> Collect all the parent providers that changed. Since this is **usually small** number, we use an Array instead of Set.

그리고 끝에서 표시를 남긴다. 그 위 주석이 두 플래그를 설명한다.

```js
// ReactFiberNewContext.js L492-L512
  // This is an optimization so that we only propagate once per subtree. If a
  // deeply nested child bails out, and it calls this propagation function, it
  // uses this flag to know that the remaining ancestor providers have already
  // been propagated.
  //
  // NOTE: This optimization is only necessary because we sometimes enter the
  // begin phase of nodes that don't have any work scheduled on them —
  // specifically, the siblings of a node that _does_ have scheduled work. The
  // siblings will bail out and call this function again, even though we already
  // propagated content changes to it and its subtree. So we use this flag to
  // mark that the parent providers already propagated.
  //
  // Unfortunately, though, we need to ignore this flag when we're inside a
  // tree whose context propagation was deferred — that's what the
  // `NeedsPropagation` flag is for.
  //
  // If we could instead bail out before entering the siblings' begin phase,
  // then we could remove both `DidPropagateContext` and `NeedsPropagation`.
  // Consider this as part of the next refactor to the fiber tree structure.
  workInProgress.flags |= DidPropagateContext;
  return contexts !== null;
```

> This is an optimization so that we **only** propagate once per subtree.

> NOTE: This optimization is **only necessary** because we **sometimes** enter the begin phase of nodes that don't have any work scheduled on them — specifically, the siblings of a node that _does_ have scheduled work.

> If we could instead bail out before entering the siblings' begin phase, then we could remove both `DidPropagateContext` and `NeedsPropagation`. **Consider this as part of** the next refactor to the fiber tree structure.

## 동작 흐름

```text
 L411  function propagateParentContextChanges(current, workInProgress,
                                              renderLanes, forcePropagateEntireTree)

 L419  contexts = null
 L420  parent = workInProgress          ★ 자기 자신부터 본다. 부모가 아니다
 L421  isInsidePropagationBailout = false

 --- 위로 ---
 L422  while (parent !== null)
 L423    isInsidePropagationBailout 이 아니면
 L424      parent.flags & NeedsPropagation 이면
 L425        isInsidePropagationBailout = true
 L426      아니면 parent.flags & DidPropagateContext 이면
 L427        break                      ** 유일한 break 다 **

 L431    parent.tag === ContextProvider 이면
 L432      currentParent = parent.alternate
 L434      currentParent === null 이면
 L435        => throw 'Should have a current fiber. This is a bug in React.'
 L438      oldProps = currentParent.memoizedProps
 L439      oldProps !== null 이면
 L440        context = parent.type
 L442        newValue = newProps.value
 L444        oldValue = oldProps.value
 L446        !is(newValue, oldValue) 이면          ** 여기가 비교다 **
 L448          contexts.push(context)  또는 L450 contexts = [context]

 L454    아니면 parent === getHostTransitionProvider() 이면
 L463      oldState / L466 newState 를 꺼내
 L470      oldState !== newState 이면
 L472        contexts 에 HostTransitionContext 를 담는다

 L478    parent = parent.return

 --- 아래로 (조건부) ---
 L481  contexts !== null 이면
 L484    propagateContextChanges(workInProgress, contexts,
                                 renderLanes, forcePropagateEntireTree)

 L511  workInProgress.flags |= DidPropagateContext
 L512  => return contexts !== null
```

```text
 루프를 벗어나는 길이 셋이다

 1  break        L427 하나뿐이다 (DidPropagateContext)
 2  조건 소진    parent === null. HostRoot 의 return 이 null 이므로
                 break 가 안 걸리면 **루트까지 올라간다**
 3  throw        L435 / L459. 함수 자체를 나간다

 없는 것 - provider 를 만나도 멈추지 않는다.
 하나 모으고 계속 올라간다 (중첩 provider 다중 수집이 정상이다)
 서브트리 경계로 멈추는 조건도, contexts 개수 상한도 없다
```

```text
 ★ 자기 자신부터 본다는 것의 효과

 L420  parent = workInProgress

 같은 fiber 에 대해 이 함수를 두 번 부르면
 첫 반복의 L426 에서 곧장 break 한다 (L511 이 이미 찍어 뒀으므로)
 => contexts 가 null 이라 false 를 돌려준다

 즉 L511 의 표시가 **자기 멱등성** 장치로도 작동한다
```

```text
 ★ 두 플래그의 분업

 DidPropagateContext   "이 서브트리는 이미 전파했다" -> break
                       L511 에서 자기 자신에게 찍는다

 NeedsPropagation      "여기는 전파가 미뤄진 트리다" -> 앞 플래그를 무시하라
                       ★ [03] 읽기 쪽 L620 에서
                         **컨텍스트를 읽은 소비자가 스스로** 붙인다

 isInsidePropagationBailout 은 한 번 true 가 되면
 함수가 끝날 때까지 false 로 돌아가지 않는다 (대입 자리가 L425 하나다)
 => 경로상 어느 조상에라도 NeedsPropagation 이 있으면
    그 위로는 DidPropagateContext 의 단축이 영구히 꺼진다

 그리고 L423 의 if 가 감싸는 것은 L424-428 뿐이다.
 L431 / L454 의 provider 검사는 그 밖이라 매 조상에서 실행된다
```

```text
 두 플래그는 렌더 한 번만 산다

 둘 다 StaticMask 에 들어 있지 않다.
 그래서 createWorkInProgress 가
   workInProgress.flags = current.flags & StaticMask
 를 할 때 자동으로 사라진다

 명시적으로 지우는 코드가 없는 이유다
```

```text
 같은 함수 안에서 비교 방식이 둘이다

 L446  !is(newValue, oldValue)       provider 값 - Object.is 의미
 L470  oldState !== newState         host transition 상태 - strict equality

 주석 L468-469 가 이유를 적는다
   "This uses regular equality instead of Object.is because we assume that
    host transition state doesn't include NaN as a valid type."
```

```text
 부르는 곳이 성격으로 갈린다

 lazilyPropagateParentContextChanges (forcePropagateEntireTree = false)
   BW L1008  updateDehydratedActivityComponent
   BW L3024  updateDehydratedSuspenseComponent
   BW L3815  bailoutOnAlreadyFinishedWork
   BW L4028  attemptEarlyBailout 의 SuspenseComponent
             ★ **반환값을 contextChanged 로 받아 쓰는 유일한 자리**다
   BW L4093  같은 함수의 SuspenseListComponent

 다섯 다 **바이아웃을 하려는 참**에 부른다.
 "그냥 건너뛰어도 되나" 를 묻는 자리다

 propagateParentContextChangesToDeferredTree (true)
   Throw L212  resetSuspendedComponent
   BW L856     deferHiddenOffscreenComponent
```

## 결과가 쓰이는 곳

```text
 반환 boolean
      --> BW L4028 이 contextChanged 로 받아
          Suspense 의 primary 재시도 여부에 쓴다
      --> 나머지 넷은 버린다

 contexts 배열
      --> [02] 가 그것으로 서브트리를 훑는다
      --> 값이 아니라 **context 객체** 목록이다

 DidPropagateContext
      --> 다음 호출이 이 자리에서 멈춘다
```

## 다루지 않는 것

`HostTransitionContext` 갈래(L454-477)의 host transition 상태와 `getHostTransitionProvider`, `is`(`shared/objectIs`)의 구현, `NeedsPropagation` 이 세워진 뒤 실제로 어떤 시나리오를 구하는지의 사례, `deferHiddenOffscreenComponent`(BW L827)가 전파 뒤 `childLanes` 를 덮어쓰는 이유는 같은 뼈대의 곁가지라 요약만 했다.
