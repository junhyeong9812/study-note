# 순회

상위: [패시브 이펙트 흐름](../README.md)

정리와 실행이 각각 트리를 훑는다. **삭제된 컴포넌트는 새 트리에 없는데도 cleanup 이 도는데**, 그 방법이 이 문서의 요점이다.

## 위치

정리 `packages/react-reconciler` / `src` / `ReactFiberCommitWork.js` L4617-L4620 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitWork.js#L4617-L4620))

실행 `packages/react-reconciler` / `src` / `ReactFiberCommitWork.js` L3528-L3544 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitWork.js#L3528-L3544))

## 실제 코드

삭제된 자식으로 갈아타는 자리.

```js
// ReactFiberCommitWork.js L4843-L4850
        const childToDelete = deletions[i];
        const prevEffectStart = pushComponentEffectStart();
        // TODO: Convert this to use recursion
        nextEffect = childToDelete;
        commitPassiveUnmountEffectsInsideOfDeletedTree_begin(
          childToDelete,
          parentFiber,
        );
```

그리고 뮤테이션 단계가 포인터를 남겨 두는 이유.

```js
// ReactFiberCommitWork.js L1301-L1307
  // Note that we can't clear child or sibling pointers yet.
  // They're needed for passive effects and for findDOMNode.
  // We defer those fields, and all other cleanup, to the passive phase (see detachFiberAfterEffects).
  //
  // Don't reset the alternate yet, either. We need that so we can detach the
  // alternate's fields in the passive phase. Clearing the return pointer is
  // sufficient for findDOMNode semantics.
```

> Note that we can't clear child or sibling pointers yet. They're needed for passive effects and for `findDOMNode`. We defer those fields, and all other cleanup, to the passive phase (see `detachFiberAfterEffects`).

## 대조표

| | 정리 (unmount) | 실행 (mount) |
|---|---|---|
| 진입 | `commitPassiveUnmountEffects` CW L4617 | `commitPassiveMountEffects` CW L3528 |
| 인자 | `finishedWork` 하나 | 다섯 (root, finishedWork, lanes, transitions, endTime) |
| 재귀 | `recursivelyTraversePassiveUnmountEffects` CW L4835 | `recursivelyTraversePassiveMountEffects` CW L3546 |
| tag switch | `commitPassiveUnmountOnFiber` CW L4882 | `commitPassiveMountOnFiber` CW L3605 |
| 마스크 | 언제나 `PassiveMask` | `PassiveMask` 또는 `PassiveTransitionMask` |
| 삭제 | **여기서 처리** (`ChildDeletion`) | 아예 안 본다 |
| 순서 | 살아있는 트리는 자식 먼저, 삭제 트리는 **부모 먼저** | 자식 먼저 |

```text
 ★ 삭제된 컴포넌트의 cleanup 이 도는 방법

 패시브는 root.current 를 훑는다. 그것은 [커밋] L4032 에서 바뀐 **새 트리**다
 삭제된 fiber 는 그 child/sibling 사슬에 없다

 그런데도 cleanup 이 도는 것은 **부모가 옛 자식을 배열로 붙들고 있기** 때문이다

 (가) 렌더 단계에서 자식을 지울 때
      returnFiber.deletions 배열에 **옛 fiber** 를 넣고
      returnFiber.flags |= ChildDeletion 을 세운다

 (나) 뮤테이션 단계는 그 배열을 비우지 않는다
      detachFiberMutation 이 return 포인터만 끊고
      child / sibling 은 일부러 남긴다 (주석 CW L1301-1307)

 (다) 패시브 정리가 새 트리를 내려가다
      ChildDeletion 인 부모를 만나면
      deletions[i] 로 **옛 트리로 갈아탄다** (CW L4846-4847)

 (라) 다 돌고 나서야 detachFiberAfterEffects 가
      child / sibling / stateNode 까지 끊는다

 => "새 트리를 도는데 옛 컴포넌트가 정리된다" 의 답이다
```

```text
 갱신된 컴포넌트의 cleanup 은 또 다른 방법이다

 리렌더된 컴포넌트는 새 fiber 위에서 cleanup 이 불리는데,
 그 destroy 함수는 fiber 가 아니라 **훅 인스턴스** 에 들어 있다

 effect.inst.destroy 를 읽는다

 inst 는 렌더 사이에 같은 객체가 유지되므로
 새 fiber 를 돌면서도 이전 렌더가 만든 정리 함수를 찾을 수 있다

 (이 설명은 검증 과정에서 확인된 것이다)
```

```text
 삭제 트리만 순회 방식이 다르다

 살아있는 트리   .child / .sibling 재귀
 삭제된 트리     모듈 전역 nextEffect + _begin / _complete 반복

 그리고 방향도 반대다
   살아있는 트리  자식 먼저 (CW L4891 재귀 -> L4892 자기 정리)
   삭제된 트리    부모 먼저
     주석 CW L5118 "Deletion effects fire in parent -> child order"

 Offscreen 이 숨겨질 때도 부모 먼저다
   주석 CW L5066-5067 "When disconnecting passive effects, we fire the
   effects in the same order as during a deletiong: parent before child"
   (원문의 오타 "deletiong" 그대로다)

 삭제 트리 순회에는 TODO 가 둘 붙어 있다
   CW L4845  "TODO: Convert this to use recursion"
   CW L5123  "Only traverse subtree if it has a PassiveStatic flag"
```

```text
 삭제와 갱신에서 부르는 범위가 다르다

 갱신  HookPassive | HookHasEffect
       deps 가 같으면 HookHasEffect 가 안 붙어 건너뛴다

 삭제  HookPassive 만
       => deps 가 그대로였어도 **전부** cleanup 한다

 당연한 이야기지만 코드로 구분돼 있다
 (이 대비는 검증 과정에서 확인된 것이고,
  나는 삭제 쪽 호출부까지만 직접 봤다)
```

```text
 사용자 코드에 닿는 길

 정리  commitHookPassiveUnmountEffects
         -> commitHookEffectListUnmount
         -> safelyCallDestroy
         -> 운영에서 destroy_()  (DEV 는 runWithFiberInDEV 경유)

 실행  commitHookPassiveMountEffects
         -> commitHookEffectListMount
         -> 운영에서 destroy = create()
            그 반환값을 훅 인스턴스에 저장한다

 => useEffect(() => { ...; return cleanup; }) 의
    cleanup 이 저장되는 자리가 여기다
```

## 결과가 쓰이는 곳

```text
 effect.inst.destroy
      --> create 의 반환값이 여기 저장된다
      --> 다음 커밋의 정리가 이것을 읽는다

 detachFiberAfterEffects
      --> 삭제 트리 순회가 끝나며 포인터를 마저 끊는다
      --> 이때까지 미룬 이유가 이 순회다

 부모의 deletions 배열
      --> 다음 렌더에서 그 fiber 를 재사용할 때 지워진다
```

## 다루지 않는 것

`commitPassiveMountOnFiber`(CW L3605)의 tag 별 갈래 열둘, `commitPassiveUnmountOnFiber`(CW L4882)의 다섯, Offscreen 숨김·재등장(`disconnectPassiveEffect` CW L5050 / `reconnectPassiveEffects` CW L4269), 숨은 트리의 캐시 refcount(`commitAtomicPassiveEffects` CW L4539), `detachFiberAfterEffects`(CW L1315)의 본문, `detachAlternateSiblings`, `PassiveMask` / `PassiveTransitionMask` 의 구성, 훅 인스턴스가 만들어지는 자리는 이 문서의 범위 밖이다.
